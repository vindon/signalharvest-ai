from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import anthropic
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from config.settings import settings
from db.brand_store import get_active_brands
from db.signal_store import fetch_scored_by_run
from schemas.brand import BrandSubscription
from schemas.signal import CuratedLead, ScoredSignal, SignalTier

_SKILL_PATH = Path(__file__).parent.parent / "skills" / "brand_match" / "SKILL.md"
_SKILL = _SKILL_PATH.read_text(encoding="utf-8")
_CLIENT = anthropic.Anthropic(api_key=settings.anthropic_api_key)
_TIER_ORDER = {SignalTier.WATCH: 0, SignalTier.WARM: 1, SignalTier.HOT: 2}


def run(state: dict) -> dict:
    run_id = state["run_id"]
    brands = get_active_brands()
    if not brands:
        return {**state, "curated_leads": [], "leads_curated": 0}
    scored = fetch_scored_by_run(run_id=run_id, min_score=settings.curator_min_score)
    if not scored:
        return {**state, "curated_leads": [], "leads_curated": 0}
    all_leads: list[CuratedLead] = []
    for brand in brands:
        try:
            leads = _match_brand(brand, scored, run_id)
            all_leads.extend(leads)
        except Exception as exc:
            print(f"[curator] brand {brand.name} error: {exc}")
    return {
        **state,
        "curated_leads": [lead.model_dump() for lead in all_leads],
        "leads_curated": len(all_leads),
    }


def _match_brand(
    brand: BrandSubscription, signals: list[ScoredSignal], run_id: str
) -> list[CuratedLead]:
    candidates = _pre_filter(brand, signals)
    if not candidates:
        return []
    candidates = sorted(candidates, key=lambda s: s.score, reverse=True)[:30]
    matches = _ask_claude(brand, candidates)
    if not matches:
        return []
    now = datetime.now(UTC)
    reasons = matches.get("match_reasons", {})
    leads = []
    for sid in matches.get("matched_signal_ids", []):
        sig = next((s for s in candidates if s.id == sid), None)
        if sig is None:
            continue
        leads.append(
            CuratedLead(
                **sig.model_dump(),
                brand_id=brand.id,
                match_reason=reasons.get(sid, "Matched brand criteria."),
                curated_at=now,
            )
        )
    return leads


def _pre_filter(brand: BrandSubscription, signals: list[ScoredSignal]) -> list[ScoredSignal]:
    min_tier_val = _TIER_ORDER[brand.min_tier]
    brand_cats = {c.value for c in brand.categories}
    brand_geos = {g.lower() for g in brand.geographies}
    exclude_kws = {k.lower() for k in brand.keywords_exclude}
    result = []
    for s in signals:
        if s.category.value not in brand_cats:
            continue
        if _TIER_ORDER.get(s.tier, 0) < min_tier_val:
            continue
        if brand_geos and s.geography:
            if not any(g in s.geography.lower() for g in brand_geos):
                continue
        if any(kw in (s.text or "").lower() for kw in exclude_kws):
            continue
        result.append(s)
    return result


@retry(
    retry=retry_if_exception_type(anthropic.RateLimitError),
    wait=wait_exponential(multiplier=2, min=4, max=60),
    stop=stop_after_attempt(3),
)
def _ask_claude(brand: BrandSubscription, candidates: list[ScoredSignal]) -> dict:
    brand_ctx = (
        f"Brand: {brand.name}\nCategories: {[c.value for c in brand.categories]}\n"
        f"Geographies: {brand.geographies or ['all']}\n"
        f"Keywords to favour: {brand.keywords_include}\n"
        f"Competitors to flag: {brand.competitor_brands}"
    )
    blocks = [
        f"ID:{s.id}|Cat:{s.category.value}|Intent:{s.intent_type.value}|"
        f"Score:{s.score}|Tier:{s.tier.value}|Geo:{s.geography or 'unknown'}\n"
        f"<signal_text>\n{(s.text or '')[:400]}\n</signal_text>"
        for s in candidates
    ]
    prompt = (
        f"Brand context:\n{brand_ctx}\n\nSignals:\n\n"
        + "\n\n---\n\n".join(blocks)
        + "\n\nReturn JSON: matched_signal_ids and match_reasons."
    )
    response = _CLIENT.messages.create(
        model=settings.model_reasoning,
        max_tokens=4096,
        system=_SKILL,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = "\n".join(text.split("\n")[1:-1])
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}

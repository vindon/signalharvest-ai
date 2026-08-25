from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import anthropic
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from config.settings import settings
from db.signal_store import fetch_unclassified, update_classification
from schemas.signal import ClassifiedSignal, IntentType, RawSignal, SignalCategory

_TAXONOMY_PATH = Path(__file__).parent.parent / "skills" / "taxonomy" / "SKILL.md"
_TAXONOMY_SKILL = _TAXONOMY_PATH.read_text(encoding="utf-8")
_CLIENT = anthropic.Anthropic(api_key=settings.anthropic_api_key)
BATCH_SIZE = 10


def _batch(items: list, size: int) -> list:
    return [items[i : i + size] for i in range(0, len(items), size)]


def run(state: dict) -> dict:
    run_id = state["run_id"]
    raw_signals = fetch_unclassified(run_id)
    if not raw_signals:
        return {**state, "signals_classified": 0}
    classified_count = 0
    for batch in _batch(raw_signals, BATCH_SIZE):
        for classified in _classify_batch(batch):
            try:
                update_classification(classified)
                classified_count += 1
            except Exception as exc:
                print(f"[classifier] db error {classified.id}: {exc}")
    return {**state, "signals_classified": classified_count}


def _classify_batch(signals: list[RawSignal]) -> list[ClassifiedSignal]:
    blocks = [
        f"[{i+1}] ID:{s.id}\nTitle:{s.title or ''}\n"
        f"<signal_text>\n{(s.text or '')[:600]}\n</signal_text>"
        for i, s in enumerate(signals)
    ]
    prompt = (
        "Classify each signal using the taxonomy. Return a JSON array. "
        "Each element: id, category, intent_type, classification_confidence, keywords, competitor_mentions.\n\n"
        + "\n\n---\n\n".join(blocks)
    )
    try:
        response = _call_claude(prompt)
        return _parse_response(response, signals)
    except Exception as exc:
        print(f"[classifier] claude error: {exc}")
        return [_fallback(s) for s in signals]


@retry(
    retry=retry_if_exception_type(anthropic.RateLimitError),
    wait=wait_exponential(multiplier=2, min=4, max=60),
    stop=stop_after_attempt(3),
)
def _call_claude(prompt: str) -> str:
    msg = _CLIENT.messages.create(
        model=settings.model_reasoning,
        max_tokens=4096,
        system=_TAXONOMY_SKILL,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def _parse_response(text: str, originals: list[RawSignal]) -> list[ClassifiedSignal]:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1])
    try:
        items = json.loads(text)
    except json.JSONDecodeError:
        return [_fallback(s) for s in originals]
    if not isinstance(items, list):
        items = [items]
    signal_map = {s.id: s for s in originals}
    now = datetime.now(UTC)
    results: list[ClassifiedSignal] = []
    for i, item in enumerate(items):
        signal_id = item.get("id", "")
        raw = signal_map.get(signal_id) or (originals[i] if i < len(originals) else None)
        if raw is None:
            continue
        try:
            category = SignalCategory(item.get("category", "other"))
        except ValueError:
            category = SignalCategory.OTHER
        try:
            intent = IntentType(item.get("intent_type", "unknown"))
        except ValueError:
            intent = IntentType.UNKNOWN
        results.append(
            ClassifiedSignal(
                **raw.model_dump(),
                category=category,
                intent_type=intent,
                classification_confidence=float(item.get("classification_confidence", 0.5)),
                keywords=item.get("keywords", []),
                competitor_mentions=item.get("competitor_mentions", []),
                classified_at=now,
            )
        )
    classified_ids = {r.id for r in results}
    for s in originals:
        if s.id not in classified_ids:
            results.append(_fallback(s))
    return results


def _fallback(s: RawSignal) -> ClassifiedSignal:
    return ClassifiedSignal(
        **s.model_dump(),
        category=SignalCategory.OTHER,
        intent_type=IntentType.UNKNOWN,
        classification_confidence=0.0,
        keywords=[],
        competitor_mentions=[],
        classified_at=datetime.now(UTC),
    )

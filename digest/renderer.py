from __future__ import annotations

import csv
from datetime import UTC, datetime
from pathlib import Path

from schemas.digest import Digest
from schemas.signal import CuratedLead

CSV_COLUMNS = [
    "id",
    "score",
    "tier",
    "category",
    "intent_type",
    "source",
    "geography",
    "title",
    "text_preview",
    "url",
    "match_reason",
    "velocity_delta_24h",
    "velocity_delta_7d",
    "engagement_score",
    "classification_confidence",
    "keywords",
    "competitor_mentions",
    "harvested_at",
    "source_created_at",
]


def render_csv(leads: list[CuratedLead], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sorted_leads = sorted(leads, key=lambda lead: lead.score, reverse=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for lead in sorted_leads:
            writer.writerow(
                {
                    "id": lead.id,
                    "score": lead.score,
                    "tier": lead.tier.value.upper(),
                    "category": lead.category.value,
                    "intent_type": lead.intent_type.value,
                    "source": lead.source.value,
                    "geography": lead.geography or "",
                    "title": (lead.title or "")[:200],
                    "text_preview": (lead.text or "")[:400],
                    "url": lead.url or "",
                    "match_reason": lead.match_reason,
                    "velocity_delta_24h": round(lead.velocity_delta_24h, 2),
                    "velocity_delta_7d": round(lead.velocity_delta_7d, 2),
                    "engagement_score": round(lead.engagement_score, 3),
                    "classification_confidence": round(lead.classification_confidence, 2),
                    "keywords": "|".join(lead.keywords),
                    "competitor_mentions": "|".join(lead.competitor_mentions),
                    "harvested_at": lead.harvested_at.isoformat() if lead.harvested_at else "",
                    "source_created_at": (
                        lead.source_created_at.isoformat() if lead.source_created_at else ""
                    ),
                }
            )


def render_summary_text(digest: Digest, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    s = digest.summary
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    hot = [lead for lead in digest.leads if lead.tier.value == "hot"]
    warm = [lead for lead in digest.leads if lead.tier.value == "warm"]
    lines = [
        "=" * 60,
        "SIGNALHARVEST AI — LEAD DIGEST",
        f"Brand    : {digest.brand_name}",
        f"Run ID   : {digest.run_id}",
        f"Generated: {now}",
        "=" * 60,
        "",
        "SUMMARY",
        "-------",
        f"Total leads    : {s.total_leads}",
        f"  HOT  (>=70)  : {s.hot_count}",
        f"  WARM (40-69) : {s.warm_count}",
        f"  WATCH (<40)  : {s.watch_count}",
        "",
        f"Top categories : {', '.join(s.top_categories[:3]) or 'n/a'}",
        f"Top geographies: {', '.join(s.top_geographies[:3]) or 'n/a'}",
        "",
    ]
    if hot:
        lines += ["HOT LEADS", "---------"]
        for lead in sorted(hot, key=lambda lead: lead.score, reverse=True):
            lines += [
                f"  Score {lead.score} | {lead.category.value} | {lead.source.value}",
                f"  {(lead.title or lead.text[:100] or '')[:120]}",
                f"  Why: {lead.match_reason[:200]}",
                f"  URL: {lead.url or 'n/a'}",
                "",
            ]
    if warm:
        lines += ["WARM LEADS", "----------"]
        for lead in sorted(warm, key=lambda lead: lead.score, reverse=True)[:10]:
            lines += [
                f"  Score {lead.score} | {lead.category.value} | {lead.source.value}",
                f"  {(lead.title or lead.text[:100] or '')[:120]}",
                f"  Why: {lead.match_reason[:200]}",
                "",
            ]
    lines += ["=" * 60, "Full data: see CSV file.", "Powered by SignalHarvest AI", "=" * 60]
    output_path.write_text("\n".join(lines), encoding="utf-8")

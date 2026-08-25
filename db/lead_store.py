from __future__ import annotations

import json
from datetime import datetime

from db.database import db_conn
from schemas.signal import CuratedLead, IntentType, SignalCategory, SignalTier


def save_curated_lead(lead: CuratedLead, run_id: str) -> None:
    with db_conn() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO curated_leads
               (id,signal_id,brand_id,run_id,match_reason,curated_at)
               VALUES (?,?,?,?,?,?)""",
            (
                f"{lead.id}:{lead.brand_id}:{run_id}",
                lead.id,
                lead.brand_id,
                run_id,
                lead.match_reason,
                (lead.curated_at or datetime.now()).isoformat(),
            ),
        )


def _row_to_lead(r: dict) -> CuratedLead:
    try:
        cat = SignalCategory(r["category"]) if r["category"] else SignalCategory.OTHER
        intent = IntentType(r["intent_type"]) if r["intent_type"] else IntentType.UNKNOWN
        tier = SignalTier(r["tier"]) if r["tier"] else SignalTier.WATCH
    except ValueError:
        cat, intent, tier = SignalCategory.OTHER, IntentType.UNKNOWN, SignalTier.WATCH
    return CuratedLead(
        id=r["id"],
        source=r["source"],
        source_id=r["source_id"],
        url=r["url"],
        title=r["title"],
        text=r["text"],
        author=r["author"],
        geography=r["geography"],
        harvested_at=datetime.fromisoformat(r["harvested_at"]),
        source_created_at=(
            datetime.fromisoformat(r["source_created_at"]) if r["source_created_at"] else None
        ),
        raw_metadata=json.loads(r["raw_metadata"] or "{}"),
        category=cat,
        intent_type=intent,
        classification_confidence=r["classification_confidence"] or 0.0,
        keywords=json.loads(r["keywords"] or "[]"),
        competitor_mentions=json.loads(r["competitor_mentions"] or "[]"),
        classified_at=datetime.fromisoformat(r["classified_at"]) if r["classified_at"] else None,
        score=r["score"] or 0,
        tier=tier,
        velocity_delta_24h=r["velocity_delta_24h"] or 0.0,
        velocity_delta_7d=r["velocity_delta_7d"] or 0.0,
        engagement_score=r["engagement_score"] or 0.0,
        scored_at=datetime.fromisoformat(r["scored_at"]) if r["scored_at"] else None,
        brand_id=r["brand_id"],
        match_reason=r["match_reason"],
        curated_at=datetime.fromisoformat(r["curated_at"]) if r["curated_at"] else None,
    )


def list_leads_for_digest(brand_id: str, run_id: str) -> list[CuratedLead]:
    with db_conn() as conn:
        rows = conn.execute(
            """SELECT cl.brand_id, cl.match_reason, cl.curated_at, s.*
               FROM curated_leads cl JOIN signals s ON s.id = cl.signal_id
               WHERE cl.brand_id=? AND cl.run_id=? ORDER BY s.score DESC""",
            (brand_id, run_id),
        ).fetchall()
    return [_row_to_lead(dict(r)) for r in rows]


def list_leads_for_run(run_id: str, limit: int = 500) -> list[CuratedLead]:
    with db_conn() as conn:
        rows = conn.execute(
            """SELECT cl.brand_id, cl.match_reason, cl.curated_at, s.*
               FROM curated_leads cl JOIN signals s ON s.id = cl.signal_id
               WHERE cl.run_id=? ORDER BY s.score DESC LIMIT ?""",
            (run_id, limit),
        ).fetchall()
    return [_row_to_lead(dict(r)) for r in rows]

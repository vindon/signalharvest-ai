from __future__ import annotations

import json
from datetime import datetime

from db.database import db_conn
from schemas.signal import (
    ClassifiedSignal,
    IntentType,
    RawSignal,
    ScoredSignal,
    SignalCategory,
    SignalTier,
)


def _dt(v: datetime | None) -> str | None:
    return v.isoformat() if v else None


def upsert_raw_signal(signal: RawSignal, run_id: str) -> bool:
    with db_conn() as conn:
        cursor = conn.execute(
            """INSERT OR IGNORE INTO signals
               (id,source,source_id,url,title,text,author,geography,
                harvested_at,source_created_at,raw_metadata,run_id)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                signal.id,
                signal.source.value,
                signal.source_id,
                signal.url,
                signal.title,
                signal.text,
                signal.author,
                signal.geography,
                _dt(signal.harvested_at),
                _dt(signal.source_created_at),
                json.dumps(signal.raw_metadata),
                run_id,
            ),
        )
        return cursor.rowcount > 0


def update_classification(signal: ClassifiedSignal) -> None:
    with db_conn() as conn:
        conn.execute(
            """UPDATE signals SET category=?,intent_type=?,classification_confidence=?,
               keywords=?,competitor_mentions=?,classified_at=? WHERE id=?""",
            (
                signal.category.value,
                signal.intent_type.value,
                signal.classification_confidence,
                json.dumps(signal.keywords),
                json.dumps(signal.competitor_mentions),
                _dt(signal.classified_at),
                signal.id,
            ),
        )


def update_score(signal: ScoredSignal) -> None:
    with db_conn() as conn:
        conn.execute(
            """UPDATE signals SET score=?,tier=?,velocity_delta_24h=?,
               velocity_delta_7d=?,engagement_score=?,scored_at=? WHERE id=?""",
            (
                signal.score,
                signal.tier.value,
                signal.velocity_delta_24h,
                signal.velocity_delta_7d,
                signal.engagement_score,
                _dt(signal.scored_at),
                signal.id,
            ),
        )


def fetch_unclassified(run_id: str) -> list[RawSignal]:
    with db_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM signals WHERE run_id=? AND classified_at IS NULL ORDER BY harvested_at ASC",
            (run_id,),
        ).fetchall()
    return [
        RawSignal(
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
        )
        for r in rows
    ]


def fetch_unscored(run_id: str) -> list[ClassifiedSignal]:
    with db_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM signals WHERE run_id=? AND classified_at IS NOT NULL AND scored_at IS NULL",
            (run_id,),
        ).fetchall()
    result = []
    for r in rows:
        try:
            cat = SignalCategory(r["category"]) if r["category"] else SignalCategory.OTHER
            intent = IntentType(r["intent_type"]) if r["intent_type"] else IntentType.UNKNOWN
        except ValueError:
            cat = SignalCategory.OTHER
            intent = IntentType.UNKNOWN
        result.append(
            ClassifiedSignal(
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
                    datetime.fromisoformat(r["source_created_at"])
                    if r["source_created_at"]
                    else None
                ),
                raw_metadata=json.loads(r["raw_metadata"] or "{}"),
                category=cat,
                intent_type=intent,
                classification_confidence=r["classification_confidence"] or 0.0,
                keywords=json.loads(r["keywords"] or "[]"),
                competitor_mentions=json.loads(r["competitor_mentions"] or "[]"),
                classified_at=(
                    datetime.fromisoformat(r["classified_at"]) if r["classified_at"] else None
                ),
            )
        )
    return result


def fetch_scored_by_run(run_id: str, min_score: int = 0) -> list[ScoredSignal]:
    with db_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM signals WHERE run_id=? AND scored_at IS NOT NULL AND score>=? ORDER BY score DESC",
            (run_id, min_score),
        ).fetchall()
    result = []
    for r in rows:
        try:
            cat = SignalCategory(r["category"]) if r["category"] else SignalCategory.OTHER
            intent = IntentType(r["intent_type"]) if r["intent_type"] else IntentType.UNKNOWN
            tier = SignalTier(r["tier"]) if r["tier"] else SignalTier.WATCH
        except ValueError:
            cat, intent, tier = SignalCategory.OTHER, IntentType.UNKNOWN, SignalTier.WATCH
        result.append(
            ScoredSignal(
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
                    datetime.fromisoformat(r["source_created_at"])
                    if r["source_created_at"]
                    else None
                ),
                raw_metadata=json.loads(r["raw_metadata"] or "{}"),
                category=cat,
                intent_type=intent,
                classification_confidence=r["classification_confidence"] or 0.0,
                keywords=json.loads(r["keywords"] or "[]"),
                competitor_mentions=json.loads(r["competitor_mentions"] or "[]"),
                classified_at=(
                    datetime.fromisoformat(r["classified_at"]) if r["classified_at"] else None
                ),
                score=r["score"] or 0,
                tier=tier,
                velocity_delta_24h=r["velocity_delta_24h"] or 0.0,
                velocity_delta_7d=r["velocity_delta_7d"] or 0.0,
                engagement_score=r["engagement_score"] or 0.0,
                scored_at=datetime.fromisoformat(r["scored_at"]) if r["scored_at"] else None,
            )
        )
    return result


def get_historical_volume(category: str, days_back: int = 30) -> list[dict]:
    with db_conn() as conn:
        rows = conn.execute(
            """SELECT date(harvested_at) as day, COUNT(*) as count FROM signals
               WHERE category=? AND harvested_at >= datetime('now', ?)
               GROUP BY date(harvested_at) ORDER BY day ASC""",
            (category, f"-{days_back} days"),
        ).fetchall()
    return [dict(r) for r in rows]


def _row_to_scored(r: dict) -> ScoredSignal:
    try:
        cat = SignalCategory(r["category"]) if r["category"] else SignalCategory.OTHER
        intent = IntentType(r["intent_type"]) if r["intent_type"] else IntentType.UNKNOWN
        tier = SignalTier(r["tier"]) if r["tier"] else SignalTier.WATCH
    except ValueError:
        cat, intent, tier = SignalCategory.OTHER, IntentType.UNKNOWN, SignalTier.WATCH
    return ScoredSignal(
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
    )


def list_recent_signals(
    hours: int = 24,
    category: str | None = None,
    tier: str | None = None,
    source: str | None = None,
    limit: int = 200,
) -> list[ScoredSignal]:
    """Signals across all runs harvested in the last `hours`, newest first —
    powers the frontend's overview/signal-feed views. Includes signals that
    haven't finished classification/scoring yet (category/tier default to
    'other'/'watch' via the row parser) so the feed shows in-progress runs
    too, not just fully-scored ones."""
    clauses = ["harvested_at >= datetime('now', ?)"]
    params: list = [f"-{hours} hours"]
    if category:
        clauses.append("category=?")
        params.append(category)
    if tier:
        clauses.append("tier=?")
        params.append(tier)
    if source:
        clauses.append("source=?")
        params.append(source)
    params.append(limit)
    with db_conn() as conn:
        rows = conn.execute(
            f"SELECT * FROM signals WHERE {' AND '.join(clauses)} "
            f"ORDER BY harvested_at DESC LIMIT ?",
            params,
        ).fetchall()
    return [_row_to_scored(dict(r)) for r in rows]

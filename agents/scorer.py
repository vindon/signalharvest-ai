from __future__ import annotations

from datetime import UTC, datetime

from db.signal_store import fetch_unscored, get_historical_volume, update_score
from schemas.signal import ScoredSignal
from tools.scoring_tool import (
    compute_engagement_score,
    compute_intent_score,
    compute_recency_multiplier,
    compute_total_score,
    compute_velocity_score,
)


def run(state: dict) -> dict:
    run_id = state["run_id"]
    classified_signals = fetch_unscored(run_id)
    if not classified_signals:
        return {**state, "signals_scored": 0}
    now = datetime.now(UTC)
    scored_count = 0
    for signal in classified_signals:
        try:
            historical = get_historical_volume(signal.category.value, days_back=30)
            current_count = sum(1 for s in classified_signals if s.category == signal.category)
            velocity = compute_velocity_score(historical, current_count)
            intent_score = compute_intent_score(
                signal.intent_type.value, signal.classification_confidence
            )
            engagement = compute_engagement_score(signal.source.value, signal.raw_metadata)
            recency = compute_recency_multiplier(signal.harvested_at, signal.source_created_at)
            total = compute_total_score(
                velocity["velocity_score"],
                intent_score,
                engagement["engagement_contribution"],
                recency,
            )
            scored = ScoredSignal(
                **signal.model_dump(),
                score=total,
                velocity_delta_24h=velocity["delta_24h_pct"],
                velocity_delta_7d=velocity["delta_7d_pct"],
                engagement_score=engagement["engagement_normalised"],
                scored_at=now,
            )
            update_score(scored)
            scored_count += 1
        except Exception as exc:
            print(f"[scorer] error {signal.id}: {exc}")
    return {**state, "signals_scored": scored_count}

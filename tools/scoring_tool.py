from __future__ import annotations

from datetime import UTC, datetime


def compute_velocity_score(historical_counts: list[dict], current_count: int) -> dict:
    if not historical_counts:
        return {"delta_24h_pct": 0.0, "delta_7d_pct": 0.0, "velocity_score": 0}
    sorted_counts = sorted(historical_counts, key=lambda x: x["day"])
    values = [r["count"] for r in sorted_counts]
    baseline_1d = max(values[-1] if values else 1, 1)
    recent_7 = values[-7:] if len(values) >= 7 else values
    baseline_7d = max(sum(recent_7) / len(recent_7), 1)
    delta_24h = ((current_count - baseline_1d) / baseline_1d) * 100
    delta_7d = ((current_count - baseline_7d) / baseline_7d) * 100
    raw = min(delta_24h / 50.0, 1.0) if delta_24h > 0 else 0
    velocity_score = int(raw * 30)
    return {
        "delta_24h_pct": round(delta_24h, 2),
        "delta_7d_pct": round(delta_7d, 2),
        "velocity_score": max(0, velocity_score),
    }


def compute_intent_score(intent_type: str, classification_confidence: float) -> int:
    weights = {
        "purchase_ready": 40,
        "churn_risk": 35,
        "complaint": 28,
        "comparison": 22,
        "information": 10,
        "unknown": 0,
    }
    base = weights.get(intent_type, 0)
    return int(base * max(0.5, classification_confidence))


def compute_engagement_score(source: str, raw_metadata: dict) -> dict:
    if source == "reddit":
        score = raw_metadata.get("score", 0)
        num_comments = raw_metadata.get("num_comments", 0)
        upvote_ratio = raw_metadata.get("upvote_ratio", 0.5)
        raw = min((score / 1000.0) * 0.6 + (num_comments / 100.0) * 0.4, 1.0) * upvote_ratio
        return {"engagement_normalised": round(raw, 3), "engagement_contribution": int(raw * 30)}
    if source == "cfpb":
        return {"engagement_normalised": 0.7, "engagement_contribution": 21}
    if source == "google_trends":
        interest = raw_metadata.get("interest_index", 0) / 100.0
        return {
            "engagement_normalised": round(interest, 3),
            "engagement_contribution": int(interest * 30),
        }
    if source == "rss":
        return {"engagement_normalised": 0.3, "engagement_contribution": 9}
    return {"engagement_normalised": 0.0, "engagement_contribution": 0}


def compute_recency_multiplier(
    harvested_at: datetime, source_created_at: datetime | None = None
) -> float:
    reference = source_created_at or harvested_at
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=UTC)
    age_hours = (datetime.now(UTC) - reference).total_seconds() / 3600
    return round(max(0.5, 1.0 - (age_hours / 168.0) * 0.5), 3)


def compute_total_score(
    velocity_score: int, intent_score: int, engagement_contribution: int, recency_multiplier: float
) -> int:
    raw = velocity_score + intent_score + engagement_contribution
    return max(0, min(100, int(raw * recency_multiplier)))

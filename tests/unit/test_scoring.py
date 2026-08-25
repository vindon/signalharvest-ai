from datetime import UTC, datetime, timedelta

import pytest

from tools.scoring_tool import (
    compute_engagement_score,
    compute_intent_score,
    compute_recency_multiplier,
    compute_total_score,
    compute_velocity_score,
)


class TestVelocityScore:
    def test_no_history_zero(self):
        r = compute_velocity_score([], 10)
        assert r["velocity_score"] == 0 and r["delta_24h_pct"] == 0.0

    def test_rising_volume_positive(self):
        r = compute_velocity_score([{"day": "2024-01-01", "count": 10}], 20)
        assert r["delta_24h_pct"] == pytest.approx(100.0, rel=0.1)
        assert r["velocity_score"] > 0

    def test_50_pct_gives_max_velocity(self):
        r = compute_velocity_score([{"day": "2024-01-01", "count": 20}], 30)
        assert r["velocity_score"] == 30

    def test_falling_volume_zero_velocity(self):
        r = compute_velocity_score([{"day": "2024-01-01", "count": 100}], 5)
        assert r["velocity_score"] == 0

    def test_capped_at_30(self):
        r = compute_velocity_score([{"day": "2024-01-01", "count": 1}], 1000)
        assert r["velocity_score"] == 30


class TestIntentScore:
    def test_purchase_ready_full(self):
        assert compute_intent_score("purchase_ready", 1.0) == 40

    def test_purchase_ready_half_confidence(self):
        assert compute_intent_score("purchase_ready", 0.5) == 20

    def test_churn_risk_full(self):
        assert compute_intent_score("churn_risk", 1.0) == 35

    def test_complaint_full(self):
        assert compute_intent_score("complaint", 1.0) == 28

    def test_unknown_zero(self):
        assert compute_intent_score("unknown", 1.0) == 0

    def test_invalid_zero(self):
        assert compute_intent_score("nonexistent", 1.0) == 0


class TestEngagementScore:
    def test_reddit_high(self):
        # score=1000, num_comments=100, upvote_ratio=0.95
        # raw = min((1000/1000)*0.6 + (100/100)*0.4, 1.0) * 0.95 = 1.0 * 0.95 = 0.95
        # contribution = int(0.95 * 30) = 28
        r = compute_engagement_score(
            "reddit", {"score": 1000, "num_comments": 100, "upvote_ratio": 0.95}
        )
        assert r["engagement_contribution"] == 28
        assert r["engagement_normalised"] == pytest.approx(0.95, abs=0.01)

    def test_reddit_zero(self):
        r = compute_engagement_score("reddit", {"score": 0, "num_comments": 0, "upvote_ratio": 0.5})
        assert r["engagement_contribution"] == 0

    def test_cfpb_fixed(self):
        r = compute_engagement_score("cfpb", {})
        assert r["engagement_contribution"] == 21

    def test_trends_max(self):
        r = compute_engagement_score("google_trends", {"interest_index": 100})
        assert r["engagement_contribution"] == 30

    def test_trends_zero(self):
        r = compute_engagement_score("google_trends", {"interest_index": 0})
        assert r["engagement_contribution"] == 0

    def test_rss_fixed(self):
        r = compute_engagement_score("rss", {})
        assert r["engagement_contribution"] == 9

    def test_unknown_zero(self):
        r = compute_engagement_score("unknown", {})
        assert r["engagement_contribution"] == 0


class TestRecencyMultiplier:
    def test_fresh_near_1(self):
        m = compute_recency_multiplier(datetime.now(UTC))
        assert 0.99 <= m <= 1.0

    def test_7d_is_half(self):
        old = datetime.now(UTC) - timedelta(days=7)
        m = compute_recency_multiplier(old)
        assert m == pytest.approx(0.5, abs=0.02)

    def test_older_floors_at_half(self):
        very_old = datetime.now(UTC) - timedelta(days=30)
        assert compute_recency_multiplier(very_old) == 0.5

    def test_uses_source_created_at(self):
        fresh = datetime.now(UTC)
        old = datetime.now(UTC) - timedelta(days=7)
        m = compute_recency_multiplier(fresh, old)
        assert m == pytest.approx(0.5, abs=0.02)


class TestTotalScore:
    def test_max(self):
        assert compute_total_score(30, 40, 30, 1.0) == 100

    def test_zero(self):
        assert compute_total_score(0, 0, 0, 1.0) == 0

    def test_recency_halves(self):
        assert compute_total_score(30, 40, 30, 0.5) == 50

    def test_clamped_at_100(self):
        assert compute_total_score(30, 40, 30, 2.0) == 100

    def test_clamped_at_0(self):
        assert compute_total_score(0, 0, 0, 0.5) == 0

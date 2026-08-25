import pytest

from schemas.brand import BrandSubscription
from schemas.digest import DigestSummary
from schemas.signal import (
    MAX_TEXT_LENGTH,
    CuratedLead,
    IntentType,
    RawSignal,
    ScoredSignal,
    SignalCategory,
    SignalSource,
    SignalTier,
)


class TestRawSignal:
    def test_creates_with_required_fields(self):
        s = RawSignal(source=SignalSource.REDDIT, source_id="abc123", text="switch carrier")
        assert s.source == SignalSource.REDDIT
        assert s.id

    def test_sanitises_html(self):
        s = RawSignal(source=SignalSource.RSS, source_id="x1", text="<p>Hello <b>world</b></p>")
        assert "<p>" not in s.text and "Hello" in s.text

    def test_truncates_text(self):
        s = RawSignal(source=SignalSource.RSS, source_id="x2", text="a" * (MAX_TEXT_LENGTH + 500))
        assert len(s.text) == MAX_TEXT_LENGTH

    def test_collapses_whitespace(self):
        s = RawSignal(
            source=SignalSource.REDDIT, source_id="x4", text="lots   of   spaces\n\nnewlines"
        )
        assert "  " not in s.text

    def test_sanitises_title(self):
        s = RawSignal(source=SignalSource.CFPB, source_id="x3", text="text", title="<h1>Title</h1>")
        assert "<h1>" not in s.title and "Title" in s.title

    def test_optional_fields_default_none(self):
        s = RawSignal(source=SignalSource.GOOGLE_TRENDS, source_id="x5", text="trend")
        assert s.url is None and s.title is None and s.geography is None


class TestScoredSignal:
    def _base(self):
        return dict(
            source=SignalSource.REDDIT,
            source_id="s1",
            text="switch internet",
            category=SignalCategory.HOME_INTERNET,
            intent_type=IntentType.PURCHASE_READY,
            classification_confidence=0.9,
        )

    def test_hot_tier_at_70(self):
        assert ScoredSignal(**self._base(), score=70).tier == SignalTier.HOT

    def test_warm_tier_at_69(self):
        assert ScoredSignal(**self._base(), score=69).tier == SignalTier.WARM

    def test_warm_tier_at_40(self):
        assert ScoredSignal(**self._base(), score=40).tier == SignalTier.WARM

    def test_watch_tier_at_39(self):
        assert ScoredSignal(**self._base(), score=39).tier == SignalTier.WATCH

    def test_watch_tier_at_0(self):
        assert ScoredSignal(**self._base(), score=0).tier == SignalTier.WATCH


class TestBrandSubscription:
    def test_valid_brand(self):
        b = BrandSubscription(
            name="Brand", contact_email="a@b.com", categories=[SignalCategory.TELECOM_MOBILE]
        )
        assert b.active is True

    def test_normalises_email(self):
        b = BrandSubscription(
            name="B", contact_email="TEST@EXAMPLE.COM", categories=[SignalCategory.TELECOM_MOBILE]
        )
        assert b.contact_email == "test@example.com"

    def test_rejects_invalid_email(self):
        with pytest.raises(ValueError):
            BrandSubscription(
                name="B", contact_email="not-email", categories=[SignalCategory.TELECOM_MOBILE]
            )

    def test_rejects_empty_categories(self):
        with pytest.raises(ValueError):
            BrandSubscription(name="B", contact_email="a@b.com", categories=[])

    def test_deduplicates_categories(self):
        b = BrandSubscription(
            name="B",
            contact_email="a@b.com",
            categories=[
                SignalCategory.TELECOM_MOBILE,
                SignalCategory.TELECOM_MOBILE,
                SignalCategory.HOME_INTERNET,
            ],
        )
        assert len(b.categories) == 2

    def test_rejects_invalid_frequency(self):
        with pytest.raises(ValueError):
            BrandSubscription(
                name="B",
                contact_email="a@b.com",
                categories=[SignalCategory.TELECOM_MOBILE],
                digest_frequency="hourly",
            )


class TestDigestSummary:
    def _lead(self, score: int, cat: str = "telecom_mobile") -> CuratedLead:
        return CuratedLead(
            source=SignalSource.REDDIT,
            source_id=f"l{score}",
            text="test",
            category=SignalCategory(cat),
            intent_type=IntentType.COMPLAINT,
            classification_confidence=0.8,
            score=score,
            brand_id="b1",
            match_reason="test",
        )

    def test_summary_counts(self):
        leads = [self._lead(75), self._lead(55), self._lead(30)]
        s = DigestSummary.from_leads(leads)
        assert s.total_leads == 3
        assert s.hot_count == 1
        assert s.warm_count == 1
        assert s.watch_count == 1

    def test_empty(self):
        s = DigestSummary.from_leads([])
        assert s.total_leads == 0

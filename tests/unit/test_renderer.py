import csv

from digest.renderer import render_csv, render_summary_text
from schemas.digest import Digest, DigestSummary
from schemas.signal import CuratedLead, IntentType, SignalCategory, SignalSource


def _lead(score: int = 75, idx: int = 1) -> CuratedLead:
    return CuratedLead(
        source=SignalSource.REDDIT,
        source_id=f"test_{idx}",
        text="Looking to switch broadband provider after billing dispute.",
        title="Help finding ISP alternatives",
        url="https://reddit.com/r/test/123",
        category=SignalCategory.TELECOM_BROADBAND,
        intent_type=IntentType.PURCHASE_READY,
        classification_confidence=0.92,
        score=score,
        velocity_delta_24h=45.5,
        velocity_delta_7d=120.0,
        engagement_score=0.78,
        keywords=["switch", "broadband", "billing"],
        competitor_mentions=["Comcast", "Spectrum"],
        brand_id="brand_abc",
        match_reason="Explicit purchase-ready intent with competitor mentions.",
    )


def _digest(leads: list) -> Digest:
    return Digest(
        run_id="run_test_001",
        brand_id="brand_abc",
        brand_name="Test Brand",
        leads=leads,
        summary=DigestSummary.from_leads(leads),
    )


class TestRenderCSV:
    def test_creates_file(self, tmp_path):
        render_csv([_lead(75, 1), _lead(50, 2)], tmp_path / "d.csv")
        assert (tmp_path / "d.csv").exists()

    def test_has_required_columns(self, tmp_path):
        out = tmp_path / "d.csv"
        render_csv([_lead(75)], out)
        with out.open() as f:
            cols = csv.DictReader(f).fieldnames
        for col in ["score", "tier", "category", "match_reason", "url"]:
            assert col in cols

    def test_sorted_descending(self, tmp_path):
        out = tmp_path / "d.csv"
        render_csv([_lead(40, 1), _lead(90, 2), _lead(60, 3)], out)
        with out.open() as f:
            scores = [int(r["score"]) for r in csv.DictReader(f)]
        assert scores == sorted(scores, reverse=True)

    def test_tier_uppercase(self, tmp_path):
        out = tmp_path / "d.csv"
        render_csv([_lead(75)], out)
        with out.open() as f:
            row = next(csv.DictReader(f))
        assert row["tier"] == row["tier"].upper()

    def test_empty_produces_header_only(self, tmp_path):
        out = tmp_path / "empty.csv"
        render_csv([], out)
        lines = [line for line in out.read_text().strip().split("\n") if line]
        assert len(lines) == 1

    def test_creates_parent_dirs(self, tmp_path):
        out = tmp_path / "nested" / "dir" / "d.csv"
        render_csv([_lead(75)], out)
        assert out.exists()


class TestRenderSummaryText:
    def test_creates_file(self, tmp_path):
        out = tmp_path / "s.txt"
        render_summary_text(_digest([_lead(75, 1), _lead(45, 2)]), out)
        assert out.exists()

    def test_contains_brand_name(self, tmp_path):
        out = tmp_path / "s.txt"
        render_summary_text(_digest([_lead(75)]), out)
        assert "Test Brand" in out.read_text()

    def test_contains_run_id(self, tmp_path):
        out = tmp_path / "s.txt"
        render_summary_text(_digest([_lead(75)]), out)
        assert "run_test_001" in out.read_text()

    def test_hot_leads_section(self, tmp_path):
        out = tmp_path / "s.txt"
        render_summary_text(_digest([_lead(80)]), out)
        assert "HOT LEADS" in out.read_text()

    def test_empty_digest_no_crash(self, tmp_path):
        out = tmp_path / "s.txt"
        render_summary_text(_digest([]), out)
        assert out.exists()

    def test_total_count_present(self, tmp_path):
        out = tmp_path / "s.txt"
        leads = [_lead(80, 1), _lead(55, 2), _lead(20, 3)]
        render_summary_text(_digest(leads), out)
        assert "3" in out.read_text()

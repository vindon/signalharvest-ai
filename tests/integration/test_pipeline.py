"""
Integration tests — real SQLite (temp path), Claude API mocked, ingestors mocked.
Tests end-to-end data flow through DB layer.
"""

from datetime import UTC, datetime
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def temp_env(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    output_dir = tmp_path / "digests"
    log_dir = tmp_path / "logs"
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-0000000000000000")
    monkeypatch.setenv("DATABASE_PATH", str(db_path))
    monkeypatch.setenv("DIGEST_OUTPUT_DIR", str(output_dir))
    monkeypatch.setenv("LOG_FILE", str(log_dir / "test.log"))
    monkeypatch.setenv("CURATOR_MIN_SCORE", "0")

    # config.settings.settings is a pydantic-settings singleton instantiated
    # once at first import — it reads env vars only at that point, so
    # monkeypatch.setenv() above has zero effect on it afterwards. Every
    # integration test was silently reading/writing the *real*
    # data/signalharvest.db and output/digests/ in the project root instead
    # of an isolated tmp_path, for as long as this fixture has existed (only
    # visible once a test actually asserts on cross-run state, which is
    # exactly what test_any_run_in_progress below does). Patch the
    # singleton's own attributes directly — that's what every db/ and
    # digest/ module actually reads at call time.
    from config.settings import settings

    monkeypatch.setattr(settings, "database_path", str(db_path))
    monkeypatch.setattr(settings, "digest_output_dir", str(output_dir))
    monkeypatch.setattr(settings, "log_file", str(log_dir / "test.log"))
    monkeypatch.setattr(settings, "curator_min_score", 0)

    # Also patch the module-level DB path used by database.py's except-path,
    # even though _get_db_path()'s try branch (settings.database_path_obj)
    # is what actually gets hit — this keeps the fallback correct too.
    import db.database as db_mod

    monkeypatch.setattr(db_mod, "_DB_PATH", db_path)
    db_mod.init_db()
    yield tmp_path


class TestSentinelAgent:
    def test_runs_with_no_sources(self):
        from agents import sentinel

        with patch("agents.sentinel.harvest_reddit", return_value=[]):
            with patch("agents.sentinel.harvest_trends", return_value=[]):
                with patch("agents.sentinel.harvest_cfpb", return_value=[]):
                    with patch("agents.sentinel.harvest_rss", return_value=[]):
                        result = sentinel.run({"run_id": "test_001"})
        assert result["signals_harvested"] == 0

    def test_persists_signals(self):
        from agents import sentinel
        from schemas.signal import RawSignal, SignalSource

        sig = RawSignal(
            source=SignalSource.CFPB,
            source_id="cfpb_001",
            text="Billing complaint against mobile carrier.",
        )
        with patch("agents.sentinel.harvest_reddit", return_value=[]):
            with patch("agents.sentinel.harvest_trends", return_value=[]):
                with patch("agents.sentinel.harvest_cfpb", return_value=[sig]):
                    with patch("agents.sentinel.harvest_rss", return_value=[]):
                        result = sentinel.run({"run_id": "test_002"})
        assert result["signals_harvested"] == 1

    def test_deduplicates(self):
        from agents import sentinel
        from schemas.signal import RawSignal, SignalSource

        sig = RawSignal(source=SignalSource.CFPB, source_id="cfpb_dup", text="Duplicate signal.")
        with patch("agents.sentinel.harvest_reddit", return_value=[]):
            with patch("agents.sentinel.harvest_trends", return_value=[]):
                with patch("agents.sentinel.harvest_cfpb", return_value=[sig, sig]):
                    with patch("agents.sentinel.harvest_rss", return_value=[]):
                        result = sentinel.run({"run_id": "test_003"})
        assert result["signals_harvested"] == 1


class TestScorerAgent:
    def test_scores_classified_signals(self):
        from agents import scorer
        from db.signal_store import fetch_scored_by_run, update_classification, upsert_raw_signal
        from schemas.signal import (
            ClassifiedSignal,
            IntentType,
            RawSignal,
            SignalCategory,
            SignalSource,
        )

        run_id = "score_test_001"
        sig = RawSignal(
            source=SignalSource.CFPB,
            source_id="score_001",
            text="Terrible billing. Want to switch.",
        )
        upsert_raw_signal(sig, run_id)
        classified = ClassifiedSignal(
            **sig.model_dump(),
            category=SignalCategory.TELECOM_BILLING,
            intent_type=IntentType.PURCHASE_READY,
            classification_confidence=0.95,
            keywords=["billing", "switch"],
            competitor_mentions=[],
            classified_at=datetime.now(UTC),
        )
        update_classification(classified)
        result = scorer.run({"run_id": run_id, "signals_harvested": 1, "signals_classified": 1})
        assert result["signals_scored"] == 1
        scored = fetch_scored_by_run(run_id, min_score=0)
        assert len(scored) == 1
        assert 0 <= scored[0].score <= 100


class TestBrandStore:
    def test_upsert_and_retrieve(self):
        from db.brand_store import get_active_brands, upsert_brand
        from schemas.brand import BrandSubscription
        from schemas.signal import SignalCategory, SignalTier

        brand = BrandSubscription(
            name="Integration Brand",
            contact_email="t@test.com",
            categories=[SignalCategory.TELECOM_MOBILE, SignalCategory.HOME_INTERNET],
            min_tier=SignalTier.WARM,
        )
        upsert_brand(brand)
        brands = get_active_brands()
        found = next((b for b in brands if b.name == "Integration Brand"), None)
        assert found is not None
        assert SignalCategory.TELECOM_MOBILE in found.categories

    def test_inactive_brand_excluded(self):
        from db.brand_store import get_active_brands, upsert_brand
        from schemas.brand import BrandSubscription
        from schemas.signal import SignalCategory

        brand = BrandSubscription(
            name="Inactive",
            contact_email="x@x.com",
            categories=[SignalCategory.FINTECH_CREDIT_CARD],
            active=False,
        )
        upsert_brand(brand)
        names = [b.name for b in get_active_brands()]
        assert "Inactive" not in names


class TestRendererIntegration:
    def test_full_render(self, tmp_path):
        from digest.renderer import render_csv, render_summary_text
        from schemas.digest import Digest, DigestSummary
        from schemas.signal import CuratedLead, IntentType, SignalCategory, SignalSource

        lead = CuratedLead(
            source=SignalSource.CFPB,
            source_id="int_001",
            text="Billing complaint, switching provider.",
            category=SignalCategory.TELECOM_BILLING,
            intent_type=IntentType.CHURN_RISK,
            classification_confidence=0.88,
            score=72,
            keywords=["billing", "switch"],
            competitor_mentions=["Comcast"],
            brand_id="b1",
            match_reason="High-intent churn signal.",
        )
        digest = Digest(
            run_id="int_run_001",
            brand_id="b1",
            brand_name="Int Brand",
            leads=[lead],
            summary=DigestSummary.from_leads([lead]),
        )
        csv_p = tmp_path / "d.csv"
        txt_p = tmp_path / "s.txt"
        render_csv([lead], csv_p)
        render_summary_text(digest, txt_p)
        assert csv_p.exists() and csv_p.stat().st_size > 0
        assert "Int Brand" in txt_p.read_text()


class TestStateStore:
    def test_save_and_load_state(self):
        from db.state_store import load_state, save_state

        state = {"run_id": "st_001", "signals_harvested": 5, "curated_leads": []}
        save_state("st_001", state)
        loaded = load_state("st_001")
        assert loaded is not None
        assert loaded["signals_harvested"] == 5

    def test_load_missing_returns_none(self):
        from db.state_store import load_state

        assert load_state("nonexistent_run_id_xyz") is None

    def test_list_runs_and_get_run(self):
        from db.state_store import get_run, list_runs, save_pipeline_run
        from schemas.digest import PipelineRun

        run = PipelineRun(id="list_run_001", status="completed")
        save_pipeline_run(run)
        runs = list_runs(limit=10)
        assert any(r["id"] == "list_run_001" for r in runs)
        fetched = get_run("list_run_001")
        assert fetched is not None
        assert fetched["status"] == "completed"

    def test_any_run_in_progress(self):
        from db.state_store import any_run_in_progress, save_pipeline_run
        from schemas.digest import PipelineRun

        assert any_run_in_progress() is False
        save_pipeline_run(PipelineRun(id="running_run_001", status="running"))
        assert any_run_in_progress() is True


class TestLeadStore:
    def test_save_and_list_leads_for_digest(self):
        from db.brand_store import upsert_brand
        from db.lead_store import list_leads_for_digest, list_leads_for_run, save_curated_lead
        from db.signal_store import update_classification, update_score, upsert_raw_signal
        from schemas.brand import BrandSubscription
        from schemas.signal import (
            ClassifiedSignal,
            CuratedLead,
            IntentType,
            RawSignal,
            ScoredSignal,
            SignalCategory,
            SignalSource,
        )

        run_id = "lead_test_run"
        upsert_brand(
            BrandSubscription(
                id="brand_001",
                name="Brand 1",
                contact_email="b1@test.com",
                categories=[SignalCategory.TELECOM_MOBILE],
            )
        )
        sig = RawSignal(
            source=SignalSource.REDDIT,
            source_id="lead_001",
            text="Switching mobile carriers, current one overcharges.",
        )
        upsert_raw_signal(sig, run_id)
        classified = ClassifiedSignal(
            **sig.model_dump(),
            category=SignalCategory.TELECOM_MOBILE,
            intent_type=IntentType.CHURN_RISK,
            classification_confidence=0.9,
        )
        update_classification(classified)
        scored = ScoredSignal(**classified.model_dump(), score=80)
        update_score(scored)
        lead = CuratedLead(
            **scored.model_dump(),
            brand_id="brand_001",
            match_reason="High-intent churn signal in telecom_mobile.",
        )
        save_curated_lead(lead, run_id)

        by_digest = list_leads_for_digest("brand_001", run_id)
        assert len(by_digest) == 1
        assert by_digest[0].match_reason == "High-intent churn signal in telecom_mobile."
        assert by_digest[0].score == 80

        by_run = list_leads_for_run(run_id)
        assert len(by_run) == 1

    def test_idempotent_resave(self):
        from db.brand_store import upsert_brand
        from db.lead_store import list_leads_for_digest, save_curated_lead
        from db.signal_store import update_classification, update_score, upsert_raw_signal
        from schemas.brand import BrandSubscription
        from schemas.signal import (
            ClassifiedSignal,
            CuratedLead,
            IntentType,
            RawSignal,
            ScoredSignal,
            SignalCategory,
            SignalSource,
        )

        run_id = "lead_test_run_2"
        upsert_brand(
            BrandSubscription(
                id="brand_002",
                name="Brand 2",
                contact_email="b2@test.com",
                categories=[SignalCategory.OTHER],
            )
        )
        sig = RawSignal(source=SignalSource.RSS, source_id="lead_002", text="Another signal.")
        upsert_raw_signal(sig, run_id)
        classified = ClassifiedSignal(
            **sig.model_dump(), category=SignalCategory.OTHER, intent_type=IntentType.UNKNOWN
        )
        update_classification(classified)
        scored = ScoredSignal(**classified.model_dump(), score=50)
        update_score(scored)
        lead = CuratedLead(**scored.model_dump(), brand_id="brand_002", match_reason="v1")
        save_curated_lead(lead, run_id)
        lead2 = CuratedLead(**scored.model_dump(), brand_id="brand_002", match_reason="v2")
        save_curated_lead(lead2, run_id)
        leads = list_leads_for_digest("brand_002", run_id)
        assert len(leads) == 1
        assert leads[0].match_reason == "v2"


class TestDigestStore:
    def test_list_and_get_digest(self):
        from db.database import db_conn
        from db.digest_store import get_digest, list_digests

        with db_conn() as conn:
            conn.execute(
                """INSERT INTO digests (id,run_id,brand_id,brand_name,lead_count,
                   summary_json,status,output_path,generated_at,delivered_at,error_message)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    "digest_001",
                    "run_001",
                    "brand_001",
                    "Test Brand",
                    3,
                    "{}",
                    "delivered",
                    "/tmp/x.csv",
                    "2026-01-01T00:00:00+00:00",
                    None,
                    None,
                ),
            )
        digests = list_digests(brand_id="brand_001")
        assert len(digests) == 1
        assert digests[0]["brand_name"] == "Test Brand"
        fetched = get_digest("digest_001")
        assert fetched is not None
        assert fetched["lead_count"] == 3


class TestPublisherPersistsLeads:
    def test_publisher_saves_curated_leads_to_db(self, tmp_path):
        from agents import publisher
        from db.brand_store import upsert_brand
        from db.lead_store import list_leads_for_digest
        from db.signal_store import update_classification, update_score, upsert_raw_signal
        from schemas.brand import BrandSubscription
        from schemas.signal import (
            ClassifiedSignal,
            CuratedLead,
            IntentType,
            RawSignal,
            ScoredSignal,
            SignalCategory,
            SignalSource,
        )

        brand = BrandSubscription(
            id="pub_brand_001",
            name="Publisher Brand",
            contact_email="p@test.com",
            categories=[SignalCategory.TELECOM_MOBILE],
        )
        upsert_brand(brand)

        # In the real pipeline, curator only ever builds a CuratedLead from a
        # signal already in the signals table (via fetch_scored_by_run), so
        # the row must exist here too for the FK on curated_leads to hold.
        sig = RawSignal(
            source=SignalSource.REDDIT,
            source_id="pub_sig_001",
            text="Ready to switch carriers today.",
        )
        upsert_raw_signal(sig, "pub_run_001")
        classified = ClassifiedSignal(
            **sig.model_dump(),
            category=SignalCategory.TELECOM_MOBILE,
            intent_type=IntentType.PURCHASE_READY,
            classification_confidence=0.9,
        )
        update_classification(classified)
        scored = ScoredSignal(**classified.model_dump(), score=75)
        update_score(scored)

        lead = CuratedLead(
            **scored.model_dump(), brand_id="pub_brand_001", match_reason="Purchase-ready signal."
        )

        state = {"run_id": "pub_run_001", "curated_leads": [lead.model_dump()]}
        result = publisher.run(state)

        assert result["digests_generated"] == 1
        saved = list_leads_for_digest("pub_brand_001", "pub_run_001")
        assert len(saved) == 1
        assert saved[0].match_reason == "Purchase-ready signal."

    def test_save_pipeline_run(self):
        from db.state_store import get_last_run, save_pipeline_run
        from schemas.digest import PipelineRun

        run = PipelineRun(
            signals_harvested=10,
            signals_classified=8,
            signals_scored=8,
            leads_curated=3,
            digests_generated=1,
            digests_delivered=1,
            status="completed",
            completed_at=datetime.now(UTC),
        )
        save_pipeline_run(run)
        last = get_last_run()
        assert last is not None
        assert last["signals_harvested"] == 10

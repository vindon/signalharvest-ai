from __future__ import annotations

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

_DB_PATH: Path = Path("./data/signalharvest.db")


def _get_db_path() -> Path:
    try:
        from config.settings import settings

        return settings.database_path_obj
    except Exception:
        return _DB_PATH


def get_connection() -> sqlite3.Connection:
    db_path = _get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


@contextmanager
def db_conn() -> Generator[sqlite3.Connection, None, None]:
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS signals (
    id TEXT PRIMARY KEY, source TEXT NOT NULL, source_id TEXT NOT NULL,
    url TEXT, title TEXT, text TEXT NOT NULL, author TEXT, geography TEXT,
    harvested_at TEXT NOT NULL, source_created_at TEXT, raw_metadata TEXT DEFAULT '{}',
    category TEXT, intent_type TEXT, classification_confidence REAL DEFAULT 0.0,
    keywords TEXT DEFAULT '[]', competitor_mentions TEXT DEFAULT '[]', classified_at TEXT,
    score INTEGER DEFAULT 0, tier TEXT DEFAULT 'watch',
    velocity_delta_24h REAL DEFAULT 0.0, velocity_delta_7d REAL DEFAULT 0.0,
    engagement_score REAL DEFAULT 0.0, scored_at TEXT, run_id TEXT,
    UNIQUE(source, source_id)
);
CREATE INDEX IF NOT EXISTS idx_signals_run_id ON signals(run_id);
CREATE INDEX IF NOT EXISTS idx_signals_category ON signals(category);
CREATE INDEX IF NOT EXISTS idx_signals_score ON signals(score DESC);

CREATE TABLE IF NOT EXISTS brands (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, contact_email TEXT NOT NULL,
    categories TEXT NOT NULL DEFAULT '[]', geographies TEXT DEFAULT '[]',
    min_tier TEXT DEFAULT 'warm', keywords_include TEXT DEFAULT '[]',
    keywords_exclude TEXT DEFAULT '[]', competitor_brands TEXT DEFAULT '[]',
    digest_frequency TEXT DEFAULT 'daily', approval_required INTEGER DEFAULT 0,
    active INTEGER DEFAULT 1, created_at TEXT NOT NULL, updated_at TEXT
);

CREATE TABLE IF NOT EXISTS curated_leads (
    id TEXT PRIMARY KEY, signal_id TEXT NOT NULL REFERENCES signals(id),
    brand_id TEXT NOT NULL REFERENCES brands(id), run_id TEXT NOT NULL,
    match_reason TEXT NOT NULL, curated_at TEXT NOT NULL,
    UNIQUE(signal_id, brand_id, run_id)
);
CREATE INDEX IF NOT EXISTS idx_leads_brand_run ON curated_leads(brand_id, run_id);

CREATE TABLE IF NOT EXISTS digests (
    id TEXT PRIMARY KEY, run_id TEXT NOT NULL, brand_id TEXT NOT NULL,
    brand_name TEXT NOT NULL, lead_count INTEGER DEFAULT 0,
    summary_json TEXT DEFAULT '{}', status TEXT DEFAULT 'pending',
    output_path TEXT, generated_at TEXT NOT NULL, delivered_at TEXT, error_message TEXT
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    id TEXT PRIMARY KEY, started_at TEXT NOT NULL, completed_at TEXT,
    signals_harvested INTEGER DEFAULT 0, signals_classified INTEGER DEFAULT 0,
    signals_scored INTEGER DEFAULT 0, leads_curated INTEGER DEFAULT 0,
    digests_generated INTEGER DEFAULT 0, digests_delivered INTEGER DEFAULT 0,
    status TEXT DEFAULT 'running', error_message TEXT
);

CREATE TABLE IF NOT EXISTS agent_state (
    run_id TEXT PRIMARY KEY, state_json TEXT NOT NULL, updated_at TEXT NOT NULL
);
"""


def init_db() -> None:
    db_path = _get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with db_conn() as conn:
        conn.executescript(SCHEMA_SQL)

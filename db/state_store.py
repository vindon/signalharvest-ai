from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from db.database import db_conn
from schemas.digest import PipelineRun


def save_state(run_id: str, state: dict[str, Any]) -> None:
    now = datetime.now(UTC).isoformat()
    with db_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO agent_state (run_id,state_json,updated_at) VALUES (?,?,?)",
            (run_id, json.dumps(state, default=str), now),
        )


def load_state(run_id: str) -> dict[str, Any] | None:
    with db_conn() as conn:
        row = conn.execute(
            "SELECT state_json FROM agent_state WHERE run_id=?", (run_id,)
        ).fetchone()
    return json.loads(row["state_json"]) if row else None


def save_pipeline_run(run: PipelineRun) -> None:
    with db_conn() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO pipeline_runs
               (id,started_at,completed_at,signals_harvested,signals_classified,
                signals_scored,leads_curated,digests_generated,digests_delivered,
                status,error_message) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                run.id,
                run.started_at.isoformat(),
                run.completed_at.isoformat() if run.completed_at else None,
                run.signals_harvested,
                run.signals_classified,
                run.signals_scored,
                run.leads_curated,
                run.digests_generated,
                run.digests_delivered,
                run.status,
                run.error_message,
            ),
        )


def get_last_run() -> dict | None:
    with db_conn() as conn:
        row = conn.execute(
            "SELECT * FROM pipeline_runs WHERE status='completed' ORDER BY started_at DESC LIMIT 1"
        ).fetchone()
    return dict(row) if row else None


def get_run(run_id: str) -> dict | None:
    with db_conn() as conn:
        row = conn.execute("SELECT * FROM pipeline_runs WHERE id=?", (run_id,)).fetchone()
    return dict(row) if row else None


def list_runs(limit: int = 20) -> list[dict]:
    with db_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM pipeline_runs ORDER BY started_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def any_run_in_progress() -> bool:
    with db_conn() as conn:
        row = conn.execute("SELECT 1 FROM pipeline_runs WHERE status='running' LIMIT 1").fetchone()
    return row is not None

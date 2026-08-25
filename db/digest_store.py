from __future__ import annotations

import json

from db.database import db_conn


def _row_to_dict(r: dict) -> dict:
    return {
        "id": r["id"],
        "run_id": r["run_id"],
        "brand_id": r["brand_id"],
        "brand_name": r["brand_name"],
        "lead_count": r["lead_count"],
        "summary": json.loads(r["summary_json"] or "{}"),
        "status": r["status"],
        "output_path": r["output_path"],
        "generated_at": r["generated_at"],
        "delivered_at": r["delivered_at"],
        "error_message": r["error_message"],
    }


def list_digests(brand_id: str | None = None, limit: int = 50) -> list[dict]:
    with db_conn() as conn:
        if brand_id:
            rows = conn.execute(
                "SELECT * FROM digests WHERE brand_id=? ORDER BY generated_at DESC LIMIT ?",
                (brand_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM digests ORDER BY generated_at DESC LIMIT ?", (limit,)
            ).fetchall()
    return [_row_to_dict(dict(r)) for r in rows]


def get_digest(digest_id: str) -> dict | None:
    with db_conn() as conn:
        row = conn.execute("SELECT * FROM digests WHERE id=?", (digest_id,)).fetchone()
    return _row_to_dict(dict(row)) if row else None

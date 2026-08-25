from __future__ import annotations

import json
from collections import defaultdict
from datetime import UTC, datetime

from config.settings import settings
from db.brand_store import get_brand_by_id
from db.database import db_conn
from db.lead_store import save_curated_lead
from digest.renderer import render_csv, render_summary_text
from schemas.digest import Digest, DigestStatus, DigestSummary
from schemas.signal import CuratedLead


def run(state: dict) -> dict:
    run_id = state["run_id"]
    raw_leads = state.get("curated_leads", [])
    if not raw_leads:
        return {**state, "digests_generated": 0, "digests_delivered": 0}
    leads = [CuratedLead(**r) for r in raw_leads]
    by_brand: dict[str, list[CuratedLead]] = defaultdict(list)
    for lead in leads:
        by_brand[lead.brand_id].append(lead)
    output_dir = settings.digest_output_path
    output_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now(UTC).strftime("%Y%m%d")
    generated = delivered = 0
    for brand_id, brand_leads in by_brand.items():
        brand = get_brand_by_id(brand_id)
        if brand is None:
            continue
        summary = DigestSummary.from_leads(brand_leads)
        digest = Digest(
            run_id=run_id,
            brand_id=brand_id,
            brand_name=brand.name,
            leads=brand_leads,
            summary=summary,
        )
        for lead in brand_leads:
            save_curated_lead(lead, run_id)
        safe_name = brand.name.lower().replace(" ", "_").replace("/", "_")
        csv_path = output_dir / f"{safe_name}_{today}_{run_id[:8]}.csv"
        txt_path = output_dir / f"{safe_name}_{today}_{run_id[:8]}_summary.txt"
        try:
            render_csv(brand_leads, csv_path)
            render_summary_text(digest, txt_path)
            digest.output_path = str(csv_path)
            generated += 1
            if brand.approval_required:
                digest.status = DigestStatus.PENDING
            else:
                digest.status = DigestStatus.DELIVERED
                digest.delivered_at = datetime.now(UTC)
                delivered += 1
        except Exception as exc:
            digest.status = DigestStatus.FAILED
            digest.error_message = str(exc)
        _save_digest(digest)
    return {**state, "digests_generated": generated, "digests_delivered": delivered}


def _save_digest(digest: Digest) -> None:
    with db_conn() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO digests
               (id,run_id,brand_id,brand_name,lead_count,summary_json,status,
                output_path,generated_at,delivered_at,error_message)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                digest.id,
                digest.run_id,
                digest.brand_id,
                digest.brand_name,
                len(digest.leads),
                json.dumps(digest.summary.model_dump()),
                digest.status.value,
                digest.output_path,
                digest.generated_at.isoformat(),
                digest.delivered_at.isoformat() if digest.delivered_at else None,
                digest.error_message,
            ),
        )

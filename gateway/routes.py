from __future__ import annotations

import asyncio
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field

from db.brand_store import delete_brand, get_all_brands, get_brand_by_id, upsert_brand
from db.digest_store import get_digest, list_digests
from db.lead_store import list_leads_for_digest
from db.signal_store import list_recent_signals
from db.state_store import any_run_in_progress, get_run, list_runs, load_state
from gateway.auth import require_api_key
from gateway.limiter import limiter
from schemas.brand import BrandSubscription

router = APIRouter(prefix="/api/v1")


# ── Pipeline endpoints ──────────────────────────────────────────────────────


@router.post("/pipeline/run", dependencies=[Depends(require_api_key)])
@limiter.limit("5/minute")
async def trigger_pipeline_run(request: Request) -> dict[str, Any]:
    """Kick off a full pipeline run in the background and return immediately.

    run_pipeline() is synchronous and can take a while (multiple sequential
    LLM calls across Classifier and Curator, plus network scraping in
    Sentinel) — it runs in a worker thread via asyncio.to_thread so it never
    blocks the event loop, and only one run is allowed at a time since they
    all share one SQLite file.
    """
    if any_run_in_progress():
        raise HTTPException(status_code=409, detail="A pipeline run is already in progress")

    run_id = str(uuid4())
    from agents.coordinator import run_pipeline

    asyncio.create_task(asyncio.to_thread(run_pipeline, run_id))
    return {"run_id": run_id, "status": "started"}


@router.get("/pipeline/runs", dependencies=[Depends(require_api_key)])
async def get_runs(limit: int = Query(20, ge=1, le=100)) -> dict[str, Any]:
    return {"runs": list_runs(limit=limit)}


@router.get("/pipeline/runs/{run_id}", dependencies=[Depends(require_api_key)])
async def get_run_detail(run_id: str) -> dict[str, Any]:
    run = get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return run


@router.get("/pipeline/runs/{run_id}/state", dependencies=[Depends(require_api_key)])
async def get_run_state(run_id: str) -> dict[str, Any]:
    """Live per-stage counters while a run is in progress — coordinator.py
    saves the LangGraph state after every node, so this reflects real-time
    progress (pipeline_runs itself only gets a start snapshot and an end
    snapshot, not one per stage)."""
    state = load_state(run_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"No state for run {run_id}")
    return {
        "run_id": run_id,
        "signals_harvested": state.get("signals_harvested", 0),
        "signals_classified": state.get("signals_classified", 0),
        "signals_scored": state.get("signals_scored", 0),
        "leads_curated": state.get("leads_curated", 0),
        "digests_generated": state.get("digests_generated", 0),
        "digests_delivered": state.get("digests_delivered", 0),
        "error": state.get("error") or None,
    }


# ── Signal endpoints ─────────────────────────────────────────────────────────


@router.get("/signals", dependencies=[Depends(require_api_key)])
async def get_signals(
    hours: int = Query(24, ge=1, le=168),
    category: str | None = Query(None),
    tier: str | None = Query(None),
    source: str | None = Query(None),
    limit: int = Query(200, ge=1, le=500),
) -> dict[str, Any]:
    signals = list_recent_signals(
        hours=hours, category=category, tier=tier, source=source, limit=limit
    )
    return {"signals": [s.model_dump(mode="json") for s in signals], "count": len(signals)}


# ── Brand endpoints ──────────────────────────────────────────────────────────


class BrandCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    contact_email: str
    categories: list[str] = Field(min_length=1)
    geographies: list[str] = Field(default_factory=list)
    min_tier: str = "warm"
    keywords_include: list[str] = Field(default_factory=list)
    keywords_exclude: list[str] = Field(default_factory=list)
    competitor_brands: list[str] = Field(default_factory=list)
    digest_frequency: str = "daily"
    approval_required: bool = False


class BrandUpdateRequest(BaseModel):
    name: str | None = None
    contact_email: str | None = None
    categories: list[str] | None = None
    geographies: list[str] | None = None
    min_tier: str | None = None
    keywords_include: list[str] | None = None
    keywords_exclude: list[str] | None = None
    competitor_brands: list[str] | None = None
    digest_frequency: str | None = None
    approval_required: bool | None = None
    active: bool | None = None


@router.get("/brands", dependencies=[Depends(require_api_key)])
async def get_brands() -> dict[str, Any]:
    brands = get_all_brands()
    return {"brands": [b.model_dump(mode="json") for b in brands], "count": len(brands)}


@router.post("/brands", dependencies=[Depends(require_api_key)])
async def create_brand(req: BrandCreateRequest) -> dict[str, Any]:
    from datetime import UTC, datetime

    brand = BrandSubscription(
        name=req.name,
        contact_email=req.contact_email,
        categories=req.categories,  # type: ignore[arg-type]
        geographies=req.geographies,
        min_tier=req.min_tier,  # type: ignore[arg-type]
        keywords_include=req.keywords_include,
        keywords_exclude=req.keywords_exclude,
        competitor_brands=req.competitor_brands,
        digest_frequency=req.digest_frequency,
        approval_required=req.approval_required,
        created_at=datetime.now(UTC),
    )
    upsert_brand(brand)
    return brand.model_dump(mode="json")


@router.patch("/brands/{brand_id}", dependencies=[Depends(require_api_key)])
async def update_brand(brand_id: str, req: BrandUpdateRequest) -> dict[str, Any]:
    from datetime import UTC, datetime

    existing = get_brand_by_id(brand_id)
    if existing is None:
        raise HTTPException(status_code=404, detail=f"Brand {brand_id} not found")
    updates = req.model_dump(exclude_unset=True)
    merged = existing.model_dump()
    merged.update(updates)
    merged["updated_at"] = datetime.now(UTC)
    updated = BrandSubscription(**merged)
    upsert_brand(updated)
    return updated.model_dump(mode="json")


@router.delete("/brands/{brand_id}", dependencies=[Depends(require_api_key)])
async def remove_brand(brand_id: str) -> dict[str, Any]:
    deleted = delete_brand(brand_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Brand {brand_id} not found")
    return {"deleted": True, "brand_id": brand_id}


# ── Digest endpoints ─────────────────────────────────────────────────────────


@router.get("/digests", dependencies=[Depends(require_api_key)])
async def get_digests(
    brand_id: str | None = Query(None), limit: int = Query(50, ge=1, le=200)
) -> dict[str, Any]:
    digests = list_digests(brand_id=brand_id, limit=limit)
    return {"digests": digests, "count": len(digests)}


@router.get("/digests/{digest_id}", dependencies=[Depends(require_api_key)])
async def get_digest_detail(digest_id: str) -> dict[str, Any]:
    digest = get_digest(digest_id)
    if digest is None:
        raise HTTPException(status_code=404, detail=f"Digest {digest_id} not found")
    leads = list_leads_for_digest(digest["brand_id"], digest["run_id"])
    return {**digest, "leads": [lead.model_dump(mode="json") for lead in leads]}


@router.get("/digests/{digest_id}/download", dependencies=[Depends(require_api_key)])
async def download_digest(digest_id: str) -> Response:
    digest = get_digest(digest_id)
    if digest is None:
        raise HTTPException(status_code=404, detail=f"Digest {digest_id} not found")
    leads = list_leads_for_digest(digest["brand_id"], digest["run_id"])
    import csv
    import io

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "score",
            "tier",
            "category",
            "intent_type",
            "source",
            "title",
            "text",
            "url",
            "geography",
            "match_reason",
            "harvested_at",
        ]
    )
    for lead in leads:
        writer.writerow(
            [
                lead.score,
                lead.tier.value,
                lead.category.value,
                lead.intent_type.value,
                lead.source.value,
                lead.title or "",
                lead.text,
                lead.url or "",
                lead.geography or "",
                lead.match_reason,
                lead.harvested_at.isoformat(),
            ]
        )
    safe_name = digest_id.replace("/", "_")
    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="digest_{safe_name}.csv"'},
    )

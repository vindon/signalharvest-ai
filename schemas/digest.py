from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field

from .signal import CuratedLead, SignalTier


class DigestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DELIVERED = "delivered"
    FAILED = "failed"
    SKIPPED = "skipped"


class DigestSummary(BaseModel):
    total_leads: int = 0
    hot_count: int = 0
    warm_count: int = 0
    watch_count: int = 0
    top_categories: list[str] = Field(default_factory=list)
    top_geographies: list[str] = Field(default_factory=list)

    @classmethod
    def from_leads(cls, leads: list[CuratedLead]) -> DigestSummary:
        tier_counts = Counter(lead.tier for lead in leads)
        categories = Counter(lead.category.value for lead in leads)
        geos = Counter(lead.geography for lead in leads if lead.geography)
        return cls(
            total_leads=len(leads),
            hot_count=tier_counts.get(SignalTier.HOT, 0),
            warm_count=tier_counts.get(SignalTier.WARM, 0),
            watch_count=tier_counts.get(SignalTier.WATCH, 0),
            top_categories=[cat for cat, _ in categories.most_common(5)],
            top_geographies=[geo for geo, _ in geos.most_common(5)],
        )


class Digest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    run_id: str
    brand_id: str
    brand_name: str
    leads: list[CuratedLead]
    summary: DigestSummary
    status: DigestStatus = DigestStatus.PENDING
    output_path: str | None = None
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    delivered_at: datetime | None = None
    error_message: str | None = None


class PipelineRun(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    signals_harvested: int = 0
    signals_classified: int = 0
    signals_scored: int = 0
    leads_curated: int = 0
    digests_generated: int = 0
    digests_delivered: int = 0
    status: str = "running"
    error_message: str | None = None

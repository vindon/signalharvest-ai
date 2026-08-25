from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

from .signal import SignalCategory, SignalTier


class BrandSubscription(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(min_length=1, max_length=200)
    contact_email: str
    categories: list[SignalCategory] = Field(min_length=1)
    geographies: list[str] = Field(default_factory=list)
    min_tier: SignalTier = SignalTier.WARM
    keywords_include: list[str] = Field(default_factory=list)
    keywords_exclude: list[str] = Field(default_factory=list)
    competitor_brands: list[str] = Field(default_factory=list)
    digest_frequency: str = Field(default="daily")
    approval_required: bool = False
    active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None

    @field_validator("digest_frequency")
    @classmethod
    def validate_frequency(cls, v: str) -> str:
        if v not in {"daily", "weekly"}:
            raise ValueError("digest_frequency must be 'daily' or 'weekly'")
        return v

    @field_validator("categories")
    @classmethod
    def deduplicate_categories(cls, v: list[SignalCategory]) -> list[SignalCategory]:
        seen: set = set()
        result = []
        for item in v:
            if item not in seen:
                seen.add(item)
                result.append(item)
        return result

    @field_validator("contact_email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("contact_email must be a valid email address")
        return v.lower().strip()

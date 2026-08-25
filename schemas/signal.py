from __future__ import annotations

import re
from datetime import UTC, datetime
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator


class SignalSource(str, Enum):
    REDDIT = "reddit"
    GOOGLE_TRENDS = "google_trends"
    CFPB = "cfpb"
    RSS = "rss"


class IntentType(str, Enum):
    COMPLAINT = "complaint"
    COMPARISON = "comparison"
    PURCHASE_READY = "purchase_ready"
    CHURN_RISK = "churn_risk"
    INFORMATION = "information"
    UNKNOWN = "unknown"


class SignalTier(str, Enum):
    HOT = "hot"
    WARM = "warm"
    WATCH = "watch"


class SignalCategory(str, Enum):
    TELECOM_MOBILE = "telecom_mobile"
    TELECOM_BROADBAND = "telecom_broadband"
    TELECOM_BUNDLED = "telecom_bundled"
    TELECOM_PORTING = "telecom_porting"
    TELECOM_BILLING = "telecom_billing"
    FINTECH_CREDIT_CARD = "fintech_credit_card"
    FINTECH_PERSONAL_LOAN = "fintech_personal_loan"
    FINTECH_BNPL = "fintech_bnpl"
    FINTECH_BANKING = "fintech_banking"
    FINTECH_INSURANCE = "fintech_insurance"
    FINTECH_INVESTMENT = "fintech_investment"
    HOME_INTERNET = "home_internet"
    HOME_SECURITY = "home_security"
    HOME_UTILITIES = "home_utilities"
    HOME_MOVING = "home_moving"
    HOME_REPAIR = "home_repair"
    DTC_SUBSCRIPTION = "dtc_subscription"
    DTC_HEALTH = "dtc_health"
    DTC_BEAUTY = "dtc_beauty"
    DTC_FOOD = "dtc_food"
    DTC_FITNESS = "dtc_fitness"
    SAAS_CRM = "saas_crm"
    SAAS_PRODUCTIVITY = "saas_productivity"
    SAAS_SECURITY = "saas_security"
    SAAS_HR = "saas_hr"
    SAAS_MARKETING = "saas_marketing"
    HEALTH_INSURANCE = "health_insurance"
    HEALTH_PHARMACY = "health_pharmacy"
    HEALTH_TELEMEDICINE = "health_telemedicine"
    AUTO_INSURANCE = "auto_insurance"
    AUTO_FINANCE = "auto_finance"
    AUTO_EV = "auto_ev"
    TRAVEL_AIRLINE = "travel_airline"
    TRAVEL_HOTEL = "travel_hotel"
    TRAVEL_BOOKING = "travel_booking"
    EDU_ONLINE_LEARNING = "edu_online_learning"
    EDU_TEST_PREP = "edu_test_prep"
    ENERGY_SOLAR = "energy_solar"
    ENERGY_UTILITY = "energy_utility"
    REALESTATE_RENTAL = "realestate_rental"
    REALESTATE_MORTGAGE = "realestate_mortgage"
    OTHER = "other"


_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")
MAX_TEXT_LENGTH = 2000


class RawSignal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    source: SignalSource
    source_id: str
    url: str | None = None
    title: str | None = None
    text: str
    author: str | None = None
    geography: str | None = None
    harvested_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source_created_at: datetime | None = None
    raw_metadata: dict = Field(default_factory=dict)

    @field_validator("text")
    @classmethod
    def sanitise_text(cls, v: str) -> str:
        v = _HTML_TAG_RE.sub(" ", v)
        v = _WHITESPACE_RE.sub(" ", v).strip()
        return v[:MAX_TEXT_LENGTH]

    @field_validator("title")
    @classmethod
    def sanitise_title(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = _HTML_TAG_RE.sub(" ", v)
        return _WHITESPACE_RE.sub(" ", v).strip()[:500]


class ClassifiedSignal(RawSignal):
    category: SignalCategory = SignalCategory.OTHER
    intent_type: IntentType = IntentType.UNKNOWN
    classification_confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    keywords: list[str] = Field(default_factory=list)
    competitor_mentions: list[str] = Field(default_factory=list)
    classified_at: datetime | None = None

    @field_validator("keywords", "competitor_mentions")
    @classmethod
    def cap_list(cls, v: list[str]) -> list[str]:
        return v[:20]


class ScoredSignal(ClassifiedSignal):
    score: int = Field(ge=0, le=100, default=0)
    tier: SignalTier = SignalTier.WATCH
    velocity_delta_24h: float = Field(default=0.0)
    velocity_delta_7d: float = Field(default=0.0)
    engagement_score: float = Field(ge=0.0, le=1.0, default=0.0)
    scored_at: datetime | None = None

    @model_validator(mode="after")
    def set_tier_from_score(self) -> ScoredSignal:
        if self.score >= 70:
            self.tier = SignalTier.HOT
        elif self.score >= 40:
            self.tier = SignalTier.WARM
        else:
            self.tier = SignalTier.WATCH
        return self


class CuratedLead(ScoredSignal):
    brand_id: str
    match_reason: str = ""
    curated_at: datetime | None = None

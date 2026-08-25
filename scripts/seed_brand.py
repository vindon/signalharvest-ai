#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import settings
from db.brand_store import upsert_brand
from db.database import init_db
from schemas.brand import BrandSubscription
from schemas.signal import SignalCategory, SignalTier


def main():
    settings.ensure_dirs()
    init_db()
    brand = BrandSubscription(
        name="Demo Telecom Brand",
        contact_email="leads@demobrand.example.com",
        categories=[
            SignalCategory.TELECOM_MOBILE,
            SignalCategory.TELECOM_BROADBAND,
            SignalCategory.TELECOM_BILLING,
            SignalCategory.HOME_INTERNET,
        ],
        geographies=[],
        min_tier=SignalTier.WARM,
        keywords_include=["switch", "cancel", "alternative", "better plan"],
        keywords_exclude=["satisfied", "love my plan"],
        competitor_brands=["Verizon", "AT&T", "T-Mobile", "Comcast", "Spectrum"],
        digest_frequency="daily",
        approval_required=False,
    )
    upsert_brand(brand)
    print(f"Seeded: {brand.name} ({brand.id})")
    print(f"Categories : {[c.value for c in brand.categories]}")
    print(f"Min tier   : {brand.min_tier.value}")


if __name__ == "__main__":
    main()

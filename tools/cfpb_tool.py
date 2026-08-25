from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta

import requests

from schemas.signal import RawSignal, SignalSource

CFPB_API_BASE = "https://api.consumerfinance.gov/data/complaints"
PRODUCT_CATEGORY_MAP = {
    "Credit card": "fintech_credit_card",
    "Credit card or prepaid card": "fintech_credit_card",
    "Mortgage": "realestate_mortgage",
    "Personal loan": "fintech_personal_loan",
    "Vehicle loan or lease": "auto_finance",
    "Checking or savings account": "fintech_banking",
    "Debt collection": "fintech_personal_loan",
}


def harvest_cfpb(
    products: list[str] | None = None, days_back: int = 7, max_results: int = 50
) -> list[RawSignal]:
    target_products = products or list(PRODUCT_CATEGORY_MAP.keys())[:4]
    signals: list[RawSignal] = []
    date_min = (datetime.now(UTC) - timedelta(days=days_back)).strftime("%Y-%m-%d")
    for product in target_products:
        try:
            resp = requests.get(
                f"{CFPB_API_BASE}.json",
                params={
                    "product": product,
                    "date_received_min": date_min,
                    "size": min(max_results, 25),
                    "sort": "created_date_desc",
                    "has_narrative": "true",
                },
                timeout=15,
                headers={"User-Agent": "SignalHarvest/1.0"},
            )
            resp.raise_for_status()
            hits = resp.json().get("hits", {}).get("hits", [])
            for hit in hits:
                src = hit.get("_source", {})
                complaint_id = str(src.get("complaint_id", hit.get("_id", "")))
                narrative = src.get("consumer_complaint_narrative", "")
                if not narrative:
                    continue
                company = src.get("company", "")
                state = src.get("state", "")
                issue = src.get("issue", "")
                sub_issue = src.get("sub_issue", "")
                date_str = src.get("date_received", "")
                try:
                    received_dt = datetime.fromisoformat(date_str).replace(tzinfo=UTC)
                except (ValueError, TypeError):
                    received_dt = None
                signals.append(
                    RawSignal(
                        source=SignalSource.CFPB,
                        source_id=f"cfpb_{complaint_id}",
                        url=f"https://www.consumerfinance.gov/data-research/consumer-complaints/search/detail/{complaint_id}/",
                        title=f"CFPB complaint: {issue} — {company}",
                        text=(
                            f"CFPB complaint against {company}. Issue: {issue}"
                            f"{f' — {sub_issue}' if sub_issue else ''}. Narrative: {narrative}"
                        ),
                        geography=state or None,
                        source_created_at=received_dt,
                        raw_metadata={
                            "complaint_id": complaint_id,
                            "company": company,
                            "product": product,
                            "issue": issue,
                            "category_hint": PRODUCT_CATEGORY_MAP.get(product, "other"),
                            "state": state,
                        },
                    )
                )
            time.sleep(2)
        except requests.RequestException:
            time.sleep(5)
            continue
        except Exception:
            continue
    return signals

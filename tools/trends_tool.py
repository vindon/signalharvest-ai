from __future__ import annotations

import random
import time
from datetime import UTC, datetime

from schemas.signal import RawSignal, SignalSource

TREND_KEYWORD_GROUPS: dict[str, list[str]] = {
    "telecom_mobile": [
        "switch mobile carrier",
        "best mobile plan",
        "cancel Verizon",
        "cancel AT&T",
    ],
    "telecom_broadband": ["best internet provider", "cancel internet service", "fiber internet"],
    "fintech_credit_card": ["best credit card", "credit card rewards", "cancel credit card"],
    "fintech_personal_loan": ["personal loan rates", "debt consolidation", "loan refinance"],
    "home_internet": ["home internet deals", "internet provider comparison"],
    "dtc_subscription": ["cancel subscription", "subscription box alternative"],
}


def harvest_trends(
    keyword_groups: dict[str, list[str]] | None = None,
    timeframe: str = "now 7-d",
    geo: str = "",
    max_groups: int = 5,
) -> list[RawSignal]:
    try:
        from pytrends.request import TrendReq
    except ImportError:
        return []
    groups = keyword_groups or TREND_KEYWORD_GROUPS
    signals: list[RawSignal] = []
    pytrends = TrendReq(hl="en-US", tz=0, timeout=(10, 25))
    for category, keywords in list(groups.items())[:max_groups]:
        try:
            kw_batch = keywords[:5]
            pytrends.build_payload(kw_batch, cat=0, timeframe=timeframe, geo=geo, gprop="")
            iot = pytrends.interest_over_time()
            if iot.empty:
                continue
            latest = iot.iloc[-1]
            prior = iot.iloc[-2] if len(iot) > 1 else latest
            week_ago = iot.iloc[0]
            for kw in kw_batch:
                if kw not in iot.columns:
                    continue
                latest_val = int(latest.get(kw, 0))
                prior_val = int(prior.get(kw, 1)) or 1
                week_val = int(week_ago.get(kw, 1)) or 1
                delta_24h = ((latest_val - prior_val) / prior_val) * 100
                delta_7d = ((latest_val - week_val) / week_val) * 100
                signals.append(
                    RawSignal(
                        source=SignalSource.GOOGLE_TRENDS,
                        source_id=f"trends_{category}_{kw.replace(' ','_')}_{int(datetime.now(UTC).timestamp())}",
                        url=f"https://trends.google.com/trends/explore?q={kw.replace(' ','+')}",
                        title=f"Trending: {kw}",
                        text=(
                            f"Google Trends signal for '{kw}' in category '{category}'. "
                            f"Interest: {latest_val}/100. 24h change: {delta_24h:+.1f}%. "
                            f"7d change: {delta_7d:+.1f}%."
                        ),
                        geography=geo or "global",
                        raw_metadata={
                            "category_hint": category,
                            "keyword": kw,
                            "interest_index": latest_val,
                            "delta_24h_pct": round(delta_24h, 2),
                            "delta_7d_pct": round(delta_7d, 2),
                        },
                    )
                )
            time.sleep(5 + random.uniform(0, 3))
        except Exception:
            time.sleep(10)
            continue
    return signals

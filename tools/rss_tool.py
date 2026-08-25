from __future__ import annotations

import time
from datetime import UTC, datetime
from uuid import uuid4

import feedparser
import requests

from schemas.signal import RawSignal, SignalSource

DEFAULT_FEEDS = [
    {
        "url": "https://www.fcc.gov/news-events/rss/blog",
        "category_hint": "telecom_broadband",
        "label": "FCC Blog",
    },
    {
        "url": "https://www.consumer.ftc.gov/rss.xml",
        "category_hint": "fintech_credit_card",
        "label": "FTC Consumer Alerts",
    },
]


def harvest_rss(feeds: list[dict] | None = None, max_per_feed: int = 20) -> list[RawSignal]:
    target_feeds = feeds or DEFAULT_FEEDS
    signals: list[RawSignal] = []
    for feed_config in target_feeds:
        url = feed_config["url"]
        category_hint = feed_config.get("category_hint", "other")
        label = feed_config.get("label", url)
        try:
            resp = requests.get(url, timeout=15, headers={"User-Agent": "SignalHarvest/1.0"})
            resp.raise_for_status()
            feed = feedparser.parse(resp.content)
            for entry in feed.entries[:max_per_feed]:
                title = entry.get("title", "")
                summary = entry.get("summary", "") or entry.get("description", "")
                link = entry.get("link", "")
                entry_id = entry.get("id", "") or str(uuid4())
                published_parsed = entry.get("published_parsed")
                published_dt = None
                if published_parsed:
                    try:
                        published_dt = datetime(*published_parsed[:6], tzinfo=UTC)
                    except Exception:
                        pass
                text = f"{title}. {summary}".strip()
                if len(text) < 20:
                    continue
                signals.append(
                    RawSignal(
                        source=SignalSource.RSS,
                        source_id=f"rss_{hash(entry_id) & 0xFFFFFFFF}",
                        url=link or None,
                        title=title,
                        text=text,
                        source_created_at=published_dt,
                        raw_metadata={
                            "feed_label": label,
                            "feed_url": url,
                            "category_hint": category_hint,
                        },
                    )
                )
            time.sleep(10)
        except Exception:
            continue
    return signals

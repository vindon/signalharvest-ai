from __future__ import annotations

import time
from datetime import UTC, datetime

from schemas.signal import RawSignal, SignalSource

DEFAULT_SUBREDDITS = [
    "tmobile",
    "verizon",
    "ATT",
    "personalfinance",
    "CreditCards",
    "homeowners",
    "Frugal",
    "NoContract",
    "HomeImprovement",
    "smallbusiness",
]


def harvest_reddit(
    subreddits: list[str] | None = None, max_per_subreddit: int = 10, run_id: str = ""
) -> list[RawSignal]:
    try:
        from config.settings import settings

        if not settings.reddit_configured:
            return []
    except Exception:
        return []
    try:
        import praw
    except ImportError:
        return []
    try:
        from config.settings import settings as s

        reddit = praw.Reddit(
            client_id=s.reddit_client_id,
            client_secret=s.reddit_client_secret,
            user_agent=s.reddit_user_agent,
        )
    except Exception:
        return []

    targets = subreddits or DEFAULT_SUBREDDITS
    signals: list[RawSignal] = []
    for sub_name in targets:
        try:
            sub = reddit.subreddit(sub_name)
            for post in list(sub.hot(limit=max_per_subreddit)):
                if post.selftext in ("[removed]", "[deleted]", ""):
                    continue
                signals.append(
                    RawSignal(
                        source=SignalSource.REDDIT,
                        source_id=post.id,
                        url=f"https://reddit.com{post.permalink}",
                        title=post.title,
                        text=post.selftext or post.title,
                        author=str(post.author) if post.author else None,
                        source_created_at=datetime.fromtimestamp(post.created_utc, tz=UTC),
                        raw_metadata={
                            "subreddit": sub_name,
                            "score": post.score,
                            "num_comments": post.num_comments,
                            "upvote_ratio": post.upvote_ratio,
                            "run_id": run_id,
                        },
                    )
                )
            time.sleep(0.5)
        except Exception:
            continue
    return signals

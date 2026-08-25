from __future__ import annotations

from db.signal_store import upsert_raw_signal
from tools.cfpb_tool import harvest_cfpb
from tools.reddit_tool import harvest_reddit
from tools.rss_tool import harvest_rss
from tools.trends_tool import harvest_trends


def run(state: dict) -> dict:
    run_id: str = state["run_id"]
    all_signals = []
    for harvester, name in [
        (harvest_reddit, "reddit"),
        (harvest_trends, "trends"),
        (harvest_cfpb, "cfpb"),
        (harvest_rss, "rss"),
    ]:
        try:
            sigs = harvester() if name != "reddit" else harvest_reddit(run_id=run_id)
            all_signals.extend(sigs)
        except Exception as exc:
            print(f"[sentinel] {name} error: {exc}")
    inserted = sum(1 for s in all_signals if upsert_raw_signal(s, run_id))
    return {**state, "signals_harvested": inserted}

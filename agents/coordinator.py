from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict
from uuid import uuid4

from langgraph.graph import END, StateGraph

from agents import classifier, curator, publisher, scorer, sentinel
from db.state_store import save_pipeline_run, save_state
from schemas.digest import PipelineRun

PROGRESS_FILE = Path("claude-progress.txt")


class PipelineState(TypedDict):
    run_id: str
    signals_harvested: int
    signals_classified: int
    signals_scored: int
    leads_curated: int
    curated_leads: list
    digests_generated: int
    digests_delivered: int
    error: str


def _wrap(agent_fn, step_name: str):
    def wrapped(state: PipelineState) -> PipelineState:
        print(f"[coordinator] → {step_name}")
        try:
            new_state = agent_fn(state)
            save_state(state["run_id"], new_state)
            return new_state
        except Exception as exc:
            print(f"[coordinator] {step_name} error: {exc}")
            return {**state, "error": f"{step_name}: {exc}"}

    wrapped.__name__ = step_name
    return wrapped


def build_graph():
    graph = StateGraph(PipelineState)
    graph.add_node("sentinel", _wrap(sentinel.run, "sentinel"))
    graph.add_node("classifier", _wrap(classifier.run, "classifier"))
    graph.add_node("scorer", _wrap(scorer.run, "scorer"))
    graph.add_node("curator", _wrap(curator.run, "curator"))
    graph.add_node("publisher", _wrap(publisher.run, "publisher"))
    graph.set_entry_point("sentinel")
    graph.add_edge("sentinel", "classifier")
    graph.add_edge("classifier", "scorer")
    graph.add_edge("scorer", "curator")
    graph.add_edge("curator", "publisher")
    graph.add_edge("publisher", END)
    return graph.compile()


def run_pipeline(run_id: str | None = None) -> PipelineRun:
    if run_id is None:
        run_id = str(uuid4())
    pipeline_run = PipelineRun(id=run_id)
    save_pipeline_run(pipeline_run)
    initial: PipelineState = {
        "run_id": run_id,
        "signals_harvested": 0,
        "signals_classified": 0,
        "signals_scored": 0,
        "leads_curated": 0,
        "curated_leads": [],
        "digests_generated": 0,
        "digests_delivered": 0,
        "error": "",
    }
    app = build_graph()
    try:
        final = app.invoke(initial)
        for k in [
            "signals_harvested",
            "signals_classified",
            "signals_scored",
            "leads_curated",
            "digests_generated",
            "digests_delivered",
        ]:
            setattr(pipeline_run, k, final.get(k, 0))
        err = final.get("error", "")
        pipeline_run.status = "failed" if err else "completed"
        if err:
            pipeline_run.error_message = err
    except Exception as exc:
        pipeline_run.status = "failed"
        pipeline_run.error_message = str(exc)
    pipeline_run.completed_at = datetime.now(UTC)
    save_pipeline_run(pipeline_run)
    _write_progress(pipeline_run)
    return pipeline_run


def _write_progress(run: PipelineRun) -> None:
    duration = ""
    if run.completed_at and run.started_at:
        duration = f"{int((run.completed_at - run.started_at).total_seconds())}s"
    PROGRESS_FILE.write_text(
        f"# SignalHarvest — Last Run\nUpdated: {datetime.now(UTC).isoformat()}\n\n"
        f"## Run ID\n{run.id}\n\n## Status\n{run.status.upper()}\n"
        f"{f'Error: {run.error_message}' if run.error_message else ''}\n\n"
        f"## Stats\n"
        f"- Harvested  : {run.signals_harvested}\n"
        f"- Classified : {run.signals_classified}\n"
        f"- Scored     : {run.signals_scored}\n"
        f"- Leads      : {run.leads_curated}\n"
        f"- Digests    : {run.digests_generated} generated / {run.digests_delivered} delivered\n"
        f"- Duration   : {duration}\n\n"
        f"## Next\n- Digests: output/digests/\n- Run: python scripts/run_pipeline.py\n"
        f"- Tests: pytest tests/ -v\n",
        encoding="utf-8",
    )

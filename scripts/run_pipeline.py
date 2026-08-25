#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import click

from config.settings import settings


@click.command()
@click.option("--mode", type=click.Choice(["full", "schedule"]), default="full", show_default=True)
def main(mode: str):
    settings.ensure_dirs()
    from db.database import init_db

    init_db()
    if mode == "full":
        _run_once()
    else:
        _run_scheduled()


def _run_once():
    from agents.coordinator import run_pipeline

    print("=" * 50)
    print("SignalHarvest AI — Pipeline starting")
    print("=" * 50)
    run = run_pipeline()
    print(f"\nStatus     : {run.status.upper()}")
    print(f"Run ID     : {run.id}")
    print(f"Harvested  : {run.signals_harvested}")
    print(f"Classified : {run.signals_classified}")
    print(f"Scored     : {run.signals_scored}")
    print(f"Leads      : {run.leads_curated}")
    print(f"Digests    : {run.digests_generated} generated / {run.digests_delivered} delivered")
    print(f"Output     : {settings.digest_output_dir}/")
    if run.error_message:
        print(f"Error      : {run.error_message}")
    if run.status == "failed":
        sys.exit(1)


def _run_scheduled():
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.cron import CronTrigger

    from agents.coordinator import run_pipeline

    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(
        run_pipeline,
        CronTrigger(hour=settings.scheduler_hour, minute=settings.scheduler_minute, timezone="UTC"),
        id="signalharvest_pipeline",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    print(
        f"Scheduler started. Runs at {settings.scheduler_hour:02d}:{settings.scheduler_minute:02d} UTC daily."
    )
    print("Ctrl+C to stop.")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown(wait=False)
        print("\nStopped.")


if __name__ == "__main__":
    main()

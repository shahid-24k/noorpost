"""
scheduler.py — Automated posting scheduler for NoorPost Ultimate
Features configurable timezone (default Asia/Kolkata), overlap prevention (max_instances=1),
event listeners, and persistent execution tracking in SQLite.
"""

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED

import config
from pipeline import run_pipeline
from logger import log

def _job_listener(event):
    if event.exception:
        log(f"❌ Scheduled Job [{event.job_id}] failed: {event.exception}", level="ERROR")
    elif event.code == EVENT_JOB_MISSED:
        log(f"⚠️  Scheduled Job [{event.job_id}] was missed (system busy or asleep)", level="WARNING")
    else:
        log(f"✨ Scheduled Job [{event.job_id}] executed successfully.")

def start_scheduler():
    """
    Initialize and start the persistent APScheduler instance.
    Reads POST_TIMES and TIMEZONE from config.
    """
    scheduler = BlockingScheduler(timezone=config.TIMEZONE)
    scheduler.add_listener(_job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR | EVENT_JOB_MISSED)

    for t in config.POST_TIMES:
        job_id = f"post_{t['hour']:02d}h{t['minute']:02d}m"
        scheduler.add_job(
            run_pipeline,
            args=[job_id],
            trigger=CronTrigger(
                hour=t["hour"],
                minute=t["minute"],
                timezone=config.TIMEZONE,
            ),
            id=job_id,
            max_instances=1,          # Prevent overlapping jobs
            coalesce=True,            # Combine missed runs into one
            misfire_grace_time=300,   # 5-minute grace period if system was suspended
        )
        log(f"Scheduled slot: {t['hour']:02d}:{t['minute']:02d} ({config.TIMEZONE})")

    slots_str = ", ".join(f"{t['hour']:02d}:{t['minute']:02d}" for t in config.POST_TIMES)
    log("[NoorPost] [WORKER: DAILY POSTING SCHEDULER]")
    log(f"   Active with {len(config.POST_TIMES)} daily slots: {slots_str}")
    log(f"   Configured Timezone: {config.TIMEZONE}")
    log("   Press Ctrl+C to stop.")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        if scheduler.running:
            scheduler.shutdown(wait=False)
        log("Daily scheduler stopped gracefully.")

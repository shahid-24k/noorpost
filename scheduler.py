"""
scheduler.py — APScheduler daily posting scheduler for NoorPost
Reads posting times from config.py and runs the pipeline automatically
"""

import config
from pipeline import run_pipeline
from logger import log
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger


def start_scheduler():
    """Start APScheduler with post times defined in config.py."""
    scheduler = BlockingScheduler(timezone=config.TIMEZONE)

    for t in config.POST_TIMES:
        scheduler.add_job(
            run_pipeline,
            trigger=CronTrigger(
                hour=t["hour"],
                minute=t["minute"],
                timezone=config.TIMEZONE,
            ),
            id=f"post_{t['hour']}h{t['minute']}m",
            misfire_grace_time=300,   # 5 min grace if system was asleep
        )
        log(f"⏰ Scheduled: {t['hour']:02d}:{t['minute']:02d} {config.TIMEZONE}")

    log(f"\n✅ Scheduler active with {len(config.POST_TIMES)} daily posts.")
    log("   Press Ctrl+C to stop.\n")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log("⬛ Scheduler stopped.")

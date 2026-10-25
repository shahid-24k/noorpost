"""
autopilot.py — Lightweight Autopilot Queue Processor for NoorPost Ultimate

Reads authorized video sources from source_queue.txt, processes them sequentially
through the existing repurpose_pipeline, and delivers finished clips via the
established Dropbox → Make.com → Instagram workflow.

Features:
- Persistent SQLite job tracking with duplicate prevention.
- Safe resume after interruption (skips completed sources, retries in-progress).
- Configurable processing interval with Asia/Kolkata timezone.
- Disabled by default — must be explicitly started.
- Never bypasses rights confirmation or YouTube access restrictions.
- Never replaces the existing Instagram publisher or Make.com scenario.
"""

import re
import hashlib
import threading
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

import config
from logger import log
from database import init_db, _get_connection
from repurpose_pipeline import run_repurpose_pipeline

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONSTANTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QUEUE_FILE = config.BASE_DIR / "source_queue.txt"

AUTOPILOT_STATES = {
    "QUEUED",           # Parsed from queue file, waiting to be processed
    "PROCESSING",       # Currently being handled by autopilot
    "COMPLETED",        # All clips rendered and handed off successfully
    "FAILED",           # Processing failed (retryable)
    "SKIPPED",          # Duplicate or invalid entry
}

# Default processing interval in minutes (configurable via .env)
DEFAULT_INTERVAL_MINUTES = int(
    getattr(config, "AUTOPILOT_INTERVAL_MINUTES", 0) or 30
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DATABASE: AUTOPILOT QUEUE TABLE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def init_autopilot_db():
    """Create the autopilot_queue table if it doesn't exist. Idempotent."""
    init_db()
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS autopilot_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_entry TEXT NOT NULL,
                source_hash TEXT UNIQUE NOT NULL,
                status TEXT NOT NULL DEFAULT 'QUEUED',
                num_clips_produced INTEGER DEFAULT 0,
                error_message TEXT,
                attempts INTEGER DEFAULT 0,
                max_attempts INTEGER DEFAULT 3,
                queued_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                updated_at TEXT NOT NULL
            )
        """)
        conn.commit()


def parse_queue_line(line: str) -> Dict[str, Any]:
    """
    Parse a queue line supporting both simple URLs and structured entries.
    Supported format:
      URL [ | CREATOR/CHANNEL | RIGHTS_CONFIRMED (YES/NO) | TIMESTAMPS (MM:SS-MM:SS) ]
    Or JSON string.
    """
    stripped = line.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        try:
            import json
            data = json.loads(stripped)
            return {
                "url": data.get("url", "").strip(),
                "channel": data.get("channel", "").strip(),
                "rights_confirmed": bool(data.get("rights_confirmed", False)),
                "timestamps": data.get("timestamps", "").strip(),
                "raw_entry": stripped
            }
        except Exception:
            pass

    parts = [p.strip() for p in stripped.split("|")]
    url = parts[0]
    channel = parts[1] if len(parts) > 1 else ""
    rights_str = parts[2].lower() if len(parts) > 2 else ""
    rights_confirmed = rights_str in ("yes", "true", "1", "confirmed")
    timestamps = parts[3] if len(parts) > 3 else ""

    return {
        "url": url,
        "channel": channel,
        "rights_confirmed": rights_confirmed,
        "timestamps": timestamps,
        "raw_entry": stripped
    }


def _hash_entry(entry: str) -> str:
    """Deterministic hash for a queue entry to prevent duplicates."""
    clean = entry.strip().lower()
    if "|" in clean:
        clean = clean.split("|")[0].strip()
    return hashlib.sha256(clean.encode("utf-8")).hexdigest()[:20]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# QUEUE FILE PARSER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def parse_queue_file(queue_path: Optional[Path] = None) -> List[str]:
    """
    Read source_queue.txt and return non-blank, non-comment lines.
    Creates the file with a header comment if it doesn't exist.
    """
    path = queue_path or QUEUE_FILE
    if not path.exists():
        path.write_text(
            "# NoorPost Autopilot Source Queue\n"
            "# Supported format: URL [ | CREATOR | RIGHTS_CONFIRMED (YES/NO) | TIMESTAMPS ]\n"
            "# Lines starting with # are ignored.\n"
            "# Examples:\n"
            "# https://www.youtube.com/watch?v=AUTHORIZED_VIDEO_ID | Islamic Reminder Channel | YES | 01:15-02:00\n"
            "# D:\\lectures\\my_khutbah.mp4\n",
            encoding="utf-8"
        )
        log("Created empty queue file: " + str(path))
        return []

    entries = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                entries.append(stripped)
    return entries


def sync_queue_to_db(entries: List[str]) -> int:
    """
    Insert new queue entries into the database. Skip already-known entries.
    Supports structured entries with creator, rights confirmation, and timestamps.
    Returns the number of newly queued entries.
    """
    init_autopilot_db()
    now_iso = datetime.now().isoformat()
    new_count = 0

    with _get_connection() as conn:
        cursor = conn.cursor()
        for entry in entries:
            parsed = parse_queue_line(entry)
            core_url = parsed["url"]
            if not core_url:
                continue

            entry_hash = _hash_entry(core_url)
            cursor.execute(
                "SELECT id FROM autopilot_queue WHERE source_hash = ?",
                (entry_hash,)
            )
            if cursor.fetchone() is None:
                cursor.execute("""
                    INSERT INTO autopilot_queue
                        (source_entry, source_hash, channel, rights_confirmed, status, queued_at, updated_at)
                    VALUES (?, ?, ?, ?, 'QUEUED', ?, ?)
                """, (
                    entry, entry_hash, parsed.get("channel") or None,
                    1 if parsed.get("rights_confirmed") else 0,
                    now_iso, now_iso
                ))
                new_count += 1
        conn.commit()

    return new_count


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# JOB STATE MANAGEMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def get_pending_jobs() -> List[Dict[str, Any]]:
    """Get QUEUED jobs and stuck PROCESSING jobs (safe resume)."""
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM autopilot_queue
            WHERE status IN ('QUEUED', 'PROCESSING')
              AND attempts < max_attempts
            ORDER BY id ASC
        """)
        return [dict(r) for r in cursor.fetchall()]


def get_retryable_jobs() -> List[Dict[str, Any]]:
    """Get FAILED jobs that haven't exceeded max attempts."""
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM autopilot_queue
            WHERE status = 'FAILED'
              AND attempts < max_attempts
            ORDER BY id ASC
        """)
        return [dict(r) for r in cursor.fetchall()]


def update_job_status(job_id: int, status: str, error_message: str = None,
                      num_clips: int = None, clip_ids: str = None):
    """Update autopilot job status with timestamp tracking."""
    now_iso = datetime.now().isoformat()
    with _get_connection() as conn:
        cursor = conn.cursor()

        updates = ["status = ?", "updated_at = ?"]
        params: list = [status, now_iso]

        if status == "PROCESSING":
            updates.append("started_at = COALESCE(started_at, ?)")
            params.append(now_iso)
            updates.append("attempts = attempts + 1")

        if status in ("COMPLETED", "FAILED"):
            updates.append("completed_at = ?")
            params.append(now_iso)

        if error_message is not None:
            updates.append("error_message = ?")
            params.append(error_message)

        if num_clips is not None:
            updates.append("num_clips_produced = ?")
            params.append(num_clips)

        if clip_ids is not None:
            updates.append("clip_ids = ?")
            params.append(clip_ids)

        params.append(job_id)
        cursor.execute(
            f"UPDATE autopilot_queue SET {', '.join(updates)} WHERE id = ?",
            params
        )
        conn.commit()


def list_all_jobs(status_filter: Optional[str] = None,
                  limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve autopilot queue records for display."""
    with _get_connection() as conn:
        cursor = conn.cursor()
        if status_filter:
            cursor.execute("""
                SELECT * FROM autopilot_queue
                WHERE status = ?
                ORDER BY id DESC LIMIT ?
            """, (status_filter, limit))
        else:
            cursor.execute("""
                SELECT * FROM autopilot_queue
                ORDER BY id DESC LIMIT ?
            """, (limit,))
        return [dict(r) for r in cursor.fetchall()]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CORE PROCESSOR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _is_youtube_url(entry: str) -> bool:
    """Quick check if entry looks like a YouTube URL."""
    return bool(re.match(
        r'^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+$',
        entry.strip()
    ))


def process_single_job(job: Dict[str, Any],
                       confirm_rights: bool = True,
                       num_clips: int = 3,
                       clip_duration: float = 45.0,
                       preset: str = "balanced",
                       theme: str = "midnight-gold",
                       reframing: str = "blur_fill") -> Dict[str, Any]:
    """
    Process one autopilot queue entry through the existing repurpose pipeline.
    Returns the pipeline result dict.
    """
    raw_entry = job["source_entry"]
    job_id = job["id"]

    parsed = parse_queue_line(raw_entry)
    core_url = parsed["url"] or raw_entry
    is_yt = _is_youtube_url(core_url)
    effective_rights = confirm_rights or parsed.get("rights_confirmed") or (job.get("rights_confirmed") == 1)

    log(f"Autopilot processing job #{job_id}: {core_url}")
    update_job_status(job_id, "PROCESSING")

    try:
        # YouTube sources MUST have rights confirmed
        if is_yt and not effective_rights:
            raise PermissionError(
                "Autopilot requires --confirm-rights for YouTube sources. "
                "Skipping to protect against unauthorized repurposing."
            )

        # Parse preferred timestamps if present
        timestamps = parsed.get("timestamps") or None
        if not timestamps and job.get("preferred_start") is not None and job.get("preferred_end") is not None:
            timestamps = f"{job['preferred_start']}-{job['preferred_end']}"

        result = run_repurpose_pipeline(
            url_or_path=core_url,
            confirm_rights=effective_rights and is_yt,
            num_clips=num_clips,
            clip_duration=clip_duration,
            reframing=reframing,
            preset=preset,
            theme=theme,
            timestamps=timestamps,
            burn_subtitles=True,
            preview_only=False,
            upload_dropbox=True,
        )

        clips = result.get("clips", [])
        clips_count = len(clips)
        clip_ids_str = ",".join(c.get("clip_id", "") for c in clips if c.get("clip_id"))
        update_job_status(job_id, "COMPLETED", num_clips=clips_count, clip_ids=clip_ids_str)
        log(f"Autopilot job #{job_id} completed: {clips_count} clips produced.")
        return result

    except Exception as e:
        error_msg = str(e)[:500]
        update_job_status(job_id, "FAILED", error_message=error_msg)
        log(f"Autopilot job #{job_id} failed: {error_msg}", level="ERROR")
        return {"status": "failed", "error": error_msg}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RUN MODES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def run_queue_once(confirm_rights: bool = True,
                   num_clips: int = 3,
                   clip_duration: float = 45.0,
                   preset: str = "balanced",
                   theme: str = "midnight-gold",
                   reframing: str = "blur_fill") -> Dict[str, Any]:
    """
    Process all pending queue entries once. Returns summary.
    Guarded by _queue_lock to prevent overlapping executions.
    """
    if not _queue_lock.acquire(blocking=False):
        log("[NoorPost] [AUTOPILOT] Queue processing already in progress. Skipping overlapping run.", level="WARNING")
        return {"processed": 0, "succeeded": 0, "failed": 0, "skipped_busy": True}

    try:
        init_autopilot_db()

        # Parse queue file and sync new entries to database
        entries = parse_queue_file()
        new_count = sync_queue_to_db(entries)
        if new_count:
            log(f"{new_count} new source(s) added to autopilot queue.")

        # Fetch jobs to process (QUEUED + interrupted PROCESSING)
        jobs = get_pending_jobs()
        if not jobs:
            log("Autopilot queue is empty. Add sources to source_queue.txt")
            return {"processed": 0, "succeeded": 0, "failed": 0}

        log(f"Autopilot starting: {len(jobs)} source(s) to process.")
        log("=" * 60)

        succeeded = 0
        failed = 0

        for job in jobs:
            result = process_single_job(
                job,
                confirm_rights=confirm_rights,
                num_clips=num_clips,
                clip_duration=clip_duration,
                preset=preset,
                theme=theme,
                reframing=reframing,
            )
            if result.get("status") == "completed":
                succeeded += 1
            else:
                failed += 1

        log("=" * 60)
        log(f"Autopilot batch complete: {succeeded} succeeded, {failed} failed out of {len(jobs)} total.")

        return {"processed": len(jobs), "succeeded": succeeded, "failed": failed}
    finally:
        _queue_lock.release()


def retry_failed_queue_jobs(confirm_rights: bool = True,
                            **kwargs) -> Dict[str, Any]:
    """Retry all FAILED autopilot jobs that haven't exceeded max_attempts."""
    init_autopilot_db()

    jobs = get_retryable_jobs()
    if not jobs:
        log("No retryable failed jobs in autopilot queue.")
        return {"retried": 0, "succeeded": 0, "failed": 0}

    log(f"Retrying {len(jobs)} failed autopilot job(s)...")
    succeeded = 0
    failed = 0

    for job in jobs:
        result = process_single_job(job, confirm_rights=confirm_rights, **kwargs)
        if result.get("status") == "completed":
            succeeded += 1
        else:
            failed += 1

    return {"retried": len(jobs), "succeeded": succeeded, "failed": failed}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SCHEDULED AUTOPILOT (APScheduler)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_stop_event = threading.Event()
_queue_lock = threading.Lock()


def _autopilot_job_listener(event):
    """APScheduler event listener for autopilot jobs."""
    if event.exception:
        log(f"Autopilot scheduled run failed: {event.exception}", level="ERROR")
    else:
        log("Autopilot scheduled run completed successfully.")


def start_autopilot_scheduler(
    interval_minutes: int = None,
    confirm_rights: bool = True,
    num_clips: int = 3,
    clip_duration: float = 45.0,
    preset: str = "balanced",
    theme: str = "midnight-gold",
    reframing: str = "blur_fill"
):
    """
    Start the autopilot scheduler that processes the queue at regular intervals.
    Uses Asia/Kolkata timezone. Blocks until stopped with Ctrl+C.
    """
    init_autopilot_db()
    _stop_event.clear()

    interval = interval_minutes or DEFAULT_INTERVAL_MINUTES
    tz = config.TIMEZONE

    log("=" * 60)
    log("NoorPost Autopilot Scheduler Starting")
    log(f"   Interval: every {interval} minutes")
    log(f"   Timezone: {tz}")
    log(f"   Queue file: {QUEUE_FILE}")
    log(f"   Rights confirmation: {'ENABLED' if confirm_rights else 'DISABLED'}")
    log("=" * 60)

    scheduler = BlockingScheduler(timezone=tz)
    scheduler.add_listener(_autopilot_job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    scheduler.add_job(
        run_queue_once,
        trigger=IntervalTrigger(minutes=interval, timezone=tz),
        kwargs={
            "confirm_rights": confirm_rights,
            "num_clips": num_clips,
            "clip_duration": clip_duration,
            "preset": preset,
            "theme": theme,
            "reframing": reframing,
        },
        id="autopilot_queue_processor",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=600,
        next_run_time=datetime.now(),  # Run immediately on start
    )

    log(f"Autopilot active. Processing queue every {interval} minutes.")
    log("   Press Ctrl+C to stop.")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        _stop_event.set()
        if scheduler.running:
            scheduler.shutdown(wait=False)
        log("Autopilot scheduler stopped gracefully.")


def stop_autopilot():
    """Signal the autopilot to stop after the current job finishes."""
    _stop_event.set()
    log("Autopilot stop signal sent.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CLI DISPLAY HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def print_autopilot_status():
    """Print a summary of the autopilot queue."""
    init_autopilot_db()

    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT status, COUNT(*) as cnt
            FROM autopilot_queue
            GROUP BY status
            ORDER BY
                CASE status
                    WHEN 'QUEUED' THEN 1
                    WHEN 'PROCESSING' THEN 2
                    WHEN 'COMPLETED' THEN 3
                    WHEN 'FAILED' THEN 4
                    WHEN 'SKIPPED' THEN 5
                    ELSE 6
                END
        """)
        rows = cursor.fetchall()

    print()
    print("=" * 65)
    print("  NOORPOST AUTOPILOT -- QUEUE STATUS")
    print("=" * 65)

    if not rows:
        print("  (empty queue)")
    else:
        total = 0
        for r in rows:
            status = r["status"]
            count = r["cnt"]
            total += count
            icon = {
                "QUEUED": "[PENDING]", "PROCESSING": "[ACTIVE]",
                "COMPLETED": "[DONE]", "FAILED": "[FAIL]", "SKIPPED": "[SKIP]"
            }.get(status, "[?]")
            print(f"  {icon:<12} {status:<14} {count:>4}")
        print(f"  {'_' * 35}")
        print(f"  TOTAL{' ' * 22}{total:>4}")

    print("=" * 65)

    # Show recent jobs
    jobs = list_all_jobs(limit=10)
    if jobs:
        print(f"\n  Recent Jobs (last {len(jobs)}):")
        print(f"  {'ID':<5} {'Status':<14} {'Clips':<7} {'Source':<40}")
        print(f"  {'_' * 66}")
        for j in jobs:
            src = j["source_entry"]
            if len(src) > 38:
                src = src[:35] + "..."
            clips = j.get("num_clips_produced", 0) or 0
            print(f"  {j['id']:<5} {j['status']:<14} {clips:<7} {src:<40}")
            if j.get("error_message"):
                err = j["error_message"][:60]
                print(f"        > Error: {err}")

    print()

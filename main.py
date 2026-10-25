"""
============================================================
              NOORPOST ULTIMATE — MAIN ENTRY
  Automated Authentic Islamic Content Creation & Repurposing
============================================================

Commands:
  # Content Engine:
  python main.py --now                  Run one complete cycle immediately
  python main.py --preview              Generate video & preview without publishing
  python main.py --category <name>      Target a specific category (e.g. friday_reminders)
  python main.py --categories <c1,c2>   Rotate within specific categories
  python main.py --list-categories      List all 13 canonical categories & content counts
  python main.py --review-status        Show human review audit & item statuses
  python main.py --approve <id>         Approve content item for publishing
  python main.py --reject <id>          Reject content item from publishing
  python main.py --list-themes          List all 7 curated Islamic visual themes
  python main.py --stats                View database metrics and history

  # Video Repurposing Engine (Long Videos -> Vertical Reels -> Dropbox):
  python main.py --repurpose-url <url> --confirm-rights   Process an authorized YouTube lecture
  python main.py --repurpose-file <path>                  Process a local video lecture
  python main.py --batch <file.txt> --confirm-rights      Process multiple video sources
  python main.py --preview-clips                          Preview candidate segments without rendering
  python main.py --clip-duration <sec>                    Target clip length (default: 45s)
  python main.py --num-clips <count>                      Number of clips per video (default: 3)
  python main.py --reframing <strategy>                   Reframing: blur_fill, center_crop, fit_themed
  python main.py --timestamps <ranges>                    Manual cuts: "01:10-01:55,04:20-05:05"
  python main.py --list-jobs                              View repurpose queue and Dropbox handoff audit
  python main.py --retry-failed                           Retry failed repurpose jobs

  # Autopilot (Automated Queue Processing):
  python main.py --autopilot-loop [--confirm-rights]      Start persistent source-queue worker loop
  python main.py --autopilot-once [--confirm-rights]      Process queued sources once and exit
  python main.py --autopilot-status                       Show autopilot queue status & stats
  python main.py --autopilot-retry [--confirm-rights]     Retry failed autopilot jobs
  python main.py --interval <minutes>                     Polling interval for autopilot loop (default: 60)

  # Daily Posting Scheduler:
  python main.py                                          Start daily posting scheduler (default)
  python main.py --scheduler                              Explicitly start daily posting scheduler
"""

import sys
import argparse
from pathlib import Path

# Ensure UTF-8 output encoding on Windows terminals to prevent charmap crashes
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from scheduler import start_scheduler
from pipeline import run_pipeline
from repurpose_pipeline import run_repurpose_pipeline
from source_manager import source_engine
from database import (
    init_db,
    sync_duas,
    _get_connection,
    update_content_review_status,
    get_repurpose_jobs,
    update_clip_status
)
from content_db import AUTHENTIC_CONTENT
from categories import CATEGORIES, resolve_category
from themes import THEMES
from autopilot import (
    run_queue_once, start_autopilot_scheduler, retry_failed_queue_jobs,
    print_autopilot_status, init_autopilot_db,
)
import config
from logger import log

BANNER = """
============================================================
              NOORPOST ULTIMATE v2.3
        بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ
   Authentic Islamic Content & Video Repurposing Engine
============================================================
"""

def print_stats():
    init_db()
    sync_duas(AUTHENTIC_CONTENT)
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*), SUM(times_used) FROM duas_meta")
        total_items, total_uses = cursor.fetchone()

        cursor.execute("SELECT COUNT(*) FROM video_records")
        total_videos = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM repurpose_clips")
        total_repurposed = cursor.fetchone()[0]

        cursor.execute("SELECT platform, status, COUNT(*) FROM publication_history GROUP BY platform, status")
        pub_rows = cursor.fetchall()

    print("\n[NoorPost] Database Statistics:")
    print(f"   * Total Authentic Content Items: {total_items}")
    print(f"   * Total Content Usages: {total_uses or 0}")
    print(f"   * Total Generated Short Videos: {total_videos}")
    print(f"   * Total Repurposed Reel Clips: {total_repurposed}")
    print("\n[NoorPost] Publication History:")
    if pub_rows:
        for r in pub_rows:
            print(f"   * {r[0]} ({r[1]}): {r[2]}")
    else:
        print("   * No publication attempts recorded yet.")
    print("")

def list_categories_summary():
    init_db()
    sync_duas(AUTHENTIC_CONTENT)
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT category, COUNT(*) FROM duas_meta GROUP BY category")
        counts = dict(cursor.fetchall())

    print("\n📚 13 Canonical Content Categories:")
    print("-------------------------------------------------------------------------------------")
    print(f"{'Category ID':<24} | {'Name':<28} | {'Badge':<20} | {'Items'}")
    print("-------------------------------------------------------------------------------------")
    for key, cat in CATEGORIES.items():
        c_count = counts.get(key, 0)
        print(f"{key:<24} | {cat['name']:<28} | {cat['badge']:<20} | {c_count}")
    print("-------------------------------------------------------------------------------------\n")

def list_themes():
    print("\n🎨 Curated Islamic Visual Themes:")
    for key, th in THEMES.items():
        print(f"   • {key:<18} : {th['name']} — {th['description']}")
    print("")

def show_review_status():
    init_db()
    sync_duas(AUTHENTIC_CONTENT)
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT review_status, COUNT(*) FROM duas_meta GROUP BY review_status")
        rows = cursor.fetchall()

    print("\n🔍 Human Review Audit Status:")
    for r in rows:
        print(f"   * {r[0].upper():<14} : {r[1]} items")
    print("")

def list_repurpose_jobs_summary():
    init_db()
    jobs = get_repurpose_jobs(limit=25)
    print("\n🎬 Repurposing Jobs & Dropbox Handoff Audit:")
    print("-------------------------------------------------------------------------------------")
    print(f"{'Clip ID':<20} | {'Status':<18} | {'Duration':<10} | {'Title'}")
    print("-------------------------------------------------------------------------------------")
    if not jobs:
        print("   No repurposing jobs recorded yet.")
    else:
        for j in jobs:
            print(f"{j['clip_id']:<20} | {j['status']:<18} | {j['duration_sec']:<10.1f} | {j['title'][:32]}")
    print("-------------------------------------------------------------------------------------\n")

def retry_failed_jobs():
    init_db()
    jobs = get_repurpose_jobs(status="FAILED", limit=50)
    if not jobs:
        print("[NoorPost] No failed repurposing jobs found to retry.")
        return

    print(f"[NoorPost] Retrying {len(jobs)} failed jobs...")
    from instagram import upload_to_dropbox
    for j in jobs:
        if j.get("video_path") and Path(j["video_path"]).exists():
            log(f"🔄 Retrying upload for: {j['clip_id']}")
            res = upload_to_dropbox(j["video_path"], j.get("caption", ""))
            if res["success"]:
                update_clip_status(j["clip_id"], "HANDED_OFF_TO_MAKE", dropbox_url=res.get("url"), dropbox_id=res.get("remote_id"))
                print(f"   * {j['clip_id']} successfully uploaded to Dropbox.")
            else:
                print(f"   * {j['clip_id']} failed again: {res.get('error')}")

def main(argv=None):
    print(BANNER, flush=True)

    parser = argparse.ArgumentParser(description="NoorPost Ultimate CLI", add_help=False)
    parser.add_argument("-h", "--help", action="store_true", help="Show this help message and exit")

    # Content Engine args
    parser.add_argument("--now", action="store_true", help="Run one cycle immediately")
    parser.add_argument("--hadith-sahih", action="store_true", help="Generate verified Sahih Hadith Reel from Sunnah.com")
    parser.add_argument("--no-nasheed", action="store_true", help="Disable background nasheed audio")
    parser.add_argument("--sync-state-down", action="store_true", help="Pull persistent state from Dropbox")
    parser.add_argument("--sync-state-up", action="store_true", help="Push persistent state to Dropbox")
    parser.add_argument("--preview", action="store_true", help="Generate preview and video without publishing")
    parser.add_argument("--init-db", action="store_true", help="Initialize database")
    parser.add_argument("--stats", action="store_true", help="Show database metrics")
    parser.add_argument("--list-themes", action="store_true", help="List available themes")
    parser.add_argument("--list-categories", action="store_true", help="List all 13 canonical categories")
    parser.add_argument("--review-status", action="store_true", help="Show review status counts")
    parser.add_argument("--approve", type=int, default=None, help="Approve content item by ID")
    parser.add_argument("--reject", type=int, default=None, help="Reject content item by ID")
    parser.add_argument("--category", type=str, default=None, help="Choose content category")
    parser.add_argument("--categories", type=str, default=None, help="Comma-separated category list")
    parser.add_argument("--caption-style", type=str, default=None, help="Caption style")
    parser.add_argument("--script-style", type=str, default=None, help="Script style")
    parser.add_argument("--theme", type=str, default=None, help="Visual theme")
    parser.add_argument("--layout", type=str, default=None, help="Visual layout")
    parser.add_argument("--preset", type=str, default=None, help="Render preset: fast, balanced, high_quality")
    parser.add_argument("--duration", type=int, default=None, help="Video duration in seconds")

    # Repurposing args
    parser.add_argument("--repurpose-url", type=str, default=None, help="Authorized YouTube URL to turn into vertical Reels")
    parser.add_argument("--repurpose-file", type=str, default=None, help="Local video file to turn into vertical Reels")
    parser.add_argument("--batch", type=str, default=None, help="Batch file with URLs/paths to process")
    parser.add_argument("--confirm-rights", action="store_true", help="Confirm authorization/ownership to repurpose source")
    parser.add_argument("--clip-duration", type=float, default=45.0, help="Target clip duration in seconds (default: 45)")
    parser.add_argument("--num-clips", type=int, default=3, help="Number of clips to extract (default: 3)")
    parser.add_argument("--reframing", type=str, default="blur_fill", help="Reframing: blur_fill, center_crop, custom_crop, fit_themed")
    parser.add_argument("--timestamps", type=str, default=None, help="Manual cuts, e.g. '01:10-01:55,04:20-05:05'")
    parser.add_argument("--preview-clips", action="store_true", help="Preview selected clips and timestamps without rendering")
    parser.add_argument("--no-subtitles", action="store_true", help="Disable burning subtitles into video")
    parser.add_argument("--list-jobs", action="store_true", help="List repurposing queue and Dropbox handoff audit")
    parser.add_argument("--retry-failed", action="store_true", help="Retry failed repurpose jobs")

    # Autopilot args
    parser.add_argument("--autopilot-loop", action="store_true", help="Start persistent source-queue worker loop")
    parser.add_argument("--autopilot", action="store_true", help="Alias for --autopilot-loop")
    parser.add_argument("--autopilot-once", action="store_true", help="Process queued sources once and exit")
    parser.add_argument("--autopilot-status", action="store_true", help="Show autopilot queue status")
    parser.add_argument("--autopilot-retry", action="store_true", help="Retry failed autopilot jobs")
    parser.add_argument("--interval", "--autopilot-interval", dest="interval", type=int, default=None, help="Autopilot polling interval in minutes (default: 60)")
    parser.add_argument("--discover-channels", action="store_true", help="Discover authorized videos from approved_channels.txt")

    # Daily Scheduler args
    parser.add_argument("--scheduler", "--daily-scheduler", action="store_true", help="Start the daily Islamic content posting scheduler")

    args, unknown = parser.parse_known_args(argv)

    if args.help:
        print("Available Commands & Options:")
        parser.print_help()
        return

    # Check for unrecognized arguments
    if unknown:
        print(f"[NoorPost] [ERROR] Unrecognized argument(s): {' '.join(unknown)}")
        print("Run 'python main.py --help' to view all available commands and options.")
        sys.exit(1)

    if args.sync_state_down:
        from state_sync import state_manager
        state_manager.pull_state()
        return

    if args.sync_state_up:
        from state_sync import state_manager
        state_manager.push_state(is_dry_run=args.preview)
        return

    if args.list_themes:
        list_themes()
        return

    # ── Autopilot Handlers ──
    if args.discover_channels:
        from channel_discovery import run_channel_discovery
        res = run_channel_discovery()
        print(f"[NoorPost] Channel discovery completed: {res.get('discovered_videos', 0)} new video(s) queued.")
        return

    if args.autopilot_status:
        print_autopilot_status()
        return

    if args.autopilot_retry:
        init_autopilot_db()
        result = retry_failed_queue_jobs(confirm_rights=args.confirm_rights)
        print(f"[NoorPost] Autopilot retry: {result.get('succeeded', 0)} succeeded, {result.get('failed', 0)} failed.")
        return

    if args.autopilot_once:
        print("[NoorPost] [WORKER: AUTOPILOT ONCE (BATCH QUEUE PROCESSOR)]", flush=True)
        print(f"           Queue file: {getattr(config, 'AUTOPILOT_QUEUE_FILE', 'source_queue.txt')}")
        print(f"           Rights confirmation: {'ENABLED' if args.confirm_rights else 'DISABLED'}\n")
        result = run_queue_once(
            confirm_rights=args.confirm_rights,
            num_clips=args.num_clips,
            clip_duration=args.clip_duration,
            preset=args.preset or "balanced",
            theme=args.theme or "midnight-gold",
            reframing=args.reframing,
        )
        print(f"[NoorPost] Autopilot run complete: {result.get('succeeded', 0)} succeeded, {result.get('failed', 0)} failed.")
        return

    if args.autopilot_loop or args.autopilot:
        interval = args.interval or getattr(config, "AUTOPILOT_INTERVAL_MINUTES", 60)
        print("[NoorPost] [WORKER: AUTOPILOT SOURCE-QUEUE WORKER]", flush=True)
        print(f"           Queue file: {getattr(config, 'AUTOPILOT_QUEUE_FILE', 'source_queue.txt')}")
        print(f"           Interval: every {interval} minutes")
        print(f"           Timezone: {config.TIMEZONE}")
        print(f"           Rights confirmation: {'ENABLED' if args.confirm_rights else 'DISABLED'}")
        print("           Press Ctrl+C to stop.\n")
        try:
            start_autopilot_scheduler(
                interval_minutes=interval,
                confirm_rights=args.confirm_rights,
                num_clips=args.num_clips,
                clip_duration=args.clip_duration,
                preset=args.preset or "balanced",
                theme=args.theme or "midnight-gold",
                reframing=args.reframing,
            )
        except (KeyboardInterrupt, SystemExit):
            print("\n[NoorPost] Autopilot worker stopped by user (Ctrl+C).")
        return

    if args.list_categories:
        list_categories_summary()
        return

    if args.review_status:
        show_review_status()
        return

    if args.list_jobs:
        list_repurpose_jobs_summary()
        return

    if args.retry_failed:
        retry_failed_jobs()
        return

    if args.approve is not None:
        init_db()
        update_content_review_status(args.approve, "approved")
        print(f"[NoorPost] Content item #{args.approve} APPROVED.")
        return

    if args.reject is not None:
        init_db()
        update_content_review_status(args.reject, "rejected")
        print(f"[NoorPost] Content item #{args.reject} REJECTED.")
        return

    if args.init_db:
        print("[NoorPost] Initializing database...")
        init_db()
        sync_duas(AUTHENTIC_CONTENT)
        print("[NoorPost] Database initialized and all authentic content synced.\n")
        return

    if args.stats:
        print_stats()
        return

    # Handle Repurposing Execution
    repurpose_target = args.repurpose_url or args.repurpose_file
    if repurpose_target or args.batch:
        targets = []
        if args.batch:
            targets = source_engine.parse_batch_file(args.batch)
        else:
            targets = [repurpose_target]

        for target in targets:
            print(f"[NoorPost] Processing source: {target}")
            run_repurpose_pipeline(
                url_or_path=target,
                confirm_rights=args.confirm_rights,
                num_clips=args.num_clips,
                clip_duration=args.clip_duration,
                reframing=args.reframing,
                preset=args.preset or "balanced",
                theme=args.theme or "midnight-gold",
                timestamps=args.timestamps,
                burn_subtitles=not args.no_subtitles,
                preview_only=args.preview_clips,
                upload_dropbox=not args.preview
            )
        return

    # Existing Content Engine Execution
    categories_list = None
    if args.categories:
        categories_list = [c.strip() for c in args.categories.split(",") if c.strip()]

    target_category = None
    if args.category:
        resolved = resolve_category(args.category)
        target_category = resolved["id"] if resolved else args.category

    if args.preview:
        print("[NoorPost] PREVIEW MODE — Generating one video preview without publishing...\n")
        config.PREVIEW_ONLY = True
        run_pipeline(
            job_id="cli_preview",
            category=target_category,
            categories_list=categories_list,
            caption_style=args.caption_style,
            script_style=args.script_style,
            theme=args.theme,
            layout=args.layout,
            preset=args.preset,
            duration=args.duration,
            force_sahih_hadith=args.hadith_sahih,
            enable_audio=not args.no_nasheed,
        )
        return

    if args.now:
        print("[NoorPost] IMMEDIATE RUN — Running one complete automation cycle now...\n")
        run_pipeline(
            job_id="cli_manual",
            category=target_category,
            categories_list=categories_list,
            caption_style=args.caption_style,
            script_style=args.script_style,
            theme=args.theme,
            layout=args.layout,
            preset=args.preset,
            duration=args.duration,
            force_sahih_hadith=args.hadith_sahih,
            enable_audio=not args.no_nasheed,
        )

        # Process up to MAX_LECTURE_REELS_PER_RUN eligible lecture reels
        max_extra = getattr(config, "MAX_LECTURE_REELS_PER_RUN", 1)
        if max_extra > 0 and not args.preview:
            try:
                from channel_discovery import run_channel_discovery
                run_channel_discovery(max_new_videos=max_extra)

                from autopilot import get_pending_jobs, process_single_job
                pending = get_pending_jobs()
                if pending:
                    log(f"🎬 Processing up to {max_extra} extra eligible lecture Reel(s) from queue...")
                    for job in pending[:max_extra]:
                        process_single_job(
                            job=job,
                            confirm_rights=True,
                            preset=args.preset or "balanced",
                            theme=args.theme or "midnight-gold",
                            num_clips=1
                        )
            except Exception as e:
                log(f"ℹ️  Extra lecture processing notice: {e}", level="INFO")

        return

    # Daily Scheduler
    # Started either with --scheduler / --daily-scheduler or by default when running main.py without arguments
    slots_str = ", ".join(f"{t['hour']:02d}:{t['minute']:02d}" for t in config.POST_TIMES)
    print("[NoorPost] [WORKER: DAILY POSTING SCHEDULER]", flush=True)
    print(f"           Timezone: {config.TIMEZONE}")
    print(f"           Configured slots: {slots_str}")
    print("           Press Ctrl+C to stop.\n")
    try:
        start_scheduler()
    except (KeyboardInterrupt, SystemExit):
        print("\n[NoorPost] Daily scheduler stopped by user (Ctrl+C).")

if __name__ == "__main__":
    main()

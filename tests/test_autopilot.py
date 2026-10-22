"""
test_autopilot.py — Tests for NoorPost Autopilot Queue Processor

Covers:
- Queue file parsing (comments, blanks, valid entries).
- SQLite duplicate prevention (same entry never inserted twice).
- Job state transitions (QUEUED -> PROCESSING -> COMPLETED/FAILED).
- Restart recovery (PROCESSING jobs are re-picked on resume).
- Retry logic (FAILED jobs under max_attempts are retryable).
- Mocked pipeline integration (no real downloads or Dropbox uploads).
- YouTube rights enforcement.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from autopilot import (
    init_autopilot_db,
    parse_queue_file,
    sync_queue_to_db,
    get_pending_jobs,
    get_retryable_jobs,
    update_job_status,
    list_all_jobs,
    process_single_job,
    run_queue_once,
    retry_failed_queue_jobs,
    _hash_entry,
    _is_youtube_url,
    print_autopilot_status,
)
from database import init_db, _get_connection

# Use a temp database for all tests
_TEST_DB = None


def setUpModule():
    """Create a temporary database for autopilot tests."""
    global _TEST_DB
    _TEST_DB = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    _TEST_DB.close()

    import config
    config.DB_PATH = _TEST_DB.name

    init_autopilot_db()


def tearDownModule():
    """Clean up temp database."""
    global _TEST_DB
    if _TEST_DB and os.path.exists(_TEST_DB.name):
        os.unlink(_TEST_DB.name)


class TestQueueFileParsing(unittest.TestCase):
    """Test source_queue.txt parsing."""

    def test_parse_empty_creates_file(self):
        """An empty/missing queue file is created with header comments."""
        with tempfile.TemporaryDirectory() as tmp:
            qf = Path(tmp) / "source_queue.txt"
            self.assertFalse(qf.exists())

            entries = parse_queue_file(qf)
            self.assertEqual(entries, [])
            self.assertTrue(qf.exists())

            # Reading again should still return empty (only comments)
            entries2 = parse_queue_file(qf)
            self.assertEqual(entries2, [])

    def test_parse_with_comments_and_blanks(self):
        """Comments and blank lines are ignored, valid entries are returned."""
        with tempfile.TemporaryDirectory() as tmp:
            qf = Path(tmp) / "source_queue.txt"
            qf.write_text(
                "# This is a comment\n"
                "\n"
                "https://www.youtube.com/watch?v=TEST123\n"
                "   \n"
                "# Another comment\n"
                "D:\\lectures\\khutbah.mp4\n"
                "\n",
                encoding="utf-8"
            )
            entries = parse_queue_file(qf)
            self.assertEqual(len(entries), 2)
            self.assertIn("https://www.youtube.com/watch?v=TEST123", entries)
            self.assertIn("D:\\lectures\\khutbah.mp4", entries)

    def test_parse_strips_whitespace(self):
        """Leading/trailing whitespace is stripped from entries."""
        with tempfile.TemporaryDirectory() as tmp:
            qf = Path(tmp) / "source_queue.txt"
            qf.write_text(
                "  https://youtube.com/watch?v=A  \n"
                "  D:\\video.mp4  \n",
                encoding="utf-8"
            )
            entries = parse_queue_file(qf)
            self.assertEqual(entries[0], "https://youtube.com/watch?v=A")
            self.assertEqual(entries[1], "D:\\video.mp4")


class TestDuplicatePrevention(unittest.TestCase):
    """Test SQLite-backed duplicate prevention."""

    def setUp(self):
        """Clear autopilot_queue for each test."""
        with _get_connection() as conn:
            conn.execute("DELETE FROM autopilot_queue")
            conn.commit()

    def test_sync_new_entries(self):
        """New entries are inserted into the database."""
        count = sync_queue_to_db(["https://youtube.com/watch?v=NEW1", "D:\\new.mp4"])
        self.assertEqual(count, 2)

        jobs = list_all_jobs()
        self.assertEqual(len(jobs), 2)

    def test_sync_prevents_duplicates(self):
        """The same entry is never inserted twice."""
        sync_queue_to_db(["https://youtube.com/watch?v=DUP1"])
        sync_queue_to_db(["https://youtube.com/watch?v=DUP1"])

        jobs = list_all_jobs()
        self.assertEqual(len(jobs), 1)

    def test_sync_case_insensitive_dedup(self):
        """Duplicate detection is case-insensitive for URLs."""
        sync_queue_to_db(["https://YouTube.com/watch?v=CASE"])
        count = sync_queue_to_db(["https://youtube.com/watch?v=case"])
        self.assertEqual(count, 0)  # Already exists

    def test_hash_deterministic(self):
        """Same input always produces same hash."""
        h1 = _hash_entry("https://youtube.com/watch?v=X")
        h2 = _hash_entry("https://youtube.com/watch?v=X")
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 20)


class TestJobStateManagement(unittest.TestCase):
    """Test job status transitions and resume logic."""

    def setUp(self):
        with _get_connection() as conn:
            conn.execute("DELETE FROM autopilot_queue")
            conn.commit()

    def test_status_transitions(self):
        """Jobs progress through QUEUED -> PROCESSING -> COMPLETED."""
        sync_queue_to_db(["https://youtube.com/watch?v=STATE1"])
        jobs = get_pending_jobs()
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["status"], "QUEUED")

        update_job_status(jobs[0]["id"], "PROCESSING")
        updated = list_all_jobs()
        self.assertEqual(updated[0]["status"], "PROCESSING")
        self.assertIsNotNone(updated[0]["started_at"])
        self.assertEqual(updated[0]["attempts"], 1)

        update_job_status(jobs[0]["id"], "COMPLETED", num_clips=3)
        updated2 = list_all_jobs()
        self.assertEqual(updated2[0]["status"], "COMPLETED")
        self.assertEqual(updated2[0]["num_clips_produced"], 3)
        self.assertIsNotNone(updated2[0]["completed_at"])

    def test_failed_status_records_error(self):
        """Failed jobs record error messages."""
        sync_queue_to_db(["https://youtube.com/watch?v=FAIL1"])
        jobs = get_pending_jobs()

        update_job_status(jobs[0]["id"], "PROCESSING")
        update_job_status(jobs[0]["id"], "FAILED", error_message="Connection timeout")

        failed = list_all_jobs(status_filter="FAILED")
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0]["error_message"], "Connection timeout")

    def test_restart_recovery_picks_processing_jobs(self):
        """PROCESSING jobs are re-picked after a crash/restart."""
        sync_queue_to_db(["https://youtube.com/watch?v=CRASH1"])
        jobs = get_pending_jobs()
        update_job_status(jobs[0]["id"], "PROCESSING")

        # Simulate restart — get_pending_jobs should still return this
        resumed = get_pending_jobs()
        self.assertEqual(len(resumed), 1)
        self.assertEqual(resumed[0]["status"], "PROCESSING")

    def test_completed_jobs_not_reprocessed(self):
        """COMPLETED jobs are never re-picked."""
        sync_queue_to_db(["https://youtube.com/watch?v=DONE1"])
        jobs = get_pending_jobs()
        update_job_status(jobs[0]["id"], "COMPLETED", num_clips=2)

        pending = get_pending_jobs()
        self.assertEqual(len(pending), 0)

    def test_retry_logic_respects_max_attempts(self):
        """Failed jobs exceeding max_attempts are not retried."""
        sync_queue_to_db(["https://youtube.com/watch?v=MAXRETRY"])
        jobs = get_pending_jobs()
        job_id = jobs[0]["id"]

        # Simulate 3 failed attempts
        for _ in range(3):
            update_job_status(job_id, "PROCESSING")
            update_job_status(job_id, "FAILED", error_message="Timeout")

        retryable = get_retryable_jobs()
        self.assertEqual(len(retryable), 0)  # Max attempts reached


class TestYouTubeDetection(unittest.TestCase):
    """Test YouTube URL detection."""

    def test_standard_youtube_url(self):
        self.assertTrue(_is_youtube_url("https://www.youtube.com/watch?v=abc123"))

    def test_short_youtube_url(self):
        self.assertTrue(_is_youtube_url("https://youtu.be/abc123"))

    def test_local_path_not_youtube(self):
        self.assertFalse(_is_youtube_url("D:\\lectures\\khutbah.mp4"))

    def test_empty_string(self):
        self.assertFalse(_is_youtube_url(""))


class TestMockedPipelineProcessing(unittest.TestCase):
    """Test autopilot processing with mocked repurpose pipeline and Dropbox."""

    def setUp(self):
        with _get_connection() as conn:
            conn.execute("DELETE FROM autopilot_queue")
            conn.commit()

    @patch("autopilot.run_repurpose_pipeline")
    def test_successful_local_file_processing(self, mock_pipeline):
        """A local file job completes successfully with mocked pipeline."""
        mock_pipeline.return_value = {
            "status": "completed",
            "source_id": "local_abc",
            "clips": [{"clip_id": "c01"}, {"clip_id": "c02"}]
        }

        sync_queue_to_db(["D:\\lectures\\test_khutbah.mp4"])
        jobs = get_pending_jobs()

        result = process_single_job(jobs[0], confirm_rights=False)
        self.assertEqual(result["status"], "completed")

        updated = list_all_jobs()
        self.assertEqual(updated[0]["status"], "COMPLETED")
        self.assertEqual(updated[0]["num_clips_produced"], 2)

        mock_pipeline.assert_called_once()

    @patch("autopilot.run_repurpose_pipeline")
    def test_youtube_requires_rights_confirmation(self, mock_pipeline):
        """YouTube sources without --confirm-rights are rejected."""
        sync_queue_to_db(["https://www.youtube.com/watch?v=NOAUTH"])
        jobs = get_pending_jobs()

        result = process_single_job(jobs[0], confirm_rights=False)
        self.assertEqual(result["status"], "failed")
        self.assertIn("requires --confirm-rights", result["error"])

        updated = list_all_jobs()
        self.assertEqual(updated[0]["status"], "FAILED")

        # Pipeline should never be called without rights
        mock_pipeline.assert_not_called()

    @patch("autopilot.run_repurpose_pipeline")
    def test_youtube_with_rights_proceeds(self, mock_pipeline):
        """YouTube sources with --confirm-rights are processed."""
        mock_pipeline.return_value = {
            "status": "completed",
            "source_id": "yt_abc",
            "clips": [{"clip_id": "c01"}]
        }

        sync_queue_to_db(["https://www.youtube.com/watch?v=AUTHED"])
        jobs = get_pending_jobs()

        result = process_single_job(jobs[0], confirm_rights=True)
        self.assertEqual(result["status"], "completed")

        # Verify confirm_rights was passed correctly
        call_kwargs = mock_pipeline.call_args[1]
        self.assertTrue(call_kwargs["confirm_rights"])

    @patch("autopilot.run_repurpose_pipeline")
    def test_pipeline_exception_marks_failed(self, mock_pipeline):
        """Pipeline exceptions are caught and job is marked FAILED."""
        mock_pipeline.side_effect = RuntimeError("FFmpeg not found")

        sync_queue_to_db(["D:\\lectures\\broken.mp4"])
        jobs = get_pending_jobs()

        result = process_single_job(jobs[0])
        self.assertEqual(result["status"], "failed")
        self.assertIn("FFmpeg not found", result["error"])

    @patch("autopilot.run_repurpose_pipeline")
    def test_run_queue_once_processes_all_pending(self, mock_pipeline):
        """run_queue_once processes all QUEUED entries sequentially."""
        mock_pipeline.return_value = {
            "status": "completed", "source_id": "x", "clips": [{"clip_id": "c01"}]
        }

        # Create a temp queue file with 2 entries
        with tempfile.TemporaryDirectory() as tmp:
            qf = Path(tmp) / "source_queue.txt"
            qf.write_text(
                "D:\\lectures\\lecture1.mp4\n"
                "D:\\lectures\\lecture2.mp4\n",
                encoding="utf-8"
            )

            # Patch QUEUE_FILE
            with patch("autopilot.QUEUE_FILE", qf):
                result = run_queue_once(confirm_rights=False)

        self.assertEqual(result["processed"], 2)
        self.assertEqual(result["succeeded"], 2)
        self.assertEqual(result["failed"], 0)
        self.assertEqual(mock_pipeline.call_count, 2)

    @patch("autopilot.run_repurpose_pipeline")
    def test_retry_failed_jobs(self, mock_pipeline):
        """retry_failed_queue_jobs retries FAILED jobs under max_attempts."""
        mock_pipeline.return_value = {
            "status": "completed", "source_id": "x", "clips": []
        }

        sync_queue_to_db(["D:\\lectures\\retry_me.mp4"])
        jobs = get_pending_jobs()

        # Simulate failure
        update_job_status(jobs[0]["id"], "PROCESSING")
        update_job_status(jobs[0]["id"], "FAILED", error_message="temp error")

        result = retry_failed_queue_jobs(confirm_rights=False)
        self.assertEqual(result["retried"], 1)
        self.assertEqual(result["succeeded"], 1)

    @patch("autopilot.run_repurpose_pipeline")
    def test_mocked_dropbox_upload_in_pipeline(self, mock_pipeline):
        """Verify the pipeline is called with upload_dropbox=True."""
        mock_pipeline.return_value = {
            "status": "completed", "source_id": "x", "clips": [{"clip_id": "c01"}]
        }

        sync_queue_to_db(["D:\\lectures\\dropbox_test.mp4"])
        jobs = get_pending_jobs()
        process_single_job(jobs[0], confirm_rights=False)

        call_kwargs = mock_pipeline.call_args[1]
        self.assertTrue(call_kwargs["upload_dropbox"])

    def test_print_status_does_not_crash(self):
        """print_autopilot_status runs without errors on empty or populated queue."""
        sync_queue_to_db(["D:\\lectures\\status_test.mp4"])
        # Should not raise
        print_autopilot_status()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. CLI ROUTING & WORKER ISOLATION REGRESSION TESTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class TestCliRoutingAndWorkerIsolation(unittest.TestCase):
    """
    Regression test proving --autopilot-loop starts the source-queue worker,
    NOT the daily posting scheduler, and unrecognized arguments do not fall through.
    """

    @patch("main.start_scheduler")
    @patch("main.start_autopilot_scheduler")
    def test_autopilot_loop_dispatches_to_queue_worker_not_scheduler(
        self, mock_autopilot_sched, mock_daily_sched
    ):
        """Verify --autopilot-loop starts start_autopilot_scheduler and never start_scheduler."""
        import main
        main.main(["--autopilot-loop", "--interval", "45", "--confirm-rights"])

        mock_autopilot_sched.assert_called_once()
        mock_daily_sched.assert_not_called()

        kwargs = mock_autopilot_sched.call_args[1]
        self.assertEqual(kwargs.get("interval_minutes"), 45)
        self.assertTrue(kwargs.get("confirm_rights"))

    @patch("main.start_scheduler")
    @patch("main.start_autopilot_scheduler")
    def test_autopilot_alias_dispatches_to_queue_worker_not_scheduler(
        self, mock_autopilot_sched, mock_daily_sched
    ):
        """Verify legacy --autopilot flag also starts start_autopilot_scheduler."""
        import main
        main.main(["--autopilot"])

        mock_autopilot_sched.assert_called_once()
        mock_daily_sched.assert_not_called()

    @patch("main.start_scheduler")
    @patch("main.start_autopilot_scheduler")
    @patch("main.run_queue_once")
    def test_autopilot_once_dispatches_to_run_queue_once_not_scheduler(
        self, mock_run_once, mock_autopilot_sched, mock_daily_sched
    ):
        """Verify --autopilot-once runs run_queue_once and exits without starting any scheduler."""
        import main
        mock_run_once.return_value = {"processed": 0, "succeeded": 0, "failed": 0}
        main.main(["--autopilot-once"])

        mock_run_once.assert_called_once()
        mock_autopilot_sched.assert_not_called()
        mock_daily_sched.assert_not_called()

    @patch("main.start_scheduler")
    @patch("main.start_autopilot_scheduler")
    def test_scheduler_flag_dispatches_to_daily_scheduler(
        self, mock_autopilot_sched, mock_daily_sched
    ):
        """Verify --scheduler explicitly starts start_scheduler and not autopilot."""
        import main
        main.main(["--scheduler"])

        mock_daily_sched.assert_called_once()
        mock_autopilot_sched.assert_not_called()

    @patch("main.start_scheduler")
    @patch("main.start_autopilot_scheduler")
    def test_default_empty_args_dispatches_to_daily_scheduler(
        self, mock_autopilot_sched, mock_daily_sched
    ):
        """Verify running main.py with no arguments defaults to start_scheduler."""
        import main
        main.main([])

        mock_daily_sched.assert_called_once()
        mock_autopilot_sched.assert_not_called()

    @patch("main.start_scheduler")
    @patch("main.start_autopilot_scheduler")
    def test_unrecognized_argument_exits_without_starting_scheduler(
        self, mock_autopilot_sched, mock_daily_sched
    ):
        """Verify unknown arguments trigger sys.exit(1) and NEVER start any scheduler."""
        import main
        with self.assertRaises(SystemExit) as cm:
            main.main(["--unknown-random-flag"])

        self.assertEqual(cm.exception.code, 1)
        mock_daily_sched.assert_not_called()
        mock_autopilot_sched.assert_not_called()

    def test_overlap_prevention_lock(self):
        """Verify _queue_lock prevents overlapping queue runs."""
        import autopilot
        self.assertTrue(autopilot._queue_lock.acquire(blocking=False))
        try:
            # While lock is held, a concurrent call must be skipped
            result = autopilot.run_queue_once()
            self.assertTrue(result.get("skipped_busy"))
            self.assertEqual(result.get("processed"), 0)
        finally:
            autopilot._queue_lock.release()


if __name__ == "__main__":
    unittest.main()

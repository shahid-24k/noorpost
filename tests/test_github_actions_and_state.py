"""
test_github_actions_and_state.py — Tests for GitHub Actions Workflow & Persistent State Sync
NoorPost Ultimate
"""

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import json

from state_sync import StateSyncManager, DROPBOX_STATE_FOLDER, DROPBOX_STATE_FILE


class TestGitHubActionsWorkflow(unittest.TestCase):
    """Validate GitHub Actions workflow configuration and structure."""

    def setUp(self):
        self.workflow_file = Path(".github/workflows/noorpost.yml")

    def test_workflow_file_exists(self):
        """Verify .github/workflows/noorpost.yml exists."""
        self.assertTrue(self.workflow_file.exists())

    def test_workflow_preserves_original_schedules(self):
        """Verify original schedules: 08:00 AM IST (02:30 UTC) and 09:00 PM IST (15:30 UTC)."""
        content = self.workflow_file.read_text(encoding="utf-8")
        self.assertIn("30 2 * * *", content)
        self.assertIn("30 15 * * *", content)

    def test_workflow_concurrency_control(self):
        """Verify concurrency group exists to prevent overlapping runner jobs."""
        content = self.workflow_file.read_text(encoding="utf-8")
        self.assertIn("concurrency:", content)
        self.assertIn("noorpost-production", content)
        self.assertIn("cancel-in-progress: false", content)

    def test_workflow_dispatch_inputs(self):
        """Verify rich workflow_dispatch inputs: content_type, theme, preset, duration, enable_nasheed, dry_run."""
        content = self.workflow_file.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", content)
        self.assertIn("content_type:", content)
        self.assertIn("hadith_sahih", content)
        self.assertIn("enable_nasheed:", content)
        self.assertIn("dry_run:", content)
        self.assertIn("repurpose_url:", content)
        self.assertIn("confirm_rights:", content)

    def test_workflow_executes_safe_runner_without_eval(self):
        """Verify workflow runs scripts/run_workflow.py and completely excludes dangerous eval."""
        content = self.workflow_file.read_text(encoding="utf-8")
        self.assertIn("python scripts/run_workflow.py", content)
        self.assertNotIn("eval", content)
        self.assertNotIn("--autopilot-loop", content)

    def test_workflow_state_sync_steps(self):
        """Verify workflow pulls state before generation and pushes state after generation."""
        content = self.workflow_file.read_text(encoding="utf-8")
        self.assertIn("python main.py --sync-state-down", content)
        self.assertIn("python main.py --sync-state-up", content)

    def test_workflow_skips_state_push_on_dry_run(self):
        """Verify the state push step is skipped during dry runs to prevent production corruption."""
        content = self.workflow_file.read_text(encoding="utf-8")
        self.assertIn("github.event.inputs.dry_run != 'true'", content)


class TestPersistentStateSync(unittest.TestCase):
    """Test StateSyncManager for ephemeral GitHub Actions runners."""

    def test_state_folder_isolated_from_make_watcher(self):
        """
        Verify state file is stored in /NoorPost_State, completely isolated from
        the live Make.com watched folder (/NoorPost/*.mp4).
        """
        self.assertEqual(DROPBOX_STATE_FOLDER, "/NoorPost_State")
        self.assertTrue(DROPBOX_STATE_FILE.startswith("/NoorPost_State/"))
        self.assertFalse(DROPBOX_STATE_FILE.startswith("/NoorPost/"))

    @patch("state_sync.StateSyncManager._get_dbx_client")
    def test_pull_state_with_mocked_dropbox(self, mock_get_client):
        """Verify pull_state downloads and merges state from Dropbox."""
        mock_dbx = MagicMock()
        mock_resp = MagicMock()
        state_payload = {
            "version": "1.0",
            "last_sync": "2026-10-22T10:00:00Z",
            "published_content_ids": ["test_dua_99"],
            "published_clips": ["clip_99"],
            "publications": []
        }
        mock_resp.content = json.dumps(state_payload).encode("utf-8")
        mock_dbx.files_download.return_value = (None, mock_resp)
        mock_get_client.return_value = mock_dbx

        manager = StateSyncManager()
        data = manager.pull_state()

        self.assertIn("test_dua_99", data.get("published_content_ids", []))
        mock_dbx.files_download.assert_called_once_with(DROPBOX_STATE_FILE)

    @patch("state_sync.StateSyncManager._get_dbx_client")
    def test_push_state_with_mocked_dropbox(self, mock_get_client):
        """Verify push_state compiles SQLite state and uploads to Dropbox."""
        mock_dbx = MagicMock()
        mock_get_client.return_value = mock_dbx

        manager = StateSyncManager()
        success = manager.push_state()

        self.assertTrue(success)
        mock_dbx.files_upload.assert_called_once()
        call_args = mock_dbx.files_upload.call_args
        self.assertEqual(call_args[0][1], DROPBOX_STATE_FILE)

    @patch("state_sync.StateSyncManager._get_dbx_client")
    def test_offline_fallback_when_dropbox_unconfigured(self, mock_get_client):
        """Verify state manager falls back gracefully without Dropbox client."""
        mock_get_client.return_value = None

        manager = StateSyncManager()
        pulled = manager.pull_state()
        self.assertIsNotNone(pulled)
        pushed = manager.push_state()
        self.assertFalse(pushed)  # Returns False safely without raising

    @patch("state_sync.StateSyncManager._get_dbx_client")
    def test_push_state_skipped_on_dry_run(self, mock_get_client):
        """Verify push_state skips Dropbox upload completely when dry_run is True."""
        mock_dbx = MagicMock()
        mock_get_client.return_value = mock_dbx

        manager = StateSyncManager()
        success = manager.push_state(is_dry_run=True)

        self.assertTrue(success)
        mock_dbx.files_upload.assert_not_called()

    @patch("state_sync.StateSyncManager._get_dbx_client")
    def test_pull_state_idempotency_does_not_multiply_counts(self, mock_get_client):
        """Verify calling pull_state repeatedly does NOT repeatedly increment times_used."""
        from database import _get_connection, init_db
        init_db()

        # Seed a test item in duas_meta
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO duas_meta (
                    content_hash, content_uid, dua_index, dua_type, arabic, transliteration,
                    translation, source, times_used, is_verified, created_at
                ) VALUES ('hash_idem_test', 'uid_idem_test', 0, 'Dua', 'test', 'test', 'test', 'source', 1, 1, '2026-10-25')
            """)
            conn.commit()

        mock_dbx = MagicMock()
        mock_resp = MagicMock()
        state_payload = {
            "version": "2.0",
            "last_sync": "2026-10-25T10:00:00Z",
            "published_content": [
                {
                    "content_hash": "hash_idem_test",
                    "content_uid": "uid_idem_test",
                    "times_used": 1,
                    "last_used_at": "2026-10-25T10:00:00Z"
                }
            ],
            "published_content_ids": ["uid_idem_test"],
            "publications": []
        }
        mock_resp.content = json.dumps(state_payload).encode("utf-8")
        mock_dbx.files_download.return_value = (None, mock_resp)
        mock_get_client.return_value = mock_dbx

        manager = StateSyncManager()
        # Pull once
        manager.pull_state()
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT times_used FROM duas_meta WHERE content_hash = 'hash_idem_test'")
            count_after_first = cursor.fetchone()[0]

        # Pull second time
        manager.pull_state()
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT times_used FROM duas_meta WHERE content_hash = 'hash_idem_test'")
            count_after_second = cursor.fetchone()[0]

        self.assertEqual(count_after_first, count_after_second, "Repeated pull_state must be idempotent!")

    @patch("state_sync.StateSyncManager._get_dbx_client")
    def test_pull_state_fails_closed_on_network_or_auth_error(self, mock_get_client):
        """Verify pull_state fails closed (raises RuntimeError) when Dropbox fails with a non-404 error in production."""
        mock_dbx = MagicMock()
        mock_dbx.files_download.side_effect = ConnectionResetError("Connection reset by peer")
        mock_get_client.return_value = mock_dbx

        manager = StateSyncManager()
        with self.assertRaises(RuntimeError) as ctx:
            manager.pull_state(fail_closed=True)
        self.assertIn("Failing closed", str(ctx.exception))



    @patch("state_sync.StateSyncManager._is_dropbox_configured", return_value=True)
    @patch("instagram.get_dropbox_client")
    def test_dropbox_client_init_failure_fails_closed_when_credentials_configured(self, mock_client_init, mock_is_conf):
        """
        Verify that if Dropbox credentials are configured but client creation fails,
        pull_state does NOT silently fall back to empty local state, but fails closed.
        """
        mock_client_init.side_effect = ValueError("Invalid OAuth refresh token or app key")
        manager = StateSyncManager()

        with self.assertRaises(RuntimeError) as ctx:
            manager.pull_state(fail_closed=True)
        self.assertIn("Dropbox client initialization failed", str(ctx.exception))
        self.assertIn("Failing closed", str(ctx.exception))

    @patch("state_sync.StateSyncManager._is_dropbox_configured", return_value=True)
    @patch("instagram.get_dropbox_client")
    def test_dropbox_client_init_failure_graceful_in_preview(self, mock_client_init, mock_is_conf):
        """
        Verify that in preview / dry-run mode (fail_closed=False),
        Dropbox client initialization failure falls back gracefully to local state.
        """
        mock_client_init.side_effect = ValueError("Network unreachable")
        manager = StateSyncManager()
        pulled = manager.pull_state(fail_closed=False)
        self.assertIsNotNone(pulled)
        self.assertIn("version", pulled)

    @patch("state_sync.StateSyncManager._get_dbx_client")
    def test_missing_remote_file_initializes_fresh_state_cleanly(self, mock_get_client):
        """
        Verify that when remote state file is missing on Dropbox (404/not_found),
        it initializes clean initial state without raising an error.
        """
        import dropbox
        mock_dbx = MagicMock()
        path_error = MagicMock()
        path_error.is_not_found.return_value = True
        lookup_error = MagicMock()
        lookup_error.is_path.return_value = True
        lookup_error.get_path.return_value = path_error
        
        mock_dbx.files_download.side_effect = dropbox.exceptions.ApiError(
            request_id="test-req",
            error=lookup_error,
            user_message_text="not_found",
            user_message_locale="en"
        )
        mock_get_client.return_value = mock_dbx

        manager = StateSyncManager()
        data = manager.pull_state(fail_closed=True)
        self.assertIsNotNone(data)
        self.assertEqual(data.get("version"), "2.0")

    @patch("state_sync.StateSyncManager._get_dbx_client")
    def test_network_connection_reset_fails_closed(self, mock_get_client):
        """Verify socket gaierror / network failure triggers fail-closed in production."""
        mock_dbx = MagicMock()
        mock_dbx.files_download.side_effect = ConnectionResetError("Connection reset by peer")
        mock_get_client.return_value = mock_dbx

        manager = StateSyncManager()
        with self.assertRaises(RuntimeError) as ctx:
            manager.pull_state(fail_closed=True)
        self.assertIn("Failing closed", str(ctx.exception))

    @patch("state_sync.StateSyncManager._get_dbx_client")
    def test_reconcile_all_state_categories_into_sqlite(self, mock_get_client):
        """
        Verify that pull_state reconciles:
        - published_content
        - published_clips
        - repurpose_clips
        - repurpose_sources
        - nasheed_history
        - autopilot_queue
        - publications
        """
        from database import _get_connection, init_db
        init_db()

        mock_dbx = MagicMock()
        mock_resp = MagicMock()
        state_payload = {
            "version": "2.0",
            "last_sync": "2026-11-03T10:00:00Z",
            "published_content": [
                {
                    "content_hash": "hash_cat_test_1",
                    "content_uid": "uid_cat_test_1",
                    "times_used": 3,
                    "last_used_at": "2026-11-03T10:00:00Z"
                }
            ],
            "published_content_ids": ["uid_cat_test_1"],
            "published_clips": ["clip_published_abc"],
            "repurpose_sources": [
                {
                    "source_id": "src_test_full_1",
                    "source_type": "youtube",
                    "source_url": "https://youtube.com/watch?v=full_test",
                    "title": "Full Source Title",
                    "channel": "Islam Channel",
                    "duration": 600.0,
                    "language": "en",
                    "rights_confirmed": 1,
                    "status": "PROCESSED"
                }
            ],
            "repurpose_clips": [
                {
                    "clip_id": "clip_published_abc",
                    "source_id": 1,
                    "clip_index": 0,
                    "start_sec": 10.0,
                    "end_sec": 40.0,
                    "duration_sec": 30.0,
                    "title": "Clip Title",
                    "status": "UPLOADED",
                    "dropbox_url": "https://dropbox.com/s/clip.mp4",
                    "dropbox_id": "/NoorPost/clip.mp4"
                }
            ],
            "nasheed_history": [
                {
                    "track_id": "nasheed_track_123",
                    "track_title": "Nasheed Track Title",
                    "times_used": 5,
                    "last_used_at": "2026-11-03T10:00:00Z"
                }
            ],
            "autopilot_queue": [
                {
                    "source_entry": "https://youtube.com/watch?v=queue_test",
                    "source_hash": "hash_queue_test_1",
                    "status": "COMPLETED",
                    "num_clips_produced": 2,
                    "attempts": 1,
                    "channel": "Islam Channel",
                    "rights_confirmed": 1
                }
            ],
            "publications": [
                {
                    "video_id": 101,
                    "platform": "dropbox_make",
                    "status": "success",
                    "remote_url": "https://dropbox.com/s/pub.mp4",
                    "remote_id": "/NoorPost/pub.mp4",
                    "attempted_at": "2026-11-03T10:00:00Z"
                }
            ]
        }
        mock_resp.content = json.dumps(state_payload).encode("utf-8")
        mock_dbx.files_download.return_value = (None, mock_resp)
        mock_get_client.return_value = mock_dbx

        manager = StateSyncManager()
        manager.pull_state()

        with _get_connection() as conn:
            cursor = conn.cursor()

            # Check repurpose_sources
            cursor.execute("SELECT title, rights_confirmed FROM repurpose_sources WHERE source_id = 'src_test_full_1'")
            src_row = cursor.fetchone()
            self.assertIsNotNone(src_row)
            self.assertEqual(src_row["title"], "Full Source Title")
            self.assertEqual(src_row["rights_confirmed"], 1)

            # Check repurpose_clips
            cursor.execute("SELECT status, dropbox_id FROM repurpose_clips WHERE clip_id = 'clip_published_abc'")
            clip_row = cursor.fetchone()
            self.assertIsNotNone(clip_row)
            self.assertEqual(clip_row["status"], "UPLOADED")
            self.assertEqual(clip_row["dropbox_id"], "/NoorPost/clip.mp4")

            # Check nasheed_usage
            cursor.execute("SELECT times_used FROM nasheed_usage WHERE track_id = 'nasheed_track_123'")
            nash_row = cursor.fetchone()
            self.assertIsNotNone(nash_row)
            self.assertEqual(nash_row["times_used"], 5)

            # Check autopilot_queue
            cursor.execute("SELECT status, num_clips_produced FROM autopilot_queue WHERE source_hash = 'hash_queue_test_1'")
            ap_row = cursor.fetchone()
            self.assertIsNotNone(ap_row)
            self.assertEqual(ap_row["status"], "COMPLETED")
            self.assertEqual(ap_row["num_clips_produced"], 2)

            # Check publication_history
            cursor.execute("SELECT remote_id FROM publication_history WHERE remote_id = '/NoorPost/pub.mp4'")
            pub_row = cursor.fetchone()
            self.assertIsNotNone(pub_row)

    @patch("state_sync.StateSyncManager._get_dbx_client")
    def test_fresh_github_runner_preserves_remote_history_on_push(self, mock_get_client):
        """
        Simulate a fresh GitHub Actions runner:
        1. Runner boots with initial empty local state.
        2. Remote state contains prior history.
        3. Runner pulls remote state, processes a local item.
        4. Runner pushes state: must contain ALL prior history, never dropping records.
        """
        mock_dbx = MagicMock()
        mock_resp = MagicMock()
        state_payload = {
            "version": "2.0",
            "last_sync": "2026-11-03T08:00:00Z",
            "published_content": [
                {"content_hash": "remote_hash_prev", "times_used": 2, "last_used_at": "2026-11-03T08:00:00Z"}
            ],
            "published_content_ids": ["remote_hash_prev"],
            "published_clips": ["remote_clip_prev"],
            "repurpose_sources": [],
            "repurpose_clips": [],
            "nasheed_history": [{"track_id": "remote_nash_prev", "times_used": 1, "last_used_at": "2026-11-03T08:00:00Z"}],
            "autopilot_queue": [],
            "publications": [{"video_id": 999, "platform": "dropbox_make", "status": "success", "remote_id": "/NoorPost/prev.mp4", "attempted_at": "2026-11-03T08:00:00Z"}]
        }
        mock_resp.content = json.dumps(state_payload).encode("utf-8")
        mock_dbx.files_download.return_value = (None, mock_resp)
        mock_get_client.return_value = mock_dbx

        manager = StateSyncManager()
        # Step 1: pull
        manager.pull_state()

        # Step 2: build pushed state
        pushed_payload = manager._build_state_from_sqlite()

        # Step 3: verify all remote items are preserved
        self.assertIn("remote_clip_prev", pushed_payload.get("published_clips", []))
        self.assertTrue(any(nh.get("track_id") == "remote_nash_prev" for nh in pushed_payload.get("nasheed_history", [])))
        self.assertTrue(any(p.get("remote_id") == "/NoorPost/prev.mp4" for p in pushed_payload.get("publications", [])))

if __name__ == "__main__":
    unittest.main()

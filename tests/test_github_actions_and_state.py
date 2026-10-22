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

    def test_workflow_executes_one_shot_commands(self):
        """Verify workflow runs one-shot commands (python main.py ...) without blocking loops."""
        content = self.workflow_file.read_text(encoding="utf-8")
        self.assertIn("python main.py", content)
        self.assertNotIn("--autopilot-loop", content)

    def test_workflow_state_sync_steps(self):
        """Verify workflow pulls state before generation and pushes state after generation."""
        content = self.workflow_file.read_text(encoding="utf-8")
        self.assertIn("python main.py --sync-state-down", content)
        self.assertIn("python main.py --sync-state-up", content)


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


if __name__ == "__main__":
    unittest.main()

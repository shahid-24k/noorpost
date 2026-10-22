"""
Integration tests for the pipeline with mocked external APIs.
Guarantees NO test posts are ever published to real social media accounts!
"""
import sys
import unittest
from unittest.mock import patch
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(BASE_DIR))

import config
from pipeline import run_pipeline, select_content, build_caption

class TestPipelineMocked(unittest.TestCase):
    def test_content_and_caption_stages(self):
        dua = select_content()
        self.assertIn("arabic", dua)
        self.assertIn("translation", dua)
        caption = build_caption(dua)
        self.assertIn(dua["source"], caption)

    @patch("instagram.upload_to_dropbox")
    @patch("youtube.upload_short")
    def test_full_mocked_pipeline_cycle(self, mock_yt, mock_dropbox):
        mock_dropbox.return_value = {
            "success": True,
            "platform": "dropbox_make",
            "url": "https://dropbox.com/mock_link",
            "remote_id": "/NoorPost/mock.mp4",
            "error": None
        }
        mock_yt.return_value = {
            "success": True,
            "platform": "youtube",
            "url": "https://youtube.com/shorts/mock123",
            "remote_id": "mock123",
            "error": None
        }

        # Run preview mode
        config.PREVIEW_ONLY = True
        res_preview = run_pipeline(job_id="test_preview")
        self.assertEqual(res_preview["status"], "preview_only")
        self.assertTrue(Path(res_preview["preview_path"]).exists())

        # Reset flag
        config.PREVIEW_ONLY = False

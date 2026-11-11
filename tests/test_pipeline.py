"""
Integration tests for the pipeline with mocked external APIs.
No test publishes to real social media accounts.
"""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

BASE_DIR = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(BASE_DIR))

import config
from pipeline import run_pipeline, select_content, build_caption


def make_test_audio(path: Path) -> Path:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise unittest.SkipTest("ffmpeg is required for pipeline audio tests")
    subprocess.run(
        [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
         "-i", "sine=frequency=540:sample_rate=44100", "-t", "2",
         "-c:a", "libmp3lame", "-q:a", "3", str(path)],
        check=True, capture_output=True, timeout=30,
    )
    return path


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
            "success": True, "platform": "dropbox_make",
            "url": "https://dropbox.com/mock_link", "remote_id": "/NoorPost/mock.mp4",
            "error": None,
        }
        mock_yt.return_value = {
            "success": True, "platform": "youtube",
            "url": "https://youtube.com/shorts/mock123", "remote_id": "mock123",
            "error": None,
        }

        with tempfile.TemporaryDirectory() as tmp:
            audio_path = make_test_audio(Path(tmp) / "owner_track.mp3")
            audio_info = {
                "track_id": "test_owner_audio", "track_title": "Test owner audio",
                "audio_path": str(audio_path), "start_time": 0.0, "end_time": 2.0,
                "duration": 2.0, "volume": 0.35, "is_quran_recitation": False,
                "loop": True,
            }
            previous_preview_only = config.PREVIEW_ONLY
            config.PREVIEW_ONLY = True
            try:
                with patch("pipeline.nasheed_engine.prepare_audio_for_video", return_value=audio_info):
                    res_preview = run_pipeline(job_id="test_preview")
                self.assertEqual(res_preview["status"], "preview_only")
                self.assertTrue(Path(res_preview["preview_path"]).exists())
                self.assertTrue(Path(res_preview["video_path"]).exists())
            finally:
                config.PREVIEW_ONLY = previous_preview_only

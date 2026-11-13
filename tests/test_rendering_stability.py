"""
test_rendering_stability.py — Regression Tests for Fixed-Dimension Video Rendering & Validation

Verifies:
1. Balanced and High Quality presets keep zoom disabled (no variable-dimension canvas distortion).
2. Rendered video frames in Balanced and High Quality presets remain strictly 1080x1920 across all frames.
3. validate_video_file verifies H.264, 1080x1920, yuv420p, fps, and full FFmpeg decoding.
4. validate_video_file rejects corrupted files or invalid dimensions.
5. Pre-upload guard in instagram.upload_to_dropbox blocks corrupted/invalid videos from cloud upload.
6. Multi-scene videos render at strictly 1080x1920 with smooth transitions.
"""

import sys
import unittest
import tempfile
import subprocess
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(BASE_DIR))

import config
from video_generator import (
    generate_video, validate_video_file, PRESETS
)
from content_db import AUTHENTIC_CONTENT
from duas_db import DUAS
from database import init_db
from instagram import upload_to_dropbox


class TestRenderingStability(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def test_presets_have_zoom_disabled(self):
        """All rendering presets must have zoom disabled to prevent canvas distortion."""
        for preset_name in ("fast", "balanced", "high_quality"):
            self.assertIn(preset_name, PRESETS)
            self.assertFalse(
                PRESETS[preset_name].get("zoom", False),
                f"Preset '{preset_name}' must have zoom=False to keep exact 1080x1920 dimensions."
            )

    def test_balanced_preset_renders_fixed_1080x1920_valid_video(self):
        """Balanced preset render must output valid H.264 1080x1920 yuv420p video."""
        dua = DUAS[0]
        # Render a short 1s video with balanced preset
        v_path, p_path = generate_video(dua, preset="balanced", duration=1, enable_audio=False)
        self.assertTrue(Path(v_path).exists())

        # Validate using validate_video_file
        is_valid, msg, meta = validate_video_file(
            v_path,
            expected_width=1080,
            expected_height=1920,
            expected_codec="h264",
            expected_pix_fmt="yuv420p",
            expected_fps=24
        )
        self.assertTrue(is_valid, f"Balanced video validation failed: {msg}")
        self.assertEqual(meta["width"], 1080)
        self.assertEqual(meta["height"], 1920)
        self.assertEqual(meta["codec"], "h264")
        self.assertEqual(meta["pix_fmt"], "yuv420p")

        # Clean up
        Path(v_path).unlink(missing_ok=True)
        Path(p_path).unlink(missing_ok=True)

    def test_high_quality_preset_renders_fixed_1080x1920_valid_video(self):
        """High Quality preset render must output valid H.264 1080x1920 yuv420p video."""
        dua = DUAS[1]
        v_path, p_path = generate_video(dua, preset="high_quality", duration=1, enable_audio=False)
        self.assertTrue(Path(v_path).exists())

        is_valid, msg, meta = validate_video_file(
            v_path,
            expected_width=1080,
            expected_height=1920,
            expected_codec="h264",
            expected_pix_fmt="yuv420p",
            expected_fps=30
        )
        self.assertTrue(is_valid, f"High Quality video validation failed: {msg}")
        self.assertEqual(meta["width"], 1080)
        self.assertEqual(meta["height"], 1920)
        self.assertEqual(meta["codec"], "h264")
        self.assertEqual(meta["pix_fmt"], "yuv420p")

        Path(v_path).unlink(missing_ok=True)
        Path(p_path).unlink(missing_ok=True)

    def test_multi_scene_video_renders_fixed_1080x1920_valid_video(self):
        """Multi-scene render for long text must maintain 1080x1920 throughout transition."""
        long_dua = max(DUAS, key=lambda d: len(d["arabic"]))
        v_path, p_path = generate_video(long_dua, preset="balanced", duration=2, enable_audio=False)
        self.assertTrue(Path(v_path).exists())

        is_valid, msg, meta = validate_video_file(
            v_path,
            expected_width=1080,
            expected_height=1920,
            expected_codec="h264",
            expected_pix_fmt="yuv420p",
            expected_fps=24
        )
        self.assertTrue(is_valid, f"Multi-scene video validation failed: {msg}")
        self.assertEqual(meta["width"], 1080)
        self.assertEqual(meta["height"], 1920)

        Path(v_path).unlink(missing_ok=True)
        Path(p_path).unlink(missing_ok=True)

    def test_validate_video_file_rejects_corrupted_file(self):
        """validate_video_file must reject corrupted or non-video files."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(b"not a valid video header" * 1000)
            corrupted_path = f.name

        try:
            is_valid, msg, _ = validate_video_file(corrupted_path)
            self.assertFalse(is_valid, "Corrupted video must be rejected.")
        finally:
            Path(corrupted_path).unlink(missing_ok=True)

    def test_validate_video_file_rejects_wrong_dimensions(self):
        """validate_video_file must reject files that do not match 1080x1920."""
        # Create a small 640x360 test video using ffmpeg
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            small_path = f.name

        try:
            ffmpeg = shutil.which("ffmpeg")
            if ffmpeg:
                cmd = [
                    ffmpeg, "-y",
                    "-f", "lavfi", "-i", "testsrc=size=640x360:rate=24",
                    "-t", "2",
                    "-c:v", "libx264", "-b:v", "1000k", "-pix_fmt", "yuv420p",
                    small_path
                ]
                subprocess.run(cmd, capture_output=True, timeout=10)

                is_valid, msg, _ = validate_video_file(
                    small_path,
                    expected_width=1080,
                    expected_height=1920
                )
                self.assertFalse(is_valid, "Video with 640x360 must be rejected when 1080x1920 is expected.")
                self.assertIn("dimensions", msg.lower())
        finally:
            Path(small_path).unlink(missing_ok=True)

    def test_upload_to_dropbox_blocks_invalid_video(self):
        """upload_to_dropbox must reject uploading an invalid/corrupted video file."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(b"corrupted data" * 1000)
            corrupted_path = f.name

        try:
            res = upload_to_dropbox(corrupted_path, "caption")
            self.assertFalse(res["success"], "Upload to Dropbox must fail for invalid video.")
            self.assertIn("PRE_UPLOAD_VALIDATION_FAILED", res["error"])
        finally:
            Path(corrupted_path).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()

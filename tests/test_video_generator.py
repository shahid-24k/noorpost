"""
Unit tests for the professional video generator, including mandatory audio verification.
"""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageDraw

BASE_DIR = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(BASE_DIR))

import config
from video_generator import (
    generate_video, render_content_frame, create_frame,
    wrap_and_shape_arabic, get_font, PRESETS
)
from duas_db import DUAS
from database import init_db, record_video, _get_connection


def make_test_audio(path: Path, seconds: float = 2.0) -> Path:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise unittest.SkipTest("ffmpeg is required for video audio tests")
    subprocess.run(
        [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
         "-i", "sine=frequency=660:sample_rate=44100", "-t", str(seconds),
         "-c:a", "libmp3lame", "-q:a", "3", str(path)],
        check=True, capture_output=True, timeout=30,
    )
    return path


class TestVideoGenerator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def test_presets_exist(self):
        self.assertIn("fast", PRESETS)
        self.assertIn("balanced", PRESETS)
        self.assertIn("high_quality", PRESETS)

    def test_frame_dimensions_and_aspect_ratio(self):
        dua = DUAS[0]
        frame = render_content_frame(
            dua,
            theme={
                "bg_top": (10, 10, 10), "bg_bottom": (5, 5, 5),
                "gold": (200, 160, 50), "gold_dim": (120, 90, 30),
                "text_primary": (240, 240, 240), "text_secondary": (150, 150, 150),
            },
        )
        self.assertEqual(frame.size, (1080, 1920))
        self.assertAlmostEqual(frame.width / frame.height, 9.0 / 16.0, places=3)

    def test_arabic_shaping_and_wrapping(self):
        font = get_font(config.FONT_ARABIC, 48)
        img = Image.new("RGB", (1080, 400))
        draw = ImageDraw.Draw(img)
        sample = "رَبَّنَا آتِنَا فِي الدُّنْيَا حَسَنَةً وَفِي الْآخِرَةِ حَسَنَةً وَقِنَا عَذَابَ النَّارِ"
        lines = wrap_and_shape_arabic(sample, font, 900, draw)
        self.assertTrue(lines)
        self.assertTrue(all(len(line) > 0 for line in lines))

    def test_multi_scene_frame_rendering(self):
        long_dua = max(DUAS, key=lambda d: len(d["arabic"]))
        theme = {
            "bg_top": (10, 10, 10), "bg_bottom": (5, 5, 5),
            "gold": (200, 160, 50), "gold_dim": (120, 90, 30),
            "text_primary": (240, 240, 240), "text_secondary": (150, 150, 150),
        }
        f1 = render_content_frame(long_dua, theme, scene_mode="scene1_arabic")
        f2 = render_content_frame(long_dua, theme, scene_mode="scene2_translation")
        self.assertEqual(f1.size, (1080, 1920))
        self.assertEqual(f2.size, (1080, 1920))

    def test_unique_output_filenames_and_creation_with_verified_audio(self):
        dua = DUAS[1]
        with tempfile.TemporaryDirectory() as tmp:
            audio_path = make_test_audio(Path(tmp) / "owner_track.mp3", 2.0)
            audio_info = {
                "audio_path": str(audio_path), "start_time": 0.0, "end_time": 2.0,
                "duration": 2.0, "volume": 0.35, "is_quran_recitation": False,
                "loop": True,
            }
            v1, p1 = generate_video(dua, preset="fast", duration=1, audio_info=audio_info)
            v2, p2 = generate_video(dua, preset="fast", duration=1, audio_info=audio_info)

        self.assertNotEqual(v1, v2)
        self.assertNotEqual(p1, p2)
        self.assertTrue(Path(v1).exists())
        self.assertTrue(Path(v2).exists())
        self.assertGreater(Path(v1).stat().st_size, 10000)

    def test_missing_audio_blocks_video_generation(self):
        with patch("nasheed_engine.nasheed_engine.prepare_audio_for_video",
                   side_effect=RuntimeError("no approved audio")):
            with self.assertRaises(RuntimeError):
                generate_video(DUAS[0], preset="fast", duration=1)

    def test_audio_cannot_be_disabled_for_publishable_output(self):
        with self.assertRaises(RuntimeError):
            generate_video(DUAS[0], preset="fast", duration=1, enable_audio=False)

    def test_database_metadata_recording(self):
        vid = record_video(
            dua_id=1, video_path="test_video.mp4", preview_path="test_preview.jpg",
            caption="test caption", theme="emerald-serenity", font="amiri",
            duration=20, layout="dua", preset="balanced",
        )
        self.assertTrue(vid > 0)
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT theme_used, layout_used, preset_used, duration FROM video_records WHERE id = ?",
                (vid,),
            )
            row = cursor.fetchone()
            self.assertEqual(row["theme_used"], "emerald-serenity")
            self.assertEqual(row["layout_used"], "dua")
            self.assertEqual(row["preset_used"], "balanced")
            self.assertEqual(row["duration"], 20)

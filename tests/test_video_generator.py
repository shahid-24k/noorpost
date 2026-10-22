"""
Unit tests for the professional video generator, text layouts, and rendering presets.
"""
import sys
import unittest
import tempfile
from pathlib import Path
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
        theme = config.DEFAULT_THEME
        frame = render_content_frame(dua, theme={"bg_top": (10, 10, 10), "bg_bottom": (5, 5, 5), "gold": (200, 160, 50), "gold_dim": (120, 90, 30), "text_primary": (240, 240, 240), "text_secondary": (150, 150, 150)})
        self.assertEqual(frame.size, (1080, 1920))
        self.assertAlmostEqual(frame.width / frame.height, 9.0 / 16.0, places=3)

    def test_arabic_shaping_and_wrapping(self):
        font = get_font(config.FONT_ARABIC, 48)
        img = Image.new("RGB", (1080, 400))
        draw = ImageDraw.Draw(img)
        sample = "رَبَّنَا آتِنَا فِي الدُّنْيَا حَسَنَةً وَفِي الْآخِرَةِ حَسَنَةً وَقِنَا عَذَابَ النَّارِ"
        lines = wrap_and_shape_arabic(sample, font, 900, draw)
        self.assertTrue(len(lines) >= 1)
        # Verify text was shaped
        for line in lines:
            self.assertTrue(len(line) > 0)

    def test_multi_scene_frame_rendering(self):
        long_dua = max(DUAS, key=lambda d: len(d["arabic"]))
        theme = {"bg_top": (10, 10, 10), "bg_bottom": (5, 5, 5), "gold": (200, 160, 50), "gold_dim": (120, 90, 30), "text_primary": (240, 240, 240), "text_secondary": (150, 150, 150)}
        f1 = render_content_frame(long_dua, theme, scene_mode="scene1_arabic")
        f2 = render_content_frame(long_dua, theme, scene_mode="scene2_translation")
        self.assertEqual(f1.size, (1080, 1920))
        self.assertEqual(f2.size, (1080, 1920))

    def test_unique_output_filenames_and_creation(self):
        dua = DUAS[1]
        v1, p1 = generate_video(dua, preset="fast", duration=1)
        v2, p2 = generate_video(dua, preset="fast", duration=1)

        self.assertNotEqual(v1, v2, "Consecutive video generations must have unique filenames")
        self.assertNotEqual(p1, p2, "Consecutive preview generations must have unique filenames")

        p_file1 = Path(v1)
        p_file2 = Path(v2)
        self.assertTrue(p_file1.exists())
        self.assertTrue(p_file2.exists())
        self.assertTrue(p_file1.stat().st_size > 10000, "Rendered video must not be empty")

    def test_database_metadata_recording(self):
        dua = DUAS[0]
        vid = record_video(
            dua_id=1,
            video_path="test_video.mp4",
            preview_path="test_preview.jpg",
            caption="test caption",
            theme="emerald-serenity",
            font="amiri",
            duration=20,
            layout="dua",
            preset="balanced"
        )
        self.assertTrue(vid > 0)
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT theme_used, layout_used, preset_used, duration FROM video_records WHERE id = ?", (vid,))
            row = cursor.fetchone()
            self.assertEqual(row["theme_used"], "emerald-serenity")
            self.assertEqual(row["layout_used"], "dua")
            self.assertEqual(row["preset_used"], "balanced")
            self.assertEqual(row["duration"], 20)

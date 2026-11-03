"""
Unit tests for native Arabic rendering and frame creation.
"""
import sys
import unittest
from pathlib import Path
from PIL import Image

BASE_DIR = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(BASE_DIR))

from video_generator import create_frame, resolve_font_path, resolve_theme
from duas_db import DUAS

class TestRendering(unittest.TestCase):
    def test_frame_generation(self):
        dua = DUAS[0]
        font_path = resolve_font_path()
        theme = resolve_theme()
        img = create_frame(dua, font_path, theme)
        self.assertIsInstance(img, Image.Image)
        self.assertEqual(img.size, (1080, 1920))

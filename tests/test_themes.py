"""
Unit tests for visual themes and procedural Islamic artwork.
"""
import sys
import unittest
from pathlib import Path
from PIL import Image

BASE_DIR = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(BASE_DIR))

from themes import (
    THEMES, THEME_ALIASES, resolve_theme, render_themed_background,
    draw_8point_star, draw_crescent_moon, draw_hanging_lantern,
    draw_mosque_silhouette, draw_nature_mountains, draw_celestial_stars
)

class TestThemes(unittest.TestCase):
    def test_all_seven_themes_defined(self):
        expected_themes = [
            "midnight-gold",
            "emerald-serenity",
            "minimal-white",
            "peaceful-nature",
            "reflective-night",
            "masjid-elegance",
            "ramadan-eid"
        ]
        for t in expected_themes:
            self.assertIn(t, THEMES, f"Theme {t} missing from THEMES registry")

    def test_theme_aliases(self):
        self.assertEqual(resolve_theme("emerald")["name"], "Emerald Serenity")
        self.assertEqual(resolve_theme("dark-gold")["name"], "Midnight Black and Gold")
        self.assertEqual(resolve_theme("white")["name"], "Minimal White")
        self.assertEqual(resolve_theme("nature")["name"], "Peaceful Nature")
        self.assertEqual(resolve_theme("night")["name"], "Reflective Night")
        self.assertEqual(resolve_theme("mosque")["name"], "Masjid Elegance")
        self.assertEqual(resolve_theme("eid")["name"], "Ramadan and Eid")
        # Default fallback
        self.assertEqual(resolve_theme("non-existent-theme")["name"], "Midnight Black and Gold")

    def test_background_rendering_all_themes(self):
        for key, theme in THEMES.items():
            img = render_themed_background(theme, 1080, 1920)
            self.assertIsInstance(img, Image.Image)
            self.assertEqual(img.size, (1080, 1920), f"Theme {key} rendered invalid dimensions: {img.size}")
            # Verify 9:16 aspect ratio
            self.assertAlmostEqual(img.width / img.height, 9.0 / 16.0, places=3)

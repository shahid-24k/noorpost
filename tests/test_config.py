"""
Unit tests for configuration loading and secret protection.
"""
import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(BASE_DIR))

import config
from logger import mask_secrets

class TestConfig(unittest.TestCase):
    def test_timezone_default(self):
        self.assertTrue(len(config.TIMEZONE) > 0)

    def test_post_times_parsed(self):
        self.assertIsInstance(config.POST_TIMES, list)
        self.assertTrue(len(config.POST_TIMES) > 0)
        for t in config.POST_TIMES:
            self.assertIn("hour", t)
            self.assertIn("minute", t)
            self.assertTrue(0 <= t["hour"] <= 23)
            self.assertTrue(0 <= t["minute"] <= 59)

    def test_secret_masking(self):
        secret_sample = "sl.u.AGXP4dQWS_88bKI6HrlafaK-6GUza2zYjazmhYmBFiIFswtAknIa-7ofR1B"
        masked = mask_secrets(f"Uploading using token {secret_sample}")
        self.assertNotIn(secret_sample, masked)
        self.assertIn("REDACTED", masked)

    def test_directories_exist(self):
        self.assertTrue(Path(config.OUTPUT_DIR).exists())
        self.assertTrue(Path(config.PREVIEWS_DIR).exists())

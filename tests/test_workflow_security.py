"""
tests/test_workflow_security.py — Tests for Workflow Input Validation & Runner Security
Verifies that all workflow inputs are strictly validated against allowlists,
repurpose URLs are sanitized, command injection is completely blocked,
and arguments are safely passed without shell expansion or eval.
"""

import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(BASE_DIR))

from scripts.run_workflow import validate_and_build_command


class TestWorkflowSecurity(unittest.TestCase):
    def test_default_cron_schedule_run(self):
        """Cron runs provide empty environment inputs; defaults to safe --now execution."""
        cmd = validate_and_build_command({})
        self.assertIn("main.py", cmd[-2] if len(cmd) > 1 else cmd[0])
        self.assertEqual(cmd[-1], "--now")

    def test_dry_run_flag(self):
        """Dry-run flag must replace --now with --preview."""
        cmd = validate_and_build_command({"INPUT_DRY_RUN": "true"})
        self.assertIn("--preview", cmd)
        self.assertNotIn("--now", cmd)

    def test_valid_options_building(self):
        """Valid inputs are properly mapped to CLI arguments."""
        env = {
            "INPUT_DRY_RUN": "false",
            "INPUT_CONTENT_TYPE": "hadith_sahih",
            "INPUT_THEME": "emerald-serenity",
            "INPUT_PRESET": "balanced",
            "INPUT_DURATION": "20",
            "INPUT_ENABLE_NASHEED": "false"
        }
        cmd = validate_and_build_command(env)
        self.assertIn("--now", cmd)
        self.assertIn("--hadith-sahih", cmd)
        self.assertIn("--theme", cmd)
        self.assertEqual(cmd[cmd.index("--theme") + 1], "emerald-serenity")
        self.assertIn("--preset", cmd)
        self.assertEqual(cmd[cmd.index("--preset") + 1], "balanced")
        self.assertIn("--duration", cmd)
        self.assertEqual(cmd[cmd.index("--duration") + 1], "20")
        self.assertIn("--no-nasheed", cmd)

    def test_invalid_content_type_rejected(self):
        """Invalid content types outside the allowlist are rejected."""
        with self.assertRaises(ValueError) as ctx:
            validate_and_build_command({"INPUT_CONTENT_TYPE": "malicious_type"})
        self.assertIn("Invalid content_type", str(ctx.exception))

    def test_invalid_theme_rejected(self):
        """Invalid themes outside the allowlist are rejected."""
        with self.assertRaises(ValueError) as ctx:
            validate_and_build_command({"INPUT_THEME": "evil_theme"})
        self.assertIn("Invalid theme", str(ctx.exception))

    def test_invalid_preset_rejected(self):
        """Invalid rendering presets are rejected."""
        with self.assertRaises(ValueError) as ctx:
            validate_and_build_command({"INPUT_PRESET": "super_fast_hacked"})
        self.assertIn("Invalid preset", str(ctx.exception))

    def test_invalid_duration_rejected(self):
        """Durations out of bounds (< 5 or > 60) or non-integers are rejected."""
        with self.assertRaises(ValueError):
            validate_and_build_command({"INPUT_DURATION": "3"})
        with self.assertRaises(ValueError):
            validate_and_build_command({"INPUT_DURATION": "120"})
        with self.assertRaises(ValueError):
            validate_and_build_command({"INPUT_DURATION": "abc"})

    def test_repurpose_url_injection_rejected(self):
        """Dangerous shell characters or command injection in repurpose_url are strictly blocked."""
        malicious_urls = [
            "https://www.youtube.com/watch?v=123; rm -rf /",
            "https://www.youtube.com/watch?v=123 && echo hacked",
            "https://www.youtube.com/watch?v=123 | cat /etc/passwd",
            "`whoami`",
            "$(id)",
            "https://youtube.com/watch?v=abc\n--unknown-flag",
        ]
        for url in malicious_urls:
            with self.assertRaises(ValueError) as ctx:
                validate_and_build_command({
                    "INPUT_CONTENT_TYPE": "repurpose",
                    "INPUT_REPURPOSE_URL": url,
                    "INPUT_CONFIRM_RIGHTS": "true"
                })
            self.assertIn("Invalid or unsafe repurpose URL", str(ctx.exception))

    def test_valid_repurpose_url_accepted(self):
        """A clean, valid YouTube URL with rights confirmation is accepted."""
        valid_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        cmd = validate_and_build_command({
            "INPUT_CONTENT_TYPE": "repurpose",
            "INPUT_REPURPOSE_URL": valid_url,
            "INPUT_CONFIRM_RIGHTS": "true"
        })
        self.assertIn("--repurpose-url", cmd)
        self.assertEqual(cmd[cmd.index("--repurpose-url") + 1], valid_url)
        self.assertIn("--confirm-rights", cmd)


if __name__ == "__main__":
    unittest.main()

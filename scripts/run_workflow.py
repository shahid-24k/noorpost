#!/usr/bin/env python3
"""
scripts/run_workflow.py — Safe Dispatcher for GitHub Actions NoorPost Workflow
Validates all workflow_dispatch inputs against strict allowlists and regex patterns.
Constructs process argument arrays without shell expansion or eval, eliminating injection risks.
"""

import os
import sys
import re
import subprocess
from typing import List, Dict, Optional

# Strict allowlists
ALLOWED_CONTENT_TYPES = {
    "auto", "hadith_sahih", "daily_duas", "quranic_verses",
    "friday_reminders", "short_reminders", "repurpose"
}

ALLOWED_THEMES = {
    "auto", "midnight-gold", "emerald-serenity", "minimal-white",
    "peaceful-nature", "reflective-night", "masjid-elegance", "ramadan-eid"
}

ALLOWED_PRESETS = {"fast", "balanced", "high_quality"}

URL_REGEX = re.compile(
    r"^https?://[a-zA-Z0-9\-\._~:/?#\[\]@!$&'()*+,;=%]+$"
)


def validate_and_build_command(env: Optional[Dict[str, str]] = None) -> List[str]:
    """
    Validates input variables from environment and returns safe command argument list.
    Raises ValueError on invalid or malicious inputs.
    """
    if env is None:
        env = os.environ

    cmd = [sys.executable, "main.py"]

    # 1. Run Mode (Dry Run vs Live Run)
    raw_dry_run = env.get("INPUT_DRY_RUN", "").strip().lower()
    is_dry_run = raw_dry_run in ("true", "1", "yes")
    if is_dry_run:
        cmd.append("--preview")
    else:
        cmd.append("--now")

    # 2. Content Type Validation
    content_type = env.get("INPUT_CONTENT_TYPE", "auto").strip().lower()
    if not content_type:
        content_type = "auto"

    if content_type not in ALLOWED_CONTENT_TYPES:
        raise ValueError(
            f"Invalid content_type '{content_type}'. Must be one of: {sorted(ALLOWED_CONTENT_TYPES)}"
        )

    if content_type == "hadith_sahih":
        cmd.append("--hadith-sahih")
    elif content_type == "repurpose":
        raw_url = env.get("INPUT_REPURPOSE_URL", "").strip()
        if not raw_url:
            raise ValueError("INPUT_REPURPOSE_URL is required when content_type is 'repurpose'.")
        if not URL_REGEX.match(raw_url) or any(c in raw_url for c in [";", "&", "|", "`", "$", "(", ")", "\n", "\r"]):
            raise ValueError(f"Invalid or unsafe repurpose URL format: {raw_url}")

        cmd.extend(["--repurpose-url", raw_url])

        raw_confirm = env.get("INPUT_CONFIRM_RIGHTS", "").strip().lower()
        if raw_confirm in ("true", "1", "yes"):
            cmd.append("--confirm-rights")
    elif content_type != "auto":
        cmd.extend(["--category", content_type])

    # 3. Visual Theme Validation
    theme = env.get("INPUT_THEME", "auto").strip().lower()
    if not theme:
        theme = "auto"

    if theme not in ALLOWED_THEMES:
        raise ValueError(
            f"Invalid theme '{theme}'. Must be one of: {sorted(ALLOWED_THEMES)}"
        )
    if theme != "auto":
        cmd.extend(["--theme", theme])

    # 4. Rendering Preset Validation
    preset = env.get("INPUT_PRESET", "").strip().lower()
    if preset:
        if preset not in ALLOWED_PRESETS:
            raise ValueError(
                f"Invalid preset '{preset}'. Must be one of: {sorted(ALLOWED_PRESETS)}"
            )
        cmd.extend(["--preset", preset])

    # 5. Duration Validation
    raw_duration = env.get("INPUT_DURATION", "").strip()
    if raw_duration:
        try:
            dur_int = int(raw_duration)
            if not (5 <= dur_int <= 60):
                raise ValueError(f"Duration must be between 5 and 60 seconds (got {dur_int}).")
            cmd.extend(["--duration", str(dur_int)])
        except ValueError as e:
            if "between 5 and 60" in str(e):
                raise
            raise ValueError(f"Invalid duration value '{raw_duration}'. Must be an integer.")

    # 6. Nasheed Flag Validation
    raw_enable_nasheed = env.get("INPUT_ENABLE_NASHEED", "").strip().lower()
    if raw_enable_nasheed in ("false", "0", "no"):
        cmd.append("--no-nasheed")

    return cmd


def main():
    try:
        cmd = validate_and_build_command()
        print(f"[NoorPost Workflow Runner] Executing safe process: {' '.join(cmd)}")
        # Execute securely with shell=False, passing list directly to OS
        result = subprocess.run(cmd, shell=False)
        sys.exit(result.returncode)
    except Exception as e:
        print(f"::error::[Workflow Security Violation] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

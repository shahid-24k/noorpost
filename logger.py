"""
logger.py — Security-aware logging for NoorPost Ultimate
Provides file + console logging with automatic credential masking and encoding safety.
"""

import sys
import re
import os
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.resolve()
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

_SECRET_PATTERNS = [
    re.compile(r'(sl\.[a-zA-Z0-9_.-]{15,})'),                  # Dropbox access tokens (including sl.u. format)
    re.compile(r'(VGIv[a-zA-Z0-9_-]{25,})'),                  # Dropbox refresh tokens
    re.compile(r'(EAAG[a-zA-Z0-9]{25,})'),                    # Meta/Facebook tokens
    re.compile(r'(AIza[a-zA-Z0-9_-]{30,})'),                  # Google API keys
    re.compile(r'(ya29\.[a-zA-Z0-9_-]{20,})'),                # Google OAuth tokens
    re.compile(r'([a-zA-Z0-9_-]{10,}:[a-zA-Z0-9_-]{25,})'),   # Generic key:secret combos
]

def mask_secrets(text: str) -> str:
    """Replace sensitive credentials in log messages with redacted strings."""
    if not isinstance(text, str):
        text = str(text)
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub(lambda m: m.group(0)[:4] + "...[REDACTED]..." + m.group(0)[-4:], text)
    return text

def log(msg: str, level: str = "INFO"):
    """Print to console and write to daily log file with credential and encoding protection."""
    safe_msg = mask_secrets(msg)
    now = datetime.now()
    timestamp = now.strftime("%H:%M:%S")
    date_str  = now.strftime("%Y-%m-%d")

    line = f"[{timestamp}] [{level.upper()}] {safe_msg}"

    try:
        print(f"[NoorPost] {line}")
    except UnicodeEncodeError:
        safe_console = line.encode(sys.stdout.encoding or "utf-8", errors="replace").decode(sys.stdout.encoding or "utf-8")
        print(f"[NoorPost] {safe_console}")

    log_file = LOG_DIR / f"{date_str}.log"
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

"""
logger.py — Simple file + console logger for NoorPost
"""

from pathlib import Path
from datetime import datetime

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


def log(msg: str, level: str = "INFO"):
    """Print to console and write to daily log file."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    date_str  = datetime.now().strftime("%Y-%m-%d")
    line = f"[{timestamp}] [{level}] {msg}"
    print(f"[NoorPost] {line}")
    log_file = LOG_DIR / f"{date_str}.log"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line + "\n")

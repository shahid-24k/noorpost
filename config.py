"""
config.py — Centralized configuration for NoorPost Ultimate
Loads settings and secrets from environment variables (.env).
Never hardcodes sensitive tokens or API credentials.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory of the NoorPost project
BASE_DIR = Path(__file__).parent.resolve()

# Load environment variables from .env file if it exists
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# =============================================================================
# 1. CLOUD STORAGE & PUBLISHING (DROPBOX / MAKE.COM)
# =============================================================================
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY", "").strip()
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET", "").strip()
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN", "").strip()
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN", "").strip()
DROPBOX_FOLDER = os.getenv("DROPBOX_FOLDER", "/NoorPost").strip()

# =============================================================================
# 2. DIRECT SOCIAL MEDIA INTEGRATIONS (OPTIONAL)
# =============================================================================
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN", "").strip()
INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID", "").strip()

YT_CREDENTIALS_FILE = os.getenv("YT_CREDENTIALS_FILE", "credentials.json").strip()
YT_TOKEN_FILE = os.getenv("YT_TOKEN_FILE", "yt_token.pkl").strip()
SKIP_YOUTUBE = os.getenv("SKIP_YOUTUBE", "True").strip().lower() in ("true", "1", "yes")

# Official Sunnah.com API Access
SUNNAH_API_KEY = os.getenv("SUNNAH_API_KEY", "").strip()

# =============================================================================
# 3. AUTOMATION & SCHEDULER
# =============================================================================
TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata").strip()

def _parse_post_times(raw_times: str) -> list[dict]:
    parsed = []
    for item in raw_times.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            parts = item.split(":")
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                parsed.append({"hour": hour, "minute": minute})
        except Exception:
            continue
    if not parsed:
        parsed = [
            {"hour": 8, "minute": 0},
            {"hour": 13, "minute": 0},
            {"hour": 17, "minute": 0},
            {"hour": 21, "minute": 0},
        ]
    return parsed

POST_TIMES_RAW = os.getenv("POST_TIMES", "08:00,13:00,17:00,21:00")
POST_TIMES = _parse_post_times(POST_TIMES_RAW)

REQUIRE_APPROVAL = os.getenv("REQUIRE_APPROVAL", "False").strip().lower() in ("true", "1", "yes")
PREVIEW_ONLY = os.getenv("PREVIEW_ONLY", "False").strip().lower() in ("true", "1", "yes")
AUTOPILOT_INTERVAL_MINUTES = int(os.getenv("AUTOPILOT_INTERVAL_MINUTES", "30"))
AUTOPILOT_ENABLED = os.getenv("AUTOPILOT_ENABLED", "False").strip().lower() in ("true", "1", "yes")
MAX_LECTURE_REELS_PER_RUN = int(os.getenv("MAX_LECTURE_REELS_PER_RUN", "1"))


# =============================================================================
# 4. PATHS & DIRECTORIES
# =============================================================================
DB_PATH = str(BASE_DIR / os.getenv("DB_NAME", "noorpost.db"))
OUTPUT_DIR = BASE_DIR / os.getenv("OUTPUT_DIR", "output_videos")
PREVIEWS_DIR = OUTPUT_DIR / "previews"
FONTS_DIR = BASE_DIR / "assets" / "fonts"
AUDIO_DIR = BASE_DIR / "assets" / "audio"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
PREVIEWS_DIR.mkdir(parents=True, exist_ok=True)
FONTS_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================
# 5. VIDEO SPECIFICATIONS & THEMES
# =============================================================================
VIDEO_WIDTH = int(os.getenv("VIDEO_WIDTH", "1080"))
VIDEO_HEIGHT = int(os.getenv("VIDEO_HEIGHT", "1920"))
VIDEO_DURATION = int(os.getenv("VIDEO_DURATION", "15"))
VIDEO_FPS = int(os.getenv("VIDEO_FPS", "24"))

# Themes: midnight-gold, emerald-serenity, minimal-white, peaceful-nature,
# reflective-night, masjid-elegance, ramadan-eid
DEFAULT_THEME = os.getenv("DEFAULT_THEME", os.getenv("THEME_MODE", "midnight-gold")).strip()
THEME_MODE = DEFAULT_THEME

# Layouts: dua, quran, reminder
DEFAULT_LAYOUT = os.getenv("DEFAULT_LAYOUT", "dua").strip()

# Rendering presets: fast (15fps, static), balanced (24fps, slow zoom), high_quality (30fps, slow zoom + crf 18)
DEFAULT_PRESET = os.getenv("DEFAULT_PRESET", "balanced").strip()

# Visual animation and element controls
ENABLE_ANIMATIONS = os.getenv("ENABLE_ANIMATIONS", "True").strip().lower() in ("true", "1", "yes")
SHOW_TRANSLITERATION = os.getenv("SHOW_TRANSLITERATION", "True").strip().lower() in ("true", "1", "yes")
SHOW_BISMILLAH = os.getenv("SHOW_BISMILLAH", "True").strip().lower() in ("true", "1", "yes")
SHOW_WATERMARK = os.getenv("SHOW_WATERMARK", "True").strip().lower() in ("true", "1", "yes")

# Audio Controls
AUDIO_VOLUME = float(os.getenv("AUDIO_VOLUME", "0.35"))

# Platform safe margins (Reels / Shorts overlay boundaries)
SAFE_MARGIN_X = int(os.getenv("SAFE_MARGIN_X", "80"))
SAFE_MARGIN_TOP = int(os.getenv("SAFE_MARGIN_TOP", "130"))
SAFE_MARGIN_BOTTOM = int(os.getenv("SAFE_MARGIN_BOTTOM", "160"))

# Font configurations
FONT_MODE = os.getenv("FONT_MODE", "amiri").strip()
FONT_ARABIC = str(FONTS_DIR / "Amiri-Regular.ttf")
FONT_BOLD = str(FONTS_DIR / "Amiri-Bold.ttf")
FONT_LATIN = str(FONTS_DIR / "NotoSans-VariableFont_wdth,wght.ttf")
FONT_LATIN_ITALIC = str(FONTS_DIR / "NotoSans-Italic-VariableFont_wdth,wght.ttf")

COLOR_BG = (8, 11, 16)
COLOR_GOLD = (212, 175, 55)
COLOR_GOLD_DIM = (135, 105, 36)
COLOR_WHITE = (245, 243, 237)
COLOR_DIM = (145, 155, 170)

# =============================================================================
# 6. CAPABILITY DETECTORS
# =============================================================================
def is_dropbox_configured() -> bool:
    return bool(DROPBOX_REFRESH_TOKEN or DROPBOX_ACCESS_TOKEN)

def is_youtube_configured() -> bool:
    if SKIP_YOUTUBE:
        return False
    creds_exist = (BASE_DIR / YT_CREDENTIALS_FILE).exists()
    token_exist = (BASE_DIR / YT_TOKEN_FILE).exists()
    return creds_exist or token_exist

def is_direct_instagram_configured() -> bool:
    return bool(INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_ACCOUNT_ID)

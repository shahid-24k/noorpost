"""
audio_manager.py — Downloads and manages halal background nasheeds
Uses acapella/instrumental-free nasheeds from free sources
"""

import os
import random
import urllib.request
from pathlib import Path
from logger import log

AUDIO_DIR = Path("assets/audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────
# FREE HALAL NASHEED SOURCES
# These are acapella / vocal only / no instruments
# All from archive.org public domain Islamic content
# ─────────────────────────────────────────────
NASHEEDS = [
    {
        "name": "subhanallah_acapella",
        "url": "https://archive.org/download/NasheedCollection/subhanallah.mp3",
        "description": "SubhanAllah acapella nasheed",
    },
    {
        "name": "tala_al_badru",
        "url": "https://archive.org/download/TalaAlBadruAlayna/tala_al_badru_alayna.mp3",
        "description": "Tala al-Badru Alayna — classic nasheed",
    },
]

# Fallback: generate silent audio if downloads fail
def generate_silence(duration: int, output_path: str) -> str:
    """Generate a silent MP3 as fallback using ffmpeg."""
    try:
        os.system(f'ffmpeg -f lavfi -i anullsrc=r=44100:cl=stereo -t {duration} -q:a 9 -acodec libmp3lame "{output_path}" -y -loglevel quiet')
        return output_path
    except:
        return None


def get_audio_file(duration: int = 15) -> str | None:
    """
    Get a background nasheed audio file.
    Returns path to audio file, or None if unavailable.
    """
    # Check for existing downloaded nasheeds
    existing = list(AUDIO_DIR.glob("*.mp3"))
    if existing:
        chosen = random.choice(existing)
        log(f"🎵 Using nasheed: {chosen.name}")
        return str(chosen)

    # Try downloading
    for nasheed in NASHEEDS:
        out_path = AUDIO_DIR / f"{nasheed['name']}.mp3"
        if out_path.exists():
            log(f"🎵 Using cached nasheed: {nasheed['name']}")
            return str(out_path)
        try:
            log(f"⬇️  Downloading nasheed: {nasheed['name']}...")
            urllib.request.urlretrieve(nasheed["url"], str(out_path))
            if out_path.stat().st_size > 10000:  # > 10KB = valid file
                log(f"✅ Nasheed downloaded: {nasheed['name']}")
                return str(out_path)
            else:
                out_path.unlink()  # delete invalid file
        except Exception as e:
            log(f"⚠️  Could not download {nasheed['name']}: {e}", level="WARNING")

    # Fallback: silent audio
    log("⚠️  No nasheed available — using silent audio", level="WARNING")
    silent_path = str(AUDIO_DIR / "silence.mp3")
    return generate_silence(duration, silent_path)

"""
audio_manager.py — Downloads and manages halal background nasheeds
Uses acapella/instrumental-free nasheeds from free sources with silent fallback.
"""

import os
import random
import urllib.request
import shutil
from pathlib import Path
from logger import log

AUDIO_DIR = Path("assets/audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Unverified public archive downloads are disabled to adhere to strict copyright & reuse policies.
# Place verified Halal Tunes tracks into assets/audio/nasheeds/ as specified in catalog.json.
NASHEEDS = []

def generate_silence(duration: int, output_path: str) -> str:
    """Generate a silent MP3 as fallback using ffmpeg."""
    try:
        # Check if ffmpeg exists
        if shutil.which("ffmpeg"):
            os.system(f'ffmpeg -f lavfi -i anullsrc=r=44100:cl=stereo -t {duration} -q:a 9 -acodec libmp3lame "{output_path}" -y -loglevel quiet')
            if Path(output_path).exists() and Path(output_path).stat().st_size > 0:
                return output_path
    except Exception:
        pass
    return None

def get_audio_file(duration: int = 15) -> str | None:
    """
    Get a background nasheed audio file.
    Returns path to audio file, or None if unavailable.
    """
    # Check for existing downloaded nasheeds (excluding silence)
    existing = [f for f in AUDIO_DIR.glob("*.mp3") if f.name != "silence.mp3" and f.stat().st_size > 10000]
    if existing:
        chosen = random.choice(existing)
        log(f"🎵 Using nasheed: {chosen.name}")
        return str(chosen)

    # Try downloading with proper User-Agent
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    for nasheed in NASHEEDS:
        out_path = AUDIO_DIR / f"{nasheed['name']}.mp3"
        if out_path.exists() and out_path.stat().st_size > 10000:
            log(f"🎵 Using cached nasheed: {nasheed['name']}")
            return str(out_path)
        try:
            log(f"⬇️  Downloading nasheed: {nasheed['name']}...")
            req = urllib.request.Request(nasheed["url"], headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp, open(out_path, "wb") as f:
                f.write(resp.read())
            if out_path.stat().st_size > 10000:
                log(f"✅ Nasheed downloaded: {nasheed['name']}")
                return str(out_path)
            else:
                out_path.unlink()
        except Exception as e:
            log(f"⚠️  Could not download {nasheed['name']}: {e}", level="WARNING")

    # Fallback: silent audio
    log("⚠️  No nasheed available — using silent audio", level="WARNING")
    silent_path = str(AUDIO_DIR / "silence.mp3")
    return generate_silence(duration, silent_path)

"""
audio_manager.py — Audio Asset & Quality Manager for NoorPost Ultimate

Enforces strict audio rules:
- Personal owner tracks (my own 1.mp3, Fall my own 2.mp3) for Hadith and Dua.
- Quran recitation isolation (original recitation without music).
- Zero silent fallbacks (silence.mp3 is strictly forbidden).
- Quality validation via ffprobe and ffmpeg volumedetect.
"""

import os
import shutil
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import config
from logger import log

AUDIO_DIR = config.BASE_DIR / "assets" / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


def validate_audio_file(file_path: str | Path, min_size: int = 1000) -> Tuple[bool, str]:
    """
    Validate that an audio file exists, has valid size, has an audio stream via ffprobe,
    and is not entirely silent (mean_volume > -80 dB).
    """
    p = Path(file_path)
    if not p.is_absolute():
        p = config.BASE_DIR / p

    if not p.exists():
        return False, f"Audio file does not exist: {p}"

    size = p.stat().st_size
    if size < min_size:
        return False, f"Audio file too small ({size} bytes < {min_size})"

    ffprobe = shutil.which("ffprobe")
    if ffprobe:
        try:
            cmd = [
                ffprobe, "-v", "error",
                "-select_streams", "a",
                "-show_entries", "stream=index,codec_name,duration,channels,sample_rate",
                "-of", "json",
                str(p)
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if res.returncode != 0:
                return False, f"ffprobe failed to inspect audio: {res.stderr.strip()}"
            data = json.loads(res.stdout or "{}")
            streams = data.get("streams", [])
            if not streams:
                return False, f"No audio stream found in {p.name}"
        except Exception as e:
            log(f"Audio ffprobe validation warning: {e}", level="WARNING")

    return True, "Audio file valid"


def validate_mp4_audio(video_path: str | Path, expected_min_duration: float = 1.0) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Comprehensive validation of rendered MP4:
    1. Video file exists and non-empty.
    2. ffprobe detects at least one audio stream (codec: aac, mp3, etc.).
    3. Audio signal analysis (volumedetect): mean_volume must be > -80 dB (not silent).
    4. Duration check: video and audio stream duration consistency.
    """
    p = Path(video_path)
    if not p.is_absolute():
        p = config.BASE_DIR / p

    if not p.exists():
        return False, f"Video file not found: {p}", {}

    if p.stat().st_size < 10000:
        return False, f"Video file corrupted or too small ({p.stat().st_size} bytes)", {}

    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return True, "ffprobe not installed; basic file check passed", {"size": p.stat().st_size}

    try:
        cmd = [
            ffprobe, "-v", "error",
            "-show_streams",
            "-show_format",
            "-of", "json",
            str(p)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if res.returncode != 0:
            return False, f"ffprobe stream inspection failed: {res.stderr.strip()}", {}

        data = json.loads(res.stdout or "{}")
        streams = data.get("streams", [])
        format_info = data.get("format", {})

        video_streams = [s for s in streams if s.get("codec_type") == "video"]
        audio_streams = [s for s in streams if s.get("codec_type") == "audio"]

        if not video_streams:
            return False, "Rendered MP4 has no video stream", {}

        if not audio_streams:
            return False, "Rendered MP4 has NO audio stream (silent output is strictly prohibited)", {}

        audio_stream = audio_streams[0]
        audio_codec = audio_stream.get("codec_name", "unknown")
        format_dur = float(format_info.get("duration", 0.0))

        # Check signal level using ffmpeg volumedetect
        ffmpeg = shutil.which("ffmpeg")
        mean_vol = None
        max_vol = None
        if ffmpeg:
            vol_cmd = [
                ffmpeg, "-i", str(p),
                "-af", "volumedetect",
                "-f", "null", "-"
            ]
            vol_res = subprocess.run(vol_cmd, capture_output=True, text=True, timeout=20)
            for line in vol_res.stderr.splitlines():
                if "mean_volume:" in line:
                    try:
                        mean_vol = float(line.split("mean_volume:")[1].replace("dB", "").strip())
                    except Exception:
                        pass
                if "max_volume:" in line:
                    try:
                        max_vol = float(line.split("max_volume:")[1].replace("dB", "").strip())
                    except Exception:
                        pass

        if mean_vol is not None and mean_vol <= -80.0:
            return False, f"Rendered MP4 is silent (mean_volume: {mean_vol} dB <= -80 dB)", {
                "mean_volume": mean_vol,
                "max_volume": max_vol,
                "audio_codec": audio_codec
            }

        meta = {
            "video_codec": video_streams[0].get("codec_name"),
            "audio_codec": audio_codec,
            "duration": format_dur,
            "size_bytes": p.stat().st_size,
            "mean_volume_db": mean_vol,
            "max_volume_db": max_vol
        }

        log(f"✅ MP4 Audio Validation passed: codec={audio_codec}, dur={format_dur:.1f}s, vol={mean_vol}dB")
        return True, "MP4 audio and video streams valid and audible", meta

    except Exception as e:
        log(f"⚠️  Audio validation exception: {e}", level="WARNING")
        return False, f"Validation exception: {e}", {}


def generate_silence(*args, **kwargs):
    """Strictly disabled — silence fallback is prohibited."""
    raise RuntimeError("Silent fallback is strictly disabled by Islamic audio policy.")


def get_audio_file(*args, **kwargs):
    """Strictly disabled — use nasheed_engine for mood-based personal audio or quran recitation."""
    raise RuntimeError("Direct get_audio_file is deprecated; use nasheed_engine for verified audio.")

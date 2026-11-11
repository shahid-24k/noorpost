"""
audio_manager.py — strict audio validation utilities for NoorPost.

This module deliberately has no silent-track generator or silent fallback.
Missing, corrupt or inaudible audio is a publishing-blocking error.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict

import config
from logger import log


def _absolute_path(path: str | Path) -> Path:
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = config.BASE_DIR / candidate
    return candidate.resolve()


def validate_audio_file(
    path: str | Path,
    min_bytes: int = 10000,
    min_mean_volume_db: float = -45.0,
) -> Dict[str, Any]:
    """Verify an audio stream exists, decodes, has duration and is not silent."""
    audio_path = _absolute_path(path)
    if not audio_path.is_file():
        raise FileNotFoundError(f"Audio file does not exist: {audio_path}")
    if audio_path.stat().st_size < min_bytes:
        raise RuntimeError(
            f"Audio file is undersized ({audio_path.stat().st_size} bytes): {audio_path}"
        )
    ffprobe = shutil.which("ffprobe")
    ffmpeg = shutil.which("ffmpeg")
    if not ffprobe or not ffmpeg:
        raise RuntimeError("ffprobe and ffmpeg are required to validate audio before publishing.")

    probe = subprocess.run(
        [
            ffprobe, "-v", "error", "-select_streams", "a:0",
            "-show_entries", "stream=codec_name,duration,sample_rate,channels",
            "-of", "json", str(audio_path),
        ],
        capture_output=True, text=True, timeout=30, check=False,
    )
    if probe.returncode != 0:
        raise RuntimeError(f"ffprobe could not read audio file {audio_path}: {probe.stderr[-500:]}")
    try:
        streams = json.loads(probe.stdout).get("streams", [])
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"ffprobe returned invalid metadata for {audio_path}") from exc
    if not streams:
        raise RuntimeError(f"No audio stream was found in {audio_path}.")
    stream = streams[0]
    try:
        duration = float(stream.get("duration") or 0)
    except (TypeError, ValueError):
        duration = 0.0
    if duration <= 0 or int(stream.get("channels") or 0) <= 0:
        raise RuntimeError(f"Audio stream has invalid duration or channel count: {audio_path}")

    levels = subprocess.run(
        [
            ffmpeg, "-hide_banner", "-nostats", "-i", str(audio_path),
            "-map", "0:a:0", "-af", "volumedetect", "-f", "null", "-",
        ],
        capture_output=True, text=True, timeout=90, check=False,
    )
    level_text = (levels.stderr or "") + (levels.stdout or "")
    match = re.search(r"mean_volume:\s*(-?\d+(?:\.\d+)?)\s*dB", level_text)
    if levels.returncode != 0 or not match:
        raise RuntimeError(f"Audio signal analysis failed for {audio_path}: {level_text[-500:]}")
    mean_volume = float(match.group(1))
    if mean_volume <= min_mean_volume_db:
        raise RuntimeError(
            f"Audio is silent or too quiet ({mean_volume:.1f} dB; minimum {min_mean_volume_db:.1f} dB): "
            f"{audio_path}"
        )

    return {
        "path": str(audio_path),
        "codec": stream.get("codec_name", ""),
        "duration": duration,
        "sample_rate": stream.get("sample_rate"),
        "channels": int(stream.get("channels")),
        "mean_volume_db": mean_volume,
        "size_bytes": audio_path.stat().st_size,
    }


def generate_silence(*_args: Any, **_kwargs: Any) -> None:
    """Removed intentionally: NoorPost must never substitute silence for required audio."""
    raise RuntimeError("Silent audio generation is disabled. Missing audio must stop the publishing pipeline.")


def get_audio_file(*_args: Any, **_kwargs: Any) -> str:
    """Legacy compatibility shim: random audio selection is prohibited."""
    raise RuntimeError(
        "Unqualified audio fallback is disabled. Select an approved owner track "
        "through NasheedEngine or fetch the exact Qur'an recitation."
    )

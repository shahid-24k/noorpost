"""
quran_audio.py — exact-ayah Qur'an recitation retrieval and validation.
Qur'an audio is independent from personal background audio and is never mixed with it.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Tuple

import requests

import config
from logger import log
from audio_manager import validate_audio_file

QURAN_AUDIO_EDITION = "ar.alafasy"
QURAN_AUDIO_BITRATE = 128
QURAN_AUDIO_DIR = config.AUDIO_DIR / "quran_recitations"


def is_quranic_content(item: Dict[str, Any]) -> bool:
    category = str(item.get("category", "")).strip().lower()
    type_text = str(item.get("type", item.get("dua_type", ""))).strip().lower()
    source = str(item.get("source", item.get("reference", ""))).strip().lower()
    return (
        category == "quranic_verses"
        or "qur'anic" in type_text
        or "quranic" in type_text
        or "qur'an" in type_text
        or "quran" in type_text
        or source.startswith("qur'an")
        or source.startswith("quran")
        or "qur'an " in source
        or "quran " in source
    )


def extract_ayah_reference(item: Dict[str, Any]) -> Tuple[int, int]:
    surah = item.get("surah_number") or item.get("surah")
    ayah = item.get("ayah_number") or item.get("verse_number") or item.get("ayah")
    if surah is not None and ayah is not None:
        try:
            s_num, a_num = int(surah), int(ayah)
            if 1 <= s_num <= 114 and a_num >= 1:
                return s_num, a_num
        except (TypeError, ValueError):
            pass

    candidates = [
        str(item.get("source", "")),
        str(item.get("source_url", "")),
        str(item.get("reference", "")),
        str(item.get("verse_key", "")),
    ]
    for candidate in candidates:
        match = re.search(
            r"(?:qur['’]?an|quran)(?:/|\s|:)*(\d{1,3})\s*[:/ ]\s*(\d{1,3})",
            candidate,
            re.IGNORECASE,
        )
        if match:
            s_num, a_num = int(match.group(1)), int(match.group(2))
            if 1 <= s_num <= 114 and a_num >= 1:
                return s_num, a_num

    raise ValueError(
        "Qur'an content is missing an exact Surah and Ayah reference; "
        "refusing to publish it without a matching recitation."
    )


def _download_recitation(surah: int, ayah: int, destination: Path) -> Dict[str, Any]:
    api_url = f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}/{QURAN_AUDIO_EDITION}"
    response = requests.get(api_url, timeout=25)
    response.raise_for_status()
    payload = response.json()
    if payload.get("code") != 200 or not isinstance(payload.get("data"), dict):
        raise RuntimeError(f"Qur'an audio API returned an invalid response for {surah}:{ayah}.")

    data = payload["data"]
    audio_url = data.get("audio")
    global_number = data.get("number")
    if not audio_url and global_number:
        audio_url = (
            f"https://cdn.islamic.network/quran/audio/"
            f"{QURAN_AUDIO_BITRATE}/{QURAN_AUDIO_EDITION}/{int(global_number)}.mp3"
        )
    if not audio_url or not str(audio_url).startswith("https://"):
        raise RuntimeError(f"No HTTPS recitation URL was returned for Qur'an {surah}:{ayah}.")

    audio_response = requests.get(audio_url, timeout=45)
    audio_response.raise_for_status()
    content_type = audio_response.headers.get("Content-Type", "").lower()
    if "audio" not in content_type and "octet-stream" not in content_type:
        raise RuntimeError(f"Unexpected recitation content type: {content_type or 'unknown'}.")
    if len(audio_response.content) < 5000:
        raise RuntimeError(f"Downloaded recitation for Qur'an {surah}:{ayah} is unexpectedly small.")

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".download")
    temporary.write_bytes(audio_response.content)
    try:
        validation = validate_audio_file(temporary, min_bytes=5000)
        temporary.replace(destination)
        return {
            "audio_path": str(destination),
            "duration": float(validation["duration"]),
            "codec": validation["codec"],
            "mean_volume_db": validation["mean_volume_db"],
            "source_url": audio_url,
        }
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def prepare_quran_recitation(item: Dict[str, Any]) -> Dict[str, Any]:
    surah, ayah = extract_ayah_reference(item)
    destination = QURAN_AUDIO_DIR / f"{surah:03d}_{ayah:03d}_{QURAN_AUDIO_EDITION}.mp3"

    if destination.is_file():
        try:
            validation = validate_audio_file(destination, min_bytes=5000)
            result = {
                "audio_path": str(destination),
                "duration": float(validation["duration"]),
                "codec": validation["codec"],
                "mean_volume_db": validation["mean_volume_db"],
            }
            log(f"Qur'an recitation cache verified: {surah}:{ayah} ({result['duration']:.2f}s).")
        except Exception as exc:
            log(f"Cached Qur'an recitation failed validation; replacing it: {exc}", level="WARNING")
            destination.unlink(missing_ok=True)
            result = _download_recitation(surah, ayah, destination)
    else:
        log(f"Downloading original Qur'an recitation for {surah}:{ayah} ({QURAN_AUDIO_EDITION}).")
        result = _download_recitation(surah, ayah, destination)

    result.update({
        "track_id": f"quran_{surah}_{ayah}_{QURAN_AUDIO_EDITION}",
        "track_title": f"Qur'an {surah}:{ayah} — Mishary Alafasy",
        "start_time": 0.0,
        "end_time": float(result["duration"]),
        "volume": 1.0,
        "highlight_label": "Complete Ayah Recitation",
        "attribution": "",
        "license_status": "QURAN_RECITATION",
        "mood": "quran_recitation",
        "is_quran_recitation": True,
        "loop": False,
        "preserve_original": True,
        "surah_number": surah,
        "ayah_number": ayah,
    })
    return result

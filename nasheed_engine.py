"""
nasheed_engine.py — approved personal audio selection and exact Qur'an audio routing.

Normal content uses the owner's happy track.
Reflective content uses the owner's emotional track.
Qur'an content uses the exact ayah recitation only — never background music.
Missing or invalid audio is a hard failure; silent publishing is prohibited.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import config
from logger import log
from audio_manager import validate_audio_file
from quran_audio import is_quranic_content, prepare_quran_recitation

CATALOG_PATH = config.BASE_DIR / "assets" / "nasheeds" / "catalog.json"

EMOTIONAL_CATEGORIES = frozenset({"forgiveness_repentance", "evening_adhkar"})
SILENT_CATEGORIES = frozenset({"quranic_verses"})  # No *background* audio; exact recitation is attached.


class NasheedEngine:
    """Selects only approved owner-provided tracks for non-Qur'anic content."""

    def __init__(self, catalog_path: Optional[Path] = None):
        selected = Path(catalog_path) if catalog_path else CATALOG_PATH
        if not selected.is_absolute():
            selected = config.BASE_DIR / selected
        self.catalog_path = selected.resolve()
        self.catalog = self._load_catalog()

    def _load_catalog(self) -> Dict[str, Any]:
        if not self.catalog_path.is_file():
            raise RuntimeError(f"Required personal audio catalog is missing: {self.catalog_path}")
        try:
            with self.catalog_path.open("r", encoding="utf-8") as handle:
                catalog = json.load(handle)
        except Exception as exc:
            raise RuntimeError(f"Could not load personal audio catalog {self.catalog_path}: {exc}") from exc
        if not isinstance(catalog, dict) or not isinstance(catalog.get("tracks"), list):
            raise RuntimeError("Personal audio catalog is malformed: expected a tracks array.")
        return catalog

    def get_tracks(self, status: str = "APPROVED") -> List[Dict[str, Any]]:
        expected = str(status).upper()
        return [
            track for track in self.catalog["tracks"]
            if str(track.get("approval_status", "")).upper() == expected
            and str(track.get("creator", "")).strip().lower() == "owner"
            and str(track.get("external_use_permission", "")).upper() == "OWNER_APPROVED"
        ]

    def _determine_mood(self, content_item: Dict[str, Any]) -> str:
        if is_quranic_content(content_item):
            return "quran_recitation"
        category = str(content_item.get("category", "")).lower().strip()
        return "emotional" if category in EMOTIONAL_CATEGORIES else "happy"

    def select_track_for_content(self, content_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if is_quranic_content(content_item):
            return None
        mood = self._determine_mood(content_item)
        approved = self.get_tracks("APPROVED")
        matching = [track for track in approved if str(track.get("mood", "")).lower() == mood]
        if not matching:
            raise RuntimeError(
                f"No owner-approved personal audio track is available for mood '{mood}'. "
                "Publishing a silent Reel is blocked."
            )
        content_id = str(content_item.get("id", ""))
        index = sum(ord(char) for char in content_id) % len(matching)
        selected = matching[index]
        log(f"Selected owner audio: {selected.get('title', selected.get('id'))} [{mood}].")
        return selected

    def get_highlight_timing(
        self, track: Dict[str, Any], target_duration: float
    ) -> Tuple[float, float, str]:
        track_duration = float(track.get("duration", 0.0))
        if track_duration <= 0:
            raise RuntimeError(f"Track duration is missing or invalid for {track.get('id')}.")
        highlights = track.get("approved_highlights") or []
        if highlights:
            highlight = highlights[0]
            start = max(0.0, float(highlight.get("start", 0.0)))
            requested_end = float(highlight.get("end", start + target_duration))
            end = min(requested_end, track_duration)
            if end <= start:
                raise RuntimeError(f"Invalid approved audio highlight for {track.get('id')}.")
            return start, end, str(highlight.get("label", "Approved highlight"))
        start = 0.0
        return start, min(track_duration, max(0.1, float(target_duration))), "Full available track"

    def _resolve_local_path(self, track: Dict[str, Any]) -> Path:
        raw_path = str(track.get("local_path", "")).strip()
        if not raw_path:
            raise RuntimeError(f"Approved audio track {track.get('id')} has no local_path.")
        path = Path(raw_path).expanduser()
        if not path.is_absolute():
            path = config.BASE_DIR / path
        return path.resolve()

    def _ensure_track_available(self, track: Dict[str, Any]) -> Path:
        path = self._resolve_local_path(track)
        if path.is_file():
            try:
                validate_audio_file(path)
                return path
            except Exception as exc:
                log(f"Existing personal audio failed validation; refreshing it: {exc}", level="WARNING")
                path.unlink(missing_ok=True)

        remote_path = str(track.get("remote_path") or f"/NoorPost_Audio/{path.name}")
        try:
            from instagram import get_dropbox_client
            dbx = get_dropbox_client()
            log(f"Downloading owner audio from private Dropbox: {remote_path}")
            _metadata, response = dbx.files_download(remote_path)
            payload = getattr(response, "content", None)
            if not payload or len(payload) < 10000:
                raise RuntimeError("Dropbox returned an empty or undersized audio file.")
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix(path.suffix + ".download")
            temporary.write_bytes(payload)
            try:
                details = validate_audio_file(temporary)
                temporary.replace(path)
                log(
                    f"Verified owner audio download: {path.name}, "
                    f"{details['duration']:.2f}s, {details['mean_volume_db']:.1f} dB."
                )
            except Exception:
                temporary.unlink(missing_ok=True)
                raise
            return path
        except Exception as exc:
            raise RuntimeError(
                f"Required owner audio '{path.name}' could not be retrieved and validated "
                f"from Dropbox ({remote_path}): {exc}"
            ) from exc

    def prepare_audio_for_video(
        self,
        content_item: Dict[str, Any],
        target_duration: float,
        is_spoken_lecture: bool = False,
        allow_quran: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Return validated audio metadata or raise; never return a silent fallback."""
        if is_quranic_content(content_item):
            return prepare_quran_recitation(content_item)

        track = self.select_track_for_content(content_item)
        if not track:
            raise RuntimeError("No audio track was selected; publishing is blocked.")
        audio_path = self._ensure_track_available(track)
        validation = validate_audio_file(audio_path)
        start_sec, end_sec, label = self.get_highlight_timing(track, float(target_duration))
        if end_sec <= start_sec:
            raise RuntimeError(f"Selected audio segment is empty for {track.get('id')}.")

        volume = (
            getattr(config, "LECTURE_AUDIO_VOLUME", 0.12)
            if is_spoken_lecture
            else getattr(config, "AUDIO_VOLUME", 0.35)
        )
        if not 0.0 < float(volume) <= 1.0:
            raise RuntimeError(f"Configured background audio volume is invalid: {volume}.")

        return {
            "track_id": track.get("id"),
            "track_title": track.get("title"),
            "audio_path": str(audio_path),
            "start_time": start_sec,
            "end_time": end_sec,
            "duration": float(end_sec - start_sec),
            "volume": float(volume),
            "highlight_label": label,
            "attribution": "",
            "license_status": "OWNER_APPROVED",
            "mood": track.get("mood", "happy"),
            "is_quran_recitation": False,
            "loop": True,
            "preserve_original": False,
            "audio_validation": validation,
        }


nasheed_engine = NasheedEngine()

"""
nasheed_engine.py — Mood-Based Audio Selection Engine for NoorPost Ultimate

Features:
- Automatic mood-based audio selection from owner-provided personal tracks.
- Structured catalog management (assets/nasheeds/catalog.json).
- Deterministic mood matching: happy/normal content vs. sad/emotional content.
- Quran Recitation Protection: Automatically disables background audio for Qur'anic content.
- Speech Clarity Attenuation: Reduces audio volume for spoken khutbahs and lectures.
- Graceful silent fallback when no suitable audio is available.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

import config
from logger import log

CATALOG_PATH = Path("assets/nasheeds/catalog.json")

# ── Mood-to-Category Mapping ────────────────────────────────────────────────
# Categories whose content carries a sad, reflective, or emotional tone.
EMOTIONAL_CATEGORIES = frozenset({
    "forgiveness_repentance",
    "evening_adhkar",
})

# Categories that must NEVER have background audio (Quran recitation sanctity).
SILENT_CATEGORIES = frozenset({
    "quranic_verses",
})

# Everything else is treated as happy / normal mood.


class NasheedEngine:
    """Manages mood-based audio selection from owner-provided personal tracks."""

    def __init__(self, catalog_path: Optional[Path] = None):
        self.catalog_path = catalog_path or CATALOG_PATH
        self.catalog = self._load_catalog()

    def _load_catalog(self) -> Dict[str, Any]:
        if self.catalog_path.exists():
            try:
                with open(self.catalog_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                log(f"Failed to load nasheed catalog: {e}", level="WARNING")
        return {"tracks": []}

    def get_tracks(self, status: str = "APPROVED") -> List[Dict[str, Any]]:
        """Retrieve tracks filtered by approval status."""
        return [t for t in self.catalog.get("tracks", []) if t.get("approval_status") == status]

    def _determine_mood(self, content_item: Dict[str, Any]) -> str:
        """
        Determine the mood for a content item based on its category.
        Returns: 'silent', 'emotional', or 'happy'.
        """
        category = content_item.get("category", "").lower().strip()
        content_type = str(content_item.get("type", "")).lower()

        # Quran recitations are always silent
        if category in SILENT_CATEGORIES or "qur'an" in content_type or "quran" in content_type or "quran" in category:
            return "silent"

        # Sad / emotional categories
        if category in EMOTIONAL_CATEGORIES:
            return "emotional"

        # Everything else is happy / normal
        return "happy"

    def select_track_for_content(
        self,
        content_item: Dict[str, Any],
        allow_quran: Optional[bool] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Select an approved audio track matching the content mood.

        Mood rules:
        - 'silent': Quran recitations → returns None (no background audio).
        - 'emotional': forgiveness_repentance, evening_adhkar → sad/emotional track.
        - 'happy': everything else → happy/normal track.

        Falls back to None (silent) when no matching approved track is available.
        """
        category = content_item.get("category", "").lower().strip()
        content_type = str(content_item.get("type", "")).lower()

        # Sacred Recitation Protection Policy:
        # Islamic norms dictate that Qur'anic recitation should not have background music.
        allow_on_quran = allow_quran if allow_quran is not None else getattr(config, "ALLOW_NASHEED_ON_QURAN", False)
        if (category in SILENT_CATEGORIES or "qur'an" in content_type or "quran" in category) and not allow_on_quran:
            log("Background audio disabled to preserve Qur'anic recitation sanctity.", level="INFO")
            return None

        approved = self.get_tracks(status="APPROVED")
        if not approved:
            return None

        mood = self._determine_mood(content_item)

        # 1. Try to match by mood field
        mood_matched = [t for t in approved if t.get("mood") == mood]
        if mood_matched:
            # Deterministic selection based on content ID for consistency
            idx = sum(ord(c) for c in str(content_item.get("id", ""))) % len(mood_matched)
            return mood_matched[idx]

        # 2. Try to match by category in topic_tags
        tag_matched = []
        for t in approved:
            tags = [tag.lower() for tag in t.get("topic_tags", [])]
            if category in tags:
                tag_matched.append(t)

        if tag_matched:
            idx = sum(ord(c) for c in str(content_item.get("id", ""))) % len(tag_matched)
            return tag_matched[idx]

        # 3. Fallback to first approved track (happy/default)
        return approved[0]

    def get_highlight_timing(self, track: Dict[str, Any], target_duration: float) -> Tuple[float, float, str]:
        """
        Determines start and end timestamps for the highlight segment.
        Returns (start_seconds, end_seconds, label).
        """
        highlights = track.get("approved_highlights", [])
        track_dur = float(track.get("duration", 180.0))

        if highlights:
            # Pick primary highlight
            hl = highlights[0]
            start = float(hl.get("start", 0.0))
            label = hl.get("label", "Highlight Refrain")
            end = min(start + target_duration, track_dur)
            return start, end, label

        # Fallback to initial segment after brief intro
        start = 10.0 if track_dur > (10.0 + target_duration) else 0.0
        end = min(start + target_duration, track_dur)
        return start, end, "Default Intro Segment"

    def prepare_audio_for_video(
        self,
        content_item: Dict[str, Any],
        target_duration: float,
        is_spoken_lecture: bool = False,
        allow_quran: Optional[bool] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Selects track by mood, extracts highlight segment, applies fades, and sets volume.
        Returns audio details dictionary, or None if no audio should be attached.
        """
        track = self.select_track_for_content(content_item, allow_quran=allow_quran)
        if not track:
            return None

        local_path = track.get("local_path")
        if not local_path or not Path(local_path).exists() or Path(local_path).stat().st_size < 1000:
            log(f"ℹ️ Audio file for '{track.get('title')}' is not present locally ({local_path}). Defaulting to silent audio.", level="INFO")
            return None
        audio_file = local_path

        start_sec, end_sec, label = self.get_highlight_timing(track, target_duration)

        # Volume configuration: for spoken content, ensure audio is quiet and speech remains intelligible
        if is_spoken_lecture:
            volume = getattr(config, "LECTURE_AUDIO_VOLUME", 0.12)
        else:
            volume = getattr(config, "AUDIO_VOLUME", 0.35)

        return {
            "track_id": track.get("id"),
            "track_title": track.get("title"),
            "audio_path": audio_file,
            "start_time": start_sec,
            "end_time": end_sec,
            "duration": target_duration,
            "volume": volume,
            "highlight_label": label,
            "attribution": track.get("required_attribution", ""),
            "license_status": track.get("external_use_permission", "OWNER_APPROVED"),
            "mood": track.get("mood", "happy"),
        }


# Global singleton instance
nasheed_engine = NasheedEngine()

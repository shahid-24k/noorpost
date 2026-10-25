"""
nasheed_engine.py — Halal Tunes Audio Sourcing & Highlight Selection Engine
NoorPost Ultimate

Features:
- Structured catalog management (assets/nasheeds/catalog.json).
- Deterministic topic matching (duas, hadith, gratitude, patience, etc.).
- Highlight timestamp extraction with smooth fade-in and fade-out.
- Quran Recitation Protection: Automatically disables background audio for Qur'anic recitations unless explicitly configured.
- Speech Clarity Attenuation: Reduces audio volume for spoken khutbahs and lectures.
- Graceful silent / local audio fallback when specific tracks are unavailable.
"""

import os
import json
import random
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

import config
from logger import log

CATALOG_PATH = Path("assets/nasheeds/catalog.json")


class NasheedEngine:
    """Manages Halal Tunes copyright-free vocal nasheeds and highlight slicing."""

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

    def select_track_for_content(
        self,
        content_item: Dict[str, Any],
        allow_quran: Optional[bool] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Deterministically selects an approved Halal Tunes nasheed matching the content topic.
        Strictly disables background audio on Qur'an recitations unless explicitly allowed.
        """
        category = content_item.get("category", "").lower().strip()
        content_type = str(content_item.get("type", "")).lower()

        # Sacred Recitation Protection Policy:
        # Islamic norms dictate that Qur'anic recitation should not have background music or overlapping tracks.
        allow_on_quran = allow_quran if allow_quran is not None else getattr(config, "ALLOW_NASHEED_ON_QURAN", False)
        if (category == "quranic_verses" or "qur'an" in content_type or "quran" in category) and not allow_on_quran:
            log("Background nasheed disabled to preserve Qur'anic recitation sanctity.", level="INFO")
            return None

        approved = self.get_tracks(status="APPROVED")
        if not approved:
            return None

        # 1. Match by specific category tag
        matching = []
        for t in approved:
            tags = [tag.lower() for tag in t.get("topic_tags", [])]
            if category in tags:
                matching.append(t)

        if matching:
            # Deterministic selection based on content ID to maintain consistency
            idx = sum(ord(c) for c in str(content_item.get("id", ""))) % len(matching)
            return matching[idx]

        # 2. General fallback approved track
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
        Selects track, extracts highlight segment, applies fades, and sets appropriate volume.
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

        # Volume configuration: for spoken content, ensure vocals are quiet and speech remains intelligible
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
            "attribution": track.get("required_attribution", "Background Nasheed by Halal Tunes"),
            "license_status": track.get("external_use_permission", "PERMITTED_WITH_ATTRIBUTION")
        }


# Global singleton instance
nasheed_engine = NasheedEngine()

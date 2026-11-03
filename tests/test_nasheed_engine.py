"""
test_nasheed_engine.py — Tests for Nasheed Catalog & Licensing Safety
Verifies:
1. All unverified/placeholder tracks are marked NEEDS_LICENSE_REVIEW and excluded from automatic publishing.
2. Missing local audio assets gracefully return None and prevent false attribution in captions.
3. Quran recitation audio protection policy suppresses background audio.
4. Highlight selection, duration limits, and volume attenuation for spoken lectures work accurately.
"""

import unittest
import tempfile
from pathlib import Path
from nasheed_engine import NasheedEngine


class TestNasheedEngine(unittest.TestCase):
    """Tests catalog loading, track filtering, topic matching, and highlights."""

    def setUp(self):
        self.engine = NasheedEngine()

    def test_catalog_loaded_and_all_placeholder_tracks_require_review(self):
        """
        Verify catalog loads and all placeholder tracks with unverified sources
        are strictly marked NEEDS_LICENSE_REVIEW and excluded from APPROVED.
        """
        approved = self.engine.get_tracks(status="APPROVED")
        # In production audit, all placeholder tracks must be unapproved until verified proof is provided
        self.assertEqual(len(approved), 0, "No unverified placeholder tracks should be APPROVED.")

        review_tracks = self.engine.get_tracks(status="NEEDS_LICENSE_REVIEW")
        self.assertGreaterEqual(len(review_tracks), 4)
        for t in review_tracks:
            self.assertEqual(t["approval_status"], "NEEDS_LICENSE_REVIEW")
            self.assertIn(t["external_use_permission"], ("UNVERIFIED_PENDING_EXPLICIT_PROOF", "UNCLEAR"))

    def test_unverified_tracks_filtered_out_from_selection(self):
        """Verify unapproved tracks are never selected for video generation."""
        item = {"id": "test_dua_1", "category": "daily_duas", "type": "Daily Dua"}
        selected = self.engine.select_track_for_content(item)
        self.assertIsNone(selected, "Unapproved tracks must never be selected.")

    def test_missing_audio_asset_returns_none_preventing_false_attribution(self):
        """
        Verify that if an approved track points to a local MP3 that does not exist on disk,
        prepare_audio_for_video returns None rather than attaching false attribution to captions.
        """
        mock_track = {
            "id": "mock_approved_track",
            "title": "Mock Nasheed",
            "local_path": "assets/audio/nasheeds/non_existent_file.mp3",
            "duration": 180.0,
            "topic_tags": ["daily_duas"],
            "approval_status": "APPROVED",
            "required_attribution": "Background Nasheed by Artist"
        }
        custom_engine = NasheedEngine(catalog_path=Path("non_existent_catalog.json"))
        custom_engine.catalog = {"tracks": [mock_track]}

        audio_prep = custom_engine.prepare_audio_for_video(
            content_item={"id": "dua_1", "category": "daily_duas"},
            target_duration=15.0
        )
        self.assertIsNone(audio_prep, "Must return None when audio asset is missing from disk.")

    def test_quran_recitation_audio_protection(self):
        """
        Verify that by default, background nasheeds are disabled for Qur'an recitations
        to protect the sacred sanctity of Qur'anic recitation.
        """
        mock_track = {
            "id": "mock_track",
            "title": "Mock Nasheed",
            "local_path": None,
            "duration": 180.0,
            "topic_tags": ["quranic_verses"],
            "approval_status": "APPROVED",
        }
        custom_engine = NasheedEngine(catalog_path=Path("non_existent.json"))
        custom_engine.catalog = {"tracks": [mock_track]}

        quran_item = {
            "id": "quran_verse_1",
            "category": "quranic_verses",
            "type": "Qur'anic Verse"
        }
        # Default policy: None
        track = custom_engine.select_track_for_content(quran_item, allow_quran=False)
        self.assertIsNone(track)

        # When explicitly allowed
        track_allowed = custom_engine.select_track_for_content(quran_item, allow_quran=True)
        self.assertIsNotNone(track_allowed)

    def test_highlight_timing_within_duration(self):
        """Verify highlight slicing respects target video duration."""
        track = {
            "duration": 120.0,
            "approved_highlights": [{"start": 20.0, "end": 60.0, "label": "Chorus"}]
        }
        target_dur = 15.0
        start, end, label = self.engine.get_highlight_timing(track, target_dur)
        self.assertEqual(start, 20.0)
        self.assertEqual(end, 35.0)
        self.assertEqual(label, "Chorus")

    def test_spoken_lecture_volume_attenuation(self):
        """Verify spoken lectures get lower volume for speech clarity when audio exists."""
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp.write(b"0" * 2000)
            tmp_path = tmp.name

        try:
            mock_track = {
                "id": "mock_lecture_track",
                "title": "Lecture Vocal Bed",
                "local_path": tmp_path,
                "duration": 180.0,
                "topic_tags": ["general_education"],
                "approval_status": "APPROVED",
                "required_attribution": "Attribution"
            }
            custom_engine = NasheedEngine(catalog_path=Path("non_existent.json"))
            custom_engine.catalog = {"tracks": [mock_track]}

            item = {"id": "khutbah_1", "category": "general_education", "type": "Lecture"}
            audio_prep = custom_engine.prepare_audio_for_video(
                item, target_duration=30.0, is_spoken_lecture=True
            )
            self.assertIsNotNone(audio_prep)
            self.assertLessEqual(audio_prep["volume"], 0.15)
        finally:
            Path(tmp_path).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()

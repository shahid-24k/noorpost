"""
test_nasheed_engine.py — Tests for Halal Tunes Nasheed Catalog & Highlight Selection Engine
"""

import unittest
from pathlib import Path
from nasheed_engine import NasheedEngine


class TestNasheedEngine(unittest.TestCase):
    """Tests catalog loading, track filtering, topic matching, and highlights."""

    def setUp(self):
        self.engine = NasheedEngine()

    def test_catalog_loaded_and_valid(self):
        """Verify catalog loads and contains approved Halal Tunes tracks."""
        tracks = self.engine.get_tracks(status="APPROVED")
        self.assertGreater(len(tracks), 0)
        for t in tracks:
            self.assertTrue(t["id"].startswith("halaltunes_"))
            self.assertEqual(t["creator"], "Halal Tunes")
            self.assertIn("required_attribution", t)
            self.assertEqual(t["approval_status"], "APPROVED")
            self.assertEqual(t["external_use_permission"], "PERMITTED_WITH_ATTRIBUTION")

    def test_unverified_tracks_filtered_out(self):
        """Verify tracks marked NEEDS_LICENSE_REVIEW are never in approved list."""
        approved = self.engine.get_tracks(status="APPROVED")
        for t in approved:
            self.assertNotEqual(t["approval_status"], "NEEDS_LICENSE_REVIEW")

        review_tracks = self.engine.get_tracks(status="NEEDS_LICENSE_REVIEW")
        self.assertGreaterEqual(len(review_tracks), 1)

    def test_topic_matching_deterministic(self):
        """Verify topic matching maps content category to relevant track."""
        item_dua = {"id": "test_dua_1", "category": "daily_duas", "type": "Daily Dua"}
        track = self.engine.select_track_for_content(item_dua)
        self.assertIsNotNone(track)
        self.assertIn("daily_duas", [tag.lower() for tag in track.get("topic_tags", [])])

    def test_quran_recitation_audio_protection(self):
        """
        Verify that by default, background nasheeds are disabled for Qur'an recitations
        to protect the sacred sanctity of Qur'anic recitation.
        """
        quran_item = {
            "id": "quran_verse_1",
            "category": "quranic_verses",
            "type": "Qur'anic Verse"
        }
        # Default policy: None
        track = self.engine.select_track_for_content(quran_item, allow_quran=False)
        self.assertIsNone(track)

        # When explicitly allowed
        track_allowed = self.engine.select_track_for_content(quran_item, allow_quran=True)
        self.assertIsNotNone(track_allowed)

    def test_highlight_timing_within_duration(self):
        """Verify highlight slicing respects target video duration."""
        tracks = self.engine.get_tracks(status="APPROVED")
        track = tracks[0]

        target_dur = 15.0
        start, end, label = self.engine.get_highlight_timing(track, target_dur)
        self.assertGreaterEqual(start, 0.0)
        self.assertLessEqual(end, track["duration"])
        self.assertEqual(round(end - start, 1), target_dur)

    def test_spoken_lecture_volume_attenuation(self):
        """Verify spoken lectures get lower volume for speech clarity."""
        item = {"id": "khutbah_1", "category": "general_education", "type": "Lecture"}
        audio_prep = self.engine.prepare_audio_for_video(
            item, target_duration=30.0, is_spoken_lecture=True
        )
        if audio_prep:
            # Volume for spoken content must be quieter (<= 0.15)
            self.assertLessEqual(audio_prep["volume"], 0.15)


if __name__ == "__main__":
    unittest.main()

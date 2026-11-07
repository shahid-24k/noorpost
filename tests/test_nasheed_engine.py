"""
test_nasheed_engine.py — Tests for Mood-Based Audio Selection & Quran Protection

Verifies:
1. Personal owner tracks are loaded and marked APPROVED.
2. Mood-based selection: happy content → 'my own 1.mp3', emotional content → 'Fall my own 2.mp3'.
3. Quran recitation audio protection: background audio is always suppressed for quranic_verses.
4. Silent fallback when no suitable audio or audio file is missing from disk.
5. Highlight selection, duration limits, and volume attenuation for spoken lectures.
6. No Halal Tunes tracks are selected (only owner-provided personal tracks).
7. All content categories map to the correct mood and track.
"""

import unittest
import tempfile
from pathlib import Path
from nasheed_engine import NasheedEngine, EMOTIONAL_CATEGORIES, SILENT_CATEGORIES


def _make_engine_with_tracks(tracks):
    """Helper: create a NasheedEngine with a custom track list."""
    engine = NasheedEngine(catalog_path=Path("non_existent_catalog.json"))
    engine.catalog = {"tracks": tracks}
    return engine


def _make_tracks_with_files():
    """Helper: create two temp files simulating the personal MP3s and return (engine, happy_path, emotional_path)."""
    happy_tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    happy_tmp.write(b"0" * 2000)
    happy_tmp.close()

    emotional_tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    emotional_tmp.write(b"0" * 2000)
    emotional_tmp.close()

    tracks = [
        {
            "id": "personal_happy_01",
            "title": "My Own 1 — Happy & Normal",
            "local_path": happy_tmp.name,
            "duration": 15.14,
            "mood": "happy",
            "topic_tags": ["daily_duas", "morning_adhkar", "gratitude_patience",
                           "remembrance_dhikr", "prophetic_hadith", "short_reminders",
                           "ramadan", "friday_reminders", "eid_content", "general_education"],
            "approval_status": "APPROVED",
            "external_use_permission": "OWNER_APPROVED",
            "required_attribution": "",
            "approved_highlights": [{"start": 0.0, "end": 15.0, "label": "Full Track"}],
        },
        {
            "id": "personal_emotional_02",
            "title": "Fall My Own 2 — Sad & Emotional",
            "local_path": emotional_tmp.name,
            "duration": 51.67,
            "mood": "emotional",
            "topic_tags": ["forgiveness_repentance", "evening_adhkar"],
            "approval_status": "APPROVED",
            "external_use_permission": "OWNER_APPROVED",
            "required_attribution": "",
            "approved_highlights": [{"start": 0.0, "end": 45.0, "label": "Emotional Opening"}],
        },
    ]
    engine = _make_engine_with_tracks(tracks)
    return engine, happy_tmp.name, emotional_tmp.name


class TestCatalogLoading(unittest.TestCase):
    """Tests for catalog loading and track filtering."""

    def test_production_catalog_has_two_approved_personal_tracks(self):
        """Production catalog must contain exactly 2 owner-provided APPROVED tracks."""
        engine = NasheedEngine()
        approved = engine.get_tracks(status="APPROVED")
        self.assertEqual(len(approved), 2, "Catalog must have exactly 2 approved personal tracks.")

    def test_no_halal_tunes_tracks_in_catalog(self):
        """No Halal Tunes or third-party tracks should exist in the approved catalog."""
        engine = NasheedEngine()
        for track in engine.catalog.get("tracks", []):
            title = track.get("title", "").lower()
            track_id = track.get("id", "").lower()
            self.assertNotIn("halaltunes", track_id,
                             f"Halal Tunes track '{track_id}' must not be in catalog.")
            self.assertNotIn("halal tunes", title,
                             f"Halal Tunes track '{title}' must not be in catalog.")

    def test_all_approved_tracks_are_owner_provided(self):
        """All APPROVED tracks must have OWNER_APPROVED permission."""
        engine = NasheedEngine()
        for track in engine.get_tracks(status="APPROVED"):
            self.assertEqual(track.get("external_use_permission"), "OWNER_APPROVED")
            self.assertEqual(track.get("creator"), "Owner")

    def test_each_track_has_mood_field(self):
        """Every approved track must have a 'mood' field (happy or emotional)."""
        engine = NasheedEngine()
        for track in engine.get_tracks(status="APPROVED"):
            self.assertIn(track.get("mood"), ("happy", "emotional"),
                          f"Track '{track['id']}' must have mood 'happy' or 'emotional'.")


class TestMoodDetermination(unittest.TestCase):
    """Tests for _determine_mood() category-to-mood mapping."""

    def setUp(self):
        self.engine = NasheedEngine()

    def test_quran_categories_return_silent(self):
        """Quranic content must always map to 'silent' mood."""
        item = {"category": "quranic_verses", "type": "Qur'anic Verse"}
        self.assertEqual(self.engine._determine_mood(item), "silent")

    def test_quran_type_string_returns_silent(self):
        """Content with 'quran' in the type string must also map to 'silent'."""
        item = {"category": "other", "type": "Quran Recitation"}
        self.assertEqual(self.engine._determine_mood(item), "silent")

    def test_forgiveness_repentance_returns_emotional(self):
        """forgiveness_repentance category must map to 'emotional' mood."""
        item = {"category": "forgiveness_repentance", "type": "Dua"}
        self.assertEqual(self.engine._determine_mood(item), "emotional")

    def test_evening_adhkar_returns_emotional(self):
        """evening_adhkar category must map to 'emotional' mood."""
        item = {"category": "evening_adhkar", "type": "Evening Dhikr"}
        self.assertEqual(self.engine._determine_mood(item), "emotional")

    def test_happy_categories_return_happy(self):
        """All non-emotional, non-silent categories must map to 'happy' mood."""
        happy_cats = [
            "daily_duas", "morning_adhkar", "gratitude_patience",
            "remembrance_dhikr", "prophetic_hadith", "short_reminders",
            "ramadan", "friday_reminders", "eid_content", "general_education",
        ]
        for cat in happy_cats:
            item = {"category": cat, "type": "Content"}
            self.assertEqual(self.engine._determine_mood(item), "happy",
                             f"Category '{cat}' must map to 'happy' mood.")

    def test_unknown_category_defaults_to_happy(self):
        """Unknown or empty category defaults to 'happy' mood."""
        self.assertEqual(self.engine._determine_mood({"category": "", "type": ""}), "happy")
        self.assertEqual(self.engine._determine_mood({"category": "new_category", "type": ""}), "happy")


class TestMoodBasedTrackSelection(unittest.TestCase):
    """Tests for select_track_for_content() mood-based selection logic."""

    def test_happy_content_selects_happy_track(self):
        """Happy/normal categories must select the happy mood track."""
        engine, happy_path, emotional_path = _make_tracks_with_files()
        try:
            for cat in ["daily_duas", "morning_adhkar", "prophetic_hadith",
                        "short_reminders", "general_education", "friday_reminders"]:
                item = {"id": f"test_{cat}", "category": cat, "type": "Content"}
                track = engine.select_track_for_content(item)
                self.assertIsNotNone(track, f"Must select a track for '{cat}'.")
                self.assertEqual(track["mood"], "happy",
                                 f"Category '{cat}' must select the happy track.")
                self.assertEqual(track["id"], "personal_happy_01")
        finally:
            Path(happy_path).unlink(missing_ok=True)
            Path(emotional_path).unlink(missing_ok=True)

    def test_emotional_content_selects_emotional_track(self):
        """Sad/emotional categories must select the emotional mood track."""
        engine, happy_path, emotional_path = _make_tracks_with_files()
        try:
            for cat in ["forgiveness_repentance", "evening_adhkar"]:
                item = {"id": f"test_{cat}", "category": cat, "type": "Content"}
                track = engine.select_track_for_content(item)
                self.assertIsNotNone(track, f"Must select a track for '{cat}'.")
                self.assertEqual(track["mood"], "emotional",
                                 f"Category '{cat}' must select the emotional track.")
                self.assertEqual(track["id"], "personal_emotional_02")
        finally:
            Path(happy_path).unlink(missing_ok=True)
            Path(emotional_path).unlink(missing_ok=True)

    def test_quran_content_returns_none(self):
        """Quranic verse content must return None (no background audio)."""
        engine, happy_path, emotional_path = _make_tracks_with_files()
        try:
            item = {"id": "quran_1", "category": "quranic_verses", "type": "Qur'anic Verse"}
            track = engine.select_track_for_content(item, allow_quran=False)
            self.assertIsNone(track, "Quran recitation must never have background audio.")
        finally:
            Path(happy_path).unlink(missing_ok=True)
            Path(emotional_path).unlink(missing_ok=True)

    def test_quran_explicit_allow_returns_track(self):
        """When explicitly allowed, Quran content can receive a track."""
        engine, happy_path, emotional_path = _make_tracks_with_files()
        try:
            item = {"id": "quran_2", "category": "quranic_verses", "type": "Qur'anic Verse"}
            track = engine.select_track_for_content(item, allow_quran=True)
            self.assertIsNotNone(track, "When explicitly allowed, Quran content may receive audio.")
        finally:
            Path(happy_path).unlink(missing_ok=True)
            Path(emotional_path).unlink(missing_ok=True)

    def test_no_approved_tracks_returns_none(self):
        """When catalog has no approved tracks, selection returns None (silent)."""
        engine = _make_engine_with_tracks([
            {"id": "unapproved", "approval_status": "NEEDS_LICENSE_REVIEW", "topic_tags": ["daily_duas"]}
        ])
        item = {"id": "dua_1", "category": "daily_duas", "type": "Dua"}
        self.assertIsNone(engine.select_track_for_content(item))


class TestQuranProtection(unittest.TestCase):
    """Dedicated tests for Sacred Recitation Protection Policy."""

    def test_quranic_verses_category_always_silent(self):
        """quranic_verses category must always produce None from select_track_for_content."""
        engine, happy_path, emotional_path = _make_tracks_with_files()
        try:
            item = {"id": "ayah_255", "category": "quranic_verses", "type": "Qur'anic Verse"}
            self.assertIsNone(engine.select_track_for_content(item))
        finally:
            Path(happy_path).unlink(missing_ok=True)
            Path(emotional_path).unlink(missing_ok=True)

    def test_quran_type_string_produces_silent(self):
        """Content with 'Qur'an' in the type string is protected."""
        engine, happy_path, emotional_path = _make_tracks_with_files()
        try:
            item = {"id": "recitation_1", "category": "daily_duas", "type": "Qur'an Recitation"}
            self.assertIsNone(engine.select_track_for_content(item))
        finally:
            Path(happy_path).unlink(missing_ok=True)
            Path(emotional_path).unlink(missing_ok=True)

    def test_quran_prepare_audio_returns_none(self):
        """prepare_audio_for_video must return None for Quranic content."""
        engine, happy_path, emotional_path = _make_tracks_with_files()
        try:
            item = {"id": "verse_1", "category": "quranic_verses", "type": "Verse"}
            result = engine.prepare_audio_for_video(item, target_duration=15.0)
            self.assertIsNone(result)
        finally:
            Path(happy_path).unlink(missing_ok=True)
            Path(emotional_path).unlink(missing_ok=True)


class TestPrepareAudioForVideo(unittest.TestCase):
    """Tests for the full prepare_audio_for_video pipeline."""

    def test_happy_content_returns_happy_audio_info(self):
        """prepare_audio_for_video returns complete audio info with happy mood for normal content."""
        engine, happy_path, emotional_path = _make_tracks_with_files()
        try:
            item = {"id": "dua_morning", "category": "morning_adhkar", "type": "Dua"}
            result = engine.prepare_audio_for_video(item, target_duration=15.0)
            self.assertIsNotNone(result)
            self.assertEqual(result["track_id"], "personal_happy_01")
            self.assertEqual(result["mood"], "happy")
            self.assertIn("audio_path", result)
            self.assertGreater(result["volume"], 0)
        finally:
            Path(happy_path).unlink(missing_ok=True)
            Path(emotional_path).unlink(missing_ok=True)

    def test_emotional_content_returns_emotional_audio_info(self):
        """prepare_audio_for_video returns emotional track for forgiveness content."""
        engine, happy_path, emotional_path = _make_tracks_with_files()
        try:
            item = {"id": "istighfar_1", "category": "forgiveness_repentance", "type": "Dua"}
            result = engine.prepare_audio_for_video(item, target_duration=15.0)
            self.assertIsNotNone(result)
            self.assertEqual(result["track_id"], "personal_emotional_02")
            self.assertEqual(result["mood"], "emotional")
        finally:
            Path(happy_path).unlink(missing_ok=True)
            Path(emotional_path).unlink(missing_ok=True)

    def test_missing_audio_file_returns_none(self):
        """When approved track's local file does not exist, returns None (silent)."""
        tracks = [{
            "id": "missing_file_track",
            "title": "Missing",
            "local_path": "assets/audio/nasheeds/does_not_exist.mp3",
            "duration": 60.0,
            "mood": "happy",
            "topic_tags": ["daily_duas"],
            "approval_status": "APPROVED",
            "required_attribution": ""
        }]
        engine = _make_engine_with_tracks(tracks)
        item = {"id": "dua_1", "category": "daily_duas", "type": "Dua"}
        self.assertIsNone(engine.prepare_audio_for_video(item, target_duration=15.0))

    def test_spoken_lecture_volume_attenuation(self):
        """Spoken lectures get lower volume for speech clarity."""
        engine, happy_path, emotional_path = _make_tracks_with_files()
        try:
            item = {"id": "khutbah_1", "category": "general_education", "type": "Lecture"}
            result = engine.prepare_audio_for_video(item, target_duration=30.0, is_spoken_lecture=True)
            self.assertIsNotNone(result)
            self.assertLessEqual(result["volume"], 0.15,
                                 "Lecture volume must be attenuated for speech clarity.")
        finally:
            Path(happy_path).unlink(missing_ok=True)
            Path(emotional_path).unlink(missing_ok=True)

    def test_no_attribution_for_personal_tracks(self):
        """Personal owner tracks must not inject third-party attribution into captions."""
        engine, happy_path, emotional_path = _make_tracks_with_files()
        try:
            item = {"id": "hadith_1", "category": "prophetic_hadith", "type": "Hadith"}
            result = engine.prepare_audio_for_video(item, target_duration=15.0)
            self.assertIsNotNone(result)
            self.assertEqual(result["attribution"], "",
                             "Personal tracks must have empty attribution (no third-party credit).")
        finally:
            Path(happy_path).unlink(missing_ok=True)
            Path(emotional_path).unlink(missing_ok=True)


class TestHighlightTiming(unittest.TestCase):
    """Tests for highlight timestamp extraction."""

    def test_highlight_timing_within_duration(self):
        """Highlight slicing respects target video duration."""
        engine = NasheedEngine()
        track = {
            "duration": 120.0,
            "approved_highlights": [{"start": 20.0, "end": 60.0, "label": "Chorus"}]
        }
        start, end, label = engine.get_highlight_timing(track, target_duration=15.0)
        self.assertEqual(start, 20.0)
        self.assertEqual(end, 35.0)
        self.assertEqual(label, "Chorus")

    def test_fallback_timing_for_tracks_without_highlights(self):
        """Tracks without approved_highlights use default intro segment."""
        engine = NasheedEngine()
        track = {"duration": 60.0, "approved_highlights": []}
        start, end, label = engine.get_highlight_timing(track, target_duration=15.0)
        self.assertEqual(start, 10.0)
        self.assertEqual(end, 25.0)
        self.assertEqual(label, "Default Intro Segment")

    def test_short_track_starts_from_zero(self):
        """Short tracks that can't accommodate a 10s offset start from 0."""
        engine = NasheedEngine()
        track = {"duration": 15.0, "approved_highlights": []}
        start, end, label = engine.get_highlight_timing(track, target_duration=15.0)
        self.assertEqual(start, 0.0)
        self.assertEqual(end, 15.0)


class TestAllCategoryMoodCoverage(unittest.TestCase):
    """Verify every canonical category is mapped to a known mood."""

    def test_all_categories_produce_valid_mood(self):
        """Every canonical category must produce one of: silent, emotional, happy."""
        engine = NasheedEngine()
        all_categories = [
            "daily_duas", "morning_adhkar", "evening_adhkar",
            "gratitude_patience", "forgiveness_repentance",
            "remembrance_dhikr", "quranic_verses", "prophetic_hadith",
            "short_reminders", "ramadan", "friday_reminders",
            "eid_content", "general_education",
        ]
        for cat in all_categories:
            item = {"category": cat, "type": "Content"}
            mood = engine._determine_mood(item)
            self.assertIn(mood, ("silent", "emotional", "happy"),
                          f"Category '{cat}' produced unexpected mood '{mood}'.")

    def test_emotional_categories_constant_matches_engine(self):
        """EMOTIONAL_CATEGORIES constant must match what _determine_mood uses."""
        engine = NasheedEngine()
        for cat in EMOTIONAL_CATEGORIES:
            item = {"category": cat, "type": "Content"}
            self.assertEqual(engine._determine_mood(item), "emotional")

    def test_silent_categories_constant_matches_engine(self):
        """SILENT_CATEGORIES constant must match what _determine_mood uses."""
        engine = NasheedEngine()
        for cat in SILENT_CATEGORIES:
            item = {"category": cat, "type": "Content"}
            self.assertEqual(engine._determine_mood(item), "silent")


if __name__ == "__main__":
    unittest.main()

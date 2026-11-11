"""Regression tests for NoorPost mood audio, strict silence prevention and Qur'an routing."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from audio_manager import validate_audio_file
from nasheed_engine import NasheedEngine
from quran_audio import extract_ayah_reference, is_quranic_content


def make_tone(path: Path, seconds: float = 2.0, silent: bool = False) -> Path:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise unittest.SkipTest("ffmpeg is required for audio validation tests")
    source = "anullsrc=r=44100:cl=stereo" if silent else "sine=frequency=660:sample_rate=44100"
    subprocess.run(
        [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
         "-i", source, "-t", str(seconds), "-c:a", "libmp3lame", "-q:a", "3", str(path)],
        check=True, capture_output=True, timeout=30,
    )
    return path


class TestCatalogAndSelection(unittest.TestCase):
    def setUp(self):
        self.engine = NasheedEngine()

    def test_catalog_has_exactly_two_owner_approved_tracks(self):
        tracks = self.engine.get_tracks()
        self.assertEqual({t["id"] for t in tracks}, {"personal_happy_01", "personal_emotional_02"})
        self.assertTrue(all(t.get("creator") == "Owner" for t in tracks))
        self.assertTrue(all(t.get("external_use_permission") == "OWNER_APPROVED" for t in tracks))

    def test_happy_content_uses_happy_personal_track(self):
        item = {"id": "test-hadith", "category": "prophetic_hadith", "type": "Prophetic Teaching"}
        self.assertEqual(self.engine.select_track_for_content(item)["id"], "personal_happy_01")

    def test_emotional_content_uses_emotional_personal_track(self):
        item = {"id": "test-istighfar", "category": "forgiveness_repentance", "type": "Dua"}
        self.assertEqual(self.engine.select_track_for_content(item)["id"], "personal_emotional_02")

    def test_quran_is_never_selected_as_personal_background_audio(self):
        item = {"category": "quranic_verses", "type": "Qur'anic Verse", "source": "Qur'an 2:255"}
        self.assertIsNone(self.engine.select_track_for_content(item))

    def test_quranic_dua_inside_daily_duas_is_still_quran(self):
        item = {"category": "daily_duas", "type": "Qur'anic Dua", "source": "Qur'an 2:201"}
        self.assertTrue(is_quranic_content(item))
        self.assertEqual(extract_ayah_reference(item), (2, 201))

    def test_missing_quran_reference_fails_closed(self):
        with self.assertRaises(ValueError):
            extract_ayah_reference({"category": "quranic_verses", "type": "Qur'anic Verse"})


class TestAudioPreparation(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.audio_path = make_tone(Path(self.temp.name) / "audible.mp3")
        self.engine = NasheedEngine()

    def _track(self, mood="happy", path=None):
        return {
            "id": "fixture_track",
            "title": "Fixture owner track",
            "creator": "Owner",
            "local_path": str(path or self.audio_path),
            "duration": 2.0,
            "mood": mood,
            "topic_tags": [],
            "approval_status": "APPROVED",
            "external_use_permission": "OWNER_APPROVED",
            "approved_highlights": [{"start": 0.0, "end": 2.0, "label": "Complete"}],
        }

    def test_audio_validator_accepts_audible_mp3(self):
        result = validate_audio_file(self.audio_path)
        self.assertEqual(result["codec"], "mp3")
        self.assertGreater(result["duration"], 1.5)
        self.assertGreater(result["mean_volume_db"], -45)

    def test_audio_validator_rejects_silence(self):
        silent = make_tone(Path(self.temp.name) / "silence.mp3", silent=True)
        with self.assertRaises(RuntimeError):
            validate_audio_file(silent)

    def test_happy_audio_preparation_returns_validated_owner_track(self):
        self.engine.catalog = {"tracks": [self._track("happy")]}
        item = {"id": "dua-1", "category": "daily_duas", "type": "Dua"}
        result = self.engine.prepare_audio_for_video(item, 15.0)
        self.assertEqual(result["track_id"], "fixture_track")
        self.assertTrue(Path(result["audio_path"]).is_file())
        self.assertFalse(result["is_quran_recitation"])
        self.assertTrue(result["loop"])

    def test_emotional_selection_has_no_happy_track_fallback(self):
        self.engine.catalog = {"tracks": [self._track("happy")]}
        with self.assertRaises(RuntimeError):
            self.engine.prepare_audio_for_video(
                {"id": "dua-2", "category": "forgiveness_repentance", "type": "Dua"}, 15.0
            )

    def test_missing_track_cannot_be_silently_substituted(self):
        self.engine.catalog = {"tracks": [self._track("happy", Path(self.temp.name) / "missing.mp3")]}
        with self.assertRaises(RuntimeError):
            self.engine.prepare_audio_for_video(
                {"id": "dua-3", "category": "daily_duas", "type": "Dua"}, 15.0
            )

    def test_quran_uses_exact_recitation_and_no_background_track(self):
        expected = {
            "audio_path": str(self.audio_path), "duration": 2.0,
            "is_quran_recitation": True, "loop": False, "volume": 1.0,
        }
        with patch("nasheed_engine.prepare_quran_recitation", return_value=expected) as prepare:
            result = self.engine.prepare_audio_for_video(
                {"id": "verse", "category": "quranic_verses", "type": "Qur'anic Verse",
                 "source": "Qur'an 2:255"}, 15.0
            )
        prepare.assert_called_once()
        self.assertTrue(result["is_quran_recitation"])
        self.assertFalse(result["loop"])
        self.assertEqual(result["volume"], 1.0)


if __name__ == "__main__":
    unittest.main()

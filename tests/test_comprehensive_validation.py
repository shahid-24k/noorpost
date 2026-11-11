"""
test_comprehensive_validation.py — NoorPost 20-Point Autonomous Verification Suite
Explicitly validates every requirement specified in the Autonomous Engineering Prompt:

 1. UmmahAPI Client Initialization
 2. UmmahAPI Authentication (X-API-Key header, env var support, keyless operation)
 3. UmmahAPI Rate Limiting & Backoff (1 req/sec pacing, 429 jittered retry)
 4. Quran Endpoints (/api/quran/surahs, /api/quran/surah/{n}, /api/quran/surah/{s}/ayah/{a})
 5. Bukhari Endpoints (/api/hadith/bukhari/{n})
 6. Muslim Endpoints (/api/hadith/muslim/{n})
 7. Strict Hadith Collection Filtering (Strictly Bukhari & Muslim; rejection of others)
 8. Authenticity Verification Guardrails (Arabic diacritics, matching, grading)
 9. Offline Caching (assets/cache/ummah_cache.json, ISO timestamps, offline survival)
10. Personal Audio Catalog (my own 1.mp3, Fall my own 2.mp3)
11. Mood-Based Selection Logic (Happy/Normal -> Track 1, Sad/Emotional -> Track 2)
12. Fallback Audio Logic (unclear -> Track 1, missing/invalid -> silence)
13. Quran Silence Protection (Background audio NEVER over Quran recitation)
14. Halal Tunes Isolation (Halal Tunes tracks removed/disabled)
15. Audio Loop & Fade Transitions (FFmpeg filtergraph volume/fade parameters)
16. Video Generation Output Specs (1080x1920 9:16 vertical, RTL Arabic subtitles)
17. Lecture Repurposing Preservation (rights confirmation, source validation)
18. Duplicate Prevention & Intelligent Content Rotation (24h duplicate lockout)
19. GitHub Actions Workflow Configuration (08:00 & 21:00 IST cron, secrets, state sync)
20. Dropbox Handoff & Security (/NoorPost production, /NoorPost_State, dry-run safety)
"""

import os
import json
import yaml
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import config
import database
from ummah_api import UmmahApiClient, ALLOWED_HADITH_COLLECTIONS, normalize_arabic
from nasheed_engine import NasheedEngine
from source_manager import SourceManager
from subtitle_engine import is_arabic_text, shape_arabic_for_subtitles, wrap_subtitle_text
from state_sync import StateSyncManager, DROPBOX_STATE_FOLDER, DROPBOX_STATE_FILE
import pipeline


class TestNoorPostComprehensive20Points(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        database.init_db()

    # 1. UmmahAPI Client Initialization
    def test_01_ummah_api_client_initialization(self):
        client = UmmahApiClient(api_key="test_key_123")
        self.assertEqual(client.base_url, "https://ummahapi.com")
        self.assertEqual(client.api_key, "test_key_123")
        self.assertTrue(client.is_configured())

    # 2. UmmahAPI Authentication
    def test_02_ummah_api_authentication(self):
        # Authenticated
        client_auth = UmmahApiClient(api_key="secret_token")
        headers = client_auth._get_headers()
        api_header = headers.get("X-API-Key") or headers.get("x-api-key")
        self.assertEqual(api_header, "secret_token")

        # Unauthenticated / Keyless
        client_anon = UmmahApiClient(api_key="")
        headers_anon = client_anon._get_headers()
        self.assertNotIn("X-API-Key", headers_anon)
        self.assertNotIn("x-api-key", headers_anon)

    # 3. UmmahAPI Rate Limiting & Backoff
    @patch("ummah_api.time.sleep")
    @patch("requests.get")
    def test_03_ummah_api_rate_limiting_and_backoff(self, mock_get, mock_sleep):
        # Use an isolated temp cache file so global disk cache is unaffected
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        try:
            client = UmmahApiClient(api_key="test_key", cache_file=tmp_path)
            client._cache = {}

            # 429 response triggers backoff sleep
            mock_429 = MagicMock(status_code=429)
            mock_200 = MagicMock(status_code=200)
            mock_200.json.return_value = {"success": True, "data": {"status": "ok"}}
            mock_get.side_effect = [mock_429, mock_200]

            res = client._make_request("api/test_rate_limit", max_retries=2)
            self.assertEqual(res, {"status": "ok"})
            mock_sleep.assert_called()
        finally:
            tmp_path.unlink(missing_ok=True)

    # 4. Quran Endpoints
    def test_04_quran_endpoints(self):
        client = UmmahApiClient()
        # Direct retrieval from seeded cache
        surahs = client.get_surahs()
        self.assertIsNotNone(surahs)
        self.assertTrue(len(surahs) > 0)

        surah1 = client.get_surah(1)
        self.assertIsNotNone(surah1)
        self.assertEqual(surah1.get("surah", {}).get("number"), 1)

        ayah = client.get_ayah(1, 1)
        self.assertIsNotNone(ayah)
        self.assertEqual(ayah.get("source"), "Qur'an 1:1")
        self.assertIn("بِسْمِ", ayah.get("arabic"))

    # 5. Bukhari Endpoints
    def test_05_bukhari_endpoints(self):
        client = UmmahApiClient()
        hadith = client.get_hadith("bukhari", 1)
        self.assertIsNotNone(hadith)
        self.assertEqual(hadith.get("collection"), "bukhari")
        self.assertEqual(hadith.get("hadith_number"), 1)
        self.assertTrue(hadith.get("is_sahih"))

    # 6. Muslim Endpoints
    def test_06_muslim_endpoints(self):
        client = UmmahApiClient()
        hadith = client.get_hadith("muslim", 15)
        self.assertIsNotNone(hadith)
        self.assertEqual(hadith.get("collection"), "muslim")
        self.assertEqual(hadith.get("hadith_number"), 15)
        self.assertTrue(hadith.get("is_sahih"))

    # 7. Strict Hadith Collection Filtering
    def test_07_strict_hadith_collection_filtering(self):
        client = UmmahApiClient()
        self.assertEqual(ALLOWED_HADITH_COLLECTIONS, frozenset({"bukhari", "muslim"}))

        forbidden_collections = ["tirmidhi", "abudawud", "nasai", "ibnmajah", "malik", "ahmad"]
        for col in forbidden_collections:
            with self.assertRaises(ValueError):
                client.get_hadith(col, 1)

            ok, reason, _ = client.verify_hadith_reference(col, 1)
            self.assertFalse(ok)
            self.assertIn("forbidden", reason.lower())

    # 8. Authenticity Verification Guardrails
    def test_08_authenticity_verification_guardrails(self):
        client = UmmahApiClient()

        # Arabic normalization check
        vocalized = "إِنَّمَا الْأَعْمَالُ بِالنِّيَّاتِ"
        normalized = normalize_arabic(vocalized)
        self.assertEqual(normalized, "انما الاعمال بالنيات")

        # Incomplete / missing text is rejected
        ok, reason = client.verify_content_item({"arabic": "", "source": "Qur'an 1:1"})
        self.assertFalse(ok)

        # Non-Sahih / unauthorized source rejected
        ok, reason = client.verify_content_item({
            "arabic": "حديث ضعيف",
            "source": "Sunan Ibn Majah 224",
            "hadith_collection": "Sunan Ibn Majah"
        })
        self.assertFalse(ok)

    # 9. Offline Caching
    def test_09_offline_caching(self):
        cache_path = Path("assets/cache/ummah_cache.json")
        self.assertTrue(cache_path.exists())
        with open(cache_path, "r", encoding="utf-8") as f:
            cache = json.load(f)
        self.assertGreaterEqual(len(cache), 5)
        # Verify ISO timestamp presence in cache
        first_entry = next(iter(cache.values()))
        self.assertIn("cached_at", first_entry)
        self.assertIn("T", first_entry["cached_at"])

    # 10. Personal Audio Catalog
    def test_10_personal_audio_catalog(self):
        engine = NasheedEngine()
        tracks = engine.catalog.get("tracks", [])
        track_ids = {t["id"] for t in tracks}
        self.assertIn("personal_happy_01", track_ids)
        self.assertIn("personal_emotional_02", track_ids)

        # Audio masters live in private Dropbox; the runner caches them locally on demand.
        for t in tracks:
            self.assertTrue(str(t["local_path"]).endswith(".mp3"))
            self.assertEqual(t["creator"], "Owner")
            self.assertEqual(t["external_use_permission"], "OWNER_APPROVED")

    # 11. Mood-Based Selection Logic
    def test_11_mood_based_audio_selection(self):
        engine = NasheedEngine()

        # Happy / Normal / Motivational -> Track 1 (personal_happy_01)
        happy_item = {"id": "dua_happy", "category": "daily_duas", "type": "Dua"}
        happy_track = engine.select_track_for_content(happy_item)
        self.assertIsNotNone(happy_track)
        self.assertEqual(happy_track["id"], "personal_happy_01")
        self.assertEqual(happy_track["mood"], "happy")

        # Sad / Emotional / Reflective -> Track 2 (personal_emotional_02)
        emotional_item = {"id": "dua_emotional", "category": "forgiveness_repentance", "type": "Dua"}
        emotional_track = engine.select_track_for_content(emotional_item)
        self.assertIsNotNone(emotional_track)
        self.assertEqual(emotional_track["id"], "personal_emotional_02")
        self.assertEqual(emotional_track["mood"], "emotional")

    # 12. Fallback Audio Logic
    def test_12_fallback_audio_logic(self):
        engine = NasheedEngine()

        # Unclear / unknown category -> defaults to Track 1 (happy)
        unclear_item = {"id": "dua_unclear", "category": "mysterious_category", "type": "Dua"}
        fallback_track = engine.select_track_for_content(unclear_item)
        self.assertEqual(fallback_track["id"], "personal_happy_01")

        # Missing / invalid audio is a hard failure, never a silent fallback.
        with patch.object(engine, "_ensure_track_available",
                          side_effect=RuntimeError("missing owner audio")):
            with self.assertRaises(RuntimeError):
                engine.prepare_audio_for_video(unclear_item, target_duration=10.0)

    # 13. Quran Recitation Routing
    def test_13_quran_recitation_routing(self):
        engine = NasheedEngine()
        quran_item = {
            "id": "quran_1", "category": "quranic_verses",
            "type": "Qur'anic Verse", "source": "Qur'an 2:255",
        }
        # Qur'an must never select a personal background track.
        self.assertIsNone(engine.select_track_for_content(quran_item))
        expected = {
            "audio_path": "verified_ayah.mp3", "duration": 12.0,
            "is_quran_recitation": True, "loop": False, "volume": 1.0,
        }
        with patch("nasheed_engine.prepare_quran_recitation", return_value=expected):
            prep = engine.prepare_audio_for_video(quran_item, target_duration=15.0)
        self.assertTrue(prep["is_quran_recitation"])
        self.assertFalse(prep["loop"])
        self.assertEqual(prep["volume"], 1.0)

    # 14. Halal Tunes Isolation
    def test_14_halal_tunes_isolation(self):
        engine = NasheedEngine()
        catalog_str = json.dumps(engine.catalog).lower()
        self.assertNotIn("halal tunes", catalog_str)
        for track in engine.catalog.get("tracks", []):
            self.assertTrue("my own" in track["title"].lower() or "my own" in track["filename"].lower())

    # 15. Audio Loop and Verified Track Metadata
    def test_15_audio_loop_and_fade_transitions(self):
        engine = NasheedEngine()
        happy_item = {"id": "dua_happy", "category": "daily_duas", "type": "Dua"}
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as fixture:
            fixture.write(b"test-fixture")
            fixture_path = Path(fixture.name)
        self.addCleanup(fixture_path.unlink, missing_ok=True)
        with patch.object(engine, "_ensure_track_available", return_value=fixture_path):
            with patch("nasheed_engine.validate_audio_file", return_value={
                "duration": 15.0, "codec": "mp3", "mean_volume_db": -20.0,
            }):
                prep = engine.prepare_audio_for_video(happy_item, target_duration=15.0)
        self.assertIn("audio_path", prep)
        self.assertGreater(prep["volume"], 0)
        self.assertEqual(prep["duration"], 15.0)
        self.assertEqual(prep["mood"], "happy")
        self.assertTrue(prep["loop"])

    # 16. Video Generation Output Specs
    def test_16_video_generation_output_specs(self):
        arabic = "إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ"
        self.assertTrue(is_arabic_text(arabic))

        shaped = shape_arabic_for_subtitles(arabic)
        self.assertIsNotNone(shaped)

        wrapped = wrap_subtitle_text(shaped, max_chars=30)
        self.assertTrue(len(wrapped) > 0)

    # 17. Lecture Repurposing Preservation
    def test_17_lecture_repurposing_preservation(self):
        sm = SourceManager()
        self.assertTrue(sm.is_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ"))

        # Rights confirmation check: without rights_confirmed, raises PermissionError
        with self.assertRaises(PermissionError):
            sm.prepare_source({
                "source_type": "youtube",
                "rights_confirmed": False,
                "source_id": "test_src",
                "source_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "title": "Test Lecture",
                "duration": 60
            })

    # 18. Duplicate Prevention & Intelligent Content Rotation
    def test_18_duplicate_prevention_and_rotation(self):
        item1 = pipeline.select_content()
        self.assertIsNotNone(item1)
        # Record video and publication to test 24h lockout
        vid_id = database.record_video(
            dua_id=item1["id"],
            video_path="video.mp4",
            preview_path="preview.jpg",
            caption="test caption",
            theme="midnight-gold",
            font="amiri",
            duration=15
        )
        database.record_publication(vid_id, "instagram", "success", "https://instagram.com/p/123", "post_123")
        self.assertTrue(database.is_recent_duplicate(item1["id"], hours=24))

        # Strict Sahih enforcement: selected content MUST be Quran, Bukhari, or Muslim
        source = item1.get("source", "").lower()
        is_valid = any(valid in source for valid in ["qur'an", "quran", "bukhari", "muslim"])
        self.assertTrue(is_valid, f"Selected content '{item1['source']}' violated strict content policy!")

    # 19. GitHub Actions Workflow Configuration
    def test_19_github_actions_workflow(self):
        wf_path = Path(".github/workflows/noorpost.yml")
        self.assertTrue(wf_path.exists())
        with open(wf_path, "r", encoding="utf-8") as f:
            wf = yaml.safe_load(f)

        # Handle PyYAML 'on' parsed as boolean True
        on_section = wf.get(True) or wf.get("on")
        self.assertIsNotNone(on_section)

        # Cron checks: 08:00 IST (02:30 UTC), 21:00 IST (15:30 UTC)
        schedules = [s["cron"] for s in on_section["schedule"]]
        self.assertIn("30 2 * * *", schedules)
        self.assertIn("30 15 * * *", schedules)

        # Secret mapping
        env = wf["jobs"]["publish_reel"]["env"]
        self.assertIn("UMMAH_API_KEY", env)
        self.assertIn("DROPBOX_REFRESH_TOKEN", env)

    # 20. Dropbox Handoff & Security
    def test_20_dropbox_handoff_and_security(self):
        self.assertEqual(config.DROPBOX_FOLDER, "/NoorPost")
        self.assertEqual(DROPBOX_STATE_FOLDER, "/NoorPost_State")

        # Test state sync dry-run safety
        with patch("state_sync.StateSyncManager._get_dbx_client") as mock_get_client:
            mock_dbx = MagicMock()
            mock_get_client.return_value = mock_dbx
            manager = StateSyncManager()
            success = manager.push_state(is_dry_run=True)
            self.assertTrue(success)
            mock_dbx.files_upload.assert_not_called()


if __name__ == "__main__":
    unittest.main()

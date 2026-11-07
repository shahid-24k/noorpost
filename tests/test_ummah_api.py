"""
test_ummah_api.py — Unit and Integration Tests for UmmahAPI Client & Strict Authenticity Rules
NoorPost Ultimate

Covers:
1. Client initialization and secure key handling (read from UMMAH_API_KEY, never exposed).
2. Strict collection restriction: ONLY Bukhari and Muslim permitted. All others rejected.
3. Quran endpoints: Surah and exact Ayah retrieval, verified Arabic and Sahih International translation.
4. Hadith endpoints: Bukhari and Muslim narrations, Sahih authenticity verification.
5. Strict verification guardrails: rejection of non-existent, mismatching, or uncertain references.
6. Arabic diacritic-insensitive normalization and text verification.
7. Caching and rate-limit throttling (1.0 req/sec pacing, 429 retry backoff).
8. Formatting helpers producing compliant NoorPost content records.
"""

import unittest
from unittest.mock import patch, MagicMock
from ummah_api import (
    UmmahApiClient,
    ALLOWED_HADITH_COLLECTIONS,
    normalize_arabic,
)


class TestUmmahApiClientInit(unittest.TestCase):
    """Test client initialization, headers, and security."""

    def test_client_init_with_key(self):
        """Client properly attaches X-API-Key when configured."""
        client = UmmahApiClient(api_key="test_secret_key_abc")
        self.assertTrue(client.is_configured())
        headers = client._get_headers()
        api_key_header = headers.get("X-API-Key") or headers.get("x-api-key")
        self.assertEqual(api_key_header, "test_secret_key_abc")
        self.assertIn("NoorPost-Ultimate", headers.get("User-Agent"))

    def test_client_without_key_runs_gracefully(self):
        """Client supports keyless operation without raising or sending empty header."""
        client = UmmahApiClient(api_key="")
        self.assertFalse(client.is_configured())
        headers = client._get_headers()
        self.assertNotIn("X-API-Key", headers)
        self.assertNotIn("x-api-key", headers)

    def test_client_reads_from_env(self):
        """Client automatically reads UMMAH_API_KEY from environment."""
        with patch.dict("os.environ", {"UMMAH_API_KEY": "env_provided_key"}):
            client = UmmahApiClient()
            self.assertEqual(client.api_key, "env_provided_key")


class TestStrictCollectionRestriction(unittest.TestCase):
    """STRICT RULE: Only Sahih al-Bukhari and Sahih Muslim are permitted."""

    def setUp(self):
        self.client = UmmahApiClient(api_key="mock_key")
        self.client._cache = {}

    def test_allowed_collections_set(self):
        """Allowed collections must contain strictly bukhari and muslim and nothing else."""
        self.assertEqual(ALLOWED_HADITH_COLLECTIONS, frozenset({"bukhari", "muslim"}))

    def test_bukhari_is_permitted(self):
        """Bukhari collection request does not raise ValueError."""
        with patch.object(self.client, "_make_request", return_value={"arabic": "حديث", "english": "Hadith", "hadithnumber": 1}):
            result = self.client.get_hadith("bukhari", 1)
            self.assertIsNotNone(result)
            self.assertEqual(result["collection"], "bukhari")

    def test_muslim_is_permitted(self):
        """Muslim collection request does not raise ValueError."""
        with patch.object(self.client, "_make_request", return_value={"arabic": "حديث", "english": "Hadith", "hadithnumber": 3}):
            result = self.client.get_hadith("muslim", 3)
            self.assertIsNotNone(result)
            self.assertEqual(result["collection"], "muslim")

    def test_forbidden_collections_raise_value_error(self):
        """Any collection other than bukhari/muslim must raise ValueError."""
        forbidden = ["abudawud", "tirmidhi", "nasai", "ibnmajah", "malik", "ahmad", "darimi", "qudsi"]
        for col in forbidden:
            with self.assertRaises(ValueError):
                self.client.get_hadith(col, 1)

    def test_verify_hadith_rejects_forbidden_collections(self):
        """verify_hadith_reference returns (False, ...) for unpermitted collections without raising."""
        ok, reason, record = self.client.verify_hadith_reference("tirmidhi", 2500)
        self.assertFalse(ok)
        self.assertIn("Forbidden", reason)
        self.assertIsNone(record)


class TestArabicNormalization(unittest.TestCase):
    """Test tashkeel stripping and orthographic normalization."""

    def test_strip_diacritics(self):
        """Strips fatha, damma, kasra, sukun, shadda, tanween."""
        vocalized = "إِنَّمَا الْأَعْمَالُ بِالنِّيَّاتِ"
        unvocalized = normalize_arabic(vocalized)
        self.assertEqual(unvocalized, "انما الاعمال بالنيات")

    def test_empty_string_safe(self):
        """Empty input safely returns empty string."""
        self.assertEqual(normalize_arabic(""), "")
        self.assertEqual(normalize_arabic(None), "")


class TestQuranEndpoints(unittest.TestCase):
    """Test Quran Surah and Ayah retrieval and verification."""

    def setUp(self):
        self.client = UmmahApiClient(api_key="mock_key")
        self.client._cache = {}

    def test_invalid_surah_number_rejected(self):
        """Surah numbers < 1 or > 114 return None."""
        self.assertIsNone(self.client.get_surah(0))
        self.assertIsNone(self.client.get_surah(115))
        self.assertIsNone(self.client.get_ayah(115, 1))

    @patch.object(UmmahApiClient, "_make_request")
    def test_get_ayah_direct_success(self, mock_req):
        """Direct Ayah endpoint parses verified Arabic and Sahih International translation."""
        mock_req.return_value = {
            "surah": {"number": 1, "name_arabic": "الفاتحة", "name_english": "Al-Fatihah"},
            "verse": {
                "verse_key": "1:1",
                "ayah": 1,
                "arabic": "بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ",
                "transliteration": "Bismi Allahi arrahmani arraheem",
                "translations": {
                    "sahih_international": "In the name of Allah, the Entirely Merciful, the Especially Merciful."
                }
            }
        }
        res = self.client.get_ayah(1, 1)
        self.assertIsNotNone(res)
        self.assertEqual(res["verse_key"], "1:1")
        self.assertEqual(res["arabic"], "بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ")
        self.assertIn("In the name of Allah", res["translation"])
        self.assertEqual(res["source"], "Qur'an 1:1")

    @patch.object(UmmahApiClient, "get_ayah")
    def test_verify_quran_reference_success(self, mock_get_ayah):
        """Verified Quran reference matches authentic text."""
        mock_get_ayah.return_value = {
            "surah_number": 112,
            "ayah_number": 1,
            "arabic": "قُلْ هُوَ اللَّهُ أَحَدٌ",
            "translation": "Say, He is Allah, [who is] One.",
            "source": "Qur'an 112:1",
            "source_url": "https://quran.com/112/1",
        }
        ok, reason, record = self.client.verify_quran_reference(
            112, 1, candidate_arabic="قل هو الله احد"
        )
        self.assertTrue(ok)
        self.assertIn("Verified", reason)
        self.assertIsNotNone(record)

    @patch.object(UmmahApiClient, "get_ayah")
    def test_verify_quran_reference_text_mismatch(self, mock_get_ayah):
        """Mismatched candidate Arabic text is strictly rejected."""
        mock_get_ayah.return_value = {
            "surah_number": 112,
            "ayah_number": 1,
            "arabic": "قُلْ هُوَ اللَّهُ أَحَدٌ",
            "translation": "Say, He is Allah, [who is] One.",
            "source": "Qur'an 112:1",
            "source_url": "https://quran.com/112/1",
        }
        # Candidate text is from a completely different verse
        ok, reason, record = self.client.verify_quran_reference(
            112, 1, candidate_arabic="الحمد لله رب العالمين"
        )
        self.assertFalse(ok)
        self.assertIn("mismatch", reason.lower())
        self.assertIsNone(record)

    @patch.object(UmmahApiClient, "verify_quran_reference")
    def test_format_quran_record(self, mock_verify):
        """format_quran_record outputs complete NoorPost record."""
        mock_verify.return_value = (True, "Verified", {
            "surah_number": 1,
            "surah_name_english": "Al-Fatihah",
            "ayah_number": 1,
            "arabic": "بِسْمِ اللَّهِ",
            "transliteration": "Bismillah",
            "translation": "In the name of Allah",
            "source": "Qur'an 1:1",
            "source_url": "https://quran.com/1/1",
        })
        record = self.client.format_quran_record(1, 1)
        self.assertIsNotNone(record)
        self.assertEqual(record["category"], "quranic_verses")
        self.assertEqual(record["type"], "Qur'anic Verse")
        self.assertEqual(record["grading"], "Mutawatir (Divine Revelation)")
        self.assertEqual(record["is_verified"], 1)


class TestHadithEndpoints(unittest.TestCase):
    """Test Bukhari and Muslim hadith retrieval and authenticity verification."""

    def setUp(self):
        self.client = UmmahApiClient(api_key="mock_key")
        self.client._cache = {}

    @patch.object(UmmahApiClient, "_make_request")
    def test_get_bukhari_hadith(self, mock_req):
        """Bukhari narration retrieval."""
        mock_req.return_value = {
            "collection": "bukhari",
            "hadithnumber": 1,
            "arabic": "إِنَّمَا الْأَعْمَالُ بِالنِّيَّاتِ",
            "english": "Actions are according to intentions.",
            "grade": "Sahih"
        }
        res = self.client.get_hadith("bukhari", 1)
        self.assertIsNotNone(res)
        self.assertEqual(res["collection_name"], "Sahih al-Bukhari")
        self.assertEqual(res["source"], "Sahih al-Bukhari 1")
        self.assertTrue(res["is_sahih"])

    @patch.object(UmmahApiClient, "_make_request")
    def test_get_muslim_hadith(self, mock_req):
        """Muslim narration retrieval."""
        mock_req.return_value = {
            "collection": "muslim",
            "hadithnumber": 3,
            "arabic": "حديث مسلم",
            "english": "Sahih Muslim narration.",
            "grade": "Sahih"
        }
        res = self.client.get_hadith("muslim", 3)
        self.assertIsNotNone(res)
        self.assertEqual(res["collection_name"], "Sahih Muslim")
        self.assertEqual(res["source"], "Sahih Muslim 3")
        self.assertTrue(res["is_sahih"])

    @patch.object(UmmahApiClient, "get_hadith")
    def test_verify_hadith_reference_success(self, mock_get):
        """Sahih Hadith verification success with Arabic match."""
        mock_get.return_value = {
            "collection": "bukhari",
            "collection_name": "Sahih al-Bukhari",
            "hadith_number": 1,
            "arabic": "إِنَّمَا الْأَعْمَالُ بِالنِّيَّاتِ",
            "translation": "Actions are according to intentions.",
            "grade": "Sahih",
            "is_sahih": True,
            "source": "Sahih al-Bukhari 1",
            "source_url": "https://sunnah.com/bukhari:1",
        }
        ok, reason, record = self.client.verify_hadith_reference(
            "bukhari", 1, candidate_arabic="انما الاعمال بالنيات"
        )
        self.assertTrue(ok)
        self.assertIn("Verified", reason)
        self.assertIsNotNone(record)

    @patch.object(UmmahApiClient, "get_hadith")
    def test_verify_hadith_rejects_weak_narration(self, mock_get):
        """Any narration marked weak or fabricated is strictly rejected."""
        mock_get.return_value = {
            "collection": "bukhari",
            "hadith_number": 9999,
            "arabic": "حديث",
            "translation": "A narration",
            "grade": "Da'if (Weak)",
            "source": "Sahih al-Bukhari 9999",
        }
        ok, reason, record = self.client.verify_hadith_reference("bukhari", 9999)
        self.assertFalse(ok)
        self.assertIn("non-Sahih", reason)
        self.assertIsNone(record)

    @patch.object(UmmahApiClient, "get_hadith")
    def test_verify_hadith_text_mismatch(self, mock_get):
        """Mismatched Hadith Arabic text is strictly rejected."""
        mock_get.return_value = {
            "collection": "bukhari",
            "collection_name": "Sahih al-Bukhari",
            "hadith_number": 1,
            "arabic": "إِنَّمَا الْأَعْمَالُ بِالنِّيَّاتِ",
            "translation": "Actions are according to intentions.",
            "grade": "Sahih",
            "source": "Sahih al-Bukhari 1",
        }
        ok, reason, record = self.client.verify_hadith_reference(
            "bukhari", 1, candidate_arabic="كلمتان خفيفتان على اللسان ثقيلتان في الميزان"
        )
        self.assertFalse(ok)
        self.assertIn("does not match", reason)
        self.assertIsNone(record)

    @patch.object(UmmahApiClient, "verify_hadith_reference")
    def test_format_hadith_record(self, mock_verify):
        """format_hadith_record outputs complete NoorPost record."""
        mock_verify.return_value = (True, "Verified", {
            "collection_name": "Sahih al-Bukhari",
            "hadith_number": 1,
            "arabic": "إِنَّمَا الْأَعْمَالُ بِالنِّيَّاتِ",
            "translation": "Actions are according to intentions.",
            "source": "Sahih al-Bukhari 1",
            "source_url": "https://sunnah.com/bukhari:1",
            "grading": "Sahih",
        })
        record = self.client.format_hadith_record("bukhari", 1)
        self.assertIsNotNone(record)
        self.assertEqual(record["category"], "prophetic_hadith")
        self.assertEqual(record["type"], "Prophetic Teaching")
        self.assertEqual(record["grading"], "Sahih")
        self.assertEqual(record["is_verified"], 1)


class TestCachingAndPacing(unittest.TestCase):
    """Test disk caching and rate-limiting pacing."""

    @patch("requests.get")
    def test_caching_prevents_duplicate_network_calls(self, mock_get):
        """Cached response is returned without making a second network call."""
        client = UmmahApiClient(api_key="mock_key")
        client._cache = {}

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "success": True,
            "data": {"arabic": "الحمد لله", "translations": {"sahih_international": "Praise be to Allah"}}
        }
        mock_get.return_value = mock_resp

        # First request hits network
        data1 = client._make_request("api/test")
        self.assertEqual(mock_get.call_count, 1)

        # Second request hits cache
        data2 = client._make_request("api/test")
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(data1, data2)

    @patch("ummah_api.time.sleep")
    @patch("requests.get")
    def test_rate_limit_throttle_pacing(self, mock_get, mock_sleep):
        """Consecutive requests under 1.0s apart trigger rate limit pacing."""
        client = UmmahApiClient(api_key="mock_key")
        client._cache = {}

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"success": True, "data": {}}
        mock_get.return_value = mock_resp

        import time
        client._last_request_time = time.time()  # Recent call
        client._make_request("api/another")
        mock_sleep.assert_called()


class TestNewUmmahApiEndpoints(unittest.TestCase):
    """Test newly added official endpoints: surahs, collections, pagination."""

    def setUp(self):
        self.client = UmmahApiClient(api_key="mock_key")
        self.client._cache = {}

    def test_get_surahs(self):
        """get_surahs calls /api/quran/surahs and returns list."""
        with patch.object(self.client, "_make_request", return_value=[{"number": 1, "name_english": "Al-Fatihah"}]):
            surahs = self.client.get_surahs()
            self.assertIsInstance(surahs, list)
            self.assertEqual(len(surahs), 1)
            self.assertEqual(surahs[0]["name_english"], "Al-Fatihah")

    def test_get_hadith_collections(self):
        """get_hadith_collections returns collections list."""
        with patch.object(self.client, "_make_request", return_value=[{"name": "bukhari"}, {"name": "muslim"}]):
            cols = self.client.get_hadith_collections()
            self.assertIsInstance(cols, list)
            self.assertEqual(len(cols), 2)

    def test_get_hadiths_by_collection_valid(self):
        """get_hadiths_by_collection with bukhari succeeds."""
        with patch.object(self.client, "_make_request", return_value={"hadiths": [{"hadithnumber": 1}]}):
            res = self.client.get_hadiths_by_collection("bukhari", page=1, limit=5)
            self.assertIsNotNone(res)
            self.assertIn("hadiths", res)

    def test_get_hadiths_by_collection_forbidden(self):
        """get_hadiths_by_collection with unapproved collection raises ValueError."""
        with self.assertRaises(ValueError):
            self.client.get_hadiths_by_collection("tirmidhi", page=1, limit=5)

    def test_verify_content_item_strict_guardrails(self):
        """verify_content_item accepts Bukhari and Muslim, rejects other collections."""
        # Valid Quran
        quran_item = {
            "category": "quranic_verses",
            "source": "Qur'an 1:1",
            "surah_name": "Al-Fatihah",
            "verse_number": "1",
            "arabic": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"
        }
        ok, _ = self.client.verify_content_item(quran_item)
        self.assertTrue(ok)

        # Valid Bukhari
        bukhari_item = {
            "category": "prophetic_hadith",
            "source": "Sahih al-Bukhari 1",
            "hadith_collection": "Sahih al-Bukhari",
            "hadith_number": "1",
            "arabic": "إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ"
        }
        ok, _ = self.client.verify_content_item(bukhari_item)
        self.assertTrue(ok)

        # Valid Muslim
        muslim_item = {
            "category": "prophetic_hadith",
            "source": "Sahih Muslim 15",
            "hadith_collection": "Sahih Muslim",
            "hadith_number": "15",
            "arabic": "بُنِيَ الإِسْلاَمُ عَلَى خَمْسٍ"
        }
        ok, _ = self.client.verify_content_item(muslim_item)
        self.assertTrue(ok)

        # Forbidden Abu Dawud
        abu_dawud_item = {
            "category": "prophetic_hadith",
            "source": "Sunan Abu Dawud 1522",
            "hadith_collection": "Sunan Abu Dawud",
            "hadith_number": "1522",
            "arabic": "اللهم إني أسألك"
        }
        ok, reason = self.client.verify_content_item(abu_dawud_item)
        self.assertFalse(ok)
        self.assertIn("forbidden", reason.lower())


if __name__ == "__main__":
    unittest.main()


"""
test_sunnah_api.py — Unit and Integration Tests for Official Sunnah.com API Client & Sahih Verification
"""

import unittest
from unittest.mock import patch, MagicMock
from sunnah_api import SunnahApiClient, CANONICAL_SAHIH_COLLECTIONS


class TestSunnahApiClient(unittest.TestCase):
    """Test Sunnah.com API client behavior, authentication, and error handling."""

    def test_client_init_and_headers_with_key(self):
        """Verify client attaches x-api-key when configured."""
        client = SunnahApiClient(api_key="test_secret_key_123")
        self.assertTrue(client.is_configured())
        headers = client._get_headers()
        self.assertEqual(headers.get("x-api-key"), "test_secret_key_123")
        self.assertIn("NoorPost-Ultimate", headers.get("User-Agent"))

    def test_client_without_key(self):
        """Verify client behaves safely when key is unconfigured."""
        client = SunnahApiClient(api_key="")
        self.assertFalse(client.is_configured())
        self.assertNotIn("x-api-key", client._get_headers())
        # Network request returns None safely without raising
        self.assertEqual(client.get_collections(), [])
        self.assertIsNone(client.get_hadith('bukhari', 1))

    @patch("requests.get")
    def test_rate_limit_backoff_and_retry(self, mock_get):
        """Verify rate limits (429) trigger backoff and retry."""
        mock_resp_429 = MagicMock()
        mock_resp_429.status_code = 429

        mock_resp_200 = MagicMock()
        mock_resp_200.status_code = 200
        mock_resp_200.json.return_value = {"data": [{"name": "bukhari"}]}

        mock_get.side_effect = [mock_resp_429, mock_resp_200]

        client = SunnahApiClient(api_key="valid_key")
        client._cache = {}
        with patch("sunnah_api.time.sleep") as mock_sleep:
            cols = client.get_collections()
            self.assertEqual(len(cols), 1)
            self.assertEqual(cols[0]["name"], "bukhari")
            mock_sleep.assert_called_once()

    @patch("requests.get")
    def test_auth_failure_returns_none(self, mock_get):
        """Verify 401/403 errors return None safely without raising exceptions."""
        mock_resp_401 = MagicMock()
        mock_resp_401.status_code = 401
        mock_get.return_value = mock_resp_401

        client = SunnahApiClient(api_key="invalid_key")
        result = client.get_hadith("bukhari", 1)
        self.assertIsNone(result)


class TestSahihVerificationPolicy(unittest.TestCase):
    """Test strict Sahih-Only verification rules for automatic publishing."""

    def test_bukhari_consensus_sahih(self):
        """Bukhari narrations qualify by canonical consensus even if grades array is empty."""
        hadith = {
            "collection": "bukhari",
            "hadithNumber": "1",
            "grades": []
        }
        is_sahih, reason, authority = SunnahApiClient.verify_hadith_authenticity(hadith)
        self.assertTrue(is_sahih)
        self.assertIn("Consensus", reason)

    def test_muslim_consensus_sahih(self):
        """Muslim narrations qualify by canonical consensus."""
        hadith = {
            "collection": "muslim",
            "hadithNumber": "2699",
            "grades": []
        }
        is_sahih, reason, authority = SunnahApiClient.verify_hadith_authenticity(hadith)
        self.assertTrue(is_sahih)
        self.assertIn("Muslim", reason)

    def test_non_canonical_with_explicit_sahih_grade(self):
        """Abu Dawud narration with explicit Sahih (Al-Albani) qualifies."""
        hadith = {
            "collection": "abudawud",
            "hadithNumber": "1500",
            "grades": [
                {"scholar": "Al-Albani", "grade": "Sahih"}
            ]
        }
        is_sahih, reason, authority = SunnahApiClient.verify_hadith_authenticity(hadith)
        self.assertTrue(is_sahih)
        self.assertEqual(authority, "Al-Albani")
        self.assertIn("Sahih", reason)

    def test_non_canonical_rejects_hasan(self):
        """Tirmidhi narration graded Hasan must be REJECTED for automatic publishing."""
        hadith = {
            "collection": "tirmidhi",
            "hadithNumber": "2500",
            "grades": [
                {"scholar": "Al-Albani", "grade": "Hasan"}
            ]
        }
        is_sahih, reason, authority = SunnahApiClient.verify_hadith_authenticity(hadith)
        self.assertFalse(is_sahih)

    def test_non_canonical_rejects_daif(self):
        """Ibn Majah narration graded Da'if must be REJECTED."""
        hadith = {
            "collection": "ibnmajah",
            "hadithNumber": "3000",
            "grades": [
                {"scholar": "Darussalam", "grade": "Da'if"}
            ]
        }
        is_sahih, reason, authority = SunnahApiClient.verify_hadith_authenticity(hadith)
        self.assertFalse(is_sahih)

    def test_non_canonical_rejects_missing_grade(self):
        """Non-canonical narration with missing/empty grades must be REJECTED."""
        hadith = {
            "collection": "nasai",
            "hadithNumber": "450",
            "grades": []
        }
        is_sahih, reason, authority = SunnahApiClient.verify_hadith_authenticity(hadith)
        self.assertFalse(is_sahih)
        self.assertIn("requires explicit Sahih grade", reason)

    def test_format_hadith_record_preserves_text_and_source(self):
        """Verify format_hadith_record maps Arabic, English, and attribution correctly."""
        client = SunnahApiClient(api_key="test_key")
        raw = {
            "collection": "bukhari",
            "hadithNumber": "1",
            "hadith": [
                {"lang": "ar", "body": "إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ"},
                {"lang": "en", "body": "Narrated 'Umar bin Al-Khattab: Actions are according to intentions."}
            ],
            "grades": []
        }
        record = client.format_hadith_record(raw)
        self.assertIsNotNone(record)
        self.assertEqual(record["arabic"], "إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ")
        self.assertIn("Actions are according to intentions", record["translation"])
        self.assertEqual(record["narrator"], "'Umar bin Al-Khattab")
        self.assertEqual(record["source"], "Sahih al-Bukhari 1")
        self.assertEqual(record["source_url"], "https://sunnah.com/bukhari:1")
        self.assertEqual(record["verification_status"], "verified_sahih")


if __name__ == "__main__":
    unittest.main()

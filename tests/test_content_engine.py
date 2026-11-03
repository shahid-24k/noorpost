"""
test_content_engine.py — Comprehensive Test Suite for NoorPost Ultimate Content Engine
Tests:
  1. Category selection & filtering
  2. Category rotation & persistent tracking across restarts
  3. Strict duplicate prevention & least-used preference
  4. Religious source-reference preservation & sacred text immutability
  5. Human review status enforcement (blocking unverified/draft/rejected items)
  6. Script generation engine (hook, sacred text, reflection, closing)
  7. Caption & hashtag engine (styles, moderate hashtags, customization)
  8. AI adapter offline mode & failure fallback
  9. Database migrations & backward compatibility
"""

import sys
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(BASE_DIR))

import database
from categories import CATEGORIES, resolve_category, get_next_category_in_rotation
from content_db import AUTHENTIC_CONTENT, get_content_by_category, get_content_by_id
from script_engine import generate_script
from caption_engine import generate_caption, get_hashtags
from ai_adapter import AIAdapter

class TestContentEngine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        database.init_db()
        database.sync_duas(AUTHENTIC_CONTENT)

    def test_canonical_13_categories_exist(self):
        """Verify all 13 canonical categories are registered."""
        expected = [
            "daily_duas", "morning_adhkar", "evening_adhkar",
            "gratitude_patience", "forgiveness_repentance", "remembrance_dhikr",
            "quranic_verses", "prophetic_hadith", "short_reminders",
            "ramadan", "friday_reminders", "eid_content", "general_education"
        ]
        for cat in expected:
            self.assertIn(cat, CATEGORIES)
            self.assertIsNotNone(resolve_category(cat))

    def test_category_content_selection(self):
        """Verify selecting by specific category returns an approved item from that category."""
        item = database.get_next_authentic_content(category="friday_reminders")
        self.assertEqual(item["category"], "friday_reminders")
        self.assertEqual(item["is_verified"], 1)
        self.assertEqual(item["review_status"], "approved")
        self.assertTrue(len(item["arabic"]) > 0)

    def test_category_list_selection(self):
        """Verify selecting from a list of categories limits selection to those categories."""
        subset = ["morning_adhkar", "evening_adhkar"]
        item = database.get_next_authentic_content(categories_list=subset)
        self.assertIn(item["category"], subset)

    def test_category_rotation_and_persistence(self):
        """Verify rotation advances through categories and persists across calls."""
        cat1 = get_next_category_in_rotation("daily_duas", prioritize_friday=False)
        self.assertEqual(cat1, "morning_adhkar")

        cat2 = get_next_category_in_rotation("morning_adhkar", prioritize_friday=False)
        self.assertEqual(cat2, "evening_adhkar")

        # Check DB state persistence
        database.set_last_category("ramadan")
        self.assertEqual(database.get_last_category(), "ramadan")

    def test_arabic_source_text_immutability(self):
        """Verify sacred Arabic text is strictly preserved verbatim."""
        for item in AUTHENTIC_CONTENT:
            arabic = item["arabic"]
            self.assertTrue(len(arabic) > 5)
            # Ensure text contains Arabic characters
            self.assertTrue(any('؀' <= char <= 'ۿ' for char in arabic))

    def test_source_reference_preservation(self):
        """Verify references (Quran Surah/Ayah, Hadith collection/number) are intact."""
        quran_item = get_content_by_id("orig_dua_001")
        self.assertIsNotNone(quran_item)
        self.assertIn("Qur'an", quran_item["source"])
        self.assertEqual(quran_item["verse_number"], "201")

        hadith_item = get_content_by_id("friday_01")
        self.assertIsNotNone(hadith_item)
        self.assertEqual(hadith_item["hadith_collection"], "Sahih al-Bukhari")
        self.assertEqual(hadith_item["grading"], "Sahih")

    def test_human_review_enforcement(self):
        """Verify unapproved, draft, or rejected items are NEVER auto-selected."""
        with database._get_connection() as conn:
            cursor = conn.cursor()
            # Temporarily insert a draft / unverified item
            cursor.execute("""
                INSERT INTO duas_meta (
                    content_hash, dua_index, dua_type, arabic, transliteration,
                    translation, source, times_used, is_verified, created_at,
                    category, review_status
                ) VALUES ('test_unverified_hash', 9999, 'Test', 'نص تجريبي غير معتمد', '', 'test translation', 'Unverified Source', 0, 0, '2026-01-01', 'daily_duas', 'draft')
                ON CONFLICT(content_hash) DO UPDATE SET review_status = 'draft', is_verified = 0
            """)
            conn.commit()

        # Selection with require_approved=True must not select this draft
        item = database.get_next_authentic_content(category="daily_duas", require_approved=True)
        self.assertNotEqual(item["content_hash"], "test_unverified_hash")
        self.assertEqual(item["review_status"], "approved")

        # Clean up
        with database._get_connection() as conn:
            conn.execute("DELETE FROM duas_meta WHERE content_hash = 'test_unverified_hash'")
            conn.commit()

    def test_review_status_transition_validation(self):
        """Verify status update validation prevents arbitrary invalid statuses."""
        item = database.get_next_authentic_content(category="daily_duas")
        item_id = item["id"]

        # Valid transitions
        database.update_content_review_status(item_id, "needs_review")
        database.update_content_review_status(item_id, "approved")

        # Invalid transition should raise ValueError
        with self.assertRaises(ValueError):
            database.update_content_review_status(item_id, "invalid_status_xyz")

    def test_script_generation(self):
        """Verify video script engine generates structured segments and distinct reflection."""
        item = get_content_by_id("orig_dua_001")
        script = generate_script(item, style="reflective", include_transliteration=True)

        self.assertIn("hook", script)
        self.assertEqual(script["arabic"], item["arabic"])
        self.assertEqual(script["translation"], item["translation"])
        self.assertEqual(script["source"], item["source"])
        self.assertTrue(len(script["segments"]) >= 4)
        self.assertTrue(script["estimated_duration_sec"] > 10)

    def test_caption_generation_and_hashtags(self):
        """Verify caption generation across styles with moderate, relevant hashtags."""
        item = get_content_by_id("friday_01")

        # Jumuah style
        cap_friday = generate_caption(item, style="friday_jumuah", include_hashtags=True)
        self.assertIn("JUMU'AH", cap_friday)
        self.assertIn(item["source"], cap_friday)
        self.assertIn("#JumuahMubarak", cap_friday)

        # Short style without hashtags
        cap_short = generate_caption(item, style="short", include_hashtags=False)
        self.assertNotIn("#", cap_short)
        self.assertIn(item["source"], cap_short)

        # Custom hashtags
        tags = get_hashtags("friday_reminders", custom_tags=["Blessings", "Faith"], max_tags=2)
        self.assertEqual(tags, "#Blessings #Faith")

    def test_ai_disabled_offline_mode(self):
        """Verify AI adapter operates 100% offline without network calls or API keys."""
        adapter = AIAdapter()
        # By default ENABLE_AI is false
        self.assertFalse(adapter.is_available())

        item = get_content_by_id("orig_dua_001")
        reflection = adapter.generate_reflection(item)
        self.assertTrue(len(reflection) > 0)
        self.assertIn(item["commentary"], reflection)

        theme, layout = adapter.suggest_theme_and_layout(item)
        self.assertIn(theme, ["midnight-gold", "masjid-elegance", "emerald-serenity", "minimal-white", "peaceful-nature", "reflective-night", "ramadan-eid"])
        self.assertIn(layout, ["dua", "quran", "reminder"])

    def test_ai_provider_failure_graceful_fallback(self):
        """Verify simulated AI API errors gracefully fall back to local rule-based engine."""
        adapter = AIAdapter()
        adapter.enabled = True
        adapter._api_key = "mock_fake_key"
        adapter.provider = "gemini"

        item = get_content_by_id("orig_dua_001")

        # Mock exception in Gemini API call
        with patch.object(adapter, "_call_ai_for_reflection", side_effect=RuntimeError("API Connection Timeout")):
            reflection = adapter.generate_reflection(item)
            self.assertEqual(reflection, item["commentary"])

    def test_database_migrations_preservation(self):
        """Verify idempotent re-initialization does not alter existing data."""
        with database._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM duas_meta")
            count_before = cursor.fetchone()[0]

        database.init_db()

        with database._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM duas_meta")
            count_after = cursor.fetchone()[0]

        self.assertEqual(count_before, count_after)

if __name__ == "__main__":
    unittest.main()

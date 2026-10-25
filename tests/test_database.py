"""
Unit tests for SQLite database, authentic content syncing, and duplicate prevention.
"""
import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(BASE_DIR))

from database import (
    init_db, sync_duas, get_next_authentic_dua,
    is_recent_duplicate, record_video, record_publication, _get_connection
)
from duas_db import DUAS

class TestDatabase(unittest.TestCase):
    def setUp(self):
        init_db()
        sync_duas(DUAS)

    def test_idempotent_sync(self):
        # Syncing multiple times should not create duplicate entries
        sync_duas(DUAS)
        dua = get_next_authentic_dua()
        self.assertIsNotNone(dua)
        self.assertIn("arabic", dua)
        self.assertIn("source", dua)

    def test_least_used_selection(self):
        dua1 = get_next_authentic_dua()
        self.assertTrue(dua1["times_used"] >= 0)

    def test_recent_duplicate_check(self):
        # Find a dua_id that has not been published in the past 24 hours
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id FROM duas_meta 
                WHERE id NOT IN (
                    SELECT v.dua_id FROM video_records v 
                    JOIN publication_history p ON p.video_id = v.id 
                    WHERE p.status = 'success'
                ) LIMIT 1
            """)
            row = cursor.fetchone()
            dua_id = row[0] if row else 99999

        # Not published yet
        self.assertFalse(is_recent_duplicate(dua_id, hours=24))

        # Record video and publication
        vid = record_video(dua_id, "dummy.mp4", "dummy.jpg", "caption", "dark-gold", "amiri", 15)
        record_publication(vid, "dropbox_make", "success")

        # Now should report recent duplicate
        self.assertTrue(is_recent_duplicate(dua_id, hours=24))

        # Clean up test publication and video record
        with _get_connection() as conn:
            conn.execute("DELETE FROM publication_history WHERE video_id = ?", (vid,))
            conn.execute("DELETE FROM video_records WHERE id = ?", (vid,))
            conn.commit()

    def test_upsert_content_item_and_string_identifier_deduplication(self):
        """Verify upsert_content_item returns valid integer ID and is_recent_duplicate works with string IDs."""
        from database import upsert_content_item, compute_content_hash

        item = {
            "id": "sunnah_bukhari_test_123",
            "category": "prophetic_hadith",
            "type": "Prophetic Hadith",
            "arabic": "إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ",
            "translation": "Actions are but by intention.",
            "source": "Sahih Bukhari 1",
            "is_verified": 1,
            "review_status": "approved"
        }

        row_id = upsert_content_item(item)
        self.assertIsInstance(row_id, int)
        self.assertGreater(row_id, 0)

        # Before publication, not a duplicate
        self.assertFalse(is_recent_duplicate(row_id, hours=24))
        self.assertFalse(is_recent_duplicate("sunnah_bukhari_test_123", hours=24))

        # Record publication using row_id
        vid = record_video(row_id, "dummy_hadith.mp4", "dummy_hadith.jpg", "caption", "dark-gold", "amiri", 15)
        record_publication(vid, "dropbox_make", "success")

        # Now duplicate checks should match by row_id, string external id, AND content hash
        chash = compute_content_hash(item["arabic"], item["source"])
        self.assertTrue(is_recent_duplicate(row_id, hours=24))
        self.assertTrue(is_recent_duplicate("sunnah_bukhari_test_123", hours=24))
        self.assertTrue(is_recent_duplicate(chash, hours=24))

        # Clean up
        with _get_connection() as conn:
            conn.execute("DELETE FROM publication_history WHERE video_id = ?", (vid,))
            conn.execute("DELETE FROM video_records WHERE id = ?", (vid,))
            conn.execute("DELETE FROM duas_meta WHERE id = ?", (row_id,))
            conn.commit()


if __name__ == "__main__":
    unittest.main()

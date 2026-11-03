"""
tests/test_channel_discovery.py — Unit Tests for Approved Channel Discovery Engine
Verifies that:
1. Only explicitly approved channels with confirmed rights are queried.
2. If no approved channels are configured, discovery remains safely inactive.
3. XML feed entries are accurately parsed without external network requests in tests.
4. Duplicate videos are strictly prevented from being queued.
"""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

BASE_DIR = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(BASE_DIR))

from channel_discovery import (
    parse_approved_channels,
    fetch_channel_feed,
    is_video_already_known,
    run_channel_discovery
)
from database import init_db, _get_connection

SAMPLE_ATOM_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns="http://www.w3.org/2005/Atom">
  <channelId>UC_TEST_CHANNEL_123</channelId>
  <title>Authentic Islamic Reminders</title>
  <entry>
    <id>yt:video:test_vid_001</id>
    <yt:videoId>test_vid_001</yt:videoId>
    <yt:channelId>UC_TEST_CHANNEL_123</yt:channelId>
    <title>Patience and Gratitude in Islam</title>
    <link rel="alternate" href="https://www.youtube.com/watch?v=test_vid_001"/>
    <author>
      <name>Authentic Islamic Reminders</name>
    </author>
    <published>2026-10-25T08:00:00+00:00</published>
  </entry>
</feed>
"""


class TestChannelDiscovery(unittest.TestCase):
    def setUp(self):
        init_db()

    def test_empty_config_returns_empty_and_inactive(self):
        """When approved_channels.txt has no active channels, discovery stays inactive."""
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt", encoding="utf-8") as tmp:
            tmp.write("# Only comments\n# No approved channels\n")
            tmp_path = Path(tmp.name)

        try:
            channels = parse_approved_channels(tmp_path)
            self.assertEqual(len(channels), 0)

            res = run_channel_discovery(filepath=tmp_path)
            self.assertEqual(res["status"], "inactive")
            self.assertEqual(res["discovered_videos"], 0)
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_unconfirmed_rights_channels_are_ignored(self):
        """Channels with RIGHTS_CONFIRMED=NO are not activated for discovery."""
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt", encoding="utf-8") as tmp:
            tmp.write(
                "# Channel ID | Name | Rights Confirmed | Notes\n"
                "UC_UNAPPROVED | Random Channel | NO | Pending permission\n"
            )
            tmp_path = Path(tmp.name)

        try:
            channels = parse_approved_channels(tmp_path)
            self.assertEqual(len(channels), 1)
            self.assertFalse(channels[0]["rights_confirmed"])

            res = run_channel_discovery(filepath=tmp_path)
            self.assertEqual(res["status"], "inactive")
            self.assertEqual(res["discovered_videos"], 0)
        finally:
            tmp_path.unlink(missing_ok=True)

    @patch("urllib.request.urlopen")
    def test_feed_parsing_and_queueing(self, mock_urlopen):
        """Valid RSS feed is parsed and queued into autopilot_queue when rights confirmed."""
        mock_resp = MagicMock()
        mock_resp.read.return_value = SAMPLE_ATOM_XML
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt", encoding="utf-8") as tmp:
            tmp.write(
                "UC_TEST_CHANNEL_123 | Authentic Islamic Reminders | YES | Creator confirmed reuse\n"
            )
            tmp_path = Path(tmp.name)

        try:
            # First discovery run queues the video
            res = run_channel_discovery(max_new_videos=1, filepath=tmp_path)
            self.assertEqual(res["status"], "active")
            self.assertEqual(res["discovered_videos"], 1)
            self.assertEqual(res["videos"][0]["url"], "https://www.youtube.com/watch?v=test_vid_001")

            # Second discovery run must detect duplicate and NOT re-queue
            res2 = run_channel_discovery(max_new_videos=1, filepath=tmp_path)
            self.assertEqual(res2["discovered_videos"], 0)

        finally:
            tmp_path.unlink(missing_ok=True)
            with _get_connection() as conn:
                conn.execute("DELETE FROM autopilot_queue WHERE source_entry LIKE '%test_vid_001%'")
                conn.commit()


if __name__ == "__main__":
    unittest.main()

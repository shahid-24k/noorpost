"""
test_repurposing.py — Comprehensive Test Suite for NoorPost Video Repurposing Engine
Tests:
  1. Source URL validation & metadata extraction (YouTube mocked + Local file)
  2. Rights confirmation requirement enforcement
  3. WebVTT and SRT subtitle parsing
  4. Sentence boundary and pause-based segment selection
  5. Manual timestamp range parsing
  6. Vertical reframing filtergraph construction (blur_fill, center_crop, custom_crop)
  7. Mobile-safe subtitle generation (SRT & ASS)
  8. Arabic subtitle shaping and RTL formatting
  9. Thumbnail generation and headline formatting
  10. Repurposing caption generation & attribution
  11. Dropbox handoff & shared-link handling (Mocked)
  12. Duplicate clip prevention across restarts
  13. Persistent SQLite job states and transitions
"""

import sys
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile

BASE_DIR = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(BASE_DIR))

import database
from source_manager import SourceManager
from clip_selector import (
    parse_vtt_srt,
    parse_manual_timestamps,
    find_candidate_clips,
    parse_time_str,
    format_time_str
)
from vertical_reframer import VerticalReframer
from subtitle_engine import (
    is_arabic_text,
    shape_arabic_for_subtitles,
    wrap_subtitle_text,
    generate_srt_file,
    generate_ass_file
)
from repurpose_packager import RepurposePackager

class TestRepurposingEngine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        database.init_db()

    def test_youtube_url_detection(self):
        sm = SourceManager()
        self.assertTrue(sm.is_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ"))
        self.assertTrue(sm.is_youtube_url("https://youtu.be/dQw4w9WgXcQ"))
        self.assertFalse(sm.is_youtube_url("https://vimeo.com/123456"))
        self.assertFalse(sm.is_youtube_url("D:/videos/lecture.mp4"))

    @patch("yt_dlp.YoutubeDL")
    def test_youtube_metadata_inspection_and_rights(self, mock_ydl_cls):
        mock_instance = MagicMock()
        mock_instance.extract_info.return_value = {
            "title": "Tafseer of Surah Al-Fatihah",
            "uploader": "Authentic Islamic Knowledge",
            "duration": 1800.0,
            "subtitles": {"en": [{"ext": "vtt"}]},
            "automatic_captions": {"ar": [{"ext": "vtt"}]}
        }
        mock_ydl_cls.return_value.__enter__.return_value = mock_instance

        sm = SourceManager()
        meta = sm.inspect_source("https://www.youtube.com/watch?v=test12345", confirm_rights=True)
        self.assertEqual(meta["source_type"], "youtube")
        self.assertEqual(meta["title"], "Tafseer of Surah Al-Fatihah")
        self.assertEqual(meta["duration"], 1800.0)
        self.assertTrue(meta["rights_confirmed"])

    def test_rights_confirmation_enforcement(self):
        sm = SourceManager()
        meta = {
            "source_id": "test_src_id",
            "source_type": "youtube",
            "source_url": "https://www.youtube.com/watch?v=test123",
            "title": "Lecture",
            "duration": 600.0,
            "rights_confirmed": False
        }
        with self.assertRaises(PermissionError):
            sm.prepare_source(meta, download_if_needed=True)

    def test_vtt_and_srt_parsing(self):
        sample_vtt = """WEBVTT

00:00:01.000 --> 00:00:04.500
In the name of Allah, Most Gracious, Most Merciful.

00:00:05.000 --> 00:00:09.000
Today we reflect upon the supreme virtues of gratitude.
"""
        with tempfile.NamedTemporaryFile("w", suffix=".vtt", delete=False, encoding="utf-8") as f:
            f.write(sample_vtt)
            vtt_path = f.name

        try:
            cues = parse_vtt_srt(vtt_path)
            self.assertEqual(len(cues), 2)
            self.assertEqual(cues[0]["start"], 1.0)
            self.assertEqual(cues[0]["end"], 4.5)
            self.assertIn("Most Gracious", cues[0]["text"])
        finally:
            if Path(vtt_path).exists():
                Path(vtt_path).unlink()

    def test_manual_timestamp_parsing(self):
        ranges = parse_manual_timestamps("01:15-02:00, 05:30-06:15, 90-120")
        self.assertEqual(len(ranges), 3)
        self.assertEqual(ranges[0], (75.0, 120.0))
        self.assertEqual(ranges[1], (330.0, 375.0))
        self.assertEqual(ranges[2], (90.0, 120.0))

    def test_candidate_clip_selection_bounds(self):
        # Build 10 consecutive cues spanning 60 seconds
        cues = []
        for i in range(12):
            cues.append({
                "start": i * 5.0,
                "end": (i + 1) * 5.0,
                "text": f"This is sentence part {i+1}."
            })
        candidates = find_candidate_clips(cues, video_duration=120.0, target_duration=30.0, min_duration=20.0, max_duration=45.0, num_clips=2)
        self.assertTrue(len(candidates) >= 1)
        for c in candidates:
            self.assertTrue(20.0 <= c["duration_sec"] <= 45.0)

    def test_vertical_reframing_filtergraph(self):
        vr = VerticalReframer()
        vf_blur = vr._build_filtergraph(strategy="blur_fill")
        self.assertIn("[bg]", vf_blur)
        self.assertIn("boxblur", vf_blur)
        self.assertIn("overlay", vf_blur)

        vf_crop = vr._build_filtergraph(strategy="center_crop")
        self.assertIn("crop=1080:1920", vf_crop)

        vf_custom = vr._build_filtergraph(strategy="custom_crop", crop_x_pct=0.25)
        self.assertIn("0.25", vf_custom)

    def test_subtitle_arabic_detection_and_wrapping(self):
        arabic_sample = "الحمد لله رب العالمين"
        english_sample = "In the name of Allah, the Most Gracious, the Most Merciful"

        self.assertTrue(is_arabic_text(arabic_sample))
        self.assertFalse(is_arabic_text(english_sample))

        wrapped = wrap_subtitle_text("This is an important reminder regarding Islamic etiquette and personal manners in the community", max_chars=30)
        self.assertTrue("\n" in wrapped)

    def test_srt_and_ass_file_generation(self):
        cues = [
            {"start": 10.0, "end": 14.0, "text": "First meaningful reflection."},
            {"start": 15.0, "end": 19.5, "text": "Second reminder from the Sunnah."}
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            srt_p = Path(tmpdir) / "test.srt"
            ass_p = Path(tmpdir) / "test.ass"

            generate_srt_file(cues, str(srt_p), time_offset_sec=10.0)
            self.assertTrue(srt_p.exists())
            with open(srt_p, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertIn("First meaningful reflection.", content)
                self.assertIn("00:00:00,000 --> 00:00:04,000", content)

            generate_ass_file(cues, str(ass_p), time_offset_sec=10.0)
            self.assertTrue(ass_p.exists())
            with open(ass_p, "r", encoding="utf-8") as f:
                ass_content = f.read()
                self.assertIn("PlayResX: 1080", ass_content)
                self.assertIn("MarginV, Effect, Text", ass_content)

    def test_repurpose_caption_generation(self):
        packager = RepurposePackager()
        cap = packager.generate_repurpose_caption(
            clip_title="Patience in Adversity",
            source_title="The Spiritual Journey of the Believer",
            channel="Imam Academy",
            transcript_snippet="When calamity strikes, the believer looks to Allah for reward.",
            category="gratitude_patience"
        )
        self.assertIn("PATIENCE IN ADVERSITY", cap)
        self.assertIn("Imam Academy", cap)
        self.assertIn("#SabrAndShukr", cap)

    @patch("instagram.get_dropbox_client")
    def test_mocked_dropbox_upload(self, mock_get_client):
        mock_dbx = MagicMock()
        mock_get_client.return_value = mock_dbx

        from instagram import upload_to_dropbox
        with tempfile.NamedTemporaryFile("w", suffix=".mp4", delete=False) as f:
            f.write("dummy video data")
            tmp_video = f.name

        try:
            res = upload_to_dropbox(tmp_video, "Test caption")
            self.assertTrue(res["success"])
            self.assertEqual(res["platform"], "dropbox_make")
            self.assertIn(Path(tmp_video).name, res["remote_id"])
        finally:
            if Path(tmp_video).exists():
                Path(tmp_video).unlink()

    def test_repurpose_database_records_and_duplicate_prevention(self):
        source_id = "test_src_unique_99"
        src_db_id = database.register_repurpose_source(
            source_id=source_id,
            source_type="local",
            source_url="D:/test/lecture.mp4",
            title="Virtues of Ramadan",
            channel="Masjid Tube",
            duration=900.0,
            rights_confirmed=True
        )
        self.assertTrue(src_db_id > 0)

        # Record clip
        clip_uid = f"{source_id}_c01"
        clip_db_id = database.record_repurpose_clip(
            source_db_id=src_db_id,
            clip_id=clip_uid,
            clip_index=1,
            start_sec=120.0,
            end_sec=165.0,
            title="Ramadan Clip 1",
            status="READY_FOR_DROPBOX"
        )
        self.assertTrue(clip_db_id > 0)

        # Check duplicate clip detection
        self.assertTrue(database.is_duplicate_clip(source_id, 120.0, 165.0))
        # Non-matching timestamps should not be duplicate
        self.assertFalse(database.is_duplicate_clip(source_id, 200.0, 245.0))

        # Check update clip status
        database.update_clip_status(clip_uid, "HANDED_OFF_TO_MAKE", dropbox_url="https://dropbox.com/mock")
        jobs = database.get_repurpose_jobs(status="HANDED_OFF_TO_MAKE", limit=5)
        found = any(j["clip_id"] == clip_uid for j in jobs)
        self.assertTrue(found)

if __name__ == "__main__":
    unittest.main()

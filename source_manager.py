"""
source_manager.py — Video Ingestion & Metadata Engine for NoorPost Ultimate
Handles authorized YouTube sources, local video files, and batch processing.

Principles:
- Requires rights/authorization confirmation before processing.
- Uses yt-dlp strictly for permitted, authorized content without bypassing DRM or protections.
- Caches downloaded sources to prevent redundant downloads.
- Extracts duration, resolution, audio tracks, and available subtitles/transcripts.
"""

import os
import re
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from logger import log
import config

SOURCES_DIR = config.BASE_DIR / "sources"
SOURCES_DIR.mkdir(parents=True, exist_ok=True)

class SourceManager:
    """Manages ingestion of YouTube URLs and local video files."""

    def __init__(self, sources_dir: Optional[Path] = None):
        self.sources_dir = Path(sources_dir or SOURCES_DIR)
        self.sources_dir.mkdir(parents=True, exist_ok=True)

    def is_youtube_url(self, url: str) -> bool:
        """Check if string is a valid YouTube URL."""
        if not url or not isinstance(url, str):
            return False
        yt_patterns = [
            r'^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+$',
        ]
        return any(re.match(p, url.strip()) for p in yt_patterns)

    def generate_source_id(self, url_or_path: str) -> str:
        """Generate deterministic SHA256 ID for a source."""
        clean = url_or_path.strip().lower()
        return hashlib.sha256(clean.encode("utf-8")).hexdigest()[:16]

    def inspect_source(self, url_or_path: str, confirm_rights: bool = False) -> Dict[str, Any]:
        """
        Inspect video metadata without downloading full media.
        """
        url_or_path = url_or_path.strip()
        source_id = self.generate_source_id(url_or_path)

        if self.is_youtube_url(url_or_path):
            return self._inspect_youtube(url_or_path, source_id, confirm_rights)
        else:
            return self._inspect_local(url_or_path, source_id, confirm_rights)

    def _inspect_youtube(self, url: str, source_id: str, confirm_rights: bool) -> Dict[str, Any]:
        """Extract metadata for an authorized YouTube URL via yt-dlp."""
        import yt_dlp

        ydl_opts = {
            "skip_download": True,
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            subtitles = list(info.get("subtitles", {}).keys()) + list(info.get("automatic_captions", {}).keys())

            return {
                "source_id": source_id,
                "source_type": "youtube",
                "source_url": url,
                "title": info.get("title", "Untitled Lecture"),
                "channel": info.get("uploader", info.get("channel", "Unknown Channel")),
                "duration": float(info.get("duration", 0.0)),
                "language": info.get("language", "en"),
                "available_subtitles": subtitles,
                "rights_confirmed": confirm_rights,
                "local_video_path": None,
                "local_subtitle_path": None,
            }
        except Exception as e:
            raise RuntimeError(f"Could not inspect YouTube video: {e}")

    def _inspect_local(self, path_str: str, source_id: str, confirm_rights: bool) -> Dict[str, Any]:
        """Inspect a local video file on disk."""
        local_path = Path(path_str).resolve()
        if not local_path.exists():
            raise FileNotFoundError(f"Local video file not found: {path_str}")

        # Check subtitle alongside video (e.g. video.srt or video.vtt)
        sub_path = None
        for ext in [".vtt", ".srt", ".sub"]:
            candidate = local_path.with_suffix(ext)
            if candidate.exists():
                sub_path = str(candidate)
                break

        # Get duration using ffprobe
        duration = self._get_local_duration(str(local_path))

        return {
            "source_id": source_id,
            "source_type": "local",
            "source_url": str(local_path),
            "title": local_path.stem.replace("_", " ").title(),
            "channel": "Local Library",
            "duration": duration,
            "language": "en",
            "available_subtitles": [Path(sub_path).suffix[1:]] if sub_path else [],
            "rights_confirmed": confirm_rights,
            "local_video_path": str(local_path),
            "local_subtitle_path": sub_path,
        }

    def _get_local_duration(self, video_path: str) -> float:
        """Extract video duration in seconds via ffprobe."""
        import subprocess
        try:
            cmd = [
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", video_path
            ]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            return float(res.stdout.strip())
        except Exception:
            # Fallback to MoviePy
            try:
                from moviepy.editor import VideoFileClip
                with VideoFileClip(video_path) as clip:
                    return float(clip.duration)
            except Exception:
                return 0.0

    def prepare_source(self, metadata: Dict[str, Any], download_if_needed: bool = True) -> Tuple[str, Optional[str]]:
        """
        Ensure source video and subtitle files are present locally.
        Returns: (local_video_path, local_subtitle_path)
        """
        if metadata["source_type"] == "local":
            return metadata["local_video_path"], metadata.get("local_subtitle_path")

        # YouTube Source
        if not metadata.get("rights_confirmed"):
            raise PermissionError(
                "Rights not confirmed. Repurposing requires explicit user authorization confirmation."
            )

        source_id = metadata["source_id"]
        target_video = self.sources_dir / f"{source_id}.mp4"
        target_sub = self.sources_dir / f"{source_id}.en.vtt"

        # Check if already cached
        if target_video.exists() and target_video.stat().st_size > 1024:
            log(f"📦 Source video already cached: {target_video.name}")
            sub_res = str(target_sub) if target_sub.exists() else None
            return str(target_video), sub_res

        if not download_if_needed:
            raise FileNotFoundError(f"Source video not downloaded yet: {target_video}")

        import yt_dlp
        log(f"⬇️  Downloading authorized source: {metadata['title']} ({metadata['duration']:.0f}s)...")

        out_template = str(self.sources_dir / f"{source_id}.%(ext)s")
        ydl_opts = {
            "format": "bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "outtmpl": out_template,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["en", "ar"],
            "subtitlesformat": "vtt",
            "quiet": True,
            "no_warnings": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([metadata["source_url"]])

        # Locate downloaded video
        found_video = None
        for ext in [".mp4", ".mkv", ".webm"]:
            cand = self.sources_dir / f"{source_id}{ext}"
            if cand.exists():
                found_video = cand
                break

        if not found_video:
            raise FileNotFoundError(f"Failed to locate downloaded video for {source_id}")

        # Locate subtitle file
        found_sub = None
        for sub_file in self.sources_dir.glob(f"{source_id}*.vtt"):
            found_sub = str(sub_file)
            break

        return str(found_video), found_sub

    def parse_batch_file(self, batch_path: str) -> List[str]:
        """Parse list of URLs or paths from text or JSON batch file."""
        p = Path(batch_path)
        if not p.exists():
            raise FileNotFoundError(f"Batch file not found: {batch_path}")

        lines = []
        if p.suffix.lower() == ".json":
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    lines = [str(x).strip() for x in data if str(x).strip()]
                elif isinstance(data, dict):
                    lines = [str(x).strip() for x in data.get("sources", []) if str(x).strip()]
        else:
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    s = line.strip()
                    if s and not s.startswith("#"):
                        lines.append(s)
        return lines

source_engine = SourceManager()

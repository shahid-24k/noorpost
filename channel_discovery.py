"""
channel_discovery.py — Approved Channel Discovery Engine for NoorPost Ultimate

Principles:
1. Reads only explicitly approved channels from approved_channels.txt.
2. Checks creator authorization (RIGHTS_CONFIRMED must be YES).
3. Uses permitted public syndication feeds (YouTube official Atom/RSS feed) without scraping or bypassing TOS.
4. Strictly prevents duplicate queueing and processing.
5. Inactive by default if no channels are configured with confirmed rights.
"""

import re
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

import config
from logger import log
from database import _get_connection, init_db
from autopilot import _hash_entry, init_autopilot_db

APPROVED_CHANNELS_FILE = config.BASE_DIR / "approved_channels.txt"
YOUTUBE_RSS_BASE = "https://www.youtube.com/feeds/videos.xml?channel_id="
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}


def parse_approved_channels(filepath: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Parse approved_channels.txt and return list of authorized channel configurations.
    Ignores blank lines and comments.
    """
    path = filepath or APPROVED_CHANNELS_FILE
    if not path.exists():
        return []

    channels = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            parts = [p.strip() for p in stripped.split("|")]
            if not parts or not parts[0]:
                continue

            channel_id = parts[0]
            channel_name = parts[1] if len(parts) > 1 else channel_id
            rights_str = parts[2].lower() if len(parts) > 2 else ""
            rights_confirmed = rights_str in ("yes", "true", "1", "confirmed")
            notes = parts[3] if len(parts) > 3 else ""

            channels.append({
                "channel_id": channel_id,
                "channel_name": channel_name,
                "rights_confirmed": rights_confirmed,
                "notes": notes
            })

    return channels


def fetch_channel_feed(channel_id: str, timeout: int = 10) -> List[Dict[str, Any]]:
    """
    Fetch and parse the official public Atom RSS feed for a YouTube channel.
    Returns list of recent video entries: [{"video_id": ..., "title": ..., "url": ..., "published": ...}]
    """
    feed_url = f"{YOUTUBE_RSS_BASE}{channel_id}"
    req = urllib.request.Request(
        feed_url,
        headers={"User-Agent": "NoorPost-Ultimate/2.3 (Islamic Educational RSS Reader)"}
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            xml_data = resp.read()
    except Exception as e:
        log(f"⚠️  Could not fetch RSS feed for channel {channel_id}: {e}", level="WARNING")
        return []

    entries = []
    try:
        root = ET.fromstring(xml_data)
        for entry in root.findall("atom:entry", ATOM_NS):
            yt_vid = entry.find("yt:videoId", ATOM_NS)
            title_elem = entry.find("atom:title", ATOM_NS)
            link_elem = entry.find("atom:link", ATOM_NS)
            pub_elem = entry.find("atom:published", ATOM_NS)

            vid_id = yt_vid.text.strip() if yt_vid is not None and yt_vid.text else None
            title = title_elem.text.strip() if title_elem is not None and title_elem.text else "Untitled"
            url = link_elem.get("href") if link_elem is not None else None
            if not url and vid_id:
                url = f"https://www.youtube.com/watch?v= {vid_id}".replace(" ", "")

            published = pub_elem.text.strip() if pub_elem is not None and pub_elem.text else ""

            if vid_id and url:
                entries.append({
                    "video_id": vid_id,
                    "title": title,
                    "url": url,
                    "published": published
                })
    except Exception as e:
        log(f"⚠️  Failed to parse RSS XML for channel {channel_id}: {e}", level="WARNING")

    return entries


def is_video_already_known(url: str) -> bool:
    """Check if video is already queued or processed in autopilot_queue or repurpose_sources."""
    v_hash = _hash_entry(url)
    clean_url = url.strip().lower()

    with _get_connection() as conn:
        cursor = conn.cursor()
        # Check autopilot_queue
        cursor.execute("SELECT id FROM autopilot_queue WHERE source_hash = ?", (v_hash,))
        if cursor.fetchone():
            return True

        # Check repurpose_sources
        cursor.execute("SELECT id FROM repurpose_sources WHERE LOWER(source_url) = ? OR source_id = ?", (clean_url, v_hash[:16]))
        if cursor.fetchone():
            return True

    return False


def run_channel_discovery(
    max_new_videos: int = 1,
    filepath: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Discover new eligible videos from approved channels with confirmed rights.
    Inserts newly discovered videos into autopilot_queue.
    """
    init_autopilot_db()
    channels = parse_approved_channels(filepath)
    active_channels = [c for c in channels if c["rights_confirmed"]]

    if not active_channels:
        log("ℹ️  No approved channels with confirmed rights configured in approved_channels.txt. Discovery is inactive.")
        return {
            "status": "inactive",
            "active_channels": 0,
            "discovered_videos": 0,
            "videos": []
        }

    log(f"🔍 Checking {len(active_channels)} approved channel(s) for authorized video discovery...")
    discovered = []
    now_iso = datetime.now().isoformat()

    with _get_connection() as conn:
        cursor = conn.cursor()
        for ch in active_channels:
            ch_id = ch["channel_id"]
            ch_name = ch["channel_name"]
            entries = fetch_channel_feed(ch_id)

            for item in entries:
                if len(discovered) >= max_new_videos:
                    break

                video_url = item["url"]
                if is_video_already_known(video_url):
                    continue

                v_hash = _hash_entry(video_url)
                queue_entry = f"{video_url} | {ch_name} | YES"
                cursor.execute("""
                    INSERT INTO autopilot_queue
                        (source_entry, source_hash, channel, rights_confirmed, status, queued_at, updated_at)
                    VALUES (?, ?, ?, 1, 'QUEUED', ?, ?)
                """, (queue_entry, v_hash, ch_name, now_iso, now_iso))
                conn.commit()

                discovered.append({
                    "channel": ch_name,
                    "title": item["title"],
                    "url": video_url,
                    "hash": v_hash
                })
                log(f"📥 Discovered new authorized lecture: '{item['title']}' ({ch_name})")

            if len(discovered) >= max_new_videos:
                break

    log(f"✨ Channel discovery complete: {len(discovered)} new video(s) queued.")
    return {
        "status": "active",
        "active_channels": len(active_channels),
        "discovered_videos": len(discovered),
        "videos": discovered
    }

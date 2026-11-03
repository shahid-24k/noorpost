"""
youtube.py — YouTube Shorts uploader via YouTube Data API v3 for NoorPost Ultimate
Handles OAuth authentication, video uploads, and error reporting.
Genuinely optional: cleanly skips when unconfigured without crashing the pipeline.
"""

import os
import pickle
import time
from pathlib import Path
from typing import Dict, Any, Optional

import config
from logger import log

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def get_youtube_client():
    """
    Get authenticated YouTube API client.
    - Loads saved token if available.
    - Refreshes expired token automatically.
    - If unconfigured, returns None gracefully.
    """
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    creds = None
    token_path = Path(config.YT_TOKEN_FILE)
    creds_path = Path(config.YT_CREDENTIALS_FILE)

    # 1. Load saved token
    if token_path.exists():
        try:
            with open(token_path, "rb") as f:
                creds = pickle.load(f)
        except Exception as e:
            log(f"⚠️  Could not read YouTube token file: {e}", level="WARNING")

    # 2. Refresh if expired
    if creds and creds.expired and creds.refresh_token:
        try:
            log("🔄 Refreshing expired YouTube token...")
            creds.refresh(Request())
            with open(token_path, "wb") as f:
                pickle.dump(creds, f)
            log("✅ YouTube token refreshed.")
        except Exception as e:
            log(f"⚠️  Could not refresh YouTube token: {e}", level="WARNING")
            creds = None

    # 3. First-time authentication (interactive browser)
    if not creds or not creds.valid:
        if not creds_path.exists():
            return None
        try:
            log("🔐 Opening browser for one-time YouTube authentication...")
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
            creds = flow.run_local_server(port=0)
            with open(token_path, "wb") as f:
                pickle.dump(creds, f)
            log("✅ YouTube token saved.")
        except Exception as e:
            log(f"❌ YouTube authentication failed: {e}", level="ERROR")
            return None

    return build("youtube", "v3", credentials=creds)

def upload_short(video_path: str, dua: Dict[str, Any], caption: str) -> Dict[str, Any]:
    """
    Upload video as a YouTube Short.
    Returns:
        {"success": bool, "platform": "youtube", "url": str, "remote_id": str, "error": str}
    """
    if config.SKIP_YOUTUBE:
        log("⏭️  YouTube skipped (SKIP_YOUTUBE=True)")
        return {"success": False, "status": "skipped", "error": "SKIP_YOUTUBE"}

    if not config.is_youtube_configured():
        log("⏭️  YouTube credentials not configured. Skipping YouTube upload.")
        return {"success": False, "status": "skipped", "error": "NOT_CONFIGURED"}

    try:
        from googleapiclient.http import MediaFileUpload
        from googleapiclient.errors import HttpError
    except ImportError:
        log("⚠️  Google API client libraries not installed. Skipping YouTube.", level="WARNING")
        return {"success": False, "status": "skipped", "error": "DEPENDENCY_MISSING"}

    youtube = get_youtube_client()
    if not youtube:
        return {"success": False, "status": "failed", "error": "AUTH_FAILED"}

    dua_type = dua.get("type", dua.get("dua_type", "Authentic Dua"))
    source = dua.get("source", "Quran/Hadith")
    title = f"{dua_type} | {source} #Shorts #Islam #Dua"[:100]

    body = {
        "snippet": {
            "title": title,
            "description": caption,
            "tags": [
                "Islam", "Quran", "Dua", "Sunnah", "Muslim",
                "Hadith", "Shorts", "DailyDua", "Islamic", "Allah",
                "Dhikr", "Alhamdulillah", "SubhanAllah", "Iman", "Faith"
            ],
            "categoryId": "22",  # People & Blogs
            "defaultLanguage": "en",
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }

    try:
        log("📤 Uploading video to YouTube Shorts...")
        media = MediaFileUpload(
            video_path,
            mimetype="video/mp4",
            resumable=True,
            chunksize=5 * 1024 * 1024,
        )

        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                pct = int(status.progress() * 100)
                log(f"   YouTube upload progress: {pct}%")

        video_id = response.get("id", "")
        yt_url = f"https://youtube.com/shorts/{video_id}"
        log(f"✅ YouTube Short uploaded: {yt_url}")
        return {
            "success": True,
            "platform": "youtube",
            "url": yt_url,
            "remote_id": video_id,
            "error": None
        }

    except HttpError as e:
        log(f"❌ YouTube HTTP error: {e}", level="ERROR")
        return {"success": False, "platform": "youtube", "url": None, "remote_id": None, "error": str(e)}
    except Exception as e:
        log(f"❌ YouTube error: {e}", level="ERROR")
        return {"success": False, "platform": "youtube", "url": None, "remote_id": None, "error": str(e)}

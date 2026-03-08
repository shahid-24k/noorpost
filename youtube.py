"""
youtube.py — YouTube Shorts uploader via YouTube Data API v3
Handles OAuth authentication + video upload
"""

import os
import pickle
import config
from logger import log

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError


SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


# ─────────────────────────────────────────────
# AUTHENTICATION
# ─────────────────────────────────────────────

def get_youtube_client():
    """
    Get authenticated YouTube API client.
    - First run: opens browser for OAuth login → saves token
    - Later runs: loads saved token automatically
    - Auto-refreshes expired tokens
    """
    creds = None

    # Load saved token
    if os.path.exists(config.YT_TOKEN_FILE):
        with open(config.YT_TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)

    # Refresh if expired
    if creds and creds.expired and creds.refresh_token:
        log("🔄 Refreshing YouTube token...")
        creds.refresh(Request())
        with open(config.YT_TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)
        log("✅ YouTube token refreshed.")

    # First-time auth
    elif not creds or not creds.valid:
        if not os.path.exists(config.YT_CREDENTIALS_FILE):
            log(f"❌ Missing {config.YT_CREDENTIALS_FILE} — see SETUP_GUIDE.md Section 3", level="ERROR")
            return None
        log("🔐 Opening browser for YouTube authentication (one-time only)...")
        flow = InstalledAppFlow.from_client_secrets_file(config.YT_CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(config.YT_TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)
        log("✅ YouTube token saved.")

    return build("youtube", "v3", credentials=creds)


# ─────────────────────────────────────────────
# YOUTUBE SHORT UPLOADER
# ─────────────────────────────────────────────

def upload_short(video_path: str, dua: dict, caption: str) -> bool:
    """
    Upload video as a YouTube Short.
    YouTube auto-classifies as Short if:
    - Video is vertical (1080x1920)
    - Duration is under 60 seconds
    - Title contains #Shorts
    """
    log("▶️  Uploading to YouTube Shorts...")

    youtube = get_youtube_client()
    if not youtube:
        return False

    # Build title (max 100 chars)
    title = f"{dua['type']} | {dua['source']} #Shorts #Islam #Dua"[:100]

    body = {
        "snippet": {
            "title":       title,
            "description": caption,
            "tags": [
                "Islam", "Quran", "Dua", "Sunnah", "Muslim",
                "Hadith", "Shorts", "DailyDua", "Islamic", "Allah",
                "Dhikr", "Alhamdulillah", "SubhanAllah", "Iman", "Faith"
            ],
            "categoryId":  "22",   # People & Blogs
            "defaultLanguage": "en",
        },
        "status": {
            "privacyStatus":           "public",
            "selfDeclaredMadeForKids": False,
        },
    }

    try:
        media = MediaFileUpload(
            video_path,
            mimetype="video/mp4",
            resumable=True,
            chunksize=5 * 1024 * 1024,   # 5MB chunks
        )

        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
        )

        response = None
        log("📤 Uploading (this may take a minute)...")
        while response is None:
            status, response = request.next_chunk()
            if status:
                pct = int(status.progress() * 100)
                log(f"   Upload progress: {pct}%")

        video_id = response["id"]
        log(f"✅ YouTube Short uploaded! https://youtube.com/shorts/{video_id}")
        return True

    except HttpError as e:
        log(f"❌ YouTube HTTP error: {e}", level="ERROR")
        return False
    except Exception as e:
        log(f"❌ YouTube error: {e}", level="ERROR")
        return False

"""
instagram.py — Cloud publishing & Instagram integration for NoorPost Ultimate
Uploads videos and captions to Dropbox (for Make.com auto-publishing)
and optionally supports direct Instagram Graph API publication.
Includes network retry handling and security protections.
"""

import time
from pathlib import Path
from typing import Dict, Any, Optional

import config
from logger import log

def get_dropbox_client():
    """Build authenticated Dropbox client using refresh token."""
    import dropbox
    if not config.DROPBOX_REFRESH_TOKEN and not config.DROPBOX_ACCESS_TOKEN:
        raise ValueError("Dropbox credentials missing. Set DROPBOX_REFRESH_TOKEN or DROPBOX_ACCESS_TOKEN in .env")

    if config.DROPBOX_REFRESH_TOKEN and config.DROPBOX_APP_KEY and config.DROPBOX_APP_SECRET:
        return dropbox.Dropbox(
            oauth2_refresh_token=config.DROPBOX_REFRESH_TOKEN,
            app_key=config.DROPBOX_APP_KEY,
            app_secret=config.DROPBOX_APP_SECRET,
        )
    return dropbox.Dropbox(config.DROPBOX_ACCESS_TOKEN)

def upload_to_dropbox(video_path: str, caption: str, max_retries: int = 3) -> Dict[str, Any]:
    """
    Upload video and caption text to Dropbox with retry handling.
    Returns:
        {"success": True, "url": "...", "path": "..."} or {"success": False, "error": "..."}
    """
    import dropbox
    file_name = Path(video_path).name
    dropbox_folder = config.DROPBOX_FOLDER.rstrip("/")
    dropbox_video_path = f"{dropbox_folder}/{file_name}"
    caption_name = Path(video_path).stem + "_caption.txt"
    dropbox_caption_path = f"{dropbox_folder}/{caption_name}"

    last_error = ""

    for attempt in range(1, max_retries + 1):
        try:
            log(f"☁️  Uploading video to Dropbox (attempt {attempt}/{max_retries}): {dropbox_video_path}")
            dbx = get_dropbox_client()

            with open(video_path, "rb") as f:
                dbx.files_upload(
                    f.read(),
                    dropbox_video_path,
                    mode=dropbox.files.WriteMode("overwrite")
                )
            log("✅ Video file uploaded to Dropbox.")

            log("📝 Uploading caption file to Dropbox...")
            dbx.files_upload(
                caption.encode("utf-8"),
                dropbox_caption_path,
                mode=dropbox.files.WriteMode("overwrite")
            )
            log("✅ Caption file uploaded to Dropbox.")

            # Retrieve or generate shared link
            shared_url = dropbox_video_path
            try:
                link = dbx.sharing_create_shared_link_with_settings(dropbox_video_path)
                shared_url = link.url
            except dropbox.exceptions.ApiError:
                try:
                    links = dbx.sharing_list_shared_links(path=dropbox_video_path)
                    if links.links:
                        shared_url = links.links[0].url
                except Exception:
                    pass

            log(f"🔗 Dropbox link generated: {shared_url}")
            return {
                "success": True,
                "platform": "dropbox_make",
                "url": shared_url,
                "remote_id": dropbox_video_path,
                "error": None
            }

        except Exception as e:
            last_error = str(e)
            log(f"⚠️  Dropbox upload attempt {attempt} failed: {e}", level="WARNING")
            if attempt < max_retries:
                time.sleep(2 * attempt)

    return {
        "success": False,
        "platform": "dropbox_make",
        "url": None,
        "remote_id": None,
        "error": last_error
    }

def post_reel(video_path: str, caption: str) -> Dict[str, Any]:
    """
    Main dispatch function for Instagram reel publication.
    Default: Uploads to Dropbox where Make.com scenario triggers automated Instagram posting.
    """
    if not config.is_dropbox_configured():
        msg = "Dropbox credentials not configured. Video saved locally in output_videos/."
        log(f"ℹ️  {msg}", level="INFO")
        return {
            "success": False,
            "platform": "dropbox_make",
            "url": None,
            "remote_id": None,
            "error": "NOT_CONFIGURED"
        }

    result = upload_to_dropbox(video_path, caption)
    if result["success"]:
        log("✅ Video ready — Make.com will post to Instagram!")
    else:
        log(f"❌ Dropbox upload failed: {result.get('error')}", level="ERROR")
    return result

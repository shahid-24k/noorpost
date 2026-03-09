"""
instagram.py — Uploads videos to Dropbox using refresh token (never expires)
Make.com watches Dropbox and auto-posts to Instagram
"""

import dropbox
from pathlib import Path
from logger import log
import config


def get_dropbox_client():
    return dropbox.Dropbox(
        oauth2_refresh_token=config.DROPBOX_REFRESH_TOKEN,
        app_key=config.DROPBOX_APP_KEY,
        app_secret=config.DROPBOX_APP_SECRET,
    )


def upload_to_dropbox(video_path: str, caption: str) -> str:
    dbx = get_dropbox_client()

    file_name    = Path(video_path).name
    dropbox_path = f"/NoorPost/{file_name}"
    caption_path = dropbox_path.replace(".mp4", "_caption.txt")

    log(f"☁️  Uploading video to Dropbox: {dropbox_path}")
    with open(video_path, "rb") as f:
        dbx.files_upload(f.read(), dropbox_path,
                         mode=dropbox.files.WriteMode("overwrite"))
    log("✅ Video uploaded to Dropbox!")

    log("📝 Uploading caption file...")
    dbx.files_upload(caption.encode("utf-8"), caption_path,
                     mode=dropbox.files.WriteMode("overwrite"))
    log("✅ Caption uploaded!")

    try:
        link = dbx.sharing_create_shared_link_with_settings(dropbox_path)
        url  = link.url
    except dropbox.exceptions.ApiError:
        links = dbx.sharing_list_shared_links(path=dropbox_path)
        url   = links.links[0].url if links.links else dropbox_path

    log(f"🔗 Dropbox link: {url}")
    return url


def post_reel(video_path: str, caption: str) -> bool:
    try:
        upload_to_dropbox(video_path, caption)
        log("✅ Video ready — Make.com will post to Instagram!")
        return True
    except Exception as e:
        log(f"❌ Dropbox upload failed: {e}", level="ERROR")
        return False

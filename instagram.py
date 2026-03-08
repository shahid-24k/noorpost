"""
instagram.py — Uploads videos to Dropbox
Make.com watches the Dropbox folder and auto-posts to Instagram
No Meta API tokens needed!
"""

import dropbox
import os
from pathlib import Path
from logger import log
import config


# ─────────────────────────────────────────────
# DROPBOX UPLOADER
# ─────────────────────────────────────────────

def upload_to_dropbox(video_path: str, caption: str) -> str:
    """Upload video + caption to Dropbox /NoorPost/ folder."""
    dbx = dropbox.Dropbox(config.DROPBOX_ACCESS_TOKEN)

    file_name    = Path(video_path).name
    dropbox_path = f"/NoorPost/{file_name}"
    caption_path = dropbox_path.replace(".mp4", "_caption.txt")

    # ── Upload video ──
    log(f"☁️  Uploading video to Dropbox: {dropbox_path}")
    with open(video_path, "rb") as f:
        dbx.files_upload(
            f.read(),
            dropbox_path,
            mode=dropbox.files.WriteMode("overwrite"),
        )
    log("✅ Video uploaded to Dropbox!")

    # ── Upload caption as text file ──
    log("📝 Uploading caption file...")
    dbx.files_upload(
        caption.encode("utf-8"),
        caption_path,
        mode=dropbox.files.WriteMode("overwrite"),
    )
    log("✅ Caption uploaded to Dropbox!")

    # ── Get shareable link ──
    try:
        link = dbx.sharing_create_shared_link(dropbox_path)
        url = link.url
    except dropbox.exceptions.ApiError:
        # Link already exists — get existing one
        links = dbx.sharing_list_shared_links(path=dropbox_path)
        url = links.links[0].url if links.links else dropbox_path

    log(f"🔗 Dropbox link: {url}")
    return url


# ─────────────────────────────────────────────
# MAIN FUNCTION — called by pipeline.py
# ─────────────────────────────────────────────

def post_reel(video_path: str, caption: str) -> bool:
    """
    Upload video to Dropbox /NoorPost/ folder.
    Make.com scenario watches this folder and auto-posts to Instagram.
    """
    try:
        upload_to_dropbox(video_path, caption)
        log("✅ Video ready in Dropbox — Make.com will post to Instagram!")
        return True
    except Exception as e:
        log(f"❌ Dropbox upload failed: {e}", level="ERROR")
        return False

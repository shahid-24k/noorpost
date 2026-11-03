---
name: dropbox-make-workflow
description: Integration patterns for delivering generated video assets and captions to Dropbox for automated Make.com Instagram Reel publishing.
---

# Dropbox & Make.com Workflow Skill

## Overview
Preserves the existing Dropbox folder structure and file naming conventions so Make.com scenarios trigger reliably without intervention.

## Key Rules
1. **Folder Convention**: Upload MP4 videos to `DROPBOX_FOLDER` (default `/NoorPost`).
2. **Caption Pairing**: Upload `<video_stem>_caption.txt` alongside the video.
3. **Thumbnails**: Store preview images in local `output_videos/previews/` and optionally in `/NoorPost/previews/` to avoid triggering video webhooks prematurely.
4. **Shared Links**: Create public shared link via `dbx.sharing_create_shared_link_with_settings()` to allow Instagram Graph API media access.
5. **Idempotency**: Prevent duplicate uploads by checking SQLite publication and video records before uploading.

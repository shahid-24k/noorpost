"""
pipeline.py — Master pipeline: pick dua → generate video → upload to Dropbox
Make.com watches Dropbox and posts to Instagram automatically
"""

import random
from datetime import datetime
from duas_db import DUAS, CAPTION_TEMPLATES
from video_generator import generate_video
from instagram import post_reel
from logger import log
import config

_used_indices = []


def run_pipeline():
    """
    Full automation cycle:
    1. Pick unique authentic dua
    2. Generate dark aesthetic video
    3. Upload to Dropbox (Make.com posts to Instagram)
    4. Upload to YouTube (if enabled)
    """
    log("=" * 50)
    log(f"🚀 Pipeline started at {datetime.now().strftime('%H:%M:%S')}")
    log("=" * 50)

    # ── 1. Pick unused dua ──
    global _used_indices
    remaining = [i for i in range(len(DUAS)) if i not in _used_indices]
    if not remaining:
        _used_indices = []
        remaining = list(range(len(DUAS)))
    idx = random.choice(remaining)
    _used_indices.append(idx)
    dua = DUAS[idx]
    log(f"📖 Selected: [{dua['type']}] {dua['source']}")

    # ── 2. Build caption ──
    template = random.choice(CAPTION_TEMPLATES)
    caption  = template.format(
        type=dua["type"],
        arabic=dua["arabic"],
        translation=dua["translation"],
        source=dua["source"],
    )
    log("✍️  Caption generated.")

    # ── 3. Generate video ──
    try:
        video_path = generate_video(dua)
    except Exception as e:
        log(f"❌ Video generation failed: {e}", level="ERROR")
        return

    # ── 4. Upload to Dropbox → Make.com → Instagram ──
    ig_success = False
    try:
        ig_success = post_reel(video_path, caption)
    except Exception as e:
        log(f"❌ Dropbox upload failed: {e}", level="ERROR")

    # ── 5. Upload to YouTube (optional) ──
    yt_success = False
    if not getattr(config, "SKIP_YOUTUBE", True):
        try:
            from youtube import upload_short
            yt_success = upload_short(video_path, dua, caption)
        except Exception as e:
            log(f"❌ YouTube failed: {e}", level="ERROR")
    else:
        log("⏭️  YouTube skipped (SKIP_YOUTUBE=True in config.py)")

    # ── 6. Summary ──
    log("=" * 50)
    log(f"✅ Dropbox/Instagram: {'SUCCESS' if ig_success else 'FAILED'}")
    log(f"✅ YouTube:           {'SKIPPED' if getattr(config, 'SKIP_YOUTUBE', True) else ('SUCCESS' if yt_success else 'FAILED')}")
    log("🌟 Cycle complete — بارك الله فيك")
    log("=" * 50)

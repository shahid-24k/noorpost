"""
pipeline.py — Master Automation Pipeline for NoorPost Ultimate
Coordinates intelligent content selection, script generation, caption crafting,
video rendering, human preview/review checkpoints, and multi-platform publishing.
Persistently tracks all history in SQLite to prevent duplicates.
"""

import random
from datetime import datetime
from typing import Dict, Any, Optional, List

import config
from logger import log
from content_db import AUTHENTIC_CONTENT, DUAS
from categories import resolve_category
from database import (
    init_db,
    sync_duas,
    upsert_content_item,
    get_next_authentic_content,
    is_recent_duplicate,
    is_duplicate_caption,
    record_video,
    update_video_status,
    record_publication,
    start_scheduler_run,
    finish_scheduler_run,
)
from script_engine import generate_script
from caption_engine import generate_caption
from ai_adapter import ai_engine
from video_generator import generate_video
from sunnah_api import sunnah_client
from ummah_api import ummah_api
from nasheed_engine import nasheed_engine

from instagram import post_reel
from youtube import upload_short

# ─────────────────────────────────────────────
# STAGE 1: INTELLIGENT CONTENT SELECTION
# ─────────────────────────────────────────────

def select_content(
    category: Optional[str] = None,
    categories_list: Optional[List[str]] = None,
    force_sahih_hadith: bool = False,
    prefer_ummah: bool = True,
) -> Dict[str, Any]:
    """
    Select verified authentic content with strict duplicate prevention.
    Integrates UmmahAPI as the primary Quran and Sahih Hadith (Bukhari & Muslim) provider,
    with safe canonical local database fallback.
    Strict Islamic Content Policy enforced: ONLY Quran, Bukhari, and Muslim permitted.
    """
    init_db()
    sync_duas(AUTHENTIC_CONTENT)

    # 1. Primary Provider: UmmahAPI (Quran & Sahih Bukhari / Muslim)
    if prefer_ummah:
        try:
            ummah_item = None
            if force_sahih_hadith or category == "prophetic_hadith":
                col = random.choice(["bukhari", "muslim"])
                log(f"🔍 [UmmahAPI] Querying verified Sahih Hadith ({col})...")
                raw = ummah_api.get_random_hadith(col)
                if raw:
                    ummah_item = ummah_api.format_hadith_record(raw["collection"], raw["hadith_number"])
            elif category == "quranic_verses":
                log("🔍 [UmmahAPI] Querying verified Qur'an verse...")
                raw = ummah_api.get_random_ayah()
                if raw:
                    ummah_item = ummah_api.format_quran_record(raw["surah_number"], raw["ayah_number"])
            elif category is None:
                choice = random.choice(["quran", "bukhari", "muslim"])
                if choice == "quran":
                    log("🔍 [UmmahAPI] Rotating: Querying verified Qur'an verse...")
                    raw = ummah_api.get_random_ayah()
                    if raw:
                        ummah_item = ummah_api.format_quran_record(raw["surah_number"], raw["ayah_number"])
                else:
                    log(f"🔍 [UmmahAPI] Rotating: Querying verified Sahih Hadith ({choice})...")
                    raw = ummah_api.get_random_hadith(choice)
                    if raw:
                        ummah_item = ummah_api.format_hadith_record(raw["collection"], raw["hadith_number"])

            if ummah_item:
                ok, reason = ummah_api.verify_content_item(ummah_item)
                if ok:
                    row_id = upsert_content_item(ummah_item)
                    ummah_item["id"] = row_id
                    if not is_recent_duplicate(row_id, hours=24):
                        log(f"📖 Selected Verified Content (UmmahAPI): [{ummah_item['source']}]")
                        return ummah_item
                    else:
                        log(f"ℹ️  UmmahAPI item {ummah_item['source']} was recently published. Falling back to pool.", level="INFO")
                else:
                    log(f"⚠️  UmmahAPI verification rejected candidate: {reason}", level="WARNING")
        except Exception as e:
            log(f"⚠️  UmmahAPI query failed or offline ({e}); proceeding to secondary/database fallback.", level="WARNING")

    # 2. Secondary Provider for Hadith: Sunnah.com (if UmmahAPI did not return and hadith was requested)
    if force_sahih_hadith or category == "prophetic_hadith":
        if sunnah_client.is_configured():
            try:
                log("🔍 Querying Sunnah.com API for verified Sahih Hadith...")
                raw_hadith = sunnah_client.get_random_hadith("bukhari")
                if not raw_hadith:
                    raw_hadith = sunnah_client.get_random_hadith("muslim")
                if raw_hadith:
                    hadith_item = sunnah_client.format_hadith_record(raw_hadith)
                    if hadith_item:
                        row_id = upsert_content_item(hadith_item)
                        hadith_item["id"] = row_id
                        if not is_recent_duplicate(row_id, hours=24):
                            log(f"📖 Selected Verified Sahih Hadith (Sunnah.com): [{hadith_item['source']}]")
                            return hadith_item
            except Exception as e:
                log(f"⚠️  Sunnah.com API query failed ({e}); falling back to local canonical database.", level="WARNING")
        category = "prophetic_hadith"

    # 3. Canonical Local Database Selection with Strict Sahih Filter
    item = get_next_authentic_content(
        category=category,
        categories_list=categories_list,
        exclude_recent_hours=24,
        require_approved=True,
        strict_sahih_only=True
    )
    content_id = item["id"]

    # Verify not recently published (within past 24 hours)
    if is_recent_duplicate(content_id, hours=24):
        log(f"⚠️  Content #{content_id} was recently published. Selecting another authentic item...", level="WARNING")
        item = get_next_authentic_content(
            category=category,
            categories_list=categories_list,
            exclude_recent_hours=48,
            require_approved=True,
            strict_sahih_only=True
        )

    cat_name = item.get("category", "daily_duas")
    content_type = item.get("type", item.get("dua_type", "Authentic Teaching"))
    log(f"📖 Selected Authentic Content: [{cat_name}] [{content_type}] {item['source']}")
    return item

# ─────────────────────────────────────────────
# STAGE 2: CAPTION GENERATION
# ─────────────────────────────────────────────

def build_caption(content: Dict[str, Any], caption_style: Optional[str] = None) -> str:
    """
    Generate social media caption using the caption engine.
    Ensures non-repetitive captions across cycles.
    """
    caption = generate_caption(content, style=caption_style)

    # If this caption was already generated recently, rotate style for fresh phrasing
    if is_duplicate_caption(caption):
        log("🔄 Similar caption detected recently; rotating style for variation...")
        alt_styles = ["short", "reflective", "educational", "reminder"]
        caption = generate_caption(content, style=random.choice(alt_styles))

    log("✍️  Caption generated.")
    return caption

# ─────────────────────────────────────────────
# STAGE 3: MEDIA GENERATION
# ─────────────────────────────────────────────

def generate_media(
    dua: Dict[str, Any],
    caption: str,
    theme: Optional[str] = None,
    layout: Optional[str] = None,
    preset: Optional[str] = None,
    duration: Optional[int] = None,
    script_style: Optional[str] = None,
    enable_audio: bool = True,
) -> Dict[str, Any]:
    """
    Generate the high-definition vertical video and preview image.
    Integrates theme resolution, script generation, and SQLite tracking.
    """
    # 1. Resolve theme and layout via AI/Category recommendations if not specified
    cat_key = dua.get("category", "daily_duas")
    cat_meta = resolve_category(cat_key) or {}

    suggested_theme, suggested_layout = ai_engine.suggest_theme_and_layout(dua)
    theme_name = theme or cat_meta.get("default_theme") or suggested_theme or config.DEFAULT_THEME
    layout_name = layout or cat_meta.get("default_layout") or suggested_layout or config.DEFAULT_LAYOUT
    preset_name = preset or config.DEFAULT_PRESET
    video_dur = duration or config.VIDEO_DURATION

    # 2. Build structured video script
    script = generate_script(dua, style=script_style)
    log(f"📜 Generated Script: Style='{script['style']}', Hook='{script['hook'][:40]}...'")

    # 3. Audio Selection & Attribution — fail closed, never produce silent publishing media.
    if not enable_audio:
        raise RuntimeError("Audio is mandatory for NoorPost publishing; silent video generation is disabled.")

    try:
        audio_info = nasheed_engine.prepare_audio_for_video(dua, float(video_dur))
    except Exception as exc:
        log(f"Required audio preparation failed; publishing is blocked: {exc}", level="ERROR")
        raise

    if not audio_info or not audio_info.get("audio_path"):
        raise RuntimeError("The audio engine returned no playable track; publishing is blocked.")

    if audio_info.get("is_quran_recitation"):
        # Record and render long enough for the complete original ayah recitation.
        video_dur = max(float(video_dur), float(audio_info.get("duration", 0.0)))

    if audio_info.get("attribution"):
        if audio_info["attribution"] not in caption:
            caption += f"\n\n🎵 {audio_info['attribution']}"

    # 4. Render video
    video_path, preview_path = generate_video(
        content=dua,
        theme=theme_name,
        layout=layout_name,
        preset=preset_name,
        duration=video_dur,
        enable_audio=enable_audio,
        audio_info=audio_info,
    )

    # 4. Record in database
    video_id = record_video(
        dua_id=dua["id"],
        video_path=video_path,
        preview_path=preview_path,
        caption=caption,
        theme=theme_name,
        font=getattr(config, "FONT_MODE", "amiri"),
        duration=video_dur,
        layout=layout_name,
        preset=preset_name,
        category=cat_key,
    )

    return {
        "video_id": video_id,
        "video_path": video_path,
        "preview_path": preview_path,
        "theme": theme_name,
        "layout": layout_name,
        "preset": preset_name,
        "category": cat_key,
        "script": script,
    }

# ─────────────────────────────────────────────
# STAGE 4: PUBLISHING DISPATCH
# ─────────────────────────────────────────────

def publish_media(video_id: int, video_path: str, caption: str, dua: Dict[str, Any]) -> Dict[str, Any]:
    """
    Publish to configured destinations (Dropbox / Make.com / Instagram & YouTube).
    Updates persistent publication history.
    """
    results = {}

    # 1. Instagram / Dropbox
    log("🚀 Initiating Instagram/Dropbox distribution...")
    try:
        ig_res = post_reel(video_path, caption)
        results["instagram"] = ig_res
        record_publication(
            video_id=video_id,
            platform="dropbox_make",
            status="success" if ig_res.get("success") else "failed",
            remote_url=ig_res.get("url"),
            remote_id=ig_res.get("remote_id"),
            error_message=ig_res.get("error")
        )
    except Exception as e:
        log(f"❌ Instagram distribution exception: {e}", level="ERROR")
        results["instagram"] = {"success": False, "error": str(e)}
        record_publication(
            video_id=video_id,
            platform="dropbox_make",
            status="failed",
            error_message=str(e)
        )

    # 2. YouTube Shorts (optional)
    log("🚀 Initiating YouTube distribution...")
    try:
        yt_res = upload_short(video_path, dua, caption)
        results["youtube"] = yt_res
        record_publication(
            video_id=video_id,
            platform="youtube",
            status=yt_res.get("status", "success" if yt_res.get("success") else "failed"),
            remote_url=yt_res.get("url"),
            remote_id=yt_res.get("remote_id"),
            error_message=yt_res.get("error")
        )
    except Exception as e:
        log(f"❌ YouTube distribution exception: {e}", level="ERROR")
        results["youtube"] = {"success": False, "error": str(e)}
        record_publication(
            video_id=video_id,
            platform="youtube",
            status="failed",
            error_message=str(e)
        )

    # Determine final video status
    any_success = any(r.get("success") for r in results.values() if isinstance(r, dict))
    final_status = "published" if any_success else "failed"
    update_video_status(video_id, final_status)

    return results

# ─────────────────────────────────────────────
# MASTER PIPELINE ORCHESTRATOR
# ─────────────────────────────────────────────

def run_pipeline(
    job_id: Optional[str] = None,
    category: Optional[str] = None,
    categories_list: Optional[List[str]] = None,
    caption_style: Optional[str] = None,
    script_style: Optional[str] = None,
    theme: Optional[str] = None,
    layout: Optional[str] = None,
    preset: Optional[str] = None,
    duration: Optional[int] = None,
    force_sahih_hadith: bool = False,
    enable_audio: bool = True,
) -> Dict[str, Any]:
    """
    Full automated cycle:
    1. Select verified authentic content (persistent SQLite tracking & category rotation)
    2. Build formatted caption
    3. Render high-res 1080x1920 video and preview
    4. Review checkpoint (if REQUIRE_APPROVAL is enabled)
    5. Publish to Dropbox / Make.com and YouTube Shorts
    """
    run_id = None
    if job_id:
        run_id = start_scheduler_run(job_id)

    log("=" * 60)
    log(f"🚀 NoorPost Pipeline started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("=" * 60)

    try:
        # Step 1: Content Selection
        dua = select_content(category=category, categories_list=categories_list, force_sahih_hadith=force_sahih_hadith)

        # Step 2: Caption
        caption = build_caption(dua, caption_style=caption_style)

        # Step 3: Media Generation
        media = generate_media(
            dua=dua,
            caption=caption,
            theme=theme,
            layout=layout,
            preset=preset,
            duration=duration,
            script_style=script_style,
            enable_audio=enable_audio,
        )
        video_id = media["video_id"]
        video_path = media["video_path"]
        preview_path = media["preview_path"]

        # Step 4: Approval / Preview Checkpoint
        if config.REQUIRE_APPROVAL:
            log(f"⏸️  REQUIRE_APPROVAL is enabled. Video saved at: {video_path}")
            log(f"🖼️  Review preview image at: {preview_path}")
            log("   Set REQUIRE_APPROVAL=False in .env to enable direct publishing.")
            if run_id:
                finish_scheduler_run(run_id, status="pending_approval", video_id=video_id)
            return {"status": "pending_approval", "video_id": video_id, "preview_path": preview_path, "video_path": video_path}

        if config.PREVIEW_ONLY:
            log(f"ℹ️  PREVIEW_ONLY mode active. Generated: {preview_path}")
            if run_id:
                finish_scheduler_run(run_id, status="preview_only", video_id=video_id)
            return {"status": "preview_only", "video_id": video_id, "preview_path": preview_path, "video_path": video_path}

        # Step 5: Publishing
        pub_results = publish_media(video_id, video_path, caption, dua)

        # Summary
        ig_status = "SUCCESS" if pub_results.get("instagram", {}).get("success") else pub_results.get("instagram", {}).get("error", "FAILED")
        yt_status = "SUCCESS" if pub_results.get("youtube", {}).get("success") else pub_results.get("youtube", {}).get("error", "SKIPPED")

        log("=" * 60)
        log(f"✅ Dropbox / Instagram: {ig_status}")
        log(f"✅ YouTube Shorts:       {yt_status}")
        log("🌟 Cycle complete — بارك الله فيك")
        log("=" * 60)

        if run_id:
            finish_scheduler_run(run_id, status="completed", video_id=video_id)

        return {
            "status": "completed",
            "video_id": video_id,
            "video_path": video_path,
            "preview_path": preview_path,
            "publishing": pub_results
        }

    except Exception as e:
        log(f"❌ Pipeline failed: {e}", level="ERROR")
        if run_id:
            finish_scheduler_run(run_id, status="failed", error_message=str(e))
        raise

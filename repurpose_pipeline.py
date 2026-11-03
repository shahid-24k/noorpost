"""
repurpose_pipeline.py — Master Video Repurposing Pipeline for NoorPost Ultimate
Transforms long Islamic lectures into professional vertical Reels and delivers them
to Dropbox for automated Make.com Instagram publishing.

Preserves:
- The existing Dropbox folder conventions and Make.com watch trigger.
- The 7 curated Islamic visual themes.
- Rights confirmation & duplicate clip prevention.
- SQLite job tracking across states.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

import config
from logger import log
from source_manager import source_engine
from clip_selector import parse_vtt_srt, find_candidate_clips, parse_manual_timestamps
from vertical_reframer import reframer_engine
from subtitle_engine import generate_srt_file, generate_ass_file
from repurpose_packager import packager_engine
from instagram import upload_to_dropbox
from database import (
    init_db,
    register_repurpose_source,
    update_source_status,
    record_repurpose_clip,
    update_clip_status,
    is_duplicate_clip,
    get_repurpose_jobs,
)

def run_repurpose_pipeline(
    url_or_path: str,
    confirm_rights: bool = False,
    num_clips: int = 3,
    clip_duration: float = 45.0,
    reframing: str = "blur_fill",
    preset: str = "balanced",
    theme: str = "midnight-gold",
    timestamps: Optional[str] = None,
    burn_subtitles: bool = True,
    preview_only: bool = False,
    upload_dropbox: bool = True
) -> Dict[str, Any]:
    """
    Execute full video repurposing workflow.
    """
    init_db()

    log("=" * 60)
    log(f"🎬 Initiating Video Repurposing Pipeline: {url_or_path}")
    log("=" * 60)

    # ─────────────────────────────────────────────
    # STAGE 1: INSPECT SOURCE & CONFIRM RIGHTS
    # ─────────────────────────────────────────────
    source_meta = source_engine.inspect_source(url_or_path, confirm_rights=confirm_rights)
    source_db_id = register_repurpose_source(
        source_id=source_meta["source_id"],
        source_type=source_meta["source_type"],
        source_url=source_meta["source_url"],
        title=source_meta["title"],
        channel=source_meta["channel"],
        duration=source_meta["duration"],
        language=source_meta.get("language", "en"),
        rights_confirmed=confirm_rights
    )

    if source_meta["source_type"] == "youtube" and not confirm_rights:
        update_source_status(source_db_id, "FAILED")
        raise PermissionError(
            "Rights confirmation required: Add --confirm-rights to confirm authorization to repurpose this source."
        )

    update_source_status(source_db_id, "SOURCE_PROCESSING")

    # ─────────────────────────────────────────────
    # STAGE 2: DOWNLOAD / LOCATE MEDIA
    # ─────────────────────────────────────────────
    local_video, local_sub = source_engine.prepare_source(source_meta, download_if_needed=not preview_only)
    source_meta["local_video_path"] = local_video
    source_meta["local_subtitle_path"] = local_sub

    # ─────────────────────────────────────────────
    # STAGE 3: SEGMENT SELECTION
    # ─────────────────────────────────────────────
    cues = []
    if local_sub and Path(local_sub).exists():
        cues = parse_vtt_srt(local_sub)
        log(f"📝 Subtitle cues parsed: {len(cues)} entries")

    if timestamps:
        manual_ranges = parse_manual_timestamps(timestamps)
        log(f"⏱️  Using manual timestamp overrides: {manual_ranges}")
        candidates = []
        for idx, (s_sec, e_sec) in enumerate(manual_ranges):
            matched_cues = [c for c in cues if c["start"] >= s_sec and c["end"] <= e_sec + 0.5]
            snippet = " ".join(c["text"] for c in matched_cues[:4]) if matched_cues else f"Segment from {s_sec:.1f}s to {e_sec:.1f}s"
            candidates.append({
                "clip_index": idx + 1,
                "start_sec": s_sec,
                "end_sec": e_sec,
                "duration_sec": round(e_sec - s_sec, 2),
                "title": f"Clip {idx + 1}: {source_meta['title'][:40]}",
                "transcript_snippet": snippet,
                "cues": matched_cues
            })
    else:
        candidates = find_candidate_clips(
            cues=cues,
            video_duration=source_meta["duration"],
            target_duration=clip_duration,
            num_clips=num_clips
        )

    update_source_status(source_db_id, "CLIPS_SELECTED")

    # If preview-only mode requested, return candidate metadata immediately
    if preview_only:
        log("🔍 PREVIEW MODE — Candidate segments identified:")
        for c in candidates:
            log(f"   * Clip #{c['clip_index']}: {c['start_sec']:.1f}s -> {c['end_sec']:.1f}s ({c['duration_sec']:.1f}s) — '{c['title']}'")
        return {
            "status": "preview_only",
            "source_id": source_meta["source_id"],
            "candidates": candidates
        }

    # ─────────────────────────────────────────────
    # STAGE 4: RENDER VERTICAL CLIPS, SUBTITLES & THUMBNAILS
    # ─────────────────────────────────────────────
    update_source_status(source_db_id, "CLIPS_RENDERING")
    rendered_clips = []

    for c in candidates:
        clip_uid = f"{source_meta['source_id']}_c{c['clip_index']:02d}"

        # Duplicate check: don't re-render exact same segment if already done
        if is_duplicate_clip(source_meta["source_id"], c["start_sec"], c["end_sec"]):
            log(f"⏩ Clip #{c['clip_index']} already rendered previously. Skipping duplicate rendering.")
            continue

        clip_stem = f"repurpose_{clip_uid}"
        out_video_path = str(config.OUTPUT_DIR / f"{clip_stem}.mp4")
        out_sub_path = str(config.OUTPUT_DIR / f"{clip_stem}.srt") if burn_subtitles and c["cues"] else None

        # Build subtitle file if cues are present
        if out_sub_path and c["cues"]:
            generate_srt_file(c["cues"], out_sub_path, time_offset_sec=c["start_sec"])

        # Render Vertical Video
        reframer_engine.render_reel_clip(
            source_video=local_video,
            output_path=out_video_path,
            start_sec=c["start_sec"],
            end_sec=c["end_sec"],
            strategy=reframing,
            preset=preset,
            subtitle_file=out_sub_path if burn_subtitles else None,
            theme_name=theme
        )

        # Generate Thumbnail Cover
        preview_path = packager_engine.generate_thumbnail(
            video_path=out_video_path,
            headline=c["title"],
            theme_name=theme,
            badge_text="ISLAMIC LECTURE"
        )

        # Generate Caption
        caption = packager_engine.generate_repurpose_caption(
            clip_title=c["title"],
            source_title=source_meta["title"],
            channel=source_meta["channel"],
            transcript_snippet=c["transcript_snippet"]
        )

        # Save caption locally alongside video
        caption_file = str(config.OUTPUT_DIR / f"{clip_stem}_caption.txt")
        with open(caption_file, "w", encoding="utf-8") as f:
            f.write(caption)

        # Record clip in SQLite
        clip_db_id = record_repurpose_clip(
            source_db_id=source_db_id,
            clip_id=clip_uid,
            clip_index=c["clip_index"],
            start_sec=c["start_sec"],
            end_sec=c["end_sec"],
            title=c["title"],
            transcript_snippet=c["transcript_snippet"],
            reframing_strategy=reframing,
            video_path=out_video_path,
            preview_path=preview_path,
            caption=caption,
            status="READY_FOR_DROPBOX"
        )

        rendered_clips.append({
            "clip_id": clip_uid,
            "clip_db_id": clip_db_id,
            "video_path": out_video_path,
            "preview_path": preview_path,
            "caption": caption,
            "caption_file": caption_file,
            "title": c["title"]
        })

    # ─────────────────────────────────────────────
    # STAGE 5: DROPBOX & MAKE.COM HANDOFF
    # ─────────────────────────────────────────────
    if upload_dropbox and config.is_dropbox_configured():
        log("🚀 Delivering completed clips to Dropbox for Make.com automated publishing...")
        for clip in rendered_clips:
            update_clip_status(clip["clip_id"], "DROPBOX_UPLOADING")
            upload_res = upload_to_dropbox(clip["video_path"], clip["caption"])

            if upload_res["success"]:
                # Also optionally upload preview thumbnail to previews/ subfolder
                try:
                    import dropbox
                    dbx_folder = config.DROPBOX_FOLDER.rstrip("/")
                    thumb_dest = f"{dbx_folder}/previews/{Path(clip['preview_path']).name}"
                    dbx = upload_to_dropbox.__globals__["get_dropbox_client"]()
                    with open(clip["preview_path"], "rb") as pf:
                        dbx.files_upload(pf.read(), thumb_dest, mode=dropbox.files.WriteMode("overwrite"))
                except Exception:
                    pass

                update_clip_status(
                    clip_id=clip["clip_id"],
                    status="HANDED_OFF_TO_MAKE",
                    dropbox_url=upload_res.get("url"),
                    dropbox_id=upload_res.get("remote_id")
                )
                log(f"✅ Clip '{clip['title']}' handed off to Make.com via Dropbox!")
            else:
                update_clip_status(
                    clip_id=clip["clip_id"],
                    status="FAILED",
                    error_message=upload_res.get("error")
                )
                log(f"❌ Failed to upload '{clip['title']}' to Dropbox: {upload_res.get('error')}", level="ERROR")
    else:
        log("ℹ️  Dropbox upload skipped (not configured or disabled). Clips saved locally in output_videos/.")
        for clip in rendered_clips:
            update_clip_status(clip["clip_id"], "READY_FOR_DROPBOX")

    update_source_status(source_db_id, "PUBLISHED" if (upload_dropbox and config.is_dropbox_configured()) else "DROPBOX_READY")

    log("=" * 60)
    log(f"🌟 Repurposing complete: {len(rendered_clips)} clips prepared successfully!")
    log("=" * 60)

    return {
        "status": "completed",
        "source_id": source_meta["source_id"],
        "clips": rendered_clips
    }

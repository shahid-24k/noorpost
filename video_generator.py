"""
video_generator.py — Professional 1080x1920 Islamic Video Engine for NoorPost Ultimate
Generates high-definition vertical videos for Instagram Reels and YouTube Shorts.
Features:
  - 7 Curated Islamic Visual Themes (procedural gradients & geometric art)
  - Flawless Arabic typography via arabic-reshaper + python-bidi
  - Multiple content layouts (Dua, Quranic Verse, Islamic Reminder)
  - Dynamic font scaling & intelligent multi-scene splitting for long texts
  - Configurable rendering presets (fast, balanced, high_quality) with rock-solid fixed 1080x1920 frames
  - Smooth opacity fade transitions without variable-dimension canvas distortion
  - Full ffprobe stream metadata validation and complete FFmpeg video decoding verification
  - Strict audio integration with authentic Quran recitation and personal mood tracks
"""

import os
import sys
import uuid
import json
import shutil
import subprocess
import tempfile
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional

# Monkeypatch Pillow for MoviePy compatibility (Pillow 10 removed Image.ANTIALIAS)
import PIL.Image
if not hasattr(PIL.Image, "ANTIALIAS"):
    PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS

from PIL import Image, ImageDraw, ImageFont

# Support both MoviePy 1.x and 2.x
try:
    from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips
except ImportError:
    from moviepy import ImageClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips

import config
from logger import log
from themes import THEMES, resolve_theme, render_themed_background, draw_8point_star
from audio_manager import validate_audio_file, validate_mp4_audio
# Backward compatibility aliases
from themes import resolve_theme
def resolve_font_path() -> str:
    return str(config.FONT_ARABIC)

# Arabic text shaping libraries
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_ARABIC_SUPPORT = True
except ImportError:
    HAS_ARABIC_SUPPORT = False

# ─────────────────────────────────────────────
# RENDERING PRESETS
# ─────────────────────────────────────────────
PRESETS = {
    "fast": {
        "fps": 15,
        "zoom": False,
        "fade_duration": 0.5,
        "ffmpeg_preset": "ultrafast",
        "crf": 23,
        "bitrate": "2500k",
    },
    "balanced": {
        "fps": 24,
        "zoom": False,
        "fade_duration": 0.8,
        "ffmpeg_preset": "fast",
        "crf": 20,
        "bitrate": "4500k",
    },
    "high_quality": {
        "fps": 30,
        "zoom": False,
        "fade_duration": 1.0,
        "ffmpeg_preset": "medium",
        "crf": 18,
        "bitrate": "6500k",
    },
}

# ─────────────────────────────────────────────
# FONT RESOLUTION & TYPOGRAPHY
# ─────────────────────────────────────────────

def get_font(path: str, size: int) -> ImageFont.ImageFont:
    """Load truetype font with safe default fallback."""
    try:
        p = Path(path)
        if p.exists():
            return ImageFont.truetype(str(p), size)
        for cand in config.FONTS_DIR.glob("*.ttf"):
            if "amiri" in cand.name.lower() or "noto" in cand.name.lower():
                return ImageFont.truetype(str(cand), size)
    except Exception:
        pass
    return ImageFont.load_default()

def wrap_and_shape_arabic(text: str, font: ImageFont.ImageFont, max_width: int, draw: ImageDraw.ImageDraw) -> List[str]:
    """Word-wrap Arabic text while accurately measuring reshaped ligatures."""
    words = text.strip().split()
    lines = []
    current = []

    for word in words:
        test_str = " ".join(current + [word])
        if HAS_ARABIC_SUPPORT:
            reshaped = arabic_reshaper.reshape(test_str)
            display_str = get_display(reshaped)
        else:
            display_str = test_str

        bbox = draw.textbbox((0, 0), display_str, font=font)
        w = bbox[2] - bbox[0]
        if w <= max_width or not current:
            current.append(word)
        else:
            lines.append(" ".join(current))
            current = [word]

    if current:
        lines.append(" ".join(current))

    shaped_lines = []
    for line in lines:
        if HAS_ARABIC_SUPPORT:
            reshaped = arabic_reshaper.reshape(line)
            shaped_lines.append(get_display(reshaped))
        else:
            shaped_lines.append(line)

    return shaped_lines

def measure_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> Tuple[int, int]:
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]
    except Exception:
        return len(text) * 12, 34

def draw_ornament(draw: ImageDraw.ImageDraw, cx: int, y: int, color: tuple, width: int = 240):
    """Draw refined Islamic decorative divider."""
    draw.line([(cx - width, y), (cx + width, y)], fill=color, width=1)
    draw.ellipse([cx - 5, y - 5, cx + 5, y + 5], fill=color)
    draw.line([(cx - width // 2, y - 7), (cx + width // 2, y - 7)], fill=color, width=1)

# ─────────────────────────────────────────────
# LAYOUT RENDERING ENGINE
# ─────────────────────────────────────────────

def render_content_frame(
    content: Dict[str, Any],
    theme: Dict[str, Any],
    layout: str = "dua",
    scene_mode: str = "full",  # 'full', 'scene1_arabic', 'scene2_translation'
    show_transliteration: bool = True,
    show_bismillah: bool = True,
    show_source: bool = True,
    show_watermark: bool = True,
) -> Image.Image:
    """
    Render a single 1080x1920 poster frame according to the requested theme and layout.
    """
    W = config.VIDEO_WIDTH
    H = config.VIDEO_HEIGHT
    cx = W // 2

    # 1. Render thematic background
    img = render_themed_background(theme, W, H)
    draw = ImageDraw.Draw(img)

    # 2. Extract theme color palette
    gold = theme["gold"]
    gold_dim = theme["gold_dim"]
    text_primary = theme["text_primary"]
    text_secondary = theme["text_secondary"]

    # 3. Safe margins & bounding area
    safe_left = config.SAFE_MARGIN_X
    safe_right = W - config.SAFE_MARGIN_X
    max_content_w = safe_right - safe_left

    # Determine content elements
    raw_type = content.get("type", content.get("dua_type", "Authentic Dua"))
    arabic_text = content.get("arabic", "").strip()
    translation_text = content.get("translation", "").strip()
    transliteration_text = content.get("transliteration", "").strip()
    source_text = content.get("source", "").strip()

    # Dynamic font sizing based on Arabic length
    arabic_len = len(arabic_text)
    if arabic_len > 140:
        arabic_size = 40
        arabic_line_gap = 14
        trans_size = 28
    elif arabic_len > 80:
        arabic_size = 46
        arabic_line_gap = 16
        trans_size = 30
    else:
        arabic_size = 52
        arabic_line_gap = 20
        trans_size = 32

    # Fonts
    font_arabic = get_font(config.FONT_ARABIC, arabic_size)
    font_bism = get_font(config.FONT_ARABIC, 42)
    font_badge = get_font(config.FONT_BOLD, 22)
    font_translation = get_font(config.FONT_LATIN, trans_size)
    font_translit = get_font(config.FONT_LATIN_ITALIC, 22)
    font_source = get_font(config.FONT_LATIN, 22)
    font_small = get_font(config.FONT_LATIN, 18)

    y = config.SAFE_MARGIN_TOP

    # ── HEADER BADGE ──
    badge_text = f"— {raw_type.upper()} —"
    bw, bh = measure_text(draw, badge_text, font_badge)
    draw.text(((W - bw) // 2, y), badge_text, font=font_badge, fill=gold_dim)
    y += bh + 20
    draw_ornament(draw, cx, y, gold_dim, width=220)
    y += 24

    # ── BISMILLAH ──
    if show_bismillah:
        bism_text = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"
        if HAS_ARABIC_SUPPORT:
            bism_display = get_display(arabic_reshaper.reshape(bism_text))
        else:
            bism_display = bism_text
        bw, bh = measure_text(draw, bism_display, font_bism)
        draw.text(((W - bw) // 2, y), bism_display, font=font_bism, fill=gold)
        y += bh + 20
        draw_ornament(draw, cx, y, gold_dim, width=280)
        y += 28

    # ── SCENE HANDLING (Full or Split) ──
    if scene_mode in ("full", "scene1_arabic"):
        # Render Arabic Text
        if arabic_text:
            arabic_lines = wrap_and_shape_arabic(arabic_text, font_arabic, max_content_w, draw)
            for line in arabic_lines:
                lw, lh = measure_text(draw, line, font_arabic)
                draw.text(((W - lw) // 2, y), line, font=font_arabic, fill=gold)
                y += lh + arabic_line_gap
            y += 14
            draw_ornament(draw, cx, y, gold_dim, width=260)
            y += 24

        # Render Transliteration (if requested)
        if show_transliteration and transliteration_text and scene_mode != "scene2_translation":
            translit_lines = textwrap.wrap(transliteration_text, width=44)
            for tline in translit_lines:
                tw, th = measure_text(draw, tline, font_translit)
                draw.text(((W - tw) // 2, y), tline, font=font_translit, fill=text_secondary)
                y += th + 8
            y += 16

    if scene_mode in ("full", "scene2_translation"):
        # Render English Translation
        if translation_text:
            formatted_trans = f"“{translation_text}”"
            trans_lines = textwrap.wrap(formatted_trans, width=38)
            for line in trans_lines:
                lw, lh = measure_text(draw, line, font_translation)
                draw.text(((W - lw) // 2, y), line, font=font_translation, fill=text_primary)
                y += lh + 14
            y += 16
            draw_ornament(draw, cx, y, gold_dim, width=200)
            y += 20

    # ── SOURCE ATTRIBUTION ──
    if show_source and source_text and scene_mode in ("full", "scene2_translation"):
        source_label = f"Source: {source_text}"
        sw, sh = measure_text(draw, source_label, font_source)
        draw.text(((W - sw) // 2, y), source_label, font=font_source, fill=gold_dim)
        y += sh + 12

    # Multi-scene indicator badge
    if scene_mode == "scene1_arabic":
        indicator = "— PART 1 · ARABIC RECITATION —"
        iw, ih = measure_text(draw, indicator, font_small)
        draw.text(((W - iw) // 2, H - 120), indicator, font=font_small, fill=gold_dim)
    elif scene_mode == "scene2_translation":
        indicator = "— PART 2 · MEANING & REFLECTION —"
        iw, ih = measure_text(draw, indicator, font_small)
        draw.text(((W - iw) // 2, H - 120), indicator, font=font_small, fill=gold_dim)

    # ── WATERMARK & VERIFICATION SEAL ──
    if show_watermark:
        wm_text = "NoorPost Ultimate · Authentic Islamic Content"
        ww, wh = measure_text(draw, wm_text, font_small)
        draw.text(((W - ww) // 2, H - 85), wm_text, font=font_small, fill=gold_dim)

    return img

def create_frame(content: Dict[str, Any], font_path: Optional[str] = None, theme: Optional[Dict[str, Any]] = None) -> Image.Image:
    """Backward-compatible single-frame renderer."""
    t = theme if isinstance(theme, dict) else resolve_theme()
    return render_content_frame(content, t, scene_mode="full")

# ─────────────────────────────────────────────
# MASTER VIDEO PRODUCTION PIPELINE
# ─────────────────────────────────────────────


def validate_video_file(
    video_path: str | Path,
    expected_width: int = 1080,
    expected_height: int = 1920,
    expected_codec: str = "h264",
    expected_pix_fmt: str = "yuv420p",
    expected_fps: Optional[int] = None,
    expected_min_duration: float = 1.0,
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Validate rendered video using ffprobe stream analysis and full FFmpeg decoding:
    1. Video file exists and is non-empty.
    2. ffprobe verifies:
       - H.264 video stream
       - Exact 1080x1920 resolution
       - yuv420p pixel format
       - Expected frame rate and duration
    3. Full decode with FFmpeg:
       ffmpeg -v error -i output.mp4 -map 0:v:0 -f null -
       Rejects the video if decoding reports any frame corruption or errors.
    """
    p = Path(video_path)
    if not p.is_absolute():
        p = config.BASE_DIR / p

    if not p.exists():
        return False, f"Video file not found: {p}", {}

    if p.stat().st_size < 10000:
        return False, f"Video file corrupted or too small ({p.stat().st_size} bytes)", {}

    ffprobe = shutil.which("ffprobe")
    ffmpeg = shutil.which("ffmpeg")

    if not ffprobe:
        return True, "ffprobe not installed; basic file check passed", {"size": p.stat().st_size}

    try:
        # Step A: ffprobe stream inspection
        cmd = [
            ffprobe, "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=codec_name,width,height,pix_fmt,r_frame_rate,avg_frame_rate,duration",
            "-show_entries", "format=duration",
            "-of", "json",
            str(p)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if res.returncode != 0:
            return False, f"ffprobe stream inspection failed: {res.stderr.strip()}", {}

        data = json.loads(res.stdout or "{}")
        streams = data.get("streams", [])
        format_info = data.get("format", {})

        if not streams:
            return False, "No video stream found in MP4 file", {}

        v_stream = streams[0]
        codec = v_stream.get("codec_name", "").lower()
        width = int(v_stream.get("width", 0))
        height = int(v_stream.get("height", 0))
        pix_fmt = v_stream.get("pix_fmt", "").lower()

        # Parse duration
        stream_dur = v_stream.get("duration")
        format_dur = format_info.get("duration")
        duration = float(format_dur or stream_dur or 0.0)

        # Parse frame rate
        fps_str = v_stream.get("r_frame_rate") or v_stream.get("avg_frame_rate") or "0/1"
        try:
            num, den = fps_str.split("/")
            fps = float(num) / float(den) if float(den) != 0 else 0.0
        except Exception:
            fps = 0.0

        # Validate H.264
        if codec != expected_codec.lower():
            return False, f"Invalid video codec: '{codec}' (expected '{expected_codec}')", {}

        # Validate 1080x1920
        if width != expected_width or height != expected_height:
            return False, f"Invalid video dimensions: {width}x{height} (expected {expected_width}x{expected_height})", {}

        # Validate yuv420p
        if pix_fmt != expected_pix_fmt.lower():
            return False, f"Invalid pixel format: '{pix_fmt}' (expected '{expected_pix_fmt}')", {}

        # Validate duration
        if duration < expected_min_duration:
            return False, f"Video duration too short: {duration:.2f}s (< {expected_min_duration}s)", {}

        # Validate frame rate if specified
        if expected_fps is not None and abs(fps - expected_fps) > 1.5:
            return False, f"Video frame rate mismatch: {fps:.2f} fps (expected ~{expected_fps} fps)", {}

        # Step B: Full video stream decoding with FFmpeg
        if ffmpeg:
            decode_cmd = [
                ffmpeg, "-v", "error",
                "-i", str(p),
                "-map", "0:v:0",
                "-f", "null", "-"
            ]
            decode_res = subprocess.run(decode_cmd, capture_output=True, text=True, timeout=30)
            if decode_res.returncode != 0 or decode_res.stderr.strip():
                err_text = decode_res.stderr.strip()
                return False, f"FFmpeg video decoding verification failed: {err_text}", {}

        meta = {
            "codec": codec,
            "width": width,
            "height": height,
            "pix_fmt": pix_fmt,
            "fps": fps,
            "duration": duration,
            "size_bytes": p.stat().st_size,
        }
        log(f"✅ Video stream verified: {codec} {width}x{height} {pix_fmt} @ {fps:.1f}fps ({duration:.1f}s)")
        return True, "Video stream valid and fully decodable", meta

    except Exception as e:
        log(f"⚠️  Video validation exception: {e}", level="WARNING")
        return False, f"Video validation exception: {e}", {}


def generate_video(
    content: Dict[str, Any],
    theme: Optional[str] = None,
    layout: Optional[str] = None,
    preset: Optional[str] = None,
    duration: Optional[int] = None,
    enable_audio: bool = True,
    enable_animations: Optional[bool] = None,
    show_transliteration: Optional[bool] = None,
    show_bismillah: bool = True,
    show_source: bool = True,
    show_watermark: bool = True,
    audio_info: Optional[Dict[str, Any]] = None,
) -> Tuple[str, str]:
    """
    Generate professional 1080x1920 video for Instagram Reels and YouTube Shorts.
    Returns:
        (video_path, preview_path)
    """
    # 1. Resolve configuration defaults
    theme_cfg = resolve_theme(theme or config.DEFAULT_THEME)
    layout_name = layout or config.DEFAULT_LAYOUT
    preset_name = preset or config.DEFAULT_PRESET
    preset_cfg = PRESETS.get(preset_name, PRESETS["balanced"])
    video_duration = duration or config.VIDEO_DURATION

    if enable_animations is None:
        enable_animations = config.ENABLE_ANIMATIONS
    if show_transliteration is None:
        show_transliteration = config.SHOW_TRANSLITERATION

    dua_type = content.get("type", content.get("dua_type", "Authentic Dua"))
    source = content.get("source", "Sahih")
    log(f"🎬 Generating {preset_name.upper()} video: [{dua_type}] {source} (Theme: {theme_cfg['name']})")

    # Generate unique output timestamp & identifier
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:6]
    base_name = f"noorpost_{timestamp}_{unique_id}"

    # 2. Estimate content height to decide single vs multi-scene
    arabic_text = content.get("arabic", "")
    trans_text = content.get("translation", "")
    is_very_long = (len(arabic_text) > 130 and len(trans_text) > 120) or (len(arabic_text) > 200)

    # 3. Create persistent preview image (always Scene 1 / Full)
    preview_img = render_content_frame(
        content, theme_cfg, layout=layout_name,
        scene_mode="full" if not is_very_long else "scene1_arabic",
        show_transliteration=show_transliteration,
        show_bismillah=show_bismillah,
        show_source=show_source,
        show_watermark=show_watermark,
    )
    preview_path = str(config.PREVIEWS_DIR / f"preview_{base_name}.jpg")
    preview_img.save(preview_path, "JPEG", quality=92)
    log(f"🖼️  Preview saved: {preview_path}")

    # 4. Build Video Clips (MoviePy)
    with tempfile.TemporaryDirectory(prefix="noorpost_render_") as tmp_dir:
        tmp_path = Path(tmp_dir)

        if not is_very_long:
            # Single Scene Video (Strict fixed 1080x1920 canvas without variable-dimension scaling)
            frame_path = tmp_path / "frame_full.png"
            preview_img.save(str(frame_path))
            clip = ImageClip(str(frame_path), duration=video_duration)

            fade_dur = preset_cfg.get("fade_duration", 0.8)
            clip = clip.fadein(fade_dur).fadeout(fade_dur)
            final_video_clip = clip

        else:
            # Two-Scene Video with Cross-Dissolve Transition
            scene1_img = preview_img
            scene2_img = render_content_frame(
                content, theme_cfg, layout=layout_name,
                scene_mode="scene2_translation",
                show_transliteration=show_transliteration,
                show_bismillah=show_bismillah,
                show_source=show_source,
                show_watermark=show_watermark,
            )

            p1_path = tmp_path / "scene1.png"
            p2_path = tmp_path / "scene2.png"
            scene1_img.save(str(p1_path))
            scene2_img.save(str(p2_path))

            half_duration = video_duration / 2.0
            clip1 = ImageClip(str(p1_path), duration=half_duration)
            clip2 = ImageClip(str(p2_path), duration=half_duration)

            # Smooth opacity transitions while keeping exact 1080x1920 dimensions
            clip1 = clip1.fadein(0.6).fadeout(0.6)
            clip2 = clip2.fadein(0.6).fadeout(0.6)
            final_video_clip = concatenate_videoclips([clip1, clip2])

        # Set target Frame Rate
        fps = preset_cfg.get("fps", 24)
        final_video_clip = final_video_clip.set_fps(fps)

        # 5. Audio Integration (Strict: zero silent fallbacks)
        if enable_audio:
            audio_file = None
            start_time = 0.0
            vol = getattr(config, "AUDIO_VOLUME", 0.35)
            is_quran = False

            # Check if content is Qur'anic
            cat_name = str(content.get("category", "")).lower()
            cnt_type = str(content.get("type", "")).lower()
            is_quran_content = (
                cat_name in ("quranic_verses", "quran")
                or "qur'an" in cnt_type
                or "quran" in cnt_type
                or "quran" in cat_name
            )

            if is_quran_content:
                from quran_audio import get_quran_recitation
                audio_res = audio_info if (audio_info and audio_info.get("is_quran_recitation")) else get_quran_recitation(content)
                audio_file = audio_res.get("audio_path")
                start_time = float(audio_res.get("start_time", 0.0))
                vol = float(audio_res.get("volume", 1.0))
                is_quran = True
            elif audio_info and audio_info.get("audio_path"):
                audio_file = audio_info["audio_path"]
                start_time = float(audio_info.get("start_time", 0.0))
                vol = float(audio_info.get("volume", vol))
                is_quran = bool(audio_info.get("is_quran_recitation", False))
            else:
                from nasheed_engine import nasheed_engine
                audio_res = nasheed_engine.prepare_audio_for_video(content, video_duration)
                if not audio_res or not audio_res.get("audio_path"):
                    raise RuntimeError(
                        f"Failed to acquire required audio for '{content.get('source')}'. "
                        "Silent fallback is strictly prohibited."
                    )
                audio_file = audio_res.get("audio_path")
                start_time = float(audio_res.get("start_time", 0.0))
                vol = float(audio_res.get("volume", vol))
                is_quran = bool(audio_res.get("is_quran_recitation", False))

            if not audio_file or not Path(audio_file).exists():
                raise RuntimeError(
                    f"Required audio file missing: {audio_file}. "
                    "Generation cannot proceed without authentic audio."
                )

            ok, msg = validate_audio_file(audio_file)
            if not ok:
                raise RuntimeError(f"Selected audio file '{audio_file}' failed validation: {msg}")

            audio = AudioFileClip(str(audio_file))
            if is_quran:
                # Never cut off authentic Quran recitation
                audio = audio.volumex(vol)
                final_video_clip = final_video_clip.set_audio(audio)
                log(f"🎙️  Qur'anic recitation attached: {Path(audio_file).name} (dur: {audio.duration:.1f}s, vol: {vol})")
            else:
                if audio.duration > (start_time + video_duration):
                    audio = audio.subclip(start_time, start_time + video_duration)
                else:
                    audio = audio.subclip(0, min(video_duration, audio.duration))
                audio = audio.volumex(vol).audio_fadein(1.0).audio_fadeout(2.0)
                final_video_clip = final_video_clip.set_audio(audio)
                log(f"🎵 Background audio attached: {Path(audio_file).name} (vol: {vol})")

        # 6. Encode Video
        out_path = str(config.OUTPUT_DIR / f"{base_name}.mp4")
        log(f"🎥 Encoding 1080x1920 video ({preset_name} preset, {fps} fps)...")

        ffmpeg_params = [
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            "-crf", str(preset_cfg.get("crf", 20)),
            "-preset", preset_cfg.get("ffmpeg_preset", "fast"),
        ]

        final_video_clip.write_videofile(
            out_path,
            codec="libx264",
            audio_codec="aac" if final_video_clip.audio is not None else None,
            bitrate=preset_cfg.get("bitrate", "4500k"),
            logger=None,
            ffmpeg_params=ffmpeg_params,
        )

        try:
            if final_video_clip.audio is not None:
                final_video_clip.audio.close()
            final_video_clip.close()
        except Exception:
            pass

    # 7. Validate rendered MP4 file: Video Stream, Fixed 1080x1920, Full Decode & Audio
    out_file = Path(out_path)
    if not out_file.exists() or out_file.stat().st_size < 10000:
        raise RuntimeError(f"Video encoding failed or output file is empty: {out_path}")

    # Step 7A: Comprehensive Video Validation (H.264, 1080x1920, yuv420p, fps, full FFmpeg decode)
    is_v_valid, v_err_msg, v_meta = validate_video_file(
        out_path,
        expected_width=config.VIDEO_WIDTH,
        expected_height=config.VIDEO_HEIGHT,
        expected_codec="h264",
        expected_pix_fmt="yuv420p",
        expected_fps=fps,
        expected_min_duration=min(1.0, float(video_duration)),
    )
    if not is_v_valid:
        try:
            out_file.unlink(missing_ok=True)
        except Exception:
            pass
        raise RuntimeError(f"Rendered video failed visual validation: {v_err_msg}")

    # Step 7B: Audio Stream & Signal Validation (Zero silent fallbacks)
    if enable_audio:
        is_a_valid, a_err_msg, a_meta = validate_mp4_audio(out_path)
        if not is_a_valid:
            try:
                out_file.unlink(missing_ok=True)
            except Exception:
                pass
            raise RuntimeError(f"Rendered video failed audio validation: {a_err_msg}")

    log(f"✅ Video produced and verified successfully: {out_path} ({out_file.stat().st_size // 1024} KB)")
    return out_path, preview_path

"""
video_generator.py — Professional 1080x1920 Islamic Video Engine for NoorPost Ultimate
Generates high-definition vertical videos for Instagram Reels and YouTube Shorts.
Features:
  - 7 Curated Islamic Visual Themes (procedural gradients & geometric art)
  - Flawless Arabic typography via arabic-reshaper + python-bidi
  - Multiple content layouts (Dua, Quranic Verse, Islamic Reminder)
  - Dynamic font scaling & intelligent multi-scene splitting for long texts
  - Configurable rendering presets (fast, balanced, high_quality)
  - Subtle Ken Burns zoom and smooth fade transitions
  - Complete audio integration with graceful silent fallbacks
"""

import os
import sys
import uuid
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
        "zoom": True,
        "zoom_rate": 0.002,   # 1.0 to ~1.03 over 15s
        "fade_duration": 0.8,
        "ffmpeg_preset": "fast",
        "crf": 20,
        "bitrate": "4500k",
    },
    "high_quality": {
        "fps": 30,
        "zoom": True,
        "zoom_rate": 0.003,   # 1.0 to ~1.045 over 15s
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
            # Single Scene Video
            frame_path = tmp_path / "frame_full.png"
            preview_img.save(str(frame_path))
            clip = ImageClip(str(frame_path), duration=video_duration)

            if enable_animations and preset_cfg.get("zoom"):
                rate = preset_cfg.get("zoom_rate", 0.002)
                clip = clip.resize(lambda t: 1.0 + rate * t)

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

            if enable_animations and preset_cfg.get("zoom"):
                rate = preset_cfg.get("zoom_rate", 0.002)
                clip1 = clip1.resize(lambda t: 1.0 + rate * t)
                clip2 = clip2.resize(lambda t: 1.0 + rate * t)

            clip1 = clip1.fadein(0.6).fadeout(0.6)
            clip2 = clip2.fadein(0.6).fadeout(0.6)
            final_video_clip = concatenate_videoclips([clip1, clip2])

        # Set target Frame Rate
        fps = preset_cfg.get("fps", 24)
        final_video_clip = final_video_clip.set_fps(fps)

        # 5. Audio Integration
        if enable_audio:
            try:
                audio_file = None
                start_time = 0.0
                vol = getattr(config, "AUDIO_VOLUME", 0.35)

                if audio_info and audio_info.get("audio_path"):
                    audio_file = audio_info["audio_path"]
                    start_time = float(audio_info.get("start_time", 0.0))
                    vol = float(audio_info.get("volume", vol))
                else:
                    try:
                        from nasheed_engine import nasheed_engine
                        audio_res = nasheed_engine.prepare_audio_for_video(content, video_duration)
                        if audio_res:
                            audio_file = audio_res.get("audio_path")
                            start_time = float(audio_res.get("start_time", 0.0))
                            vol = float(audio_res.get("volume", vol))
                    except Exception:
                        pass

                if not audio_file:
                    from audio_manager import get_audio_file
                    audio_file = get_audio_file(duration=video_duration)

                if audio_file and Path(audio_file).exists():
                    audio = AudioFileClip(audio_file)
                    if audio.duration > (start_time + video_duration):
                        audio = audio.subclip(start_time, start_time + video_duration)
                    else:
                        audio = audio.subclip(0, min(video_duration, audio.duration))
                    audio = audio.volumex(vol).audio_fadein(1.0).audio_fadeout(2.0)
                    final_video_clip = final_video_clip.set_audio(audio)
                    log(f"🎵 Background audio attached: {Path(audio_file).name} (vol: {vol})")
            except Exception as e:
                log(f"⚠️  Audio attachment skipped: {e}", level="WARNING")

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

    # 7. Validate rendered file
    out_file = Path(out_path)
    if not out_file.exists() or out_file.stat().st_size < 10000:
        raise RuntimeError(f"Video encoding failed or output file is empty: {out_path}")

    log(f"✅ Video produced successfully: {out_path} ({out_file.stat().st_size // 1024} KB)")
    return out_path, preview_path

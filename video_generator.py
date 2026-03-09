"""
video_generator.py — Generates dark aesthetic MP4 videos with nasheed audio
Fixed: Arabic bidi, transliteration direction, text overflow, audio mixing
"""

import textwrap
import os
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display
from moviepy.editor import ImageClip, AudioFileClip, CompositeAudioClip

import config

OUTPUT_DIR = Path("output_videos")
OUTPUT_DIR.mkdir(exist_ok=True)


# ─────────────────────────────────────────────
# FONT LOADER
# ─────────────────────────────────────────────

def load_fonts():
    try:
        fonts = {
            "arabic_xl": ImageFont.truetype(config.FONT_ARABIC, 72),
            "arabic_lg": ImageFont.truetype(config.FONT_ARABIC, 58),
            "arabic_md": ImageFont.truetype(config.FONT_ARABIC, 44),
            "latin_lg":  ImageFont.truetype(config.FONT_LATIN,  32),
            "latin_md":  ImageFont.truetype(config.FONT_LATIN,  26),
            "latin_sm":  ImageFont.truetype(config.FONT_LATIN,  20),
        }
        print("[Video] ✅ Custom fonts loaded (Amiri + NotoSans)")
        return fonts
    except Exception as e:
        print(f"[Video] ⚠️  Font fallback: {e}")
        default = ImageFont.load_default()
        return {k: default for k in ["arabic_xl","arabic_lg","arabic_md","latin_lg","latin_md","latin_sm"]}


# ─────────────────────────────────────────────
# ARABIC TEXT — FIX BIDI + RESHAPING
# ─────────────────────────────────────────────

def fix_arabic(text: str) -> str:
    """Reshape Arabic text and apply RTL bidi algorithm correctly."""
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)


def wrap_arabic(text: str, chars_per_line: int = 30) -> list:
    """Wrap Arabic text into lines BEFORE bidi processing."""
    raw_lines = textwrap.wrap(text, width=chars_per_line, break_long_words=False)
    if not raw_lines:
        raw_lines = [text]
    return [fix_arabic(line) for line in raw_lines]


def wrap_latin(text: str, chars_per_line: int = 45) -> list:
    """Wrap Latin text into lines."""
    lines = textwrap.wrap(text, width=chars_per_line)
    return lines if lines else [text]


# ─────────────────────────────────────────────
# TEXT MEASUREMENT
# ─────────────────────────────────────────────

def measure_line(draw, text, font):
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]
    except:
        return len(text) * 12, 36


# ─────────────────────────────────────────────
# DRAW CENTERED TEXT BLOCK
# ─────────────────────────────────────────────

def draw_block(draw, lines, y_start, font, color, line_spacing=12):
    """Draw a block of centered lines. Returns final Y."""
    W = config.VIDEO_WIDTH
    y = y_start
    for line in lines:
        w, h = measure_line(draw, line, font)
        x = max(40, (W - w) // 2)
        draw.text((x, y), line, font=font, fill=color)
        y += h + line_spacing
    return y


# ─────────────────────────────────────────────
# DECORATIVE ELEMENTS
# ─────────────────────────────────────────────

def draw_ornament(draw, cx, y, color, width=200):
    """Draw a simple Islamic geometric ornament line."""
    draw.line([(cx - width, y), (cx + width, y)], fill=color, width=1)
    draw.ellipse([cx-4, y-4, cx+4, y+4], fill=color)
    draw.line([(cx - width//2, y-8), (cx + width//2, y-8)], fill=color, width=1)


# ─────────────────────────────────────────────
# FRAME RENDERER
# ─────────────────────────────────────────────

def create_frame(dua: dict) -> Image.Image:
    W, H   = config.VIDEO_WIDTH, config.VIDEO_HEIGHT
    fonts  = load_fonts()
    MARGIN = 80
    MAX_W  = W - MARGIN * 2

    img  = Image.new("RGB", (W, H), config.COLOR_BG)
    draw = ImageDraw.Draw(img)

    # ── Radial glow background ──
    for r in range(600, 0, -8):
        ratio = (1 - r / 600) ** 2
        c = tuple(int(config.COLOR_BG[i] +
                      (config.COLOR_GOLD[i] - config.COLOR_BG[i]) * ratio * 0.15)
                  for i in range(3))
        draw.ellipse([W//2-r, H//3-r//2, W//2+r, H//3+r//2], fill=c)

    # ── Outer frame lines ──
    pad = 40
    draw.rectangle([pad, pad, W-pad, H-pad], outline=config.COLOR_GOLD_DIM, width=1)
    draw.rectangle([pad+12, pad+12, W-pad-12, H-pad-12], outline=config.COLOR_GOLD_DIM, width=1)

    y = 120

    # ── Bismillah ──
    bism_lines = wrap_arabic("بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ", chars_per_line=40)
    y = draw_block(draw, bism_lines, y, fonts["arabic_md"], config.COLOR_GOLD, line_spacing=14)

    y += 20
    cx = W // 2
    draw_ornament(draw, cx, y, config.COLOR_GOLD_DIM, width=280)
    y += 30

    # ── Type badge ──
    badge = f"— {dua['type'].upper()} —"
    w, h  = measure_line(draw, badge, fonts["latin_sm"])
    draw.text(((W - w)//2, y), badge, font=fonts["latin_sm"], fill=config.COLOR_GOLD_DIM)
    y += h + 30

    draw_ornament(draw, cx, y, config.COLOR_GOLD_DIM, width=200)
    y += 40

    # ── Arabic main text ──
    arabic_lines = wrap_arabic(dua["arabic"], chars_per_line=28)
    y = draw_block(draw, arabic_lines, y, fonts["arabic_lg"],
                   config.COLOR_GOLD, line_spacing=28)

    y += 30
    draw_ornament(draw, cx, y, config.COLOR_GOLD_DIM, width=240)
    y += 30

    # ── Transliteration (force LTR) ──
    translit_clean = get_display(dua["transliteration"], base_dir='L')
    translit_lines = wrap_latin(translit_clean, chars_per_line=48)
    y = draw_block(draw, translit_lines, y, fonts["latin_sm"],
                   config.COLOR_DIM, line_spacing=8)

    y += 24

    # ── Translation ──
    trans_text  = f'\u201c{dua["translation"]}\u201d'
    trans_lines = wrap_latin(trans_text, chars_per_line=42)
    y = draw_block(draw, trans_lines, y, fonts["latin_lg"],
                   config.COLOR_WHITE, line_spacing=12)

    y += 28
    draw_ornament(draw, cx, y, config.COLOR_GOLD_DIM, width=180)
    y += 24

    # ── Source ──
    src_lines = wrap_latin(f"📖  {dua['source']}", chars_per_line=50)
    y = draw_block(draw, src_lines, y, fonts["latin_sm"],
                   config.COLOR_GOLD_DIM, line_spacing=8)

    # ── Bottom watermark ──
    wm = "NoorPost · Authentic Islamic Content"
    w, h = measure_line(draw, wm, fonts["latin_sm"])
    draw.text(((W-w)//2, H-90), wm, font=fonts["latin_sm"], fill=config.COLOR_GOLD_DIM)

    return img


# ─────────────────────────────────────────────
# VIDEO GENERATOR WITH AUDIO
# ─────────────────────────────────────────────

def generate_video(dua: dict) -> str:
    print(f"[Video] 🎨 Generating video: {dua['type']} — {dua['source']}")

    # ── Render frame ──
    frame      = create_frame(dua)
    frame_path = OUTPUT_DIR / "_frame_temp.png"
    frame.save(str(frame_path))

    duration = config.VIDEO_DURATION
    clip     = ImageClip(str(frame_path), duration=duration)
    clip     = clip.set_fps(config.VIDEO_FPS)

    # ── Add nasheed audio ──
    try:
        from audio_manager import get_audio_file
        audio_path = get_audio_file(duration=duration)

        if audio_path and os.path.exists(audio_path):
            audio = AudioFileClip(audio_path).subclip(0, min(duration, AudioFileClip(audio_path).duration))
            audio = audio.volumex(0.35)  # 35% volume — gentle background
            audio = audio.audio_fadeout(2)
            clip  = clip.set_audio(audio)
            print("[Video] 🎵 Nasheed audio added!")
        else:
            print("[Video] ⚠️  No audio — generating silent video")
    except Exception as e:
        print(f"[Video] ⚠️  Audio skipped: {e}")

    # ── Export ──
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path  = str(OUTPUT_DIR / f"noorpost_{timestamp}.mp4")

    clip.write_videofile(
        out_path,
        codec="libx264",
        audio_codec="aac",
        logger=None,
        ffmpeg_params=["-pix_fmt", "yuv420p", "-movflags", "+faststart"],
    )

    # Cleanup temp frame
    try:
        frame_path.unlink()
    except:
        pass

    print(f"[Video] ✅ Saved: {out_path}")
    return out_path

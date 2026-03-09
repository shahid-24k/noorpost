"""
video_generator.py — Generates dark aesthetic MP4 videos
Arabic text rendered properly RTL using Amiri font (Quranic style)
"""

import textwrap
import os
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from arabic_reshaper.config_factory import config as reshaper_config_factory
from bidi.algorithm import get_display
from moviepy.editor import ImageClip, AudioFileClip

import config

OUTPUT_DIR = Path("output_videos")
OUTPUT_DIR.mkdir(exist_ok=True)

# ─────────────────────────────────────────────
# ARABIC RESHAPER CONFIG — Force proper Arabic
# ─────────────────────────────────────────────
RESHAPER_CONFIG = {
    'language': 'Arabic',
    'support_ligatures': True,
    'delete_harakat': False,
    'delete_tatweel': False,
    'support_zwj': True,
    'shift_harakat_position': False,
    'use_unsupported_chars_as_unshaped': True,
    'support_ligatures': True,
    'ARABIC LETTER SMALL HIGH ROUNDED ZERO': True,
    'ARABIC LETTER SMALL HIGH UPRIGHT RECTANGULAR ZERO': True,
}

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
# ARABIC TEXT — PROPER RTL
# ─────────────────────────────────────────────

def reshape_arabic(text: str) -> str:
    """Reshape + apply bidi to get proper RTL Arabic as in Quran."""
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)


def wrap_arabic(text: str, max_chars: int = 25) -> list:
    """
    Split Arabic text into lines by word, THEN reshape each line.
    This preserves correct letter joining within words.
    """
    words = text.split()
    lines = []
    current_words = []
    current_len = 0

    for word in words:
        word_len = len(word)
        if current_len + word_len > max_chars and current_words:
            lines.append(" ".join(current_words))
            current_words = [word]
            current_len = word_len + 1
        else:
            current_words.append(word)
            current_len += word_len + 1

    if current_words:
        lines.append(" ".join(current_words))

    # Reshape each line separately for correct letter joining
    return [reshape_arabic(line) for line in lines] if lines else [reshape_arabic(text)]


def wrap_latin(text: str, max_chars: int = 45) -> list:
    """Wrap Latin/transliteration text."""
    lines = textwrap.wrap(text, width=max_chars)
    return lines if lines else [text]


# ─────────────────────────────────────────────
# DRAWING HELPERS
# ─────────────────────────────────────────────

def measure(draw, text, font):
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]
    except:
        return len(text) * 12, 36


def draw_centered(draw, lines, y, font, color, line_gap=12):
    """Draw lines centered horizontally. Returns new Y."""
    W = config.VIDEO_WIDTH
    for line in lines:
        w, h = measure(draw, line, font)
        x = max(50, (W - w) // 2)
        draw.text((x, y), line, font=font, fill=color)
        y += h + line_gap
    return y


def draw_ornament(draw, cx, y, color, width=220):
    draw.line([(cx - width, y), (cx + width, y)], fill=color, width=1)
    draw.ellipse([cx-5, y-5, cx+5, y+5], fill=color)
    draw.line([(cx - width//2, y-10), (cx + width//2, y-10)], fill=color, width=1)


# ─────────────────────────────────────────────
# FRAME RENDERER
# ─────────────────────────────────────────────

def create_frame(dua: dict) -> Image.Image:
    W, H  = config.VIDEO_WIDTH, config.VIDEO_HEIGHT
    fonts = load_fonts()
    cx    = W // 2

    img  = Image.new("RGB", (W, H), config.COLOR_BG)
    draw = ImageDraw.Draw(img)

    # ── Background glow ──
    for r in range(600, 0, -8):
        ratio = (1 - r / 600) ** 2
        c = tuple(int(config.COLOR_BG[i] +
                      (config.COLOR_GOLD[i] - config.COLOR_BG[i]) * ratio * 0.15)
                  for i in range(3))
        draw.ellipse([cx-r, H//3-r//2, cx+r, H//3+r//2], fill=c)

    # ── Double border frame ──
    p = 40
    draw.rectangle([p, p, W-p, H-p], outline=config.COLOR_GOLD_DIM, width=1)
    draw.rectangle([p+14, p+14, W-p-14, H-p-14], outline=config.COLOR_GOLD_DIM, width=1)

    y = 130

    # ── Bismillah (RTL Arabic) ──
    bism = wrap_arabic("بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ", max_chars=40)
    y = draw_centered(draw, bism, y, fonts["arabic_md"], config.COLOR_GOLD, line_gap=16)

    y += 18
    draw_ornament(draw, cx, y, config.COLOR_GOLD_DIM, width=300)
    y += 32

    # ── Type badge ──
    badge = f"\u2014 {dua['type'].upper()} \u2014"
    w, h  = measure(draw, badge, fonts["latin_sm"])
    draw.text(((W-w)//2, y), badge, font=fonts["latin_sm"], fill=config.COLOR_GOLD_DIM)
    y += h + 28

    draw_ornament(draw, cx, y, config.COLOR_GOLD_DIM, width=200)
    y += 42

    # ── Main Arabic dua (RTL, Quranic style) ──
    arabic_lines = wrap_arabic(dua["arabic"], max_chars=22)
    y = draw_centered(draw, arabic_lines, y, fonts["arabic_lg"],
                      config.COLOR_GOLD, line_gap=30)

    y += 32
    draw_ornament(draw, cx, y, config.COLOR_GOLD_DIM, width=250)
    y += 28

    # ── Transliteration — always LTR ──
    translit = get_display(dua["transliteration"], base_dir='L')
    translit_lines = wrap_latin(translit, max_chars=46)
    y = draw_centered(draw, translit_lines, y, fonts["latin_sm"],
                      config.COLOR_DIM, line_gap=8)

    y += 22

    # ── Translation ──
    translation = f'\u201c{dua["translation"]}\u201d'
    trans_lines  = wrap_latin(translation, max_chars=40)
    y = draw_centered(draw, trans_lines, y, fonts["latin_lg"],
                      config.COLOR_WHITE, line_gap=14)

    y += 26
    draw_ornament(draw, cx, y, config.COLOR_GOLD_DIM, width=180)
    y += 22

    # ── Source ──
    src_lines = wrap_latin(f"Source: {dua['source']}", max_chars=52)
    y = draw_centered(draw, src_lines, y, fonts["latin_sm"],
                      config.COLOR_GOLD_DIM, line_gap=8)

    # ── Watermark ──
    wm   = "NoorPost \u00b7 Authentic Islamic Content"
    w, h = measure(draw, wm, fonts["latin_sm"])
    draw.text(((W-w)//2, H-85), wm, font=fonts["latin_sm"], fill=config.COLOR_GOLD_DIM)

    return img


# ─────────────────────────────────────────────
# VIDEO GENERATOR
# ─────────────────────────────────────────────

def generate_video(dua: dict) -> str:
    print(f"[Video] Generating: {dua['type']} — {dua['source']}")

    frame      = create_frame(dua)
    frame_path = OUTPUT_DIR / "_frame_temp.png"
    frame.save(str(frame_path))

    duration = config.VIDEO_DURATION
    clip     = ImageClip(str(frame_path), duration=duration)
    clip     = clip.set_fps(config.VIDEO_FPS)

    # ── Add nasheed audio if available ──
    try:
        from audio_manager import get_audio_file
        audio_path = get_audio_file(duration=duration)
        if audio_path and os.path.exists(audio_path):
            audio = AudioFileClip(audio_path)
            audio = audio.subclip(0, min(duration, audio.duration))
            audio = audio.volumex(0.35).audio_fadeout(2)
            clip  = clip.set_audio(audio)
            print("[Video] Nasheed audio added!")
    except Exception as e:
        print(f"[Video] Audio skipped: {e}")

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

    try:
        frame_path.unlink()
    except:
        pass

    print(f"[Video] Saved: {out_path}")
    return out_path

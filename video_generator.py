"""
video_generator.py — Generates dark aesthetic MP4 videos
Proper Arabic RTL rendering using harfbuzz/bidi approach
"""

import textwrap
import os
import random
from datetime import datetime
from pathlib import Path
import urllib.request
import subprocess

from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display
from moviepy.editor import ImageClip, AudioFileClip

import config

OUTPUT_DIR = Path("output_videos")
OUTPUT_DIR.mkdir(exist_ok=True)
FONTS_DIR = Path("assets/fonts")
FONTS_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────
# FONT REGISTRY
# ─────────────────────────────────────────────
ARABIC_FONTS = {
    "amiri": {
        "file": "assets/fonts/Amiri-Regular.ttf",
        "url":  None,
    },
    "scheherazade": {
        "file": "assets/fonts/Scheherazade-Regular.ttf",
        "url":  "https://github.com/silnrsi/font-scheherazade/releases/download/v3.300/Scheherazade-Regular.ttf",
    },
    "noto": {
        "file": "assets/fonts/NotoNaskhArabic-Regular.ttf",
        "url":  "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoNaskhArabic/NotoNaskhArabic-Regular.ttf",
    },
}

# ─────────────────────────────────────────────
# THEME REGISTRY
# ─────────────────────────────────────────────
THEMES = {
    "dark-gold": {
        "bg":       (8,   11,  16),
        "gold":     (201, 168,  76),
        "gold_dim": (122,  97,  40),
        "white":    (232, 228, 217),
        "dim":      (122, 135, 153),
    },
    "navy": {
        "bg":       (8,   18,  40),
        "gold":     (192, 160,  64),
        "gold_dim": (100,  80,  30),
        "white":    (220, 230, 255),
        "dim":      (100, 120, 160),
    },
    "green": {
        "bg":       (6,   22,  14),
        "gold":     (180, 160,  60),
        "gold_dim": ( 90,  80,  30),
        "white":    (220, 240, 225),
        "dim":      ( 90, 130, 100),
    },
    "pure-black": {
        "bg":       (  0,   0,   0),
        "gold":     (220, 190,  80),
        "gold_dim": (130, 110,  45),
        "white":    (255, 255, 255),
        "dim":      (160, 160, 160),
    },
}


# ─────────────────────────────────────────────
# FONT RESOLVER
# ─────────────────────────────────────────────

def resolve_font_path() -> str:
    mode = getattr(config, "FONT_MODE", "amiri").lower()
    if mode == "random":
        mode = random.choice(list(ARABIC_FONTS.keys()))

    font = ARABIC_FONTS.get(mode, ARABIC_FONTS["amiri"])
    path = Path(font["file"])

    if not path.exists() and font["url"]:
        try:
            print(f"[Video] Downloading font: {mode}...")
            urllib.request.urlretrieve(font["url"], str(path))
            if path.stat().st_size > 10000:
                print(f"[Video] Font ready: {mode}")
            else:
                path.unlink()
                path = Path(ARABIC_FONTS["amiri"]["file"])
        except Exception as e:
            print(f"[Video] Font download failed ({e}), using Amiri")
            path = Path(ARABIC_FONTS["amiri"]["file"])

    print(f"[Video] Font: {mode} -> {path}")
    return str(path)


def resolve_theme() -> dict:
    mode = getattr(config, "THEME_MODE", "dark-gold").lower()
    if mode == "random":
        mode = random.choice(list(THEMES.keys()))
    theme = THEMES.get(mode, THEMES["dark-gold"])
    print(f"[Video] Theme: {mode}")
    return theme


# ─────────────────────────────────────────────
# ARABIC RENDERING — USE CAIRO/PANGO VIA IMAGEMAGICK
# Fallback: reshape + bidi with Pillow
# ─────────────────────────────────────────────

def render_arabic_line_imagemagick(text: str, font_path: str, font_size: int,
                                    color: tuple, bg: tuple, width: int) -> Image.Image | None:
    """
    Use ImageMagick to render a single Arabic line properly RTL.
    ImageMagick has built-in RTL/bidi support.
    Returns PIL Image or None if ImageMagick not available.
    """
    try:
        hex_color = "#{:02x}{:02x}{:02x}".format(*color)
        hex_bg    = "#{:02x}{:02x}{:02x}".format(*bg)
        out_path  = "/tmp/arabic_line.png"

        cmd = [
            "convert",
            "-size", f"{width}x{font_size * 3}",
            f"xc:{hex_bg}",
            "-font", font_path,
            "-pointsize", str(font_size),
            "-fill", hex_color,
            "-gravity", "Center",
            "-annotate", "0", text,
            out_path
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=10)
        if result.returncode == 0:
            return Image.open(out_path)
    except Exception as e:
        pass
    return None


def render_arabic_pil(text: str, font: ImageFont, color: tuple,
                       bg_color: tuple, width: int) -> Image.Image:
    """
    Render Arabic text using PIL with proper reshape+bidi.
    Each word is reshaped then the whole line is bidi-processed.
    """
    # Step 1: reshape the full text first
    reshaped = arabic_reshaper.reshape(text)
    # Step 2: apply bidi to get visual order (RTL)
    visual   = get_display(reshaped)

    # Measure
    tmp_img  = Image.new("RGB", (10, 10), bg_color)
    tmp_draw = ImageDraw.Draw(tmp_img)
    try:
        bbox = tmp_draw.textbbox((0, 0), visual, font=font)
        tw   = bbox[2] - bbox[0]
        th   = bbox[3] - bbox[1]
    except:
        tw, th = len(visual) * 20, 60

    # Create line image with text centered
    line_img  = Image.new("RGB", (width, th + 20), bg_color)
    line_draw = ImageDraw.Draw(line_img)
    x = max(0, (width - tw) // 2)
    line_draw.text((x, 10), visual, font=font, fill=color)
    return line_img


def split_arabic_lines(text: str, font: ImageFont, max_width: int) -> list:
    """
    Split Arabic text into lines that fit within max_width.
    Split by words, measure each line.
    """
    words = text.split()
    lines = []
    current = []

    for word in words:
        test_line = " ".join(current + [word])
        reshaped  = arabic_reshaper.reshape(test_line)
        visual    = get_display(reshaped)

        tmp_img  = Image.new("RGB", (10, 10))
        tmp_draw = ImageDraw.Draw(tmp_img)
        try:
            bbox = tmp_draw.textbbox((0, 0), visual, font=font)
            w    = bbox[2] - bbox[0]
        except:
            w = len(visual) * 20

        if w > max_width and current:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)

    if current:
        lines.append(" ".join(current))

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


def draw_latin_centered(draw, lines, y, font, color, line_gap=12):
    W = config.VIDEO_WIDTH
    for line in lines:
        w, h = measure(draw, line, font)
        x = max(50, (W - w) // 2)
        draw.text((x, y), line, font=font, fill=color)
        y += h + line_gap
    return y


def draw_arabic_block(img, lines_text, y, font, color, bg, line_gap=24):
    """Draw Arabic lines onto img using render_arabic_pil."""
    W = img.width
    for line in lines_text:
        line_img = render_arabic_pil(line, font, color, bg, W - 100)
        lh = line_img.height
        # Paste centered
        x = 50
        img.paste(line_img, (x, y))
        y += lh + line_gap
    return y


def draw_ornament(draw, cx, y, color, width=220):
    draw.line([(cx - width, y), (cx + width, y)], fill=color, width=1)
    draw.ellipse([cx-5, y-5, cx+5, y+5], fill=color)
    draw.line([(cx - width//2, y-10), (cx + width//2, y-10)], fill=color, width=1)


def wrap_latin(text: str, max_chars: int = 45) -> list:
    lines = textwrap.wrap(text, width=max_chars)
    return lines if lines else [text]


# ─────────────────────────────────────────────
# FRAME RENDERER
# ─────────────────────────────────────────────

def create_frame(dua: dict, font_path: str, theme: dict) -> Image.Image:
    W, H = config.VIDEO_WIDTH, config.VIDEO_HEIGHT
    cx   = W // 2

    try:
        fonts = {
            "arabic_lg": ImageFont.truetype(font_path, 58),
            "arabic_md": ImageFont.truetype(font_path, 44),
            "latin_lg":  ImageFont.truetype(config.FONT_LATIN, 32),
            "latin_sm":  ImageFont.truetype(config.FONT_LATIN, 20),
        }
    except Exception as e:
        print(f"[Video] Font load error: {e}, falling back to Amiri")
        fallback = "assets/fonts/Amiri-Regular.ttf"
        fonts = {
            "arabic_lg": ImageFont.truetype(fallback, 58),
            "arabic_md": ImageFont.truetype(fallback, 44),
            "latin_lg":  ImageFont.truetype(config.FONT_LATIN, 32),
            "latin_sm":  ImageFont.truetype(config.FONT_LATIN, 20),
        }

    img  = Image.new("RGB", (W, H), theme["bg"])
    draw = ImageDraw.Draw(img)

    # ── Background glow ──
    for r in range(600, 0, -8):
        ratio = (1 - r / 600) ** 2
        c = tuple(int(theme["bg"][i] +
                      (theme["gold"][i] - theme["bg"][i]) * ratio * 0.15)
                  for i in range(3))
        draw.ellipse([cx-r, H//3-r//2, cx+r, H//3+r//2], fill=c)

    # ── Double border ──
    p = 40
    draw.rectangle([p, p, W-p, H-p], outline=theme["gold_dim"], width=1)
    draw.rectangle([p+14, p+14, W-p-14, H-p-14], outline=theme["gold_dim"], width=1)

    y = 130

    # ── Bismillah ──
    bism_lines = split_arabic_lines(
        "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
        fonts["arabic_md"], W - 160
    )
    y = draw_arabic_block(img, bism_lines, y, fonts["arabic_md"],
                          theme["gold"], theme["bg"], line_gap=16)

    draw = ImageDraw.Draw(img)  # refresh draw after paste
    y += 18
    draw_ornament(draw, cx, y, theme["gold_dim"], width=300)
    y += 32

    # ── Type badge ──
    badge = f"\u2014 {dua['type'].upper()} \u2014"
    w, h  = measure(draw, badge, fonts["latin_sm"])
    draw.text(((W-w)//2, y), badge, font=fonts["latin_sm"], fill=theme["gold_dim"])
    y += h + 28

    draw_ornament(draw, cx, y, theme["gold_dim"], width=200)
    y += 42

    # ── Arabic dua ──
    arabic_lines = split_arabic_lines(dua["arabic"], fonts["arabic_lg"], W - 160)
    y = draw_arabic_block(img, arabic_lines, y, fonts["arabic_lg"],
                          theme["gold"], theme["bg"], line_gap=30)

    draw = ImageDraw.Draw(img)
    y += 32
    draw_ornament(draw, cx, y, theme["gold_dim"], width=250)
    y += 28

    # ── Transliteration (force LTR) ──
    translit       = get_display(dua["transliteration"], base_dir='L')
    translit_lines = wrap_latin(translit, max_chars=46)
    y = draw_latin_centered(draw, translit_lines, y, fonts["latin_sm"],
                             theme["dim"], line_gap=8)
    y += 22

    # ── Translation ──
    translation = f'\u201c{dua["translation"]}\u201d'
    trans_lines  = wrap_latin(translation, max_chars=40)
    y = draw_latin_centered(draw, trans_lines, y, fonts["latin_lg"],
                             theme["white"], line_gap=14)
    y += 26
    draw_ornament(draw, cx, y, theme["gold_dim"], width=180)
    y += 22

    # ── Source ──
    src_lines = wrap_latin(f"Source: {dua['source']}", max_chars=52)
    y = draw_latin_centered(draw, src_lines, y, fonts["latin_sm"],
                             theme["gold_dim"], line_gap=8)

    # ── Watermark ──
    wm   = "NoorPost \u00b7 Authentic Islamic Content"
    w, h = measure(draw, wm, fonts["latin_sm"])
    draw.text(((W-w)//2, H-85), wm, font=fonts["latin_sm"], fill=theme["gold_dim"])

    return img


# ─────────────────────────────────────────────
# VIDEO GENERATOR
# ─────────────────────────────────────────────

def generate_video(dua: dict) -> str:
    font_path = resolve_font_path()
    theme     = resolve_theme()

    print(f"[Video] Generating: {dua['type']} — {dua['source']}")

    frame      = create_frame(dua, font_path, theme)
    frame_path = OUTPUT_DIR / "_frame_temp.png"
    frame.save(str(frame_path))

    timestamp    = datetime.now().strftime("%Y%m%d_%H%M%S")
    preview_path = OUTPUT_DIR / f"preview_{timestamp}.jpg"
    frame.save(str(preview_path), "JPEG", quality=85)
    print(f"[Video] Preview saved: {preview_path.name}")

    try:
        from instagram import get_dropbox_client
        import dropbox as dbx_module
        dbx = get_dropbox_client()
        with open(str(preview_path), "rb") as f:
            dbx.files_upload(
                f.read(),
                f"/NoorPost/previews/preview_{timestamp}.jpg",
                mode=dbx_module.files.WriteMode("overwrite")
            )
        print("[Video] Preview uploaded to Dropbox /NoorPost/previews/")
    except Exception as e:
        print(f"[Video] Preview upload skipped: {e}")

    duration = config.VIDEO_DURATION
    clip     = ImageClip(str(frame_path), duration=duration)
    clip     = clip.set_fps(config.VIDEO_FPS)

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

    out_path = str(OUTPUT_DIR / f"noorpost_{timestamp}.mp4")
    clip.write_videofile(
        out_path,
        codec="libx264",
        audio_codec="aac",
        logger=None,
        ffmpeg_params=["-pix_fmt", "yuv420p", "-movflags", "+faststart"],
    )

    try:
        frame_path.unlink()
        preview_path.unlink()
    except:
        pass

    print(f"[Video] Saved: {out_path}")
    return out_path

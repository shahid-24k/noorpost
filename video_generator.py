"""
video_generator.py — Arabic rendered via ImageMagick (proper shaping engine)
Latin text via Pillow. Composited together.
"""

import textwrap
import os
import random
import subprocess
from datetime import datetime
from pathlib import Path
import urllib.request

from PIL import Image, ImageDraw, ImageFont
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

THEMES = {
    "dark-gold": {
        "bg":       (8,   11,  16),
        "gold":     (201, 168,  76),
        "gold_dim": (122,  97,  40),
        "white":    (232, 228, 217),
        "dim":      (122, 135, 153),
        "bg_hex":   "#080b10",
        "gold_hex": "#c9a84c",
    },
    "navy": {
        "bg":       (8,   18,  40),
        "gold":     (192, 160,  64),
        "gold_dim": (100,  80,  30),
        "white":    (220, 230, 255),
        "dim":      (100, 120, 160),
        "bg_hex":   "#08122a",
        "gold_hex": "#c0a040",
    },
    "green": {
        "bg":       (6,   22,  14),
        "gold":     (180, 160,  60),
        "gold_dim": ( 90,  80,  30),
        "white":    (220, 240, 225),
        "dim":      ( 90, 130, 100),
        "bg_hex":   "#06160e",
        "gold_hex": "#b4a03c",
    },
    "pure-black": {
        "bg":       (  0,   0,   0),
        "gold":     (220, 190,  80),
        "gold_dim": (130, 110,  45),
        "white":    (255, 255, 255),
        "dim":      (160, 160, 160),
        "bg_hex":   "#000000",
        "gold_hex": "#dcc050",
    },
}


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
            if path.stat().st_size < 10000:
                path.unlink()
                path = Path(ARABIC_FONTS["amiri"]["file"])
        except:
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
# IMAGEMAGICK ARABIC RENDERER
# ─────────────────────────────────────────────

def render_arabic_imagemagick(text: str, font_path: str, font_size: int,
                               color_hex: str, bg_hex: str,
                               canvas_w: int) -> Image.Image:
    """
    Render Arabic text properly using ImageMagick.
    ImageMagick uses FreeType + HarfBuzz for correct Arabic shaping & RTL.
    """
    out_path = "/tmp/arabic_render.png"

    # Use pango markup for proper RTL/Arabic rendering
    cmd = [
        "convert",
        "-size", f"{canvas_w}x400",
        f"xc:{bg_hex}",
        "-font", font_path,
        "-pointsize", str(font_size),
        "-fill", color_hex,
        "-gravity", "Center",
        "-annotate", "0", text,
        "-trim",
        "+repage",
        out_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, timeout=15)
        if result.returncode == 0 and Path(out_path).exists():
            img = Image.open(out_path).copy()
            # Add padding
            padded = Image.new("RGB", (canvas_w, img.height + 20),
                               tuple(int(bg_hex.lstrip('#')[i:i+2], 16) for i in (0,2,4)))
            x = (canvas_w - img.width) // 2
            padded.paste(img, (x, 10))
            return padded
    except Exception as e:
        print(f"[Video] ImageMagick error: {e}")

    # Fallback: blank image
    blank = Image.new("RGB", (canvas_w, font_size + 20),
                      tuple(int(bg_hex.lstrip('#')[i:i+2], 16) for i in (0,2,4)))
    return blank


def render_arabic_block_imagemagick(lines: list, font_path: str, font_size: int,
                                     color_hex: str, bg_hex: str,
                                     canvas_w: int) -> Image.Image:
    """Render multiple Arabic lines and stack them vertically."""
    line_imgs = []
    for line in lines:
        img = render_arabic_imagemagick(line, font_path, font_size,
                                         color_hex, bg_hex, canvas_w)
        line_imgs.append(img)

    total_h = sum(img.height for img in line_imgs) + 8 * (len(line_imgs) - 1)
    bg_rgb  = tuple(int(bg_hex.lstrip('#')[i:i+2], 16) for i in (0,2,4))
    result  = Image.new("RGB", (canvas_w, total_h), bg_rgb)

    y = 0
    for img in line_imgs:
        result.paste(img, (0, y))
        y += img.height + 8

    return result


def split_arabic_by_words(text: str, max_words_per_line: int = 4) -> list:
    """Simple word-based split for Arabic lines."""
    words = text.split()
    lines = []
    for i in range(0, len(words), max_words_per_line):
        lines.append(" ".join(words[i:i+max_words_per_line]))
    return lines if lines else [text]


# ─────────────────────────────────────────────
# PILLOW LATIN HELPERS
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
    W, H    = config.VIDEO_WIDTH, config.VIDEO_HEIGHT
    cx      = W // 2
    bg_hex  = theme["bg_hex"]
    gold_hex= theme["gold_hex"]

    try:
        latin_lg = ImageFont.truetype(config.FONT_LATIN, 32)
        latin_sm = ImageFont.truetype(config.FONT_LATIN, 20)
    except:
        latin_lg = ImageFont.load_default()
        latin_sm = ImageFont.load_default()

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

    y = 110

    # ── Bismillah via ImageMagick ──
    bism_lines = split_arabic_by_words("بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ", max_words_per_line=6)
    bism_img   = render_arabic_block_imagemagick(bism_lines, font_path, 44,
                                                  gold_hex, bg_hex, W - 100)
    img.paste(bism_img, (50, y))
    y += bism_img.height + 18

    draw = ImageDraw.Draw(img)
    draw_ornament(draw, cx, y, theme["gold_dim"], width=300)
    y += 28

    # ── Type badge ──
    badge = f"\u2014 {dua['type'].upper()} \u2014"
    w, h  = measure(draw, badge, latin_sm)
    draw.text(((W-w)//2, y), badge, font=latin_sm, fill=theme["gold_dim"])
    y += h + 24

    draw_ornament(draw, cx, y, theme["gold_dim"], width=200)
    y += 36

    # ── Arabic dua via ImageMagick ──
    arabic_lines = split_arabic_by_words(dua["arabic"], max_words_per_line=4)
    arabic_img   = render_arabic_block_imagemagick(arabic_lines, font_path, 58,
                                                    gold_hex, bg_hex, W - 100)
    img.paste(arabic_img, (50, y))
    y += arabic_img.height + 28

    draw = ImageDraw.Draw(img)
    draw_ornament(draw, cx, y, theme["gold_dim"], width=250)
    y += 24

    # ── Transliteration ──
    translit_lines = wrap_latin(dua["transliteration"], max_chars=46)
    y = draw_latin_centered(draw, translit_lines, y, latin_sm,
                             theme["dim"], line_gap=8)
    y += 20

    # ── Translation ──
    translation = f'\u201c{dua["translation"]}\u201d'
    trans_lines  = wrap_latin(translation, max_chars=40)
    y = draw_latin_centered(draw, trans_lines, y, latin_lg,
                             theme["white"], line_gap=14)
    y += 24

    draw_ornament(draw, cx, y, theme["gold_dim"], width=180)
    y += 20

    # ── Source ──
    src_lines = wrap_latin(f"Source: {dua['source']}", max_chars=52)
    draw_latin_centered(draw, src_lines, y, latin_sm, theme["gold_dim"], line_gap=8)

    # ── Watermark ──
    wm   = "NoorPost \u00b7 Authentic Islamic Content"
    w, h = measure(draw, wm, latin_sm)
    draw.text(((W-w)//2, H-85), wm, font=latin_sm, fill=theme["gold_dim"])

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

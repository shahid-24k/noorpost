"""
video_generator.py — Arabic rendered via Wand (ImageMagick Python binding)
Proper Arabic shaping, RTL, connected letters. Latin via Pillow.
"""

import textwrap
import os
import random
from datetime import datetime
from pathlib import Path
import urllib.request

from PIL import Image, ImageDraw, ImageFont
from wand.image import Image as WandImage
from wand.drawing import Drawing
from wand.color import Color
from moviepy.editor import ImageClip, AudioFileClip

import config

OUTPUT_DIR = Path("output_videos")
OUTPUT_DIR.mkdir(exist_ok=True)
FONTS_DIR  = Path("assets/fonts")
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
        "dim_hex":  "#7a8799",
        "white_hex":"#e8e4d9",
    },
    "navy": {
        "bg":       (8,   18,  40),
        "gold":     (192, 160,  64),
        "gold_dim": (100,  80,  30),
        "white":    (220, 230, 255),
        "dim":      (100, 120, 160),
        "bg_hex":   "#08122a",
        "gold_hex": "#c0a040",
        "dim_hex":  "#6478a0",
        "white_hex":"#dce6ff",
    },
    "green": {
        "bg":       (6,   22,  14),
        "gold":     (180, 160,  60),
        "gold_dim": ( 90,  80,  30),
        "white":    (220, 240, 225),
        "dim":      ( 90, 130, 100),
        "bg_hex":   "#06160e",
        "gold_hex": "#b4a03c",
        "dim_hex":  "#5a8264",
        "white_hex":"#dcf0e1",
    },
    "pure-black": {
        "bg":       (  0,   0,   0),
        "gold":     (220, 190,  80),
        "gold_dim": (130, 110,  45),
        "white":    (255, 255, 255),
        "dim":      (160, 160, 160),
        "bg_hex":   "#000000",
        "gold_hex": "#dcc050",
        "dim_hex":  "#a0a0a0",
        "white_hex":"#ffffff",
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
# WAND ARABIC RENDERER — proper RTL shaping
# ─────────────────────────────────────────────

def render_arabic_line_wand(text: str, font_path: str, font_size: int,
                              color_hex: str, bg_hex: str, canvas_w: int) -> Image.Image:
    """Render one Arabic line using Wand — proper RTL connected letters."""
    height = int(font_size * 2.0)
    with Drawing() as draw:
        draw.font            = font_path
        draw.font_size       = font_size
        draw.fill_color      = Color(color_hex)
        draw.gravity         = 'center'
        draw.text_direction  = 'right_to_left'
        draw.text_encoding   = 'UTF-8'
        with WandImage(width=canvas_w, height=height,
                       background=Color(bg_hex)) as wimg:
            draw.text(0, 0, text)
            draw(wimg)
            wimg.trim()
            wimg.save(filename='/tmp/_wand_line.png')

    pil_img = Image.open('/tmp/_wand_line.png').convert('RGB')
    # Center on canvas
    canvas = Image.new('RGB', (canvas_w, pil_img.height + 16),
                       tuple(int(bg_hex.lstrip('#')[i:i+2], 16) for i in (0,2,4)))
    x = (canvas_w - pil_img.width) // 2
    canvas.paste(pil_img, (max(0, x), 8))
    return canvas


def render_arabic_block(lines: list, font_path: str, font_size: int,
                         color_hex: str, bg_hex: str, canvas_w: int,
                         line_gap: int = 10) -> Image.Image:
    """Render multiple Arabic lines stacked vertically."""
    imgs = [render_arabic_line_wand(line, font_path, font_size,
                                     color_hex, bg_hex, canvas_w)
            for line in lines]
    total_h = sum(i.height for i in imgs) + line_gap * (len(imgs) - 1)
    bg_rgb  = tuple(int(bg_hex.lstrip('#')[i:i+2], 16) for i in (0,2,4))
    result  = Image.new('RGB', (canvas_w, total_h), bg_rgb)
    y = 0
    for i in imgs:
        result.paste(i, (0, y))
        y += i.height + line_gap
    return result


def split_arabic(text: str, words_per_line: int = 4) -> list:
    """Split Arabic text into lines by word count."""
    words = text.split()
    lines = []
    for i in range(0, len(words), words_per_line):
        lines.append(" ".join(words[i:i+words_per_line]))
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


def draw_latin(draw, lines, y, font, color, gap=12):
    W = config.VIDEO_WIDTH
    for line in lines:
        w, h = measure(draw, line, font)
        draw.text(((W-w)//2, y), line, font=font, fill=color)
        y += h + gap
    return y


def ornament(draw, cx, y, color, width=220):
    draw.line([(cx-width, y), (cx+width, y)], fill=color, width=1)
    draw.ellipse([cx-5, y-5, cx+5, y+5], fill=color)
    draw.line([(cx-width//2, y-10), (cx+width//2, y-10)], fill=color, width=1)


def wrap(text, n=45):
    lines = textwrap.wrap(text, width=n)
    return lines if lines else [text]


# ─────────────────────────────────────────────
# FRAME RENDERER
# ─────────────────────────────────────────────

def create_frame(dua: dict, font_path: str, theme: dict) -> Image.Image:
    W, H   = config.VIDEO_WIDTH, config.VIDEO_HEIGHT
    cx     = W // 2
    BG     = theme["bg"]
    GOLD   = theme["gold"]
    GDIM   = theme["gold_dim"]
    WHITE  = theme["white"]
    DIM    = theme["dim"]
    BH     = theme["bg_hex"]
    GH     = theme["gold_hex"]

    try:
        lg = ImageFont.truetype(config.FONT_LATIN, 32)
        sm = ImageFont.truetype(config.FONT_LATIN, 20)
    except:
        lg = sm = ImageFont.load_default()

    img  = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # ── Glow ──
    for r in range(600, 0, -8):
        ratio = (1 - r/600)**2
        c = tuple(int(BG[i] + (GOLD[i]-BG[i])*ratio*0.15) for i in range(3))
        draw.ellipse([cx-r, H//3-r//2, cx+r, H//3+r//2], fill=c)

    # ── Border ──
    p = 40
    draw.rectangle([p, p, W-p, H-p], outline=GDIM, width=1)
    draw.rectangle([p+14, p+14, W-p-14, H-p-14], outline=GDIM, width=1)

    y = 110

    # ── Bismillah ──
    bism = render_arabic_block(
        split_arabic("بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ", words_per_line=6),
        font_path, 44, GH, BH, W-100, line_gap=8
    )
    img.paste(bism, (50, y))
    y += bism.height + 16

    draw = ImageDraw.Draw(img)
    ornament(draw, cx, y, GDIM, 300)
    y += 26

    # ── Type badge ──
    badge = f"\u2014 {dua['type'].upper()} \u2014"
    w, h  = measure(draw, badge, sm)
    draw.text(((W-w)//2, y), badge, font=sm, fill=GDIM)
    y += h + 22

    ornament(draw, cx, y, GDIM, 200)
    y += 34

    # ── Arabic dua ──
    arabic_img = render_arabic_block(
        split_arabic(dua["arabic"], words_per_line=4),
        font_path, 58, GH, BH, W-100, line_gap=14
    )
    img.paste(arabic_img, (50, y))
    y += arabic_img.height + 26

    draw = ImageDraw.Draw(img)
    ornament(draw, cx, y, GDIM, 250)
    y += 24

    # ── Transliteration ──
    y = draw_latin(draw, wrap(dua["transliteration"], 46),
                   y, sm, DIM, gap=8)
    y += 18

    # ── Translation ──
    y = draw_latin(draw, wrap(f'\u201c{dua["translation"]}\u201d', 40),
                   y, lg, WHITE, gap=14)
    y += 22

    ornament(draw, cx, y, GDIM, 180)
    y += 20

    # ── Source ──
    draw_latin(draw, wrap(f"Source: {dua['source']}", 52),
               y, sm, GDIM, gap=8)

    # ── Watermark ──
    wm   = "NoorPost \u00b7 Authentic Islamic Content"
    w, h = measure(draw, wm, sm)
    draw.text(((W-w)//2, H-85), wm, font=sm, fill=GDIM)

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
    print(f"[Video] Preview: {preview_path.name}")

    try:
        from instagram import get_dropbox_client
        import dropbox as dbx_module
        dbx = get_dropbox_client()
        with open(str(preview_path), "rb") as f:
            dbx.files_upload(f.read(),
                f"/NoorPost/previews/preview_{timestamp}.jpg",
                mode=dbx_module.files.WriteMode("overwrite"))
        print("[Video] Preview uploaded to Dropbox!")
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

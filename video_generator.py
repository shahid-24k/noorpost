"""
video_generator.py — Arabic rendered via wkhtmltoimage (perfect RTL shaping)
Latin text via Pillow. Full 1080x1920 Islamic video generator.
"""

import textwrap
import os
import random
import subprocess
import json
from datetime import datetime
from pathlib import Path
import urllib.request

from PIL import Image, ImageDraw, ImageFont
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
        "bg":        (8,   11,  16),
        "gold":      (201, 168,  76),
        "gold_dim":  (122,  97,  40),
        "white":     (232, 228, 217),
        "dim":       (122, 135, 153),
        "bg_hex":    "#080b10",
        "gold_hex":  "#c9a84c",
        "dim_hex":   "#7a8799",
        "white_hex": "#e8e4d9",
        "gdim_hex":  "#7a6128",
    },
    "navy": {
        "bg":        (8,   18,  40),
        "gold":      (192, 160,  64),
        "gold_dim":  (100,  80,  30),
        "white":     (220, 230, 255),
        "dim":       (100, 120, 160),
        "bg_hex":    "#08122a",
        "gold_hex":  "#c0a040",
        "dim_hex":   "#6478a0",
        "white_hex": "#dce6ff",
        "gdim_hex":  "#64501e",
    },
    "green": {
        "bg":        (6,   22,  14),
        "gold":      (180, 160,  60),
        "gold_dim":  (90,   80,  30),
        "white":     (220, 240, 225),
        "dim":       (90,  130, 100),
        "bg_hex":    "#06160e",
        "gold_hex":  "#b4a03c",
        "dim_hex":   "#5a8264",
        "white_hex": "#dcf0e1",
        "gdim_hex":  "#5a501e",
    },
    "pure-black": {
        "bg":        (0,    0,   0),
        "gold":      (220, 190,  80),
        "gold_dim":  (130, 110,  45),
        "white":     (255, 255, 255),
        "dim":       (160, 160, 160),
        "bg_hex":    "#000000",
        "gold_hex":  "#dcc050",
        "dim_hex":   "#a0a0a0",
        "white_hex": "#ffffff",
        "gdim_hex":  "#826e2d",
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
# WKHTMLTOIMAGE ARABIC RENDERER
# ─────────────────────────────────────────────

def render_arabic_html(text: str, font_path: str, font_size: int,
                        color_hex: str, bg_hex: str, canvas_w: int) -> Image.Image:
    """
    Render Arabic text via wkhtmltoimage using local font.
    Returns a PIL Image with the rendered Arabic text.
    """
    abs_font = str(Path(font_path).resolve())

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
@font-face {{ font-family:'ArabicFont'; src:url('{abs_font}'); }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ background:{bg_hex}; width:{canvas_w}px; overflow:hidden; }}
p {{
  font-family:'ArabicFont',serif;
  font-size:{font_size}px;
  color:{color_hex};
  direction:rtl;
  text-align:center;
  padding:10px 20px;
  line-height:1.8;
  word-spacing:4px;
}}
</style></head>
<body><p>{text}</p></body></html>"""

    html_path = "/tmp/_arabic_render.html"
    img_path  = "/tmp/_arabic_render.png"

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    try:
        result = subprocess.run([
            "wkhtmltoimage",
            "--width", str(canvas_w),
            "--quality", "100",
            "--format", "png",
            html_path, img_path
        ], capture_output=True, timeout=20)

        if Path(img_path).exists():
            img = Image.open(img_path).convert("RGB")
            return img
    except Exception as e:
        print(f"[Video] wkhtmltoimage error: {e}")

    # Fallback: blank image
    return Image.new("RGB", (canvas_w, font_size + 20),
                     tuple(int(bg_hex.lstrip('#')[i:i+2], 16) for i in (0,2,4)))


# ─────────────────────────────────────────────
# PILLOW LATIN + DECORATION HELPERS
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
    W, H = config.VIDEO_WIDTH, config.VIDEO_HEIGHT
    cx   = W // 2
    BG   = theme["bg"]
    GOLD = theme["gold"]
    GDIM = theme["gold_dim"]
    BH   = theme["bg_hex"]
    GH   = theme["gold_hex"]

    try:
        lg = ImageFont.truetype(config.FONT_LATIN, 32)
        sm = ImageFont.truetype(config.FONT_LATIN, 20)
    except:
        lg = sm = ImageFont.load_default()

    img  = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # ── Background glow ──
    for r in range(600, 0, -8):
        ratio = (1 - r/600) ** 2
        c = tuple(int(BG[i] + (GOLD[i]-BG[i])*ratio*0.15) for i in range(3))
        draw.ellipse([cx-r, H//3-r//2, cx+r, H//3+r//2], fill=c)

    # ── Double border ──
    p = 40
    draw.rectangle([p, p, W-p, H-p], outline=GDIM, width=1)
    draw.rectangle([p+14, p+14, W-p-14, H-p-14], outline=GDIM, width=1)

    y = 100

    # ── Bismillah via wkhtmltoimage ──
    bism_img = render_arabic_html(
        "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
        font_path, 44, GH, BH, W
    )
    img.paste(bism_img, (0, y))
    y += bism_img.height + 14

    draw = ImageDraw.Draw(img)
    ornament(draw, cx, y, GDIM, 300)
    y += 26

    # ── Type badge ──
    badge = f"\u2014 {dua['type'].upper()} \u2014"
    w, h  = measure(draw, badge, sm)
    draw.text(((W-w)//2, y), badge, font=sm, fill=GDIM)
    y += h + 22

    ornament(draw, cx, y, GDIM, 200)
    y += 32

    # ── Arabic dua via wkhtmltoimage ──
    arabic_img = render_arabic_html(
        dua["arabic"],
        font_path, 54, GH, BH, W
    )
    img.paste(arabic_img, (0, y))
    y += arabic_img.height + 24

    draw = ImageDraw.Draw(img)
    ornament(draw, cx, y, GDIM, 250)
    y += 22

    # ── Transliteration ──
    y = draw_latin(draw, wrap(dua["transliteration"], 46),
                   y, sm, theme["dim"], gap=8)
    y += 18

    # ── Translation ──
    y = draw_latin(draw, wrap(f'\u201c{dua["translation"]}\u201d', 40),
                   y, lg, theme["white"], gap=14)
    y += 22

    ornament(draw, cx, y, GDIM, 180)
    y += 18

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

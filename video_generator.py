"""
video_generator.py — Generates dark aesthetic MP4 videos from duas
Uses Pillow for frame rendering + MoviePy for video encoding
"""

import textwrap
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

from moviepy.editor import ImageClip
import config

OUTPUT_DIR = Path("output_videos")
OUTPUT_DIR.mkdir(exist_ok=True)


# ─────────────────────────────────────────────
# FONT LOADER
# ─────────────────────────────────────────────

def load_fonts():
    try:
        f_arabic_xl = ImageFont.truetype(config.FONT_ARABIC, 80)
        f_arabic_lg = ImageFont.truetype(config.FONT_ARABIC, 64)
        f_arabic_md = ImageFont.truetype(config.FONT_ARABIC, 46)
        f_latin_lg  = ImageFont.truetype(config.FONT_LATIN,  34)
        f_latin_md  = ImageFont.truetype(config.FONT_LATIN,  28)
        f_latin_sm  = ImageFont.truetype(config.FONT_LATIN,  22)
        print("[Video] ✅ Custom fonts loaded (Amiri + NotoSans)")
    except Exception as e:
        print(f"[Video] ⚠️  Font fallback: {e}")
        default = ImageFont.load_default()
        f_arabic_xl = f_arabic_lg = f_arabic_md = default
        f_latin_lg  = f_latin_md  = f_latin_sm  = default

    return {
        "arabic_xl": f_arabic_xl,
        "arabic_lg": f_arabic_lg,
        "arabic_md": f_arabic_md,
        "latin_lg":  f_latin_lg,
        "latin_md":  f_latin_md,
        "latin_sm":  f_latin_sm,
    }


# ─────────────────────────────────────────────
# ARABIC RENDERER — FIXED
# ─────────────────────────────────────────────

def fix_arabic(text: str) -> str:
    """Properly reshape and apply bidi algorithm to Arabic text."""
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)


def fix_transliteration(text: str) -> str:
    """Ensure transliteration is always left-to-right."""
    return get_display(text, base_dir='L')


# ─────────────────────────────────────────────
# TEXT DRAWER — handles Arabic (RTL) and Latin (LTR) separately
# ─────────────────────────────────────────────

def draw_text_centered(draw, text, y, font, color, max_width=880,
                        line_spacing=16, is_arabic=False):
    """Draw centered wrapped text. Returns final Y position."""
    W = config.VIDEO_WIDTH

    # Estimate chars per line
    try:
        sample_w = font.getlength("ا" if is_arabic else "A")
        chars_per_line = max(10, int(max_width / max(sample_w, 1)))
    except:
        chars_per_line = 25 if is_arabic else 40

    # For Arabic — wrap BEFORE applying bidi/reshape
    if is_arabic:
        raw_lines = textwrap.wrap(text, width=chars_per_line)
        lines = [fix_arabic(line) for line in raw_lines]
    else:
        lines = textwrap.wrap(text, width=chars_per_line)
        if not lines:
            lines = [text]

    for line in lines:
        try:
            bbox   = draw.textbbox((0, 0), line, font=font)
            line_w = bbox[2] - bbox[0]
            line_h = bbox[3] - bbox[1]
        except:
            line_w = len(line) * 14
            line_h = 40

        x = (W - line_w) // 2
        draw.text((x, y), line, font=font, fill=color)
        y += line_h + line_spacing

    return y


# ─────────────────────────────────────────────
# FRAME RENDERER
# ─────────────────────────────────────────────

def create_frame(dua: dict) -> Image.Image:
    W, H  = config.VIDEO_WIDTH, config.VIDEO_HEIGHT
    fonts = load_fonts()

    img  = Image.new("RGB", (W, H), config.COLOR_BG)
    draw = ImageDraw.Draw(img)

    # ── Background glow ──
    for r in range(500, 0, -10):
        ratio = 1 - r / 500
        c = tuple(int(config.COLOR_BG[i] +
                      (config.COLOR_GOLD[i] - config.COLOR_BG[i]) * ratio * 0.12)
                  for i in range(3))
        draw.ellipse([W//2-r, 200-r//2, W//2+r, 200+r//2], fill=c)

    # ── Top border ──
    draw.line([(80,  200), (W-80,  200)], fill=config.COLOR_GOLD_DIM, width=1)
    draw.line([(140, 212), (W-140, 212)], fill=config.COLOR_GOLD_DIM, width=1)

    # ── Bismillah ──
    bismillah = fix_arabic("بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ")
    y = draw_text_centered(draw, bismillah, 240,
                           fonts["arabic_md"], config.COLOR_GOLD,
                           is_arabic=True)

    # ── Content type badge ──
    badge = f"— {dua['type'].upper()} —"
    y = draw_text_centered(draw, badge, y + 20,
                           fonts["latin_sm"], config.COLOR_GOLD_DIM)

    # ── Divider ──
    y += 30
    draw.line([(180, y), (W-180, y)], fill=config.COLOR_GOLD_DIM, width=1)
    y += 50

    # ── Arabic main text ──
    y = draw_text_centered(draw, dua["arabic"], y,
                           fonts["arabic_lg"], config.COLOR_GOLD,
                           max_width=900, line_spacing=28,
                           is_arabic=True)

    # ── Divider ──
    y += 40
    draw.line([(200, y), (W-200, y)], fill=config.COLOR_GOLD_DIM, width=1)
    y += 40

    # ── Transliteration — force LTR ──
    translit = fix_transliteration(dua["transliteration"])
    y = draw_text_centered(draw, translit, y,
                           fonts["latin_sm"], config.COLOR_DIM,
                           max_width=820, line_spacing=10,
                           is_arabic=False)

    # ── Translation ──
    y += 30
    trans = f'"{dua["translation"]}"'
    y = draw_text_centered(draw, trans, y,
                           fonts["latin_lg"], config.COLOR_WHITE,
                           max_width=820, line_spacing=14,
                           is_arabic=False)

    # ── Source ──
    y += 40
    y = draw_text_centered(draw, f"📖  {dua['source']}", y,
                           fonts["latin_sm"], config.COLOR_GOLD_DIM,
                           is_arabic=False)

    # ── Bottom border ──
    draw.line([(140, H-212), (W-140, H-212)], fill=config.COLOR_GOLD_DIM, width=1)
    draw.line([(80,  H-200), (W-80,  H-200)], fill=config.COLOR_GOLD_DIM, width=1)

    # ── Watermark ──
    draw_text_centered(draw, "NoorPost · Authentic Islamic Content",
                       H-180, fonts["latin_sm"], config.COLOR_GOLD_DIM)

    return img


# ─────────────────────────────────────────────
# VIDEO GENERATOR
# ─────────────────────────────────────────────

def generate_video(dua: dict) -> str:
    print(f"[Video] 🎨 Generating video: {dua['type']} — {dua['source']}")

    frame      = create_frame(dua)
    frame_path = OUTPUT_DIR / "_frame_temp.png"
    frame.save(str(frame_path))

    clip = ImageClip(str(frame_path), duration=config.VIDEO_DURATION)
    clip = clip.set_fps(config.VIDEO_FPS)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path  = str(OUTPUT_DIR / f"noorpost_{timestamp}.mp4")

    clip.write_videofile(
        out_path,
        codec="libx264",
        audio=False,
        logger=None,
        ffmpeg_params=["-pix_fmt", "yuv420p"],
    )

    print(f"[Video] ✅ Saved: {out_path}")
    return out_path

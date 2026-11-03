"""
repurpose_packager.py — Complete Content Packaging Engine for NoorPost Ultimate
Generates high-contrast 1080x1920 thumbnail covers and platform-optimized captions.

Principles:
- Thumbnails feature bold, legible typography and safe margins matching the chosen theme.
- Captions strictly attribute the original source, channel, and timestamps.
- Avoids exaggerated clickbait or unverified theological claims.
"""

import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from logger import log
from themes import resolve_theme, draw_8point_star
from caption_engine import get_hashtags
import config

class RepurposePackager:
    """Creates thumbnail covers and social media captions for repurposed video clips."""

    def extract_keyframe(self, video_path: str, timestamp_sec: float = 2.0) -> Image.Image:
        """Extract a single video frame as a PIL Image using FFmpeg."""
        v_path = Path(video_path).resolve()
        cmd = [
            "ffmpeg", "-y",
            "-ss", f"{timestamp_sec:.2f}",
            "-i", str(v_path),
            "-vframes", "1",
            "-f", "image2pipe",
            "-vcodec", "png",
            "-"
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            import io
            return Image.open(io.BytesIO(res.stdout)).convert("RGB")
        except Exception as e:
            log(f"⚠️  FFmpeg keyframe extraction failed: {e}. Generating procedural cover.", level="WARNING")
            return Image.new("RGB", (1080, 1920), color=(15, 20, 25))

    def generate_thumbnail(
        self,
        video_path: str,
        headline: str,
        theme_name: str = "midnight-gold",
        output_path: Optional[str] = None,
        badge_text: str = "ISLAMIC REMINDER"
    ) -> str:
        """
        Create 1080x1920 thumbnail cover with headline banner and theme styling.
        """
        theme = resolve_theme(theme_name)
        v_path = Path(video_path).resolve()
        out_p = Path(output_path) if output_path else config.PREVIEWS_DIR / f"preview_{v_path.stem}.jpg"
        out_p.parent.mkdir(parents=True, exist_ok=True)

        # 1. Extract video frame (at 20% or 2s)
        base_frame = self.extract_keyframe(str(v_path), timestamp_sec=2.0)
        # Resize to fit 1080x1920
        frame_cover = base_frame.resize((1080, 1920), Image.Resampling.LANCZOS)

        # 2. Add subtle dark gradient overlay for text readability
        overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
        draw_ov = ImageDraw.Draw(overlay)

        # Top banner gradient
        for y in range(350):
            alpha = int(210 * (1 - y / 350))
            draw_ov.line([(0, y), (1080, y)], fill=(0, 0, 0, alpha))

        # Bottom card background
        card_top = 1350
        card_bottom = 1750
        draw_ov.rectangle([(40, card_top), (1040, card_bottom)], fill=(10, 15, 20, 220), outline=theme["accent"], width=3)

        # Draw decorative stars
        draw_8point_star(draw_ov, (100, card_top + 45), radius=16, fill_color=theme["accent"])
        draw_8point_star(draw_ov, (980, card_top + 45), radius=16, fill_color=theme["accent"])

        # Composite frame and overlay
        img = Image.alpha_composite(frame_cover.convert("RGBA"), overlay).convert("RGB")
        draw = ImageDraw.Draw(img)

        # 3. Typography
        try:
            font_badge = ImageFont.truetype(str(config.FONT_ENGLISH), 26)
            font_headline = ImageFont.truetype(str(config.FONT_ENGLISH_BOLD if hasattr(config, 'FONT_ENGLISH_BOLD') else config.FONT_ENGLISH), 44)
        except Exception:
            font_badge = ImageFont.load_default()
            font_headline = ImageFont.load_default()

        # Render Badge
        draw.text((540, card_top + 45), badge_text, fill=theme["accent"], font=font_badge, anchor="mm")

        # Wrap headline
        wrapped_lines = self._wrap_text(headline, max_chars=28)
        text_y = card_top + 110
        for line in wrapped_lines[:3]:
            draw.text((540, text_y), line, fill=(255, 255, 255), font=font_headline, anchor="mm")
            text_y += 55

        # Render NoorPost watermark
        try:
            font_wm = ImageFont.truetype(str(config.FONT_ENGLISH), 22)
        except Exception:
            font_wm = ImageFont.load_default()
        draw.text((540, card_bottom - 35), "NOORPOST ULTIMATE", fill=(180, 180, 180), font=font_wm, anchor="mm")

        img.save(str(out_p), "JPEG", quality=92)
        log(f"🖼️  Clip thumbnail generated: {out_p.name}")
        return str(out_p)

    def _wrap_text(self, text: str, max_chars: int = 28) -> List[str]:
        words = text.split()
        lines = []
        cur = []
        cur_len = 0
        for w in words:
            if cur_len + len(w) + 1 > max_chars and cur:
                lines.append(" ".join(cur))
                cur = [w]
                cur_len = len(w)
            else:
                cur.append(w)
                cur_len += len(w) + 1
        if cur:
            lines.append(" ".join(cur))
        return lines

    def generate_repurpose_caption(
        self,
        clip_title: str,
        source_title: str,
        channel: str,
        transcript_snippet: str,
        category: str = "short_reminders",
        custom_tags: Optional[List[str]] = None
    ) -> str:
        """
        Generate social media caption attributing the original creator and lecture.
        """
        tags = get_hashtags(category, custom_tags=custom_tags, max_tags=7)

        caption = (
            f"✨ {clip_title.upper()}\n\n"
            f"🎙️ Speaker / Channel: {channel}\n"
            f"📖 Source: {source_title}\n\n"
            f"💬 Key Takeaway:\n\"{transcript_snippet}\"\n\n"
            f"Take a moment to reflect and apply this in your daily walk with Allah. 🤍\n\n"
            f"Save this reel and share with someone who may benefit!\n\n"
            f"{tags}"
        )
        return caption

packager_engine = RepurposePackager()

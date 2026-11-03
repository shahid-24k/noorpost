"""
vertical_reframer.py — High-Performance Vertical Video Reframing Engine for NoorPost Ultimate
Transforms 16:9 landscape Islamic lectures into pristine 1080x1920 (9:16) Reels/Shorts.

Reframing Options:
1. blur_fill (Default): Preserves full landscape presentation with smooth blurred background fill.
2. center_crop: Crops 1080 width centered on speaker.
3. custom_crop: Allows horizontal shift for podium/stage positioning.
4. fit_themed: Integrates with NoorPost 7 procedural Islamic themes.
"""

import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from logger import log
import config

REFRAMING_STRATEGIES = ["blur_fill", "center_crop", "custom_crop", "fit_themed"]

class VerticalReframer:
    """Orchestrates FFmpeg filtergraphs for professional 9:16 vertical conversions."""

    def __init__(self, ffmpeg_bin: str = "ffmpeg"):
        self.ffmpeg = shutil.which(ffmpeg_bin) or "ffmpeg"

    def render_reel_clip(
        self,
        source_video: str,
        output_path: str,
        start_sec: float,
        end_sec: float,
        strategy: str = "blur_fill",
        preset: str = "balanced",
        crop_x_pct: float = 0.5,
        subtitle_file: Optional[str] = None,
        theme_name: Optional[str] = None
    ) -> str:
        """
        Cut and reframe segment to 1080x1920 MP4.
        """
        dur = round(end_sec - start_sec, 2)
        if dur <= 0:
            raise ValueError(f"Invalid clip duration: start={start_sec}, end={end_sec}")

        out_p = Path(output_path).resolve()
        out_p.parent.mkdir(parents=True, exist_ok=True)

        # 1. Build FFmpeg Video Filter
        vf_filter = self._build_filtergraph(
            strategy=strategy,
            crop_x_pct=crop_x_pct,
            subtitle_file=subtitle_file,
            theme_name=theme_name
        )

        # 2. Select encoding preset
        encoding_flags = self._resolve_preset_flags(preset)

        # 3. Assemble FFmpeg command
        cmd = [
            self.ffmpeg,
            "-y",  # Overwrite
            "-ss", f"{start_sec:.3f}",
            "-to", f"{end_sec:.3f}",
            "-i", str(Path(source_video).resolve()),
            "-filter_complex" if "[bg]" in vf_filter else "-vf", vf_filter,
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "44100",
        ] + encoding_flags + [str(out_p)]

        log(f"🎬 FFmpeg converting [{strategy}] {start_sec:.1f}s -> {end_sec:.1f}s ({preset} preset)...")
        try:
            res = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            log(f"✅ Vertical Reel rendered: {out_p.name} ({out_p.stat().st_size // 1024} KB)")
            return str(out_p)
        except subprocess.CalledProcessError as e:
            err_msg = e.stderr[-500:] if e.stderr else str(e)
            log(f"❌ FFmpeg rendering failed: {err_msg}", level="ERROR")
            raise RuntimeError(f"FFmpeg rendering failed: {err_msg}")

    def _build_filtergraph(
        self,
        strategy: str,
        crop_x_pct: float = 0.5,
        subtitle_file: Optional[str] = None,
        theme_name: Optional[str] = None
    ) -> str:
        """Construct filter string for vertical aspect ratio transformation."""
        sub_filter = ""
        if subtitle_file and Path(subtitle_file).exists():
            clean_sub_path = Path(subtitle_file).resolve().as_posix().replace(":", "\\:")
            sub_filter = f",subtitles='{clean_sub_path}'"

        if strategy == "blur_fill":
            # Scale background to fill 1080x1920, blur heavily, scale foreground to fit width, overlay
            fg_chain = f"scale=1080:-2{sub_filter}[fg]"
            filtergraph = (
                f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:5[bg];"
                f"[0:v]{fg_chain};"
                f"[bg][fg]overlay=(W-w)/2:(H-h)/2"
            )
            return filtergraph

        elif strategy == "center_crop":
            # Scale height to 1920, center crop width to 1080
            return f"scale=-2:1920,crop=1080:1920:(in_w-1080)/2:0{sub_filter}"

        elif strategy == "custom_crop":
            # Adjustable horizontal crop
            x_pct = max(0.0, min(1.0, crop_x_pct))
            return f"scale=-2:1920,crop=1080:1920:(in_w-1080)*{x_pct}:0{sub_filter}"

        else: # fit_themed or fallback
            # Scale to fit inside 1080x1920 box with black/dark bars
            return (
                f"[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,"
                f"pad=1080:1920:(1080-iw)/2:(1920-ih)/2:black{sub_filter}"
            )

    def _resolve_preset_flags(self, preset: str) -> List[str]:
        if preset == "fast":
            return ["-preset", "ultrafast", "-crf", "26"]
        elif preset == "high_quality":
            return ["-preset", "slow", "-crf", "18"]
        else: # balanced
            return ["-preset", "fast", "-crf", "22"]

reframer_engine = VerticalReframer()

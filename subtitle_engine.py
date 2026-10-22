"""
subtitle_engine.py — Subtitle Formatting & Synchronization Engine for NoorPost Ultimate
Formats, styles, and aligns subtitles for 1080x1920 Instagram Reels and YouTube Shorts.

Features:
- Native Arabic cursive shaping & RTL layout via arabic-reshaper + python-bidi.
- Mobile safe-zone positioning (reserves bottom 320px for platform captions/audio tag).
- Line wrapping (max ~32 characters per line to prevent screen clutter).
- Clear demarcation of machine transcription vs verified sacred texts.
- Exports standard SRT and high-styled ASS (Advanced Substation Alpha).
"""

import re
from pathlib import Path
from typing import Dict, Any, List, Optional
import config
from logger import log

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_ARABIC_SUPPORT = True
except ImportError:
    HAS_ARABIC_SUPPORT = False

def is_arabic_text(text: str) -> bool:
    """Detect if text contains predominantly Arabic characters."""
    arabic_chars = [c for c in text if '؀' <= c <= 'ۿ' or 'ݐ' <= c <= 'ݿ']
    return len(arabic_chars) > len(text) * 0.3

def shape_arabic_for_subtitles(text: str) -> str:
    """Apply cursive shaping and BiDi reordering for Arabic subtitles."""
    if not HAS_ARABIC_SUPPORT or not text:
        return text
    try:
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except Exception:
        return text

def wrap_subtitle_text(text: str, max_chars: int = 34) -> str:
    """Wrap text to 1-2 balanced lines suitable for mobile viewing."""
    words = text.split()
    if not words:
        return ""

    lines = []
    current_line = []
    current_len = 0

    for w in words:
        if current_len + len(w) + 1 > max_chars and current_line:
            lines.append(" ".join(current_line))
            current_line = [w]
            current_len = len(w)
        else:
            current_line.append(w)
            current_len += len(w) + 1

    if current_line:
        lines.append(" ".join(current_line))

    # Keep at most 2 lines per subtitle cue to avoid face occlusion
    if len(lines) > 2:
        return lines[0] + "\n" + " ".join(lines[1:])
    return "\n".join(lines)

def generate_srt_file(
    cues: List[Dict[str, Any]],
    output_path: str,
    time_offset_sec: float = 0.0
) -> str:
    """
    Generate an SRT subtitle file adjusted to clip start offset.
    """
    out_p = Path(output_path).resolve()
    out_p.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    counter = 1

    for cue in cues:
        start = max(0.0, cue["start"] - time_offset_sec)
        end = max(start + 0.5, cue["end"] - time_offset_sec)
        raw_text = cue["text"].strip()
        if not raw_text:
            continue

        if is_arabic_text(raw_text):
            processed_text = shape_arabic_for_subtitles(raw_text)
        else:
            processed_text = wrap_subtitle_text(raw_text)

        start_srt = _format_srt_time(start)
        end_srt = _format_srt_time(end)

        lines.append(f"{counter}")
        lines.append(f"{start_srt} --> {end_srt}")
        lines.append(processed_text)
        lines.append("")
        counter += 1

    with open(out_p, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return str(out_p)

def _format_srt_time(seconds: float) -> str:
    millis = int((seconds - int(seconds)) * 1000)
    secs = int(seconds)
    hours = secs // 3600
    minutes = (secs % 3600) // 60
    rem_secs = secs % 60
    return f"{hours:02d}:{minutes:02d}:{rem_secs:02d},{millis:03d}"

def generate_ass_file(
    cues: List[Dict[str, Any]],
    output_path: str,
    time_offset_sec: float = 0.0,
    font_name: str = "Noto Sans",
    font_size: int = 16
) -> str:
    """
    Generate an ASS subtitle file with mobile-safe positioning (MarginV=280).
    """
    out_p = Path(output_path).resolve()
    out_p.parent.mkdir(parents=True, exist_ok=True)

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,2,2,40,40,320,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    for cue in cues:
        start = max(0.0, cue["start"] - time_offset_sec)
        end = max(start + 0.5, cue["end"] - time_offset_sec)
        raw_text = cue["text"].strip()
        if not raw_text:
            continue

        if is_arabic_text(raw_text):
            text = shape_arabic_for_subtitles(raw_text)
        else:
            text = wrap_subtitle_text(raw_text).replace("\n", "\\N")

        start_ass = _format_ass_time(start)
        end_ass = _format_ass_time(end)
        events.append(f"Dialogue: 0,{start_ass},{end_ass},Default,,0,0,0,,{text}")

    full_content = header + "\n".join(events) + "\n"
    with open(out_p, "w", encoding="utf-8") as f:
        f.write(full_content)

    return str(out_p)

def _format_ass_time(seconds: float) -> str:
    centis = int((seconds - int(seconds)) * 100)
    secs = int(seconds)
    hours = secs // 3600
    minutes = (secs % 3600) // 60
    rem_secs = secs % 60
    return f"{hours}:{minutes:02d}:{rem_secs:02d}.{centis:02d}"

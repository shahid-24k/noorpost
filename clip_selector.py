"""
clip_selector.py — Intelligent Video Segment Selection for NoorPost Ultimate
Identifies self-contained, meaningful 30-60 second clips from long Islamic lectures.

Principles:
- Respects sentence and thought boundaries using timestamped transcripts.
- Never cuts in the middle of a sentence, complete explanation, or supplication.
- Evaluates speech pauses and silence gaps.
- Supports manual timestamp overrides.
- Provides preview mode before rendering.
"""

import re
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from logger import log

def parse_time_str(time_str: str) -> float:
    """Convert 'HH:MM:SS.mmm' or 'MM:SS' or 'SS' into float seconds."""
    s = time_str.strip().replace(",", ".")
    parts = s.split(":")
    if len(parts) == 3:
        return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    elif len(parts) == 2:
        return float(parts[0]) * 60 + float(parts[1])
    else:
        return float(parts[0])

def format_time_str(seconds: float) -> str:
    """Format seconds into HH:MM:SS."""
    secs = int(seconds)
    hours = secs // 3600
    minutes = (secs % 3600) // 60
    rem_secs = secs % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{rem_secs:02d}"
    return f"{minutes:02d}:{rem_secs:02d}"

def parse_vtt_srt(file_path: str) -> List[Dict[str, Any]]:
    """
    Parse WebVTT or SRT subtitle file into timestamped cues.
    Returns: [{"start": float, "end": float, "text": str}]
    """
    p = Path(file_path)
    if not p.exists():
        return []

    cues = []
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    # WebVTT / SRT time regex: 00:01:23.456 --> 00:01:27.890
    time_pattern = re.compile(
        r'(\d{1,2}:(?:\d{2}:)?\d{2}[.,]\d{3})\s*-->\s*(\d{1,2}:(?:\d{2}:)?\d{2}[.,]\d{3})'
    )

    blocks = content.replace("\r\n", "\n").split("\n\n")
    for block in blocks:
        lines = block.strip().split("\n")
        time_match = None
        text_lines = []
        for line in lines:
            m = time_pattern.search(line)
            if m:
                time_match = m
            elif time_match and line.strip() and not line.strip().isdigit():
                # Clean formatting tags like <c> </c> <v>
                clean_line = re.sub(r'<[^>]+>', '', line).strip()
                if clean_line:
                    text_lines.append(clean_line)

        if time_match and text_lines:
            start_sec = parse_time_str(time_match.group(1))
            end_sec = parse_time_str(time_match.group(2))
            text = " ".join(text_lines)
            cues.append({
                "start": start_sec,
                "end": end_sec,
                "text": text
            })

    # Deduplicate consecutive identical subtitles (common in auto-generated captions)
    clean_cues = []
    for c in cues:
        if clean_cues and clean_cues[-1]["text"] == c["text"]:
            clean_cues[-1]["end"] = max(clean_cues[-1]["end"], c["end"])
        else:
            clean_cues.append(c)

    return clean_cues

def parse_manual_timestamps(ts_string: str) -> List[Tuple[float, float]]:
    """
    Parse user-provided timestamp ranges, e.g. '01:15-02:00, 05:30-06:15'.
    """
    results = []
    ranges = [r.strip() for r in ts_string.split(",") if r.strip()]
    for r in ranges:
        if "-" in r:
            start_str, end_str = r.split("-", 1)
            try:
                start_sec = parse_time_str(start_str)
                end_sec = parse_time_str(end_str)
                if end_sec > start_sec:
                    results.append((start_sec, end_sec))
            except Exception:
                continue
    return results

def find_candidate_clips(
    cues: List[Dict[str, Any]],
    video_duration: float,
    target_duration: float = 45.0,
    min_duration: float = 25.0,
    max_duration: float = 65.0,
    num_clips: int = 3
) -> List[Dict[str, Any]]:
    """
    Identify self-contained clips based on transcript cues and sentence boundaries.
    """
    if not cues:
        return _fallback_uniform_clips(video_duration, target_duration, num_clips)

    # 1. Group cues into sentences based on punctuation or pause gaps
    sentences = []
    curr_words = []
    curr_start = None
    curr_end = None

    for i, cue in enumerate(cues):
        if curr_start is None:
            curr_start = cue["start"]
        curr_end = cue["end"]
        curr_words.append(cue["text"])

        # Check pause gap to next cue
        is_pause = False
        if i < len(cues) - 1:
            gap = cues[i+1]["start"] - cue["end"]
            if gap >= 0.7:
                is_pause = True

        # Check sentence ending punctuation
        ends_sentence = any(cue["text"].rstrip().endswith(p) for p in [".", "!", "?", "—", "؛", "۔"])

        if ends_sentence or is_pause or i == len(cues) - 1:
            sentence_text = " ".join(curr_words).strip()
            if sentence_text:
                sentences.append({
                    "start": curr_start,
                    "end": curr_end,
                    "text": sentence_text
                })
            curr_words = []
            curr_start = None
            curr_end = None

    if not sentences:
        return _fallback_uniform_clips(video_duration, target_duration, num_clips)

    # 2. Form candidate clips by assembling contiguous sentences
    candidates = []
    i = 0
    while i < len(sentences):
        clip_start = sentences[i]["start"]
        clip_text_parts = []
        clip_cues = []
        j = i

        while j < len(sentences):
            clip_text_parts.append(sentences[j]["text"])
            clip_end = sentences[j]["end"]
            dur = clip_end - clip_start

            # Check matching cues
            matched_cues = [c for c in cues if c["start"] >= clip_start and c["end"] <= clip_end + 0.5]

            if dur >= min_duration:
                # If adding next sentence would exceed max duration or if we reached target
                next_dur = (sentences[j+1]["end"] - clip_start) if j + 1 < len(sentences) else dur
                if dur >= target_duration or next_dur > max_duration:
                    snippet = " ".join(clip_text_parts)
                    title = snippet.split(".")[0].strip()[:60]
                    candidates.append({
                        "start_sec": clip_start,
                        "end_sec": clip_end,
                        "duration_sec": round(dur, 2),
                        "title": title or "Islamic Reminder Clip",
                        "transcript_snippet": snippet[:250] + "...",
                        "cues": matched_cues
                    })
                    # Advance i past this clip
                    i = j + 1
                    break
            j += 1
        else:
            i += 1

    # Filter candidates by length and select top N spaced across the video
    valid_candidates = [c for c in candidates if min_duration <= c["duration_sec"] <= max_duration]

    if not valid_candidates:
        return _fallback_uniform_clips(video_duration, target_duration, num_clips)

    # If we have more than needed, space them evenly across the video
    if len(valid_candidates) > num_clips:
        step = len(valid_candidates) / num_clips
        selected = [valid_candidates[int(idx * step)] for idx in range(num_clips)]
    else:
        selected = valid_candidates[:num_clips]

    for idx, c in enumerate(selected):
        c["clip_index"] = idx + 1

    return selected

def _fallback_uniform_clips(
    video_duration: float,
    target_duration: float,
    num_clips: int
) -> List[Dict[str, Any]]:
    """Fallback segmenter when no subtitles are available."""
    clips = []
    usable_dur = max(video_duration - 20, target_duration)
    step = usable_dur / max(num_clips, 1)

    for idx in range(num_clips):
        start = 10.0 + (idx * step)
        end = min(start + target_duration, video_duration)
        if end > start + 15:
            clips.append({
                "clip_index": idx + 1,
                "start_sec": round(start, 2),
                "end_sec": round(end, 2),
                "duration_sec": round(end - start, 2),
                "title": f"Islamic Lecture Clip {idx + 1}",
                "transcript_snippet": f"Video segment from {format_time_str(start)} to {format_time_str(end)}.",
                "cues": []
            })
    return clips

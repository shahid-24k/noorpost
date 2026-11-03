---
name: long-video-to-reels
description: Workflow and best practices for repurposing long Islamic lectures, khutbahs, and recitations into high-engagement vertical Reels and Shorts.
---

# Long Video to Reels Skill

## Overview
Automates turning 15-90 minute Islamic lectures, khutbahs, and recitations into 30-60s self-contained vertical video clips.

## Guidelines
1. **Rights & Permission**: Verify source video is authorized/owned before processing.
2. **Segment Selection**:
   - Extract timestamped subtitles/transcripts via `yt-dlp` or local VTT/SRT.
   - Detect natural speech pauses and sentence boundaries.
   - Never cut mid-sentence, mid-ayah, or mid-dua.
   - Target duration: 30–60 seconds per clip.
3. **Clip Packaging**:
   - Vertical reframing (1080x1920, 9:16).
   - Styled subtitles with platform safe zones.
   - Engaging headline thumbnail matching NoorPost visual themes.
   - Contextual caption with source attribution and relevant hashtags.

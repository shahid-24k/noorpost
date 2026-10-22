---
name: ffmpeg-vertical-reframer
description: High-performance FFmpeg filtergraphs for converting 16:9 landscape video to 1080x1920 (9:16) vertical video using blurred background fill, center cropping, and subtitle overlay.
---

# FFmpeg Vertical Reframer Skill

## Core Reframing Strategies
1. **Blurred Background Filling (`blur_fill`)**:
   - Scales original 16:9 video to fit width (1080x608), sharp in center.
   - Scales and heavily blurs another copy to fill background (1080x1920).
   - Filtergraph: `[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:5[bg];[0:v]scale=1080:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2`
   - Best for: Lectures with slides, wide mosque shots, multiple speakers.

2. **Center Crop (`center_crop`)**:
   - Scales height to 1920 and crops center 1080px.
   - Filtergraph: `scale=-2:1920,crop=1080:1920:(in_w-1080)/2:0`
   - Best for: Centered podium speaker / single lecturer.

3. **Themed Background Fit (`fit_themed`)**:
   - Places 16:9 video inside NoorPost 1080x1920 canvas with Islamic theme ornaments.

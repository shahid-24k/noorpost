# Alternative Vocal-Only Nasheed Sources & Licensing Report

**Project**: NoorPost Ultimate  
**Policy**: Strict Copyright Safety & Islamic Compliance (Vocals Only, Acapella / Instrumental-Free, No Background Music on Quranic Verses)  
**Date**: November 3, 2026  

---

## Executive Summary

While awaiting formal written confirmation from Halal Tunes (`halal.tunes@my.com`), an evaluation of alternative vocal-only audio platforms was conducted to identify backup sources that provide explicit commercial and social media reuse clearances.

---

## 1. Aswati Studio (`https://aswati.co`)
- **Nature**: Specialized vocal-only, instrument-free background audio library for Islamic media creators.
- **Licensing Model**:
  - **Free Starter Pack**: ~8 full-length vocal audio beds cleared for social media creators with zero cost.
  - **Commercial Clearance**: Royalty-free content license specifically covering monetized YouTube, Instagram Reels, and TikTok.
  - **Attribution Policy**: Attribution is optional on licensed tiers, recommended on free starter packs.
  - **Suitability for NoorPost**: **High**. Provides studio-quality acapella beds with no instruments, avoiding Content ID strikes on Meta and YouTube platforms.

---

## 2. NoCopyrightNasheeds (NCN) (`https://nocopyrightnasheeds.com`)
- **Nature**: Curated network distributing royalty-free vocal-only nasheed tracks by emerging Muslim vocal artists.
- **Licensing Model**:
  - **Free Usage with Mandatory Attribution**: Tracks can be used freely across social platforms provided the exact attribution block is copied into the caption/description.
  - **Required Caption Template**:
    ```text
    Track: [Nasheed Name] - [Artist Name]
    Music provided by NoCopyrightNasheeds
    Watch: [YouTube Link]
    ```
  - **Commercial Terms**: Permitted for monetized and non-monetized creator posts provided attribution is preserved.
  - **Suitability for NoorPost**: **Moderate-High**. Works well with NoorPost's caption engine, which automatically appends track-specific credits to post text.

---

## 3. NUR Vocals (`https://nurvocals.com`)
- **Nature**: Contemporary acapella vocal library for Muslim brands and filmmakers.
- **Licensing Model**:
  - **Paid / Perpetual Commercial Tier**: Single-track purchase or subscription providing perpetual social media and broadcast clearance.
  - **Attribution**: None required.
  - **Suitability for NoorPost**: High technical quality, but requires paid licensing purchase (which is deferred until explicit user approval).

---

## 4. Wikimedia Commons / Free Music Archive (Public Domain Islamic Chants)
- **Nature**: Historical public-domain acapella talbiya, adhan recordings, and traditional vocal salawat.
- **Licensing Model**: CC0 (Public Domain) or CC-BY 4.0.
- **Suitability for NoorPost**: Completely free of copyright claims, but limited selection of ambient background beds.

---

## Policy Safeguards Maintained in NoorPost Engine
1. **Quranic Recitation Sanctity**: `nasheed_engine.py` inspects `content_item["category"]` and `content_item["type"]`. Any recitation of the Qur'an automatically disables background audio, overriding all catalog tracks.
2. **Speech Intelligibility Attenuation**: For lectures and spoken reflections, audio volume is attenuated from `0.35` down to `0.12`.
3. **Silent Audio Fallback**: If no track possesses an explicit `"approval_status": "APPROVED"`, NoorPost strictly renders with silent background audio (`silence.mp3`) rather than risk an unverified copyright claim.


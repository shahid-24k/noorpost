# Islamic Lecture Repurposing Authorization Policy

**Project**: NoorPost Ultimate  
**Policy Objective**: Prevent unauthorized redistribution of third-party intellectual property and protect Islamic content creators.  
**Date**: November 3, 2026  

---

## 1. Fundamental Principle
**Public availability on YouTube does NOT imply reuse permission.**

Under YouTube's Terms of Service and standard intellectual property law, uploading a lecture or khutbah to YouTube grants YouTube a hosting license, but does NOT grant third parties the right to download, reframe, re-edit, or republish the content on Instagram Reels without explicit consent.

---

## 2. Permitted Authorization Types
A lecture source may ONLY be marked `RIGHTS_CONFIRMED = YES` in `approved_channels.txt` or `source_queue.txt` under one of the following verifiable conditions:

### Condition A: Express Written Creator Consent
- Direct written permission (email, letter, or direct message agreement) from the speaker or producing organization granting NoorPost authorization to repurpose lectures into short educational clips.
- Written records must be archived in `assets/sources/permissions/`.

### Condition B: Creative Commons Attribution License (CC BY)
- The video is officially published on YouTube by the original copyright holder under the **Creative Commons Attribution license (reuse allowed)**.
- Full creator attribution and original source link must accompany every excerpt.

### Condition C: Explicit Public Open-Access / Dawah Reuse Policy
- The organization (e.g. university open courseware or designated open dawah resource) maintains an official terms-of-use page explicitly stating that short clips and summaries are encouraged for educational Dawah.

---

## 3. Strict Code-Level Enforcement in NoorPost
1. **No Silent Overrides**: The global CLI flag `--confirm-rights` CANNOT override a source with missing or negative authorization.
2. **Independent Record Verification**: `autopilot.py` examines the source entry directly. If `rights_confirmed` is not positive in the queue or channel registry, processing is blocked with a `PermissionError`.
3. **Automated Discovery Inactivity**: `channel_discovery.py` will never automatically query or queue videos from channels unless they are listed in `approved_channels.txt` with `RIGHTS_CONFIRMED == YES`.
4. **Rate Limiting**: Daily production runs limit extra lecture processing to a maximum of 1 clip per run (`MAX_LECTURE_REELS_PER_RUN = 1`) to prioritize authentic Hadiths and Duas.


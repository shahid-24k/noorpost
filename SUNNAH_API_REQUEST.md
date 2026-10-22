# Official Sunnah.com API Access Request

This document details the official API access request for **NoorPost Ultimate**, prepared in accordance with the official [Sunnah.com Developer Guidelines](https://sunnah.com) and the [sunnah-com/api GitHub issue template](https://github.com/sunnah-com/api/issues).

---

## 1. Request Overview

- **Target Repository:** [sunnah-com/api](https://github.com/sunnah-com/api/issues)
- **Action Required:** Open a new GitHub Issue using the template below.
- **Single Missing Step:** Because agentic environments do not have the user's personal GitHub login or personal contact email, the user must submit the issue below using their own authenticated GitHub account and email address.

---

## 2. Issue Submission Template

**Issue Title:**
```text
API Key Request for NoorPost (Islamic Educational Video & Hadith Attribution Engine)
```

**Issue Body:**
```markdown
- **Please tell us about yourself (include an email address):**
  Name: [YOUR NAME]
  Role: Creator / Developer of NoorPost Ultimate
  Email: [YOUR CONTACT EMAIL]
  GitHub: [YOUR GITHUB USERNAME]

- **Your purpose in using this API:**
  NoorPost is an open-source, non-commercial Islamic educational content platform that automatically produces short-form educational videos (Reels / Shorts) featuring verified Sahih Hadith, daily supplications, and prophetic teachings.

  We require the official Sunnah.com API to:
  1. Programmatically fetch individual verified Hadith with their authentic Arabic text and English translations.
  2. Display exact collection references (collection name, book number, Hadith number) and authenticity gradings (e.g., Sahih al-Bukhari, Sahih Muslim, or explicit Sahih evaluations by recognized muhaddithin like Shaykh al-Albani or Darussalam).
  3. Include clear, visible on-screen and in-caption attribution back to Sunnah.com for every displayed narration.
  4. Ensure strict authenticity: our system automatically rejects any unverified, missing-grade, Da'if, or fabricated narrations.

- **API rate limits:**
  - Maximum requests per second: 1 request/sec (NoorPost batches queries and caches all fetched records locally to minimize server load).
  - Maximum requests per day: 10–50 requests/day (used only during scheduled educational video generation cycles).

- **Is your use case better served by having an offline dump of hadith data or programmatic API access?**
  Programmatic API access with local caching. We fetch specific Hadith narrations on demand for educational video generation and cache them locally according to terms of service.

- **What are the languages in which you would like hadith data?**
  Arabic (original text) and English (translation).

- **What programming language will your API client be in?**
  Python 3.10+ (using standard HTTPS requests with `x-api-key` header).
```

---

## 3. Secret Storage & Local Configuration

Once the Sunnah.com team approves the request and issues your API key:

1. **GitHub Actions Secret:**
   - In your GitHub repository: Go to **Settings** → **Secrets and variables** → **Actions**.
   - Click **New repository secret**.
   - Name: `SUNNAH_API_KEY`
   - Value: `<Your Issued Sunnah.com API Key>`

2. **Local Development (.env):**
   Add to `D:\noorpost\.env`:
   ```env
   SUNNAH_API_KEY=your_issued_api_key_here
   ```

3. **Security Guarantee:**
   - The key is **never** committed to Git, logs, generated video metadata, or repository files.
   - If `SUNNAH_API_KEY` is not configured, the system operates in offline fallback mode using verified canonical local content and skips external Hadith fetching safely.

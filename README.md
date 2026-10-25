# NOORPOST ULTIMATE 🌙
بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ

**NoorPost Ultimate** is an automated, authentic Islamic Reels production system engineered to create and publish high-definition 1080×1920 (9:16) vertical videos for Instagram Reels and YouTube Shorts.

It bridges automated content creation with your existing **Dropbox → Make.com → Instagram Reels** distribution workflow.

---

## 🌟 Key Features

1. **Automated Scheduled Production**:
   - Two daily production runs at **08:00 AM IST** (`30 2 * * *` UTC) and **09:00 PM IST** (`30 15 * * *` UTC) via GitHub Actions.
   - Rotates through verified Duas, morning/evening Adhkar, authentic Sahih Hadiths, and Quranic reflections across 13 canonical categories.

2. **Intelligent Lecture-to-Reels Repurposing**:
   - Converts authorized long-form Islamic lectures, khutbahs, and recitations into high-engagement vertical Reels.
   - **Aspect Ratio & Reframing**: Converts 16:9 to 9:16 using high-performance blurred background fill (`blur_fill`), center-cropping, or custom offsets without face stretching.
   - **Subtitles**: Platform-safe subtitles (SRT/ASS) with automatic RTL Arabic text shaping (`Amiri-Regular.ttf`) and safe margin buffers against Instagram UI overlays.
   - **Publishing Package**: Each clip generates the final `.mp4` video, structured attribution caption (`_caption.txt`), and 1080×1920 thumbnail cover (`previews/preview_<name>.jpg`).

3. **Source Discovery & Queue Processing**:
   - **Manual Source Queue (`source_queue.txt`)**: Supports structured entries with URL/path, creator, confirmed rights, and preferred timestamp ranges.
   - **Approved Channel Discovery (`approved_channels.txt`)**: Discovers recent uploads from authorized YouTube channels via official Atom RSS feeds without scraping.
   - **Configurable Lecture Limit**: `MAX_LECTURE_REELS_PER_RUN` (default: 1) prevents runaway rendering or rate-limiting.

4. **Strict Religious Authenticity**:
   - **Quran**: Verified Surah names, numbers, Ayah references, and translations.
   - **Duas**: Sourced with authenticated chapter and book references.
   - **Hadith**: Integrates the official Sunnah.com API with a curated, verified local Sahih collection fallback. Never fabricates citations or authenticity grades.

5. **Audio & Nasheed Engine**:
   - Manages authorized tracks via `assets/nasheeds/catalog.json`.
   - Supports custom personal audio files in `assets/audio/custom/`.
   - Strictly excludes unverified tracks from automatic use; falls back cleanly to silent audio without false caption attribution.

6. **Idempotent Cloud State Synchronization (Schema 2.0)**:
   - Synchronizes publication history, deduplication records, and queue status via Dropbox (`/NoorPost_State/noorpost_state.json`).
   - Stable content identifiers decoupled from local SQLite autoincrement IDs.
   - Usage counters merge with `MAX()` to ensure repeating runs or re-downloads never artificially inflate counts.
   - Fails closed on remote auth/network failures to prevent duplicate publications.
   - Dry runs strictly isolate production state.

---

## 🏗️ Architecture & Publishing Pipeline

```
[SCHEDULE / QUEUED LECTURE]
             │
             ▼
   [GITHUB ACTIONS RUNNER]
             │
   ├── 1. Pull Persistent State from Dropbox (/NoorPost_State)
   ├── 2. Select Authentic Content or Slice Queued Lecture Highlight
   ├── 3. Render 1080x1920 Vertical Video (H.264 / AAC)
   ├── 4. Generate Subtitles, Thumbnail Card & Attributed Caption
   └── 5. Safe Push State to Dropbox (on successful run only)
             │
             ▼
      [DROPBOX (/NoorPost)]
   ├── /NoorPost/<video>.mp4
   ├── /NoorPost/<video>_caption.txt
   └── /NoorPost/previews/<thumb>.jpg
             │
             ▼
   [EXISTING MAKE.COM SCENARIO]
   Watches /NoorPost folder ──► Reads video & caption ──► Publishes to Instagram Reels
```

---

## 🚀 Quick Start

### 1. Installation
```powershell
# Clone repository
git clone https://github.com/shahid-24k/noorpost.git
cd noorpost

# Setup environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configure Environment (`.env`)
```ini
DROPBOX_APP_KEY=your_key
DROPBOX_APP_SECRET=your_secret
DROPBOX_REFRESH_TOKEN=your_refresh_token
DROPBOX_FOLDER=/NoorPost

TIMEZONE=Asia/Kolkata
POST_TIMES=08:00, 21:00
MAX_LECTURE_REELS_PER_RUN=1
```

### 3. Generate a Test Preview (Dry-Run)
```powershell
# Generate a 5-second fast preview without uploading
python main.py --preview --category daily_duas --preset fast --duration 5
```

### 4. Run the Full Test Suite
```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

---

## 📖 Documentation Reference

For comprehensive setup, advanced configuration, visual theme specifications, reframing options, and troubleshooting, consult the [SETUP_GUIDE.md](file:///d:/noorpost/SETUP_GUIDE.md).

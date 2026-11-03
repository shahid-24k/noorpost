# NOORPOST ULTIMATE — SETUP & OPERATING GUIDE
بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ

NoorPost Ultimate is an intelligent, authentic Islamic content creation and automated video repurposing engine.
It generates high-definition 1080x1920 vertical videos (9:16) for Instagram Reels and YouTube Shorts via:
1. **Islamic Content Engine**: Verified daily duas, adhkar, Quranic verses, and Hadith across 13 canonical categories.
2. **Video Repurposing Engine**: Automated slicing of long-form Islamic lectures, khutbahs, and recitations into engaging, subtitled vertical Reels with thumbnails and captions, delivered directly to Dropbox for automated Make.com Instagram publishing.

---

## 📋 TABLE OF CONTENTS
1. [Prerequisites & Installation](#1-prerequisites--installation)
2. [Environment Configuration (.env)](#2-environment-configuration-env)
3. [The Dropbox & Make.com Publishing Workflow](#3-the-dropbox--makecom-publishing-workflow)
4. [Video Repurposing Engine (Long Video -> Vertical Reels)](#4-video-repurposing-engine-long-video---vertical-reels)
5. [Reframing Strategies (16:9 to 9:16)](#5-reframing-strategies-169-to-916)
6. [Subtitles & Arabic Text Shaping](#6-subtitles--arabic-text-shaping)
7. [Thumbnail Covers & Caption Packaging](#7-thumbnail-covers--caption-packaging)
8. [Queue Management & Duplicate Prevention](#8-queue-management--duplicate-prevention)
9. [13 Canonical Content Categories](#9-13-canonical-content-categories)
10. [Visual Themes & Presets](#10-visual-themes--presets)
11. [Command-Line Reference (CLI)](#11-command-line-reference-cli)
12. [NoorPost Autopilot (Automated Batch & Recurring Processing)](#12-noorpost-autopilot-automated-batch--recurring-processing)
13. [Automatic Approved-Channel Discovery](#13-automatic-approved-channel-discovery)
14. [GitHub Actions Production Automation](#14-github-actions-production-automation)
15. [State Synchronization & Deduplication (Schema 2.0)](#15-state-synchronization--deduplication-schema-20)
16. [Content Rotation & Religious Accuracy](#16-content-rotation--religious-accuracy)
17. [Nasheed & Audio Asset Integration](#17-nasheed--audio-asset-integration)
18. [GitHub Secrets Configuration](#18-github-secrets-configuration)
19. [Automated Testing & Verification](#19-automated-testing--verification)

---

## 1. PREREQUISITES & INSTALLATION

### System Requirements:
- Windows 10/11 (or macOS / Linux)
- Python 3.9+ (Python 3.10+ recommended)
- FFmpeg 6.0+ (with libx264, libass, libfribidi)

### Step 1: Open Windows PowerShell
Navigate to the project root:
```powershell
cd D:\noorpost
```

### Step 2: Set up a Python Virtual Environment (Recommended)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Step 3: Install Required Dependencies
```powershell
pip install -r requirements.txt
```

*Key dependencies:*
- `yt-dlp` (Authorized video & transcript ingestion)
- `Pillow` (HD graphic rendering & thumbnail composition)
- `arabic-reshaper` & `python-bidi` (Native Arabic cursive shaping and RTL layout)
- `moviepy` & `FFmpeg` (Video cutting, blurred background reframing, audio multiplexing)
- `APScheduler` (Background automation scheduler)
- `python-dotenv` (Secure environment configuration)
- `dropbox` (Cloud distribution for Make.com / Instagram)

---

## 2. ENVIRONMENT CONFIGURATION (.env)

```ini
# --- Dropbox & Make.com (Instagram Auto-Publishing) ---
DROPBOX_APP_KEY=your_dropbox_app_key
DROPBOX_APP_SECRET=your_dropbox_app_secret
DROPBOX_REFRESH_TOKEN=your_dropbox_refresh_token
DROPBOX_ACCESS_TOKEN=your_dropbox_access_token
DROPBOX_FOLDER=/NoorPost

# --- Automation Timing ---
TIMEZONE=Asia/Kolkata
POST_TIMES=08:00, 13:00, 17:00, 21:00

# --- Video Presets & Appearance ---
DEFAULT_THEME=midnight-gold
DEFAULT_LAYOUT=dua
DEFAULT_PRESET=balanced
VIDEO_DURATION=15
SHOW_TRANSLITERATION=True
ENABLE_ANIMATIONS=True

# --- Safety & Approval Controls ---
REQUIRE_APPROVAL=False
PREVIEW_ONLY=False
SKIP_YOUTUBE=True
```

---

## 3. THE DROPBOX & MAKE.COM PUBLISHING WORKFLOW

NoorPost Ultimate preserves your existing Dropbox + Make.com publishing pipeline:

```
[AUTHORIZED VIDEO SOURCE / LECTURE]
                │
                ▼
      [NOORPOST ULTIMATE]
                │
   ├── 1. Transcript-Based Segment Selection (30-60s)
   ├── 2. 1080x1920 Vertical Reframing (blur_fill / center_crop)
   ├── 3. Mobile-Safe Subtitles (SRT/ASS with Arabic shaping)
   ├── 4. Themed 1080x1920 Thumbnail (preview_<name>.jpg)
   └── 5. Attributed Caption & Hashtags (<name>_caption.txt)
                │
                ▼
      [DROPBOX (/NoorPost)]
   ├── /NoorPost/<video>.mp4          (Final vertical Reel)
   ├── /NoorPost/<video>_caption.txt  (Caption & hashtags)
   └── /NoorPost/previews/<thumb>.jpg (Thumbnail reference)
                │
                ▼
      [EXISTING MAKE.COM SCENARIO]
   Watches /NoorPost folder -> Reads video & caption -> Publishes to Instagram Reels
```

### Important Integration Rules:
1. **Never alter `DROPBOX_FOLDER`** unless your Make.com scenario is updated to watch the new path.
2. **File Pairing**: NoorPost uploads `<name>.mp4` and `<name>_caption.txt` in the exact folder structure Make.com expects.
3. **Thumbnail Isolation**: Preview thumbnails are placed in `/NoorPost/previews/` to prevent folder-watch triggers from mistaking a JPEG for a video file.
4. **Public Shared Links**: Shared links are generated automatically with `dbx.sharing_create_shared_link_with_settings()` for direct Instagram media ingestion.

---

## 4. VIDEO REPURPOSING ENGINE (LONG VIDEO -> VERTICAL REELS)

### Basic Usage:

#### 1. Repurposing an Authorized YouTube Lecture:
```powershell
python main.py --repurpose-url "https://www.youtube.com/watch?v=EXAMPLE" --confirm-rights
```

#### 2. Repurposing a Local Video File:
```powershell
python main.py --repurpose-file "D:\lectures\tafseer_fatihah.mp4"
```

#### 3. Batch Repurposing:
Create a text file `batch.txt` containing URLs or file paths:
```powershell
python main.py --batch batch.txt --confirm-rights
```

#### 4. Preview Segments Before Rendering:
```powershell
python main.py --repurpose-url "https://www.youtube.com/watch?v=EXAMPLE" --confirm-rights --preview-clips
```

---

## 5. REFRAMING STRATEGIES (16:9 TO 9:16)

When converting wide landscape video to vertical 1080x1920:

| Strategy | Flag | Description | Ideal For |
|---|---|---|---|
| `blur_fill` | `--reframing blur_fill` (Default) | Scales original video to fit 1080 width; backgrounds it with a blurred, darkened 1080x1920 copy | Lectures with slides, wide mosque shots, multiple speakers |
| `center_crop` | `--reframing center_crop` | Scales height to 1920 and center-crops 1080 width | Centered podium speaker or single lecturer |
| `custom_crop` | `--reframing custom_crop` | Uses custom X offset (e.g. speaker stands on left/right third) | Stage presentations with offset podiums |
| `fit_themed` | `--reframing fit_themed` | Centers video inside a 1080x1920 canvas using one of the 7 NoorPost Islamic themes | Educational clips with top/bottom decorative borders |

---

## 6. SUBTITLES & ARABIC TEXT SHAPING

- **Automatic Extraction**: Uses available subtitles or transcripts from YouTube (`en`, `ar`) or local `.vtt` / `.srt` files alongside the video.
- **Mobile Safe Zones**: Subtitles are positioned with a 320px bottom margin so Instagram caption and audio badges never obscure the text.
- **Arabic Text Shaping**: Automatically reshaped and rendered RTL using `Amiri-Regular.ttf`.
- **Face Occlusion Prevention**: Maximum 32–34 characters per line, at most 2 lines per cue.
- **Disable Subtitles**: Add `--no-subtitles` if you want clean video without burned text.

---

## 7. THUMBNAIL COVERS & CAPTION PACKAGING

Each generated clip receives a complete publishing package:

1. **Thumbnail Cover (`output_videos/previews/preview_<name>.jpg`)**:
   - 1080x1920 vertical format.
   - Keyframe extracted from speech.
   - High-contrast card with Islamic star ornaments matching the selected theme.
   - Bold, wrapped headline.
2. **Social Caption (`output_videos/<name>_caption.txt`)**:
   - Structured headline.
   - Speaker & lecture attribution (`🎙️ Speaker: ... | 📖 Source: ...`).
   - Core takeaway quote.
   - Curated category hashtags.
   - Respectful call to action.

---

## 8. QUEUE MANAGEMENT & DUPLICATE PREVENTION

All repurposing jobs are recorded in SQLite (`noorpost.db`):

- **Job States**: `SOURCE_QUEUED`, `SOURCE_PROCESSING`, `CLIPS_SELECTED`, `CLIPS_RENDERING`, `READY_FOR_DROPBOX`, `DROPBOX_UPLOADING`, `DROPBOX_READY`, `HANDED_OFF_TO_MAKE`, `PUBLISHED`, `FAILED`, `SKIPPED`.
- **Duplicate Prevention**: Slices are tracked by source ID and start/end timestamps. The exact same timestamp range will never be re-rendered or re-uploaded.
- **Auditing Jobs**:
  ```powershell
  python main.py --list-jobs
  ```
- **Retrying Failed Uploads**:
  ```powershell
  python main.py --retry-failed
  ```

---

## 9. 13 CANONICAL CONTENT CATEGORIES

| Category ID | Name | Arabic Badge | Default Theme |
|---|---|---|---|
| `daily_duas` | Daily Duas | DAILY DUA | `midnight-gold` |
| `morning_adhkar` | Morning Adhkar | MORNING ADHKAR | `peaceful-nature` |
| `evening_adhkar` | Evening Adhkar | EVENING ADHKAR | `reflective-night` |
| `gratitude_patience` | Gratitude & Patience | SABR & SHUKR | `emerald-serenity` |
| `forgiveness_repentance` | Repentance & Forgiveness | SEEKING FORGIVENESS | `midnight-gold` |
| `remembrance_dhikr` | Remembrance of Allah | DHIKR & REMEMBRANCE | `midnight-gold` |
| `quranic_verses` | Quranic Verses | THE NOBLE QUR'AN | `masjid-elegance` |
| `prophetic_hadith` | Prophetic Hadith | PROPHETIC TEACHING | `emerald-serenity` |
| `short_reminders` | Short Reminders | FAITH REMINDER | `minimal-white` |
| `ramadan` | Ramadan Content | RAMADAN REMINDER | `ramadan-eid` |
| `friday_reminders` | Friday Reminders | JUMU'AH REMINDER | `masjid-elegance` |
| `eid_content` | Eid Content | EID MUBARAK | `ramadan-eid` |
| `general_education` | General Education | ISLAMIC WISDOM | `minimal-white` |

---

## 10. VISUAL THEMES & PRESETS

### Visual Themes:
- `midnight-gold` — Obsidian black background, royal gold accents & 8-point geometric stars.
- `emerald-serenity` — Forest emerald gradients with traditional Islamic arches.
- `minimal-white` — Clean ivory parchment with deep onyx typography.
- `peaceful-nature` — Earthy dawn gradients with mountain silhouettes.
- `reflective-night` — Indigo night sky with celestial crescent & stars.
- `masjid-elegance` — Twilight blue with mosque dome silhouettes.
- `ramadan-eid` — Festive violet/sapphire with traditional fanous lanterns.

### Render Presets:
- `fast`: Ultrafast encoding, 15 fps (great for quick drafts & testing).
- `balanced`: Fast encoding, 24 fps (standard production balance).
- `high_quality`: Slow encoding, 30 fps, high bitrate (pristine archival quality).

---

## 11. COMMAND-LINE REFERENCE (CLI)

```powershell
# --- Video Repurposing ---
# Repurpose authorized YouTube lecture
python main.py --repurpose-url "https://youtube.com/watch?v=..." --confirm-rights

# Repurpose with custom settings (4 clips, 50s each, center crop, fast preset)
python main.py --repurpose-url "https://youtube.com/watch?v=..." --confirm-rights --num-clips 4 --clip-duration 50 --reframing center_crop --preset fast

# Repurpose local lecture file
python main.py --repurpose-file "D:\lectures\khutbah.mp4" --clip-duration 40

# Preview candidate clips without rendering
python main.py --repurpose-file "D:\lectures\khutbah.mp4" --preview-clips

# Manual timestamp cuts
python main.py --repurpose-file "D:\lectures\khutbah.mp4" --timestamps "01:15-02:00, 05:30-06:15"

# List repurposing jobs & statuses
python main.py --list-jobs

# Retry failed uploads
python main.py --retry-failed

# --- Original Content Engine ---
# Render video preview for a category
python main.py --preview --category friday_reminders --preset fast --duration 5

# List 13 canonical categories
python main.py --list-categories

# View review audit status
python main.py --review-status

# Approve/Reject items
python main.py --approve 12
python main.py --reject 15

# Run one full automated cycle
python main.py --now

# Start automated background daily scheduler
python main.py
```

---

## 12. NOORPOST AUTOPILOT (AUTOMATED BATCH & RECURRING PROCESSING)

NoorPost Autopilot operates as an autonomous worker that continuously monitors a queue of long-form Islamic lectures, khutbahs, and educational videos, generates professional vertical Reels (1080x1920) with subtitles, thumbnails, and captions, and deposits them into Dropbox for your Make.com Instagram scenario.

### Queue File (`source_queue.txt`)
The queue file is located at `D:\noorpost\source_queue.txt`. It supports both plain paths/URLs and pipe-delimited structured entries:

#### Structured Queue Format:
```text
URL_OR_PATH | CHANNEL_OR_CREATOR | RIGHTS_CONFIRMED (YES/NO) | PREFERRED_TIMESTAMPS (OPTIONAL)
```

Example entries:
```text
# Authorized YouTube lecture with confirmed rights and specific timestamps:
https://www.youtube.com/watch?v=example123 | Bayyinah Institute | YES | 01:15-02:00, 05:30-06:15

# Local lecture file with confirmed ownership:
D:\lectures\friday_khutbah_2026.mp4 | Sheikh Omar Suleiman | YES |

# Queue item pending license confirmation (will be safely skipped until YES):
https://www.youtube.com/watch?v=unconfirmed456 | Guest Speaker | NO |
```

### Autopilot CLI Commands:

```powershell
# Check current autopilot queue status & statistics
python main.py --autopilot-status

# Process all queued sources once and exit (local files only)
python main.py --autopilot-once

# Process all queued sources once including authorized YouTube URLs
python main.py --autopilot-once --confirm-rights

# Start continuous background autopilot loop (polls every 60 minutes)
python main.py --autopilot-loop

# Start loop with custom polling interval (e.g., every 30 minutes) and YouTube rights confirmed
python main.py --autopilot-loop --interval 30 --confirm-rights

# Discover recent uploads from approved channels into queue
python main.py --discover-channels

# Retry failed queue jobs (up to max attempts)
python main.py --autopilot-retry
```

### Key Autopilot Safeguards:
- **Duplicate Prevention:** Every source URL and file path is normalized and hashed in SQLite (`autopilot_jobs`). The exact same source is never processed twice.
- **Crash Recovery:** If the system is interrupted or restarted, any job left in `PROCESSING` status is safely resumed on the next cycle.
- **Rights Enforcement:** YouTube sources strictly require rights confirmation (`YES` in structured queue or `--confirm-rights` CLI flag). Unconfirmed sources are safely skipped.
- **Retry Backoff:** Transient pipeline errors are caught and tracked up to `AUTOPILOT_MAX_RETRY_ATTEMPTS` before permanently failing.

---

## 13. AUTOMATIC APPROVED-CHANNEL DISCOVERY

To discover authorized long-form lectures automatically, configure `approved_channels.txt`:

### Configuration Format (`approved_channels.txt`):
```text
CHANNEL_ID | CHANNEL_NAME | RIGHTS_CONFIRMED (YES/NO) | NOTES
```

Example:
```text
UC_x5XG1OV2P6uZZ5FSM9Ttw | Example Islamic Foundation | YES | Authorized syndication partner
```

### Discovery Mechanics:
1. Discovery uses YouTube's official public Atom RSS feed (`https://www.youtube.com/feeds/videos.xml?channel_id=...`). It never scrapes, downloads without authorization, or circumvents platform rules.
2. Only channels with `RIGHTS_CONFIRMED=YES` are queried. If no approved channels are configured, discovery remains inactive without generating false errors.
3. Discovered video IDs are checked against existing `autopilot_queue` and `repurpose_sources` records to prevent duplicate queueing.
4. Run discovery via:
   ```powershell
   python main.py --discover-channels
   ```

---

## 14. GITHUB ACTIONS PRODUCTION AUTOMATION

Production automation runs via `.github/workflows/noorpost.yml` on GitHub Actions:

### Daily Schedule (India Standard Time - IST):
- **Morning Slot:** 08:00 AM IST (`30 2 * * *` UTC)
- **Evening Slot:** 09:00 PM IST (`30 15 * * *` UTC)

### Extra Lecture Reels Limit:
In addition to the scheduled authentic reminder/dua/Hadith, the workflow can process up to `MAX_LECTURE_REELS_PER_RUN` (default: `1`) eligible lecture Reel per execution. This prevents runaway processing and API rate limit exhaustion.

### Safe Dry-Run Workflow Dispatch:
You can trigger the workflow manually from the GitHub Actions UI:
1. Navigate to **Actions** -> **NoorPost Daily Production Pipeline**.
2. Click **Run workflow**.
3. Choose branch (e.g., `main` or `noorpost/automation-release`).
4. Set `dry_run` to `true` (renders video and preview artifacts without uploading to Dropbox or modifying remote state).
5. Review the generated video artifact in GitHub Actions summary.

---

## 15. STATE SYNCHRONIZATION & DEDUPLICATION (SCHEMA 2.0)

Ephemeral GitHub-hosted runners do not persist local disk state between runs. NoorPost solves this through secure, cloud-synchronized state via Dropbox (`/NoorPost_State/noorpost_state.json`):

### Idempotent State Merging:
- **Usage Counters:** Instead of blind incrementation (`times_used + 1`), `state_sync.py` merges `duas_meta.times_used` using `MAX(local, remote)`. Repeating state pulls or rerunning workflows will never artificially inflate usage counters.
- **Multi-Table Reconciliation:** `state_sync.py` reconciles `publication_history`, `video_records`, `autopilot_queue`, and `repurpose_clips`. Completed jobs and deduplication history survive runner restarts.
- **Identifier Decoupling:** Content items are tracked by stable source-qualified identifiers (`content_uid`) and SHA-256 hashes (`content_hash`), decoupled from ephemeral SQLite autoincrement integer row IDs.
- **Fail-Closed Safety:** If Dropbox authentication fails or the network times out during production execution, state synchronization fails closed (`RuntimeError`) rather than assuming an empty state, preventing accidental duplicates.
- **Dry-Run Isolation:** State upload is strictly guarded with `if: success() && github.event.inputs.dry_run != 'true'`. Dry runs and failed workflows never overwrite production state.

---

## 16. CONTENT ROTATION & RELIGIOUS ACCURACY

NoorPost prioritizes strict religious authenticity over filler content. Content is selected in order of preference:
1. **Eligible Lecture Highlights** (when authorized and queued).
2. **Verified Duas** (with authenticated book and chapter references).
3. **Authenticated Sahih Hadiths** (from official Sunnah.com API or curated local Sahih collection).
4. **Accurate Quranic Reminders** (with verified Surah/Ayah numbers and reliable translations).

### Hadith Pipeline:
- **Official Sunnah.com API:** Used when `SUNNAH_API_KEY` is configured. Fetches Bukhari, Muslim, and other canonical collections, grading authenticity strictly.
- **Curated Local Fallback:** When API access is unavailable or offline, the system falls back to verified Sahih Hadiths from `content_db.py`.
- **Deduplication:** Uses both internal database IDs and source-qualified external keys (e.g., `sunnah_bukhari_1`) plus SHA-256 content hashes to prevent repeating Hadiths across 24-hour windows.

---

## 17. NASHEED & AUDIO ASSET INTEGRATION

### Halal Tunes & Personal Audio:
- **Catalog Management:** `assets/nasheeds/catalog.json` tracks all candidate audio tracks.
- **License Status:** Only tracks marked `"status": "APPROVED"` with documented creator permission are selected for production video mixing.
- **Adding Your Audio Files:** Place your authorized `.mp3` or `.wav` files into `assets/audio/custom/` or `assets/audio/nasheeds/` and register them in `catalog.json` with proof of rights.
- **Safe Silent Fallback:** If no approved audio tracks exist or local audio files are missing, the pipeline renders clean video with silent audio fallback. It **never** manufactures fake audio attributions in captions.

---

## 18. GITHUB SECRETS CONFIGURATION

To enable automated production runs in GitHub Actions, configure the following secrets in your GitHub repository (**Settings** -> **Secrets and variables** -> **Actions**):

| Secret Name | Required? | Purpose |
|---|---|---|
| `DROPBOX_APP_KEY` | Yes | Dropbox OAuth App Key |
| `DROPBOX_APP_SECRET` | Yes | Dropbox OAuth App Secret |
| `DROPBOX_REFRESH_TOKEN` | Yes | Long-lived Dropbox OAuth Refresh Token |
| `DROPBOX_ACCESS_TOKEN` | Optional | Initial short-lived access token |
| `SUNNAH_API_KEY` | Optional | Official Sunnah.com Hadith API access key |

---

## 19. AUTOMATED TESTING & VERIFICATION

Run the entire test suite (121+ tests):
```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

Run specific test modules:
```powershell
# Autopilot & structured queue tests:
python -m unittest tests/test_autopilot.py -v

# Approved channel discovery tests:
python -m unittest tests/test_channel_discovery.py -v

# State synchronization & idempotency tests:
python -m unittest tests/test_github_actions_and_state.py -v

# Database migrations & Hadith deduplication:
python -m unittest tests/test_database.py -v

# Nasheed engine & licensing tests:
python -m unittest tests/test_nasheed_engine.py -v
```

*All external services (Dropbox, YouTube downloaders, AI endpoints) are mocked in tests to guarantee test runs never upload to real accounts.*


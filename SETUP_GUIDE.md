# NOORPOST — COMPLETE SETUP GUIDE
بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ

This guide walks you through everything from zero to fully automated
Islamic content posting on Instagram + YouTube.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## STEP 0 — INSTALL PYTHON & DEPENDENCIES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Make sure Python 3.9+ is installed:
   python --version

2. Install all dependencies:
   pip install -r requirements.txt

3. Download fonts (required for beautiful Arabic text):
   - Amiri font:    https://fonts.google.com/specimen/Amiri
     → Download → extract → copy Amiri-Regular.ttf + Amiri-Bold.ttf
     → paste into:  assets/fonts/

   - Noto Sans:     https://fonts.google.com/specimen/Noto+Sans
     → Download → extract → copy NotoSans-Regular.ttf
     → paste into:  assets/fonts/

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 1 — INSTAGRAM TOKEN SETUP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### 1A — Convert Instagram to Professional Account
1. Instagram app → Profile → Menu → Settings and Privacy
2. Account type and tools → Switch to Professional Account
3. Choose: Creator (recommended for content creators)

### 1B — Create Meta Developer App
1. Go to: https://developers.facebook.com
2. Log in with your Facebook account (linked to Instagram)
3. My Apps → Create App → Other → Next
4. Type: Business → Next
5. App Name: NoorPost → Create App

### 1C — Add Instagram Product
1. Inside app dashboard → scroll to Products → Instagram → Set Up
2. Left sidebar → Instagram → API Setup with Instagram Login
3. Click "Add Instagram Account" → log in with your Instagram → Authorize

### 1D — Add Yourself as Tester
1. Left sidebar → App Roles → Roles
2. Add People → search your Facebook name → role: Tester → Submit
3. On your PHONE: Instagram → Settings → Website permissions
   → Tester Invites → Accept your app

### 1E — Generate Access Token
1. Left sidebar → Instagram → API Setup
2. Click "Generate Token" next to your account → Allow
3. COPY the token (very long string starting with IGAA...)
   ⚠️ SAVE IT — you will not see it again!

### 1F — Get Your Instagram User ID
Open this URL in browser (replace YOUR_TOKEN):
https://graph.facebook.com/v21.0/me?fields=id,name&access_token=YOUR_TOKEN

The "id" value is your IG_USER_ID.

### 1G — Make Token Long-Lived (60 days)
Open this URL in browser (replace all values):
https://graph.facebook.com/v21.0/oauth/access_token?grant_type=fb_exchange_token&client_id=YOUR_APP_ID&client_secret=YOUR_APP_SECRET&fb_exchange_token=YOUR_SHORT_TOKEN

App ID and App Secret: your app dashboard → Settings → Basic

### 1H — Paste Into config.py
IG_ACCESS_TOKEN = "your_long_lived_token"
IG_USER_ID      = "your_user_id"
IG_APP_ID       = "your_app_id"
IG_APP_SECRET   = "your_app_secret"

### Token Refresh
Tokens expire every 60 days. NoorPost auto-refreshes them — no action needed.
But if it ever fails, just repeat Step 1E–1G.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 2 — CLOUDINARY SETUP (Free Video Hosting)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Instagram API does NOT accept local files — video must be at a public URL.
Cloudinary gives you free hosting (25GB/month free).

1. Go to: https://cloudinary.com
2. Sign Up Free (use email or Google)
3. After login → Dashboard shows:
   - Cloud Name
   - API Key
   - API Secret
4. Paste into config.py:
   CLOUDINARY_CLOUD_NAME = "your_cloud_name"
   CLOUDINARY_API_KEY    = "your_api_key"
   CLOUDINARY_API_SECRET = "your_api_secret"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 3 — YOUTUBE OAUTH SETUP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### 3A — Create Google Cloud Project
1. Go to: https://console.cloud.google.com
2. Click "Select a project" (top bar) → New Project
3. Name: NoorPost → Create

### 3B — Enable YouTube Data API
1. Left menu → APIs & Services → Library
2. Search: YouTube Data API v3 → Click it → Enable

### 3C — Create OAuth Credentials
1. APIs & Services → Credentials → Create Credentials
2. Choose: OAuth client ID
3. If asked to configure consent screen:
   - User Type: External → Create
   - App name: NoorPost
   - Your email in support + developer fields
   - Save and Continue (skip scopes for now) → Back to Dashboard
4. Create Credentials → OAuth client ID again
5. Application type: Desktop app → Name: NoorPost → Create
6. Click DOWNLOAD JSON → rename file to: credentials.json
7. Place credentials.json in your NoorPost project folder

### 3D — Add Test User (important!)
1. APIs & Services → OAuth consent screen
2. Scroll to "Test users" → Add Users
3. Add your Gmail address → Save

### 3E — First Run Authentication
Run this ONCE to authenticate:
   python main.py --now

A browser window will open → log in with your Google account → Allow
This creates yt_token.pkl automatically.
After this, YouTube uploads work forever without needing to log in again.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## STEP 4 — TEST EVERYTHING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Run one full test cycle (posts immediately):
   python main.py --now

Check your Instagram and YouTube — you should see the post within 2-3 minutes.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## STEP 5 — START THE SCHEDULER (daily auto-posting)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   python main.py

This runs forever, posting at 8AM, 1PM, 5PM, 9PM (IST) daily.
Keep the terminal open (or run in background — see below).

### Run in background (so you can close terminal):
   # Windows:
   pythonw main.py

   # Or use a simple batch file (Windows):
   Create run_noorpost.bat with:
   @echo off
   python main.py
   pause

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## PROJECT FOLDER STRUCTURE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

noorpost/
├── main.py              ← Entry point (run this)
├── config.py            ← Your credentials (KEEP PRIVATE)
├── pipeline.py          ← Master pipeline + logger + scheduler
├── video_generator.py   ← Frame rendering + MP4 creation
├── instagram.py         ← Instagram Graph API uploader
├── youtube.py           ← YouTube Data API uploader
├── duas_db.py           ← 20+ authentic duas database
├── requirements.txt     ← Python dependencies
├── credentials.json     ← YouTube OAuth (you download this)
├── yt_token.pkl         ← YouTube token (auto-created)
├── assets/
│   └── fonts/
│       ├── Amiri-Regular.ttf   ← You download this
│       ├── Amiri-Bold.ttf      ← You download this
│       └── NotoSans-Regular.ttf ← You download this
├── output_videos/       ← Generated MP4s saved here
└── logs/                ← Daily log files saved here

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## COMMON ERRORS & FIXES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| Error                          | Fix                                          |
|-------------------------------|----------------------------------------------|
| Insufficient Developer Role    | Accept tester invite in Instagram app        |
| Token expired                  | Re-run Step 1E–1G (auto-refresh handles it)  |
| Cloudinary upload failed       | Check API key/secret in config.py            |
| credentials.json not found     | Download from Google Cloud → place in folder |
| Font not found                 | Download fonts → place in assets/fonts/      |
| moviepy ffmpeg error           | pip install imageio-ffmpeg                   |
| YouTube quota exceeded         | Free quota = 6 uploads/day. Reduce POST_TIMES|

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECURITY REMINDERS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️  NEVER share config.py with anyone
⚠️  NEVER share credentials.json or yt_token.pkl
⚠️  NEVER paste your tokens in any chat or email
⚠️  If a token is accidentally shared → REVOKE IT IMMEDIATELY
    (Meta Developer → App → Revoke token)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
May Allah SWT accept this effort. آمين
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

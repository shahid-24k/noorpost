"""
database.py — Persistent SQLite storage & duplicate prevention for NoorPost Ultimate
Tracks authentic content metadata, video generations, publication history,
scheduler runs, and content review statuses.
Preserves complete history across restarts.
"""

import sqlite3
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List, Set
import config
from logger import log

# Canonical Status Constants
VALID_REVIEW_STATUSES: Set[str] = {"draft", "needs_review", "approved", "rejected"}
VALID_VIDEO_STATUSES: Set[str] = {
    "draft", "generated", "pending_approval", "approved", "scheduled", "published", "failed", "rejected"
}

def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Idempotent database initialization.
    Creates tables if they don't already exist without deleting or altering existing user records.
    Applies safe backward-compatible column migrations.
    """
    with _get_connection() as conn:
        cursor = conn.cursor()

        # 1. Authentic content metadata table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS duas_meta (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_hash TEXT UNIQUE NOT NULL,
                dua_index INTEGER NOT NULL,
                dua_type TEXT NOT NULL,
                arabic TEXT NOT NULL,
                transliteration TEXT NOT NULL,
                translation TEXT NOT NULL,
                source TEXT NOT NULL,
                times_used INTEGER DEFAULT 0,
                last_used_at TEXT,
                is_verified INTEGER DEFAULT 1,
                created_at TEXT NOT NULL
            )
        """)

        # 2. Generated video records
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS video_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dua_id INTEGER NOT NULL,
                video_path TEXT NOT NULL,
                preview_path TEXT,
                caption TEXT NOT NULL,
                theme_used TEXT,
                font_used TEXT,
                duration INTEGER DEFAULT 15,
                file_size_bytes INTEGER,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                layout_used TEXT DEFAULT 'dua',
                preset_used TEXT DEFAULT 'balanced'
            )
        """)

        # 3. Multi-platform publication audit trail
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS publication_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id INTEGER NOT NULL,
                platform TEXT NOT NULL,
                status TEXT NOT NULL,
                remote_url TEXT,
                remote_id TEXT,
                error_message TEXT,
                attempted_at TEXT NOT NULL
            )
        """)

        # 4. Automation & scheduler run history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scheduler_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                status TEXT NOT NULL,
                video_id INTEGER,
                error_message TEXT,
                started_at TEXT NOT NULL,
                completed_at TEXT
            )
        """)

        # 5. Persistent engine state (category rotation, settings)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS content_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Non-destructive migrations for duas_meta:
        cursor.execute("PRAGMA table_info(duas_meta)")
        existing_cols = {col["name"] for col in cursor.fetchall()}

        new_columns = [
            ("category", "TEXT DEFAULT 'daily_duas'"),
            ("surah_name", "TEXT"),
            ("verse_number", "TEXT"),
            ("hadith_collection", "TEXT"),
            ("hadith_number", "TEXT"),
            ("narrator", "TEXT"),
            ("grading", "TEXT DEFAULT 'Sahih'"),
            ("review_status", "TEXT DEFAULT 'approved'"),
            ("commentary", "TEXT"),
            ("tags", "TEXT"),
            ("content_uid", "TEXT")
        ]

        for col_name, col_def in new_columns:
            if col_name not in existing_cols:
                cursor.execute(f"ALTER TABLE duas_meta ADD COLUMN {col_name} {col_def}")

        # Non-destructive migrations for video_records:
        cursor.execute("PRAGMA table_info(video_records)")
        video_cols = {col["name"] for col in cursor.fetchall()}
        if "category" not in video_cols:
            cursor.execute("ALTER TABLE video_records ADD COLUMN category TEXT DEFAULT 'daily_duas'")

        # Non-destructive migrations for autopilot_queue:
        cursor.execute("PRAGMA table_info(autopilot_queue)")
        ap_cols = {col["name"] for col in cursor.fetchall()}
        if ap_cols:
            ap_new_cols = [
                ("channel", "TEXT"),
                ("rights_confirmed", "INTEGER DEFAULT 0"),
                ("preferred_start", "REAL"),
                ("preferred_end", "REAL"),
                ("clip_ids", "TEXT")
            ]
            for ap_col_name, ap_col_def in ap_new_cols:
                if ap_col_name not in ap_cols:
                    cursor.execute(f"ALTER TABLE autopilot_queue ADD COLUMN {ap_col_name} {ap_col_def}")

        
        # 6. Repurpose Sources Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS repurpose_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id TEXT UNIQUE NOT NULL,
                source_type TEXT NOT NULL,
                source_url TEXT NOT NULL,
                title TEXT,
                channel TEXT,
                duration REAL,
                language TEXT,
                rights_confirmed INTEGER DEFAULT 0,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # 7. Repurpose Clips Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS repurpose_clips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                clip_id TEXT UNIQUE NOT NULL,
                source_id INTEGER NOT NULL,
                clip_index INTEGER NOT NULL,
                start_sec REAL NOT NULL,
                end_sec REAL NOT NULL,
                duration_sec REAL NOT NULL,
                title TEXT,
                transcript_snippet TEXT,
                reframing_strategy TEXT DEFAULT 'blur_fill',
                video_path TEXT,
                preview_path TEXT,
                caption TEXT,
                status TEXT NOT NULL,
                dropbox_url TEXT,
                dropbox_id TEXT,
                error_message TEXT,
                retry_count INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (source_id) REFERENCES repurpose_sources(id)
            )
        """)

        conn.commit()
    log("🗄️  Database verified and initialized successfully.")

def compute_content_hash(arabic: str, source: str) -> str:
    """Generate deterministic SHA256 hash for content identity."""
    raw = f"{arabic.strip()}|{source.strip()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def sync_duas(duas_list: List[Dict[str, Any]]):
    """
    Sync in-memory authentic content into the persistent database.
    Does NOT overwrite usage counts or timestamps for existing items.
    Accepts both traditional duas and enriched content items.
    """
    now_iso = datetime.now().isoformat()
    with _get_connection() as conn:
        cursor = conn.cursor()
        for idx, item in enumerate(duas_list):
            chash = compute_content_hash(item["arabic"], item["source"])
            content_uid = str(item.get("id") or item.get("content_uid") or chash[:16])
            category = item.get("category", "daily_duas")
            review_status = item.get("review_status", "approved")
            is_verified = int(item.get("is_verified", 1))

            cursor.execute("""
                INSERT INTO duas_meta (
                    content_hash, content_uid, dua_index, dua_type, arabic, transliteration,
                    translation, source, times_used, is_verified, created_at,
                    category, surah_name, verse_number, hadith_collection,
                    hadith_number, narrator, grading, review_status, commentary, tags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(content_hash) DO UPDATE SET
                    content_uid = COALESCE(excluded.content_uid, duas_meta.content_uid),
                    dua_index = excluded.dua_index,
                    dua_type = excluded.dua_type,
                    transliteration = excluded.transliteration,
                    translation = excluded.translation,
                    source = excluded.source,
                    category = excluded.category,
                    surah_name = excluded.surah_name,
                    verse_number = excluded.verse_number,
                    hadith_collection = excluded.hadith_collection,
                    hadith_number = excluded.hadith_number,
                    narrator = excluded.narrator,
                    grading = excluded.grading,
                    review_status = excluded.review_status,
                    commentary = excluded.commentary,
                    tags = excluded.tags
            """, (
                chash, content_uid, idx, item.get("type", item.get("dua_type", "Authentic Content")),
                item["arabic"], item.get("transliteration", ""), item["translation"],
                item["source"], is_verified, now_iso, category,
                item.get("surah_name"), item.get("verse_number"),
                item.get("hadith_collection"), item.get("hadith_number"),
                item.get("narrator"), item.get("grading", "Sahih"),
                review_status, item.get("commentary"), item.get("tags")
            ))
        conn.commit()

# Alias for sync_duas
sync_content = sync_duas

def upsert_content_item(item: Dict[str, Any]) -> int:
    """
    Insert or update a verified Islamic content item into duas_meta.
    Returns the integer primary key (id) of the item in SQLite.
    Preserves existing times_used and last_used_at.
    """
    now_iso = datetime.now().isoformat()
    chash = compute_content_hash(item["arabic"], item["source"])
    content_uid = str(item.get("id") or item.get("content_uid") or chash[:16])
    category = item.get("category", "daily_duas")
    review_status = item.get("review_status", "approved")
    is_verified = int(item.get("is_verified", 1))

    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO duas_meta (
                content_hash, content_uid, dua_index, dua_type, arabic, transliteration,
                translation, source, times_used, is_verified, created_at,
                category, surah_name, verse_number, hadith_collection,
                hadith_number, narrator, grading, review_status, commentary, tags
            ) VALUES (?, ?, 0, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(content_hash) DO UPDATE SET
                content_uid = COALESCE(excluded.content_uid, duas_meta.content_uid),
                dua_type = excluded.dua_type,
                transliteration = excluded.transliteration,
                translation = excluded.translation,
                source = excluded.source,
                category = excluded.category,
                surah_name = excluded.surah_name,
                verse_number = excluded.verse_number,
                hadith_collection = excluded.hadith_collection,
                hadith_number = excluded.hadith_number,
                narrator = excluded.narrator,
                grading = excluded.grading,
                review_status = excluded.review_status,
                commentary = excluded.commentary,
                tags = excluded.tags
        """, (
            chash, content_uid, item.get("type", item.get("dua_type", "Authentic Content")),
            item["arabic"], item.get("transliteration", ""), item["translation"],
            item["source"], is_verified, now_iso, category,
            item.get("surah_name"), item.get("verse_number"),
            item.get("hadith_collection"), item.get("hadith_number"),
            item.get("narrator"), item.get("grading", "Sahih"),
            review_status, item.get("commentary"), item.get("tags")
        ))

        cursor.execute("SELECT id FROM duas_meta WHERE content_hash = ?", (chash,))
        row = cursor.fetchone()
        conn.commit()
        return row["id"]

def update_content_review_status(content_id: int, new_status: str):
    """
    Safely transition content review status.
    Must be one of: 'draft', 'needs_review', 'approved', 'rejected'.
    """
    if new_status not in VALID_REVIEW_STATUSES:
        raise ValueError(f"Invalid review status: '{new_status}'. Allowed: {VALID_REVIEW_STATUSES}")

    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE duas_meta SET review_status = ? WHERE id = ?", (new_status, content_id))
        if cursor.rowcount == 0:
            raise ValueError(f"Content item with id={content_id} not found.")
        conn.commit()
    log(f"📋 Content #{content_id} review status updated to: {new_status}")

def get_last_category() -> Optional[str]:
    """Retrieve last rotated category from engine state."""
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM content_state WHERE key = 'last_category'")
        row = cursor.fetchone()
        return row["value"] if row else None

def set_last_category(category: str):
    """Store last rotated category in engine state."""
    now_iso = datetime.now().isoformat()
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO content_state (key, value, updated_at) VALUES ('last_category', ?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
        """, (category, now_iso))
        conn.commit()

def get_next_authentic_content(
    category: Optional[str] = None,
    categories_list: Optional[List[str]] = None,
    exclude_recent_hours: int = 24,
    require_approved: bool = True
) -> Dict[str, Any]:
    """
    Intelligent selection of verified Islamic content:
    - Supports single category, list of categories, or automatic category rotation.
    - Strictly prevents duplicate selection by tracking times_used and last_used_at.
    - Excludes items with review_status != 'approved' when require_approved=True.
    - Avoids recently published content within `exclude_recent_hours`.
    - Recovers gracefully if all items in a category have been used.
    - Atomically updates times_used and last_used_at.
    """
    from categories import CATEGORIES, get_next_category_in_rotation

    with _get_connection() as conn:
        cursor = conn.cursor()

        # Step A: Resolve target category
        target_categories = None
        if category:
            target_categories = [category]
        elif categories_list:
            target_categories = categories_list
        else:
            # Auto-rotate across all canonical categories
            last_cat = get_last_category()
            next_cat = get_next_category_in_rotation(last_cat)
            target_categories = [next_cat]

        # Step B: Build query with filters
        conditions = ["is_verified = 1"]
        params: List[Any] = []

        if require_approved:
            conditions.append("(review_status = 'approved' OR review_status IS NULL)")

        # Category condition
        if target_categories:
            placeholders = ",".join("?" for _ in target_categories)
            conditions.append(f"category IN ({placeholders})")
            params.extend(target_categories)

        # Recent usage threshold
        threshold = (datetime.now() - timedelta(hours=exclude_recent_hours)).isoformat()
        recent_cond = " AND (last_used_at IS NULL OR last_used_at < ?)"

        where_clause = " WHERE " + " AND ".join(conditions)
        order_clause = """
            ORDER BY times_used ASC,
                     CASE WHEN last_used_at IS NULL THEN 0 ELSE 1 END ASC,
                     last_used_at ASC,
                     RANDOM()
            LIMIT 1
        """

        # 1. Try with recent exclusion
        cursor.execute(f"SELECT * FROM duas_meta {where_clause} {recent_cond} {order_clause}", params + [threshold])
        row = cursor.fetchone()

        # 2. If no items found due to recency lockout, relax recency restriction
        if not row:
            cursor.execute(f"SELECT * FROM duas_meta {where_clause} {order_clause}", params)
            row = cursor.fetchone()

        # 3. If category has no items at all, fallback to any approved verified content
        if not row:
            log(f"⚠️  No approved items in {target_categories}; falling back to general approved pool.", level="WARNING")
            cursor.execute(f"""
                SELECT * FROM duas_meta
                WHERE is_verified = 1 AND (review_status = 'approved' OR review_status IS NULL)
                {order_clause}
            """)
            row = cursor.fetchone()

        if not row:
            raise RuntimeError("No approved verified Islamic content found in database. Please run sync_content.")

        content_id = row["id"]
        chosen_cat = row["category"] or "daily_duas"
        now_iso = datetime.now().isoformat()

        # Atomically record usage
        cursor.execute("""
            UPDATE duas_meta
            SET times_used = times_used + 1,
                last_used_at = ?
            WHERE id = ?
        """, (now_iso, content_id))
        conn.commit()

        # Persist last rotated category
        set_last_category(chosen_cat)

        res = dict(row)
        # Ensure type key is present for video generator compatibility
        if "type" not in res and "dua_type" in res:
            res["type"] = res["dua_type"]
        return res

def get_next_authentic_dua() -> Dict[str, Any]:
    """Backward compatibility wrapper for get_next_authentic_content."""
    return get_next_authentic_content()

def is_recent_duplicate(identifier: Any, hours: int = 24) -> bool:
    """
    Check if this specific content item has been successfully published in the past N hours.
    Accepts:
    - Internal integer database id (e.g. 42)
    - Content hash string (SHA-256)
    - External identifier or content_uid string (e.g. 'orig_dua_001', 'sunnah_bukhari_1')
    """
    if identifier is None:
        return False

    threshold = (datetime.now() - timedelta(hours=hours)).isoformat()
    with _get_connection() as conn:
        cursor = conn.cursor()

        is_num = False
        num_id = None
        if isinstance(identifier, int):
            is_num = True
            num_id = identifier
        elif isinstance(identifier, str) and identifier.strip().isdigit():
            is_num = True
            num_id = int(identifier.strip())

        if is_num:
            cursor.execute("""
                SELECT v.id FROM video_records v
                JOIN publication_history p ON p.video_id = v.id
                WHERE v.dua_id = ? AND p.status = 'success' AND p.attempted_at >= ?
                LIMIT 1
            """, (num_id, threshold))
            if cursor.fetchone() is not None:
                return True

        # Check by content_hash or content_uid in duas_meta
        ident_str = str(identifier).strip()
        cursor.execute("""
            SELECT v.id FROM video_records v
            JOIN publication_history p ON p.video_id = v.id
            JOIN duas_meta d ON d.id = v.dua_id
            WHERE (d.content_hash = ? OR d.content_uid = ? OR v.dua_id = ?)
              AND p.status = 'success' AND p.attempted_at >= ?
            LIMIT 1
        """, (ident_str, ident_str, ident_str, threshold))
        return cursor.fetchone() is not None

def is_duplicate_caption(caption: str, lookback_days: int = 7) -> bool:
    """Check if an identical caption was already used in recent videos."""
    clean_cap = caption.strip()
    threshold = (datetime.now() - timedelta(days=lookback_days)).isoformat()
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id FROM video_records
            WHERE TRIM(caption) = ? AND created_at >= ?
            LIMIT 1
        """, (clean_cap, threshold))
        return cursor.fetchone() is not None

def record_video(dua_id: int, video_path: str, preview_path: str,
                 caption: str, theme: str, font: str, duration: int,
                 layout: str = "dua", preset: str = "balanced",
                 category: str = "daily_duas") -> int:
    """Store generated video record."""
    file_size = 0
    p = Path(video_path)
    if p.exists():
        file_size = p.stat().st_size

    now_iso = datetime.now().isoformat()
    initial_status = "pending_approval" if config.REQUIRE_APPROVAL else "generated"

    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO video_records (
                dua_id, video_path, preview_path, caption, theme_used,
                font_used, duration, file_size_bytes, status, created_at,
                layout_used, preset_used, category
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            dua_id, video_path, preview_path, caption, theme,
            font, duration, file_size, initial_status, now_iso,
            layout, preset, category
        ))
        conn.commit()
        return cursor.lastrowid

def update_video_status(video_id: int, status: str):
    """
    Update video processing / publication status.
    Valid statuses: draft, generated, pending_approval, approved, scheduled, published, failed, rejected.
    """
    if status not in VALID_VIDEO_STATUSES:
        raise ValueError(f"Invalid video status '{status}'. Must be one of {VALID_VIDEO_STATUSES}")
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE video_records SET status = ? WHERE id = ?", (status, video_id))
        conn.commit()

def record_publication(video_id: int, platform: str, status: str,
                       remote_url: Optional[str] = None, remote_id: Optional[str] = None,
                       error_message: Optional[str] = None) -> int:
    """Log individual platform publication result."""
    now_iso = datetime.now().isoformat()
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO publication_history (
                video_id, platform, status, remote_url, remote_id, error_message, attempted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (video_id, platform, status, remote_url, remote_id, error_message, now_iso))
        conn.commit()
        return cursor.lastrowid

def start_scheduler_run(job_id: str) -> int:
    """Log the start of a scheduled automation run."""
    now_iso = datetime.now().isoformat()
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO scheduler_runs (job_id, status, started_at)
            VALUES (?, 'started', ?)
        """, (job_id, now_iso))
        conn.commit()
        return cursor.lastrowid

def finish_scheduler_run(run_id: int, status: str, video_id: Optional[int] = None,
                         error_message: Optional[str] = None):
    """Mark scheduler run finished."""
    now_iso = datetime.now().isoformat()
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE scheduler_runs
            SET status = ?, video_id = ?, error_message = ?, completed_at = ?
            WHERE id = ?
        """, (status, video_id, error_message, now_iso, run_id))
        conn.commit()


# ─────────────────────────────────────────────
# REPURPOSING JOB QUEUE & AUDIT FUNCTIONS
# ─────────────────────────────────────────────

REPURPOSE_STATES = {
    "SOURCE_QUEUED", "SOURCE_PROCESSING", "CLIPS_SELECTED", "CLIPS_RENDERING",
    "READY_FOR_DROPBOX", "DROPBOX_UPLOADING", "DROPBOX_READY",
    "HANDED_OFF_TO_MAKE", "PUBLISHED", "FAILED", "SKIPPED"
}

def register_repurpose_source(
    source_id: str,
    source_type: str,
    source_url: str,
    title: str,
    channel: str,
    duration: float,
    language: str = "en",
    rights_confirmed: bool = False
) -> int:
    """Register or retrieve an existing source video record."""
    now_iso = datetime.now().isoformat()
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO repurpose_sources (
                source_id, source_type, source_url, title, channel,
                duration, language, rights_confirmed, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'SOURCE_QUEUED', ?, ?)
            ON CONFLICT(source_id) DO UPDATE SET
                title = excluded.title,
                duration = excluded.duration,
                rights_confirmed = excluded.rights_confirmed,
                updated_at = excluded.updated_at
        """, (
            source_id, source_type, source_url, title, channel,
            duration, language, int(rights_confirmed), now_iso, now_iso
        ))
        conn.commit()

        cursor.execute("SELECT id FROM repurpose_sources WHERE source_id = ?", (source_id,))
        return cursor.fetchone()["id"]

def update_source_status(source_db_id: int, status: str):
    now_iso = datetime.now().isoformat()
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE repurpose_sources SET status = ?, updated_at = ? WHERE id = ?
        """, (status, now_iso, source_db_id))
        conn.commit()

def record_repurpose_clip(
    source_db_id: int,
    clip_id: str,
    clip_index: int,
    start_sec: float,
    end_sec: float,
    title: str,
    transcript_snippet: str = "",
    reframing_strategy: str = "blur_fill",
    video_path: Optional[str] = None,
    preview_path: Optional[str] = None,
    caption: Optional[str] = None,
    status: str = "CLIPS_SELECTED"
) -> int:
    """Store or update a selected clip candidate."""
    now_iso = datetime.now().isoformat()
    dur = round(end_sec - start_sec, 2)
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO repurpose_clips (
                clip_id, source_id, clip_index, start_sec, end_sec, duration_sec,
                title, transcript_snippet, reframing_strategy, video_path,
                preview_path, caption, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(clip_id) DO UPDATE SET
                video_path = COALESCE(excluded.video_path, repurpose_clips.video_path),
                preview_path = COALESCE(excluded.preview_path, repurpose_clips.preview_path),
                caption = COALESCE(excluded.caption, repurpose_clips.caption),
                status = excluded.status,
                updated_at = excluded.updated_at
        """, (
            clip_id, source_db_id, clip_index, start_sec, end_sec, dur,
            title, transcript_snippet, reframing_strategy, video_path,
            preview_path, caption, status, now_iso, now_iso
        ))
        conn.commit()
        cursor.execute("SELECT id FROM repurpose_clips WHERE clip_id = ?", (clip_id,))
        return cursor.fetchone()["id"]

def update_clip_status(
    clip_id: str,
    status: str,
    dropbox_url: Optional[str] = None,
    dropbox_id: Optional[str] = None,
    error_message: Optional[str] = None
):
    now_iso = datetime.now().isoformat()
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE repurpose_clips
            SET status = ?,
                dropbox_url = COALESCE(?, dropbox_url),
                dropbox_id = COALESCE(?, dropbox_id),
                error_message = ?,
                updated_at = ?
            WHERE clip_id = ?
        """, (status, dropbox_url, dropbox_id, error_message, now_iso, clip_id))
        conn.commit()

def get_repurpose_jobs(status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve repurpose clip records with source details."""
    with _get_connection() as conn:
        cursor = conn.cursor()
        if status:
            cursor.execute("""
                SELECT c.*, s.title as source_title, s.source_url
                FROM repurpose_clips c
                JOIN repurpose_sources s ON c.source_id = s.id
                WHERE c.status = ?
                ORDER BY c.id DESC LIMIT ?
            """, (status, limit))
        else:
            cursor.execute("""
                SELECT c.*, s.title as source_title, s.source_url
                FROM repurpose_clips c
                JOIN repurpose_sources s ON c.source_id = s.id
                ORDER BY c.id DESC LIMIT ?
            """, (limit,))
        return [dict(r) for r in cursor.fetchall()]

def is_duplicate_clip(source_id: str, start_sec: float, end_sec: float) -> bool:
    """Check if this exact portion of the video was already clipped and rendered."""
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.id FROM repurpose_clips c
            JOIN repurpose_sources s ON c.source_id = s.id
            WHERE s.source_id = ?
              AND ABS(c.start_sec - ?) < 1.0
              AND ABS(c.end_sec - ?) < 1.0
              AND c.status NOT IN ('FAILED')
            LIMIT 1
        """, (source_id, start_sec, end_sec))
        return cursor.fetchone() is not None

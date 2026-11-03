"""
state_sync.py — Persistent State Synchronization for GitHub Actions Runners
NoorPost Ultimate

Features:
- Ephemeral Runner Resilience: GitHub Actions runners are temporary; this module synchronizes
  publication history, content usage, autopilot queue status, repurposing clip history,
  repurposing source history, nasheed usage history, and duplicate prevention state
  between Dropbox and local SQLite.
- Make.com Trigger Isolation: State files are stored strictly in '/NoorPost_State/noorpost_state.json',
  guaranteeing zero interference with the Make.com trigger folder ('/NoorPost/*.mp4').
- Idempotency & Stale State Protection: Merges state idempotently using MAX() counters and
  conflict resolution. Preserves all history across repeated pulls and never overwrites existing
  history with empty or stale state.
- Fail-Closed Security: If Dropbox credentials are configured but Dropbox client creation fails,
  or remote state download encounters an error (network, auth, corrupted token), it fails closed
  to protect production against duplicate publishing.
- Dry-Run Isolation: Skips uploading state to Dropbox during dry-run or preview mode.
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Set, Optional

import config
from logger import log
from database import _get_connection, init_db

STATE_DIR = Path("assets/state")
LOCAL_STATE_FILE = STATE_DIR / "noorpost_state.json"
DROPBOX_STATE_FOLDER = "/NoorPost_State"
DROPBOX_STATE_FILE = f"{DROPBOX_STATE_FOLDER}/noorpost_state.json"


class StateSyncManager:
    """Synchronizes persistent publishing and deduplication records across runner executions."""

    def __init__(self, local_file: Optional[Path] = None):
        self.local_file = local_file or LOCAL_STATE_FILE
        STATE_DIR.mkdir(parents=True, exist_ok=True)

    def _is_dropbox_configured(self) -> bool:
        """Check whether production Dropbox credentials are provided in config or environment."""
        return bool(
            getattr(config, "DROPBOX_REFRESH_TOKEN", None)
            or getattr(config, "DROPBOX_ACCESS_TOKEN", None)
            or os.environ.get("DROPBOX_REFRESH_TOKEN")
            or os.environ.get("DROPBOX_ACCESS_TOKEN")
        )

    def _get_dbx_client(self, fail_closed: bool = True):
        """
        Obtain authenticated Dropbox client if configured.
        If credentials are configured but initialization fails, fails closed
        when fail_closed is True and not in preview mode.
        """
        if not self._is_dropbox_configured():
            return None

        try:
            from instagram import get_dropbox_client
            return get_dropbox_client()
        except Exception as e:
            log(f"❌ Dropbox client initialization failed with configured credentials: {e}", level="ERROR")
            if fail_closed and not getattr(config, "PREVIEW_ONLY", False):
                raise RuntimeError(
                    f"Dropbox client initialization failed with configured credentials: {e}. "
                    "Failing closed to prevent duplicate publication in production."
                ) from e
            return None

    # ── State Pull (Run at beginning of workflow) ────────────────────────────────
    def pull_state(self, fail_closed: bool = True) -> Dict[str, Any]:
        """
        Download the persistent state file from Dropbox and sync into local SQLite.
        Returns the parsed state dictionary.
        Fails closed if Dropbox is configured but client creation or download encounters an error.
        """
        init_db()
        state_data = None
        dbx = self._get_dbx_client(fail_closed=fail_closed)

        if dbx:
            try:
                log(f"☁️  Checking Dropbox for persistent state file ({DROPBOX_STATE_FILE})...")
                metadata, response = dbx.files_download(DROPBOX_STATE_FILE)
                content_str = response.content.decode("utf-8")
                state_data = json.loads(content_str)
                log(f"✅ Persistent state successfully downloaded from Dropbox (last synced: {state_data.get('last_sync')}).")
            except Exception as e:
                err_str = str(e).lower()
                is_not_found = False
                try:
                    import dropbox
                    if isinstance(e, dropbox.exceptions.ApiError):
                        if hasattr(e.error, "is_path") and e.error.is_path() and hasattr(e.error.get_path(), "is_not_found") and e.error.get_path().is_not_found():
                            is_not_found = True
                except Exception:
                    pass

                if "not_found" in err_str or "path/not_found" in err_str or "does not exist" in err_str or is_not_found:
                    log("ℹ️  Remote state not found on Dropbox (initial clean setup). Initializing fresh state.", level="INFO")
                    state_data = self._initial_state()
                else:
                    log(f"❌ Failed to download persistent state from Dropbox: {e}", level="ERROR")
                    if fail_closed and not getattr(config, "PREVIEW_ONLY", False):
                        raise RuntimeError(
                            f"Persistent state download failed from Dropbox: {e}. "
                            "Failing closed to prevent duplicate publication in production."
                        ) from e

        if not state_data:
            # Fallback to local state if exists
            if self.local_file.exists():
                try:
                    with open(self.local_file, "r", encoding="utf-8") as f:
                        state_data = json.load(f)
                except Exception:
                    state_data = self._initial_state()
            else:
                state_data = self._initial_state()

        # Save to local state file
        try:
            with open(self.local_file, "w", encoding="utf-8") as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            log(f"Warning: Could not write local state file: {e}", level="WARNING")

        # Synchronize into local SQLite
        self._merge_into_sqlite(state_data)
        return state_data

    # ── State Push (Run at end of workflow) ──────────────────────────────────────
    def push_state(self, is_dry_run: bool = False) -> bool:
        """
        Export publication records from SQLite, merge with historical state to prevent data loss,
        and upload the persistent state to Dropbox.
        If is_dry_run or config.PREVIEW_ONLY is True, remote push is strictly skipped to protect production state.
        """
        if is_dry_run or getattr(config, "PREVIEW_ONLY", False):
            log("ℹ️  Dry-run / preview mode active. Skipping persistent state push to Dropbox to protect production state.", level="INFO")
            return True

        init_db()
        state_data = self._build_state_from_sqlite()

        # Save locally
        try:
            with open(self.local_file, "w", encoding="utf-8") as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            log(f"Warning: Could not write local state: {e}", level="WARNING")

        if not self._is_dropbox_configured():
            log("ℹ️  Dropbox not configured; state saved locally only.", level="INFO")
            return False

        dbx = self._get_dbx_client(fail_closed=True)
        if not dbx:
            return False

        try:
            import dropbox
            payload = json.dumps(state_data, indent=2, ensure_ascii=False).encode("utf-8")
            log(f"☁️  Uploading persistent state to Dropbox: {DROPBOX_STATE_FILE}...")
            dbx.files_upload(
                payload,
                DROPBOX_STATE_FILE,
                mode=dropbox.files.WriteMode("overwrite")
            )
            log("✅ Persistent state uploaded to Dropbox successfully.")
            return True
        except Exception as e:
            log(f"⚠️  Failed to upload state to Dropbox: {e}", level="WARNING")
            return False

    # ── Internal Helpers ─────────────────────────────────────────────────────────
    def _initial_state(self) -> Dict[str, Any]:
        return {
            "version": "2.0",
            "last_sync": datetime.utcnow().isoformat() + "Z",
            "published_content": [],
            "published_content_ids": [],
            "published_clips": [],
            "publications": [],
            "repurpose_clips": [],
            "repurpose_sources": [],
            "autopilot_queue": [],
            "nasheed_history": []
        }

    def _merge_into_sqlite(self, state_data: Dict[str, Any]) -> None:
        """
        Idempotently merge persistent state from remote into local SQLite.
        Ensures times_used is never repeatedly incremented if pull_state is called multiple times.
        Reconciles authentic content, repurposing clips, repurposing sources,
        nasheed history, autopilot queue, and publication history.
        """
        if not state_data:
            return

        with _get_connection() as conn:
            cursor = conn.cursor()

            # 1. Reconcile published_content (v2.0 format)
            pub_content = state_data.get("published_content", [])
            merged_content_count = 0
            if pub_content:
                for item in pub_content:
                    chash = item.get("content_hash")
                    c_uid = item.get("content_uid")
                    r_times = int(item.get("times_used", 1))
                    r_last = item.get("last_used_at")

                    if chash:
                        cursor.execute("""
                            UPDATE duas_meta
                            SET times_used = CASE WHEN times_used > ? THEN times_used ELSE ? END,
                                last_used_at = CASE 
                                    WHEN last_used_at IS NULL THEN ? 
                                    WHEN ? > last_used_at THEN ? 
                                    ELSE last_used_at 
                                END
                            WHERE content_hash = ?
                        """, (r_times, r_times, r_last, r_last, r_last, chash))
                        if cursor.rowcount > 0:
                            merged_content_count += 1
                    elif c_uid:
                        cursor.execute("""
                            UPDATE duas_meta
                            SET times_used = CASE WHEN times_used > ? THEN times_used ELSE ? END,
                                last_used_at = CASE 
                                    WHEN last_used_at IS NULL THEN ? 
                                    WHEN ? > last_used_at THEN ? 
                                    ELSE last_used_at 
                                END
                            WHERE content_uid = ?
                        """, (r_times, r_times, r_last, r_last, r_last, str(c_uid)))
                        if cursor.rowcount > 0:
                            merged_content_count += 1

            # 2. Reconcile legacy published_content_ids (v1.0 format)
            legacy_ids = state_data.get("published_content_ids", [])
            if legacy_ids and not pub_content:
                for cid in legacy_ids:
                    if isinstance(cid, int) or (isinstance(cid, str) and cid.isdigit()):
                        cursor.execute("""
                            UPDATE duas_meta
                            SET times_used = CASE WHEN times_used > 0 THEN times_used ELSE 1 END,
                                last_used_at = COALESCE(last_used_at, CURRENT_TIMESTAMP)
                            WHERE id = ?
                        """, (int(cid),))
                    else:
                        cursor.execute("""
                            UPDATE duas_meta
                            SET times_used = CASE WHEN times_used > 0 THEN times_used ELSE 1 END,
                                last_used_at = COALESCE(last_used_at, CURRENT_TIMESTAMP)
                            WHERE content_hash = ? OR content_uid = ?
                        """, (str(cid), str(cid)))
                    if cursor.rowcount > 0:
                        merged_content_count += 1

            # 3. Reconcile repurpose_sources
            rep_sources = state_data.get("repurpose_sources", [])
            if rep_sources:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='repurpose_sources'")
                if cursor.fetchone():
                    for src in rep_sources:
                        s_id = src.get("source_id")
                        s_url = src.get("source_url")
                        if not s_id or not s_url:
                            continue
                        cursor.execute("""
                            INSERT INTO repurpose_sources (
                                source_id, source_type, source_url, title, channel,
                                duration, language, rights_confirmed, status, created_at, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT(source_id) DO UPDATE SET
                                status = CASE 
                                    WHEN excluded.status IN ('PROCESSED', 'COMPLETED', 'ARCHIVED') THEN excluded.status 
                                    WHEN repurpose_sources.status IN ('PROCESSED', 'COMPLETED', 'ARCHIVED') THEN repurpose_sources.status 
                                    ELSE excluded.status 
                                END,
                                title = COALESCE(excluded.title, repurpose_sources.title),
                                channel = COALESCE(excluded.channel, repurpose_sources.channel),
                                rights_confirmed = CASE WHEN repurpose_sources.rights_confirmed > excluded.rights_confirmed THEN repurpose_sources.rights_confirmed ELSE excluded.rights_confirmed END,
                                updated_at = excluded.updated_at
                        """, (
                            s_id, src.get("source_type", "youtube"), s_url,
                            src.get("title"), src.get("channel"), src.get("duration"),
                            src.get("language", "en"), int(src.get("rights_confirmed", 0)),
                            src.get("status", "PENDING"),
                            src.get("created_at", datetime.now().isoformat()),
                            src.get("updated_at", datetime.now().isoformat())
                        ))

            # 4. Reconcile repurpose_clips
            rep_clips = state_data.get("repurpose_clips", [])
            if rep_clips:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='repurpose_clips'")
                if cursor.fetchone():
                    for clip in rep_clips:
                        c_id = clip.get("clip_id")
                        if not c_id:
                            continue

                        # Ensure valid source_id foreign key
                        src_fk = clip.get("source_id")
                        if not isinstance(src_fk, int) or src_fk <= 0:
                            cursor.execute("SELECT id FROM repurpose_sources LIMIT 1")
                            first_src = cursor.fetchone()
                            if first_src:
                                src_fk = first_src[0]
                            else:
                                cursor.execute("""
                                    INSERT INTO repurpose_sources (
                                        source_id, source_type, source_url, status, created_at, updated_at
                                    ) VALUES (?, 'imported', 'imported', 'PROCESSED', ?, ?)
                                """, (f"imported_src_{c_id}", datetime.now().isoformat(), datetime.now().isoformat()))
                                src_fk = cursor.lastrowid

                        cursor.execute("""
                            INSERT INTO repurpose_clips (
                                clip_id, source_id, clip_index, start_sec, end_sec, duration_sec,
                                title, transcript_snippet, reframing_strategy, video_path, preview_path,
                                caption, status, dropbox_url, dropbox_id, error_message, retry_count,
                                created_at, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT(clip_id) DO UPDATE SET
                                status = CASE 
                                    WHEN excluded.status IN ('UPLOADED', 'HANDED_OFF_TO_MAKE', 'COMPLETED') THEN excluded.status 
                                    WHEN repurpose_clips.status IN ('UPLOADED', 'HANDED_OFF_TO_MAKE', 'COMPLETED') THEN repurpose_clips.status 
                                    ELSE excluded.status 
                                END,
                                dropbox_url = COALESCE(excluded.dropbox_url, repurpose_clips.dropbox_url),
                                dropbox_id = COALESCE(excluded.dropbox_id, repurpose_clips.dropbox_id),
                                error_message = COALESCE(excluded.error_message, repurpose_clips.error_message),
                                updated_at = excluded.updated_at
                        """, (
                            c_id, src_fk, clip.get("clip_index", 0),
                            float(clip.get("start_sec", 0.0)), float(clip.get("end_sec", 0.0)),
                            float(clip.get("duration_sec", 0.0)), clip.get("title"),
                            clip.get("transcript_snippet"), clip.get("reframing_strategy", "blur_fill"),
                            clip.get("video_path"), clip.get("preview_path"), clip.get("caption"),
                            clip.get("status", "EXTRACTED"), clip.get("dropbox_url"), clip.get("dropbox_id"),
                            clip.get("error_message"), int(clip.get("retry_count", 0)),
                            clip.get("created_at", datetime.now().isoformat()),
                            clip.get("updated_at", datetime.now().isoformat())
                        ))

            # 5. Reconcile published_clips list
            pub_clips = state_data.get("published_clips", [])
            if pub_clips:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='repurpose_clips'")
                if cursor.fetchone():
                    for pc_id in pub_clips:
                        cursor.execute("""
                            UPDATE repurpose_clips
                            SET status = 'HANDED_OFF_TO_MAKE', updated_at = ?
                            WHERE clip_id = ? AND status NOT IN ('UPLOADED', 'HANDED_OFF_TO_MAKE', 'COMPLETED')
                        """, (datetime.now().isoformat(), str(pc_id)))

            # 6. Reconcile nasheed_history
            nash_hist = state_data.get("nasheed_history", [])
            if nash_hist:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='nasheed_usage'")
                if cursor.fetchone():
                    for nh in nash_hist:
                        t_id = nh.get("track_id")
                        if not t_id:
                            continue
                        t_title = nh.get("track_title", t_id)
                        t_times = int(nh.get("times_used", 1))
                        t_last = nh.get("last_used_at", datetime.now().isoformat())
                        t_created = nh.get("created_at", datetime.now().isoformat())

                        cursor.execute("""
                            INSERT INTO nasheed_usage (track_id, track_title, times_used, last_used_at, created_at)
                            VALUES (?, ?, ?, ?, ?)
                            ON CONFLICT(track_id) DO UPDATE SET
                                times_used = CASE WHEN nasheed_usage.times_used > excluded.times_used THEN nasheed_usage.times_used ELSE excluded.times_used END,
                                last_used_at = CASE 
                                    WHEN nasheed_usage.last_used_at IS NULL THEN excluded.last_used_at
                                    WHEN excluded.last_used_at > nasheed_usage.last_used_at THEN excluded.last_used_at
                                    ELSE nasheed_usage.last_used_at
                                END,
                                track_title = COALESCE(excluded.track_title, nasheed_usage.track_title)
                        """, (t_id, t_title, t_times, t_last, t_created))

            # 7. Reconcile autopilot queue
            ap_items = state_data.get("autopilot_queue", [])
            if ap_items:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='autopilot_queue'")
                if cursor.fetchone():
                    for ap in ap_items:
                        s_hash = ap.get("source_hash")
                        s_entry = ap.get("source_entry")
                        if not s_hash or not s_entry:
                            continue
                        cursor.execute("""
                            INSERT INTO autopilot_queue (
                                source_entry, source_hash, status, num_clips_produced,
                                error_message, attempts, queued_at, completed_at, updated_at,
                                channel, rights_confirmed, preferred_start, preferred_end, clip_ids
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT(source_hash) DO UPDATE SET
                                status = CASE 
                                    WHEN excluded.status IN ('COMPLETED', 'SKIPPED') THEN excluded.status 
                                    WHEN autopilot_queue.status IN ('COMPLETED', 'SKIPPED') THEN autopilot_queue.status 
                                    ELSE excluded.status 
                                END,
                                num_clips_produced = CASE WHEN autopilot_queue.num_clips_produced > excluded.num_clips_produced THEN autopilot_queue.num_clips_produced ELSE excluded.num_clips_produced END,
                                completed_at = COALESCE(excluded.completed_at, autopilot_queue.completed_at),
                                attempts = CASE WHEN autopilot_queue.attempts > excluded.attempts THEN autopilot_queue.attempts ELSE excluded.attempts END,
                                updated_at = excluded.updated_at,
                                channel = COALESCE(excluded.channel, autopilot_queue.channel),
                                rights_confirmed = CASE WHEN autopilot_queue.rights_confirmed > excluded.rights_confirmed THEN autopilot_queue.rights_confirmed ELSE excluded.rights_confirmed END,
                                preferred_start = COALESCE(excluded.preferred_start, autopilot_queue.preferred_start),
                                preferred_end = COALESCE(excluded.preferred_end, autopilot_queue.preferred_end),
                                clip_ids = COALESCE(excluded.clip_ids, autopilot_queue.clip_ids)
                        """, (
                            s_entry, s_hash, ap.get("status", "QUEUED"),
                            ap.get("num_clips_produced", 0), ap.get("error_message"),
                            ap.get("attempts", 0), ap.get("queued_at", datetime.now().isoformat()),
                            ap.get("completed_at"), ap.get("updated_at", datetime.now().isoformat()),
                            ap.get("channel"), int(ap.get("rights_confirmed", 0)),
                            ap.get("preferred_start"), ap.get("preferred_end"),
                            ap.get("clip_ids")
                        ))

            # 8. Reconcile publication history (prevents duplicates across runner instances)
            pub_hist = state_data.get("publications", [])
            if pub_hist:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='publication_history'")
                if cursor.fetchone():
                    for pub in pub_hist:
                        v_id = pub.get("video_id")
                        plat = pub.get("platform", "dropbox_make")
                        stat = pub.get("status", "success")
                        att = pub.get("attempted_at", datetime.now().isoformat())
                        r_url = pub.get("remote_url")
                        r_id = pub.get("remote_id")

                        # Query by remote_id or (video_id, platform, attempted_at) to ensure idempotency
                        already_recorded = False
                        if r_id:
                            cursor.execute("SELECT id FROM publication_history WHERE remote_id = ? AND platform = ?", (r_id, plat))
                            if cursor.fetchone():
                                already_recorded = True
                        if not already_recorded and v_id:
                            cursor.execute("""
                                SELECT id FROM publication_history
                                WHERE video_id = ? AND platform = ? AND status = ? AND attempted_at = ?
                            """, (v_id, plat, stat, att))
                            if cursor.fetchone():
                                already_recorded = True

                        if not already_recorded and v_id:
                            cursor.execute("""
                                INSERT INTO publication_history (video_id, platform, status, remote_url, remote_id, error_message, attempted_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (v_id, plat, stat, r_url, r_id, pub.get("error_message"), att))

            conn.commit()
            if merged_content_count > 0:
                log(f"🗄️  Merged {merged_content_count} published content record(s) into SQLite.")

    def _build_state_from_sqlite(self) -> Dict[str, Any]:
        """
        Compile state dictionary from SQLite tables, idempotently merging with existing local state
        file to guarantee history is never dropped or overwritten with empty state.
        """
        published_content_map: Dict[str, Dict[str, Any]] = {}
        published_ids_set: Set[str] = set()
        publications_map: Dict[str, Dict[str, Any]] = {}
        published_clips_set: Set[str] = set()
        repurpose_clips_map: Dict[str, Dict[str, Any]] = {}
        repurpose_sources_map: Dict[str, Dict[str, Any]] = {}
        autopilot_queue_map: Dict[str, Dict[str, Any]] = {}
        nasheed_history_map: Dict[str, Dict[str, Any]] = {}

        # 1. Load existing historical state from local state file if present
        if self.local_file.exists():
            try:
                with open(self.local_file, "r", encoding="utf-8") as f:
                    prior = json.load(f)
                    for item in prior.get("published_content", []):
                        key = item.get("content_hash") or str(item.get("content_uid") or item.get("id"))
                        if key:
                            published_content_map[key] = item
                    for cid in prior.get("published_content_ids", []):
                        published_ids_set.add(str(cid))
                    for p in prior.get("publications", []):
                        pkey = p.get("remote_id") or f"{p.get('video_id')}_{p.get('platform')}_{p.get('attempted_at')}"
                        publications_map[pkey] = p
                    for clip in prior.get("repurpose_clips", []):
                        if clip.get("clip_id"):
                            repurpose_clips_map[clip["clip_id"]] = clip
                    for c_id in prior.get("published_clips", []):
                        published_clips_set.add(str(c_id))
                    for src in prior.get("repurpose_sources", []):
                        if src.get("source_id"):
                            repurpose_sources_map[src["source_id"]] = src
                    for ap in prior.get("autopilot_queue", []):
                        if ap.get("source_hash"):
                            autopilot_queue_map[ap["source_hash"]] = ap
                    for nh in prior.get("nasheed_history", []):
                        if nh.get("track_id"):
                            nasheed_history_map[nh["track_id"]] = nh
            except Exception as e:
                log(f"Warning: Could not read prior local state file for merge: {e}", level="WARNING")

        # 2. Query current SQLite tables and idempotently merge / update
        with _get_connection() as conn:
            cursor = conn.cursor()

            # 2a. duas_meta
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='duas_meta'")
            if cursor.fetchone():
                cursor.execute("""
                    SELECT id, content_hash, content_uid, source, times_used, last_used_at, category
                    FROM duas_meta
                    WHERE times_used > 0
                """)
                for row in cursor.fetchall():
                    r_dict = dict(row)
                    key = r_dict.get("content_hash") or str(r_dict.get("content_uid") or r_dict.get("id"))
                    if key in published_content_map:
                        existing = published_content_map[key]
                        r_dict["times_used"] = max(int(existing.get("times_used", 0)), int(r_dict.get("times_used", 0)))
                        if existing.get("last_used_at") and (not r_dict.get("last_used_at") or existing["last_used_at"] > r_dict["last_used_at"]):
                            r_dict["last_used_at"] = existing["last_used_at"]
                    published_content_map[key] = r_dict
                    published_ids_set.add(str(r_dict["id"]))
                    if r_dict.get("content_uid"):
                        published_ids_set.add(str(r_dict["content_uid"]))
                    if r_dict.get("content_hash"):
                        published_ids_set.add(str(r_dict["content_hash"]))

            # 2b. publication_history
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='publication_history'")
            if cursor.fetchone():
                cursor.execute("""
                    SELECT p.id, p.video_id, p.platform, p.status, p.remote_url, p.remote_id, p.error_message, p.attempted_at,
                           d.content_hash, d.content_uid
                    FROM publication_history p
                    LEFT JOIN video_records v ON v.id = p.video_id
                    LEFT JOIN duas_meta d ON d.id = v.dua_id
                    ORDER BY p.id DESC LIMIT 200
                """)
                for r in cursor.fetchall():
                    p_dict = dict(r)
                    pkey = p_dict.get("remote_id") or f"{p_dict.get('video_id')}_{p_dict.get('platform')}_{p_dict.get('attempted_at')}"
                    publications_map[pkey] = p_dict

            # 2c. repurpose_clips
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='repurpose_clips'")
            if cursor.fetchone():
                cursor.execute("""
                    SELECT clip_id, source_id, clip_index, start_sec, end_sec, duration_sec,
                           title, transcript_snippet, reframing_strategy, video_path, preview_path,
                           caption, status, dropbox_url, dropbox_id, error_message, retry_count,
                           created_at, updated_at
                    FROM repurpose_clips
                """)
                for r in cursor.fetchall():
                    c_dict = dict(r)
                    cid = c_dict.get("clip_id")
                    if cid:
                        repurpose_clips_map[cid] = c_dict
                        if c_dict.get("status") in ("UPLOADED", "HANDED_OFF_TO_MAKE", "COMPLETED"):
                            published_clips_set.add(cid)

            # 2d. repurpose_sources
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='repurpose_sources'")
            if cursor.fetchone():
                cursor.execute("""
                    SELECT source_id, source_type, source_url, title, channel, duration, language, rights_confirmed, status, created_at, updated_at
                    FROM repurpose_sources
                """)
                for r in cursor.fetchall():
                    s_dict = dict(r)
                    sid = s_dict.get("source_id")
                    if sid:
                        repurpose_sources_map[sid] = s_dict

            # 2e. autopilot_queue
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='autopilot_queue'")
            if cursor.fetchone():
                cursor.execute("""
                    SELECT source_entry, source_hash, status, num_clips_produced,
                           error_message, attempts, queued_at, completed_at, updated_at,
                           channel, rights_confirmed, preferred_start, preferred_end, clip_ids
                    FROM autopilot_queue
                """)
                for r in cursor.fetchall():
                    ap_dict = dict(r)
                    shash = ap_dict.get("source_hash")
                    if shash:
                        autopilot_queue_map[shash] = ap_dict

            # 2f. nasheed_usage
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='nasheed_usage'")
            if cursor.fetchone():
                cursor.execute("""
                    SELECT track_id, track_title, times_used, last_used_at, created_at
                    FROM nasheed_usage
                """)
                for r in cursor.fetchall():
                    nh_dict = dict(r)
                    tid = nh_dict.get("track_id")
                    if tid:
                        if tid in nasheed_history_map:
                            prev_nh = nasheed_history_map[tid]
                            nh_dict["times_used"] = max(int(prev_nh.get("times_used", 0)), int(nh_dict.get("times_used", 0)))
                            if prev_nh.get("last_used_at") and (not nh_dict.get("last_used_at") or prev_nh["last_used_at"] > nh_dict["last_used_at"]):
                                nh_dict["last_used_at"] = prev_nh["last_used_at"]
                        nasheed_history_map[tid] = nh_dict

        return {
            "version": "2.0",
            "last_sync": datetime.utcnow().isoformat() + "Z",
            "published_content": list(published_content_map.values()),
            "published_content_ids": sorted(list(published_ids_set)),
            "published_clips": sorted(list(published_clips_set)),
            "publications": list(publications_map.values()),
            "repurpose_clips": list(repurpose_clips_map.values()),
            "repurpose_sources": list(repurpose_sources_map.values()),
            "autopilot_queue": list(autopilot_queue_map.values()),
            "nasheed_history": list(nasheed_history_map.values())
        }


# Global singleton instance
state_manager = StateSyncManager()

"""
state_sync.py — Persistent State Synchronization for GitHub Actions Runners
NoorPost Ultimate

Features:
- Ephemeral Runner Resilience: GitHub Actions runners are temporary; this module synchronizes
  publication history, content usage, autopilot queue status, and duplicate prevention state
  between Dropbox and local SQLite.
- Make.com Trigger Isolation: State files are stored in '/NoorPost_State/noorpost_state.json',
  guaranteeing zero interference with the Make.com trigger folder ('/NoorPost/*.mp4').
- Idempotency: Merges state without repeatedly incrementing usage counters when pull_state
  is invoked across multiple runs or tests.
- Fail-Closed Security: If Dropbox credentials are configured but persistent remote state
  cannot be retrieved or validated (due to network or authentication errors, not initial absence),
  it fails closed to protect production against duplicate publishing.
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

    def _get_dbx_client(self):
        """Obtain Dropbox client if configured."""
        try:
            from instagram import get_dropbox_client
            return get_dropbox_client()
        except Exception:
            return None

    # ── State Pull (Run at beginning of workflow) ────────────────────────────────
    def pull_state(self, fail_closed: bool = True) -> Dict[str, Any]:
        """
        Download the persistent state file from Dropbox and sync into local SQLite.
        Returns the parsed state dictionary.
        Fails closed if Dropbox is configured but remote download encounters an error.
        """
        init_db()
        dbx = self._get_dbx_client()
        state_data = None

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
                        )

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
        Export publication records from SQLite and upload the persistent state to Dropbox.
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

        dbx = self._get_dbx_client()
        if not dbx:
            log("ℹ️  Dropbox not configured; state saved locally only.", level="INFO")
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
        Reconciles authentic content, autopilot queue, and publication history.
        """
        if not state_data:
            return

        with _get_connection() as conn:
            cursor = conn.cursor()

            # 1. Reconcile published_content (v2.0 format)
            pub_content = state_data.get("published_content", [])
            merged_count = 0
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
                            merged_count += 1
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
                            merged_count += 1

            # 2. Reconcile legacy published_content_ids (v1.0 format)
            legacy_ids = state_data.get("published_content_ids", [])
            if legacy_ids and not pub_content:
                for cid in legacy_ids:
                    # Idempotent: set times_used to at least 1, never repeatedly increment
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
                        merged_count += 1

            # 3. Reconcile autopilot queue
            ap_items = state_data.get("autopilot_queue", [])
            if ap_items:
                cursor.execute("PRAGMA table_info(autopilot_queue)")
                if len(cursor.fetchall()) > 0:
                    for ap in ap_items:
                        s_hash = ap.get("source_hash")
                        s_entry = ap.get("source_entry")
                        if not s_hash or not s_entry:
                            continue
                        cursor.execute("""
                            INSERT INTO autopilot_queue (
                                source_entry, source_hash, status, num_clips_produced,
                                error_message, attempts, queued_at, completed_at, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT(source_hash) DO UPDATE SET
                                status = CASE 
                                    WHEN excluded.status IN ('COMPLETED', 'SKIPPED') THEN excluded.status 
                                    WHEN autopilot_queue.status IN ('COMPLETED', 'SKIPPED') THEN autopilot_queue.status 
                                    ELSE excluded.status 
                                END,
                                num_clips_produced = MAX(autopilot_queue.num_clips_produced, excluded.num_clips_produced),
                                completed_at = COALESCE(excluded.completed_at, autopilot_queue.completed_at),
                                updated_at = excluded.updated_at
                        """, (
                            s_entry, s_hash, ap.get("status", "QUEUED"),
                            ap.get("num_clips_produced", 0), ap.get("error_message"),
                            ap.get("attempts", 0), ap.get("queued_at", datetime.now().isoformat()),
                            ap.get("completed_at"), ap.get("updated_at", datetime.now().isoformat())
                        ))

            # 4. Reconcile publication history (prevents duplicates across runner instances)
            pub_hist = state_data.get("publications", [])
            if pub_hist:
                for pub in pub_hist:
                    v_id = pub.get("video_id")
                    plat = pub.get("platform", "instagram")
                    stat = pub.get("status", "success")
                    att = pub.get("attempted_at", datetime.now().isoformat())
                    if v_id:
                        cursor.execute("""
                            SELECT id FROM publication_history
                            WHERE video_id = ? AND platform = ? AND status = ?
                        """, (v_id, plat, stat))
                        if not cursor.fetchone():
                            cursor.execute("""
                                INSERT INTO publication_history (video_id, platform, status, remote_url, remote_id, error_message, attempted_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (v_id, plat, stat, pub.get("remote_url"), pub.get("remote_id"), pub.get("error_message"), att))

            conn.commit()
            if merged_count > 0:
                log(f"🗄️  Merged {merged_count} published content record(s) into SQLite.")

    def _build_state_from_sqlite(self) -> Dict[str, Any]:
        """Compile state dictionary from SQLite tables."""
        published_content = []
        published_ids = []
        publications = []
        published_clips = []
        repurpose_clips = []
        repurpose_sources = []
        autopilot_queue = []

        with _get_connection() as conn:
            cursor = conn.cursor()

            # 1. Published duas / hadith
            cursor.execute("""
                SELECT id, content_hash, content_uid, source, times_used, last_used_at, category
                FROM duas_meta
                WHERE times_used > 0
            """)
            for row in cursor.fetchall():
                r_dict = dict(row)
                published_content.append(r_dict)
                published_ids.append(r_dict["id"])
                if r_dict.get("content_uid"):
                    published_ids.append(r_dict["content_uid"])
                if r_dict.get("content_hash"):
                    published_ids.append(r_dict["content_hash"])

            # 2. Publication history
            cursor.execute("""
                SELECT p.id, p.video_id, p.platform, p.status, p.remote_url, p.remote_id, p.error_message, p.attempted_at,
                       d.content_hash, d.content_uid
                FROM publication_history p
                LEFT JOIN video_records v ON v.id = p.video_id
                LEFT JOIN duas_meta d ON d.id = v.dua_id
                ORDER BY p.id DESC LIMIT 150
            """)
            for r in cursor.fetchall():
                publications.append(dict(r))

            # 3. Repurposed clips
            cursor.execute("""
                SELECT clip_id, source_id, clip_index, start_sec, end_sec, duration_sec,
                       title, status, dropbox_url, dropbox_id, error_message, updated_at
                FROM repurpose_clips
            """)
            for r in cursor.fetchall():
                c_dict = dict(r)
                repurpose_clips.append(c_dict)
                if c_dict.get("status") in ("UPLOADED", "HANDED_OFF_TO_MAKE"):
                    published_clips.append(c_dict["clip_id"])

            # 4. Repurpose sources
            cursor.execute("""
                SELECT source_id, source_type, source_url, title, channel, duration, status, updated_at
                FROM repurpose_sources
            """)
            for r in cursor.fetchall():
                repurpose_sources.append(dict(r))

            # 5. Autopilot queue
            cursor.execute("PRAGMA table_info(autopilot_queue)")
            if len(cursor.fetchall()) > 0:
                cursor.execute("""
                    SELECT source_entry, source_hash, status, num_clips_produced,
                           error_message, attempts, queued_at, completed_at, updated_at
                    FROM autopilot_queue
                """)
                for r in cursor.fetchall():
                    autopilot_queue.append(dict(r))

        return {
            "version": "2.0",
            "last_sync": datetime.utcnow().isoformat() + "Z",
            "published_content": published_content,
            "published_content_ids": list(set(str(x) for x in published_ids)),
            "published_clips": published_clips,
            "publications": publications,
            "repurpose_clips": repurpose_clips,
            "repurpose_sources": repurpose_sources,
            "autopilot_queue": autopilot_queue,
        }


# Global singleton instance
state_manager = StateSyncManager()

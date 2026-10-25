"""
state_sync.py — Persistent State Synchronization for GitHub Actions Runners
NoorPost Ultimate

Features:
- Ephemeral Runner Resilience: GitHub Actions runners are temporary; this module synchronizes
  publication history and duplicate prevention state between Dropbox and local SQLite.
- Make.com Trigger Isolation: State files are stored in '/NoorPost_State/noorpost_state.json',
  guaranteeing zero interference with the Make.com trigger folder ('/NoorPost/*.mp4').
- Idempotency & Duplicate Prevention: Ensures already published Hadith, Duas, and Repurposed
  video clips are never re-published across separate GitHub Actions runs.
- Graceful offline / test fallback: Operates locally if Dropbox credentials are not present.
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
    def pull_state(self) -> Dict[str, Any]:
        """
        Download the persistent state file from Dropbox and sync into local SQLite.
        Returns the parsed state dictionary.
        """
        init_db()
        dbx = self._get_dbx_client()
        state_data = None

        if dbx:
            try:
                log("☁️  Checking Dropbox for persistent state file (/NoorPost_State/noorpost_state.json)...")
                metadata, response = dbx.files_download(DROPBOX_STATE_FILE)
                state_data = json.loads(response.content.decode("utf-8"))
                log(f"✅ Persistent state successfully downloaded from Dropbox (last synced: {state_data.get('last_sync')}).")
            except Exception as e:
                # File not found is expected on initial run
                log(f"ℹ️  Remote state not found or inaccessible ({e}). Initializing from local.", level="INFO")

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
            "version": "1.0",
            "last_sync": datetime.utcnow().isoformat() + "Z",
            "published_content_ids": [],
            "published_clips": [],
            "publications": [],
            "nasheed_history": []
        }

    def _merge_into_sqlite(self, state_data: Dict[str, Any]) -> None:
        """Merge published content items from remote state into SQLite."""
        pub_ids = state_data.get("published_content_ids", [])
        if not pub_ids:
            return

        with _get_connection() as conn:
            cursor = conn.cursor()
            for cid in pub_ids:
                # Update times_used and last_used in duas_meta
                cursor.execute("""
                    UPDATE duas_meta
                    SET times_used = times_used + 1,
                        last_used_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (cid,))
            conn.commit()
            log(f"🗄️  Merged {len(pub_ids)} published content record(s) into SQLite.")

    def _build_state_from_sqlite(self) -> Dict[str, Any]:
        """Compile state dictionary from SQLite tables."""
        published_ids = []
        publications = []

        with _get_connection() as conn:
            cursor = conn.cursor()
            # Published duas / hadith
            cursor.execute("SELECT id FROM duas_meta WHERE times_used > 0")
            published_ids = [row[0] for row in cursor.fetchall()]

            # Publication history
            cursor.execute("""
                SELECT video_id, platform, status, remote_url, remote_id, attempted_at
                FROM publication_history
                ORDER BY id DESC LIMIT 100
            """)
            for r in cursor.fetchall():
                publications.append({
                    "video_id": r[0],
                    "platform": r[1],
                    "status": r[2],
                    "remote_url": r[3],
                    "remote_id": r[4],
                    "attempted_at": r[5]
                })

            # Repurposed clips
            cursor.execute("SELECT clip_id FROM repurpose_clips WHERE status IN ('UPLOADED', 'HANDED_OFF_TO_MAKE')")
            published_clips = [row[0] for row in cursor.fetchall()]

        return {
            "version": "1.0",
            "last_sync": datetime.utcnow().isoformat() + "Z",
            "published_content_ids": published_ids,
            "published_clips": published_clips,
            "publications": publications,
        }


# Global singleton instance
state_manager = StateSyncManager()

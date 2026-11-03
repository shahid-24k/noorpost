"""
sunnah_api.py — Official Sunnah.com API Client & Sahih Verification Engine
NoorPost Ultimate

Features:
- Secure API key handling via SUNNAH_API_KEY environment variable.
- Support for official endpoints: /v1/collections, /v1/collections/{col}/hadiths/{num}, /v1/hadiths/random.
- Strict Sahih-Only Verification Policy (Bukhari & Muslim consensus, or explicit scholarly Sahih grading).
- Robust local caching (assets/cache/sunnah_cache.json) to minimize server load.
- Rate limit backoff and error handling.
- Safe offline fallback when API key is unconfigured.
"""

import os
import re
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

import requests
from logger import log
import config

BASE_URL = "https://api.sunnah.com/v1"
CACHE_DIR = Path("assets/cache")
CACHE_FILE = CACHE_DIR / "sunnah_cache.json"

# Universal Consensus Sahih Collections
# Sunni consensus uniformly accepts that narrations in the primary texts of Bukhari and Muslim are Sahih.
CANONICAL_SAHIH_COLLECTIONS = {
    "bukhari": "Sahih al-Bukhari",
    "muslim": "Sahih Muslim",
}

# Recognized Hadith Collection Display Names
COLLECTION_DISPLAY_NAMES = {
    "bukhari": "Sahih al-Bukhari",
    "muslim": "Sahih Muslim",
    "nasai": "Sunan an-Nasa'i",
    "abudawud": "Sunan Abi Dawud",
    "tirmidhi": "Jami` at-Tirmidhi",
    "ibnmajah": "Sunan Ibn Majah",
    "malik": "Muwatta Malik",
    "ahmad": "Musnad Ahmad",
    "darimi": "Sunan ad-Darimi",
    "nawawi40": "40 Hadith an-Nawawi",
    "qudsi40": "40 Hadith Qudsi",
    "riyadussalihin": "Riyadh as-Salihin",
}


class SunnahApiClient:
    """Official Sunnah.com API client with strict Sahih verification and caching."""

    def __init__(self, api_key: Optional[str] = None, base_url: str = BASE_URL):
        self.api_key = (api_key or os.getenv("SUNNAH_API_KEY") or getattr(config, "SUNNAH_API_KEY", "")).strip()
        self.base_url = base_url.rstrip("/")
        self.cache_file = CACHE_FILE
        self._cache = self._load_cache()

    # ── Cache Management ─────────────────────────────────────────────────────────
    def _load_cache(self) -> Dict[str, Any]:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_cache(self) -> None:
        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            log(f"Failed to save Sunnah API cache: {e}", level="WARNING")

    def is_configured(self) -> bool:
        """Returns True if an API key is available."""
        return bool(self.api_key)

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/json",
            "User-Agent": "NoorPost-Ultimate/2.3 (Islamic Educational Content Engine)"
        }
        if self.api_key:
            headers["x-api-key"] = self.api_key
        return headers

    # ── Network Request Helper with Rate Limiting ────────────────────────────────
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None, max_retries: int = 3) -> Optional[Dict[str, Any]]:
        """Make an authenticated request to the Sunnah.com API with retry handling."""
        if not self.is_configured():
            log("Sunnah.com API key not configured (SUNNAH_API_KEY missing).", level="INFO")
            return None

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        cache_key = f"{url}?{json.dumps(params or {}, sort_keys=True)}"

        # Return cached response if available
        if cache_key in self._cache:
            return self._cache[cache_key]

        headers = self._get_headers()

        for attempt in range(1, max_retries + 1):
            try:
                resp = requests.get(url, headers=headers, params=params, timeout=12)
                if resp.status_code == 200:
                    data = resp.json()
                    # Cache successful response
                    self._cache[cache_key] = data
                    self._save_cache()
                    return data
                elif resp.status_code == 429:
                    # Rate limited: exponential backoff
                    wait_sec = attempt * 2
                    log(f"Sunnah.com API rate limited (429). Retrying in {wait_sec}s...", level="WARNING")
                    time.sleep(wait_sec)
                elif resp.status_code in (401, 403):
                    log(f"Sunnah.com API authentication failed ({resp.status_code}). Check SUNNAH_API_KEY.", level="ERROR")
                    return None
                elif resp.status_code == 404:
                    log(f"Sunnah.com resource not found: {endpoint}", level="WARNING")
                    return None
                else:
                    log(f"Sunnah.com API HTTP error {resp.status_code}: {resp.text[:120]}", level="WARNING")
            except requests.exceptions.RequestException as e:
                log(f"Sunnah.com API request failed (attempt {attempt}/{max_retries}): {e}", level="WARNING")
                time.sleep(1)

        return None

    # ── API Endpoints ────────────────────────────────────────────────────────────
    def get_collections(self) -> List[Dict[str, Any]]:
        """Fetch list of all available Hadith collections."""
        data = self._make_request("collections")
        if data and isinstance(data, dict):
            # API can return {"data": [...]} or list directly
            return data.get("data", data if isinstance(data, list) else [])
        elif isinstance(data, list):
            return data
        return []

    def get_hadith(self, collection: str, hadith_number: str | int) -> Optional[Dict[str, Any]]:
        """Fetch specific Hadith by collection slug and number."""
        clean_col = collection.lower().strip()
        endpoint = f"collections/{clean_col}/hadiths/{hadith_number}"
        data = self._make_request(endpoint)
        if not data:
            return None
        # Handle response formats: standard {"data": {...}} or direct object
        if isinstance(data, dict) and "data" in data and isinstance(data["data"], dict):
            return data["data"]
        return data if isinstance(data, dict) else None

    def get_random_hadith(self, collection: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Fetch a random Hadith (optionally restricted to a specific collection)."""
        params = {"collection": collection.lower().strip()} if collection else None
        data = self._make_request("hadiths/random", params=params)
        if not data:
            return None
        if isinstance(data, dict) and "data" in data and isinstance(data["data"], dict):
            return data["data"]
        return data if isinstance(data, dict) else None

    # ── Strict Sahih Authenticity Verification ──────────────────────────────────
    @staticmethod
    def verify_hadith_authenticity(hadith_data: Dict[str, Any]) -> Tuple[bool, str, Optional[str]]:
        """
        Verify whether a Hadith record strictly qualifies as Sahih.

        Rules:
        1. Canonical Consensus: Sahih al-Bukhari and Sahih Muslim are universally recognized
           by Sunni scholarship as inherently Sahih.
        2. Explicit Scholarly Grading: For all other collections (Abu Dawud, Tirmidhi, Nasa'i, etc.),
           the record MUST possess an explicit grade string containing 'Sahih' (e.g. 'Sahih', 'Sahih Isnad',
           'Sahih li-ghayrihi') from a recognized authority, AND must NOT contain negative terms
           (such as 'Da'if', 'Daeef', 'Weak', 'Hasan', 'Mawdu', 'Fabricated').
        3. All unverified, missing-grade, Hasan, or Da'if items are strictly REJECTED.

        Returns:
            Tuple[is_sahih, reason_or_justification, grading_authority]
        """
        collection = hadith_data.get("collection", "").lower().strip()
        grades = hadith_data.get("grades", []) or []

        # 1. Check explicit grades
        sahih_matches = []
        for g in grades:
            if not isinstance(g, dict):
                continue
            grade_str = str(g.get("grade", "")).strip()
            scholar = str(g.get("scholar", "Scholarly Authority")).strip()
            grade_lower = grade_str.lower()

            # Reject any grading containing negative or non-Sahih qualifiers
            if any(neg in grade_lower for neg in ["da'if", "daeef", "weak", "hasan", "mawdu", "fabricated", "munkar"]):
                continue

            # Must contain 'sahih'
            if "sahih" in grade_lower:
                sahih_matches.append((scholar, grade_str))

        if sahih_matches:
            scholar, grade_str = sahih_matches[0]
            return True, f"Explicit grading: {grade_str}", scholar

        # 2. Check canonical consensus justification (Bukhari & Muslim only)
        if collection in CANONICAL_SAHIH_COLLECTIONS:
            corpus_name = CANONICAL_SAHIH_COLLECTIONS[collection]
            return True, f"{corpus_name} — Universal Consensus Sahih Collection", "Canonical Sahih Corpus Consensus"

        # 3. Reject everything else
        return False, f"Collection '{collection}' requires explicit Sahih grade; none verified.", None

    # ── Content Record Formatting for NoorPost Video Generator ──────────────────
    def format_hadith_record(self, raw_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert a raw Sunnah.com API Hadith into a standardized NoorPost content item.
        Returns None if authenticity cannot be established.
        """
        is_sahih, reason, scholar = self.verify_hadith_authenticity(raw_data)
        if not is_sahih:
            log(f"Hadith rejected by authenticity policy: {reason}", level="INFO")
            return None

        collection_slug = raw_data.get("collection", "bukhari").lower().strip()
        collection_display = COLLECTION_DISPLAY_NAMES.get(collection_slug, collection_slug.capitalize())
        hadith_num = str(raw_data.get("hadithNumber") or raw_data.get("hadith_number") or "").strip()

        # Extract Arabic and English texts
        arabic_text = ""
        english_text = ""
        narrator = ""

        # Format 1: raw_data has 'hadith' list with 'lang' entries
        if "hadith" in raw_data and isinstance(raw_data["hadith"], list):
            for entry in raw_data["hadith"]:
                if isinstance(entry, dict):
                    lang = entry.get("lang", "")
                    body = self._clean_html(entry.get("body", ""))
                    if lang == "ar":
                        arabic_text = body
                    elif lang == "en":
                        english_text = body
                        narrator = self._extract_narrator(body)

        # Format 2: raw_data has direct 'arabic' and 'english' keys
        if not arabic_text and "arabic" in raw_data:
            arabic_text = self._clean_html(str(raw_data["arabic"]))
        if not english_text and "english" in raw_data:
            if isinstance(raw_data["english"], dict):
                english_text = self._clean_html(str(raw_data["english"].get("text", "")))
                narrator = raw_data["english"].get("narrator", "")
            else:
                english_text = self._clean_html(str(raw_data["english"]))
                narrator = self._extract_narrator(english_text)

        if not arabic_text and not english_text:
            return None

        hadith_id = f"sunnah_{collection_slug}_{hadith_num or int(time.time())}"
        source_ref = f"{collection_display} {hadith_num}".strip()
        grading_str = f"Sahih ({scholar})" if scholar else "Sahih"

        return {
            "id": hadith_id,
            "category": "prophetic_hadith",
            "type": "Prophetic Hadith",
            "arabic": arabic_text,
            "transliteration": "",
            "translation": english_text,
            "narrator": narrator,
            "source": source_ref,
            "collection": collection_slug,
            "hadith_number": hadith_num,
            "is_verified": 1,
            "review_status": "approved",
            "grading": grading_str,
            "grading_authority": scholar or "Canonical Consensus",
            "source_url": f"https://sunnah.com/{collection_slug}:{hadith_num}" if hadith_num else "https://sunnah.com",
            "retrieval_date": datetime.now().strftime("%Y-%m-%d"),
            "verification_status": "verified_sahih",
            "commentary": f"Authentic narration from {collection_display}. Attribution: Sunnah.com.",
            "tags": f"prophetic_hadith,sahih,{collection_slug}",
        }

    @staticmethod
    def _clean_html(text: str) -> str:
        """Strip HTML tags and normalize whitespace."""
        clean = re.sub(r"<[^>]+>", " ", text)
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean

    @staticmethod
    def _extract_narrator(text: str) -> str:
        """Attempt to extract narrator from initial English sentence (e.g. 'Narrated Abu Huraira:')."""
        match = re.match(r"^(?:Narrated|Narrator:?)\s+([A-Za-z\s'\-]+?):", text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ""


# Global singleton client instance
sunnah_client = SunnahApiClient()

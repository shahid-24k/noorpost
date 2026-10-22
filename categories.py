"""
categories.py — Canonical Content Categories for NoorPost Ultimate
Defines 13 verified Islamic content categories, their visual theme pairings,
presentation badges, and metadata.
"""

from typing import Dict, Any, List, Optional

CATEGORIES: Dict[str, Dict[str, Any]] = {
    "daily_duas": {
        "id": "daily_duas",
        "name": "Daily Duas",
        "arabic_name": "الأدعية اليومية",
        "description": "Essential authentic supplications for daily moments (waking, sleeping, leaving home, meals).",
        "badge": "DAILY DUA",
        "default_theme": "midnight-gold",
        "default_layout": "dua",
        "tags": ["dua", "daily", "sunnah", "prophetic"],
    },
    "morning_adhkar": {
        "id": "morning_adhkar",
        "name": "Morning Adhkar",
        "arabic_name": "أذكار الصباح",
        "description": "Authentic morning supplications and daily remembrances from the Sunnah.",
        "badge": "MORNING ADHKAR",
        "default_theme": "peaceful-nature",
        "default_layout": "dua",
        "tags": ["adhkar", "morning", "protection", "sunnah"],
    },
    "evening_adhkar": {
        "id": "evening_adhkar",
        "name": "Evening Adhkar",
        "arabic_name": "أذكار المساء",
        "description": "Authentic evening supplications for protection and peace before nightfall.",
        "badge": "EVENING ADHKAR",
        "default_theme": "reflective-night",
        "default_layout": "dua",
        "tags": ["adhkar", "evening", "protection", "peace"],
    },
    "gratitude_patience": {
        "id": "gratitude_patience",
        "name": "Gratitude and Patience",
        "arabic_name": "الشكر والصبر",
        "description": "Verses and hadith on Shukr (gratitude) and Sabr (patience) through trials.",
        "badge": "SABR & SHUKR",
        "default_theme": "emerald-serenity",
        "default_layout": "quran",
        "tags": ["gratitude", "patience", "sabr", "shukr", "trials"],
    },
    "forgiveness_repentance": {
        "id": "forgiveness_repentance",
        "name": "Repentance and Forgiveness",
        "arabic_name": "الاستغفار والتوبة",
        "description": "Sayyid al-Istighfar, sincere repentance (Tawbah), and Allah's boundless mercy.",
        "badge": "SEEKING FORGIVENESS",
        "default_theme": "midnight-gold",
        "default_layout": "dua",
        "tags": ["istighfar", "tawbah", "mercy", "forgiveness"],
    },
    "remembrance_dhikr": {
        "id": "remembrance_dhikr",
        "name": "Remembrance of Allah",
        "arabic_name": "ذكر الله",
        "description": "Tasbih, Tahmid, Tahlil, and Takbir — the heaviest deeds on the Scales.",
        "badge": "DHIKR & REMEMBRANCE",
        "default_theme": "midnight-gold",
        "default_layout": "dua",
        "tags": ["dhikr", "tasbih", "tahmid", "rewards"],
    },
    "quranic_verses": {
        "id": "quranic_verses",
        "name": "Quranic Verses",
        "arabic_name": "آيات قرآنية",
        "description": "Profound ayaat of hope, tawheed, reflection, and guidance from the Noble Qur'an.",
        "badge": "THE NOBLE QUR'AN",
        "default_theme": "masjid-elegance",
        "default_layout": "quran",
        "tags": ["quran", "ayah", "tawheed", "guidance"],
    },
    "prophetic_hadith": {
        "id": "prophetic_hadith",
        "name": "Hadith and Prophetic Teachings",
        "arabic_name": "الأحاديث النبوية",
        "description": "Authentic sayings and character of the Prophet Muhammad ﷺ from Sahih collections.",
        "badge": "PROPHETIC TEACHING",
        "default_theme": "emerald-serenity",
        "default_layout": "reminder",
        "tags": ["hadith", "sunnah", "prophetic", "bukhari", "muslim"],
    },
    "short_reminders": {
        "id": "short_reminders",
        "name": "Short Islamic Reminders",
        "arabic_name": "تذكير إيماني",
        "description": "Concise, powerful spiritual reminders to soften the heart and realign intentions.",
        "badge": "FAITH REMINDER",
        "default_theme": "minimal-white",
        "default_layout": "reminder",
        "tags": ["reminder", "iman", "taqwa", "heart"],
    },
    "ramadan": {
        "id": "ramadan",
        "name": "Ramadan Content",
        "arabic_name": "رمضان المبارك",
        "description": "Fasting duas, Laylat al-Qadr supplications, and virtues of the blessed month.",
        "badge": "RAMADAN REMINDER",
        "default_theme": "ramadan-eid",
        "default_layout": "dua",
        "tags": ["ramadan", "fasting", "iftar", "qadr", "suhoor"],
    },
    "friday_reminders": {
        "id": "friday_reminders",
        "name": "Friday Reminders",
        "arabic_name": "يوم الجمعة",
        "description": "Virtues of Jumu'ah, sending blessings (Salawat) upon the Prophet ﷺ, and Surat al-Kahf.",
        "badge": "JUMU'AH REMINDER",
        "default_theme": "masjid-elegance",
        "default_layout": "reminder",
        "tags": ["friday", "jumuah", "salawat", "kahf"],
    },
    "eid_content": {
        "id": "eid_content",
        "name": "Eid Content",
        "arabic_name": "تكبيرات وأدعية العيد",
        "description": "Eid Takbeerat, authentic sunnahs, and prayers for Eid al-Fitr and Eid al-Adha.",
        "badge": "EID MUBARAK",
        "default_theme": "ramadan-eid",
        "default_layout": "reminder",
        "tags": ["eid", "takbeer", "celebration", "sunnah"],
    },
    "general_education": {
        "id": "general_education",
        "name": "General Islamic Education",
        "arabic_name": "فوائد إسلامية",
        "description": "Fundamental virtues, Islamic etiquette (Adab), and core principles of the Deen.",
        "badge": "ISLAMIC WISDOM",
        "default_theme": "minimal-white",
        "default_layout": "reminder",
        "tags": ["education", "adab", "virtues", "akhlaq"],
    },
}

# Aliases for flexible category lookups
CATEGORY_ALIASES = {
    "daily": "daily_duas",
    "duas": "daily_duas",
    "dua": "daily_duas",
    "morning": "morning_adhkar",
    "morning_dhikr": "morning_adhkar",
    "evening": "evening_adhkar",
    "evening_dhikr": "evening_adhkar",
    "gratitude": "gratitude_patience",
    "patience": "gratitude_patience",
    "sabr": "gratitude_patience",
    "shukr": "gratitude_patience",
    "forgiveness": "forgiveness_repentance",
    "repentance": "forgiveness_repentance",
    "istighfar": "forgiveness_repentance",
    "tawbah": "forgiveness_repentance",
    "dhikr": "remembrance_dhikr",
    "tasbih": "remembrance_dhikr",
    "remembrance": "remembrance_dhikr",
    "quran": "quranic_verses",
    "verse": "quranic_verses",
    "verses": "quranic_verses",
    "hadith": "prophetic_hadith",
    "sunnah": "prophetic_hadith",
    "reminder": "short_reminders",
    "reminders": "short_reminders",
    "jumuah": "friday_reminders",
    "friday": "friday_reminders",
    "jummah": "friday_reminders",
    "education": "general_education",
    "adab": "general_education",
}

def resolve_category(category_name: Optional[str]) -> Optional[Dict[str, Any]]:
    """Resolve category dictionary from name or alias."""
    if not category_name:
        return None
    key = category_name.strip().lower().replace("-", "_").replace(" ", "_")
    canonical = CATEGORY_ALIASES.get(key, key)
    return CATEGORIES.get(canonical)

def get_all_category_keys() -> List[str]:
    """Return all 13 canonical category IDs."""
    return list(CATEGORIES.keys())


def get_next_category_in_rotation(last_category: Optional[str] = None, prioritize_friday: bool = True) -> str:
    """
    Select the next category in sequential rotation.
    If today is Friday and prioritize_friday is True, prioritizes friday_reminders.
    """
    from datetime import datetime
    if prioritize_friday and datetime.now().weekday() == 4:
        return "friday_reminders"

    keys = list(CATEGORIES.keys())
    if not last_category or last_category not in keys:
        return keys[0]

    current_idx = keys.index(last_category)
    next_idx = (current_idx + 1) % len(keys)
    # If rotation would pick friday_reminders on a non-Friday, skip to next to keep Friday special
    if keys[next_idx] == "friday_reminders" and datetime.now().weekday() != 4:
        next_idx = (next_idx + 1) % len(keys)
    return keys[next_idx]

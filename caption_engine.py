"""
caption_engine.py — Configurable Islamic Caption & Hashtag Engine for NoorPost Ultimate
Generates beautiful, varied, platform-optimized captions for Instagram Reels and YouTube Shorts.

Religious Integrity Principles:
- Strictly preserves sacred Arabic wording and source citations.
- Separates authentic religious citations from human reflections.
- Avoids clickbait, fabricated virtues, or sensationalist claims.
- Curates moderate, relevant hashtags (avoids spammy tag walls).
"""

from typing import Dict, Any, List, Optional
import random
from categories import resolve_category

# Supported Caption Styles
CAPTION_STYLES = [
    "short",          # Crisp & minimalist: Arabic + translation + source
    "reflective",     # Contemplative thought + sacred text + reflection
    "educational",    # Prophetic context + text + lesson + reference
    "daily_dua",      # Memorization focus + phonetics + translation
    "quranic_verse",  # Deep Quranic focus with Surah/Ayah citation
    "friday_jumuah",  # Friday Sunnah & Salawat focus
    "reminder"        # Short heart-softener & faith re-alignment
]

# Curated, moderate category-specific hashtag sets (5-8 tags each, never excessive)
CATEGORY_HASHTAGS: Dict[str, List[str]] = {
    "daily_duas": [
        "#DailyDua", "#IslamicDua", "#Sunnah", "#MuslimFaith", "#IslamicReminders", "#Alhamdulillah", "#Supplication"
    ],
    "morning_adhkar": [
        "#MorningAdhkar", "#Dhikr", "#MorningRemembrance", "#Sunnah", "#ProtectionDua", "#MuslimMorning", "#SubhanAllah"
    ],
    "evening_adhkar": [
        "#EveningAdhkar", "#NightDua", "#IslamicRemembrance", "#ProtectionInIslam", "#Sunnah", "#Alhamdulillah", "#Peace"
    ],
    "gratitude_patience": [
        "#SabrAndShukr", "#IslamicPatience", "#GratitudeInIslam", "#Tawakkul", "#FaithThroughTrials", "#QuranicWisdom"
    ],
    "forgiveness_repentance": [
        "#Tawbah", "#Istighfar", "#AllahForgives", "#SayyidAlIstighfar", "#RepentanceInIslam", "#MercyOfAllah"
    ],
    "remembrance_dhikr": [
        "#DhikrOfAllah", "#Tasbih", "#SubhanAllah", "#Alhamdulillah", "#AllahuAkbar", "#RemembranceOfAllah", "#HeartTranquility"
    ],
    "quranic_verses": [
        "#NobleQuran", "#QuranicVerse", "#AyahOfTheDay", "#Tadabbur", "#WordsOfAllah", "#QuranGuidance"
    ],
    "prophetic_hadith": [
        "#PropheticHadith", "#AuthenticSunnah", "#HadithOfTheDay", "#ProphetMuhammadﷺ", "#IslamicEthics", "#BukhariMuslim"
    ],
    "short_reminders": [
        "#IslamicReminder", "#DeenOverDunya", "#SoftHeart", "#MuslimReflection", "#FaithJourney", "#ShortReminder"
    ],
    "ramadan": [
        "#RamadanKareem", "#RamadanDua", "#LaylatAlQadr", "#FastingInIslam", "#RamadanMubarak", "#IftarReflection"
    ],
    "friday_reminders": [
        "#JumuahMubarak", "#FridaySunnah", "#Salawat", "#DuroodShareef", "#SurahAlKahf", "#BlessedFriday"
    ],
    "eid_content": [
        "#EidMubarak", "#EidTakbeerat", "#SunnahOfEid", "#MuslimCelebration", "#PraiseAllah", "#EidUlFitr", "#EidUlAdha"
    ],
    "general_education": [
        "#LearnIslam", "#IslamicWisdom", "#IslamicManners", "#AdabInIslam", "#SeekKnowledge", "#MuslimCommunity"
    ]
}

DEFAULT_BASE_TAGS = ["#Islam", "#Muslim", "#Faith"]

def get_hashtags(category: str, custom_tags: Optional[List[str]] = None, max_tags: int = 7) -> str:
    """Generate a clean, moderate hashtag string."""
    if custom_tags is not None:
        return " ".join(t if t.startswith("#") else f"#{t}" for t in custom_tags[:max_tags])

    cat_tags = CATEGORY_HASHTAGS.get(category, CATEGORY_HASHTAGS["daily_duas"])
    # Pick a balanced selection without spam
    selected = cat_tags[:max_tags]
    return " ".join(selected)

def generate_caption(
    content: Dict[str, Any],
    style: Optional[str] = None,
    include_hashtags: bool = True,
    custom_hashtags: Optional[List[str]] = None,
    language: str = "en"
) -> str:
    """
    Generate an engaging, religiously accurate social media caption.
    Strictly preserves Arabic text and authentic source citations.
    """
    category = content.get("category", "daily_duas")
    arabic = content.get("arabic", "").strip()
    translation = content.get("translation", "").strip()
    transliteration = content.get("transliteration", "").strip()
    source = content.get("source", "").strip()
    commentary = content.get("commentary", "").strip()
    grading = content.get("grading", "Sahih")
    narrator = content.get("narrator", "")

    cat_meta = resolve_category(category) or {}
    badge = cat_meta.get("badge", "ISLAMIC REMINDER")

    # Pick style if not provided or invalid
    if not style or style not in CAPTION_STYLES:
        if category == "friday_reminders":
            style = "friday_jumuah"
        elif category == "quranic_verses":
            style = "quranic_verse"
        elif category in ("daily_duas", "morning_adhkar", "evening_adhkar"):
            style = random.choice(["daily_dua", "reflective", "short"])
        elif category in ("prophetic_hadith", "general_education"):
            style = "educational"
        else:
            style = random.choice(["reflective", "reminder", "short"])

    tags_block = get_hashtags(category, custom_tags=custom_hashtags) if include_hashtags else ""

    # Build caption by style
    if style == "short":
        caption = (
            f"✨ {badge}\n\n"
            f"{arabic}\n\n"
            f'"{translation}"\n\n'
            f"📖 Reference: {source}"
        )

    elif style == "reflective":
        caption = (
            f"🌙 {badge}\n\n"
            f"{arabic}\n\n"
            f'"{translation}"\n\n'
        )
        if commentary:
            caption += f"💡 Reflection:\n{commentary}\n\n"
        caption += f"📖 Source: {source}\n\nTake a moment to reflect and save this reminder."

    elif style == "educational":
        caption = f"📚 {badge}\n\n"
        if narrator:
            caption += f"Narrated by {narrator}:\n\n"
        caption += (
            f"{arabic}\n\n"
            f'"{translation}"\n\n'
        )
        if commentary:
            caption += f"🔍 Understanding & Context:\n{commentary}\n\n"
        caption += f"✅ Source: {source} ({grading})"

    elif style == "daily_dua":
        caption = (
            f"🤲 DAILY SUPPLICATION\n\n"
            f"{arabic}\n\n"
        )
        if transliteration:
            caption += f"🗣️ Transliteration:\n{transliteration}\n\n"
        caption += (
            f"Meaning:\n\"{translation}\"\n\n"
            f"📖 Source: {source}\n\n"
            f"Save and memorize this beautiful prayer."
        )

    elif style == "quranic_verse":
        surah_ref = content.get("surah_name", "")
        verse_num = content.get("verse_number", "")
        ref_header = f"Surah {surah_ref} [{verse_num}]" if surah_ref and verse_num else source
        caption = (
            f"📖 THE NOBLE QUR'AN — {ref_header}\n\n"
            f"{arabic}\n\n"
            f'"{translation}"\n\n'
        )
        if commentary:
            caption += f"🤍 Contemplation:\n{commentary}\n\n"
        caption += f"Recited from {source}."

    elif style == "friday_jumuah":
        caption = (
            f"🕌 JUMU'AH MUBARAK ✨\n\n"
            f"On this blessed Friday, remember to send abundant Salawat upon the Messenger of Allah ﷺ and recite Surat Al-Kahf.\n\n"
            f"{arabic}\n\n"
            f'"{translation}"\n\n'
            f"📖 Source: {source}"
        )

    else: # reminder
        caption = (
            f"📿 FAITH REMINDER\n\n"
            f"{arabic}\n\n"
            f'"{translation}"\n\n'
        )
        if commentary:
            caption += f"🌱 Note: {commentary}\n\n"
        caption += f"🔖 Reference: {source}"

    if tags_block:
        caption += f"\n\n{tags_block}"

    return caption

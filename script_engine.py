"""
script_engine.py — Engaging & Source-Conscious Video Script Engine for NoorPost Ultimate
Generates structured, vertical-video-optimized scripts for Reels and Shorts.

Religious Integrity Guardrails:
- Sacred Arabic text is strictly immutable.
- Religious commentary/reflections are clearly separated from sacred texts.
- Never invents spiritual rewards, fabricated promises, or religious rulings.
- Avoids exaggerated clickbait, fear-based sensationalism, and misleading claims.
"""

from typing import Dict, Any, List, Optional
import random

# Available Script Styles
SCRIPT_STYLES = [
    "reflective",      # Contemplative question + sacred text + heartfelt reflection
    "educational",     # Contextual background + prophetic Sunnah + practical takeaway
    "daily_habit",     # Everyday practical connection + supplication + encouragement
    "inspirational",   # Hope and trust in Allah + Quranic/Hadith anchor
    "direct_sacred"    # Minimalist presentation: pure sacred text + translation + source
]

# Category-aware authentic opening hooks (Respectful, genuine, non-clickbait)
HOOKS_BY_CATEGORY: Dict[str, List[str]] = {
    "daily_duas": [
        "A beautiful prophetic supplication to begin your day with purpose.",
        "When you need peace and protection in your daily routine, remember this dua.",
        "The Prophet ﷺ taught us this timeless prayer for everyday guidance.",
        "A short supplication with profound meaning for every believer."
    ],
    "morning_adhkar": [
        "Start your morning by remembering the Creator of every dawn.",
        "The Sunnah of the morning: beginning your day in the protection of Allah.",
        "A blessed reminder from the morning adhkar to illuminate your day.",
        "As the morning unfolds, center your heart with this remembrance."
    ],
    "evening_adhkar": [
        "As daylight fades, find tranquility in this evening remembrance.",
        "A Sunnah supplication for peace and divine protection before nightfall.",
        "Close your day with gratitude and seek refuge in Allah's mercy.",
        "An authentic evening dhikr to bring calmness to your heart."
    ],
    "gratitude_patience": [
        "When trials feel heavy, this divine guidance offers true solace.",
        "Between gratitude and patience lies the entire strength of a believer.",
        "A timeless reminder on how thankfulness multiplies your blessings.",
        "How the believer finds peace in both prosperity and adversity."
    ],
    "forgiveness_repentance": [
        "No matter where you find yourself today, never despair of Allah's mercy.",
        "A heartfelt supplication turning back to the Most Forgiving.",
        "The door of repentance is always open for the sincere heart.",
        "Learn the words the Prophet ﷺ loved to recite for forgiveness."
    ],
    "remembrance_dhikr": [
        "Two simple words that are light on the tongue, yet heavy on the Scales.",
        "In the constant busyness of life, pause to revive your heart with dhikr.",
        "The Prophet ﷺ reminded us of the immense virtues of constant remembrance.",
        "A moment of reflection on the supreme remembrance of Allah."
    ],
    "quranic_verses": [
        "A verse of deep contemplation and guidance from the Noble Qur'an.",
        "Let this divine ayah bring reassurance and clarity to your day.",
        "The words of our Creator: guidance, healing, and mercy for the believers.",
        "Reflect upon this profound message revealed in the Qur'an."
    ],
    "prophetic_hadith": [
        "A golden prophetic teaching to refine our character and manners.",
        "The Messenger of Allah ﷺ shared timeless wisdom for our daily lives.",
        "From the authentic Sunnah: a guiding principle for every situation.",
        "A prophetic reminder on faith, sincerity, and upright conduct."
    ],
    "short_reminders": [
        "A brief spiritual reminder to carry with you through the week.",
        "Pause for 15 seconds to reflect on what truly matters.",
        "A simple Islamic truth that realigns our daily focus.",
        "Gentle words of wisdom to uplift your spiritual journey."
    ],
    "ramadan": [
        "A blessed supplication from the Sunnah for the season of devotion.",
        "Maximizing the virtues of fasting with heartfelt prayer.",
        "A cherished dua taught by the Prophet ﷺ for seeking forgiveness.",
        "Embracing the spiritual atmosphere of the blessed days of Ramadan."
    ],
    "friday_reminders": [
        "Jumu'ah Mubarak — remember to send abundant blessings upon the Prophet ﷺ.",
        "The blessed day of Friday: a time for prayer, reflection, and Surah Al-Kahf.",
        "Reviving the Sunnah on the best day upon which the sun has risen.",
        "A Friday reminder to elevate our prayers and send Salawat upon the Messenger ﷺ."
    ],
    "eid_content": [
        "Celebrating the blessings of Allah with authentic Takbeerat and joy.",
        "The Sunnah of Eid: glorifying Allah in gratitude and spreading peace.",
        "A joyous occasion of praise, connection, and spiritual renewal.",
        "Reviving the authentic Takbeerat on these blessed days."
    ],
    "general_education": [
        "An essential Islamic principle that enriches our daily conduct.",
        "Understanding the beauty and balance of our faith.",
        "A foundational teaching on community, compassion, and character.",
        "Islamic wisdom for personal growth and spiritual refinement."
    ]
}

# Respectful closing reflections (no exaggerated claims)
CLOSING_REMINDERS: List[str] = [
    "Save this reminder to revisit whenever you need grounding.",
    "Share this with someone who might need to hear it today.",
    "May Allah grant us understanding and sincerity in our practice.",
    "May Allah accept our supplications and bless your day.",
    "Recite this with conviction and presence of heart."
]

def generate_script(
    content: Dict[str, Any],
    style: Optional[str] = None,
    include_transliteration: bool = True
) -> Dict[str, Any]:
    """
    Generate a vertical short-form video script with distinct segments.
    Ensures strict separation between religious source text and human reflection.
    """
    category = content.get("category", "daily_duas")
    content_type = content.get("type", "Authentic Reminder")
    arabic = content.get("arabic", "").strip()
    translation = content.get("translation", "").strip()
    transliteration = content.get("transliteration", "").strip()
    source = content.get("source", "").strip()
    commentary = content.get("commentary", "").strip()

    # Determine style
    chosen_style = style if style in SCRIPT_STYLES else "reflective"

    # 1. Select Hook
    category_hooks = HOOKS_BY_CATEGORY.get(category, HOOKS_BY_CATEGORY["daily_duas"])
    hook = random.choice(category_hooks) if chosen_style != "direct_sacred" else ""

    # 2. Select Closing
    closing = random.choice(CLOSING_REMINDERS) if chosen_style != "direct_sacred" else ""

    # 3. Assemble Segments
    segments = []
    if hook:
        segments.append({
            "segment_type": "hook",
            "title": "Opening Hook",
            "text": hook,
            "scene": 1,
            "duration_hint": 3
        })

    segments.append({
        "segment_type": "sacred_text",
        "title": "Sacred Arabic Text",
        "text": arabic,
        "scene": 2 if hook else 1,
        "duration_hint": 5
    })

    if include_transliteration and transliteration:
        segments.append({
            "segment_type": "transliteration",
            "title": "Transliteration",
            "text": transliteration,
            "scene": 2 if hook else 1,
            "duration_hint": 3
        })

    segments.append({
        "segment_type": "translation",
        "title": "English Translation",
        "text": f'"{translation}"',
        "scene": 3 if hook else 2,
        "duration_hint": 5
    })

    if commentary and chosen_style in ("reflective", "educational", "daily_habit"):
        segments.append({
            "segment_type": "reflection",
            "title": "Reflection & Context",
            "text": commentary,
            "scene": 4 if hook else 3,
            "duration_hint": 4
        })

    segments.append({
        "segment_type": "source",
        "title": "Verified Reference",
        "text": f"Reference: {source}",
        "scene": 4 if hook else 3,
        "duration_hint": 2
    })

    if closing:
        segments.append({
            "segment_type": "closing",
            "title": "Closing Reminder",
            "text": closing,
            "scene": 5 if hook else 4,
            "duration_hint": 3
        })

    # Assemble Full Narration Script
    narration_parts = []
    if hook:
        narration_parts.append(hook)
    narration_parts.append(f"In the sacred text: {arabic}")
    narration_parts.append(f"Translation: {translation}")
    if commentary and chosen_style != "direct_sacred":
        narration_parts.append(f"Reflection: {commentary}")
    narration_parts.append(f"Source: {source}")
    if closing:
        narration_parts.append(closing)

    full_narration = " \n\n".join(narration_parts)

    return {
        "style": chosen_style,
        "category": category,
        "content_type": content_type,
        "hook": hook,
        "arabic": arabic,
        "transliteration": transliteration if include_transliteration else "",
        "translation": translation,
        "reflection": commentary,
        "source": source,
        "closing": closing,
        "segments": segments,
        "full_narration": full_narration,
        "estimated_duration_sec": sum(s["duration_hint"] for s in segments)
    }

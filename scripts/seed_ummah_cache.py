import json
from pathlib import Path

cache_path = Path("assets/cache/ummah_cache.json")
cache = {}
if cache_path.exists():
    try:
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
    except Exception:
        cache = {}

now = "2026-11-07T14:40:00Z"

# Surahs
cache['https://ummahapi.com/api/quran/surahs?{}'] = {
    "data": [
        {"number": 1, "name_arabic": "الفاتحة", "name_english": "Al-Fatihah", "total_ayahs": 7},
        {"number": 2, "name_arabic": "البقرة", "name_english": "Al-Baqarah", "total_ayahs": 286},
        {"number": 112, "name_arabic": "الإخلاص", "name_english": "Al-Ikhlas", "total_ayahs": 4}
    ],
    "cached_at": now
}

# Hadith collections
cache['https://ummahapi.com/api/hadith/collections?{}'] = {
    "data": [
        {"name": "bukhari", "title": "Sahih al-Bukhari", "total_hadith": 7563},
        {"name": "muslim", "title": "Sahih Muslim", "total_hadith": 7500}
    ],
    "cached_at": now
}

# Quran 1:1
cache['https://ummahapi.com/api/quran/surah/1/ayah/1?{}'] = {
    "data": {
        "surah": {"number": 1, "name_arabic": "الفاتحة", "name_english": "Al-Fatihah", "name_translation": "The Opening"},
        "verse": {
            "ayah": 1,
            "arabic": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
            "transliteration": "Bismillaahir Rahmaanir Raheem",
            "translations": {
                "sahih_international": "In the name of Allah, the Entirely Merciful, the Especially Merciful."
            }
        }
    },
    "cached_at": now
}

# Quran 1 (Full Surah)
cache['https://ummahapi.com/api/quran/surah/1?{}'] = {
    "data": {
        "surah": {"number": 1, "name_arabic": "الفاتحة", "name_english": "Al-Fatihah", "name_translation": "The Opening"},
        "verses": [
            {
                "ayah": 1,
                "arabic": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
                "transliteration": "Bismillaahir Rahmaanir Raheem",
                "translations": {"sahih_international": "In the name of Allah, the Entirely Merciful, the Especially Merciful."}
            },
            {
                "ayah": 2,
                "arabic": "الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ",
                "transliteration": "Alhamdu lillaahi Rabbil 'aalameen",
                "translations": {"sahih_international": "[All] praise is [due] to Allah, Lord of the worlds -"}
            }
        ]
    },
    "cached_at": now
}

# Quran random
cache['https://ummahapi.com/api/quran/random?{}'] = {
    "data": {
        "surah": {"number": 1, "name_arabic": "الفاتحة", "name_english": "Al-Fatihah", "name_translation": "The Opening"},
        "verse": {
            "ayah": 1,
            "arabic": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
            "transliteration": "Bismillaahir Rahmaanir Raheem",
            "translations": {
                "sahih_international": "In the name of Allah, the Entirely Merciful, the Especially Merciful."
            }
        }
    },
    "cached_at": now
}

# Bukhari 1
cache['https://ummahapi.com/api/hadith/bukhari/1?{}'] = {
    "data": {
        "collection": "bukhari",
        "number": 1,
        "hadithnumber": 1,
        "arabic": "إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ، وَإِنَّمَا لِكُلِّ امْرِئٍ مَا نَوَى",
        "english": "Actions are according to intentions, and everyone will get what was intended for.",
        "grade": "Sahih"
    },
    "cached_at": now
}

# Bukhari random
bukhari_params = json.dumps({"collection": "bukhari"}, sort_keys=True)
cache[f"https://ummahapi.com/api/hadith/random?{bukhari_params}"] = {
    "data": {
        "collection": "bukhari",
        "number": 1,
        "hadithnumber": 1,
        "arabic": "إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ، وَإِنَّمَا لِكُلِّ امْرِئٍ مَا نَوَى",
        "english": "Actions are according to intentions, and everyone will get what was intended for.",
        "grade": "Sahih"
    },
    "cached_at": now
}

# Muslim 15
cache['https://ummahapi.com/api/hadith/muslim/15?{}'] = {
    "data": {
        "collection": "muslim",
        "number": 15,
        "hadithnumber": 15,
        "arabic": "بُنِيَ الإِسْلاَمُ عَلَى خَمْسٍ",
        "english": "Islam is built upon five pillars.",
        "grade": "Sahih"
    },
    "cached_at": now
}

# Muslim random
muslim_params = json.dumps({"collection": "muslim"}, sort_keys=True)
cache[f"https://ummahapi.com/api/hadith/random?{muslim_params}"] = {
    "data": {
        "collection": "muslim",
        "number": 15,
        "hadithnumber": 15,
        "arabic": "بُنِيَ الإِسْلاَمُ عَلَى خَمْسٍ",
        "english": "Islam is built upon five pillars.",
        "grade": "Sahih"
    },
    "cached_at": now
}

cache_path.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"UmmahAPI cache seeded successfully. Total cached endpoints: {len(cache)}")

"""
duas_db.py — Authentic Islamic Duas & Content Database for NoorPost Ultimate
Re-exports the complete authentic Islamic content library from content_db.py
and provides legacy caption templates for backward compatibility.
"""

from content_db import AUTHENTIC_CONTENT, DUAS

# Legacy Caption Templates (retained for backward compatibility)
CAPTION_TEMPLATES = [
    "✨ {type}\n\n{arabic}\n\n\"{translation}\"\n\n"
    "📖 {source}\n\nShare to earn Sadaqah Jariyah 🤍\n\n"
    "#Islam #Quran #Dua #Sunnah #Muslim #Hadith #DailyDua #IslamicReminder #Ummah #Alhamdulillah #Dhikr #Allah #Faith #Iman #SubhanAllah",

    "🌙 {type}\n\n{arabic}\n\n\"{translation}\"\n\n"
    "✅ Source: {source}\n\n"
    "#Dua #Dhikr #IslamicContent #Quran #Sunnah #Muslim #Hadith #Allah #Islam #Reminder #DailyQuran #Ummah #SubhanAllah #Alhamdulillah #MashAllah",

    "📿 {type}\n\n{arabic}\n\n\"{translation}\"\n\n"
    "🔖 {source}\n\n"
    "#IslamicPost #DailyQuran #Sunnah #MuslimCommunity #Dua #Dhikr #Alhamdulillah #IslamicReminder #Hadith #Faith #Iman #SubhanAllah #Muslim",

    "🤲 Memorize this beautiful dua:\n\n{arabic}\n\n\"{translation}\"\n\n"
    "📖 {source} | {type}\n\n"
    "#DuaOfTheDay #Islam #Quran #Sunnah #Muslim #IslamicReminder #Dhikr #Allah #Ummah #Hadith #DailyDua #Alhamdulillah #SubhanAllah #MashAllah #Faith",

    "☪️ {type}\n\n{arabic}\n\n\"{translation}\"\n\n"
    "✅ {source}\n\n"
    "#AuthenticIslam #Quran #Hadith #Dua #Sunnah #Muslim #IslamicContent #DailyReminder #Allah #Iman #Dhikr #Salah #Ummah #NoorPost #Islam",
]

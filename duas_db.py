"""
duas_db.py — Authentic Islamic content database
All duas verified from Sahih sources (Quran, Bukhari, Muslim, etc.)
"""

DUAS = [
    # ── QUR'ANIC DUAS ──────────────────────────────────────
    {
        "arabic":          "رَبَّنَا آتِنَا فِي الدُّنْيَا حَسَنَةً وَفِي الْآخِرَةِ حَسَنَةً وَقِنَا عَذَابَ النَّارِ",
        "transliteration": "Rabbana atina fid-dunya hasanatan wa fil-akhirati hasanatan wa qina 'adhab an-nar",
        "translation":     "Our Lord, grant us good in this world and good in the Hereafter, and protect us from the punishment of the Fire.",
        "source":          "Qur'an 2:201",
        "type":            "Qur'anic Dua",
    },
    {
        "arabic":          "رَبِّ زِدْنِي عِلْمًا",
        "transliteration": "Rabbi zidni 'ilma",
        "translation":     "My Lord, increase me in knowledge.",
        "source":          "Qur'an 20:114",
        "type":            "Qur'anic Dua",
    },
    {
        "arabic":          "حَسْبُنَا اللَّهُ وَنِعْمَ الْوَكِيلُ",
        "transliteration": "Hasbunallahu wa ni'mal-wakil",
        "translation":     "Allah is sufficient for us and He is the best Disposer of affairs.",
        "source":          "Qur'an 3:173",
        "type":            "Qur'anic Dua",
    },
    {
        "arabic":          "رَبَّنَا لَا تُزِغْ قُلُوبَنَا بَعْدَ إِذْ هَدَيْتَنَا وَهَبْ لَنَا مِن لَّدُنكَ رَحْمَةً",
        "transliteration": "Rabbana la tuzigh qulubana ba'da idh hadaytana wa hab lana min ladunka rahmah",
        "translation":     "Our Lord, let not our hearts deviate after You have guided us and grant us from Yourself mercy.",
        "source":          "Qur'an 3:8",
        "type":            "Qur'anic Dua",
    },
    {
        "arabic":          "رَبِّ اشْرَحْ لِي صَدْرِي وَيَسِّرْ لِي أَمْرِي",
        "transliteration": "Rabbi-shrah li sadri wa yassir li amri",
        "translation":     "My Lord, expand my chest and ease my task for me.",
        "source":          "Qur'an 20:25-26",
        "type":            "Qur'anic Dua",
    },
    {
        "arabic":          "رَبَّنَا ظَلَمْنَا أَنفُسَنَا وَإِن لَّمْ تَغْفِرْ لَنَا وَتَرْحَمْنَا لَنَكُونَنَّ مِنَ الْخَاسِرِينَ",
        "transliteration": "Rabbana zalamna anfusana wa in lam taghfir lana wa tarhamna lanakunanna minal-khasirin",
        "translation":     "Our Lord, we have wronged ourselves, and if You do not forgive us and have mercy upon us, we will surely be among the losers.",
        "source":          "Qur'an 7:23",
        "type":            "Qur'anic Dua",
    },
    {
        "arabic":          "لَّا إِلَٰهَ إِلَّا أَنتَ سُبْحَانَكَ إِنِّي كُنتُ مِنَ الظَّالِمِينَ",
        "transliteration": "La ilaha illa anta subhanaka inni kuntu minaz-zalimin",
        "translation":     "There is no deity except You; exalted are You. Indeed, I have been of the wrongdoers.",
        "source":          "Qur'an 21:87 (Dua of Yunus AS)",
        "type":            "Qur'anic Dua",
    },
    {
        "arabic":          "رَبِّ إِنِّي لِمَا أَنزَلْتَ إِلَيَّ مِنْ خَيْرٍ فَقِيرٌ",
        "transliteration": "Rabbi inni lima anzalta ilayya min khayrin faqir",
        "translation":     "My Lord, indeed I am in need of whatever good You would send down to me.",
        "source":          "Qur'an 28:24 (Dua of Musa AS)",
        "type":            "Qur'anic Dua",
    },

    # ── MORNING ADHKAR ─────────────────────────────────────
    {
        "arabic":          "اللَّهُمَّ أَنْتَ رَبِّي لَا إِلَٰهَ إِلَّا أَنْتَ خَلَقْتَنِي وَأَنَا عَبْدُكَ وَأَنَا عَلَىٰ عَهْدِكَ وَوَعْدِكَ مَا اسْتَطَعْتُ",
        "transliteration": "Allahumma anta rabbi la ilaha illa anta, khalaqtani wa ana 'abduka, wa ana 'ala 'ahdika wa wa'dika mastata't",
        "translation":     "O Allah, You are my Lord. None has the right to be worshipped except You. You created me and I am Your slave, and I am faithful to my covenant and my promise to You as much as I can.",
        "source":          "Sahih Bukhari 6306 — Sayyid al-Istighfar",
        "type":            "Morning Adhkar",
    },
    {
        "arabic":          "أَصْبَحْنَا وَأَصْبَحَ الْمُلْكُ لِلَّهِ وَالْحَمْدُ لِلَّهِ لَا إِلَٰهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ",
        "transliteration": "Asbahna wa asbahal mulku lillah, walhamdu lillah, la ilaha illallahu wahdahu la sharika lah",
        "translation":     "We have reached the morning and at this very time the whole dominion belongs to Allah. All praise is for Allah. None has the right to be worshipped except Allah, alone, without any partner.",
        "source":          "Sahih Muslim 2723",
        "type":            "Morning Adhkar",
    },

    # ── EVENING ADHKAR ─────────────────────────────────────
    {
        "arabic":          "أَمْسَيْنَا وَأَمْسَى الْمُلْكُ لِلَّهِ وَالْحَمْدُ لِلَّهِ لَا إِلَٰهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ",
        "transliteration": "Amsayna wa amsal mulku lillah, walhamdu lillah, la ilaha illallahu wahdahu la sharika lah",
        "translation":     "We have reached the evening and at this very time the whole dominion belongs to Allah. All praise is for Allah. None has the right to be worshipped except Allah, alone, without any partner.",
        "source":          "Sahih Muslim 2723",
        "type":            "Evening Adhkar",
    },

    # ── PROPHETIC DUAS ─────────────────────────────────────
    {
        "arabic":          "اللَّهُمَّ إِنِّي أَعُوذُ بِكَ مِنَ الْهَمِّ وَالْحَزَنِ وَالْعَجْزِ وَالْكَسَلِ",
        "transliteration": "Allahumma inni a'udhu bika minal-hammi wal-hazan wal-'ajzi wal-kasal",
        "translation":     "O Allah, I seek refuge in You from grief, sadness, incapacity and laziness.",
        "source":          "Sahih Bukhari 6369",
        "type":            "Prophetic Dua",
    },
    {
        "arabic":          "اللَّهُمَّ اهْدِنِي وَسَدِّدْنِي",
        "transliteration": "Allahumma-hdini wa saddidni",
        "translation":     "O Allah, guide me and make me steadfast.",
        "source":          "Sahih Muslim 2725",
        "type":            "Prophetic Dua",
    },
    {
        "arabic":          "اللَّهُمَّ إِنِّي أَسْأَلُكَ الْعَافِيَةَ فِي الدُّنْيَا وَالْآخِرَةِ",
        "transliteration": "Allahumma inni as'alukal-'afiyata fid-dunya wal-akhirah",
        "translation":     "O Allah, I ask You for well-being in this world and the Hereafter.",
        "source":          "Sunan Ibn Majah 3871 — Sahih",
        "type":            "Prophetic Dua",
    },
    {
        "arabic":          "اللَّهُمَّ أَصْلِحْ لِي دِينِي الَّذِي هُوَ عِصْمَةُ أَمْرِي",
        "transliteration": "Allahumma aslih li dini alladhi huwa 'ismatu amri",
        "translation":     "O Allah, set right my religion which is the safeguard of my affairs.",
        "source":          "Sahih Muslim 2720",
        "type":            "Prophetic Dua",
    },

    # ── ISTIGHFAR ──────────────────────────────────────────
    {
        "arabic":          "رَبِّ اغْفِرْ لِي وَتُبْ عَلَيَّ إِنَّكَ أَنْتَ التَّوَّابُ الْغَفُورُ",
        "transliteration": "Rabbi-ghfir li wa tub 'alayya innaka anta-t-Tawwabul Ghafur",
        "translation":     "My Lord, forgive me and accept my repentance. Verily You are the Ever-Returning, the Oft-Forgiving.",
        "source":          "Sahih Bukhari 834",
        "type":            "Istighfar",
    },
    {
        "arabic":          "أَسْتَغْفِرُ اللَّهَ الْعَظِيمَ الَّذِي لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ وَأَتُوبُ إِلَيْهِ",
        "transliteration": "Astaghfirullahil-'Azim alladhi la ilaha illa huwal-Hayyul-Qayyum wa atubu ilaih",
        "translation":     "I seek forgiveness from Allah the Magnificent, besides Whom none has the right to be worshipped, the Ever-Living, the Sustainer, and I repent to Him.",
        "source":          "Sunan Abu Dawud 1517 — Sahih",
        "type":            "Istighfar",
    },

    # ── TASBIH ─────────────────────────────────────────────
    {
        "arabic":          "سُبْحَانَ اللَّهِ وَبِحَمْدِهِ سُبْحَانَ اللَّهِ الْعَظِيمِ",
        "transliteration": "SubhanAllahi wa bihamdihi, SubhanAllahil-'Adhim",
        "translation":     "Glory be to Allah and His is the praise. Glory be to Allah the Magnificent.",
        "source":          "Sahih Bukhari 6682",
        "type":            "Tasbih",
    },
    {
        "arabic":          "سُبْحَانَ اللَّهِ وَالْحَمْدُ لِلَّهِ وَلَا إِلَٰهَ إِلَّا اللَّهُ وَاللَّهُ أَكْبَرُ",
        "transliteration": "SubhanAllah, walhamdulillah, wa la ilaha illallah, wallahu Akbar",
        "translation":     "Glory be to Allah, all praise is for Allah, none has the right to be worshipped except Allah, and Allah is the Greatest.",
        "source":          "Sahih Muslim 2695",
        "type":            "Tasbih",
    },
]

# Caption templates
CAPTION_TEMPLATES = [
    "✨ {type}\n\n{arabic}\n\n\"{translation}\"\n\n"
    "📖 Source: {source}\n\n"
    "Share to earn Sadaqah Jariyah 🤍\n\n"
    "#Islam #Quran #Dua #Sunnah #Muslim #Hadith #DailyDua #IslamicReminder #Ummah #Alhamdulillah #Dhikr #Allah #Faith #Iman #SubhanAllah",

    "🌙 {type}\n\n{arabic}\n\n\"{translation}\"\n\n"
    "✅ Authenticated: {source}\n\n"
    "#Dua #Dhikr #IslamicContent #Quran #Sunnah #Muslim #Hadith #Allah #Islam #Reminder #DailyQuran #Ummah #SubhanAllah #Alhamdulillah #MashAllah",

    "📿 Strengthen your connection with Allah SWT:\n\n"
    "{arabic}\n\n\"{translation}\"\n\n"
    "🔖 {source}\n\n"
    "#IslamicPost #DailyQuran #Sunnah #MuslimCommunity #Dua #Dhikr #Alhamdulillah #QuranDaily #IslamicReminder #Hadith #Salah #Faith #Iman #SubhanAllah #Muslim",
]

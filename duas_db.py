"""
duas_db.py — Complete Authentic Islamic Duas Database
All duas verified from Sahih sources only
"""

DUAS = [

    # ══════════════════════════════════════
    # QUR'ANIC DUAS
    # ══════════════════════════════════════
    {"arabic": "رَبَّنَا آتِنَا فِي الدُّنْيَا حَسَنَةً وَفِي الْآخِرَةِ حَسَنَةً وَقِنَا عَذَابَ النَّارِ",
     "transliteration": "Rabbana atina fid-dunya hasanatan wa fil-akhirati hasanatan wa qina 'adhab an-nar",
     "translation": "Our Lord, grant us good in this world and good in the Hereafter, and protect us from the punishment of the Fire.",
     "source": "Qur'an 2:201", "type": "Qur'anic Dua"},

    {"arabic": "رَبَّنَا تَقَبَّلْ مِنَّا إِنَّكَ أَنتَ السَّمِيعُ الْعَلِيمُ",
     "transliteration": "Rabbana taqabbal minna innaka antas-Sami'ul-'Alim",
     "translation": "Our Lord, accept from us. Indeed You are the Hearing, the Knowing.",
     "source": "Qur'an 2:127", "type": "Qur'anic Dua"},

    {"arabic": "رَبَّنَا وَاجْعَلْنَا مُسْلِمَيْنِ لَكَ وَمِن ذُرِّيَّتِنَا أُمَّةً مُّسْلِمَةً لَّكَ وَأَرِنَا مَنَاسِكَنَا وَتُبْ عَلَيْنَا",
     "transliteration": "Rabbana waj'alna muslimayni laka wa min dhurriyyatina ummatan muslimatan laka wa arina manasikana wa tub 'alayna",
     "translation": "Our Lord, make us Muslims submitted to You and from our descendants a Muslim nation. Show us our rites and accept our repentance.",
     "source": "Qur'an 2:128", "type": "Qur'anic Dua"},

    {"arabic": "رَبَّنَا لَا تُؤَاخِذْنَا إِن نَّسِينَا أَوْ أَخْطَأْنَا",
     "transliteration": "Rabbana la tu'akhidhna in nasina aw akhta'na",
     "translation": "Our Lord, do not impose blame upon us if we have forgotten or erred.",
     "source": "Qur'an 2:286", "type": "Qur'anic Dua"},

    {"arabic": "رَبَّنَا لَا تُحَمِّلْنَا مَا لَا طَاقَةَ لَنَا بِهِ وَاعْفُ عَنَّا وَاغْفِرْ لَنَا وَارْحَمْنَا أَنتَ مَوْلَانَا",
     "transliteration": "Rabbana wa la tuhammilna ma la taqata lana bih wa'fu 'anna waghfir lana warhamna anta mawlana",
     "translation": "Our Lord, do not burden us with what we cannot bear. Pardon us, forgive us, and have mercy upon us. You are our Guardian.",
     "source": "Qur'an 2:286", "type": "Qur'anic Dua"},

    {"arabic": "رَبَّنَا لَا تُزِغْ قُلُوبَنَا بَعْدَ إِذْ هَدَيْتَنَا وَهَبْ لَنَا مِن لَّدُنكَ رَحْمَةً إِنَّكَ أَنتَ الْوَهَّابُ",
     "transliteration": "Rabbana la tuzigh qulubana ba'da idh hadaytana wa hab lana min ladunka rahmah innaka antal-Wahhab",
     "translation": "Our Lord, let not our hearts deviate after You have guided us and grant us from Yourself mercy. Indeed You are the Bestower.",
     "source": "Qur'an 3:8", "type": "Qur'anic Dua"},

    {"arabic": "رَبَّنَا إِنَّكَ جَامِعُ النَّاسِ لِيَوْمٍ لَّا رَيْبَ فِيهِ إِنَّ اللَّهَ لَا يُخْلِفُ الْمِيعَادَ",
     "transliteration": "Rabbana innaka jami'un-nasi li-yawmil-la rayba fih innallaha la yukhlifu al-mi'ad",
     "translation": "Our Lord, surely You will gather the people for a Day about which there is no doubt. Indeed, Allah does not fail in His promise.",
     "source": "Qur'an 3:9", "type": "Qur'anic Dua"},

    {"arabic": "حَسْبُنَا اللَّهُ وَنِعْمَ الْوَكِيلُ",
     "transliteration": "Hasbunallahu wa ni'mal-wakil",
     "translation": "Allah is sufficient for us, and He is the best Disposer of affairs.",
     "source": "Qur'an 3:173", "type": "Qur'anic Dua"},

    {"arabic": "رَبَّنَا اغْفِرْ لَنَا ذُنُوبَنَا وَإِسْرَافَنَا فِي أَمْرِنَا وَثَبِّتْ أَقْدَامَنَا وَانصُرْنَا عَلَى الْقَوْمِ الْكَافِرِينَ",
     "transliteration": "Rabbana-ghfir lana dhunubana wa israfana fi amrina wa thabbit aqdamana wansurna 'alal-qawmil-kafirin",
     "translation": "Our Lord, forgive us our sins and the excess in our affairs, and plant firmly our feet, and give us victory over the disbelieving people.",
     "source": "Qur'an 3:147", "type": "Qur'anic Dua"},

    {"arabic": "رَبَّنَا مَا خَلَقْتَ هَٰذَا بَاطِلًا سُبْحَانَكَ فَقِنَا عَذَابَ النَّارِ",
     "transliteration": "Rabbana ma khalaqta hadha batilan subhanaka faqina 'adhab an-nar",
     "translation": "Our Lord, You did not create this without purpose; exalted are You, so protect us from the punishment of the Fire.",
     "source": "Qur'an 3:191", "type": "Qur'anic Dua"},

    {"arabic": "رَبَّنَا إِنَّنَا آمَنَّا فَاغْفِرْ لَنَا ذُنُوبَنَا وَقِنَا عَذَابَ النَّارِ",
     "transliteration": "Rabbana innana amanna faghfir lana dhunubana wa qina 'adhab an-nar",
     "translation": "Our Lord, indeed we have believed, so forgive us our sins and protect us from the punishment of the Fire.",
     "source": "Qur'an 3:16", "type": "Qur'anic Dua"},

    {"arabic": "رَبَّنَا آمَنَّا فَاكْتُبْنَا مَعَ الشَّاهِدِينَ",
     "transliteration": "Rabbana amanna faktubna ma'ash-shahidin",
     "translation": "Our Lord, we have believed, so register us among the witnesses.",
     "source": "Qur'an 5:83", "type": "Qur'anic Dua"},

    {"arabic": "رَبَّنَا لَا تَجْعَلْنَا مَعَ الْقَوْمِ الظَّالِمِينَ",
     "transliteration": "Rabbana la taj'alna ma'al-qawmiz-zalimin",
     "translation": "Our Lord, do not place us with the wrongdoing people.",
     "source": "Qur'an 7:47", "type": "Qur'anic Dua"},

    {"arabic": "رَبَّنَا ظَلَمْنَا أَنفُسَنَا وَإِن لَّمْ تَغْفِرْ لَنَا وَتَرْحَمْنَا لَنَكُونَنَّ مِنَ الْخَاسِرِينَ",
     "transliteration": "Rabbana zalamna anfusana wa in lam taghfir lana wa tarhamna lanakunanna minal-khasirin",
     "translation": "Our Lord, we have wronged ourselves, and if You do not forgive us and have mercy upon us, we will surely be among the losers.",
     "source": "Qur'an 7:23", "type": "Qur'anic Dua"},

    {"arabic": "رَبِّ اغْفِرْ وَارْحَمْ وَأَنتَ خَيْرُ الرَّاحِمِينَ",
     "transliteration": "Rabbi-ghfir warham wa anta khayrur-rahimin",
     "translation": "My Lord, forgive and have mercy, and You are the best of the merciful.",
     "source": "Qur'an 23:118", "type": "Qur'anic Dua"},

    {"arabic": "لَّا إِلَٰهَ إِلَّا أَنتَ سُبْحَانَكَ إِنِّي كُنتُ مِنَ الظَّالِمِينَ",
     "transliteration": "La ilaha illa anta subhanaka inni kuntu minaz-zalimin",
     "translation": "There is no deity except You; exalted are You. Indeed, I have been of the wrongdoers.",
     "source": "Qur'an 21:87 — Dua of Yunus AS", "type": "Qur'anic Dua"},

    {"arabic": "رَبِّ إِنِّي مَسَّنِيَ الضُّرُّ وَأَنتَ أَرْحَمُ الرَّاحِمِينَ",
     "transliteration": "Rabbi inni massaniyad-durru wa anta arhamur-rahimin",
     "translation": "My Lord, adversity has touched me, and You are the most merciful of the merciful.",
     "source": "Qur'an 21:83 — Dua of Ayyub AS", "type": "Qur'anic Dua"},

    {"arabic": "رَبِّ إِنِّي لِمَا أَنزَلْتَ إِلَيَّ مِنْ خَيْرٍ فَقِيرٌ",
     "transliteration": "Rabbi inni lima anzalta ilayya min khayrin faqir",
     "translation": "My Lord, indeed I am in need of whatever good You would send down to me.",
     "source": "Qur'an 28:24 — Dua of Musa AS", "type": "Qur'anic Dua"},

    {"arabic": "رَبِّ اشْرَحْ لِي صَدْرِي وَيَسِّرْ لِي أَمْرِي وَاحْلُلْ عُقْدَةً مِّن لِّسَانِي يَفْقَهُوا قَوْلِي",
     "transliteration": "Rabbi-shrah li sadri wa yassir li amri wahlul 'uqdatan min lisani yafqahu qawli",
     "translation": "My Lord, expand for me my chest, ease my task, and untie the knot from my tongue that they may understand my speech.",
     "source": "Qur'an 20:25-28 — Dua of Musa AS", "type": "Qur'anic Dua"},

    {"arabic": "رَبِّ زِدْنِي عِلْمًا",
     "transliteration": "Rabbi zidni 'ilma",
     "translation": "My Lord, increase me in knowledge.",
     "source": "Qur'an 20:114", "type": "Qur'anic Dua"},

    {"arabic": "رَبَّنَا هَبْ لَنَا مِنْ أَزْوَاجِنَا وَذُرِّيَّاتِنَا قُرَّةَ أَعْيُنٍ وَاجْعَلْنَا لِلْمُتَّقِينَ إِمَامًا",
     "transliteration": "Rabbana hab lana min azwajina wa dhurriyyatina qurrata a'yunin waj'alna lil-muttaqina imama",
     "translation": "Our Lord, grant us from among our wives and offspring comfort to our eyes and make us a leader for the righteous.",
     "source": "Qur'an 25:74", "type": "Qur'anic Dua"},

    {"arabic": "رَبِّ أَوْزِعْنِي أَنْ أَشْكُرَ نِعْمَتَكَ الَّتِي أَنْعَمْتَ عَلَيَّ وَعَلَىٰ وَالِدَيَّ وَأَنْ أَعْمَلَ صَالِحًا تَرْضَاهُ",
     "transliteration": "Rabbi awzi'ni an ashkura ni'matakal-lati an'amta 'alayya wa 'ala walidayya wa an a'mala salihan tardah",
     "translation": "My Lord, enable me to be grateful for Your favor upon me and my parents, and to do righteousness of which You approve.",
     "source": "Qur'an 27:19", "type": "Qur'anic Dua"},

    {"arabic": "رَبَّنَا وَسِعْتَ كُلَّ شَيْءٍ رَّحْمَةً وَعِلْمًا فَاغْفِرْ لِلَّذِينَ تَابُوا وَاتَّبَعُوا سَبِيلَكَ",
     "transliteration": "Rabbana wasi'ta kulla shay'ir rahmatan wa 'ilman faghfir lilladhina tabu wattaba'u sabilak",
     "translation": "Our Lord, You have encompassed all things in mercy and knowledge, so forgive those who have repented and followed Your way.",
     "source": "Qur'an 40:7", "type": "Qur'anic Dua"},

    {"arabic": "رَبَّنَا اغْفِرْ لَنَا وَلِإِخْوَانِنَا الَّذِينَ سَبَقُونَا بِالْإِيمَانِ وَلَا تَجْعَلْ فِي قُلُوبِنَا غِلًّا لِّلَّذِينَ آمَنُوا",
     "transliteration": "Rabbana-ghfir lana wa li-ikhwaninal-ladhina sabaquna bil-iman wa la taj'al fi qulubina ghillan lilladhina amanu",
     "translation": "Our Lord, forgive us and our brothers who preceded us in faith and put not in our hearts any resentment toward those who have believed.",
     "source": "Qur'an 59:10", "type": "Qur'anic Dua"},

    {"arabic": "رَبَّنَا أَتْمِمْ لَنَا نُورَنَا وَاغْفِرْ لَنَا إِنَّكَ عَلَىٰ كُلِّ شَيْءٍ قَدِيرٌ",
     "transliteration": "Rabbana atmim lana nurana waghfir lana innaka 'ala kulli shay'in qadir",
     "translation": "Our Lord, perfect our light for us and forgive us. Indeed, You are over all things competent.",
     "source": "Qur'an 66:8", "type": "Qur'anic Dua"},

    {"arabic": "رَبِّ اجْعَلْنِي مُقِيمَ الصَّلَاةِ وَمِن ذُرِّيَّتِي رَبَّنَا وَتَقَبَّلْ دُعَاءِ",
     "transliteration": "Rabbi-j'alni muqimas-salati wa min dhurriyyati Rabbana wa taqabbal du'a'",
     "translation": "My Lord, make me an establisher of prayer, and from my descendants. Our Lord, and accept my supplication.",
     "source": "Qur'an 14:40", "type": "Qur'anic Dua"},

    {"arabic": "رَبَّنَا اغْفِرْ لِي وَلِوَالِدَيَّ وَلِلْمُؤْمِنِينَ يَوْمَ يَقُومُ الْحِسَابُ",
     "transliteration": "Rabbana-ghfir li wa liwalidayya wa lil-mu'minina yawma yaqumul-hisab",
     "translation": "Our Lord, forgive me and my parents and the believers the Day the account is established.",
     "source": "Qur'an 14:41", "type": "Qur'anic Dua"},

    {"arabic": "رَّبِّ ارْحَمْهُمَا كَمَا رَبَّيَانِي صَغِيرًا",
     "transliteration": "Rabbi-rhamhuma kama rabbayani saghira",
     "translation": "My Lord, have mercy upon them as they brought me up when I was small.",
     "source": "Qur'an 17:24", "type": "Qur'anic Dua"},

    {"arabic": "رَبِّ أَدْخِلْنِي مُدْخَلَ صِدْقٍ وَأَخْرِجْنِي مُخْرَجَ صِدْقٍ وَاجْعَل لِّي مِن لَّدُنكَ سُلْطَانًا نَّصِيرًا",
     "transliteration": "Rabbi adkhilni mudkhala sidqin wa akhrijni mukhraja sidqin waj'al li min ladunka sultanan nasira",
     "translation": "My Lord, cause me to enter a sound entrance and to exit a sound exit and grant me from Yourself a supporting authority.",
     "source": "Qur'an 17:80", "type": "Qur'anic Dua"},

    {"arabic": "رَبَّنَا آتِنَا مِن لَّدُنكَ رَحْمَةً وَهَيِّئْ لَنَا مِنْ أَمْرِنَا رَشَدًا",
     "transliteration": "Rabbana atina min ladunka rahmatan wa hayyi' lana min amrina rashada",
     "translation": "Our Lord, grant us from Yourself mercy and prepare for us from our affair right guidance.",
     "source": "Qur'an 18:10", "type": "Qur'anic Dua"},

    {"arabic": "رَبِّ لَا تَذَرْنِي فَرْدًا وَأَنتَ خَيْرُ الْوَارِثِينَ",
     "transliteration": "Rabbi la tadharni fardan wa anta khayrul-waritheen",
     "translation": "My Lord, do not leave me alone, and You are the best of inheritors.",
     "source": "Qur'an 21:89 — Dua of Zakariyya AS", "type": "Qur'anic Dua"},

    {"arabic": "رَبِّ إِنِّي وَهَنَ الْعَظْمُ مِنِّي وَاشْتَعَلَ الرَّأْسُ شَيْبًا وَلَمْ أَكُن بِدُعَائِكَ رَبِّ شَقِيًّا",
     "transliteration": "Rabbi inni wahana al-'azmu minni wash-ta'alar-ra'su shayban wa lam akun bidu'a'ika rabbi shaqiyya",
     "translation": "My Lord, my bones have weakened, and my head has filled with white hair, and never have I been in my supplication to You, my Lord, unhappy.",
     "source": "Qur'an 19:4 — Dua of Zakariyya AS", "type": "Qur'anic Dua"},

    {"arabic": "رَبِّ هَبْ لِي مِنَ الصَّالِحِينَ",
     "transliteration": "Rabbi hab li minas-salihin",
     "translation": "My Lord, grant me a child from among the righteous.",
     "source": "Qur'an 37:100 — Dua of Ibrahim AS", "type": "Qur'anic Dua"},

    {"arabic": "رَبِّ إِنِّي أَعُوذُ بِكَ أَنْ أَسْأَلَكَ مَا لَيْسَ لِي بِهِ عِلْمٌ وَإِلَّا تَغْفِرْ لِي وَتَرْحَمْنِي أَكُن مِّنَ الْخَاسِرِينَ",
     "transliteration": "Rabbi inni a'udhu bika an as'alaka ma laysa li bihi 'ilmun wa illa taghfir li wa tarhamni akun minal-khasirin",
     "translation": "My Lord, I seek refuge in You from asking that of which I have no knowledge. And unless You forgive me and have mercy upon me, I will be among the losers.",
     "source": "Qur'an 11:47 — Dua of Nuh AS", "type": "Qur'anic Dua"},

    {"arabic": "إِنِّي تَوَكَّلْتُ عَلَى اللَّهِ رَبِّي وَرَبِّكُمْ مَّا مِن دَابَّةٍ إِلَّا هُوَ آخِذٌ بِنَاصِيَتِهَا",
     "transliteration": "Inni tawakkaltu 'alallahi rabbi wa rabbikum ma min dabbatin illa huwa akhidhun binasiyatiha",
     "translation": "I have put my trust in Allah, my Lord and your Lord. There is no creature but that He holds its forelock.",
     "source": "Qur'an 11:56", "type": "Qur'anic Dua"},

    # ══════════════════════════════════════
    # MORNING ADHKAR
    # ══════════════════════════════════════
    {"arabic": "اللَّهُمَّ أَنْتَ رَبِّي لَا إِلَٰهَ إِلَّا أَنْتَ خَلَقْتَنِي وَأَنَا عَبْدُكَ وَأَنَا عَلَىٰ عَهْدِكَ وَوَعْدِكَ مَا اسْتَطَعْتُ",
     "transliteration": "Allahumma anta rabbi la ilaha illa anta, khalaqtani wa ana 'abduka, wa ana 'ala 'ahdika wa wa'dika mastata't",
     "translation": "O Allah, You are my Lord. None has the right to be worshipped except You. You created me and I am Your slave, faithful to my covenant and promise as best I can.",
     "source": "Sahih Bukhari 6306 — Sayyid al-Istighfar", "type": "Morning Adhkar"},

    {"arabic": "أَصْبَحْنَا وَأَصْبَحَ الْمُلْكُ لِلَّهِ وَالْحَمْدُ لِلَّهِ لَا إِلَٰهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ",
     "transliteration": "Asbahna wa asbahal mulku lillah, walhamdu lillah, la ilaha illallahu wahdahu la sharika lah",
     "translation": "We have reached the morning and at this very time the whole dominion belongs to Allah. All praise is for Allah. None has the right to be worshipped except Allah, alone, without any partner.",
     "source": "Sahih Muslim 2723", "type": "Morning Adhkar"},

    {"arabic": "اللَّهُمَّ بِكَ أَصْبَحْنَا وَبِكَ أَمْسَيْنَا وَبِكَ نَحْيَا وَبِكَ نَمُوتُ وَإِلَيْكَ النُّشُورُ",
     "transliteration": "Allahumma bika asbahna wa bika amsayna wa bika nahya wa bika namutu wa ilaykan-nushur",
     "translation": "O Allah, by You we enter the morning, by You we enter the evening, by You we live, by You we die, and to You is the resurrection.",
     "source": "Sunan Abu Dawud 5068 — Sahih", "type": "Morning Adhkar"},

    {"arabic": "اللَّهُمَّ عَافِنِي فِي بَدَنِي اللَّهُمَّ عَافِنِي فِي سَمْعِي اللَّهُمَّ عَافِنِي فِي بَصَرِي",
     "transliteration": "Allahumma 'afini fi badani, Allahumma 'afini fi sam'i, Allahumma 'afini fi basari",
     "translation": "O Allah, grant me health in my body. O Allah, grant me health in my hearing. O Allah, grant me health in my sight.",
     "source": "Sunan Abu Dawud 5090 — Sahih", "type": "Morning Adhkar"},

    {"arabic": "أَعُوذُ بِاللَّهِ السَّمِيعِ الْعَلِيمِ مِنَ الشَّيْطَانِ الرَّجِيمِ",
     "transliteration": "A'udhu billahis-sami'il-'alimi minash-shaytanir-rajim",
     "translation": "I seek refuge in Allah, the All-Hearing, the All-Knowing, from the accursed Satan.",
     "source": "Sunan Abu Dawud 5082 — Sahih", "type": "Morning Adhkar"},

    # ══════════════════════════════════════
    # EVENING ADHKAR
    # ══════════════════════════════════════
    {"arabic": "أَمْسَيْنَا وَأَمْسَى الْمُلْكُ لِلَّهِ وَالْحَمْدُ لِلَّهِ لَا إِلَٰهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ",
     "transliteration": "Amsayna wa amsal mulku lillah, walhamdu lillah, la ilaha illallahu wahdahu la sharika lah",
     "translation": "We have reached the evening and at this very time the whole dominion belongs to Allah. All praise is for Allah. None has the right to be worshipped except Allah, alone, without any partner.",
     "source": "Sahih Muslim 2723", "type": "Evening Adhkar"},

    {"arabic": "اللَّهُمَّ بِكَ أَمْسَيْنَا وَبِكَ أَصْبَحْنَا وَبِكَ نَحْيَا وَبِكَ نَمُوتُ وَإِلَيْكَ الْمَصِيرُ",
     "transliteration": "Allahumma bika amsayna wa bika asbahna wa bika nahya wa bika namutu wa ilaykal-masir",
     "translation": "O Allah, by You we enter the evening, by You we enter the morning, by You we live, by You we die, and to You is the return.",
     "source": "Sunan Abu Dawud 5068 — Sahih", "type": "Evening Adhkar"},

    {"arabic": "اللَّهُمَّ إِنِّي أَمْسَيْتُ أُشْهِدُكَ وَأُشْهِدُ حَمَلَةَ عَرْشِكَ وَمَلَائِكَتَكَ وَجَمِيعَ خَلْقِكَ أَنَّكَ أَنْتَ اللَّهُ لَا إِلَٰهَ إِلَّا أَنْتَ",
     "transliteration": "Allahumma inni amsaytu ushhiduka wa ushhidu hamalata 'arshika wa mala'ikataka wa jami'a khalqika annaka antallahu la ilaha illa ant",
     "translation": "O Allah, I have reached the evening calling You, the bearers of Your Throne, Your angels, and all of Your creation to witness that You are Allah; there is no deity except You.",
     "source": "Sunan Abu Dawud 5069 — Sahih", "type": "Evening Adhkar"},

    # ══════════════════════════════════════
    # PROPHETIC DUAS
    # ══════════════════════════════════════
    {"arabic": "اللَّهُمَّ إِنِّي أَعُوذُ بِكَ مِنَ الْهَمِّ وَالْحَزَنِ وَالْعَجْزِ وَالْكَسَلِ وَالْبُخْلِ وَالْجُبْنِ وَضَلَعِ الدَّيْنِ وَغَلَبَةِ الرِّجَالِ",
     "transliteration": "Allahumma inni a'udhu bika minal-hammi wal-hazan, wal-'ajzi wal-kasal, wal-bukhli wal-jubn, wa dhala'id-dayni wa ghalabatir-rijal",
     "translation": "O Allah, I seek refuge in You from worry, grief, incapacity, laziness, miserliness, cowardice, the burden of debt, and being overpowered by men.",
     "source": "Sahih Bukhari 6369", "type": "Prophetic Dua"},

    {"arabic": "اللَّهُمَّ اهْدِنِي وَسَدِّدْنِي",
     "transliteration": "Allahumma-hdini wa saddidni",
     "translation": "O Allah, guide me and make me steadfast.",
     "source": "Sahih Muslim 2725", "type": "Prophetic Dua"},

    {"arabic": "اللَّهُمَّ إِنِّي أَسْأَلُكَ الْعَافِيَةَ فِي الدُّنْيَا وَالْآخِرَةِ",
     "transliteration": "Allahumma inni as'alukal-'afiyata fid-dunya wal-akhirah",
     "translation": "O Allah, I ask You for well-being in this world and the Hereafter.",
     "source": "Sunan Ibn Majah 3871 — Sahih", "type": "Prophetic Dua"},

    {"arabic": "اللَّهُمَّ أَصْلِحْ لِي دِينِي الَّذِي هُوَ عِصْمَةُ أَمْرِي وَأَصْلِحْ لِي دُنْيَايَ الَّتِي فِيهَا مَعَاشِي",
     "transliteration": "Allahumma aslih li dini alladhi huwa 'ismatu amri, wa aslih li dunyaya allati fiha ma'ashi",
     "translation": "O Allah, set right my religion which is the safeguard of my affairs, and set right my worldly affairs wherein is my livelihood.",
     "source": "Sahih Muslim 2720", "type": "Prophetic Dua"},

    {"arabic": "اللَّهُمَّ إِنِّي أَسْأَلُكَ الْجَنَّةَ وَأَعُوذُ بِكَ مِنَ النَّارِ",
     "transliteration": "Allahumma inni as'alukal-jannata wa a'udhu bika minan-nar",
     "translation": "O Allah, I ask You for Paradise and I seek refuge in You from the Fire.",
     "source": "Sunan Abu Dawud 792 — Sahih", "type": "Prophetic Dua"},

    {"arabic": "اللَّهُمَّ اغْفِرْ لِي وَارْحَمْنِي وَاهْدِنِي وَعَافِنِي وَارْزُقْنِي",
     "transliteration": "Allahumma-ghfir li warhamni wahdinni wa 'afini warzuqni",
     "translation": "O Allah, forgive me, have mercy on me, guide me, grant me well-being, and provide for me.",
     "source": "Sahih Muslim 2697", "type": "Prophetic Dua"},

    {"arabic": "اللَّهُمَّ إِنِّي أَسْأَلُكَ عِلْمًا نَافِعًا وَرِزْقًا طَيِّبًا وَعَمَلًا مُتَقَبَّلًا",
     "transliteration": "Allahumma inni as'aluka 'ilman nafi'an wa rizqan tayyiban wa 'amalan mutaqabbala",
     "translation": "O Allah, I ask You for beneficial knowledge, pure provision, and accepted deeds.",
     "source": "Sunan Ibn Majah 925 — Sahih", "type": "Prophetic Dua"},

    {"arabic": "اللَّهُمَّ أَعِنِّي عَلَىٰ ذِكْرِكَ وَشُكْرِكَ وَحُسْنِ عِبَادَتِكَ",
     "transliteration": "Allahumma a'inni 'ala dhikrika wa shukrika wa husni 'ibadatik",
     "translation": "O Allah, help me to remember You, to thank You, and to worship You in the best manner.",
     "source": "Sunan Abu Dawud 1522 — Sahih", "type": "Prophetic Dua"},

    {"arabic": "اللَّهُمَّ إِنِّي أَسْأَلُكَ الثَّبَاتَ فِي الْأَمْرِ وَالْعَزِيمَةَ عَلَى الرُّشْدِ",
     "transliteration": "Allahumma inni as'alukas-thabata fil-amri wal-'azimata 'alar-rushd",
     "translation": "O Allah, I ask You for steadfastness in all matters and determination upon the right path.",
     "source": "Sunan al-Nasa'i 1305 — Sahih", "type": "Prophetic Dua"},

    {"arabic": "اللَّهُمَّ لَا سَهْلَ إِلَّا مَا جَعَلْتَهُ سَهْلًا وَأَنْتَ تَجْعَلُ الْحَزْنَ إِذَا شِئْتَ سَهْلًا",
     "transliteration": "Allahumma la sahla illa ma ja'altahu sahla, wa anta taj'alul hazna idha shi'ta sahla",
     "translation": "O Allah, nothing is easy except what You make easy, and You make the difficult easy if You wish.",
     "source": "Ibn Hibban 2427 — Sahih", "type": "Prophetic Dua"},

    {"arabic": "يَا حَيُّ يَا قَيُّومُ بِرَحْمَتِكَ أَسْتَغِيثُ أَصْلِحْ لِي شَأْنِي كُلَّهُ وَلَا تَكِلْنِي إِلَىٰ نَفْسِي طَرْفَةَ عَيْنٍ",
     "transliteration": "Ya Hayyu ya Qayyumu bi-rahmatika astaghithu, aslih li sha'ni kullahu wa la takilni ila nafsi tarfata 'ayn",
     "translation": "O Ever-Living, O Sustainer, by Your mercy I seek help. Rectify all of my affairs and do not leave me to myself for the blink of an eye.",
     "source": "Mustadrak al-Hakim — Sahih", "type": "Prophetic Dua"},

    {"arabic": "اللَّهُمَّ إِنِّي أَعُوذُ بِكَ مِنْ زَوَالِ نِعْمَتِكَ وَتَحَوُّلِ عَافِيَتِكَ وَفُجَاءَةِ نِقْمَتِكَ وَجَمِيعِ سَخَطِكَ",
     "transliteration": "Allahumma inni a'udhu bika min zawali ni'matika wa tahawwuli 'afiyatika wa fuja'ati niqmatika wa jami'i sakhatik",
     "translation": "O Allah, I seek refuge in You from the removal of Your blessing, the change of Your protection, the suddenness of Your punishment, and all forms of Your displeasure.",
     "source": "Sahih Muslim 2739", "type": "Prophetic Dua"},

    {"arabic": "اللَّهُمَّ إِنِّي أَسْأَلُكَ حُبَّكَ وَحُبَّ مَن يُحِبُّكَ وَحُبَّ عَمَلٍ يُقَرِّبُنِي إِلَىٰ حُبِّكَ",
     "transliteration": "Allahumma inni as'aluka hubbaka wa hubba man yuhibbuka wa hubba 'amalin yuqarribuni ila hubbik",
     "translation": "O Allah, I ask You for Your love, the love of those who love You, and the love of deeds that will bring me closer to Your love.",
     "source": "Sunan al-Tirmidhi 3490 — Sahih", "type": "Prophetic Dua"},

    {"arabic": "اللَّهُمَّ إِنِّي أَسْأَلُكَ الْهُدَى وَالتُّقَى وَالْعَفَافَ وَالْغِنَى",
     "transliteration": "Allahumma inni as'alukal-huda wat-tuqa wal-'afafa wal-ghina",
     "translation": "O Allah, I ask You for guidance, piety, chastity and self-sufficiency.",
     "source": "Sahih Muslim 2721", "type": "Prophetic Dua"},

    {"arabic": "اللَّهُمَّ آتِ نَفْسِي تَقْوَاهَا وَزَكِّهَا أَنتَ خَيْرُ مَن زَكَّاهَا أَنتَ وَلِيُّهَا وَمَوْلَاهَا",
     "transliteration": "Allahumma ati nafsi taqwaha wa zakkiha anta khayru man zakkaha anta waliyyuha wa mawlaha",
     "translation": "O Allah, grant my soul its piety and purify it, for You are the best to purify it. You are its Guardian and Master.",
     "source": "Sahih Muslim 2722", "type": "Prophetic Dua"},

    {"arabic": "اللَّهُمَّ مُصَرِّفَ الْقُلُوبِ صَرِّفْ قُلُوبَنَا عَلَىٰ طَاعَتِكَ",
     "transliteration": "Allahumma musarrifal-qulubi sarrif qulubana 'ala ta'atik",
     "translation": "O Allah, Turner of hearts, turn our hearts towards Your obedience.",
     "source": "Sahih Muslim 2654", "type": "Prophetic Dua"},

    {"arabic": "اللَّهُمَّ إِنِّي أَسْأَلُكَ مِنَ الْخَيْرِ كُلِّهِ عَاجِلِهِ وَآجِلِهِ مَا عَلِمْتُ مِنْهُ وَمَا لَمْ أَعْلَمْ",
     "transliteration": "Allahumma inni as'aluka minal-khayri kullihi 'ajilihi wa ajilihi ma 'alimtu minhu wa ma lam a'lam",
     "translation": "O Allah, I ask You for all good, in this world and the next, what I know of it and what I do not know.",
     "source": "Sunan Ibn Majah 3846 — Sahih", "type": "Prophetic Dua"},

    # ══════════════════════════════════════
    # ISTIGHFAR
    # ══════════════════════════════════════
    {"arabic": "رَبِّ اغْفِرْ لِي وَتُبْ عَلَيَّ إِنَّكَ أَنْتَ التَّوَّابُ الْغَفُورُ",
     "transliteration": "Rabbi-ghfir li wa tub 'alayya innaka anta-t-Tawwabul Ghafur",
     "translation": "My Lord, forgive me and accept my repentance. Verily You are the Ever-Returning, the Oft-Forgiving.",
     "source": "Sahih Bukhari 834", "type": "Istighfar"},

    {"arabic": "أَسْتَغْفِرُ اللَّهَ الْعَظِيمَ الَّذِي لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ وَأَتُوبُ إِلَيْهِ",
     "transliteration": "Astaghfirullahil-'Azim alladhi la ilaha illa huwal-Hayyul-Qayyum wa atubu ilaih",
     "translation": "I seek forgiveness from Allah the Magnificent, besides Whom none has the right to be worshipped, the Ever-Living, the Sustainer, and I repent to Him.",
     "source": "Sunan Abu Dawud 1517 — Sahih", "type": "Istighfar"},

    {"arabic": "سُبْحَانَكَ اللَّهُمَّ وَبِحَمْدِكَ أَشْهَدُ أَن لَّا إِلَٰهَ إِلَّا أَنتَ أَسْتَغْفِرُكَ وَأَتُوبُ إِلَيْكَ",
     "transliteration": "Subhanakal-lahumma wa bihamdika, ashhadu an la ilaha illa anta, astaghfiruka wa atubu ilayk",
     "translation": "Glory be to You O Allah, and with Your praise, I testify that there is none worthy of worship except You. I seek Your forgiveness and I repent to You.",
     "source": "Sunan al-Tirmidhi 3433 — Sahih", "type": "Istighfar"},

    # ══════════════════════════════════════
    # TASBIH & DHIKR
    # ══════════════════════════════════════
    {"arabic": "سُبْحَانَ اللَّهِ وَبِحَمْدِهِ سُبْحَانَ اللَّهِ الْعَظِيمِ",
     "transliteration": "SubhanAllahi wa bihamdihi, SubhanAllahil-'Adhim",
     "translation": "Glory be to Allah and His is the praise. Glory be to Allah the Magnificent.",
     "source": "Sahih Bukhari 6682", "type": "Tasbih"},

    {"arabic": "سُبْحَانَ اللَّهِ وَالْحَمْدُ لِلَّهِ وَلَا إِلَٰهَ إِلَّا اللَّهُ وَاللَّهُ أَكْبَرُ",
     "transliteration": "SubhanAllah, walhamdulillah, wa la ilaha illallah, wallahu Akbar",
     "translation": "Glory be to Allah, all praise is for Allah, none has the right to be worshipped except Allah, and Allah is the Greatest.",
     "source": "Sahih Muslim 2695", "type": "Tasbih"},

    {"arabic": "لَا إِلَٰهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ لَهُ الْمُلْكُ وَلَهُ الْحَمْدُ وَهُوَ عَلَىٰ كُلِّ شَيْءٍ قَدِيرٌ",
     "transliteration": "La ilaha illallahu wahdahu la sharika lahu, lahul-mulku wa lahul-hamdu wa huwa 'ala kulli shay'in qadir",
     "translation": "None has the right to be worshipped except Allah, alone, without any partner. To Him belongs all dominion and all praise, and He is over all things capable.",
     "source": "Sahih Bukhari 6403", "type": "Tasbih"},

    {"arabic": "سُبْحَانَ اللَّهِ وَبِحَمْدِهِ عَدَدَ خَلْقِهِ وَرِضَا نَفْسِهِ وَزِنَةَ عَرْشِهِ وَمِدَادَ كَلِمَاتِهِ",
     "transliteration": "SubhanAllahi wa bihamdihi 'adada khalqihi wa rida nafsihi wa zinata 'arshihi wa midada kalimatihi",
     "translation": "Glory be to Allah and His is the praise, to the number of His creation, His pleasure, the weight of His throne and the ink of His words.",
     "source": "Sahih Muslim 2726", "type": "Tasbih"},

    {"arabic": "لَا حَوْلَ وَلَا قُوَّةَ إِلَّا بِاللَّهِ",
     "transliteration": "La hawla wa la quwwata illa billah",
     "translation": "There is no might nor power except with Allah.",
     "source": "Sahih Bukhari 6384", "type": "Tasbih"},

    {"arabic": "اللَّهُ أَكْبَرُ كَبِيرًا وَالْحَمْدُ لِلَّهِ كَثِيرًا وَسُبْحَانَ اللَّهِ بُكْرَةً وَأَصِيلًا",
     "transliteration": "Allahu Akbaru kabiran walhamdulillahi kathiran wa subhanAllahi bukratan wa asila",
     "translation": "Allah is the Greatest, greatly. All praise is for Allah, abundantly. Glory be to Allah morning and evening.",
     "source": "Sahih Muslim 601", "type": "Tasbih"},

    # ══════════════════════════════════════
    # PROTECTION DUAS
    # ══════════════════════════════════════
    {"arabic": "بِسْمِ اللَّهِ الَّذِي لَا يَضُرُّ مَعَ اسْمِهِ شَيْءٌ فِي الْأَرْضِ وَلَا فِي السَّمَاءِ وَهُوَ السَّمِيعُ الْعَلِيمُ",
     "transliteration": "Bismillahil-ladhi la yadurru ma'asmihi shay'un fil-ardi wa la fis-sama'i wa huwas-sami'ul-'alim",
     "translation": "In the Name of Allah, with Whose Name nothing can cause harm on earth or in the heavens, and He is the All-Hearing, the All-Knowing.",
     "source": "Sunan Abu Dawud 5088 — Sahih", "type": "Dua for Protection"},

    {"arabic": "أَعُوذُ بِكَلِمَاتِ اللَّهِ التَّامَّاتِ مِنْ شَرِّ مَا خَلَقَ",
     "transliteration": "A'udhu bi kalimatillahit-tammati min sharri ma khalaq",
     "translation": "I seek refuge in the perfect words of Allah from the evil of what He has created.",
     "source": "Sahih Muslim 2708", "type": "Dua for Protection"},

    {"arabic": "اللَّهُمَّ احْفَظْنِي مِنْ بَيْنِ يَدَيَّ وَمِنْ خَلْفِي وَعَنْ يَمِينِي وَعَنْ شِمَالِي وَمِنْ فَوْقِي وَأَعُوذُ بِعَظَمَتِكَ أَن أُغْتَالَ مِنْ تَحْتِي",
     "transliteration": "Allahumma-hfazni min bayni yadayya wa min khalfi wa 'an yamini wa 'an shimali wa min fawqi, wa a'udhu bi'azamatika an ughtala min tahti",
     "translation": "O Allah, protect me from in front, from behind, from my right, from my left, and from above me. I seek refuge in Your greatness from being swallowed from beneath me.",
     "source": "Sunan Abu Dawud 5074 — Sahih", "type": "Dua for Protection"},

    # ══════════════════════════════════════
    # SALAH DUAS
    # ══════════════════════════════════════
    {"arabic": "اللَّهُمَّ إِنِّي ظَلَمْتُ نَفْسِي ظُلْمًا كَثِيرًا وَلَا يَغْفِرُ الذُّنُوبَ إِلَّا أَنْتَ فَاغْفِرْ لِي مَغْفِرَةً مِّنْ عِنْدِكَ وَارْحَمْنِي إِنَّكَ أَنتَ الْغَفُورُ الرَّحِيمُ",
     "transliteration": "Allahumma inni zalamtu nafsi zulman kathiran wa la yaghfirudh-dhunuba illa anta faghfir li maghfiratan min 'indika warhamni innaka antal-Ghafurur-Rahim",
     "translation": "O Allah, I have greatly wronged myself and no one forgives sins but You. So grant me forgiveness and have mercy on me. Surely, You are the Forgiving, the Merciful.",
     "source": "Sahih Bukhari 834", "type": "Salah Dua"},

    {"arabic": "سُبْحَانَكَ اللَّهُمَّ وَبِحَمْدِكَ وَتَبَارَكَ اسْمُكَ وَتَعَالَىٰ جَدُّكَ وَلَا إِلَٰهَ غَيْرُكَ",
     "transliteration": "Subhanakal-lahumma wa bihamdika wa tabarakasmuka wa ta'ala jadduka wa la ilaha ghayruk",
     "translation": "How perfect You are O Allah, and I praise You. Blessed is Your name and exalted is Your majesty. There is no deity worthy of worship except You.",
     "source": "Sunan Abu Dawud 775 — Sahih", "type": "Salah Dua"},
]

# ══════════════════════════════════════
# CAPTION TEMPLATES
# ══════════════════════════════════════
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

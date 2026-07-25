"""
Download GRETIL corpustei plain-text (IAST) source files into data/raw/gretil/.

These are romanized (IAST); transliteration to Devanagari + cleaning happens in
build_corpus.py. GRETIL corpustei files are CC BY-NC-SA 4.0 (NonCommercial) —
recorded in sources.json. Corpus (Sanskrit-only) use; no aligned English.

Curated toward classical *verse* register (Puranas, principal Upanishads, Kavya).
"""
import os
import time
import requests

RAW = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "gretil")
BASE = "https://gretil.sub.uni-goettingen.de/gretil/corpustei/transformations/html/"

# (filename, source_id, display_name, sanskrit_name, category)
SOURCES = [
    # --- Mahapuranas ---
    ("sa_agnipurANa.htm", "AgniP", "Agni Purana", "अग्निपुराण", "Purana"),
    ("sa_bhAgavatapurANa.htm", "BhagP", "Bhagavata Purana", "भागवतपुराण", "Purana"),
    ("sa_brahmapurANa-1-246.htm", "BrahmaP", "Brahma Purana", "ब्रह्मपुराण", "Purana"),
    ("sa_brahmANDapurANa.htm", "BrahmandaP", "Brahmanda Purana", "ब्रह्माण्डपुराण", "Purana"),
    ("sa_garuDapurANa.htm", "GarudaP", "Garuda Purana", "गरुडपुराण", "Purana"),
    ("sa_kUrmapurANa.htm", "KurmaP", "Kurma Purana", "कूर्मपुराण", "Purana"),
    ("sa_liGgapurANa1-108.htm", "LingaP1", "Linga Purana (1-108)", "लिङ्गपुराण", "Purana"),
    ("sa_mArkaNDeyapurANa1-93.htm", "MarkP", "Markandeya Purana (1-93)", "मार्कण्डेयपुराण", "Purana"),
    ("sa_matsyapurANa1-176.htm", "MatsyaP", "Matsya Purana (1-176)", "मत्स्यपुराण", "Purana"),
    ("sa_nAradapurANa.htm", "NaradaP", "Narada Purana", "नारदपुराण", "Purana"),
    ("sa_narasiMhapurANa.htm", "NarasimhaP", "Narasimha Purana", "नरसिंहपुराण", "Purana"),
    ("sa_skandapurANa-revAkhaNDa-rks.htm", "SkandaP", "Skanda Purana (Reva Khanda)", "स्कन्दपुराण", "Purana"),
    ("sa_vAmanapurANa1-69.htm", "VamanaP", "Vamana Purana (1-69)", "वामनपुराण", "Purana"),
    ("sa_viSNupurANa-crit.htm", "VishnuP", "Vishnu Purana (crit. ed.)", "विष्णुपुराण", "Purana"),
    ("sa_zivapurANabooks-1-and-7.htm", "ShivaP", "Shiva Purana (books 1 & 7)", "शिवपुराण", "Purana"),
    # --- Principal Upanishads (verse + Shankara commentary where only form available) ---
    ("sa_IzopaniSad-or-IzAvAsyopaniSadkANva-recension-comm.htm", "IsaU", "Isha Upanishad", "ईशोपनिषद्", "Upanishad"),
    ("sa_kathopaniSad.htm", "KathaU", "Katha Upanishad", "कठोपनिषद्", "Upanishad"),
    ("sa_kaivalyopaniSad.htm", "KaivalyaU", "Kaivalya Upanishad", "कैवल्योपनिषद्", "Upanishad"),
    ("sa_praznopaniSad-comm.htm", "PrasnaU", "Prashna Upanishad", "प्रश्नोपनिषद्", "Upanishad"),
    ("sa_zvetAzvataropaniSad.htm", "SvetU", "Shvetashvatara Upanishad", "श्वेताश्वतरोपनिषद्", "Upanishad"),
    ("sa_mANDUkyopaniSad-alt.htm", "MandU", "Mandukya Upanishad", "माण्डूक्योपनिषद्", "Upanishad"),
    # --- Kavya (classical verse) ---
    ("sa_kAlidAsa-raghuvaMza.htm", "Raghu", "Raghuvamsha (Kalidasa)", "रघुवंश", "Kavya"),
    ("sa_kAlidAsa-kumArasaMbhava.htm", "Kumara", "Kumarasambhava (Kalidasa)", "कुमारसम्भव", "Kavya"),
    ("sa_kAlidAsa-meghadUta.htm", "Megha", "Meghaduta (Kalidasa)", "मेघदूत", "Kavya"),
    ("sa_bhAravi-kirAtArjunIya.htm", "Kirata", "Kiratarjuniya (Bharavi)", "किरातार्जुनीय", "Kavya"),
    ("sa_mAgha-zizupAlavadha.htm", "Shishu", "Shishupalavadha (Magha)", "शिशुपालवध", "Kavya"),
    # --- Epics (full texts, corpustei) ---
    ("sa_rAmAyaNa.htm", "RamayanaFull", "Valmiki Ramayana (full)", "वाल्मीकिरामायण", "Epic"),
    ("sa_harivaMza.htm", "Harivamsha", "Harivamsha", "हरिवंश", "Epic"),
    ("sa_kSemendra-bhAratamaJjarI-6-19.htm", "BharataM", "Bharatamanjari (Kshemendra)", "भारतमञ्जरी", "Kavya"),
    # --- Dharmashastra (smritis — classical verse) ---
    ("sa_manusmRti.htm", "Manu", "Manusmriti", "मनुस्मृति", "Dharmashastra"),
    ("sa_yAjJavalkyasmRti.htm", "Yajnavalkya", "Yajnavalkya Smriti", "याज्ञवल्क्यस्मृति", "Dharmashastra"),
    ("sa_nAradasmRti.htm", "NaradaSm", "Narada Smriti", "नारदस्मृति", "Dharmashastra"),
    ("sa_viSNusmRti.htm", "VishnuSm", "Vishnu Smriti", "विष्णुस्मृति", "Dharmashastra"),
    ("sa_kAtyAyanasmRti.htm", "Katyayana", "Katyayana Smriti", "कात्यायनस्मृति", "Dharmashastra"),
    ("sa_parAzarasmRti-AcAra-prAyazcitta.htm", "Parashara", "Parashara Smriti", "पराशरस्मृति", "Dharmashastra"),
    ("sa_yamasmRti-182v.htm", "Yama", "Yama Smriti", "यमस्मृति", "Dharmashastra"),
    ("sa_AGgirasasmRti.htm", "Angirasa", "Angirasa Smriti", "आङ्गिरसस्मृति", "Dharmashastra"),
    ("sa_bRhaspatismRti-vyavahArakANDa.htm", "Brihaspati", "Brihaspati Smriti", "बृहस्पतिस्मृति", "Dharmashastra"),
    # --- Additional Puranas (distinct texts; non-crit Vishnu vulgate deliberately
    #     omitted — it duplicates the critical-edition Vishnu Purana already used) ---
    ("sa_revAkhANDa-of-the-vAyupurANa-rkv.htm", "VayuP", "Vayu Purana (Reva Khanda)", "वायुपुराण", "Purana"),
    ("sa_svayaMbhupurANa.htm", "SvayambhuP", "Svayambhu Purana", "स्वयम्भूपुराण", "Purana"),
    ("sa_vAmanapurANasaromAhAtmya.htm", "VamanaSaro", "Vamana Purana (Saromahatmya)", "वामनपुराण", "Purana"),
    # --- Vedas (samhitas; Vedic register, pitch accents stripped in cleaning) ---
    ("sa_Rgveda-edAufrecht.htm", "Rigveda", "Rigveda Samhita (Aufrecht)", "ऋग्वेद", "Veda"),
    ("sa_sAmavedasaMhitA.htm", "Samaveda", "Samaveda Samhita", "सामवेद", "Veda"),
    ("sa_RgvedakhilAni.htm", "RigvedaKh", "Rigveda Khilani", "ऋग्वेदखिलानि", "Veda"),
    # --- Additional Kavya (classical poetry) ---
    ("sa_bhaTTi-rAvaNavadha.htm", "Bhatti", "Bhattikavya (Ravanavadha)", "भट्टिकाव्य", "Kavya"),
    ("sa_bhatRhari-zatakatraya.htm", "Bhartrhari", "Bhartrhari Shatakatraya", "शतकत्रय", "Kavya"),
    ("sa_jayadeva-gItagovinda.htm", "GitaGov", "Gita Govinda (Jayadeva)", "गीतगोविन्द", "Kavya"),
    ("sa_amaru-amaruzataka.htm", "Amaru", "Amaru Shataka", "अमरुशतक", "Kavya"),
    ("sa_bhallaTa-bhallaTazataka.htm", "Bhallata", "Bhallata Shataka", "भल्लटशतक", "Kavya"),
    ("sa_appayadIkSita-vairAgyazatakam.htm", "Vairagya", "Vairagya Shataka", "वैराग्यशतक", "Kavya"),
    ("sa_daNDin-kAvyAdarza-1-2.htm", "Kavyadarsha12", "Kavyadarsha 1-2 (Dandin)", "काव्यादर्श", "Kavya"),
    ("sa_daNDin-kAvyAdarza-3.htm", "Kavyadarsha3", "Kavyadarsha 3 (Dandin)", "काव्यादर्श", "Kavya"),
    ("sa_somadeva-kathAsaritsAgara.htm", "Katha", "Kathasaritsagara (Somadeva)", "कथासरित्सागर", "Kavya"),
    ("sa_jonarAja-and-pseudo-jonarAja-rAjataraGginI.htm", "Rajat", "Rajatarangini (Jonaraja)", "राजतरङ्गिणी", "Kavya"),
    # --- Subhashita (gnomic verse anthologies; high verse density, classical) ---
    ("sa_mahAsubhASitasaMgraha-1-9979.htm", "MahaSubh", "Maha-subhashita-sangraha", "महासुभाषितसंग्रह", "Subhashita"),
    ("sa_vidyAkara-subhASitaratnakoza.htm", "SubhRatna", "Subhashitaratnakosha (Vidyakara)", "सुभाषितरत्नकोश", "Subhashita"),
    ("sa_vallabhadeva-subhASitAvali-1-1040.htm", "SubhAvali", "Subhashitavali (Vallabhadeva)", "सुभाषितावलि", "Subhashita"),
]

# Full Mahabharata — GRETIL legacy 2_epic files (18 books). Different format
# (reference<TAB>verse) and a different base URL, so handled separately.
MBH_BASE = "https://gretil.sub.uni-goettingen.de/gretil/1_sanskr/2_epic/mbh/"
MBH_FILES = [f"mbh_{i:02d}_u.htm" for i in range(1, 19)]


def main(force=False):
    os.makedirs(RAW, exist_ok=True)
    for fn, sid, name, _skt, _cat in SOURCES:
        dest = os.path.join(RAW, fn)
        if os.path.exists(dest) and not force:
            print(f"skip  {name} (exists)")
            continue
        try:
            r = requests.get(BASE + fn, timeout=180)
            r.raise_for_status()
            r.encoding = "utf-8"
            with open(dest, "w", encoding="utf-8", newline="\n") as f:
                f.write(r.text)
            print(f"saved {name:38s} ({len(r.text):>9,} chars)")
        except Exception as e:
            print(f"FAIL  {name}: {e}")
        time.sleep(0.5)  # be polite to GRETIL

    # Full Mahabharata (18 legacy books)
    for fn in MBH_FILES:
        dest = os.path.join(RAW, fn)
        if os.path.exists(dest) and not force:
            print(f"skip  {fn} (exists)")
            continue
        try:
            r = requests.get(MBH_BASE + fn, timeout=180)
            r.raise_for_status()
            r.encoding = "utf-8"
            with open(dest, "w", encoding="utf-8", newline="\n") as f:
                f.write(r.text)
            print(f"saved {fn:38s} ({len(r.text):>9,} chars)")
        except Exception as e:
            print(f"FAIL  {fn}: {e}")
        time.sleep(0.5)


if __name__ == "__main__":
    import sys
    main(force="--force" in sys.argv)

"""
Build data/rag/sources.json — one metadata entry per text (corpus + RAG),
including the license of each source so provenance is never lost. GRETIL
counts are recomputed from the raw files for honesty.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from gretil_extract import extract_devanagari_verses, extract_legacy_epic_verses
from fetch_gretil import SOURCES as GRETIL_SOURCES, MBH_FILES

ROOT = os.path.join(os.path.dirname(__file__), "..")
RAW = os.path.join(ROOT, "data", "raw")
RAG_DIR = os.path.join(ROOT, "data", "rag")

BG_TRANSLATORS = [
    "Swami Sivananda", "Shri Purohit Swami", "Dr. S. Sankaranarayan",
    "Swami Adidevananda", "Swami Gambirananda", "Sri Ramanuja",
    "Sri Abhinav Gupta", "Sri Shankaracharya", "A.C. Bhaktivedanta Swami Prabhupada",
]

GRETIL_LICENSE = "CC BY-NC-SA 4.0 (NonCommercial) — GRETIL corpus"


def main():
    sources = []

    sources.append({
        "id": "BG", "name": "Bhagavad Gita", "sanskrit_name": "श्रीमद्भगवद्गीता",
        "category": "Itihasa", "verse_count": 719, "has_translation": True,
        "translators": BG_TRANSLATORS,
        "origin_url": "https://github.com/vedicscriptures/bhagavad-gita",
        "license": "GPL-3.0",
    })

    # Itihasa RAG record count (aligned pairs actually kept)
    itihasa_n = 0
    for split in ("train", "dev", "test"):
        sn = os.path.join(RAW, "itihasa", f"{split}.sn")
        en = os.path.join(RAW, "itihasa", f"{split}.en")
        if os.path.exists(sn) and os.path.exists(en):
            with open(sn, encoding="utf-8") as fs, open(en, encoding="utf-8") as fe:
                itihasa_n += sum(1 for s, e in zip(fs, fe) if s.strip() and e.strip())
    sources.append({
        "id": "ITIH", "name": "Itihasa (Ramayana + Mahabharata)",
        "sanskrit_name": "रामायण-महाभारत", "category": "Itihasa",
        "verse_count": itihasa_n, "has_translation": True,
        "translators": ["M. N. Dutt (public domain)"],
        "origin_url": "https://github.com/rahular/itihasa",
        "license": "Apache-2.0 (English from M. N. Dutt, public domain)",
    })

    for fn, sid, name, skt, cat in GRETIL_SOURCES:
        path = os.path.join(RAW, "gretil", fn)
        if not os.path.exists(path):
            continue
        n = len(extract_devanagari_verses(open(path, encoding="utf-8").read()))
        sources.append({
            "id": sid, "name": name, "sanskrit_name": skt, "category": cat,
            "verse_count": n, "has_translation": False, "translators": [],
            "origin_url": f"https://gretil.sub.uni-goettingen.de/gretil/corpustei/transformations/html/{fn}",
            "license": GRETIL_LICENSE,
        })
        print(f"  {name:36s} {n:>7,}")

    # Full Mahabharata — 18 legacy books (aggregate entry)
    mbh_n = 0
    for fn in MBH_FILES:
        p = os.path.join(RAW, "gretil", fn)
        if os.path.exists(p):
            mbh_n += len(extract_legacy_epic_verses(open(p, encoding="utf-8").read()))
    if mbh_n:
        sources.append({
            "id": "MBH", "name": "Mahabharata (full, Pune crit. ed.)",
            "sanskrit_name": "महाभारत", "category": "Epic",
            "verse_count": mbh_n, "has_translation": False, "translators": [],
            "origin_url": "https://gretil.sub.uni-goettingen.de/gretil/1_sanskr/2_epic/mbh/",
            "license": GRETIL_LICENSE,
        })
        print(f"  {'Mahabharata (full)':36s} {mbh_n:>7,}")

    out = os.path.join(RAG_DIR, "sources.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(sources, f, ensure_ascii=False, indent=2)
    print(f"\nwrote {len(sources)} source entries -> {out}")


if __name__ == "__main__":
    main()

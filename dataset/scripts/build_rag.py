"""
Build data/rag/verses.jsonl — the comprehensive, source-tagged verse index for
retrieval. ONE record per verse, covering EVERY corpus text so any source can be
retrieved faithfully (e.g. "give me Garuda Purana shlokas"):

  - Bhagavad Gita        — Sanskrit + 9 English translators + commentary
  - Itihasa              — Ramayana/Mahabharata verses + M. N. Dutt English
  - all GRETIL sources   — Puranas, Kavya, Vedas, Dharmashastra, Subhashita,
                           Upanishads, full Ramayana/Harivamsha (Sanskrit only)
  - full Mahabharata     — 18 legacy books (Sanskrit only)

Records without a public-domain aligned translation carry translations={} and
translation_source="none" (they are still retrievable by Sanskrit + source).
Output is JSONL (one JSON object per line) — the standard format for a retrieval
corpus: streamable and easy to embed line-by-line.
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common import clean_for_rag, clean_devanagari_block, is_valid_verse, resegment_long
from gretil_extract import extract_devanagari_verses, extract_legacy_epic_verses
from fetch_gretil import SOURCES as GRETIL_SOURCES, MBH_FILES

ROOT = os.path.join(os.path.dirname(__file__), "..")
RAW = os.path.join(ROOT, "data", "raw")
RAG_DIR = os.path.join(ROOT, "data", "rag")

REQUIRED_FIELDS = ["id", "source", "source_sanskrit", "category", "book", "chapter",
                   "verse", "speaker", "sanskrit", "transliteration", "translations",
                   "commentary", "keywords", "translation_source"]


def _rec(id, source, skt_name, category, sanskrit, *, book=None, chapter=None,
         verse=None, speaker="", translit="", translations=None, commentary="",
         translation_source="none"):
    return {
        "id": id, "source": source, "source_sanskrit": skt_name, "category": category,
        "book": book, "chapter": chapter, "verse": verse, "speaker": speaker,
        "sanskrit": sanskrit, "transliteration": translit,
        "translations": translations or {}, "commentary": commentary,
        "keywords": [], "translation_source": translation_source,
    }


def _bg_records():
    out = []
    for path in sorted(glob.glob(os.path.join(RAW, "bhagavad-gita", "*.json"))):
        try:
            rec = json.load(open(path, encoding="utf-8"))
        except Exception:
            continue
        translations, commentary = {}, ""
        for v in rec.values():
            if isinstance(v, dict) and v.get("et"):
                translations[v.get("author", "").strip() or "Unknown"] = v["et"].strip()
                if not commentary and v.get("ec"):
                    commentary = v["ec"].strip()
        if not translations:
            continue
        out.append(_rec(
            rec.get("_id") or f"BG{rec['chapter']}.{rec['verse']}",
            "Bhagavad Gita", "श्रीमद्भगवद्गीता", "Gita",
            clean_for_rag(rec.get("slok", "")),
            chapter=rec.get("chapter"), verse=rec.get("verse"),
            speaker=rec.get("speaker", ""), translit=rec.get("transliteration", "").strip(),
            translations=translations, commentary=commentary, translation_source="human"))
    return out


def _itihasa_records():
    out, n = [], 0
    for split in ("train", "dev", "test"):
        sn = os.path.join(RAW, "itihasa", f"{split}.sn")
        en = os.path.join(RAW, "itihasa", f"{split}.en")
        if not (os.path.exists(sn) and os.path.exists(en)):
            continue
        with open(sn, encoding="utf-8") as fs, open(en, encoding="utf-8") as fe:
            for s_line, e_line in zip(fs, fe):
                s, e = clean_for_rag(s_line), e_line.strip()
                if not s or not e:
                    continue
                n += 1
                out.append(_rec(f"ITIH{n}", "Itihasa (Ramayana + Mahabharata)",
                                "रामायण-महाभारत", "Epic", s, verse=n,
                                translations={"M. N. Dutt": e}, translation_source="human"))
    return out


def _tagged_verses(verses, sid, source, skt_name, category, book=None):
    """Turn a list of extracted Devanagari verses into source-tagged records,
    de-duplicated within the source (whitespace-insensitive)."""
    out, seen, n = [], set(), 0
    for v in verses:
        for sub in resegment_long(v):
            if not is_valid_verse(sub):
                continue
            key = "".join(sub.split())
            if key in seen:
                continue
            seen.add(key)
            n += 1
            rid = f"{sid}-{book}-{n}" if book else f"{sid}-{n}"
            out.append(_rec(rid, source, skt_name, category, sub, book=book, verse=n))
    return out


def _gretil_records():
    out = []
    for fn, sid, name, skt, cat in GRETIL_SOURCES:
        path = os.path.join(RAW, "gretil", fn)
        if not os.path.exists(path):
            continue
        verses = extract_devanagari_verses(open(path, encoding="utf-8").read())
        recs = _tagged_verses(verses, sid, name, skt, cat)
        out.extend(recs)
        print(f"  {name:38s} {len(recs):>7,}")
    return out


def _mbh_records():
    out = []
    for fn in MBH_FILES:
        path = os.path.join(RAW, "gretil", fn)
        if not os.path.exists(path):
            continue
        book = fn.replace("mbh_", "").replace("_u.htm", "")
        verses = extract_legacy_epic_verses(open(path, encoding="utf-8").read())
        recs = _tagged_verses(verses, "MBH", "Mahabharata (full, Pune crit. ed.)",
                              "महाभारत", "Epic", book=book)
        out.extend(recs)
    print(f"  {'Mahabharata (full, 18 books)':38s} {len(out):>7,}")
    return out


def build():
    os.makedirs(RAG_DIR, exist_ok=True)
    print("=== building comprehensive RAG index ===")
    records = []
    records += _bg_records()
    records += _itihasa_records()
    records += _gretil_records()
    records += _mbh_records()

    # schema + uniqueness guard
    ids = set()
    for r in records:
        missing = [f for f in REQUIRED_FIELDS if f not in r]
        assert not missing, f"{r.get('id')} missing {missing}"
        assert r["id"] not in ids, f"duplicate id {r['id']}"
        ids.add(r["id"])

    out = os.path.join(RAG_DIR, "verses.jsonl")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # drop the superseded array file if present
    old = os.path.join(RAG_DIR, "verses.json")
    if os.path.exists(old):
        os.remove(old)

    translated = sum(1 for r in records if r["translations"])
    by_cat = {}
    for r in records:
        by_cat[r["category"]] = by_cat.get(r["category"], 0) + 1
    print("\n=== RAG index summary ===")
    for c, n in sorted(by_cat.items(), key=lambda x: -x[1]):
        print(f"  {c:14s} {n:>8,} records")
    print(f"  TOTAL {len(records):,} records | {translated:,} with translation "
          f"({100*translated/len(records):.0f}%)")
    print(f"  size: {os.path.getsize(out)/1e6:.1f} MB -> {out}")


if __name__ == "__main__":
    build()

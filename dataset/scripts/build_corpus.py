"""
Build data/corpus/shlok_corpus.txt (+ train/val split) from data/raw/.

Pipeline per source -> clean Devanagari verse blocks -> global exact-dedup ->
min-length filter -> write corpus. Train/val split is done by *chunk* (chapter or
contiguous block), never per-verse, so neighbouring verses can't leak across the
split. One verse per block, blank line between verses (DATA_REQUIREMENTS Part 1).
"""
import glob
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common import clean_devanagari_block, is_valid_verse, resegment_long
from gretil_extract import extract_devanagari_verses, extract_legacy_epic_verses
from fetch_gretil import SOURCES as GRETIL_SOURCES, MBH_FILES

ROOT = os.path.join(os.path.dirname(__file__), "..")
RAW = os.path.join(ROOT, "data", "raw")
CORPUS_DIR = os.path.join(ROOT, "data", "corpus")

VAL_EVERY = 20          # ~5% of chunks held out for validation
MIN_CHARS = 10
CHUNK_SIZE = 250        # verses per chunk for sources without chapter metadata


def _iter_bg():
    """Bhagavad Gita: one cleaned verse per slok JSON, chunked by chapter."""
    for path in sorted(glob.glob(os.path.join(RAW, "bhagavad-gita", "*.json"))):
        try:
            rec = json.load(open(path, encoding="utf-8"))
        except Exception:
            continue
        slok = rec.get("slok", "")
        block = clean_devanagari_block(slok)
        if block:
            yield f"BG-ch{rec.get('chapter','?')}", block


def _iter_itihasa():
    """Itihasa .sn files: one verse per line, chunked in contiguous blocks."""
    for split in ("train", "dev", "test"):
        p = os.path.join(RAW, "itihasa", f"{split}.sn")
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf-8") as f:
            for i, line in enumerate(f):
                block = clean_devanagari_block(line)
                if block:
                    yield f"ITIH-{split}-{i // CHUNK_SIZE}", block


def _iter_gretil():
    """GRETIL: EVERY corpustei sa_*.htm (IAST) -> Devanagari verses. Processes the
    full catalog (not just the curated SOURCES list) to scale the corpus."""
    import glob
    paths = sorted(glob.glob(os.path.join(RAW, "gretil", "sa_*.htm")))
    for path in paths:
        sid = os.path.basename(path)[:-4]      # filename w/o .htm
        try:
            verses = extract_devanagari_verses(open(path, encoding="utf-8").read())
        except Exception:
            continue
        for i, block in enumerate(verses):
            yield f"{sid}-{i // CHUNK_SIZE}", block
        if verses:
            print(f"  {sid[:44]:44s} {len(verses):>7,}")


def _iter_mbh():
    """Full Mahabharata: GRETIL legacy tab-delimited books -> Devanagari verses."""
    for fn in MBH_FILES:
        path = os.path.join(RAW, "gretil", fn)
        if not os.path.exists(path):
            continue
        raw = open(path, encoding="utf-8").read()
        verses = extract_legacy_epic_verses(raw)
        book = fn.replace("mbh_", "").replace("_u.htm", "")
        for i, block in enumerate(verses):
            yield f"MBH-{book}-{i // CHUNK_SIZE}", block
        print(f"  mbh book {book:3s} {len(verses):>7,} verses")


def _iter_dcs():
    """Digital Corpus of Sanskrit: '# text' IAST lines from .conllu -> Devanagari."""
    import glob
    from common import iast_to_devanagari
    files = sorted(glob.glob(os.path.join(RAW, "dcs", "**", "*.conllu"), recursive=True))
    n = 0
    for k, path in enumerate(files):
        try:
            fh = open(path, encoding="utf-8")
        except Exception:
            continue
        for line in fh:
            if line.startswith("# text = "):
                iast = line[9:].strip()
                if not iast:
                    continue
                try:
                    block = clean_devanagari_block(iast_to_devanagari(iast))
                except Exception:
                    continue
                if block:
                    n += 1
                    yield f"DCS-{k // 200}", block
        fh.close()
    print(f"  DCS {len(files):,} files -> {n:,} raw sentences")


def _iter_hf_mono():
    """HuggingFace chronbmm sanskrit-monolingual-pretraining parquet shards (IAST)."""
    import glob
    import pyarrow.parquet as pq
    from common import iast_to_devanagari
    for path in sorted(glob.glob(os.path.join(RAW, "hf_mono", "*.parquet"))):
        rows = pq.read_table(path, columns=["text"]).column("text").to_pylist()
        n = 0
        for iast in rows:
            if not iast or not iast.strip():
                continue
            try:
                block = clean_devanagari_block(iast_to_devanagari(iast))
            except Exception:
                continue
            if block:
                n += 1
                yield f"HFM-{n // CHUNK_SIZE}", block
        print(f"  hf_mono {os.path.basename(path)} -> {n:,}")


def build():
    os.makedirs(CORPUS_DIR, exist_ok=True)
    seen = set()         # normalized keys (whitespace-insensitive) for dedup
    kept = []            # (chunk_key, text)
    stats = {}
    dup = 0
    short = 0

    # NOTE: Itihasa (Ramayana + Mahabharata, Dutt edition) is intentionally NOT in
    # the corpus — it is a redundant subset of the full GRETIL Ramayana + Mahabharata
    # (different critical editions of the same works). Itihasa remains in the RAG
    # dataset (build_rag.py), where its value is the aligned English translation.
    for source_iter, label in ((_iter_bg, "BG"),
                               (_iter_gretil, "GRETIL"), (_iter_mbh, "Mahabharata"),
                               (_iter_dcs, "DCS"), (_iter_hf_mono, "HF-mono")):
        print(f"[{label}] extracting...")
        n0 = len(kept)
        for chunk_key, block in source_iter():
            for sub in resegment_long(block):
                if not is_valid_verse(sub, MIN_CHARS):
                    short += 1
                    continue
                # dedup on a whitespace-insensitive key so the same verse with
                # different line-breaks/spacing across editions counts as one
                key = "".join(sub.split())
                h = hashlib.md5(key.encode("utf-8")).digest()
                if h in seen:
                    dup += 1
                    continue
                seen.add(h)
                kept.append((chunk_key, sub))
        stats[label] = len(kept) - n0
        print(f"[{label}] kept {stats[label]:,} unique verses")

    # --- write full corpus ---
    corpus_path = os.path.join(CORPUS_DIR, "shlok_corpus.txt")
    with open(corpus_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n\n".join(text for _, text in kept))
        f.write("\n")

    # --- chapter/chunk-level train/val split ---
    def is_val(chunk_key):
        d = hashlib.md5(chunk_key.encode("utf-8")).hexdigest()
        return int(d, 16) % VAL_EVERY == 0

    train, val = [], []
    for chunk_key, text in kept:
        (val if is_val(chunk_key) else train).append(text)

    with open(os.path.join(CORPUS_DIR, "train.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n\n".join(train) + "\n")
    with open(os.path.join(CORPUS_DIR, "val.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n\n".join(val) + "\n")

    total_bytes = os.path.getsize(corpus_path)
    print("\n=== corpus build summary ===")
    for k, v in stats.items():
        print(f"  {k:10s} {v:>8,} verses")
    print(f"  {'TOTAL':10s} {len(kept):>8,} verses")
    print(f"  duplicates removed: {dup:,}   too-short dropped: {short:,}")
    print(f"  train: {len(train):,}   val: {len(val):,}  ({100*len(val)/max(1,len(kept)):.1f}% held out)")
    print(f"  corpus size: {total_bytes/1_000_000:.1f} MB")
    print(f"  -> {corpus_path}")


if __name__ == "__main__":
    build()

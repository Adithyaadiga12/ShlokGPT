"""
ShlokGPT — dataset validation report (DATA_REQUIREMENTS.md Part 4).

Runs read-only checks over the built corpus + RAG dataset and prints a report:
corpus size, character-set audit, length distribution, RAG coverage, schema
validation, and a random sample dump. Exits non-zero if a hard check fails.
"""
import collections
import json
import os
import random
import statistics
import sys
import unicodedata

ROOT = os.path.join(os.path.dirname(__file__), "..")
CORPUS = os.path.join(ROOT, "data", "corpus", "shlok_corpus.txt")
VERSES = os.path.join(ROOT, "data", "rag", "verses.jsonl")

REQUIRED_FIELDS = ["id", "source", "source_sanskrit", "category", "book", "chapter",
                   "verse", "speaker", "sanskrit", "transliteration", "translations",
                   "commentary", "keywords", "translation_source"]

FAIL = []


def load_verses():
    """Read the JSONL RAG index (one record per line)."""
    with open(VERSES, encoding="utf-8") as f:
        return [json.loads(ln) for ln in f if ln.strip()]


def hr(t):
    print("\n" + "=" * 60 + f"\n{t}\n" + "=" * 60)


def check_corpus():
    hr("1-2. CORPUS SIZE + CHARACTER SET")
    txt = open(CORPUS, encoding="utf-8").read()
    blocks = txt.split("\n\n")
    print(f"chars: {len(txt):,} | UTF-8 bytes: {len(txt.encode('utf-8')):,} | verse blocks: {len(blocks):,}")

    chars = collections.Counter(txt)
    latin = sorted(c for c in chars if "a" <= c.lower() <= "z")
    digits = sorted(c for c in chars if c.isdigit())
    non_dev = sorted(c for c in chars if not ("ऀ" <= c <= "ॿ" or c in " \n"))
    print(f"distinct characters: {len(chars)}")
    print(f"Latin letters: {latin or 'none'}")
    print(f"digits: {digits or 'none'}")
    print(f"non-Devanagari/space chars: {[repr(c) for c in non_dev] or 'none'}")
    if latin:
        FAIL.append("Latin letters present in corpus")
    if digits:
        FAIL.append("digits present in corpus")

    hr("6. LENGTH DISTRIBUTION (aksharas, non-space)")
    lens = sorted(len(b.replace("\n", "").replace(" ", "")) for b in blocks)
    print(f"min: {lens[0]} | median: {statistics.median(lens)} | "
          f"mean: {statistics.mean(lens):.1f} | max: {lens[-1]}")
    print(f"blocks < 10 aksharas: {sum(1 for n in lens if n < 10)} (should be 0)")
    print(f"blocks > 200 aksharas: {sum(1 for n in lens if n > 200)}")


def check_rag():
    hr("5. RAG SCHEMA VALIDATION")
    recs = load_verses()
    ids = set()
    bad = 0
    for r in recs:
        missing = [f for f in REQUIRED_FIELDS if f not in r]
        if missing:
            bad += 1
            if bad <= 3:
                print(f"  {r.get('id','?')} missing {missing}")
        if r["id"] in ids:
            FAIL.append(f"duplicate id {r['id']}")
        ids.add(r["id"])
    print(f"records: {len(recs):,} | unique ids: {len(ids):,} | "
          f"records missing fields: {bad}")
    if bad:
        FAIL.append(f"{bad} records missing required fields")

    hr("4. RAG COVERAGE (>=1 English translation)")
    by_src = collections.defaultdict(lambda: [0, 0])
    for r in recs:
        by_src[r["source"]][0] += 1
        if r["translations"]:
            by_src[r["source"]][1] += 1
    for src, (tot, tr) in sorted(by_src.items()):
        print(f"  {src:38s} {tr:>7,}/{tot:<7,} ({100*tr/tot:.0f}%)")

    hr("7. SAMPLE DUMP (5 random records)")
    random.seed(42)
    for r in random.sample(recs, 5):
        t0 = next(iter(r["translations"].items()), ("—", ""))
        print(f"\n[{r['id']}] {r['source']} ch{r['chapter']} v{r['verse']}")
        print(f"  SKT: {r['sanskrit'][:70].replace(chr(10),' ')}")
        print(f"  {t0[0]}: {t0[1][:90]}")
    return recs


def main():
    check_corpus()
    check_rag()
    hr("RESULT")
    if FAIL:
        print("FAILED:")
        for f in FAIL:
            print("  -", f)
        sys.exit(1)
    print("All hard checks passed. ✓")


if __name__ == "__main__":
    main()

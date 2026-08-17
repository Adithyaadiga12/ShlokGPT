# ShlokGPT — Dataset

Clean Sanskrit datasets for training a GPT from scratch and for retrieval-augmented
Q&A, built entirely from public-domain / permissively-licensed sources. Everything
under `data/` is produced by the scripts in `scripts/` and rebuilds from empty with
one command.

Two datasets, different purposes:

1. **Training corpus** — 87 MB of clean Devanagari verse (one file), Sanskrit only.
2. **RAG dataset** — a source-tagged verse index covering **every** corpus text
   (575K records), so any source is retrievable (e.g. "give me Garuda Purana
   shlokas"). English translations included where public-domain-aligned, plus
   entity / glossary / evaluation support files.

---

## Quick start

```bash
pip install -r requirements.txt
python scripts/build_all.py          # fetch -> build -> validate (rebuilds everything)
python scripts/validate.py           # re-run validation report only
```

Fetch steps are idempotent (skip files already in `data/raw/`); pass `--force` to
re-download. On Windows the pipeline sets `PYTHONUTF8=1` itself; if you run a script
directly in a console, set it first so Devanagari prints correctly.

---

## What's in the dataset

```
data/
├── corpus/
│   ├── shlok_corpus.txt   # training corpus — 479,170 verse blocks, 87.3 MB
│   ├── train.txt          # ~94% (split BY CHAPTER/chunk, no verse leakage)
│   └── val.txt            # ~6% held out
├── rag/
│   ├── verses.jsonl       # 575,377 source-tagged verse records, JSONL (~319 MB)
│   ├── sources.json       # 60 source texts, each with its license
│   ├── entities.json      # 30 characters / places
│   └── glossary.json      # 40 Sanskrit term definitions
└── eval/
    └── queries.json       # 37 retrieval eval queries (incl. 8 should-fail)
```

**Corpus:** 479,170 verse blocks, 32.1 M characters, 87.3 MB. Validated clean —
68 distinct characters, **0 Latin letters, 0 digits, Devanagari + whitespace only**,
every block 10–200 aksharas. No repeated verses (whitespace-insensitive dedup).

**RAG (`verses.jsonl`):** 575,377 records — one per verse, covering every corpus
text, each tagged with `source` + `category` so retrieval can filter by text (e.g.
all Garuda Purana verses). 16% carry an English translation (the Bhagavad Gita with 9
translators + commentary; the Ramayana + Mahabharata with M. N. Dutt's
public-domain translation). The rest are Sanskrit-only but fully retrievable.

---

## Sources & licenses

Every source is public-domain or permissively licensed. Per-text license is recorded
in `data/rag/sources.json`.

| Group | Texts | Role | License |
|---|---|---|---|
| **Bhagavad Gita** | 1 (719 verses) | corpus + RAG | GPL-3.0 (vedicscriptures) |
| **Itihasa** (Ramayana + Mahabharata, Dutt) | — (93K aligned pairs) | **RAG only** | Apache-2.0; English = M. N. Dutt (public domain) |
| **Epics** — full Mahabharata (Pune ed.), Valmiki Ramayana, Harivamsha | 3 | corpus + RAG | CC BY-NC-SA 4.0 (GRETIL) |
| **Puranas** | 18 | corpus + RAG | CC BY-NC-SA 4.0 (GRETIL) |
| **Kavya** (Kalidasa, Bharavi, Magha, Bhatti, Jayadeva, Kathasaritsagara…) | 16 | corpus + RAG | CC BY-NC-SA 4.0 (GRETIL) |
| **Dharmashastra** (Manusmriti, Yajnavalkya, Narada…) | 9 | corpus + RAG | CC BY-NC-SA 4.0 (GRETIL) |
| **Subhashita** anthologies | 3 | corpus + RAG | CC BY-NC-SA 4.0 (GRETIL) |
| **Vedas** (Rigveda, Samaveda, Khilani) | 3 | corpus + RAG | CC BY-NC-SA 4.0 (GRETIL) |
| **Upanishads** (principal) | 6 | corpus + RAG | CC BY-NC-SA 4.0 (GRETIL) |

> ⚠️ The GRETIL portion is **NonCommercial (CC BY-NC-SA 4.0)**. Fine for personal /
> research use with attribution; not for commercial use. The Bhagavad Gita and the
> RAG English (M. N. Dutt) are unrestricted.

**Deliberately excluded to avoid redundancy:** Itihasa is **not** in the training
corpus — it is the same two epics as the full GRETIL Ramayana + Mahabharata, only in
a different edition, so it would repeat content. It is kept in the RAG dataset, where
its value is the aligned English. The non-critical Vishnu Purana (vulgate) was also
skipped because it duplicates the critical edition already used.

---

## How it was built

The pipeline is fetch → extract → clean → dedup → split. It handles two very
different raw formats and funnels both through one cleaning pass.

**1. Fetch** (`fetch_bg.py`, `fetch_itihasa.py`, `fetch_gretil.py`) — download raw
sources into `data/raw/`. Bhagavad Gita as per-verse JSON; Itihasa as aligned
`.sn`/`.en` text; GRETIL as HTML (romanized IAST).

**2. Transliterate** (`gretil_extract.py`) — GRETIL texts are romanized (IAST), not
Devanagari. They are transliterated to Devanagari with `indic_transliteration`, which
is **lossless and produces correct conjuncts** — the key reason this corpus is clean
where the original 31 MB corpus (a romanization→Devanagari conversion) had broken
conjuncts like `शरुत्वा` for `श्रुत्वा`. Two GRETIL layouts are supported: corpustei
files (verse text + reference labels) and legacy epic files (`reference<TAB>verse`).

**3. Clean** (`common.py`) — one pass applied to every source:
- Normalize Unicode to NFC; keep **Devanagari only** (strip Latin/IAST, digits,
  symbols, HTML).
- Strip verse-number and reference markers (`॥२-४७॥`, `//ViP_1,1.0//`, `/AP_1.001ab/`,
  bare labels), dandas, and Vedic pitch accents.
- Drop transliterated English editorial apparatus (caught by an English-word filter,
  a nukta `़` canary, and an all-halant-consonant "reference fragment" net).
- Keep avagraha (`ऽ`) and phonemic signs (anusvara, visarga, candrabindu).

**4. Dedup + normalize length** (`build_corpus.py`) — remove duplicate verses using a
**whitespace-insensitive key**, so the same verse with different line-breaks/spacing
across editions counts once (this removed ~33K near-duplicates). Drop blocks < 10
aksharas; re-split any block > 200 aksharas into shloka-sized units so no unsegmented
prose runs survive.

**5. Split** — train/val split is done **by chapter/chunk, never per-verse**, so
neighbouring verses can't leak across the split (~94% train / ~6% val).

**6. RAG + support files** — `build_rag.py` (verse records + English), `build_sources.py`
(metadata + licenses), `build_entities.py` / `build_glossary.py` (curated), `build_eval.py`
(eval queries). `validate.py` prints the full Part-4 report and fails on any hard error.

**Notable challenges solved:** GRETIL uses at least four different reference-marker
formats across files (bare labels, `//ref//`, `/ref/`, no-closing-slash); critical
editions embed English apparatus that transliterates into Devanagari gibberish;
several files collapse into one giant block without segmentation. Each was handled
generically (format-agnostic reference regex + nukta/fragment nets + length fallback)
rather than per-file, so the pipeline is robust to new GRETIL sources.

---

## Schemas

**`verses.jsonl`** (one record per line):
```json
{
  "id": "BG2.47", "source": "Bhagavad Gita", "source_sanskrit": "श्रीमद्भगवद्गीता",
  "category": "Gita", "book": null, "chapter": 2, "verse": 47, "speaker": "श्रीभगवान्",
  "sanskrit": "कर्मण्येवाधिकारस्ते ...", "transliteration": "karmaṇyevādhikāraste ...",
  "translations": { "Swami Sivananda": "..." },
  "commentary": "...", "keywords": [], "translation_source": "human"
}
```
Every record has the same fields. `category` (Gita / Epic / Purana / Kavya /
Dharmashastra / Subhashita / Veda / Upanishad) enables source filtering. Sanskrit-only
sources carry `translations: {}` and `translation_source: "none"` — still retrievable
by Sanskrit + source. All translations are human + public-domain-derived (no machine
translation). ids are prefixed by source (`BG2.47`, `ITIH1`, `GarudaP-1`, `MBH-01-1`).
`entities.json`, `glossary.json`, `queries.json` are simple flat records (see the files).

---

## Rebuild from empty

```bash
pip install -r requirements.txt          # torch, numpy, requests, indic_transliteration
python scripts/build_all.py              # ~2-3 min (Mahabharata transliteration dominates)
```

Storage: `data/raw/` (~150 MB of downloads) is gitignored and re-derivable. The built
corpus + `verses.jsonl` (~319 MB) are tracked via **Git LFS** (`.gitattributes`); run
`git lfs install` once before committing, or add them to `.gitignore` and rebuild
locally instead.

---

## Limitations & how to extend

- **Register:** mostly classical verse. The Vedas (~11K verses) add an older Vedic
  register; drop the three `Veda` entries from `fetch_gretil.py` and rebuild for a
  pure-classical corpus.
- **Size ceiling:** ~87 MB is roughly the ceiling for clean, non-redundant, classical
  *verse* from readily-available GRETIL sources (the big remaining Puranas — Skanda,
  Padma, Bhagavata bk 10 — are dead links on GRETIL). Reaching 100 MB+ would require
  classical prose (Upanishad commentaries, Harshacharita) or non-GRETIL sources.
- **RAG coverage:** only the Bhagavad Gita and the epics have verse-aligned English;
  the Puranas/Kavya/Vedas are corpus-only. Public-domain translations (Griffith for
  the Vedas, Wilson for Vishnu Purana) could be added and aligned later.
- **Book/verse numbering** was stripped from the corpus (it is training text); the RAG
  dataset preserves identity where the source provides it.

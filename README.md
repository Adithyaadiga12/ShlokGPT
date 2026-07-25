# ShlokGPT

A from-scratch GPT for classical Sanskrit — trained on a clean corpus of scripture
and classical verse — plus a retrieval-augmented (RAG) dataset for English Q&A over
the verses.

The project is built bottom-up, without pulling in a pretrained model or an
off-the-shelf tokenizer: the data is collected and cleaned from source, the BPE
tokenizer is written by hand, and the model/training follow.

## Components

| Part | Status | Where |
|---|---|---|
| **Dataset** — 87 MB clean Devanagari corpus + 94K RAG records | ✅ done | `data/`, see **[DATASET.md](DATASET.md)** |
| **Tokenizer** — byte-level BPE, from scratch (minbpe-style) | ✅ done | [tokenizer.py](tokenizer.py), benchmarked in [tokenization_comp.md](tokenization_comp.md) |
| **Model** — GPT architecture | 🚧 todo | [model.py](model.py) |
| **Training** loop | 🚧 todo | [train.py](train.py) |

## The dataset (summary)

Two datasets, both rebuilt from source by scripts in `scripts/` — full details in
**[DATASET.md](DATASET.md)**:

- **Training corpus** (`data/corpus/shlok_corpus.txt`) — 479,170 verse blocks, 87.3 MB
  of clean Devanagari verse: full Mahabharata, Ramayana + Harivamsha, 18 Puranas,
  Kathasaritsagara, Subhashita anthologies, Dharmashastra, Vedas, and Kavya. Validated
  clean (0 Latin, 0 digits, Devanagari-only), non-redundant, with a chapter-level
  train/val split.
- **RAG dataset** (`data/rag/verses.jsonl`) — 575,377 source-tagged verse records
  covering **every** corpus text (so any source is retrievable, e.g. Garuda Purana),
  with aligned English where available (Bhagavad Gita + Ramayana/Mahabharata), plus
  entity, glossary, and evaluation support files.

## Quick start

```bash
pip install -r requirements.txt

# Build the datasets from source (fetch -> clean -> validate)
python scripts/build_all.py

# Train / inspect the from-scratch BPE tokenizer
python tokenizer.py
```

See **[DATASET.md](DATASET.md)** for sources, licenses, the full build methodology,
schemas, and how to extend the corpus.

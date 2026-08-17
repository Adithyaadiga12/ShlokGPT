# ShlokGPT

A **from-scratch GPT for classical Sanskrit** — a clean Sanskrit corpus collected and
built from source, a SentencePiece tokenizer, and a ~50M-parameter transformer trained
from zero (no pretrained weights). Generates coherent classical Sanskrit across multiple
registers (epic, Vedic, Purāṇic, tantric).

**Companion app:** [Shlok-RAG](https://github.com/Adithyaadiga12/Shlok-RAG) — a
retrieval-augmented Q&A app that answers English questions with real verses. Built on
the dataset produced here.

## Layout

```
ShlokGPT/
├── dataset/        # build the corpus + RAG data from source
│   ├── scripts/        fetch → clean → validate → build
│   ├── data/           generated corpus + verses (gitignored, reproducible)
│   └── DATASET.md      sources, licenses, schema, rebuild steps
└── gpt/            # the from-scratch language model
    ├── tokenizer/      SentencePiece (train_tokenizer.py, encode.py)
    ├── model.py        nanoGPT-style decoder-only transformer
    ├── train.py        training loop (checkpoint/resume, Kaggle-ready)
    ├── generate.py     sampling with temperature / top-k / repetition penalty
    ├── sample.py       quick sampler from a checkpoint
    └── edge_cases.py   prompt battery for eval
```

## The model

| | |
|---|---|
| Parameters | ~49.8M (8 layers, 10 heads, 640 dim, block 256) |
| Vocabulary | 16,000 (SentencePiece unigram, Devanagari) |
| Training data | ~920 MB corpus → ~86M tokens |
| Final val loss | 4.16 |
| Trained on | Kaggle T4 (float16), 40,000 iters |

Weights (`final_ckpt.pt`, ~570 MB) are hosted on Hugging Face, not git.

## The dataset

Built from source by `dataset/scripts/` — full details in
**[dataset/DATASET.md](dataset/DATASET.md)**:

- **Training corpus** — clean Devanagari verse (Mahābhārata, Rāmāyaṇa, Purāṇas, Vedas,
  Kāvya, Dharmaśāstra…), validated 0 Latin / 0 digits / Devanagari-only, with a
  train/val split.
- **RAG dataset** (`verses.jsonl`) — 575,377 source-tagged verse records, with aligned
  English where available (Gītā + epics). Feeds the [Shlok-RAG](https://github.com/Adithyaadiga12/Shlok-RAG) app.

## Quick start

```bash
pip install -r requirements.txt

# 1. (optional) rebuild the dataset from source
python dataset/scripts/build_all.py

# 2. tokenizer -> token binaries
python gpt/tokenizer/train_tokenizer.py
python gpt/tokenizer/encode.py

# 3. train (locally, or on Kaggle with DATA_DIR / OUT_DIR env vars)
python gpt/train.py

# 4. generate
python gpt/generate.py --checkpoint gpt/final_ckpt.pt \
    --tokenizer gpt/tokenizer/shlok.model \
    --prompt "धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः"
```

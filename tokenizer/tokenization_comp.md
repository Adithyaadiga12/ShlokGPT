# Tokenizer Comparison — ShlokGPT

Benchmark of a **from-scratch byte-level BPE** implementation against
**SentencePiece (Unigram)** on a Sanskrit shloka corpus.

## Setup

- **Corpus:** Sanskrit shlokas (Mahabharata, Valmiki Ramayana, Ramcharitmanas, Rigveda, Yajurveda, Atharvaveda, Bhagavad Gita) — 11.9M chars total
- **Trained on:** first 300,000 chars (slice used so the pure-Python implementation finishes quickly)
- **Target vocab size:** 1000 (both)
- **Test string:** `धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः` (42 chars)

## Results

| Metric | Ours (from-scratch BPE) | SentencePiece (Unigram) |
|---|---|---|
| Training time | 45.9 s | 1.4 s |
| Speed | baseline | **~33x faster** |
| Tokens on test string | 20 | 14 |
| Tokens per char | 0.48 | 0.33 |
| Whitespace handling | glues space to word-start (e.g. `' कुर'`) | explicit `▁` boundary marker |
| Partial-character tokens | possible mid-vocab | none (normalized) |

For reference, GPT-2's `tiktoken` scores ~2.9 tokens/char on Devanagari — both
tokenizers here are ~6-9x more efficient than an English-trained tokenizer.

## Splits side by side

**Ours:**
```
धर्म | क्ष | े | त्र | े | ' कुर' | ु | क्ष | े | त्र | े | ' सम' | व | ेत | 'ा य' | ुय | ुत | ्स | व | ः
```

**SentencePiece:**
```
▁धर्म | क्ष | े | त्र | े | ▁कुरुक्षेत्र | े | ▁सम | व | े | ता | ▁युयुत्स | व | ः
```

## Key finding

The token-count gap comes almost entirely from one word:

- **SP** learned `कुरुक्षेत्र` (Kurukshetra) as a **single token** — it's very frequent in this corpus.
- **Ours** split the same word into 6 syllable-level pieces.

Two reasons for the difference:

1. **Vocab budget** — ours only formed 744 merges (1000 − 256 base bytes); SP's Unigram algorithm builds a smarter 1000-piece vocab via probabilistic pruning (EM), so it captured whole frequent words.
2. **Word boundaries** — SP marks boundaries with `▁` and can learn whole words as units. Ours instead spends vocab gluing spaces to word-starts (`' कुर'`), which wastes capacity.

## How to close the gap (ours)

1. **Larger vocab** (~2000-4000) → learns whole common words like `कुरुक्षेत्र`.
2. **Train on the full corpus** (11.9M chars, not the 300K slice) → better statistics.
3. **Speed optimization** — only recount pairs affected by the last merge instead of rescanning the whole sequence each round → moves training time toward SP's range.

## Decision

Use the **from-scratch BPE** as ShlokGPT's tokenizer (trained at larger vocab on the
full corpus). Rationale:

- Token efficiency is already in the same range as SentencePiece and far ahead of English-trained tokenizers.
- Building it from scratch is the point of the project — it demonstrates understanding of tokenization internals.
- The benchmark against SentencePiece validates the implementation and documents exactly *why* SP is the production choice (Unigram pruning, explicit word boundaries, C++ speed).

## Notes on SentencePiece (for later)

- **Two algorithms:** BPE (bottom-up greedy merging) and **Unigram LM** (top-down probabilistic pruning). Unigram is SP's signature and tends to give cleaner splits for morphologically rich / inflected languages like Sanskrit.
- **No pre-tokenization needed:** treats whitespace as a normal symbol (`▁`), making it language-agnostic and well suited to no-space or sandhi-heavy text.
- **Used by:** T5, LLaMA, ALBERT, and most modern multilingual models.
- **`character_coverage`:** set below 1.0 (e.g. 0.9995) so rare characters don't blow up the vocab — important for Devanagari with its accent marks and rare conjuncts. 
"""
encode.py — encode train.txt / val.txt into token-ID binaries using the trained
SentencePiece tokenizer. Run once on the laptop -> train.bin / val.bin.

Streams the corpus in line batches so a ~900MB / ~100M-token corpus never has to
sit in RAM as one giant Python list. Tokens are uint16 (vocab 16000 < 65535).
"""
import os
import numpy as np
import sentencepiece as spm

_HERE   = os.path.dirname(os.path.abspath(__file__))                 # gpt/tokenizer
_CORPUS = os.path.join(os.path.dirname(os.path.dirname(_HERE)), "dataset", "data", "corpus")
MODEL   = os.path.join(_HERE, "shlok.model")

sp = spm.SentencePieceProcessor(model_file=MODEL)

BATCH = 50_000   # lines per encode call

for split in ["train", "val"]:
    txt = os.path.join(_CORPUS, f"{split}.txt")
    out = os.path.join(_CORPUS, f"{split}.bin")

    with open(txt, encoding="utf-8") as f, open(out, "wb") as fout:
        batch = []
        for line in f:
            line = line.rstrip("\n")
            if line:
                batch.append(line)
            if len(batch) >= BATCH:
                for ids in sp.encode(batch):            # list[list[int]]
                    np.array(ids, dtype=np.uint16).tofile(fout)
                batch = []
        if batch:                                        # flush remainder
            for ids in sp.encode(batch):
                np.array(ids, dtype=np.uint16).tofile(fout)

    n = os.path.getsize(out) // 2                         # uint16 = 2 bytes/token
    print(f"{split:5s}: {n:,} tokens  ->  {out}")

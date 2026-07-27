"""
encode.py — encode train.txt / val.txt into token-ID binaries using the trained
SentencePiece tokenizer. Run once on the laptop -> train.bin / val.bin.

Streams the corpus in line batches so a ~900MB / ~100M-token corpus never has to
sit in RAM as one giant Python list. Tokens are uint16 (vocab 16000 < 65535).
"""
import os
import numpy as np
import sentencepiece as spm

ROOT  = r"C:\Adithya\ShlokGPT"
MODEL = ROOT + r"\tokenizer\shlok.model"

sp = spm.SentencePieceProcessor(model_file=MODEL)

BATCH = 50_000   # lines per encode call

for split in ["train", "val"]:
    txt = ROOT + rf"\data\corpus\{split}.txt"
    out = ROOT + rf"\data\corpus\{split}.bin"

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

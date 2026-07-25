"""
encode.py — encode train.txt / val.txt into token-ID binaries using the trained
SentencePiece tokenizer. Run once on the laptop -> train.bin / val.bin.
"""
import numpy as np
import sentencepiece as spm

ROOT  = r"C:\Adithya\ShlokGPT"
MODEL = ROOT + r"\tokenizer\shlok.model"

sp = spm.SentencePieceProcessor(model_file=MODEL)

for split in ["train", "val"]:
    txt = ROOT + rf"\data\corpus\{split}.txt"
    out = ROOT + rf"\data\corpus\{split}.bin"

    text = open(txt, encoding="utf-8").read()   # read the whole file
    ids  = sp.encode(text)                       # list of token ids
    arr  = np.array(ids, dtype=np.uint16)        # 2 bytes/token (ids < 4000)
    arr.tofile(out)                              # raw binary dump

    print(f"{split:5s}: {len(arr):,} tokens  ->  {out}")
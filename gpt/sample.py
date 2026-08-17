"""
sample.py — generate Sanskrit text from a trained checkpoint.

Local:  python sample.py
Kaggle: set OUT_DIR + SP_MODEL env vars (see below), then run.
"""
import os

import torch
import sentencepiece as spm

from model import GPT, GPTConfig

_ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # repo root (gpt/..)
OUT_DIR  = os.environ.get("OUT_DIR",  os.path.join(_ROOT, "out"))
SP_MODEL = os.environ.get("SP_MODEL", os.path.join(os.path.dirname(os.path.abspath(__file__)), "tokenizer", "shlok.model"))
PROMPT   = os.environ.get("PROMPT", "")          # empty = start fresh (from <s>)

num_samples    = 3
max_new_tokens = 200
temperature    = 0.8      # lower = safer/repetitive, higher = wilder
top_k          = 200

device = "cuda" if torch.cuda.is_available() else "cpu"
sp = spm.SentencePieceProcessor(model_file=SP_MODEL)

ck = torch.load(os.path.join(OUT_DIR, "ckpt.pt"), map_location=device)
model = GPT(GPTConfig(**ck["config"]))
model.load_state_dict(ck["model"])
model.eval().to(device)
print(f"loaded checkpoint: iter {ck['iter']}, val loss {ck['best_val']:.4f}\n")

start = sp.encode(PROMPT) if PROMPT else [sp.bos_id()]
x = torch.tensor([start], dtype=torch.long, device=device)

for i in range(num_samples):
    y = model.generate(x, max_new_tokens=max_new_tokens,
                       temperature=temperature, top_k=top_k)
    print(f"--- sample {i+1} ---")
    print(sp.decode(y[0].tolist()))
    print()

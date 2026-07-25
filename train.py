"""
train.py — train the small GPT on train.bin / val.bin. Checkpoints + resumes.
Runs locally (CPU, slow) and on Kaggle (GPU). For Kaggle, set env vars:
    DATA_DIR=/kaggle/input/<your-dataset>   OUT_DIR=/kaggle/working
"""
import os
import math
import time
from contextlib import nullcontext

import numpy as np
import torch

from model import GPT, GPTConfig

# ---------------- config (edit these) ----------------
DATA_DIR = os.environ.get("DATA_DIR", r"C:\Adithya\ShlokGPT\data\corpus")
OUT_DIR  = os.environ.get("OUT_DIR",  r"C:\Adithya\ShlokGPT\out")

# model (~12M params at vocab 4000)
block_size, n_layer, n_head, n_embd, dropout = 256, 6, 6, 384, 0.1
vocab_size = 4000

# optimisation
batch_size     = 32
max_iters      = 20000
eval_interval  = 500
eval_iters     = 100
learning_rate  = 6e-4
min_lr         = 6e-5
warmup_iters   = 200
weight_decay   = 0.1
grad_clip      = 1.0
seed           = 1337
# -----------------------------------------------------

os.makedirs(OUT_DIR, exist_ok=True)
torch.manual_seed(seed)

device = "cuda" if torch.cuda.is_available() else "cpu"
if device == "cuda":
    dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    ctx = torch.autocast(device_type="cuda", dtype=dtype)
else:
    dtype = torch.float32
    ctx = nullcontext()
scaler = torch.cuda.amp.GradScaler(enabled=(dtype == torch.float16))

train_data = np.memmap(os.path.join(DATA_DIR, "train.bin"), dtype=np.uint16, mode="r")
val_data   = np.memmap(os.path.join(DATA_DIR, "val.bin"),   dtype=np.uint16, mode="r")


def get_batch(split):
    data = train_data if split == "train" else val_data
    ix = torch.randint(len(data) - block_size, (batch_size,))
    x = torch.stack([torch.from_numpy(data[i:i + block_size].astype(np.int64)) for i in ix])
    y = torch.stack([torch.from_numpy(data[i + 1:i + 1 + block_size].astype(np.int64)) for i in ix])
    return x.to(device), y.to(device)


cfg = GPTConfig(block_size=block_size, vocab_size=vocab_size, n_layer=n_layer,
                n_head=n_head, n_embd=n_embd, dropout=dropout)
model = GPT(cfg).to(device)
print(f"params: {model.num_params()/1e6:.1f}M | device: {device} | dtype: {dtype}")

optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate,
                              weight_decay=weight_decay, betas=(0.9, 0.95))

# ---- resume from checkpoint if present ----
ckpt_path = os.path.join(OUT_DIR, "ckpt.pt")
start_iter, best_val = 0, 1e9
if os.path.exists(ckpt_path):
    ck = torch.load(ckpt_path, map_location=device)
    model.load_state_dict(ck["model"])
    optimizer.load_state_dict(ck["optimizer"])
    start_iter, best_val = ck["iter"] + 1, ck["best_val"]
    print(f"resumed from iter {start_iter} (best val {best_val:.4f})")


def get_lr(it):
    if it < warmup_iters:
        return learning_rate * (it + 1) / warmup_iters
    if it > max_iters:
        return min_lr
    ratio = (it - warmup_iters) / (max_iters - warmup_iters)
    return min_lr + 0.5 * (1 + math.cos(math.pi * ratio)) * (learning_rate - min_lr)


@torch.no_grad()
def estimate_loss():
    model.eval()
    out = {}
    for split in ("train", "val"):
        losses = torch.zeros(eval_iters)
        for k in range(eval_iters):
            x, y = get_batch(split)
            with ctx:
                _, loss = model(x, y)
            losses[k] = loss.item()
        out[split] = losses.mean().item()
    model.train()
    return out


t0 = time.time()
for it in range(start_iter, max_iters + 1):
    for pg in optimizer.param_groups:
        pg["lr"] = get_lr(it)

    if it % eval_interval == 0:
        losses = estimate_loss()
        print(f"iter {it:5d} | train {losses['train']:.4f} | val {losses['val']:.4f} "
              f"| {(time.time()-t0)/60:.1f} min")
        if losses["val"] < best_val:
            best_val = losses["val"]
            torch.save({"model": model.state_dict(), "optimizer": optimizer.state_dict(),
                        "iter": it, "best_val": best_val, "config": cfg.__dict__}, ckpt_path)
            print(f"  -> saved checkpoint (best val {best_val:.4f})")

    x, y = get_batch("train")
    with ctx:
        _, loss = model(x, y)
    optimizer.zero_grad(set_to_none=True)
    scaler.scale(loss).backward()
    scaler.unscale_(optimizer)
    torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
    scaler.step(optimizer)
    scaler.update()

print(f"done. best val loss: {best_val:.4f}")

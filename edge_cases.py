"""
edge_cases.py — probe the trained model across varied / adversarial prompts.
Loads the checkpoint once, runs a battery of prompts.
"""
import sentencepiece as spm
import torch
from model import GPT, GPTConfig

CKPT = "final_ckpt.pt"
TOK  = "tokenizer/shlok.model"

sp = spm.SentencePieceProcessor(); sp.load(TOK)
ck = torch.load(CKPT, map_location="cpu")
model = GPT(GPTConfig(**ck["config"])); model.load_state_dict(ck["model"]); model.eval()

def gen(prompt, n=80, temp=0.9, top_k=50, rep=1.3, nrng=3):
    ids = sp.encode(prompt) if prompt.strip() else [sp.bos_id()]
    x = torch.tensor([ids], dtype=torch.long)
    with torch.no_grad():
        y = model.generate(x, max_new_tokens=n, temperature=temp, top_k=top_k,
                           repetition_penalty=rep, no_repeat_ngram_size=nrng)
    return sp.decode(y[0].tolist())

CASES = [
    ("Dharma theme",        "धर्मः सत्यं च"),
    ("Knowledge/Upanishad", "विद्या ददाति विनयं"),
    ("Devotion",            "ॐ नमः शिवाय"),
    ("Nature/description",  "वने वसन्ति मुनयः"),
    ("English input",       "Hello, how are you"),
    ("Mixed En+Sa",         "The king राजा said"),
    ("Single word",         "अग्निः"),
    ("Number",              "एकं द्वे त्रीणि"),
    ("Question form",       "किं कर्तव्यम्"),
    ("Nonsense Devanagari",  "कखगघ ङचछज"),
]

for label, p in CASES:
    print("\n" + "="*80)
    print(f"[{label}]  prompt: {p!r}")
    print("-"*80)
    print(gen(p))

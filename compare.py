import time
import sentencepiece as spm
from tokenizer import BPETokenizer

VOCAB_SIZE = 1000

# ---------- load corpus ----------
with open("data/corpus/shlok_corpus.txt", "r", encoding="utf-8") as f:
    corpus = f.read()

sample = corpus[:300_000]   # slice so OURS (pure python) finishes fast
print(f"training both on {len(sample)} chars, vocab={VOCAB_SIZE}\n")

# ---------- 1. TRAIN OURS ----------
t0 = time.time()
ours = BPETokenizer()
ours.train(sample, vocab_size=VOCAB_SIZE)
ours_time = time.time() - t0
print(f"[OURS] trained in {ours_time:.1f}s")

# ---------- 2. TRAIN SENTENCEPIECE ----------
with open("sp_input.txt", "w", encoding="utf-8") as f:
    f.write(sample)

t0 = time.time()
spm.SentencePieceTrainer.train(
    input="sp_input.txt",
    model_prefix="sp_shlok",
    vocab_size=VOCAB_SIZE,
    model_type="unigram",
    character_coverage=0.9995,
)
sp_time = time.time() - t0
sp = spm.SentencePieceProcessor(model_file="sp_shlok.model")
print(f"[SP]   trained in {sp_time:.1f}s")

# ---------- 3. COMPRESSION ----------
test = "धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः"
ours_ids = ours.encode(test)
sp_ids   = sp.encode(test, out_type=int)

print("\n--- COMPRESSION (fewer tokens = better) ---")
print(f"test: {len(test)} chars")
print(f"[OURS] {len(ours_ids)} tokens  ({len(ours_ids)/len(test):.2f} tok/char)")
print(f"[SP]   {len(sp_ids)} tokens  ({len(sp_ids)/len(test):.2f} tok/char)")

# ---------- 4. SPLITS side by side ----------
print("\n--- SPLITS ---")
print(f"[OURS] {ours.decode_pieces(ours_ids)}")
print(f"[SP]   {sp.encode(test, out_type=str)}")

# ---------- 5. SPEED SUMMARY ----------
print(f"\n[SPEED] SP was {ours_time/sp_time:.0f}x faster than ours")
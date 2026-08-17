"""
train_tokenizer.py — trains a SentencePiece tokenizer on the Sanskrit corpus.
Run once. Produces tokenizer/shlok.model and tokenizer/shlok.vocab
"""
import os
import sentencepiece as spm

_HERE   = os.path.dirname(os.path.abspath(__file__))                 # gpt/tokenizer
_CORPUS = os.path.join(os.path.dirname(os.path.dirname(_HERE)),
                       "dataset", "data", "corpus", "shlok_corpus.txt")

spm.SentencePieceTrainer.train(
    input=_CORPUS,
    model_prefix=os.path.join(_HERE, "shlok"),
    vocab_size=16000,
    model_type="unigram",           # unigram > bpe for inflected languages
    character_coverage=0.9995,      # 0.9995 keeps rare Devanagari chars sane
    byte_fallback=True,             # unknown chars -> bytes, never <unk>
    input_sentence_size=5_000_000,  # cap sentences fed to trainer (speed)
    shuffle_input_sentence=True,
    max_sentence_length=8192,
    num_threads=8,
    pad_id=0, unk_id=1, bos_id=2, eos_id=3,
    pad_piece="<pad>", unk_piece="<unk>", bos_piece="<s>", eos_piece="</s>",
)

# ---- sanity check ----
sp = spm.SentencePieceProcessor(model_file=os.path.join(_HERE, "shlok.model"))
test = "धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः"
ids = sp.encode(test)

print("vocab size :", sp.vocab_size())
print("test       :", test)
print("pieces     :", sp.encode(test, out_type=str))
print("ids        :", ids)
print("decoded    :", sp.decode(ids))
print("round-trip :", sp.decode(ids) == test)
print("tok/char   :", round(len(ids) / len(test), 3))
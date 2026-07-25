"""
ShlokGPT - BPE Tokenizer (from scratch)
Byte-level Byte Pair Encoding, following Karpathy's minbpe approach.
"""


def get_stats(ids):
    """Count adjacent pairs. [97,97,98] -> {(97,97):1, (97,98):1}"""
    counts = {}
    for pair in zip(ids, ids[1:]):
        counts[pair] = counts.get(pair, 0) + 1
    return counts



def merge(ids, pair, idx):
    """Replace every occurrence of `pair` with new token `idx`."""
    newids = []
    i = 0
    while i < len(ids):
        if i < len(ids) - 1 and ids[i] == pair[0] and ids[i + 1] == pair[1]:
            newids.append(idx)
            i += 2
        else:
            newids.append(ids[i])
            i += 1
    return newids


class BPETokenizer:
    def __init__(self):
        self.merges = {}   # (int, int) -> int
        self.vocab = {}    # int -> bytes

    def train(self, text, vocab_size, verbose=False):
        assert vocab_size >= 256
        num_merges = vocab_size - 256

        ids = list(text.encode("utf-8"))
        merges = {}
        vocab = {i: bytes([i]) for i in range(256)}

        for i in range(num_merges):
            stats = get_stats(ids)
            if not stats:
                break
            top = max(stats, key=stats.get)
            idx = 256 + i
            ids = merge(ids, top, idx)
            merges[top] = idx
            vocab[idx] = vocab[top[0]] + vocab[top[1]]
            if verbose:
                print(f"merge {i+1}/{num_merges}: {top} -> {idx} (count {stats[top]})")

        self.merges = merges
        self.vocab = vocab

    def encode(self, text):
        """text -> list of token ids"""
        ids = list(text.encode("utf-8"))
        while len(ids) >= 2:
            stats = get_stats(ids)
            pair = min(stats, key=lambda p: self.merges.get(p, float("inf")))
            if pair not in self.merges:
                break
            ids = merge(ids, pair, self.merges[pair])
        return ids

    def decode(self, ids):
        """list of token ids -> text"""
        tokens = b"".join(self.vocab[i] for i in ids)
        return tokens.decode("utf-8", errors="replace")

    def decode_pieces(self, ids):
        """each token id -> readable piece (for inspecting splits)"""
        pieces = []
        for i in ids:
            try:
                pieces.append(self.vocab[i].decode("utf-8"))
            except UnicodeDecodeError:
                pieces.append(f"<{i}:partial>")
        return pieces

    def save(self, path):
        with open(path, "w", encoding="utf-8") as f:
            for (a, b), idx in self.merges.items():
                f.write(f"{a} {b} {idx}\n")

    def load(self, path):
        merges = {}
        vocab = {i: bytes([i]) for i in range(256)}
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                a, b, idx = map(int, line.split())
                merges[(a, b)] = idx
                vocab[idx] = vocab[a] + vocab[b]
        self.merges = merges
        self.vocab = vocab


if __name__ == "__main__":
    with open("data/corpus/shlok_corpus.txt", "r", encoding="utf-8") as f:
        corpus = f.read()

    print("corpus chars:", len(corpus))

    tok = BPETokenizer()
    tok.train(corpus[:100_000], vocab_size=256 + 300, verbose=False)

    test = "धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः"
    ids = tok.encode(test)

    print("\ntest string:", test)
    print("chars:", len(test), "-> tokens:", len(ids))
    print("pieces:", tok.decode_pieces(ids))

    back = tok.decode(ids)
    print("round-trip ok:", back == test)

    tok.save("shlok_tokenizer.model")
    print("saved -> shlok_tokenizer.model")
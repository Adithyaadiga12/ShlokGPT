"""
Fetch the Bhagavad Gita (vedicscriptures/bhagavad-gita) into data/raw/bhagavad-gita/.

719 verses, clean Devanagari + up to 9 English translators + commentary.
License: GPL-3.0. Downloaded as a repo tarball, keeping only slok/*.json.
"""
import io
import os
import tarfile
import requests

RAW = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "bhagavad-gita")
TARBALL = "https://codeload.github.com/vedicscriptures/bhagavad-gita/tar.gz/refs/heads/main"


def main(force=False):
    os.makedirs(RAW, exist_ok=True)
    existing = [f for f in os.listdir(RAW) if f.endswith(".json")]
    if existing and not force:
        print(f"skip  bhagavad-gita ({len(existing)} json files already present)")
        return
    print("downloading tarball...")
    r = requests.get(TARBALL, timeout=180)
    r.raise_for_status()
    n = 0
    with tarfile.open(fileobj=io.BytesIO(r.content), mode="r:gz") as tar:
        for m in tar.getmembers():
            # keep only the per-verse slok JSONs
            if "/slok/" in m.name and m.name.endswith(".json"):
                data = tar.extractfile(m).read()
                out = os.path.join(RAW, os.path.basename(m.name))
                with open(out, "wb") as f:
                    f.write(data)
                n += 1
    print(f"saved {n} slok JSON files -> {RAW}")


if __name__ == "__main__":
    import sys
    main(force="--force" in sys.argv)

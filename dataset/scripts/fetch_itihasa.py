"""
Fetch the Itihasa parallel corpus (Sanskrit <-> English) into data/raw/itihasa/.

Itihasa = ~93K aligned shlokas from Valmiki Ramayana + Mahabharata, with English
from M. N. Dutt (public domain). License: Apache-2.0.
Source: https://github.com/rahular/itihasa
"""
import os
import requests

RAW = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "itihasa")
BASE = "https://raw.githubusercontent.com/rahular/itihasa/main/data/"
FILES = ["train.sn", "train.en", "dev.sn", "dev.en", "test.sn", "test.en"]


def main(force=False):
    os.makedirs(RAW, exist_ok=True)
    for fn in FILES:
        dest = os.path.join(RAW, fn)
        if os.path.exists(dest) and not force:
            print(f"skip  {fn} (exists)")
            continue
        r = requests.get(BASE + fn, timeout=120)
        r.raise_for_status()
        r.encoding = "utf-8"
        with open(dest, "w", encoding="utf-8", newline="\n") as f:
            f.write(r.text)
        print(f"saved {fn}  ({len(r.text):,} chars)")


if __name__ == "__main__":
    import sys
    main(force="--force" in sys.argv)

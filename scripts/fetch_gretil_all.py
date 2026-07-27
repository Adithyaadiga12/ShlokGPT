"""
fetch_gretil_all.py — download the ENTIRE GRETIL corpustei catalog (~800 texts)
into data/raw/gretil/. Skips files already present. Politeness delay between
requests. Used to scale the corpus far beyond the hand-picked SOURCES list.
"""
import os
import re
import time
import requests

RAW = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "gretil")
CATALOG = "https://gretil.sub.uni-goettingen.de/gretil.html"
BASE = "https://gretil.sub.uni-goettingen.de/gretil/corpustei/transformations/html/"


def main():
    os.makedirs(RAW, exist_ok=True)
    r = requests.get(CATALOG, timeout=120)
    r.encoding = "utf-8"
    files = sorted(set(re.findall(
        r"corpustei/transformations/html/(sa_[A-Za-z0-9_.\-]+\.htm)", r.text)))
    print(f"catalog: {len(files)} corpustei files")

    done = skip = fail = 0
    for i, fn in enumerate(files):
        dest = os.path.join(RAW, fn)
        if os.path.exists(dest):
            skip += 1
            continue
        try:
            rr = requests.get(BASE + fn, timeout=120)
            rr.raise_for_status()
            rr.encoding = "utf-8"
            with open(dest, "w", encoding="utf-8", newline="\n") as f:
                f.write(rr.text)
            done += 1
            if done % 25 == 0:
                mb = sum(os.path.getsize(os.path.join(RAW, f)) for f in os.listdir(RAW)
                         if f.endswith(".htm")) / 1e6
                print(f"  {done} new ({i+1}/{len(files)}) | raw gretil ~{mb:.0f} MB")
        except Exception as e:
            fail += 1
            print(f"  FAIL {fn}: {str(e)[:60]}")
        time.sleep(0.3)

    print(f"\ndone: {done} downloaded, {skip} already present, {fail} failed")


if __name__ == "__main__":
    main()

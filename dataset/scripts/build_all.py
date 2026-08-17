"""
ShlokGPT — full dataset rebuild from empty.

Runs the whole pipeline in order: fetch raw sources -> build corpus (+split) ->
build RAG + supporting files -> validate. Idempotent: fetch steps skip files that
already exist (pass --force to re-download). Everything under data/ is reproduced
from scripts, so the datasets can be rebuilt on any machine with no manual steps.

    python scripts/build_all.py
"""
import os
import subprocess
import sys

HERE = os.path.dirname(__file__)
STEPS = [
    "fetch_itihasa.py",
    "fetch_bg.py",
    "fetch_gretil.py",
    "build_corpus.py",
    "build_rag.py",
    "build_sources.py",
    "build_entities.py",
    "build_glossary.py",
    "build_eval.py",
    "validate.py",
]


def main():
    env = dict(os.environ, PYTHONUTF8="1")
    force = "--force" in sys.argv
    for step in STEPS:
        args = [sys.executable, os.path.join(HERE, step)]
        if force and step.startswith("fetch_"):
            args.append("--force")
        print(f"\n{'#'*60}\n# {step}\n{'#'*60}")
        r = subprocess.run(args, env=env)
        if r.returncode != 0:
            print(f"\n!! step failed: {step} (exit {r.returncode})")
            sys.exit(r.returncode)
    print("\nAll steps completed. Datasets are in data/.")


if __name__ == "__main__":
    main()

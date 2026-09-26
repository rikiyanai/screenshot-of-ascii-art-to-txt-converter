#!/usr/bin/env python3
"""Build the decoder's character prior from a TRAINING split of an art corpus.

Counts every character in the training texts, spaces included, and writes
``data/aa_char_prior.json`` with the corpus identity, the slugs used, and the
slugs held out. The held-out slugs must never be counted: they are what the
decoder is scored on.

Only counts leave the corpus. No art text is written.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HELD_OUT = ("hakumen-no-mono", "joshua-bright", "excel-saga", "wizards-climber", "violet-evergarden-tahen")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("archive", type=Path, help="ascii-art-archive checkout")
    parser.add_argument("--collection", default="collections/aahub")
    parser.add_argument("--out", type=Path, default=REPO / "data/aa_char_prior.json")
    args = parser.parse_args()

    root = args.archive / args.collection
    slugs = sorted(p.name for p in root.iterdir() if p.is_dir())
    train = [s for s in slugs if s not in HELD_OUT]
    counts: Counter[str] = Counter()
    pages = 0
    for slug in train:
        for text in sorted((root / slug).glob("res*.txt")):
            body = text.read_text(encoding="utf-8")
            counts.update(ch for ch in body if ch not in "\r\n")
            pages += 1
    commit = subprocess.run(["git", "-C", str(args.archive), "rev-parse", "HEAD"],
                            capture_output=True, text=True, check=True).stdout.strip()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({
        "schema": "aa_char_prior.v1",
        "corpus": "rikiyanai/ascii-art-archive:" + args.collection,
        "corpus_commit": commit,
        "train_slugs": train,
        "held_out_slugs": list(HELD_OUT),
        "train_pages": pages,
        "total_characters": sum(counts.values()),
        "counts": dict(counts.most_common()),
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{pages} training pages, {len(counts)} distinct characters -> {args.out}")


if __name__ == "__main__":
    main()

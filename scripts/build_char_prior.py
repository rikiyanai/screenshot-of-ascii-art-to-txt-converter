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
import hashlib
import json
from collections import Counter
from pathlib import Path

from archive_snapshot import SPLIT, load_split, read_blobs

REPO = Path(__file__).resolve().parent.parent


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("archive", type=Path, help="ascii-art-archive checkout")
    parser.add_argument("--split", type=Path, default=SPLIT)
    parser.add_argument("--out", type=Path, default=REPO / "data/aa_char_prior.json")
    args = parser.parse_args()

    split, jobs = load_split(args.archive, args.split)
    held_out = set(split["held_out_slugs"])
    train = [s for s in jobs if s not in held_out]
    counts: Counter[str] = Counter()
    pages = 0
    paths = [stem + ".txt" for slug in train for stem in jobs[slug]]
    for _, blob in read_blobs(args.archive, split, paths):
        body = blob.decode("utf-8")
        counts.update(ch for ch in body if ch not in "\r\n")
        pages += 1
    if pages + sum(len(jobs[s]) for s in held_out) != split["expected_pairs"]:
        raise ValueError("training and held-out pages do not cover the pinned corpus")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({
        "schema": "aa_char_prior.v1",
        "corpus": split["archive_repo"] + ":" + split["collection"],
        "corpus_commit": split["archive_commit"],
        "manifest_sha256": split["manifest_sha256"],
        "split_sha256": hashlib.sha256(args.split.read_bytes()).hexdigest(),
        "train_slugs": train,
        "held_out_slugs": split["held_out_slugs"],
        "train_pages": pages,
        "total_characters": sum(counts.values()),
        "counts": dict(counts.most_common()),
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{pages} training pages, {len(counts)} distinct characters -> {args.out}")


if __name__ == "__main__":
    main()

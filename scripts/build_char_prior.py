#!/usr/bin/env python3
"""Build the decoder's character prior from a TRAINING split of an art corpus.

Counts every character in the training texts, spaces included, and writes
``data/aa_char_prior.json`` with the corpus identity, the slugs used, and the
slugs held out. The held-out slugs must never be counted: they are what the
decoder is scored on.

It also writes ``data/aa_bigram_prior.json``: counts of touching glyph pairs
(two adjacent non-space characters on one line), kept when seen at least
``BIGRAM_MIN_COUNT`` times. These are the multi-glyph stroke idioms of
ascii-art-authoring 15.5 (converter FL 2026-09-27 note, item 2).

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
BIGRAM_MIN_COUNT = 3
SPACES = " \u3000"


def build_mlt_prior(args: argparse.Namespace) -> None:
    """P0C-10 2026-10-01: the AA-003 prior covers 23,363 hand-saved pages; the
    AA-004 crawl's TRAIN partition has 905,073 entries on 10,559 pages. Count
    decoded art pieces (mlt_pairs.piece_text / is_art) from train_keys only.
    Held-out records are never opened. This prior is valid only for --mlt-split
    evaluation: AA-004 TRAIN folders are disjoint from AA-004 held-out, not
    from every AA-003 held-out piece."""
    import mlt_pairs

    archive = args.archive.resolve()
    split, rows = mlt_pairs.load_split(archive, args.mlt_split)
    counts: Counter[str] = Counter()
    pieces = pages = 0
    for key in split["train_keys"]:
        record = mlt_pairs.load_record_checked(archive, rows[key])
        pages += 1
        for entry in record["aa"]:
            text = mlt_pairs.piece_text(entry)
            if mlt_pairs.is_art(text):
                counts.update(ch for ch in text if ch not in "\r\n")
                pieces += 1
    out = args.out if args.out != REPO / "data/aa_char_prior.json" else REPO / "data/aa004_char_prior.json"
    out.write_text(json.dumps({
        "schema": "aa_char_prior.v1",
        "corpus": "ascii-art-archive:collections/aahub-mlt",
        "corpus_commit": split["archive_commit"],
        "index_sha256": split["index_sha256"],
        "mlt_split_sha256": hashlib.sha256(args.mlt_split.read_bytes()).hexdigest(),
        "train_pages": pages,
        "train_art_pieces": pieces,
        "total_characters": sum(counts.values()),
        "counts": dict(counts.most_common()),
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{pages} AA-004 training pages, {pieces} art pieces, {len(counts)} distinct characters -> {out}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("archive", type=Path, help="ascii-art-archive checkout")
    parser.add_argument("--split", type=Path, default=SPLIT)
    parser.add_argument("--out", type=Path, default=REPO / "data/aa_char_prior.json")
    parser.add_argument("--bigram-out", type=Path, default=REPO / "data/aa_bigram_prior.json")
    parser.add_argument("--mlt-split", type=Path, default=None,
                        help="count AA-004 TRAIN art pieces (data/aahub_mlt_split.json) instead of AA-003; "
                             "writes --out only (default data/aa004_char_prior.json), no bigram file")
    args = parser.parse_args()
    if args.mlt_split:
        build_mlt_prior(args)
        return

    split, jobs = load_split(args.archive, args.split)
    held_out = set(split["held_out_slugs"])
    train = [s for s in jobs if s not in held_out]
    counts: Counter[str] = Counter()
    pairs: Counter[str] = Counter()
    pages = 0
    paths = [stem + ".txt" for slug in train for stem in jobs[slug]]
    for _, blob in read_blobs(args.archive, split, paths):
        body = blob.decode("utf-8")
        counts.update(ch for ch in body if ch not in "\r\n")
        for line in body.splitlines():
            pairs.update(a + b for a, b in zip(line, line[1:]) if a not in SPACES and b not in SPACES)
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
    kept = {g: n for g, n in pairs.most_common() if n >= BIGRAM_MIN_COUNT}
    args.bigram_out.write_text(json.dumps({
        "schema": "aa_bigram_prior.v1",
        "corpus": split["archive_repo"] + ":" + split["collection"],
        "corpus_commit": split["archive_commit"],
        "manifest_sha256": split["manifest_sha256"],
        "split_sha256": hashlib.sha256(args.split.read_bytes()).hexdigest(),
        "train_pages": pages,
        "definition": "two adjacent non-space characters on one line (U+0020 and U+3000 are spaces)",
        "min_count": BIGRAM_MIN_COUNT,
        "total_pairs": sum(pairs.values()),
        "distinct_pairs": len(pairs),
        "counts": kept,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{pages} training pages, {len(counts)} distinct characters -> {args.out}")
    print(f"{sum(pairs.values())} touching pairs, {len(kept)} kept (n >= {BIGRAM_MIN_COUNT}) -> {args.bigram_out}")


if __name__ == "__main__":
    main()

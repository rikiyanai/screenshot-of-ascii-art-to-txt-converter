#!/usr/bin/env python3
"""Lock a train/held-out split over the AA-004 AAHub crawl (P0C-10, 2026-09-30).

Input: ascii-art-archive `collections/aahub-mlt/index.jsonl` and page records
(AA-004, one gzipped AAHub art record per MLT page). Output:
`data/aahub_mlt_split.json`, the partition owner for every later AA-004
measurement (converter evaluation, glyph-viewer corpus combos, style audits).

Rules, in order:
1. A page that is an AA-003 slug (matched by page title against the slug's
   manifest) keeps the AA-003 side from `data/aahub_split.json`, so AA-003
   results stay comparable. Ambiguous titles are resolved by content overlap.
2. Pages are grouped by folder (the record path without its last element), so
   one character or series does not straddle the partition. A folder holding
   an AA-003 held-out page is held out; else a folder holding an AA-003 train
   page is train.
3. Every other folder is held out when sha256(folder) / 2**256 < HELD_OUT_SHARE.
4. Held-out pieces whose whitespace-normalised text also occurs in a train
   page are counted as leakage and listed by (key, index), so evaluations can
   exclude them. Train is not altered.

The archive is read from Git blobs at the commit named on the command line,
never from the worktree, as for AA-003.
"""
from __future__ import annotations

import argparse
import glob
import gzip
import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HELD_OUT_SHARE = 0.30
OUT = REPO / "data" / "aahub_mlt_split.json"
AA003 = REPO / "data" / "aahub_split.json"


def blob(archive: Path, commit: str, path: str) -> bytes:
    return subprocess.run(["git", "-C", str(archive), "show", f"{commit}:{path}"],
                          check=True, capture_output=True).stdout


def norm(text: str) -> str:
    return re.sub(r"[\s　]+", "", text)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--commit", required=True, help="ascii-art-archive commit holding AA-004")
    args = parser.parse_args()
    archive = args.archive.resolve()

    index_bytes = blob(archive, args.commit, "collections/aahub-mlt/index.jsonl")
    pages = [json.loads(l) for l in index_bytes.decode("utf-8").splitlines() if l.strip()]
    records = {}
    for p in pages:
        records[p["key"]] = json.loads(gzip.decompress(blob(archive, args.commit, p["stored"])))
    folder = {p["key"]: "/".join((p["path"] or "").split("/")[:-1]) for p in pages}

    aa003 = json.loads(AA003.read_text(encoding="utf-8"))
    held_slugs = set(aa003["held_out_slugs"])
    by_name = defaultdict(list)
    for p in pages:
        by_name[p["name"]].append(p["key"])
    slug_key, unresolved = {}, []
    for manifest in sorted(glob.glob(str(archive / "collections" / "aahub" / "*" / "manifest.txt"))):
        slug = Path(manifest).parent.name
        text = blob(archive, aa003["archive_commit"], f"collections/aahub/{slug}/manifest.txt").decode("utf-8")
        title = next((l.split(":", 1)[1].strip() for l in text.splitlines() if l.startswith("title:")), "")
        name = title.split(" | ")[0].replace(" - AAHub", "").strip()
        keys = by_name.get(name, [])
        if len(keys) > 1:  # resolve by content: the page sharing most normalised lines with the slug
            slug_lines = set()
            for path in glob.glob(str(archive / "collections" / "aahub" / slug / "*.txt")):
                rel = str(Path(path).relative_to(archive))
                slug_lines |= {norm(l) for l in blob(archive, aa003["archive_commit"], rel).decode("utf-8").splitlines()
                               if len(norm(l)) >= 10}
            score = {k: sum(norm(l) in slug_lines for e in records[k]["aa"] for l in e["value"].splitlines()
                            if len(norm(l)) >= 10) for k in keys}
            keys = [max(score, key=score.get)] if max(score.values()) > 0 else []
        if len(keys) == 1:
            slug_key[slug] = keys[0]
        else:
            unresolved.append({"slug": slug, "title": name, "candidates": len(by_name.get(name, []))})

    side = {}
    for slug, key in slug_key.items():
        side[key] = "heldout" if slug in held_slugs else "train"
    folder_side = {}
    for key, s in side.items():
        f = folder[key]
        folder_side[f] = "heldout" if s == "heldout" or folder_side.get(f) == "heldout" else "train"
    for key in records:
        if key in side:
            continue
        f = folder[key]
        if f not in folder_side:
            h = int.from_bytes(hashlib.sha256(f.encode("utf-8")).digest(), "big") / 2**256
            folder_side[f] = "heldout" if h < HELD_OUT_SHARE else "train"
        side[key] = folder_side[f]

    train_text = set()
    for key, s in side.items():
        if s == "train":
            train_text |= {norm(e["value"]) for e in records[key]["aa"] if norm(e["value"])}
    leaks = [[key, i] for key, s in sorted(side.items()) if s == "heldout"
             for i, e in enumerate(records[key]["aa"]) if norm(e["value"]) and norm(e["value"]) in train_text]

    pieces = Counter()
    for key, s in side.items():
        pieces[s] += len(records[key]["aa"])
    out = {
        "schema": "aahub_mlt_split.v1",
        "archive_repo": "ascii-art-archive",
        "archive_commit": subprocess.run(["git", "-C", str(archive), "rev-parse", args.commit], check=True,
                                         capture_output=True, text=True).stdout.strip(),
        "index_sha256": hashlib.sha256(index_bytes).hexdigest(),
        "aa003_split_sha256": hashlib.sha256(AA003.read_bytes()).hexdigest(),
        "rules": {"unit": "MLT page", "group": "folder (record path minus last element)",
                  "aa003_pages": "keep AA-003 side", "folder_hash_held_out_share": HELD_OUT_SHARE,
                  "leakage": "held-out pieces whose whitespace-normalised text occurs in train"},
        "counts": {"pages": dict(Counter(side.values())), "pieces": dict(pieces),
                   "folders": dict(Counter(folder_side.values())), "aa003_slugs_mapped": len(slug_key),
                   "held_out_pieces_leaking": len(leaks)},
        "aa003_slug_to_key": dict(sorted(slug_key.items())),
        "aa003_unresolved": unresolved,
        "train_keys": sorted(k for k, s in side.items() if s == "train"),
        "held_out_keys": sorted(k for k, s in side.items() if s == "heldout"),
        "held_out_leaking_pieces": leaks,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out["counts"], ensure_ascii=False), "unresolved", unresolved)
    print(f"wrote {OUT.relative_to(REPO)} sha256 {hashlib.sha256(OUT.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    main()

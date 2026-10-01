#!/usr/bin/env python3
"""Text + render pairs from the AA-004 AAHub crawl (P0C-10, 2026-09-30).

AA-004 stores each AAHub MLT page as one gzipped art record (ascii-art-archive
`collections/aahub-mlt/`), not as txt+png pairs: 1.24 M PNGs (~12 GB) would not
fit the disk or the archive's Git tree. A pair is therefore derived:

  text  = the record's `aa[i].value` (already plain text)
  image = render_aahub(text): Saitamaar 16 px, 8 px pad, 17 px line pitch,
          first baseline at y = 22, width = widest row + 16, height =
          rows * 17 + 16, bilevel ("1"), black on white.

That render reproduces the AA-003 archive PNGs pixel for pixel (goraku/resK-72:
0 of 248,148 pixels differ; test `MltPairs` in tests/test_mlt_pairs.py).

`python3 scripts/mlt_pairs.py ARCHIVE OUT --partition train --every 1000`
writes a sample of pairs to OUT/<key>/aaNNNN.{txt,png} plus OUT/receipt.json,
for inspection or for tools that need files. The evaluator reads records
directly (`eval_corpus.py --mlt-split`) and never needs these files.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import html
import json
import math
import subprocess
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[1]
SPLIT = REPO / "data" / "aahub_mlt_split.json"
FONT_REL = "collections/aahub/Saitamaar.ttf"
SIZE_PX, PAD_PX, PITCH_PX, FIRST_BASELINE = 16, 8, 17, 22


@lru_cache(maxsize=2)
def _font(path: str) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, SIZE_PX)


def render_aahub(text: str, font_path: str | Path) -> Image.Image:
    lines = text.rstrip("\n").split("\n")
    font = _font(str(font_path))
    width = max(int(math.ceil(font.getlength(line))) for line in lines) + 2 * PAD_PX
    height = len(lines) * PITCH_PX + 2 * PAD_PX
    image = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(image)
    for i, line in enumerate(lines):
        draw.text((PAD_PX, FIRST_BASELINE + i * PITCH_PX), line, font=font, fill=0, anchor="ls")
    return image.point(lambda v: 255 if v >= 128 else 0).convert("1")


def git_blob(archive: Path, commit: str, path: str) -> bytes:
    return subprocess.run(["git", "-C", str(archive), "show", f"{commit}:{path}"],
                          check=True, capture_output=True).stdout


def load_split(archive: Path, split_path: Path = SPLIT) -> tuple[dict, dict[str, dict]]:
    """The split plus its index rows, verified against the archive commit it names."""
    split = json.loads(split_path.read_text(encoding="utf-8"))
    index = git_blob(archive, split["archive_commit"], "collections/aahub-mlt/index.jsonl")
    if hashlib.sha256(index).hexdigest() != split["index_sha256"]:
        raise SystemExit("AA-004 index does not match the split")
    rows = {r["key"]: r for r in map(json.loads, index.decode("utf-8").splitlines()) if r}
    return split, rows


def load_record(archive: Path, commit: str, row: dict) -> dict:
    return json.loads(gzip.decompress(git_blob(archive, commit, row["stored"])))


def load_record_checked(archive: Path, row: dict) -> dict:
    """Read the worktree file (fast) and refuse it unless its bytes hash to the
    index row the split pinned, so a drifted worktree cannot enter a receipt."""
    raw = gzip.decompress((archive / row["stored"]).read_bytes())
    if hashlib.sha256(raw).hexdigest() != row["raw_sha256"]:
        raise ValueError(f"AA-004 record {row['key']} does not match the pinned index")
    return json.loads(raw)


def piece_text(entry: dict) -> str:
    """The piece as AAHub's viewer shows it. 2026-10-01: ~3 % of AA-004 pieces
    store characters as numeric HTML references (&#8201; thin space, &#9617; ░,
    &#x2588; █ ...); the viewer decodes them, and AA-003's extracted text holds
    the decoded characters (no literal '&#' in 32,950 files). Raw values must
    not be rendered or scored as-is."""
    return html.unescape(entry["value"])


def is_art(text: str) -> bool:
    """Section headers are single short lines; a piece has at least two lines."""
    return text.strip("\n").count("\n") >= 1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("archive", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--partition", choices=("train", "heldout"), required=True)
    parser.add_argument("--every", type=int, default=1000, help="keep every k-th art piece of the partition")
    args = parser.parse_args()
    archive = args.archive.resolve()
    split, rows = load_split(archive)
    font = archive / FONT_REL
    keys = split["train_keys"] if args.partition == "train" else split["held_out_keys"]
    leaking = {(k, i) for k, i in split["held_out_leaking_pieces"]}
    args.out.mkdir(parents=True, exist_ok=False)
    n = written = 0
    for key in keys:
        record = load_record(archive, split["archive_commit"], rows[key])
        for i, entry in enumerate(record["aa"]):
            text = piece_text(entry)
            if not is_art(text) or (key, i) in leaking:
                continue
            if n % args.every == 0:
                folder = args.out / key
                folder.mkdir(exist_ok=True)
                (folder / f"aa{i:04d}.txt").write_text(text, encoding="utf-8")
                render_aahub(text, font).save(folder / f"aa{i:04d}.png")
                written += 1
            n += 1
    receipt = {"split_sha256": hashlib.sha256(SPLIT.read_bytes()).hexdigest(), "archive_commit": split["archive_commit"],
               "partition": args.partition, "every": args.every, "art_pieces_seen": n, "pairs_written": written,
               "font_sha256": hashlib.sha256(font.read_bytes()).hexdigest(),
               "render": {"size_px": SIZE_PX, "pad_px": PAD_PX, "pitch_px": PITCH_PX, "first_baseline": FIRST_BASELINE}}
    (args.out / "receipt.json").write_text(json.dumps(receipt, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()

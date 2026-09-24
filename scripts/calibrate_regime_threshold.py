#!/usr/bin/env python3
"""Calibrate the regime detector's threshold against a rendered population.

The detector decides whether one advance can describe an image. This script
builds the two populations it has to separate, by rendering the same canonical
art through monospaced and proportional faces, and reports the error rates at a
range of thresholds so the shipped value is a recorded choice rather than a
guess.

Two regimes of *proportional* art matter and they are not equally hard:

* CJK proportional (Osaka, MS PGothic) spans roughly a 4x advance range and
  separates trivially.
* Latin proportional (Helvetica, Geneva, DejaVu Sans) spans far less and
  overlaps the monospaced population in the tails.

Run it with the archived collection as the corpus:

    python3 scripts/calibrate_regime_threshold.py \
        --corpus ../asciicker-Y9-2/articles/2026-09-21-ascii-art-reference-batch-media/ascii-art-de-collection
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))

from recover_monospace_ascii import (  # noqa: E402
    detect_regime,
    dominant_background,
    ink_intensity,
    measure_lattice,
)

MONOSPACED_FACES = (
    ("DejaVuSansMono", "/Library/Fonts/DejaVuSansMono.ttf"),
    ("Menlo", "/System/Library/Fonts/Menlo.ttc"),
    ("Courier", "/System/Library/Fonts/Courier.ttc"),
)
PROPORTIONAL_FACES = (
    ("DejaVuSans", "/Library/Fonts/DejaVuSans.ttf"),
    ("Helvetica", "/System/Library/Fonts/Helvetica.ttc"),
    ("Geneva", "/System/Library/Fonts/Geneva.ttf"),
)
THRESHOLDS = (0.4, 0.5, 0.6, 0.75, 1.0, 1.25, 1.5, 2.0)


def harvest(corpus: Path, low: int = 6, high: int = 24, width: int = 78):
    """Every blank-line-delimited block of the corpus that fits a page."""
    pieces: list[tuple[str, list[str]]] = []
    for path in sorted(corpus.glob("*.txt")):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # advent_calendar99.txt is ISO-8859-1 and fails UTF-8 at byte 22469.
            text = path.read_text(encoding="latin-1")
        block: list[str] = []
        for line in text.split("\n"):
            line = line.replace("\t", "    ").replace("\xa0", " ").rstrip()
            if line.strip():
                block.append(line)
                continue
            if low <= len(block) <= high and max(len(x) for x in block) <= width:
                pieces.append((path.name, block))
            block = []
        if low <= len(block) <= high and max((len(x) for x in block), default=0) <= width:
            pieces.append((path.name, block))
    return pieces


def render(block: list[str], font_path: str, size: int, line_height: int, margin: int):
    font = ImageFont.truetype(font_path, size)
    width = int(max(font.getlength(line) for line in block)) + 2 * margin
    height = line_height * len(block) + 2 * margin
    image = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    for index, line in enumerate(block):
        draw.text((margin, margin + index * line_height), line, font=font, fill=(0, 0, 0))
    return image


def drift_of(image: Image.Image) -> float | None:
    array = np.asarray(image.convert("RGB"))
    ink = ink_intensity(array, dominant_background(array))
    verdict = detect_regime(ink, measure_lattice(ink), threshold_cells=1.0)
    return verdict.median_drift_cells


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--sample", type=int, default=30)
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument("--size", type=int, default=16)
    parser.add_argument("--line-height", type=int, default=22)
    parser.add_argument("--margin", type=int, default=12)
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args()

    pieces = harvest(args.corpus)
    random.seed(args.seed)
    selection = random.sample(pieces, min(args.sample, len(pieces)))
    print(f"corpus pieces {len(pieces)}, sampled {len(selection)}", file=sys.stderr)

    population: dict[str, list[float]] = {"monospaced": [], "proportional": []}
    by_face: dict[str, list[float]] = {}
    for kind, faces in (("monospaced", MONOSPACED_FACES), ("proportional", PROPORTIONAL_FACES)):
        for name, path in faces:
            if not Path(path).exists():
                print(f"skip missing face {name}", file=sys.stderr)
                continue
            drifts: list[float] = []
            for _, block in selection:
                value = drift_of(
                    render(block, path, args.size, args.line_height, args.margin)
                )
                if value is not None:
                    drifts.append(value)
            by_face[f"{kind}/{name}"] = drifts
            population[kind] += drifts
            print(
                f"{kind:12s} {name:16s} n={len(drifts):3d} "
                f"p50={statistics.median(drifts):6.3f} max={max(drifts):7.3f}",
                file=sys.stderr,
            )

    mono, prop = population["monospaced"], population["proportional"]
    rows = []
    for threshold in THRESHOLDS:
        refuse = sum(1 for v in mono if v > threshold) / len(mono)
        accept = sum(1 for v in prop if v <= threshold) / len(prop)
        rows.append(
            {
                "threshold_cells": threshold,
                "false_refusal_rate": round(refuse, 4),
                "false_acceptance_rate": round(accept, 4),
            }
        )
        print(
            f"threshold {threshold:4.2f} cells -> false refusal {refuse:6.1%}, "
            f"false acceptance {accept:6.1%}"
        )

    if args.json:
        args.json.write_text(
            json.dumps(
                {
                    "sampled_pieces": len(selection),
                    "seed": args.seed,
                    "render": {
                        "size_px": args.size,
                        "line_height_px": args.line_height,
                        "margin_px": args.margin,
                    },
                    "per_face_median_drift_cells": {
                        k: round(statistics.median(v), 4) for k, v in by_face.items() if v
                    },
                    "per_face_max_drift_cells": {
                        k: round(max(v), 4) for k, v in by_face.items() if v
                    },
                    "threshold_sweep": rows,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()

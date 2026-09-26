#!/usr/bin/env python3
"""Score deterministic fixed-grid recovery over the pinned ascii-art.de corpus.

This is deliberately a declared-geometry baseline. The corpus render contract
supplies its 8x19 cell, 8 px padding, baseline and font; this script tests the
classifier over every selected page without pretending that those values were
inferred from the pixels. The existing recovery CLI remains the blind geometry
benchmark.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import random
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from archive_snapshot import load_pair_corpus, read_blob, read_blobs  # noqa: E402
from score_against_key import score  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
LOCK = REPO / "data" / "ascii_art_de_corpus.json"


def declared_alphabet() -> str:
    """The render contract's printable byte repertoire plus box drawing.

    This is fixed independently of the answer keys, so the benchmark cannot
    learn its candidate alphabet from the pages it later scores.
    """
    cp1252 = bytes(range(32, 256)).decode("cp1252", errors="ignore")
    box = "".join(chr(codepoint) for codepoint in range(0x2500, 0x2580))
    return "".join(dict.fromkeys(cp1252 + box))


def render_templates(font_bytes: bytes, render: dict) -> tuple[dict[bytes, tuple[str, ...]], dict]:
    """Render a key-independent exact-raster lookup for the declared primary face."""
    size = int(render["font_size_px"])
    width = int(render["cell_advance_px"])
    height = int(render["line_step_px"])
    baseline = int(render["baseline_px_in_cell"])
    threshold = int(render["bilevel_threshold"])
    font = ImageFont.truetype(io.BytesIO(font_bytes), size)
    cmap = TTFont(io.BytesIO(font_bytes)).getBestCmap()
    by_raster: dict[bytes, list[str]] = {}
    unsupported: list[str] = []
    for character in declared_alphabet():
        if ord(character) not in cmap:
            unsupported.append(character)
            continue
        cell = Image.new("L", (width, height), 255)
        ImageDraw.Draw(cell).text((0, baseline), character, font=font, fill=0, anchor="ls")
        raster = (np.asarray(cell) < threshold).tobytes()
        by_raster.setdefault(raster, []).append(character)
    # Several printable code points (notably SPACE and NO-BREAK SPACE) have
    # the same zero-ink raster. Pixels cannot identify which was present. The
    # converter's fixed-grid contract treats a genuinely blank cell as ASCII
    # space instead of emitting an ambiguity marker for every layout cell.
    blank = np.zeros((height, width), dtype=bool).tobytes()
    blank_aliases = by_raster.get(blank, [])
    by_raster[blank] = [" "]
    return {key: tuple(value) for key, value in by_raster.items()}, {
        "declared_alphabet_size": len(declared_alphabet()),
        "primary_supported_characters": len(declared_alphabet()) - len(unsupported),
        "primary_unsupported_characters": [f"U+{ord(ch):04X}" for ch in unsupported],
        "distinct_primary_rasters": len(by_raster),
        "zero_ink_aliases_canonicalized_to_space": [
            f"U+{ord(ch):04X}" for ch in blank_aliases
        ],
    }


def randomize_outer_margins(
    image: np.ndarray, stem: str, render: dict, seed: str, maximum: int
) -> tuple[np.ndarray, dict[str, int]]:
    """Replace the archive's uniform pad with reproducible uneven margins."""
    pad = int(render["padding_px"])
    if image.shape[0] < 2 * pad or image.shape[1] < 2 * pad:
        raise ValueError("image is smaller than its declared padding")
    content = image[pad : image.shape[0] - pad, pad : image.shape[1] - pad]
    page_seed = int.from_bytes(hashlib.sha256(f"{seed}\0{stem}".encode()).digest()[:8], "big")
    generator = random.Random(page_seed)
    margins = {
        edge: generator.randint(0, maximum) for edge in ("top", "right", "bottom", "left")
    }
    canvas = np.full(
        (
            margins["top"] + content.shape[0] + margins["bottom"],
            margins["left"] + content.shape[1] + margins["right"],
        ),
        255,
        dtype=np.uint8,
    )
    canvas[
        margins["top"] : margins["top"] + content.shape[0],
        margins["left"] : margins["left"] + content.shape[1],
    ] = content
    return canvas, margins


def _cut_cells(ink: np.ndarray, y0: int, x0: int, height: int, width: int) -> np.ndarray:
    rows = (ink.shape[0] - y0) // height
    columns = (ink.shape[1] - x0) // width
    if rows < 1 or columns < 1:
        return np.empty((0, 0, height, width), dtype=bool)
    region = ink[y0 : y0 + rows * height, x0 : x0 + columns * width]
    return region.reshape(rows, height, columns, width).transpose(0, 2, 1, 3)


def fit_origin(
    ink: np.ndarray,
    templates: dict[bytes, tuple[str, ...]],
    height: int,
    width: int,
    sample_limit: int = 64,
) -> tuple[int, int, dict]:
    """Fit the unknown screenshot crop phase without using augmentation metadata."""
    best: tuple[tuple[int, int, int], int, int, dict] | None = None
    for y0 in range(min(height, ink.shape[0])):
        for x0 in range(min(width, ink.shape[1])):
            cells = _cut_cells(ink, y0, x0, height, width)
            if not cells.size:
                continue
            flat = cells.reshape(-1, height, width)
            weights = flat.sum(axis=(1, 2))
            candidates = np.flatnonzero(weights)
            if len(candidates) > sample_limit:
                # Even coverage is deterministic and avoids learning the phase
                # from just one dense corner of a large sheet.
                indices = np.linspace(0, len(candidates) - 1, sample_limit, dtype=int)
                candidates = candidates[indices]
            tally = Counter()
            for index in candidates:
                matches = templates.get(np.ascontiguousarray(flat[int(index)]).tobytes(), ())
                tally["resolved" if len(matches) == 1 else "ambiguous" if matches else "unmatched"] += 1
            ranking = (tally["unmatched"], tally["ambiguous"], -tally["resolved"])
            detail = {"sampled_ink_cells": len(candidates), **tally}
            if best is None or ranking < best[0]:
                best = ranking, y0, x0, detail
    if best is None:
        raise ValueError("image contains no complete candidate grid")
    return best[1], best[2], best[3]


def strip_outer_blank_cells(rows: list[str]) -> list[str]:
    """Remove screenshot border cells while preserving relative indentation."""
    while rows and not rows[0].strip(" "):
        rows.pop(0)
    while rows and not rows[-1].strip(" "):
        rows.pop()
    nonempty = [row for row in rows if row.strip(" ")]
    common = min((len(row) - len(row.lstrip(" ")) for row in nonempty), default=0)
    return [row[common:].rstrip() for row in rows]


def decode_page(
    png: bytes,
    stem: str,
    templates: dict[bytes, tuple[str, ...]],
    render: dict,
    margin_seed: str,
    max_outer_margin: int,
) -> tuple[list[str], dict]:
    width = int(render["cell_advance_px"])
    height = int(render["line_step_px"])
    threshold = int(render["bilevel_threshold"])
    image = np.asarray(Image.open(io.BytesIO(png)).convert("L"))
    pad = int(render["padding_px"])
    inner_height = image.shape[0] - 2 * pad
    inner_width = image.shape[1] - 2 * pad
    if inner_height < 0 or inner_width < 0 or inner_height % height or inner_width % width:
        raise ValueError(f"image violates declared geometry: {image.shape[1]}x{image.shape[0]}")
    expected_rows, expected_columns = inner_height // height, inner_width // width
    image, margins = randomize_outer_margins(
        image, stem, render, margin_seed, max_outer_margin
    )
    ink = image < threshold
    y0, x0, phase_fit = fit_origin(ink, templates, height, width)
    cells = _cut_cells(ink, y0, x0, height, width)
    rows, columns = cells.shape[:2]
    recovered: list[str] = []
    tally = Counter()
    for row in cells:
        characters: list[str] = []
        for cell in row:
            candidates = templates.get(np.ascontiguousarray(cell).tobytes(), ())
            if len(candidates) == 1:
                characters.append(candidates[0])
                tally["resolved"] += 1
            elif candidates:
                characters.append("?")
                tally["ambiguous"] += 1
            else:
                characters.append("?")
                tally["unmatched"] += 1
        recovered.append("".join(characters).rstrip())
    recovered = strip_outer_blank_cells(recovered)
    return recovered, {
        "rows": rows,
        "columns": columns,
        "expected_content_rows": expected_rows,
        "expected_content_columns": expected_columns,
        "outer_margins_px": margins,
        "fitted_origin_phase_px": {"x": x0, "y": y0},
        "actual_content_origin_phase_px": {
            "x": margins["left"] % width,
            "y": margins["top"] % height,
        },
        "phase_fit": phase_fit,
        **tally,
    }


def decode_key(body: bytes, encoding: str) -> list[str]:
    codec = "cp1252" if encoding == "cp1252" else "utf-8"
    return body.decode(codec).splitlines()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--lock", type=Path, default=LOCK)
    parser.add_argument("--every", type=int, default=1)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--margin-seed", default="p0c-10-fixed-grid-v1")
    parser.add_argument("--max-outer-margin-px", type=int, default=31)
    args = parser.parse_args()
    if (args.every < 1 or (args.limit is not None and args.limit < 1)
            or args.max_outer_margin_px < 0):
        parser.error("--every/--limit must be positive and --max-outer-margin-px nonnegative")
    if args.out.exists():
        parser.error("output path already exists")

    lock, all_stems = load_pair_corpus(args.archive, args.lock)
    stems = all_stems[:: args.every]
    if args.limit is not None:
        stems = stems[: args.limit]
    font_bytes = read_blob(args.archive, lock, lock["font_path"])
    templates, template_receipt = render_templates(font_bytes, lock["render"])

    started = time.time()
    paths = [path for stem in stems for path in (stem + ".txt", stem + ".png")]
    blobs = read_blobs(args.archive, lock, paths)
    pages: list[dict] = []
    totals = Counter()
    outside = Counter()
    alphabet = set(declared_alphabet())
    for stem in stems:
        text_path, text_body = next(blobs)
        png_path, png_body = next(blobs)
        if text_path != stem + ".txt" or png_path != stem + ".png":
            raise RuntimeError("batch blob order changed")
        key = decode_key(text_body, lock["_encodings"][text_path])
        recovered, cells = decode_page(
            png_body, stem, templates, lock["render"],
            args.margin_seed, args.max_outer_margin_px,
        )
        result = score(recovered, key)
        result.pop("per_row")
        key_characters = Counter("".join(key))
        missing = {character: count for character, count in key_characters.items() if character not in alphabet}
        outside.update(missing)
        totals.update({
            "rows": result["rows_key"],
            "exact_rows": result["exact_rows"],
            "indentation_exact_rows": result["exact_rows_indentation_invariant"],
            "row_count_match": int(result["rows_recovered"] == result["rows_key"]),
            "resolved_cells": cells.get("resolved", 0),
            "ambiguous_cells": cells.get("ambiguous", 0),
            "unmatched_cells": cells.get("unmatched", 0),
        })
        pages.append({
            "page": stem.removeprefix(lock["collection"] + "/") + ".png",
            **result,
            "grid": {"rows": cells["rows"], "columns": cells["columns"]},
            "outer_margins_px": cells["outer_margins_px"],
            "fitted_origin_phase_px": cells["fitted_origin_phase_px"],
            "actual_content_origin_phase_px": cells["actual_content_origin_phase_px"],
            "phase_fit": cells["phase_fit"],
            "resolved_cells": cells.get("resolved", 0),
            "ambiguous_cells": cells.get("ambiguous", 0),
            "unmatched_cells": cells.get("unmatched", 0),
            "key_characters_outside_declared_alphabet": sum(missing.values()),
        })

    mean_canonical = sum(page["canonical_cer"] for page in pages) / max(len(pages), 1)
    mean_strict = sum(page["strict_cer"] for page in pages) / max(len(pages), 1)
    summary = {
        "pages": len(pages),
        "rows": totals["rows"],
        "exact_rows": totals["exact_rows"],
        "exact_row_rate": round(totals["exact_rows"] / max(totals["rows"], 1), 4),
        "exact_rows_indentation_invariant": totals["indentation_exact_rows"],
        "row_count_match": totals["row_count_match"],
        "mean_canonical_cer": round(mean_canonical, 4),
        "mean_strict_cer": round(mean_strict, 4),
        "resolved_cells": totals["resolved_cells"],
        "ambiguous_cells": totals["ambiguous_cells"],
        "unmatched_cells": totals["unmatched_cells"],
        "key_characters_outside_declared_alphabet": sum(outside.values()),
        "seconds": round(time.time() - started, 1),
    }
    receipt = {
        "schema": "fixed_grid_corpus_eval.v1",
        "mode": "declared_geometry_and_font",
        "archive_commit": lock["archive_commit"],
        "manifest_sha256": lock["manifest_sha256"],
        "lock_sha256": hashlib.sha256(args.lock.read_bytes()).hexdigest(),
        "collection": lock["collection"],
        "corpus_pairs": len(all_stems),
        "every": args.every,
        "limit": args.limit,
        "render": lock["render"],
        "augmentation": {
            "method": "replace uniform archive pad with deterministic independent white margins",
            "seed": args.margin_seed,
            "range_px_inclusive": [0, args.max_outer_margin_px],
            "decoder_uses_generated_margins": False,
        },
        "font": {"path": lock["font_path"], "sha256": lock["font_sha256"]},
        "template_bank": template_receipt,
        "outside_alphabet": {f"U+{ord(ch):04X}": count for ch, count in outside.most_common()},
        "summary": summary,
        "pages": pages,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()

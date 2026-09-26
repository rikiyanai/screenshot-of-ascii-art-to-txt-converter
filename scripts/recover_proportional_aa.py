#!/usr/bin/env python3
"""Recover Shift_JIS-style proportional text art from a screenshot.

The fixed-grid recoverer refuses proportional art, because no single advance
describes it. This tool decodes it instead, under one explicit assumption: the
art was set in a known typeface (by default Saitamaar, the MS PGothic-metric
face that 2ch/5ch art viewers ship), and the font's own advance table gives the
pen positions a row is allowed to take.

Each row is decoded by dynamic programming over pen positions. A glyph placed at
pen x owns the pixel columns whose centres fall inside [x, x + advance); its
cost is the squared difference between the source and the glyph rendered at
that sub-pixel phase over those columns. The columns of a row are tiled exactly
once, so the path cost is the whole-row reconstruction error, and whitespace is
decided by the same score as ink: a blank run is filled by the cheapest legal
combination of U+3000 (ideographic) and U+0020 spaces whose advances land the
next glyph on its ink.

Conventions of the art form enter as constraints, not as guesses: two U+0020
in a row are illegal (HTML would collapse them), and a blank run is written in
one canonical order, because every order of the same spaces renders the same.

Everything fitted is reported in the receipt: size, line pitch, per-row
baseline, text-box origin, and the per-row reconstruction error.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import dataclass
from functools import reduce
from pathlib import Path

import numpy as np
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parent.parent
DEFAULT_FONT = REPO / "fonts" / "Saitamaar-Regular.ttf"

FULL_SPACE = "　"
HALF_SPACE = " "

SUPERSAMPLE = 8  # sub-pixel phases per pixel


def _ranges(*spans: tuple[int, int]) -> str:
    return "".join(chr(c) for lo, hi in spans for c in range(lo, hi + 1))


# The candidate alphabet. Wide enough for the art form (ASCII, full-width forms,
# both kana, half-width kana, the punctuation and CJK strokes that art is drawn
# with, and the Greek/Cyrillic letters faces are built from), narrow enough that
# the decoder is not choosing among ten thousand ideographs.
AA_ALPHABET = (
    _ranges((0x21, 0x7E))
    + "´¨°±×÷¦§¶·"
    + _ranges((0xFF01, 0xFF5E), (0xFF61, 0xFF9F))
    + _ranges((0x3001, 0x3003), (0x3005, 0x3015), (0x3041, 0x3096), (0x309B, 0x309E))
    + _ranges((0x30A1, 0x30FA), (0x30FC, 0x30FE))
    + _ranges((0x0391, 0x03A9), (0x03B1, 0x03C9), (0x0410, 0x044F))
    + "‐―‖‘’“”†‡‥…‰′″※‾∀∂∃∇∈∋∑−√∝∞∟∠∥∧∨∩∪∫∬∴∵∽≒≠≡≦≧≪≫⊂⊃⊆⊇⊥⌒"
    + "─│┌┐└┘├┤┬┴┼━┃┏┓┗┛┣┫┳┻╋"
    + "■□◆◇○◎●△▲▽▼★☆♀♂♪￣￤"
    + "丶丿乂亅亠人从个入八冂冖凵刀力勹匕匚十卜卩厂厶又口土士夕大女子宀寸小尢尸屮山川巛工己巾干幺广廴廾弋弓彡彳心戈手斤方日曰月木欠止歹殳毋比毛氏气水火爪父爻片牛犬王"
    + "从乙了云井亡凸凹"
)


@dataclass
class FontModel:
    path: Path
    units_per_em: int
    advances: dict[str, int]  # font units
    unit_step: int  # gcd of every advance: the pen lattice, in font units


def load_font_model(path: Path, alphabet: str) -> FontModel:
    font = TTFont(str(path))
    cmap = font.getBestCmap()
    metrics = font["hmtx"]
    advances: dict[str, int] = {}
    for character in dict.fromkeys(FULL_SPACE + HALF_SPACE + alphabet):
        glyph = cmap.get(ord(character))
        if glyph is None:
            continue
        advance = metrics[glyph][0]
        if advance > 0:
            advances[character] = advance
    step = reduce(math.gcd, advances.values())
    return FontModel(path, font["head"].unitsPerEm, advances, step)


@dataclass
class GlyphBank:
    """Every candidate rendered at every sub-pixel phase, clipped to its advance."""

    characters: list[str]
    size_px: float
    height: int
    baseline: int
    advance_px: np.ndarray  # (n,)
    advance_steps: np.ndarray  # (n,) advances in pen-lattice steps
    templates: np.ndarray  # (n, K, height, wmax), zero outside the owned columns
    widths: np.ndarray  # (n, K) number of owned columns
    energy: np.ndarray  # (n, K) sum of squared template ink
    step_px: float


def render_bank(model: FontModel, size_px: float, height: int, baseline: int) -> GlyphBank:
    k = SUPERSAMPLE
    font = ImageFont.truetype(str(model.path), size=max(1, round(size_px * k)))
    blank = np.zeros((height, 1))
    chars: list[str] = []
    rendered: list[list[np.ndarray]] = []
    widths: list[list[int]] = []
    seen: dict[tuple[int, bytes], str] = {}
    scale = size_px / model.units_per_em
    for character, advance_units in model.advances.items():
        advance = advance_units * scale
        phases: list[np.ndarray] = []
        owned: list[int] = []
        for phase in range(k):
            x_start = phase / k
            first = 0
            last = math.ceil(x_start + advance - 0.5)  # exclusive: centres j+0.5 < x+a
            columns = max(0, last - first)
            pad = 4
            canvas_w = (columns + 2 * pad + 4) * k
            canvas = Image.new("L", (canvas_w, height * k), 0)
            if character not in (FULL_SPACE, HALF_SPACE):
                ImageDraw.Draw(canvas).text(
                    (pad * k + phase, baseline * k), character, font=font, fill=255, anchor="ls"
                )
            small = np.asarray(
                canvas.resize((canvas_w // k, height), Image.BOX), dtype=np.float64
            ) / 255.0
            phases.append(small[:, pad : pad + columns] if columns else blank[:, :0])
            owned.append(columns)
        if character not in (FULL_SPACE, HALF_SPACE):
            if all(p.sum() == 0 for p in phases):
                continue  # no ink in this face: not a usable candidate
            key = (advance_units, np.round(phases[0], 2).tobytes())
            if key in seen:
                continue  # same shape at the same advance as an earlier candidate
            seen[key] = character
        chars.append(character)
        rendered.append(phases)
        widths.append(owned)
    wmax = max(max(w) for w in widths)
    templates = np.zeros((len(chars), k, height, wmax))
    for i, phases in enumerate(rendered):
        for p, t in enumerate(phases):
            templates[i, p, :, : t.shape[1]] = t
    advance_units = np.array([model.advances[c] for c in chars])
    return GlyphBank(
        characters=chars,
        size_px=size_px,
        height=height,
        baseline=baseline,
        advance_px=advance_units * scale,
        advance_steps=advance_units // model.unit_step,
        templates=templates,
        widths=np.array(widths),
        energy=(templates**2).sum(axis=(2, 3)),
        step_px=model.unit_step * scale,
    )


def ink_of(image: Image.Image) -> tuple[np.ndarray, np.ndarray]:
    rgb = np.asarray(image.convert("RGB"), dtype=np.float64)
    grey = rgb.mean(axis=2)
    values, counts = np.unique(grey.astype(np.int32), return_counts=True)
    background = float(values[np.argmax(counts)])
    ink = np.clip((background - grey) / max(background, 1.0), 0.0, 1.0)
    # Frame rules and panel tints are faint and flat; glyph ink is not. Anything
    # fainter than this is page chrome, never text, and must not be explained.
    ink[ink < 0.15] = 0.0
    return ink, grey


def container_left_edge(grey: np.ndarray) -> int | None:
    """Right side of a vertical rule (a text-box border) left of the art, if any."""
    ink_cols = np.nonzero((grey < 128).any(axis=0))[0]
    if ink_cols.size == 0:
        return None
    limit = int(ink_cols[0])
    background = np.median(grey)
    rule = [
        x
        for x in range(limit)
        if np.mean(np.abs(grey[:, x] - background) > 8) > 0.6
    ]
    return rule[-1] + 1 if rule else None


def row_strip(ink: np.ndarray, baseline_y: int, bank: GlyphBank) -> np.ndarray:
    top = baseline_y - bank.baseline
    strip = np.zeros((bank.height, ink.shape[1]))
    lo, hi = max(0, top), min(ink.shape[0], top + bank.height)
    if hi > lo:
        strip[lo - top : hi - top] = ink[lo:hi]
    return strip


def correlations(strip: np.ndarray, bank: GlyphBank) -> np.ndarray:
    """corr[col, i, phase] = sum(strip[:, col:col+w] * template[i, phase])."""
    n, k, h, wmax = bank.templates.shape
    padded = np.pad(strip, ((0, 0), (0, wmax)))
    windows = np.lib.stride_tricks.sliding_window_view(padded, wmax, axis=1)[:, : strip.shape[1]]
    windows = windows.transpose(1, 0, 2).reshape(strip.shape[1], h * wmax)
    flat = bank.templates.reshape(n * k, h * wmax)
    return (windows @ flat.T).reshape(strip.shape[1], n, k)


@dataclass
class RowDecode:
    text: str
    cost: float
    ink_energy: float
    end_px: float


def decode_row(
    strip: np.ndarray,
    corr: np.ndarray,
    bank: GlyphBank,
    x0: float,
    glyph_penalty: float,
) -> RowDecode:
    width = strip.shape[1]
    column_energy = (strip**2).sum(axis=0)
    cum = np.concatenate([[0.0], np.cumsum(column_energy)])
    total_ink = float(cum[-1])
    last_ink = int(np.nonzero(column_energy > 1e-9)[0][-1]) if total_ink > 0 else -1
    if last_ink < 0:
        return RowDecode("", 0.0, 0.0, x0)

    n = len(bank.characters)
    k = SUPERSAMPLE
    steps = bank.advance_steps
    states = int(math.ceil((width - x0) / bank.step_px)) + int(steps.max()) + 2
    half = bank.characters.index(HALF_SPACE)
    penalty = np.full(n, glyph_penalty)
    penalty[bank.characters.index(FULL_SPACE)] = glyph_penalty * 0.5
    penalty[half] = glyph_penalty * 0.5

    inf = np.inf
    # layer 0: previous glyph was not U+0020; layer 1: it was.
    best = np.full((2, states), inf)
    back = np.full((2, states, 2), -1, dtype=np.int64)  # (prev_state, glyph)
    best[0, 0] = 0.0
    idx = np.arange(n)
    out_layer = np.where(idx == half, 1, 0)
    for s in range(states):
        here = np.minimum(best[0, s], best[1, s])
        if not np.isfinite(here):
            continue
        pen = x0 + s * bank.step_px
        if pen > last_ink + 1:
            continue  # nothing left to explain; the row ends here
        col = int(math.floor(pen))
        phase = int(round((pen - col) * k))
        if phase == k:
            col, phase = col + 1, 0
        if col >= width:
            continue
        w = bank.widths[:, phase]
        end = np.minimum(col + w, width)
        window_energy = cum[end] - cum[col]
        cost = window_energy - 2.0 * corr[col, :, phase] + bank.energy[:, phase] + penalty
        targets = s + steps
        for layer in (0, 1):
            origin = best[layer, s]
            if not np.isfinite(origin):
                continue
            allowed = np.ones(n, dtype=bool)
            if layer == 1:
                allowed[half] = False
            total = origin + cost
            ok = np.nonzero(allowed & (targets < states))[0]
            if ok.size == 0:
                continue
            order = ok[np.argsort(-total[ok])]  # largest first: the smallest write wins
            cand = np.full((2, states), inf)
            pick = np.full((2, states), -1, dtype=np.int64)
            cand[out_layer[order], targets[order]] = total[order]
            pick[out_layer[order], targets[order]] = order
            better = cand < best
            best[better] = cand[better]
            back[better] = np.stack([np.full(better.sum(), s * 2 + layer), pick[better]], axis=1)

    # Terminate after the last ink, charging any ink the path never covered.
    finish = inf
    final = None
    for s in range(states):
        pen = x0 + s * bank.step_px
        if pen < last_ink - bank.advance_px.max():
            continue
        col = min(width, int(math.floor(pen)))
        tail = float(cum[-1] - cum[col])
        for layer in (0, 1):
            value = best[layer, s] + tail
            if value < finish:
                finish, final = value, (layer, s)
    glyphs: list[str] = []
    layer, s = final
    while s > 0:
        prev, g = back[layer, s]
        glyphs.append(bank.characters[g])
        s, layer = divmod(int(prev), 2)
    text = canonical_spacing("".join(reversed(glyphs))).rstrip(FULL_SPACE + HALF_SPACE)
    return RowDecode(text, float(finish), total_ink, x0 + final[1] * bank.step_px)


def canonical_spacing(text: str) -> str:
    """Rewrite every blank run in one order: surplus U+3000 first, then
    U+0020 alternating with U+3000, ending on U+0020 when it can. Every order
    of the same spaces renders identically; this picks the art form's usual one
    and never places two U+0020 side by side."""
    out: list[str] = []
    run: list[str] = []

    def flush() -> None:
        full, half = run.count(FULL_SPACE), run.count(HALF_SPACE)
        if half == 0:
            out.append(FULL_SPACE * full)
        elif half - 1 > full:
            out.append("".join(run))  # cannot separate every pair; keep the decoder's order
        else:
            between = half - 1
            out.append(FULL_SPACE * (full - between) + (HALF_SPACE + FULL_SPACE) * between + HALF_SPACE)
        run.clear()

    for character in text:
        if character in (FULL_SPACE, HALF_SPACE):
            run.append(character)
        else:
            if run:
                flush()
            out.append(character)
    if run:
        flush()
    return "".join(out)


def line_geometry(ink: np.ndarray, bank_height: int) -> tuple[float, list[int]]:
    """Line pitch from the autocorrelation of the row ink profile, and one
    bottom-of-ink anchor per line (refined later against the glyph bank)."""
    profile = ink.sum(axis=1)
    centred = profile - profile.mean()
    ac = np.correlate(centred, centred, mode="full")[len(profile) - 1 :]
    low, high = max(8, bank_height // 2), min(len(ac) - 1, bank_height * 3)
    lag = low + int(np.argmax(ac[low:high]))
    # refine to sub-pixel by parabola
    if 0 < lag < len(ac) - 1:
        a, b, c = ac[lag - 1], ac[lag], ac[lag + 1]
        denom = a - 2 * b + c
        pitch = lag + (0.5 * (a - c) / denom if denom else 0.0)
    else:
        pitch = float(lag)
    rows = np.nonzero(profile > 0)[0]
    first, last = int(rows[0]), int(rows[-1])
    count = int(math.floor((last - first) / pitch)) + 1
    return pitch, [first, last, count]


def fit_rows(ink: np.ndarray, bank: GlyphBank, pitch: float, first: int, last: int) -> list[int]:
    """Baselines on one global lattice, baseline_i = b0 + i * pitch.

    b0 is chosen by matching every line at once against the face's vertical
    ink profile, never by walking down from the first ink: a line holding only
    underscores puts its first ink at the baseline, not at the cap height, and
    a greedy walk anchored there merges lines.
    pixel of rounding."""
    profile = ink.sum(axis=1)
    face = bank.templates[:, 0].sum(axis=(0, 2))
    face = face / max(face.sum(), 1e-9)

    def match(baseline_y: int) -> float:
        top = baseline_y - bank.baseline
        seg = np.zeros(bank.height)
        lo, hi = max(0, top), min(len(profile), top + bank.height)
        if hi > lo:
            seg[lo - top : hi - top] = profile[lo:hi]
        return float(seg @ face)

    def lattice(b0: float) -> list[float]:
        # first line: the earliest whose box reaches the first ink
        start = b0 - math.floor((b0 - first) / pitch) * pitch
        while start - pitch + (bank.height - bank.baseline) >= first:
            start -= pitch
        ys = []
        y = start
        while y - bank.baseline <= last:
            if y + (bank.height - bank.baseline) >= first:
                ys.append(y)
            y += pitch
        return ys

    best_b0, best_score = float(first), -1.0
    for b0 in np.arange(first, first + pitch, 0.25):
        score = sum(match(int(round(y))) for y in lattice(b0))
        if score > best_score:
            best_b0, best_score = float(b0), score
    # No per-line refinement: a browser lays every line on the same pitch, and
    # letting each line chase its own ink profile measured worse (a line of
    # dots and a line of slashes have different profiles, not different
    # baselines).
    baselines = [int(round(y)) for y in lattice(best_b0)]
    # a lattice line with no ink in its box is not a row of the art
    return [b for b in baselines if match(b) > 0]


def decode_image(
    image: Image.Image,
    model: FontModel,
    size_px: float,
    glyph_penalty: float,
    x0: float | None = None,
) -> dict:
    ink, grey = ink_of(image)
    height = int(math.ceil(size_px * 1.25)) + 2
    baseline = int(round(size_px * 1.0))
    bank = render_bank(model, size_px, height, baseline)
    pitch, (first, last, _) = line_geometry(ink, height)
    baselines = fit_rows(ink, bank, pitch, first, last)
    strips = [row_strip(ink, b, bank) for b in baselines]
    corrs = [correlations(s, bank) for s in strips]

    edge = container_left_edge(grey)
    ink_cols = np.nonzero((ink > 0.5).any(axis=0))[0]
    full_px = model.advances[FULL_SPACE] * size_px / model.units_per_em
    if x0 is None:
        low = float(edge) if edge is not None else max(0.0, float(ink_cols[0]) - full_px)
        candidates = np.arange(low, low + full_px, 1.0 / SUPERSAMPLE)
        sample = [i for i, s in enumerate(strips) if s.sum() > 0][:: max(1, len(strips) // 6)]
        scores = []
        for candidate in candidates:
            scores.append(
                sum(decode_row(strips[i], corrs[i], bank, candidate, glyph_penalty).cost for i in sample)
            )
        # Shifting the origin by any legal run of spaces explains the ink
        # equally well, so the fit is a plateau, not a peak. Take the SMALLEST
        # origin on the plateau: text starts at the box edge unless ink says
        # otherwise.
        scores = np.array(scores)
        floor = scores.min()
        tolerance = max(1e-6, 1e-3 * floor)
        x0 = float(candidates[int(np.nonzero(scores <= floor + tolerance)[0][0])])
        x0_source = "container_rule" if edge is not None else "ink_minus_one_full_space"
    else:
        x0_source = "given"

    rows = [decode_row(s, c, bank, x0, glyph_penalty) for s, c in zip(strips, corrs)]
    return {
        "bank": bank,
        "pitch": pitch,
        "baselines": baselines,
        "x0": x0,
        "x0_source": x0_source,
        "container_edge": edge,
        "rows": rows,
    }


def render_text(lines: list[str], model: FontModel, size_px: float, pitch: float, x0: float,
                baselines: list[int], shape: tuple[int, int]) -> np.ndarray:
    k = SUPERSAMPLE
    font = ImageFont.truetype(str(model.path), size=max(1, round(size_px * k)))
    canvas = Image.new("L", (shape[1] * k, shape[0] * k), 0)
    draw = ImageDraw.Draw(canvas)
    for line, base in zip(lines, baselines):
        draw.text((x0 * k, base * k), line, font=font, fill=255, anchor="ls")
    return np.asarray(canvas.resize((shape[1], shape[0]), Image.BOX), dtype=np.float64) / 255.0


def display_path(path: Path) -> str:
    """Repository-relative when possible, so a receipt carries no home directory."""
    try:
        return str(path.resolve().relative_to(REPO))
    except ValueError:
        return path.name


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--font", type=Path, default=DEFAULT_FONT)
    parser.add_argument("--size-px", type=float, default=None,
                        help="font size in source pixels; fitted when omitted")
    parser.add_argument("--glyph-penalty", type=float, default=0.02)
    parser.add_argument("--x0", type=float, default=None, help="text-box origin in px; fitted when omitted")
    args = parser.parse_args()

    image = Image.open(args.source)
    model = load_font_model(args.font, AA_ALPHABET)

    if args.size_px is None:
        size_px, size_trace = fit_size(image, model, args.glyph_penalty)
    else:
        size_px, size_trace = args.size_px, []

    result = decode_image(image, model, size_px, args.glyph_penalty, args.x0)
    lines = [row.text for row in result["rows"]]
    # drop blank leading/trailing lines
    while lines and not lines[-1]:
        lines.pop()

    ink, _ = ink_of(image)
    recon = render_text(lines, model, size_px, result["pitch"], result["x0"], result["baselines"], ink.shape)
    a, b = ink > 0.35, recon > 0.35
    iou = float((a & b).sum() / max((a | b).sum(), 1))

    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "recovered.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    Image.fromarray((255 - recon * 255).astype(np.uint8)).save(args.output / "reconstruction.png")
    receipt = {
        "schema": "proportional_aa_recovery.v1",
        "acceptance_status": "experimental_unaccepted",
        "source": str(args.source),
        "source_sha256": sha256(args.source),
        "font": {"path": display_path(args.font), "sha256": sha256(args.font), "units_per_em": model.units_per_em,
                 "pen_lattice_units": model.unit_step},
        "size_px": size_px,
        "size_fit": size_trace,
        "line_pitch_px": round(result["pitch"], 4),
        "baselines_px": result["baselines"],
        "text_origin_x_px": result["x0"],
        "text_origin_source": result["x0_source"],
        "container_edge_px": result["container_edge"],
        "candidate_glyphs": len(result["bank"].characters),
        "glyph_penalty": args.glyph_penalty,
        "rows": [
            {"text": r.text, "reconstruction_cost": round(r.cost, 3), "ink_energy": round(r.ink_energy, 3)}
            for r in result["rows"]
        ],
        "reconstruction_ink_iou": round(iou, 4),
        "conventions": [
            "no two U+0020 adjacent (HTML collapse)",
            "blank runs written in canonical order: surplus U+3000, then U+0020/U+3000 alternating",
            "no trailing whitespace",
        ],
    }
    (args.output / "quality.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
                                              encoding="utf-8")
    print(f"size {size_px}px, pitch {result['pitch']:.3f}px, origin x {result['x0']:.3f} "
          f"({result['x0_source']}), {len(lines)} rows, reconstruction IoU {iou:.3f}")
    print(f"recovered text: {args.output / 'recovered.txt'}")


def fit_size(image: Image.Image, model: FontModel, glyph_penalty: float) -> tuple[float, list]:
    """Pick the size whose decode explains the ink best, per unit of ink, on a
    sample of rows. Coarse 1 px sweep, then 0.25 px around the best."""
    ink, grey = ink_of(image)

    def cost(size: float) -> float:
        height = int(math.ceil(size * 1.25)) + 2
        bank = render_bank(model, size, height, int(round(size)))
        pitch, (first, last, _) = line_geometry(ink, height)
        baselines = fit_rows(ink, bank, pitch, first, last)
        chosen = baselines[:: max(1, len(baselines) // 4)][:4]
        edge = container_left_edge(grey)
        ink_cols = np.nonzero((ink > 0.5).any(axis=0))[0]
        full_px = model.advances[FULL_SPACE] * size / model.units_per_em
        low = float(edge) if edge is not None else max(0.0, float(ink_cols[0]) - full_px)
        total = energy = 0.0
        for b in chosen:
            strip = row_strip(ink, b, bank)
            corr = correlations(strip, bank)
            best = min(decode_row(strip, corr, bank, x, glyph_penalty).cost
                       for x in np.arange(low, low + full_px, 0.5))
            total += best
            energy += float((strip**2).sum())
        return total / max(energy, 1e-9)

    trace = []
    for size in np.arange(12.0, 33.0, 1.0):
        trace.append((float(size), round(cost(size), 4)))
    centre = min(trace, key=lambda t: t[1])[0]
    for size in np.arange(centre - 0.75, centre + 0.76, 0.25):
        if all(abs(size - s) > 1e-6 for s, _ in trace):
            trace.append((float(size), round(cost(size), 4)))
    best = min(trace, key=lambda t: t[1])[0]
    return best, sorted(trace)


if __name__ == "__main__":
    main()

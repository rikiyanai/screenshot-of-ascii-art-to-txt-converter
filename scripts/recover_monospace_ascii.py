#!/usr/bin/env python3
"""Recover fixed-grid text from a raster of monospaced character art.

Nothing about the source is assumed. The lattice is measured from the image, the
typeface and its size are inferred from the image by fitting a library of
monospaced fonts to the measured cell, and every cell is decided by a recorded
score with a recorded margin. A cell is written only when its best candidate
beats the runner-up by that margin; otherwise it is ``?``.

Design notes, because the previous pipeline failed on each of these:

* No cell aspect is hard-coded. 1:1, 1:2 and 16:29 are all just fits.
* No reference font is declared. The font is a fitted parameter, reported in
  the receipt along with its residual, so a wrong fit is visible instead of
  silent.
* Blank output is a scored decision. A cell that matches the space template
  wins as a space; it is never a silently dropped cell.
* Coverage is measured against ink-bearing source cells, not against the
  tool's own output.
* The recovered text is rendered back at the measured lattice and compared with
  the source, so the receipt carries a ground-truth-free agreement figure.

Tesseract is retained behind ``--engine tesseract`` for comparison only. It is
not the default: it classifies against an unbounded prose alphabet with no
score, which is what produced letters and currency signs on line art.
"""

from __future__ import annotations

import argparse
import json
import math
import string
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


DEFAULT_ALPHABET = "".join(sorted(set(string.printable[:95]) - {"\x0b", "\x0c"}))

# Candidate faces, widest-net first. Any path that does not exist is skipped, so
# this list is a preference order and not a requirement.
DEFAULT_FONT_DIRS = (
    "/System/Library/Fonts",
    "/System/Library/Fonts/Supplemental",
    str(Path.home() / "Library/Fonts"),
    "/usr/share/fonts",
    "/usr/local/share/fonts",
)
MONOSPACE_HINTS = (
    "menlo",
    "monaco",
    "courier",
    "sfnsmono",
    "andale",
    "ptmono",
    "dejavusansmono",
    "liberationmono",
    "jetbrainsmono",
    "intelonemono",
    "firacode",
    "hack",
    "inconsolata",
    "sourcecodepro",
    "ubuntumono",
    "consola",
)
ITALIC_MARKERS = ("italic", "oblique")


# --------------------------------------------------------------------------
# lattice measurement
# --------------------------------------------------------------------------


@dataclass
class AxisFit:
    period: float
    phase: float
    boundary_ink_mean: float
    boundary_ink_max: float
    seed_period: int
    method: str


def dominant_background(image: np.ndarray) -> tuple[int, int, int]:
    colours, counts = np.unique(image[:, :, :3].reshape(-1, 3), axis=0, return_counts=True)
    return tuple(int(value) for value in colours[np.argmax(counts)])


def ink_intensity(image: np.ndarray, background: tuple[int, int, int]) -> np.ndarray:
    """Per-pixel ink weight in [0, 1]. Anti-aliased edges keep partial weight."""
    distance = np.max(np.abs(image[:, :, :3].astype(float) - np.asarray(background, dtype=float)), axis=2)
    scale = max(float(distance.max()), 1.0)
    return np.clip(distance / scale, 0.0, 1.0)


def autocorrelation_seed(profile: np.ndarray, low: int, high: int) -> int:
    centred = profile.astype(float) - profile.mean()
    best_lag, best_score = low, -math.inf
    for lag in range(low, min(high, len(centred) - 1) + 1):
        score = float(np.dot(centred[:-lag], centred[lag:])) / (len(centred) - lag)
        if score > best_score:
            best_lag, best_score = lag, score
    return best_lag


def _boundary_cost(profile: np.ndarray, period: float, phase: float) -> tuple[float, float]:
    """Mean and max ink lying on the cut lines of a lattice."""
    if period <= 1:
        return math.inf, math.inf
    extent = len(profile)
    cuts = np.arange(phase, extent - 0.5, period)
    if len(cuts) < 3:
        return math.inf, math.inf
    # Sample the profile with linear interpolation so sub-pixel phases are real.
    values = np.interp(cuts, np.arange(extent), profile)
    return float(values.mean()), float(values.max())


def _best_phase(profile: np.ndarray, period: float, step: float) -> tuple[float, float, float]:
    best = (math.inf, 0.0, math.inf)
    for phase in np.arange(0.0, period, step):
        mean, peak = _boundary_cost(profile, period, float(phase))
        if mean < best[0]:
            best = (mean, float(phase), peak)
    return best


def _refine(profile: np.ndarray, centre: float, span: float, low: float) -> tuple[float, float, float, float]:
    best = (math.inf, centre, 0.0, math.inf)
    for period in np.arange(max(low, 2.0, centre - span), centre + span, 0.01):
        mean, phase, peak = _best_phase(profile, float(period), 0.05)
        if mean < best[0]:
            best = (mean, float(period), phase, peak)
    return best


def spectral_period(profile: np.ndarray, low: float, high: float, step: float = 0.02) -> float:
    """Period by projection onto a complex exponential.

    This is the estimator that survives connected strokes. Boundary-ink
    minimisation assumes the typeface leaves a gutter between cells, and a row
    of underscores or dashes renders as one continuous rule that crosses every
    boundary — on such a sheet no lattice is "legal" at any period and the
    search runs away to a multiple of the truth.
    """
    centred = profile.astype(float) - profile.mean()
    index = np.arange(len(profile))
    best_period, best_magnitude = low, -math.inf
    for period in np.arange(low, high, step):
        magnitude = abs(complex(np.dot(centred, np.exp(-2j * np.pi * index / period))))
        if magnitude > best_magnitude:
            best_period, best_magnitude = float(period), magnitude
    return best_period


def autocorrelation_fundamental(
    profile: np.ndarray, low: int, high: int, near_max: float = 0.8
) -> int | None:
    """The line pitch, as the largest near-maximal autocorrelation peak.

    Row axes carry only a handful of cycles, so a single spectral component
    matches the block envelope rather than the pitch, and tall glyphs put a
    strong peak at their own internal structure — 12px of stroke inside a 29px
    cell, for instance. Both of those artefacts sit at *shorter* lags than the
    pitch, while true multiples of the pitch sit at longer lags and decay. So
    among the peaks that come close to the maximum, the largest lag is the
    fundamental.
    """
    centred = profile.astype(float) - profile.mean()
    upper = min(high, len(centred) - 1)
    if upper <= low:
        return None
    lags = np.arange(low, upper + 1)
    scores = np.array([float(np.dot(centred[:-lag], centred[lag:])) / (len(centred) - lag) for lag in lags])
    if scores.max() <= 0:
        return None
    normalised = scores / scores.max()
    peaks = [
        int(lags[index])
        for index in range(1, len(normalised) - 1)
        if normalised[index] > normalised[index - 1]
        and normalised[index] >= normalised[index + 1]
        and normalised[index] >= near_max
    ]
    return max(peaks) if peaks else None


def band_pitch(profile: np.ndarray, threshold_fraction: float = 0.08) -> float | None:
    """Pitch from the spacing of ink bands, for axes with too few periods.

    A sheet of six text rows does not carry enough cycles for a spectral
    estimate: the strongest component ends up matching the envelope of the
    block, not the line pitch. The bands themselves are unambiguous, so fit a
    straight line through their leading edges instead.
    """
    threshold = threshold_fraction * float(profile.max()) if profile.max() > 0 else 0.0
    inked = profile > threshold
    starts: list[int] = []
    for index in range(len(inked)):
        if inked[index] and (index == 0 or not inked[index - 1]):
            starts.append(index)
    if len(starts) < 3:
        return None
    positions = np.asarray(starts, dtype=float)
    order = np.arange(len(positions), dtype=float)
    slope, _ = np.polyfit(order, positions, 1)
    if slope <= 1.0:
        return None
    # Reject a fit whose residuals say the bands are not evenly spaced, which
    # happens when a blank line splits the block.
    predicted = np.polyval(np.polyfit(order, positions, 1), order)
    if float(np.abs(predicted - positions).max()) > slope * 0.45:
        return None
    return float(slope)


def fit_axis_periodic(
    profile: np.ndarray, low: int, high: int, prefer_bands: bool
) -> AxisFit:
    """Estimate the period, then place the phase where it carries least ink."""
    upper = min(float(high), max(float(low) + 1.0, len(profile) / 2.0))
    period = None
    method = ""
    if prefer_bands:
        candidate = band_pitch(profile)
        if candidate is not None and low <= candidate <= upper:
            period = candidate
            method = "ink-band pitch, least squares over band leading edges"
        else:
            peak = autocorrelation_fundamental(profile, low, int(upper))
            if peak is not None:
                period = float(peak)
                method = "largest near-maximal autocorrelation peak"
    if period is None:
        period = spectral_period(profile, float(low), upper)
        method = "spectral projection onto a complex exponential"

    # Sub-pixel refinement, held inside a window around the estimate so the
    # refinement cannot wander to a different multiple.
    refined = spectral_period(
        profile, max(float(low), period - 0.6), min(upper, period + 0.6), 0.01
    )
    if abs(refined - period) > 0.6:
        refined = period

    mean, phase, peak = _best_phase(profile, refined, 0.05)
    return AxisFit(
        period=refined,
        phase=phase,
        boundary_ink_mean=mean,
        boundary_ink_max=peak,
        seed_period=autocorrelation_seed(profile, low, high),
        method=method + "; phase by minimum boundary ink",
    )


def fit_axis(profile: np.ndarray, low: int, high: int, legal_fraction: float = 0.08) -> AxisFit:
    """Find the finest legal lattice: the one whose cut lines stay in the gutters.

    Boundary ink is the cost. A plain global minimum is not enough, because a
    lattice of twice the true period keeps every one of its cuts in a gutter and
    scores at least as well — on this corpus the double scores *better*, since it
    uses half as many cuts.

    So the search descends: take the global minimum, then keep halving (and
    thirding) as long as the submultiple is still legal. Legality is absolute,
    not a ratio: a lattice is legal when the mean ink on its cuts is under
    `legal_fraction` of the profile's mean ink. Ratios fail here because a clean
    lattice can score exactly zero, and nothing is within a factor of zero.

    The cliff is wide in practice. On the bundled sample the true period costs
    under 1 per cent of mean ink and the next split costs about 60 per cent, so
    the rule is not sitting on a knife edge.
    """
    seed = autocorrelation_seed(profile, low, high)
    upper = min(float(high), len(profile) / 3.0)
    legal_ceiling = legal_fraction * max(float(profile.mean()), 1e-6)

    coarse: list[tuple[float, float, float, float]] = []
    for period in np.arange(max(float(low), 2.0), upper + 0.001, 0.05):
        mean, phase, peak = _best_phase(profile, float(period), 0.25)
        coarse.append((mean, float(period), phase, peak))
    coarse.sort()

    mean, period, phase, peak = _refine(profile, coarse[0][1], 0.20, float(low))

    descended = True
    while descended:
        descended = False
        for divisor in (2, 3):
            candidate = period / divisor
            if candidate < max(float(low), 2.0):
                continue
            sub_mean, sub_period, sub_phase, sub_peak = _refine(
                profile, candidate, 0.25, float(low)
            )
            if sub_mean <= legal_ceiling:
                mean, period, phase, peak = sub_mean, sub_period, sub_phase, sub_peak
                descended = True
                break

    return AxisFit(
        period=period,
        phase=phase,
        boundary_ink_mean=mean,
        boundary_ink_max=peak,
        seed_period=seed,
        method=f"boundary-ink minimisation, descended to finest lattice under {legal_fraction} of mean ink",
    )


@dataclass
class Lattice:
    origin_x: float
    origin_y: float
    advance_x: float
    advance_y: float
    columns: int
    rows: int
    x_fit: AxisFit
    y_fit: AxisFit

    def cell_bounds(self, row: int, column: int) -> tuple[float, float, float, float]:
        x0 = self.origin_x + column * self.advance_x
        y0 = self.origin_y + row * self.advance_y
        return x0, y0, x0 + self.advance_x, y0 + self.advance_y


def measure_lattice(ink: np.ndarray) -> Lattice:
    column_profile = ink.sum(axis=0)
    row_profile = ink.sum(axis=1)
    # Columns carry many cycles, so the spectral estimate is well conditioned.
    # Rows usually do not — a sheet has tens of columns but only a handful of
    # lines — so the row pitch comes from the ink bands when they are clean.
    x_fit = fit_axis_periodic(column_profile, 4, 40, prefer_bands=False)
    y_fit = fit_axis_periodic(row_profile, 6, 60, prefer_bands=True)

    height, width = ink.shape
    # Anchor the lattice at or before the first ink so no ink falls outside it.
    origin_x = x_fit.phase - math.ceil(x_fit.phase / x_fit.period) * x_fit.period
    origin_y = y_fit.phase - math.ceil(y_fit.phase / y_fit.period) * y_fit.period
    columns = int(math.ceil((width - origin_x) / x_fit.period))
    rows = int(math.ceil((height - origin_y) / y_fit.period))
    return Lattice(origin_x, origin_y, x_fit.period, y_fit.period, columns, rows, x_fit, y_fit)


def cut_cells(ink: np.ndarray, lattice: Lattice) -> tuple[np.ndarray, tuple[int, int]]:
    """Resample every cell onto one common integer raster."""
    cell_h = max(4, int(round(lattice.advance_y)))
    cell_w = max(3, int(round(lattice.advance_x)))
    height, width = ink.shape
    cells = np.zeros((lattice.rows, lattice.columns, cell_h, cell_w), dtype=np.float32)
    ys = np.arange(height)
    xs = np.arange(width)
    for row in range(lattice.rows):
        y0 = lattice.origin_y + row * lattice.advance_y
        sample_y = y0 + (np.arange(cell_h) + 0.5) * (lattice.advance_y / cell_h)
        band = np.empty((cell_h, width), dtype=np.float32)
        for index, y in enumerate(sample_y):
            if y < 0 or y >= height:
                band[index] = 0.0
            else:
                band[index] = np.interp(xs, xs, ink[int(min(max(y, 0), height - 1))])
        for column in range(lattice.columns):
            x0 = lattice.origin_x + column * lattice.advance_x
            sample_x = x0 + (np.arange(cell_w) + 0.5) * (lattice.advance_x / cell_w)
            patch = np.empty((cell_h, cell_w), dtype=np.float32)
            for index, x in enumerate(sample_x):
                if x < 0 or x >= width:
                    patch[:, index] = 0.0
                else:
                    patch[:, index] = band[:, int(min(max(x, 0), width - 1))]
            cells[row, column] = patch
    return cells, (cell_h, cell_w)


# --------------------------------------------------------------------------
# typeface inference
# --------------------------------------------------------------------------


def family_key(path: Path) -> str:
    """Collapse packaging variants of one face onto a single key.

    A system font directory carries the same outlines a dozen times over
    (NerdFont, NerdFontMono, NerdFontPropo, NL, and so on). Fitting each one
    costs the same as fitting a genuinely different face and teaches nothing,
    because their residuals come out identical.
    """
    name = path.stem.lower()
    for token in ("nerdfontpropo", "nerdfontmono", "nerdfont", "propo", "nl", "mono", "regular", "book"):
        name = name.replace(token, "")
    return "".join(character for character in name if character.isalnum())


def discover_fonts(
    explicit: list[Path] | None,
    font_dirs: tuple[str, ...],
    limit: int = 14,
) -> list[Path]:
    if explicit:
        return [path for path in explicit if path.exists()]
    by_family: dict[str, Path] = {}
    for directory in font_dirs:
        base = Path(directory)
        if not base.is_dir():
            continue
        for path in sorted(base.iterdir()):
            name = path.name.lower()
            if path.suffix.lower() not in {".ttf", ".ttc", ".otf"}:
                continue
            if any(marker in name for marker in ITALIC_MARKERS):
                continue
            flattened = name.replace(" ", "").replace("-", "")
            if not any(hint in flattened for hint in MONOSPACE_HINTS):
                continue
            key = family_key(path)
            if key not in by_family:
                by_family[key] = path
    return list(by_family.values())[:limit]


def sizes_for_advance(font_path: Path, target_advance: float, tolerance: float = 0.18) -> list[int]:
    """Pick the point sizes whose advance width matches the measured cell."""
    matches: list[int] = []
    for size in range(4, 80):
        try:
            font = ImageFont.truetype(str(font_path), size)
        except Exception:
            return matches
        try:
            advance = font.getlength("M")
        except Exception:
            continue
        if advance <= 0:
            continue
        if abs(advance - target_advance) / target_advance <= tolerance:
            matches.append(size)
    return matches


SUBPIXEL_OFFSETS = (-0.5, 0.0, 0.5)


def render_alphabet(
    font_path: Path,
    size: int,
    alphabet: str,
    cell: tuple[int, int],
    pad_x: int,
    pad_y: int,
) -> np.ndarray | None:
    """Rasterise every candidate at every sub-pixel offset.

    The measured period is almost never an integer, so successive cells carry
    their glyph at a different fractional offset. On a twelve-pixel cell with
    one-pixel strokes, half a pixel of misalignment is the difference between a
    match and a miss, which is why a single integer-aligned template set cannot
    read the right-hand half of a row.

    Shape: (variant, character, height, width), still padded.
    """
    cell_h, cell_w = cell
    try:
        font = ImageFont.truetype(str(font_path), size)
    except Exception:
        return None
    # The baseline sits a full cell height down the canvas, so a window of one
    # cell can be placed anywhere from "baseline at the window's bottom edge" to
    # "baseline at its top edge" without ever running off the top. Half a cell of
    # headroom is not enough: the window that actually aligns the glyph then
    # starts at a negative index, gets skipped, and every surviving window is
    # misaligned — at which point a blank template beats every real one, because
    # missing the glyph costs less than hitting it in the wrong place.
    canvas_h = cell_h + 2 * pad_y
    canvas_w = cell_w + 2 * pad_x
    variants = [(ox, oy) for oy in SUBPIXEL_OFFSETS for ox in SUBPIXEL_OFFSETS]
    stack = np.zeros((len(variants), len(alphabet), canvas_h, canvas_w), dtype=np.float32)
    for variant_index, (offset_x, offset_y) in enumerate(variants):
        for index, character in enumerate(alphabet):
            image = Image.new("L", (canvas_w, canvas_h), 0)
            draw = ImageDraw.Draw(image)
            try:
                draw.text(
                    (pad_x + offset_x, pad_y + offset_y),
                    character,
                    fill=255,
                    font=font,
                    anchor="ls",
                )
            except Exception:
                try:
                    draw.text(
                        (pad_x + offset_x, pad_y + offset_y), character, fill=255, font=font
                    )
                except Exception:
                    return None
            stack[variant_index, index] = np.asarray(image, dtype=np.float32) / 255.0
    return stack


@dataclass
class FontFit:
    font: str
    size: int
    offset_x: int
    offset_y: int
    residual: float
    advance_px: float


def fit_typeface(
    cells: np.ndarray,
    cell: tuple[int, int],
    alphabet: str,
    fonts: list[Path],
    advance_x: float,
    ink_floor: float,
    sample_limit: int,
) -> tuple[FontFit | None, np.ndarray | None, list[dict]]:
    """Choose the (font, size, offset) whose templates explain the image best."""
    cell_h, cell_w = cell
    flat = cells.reshape(-1, cell_h, cell_w)
    weights = flat.sum(axis=(1, 2))
    inked = np.argsort(weights)[::-1]
    inked = [index for index in inked if weights[index] >= ink_floor]
    if not inked:
        return None, None, []
    sample = np.asarray(flat[inked[:sample_limit]], dtype=np.float32)

    pad_x = max(4, cell_w // 2)
    pad_y = cell_h
    centre_variant = len(SUBPIXEL_OFFSETS) * (len(SUBPIXEL_OFFSETS) // 2) + len(SUBPIXEL_OFFSETS) // 2
    best: tuple[float, FontFit, np.ndarray] | None = None
    trials: list[dict] = []
    for font_path in fonts:
        for size in sizes_for_advance(font_path, advance_x):
            stack = render_alphabet(font_path, size, alphabet, cell, pad_x, pad_y)
            if stack is None:
                continue
            try:
                advance = float(ImageFont.truetype(str(font_path), size).getlength("M"))
            except Exception:
                advance = float("nan")
            # Baseline anywhere from the cell's top edge to its bottom edge.
            for offset_y in range(pad_y, pad_y + cell_h + 1):
                for offset_x in range(pad_x - 3, pad_x + 4):
                    window = stack[:, :, offset_y - cell_h : offset_y, offset_x : offset_x + cell_w]
                    if window.shape[2:] != (cell_h, cell_w):
                        continue
                    # Search the font, size and integer offset using the
                    # centre variant only. The sub-pixel variants multiply this
                    # loop by nine and cannot change which typeface wins.
                    centre = np.ascontiguousarray(window[centre_variant])
                    distance = np.abs(sample[:, None, :, :] - centre[None, :, :, :]).sum(axis=(2, 3))
                    residual = float(distance.min(axis=1).mean())
                    trials.append(
                        {
                            "font": font_path.name,
                            "size": size,
                            "offset_x": offset_x - pad_x,
                            "offset_y": offset_y - pad_y,
                            "residual": residual,
                        }
                    )
                    if best is None or residual < best[0]:
                        fit = FontFit(
                            font=str(font_path),
                            size=size,
                            offset_x=offset_x - pad_x,
                            offset_y=offset_y - pad_y,
                            residual=residual,
                            advance_px=advance,
                        )
                        # Keep every sub-pixel variant of the winning window for
                        # classification.
                        best = (residual, fit, np.ascontiguousarray(window))
    if best is None:
        return None, None, trials
    trials.sort(key=lambda row: row["residual"])
    return best[1], best[2], trials[:12]


# --------------------------------------------------------------------------
# classification
# --------------------------------------------------------------------------


@dataclass
class CellDecision:
    row: int
    column: int
    glyph: str
    best: float
    runner_up: float
    margin: float
    ink: float
    state: str
    variant: int


def classify(
    cells: np.ndarray,
    templates: np.ndarray,
    alphabet: str,
    ink_floor: float,
    margin: float,
) -> tuple[list[list[str]], list[CellDecision], dict[str, int], list[list[int]]]:
    rows, columns = cells.shape[0], cells.shape[1]
    grid = [[" " for _ in range(columns)] for _ in range(rows)]
    placement = [[0 for _ in range(columns)] for _ in range(rows)]
    decisions: list[CellDecision] = []
    tally = {"blank": 0, "resolved": 0, "ambiguous": 0}
    space_index = alphabet.index(" ") if " " in alphabet else None

    for row in range(rows):
        for column in range(columns):
            patch = cells[row, column]
            ink = float(patch.sum())
            # Best sub-pixel placement per character, then rank characters. The
            # margin must separate two different characters, never two
            # placements of the same one.
            per_variant = np.abs(patch[None, None, :, :] - templates).sum(axis=(2, 3))
            distance = per_variant.min(axis=0)
            variant_of = per_variant.argmin(axis=0)
            order = np.argsort(distance)
            best_index = int(order[0])
            best = float(distance[best_index])
            runner = float(distance[int(order[1])]) if len(order) > 1 else math.inf
            gap = runner - best
            glyph = alphabet[best_index]

            if ink < ink_floor:
                # Below the ink floor nothing is there to classify.
                state = "blank"
                grid[row][column] = " "
                tally["blank"] += 1
            elif space_index is not None and best_index == space_index:
                # A scored space: the blank template genuinely won.
                state = "resolved-space"
                grid[row][column] = " "
                tally["resolved"] += 1
            elif gap >= margin:
                state = "resolved"
                grid[row][column] = glyph
                tally["resolved"] += 1
            else:
                state = "ambiguous"
                grid[row][column] = "?"
                tally["ambiguous"] += 1

            chosen_variant = int(variant_of[best_index])
            placement[row][column] = chosen_variant
            if ink >= ink_floor:
                decisions.append(
                    CellDecision(
                        row, column, glyph, best, runner, gap, ink, state, chosen_variant
                    )
                )
    return grid, decisions, tally, placement


def learn_empirical_templates(
    cells: np.ndarray,
    templates: np.ndarray,
    decisions: list[CellDecision],
    alphabet: str,
    minimum_exemplars: int,
    margin_quantile: float,
) -> tuple[np.ndarray, dict[str, int]]:
    """Rebuild templates from the image's own cells.

    The synthetic templates come from whatever installed face fits best, and on
    a source whose typeface is not installed that face is only an approximation
    — which is exactly where the surviving errors live, as `=` read for `-` or
    `#` read for `=`. But the source contains many instances of each character,
    and they are identical to each other by construction. So the confidently
    read cells of a character are a better template for that character than any
    substitute font's rendering of it.

    Only the cells that won by a wide margin are used, because bootstrapping
    from uncertain reads would entrench them. The caller keeps this pass only
    if it improves agreement with the source.
    """
    cell_h, cell_w = cells.shape[2], cells.shape[3]
    confident = [d for d in decisions if d.state in {"resolved", "resolved-space"}]
    if not confident:
        return templates, {}
    cutoff = float(np.quantile([d.margin for d in confident], margin_quantile))

    grouped: dict[str, list[np.ndarray]] = {}
    for decision in confident:
        if decision.margin < cutoff:
            continue
        grouped.setdefault(decision.glyph, []).append(cells[decision.row, decision.column])

    learned = templates.copy()
    counts: dict[str, int] = {}
    for glyph, patches in grouped.items():
        if len(patches) < minimum_exemplars or glyph not in alphabet:
            continue
        index = alphabet.index(glyph)
        average = np.mean(np.stack(patches), axis=0).astype(np.float32)
        # One empirical template replaces every sub-pixel variant: the exemplars
        # already come from the measured lattice, so they carry the source's own
        # placement.
        learned[:, index] = average
        counts[glyph] = len(patches)
    return learned, counts


def render_reconstruction(
    grid: list[list[str]],
    templates: np.ndarray,
    alphabet: str,
    cell: tuple[int, int],
    placement: list[list[int]],
) -> np.ndarray:
    cell_h, cell_w = cell
    rows, columns = len(grid), len(grid[0])
    canvas = np.zeros((rows * cell_h, columns * cell_w), dtype=np.float32)
    index_of = {character: index for index, character in enumerate(alphabet)}
    for row in range(rows):
        for column in range(columns):
            character = grid[row][column]
            if character == "?":
                continue
            index = index_of.get(character)
            if index is None:
                continue
            canvas[
                row * cell_h : (row + 1) * cell_h, column * cell_w : (column + 1) * cell_w
            ] = templates[placement[row][column], index]
    return canvas


def agreement(reconstruction: np.ndarray, cells: np.ndarray) -> dict[str, float]:
    rows, columns, cell_h, cell_w = cells.shape
    source = cells.transpose(0, 2, 1, 3).reshape(rows * cell_h, columns * cell_w)
    a = source > 0.35
    b = reconstruction > 0.35
    union = int(np.logical_or(a, b).sum())
    intersection = int(np.logical_and(a, b).sum())
    return {
        "ink_intersection_over_union": (intersection / union) if union else None,
        "source_ink_px": int(a.sum()),
        "reconstructed_ink_px": int(b.sum()),
    }


# --------------------------------------------------------------------------
# comparison engine, off by default
# --------------------------------------------------------------------------


def tesseract_boxes(source: Path) -> list[dict[str, int | str]]:
    result = subprocess.run(
        ["tesseract", str(source), "stdout", "--psm", "6", "makebox"],
        check=True,
        capture_output=True,
        text=True,
    )
    boxes: list[dict[str, int | str]] = []
    for raw in result.stdout.splitlines():
        fields = raw.split()
        if len(fields) != 6:
            continue
        glyph, left, bottom, right, top, page = fields
        boxes.append(
            {
                "glyph": glyph,
                "left": int(left),
                "bottom": int(bottom),
                "right": int(right),
                "top": int(top),
                "page": int(page),
            }
        )
    return boxes


# --------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--calibration",
        type=Path,
        default=None,
        help="optional prior; the measured lattice always wins and the disagreement is reported",
    )
    parser.add_argument("--alphabet", default=DEFAULT_ALPHABET)
    parser.add_argument(
        "--extra-glyphs",
        default="",
        help="characters to add to the candidate set, e.g. overscore or acute for line art",
    )
    parser.add_argument("--font", type=Path, action="append", default=None)
    parser.add_argument("--engine", choices=("template", "tesseract"), default="template")
    parser.add_argument("--margin", type=float, default=0.6)
    parser.add_argument("--ink-floor", type=float, default=0.8)
    parser.add_argument("--sample-limit", type=int, default=160)
    parser.add_argument(
        "--adapt",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="rebuild templates from the image's own confident reads and re-classify",
    )
    parser.add_argument("--min-exemplars", type=int, default=2)
    parser.add_argument("--margin-quantile", type=float, default=0.35)
    args = parser.parse_args()

    alphabet = args.alphabet
    for character in args.extra_glyphs:
        if character not in alphabet:
            alphabet += character
    if " " not in alphabet:
        alphabet = " " + alphabet

    image = np.asarray(Image.open(args.source).convert("RGB"))
    background = dominant_background(image)
    ink = ink_intensity(image, background)
    lattice = measure_lattice(ink)
    cells, cell = cut_cells(ink, lattice)

    args.output.mkdir(parents=True, exist_ok=False)

    if args.engine == "tesseract":
        boxes = tesseract_boxes(args.source)
        (args.output / "tesseract-boxes.json").write_text(
            json.dumps(boxes, indent=2) + "\n", encoding="utf-8"
        )
        print("tesseract engine records boxes only; it does not produce a scored grid", file=sys.stderr)
        return

    fonts = discover_fonts(args.font, DEFAULT_FONT_DIRS)
    fit, templates, trials = fit_typeface(
        cells, cell, alphabet, fonts, lattice.advance_x, args.ink_floor, args.sample_limit
    )
    if fit is None or templates is None:
        raise SystemExit("no monospaced font could be fitted to the measured cell")

    grid, decisions, tally, placement = classify(
        cells, templates, alphabet, args.ink_floor, args.margin
    )
    reconstruction = render_reconstruction(grid, templates, alphabet, cell, placement)
    scores = agreement(reconstruction, cells)

    # Second pass: rebuild the templates from the image's own confident reads,
    # then classify again. Kept only if it agrees with the source better, so a
    # bootstrap that entrenches a mistake is discarded rather than shipped.
    adaptation: dict[str, object] = {"enabled": bool(args.adapt), "accepted": False}
    if args.adapt:
        learned, counts = learn_empirical_templates(
            cells, templates, decisions, alphabet, args.min_exemplars, args.margin_quantile
        )
        adaptation["templates_learned"] = len(counts)
        adaptation["exemplars_per_glyph"] = counts
        adaptation["agreement_before"] = scores["ink_intersection_over_union"]
        if counts:
            grid2, decisions2, tally2, placement2 = classify(
                cells, learned, alphabet, args.ink_floor, args.margin
            )
            reconstruction2 = render_reconstruction(grid2, learned, alphabet, cell, placement2)
            scores2 = agreement(reconstruction2, cells)
            adaptation["agreement_after"] = scores2["ink_intersection_over_union"]
            before = scores["ink_intersection_over_union"] or 0.0
            after = scores2["ink_intersection_over_union"] or 0.0
            if after > before:
                adaptation["accepted"] = True
                grid, decisions, tally = grid2, decisions2, tally2
                templates, placement = learned, placement2
                reconstruction, scores = reconstruction2, scores2

    text = "\n".join("".join(row).rstrip() for row in grid).rstrip("\n") + "\n"
    (args.output / "machine-ocr.txt").write_text(text, encoding="utf-8")

    Image.fromarray((np.clip(reconstruction, 0, 1) * 255).astype(np.uint8)).save(
        args.output / "reconstruction.png"
    )

    prior = None
    if args.calibration and args.calibration.exists():
        declared = json.loads(args.calibration.read_text(encoding="utf-8")).get("grid", {})
        prior = {
            "declared_cell_advance_x_px": declared.get("cell_advance_x_px"),
            "declared_line_height_px": declared.get("line_height_px"),
            "declared_columns": declared.get("columns"),
            "declared_rows": declared.get("rows"),
            "measured_minus_declared_x": (
                lattice.advance_x - float(declared["cell_advance_x_px"])
                if declared.get("cell_advance_x_px")
                else None
            ),
            "measured_minus_declared_y": (
                lattice.advance_y - float(declared["line_height_px"])
                if declared.get("line_height_px")
                else None
            ),
        }

    ink_cells = int(sum(1 for decision in decisions))
    receipt = {
        "schema": "fixed_grid_recovery.v3",
        "acceptance_status": "experimental_unaccepted",
        "source": str(args.source),
        "pixel_size": {"width": int(image.shape[1]), "height": int(image.shape[0])},
        "background_rgb": list(background),
        "measured_lattice": {
            "cell_advance_x_px": round(lattice.advance_x, 4),
            "line_height_px": round(lattice.advance_y, 4),
            "origin_x_px": round(lattice.origin_x, 4),
            "origin_y_px": round(lattice.origin_y, 4),
            "columns": lattice.columns,
            "rows": lattice.rows,
            "cell_aspect_w_over_h": round(lattice.advance_x / lattice.advance_y, 4),
            "x_fit": asdict(lattice.x_fit),
            "y_fit": asdict(lattice.y_fit),
        },
        "declared_prior": prior,
        "inferred_typeface": asdict(fit),
        "typeface_runners_up": trials,
        "alphabet_size": len(alphabet),
        "decision_policy": {
            "engine": "template-match with recorded margin",
            "margin_required": args.margin,
            "ink_floor": args.ink_floor,
            "rule": "emit best candidate only when runner-up distance exceeds it by the margin",
        },
        "coverage": {
            "grid_cells": lattice.rows * lattice.columns,
            "ink_bearing_source_cells": ink_cells,
            "resolved_cells": tally["resolved"],
            "ambiguous_cells": tally["ambiguous"],
            "resolved_fraction_of_ink_cells": (
                tally["resolved"] / ink_cells if ink_cells else None
            ),
        },
        "reconstruction_agreement": scores,
        "adaptation": adaptation,
        "note": "Question marks are scored-but-ambiguous cells. Spaces inside the ink region are scored decisions, not drops.",
    }
    (args.output / "quality.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    (args.output / "cell-decisions.json").write_text(
        json.dumps([asdict(decision) for decision in decisions], indent=2) + "\n",
        encoding="utf-8",
    )

    iou = scores["ink_intersection_over_union"]
    print(
        f"recovery: {tally['resolved']}/{ink_cells} ink-bearing cells resolved, "
        f"{tally['ambiguous']} ambiguous; "
        f"lattice {lattice.advance_x:.3f}x{lattice.advance_y:.3f}px "
        f"(aspect {lattice.advance_x / lattice.advance_y:.4f}); "
        f"font {Path(fit.font).name}@{fit.size}; "
        f"reconstruction IoU {iou:.3f}" if iou is not None else "reconstruction IoU n/a"
    )


if __name__ == "__main__":
    main()

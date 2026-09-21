"""Round-trip accuracy on synthetic sheets with known ground truth.

The bundled sample has no accepted transcript, so it cannot say whether the
recovery is right — only whether it is self-consistent. These tests render text
the pipeline has never seen, at a font and a cell geometry the pipeline is not
told, and then demand the characters back.

That separates two failures that the sample confuses:

* the machinery is wrong, which these tests catch;
* the machinery is right but the source typeface is not installed, which these
  tests deliberately exclude by rendering with a font that is installed.

Aspect ratios here are 1:1, 1:2 and 16:29 on purpose. Nothing in the pipeline
may prefer any of them.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
RECOVER = ROOT / "scripts/recover_monospace_ascii.py"

CANDIDATE_FONTS = (
    "/System/Library/Fonts/Menlo.ttc",
    "/System/Library/Fonts/Monaco.ttf",
    "/System/Library/Fonts/Supplemental/Andale Mono.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
)

LINE_ART = [
    "   _.-'''-._   ",
    "  /         \\  ",
    " |  (o) (o)  | ",
    " |     ^     | ",
    "  \\  \\___/  /  ",
    "   '-._____.-'  ",
]

MIXED = [
    "def grid(n):   ",
    "    return n*2 ",
    "  # note: 3+4  ",
]


def first_available_font() -> str | None:
    for path in CANDIDATE_FONTS:
        if Path(path).exists():
            return path
    return None


def cell_width_for(font_path: str, size: int) -> int:
    """The advance the font actually has at this size.

    A synthetic sheet must be self-consistent. Rendering 17px glyphs on a 10px
    pitch makes every glyph overflow its cell, puts ink on every boundary, and
    leaves the sheet with no legal lattice to find. That is a broken fixture,
    not a pipeline failure — the first version of this file had exactly that bug.
    """
    return int(round(ImageFont.truetype(font_path, size).getlength("M")))


def render_sheet(
    lines: list[str],
    font_path: str,
    size: int,
    cell_h: int,
    baseline: int,
    target: Path,
) -> int:
    cell_w = cell_width_for(font_path, size)
    columns = max(len(line) for line in lines)
    image = Image.new("RGB", (columns * cell_w + 8, len(lines) * cell_h + 8), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_path, size)
    for row, line in enumerate(lines):
        for column, character in enumerate(line):
            if character == " ":
                continue
            draw.text(
                (4 + column * cell_w, 4 + row * cell_h + baseline),
                character,
                fill=(20, 20, 20),
                font=font,
                anchor="ls",
            )
    image.save(target)
    return cell_w


def recover(source: Path, output: Path, extra: list[str] | None = None) -> dict:
    subprocess.run(
        [sys.executable, str(RECOVER), str(source), str(output), *(extra or [])],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads((output / "quality.json").read_text())


def _score_at(expected: list[str], got: list[str], row_shift: int, column_shift: int) -> tuple[int, int, int]:
    exact = ambiguous = comparable = 0
    for row, line in enumerate(expected):
        for column, character in enumerate(line):
            if character == " ":
                continue
            comparable += 1
            source_row, source_column = row + row_shift, column + column_shift
            found = ""
            if 0 <= source_row < len(got) and 0 <= source_column < len(got[source_row]):
                found = got[source_row][source_column]
            if found == character:
                exact += 1
            elif found == "?":
                ambiguous += 1
    return exact, ambiguous, comparable


def score(expected: list[str], recovered: str) -> tuple[int, int, int]:
    """Return (exact, ambiguous, comparable) over non-space expected cells.

    The recovered grid covers the whole canvas, including its margins, and the
    tool is never told where the text block begins. So the comparison searches a
    small rigid offset first. Without that, a perfect recovery that happens to
    start one column further in scores near zero — which is what the first
    version of this scorer reported.
    """
    got = recovered.splitlines()
    best = (-1, 0, 0)
    for row_shift in range(-4, 5):
        for column_shift in range(-6, 7):
            exact, ambiguous, comparable = _score_at(expected, got, row_shift, column_shift)
            if exact > best[0]:
                best = (exact, ambiguous, comparable)
    return best


class RoundTrip(unittest.TestCase):
    def setUp(self) -> None:
        self.font = first_available_font()
        if self.font is None:
            self.skipTest("no known monospaced font on this machine")

    def _run(self, lines: list[str], cell_h: int, size: int, baseline: int) -> dict:
        with tempfile.TemporaryDirectory() as parent:
            source = Path(parent) / "sheet.png"
            output = Path(parent) / "out"
            cell_w = render_sheet(lines, self.font, size, cell_h, baseline, source)
            receipt = recover(source, output)
            text = (output / "machine-ocr.txt").read_text()
            exact, ambiguous, comparable = score(lines, text)
            return {
                "receipt": receipt,
                "text": text,
                "cell_w": cell_w,
                "cell_h": cell_h,
                "exact": exact,
                "ambiguous": ambiguous,
                "comparable": comparable,
            }

    def test_measures_a_one_to_two_cell_without_being_told(self) -> None:
        # size 17 gives a 10px advance; a 20px line pitch makes the cell 1:2.
        result = self._run(LINE_ART, cell_h=20, size=17, baseline=15)
        lattice = result["receipt"]["measured_lattice"]
        self.assertAlmostEqual(lattice["cell_advance_x_px"], result["cell_w"], delta=0.6)
        self.assertAlmostEqual(lattice["line_height_px"], 20.0, delta=0.9)

    def test_measures_a_near_square_cell_without_being_told(self) -> None:
        # size 13 gives an 8px advance; a 9px pitch makes the cell nearly square.
        result = self._run(MIXED, cell_h=9, size=13, baseline=7)
        lattice = result["receipt"]["measured_lattice"]
        self.assertAlmostEqual(lattice["cell_advance_x_px"], result["cell_w"], delta=0.7)
        self.assertAlmostEqual(lattice["line_height_px"], 9.0, delta=0.9)

    def test_measures_a_sixteen_by_twentynine_cell_without_being_told(self) -> None:
        # size 27 gives a 16px advance; a 29px pitch is the Stone Story aspect,
        # which the pipeline must treat as one fit among others.
        result = self._run(LINE_ART, cell_h=29, size=27, baseline=23)
        lattice = result["receipt"]["measured_lattice"]
        self.assertAlmostEqual(lattice["cell_advance_x_px"], result["cell_w"], delta=0.8)
        self.assertAlmostEqual(lattice["line_height_px"], 29.0, delta=1.2)

    def test_recovers_most_characters_when_the_font_is_available(self) -> None:
        result = self._run(LINE_ART, cell_h=22, size=19, baseline=17)
        ratio = result["exact"] / result["comparable"]
        self.assertGreater(
            ratio,
            0.6,
            msg=f"only {result['exact']}/{result['comparable']} exact\n{result['text']}",
        )

    def test_never_invents_a_character_it_did_not_score(self) -> None:
        result = self._run(LINE_ART, cell_h=22, size=19, baseline=17)
        coverage = result["receipt"]["coverage"]
        self.assertEqual(
            coverage["resolved_cells"] + coverage["ambiguous_cells"],
            coverage["ink_bearing_source_cells"],
        )

    def test_receipt_reports_the_fitted_typeface_and_its_residual(self) -> None:
        result = self._run(MIXED, cell_h=9, size=13, baseline=7)
        typeface = result["receipt"]["inferred_typeface"]
        self.assertIn("font", typeface)
        self.assertGreater(typeface["size"], 0)
        self.assertGreaterEqual(typeface["residual"], 0.0)


if __name__ == "__main__":
    unittest.main()

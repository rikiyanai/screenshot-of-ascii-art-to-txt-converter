"""The measured lattice must be the fundamental, not one of its harmonics.

Both period estimators in the pipeline suffer octave error, and they fail in
opposite directions, which is why neither a bias toward large periods nor a
bias toward small ones can fix it:

* the spectral projection locks onto HALF the true advance on dense text,
  because the second harmonic of a tightly packed row is stronger than its
  fundamental;
* the autocorrelation peak locks onto TWICE the true line pitch, because an
  integer multiple of a period is also a peak of the autocorrelation.

The defect was invisible for a long time because real character art is sparse.
Whitespace breaks up the runs, the fundamental dominates, and both estimators
land on the right answer. Prose-dense text is what exposes it, so these tests
render both and demand the same accuracy from each.

Ground truth here is the font's own advance, read from the font, never a
constant written into the test.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from recover_monospace_ascii import (  # noqa: E402
    dominant_background,
    gutter_contrast,
    ink_intensity,
    measure_lattice,
    resolve_harmonic,
)

CANDIDATE_FONTS = (
    "/Library/Fonts/DejaVuSansMono.ttf",
    "/System/Library/Fonts/Menlo.ttc",
    "/System/Library/Fonts/Monaco.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
)

DENSE = [
    "ABCDEFGHIJKLMNOP",
    "abcdefghijklmnop",
    "0123456789012345",
    "################",
    "ABCDEFGHIJKLMNOP",
    "abcdefghijklmnop",
    "0123456789012345",
    "################",
]
WORDS = [
    "the quick brown",
    "fox jumps over ",
    "the lazy dog   ",
    "pack my box    ",
    "with five dozen",
    "liquor jugs    ",
    "how vexingly   ",
    "quick daft     ",
]
SPARSE = [
    "  /\\_/\\   ",
    " ( o.o )  ",
    "  > ^ <   ",
    "  |   |   ",
    "  `---`   ",
    "          ",
    "   ***    ",
    "  *   *   ",
]


def first_font() -> str | None:
    for path in CANDIDATE_FONTS:
        if Path(path).exists():
            return path
    return None


def render(rows: list[str], font_path: str, size: int, line_height: int, margin: int = 12):
    font = ImageFont.truetype(font_path, size)
    width = int(max(font.getlength(line) for line in rows)) + 2 * margin
    height = line_height * len(rows) + 2 * margin
    image = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    for index, line in enumerate(rows):
        draw.text((margin, margin + index * line_height), line, font=font, fill=(0, 0, 0))
    return image, float(font.getlength("M"))


class HarmonicResolution(unittest.TestCase):
    def setUp(self):
        self.font = first_font()
        if self.font is None:
            self.skipTest("no monospaced font available")

    def _check(self, rows: list[str], line_height: int, label: str):
        image, advance = render(rows, self.font, 16, line_height)
        array = np.asarray(image.convert("RGB"))
        lattice = measure_lattice(ink_intensity(array, dominant_background(array)))
        self.assertAlmostEqual(
            lattice.advance_x / advance,
            1.0,
            delta=0.06,
            msg=(
                f"{label}: measured advance {lattice.advance_x:.3f} against a true "
                f"{advance:.3f}; a ratio near 0.5 or 2.0 is an octave error"
            ),
        )
        self.assertAlmostEqual(
            lattice.advance_y / line_height,
            1.0,
            delta=0.06,
            msg=(
                f"{label}: measured line pitch {lattice.advance_y:.3f} against a true "
                f"{line_height}; a ratio near 2.0 or 3.0 is an octave error"
            ),
        )

    def test_dense_rows_do_not_halve_the_advance(self):
        self._check(DENSE, 22, "dense")

    def test_prose_rows_do_not_halve_the_advance(self):
        self._check(WORDS, 22, "words")

    def test_sparse_art_still_measures_correctly(self):
        # This case always worked. It is here so a fix aimed at the dense case
        # cannot quietly break the one the tool actually ships for.
        self._check(SPARSE, 22, "sparse")

    def test_the_defect_is_present_at_several_line_heights(self):
        for line_height in (18, 20, 24, 28):
            with self.subTest(line_height=line_height):
                self._check(WORDS, line_height, f"words at {line_height}")


class GutterContrast(unittest.TestCase):
    """The criterion that decides between harmonics."""

    def setUp(self):
        self.profile = np.zeros(400, dtype=np.float64)
        for start in range(10, 390, 10):
            self.profile[start : start + 6] = 1.0

    def test_the_true_period_beats_both_of_its_neighbours(self):
        true = gutter_contrast(self.profile, 10.0)
        self.assertGreater(true, gutter_contrast(self.profile, 5.0))
        self.assertGreater(true, gutter_contrast(self.profile, 20.0))

    def test_a_doubled_estimate_is_pulled_back_to_the_fundamental(self):
        resolved, note = resolve_harmonic(self.profile, 20.0, 4.0, 60.0)
        self.assertAlmostEqual(resolved, 10.0, delta=0.5)
        self.assertIn("harmonic corrected", note)

    def test_a_halved_estimate_is_pulled_back_to_the_fundamental(self):
        resolved, _ = resolve_harmonic(self.profile, 5.0, 4.0, 60.0)
        self.assertAlmostEqual(resolved, 10.0, delta=0.5)

    def test_a_correct_estimate_is_left_alone(self):
        resolved, note = resolve_harmonic(self.profile, 10.0, 4.0, 60.0)
        self.assertAlmostEqual(resolved, 10.0, delta=0.5)
        self.assertNotIn("harmonic corrected", note)


if __name__ == "__main__":
    unittest.main()

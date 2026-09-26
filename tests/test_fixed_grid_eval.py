from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from eval_fixed_grid_corpus import (  # noqa: E402
    fit_origin,
    randomize_outer_margins,
    strip_outer_blank_cells,
)


class RandomMarginRecovery(unittest.TestCase):
    def test_random_margins_are_reproducible(self) -> None:
        source = np.full((10, 12), 255, dtype=np.uint8)
        source[3:7, 4:8] = 0
        render = {"padding_px": 2}
        first, margins = randomize_outer_margins(source, "piece/res01", render, "seed", 31)
        second, repeated = randomize_outer_margins(source, "piece/res01", render, "seed", 31)
        self.assertEqual(margins, repeated)
        np.testing.assert_array_equal(first, second)
        self.assertTrue(all(0 <= value <= 31 for value in margins.values()))

    def test_phase_is_fitted_without_margin_metadata(self) -> None:
        height, width = 3, 2
        glyph_a = np.array([[1, 0], [0, 1], [1, 1]], dtype=bool)
        glyph_b = np.array([[0, 1], [1, 1], [1, 0]], dtype=bool)
        templates = {glyph_a.tobytes(): ("A",), glyph_b.tobytes(): ("B",)}
        content = np.block([[glyph_a, glyph_b, glyph_a], [glyph_b, glyph_a, glyph_b]])
        top, left, bottom, right = 4, 5, 5, 4
        screenshot = np.zeros(
            (top + content.shape[0] + bottom, left + content.shape[1] + right), dtype=bool
        )
        screenshot[top : top + content.shape[0], left : left + content.shape[1]] = content
        y0, x0, receipt = fit_origin(screenshot, templates, height, width)
        self.assertEqual((y0, x0), (top % height, left % width))
        self.assertEqual(receipt.get("unmatched", 0), 0)

    def test_screenshot_border_cells_are_removed(self) -> None:
        rows = ["       ", "   AB  ", "   C   ", "       "]
        self.assertEqual(strip_outer_blank_cells(rows), ["AB", "C"])


if __name__ == "__main__":
    unittest.main()

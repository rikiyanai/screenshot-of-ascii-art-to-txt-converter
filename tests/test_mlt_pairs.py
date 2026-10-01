"""AA-004 pairs: the derived render must equal AAHub's own renders (P0C-10)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import mlt_pairs  # noqa: E402

ARCHIVE = ROOT.parent / "ascii-art-archive"
FONT = ARCHIVE / mlt_pairs.FONT_REL


@unittest.skipUnless(FONT.exists(), "ascii-art-archive not checked out beside this repository")
class MltPairs(unittest.TestCase):
    def test_render_matches_archive_png_pixel_for_pixel(self) -> None:
        for page in ("goraku/resK-72", "kyoko-01/res129"):
            text = (ARCHIVE / "collections" / "aahub" / f"{page}.txt").read_text(encoding="utf-8")
            want = np.asarray(Image.open(ARCHIVE / "collections" / "aahub" / f"{page}.png").convert("L")) < 128
            got = np.asarray(mlt_pairs.render_aahub(text, FONT).convert("L")) < 128
            self.assertEqual(got.shape, want.shape, page)
            self.assertEqual(int((got ^ want).sum()), 0, page)

    def test_headers_are_not_art(self) -> None:
        self.assertFalse(mlt_pairs.is_art("【建物】\n"))
        self.assertTrue(mlt_pairs.is_art("　 ／￣＼\n　 ＼＿／\n"))


if __name__ == "__main__":
    unittest.main()

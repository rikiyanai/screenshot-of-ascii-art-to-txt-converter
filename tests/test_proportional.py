"""Proportional (Shift_JIS-style) art decoded against a real answer key.

``sample/proportional/madonna.source.png`` is a real 2x retina screenshot of
art set in Saitamaar at 11 CSS px; ``madonna.expected.txt`` is its source text,
supplied by the user. Rendering the key in the vendored face at 22 px, origin
x=6 and a 24 px pitch reproduces the screenshot at cosine 0.976, which is what
identifies the face and size.

The gate is on the spacing-canonical view: any order of the same U+3000 and
U+0020 in a blank run renders identically, so order is not in the pixels and
is not scored. Strict CER is reported, not gated.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "sample/proportional"
sys.path.insert(0, str(ROOT / "scripts"))

import recover_proportional_aa as rp  # noqa: E402
from score_against_key import score  # noqa: E402


class CanonicalSpacing(unittest.TestCase):
    def test_never_two_half_spaces_adjacent(self) -> None:
        for full in range(0, 5):
            for half in range(0, full + 2):
                run = "　" * full + " " * half
                out = rp.canonical_spacing("a" + run + "b")
                self.assertNotIn("  ", out)
                self.assertEqual(out.count("　"), full)
                self.assertEqual(out.count(" "), half)

    def test_kanji_fallback_covers_the_whole_unified_block(self) -> None:
        ordinary = rp.prior_alphabet({})
        fallback = rp.prior_alphabet({}, kanji_fallback=True)
        self.assertNotIn("龿", ordinary)
        self.assertIn("一", fallback)
        self.assertIn("龿", fallback)


class ShortPagePhase(unittest.TestCase):
    def test_pre_rendered_bank_preserves_decode(self) -> None:
        model = rp.load_font_model(rp.DEFAULT_FONT, "._")
        rows = ["._._", "_.._", "..__"]
        baselines = [22 + 17 * i for i in range(len(rows))]
        ink = rp.render_text(rows, model, 16, 17, 8, baselines, (80, 80))
        image = Image.fromarray((255 - 255 * (ink > 0.35)).astype(np.uint8))
        bank = rp.render_bank(model, 16, 22, 16, {})
        direct = rp.decode_image(image, model, 16, 0.02, 8, {}, 0)
        cached = rp.decode_image(image, model, 16, 0.02, 8, {}, 0, True, bank)
        self.assertEqual([row.text for row in cached["rows"]], [row.text for row in direct["rows"]])
        self.assertEqual(cached["baselines"], direct["baselines"])

    def test_image_fits_actual_baseline_not_average_glyph_profile(self) -> None:
        rows = [
            " /\\_/\\ ", "( o.o )", " > ^ < ", "  /|\\  ", " /_|_\\ ",
            "  | |  ", " /   \\ ", "(_____) ", "  ~~~  ",
        ]
        prior = rp.load_prior(rp.DEFAULT_PRIOR)
        model = rp.load_font_model(rp.DEFAULT_FONT, rp.prior_alphabet(prior))
        expected_baselines = [22 + 17 * i for i in range(len(rows))]
        ink = rp.render_text(rows, model, 16, 17, 8, expected_baselines, (180, 180))
        image = Image.fromarray((255 - 255 * (ink > 0.35)).astype(np.uint8))
        result = rp.decode_image(image, model, 16, 0.02, 8, prior, 0)
        self.assertAlmostEqual(result["pitch"], 17, delta=0.05)
        self.assertEqual(result["baselines"], expected_baselines)
        self.assertEqual(len(result["rows"]), len(rows))


class StrokeIdiomPrior(unittest.TestCase):
    """Converter FL 2026-09-27 note item 2: touching-pair prior from training pages."""

    def _counts(self, counts: dict[str, int]) -> Path:
        tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        json.dump({"counts": counts}, tmp, ensure_ascii=False)
        tmp.close()
        return Path(tmp.name)

    def test_only_positive_associations_are_kept(self) -> None:
        chars = [" ", "　", "⌒", "ヽ", "_", "ノ"]
        path = self._counts({"⌒ヽ": 90, "⌒_": 10, "_ノ": 50, "__": 50, "ヽ_": 5})
        table = rp.bigram_bonus(path, chars)
        a, b = chars.index("⌒"), chars.index("ヽ")
        self.assertIn(a, table)
        succ, pmi = table[a]
        self.assertIn(b, succ.tolist())
        self.assertTrue((pmi > 0).all())
        self.assertNotIn(chars.index(" "), table)
        self.assertEqual(rp.bigram_bonus(None, chars), {})

    def test_weight_zero_is_the_unprimed_decode_and_bonus_reaches_the_path(self) -> None:
        model = rp.load_font_model(rp.DEFAULT_FONT, ".:_")
        rows = ["._._"]
        ink = rp.render_text(rows, model, 16, 17, 8, [22], (40, 80))
        image = Image.fromarray((255 - 255 * (ink > 0.35)).astype(np.uint8))
        bank = rp.render_bank(model, 16, 22, 16, {})
        table = rp.bigram_bonus(self._counts({".:": 1000, ":.": 1000, "_.": 1, "._": 1}), bank.characters)
        plain = rp.decode_image(image, model, 16, 0.02, 8, {}, 0, True, bank)
        zero = rp.decode_image(image, model, 16, 0.02, 8, {}, 0, True, bank, table, 0.0)
        self.assertEqual([r.text for r in zero["rows"]], [r.text for r in plain["rows"]])
        self.assertEqual(plain["rows"][0].text, "._._")
        # an absurd weight must override the ink: this checks the wiring, not a setting
        forced = rp.decode_image(image, model, 16, 0.02, 8, {}, 0, True, bank, table, 1e4)
        self.assertIn(":", forced["rows"][0].text)
        self.assertEqual(forced["baselines"], plain["baselines"])


class SubFloorPitch(unittest.TestCase):
    """P0C-10: 30/986 AA-003 train pages crashed with an empty pitch-candidate
    set. The autocorrelation locked onto bars inside a line (8-15 px) instead
    of the 17 px line box, and every candidate under 0.95 em was skipped."""

    def test_in_line_structure_does_not_empty_the_pitch_candidates(self) -> None:
        model = rp.load_font_model(rp.DEFAULT_FONT, "三二")
        rows = ["三二三", "二三二"]
        baselines = [22 + 17 * i for i in range(len(rows))]
        ink = rp.render_text(rows, model, 16, 17, 8, baselines, (60, 50))
        self.assertLess(rp.line_geometry(ink, 22)[0], 0.95 * 16)  # the fault
        image = Image.fromarray((255 - 255 * (ink > 0.35)).astype(np.uint8))
        result = rp.decode_image(image, model, 16, 0.02, 8, {}, 0)
        self.assertAlmostEqual(result["pitch"], 17, delta=0.5)
        self.assertEqual([r.text for r in result["rows"]][:2], rows)


class MadonnaAgainstKey(unittest.TestCase):
    """Decode at the fitted size (22 px) so the test does not spend four
    minutes re-fitting it; the size fit itself is recorded in the receipt."""

    def test_rows_recovered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "run"
            subprocess.run(
                [sys.executable, str(ROOT / "scripts/recover_proportional_aa.py"),
                 str(SAMPLE / "madonna.source.png"), str(out), "--size-px", "22"],
                check=True, capture_output=True,
            )
            got = (out / "recovered.txt").read_text(encoding="utf-8").splitlines()
        key = (SAMPLE / "madonna.expected.txt").read_text(encoding="utf-8").splitlines()
        result = score(got, key)
        self.assertEqual(result["rows_recovered"], len(key))
        self.assertGreaterEqual(result["exact_rows"], 22)
        self.assertLessEqual(result["canonical_cer"], 0.01)


if __name__ == "__main__":
    unittest.main()

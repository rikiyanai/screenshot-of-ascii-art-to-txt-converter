"""The regime detector: can one advance describe this image at all?

The converter assumes a single horizontal advance for every glyph. A whole
class of character art breaks that assumption, and before this detector existed
the tool had no way to notice: it would cut a lattice anyway and report a
confident, meaningless grid.

The fixtures under ``sample/regime`` are the two halves of a paired control.
Both are the same 18 rows of archived Shift_JIS art, rendered at the same size
and line height, through two faces from the SAME family:

* ``Osaka`` is proportional, 30 distinct advances spanning 3.75 to 16 px;
* ``OsakaMono`` is fixed pitch, exactly two advances, 8 and 16 px.

Glyph shapes, text and layout are therefore identical and the metrics are the
only variable. Without that pairing a detector that merely fires on CJK
codepoints would look like a success.

The images are committed rather than rendered at test time because the faces
live under content-hashed ``/System/Library/AssetsV2`` paths that differ
between machines. ``sample/regime/cjk-render.json`` records how they were made.
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
RECOVER = ROOT / "scripts/recover_monospace_ascii.py"
REGIME = ROOT / "sample/regime"

sys.path.insert(0, str(ROOT / "scripts"))

from recover_monospace_ascii import (  # noqa: E402
    REGIME_THRESHOLD_CELLS,
    Lattice,
    detect_regime,
    dominant_background,
    ink_intensity,
    measure_lattice,
    sequence_drift,
)


def run(source: Path, output: Path, extra: list[str] | None = None):
    return subprocess.run(
        [sys.executable, str(RECOVER), str(source), str(output), *(extra or [])],
        capture_output=True,
        text=True,
    )


def verdict_for(source: Path):
    array = np.asarray(Image.open(source).convert("RGB"))
    ink = ink_intensity(array, dominant_background(array))
    return detect_regime(ink, measure_lattice(ink))


class DriftStatistic(unittest.TestCase):
    """Properties of the statistic itself, independent of any image."""

    def test_a_uniform_sequence_has_no_drift(self):
        positions = [10 + 8 * index for index in range(20)]
        self.assertAlmostEqual(sequence_drift(positions, 8.0), 0.0, places=6)

    def test_bounded_jitter_does_not_accumulate(self):
        # Side bearings move each boundary a little but telescope away, so the
        # accumulated residual stays near the size of one bearing.
        jitter = [0, 2, -1, 1, -2, 0, 1, -1, 2, 0, -1, 1]
        positions = [10 + 8 * index + jitter[index % len(jitter)] for index in range(24)]
        self.assertLess(sequence_drift(positions, 8.0), 8.0)

    def test_a_systematic_error_accumulates_past_half_a_cell(self):
        # This is the property the whole detector rests on. Advances of 10 px
        # read against an 8 px period must pile up, not wrap. A statistic that
        # measured distance to the nearest lattice line instead would cap at
        # 4 px here and report nothing wrong.
        positions = [10 + 10 * index for index in range(20)]
        drift = sequence_drift(positions, 8.0)
        self.assertGreater(drift, 8.0, "drift must accumulate rather than wrap at half a cell")


class BandSegmentation(unittest.TestCase):
    def test_bands_come_from_the_ink_and_not_from_the_row_lattice(self):
        """The detector runs before the lattice is trusted, so it cannot use it.

        The row lattice is measured by the same machinery this detector exists
        to guard, and it is observed to lock onto twice the true line pitch on
        real input. Passing a deliberately wrong row advance must therefore
        change nothing.
        """
        ink = np.zeros((100, 200), dtype=np.float32)
        for row in (10, 30, 50, 70):
            for start in range(10, 190, 8):
                ink[row : row + 8, start : start + 5] = 1.0

        honest = measure_lattice(ink)
        deceived = Lattice(
            origin_x=honest.origin_x,
            origin_y=honest.origin_y,
            advance_x=honest.advance_x,
            advance_y=honest.advance_y * 4,
            columns=honest.columns,
            rows=max(1, honest.rows // 4),
            x_fit=honest.x_fit,
            y_fit=honest.y_fit,
        )
        self.assertEqual(
            detect_regime(ink, honest).evaluable_bands,
            detect_regime(ink, deceived).evaluable_bands,
        )


class TooLittleEvidence(unittest.TestCase):
    """Refusing needs evidence too. Silence is not a proportional verdict."""

    def test_a_blank_image_is_undetermined_rather_than_refused(self):
        ink = np.zeros((60, 120), dtype=np.float32)
        verdict = detect_regime(ink, measure_lattice(ink))
        self.assertEqual(verdict.regime, "undetermined")
        self.assertIsNone(verdict.median_drift_cells)

    def test_undetermined_does_not_stop_the_pipeline(self):
        # Only "proportional" refuses. A verdict of "undetermined" means the
        # detector could not judge, which is not grounds to block a reading.
        ink = np.zeros((60, 120), dtype=np.float32)
        ink[20:28, 10:15] = 1.0
        self.assertNotEqual(detect_regime(ink, measure_lattice(ink)).regime, "proportional")


class PairedControl(unittest.TestCase):
    """The same text and the same glyph shapes; only the metrics differ."""

    def setUp(self):
        self.proportional = REGIME / "cjk-proportional.source.png"
        self.monospaced = REGIME / "cjk-monospaced.source.png"
        for path in (self.proportional, self.monospaced):
            if not path.exists():
                self.skipTest(f"missing fixture {path}")

    def test_the_proportional_half_is_classified_proportional(self):
        verdict = verdict_for(self.proportional)
        self.assertEqual(verdict.regime, "proportional")
        self.assertGreater(verdict.median_drift_cells, REGIME_THRESHOLD_CELLS)

    def test_the_monospaced_half_is_classified_monospaced(self):
        verdict = verdict_for(self.monospaced)
        self.assertEqual(
            verdict.regime,
            "monospaced",
            "same text, same face family, fixed pitch: a detector that fired "
            "here would be reacting to the script, not to the metrics",
        )

    def test_the_two_halves_are_separated_by_a_wide_margin(self):
        loose = verdict_for(self.proportional).median_drift_cells
        tight = verdict_for(self.monospaced).median_drift_cells
        self.assertGreater(loose, 10 * tight)


class RefusalBehaviour(unittest.TestCase):
    def setUp(self):
        self.proportional = REGIME / "cjk-proportional.source.png"
        if not self.proportional.exists():
            self.skipTest("missing fixture")
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_proportional_input_is_refused_and_emits_no_text(self):
        output = Path(self.tmp.name) / "refused"
        result = run(self.proportional, output)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertFalse(
            (output / "machine-ocr.txt").exists(),
            "a refusal must not leave behind text that looks like a reading",
        )
        receipt = json.loads((output / "quality.json").read_text())
        self.assertEqual(receipt["schema"], "fixed_grid_recovery.v4")
        self.assertEqual(receipt["acceptance_status"], "refused_not_a_fixed_grid")
        self.assertEqual(receipt["regime"]["regime"], "proportional")
        self.assertIn("reason", receipt["regime"])

    def test_the_refusal_can_be_overridden_on_purpose(self):
        output = Path(self.tmp.name) / "anyway"
        result = run(self.proportional, output, ["--on-proportional", "warn"])
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = json.loads((output / "quality.json").read_text())
        self.assertEqual(
            receipt["regime"]["regime"],
            "proportional",
            "an override must still record that the result is not trustworthy",
        )


class RealPairIsNotRefused(unittest.TestCase):
    """The regression that matters: do not start refusing work that worked."""

    def test_the_bonsai_pair_stays_monospaced(self):
        source = ROOT / "sample/bonsai.source.png"
        if not source.exists():
            self.skipTest("missing sample")
        verdict = verdict_for(source)
        self.assertEqual(verdict.regime, "monospaced")
        self.assertLess(verdict.median_drift_cells, REGIME_THRESHOLD_CELLS)


if __name__ == "__main__":
    unittest.main()

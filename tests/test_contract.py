from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
VISUAL_GIF = ROOT / "docs/screenshot-to-txt-comparison.gif"
VISUAL_RECEIPT = ROOT / "docs/screenshot-to-txt-comparison.receipt.json"


class BundledSampleContract(unittest.TestCase):
    def test_calibration_uses_package_relative_source(self) -> None:
        calibration = json.loads((ROOT / "sample/calibration.json").read_text())
        self.assertEqual(calibration["source_png"], "sample/source.normalized.png")

    def test_wrapper_pins_sample_and_calibration_hashes(self) -> None:
        wrapper = (ROOT / "run-sample.sh").read_text()
        self.assertIn("9ea8eab2c0b378ed89ad2337515a6baea4ec81d0eace6ba042fab4abee63a3d3", wrapper)
        self.assertIn("f8a1aca96ccc43a08b1981a7fff0d34ebe773f7cc45fe148178c3554d65f7944", wrapper)

    def test_python_dependencies_are_pinned(self) -> None:
        requirements = (ROOT / "requirements.txt").read_text().splitlines()
        self.assertEqual(requirements, ["numpy==2.4.1", "Pillow==12.1.0"])

    def test_bundled_sample_produces_expected_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as parent:
            output = Path(parent) / "recovery"
            subprocess.run([str(ROOT / "run-sample.sh"), str(output)], check=True)

            self.assertEqual(
                {path.name for path in output.iterdir()},
                {
                    'machine-ocr.txt',
                    "quality.json",
                    "cell-decisions.json",
                    "reconstruction.png",
                },
            )
            machine_text = (output / 'machine-ocr.txt').read_text()
            quality = json.loads((output / "quality.json").read_text())

            self.assertEqual(quality["schema"], "fixed_grid_recovery.v4")
            self.assertEqual(quality["acceptance_status"], "experimental_unaccepted")

            # v4 adds the regime verdict. Every reading carries the evidence
            # that one advance was able to describe the image at all, so a
            # reader never has to assume it.
            regime = quality["regime"]
            self.assertEqual(regime["regime"], "monospaced")
            self.assertGreater(regime["evaluable_bands"], 0)
            self.assertLessEqual(
                regime["median_drift_cells"], regime["threshold_cells"]
            )
            self.assertIn("reason", regime)
            self.assertIn("drift", regime["method"])

            # The lattice is measured, not taken from the calibration prior.
            lattice = quality["measured_lattice"]
            self.assertGreater(lattice["cell_advance_x_px"], 0)
            self.assertGreater(lattice["line_height_px"], 0)
            self.assertEqual(lattice["columns"], 37)

            # The prior is recorded beside the measurement, so a disagreement is
            # visible instead of silent.
            prior = quality["declared_prior"]
            self.assertEqual(prior["declared_columns"], 37)
            self.assertIsNotNone(prior["measured_minus_declared_x"])

            # The typeface is a fitted parameter carrying a reported residual.
            typeface = quality["inferred_typeface"]
            self.assertTrue(typeface["font"])
            self.assertGreater(typeface["size"], 0)
            self.assertGreaterEqual(typeface["residual"], 0.0)

            # Coverage counts ink-bearing SOURCE cells, and every such cell is
            # either resolved or explicitly ambiguous. This is the check the old
            # receipt could not make, because it divided output by output.
            coverage = quality["coverage"]
            self.assertGreater(coverage["ink_bearing_source_cells"], 0)
            self.assertEqual(
                coverage["resolved_cells"] + coverage["ambiguous_cells"],
                coverage["ink_bearing_source_cells"],
            )
            self.assertLessEqual(
                coverage["ink_bearing_source_cells"], coverage["grid_cells"]
            )

            # Every decision carries the score that produced it.
            decisions = json.loads((output / "cell-decisions.json").read_text())
            self.assertEqual(len(decisions), coverage["ink_bearing_source_cells"])
            for decision in decisions:
                self.assertIn("best", decision)
                self.assertIn("runner_up", decision)
                self.assertIn("margin", decision)

            # The margin policy is recorded, not implied.
            policy = quality["decision_policy"]
            self.assertGreater(policy["margin_required"], 0)
            self.assertIn("margin", policy["rule"])

            # Question marks are ambiguous cells, never invented glyphs.
            self.assertEqual(machine_text.count("?"), coverage["ambiguous_cells"])

    def test_tesseract_is_not_required_to_run(self) -> None:
        wrapper = (ROOT / "run-sample.sh").read_text()
        self.assertNotIn("command -v tesseract", wrapper)

    def test_no_cell_aspect_is_hard_coded(self) -> None:
        source = (ROOT / "scripts/recover_monospace_ascii.py").read_text()
        for forbidden in ("16 / 29", "16/29", "0.5517"):
            self.assertNotIn(forbidden, source)

    def test_visual_evidence_contract(self) -> None:
        receipt = json.loads(VISUAL_RECEIPT.read_text())
        source_hash = hashlib.sha256(
            (ROOT / "sample/source.normalized.png").read_bytes()
        ).hexdigest()
        self.assertEqual(receipt["schema"], "lateletter.fixed_grid_visual_evidence.v1")
        self.assertEqual(receipt["artifact"], "screenshot-to-txt-comparison.gif")
        self.assertEqual(receipt["canvas_px"], {"width": 1400, "height": 860})
        self.assertEqual(receipt["frame_count"], 4)
        self.assertEqual(
            receipt["hold_label_on_every_frame"],
            "EXPERIMENTAL — 16 unresolved / 78 emitted; source coverage unknown",
        )
        self.assertEqual(receipt["acceptance_status"], "experimental_unaccepted")
        self.assertEqual(
            receipt["source_coverage_status"],
            "unknown_without_accepted_transcript",
        )
        self.assertEqual(receipt["source_sha256"], source_hash)
        self.assertEqual(
            receipt["machine_output_sha256"],
            "22608d602c07c329264853fc0b087e0e1454d1e4c266f810c8758f32851fcad1",
        )
        self.assertEqual(
            receipt["quality_receipt_sha256"],
            "837f2979e71ffaac0690a39639cefb98c2d25364b11c4fcc7dc3588700c04668",
        )
        self.assertEqual(
            receipt["gif_sha256"], hashlib.sha256(VISUAL_GIF.read_bytes()).hexdigest()
        )
        frames = receipt["semantic_frames"]
        self.assertEqual(
            [frame["id"] for frame in frames],
            [
                "full-source-and-full-output",
                "matched-closeup-1",
                "matched-closeup-2",
                "matched-closeup-3",
            ],
        )
        self.assertEqual(
            [frame["output_rows_zero_based_half_open"] for frame in frames],
            [[0, 22], [0, 5], [7, 12], [14, 19]],
        )
        self.assertEqual(
            [frame["source_crop_px"] for frame in frames],
            [
                [0, 0, 424, 468],
                [0, 8, 424, 113],
                [0, 155, 424, 260],
                [0, 302, 424, 407],
            ],
        )
        self.assertTrue(
            all(frame["source_sha256"] == source_hash for frame in frames)
        )
        self.assertTrue(
            all(
                frame["machine_output_sha256"] == receipt["machine_output_sha256"]
                for frame in frames
            )
        )

        with Image.open(VISUAL_GIF) as gif:
            self.assertEqual(gif.size, (1400, 860))
            self.assertEqual(gif.n_frames, 4)
            hold_masks = []
            frame_hashes = []
            durations = []
            for index in range(gif.n_frames):
                gif.seek(index)
                rgb = gif.convert("RGB")
                durations.append(gif.info["duration"])
                hold_masks.append(
                    rgb.crop((0, 60, 1400, 116))
                    .convert("L")
                    .point(lambda value: 255 if value < 120 else 0)
                )
                frame_hashes.append(hashlib.sha256(rgb.tobytes()).hexdigest())
            self.assertEqual(len(set(frame_hashes)), 4)
            self.assertEqual(durations, [4200, 3600, 3600, 4200])
            self.assertEqual(
                durations,
                [frame["duration_ms"] for frame in receipt["semantic_frames"]],
            )
            self.assertTrue(
                all(mask.getbbox() == (30, 22, 800, 44) for mask in hold_masks)
            )
            foreground_counts = [
                sum(bool(pixel) for pixel in mask.get_flattened_data())
                for mask in hold_masks
            ]
            self.assertLessEqual(max(foreground_counts) - min(foreground_counts), 10)

    def test_wrapper_refuses_existing_output(self) -> None:
        with tempfile.TemporaryDirectory() as output:
            result = subprocess.run(
                [str(ROOT / "run-sample.sh"), output],
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 73)
            self.assertIn("refusing existing output path", result.stderr)


if __name__ == "__main__":
    unittest.main()

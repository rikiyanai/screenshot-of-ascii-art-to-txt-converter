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

    @unittest.skipUnless(shutil.which("tesseract"), "tesseract is required")
    def test_bundled_sample_produces_expected_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as parent:
            output = Path(parent) / "recovery"
            subprocess.run([str(ROOT / "run-sample.sh"), str(output)], check=True)

            self.assertEqual(
                {path.name for path in output.iterdir()},
                {
                    "machine-ocr.txt",
                    "tesseract-boxes.json",
                    "calibration.json",
                    "quality.json",
                },
            )
            self.assertEqual(
                len((output / "machine-ocr.txt").read_text().splitlines()),
                22,
            )
            machine_text = (output / "machine-ocr.txt").read_text()
            self.assertEqual({len(line) for line in machine_text.splitlines()}, {37})
            quality = json.loads((output / "quality.json").read_text())
            self.assertEqual(quality["schema"], "lateletter.fixed_grid_recovery_quality.v2")
            self.assertEqual(quality["acceptance_status"], "experimental_unaccepted")
            self.assertEqual(
                quality["source_coverage_status"],
                "unknown_without_accepted_transcript",
            )
            self.assertEqual(quality["grid_rows"], 22)
            self.assertEqual(quality["grid_columns"], 37)
            self.assertEqual(quality["grid_cells"], 814)
            self.assertGreater(quality["emitted_non_space_cells"], 0)
            self.assertGreater(quality["unresolved_emitted_cells"], 0)
            self.assertEqual(
                quality["recognized_emitted_cells"]
                + quality["unresolved_emitted_cells"],
                quality["emitted_non_space_cells"],
            )
            self.assertAlmostEqual(
                quality["unresolved_among_emitted_fraction"],
                quality["unresolved_emitted_cells"]
                / quality["emitted_non_space_cells"],
            )
            self.assertTrue(quality["tesseract_version"].startswith("tesseract "))
            self.assertIn("do not measure omitted source glyphs", quality["acceptance_note"])
            if quality["tesseract_version"] == "tesseract 5.5.1":
                self.assertEqual(quality["emitted_non_space_cells"], 78)
                self.assertEqual(quality["unresolved_emitted_cells"], 40)
                readme = (ROOT / "README.md").read_text()
                self.assertIn("40 unresolved `?` cells among 78 emitted", readme)
                observed = readme.split("<!-- observed-output-start -->", 1)[1]
                observed = observed.split("<!-- observed-output-end -->", 1)[0]
                observed = observed.split("```text\n", 1)[1].rsplit("\n```", 1)[0]
                expected_lines = [line.rstrip() for line in machine_text.splitlines()]
                while expected_lines and not expected_lines[-1]:
                    expected_lines.pop()
                self.assertEqual(observed, "\n".join(expected_lines))
                generated_gif = Path(parent) / "screenshot-to-txt-comparison.gif"
                generated_receipt = (
                    Path(parent) / "screenshot-to-txt-comparison.receipt.json"
                )
                subprocess.run(
                    [
                        "python3",
                        str(ROOT / "scripts/generate_visual_evidence.py"),
                        "--source",
                        str(ROOT / "sample/source.normalized.png"),
                        "--machine-output",
                        str(output / "machine-ocr.txt"),
                        "--quality",
                        str(output / "quality.json"),
                        "--calibration",
                        str(ROOT / "sample/calibration.json"),
                        "--gif",
                        str(generated_gif),
                        "--receipt",
                        str(generated_receipt),
                    ],
                    check=True,
                )
                self.assertEqual(generated_gif.read_bytes(), VISUAL_GIF.read_bytes())
                generated = json.loads(generated_receipt.read_text())
                packaged = json.loads(VISUAL_RECEIPT.read_text())
                self.assertEqual(generated, packaged)

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
            "EXPERIMENTAL — 40 unresolved / 78 emitted; source coverage unknown",
        )
        self.assertEqual(receipt["acceptance_status"], "experimental_unaccepted")
        self.assertEqual(
            receipt["source_coverage_status"],
            "unknown_without_accepted_transcript",
        )
        self.assertEqual(receipt["source_sha256"], source_hash)
        self.assertEqual(
            receipt["machine_output_sha256"],
            "d74fea7577fa486b4a016aea023d95c2cab42a81b23e00c93ba6cd011527d7d6",
        )
        self.assertEqual(
            receipt["quality_receipt_sha256"],
            "e0beab20f939d65c31684ff432d1e5e766b789238ec535584468e17faf0559e5",
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

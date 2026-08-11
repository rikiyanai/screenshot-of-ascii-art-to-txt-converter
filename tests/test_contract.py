from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


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

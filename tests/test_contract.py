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
                {"machine-ocr.txt", "tesseract-boxes.json", "calibration.json"},
            )
            self.assertEqual(
                len((output / "machine-ocr.txt").read_text().splitlines()),
                22,
            )

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

from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class BundledSampleContract(unittest.TestCase):
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

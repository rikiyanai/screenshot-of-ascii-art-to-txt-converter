# Dependencies and attribution

The standalone package contains no vendored third-party source. Its runtime
dependencies are installed separately:

| Dependency | Tested/pinned version | License | Upstream |
| --- | --- | --- | --- |
| Python | 3.11+ | PSF-2.0 | <https://www.python.org/> |
| NumPy | 2.4.1 | BSD-3-Clause | <https://numpy.org/> |
| Pillow | 12.1.0 | HPND | <https://python-pillow.github.io/> |
| Tesseract OCR | 5.5.1 tested | Apache-2.0 | <https://github.com/tesseract-ocr/tesseract> |

`requirements.txt` pins the two Python packages used by the recovery script.
Tesseract is an external executable and is checked by `run-sample.sh` before
the output directory is created.

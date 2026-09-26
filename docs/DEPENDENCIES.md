# Dependencies and attribution

The package vendors one third-party asset, the Saitamaar typeface
(`fonts/Saitamaar-Regular.ttf`, SIL OFL 1.1, licence in
`fonts/Saitamaar-OFL.txt`, from <https://github.com/asciiart-development/SaitamaarFont>
at commit `695bee7`, sha256 `8f8c9b6e…a35890`). The proportional decoder uses it
as its glyph and advance model. Other runtime dependencies are installed
separately:

| Dependency | Tested/pinned version | License | Upstream |
| --- | --- | --- | --- |
| Python | 3.11+ | PSF-2.0 | <https://www.python.org/> |
| NumPy | 2.4.1 | BSD-3-Clause | <https://numpy.org/> |
| Pillow | 12.1.0 | HPND | <https://python-pillow.github.io/> |
| fontTools | 4.62.1 | MIT | <https://github.com/fonttools/fonttools> |
| Tesseract OCR | 5.5.1 tested | Apache-2.0 | <https://github.com/tesseract-ocr/tesseract> |

`requirements.txt` pins the Python packages used by the recovery scripts.
Tesseract is an external executable and is checked by `run-sample.sh` before
the output directory is created.

# Screenshot of ASCII Art to TXT Converter

Experimental converter for turning screenshots of fixed-grid ASCII art back into text.

The converter measures a character grid, uses Tesseract box data, and writes `?` when it cannot identify a cell. It does not guess missing glyphs.

On the bundled sample with Tesseract 5.5.1, 40 of 78 emitted non-space cells remain unresolved. That count does not include source characters that OCR may have missed entirely, so total source coverage is unknown.

![Bundled screenshot compared with the fixed-grid text result](docs/screenshot-to-txt-comparison.gif)

The GIF shows the source screenshot beside the current text result, followed by enlarged matching regions. It is a README comparison, not evidence that the converter is generally accurate.

## Run the bundled sample

Requirements: Python 3.11+, Tesseract, NumPy, and Pillow.

```sh
python3 -m pip install -r requirements.txt
./run-sample.sh /tmp/screenshot-of-ascii-art-to-txt-converter-output
```

The output directory must not already exist. A successful run creates:

- `machine-ocr.txt`
- `tesseract-boxes.json`
- `calibration.json`
- `quality.json`

The bundled horse-sheet sample produces a 22-row text grid. Question marks mark unresolved cells.

## Current bundled result

Source image:

![Horse animation sheet source raster](sample/source.normalized.png)

Observed Tesseract 5.5.1 output on 2026-08-12, with trailing blank cells omitted here:

```text

    [/\ ?  _ ?
     ?? ? ? )\??
     ? ?  ||? \???
        \    \


    ((??=__
    | /\   ? ?
       (  /  \  ? ?
       / |????/  \  ??
     /    \ /      \


    ? ?\
    ? ?  ?  ?
      (       ?
     ?-\??? [\  \
        ? ?_   ?
```

This output is still an OCR candidate, not an accepted reconstruction.

## Repository contents

This repository contains the converter, one bundled sample image, calibration data, tests, and the comparison GIF. It does not include the larger LateLetter application or unrelated application data.

See [docs/provenance.md](docs/provenance.md) for source information and [docs/DEPENDENCIES.md](docs/DEPENDENCIES.md) for runtime dependencies and licenses.

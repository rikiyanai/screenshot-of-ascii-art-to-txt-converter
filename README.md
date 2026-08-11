# LateLetter Fixed-Grid ASCII Recovery

Private standalone extraction of LateLetter's fail-closed raster-to-ASCII
recovery tool. It measures a fixed character lattice, records Tesseract box
evidence, and writes `?` for unresolved cells instead of inventing glyphs.

## Run the bundled sample

Requirements: Python 3.11+, Tesseract, NumPy, and Pillow.

```sh
python3 -m pip install -r requirements.txt
./run-sample.sh /tmp/lateletter-fixed-grid-ascii-output
```

The output directory must not already exist. A successful run creates:

- `machine-ocr.txt`
- `tesseract-boxes.json`
- `calibration.json`

The bundled horse-sheet sample produces 22 text rows. The result remains a
machine candidate; question marks are explicit unresolved cells.

## Boundary

This repository contains only the recovery script, one hash-bound sample image,
its calibration, the wrapper, and focused tests. It excludes the LateLetter
product, transcription pipeline, session history, caches, and unrelated data.

See [docs/provenance.md](docs/provenance.md) for the source identities.

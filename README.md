# LateLetter Fixed-Grid ASCII Recovery

Private standalone extraction of LateLetter's fail-closed raster-to-ASCII
recovery tool. It measures a fixed character lattice, records Tesseract box
evidence, and writes `?` for unresolved cells instead of inventing glyphs.

**Status: acceptance hold.** This is an experimental OCR candidate generator,
not a completed ASCII recovery. With Tesseract 5.5.1, the 2026-08-12 re-audit
observed 40 unresolved `?` cells among 78 emitted non-space positions. That
output-only denominator cannot measure source glyphs omitted as blanks, so
source coverage remains unknown. The prior GIF was removed because it showed
shell commands and output rather than a human-judgeable recovery result.

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
- `quality.json`, which records emitted-output statistics, the Tesseract
  version, and an explicit `unknown_without_accepted_transcript` source-coverage
  state

The bundled horse-sheet sample produces 22 text rows. The result remains a
machine candidate; question marks are explicit unresolved cells.

## Judge the bundled result

The actual standalone product is the fixed-grid recovery candidate below: a
source raster goes in and a fail-closed 22-by-37 text grid comes out. It is not
the LateLetter application, and a shell transcript is not its acceptance
surface.

Bundled source:

![Horse animation sheet source raster](sample/source.normalized.png)

Observed Tesseract 5.5.1 output on 2026-08-12, with trailing blank grid cells
omitted from this display only:

<!-- observed-output-start -->
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
<!-- observed-output-end -->

This comparison is deliberately not labelled a pass. `quality.json` is the
machine-readable execution receipt; only an accepted transcript plus explicit
source-versus-output judgment could establish recovery quality.

## Boundary

This repository contains only the recovery script, one hash-bound sample image,
its calibration, the wrapper, and focused tests. It excludes the LateLetter
product, transcription pipeline, session history, caches, and unrelated data.

See [docs/provenance.md](docs/provenance.md) for source identities and
[docs/DEPENDENCIES.md](docs/DEPENDENCIES.md) for the pinned runtime dependency
and license map.

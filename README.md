# Screenshot of ASCII Art to TXT Converter

Experimental converter for turning screenshots of fixed-grid character art back into text.

Nothing about the source is assumed. The converter measures the character lattice
from the image, infers the typeface and size by fitting a library of monospaced
fonts to that measured cell, and decides every cell by a recorded score. A cell is
written only when its best candidate beats the runner-up by a recorded margin;
otherwise it is `?`. It does not guess missing glyphs.

No cell aspect is built in. 1:1, 1:2 and 16:29 are all just fits, and the measured
aspect is reported in the receipt.

Tesseract is no longer used by default. It stays reachable through
`--engine tesseract` for comparison only, because it classifies against an
unbounded prose alphabet with no score — which is how earlier versions of this
tool emitted letters, an em dash and a euro sign on art containing no letters at
all.

## What the numbers are

Accuracy is measured two ways, because they answer different questions.

**Round-trip on synthetic sheets, where the source font is installed.** These
render text the pipeline has never seen, at a cell geometry it is not told, and
demand the characters back. Measured with Menlo on 2026-09-21:

| Sheet | Cell | Exact | Ambiguous | Reconstruction IoU | Typeface recovered |
|---|---|---|---|---|---|
| line art | 11 x 22 (1:2) | 40/40 (100%) | 0 | 0.992 | Menlo @ 19 |
| code | 8 x 9 (near square) | 27/29 (93%) | 0 | 0.866 | Menlo @ 13 |
| line art | 16 x 29 | 40/40 (100%) | 0 | 1.000 | Menlo @ 27 |

The typeface and size are recovered correctly in each case, which is the part
that proves the machinery rather than the fixture.

**A real screenshot with an operator transcript.** This is the strongest
evidence: a screen capture, not a render, scored against a transcript supplied by
hand. Measured 2026-09-21 on `sample/bonsai.source.png`:

- **54 of 67 characters exact (80.6%)**, 1 ambiguous
- measured lattice 15.72 x 30.42 px, aspect 0.5168, inferred Menlo @ 26
- reconstruction agreement, ink IoU: 0.605

The remaining errors are reference-typeface errors, not structural ones: `=`
read as `-`, `#` as `=`, a trailing `_` lost to a space. The lattice and the
layout are right; the glyph shapes are approximated by the nearest installed
face.

That run also validates the self-check. Forcing Courier instead of the fitted
Menlo gives a *lower* agreement (0.544 against 0.605) and a *lower* true
accuracy (67.2% against 80.6%), so the reported IoU ranked the two fits in the
same order as the ground truth. The receipt's agreement figure is a usable proxy
for accuracy when no transcript exists.

Add more pairs by dropping `<name>.source.png` and `<name>.expected.txt` into
`sample/` and extending `PAIRS` in `tests/test_roundtrip.py`. The suite gates
every pair at 75% exact.

**The bundled sample, where the source font is not installed.** The other sample is
Stone Story RPG art. Its typeface is a custom unnamed face that is not publicly
downloadable, so the fit necessarily lands on the nearest installed
approximation. No transcript has been supplied for this image, so no exact
accuracy can be quoted for it — only the self-consistency figures:

- measured lattice 11.560 x 21.510 px, aspect 0.5374, 37 columns
- inferred typeface SFNSMono @ 18px, residual 12.49
- 106 of 106 ink-bearing cells resolved
- reconstruction agreement, ink IoU: 0.557

An IoU of 0.557 is the honest signal that the reference typeface does not match
the source. Treat the bundled result as a candidate, not a reconstruction.

**Known gap.** On the bundled sample the run reports zero ambiguous cells despite
that 0.557 agreement. The margin threshold is not yet calibrated against a
reference-font mismatch, so it is not yet refusing cells it should refuse. Do not
read "0 ambiguous" as confidence.

## Run the bundled sample

Requirements: Python 3.11+, NumPy, and Pillow. Tesseract is not required.

```sh
python3 -m pip install -r requirements.txt
./run-sample.sh /tmp/screenshot-of-ascii-art-to-txt-converter-output
```

The output directory must not already exist. A successful run creates:

- `machine-ocr.txt` — the recovered grid
- `quality.json` — measured lattice, inferred typeface, coverage, agreement
- `cell-decisions.json` — per-cell best, runner-up, margin, ink and state
- `reconstruction.png` — the recovered text re-rendered at the measured lattice

The bundled calibration file is passed as a **prior only**. The lattice is
measured from the image, and the receipt records how far the measurement fell
from the declaration.

## Current bundled result

Source image:

![Horse animation sheet source raster](sample/source.normalized.png)

Observed on 2026-09-21:

<!-- observed-output-start -->
```text
   ,--_
   |/\ =_ _ ~
    _( )_( )\~~
    \,\  _|\ \~~~
       \`   \
       `    `

   ((^--__
   | /\  --___ __
      (  /  \  ) \\
      / |~~~~/  \  \\
    /    \ /      \

    ,
   /,`\
   ` | \____\\
    _(      ) \
    \-\~~~_|\  \
       \ `   \  `
       `     `
```
<!-- observed-output-end -->

This output is a machine candidate, not an accepted reconstruction.

## Proportional (Shift_JIS) art

`recover_monospace_ascii.py` refuses art set in a proportional face, because no
single advance describes it. `scripts/recover_proportional_aa.py` decodes it
instead, assuming the art was set in Saitamaar (the MS PGothic-metric face that
2ch/5ch art viewers use, vendored under `fonts/`). Each row is decoded by
dynamic programming over the pen positions that the font's advance table
allows. The font size, line pitch, text-box origin and row baselines are all
fitted from the image and recorded in `quality.json`. It also needs fontTools
(pinned in `requirements.txt`).

```sh
python3 scripts/recover_proportional_aa.py sample/proportional/madonna.source.png OUT
python3 scripts/score_against_key.py OUT/recovered.txt sample/proportional/madonna.expected.txt
```

On the one real screenshot with an answer key, 22 of 24 rows come out exact and
the character error rate is 0.56%. That comparison ignores the order of spaces
within a blank run, which the pixels do not determine. The strict character
error rate is 1.61%. This is one sample in one face, so the result is
experimental and unaccepted. See `docs/receipts/2026-09-26-proportional-madonna/`.

## Coverage accounting

Coverage is measured against ink-bearing source cells, never against the tool's
own output. An earlier version reported "16 of 78 emitted cells unresolved",
which divided the output by itself and hid 43 source cells that had been dropped
to spaces without ever being scored. A space inside the ink region is now a
scored decision that the blank template won.

## Repository contents

This repository contains the converter, one bundled sample image, calibration
data, tests, and the comparison GIF. It does not include the larger LateLetter
application or unrelated application data.

The comparison GIF in `docs/` still shows the old Tesseract-era result and needs
regenerating.

See [docs/provenance.md](docs/provenance.md) for source information and
[docs/DEPENDENCIES.md](docs/DEPENDENCIES.md) for runtime dependencies and licenses.

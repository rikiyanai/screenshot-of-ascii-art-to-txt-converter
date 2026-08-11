# Failure Log

## P0C-01 · 2026-08-11 — standalone recovery extraction created

- Copied only the reviewed recovery script, hash-bound calibration, and sample.
- Two contract tests and the real 22-row sample passed.
- The real-path terminal recording and user acceptance remained open.

## P0C-01 · 2026-08-12 — publication package completed

- Pinned the Python dependency versions and documented dependency licenses.
- Added a real terminal recording linked from the README.
- Automated execution is verified; user judgment of the OCR candidate remains
  a distinct acceptance gate.

## P0C-01 · 2026-08-12 — acceptance re-audit revoked visual proof

- Intended product: a standalone fixed-grid raster-to-ASCII recovery whose
  output can be judged against the bundled source sheet.
- Observed result: the command executes and produces the three promised files,
  but the sample contains 40 unresolved `?` cells among 78 non-space cells.
- The deleted GIF only typed the wrapper command and printed 22 output rows. It
  was not a TUI and did not make source-versus-recovery quality judgeable.
- Highest supported stage: **Executed experimental candidate**, not Verified or
  Accepted. A replacement proof must show the source and recovered grid at a
  readable scale and preserve the unresolved-cell count.
- The rejected `.tape` recipe was deleted because running it would recreate the
  invalid proof without first satisfying that product and judgment surface.

## P0C-01 · 2026-08-12 — first quality-receipt patch did not apply

- The first patch expected the README phrase `The command refuses...`; the file
  actually says `The output directory must not already exist`. `apply_patch`
  rejected the whole patch before changing any file.
- No product or test conclusion was taken from that failed edit. The successor
  uses the inspected current README context.

## P0C-01 · 2026-08-12 — product-quality evidence separated from execution tests

- The original five tests could all pass while 40 of 78 non-space cells remained
  unresolved because they checked artifacts, hashes, dependencies, and refusal
  behavior only.
- `run-sample.sh` now writes `quality.json` with the measured unresolved count,
  fraction, and explicit `experimental_unaccepted` state. The sample test pins
  that honest receipt instead of treating artifact production as recovery proof.
- No quality threshold was invented. Completed recovery remains unproved until a
  threshold and source-versus-output operator judgment are explicitly owned.

## P0C-01 · 2026-08-12 — first quality receipt used an invalid coverage denominator

- The first `quality.json` draft named 40 unresolved cells divided by 78
  non-space output cells an `unresolved_fraction`. That denominator contains
  only characters Tesseract emitted; it cannot count source glyphs that OCR
  omitted as blanks and therefore cannot measure recovery coverage.
- The broader LateLetter research attempt 064 emits 105 non-space cells for the
  same raster but remains rejected with 17 unknown cells. It is not accepted
  ground truth and is outside this standalone boundary, but it falsifies any
  interpretation of the simple tool's 78 emitted cells as complete source
  coverage.
- The failed field names and exact-count test are not acceptance evidence. The
  successor must label them as emitted-output statistics, state that source
  coverage is unknown without an accepted transcript, and expose the source and
  observed output together for human judgment.

## P0C-01 · 2026-08-12 — full-resolution preview injection was rejected

- The first direct image-inspection call was blocked by the environment because
  it would have injected inline image bytes into the work context. It did not
  inspect or change the product.
- The successor used the environment-generated bounded preview of the same
  SHA-256-pinned PNG. The preview visibly confirmed that the old terminal GIF
  was not a source-versus-output proof.

## P0C-01 · 2026-08-12 — emitted-output receipt and judgment surface verified

- The original P0C-01 audit at parent commit `d4746d0` was re-read before this
  repair. It explicitly selected `scripts/recover_monospace_ascii.py`, the
  horse-sheet raster, and its calibration while excluding the LateLetter app
  and broader transcription subsystem. The standalone boundary was therefore
  preserved rather than rewritten to match the repository name.
- Receipt schema v2 records the 22-by-37 grid, emitted recognized/unresolved
  cells, Tesseract version, and
  `source_coverage_status=unknown_without_accepted_transcript`. It no longer
  presents an output-only denominator as source coverage.
- The README now places the SHA-256-pinned source raster beside the observed
  Tesseract 5.5.1 text result. It explicitly refuses pass status and does not
  replace product-specific judgment with a terminal recording.
- Five contract tests pass and a direct wrapper run writes all four artifacts.
  The observed receipt remains 40 unresolved among 78 emitted non-space cells;
  omitted-source coverage is unknown. Highest supported stage: Executed
  experimental candidate. Recovery is not Verified or Accepted.
- Code review passed at 8.2/10 and identified two non-blocking drift risks. The
  successor now rejects a non-rectangular output grid and, when the tested
  Tesseract version is exactly 5.5.1, checks the README observation and displayed
  transcript against the live generated output.

## P0C-01 · 2026-08-12 — first README drift check exposed extra blank rows

- The first test run after adding mechanical README comparison failed one of
  five tests. The hand-pasted display contained one extra blank row in each of
  two inter-frame gaps, so it was not the same row sequence as the live 22-row
  machine output.
- The nonblank glyph lines and 40/78 counts matched, but visual similarity is
  not byte fidelity. The failed README display is not retained as proof; the
  successor removes the two extra rows and reruns the full contract suite.
- The corrected display now matches every generated row after right-trimming
  blank grid columns and omitting only the three trailing all-blank rows. All
  five tests pass, including the version-gated README drift assertion.
- Round-two code review passed at 8.8/10 after those corrections, with
  correctness, surface fidelity, security, tests, and idempotency each scored
  9/10. The review did not upgrade the recovery stage or supply acceptance.

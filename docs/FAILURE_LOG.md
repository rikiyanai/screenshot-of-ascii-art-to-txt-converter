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

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

## P0C-01 · 2026-08-12 — missing product-specific visual evidence

- Intended product: `screenshot-of-ascii-art-to-txt-converter`, an experimental
  calibrated fixed-grid screenshot-to-TXT converter. It is not a general OCR
  system and has no accepted recovery claim.
- Observed mismatch: after the invalid command-entry recording was removed, the
  README exposed the source and output only as separate static blocks. It had no
  GIF that kept the exact bundled source and exact `machine-ocr.txt` result
  visible together, no matched close-ups, and no always-visible quality HOLD.
- Consequence: execution and text drift tests existed, but the README still
  lacked a human-judgeable visual artifact for the product's actual
  screenshot-to-TXT transformation. The prior 5/5 test result did not prove
  that missing visual acceptance surface.
- Successor requirement: generate a reproducible GIF with no shell interaction;
  bind its frames and receipt to the exact source/output hashes, grid dimensions,
  quality receipt, matched crop regions, and the explicit
  `EXPERIMENTAL — 40 unresolved / 78 emitted; source coverage unknown` label.
  Inspect the rendered artifact before linking it. Highest current stage remains
  **Executed experimental candidate**; recovery is neither Verified nor
  Accepted.
- Canonical FL4512 attempt accounting and overlays live in the parent research
  checkout, whose tooling is not packaged in this standalone repository. This
  repository records the local corrective attempt without pretending its local
  log is that canonical ledger.

## P0C-01 · 2026-08-12 — first comparison GIF used unsupported display glyphs

- The first four-frame render completed at 1400×860, but contact-sheet
  inspection showed missing-glyph boxes where Pillow's packaged default font
  could not draw the em dash, arrow, multiplication sign, middle dot, and en
  dash used in labels. The source and machine-output glyphs were readable, but
  the mandated HOLD label was not rendered exactly enough for evidence use.
- That first GIF hash, `60b04d684e772c8ace677b584694a1d8aaeadb9043574faaf8fab7b2b2a0f92d`,
  is rejected. Its existence and generator success are not a visual pass.
- Successor: keep the dependency-free packaged font, replace incidental label
  typography with ASCII, and draw the required em-dash mark explicitly between
  the HOLD label segments. Regenerate and visually inspect all four frames.

## P0C-01 · 2026-08-12 — second comparison GIF cleared repeated header pixels

- The second render removed the unsupported-glyph boxes and hash-bound all four
  frames, but frame-by-frame decoding showed that GIF disposal mode 2 cleared
  unchanged header pixels after frame one. The long-dash mark and other repeated
  HOLD text were therefore not reliably visible throughout playback even though
  each pre-encoding canvas contained them.
- Hash `799b0be764636dd2b2301c0510a0eb1391478f27cf747e049961134d0a72999b`
  is rejected. The successor uses preservation disposal and must pass a decoded
  pixel-equality check for the complete 116-pixel header on every frame.

## P0C-01 · 2026-08-12 — preservation alone did not equalize frame palettes

- Disposal mode 1 made the complete HOLD visibly survive decoded playback, but
  the planned header equality check still found small antialias colour changes.
  Each frame had been independently quantized to a different GIF palette, so
  equal pre-encoding header pixels did not decode to equal RGB values.
- Hash `5616031583cc4654f251ff46501a13ea9220c0166b382dd3cdc80dcb90bf4bd0`
  is rejected as the bound artifact. The successor quantizes every semantic
  frame through the first frame's shared palette before rerunning the decoded
  header invariant.

## P0C-01 · 2026-08-12 — exact RGB equality was an over-strict GIF invariant

- Shared-palette hash `175c6fc1e701e18762dd575beeda88dadf9e4ddb222f0dac8bf9474de268caef`
  still decoded repeated antialiased header pixels with one-to-seven-level RGB
  differences after GIF delta encoding. Direct frame inspection showed the
  complete HOLD in all four frames; the varying values were palette rounding,
  not missing label geometry or content.
- Exact RGB equality therefore measured encoder colour assignment rather than
  the acceptance condition. The successor keeps the shared palette, verifies
  the identical HOLD foreground bounds on each decoded frame, bounds foreground
  pixel-count drift to antialias-edge pixels, and separately enforces the exact
  label text through the receipt and deterministic generator.

## P0C-01 · 2026-08-12 — first repository rename preflight used a reserved zsh name

- The first read-only target-name probe stopped after confirming the current
  GitHub repository is private with default branch `main`. Its shell tried to
  assign the target probe's exit code to zsh's read-only `status` parameter.
- No repository, remote, directory, or tracked file was renamed by that failed
  preflight. The successor uses a task-specific variable, repeats the target
  absence check, and mutates only after all identities converge.

## P0C-01 · 2026-08-12 — product-specific visual evidence and rename verified

- GitHub repository `rikiyanai/screenshot-of-ascii-art-to-txt-converter` is
  private with default branch `main`. The local checkout and `origin` use the
  same exact name; the old local path is absent. No commit or push was performed
  during the rename or this evidence repair.
- The README now names the actual product and qualifies it immediately as an
  experimental one-sample converter. Its linked GIF contains no shell command
  entry: one full input/output frame and three calibrated matched close-ups keep
  the HOLD visible throughout.
- Final GIF: 1400×860, four frames, durations 4200/3600/3600/4200 ms, 139271
  bytes, SHA-256
  `175c6fc1e701e18762dd575beeda88dadf9e4ddb222f0dac8bf9474de268caef`.
  It binds source SHA-256
  `9ea8eab2c0b378ed89ad2337515a6baea4ec81d0eace6ba042fab4abee63a3d3`
  to generated output SHA-256
  `d74fea7577fa486b4a016aea023d95c2cab42a81b23e00c93ba6cd011527d7d6`.
- The actual wrapper, deterministic GIF regeneration, all four decoded semantic
  frames, local README links, compile check, security scan, old-slug scan, and
  6/6 contract tests pass. Direct inspection covered the overview and every
  close-up.
- Highest supported state: **visual evidence Verified; converter remains an
  Executed experimental candidate**. Forty of 78 emitted non-space cells remain
  unresolved, source coverage remains unknown, and recovery is not Accepted.

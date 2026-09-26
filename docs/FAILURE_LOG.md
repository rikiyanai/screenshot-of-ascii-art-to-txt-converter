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
## P0C-01 · 2026-08-12 — first renamed-repository push correctly rejected concurrent README work

- Push of local visual-proof commit `750016a` was rejected as non-fast-forward.
  The renamed private remote had advanced from `dcc50d3` to user-authored
  `f8c17a8`, which adds the screenshot-to-text motivation to `README.md`.
- No force push or overwrite is permitted. The successor must preserve that
  remote motivation, integrate the local experimental/HOLD qualification and
  GIF proof on top, rerun all contracts, and push only a fast-forward history.

## P0C-01 · 2026-08-12 — concurrent README motivation preserved

- The local proof history was rebased onto user commit `f8c17a8`. The README
  keeps the user's online/Instagram screenshot motivation, adds the exact
  requested repository identity, and retains the one-sample experimental/HOLD
  boundary beside the source/output GIF.

## P0C-01 · 2026-08-12 — conflict wording had to preserve the user's exact text

- The post-rebase failure-log wording overstated the conflict resolution as if
  the agent-owned README wording were the source of truth. The acceptance
  surface is the user-authored `f8c17a8` heading and motivation paragraph:
  `Screenshot-of-ascii-art to actual ascii art txt converter pipeline.` and
  the online/Instagram screenshot motivation.
- The successor keeps those exact README lines from `f8c17a8` intact, leaves
  the experimental/HOLD proof below them, and confirms the README contains no
  redundant private-visibility wording.

## P0C-02 · 2026-09-20 — custom-font-informed recovery gap opened

- GitHub issue: https://github.com/rikiyanai/screenshot-of-ascii-art-to-txt-converter/issues/2
- Intended product: screenshot capture should let the user save ASCII art seen
  anywhere online as editable text, whether the source is a message reaction,
  an explore-page post, a tutorial plate, or another screenshot source.
- Observed mismatch: this repository still has only an executed experimental
  candidate. The prior Tesseract-first fixed-grid path left unresolved emitted
  cells, unknown source coverage, and no accepted broad screenshot recovery.
- New hypothesis: recovery needs to be custom-font-informed. The Stone Story
  tutorial reference matters because its font is a custom Courier Sans-derived
  family with small grid-aligned sizes, so glyph metrics and font dimensions
  can become segmentation/classification evidence instead of generic OCR noise.
- Optional integration: evaluate JEV only if it improves glyph identification,
  alignment, review, or receipt quality without hiding unknown cells.
- Acceptance remains open until multiple screenshot sources produce useful TXT
  candidates with receipts that record font-model assumptions, segmentation
  parameters, unknown cells, omitted-source risk, and a human-judgment surface.

## P0C-03 · 2026-09-21 — ASCII emission widened past punctuation; 16/78 still unaccepted

- Cause measured, not guessed: of the 40 `?` cells, the dominant class was
  single-cell unconflicted Tesseract boxes outside the punctuation safe set
  (letters, digits, `~`, `%`, `,`, `1`), plus 4 multi-cell boxes, 4 conflicts,
  and non-ASCII recognitions (em dash, euro). Font-template matching (DejaVu,
  Courier New) and per-cell Tesseract psm-10 both scored ~0 agreement with
  Tesseract on safe cells at 12px glyph size, so neither is the classifier.
- Fix: `scripts/recover_monospace_ascii.py` now emits single-cell
  unconflicted ASCII letters, digits, and common punctuation (`EMITTABLE_EXTRA`);
  non-ASCII stays `?` (output contract is ASCII text). Conflict, width, and
  out-of-grid rules unchanged. Receipt records the policy in
  `emission_policy` (output `calibration.json`).
- Result on the bundled sample (Tesseract 5.5.1): 16/78 emitted cells
  unresolved, down from 40/78. Still `experimental_unaccepted`: 16 remain
  (conflicts, wide boxes, non-ASCII, unboxed ink) and source coverage stays
  unknown without an accepted transcript. Blank-but-inked cells (omitted
  source) remain the open gap; neither template nor psm-10 recovers them.
- Collateral honesty repairs: the README wording pin and observed-output
  markers had drifted at HEAD (suite already red); both restored against the
  new output, and the evidence GIF is remapped through one shared palette so
  the common header quantizes identically on all frames (was: frame-0
  unsnapped, 34px spread against a 10px gate).
- Highest stage: Executed improved candidate, not Verified or Accepted. Issue
  #2 acceptance (multiple screenshot sources judged) remains open.

## P0C-04 · 2026-09-24 — fixed-pitch assumption falsified by Shift_JIS art; regime detector and harmonic fix

- Trigger: the user supplied archived Shift_JIS art. It falsifies the
  one-advance-per-glyph assumption for proportional-font art, and the pipeline
  had no way to notice. It cut a lattice anyway and reported a confident,
  meaningless result. Fixture source: `sample/regime/cjk-render.json` (18 rows
  from the Index-Librorum-Prohibitorum page).
- Fix 1 (`b0bd44c`): `detect_regime()` runs between `measure_lattice()` and
  `cut_cells()`. It uses only the image. Per ink band it gives each run-boundary
  gap a whole number of cells and accumulates the SIGNED residual, so that a
  systematic error accumulates and does not cancel. Bands come from ink, not
  from the row lattice.
- Paired fixtures: the same 18 rows rendered through Osaka (proportional, 30
  advances) and OsakaMono (fixed pitch, 2 advances). Metrics are the only
  variable, so a detector that fires on CJK codepoints cannot pass. Measured
  23.91 vs 0.56 cells.
- Refusal exits 2 and emits no text; `--on-proportional warn` overrides.
  Receipt schema `fixed_grid_recovery.v4` records the verdict on every run.
- Fix 2 (`49d4f39`): `measure_lattice` locked onto period harmonics. Spectral
  projection gave half the true advance and autocorrelation gave twice the line
  pitch (9.641 px / 22 px rendered, 4.82 / 44.6 measured). `resolve_harmonic()`
  scores {p/3, p/2, p, 2p, 3p} and takes the finest period within 70% of the
  best score. Period accuracy over 90 sheets: 94.4%/90.0% at 0.90, 96.7%/92.2%
  at 0.70, 92.2%/86.7% at 0.60. `tests/test_lattice.py` renders dense, prose,
  and sparse sheets because sparse real art hid the defect.
- The detector took the WORSE of the two boundary sequences. It now takes the
  better one: fixed-pitch CJK went from 0.56 to 0.375, and proportional did not
  change.
- Threshold moved 0.75 -> 0.50 after recalibration against the shipped code.
  False refusal is flat across 0.50, 0.60, and 0.75, so 0.50 removes fifteen
  points of false acceptance at no cost. Below 0.50, refusal triples. Margins:
  Stone Story 2.63x, bonsai 1.88x, fixed-pitch CJK 1.33x, proportional CJK
  refused at 0.03x.
- Test evidence (2026-09-26): `python3 -m pytest -q` gave 36 passed, 6 subtests
  passed, in 506 s. Only the test suite ran. No new screenshot run was done.
- Open: fixed-pitch CJK is dual-period and sits near the threshold. It needs a
  third regime, not a better threshold. Proportional art is refused, not
  converted. Issue #2 remains open.
- Highest stage: **Executed**, not Verified or Accepted.
- Provenance: the originating Claude session transcript no longer exists on
  disk. The only local copy is the current session
  `b91a27b9-886b-4482-a0a0-f9c2be89f42b`. Commits `b0bd44c` and `49d4f39` are
  the durable record.
- Next: a new proportional Shift_JIS screenshot with an answer key (added
  2026-09-26) is the target for proportional-aware recovery. It is logged as a
  separate entry.

## P0C-05 · 2026-09-26 — proportional Shift_JIS art decoded instead of refused

- Input: a real 2x retina screenshot of proportional art plus its source text,
  both supplied by the user:
  `sample/proportional/madonna.source.png` (sha256 `b0a6c7f1…f8562cd`) and
  `madonna.expected.txt` (24 rows).
- Baseline: `recover_monospace_ascii.py` refused it (exit 2, median band drift
  3.85 cells against a 0.50 threshold). 0 characters recovered.
- Typeface identified, not assumed. The leading-whitespace fit gave a half/full
  space ratio of 0.49, which rules out fixed pitch. The right-edge residuals of
  a two-width model reached 33 px, which rules out dual pitch as well. No
  installed CJK face correlated above 0.44. Saitamaar (MS PGothic metrics, OFL,
  now vendored under `fonts/`) correlated 0.94 at 22 px; IPAGP-Mona reached
  0.66. Rendering the key in Saitamaar at 22 px, origin x=6 and a 24 px pitch
  reproduces the screenshot at cosine 0.976.
- New `scripts/recover_proportional_aa.py`: per-row DP over pen positions on
  the font's advance lattice (gcd of the advances, 80 units). Glyphs are
  rendered at 1/8 px phases and each owns the columns inside its advance, so
  the path cost is the whole-row reconstruction error. Two U+0020 in a row are
  forbidden, and blank runs are written in one canonical order. Size, pitch,
  origin and baselines are all fitted from the image. The origin comes from
  the container rule.
- Two geometry faults were found and fixed on the way:
  (1) Walking baselines greedily from the first ink merged lines, because row 0
  holds only `_ ＿` and its first ink is at the baseline. Now one global
  lattice is fitted.
  (2) The origin fit is a plateau: shifting by any legal space run explains
  the ink equally well, and it picked +6.875 px (one half space). Now the
  smallest origin on the plateau is taken.
  Per-line ±1 px baseline refinement was measured worse (19 vs 22 exact rows)
  and was removed.
- Result (receipt `docs/receipts/2026-09-26-proportional-madonna/`): the size
  was fitted automatically to 22.0 px (normalised cost 0.155 against 0.254 at
  the next size). 24/24 rows; 22/24 rows exact under spacing-canonical
  comparison; canonical CER 0.56%; strict CER 1.61%. Strict error is mostly
  the order of spaces inside blank runs. The key itself is not consistent
  about that order, and the order does not reach the pixels.
- Remaining real errors:
  row 20: `.::: !` read as `.:: .!` (same width; the colon's upper dot was
  lost).
  row 23: `/　|　'` read as `/ ｜ '`. Both come to 2080 units with the bar in
  the same place, so the pixels cannot tell them apart and it needs a
  corpus prior.
- Tests: `tests/test_proportional.py` gates on ≥22 exact rows and canonical
  CER ≤1% at the fitted size. It also checks that no canonical blank run ever
  has two adjacent U+0020.
- Limits: one screenshot, one face, one renderer (macOS). The full automatic
  run takes about 4 minutes, mostly in the size sweep. The face is not fitted
  from a library: Saitamaar is the only model. The monospace tool still
  refuses and now points to the new decoder; nothing routes between the two
  automatically.
- Highest stage: **Executed** against one answer key. Not Verified across
  sources, not Accepted. Issue #2 remains open.

## P0C-06 · 2026-09-26 — shared ASCII-art archive approved; AAHub corpus available

- Audit (subagent, 2026-09-26) recommended a standalone PRIVATE archive
  repository instead of placing it in asciicker-Y9-2. Reasons: visibility
  mismatch (Y9-2 private, consumers public); Y9-2 history is 23.5 GiB with LFS
  banned; no licence/provenance owner; 442 of 525 indexed files live only in
  ~/Downloads, ~/Pictures or ~/Desktop.
- User decision (2026-09-26): approved. Create the private repository,
  **no Git LFS**. Delegated to a subagent; migration is copy-only and
  reversible.
- The audit document and `reference-art-index.txt` (v3) are deliberately NOT
  committed here. This repository is public and both files expose local paths
  and private-repository details. They move to the private archive.
- New corpus for this converter: the AAHub archive, 1,153 txt+png pairs in 16
  slug directories. The PNGs are synthetic renders (Saitamaar 16 px, bilevel,
  17 px line step, 8 px pad), so they test scale, binarised input and throughput.
  They are not independent screenshot evidence, because the renderer's face is
  the decoder's model.

## P0C-07 · 2026-09-26 — proportional decoder scored on the AAHub corpus; held-out gap measured

- Corpus: `rikiyanai/ascii-art-archive` (private) `collections/aahub`, 1,153
  synthetic txt+png pairs rendered in Saitamaar 16 px with an 8 px pad. Split by
  slug. The 5 held-out slugs (hakumen-no-mono, joshua-bright, excel-saga,
  wizards-climber, violet-evergarden-tahen) are never counted or tuned on.
  `data/aa_char_prior.json` holds character counts only, from the 935 training
  pages (`scripts/build_char_prior.py`).
- Faults found on the corpus and fixed:
  (1) DP scatter via argsort. Glyphs are now grouped by advance, taking 57 s
  to 16 s per page with identical output.
  (2) Pitch error accumulating over long pages (16.968 vs 17 misread lines
  0-23). Pitch is now chosen by decode cost among candidates.
  (3) Sparse pages locked the pitch onto harmonics (34, 53, 58, 65 for 17).
  Candidates now include sub-harmonics and their neighbouring whole pixels.
  (4) With no container rule, the origin now takes the least indentation, not
  the smallest origin.
  (5) Blank lines inside the art were dropped. Only leading and trailing blank
  lattice lines are dropped now.
  (6) The alphabet is extended with training characters seen at least 3
  times. Pixel-identical glyphs keep the more frequent.
- Prior weight measured on the training split, known origin: exact rows 77.2%
  at 0, 75.0% at 0.03, 73.6% at 0.1, 25.8% at 0.3 (earlier code), 2.8% at 1.0.
  The default is 0.
- Receipts (`docs/receipts/2026-09-26-aahub-*/eval.json`, size 16 px given):
  - train, every 25th page, origin given: 42 pages, 780/1010 rows exact
    (77.2%);
  - held-out, every 5th page, origin given: 46 pages, 606/1106 rows exact
    (54.8%); 3 pages fully exact, 12 at 90% or better;
  - held-out, origin fitted: 385/1106 exact, 486/1106
    indentation-invariant. Without a text-box edge, absolute indentation is
    the dominant loss.
  - Madonna is unchanged at 22/24 (receipt regenerated).
- Held-out gap, measured: 175/1106 held-out key rows (15.8%) contain
  characters not in the candidate bank, against 57/1010 (5.6%) in training.
  The held-out art fills texture with kanji the training split never uses
  (怨 619 times, 絲 181 times). `─`, `│`, `ｊ` and `ｖ` are pixel-identical to
  `―`, `｜`, `j` and `v` at the same advance, so those misses cannot be
  resolved from pixels.
- Next:
  (a) a second pass that rescores poorly matched 1280-unit windows against
  the whole CJK block, because every kanji shares that advance;
  (b) the remaining sparse-page pitch errors (18 or 19 chosen for 17);
  (c) the size fit takes about 4 minutes and has not been exercised on the
  corpus;
  (d) all corpus pages are synthetic Saitamaar renders, so this is
  in-distribution for the face model. Real screenshots remain one (Madonna).
- Highest stage: **Executed** (corpus-scored). Not Verified across real
  screenshot sources; not Accepted.

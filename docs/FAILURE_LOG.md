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

## P0C-08 · 2026-09-26 — archive corpus grew; P0C-07 figures are pinned to the older snapshot

- `ascii-art-archive` AA-002 (commit `07a6198`, MANIFEST sha256
  `0f0d6988…c897a3`) did two things.
  - AAHub grew from 1,153 to 5,703 pairs in 43 slugs. 985 files were
    re-extracted at source, including removal of a leaked "SAI" token.
  - It added `ascii-art-de-rendered`: 12,816 pairs in Inconsolata 16 px, fixed
    grid, 8 px advance, 19 px line step, 8 px pad, bilevel.
- `data/aa_char_prior.json` and the P0C-07 receipts were built from archive
  commit `eb5a7bf` and stay valid only for that snapshot. The HELD_OUT slug
  list in `scripts/build_char_prior.py` names 5 of the original 16 slugs. A
  rebuild against the new snapshot would put every NEW slug into training
  unless the split is extended first. Re-split, re-count, and re-score before
  quoting new figures.
- New opportunity: `ascii-art-de-rendered` is the first large answer-key
  corpus for the FIXED-GRID tool (`recover_monospace_ascii.py`). That tool
  has so far been judged on one bundled sample and one screenshot pair.

## P0C-09 · 2026-09-26 — converter status and archive-snapshot audit

- Status before this attempt: `main` at `3192192`, clean and synchronized with
  `origin/main`. The fixed-grid tool is an executed experimental candidate:
  its one real answer-key screenshot scored 54/67 exact, while the bundled
  Stone Story sheet has no accepted transcript and has low reconstruction IoU.
  The proportional tool is also experimental: Madonna scored 22/24 canonical
  rows exact, and P0C-07's AAHub scores belong only to archive `eb5a7bf`.
  Neither tool is accepted for general screenshots; there is no automatic
  regime router.
- Audit falsifier for P0C-08: immutable archive commit `07a6198` contains
  **3,922** `res*.txt` and **3,922** matching `res*.png` AAHub files, not
  5,703 pairs. The counts come independently from `git ls-tree -r 07a6198`
  and `git show 07a6198:MANIFEST.tsv`. The 12,816 ascii-art.de pairs *do*
  match the committed manifest. Thus `P0C-08`, the archive README, and the
  handoff overstate the AAHub pair count for that commit. Do not score or
  train against the claimed 5,703 until those files are committed and pinned.
- During this audit the archive worktree acquired untracked AAHub directories
  and a modified manifest. These are concurrent, non-owned changes. No archive
  file was changed by this converter attempt, and worktree enumeration is not
  an acceptable corpus definition. Training must use an explicit split over
  only the committed slugs and verify each input against the pinned manifest.
- Roadmap and gates: (1) freeze the committed archive identity and expand the
  slug-held-out split; (2) rebuild character counts from training slugs only;
  (3) measure a new training baseline and held-out baseline on the same pinned
  pages before changing the decoder; (4) implement and ablate kanji fallback
  and short-page pitch fixes on training pages, then run held-out evaluation
  once; (5) independently establish a fixed-grid ascii-art.de baseline and
  error taxonomy. Real, independent screenshots and operator judgment remain
  the acceptance gate. No synthetic-corpus score upgrades acceptance.
- Current stage of this entry: audit finding and roadmap recorded. Training
  and code fixes are not yet claimed here; append their actual results below.

### Count correction before training

- The first audit count was **wrong**. It matched only numeric `res[0-9]+`
  names and omitted 1,781 legitimate names such as `resK-01`. Both
  `git ls-tree -r 07a6198` and `git show 07a6198:MANIFEST.tsv`, counted with
  `res*.txt`/`res*.png`, show **5,703 matched pairs** across 43 slugs.
  The 3,922 figure and the resulting README claim in `c35692b` are rejected.
  The archive handoff and P0C-08 pair count were correct after all.
- The worktree caution remains valid: untracked AAHub directories and a
  modified live manifest appeared during inspection. The training reader uses
  committed Git blobs from `07a6198`, not the moving worktree.
- The frozen split retains the original five held-out slugs and assigns nine
  of the 27 newly committed slugs to held-out by lowest SHA-256 slug name.
  `data/aahub_split.json` records the exact choices: 4,246 training pairs in
  29 slugs and 1,457 held-out pairs in 14 slugs. This prevents new-slug
  training leakage but is not franchise-disjoint. The prior and evaluations
  must carry the archive commit, manifest hash, and split hash together.

### First training pass on the corrected snapshot

- `build_char_prior.py` completed on 4,246 training Git blobs, producing
  `data/aa_char_prior.json`: 5,260,288 non-newline characters and 2,090
  distinct characters. Its archive commit, manifest hash, and split hash match
  `data/aahub_split.json`; no held-out text was read. The new reader verifies
  each Git blob against the committed manifest and ignores concurrent archive
  worktree changes.
- A one-page training smoke (`alisa-ransefort-01/res01.png`) decoded without an
  error: 14/33 canonical rows exact, line pitch 17 px, canonical CER 0.0517.
  This is only a smoke receipt, not a corpus estimate. Its score is not a
  decoder improvement claim and did not determine a tuning choice.
- Focused checks: `tests/test_archive_snapshot.py`, `test_lattice.py`, and
  `test_contract.py` passed (17 tests, 4 subtests). A larger training baseline
  remains pending at this checkpoint; held-out evaluation has not run.

### First train/held-out baseline completed

- Both evaluations read Git blobs from archive `07a6198`, use split hash
  `3dc65a19…02cb5`, known render size 16 px, known text origin x=8 px, and
  decoder prior weight 0. With `--every 1000`, they select the first page of
  each nonempty slug. The 2 empty training slugs contribute no pages.
- Training receipt `docs/receipts/2026-09-26-aahub-new-train/eval.json`:
  27 pages, 641 key rows, 432 exact (67.39%), 22/27 page row counts matched,
  0 crashes. Held-out receipt `docs/receipts/2026-09-26-aahub-new-heldout/eval.json`:
  14 pages, 357 key rows, 271 exact (75.91%), 14/14 page row counts matched,
  0 crashes. Combined 703/998 exact rows (70.44%) is descriptive only; the
  sampling is one page per slug, not a population estimate, and the partitions
  have different page compositions. These figures are not comparable to
  P0C-07's every-25th/every-5th older-snapshot measurements.
- Train-only pitch failures remain: `shingu-butsugu-mingeihin-zou/res02` was
  given 10 rows for a 9-row key at 16.2237 px; `kirby/res00`, `tonfa/res01`,
  and `violet-02-alt/res01` selected 18 px and lost a row. For the Shingu page,
  the 16.2237 px lattice gives its extra edge row only 3 units of exclusive
  source ink energy out of 760 total, versus 20 units for the first row of
  the 17 px, 9-row lattice. This supports an edge-row overfit hypothesis, not
  yet a general pitch fix. Do not tune to the held-out receipt.
- Character-class errors remain separately open. A kanji fallback has not been
  implemented or scored. The corpus is synthetic Saitamaar rendering, so the
  highest supported stage remains **Executed experimental candidate**; neither
  real-screenshot generalization nor user acceptance has changed.

### Fix gate after the baseline

- Full regression suite passed on the split/prior/evaluator changes:
  `python3 -m pytest -q` gave 39 passed, 6 subtests passed in 536.05 s.
- A train-only pitch oracle forced the documented 17 px render pitch on all
  five sampled pages whose row counts failed. It restored the correct row
  count on all five, but did **not** restore text accuracy: their canonical
  exact-row counts were 0/11, 1/9, 0/20, 0/12, and 0/25, respectively.
  Canonical CER remained 0.7112-1.1828. Thus wrong
  pitch is real, but is not the sole cause of these failures. A forced-pitch
  shortcut is rejected as a decoder fix; row phase, segmentation, and glyph
  scoring need separate train-only diagnosis before changing the algorithm.
- In the 27 sampled training pages, only 8/641 key rows contain a character
  absent from the rendered candidate bank (mostly pixel-identical `─`, plus
  one `姉`). The new training prior has 743 characters with frequency below
  the current inclusion threshold of 3, totaling 1,006 occurrences out of
  5,260,288. This does not justify claiming a broad gain from simply adding
  rare training characters. Whole-CJK fallback remains an unimplemented,
  separately measurable experiment, not an accepted correction.
- The archive has since advanced beyond `07a6198`; that does not change these
  pinned receipts. A later archive revision needs its own manifest pin and
  slug-disjoint split before any new prior or score is quoted.

### Train-only baseline-phase intervention

- Falsifier of the preceding forced-pitch test: on `tonfa/res01`, rendering
  the answer key with Saitamaar at 16 px, x=8, first baseline=22 px and 17 px
  pitch reproduces the archived bitmap exactly (thresholded ink IoU 1.0).
  The old fitted 17 px lattice started at 16 px. At the true geometry, the
  decoder scores 17/20 rows exact rather than 0/20. Kirby and Violet's
  row-count-failure pages score 11/11 and 25/25 at the same true geometry.
- Hypothesis: the average-glyph vertical profile used by `fit_rows()` selects
  the wrong baseline phase on short pages, which then also biases pitch
  selection. The intervention evaluates integer first-baseline phases by
  sampled glyph reconstruction cost, charges uncovered source ink, and
  compares the image-selected pitch with a 1.08-em whole-pixel candidate.
  The latter is a candidate, not a forced corpus pitch. Existing receipts
  remain the ablation baseline; a five-page train-only re-score and the
  Madonna/synthetic geometry regression tests must pass before acceptance.
- The five-page train-only re-score cleared that gate: 70/77 canonical rows
  exact, all 5 page row counts matched, versus 6/77 exact and 0/5 row counts
  matched on the same pages before the intervention. Each selected pitch is
  17 px; the baseline starts at 22 px. No held-out page informed the change.
  `tests/test_proportional.py` passed 3/3, including Madonna and a synthetic
  nine-row short page. A 27-page training re-score is still pending; the
  intervention is not yet accepted across the sample.
- The matched 27-page training re-score also cleared: 559/641 canonical rows
  exact (87.21%) and 27/27 page row counts matched, versus 432/641 (67.39%)
  and 22/27 before. Every page was unchanged or improved in exact rows; none
  regressed on this sample. Mean canonical CER fell from 0.2515 to 0.0181.
  Receipt: `docs/receipts/2026-09-26-aahub-phase-fix-train/eval.json`.
  The full suite passed after the code change: 40 tests, 6 subtests in
  825.73 s.
- The one post-fix held-out comparison also cleared without tuning on its
  results: 278/357 canonical rows exact (77.87%) versus 271/357 (75.91%),
  with 14/14 page row counts matched both before and after. Mean canonical CER
  fell from 0.1106 to 0.0386. Twelve pages were unchanged in exact-row count;
  `magia-record-sonota/resK-01` gained 1 and `ushiotora-sonota/res00` gained 6;
  none regressed. Receipt:
  `docs/receipts/2026-09-26-aahub-phase-fix-heldout/eval.json`.
- Accepted scope: the baseline-phase intervention is implemented, connected,
  executed, and verified on the pinned synthetic sample plus the Madonna test.
  It fixes the measured short-page line-spacing failure. It does not establish
  general screenshot acceptance, and it does not implement the open whole-CJK
  fallback. Highest product stage remains **Executed experimental candidate**.

## P0C-10 · 2026-09-26 — full AA-003 corpus training and scoring

- Start checkpoint. User-visible target: train and score the converter against
  the latest committed corpus, not another small smoke sample. Starting state:
  converter `main` at `3fc2286`, clean and synchronized with `origin/main`;
  archive `main` at clean commit `3687cc5` (AA-003), manifest SHA-256
  `15bb0213…d0c1f7bd58`.
- Direct Git-tree counts: AAHub has 32,950 matched `res*.txt`/`res*.png` pairs
  across 173 slugs. The prior P0C-09 lock covers only AA-002 at 5,703 pairs and
  is now a historical evaluation identity. It must not supply the current
  prior, split, or headline score.
- Phase plan: extend the immutable slug split before reading any new answer
  keys; rebuild the training-only prior over every training pair; run matched
  train and held-out evaluations at a declared deterministic sampling rate;
  diagnose and implement kanji fallback only from training evidence; run one
  post-change held-out comparison; then establish a separately pinned
  fixed-grid ascii-art.de baseline. Each receipt must name the archive commit,
  manifest hash, split hash, sampling rule, and decoder configuration.
- Current stage: **Started**. No AA-003 answer key has yet entered a prior or
  tuning decision at this checkpoint. The archive repository is read-only for
  this task.

### Split and full training prior checkpoint

- The split lock now covers all 173 slugs and 32,950 pairs at archive commit
  `3687cc5`. It preserves the 14 AA-002 held-out slugs, then assigns 43 of the
  130 new AA-003 slugs to held-out by the lowest SHA-256 of each UTF-8 slug
  name. Result: 116 training slugs / 23,363 pages and 57 held-out slugs /
  9,587 pages. Split SHA-256:
  `d61d856f26b0fd019797e6f5756bce0cc76249618c482962a14c364919a8d500`.
- `data/aa_char_prior.json` was rebuilt from every one of the 23,363 training
  TXT blobs at that immutable commit. It contains 23,746,955 characters and
  4,469 distinct characters. The split, commit, and manifest identities in the
  prior match the locks exactly. No held-out answer key entered the prior.
- Training evidence materially changes the kanji question: the prior contains
  3,596 distinct CJK Unified Ideographs (417,438 occurrences). Of those, 2,338
  occur at least three times and enter the current candidate alphabet; 1,258
  occur only once or twice and remain below `PRIOR_MIN_COUNT`. The successor
  must measure training decode failures before deciding whether the fallback
  should lower that threshold or lazily search the font's wider CJK coverage.

### Bulk-reader deadlock and correction

- The first full-prior build, corpus inventory, and fixed-grid run stalled in
  `git cat-file --batch`. The reader wrote every request before reading any
  response; with tens of thousands of blobs, Git filled stdout while the parent
  was still filling stdin. That is a deterministic pipe deadlock, not slow
  training. Those three agent-owned processes were terminated with exit 143;
  none had written its final receipt.
- `read_blobs` now writes, flushes, reads, and hash-verifies one requested blob
  at a time while retaining the single Git process. The snapshot test and
  compile checks pass. The corrected full prior completed in 7.8 seconds.

### Fixed-grid corpus contract and screenshot margins

- `data/ascii_art_de_corpus.json` locks all 12,816 matched pairs, the committed
  Inconsolata font, and the declared 8×19 cell / baseline 14 / 8 px pad /
  bilevel render contract. Direct validation found 12,715 UTF-8 and 101 CP-1252
  answer keys. A direct pixel probe reproduced the first archived page with
  zero differing pixels at the declared baseline.
- The full evaluator replaces the archive's uniform pad with deterministic,
  independently randomized top/right/bottom/left white margins from 0 through
  31 px. It fits the grid phase from the resulting screenshot pixels and does
  not use the generated margins to crop. Every page receipt records both the
  random margins and fitted phase so origin recovery is auditable.
- A three-page smoke run fit all three randomized origin phases exactly, kept
  all row counts, and resolved every source cell to a known raster (zero
  unmatched cells). Its 24/30 exact rows are not a corpus result; the remaining
  six rows contain raster-identical character ties and are retained as `?`
  rather than guessed. The complete 12,816-pair run is the next receipt.

### AAHub long-tail fallback prepared from training evidence

- At the existing `PRIOR_MIN_COUNT=3`, 1,315 printable training characters
  remain outside the learned extension: 1,258 are CJK Unified Ideographs,
  accounting for 1,678 actual training occurrences. This is direct training
  evidence for a kanji fallback rather than a held-out-driven guess.
- `--kanji-fallback` now expands the candidate request to the complete
  U+4E00–U+9FFF block; the declared Saitamaar cmap filters it to supported
  glyphs. On AA-003 this changes the pre-raster-dedup candidate bank from 3,152
  characters (2,339 CJK) to 7,547 (6,734 CJK). The option is not yet the
  default: it must beat the no-fallback decoder on a matched training receipt
  before the one post-choice held-out run.
- Direct coverage accounting over all 23,363 training keys found 1,920 of
  457,065 rows on 675 pages contain at least one character outside the baseline
  font bank. The 4,627 occurrences include 1,677 rare kanji; most of the
  remainder are alternate Unicode-width spaces that render blank. In the
  deterministic every-25 comparison sample, 85 of 18,990 rows on 31/986 pages
  contain an out-of-bank character, including 56 rare-kanji occurrences. This
  bounds the fallback's direct coverage opportunity before decode effects.
- The larger bank exposed repeated evaluator work. `decode_image` now accepts a
  geometry-checked pre-rendered bank, and each corpus worker renders that bank
  once instead of once per page. This is an evaluation performance change; the
  decoder path and glyph scores are unchanged. Compile and focused fallback
  coverage checks pass; the complete proportional test module then passed 3/3
  in 115.63 seconds.

### First full fixed-grid receipt rejected; mixed bilevel rasterizers found

- The first complete randomized-margin run is preserved at
  `docs/receipts/2026-09-26-ascii-art-de-full-random-margins.json`, but rejected
  as the fixed-grid baseline. It processed all 12,816 pairs and 217,049 key
  rows, yet produced only 57,113 exact rows (26.31%), 731,243 unmatched cells,
  and 1,021 row-count mismatches. This was a classifier failure, not a corpus
  score worth optimizing against.
- The archive manifests describe hard thresholding throughout, but the pixels
  prove two render behaviors. Re-rendering `ab/007/res03` with `<128` hard
  threshold gives zero differing pixels. The same operation on
  `jkl/law/res01` differs by 13,566 pixels, while Pillow's default
  Floyd–Steinberg bilevel conversion gives zero differences. It reduces the
  `mno/meriday/res06` difference from 102,180 pixels to 18 and
  `mno/michelangelo/res02` from 33,123 to 418. The archive contract is therefore
  incomplete even though the font and geometry are correct.
- The exact-raster evaluator has been replaced by an ASCII-first classifier:
  exact hard-threshold and per-cell Floyd rasters resolve immediately; unseen
  bilevel patterns fall back to a greyscale/threshold/Floyd nearest-template
  distance and retain `?` when the best/runner-up margin is under 0.6. This
  avoids the CP-1252 look-alike guesses that turned dithered ASCII `|` into
  broken bars. Tabs are expanded to visible 8-column stops before scoring,
  because their code point is not recoverable from screenshot pixels.
- Focused verification passes (6 tests). The corrected first three pages score
  30/30 exact rows. On three former high-loss pages, the corrected path scores
  `mno/meriday/res06` 284/290, `jkl/law/res01` 208/208, and `ab/007/res03`
  24/24, with exact randomized origin phases and zero crashes. A new full
  receipt must replace, not overwrite, the rejected one.

### Corrected full fixed-grid baseline completed

- Accepted diagnostic receipt:
  `docs/receipts/2026-09-26-ascii-art-de-full-random-margins-v2.json`, SHA-256
  `9a821605d7c0d03cb47350514a0b7b7907178a267d47b7e728cc863033f1755c`.
  It processed all 12,816 pairs / 217,049 key rows with independently
  randomized 0–31 px margins, zero crashes, and zero unmatched cells in
  2,819.3 seconds.
- Result: 112,909/217,049 strict exact rows (52.02%); 153,396/217,049
  indentation-invariant exact rows (70.67%); mean per-page canonical CER
  0.0767; row counts matched on 11,725/12,816 pages. It resolved 12,706,165
  cells by exact threshold/Floyd raster and 406,888 by the conservative nearest
  fallback; 3,108 remained ambiguous. The ASCII-only bank leaves 1,893
  non-ASCII key characters outside scope.
- Crop-origin separation: both randomized phases were fit exactly on
  10,916/12,816 pages; x phase alone on 12,602 and y phase alone on 10,918.
  Exact-phase pages scored 99,775/187,498 strict exact rows (53.21%) and
  135,363/187,498 indentation-invariant rows (72.19%), with mean canonical CER
  0.0386. Phase-wrong pages scored materially worse (mean canonical CER
  0.2955). The realistic uneven margin test therefore exposes origin fitting
  as a separate open problem rather than hiding it behind a perfect crop.
- Scope boundary: font, size, cell pitch, and line step come from the pinned
  corpus render contract; only outer crop phase is inferred. This is a full
  corpus diagnostic for classification plus imperfect cropping, not evidence
  that the blind fixed-grid CLI can infer every declared parameter.
- The evaluator now batches new raster patterns per page for distance scoring.
  Five focused tests pass, and the batched path reproduces the same exact-row
  results on the four threshold/dither representative pages.

## 2026-09-27 — authoring-principle implications for the proportional decoder (operator note)

- **Source:** a parallel audit of the ascii-art-authoring skill, logged in the
  unicode-glyph-morphology-explorer failure log, with an operator correction
  on 2026-09-27. Proportional Shift_JIS art follows the same core authoring
  principles as fixed-grid art: anisotropic stroke glyphs, form carried by
  negative space, and mirrored glyph pairs. Only the placement lattice
  differs.
- **Implications for this repository (open, not yet implemented):**
  1. The space-collapse law and the advance lattice are already hard
     constraints in `recover_proportional_aa.py` (no adjacent U+0020; pen
     positions on the font's unit gcd). A 3,214-line AAHub page measured zero
     adjacent and zero leading half-width spaces, which confirms both.
  2. The single-character prior hurt exact rows at every weight tested
     (P0C-07). The authoring idioms are multi-glyph strokes: `⌒ヽ` occurs 128
     times on one page, alongside `_ノ`, `ゝ__ノ`, `／￣`/`￣＼` and `-―-`.
     A bigram or stroke-idiom prior, counted on training slugs only, is the
     next prior hypothesis. Falsifier: no gain in held-out exact rows over the
     weight-0 baseline at the pinned split.
  3. `i`, `l`, `|`, `:` and `.` are used as stroke and tone shapes, not
     letters. Any letter-plausibility heuristic must not penalise them.
  4. Rows that are pixel-identical under alternative spellings, such as
     Madonna row 23 (`/　|　'` vs `/ ｜ '`), cannot be told apart from pixels.
     Pair text-level scoring with a raster re-render score so that these
     rows are not counted as reading errors.
- **Owner:** this log. The work sits behind the current P0C-10 sequence
  and does not change its pinned identities.

## 2026-09-27 — status review: AA-003 intake, orphan training receipt, skill-guided extraction gap

- **Orphan receipt logged here:** `docs/receipts/2026-09-26-aahub-aa003-train-every25/eval.json`
  (sha256 `b85c9953…a0ab7`). Archive `3687cc5`, split `d61d856f…`, train
  partition, every 25th page, `phase_refine=true`, `kanji_fallback=false`,
  prior weight 0. Summary: 986 pages, **30 errors**, 18,559 rows, 12,830
  exact (69.13%), 12,698 exact ignoring indentation, 818/986 row counts
  right, canonical CER 0.1626, strict CER 0.1311. The file was written after the
  last P0C-10 commit and was not logged. It is probably the no-fallback half
  of the pending matched comparison (P0C-10 "AAHub long-tail fallback").
  The 30 failing pages must be diagnosed before the `--kanji-fallback`
  receipt is run. The receipt records all 30 as
  `ValueError('min() iterable argument is empty')`. The error has not been
  reproduced yet. Stage: Executed. It is not a headline number.
- **Corpus use at archive `3687cc5`:**
  - AAHub has 32,950 pairs in 173 slugs, split into 23,363 train and 9,587
    held-out pages. The prior is rebuilt from train. Held-out is not scored
    on AA-003.
  - ascii-art-de-rendered has 12,816 pairs. It is scored by the fixed-grid
    evaluator (52.02% strict exact rows) and not used for training.
  - ascii-art-de-raw has 2,304 pages and is not used.
  - Real screenshots: Madonna only.
- **Viewer (unicode-glyph-morphology-explorer, HEAD `deee318`):** It shows
  Unicode seam, run and Stone Story plate combinations only. No
  AAHub/AA-003/Shift_JIS pattern is extracted into it. The only Shift_JIS
  measurement is the one-page
  `docs/research/ascii/sjis_aa_skill_audit/bakuhatsu_kemuri_stats.json`,
  which the viewer does not load. Skill section 15 (proportional addendum,
  skills commit `ec93ca1`) is not yet recorded in the viewer FL.
- **Skill-guided extraction jobs (proposals, priority order):**
  1. Glyph bigram/trigram prior from training slugs only, pooled across
     mirror pairs. `decode_row` must carry the last glyph or its class in
     its state. Falsifier as in the 2026-09-27 note item 2.
  2. Pixel-identical look-alike class table plus raster re-render scoring
     (note item 4). This also targets the 3,108 fixed-grid `?` cells.
  3. Run `aa_slug_stats.py` over all 116 training slugs, not one page, and
     make the output viewable in the explorer's combo browser. Needs the
     proposed v2 combo schema with `x_px` (audit P5).
  4. Tone-region band model (`.:::`-type errors, Madonna row 20).
  5. Fixed-grid n-grams from ascii-art-de-rendered for
     `recover_monospace_ascii.py`.
- **Next step in order:** diagnose the 30 errors → matched `--kanji-fallback`
  training receipt → one AA-003 held-out run → then job 1.

### 2026-09-27 — sub-floor pitch crash fixed; corrected every-25 train receipt

- **Symptom:** 30/986 pages in `2026-09-26-aahub-aa003-train-every25` failed
  with `ValueError('min() iterable argument is empty')` at
  `decode_image` → `min(pitch_trace, …)`. Reproduced on buki-01/res01,
  kanji/resK-308, buki-02/resK-114 and tabako/resK-26.
- **Cause (measured):** `line_geometry` searches autocorrelation lags from
  `bank_height // 2` (11 px at 16 px). All 30 pages returned a pitch below
  the 0.95 em line-box floor (15.2 px). The values were 8.1–15.0 px, plus one
  −7.37 px from a parabola vertex on a window-edge lag. A random control
  sample of 80 pages that decoded had none below the floor (lowest 16.71).
  Every pitch candidate is below the floor, so `options` and `pitch_trace`
  are empty.
- **Fix:** `decode_image` re-measures with `min_lag = ceil(0.95 em)` only
  when the default estimate is below the floor. On that path the parabola
  offset is clamped to ±0.5, and a page shorter than the window returns the
  floor. The default path is unchanged. `fit_size` is not changed. Regression
  test `SubFloorPitch` (synthetic 三二三 / 二三二 page, default pitch 11.20)
  fails without the fix and passes with it.
  `tests/test_proportional.py` 6/6 pass, and the rest of the suite 42/42.
- **Corrected receipt:** `docs/receipts/2026-09-27-aahub-aa003-train-every25-pitchfloor/eval.json`
  (sha256 `d116ad95…25968`). Identities are the same as the 2026-09-26
  receipt. Run with 8 workers and one BLAS thread each.
  - 986 pages, **0 errors**, 18,990 rows (matches the P0C-10 expectation).
  - 13,163 exact (**69.32%**), 13,031 exact ignoring indentation.
  - 843/986 row counts right, canonical CER 0.1631, strict CER 0.1316.
- **Identity check:** all 956 previously decoded pages give identical rows,
  exact counts, CERs, pitch and x0 (0 differ). The 30 recovered pages give
  333/431 exact rows (77.26%) and 25/30 row counts right. Pitch is 17.0 on
  28 pages; the other two are 19.63 and 24.0.
- **Stage:** Verified on the every-25 train sample. This receipt is the
  no-fallback half of the matched `--kanji-fallback` comparison. The
  2026-09-26 receipt is superseded as that baseline.
- **Side note:** the first rerun ran 10 workers × 11 numpy threads while
  other sessions were running. The machine then crashed with swap full. A
  30 GB-footprint `git grep` from another session in asciicker-Y9-2 was seen
  during the second run. Run corpus evaluations with
  `OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1`.

### 2026-09-27 — pointer: corpus combo extraction done in the glyph viewer (job 3)

- Job 3 from the status review is executed in unicode-glyph-morphology-explorer
  commit `661b220`. Output:
  `assets/glyphs/corpus/aahub_aa003_train.sjis_combos.v1.json`, built from
  training slugs of this repo's split `d61d856f…` only. It is viewable with
  `./run-families.sh --mode sjis`.
- Its training-only bigram, trigram and stack counts are the input for job 1
  (the stroke-idiom prior). This repository still owns building and scoring
  that prior.

### 2026-09-27 — stroke-idiom prior implemented; kanji-fallback targeted run and weight sweep started

- **Bigram prior (note item 2):**
  - `build_char_prior.py` now also writes `data/aa_bigram_prior.json`:
    touching non-space pairs from the 23,363 training pages, 9,735,411
    pairs, 51,950 kept at n ≥ 3. `aa_char_prior.json` is rebuilt
    byte-identical (sha256 `c18e3167…3c6`).
  - `bigram_bonus` keeps only positive associations ln(p(b|a)/p(b)). An
    unseen pair gets 0, never a penalty.
  - `decode_row` subtracts `weight × association` on layer 0, keyed on the
    best path's previous glyph. This approximates a bigram search with one
    survivor per state.
  - The prior acts only in the final reading. Pitch, phase and origin are
    unchanged, so a receipt differs only in which glyphs were read.
- **Checks:** weight 0 matches the pitch-floor receipt exactly on 12 pages,
  with no slowdown. New tests `StrokeIdiomPrior` pass: positive-only table,
  weight 0 identical, and an extreme weight reaches the path while baselines
  stay identical. The 12-page probe at weight 0.1 read 104/211 rows exactly
  against 105/211, which is too small to judge.
- **Weight selection (running):** receipts are
  `docs/receipts/2026-09-27-aahub-aa003-bigram-tune-every200-off12-w{0,0.03,0.1,0.3,1.0}`.
  The sample is every 200th train page starting at index 12, disjoint from
  the every-25 comparison sample. The best weight on it then gets one matched
  every-25 train receipt against `…-train-every25-pitchfloor`, and then the
  single held-out run.
- **Kanji fallback, targeted (operator choice 2026-09-27):**
  - Measured cost: bank 7,530 glyphs, 4.4 GB peak RSS and 127 s on the
    434×1138 page buki-02/resK-114.
  - Maximum possible gain on the every-25 sample: 85 rows on 31 pages.
  - The run covers those 31 pages plus 120 seeded control pages
    (`data/kanji_fallback_targeted_pages.json`, groups in
    `data/kanji_fallback_targeted_groups.json`). The no-fallback side is the
    same pages in the pitch-floor receipt.
  - Receipt: `docs/receipts/2026-09-27-aahub-aa003-train-kanji-fallback-targeted`.
- `eval_corpus.py` gains `--bigram-prior`, `--bigram-weight`,
  `--every-offset` and `--pages-file`. Their hashes and values are recorded
  in each receipt.

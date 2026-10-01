#!/usr/bin/env python3
"""Score the proportional decoder over pinned txt+png Git blobs of an art corpus.

Pages are chosen deterministically (every k-th page of each slug), decoded in
parallel at a given size, and scored with score_against_key. The per-page and
aggregate results are written to OUT/eval.json; that file is the receipt.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import recover_proportional_aa as rp  # noqa: E402
from score_against_key import score  # noqa: E402
from PIL import Image  # noqa: E402
from archive_snapshot import SPLIT, load_split, read_blob  # noqa: E402
from eval_fixed_grid_corpus import randomize_outer_margins  # noqa: E402
import mlt_pairs  # noqa: E402
import numpy as np  # noqa: E402

# AAHub renders put the text box 8 px from the left and top edges, with at
# least 8 px of paper on every side (measured on 28 pages across 14 slugs,
# 2026-09-29). Screenshot mode crops exactly this pad before adding margins.
AAHUB_PAD_PX = 8

_STATE: dict = {}


def _rel(path: str) -> str:
    """slug/page only: receipts in this public repository carry no local paths."""
    p = Path(path)
    return f"{p.parent.name}/{p.name}"


def _init(prior_path: str, weight: float, font: str, size_px: float, x0: float | None,
          archive: str, split: dict, phase_refine: bool, kanji_fallback: bool,
          bigram_path: str | None = None, bigram_weight: float = 0.0, bigram_score: str = "pmi",
          fallback_geometry: str = "full", margin_max: int | None = None,
          margin_seed: str = "", mlt_rows: dict | None = None) -> None:
    prior = rp.load_prior(Path(prior_path)) if prior_path else {}
    model = rp.load_font_model(Path(font), rp.prior_alphabet(prior, kanji_fallback))
    height = int(math.ceil(size_px * 1.25)) + 2
    baseline = int(round(size_px))
    # P0C-10: every job in this worker has the same face, size, and prior.
    # Rendering the expanded AA-003 glyph bank per page made corpus scoring
    # repeat identical work hundreds of times.
    bank = rp.render_bank(model, size_px, height, baseline, prior)
    # P0C-10 2026-09-28: "base" chooses pitch, phase and origin with the
    # ordinary bank and lets the whole-CJK bank read the final rows only.
    geometry_bank = None
    if kanji_fallback and fallback_geometry == "base":
        base_model = rp.load_font_model(Path(font), rp.prior_alphabet(prior, False))
        geometry_bank = rp.render_bank(base_model, size_px, height, baseline, prior)
    _STATE.update(prior=prior, weight=weight, x0=x0,
                  model=model,
                  bank=bank, geometry_bank=geometry_bank, margin_max=margin_max, margin_seed=margin_seed,
                  mlt_rows=mlt_rows or {},
                  bigram=rp.bigram_bonus(Path(bigram_path), bank.characters, bigram_score) if bigram_path else {},
                  bigram_weight=bigram_weight,
                  archive=Path(archive), split=split, phase_refine=phase_refine)


def _png(stem: str) -> str:
    """The page's image path; for AA-004 a derived name (no file exists)."""
    if stem.startswith("mlt:"):
        _, key, index = stem.split(":")
        return f"mlt/{key}/aa{int(index):04d}.png"
    return stem + ".png"


def _page_id(stem: str) -> str:
    return _rel(_png(stem))


_MLT_CACHE: dict[str, dict] = {}


def _mlt_text(stem: str) -> str:
    """AA-004 job 'mlt:<key>:<index>': the piece's text from the pinned record."""
    _, key, index = stem.split(":")
    if key not in _MLT_CACHE:
        _MLT_CACHE.clear()  # jobs arrive grouped by page; keep one record per worker
        _MLT_CACHE[key] = mlt_pairs.load_record_checked(_STATE["archive"], _STATE["mlt_rows"][key])
    return mlt_pairs.piece_text(_MLT_CACHE[key]["aa"][int(index)])


def _run(job: tuple[str, float]) -> dict:
    stem, size = job
    started = time.time()
    try:
        if stem.startswith("mlt:"):
            # P0C-10 2026-09-30: AA-004 pairs are derived, not stored. The render
            # equals AAHub's own (tests/test_mlt_pairs.py, 0 px differ).
            png = _png(stem)
            text = _mlt_text(stem)
            image = mlt_pairs.render_aahub(text, _STATE["archive"] / mlt_pairs.FONT_REL)
        else:
            png = stem + ".png"
            image = Image.open(io.BytesIO(read_blob(_STATE["archive"], _STATE["split"], png)))
        margins = None
        if _STATE["margin_max"] is not None:
            # P0C-10 2026-09-29 screenshot mode: a real capture is not aligned
            # to the text box. Crop the declared pad (refusing a page whose ink
            # reaches into it), then add reproducible 0..max px margins per edge.
            grey = np.asarray(image.convert("L"))
            inked = grey < 128
            rows, cols = np.nonzero(inked.any(axis=1))[0], np.nonzero(inked.any(axis=0))[0]
            # Crop the declared pad, but never ink: art that reaches into the
            # pad (5/170 tuning pages) keeps those columns or rows. The true
            # origin moves by whatever part of the left pad was kept.
            cut = {"top": min(AAHUB_PAD_PX, int(rows[0])), "left": min(AAHUB_PAD_PX, int(cols[0])),
                   "bottom": min(AAHUB_PAD_PX, grey.shape[0] - 1 - int(rows[-1])),
                   "right": min(AAHUB_PAD_PX, grey.shape[1] - 1 - int(cols[-1]))}
            content = grey[cut["top"]:grey.shape[0] - cut["bottom"], cut["left"]:grey.shape[1] - cut["right"]]
            canvas, margins = randomize_outer_margins(np.pad(content, 1, constant_values=255), _rel(png),
                                                      {"padding_px": 1}, _STATE["margin_seed"],
                                                      _STATE["margin_max"])
            margins["kept_left_pad"] = AAHUB_PAD_PX - cut["left"]
            image = Image.fromarray(canvas)
        result = rp.decode_image(image,
                                 _STATE["model"], size, 0.02, _STATE["x0"],
                                 _STATE["prior"], _STATE["weight"], _STATE["phase_refine"],
                                 _STATE["bank"], _STATE["bigram"], _STATE["bigram_weight"],
                                 _STATE["geometry_bank"])
        lines = [r.text for r in result["rows"]]
        while lines and not lines[-1]:
            lines.pop()
        key = (text.splitlines() if stem.startswith("mlt:") else
               read_blob(_STATE["archive"], _STATE["split"], stem + ".txt").decode("utf-8").splitlines())
        s = score(lines, key)
        s.pop("per_row")
        extra = {}
        if margins is not None:
            extra = {"margins": margins, "x0_true": float(margins["left"] + margins["kept_left_pad"]),
                     "x0_error": round(result["x0"] - margins["left"] - margins["kept_left_pad"], 4), "x0_source": result["x0_source"]}
        return {"page": _rel(png), **s, "pitch": result["pitch"], "x0": result["x0"], **extra,
                "candidate_glyphs": len(result["bank"].characters),
                "seconds": round(time.time() - started, 1)}
    except Exception as error:  # a crash is a result, not a silent skip
        return {"page": _rel(png), "error": repr(error)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="ascii-art-archive checkout; reads Git objects, not its worktree")
    parser.add_argument("out", type=Path)
    parser.add_argument("--split", type=Path, default=SPLIT)
    parser.add_argument("--partition", choices=("train", "heldout"), required=True)
    parser.add_argument("--slugs", nargs="+", help="optional subset within the chosen partition")
    parser.add_argument("--every", type=int, default=10)
    parser.add_argument("--size-px", type=float, required=True)
    parser.add_argument("--prior", default=str(rp.DEFAULT_PRIOR))
    parser.add_argument("--prior-weight", type=float, default=0.0)
    parser.add_argument("--workers", type=int, default=10)
    parser.add_argument("--x0", type=float, default=None,
                        help="known text origin (AAHub renders: 8 px pad); fitted when omitted")
    parser.add_argument("--no-phase-refine", action="store_true")
    parser.add_argument("--kanji-fallback", action="store_true")
    parser.add_argument("--fallback-geometry", choices=("full", "base"), default="full",
                        help="with --kanji-fallback: choose pitch/phase/origin with the full bank (historical) "
                             "or with the ordinary bank, reading only the final rows with the full bank")
    parser.add_argument("--bigram-prior", default=None,
                        help="touching-pair counts from build_char_prior.py (e.g. data/aa_bigram_prior.json)")
    parser.add_argument("--bigram-weight", type=float, default=0.0)
    parser.add_argument("--bigram-score", choices=("pmi", "cond"), default="pmi",
                        help="pmi: ln p(b|a)/p(b); cond: ln count(ab)/min_count (favours the frequent variant)")
    parser.add_argument("--pages-file", type=Path, default=None,
                        help="JSON list of slug/resN page names (as receipts print them, .png optional); "
                             "replaces the every-k sample, and every page must lie in the chosen partition")
    parser.add_argument("--resume", action="store_true",
                        help="continue an interrupted run in OUT from its partial.jsonl checkpoint; "
                             "refused unless the checkpoint's configuration matches this command")
    parser.add_argument("--random-margins", type=int, default=None, metavar="MAX_PX",
                        help="screenshot mode: crop the 8 px render pad and add reproducible 0..MAX_PX margins "
                             "per edge; the origin is then fitted (--x0 is refused)")
    parser.add_argument("--margin-seed", default="p0c10-aahub-screenshot-margins-v1")
    parser.add_argument("--mlt-split", type=Path, default=None,
                        help="score AA-004 crawl pieces (data/aahub_mlt_split.json) instead of AA-003 pairs; "
                             "--every samples art pieces of the partition, held-out pieces leaking into train "
                             "are excluded, and the image is rendered from the text (mlt_pairs.render_aahub)")
    parser.add_argument("--every-offset", type=int, default=0,
                        help="start index within each slug for the every-k sample (0 keeps the historical sample)")
    args = parser.parse_args()
    if args.every < 1 or args.workers < 1:
        parser.error("--every and --workers must both be positive")
    if args.random_margins is not None and (args.x0 is not None or args.random_margins < 0):
        parser.error("--random-margins needs a non-negative maximum and a fitted origin (omit --x0)")
    if args.out.exists() and not args.resume:
        parser.error("output directory already exists; use a new receipt path or --resume")
    if (args.out / "eval.json").exists():
        parser.error("output already holds a finished receipt")

    split, by_slug = load_split(args.archive, args.split)
    prior_metadata = json.loads(Path(args.prior).read_text(encoding="utf-8")) if args.prior else None
    if args.bigram_prior:
        bigram_metadata = json.loads(Path(args.bigram_prior).read_text(encoding="utf-8"))
        if (bigram_metadata.get("corpus_commit") != split["archive_commit"] or
                bigram_metadata.get("split_sha256") != hashlib.sha256(args.split.read_bytes()).hexdigest()):
            raise SystemExit("bigram prior was not built from this locked archive and split")
    if prior_metadata and (prior_metadata.get("corpus_commit") != split["archive_commit"] or
                           prior_metadata.get("manifest_sha256") != split["manifest_sha256"] or
                           prior_metadata.get("split_sha256") != hashlib.sha256(args.split.read_bytes()).hexdigest()):
        raise SystemExit("prior was not built from this locked archive and split")
    held_out = set(split["held_out_slugs"])
    allowed = sorted(s for s in by_slug if (s in held_out) == (args.partition == "heldout"))
    slugs = args.slugs or allowed
    if set(slugs) - set(allowed):
        raise SystemExit("requested slug is outside the chosen split partition")
    if len(slugs) != len(set(slugs)):
        raise SystemExit("requested slugs contain duplicates")
    jobs = []
    mlt_rows: dict = {}
    if args.mlt_split:
        if args.pages_file or args.slugs:
            parser.error("--mlt-split samples by --every; --pages-file and --slugs do not apply")
        mlt_split, mlt_rows = mlt_pairs.load_split(args.archive.resolve(), args.mlt_split)
        keys = mlt_split["train_keys"] if args.partition == "train" else mlt_split["held_out_keys"]
        leaking = {(k, i) for k, i in mlt_split["held_out_leaking_pieces"]}
        n = 0
        for key in keys:
            record = mlt_pairs.load_record_checked(args.archive.resolve(), mlt_rows[key])
            for i, entry in enumerate(record["aa"]):
                if not mlt_pairs.is_art(mlt_pairs.piece_text(entry)) or (key, i) in leaking:
                    continue
                if n % args.every == args.every_offset % args.every:
                    jobs.append((f"mlt:{key}:{i}", args.size_px))
                n += 1
        slugs = []
    elif args.pages_file:
        wanted = [p.removesuffix(".png") for p in json.loads(args.pages_file.read_text(encoding="utf-8"))]
        index = {f"{Path(stem).parent.name}/{Path(stem).name}": stem for slug in slugs for stem in by_slug[slug]}
        missing = [p for p in wanted if p not in index]
        if missing:
            raise SystemExit(f"{len(missing)} listed pages are not in the chosen partition, e.g. {missing[:3]}")
        if len(wanted) != len(set(wanted)):
            raise SystemExit("pages file contains duplicates")
        jobs = [(index[p], args.size_px) for p in wanted]
    for slug in ([] if (args.pages_file or args.mlt_split) else slugs):
        jobs.extend((stem, args.size_px) for stem in by_slug[slug][args.every_offset:: args.every])
    if not jobs:
        raise SystemExit("no pages matched: check the root and slug names")
    # 2026-09-27: a run killed for memory lost every finished page, because
    # results were only written at the end. Each finished page is now appended
    # to OUT/partial.jsonl as it arrives; --resume reuses those pages when the
    # configuration line matches exactly. The partial file is removed once
    # eval.json is written.
    config = {
        "archive_commit": split["archive_commit"],
        "split_sha256": hashlib.sha256(args.split.read_bytes()).hexdigest(),
        "partition": args.partition, "slugs": slugs, "every": args.every, "every_offset": args.every_offset,
        "pages_file_sha256": hashlib.sha256(args.pages_file.read_bytes()).hexdigest() if args.pages_file else None,
        "mlt_split_sha256": hashlib.sha256(args.mlt_split.read_bytes()).hexdigest() if args.mlt_split else None,
        "size_px": args.size_px, "x0": args.x0,
        "prior_sha256": hashlib.sha256(Path(args.prior).read_bytes()).hexdigest() if args.prior else None,
        "prior_weight": args.prior_weight, "phase_refine": not args.no_phase_refine,
        "kanji_fallback": args.kanji_fallback,
        "fallback_geometry": args.fallback_geometry,
        "random_margins": args.random_margins,
        "margin_seed": args.margin_seed if args.random_margins is not None else None,
        "bigram_prior_sha256": (hashlib.sha256(Path(args.bigram_prior).read_bytes()).hexdigest()
                                if args.bigram_prior else None),
        "bigram_weight": args.bigram_weight,
        "bigram_score": args.bigram_score,
        "decoder_sha256": hashlib.sha256(Path(rp.__file__).read_bytes()).hexdigest(),
    }
    partial = args.out / "partial.jsonl"
    done: dict[str, dict] = {}
    if args.resume and partial.exists():
        lines = partial.read_text(encoding="utf-8").splitlines()
        if not lines or json.loads(lines[0]).get("config") != config:
            raise SystemExit("checkpoint configuration differs from this command; refusing to resume")
        for line in lines[1:]:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                break  # a line cut off by the kill
            done[row["page"]] = row
        print(f"resuming: {len(done)} of {len(jobs)} pages already scored", file=sys.stderr)
    args.out.mkdir(parents=True, exist_ok=True)
    if not partial.exists() or not done:
        partial.write_text(json.dumps({"config": config}, ensure_ascii=False) + "\n", encoding="utf-8")
    todo = [j for j in jobs if _page_id(j[0]) not in done]
    with ProcessPoolExecutor(args.workers, initializer=_init,
                             initargs=(args.prior, args.prior_weight, str(rp.DEFAULT_FONT), args.size_px, args.x0,
                                       str(args.archive), split, not args.no_phase_refine,
                                       args.kanji_fallback, args.bigram_prior, args.bigram_weight,
                                       args.bigram_score, args.fallback_geometry,
                                       args.random_margins, args.margin_seed, mlt_rows)) as pool, \
            partial.open("a", encoding="utf-8") as sink:
        for future in as_completed([pool.submit(_run, job) for job in todo]):
            row = future.result()
            sink.write(json.dumps(row, ensure_ascii=False) + "\n")
            sink.flush()
            done[row["page"]] = row
    pages = [done[_page_id(j[0])] for j in jobs]
    ok = [p for p in pages if "error" not in p]
    rows = sum(p["rows_key"] for p in ok)
    summary = {
        "pages": len(pages), "errors": len(pages) - len(ok),
        "candidate_glyphs": ok[0]["candidate_glyphs"] if ok else None,
        "rows": rows, "exact_rows": sum(p["exact_rows"] for p in ok),
        "exact_rows_indentation_invariant": sum(p["exact_rows_indentation_invariant"] for p in ok),
        "exact_row_rate": round(sum(p["exact_rows"] for p in ok) / max(rows, 1), 4),
        "row_count_match": sum(p["rows_recovered"] == p["rows_key"] for p in ok),
        "mean_canonical_cer": round(sum(p["canonical_cer"] for p in ok) / max(len(ok), 1), 4),
        "mean_strict_cer": round(sum(p["strict_cer"] for p in ok) / max(len(ok), 1), 4),
    }
    if args.random_margins is not None and ok:
        errors = [abs(p["x0_error"]) for p in ok]
        summary["origin"] = {
            "within_0.5px": sum(e <= 0.5 for e in errors),
            "within_1px": sum(e <= 1.0 for e in errors),
            "mean_abs_error_px": round(sum(errors) / len(errors), 3),
            "max_abs_error_px": round(max(errors), 3),
        }
    (args.out / "eval.json").write_text(json.dumps({
        "schema": "proportional_eval.v2", "archive_commit": split["archive_commit"],
        "manifest_sha256": split["manifest_sha256"],
        "split_sha256": hashlib.sha256(args.split.read_bytes()).hexdigest(),
        "partition": args.partition, "slugs": slugs, "every": args.every,
        "phase_refine": not args.no_phase_refine,
        "kanji_fallback": args.kanji_fallback,
        "fallback_geometry": args.fallback_geometry,
        "random_margins": args.random_margins,
        "margin_seed": args.margin_seed if args.random_margins is not None else None,
        "size_px": args.size_px, "x0": args.x0, "prior": args.prior and Path(args.prior).name,
        "prior_weight": args.prior_weight,
        "bigram_prior": args.bigram_prior and Path(args.bigram_prior).name,
        "bigram_prior_sha256": (hashlib.sha256(Path(args.bigram_prior).read_bytes()).hexdigest()
                                if args.bigram_prior else None),
        "bigram_weight": args.bigram_weight,
        "bigram_score": args.bigram_score,
        "every_offset": args.every_offset,
        "mlt_split_sha256": hashlib.sha256(args.mlt_split.read_bytes()).hexdigest() if args.mlt_split else None,
        "pages_file_sha256": (hashlib.sha256(args.pages_file.read_bytes()).hexdigest()
                              if args.pages_file else None),
        "summary": summary, "pages": pages,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    partial.unlink()
    print(json.dumps(summary))
    if summary["errors"]:
        raise SystemExit(f"{summary['errors']} pages failed; inspect the receipt")


if __name__ == "__main__":
    main()

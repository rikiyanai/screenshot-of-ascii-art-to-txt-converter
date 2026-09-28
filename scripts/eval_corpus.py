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
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import recover_proportional_aa as rp  # noqa: E402
from score_against_key import score  # noqa: E402
from PIL import Image  # noqa: E402
from archive_snapshot import SPLIT, load_split, read_blob  # noqa: E402

_STATE: dict = {}


def _rel(path: str) -> str:
    """slug/page only: receipts in this public repository carry no local paths."""
    p = Path(path)
    return f"{p.parent.name}/{p.name}"


def _init(prior_path: str, weight: float, font: str, size_px: float, x0: float | None,
          archive: str, split: dict, phase_refine: bool, kanji_fallback: bool,
          bigram_path: str | None = None, bigram_weight: float = 0.0) -> None:
    prior = rp.load_prior(Path(prior_path)) if prior_path else {}
    model = rp.load_font_model(Path(font), rp.prior_alphabet(prior, kanji_fallback))
    height = int(math.ceil(size_px * 1.25)) + 2
    baseline = int(round(size_px))
    # P0C-10: every job in this worker has the same face, size, and prior.
    # Rendering the expanded AA-003 glyph bank per page made corpus scoring
    # repeat identical work hundreds of times.
    bank = rp.render_bank(model, size_px, height, baseline, prior)
    _STATE.update(prior=prior, weight=weight, x0=x0,
                  model=model,
                  bank=bank,
                  bigram=rp.bigram_bonus(Path(bigram_path), bank.characters) if bigram_path else {},
                  bigram_weight=bigram_weight,
                  archive=Path(archive), split=split, phase_refine=phase_refine)


def _run(job: tuple[str, float]) -> dict:
    stem, size = job
    started = time.time()
    try:
        png = stem + ".png"
        result = rp.decode_image(Image.open(io.BytesIO(read_blob(_STATE["archive"], _STATE["split"], png))),
                                 _STATE["model"], size, 0.02, _STATE["x0"],
                                 _STATE["prior"], _STATE["weight"], _STATE["phase_refine"],
                                 _STATE["bank"], _STATE["bigram"], _STATE["bigram_weight"])
        lines = [r.text for r in result["rows"]]
        while lines and not lines[-1]:
            lines.pop()
        key = read_blob(_STATE["archive"], _STATE["split"], stem + ".txt").decode("utf-8").splitlines()
        s = score(lines, key)
        s.pop("per_row")
        return {"page": _rel(png), **s, "pitch": result["pitch"], "x0": result["x0"],
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
    parser.add_argument("--bigram-prior", default=None,
                        help="touching-pair counts from build_char_prior.py (e.g. data/aa_bigram_prior.json)")
    parser.add_argument("--bigram-weight", type=float, default=0.0)
    parser.add_argument("--pages-file", type=Path, default=None,
                        help="JSON list of slug/resN page names (as receipts print them, .png optional); "
                             "replaces the every-k sample, and every page must lie in the chosen partition")
    parser.add_argument("--every-offset", type=int, default=0,
                        help="start index within each slug for the every-k sample (0 keeps the historical sample)")
    args = parser.parse_args()
    if args.every < 1 or args.workers < 1:
        parser.error("--every and --workers must both be positive")
    if args.out.exists():
        parser.error("output directory already exists; use a new receipt path")

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
    if args.pages_file:
        wanted = [p.removesuffix(".png") for p in json.loads(args.pages_file.read_text(encoding="utf-8"))]
        index = {f"{Path(stem).parent.name}/{Path(stem).name}": stem for slug in slugs for stem in by_slug[slug]}
        missing = [p for p in wanted if p not in index]
        if missing:
            raise SystemExit(f"{len(missing)} listed pages are not in the chosen partition, e.g. {missing[:3]}")
        if len(wanted) != len(set(wanted)):
            raise SystemExit("pages file contains duplicates")
        jobs = [(index[p], args.size_px) for p in wanted]
    for slug in ([] if args.pages_file else slugs):
        jobs.extend((stem, args.size_px) for stem in by_slug[slug][args.every_offset:: args.every])
    if not jobs:
        raise SystemExit("no pages matched: check the root and slug names")
    with ProcessPoolExecutor(args.workers, initializer=_init,
                             initargs=(args.prior, args.prior_weight, str(rp.DEFAULT_FONT), args.size_px, args.x0,
                                       str(args.archive), split, not args.no_phase_refine,
                                       args.kanji_fallback, args.bigram_prior, args.bigram_weight)) as pool:
        pages = list(pool.map(_run, jobs))
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
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / "eval.json").write_text(json.dumps({
        "schema": "proportional_eval.v2", "archive_commit": split["archive_commit"],
        "manifest_sha256": split["manifest_sha256"],
        "split_sha256": hashlib.sha256(args.split.read_bytes()).hexdigest(),
        "partition": args.partition, "slugs": slugs, "every": args.every,
        "phase_refine": not args.no_phase_refine,
        "kanji_fallback": args.kanji_fallback,
        "size_px": args.size_px, "x0": args.x0, "prior": args.prior and Path(args.prior).name,
        "prior_weight": args.prior_weight,
        "bigram_prior": args.bigram_prior and Path(args.bigram_prior).name,
        "bigram_prior_sha256": (hashlib.sha256(Path(args.bigram_prior).read_bytes()).hexdigest()
                                if args.bigram_prior else None),
        "bigram_weight": args.bigram_weight,
        "every_offset": args.every_offset,
        "pages_file_sha256": (hashlib.sha256(args.pages_file.read_bytes()).hexdigest()
                              if args.pages_file else None),
        "summary": summary, "pages": pages,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary))
    if summary["errors"]:
        raise SystemExit(f"{summary['errors']} pages failed; inspect the receipt")


if __name__ == "__main__":
    main()

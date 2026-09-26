#!/usr/bin/env python3
"""Score the proportional decoder over txt+png pairs of an art corpus.

Pages are chosen deterministically (every k-th page of each slug), decoded in
parallel at a given size, and scored with score_against_key. The per-page and
aggregate results are written to OUT/eval.json; that file is the receipt.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import recover_proportional_aa as rp  # noqa: E402
from score_against_key import score  # noqa: E402
from PIL import Image  # noqa: E402

_STATE: dict = {}


def _rel(path: str) -> str:
    """slug/page only: receipts in this public repository carry no local paths."""
    p = Path(path)
    return f"{p.parent.name}/{p.name}"


def _init(prior_path: str, weight: float, font: str, x0: float | None) -> None:
    prior = rp.load_prior(Path(prior_path)) if prior_path else {}
    _STATE.update(prior=prior, weight=weight, x0=x0,
                  model=rp.load_font_model(Path(font), rp.prior_alphabet(prior)))


def _run(job: tuple[str, str, float]) -> dict:
    png, txt, size = job
    started = time.time()
    try:
        result = rp.decode_image(Image.open(png), _STATE["model"], size, 0.02, _STATE["x0"],
                                 _STATE["prior"], _STATE["weight"])
        lines = [r.text for r in result["rows"]]
        while lines and not lines[-1]:
            lines.pop()
        key = Path(txt).read_text(encoding="utf-8").splitlines()
        s = score(lines, key)
        s.pop("per_row")
        return {"page": _rel(png), **s, "pitch": result["pitch"], "x0": result["x0"],
                "seconds": round(time.time() - started, 1)}
    except Exception as error:  # a crash is a result, not a silent skip
        return {"page": _rel(png), "error": repr(error)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="collection root with <slug>/resNN.{png,txt}")
    parser.add_argument("out", type=Path)
    parser.add_argument("--slugs", nargs="+", required=True)
    parser.add_argument("--every", type=int, default=10)
    parser.add_argument("--size-px", type=float, required=True)
    parser.add_argument("--prior", default=str(rp.DEFAULT_PRIOR))
    parser.add_argument("--prior-weight", type=float, default=0.0)
    parser.add_argument("--workers", type=int, default=10)
    parser.add_argument("--x0", type=float, default=None,
                        help="known text origin (AAHub renders: 8 px pad); fitted when omitted")
    args = parser.parse_args()

    jobs = []
    for slug in args.slugs:
        pngs = sorted((args.root / slug).glob("res*.png"))
        for png in pngs[:: args.every]:
            jobs.append((str(png), str(png.with_suffix(".txt")), args.size_px))
    if not jobs:
        raise SystemExit("no pages matched: check the root and slug names")
    with ProcessPoolExecutor(args.workers, initializer=_init,
                             initargs=(args.prior, args.prior_weight, str(rp.DEFAULT_FONT), args.x0)) as pool:
        pages = list(pool.map(_run, jobs))
    ok = [p for p in pages if "error" not in p]
    rows = sum(p["rows_key"] for p in ok)
    summary = {
        "pages": len(pages), "errors": len(pages) - len(ok),
        "rows": rows, "exact_rows": sum(p["exact_rows"] for p in ok),
        "exact_rows_indentation_invariant": sum(p["exact_rows_indentation_invariant"] for p in ok),
        "exact_row_rate": round(sum(p["exact_rows"] for p in ok) / max(rows, 1), 4),
        "row_count_match": sum(p["rows_recovered"] == p["rows_key"] for p in ok),
        "mean_canonical_cer": round(sum(p["canonical_cer"] for p in ok) / max(len(ok), 1), 4),
        "mean_strict_cer": round(sum(p["strict_cer"] for p in ok) / max(len(ok), 1), 4),
    }
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "eval.json").write_text(json.dumps({
        "schema": "proportional_eval.v1", "slugs": args.slugs, "every": args.every,
        "size_px": args.size_px, "x0": args.x0, "prior": args.prior and Path(args.prior).name,
        "prior_weight": args.prior_weight, "summary": summary, "pages": pages,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()

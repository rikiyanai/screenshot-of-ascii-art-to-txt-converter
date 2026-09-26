#!/usr/bin/env python3
"""Score recovered text against an answer key, row by row.

Three figures, strictest first:

* strict: character error rate over the raw rows.
* spacing-canonical: every blank run replaced by its (U+3000, U+0020) counts,
  because any order of the same spaces renders identically in the source face.
* exact rows: rows equal under the spacing-canonical view.

Rows are compared by index. A dropped or merged row therefore shows up as a
large error in every row after it, which is the intended behaviour: row
structure is part of the answer.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

BLANK = re.compile("[ 　]+")


def levenshtein(a: list, b: list) -> int:
    previous = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        current = [i]
        for j, y in enumerate(b, 1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (x != y)))
        previous = current
    return previous[-1]


def canonical_tokens(row: str) -> list:
    tokens: list = []
    position = 0
    for match in BLANK.finditer(row):
        tokens.extend(row[position : match.start()])
        run = match.group()
        tokens.append(("blank", run.count("　"), run.count(" ")))
        position = match.end()
    tokens.extend(row[position:])
    return tokens


def score(recovered: list[str], key: list[str]) -> dict:
    rows = []
    strict_err = strict_len = canon_err = canon_len = exact = 0
    for i in range(max(len(recovered), len(key))):
        got = recovered[i] if i < len(recovered) else ""
        want = key[i] if i < len(key) else ""
        s = levenshtein(list(got), list(want))
        c = levenshtein(canonical_tokens(got), canonical_tokens(want))
        strict_err += s
        strict_len += len(want)
        canon_err += c
        canon_len += len(canonical_tokens(want))
        exact += int(c == 0 and i < len(key))
        rows.append({"row": i, "strict_edits": s, "canonical_edits": c})
    return {
        "rows_key": len(key),
        "rows_recovered": len(recovered),
        "strict_cer": round(strict_err / max(strict_len, 1), 4),
        "canonical_cer": round(canon_err / max(canon_len, 1), 4),
        "exact_rows": exact,
        "per_row": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("recovered", type=Path)
    parser.add_argument("key", type=Path)
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args()
    recovered = args.recovered.read_text(encoding="utf-8").splitlines()
    key = args.key.read_text(encoding="utf-8").splitlines()
    result = score(recovered, key)
    if args.json:
        args.json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        f"rows {result['rows_recovered']}/{result['rows_key']}, strict CER {result['strict_cer']:.4f}, "
        f"spacing-canonical CER {result['canonical_cer']:.4f}, exact rows {result['exact_rows']}/{result['rows_key']}"
    )
    print(" ".join(f"{r['row']}:{r['canonical_edits']}" for r in result["per_row"]))


if __name__ == "__main__":
    main()

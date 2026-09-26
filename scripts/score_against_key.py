#!/usr/bin/env python3
"""Score recovered text against an answer key, row by row.

Four figures, strictest first:

* strict: character error rate over the raw rows.
* spacing-canonical: every blank run replaced by its (U+3000, U+0020) counts,
  because any order of the same spaces renders identically in the source face.
* exact rows: rows equal under the spacing-canonical view.
* indentation-invariant exact rows: the same, after removing the indentation
  common to every row of each side. Without a visible text-box edge the
  absolute indentation is not in the pixels; this figure separates that from
  reading errors.

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


def dedent(rows: list[str]) -> list[str]:
    """Remove the whitespace prefix common to every non-empty row, measured in
    font units of Saitamaar (U+3000 = 880, U+0020 = 400) so that equal widths
    written differently still cancel."""
    def lead(row: str) -> int:
        n = len(row) - len(row.lstrip(" \u3000"))
        return sum(880 if c == "\u3000" else 400 for c in row[:n])

    widths = [lead(r) for r in rows if r.strip(" \u3000")]
    common = min(widths) if widths else 0
    out = []
    for row in rows:
        n = len(row) - len(row.lstrip(" \u3000"))
        prefix, body = row[:n], row[n:]
        remaining = lead(row) - common if body else 0
        full, rest = divmod(remaining, 880)
        # rewrite the leftover prefix canonically; widths that are not a sum of
        # the two spaces keep their original prefix so they still count as wrong
        halves = rest // 400 if rest % 400 == 0 else None
        out.append(("\u3000" * full + " " * halves + body) if halves is not None else prefix + body)
    return out


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
    dr, dk = dedent(recovered), dedent(key)
    indent_free = sum(
        int(i < len(dr) and levenshtein(canonical_tokens(dr[i]), canonical_tokens(dk[i])) == 0)
        for i in range(len(dk))
    )
    return {
        "exact_rows_indentation_invariant": indent_free,
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
        f"spacing-canonical CER {result['canonical_cer']:.4f}, exact rows {result['exact_rows']}/{result['rows_key']}, "
        f"indentation-invariant {result['exact_rows_indentation_invariant']}/{result['rows_key']}"
    )
    print(" ".join(f"{r['row']}:{r['canonical_edits']}" for r in result["per_row"]))


if __name__ == "__main__":
    main()

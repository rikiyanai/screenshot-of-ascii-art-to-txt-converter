#!/usr/bin/env python3
"""Ask TypeSafe Jev to pick among text candidates the pixels cannot separate.

Jev cannot see pixels. The decoders produce candidates and pixel evidence;
this module only forwards spans whose candidates the pixels leave open, as
text, and records Jev's distribution next to the pixel costs. Pixel evidence
is never overwritten.

Page contract (input and output, JSON):

    {
      "schema": "jev-spans/v1",
      "page": "<id>",
      "text_type": {"fit_cost": {"monospace": 0.41, "proportional": 0.03}},
      "font": {"fit_cost": {"Saitamaar @ 16px": 0.02, "IPAGP-Mona @ 16px": 0.05}},
      "rows": [
        {"text": "<decoder best row>",
         "spans": [
           {"cols": [start, end],          # str indices into text, end exclusive
            "kind": "kanji" | "glyph" | "width" | "lookalike",
            "options": {"a": "...", "b": "..."},
            "pixel_cost": {"a": 0.12, "b": 0.13},   # lower is better
            "pixel_identical": false,
            "jev": null}                            # filled by merge
         ]}
      ]
    }

text_type and font are decided by code (lowest fit_cost); Jev is not used.
`choice` is written beside `fit_cost` by `decide_by_fit`.

Span selection (`select_span`): a span is sent only when
  - it has at least two distinct options and none contains `?`
    (unknown glyphs stay `?` and are never sent),
  - it is not pixel-identical: the `pixel_identical` flag is false, and for
    `width` spans the options are not the same multiset of U+3000/U+0020
    (any order of the same blanks renders identically; P0C-10 / 2026-09-27
    operator note, item 4),
  - at least two options lie within the margin of the best pixel cost:
    cost - best <= max(abs_margin, rel_margin * |best|).
Only the options inside the margin are offered to Jev.

HTTP contract, from https://docs.typesafe.ai/api.md ("Evaluation endpoint"):
    POST https://api.typesafe.ai/v1/systemone
    Authorization: Bearer <API_KEY>
    Content-Type: application/json
    body: {"state": string|object|array, "model": "jev-latest",
           "questions": {<id>: {"type": "choice", "instructions": ...,
                                "criteria": {<option>: string|object|null}}}}
The key is read from TYPESAFE_API_KEY, the variable the Python SDK page names
(https://docs.typesafe.ai/sdk/python.md, Quickstart step 2).
Choice answer ("Answer types > Choice answer"): {"type": "choice",
"choice": str, "probabilities": {option: float}, "confidence": float}.
429 and 529 are retried with exponential backoff ("Handling rate limits").
Choice accepts at most 255 options (https://docs.typesafe.ai/primitives/choice.md).
State is text only; CJK is accepted with lower accuracy
(https://docs.typesafe.ai/concepts/state.md).

CLI:
    python3 scripts/jev_disambiguate.py SPANS.json --dry-run --out REQUESTS.json
    python3 scripts/jev_disambiguate.py SPANS.json --out MERGED.json   # needs TYPESAFE_API_KEY
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Literal, Optional, TypedDict

SCHEMA = "jev-spans/v1"
API_URL = "https://api.typesafe.ai/v1/systemone"
API_KEY_ENV = "TYPESAFE_API_KEY"
DEFAULT_MODEL = "jev-latest"
MAX_CHOICE_OPTIONS = 255
RETRY_STATUSES = (429, 529)
PLACEHOLDER = "⟦{sid}⟧"  # ⟦s0⟧ — marks the span inside the row text
BLANKS = {"　", " "}

SpanKind = Literal["kanji", "glyph", "width", "lookalike"]
SPAN_KINDS: tuple[str, ...] = ("kanji", "glyph", "width", "lookalike")


class JevAnswer(TypedDict):
    choice: str
    probabilities: dict[str, float]
    confidence: float


class Span(TypedDict, total=False):
    cols: list[int]
    kind: SpanKind
    options: dict[str, str]
    pixel_cost: dict[str, float]
    pixel_identical: bool
    jev: Optional[JevAnswer]
    jev_status: str  # "sent" or the reason it was not sent (added by merge/plan)


class Row(TypedDict, total=False):
    text: str
    spans: list[Span]


class FitDecision(TypedDict, total=False):
    fit_cost: dict[str, float]
    choice: str


class Page(TypedDict, total=False):
    schema: str
    page: str
    text_type: FitDecision
    font: FitDecision
    rows: list[Row]


@dataclass(frozen=True)
class SelectionConfig:
    abs_margin: float = 0.0
    rel_margin: float = 0.05
    neighbours: int = 2


@dataclass(frozen=True)
class Selection:
    send: bool
    reason: str  # "sent" | "pixel_identical" | "unknown_glyph" | "single_option" | "pixel_decided"
    options: tuple[str, ...]  # option keys offered to Jev (empty when not sent)


# --------------------------------------------------------------------------- validation


def validate_page(page: Page) -> None:
    if page.get("schema") != SCHEMA:
        raise ValueError(f"schema must be {SCHEMA!r}, got {page.get('schema')!r}")
    for field in ("text_type", "font"):
        fit = page.get(field)
        if fit is not None and not fit.get("fit_cost"):
            raise ValueError(f"{field}.fit_cost must be a non-empty map")
    for r, row in enumerate(page.get("rows", [])):
        text = row.get("text")
        if not isinstance(text, str):
            raise ValueError(f"row {r}: text must be a string")
        taken: list[tuple[int, int]] = []
        for s, span in enumerate(row.get("spans", [])):
            where = f"row {r} span {s}"
            cols = span.get("cols")
            if not (isinstance(cols, list) and len(cols) == 2 and 0 <= cols[0] <= cols[1] <= len(text)):
                raise ValueError(f"{where}: cols must be [start, end] inside the row text")
            if span.get("kind") not in SPAN_KINDS:
                raise ValueError(f"{where}: kind must be one of {SPAN_KINDS}")
            options = span.get("options") or {}
            costs = span.get("pixel_cost") or {}
            if not options or set(options) != set(costs):
                raise ValueError(f"{where}: options and pixel_cost must name the same keys")
            if len(options) > MAX_CHOICE_OPTIONS:
                raise ValueError(f"{where}: more than {MAX_CHOICE_OPTIONS} options")
            if text[cols[0]:cols[1]] not in options.values():
                raise ValueError(f"{where}: row text at cols is not one of the options")
            for a, b in taken:
                if cols[0] < b and a < cols[1]:
                    raise ValueError(f"{where}: overlaps another span")
            taken.append((cols[0], cols[1]))


# --------------------------------------------------------------------------- code-owned decisions


def decide_by_fit(fit: FitDecision) -> str:
    """Lowest fit cost wins. Code decides text type and font; Jev is not used."""
    costs = fit["fit_cost"]
    return min(costs, key=lambda k: (costs[k], k))


def width_spellings_identical(options: dict[str, str]) -> bool:
    """Blank runs spelled with the same counts of U+3000 and U+0020 render
    identically in any order, so the pixels cannot order them."""
    values = list(options.values())
    if not all(v and set(v) <= BLANKS for v in values):
        return False
    counts = {(v.count("　"), v.count(" ")) for v in values}
    return len(counts) == 1


def select_span(span: Span, config: SelectionConfig) -> Selection:
    options = span["options"]
    costs = span["pixel_cost"]
    if any("?" in v for v in options.values()):
        return Selection(False, "unknown_glyph", ())
    if len(set(options.values())) < 2:
        return Selection(False, "single_option", ())
    if span.get("pixel_identical") or (span["kind"] == "width" and width_spellings_identical(options)):
        return Selection(False, "pixel_identical", ())
    best = min(costs.values())
    limit = max(config.abs_margin, config.rel_margin * abs(best))
    close = tuple(sorted((k for k in options if costs[k] - best <= limit), key=lambda k: (costs[k], k)))
    # Distinct texts only: two keys with the same text are not a question.
    seen: dict[str, str] = {}
    for k in close:
        seen.setdefault(options[k], k)
    close = tuple(k for k in close if seen[options[k]] == k)
    if len(close) < 2:
        return Selection(False, "pixel_decided", ())
    return Selection(True, "sent", close)


# --------------------------------------------------------------------------- question builder


def describe_text(text: str) -> str:
    names = []
    for ch in text:
        name = unicodedata.name(ch, "UNNAMED")
        names.append(f"U+{ord(ch):04X} {name}")
    return ", ".join(names)


KIND_INSTRUCTIONS: dict[str, str] = {
    "kanji": ("The marked position {mark} in `row.text` holds one Japanese character whose rendered "
              "shapes are nearly identical for every candidate. Which candidate did the author type, "
              "judging from the words and characters around it in `row.text` and the neighbouring rows?"),
    "glyph": ("The marked position {mark} in `row.text` holds a glyph whose candidates render almost "
              "the same. In this art, symbols are drawn as stroke shapes, not read as letters. Which "
              "candidate continues the strokes and glyph idioms in `row.text` and the neighbouring rows?"),
    "lookalike": ("The marked position {mark} in `row.text` holds one of several look-alike characters "
                  "(for example a half-width and a full-width form). Which candidate would the author "
                  "have typed here, given how the same shapes are spelled elsewhere in `row.text` and "
                  "the neighbouring rows?"),
    "width": ("The marked position {mark} in `row.text` is a blank run whose candidate spellings render "
              "with nearly the same width. Which spelling would the author have typed, given how blank "
              "runs are spelled elsewhere in `row.text` and the neighbouring rows?"),
}


def page_context(page: Page) -> dict[str, str]:
    context = {
        "medium": ("Text art (Shift_JIS / 2channel AA style). Characters are chosen for their shapes. "
                   "Candidates were produced from a screenshot; the pixels could not separate them."),
    }
    if page.get("text_type"):
        context["text_type"] = page["text_type"].get("choice") or decide_by_fit(page["text_type"])
    if page.get("font"):
        context["font"] = page["font"].get("choice") or decide_by_fit(page["font"])
    return context


def marked_row(text: str, spans: list[Span], marks: dict[int, str]) -> str:
    """Replace each selected span with its placeholder; other spans keep the decoder's text."""
    out, pos = [], 0
    for s, span in sorted(enumerate(spans), key=lambda item: item[1]["cols"][0]):
        start, end = span["cols"]
        if s not in marks:
            continue
        out.append(text[pos:start])
        out.append(PLACEHOLDER.format(sid=marks[s]))
        pos = end
    out.append(text[pos:])
    return "".join(out)


@dataclass
class PlannedRequest:
    row: int
    body: dict[str, Any]           # the exact JSON sent to the endpoint
    questions: dict[str, tuple[int, int]]  # question id -> (row, span)


def plan_requests(page: Page, config: SelectionConfig, model: str = DEFAULT_MODEL
                  ) -> tuple[list[PlannedRequest], dict[tuple[int, int], Selection]]:
    """One request per row that has sendable spans. All of that row's spans are
    asked together over one state (independent questions, evaluated in parallel)."""
    validate_page(page)
    rows = page.get("rows", [])
    context = page_context(page)
    selections: dict[tuple[int, int], Selection] = {}
    requests: list[PlannedRequest] = []
    for r, row in enumerate(rows):
        spans = row.get("spans", [])
        marks: dict[int, str] = {}
        for s, span in enumerate(spans):
            sel = select_span(span, config)
            selections[(r, s)] = sel
            if sel.send:
                marks[s] = f"s{len(marks)}"
        if not marks:
            continue
        lo, hi = max(0, r - config.neighbours), min(len(rows), r + config.neighbours + 1)
        state = {
            "art": context,
            "rows_above": [rows[i]["text"] for i in range(lo, r)],
            "row": {"text": marked_row(row["text"], spans, marks)},
            "rows_below": [rows[i]["text"] for i in range(r + 1, hi)],
        }
        questions: dict[str, Any] = {}
        qmap: dict[str, tuple[int, int]] = {}
        for s, sid in marks.items():
            span = spans[s]
            mark = PLACEHOLDER.format(sid=sid)
            criteria = {
                key: {"text": span["options"][key], "characters": describe_text(span["options"][key])}
                for key in selections[(r, s)].options
            }
            qid = f"r{r}_{sid}"
            questions[qid] = {
                "type": "choice",
                "instructions": KIND_INSTRUCTIONS[span["kind"]].format(mark=mark),
                "criteria": criteria,
            }
            qmap[qid] = (r, s)
        body = {"state": state, "model": model, "questions": questions}
        requests.append(PlannedRequest(r, body, qmap))
    return requests, selections


# --------------------------------------------------------------------------- HTTP client


class JevError(RuntimeError):
    pass


KEY_FILE = Path.home() / ".config" / "typesafe" / "key"  # written by ~/.config/typesafe/set_key.sh (mode 600)


def api_key(env: Optional[dict[str, str]] = None, key_file: Optional[Path] = None) -> str:
    """TYPESAFE_API_KEY, else the operator's key file. The key is never logged."""
    key = (env if env is not None else os.environ).get(API_KEY_ENV, "")
    path = key_file if key_file is not None else (KEY_FILE if env is None else None)
    if not key and path is not None and path.exists():
        key = path.read_text(encoding="utf-8").strip()
    if not key:
        raise JevError(f"{API_KEY_ENV} is not set and {KEY_FILE} is missing; use --dry-run instead")
    return key


def post_systemone(body: dict[str, Any], key: str, *, url: str = API_URL, retries: int = 4,
                   backoff_s: float = 1.0, timeout_s: float = 60.0,
                   opener: Callable[..., Any] = urllib.request.urlopen,
                   sleep: Callable[[float], None] = time.sleep) -> dict[str, Any]:
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    for attempt in range(retries + 1):
        request = urllib.request.Request(url, data=data, method="POST", headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        })
        try:
            with opener(request, timeout=timeout_s) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as err:
            if err.code in RETRY_STATUSES and attempt < retries:
                sleep(backoff_s * (2 ** attempt))
                continue
            detail = err.read().decode("utf-8", "replace") if err.fp else ""
            raise JevError(f"HTTP {err.code} from {url}: {detail[:500]}") from err
    raise JevError("unreachable")  # pragma: no cover


# --------------------------------------------------------------------------- merge


def parse_choice_answer(answer: dict[str, Any], offered: tuple[str, ...], qid: str) -> JevAnswer:
    if answer.get("type") != "choice":
        raise JevError(f"{qid}: expected a choice answer, got {answer.get('type')!r}")
    probabilities = {str(k): float(v) for k, v in (answer.get("probabilities") or {}).items()}
    choice = answer.get("choice")
    if choice not in offered or not set(probabilities) <= set(offered):
        raise JevError(f"{qid}: answer names options that were not offered")
    return {"choice": choice, "probabilities": probabilities, "confidence": float(answer["confidence"])}


def merge(page: Page, requests: list[PlannedRequest], selections: dict[tuple[int, int], Selection],
          responses: list[dict[str, Any]]) -> Page:
    """Return a copy of the page with `jev` and `jev_status` on every span and the
    code decisions on text_type/font. Row text and pixel costs are left as given."""
    out: Page = copy.deepcopy(page)
    for fit_field in ("text_type", "font"):
        if out.get(fit_field):
            out[fit_field]["choice"] = decide_by_fit(out[fit_field])
    for (r, s), sel in selections.items():
        span = out["rows"][r]["spans"][s]
        span["jev"] = None
        span["jev_status"] = sel.reason
    for planned, response in zip(requests, responses, strict=True):
        answers = response.get("answers") or {}
        for qid, (r, s) in planned.questions.items():
            if qid not in answers:
                raise JevError(f"{qid}: missing from response")
            out["rows"][r]["spans"][s]["jev"] = parse_choice_answer(answers[qid], selections[(r, s)].options, qid)
    return out


# --------------------------------------------------------------------------- CLI


def dry_run_document(page: Page, requests: list[PlannedRequest],
                     selections: dict[tuple[int, int], Selection]) -> dict[str, Any]:
    # Matched against https://docs.typesafe.ai/api.md (read 2026-09-29):
    #   "## Evaluation endpoint
    #    POST https://api.typesafe.ai/v1/systemone
    #    Authorization: Bearer <API_KEY>
    #    Content-Type: application/json"
    #   Choice criteria: "A map of option to rubric description; use null when
    #   an option needs no extra detail. You can have a maximum of 255 options
    #   per Choice."
    # Each `body` below is the exact request body that would be POSTed.
    return {
        "endpoint": {"method": "POST", "url": API_URL,
                     "headers": {"Authorization": f"Bearer ${API_KEY_ENV}", "Content-Type": "application/json"}},
        "page": page.get("page"),
        "requests": [{"row": p.row, "questions": {q: list(v) for q, v in p.questions.items()}, "body": p.body}
                     for p in requests],
        "not_sent": [{"row": r, "span": s, "reason": sel.reason}
                     for (r, s), sel in sorted(selections.items()) if not sel.send],
    }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("spans", type=Path, help=f"page JSON ({SCHEMA})")
    parser.add_argument("--out", type=Path, help="output JSON (default: stdout)")
    parser.add_argument("--dry-run", action="store_true", help="write the request payloads; send nothing")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--abs-margin", type=float, default=SelectionConfig.abs_margin)
    parser.add_argument("--rel-margin", type=float, default=SelectionConfig.rel_margin)
    parser.add_argument("--neighbours", type=int, default=SelectionConfig.neighbours)
    args = parser.parse_args(argv)

    page: Page = json.loads(args.spans.read_text(encoding="utf-8"))
    config = SelectionConfig(args.abs_margin, args.rel_margin, args.neighbours)
    requests, selections = plan_requests(page, config, args.model)

    if args.dry_run:
        document: Any = dry_run_document(page, requests, selections)
    else:
        key = api_key()
        responses = [post_systemone(p.body, key) for p in requests]
        document = merge(page, requests, selections, responses)

    text = json.dumps(document, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
        print(f"wrote {args.out} ({len(requests)} request(s), "
              f"{sum(len(p.questions) for p in requests)} question(s))", file=sys.stderr)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (JevError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)

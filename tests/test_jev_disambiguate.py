"""Jev disambiguation module: span selection, request shape, merge, client.

Every test is offline. The HTTP layer is replaced by a fake opener; no request
leaves the machine and no API key is needed.
"""

from __future__ import annotations

import copy
import io
import json
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/jev_spans_example.json"
sys.path.insert(0, str(ROOT / "scripts"))

import jev_disambiguate as jd  # noqa: E402


def load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def span(options, costs, kind="lookalike", identical=False):
    return {"cols": [0, len(next(iter(options.values())))], "kind": kind, "options": options,
            "pixel_cost": costs, "pixel_identical": identical, "jev": None}


class FakeResponse:
    def __init__(self, payload: dict):
        self._data = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def fake_answers(request_body: dict) -> dict:
    """A plausible response: the first offered option wins."""
    answers = {}
    for qid, question in request_body["questions"].items():
        keys = list(question["criteria"])
        probs = {k: (0.8 if i == 0 else 0.2 / (len(keys) - 1)) for i, k in enumerate(keys)}
        answers[qid] = {"type": "choice", "choice": keys[0], "probabilities": probs, "confidence": 0.7}
    return {"model": "jev-1.13.0", "answers": answers, "usage": {"input_tokens": 1, "output_tokens": 1}}


class SelectionTest(unittest.TestCase):
    config = jd.SelectionConfig(abs_margin=0.0, rel_margin=0.05)

    def test_close_costs_are_sent(self):
        sel = jd.select_span(span({"a": "|", "b": "｜"}, {"a": 0.118, "b": 0.121}), self.config)
        self.assertTrue(sel.send)
        self.assertEqual(sel.options, ("a", "b"))

    def test_far_costs_are_decided_by_pixels(self):
        sel = jd.select_span(span({"a": "ヽ", "b": "丶"}, {"a": 0.10, "b": 0.31}), self.config)
        self.assertEqual((sel.send, sel.reason), (False, "pixel_decided"))

    def test_margin_is_configurable(self):
        s = span({"a": "ヽ", "b": "丶"}, {"a": 0.10, "b": 0.31})
        self.assertTrue(jd.select_span(s, jd.SelectionConfig(abs_margin=0.25)).send)

    def test_pixel_identical_flag_is_never_sent(self):
        sel = jd.select_span(span({"a": "l", "b": "I"}, {"a": 0.1, "b": 0.1}, identical=True), self.config)
        self.assertEqual((sel.send, sel.reason), (False, "pixel_identical"))

    def test_width_order_is_pixel_identical_even_without_flag(self):
        s = span({"a": "　 ", "b": " 　"}, {"a": 0.0, "b": 0.0}, kind="width")
        self.assertEqual(jd.select_span(s, self.config).reason, "pixel_identical")

    def test_width_with_different_blank_counts_can_be_sent(self):
        s = span({"a": "　", "b": " "}, {"a": 0.300, "b": 0.309}, kind="width")
        self.assertTrue(jd.select_span(s, self.config).send)

    def test_unknown_glyph_is_never_sent(self):
        for options in ({"a": "?"}, {"a": "?", "b": "ヽ"}):
            costs = {k: 0.1 for k in options}
            self.assertEqual(jd.select_span(span(options, costs), self.config).reason, "unknown_glyph")

    def test_nbest_keeps_only_options_inside_margin(self):
        s = span({"a": "人", "b": "入", "c": "八"}, {"a": 0.200, "b": 0.205, "c": 0.400}, kind="kanji")
        self.assertEqual(jd.select_span(s, self.config).options, ("a", "b"))


class CodeDecisionTest(unittest.TestCase):
    def test_text_type_and_font_are_lowest_fit_cost(self):
        page = load_fixture()
        self.assertEqual(jd.decide_by_fit(page["text_type"]), "proportional")
        self.assertEqual(jd.decide_by_fit(page["font"]), "Saitamaar @ 16px")


class ValidationTest(unittest.TestCase):
    def test_fixture_is_valid(self):
        jd.validate_page(load_fixture())

    def test_cols_must_match_an_option(self):
        page = load_fixture()
        page["rows"][1]["spans"][0]["cols"] = [0, 1]
        with self.assertRaises(ValueError):
            jd.validate_page(page)

    def test_options_and_costs_must_share_keys(self):
        page = load_fixture()
        del page["rows"][1]["spans"][0]["pixel_cost"]["b"]
        with self.assertRaises(ValueError):
            jd.validate_page(page)

    def test_choice_option_limit(self):
        page = load_fixture()
        s = page["rows"][1]["spans"][0]
        s["options"] = {f"o{i}": "|" if i == 0 else chr(0x4E00 + i) for i in range(256)}
        s["pixel_cost"] = {k: 0.1 for k in s["options"]}
        with self.assertRaises(ValueError):
            jd.validate_page(page)


class RequestShapeTest(unittest.TestCase):
    def setUp(self):
        self.page = load_fixture()
        self.requests, self.selections = jd.plan_requests(self.page, jd.SelectionConfig())

    def test_only_selected_spans_become_questions(self):
        asked = sorted(v for p in self.requests for v in p.questions.values())
        self.assertEqual(asked, [(1, 0), (2, 1), (3, 2)])
        reasons = {k: v.reason for k, v in self.selections.items() if not v.send}
        self.assertEqual(reasons, {(2, 0): "pixel_identical", (3, 0): "unknown_glyph", (3, 1): "pixel_decided"})

    def test_body_matches_api_schema(self):
        # https://docs.typesafe.ai/api.md: top level state/model/questions;
        # Choice question has type, instructions, criteria (map, <= 255 options).
        for planned in self.requests:
            body = planned.body
            self.assertEqual(set(body), {"state", "model", "questions"})
            self.assertEqual(body["model"], "jev-latest")
            for question in body["questions"].values():
                self.assertEqual(set(question), {"type", "instructions", "criteria"})
                self.assertEqual(question["type"], "choice")
                self.assertIsInstance(question["instructions"], str)
                self.assertGreaterEqual(len(question["criteria"]), 2)
                self.assertLessEqual(len(question["criteria"]), jd.MAX_CHOICE_OPTIONS)
            json.dumps(body)  # serialisable

    def test_state_is_text_only_and_carries_no_pixel_evidence(self):
        for planned in self.requests:
            blob = json.dumps(planned.body, ensure_ascii=False)
            self.assertNotIn("pixel_cost", blob)
            self.assertNotIn("pixel_identical", blob)
            for cost in ("0.118", "0.121", "0.241", "0.2463", "0.309"):
                self.assertNotIn(cost, blob)
            self.assertNotIn("fit_cost", blob)

            def walk(value):
                if isinstance(value, dict):
                    for v in value.values():
                        walk(v)
                elif isinstance(value, list):
                    for v in value:
                        walk(v)
                else:
                    self.assertIsInstance(value, str)
            walk(planned.body["state"])

    def test_span_is_marked_and_neighbours_included(self):
        row2 = next(p for p in self.requests if p.row == 2)
        state = row2.body["state"]
        # The pixel-identical width span keeps the decoder text; the kanji span is marked.
        self.assertEqual(state["row"]["text"], "　 （ ⟦s0⟧間 ）")
        self.assertEqual(state["rows_above"], [self.page["rows"][0]["text"], self.page["rows"][1]["text"]])
        self.assertEqual(state["rows_below"], [self.page["rows"][3]["text"], self.page["rows"][4]["text"]])
        question = row2.body["questions"]["r2_s0"]
        self.assertIn("⟦s0⟧", question["instructions"])
        self.assertEqual(question["criteria"]["a"]["text"], "人")
        self.assertIn("U+5165", question["criteria"]["b"]["characters"])
        self.assertEqual(state["art"]["font"], "Saitamaar @ 16px")

    def test_page_is_not_mutated(self):
        self.assertEqual(self.page, load_fixture())


class MergeTest(unittest.TestCase):
    def test_merge_records_jev_beside_pixel_costs(self):
        page = load_fixture()
        requests, selections = jd.plan_requests(page, jd.SelectionConfig())
        merged = jd.merge(page, requests, selections, [fake_answers(p.body) for p in requests])
        self.assertEqual(merged["text_type"]["choice"], "proportional")
        for r, row in enumerate(merged["rows"]):
            self.assertEqual(row["text"], page["rows"][r]["text"])
            for s, sp in enumerate(row["spans"]):
                original = page["rows"][r]["spans"][s]
                self.assertEqual(sp["pixel_cost"], original["pixel_cost"])
                self.assertEqual(sp["options"], original["options"])
                if selections[(r, s)].send:
                    self.assertEqual(sp["jev_status"], "sent")
                    self.assertEqual(set(sp["jev"]), {"choice", "probabilities", "confidence"})
                else:
                    self.assertIsNone(sp["jev"])
        self.assertEqual(merged["rows"][3]["spans"][0]["jev_status"], "unknown_glyph")
        self.assertEqual(merged["rows"][3]["spans"][0]["options"], {"a": "?"})

    def test_merge_rejects_unoffered_option(self):
        page = load_fixture()
        requests, selections = jd.plan_requests(page, jd.SelectionConfig())
        responses = [fake_answers(p.body) for p in requests]
        bad = copy.deepcopy(responses)
        answer = next(iter(bad[0]["answers"].values()))
        answer["choice"] = "z"
        with self.assertRaises(jd.JevError):
            jd.merge(page, requests, selections, bad)

    def test_merge_rejects_missing_answer(self):
        page = load_fixture()
        requests, selections = jd.plan_requests(page, jd.SelectionConfig())
        responses = [fake_answers(p.body) for p in requests]
        responses[0]["answers"].clear()
        with self.assertRaises(jd.JevError):
            jd.merge(page, requests, selections, responses)


class ClientTest(unittest.TestCase):
    body = {"state": "x", "model": "jev-latest", "questions": {}}

    def test_request_url_headers_and_body(self):
        seen = []

        def opener(request, timeout):
            seen.append(request)
            return FakeResponse({"answers": {}})

        jd.post_systemone(self.body, "k-test", opener=opener, sleep=lambda s: None)
        request = seen[0]
        self.assertEqual(request.full_url, "https://api.typesafe.ai/v1/systemone")
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.get_header("Authorization"), "Bearer k-test")
        self.assertEqual(request.get_header("Content-type"), "application/json")
        self.assertEqual(json.loads(request.data), self.body)

    def test_retries_429_and_529_with_backoff(self):
        codes = iter([429, 529])
        sleeps = []

        def opener(request, timeout):
            code = next(codes, None)
            if code:
                raise urllib.error.HTTPError(request.full_url, code, "busy", {}, io.BytesIO(b"{}"))
            return FakeResponse({"answers": {"ok": 1}})

        out = jd.post_systemone(self.body, "k", opener=opener, sleep=sleeps.append, backoff_s=1.0)
        self.assertEqual(out, {"answers": {"ok": 1}})
        self.assertEqual(sleeps, [1.0, 2.0])

    def test_422_is_not_retried(self):
        calls = []

        def opener(request, timeout):
            calls.append(1)
            raise urllib.error.HTTPError(request.full_url, 422, "bad", {}, io.BytesIO(b'{"detail":"x"}'))

        with self.assertRaises(jd.JevError):
            jd.post_systemone(self.body, "k", opener=opener, sleep=lambda s: None)
        self.assertEqual(len(calls), 1)

    def test_missing_key_is_an_error(self):
        with self.assertRaises(jd.JevError):
            jd.api_key({})
        self.assertEqual(jd.api_key({"TYPESAFE_API_KEY": "abc"}), "abc")


class CliTest(unittest.TestCase):
    def test_dry_run_writes_payloads_without_network(self):
        def no_network(*args, **kwargs):
            raise AssertionError("dry run must not open a connection")

        original = jd.urllib.request.urlopen
        jd.urllib.request.urlopen = no_network
        try:
            with tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp) / "requests.json"
                self.assertEqual(jd.main([str(FIXTURE), "--dry-run", "--out", str(out)]), 0)
                document = json.loads(out.read_text(encoding="utf-8"))
        finally:
            jd.urllib.request.urlopen = original
        self.assertEqual(document["endpoint"]["url"], jd.API_URL)
        self.assertEqual([r["row"] for r in document["requests"]], [1, 2, 3])
        self.assertEqual(len(document["not_sent"]), 3)
        for request in document["requests"]:
            self.assertEqual(set(request["body"]), {"state", "model", "questions"})


if __name__ == "__main__":
    unittest.main()

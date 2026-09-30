"""Indentation-invariant scoring (P0C-10 2026-09-29)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from score_against_key import score  # noqa: E402


class IndentationInvariant(unittest.TestCase):
    def test_relative_width_no_spaces_can_spell_still_matches(self) -> None:
        # rows differ by 880 - 400 = 480 units, which no U+3000/U+0020 mix spells;
        # the old dedent kept raw prefixes there and scored a correct page as wrong
        key = ["　　 　x", "　　　y"]
        shifted = ["　 　x", "　　y"]  # the whole page 880 units less indented
        result = score(shifted, key)
        self.assertEqual(result["exact_rows"], 0)
        self.assertEqual(result["exact_rows_indentation_invariant"], 2)

    def test_relative_indentation_error_is_still_an_error(self) -> None:
        key = ["　x", "　　y"]
        wrong = ["x", "　　y"]
        # row 0 is the page's reference; row 1 is 880 units too far right relative to it
        self.assertEqual(score(wrong, key)["exact_rows_indentation_invariant"], 1)


if __name__ == "__main__":
    unittest.main()

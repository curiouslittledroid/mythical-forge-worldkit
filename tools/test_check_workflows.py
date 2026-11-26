#!/usr/bin/env python3
"""Tests for `check-workflows.py`.

The bug this exists for: two `if:` keys on one workflow step. A lenient YAML parser keeps the last one,
GitHub refuses the whole file, and the workflow then appears in Actions named by its path, failing
every run with nothing a reader can act on.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # the suite runs from the repository root

from check_workflows import duplicates  # noqa: E402

CLEAN = """\
name: Tooling drift
on:
  push:
jobs:
  drift:
    steps:
      - uses: actions/checkout@v4
        with:
          path: kit
      - name: Read the pin
        id: kit
        run: |
          echo hi
      - name: Is the pin behind?
        if: steps.kit.outputs.ok == '1'
        run: |
          echo there
"""

DUPLICATE = """\
jobs:
  drift:
    steps:
      - name: Is this a world?
        id: kind
        run: |
          echo world
      - name: Is the pin behind?
        if: steps.kind.outputs.world == '1'
        if: steps.kit.outputs.reachable == '1'
        run: |
          echo there
"""


class DuplicateKeysCase(unittest.TestCase):
    def test_a_clean_workflow_has_none(self):
        self.assertEqual(duplicates(CLEAN), [])

    def test_repeated_keys_across_sibling_steps_are_not_duplicates(self):
        # `run:` and `with:` repeat at the same indentation in every step, by design. A detector that
        # ignored sequence items reported 13 of these and would have been switched off on day one.
        text = "steps:\n" + "".join(
            f"  - name: step {i}\n    run: echo {i}\n" for i in range(4)
        )
        self.assertEqual(duplicates(text), [])

    def test_the_duplicate_if_is_found(self):
        got = duplicates(DUPLICATE)
        self.assertEqual(len(got), 1, got)
        self.assertIn("duplicate key 'if'", got[0])

    def test_the_line_number_points_at_the_second_key(self):
        # Find the line rather than asserting a number I would have to keep in step by hand.
        lines = DUPLICATE.splitlines()
        second = lines.index("        if: steps.kit.outputs.reachable == '1'") + 1
        self.assertIn(f"{second}:", duplicates(DUPLICATE)[0])

    def test_comments_and_blank_lines_are_ignored(self):
        self.assertEqual(duplicates("a:\n  # b: c\n\n  b: 1\n"), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)

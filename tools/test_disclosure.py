#!/usr/bin/env python3
"""Tests for tools/disclosure.py. Run: python3 tools/test_disclosure.py"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import disclosure  # noqa: E402
import lint  # noqa: E402
import testkit  # noqa: E402

REAL_ROOT = lint.ROOT


def note(kind="NPC", extra="", body=""):
    return (
        f"---\nid: npc_a\nkind: {kind}\ntitle: A\nname_status: working\nstatus: working\n"
        f"engine: false\n{extra}---\n\n# A\n\n**Summary:** A reasonably long summary.\n\n{body}"
    )


class TestClassify(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        lint.ROOT = Path(self.tmp.name)
        testkit.write_config(lint.ROOT)

    def tearDown(self):
        lint.ROOT = REAL_ROOT
        self.tmp.cleanup()

    def classes(self, text):
        (lint.ROOT / "world").mkdir(exist_ok=True)
        (lint.ROOT / "world" / "a.md").write_text(text, encoding="utf-8")
        (lint.ROOT / "meta").mkdir(exist_ok=True)
        (lint.ROOT / "meta" / "b.md").write_text(note(kind="TOPIC", body="## Details\nx\n"), encoding="utf-8")
        return {h: (s, c) for _, _, _, h, s, c in disclosure.survey()}

    def test_default_secrets_and_design_sections(self):
        got = self.classes(note(body="## Details\nPublic face.\n\n## Secrets\nHidden.\n\n## Hooks\n- go\n"))
        self.assertEqual(got["Details"], ("unreviewed", "earned"))
        self.assertEqual(got["Secrets"], ("secrets", "earned"))
        self.assertEqual(got["Hooks"], ("notlore", "-"))

    def test_explicit_mark_wins_over_the_secrets_rule(self):
        got = self.classes(note(body="## Secrets\n**Disclosure:** sealed\nThe keystone.\n"))
        self.assertEqual(got["Secrets"], ("marked", "sealed"))

    def test_note_default(self):
        self.assertEqual(self.classes(note(kind="TOPIC", extra="disclosure: earned\n", body="## Details\nx\n"))["Details"],
                         ("note", "earned"))
        # `visibility` is retired (Step 2e) and decides nothing: an unmarked note fails closed.
        self.assertEqual(self.classes(note(kind="TOPIC", extra="visibility: public\n", body="## Details\nx\n"))["Details"],
                         ("unreviewed", "earned"))

    def test_history_layers(self):
        got = self.classes(note(kind="HISTORY_EVENT", body="## Details\n- **Official:** a\n- **Truth:** b\n"))
        self.assertEqual(got["Details"], ("layered", "mixed"))

    def test_truth_label_with_a_qualifier_and_design_scope(self):
        got = self.classes(note(kind="HISTORY_EVENT", body="## Details\n- **Truth (decided):** b\n\n## Run it: a court scene\n- go\n"))
        self.assertEqual(got["Details"], ("layered", "mixed"))
        self.assertEqual(got["Run it: a court scene"], ("notlore", "-"))
        self.assertEqual(len(disclosure.survey()), len(got))  # the meta/ note is not surveyed

    def test_check_fails_only_when_a_section_is_unreviewed(self):
        self.classes(note(body="## Details\nPublic face.\n"))
        self.assertEqual(disclosure.main(["--check"]), 1)
        self.classes(note(extra="disclosure: open\n", body="## Details\nPublic face.\n"))
        self.assertEqual(disclosure.main(["--check"]), 0)

    def test_named_members_roster_is_not_lore(self):
        got = self.classes(note(body="## Named members (decided, Step 2)\n- x\n"))
        self.assertEqual(got["Named members (decided, Step 2)"], ("notlore", "-"))

    def test_author_notes_is_not_lore(self):
        """A design citation kept for the author must never reach a player page."""
        got = self.classes(note(extra="disclosure: open\n", body=(
            "## Details\nPublic face.\n\n## Author Notes\n- **Engine form:** a Fact (PR-4).\n")))
        self.assertEqual(got["Details"], ("note", "open"))
        self.assertEqual(got["Author Notes"], ("notlore", "-"))

    def test_author_notes_wins_even_on_an_earned_note(self):
        got = self.classes(note(body="## Secrets\nHidden.\n\n## Author Notes\n- x (CP-6)\n"))
        self.assertEqual(got["Author Notes"], ("notlore", "-"))


if __name__ == "__main__":
    unittest.main()

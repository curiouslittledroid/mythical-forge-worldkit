#!/usr/bin/env python3
"""Tests for `check_doc_examples.py`.

The bug this exists for: site.md named another world's sealed keystones as "the current list", and
thread-pattern.md taught the pattern with that world's ids, None of them existed in the demo world,
so a reader copying an example got a vault where nothing resolved.

Run: python3 tools/test_check_doc_examples.py
"""
from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_doc_examples  # noqa: E402


class DocCase(unittest.TestCase):
    """A throwaway kit: one demo world, one world-facing document."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self._root = check_doc_examples.ROOT
        check_doc_examples.ROOT = self.root
        demo = self.root / "template" / "example-world"
        (demo / "world" / "npcs").mkdir(parents=True)
        (demo / "world.config.yaml").write_text("world:\n  id: world_demo\n", encoding="utf-8")
        (demo / "world" / "npcs" / "tomas-reed.md").write_text(
            "---\nid: npc_tomas_reed\n---\n\n# Tomas\n\nA faction: faction_ferry_creditors.\n",
            encoding="utf-8")
        (self.root / "tools").mkdir()
        self.doc = self.root / "tools" / "README.md"

    def tearDown(self):
        check_doc_examples.ROOT = self._root
        self.tmp.cleanup()

    def run_check(self, text: str) -> tuple[int, str]:
        self.doc.write_text(text, encoding="utf-8")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = check_doc_examples.main([])
        return code, out.getvalue()


class TestDocExamples(DocCase):
    def test_the_demo_worlds_id_passes(self):
        code, out = self.run_check("An NPC, `npc_tomas_reed`, and `faction_ferry_creditors`.\n")
        self.assertEqual(code, 0, out)

    def test_an_id_the_demo_world_does_not_have_fails(self):
        code, out = self.run_check("An NPC, `npc_halvard_sorn`, which is another world's.\n")
        self.assertEqual(code, 1)
        self.assertIn("npc_halvard_sorn", out)
        self.assertIn("README.md:1", out)

    def test_one_bad_id_among_good_ones_still_fails(self):
        code, _ = self.run_check("`npc_tomas_reed` and `evt_lin_seized`.\n")
        self.assertEqual(code, 1)

    def test_a_placeholder_passes(self):
        code, out = self.run_check(
            "Write `npc_<role>`, `evt_example_stage`, `foo_id`, `npc_x`, and "
            "`world/events/evt_ferry_*.yaml`.\n")
        self.assertEqual(code, 0, out)

    def test_a_predicate_is_not_an_id(self):
        code, out = self.run_check("Conditions: `quest_state`, `npc_alive`, `faction_rep_gte`.\n")
        self.assertEqual(code, 0, out)

    def test_a_worlds_own_documents_are_not_checked(self):
        (self.root / "AGENTS.md").write_text("This world uses `npc_only_here`.\n", encoding="utf-8")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = check_doc_examples.main([])
        self.assertEqual(code, 0, out.getvalue())

    def test_a_source_world_phrase_fails(self):
        code, out = self.run_check("Current list: `Choir water`, `Convenor`.\n")
        self.assertEqual(code, 1)
        self.assertIn("Choir water", out)
        self.assertIn("Convenor", out)

    def test_a_source_world_phrase_is_case_sensitive(self):
        # "lineage" is an ordinary word; "Lineage" was that world's thread.
        code, out = self.run_check("A testable lineage, and a lineage predicate.\n")
        self.assertEqual(code, 0, out)

    def test_a_source_world_phrase_in_the_machinery_is_not_scanned_by_default(self):
        (self.root / "tools" / "a_test.py").write_text('"Choir water"\n', encoding="utf-8")
        code, out = self.run_check("An NPC, `npc_tomas_reed`.\n")
        self.assertEqual(code, 0, out)

    def test_all_also_sweeps_the_machinery_for_phrases(self):
        (self.root / "tools" / "a_test.py").write_text('"Choir water"\n', encoding="utf-8")
        self.doc.write_text("An NPC, `npc_tomas_reed`.\n", encoding="utf-8")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = check_doc_examples.main(["--all"])
        self.assertEqual(code, 1)
        self.assertIn("a_test.py", out.getvalue())

    def test_all_does_not_apply_the_id_rule_to_code(self):
        (self.root / "tools" / "a_test.py").write_text('x = "evt_made_up_here"\n', encoding="utf-8")
        self.doc.write_text("An NPC, `npc_tomas_reed`.\n", encoding="utf-8")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = check_doc_examples.main(["--all"])
        self.assertEqual(code, 0, out.getvalue())

    def test_no_demo_world_passes_and_says_so(self):
        (self.root / "template" / "example-world" / "world.config.yaml").unlink()
        code, out = self.run_check("`npc_halvard_sorn`\n")
        self.assertEqual(code, 0)
        self.assertIn("no demo world", out)

    def test_a_named_path_limits_the_check(self):
        other = self.root / "notes.md"
        other.write_text("`npc_halvard_sorn`\n", encoding="utf-8")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = check_doc_examples.main([str(other)])
        self.assertEqual(code, 1, out.getvalue())


if __name__ == "__main__":
    unittest.main()

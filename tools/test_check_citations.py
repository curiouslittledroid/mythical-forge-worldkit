#!/usr/bin/env python3
"""Tests for tools/check_citations.py. citations: ignore (the fixtures cite documents that
only exist inside each test).

Run: python3 tools/test_check_citations.py"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_citations  # noqa: E402

REAL_ROOT = check_citations.ROOT


class VaultCase(unittest.TestCase):
    """A throwaway repository: documents with numbered sections, and files citing them."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        check_citations.ROOT = self.root
        self.docs = {"meta/conventions/conventions.md": "# Conventions\n## 7. Audience\n### 7.4 Secrets\n## 9. Ids\n"}
        for rel, text in self.docs.items():
            (self.root / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.root / rel).write_text(text, encoding="utf-8")

    def tearDown(self):
        check_citations.ROOT = REAL_ROOT
        self.tmp.cleanup()

    def write(self, rel: str, text: str) -> None:
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def issues(self, rel: str = "note.md") -> list[tuple[int, str, str]]:
        return check_citations.check_file(self.root / rel, rel, check_citations.scan_docs(self.root))


class TestResolves(VaultCase):
    def test_the_number_it_names(self):
        self.write("note.md", "See the kit's `meta/conventions/conventions.md` §7.4 for the rule.\n")
        self.assertEqual([], self.issues())

    def test_a_prose_name_for_a_kit_document(self):
        self.write("note.md", "Disclosure is conventions §7. Nothing else.\n")
        self.assertEqual([], self.issues())

    def test_a_parent_number_satisfied_by_its_children(self):
        self.write("note.md", "The whole of `meta/conventions/conventions.md` §7 applies.\n")
        self.assertEqual([], self.issues())

    def test_a_numbered_table_row(self):
        self.docs["maps/atlas.md"] = "# Atlas\n## 14. Corrections\n| 14.32 | a row |\n"
        self.write("maps/atlas.md", self.docs["maps/atlas.md"])
        self.write("note.md", "`maps/atlas.md` §14.32 records it.\n")
        self.assertEqual([], self.issues())

    def test_the_files_own_numbering(self):
        self.write("ROADMAP.md", "# Roadmap\n## 0.1 Layout\n### 0.1.1 More\n\nStep 0.1.1 is done.\n")
        self.assertEqual([], self.issues("ROADMAP.md"))

    def test_a_document_named_in_the_sentence_introducing_a_list(self):
        self.write("note.md", "`meta/conventions/conventions.md` numbers these:\n\n- §7.4 secrets\n- §9 ids\n")
        self.assertEqual([], self.issues())


class TestFails(VaultCase):
    def test_a_number_the_document_does_not_have(self):
        self.write("note.md", "See `meta/conventions/conventions.md` §7.9.\n")
        (line, level, message), = self.issues()
        self.assertEqual("error", level)
        self.assertIn("§7.9", message)
        self.assertIn("meta/conventions/conventions.md", message)

    def test_a_document_that_numbers_nothing(self):
        self.write("meta/conventions/atlas.md", "# Atlas\n## What it is\n")
        self.write("note.md", "See `meta/conventions/atlas.md` §4.\n")
        (_, level, message), = self.issues()
        self.assertEqual("error", level)
        self.assertIn("numbers nothing", message)

    def test_a_path_that_does_not_exist(self):
        self.write("note.md", "See `meta/conventions/site.md` §4.\n")
        (_, level, message), = self.issues()
        self.assertEqual("error", level)
        self.assertIn("no document matches", message)

    def test_the_files_own_numbering_when_it_is_wrong(self):
        self.write("ROADMAP.md", "# Roadmap\n## 0.1 Layout\n\nThe plan is in section 6.5.\n")
        (line, level, message), = self.issues("ROADMAP.md")
        self.assertEqual("error", level)
        self.assertIn("§6.5", message)


class TestDeliberatelySkipped(VaultCase):
    def test_historical_citations(self):
        self.write("note.md", "The spec (formerly `meta/conventions/conventions.md` §3.4) moved out.\n")
        self.assertEqual([], self.issues())

    def test_the_platforms_specs(self):
        self.write("note.md", "The engine is closed over the SRD (Design 23 §1.1).\n")
        self.assertEqual([], self.issues())

    def test_a_worlds_own_document_is_not_checked_here(self):
        """The kit cites a world's atlas register, which only a world has -- reported, not failed."""
        self.write("note.md", "Update `maps/atlas-register.md` §14.\n")
        (_, level, message), = self.issues()
        self.assertEqual("note", level)
        self.assertIn("does not have", message)

    def test_a_note_that_numbers_nothing_warns_rather_than_failing(self):
        """A changelog can say "a world note's section 6" without citing a document."""
        self.write("world/notes.md", "no headings here\n")
        self.write("note.md", "`world/notes.md` told authors about its section 6.\n")
        (_, level, _), = self.issues()
        self.assertEqual("warning", level)

    def test_a_vault_note_that_numbers_nothing_does_not_shadow(self):
        self.write("world/places/a.md", "---\nid: loc_a\n---\n\nNo headings here.\n")
        self.write("note.md", "`world/places/a.md` and `meta/conventions/conventions.md` §9 ids.\n")
        self.assertEqual([], self.issues())


class TestWarnings(VaultCase):
    def test_an_ambiguous_basename_warns(self):
        self.write("meta/notes.md", "# Notes\n## 4. Four\n")
        self.write("docs/notes.md", "# Notes\n## 4. Four\n")
        self.write("note.md", "See `notes.md` §4.\n")
        (_, level, message), = self.issues()
        self.assertEqual("warning", level)
        self.assertIn("Cite the path", message)


class AsWorldCase(unittest.TestCase):
    """`--as-world`: the documents where a WORLD holds them, beside the demo world.

    The defect this exists for is not a wrong number, it is a number that binds to a different
    document in the two layouts. The kit skips `template/` and `example-world/` (a template's notes
    belong to another world, and indexing them would resolve citations meant for the kit's), so a
    guide sentence whose nearest prior document name was `the-ferrymans-debt.md` read fine here and
    failed in every world: the file exists there, it carries no numbered sections, and the sentence's
    "section 8.2" bound to it. It reached a release, because the only check that could see it sat
    behind the engine's schemas.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.kit = Path(self.tmp.name)
        # The kit's layout: the guide under template/, the demo world beside it, the thread note
        # numbering nothing (a plot-web note has prose, not sections).
        files = {
            "template/meta/conventions/guide.md":
                "# Guide\n## 8.1 Writing the threads\n"
                "`the-ferrymans-debt.md` is Resolvable. {citation} sketches a Managed one.\n"
                "## 8.2 Bounded cycles\nA Managed thread, sketched.\n",
            "template/example-world/world/plot-web/the-ferrymans-debt.md":
                "---\nid: thread_ferry\n---\n\nThe ferryman takes his fee.\n",
        }
        for rel, text in files.items():
            path = self.kit / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text.format(citation="section 8.2"), encoding="utf-8")

    def tearDown(self):
        check_citations.ROOT = REAL_ROOT
        self.tmp.cleanup()

    def run_mode(self) -> list[str]:
        saved, check_citations.ROOT = check_citations.ROOT, self.kit
        try:
            tmp, world = check_citations.as_world(self.kit)
            try:
                check_citations.ROOT = world
                docs = check_citations.scan_docs(world)
                rel = "meta/conventions/guide.md"
                return [f"{level}: {message}"
                        for _, level, message in check_citations.check_file(world / rel, rel, docs)]
            finally:
                tmp.cleanup()
        finally:
            check_citations.ROOT = saved

    def test_the_prose_that_failed_in_a_world(self):
        """The regression: it is an error here, and it was silent in the kit's own layout."""
        issues = self.run_mode()
        self.assertEqual(1, len(issues), issues)
        self.assertTrue(issues[0].startswith("error:"), issues[0])
        self.assertIn("numbers nothing", issues[0])

    def test_naming_the_section_instead_is_clean(self):
        """How it was fixed: cite the section by name, which is what the error asks for."""
        path = self.kit / "template/meta/conventions/guide.md"
        path.write_text(path.read_text().replace("section 8.2 sketches", "*Bounded cycles* sketches"),
                        encoding="utf-8")
        self.assertEqual([], self.run_mode())

    def test_the_kit_layout_alone_cannot_see_it(self):
        """Why the mode exists: `example-world/` is skipped, so the same guide passes there."""
        docs = check_citations.scan_docs(self.kit)
        rel = "template/meta/conventions/guide.md"
        self.assertEqual([], check_citations.check_file(self.kit / rel, rel, docs))


if __name__ == "__main__":
    unittest.main()

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
        self.docs = {"docs/conventions.md": "# Conventions\n## 7. Audience\n### 7.4 Secrets\n## 9. Ids\n"}
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
        self.write("note.md", "See the kit's `docs/conventions.md` §7.4 for the rule.\n")
        self.assertEqual([], self.issues())

    def test_a_prose_name_for_a_kit_document(self):
        self.write("note.md", "Disclosure is conventions §7. Nothing else.\n")
        self.assertEqual([], self.issues())

    def test_a_parent_number_satisfied_by_its_children(self):
        self.write("note.md", "The whole of `docs/conventions.md` §7 applies.\n")
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
        self.write("note.md", "`docs/conventions.md` numbers these:\n\n- §7.4 secrets\n- §9 ids\n")
        self.assertEqual([], self.issues())


class TestFails(VaultCase):
    def test_a_number_the_document_does_not_have(self):
        self.write("note.md", "See `docs/conventions.md` §7.9.\n")
        (line, level, message), = self.issues()
        self.assertEqual("error", level)
        self.assertIn("§7.9", message)
        self.assertIn("docs/conventions.md", message)

    def test_a_document_that_numbers_nothing(self):
        self.write("docs/atlas.md", "# Atlas\n## What it is\n")
        self.write("note.md", "See `docs/atlas.md` §4.\n")
        (_, level, message), = self.issues()
        self.assertEqual("error", level)
        self.assertIn("numbers nothing", message)

    def test_a_path_that_does_not_exist(self):
        self.write("note.md", "See `docs/site.md` §4.\n")
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
        self.write("note.md", "The spec (formerly `docs/conventions.md` §3.4) moved out.\n")
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
        self.write("note.md", "`world/places/a.md` and `docs/conventions.md` §9 ids.\n")
        self.assertEqual([], self.issues())


class TestWarnings(VaultCase):
    def test_an_ambiguous_basename_warns(self):
        self.write("meta/notes.md", "# Notes\n## 4. Four\n")
        self.write("docs/notes.md", "# Notes\n## 4. Four\n")
        self.write("note.md", "See `notes.md` §4.\n")
        (_, level, message), = self.issues()
        self.assertEqual("warning", level)
        self.assertIn("Cite the path", message)


if __name__ == "__main__":
    unittest.main()

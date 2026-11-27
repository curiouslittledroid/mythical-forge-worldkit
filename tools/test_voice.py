#!/usr/bin/env python3
"""Tests for tools/voice_lint.py and tools/voice_stale.py. Run: python3 tools/test_voice.py

The rule that matters: a teller may not say a word that is not hers, and may not describe a place
she has never been to. Everything else about a voice is for a human to read.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lint  # noqa: E402
import site_export  # noqa: E402
import voice_lint  # noqa: E402
import testkit  # noqa: E402
import voice_stale  # noqa: E402

REAL_ROOT = lint.ROOT

BOOK = "world/items-materials/book.md"
SHEETS = """
## Author Notes
**Sabel Cray** — wrecker, Dustport. Cannot read; dictates.

| | |
|---|---|
| **Range** | [[dustport|Dustport]], [[the-dry-sea|the Dry Sea]] |
| **Never says** | leyline, resonant, provenance — she says "the chain" |

**Tilda Ordway** — penny-writer, Saltmarch.

| | |
|---|---|
| **Range** | [[saltmarch|Saltmarch]] |
| **Never says** | fathom, seabed |
"""


def note(id_, kind, title, body, extra="", disclosure="open"):
    disc = f"disclosure: {disclosure}\n" if disclosure else ""
    return ("---\n"
            f"id: {id_}\nkind: {kind}\ntitle: {title}\nname_status: working\nstatus: working\n"
            f"{disc}{extra}engine: false\n---\n\n# {title}\n\n**Summary:** A summary.\n\n{body}")


def note_at(rel: str):
    """A fixture note, by path. `load_notes()` order is not part of a test's contract, and the
    fixture vault now also carries the config's vocabulary note."""
    return {n.rel: n for n in lint.load_notes()}[rel]


def account(teller: str, text: str) -> str:
    return ("## Testimony\n**Disclosure:** open\n"
            f"**{teller}**, told to him at the slips.\n\n{text}\n")


class VoiceCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        lint.ROOT = self.root
        # The tools are config-driven (T1): a fixture vault needs a config, and it uses the
        # world's own so the vocabulary is the real one.
        testkit.write_config(self.root)

    def tearDown(self):
        lint.ROOT = REAL_ROOT
        self.tmp.cleanup()

    def write(self, rel: str, text: str) -> None:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def vault(self, account_body: str, teller="Sabel Cray") -> None:
        self.write("world/places/dustport.md", note("loc_dustport", "SETTLEMENT", "Dustport",
                                                    "## Details\n- hulks\n"))
        self.write("world/places/highwell.md", note("loc_highwell", "SETTLEMENT", "Highwell",
                                                    "## Details\n- water\n"))
        self.write(BOOK, note("item_book", "ITEM", "The Book",
                              "## Details\n- quires\n" + SHEETS + "\n" + account_body
                              if "## Testimony" in account_body else
                              "## Details\n- quires\n" + SHEETS, extra="testimony_index: true\n"))
        if "## Testimony" in account_body:
            self.write("world/items-materials/a.md",
                       note("item_a", "ITEM", "A chit",
                            "## Details\n- a token\n\n" + account_body))

    def run_lint(self) -> int:
        return voice_lint.main(["--book", BOOK])


class TestSheets(VoiceCase):
    def test_sheets_parse_name_range_and_vocabulary(self):
        self.write(BOOK, note("item_book", "ITEM", "The Book", "## Details\n- x\n" + SHEETS))
        sheets = voice_lint.parse_sheets(note_at(BOOK).text)
        self.assertEqual(sorted(sheets), ["Sabel Cray", "Tilda Ordway"])
        self.assertEqual(sheets["Sabel Cray"]["range"], {"dustport", "the-dry-sea"})
        self.assertEqual(sheets["Sabel Cray"]["never"], ["leyline", "resonant", "provenance"])
        # The free-text tail after an em-dash is not a forbidden word.
        self.assertNotIn("she says", " ".join(sheets["Sabel Cray"]["never"]))

    def test_a_missing_book_is_an_error(self):
        self.write("world/places/dustport.md", note("loc_dustport", "SETTLEMENT", "Dustport",
                                                    "## Details\n- hulks\n"))
        self.assertEqual(voice_lint.main(["--book", BOOK]), 1)


class TestVoiceLint(VoiceCase):
    def test_a_clean_account_passes(self):
        self.vault(account("Sabel Cray", "We came in on a rope and the wind was against us."))
        self.assertEqual(self.run_lint(), 0)

    def test_a_forbidden_word_fails(self):
        self.vault(account("Sabel Cray", "The resonant thing of it is the clay."))
        self.assertEqual(self.run_lint(), 1)

    def test_a_word_another_teller_owns_is_fine(self):
        self.vault(account("Tilda Ordway", "The clay is resonant grit and the pans know it."))
        self.assertEqual(self.run_lint(), 0)

    def test_a_place_outside_the_range_fails(self):
        self.vault(account("Sabel Cray", "You carry it up to [Highwell](/places/highwell/) and queue."))
        self.assertEqual(self.run_lint(), 1)

    def test_a_place_inside_the_range_passes(self):
        self.vault(account("Sabel Cray", "You carry it down to [Dustport](/places/dustport/) and spend it."))
        self.assertEqual(self.run_lint(), 0)

    def test_a_concept_link_is_not_a_place(self):
        self.write("world/society/economy.md", note("topic_economy", "TOPIC", "Economy",
                                                    "## Details\n- money\n"))
        self.vault(account("Sabel Cray", "It is [economy](/world/economy/) and nothing else."))
        self.assertEqual(self.run_lint(), 0)

    def test_a_table_escaped_range_link_is_unescaped(self):
        # A range row is a table row, so its wikilinks carry the `\|` escape.
        sheets = voice_lint.parse_sheets(
            "## Author Notes\n**T** — x\n\n| | |\n|---|---|\n"
            "| **Range** | [[the-godbleed-corpse\\|the corpse]] |\n")
        self.assertEqual(sheets["T"]["range"], {"the-godbleed-corpse"})

    def test_an_unknown_teller_is_a_warning_not_an_error(self):
        self.vault(account("Some Stranger", "I have been everywhere and said everything."))
        self.assertEqual(self.run_lint(), 0)


class TestDating(unittest.TestCase):
    """An account may be old on purpose; an undated one claims to be current (the kit's `meta/conventions/site.md` 3.5)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        lint.ROOT = self.root
        # The tools are config-driven (T1): a fixture vault needs a config, and it uses the
        # world's own so the vocabulary is the real one.
        testkit.write_config(self.root)

    def tearDown(self):
        lint.ROOT = REAL_ROOT
        self.tmp.cleanup()

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def test_the_present_year_is_read_from_the_chronology_block(self):
        self.write("world/society/calendar.md",
                   note("topic_calendar", "TOPIC", "The Calendar",
                        "## Details\nThe present is about CY 650.\n"
                        "## Author Notes\n\n```chronology\ndate_prefix: CY\npresent: 650\n```\n"))
        current, source = voice_stale.present_year(lint.load_notes())
        self.assertEqual(current, 650)
        self.assertEqual(source, "world/society/calendar.md")

    def test_prose_alone_does_not_give_a_present_year(self):
        """Zero means unknown (D18): the caller skips the comparison rather than guessing a
        year, because a guessed present year invents staleness verdicts."""
        self.write("world/society/calendar.md",
                   note("topic_calendar", "TOPIC", "The Calendar",
                        "## Details\nThe present is about CY 650.\n"))
        current, source = voice_stale.present_year(lint.load_notes())
        self.assertEqual(current, 0)
        self.assertIn("no `chronology` block", source)

    def test_the_teller_is_the_bold_run_that_is_not_the_date(self):
        teller, taken = site_export.entry_ident(
            "**CY 649, in the BLAZE.** **Sabel Cray**, at the slips in Dustport — told to me.")
        self.assertEqual((teller, taken), ("Sabel Cray", 649))

    def test_an_older_heading_form_still_reads(self):
        teller, taken = site_export.entry_ident("**Bela of Mirewell**, told to me in CY 648.")
        self.assertEqual((teller, taken), ("Bela of Mirewell", 648))

    def test_the_year_is_taken_from_the_transmission_line(self):
        self.write("world/places/a.md", note(
            "loc_a", "SETTLEMENT", "A",
            "## Details\n- lore\n\n## Testimony\n**Disclosure:** open\n"
            "**CY 649, in the BLAZE.** **Sabel Cray**, at the slips — told to me.\n\nText.\n"))
        self.assertEqual(voice_stale.taken_year(note_at("world/places/a.md"), "Testimony"), 649)

    def test_an_account_with_no_year_is_undated(self):
        self.write("world/places/a.md", note(
            "loc_a", "SETTLEMENT", "A",
            "## Details\n- lore\n\n## Testimony\n**Disclosure:** open\n"
            "**Sabel Cray**, told to me at the slips.\n\nText.\n"))
        self.assertEqual(voice_stale.taken_year(note_at("world/places/a.md"), "Testimony"), 0)


class TestStaleness(unittest.TestCase):
    """The comparison itself, without git: synthetic blame times."""

    def test_body_newer_than_voice_is_stale(self):
        verse, body = {1, 2, 3}, {4, 5, 6}
        self.assertGreater(voice_stale.newest({1: 10, 2: 20, 3: 30}, verse),
                           voice_stale.newest({4: 5, 5: 6, 6: 7}, body))

    def test_the_same_commit_reads_as_fine(self):
        times = {n: 42 for n in range(1, 7)}
        self.assertEqual(voice_stale.newest(times, {1, 2}), voice_stale.newest(times, {3, 4}))

    def test_a_missing_section_is_not_newest(self):
        self.assertEqual(voice_stale.newest({1: 99}, {2, 3}), 0)

    def test_sections_split_at_h2(self):
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        lint.ROOT = root
        try:
            path = root / "world" / "places" / "a.md"
            path.parent.mkdir(parents=True)
            path.write_text(note("loc_a", "SETTLEMENT", "A",
                                 "## Details\n- one\n- two\n\n## Testimony\n**Disclosure:** open\n"
                                 "**T** , told.\n\nthree\n"), encoding="utf-8")
            n = lint.load_notes()[0]
            voice, body = voice_stale.section_lines(n, "Testimony")
            self.assertFalse(voice & body)
            self.assertTrue(voice)
            self.assertTrue({ln for ln in body if ln} )
        finally:
            lint.ROOT = REAL_ROOT
            tmp.cleanup()


if __name__ == "__main__":
    unittest.main()

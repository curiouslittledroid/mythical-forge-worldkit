#!/usr/bin/env python3
"""Tests for tools/lore_export.py. Run: python3 tools/test_lore_export.py"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lint  # noqa: E402
import lore_export  # noqa: E402

REAL_ROOT = lint.ROOT


def note(nid="npc_a", kind="NPC", extra="", body="", title="A"):
    return (
        f"---\nid: {nid}\nkind: {kind}\ntitle: {title}\nname_status: working\nstatus: working\n"
        f"engine: false\n{extra}---\n\n# {title}\n\n**Summary:** A reasonably long summary.\n\n{body}"
    )


class Corpus(unittest.TestCase):
    """Builds a throwaway vault, then runs the exporter over it."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        lint.ROOT = Path(self.tmp.name)
        (lint.ROOT / "world").mkdir()

    def tearDown(self):
        lint.ROOT = REAL_ROOT
        self.tmp.cleanup()

    def build(self, files: dict[str, str]):
        for name, text in files.items():
            path = lint.ROOT / "world" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        notes = [n for n in lint.load_notes() if n.rel.startswith("world/")]
        chunks, warnings = lore_export.build_chunks(notes)
        return chunks, warnings, lore_export.npc_index(notes)

    def one(self, text, **kw):
        chunks, _, _ = self.build({"a.md": text})
        return [c for c in chunks if c["topic"] == kw.get("topic", "npc_a")]

    def one_in(self, text, heading, **kw):
        return [c for c in self.one(text, **kw) if c["heading"] == heading]


class TestChunking(Corpus):
    def test_one_chunk_per_paragraph(self):
        chunks = self.one_in(note(extra="disclosure: open\n", body="## Details\nFirst para.\n\nSecond para.\n"), "Details")
        self.assertEqual([c["text"] for c in chunks], ["First para.", "Second para."])

    def test_the_summary_is_a_chunk(self):
        chunks = self.one(note(extra="disclosure: open\n", body="## Details\nBody.\n"))
        self.assertEqual(chunks[0]["heading"], "Summary")
        self.assertEqual(chunks[0]["text"], "**Summary:** A reasonably long summary.")

    def test_history_layers_split_and_keep_their_layer(self):
        body = (
            "## Details\n**Official:** The Church says the Cup is holy.\n"
            "**Myth:** Old wives say it is well water.\n"
            "**Truth:** It is deep water.\n"
        )
        chunks = self.one(note(nid="hist_x", kind="HISTORY_EVENT", extra="disclosure: open\n", body=body), topic="hist_x")
        got = {c["layer"]: c["text"] for c in chunks}
        self.assertEqual(got["official"], "The Church says the Cup is holy.")
        self.assertEqual(got["myth"], "Old wives say it is well water.")
        self.assertEqual(got["truth"], "It is deep water.")
        self.assertNotIn("official", got["truth"])

    def test_a_mixed_section_takes_its_class_from_the_layer(self):
        body = (
            "## Details\n**Official:** The Church says the Cup is holy.\n"
            "**Truth:** It is deep water.\n"
        )
        chunks = self.one(
            note(nid="hist_x", kind="HISTORY_EVENT", extra="disclosure: open\n", body=body), topic="hist_x"
        )
        got = {c["layer"]: c["disclosure"] for c in chunks}
        self.assertEqual(got["official"], "open")  # conventions 7.3 rule 3
        self.assertEqual(got["truth"], "earned")  # conventions 7.3 rule 4

    def test_an_over_cap_paragraph_splits_at_sentence_boundaries(self):
        sentence = "The sea walks uphill and the salt remembers. "
        chunks = self.one(note(extra="disclosure: open\n", body="## Details\n" + sentence * 80 + "\n"))
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(c["_words"] <= lore_export.MAX_WORDS + 12 for c in chunks))

    def test_chunk_ids_are_stable_and_legal(self):
        body = "## Keystone secrets\n**Disclosure:** sealed\nThe cult serves what sleeps in it.\n"
        chunks = self.one_in(note(extra="disclosure: open\n", body=body), "Keystone secrets")
        self.assertEqual(chunks[0]["id"], "lore_npc_a_keystone_secrets_01")
        self.assertRegex(chunks[0]["id"], r"^[a-z][a-z0-9]*(_[a-z0-9]+)+$")

    def test_not_lore_sections_are_dropped(self):
        body = "## Details\nSeen.\n\n## Hooks\n- a thread goes here\n\n## Author Notes\n- Step 12\n"
        chunks = self.one(note(extra="disclosure: open\n", body=body))
        self.assertEqual([c["heading"] for c in chunks], ["Summary", "Details"])


class TestAudience(Corpus):
    def test_open_is_world(self):
        chunks = self.one_in(note(extra="disclosure: open\n", body="## Details\nPublic.\n"), "Details")
        self.assertEqual(chunks[0]["audience"], {"scope": "world"})

    def test_a_faction_secret_is_its_inner_circle(self):
        body = "## Secrets\nHidden.\n\n## Keystone secrets\n**Disclosure:** sealed\nDeeper.\n"
        chunks = self.one(note(nid="faction_x", kind="FACTION", extra="disclosure: earned\n", body=body), topic="faction_x")
        by_heading = {c["heading"]: c["audience"] for c in chunks}
        self.assertEqual(by_heading["Secrets"], {"scope": "faction", "groups": ["faction_x"], "tiers": ["select"]})
        self.assertEqual(by_heading["Keystone secrets"], {"scope": "faction", "groups": ["faction_x"], "tiers": ["inner"]})

    def test_an_npcs_own_secret_and_want_are_self(self):
        body = "## Details\n**Want:** to be remembered.\n\n## Secrets\nHe did it.\n"
        chunks = self.one(note(extra="disclosure: open\n", body=body))
        by_heading = {c["heading"]: c["audience"] for c in chunks}
        self.assertEqual(by_heading["Details"], {"scope": "self", "about": "npc_a"})
        self.assertEqual(by_heading["Secrets"], {"scope": "self", "about": "npc_a"})

    def test_known_by_overrides_the_default(self):
        body = "## Secrets\n**Known by:** faction_wardens@inner, race_elf\nHidden.\n"
        chunks = self.one_in(note(extra="disclosure: earned\n", body=body), "Secrets")
        self.assertEqual(chunks[0]["audience"], {"scope": "faction", "groups": ["faction_wardens", "race_elf"], "tiers": ["inner", "common"]})

    def test_an_earned_place_section_is_scoped_to_its_zone(self):
        body = "## Secrets\nSomething local.\n"
        chunks = self.one_in(
            note(nid="loc_x", kind="SETTLEMENT", extra="disclosure: open\nzone: zone_dry_sea\n", body=body),
            "Secrets",
            topic="loc_x",
        )
        self.assertEqual(chunks[0]["audience"], {"scope": "zone", "about": "zone_dry_sea"})


class TestResolution(unittest.TestCase):
    npc = {"id": "npc_a", "race": "race_elf", "zone": "zone_dry_sea", "groups": [("faction_wardens", "select")]}

    def test_scopes(self):
        self.assertTrue(lore_export.knows({"scope": "world"}, self.npc))
        self.assertTrue(lore_export.knows({"scope": "zone", "about": "zone_dry_sea"}, self.npc))
        self.assertFalse(lore_export.knows({"scope": "zone", "about": "zone_green_belt"}, self.npc))
        self.assertTrue(lore_export.knows({"scope": "self", "about": "npc_a"}, self.npc))
        self.assertFalse(lore_export.knows({"scope": "self", "about": "npc_b"}, self.npc))

    def test_tiers_nest_and_races_ignore_them(self):
        sel = {"scope": "faction", "groups": ["faction_wardens"], "tiers": ["select"]}
        inner = {"scope": "faction", "groups": ["faction_wardens"], "tiers": ["inner"]}
        self.assertTrue(lore_export.knows(sel, self.npc))  # select >= select
        self.assertFalse(lore_export.knows(inner, self.npc))  # select < inner
        self.assertTrue(lore_export.knows({"scope": "faction", "groups": ["race_elf"], "tiers": ["inner"]}, self.npc))
        self.assertFalse(lore_export.knows({"scope": "faction", "groups": ["faction_other"], "tiers": ["common"]}, self.npc))


class TestSubjects(Corpus):
    def test_wikilinks_are_the_subject_index(self):
        self.build(
            {
                "npcs/a.md": note(extra="disclosure: open\n", body="## Details\nHe hails from [[ashport|Ashport]].\n"),
                "settlements/ashport.md": note(nid="loc_ashport", kind="SETTLEMENT", extra="disclosure: open\n", title="Ashport"),
            }
        )
        notes = [n for n in lint.load_notes() if n.rel.startswith("world/")]
        chunks, _ = lore_export.build_chunks(notes)
        chunk = next(c for c in chunks if c["heading"] == "Details" and c["topic"] == "npc_a")
        self.assertIn("loc_ashport", chunk["subjects"])
        self.assertIn("npc_a", chunk["subjects"])
        self.assertIn("Ashport", chunk["text"])  # the label, not the link syntax
        self.assertNotIn("[[", chunk["text"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

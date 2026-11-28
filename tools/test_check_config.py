#!/usr/bin/env python3
"""Tests for tools/check_config.py. Run: python3 tools/test_check_config.py

Every check gets a fixture that breaks exactly one thing, because the failure mode this tool
exists for is a *wrong* answer: it must be silent on a coherent world and it must name the key that
is not. The suite also asks two questions nothing else can: that the live world (the kit's demo
world, or a world holding these tools) is coherent, and that the two config readers agree about it.
"""
from __future__ import annotations

import io
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_config  # noqa: E402
import testkit  # noqa: E402

CONFIG = """\
version: 1
world:
  id: world_test
  title: Test
  slug: test
vault:
  notes:
    flags: topic_flags
    calendar: topic_calendar
    eras: topic_eras
    site_vocabulary: topic_site_decisions
  process_docs:
    - README.md
    - NOTES.md
  scenarios: campaigns/test/scenarios
features: [site]
site:
  url: https://example.invalid/test
  sections:
    - slug: world
      label: The World
      kinds: [TOPIC]
    - slug: places
      label: Places
      kinds: [SETTLEMENT]
    - slug: people
      label: People
      kinds: [NPC]
"""

FLAGS = "```flags\n- id: quay_armed\n  description: The quay is armed.\n```"
CALENDAR = "```chronology\ndate_prefix: CY\npresent: 650\n```"
ERAS = "```eras\norder:\n  - first\n  - second\n```"
VOCABULARY = ("```site-vocabulary\npublished_tags: [quay]\nkeystones: []\n"
              "plot_web_surfaces: []\n```")
TAGS = "```tags-vocabulary\nquay: [quay]\n```"


def note(note_id, kind="TOPIC", engine="false", block=None):
    head = (f"---\nid: {note_id}\nkind: {kind}\ntitle: T\nname_status: working\n"
            f"status: working\nengine: {engine}\n---\n\n# T\n\n**Summary:** A fixture note.\n\n")
    return head + (block + "\n" if block else "")


class Fixture(unittest.TestCase):
    """A minimal coherent world, which each test breaks in one place."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        self.write("world.config.yaml", CONFIG)
        self.write("README.md", "# Read me\n")
        self.write("NOTES.md", "# Notes\n")
        self.write("meta/flags.md", note("topic_flags", block=FLAGS))
        self.write("meta/calendar.md", note("topic_calendar", block=CALENDAR))
        self.write("meta/eras.md", note("topic_eras", block=ERAS))
        self.write("meta/site-decisions.md", note("topic_site_decisions", block=VOCABULARY))
        self.write("world/places/quay.md", note("loc_quay", "SETTLEMENT"))
        (self.root / "campaigns/test/scenarios").mkdir(parents=True)

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def replace(self, rel, old, new):
        path = self.root / rel
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text, f"the fixture no longer contains {old!r}")
        path.write_text(text.replace(old, new, 1), encoding="utf-8")

    def findings(self):
        return check_config.findings(self.root)

    def messages(self, level="ERROR"):
        """Every finding at one level, joined: a fixture can break one thing in two places."""
        return " | ".join(f.message for f in self.findings() if f.level == level)


class CleanWorldCase(Fixture):
    def test_a_coherent_world_is_silent(self):
        found = check_config.findings(self.root)
        self.assertEqual([f.message for f in found], [],
                         "a coherent world must produce nothing at all")

    def test_main_exits_zero_and_says_clean(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(check_config.main([str(self.root)]), 0)
        self.assertIn("clean", out.getvalue())

    def test_no_config_is_not_a_world(self):
        (self.root / "world.config.yaml").unlink()
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(check_config.main([str(self.root)]), 0)
        self.assertIn("nothing to check", out.getvalue())


class NotesCase(Fixture):
    def test_an_id_no_note_carries_is_an_error(self):
        self.replace("world.config.yaml", "flags: topic_flags", "flags: topic_gone")
        (self.root / "meta/flags.md").unlink()
        self.assertIn("vault.notes.flags is 'topic_gone'", self.messages())

    def test_a_declared_note_without_its_block_is_an_error(self):
        self.write("meta/eras.md", note("topic_eras"))
        self.assertIn("carries no ```eras``` block", self.messages())

    def test_a_block_that_does_not_parse_is_an_error(self):
        self.write("meta/eras.md", note("topic_eras", block="```eras\norder:\n  - one: two: three\n```"))
        self.assertIn("does not parse", self.messages())

    def test_an_empty_list_block_parses(self):
        """`[]` is how a world says "none yet": the template's own flags note ships it."""
        self.write("meta/flags.md", note("topic_flags", block="```flags\n[]\n```"))
        self.assertFalse([f for f in check_config.findings(self.root) if f.level == "ERROR"])

    def test_an_undeclared_note_is_inert(self):
        self.replace("world.config.yaml", "    eras: topic_eras\n", "")
        (self.root / "meta/eras.md").unlink()
        self.assertEqual([f.message for f in check_config.findings(self.root)], [])


class BlockShapeCase(Fixture):
    def test_a_repeated_era_is_an_error(self):
        self.write("meta/eras.md", note("topic_eras", block="```eras\norder:\n  - one\n  - one\n```"))
        self.assertIn("listed twice", self.messages())

    def test_an_empty_era_order_is_an_error(self):
        self.write("meta/eras.md", note("topic_eras", block="```eras\norder: []\n```"))
        self.assertIn("at least one era", self.messages())

    def test_the_present_year_must_be_a_number(self):
        self.write("meta/calendar.md", note("topic_calendar",
                                            block="```chronology\ndate_prefix: CY\npresent: soon\n```"))
        self.assertIn("must be a number", self.messages())

    def test_a_placeholder_calendar_is_a_note_not_a_failure(self):
        self.write("meta/calendar.md",
                   note("topic_calendar", block="```chronology\ndate_prefix: REPLACE\npresent: REPLACE_ME\n```"))
        found = check_config.findings(self.root)
        self.assertEqual([f for f in found if f.level == "ERROR"], [])
        self.assertEqual([f.level for f in found], ["NOTE", "NOTE"])
        with redirect_stdout(io.StringIO()):
            self.assertEqual(check_config.main([str(self.root)]), 0)

    def test_the_date_prefix_is_short_capitals(self):
        self.write("meta/calendar.md", note("topic_calendar",
                                            block="```chronology\ndate_prefix: cy\npresent: 650\n```"))
        self.assertIn("2-6 capital letters", self.messages())

    def test_a_published_tag_must_be_a_slug(self):
        self.write("meta/site-decisions.md", note(
            "topic_site_decisions", block=VOCABULARY.replace("[quay]", "[Quay]").replace("[quay]", "[Quay]")))
        self.assertTrue(self.messages(), "an upper-case tag is not a slug")

    def test_a_repeated_published_tag_is_an_error(self):
        self.write("meta/site-decisions.md", note(
            "topic_site_decisions", block=VOCABULARY.replace("published_tags: [quay]",
                                                             "published_tags: [quay, quay]")))
        self.assertIn("listed twice", self.messages())

    def test_a_missing_vocabulary_list_is_a_warning(self):
        self.write("meta/site-decisions.md", note(
            "topic_site_decisions", block="```site-vocabulary\npublished_tags: [quay]\n```"))
        self.assertIn("does not declare `keystones:`", self.messages("WARN"))

    def test_a_flag_without_an_id_is_an_error(self):
        self.write("meta/flags.md", note("topic_flags", block="```flags\n- description: no id\n```"))
        self.assertIn("has no `id:`", self.messages())

    def test_a_repeated_flag_is_an_error(self):
        self.write("meta/flags.md", note(
            "topic_flags",
            block="```flags\n- id: a\n  description: x\n- id: a\n  description: y\n```"))
        self.assertIn("declared twice", self.messages())


class SiteSectionsCase(Fixture):
    def test_a_repeated_slug_is_an_error(self):
        self.replace("world.config.yaml", "slug: people", "slug: places")
        self.assertIn("is already used by", self.messages())

    def test_a_kind_claimed_twice_is_an_error(self):
        self.replace("world.config.yaml", "kinds: [NPC]", "kinds: [NPC, SETTLEMENT]")
        self.assertIn("claims kind SETTLEMENT", self.messages())


class DeclaredPathsCase(Fixture):
    def test_a_missing_process_doc_is_a_warning(self):
        (self.root / "NOTES.md").unlink()
        self.assertIn("vault.process_docs lists 'NOTES.md'", self.messages("WARN"))

    def test_a_missing_scenarios_directory_is_a_warning(self):
        shutil.rmtree(self.root / "campaigns")
        self.assertIn("vault.scenarios is", self.messages("WARN"))

    def test_warnings_do_not_fail_the_run(self):
        (self.root / "NOTES.md").unlink()
        with redirect_stdout(io.StringIO()):
            self.assertEqual(check_config.main([str(self.root)]), 0)


class VaultAgainstConfigCase(Fixture):
    def test_a_published_tag_outside_the_vocabulary_is_a_warning(self):
        self.write("meta/tag-vocabulary.md", note("topic_tags", block=TAGS))
        self.replace("meta/site-decisions.md", "published_tags: [quay]",
                     "published_tags: [quay, ferry]")
        self.assertIn("published tag(s) ['ferry'] are not in the world's `tags-vocabulary`",
                      self.messages("WARN"))

    def test_no_vocabulary_block_means_no_question(self):
        self.assertEqual([f for f in self.findings() if f.level == "WARN"], [])

    def test_a_kind_no_section_claims_is_a_warning(self):
        self.write("world/relics/rope.md", note("item_rope", "ITEM"))
        self.assertIn("kind ITEM is used by 1 note(s)", self.messages("WARN"))

    def test_an_engine_entity_needs_no_section(self):
        self.write("world/relics/rope.md", note("item_rope", "ITEM", engine="true"))
        self.assertEqual([f.message for f in check_config.findings(self.root)], [])

    def test_a_deferred_kind_needs_no_section(self):
        self.write("world/relics/rope.md", note("item_rope", "ITEM"))
        self.replace("world.config.yaml", "  sections:", "  deferred_kinds: [ITEM]\n  sections:")
        self.assertEqual([f.message for f in check_config.findings(self.root)], [])


class ParityCase(Fixture):
    """The two readers must agree about the live config. The checker itself must not cry wolf."""

    def test_the_readers_agree_about_this_fixture(self):
        if not check_config.shutil.which("node"):
            self.skipTest("node is not installed")
        cfg = check_config.kit_config.load(self.root / "world.config.yaml")
        self.assertEqual(check_config.parity(cfg, self.root), [])

    def test_a_list_order_difference_is_not_a_disagreement(self):
        """`process_docs` is a frozenset in Python and the file's order in Node. The first version
        of this check reported that as a disagreement in every world with two process documents."""
        if not check_config.shutil.which("node"):
            self.skipTest("node is not installed")
        self.replace("world.config.yaml", "    - README.md\n    - NOTES.md\n",
                     "    - NOTES.md\n    - README.md\n")
        cfg = check_config.kit_config.load(self.root / "world.config.yaml")
        self.assertEqual(check_config.parity(cfg, self.root), [])

    def test_a_real_disagreement_is_reported_as_a_tooling_defect(self):
        cfg = check_config.kit_config.load(self.root / "world.config.yaml")
        output = '{"world_id": "world_other", "title": "Test", "slug": "test", "overland": "",' \
                 ' "game_ready_repo": "", "features": [], "notes": {}, "process_docs": [],' \
                 ' "scenarios_dir": null, "spelling": "british", "site": null, "blocks": {}}'
        fake = mock.Mock(returncode=0, stdout=output, stderr="")
        with mock.patch.object(check_config.shutil, "which", return_value="/usr/bin/node"), \
             mock.patch.object(check_config.subprocess, "run", return_value=fake):
            found = check_config.parity(cfg, self.root)
        self.assertTrue(found)
        self.assertIn("tooling defect", found[0].message)
        self.assertIn("world_id", found[0].message)

    def test_the_node_reader_failing_to_load_is_an_error(self):
        cfg = check_config.kit_config.load(self.root / "world.config.yaml")
        fake = mock.Mock(returncode=1, stdout="", stderr="Error: expected 'key: value'")
        with mock.patch.object(check_config.shutil, "which", return_value="/usr/bin/node"), \
             mock.patch.object(check_config.subprocess, "run", return_value=fake):
            found = check_config.parity(cfg, self.root)
        self.assertEqual(found[0].level, "ERROR")
        self.assertIn("Node reader cannot read this config", found[0].message)

    def test_no_node_is_a_note_not_a_failure(self):
        cfg = check_config.kit_config.load(self.root / "world.config.yaml")
        with mock.patch.object(check_config.shutil, "which", return_value=None):
            found = check_config.parity(cfg, self.root)
        self.assertEqual([f.level for f in found], ["NOTE"])


class LiveWorldCase(unittest.TestCase):
    """The world these tools are installed in. In the kit that is the demo world, and the kit's own
    `verify-kit.sh` runs this same check.

    It used to be an assertion in `test_kit_config.py` that loaded the live config directly. It
    moved here because the assertion had no *named output*: when a world's config stopped matching
    its vault, the failure was a stack trace in a suite written for the kit's maintainer, in a file
    a world author is told never to edit.
    """

    @classmethod
    def setUpClass(cls):
        cls.root = testkit.REAL_CONFIG.parent

    def test_the_live_world_is_coherent(self):
        found = check_config.findings(self.root)
        errors = [f"{f.where}: {f.message}" for f in found if f.level == "ERROR"]
        self.assertEqual(errors, [])
        self.assertEqual([f.message for f in found if f.level == "WARN"], [])

    def test_the_check_names_the_live_config(self):
        cfg = check_config.kit_config.load(testkit.REAL_CONFIG)
        self.assertRegex(cfg.world_id, r"^world_[a-z0-9_]+$")
        self.assertTrue(cfg.title.strip())
        self.assertTrue(cfg.site, "the demo world publishes a site; a world that does not says "
                                  "so by dropping the feature")
        self.assertRegex(cfg.slug, r"^[a-z0-9-]+$")

    def test_the_site_section_list_is_consistent(self):
        """Shape, not contents: the sections are the world's. Every kind resolves to the section
        that claims it, and a kind nobody claims resolves to nothing."""
        cfg = check_config.kit_config.load(testkit.REAL_CONFIG)
        for section in cfg.site.sections:
            for kind in section.kinds:
                with self.subTest(kind=kind):
                    self.assertEqual(cfg.site.section_of_kind(kind), section.slug)
                    self.assertEqual(cfg.site.label_of(section.slug), section.label)
        self.assertIsNone(cfg.site.section_of_kind("NOT_A_KIND"))
        self.assertEqual(cfg.site.label_of("no-such-section"), "no-such-section")


if __name__ == "__main__":
    unittest.main(verbosity=2)

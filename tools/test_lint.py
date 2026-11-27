#!/usr/bin/env python3
"""Tests for tools/lint.py. Run: python3 tools/test_lint.py"""
from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lint  # noqa: E402
import testkit  # noqa: E402

REAL_ROOT = lint.ROOT


def note(id_="topic_a", kind="TOPIC", title="A", extra="", body=None, status="working", engine="false"):
    body = body if body is not None else "# A\n\n**Summary:** A reasonably long summary line.\n\n## Details\n- text\n"
    return (
        f"---\nid: {id_}\nkind: {kind}\ntitle: {title}\nname_status: working\n"
        f"status: {status}\nengine: {engine}\n{extra}---\n\n{body}"
    )


class VaultCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        lint.ROOT = self.root

    def tearDown(self):
        lint.ROOT = REAL_ROOT
        self.tmp.cleanup()

    def write(self, rel, text):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def codes(self, level=None):
        issues = lint.Linter(lint.load_notes()).run()
        return sorted({i.code for i in issues if level is None or i.level == level})

    def link_all(self, *names):
        """An index that links every note so orphan warnings stay out of the way."""
        self.write("world/_index.md", note("topic_index", "INDEX",
                   body="# I\n\n**Purpose:** a map of content for this test folder.\n\n## Notes\n"
                        + "".join(f"- [[{n}]]\n" for n in names)))
        self.write("README.md", "[[world/_index]]\n")


class TestClean(VaultCase):
    def test_clean_vault_has_no_issues(self):
        self.write("world/a.md", note())
        self.link_all("a")
        self.assertEqual(self.codes(), [])


VOCAB = """---
id: topic_tag_vocabulary
kind: TOPIC
title: Tag Vocabulary
name_status: agreed
status: agreed
engine: false
tags: []
---

# Tag Vocabulary

**Summary:** The tag vocabulary under test.

```tags-vocabulary
peoples: [humans, fae]
powers: [choir]
places: [dustport]
magic: [leylines]
relic_categories: [holy]
choir: [gate-born]
world: [ruins]
gm_only: [gate-born]
homes:
  choir: the-choir
```
"""


class TestTags(VaultCase):
    def vocabulary(self):
        self.write("meta/tag-vocabulary.md", VOCAB)

    def tag_codes(self):
        issues = lint.Linter(lint.load_notes()).run()
        return sorted({i.code for i in issues if i.code.startswith("TG")})

    def test_a_tag_outside_the_vocabulary_is_an_error(self):
        self.vocabulary()
        self.write("world/a.md", note(extra="tags: [npcs, bogus]\n"))
        self.assertEqual(self.tag_codes(), ["TG001"])

    def test_a_vocabulary_tag_passes(self):
        self.vocabulary()
        self.write("world/a.md", note(extra="tags: [ruins, leylines]\n"))
        self.assertEqual(self.tag_codes(), [])

    def test_a_naming_tag_must_resolve_to_a_note(self):
        self.vocabulary()
        self.write("world/a.md", note(extra="tags: [dustport]\n"))
        self.assertEqual(self.tag_codes(), ["TG002"])
        self.write("world/places/dustport.md", note(id_="loc_dustport", kind="SETTLEMENT", title="Dustport"))
        self.assertEqual(self.tag_codes(), [])

    def test_a_home_overrides_the_slug(self):
        self.vocabulary()
        self.write("world/a.md", note(extra="tags: [choir]\n"))
        self.assertEqual(self.tag_codes(), ["TG002"])  # expects the-choir, not choir
        self.write("world/factions/the-choir.md", note(id_="faction_choir", kind="FACTION", title="The Choir"))
        self.assertEqual(self.tag_codes(), [])

    def test_no_vocabulary_block_means_no_tag_check(self):
        self.write("world/a.md", note(extra="tags: [anything]\n"))
        self.assertEqual(self.tag_codes(), [])


class TestDisclosure(VaultCase):
    def test_valid_frontmatter_and_mark_are_clean(self):
        body = "# A\n\n**Summary:** A reasonably long summary line.\n\n## Secrets\n**Disclosure:** sealed\nThe truth.\n"
        self.write("world/a.md", note(extra="disclosure: earned\n", body=body))
        self.link_all("a")
        self.assertEqual(self.codes(), [])

    def test_bad_frontmatter_class(self):
        self.write("world/a.md", note(extra="disclosure: secret\n"))
        self.link_all("a")
        self.assertIn("FM011", self.codes("ERROR"))

    def test_bad_mark(self):
        body = "# A\n\n**Summary:** A reasonably long summary line.\n\n## Secrets\n**Disclosure:** hidden\nThe truth.\n"
        self.write("world/a.md", note(body=body))
        self.link_all("a")
        self.assertIn("DS001", self.codes("ERROR"))

    def test_mark_inside_a_code_block_is_ignored(self):
        body = "# A\n\n**Summary:** A reasonably long summary line.\n\n## Details\n```\n**Disclosure:** hidden\n```\n"
        self.write("world/a.md", note(body=body))
        self.link_all("a")
        self.assertNotIn("DS001", self.codes())


class TestLinks(VaultCase):
    def test_unbalanced_link_is_an_error(self):
        # The Step 0b bug: a generator split `[[giver|Giver's]]` on the pipe.
        self.write("world/a.md", note(body="# A\n\n**Summary:** The [[giver\n\n## Details\n- Giver's]] cult\n"))
        self.link_all("a")
        self.assertIn("LK001", self.codes("ERROR"))

    def test_section_sign_before_digit_is_fine_but_a_separator_is_not(self):
        self.write("world/a.md", note(body="# A\n\n**Summary:** See Design 23 §4 and §5.3 for the model.\n\n## D\n- x\n"))
        self.write("world/b.md", note("topic_b", title="B", body="# B\n\n**Summary:** One sentence.§Another sentence here.\n\n## D\n- x\n"))
        self.link_all("a", "b")
        issues = lint.Linter(lint.load_notes()).run()
        bad = {i.path for i in issues if i.code == "LK002"}
        self.assertEqual(bad, {"world/b.md"})

    def test_dead_link(self):
        self.write("world/a.md", note(body="# A\n\n**Summary:** Points at [[nowhere]] which is missing.\n\n## D\n- x\n"))
        self.link_all("a")
        self.assertIn("LK003", self.codes("ERROR"))

    def test_alias_and_table_escape_resolve(self):
        self.write("world/a.md", note(body="# A\n\n**Summary:** Alias [[b|the B]] works fine here.\n\n| x |\n|---|\n| [[b\\|B]] |\n\n## D\n- x\n"))
        self.write("world/b.md", note("topic_b", title="B", body="# B\n\n**Summary:** A reasonable summary here.\n\n## D\n- x\n"))
        self.link_all("a", "b")
        self.assertEqual(self.codes(), [])

    def test_link_to_yaml_needs_extension(self):
        self.write("maps/data.yaml", "a: 1\n")
        self.write("world/a.md", note(body="# A\n\n**Summary:** Data lives in [[data]] somewhere.\n\n## D\n- x\n"))
        self.link_all("a")
        self.assertIn("LK005", self.codes("ERROR"))

    def test_links_inside_code_are_ignored(self):
        self.write("world/a.md", note(body="# A\n\n**Summary:** Syntax is `[[not a link` in prose.\n\n```\n[[also not\n```\n\n## D\n- x\n"))
        self.link_all("a")
        self.assertEqual(self.codes(), [])

    def test_ambiguous_index_link(self):
        self.write("world/x/_index.md", note("topic_x_index", "INDEX", body="# X\n\n**Purpose:** index of the x folder.\n\n## N\n- y\n"))
        self.write("world/y/_index.md", note("topic_y_index", "INDEX", body="# Y\n\n**Purpose:** index of the y folder.\n\n## N\n- x\n"))
        self.write("world/a.md", note(body="# A\n\n**Summary:** A bare [[_index]] link is ambiguous.\n\n## D\n- x\n"))
        self.write("README.md", "[[a]] [[x/_index]] [[y/_index]]\n")
        self.assertIn("LK004", self.codes("ERROR"))


class TestFrontmatter(VaultCase):
    def test_missing_frontmatter(self):
        self.write("world/a.md", "# A\n\nNo frontmatter.\n")
        self.link_all("a")
        self.assertIn("FM001", self.codes("ERROR"))

    def test_bad_status(self):
        self.write("world/a.md", note(status="finished"))
        self.link_all("a")
        self.assertIn("FM003", self.codes("ERROR"))

    def test_visibility_is_no_longer_read(self):
        # Retired in Step 2e: an old note that still carries the field lints clean.
        self.write("world/a.md", note().replace("engine: false", "visibility: gm\nengine: false"))
        self.link_all("a")
        self.assertFalse(self.codes("ERROR"))

    def test_id_prefix_must_match_kind(self):
        self.write("world/a.md", note(id_="npc_wrong", kind="TOPIC"))
        self.link_all("a")
        self.assertIn("ID002", self.codes("ERROR"))

    def test_bad_id_grammar(self):
        self.write("world/a.md", note(id_="Topic-A"))
        self.link_all("a")
        self.assertIn("ID001", self.codes("ERROR"))

    def test_duplicate_ids_and_filenames(self):
        self.write("world/a.md", note())
        self.write("world/sub/a.md", note(title="A2"))
        self.link_all("a")
        errs = self.codes("ERROR")
        self.assertIn("ID004", errs)
        self.assertIn("FN002", errs)

    def test_filename_must_be_kebab(self):
        self.write("world/My Note.md", note())
        self.link_all("My Note")
        self.assertIn("FN001", self.codes("ERROR"))

    def test_replace_in_required_field(self):
        self.write("world/a.md", note(title="REPLACE"))
        self.link_all("a")
        self.assertIn("FM008", self.codes("ERROR"))

    def test_unknown_group_reference_warns(self):
        self.write("world/a.md", note(extra="group_knowledge:\n  - { group: faction_ghost, tier: inner }\n"))
        self.link_all("a")
        self.assertIn("REF001", self.codes("WARN"))


class TestEngine(VaultCase):
    def fact(self, extra=""):
        return ("# A\n\n**Summary:** Has an engine block for testing it.\n\n## Engine\n"
                "```engine\nkind: FACT\nid: fact_x\ntext: \"t\"\ntruth: TRUE\n" + extra + "```\n")

    def test_real_block_requires_engine_true(self):
        self.write("world/a.md", note(body=self.fact(), engine="false"))
        self.link_all("a")
        self.assertIn("EN001", self.codes("ERROR"))

    def test_engine_true_requires_a_block(self):
        self.write("world/a.md", note(engine="true"))
        self.link_all("a")
        self.assertIn("EN002", self.codes("ERROR"))

    def test_valid_engine_note(self):
        self.write("world/a.md", note(body=self.fact(), engine="true"))
        self.link_all("a")
        self.assertEqual(self.codes(), [])

    def test_derived_values_forbidden(self):
        self.write("world/a.md", note(body=self.fact("hp: 12\nauthor_id: u1\n"), engine="true"))
        self.link_all("a")
        self.assertIn("EN004", self.codes("ERROR"))

    def test_world_id_only_in_campaign(self):
        self.write("world/a.md", note(body=self.fact("world_id: world_x\n"), engine="true"))
        self.link_all("a")
        self.assertIn("EN004", self.codes("ERROR"))

    def test_replace_forbidden_in_real_block_but_fine_in_example(self):
        self.write("world/a.md", note(body=self.fact("subjects: [loc_REPLACE]\n"), engine="true"))
        self.link_all("a")
        self.assertIn("EN005", self.codes("ERROR"))
        ex = ("# A\n\n**Summary:** Only an example block here.\n\n## Engine\n```engine-example\n"
              "kind: FACT\nid: fact_y\ntext: \"REPLACE\"\ntruth: TRUE\n```\n")
        self.write("world/a.md", note(body=ex, engine="false"))
        self.assertNotIn("EN005", self.codes())

    def test_dangling_id_reference(self):
        self.write("world/a.md", note(body=self.fact("subjects: [loc_missing]\n"), engine="true"))
        self.link_all("a")
        self.assertIn("EN006", self.codes("ERROR"))

    def test_status_engine_ready_needs_engine_true(self):
        self.write("world/a.md", note(status="engine-ready", engine="false"))
        self.link_all("a")
        self.assertIn("FM009", self.codes("ERROR"))


class TestBody(VaultCase):
    def test_american_spelling_warns(self):
        self.write("world/a.md", note(body="# A\n\n**Summary:** The color of the armor is gray here.\n\n## D\n- x\n"))
        self.link_all("a")
        self.assertIn("SP001", self.codes("WARN"))

    def test_empty_section_warns_but_parent_with_subheading_does_not(self):
        self.write("world/a.md", note(body="# A\n\n**Summary:** Has an empty section below it.\n\n## Empty\n\n## Full\n- x\n"))
        self.write("world/b.md", note("topic_b", title="B", body="# B\n\n**Summary:** Parent has only subheadings.\n\n## Parent\n### Child\n- x\n"))
        self.link_all("a", "b")
        issues = lint.Linter(lint.load_notes()).run()
        flagged = {(i.path) for i in issues if i.code == "BD004"}
        self.assertEqual(flagged, {"world/a.md"})

    def test_truncated_summary_warns(self):
        self.write("world/a.md", note(body="# A\n\n**Summary:** The\n\n## D\n- x\n"))
        self.link_all("a")
        self.assertIn("BD003", self.codes("WARN"))

    def test_orphan_warns(self):
        self.write("world/a.md", note())
        self.write("README.md", "nothing here\n")
        self.assertIn("OR001", self.codes("WARN"))


class TestCli(VaultCase):
    def test_exit_codes(self):
        self.write("world/a.md", note(body="# A\n\n**Summary:** The color of it is plain.\n\n## D\n- x\n"))
        self.link_all("a")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(lint.main([]), 0)                # warnings only
            self.assertEqual(lint.main(["--strict"]), 1)      # warnings fail in strict mode
            self.write("world/b.md", "no frontmatter\n")
            self.assertEqual(lint.main(["--errors-only"]), 1)


class TestRealVault(unittest.TestCase):
    def test_the_real_vault_has_no_errors(self):
        lint.ROOT = testkit.REAL_CONFIG.parent
        issues = lint.Linter(lint.load_notes()).run()
        errors = [f"{i.path}:{i.line} {i.code} {i.msg}" for i in issues if i.level == "ERROR"]
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main(verbosity=1)

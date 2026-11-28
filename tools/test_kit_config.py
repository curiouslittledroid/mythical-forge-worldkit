#!/usr/bin/env python3
"""Tests for tools/yaml_subset.py and tools/kit_config.py. Run: python3 tools/test_kit_config.py"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit_config  # noqa: E402
import testkit  # noqa: E402
import yaml_subset  # noqa: E402

REAL_ROOT = Path(kit_config.__file__).resolve().parent.parent


def parse(text):
    return yaml_subset.load_text(text, "test.yaml")


class YamlSubsetCase(unittest.TestCase):
    def test_scalars_and_nesting(self):
        got = parse("a: 1\nb: two\nc: true\nd: null\ne: [x, y, 2]\nmap:\n  inner: 3\n")
        self.assertEqual(got, {"a": 1, "b": "two", "c": True, "d": None, "e": ["x", "y", 2],
                              "map": {"inner": 3}})

    def test_quoted_values_may_contain_colons(self):
        got = parse('a: "one: two"\nb: \'three: four\'\n')
        self.assertEqual(got, {"a": "one: two", "b": "three: four"})

    def test_unquoted_colon_is_refused(self):
        with self.assertRaises(yaml_subset.SchemaError):
            parse("a: one: two\n")

    def test_trailing_comment(self):
        self.assertEqual(parse("a: 1  # why\n"), {"a": 1})

    def test_hash_inside_a_value_is_not_a_comment(self):
        self.assertEqual(parse("a: https://x/y#frag\n"), {"a": "https://x/y#frag"})

    def test_hash_inside_quotes_is_not_a_comment(self):
        self.assertEqual(parse('a: "x # y"\n'), {"a": "x # y"})

    def test_comment_after_a_block_key_still_opens_the_block(self):
        # The bug this guards: reading the comment as the value, so the block became None.
        got = parse("site:   # the site section\n  url: https://example.test\n")
        self.assertEqual(got, {"site": {"url": "https://example.test"}})

    def test_whole_line_comments_and_blanks_are_skipped(self):
        self.assertEqual(parse("# lead\n\na: 1\n\n# tail\n"), {"a": 1})

    def test_sequence_of_mappings(self):
        got = parse("items:\n  - id: a\n    name: A\n  - id: b\n    name: B\n")
        self.assertEqual(got, {"items": [{"id": "a", "name": "A"}, {"id": "b", "name": "B"}]})

    def test_sequence_of_scalars(self):
        self.assertEqual(parse("order:\n  - one\n  - two\n"), {"order": ["one", "two"]})

    def test_sequence_item_scalar_with_a_colon_is_not_a_mapping(self):
        self.assertEqual(parse("urls:\n  - https://x/y\n"), {"urls": ["https://x/y"]})

    def test_top_level_sequence(self):
        got = parse("- id: a\n  description: first\n- id: b\n  description: second\n")
        self.assertEqual([i["id"] for i in got], ["a", "b"])

    def test_duplicate_top_level_key_is_refused(self):
        with self.assertRaises(yaml_subset.SchemaError):
            parse("a: 1\nb: 2\na: 3\n")

    def test_tab_is_refused(self):
        with self.assertRaises(yaml_subset.SchemaError):
            parse("a:\n\tb: 1\n")

    def test_key_outside_a_top_level_sequence_is_refused(self):
        with self.assertRaises(yaml_subset.SchemaError):
            parse("- id: a\nname: oops\n")


CONFIG = """\
version: 1
world:
  id: world_test
  title: Test
  slug: test
vault:
  notes:
    flags: topic_flags
  process_docs: [README.md]
features: [atlas]
"""


class ConfigCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        (self.root / "world").mkdir()
        self.write("world/flags.md",
                   "---\nid: topic_flags\nkind: TOPIC\ntitle: F\nname_status: working\n"
                   "status: working\nengine: false\n---\n\n```flags\n- id: a\n  description: x\n```\n")
        self.write("world.config.yaml", CONFIG)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def load(self, text=None):
        if text is not None:
            self.write("world.config.yaml", text)
        return kit_config.load(self.root / "world.config.yaml")

    # --- the happy path ---------------------------------------------------------------

    def test_reads_identity_and_derives_the_overland_id(self):
        cfg = self.load()
        self.assertEqual(cfg.world_id, "world_test")
        self.assertEqual(cfg.title, "Test")
        self.assertEqual(cfg.overland_id, "overland_test")  # derived from the id (schema note 3)
        self.assertEqual(cfg.root, self.root.resolve())

    def test_game_ready_repo_defaults_beside_the_vault(self):
        self.assertEqual(self.load().game_ready_repo, self.root.resolve().parent / "test-gameready")

    def test_resolves_a_note_id_to_a_path(self):
        self.assertEqual(self.load().path_of("flags"), self.root / "world" / "flags.md")

    def test_reads_a_block_by_the_notes_name(self):
        self.assertEqual(self.load().block("flags"), [{"id": "a", "description": "x"}])

    def test_an_absent_block_is_none_not_an_error(self):
        cfg = self.load()
        self.assertIsNone(cfg.block("eras"))       # no vault.notes.eras at all
        self.assertIsNone(cfg.path_of("eras"))

    def test_a_missing_block_in_the_named_note_is_none(self):
        # The note resolves, but it carries no `flags` block: inert, not a crash.
        self.write("world/other.md", "---\nid: topic_other\nkind: TOPIC\ntitle: O\n"
                                    "name_status: working\nstatus: working\nengine: false\n---\n\nbody\n")
        cfg = self.load(CONFIG.replace("flags: topic_flags", "flags: topic_other"))
        self.assertEqual(cfg.path_of("flags"), self.root / "world" / "other.md")
        self.assertIsNone(cfg.block("flags"))

    def test_required_block_says_which_note_it_looked_in(self):
        cfg = self.load(CONFIG.replace("    flags: topic_flags", "    flags: topic_absent"))
        with self.assertRaises(kit_config.ConfigError) as ctx:
            cfg.required_block("flags")
        self.assertIn("topic_absent", str(ctx.exception))

    def test_a_malformed_block_names_the_note_and_the_block(self):
        self.write("world/flags.md",
                   "---\nid: topic_flags\nkind: TOPIC\ntitle: F\nname_status: working\n"
                   "status: working\nengine: false\n---\n\n```flags\n- id: a\n  x: one: two\n```\n")
        with self.assertRaises(kit_config.ConfigError) as ctx:
            self.load().block("flags")
        self.assertIn("flags block", str(ctx.exception))

    # --- features ---------------------------------------------------------------------

    def test_features_are_a_set_and_require_is_loud(self):
        cfg = self.load()
        self.assertTrue(cfg.has("atlas"))
        self.assertFalse(cfg.has("site"))
        cfg.require("atlas")                        # does not raise
        with self.assertRaises(kit_config.ConfigError) as ctx:
            cfg.require("site")
        self.assertIn("'site' feature", str(ctx.exception))

    # --- refusals ---------------------------------------------------------------------

    def test_unknown_top_level_key(self):
        with self.assertRaises(kit_config.ConfigError):
            self.load(CONFIG + "extra: 1\n")

    def test_unknown_key_inside_world(self):
        with self.assertRaises(kit_config.ConfigError):
            self.load(CONFIG.replace("  slug: test", "  slug: test\n  slagg: no"))

    def test_unknown_note_name(self):
        with self.assertRaises(kit_config.ConfigError):
            self.load(CONFIG.replace("    flags: topic_flags", "    flags: topic_flags\n    nope: topic_x"))

    def test_unknown_feature(self):
        with self.assertRaises(kit_config.ConfigError):
            self.load(CONFIG.replace("[atlas]", "[atlas, spelunking]"))

    def test_wrong_version(self):
        with self.assertRaises(kit_config.ConfigError):
            self.load(CONFIG.replace("version: 1", "version: 2"))

    def test_missing_required_world_key(self):
        with self.assertRaises(kit_config.ConfigError):
            self.load(CONFIG.replace("  slug: test\n", ""))

    def test_a_site_section_needs_its_fields(self):
        with self.assertRaises(kit_config.ConfigError) as ctx:
            self.load(CONFIG.replace("[atlas]", "[atlas, site]")
                      + "site:\n  url: https://x.test\n  sections:\n    - slug: a\n      label: A\n")
        self.assertIn("kinds is required", str(ctx.exception))

    def test_a_site_section_needs_the_site_feature(self):
        with self.assertRaises(kit_config.ConfigError):
            self.load(CONFIG + "site:\n  url: https://x.test\n")

    def test_missing_config_file(self):
        with self.assertRaises(kit_config.ConfigError):
            kit_config.load(self.root / "nope.yaml")


class SubsetEdgeCase(unittest.TestCase):
    """Two corners of the subset that the readers must agree about, because a world writes them.

    `[]` alone in a block: a world that has declared no flags yet says exactly that, and the
    template ships it, so both readers must read an empty list rather than refusing a block that is
    perfectly clear. This is a *block root* case only -- `key: []` was always a value.
    """

    def test_an_empty_flow_sequence_as_a_whole_block_is_an_empty_list(self):
        self.assertEqual(parse("[]"), [])
        self.assertEqual(parse("# nothing declared yet\n[]\n"), [])

    def test_node_reads_it_the_same_way(self):
        if shutil.which("node") is None:
            self.skipTest("node is not installed")
        script = ("import {parseSubset} from '" + (REAL_ROOT / "tools" / "kit_config.mjs").as_posix()
                  + "';\nprocess.stdout.write(JSON.stringify([parseSubset('[]'), "
                    "parseSubset('# none\\n[]\\n'), parseSubset('a: []\\n')]));")
        out = subprocess.run(["node", "--input-type=module", "-e", script],
                             capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(json.loads(out.stdout), [[], [], {"a": []}])


class LiveConfigShapeCase(unittest.TestCase):
    """The live config's *shape*, through the reader, not its contents.

    What used to be here -- and is now `tools/check_config.py`, whose tests are
    `test_check_config.py` -- was the only assertion that a config is coherent with its vault, and
    it lived in a suite a world author is told never to touch. The parity proof moved with it: the
    two readers are compared on the live config by `check_config.parity`, which every world runs.
    This class keeps the reader-level half: the values a tool is entitled to assume.
    """

    @classmethod
    def setUpClass(cls):
        cls.cfg = kit_config.load(testkit.REAL_CONFIG)

    def test_identity(self):
        self.assertRegex(self.cfg.world_id, r"^world_[a-z0-9_]+$")
        self.assertTrue(self.cfg.title.strip())
        self.assertTrue(self.cfg.site)
        self.assertRegex(self.cfg.slug, r"^[a-z0-9-]+$")
        self.assertTrue(self.cfg.game_ready_repo.name, "game_ready_repo must name a directory")

    def test_note_ids_is_the_declaration_and_a_copy(self):
        ids = self.cfg.note_ids
        self.assertEqual(ids.get("flags"), self.cfg._note_ids.get("flags"))
        ids["flags"] = "topic_mine"
        self.assertNotEqual(self.cfg.note_ids.get("flags"), "topic_mine",
                            "note_ids hands out a copy: a check must not be able to rewrite the config")

    def test_overland_is_derived_when_the_world_does_not_name_one(self):
        self.assertEqual(self.cfg.overland_id, "overland_" + self.cfg.world_id.removeprefix("world_"))


if __name__ == "__main__":
    unittest.main(verbosity=2)

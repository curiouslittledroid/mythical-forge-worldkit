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


class RealWorldCase(unittest.TestCase):
    """The live config: this is the regression test that T1 actually landed."""

    @classmethod
    def setUpClass(cls):
        cls.cfg = kit_config.load(testkit.REAL_CONFIG)

    def test_identity(self):
        """The live config must be *shaped* right, not equal to any one world's values.

        This test used to assert the first world's own id. The kit ships a demo world, so an assertion on
        a world's own name is exactly the literal the extraction removes: what matters is the form
        the engine and the tools require.
        """
        self.assertRegex(self.cfg.world_id, r"^world_[a-z0-9_]+$")
        self.assertTrue(self.cfg.title.strip())
        self.assertTrue(self.cfg.site)
        self.assertRegex(self.cfg.slug, r"^[a-z0-9-]+$")
        self.assertTrue(self.cfg.game_ready_repo.name, "game_ready_repo must name a directory")

    def test_every_named_note_resolves_to_a_real_note(self):
        for name in kit_config.BLOCK_INFO:
            with self.subTest(note=name):
                self.assertIsNotNone(self.cfg.path_of(name), f"vault.notes.{name} does not resolve")
                self.assertIsNotNone(self.cfg.block(name), f"{name} carries no block")

    def test_the_testimony_book_resolves(self):
        self.assertIsNotNone(self.cfg.path_of("testimony_book"))

    def test_eras(self):
        order = self.cfg.block("eras")["order"]
        self.assertTrue(order, "an eras block must list at least one era")
        self.assertEqual(len(order), len(set(order)), "an era may not be listed twice")

    def test_chronology(self):
        c = self.cfg.block("calendar")
        self.assertRegex(c["date_prefix"], r"^[A-Z]{2,6}$", "the date prefix is a short capital")
        self.assertIsInstance(c["present"], int, "the present year is a number the tools do arithmetic on")

    def test_site_vocabulary(self):
        """Shape, not contents: the vocabularies are the world's."""
        v = self.cfg.block("site_vocabulary")
        for key in ("published_tags", "keystones", "plot_web_surfaces"):
            self.assertIn(key, v, f"the site-vocabulary block must declare {key}")
            self.assertIsInstance(v[key], list)
        for tag in v["published_tags"]:
            self.assertRegex(tag, r"^[a-z0-9-]+$", "a published tag is a slug: it becomes a URL")
        self.assertEqual(len(v["published_tags"]), len(set(v["published_tags"])))

    def test_the_site_section_list_is_consistent(self):
        site = self.cfg.site
        self.assertIsNotNone(site)
        slugs = [s.slug for s in site.sections]
        self.assertEqual(len(slugs), len(set(slugs)), "duplicate section slug")
        kinds = [k for s in site.sections for k in s.kinds]
        self.assertEqual(len(kinds), len(set(kinds)), "a kind is claimed by two sections")
        self.assertEqual(site.section_of_kind("NPC"), "people")
        self.assertEqual(site.section_of_kind("NOT_A_KIND"), None)
        self.assertEqual(site.label_of("gods"), "Gods")

    def test_process_docs_are_the_ones_at_the_root(self):
        for rel in self.cfg.process_docs:
            with self.subTest(doc=rel):
                self.assertTrue((testkit.REAL_CONFIG.parent / rel).is_file(), f"{rel} is listed but missing")


class NodeParityCase(unittest.TestCase):
    """Python and Node each read `world.config.yaml`. They must agree.

    There is a second reader because the Node tools cannot call Python, and the subset parser is
    small enough to keep in both. A divergence would silently corrupt a build, so it fails here.
    """

    @classmethod
    def setUpClass(cls):
        if shutil.which("node") is None:
            raise unittest.SkipTest("node is not installed")
        cls.cfg = kit_config.load(testkit.REAL_CONFIG)
        out = subprocess.run(["node", str(REAL_ROOT / "tools" / "kit_config.mjs")],
                             capture_output=True, text=True, cwd=REAL_ROOT,
                             env={**os.environ, "WORLD_CONFIG": str(testkit.REAL_CONFIG)})
        if out.returncode != 0:
            raise AssertionError(f"kit_config.mjs failed:\n{out.stderr}")
        cls.node = json.loads(out.stdout)

    def test_identity_and_paths(self):
        self.assertEqual(self.node["world_id"], self.cfg.world_id)
        self.assertEqual(self.node["title"], self.cfg.title)
        self.assertEqual(self.node["slug"], self.cfg.slug)
        self.assertEqual(self.node["overland"], self.cfg.overland_id)
        self.assertEqual(Path(self.node["game_ready_repo"]), self.cfg.game_ready_repo)
        self.assertEqual(sorted(self.node["features"]), sorted(self.cfg.features))
        self.assertEqual(self.node["notes"], self.cfg._note_ids)
        self.assertEqual(sorted(self.node["process_docs"]), sorted(self.cfg.process_docs))

    def test_the_site_sections_agree(self):
        python = [(s.slug, s.label, list(s.kinds)) for s in self.cfg.site.sections]
        node = [(s["slug"], s["label"], s["kinds"]) for s in self.node["site"]["sections"]]
        self.assertEqual(node, python)
        self.assertEqual(self.node["site"]["url"], self.cfg.site.url)

    def test_every_block_agrees(self):
        for name in kit_config.BLOCK_INFO:
            with self.subTest(block=name):
                self.assertEqual(self.node["blocks"][name], self.cfg.block(name))


if __name__ == "__main__":
    unittest.main(verbosity=2)

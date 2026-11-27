#!/usr/bin/env python3
"""Tests for the atlas tools: `atlas_yaml.py` (the schema) and `atlas_tables.py` (the view).

The bug this exists for: the schema shipped with one world's frames, sections and type vocabulary
baked in, and the renderer wrote that world's geography into the note it generated. A world with
different frames could not use either.

Run: python3 tools/test_atlas.py
"""
from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import atlas_tables  # noqa: E402
import atlas_yaml  # noqa: E402
from yaml_subset import SchemaError  # noqa: E402


def atlas(**overrides):
    """A small, valid atlas with no world in it: two frames, a region and two towns."""
    data = {
        "schema": 1,
        "default_frame": "home",
        "title": "The Map Register",
        "frames": {
            "home": {"x": [0, 500], "y": [0, 300]},
            "isles": {"x": [0, 200], "y": [0, 200], "prefix": "I", "grid_km": 100},
            "world": {"x": [0, 1000], "y": [0, 800]},
        },
        "regions": [
            {"id": "zone_woods", "name": "The Woods", "frame": "home",
             "bounds": [10, 20, 110, 120], "source": "world/places/woods.md"},
        ],
        "towns": [
            {"id": "loc_north", "name": "North Town", "x": 260, "y": 130,
             "source": "world/places/north.md", "origin": "old-town", "population": 1200},
            {"id": "loc_south", "name": "South Town", "x": 20, "y": 20,
             "source": "world/places/south.md"},
        ],
        "route_legs": [{"from": "loc_south", "to": "loc_north", "km": 250, "terrain": "standard"}],
        "plates": [
            {"id": "plate_home", "title": "The Home Plate", "paper": [420, 297],
             "scale": 2_000_000, "grid": 250, "file": "home.svg", "frame": "home"},
        ],
    }
    data.update(overrides)
    return data


class TestSchema(unittest.TestCase):
    def test_a_clean_atlas_validates(self):
        self.assertTrue(atlas_yaml.validate(atlas()))

    def test_frames_are_required(self):
        data = atlas()
        del data["frames"]
        with self.assertRaisesRegex(SchemaError, "frames"):
            atlas_yaml.validate(data)

    def test_a_frame_needs_both_extents(self):
        data = atlas()
        data["frames"]["home"] = {"x": [0, 500]}
        with self.assertRaisesRegex(SchemaError, "home.y"):
            atlas_yaml.validate(data)

    def test_an_entry_in_an_undeclared_frame_fails(self):
        data = atlas()
        data["towns"][0]["frame"] = "somewhere_else"
        with self.assertRaisesRegex(SchemaError, "somewhere_else"):
            atlas_yaml.validate(data)

    def test_a_default_frame_must_be_declared(self):
        data = atlas(default_frame="nowhere")
        with self.assertRaisesRegex(SchemaError, "nowhere"):
            atlas_yaml.validate(data)

    def test_the_default_frame_falls_back_to_world_then_the_first(self):
        data = atlas()
        del data["default_frame"]
        self.assertEqual(atlas_yaml.default_frame(data), "world")
        data["frames"].pop("world")
        self.assertEqual(atlas_yaml.default_frame(data), "home")

    def test_ids_are_unique_across_sections(self):
        data = atlas()
        data["towns"][1]["id"] = "zone_woods"
        with self.assertRaisesRegex(SchemaError, "duplicate id"):
            atlas_yaml.validate(data)

    def test_bounds_must_be_four_numbers(self):
        data = atlas()
        data["regions"][0]["bounds"] = [1, 2, 3]
        with self.assertRaisesRegex(SchemaError, "bounds"):
            atlas_yaml.validate(data)

    def test_points_must_parse(self):
        data = atlas()
        data["towns"][0].pop("x")
        data["towns"][0].pop("y")
        data["towns"][0]["points"] = "1,2 3,nope"
        with self.assertRaisesRegex(SchemaError, "points"):
            atlas_yaml.validate(data)

    def test_x_and_y_go_together(self):
        data = atlas()
        del data["towns"][0]["y"]
        with self.assertRaisesRegex(SchemaError, "both x and y"):
            atlas_yaml.validate(data)

    def test_a_status_outside_the_scale_fails(self):
        data = atlas()
        data["towns"][0]["status"] = "maybe"
        with self.assertRaisesRegex(SchemaError, "maybe"):
            atlas_yaml.validate(data)

    def test_a_section_entry_needs_a_name_or_a_title_or_a_pair(self):
        data = atlas()
        del data["towns"][0]["name"]
        with self.assertRaisesRegex(SchemaError, "needs 'name'"):
            atlas_yaml.validate(data)

    def test_a_world_may_add_its_own_section(self):
        data = atlas()
        data["cairns"] = [{"id": "loc_cairn", "name": "A Cairn", "x": 1, "y": 1,
                           "type": "whatever-the-world-calls-it"}]
        self.assertTrue(atlas_yaml.validate(data))


class TestView(unittest.TestCase):
    def setUp(self):
        self.text = atlas_tables.render(atlas())

    def test_every_section_becomes_a_table(self):
        for heading in ("## Frames", "## Regions", "## Towns", "## Route legs", "## Plates"):
            self.assertIn(heading, self.text)

    def test_the_title_and_summary_are_the_data_s(self):
        self.assertIn('title: "The Map Register"', self.text)
        self.assertIn("# The Map Register", self.text)

    def test_labels_rename_a_heading(self):
        text = atlas_tables.render(atlas(labels={"towns": "Settlements"}))
        self.assertIn("## Settlements", text)

    def test_the_default_frame_gets_a_master_reference(self):
        self.assertIn("| **North Town** | x 260, y 130 | B01 |", self.text)

    def test_a_prefixed_frame_gets_a_local_reference(self):
        data = atlas()
        data["towns"][0]["frame"] = "isles"
        data["towns"][0]["x"], data["towns"][0]["y"] = 150, 50
        text = atlas_tables.render(data)
        self.assertIn("| I B01 |", text)

    def test_the_world_frame_has_no_reference(self):
        data = atlas()
        data["towns"][0]["frame"] = "world"
        self.assertIn("| world |", atlas_tables.render(data))

    def test_a_route_leg_gets_a_bearing_and_days(self):
        self.assertIn("South Town → North Town", self.text)
        self.assertIn("| 250 |", self.text)

    def test_gm_sections_are_wrapped_in_an_earned_disclosure(self):
        text = atlas_tables.render(atlas(gm_sections=["towns"]))
        self.assertIn("**Disclosure:** earned", text)

    def test_notes_and_links_are_the_data_s(self):
        text = atlas_tables.render(atlas(notes=["Read me first."], links=["[[atlas-register|The brief]]"]))
        self.assertIn("- Read me first.", text)
        self.assertIn("[[atlas-register|The brief]]", text)

    def test_the_default_disclosure_is_earned(self):
        self.assertIn("disclosure: earned", self.text)

    def test_no_source_world_phrase_appears(self):
        # The renderer must not invent a world: the same phrase list the document check uses finds
        # nothing in a synthetic atlas.
        import check_doc_examples
        for phrase in check_doc_examples.SOURCE_WORLD_PHRASES:
            self.assertNotIn(phrase, self.text)


class TestCheck(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.data = self.root / "atlas-features.yaml"
        self.out = self.root / "atlas-features.md"
        self._data, self._out = atlas_tables.DATA, atlas_tables.OUT
        atlas_tables.DATA, atlas_tables.OUT = str(self.data), str(self.out)

    def tearDown(self):
        atlas_tables.DATA, atlas_tables.OUT = self._data, self._out
        self.tmp.cleanup()

    def write(self):
        self.data.write_text(self.yaml(), encoding="utf-8")

    def yaml(self):
        return """\
schema: 1
default_frame: home
frames:
  home:
    x: [0, 500]
    y: [0, 300]
  isles:
    x: [0, 200]
    y: [0, 200]
    prefix: I
    grid_km: 100
  world:
    x: [0, 1000]
    y: [0, 800]
towns:
  - id: loc_north
    name: North Town
    x: 260
    y: 130
    source: world/places/north.md
"""

    def test_check_passes_on_a_fresh_file(self):
        self.write()
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(atlas_tables.main(), 0)
            self.assertEqual(atlas_tables.main(["--check"]), 0)

    def test_check_fails_when_the_file_is_stale(self):
        self.write()
        with contextlib.redirect_stdout(io.StringIO()):
            atlas_tables.main()
        self.out.write_text("stale\n", encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(atlas_tables.main(["--check"]), 1)


if __name__ == "__main__":
    unittest.main()

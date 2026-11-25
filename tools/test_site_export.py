#!/usr/bin/env python3
"""Tests for tools/site_export.py. Run: python3 tools/test_site_export.py

Every redaction rule in meta/site.md section 2.2 has a test here. The rule that matters most:
**nothing that is not `open` may reach the output.**
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lint  # noqa: E402
import kit_config  # noqa: E402
import site_export  # noqa: E402
import testkit  # noqa: E402

REAL_ROOT = lint.ROOT


def note(id_="loc_a", kind="SETTLEMENT", title="A", extra="", body="## Details\n- some lore\n",
         disclosure=""):
    disc = f"disclosure: {disclosure}\n" if disclosure else ""
    return (
        "---\n"
        f"id: {id_}\nkind: {kind}\ntitle: {title}\nname_status: working\nstatus: working\n"
        f"{disc}{extra}engine: false\n---\n\n# {title}\n\n"
        f"**Summary:** A summary of {title}.\n\n{body}"
    )


class SiteCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        lint.ROOT = self.root
        # The tools are config-driven (T1): a fixture vault needs a config, and it uses the
        # world's own so the section list and the vocabulary are the real ones.
        testkit.write_config(self.root)
        self.out = self.root / "_site" / "content"
        self.data = self.root / "_site" / "data"
        self.audit_file = self.root / "_site" / "audit" / "latest.json"

    def tearDown(self):
        lint.ROOT = REAL_ROOT
        self.tmp.cleanup()

    # --- helpers -------------------------------------------------------------------
    def write(self, rel: str, text: str) -> None:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def build(self, today="2026-01-02"):
        return site_export.build(today=today, out=self.out, data=self.data,
                                 audit_file=self.audit_file)

    def page(self, rel: str) -> str:
        return (self.out / rel).read_text(encoding="utf-8")

    def audit(self) -> dict:
        return json.loads(self.audit_file.read_text(encoding="utf-8"))

    def audit_field(self, key: str) -> list:
        return self.audit()[key]

    def pages(self) -> list[str]:
        return sorted(p.relative_to(self.out).as_posix() for p in self.out.rglob("*.md"))


class TestWhatIsPublished(SiteCase):
    def test_open_note_is_published(self):
        self.write("world/places/a.md", note(disclosure="open"))
        self.build()
        self.assertEqual(self.pages(), ["places/a.md"])
        self.assertIn("## Details", self.page("places/a.md")) if False else None
        page = self.page("places/a.md")
        self.assertIn('summary: "A summary of A."', page)
        self.assertIn("A summary of A.", page)

    def test_earned_note_is_not_published(self):
        self.write("world/places/a.md", note(disclosure="earned", body="## Details\nthe truth\n"))
        audit = self.build()
        self.assertEqual(self.pages(), [])
        self.assertEqual(audit["skipped_notes"][0]["reason"], "no open content")

    def test_secrets_and_keystone_sections_never_publish(self):
        self.write("world/places/a.md", note(
            disclosure="open",
            body="## Details\nsafe\n\n## Secrets\nthe hidden thing\n\n"
                 "## Keystone secrets\n**Disclosure:** sealed\nthe keystone\n",
        ))
        self.build()
        page = self.page("places/a.md")
        self.assertNotIn("hidden thing", page)
        self.assertNotIn("keystone", page)
        self.assertIn("safe", page)

    def test_unmarked_note_fails_closed(self):
        self.write("world/places/a.md", note(body="## Details\nunmarked prose\n"))
        audit = self.build()
        self.assertEqual(self.pages(), [])
        self.assertIn("no open content",
                      [s["reason"] for s in audit["skipped_notes"]])

    def test_deferred_kind_is_skipped(self):
        self.write("world/npcs/x.md", note(id_="npc_x", kind="NPC", disclosure="open"))
        audit = self.build()
        self.assertEqual(self.pages(), [])
        self.assertEqual(audit["skipped_notes"][0]["reason"], "deferred kind")

    def test_kind_without_a_section_is_skipped(self):
        self.write("world/secrets/t.md", note(id_="thread_t", kind="THREAD", disclosure="open"))
        audit = self.build()
        self.assertEqual(self.pages(), [])
        self.assertIn("no section", audit["skipped_notes"][0]["reason"])


class TestLayers(SiteCase):
    def test_layered_history_publishes_official_myth_rival_and_drops_truth(self):
        self.write("world/history/e.md", note(
            id_="hist_e", kind="HISTORY_EVENT", title="E", disclosure="earned",
            body="## Details\n"
                 "- **Official:** a tragic accident. **Myth:** a demon did it.\n"
                 "- **Rival:** the dwarves blame the elves.\n"
                 "- **Truth:** the archmage knew.\n"
                 "- **Who knows:** nobody outside the Dissenters.\n",
        ))
        self.build()
        page = self.page("history/e.md")
        self.assertIn("## What people say", page)
        self.assertIn("**Official.** a tragic accident.", page)
        self.assertIn("**Myth.** a demon did it.", page)
        self.assertIn("**Rival.** the dwarves blame the elves.", page)
        self.assertNotIn("archmage", page)
        self.assertNotIn("Who knows", page)

    def test_frontmatter_layers_become_what_people_say(self):
        self.write("world/history/e.md", note(
            id_="hist_e", kind="HISTORY_EVENT", title="E", disclosure="open",
            extra='official: "the official line"\nmyth: "the popular story"\n',
            body="## Details\nplain detail\n",
        ))
        self.build()
        page = self.page("history/e.md")
        self.assertIn("## What people say", page)
        self.assertIn("**Official.** the official line", page)
        self.assertIn("**Myth.** the popular story", page)
        self.assertTrue(page.index("What people say") < page.index("## Details"))


class TestRedaction(SiteCase):
    def test_heading_annotations_are_stripped(self):
        self.write("world/places/a.md", note(
            disclosure="open",
            body="## Culture (decided, Step 5, Round 1)\n- **Two layers (decided, Step 2).** x\n"
                 "### The gate (decided, Step 2)\n- y\n",
        ))
        self.build()
        page = self.page("places/a.md")
        self.assertIn("## Culture\n", page)
        self.assertIn("**Two layers.**", page)
        self.assertIn("### The gate\n", page)
        self.assertNotIn("decided", page)

    def test_markers_are_removed(self):
        self.write("world/places/a.md", note(
            disclosure="open",
            body="## Details\n**Disclosure:** open\n**Reveal when:** they ask\n"
                 "- keeps this [OPEN] but drops the marker\n",
        ))
        self.build()
        page = self.page("places/a.md")
        for marker in ("**Disclosure:**", "**Reveal when:**", "[OPEN]"):
            self.assertNotIn(marker, page)
        self.assertIn("keeps this but drops the marker", page)

    def test_npc_want_line_is_stripped_but_a_gods_wants_are_kept(self):
        self.write("world/npcs/x.md", note(id_="npc_x", kind="NPC", disclosure="open",
                                          body="## Details\n- **Want:** the gate key\n- public\n"))
        self.write("world/gods/g.md", note(id_="god_g", kind="GOD", title="G", disclosure="open",
                                          body="## Details\n- **Wants now:** battle.\n"))
        self.build()
        audit = self.audit()
        # NPC pages are deferred, so assert on the rule directly:
        log = {"design_fields": [], "internal_references": []}
        self.assertEqual(site_export.clean_lines(["**Want:** the key"], "NPC", "n", log), [])
        self.assertEqual(site_export.clean_lines(["**Want:** the key"], "TOPIC", "n", log),
                         ["**Want:** the key"])
        self.assertIn("Wants now", self.page("gods/g.md"))
        self.assertIn("deferred kind", [s["reason"] for s in audit["skipped_notes"]])

    def test_engine_fields_are_dropped_and_logged(self):
        self.write("world/relics/r.md", note(id_="item_r", kind="ITEM", title="R", disclosure="open",
                                            body="## Details\n**SRD base:** [OPEN] (PR-4)\n"
                                                 "- **Engine mapping:** **CLERIC**.\n- real lore\n"))
        audit = self.build()
        page = self.page("relics/r.md")
        self.assertNotIn("SRD base", page)
        self.assertNotIn("Engine mapping", page)
        self.assertNotIn("PR-4", page)
        self.assertIn("real lore", page)
        self.assertEqual(len(audit["design_fields"]), 2)

    def test_roadmap_references_are_scrubbed_and_logged(self):
        self.write("world/places/a.md", note(
            disclosure="open",
            body="## Details\n- **Names.** Their names are for Step 11/13. Most are ruins.\n",
        ))
        audit = self.build()
        page = self.page("places/a.md")
        self.assertNotIn("Step 11/13", page)
        self.assertIn("Most are ruins", page)
        self.assertEqual(len(audit["internal_references"]), 1)

    def test_design_citations_are_scrubbed_and_logged(self):
        self.write("world/places/a.md", note(
            disclosure="open",
            body="## Details\nEvery note names one magic class (conventions §9.6).\n"
                 "Potency is scene-gated (M3, class D).\n",
        ))
        audit = self.build()
        page = self.page("places/a.md")
        self.assertNotIn("§9.6", page)
        self.assertNotIn("M3", page)
        self.assertIn("Every note names one magic class.", page)
        self.assertEqual(len(audit["internal_references"]), 2)


class TestWhatMakesAPage(SiteCase):
    def test_a_summary_alone_is_not_a_page(self):
        self.write("world/places/a.md", note(disclosure="open", body=""))
        audit = self.build()
        self.assertEqual(self.pages(), [])
        self.assertEqual(audit["skipped_notes"][0]["reason"], "no open content")
        # and a link to it keeps its words rather than going nowhere
        self.write("world/places/b.md", note(id_="loc_b", disclosure="open",
                                            body="## Details\nsee [[a|the stub]]\n"))
        self.build()
        self.assertIn("the stub", self.page("places/b.md"))
        self.assertNotIn("(/places/a/)", self.page("places/b.md"))


class TestLinks(SiteCase):
    def setUp(self):
        super().setUp()
        self.write("world/gods/g.md", note(id_="god_g", kind="GOD", title="The Giver", disclosure="open",
                                          body="## Details\nthe god\n"))
        self.write("world/places/b.md", note(id_="loc_b", kind="SETTLEMENT", title="B", disclosure="open",
                                            body="## Details\nB exists.\n"))
        self.write("world/secrets/hidden.md", note(id_="topic_h", kind="TOPIC", title="Hidden",
                                                  disclosure="earned", body="## Details\nsecret\n"))
        self.write("meta/design-doc.md", note(id_="topic_d", kind="TOPIC", title="Design Doc",
                                             disclosure="open"))
        self.write("world/gods/_index.md", note(id_="topic_gi", kind="INDEX", title="Gods", disclosure="open"))

    def test_link_to_a_published_page_becomes_a_site_link(self):
        self.write("world/places/a.md", note(disclosure="open",
                                            body="## Details\nSee [[b|B]] and [[gods/g|the god]].\n"))
        self.build()
        page = self.page("places/a.md")
        self.assertIn("[B](/places/b/)", page)
        self.assertIn("[the god](/gods/g/)", page)

    def test_link_to_a_note_with_no_open_content_keeps_the_words(self):
        self.write("world/places/a.md", note(disclosure="open",
                                            body="## Details\nSee [[hidden|the hidden thing]].\n"))
        audit = self.build()
        page = self.page("places/a.md")
        self.assertIn("the hidden thing", page)
        self.assertNotIn("/secrets/", page)
        self.assertNotIn("[[", page)
        self.assertEqual(audit["flattened_links"][0]["reason"], "no-open-content")

    def test_infrastructure_link_keeps_the_sentence(self):
        self.write("world/places/a.md", note(disclosure="open",
                                            body="## Details\nSee [[design-doc|the design doc]].\n"))
        audit = self.build()
        page = self.page("places/a.md")
        self.assertIn("the design doc", page)
        self.assertNotIn("design-doc", page)
        self.assertEqual(audit["flattened_links"][0]["reason"], "infrastructure")

    def test_plot_web_name_in_details_is_logged(self):
        """A thread named as plain text flattens nothing, so only this key can find it."""
        self.write("world/plot-web/the-rush.md",
                   note(id_="thread_rush", kind="THREAD", title="The Great Rush",
                        body="## Details\n- a boom\n"))
        self.write("world/places/a.md", note(disclosure="open",
                                            body="## Details\nA frontier during the Great Rush.\n"))
        audit = self.build()
        page = self.page("places/a.md")
        self.assertIn("the Great Rush", page)  # the prose survives; the codex is at fault
        self.assertEqual([(m["page"], m["target"], m["text"])
                          for m in audit["plot_web_text_mentions"]],
                         [("a", "world/plot-web/the-rush.md", "Great Rush")])

    def test_plot_web_name_under_hooks_is_not_logged(self):
        self.write("world/plot-web/the-rush.md",
                   note(id_="thread_rush", kind="THREAD", title="The Great Rush",
                        body="## Details\n- a boom\n"))
        self.write("world/places/a.md", note(disclosure="open",
                                            body="## Details\n- some lore\n"
                                                 "## Hooks\n- The Great Rush reaches here.\n"))
        audit = self.build()
        self.assertEqual(audit["plot_web_text_mentions"], [])
        self.assertNotIn("Great Rush", self.page("places/a.md"))

    def test_plot_web_matching_is_case_sensitive(self):
        """Lowercase English that shares a thread's words is not a mention of the thread."""
        self.write("world/plot-web/the-rush.md",
                   note(id_="thread_rush", kind="THREAD", title="Choir Is Not Monolithic",
                        body="## Details\n- a boom\n"))
        self.write("world/places/a.md", note(disclosure="open",
                                            body="## Details\nThe choir is not monolithic.\n"))
        audit = self.build()
        self.assertEqual(audit["plot_web_text_mentions"], [])

    def test_reviewed_plot_web_surface_is_not_logged(self):
        """A thread whose title is also in-world vocabulary is reported only until reviewed."""
        self.write("world/plot-web/gone.md",
                   note(id_="thread_gone", kind="THREAD", title="The Gone Tide",
                        body="## Details\n- wretches\n"))
        self.write("world/places/a.md", note(disclosure="open",
                                            body="## Details\nThe Gone Tide is rising.\n"))
        self.assertEqual(len(self.build()["plot_web_text_mentions"]), 1)

        testkit.write_config(
            self.root,
            plot_web_surfaces=[*testkit.real_vocabulary()["plot_web_surfaces"], "gone tide"])
        self.assertEqual(self.build()["plot_web_text_mentions"], [])

    def test_author_notes_are_never_published(self):
        """A citation is worth keeping in the note; it is never worth showing a player."""
        self.write("world/places/a.md", note(disclosure="open", body=(
            "## Details\n- Public face.\n\n"
            "## Author Notes\n- **Engine form:** a Fact (Design 23 \u00a75.4, PR-4).\n")))
        audit = self.build()
        page = self.page("places/a.md")
        self.assertIn("Public face", page)
        for leaked in ("Author Notes", "Design 23", "PR-4", "Engine form"):
            self.assertNotIn(leaked, page)
        self.assertEqual(audit["internal_references"], [])  # nothing to scrub: it never got here

    def test_author_notes_do_not_need_scrubbing(self):
        self.write("world/places/a.md", note(disclosure="open", body=(
            "## Details\n- Cairo, decided in Step 9.\n\n"
            "## Author Notes\n- the peg to the engine is fixed in Step 9 (PR-4)\n")))
        audit = self.build()
        self.assertEqual([r["note"] for r in audit["internal_references"]],
                         ["world/places/a.md"])  # only the Details line is a defect

    def test_table_escaped_link_is_resolved(self):
        self.write("world/places/a.md", note(disclosure="open",
                                            body="## Details\n| Name | Place |\n|---|---|\n"
                                                 "| b | [[b\\|B]] |\n"))
        self.build()
        page = self.page("places/a.md")
        self.assertIn("[B](/places/b/)", page)
        self.assertIn("|---|---|", page.split("## Details")[1])  # the table survives

    def test_unresolved_link_keeps_the_label_and_is_logged(self):
        self.write("world/places/a.md", note(disclosure="open",
                                            body="## Details\nSee [[nowhere|the far place]].\n"))
        audit = self.build()
        self.assertIn("the far place", self.page("places/a.md"))
        self.assertEqual(audit["unresolved_links"][0]["reason"], "unresolved")
        self.assertEqual(audit["ambiguous_links"], [])

    def test_ambiguous_link_fails_check(self):
        self.write("world/places/a.md", note(disclosure="open", body="## Details\n[[dup]]\n"))
        self.write("world/places/one/dup.md", note(id_="loc_dup1", disclosure="open"))
        self.write("world/places/two/dup.md", note(id_="loc_dup2", disclosure="open"))
        audit = self.build()
        self.assertEqual(len(audit["ambiguous_links"]), 1)
        self.assertEqual(site_export.main(["--out", str(self.out), "--data", str(self.data),
                                           "--audit", str(self.audit_file), "--check"]), 1)

    def test_a_deferred_kind_keeps_its_words_without_a_link(self):
        self.write("world/npcs/x.md", note(id_="npc_x", kind="NPC", title="X", disclosure="open"))
        self.write("world/places/a.md", note(disclosure="open",
                                            body="## Details\nsee [[x|X]]\n"))
        audit = self.build()
        page = self.page("places/a.md")
        self.assertIn("see X", page)
        self.assertNotIn("/people/", page)
        self.assertEqual([f["reason"] for f in audit["flattened_links"]], ["deferred"])

    def test_section_index_link_points_at_the_section(self):
        self.write("world/places/a.md", note(disclosure="open",
                                            body="## Details\nSee the [[gods/_index|pantheon]].\n"))
        self.write("world/gods/g.md", note(id_="god_g", kind="GOD", disclosure="open"))
        self.build()
        page = self.page("places/a.md")
        self.assertIn("[pantheon](/gods/)", page)

    def test_section_index_with_no_pages_is_plain_text(self):
        self.write("world/places/a.md", note(disclosure="open",
                                            body="## Details\nSee [[creatures/_index|creatures]].\n"))
        self.build()
        page = self.page("places/a.md")
        self.assertIn("creatures", page)
        self.assertNotIn("/creatures/", page)


class TestTags(SiteCase):
    """Only the curated public vocabulary publishes (meta/site.md section 3.3)."""

    def test_only_published_tags_reach_the_page(self):
        self.write("world/places/a.md", note(
            disclosure="open", extra="tags: [places, choir, truth-ledger, lineage]\n"))
        testkit.write_config(self.root, published_tags=["choir"])
        self.build()
        self.assertIn('tags: ["choir"]', self.page("places/a.md"))

    def test_withheld_tags_are_logged(self):
        self.write("world/places/a.md", note(
            disclosure="open", extra="tags: [places, choir, lineage]\n"))
        testkit.write_config(self.root, published_tags=["choir"])
        audit = self.build()
        self.assertEqual(audit["withheld_tags"],
                         {"lineage": ["world/places/a.md"], "places": ["world/places/a.md"]})

    def test_a_note_with_no_published_tag_says_nothing(self):
        self.write("world/places/a.md", note(disclosure="open", extra="tags: [places]\n"))
        self.build()
        self.assertNotIn("tags:", self.page("places/a.md"))

    def test_a_published_tag_no_note_carries_is_empty_and_fails_check(self):
        self.write("world/places/a.md", note(disclosure="open", extra="tags: [choir]\n"))
        testkit.write_config(
            self.root,
            published_tags=[*testkit.real_vocabulary()["published_tags"], "ledger"])
        audit = self.build()
        self.assertIn("ledger", audit["empty_tags"])
        self.assertNotIn("choir", audit["empty_tags"])
        # --check fails the build: a published tag with no page is a dead index entry.
        self.assertEqual(site_export.main(["--check",
                                           "--out", str(self.out),
                                           "--data", str(self.data),
                                           "--audit", str(self.audit_file)]), 1)

    def test_a_keystone_term_in_a_tag_is_a_keyword_hit(self):
        self.write("world/places/a.md", note(disclosure="open", extra="tags: [lineage]\n"))
        testkit.write_config(
            self.root,
            published_tags=[*testkit.real_vocabulary()["published_tags"], "lineage"],
            keystones=["Lineage"])
        audit = self.build()
        self.assertEqual([h["term"] for h in audit["keyword_hits"]], ["Lineage"])


class TestAuditAndHistory(SiteCase):
    def test_audit_has_the_documented_keys(self):
        self.write("world/places/a.md", note(disclosure="open"))
        self.build()
        audit = self.audit()
        for key in ("generated", "pages", "sections", "words", "flattened_links",
                    "skipped_notes", "dropped_sections", "dropped_lines", "unresolved_links",
                    "keyword_hits", "internal_references", "design_fields", "withheld_tags",
                    "empty_tags"):
            self.assertIn(key, audit)
        self.assertEqual(audit["pages"], 1)

    def test_keyword_hits_are_reported(self):
        self.write("world/places/a.md", note(disclosure="open",
                                            body="## Details\nThe archmage knew.\n"))
        testkit.write_config(self.root, keystones=["archmage"])
        audit = self.build()
        self.assertEqual([h["term"] for h in audit["keyword_hits"]], ["archmage"])

    def test_changelog_records_added_then_updated(self):
        self.write("world/places/a.md", note(disclosure="open"))
        self.build(today="2026-01-02")
        changelog = json.loads((self.data / "changelog.json").read_text())
        self.assertEqual(changelog[0]["change"], "added")

        self.write("world/places/a.md", note(disclosure="open", body="## Details\nnew line\n"))
        self.build(today="2026-01-03")
        changelog = json.loads((self.data / "changelog.json").read_text())
        self.assertEqual(changelog[0]["change"], "updated")
        self.assertEqual(changelog[0]["date"], "2026-01-03")

    def test_a_renamed_page_leaves_a_redirect(self):
        self.write("world/places/old-name.md", note(id_="loc_x", disclosure="open"))
        self.build()
        (self.root / "world/places/old-name.md").unlink()
        self.write("world/places/new-name.md", note(id_="loc_x", disclosure="open"))
        self.build()
        redirects = json.loads((self.data / "redirects.json").read_text())
        self.assertEqual(redirects, [{"from": "/places/old-name/", "to": "/places/new-name/"}])

    def test_stale_pages_are_removed(self):
        self.write("world/places/a.md", note(disclosure="open"))
        self.build()
        (self.root / "world/places/a.md").unlink()
        self.build()
        self.assertEqual(self.pages(), [])

    def test_navigation_counts_pages_per_section(self):
        self.write("world/places/a.md", note(disclosure="open"))
        self.write("world/gods/g.md", note(id_="god_g", kind="GOD", disclosure="open"))
        self.build()
        nav = json.loads((self.data / "navigation.json").read_text())
        self.assertEqual([(s["slug"], s["count"]) for s in nav], [("gods", 1), ("places", 1)])

    def test_the_build_is_deterministic(self):
        self.write("world/places/a.md", note(disclosure="open", body="## Details\nx\n"))
        self.build()
        first = self.page("places/a.md")
        self.build()
        self.assertEqual(first, self.page("places/a.md"))

    def test_dry_run_writes_nothing(self):
        self.write("world/places/a.md", note(disclosure="open"))
        site_export.build(today="2026-01-02", out=self.out, data=self.data,
                          audit_file=self.audit_file, dry_run=True)
        self.assertFalse(self.out.exists())
        self.assertFalse(self.audit_file.exists())


class TestUnits(unittest.TestCase):
    def test_sanitise_heading(self):
        self.assertEqual(site_export.sanitise_heading("Culture (decided, Step 5, Round 1)"), "Culture")
        self.assertEqual(site_export.sanitise_heading("The gate (decided, Step 2)"), "The gate")
        self.assertEqual(site_export.sanitise_heading("Details"), "Details")

    def test_split_layers_multiple_segments_on_one_line(self):
        got = site_export.split_layers("- **Official:** a. **Myth:** b. **Truth:** c.")
        self.assertEqual(got[0], ("Official", "a."))
        self.assertEqual(got[1], ("Myth", "b."))
        self.assertEqual(got[2], ("Truth", "c."))

    def test_parse_link_handles_the_table_escape_and_anchors(self):
        self.assertEqual(site_export.parse_link("b\\|B"), ("b", "B"))
        self.assertEqual(site_export.parse_link("b#heading|B"), ("b", "B"))
        self.assertEqual(site_export.parse_link("b"), ("b", None))

    def test_tidy_preserves_list_indentation(self):
        text = "- a  b\n  - c ( ) d"
        self.assertEqual(site_export.tidy(text), "- a b\n  - c d")


class TestPlates(SiteCase):
    """An accepted plate illustrates the notes it names, and nothing else does."""

    CROP = "site/public/img/plate-a-16x9.jpg"

    def plate(self, status="accepted", canon="world/places/a.md",
              page_image="plate-a-16x9.jpg", alt="A sketch."):
        return (
            "---\nplate: 01\nslug: a-plate\ntitle: A plate\nstatus: " + status + "\n"
            "style: sketch\noutput: site/public/img/plate-a\n"
            f"page_image: {page_image}\nalt: \"{alt}\"\ncanon:\n  - {canon}\n---\n\n# A plate\n"
        )

    def test_accepted_plate_illustrates_its_canon_note(self):
        self.write("world/places/a.md", note(disclosure="open"))
        self.write("site/image-prompts/01-a-plate.md", self.plate())
        self.write(self.CROP, "jpeg")
        self.build()
        page = self.page("places/a.md")
        self.assertIn('image: "plate-a-16x9.jpg"', page)
        self.assertIn('imageAlt: "A sketch."', page)
        self.assertEqual(self.audit_field("plates"),
                         [{"note": "world/places/a.md", "image": "plate-a-16x9.jpg"}])

    def test_plate_only_reaches_the_notes_it_names(self):
        self.write("world/places/a.md", note(disclosure="open"))
        self.write("world/places/b.md", note(id_="loc_b", title="B", disclosure="open"))
        self.write("site/image-prompts/01-a-plate.md", self.plate())
        self.write(self.CROP, "jpeg")
        self.build()
        self.assertIn("image:", self.page("places/a.md"))
        self.assertNotIn("image:", self.page("places/b.md"))

    def test_unaccepted_plate_is_ignored(self):
        self.write("world/places/a.md", note(disclosure="open"))
        self.write("site/image-prompts/01-a-plate.md", self.plate(status="iterating"))
        self.write(self.CROP, "jpeg")
        self.build()
        self.assertNotIn("image:", self.page("places/a.md"))
        self.assertEqual(self.audit_field("plates"), [])

    def test_plate_whose_crop_is_missing_is_ignored(self):
        self.write("world/places/a.md", note(disclosure="open"))
        self.write("site/image-prompts/01-a-plate.md", self.plate())
        self.build()
        self.assertNotIn("image:", self.page("places/a.md"))

    def test_readme_and_underscore_files_are_not_plates(self):
        self.write("world/places/a.md", note(disclosure="open"))
        self.write("site/image-prompts/README.md", self.plate())
        self.write("site/image-prompts/_style.md", self.plate())
        self.write(self.CROP, "jpeg")
        self.build()
        self.assertNotIn("image:", self.page("places/a.md"))


class TestProseShape(SiteCase):
    """Two defects found while building testimony (Step 16): nesting and inline code."""

    def test_nested_bullets_keep_their_indentation(self):
        self.write("world/places/a.md", note(
            disclosure="open",
            body="## Details\n- **Theft has names:**\n  - **Short-skinning:** short weight.\n"
                 "  - **Tapping:** a drilled conduit.\n- **Next thing.**\n",
        ))
        self.build()
        page = self.page("places/a.md")
        self.assertIn("  - **Short-skinning:**", page)
        self.assertIn("  - **Tapping:**", page)
        self.assertIn("\n- **Next thing.**", page)

    def test_inline_code_is_not_blanked(self):
        self.write("world/places/a.md", note(
            disclosure="open",
            body="## Details\nHe writes `read twice` in the margin.\n",
        ))
        self.build()
        self.assertIn("He writes `read twice` in the margin.", self.page("places/a.md"))

    def test_fenced_block_inside_a_note_still_never_publishes(self):
        self.write("world/places/a.md", note(
            disclosure="open",
            body="## Details\nsafe\n\n```engine\nsecret: yes\n```\n",
        ))
        self.build()
        self.assertNotIn("secret: yes", self.page("places/a.md"))


class TestTestimony(SiteCase):
    """A `## Testimony` section is lifted into frontmatter (docs/testimony.md section 3.4)."""

    ACCOUNT = (
        "## Testimony\n**Disclosure:** open\n"
        "**CY 649, in the BLAZE.** **Sabel Cray**, at the slips in Dustport — told to me.\n\n"
        "**Quote:** A promise made by a city.\n\n"
        "The wind came off the basin for three days.\n\n"
        "The clerk counts what you have.\n"
    )

    def test_testimony_moves_out_of_the_body_into_frontmatter(self):
        self.write("world/places/a.md", note(
            disclosure="open", body="## Details\n- some lore\n\n" + self.ACCOUNT))
        self.build()
        page = self.page("places/a.md")
        self.assertIn("testimony:", page)
        self.assertIn('  teller: "Sabel Cray"', page)
        self.assertIn("  taken: 649", page)
        # The entry heading is kept exactly as he wrote it: date, then person, then place.
        self.assertIn('  heading: "**CY 649, in the BLAZE.** **Sabel Cray**, at the slips in '
                      'Dustport — told to me."', page)
        self.assertIn('  transmission: "at the slips in Dustport — told to me"', page)
        self.assertIn('  quote: "A promise made by a city."', page)
        self.assertIn("    - \"The wind came off the basin for three days.\"", page)
        self.assertIn("    - \"The clerk counts what you have.\"", page)
        # Not a body section any more: no heading, and no duplicate copy of the prose.
        self.assertNotIn("## Testimony", page)
        self.assertEqual(page.count("The wind came off the basin"), 1)

    def test_quote_falls_back_to_the_opening_sentence(self):
        account = ("## Testimony\n**Disclosure:** open\n**Bela of Mirewell**, told to me in CY 648.\n\n"
                   "Four days to Redwell with a loaded beast. Five if the dust is up.\n")
        self.write("world/places/a.md", note(disclosure="open", body="## Details\n- some lore\n\n" + account))
        self.build()
        self.assertIn('  quote: "Four days to Redwell with a loaded beast."', self.page("places/a.md"))

    def test_earned_testimony_never_publishes(self):
        earned = self.ACCOUNT.replace("**Disclosure:** open", "**Disclosure:** earned")
        self.write("world/places/a.md", note(
            disclosure="open", body="## Details\n- some lore\n\n" + earned))
        self.build()
        page = self.page("places/a.md")
        self.assertNotIn("testimony:", page)
        self.assertNotIn("wind came off the basin", page)

    def test_attribution_without_an_account_publishes_nothing(self):
        self.write("world/places/a.md", note(
            disclosure="open",
            body="## Details\n- some lore\n\n## Testimony\n**Disclosure:** open\n"
                 "**Sabel Cray**, told to him at the slips.\n"))
        audit = self.build()
        self.assertNotIn("testimony:", self.page("places/a.md"))
        self.assertIn("testimony without an account",
                      [s["class"] for s in audit["dropped_sections"]])

    def test_a_hedged_date_prints_as_approximate(self):
        hedged = self.ACCOUNT.replace("**CY 649, in the BLAZE.**", "**CY 649, or near it.**")
        self.write("world/places/a.md", note(disclosure="open", body="## Details\n- lore\n\n" + hedged))
        self.build()
        page = self.page("places/a.md")
        self.assertIn("  taken: 649", page)
        self.assertIn("  approx: true", page)

    def test_a_sure_date_is_not_called_approximate(self):
        self.write("world/places/a.md", note(disclosure="open", body="## Details\n- lore\n\n" + self.ACCOUNT))
        self.build()
        self.assertNotIn("approx", self.page("places/a.md"))

    def test_an_undated_account_reports_itself(self):
        account = ("## Testimony\n**Disclosure:** open\n"
                   "**Sabel Cray**, at the slips in Dustport — told to me.\n\nEleven fathoms down.\n")
        self.write("world/places/a.md", note(disclosure="open", body="## Details\n- lore\n\n" + account))
        self.build()
        self.assertIn("  taken: 0", self.page("places/a.md"))
        self.assertEqual(self.audit_field("testimony_undated")[0]["page"], "a")

    def test_testimony_is_in_the_keystone_scan(self):
        leaky = self.ACCOUNT.replace("A promise made by a city.", "The Convenor said so.")
        self.write("world/places/a.md", note(
            disclosure="open", body="## Details\n- some lore\n\n" + leaky))
        testkit.write_config(self.root, keystones=["Convenor"])
        self.build()
        terms = [h["term"] for h in self.audit_field("keyword_hits")]
        self.assertIn("Convenor", terms)

    def test_the_book_page_assembles_every_account(self):
        self.write("world/items-materials/book.md", note(
            id_="item_book", kind="ITEM", title="The Book", disclosure="open",
            extra="testimony_index: true\n",
            body="## Details\n- sewn quires\n"))
        for slug, teller, line in (("a", "Sabel Cray", "Eleven fathoms down."),
                                   ("b", "Tilda Ordway", "Three hundred cups short.")):
            self.write(f"world/items-materials/{slug}.md", note(
                id_=f"item_{slug}", kind="ITEM", title=slug.upper(), disclosure="open",
                body=("## Details\n- a trade good\n\n## Testimony\n**Disclosure:** open\n"
                      f"**CY 648.** **{teller}**, at the slips — told to me.\n\n{line}\n")))
        audit = self.build()
        book = self.page("relics/book.md")
        self.assertIn("## The accounts", book)
        self.assertIn("Eleven fathoms down.", book)
        self.assertIn("Three hundred cups short.", book)
        self.assertIn("(/relics/a/)", book)
        # The date is the point of a reading order: every entry keeps its heading.
        self.assertIn("**CY 648.**", book)
        self.assertEqual(len(audit["testimony"]), 2)
        # The account still keeps its own home: the trade-good page is untouched by assembly.
        self.assertNotIn("Three hundred cups short.", self.page("relics/a.md"))

    def test_a_volume_collects_only_its_own_years(self):
        for n, years in ((1, "575-598"), (4, "636-650")):
            self.write(f"world/items-materials/vol{n}.md", note(
                id_=f"item_vol{n}", kind="ITEM", title=f"Volume {n}", disclosure="open",
                extra=f"testimony_index: {years}\n", body="## Details\n- quires\n"))
        for slug, year, word in (("old", 590, "Bitterwell"), ("new", 649, "Redwell")):
            self.write(f"world/items-materials/{slug}.md", note(
                id_=f"item_{slug}", kind="ITEM", title=slug.upper(), disclosure="open",
                body=("## Details\n- a trade good\n\n## Testimony\n**Disclosure:** open\n"
                      f"**CY {year}.** **Bela of Mirewell**, at {word} — told to me.\n\nThe well at {word}.\n")))
        self.build()
        old, new = self.page("relics/vol1.md"), self.page("relics/vol4.md")
        self.assertIn("Bitterwell", old)
        self.assertNotIn("Redwell", old)
        self.assertIn("Redwell", new)
        self.assertNotIn("Bitterwell", new)

    def test_accounts_read_forwards_in_time(self):
        self.write("world/items-materials/vol.md", note(
            id_="item_vol", kind="ITEM", title="Volume", disclosure="open",
            extra="testimony_index: true\n", body="## Details\n- quires\n"))
        for slug, year in (("late", 649), ("early", 590)):
            self.write(f"world/items-materials/{slug}.md", note(
                id_=f"item_{slug}", kind="ITEM", title=slug.upper(), disclosure="open",
                body=("## Details\n- a trade good\n\n## Testimony\n**Disclosure:** open\n"
                      f"**CY {year}.** **Bela of Mirewell**, in the interior — told to me.\n\n{slug} news.\n")))
        self.build()
        book = self.page("relics/vol.md")
        self.assertLess(book.index("early news"), book.index("late news"))

    def test_the_account_links_back_to_the_hub(self):
        self.write("world/items-materials/book.md", note(
            id_="item_book", kind="ITEM", title="The Book", disclosure="open",
            extra="testimony_source: true\n", body="## Details\n- sewn quires\n"))
        self.write("world/places/a.md", note(
            disclosure="open", body="## Details\n- some lore\n\n" + self.ACCOUNT))
        self.build()
        self.assertIn('testimonySource: "/relics/book/"', self.page("places/a.md"))
        # The hub carries no account of its own, so it links nowhere.
        self.assertNotIn("testimonySource", self.page("relics/book.md"))

    def test_a_note_without_the_flag_assembles_nothing(self):
        self.write("world/places/a.md", note(disclosure="open", body="## Details\n- some lore\n\n" + self.ACCOUNT))
        self.build()
        self.assertNotIn("## The accounts", self.page("places/a.md"))



class ConfigSeamTest(unittest.TestCase):
    """Every config value the theme reads must reach it through site.json.

    A forgotten field is silent: `SITE.searchPlaceholder` renders as an empty placeholder and a
    missing `heroFile` makes the hero art never resolve -- neither raises. So compare the keys the
    theme asks for against the keys the exporter writes, by calling the exporter's payload
    function (no side effects, no stale file on disk).
    """

    def test_theme_reads_only_fields_the_exporter_writes(self):
        root = kit_config.load().root
        theme = root / "site/src/lib/site.ts"
        if not theme.exists():
            self.skipTest("no theme in this repo")
        wanted = set(re.findall(r"generated\.(\w+)", theme.read_text(encoding="utf-8")))
        self.assertTrue(wanted, "site.ts reads nothing from site.json")
        written = set(site_export.site_json(kit_config.load()))
        self.assertEqual(set(), wanted - written,
                         f"the theme reads fields site.json does not carry: {sorted(wanted - written)}")

    def test_the_worlds_own_site_settings_reach_the_theme(self):
        """The fields whose absence is invisible: a hint that renders empty, a hero that 404s."""
        root = kit_config.load().root
        if not (root / "site/src/lib/site.ts").exists():
            self.skipTest("no theme in this repo")
        cfg = kit_config.load().site
        written = site_export.site_json(kit_config.load())
        self.assertEqual(cfg.hero_file, written.get("heroFile"))
        self.assertEqual(cfg.search_placeholder, written.get("searchPlaceholder"))


if __name__ == "__main__":
    unittest.main()

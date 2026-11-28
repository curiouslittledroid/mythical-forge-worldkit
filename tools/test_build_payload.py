#!/usr/bin/env python3
"""Tests for `build_payload.py` -- the release payload a world syncs from.

The payload is the thing a world downloads instead of cloning the kit, so the failures that matter
are not "the tarball is wrong" but "the tarball is wrong in a way nobody notices until a world has
taken it": a member missing that the sync writes, a path that belongs to a world, an execute bit
lost in transit, a pin that disagrees with the tag on the release page.
"""

from __future__ import annotations

import io
import os
import sys
import tarfile
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # the suite runs from the repository root

import build_payload  # noqa: E402

REAL_ROOT = Path(__file__).resolve().parent.parent


def make_kit(root: Path, pin: str = "v9.9.9-test") -> Path:
    """A minimal kit: exactly what `build_payload.REQUIRED` names, and nothing else."""
    files = {
        "TOOLING_VERSION": pin + "\n",
        "LICENSE": "MIT\n",
        "LICENSE-CONTENT": "CC BY 4.0\n",
        "tools/lint.py": "# the linter\n",
        "tools/sync-tooling.sh": "#!/bin/sh\necho sync\n",
        "tools/kit_config.py": "# a tool\n",
        "tools/local/mine.py": "# world-owned: must never travel\n",
        "tools/docs/old.md": "# retired\n",
        "tools/__pycache__/x.pyc": "not text\n",
        "template/meta/conventions/conventions.md": "# conventions\n",
        "template/meta/conventions/tooling.md": "# tooling\n",
        "template/meta/conventions/agent-protocol.md": "# protocol\n",
        "template/meta/templates/topic.md": "# a template\n",
        "template/.pi/prompts/new-creature.md": "# a prompt\n",
        "template/example-world/world.config.yaml": "world:\n  id: world_fixture\n",
        "site-theme/package.json": "{}\n",
        "site-theme/src/pages/index.astro": "---\n---\n",
        "site-theme/public/favicon.svg": "<svg/>\n",
        "site-theme/infra/state.json": "{}\n",
        "site-theme/dist/index.html": "built\n",
        ".github/workflows/checks.yml": "name: Checks\n",
        ".github/workflows/site.yml": "name: Site\n",
        ".github/workflows/tooling-drift.yml": "name: Drift\n",
        ".github/workflows/ci.yml": "name: CI (the kit's own: never a world's)\n",
        "docs/extraction.md": "# the kit's own\n",
        "meta/platform-requests/register.md": "# the kit's own\n",
    }
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        if rel.endswith(".sh"):
            path.chmod(0o755)
    return root


def build(root: Path, pin: str = "v9.9.9-test", out: Path | None = None) -> Path:
    """Stage and pack into a scratch directory the CALLER can still read afterwards."""
    target_dir = out or (root.parent / "dist")
    target_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        payload = Path(tmp) / f"worldkit-{pin}"
        payload.mkdir()
        build_payload.stage(root, pin, payload)
        build_payload.pack(payload, target_dir / f"worldkit-{pin}.tar.gz")
    return target_dir / f"worldkit-{pin}.tar.gz"


class DeterminismCase(unittest.TestCase):
    """Two builds of the same tree are the same bytes, or the published digest means nothing."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = make_kit(Path(self.tmp.name) / "kit")

    def test_two_builds_of_one_tree_are_byte_identical(self):
        first = build(self.root, out=Path(self.tmp.name) / "a")
        second = build(self.root, out=Path(self.tmp.name) / "b")
        self.assertEqual(build_payload.sha256_of(first), build_payload.sha256_of(second))

    def test_mtime_does_not_leak_into_the_digest(self):
        # The real failure this prevents: a developer's checkout and CI's checkout of the same commit
        # produce different digests, so the release notes name a sum nobody can reproduce.
        first = build(self.root, out=Path(self.tmp.name) / "a")
        later = time.time() + 10_000
        for path in self.root.rglob("*"):
            path.touch()
            os.utime(path, (later, later))
        second = build(self.root, out=Path(self.tmp.name) / "b")
        self.assertEqual(build_payload.sha256_of(first), build_payload.sha256_of(second))

    def test_a_file_appearing_changes_it(self):
        first = build(self.root, out=Path(self.tmp.name) / "a")
        (self.root / "tools" / "extra.py").write_text("# new\n", encoding="utf-8")
        second = build(self.root, out=Path(self.tmp.name) / "b")
        self.assertNotEqual(build_payload.sha256_of(first), build_payload.sha256_of(second))


class WhatTravelsCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = make_kit(Path(self.tmp.name) / "kit")
        self.payload = build(self.root)
        with tarfile.open(self.payload) as archive:
            self.names = {name.split("/", 1)[1] for name in archive.getnames() if "/" in name}

    def test_the_world_facing_material_is_all_there(self):
        for rel in ("tools/lint.py", "tools/sync-tooling.sh", "tools/LICENSE", "tools/LICENSE-CONTENT",
                    "template/meta/conventions/conventions.md", "template/meta/templates/topic.md",
                    "template/.pi/prompts/new-creature.md", "template/example-world/world.config.yaml",
                    "site-theme/package.json", "site-theme/src/pages/index.astro",
                    ".github/workflows/tooling-drift.yml", "TOOLING_VERSION", "ARCHIVE.md"):
            with self.subTest(rel=rel):
                self.assertIn(rel, self.names)

    def test_the_kits_own_maintenance_never_travels(self):
        for rel in ("docs/extraction.md", "meta/platform-requests/register.md"):
            with self.subTest(rel=rel):
                self.assertNotIn(rel, self.names)

    def test_a_worlds_own_paths_never_travel(self):
        # `tools/local/`, the theme's built output and its deploy state are a world's; `site/public/`
        # is the one that looks like the kit's and is not (the sync never writes it).
        for rel in ("tools/local/mine.py", "tools/__pycache__/x.pyc", "tools/docs/old.md",
                    "site-theme/public/favicon.svg", "site-theme/infra/state.json",
                    "site-theme/dist/index.html"):
            with self.subTest(rel=rel):
                self.assertNotIn(rel, self.names)

    def test_only_the_worlds_three_workflows_travel(self):
        self.assertNotIn(".github/workflows/ci.yml", self.names)
        self.assertIn(".github/workflows/checks.yml", self.names)

    def test_the_licences_land_beside_the_tools(self):
        # MIT requires the notice to travel with the copy, and a vendored `tools/` is a copy.
        self.assertIn("tools/LICENSE", self.names)
        self.assertIn("tools/LICENSE-CONTENT", self.names)


class ExecuteBitCase(unittest.TestCase):
    def test_a_shell_tool_keeps_its_bit(self):
        # A release once shipped a non-executable sync, and the failure read "Permission denied" on
        # the command the docs tell you to run.
        with tempfile.TemporaryDirectory() as tmp:
            root = make_kit(Path(tmp) / "kit")
            (root / "tools" / "deploy.sh").write_text("#!/bin/sh\n", encoding="utf-8")
            (root / "tools" / "deploy.sh").chmod(0o755)
            payload = build(root)
            with tarfile.open(payload) as archive:
                member = archive.getmember(f"worldkit-v9.9.9-test/tools/deploy.sh")
            self.assertTrue(member.mode & 0o111, oct(member.mode))
            build_payload.check(payload)  # and `--check` agrees

    def test_check_refuses_a_payload_whose_shell_tool_lost_its_bit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_kit(Path(tmp) / "kit")
            payload = build(root)
            # Repack with the bit cleared, the way a Windows checkout would produce it.
            broken = Path(tmp) / payload.name
            with tarfile.open(payload) as source, tarfile.open(broken, "w:gz") as dest:
                for member in source.getmembers():
                    if member.name.endswith(".sh"):
                        member.mode = 0o644
                    dest.addfile(member, source.extractfile(member) if member.isfile() else None)
            with self.assertRaises(build_payload.PayloadError) as caught:
                build_payload.check(broken)
            self.assertIn("execute bit", str(caught.exception))


class CheckCase(unittest.TestCase):
    """`--check` is what CI and a world both trust, so each refusal is a test."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = make_kit(Path(self.tmp.name) / "kit")
        self.payload = build(self.root)

    def repack(self, drop=(), add=None, rename_top=None) -> Path:
        """Rewrite the payload with one member removed, one added, or a different root name."""
        out = Path(self.tmp.name) / self.payload.name
        with tarfile.open(self.payload) as source, tarfile.open(out, "w:gz") as dest:
            for member in source.getmembers():
                if member.name.split("/", 1)[-1] in drop:
                    continue
                if rename_top:
                    member.name = member.name.replace("worldkit-v9.9.9-test", rename_top, 1)
                dest.addfile(member, source.extractfile(member) if member.isfile() else None)
            for rel, text in (add or {}).items():
                data = text.encode()
                info = tarfile.TarInfo(f"worldkit-v9.9.9-test/{rel}")
                info.size, info.mode = len(data), 0o644
                dest.addfile(info, io.BytesIO(data))
        return out

    def test_a_good_payload_passes_and_reports_its_pin(self):
        self.assertEqual(build_payload.check(self.payload), "v9.9.9-test")

    def test_a_missing_member_the_sync_writes_is_caught(self):
        with self.assertRaises(build_payload.PayloadError) as caught:
            build_payload.check(self.repack(drop={"tools/sync-tooling.sh"}))
        self.assertIn("tools/sync-tooling.sh", str(caught.exception))

    def test_a_world_owned_path_that_sneaked_in_is_caught(self):
        with self.assertRaises(build_payload.PayloadError) as caught:
            build_payload.check(self.repack(add={"tools/local/mine.py": "# ours\n"}))
        self.assertIn("tools/local/", str(caught.exception))

    def test_a_top_level_that_does_not_match_the_name_is_caught(self):
        with self.assertRaises(build_payload.PayloadError) as caught:
            build_payload.check(self.repack(rename_top="worldkit-v0.0.1"))
        self.assertIn("top-level", str(caught.exception))

    def test_a_checksum_mismatch_is_caught(self):
        with self.assertRaises(build_payload.PayloadError) as caught:
            build_payload.check(self.payload, "0" * 64)
        self.assertIn("checksum", str(caught.exception))

    def test_a_traversing_path_is_caught(self):
        out = Path(self.tmp.name) / "evil.tar.gz"
        with tarfile.open(out, "w:gz") as archive:
            for name in ("worldkit-v9.9.9-test/", "worldkit-v9.9.9-test/../../etc/passwd"):
                info = tarfile.TarInfo(name)
                archive.addfile(info)
        with self.assertRaises(build_payload.PayloadError) as caught:
            build_payload.check(out)
        self.assertIn("traversing", str(caught.exception))

    def test_two_top_level_entries_are_caught(self):
        # The sync moves "the one top-level directory" it finds; two would have been half-applied.
        out = Path(self.tmp.name) / "two.tar.gz"
        with tarfile.open(out, "w:gz") as archive:
            for name in ("worldkit-v9.9.9-test/", "worldkit-v9.9.9-test/TOOLING_VERSION", "other/"):
                archive.addfile(tarfile.TarInfo(name))
        with self.assertRaises(build_payload.PayloadError) as caught:
            build_payload.check(out)
        self.assertIn("top-level", str(caught.exception))


class TagIsThePinCase(unittest.TestCase):
    def test_a_tag_that_disagrees_with_tooling_version_is_refused(self):
        # The release page and the payload must name the same version, or every world that takes it
        # pins a version it is not holding (CONTRIBUTING.md, Release step 4).
        with tempfile.TemporaryDirectory() as tmp:
            root = make_kit(Path(tmp) / "kit", pin="v9.9.9-test")
            out = Path(tmp) / "worldkit-v1.0.0"
            out.mkdir()
            with self.assertRaises(build_payload.PayloadError) as caught:
                build_payload.stage(root, "v1.0.0", out)
            self.assertIn("TOOLING_VERSION", str(caught.exception))

    def test_a_directory_that_is_not_a_kit_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(build_payload.PayloadError) as caught:
                build_payload.stage(Path(tmp), "v1.0.0", Path(tmp) / "out")
            self.assertIn("not a worldkit", str(caught.exception))


class TheRealKitCase(unittest.TestCase):
    """The payload the kit actually ships. This is the integration test the release job runs."""

    @classmethod
    def setUpClass(cls):
        # The payload is built from the KIT: it reads `template/`, which a world does not have. The
        # suite ships in `tools/`, so a world runs it too, and the honest answer there is to say so.
        if not (REAL_ROOT / "template/meta/conventions").is_dir():
            raise unittest.SkipTest(
                "not a kit checkout: a payload is built from template/, which only the kit has"
            )
        cls.tmp = tempfile.TemporaryDirectory()
        cls.pin = (REAL_ROOT / "TOOLING_VERSION").read_text(encoding="utf-8").strip()
        cls.payload = build(REAL_ROOT, cls.pin, out=Path(cls.tmp.name))
        cls.checked = build_payload.check(cls.payload)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_it_passes_its_own_check(self):
        self.assertEqual(self.checked, self.pin)

    def test_the_tarball_name_ends_in_the_pin(self):
        self.assertTrue(self.payload.name.endswith(f"worldkit-{self.pin}.tar.gz"))

    def test_its_summary_file_names_the_same_digest(self):
        summary = self.payload.with_suffix(self.payload.suffix + ".sha256").read_text(encoding="utf-8")
        self.assertEqual(summary.split()[0], build_payload.sha256_of(self.payload))

    def test_the_tools_it_carries_are_the_tools_this_checkout_has(self):
        # The payload is a copy, not a build: a difference means the staging has an exclusion the
        # kit's tools/ does not, and a world would take a kit that is not this one.
        with tarfile.open(self.payload) as archive:
            for name in archive.getnames():
                rel = name.split("/", 1)[-1]
                if not rel.startswith("tools/") or not "/" in rel:
                    continue
                source = REAL_ROOT / rel
                if not source.is_file() or rel.startswith(("tools/local/", "tools/docs/")):
                    continue
                with self.subTest(rel=rel):
                    self.assertEqual(archive.extractfile(name).read(), source.read_bytes())

    def test_the_documents_it_carries_are_the_ones_a_world_reads(self):
        with tarfile.open(self.payload) as archive:
            member = "worldkit-" + self.pin + "/template/meta/conventions/conventions.md"
            self.assertEqual(archive.extractfile(member).read(),
                             (REAL_ROOT / "template/meta/conventions/conventions.md").read_bytes())

    def test_it_carries_none_of_the_kits_own_maintenance(self):
        with tarfile.open(self.payload) as archive:
            names = archive.getnames()
        for fragment in ("/docs/", "/meta/platform-requests/", "extraction.md", "/tools/local/"):
            with self.subTest(fragment=fragment):
                self.assertFalse([n for n in names if fragment in f"/{n}/"], fragment)


if __name__ == "__main__":
    unittest.main(verbosity=2)

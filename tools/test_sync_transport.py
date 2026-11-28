#!/usr/bin/env python3
"""The sync's transport: a release payload and a checkout must produce the same world.

The claim `tools/verify-payload.sh` makes from the shell is made here from Python, on a fixture
small enough to read: build a world twice, once from a clone and once from an archive, and compare
them byte for byte. What the fixture adds is the cases a payload has and a clone does not -- a
checksum, a pin that disagrees with the tag, an offline machine -- and they are the ones that fail
*silently* in production: a refused payload that quietly becomes a clone, or an argument lost across
the script's own re-exec, both end in a world that looks updated.

Run: python3 tools/test_sync_transport.py
"""
from __future__ import annotations

import hashlib
import io
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SYNC = ROOT / "tools/sync-tooling.sh"
MARKER = "STEP-ADDED-IN-THE-NEW-RELEASE"


class TransportCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.kit = self.base / "kit"
        self._kit()
        self.world = self._world("clone")
        self.archive = self._archive()

    def tearDown(self):
        self.tmp.cleanup()

    # --- fixtures ------------------------------------------------------------------------------

    def _kit(self) -> None:
        """A stand-in worldkit. The marker proves a NEW script's step ran, not the old one's."""
        for rel, text in {
            "TOOLING_VERSION": "v9.9.9\n",
            "LICENSE": "MIT\n",
            "LICENSE-CONTENT": "CC BY 4.0\n",
            "template/meta/conventions/conventions.md": "# Conventions\n",
            "template/meta/templates/npc.md": "# npc\n",
            "site/src/lib/site.ts": "// theme\n",
        }.items():
            path = self.kit / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        script = SYNC.read_text(encoding="utf-8").replace(
            'echo "sync-tooling: $OLD -> $TAG"',
            'echo "sync-tooling: $OLD -> $TAG"\necho "MARKER: ' + MARKER + '"')
        (self.kit / "tools").mkdir(parents=True, exist_ok=True)
        (self.kit / "tools/sync-tooling.sh").write_text(script, encoding="utf-8")
        (self.kit / "tools/sync-tooling.sh").chmod(0o755)
        subprocess.run(["git", "init", "-q"], cwd=self.kit, check=True)
        subprocess.run(["git", "add", "-A"], cwd=self.kit, check=True)
        subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "kit"],
                       cwd=self.kit, check=True)
        subprocess.run(["git", "tag", "v9.9.9"], cwd=self.kit, check=True)

    def _world(self, name: str, script: Path | None = None, pin: str = "v9.9.8") -> Path:
        world = self.base / name
        (world / "tools").mkdir(parents=True, exist_ok=True)
        shutil.copy2(script or SYNC, world / "tools/sync-tooling.sh")
        (world / "tools/sync-tooling.sh").chmod(0o755)     # as a world's copy is
        (world / "tools/local").mkdir(exist_ok=True)
        (world / "tools/local/mine.sh").write_text("#!/bin/sh\necho mine\n", encoding="utf-8")
        (world / "TOOLING_VERSION").write_text(pin + "\n", encoding="utf-8")
        return world

    def _archive(self, tag: str = "v9.9.9", pin: str | None = None) -> Path:
        """Pack the fake kit as a payload, one top-level directory, as the real one is."""
        out = self.base / f"worldkit-{tag}.tar.gz"
        with tarfile.open(out, "w:gz") as archive:
            for base, dirs, files in os.walk(self.kit):
                if ".git" in dirs:
                    dirs.remove(".git")
                dirs.sort()
                for name in sorted(files):
                    full = Path(base) / name
                    rel = full.relative_to(self.kit)
                    if rel.name == "TOOLING_VERSION" and pin:
                        data = (pin + "\n").encode()
                    else:
                        data = full.read_bytes()
                    info = tarfile.TarInfo(f"worldkit-{tag}/{rel.as_posix()}")
                    info.size, info.mtime = len(data), 315532800
                    info.mode = full.stat().st_mode & 0o777
                    archive.addfile(info, io.BytesIO(data))
        digest = hashlib.sha256(out.read_bytes()).hexdigest()
        out.with_suffix(out.suffix + ".sha256").write_text(f"{digest}  {out.name}\n", encoding="utf-8")
        return out

    # --- running -----------------------------------------------------------------------------

    def run_sync(self, *args: str, repo: str | None = "default") -> tuple[int, str]:
        env = dict(os.environ)
        # A world's own repo: the rails must not refuse because the fixture is not a checkout.
        env.pop("SYNC_REEXEC", None)
        env["WORLDKIT_REPO"] = repo if repo is not None else str(self.kit)
        world = self.world
        proc = subprocess.run([str(world / "tools/sync-tooling.sh"), *args],
                              cwd=world, env=env, capture_output=True, text=True)
        return proc.returncode, proc.stdout + proc.stderr

    def snapshot(self, root: Path) -> dict[str, str]:
        """Path -> mode+content. Deliberately not mtime: the sync's `cp` stamps a fresh one."""
        out = {}
        for base, dirs, files in os.walk(root):
            dirs.sort()
            for name in dirs + files:
                path = Path(base) / name
                rel = path.relative_to(root).as_posix()
                if path.is_dir():
                    out[rel + "/"] = oct(path.stat().st_mode & 0o777)
                else:
                    out[rel] = oct(path.stat().st_mode & 0o777) + ":" + hashlib.sha256(
                        path.read_bytes()).hexdigest()
        return out

    # --- the invariant ------------------------------------------------------------------------

    def test_the_archive_and_the_checkout_produce_the_same_world(self):
        world_archive = self._world("archive")
        code, out = self.run_sync("v9.9.9", repo=str(self.kit))
        self.assertEqual(0, code, out)
        self.assertIn(f"MARKER: {MARKER}", out)

        self.world, saved = world_archive, self.world
        try:
            code, out = self.run_sync("--archive", str(self.archive), repo="https://invalid.invalid/x")
        finally:
            self.world = saved
        self.assertEqual(0, code, out)
        self.assertEqual(self.snapshot(self.base / "clone"), self.snapshot(world_archive))

    def test_the_archive_needs_no_network(self):
        # Get this wrong and an offline sync either fails or -- worse -- quietly clones.
        code, out = self.run_sync("--archive", str(self.archive), repo="https://invalid.invalid/x")
        self.assertEqual(0, code, out)
        self.assertNotIn("invalid.invalid", out.split("\n")[-5:])
        self.assertEqual("v9.9.9\n", (self.world / "TOOLING_VERSION").read_text())

    def test_the_worlds_own_script_survives_every_transport(self):
        code, out = self.run_sync("--archive", str(self.archive))
        self.assertEqual(0, code, out)
        self.assertTrue((self.world / "tools/local/mine.sh").exists())

    # --- the refusals -------------------------------------------------------------------------

    def test_a_bad_checksum_is_refused_and_nothing_is_written(self):
        before = self.snapshot(self.world)
        code, out = self.run_sync("--archive", str(self.archive), "--sha256", "0" * 64)
        self.assertEqual(2, code, out)
        self.assertIn("does not match its checksum", out)
        self.assertEqual(before, self.snapshot(self.world), "a refused payload wrote something")

    def test_the_published_summary_beside_the_file_is_used_without_being_asked(self):
        self.archive.with_suffix(self.archive.suffix + ".sha256").write_text("0" * 64 + "  x\n",
                                                                           encoding="utf-8")
        code, out = self.run_sync("--archive", str(self.archive))
        self.assertEqual(2, code, out)
        self.assertIn("does not match its checksum", out)

    def test_a_payload_whose_pin_is_not_the_tag_asked_for_is_refused(self):
        other = self._archive(tag="v9.9.9", pin="v1.0.0")
        code, out = self.run_sync("--archive", str(other), "v9.9.9")
        self.assertEqual(2, code, out)
        self.assertIn("v1.0.0", out)
        self.assertEqual("v9.9.8\n", (self.world / "TOOLING_VERSION").read_text())

    def test_an_archive_with_two_top_level_directories_is_refused(self):
        # `find | head -1` used to pick one and report success.
        repacked = self.base / "two-roots.tar.gz"
        with tarfile.open(self.archive) as source, tarfile.open(repacked, "w:gz") as dest:
            for member in source.getmembers():
                dest.addfile(member, source.extractfile(member) if member.isfile() else None)
            dest.addfile(tarfile.TarInfo("stray/"))
        self.archive = repacked
        code, out = self.run_sync("--archive", str(self.archive))
        self.assertEqual(2, code, out)
        self.assertIn("top-level entries", out)

    def test_the_option_you_passed_survives_the_self_reexec(self):
        """The regression test for the bug that made `--archive` run a clone instead.

        The re-exec passed `${TAG}` and nothing else, so every option was dropped. With `--archive`
        that meant a world's worth of files came from the network while the operator believed the
        run was offline -- and it exited 0. The world's script here is an OLDER one that already
        understands `--archive` but not the marker step, so the re-exec has to happen: if the option
        is not carried, the run reaches for the network and fails against an unreachable repo.
        """
        old = SYNC.read_text(encoding="utf-8")
        old_path = self.base / "old-sync.sh"
        old_path.write_text(old, encoding="utf-8")
        old_path.chmod(0o755)
        self.world = self._world("older", script=old_path)

        code, out = self.run_sync("--archive", str(self.archive), repo="https://invalid.invalid/x")
        self.assertEqual(0, code, out)
        self.assertIn("re-running with the new version", out)
        self.assertIn(f"MARKER: {MARKER}", out)
        self.assertEqual("v9.9.9\n", (self.world / "TOOLING_VERSION").read_text())

    def test_the_deletion_preview_keeps_the_archive_too(self):
        """Same bug, second site: the preview re-ran the sync as `--dry-run "$TAG"`.

        An offline sync then fetched the network to draw up its deletion list, compared against a
        different tree, and reported files that were never deletions -- and the message tells the
        reader to pass `--force`, which is how a real finding gets forced away.
        """
        (self.world / "tools/stray.py").write_text("# a world's file where only the kit's belong\n",
                                                   encoding="utf-8")
        code, out = self.run_sync("--archive", str(self.archive), repo="https://invalid.invalid/x")
        self.assertEqual(2, code, out)
        self.assertIn("refusing to run: this sync would DELETE files", out)
        self.assertIn("stray.py", out)
        self.assertNotIn("invalid.invalid", out.replace("https://invalid.invalid/x", ""))

    def test_dry_run_writes_nothing(self):
        before = self.snapshot(self.world)
        code, out = self.run_sync("--dry-run", "--archive", str(self.archive))
        self.assertEqual(0, code, out)
        self.assertEqual(before, self.snapshot(self.world))
        self.assertIn("DRY RUN", out)

    def test_an_option_with_no_value_is_refused_rather_than_ignored(self):
        # `for arg in "$@"` could not consume an option's value at all; an empty one then fell
        # silently through to the network, which is the opposite of what `--archive` promises.
        code, out = self.run_sync("--archive")
        self.assertEqual(2, code, out)
        self.assertIn("--archive needs a file", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)

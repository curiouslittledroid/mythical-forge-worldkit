#!/usr/bin/env python3
"""The sync re-executes itself when the release replaces the running script -- and it must not
delete the world's rules on the way past.

The second is a regression test for a real bug that the END STATE hid perfectly. The kit keeps
`docs/` as a sibling of `tools/`; a world keeps it at `tools/docs/`. So the `tools/` rsync found
`docs/` present in the world and absent from the kit, deleted it, and the next line recreated it --
on every run. Every finished sync looked correct. A sync that stopped in between (a refusal, a
Ctrl-C) left a world with no rules at all.

An end-state assertion cannot see that, which is why this one uses a probe: a file in `tools/docs/`
that the kit does not have. If the rsync can delete it, the exclusion is missing.

Without it, a release that adds a sync step does not run that step when a world takes the release:
`tools/` is copied early, the running script keeps executing the old text, and the new step is
silently skipped. The comparison must be against a copy of the running script, because the rsync
has just made the destination identical to the kit's.

Run: python3 tools/test_sync_reexec.py
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SYNC = ROOT / "tools/sync-tooling.sh"


class ReexecCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.kit = self.base / "kit"
        self.world = self.base / "world"
        self._kit(marker="STEP-ADDED-IN-THE-NEW-RELEASE")
        self._world()

    def tearDown(self):
        self.tmp.cleanup()

    def _kit(self, marker: str) -> None:
        """A stand-in worldkit: a version, a tools/ sync script that prints a marker, one template."""
        (self.kit / "tools").mkdir(parents=True)
        (self.kit / "docs").mkdir(parents=True)
        (self.kit / "meta/templates").mkdir(parents=True)
        # A theme, or the site step does not run at all -- and then the test cannot see what the
        # site step does to a world's generated directories. (It could not: the first version of
        # this fixture had no site/, so the assertion passed with the bug present.)
        (self.kit / "site/src/lib").mkdir(parents=True)
        (self.kit / "site/src/lib/site.ts").write_text("// theme\n", encoding="utf-8")
        (self.kit / "docs/conventions.md").write_text("# Conventions\n", encoding="utf-8")
        (self.kit / "LICENSE").write_text("MIT\n", encoding="utf-8")
        (self.kit / "LICENSE-CONTENT").write_text("CC BY 4.0\n", encoding="utf-8")
        (self.kit / "TOOLING_VERSION").write_text("v9.9.9\n", encoding="utf-8")
        (self.kit / "meta/templates/npc.md").write_text("# npc\n", encoding="utf-8")
        script = SYNC.read_text(encoding="utf-8").replace(
            'echo "sync-tooling: $OLD -> $TAG"',
            'echo "sync-tooling: $OLD -> $TAG"\necho "MARKER: ' + marker + '"')
        (self.kit / "tools/sync-tooling.sh").write_text(script, encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=self.kit, check=True)
        subprocess.run(["git", "add", "-A"], cwd=self.kit, check=True)
        subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit",
                        "-qm", "kit"], cwd=self.kit, check=True)
        subprocess.run(["git", "tag", "v9.9.9"], cwd=self.kit, check=True)

    def _world(self, script: Path | None = None) -> None:
        (self.world / "tools").mkdir(parents=True, exist_ok=True)
        # The generated site directories: a world that has built its site has them, the kit never
        # does. A sync that deletes them breaks the next build, and one that REFUSES because of them
        # is a false alarm -- which is worse, because it teaches a world to pass --force.
        for rel in ("site/src/data/generated", "site/src/content/generated"):
            (self.world / rel).mkdir(parents=True, exist_ok=True)
            (self.world / rel / "x.json").write_text("{}\n", encoding="utf-8")
        shutil.copy2(script or SYNC, self.world / "tools/sync-tooling.sh")
        (self.world / "tools/sync-tooling.sh").chmod(0o755)   # as a world's copy is
        (self.world / "world.config.yaml").write_text("version: 1\n", encoding="utf-8")
        (self.world / "TOOLING_VERSION").write_text("v9.9.8\n", encoding="utf-8")

    def run_sync(self) -> str:
        env = {**os.environ, "WORLDKIT_REPO": str(self.kit)}
        proc = subprocess.run([str(self.world / "tools/sync-tooling.sh"), "v9.9.9"],
                              cwd=self.world, env=env, capture_output=True, text=True)
        return proc.stdout + proc.stderr

    def test_the_new_step_runs_even_though_the_old_script_started(self):
        out = self.run_sync()
        self.assertIn("re-running with the new version", out)
        self.assertIn("MARKER: STEP-ADDED-IN-THE-NEW-RELEASE", out)
        self.assertEqual("v9.9.9\n", (self.world / "TOOLING_VERSION").read_text())

    def test_it_does_not_loop(self):
        out = self.run_sync()
        self.assertEqual(1, out.count("re-running with the new version"))

    def test_a_second_sync_has_nothing_to_delete(self):
        """The regression test for the bug the end state hid.

        The kit keeps `docs/` as a sibling of `tools/`; a world keeps it at `tools/docs/`. So the
        `tools/` rsync used to find `docs/` in the world and not in the kit, delete it, and let the
        next line recreate it -- on every run. Every *finished* sync looked correct, which is why it
        survived two releases.

        One sync puts the docs where a world keeps them, so the second sync is the case that used to
        plan ten deletions and, once the rails existed, refuse. It must find nothing to do.
        """
        first = self.run_sync()
        self.assertNotIn("refusing to run", first)
        self.assertEqual("# Conventions\n",
                         (self.world / "tools/docs/conventions.md").read_text(encoding="utf-8"))

        second = self.run_sync()
        self.assertIn("sync-tooling: v9.9.9 -> v9.9.9", second)
        for rel in ("tools/LICENSE", "tools/LICENSE-CONTENT"):
            self.assertTrue((self.world / rel).exists(),
                            f"{rel} did not travel with the code it covers")
        for rel in ("site/src/data/generated/x.json", "site/src/content/generated/x.json"):
            self.assertTrue((self.world / rel).exists(), f"the sync deleted {rel}")
        self.assertNotIn("refusing to run", second,
                         "a normal sync should find nothing to delete inside tools/docs/")
        self.assertTrue((self.world / "tools/docs/conventions.md").exists())

    def test_an_unchanged_script_is_not_re_run(self):
        self._world(script=self.kit / "tools/sync-tooling.sh")   # already the new one
        out = self.run_sync()
        self.assertNotIn("re-running with the new version", out)
        self.assertIn("MARKER:", out)


if __name__ == "__main__":
    unittest.main()

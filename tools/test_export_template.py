#!/usr/bin/env python3
"""Tests for `export-template.sh`'s REPLACE step: what it says before it deletes, and that it survives
saying it.

The bug this exists for killed the export silently at the last step before anything was written:

    ./export-template.sh v3.4.0 ../mythical-forge-world-template --force
    export-template: removing 14687 path(s) the export does not produce:
      site/node_modules/...
      ...
    ./export-template.sh: line 191: printf: write error: Broken pipe

`printf '%s\\n' "$gone" | head -20` -- `head` exits after twenty lines, `printf` takes SIGPIPE
writing the rest, and `set -o pipefail` turns that into the script dying inside its own progress
report. Exit 1, no message naming the cause, and the destination left exactly as it was, because the
`rsync --delete` on the next line never ran.

Why it took a year to appear: the writer has to fill a pipe (64K) for the reader to have exited
first. A template checkout with a few retired paths never does. One that has been BUILT does --
`site/node_modules` and the exporter's generated directories are thousands of paths the export does
not produce -- and exporting over it is exactly what a maintainer does after proving the site.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXPORT = ROOT / "export-template.sh"


class ExportReplaceCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # The export reads `template/`, which only a kit has. The suite ships in `tools/`, so a
        # world runs it too, and the honest answer there is to say so.
        if not (ROOT / "template" / "meta" / "conventions").is_dir():
            raise unittest.SkipTest("not a kit checkout: an export needs template/, which only the kit has")
        if shutil.which("rsync") is None:
            raise unittest.SkipTest("rsync is not installed")

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.dest = self.base / "template-checkout"
        # A destination that has been built: enough paths to fill a pipe, which is the condition the
        # old code needed in order to fail.
        package = self.dest / "site/node_modules/a-package-with-a-long-enough-name/dist/esm"
        package.mkdir(parents=True)
        for i in range(3000):
            (package / f"a-module-file-with-a-long-name-{i:05d}.js").write_text("x\n", encoding="utf-8")
        (self.dest / "a-retired-path.md").write_text("gone\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def export(self) -> subprocess.CompletedProcess:
        return subprocess.run([str(EXPORT), "--worktree", str(self.dest), "--force"],
                              cwd=ROOT, capture_output=True, text=True)

    def test_it_survives_a_destination_big_enough_to_fill_a_pipe(self):
        done = self.export()
        self.assertEqual(0, done.returncode, done.stdout + done.stderr)
        self.assertNotIn("Broken pipe", done.stderr)

    def test_the_preview_truncates_and_says_how_many_it_hid(self):
        out = self.export().stdout
        self.assertIn("path(s) the export does not produce", out)
        hidden = [line for line in out.splitlines() if line.startswith("  ... and ")]
        self.assertEqual(1, len(hidden), out[-500:])
        # `... and N more`, and N is the remainder of the count the line above it named.
        total = int([line for line in out.splitlines() if "removing" in line][0]
                    .split("removing ")[1].split(" path")[0])
        self.assertEqual(total - 20, int(hidden[0].split("and ")[1].split(" more")[0]))

    def test_the_export_actually_happened(self):
        # The old failure left the destination untouched and said nothing about why, which reads as
        # "the export ran". This is the half of the assertion that matters: it did.
        self.export()
        self.assertTrue((self.dest / "world.config.yaml").is_file())
        self.assertFalse((self.dest / "site/node_modules").exists(), "the stale tree was not replaced")
        self.assertFalse((self.dest / "a-retired-path.md").exists(), "a retired path survived")

    def test_a_clean_destination_says_nothing_about_removing(self):
        shutil.rmtree(self.dest / "site")
        (self.dest / "a-retired-path.md").unlink()
        out = self.export().stdout
        self.assertNotIn("does not produce", out)
        self.assertIn("wrote", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)

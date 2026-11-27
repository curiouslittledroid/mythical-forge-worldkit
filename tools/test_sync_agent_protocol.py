#!/usr/bin/env python3
"""Tests for the one tool that keeps a duplicate honest.

The agent protocol is copied verbatim into a world's `AGENTS.md` on purpose (an agent may never
follow a link out of its repository), so a silent divergence is the failure mode this tool exists to
catch. It was also broken by a hand edit while being written, which is the other reason for these.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE / "sync-agent-protocol.py"


def find_source() -> Path:
    """The protocol, wherever the kit keeps it: the template's conventions/, or a world's own."""
    for rel in ("template/meta/conventions/agent-protocol.md",
                "meta/conventions/agent-protocol.md",
                "tools/docs/agent-protocol.md"):
        p = HERE.parent / rel
        if p.is_file():
            return p
    raise SystemExit(f"test_sync_agent_protocol: no agent-protocol.md beside {HERE}")


SOURCE = find_source()

BEGIN = "<!-- BEGIN agent-protocol — synced; edit that, not this -->"
END = "<!-- END agent-protocol -->"


def world(root: Path, *, body: str = "PLACEHOLDER", markers: bool = True) -> Path:
    """A throwaway world: a config, the vendored protocol, and an AGENTS.md with the region."""
    (root / "meta" / "conventions").mkdir(parents=True, exist_ok=True)
    (root / "meta" / "conventions" / "agent-protocol.md").write_text(
        SOURCE.read_text(encoding="utf-8"), encoding="utf-8")
    (root / "world.config.yaml").write_text("version: 1\n", encoding="utf-8")
    if markers:
        text = f"# AGENTS.md: the world\n\n## My brief\n\n| a | b |\n\n{BEGIN}\n{body}\n{END}\n"
    else:
        text = "# AGENTS.md: the world\n\nNo markers here at all.\n"
    (root / "AGENTS.md").write_text(text, encoding="utf-8")
    return root


def run(root: Path, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "WORLD_CONFIG": str(root / "world.config.yaml")}
    return subprocess.run([sys.executable, str(TOOL), *args], capture_output=True, text=True, env=env)


class SyncAgentProtocol(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = world(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def test_it_writes_the_region_and_leaves_the_brief_alone(self):
        r = run(self.root)
        self.assertEqual(r.returncode, 0, r.stderr)
        text = (self.root / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("## My brief", text, "the world's own brief must survive")
        self.assertIn("## Persona", text, "the protocol must arrive")
        self.assertNotIn("PLACEHOLDER", text)

    def test_check_passes_once_synced(self):
        run(self.root)
        self.assertEqual(run(self.root, "--check").returncode, 0)

    def test_check_fails_on_drift(self):
        run(self.root)
        p = self.root / "AGENTS.md"
        p.write_text(p.read_text(encoding="utf-8").replace("## Persona", "## Persona EDITED", 1),
                     encoding="utf-8")
        r = run(self.root, "--check")
        self.assertEqual(r.returncode, 1)
        self.assertIn("DRIFT", r.stderr)

    def test_check_fails_when_the_world_has_no_markers(self):
        """A world whose AGENTS.md lost its region is broken, not 'up to date'."""
        world(self.root, markers=False)
        r = run(self.root, "--check")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("markers", r.stderr)

    def test_the_kit_owns_the_protocol_and_does_not_sync_into_itself(self):
        """With the source under <root>/template/ this IS the kit: nothing to sync, not an error."""
        kit = Path(self.tmp.name) / "kit"
        (kit / "template" / "meta" / "conventions").mkdir(parents=True)
        (kit / "template" / "meta" / "conventions" / "agent-protocol.md").write_text(
            SOURCE.read_text(encoding="utf-8"), encoding="utf-8")
        (kit / "world.config.yaml").write_text("version: 1\n", encoding="utf-8")
        (kit / "AGENTS.md").write_text("# AGENTS.md: the Worldkit\n", encoding="utf-8")
        for args in ((), ("--check",)):
            r = run(kit, *args)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("owns the protocol", r.stdout)

    def test_an_unknown_argument_is_refused(self):
        r = run(self.root, "--wat")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("unknown argument", r.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)

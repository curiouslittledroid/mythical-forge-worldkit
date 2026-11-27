#!/usr/bin/env python3
"""Write the worldkit's agent protocol into this repo's AGENTS.md, between the marked region.

A world's AGENTS.md is two documents: the world's own brief, and the shared agent protocol. The
protocol is the worldkit's (`meta/conventions/agent-protocol.md`), and an agent cannot follow a link out of the
repository, so the text has to be *in* the file. It is therefore duplicated, and this tool is what
keeps the copy honest — `--check` is what CI runs.

Usage:
    python3 tools/sync-agent-protocol.py            # rewrite the region
    python3 tools/sync-agent-protocol.py --check    # exit 1 if the region and the source differ
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

BEGIN = "<!-- BEGIN agent-protocol"
END = "<!-- END agent-protocol -->"
START = "<!-- protocol:start -->"
STOP = "<!-- protocol:end -->"


def find_root() -> Path:
    """The vault: $WORLD_CONFIG's directory, else the repo this script sits in."""
    cfg = os.environ.get("WORLD_CONFIG")
    if cfg:
        return Path(cfg).resolve().parent
    return Path(__file__).resolve().parent.parent


def find_source(root: Path) -> Path:
    """The protocol source, in the kit repo or while the kit is staged inside a world."""
    for rel in ("meta/conventions/agent-protocol.md",
                "template/meta/conventions/agent-protocol.md",
                "tools/docs/agent-protocol.md"):
        p = root / rel
        if p.is_file():
            return p
    sys.exit("sync-agent-protocol: cannot find agent-protocol.md. It is the kit's world-facing "
             "document: a world holds it at meta/conventions/agent-protocol.md, and the kit at "
             "template/meta/conventions/agent-protocol.md.")


def region_of(text: str, *, start: str, stop: str, what: str) -> str:
    """The text between two markers, from the start of the line after the opening one.

    A marker may carry a trailing comment on its own line (the world's BEGIN marker does), so the
    remainder of that line is not part of the region.
    """
    i, j = text.find(start), text.find(stop)
    if i < 0 or j < 0 or j < i:
        sys.exit(f"sync-agent-protocol: {what} is missing its {start!r} / {stop!r} markers")
    nl = text.find("\n", i)
    if nl < 0 or nl > j:
        sys.exit(f"sync-agent-protocol: {what} has its markers on one line")
    return text[nl + 1:j].strip("\n")


def main() -> int:
    check = "--check" in sys.argv[1:]
    unknown = [a for a in sys.argv[1:] if a != "--check"]
    if unknown:
        sys.exit(f"sync-agent-protocol: unknown argument(s): {' '.join(unknown)}")

    root = find_root()
    source = find_source(root)
    want = region_of(source.read_text(encoding="utf-8"), start=START, stop=STOP, what=str(source))
    # The kit owns the protocol, so there is nothing to sync into the KIT's own AGENTS.md: a
    # self-sync would copy a file onto itself and say nothing (D36). The test is the source's path
    # RELATIVE to the vault root, not the names of its parent directories: the kit's own template/
    # holds a copy at exactly the world's path (`meta/conventions/`), and that copy must be synced.
    rel = source.relative_to(root).as_posix()
    if rel == "template/meta/conventions/agent-protocol.md":
        print("sync-agent-protocol: this is the worldkit, which owns the protocol; nothing to sync")
        return 0
    agents = root / "AGENTS.md"
    if not agents.is_file():
        sys.exit(f"sync-agent-protocol: no AGENTS.md at {agents}")
    text = agents.read_text(encoding="utf-8")
    have = region_of(text, start=BEGIN, stop=END, what=str(agents))
    if have == want:
        print(f"sync-agent-protocol: {agents.name} is up to date with {source.name} "
              f"({len(want.splitlines())} lines)")
        return 0

    if check:
        print(f"sync-agent-protocol: DRIFT — {agents} does not match {source}", file=sys.stderr)
        print("  the shared region was edited by hand, or the kit's protocol changed.\n"
              "  Run `python3 tools/sync-agent-protocol.py` and commit the result.", file=sys.stderr)
        return 1

    begin_at = text.index(BEGIN)
    start = text.index("\n", begin_at) + 1                  # keep the marker line as it is
    agents.write_text(text[:start] + want + "\n" + text[text.index(END):], encoding="utf-8")
    print(f"sync-agent-protocol: wrote {len(want.splitlines())} lines into {agents}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

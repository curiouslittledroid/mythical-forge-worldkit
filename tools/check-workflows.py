#!/usr/bin/env python3
"""Check that .github/workflows/*.yml will load: no duplicate keys in any mapping.

A duplicate key in a workflow step is invisible to a lenient YAML parser -- it keeps the last one --
and fatal to GitHub, which refuses the whole file. The workflow then appears in the Actions list named
by its file PATH rather than by its `name:`, and every run of it fails, with no message a reader can
act on. This happened here with two `if:` keys on one step, and the validation used at the time
(`ruby -ryaml`) parsed it happily.

Sequence items are not duplicates: a list of steps repeats `run:` and `with:` at the same indentation
by design, so the stack is cleared at every `- ` item.

    python3 tools/check-workflows.py [path ...]     # defaults to .github/workflows/*.yml
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

KEY = re.compile(r"^(\s*)(?:-\s+)?([A-Za-z_][\w-]*):(?:\s|$)")


def duplicates(text: str) -> list[str]:
    """Every `line:key` where a key repeats inside one mapping."""
    found: list[str] = []
    stack: list[tuple[int, str]] = []  # (indent, key), the open chain of the current mapping
    for lineno, raw in enumerate(text.splitlines(), 1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        m = KEY.match(raw)
        if not m:
            continue
        indent, key = len(m.group(1)), m.group(2)
        if raw.lstrip().startswith("- "):  # a new sequence item: its keys are its own
            while stack and stack[-1][0] >= indent:
                stack.pop()
        while stack and stack[-1][0] > indent:
            stack.pop()
        if stack and stack[-1][0] == indent and stack[-1][1] == key:
            found.append(f"{lineno}: duplicate key '{key}'")
        stack.append((indent, key))
    return found


def main(argv: list[str]) -> int:
    files = [Path(a) for a in argv] or sorted(Path(".github/workflows").glob("*.yml"))
    if not files:
        print("no workflows to check")
        return 0
    bad = 0
    for f in files:
        if not f.exists():
            print(f"{f}: no such file")
            bad += 1
            continue
        for problem in duplicates(f.read_text(encoding="utf-8")):
            print(f"{f}: {problem}")
            bad += 1
    if bad:
        print(f"\n{bad} problem(s). GitHub refuses a workflow with a duplicate key: the file will show")
        print("up in Actions named by its path, and every run of it will fail with no useful message.")
        return 1
    print(f"no duplicate keys in {len(files)} workflow file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

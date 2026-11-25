#!/usr/bin/env python3
"""Compare the atlas feature file against a baseline and print a readable diff.

Default baseline: the committed version (git show HEAD:maps/atlas-features.yaml),
so after running /atlas-refresh you can see exactly what the canon change did.

    python3 tools/atlas_diff.py                     # compare with HEAD
    python3 tools/atlas_diff.py old.yaml            # compare with a file
    python3 tools/atlas_diff.py --check             # exit 1 if anything changed
    python3 tools/atlas_diff.py --section cities     # one section only

Only authored fields are compared. Derived values (grid refs, bearings, travel
days) are computed by the renderer, so they never appear here.
"""

import math
import os
import subprocess
import sys
import tempfile

import atlas_yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CURRENT = os.path.join(ROOT, "maps", "atlas-features.yaml")
REL = "maps/atlas-features.yaml"

KEY_FIELDS = ("name", "type", "frame", "x", "y", "bounds", "points", "status", "source",
              "note", "draw", "population", "origin", "magic_class", "god", "holder")


def baseline_from_git():
    try:
        text = subprocess.run(["git", "show", f"HEAD:{REL}"], cwd=ROOT,
                              capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError:
        return None
    fd, path = tempfile.mkstemp(suffix=".yaml")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


def index(data):
    """(section, key) -> entry, for every list section."""
    out = {}
    for section, entries in data.items():
        if not isinstance(entries, list):
            continue
        for e in entries:
            if not isinstance(e, dict):
                continue
            if "id" in e:
                key = e["id"]
            elif "from" in e and "to" in e:
                key = f"{e['from']}->{e['to']}"
            else:
                key = e.get("name", "?")
            out[(section, key)] = e
    return out


def fmt(v):
    if isinstance(v, list):
        return "[" + ", ".join(str(x) for x in v) + "]"
    return str(v)


def moved(a, b):
    if "x" in a and "x" in b:
        return math.hypot(a["x"] - b["x"], a["y"] - b["y"])
    return None


def main():
    args = [a for a in sys.argv[1:]]
    check = "--check" in args
    args = [a for a in args if a != "--check"]
    only = None
    if "--section" in args:
        i = args.index("--section")
        only = args[i + 1]
        del args[i:i + 2]

    base_path = args[0] if args else baseline_from_git()
    if base_path is None:
        print("no baseline: maps/atlas-features.yaml is not in HEAD yet (first run?).")
        print("Commit it once, or pass an old copy: python3 tools/atlas_diff.py old.yaml")
        return 2

    old = atlas_yaml.load(base_path)
    new = atlas_yaml.load(CURRENT)
    atlas_yaml.validate(new)

    oi, ni = index(old), index(new)
    sections = sorted({s for s, _ in oi} | {s for s, _ in ni})
    changes = 0

    for section in sections:
        if only and section != only:
            continue
        added = sorted(k for (s, k) in ni if s == section and (s, k) not in oi)
        removed = sorted(k for (s, k) in oi if s == section and (s, k) not in ni)
        changed = []
        for (s, k), nb in ni.items():
            if s != section or (s, k) not in oi:
                continue
            ob = oi[(s, k)]
            delta = {f: (ob.get(f), nb.get(f)) for f in KEY_FIELDS
                     if ob.get(f) != nb.get(f)}
            if delta:
                changed.append((k, ob, nb, delta))
        if not (added or removed or changed):
            continue
        print(f"\n## {section}")
        for k in added:
            e = ni[(section, k)]
            where = f"({e['x']:,}, {e['y']:,})" if "x" in e else ""
            print(f"  + {k}  {e.get('name', '')} {where} [{e.get('status', 'canon')}]")
            changes += 1
        for k in removed:
            e = oi[(section, k)]
            print(f"  - {k}  {e.get('name', '')}")
            changes += 1
        for k, ob, nb, delta in changed:
            d = moved(ob, nb)
            mv = f"  (moved {d:,.0f} km)" if d else ""
            print(f"  ~ {k}  {nb.get('name', '')}{mv}")
            for f, (a, b) in delta.items():
                print(f"      {f}: {fmt(a) if a is not None else '—'} → "
                      f"{fmt(b) if b is not None else '—'}")
            changes += 1

    if not changes:
        print("no changes against the baseline")
    else:
        print(f"\n{changes} change(s)")
    return 1 if (check and changes) else 0


if __name__ == "__main__":
    sys.exit(main())

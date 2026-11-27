#!/usr/bin/env python3
"""Check that every engine id named in the world-facing documents is the demo world's.

The kit's documents teach with examples, and exactly two kinds are allowed: an id that exists in the
demo world (`example-world/`, the one sanctioned fixture), and an obvious placeholder
(`npc_<role>`, `evt_example_stage`, `flag_x`, `camp_id`). Anything else is another world's id, which
a reader would copy into a vault where it means nothing — or worse, into a scenario that silently
tests nothing.

It also checks the other shape: **a phrase from the world the kit was extracted from.** That world
is not the demo; its names, its sealed keystones and its thread vocabulary have no place in a
document every world receives. site.md shipped its whole keystone list as "the current list", and
no id check could see it.

    python3 tools/check_doc_examples.py                  # the world-facing documents
    python3 tools/check_doc_examples.py --all            # the documents and the whole machinery
    python3 tools/check_doc_examples.py --verbose        # say what was read
    python3 tools/check_doc_examples.py meta/conventions/site.md

Checked: `meta/conventions/*.md`, `meta/templates/*.md`, `.pi/prompts/*.md` and `tools/README.md` — the documents a world
receives as the kit's rules and note shapes. In the kit those live under `template/`; in a world they
are at the root. A world's own `README.md`, `AGENTS.md` and `ROADMAP.md` are the world's, so they are
not checked: their ids are genuinely that world's.

**Not paths.** `world/plot-web/` is a shape, not an example; a path check would report every folder
reference and teach the reader to ignore it. `campaigns/<campaign>/scenarios/<name>.yaml` is a
placeholder, not a path to resolve.

**`--all`** also scans the machinery — `tools/` and `template/` — for the phrases. The id rule does
not apply there (a test fixture may invent an id), but another world's names must not appear in a
script, a prompt or a default either. The list lives here, once, so the document check and the
machinery check cannot drift apart.

When there is no demo world (a world that deleted it by hand), the check says so and passes rather
than inventing a verdict.

Exit codes: 0 clean, 1 an id the demo world does not have, 2 usage.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The same grammar the linter uses (conventions.md 5.1). A token that matches is an engine id.
ID_RE = re.compile(
    r"\b(?:loc|zone|npc|want|fact|faction|evt|item|mon|mod|camp|quest|room|enc|race|"
    r"hist|fig|god|thread|topic|overlay|mig|rel)_[a-z0-9_]+\b"
)

# Where the documents live, in the kit first, then in a world.
DOC_DIRS = ("template/meta/conventions", "meta/conventions",
            "template/meta/templates", "meta/templates",
            "template/.pi/prompts", ".pi/prompts")
DOC_FILES = ("tools/README.md",)
# The demo world, in the kit's layout or beside a world's tools/.
DEMO_DIRS = ("template/example-world", "example-world")

# Predicates and structural field names that take an id-shaped spelling but are not ids.
NOT_IDS = {"npc_alive", "fact_revealed", "quest_state", "faction_rep_gte"}

# The world the kit was extracted from. These are its identity, its sealed keystones and its thread
# vocabulary: phrases, so no id check can see them. Case-sensitive on purpose — "lineage" is an
# ordinary English word, "Lineage" was a thread. The kit's CI greps the whole machinery for the same
# family (plus `Hollowfall`); this list covers the documents a world is told to read.
SOURCE_WORLD_PHRASES = (
    "Choir water", "Quiet Counsellor", "Gate-born", "gate-born", "reopen the Gate", "Convenor",
    "the Severing", "Long Ebb", "Quiet Trade", "Door-Warden", "First Wheel", "Ketheri",
    "Far Reach", "the-quay-boy", "dustport-pilot", "Lineage",
    "Ennis", "Sorn", "Rusk", "Quillon", "Verran", "Halvard", "Dagna",
    "Hollowfall", "hollowfall", "world_hollowfall",
)


def is_placeholder(token: str) -> bool:
    """A spelling a reader can tell is not a real id."""
    return ("example" in token
            or token.endswith("_id")
            or token.endswith("_")          # a glob prefix: `world/events/evt_ferry_*.yaml`
            or re.search(r"(^|_)x$", token) is not None)


def demo_world() -> Path | None:
    for rel in DEMO_DIRS:
        path = ROOT / rel
        if (path / "world.config.yaml").is_file():
            return path
    return None


def documents() -> list[Path]:
    docs: list[Path] = []
    for rel in DOC_DIRS:
        base = ROOT / rel
        if base.is_dir():
            docs.extend(sorted(base.glob("*.md")))
    for rel in DOC_FILES:
        path = ROOT / rel
        if path.is_file():
            docs.append(path)
    return docs


def demo_ids(demo: Path) -> set[str]:
    """Every id-shaped token the demo world uses anywhere: frontmatter, blocks, prose."""
    known: set[str] = set()
    for path in demo.rglob("*"):
        if path.is_file() and path.suffix in {".md", ".yaml", ".yml"}:
            known.update(ID_RE.findall(path.read_text(encoding="utf-8", errors="ignore")))
    return known


def machinery(root: Path = None) -> list[Path]:
    """Every source file the kit ships, for the `--all` phrase sweep.

    The checker and its test are the list's home, so they are the one place the phrases belong.
    """
    root = root or ROOT
    out: list[Path] = []
    for base in ("tools", "template"):
        for path in (root / base).rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".sh", ".mjs", ".md", ".yaml", ".yml"}:
                continue
            if "__pycache__" in path.parts or "node_modules" in path.parts:
                continue
            if path.name in {"check_doc_examples.py", "test_check_doc_examples.py"}:
                continue
            out.append(path)
    return sorted(out)


def find_leaks(paths: list[Path], known: set[str], check_ids: bool = True) -> list[tuple[str, int, str]]:
    """(file, line, token) for every id or source-world phrase that should not appear."""
    leaks: list[tuple[str, int, str]] = []
    for path in paths:
        try:
            rel = path.relative_to(ROOT).as_posix()
        except ValueError:
            rel = str(path)
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            seen: set[str] = set()
            if check_ids:
                for token in ID_RE.findall(line):
                    if token in known or token in NOT_IDS or is_placeholder(token):
                        continue
                    seen.add(token)
            for phrase in SOURCE_WORLD_PHRASES:
                if phrase in line:
                    seen.add(phrase)
            leaks.extend((rel, number, token) for token in sorted(seen))
    return leaks


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Every id in the world-facing docs is the demo world's.")
    ap.add_argument("paths", nargs="*", type=Path,
                    help="check only these documents (default: all of them)")
    ap.add_argument("--all", action="store_true",
                    help="also scan tools/ and template/ for the source world's phrases")
    ap.add_argument("--verbose", action="store_true", help="say what was read")
    args = ap.parse_args(argv)

    demo = demo_world()
    if demo is None:
        print("check_doc_examples: no demo world (example-world/); nothing to check against")
        return 0
    paths = args.paths or documents()
    if not paths:
        print("check_doc_examples: no world-facing documents found")
        return 0
    known = demo_ids(demo)
    leaks = find_leaks(paths, known)
    if args.all:
        already = {path.resolve() for path in paths}
        extra = [path for path in machinery() if path.resolve() not in already]
        leaks += find_leaks(extra, known, check_ids=False)
        if args.verbose:
            print(f"check_doc_examples: also swept {len(extra)} machinery file(s) for phrases")
    if args.verbose:
        print(f"check_doc_examples: {len(paths)} document(s) against {len(known)} id(s) "
              f"in {demo.relative_to(ROOT).as_posix()}")
    if leaks:
        for rel, number, token in leaks:
            print(f"{rel}:{number}: `{token}` is not the demo world's")
        print(f"\n{len(leaks)} finding(s) in {len({rel for rel, _, _ in leaks})} document(s). "
              "Use the demo world's id, or write a placeholder (`npc_<role>`, `evt_example_stage`); "
              "a phrase from the source world is never the answer.")
        return 1
    if args.verbose:
        print("every id named is the demo world's or a placeholder, and no source-world phrase appears")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

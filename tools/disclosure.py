#!/usr/bin/env python3
"""Effective disclosure class of every lore section in the vault (conventions section 7).

    python3 tools/disclosure.py              # counts by note kind and by how each section was classed
    python3 tools/disclosure.py --list       # also list every UNREVIEWED section
    python3 tools/disclosure.py --kind NPC   # limit to one note kind
    python3 tools/disclosure.py --check      # exit 1 if any section is unreviewed (pre-commit)

A section is an H2 heading and everything under it (the text before the first H2 is the
"Summary" section). Its class comes from the first rule that applies:

  marked      a `**Disclosure:** <class>` line directly under the heading
  secrets     the heading is `## Secrets`                        -> earned
  layered     a HISTORY_EVENT section holding **Official:** / **Myth:** / **Rival:**
              (open) and **Truth:** (earned) lines; split per line at export. The note's
              frontmatter official / myth / rival are `open` chunks too.
  note        the note's frontmatter `disclosure:`
  notlore     Hooks, Author Notes, Open questions, Links, Engine, a `Run it` scene guide, a `Named members` roster (it feeds the group tiers, conventions 9.5), or a
              THREAD / CAMPAIGN / MODULE / OVERLAY / INDEX note: design material, not lore
              (not in the corpus). Only `world/` is surveyed; `principles/`, `campaigns/`
              and `meta/` are design, not lore. GM-side plot-thread links belong under
              `## Hooks`, which is the one heading for them; engine and authoring citations
              (register ids, `§` refs, `Step N`) belong under `## Author Notes`, so they stay
              in the note for the author without reaching a player (conventions section 10).
  unreviewed  nothing above applies. It FAILS CLOSED: treated as `earned` until someone
              decides. Step 2d is done when this count is zero.

Line-level exceptions the export (Step 14) must also apply: a `**Want:**` line is `earned` with the
NPC itself as its only audience (it always reaches that NPC's agent); layer lines in a history
event split as above.

The transformer (Step 14) should port `classify`, not re-derive it.
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lint  # noqa: E402

NOT_LORE_KINDS = {"THREAD", "CAMPAIGN", "MODULE", "OVERLAY", "INDEX"}
NOT_LORE_HEADINGS = {"hooks", "author notes", "open questions", "links", "engine"}
NOT_LORE_PREFIXES = ("run it", "named members")  # GM scene guidance; the roster that feeds group tiers (conventions 9.5)
LAYER_RE = re.compile(r"\*\*(Official|Myth|Rival|Truth)\b[^*:]*:\*\*")  # also a legacy **Truth (decided):**
LORE_ROOT = "world/"  # lore lives here; principles/, campaigns/ and meta/ are design, not lore
# The engine flag registry is not lore. Its path comes from the world config by note id, so a
# world that moves the note does not silently start publishing it.


def not_lore_files() -> set[str]:
    cfg = lint.world_config()
    path = cfg.path_of("flags") if cfg else None
    return {path.relative_to(cfg.root).as_posix()} if path else set()
MARK_RE = re.compile(r"^\*\*Disclosure:\*\*\s*([A-Za-z]*)")
SOURCES = ["marked", "secrets", "layered", "note", "notlore", "unreviewed"]


def sections(note: lint.Note):
    """Yield (heading, first_line_number, lines) for the Summary and each H2 section."""
    # `inline=False`: inline code is prose here. Blanking it made the export publish
    # "`` `read twice` ``" as "****", and dropped the words inside any code span (Step 16).
    lines = lint.strip_code(note.text, inline=False).split("\n")
    head, start, buf = "Summary", note.body_start + 1, []
    for i, ln in enumerate(lines[note.body_start :], note.body_start + 1):
        if ln.startswith("## "):
            yield head, start, buf
            head, start, buf = ln[3:].strip(), i, []
        else:
            buf.append(ln)
    yield head, start, buf


def classify(note: lint.Note, heading: str, lines: list[str]) -> tuple[str, str]:
    """Return (source, class). The class is `open`, `earned`, `sealed` or `-` (not lore)."""
    kind = lint.unquote(note.fm.get("kind", ""))
    first = next((ln for ln in lines if ln.strip()), "")
    m = MARK_RE.match(first)
    if m and m.group(1).lower() in lint.DISCLOSURE:
        return "marked", m.group(1).lower()
    if kind in NOT_LORE_KINDS or heading.lower() in NOT_LORE_HEADINGS or heading.lower().startswith(NOT_LORE_PREFIXES):
        return "notlore", "-"
    if heading.lower() == "secrets":
        return "secrets", "earned"
    if kind == "HISTORY_EVENT" and any(LAYER_RE.search(ln) for ln in lines):
        return "layered", "mixed"
    note_class = lint.unquote(note.fm.get("disclosure", ""))
    if note_class in lint.DISCLOSURE:
        return "note", note_class
    return "unreviewed", "earned"


def survey(kind_filter: str | None = None):
    out = []
    for note in lint.load_notes():
        if note.is_doc or not note.has_fm or not note.rel.startswith(LORE_ROOT) \
                or note.rel in not_lore_files():
            continue
        kind = lint.unquote(note.fm.get("kind", ""))
        if kind_filter and kind != kind_filter:
            continue
        for heading, line, lines in sections(note):
            if not any(ln.strip() for ln in lines):
                continue
            source, cls = classify(note, heading, lines)
            out.append((kind, note.rel, line, heading, source, cls))
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Report the effective disclosure class of every lore section.")
    ap.add_argument("--list", action="store_true", help="list every unreviewed section")
    ap.add_argument("--kind", help="limit to one note kind, e.g. NPC")
    ap.add_argument("--check", action="store_true", help="exit 1 if any lore section is unreviewed (run before a commit)")
    args = ap.parse_args(argv)
    rows = survey(args.kind)

    by_kind: dict[str, Counter] = defaultdict(Counter)
    for kind, _, _, _, source, _ in rows:
        by_kind[kind][source] += 1
    print(f"{'kind':<14}" + "".join(f"{s:>11}" for s in SOURCES) + f"{'total':>8}")
    total = Counter()
    for kind in sorted(by_kind, key=lambda k: -sum(by_kind[k].values())):
        c = by_kind[kind]
        total.update(c)
        print(f"{kind:<14}" + "".join(f"{c[s]:>11}" for s in SOURCES) + f"{sum(c.values()):>8}")
    print(f"{'ALL':<14}" + "".join(f"{total[s]:>11}" for s in SOURCES) + f"{sum(total.values()):>8}")

    if args.list:
        print("\nUnreviewed sections (fail closed as earned):")
        for kind, rel, line, heading, source, _ in rows:
            if source == "unreviewed":
                print(f"  {rel}:{line}  [{kind}] {heading}")
    if args.check and any(r[4] == "unreviewed" for r in rows):
        print("\nUnreviewed lore sections remain: classify them (conventions section 7).", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

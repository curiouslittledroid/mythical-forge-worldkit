#!/usr/bin/env python3
"""Check a `## Testimony` section against its teller's voice sheet (Step 16).

    python3 tools/voice_lint.py              # report every account
    python3 tools/voice_lint.py --list       # also list the sheets it parsed

**What it is for.** Testimony is written in a named teller's voice, and four voices drift into
one unless something checks them. Two of the six parts of a voice sheet are mechanical:

- **Never says** — a short forbidden vocabulary. "Sabel Cray" is a Dustport wrecker who cannot
  read; a sentence of hers containing *resonant* or *provenance* is the author's voice, not hers.
- **Range** — the places the teller has been. A place link outside it is a teller describing
  somewhere they have never stood, which is the likeliest way a good account goes wrong.

The other four (blind spots, wrong about, signature, samples) are for the reader, not the tool.

**Where the sheets live.** `## Author Notes` of [[the-readers-book]] — authoring material that
never publishes. One sheet per teller: a `**Name** — …` line, then a table with a `**Range**` row
and a `**Never says**` row, which is what this reads.

Exit code 1 when an account breaks a sheet (like `tools/lint.py`); warnings do not fail.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import disclosure  # noqa: E402
import lint  # noqa: E402
import site_export  # noqa: E402  (one rule for reading an entry heading, shared not copied)

TESTIMONY_HEADING = "testimony"


def default_book() -> str:
    """The testimony book's path, from the world config (`vault.notes.testimony_book`).

    A world with no testimony device simply never runs this tool: the path is required only by
    the `--book` default, so an unset config fails here and nowhere else.
    """
    cfg = lint.world_config()
    path = cfg.path_of("testimony_book") if cfg else None
    if path is None:
        raise SystemExit("no testimony book: set vault.notes.testimony_book in world.config.yaml "
                         "to the id of the note holding the voice sheets")
    return path.relative_to(cfg.root).as_posix()
SHEET_HEADING = "author notes"
PLACE_KINDS = {"SETTLEMENT", "PLACE", "REGION"}

PERSONA_RE = re.compile(r"^\*\*(?P<name>[^*]+?)\*\*\s+[—-]\s+")
ROW_RE = re.compile(r"^\|\s*\*\*(?P<key>Range|Never says)\*\*\s*\|\s*(?P<value>.*?)\s*\|\s*$")
# A place is named either as a wikilink (the vault's habit) or as a site path (a mistake the
# tool should still catch: `/places/highwell/`). Both reduce to a note slug.
LINK_RE = re.compile(r"\[\[([^\[\]|]+)(?:\|[^\[\]]*)?\]\]|\((?:/[a-z-]+)+/([a-z0-9-]+)/?\)")
MARKER_RE = re.compile(r"^\*\*(Disclosure|Reveal when)\b[^*]*:\*\*")
NO_SHEET_NOTE = "(no sheet)"


def slug_of(target: str) -> str:
    """`the-heartland` from `[[the-heartland|the Heartland]]`; a path segment if one is given."""
    return Path(target.strip().replace("\\", "")).name.removesuffix(".md")


def targets_of(text: str) -> list[str]:
    """Every place a passage names, as note slugs, in order of first appearance.

    The backslash-pipe is the table escape for a pipe inside a wikilink (conventions, and
    site.md 2.2), so it is unescaped first: a range row is a table row, and every wikilink in one
    is escaped.
    """
    out = []
    for wikilink, path in LINK_RE.findall(text.replace("\\|", "|")):
        slug = slug_of(wikilink or path)
        if slug:
            out.append(slug)
    return out


def split_terms(cell: str) -> list[str]:
    """`fathom, seabed — he quotes jargon` -> ['fathom', 'seabed']."""
    head = re.split(r"\s+[—–-]{1,2}\s+", cell, maxsplit=1)[0]
    terms = []
    for term in re.split(r"[,;]", head):
        term = term.strip().strip('.').strip()
        if len(term) > 2 and not term.startswith('"'):
            terms.append(term)
    return terms


def parse_sheets(text: str) -> dict[str, dict]:
    """{teller: {range: set[slug], never: [term]}} from the book's `## Author Notes`."""
    sheets: dict[str, dict] = {}
    in_notes = False
    current: dict | None = None
    for line in text.split("\n"):
        if line.startswith("## "):
            in_notes = line[3:].strip().lower() == SHEET_HEADING
            current = None
            continue
        if not in_notes:
            continue
        m = PERSONA_RE.match(line)
        if m:
            name = m.group("name").strip()
            current = sheets.setdefault(name, {"range": set(), "never": []})
            continue
        row = ROW_RE.match(line)
        if row and current is not None:
            value = row.group("value")
            if row.group("key") == "Range":
                current["range"] |= set(targets_of(value))
            else:
                current["never"] = split_terms(value)
    return sheets


def testimony_of(note: lint.Note) -> str:
    """The account's text, without the section heading or its disclosure marker."""
    for heading, _, lines in disclosure.sections(note):
        if heading.strip().lower() != TESTIMONY_HEADING:
            continue
        kept = [ln for ln in lines if ln.strip() and not MARKER_RE.match(ln.strip())]
        return "\n".join(kept)
    return ""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--book", default=None,
                    help="the note holding the voice sheets (default: the config's testimony_book)")
    ap.add_argument("--list", action="store_true", help="print the parsed sheets")
    args = ap.parse_args(argv)

    # The config's `testimony_book` unless `--book` overrode it. This line was missing: the
    # default was documented, defined in default_book() and never called, so every run without an
    # explicit --book failed with "None not found" - a check nobody could have been passing.
    book_arg = args.book or default_book()
    notes = {n.rel: n for n in lint.load_notes()}
    by_slug = {slug_of(n.rel): n for n in notes.values()}
    book = notes.get(book_arg)
    if book is None:
        print(f"voice_lint: {book_arg} not found. The voice sheets have no home.")
        return 1

    sheets = parse_sheets(book.text)
    if not sheets:
        print(f"voice_lint: no voice sheets under `## Author Notes` in {book_arg}.")
        return 1

    if args.list:
        for name, sheet in sheets.items():
            print(f"{name}: {len(sheet['range'])} places in range; "
                  f"never says {len(sheet['never'])} terms")
        print()

    errors: list[str] = []
    warnings: list[str] = []
    accounts = 0

    for note in notes.values():
        account = testimony_of(note)
        if not account:
            continue
        accounts += 1
        first = next((ln for ln in account.split("\n") if ln.strip()), "")
        teller, taken = site_export.entry_ident(first)
        sheet = sheets.get(teller)
        print(f"\n{note.rel}  —  {teller or NO_SHEET_NOTE}")
        if sheet is None:
            warnings.append(f"{note.rel}: no voice sheet for teller {teller!r}")
            print("  WARN  VL001  no voice sheet for this teller")
            continue

        low = account.lower()
        faults = 0
        for term in sheet["never"]:
            hit = re.search(r"(?<![\w-])" + re.escape(term.lower()) + r"(?![\w-])", low)
            if hit:
                errors.append(f"{note.rel}: {teller} would never say {term!r}")
                print(f"  ERROR VL002  {teller} would never say {term!r}")
                faults += 1

        off = []
        for target in dict.fromkeys(targets_of(account)):
            target_note = by_slug.get(target)
            if target_note is None:
                continue
            kind = lint.unquote(target_note.fm.get("kind", ""))
            if kind in PLACE_KINDS and target not in sheet["range"]:
                off.append(target)
        for target in off:
            errors.append(f"{note.rel}: {teller} has not been to {target!r}")
            print(f"  ERROR VL003  {teller} has no business in {target!r} — add it to her range, "
                  f"or take the place out")
            faults += 1
        if not faults:
            print("  ok")

    print()
    print(f"{accounts} account(s), {len(errors)} error(s), {len(warnings)} warning(s).")
    for w in warnings:
        print(f"  warn: {w}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Check every section citation against the document it names.

A vault cites its rules by number — "the kit's `docs/conventions.md` §9.6", "the register's
corrections table (§14)" — and nothing else in the toolchain notices when one of those numbers
stops being true. A document that renumbers silently breaks every citation of it, in both
repositories, and the broken ones read exactly like the correct ones.

What this checks:

1. **The document is named.** A citation inside a paragraph that names a document checks against
   that document; the nearest reference *before* the number wins, which is why a citation should
   name its document in the same sentence.
2. **The document numbers its sections.** Asking for §4 of a document with named sections is an
   error even if §4 would have been plausible.
3. **The number exists** as a heading, or as a numbered table row (`| 14.32 |`), or the cited
   number is a prefix of one (§9 is satisfied by §9.1).
4. **The path exists.** `docs/atlas.md` that no longer exists is an error, not a silent pass.

Deliberately not checked: citations of the platform's specs (`Design 23 §1.1`), paths outside the
repository, and **historical** citations — "formerly `docs/site.md` §3.4" describes where something
used to be, so the rule is to write it with a word that says so. A line containing the words
`citations: ignore` opts out — on a line, for an example of a bad citation in prose, or in the
first five lines of a file, for a test whose fixtures cite documents that exist only inside it.

Usage:
  python3 tools/check_citations.py            # the whole repo
  python3 tools/check_citations.py docs/      # only files under one path

Exit codes: 0 clean, 1 mismatches (errors), 2 usage.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Directories that are not the vault: build output, vendored kit prose that is checked where it
# lives (the kit), and the template's mirrored example world.
SKIP_DIRS = {".git", ".obsidian", ".trash", "node_modules", "site", "example-world",
             "__pycache__", ".astro", "dist"}
SCAN_SUFFIXES = {".md", ".py", ".sh", ".mjs", ".yaml", ".yml"}

# The kit's own documents, as prose names them. A world cites the vendored copies by the same
# names, so these aliases work in both repositories.
ALIASES = {
    "conventions": "docs/conventions.md",
    "engine-capability-register": "docs/engine-capability-register.md",
    "capability register": "docs/engine-capability-register.md",
    "campaign-authoring-guide": "docs/campaign-authoring-guide.md",
    "thread-pattern": "docs/thread-pattern.md",
    "tag-vocabulary": "docs/tag-vocabulary.md",
    "agent-protocol": "docs/agent-protocol.md",
}

# A line can opt out: fixture text in a test, or an example of a BAD citation in documentation.
# Write it in a comment or in the surrounding prose of a markdown file.
NOCHECK = "citations: ignore"

CITE = re.compile(r"§\s*(\d+(?:\.\d+)*)|[Ss]ections?\s+(\d+(?:\.\d+)*)")
# A document reference: a path-like token ending in .md, optionally in backticks.
DOCREF = re.compile(r"`([^`]*?\.md)`|([\w./-]+\.md)")
# "was", "formerly", "renumbered": a citation of where something USED to live.
HISTORICAL = re.compile(r"\b(was|were|formerly|previously|used to be|used to live|renumbered)\b",
                        re.IGNORECASE)
EXTERNAL = re.compile(r"Design\s*\d|SRD|\bdesign doc", re.IGNORECASE)


class Doc:
    """A markdown document, with the numbers it can be cited by."""

    def __init__(self, path: Path, rel: str):
        self.path, self.rel = path, rel
        self.headings: set[str] = set()
        self.rows: set[str] = set()
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            text = ""
        for line in text.split("\n"):
            m = re.match(r"^#{1,6}\s+(\d+(?:\.\d+)*)", line)
            if m:
                self.headings.add(m.group(1))
                continue
            m = re.match(r"^\|\s*\*{0,2}(\d+(?:\.\d+)*)\*{0,2}\s*\|", line)
            if m:
                self.rows.add(m.group(1))

    @property
    def numbers(self) -> bool:
        return bool(self.headings or self.rows)

    def has(self, number: str) -> bool:
        """Is `number` cited exactly, or as a prefix of a longer number (§9 for §9.4)?"""
        if number in self.headings or number in self.rows:
            return True
        return any(h.startswith(number + ".") for h in self.headings | self.rows)


def scan_docs(root: Path) -> dict[str, Doc]:
    """Every document in the repository, by relative path. All of them, numbered or not: a
    citation of a document that numbers nothing must fail rather than go unchecked."""
    docs: dict[str, Doc] = {}
    for path in sorted(root.rglob("*.md")):
        rel = path.relative_to(root).as_posix()
        if any(part in SKIP_DIRS for part in rel.split("/")[:-1]):
            continue
        docs[rel] = Doc(path, rel)
    return docs


def candidate_docs(token: str, docs: dict[str, Doc]) -> list[Doc]:
    """Documents a reference could mean: as written, as a suffix of a path, or by basename."""
    token = token.strip().lstrip("./")
    found = []
    if token in docs:
        found.append(docs[token])
    if not found:
        for rel, doc in docs.items():
            if rel.endswith("/" + token):
                found.append(doc)
    if not found:
        base = token.split("/")[-1]
        found = [doc for rel, doc in docs.items() if rel.split("/")[-1] == base]
    if not found:
        for name, rel in ALIASES.items():          # a prose name for a kit document
            if token == name or token.endswith("/" + name):
                if rel in docs:
                    found.append(docs[rel])
                else:
                    for r, doc in docs.items():
                        if r.endswith("/" + rel):
                            found.append(doc)
    return found


def context(text: str, pos: int) -> str:
    """The stretch of text a citation is read in: from the enclosing heading down to the citation.

    A citation often names its document a few lines earlier -- in the sentence introducing a list,
    say -- so the unit is the whole section rather than the paragraph. The nearest reference BEFORE
    the number still wins, so a wider window only helps citations that name their document earlier.
    """
    head = text.rfind("\n#", 0, pos)
    start = 0 if head == -1 else head + 1
    return text[start:pos]


VAULT_DIRS = ("world/", "campaigns/", "principles/", "maps/", "meta/")


def references(ctx: str, docs: dict[str, Doc]) -> list[tuple[int, list[Doc], str]]:
    """(offset, documents, as-written) for every document reference in the context.

    Two forms: a path-like token (`docs/site.md`, `tools/docs/testimony.md`) and a PROSE name for a
    kit document ("conventions", "the guide"). A reference to a note in this vault -- `world/places/a.md`
    -- is not a reference to a document, and is ignored so it cannot shadow one.
    """
    found: list[tuple[int, list[Doc], str]] = []
    for m in DOCREF.finditer(ctx):
        token = (m.group(1) or m.group(2)).strip()
        if token.startswith("http") or token.startswith("~"):
            continue
        candidates = candidate_docs(token, docs)
        if token.startswith(VAULT_DIRS) and "/docs/" not in token:
            # A note, not a kit document: citable by number only if it actually numbers sections.
            # Kept even when empty, so it can still say "a document, but not one of this repository's"
            # -- a prompt the kit ships cites the world's atlas register, which lives in a world.
            candidates = [d for d in candidates if d.numbers]
        found.append((m.end(), candidates, token))
    for m in re.finditer(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]", ctx):
        token = m.group(1).strip()
        # A wikilink can only mean a NOTE, and only a note that numbers its sections can be cited
        # by number. The kit's documents are never wikilinked (the kit is not a vault).
        candidates = [d for d in candidate_docs(token, docs) + candidate_docs(token + ".md", docs)
                      if d.numbers and not d.rel.startswith(("docs/", "tools/docs/"))]
        found.append((m.end(), candidates, f"[[{token}]]"))
    for name in ALIASES:
        for m in re.finditer(rf"(?<![\w-]){re.escape(name)}(?![\w-])", ctx):
            found.append((m.end(), candidate_docs(name, docs), name))
    return sorted(found)


def check_file(path: Path, rel: str, docs: dict[str, Doc]) -> list[tuple[int, str, str]]:
    """(line number, level, message) for every citation in one file."""
    issues: list[tuple[int, str, str]] = []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return issues
    lines = text.split("\n")
    if any(NOCHECK in head for head in lines[:5]):
        return issues                            # the whole file opts out: a fixture world
    offsets, running = [], 0
    for line in lines:
        offsets.append(running)
        running += len(line) + 1

    for m in CITE.finditer(text):
        number = m.group(1) or m.group(2)
        span = text[m.start():m.start() + len(m.group(0)) + 8]
        if re.match(r"^\s*[–—-]\s*\d", span[len(m.group(0)):]) or \
           re.search(r"\d\s*[–—-]\s*$", text[max(0, m.start() - 4):m.start()]):
            continue                                     # a range (1–24), not a citation
        line_no = next((i for i, off in enumerate(offsets) if off > m.start()), len(lines))
        line = lines[line_no - 1] if 0 < line_no <= len(lines) else ""
        if NOCHECK in line:
            continue
        ctx = context(text, m.start())
        ctx_offset = len(ctx)
        # The nearest reference BEFORE the number wins, but a token that matches no document (a
        # fixture path in a test, say) must not stop the search: fall back to the previous one.
        before = [r for r in references(ctx, docs) if r[0] <= ctx_offset]
        refs = [r for r in before if r[1]]
        if refs:
            refs = [refs[-1]]
        if EXTERNAL.search(ctx):
            continue
        if not refs:
            # No document named at all: the file's own numbering (a ROADMAP cites its own §0.1).
            if before:
                _, _, token = before[-1]
                if not (token.startswith("docs/") or token.startswith("tools/docs/")):
                    continue                          # not a document of ours; checked where it lives
                issues.append((line_no, "error", f"§{number}: no document matches `{token}`"))
                continue
            own = docs.get(rel)
            if own and not own.has(number):
                issues.append((line_no, "error",
                               f"§{number} is not a section of this file ({rel}). "
                               f"Name the document it belongs to in the same sentence."))
            continue
        off, docs_here, token = refs[-1]
        ref_start = max(0, ctx.rfind(token, 0, off))
        between = ctx[max(0, ref_start - 40):ctx_offset]
        if HISTORICAL.search(between):
            continue
        if "Design" in token or "/Users/" in token:
            continue
        if not docs_here:
            if token.startswith(VAULT_DIRS) or token in ALIASES:
                continue                 # a world's own document: checked in the world, not here
            issues.append((line_no, "error", f"§{number}: no document matches `{token}`"))
            continue
        if len(docs_here) > 1:
            issues.append((line_no, "warning",
                           f"§{number} is ambiguous: `{token}` matches "
                           f"{', '.join(d.rel for d in docs_here)}. Cite the path."))
            if not any(d.has(number) for d in docs_here):
                issues.append((line_no, "error", f"§{number} is in none of them"))
            continue
        doc = docs_here[-1]
        if not doc.numbers:
            issues.append((line_no, "error",
                           f"§{number} cites `{doc.rel}`, which numbers nothing. "
                           f"Cite the section by name."))
        elif not doc.has(number):
            have = sorted(doc.headings | doc.rows)
            shown = ", ".join(have[:12]) + ("…" if len(have) > 12 else "")
            issues.append((line_no, "error",
                           f"§{number} is not in `{doc.rel}`. It numbers: {shown or '(nothing)'}"))
    return issues


def main(argv: list[str]) -> int:
    target = ROOT
    if len(argv) > 1:
        if len(argv) > 2 or argv[1] in {"-h", "--help"}:
            print(__doc__)
            return 2 if argv[1] not in {"-h", "--help"} else 0
        target = (ROOT / argv[1]).resolve()
    docs = scan_docs(ROOT)
    errors = warnings = checked = 0
    for path in sorted(target.rglob("*")):
        if not path.is_file() or path.suffix not in SCAN_SUFFIXES:
            continue
        rel = path.relative_to(ROOT).as_posix()
        if any(part in SKIP_DIRS for part in rel.split("/")[:-1]):
            continue
        issues = check_file(path, rel, docs)
        for line_no, level, message in issues:
            checked += 1
            if level == "error":
                errors += 1
            else:
                warnings += 1
            print(f"{rel}:{line_no}: {level.upper()}: {message}")
    print(f"{checked} citation problem(s): {errors} error(s), {warnings} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

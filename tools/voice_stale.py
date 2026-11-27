#!/usr/bin/env python3
"""Report notes whose voice section is older than the canon around it (Step 16).

    python3 tools/voice_stale.py                 # every `## Testimony` section
    python3 tools/voice_stale.py --heading Folklore
    python3 tools/voice_stale.py --strict        # exit 1 if anything is stale
    python3 tools/voice_stale.py --all           # include notes with no voice section

**What it is for.** A voice section ([[the-readers-book|testimony]], or the older `## Folklore`)
speaks in the world's voice about facts the note owns. Canon moves; the voice does not follow on
its own. This is the nag that says "read these before you publish", so that keeping the prose
true is a list someone works through rather than a thing someone remembers.

**An account may be old on purpose.** The Reader's book spans seventy-five years, so most of its
accounts describe a moment, not the present. Three verdicts, not two:

| Verdict | Rule |
|---|---|
| `undated` | a testimony whose transmission line carries no `CY <n>`: it silently claims to be current, and is reported |
| `STALE` | taken within `RECENT_YEARS` of the present, and the canon around it changed afterwards |
| `old` | taken before that window: expected to be out of date, so it is **not** nagged about |
| `ok` | recent, and nothing around it has changed since |

An account that is old *and* wrong is in fiction. A recent account that is wrong is a defect.
The present year is read from [[calendar|the calendar]], which owns it; it is not restated here.

**How it works.** Git already records which line changed when, so nothing needs stamping into a
note (and no derived value is authored, per `AGENTS.md`). `git blame --line-porcelain` gives every
line a commit and an author time. The note is split into sections with `disclosure.sections` — the
same parser the linter and the exporter use — and two timestamps are compared:

    voice = the newest line inside the voice section
    body  = the newest line anywhere else in the note (frontmatter excluded)

The note is **stale** when the body is newer than the voice: the canon changed and the voice did
not. Simultaneous edits read as fine, because they were written together.

**Report only, never a gate.** Whether the voice *needs* changing is a judgement: a Folklore about
what commoners believe often survives a refinement to the Details untouched. `--strict` exists for
CI experiments; the session workflow runs it plain.

**Known limits** (all documented in the kit's `meta/conventions/testimony.md` section 3.5):
- an uncommitted edit is invisible to blame, so a dirty note is reported as `unknown`, never `ok`;
- a squash-merge or a whole-file rewrite makes everything simultaneous: that causes **misses**,
  never false alarms;
- author time is used, not committer time, because a rebase preserves it;
- nothing is checked outside a git checkout, including the test fixtures.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import disclosure  # noqa: E402
import lint  # noqa: E402

DEFAULT_HEADING = "Testimony"
RECENT_YEARS = 5  # an account taken within this many years of the present must still be true


def calendar_rel() -> str | None:
    """The calendar note's path, from the world config, or None when it names no note."""
    cfg = lint.world_config()
    path = cfg.path_of("calendar") if cfg else None
    return path.relative_to(cfg.root).as_posix() if path else None


def chronology() -> dict:
    """The world's date prefix and present year, from the `chronology` block.

    The block is the authority (D18). The note's prose still says what the date *means*; the block
    carries the two values a tool needs, so nothing has to be scraped out of a sentence.
    """
    cfg = lint.world_config()
    block = cfg.block("calendar") if cfg else None
    return dict(block) if isinstance(block, dict) else {}


def taken_re() -> "re.Pattern[str]":
    return re.compile(rf"\b{re.escape(str(chronology().get('date_prefix', 'CY')))}\s*(\d{{2,4}})\b")


def repo_root() -> Path | None:
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=lint.ROOT,
                             capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return Path(out.stdout.strip())


def blame_times(root: Path, rel: str) -> dict[int, int]:
    """{line number: author time} for one file, from `git blame --line-porcelain`."""
    out = subprocess.run(["git", "blame", "--line-porcelain", "--", rel], cwd=root,
                         capture_output=True, text=True)
    if out.returncode != 0:
        return {}
    times, current = {}, None
    for line in out.stdout.split("\n"):
        header = re.match(r"^[0-9a-f]{40} \d+ (\d+)", line)
        if header:
            current = int(header.group(1))
        elif line.startswith("author-time ") and current:
            times[current] = int(line.split()[1])
    return times


def is_dirty(root: Path, rel: str) -> bool:
    out = subprocess.run(["git", "status", "--porcelain", "--", rel], cwd=root,
                         capture_output=True, text=True)
    return bool(out.stdout.strip())


def section_lines(note: lint.Note, heading: str) -> tuple[set[int], set[int]]:
    """(voice line numbers, body line numbers) for one note."""
    voice: set[int] = set()
    body: set[int] = set()
    for head, start, lines in disclosure.sections(note):
        # A section runs from its heading line (or, for the Summary, its first line) for as many
        # lines as it holds. `disclosure.sections` gives the heading's number in `start`.
        first = start if head != "Summary" else start
        span = set(range(first, first + max(len(lines), 1)))
        if head.strip().lower() == heading.strip().lower():
            voice |= span
        else:
            body |= span
    return voice, body


def present_year(notes: list[lint.Note]) -> tuple[int, str]:
    """The present year as `(year, source)`, or `(0, why)` when the world does not state one.

    Zero means "unknown", never "year zero": the caller must skip the comparison rather than
    guess, because a guessed present year invents staleness verdicts.
    """
    rel = calendar_rel()
    if rel is None:
        return 0, "vault.notes.calendar names no note in world.config.yaml"
    year = chronology().get("present")
    if not isinstance(year, int):
        return 0, f"no `chronology` block in {rel}"
    return year, rel


def taken_year(note: lint.Note, heading: str) -> int:
    """The `CY <n>` in a voice section's transmission line, or 0 when it has none."""
    for head, _, lines in disclosure.sections(note):
        if head.strip().lower() != heading.strip().lower():
            continue
        first = next((ln for ln in lines if ln.strip() and not ln.startswith("**Disclosure")), "")
        m = taken_re().search(first)
        return int(m.group(1)) if m else 0
    return 0


def newest(times: dict[int, int], lines: set[int]) -> int:
    return max((times[n] for n in lines if n in times), default=0)


def when(stamp: int) -> str:
    if not stamp:
        return "-"
    return dt.datetime.fromtimestamp(stamp, dt.UTC).strftime("%Y-%m-%d")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--heading", default=DEFAULT_HEADING,
                    help=f"the voice section to check (default {DEFAULT_HEADING!r})")
    ap.add_argument("--strict", action="store_true", help="exit 1 when anything is stale")
    ap.add_argument("--all", action="store_true", help="list notes without a voice section too")
    args = ap.parse_args(argv)

    root = repo_root()
    if root is None:
        print("voice_stale: not a git checkout, so there is no history to compare.")
        return 0

    notes = lint.load_notes()
    current, source = present_year(notes)
    if not current:
        print(f"voice_stale: no present year ({source}); the staleness check needs the "
              f"`chronology` block in the note the config names as vault.notes.calendar.")
        return 0
    recent_from = current - RECENT_YEARS

    rows = []
    for note in notes:
        if not note.rel.startswith(disclosure.LORE_ROOT):
            continue
        voice, body = section_lines(note, args.heading)
        if not voice:
            if args.all:
                rows.append((note.rel, 0, 0, "none"))
            continue
        taken = taken_year(note, args.heading)
        if taken and taken < recent_from:
            rows.append((note.rel, 0, 0, f"old (CY {taken})"))
            continue
        if not taken and args.heading.lower() == "testimony":
            rows.append((note.rel, 0, 0, "undated"))
            continue
        times = blame_times(root, note.rel)
        if not times:
            rows.append((note.rel, 0, 0, "unversioned"))
            continue
        v, b = newest(times, voice), newest(times, body)
        verdict = "unknown" if is_dirty(root, note.rel) else ("STALE" if b > v else "ok")
        rows.append((note.rel, v, b, verdict))

    if not rows:
        print(f"voice_stale: no note carries a `## {args.heading}` section.")
        return 0

    def bucket(verdict: str) -> int:
        if verdict == "STALE":
            return 0
        if verdict == "undated":
            return 1
        if verdict == "unknown":
            return 2
        if verdict.startswith("old"):
            return 3
        return 4 if verdict == "ok" else 5

    rows.sort(key=lambda r: (bucket(r[3]), -r[2], r[0]))
    width = max(len(r[0]) for r in rows)

    print(f"{'note':{width}}  {f'## {args.heading}':10}  {'around it':10}  verdict")
    for rel, v, b, verdict in rows:
        if verdict == "ok" and not args.all:
            continue
        print(f"{rel:{width}}  {when(v):10}  {when(b):10}  {verdict}")

    stale = sum(1 for r in rows if r[3] == "STALE")
    undated = sum(1 for r in rows if r[3] == "undated")
    unknown = sum(1 for r in rows if r[3] == "unknown")
    old = sum(1 for r in rows if r[3].startswith("old"))
    checked = len(rows) - sum(1 for r in rows if r[3] in ("none", "unversioned"))
    print(f"\n{stale} stale, {undated} undated, {unknown} unknown (uncommitted), {old} old by "
          f"design; {checked} checked against a present of CY {current} ({source}).")
    if stale or undated or unknown:
        print("Read these before publishing: a recent account, or one that claims to be current,"
              " is out of step with the canon around it.")
    return 1 if (args.strict and (stale or undated or unknown)) else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Build the worldkit **release payload**: the tarball a world syncs from.

A world does not need the kit's history. It needs a tree -- `tools/`, the world-facing documents,
the note templates, the prompt files, the theme, three workflows and the pin -- and `tools/
sync-tooling.sh` places each of those. So the payload is that tree, in the kit's own layout, and
`sync-tooling.sh --archive` applies it exactly as it applies a checkout. The two transports are
interchangeable by construction; `tools/verify-payload.sh` is the proof, and `RELEASE.md` here is
the record of why.

    python3 tools/build_payload.py                      # this checkout's pin, into ./dist/
    python3 tools/build_payload.py --out /tmp/dist      # somewhere else
    python3 tools/build_payload.py --tag v3.4.0 --out dist   # the tag must equal TOOLING_VERSION
    python3 tools/build_payload.py --check dist/worldkit-v3.4.0.tar.gz

**Deterministic.** Entries are sorted, every mtime is one constant, uid/gid are 0, and the gzip
header carries no name and no time -- so the same tree always produces the same sha256. That is
what lets a release be rebuilt and compared, and what makes the digest a thing worth publishing.

**What is NOT in it, on purpose.** A world owns `tools/local/`, the three site pages, its art, its
`site/public/`, its deploy state and its own lore; the sync never writes those, so the payload does
not carry them. Neither does it carry the kit's maintenance material (`docs/`, `CHANGELOG.md`,
`meta/platform-requests/`): those are the kit's own and a world receives none of it.

Exit codes: 0 fine, 2 a defect (a payload that would sync a world to the wrong version, a missing
member, a path that must never travel).
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import os
import shutil
import sys
import tarfile
import tempfile
from pathlib import Path

# 1980-01-01T00:00:00Z -- the epoch both gzip and the ustar format can represent, and a constant,
# which is the whole point: a rebuild of the same tree must hash the same.
FIXED_MTIME = 315532800

# Everything the payload carries, as (kit path, where a world holds it, who puts it there).
# `sync` is tools/sync-tooling.sh, on every update; `init` is export-template.sh / init-world.sh,
# when a world is created -- the demo world travels so that a world can ask for it back, and so the
# payload can prove itself without a checkout. This table is documentation *and* the source the
# staging below reads, so the two cannot drift apart.
PLACEMENT = (
    ("tools/", "tools/", "sync"),
    ("template/meta/conventions/", "meta/conventions/", "sync"),
    ("template/meta/templates/", "meta/templates/", "sync"),
    ("template/.pi/prompts/", ".pi/prompts/", "sync"),
    ("site-theme/", "site/", "sync"),
    (".github/workflows/", ".github/workflows/", "sync"),
    ("TOOLING_VERSION", "TOOLING_VERSION", "sync"),
    ("template/example-world/", "example-world/", "init"),
)

# Beside `tools/` in the kit, `tools/` in a world. MIT requires the notice to travel with the copy.
LICENCES = ("LICENSE", "LICENSE-CONTENT")

# The three workflows a world runs. All the OTHER workflows in the kit are the kit's (`ci.yml`,
# `template-fork.yml`, `release.yml`) and a world has no use for them.
WORKFLOWS = ("checks.yml", "site.yml", "tooling-drift.yml")

# Directories that exist only in the kit, or only after a world has built something. A world's own
# copy of these is not the kit's to hand out.
EXCLUDE_TOOLS = {"local", "docs", "__pycache__", ".git"}
EXCLUDE_SITE = {"dist", ".astro", "node_modules", "audit", "public"}
EXCLUDE_SITE_RELATIVE = {"src/content/generated", "src/data/generated", "infra/state.json"}

# What must be in a payload for it to be usable by the thing that applies it. Names a world's tools
# already depend on, not a file list to be maintained for its own sake.
REQUIRED = (
    "TOOLING_VERSION",
    "ARCHIVE.md",
    "tools/sync-tooling.sh",
    "tools/lint.py",
    "tools/LICENSE",
    "tools/LICENSE-CONTENT",
    "template/meta/conventions/conventions.md",
    "template/meta/conventions/tooling.md",
    "template/meta/conventions/agent-protocol.md",
    "template/meta/templates/",
    "template/.pi/prompts/",
    "template/example-world/world.config.yaml",
    "site-theme/package.json",
    "site-theme/src/",
    ".github/workflows/checks.yml",
    ".github/workflows/site.yml",
    ".github/workflows/tooling-drift.yml",
)

# A path that must never appear. Most are a world's; `site/public/` is the one that looks like the
# kit's and is not -- the sync never writes it, so shipping it would hand a world a file nothing
# places and invite someone to extract the payload over a tree (see ARCHIVE.md).
FORBIDDEN = (
    "docs/",
    "meta/platform-requests/",
    "tools/local/",
    "site-theme/public/",
    "site-theme/src/data/generated/",
    "site-theme/src/content/generated/",
    "site-theme/infra/state.json",
    "node_modules/",
    "__pycache__/",
    ".git/",
    ".astro/",
    "site-theme/dist/",
    "site-theme/audit/",
)

ARCHIVE_MD = """\
# worldkit {tag}

This archive is the kit's **release payload**: the tree a world needs, in the kit's own layout, and
the one file that knows where each part goes -- `tools/sync-tooling.sh`. The kit's history is not
here, because a world never needed it.

**Do not extract this over a world.** Untarred blindly it would invent `site-theme/` and
`template/` beside a world's own files, leave the documents where the world does not read them, and
still replace `TOOLING_VERSION` -- so the world would pin {tag} while holding the previous version's
rules. Apply it with the tools inside it, from the world's root:

    tools/sync-tooling.sh --archive worldkit-{tag}.tar.gz

A world that has no `tools/` yet cannot run that, and it is the one case where copying is right:

    tar -xzf worldkit-{tag}.tar.gz -C /tmp
    cp -R /tmp/worldkit-{tag}/tools ./tools
    tools/sync-tooling.sh --archive "$PWD/worldkit-{tag}.tar.gz"   # or omit --archive to fetch it

## What is in it, and where a world holds it

| in this archive | a world holds it at | written by |
|---|---|---|
| `tools/` | `tools/` (never `tools/local/`) | every sync |
| `template/meta/conventions/` | `meta/conventions/` | every sync |
| `template/meta/templates/` | `meta/templates/` | every sync |
| `template/.pi/prompts/` | `.pi/prompts/` | every sync |
| `site-theme/` | `site/` (the theme; a world keeps its pages, art and public/) | every sync |
| `.github/workflows/checks.yml`, `site.yml`, `tooling-drift.yml` | `.github/workflows/` | every sync |
| `TOOLING_VERSION` | the pin | every sync |
| `template/example-world/` | `example-world/`, only if asked for | `init-world.sh --fetch-example` |

`tools/LICENSE` and `tools/LICENSE-CONTENT` travel with the copy: MIT requires its notice to travel,
and CC BY 4.0 covers the documents, the templates and the demo world.

## What a world owns, and this archive will not touch

`tools/local/`, `meta/world-conventions.md`, `world.config.yaml`, `AGENTS.md` (outside the marked
protocol region), the three site pages (`index`, `about`, `follow`), `site/public/`, the world's art
and prompt notes, `site/infra/state.json`, and every note in the vault.
"""


class PayloadError(Exception):
    """A payload that must not be built, or must not be trusted."""


# --- staging ------------------------------------------------------------------------------------

def _copy(source: Path, dest: Path, excluded: set[str], excluded_relative: tuple[str, ...] = ()):
    """Copy a directory tree, refusing the paths a world owns instead of carrying them."""
    dest.mkdir(parents=True, exist_ok=True)
    for base, dirs, files in os.walk(source):
        dirs.sort()
        rel_base = Path(base).relative_to(source)
        dirs[:] = [d for d in dirs if d not in excluded]
        for name in sorted(files):
            rel = rel_base / name
            if rel.as_posix() in excluded_relative or name in {"__pycache__", ".DS_Store"}:
                continue
            if name.endswith((".pyc", ".pyo")):
                continue
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(Path(base) / name, target)


def stage(root: Path, tag: str, dest: Path) -> None:
    """Lay the payload out in the kit's own layout, under `worldkit-<tag>/`."""
    if not (root / "TOOLING_VERSION").is_file():
        raise PayloadError(f"{root} is not a worldkit: no TOOLING_VERSION")
    pin = (root / "TOOLING_VERSION").read_text(encoding="utf-8").strip()
    if tag != pin:
        raise PayloadError(
            f"the tag is {tag} but TOOLING_VERSION says {pin}. They are the same string by "
            "design (CONTRIBUTING.md, Release step 4): a world copies the tag into its own pin, so "
            "a payload whose two halves disagree makes every world that takes it lie about itself."
        )

    _copy(root / "tools", dest / "tools", EXCLUDE_TOOLS, {"LICENSE", "LICENSE-CONTENT"})
    for licence in LICENCES:
        if not (root / licence).is_file():
            raise PayloadError(f"{root} has no {licence}: a copy of the tools may not travel without it")
        shutil.copy2(root / licence, dest / "tools" / licence)

    for rel in ("template/meta/conventions", "template/meta/templates",
                "template/.pi/prompts", "template/example-world"):
        _copy(root / rel, dest / rel, set())
    _copy(root / "site-theme", dest / "site-theme", EXCLUDE_SITE, EXCLUDE_SITE_RELATIVE)

    workflows = dest / ".github/workflows"
    workflows.mkdir(parents=True, exist_ok=True)
    for name in WORKFLOWS:
        source = root / ".github/workflows" / name
        if not source.is_file():
            raise PayloadError(f"{root} has no .github/workflows/{name}: a world would run without it")
        shutil.copy2(source, workflows / name)

    (dest / "TOOLING_VERSION").write_text(tag + "\n", encoding="utf-8")
    (dest / "ARCHIVE.md").write_text(ARCHIVE_MD.format(tag=tag), encoding="utf-8")


# --- packing ------------------------------------------------------------------------------------

def pack(payload_dir: Path, out: Path) -> str:
    """Write a deterministic .tar.gz of `payload_dir` and return its sha256.

    One top-level directory (`worldkit-<tag>/`), sorted entries, one mtime, mode preserved so a
    shell tool keeps its execute bit, and a gzip header with no name and no time.
    """
    entries: list[tuple[str, Path | None]] = []
    for base, dirs, files in os.walk(payload_dir):
        dirs.sort()
        rel_base = Path(base).relative_to(payload_dir)
        for name in dirs:
            entries.append(((rel_base / name).as_posix(), None))
        for name in sorted(files):
            entries.append(((rel_base / name).as_posix(), Path(base) / name))
    entries.sort(key=lambda entry: entry[0])

    top = payload_dir.name
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w", format=tarfile.GNU_FORMAT) as archive:
        def add(rel: str, full: Path | None) -> None:
            info = tarfile.TarInfo(top if rel == "." else f"{top}/{rel}")
            info.mtime = FIXED_MTIME
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            if full is None:
                info.type, info.mode = tarfile.DIRTYPE, 0o755
                archive.addfile(info)
            else:
                info.mode = full.stat().st_mode & 0o777
                info.size = full.stat().st_size
                with full.open("rb") as handle:
                    archive.addfile(info, handle)

        add(".", None)
        for rel, full in entries:
            add(rel, full)

    gz = gzip.compress(buffer.getvalue(), 9, mtime=0)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(gz)
    digest = hashlib.sha256(gz).hexdigest()
    out.with_suffix(out.suffix + ".sha256").write_text(f"{digest}  {out.name}\n", encoding="utf-8")
    return digest


# --- checking -----------------------------------------------------------------------------------

def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(path: Path, expect_sha: str | None = None) -> str:
    """Validate a payload. Returns its pin. Raises PayloadError on anything that must not ship."""
    if not path.is_file():
        raise PayloadError(f"{path} is not a file")

    summary = path.with_suffix(path.suffix + ".sha256")
    want = expect_sha
    if want is None and summary.is_file():
        want = summary.read_text(encoding="utf-8").split()[0]
    got = sha256_of(path)
    if want is not None and want != got:
        raise PayloadError(
            f"{path.name} does not match its checksum.\n  expected {want}\n  got      {got}\n"
            "  Do not publish it, and do not sync from it."
        )

    with tarfile.open(path, "r:gz") as archive:
        members = archive.getmembers()
        names = [member.name for member in members]
        # The sync untars this into a temporary directory and then MOVES the one top-level
        # directory it finds. Anything else -- a traversal, an absolute path, two roots -- is a
        # payload that would write somewhere it was not asked to.
        for name in names:
            if name.startswith("/") or ".." in Path(name).parts:
                raise PayloadError(f"{path.name} contains an absolute or traversing path: {name}")
        tops = {name.split("/")[0] for name in names}
        if len(tops) != 1:
            raise PayloadError(f"{path.name} has {len(tops)} top-level entries, not one: {sorted(tops)}")
        top = tops.pop()
        # `worldkit-<tag>.tar.gz`, so the name says which tag the file claims to be. The pin inside
        # has to say the same thing: a payload attached to the wrong release is a copy-paste on a
        # release page, and it must not be able to make a world pin a version it is not holding.
        named = path.name.removeprefix("worldkit-").removesuffix(".tar.gz")
        if top != f"worldkit-{named}":
            raise PayloadError(f"{path.name}: the top-level directory is {top}, not worldkit-{named}")

        pin = None
        for member in members:
            if member.name == f"{top}/TOOLING_VERSION":
                pin = archive.extractfile(member).read().decode("utf-8").strip()
        if not pin:
            raise PayloadError(f"{path.name} has no TOOLING_VERSION: nothing in it says what version it is")
        if top != f"worldkit-{pin}":
            raise PayloadError(f"{path.name} carries the pin {pin} but is named after another tag")

        listed = set(names)
        for required in REQUIRED:
            full = f"{top}/{required}"
            if full in listed:
                continue
            if required.endswith("/") and any(name.startswith(full) for name in names):
                continue
            raise PayloadError(f"{path.name} is missing {required}, so it cannot be used as it claims")

        for forbidden in FORBIDDEN:
            full = f"{top}/{forbidden}"
            hits = [name for name in names if name == full or name.startswith(full)]
            if hits:
                raise PayloadError(
                    f"{path.name} carries {forbidden}, which belongs to a world (or to the kit's own "
                    f"maintenance) and must not travel: {hits[0]}"
                )

        for member in members:
            if member.name.endswith(".sh") and member.isfile() and not member.mode & 0o111:
                raise PayloadError(
                    f"{path.name}: {member.name} has no execute bit. A shell tool that arrives "
                    "unrunnable is the defect that cost a release once (CHANGELOG 1.3.x)."
                )

    return pin


# --- cli ----------------------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="build_payload.py",
        description="Build or check the worldkit release payload.",
    )
    parser.add_argument("--root", default=".", help="the kit checkout (default: .)")
    parser.add_argument("--tag", default=None, help="default: TOOLING_VERSION; must equal it when given")
    parser.add_argument("--out", default="dist", help="where to write the tarball (default: dist/)")
    parser.add_argument("--check", metavar="TARBALL", default=None,
                        help="check an existing payload instead of building one")
    parser.add_argument("--sha256", default=None, help="with --check: the digest you expected")
    args = parser.parse_args(argv)

    try:
        if args.check:
            pin = check(Path(args.check), args.sha256)
            print(f"ok: {args.check} is a worldkit {pin} payload, {sha256_of(Path(args.check))}")
            return 0

        root = Path(args.root).resolve()
        tag = args.tag or (root / "TOOLING_VERSION").read_text(encoding="utf-8").strip()
        out = Path(args.out) / f"worldkit-{tag}.tar.gz"
        with tempfile.TemporaryDirectory() as tmp:
            payload = Path(tmp) / f"worldkit-{tag}"
            payload.mkdir()
            stage(root, tag, payload)
            digest = pack(payload, out)
        pin = check(out, digest)
        print(f"{digest}  {out}")
        print(f"ok: worldkit {pin} payload, {len(list(_members(out)))} entries", file=sys.stderr)
        return 0
    except PayloadError as error:
        print(f"build_payload: {error}", file=sys.stderr)
        return 2


def _members(path: Path):
    with tarfile.open(path, "r:gz") as archive:
        yield from archive.getmembers()


if __name__ == "__main__":
    sys.exit(main())

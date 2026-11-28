#!/usr/bin/env python3
"""Does `world.config.yaml` agree with the vault it describes?

Every tool in this directory reads the config before it reads a note, and its failure modes are
quiet or far away:

* an id in `vault.notes` that no note carries makes that check **inert**, not wrong — the linter
  stops enforcing the world's flags, the exporter publishes without the world's vocabulary, and
  nothing anywhere says so;
* a block that does not parse is a traceback out of whichever tool touched it first, pointing at a
  note rather than at the block's shape;
* a section slug listed twice, or a kind claimed by two sections, silently drops notes from the
  site: the second claimant wins or loses depending on ordering, and no page reports it;
* the Python reader and the Node reader can disagree about the same file, and both build happily —
  on their own half of it.

The kit's suites ask these questions against fixtures and against the kit's demo world (36
entities, no gods, no atlas, one thread). This asks them of **this** world's config, in this
repository, and answers in the author's terms: which key, which note, and what to write instead.

    python3 tools/check_config.py                 # this repository (the demo world, in the kit)
    python3 tools/check_config.py path/to/vault   # another vault, for comparison or debugging

Levels, and what each one means for the run:

* **ERROR** — the config and the vault contradict each other. Exit 1. Every tool that read the
  config would be reading a lie.
* **WARN** — consistent, but something declared is not there, or something used is not declared.
  Not a failure: a world mid-authoring has these, and `lint.py --strict` already fails on worse.
* **NOTE** — the value is still the template's `REPLACE`. The author's to-do list, never a failure;
  `lint.py` reports the same placeholders in prose, as warnings.

The kit's rule for a fenced block is "inert when absent": a world that never declares its eras
loses that check rather than failing to build. This tool honours that — but a block that is
*declared and missing* is not absent, it is a promise the vault does not keep, and that is an ERROR.

Exit codes: 0 clean (warnings and notes are not failures), 1 errors, 2 usage.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit_config  # noqa: E402  (the world's config seam)
import lint  # noqa: E402  (the kind vocabulary and the tag-vocabulary reader, not a second copy)

ROOT = Path(__file__).resolve().parent.parent
#: Where the kit keeps the one world it owns. `tools/`'s own README and the tests resolve a world
#: the same way: the repository root when it is a world, otherwise its demo world.
DEMO = ROOT / "template" / "example-world"

#: The template's placeholder token, as `init-world.sh` and `lint.py` spell it. A value that still
#: carries it is the author's to-do, not a defect -- which is the line lint draws for prose, and it
#: has to be the same line here or a fresh fork is red from its first push.
PLACEHOLDER = "REPLACE"

LEVELS = ("ERROR", "WARN", "NOTE")
SLUG_RE = re.compile(r"^[a-z0-9-]+$")
DATE_PREFIX_RE = re.compile(r"^[A-Z]{2,6}$")
VOCABULARY_LISTS = ("published_tags", "keystones", "plot_web_surfaces")


@dataclass(frozen=True)
class Finding:
    level: str      # ERROR | WARN | NOTE
    where: str      # a repository-relative path the author can open
    message: str


# --- the checks ---------------------------------------------------------------------------


def findings(root: Path) -> list[Finding]:
    """Every disagreement between the config at `root` and the vault around it."""
    root = Path(root).resolve()
    path = root / "world.config.yaml"
    try:
        cfg = kit_config.load(path)
    except kit_config.ConfigError as exc:
        # The loader already says `file:line` and what it expected, in words written for an
        # author. Repeating it as one finding keeps the output one shape.
        return [Finding("ERROR", _rel(root, path), str(exc))]

    found: list[Finding] = []
    _check_notes(cfg, root, found)
    _check_site_sections(cfg, root, found)
    _check_declared_paths(cfg, root, found)
    notes = _notes(root)
    _check_blocks(cfg, root, found)
    _check_vocabularies(cfg, notes, found)
    found.extend(parity(cfg, root))
    return found


def _check_notes(cfg: kit_config.Config, root: Path, found: list[Finding]) -> None:
    """Every id the config names resolves to a note that carries the block the kit looks for."""
    for name in (*kit_config.BLOCK_INFO, "testimony_book"):
        note_id = cfg.note_ids.get(name)
        if not note_id:
            continue  # not declared: the check is inert, which is a world's right (D15)
        if cfg.path_of(name) is None:
            _add(found, "ERROR", "world.config.yaml",
                 f"vault.notes.{name} is '{note_id}', and no note in the vault has that id. Ids "
                 f"are frontmatter `id:` values; the note may be missing, or its id misspelt.",
                 note_id)


def _check_blocks(cfg: kit_config.Config, root: Path, found: list[Finding]) -> None:
    """Each block a note is expected to carry is present, parses, and is the right shape."""
    for name, info in kit_config.BLOCK_INFO.items():
        note_path = cfg.path_of(name)
        if note_path is None:
            continue  # unresolved, or not declared: `_check_notes` has said so
        where = _rel(root, note_path)
        raw = kit_config.read_block(note_path, info)
        if raw is None:
            _add(found, "ERROR", where,
                 f"this note is vault.notes.{name}, and it carries no ```{info}``` block. Add the "
                 f"block, or remove vault.notes.{name} from world.config.yaml and lose the check.")
            continue
        try:
            block = cfg.block(name)
        except kit_config.ConfigError as exc:
            _add(found, "ERROR", where, f"the ```{info}``` block does not parse: {exc}", raw)
            continue
        if block is None:
            _add(found, "ERROR", where,
                 f"the ```{info}``` block is there but reads as empty. An empty list is `[]`.",
                 raw)
            continue
        _check_block_shape(name, info, block, where, found)


def _check_block_shape(name: str, info: str, block, where: str, found: list[Finding]) -> None:
    """The shape each block must have. Never its contents: the vocabularies are the world's."""
    if name == "flags":
        if not isinstance(block, list):
            _add(found, "ERROR", where, "the `flags` block must be a list, `[]` when a world has "
                                        "declared none yet", block)
            return
        seen = set()
        for i, flag in enumerate(block):
            flag_id = flag.get("id") if isinstance(flag, dict) else None
            if not flag_id:
                _add(found, "ERROR", where, f"flag #{i + 1} has no `id:`", block)
            elif flag_id in seen:
                _add(found, "ERROR", where, f"flag '{flag_id}' is declared twice", block)
            else:
                seen.add(flag_id)
        return

    if not isinstance(block, dict):
        _add(found, "ERROR", where, f"the `{info}` block must be a mapping of keys", block)
        return

    if name == "eras":
        order = block.get("order")
        if not isinstance(order, list) or not order:
            _add(found, "ERROR", where, "the `eras` block needs `order:` with at least one era",
                 block)
            return
        duplicates = sorted({e for e in order if order.count(e) > 1})
        if duplicates:
            _add(found, "ERROR", where, f"era(s) listed twice in `order:` {duplicates}; the tools "
                                        f"rank eras by their position", duplicates)

    elif name == "calendar":
        prefix = block.get("date_prefix")
        if not isinstance(prefix, str) or not DATE_PREFIX_RE.match(prefix):
            _add(found, "ERROR", where,
                 "`date_prefix:` must be 2-6 capital letters (it is the prefix a date is written "
                 f"with, e.g. CY 650); found {prefix!r}", prefix)
        present = block.get("present")
        if not isinstance(present, int) or isinstance(present, bool):
            _add(found, "ERROR", where,
                 "`present:` must be a number: the tools do arithmetic on it (an account is stale "
                 f"when its canon moved after it); found {present!r}", present)

    elif name == "site_vocabulary":
        for key in VOCABULARY_LISTS:
            if key not in block:
                _add(found, "WARN", where, f"the `site-vocabulary` block does not declare `{key}:`; "
                                           f"the site build reads it and treats it as empty. Use "
                                           f"`{key}: []` to mean none.", block)
            elif not isinstance(block[key], list):
                _add(found, "ERROR", where, f"`{key}:` must be a list", block[key])
        tags = block.get("published_tags")
        if isinstance(tags, list):
            for tag in tags:
                if not isinstance(tag, str) or not SLUG_RE.match(tag):
                    _add(found, "ERROR", where,
                         f"published tag {tag!r} is not a slug (lower case, digits, hyphens): it "
                         f"becomes a URL", tag)
            duplicates = sorted({t for t in tags if isinstance(t, str) and tags.count(t) > 1})
            if duplicates:
                _add(found, "ERROR", where, f"published tag(s) listed twice: {duplicates}",
                     duplicates)


def _check_site_sections(cfg: kit_config.Config, root: Path, found: list[Finding]) -> None:
    """Sections own kinds. A slug or a kind claimed twice loses notes without saying so."""
    if cfg.site is None:
        return
    where = "world.config.yaml"
    seen_slugs: dict[str, int] = {}
    claimed: dict[str, str] = {}
    for i, section in enumerate(cfg.site.sections):
        if section.slug in seen_slugs:
            _add(found, "ERROR", where,
                 f"site.sections[{i}]: slug '{section.slug}' is already used by "
                 f"site.sections[{seen_slugs[section.slug]}]", section.slug)
        else:
            seen_slugs[section.slug] = i
        for kind in section.kinds:
            if kind in claimed:
                _add(found, "ERROR", where,
                     f"site.sections[{i}] ('{section.slug}') claims kind {kind}, which "
                     f"'{claimed[kind]}' already claims. The first section wins, so every {kind} "
                     f"note appears under '{claimed[kind]}' and the other section stays empty.", kind)
            else:
                claimed[kind] = section.slug


def _check_declared_paths(cfg: kit_config.Config, root: Path, found: list[Finding]) -> None:
    """Paths the config declares that are not there. Both are world content, and both are a WARN:
    lint already exempts a missing process doc from frontmatter, so nothing is broken by it."""
    for doc in sorted(cfg.process_docs):
        if not (root / doc).is_file():
            _add(found, "WARN", "world.config.yaml",
                 f"vault.process_docs lists '{doc}', and there is no such file. The list only "
                 f"exempts a document from frontmatter, so this is harmless — or a misspelt path.",
                 doc)
    if cfg.scenarios_dir is not None and not cfg.scenarios_dir.is_dir():
        rel = _rel(root, cfg.scenarios_dir)
        _add(found, "WARN", "world.config.yaml",
             f"vault.scenarios is '{rel}', and there is no such directory. The simulator will "
             f"refuse until it exists or the key goes. One directory per campaign, which is also "
             f"where its scenario files are looked for.", rel)


def _check_vocabularies(cfg: kit_config.Config, notes: list, found: list[Finding]) -> None:
    """What the config publishes against what the vault actually has.

    Two questions nothing else asks: a published tag the world's own `tags-vocabulary` does not
    know (the site grows a page for a tag no note may carry), and a note kind no site section
    claims (the note is never published, which reads as a broken page rather than a decision).
    """
    tags: set[str] | None = None
    for note in notes:
        for info, _line, text in note.blocks:
            if info == lint.TAG_BLOCK:
                tags = lint.parse_tag_vocabulary(text)["tags"]
                break
        if tags is not None:
            break

    vocab = cfg.block("site_vocabulary") if cfg.note_ids.get("site_vocabulary") else None
    published = vocab.get("published_tags") if isinstance(vocab, dict) else None
    if tags is not None and isinstance(published, list):
        unknown = [t for t in published if isinstance(t, str) and t not in tags]
        if unknown:
            _add(found, "WARN", "world.config.yaml",
                 f"published tag(s) {unknown} are not in the world's `tags-vocabulary` block. The "
                 f"site builds a page for each and no note may carry one.", unknown)

    if cfg.site is None:
        return
    deferred = set(cfg.site.deferred_kinds)
    unclaimed: dict[str, list[str]] = {}
    for note in notes:
        kind = note.fm.get("kind")
        if not kind or note.is_index or note.fm.get("engine") == "true":
            continue  # engine entities are the platform's, not the site's
        if kind in deferred or cfg.site.section_of_kind(kind) is not None:
            continue
        unclaimed.setdefault(kind, []).append(note.rel)
    for kind, rels in sorted(unclaimed.items()):
        _add(found, "WARN", rels[0],
             f"kind {kind} is used by {len(rels)} note(s) and no `site.sections` entry lists it, "
             f"so none of them is published. Add {kind} to a section's `kinds:`, or to "
             f"site.deferred_kinds if that is intended.", kind)


# --- the two readers ----------------------------------------------------------------------


def parity(cfg: kit_config.Config, root: Path) -> list[Finding]:
    """`kit_config.py` and `kit_config.mjs` must agree about *this* config, field by field.

    There are two readers because the Node tools cannot call Python, and one grammar kept in two
    languages drifts. A disagreement is never the world's fault and never looks like one: the
    linter and the site build read one answer, the transformer another.
    """
    node = shutil.which("node")
    if node is None:
        return [Finding("NOTE", "world.config.yaml",
                        "node is not installed, so the two config readers' agreement was not "
                        "checked here. Lint, the site export and the checks above are unaffected.")]
    proc = subprocess.run([node, str(Path(__file__).with_name("kit_config.mjs"))],
                          capture_output=True, text=True, cwd=str(root),
                          env={**os.environ, "WORLD_CONFIG": str(cfg.path)})
    if proc.returncode != 0:
        detail = (proc.stderr.strip().splitlines() or ["(no message)"])[0]
        return [Finding("ERROR", "tools/kit_config.mjs",
                        f"the Node reader cannot read this config, although the Python reader can: "
                        f"{detail} This is a tooling defect — report it, and do not edit the config "
                        f"around it.")]
    try:
        theirs = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return [Finding("ERROR", "tools/kit_config.mjs",
                        "the Node reader printed something that is not JSON. This is a tooling "
                        "defect — report it, and do not edit the config around it.")]

    ours = {
        "world_id": cfg.world_id,
        "title": cfg.title,
        "slug": cfg.slug,
        "overland": cfg.overland_id,
        "game_ready_repo": str(cfg.game_ready_repo),
        "features": sorted(cfg.features),
        "notes": cfg.note_ids,
        "process_docs": sorted(cfg.process_docs),
        "scenarios_dir": str(cfg.scenarios_dir) if cfg.scenarios_dir else None,
        "spelling": cfg.spelling,
    }
    # Two of these are lists whose ORDER the readers have no reason to agree on: the config writes
    # them in the order it declares, and Python holds them in a frozenset. Comparing the raw values
    # reported a disagreement in every world with more than one process document — a false alarm
    # from the checker, which is the defect class this whole tool exists to avoid.
    unordered = {"features", "process_docs"}

    def same(key, mine, them):
        if key in unordered:
            return sorted(them or []) == sorted(mine or [])
        return them == mine

    found: list[Finding] = []
    for key, mine in ours.items():
        if not same(key, mine, theirs.get(key)):
            _add_disagreement(found, key, mine, theirs.get(key))

    if cfg.site is not None:
        their_site = theirs.get("site") or {}
        pairs = {
            "site.url": (cfg.site.url, their_site.get("url")),
            "site.sections": ([{"slug": s.slug, "label": s.label, "kinds": list(s.kinds)}
                               for s in cfg.site.sections],
                              [{"slug": s.get("slug"), "label": s.get("label"),
                                "kinds": list(s.get("kinds") or [])}
                               for s in their_site.get("sections") or []]),
            "site.deferred_kinds": (sorted(cfg.site.deferred_kinds),
                                    sorted(their_site.get("deferred_kinds") or [])),
        }
        for key, (mine, them) in pairs.items():
            if them != mine:
                _add_disagreement(found, key, mine, them)
    for name in kit_config.BLOCK_INFO:
        try:
            mine = cfg.block(name)
        except kit_config.ConfigError:
            continue  # already reported, with the parser's own message
        them = (theirs.get("blocks") or {}).get(name)
        if mine != them:
            _add_disagreement(found, f"the ```{kit_config.BLOCK_INFO[name]}``` block", mine, them)
    return found


def _add_disagreement(found: list[Finding], key: str, mine, them) -> None:
    found.append(Finding(
        "ERROR", "world.config.yaml",
        f"the two readers disagree about {key}: kit_config.py reads {mine!r}, kit_config.mjs "
        f"{them!r}. Both build their half of the world happily, so this is a tooling defect — "
        f"report it, and do not edit the config around it."))


# --- plumbing -----------------------------------------------------------------------------


def _add(found: list[Finding], level: str, where: str, message: str, value=None) -> None:
    """Append a finding, downgrading it to a NOTE when the value it is about is a placeholder."""
    if value is not None and PLACEHOLDER in str(value).upper():
        level = "NOTE"
    found.append(Finding(level, where, message))


def _notes(root: Path) -> list:
    """The vault's notes, read by the linter's own loader (one reader, not a second copy).

    `lint.load_notes` reads `lint.ROOT`, which is module state the tests move on purpose; the
    original is restored here so a caller that imported lint keeps what it had.
    """
    previous = lint.ROOT
    try:
        lint.ROOT = Path(root)
        return lint.load_notes()
    finally:
        lint.ROOT = previous


def _rel(root: Path, path: Path) -> str:
    try:
        return Path(path).resolve().relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _shown(path: Path) -> str:
    """A path as the author's terminal would say it: relative when it is below the cwd."""
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return str(path)


def default_root() -> Path:
    """The world this repository holds: its root, or the kit's demo world when the root is the kit."""
    if (ROOT / "world.config.yaml").is_file():
        return ROOT
    return DEMO


def main(argv: list[str]) -> int:
    root = Path(argv[0]).resolve() if argv else default_root()
    path = root / "world.config.yaml"
    if not path.is_file():
        print(f"no world.config.yaml in {root}: this is not a world, so there is nothing to check")
        return 0

    found = findings(root)
    found.sort(key=lambda f: (LEVELS.index(f.level), f.where))
    for finding in found:
        print(f"{finding.where}: {finding.level:<5} {finding.message}")
    counts = {level: sum(1 for f in found if f.level == level) for level in LEVELS}
    summary = ", ".join(f"{n} {level.lower()}(s)" for level, n in counts.items() if n)
    print(f"checked {_shown(path)} against {len(_notes(root))} notes: {summary or 'clean'}")
    if counts["NOTE"]:
        print("a NOTE is a placeholder you have not filled in yet; it does not fail the run.")
    return 1 if counts["ERROR"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

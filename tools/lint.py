#!/usr/bin/env python3
"""Vault linter for a world codex.

Checks the rules in the kit's docs/conventions.md that can be checked mechanically, so any
model or human can verify a session's output. Standard library only.

World-specific values come from `world.config.yaml` and the world's fenced blocks (T1); this
script hardcodes none of them. A vault with no config still lints, with those checks inert.

    python3 tools/lint.py              # lint the whole vault
    python3 tools/lint.py world/gods   # lint part of it (links still resolve vault-wide)
    python3 tools/lint.py --strict     # warnings also fail the run
    python3 tools/lint.py --json       # machine-readable output

Exit code: 0 clean, 1 errors (or warnings with --strict), 2 usage error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit_config  # noqa: E402  (the world's config seam: `docs/extraction.md` T1)

ROOT = Path(__file__).resolve().parent.parent

# --- The world's vocabulary (T1) ------------------------------------------------------------
# Resolved lazily, per `ROOT`, so the test harness can point ROOT at a fixture vault. When a
# vault carries no config, these are inert rather than wrong (D15).

#: Process documents the kit always exempts from frontmatter. A world adds its own in
#: `vault.process_docs` — e.g. a temporary plan of a world's own.
KIT_DOC_FILES = {"README.md", "ROADMAP.md", "AGENTS.md", "meta/world-conventions.md"}

def world_config() -> "kit_config.Config | None":
    """The world's config, or None when there is none. Cached per resolved root by kit_config."""
    return kit_config.for_root(ROOT)


def doc_files() -> set[str]:
    return KIT_DOC_FILES | (set(world_config().process_docs) if world_config() else set())


def spelling() -> str:
    """The world's spelling rule (`vault.spelling`): british (the default), american or off."""
    cfg = world_config()
    return cfg.spelling if cfg else "british"


def era_vocabulary() -> set[str]:
    """The values `era:` may take, from the `eras` block. Empty when the world declares none."""
    cfg = world_config()
    block = cfg.block("eras") if cfg else None
    return set(block.get("order", [])) if isinstance(block, dict) else set()

# --- Vocabulary (the kit's docs/conventions.md) -------------------------------------------------

STATUS = {"working", "agreed", "engine-ready", "deprecated"}
NAME_STATUS = {"working", "agreed"}
DISCLOSURE = {"open", "earned", "sealed"}  # conventions section 7 (in-play disclosure)
REQUIRED = ["id", "kind", "title", "name_status", "status", "engine"]

KIND_PREFIX = {
    "SETTLEMENT": "loc_", "PLACE": "loc_", "REGION": "zone_", "FACTION": "faction_",
    "NPC": "npc_", "GOD": "god_", "RACE": "race_", "CREATURE": "mon_", "ITEM": "item_",
    "HISTORY_EVENT": "hist_", "FIGURE": "fig_", "THREAD": "thread_", "TOPIC": "topic_",
    "CAMPAIGN": "camp_", "OVERLAY": "overlay_", "MODULE": "mod_", "INDEX": "topic_",
}
ID_RE = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)+$")
ID_REF_RE = re.compile(
    r"\b(?:loc|zone|npc|want|fact|faction|evt|item|mon|mod|camp|quest|room|enc|race|"
    r"hist|fig|god|thread|topic|overlay|mig|rel)_[a-zA-Z0-9_]+\b"
)
FORBIDDEN_ENGINE_KEYS = {"hp", "ac", "bab", "cr", "author_id"}
# Condition predicate names that look like ids (npc_, fact_, quest_ prefixes) but are not references.
PREDICATE_NAMES = {"npc_alive", "fact_revealed", "quest_state"}
EXCLUDE_DIRS = {".git", ".obsidian", "node_modules", ".trash", "tools", "meta/templates",
                "site", "site-theme", ".pi",
                # The kit's own source of the world template. It is a world (the skeleton an author
                # forks), but it is not THIS vault: it is verified where it is exported, and its
                # embedded example world is a separate world again.
                "template",
                # The template's mirrored example world is a world, but it is not THIS vault: it must
                # neither be linted as one nor be published by the exporter (which reuses load_notes).
                # The id resolver never sees it either: it walks SCOPE_DIRS, not the vault root.
                "example-world",
                # The kit's own documents (conventions, the registers, the guide) and the draft
                # specs written for the platform repository. Neither is a vault note: the kit is
                # not a world, and only its `verify-kit.sh` fixture vault is linted.
                "docs", "meta/platform-requests"}
SCOPE_DIRS = {"principles", "world", "campaigns", "maps", "meta"}

AMERICAN = {  # American spelling -> British (AGENTS.md writing conventions)
    "color": "colour", "colors": "colours", "favor": "favour", "favors": "favours",
    "center": "centre", "centers": "centres", "civilization": "civilisation",
    "organized": "organised", "organize": "organise", "gray": "grey", "toward": "towards",
    "honor": "honour", "honors": "honours", "defense": "defence", "armor": "armour",
    "artifact": "artefact", "artifacts": "artefacts", "realize": "realise",
    "realized": "realised", "recognize": "recognise", "meter": "metre", "meters": "metres",
    "kilometer": "kilometre", "kilometers": "kilometres", "neighbor": "neighbour",
    "labor": "labour", "behavior": "behaviour", "theater": "theatre", "analyze": "analyse",
}
AMERICAN_RE = re.compile(r"\b(" + "|".join(AMERICAN) + r")\b", re.IGNORECASE)


@dataclass
class Issue:
    level: str  # ERROR | WARN
    path: str
    line: int
    code: str
    msg: str


@dataclass
class Note:
    path: Path
    rel: str
    text: str
    fm: dict = field(default_factory=dict)
    fm_raw: str = ""
    body_start: int = 0  # 0-based line index where the body starts
    has_fm: bool = False
    is_doc: bool = False
    is_index: bool = False
    blocks: list = field(default_factory=list)  # (kind_of_fence, start_line, text)


# --- Parsing --------------------------------------------------------------------------


def parse_frontmatter(text: str):
    """Minimal frontmatter parser (no PyYAML). Returns (dict, raw, body_start_line)."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}, "", 0
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            raw = "\n".join(lines[1:i])
            fm: dict = {}
            key = None
            for ln in lines[1:i]:
                m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*?)\s*$", ln)
                if m and not ln.startswith((" ", "\t")):
                    key = m.group(1)
                    fm[key] = m.group(2)
                elif key is not None and ln.strip():
                    fm[key] = (fm[key] + " " + ln.strip()).strip()
            return fm, raw, i + 1
    return {}, "", 0


def unquote(v: str) -> str:
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    # strip trailing comment
    return re.sub(r"\s+#.*$", "", v).strip()


def fenced_blocks(lines: list[str]):
    """Yield (info, start_line_1based, text) for each fenced block."""
    i = 0
    while i < len(lines):
        m = re.match(r"^```(\S*)\s*$", lines[i])
        if m:
            info, start = m.group(1), i
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"):
                j += 1
            yield info, start + 1, "\n".join(lines[start + 1 : j])
            i = j + 1
        else:
            i += 1


TAG_BLOCK = "tags-vocabulary"
TAG_NAMING_FAMILIES = ("peoples", "powers", "places")


def parse_tag_vocabulary(text: str) -> dict:
    """Parse the `tags-vocabulary` block in meta/tag-vocabulary.md.

    Families are `family: [a, b, c]` on one line; `homes:` opens a short-name map, one
    `tag: note` per line. The vocabulary is the single home for what a tag may be, so the
    linter reads it from the note rather than keeping a second copy.
    """
    vocab: dict = {"tags": set(), "naming": set(), "gm_only": set(), "homes": {}}
    section = ""
    for raw in text.split("\n"):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        key, _, rest = line.partition(":")
        key, rest = key.strip(), rest.strip()
        if not rest:  # `homes:` opens the map
            section = key
            continue
        if section == "homes":
            vocab["homes"][key] = rest
            continue
        names = [t.strip().strip("'\"") for t in rest.strip("[]").split(",") if t.strip()]
        vocab["tags"].update(names)
        if key == "gm_only":
            vocab["gm_only"].update(names)
        elif key in TAG_NAMING_FAMILIES:
            vocab["naming"].update(names)
    return vocab


def strip_code(text: str, inline: bool = True) -> str:
    """Blank out fenced blocks, and inline code too unless `inline=False`, keeping line numbers.

    Fenced blocks are always blanked: they hold engine YAML and examples, never prose. Inline
    code is blanked for the link and heading checks, which must not read a link inside a code
    span. The **export** passes `inline=False`: a lore line may quote a word in a backtick span,
    and blanking it published `**\u0060read twice\u0060**` as `****` (fixed in Step 16).
    """
    out, in_fence = [], False
    for ln in text.split("\n"):
        if ln.startswith("```"):
            in_fence = not in_fence
            out.append("")
        elif in_fence:
            out.append("")
        elif inline:
            out.append(re.sub(r"`[^`]*`", "", ln))
        else:
            out.append(ln)
    return "\n".join(out)


def top_level_keys(block: str) -> list[str]:
    return re.findall(r"^([A-Za-z_][\w-]*):", block, re.M)


def load_notes() -> list[Note]:
    notes = []
    for p in sorted(ROOT.rglob("*.md")):
        rel = p.relative_to(ROOT).as_posix()
        if any(rel == d or rel.startswith(d + "/") for d in EXCLUDE_DIRS):
            continue
        text = p.read_text(encoding="utf-8")
        fm, raw, start = parse_frontmatter(text)
        n = Note(path=p, rel=rel, text=text, fm=fm, fm_raw=raw, body_start=start,
                 has_fm=bool(fm), is_doc=rel in doc_files(), is_index=p.name == "_index.md")
        n.blocks = list(fenced_blocks(text.split("\n")))
        notes.append(n)
    return notes


# --- Linting --------------------------------------------------------------------------


class Linter:
    def __init__(self, notes: list[Note]):
        self.notes = notes
        self.issues: list[Issue] = []
        self.md_by_stem: dict[str, list[Note]] = defaultdict(list)
        self.md_by_relnoext: dict[str, Note] = {}
        for n in notes:
            self.md_by_stem[n.path.stem.lower()].append(n)
            self.md_by_relnoext[n.rel[:-3].lower()] = n
        self.other_files = {
            p.relative_to(ROOT).as_posix().lower()
            for p in ROOT.rglob("*")
            if p.is_file() and p.suffix != ".md" and ".git" not in p.parts
        }
        self.inbound: dict[str, int] = defaultdict(int)
        self.defined_ids: set[str] = set()
        self._flag_refs: list[tuple[Note, int, str]] = []
        self.declared_flags: set[str] = set()

    def add(self, level, n, line, code, msg):
        self.issues.append(Issue(level, n.rel, line, code, msg))

    def load_tag_vocabulary(self):
        for n in self.notes:
            for info, _line, text in n.blocks:
                if info == TAG_BLOCK:
                    return parse_tag_vocabulary(text)
        return None

    def tag_home_candidates(self, tag: str) -> list[str]:
        home = self.tag_vocab["homes"].get(tag)
        return [home] if home else [tag, f"the-{tag}"]

    def check_tags(self, n: Note):
        """A tag must be in the vocabulary, and a naming tag must resolve to a note (R3)."""
        if n.is_doc or not n.has_fm or not self.tag_vocab:
            return
        raw = unquote(n.fm.get("tags", "")).strip()
        tags = [t.strip().strip("'\"") for t in raw.strip("[]").split(",") if t.strip()]
        rels = {other.rel[:-3] for other in self.notes}
        for tag in tags:
            if tag not in self.tag_vocab["tags"]:
                self.add("ERROR", n, 1, "TG001",
                         f"tag '{tag}' is not in the vocabulary (meta/tag-vocabulary.md)")
                continue
            if tag not in self.tag_vocab["naming"]:
                continue
            candidates = self.tag_home_candidates(tag)
            if not any(r == c or r.endswith("/" + c) for c in candidates for r in rels):
                self.add("WARN", n, 1, "TG002",
                         f"tag '{tag}' names no note (expected {' or '.join(candidates)})")

    # -- per-note checks

    def check_frontmatter(self, n: Note):
        if n.is_doc:
            return
        if not n.has_fm:
            self.add("ERROR", n, 1, "FM001", "missing frontmatter")
            return
        for k in REQUIRED:
            if k not in n.fm or n.fm[k] == "":
                self.add("ERROR", n, 1, "FM002", f"missing required field '{k}'")
        status = unquote(n.fm.get("status", ""))
        if status and status not in STATUS:
            self.add("ERROR", n, 1, "FM003", f"status '{status}' not in {sorted(STATUS)}")
        ns = unquote(n.fm.get("name_status", ""))
        if ns and ns not in NAME_STATUS:
            self.add("ERROR", n, 1, "FM004", f"name_status '{ns}' not in {sorted(NAME_STATUS)}")
        # FM005 (visibility vocabulary) is retired with the field itself (Step 2e).
        eng = unquote(n.fm.get("engine", ""))
        if eng and eng not in {"true", "false"}:
            self.add("ERROR", n, 1, "FM006", f"engine must be true or false, got '{eng}'")
        eras = era_vocabulary()
        era = unquote(n.fm.get("era", ""))
        if era and eras and era not in eras:
            self.add("WARN", n, 1, "FM007", f"era '{era}' not in {sorted(eras)}")
        for k in REQUIRED + ["t0", "official", "myth"]:
            if "REPLACE" in n.fm.get(k, "") and k in REQUIRED:
                self.add("ERROR", n, 1, "FM008", f"placeholder REPLACE in required field '{k}'")
        if status == "engine-ready" and eng != "true":
            self.add("ERROR", n, 1, "FM009", "status engine-ready requires engine: true")
        dis = unquote(n.fm.get("disclosure", ""))
        if dis and dis not in DISCLOSURE:
            self.add("ERROR", n, 1, "FM011", f"disclosure '{dis}' not in {sorted(DISCLOSURE)}")
        race = unquote(n.fm.get("race", ""))
        if race and not race.startswith("race_"):
            self.add("ERROR", n, 1, "FM010", f"race '{race}' must be a codex race id starting with 'race_'")
        elif race and race not in self.defined_ids:
            self.add("WARN", n, 1, "REF001", f"frontmatter 'race' references unknown id '{race}'")

        # id grammar and kind prefix
        nid, kind = unquote(n.fm.get("id", "")), unquote(n.fm.get("kind", ""))
        if nid:
            if not ID_RE.match(nid) or len(nid) > 100:
                self.add("ERROR", n, 1, "ID001", f"id '{nid}' breaks the id grammar")
            if kind in KIND_PREFIX and not nid.startswith(KIND_PREFIX[kind]):
                self.add("ERROR", n, 1, "ID002",
                         f"id '{nid}' should start with '{KIND_PREFIX[kind]}' for kind {kind}")
            elif kind and kind not in KIND_PREFIX:
                self.add("WARN", n, 1, "ID003", f"unknown kind '{kind}'")
        # filename is a kebab slug
        if not re.match(r"^_?[a-z0-9]+(-[a-z0-9]+)*$", n.path.stem):
            self.add("ERROR", n, 1, "FN001", f"filename '{n.path.name}' is not a kebab-case slug")

    def check_ids(self):
        seen: dict[str, Note] = {}
        for n in self.notes:
            nid = unquote(n.fm.get("id", "")) if n.has_fm else ""
            if not nid:
                continue
            self.defined_ids.add(nid)
            if nid in seen:
                self.add("ERROR", n, 1, "ID004", f"duplicate id '{nid}' (also {seen[nid].rel})")
            else:
                seen[nid] = n
        # filenames unique vault-wide (except _index.md and examples)
        by_name: dict[str, list[Note]] = defaultdict(list)
        for n in self.notes:
            if not n.is_index:
                by_name[n.path.name].append(n)
        for name, group in by_name.items():
            if len(group) > 1:
                for n in group:
                    others = ", ".join(g.rel for g in group if g is not n)
                    self.add("ERROR", n, 1, "FN002", f"filename '{name}' not unique (also {others})")

    def engine_blocks(self, n: Note):
        for info, line, text in n.blocks:
            if info in {"engine", "engine-example"}:
                yield info, line, text

    def check_engine(self, n: Note):
        if n.is_doc:
            return
        eng_true = unquote(n.fm.get("engine", "")) == "true"
        real = [b for b in self.engine_blocks(n) if b[0] == "engine"]
        if real and not eng_true:
            self.add("ERROR", n, real[0][1], "EN001", "has real `engine` blocks but engine: false")
        if eng_true and not real:
            self.add("ERROR", n, 1, "EN002", "engine: true but no `engine` block")
        for info, line, text in self.engine_blocks(n):
            level = "ERROR" if info == "engine" else "WARN"
            keys = top_level_keys(text)
            kind = ""
            m = re.search(r"^kind:\s*(\S+)", text, re.M)
            if m:
                kind = m.group(1)
            elif info == "engine":
                self.add("ERROR", n, line, "EN003", "engine block has no `kind`")
            for k in keys:
                if k in FORBIDDEN_ENGINE_KEYS:
                    self.add("ERROR", n, line, "EN004",
                             f"authored value '{k}' is derived/stamped and must not be written")
                if k == "world_id" and kind != "CAMPAIGN":
                    self.add("ERROR", n, line, "EN004", "world_id belongs only in a CAMPAIGN block")
            if info == "engine" and "REPLACE" in text:
                self.add("ERROR", n, line, "EN005", "placeholder REPLACE in a real `engine` block")
            # referenced ids must exist (checked after all ids are collected)
            for ref in set(ID_REF_RE.findall(text)):
                if "REPLACE" in ref or ref.endswith("_") or ref.endswith("_id") or ref in PREDICATE_NAMES:
                    continue
                n_refs = getattr(self, "_refs", None)
                if n_refs is None:
                    self._refs = []
                self._refs.append((level, n, line, ref))
            # effect-only flags must be declared in the World Flags note
            if info == "engine":
                for flag in set(re.findall(r"\bflag:\s*([a-z][a-z0-9_]*)", text)):
                    self._flag_refs.append((n, line, flag))

    def collect_declared_flags(self):
        """Flags declared in the `flags` block of the World Flags note."""
        for n in self.notes:
            for info, _line, text in n.blocks:
                if info == "flags":
                    self.declared_flags.update(re.findall(r"\bid:\s*([a-z][a-z0-9_]*)", text))

    def check_flag_refs(self):
        for n, line, flag in self._flag_refs:
            if flag not in self.declared_flags:
                self.add("ERROR", n, line, "EN007",
                         f"flag '{flag}' is not declared in a `flags` block (world/flags.md)")

    def collect_block_ids(self):
        """Ids declared inside engine/engine-example blocks count as defined."""
        for n in self.notes:
            if n.is_doc:
                continue
            for info, line, text in self.engine_blocks(n):
                # `id:` at top level, or inside an overlay's `adds:` list (indented / after "- ")
                for m in re.finditer(r"^[ \t]*(?:-[ \t]+)?id:\s*(\S+)", text, re.M):
                    self.defined_ids.add(m.group(1))
                # overland edges and relationships have no id; node ids are on `id:`

    def check_block_refs(self):
        for level, n, line, ref in getattr(self, "_refs", []):
            if ref not in self.defined_ids:
                self.add(level, n, line, "EN006", f"references id '{ref}' that no note defines")

    def check_group_refs(self, n: Note):
        """Group ids in frontmatter (group_knowledge, groups, home, zone) must exist."""
        if not n.has_fm:
            return
        for key in ("group_knowledge", "groups", "home", "zone", "parent"):
            for ref in set(ID_REF_RE.findall(n.fm.get(key, ""))):
                if "REPLACE" in ref:
                    continue
                if ref not in self.defined_ids:
                    self.add("WARN", n, 1, "REF001", f"frontmatter '{key}' references unknown id '{ref}'")

    def resolve(self, target: str):
        t = target.strip().replace("\\", "")
        t = t.split("#")[0].split("^")[0].strip()
        if not t:
            return "self"
        low = t.lower()
        if low.endswith(".md"):
            low = low[:-3]
        if "." in Path(low).name and f"{low}" in self.other_files:
            return "file"
        if "/" in low:
            hits = [n for rel, n in self.md_by_relnoext.items() if rel == low or rel.endswith("/" + low)]
            if len(hits) == 1:
                return hits[0]
            return "ambiguous" if hits else None
        hits = self.md_by_stem.get(low, [])
        if len(hits) == 1:
            return hits[0]
        if len(hits) > 1:
            return "ambiguous"
        # a non-md file linked without extension does not resolve in Obsidian
        if any(Path(f).stem == low for f in self.other_files):
            return "noext"
        return None

    def check_links(self, n: Note):
        clean = strip_code(n.text)
        for i, ln in enumerate(clean.split("\n"), 1):
            if ln.count("[[") != ln.count("]]"):
                self.add("ERROR", n, i, "LK001", "unbalanced [[ ]] on this line")
            if re.search(r"§(?!\d)", ln):
                self.add("ERROR", n, i, "LK002", "stray '§' (generator separator leaked into text)")
            for m in re.finditer(r"\[\[([^\[\]]+)\]\]", ln):
                inner = m.group(1)
                target = inner.split("|")[0]
                res = self.resolve(target)
                if res is None:
                    self.add("ERROR", n, i, "LK003", f"dead link [[{inner}]]")
                elif res == "ambiguous":
                    self.add("ERROR", n, i, "LK004", f"ambiguous link [[{inner}]] (use a folder path)")
                elif res == "noext":
                    self.add("ERROR", n, i, "LK005",
                             f"[[{inner}]] points at a non-Markdown file; Obsidian needs the extension")
                elif isinstance(res, Note) and res is not n:
                    self.inbound[res.rel] += 1

    def check_body(self, n: Note):
        if n.is_doc or not n.has_fm:
            return
        lines = n.text.split("\n")
        body = "\n".join(lines[n.body_start :])
        kind = unquote(n.fm.get("kind", ""))
        # H1 and summary
        h1 = re.search(r"^# (.+)$", body, re.M)
        if not h1:
            self.add("WARN", n, n.body_start + 1, "BD001", "no H1 heading")
        marker = "**Purpose:**" if kind == "INDEX" else "**Summary:**"
        if marker not in body:
            self.add("WARN", n, n.body_start + 1, "BD002", f"missing {marker} line")
        else:
            m = re.search(re.escape(marker) + r"\s*(.*)", body)
            if m and len(m.group(1).strip()) < 10:
                self.add("WARN", n, n.body_start + 1, "BD003", f"{marker} line is empty or truncated")
        # empty sections (a heading immediately followed by another heading)
        heads = [(i, ln) for i, ln in enumerate(lines) if re.match(r"^#{2,3} ", ln)]
        for (i, ln), nxt in zip(heads, heads[1:] + [(len(lines), "")]):
            seg = [x for x in lines[i + 1 : nxt[0]] if x.strip()]
            deeper = len(nxt[1]) - len(nxt[1].lstrip("#")) > len(ln) - len(ln.lstrip("#")) if nxt[1] else False
            if not seg and not deeper:
                self.add("WARN", n, i + 1, "BD004", f"empty section '{ln.strip()}'")
        # disclosure marks: `**Disclosure:** <class>` under a heading
        for i, ln in enumerate(strip_code(n.text).split("\n"), 1):
            m = re.match(r"^\*\*Disclosure:\*\*\s*([A-Za-z]*)", ln)
            if i > n.body_start and m and m.group(1).lower() not in DISCLOSURE:
                self.add("ERROR", n, i, "DS001", f"disclosure class '{m.group(1)}' not in {sorted(DISCLOSURE)}")
        # placeholders in prose
        for i, ln in enumerate(strip_code(n.text).split("\n"), 1):
            if i > n.body_start and re.search(r"\bREPLACE\b", ln):
                self.add("WARN", n, i, "BD005", "placeholder REPLACE left in prose")
        # Spelling, per the world's rule (`vault.spelling`; SP001)
        if spelling() == "british":
            for i, ln in enumerate(strip_code(n.text).split("\n"), 1):
                if i <= n.body_start:
                    continue
                ln_nolink = re.sub(r"\[\[[^\]]*\]\]", "", ln)
                for m in AMERICAN_RE.finditer(ln_nolink):
                    w = m.group(1).lower()
                    self.add("WARN", n, i, "SP001",
                             f"American spelling '{m.group(1)}' (use '{AMERICAN[w]}')")

    def check_orphans(self):
        for n in self.notes:
            if n.is_doc or n.rel in ("meta/canon-digest.md",):
                continue
            if self.inbound.get(n.rel, 0) == 0:
                self.add("WARN", n, 1, "OR001", "orphan: no note links to this one")

    def run(self, only: list[str] | None = None):
        self.collect_block_ids()
        self.collect_declared_flags()
        self.tag_vocab = self.load_tag_vocabulary()
        self.check_ids()
        for n in self.notes:
            self.check_frontmatter(n)
            self.check_tags(n)
            self.check_engine(n)
            self.check_group_refs(n)
            self.check_links(n)
            self.check_body(n)
        self.check_block_refs()
        self.check_flag_refs()
        self.check_orphans()
        if only:
            keep = tuple(only)
            self.issues = [i for i in self.issues if i.path.startswith(keep)]
        return self.issues


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Lint a world's vault.")
    ap.add_argument("paths", nargs="*", help="limit reporting to these paths (relative to the repo root)")
    ap.add_argument("--strict", action="store_true", help="warnings also fail the run")
    ap.add_argument("--json", action="store_true", help="output JSON")
    ap.add_argument("--errors-only", action="store_true", help="hide warnings")
    args = ap.parse_args(argv)

    only = []
    for p in args.paths:
        rel = Path(p).resolve().relative_to(ROOT).as_posix() if Path(p).exists() else p
        only.append(rel)
    issues = Linter(load_notes()).run(only or None)
    if args.errors_only:
        issues = [i for i in issues if i.level == "ERROR"]
    issues.sort(key=lambda i: (i.path, i.line, i.code))

    errors = sum(1 for i in issues if i.level == "ERROR")
    warns = sum(1 for i in issues if i.level == "WARN")
    if args.json:
        print(json.dumps([i.__dict__ for i in issues], indent=2))
    else:
        cur = None
        for i in issues:
            if i.path != cur:
                print(f"\n{i.path}")
                cur = i.path
            print(f"  {i.line:>4}  {i.level:<5} {i.code}  {i.msg}")
        n_files = len(load_notes())
        print(f"\n{n_files} notes checked: {errors} error(s), {warns} warning(s).")
    return 1 if errors or (args.strict and warns) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

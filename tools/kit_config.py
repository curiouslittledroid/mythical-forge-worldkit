#!/usr/bin/env python3
"""Read `world.config.yaml` and the world's vocabularies — the worldkit's config seam (T1).

The worldkit is world-agnostic. Every world-specific value lives in one of two places:

* **`world.config.yaml`** at the vault root — repo identity, the ids of the notes the tools need,
  the feature switches, and the site's plumbing. This module reads it.
* **fenced blocks in vault notes** — the vocabularies that are *lore* decisions and change as the
  canon grows (`eras`, `chronology`, `site-vocabulary`, `tags-vocabulary`). Obsidian-editable,
  lint-enforced, versioned with the lore. `block()` reads them.

Standard library only, so the linter and the exporters can import it without a dependency.

    import kit_config
    cfg = kit_config.load()                    # the vault this file is installed in
    cfg = kit_config.load("/elsewhere/world.config.yaml")

    cfg.root                cfg.world_id      cfg.title        cfg.slug
    cfg.overland_id         cfg.game_ready_repo
    cfg.has("site")         cfg.require("testimony")
    cfg.path_of("flags")    cfg.block("eras")  cfg.block("chronology")
    cfg.site.sections       cfg.site.deferred_kinds
    cfg.process_docs

Design rules this module exists to enforce:

* **Ids, not paths** (D12). `path_of("flags")` resolves `vault.notes.flags` to a path by scanning
  frontmatter. Nothing else in the kit hardcodes a note's path.
* **Inert when absent** (D14, D15). A missing feature or a missing block is not a crash; the
  consumer decides. `require()` is for the cases where it genuinely cannot continue.
* **Fail loudly on a typo.** An unknown key is a `ConfigError`, never a silently ignored setting.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml_subset

# The vault directories a note id can live in. A world does not renames these (D13).
SCOPE_DIRS = ("principles", "world", "campaigns", "maps", "meta")

FEATURES = {"site", "atlas", "testimony", "voice"}
SPELLING = {"british", "american", "off"}

# config note name -> the info string of the block that note must carry
BLOCK_INFO = {
    "flags": "flags",
    "calendar": "chronology",
    "eras": "eras",
    "site_vocabulary": "site-vocabulary",
}

_TOP_KEYS = {"version", "world", "vault", "features", "site"}
_WORLD_KEYS = {"id", "title", "slug", "tagline", "description", "author", "license", "overland",
               "game_ready_repo"}
_VAULT_KEYS = {"notes", "process_docs", "scenarios", "spelling"}
_SITE_KEYS = {"url", "buttondown_user", "hero_alt", "hero_credit", "deferred_kinds", "sections",
              # The theme reads these from `site.json`, so a world's look and copy never live in
              # the theme's source: navigation cards, the engine's content descriptors, and what
              # the world calls its year zero.
              "content_descriptors", "t0_prefix", "t0_epoch", "doorways", "hero_file",
              "search_placeholder"}
_SECTION_KEYS = {"slug", "label", "kinds", "blurb"}
_DOORWAY_KEYS = {"href", "label", "blurb"}

_FM_ID_RE = re.compile(r"^---\s*\n(.*?)\n---\s*(\n|$)", re.S)
_ID_LINE_RE = re.compile(r"^id:\s*(\S+)\s*$", re.M)


class ConfigError(Exception):
    """The world's config is missing, malformed, or contradicts itself."""


@dataclass(frozen=True)
class Section:
    slug: str
    label: str
    kinds: tuple[str, ...]
    blurb: str = ""


@dataclass
@dataclass(frozen=True)
class Doorway:
    """A card on the landing page. The world's copy; the theme renders it."""
    href: str
    label: str
    blurb: str = ""


@dataclass(frozen=True)
class Site:
    url: str
    buttondown_user: str
    hero_alt: str
    hero_credit: str
    sections: tuple[Section, ...]
    deferred_kinds: frozenset[str] = field(default_factory=frozenset)
    # --- what the theme needs and must not hardcode ---
    content_descriptors: tuple[str, ...] = ()
    # The year-zero prefix and its name in prose ("T0", "the Severing"). The theme formats a page's
    # offset; what the zero *means* is the world's.
    t0_prefix: str = "T0"
    t0_epoch: str = ""
    doorways: tuple[Doorway, ...] = ()
    # The hero image's basename in public/img/, without an extension: `hero` finds hero.webp;
    # `hero-dust-road` finds hero-dust-road.webp. The world names its own art.
    hero_file: str = "hero"
    # The search box's hint. The world's, because the useful examples are its own vocabulary.
    search_placeholder: str = "Search the codex"

    def label_of(self, slug: str) -> str:
        for s in self.sections:
            if s.slug == slug:
                return s.label
        return slug

    def section_of_kind(self, kind: str) -> str | None:
        """The slug of the first section that owns this note kind."""
        for s in self.sections:
            if kind in s.kinds:
                return s.slug
        return None


class Config:
    """The resolved world. Built by `load()`; hold it, do not re-read it per note."""

    def __init__(self, data: dict, path: Path):
        self.path = path
        self.root = path.parent
        self._data = data
        self._id_index: dict[str, Path] | None = None
        self._blocks: dict[str, dict | list | None] = {}

        self._validate()

        w = data.get("world", {})
        self.world_id: str = w["id"]
        self.title: str = w["title"]
        self.slug: str = w["slug"]
        self.tagline: str = w.get("tagline", "")
        self.description: str = w.get("description", "")
        self.author: str = w.get("author", "")
        self.license: str = w.get("license", "")
        # `overland` defaults to overland_<id without its world_ prefix> (T1 schema note 3).
        self.overland_id: str = w.get("overland") or "overland_" + self.world_id.removeprefix("world_")
        self.game_ready_repo: Path = (self.root / w.get("game_ready_repo", "")).resolve() \
            if w.get("game_ready_repo") else self.root.parent / f"{self.slug}-gameready"

        self.features: frozenset[str] = frozenset(data.get("features", []))
        self._vault: dict = data.get("vault", {})
        self._note_ids: dict[str, str] = dict(self._vault.get("notes", {}))
        self.process_docs: frozenset[str] = frozenset(self._vault.get("process_docs", []))
        # The one world-declared directory (T4): scenarios are world content, so unlike the vault
        # layout they are named by the world. None when the world has none.
        self.spelling: str = str(self._vault.get("spelling", "british")).lower()
        self.scenarios_dir: Path | None = (
            (self.root / self._vault["scenarios"]).resolve() if self._vault.get("scenarios") else None)

        site = data.get("site")
        self.site: Site | None = None
        if site is not None:
            self.site = Site(
                url=site.get("url", ""),
                buttondown_user=site.get("buttondown_user", ""),
                hero_alt=site.get("hero_alt", ""),
                hero_credit=site.get("hero_credit", ""),
                sections=tuple(Section(s["slug"], s["label"], tuple(s["kinds"]), s.get("blurb", ""))
                               for s in site.get("sections", [])),
                deferred_kinds=frozenset(site.get("deferred_kinds", [])),
                content_descriptors=tuple(site.get("content_descriptors", [])),
                t0_prefix=site.get("t0_prefix", "T0"),
                t0_epoch=site.get("t0_epoch", ""),
                doorways=tuple(Doorway(d["href"], d["label"], d.get("blurb", ""))
                               for d in site.get("doorways", [])),
                hero_file=site.get("hero_file", "hero"),
                search_placeholder=site.get("search_placeholder", "Search the codex"),
            )

    # --- validation -------------------------------------------------------------------

    def _validate(self) -> None:
        if not isinstance(self._data, dict):
            raise ConfigError(f"{self.path}: the file is not a mapping")
        _reject_unknown(self._data, _TOP_KEYS, self.path, "")
        if self._data.get("version") != 1:
            raise ConfigError(f"{self.path}: version must be 1, found {self._data.get('version')!r}")

        world = self._data.get("world")
        if not isinstance(world, dict):
            raise ConfigError(f"{self.path}: `world:` is missing")
        _reject_unknown(world, _WORLD_KEYS, self.path, "world")
        for key in ("id", "title", "slug"):
            if not world.get(key):
                raise ConfigError(f"{self.path}: world.{key} is required")

        vault = self._data.get("vault")
        if not isinstance(vault, dict):
            raise ConfigError(f"{self.path}: `vault:` is missing")
        _reject_unknown(vault, _VAULT_KEYS, self.path, "vault")
        notes = vault.get("notes")
        if not isinstance(notes, dict) or not notes.get("flags"):
            raise ConfigError(f"{self.path}: vault.notes.flags is required (by id, e.g. topic_world_flags)")
        for key in notes:
            if key not in BLOCK_INFO and key != "testimony_book":
                raise ConfigError(
                    f"{self.path}: vault.notes.{key} is not a note the kit reads "
                    f"(known: {', '.join(sorted(BLOCK_INFO) + ['testimony_book'])})")

        spelling = self._data.get("vault", {}).get("spelling", "british")
        if str(spelling).lower() not in SPELLING:
            raise ConfigError(f"{self.path}: vault.spelling must be one of {sorted(SPELLING)}, "
                              f"found {spelling!r}")

        features = self._data.get("features")
        if not isinstance(features, list):
            raise ConfigError(f"{self.path}: `features:` must be a list, e.g. [site, atlas]")
        unknown = sorted(set(features) - FEATURES)
        if unknown:
            raise ConfigError(f"{self.path}: unknown feature(s) {unknown}; known: {sorted(FEATURES)}")

        site = self._data.get("site")
        if site is not None:
            _reject_unknown(site, _SITE_KEYS, self.path, "site")
            if "site" not in features:
                raise ConfigError(f"{self.path}: a `site:` section needs the `site` feature")
            if not site.get("url"):
                raise ConfigError(f"{self.path}: site.url is required")
            for i, s in enumerate(site.get("sections", [])):
                where = f"site.sections[{i}]"
                if not isinstance(s, dict):
                    raise ConfigError(f"{self.path}: {where} is not a mapping")
                _reject_unknown(s, _SECTION_KEYS, self.path, where)
                for key in ("slug", "label", "kinds"):
                    if not s.get(key):
                        raise ConfigError(f"{self.path}: {where}.{key} is required")
        elif "site" in features:
            raise ConfigError(f"{self.path}: the `site` feature needs a `site:` section")

    # --- features ---------------------------------------------------------------------

    def has(self, feature: str) -> bool:
        return feature in self.features

    def require(self, feature: str) -> None:
        """Raise unless the feature is on. Call this in the tool that owns the feature."""
        if feature not in self.features:
            raise ConfigError(
                f"{self.path}: this tool needs the '{feature}' feature; add it to `features:`")

    # --- notes and blocks -------------------------------------------------------------

    def id_index(self) -> dict[str, Path]:
        """Every note id in the vault -> its path. Built once, on first use."""
        if self._id_index is None:
            index: dict[str, Path] = {}
            for scope in SCOPE_DIRS:
                base = self.root / scope
                if not base.is_dir():
                    continue
                for path in sorted(base.rglob("*.md")):
                    try:
                        head = path.read_text(encoding="utf-8")[:2000]
                    except OSError:
                        continue
                    m = _FM_ID_RE.match(head)
                    if not m:
                        continue
                    idm = _ID_LINE_RE.search(m.group(1))
                    if idm:
                        index.setdefault(idm.group(1), path)
            self._id_index = index
        return self._id_index

    def path_of(self, name: str) -> Path | None:
        """The path of the note named in `vault.notes.<name>`, or None if it is not there."""
        note_id = self._note_ids.get(name)
        if not note_id:
            return None
        return self.id_index().get(note_id)

    def block(self, name: str) -> dict | list | None:
        """Parse the block that note `name` carries — a mapping, or a list (`flags` is one).

        None when the note or the block is absent.

        The info string for each note is fixed by the kit (`BLOCK_INFO`), so a world declares
        *which note* and the kit knows *what to look for*.
        """
        if name in self._blocks:
            return self._blocks[name]
        result: dict | list | None = None
        info = BLOCK_INFO.get(name)
        path = self.path_of(name) if info else None
        if path is not None:
            raw = read_block(path, info)
            if raw is not None:
                try:
                    parsed = yaml_subset.load_text(raw, f"{path} ({info} block)")
                except yaml_subset.SchemaError as exc:
                    raise ConfigError(str(exc)) from exc
                result = parsed if isinstance(parsed, (dict, list)) else None
        self._blocks[name] = result
        return result

    def required_block(self, name: str) -> dict | list:
        got = self.block(name)
        if got is None:
            note = self._note_ids.get(name, "(unset)")
            raise ConfigError(
                f"the '{BLOCK_INFO.get(name, name)}' block is missing: vault.notes.{name} is "
                f"{note}, and that note must carry the block")
        return got


def _reject_unknown(mapping: dict, allowed: set[str], path: Path, where: str) -> None:
    unknown = sorted(set(mapping) - allowed)
    if unknown:
        prefix = f"{where}." if where else ""
        raise ConfigError(
            f"{path}: unknown key(s) {[prefix + k for k in unknown]}; "
            f"expected only {sorted(allowed)}")


FENCE_RE = re.compile(r"^```(\S+)[ \t]*\n(.*?)^```[ \t]*$", re.M | re.S)


def read_block(path: Path, info: str) -> str | None:
    """The text of the first fenced block in `path` whose info string is `info`."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    for m in FENCE_RE.finditer(text):
        if m.group(1) == info:
            return m.group(2)
    return None


#: root -> (config mtime in ns, Config or None). Keyed on the mtime as well as the root, so a
#: config rewritten under a running tool is picked up instead of silently ignored.
_CACHE: dict[Path, tuple[int, "Config | None"]] = {}


def for_root(root: str | os.PathLike) -> "Config | None":
    """The config for a vault root, or None when that vault has none. Cached per root and mtime.

    Tools call this rather than `load()`: a bare vault (a test fixture, or the worldkit's own
    examples) still has to work, and a tool that reads `lint.ROOT` at call time stays
    testable. A config that exists but is broken still raises — only *absence* is silent.
    """
    root = Path(root).resolve()
    path = root / "world.config.yaml"
    stamp = path.stat().st_mtime_ns if path.is_file() else -1
    hit = _CACHE.get(root)
    if hit is not None and hit[0] == stamp:
        return hit[1]
    cfg = load(path) if stamp != -1 else None
    _CACHE[root] = (stamp, cfg)
    return cfg


def load_optional(path: str | os.PathLike | None = None) -> "Config | None":
    """`load`, but None when there is no config file at that path."""
    if path is not None and not Path(path).is_file():
        return None
    return load(path)


def load(path: str | os.PathLike | None = None) -> Config:
    """Resolve and read a world's config.

    Order: the argument, then $WORLD_CONFIG, then `world.config.yaml` beside the repo that holds
    this file. The repo root is the config's own directory, so a tool can be run from anywhere.
    """
    if path is None:
        path = os.environ.get("WORLD_CONFIG")
    if path is None:
        path = Path(__file__).resolve().parent.parent / "world.config.yaml"
    path = Path(path).resolve()
    if not path.is_file():
        raise ConfigError(f"no world config at {path} (set $WORLD_CONFIG to point at one)")
    try:
        data = yaml_subset.load(path)
    except yaml_subset.SchemaError as exc:
        raise ConfigError(str(exc)) from exc
    return Config(data, path)


if __name__ == "__main__":
    cfg = load()
    print(f"{cfg.title} ({cfg.world_id})")
    print(f"  root            {cfg.root}")
    print(f"  game ready      {cfg.game_ready_repo}")
    print(f"  features        {', '.join(sorted(cfg.features))}")
    print(f"  notes           {len(cfg.id_index())} ids indexed")
    print(f"  scenarios       {cfg.scenarios_dir or '(none declared)'}")
    print(f"  spelling        {cfg.spelling}")
    for name in BLOCK_INFO:
        got = cfg.block(name)
        if got is None:
            state = "(no block)"
        elif isinstance(got, list):
            state = f"{len(got)} item(s)"
        else:
            state = f"{len(got)} key(s): {', '.join(got)}"
        print(f"  {name:16}{state}")
    if cfg.site:
        print(f"  site            {cfg.site.url} ({len(cfg.site.sections)} sections)")

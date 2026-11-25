#!/usr/bin/env python3
"""Export the player-facing view of the codex for the public site (roadmap Step 16).

The rules this implements live in `docs/site.md` section 2. In one line: **publish the
`open` part of every section, and nothing else.** Standard library only.

    python3 tools/site_export.py              # build into site/
    python3 tools/site_export.py --dry-run    # report only, write nothing
    python3 tools/site_export.py --check      # exit 1 on an ambiguous link (a real bug)
    python3 tools/site_export.py --out DIR --data DIR --audit FILE

Output

    site/src/content/generated/<section>/<slug>.md   one file per published page
    site/src/data/generated/site.json                branding and site settings
    site/src/data/generated/navigation.json          sections, labels, counts
    site/src/data/generated/changelog.json           recently added / updated
    site/src/data/generated/redirects.json           old slug -> current slug
    site/audit/latest.json                           what was published, and why (COMMIT THIS)
    site/audit/history.json                          slug history, dates, content hashes

Design rules

- **`disclosure.classify` is imported, never re-derived** (conventions section 7). One
  classifier, two consumers.
- **Deny by default.** A section is published only if its effective class is `open`, or
  `mixed` (a layered history event), whose open part is its Official/Myth/Rival segments.
- **The exporter never authors canon.** It moves, splits and strips; it never writes prose.
- **Every dropped line, link and section is logged** in the audit. A build may be deployed
  only after a human has read it (`docs/site.md` section 2.3).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import disclosure  # noqa: E402
import kit_config  # noqa: E402
import lint  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
LORE_ROOT = "world/"

# --- The world's configuration (T1) -------------------------------------------------------
# Every world-specific value comes from world.config.yaml and the `site-vocabulary` block, so the
# exporter follows whichever world it is pointed at. `_reload()` runs at each entry point; the
# test suite points lint.ROOT at a fixture vault and builds there.

CFG: "kit_config.Config | None" = None
# (url slug, nav label, note kinds, blurb). Order is the navigation order.
SECTIONS: list[tuple[str, str, tuple[str, ...], str]] = []
SECTION_OF_KIND: dict[str, str] = {}
SECTION_LABEL: dict[str, str] = {}
# Phase 4 only: NPC pages are not part of the first launch.
DEFERRED_KINDS: set[str] = set()
# Sealed keystones (conventions section 7.4). Published text is scanned for these; a hit is a line
# for a human to read, not necessarily a leak. docs/site.md section 2.3 points here.
KEYSTONE_TERMS: tuple[str, ...] = ()
# The tags that earn an index page. The vault stays the source of truth: add a tag here only when
# it earns a page, and never one that no note carries.
PUBLISHED_TAGS: tuple[str, ...] = ()
# Thread surfaces that are also ordinary in-world vocabulary, so their appearance in open prose is
# not a leak. Each needs a reason; anything else is reported and moved to `## Hooks`.
REVIEWED_PLOT_WEB_SURFACES: set[str] = set()
# The world's player-facing copy that the theme renders: the tone statement, and how its tags read.
WHAT_TO_EXPECT: tuple[str, ...] = ()
TAG_LABELS: dict[str, str] = {}
# The world's date pattern. Built from `chronology.date_prefix`; the literal here is only the
# pre-`_reload()` placeholder, for a helper called outside an entry point.
TAKEN_RE: "re.Pattern[str]" = re.compile(r"\bCY\s*(\d{2,4})\b")

# Link targets that are design material, not lore: the link goes, the words stay.
INFRASTRUCTURE_PREFIXES = ("campaigns/", "world/plot-web/", "meta/", "maps/", "principles/")
INFRASTRUCTURE_FILES: set[str] = set()

# A layered history event: the three attributed views that publish, and the one that never does.
# Kit vocabulary (conventions section 7), not world vocabulary.
LAYER_LABELS = ("Official", "Myth", "Rival")
TRUTH_LABEL = "Truth"
YAML_BOOLEANS = {"true", "false"}


def _rel_of(name: str) -> str | None:
    """A config note name as a path relative to the vault root, or None when it has no note."""
    path = CFG.path_of(name) if CFG else None
    return path.relative_to(CFG.root).as_posix() if path else None


def _reload() -> None:
    """Re-read the world's config, so the exporter never mixes two worlds' settings."""
    global CFG, SECTIONS, SECTION_OF_KIND, SECTION_LABEL, DEFERRED_KINDS, KEYSTONE_TERMS
    global PUBLISHED_TAGS, REVIEWED_PLOT_WEB_SURFACES, INFRASTRUCTURE_FILES, TAKEN_RE
    global WHAT_TO_EXPECT, TAG_LABELS
    CFG = lint.world_config()
    if CFG is None:
        raise SystemExit(f"no world.config.yaml in {lint.ROOT}: the site exporter needs one")
    CFG.require("site")
    # (slug, label, kinds, blurb): the blurb is the world's one-line description of the section,
    # shown on its index page. The theme has no opinion about any section's contents.
    SECTIONS = [(s.slug, s.label, s.kinds, s.blurb) for s in CFG.site.sections]
    SECTION_OF_KIND = {kind: slug for slug, _, kinds, _b in SECTIONS for kind in kinds}
    SECTION_LABEL = {slug: label for slug, label, _k, _b in SECTIONS}
    DEFERRED_KINDS = set(CFG.site.deferred_kinds)
    vocab = CFG.block("site_vocabulary") or {}
    KEYSTONE_TERMS = tuple(vocab.get("keystones", ()))
    PUBLISHED_TAGS = tuple(vocab.get("published_tags", ()))
    REVIEWED_PLOT_WEB_SURFACES = set(vocab.get("plot_web_surfaces", ()))
    # Player-facing copy the theme renders but must not author (the world's tone statement, and how
    # its tags read). A world that declares neither gets an empty list and title-cased tag slugs.
    WHAT_TO_EXPECT = tuple(vocab.get("what_to_expect", ()))
    TAG_LABELS = dict(vocab.get("tag_labels", {}))
    INFRASTRUCTURE_FILES = {rel for rel in (_rel_of("flags"),) if rel}
    prefix = str((CFG.block("calendar") or {}).get("date_prefix", "CY"))
    TAKEN_RE = re.compile(rf"\b{re.escape(prefix)}\s*(\d{{2,4}})\b")


# --- Patterns ----------------------------------------------------------------------------

LINK_RE = re.compile(r"\[\[([^\[\]]+?)\]\]")
# Authoring annotations, which are design notes rather than lore. Stripped from headings, bold
# lead-ins and prose alike: `(decided, Step 5, Round 1)`, `(Step 2)`, `(mechanics gap register)`.
ANNOTATION_RE = re.compile(
    r"\s*\((?:decided|agreed|defined)\b[^)]*\)"
    r"|\s*\(Step \d+\b[^)]*\)"
    r"|\s*\((?:mechanics gap register|see conventions[^)]*|see canon-digest[^)]*|OPEN)\)",
    re.IGNORECASE,
)
H1_RE = re.compile(r"^#\s+.*$", re.MULTILINE)
LAYER_LINE_RE = re.compile(r"\*\*(Official|Myth|Rival|Truth)\b[^*:]*:\*\*")
STRIP_LINE_RE = re.compile(r"^\s*(?:[-*+]\s+)?\*\*(?:Disclosure|Reveal when)\b[^*]*:\*\*")
WANT_LINE_RE = re.compile(r"^\s*(?:[-*+]\s+)?\*\*Wants?\b[^*]*:\*\*")
EMPTY_PARENS_RE = re.compile(r"[ \t]*\(\s*\)")

# --- Testimony (Step 16) ------------------------------------------------------------------
#
# A `## Testimony` section is an account quoted from the Reader's book (world/items-materials/
# the-readers-book.md): first person, in a named teller's voice, longer than a Folklore and not
# the page's own voice. It is not published as a body section. It is lifted into `testimony:`
# in the page's frontmatter, so that the layout can show a pull-quote at the head and the whole
# account after the body, and so that the book's page can assemble every account in one place.
#
# Its first line is the entry heading, written in the Reader's own voice and always in his order:
# **the date, then the person, then the place**, then how it reached him.
#
#     **CY 649, in the BLAZE.** **Sabel Cray**, at the slips in Dustport — told to me.
#
# The `CY <n>` year is parsed into `taken`. It orders the accounts, decides which volume of the
# book an account falls in, and tells `tools/voice_stale.py` whether an account is expected to
# describe the present. An account with no year silently claims to be current, so it is reported.
# The teller is the first bold run **that is not the date**, so a heading may open with either.
#
# See docs/testimony.md section 3.4.
TESTIMONY_HEADING = "testimony"
TESTIMONY_RANGE_RE = re.compile(r"^\s*(\d{2,4})\s*[-–]\s*(\d{2,4})\s*$")
# `**CY 649, in the BLAZE.**` — the date's own bold run, at the head of the line.
LEAD_DATE_RE = re.compile(r"^\s*\*\*[^*]*\bCY\s*\d{2,4}[^*]*\*\*[.,;:]?\s*")
# He is often working from memory or from letters, and he says so rather than pretending to a
# clerk's precision — which is why a copied account reads `CY 601, or near it`. The hedge is his,
# so the site must not print the year as if he had been sure: the byline becomes `c. CY 601`.
# A closed list, like every other vocabulary in this exporter.
APPROX_PHRASES = (
    "or near it",
    "or thereabouts",
    "as near as i can make it",
    "as near as i can",
    "i make it",
    "my best reckoning",
    "so far as i know",
    "i cannot be sure",
)
TELLER_RE = re.compile(
    r"^\s*\*\*(?P<teller>[^*]+?)\*\*\s*[,;:—–-]?\s*(?P<rest>.*)$", re.MULTILINE
)
QUOTE_RE = re.compile(r"^\s*\*\*Quote:\*\*\s*(?P<quote>.+)$", re.MULTILINE)
QUOTE_MAX = 220

# Design vocabulary that has no place on a player page: register ids, section refs and
# engine-mapping asides. Published text is scrubbed of them and the note is listed in the
# audit as `internal_references`, for the prose to be fixed at source (meta/site.md 2.2).
DESIGN_TOKEN = (r"\b(?:CP|PR|PF|DT|S|FM|DS|ID|LK|EN|REF)-\d{1,3}\b"
                r"|\b[MV]\d{1,2}\b"
                r"|§\s?\d+(?:\.\d+)*")
DESIGN_PAREN_RE = re.compile(
    r"\s*\([^)]*?(?:" + DESIGN_TOKEN + r"|conventions|gap register|canon-digest|the register)[^)]*?\)",
    re.IGNORECASE)
DESIGN_TOKEN_RE = re.compile(DESIGN_TOKEN)
# "…are still [OPEN] for Step 12/15." — a roadmap reference in lore prose. Expected to be zero
# once the prose is fixed; scrubbed and logged as a guard (meta/site.md 2.2).
STEP_SENTENCE_RE = re.compile(r"[^.\n]*\bStep \d+(?:/\d+)?\b[^.\n]*\.?[ \t]*")
DESIGN_FIELD_RE = re.compile(r"^\s*(?:[-*+]\s+)?\*\*[^*]+:\*\*[\s.,;:()]*$")
# Engine-facing fields that are not lore: `- **SRD base:** a blade`, `| **Engine form** | ... |`.
DESIGN_FIELDS = {"srd base", "nearest srd 3.5", "templates", "srd race", "engine", "engine form", "engine mapping", "engine id"}
DESIGN_LABEL_RE = re.compile(
    r"^\s*(?:[-*+]\s+|\|\s*)?\*\*([^*:]+?):?\*\*")
SUMMARY_LABEL_RE = re.compile(r"^\s*\*\*Summary:\*\*\s*")


# --- Small helpers -----------------------------------------------------------------------

def slug_of(rel: str) -> str:
    return Path(rel).stem


def section_of(kind: str) -> str | None:
    return SECTION_OF_KIND.get(kind)


def url_of(section: str, slug: str) -> str:
    return f"/{section}/{slug}/"


def humanise(text: str) -> str:
    return text.replace("-", " ").replace("_", " ").strip()


def content_hash(*parts: str) -> str:
    """Hash the published text, ignoring trailing whitespace, so an editor that strips or adds
    a trailing space does not register as a lore revision in the changelog."""
    normalised = ["\n".join(line.rstrip() for line in part.split("\n")) for part in parts]
    h = hashlib.sha256("\x00".join(normalised).encode("utf-8"))
    return h.hexdigest()[:12]


def sanitise_text(text: str) -> str:
    """Strip authoring annotations from prose: `**Two layers (decided, Step 2).**`."""
    return ANNOTATION_RE.sub("", text)


def sanitise_heading(heading: str) -> str:
    """`Culture (decided, Step 5, Round 1)` -> `Culture`."""
    return sanitise_text(heading).strip()


def strip_markers(line: str, kind: str) -> str | None:
    """Remove an authoring marker line, or an `[OPEN]` marker inside a line.

    `**Want(s):**` is stripped only in an NPC note: that is the rule in conventions section
    7.3 (an NPC's motive is `earned`, audience that NPC only). A god's `**Wants now:**` is
    public doctrine and stays. Returns None when the line is nothing but a marker.
    """
    if not line.strip():
        return line
    if STRIP_LINE_RE.match(line):
        return None
    if kind == "NPC" and WANT_LINE_RE.match(line):
        return None
    return line.replace("[OPEN]", "").rstrip()


def split_layers(line: str) -> list[tuple[str, str]]:
    """Split one line into (label, text) segments at **Official:** / **Myth:** / **Rival:** /
    **Truth:** markers. Text before the first marker is returned with the label ""."""
    line = re.sub(r"^\s*[-*+]\s+", "", line)  # a bullet is not part of the words
    if not LAYER_LINE_RE.search(line):
        return [("", line)]
    out: list[tuple[str, str]] = []
    pos = 0
    for m in LAYER_LINE_RE.finditer(line):
        before = line[pos : m.start()].strip()
        if before:
            out.append((out[-1][0] if out else "", before))
        out.append((m.group(1), ""))
        pos = m.end()
    tail = line[pos:].strip()
    if tail:
        label = out[-1][0] if out else ""
        out[-1] = (label, tail)
    return [(label, text) for label, text in out if text]


# --- The vault index and link resolution --------------------------------------------------

@dataclass
class Index:
    by_rel: dict[str, lint.Note] = field(default_factory=dict)
    by_stem: dict[str, list[lint.Note]] = field(default_factory=dict)
    by_id: dict[str, lint.Note] = field(default_factory=dict)
    _publishable: dict[str, bool] = field(default_factory=dict)

    @classmethod
    def build(cls, notes: list[lint.Note]) -> "Index":
        idx = cls()
        for n in notes:
            idx.by_rel[n.rel[:-3]] = n  # drop '.md'
            idx.by_stem.setdefault(slug_of(n.rel), []).append(n)
            note_id = lint.unquote(n.fm.get("id", ""))
            if note_id:
                idx.by_id[note_id] = n
        return idx

    def publishable(self, note: lint.Note) -> bool:
        if note.rel not in self._publishable:
            self._publishable[note.rel] = publishable(note)
        return self._publishable[note.rel]

    def sections_with_pages(self) -> set[str]:
        """Sections that will have at least one page (a nav link must never 404)."""
        if not hasattr(self, "_sections"):
            self._sections = {
                section_of(lint.unquote(n.fm.get("kind", "")))
                for n in self.by_rel.values()
                if n.has_fm and self.publishable(n)
            }
            self._sections.discard(None)
        return self._sections

    def section_for_index(self, note: lint.Note) -> str | None:
        """A map-of-content note (`gods/_index`) points at the section its folder publishes.

        `world/gods/_index` -> `gods`; `world/cosmology/_index` -> `world` (via its members).
        """
        folder = Path(note.rel).parent.as_posix()
        direct = Path(folder).name
        if direct in {slug for slug, _, _k, _b in SECTIONS} and direct in self.sections_with_pages():
            return direct
        members = [n for n in self.by_rel.values() if Path(n.rel).parent.as_posix() == folder]
        sections = {section_of(lint.unquote(n.fm.get("kind", ""))) for n in members if n.has_fm}
        sections.discard(None)
        if len(sections) == 1:
            return sections.pop()
        return None

    def lookup(self, target: str) -> tuple[lint.Note | None, str]:
        """Return (note, problem). `problem` is '', 'ambiguous' or 'unresolved'.

        Resolution order: exact path, path under `world/` (the common short form, e.g.
        `gods/_index`), a unique path suffix, an `id:`, then a unique filename.
        """
        target = target.rstrip("\\").strip()
        if target in self.by_rel:
            return self.by_rel[target], ""
        if LORE_ROOT + target in self.by_rel:
            return self.by_rel[LORE_ROOT + target], ""
        if target in self.by_id:
            return self.by_id[target], ""
        suffix = [n for rel, n in self.by_rel.items() if rel.endswith("/" + target)]
        if len(suffix) == 1:
            return suffix[0], ""
        if len(suffix) > 1:
            return None, "ambiguous"
        cands = self.by_stem.get(slug_of(target), [])
        if len(cands) == 1:
            return cands[0], ""
        if len(cands) > 1:
            # `_index` and duplicate stems: prefer the one in the same folder as the target.
            same = [c for c in cands if c.rel[:-3] == target]
            if len(same) == 1:
                return same[0], ""
            return None, "ambiguous"
        return None, "unresolved"


def parse_link(inner: str) -> tuple[str, str | None]:
    """`target#anchor|Label` -> (target, label). Handles the table escape `\\|`."""
    inner = inner.replace("\\|", "|")
    target, _, label = inner.partition("|")
    target = target.split("#", 1)[0].strip()
    label = label.strip() if label else None
    return target, (label or None)


ARTICLE_RE = re.compile(r"^(?:the|a|an)\s+", re.I)


def plot_web_names(index: Index) -> list[tuple[str, str]]:
    """Every plot-web thread's title and aliases, as (name, note.rel), longest first.

    A thread link in lore prose is already caught by `render_links` (it flattens as
    `infrastructure`). What that rule cannot see is the thread's **name written as plain
    text**, which reaches the site as an orphaned proper noun: the reader sees "the
    Uncovering" mentioned and no page to open. GM-side thread references belong under
    `## Hooks`, which is not lore and never publishes (conventions section 7.3).

    The leading article is dropped, so `The Great Rush` is policed as `Great Rush`: the
    name matters in any sentence position, and matching only the article-carrying form
    would miss every mid-sentence use.
    """
    names: list[tuple[str, str]] = []
    for note in index.by_rel.values():
        if not note.rel.startswith("world/plot-web/") or not note.has_fm:
            continue
        surfaces = [lint.unquote(note.fm.get("title", ""))]
        aliases = lint.unquote(note.fm.get("aliases", ""))
        surfaces += [a.strip().strip('"') for a in aliases.strip("[]").split(",") if a.strip()]
        for surface in surfaces:
            name = ARTICLE_RE.sub("", surface).strip()
            if len(name) > 5:  # a two-word name shorter than this is too generic to police
                names.append((name, note.rel))
    return sorted(names, key=lambda pair: -len(pair[0]))


def log_plot_web_mentions(text: str, page_slug: str, names: list[tuple[str, str]], log: dict) -> None:
    """Record thread names written as plain text, i.e. leaks that flatten nothing.

    Matching is case-sensitive: only a name used *as a proper noun* reads to a player as a
    missing page. Lowercase prose that happens to share a thread's words is English, not a
    leak (the Choir being "not monolithic" is not a mention of the thread of that name).
    """
    prose = LINK_RE.sub(" ", text)  # a linked mention is `render_links`' business, not ours
    for name, rel in names:
        if name.lower() in REVIEWED_PLOT_WEB_SURFACES:
            continue
        pattern = r"(?<![\w-])" + re.escape(name) + r"(?![\w-])"
        for m in re.finditer(pattern, prose):
            log["plot_web_text_mentions"].append(
                {"page": page_slug, "target": rel, "text": m.group(0)}
            )
            prose = prose[: m.start()] + " " * len(m.group(0)) + prose[m.end():]  # count once


def render_links(text: str, index: Index, page_slug: str, log: dict) -> str:
    def one(m: re.Match) -> str:
        log["links_total"] = log.get("links_total", 0) + 1
        target, label = parse_link(m.group(1))
        note, problem = index.lookup(target)
        if note is None:
            log["unresolved_links"].append(
                {"page": page_slug, "text": m.group(0), "target": target, "reason": problem}
            )
            return label or humanise(target)
        if note.rel.startswith(INFRASTRUCTURE_PREFIXES) or note.rel in INFRASTRUCTURE_FILES:
            log["flattened_links"].append(
                {"page": page_slug, "text": label or humanise(target), "target": note.rel,
                 "reason": "infrastructure"}
            )
            # An unlabelled design link has only a slug for words: use the target's title and
            # flag it in the audit, so the prose can be given a real label later.
            title = lint.unquote(note.fm.get("title", ""))
            if not label:
                log["flattened_links"][-1]["unlabelled"] = True
            return label or title or humanise(target)
        kind = lint.unquote(note.fm.get("kind", ""))
        section = section_of(kind)
        if note.is_index or slug_of(note.rel) == "_index":
            # A map-of-content note: point at the section, or flatten the label.
            index_section = index.section_for_index(note)
            if index_section:
                display = label or SECTION_LABEL.get(index_section, "")
                log["flattened_links"].append(
                    {"page": page_slug, "text": display, "target": note.rel,
                     "reason": "section-index"}
                )
                return f"[{display}](/{index_section}/)"
            log["flattened_links"].append(
                {"page": page_slug, "text": label or humanise(target), "target": note.rel,
                 "reason": "navigation"}
            )
            return label or humanise(target)
        if kind in DEFERRED_KINDS:
            log["flattened_links"].append(
                {"page": page_slug, "text": label or humanise(target), "target": note.rel,
                 "reason": "deferred"}
            )
            return label or lint.unquote(note.fm.get("title", "")) or humanise(target)
        if section is None or not index.publishable(note):
            log["flattened_links"].append(
                {"page": page_slug, "text": label or humanise(target), "target": note.rel,
                 "reason": "no-open-content"}
            )
            return label or lint.unquote(note.fm.get("title", "")) or humanise(target)
        display = label or lint.unquote(note.fm.get("title", "")) or humanise(target)
        return f"[{display}]({url_of(section, slug_of(note.rel))})"

    return LINK_RE.sub(one, text)


# --- Building pages ----------------------------------------------------------------------

def publishable(note: lint.Note) -> bool:
    """A note becomes a page only if it has open content in a section that is not the Summary.

    The Summary is a page's standfirst, not its body: a note with nothing else would publish
    an empty page (and every link to it would go nowhere).
    """
    kind = lint.unquote(note.fm.get("kind", ""))
    if kind in DEFERRED_KINDS or section_of(kind) is None:
        return False
    for heading, _, lines in disclosure.sections(note):
        if not any(ln.strip() for ln in lines):
            continue
        _, cls = disclosure.classify(note, heading, lines)
        if cls in ("open", "mixed") and heading != "Summary":
            return True
    return False


def scrub_design_refs(text: str, note_rel: str, log: dict) -> str:
    """Remove design citations from lore prose, and record that the note needs fixing."""
    hits = DESIGN_PAREN_RE.findall(text) + DESIGN_TOKEN_RE.findall(text) + STEP_SENTENCE_RE.findall(text)
    if not hits:
        return text
    log["internal_references"].append({"note": note_rel, "text": text.strip()[:160]})
    return STEP_SENTENCE_RE.sub("", DESIGN_TOKEN_RE.sub("", DESIGN_PAREN_RE.sub("", text)))


def clean_lines(lines: list[str], kind: str, note_rel: str, log: dict) -> list[str]:
    out = []
    for ln in lines:
        cleaned = strip_markers(ln, kind)
        if cleaned is None:
            continue
        # Keep the leading whitespace: it is what nests a bullet under its parent. Stripping it
        # here published every sub-list flush (fixed in Step 16; `tidy` preserves indent).
        cleaned = sanitise_text(cleaned)
        indent = cleaned[: len(cleaned) - len(cleaned.lstrip())]
        cleaned = indent + cleaned.strip()
        label = DESIGN_LABEL_RE.match(cleaned)
        if label and label.group(1).strip().lower() in DESIGN_FIELDS:
            log["design_fields"].append({"note": note_rel, "label": label.group(1).strip(),
                                         "text": cleaned[:120]})
            continue  # an engine-facing field (`SRD base`, `Engine mapping`): not lore
        if not cleaned.strip():
            # A paragraph break. Keep it: dropping blank lines ran every paragraph of a section
            # together on the published page (fixed with testimony, Step 16). `collapse`
            # normalises runs of them.
            out.append("")
            continue
        before_scrub = cleaned
        cleaned = indent + scrub_design_refs(cleaned, note_rel, log).strip()
        if not cleaned.strip():
            continue
        if DESIGN_FIELD_RE.match(cleaned) and not DESIGN_FIELD_RE.match(indent + before_scrub.strip()):
            # This line was content that the scrubber emptied (`- **Engine mapping:** §9.7`).
            # A line that was *already* only a bold label is kept: it introduces a sub-list.
            log["design_fields"].append({"note": note_rel, "label": "(empty after scrub)",
                                         "text": ln.strip()[:120]})
            continue
        out.append(cleaned)
    return out


def tidy(text: str) -> str:
    """Close the holes a removed link leaves (`goes wrong ().` -> `goes wrong.`).

    Line by line, so that list indentation survives.
    """
    out = []
    for line in text.split("\n"):
        indent = len(line) - len(line.lstrip(" "))
        body = line[indent:]
        body = re.sub(r"\(\s*[,;]\s*\)", "", body)  # "( )" left by a removed link
        body = re.sub(r",\s*\)", ")", body)  # "(SRD, )" -> "(SRD)"
        body = EMPTY_PARENS_RE.sub("", body)
        body = re.sub(r"[ \t]{2,}", " ", body)
        body = re.sub(r"[ \t]+([.,;:!?])", r"\1", body)
        out.append(" " * indent + body)
    return "\n".join(out)


def collapse(lines: list[str]) -> str:
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return tidy(text).strip()


def first_sentence(text: str) -> str:
    """The pull-quote fallback: the account's opening sentence, shortened if it rambles."""
    plain = re.sub(r"\*\*([^*]+)\*\*", r"\1", text).strip()
    sentence = re.split(r"(?<=[.!?])\s+", plain)[0].strip()
    if len(sentence) <= QUOTE_MAX:
        return sentence
    cut = sentence[:QUOTE_MAX]
    at = max(cut.rfind(", "), cut.rfind("; "))
    if at < QUOTE_MAX // 2:
        at = cut.rfind(" ")
    return cut[: at if at > 0 else QUOTE_MAX].rstrip(" ,;:") + "…"


def is_approximate(heading: str) -> bool:
    """Did he hedge the date? `CY 601, or near it.` -> True."""
    low = heading.lower()
    return any(phrase in low for phrase in APPROX_PHRASES)


def entry_ident(heading: str) -> tuple[str, int]:
    """(teller, taken) from an entry heading, which opens with either the date or the person.

    One rule, one home: `tools/voice_lint.py` imports this rather than re-deriving it, so the
    linter and the exporter can never disagree about who is speaking.
    """
    taken = TAKEN_RE.search(heading)
    rest = LEAD_DATE_RE.sub("", heading) if taken else heading
    m = TELLER_RE.match(rest)
    return (m.group("teller").strip() if m else "",
            int(taken.group(1)) if taken else 0)


def parse_testimony(lines: list[str]) -> dict | None:
    """Turn a clean `## Testimony` section into teller / transmission / quote / paragraphs.

    None when there is no account under the transmission line: an attribution alone is not
    testimony, and publishing it would give the page an empty block.
    """
    text = collapse(lines)
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paragraphs:
        return None

    heading = paragraphs[0]
    teller, taken = entry_ident(heading)
    transmission = ""
    rest = LEAD_DATE_RE.sub("", heading) if taken else heading
    m = TELLER_RE.match(rest)
    if m:
        transmission = m.group("rest").strip().rstrip(".").strip()
        paragraphs = paragraphs[1:]

    quote = ""
    if paragraphs:
        qm = QUOTE_RE.match(paragraphs[0])
        if qm:
            quote = qm.group("quote").strip().strip('"“”').strip()
            paragraphs = paragraphs[1:]

    if not paragraphs or not any(p.strip() for p in paragraphs):
        return None
    if not quote:
        quote = first_sentence(paragraphs[0])
    return {"teller": teller, "transmission": transmission, "quote": quote,
            "paragraphs": paragraphs, "heading": heading, "taken": taken,
            "approx": is_approximate(heading)}


def testimony_text(testimony: dict | None) -> str:
    """The account as plain text, for the content hash and the keystone scan."""
    if not testimony:
        return ""
    return "\n".join([testimony.get("quote", ""), *testimony.get("paragraphs", [])])


# --- Plates -------------------------------------------------------------------------------
# An accepted plate in `site/image-prompts/` can illustrate the notes it names in its
# `canon:` list. The join is here so the codex never repeats an image path in a lore note,
# and so an image can only appear on a page once it is accepted AND its crop exists.

PLATES_DIR = "site/image-prompts"
PUBLIC_IMG = "site/public/img"
DEFAULT_PLATE_CROP = "16x9"


def _plate_scalar(value: str) -> str:
    v = value.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        if v[0] == '"':
            try:
                return json.loads(v)
            except ValueError:
                pass
        return v[1:-1]
    return v


def parse_plate_frontmatter(text: str) -> dict:
    """Parse a plate note's frontmatter: scalars, flow lists and block lists."""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    fm: dict = {}
    key = ""
    for raw in text[3:end].strip("\n").split("\n"):
        line = raw.rstrip()
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- ") and key:
            if not isinstance(fm.get(key), list):
                fm[key] = []
            fm[key].append(_plate_scalar(stripped[2:]))
            continue
        if ":" not in line:
            continue
        name, _, value = line.partition(":")
        key = name.strip()
        value = value.strip()
        if not value:
            fm[key] = []
        elif value.startswith("[") and value.endswith("]"):
            fm[key] = [_plate_scalar(p) for p in value[1:-1].split(",") if p.strip()]
        else:
            fm[key] = _plate_scalar(value)
    return fm


def load_plates(root: Path) -> dict[str, dict]:
    """Map a canon note path to the page image its plate supplies.

    A plate counts only when its frontmatter says `status: accepted`, it names the note in
    `canon:`, and the crop file is really in `site/public/img/`. Anything else is ignored, so
    a half-finished plate can never publish a broken image.
    """
    plates: dict[str, dict] = {}
    base = root / PLATES_DIR
    if not base.is_dir():
        return plates
    for path in sorted(base.glob("*.md")):
        if path.name.startswith("_") or path.name.lower() == "readme.md":
            continue
        try:
            fm = parse_plate_frontmatter(path.read_text(encoding="utf-8"))
        except OSError:
            continue
        if fm.get("status") != "accepted":
            continue
        stem = Path(str(fm.get("output", ""))).name
        if not stem:
            continue
        image = str(fm.get("page_image") or f"{stem}-{DEFAULT_PLATE_CROP}.jpg")
        if not (root / PUBLIC_IMG / image).is_file():
            continue
        alt = str(fm.get("alt") or fm.get("title") or "").strip()
        for canon in fm.get("canon") or []:
            target = str(canon).strip()
            if target:
                plates[target] = {"image": image, "alt": alt,
                                  "plate": str(fm.get("slug") or stem)}
    return plates


@dataclass
class Page:
    id: str
    kind: str
    title: str
    section: str
    slug: str
    summary: str
    body: str
    era: str = ""
    t0: str = ""
    tags: list[str] = field(default_factory=list)
    image: str = ""
    image_alt: str = ""
    testimony: dict | None = None
    # A volume of the Reader's book: `testimony_index` in frontmatter, either `true` (every
    # account) or a year range `575-598`, which says which volume an account falls in.
    testimony_index: tuple[int, int] | None = None
    # True on the hub: the note whose page every account links back to.
    testimony_source_hub: bool = False
    # Where "From the Reader's book" links to: the hub page, resolved from the note that declares
    # `testimony_source: true`, so the layout never hard-codes a slug.
    testimony_source: str = ""


def frontmatter_layers(note: lint.Note) -> list[tuple[str, str]]:
    out = []
    for label in LAYER_LABELS:
        value = lint.unquote(note.fm.get(label.lower(), ""))
        if value:
            out.append((label, value))
    return out


def parse_testimony_index(note: lint.Note) -> tuple[int, int] | None:
    """`testimony_index: true` (every account, undated ones included) or `575-598` (a volume)."""
    value = lint.unquote(note.fm.get("testimony_index", "")).strip()
    if not value:
        return None
    if value.lower() in ("true", "yes", "1"):
        return (0, 9999)
    m = TESTIMONY_RANGE_RE.match(value)
    if not m:
        return None
    low, high = sorted((int(m.group(1)), int(m.group(2))))
    return (low, high)


def page_for(note: lint.Note, index: Index, log: dict,
             plates: dict[str, dict] | None = None) -> Page | None:
    kind = lint.unquote(note.fm.get("kind", ""))
    if kind in DEFERRED_KINDS:
        log["skipped_notes"].append({"note": note.rel, "reason": "deferred kind"})
        return None
    section = section_of(kind)
    if section is None:
        log["skipped_notes"].append({"note": note.rel, "reason": f"kind {kind!r} has no section"})
        return None
    if not index.publishable(note):
        log["skipped_notes"].append({"note": note.rel, "reason": "no open content"})
        return None

    slug = slug_of(note.rel)
    title = lint.unquote(note.fm.get("title", "")) or humanise(slug)
    summary = ""
    blocks: list[str] = []
    used: set[str] = set()
    has_layers = False
    testimony: dict | None = None

    for heading, _, lines in disclosure.sections(note):
        if not any(ln.strip() for ln in lines):
            continue
        _, cls = disclosure.classify(note, heading, lines)
        if cls not in ("open", "mixed"):
            if cls in ("earned", "sealed"):
                log["dropped_sections"].append(
                    {"note": note.rel, "heading": heading, "class": cls}
                )
            continue

        if cls == "mixed":
            segments: list[tuple[str, str]] = []
            for ln in lines:
                for label, text in split_layers(ln):
                    if not label:
                        log["dropped_lines"].append(
                            {"note": note.rel, "heading": heading, "text": text[:120]}
                        )
                        continue
                    if label == TRUTH_LABEL:
                        log["dropped_lines"].append(
                            {"note": note.rel, "heading": heading, "text": f"Truth: {text[:110]}"}
                        )
                        continue
                    segments.append((label, text))
            if not segments:
                continue
            has_layers = True
            name = sanitise_heading(heading) or "The record"
            if all(label in LAYER_LABELS for label, _ in segments):
                name = "What people say" if "What people say" not in used else name
            used.add(name)
            body_lines = [f"## {name}"]
            for label, text in segments:
                # A blank line between them: one paragraph per attested view.
                body_lines.append(f"**{label}.** {text}\n")
            blocks.append(collapse(body_lines))
            continue

        if cls == "open" and heading.strip().lower() == TESTIMONY_HEADING:
            # Not a body section: lifted into the page's frontmatter (docs/testimony.md section 3.4).
            parsed = parse_testimony(clean_lines(lines, kind, note.rel, log))
            if parsed is None:
                log["dropped_sections"].append(
                    {"note": note.rel, "heading": heading, "class": "testimony without an account"}
                )
            elif testimony is not None:
                log["dropped_sections"].append(
                    {"note": note.rel, "heading": heading, "class": "second testimony"}
                )
            else:
                testimony = parsed
            continue

        cleaned = clean_lines(lines, kind, note.rel, log)
        text = collapse(cleaned)
        if not text:
            continue
        if heading == "Summary":
            text = H1_RE.sub("", text).strip()  # the note's own title line
            if not text:
                continue
            m = SUMMARY_LABEL_RE.match(text)
            if m:
                first, _, rest = text[m.end():].partition("\n")
                summary = first.strip()
                rest = rest.strip()
                if rest:
                    blocks.append(rest)
            else:
                summary = text.split("\n", 1)[0].strip()
        else:
            name = sanitise_heading(heading)
            used.add(name)
            blocks.append(f"## {name}\n{text}" if name else text)

    layers = frontmatter_layers(note)
    if layers and not has_layers:
        used.add("What people say")
        lines = ["## What people say"]
        for label, text in layers:
            lines.append(f"**{label}.** {text}\n")
        blocks.insert(0, collapse(lines))

    body = "\n\n".join(collapse([b]) for b in blocks if b.strip())
    if not body:
        log["skipped_notes"].append({"note": note.rel, "reason": "summary only"})
        return None
    body = render_links(body, index, slug, log)
    summary = render_links(summary, index, slug, log) if summary else ""
    if testimony:
        testimony["quote"] = render_links(testimony["quote"], index, slug, log)
        testimony["paragraphs"] = [render_links(p, index, slug, log)
                                   for p in testimony["paragraphs"]]

    names = log.setdefault("_plot_web_names", None)
    if names is None:
        names = log["_plot_web_names"] = plot_web_names(index)
    for surface in (summary, body, testimony_text(testimony)):
        if surface:
            log_plot_web_mentions(surface, slug, names, log)

    authored = [
        t for t in re.findall(r"[a-z0-9_-]+", lint.unquote(note.fm.get("tags", "")))
        if t not in YAML_BOOLEANS
    ]
    tags = [t for t in dict.fromkeys(authored) if t in PUBLISHED_TAGS]
    withheld = [t for t in dict.fromkeys(authored) if t not in PUBLISHED_TAGS]
    if withheld:
        log["withheld_tags"].append({"note": note.rel, "tags": withheld})

    page = Page(
        id=lint.unquote(note.fm.get("id", "")),
        kind=kind,
        title=title,
        section=section,
        slug=slug,
        summary=summary,
        body=body,
        era=lint.unquote(note.fm.get("era", "")),
        t0=lint.unquote(note.fm.get("t0", "")),
        tags=tags,
        testimony=testimony,
        testimony_index=parse_testimony_index(note),
    )
    page.testimony_source_hub = lint.unquote(note.fm.get("testimony_source", "")).lower() in (
        "true", "yes", "1")
    plate = (plates or {}).get(note.rel)
    if plate:
        page.image = plate["image"]
        page.image_alt = plate["alt"]
    return page


# --- Emitting ----------------------------------------------------------------------------

def yaml_scalar(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def render_page(page: Page, updated: str) -> str:
    fm = [
        "---",
        f"id: {yaml_scalar(page.id)}",
        f"kind: {page.kind}",
        f"title: {yaml_scalar(page.title)}",
        f"section: {page.section}",
        f"slug: {page.slug}",
        f"summary: {yaml_scalar(page.summary)}",
        f"updated: {yaml_scalar(updated)}",
    ]
    if page.era:
        fm.append(f"era: {yaml_scalar(page.era)}")
    if page.t0:
        fm.append(f"t0: {yaml_scalar(page.t0)}")
    if page.tags:
        fm.append("tags: [" + ", ".join(yaml_scalar(t) for t in page.tags) + "]")
    if page.image:
        fm.append(f"image: {yaml_scalar(page.image)}")
        fm.append(f"imageAlt: {yaml_scalar(page.image_alt)}")
    if page.testimony:
        t = page.testimony
        if page.testimony_source:
            fm.append(f"testimonySource: {yaml_scalar(page.testimony_source)}")
        fm.append("testimony:")
        fm.append(f"  teller: {yaml_scalar(t['teller'])}")
        fm.append(f"  transmission: {yaml_scalar(t['transmission'])}")
        fm.append(f"  heading: {yaml_scalar(t['heading'])}")
        fm.append(f"  quote: {yaml_scalar(t['quote'])}")
        fm.append(f"  taken: {int(t.get('taken') or 0)}")
        if t.get("approx"):
            fm.append("  approx: true")
        fm.append("  paragraphs:")
        for para in t["paragraphs"]:
            fm.append(f"    - {yaml_scalar(para)}")
    fm.append("---")
    return "\n".join(fm) + "\n\n" + page.body + "\n"


def assemble_accounts(pages: list[Page], log: dict) -> list[Page]:
    """Give each volume of the Reader's book the accounts taken in its years, in order.

    The accounts have one home (the note they describe); a volume page is a reading order,
    assembled the way a tag page is assembled. Order is **chronological** — a record should read
    forwards in time — then by title. Each account falls in exactly one volume, the first whose
    year range holds its `taken` year; an account with no year falls in no volume and is listed
    in the audit so that the omission is visible.
    """
    volumes = sorted((p for p in pages if p.testimony_index),
                     key=lambda p: p.testimony_index[0])
    excerpts = sorted((p for p in pages if p.testimony),
                     key=lambda p: (p.testimony["taken"] or 9999, p.title))
    for p in excerpts:
        if not p.testimony["taken"]:
            # Undated is a defect whether or not it is collected: the account claims to describe
            # the present. Reported even when a `true` index places it anyway.
            log["testimony_undated"].append({"page": p.slug, "teller": p.testimony["teller"]})
    if not volumes:
        return pages

    placed: dict[str, list[Page]] = {v.slug: [] for v in volumes}
    for p in excerpts:
        taken = p.testimony["taken"]
        for v in volumes:
            low, high = v.testimony_index
            if low <= taken <= high:
                placed[v.slug].append(p)
                break
        else:
            log["testimony_unplaced"].append(
                {"page": p.slug, "teller": p.testimony["teller"], "taken": taken})
            continue
        log["testimony"].append({"page": p.slug, "section": p.section,
                                 "teller": p.testimony["teller"], "taken": taken,
                                 "collected_on": v.slug})

    for volume in volumes:
        blocks = ["## The accounts"]
        for p in placed[volume.slug]:
            t = p.testimony
            # His whole entry heading, date and all: a volume is read in order of time, so the
            # date is the one thing it must never lose.
            heading = f"### [{p.title}]({url_of(p.section, p.slug)})"
            entry = t.get("heading") or f"**{t['teller']}**, {t['transmission']}"
            blocks.append("\n\n".join([heading, entry, *t["paragraphs"]]))
        if len(blocks) > 1:
            volume.body = (volume.body + "\n\n" + "\n\n".join(blocks)).strip()
    return pages


def load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                    encoding="utf-8")


def keyword_hits(page: Page) -> list[dict]:
    hits = []
    # Tags are published text too: a keystone term in a tag is a hit like any other.
    haystack = (f"{page.title}\n{page.summary}\n{page.body}\n{testimony_text(page.testimony)}\n"
                f"{' '.join(page.tags)}")
    lower = haystack.lower()
    for term in KEYSTONE_TERMS:
        if term.lower() in lower:
            hits.append({"page": page.slug, "section": page.section, "term": term})
    return hits


def build(today: str | None = None, out: Path | None = None, data: Path | None = None,
          audit_file: Path | None = None, dry_run: bool = False) -> dict:
    _reload()
    today = today or date.today().isoformat()
    out = out or ROOT / "site" / "src" / "content" / "generated"
    data = data or ROOT / "site" / "src" / "data" / "generated"
    audit_file = audit_file or ROOT / "site" / "audit" / "latest.json"

    # Index the whole vault, so a link into design material resolves and is classed as
    # infrastructure rather than as a broken link. Only `world/` notes become pages.
    index = Index.build(lint.load_notes())  # includes design docs, so their links resolve
    notes = [n for n in lint.load_notes() if n.has_fm and not n.is_doc and n.rel.startswith(LORE_ROOT)]

    log: dict = {"flattened_links": [], "skipped_notes": [], "dropped_sections": [],
                 "dropped_lines": [], "unresolved_links": [], "internal_references": [],
                 "design_fields": [], "withheld_tags": [], "plot_web_text_mentions": [],
                 "testimony": [], "testimony_unplaced": [], "testimony_undated": []}

    plates = load_plates(lint.ROOT)
    log["plates"] = []

    pages: list[Page] = []
    for note in notes:
        page = page_for(note, index, log, plates)
        if page:
            pages.append(page)
            if page.image:
                log["plates"].append({"note": note.rel, "image": page.image})
    pages.sort(key=lambda p: (p.section, p.slug))

    # The book's own page is the way back from any account: "From the Reader's book" is a link.
    source = next((p for p in pages if p.testimony_source_hub), None)
    if source is not None:
        hub = url_of(source.section, source.slug)
        for page in pages:
            if page.testimony:
                page.testimony_source = hub

    pages = assemble_accounts(pages, log)

    # History: slug changes, first appearance, last change.
    history_path = (audit_file.parent / "history.json") if audit_file else None
    history = load_json(history_path, {}) if history_path else {}
    known = history.setdefault("pages", {})
    entries = history.setdefault("entries", [])

    rendered: dict[str, tuple[Page, str]] = {}
    for page in pages:
        body = render_page(page, "1970-01-01")
        # Tags are deliberately outside the hash: refiling a note is not a lore revision, and the
        # changelog tracks lore. A tag change still republishes the page.
        digest = content_hash(page.title, page.summary, page.body, testimony_text(page.testimony))
        prev = known.get(page.id, {})
        added = prev.get("added", today)
        changed = prev.get("hash") != digest
        updated = today if changed else prev.get("updated", today)
        previous_slugs = list(prev.get("previous_slugs", []))
        if prev and prev.get("slug") and prev["slug"] != page.slug:
            previous_slugs.append(prev["slug"])
        known[page.id] = {
            "slug": page.slug, "section": page.section, "title": page.title,
            "hash": digest, "added": added, "updated": updated,
            "previous_slugs": sorted(set(previous_slugs) - {page.slug}),
        }
        if not prev:
            entries.append({"date": today, "change": "added", "id": page.id,
                            "title": page.title, "section": page.section, "slug": page.slug})
        elif changed:
            entries.append({"date": today, "change": "updated", "id": page.id,
                            "title": page.title, "section": page.section, "slug": page.slug})
        rendered[page.id] = (page, render_page(page, updated))

    # The changelog must never point at a page that no longer publishes.
    published_ids = {page.id for page in pages}
    entries = [e for e in entries if e["id"] in published_ids]

    redirects = []
    for page in pages:
        for old in known.get(page.id, {}).get("previous_slugs", []):
            redirects.append({"from": url_of(known[page.id]["section"], old),
                              "to": url_of(page.section, page.slug)})

    navigation = [
        {"slug": slug, "label": label, "blurb": blurb,
         "count": sum(1 for p in pages if p.section == slug)}
        for slug, label, _k, blurb in SECTIONS
        if sum(1 for p in pages if p.section == slug)
    ]

    # Invert the per-note log into tag -> notes: a reviewer reads "what are we withholding, and
    # where", not one entry per note.
    withheld: dict[str, list[str]] = {}
    for item in log["withheld_tags"]:
        for tag in item["tags"]:
            withheld.setdefault(tag, []).append(item["note"])

    audit = {
        "generated": today,
        "pages": len(pages),
        "sections": sum(len(re.findall(r"^## ", p.body, re.M)) + 1 for p in pages),
        "words": sum(len(re.sub(r"[#*\[\]()]", " ", p.body).split()) for p in pages),
        "testimony_words": sum(len(testimony_text(p.testimony).split()) for p in pages),
        "links": log.get("links_total", 0),
        "testimony": log["testimony"],
        "testimony_unplaced": log["testimony_unplaced"],
        "testimony_undated": log["testimony_undated"],
        "pages_without_summary": [p.slug for p in pages if not p.summary],
        "flattened_links": log["flattened_links"],
        "plot_web_text_mentions": log["plot_web_text_mentions"],
        "skipped_notes": log["skipped_notes"],
        "dropped_sections": log["dropped_sections"],
        "dropped_lines": log["dropped_lines"],
        "unresolved_links": log["unresolved_links"],
        "internal_references": log["internal_references"],
        "design_fields": log["design_fields"],
        "withheld_tags": {tag: sorted(notes) for tag, notes in sorted(withheld.items())},
        # A published tag that no note carries would be a dead index page: a config bug.
        "empty_tags": [t for t in PUBLISHED_TAGS
                       if t not in {tag for page in pages for tag in page.tags}],
        "keyword_hits": [h for p in pages for h in keyword_hits(p)],
        "ambiguous_links": [u for u in log["unresolved_links"] if u["reason"] == "ambiguous"],
        # Pages carrying an accepted plate, so the publish record shows which images shipped.
        "plates": log["plates"],
    }

    if not dry_run:
        if out.exists():
            for stale in out.rglob("*.md"):
                stale.unlink()
        for page in pages:
            path = out / page.section / f"{page.slug}.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(rendered[page.id][1], encoding="utf-8")
        # The Astro build cannot call Python, so the world's branding reaches it here. `site.ts`
        # imports this instead of holding a second copy of the world's name and tagline.
        write_json(data / "site.json", site_json())
        write_json(data / "navigation.json", navigation)
        write_json(data / "changelog.json", list(reversed(entries[-100:])))
        write_json(data / "redirects.json", redirects)
        write_json(audit_file, audit)
        if history_path:
            write_json(history_path, history)

    return audit


def summarise(audit: dict) -> str:
    flat = audit["flattened_links"]
    by_reason: dict[str, int] = {}
    for f in flat:
        by_reason[f["reason"]] = by_reason.get(f["reason"], 0) + 1
    lines = [
        f"pages {audit['pages']} | sections {audit['sections']} | words {audit['words']}",
        f"flattened links {len(flat)} " + " ".join(f"({k} {v})" for k, v in sorted(by_reason.items())),
        f"skipped notes {len(audit['skipped_notes'])} | dropped sections {len(audit['dropped_sections'])}"
        f" | dropped lines {len(audit['dropped_lines'])}",
        f"unresolved links {len(audit['unresolved_links'])} (ambiguous {len(audit['ambiguous_links'])})",
        f"keyword hits {len(audit['keyword_hits'])} | pages without a summary {len(audit['pages_without_summary'])}",
        f"internal references {len(audit['internal_references'])} (design citations in lore prose,"
        f" fix at source) | engine fields dropped {len(audit['design_fields'])}",
        f"plot-web names in prose {len(audit['plot_web_text_mentions'])}"
        f" (solve leaks: move the reference to `## Hooks`)",
        f"plates on pages {len(audit['plates'])}"
        + (f" ({', '.join(sorted({p['image'] for p in audit['plates']}))})" if audit["plates"] else ""),
        f"tags {len(PUBLISHED_TAGS)} published | "
        f"{sum(len(notes) for notes in audit['withheld_tags'].values())} chip names withheld"
        f" ({len(audit['withheld_tags'])} tags) | empty tags {len(audit['empty_tags'])}",
    ]
    return "\n".join(lines)


def site_json(cfg=None, what_to_expect=None, tag_labels=None) -> dict[str, object]:
    """The world's branding, as the theme reads it from site/src/data/generated/site.json.

    A function rather than an inline literal so the seam can be tested: every field here is a
    value the THEME reads, and a field the theme reads but this omits is silent - an empty
    search hint, a hero image that never resolves - so test_site_export checks the two lists
    against each other.
    """
    cfg = CFG if cfg is None else cfg
    what_to_expect = WHAT_TO_EXPECT if what_to_expect is None else what_to_expect
    tag_labels = TAG_LABELS if tag_labels is None else tag_labels
    return {

            "name": cfg.title,
            "worldId": cfg.world_id,
            "slug": cfg.slug,
            "tagline": cfg.tagline,
            "description": cfg.description,
            "author": cfg.author,
            "license": cfg.license,
            "url": cfg.site.url,
            "buttondownUser": cfg.site.buttondown_user,
            "heroAlt": cfg.site.hero_alt,
            "heroCredit": cfg.site.hero_credit,
            "heroFile": cfg.site.hero_file,
            "searchPlaceholder": cfg.site.search_placeholder,
            # Everything here is the world's: the theme has no opinion about any of it.
            "contentDescriptors": list(cfg.site.content_descriptors),
            "t0Prefix": cfg.site.t0_prefix,
            "t0Epoch": cfg.site.t0_epoch,
            "doorways": [{"href": d.href, "label": d.label, "blurb": d.blurb}
                         for d in cfg.site.doorways],
            "whatToExpect": list(what_to_expect),
            "tagLabels": dict(tag_labels),
            }



def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Export the player-facing view of the codex.")
    ap.add_argument("--out", type=Path, help="content output directory")
    ap.add_argument("--data", type=Path, help="data output directory")
    ap.add_argument("--audit", type=Path, help="audit file")
    ap.add_argument("--dry-run", action="store_true", help="report only, write nothing")
    ap.add_argument("--check", action="store_true",
                    help="exit 1 on an ambiguous link (authoring bug); other findings are for review")
    args = ap.parse_args(argv)

    audit = build(out=args.out, data=args.data, audit_file=args.audit, dry_run=args.dry_run)
    print(summarise(audit))
    failed = False
    if args.check and audit["ambiguous_links"]:
        print("\nAmbiguous links must be fixed (add the folder to the link):", file=sys.stderr)
        for item in audit["ambiguous_links"][:20]:
            print(f"  {item['page']}: {item['text']}", file=sys.stderr)
        failed = True
    if args.check and audit["empty_tags"]:
        print("\nPublished tags that no note carries (drop them from the `site-vocabulary`\n"
              "block in the note world.config.yaml names as vault.notes.site_vocabulary):",
              file=sys.stderr)
        for tag in audit["empty_tags"]:
            print(f"  {tag}", file=sys.stderr)
        failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

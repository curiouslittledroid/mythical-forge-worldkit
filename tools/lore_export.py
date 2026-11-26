#!/usr/bin/env python3
"""Step 14: the Lore corpus export (Design 24 §2, PR-14) and its calibration report.

Turns every classified prose section of `world/` into **Lore chunks** — the retrievable,
audience-scoped form of the lore that NPC agents and the narrator read — and reports the
numbers the platform's Phase 5 A4 needs to set a top-k and a token cap.

    python3 tools/lore_export.py                 # the report (default)
    python3 tools/lore_export.py --json out.json # also write every chunk record
    python3 tools/lore_export.py --limit 3       # cap the ranked lists in the report

Rules (meta/lore-corpus.md, conventions §7.5):

* **One chunk per paragraph.** A paragraph over 300 words splits at sentence boundaries.
  Nothing is truncated and nothing is rejected.
* **A history event's layer lines split.** `**Official:**` / `**Myth:**` / `**Rival:**` /
  `**Truth:**` each become their own chunk, so a believer of the myth is handed the myth.
* **Class comes from `disclosure.classify`** — imported, never re-derived.
* **Audience is derived, not authored** (with `**Known by:**` as the override). Emitted as
  groups and tiers, *not* NPC ids, so a roster edit costs no re-embedding (PR-14 amendment).

Not built here: the write into the Game Ready Repository. `LORE` is not yet an entity kind
in `packages/authored-content` (Phase 5 A4), so `--json` is the hand-off until it is.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import disclosure  # noqa: E402
import lint  # noqa: E402

MAX_WORDS = 300  # a chunk's ceiling; exceeded paragraphs split at sentence boundaries
WORDS = re.compile(r"[A-Za-z0-9'’-]+")
SENTENCE = re.compile(r"(?<=[.!?])\s+")
DASHED = re.compile(r"\[\[([^\[\]]+)\]\]")

RANK = {"common": 0, "select": 1, "inner": 2}
LAYER_OF_MARK = {"official": "official", "myth": "myth", "rival": "rival", "truth": "truth"}
LAYER_LINE = re.compile(r"\*\*(Official|Myth|Rival|Truth)\b[^*:]*:\*\*")
KNOWN_BY = re.compile(r"^\*\*Known by:\*\*\s*(.+)$")
REVEAL_WHEN = re.compile(r"^\*\*Reveal when:\*\*\s*(.+)$")
WANT_LINE = re.compile(r"^\*\*Wants?:\*\*")
# Entity ids a chunk can be "about". Predicate names that look like ids are excluded.
ID_REF = re.compile(
    r"\b(?:loc|zone|npc|want|fact|faction|evt|item|mon|mod|camp|quest|room|enc|race|"
    r"hist|fig|god|thread|topic|overlay|mig|rel)_[a-z0-9_]+\b"
)
NOT_SUBJECTS = {"npc_alive", "fact_revealed", "quest_state"}

# Note kinds whose prose reaches nobody but the people in one place or one body.
LOCAL_KINDS = {"REGION", "SETTLEMENT", "PLACE"}


# ─── helpers ────────────────────────────────────────────────────────────────────


def slug(text: str, limit: int = 40) -> str:
    out = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return (out[:limit].rstrip("_")) or "body"


def flatten_links(line: str) -> str:
    """`[[the-dry-sea|the Dry Sea]]` -> `the Dry Sea`; `[[the-spine]]` -> `the spine`."""

    def one(m: re.Match) -> str:
        inner = m.group(1).replace("\\|", "|")
        target, _, label = inner.partition("|")
        if label.strip():
            return label.strip()
        return target.split("#", 1)[0].strip().replace("-", " ")

    return DASHED.sub(one, line)


def word_count(text: str) -> int:
    return len(WORDS.findall(text))


def split_paragraph(text: str, limit: int = MAX_WORDS) -> list[str]:
    """Split at sentence boundaries until every piece is within the ceiling."""
    if word_count(text) <= limit:
        return [text]
    sentences = [s for s in SENTENCE.split(text) if s.strip()]
    out: list[str] = []
    current: list[str] = []
    count = 0
    for sentence in sentences:
        n = word_count(sentence)
        if current and count + n > limit:
            out.append(" ".join(current).strip())
            current, count = [], 0
        current.append(sentence)
        count += n
    if current:
        out.append(" ".join(current).strip())
    return out


def paragraphs(lines: list[str]) -> list[str]:
    """Blank-line-separated blocks, keeping a lead-in line with the block under it."""
    out: list[str] = []
    buf: list[str] = []
    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            if buf:
                out.append("\n".join(buf).strip())
                buf = []
            continue
        if line.lstrip().startswith("#"):  # an H3 sub-heading: not prose, not a separator
            continue
        buf.append(line)
    if buf:
        out.append("\n".join(buf).strip())
    return [p for p in out if p and word_count(p) > 0]


def zone_of(note: lint.Note, places: dict[str, str]) -> str | None:
    """The zone a note sits in: its own `zone`, its home's zone, or its own id for a REGION."""
    kind = lint.unquote(note.fm.get("kind", ""))
    zid = lint.unquote(note.fm.get("id", ""))
    zone = lint.unquote(note.fm.get("zone", "")).strip()
    if zone:
        return zone
    if kind == "REGION":
        return zid
    home = lint.unquote(note.fm.get("home", "")).strip()
    if home and home in places:
        return places[home]
    return None


def parse_groups(raw: str) -> list[tuple[str, str]]:
    """`[{ id: faction_x, rank: inner }]` (a one-line YAML list) -> [(id, rank)]."""
    return [(gid, rank) for gid, rank in re.findall(r"id:\s*([a-z0-9_]+)\s*,\s*rank:\s*([a-z]+)", raw)]


def npc_index(notes: list[lint.Note]) -> list[dict]:
    places = {
        lint.unquote(n.fm.get("id", "")): lint.unquote(n.fm.get("zone", "")).strip()
        for n in notes
        if lint.unquote(n.fm.get("kind", "")) in LOCAL_KINDS
    }
    out = []
    for n in notes:
        if lint.unquote(n.fm.get("kind", "")) != "NPC":
            continue
        out.append(
            {
                "id": lint.unquote(n.fm.get("id", "")),
                "race": lint.unquote(n.fm.get("race", "")).strip(),
                "zone": zone_of(n, places) or "",
                "groups": parse_groups(n.fm.get("groups", "")),
            }
        )
    return out


# ─── audience (conventions §7.5) ────────────────────────────────────────────────


def derive_audience(note: lint.Note, heading: str, cls: str, lines: list[str], zone: str | None) -> dict:
    """Who in the world could know this chunk. Groups and tiers, never NPC ids."""
    kind = lint.unquote(note.fm.get("kind", ""))
    nid = lint.unquote(note.fm.get("id", ""))

    known = next((KNOWN_BY.match(ln.strip()) for ln in lines if KNOWN_BY.match(ln.strip())), None)
    if known:  # the author's override wins over every default
        groups, tiers = [], []
        for part in re.split(r"[,\s]+", known.group(1)):
            if not part:
                continue
            gid, _, tier = part.partition("@")
            groups.append(gid)
            tiers.append(tier if tier in RANK else "common")
        if groups == ["self"]:
            return {"scope": "self", "about": nid}
        return {"scope": "faction", "groups": groups, "tiers": tiers}

    if kind == "NPC" and (any(WANT_LINE.match(ln.strip()) for ln in lines) or heading.lower().endswith("secrets")):
        # An NPC's own motive and its own secrets reach its own agent and nobody else.
        return {"scope": "self", "about": nid}

    if cls == "open":
        return {"scope": "world"}

    if kind == "FACTION":
        return {"scope": "faction", "groups": [nid], "tiers": ["inner" if cls == "sealed" else "select"]}

    if zone:
        return {"scope": "zone", "about": zone}

    return {"scope": "world"}


def knows(audience: dict, npc: dict) -> bool:
    """Does this NPC's audience include the chunk? The one resolution rule the engine shares."""
    scope = audience.get("scope")
    if scope == "world":
        return True
    if scope == "self":
        return audience.get("about") == npc["id"]
    if scope == "zone":
        return bool(npc["zone"]) and audience.get("about") == npc["zone"]
    if scope == "faction":
        ranks = dict(npc["groups"])
        for gid, tier in zip(audience.get("groups", []), audience.get("tiers", [])):
            if gid == npc["race"]:  # a race group has no tiers
                return True
            if gid in ranks and RANK.get(ranks[gid], -1) >= RANK.get(tier, 0):
                return True
        return False
    return False


# ─── chunks ─────────────────────────────────────────────────────────────────────


def chunk_text(block: str) -> str:
    return flatten_links(block).replace("[OPEN]", "").strip()


def subjects_of(text: str, topic: str, stem2id: dict[str, str]) -> list[str]:
    """What the chunk is about: the note's wikilinks (the real index) plus any literal ids.

    Prose almost never spells out an id — it links. The link targets are therefore the
    subject index, which is what makes subject narrowing possible at retrieval time.
    """
    found = {m.group(0) for m in ID_REF.finditer(text)} - NOT_SUBJECTS
    for m in DASHED.finditer(text):
        target = m.group(1).replace("\\|", "|").partition("|")[0].split("#", 1)[0].strip()
        stem = target.lower()
        if stem.endswith(".md"):
            stem = stem[:-3]
        stem = stem.rsplit("/", 1)[-1]
        if stem in stem2id:
            found.add(stem2id[stem])
    found.add(topic)
    return sorted(found)


def build_chunks(notes: list[lint.Note]) -> tuple[list[dict], list[str]]:
    """Every classified lore section -> its chunks, in authored order."""
    stem2id = {
        Path(n.rel).stem: lint.unquote(n.fm.get("id", ""))
        for n in notes
        if lint.unquote(n.fm.get("id", ""))
    }
    places = {
        lint.unquote(n.fm.get("id", "")): lint.unquote(n.fm.get("zone", "")).strip()
        for n in notes
        if lint.unquote(n.fm.get("kind", "")) in LOCAL_KINDS
    }
    chunks: list[dict] = []
    warnings: list[str] = []
    for note in notes:
        if note.is_doc:
            continue
        nid = lint.unquote(note.fm.get("id", ""))
        kind = lint.unquote(note.fm.get("kind", ""))
        zone = zone_of(note, places)
        for heading, line, lines in disclosure.sections(note):
            source, cls = disclosure.classify(note, heading, lines)
            if cls == "-":
                continue
            body = [lint.unquote(ln) for ln in lines]
            block = "\n".join(ln for ln in body if not KNOWN_BY.match(ln.strip()) or False)
            reveal = next((REVEAL_WHEN.match(ln.strip()) for ln in body if REVEAL_WHEN.match(ln.strip())), None)
            reveal_when = reveal.group(1).strip() if reveal else None
            audience = derive_audience(note, heading, cls, body, zone)

            # A history event's layer lines split; everything else is paragraph-split.
            pieces: list[tuple[str, str]] = []
            if cls == "mixed":
                for para in paragraphs(body):
                    segments = []
                    pos = 0
                    for m in LAYER_LINE.finditer(para):
                        if m.start() > pos:
                            segments.append(("", para[pos : m.start()]))
                        segments.append((LAYER_OF_MARK[m.group(1).lower()], ""))
                        pos = m.end()
                    tail = para[pos:]
                    labelled: list[tuple[str, str]] = []
                    for i, (label, before) in enumerate(segments):
                        text = before.strip()
                        if label:
                            nxt = segments[i + 1][1] if i + 1 < len(segments) else tail
                            text = nxt.strip()
                        if text:
                            labelled.append((label or "truth", text))
                    pieces.extend(labelled or [("truth", para)])
            else:
                for para in paragraphs(body):
                    for piece in split_paragraph(para):
                        pieces.append(("truth", piece))

            for ordinal, (layer, piece) in enumerate(pieces, start=1):
                text = chunk_text(piece)
                if not text:
                    continue
                # `mixed` is a section source, not a class: conventions 7.3 rules 3-4 put the
                # official/myth/rival layers at `open` and the truth layer at `earned`.
                cls_chunk = cls if cls in ("open", "earned", "sealed") else ("earned" if layer == "truth" else "open")
                cid = f"lore_{nid}_{slug(heading)}_{ordinal:02d}"
                if len(cid) > 100:
                    cid = f"lore_{slug(nid, 40)}_{ordinal:02d}"
                chunks.append(
                    {
                        "id": cid,
                        "topic": nid,
                        "heading": heading,
                        "layer": layer,
                        "disclosure": cls_chunk,
                        "audience": audience,
                        "reveal_when": reveal_when if cls_chunk == "earned" else None,
                        "subjects": subjects_of(piece, nid, stem2id),
                        "text": text,
                        "_source": note.rel,
                        "_line": line,
                        "_class_source": source,
                        "_kind": kind,
                        "_words": word_count(text),
                    }
                )
            if derive_audience(note, heading, cls, body, zone)["scope"] == "faction":
                groups = derive_audience(note, heading, cls, body, zone).get("groups", [])
                for gid in groups:
                    if gid != "self" and not gid.startswith(("faction_", "race_")):
                        warnings.append(f"{note.rel}: '{heading}' has an audience group '{gid}' that is not a faction_/race_ id")
    return chunks, warnings


# ─── report ────────────────────────────────────────────────────────────────────


def pct(values: list[int], p: float) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(len(ordered) * p))]


def report(chunks: list[dict], npcs: list[dict], warnings: list[str], limit: int) -> str:
    out: list[str] = []
    words = sum(c["_words"] for c in chunks)
    out.append("Lore corpus report (Step 14 / PR-14)")
    out.append("=" * 60)
    out.append(f"chunks:          {len(chunks)}")
    out.append(f"words / tokens:  {words} / ~{int(words * 1.33)}")
    out.append(f"distinct topics: {len({c['topic'] for c in chunks})}")
    out.append("")
    out.append("By disclosure class")
    for cls in ("open", "earned", "sealed"):
        n = [c for c in chunks if c["disclosure"] == cls]
        out.append(f"  {cls:<8} {len(n):>5} chunks, {sum(c['_words'] for c in n):>6} words")
    out.append("")
    out.append("By layer")
    for layer in ("truth", "official", "myth", "rival"):
        n = [c for c in chunks if c["layer"] == layer]
        if n:
            out.append(f"  {layer:<9} {len(n):>5}")
    out.append("")
    lengths = [c["_words"] for c in chunks]
    out.append("Chunk length (words)")
    out.append(f"  median {pct(lengths, 0.5)}   p90 {pct(lengths, .9)}   p99 {pct(lengths, .99)}   max {max(lengths) if lengths else 0}")
    over = [c for c in chunks if c["_words"] > MAX_WORDS]
    out.append(
        f"  over the {MAX_WORDS}-word cap: {len(over)} (a single sentence longer than the cap; "
        "the platform's truncate-or-reject rule applies)"
    )
    out.append("")
    scopes = {}
    for c in chunks:
        scopes[c["audience"]["scope"]] = scopes.get(c["audience"]["scope"], 0) + 1
    out.append("Audience scope (derived; conventions 7.5)")
    for scope, n in sorted(scopes.items(), key=lambda kv: -kv[1]):
        out.append(f"  {scope:<8} {n:>5} chunks")
    if npcs:
        fan = sorted(sum(1 for c in chunks if knows(c["audience"], n)) for n in npcs)
        out.append("")
        out.append(f"Fan-out: chunks in scope for one NPC ({len(npcs)} NPCs)")
        out.append(f"  min {fan[0]}   median {fan[len(fan) // 2]}   p90 {fan[int(len(fan) * .9)]}   max {fan[-1]}")
        top = sorted(npcs, key=lambda n: -sum(1 for c in chunks if knows(c["audience"], n)))[:limit]
        for n in top:
            count = sum(1 for c in chunks if knows(c["audience"], n))
            out.append(f"  {n['id']:<34} {count:>5}  ({len(n['groups'])} group(s), zone {n['zone'] or '-'})")
    out.append("")
    with_subject = [c for c in chunks if len(c["subjects"]) > 1]
    out.append("Subject coverage (retrieval narrowing)")
    out.append(f"  chunks with a subject besides their own topic: {len(with_subject)}/{len(chunks)} ({100 * len(with_subject) // max(1, len(chunks))}%)")
    counts: dict[str, int] = {}
    for c in chunks:
        for s in c["subjects"]:
            counts[s] = counts.get(s, 0) + 1
    for sid, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:limit]:
        out.append(f"  {sid:<40} {n:>5}")
    spread = [n for sid, n in counts.items() if not sid.startswith("topic_")]
    if spread:
        out.append(
            f"  a subject selects median {pct(spread, .5)} chunks (p90 {pct(spread, .9)}, max {max(spread)}); "
            f"{sum(1 for n in spread if n <= 12)}/{len(spread)} subjects select 12 or fewer"
        )
    out.append("")
    if warnings:
        out.append(f"Warnings ({len(warnings)})")
        for w in warnings[:limit * 3]:
            out.append(f"  {w}")
        out.append("")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Export the Lore corpus and report its calibration numbers.")
    ap.add_argument("--json", metavar="PATH", help="write every chunk record as JSON")
    ap.add_argument("--limit", type=int, default=8, help="rows per ranked list (default 8)")
    args = ap.parse_args(argv)

    notes = [n for n in lint.load_notes() if n.rel.startswith("world/")]
    chunks, warnings = build_chunks(notes)
    npcs = npc_index(notes)
    print(report(chunks, npcs, warnings, args.limit))
    if args.json:
        Path(args.json).write_text(json.dumps(chunks, indent=1, ensure_ascii=False) + "\n")
        print(f"wrote {len(chunks)} chunk records to {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

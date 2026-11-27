#!/usr/bin/env python3
"""Render maps/atlas-features.md from maps/atlas-features.yaml.

The YAML is the authored data; this file is a deterministic view of it: every section the data
declares becomes a table, and the derived values (grid references, bearings, travel days) are
computed here so they cannot drift.

**The prose is data too.** A world's title, summary, section headings, reading notes, GM sections
and links live in the YAML (`title`, `summary`, `labels`, `notes`, `gm_sections`, `links`); a world
that sets none of them still gets a readable register. This module knows no world's geography.

    python3 tools/atlas_tables.py            # write the file
    python3 tools/atlas_tables.py --check    # exit 1 if the file is out of date
"""

import json
import math
import os
import sys
from pathlib import Path

import atlas_yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "maps", "atlas-features.yaml")
OUT = os.path.join(ROOT, "maps", "atlas-features.md")

# Generic paces; a world may override or extend them with `travel:` in its YAML.
KM_PER_DAY = {"standard": (25, 30), "difficult": (17.5, 21), "trackless": (12.5, 15)}


# ---------------------------------------------------------------------------
# derived values
# ---------------------------------------------------------------------------
def letters(index: int) -> str:
    """0 -> A, 25 -> Z, 26 -> AA. A grid column label."""
    out = ""
    index += 1
    while index:
        index, rem = divmod(index - 1, 26)
        out = chr(ord("A") + rem) + out
    return out


def ref(x, y, x0, y0, step) -> str:
    """A grid reference in a frame that starts at (x0, y0): column letter, row number from 1."""
    col = max(0, int((x - x0) // step))
    row = max(0, int((y - y0) // step)) + 1
    return f"{letters(col)}{row:02d}"


def bearing(a, b):
    ax, ay = a
    bx, by = b
    ang = math.degrees(math.atan2(bx - ax, by - ay)) % 360
    pts = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW",
           "W", "WNW", "NW", "NNW"]
    return ang, pts[int((ang + 11.25) // 22.5) % 16]


def days(km, terrain, paces=None):
    paces = {**KM_PER_DAY, **(paces or {})}
    lo, hi = paces.get(terrain, paces["standard"])
    if not hi:
        return "instant"
    a, b = km / hi, km / lo
    return f"{a:.0f}" if f"{a:.0f}" == f"{b:.0f}" else f"{a:.0f}–{b:.0f}"


def human(km):
    return f"{km:,}"


def extent(e):
    if "x" in e and "y" in e:
        return f"x {e['x']:,}, y {e['y']:,}"
    if "bounds" in e:
        x0, y0, x1, y1 = e["bounds"]
        return f"x {x0:,}–{x1:,}, y {y0:,}–{y1:,}"
    if "points" in e:
        pts = atlas_yaml.points(e["points"])
        (x0, y0), (x1, y1) = pts[0], pts[-1]
        tail = "" if len(pts) == 2 else f" · {len(pts)} points"
        return f"({x0:,.0f}, {y0:,.0f}) → ({x1:,.0f}, {y1:,.0f}){tail}"
    if e.get("global_x") and e.get("global_y"):
        gx, gy = e["global_x"], e["global_y"]
        return f"global x {gx[0]:,} to {gx[1]:,}, y {gy[0]:,} to {gy[1]:,}"
    return ""


NAMES = {}


def _first_point(e):
    if "x" in e and "y" in e:
        return e["x"], e["y"]
    if "bounds" in e:
        return e["bounds"][0], e["bounds"][1]
    if "points" in e:
        return atlas_yaml.points(e["points"])[0]
    return None


def frame_of(e, data):
    return e.get("frame") or atlas_yaml.default_frame(data)


def grid_of(e, data):
    """The grid reference for an entry, in the terms its frame declares.

    A frame with a `prefix` gets a prefixed local reference (100 km by default); one with `grid_km`
    gets a master reference of that step; the default frame gets a 250 km master reference; a frame
    named `world` gets no reference. These are display rules, not a world's geography: each is set
    by the frame itself.
    """
    point = _first_point(e)
    if point is None:
        return ""
    frame_name = frame_of(e, data)
    meta = atlas_yaml.frames(data).get(frame_name) or {}
    x0, y0 = meta.get("x", [0, 0])[0], meta.get("y", [0, 0])[0]
    x, y = point
    if meta.get("prefix"):
        return f"{meta['prefix']} {ref(x, y, x0, y0, meta.get('grid_km', 100))}"
    if meta.get("grid_km"):
        return ref(x, y, x0, y0, meta["grid_km"])
    if frame_name == "world":
        return "world"
    step = 250 if frame_name == atlas_yaml.default_frame(data) else 100
    return ref(x, y, x0, y0, step)


def note(e):
    bits = []
    for k in ("note", "draw"):
        if e.get(k):
            bits.append(str(e[k]))
    if e.get("also_known_as"):
        bits.append(f"also {e['also_known_as']}")
    if e.get("area_million_km2"):
        bits.append(f"{e['area_million_km2']}M km²")
    if e.get("latitude"):
        bits.append(f"lat. {e['latitude']}")
    if e.get("climate"):
        bits.append(str(e["climate"]))
    if e.get("population"):
        bits.append(f"pop. {e['population']:,}")
    if e.get("population_each"):
        bits.append(f"{e['count']} × {e['population_each']}")
    if e.get("length_km"):
        bits.append(f"{e['length_km']:,} km")
    if e.get("origin"):
        bits.append(str(e["origin"]).replace("-", " "))
    if e.get("magic_class"):
        bits.append(f"magic: {e['magic_class']}")
    if e.get("god"):
        bits.append(f"god: {e['god']}")
    if e.get("holder"):
        bits.append(f"held by {NAMES.get(e['holder'], e['holder'])}")
    return "; ".join(bits)


def status_cell(e):
    st = e.get("status", "canon")
    return {"canon": "C", "proposed": "P", "retired": "retired"}[st]


def heading(key, data):
    labels = data.get("labels") or {}
    if key in labels:
        return labels[key]
    return key.replace("_", " ").capitalize()


def frame_label(name, meta):
    return meta.get("name") or name.replace("_", " ")


# ---------------------------------------------------------------------------
# tables
# ---------------------------------------------------------------------------
def generic_table(entries, data):
    cols = ("Feature", "Extent", "Grid", "Status", "Notes")
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for e in entries:
        out.append(f"| **{e['name']}** | {extent(e)} | {grid_of(e, data)} | "
                   f"{status_cell(e)} | {note(e)} |")
    return out


def leg_table(legs, by_id, data):
    out = ["| Leg | km | Bearing | Terrain | Days | Notes |", "|---|---|---|---|---|---|"]
    paces = data.get("travel") or {}
    for leg in legs:
        a, b = by_id.get(leg["from"]), by_id.get(leg["to"])
        if not a or not b or "x" not in a or "x" not in b:
            continue
        km = leg["km"]
        ang, pt = bearing((a["x"], a["y"]), (b["x"], b["y"]))
        terrain = leg.get("terrain", "standard")
        out.append(f"| {a['name']} → {b['name']} | {km:,} | {pt} ({ang:.0f}°) | {terrain} | "
                   f"{days(km, terrain, paces)} | {leg.get('note', '')} |")
    return out


def plates_table(plates, data):
    out = ["| Plate | Area | Paper | Scale | 1 cm = | Grid | File |",
           "|---|---|---|---|---|---|---|"]
    for p in plates:
        w, h = p["paper"]
        km_per_mm = p["scale"] / 1_000_000
        if "window" in p:
            frame = (f"x {p['window'][0]:,}–{p['window'][1]:,}, "
                     f"y {p['window'][2]:,}–{p['window'][3]:,}")
        else:
            meta = atlas_yaml.frames(data).get(p.get("frame"), {})
            frame = f"{frame_label(p.get('frame'), meta)} frame" if p.get("frame") else "—"
        kind = "GM overlay" if p.get("gm") else "plate"
        out.append(f"| **{p['id']}** — {p['title']} | {frame} | {w} × {h} mm | "
                   f"1:{p['scale']:,} | {km_per_mm:g} km | {p['grid']:,} km | "
                   f"`svg/{p['file']}` ({kind}) |")
    return out


def frames_table(data):
    out = ["| Frame | Extent (km) | Grid |", "|---|---|---|"]
    default = atlas_yaml.default_frame(data)
    for name, meta in atlas_yaml.frames(data).items():
        x0, x1 = meta["x"]
        y0, y1 = meta["y"]
        if name == "world" and not meta.get("prefix") and not meta.get("grid_km"):
            grid = "world"
        elif meta.get("prefix"):
            grid = f"`{meta['prefix']}` + {meta.get('grid_km', 100)} km local"
        else:
            grid = f"{meta.get('grid_km', 250 if name == default else 100)} km master"
        out.append(f"| {frame_label(name, meta)} | x {x0:,}–{x1:,}, y {y0:,}–{y1:,} | {grid} |")
    return out


def table_for(entries, data):
    if entries and all("from" in e and "to" in e for e in entries):
        by_id = {e["id"]: e for section in atlas_yaml.sections(data).values()
                 for e in section if "id" in e}
        return leg_table(entries, by_id, data)
    if entries and any("paper" in e and "scale" in e for e in entries):
        return plates_table(entries, data)
    return generic_table(entries, data)


# ---------------------------------------------------------------------------
def render(data):
    by_id = {}
    NAMES.clear()
    for entries in atlas_yaml.sections(data).values():
        for e in entries:
            if "id" in e:
                by_id[e["id"]] = e
                NAMES[e["id"]] = e.get("name", e["id"])

    title = data.get("title") or "Atlas Features"
    summary = data.get("summary") or (
        "Every drawable feature this world's map data declares, by section, with its extent, grid "
        "reference and status. **This file is generated** from `maps/atlas-features.yaml`; do not "
        "edit it by hand.")
    links = data.get("links") or ["[[maps/_index|Maps]]"]
    gm = set(data.get("gm_sections") or ())
    notes = data.get("notes") or [
        "**x, y** are km in the entry's own frame; every frame's extent is in the table below.",
        "**Grid** is the reference the frame declares: a master grid, a prefixed local grid, or "
        "`world`.",
        "**Status:** `C` = canon (a note states it), `P` = proposed (a map position awaiting "
        "canon), `retired` = kept for one refresh so the diff shows the retirement.",
        "Derived values (grid references, bearings, travel days) are computed here; the drawings "
        "are the world's own renderer's.",
    ]

    L = []
    L.append("---")
    L.append("id: topic_atlas_features")
    L.append("kind: TOPIC")
    L.append(f"title: {json.dumps(title)}")
    L.append("aliases: []")
    L.append("name_status: working")
    L.append("status: working")
    L.append("engine: false")
    L.append(f"era: {data.get('era', 'present')}")
    L.append("tags: []")
    L.append(f"disclosure: {data.get('disclosure', 'earned')}")
    L.append("---")
    L.append("")
    L.append(f"# {title}")
    L.append("")
    L.append(f"**Summary:** {summary}")
    L.append("")
    L.append("## How to read the tables")
    L.append("")
    for line in notes:
        L.append(f"- {line}")
    L.append("")

    if atlas_yaml.frames(data):
        L.append("## Frames")
        L.append("")
        L += frames_table(data)
        L.append("")

    for key, entries in atlas_yaml.sections(data).items():
        L.append(f"## {heading(key, data)}")
        L.append("")
        if key in gm:
            L.append("**Disclosure:** earned")
            L.append("")
            L.append("The secret layer: it is drawn on the GM sheets only.")
            L.append("")
        L += table_for(entries, data)
        L.append("")

    L.append("## Links")
    L.append("")
    L.append(" · ".join(links))
    L.append("")
    return "\n".join(L)


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    data = atlas_yaml.load(DATA)
    atlas_yaml.validate(data)
    text = render(data)
    if "--check" in args:
        current = Path(OUT).read_text(encoding="utf-8") if Path(OUT).exists() else ""
        if current != text:
            print(f"{OUT} is out of date: run python3 tools/atlas_tables.py")
            return 1
        print(f"{OUT} is up to date")
        return 0
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(f"wrote {os.path.relpath(OUT, ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

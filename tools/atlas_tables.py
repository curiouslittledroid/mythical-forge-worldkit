#!/usr/bin/env python3
"""Render maps/atlas-features.md from maps/atlas-features.yaml.

The YAML is the authored data; this file is a deterministic view of it: one
section per feature kind, a table per section, derived values (grid refs,
bearings, travel days) computed here so they cannot drift.

    python3 tools/atlas_tables.py            # write the file
    python3 tools/atlas_tables.py --check    # exit 1 if the file is out of date
"""

import math
import os
import sys

import atlas_yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "maps", "atlas-features.yaml")
OUT = os.path.join(ROOT, "maps", "atlas-features.md")

KM_PER_DAY = {"standard": (25, 30), "difficult": (17.5, 21), "trackless": (12.5, 15),
              "gate": (0, 0)}

# A site's era of foundation. Authored as a slug in the YAML, printed as words.
ORIGIN_LABEL = {
    "golden-age": "golden age",
    "war-wound": "war wound",
    "choir": "Choir",
    "sentinel": "sentinel",
}


# ---------------------------------------------------------------------------
# derived values
# ---------------------------------------------------------------------------
def master_ref(x, y):
    """250 km grid reference: column A-R, row 01-11."""
    col = int(min(max(x, 0), 4499) // 250)
    row = int(min(max(y, 0), 2699) // 250) + 1
    return f"{'ABCDEFGHIJKLMNOPQR'[col]}{row:02d}"


def fine_ref(x, y):
    """100 km grid reference, e.g. V17, in the same origin."""
    cols = [a + b for a in [""] + list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
            for b in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"]
    return f"{cols[int(x // 100)]}{int(y // 100) + 1:02d}"


def bearing(a, b):
    ax, ay = a
    bx, by = b
    ang = math.degrees(math.atan2(bx - ax, by - ay)) % 360
    pts = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW",
           "W", "WNW", "NW", "NNW"]
    return ang, pts[int((ang + 11.25) // 22.5) % 16]


def days(km, terrain):
    lo, hi = KM_PER_DAY.get(terrain, KM_PER_DAY["standard"])
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
    return ""


NAMES = {}


def grid_of(e):
    frame = e.get("frame", "heartland")
    if "x" in e and "y" in e:
        x, y = e["x"], e["y"]
    elif "bounds" in e:
        x, y = e["bounds"][0], e["bounds"][1]
    elif "points" in e:
        x, y = atlas_yaml.points(e["points"])[0]
    else:
        return ""
    local = {"far_reach": "FR", "severed_west": "SW",
             "frostbound_north": "FN", "bloom": "BL"}
    if frame in local:
        return local[frame] + " " + fine_ref(x, y)
    if frame == "world":
        return "world"
    return master_ref(x, y)


def note(e):
    bits = []
    for k in ("note", "draw"):
        if e.get(k):
            bits.append(str(e[k]))
    if e.get("also_known_as"):
        bits.append(f"also {e['also_known_as']}")
    if e.get("population"):
        bits.append(f"pop. {e['population']:,}")
    if e.get("population_each"):
        bits.append(f"{e['count']} × {e['population_each']}")
    if e.get("length_km"):
        bits.append(f"{e['length_km']:,} km")
    if e.get("origin"):
        origin = e["origin"]
        bits.append(ORIGIN_LABEL.get(origin, str(origin)))
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


# ---------------------------------------------------------------------------
# tables
# ---------------------------------------------------------------------------
def point_table(entries, cols=("Feature", "x, y", "Grid", "Status", "Notes")):
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for e in entries:
        if "x" not in e:
            continue
        x, y = e["x"], e["y"]
        grid = grid_of(e)
        out.append(f"| **{e['name']}** | {x:,}, {y:,} | {grid} | {status_cell(e)} | {note(e)} |")
    return out


def area_table(entries, cols=("Feature", "Extent", "Grid", "Status", "Notes")):
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for e in entries:
        grid = grid_of(e)
        out.append(f"| **{e['name']}** | {extent(e)} | {grid} | {status_cell(e)} | {note(e)} |")
    return out


def landmass_table(entries):
    out = ["| Landmass | Area | Latitude | Global x | Global y | Climate |",
           "|---|---|---|---|---|---|"]
    for e in entries:
        gx = e["global_x"]
        gy = e["global_y"]
        out.append(f"| **{e['name']}** | {e['area_million_km2']}M km² | {e['latitude']} | "
                   f"{gx[0]:,} to {gx[1]:,} | {gy[0]:,} to {gy[1]:,} | {e.get('climate', '')} |")
    return out


def leg_table(legs, by_id):
    out = ["| Leg | km | Bearing | Terrain | Days | Notes |", "|---|---|---|---|---|---|"]
    for leg in legs:
        a, b = by_id[leg["from"]], by_id[leg["to"]]
        if "x" not in a or "x" not in b:
            continue
        km = leg["km"]
        ang, pt = bearing((a["x"], a["y"]), (b["x"], b["y"]))
        out.append(f"| {a['name']} → {b['name']} | {km:,} | {pt} ({ang:.0f}°) | "
                   f"{leg.get('terrain', 'standard')} | "
                   f"{days(km, leg.get('terrain', 'standard'))} | {leg.get('note', '')} |")
    return out


def plates_table(plates):
    out = ["| Plate | Area | Paper | Scale | 1 cm = | Grid | File |",
           "|---|---|---|---|---|---|---|"]
    for p in plates:
        w, h = p["paper"]
        km_per_mm = p["scale"] / 1_000_000
        pretty = {"heartland": "the Heartland", "far_reach": "the Far Reach",
                  "severed_west": "the Severed West",
                  "frostbound_north": "the Frostbound North",
                  "bloom": "the Bloom", "world": "the world"}
        frame = f"x {p['window'][0]:,}–{p['window'][1]:,}, y {p['window'][2]:,}–{p['window'][3]:,}" \
            if "window" in p else f"{pretty[p['frame']]} frame"
        kind = "GM overlay" if p.get("gm") else "plate"
        out.append(f"| **{p['id']}** — {p['title']} | {frame} | {w} × {h} mm | "
                   f"1:{p['scale']:,} | {km_per_mm:g} km | {p['grid']:,} km | "
                   f"`svg/{p['file']}` ({kind}) |")
    return out


def files_table(plates, data):
    out = ["| File | Sheet | Notes |", "|---|---|---|"]
    for p in plates:
        w, h = p["paper"]
        out.append(f"| `svg/{p['file']}` | {w} × {h} mm, 1:{p['scale']:,} | "
                   f"{p['title']}{' (GM tracing sheet)' if p.get('gm') else ''}, "
                   f"grid {p['grid']:,} km |")
    return out


# ---------------------------------------------------------------------------
def render(data):
    by_id = {}
    NAMES.clear()
    for section, entries in data.items():
        if isinstance(entries, list):
            for e in entries:
                if "id" in e:
                    by_id[e["id"]] = e
                    NAMES[e["id"]] = e.get("name", e["id"])

    L = []
    L.append("""---
id: topic_atlas_features
kind: TOPIC
title: Atlas Features
aliases: [The Feature Register]
name_status: working
status: working
engine: false
era: present
tags: []
disclosure: earned
---

# Atlas Features

**Summary:** Every drawable feature in the world, by kind, with its coordinate, grid reference and status. **This file is generated** from `maps/atlas-features.yaml` by `tools/atlas_tables.py`; do not edit it by hand. The YAML is the authored data; [[atlas-register]] is the brief that explains it.

## How to read the tables

- **x, y** are km in the feature's own frame. The Heartland, the Severed West, the Frostbound North and the Bloom each measure x east of their west coast and y north of their south coast. The Far Reach has its own local frame, and Plate D uses the world frame.
- **Grid** is the 250 km master reference (column A–R, row 01–11) for the Heartland. The other continents show a 100 km local reference with their frame's prefix: `FR` the Far Reach, `SW` the Severed West, `FN` the Frostbound North, `BL` the Bloom.
- **Status:** `C` = canon (a place note states it), `P` = proposed map position (in the YAML, awaiting canon).
- Coastlines are not listed: they are unsurveyed, and drawing them is the cartographer's job.
""")
    S = data
    L.append("## Landmasses")
    L.append("")
    L += landmass_table(S["landmasses"])
    L.append("")

    L.append("## Regions")
    L.append("")
    L += area_table(S["regions"])
    L.append("")

    L.append("## Seas and lakes")
    L.append("")
    L.append("Water bodies include the Dry Sea's fossil basin; draw the old shore dashed.")
    L.append("")
    L += area_table(S["seas_and_lakes"])
    L.append("")

    L.append("## Rivers")
    L.append("")
    L += area_table(S["rivers"])
    L.append("")

    L.append("## Relief")
    L.append("")
    L += area_table(S["relief"])
    L.append("")

    L.append("## Deserts and plains")
    L.append("")
    L += area_table(S["deserts_and_plains"])
    L.append("")

    L.append("## Cities")
    L.append("")
    L += point_table(S["cities"])
    L.append("")

    L.append("## Towns and villages")
    L.append("")
    L += point_table(S["towns"])
    L.append("")

    L.append("## Dwarven holds")
    L.append("")
    L += point_table(S["holds"])
    L.append("")

    L.append("## Ruins and sites")
    L.append("")
    L += point_table(S["ruins"])
    L.append("")

    L.append("## Sentinels")
    L.append("")
    L += point_table(S["sentinels"])
    L.append("")

    L.append("## Leylines, wells and knots")
    L.append("")
    L += area_table(S["leylines"])
    L.append("")

    L.append("## Routes")
    L.append("")
    L += area_table(S["routes"])
    L.append("")

    L.append("## Route legs")
    L.append("")
    L.append("Straight-line km from the coordinates; days assume 25–30 km/day on standard "
             "ground, slower on difficult and trackless going. A real road meanders, so give "
             "each drawn road its own rough length.")
    L.append("")
    L += leg_table(S["route_legs"], by_id)
    L.append("")

    L.append("## Holy sites")
    L.append("")
    L += point_table(S["holy_sites"])
    L.append("")

    L.append("## Territories")
    L.append("")
    L += area_table(S["territories"])
    L.append("")

    L.append("## GM overlay")
    L.append("")
    L.append("**Disclosure:** earned")
    L.append("")
    L.append("The secret layer, drawn on the GM tracing sheets only.")
    L.append("")
    L += point_table(S["gm_overlay"])
    L.append("")

    L.append("## Sheets and files")
    L.append("")
    L += plates_table(S["plates"])
    L.append("")

    L.append("## Links")
    L.append("")
    L.append("[[atlas-register]] · [[geography-data]] · [[the-planet]] · [[maps/_index|Maps]] · "
             "[[the-heartland]] · [[the-far-reach]] · [[open-questions]]")
    L.append("")
    return "\n".join(L)


def main():
    data = atlas_yaml.load(DATA)
    atlas_yaml.validate(data)
    text = render(data)
    if "--check" in sys.argv:
        current = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
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

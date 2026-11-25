#!/usr/bin/env python3
"""Read the atlas feature file (maps/atlas-features.yaml) and validate it.

The YAML reader itself is `yaml_subset.py`, shared with `kit_config.py`; this module owns the
atlas **schema** and the command-line check. Standard library only.

    python3 tools/atlas_yaml.py maps/atlas-features.yaml

Exits 1 with `INVALID path: file:line: reason` on the first schema error. `load`, `SchemaError`
and `points` are what the other atlas tools import from here.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yaml_subset import SchemaError, load  # noqa: F401  re-exported for make_atlas.py


# ---------------------------------------------------------------------------
# schema
# ---------------------------------------------------------------------------
FRAMES = {"heartland", "far_reach", "severed_west", "frostbound_north", "bloom", "world"}

SECTIONS = [
    # (section, required keys, geometry: point|bounds|points|none)
    ("landmasses", ["id", "name", "area_million_km2", "latitude"], "none"),
    ("regions", ["id", "name", "type", "frame"], "bounds"),
    ("seas_and_lakes", ["id", "name", "type"], "any"),
    ("rivers", ["id", "name"], "points"),
    ("relief", ["id", "name", "type"], "any"),
    ("deserts_and_plains", ["id", "name", "type"], "bounds"),
    ("cities", ["id", "name", "type", "x", "y"], "point"),
    ("towns", ["id", "name", "type", "x", "y"], "point"),
    ("holds", ["id", "name", "x", "y"], "point"),
    ("ruins", ["id", "name", "type", "x", "y"], "point"),
    ("sentinels", ["id", "name", "x", "y"], "point"),
    ("leylines", ["id", "name", "type"], "points_or_point"),
    ("routes", ["id", "name", "type"], "points"),
    ("route_legs", ["from", "to", "km"], "none"),
    ("holy_sites", ["id", "name", "god", "x", "y"], "point"),
    ("territories", ["id", "name", "holder"], "bounds"),
    ("gm_overlay", ["id", "name", "type", "x", "y"], "point"),
]

STATUSES = {"canon", "proposed", "retired"}
TYPES = {
    "regions": {"forest", "fae", "storm", "scrub", "coast", "warm", "lee", "plateau", "highland",
                "steppe", "crater", "eddy", "tundra", "ice_sheet", "jungle", "canopy", "basin"},
    "seas_and_lakes": {"dry_sea", "dry_gulf", "brine_pool", "lake", "old_shore"},
    "relief": {"range", "pass", "glacier", "badlands", "plateau", "breach", "seam"},
    "deserts_and_plains": {"salt_desert", "ash_plain", "scrub"},
    "cities": {"city", "sealed_city"},
    "towns": {"town", "village", "port", "camp"},
    "routes": {"road", "track", "aqueduct", "deeproad", "sealane", "coast"},
    "ruins": {"ruin", "ruin_port", "dungeon", "battlefield", "fortress", "wreck_field",
              "monument", "capital"},
    "leylines": {"line", "knot", "well", "remnant"},
    "routes": {"road", "track", "aqueduct", "deeproad", "sealane", "coast"},
    "gm_overlay": {"seed_site", "hearth", "hushed", "stronghold", "trade", "well",
                   "wyrm", "cantor", "silent_city", "sentinel"},
}


def validate(data, path="<data>"):
    """Check the schema, ids, references and geometry. Raises SchemaError."""
    if data.get("schema") != 1:
        raise SchemaError("schema must be 1")
    frames = data.get("frames") or {}
    for name in FRAMES:
        f = frames.get(name)
        if not f:
            raise SchemaError(f"missing frame '{name}'")
        for k in ("x", "y"):
            if k not in f or len(f[k]) != 2:
                raise SchemaError(f"frame '{name}' needs x and y as [min, max]")

    ids = {}
    for section, required, geom in SECTIONS:
        entries = data.get(section)
        if entries is None:
            raise SchemaError(f"missing section '{section}'")
        if not isinstance(entries, list):
            raise SchemaError(f"section '{section}' must be a list")
        for i, e in enumerate(entries):
            where = f"{section}[{i}]"
            if not isinstance(e, dict):
                raise SchemaError(f"{where} is not a mapping")
            for k in required:
                if k not in e:
                    raise SchemaError(f"{where} missing '{k}'")
            if "id" in e:
                if e["id"] in ids:
                    raise SchemaError(f"duplicate id '{e['id']}' ({where} and {ids[e['id']]})")
                ids[e["id"]] = where
            st = e.get("status", "canon")
            if st not in STATUSES:
                raise SchemaError(f"{where}: status '{st}' not in {sorted(STATUSES)}")
            if section in TYPES and e.get("type") and e["type"] not in TYPES[section]:
                raise SchemaError(
                    f"{where}: type '{e['type']}' not in {sorted(TYPES[section])}")
            if "source" not in e and section not in ("route_legs",):
                raise SchemaError(f"{where} missing 'source'")
            # geometry
            if geom == "point":
                if "x" not in e or "y" not in e:
                    raise SchemaError(f"{where} needs x and y")
            elif geom == "bounds":
                b = e.get("bounds")
                if not b or len(b) != 4:
                    raise SchemaError(f"{where} needs bounds [x0, y0, x1, y1]")
            elif geom == "points":
                if not e.get("points"):
                    raise SchemaError(f"{where} needs points")
            elif geom == "points_or_point":
                if not (e.get("points") or ("x" in e and "y" in e)):
                    raise SchemaError(f"{where} needs points or x/y")
            elif geom == "bounds_or_point":
                if not (e.get("bounds") or ("x" in e and "y" in e)):
                    raise SchemaError(f"{where} needs bounds or x/y")
            elif geom == "any":
                if not (e.get("points") or e.get("bounds") or ("x" in e and "y" in e)):
                    raise SchemaError(f"{where} needs points, bounds or x/y")
            if e.get("frame") and e["frame"] not in FRAMES:
                raise SchemaError(f"{where}: frame '{e['frame']}' not in {sorted(FRAMES)}")

    for i, leg in enumerate(data.get("route_legs", [])):
        for end in ("from", "to"):
            if leg.get(end) not in ids:
                raise SchemaError(f"route_legs[{i}]: '{end}' is not a known id ({leg.get(end)})")
    return True


def points(value):
    """Parse a 'points' string into a list of (x, y) tuples."""
    out = []
    if not value:
        return out
    for pair in str(value).split():
        x, _, y = pair.partition(",")
        out.append((float(x), float(y)))
    return out


if __name__ == "__main__":
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else "maps/atlas-features.yaml"
    try:
        d = load(path)
        validate(d)
    except SchemaError as exc:
        print(f"INVALID {path}: {exc}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"NOT FOUND {path}: run this from the repository root")
        sys.exit(1)
    total = sum(len(v) for k, v in d.items() if isinstance(v, list))
    print(f"ok: {len([k for k in d if isinstance(d[k], list)])} sections, {total} entries")

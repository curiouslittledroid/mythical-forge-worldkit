#!/usr/bin/env python3
"""Read the atlas feature file (maps/atlas-features.yaml) and validate it.

The YAML reader itself is `yaml_subset.py`, shared with `kit_config.py`; this module owns the
atlas **schema** and the command-line check. Standard library only.

**The schema is the kit's; the atlas is the world's.** Nothing here knows a world's frames, its
feature kinds or its type vocabulary: the file declares its frames, and every list-valued top-level
key is a section. What this validates is structure — a frame an entry names must be declared, an id
must be unique, geometry must be well formed — not a world's taxonomy. See
`meta/conventions/atlas.md`.

    python3 tools/atlas_yaml.py maps/atlas-features.yaml

Exits 1 with `INVALID path: file:line: reason` on the first schema error. `load`, `SchemaError`,
`points`, `frames`, `default_frame` and `sections` are what the other atlas tools import from here.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yaml_subset import SchemaError, load  # noqa: F401  re-exported for make_atlas.py


# ---------------------------------------------------------------------------
# schema
# ---------------------------------------------------------------------------
# Top-level keys that are not sections. A world may use others for its own renderer; only these
# have a meaning here, and a list-valued key is a section whatever else it is called.
SCALAR_KEYS = {"schema", "default_frame", "title", "summary", "disclosure", "era",
               "labels", "links", "notes", "gm_sections"}

# The status scale is the kit's: it is what the diff and the audit understand.
STATUSES = {"canon", "proposed", "retired"}

# Frame fields. `x` and `y` are required; the rest change the generated view.
FRAME_REQUIRED = ("x", "y")


def frames(data) -> dict:
    """The declared frames, name -> {x, y, name?, prefix?, grid_km?}."""
    return data.get("frames") or {}


def default_frame(data):
    """The frame an entry without one belongs to: `default_frame:`, else `world`, else the first."""
    declared = frames(data)
    name = data.get("default_frame")
    if name:
        return name
    if "world" in declared:
        return "world"
    return next(iter(declared), None)


def sections(data) -> dict:
    """Every list-valued top-level key that is not a reserved scalar, in file order.

    That is what a section is: a world names its own kinds, so the file declares them.
    """
    return {key: value for key, value in data.items()
            if isinstance(value, list) and key not in SCALAR_KEYS}


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate(data, path="<data>"):
    """Check the schema, ids, frames and geometry. Raises SchemaError."""
    if data.get("schema") != 1:
        raise SchemaError("schema must be 1")

    declared = frames(data)
    if not declared:
        raise SchemaError("missing 'frames': declare each frame's x and y extent")
    for name, frame in declared.items():
        if not isinstance(frame, dict):
            raise SchemaError(f"frames.{name} is not a mapping")
        for key in FRAME_REQUIRED:
            extent = frame.get(key)
            if not isinstance(extent, list) or len(extent) != 2:
                raise SchemaError(f"frames.{name}.{key} must be [min, max]")
            if not all(_is_number(v) for v in extent):
                raise SchemaError(f"frames.{name}.{key} must be two numbers")
    fallback = default_frame(data)
    if fallback not in declared:
        raise SchemaError(f"default_frame '{fallback}' is not a declared frame "
                          f"({', '.join(sorted(declared))})")

    ids = {}
    for section, entries in sections(data).items():
        for i, e in enumerate(entries):
            where = f"{section}[{i}]"
            if not isinstance(e, dict):
                raise SchemaError(f"{where} is not a mapping")
            if "id" in e:
                if e["id"] in ids:
                    raise SchemaError(f"duplicate id '{e['id']}' ({where} and {ids[e['id']]})")
                ids[e["id"]] = where
            # A route leg is the one entry that is a pair, not a feature; a plate carries a
            # `title` rather than a `name`.
            if "name" not in e and "title" not in e and not ("from" in e and "to" in e):
                raise SchemaError(f"{where} needs 'name' (or title, or from/to for a route leg)")
            status = e.get("status", "canon")
            if status not in STATUSES:
                raise SchemaError(f"{where}: status '{status}' not in {sorted(STATUSES)}")
            # Geometry: whatever is present must be well formed. Which sections need which is the
            # world's rule, not the kit's.
            for key in ("x", "y"):
                if key in e and not _is_number(e[key]):
                    raise SchemaError(f"{where}.{key} must be a number")
            if ("x" in e) != ("y" in e):
                raise SchemaError(f"{where} needs both x and y, or neither")
            if "bounds" in e:
                b = e["bounds"]
                if not isinstance(b, list) or len(b) != 4 or not all(_is_number(v) for v in b):
                    raise SchemaError(f"{where}.bounds must be [x0, y0, x1, y1]")
            if "points" in e:
                if not isinstance(e["points"], str) or not e["points"].strip():
                    raise SchemaError(f"{where}.points must be a string of x,y pairs")
                try:
                    points(e["points"])
                except ValueError:
                    raise SchemaError(f"{where}.points: '{e['points']}' is not 'x,y x,y ...'")
            if e.get("frame") and e["frame"] not in declared:
                raise SchemaError(f"{where}: frame '{e['frame']}' not in {sorted(declared)}")
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
    total = sum(len(v) for v in sections(d).values())
    print(f"ok: {len(sections(d))} sections, {total} entries")

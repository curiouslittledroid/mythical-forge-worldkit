#!/usr/bin/env python3
"""Read a small, strict YAML subset without PyYAML (standard library only).

The worldkit's own data files use a deliberately small subset so that they diff cleanly
and can be read anywhere Python runs. Extracted from `atlas_yaml.py`, which had the only
copy; `kit_config.py` is the second consumer.

  * mappings by indentation, two spaces per level
  * sequences, introduced by "- " at the parent's indent + 2: scalars or mappings
  * scalar values: plain, "double" or 'single' quoted, integers, true/false, null
  * flat flow sequences of scalars: [0, 4500]
  * comments: whole-line (# ...) or trailing (a `#` preceded by whitespace, outside quotes)
  * no anchors, no multi-line strings, no flow mappings

A value containing ": " must be quoted. Use a flow sequence for a list of scalars; a block
sequence of scalars works too. `SchemaError` carries `file:line` for every refusal.

Use:
    import yaml_subset
    data = yaml_subset.load("world.config.yaml")   # raises SchemaError
"""

import re

NUMBER_RE = re.compile(r"^-?\d+(\.\d+)?$")
# A sequence item is a mapping only when its first token is a bare key. This keeps `- https://x`
# and `- "a: b"` as scalars, which a bare `":" in body` test would have broken.
KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_.-]*)\s*:(?:\s|$)")


class SchemaError(Exception):
    pass


def _strip_comment(raw):
    """Drop a trailing `# ...` comment: a `#` preceded by whitespace, outside quotes."""
    out = []
    quote = None
    for i, ch in enumerate(raw):
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == "#" and i > 0 and raw[i - 1] in " \t":
            break
        out.append(ch)
    return "".join(out)


def _value(raw):
    v = raw.strip()
    if not v:
        return None
    if v.startswith('"') and v.endswith('"'):
        return v[1:-1].replace('\\"', '"')
    if v.startswith("'") and v.endswith("'"):
        return v[1:-1].replace("''", "'")
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        if not inner:
            return []
        return [_value(p) for p in inner.split(",")]
    if v == "null" or v == "~":
        return None
    if v == "true":
        return True
    if v == "false":
        return False
    if NUMBER_RE.match(v):
        return int(v) if "." not in v else float(v)
    if ": " in v or v.endswith(":"):
        raise SchemaError(f"unquoted colon in value: {raw!r}")
    return v


def load(path):
    """Parse a file in the subset above into nested dicts and lists."""
    with open(path, encoding="utf-8") as fh:
        return load_text(fh.read(), str(path))


def load_text(text, path="<text>"):
    """Parse text in the subset above. `path` is only a label, used in every error message."""
    lines = text.split("\n")

    def val(raw):
        """`_value` with the file:line attached, so a scalar error is locatable."""
        try:
            return _value(raw)
        except SchemaError as exc:
            raise SchemaError(f"{path}:{lineno}: {exc}") from None

    first = _next_content(lines, 0)
    # A document whose first content line is a sequence item is a top-level sequence (the `flags`
    # block is one); everything else is a mapping.
    root = [] if first is not None and first[1].startswith("- ") else {}
    top_keys = {}
    # stack of (indent, container)
    stack = [(-1, root)]
    current_item = None  # the last sequence item, for its child keys

    for lineno, raw in enumerate(lines, 1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if "\t" in raw:
            raise SchemaError(f"{path}:{lineno}: tab character")
        indent = len(raw) - len(raw.lstrip(" "))
        text = raw.strip()

        while stack and indent <= stack[-1][0] and stack[-1][0] >= 0:
            stack.pop()
        parent = stack[-1][1]

        if text.startswith("- "):
            if not isinstance(parent, list):
                raise SchemaError(f"{path}:{lineno}: sequence item outside a list")
            body = _strip_comment(text[2:]).strip()
            if not body:
                item = {}
                parent.append(item)
                stack.append((indent, item))
                continue
            m = KEY_RE.match(body)
            if m is None:
                parent.append(val(body))  # a scalar item carries no children
                continue
            item = {m.group(1): val(body[m.end(1) + 1:])}
            parent.append(item)
            stack.append((indent, item))
            continue

        if ":" not in text:
            raise SchemaError(f"{path}:{lineno}: expected 'key: value'")
        if indent == 0 and isinstance(root, dict):
            # a repeated top-level key silently discards the first block: refuse it
            key0 = text.partition(":")[0].strip()
            if key0 in top_keys:
                raise SchemaError(
                    f"{path}:{lineno}: duplicate top-level key '{key0}' "
                    f"(first at line {top_keys[key0]})")
            top_keys[key0] = lineno
        key, _, rest = text.partition(":")
        key = key.strip()
        # Strip a trailing comment BEFORE deciding block-vs-scalar, so `site:   # a note` still
        # opens a block rather than being read as the value `None`.
        rest = _strip_comment(rest).strip()

        if rest:
            if not isinstance(parent, dict):
                raise SchemaError(f"{path}:{lineno}: key outside a mapping")
            parent[key] = val(rest)
            continue

        # block value: decide list or mapping by the next meaningful line
        if not isinstance(parent, dict):
            raise SchemaError(f"{path}:{lineno}: key '{key}' outside a mapping")
        nxt = _next_content(lines, lineno)
        if nxt is not None and nxt[1].startswith("- "):
            container = []
        else:
            container = {}
        parent[key] = container
        stack.append((indent, container))
        if isinstance(container, list):
            # a list introduced by "key:" then "- " at indent+2 is unusual here;
            # keep it working by pushing the list and letting items land in it.
            pass

    return root


def _next_content(lines, lineno):
    for i in range(lineno, len(lines)):
        raw = lines[i]
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        return i + 1, raw.strip()
    return None


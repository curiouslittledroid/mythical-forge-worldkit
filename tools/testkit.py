#!/usr/bin/env python3
"""Fixture helpers for the tool test suites.

Since T1 the tools are **config-driven**, so a fixture vault needs a `world.config.yaml` and the
vault blocks. Rather than keep a second, drifting copy of the world's, these helpers copy the
world's own config into the fixture and let a test override one vocabulary list. A change to the
real information architecture then shows up in the fixtures, which is the point: the exporter
tests run against a realistic config rather than an invented one.

    import testkit
    testkit.write_config(self.root)                          # the world's own IA
    testkit.write_config(self.root, published_tags=["choir"]) # one list replaced

Only `site-vocabulary` is written, because that is the block the exporter reads. A fixture that
also needs the calendar or the eras block writes its own note and points the config at it.
"""
from __future__ import annotations

from pathlib import Path

import kit_config

REAL_ROOT = Path(__file__).resolve().parent.parent
# The "real" config a fixture copies: the world's own when these tools are vendored into a world,
# or the kit's demo world when the tests run in the kit (whose root is not a world).
REAL_CONFIG = REAL_ROOT / "world.config.yaml"
if not REAL_CONFIG.is_file():
    REAL_CONFIG = REAL_ROOT / "template" / "example-world" / "world.config.yaml"

SITE_NOTE = """---
id: topic_site_decisions
kind: TOPIC
title: Site Decisions
name_status: working
status: working
engine: false
---

# Site Decisions

**Summary:** Fixture vocabulary for the site exporter's tests. Written by `tools/testkit.py`.

## Site vocabulary

```site-vocabulary
published_tags: {published_tags}
keystones: {keystones}
plot_web_surfaces: {plot_web_surfaces}
```
"""


def real_vocabulary() -> dict:
    """The world's own `site-vocabulary` block, as a dict."""
    return dict(kit_config.load(REAL_CONFIG).block("site_vocabulary") or {})


def _flow(values) -> str:
    return "[" + ", ".join(f'"{v}"' for v in values) + "]"


def write_config(root, *, published_tags=None, keystones=None, plot_web_surfaces=None) -> dict:
    """Write the config and the vocabulary note into a fixture vault. Returns the vocabulary.

    The config is the world's own, verbatim, so the fixture's section list and feature switches are
    the real ones. `game_ready_repo` is left alone: the tools that use it take a `--repo` flag.
    """
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    (root / "world.config.yaml").write_text(REAL_CONFIG.read_text(encoding="utf-8"),
                                            encoding="utf-8")
    vocab = real_vocabulary()
    if published_tags is not None:
        vocab["published_tags"] = list(published_tags)
    if keystones is not None:
        vocab["keystones"] = list(keystones)
    if plot_web_surfaces is not None:
        vocab["plot_web_surfaces"] = list(plot_web_surfaces)

    path = root / "meta" / "site-decisions.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(SITE_NOTE.format(
        published_tags=_flow(vocab["published_tags"]),
        keystones=_flow(vocab["keystones"]),
        plot_web_surfaces=_flow(vocab["plot_web_surfaces"]),
    ), encoding="utf-8")
    return vocab


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        got = write_config(tmp, published_tags=["choir", "leylines"])
        back = kit_config.load(Path(tmp) / "world.config.yaml")
        print(f"features  {sorted(back.features)}")
        print(f"sections  {[s.slug for s in back.site.sections]}")
        print(f"tags      {got['published_tags']}")
        print(f"read back {back.block('site_vocabulary')['published_tags']}")

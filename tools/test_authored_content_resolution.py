#!/usr/bin/env python3
"""Tests for where the engine's schemas come from: an installed package, or a checkout.

`tools/kit_config.mjs` is the only code that decides, and everything downstream depends on the answer:
the transformer and the validator are the engine's own code, and before this existed they could only
be reached through a checkout of the platform repository, which is why no world's CI could run its own
pipeline.

The four cases are the four states a consumer can be in. Each gets a stub `dist/index.js`, so the test
proves the *resolution* rather than the engine's behaviour — the real package's own suite does that.

    python3 tools/test_authored_content_resolution.py
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = "@curiouslittledroid/authored-content"


def make_package(root: Path, name: str) -> None:
    """A minimal stand-in for the published package: a manifest and one CJS entry."""
    pkg = root / "node_modules" / PKG if name == "installed" else root / "packages" / "authored-content"
    (pkg / "dist").mkdir(parents=True, exist_ok=True)
    (pkg / "package.json").write_text(json.dumps({
        "name": PKG,
        "version": "0.0.0-stub",
        "main": "dist/index.js",
        "exports": {".": {"require": "./dist/index.js", "import": "./dist/index.js"}},
    }) + "\n", encoding="utf-8")
    (pkg / "dist" / "index.js").write_text(
        'module.exports = { stub: "'
        + name
        + '", parseAuthoredEntity: () => ({ success: true }), parseWorldManifest: () => ({ success: true }) };\n',
        encoding="utf-8",
    )


def run(root: Path, *, mf_root: str | None) -> tuple[int, str]:
    """Ask `authoredContent()` what it loaded, in a child process with a controlled environment."""
    env = dict(os.environ)
    env.pop("MYTHICAL_FORGE_ROOT", None)
    if mf_root is not None:
        env["MYTHICAL_FORGE_ROOT"] = mf_root
    script = (
        f"import({json.dumps(str(root / 'tools' / 'kit_config.mjs'))})"
        ".then((m) => { console.log('STUB=' + m.authoredContent().stub); })"
        ".catch((e) => { console.error('MESSAGE=' + e.message); process.exit(3); })"
    )
    done = subprocess.run(["node", "--input-type=module", "-e", script],
                          capture_output=True, text=True, env=env, cwd=str(root))
    return done.returncode, done.stdout + done.stderr


class ResolutionCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="kit-ac-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        (self.tmp / "tools").mkdir()
        shutil.copy(HERE / "kit_config.mjs", self.tmp / "tools" / "kit_config.mjs")

    def test_the_installed_package_is_the_default(self):
        make_package(self.tmp, "installed")
        code, out = run(self.tmp, mf_root=None)
        self.assertEqual(code, 0, out)
        self.assertIn("STUB=installed", out)

    def test_a_checkout_wins_when_the_variable_is_set(self):
        # Both sources present on purpose: the point of the test is which one wins.
        make_package(self.tmp, "installed")
        make_package(self.tmp, "checkout")
        code, out = run(self.tmp, mf_root=str(self.tmp))
        self.assertEqual(code, 0, out)
        self.assertIn("STUB=checkout", out)

    def test_neither_source_names_the_install_an_author_can_do(self):
        """This message is read by a world's author, not by the kit's maintainer.

        It must be actionable — the registry, the token variable, the install command — and it must
        NOT offer a checkout of the private platform repository: an author who has the world and
        nothing else cannot follow that, and a message with a route they cannot take reads as "you
        are missing something you will never get". `verify-kit.sh` carries that route for the kit.
        """
        code, out = run(self.tmp, mf_root=None)
        self.assertNotEqual(code, 0)
        self.assertIn(f"{PKG} is not installed", out)
        self.assertIn("npm.pkg.github.com", out)
        self.assertIn("NODE_AUTH_TOKEN", out)
        self.assertIn("npm install", out)
        self.assertNotIn("MYTHICAL_FORGE_ROOT", out)
        # Nor a design-document number: `Design 23 §4.1` is how the kit's own documents cite the
        # schema, and an author holding a vault has no way to look it up.
        self.assertNotIn("Design 23", out)
        # ...and it must not be a stack trace. This is the assertion that keeps the guard in
        # verify-world.sh honest, because that is the code path a world hits first.
        self.assertNotIn("at ModuleJob", out)
        self.assertNotIn("node:internal", out)

    def test_a_wrong_checkout_names_the_missing_package(self):
        # Set to a directory that exists but holds no platform checkout: the classic mistyped path.
        code, out = run(self.tmp, mf_root=str(self.tmp))
        self.assertNotEqual(code, 0)
        self.assertIn("packages/authored-content/package.json", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)

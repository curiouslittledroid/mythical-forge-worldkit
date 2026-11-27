#!/usr/bin/env bash
# The kit's end-to-end proof. Copies the DEMO WORLD (this repository) into a throwaway directory and
# runs the whole pipeline on it: lint, transform, validate, thread-check, and the fixture's six
# scenarios. Nothing here is touched.
#
# The schemas the transformer and the validator check against are the engine's own (Design 23 §4.1).
# Two sources, and this script does not care which: the published `@curiouslittledroid/authored-content`,
# installed as an ordinary dependency (`npm install` in the kit's root), or a local checkout named by
# MYTHICAL_FORGE_ROOT — which wins when set. The installed package is what lets this script run in CI.
#
# Usage: ./verify-kit.sh [--keep]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
TMP="$(mktemp -d)"
trap '[ "${1:-}" = "--keep" ] || rm -rf "$TMP"' EXIT

# The documents first: they need no schemas, and a doc that teaches another world's ids is a defect
# in the machinery rather than in the pipeline. Cheap, so it runs before anything can be skipped.
echo "== docs"; python3 "$ROOT/tools/check_doc_examples.py" --all --verbose

# The schemas, from whichever source, probed once here: a missing install is one clear message naming
# both fixes rather than a stack trace out of the first tool that needs them.
if ! schemas_err="$(node --input-type=module -e "import('$ROOT/tools/kit_config.mjs').then((m) => { m.authoredContent(); }).catch((e) => { console.error(e.message); process.exit(1); })" 2>&1)"; then
  printf '%s\n' "$schemas_err" | sed 's/^/verify-kit: /' >&2
  exit 2
fi

echo "== version";  ROOT="$ROOT" python3 - <<'EOF'
import os, pathlib, subprocess
root = os.environ["ROOT"]

def git(*args):
    return subprocess.run(["git", "-C", root, *args], capture_output=True, text=True).stdout.strip()

# ONE question: is the marker BEHIND the newest tag? That was the bug it exists for -- the kit shipped
# v1.3.0 while this file said v1.2.3, and sync-tooling.sh reads the file to recognise a worldkit.
#
# Two earlier versions asked more and were wrong. Demanding equality fired while PREPARING a release
# (bump the file, commit, tag -- HEAD is still the old tag at the first step); asking equality only
# when HEAD is tagged fired at exactly that same moment, because "preparing" and "just tagged" are
# indistinguishable until the tag exists. False alarms are worse than no check: they teach the reader
# to ignore it. Being ahead is a version in flight and is never wrong.
v = pathlib.Path(root, "TOOLING_VERSION").read_text().strip()
newest = git("describe", "--tags", "--abbrev=0")
if not newest:
    print("no tags yet: nothing to compare the version to")
else:
    behind = subprocess.run(["sort", "-V", "-C"], input=f"{newest}\n{v}\n", text=True,
                            capture_output=True).returncode != 0
    if behind:
        raise SystemExit(f"FAIL: TOOLING_VERSION says {v} but the newest tag is {newest} -- it is stale (CONTRIBUTING.md, Release step 2)")
    print(f"TOOLING_VERSION ({v}) is not behind the newest tag ({newest})")
EOF

# Assemble the demo world the way a world holds it: the kit's example-world/, plus the vendored
# tools/ and the kit's world-facing documents at meta/conventions/. The proof then runs exactly as
# an author's tools/verify-world.sh would, against a copy of the fixture rather than the kit root
# (which is not a world).
rsync -a --exclude .git --exclude node_modules --exclude __pycache__ \
      "$ROOT/template/example-world/" "$TMP/world/"
rsync -a --exclude .git --exclude node_modules --exclude __pycache__ \
      "$ROOT/tools/" "$TMP/world/tools/"
mkdir -p "$TMP/world/meta/conventions"
rsync -a "$ROOT/template/meta/conventions/" "$TMP/world/meta/conventions/"
mkdir -p "$TMP/world/meta/templates"
rsync -a "$ROOT/template/meta/templates/" "$TMP/world/meta/templates/"
mkdir -p "$TMP/gameready"
# The copy excludes node_modules -- slow to copy, and not part of the vault -- so the real one is
# linked back in: the tools need the engine's schemas, and in an installed deployment those are this
# repository's own dependencies. Unset when the schemas come from a checkout instead (the guard above
# has already established that one source or the other is available).
[ -d "$ROOT/node_modules" ] && ln -s "$ROOT/node_modules" "$TMP/world/node_modules"

cd "$TMP/world"

echo "== suites";     for suite in tools/test_*.py; do printf '%s ' "$suite"; python3 "$suite" | tail -1; done
echo "== workflows";  python3 tools/check_workflows.py | tail -1
echo "== citations";  python3 tools/check_citations.py | tail -2
echo "== lint";       python3 tools/lint.py | tail -6
echo "== transform";  GAME_READY_REPO="$TMP/gameready" node tools/transform.mjs | grep -E "Wrote|thread ferry" || true
echo "== validate";   GAME_READY_REPO="$TMP/gameready" node tools/validate-world.mjs 2>&1 | grep -E "schema error|✗" || true
echo "== thread-check"; node tools/thread-check.mjs --repo "$TMP/gameready" | grep -E "OK|problem|Missing|never|Dangling|mismatch" || true
echo "== scenarios";  node tools/simulate-world.mjs --repo "$TMP/gameready" --quiet campaigns/ferryman-demo/scenarios/0*.yaml

[ "${1:-}" = "--keep" ] && echo "kept: $TMP" || true

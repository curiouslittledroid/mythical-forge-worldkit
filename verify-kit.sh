#!/usr/bin/env bash
# The kit's end-to-end proof. Copies the DEMO WORLD (this repository) into a throwaway directory and
# runs the whole pipeline on it: lint, transform, validate, thread-check, and the fixture's six
# scenarios. Nothing here is touched.
#
# Needs MYTHICAL_FORGE_ROOT, pointing at the platform repository (the directory holding
# packages/authored-content): the transformer and the validator are the engine's own code.
#
# Usage: ./verify-kit.sh [--keep]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
TMP="$(mktemp -d)"
trap '[ "${1:-}" = "--keep" ] || rm -rf "$TMP"' EXIT

if [ -z "${MYTHICAL_FORGE_ROOT:-}" ]; then
  echo "verify-kit: MYTHICAL_FORGE_ROOT is unset. It must point at the platform repository —" >&2
  echo "            the directory that holds packages/authored-content." >&2
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

rsync -a --exclude .git --exclude node_modules --exclude __pycache__ --exclude site/dist \
      "$ROOT/" "$TMP/world/"
mkdir -p "$TMP/gameready"
cd "$TMP/world"

echo "== suites";     for suite in tools/test_*.py; do printf '%s ' "$suite"; python3 "$suite" | tail -1; done
echo "== citations";  python3 tools/check_citations.py | tail -2
echo "== lint";       python3 tools/lint.py | tail -6
echo "== transform";  GAME_READY_REPO="$TMP/gameready" node tools/transform.mjs | grep -E "Wrote|thread ferry" || true
echo "== validate";   GAME_READY_REPO="$TMP/gameready" node tools/validate-world.mjs 2>&1 | grep -E "schema error|✗" || true
echo "== thread-check"; node tools/thread-check.mjs --repo "$TMP/gameready" | grep -E "OK|problem|Missing|never|Dangling|mismatch" || true
echo "== scenarios";  node tools/simulate-world.mjs --repo "$TMP/gameready" --quiet campaigns/ferryman-demo/scenarios/0*.yaml

[ "${1:-}" = "--keep" ] && echo "kept: $TMP" || true

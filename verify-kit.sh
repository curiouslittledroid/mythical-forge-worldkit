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

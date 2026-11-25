#!/usr/bin/env bash
# A WORLD's proof: build this world's vault into a throwaway Game Ready Repository and run the whole
# pipeline on the world's OWN content. Nothing here is touched.
#
# The division of labour:
#   ../verify-kit.sh (in the kit)   proves the TOOLCHAIN, against the kit's demo world
#   tools/verify-world.sh           proves THIS WORLD, against its own vault and its own scenarios
#
# A world overlays nothing. It used to overlay a copy of the kit's teaching example, which meant
# every world carried a duplicate of a fixture it did not own, and a failure could not be attributed:
# a broken toolchain and broken lore looked the same. Now the kit answers the first question and this
# answers the second, from the world's own content.
#
# Needs MYTHICAL_FORGE_ROOT - the platform repository, i.e. the directory holding
# packages/authored-content - because the transformer and the validator are the engine's own code.
#
# Usage: tools/verify-world.sh [--keep] [--scenario file.yaml ...]
#        with no scenario arguments, every scenario in `vault.scenarios` is run (`--coverage`).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
KEEP=""
SCENARIOS=()
for a in "$@"; do
  case "$a" in
    --keep) KEEP=1 ;;
    *) SCENARIOS+=("$a") ;;
  esac
done

if [ -z "${MYTHICAL_FORGE_ROOT:-}" ]; then
  echo "verify-world: MYTHICAL_FORGE_ROOT is unset. It must point at the platform repository —" >&2
  echo "              the directory that holds packages/authored-content. The transformer and the" >&2
  echo "              validator are the engine's own code." >&2
  exit 2
fi

TMP="$(mktemp -d)"
trap '[ -n "$KEEP" ] || rm -rf "$TMP"' EXIT
GR="$TMP/gameready"
mkdir -p "$GR"

# The transform writes codex-threads.yaml into the vault, so it runs on a copy: the world's own
# directory is never modified by a check.
rsync -a --exclude .git --exclude node_modules --exclude __pycache__ --exclude site/dist \
      "$ROOT/" "$TMP/world/"
cd "$TMP/world"

echo "== lint          (frontmatter, ids, dead links, undeclared flags)"
python3 tools/lint.py | tail -6
echo "== disclosure    (every lore section has a class; exits 1 if any is unreviewed)"
python3 tools/disclosure.py --check
echo "== transform"
GAME_READY_REPO="$GR" node tools/transform.mjs | grep -E "Wrote|thread " || true
echo "== validate      (the engine's own schema and reference checks)"
GAME_READY_REPO="$GR" node tools/validate-world.mjs --repo "$GR" 2>&1 | grep -E "schema error|✗" || true
echo "== thread-check  (flag registry, own-stage guards, references, thread interfaces)"
node tools/thread-check.mjs --repo "$GR" | grep -E "OK|problem|Missing|never|Dangling|mismatch" || true
echo "== voice"
python3 tools/voice_lint.py | tail -3 || true
python3 tools/voice_stale.py | tail -3 || true
if [ "${#SCENARIOS[@]}" -gt 0 ]; then
  echo "== scenarios     (${#SCENARIOS[@]} named)"
  node tools/simulate-world.mjs --repo "$GR" --quiet "${SCENARIOS[@]}"
else
  echo "== scenarios     (every scenario in vault.scenarios, with coverage)"
  node tools/simulate-world.mjs --repo "$GR" --coverage --quiet
fi

[ -n "$KEEP" ] && echo "kept: $TMP" || true

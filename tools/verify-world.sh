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
# The schemas the transformer and the validator check against are the engine's own.
# Two sources, and this script does not care which: the published `@curiouslittledroid/authored-content`,
# installed as an ordinary dependency (`npm install` in this repository's root), or a local checkout
# named by MYTHICAL_FORGE_ROOT — which wins when set, so an unreleased schema change is developed
# against it. The installed package is what lets this script run in CI, with no checkout of anything
# but the world itself.
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

# The schemas, from whichever source. Probed once here, so a missing install is one clear message
# naming both fixes rather than a stack trace out of the first tool that needs them.
if ! schemas_err="$(node --input-type=module -e "import('$ROOT/tools/kit_config.mjs').then((m) => { m.authoredContent(); }).catch((e) => { console.error(e.message); process.exit(1); })" 2>&1)"; then
  printf '%s\n' "$schemas_err" | sed 's/^/verify-world: /' >&2
  exit 2
fi

TMP="$(mktemp -d)"
trap '[ -n "$KEEP" ] || rm -rf "$TMP"' EXIT
GR="$TMP/gameready"
mkdir -p "$GR"

# The voice checks run against the world ITSELF, before the copy: `voice_stale.py` reads git history,
# and a copy without .git cannot tell it anything (it says so, which is honest but useless). Both are
# read-only.
echo "== voice         (each account against its teller's sheet; then canon that moved after it)"
python3 "$ROOT/tools/voice_lint.py" | tail -3 || true
python3 "$ROOT/tools/voice_stale.py" | tail -5 || true

# Every check runs on a COPY of the world, so the world's own directory is never modified by a
# check -- even if a tool misbehaves. (The transform writes into the Game Ready Repository, not the
# vault; the first version of this comment said otherwise, which is the kind of small lie a
# maintainer eventually trusts.)
rsync -a --exclude .git --exclude node_modules --exclude __pycache__ --exclude site/dist \
      "$ROOT/" "$TMP/world/"
# The copy excludes node_modules -- slow to copy, and not part of the vault -- so the real one is
# linked back in: the tools need the engine's schemas, and in an installed deployment those are this
# repository's own dependencies. Unset when the schemas come from a checkout instead (the guard above
# has already established that one source or the other is available).
[ -d "$ROOT/node_modules" ] && ln -s "$ROOT/node_modules" "$TMP/world/node_modules"

cd "$TMP/world"

echo "== citations     (every section citation names a section the document has)"
python3 tools/check_citations.py
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
# A world that has not written a scenario yet is not a broken world: it is a world at Step 0b. Say
# so and pass -- but only when there is genuinely nothing to run. If scenario files exist and the
# config does not name them, the simulator's own error is the honest answer, and it still fires.
SCENARIO_FILES="$(find campaigns -path '*/scenarios/*.yaml' 2>/dev/null | head -1 || true)"
if [ "${#SCENARIOS[@]}" -gt 0 ]; then
  echo "== scenarios     (${#SCENARIOS[@]} named)"
  node tools/simulate-world.mjs --repo "$GR" --quiet "${SCENARIOS[@]}"
elif [ -z "$SCENARIO_FILES" ]; then
  echo "== scenarios     (none yet: no campaign has a scenario file)"
  echo "                  Expected while a world is still writing lore. Step 12a writes the first,"
  echo "                  and this step starts proving behaviour from then on."
else
  echo "== scenarios     (every scenario in vault.scenarios, with coverage)"
  node tools/simulate-world.mjs --repo "$GR" --coverage --quiet
fi

[ -n "$KEEP" ] && echo "kept: $TMP" || true

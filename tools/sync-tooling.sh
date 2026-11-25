#!/usr/bin/env bash
# Update this world's copy of the worldkit to a release tag.
#
# A world does not depend on the kit at run time: it holds a copy of `tools/` and pins it in
# `TOOLING_VERSION`. This is the one command that moves that pin, and the diff it prints is the
# whole review surface.
#
# Usage:
#   tools/sync-tooling.sh              # the latest tag
#   tools/sync-tooling.sh v1.2.0       # a named tag
#   WORLDKIT_REPO=/path/to/checkout tools/sync-tooling.sh v1.2.0   # a local checkout, for testing
#
# What it replaces (all of it the kit's):
#   tools/            except tools/local/ — world-owned; the kit never writes it
#   docs/ of the kit  into tools/docs/ — the RULES ARE PART OF THE TOOLING: a tool enforces a rule
#                     the world's agent must be able to read. A pointer in prose therefore names the
#                     kit document AND its vendored path ("the kit's conventions.md §7, vendored at
#                     tools/docs/conventions.md"), so the rule is always one file away.
#   meta/templates/   the canonical note templates
#   site/             the Astro theme (when the kit ships one and the world uses it)
#
# It never touches: tools/local/, the world's lore, its world.config.yaml, its meta/ notes, its
# AGENTS.md brief (only the marked protocol region is re-synced, by tools/sync-agent-protocol.py).
set -euo pipefail

WORLD_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
KIT_REPO="${WORLDKIT_REPO:-https://github.com/curiouslittledroid/mythical-forge-worldkit}"
TAG="${1:-}"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "sync-tooling: fetching ${TAG:-the latest tag} from $KIT_REPO"
if [ -d "$KIT_REPO/.git" ]; then
  git clone --quiet "$KIT_REPO" "$TMP/kit"                 # a local checkout: for testing the script
  [ -n "$TAG" ] && git -C "$TMP/kit" checkout --quiet "$TAG"
else
  git clone --quiet ${TAG:+--branch "$TAG"} --depth 1 "$KIT_REPO" "$TMP/kit"
fi
if [ -z "$TAG" ]; then
  TAG="$(git -C "$TMP/kit" describe --tags --abbrev=0 2>/dev/null || echo unreleased)"
fi
if [ ! -f "$TMP/kit/TOOLING_VERSION" ]; then
  echo "sync-tooling: $KIT_REPO is not a worldkit (no TOOLING_VERSION)" >&2; exit 2
fi

OLD="$(cat "$WORLD_ROOT/TOOLING_VERSION" 2>/dev/null || echo none)"

# --exclude local/ is what makes D16 true: a world's own scripts survive every sync.
rsync -a --delete --exclude 'local/' --exclude '__pycache__' "$TMP/kit/tools/" "$WORLD_ROOT/tools/"
mkdir -p "$WORLD_ROOT/tools/docs"
rsync -a --delete "$TMP/kit/docs/" "$WORLD_ROOT/tools/docs/"
[ -d "$TMP/kit/meta/templates" ] && rsync -a "$TMP/kit/meta/templates/" "$WORLD_ROOT/meta/templates/"
[ -d "$TMP/kit/site/src" ] && rsync -a --delete "$TMP/kit/site/src/" "$WORLD_ROOT/site/src/"

printf '%s\n' "$TAG" > "$WORLD_ROOT/TOOLING_VERSION"

echo "sync-tooling: $OLD -> $TAG"
echo "sync-tooling: the protocol region, if it changed:"
python3 "$WORLD_ROOT/tools/sync-agent-protocol.py" || true

echo
echo "Review the diff, then run the proof:"
if [ -d "$WORLD_ROOT/.git" ]; then git -C "$WORLD_ROOT" diff --stat; else echo "  (not a git repository: review and commit by hand)"; fi
echo "  cd $WORLD_ROOT && python3 tools/lint.py && tools/verify-world.sh"
echo "Read CHANGELOG.md in the kit for anything a world must do by hand."

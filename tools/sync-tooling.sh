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
#   meta/templates/   the canonical note templates (mirrored: this directory is wholly the kit's,
#                     so a template deleted upstream goes away. A world's own examples live in its
#                     own folder, never here.)
#   site/             the theme: src/ (minus the generated pages and the world's own copy pages),
#                     the Astro config, package.json,
#                     deploy.sh, the infra process, the image-prompt process, the workflow. A
#                     world's own art, prompt notes, audit, deploy state and hero stay.
#   .pi/prompts/      the agent prompts (atlas-refresh, new-creature, the image pipeline)
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

# The copy of THIS script has just been replaced, and bash is still reading the old text: a step
# added in the new version would silently not run (which is exactly what happened the first time a
# world took this release - the theme synced but the theme's README did not). Re-exec once, with the
# new script, and only then continue.
if [ -z "${SYNC_REEXEC:-}" ] && ! cmp -s "$TMP/kit/tools/sync-tooling.sh" "$WORLD_ROOT/tools/sync-tooling.sh" >/dev/null 2>&1; then
  echo "sync-tooling: this script itself changed; re-running with the new version"
  SYNC_REEXEC=1 exec "$WORLD_ROOT/tools/sync-tooling.sh" ${TAG:+"$TAG"}
fi
mkdir -p "$WORLD_ROOT/tools/docs"
rsync -a --delete "$TMP/kit/docs/" "$WORLD_ROOT/tools/docs/"
[ -d "$TMP/kit/meta/templates" ] && rsync -a --delete "$TMP/kit/meta/templates/" "$WORLD_ROOT/meta/templates/"

# The theme. `--delete` everywhere the kit owns the file; the exclusions are what a world keeps:
# the generated pages, its art, its own prompt notes, and its deploy state.
if [ -d "$TMP/kit/site" ] && [ -d "$WORLD_ROOT/site" ]; then
  # Three pages are the WORLD'S copy, not theme chrome: the landing page, About and Follow. The kit
  # ships a neutral version of each so a new world has a working site, and then leaves them alone -
  # a world's About page is its own prose, and a sync that rewrote it would be destroying content.
  rsync -a --delete \
        --exclude 'content/generated' --exclude 'data/generated' \
        --exclude 'pages/index.astro' --exclude 'pages/about.astro' --exclude 'pages/follow.astro' \
        "$TMP/kit/site/src/" "$WORLD_ROOT/site/src/"
  for f in astro.config.mjs package.json package-lock.json deploy.sh README.md; do
    [ -f "$TMP/kit/site/$f" ] && cp "$TMP/kit/site/$f" "$WORLD_ROOT/site/$f"
  done
  [ -d "$TMP/kit/site/infra" ] && rsync -a --exclude 'state.json' \
        "$TMP/kit/site/infra/" "$WORLD_ROOT/site/infra/"
  [ -f "$TMP/kit/site/image-prompts/README.md" ] && \
    cp "$TMP/kit/site/image-prompts/README.md" "$WORLD_ROOT/site/image-prompts/README.md"
fi
[ -d "$TMP/kit/.pi/prompts" ] && rsync -a --delete "$TMP/kit/.pi/prompts/" "$WORLD_ROOT/.pi/prompts/"
[ -f "$TMP/kit/.github/workflows/site.yml" ] && \
  cp "$TMP/kit/.github/workflows/site.yml" "$WORLD_ROOT/.github/workflows/site.yml"

printf '%s\n' "$TAG" > "$WORLD_ROOT/TOOLING_VERSION"

echo "sync-tooling: $OLD -> $TAG"
echo "sync-tooling: the protocol region, if it changed:"
python3 "$WORLD_ROOT/tools/sync-agent-protocol.py" || true

echo
echo "Review the diff, then run the proof:"
if [ -d "$WORLD_ROOT/.git" ]; then git -C "$WORLD_ROOT" diff --stat; else echo "  (not a git repository: review and commit by hand)"; fi
echo "  cd $WORLD_ROOT && python3 tools/lint.py && tools/verify-world.sh"
echo "Read CHANGELOG.md in the kit for anything a world must do by hand."

#!/usr/bin/env bash
# Assemble the complete mythical-forge-world-template repository from this kit.
#
# The template repo is GENERATED: it is never edited by hand. This script builds it from
#   - template/          the skeleton a new author forks (world.config.yaml, init-world.sh,
#                        the brief, the roadmap, principles/, the empty vault, the note
#                        templates, and the embedded example-world/ demo);
#   - tools/, site-theme/, .github/workflows/  vendored into the template exactly as
#                        sync-tooling.sh vendors them into a world;
#   - TOOLING_VERSION    the pin.
#
# Usage:
#   ./export-template.sh                     # the latest tag, into /tmp/template-export
#   ./export-template.sh out/                # the latest tag, into out/
#   ./export-template.sh v1.2.0 out/         # a named tag, into out/
#   ./export-template.sh --worktree out/     # THIS working tree, unpinned (what CI proves)
#   WORLDKIT_REPO=/path/to/checkout ./export-template.sh out/
#
# `--worktree` skips the clone and exports the checkout this script sits in, so an uncommitted
# change can be exported and CI can prove the commit it actually ran on rather than a branch tip.
# The pin then names the newest tag, or `unreleased` when the commit is past it.
#
# This only WRITES the destination directory. Committing, pushing and opening a PR into
# mythical-forge-world-template is a separate, deliberate step (see the release steps in
# CONTRIBUTING.md): the export runs at milestones, not on every commit.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
KIT_REPO="${WORLDKIT_REPO:-https://github.com/curiouslittledroid/mythical-forge-worldkit}"
TAG=""
DEST=""
FORCE=0
WORKTREE=0
POS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --force|-f) FORCE=1; shift ;;
    --worktree|-w) WORKTREE=1; shift ;;
    -h|--help) sed -n '2,20p' "$0" | sed 's/^# \?//'; exit 0 ;;
    -*) echo "export-template: unknown option: $1" >&2; exit 2 ;;
    *) POS+=("$1"); shift ;;
  esac
done
case "${#POS[@]}" in
  0) ;;
  1) DEST="${POS[0]}" ;;
  2) TAG="${POS[0]}"; DEST="${POS[1]}" ;;
  *) echo "export-template: at most two arguments (a tag, then a destination)" >&2; exit 2 ;;
esac
DEST="${DEST:-/tmp/template-export}"

if [ -e "$DEST" ] && [ -n "$(ls -A "$DEST" 2>/dev/null)" ] && [ "$FORCE" != 1 ]; then
  echo "export-template: $DEST is not empty (pass --force to overwrite, or name another directory)" >&2
  exit 2
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

if [ "$WORKTREE" = 1 ]; then
  [ -z "$TAG" ] || { echo "export-template: --worktree exports the working tree; it cannot also take the tag '$TAG'" >&2; exit 2; }
  echo "export-template: exporting the working tree at $ROOT"
  mkdir -p "$TMP/kit"
  rsync -a --exclude .git --exclude node_modules --exclude __pycache__ \
        --exclude 'site-theme/dist' --exclude 'site-theme/.astro' \
        "$ROOT/" "$TMP/kit/"
elif [ -d "$KIT_REPO/.git" ]; then
  echo "export-template: fetching ${TAG:-the latest tag} from $KIT_REPO"
  git clone --quiet "$KIT_REPO" "$TMP/kit"
  [ -n "$TAG" ] && git -C "$TMP/kit" checkout --quiet "$TAG"
else
  echo "export-template: fetching ${TAG:-the latest tag} from $KIT_REPO"
  git clone --quiet ${TAG:+--branch "$TAG"} --depth 1 "$KIT_REPO" "$TMP/kit"
fi
if [ -z "$TAG" ]; then
  # In worktree mode the copy under $TMP has no history; the pin comes from the real checkout.
  src="$TMP/kit"
  [ "$WORKTREE" = 1 ] && src="$ROOT"
  TAG="$(git -C "$src" describe --tags --abbrev=0 2>/dev/null || echo unreleased)"
fi
if [ ! -f "$TMP/kit/TOOLING_VERSION" ]; then
  echo "export-template: $KIT_REPO is not a worldkit (no TOOLING_VERSION)" >&2; exit 2
fi
if [ ! -d "$TMP/kit/template" ]; then
  echo "export-template: $KIT_REPO has no template/ (it predates the generated template)" >&2; exit 2
fi

mkdir -p "$DEST"

# --- 1. The template skeleton, verbatim (it already contains example-world/). -------------------
rsync -a --delete "$TMP/kit/template/" "$DEST/"

# --- 2. The vendored machinery, exactly as a world holds it. -------------------------------------
# tools/, except the things the kit keeps elsewhere and a world keeps beside/inside tools/.
rsync -a --exclude 'local/' --exclude 'docs/' \
      --exclude 'LICENSE' --exclude 'LICENSE-CONTENT' \
      --exclude '__pycache__' "$TMP/kit/tools/" "$DEST/tools/"
for licence in LICENSE LICENSE-CONTENT; do
  cp "$TMP/kit/$licence" "$DEST/tools/$licence"
done
chmod +x "$DEST/tools/"*.sh 2>/dev/null || true

# The world-facing documents (meta/conventions/) and the note templates (meta/templates/) arrive
# with template/ above, so nothing to do here.


# The theme. The kit keeps it at site-theme/; a world holds it at site/.
#
# NOT the sync's exclusions. A sync must leave the three world-owned pages alone (the landing page,
# About and Follow are a world's own prose, and the kit ships a neutral copy only so a NEW world has
# a working site). An export is building that new world, so it needs the neutral copies: excluding
# them here produced a template with no landing page, and therefore a site that cannot build.
# Only the exporter's generated directories are excluded -- they do not exist in a fresh fork.
mkdir -p "$DEST/site/src" "$DEST/site/infra" "$DEST/site/image-prompts"
rsync -a --exclude 'content' --exclude 'data' \
      "$TMP/kit/site-theme/src/" "$DEST/site/src/"
for page in index about follow; do
  [ -f "$DEST/site/src/pages/$page.astro" ] || {
    echo "export-template: the theme has no neutral pages/$page.astro; a fork would have no $page page" >&2
    exit 1
  }
done
for f in astro.config.mjs package.json package-lock.json deploy.sh README.md LICENSES.md; do
  [ -f "$TMP/kit/site-theme/$f" ] && cp "$TMP/kit/site-theme/$f" "$DEST/site/$f"
done
rsync -a --exclude 'state.json' "$TMP/kit/site-theme/infra/" "$DEST/site/infra/"
# The kit's two image-prompt files: the process (README.md) and the house style (_style.md). The
# process calls _style.md the authority on the look, so an export without it ships half the pipeline.
for f in README.md _style.md; do
  [ -f "$TMP/kit/site-theme/image-prompts/$f" ] || {
    echo "export-template: the theme has no image-prompts/$f" >&2; exit 1; }
  cp "$TMP/kit/site-theme/image-prompts/$f" "$DEST/site/image-prompts/$f"
done

# The workflows a world runs. (The agent prompts arrive with template/ above.)
mkdir -p "$DEST/.github/workflows"
for wf in site.yml checks.yml tooling-drift.yml; do
  cp "$TMP/kit/.github/workflows/$wf" "$DEST/.github/workflows/$wf"
done

# The pin.
printf '%s\n' "$TAG" > "$DEST/TOOLING_VERSION"

# The protocol region of the template's AGENTS.md, synced from the kit's source.
python3 "$DEST/tools/sync-agent-protocol.py" || true

echo "export-template: wrote $DEST (template at $TAG)"
echo "Next, by hand:"
echo "  cd $DEST && git init -b main && git add -A && git commit   # or into the real template repo"
echo "  cd $DEST && python3 tools/lint.py && tools/verify-world.sh # a fresh fork still works"

#!/usr/bin/env bash
# Assemble the complete mythical-forge-world-template repository from this kit.
#
# The template repo is GENERATED: it is never edited by hand. This script builds it from
#   - template/          the skeleton a new author forks (world.config.yaml, init-world.sh,
#                        the brief, the roadmap, principles/, the empty vault, the note
#                        templates, and the embedded example-world/ demo);
#   - tools/, site-theme/, .github/workflows/  vendored into the template exactly as
#                        sync-tooling.sh vendors them into a world (site-theme/public/
#                        included: the neutral favicon a fork starts from);
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
# The destination is REPLACED, not merged into: anything there that this export does not produce is
# removed, so a path the kit retires cannot linger in a published template. The one exception is the
# destination's own `.git`, which is kept -- exporting over a checkout of mythical-forge-world-template
# on a branch is the normal case, and the tree is committed from there.
#
# This only WRITES the destination directory. Committing, pushing and opening a PR into
# mythical-forge-world-template is a separate, deliberate step (see "Publish the template" in
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
    # The header, up to the line that starts the script, so the help cannot be truncated by an edit
    # above it -- it was `sed -n '2,20p'` once, and outgrew the range the first time it was extended.
    -h|--help) awk 'NR > 1 { if ($0 == "set -euo pipefail") exit; print }' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
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
  echo "export-template: $DEST is not empty (pass --force to replace its contents; a .git in it is kept)" >&2
  exit 2
fi

# Refuse a destination that HOLDS a repository rather than being one. The export deletes every path
# it does not produce, so a container directory -- `<project>/{bare.git,main}`, the layout these
# projects use -- would lose both the mirror and the worktree, and the finished export would look
# perfect. That is not hypothetical: it destroyed a template clone once, which is why this exists.
if repos="$(find "$DEST" -maxdepth 2 -name '*.git' ! -path "$DEST/.git" -print 2>/dev/null)" && [ -n "$repos" ]; then
  echo "export-template: $DEST contains a git repository this export would delete:" >&2
  printf '%s\n' "$repos" | sed 's/^/  /' >&2
  echo "export-template: name the checkout itself (the directory with the .git), not the one holding it" >&2
  exit 2
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
OUT="$TMP/out"

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
  # The pin is the exported tree's OWN `TOOLING_VERSION`, not `git describe`. They are the same
  # string on a tagged checkout -- and they differ in the one case that matters: the pin is bumped
  # before the commit and the tag, so a `--worktree` export made from a release in flight described
  # itself as the PREVIOUS tag while carrying the new content. A fork of that template is then told
  # by `tooling-drift.yml` that it has hand-edited every file the release touched.
  TAG="$(tr -d '[:space:]' < "$TMP/kit/TOOLING_VERSION" 2>/dev/null || true)"
  [ -n "$TAG" ] || TAG=unreleased
fi
if [ ! -f "$TMP/kit/TOOLING_VERSION" ]; then
  echo "export-template: $KIT_REPO is not a worldkit (no TOOLING_VERSION)" >&2; exit 2
fi
if [ ! -d "$TMP/kit/template" ]; then
  echo "export-template: $KIT_REPO has no template/ (it predates the generated template)" >&2; exit 2
fi

mkdir -p "$OUT"

# --- 1. The template skeleton, verbatim (it already contains example-world/). -------------------
rsync -a "$TMP/kit/template/" "$OUT/"

# --- 2. The vendored machinery, exactly as a world holds it. -------------------------------------
# tools/, except the things the kit keeps elsewhere and a world keeps beside/inside tools/.
rsync -a --exclude 'local/' --exclude 'docs/' \
      --exclude 'LICENSE' --exclude 'LICENSE-CONTENT' \
      --exclude '__pycache__' "$TMP/kit/tools/" "$OUT/tools/"
for licence in LICENSE LICENSE-CONTENT; do
  cp "$TMP/kit/$licence" "$OUT/tools/$licence"
done
chmod +x "$OUT/tools/"*.sh 2>/dev/null || true

# The world-facing documents (meta/conventions/) and the note templates (meta/templates/) arrive
# with template/ above, so nothing to do here.


# The theme. The kit keeps it at site-theme/; a world holds it at site/.
#
# NOT the sync's exclusions. A sync must leave the three world-owned pages alone (the landing page,
# About and Follow are a world's own prose, and the kit ships a neutral copy only so a NEW world has
# a working site). An export is building that new world, so it needs the neutral copies: excluding
# them here produced a template with no landing page, and therefore a site that cannot build.
# Only the exporter's generated directories are excluded -- they do not exist in a fresh fork.
mkdir -p "$OUT/site/src" "$OUT/site/infra" "$OUT/site/image-prompts"
rsync -a --exclude 'content' --exclude 'data' \
      "$TMP/kit/site-theme/src/" "$OUT/site/src/"
for page in index about follow; do
  [ -f "$OUT/site/src/pages/$page.astro" ] || {
    echo "export-template: the theme has no neutral pages/$page.astro; a fork would have no $page page" >&2
    exit 1
  }
done
for f in astro.config.mjs package.json package-lock.json deploy.sh README.md LICENSES.md; do
  [ -f "$TMP/kit/site-theme/$f" ] && cp "$TMP/kit/site-theme/$f" "$OUT/site/$f"
done
rsync -a --exclude 'state.json' "$TMP/kit/site-theme/infra/" "$OUT/site/infra/"
# The kit's two image-prompt files: the process (README.md) and the house style (_style.md). The
# process calls _style.md the authority on the look, so an export without it ships half the pipeline.
for f in README.md _style.md; do
  [ -f "$TMP/kit/site-theme/image-prompts/$f" ] || {
    echo "export-template: the theme has no image-prompts/$f" >&2; exit 1; }
  cp "$TMP/kit/site-theme/image-prompts/$f" "$OUT/site/image-prompts/$f"
done

# The site's own static files: today the neutral favicon, later art. `BaseLayout.astro` links
# `/favicon.svg`, so an export without it ships a fork whose every page 404s its icon -- which is
# what happened while the file lived only in the old hand-made template and the first export
# "correctly" deleted it. `site/public/` is the WORLD's from here on: the sync never writes it, so a
# world's own favicon and its `img/` hero survive every release.
mkdir -p "$OUT/site/public"
rsync -a "$TMP/kit/site-theme/public/" "$OUT/site/public/"
[ -f "$OUT/site/public/favicon.svg" ] || {
  echo "export-template: the theme has no public/favicon.svg; a fork's site would 404 its icon" >&2
  exit 1
}

# The workflows a world runs. (The agent prompts arrive with template/ above.)
mkdir -p "$OUT/.github/workflows"
for wf in site.yml checks.yml tooling-drift.yml; do
  cp "$TMP/kit/.github/workflows/$wf" "$OUT/.github/workflows/$wf"
done

# The pin.
printf '%s\n' "$TAG" > "$OUT/TOOLING_VERSION"

# The protocol region of the template's AGENTS.md, synced from the kit's source.
python3 "$OUT/tools/sync-agent-protocol.py" || true

# --- 4. Publish: the destination becomes exactly this export, minus its own .git. ----------------
# The destination is normally a checkout of mythical-forge-world-template on a branch, so the export
# replaces the tree: a path the kit has retired has to disappear, or the template keeps a stale copy
# of something that was renamed. `.git` is excluded -- and only at the root, so a nested repository
# is still the export's to overwrite -- because the commit happens from this tree: deleting it leaves
# a working directory with no repository. An earlier version did exactly that to a destination that
# was a clone, and a *finished* export looked perfect.
mkdir -p "$DEST"
gone="$(rsync -a --delete --exclude=/.git --dry-run --itemize-changes "$OUT/" "$DEST/" \
        | sed -n 's/^\*deleting *//p')"
if [ -n "$gone" ]; then
  count="$(printf '%s\n' "$gone" | wc -l | tr -d ' ')"
  echo "export-template: removing $count path(s) the export does not produce:"
  # `sed -n '1,20s/^/  /p'`, NOT `| head -20`. `head` exits after its twentieth line, `printf` takes
  # SIGPIPE writing the rest, and `set -o pipefail` turns that into THIS SCRIPT DYING inside its own
  # progress report: exit 1, no message that names the cause, and the destination left as it was --
  # because the rsync below never runs. It needs a destination big enough to fill a pipe (64K of
  # paths) before it fires, so it stayed hidden until a template checkout that had been BUILT was
  # exported over: `site/node_modules` and the exporter's generated directories alone are thousands
  # of paths the export does not produce.
  printf '%s\n' "$gone" | sed -n '1,20s/^/  /p'
  if [ "$count" -gt 20 ]; then echo "  ... and $((count - 20)) more"; fi
fi
rsync -a --delete --exclude=/.git "$OUT/" "$DEST/"

echo "export-template: wrote $DEST (template at $TAG)"
# `-e`, not `-d`: in a `bare.git` + worktree layout, which is how these projects are kept, `.git` is
# a FILE pointing at the mirror. Testing for a directory said "no repository here" about a checkout.
if [ -e "$DEST/.git" ]; then
  echo "export-template: kept $DEST/.git, on branch '$(git -C "$DEST" branch --show-current 2>/dev/null || echo detached)' -- review and commit:"
  echo "  git -C $DEST status && git -C $DEST add -A && git -C $DEST commit -m 'Worldkit $TAG'"
else
  echo "Next, by hand:"
  echo "  cd $DEST && git init -b main && git add -A && git commit"
fi
echo "  cd $DEST && python3 tools/lint.py && tools/verify-world.sh # a fresh fork still works"

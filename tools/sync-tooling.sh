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
#   tools/sync-tooling.sh --dry-run    # print every change, write nothing
#   tools/sync-tooling.sh --force v1.2.0   # proceed despite a dirty tree or a deletion
#   WORLDKIT_REPO=/path/to/checkout tools/sync-tooling.sh v1.2.0   # a local checkout, for testing
#
# It refuses to run when the world has uncommitted changes in files this sync is about to replace,
# or when it would DELETE a file that lives in a directory the kit owns: the point of vendoring is
# that the diff is reviewable, and a diff nobody can attribute is the failure mode.

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
TAG=""
DRY=0
FORCE=0
for arg in "$@"; do
  case "$arg" in
    --dry-run|-n) DRY=1 ;;
    --force|-f)   FORCE=1 ;;
    -h|--help)    sed -n '2,26p' "$0" | sed 's/^# \?//'; exit 0 ;;
    -*)           echo "sync-tooling: unknown option: $arg" >&2; exit 2 ;;
    *)            TAG="$arg" ;;
  esac
done
# A dry run itemises, so a deletion is visible as `*deleting `; a real run stays quiet.
RS="rsync -a --delete"
[ "$DRY" = 1 ] && RS="rsync -a --delete -i -n"
# A copy that would not happen: same shape as cp, so the call sites read the same either way.
cpfile() {
  if [ "$DRY" = 1 ]; then echo "would copy $1 -> $2"; else cp "$1" "$2"; fi
}

# --- the rails, before anything is fetched or written -----------------------------------------
# Only the paths this sync actually replaces. `tools/local/`, the world's three site pages and its
# own art are the world's, so a world is expected to have them dirty.
if [ "$DRY" = 0 ] && [ "$FORCE" = 0 ] && [ -z "${SYNC_REEXEC:-}" ] && [ -d "$WORLD_ROOT/.git" ]; then
  dirty="$(git -C "$WORLD_ROOT" status --porcelain -- \
             tools meta/templates site/src site/image-prompts/README.md .pi/prompts .github/workflows 2>/dev/null \
           | grep -vE ' tools/local/| site/src/pages/(index|about|follow)\.astro$' || true)"
  if [ -n "$dirty" ]; then
    echo "sync-tooling: refusing to run: uncommitted changes in files this sync would replace." >&2
    printf '%s\n' "$dirty" | sed 's/^/  /' >&2
    echo >&2
    echo "  Commit or stash them, or run again with --force. A sync onto a dirty tree produces a" >&2
    echo "  diff nobody can attribute, which is the whole review surface of vendoring." >&2
    exit 2
  fi
fi

# Deletions can only be seen by asking rsync, so ask it: this reruns the whole sync in dry-run mode,
# reads what it would remove, and throws that away. It costs a second fetch and buys the review.
if [ "$DRY" = 0 ] && [ "$FORCE" = 0 ] && [ -z "${SYNC_REEXEC:-}" ]; then
  plan="$(SYNC_REEXEC=1 bash "$0" --dry-run "$TAG" 2>&1 || true)"
  dels="$(printf '%s\n' "$plan" | grep -E '^\*deleting ' || true)"
  if [ -n "$dels" ]; then
    echo "sync-tooling: refusing to run: this sync would DELETE files." >&2
    printf '%s\n' "$dels" | sed 's/^\*deleting */  /' >&2
    echo >&2
    echo "  They are inside a directory the kit owns and are not in the kit at ${TAG:-the latest tag}," >&2
    echo "  so a world's file has ended up where only the kit's belong. Move it to tools/local/ (if it" >&2
    echo "  is a script), to the world's own folder (if it is a template's example), or run again with" >&2
    echo "  --force to let the sync remove it." >&2
    exit 2
  fi
fi

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

# What THIS run is executing, saved before the copy below replaces the file on disk. Bash is still
# reading the old text, so a step added upstream would silently not run. The comparison has to be
# against this saved copy: comparing the new file with the WORLD's copy cannot notice anything,
# because the rsync has just made them identical -- which is why the first version of this guard
# never fired.
cp "$0" "$TMP/running.sh"

# --exclude local/ is what makes D16 true: a world's own scripts survive every sync.
# --exclude docs is not cosmetic. The kit keeps `docs/` as a SIBLING of `tools/`; a world keeps it at
# `tools/docs/`. Without this exclusion the rsync finds `docs/` in the world and not in the kit, and
# DELETES it -- on every run -- and the next line recreates it from the kit's `docs/`. The end state
# was always right, so nobody noticed; but a run that stopped in between left a world with no rules
# at all, and a refusal is a stop. (The same asymmetry cost 1.0.11 a release in the drift check.)
$RS --exclude 'local/' --exclude 'docs/' --exclude '__pycache__' "$TMP/kit/tools/" "$WORLD_ROOT/tools/"
# A shell tool that arrives without its execute bit is unusable, and the failure is confusing
# ("Permission denied" on a command the docs tell you to run). Cheap insurance.
[ "$DRY" = 0 ] && chmod +x "$WORLD_ROOT/tools/"*.sh 2>/dev/null || true

# The copy of THIS script has just been replaced, and bash is still reading the old text: a step
# added in the new version would silently not run (which is exactly what happened the first time a
# world took this release - the theme synced but the theme's README did not). Re-exec once, with the
# new script, and only then continue.
if [ "$DRY" = 0 ] && [ -z "${SYNC_REEXEC:-}" ] && ! cmp -s "$TMP/running.sh" "$WORLD_ROOT/tools/sync-tooling.sh" >/dev/null 2>&1; then
  echo "sync-tooling: this script itself changed; re-running with the new version"
  # Through `bash`, not directly: the copy that just arrived may not be executable (a release that
  # lost the bit is the first defect this script ever had), and a re-exec that fails on permissions
  # would be worse than no re-exec at all.
  SYNC_REEXEC=1 exec bash "$WORLD_ROOT/tools/sync-tooling.sh" ${TAG:+"$TAG"}
fi
mkdir -p "$WORLD_ROOT/tools/docs"
[ -d "$TMP/kit/docs" ] && $RS --delete "$TMP/kit/docs/" "$WORLD_ROOT/tools/docs/"
mkdir -p "$WORLD_ROOT/meta/templates"
[ -d "$TMP/kit/meta/templates" ] && $RS --delete "$TMP/kit/meta/templates/" "$WORLD_ROOT/meta/templates/"

# The theme. `--delete` everywhere the kit owns the file; the exclusions are what a world keeps:
# the generated pages, its art, its own prompt notes, and its deploy state.
if [ -d "$TMP/kit/site" ] && [ -d "$WORLD_ROOT/site" ]; then
  # Three pages are the WORLD'S copy, not theme chrome: the landing page, About and Follow. The kit
  # ships a neutral version of each so a new world has a working site, and then leaves them alone -
  # a world's About page is its own prose, and a sync that rewrote it would be destroying content.
  mkdir -p "$WORLD_ROOT/site/src" "$WORLD_ROOT/site/infra" "$WORLD_ROOT/site/image-prompts"
  # The generated directories are the exporter's, not the theme's: a world that has built its site
  # has them and the kit never does. Excluding only `data/generated` is not enough -- rsync still
  # finds `data/` and `content/` in the world and not in the kit, deletes them, and (once the rails
  # existed) refuses every published world. A false alarm is worse than no rail: it teaches a world
  # to pass --force, and then the real one is missed.
  $RS \
        --exclude 'content' --exclude 'data' \
        --exclude 'pages/index.astro' --exclude 'pages/about.astro' --exclude 'pages/follow.astro' \
        "$TMP/kit/site/src/" "$WORLD_ROOT/site/src/"
  for f in astro.config.mjs package.json package-lock.json deploy.sh README.md; do
    [ -f "$TMP/kit/site/$f" ] && cpfile "$TMP/kit/site/$f" "$WORLD_ROOT/site/$f"
  done
  [ -d "$TMP/kit/site/infra" ] && $RS --exclude 'state.json' \
        "$TMP/kit/site/infra/" "$WORLD_ROOT/site/infra/"
  [ -f "$TMP/kit/site/image-prompts/README.md" ] && \
    cpfile "$TMP/kit/site/image-prompts/README.md" "$WORLD_ROOT/site/image-prompts/README.md"
fi
# The template mirrors the kit's EXAMPLE WORLD: one copy of the fixture, so the example an author
# reads can never drift from the one the kit's own tests run against. `template: true` in
# world.config.yaml is the switch; a world forked from the template keeps whatever it already has,
# and `init-world.sh` removes it. lint.py and the exporter ignore the directory by name (it is a
# world, but it is not THIS vault).
if grep -qE '^template:[[:space:]]*true' "$WORLD_ROOT/world.config.yaml" 2>/dev/null; then
  echo "-> example-world/ (the kit's demo world, mirrored)"
  mkdir -p "$WORLD_ROOT/example-world/world" "$WORLD_ROOT/example-world/campaigns" \
           "$WORLD_ROOT/example-world/meta"
  $RS --delete "$TMP/kit/world/" "$WORLD_ROOT/example-world/world/"
  [ -d "$TMP/kit/campaigns" ] && $RS --delete "$TMP/kit/campaigns/" \
        "$WORLD_ROOT/example-world/campaigns/"
  # The kit's meta/ mixes the demo world's notes with the kit's own documents; only the former are
  # part of the example.
  [ -d "$TMP/kit/meta" ] && $RS --delete \
        --exclude 'templates/' --exclude 'platform-requests/' \
        --exclude 'campaign-authoring-guide.md' --exclude 'world-conventions.md' \
        "$TMP/kit/meta/" "$WORLD_ROOT/example-world/meta/"
  cpfile "$TMP/kit/world.config.yaml" "$WORLD_ROOT/example-world/world.config.yaml"
fi

mkdir -p "$WORLD_ROOT/.pi/prompts"
[ -d "$TMP/kit/.pi/prompts" ] && $RS --delete "$TMP/kit/.pi/prompts/" "$WORLD_ROOT/.pi/prompts/"
mkdir -p "$WORLD_ROOT/.github/workflows"
# The workflows a world runs: the site deploy, the fast checks, and the drift check. The kit's own
# `ci.yml` and `template-fork.yml` are the kit's: a world has no use for either.
for wf in site.yml checks.yml tooling-drift.yml; do
  [ -f "$TMP/kit/.github/workflows/$wf" ] && \
    cpfile "$TMP/kit/.github/workflows/$wf" "$WORLD_ROOT/.github/workflows/$wf"
done
# A workflow that is no longer the kit's is no longer shipped: a world that keeps one is running
# something nobody maintains.
for wf in "$WORLD_ROOT/.github/workflows"/*.yml; do
  [ -e "$wf" ] || continue
  case "$(basename "$wf")" in
    site.yml|checks.yml|tooling-drift.yml) ;;
    *) echo "-> note: .github/workflows/$(basename "$wf") is the world's own; the kit does not maintain it" ;;
  esac
done

if [ "$DRY" = 1 ]; then echo "would write TOOLING_VERSION: $TAG"
else printf '%s\n' "$TAG" > "$WORLD_ROOT/TOOLING_VERSION"; fi

echo "sync-tooling: $OLD -> $TAG"
if [ "$DRY" = 1 ]; then echo "would re-sync the AGENTS.md protocol region"
else
  echo "sync-tooling: the protocol region, if it changed:"
  python3 "$WORLD_ROOT/tools/sync-agent-protocol.py" || true
fi

echo
[ "$DRY" = 1 ] && echo "DRY RUN: nothing above was written." && echo
echo "Review the diff, then run the proof:"
if [ -d "$WORLD_ROOT/.git" ]; then git -C "$WORLD_ROOT" diff --stat; else echo "  (not a git repository: review and commit by hand)"; fi
echo "  cd $WORLD_ROOT && python3 tools/lint.py && tools/verify-world.sh"
echo "Read CHANGELOG.md in the kit for anything a world must do by hand."

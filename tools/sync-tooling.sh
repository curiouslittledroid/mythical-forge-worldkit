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
#   tools/sync-tooling.sh --archive worldkit-v1.2.0.tar.gz   # a release payload, no network at all
#   WORLDKIT_REPO=/path/to/checkout tools/sync-tooling.sh v1.2.0   # a local checkout, for testing
#
# It refuses to run when the world has uncommitted changes in files this sync is about to replace,
# or when it would DELETE a file that lives in a directory the kit owns: the point of vendoring is
# that the diff is reviewable, and a diff nobody can attribute is the failure mode.
#
# HOW IT FETCHES. What this needs from the kit is a TREE, not a history, so the kit publishes one: a
# release payload (tools/build_payload.py, attached to each GitHub release). The transports, in the
# order tried:
#   --archive FILE   a payload on disk. No network, no git: for an air-gapped machine, and the
#                    transport `tools/verify-payload.sh` proves equal to the others.
#   WORLDKIT_REPO    a local checkout or bare mirror, when that path exists.
#   --url URL        a payload by URL.
#   (default)        https://github.com/<owner>/<repo>/releases/download/<tag>/worldkit-<tag>.tar.gz
#                    -- derived from the tag, so no API, no `gh`, no token on a public kit. A tag
#                    from before releases existed falls back to a shallow clone.
#   --from-git       force the clone (a proxy that blocks release assets, say).
# The payload's TOOLING_VERSION must equal the tag asked for, or this refuses: an archive cannot be
# checked out, and a payload attached to the wrong release must not pin a world to a lie.

#
# What it replaces (all of it the kit's):
#   tools/            except tools/local/ — world-owned; the kit never writes it
#   meta/conventions/ the kit's world-facing documents (conventions, the authoring guide, the
#                     thread pattern, site, testimony, tag vocabulary, atlas, the agent protocol).
#                     They live IN the vault, so the rule a world follows is one file away: "the
#                     kit's conventions.md §7" is meta/conventions/conventions.md. Wholly the kit's,
#                     so a document deleted upstream goes away -- which is how the capability
#                     register left every world: it was never an author's document.
#   meta/templates/   the canonical note templates (mirrored: this directory is wholly the kit's,
#                     so a template deleted upstream goes away. A world's own examples live in its
#                     own folder, never here.)
#   site/             the theme: src/ (minus the generated pages and the world's own copy pages),
#                     the Astro config, package.json,
#                     deploy.sh, the infra process, the image-prompt process, the workflow. A
#                     world's own art, prompt notes, audit, deploy state and hero stay.
#   .pi/prompts/      the agent prompts (atlas-refresh, new-creature, the image pipeline),
#                     from the kit's template/.pi/prompts/
#   tools/LICENSE     the kit's licences, MIT and CC BY 4.0 (tools/LICENSE-CONTENT). MIT requires
#                     its notice to travel with every copy, and a world's tools/ is a copy.
#
# It never touches: tools/local/, the world's lore, its world.config.yaml, its meta/ notes, its
# AGENTS.md brief (only the marked protocol region is re-synced, by tools/sync-agent-protocol.py).
set -euo pipefail

WORLD_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
KIT_REPO="${WORLDKIT_REPO:-https://github.com/curiouslittledroid/mythical-forge-worldkit}"
TAG=""
TAG_GIVEN=0
DRY=0
FORCE=0
ARCHIVE=""
URL=""
SHA=""
FROM_GIT=0
# What the re-exec below must hand to the new copy of this script: `"$@"` is gone by then, and the
# old re-exec passed only ${TAG} -- so an option that CARRIES DATA would have been dropped silently.
ORIG_ARGS=("$@")
# `while`/`shift`, not `for arg in "$@"`: three of the options take a value, and a for-loop over the
# expanded list cannot consume one (`--archive f` would leave `f` to be read as the tag).
while [ $# -gt 0 ]; do
  # The argument is consumed BEFORE the case, so the two that take a value consume theirs with a
  # single `shift` and an absent value is an empty string to refuse rather than a failed `shift`
  # that killed the script under `set -e` with no message at all.
  arg="$1"; shift
  case "$arg" in
    --dry-run|-n) DRY=1 ;;
    --force|-f)   FORCE=1 ;;
    --from-git)   FROM_GIT=1 ;;
    --archive)    ARCHIVE="${1:-}"; ARCHIVE_SET=1; if [ $# -gt 0 ]; then shift; fi ;;
    --url)        URL="${1:-}"; URL_SET=1; if [ $# -gt 0 ]; then shift; fi ;;
    --sha256)     SHA="${1:-}"; SHA_SET=1; if [ $# -gt 0 ]; then shift; fi ;;
    # The header, up to the line that starts the script: `sed -n '2,26p'` outgrew its range the
    # first time an option was added above it, and truncated the help without saying so.
    -h|--help)    awk 'NR > 1 { if ($0 == "set -euo pipefail") exit; print }' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    -*)           echo "sync-tooling: unknown option: $arg" >&2; exit 2 ;;
    *)            TAG="$arg"; TAG_GIVEN=1 ;;
  esac
done
# `--archive` with nothing after it would otherwise read as an empty string and fall silently
# through to the network, which is the opposite of what the flag promises.
if [ "${ARCHIVE_SET:-0}" = 1 ] && [ -z "$ARCHIVE" ]; then echo "sync-tooling: --archive needs a file" >&2; exit 2; fi
if [ "${URL_SET:-0}" = 1 ] && [ -z "$URL" ]; then echo "sync-tooling: --url needs a URL" >&2; exit 2; fi
if [ -n "$ARCHIVE" ] && [ -n "$URL" ]; then echo "sync-tooling: --archive and --url are one or the other" >&2; exit 2; fi
# A dry run itemises, so a deletion is visible as `*deleting `; a real run stays quiet.
RS="rsync -a --delete"
[ "$DRY" = 1 ] && RS="rsync -a --delete -i -n"
# ...and a dry run writes nothing, which includes the directories the placement below needs. rsync
# in dry-run mode is happy to report into a directory that does not exist yet; only the `mkdir` had
# to learn the difference.
mkplace() { [ "$DRY" = 1 ] || mkdir -p "$@"; }
# A copy that would not happen: same shape as cp, so the call sites read the same either way.
cpfile() {
  if [ "$DRY" = 1 ]; then echo "would copy $1 -> $2"; else cp "$1" "$2"; fi
}

# --- the rails, before anything is fetched or written -----------------------------------------
# Only the paths this sync actually replaces. `tools/local/`, the world's three site pages and its
# own art are the world's, so a world is expected to have them dirty.
if [ "$DRY" = 0 ] && [ "$FORCE" = 0 ] && [ -z "${SYNC_REEXEC:-}" ] && [ -d "$WORLD_ROOT/.git" ]; then
  dirty="$(git -C "$WORLD_ROOT" status --porcelain -- \
             tools meta/templates meta/conventions site/src \
             site/image-prompts/README.md site/image-prompts/_style.md \
             .pi/prompts .github/workflows 2>/dev/null \
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
#
# The preview is the SAME sync, so it gets the same arguments -- `--archive` above all, or an offline
# sync would silently fetch from the network here, compare against a different tag, and report files
# that are not deletions at all. Being told to `--force` a false finding is how a reader learns to
# --force the real one.
if [ "$DRY" = 0 ] && [ "$FORCE" = 0 ] && [ -z "${SYNC_REEXEC:-}" ]; then
  plan_args=(--dry-run "${ORIG_ARGS[@]}")
  [ "$TAG_GIVEN" = 0 ] && [ -n "$TAG" ] && plan_args+=("$TAG")
  plan="$(SYNC_REEXEC=1 bash "$0" "${plan_args[@]}" 2>&1 || true)"
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

# --- fetch: one seam, four transports -----------------------------------------------------------
# A URL is echoed without its credentials: a private kit is reached as
# `https://x-access-token:<token>@github.com/...` (as tooling-drift.yml does), and a token in a log
# line is a token in a CI transcript.
redact() { sed -E 's|//[^@/]*@|//|' <<<"$1"; }
sha256_of() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | awk '{print $1}'
  else shasum -a 256 "$1" | awk '{print $1}'; fi
}
# `github.com/<o>/<r>/releases/download/<tag>/worldkit-<tag>.tar.gz`: the release payload for a tag.
# Derived, so it needs no API call and no rate limit -- and none of this needs a token, because the
# kit is public. `--latest` redirects to `--tag <tag>`, which is how "the newest" is answered
# without git and without the API.
asset_url() { printf '%s/releases/download/%s/worldkit-%s.tar.gz' "${KIT_REPO%/}" "$1" "$1"; }
latest_tag() {
  command -v curl >/dev/null 2>&1 || return 1
  curl -sSI -o /dev/null -w '%{redirect_url}' "${KIT_REPO%/}/releases/latest" 2>/dev/null \
    | sed -n 's|.*/releases/tag/\(.*\)$|\1|p'
}
# Whatever came in is unpacked to $TMP/kit: the rest of this script never learns which transport ran,
# which is what makes the transports interchangeable.
unpack_payload() {  # unpack_payload <file-or-url> <what-it-is>
  local source="$1" what="$2" file="$1" want_sum="" got
  if [ -f "$source" ]; then
    :
  elif command -v curl >/dev/null 2>&1; then
    file="$TMP/payload.tar.gz"
    curl -fsSL "$source" -o "$file" || return 1
  else
    return 1
  fi
  # A published checksum is a checked checksum. `--sha256` wins, then a `.sha256` beside the file;
  # an unaccompanied payload is a warning rather than a failure, because a hand-built one is a
  # legitimate thing to sync from while developing the payload itself.
  [ -n "$SHA" ] && want_sum="$SHA"
  if [ -z "$want_sum" ] && [ -f "$file.sha256" ]; then
    want_sum="$(awk '{print $1}' "$file.sha256")"
  fi
  got="$(sha256_of "$file")"
  if [ -n "$want_sum" ] && [ "$want_sum" != "$got" ]; then
    echo "sync-tooling: $what does not match its checksum." >&2
    echo "  expected $want_sum" >&2
    echo "  got      $got" >&2
    echo "  Do not extract it. Fetch it again, or compare with the release page." >&2
    return 3
  fi
  [ -z "$want_sum" ] && echo "sync-tooling: no checksum for $what; not verifying it" >&2
  # Refuse a member that would write outside the directory it is unpacked into. The payload's own
  # builder refuses to make one, but the sync is the side that extracts.
  if tar -tzf "$file" 2>/dev/null | grep -qE '(^|/)\.\.(/|$)|^/'; then
    echo "sync-tooling: $what contains an absolute or traversing path; refusing it" >&2
    return 3
  fi
  mkdir -p "$TMP/x"
  tar -xzf "$file" -C "$TMP/x" 2>/dev/null || { echo "sync-tooling: $what is not a tar.gz" >&2; return 3; }
  # Exactly one top-level directory, because that is the shape a payload is promised to have. Two
  # would have been silently half-applied by `head -1`.
  local tops count
  tops="$(find "$TMP/x" -mindepth 1 -maxdepth 1 | wc -l | tr -d ' ')"
  count="$(find "$TMP/x" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')"
  if [ "$tops" != 1 ] || [ "$count" != 1 ]; then
    echo "sync-tooling: $what has $tops top-level entries, not one directory" >&2; return 3
  fi
  mv "$(find "$TMP/x" -mindepth 1 -maxdepth 1 -type d)" "$TMP/kit"
}

clone_kit() {
  git clone --quiet --config advice.detachedHead=false \
    ${TAG:+--branch "$TAG"} --depth 1 "$KIT_REPO" "$TMP/kit"
}

if [ -n "$ARCHIVE" ]; then
  echo "sync-tooling: fetching ${TAG:-the tag this payload names}, from the archive $ARCHIVE"
  unpack_payload "$ARCHIVE" "$ARCHIVE" || exit 2
elif [ -n "$URL" ]; then
  echo "sync-tooling: fetching ${TAG:-the latest tag}, from $(redact "$URL")"
  unpack_payload "$URL" "$(redact "$URL")" || exit 2
elif [ "$FROM_GIT" = 0 ] && [ ! -e "$KIT_REPO" ]; then
  [ -z "$TAG" ] && TAG="$(latest_tag || true)"
  if [ -z "$TAG" ]; then
    # Nothing redirects /releases/latest to a tag: the kit has cut no release yet, or the network is
    # not there. A derived URL would only be a 404 to explain, so go straight to the clone.
    echo "sync-tooling: no release names the newest tag; cloning" >&2
    clone_kit || { echo "sync-tooling: cannot fetch $KIT_REPO" >&2; exit 2; }
  else
    url="$(asset_url "$TAG")"
    echo "sync-tooling: fetching $TAG, from the release payload $(redact "$url")"
    status=0
    unpack_payload "$url" "worldkit-$TAG.tar.gz" || status=$?
    case "$status" in
      0) ;;
      # 1 is `curl` failing: no asset for this tag, which is every tag cut before payloads existed.
      # The clone is the documented fallback and it is not a downgrade.
      1) echo "sync-tooling: no payload for $TAG (a tag from before releases existed?); cloning" >&2
         rm -rf "$TMP/kit" "$TMP/x"
         clone_kit || { echo "sync-tooling: cannot fetch $KIT_REPO at $TAG" >&2; exit 2; } ;;
      # Anything else is a payload we REFUSED -- a checksum mismatch, a traversal, two roots. Falling
      # back to the clone there would silently replace something we rejected with something we did
      # not check, which is the one outcome a verification may never have.
      *) echo "sync-tooling: refusing the payload for $TAG, and not falling back to a clone." >&2
         exit 2 ;;
    esac
  fi
elif [ "$FROM_GIT" = 0 ]; then
  echo "sync-tooling: fetching ${TAG:-the latest tag} from the local checkout $KIT_REPO"
  # `-e`, not `-d`: in the bare-repo-plus-worktree layout these projects use, `.git` is a FILE. With
  # `-d` the documented "local checkout" route silently took the network branch instead.
  git clone --quiet "$KIT_REPO" "$TMP/kit" || { echo "sync-tooling: cannot clone $KIT_REPO" >&2; exit 2; }
  [ -n "$TAG" ] && git -C "$TMP/kit" checkout --quiet "$TAG"
else
  echo "sync-tooling: fetching ${TAG:-the latest tag} from $KIT_REPO (git)"
  clone_kit || { echo "sync-tooling: cannot fetch $KIT_REPO${TAG:+ at $TAG}" >&2; exit 2; }
fi
if [ ! -f "$TMP/kit/TOOLING_VERSION" ]; then
  echo "sync-tooling: what arrived is not a worldkit (no TOOLING_VERSION)" >&2; exit 2
fi
if [ -z "$TAG" ]; then
  TAG="$(cat "$TMP/kit/TOOLING_VERSION")"
fi
# The pin is the tag's twin. A checkout at "the latest tag" would have this for free; an archive has
# no history to ask, so ask the file -- and refuse a payload whose two halves disagree, which is how
# a mis-attached asset (or a copy-paste on a release page) would otherwise pin a world to a version
# it is not holding.
pin="$(tr -d '[:space:]' < "$TMP/kit/TOOLING_VERSION")"
if [ "$pin" != "$TAG" ] && [ "$TAG" != unreleased ]; then
  echo "sync-tooling: the kit says $pin, but $TAG was asked for." >&2
  echo "  Refusing: this world would pin $TAG while holding $pin's files." >&2
  exit 2
fi

OLD="$(cat "$WORLD_ROOT/TOOLING_VERSION" 2>/dev/null || echo none)"

# What THIS run is executing, saved before the copy below replaces the file on disk. Bash is still
# reading the old text, so a step added upstream would silently not run. The comparison has to be
# against this saved copy: comparing the new file with the WORLD's copy cannot notice anything,
# because the rsync has just made them identical -- which is why the first version of this guard
# never fired.
cp "$0" "$TMP/running.sh"

# --exclude local/ is what makes D16 true: a world's own scripts survive every sync.
#
# THE RULE, learned four times: anything this script places INSIDE a world's `tools/` from the KIT'S
# ROOT must be excluded here. The kit keeps its documents at `docs/` and its licences at `LICENSE`,
# `LICENSE-CONTENT`; a world keeps all of them inside `tools/`. Without the exclusion, rsync finds
# them in the world, not in the kit, DELETES them on every run, and the next lines recreate them --
# so the end state is always right and nobody notices, until a run stops in between (a refusal is a
# stop) and leaves a world with no rules, or no licence. `docs/` cost the release before this one.
$RS --exclude 'local/' --exclude 'docs/' \
    --exclude 'LICENSE' --exclude 'LICENSE-CONTENT' \
    --exclude '__pycache__' "$TMP/kit/tools/" "$WORLD_ROOT/tools/"

# The licences have to travel with the code they cover: MIT requires its notice in every copy, and a
# world's `tools/` IS a copy. A world that vendors the kit without this is redistributing it without
# its licence. `tools/LICENSE-CONTENT` covers the vendored documents, which are CC BY 4.0.
for licence in LICENSE LICENSE-CONTENT; do
  [ -f "$TMP/kit/$licence" ] && cpfile "$TMP/kit/$licence" "$WORLD_ROOT/tools/$licence"
done
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
  # Every option is replayed, in its original order, and the resolved tag is appended only when the
  # caller did not name one. The old re-exec passed ${TAG} alone, so `--force` and `--dry-run` were
  # lost -- harmless, because the re-entered run skips both rails -- but an option that carries data
  # was lost silently too, and the run then succeeded having done something else.
  reexec_args=("${ORIG_ARGS[@]}")
  [ "$TAG_GIVEN" = 0 ] && reexec_args+=("$TAG")
  SYNC_REEXEC=1 exec bash "$WORLD_ROOT/tools/sync-tooling.sh" "${reexec_args[@]}"
fi
mkplace "$WORLD_ROOT/meta/conventions"
[ -d "$TMP/kit/template/meta/conventions" ] && $RS --delete \
      "$TMP/kit/template/meta/conventions/" "$WORLD_ROOT/meta/conventions/"
mkplace "$WORLD_ROOT/meta/templates"
[ -d "$TMP/kit/template/meta/templates" ] && $RS --delete "$TMP/kit/template/meta/templates/" "$WORLD_ROOT/meta/templates/"

# The theme. `--delete` everywhere the kit owns the file; the exclusions are what a world keeps:
# the generated pages, its art, its own prompt notes, and its deploy state.
if [ -d "$TMP/kit/site-theme" ] && [ -d "$WORLD_ROOT/site" ]; then
  # Three pages are the WORLD'S copy, not theme chrome: the landing page, About and Follow. The kit
  # ships a neutral version of each so a new world has a working site, and then leaves them alone -
  # a world's About page is its own prose, and a sync that rewrote it would be destroying content.
  mkplace "$WORLD_ROOT/site/src" "$WORLD_ROOT/site/infra" "$WORLD_ROOT/site/image-prompts"
  # The generated directories are the exporter's, not the theme's: a world that has built its site
  # has them and the kit never does. Excluding only `data/generated` is not enough -- rsync still
  # finds `data/` and `content/` in the world and not in the kit, deletes them, and (once the rails
  # existed) refuses every published world. A false alarm is worse than no rail: it teaches a world
  # to pass --force, and then the real one is missed.
  $RS \
        --exclude 'content' --exclude 'data' \
        --exclude 'pages/index.astro' --exclude 'pages/about.astro' --exclude 'pages/follow.astro' \
        "$TMP/kit/site-theme/src/" "$WORLD_ROOT/site/src/"
  for f in astro.config.mjs package.json package-lock.json deploy.sh README.md LICENSES.md; do
    [ -f "$TMP/kit/site-theme/$f" ] && cpfile "$TMP/kit/site-theme/$f" "$WORLD_ROOT/site/$f"
  done
  [ -d "$TMP/kit/site-theme/infra" ] && $RS --exclude 'state.json' \
        "$TMP/kit/site-theme/infra/" "$WORLD_ROOT/site/infra/"
  # The kit's TWO image-prompt files, by name. The rest of a world's site/image-prompts/ is the
  # world's: its own prompt notes and its candidates. `_style.md` is the house style the process
  # calls authoritative, so a world without it has an image pipeline and no look.
  for f in README.md _style.md; do
    [ -f "$TMP/kit/site-theme/image-prompts/$f" ] && \
      cpfile "$TMP/kit/site-theme/image-prompts/$f" "$WORLD_ROOT/site/image-prompts/$f"
  done
fi

mkplace "$WORLD_ROOT/.pi/prompts"
[ -d "$TMP/kit/template/.pi/prompts" ] && $RS --delete \
      "$TMP/kit/template/.pi/prompts/" "$WORLD_ROOT/.pi/prompts/"
mkplace "$WORLD_ROOT/.github/workflows"
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
# A world does not receive the kit's CHANGELOG: it is the kit's own record, and the payload leaves it
# out on purpose. Pointing at it was pointing at a file the reader does not have; the release notes
# for the tag carry the same migration note, at an address a world can open.
case "$KIT_REPO" in
  http*)
    echo "What this release changes for a world is in its notes:"
    echo "  ${KIT_REPO%/}/releases/tag/$TAG" ;;
  *)
    echo "What this release changes for a world is in the kit's CHANGELOG.md:"
    echo "  $KIT_REPO/CHANGELOG.md" ;;
esac

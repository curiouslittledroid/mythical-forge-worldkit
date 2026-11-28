#!/usr/bin/env bash
# Prove a release payload is a faithful, self-consistent replacement for a git checkout.
#
# The claim a payload makes is narrow and total: applying it with its own `tools/sync-tooling.sh`
# produces exactly what applying a checkout of the same tag produces. This script proves the half
# that can be proved without a second kit -- and it is the half that breaks in practice:
#
#   1. the payload passes its own check (`build_payload.py --check`: members, pin, forbidden paths,
#      execute bits, traversal);
#   2. it can build a working world -- a world assembled from its `template/example-world/` and its
#      `tools/` lints with **0 errors**, using the tools it shipped;
#   3. the sync, run from inside that world with nothing but the payload, places every document,
#      template, prompt, workflow and pin where a world reads them;
#   4. a SECOND run changes nothing. That is the assertion that matters: it says the payload's
#      layout and the sync's placement agree, so the payload cannot quietly stop carrying something
#      the sync writes -- the drift that would only surface in a world, after a release.
#
# No network and no engine schemas: this runs in CI on every commit, unlike `verify-kit.sh`.
#
# Usage: tools/verify-payload.sh <worldkit-vX.tar.gz> [--keep]
set -euo pipefail
TOOLS="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$TOOLS/.." && pwd)"
KEEP=0
TARBALL=""
for arg in "$@"; do
  case "$arg" in
    --keep) KEEP=1 ;;
    -h|--help) awk 'NR > 1 { if ($0 == "set -euo pipefail") exit; print }' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    -*) echo "verify-payload: unknown option: $arg" >&2; exit 2 ;;
    *) TARBALL="$arg" ;;
  esac
done
[ -n "$TARBALL" ] || { echo "verify-payload: name a payload (worldkit-vX.tar.gz)" >&2; exit 2; }
[ -f "$TARBALL" ] || { echo "verify-payload: no such file: $TARBALL" >&2; exit 2; }
TARBALL="$(cd "$(dirname "$TARBALL")" && pwd)/$(basename "$TARBALL")"

TMP="$(mktemp -d)"
trap '[ "$KEEP" = 1 ] && echo "verify-payload: kept $TMP" || rm -rf "$TMP"' EXIT
W="$TMP/world"

echo "== check      $TARBALL"
# `--check` is the payload's own contract. In a world the tool ships but has no use; here it is the
# first reader of the thing we are about to trust.
[ -f "$TOOLS/build_payload.py" ] && python3 "$TOOLS/build_payload.py" --check "$TARBALL"

echo "== unpack"
mkdir -p "$TMP/x"
tar -xzf "$TARBALL" -C "$TMP/x"
PAYLOAD="$(find "$TMP/x" -mindepth 1 -maxdepth 1 -type d)"
PIN="$(tr -d '[:space:]' < "$PAYLOAD/TOOLING_VERSION")"
echo "   worldkit $PIN"

# A world, assembled the way a world is: the demo world's vault, the payload's `tools/`, and the
# payload's `site-theme/` where a world keeps its theme. The documents are NOT placed here -- placing
# them is the sync's job, and that is what step 3 is for.
mkdir -p "$W" "$W/site"
rsync -a "$PAYLOAD/template/example-world/" "$W/"
rsync -a "$PAYLOAD/tools/" "$W/tools/"
rsync -a "$PAYLOAD/site-theme/" "$W/site/"

echo "== the payload's own tools build a world that lints"
( cd "$W" && python3 tools/lint.py | tail -2 )

echo "== the sync, from the payload alone"
( cd "$W" && bash tools/sync-tooling.sh --archive "$TARBALL" >"$TMP/sync-1.log" 2>&1 ) \
  || { echo "verify-payload: the sync failed:" >&2; sed 's/^/  /' "$TMP/sync-1.log" >&2; exit 1; }
[ "$(tr -d '[:space:]' < "$W/TOOLING_VERSION")" = "$PIN" ] \
  || { echo "verify-payload: the world pinned $(cat "$W/TOOLING_VERSION"), not $PIN" >&2; exit 1; }
for placed in meta/conventions/conventions.md meta/conventions/tooling.md \
              meta/templates .pi/prompts .github/workflows/checks.yml \
              .github/workflows/site.yml .github/workflows/tooling-drift.yml; do
  [ -e "$W/$placed" ] || { echo "verify-payload: the sync did not place $placed" >&2; exit 1; }
done
( cd "$W" && python3 tools/lint.py | tail -1 )

echo "== a second sync changes nothing"
# Content, mode and path -- deliberately not mtime: the sync's `cp` stamps a fresh mtime on the named
# files, so a file could survive with a new timestamp and still be the same file. A payload that
# stopped carrying something would show up here as a difference, not as a timestamp.
snapshot() {
  W="$1" python3 - <<'PY'
import hashlib, os, sys
root = os.environ["W"]
lines = []
for base, dirs, files in os.walk(root):
    dirs.sort()
    for name in dirs:
        path = os.path.join(base, name)
        lines.append(f"d {os.stat(path).st_mode & 0o777:o} {os.path.relpath(path, root)}")
    for name in sorted(files):
        path = os.path.join(base, name)
        with open(path, "rb") as handle:
            digest = hashlib.sha256(handle.read()).hexdigest()
        lines.append(f"f {os.stat(path).st_mode & 0o777:o} {digest} {os.path.relpath(path, root)}")
print("\n".join(sorted(lines)))
PY
}
snapshot "$W" > "$TMP/before"
( cd "$W" && bash tools/sync-tooling.sh --archive "$TARBALL" >"$TMP/sync-2.log" 2>&1 ) \
  || { echo "verify-payload: the second sync failed:" >&2; sed 's/^/  /' "$TMP/sync-2.log" >&2; exit 1; }
snapshot "$W" > "$TMP/after"
if ! diff -u "$TMP/before" "$TMP/after" > "$TMP/delta"; then
  echo "verify-payload: the second sync was not a no-op: the payload and the sync disagree." >&2
  head -20 "$TMP/delta" | sed 's/^/  /' >&2
  exit 1
fi

echo
echo "verify-payload: ok. $PIN places itself, lints a real vault, and is idempotent."

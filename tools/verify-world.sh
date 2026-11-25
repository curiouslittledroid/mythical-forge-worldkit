#!/usr/bin/env bash
# Builds a world's teaching example into a THROWAWAY copy of the vault and runs the whole pipeline
# on it: lint, transform, validate, thread-check, and the example's scenarios. Nothing in the real
# vault or the real Game Ready Repository is touched.
#
# This is the WORLD's proof. The kit proves itself with ./verify-kit.sh against its demo world; a
# world proves the pipeline against its own vault plus a small, known-good example laid over it.
# That way a world's failing pipeline can be told apart from a broken example.
#
# Usage: tools/verify-world.sh [--keep] [example-dir]
#        the example dir defaults to meta/templates/examples/ferryman
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
KIT="${2:-$ROOT/meta/templates/examples/ferryman}"
TMP="$(mktemp -d)"
trap '[ "${1:-}" = "--keep" ] || rm -rf "$TMP"' EXIT

if [ ! -d "$KIT" ]; then
  echo "verify-world: no example at $KIT" >&2
  echo "  pass one: tools/verify-world.sh --keep <example-dir>" >&2
  exit 2
fi

rsync -a --exclude .git --exclude node_modules --exclude __pycache__ --exclude site/dist \
      "$ROOT/" "$TMP/vault/"
mkdir -p "$TMP/gameready"
# The example's notes overlay the vault, in the layout a real world uses.
cp -R "$KIT/world/." "$TMP/vault/world/" 2>/dev/null || true
cp -R "$KIT/campaigns/." "$TMP/vault/campaigns/" 2>/dev/null || true
# An example that declares its own flags has them appended to the World Flags block.
if [ -f "$KIT/flags-to-add.yaml" ]; then
  python3 - "$TMP/vault" "$KIT/flags-to-add.yaml" "$TMP/vault/tools" <<'PY'
import sys
from pathlib import Path

sys.path.insert(0, sys.argv[3])                      # the vault's own copy of the tools
import kit_config

vault = Path(sys.argv[1])
add = "".join(l for l in Path(sys.argv[2]).read_text(encoding="utf-8").splitlines(True)
              if not l.startswith("#"))
flags = kit_config.load(vault / "world.config.yaml").path_of("flags")
s = flags.read_text(encoding="utf-8")
i = s.rindex("```")
flags.write_text(s[:i] + add + s[i:], encoding="utf-8")
PY
fi

cd "$TMP/vault"
echo "== lint";       python3 tools/lint.py | tail -6 || true
echo "== transform";  GAME_READY_REPO="$TMP/gameready" node tools/transform.mjs | grep -E "Wrote|thread ferry" || true
echo "== validate";   GAME_READY_REPO="$TMP/gameready" node tools/validate-world.mjs 2>&1 | grep -E "schema error|✗" || true
echo "== thread-check"; node tools/thread-check.mjs --repo "$TMP/gameready" | grep -E "OK|problem|Missing|never|Dangling|mismatch" || true
echo "== scenarios";  node tools/simulate-world.mjs --repo "$TMP/gameready" --quiet "$KIT"/scenarios/0*.yaml

[ "${1:-}" = "--keep" ] && echo "kept: $TMP" || true

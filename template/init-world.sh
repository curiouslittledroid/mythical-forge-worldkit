#!/usr/bin/env bash
#
# Turn this template into a world: give the repository an identity.
#
#   ./init-world.sh                                  # ask four questions
#   ./init-world.sh --title "Ashfall" --yes          # non-interactive (id and slug derived)
#   ./init-world.sh --keep-example                   # keep example-world/ to read
#   ./init-world.sh --init-git                       # also discard .git and start a fresh history
#
# What it changes: world.config.yaml (the identity values, all of them), the AGENTS.md title,
# package.json's name and
# pitch line, and nothing else. What it removes: `template: true` (so the tooling sync stops
# mirroring the demo world) and example-world/ (unless asked to keep it).
#
# It does NOT touch git history unless you pass --init-git: a fork's history is yours to decide
# about, and destroying it by default would be rude. It does not touch tools/ (the kit's) or your
# lore notes: the REPLACE prompts in principles/ are answered by interview, in Step 0b.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
CONFIG="world.config.yaml"
AGENTS="AGENTS.md"

TITLE="" ID="" SLUG="" NAME="" ASSUME_NO=0 KEEP_EXAMPLE=0 INIT_GIT=0

die() { echo "init-world: $*" >&2; exit 1; }
say() { printf '%s\n' "$*"; }

usage() { sed -n '2,20p' "$0" | sed 's/^# \?//'; }

while [ $# -gt 0 ]; do
  case "$1" in
    --title)   TITLE="${2:-}"; shift 2 ;;
    --name)    NAME="${2:-}";  shift 2 ;;
    --id)      ID="${2:-}";    shift 2 ;;
    --slug)    SLUG="${2:-}";  shift 2 ;;
    --yes|-y)  ASSUME_NO=1;    shift ;;
    --keep-example) KEEP_EXAMPLE=1; shift ;;
    --init-git)     INIT_GIT=1;     shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown argument: $1 (try --help)" ;;
  esac
done

[ -f "$CONFIG" ] || die "$CONFIG not found: run this from the repository root"
[ -f "$AGENTS" ] || die "$AGENTS not found: is this the template?"

# ---------------------------------------------------------------------------------------------
# 1. The four questions. Every default is derived from the repository directory's name, so that
#    pressing Return four times does the reasonable thing.
# ---------------------------------------------------------------------------------------------
hint="$(basename "$ROOT" | sed -e 's/[-_]codex$//' -e 's/[-_]world$//' -e 's/[-_]//g')"
default_title="$(printf '%s' "$hint" | sed -e 's/^\(.\)/\U\1/')"
default_id="$(printf '%s' "$hint" | tr 'A-Z' 'a-z')"
default_slug="$(printf '%s' "${TITLE:-$default_id}" | tr 'A-Z' 'a-z' | tr -cd 'a-z0-9' | sed 's/^$/myworld/')"

ask() {  # ask <prompt> <default>
  local prompt="$1" def="$2" reply=""
  if [ -n "$def" ]; then prompt="$prompt [$def]"; fi
  if [ "$ASSUME_NO" -eq 1 ]; then printf '%s' "$def"; return; fi
  read -r -p "$prompt: " reply </dev/tty || reply=""
  printf '%s' "${reply:-$def}"
}

if [ -z "$TITLE" ]; then
  say "Four questions. Press Return to accept the default. (Ctrl-C to back out: nothing has been"
  say "changed yet.)"
  say ""
  TITLE="$(ask "The world's title, as it should read on a cover" "$default_title")"
  default_id="$(printf '%s' "$TITLE" | tr 'A-Z' 'a-z' | tr -cd 'a-z0-9')"
  default_slug="$(printf '%s' "$TITLE" | tr 'A-Z' 'a-z' | tr -cd 'a-z0-9')"
  ID="$(ask "Its engine id (world_…)" "world_${ID:-$default_id}")"
  SLUG="$(ask "Its site slug (lower-case, no spaces)" "${SLUG:-$default_slug}")"
  NAME="$(ask "The author's name, for the site footer" "$(git config user.name 2>/dev/null || echo "")")"
fi

# Whatever was not asked for (or was passed on the command line) is derived from the title, so a
# non-interactive run needs one value and nothing else.
[ -n "$TITLE" ] || die "a title is required"
if [ -z "$ID" ]; then
  ID="world_$(printf '%s' "$TITLE" | tr 'A-Z' 'a-z' | tr -cd 'a-z0-9')"
fi
if [ -z "$SLUG" ]; then
  SLUG="$(printf '%s' "$TITLE" | tr 'A-Z' 'a-z' | tr -cd 'a-z0-9')"
fi
case "$ID" in world_*) ;; *) ID="world_$ID" ;; esac
ID="$(printf '%s' "$ID" | tr 'A-Z' 'a-z' | tr -cd 'a-z0-9_')"
SLUG="$(printf '%s' "$SLUG" | tr 'A-Z' 'a-z' | tr -cd 'a-z0-9-')"
[ -n "$SLUG" ] || die "a slug is required"
[ -n "$NAME" ] || NAME="$(git config user.name 2>/dev/null || echo "TODO — the author's name")"

say ""
say "World:  $TITLE"
say "Id:     $ID"
say "Slug:   $SLUG"
say "Author: $NAME"
say ""

# ---------------------------------------------------------------------------------------------
# 2. Rewrite world.config.yaml. Every REPLACE_ME goes: what is left is a value the author can see
#    is provisional (`.invalid` url, a generic description) rather than a placeholder in disguise.
# ---------------------------------------------------------------------------------------------
python3 - "$CONFIG" "$TITLE" "$ID" "$SLUG" "$NAME" <<'PY'
import json, re, sys
from pathlib import Path

path, title, wid, slug, name = sys.argv[1:6]
text = Path(path).read_text(encoding="utf-8")

def setkey(text, key, value, indent="  "):
    """Replace `key: …` at the given indent, once."""
    pattern = re.compile(rf"^{re.escape(indent)}{re.escape(key)}:.*$", re.M)
    if not pattern.search(text):
        raise SystemExit(f"init-world: {path} has no `{key}:` line at that indent")
    return pattern.sub(lambda m: f"{indent}{key}: {value}", text, count=1)

text = setkey(text, "id", wid)
text = setkey(text, "title", title)
text = setkey(text, "slug", slug)
text = setkey(text, "tagline", title)
text = setkey(text, "description",
              f'"{title} — a world for tabletop roleplaying, being built in the open."')
text = setkey(text, "author", name)
text = setkey(text, "license", '"All rights reserved. Use it at your table."')
text = setkey(text, "game_ready_repo", f"../{slug}-gameready")

# The fork's own package name. It is not published, but a fork whose package.json says
# `REPLACE_ME` fails the template fork's "nothing left behind" check, and one named after the
# template is just wrong. The dependency pinned there is the engine's schemas (Phase 5 B4).
pkg = Path("package.json")
if pkg.exists():
    data = json.loads(pkg.read_text(encoding="utf-8"))
    data["name"] = slug
    pkg.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

# The site section.
text = setkey(text, "url", f"https://{slug}.invalid")
text = setkey(text, "buttondown_user", slug)
text = setkey(text, "hero_alt",
              f'"{title} — describe the hero image in a sentence, for readers who cannot see it."')
text = setkey(text, "search_placeholder", '"Search the codex"')
text = setkey(text, "t0_epoch", f'"{title}"')

# `vault.scenarios` points at a campaign that does not exist yet: omit it, as the comment says,
# and the simulator asks for explicit files until there is one.
text = re.sub(r"^  scenarios:.*$\n", "", text, flags=re.M)

# Blurbs with nothing behind them are worse than none: drop the keys, keep the sections.
text = re.sub(r"^\s+blurb: \"REPLACE_ME[^\"]*\"$\n", "", text, flags=re.M)
text = re.sub(r"^  # The landing page's \"Ways in\" cards\..*\n(^  #.*\n)*", "", text, flags=re.M)

# The switch that mirrors the demo world. init-world.sh is removing the demo world instead.
text = re.sub(r"^template: true$\n", "", text, flags=re.M)
text = re.sub(r"^# This repository IS the template.*\n(^#.*\n)*", "", text, flags=re.M)

if "REPLACE_ME" in text:
    leftover = [l for l in text.splitlines() if "REPLACE_ME" in l]
    raise SystemExit("init-world: REPLACE_ME survived in " + path + ":\n  " + "\n  ".join(leftover))
Path(path).write_text(text, encoding="utf-8")
print(f"init-world: {path} rewritten")
PY

# ---------------------------------------------------------------------------------------------
# 2b. The world's own licence. The template's own licence file says "replace this file"; this is
# that, written. A world bible starts restrictive, because a licence granted cannot be taken back.
# ---------------------------------------------------------------------------------------------
python3 - "$TITLE" "$NAME" <<'WORLDLICENCE'
import datetime, sys
from pathlib import Path

title, name = sys.argv[1:3]
year = datetime.date.today().year
Path("LICENSE").write_text(f"""All rights reserved.

Copyright (c) {year} {name}. Everything in this repository that is not the worldkit's machinery --
the lore, the notes, the prose, the maps and the art of {title} -- is the author's, and no licence is
granted to copy, adapt or redistribute it. Run games in it, talk about it, and enjoy it; do not
republish the codex.

THE MACHINERY IS NOT OURS. `tools/` (except `tools/local/`), `meta/conventions/`, `meta/templates/`, the
site theme under `site/` and the agent prompts in `.pi/prompts/` are the worldkit's, vendored at the
tag in `TOOLING_VERSION`. They travel with their own licences, which is the point of having one: MIT
for the tools (`tools/LICENSE`) and CC BY 4.0 for the prose (`tools/LICENSE-CONTENT`).

If you later want to let others reuse {title} -- a permissive wiki, a fan policy, a commercial
licence -- replace this file. Everything published before the change keeps the licence it had.
""", encoding="utf-8")
print("init-world: LICENSE written (all rights reserved)")
WORLDLICENCE

# ---------------------------------------------------------------------------------------------
# 3. The two lines of AGENTS.md that carry the identity.
# ---------------------------------------------------------------------------------------------
python3 - "$AGENTS" "$TITLE" <<'PY'
import sys
from pathlib import Path
path, title = sys.argv[1:3]
text = Path(path).read_text(encoding="utf-8")
text = text.replace("# AGENTS.md: REPLACE_ME", f"# AGENTS.md: {title}", 1)
text = text.replace(
    f"the canonical record of **REPLACE_ME**, a **REPLACE_ME — genre and pitch** world",
    f"the canonical record of **{title}**, a **REPLACE_ME — genre and pitch** world", 1)
Path(path).write_text(text, encoding="utf-8")
print(f"init-world: {path} retitled")
PY

# ---------------------------------------------------------------------------------------------
# 4. The demo world, and git.
# ---------------------------------------------------------------------------------------------
if [ "$KEEP_EXAMPLE" -eq 1 ]; then
  say "-> keeping example-world/ (the demo world) for reference"
elif [ -d example-world ]; then
  rm -rf example-world
  say "-> removed example-world/ (the demo world); it comes back with a sync while \`template: true\`"
  say "   is set, so do not set that switch again by hand"
fi

if [ "$INIT_GIT" -eq 1 ]; then
  if [ -d .git ]; then rm -rf .git; fi
  git init -q -b main
  say "-> git re-initialised on main (history discarded, as asked)"
else
  say "-> git history left alone. For a fresh history: rm -rf .git && git init -b main"
fi

# ---------------------------------------------------------------------------------------------
# 5. Prove it, and say what is left.
# ---------------------------------------------------------------------------------------------
say ""
if python3 tools/lint.py >/tmp/init-world-lint.$$ 2>&1; then
  say "lint: $(tail -1 /tmp/init-world-lint.$$)"
else
  say "lint FAILED — that is not expected; send this to the worldkit:"
  tail -20 /tmp/init-world-lint.$$
  rm -f /tmp/init-world-lint.$$
  exit 1
fi
rm -f /tmp/init-world-lint.$$

todo="$(grep -rl 'REPLACE' principles/ meta/canon-digest.md 2>/dev/null | wc -l | tr -d ' ')"
say ""
say "$TITLE now has an identity. What is left is the world itself:"
say ""
say "  1. Read AGENTS.md, then principles/ — four notes written as questions."
say "  2. Open ROADMAP.md and start at Step 0b. Work by interview; the answers are the world."
say "  3. Write your own site/public/favicon.svg (a placeholder ships) and the hero art."
say "  4. Fill anything still marked REPLACE — $todo file(s) carry prompts in principles/ and"
say "     meta/canon-digest.md, and lint will warn about each one until you do."
say "  5. Read LICENSE — all rights reserved, which is the right default. Change it if you want"
say "     others to reuse the world: a licence you grant cannot be taken back."
say "  6. Check world.config.yaml: spelling (british?), features, content_descriptors, and the"
say "     site's sections — every note kind the world uses needs a section to live in."
say ""
say "Then: python3 tools/lint.py && tools/verify-world.sh"

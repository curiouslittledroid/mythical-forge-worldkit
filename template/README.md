# World Template — a Mythical Forge world codex

This repository is a **starting point for a new built world**: a vault-shaped repository with the
rules, the tools and the note templates already in place, and every question still unanswered.

It is **not a world**. It carries one small worked example — `example-world/`, the worldkit's demo
world — so that "what does a finished note look like?" has an answer on disk. Delete that directory
once you have notes of your own.

The vault's shape is fixed by the toolchain (the kit's `conventions.md` §3). What goes in
it is yours: a world bible for tabletop play, written to be run by a game master, with the lore
readable in Obsidian, the engine's data extracted from it, and — if you want one — a public site
generated from its open content.

---

## Start a world in 30 minutes

### 1. Make it yours (2 minutes)

```bash
./init-world.sh
```

It asks four things — the world's name, its title, its id and its site slug — then rewrites
`world.config.yaml`, drops the `template: true` switch, removes `example-world/`, and re-initialises
git with a first commit. (Do it by hand if you prefer: edit the `world:` block, delete that switch
and the directory, then `rm -rf .git && git init -b main`.)

### 2. Read the brief (5 minutes)

`AGENTS.md` is the world brief, followed by the worldkit's shared protocol — the persona, the session
protocol, the vault and engine rules, the writing conventions. It is what an AI agent loads first,
and it is worth the five minutes for a human too.

Then open `principles/`. It holds **four notes written as questions**, and they are the only thing
standing between you and a world that does not cohere. You do not answer them alone: `ROADMAP.md`
Step 0b is the session that does.

### 3. Start writing (20 minutes)

Open `ROADMAP.md` and start at **Step 0b**. If you are working with an AI agent, that is the whole
instruction — the roadmap gives the step's goal, its **Read first** list, what it produces and how
you know it is done.

Work in interview rounds, not dictation: an agent proposing numbered questions with recommendations,
you accepting or changing them. See the protocol in `AGENTS.md`.

### 4. Decide the licence — or leave it

`init-world.sh` wrote `LICENSE` as **all rights reserved**, which is the right default for a world
bible: you can loosen a licence later, but not tighten one, because everything already published
keeps the licence it had. The worldkit's own material you are carrying — `tools/`, `meta/conventions/`,
`meta/templates/`, the site theme, the prompts — is MIT and CC BY 4.0 (`tools/LICENSE`,
`tools/LICENSE-CONTENT`) and is not yours to relicense. **Read
`meta/conventions/licensing.md`** before you decide: it says what you inherit, what you decide, and
what you may not touch.

### 5. Keep the machinery current

```bash
tools/sync-tooling.sh v1.0.x     # fetch a worldkit tag
tools/verify-world.sh            # prove the world still builds
```

The sync replaces `tools/`, `meta/conventions/` and `meta/templates/`, rewrites `TOOLING_VERSION`, and
re-syncs the protocol region of `AGENTS.md`. It never touches `tools/local/` (your own scripts) or the
three site pages you own. One command, one commit, and the diff *is* the upgrade.

---

## The tour

| Path | What it is |
|---|---|
| `AGENTS.md` | The world brief and the worldkit's protocol. **Read first.** |
| `ROADMAP.md` | The ordered plan: 0a → 16, with each step's context and a status tracker to keep current. |
| `world.config.yaml` | **This world's identity:** ids, title, the notes the tools read, the feature switches, the site's navigation. |
| `principles/` | The four notes that decide what the world is. Answer these first. |
| `world/` | The lore. The transformer scans this and `campaigns/` — nothing else. |
| `campaigns/` | Campaigns, their modules and their scenarios. `campaigns/_seeds/` holds the ideas not yet grown. |
| `maps/` | Coordinate data, the atlas register and the sheets. |
| `meta/` | This world's own decisions: the canon digest, the name list, open questions, the mechanics gaps, the site notes. |
| `tools/` | The worldkit's tools, **vendored** and pinned. `tools/local/` is yours; the rest is not. |
| `meta/conventions/` | The kit's world-facing documents, at the pinned version. The kit's, not yours. |
| `meta/templates/` | One template per note type, mirrored from the kit. **Never add a file here.** |
| `site/` | The public, player-facing site, generated from `open` content only. |
| `example-world/` | The demo world. Read it, then delete it. |

Every folder has an `_index.md` that links its notes.

---

## This repository and the worldkit

The machinery is not yours to maintain. [`mythical-forge-worldkit`](https://github.com/curiouslittledroid/mythical-forge-worldkit)
owns the tools, the rules, the note templates and the site theme. A world repository owns the lore and
the world's decisions, and holds a **pinned copy** of the machinery:

| Vendored here | Source | Updated by |
|---|---|---|
| `tools/` (except `tools/local/`) | the kit's `tools/` | `tools/sync-tooling.sh <tag>` |
| `meta/conventions/` | the kit's `template/meta/conventions/` | the same |
| `meta/templates/` | the kit's `meta/templates/` (mirrored) | the same |
| most of `site/` | the kit's `site/` (theme, infra, workflow) | the same |
| `.pi/prompts/` | the kit's `template/.pi/prompts/` | the same |
| `TOOLING_VERSION` | the kit's tag | the same |

**Rules that follow from this:**

- **A kit document is cited by name and section, never by a wikilink.** It is the kit's, not this
  vault's: the text is at `meta/conventions/<name>.md`, and that is where a reader should look.
- **Never edit a vendored file.** Your edit is silently reverted at the next sync. World-specific
  scripts go in `tools/local/`; world-specific rules go in `meta/world-conventions.md`.
- **The engine's Game Ready Repository is a separate, generated repository.** Never hand-edit it.

`tools/check_citations.py` enforces the first rule (a `§N` must resolve in the document it names) and
will fail the build if a citation rots.

---

## What to do when

| I want to… | Do this |
|---|---|
| Know what to do next | `ROADMAP.md` |
| Know how to write a note | the kit's `conventions.md`, then `meta/world-conventions.md` for this world's own choices |
| Write a thread, a Campaign or a Quest | the kit's `campaign-authoring-guide.md` |
| See a finished example | `example-world/` |
| Check my work | `python3 tools/lint.py` |
| Prove the whole pipeline | `tools/verify-world.sh` |
| Publish the player-facing view | the kit's `meta/conventions/site.md`, plus this world's `meta/site.md` |
| Add a creature, an image or refresh the map | `.pi/prompts/` (the project prompts) |

---

## Requirements

- **Python 3.12+**, standard library only. No pip installs.
- **Node 18+** and `npm` for the site and the transformer.
- **`MYTHICAL_FORGE_ROOT`**, pointing at the platform repository. It has **no default**: the tools fail
  loudly and name it, rather than building against the wrong checkout.
- `git`, and optionally [Obsidian](https://obsidian.md) — open the repository root as a vault.

---

## The commands

```bash
python3 tools/lint.py                 # every note: frontmatter, ids, links, engine blocks, spelling
python3 tools/check_citations.py      # every §N and section reference resolves
python3 tools/disclosure.py --check   # every section is classified open / earned / sealed
tools/verify-world.sh                 # the whole pipeline, ending in every scenario

python3 tools/site_export.py          # build the site's content from open sections only
npm --prefix site run build           # build the site
python3 tools/site_link_check.py      # no internal link reaches a file that does not exist
```

Run the linter after any bulk or scripted edit — before you commit, not after.

---

## If you are an AI agent

Read `AGENTS.md` first: it is the brief, and below the protocol marker it is the same text every
world built this way shares. Then `ROADMAP.md` for the step you are on, then only that step's
**Read first** list. Do not load the whole canon.

Record **decisions, not discussion**, in the note of the entity each decision is about; each fact has
one home. Commit at the end of the session with a clear message, and keep the working tree clean.

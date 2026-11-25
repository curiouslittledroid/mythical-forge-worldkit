# mythical-forge-worldkit

**The tooling and the shared rules for a Mythical Forge world codex.** A *world* is a repository of
lore — places, people, factions, history — written as markdown notes. This kit turns one into a
**Game Ready Repository** the engine can run, a **player-facing site**, and a set of maps; and it
holds the rules every world follows so that a new world does not have to invent them.

It is not a world and it contains no canon. Its only prose is the rules, and its only example is the
**Ferryman's Debt** — a fixture small enough to hold in your head and real enough to run.

## The three repositories

| Repository | Owns | Depends on |
|---|---|---|
| **`mythical-forge-worldkit`** (this) | the tools, the rules, the note templates, the site theme, the engine-capability register, the agent protocol | — |
| `mythical-forge-world-template` | an empty, forked-ready world: the folder skeleton, the quickstart, `init-world.sh` | the kit, vendored |
| a world (for example `hollowfall-codex`) | its lore, its decisions, its spelling, its vocabularies | the kit, vendored at `tools/` |

A world does **not** depend on this repository at run time. It holds a **copy** of the kit's tools in
`tools/`, pinned by `TOOLING_VERSION`, and updates them with `tools/sync-tooling.sh`. Nothing is
published as a package and nothing is installed: a world is a git repository that happens to contain
a copy of `tools/`, so a clone is always buildable.

## Install it in a world

```bash
git clone https://github.com/curiouslittledroid/mythical-forge-world-template my-world
cd my-world && ./init-world.sh        # asks for the world's name, title, id and site slug
```

To start from an existing world instead, copy the kit by hand:

```bash
cp -R /path/to/mythical-forge-worldkit/tools ./tools
echo v1.0.0 > TOOLING_VERSION
```

Then write `world.config.yaml` (**the one file a world must supply**) and start authoring notes. The
config's schema is `docs/conventions.md` §2; a worked example is this repository's own, which is the
demo world's.

## What a world must supply

| Thing | Where | Notes |
|---|---|---|
| its identity | `world.config.yaml` → `world:` | id, title, slug, tagline, the game-ready repo path |
| the note slugs its tools must find | `world.config.yaml` → `vault.notes` | the flag register, the calendar, the eras, the site vocabulary, the testimony book. **By id, never by path** |
| its spelling | `world.config.yaml` → `vault.spelling` | `british` (default), `american` or `off`. Units are not a choice: the codex is metric |
| which subsystems it uses | `world.config.yaml` → `features` | `site`, `atlas`, `testimony`, `voice`. An unlisted feature is inert |
| its lore | `world/`, `principles/`, `maps/`, `campaigns/` | the vault |
| its own choices on top of the rules | `meta/world-conventions.md` | the folder shape it adds, its vocabulary lists, its keystones |
| a pointer to each kit document it cites | its `meta/` | by **name and section**, never a wikilink: a wikilink cannot reach another repository |

## Layout

```
docs/                  the rules and the registers - the kit's own documents
  conventions.md               the id grammar, the note-body contract, the lint codes, the vocabularies
  engine-capability-register.md  what the engine can express, the platform requests, the dispositions
  agent-protocol.md            the protocol a world's AGENTS.md carries verbatim
  campaign-authoring-guide.md  how to author a thread, a Campaign, its Modules and Quests
  thread-pattern.md            why a thread is a state graph (the reference behind the guide)
  site.md                      how a site is generated from a vault
  testimony.md                 the first-person device, the voice sheets and the two checks
  tag-vocabulary.md            the five rules, the block the linter reads, how themes are chosen
  atlas.md                     the map pipeline, the data layer, and what stays the world's
meta/templates/        one template per note type. The end-to-end example IS the demo world
                       (world/, campaigns/ferryman-demo/), so there is no second copy to drift
meta/platform-requests/  draft specs written for the platform repository - not the kit's backlog
tools/                 the scripts and their tests
world/, campaigns/, meta/  the DEMO WORLD: the smallest complete vault the tools can run against
verify-kit.sh          the end-to-end proof: lint, transform, validate, thread-check, six scenarios
```

## Verify it

```bash
python3 tools/test_lint.py                 # and the four other suites
python3 tools/lint.py                      # the demo world
./verify-kit.sh                            # the whole pipeline, in a throwaway directory
```

`verify-kit.sh` needs the **platform repository** (`MYTHICAL_FORGE_ROOT`, pointing at the directory
that holds `packages/authored-content`), because the transformer and the validator are the engine's
own code. It copies the demo world to a throwaway directory, overlays the Ferryman's Debt, and runs
lint → transform → validate → thread-check → six scenarios. Nothing in a real world is touched.

CI runs the Python suites and the lint only: the platform repository is private, so the end-to-end
proof is a local, pre-commit step. Run it before you tag a release.

## Working on the kit

`AGENTS.md` is the brief for an agent working **here** (as opposed to on a world). In short:

- **No world literals anywhere** — not in a script, not in a default, not in a doc example. The
  example is the Ferryman's Debt; if it cannot be, use a placeholder.
- **The tests are the contract**, and every tool must run against the demo world with no world
  literals. A change that makes a tool depend on a world is wrong.
- **A doc change is a code change**: the templates, the conventions and the tools are one system.
- A change a world cannot absorb silently is a **major** version bump plus a migration note in
  `CHANGELOG.md`.

## Status

Extracted from the first world (`hollowfall-codex`) in 2026. **Version `1.0.0`**; the version a world
pins lives in its `TOOLING_VERSION`. The extraction's remaining business is in `ROADMAP.md`.

## Licence

Tooling and documentation: to be decided (see `ROADMAP.md`, K1). The rule is intended to be
permissive for a world that wants to publish its own codex; the demo world and every template
example are *not canon* and carry no rights of their own.

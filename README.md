# mythical-forge-worldkit

**The tooling and the shared rules for a Mythical Forge world codex.** A *world* is a repository of
lore — places, people, factions, history — written as markdown notes. This kit turns one into a
**Game Ready Repository** the engine can run, a **player-facing publishable website**, and a set of maps; and it
holds the conventions every world follows so that it is consumable by the Mythical Forge engine.

It is not a world and it contains no canon. Its only prose are the conventions. It contains an example world - 
**Ferryman's Debt** — a fixture small enough to hold in your head and real enough to run.

## The three repositories

| Repository | Owns | Depends on |
|---|---|---|
| **`mythical-forge-worldkit`** (this) | the tools, the rules, the note templates, the website theme, the engine-capability register, the agent protocol | — |
| `mythical-forge-world-template` | an empty, forked-ready world: the folder skeleton, the quickstart, `init-world.sh` | the kit, vendored |
| a world (for example `hollowfall-codex`) | its lore, its decisions, its spelling, its vocabularies | the kit, vendored at `tools/` |

A world does **not** depend on this repository at run time. It holds a **copy** of the kit's tools in
`tools/`, pinned by `TOOLING_VERSION`, and updates them with `tools/sync-tooling.sh`. Nothing is
published as a package and nothing is installed: a world is a git repository that happens to contain
a copy of `tools/`, so the world repo is always buildable.

## Install it in a world

```bash
# clone the template world
git clone https://github.com/curiouslittledroid/mythical-forge-world-template my-world

# set up the new world and import the worldkit scripts
cd my-world && ./init-world.sh        # asks for the world's name, title, id and site slug
```

To put the kit into an existing world instead, take the **release payload** — an archive attached to
every tag, reduced to what a world receives and needing no token, because this repository is public:

```bash
curl -LO https://github.com/curiouslittledroid/mythical-forge-worldkit/releases/download/v3.4.0/worldkit-v3.4.0.tar.gz
tar -xzf worldkit-v3.4.0.tar.gz -C /tmp
cp -R /tmp/worldkit-v3.4.0/tools ./tools          # the one time copying is right: no tools/ yet
tools/sync-tooling.sh --archive "$PWD/worldkit-v3.4.0.tar.gz"
```

**Never extract the payload over a world.** It appears to work — and leaves the kit's documents where
a world does not read them, so the world pins the new version while its rules stay old. The archive is
applied by the tools inside it; `ARCHIVE.md` in the download says so, and `docs/release-payload.md`
here explains why.

After the first update, a world never needs the archive by hand again — its own sync fetches the
release for the tag:

```bash
tools/sync-tooling.sh v3.4.0        # the release payload (or the clone, for an older tag)
tools/sync-tooling.sh --archive worldkit-v3.4.0.tar.gz   # offline
```

A checkout on this machine is still a transport, and is how the tests drive it:
`WORLDKIT_REPO=/path/to/mythical-forge-worldkit tools/sync-tooling.sh v3.4.0`.

Then write `world.config.yaml` (**the one file a world must supply**) and start authoring notes. The
config's schema is `meta/conventions/conventions.md` §2; a worked example is the demo world's config at
`template/example-world/world.config.yaml`.

**Which command to run, and when** is the runbook: `meta/conventions/tooling.md` in a world, or
`template/meta/conventions/tooling.md` here. It maps what you just changed to the command that proves
it — the everyday loop, the pre-commit gate, publishing, and what each tool writes.
`tools/README.md` is the script-by-script reference beside it.

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
docs/                  KIT MAINTENANCE only - nothing an author of a world needs to read
  extraction.md                the record of the extraction from the first world. It names that
                               world throughout, so it does NOT travel with a world
meta/platform-requests/  draft specs written for the platform repository - not the kit's backlog
tools/                 the scripts and their tests
site-theme/            the Astro theme, vendored into a world as site/
template/              the generated world-template's source: the skeleton a new author forks
                       (world.config.yaml, init-world.sh, the brief, the roadmap, principles/,
                       the empty vault) plus the embedded example-world/ demo
template/meta/conventions/  EVERY WORLD-FACING DOCUMENT: conventions.md (the rules),
                       campaign-authoring-guide.md, thread-pattern.md, site.md, testimony.md,
                       tag-vocabulary.md, atlas.md, agent-protocol.md,
                       tooling.md (which script to run, and when), licensing.md (what a world may
                       and may not relicence)
                       A world holds these at meta/conventions/ at the pinned tag. They are prose,
                       not notes: no frontmatter, no id, cited by name and section, never wikilinked
template/meta/templates/    one template per note type, vendored into a world as meta/templates/
template/.pi/prompts/  the agent prompts (atlas refresh, new creature, the image pipeline),
                       vendored into a world as .pi/prompts/
example-world/         (inside template/) the DEMO WORLD: the smallest complete vault the tools
                       run against
export-template.sh     assembles mythical-forge-world-template from template/ + the vendored kit
tools/build_payload.py builds the release payload a world syncs from (docs/release-payload.md)
tools/verify-payload.sh  its proof: lints a vault, places itself, and a second sync is a no-op
verify-kit.sh          the end-to-end proof: assembles the demo world, then lint → transform →
                       validate → thread-check → six scenarios
```

## Verify it

```bash
python3 tools/test_lint.py                 # and the other suites
tools/verify-payload.sh dist/worldkit-*.tar.gz   # the release payload (no schemas needed)
./verify-kit.sh                            # assembles the demo world and runs the whole pipeline
```

`verify-kit.sh` needs the **engine's schemas**, because the transformer and the validator are the
engine's own code (Design 23 §4.1). Install them once — they are published on GitHub Packages, so
this needs a token with `read:packages`:

```bash
export NODE_AUTH_TOKEN=<a fine-grained PAT with read:packages>
npm install          # the pinned version, from the repository's own .npmrc
```

Or point at a local checkout instead — it wins when set, and it is how an unreleased schema change is
developed: `MYTHICAL_FORGE_ROOT=/path/to/mythical-forge/main ./verify-kit.sh`. Either way the script
assembles the demo world (`template/example-world/` + the vendored `tools/`) in a throwaway directory,
and runs lint → transform → validate → thread-check → six scenarios. Nothing in a real world is touched.

CI runs the same proof: the suites, the lint, the citations and the workflow check always, and — when
the `WORLDKIT_PACKAGES_TOKEN` secret is present — the guide check and `./verify-kit.sh`. Without the
secret those two are skipped with a warning naming what was skipped, because the schemas live on a
private registry.

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

Extracted from the first world in 2026 (`CHANGELOG.md` is the record, `docs/extraction.md` the
reasoning). The version a world pins lives in its `TOOLING_VERSION`; this repository's own version
is the newest tag. The kit's open work is in `ROADMAP.md`.

## Licence

**MIT** for the tools, the theme and the scripts (`LICENSE`); **CC BY 4.0** for the prose — the
documents, the note templates, the agent prompts and the example world (`LICENSE-CONTENT`). The
prose is the part that exists to be copied into other worlds, which is what that licence is for.

A world that vendors the kit receives both at `tools/LICENSE` and `tools/LICENSE-CONTENT`, because
MIT requires its notice to travel with every copy — and a world's `tools/` is a copy. A world's own
lore stays the world's, under the world's own `LICENSE`.

**`template/meta/conventions/licensing.md` is the reasoning:** why MIT and not Apache-2.0 or the GPL,
why CC BY and not BY-SA, why a world starts restrictive, and how the notices are enforced rather
than declared. It is world-facing (a world holds it at `meta/conventions/licensing.md`), because a
world author has to know what they inherit and what they may not relicence.

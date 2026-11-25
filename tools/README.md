# Codex tools

The scripts that read a world codex and produce the things made from it: the Game Ready
Repository, the public site, the atlas, and the checks that keep the vault honest.

**Nothing here is Hollowfall-specific.** Every world value lives in `world.config.yaml` at the
vault root and in the world's fenced vault blocks, both read by `kit_config` (Python and Node).
A script that needs to know the world's name, its section list, its era vocabulary or where its
flags note lives asks the config. See `ROADMAP-EXTRACTION.md` for the design and the reasoning.

Standard library Python 3.12+; Node 18+ for the transformer and the site.

## Setup: `MYTHICAL_FORGE_ROOT`

The Node tools read the platform's own schemas and YAML implementation, so they need the
checkout that holds `packages/authored-content`:

```bash
export MYTHICAL_FORGE_ROOT=/path/to/mythical-forge/main
```

**There is no default.** In a bare-repo-plus-worktree layout it is the *worktree*
(`.../mythical-forge/main`), not the parent. Without it a Node tool stops immediately and says
so; with a wrong path it names the missing package rather than failing later on a stray `require`.

## Configuration

| File | What it is |
|---|---|
| `world.config.yaml` | The world's identity, the ids of the notes the tools need, the feature switches, and the site's plumbing. Validated strictly: an unknown key is an error. |
| `kit_config.py` / `kit_config.mjs` | The readers. `path_of("flags")` resolves a config name to a note **by id**; `block("eras")` parses a vault block. Run `python3 tools/kit_config.py` to print what the tools see. |
| `yaml_subset.py` | The strict YAML reader, shared by `kit_config.py` and `atlas_yaml.py`. A world file that steps outside the subset is refused with a `file:line`. |
| `testkit.py` | Fixture helper for the test suites: writes a config and a vocabulary note into a temp vault. |

A world's `features:` switch turns subsystems off. A tool that belongs to an off feature refuses
to run rather than guessing.

## The scripts

| Script | Purpose |
|---|---|
| `kit_config.py` | Reads the world config and its blocks. Import it; also runnable to print a summary. |
| `kit_config.mjs` | The same, for Node. `loadConfig()`, `mfRoot()`, `block()`, `notePath()`. |
| `yaml_subset.py` | The strict YAML reader behind both config readers and the atlas. |
| `lint.py` | The vault linter (only standard-library Python). See the kit's `docs/conventions.md` §16. |
| `test_lint.py` | Its tests. |
| `testkit.py` | Fixture helper for the suites (config + vocabulary note). |
| `test_kit_config.py` | Tests for the two config readers and the subset parser, including a **parity test** that the Python and Node readers agree on the live config. |
| `disclosure.py` | The effective disclosure class of every lore section (conventions §7); `--list` shows the sections still unreviewed; `--check` exits 1 if there are any (run it before a commit). Its `classify` is the reference for the corpus export. |
| `test_disclosure.py` | Its tests. |
| `voice_lint.py` | Checks each testimony against its teller's voice sheet: vocabulary the teller never says, and places outside their range. |
| `voice_stale.py` | Reports accounts that claim to describe the present but whose surrounding canon has moved since. Reads the present year from the `chronology` block. |
| `test_voice.py` | Their tests. |
| `transform.mjs` | Codex → Game Ready Repository. Deterministic. |
| `validate-world.mjs` | Validates a generated Game Ready Repository with `@mythical-forge/authored-content`. |
| `thread-check.mjs` | Flag registry (declared, set, read), own-stage guards, references inside Conditions and Effects, thread interface. |
| `codex-threads.yaml` (generated) | Written by `transform.mjs`: each thread's members and interface. Tooling only; not an entity. |
| `simulate-world.mjs` | The idle-world and scenario simulator; generates fast-forward start states; reports coverage. |
| `verify-example.sh` | Builds the teaching example into a throwaway copy of the vault and runs lint, transform, validate, thread-check and its six scenarios. |
| `site_export.py` | Exports the **player-facing site content** from the `open` part of every section (see the kit's `docs/site.md`). Imports `disclosure.classify`; never re-derives it. Emits `site.json` so the Astro build gets the world's branding. |
| `test_site_export.py` | Its tests: one per redaction rule. |
| `site_link_check.py` | Fails the build on any internal link to a file that does not exist. |
| `site_audit_report.py` | Prints the publish audit into a CI run summary; `--strict` gates the build. |
| `verify-world.sh` | **A world's pipeline proof.** Copies the vault to a throwaway directory, overlays a small known-good example (default `meta/templates/examples/ferryman`), and runs lint → transform → validate → thread-check → scenarios. It telling a *world's* broken pipeline apart from a broken example is the point: the kit proves itself separately, with `verify-kit.sh`. |
| `sync-tooling.sh` | **A world's updater.** Fetches a release tag of the worldkit and replaces this repo's `tools/` (except `tools/local/`), the kit's `docs/` into `tools/docs/`, the templates and the theme. It is the one command that moves a world's `TOOLING_VERSION` pin, and its diff is the whole review surface. |
| `check-guide.mjs` | Checks every `yaml` block in the campaign authoring guide against the engine's schema. The guide is a kit document, so its path is **resolved**, not hardcoded: `<kit>/docs/`, the staged `<repo>/worldkit/docs/`, or an argument. |
| `sync-agent-protocol.py` | Writes the kit's `docs/agent-protocol.md` into `AGENTS.md`, between the marked region. `--check` fails on drift and is what CI runs. A world's `AGENTS.md` is its own brief plus this region; the protocol is duplicated on purpose, because an agent may never follow a link out of the repository, and the duplication is kept honest by this tool. |
| `atlas_yaml.py` | Reads and validates `maps/atlas-features.yaml` (the reader is `yaml_subset.py`; this owns the atlas schema). |
| `atlas_tables.py` | Renders `maps/atlas-features.md` from the YAML; `--check` fails if it is stale. |
| `atlas_diff.py` | Compares the YAML with `HEAD` or a file; reports added, removed, moved and changed features. |
| `atlas_previews.sh` | Renders the PNG previews (macOS + Chrome). |
| `local/make_atlas.py` | Renders the SVG sheets. **World-owned** (D16): label placement, the frame layout and the map title are world choices, so it lives in `tools/local/` and `sync-tooling.sh` never touches it. |

## Atlas tools

How to run them, and the recipes for changing the map, are in
[[atlas-howto|Keeping the Map Up to Date]] (`maps/atlas-howto.md`). Short version:

```
python3 tools/atlas_yaml.py maps/atlas-features.yaml   # validate
python3 tools/atlas_tables.py                          # maps/atlas-features.md
python3 tools/local/make_atlas.py                            # maps/svg/*.svg
python3 tools/atlas_diff.py                            # what changed
tools/atlas_previews.sh                                # PNG previews
```

`/atlas-refresh` (`.pi/prompts/atlas-refresh.md`) does all of it from the place notes.

## Transformer and thread tools

```
node tools/transform.mjs [--out <game-ready-repo>]
node tools/validate-world.mjs [--repo <game-ready-repo>]
node tools/thread-check.mjs   [--repo <game-ready-repo>]
node tools/simulate-world.mjs --coverage   # every scenario; --quiet for results only; --md for a table
node tools/simulate-world.mjs campaigns/dustport-pilot/scenarios/05-rescue-then-idle.yaml   # one scenario, full timeline
```

The Game Ready Repository defaults to `world.game_ready_repo` in the config; the flags note is
found by the id in `vault.notes.flags`; the overland entity id comes from `world.overland`.

- Reads notes in `world/` and `campaigns/` whose frontmatter is `engine: true`.
- Extracts fenced `engine` blocks; assembles `OVERLAND_NODE` / `OVERLAND_EDGE` fragments into the
  overland graph; converts `distance_km` → whole `distance_miles`.
- Reads the world's flags from the `flags` block into `manifest.yaml`.
- Resolves `_known_by_groups` / `_believed_by_groups` to NPC ids (conventions §9.5).
- Never writes `author_id` or `world_id` except in `manifest.yaml`.

A scenario scripts the player (`quest:`, `kill:`, `move:`) and other threads (`inputs:`), then
asserts flags, events, edges, locations and Want states. `start: { fast_forward: <stage flag> }`
generates and applies a Campaign start state.

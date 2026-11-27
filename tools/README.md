# Codex tools

The scripts that read a world codex and produce the things made from it: the Game Ready
Repository, the public site, the atlas, and the checks that keep the vault honest.

**Nothing here is specific to one world.** Every world value lives in `world.config.yaml` at the
vault root and in the world's fenced vault blocks, both read by `kit_config` (Python and Node).
A script that needs to know the world's name, its section list, its era vocabulary or where its
flags note lives asks the config. The design and the reasoning are the kit's, in its own
`docs/extraction.md`; a world does not receive that file.

**Which script to run, and when:** the kit's `meta/conventions/tooling.md`. It is the task-first
map — what you just changed, what proves it, what each tool writes and what it will not catch. This
file is the reference: one row per script, its purpose, its flags.

Standard library Python 3.12+; Node 18+ for the transformer and the site.

## Setup: the engine's schemas

The Node tools read the engine's own schemas and its YAML implementation (Design 23 §4.1). They come
from one of two places, and `tools/kit_config.mjs` is the only code that decides which:

| Source | When | How |
|---|---|---|
| **The published package** — `@curiouslittledroid/authored-content`, pinned exactly in this repository's root `package.json` | The default, and what CI uses | `export NODE_AUTH_TOKEN=<a PAT with read:packages>`, then `npm install`. The repository's `.npmrc` points at GitHub Packages; without a token the install is a 401 |
| **A local checkout** — `packages/authored-content` in the platform repository | Developing an unreleased schema change | `export MYTHICAL_FORGE_ROOT=/path/to/mythical-forge/main` — it wins when set |

A tool that finds neither stops immediately and names both fixes. A `MYTHICAL_FORGE_ROOT` pointing
somewhere without `packages/authored-content` is its own loud error, rather than a stray `require`
much later. In a bare-repo-plus-worktree layout the path is the *worktree*
(`.../mythical-forge/main`), not the parent.

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
| `lint.py` | The vault linter (only standard-library Python). See the kit's `meta/conventions/conventions.md` §16. |
| `check_workflows.py` | Loads every `.github/workflows/*.yml` far enough to find a **duplicate key**. A lenient parser keeps the last one; GitHub refuses the file, and the workflow then appears in Actions named by its path, failing every run. Writes nothing. |
| `test_check_workflows.py` | Its tests. |
| `check_citations.py` | Resolves every `§N` citation against the document it names and fails on one that does not exist. See the kit's `meta/conventions/conventions.md` §16.1. |
| `test_lint.py` | Its tests. |
| `testkit.py` | Fixture helper for the suites (config + vocabulary note). |
| `test_kit_config.py` | Tests for the two config readers and the subset parser, including a **parity test** that the Python and Node readers agree on the live config. |
| `disclosure.py` | The effective disclosure class of every lore section (conventions §7); `--list` shows the sections still unreviewed; `--check` exits 1 if there are any (run it before a commit). Its `classify` is the reference for the corpus export. |
| `test_disclosure.py` | Its tests. |
| `voice_lint.py` | Checks each testimony against its teller's voice sheet: vocabulary the teller never says, and places outside their range. |
| `voice_stale.py` | Reports accounts that claim to describe the present but whose surrounding canon has moved since. Reads the present year from the `chronology` block. |
| `test_voice.py` | Their tests. |
| `lore_export.py` | Step 14: builds the **Lore corpus** — one chunk per paragraph, layer-split history events, derived audience, wikilink subjects — and prints the calibration report. `--json PATH` writes every chunk record. See the kit's `meta/conventions/conventions.md` §7.5. |
| `test_lore_export.py` | Its tests: chunking, the layer split, the audience rules, tier and race resolution, wikilink subjects. |
| `transform.mjs` | Codex → Game Ready Repository. Deterministic. |
| `validate-world.mjs` | Validates a generated Game Ready Repository with `@mythical-forge/authored-content`. |
| `thread-check.mjs` | Flag registry (declared, set, read), own-stage guards, references inside Conditions and Effects, thread interface. |
| `codex-threads.yaml` (generated) | Written by `transform.mjs`: each thread's members and interface. Tooling only; not an entity. |
| `simulate-world.mjs` | The idle-world and scenario simulator; generates fast-forward start states; reports coverage. |
| `verify-world.sh` | **A world's pipeline proof.** Copies the vault to a throwaway directory and runs the whole pipeline on the world's **own** content: lint → disclosure → transform → validate → thread-check → voice → every scenario in `vault.scenarios`. **It overlays nothing.** It used to overlay a copy of the kit's teaching example, which meant every world carried a duplicate of a fixture it did not own — and a broken toolchain looked exactly like broken lore. The division now: `verify-kit.sh` (in the kit) proves the **toolchain** against the demo world; this proves the **world**. |
| `site_export.py` | Exports the **player-facing site content** from the `open` part of every section (see the kit's `meta/conventions/site.md`). Imports `disclosure.classify`; never re-derives it. Emits `site.json` so the Astro build gets the world's branding. |
| `test_site_export.py` | Its tests: one per redaction rule. |
| `site_link_check.py` | Fails the build on any internal link to a file that does not exist. |
| `site_audit_report.py` | Prints the publish audit into a CI run summary; `--strict` gates the build. |
| `sync-tooling.sh` | **A world's updater.** Fetches a release tag of the worldkit and replaces this repo's `tools/` (except `tools/local/`), the kit's documents into `meta/conventions/`, the templates and the theme. It is the one command that moves a world's `TOOLING_VERSION` pin, and its diff is the whole review surface. |
| `check-guide.mjs` | Checks every `yaml` block in the campaign authoring guide against the engine's schema. The guide is a kit document, so its path is **resolved**, not hardcoded: `template/meta/conventions/` in the kit, a world's `meta/conventions/`, or an argument. |
| `sync-agent-protocol.py` | Writes the kit's `meta/conventions/agent-protocol.md` into `AGENTS.md`, between the marked region. `--check` fails on drift and is what CI runs. A world's `AGENTS.md` is its own brief plus this region; the protocol is duplicated on purpose, because an agent may never follow a link out of the repository, and the duplication is kept honest by this tool. |
| `atlas_yaml.py` | Reads and validates `maps/atlas-features.yaml` (the reader is `yaml_subset.py`; this owns the atlas schema). |
| `atlas_tables.py` | Renders `maps/atlas-features.md` from the YAML; `--check` fails if it is stale. |
| `atlas_diff.py` | Compares the YAML with `HEAD` or a file; reports added, removed, moved and changed features. |
| `atlas_previews.sh` | Renders the PNG previews (macOS + Chrome). |
| `local/make_atlas.py` | Renders the SVG sheets. **World-owned** (D16): label placement, the frame layout and the map title are world choices, so it lives in `tools/local/` and `sync-tooling.sh` never touches it. |

## Atlas tools

The mechanism, the data schema and the recipes are the kit's `meta/conventions/atlas.md`; a world's own frame,
sheets and drawing rules are that world's business. Short version:

```
python3 tools/atlas_yaml.py maps/atlas-features.yaml   # validate
python3 tools/atlas_tables.py                          # maps/atlas-features.md
python3 tools/local/make_atlas.py                      # maps/svg/*.svg (the world's renderer)
python3 tools/atlas_diff.py                            # what changed
tools/atlas_previews.sh                                # PNG previews
```

A world may wire those four commands into one prompt or script; the kit does not, because
what to re-read and what to reconcile is the world's.

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

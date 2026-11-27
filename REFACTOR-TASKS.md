# Refactor: single-source the template & the example world

> **TEMPORARY WORKING DOCUMENT.** This is the checkpoint for the refactor session. It is not part
> of the kit and must be deleted once the refactor lands. Update the checkboxes as steps complete,
> so a compacted session can resume from the first unchecked box.

## Status

- [x] D1 — demo-world config placement: **option A** (`template/example-world/world.config.yaml`)
- [x] S1 — rename `site/` → `site-theme/`
- [x] S2 — bring the template skeleton into `template/`
- [x] S3 — move the demo world into `template/example-world/`
- [x] S4 — rewire `verify-kit.sh`, `testkit.py`, config readers, CI
- [x] S5 — remove the `template: true` special-case from `sync-tooling.sh`
- [ ] S6 — single vendoring manifest (K15) — **DEFERRED to a follow-up** (orthogonal cleanup of sync↔drift-check; not needed for the export)
- [x] S7 — `export-template.sh` (manual; the branch/commit/merge is a release step, not scripted)
- [ ] S8 — K2 de-brand the fixture — **DEFERRED**: ~145 references across docs, tools, tests and the whole fixture (incl. the six scenarios); needs its own PR, not a fold-in
- [x] S9 — docs (README/AGENTS/CONTRIBUTING/ROADMAP/CHANGELOG + TOOLING_VERSION v3.0.0) — done; the first real export (branch → commit → merge → tag the template repo) is a merge-time step

---

## Goal

One repository (`mythical-forge-worldkit`) is the source of truth for **everything** a template or a
world receives: the tools, the rules, the theme, **and** the template's own skeleton + docs + demo
world. The `mythical-forge-world-template` repo becomes a *generated artifact*: it is never edited by
hand; it is updated only by exporting from this repo onto a branch, committing, and merging at
milestones.

The toolkit *distribution* (tarball/package) is **out of scope** here — a separate follow-up.

---

## Decisions locked (from the interview)

1. **Template repo is mechanically updated** from an export in this repo. No hand edits to it.
2. **`site/` → `site-theme/`** in the kit. On export (and on world sync), `site-theme/` is written
   into the destination as **`site/`** — the theme's source directory in the kit is renamed, the
   vendored path in a world/template is unchanged.
3. **Export is a manual script**, run at defined milestones — not on every commit.
4. **Keep the template repo's history.** Future updates are branch → commit → merge → tag.
5. **Toolkit artifact**: separate follow-up; a tarball is acceptable.
6. **Remove the `template: true` special-case from `sync-tooling.sh`.** The example-world mirroring
   moves into the export. (Whether the `template: true` config *key* survives as an inert marker for
   `init-world.sh` / `check_workflows.py` is a detail to settle in S5 — leaning keep-the-key,
   remove-the-sync-behaviour.)
7. **Fold in K2** (de-brand `Dustport` / `Saltmarch` / `Vigil`) as its own commit, drop it if it
   explodes.
8. **`template/` is what the kit verifies.** Copy it to a temp dir. The demo world is **embedded** at
   `template/example-world/` (that is where it sits in the generated template repo).
9. **Single vendoring manifest** (K15) shared by sync and export.

---

## Open decisions (need the owner)

- **D1 — where the demo world's `world.config.yaml` lives.** The demo (Ferryman's Debt) is a
  *separate world* from the template: it has its own `world.id` (`world_ferry_demo`), its own
  `vault.notes`, `vault.scenarios: campaigns/ferryman-demo/scenarios`, and its own six scenarios.
  The six-scenario proof (`verify-kit.sh`) cannot run without that config. Two options:

  - **A (recommended):** `template/example-world/world.config.yaml`. Self-contained, matches the
    template repo today, deleted wholesale by `init-world.sh`, zero overlay hacks in the proof.
    "No config in example-world" is the only instruction this contradicts.
  - **B:** `example-world/` stays config-free; the demo's config is a kit test fixture
    (`tools/fixtures/demo-world/world.config.yaml` or `template/example-world.config.yaml`, excluded
    from export). `verify-kit.sh` overlays it into the temp demo world before running the pipeline.
    Honours "no config in example-world" literally, but splits the demo's identity from its lore.

---

## Target layout (this repo, after)

```
mythical-forge-worldkit/
  README.md  AGENTS.md  CONTRIBUTING.md  CHANGELOG.md  ROADMAP.md   # the KIT's own docs (unchanged)
  TOOLING_VERSION  LICENSE  LICENSE-CONTENT
  .npmrc  package.json          # the kit's own schema dependency (unchanged)
  docs/                         # the rules (unchanged)
  meta/
    templates/                  # note templates (kit-owned)
    platform-requests/          # platform specs (kit-owned)
    # NOTE: the demo's meta notes move OUT of here (into template/example-world/meta/)
  tools/                        # scripts + tests (unchanged)
  site-theme/                   # THEME (was site/); exported/synced into destinations as site/
  .pi/prompts/                  # agent prompts (kit-owned)
  .github/workflows/            # kit CI + the three shipped to worlds
  template/                     # == the generated template repo, in source form
    world.config.yaml           # template: true + REPLACE_ME
    init-world.sh
    README.md  AGENTS.md  ROADMAP.md        # the WORLD brief / template docs (not the kit's)
    package.json  .gitignore  LICENSE        # template-owned root files
    principles/  world/  maps/  campaigns/   # skeleton vault
    meta/                         # skeleton meta notes (canon-digest, names, world-conventions, …)
    example-world/                # THE DEMO WORLD (embedded, as it will sit in the template repo)
      world/  campaigns/  meta/   # demo lore + demo meta notes (calendar, timeline, site-decisions, …)
      world.config.yaml           # ONLY IF option A (see D1)
  verify-kit.sh                 # copies template/ → temp; fresh-fork checks + six-scenario demo proof
  export-template.sh            # assembles the template repo from template/ + vendored kit
```

Notes:

- Two `README.md` and two `AGENTS.md` in the repo is **correct**: the kit root ones are the kit's
  brief; the `template/` ones are the world brief an author forks. They are different documents.
- The demo's meta notes currently at kit-root `meta/` (`_index.md`, `calendar.md`, `site-decisions.md`,
  `timeline.md`, `campaign-authoring-guide.md`) move to `template/example-world/meta/`. The kit's
  `meta/` then holds only `templates/` and `platform-requests/`.

## Target layout (template repo, generated — for reference)

```
mythical-forge-world-template/
  <everything under template/ above, as-is>
  tools/            tools/docs/          # vendored from the kit
  meta/templates/                        # vendored (mirrored)
  site/                                  # vendored from kit's site-theme/
  .pi/prompts/     .github/workflows/    # vendored
  TOOLING_VERSION                        # the kit tag
  example-world/                         # the demo, embedded (as in template/)
```

`export-template.sh` produces exactly this from `template/` + `tools/` + `docs/` + `meta/templates/` +
`site-theme/` + `.pi/prompts/` + the world-shipped workflows + licences.

---

## Steps

Each step is one commit, verified before it lands. Keep `./verify-kit.sh` green (local, with schemas)
and `python3 -m unittest discover -s tools -p 'test_*.py'` green throughout.

### S1 — rename `site/` → `site-theme/`

- `git mv site site-theme`.
- Update every reference to the *source* path, keeping the *destination* path `site/`:
  - `tools/sync-tooling.sh` (the `$TMP/kit/site` rsync source)
  - `.github/workflows/*.yml` paths
  - `docs/site.md`, `docs/*.md` that mention the kit's `site/`
  - `verify-kit.sh`, `tools/verify-world.sh`, any tool that reads `site/`
- **Done when:** `./verify-kit.sh` green and a grep for a stale `site/` source reference finds none.

### S2 — bring the template skeleton into `template/`

- Create `template/` and copy the authored content from the current
  `mythical-forge-world-template/main` (do **not** delete it there yet):
  `init-world.sh`, `README.md`, `AGENTS.md` (brief), `ROADMAP.md`, `world.config.yaml`,
  `package.json`, `.gitignore`, `LICENSE`, `principles/`, `world/`, `maps/`, `campaigns/_seeds/`,
  and the skeleton `meta/` notes.
- Do **not** copy `tools/`, `tools/docs/`, `meta/templates/`, `site/`, `.pi/prompts/`,
  `.github/workflows/`, or `example-world/` — those are vendored/exported, not authored.
- **Done when:** the files exist under `template/` and nothing is wired to them yet (kit still green).

### S3 — move the demo world into `template/example-world/`

- `git mv world template/example-world/world`
- `git mv campaigns template/example-world/campaigns`
- Move the demo meta notes from kit `meta/` → `template/example-world/meta/`
  (`_index.md`, `calendar.md`, `site-decisions.md`, `timeline.md`, `campaign-authoring-guide.md`).
- Move the demo config per **D1** (recommended: `template/example-world/world.config.yaml`).
- Remove the now-empty kit-root `world/`, `campaigns/`, and root `world.config.yaml`.
- **Done when:** the kit root has no world content, and `template/example-world/` holds the complete
  demo world.

### S4 — rewire `verify-kit.sh`, `testkit.py`, config readers, CI

- `verify-kit.sh`: copy `template/` → temp (not the kit root). Symlink the kit's `node_modules` for
  the schema package. Two phases:
  1. fresh-fork checks against the temp template (lint, citations, workflows, `init-world.sh`, site
     build — the current `template-fork.yml` checks);
  2. six-scenario demo proof: `cd temp/example-world` and run the full pipeline against the demo.
- `tools/testkit.py`: point the fixture config at the demo world (per D1).
- `tools/kit_config.py` / `kit_config.mjs`: the `load()`/`configPath()` default still works for
  vendored worlds; verify the kit's own invocations pass `WORLD_CONFIG` or `cd` into the right dir.
- `ci.yml`: lint against `template/` (via `WORLD_CONFIG=template/world.config.yaml`), not the kit root.
- `template-fork.yml`: generate the template with the export script, then fork → `init-world.sh` → prove.
- **Done when:** `./verify-kit.sh` green end to end from the new layout; CI's lint target updated.

### S5 — remove the `template: true` special-case from `sync-tooling.sh`

- Delete the block that mirrors `world/` + `campaigns/` + part of `meta/` + `world.config.yaml` into
  `example-world/`. The export script owns that now.
- Decide the fate of the `template: true` config key (leaning: keep as an inert marker).
- **Done when:** a world's sync no longer writes `example-world/`; `tools/test_sync_reexec.py` and
  friends still green.

### S6 — single vendoring manifest (K15)

- Extract the list of "what the kit vendors, and where" into one manifest file consumed by both
  `sync-tooling.sh` and `export-template.sh` (fixes the three-list drift).
- **Done when:** changing the manifest changes both paths; the drift check compares against the
  manifest's output.

### S7 — `export-template.sh` + manual release wrapper

- `export-template.sh <tag|HEAD> <dest-dir>` assembles the complete template repo:
  `template/` + `tools/` + `docs/→tools/docs/` + `meta/templates/` + `site-theme/→site/` +
  `.pi/prompts/` + world workflows + licences + `TOOLING_VERSION`.
- A wrapper: clone the template repo, `checkout -b worldkit-<tag>`, export, commit, push, open a PR.
- **Done when:** the generated template repo is byte-equivalent (modulo intended changes) to the
  current hand-maintained one; a fresh fork passes the S4 fresh-fork checks.

### S8 — K2 de-brand the fixture

- Rename `Dustport`, `Saltmarch`, `Vigil` in `template/example-world/` to the demo's own names;
  remove the stub notes they force. Keep as its own commit.
- **Done when:** the demo carries no name from another world, and `./verify-kit.sh` is green.

### S9 — docs, release, first export

- Update `README.md`, `AGENTS.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `ROADMAP.md` for the new layout
  and process (kit root no longer a world; template is generated; export is the release step).
- Bump `TOOLING_VERSION` + `CHANGELOG.md` migration note per the sync contract.
- First real export at the milestone: branch → commit → merge → tag the template repo.
- **Done when:** the template repo's newest commit is export-generated, and CI is green in both repos.

---

## How to resume after compaction

1. Read this file's Status section and `AGENTS.md`.
2. Start at the first unchecked step; do not redo checked steps unless a check is ambiguous.
3. Keep `./verify-kit.sh` and the Python suites green after every step, and commit each step alone.

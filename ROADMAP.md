# Worldkit Roadmap

**What this is.** The kit's own work plan. It starts as the second half of the extraction that lifted
the tooling out of the first world (`hollowfall-codex`), and continues as ordinary kit maintenance.
The kit's *users* are worlds; a world's own plan lives in its own `ROADMAP.md`.

**Read first:** `AGENTS.md`, `README.md`, `docs/conventions.md` §16 (the linter's codes).

## 0. Status

| | |
|---|---|
| Version | `1.0.0` (`TOOLING_VERSION`) |
| Origin | extracted from `hollowfall-codex`, 2026. D1–D36 of that repository's `ROADMAP-EXTRACTION.md` are the decisions; they were made there and are not repeated here |
| The proof | `./verify-kit.sh` — lint → transform → validate → thread-check → six scenarios, in a throwaway directory |
| The fixture | the **Ferryman's Debt**: `world/` and `campaigns/ferryman-demo/`. One copy only — it used to sit beside the templates as well, and two copies of a fixture drift |
| Known debt | the fixture's place names are borrowed from the first world (K2), which is why CI greps for that world's names. CI cannot run `verify-kit.sh` (the platform repository is private), so the end-to-end proof is a local step before a tag |

## 1. The plan

Ordered. Each task is one commit, verified before it lands (see `CONTRIBUTING.md`).

| # | Task | Kind | Status | Done when |
|---|---|---|---|---|
| **K1** | Decide the licence | Decision | **Done** (v1.2.0) — MIT for the tools, the theme and the scripts; CC BY 4.0 for the prose; the sync carries both into a world's `tools/`, because MIT requires its notice to travel with the copy | `LICENSE` and `LICENSE-CONTENT` exist, the README names them, and `tools/LICENSE` arrives at the next sync | - |
| **K2** | **De-brand the fixture.** Its places are the first world's: `Dustport`, `Saltmarch`, `Vigil`. Rename them to the demo world's own, and remove the three stub place notes they force (`world/places/`, `world/peoples/humans.md`) | Coding | **Not started** | the demo world carries no name that comes from another world, and `verify-kit.sh` is still green |
| **K3** | ~~**Move the templates in.**~~ `meta/templates/` is already here; **Done.** The 15 templates are here, and the demo world is the single copy of the fixture: it used to sit beside the templates too, and two copies of a fixture drift | Coding | **Done** | — |
| **K4** | ~~**`verify-kit.sh` and the fixture.**~~ Generalise the last of the extraction's `verify-example.sh` (now `tools/verify-world.sh`): **Done.** It builds the demo world from this repository alone and runs the whole pipeline on it | Coding | **Done** | — |
| **K5** | **Versioning and the sync contract.** ~~Exists and exercised once.~~ **Done** — the first world vendored its `tools/`, `tools/docs/` and templates from the tag, and now differs from the kit only by `tools/local/` (its own scripts) and `tools/docs/` (the vendored rules). What it found: the script shipped non-executable, and a vendored test hardcoded the kit's layout | Coding | **Done** | — |
| **K10** | **The sync's safety rails** (`docs/extraction.md`'s third testing gap (its section 3.4)): refuse a dirty working tree, preview deletions before applying them, and offer `--dry-run`. `rsync --delete` on `tools/` silently removes a world's script that is not in `tools/local/` | Coding | **Done** (v1.1.0, and the rails then found three bugs in themselves: v1.1.1 the sync was deleting a world's `tools/docs/` on every run, v1.1.2 it refused every published world over the site's generated directories) | a sync on a dirty tree refuses; a deletion is shown before it happens — refuses a dirty tree (in the paths it replaces only: `tools/local/` is the world's), previews deletions by re-running in dry-run mode and refuses when there are any, and adds `--dry-run` |
| **K6** | **The site theme as a kit asset.** Move `site/src/**`, `astro.config.mjs`, `package.json`, the deploy script and `image-prompts/_style.md`; strip the first world's branding into the config. **The theme stays in one directory behind the config seam**, so a world can replace it | Coding | **Not started** | a world whose only file is `world.config.yaml` plus content builds the site |
| **K7** | ~~**The remaining doc splits.**~~ **Done**, plus `docs/atlas.md` (D38): `site.md` (keeping its section numbers, because worlds cite them), `thread-pattern.md`, `testimony.md`, `tag-vocabulary.md`. Each was extracted from the first world's note by line range and then de-branded, so the world kept only its own decisions and a pointer | Coding | **Done** | — |
| **K8** | **The world template.** A separate repository: the folder skeleton, the quickstart, `init-world.sh`. Its `AGENTS.md` is the third of the three (D36): a world's brief, with the protocol synced in | Coding | **Not started** | a fork runs the whole pipeline and the site build with **zero code edits** |
| **K9** | **A `new-world` CLI.** `npx`-style scaffolding, or `init-world.sh` grown up: ask the questions, write the config, set up the deploy variables, offer to remove the demo world | Decision then coding | **Blocked on K1** | — (open: does the kit ship one at all?) |

## 2. Open items

- [K11] **A prose reference to a file that does not exist is checked by nothing.** `tools/check_citations.py`
  covers section *numbers*; the audit that found seven dangling path references (an agent prompt full
  of one world's creature rules, a tool name renamed two releases earlier, a config file that never
  existed) was a throwaway script. Making it permanent means encoding the categories by hand:
  generated artefacts, world-owned paths, illustrative names, forward references.
- [K12] **The codex index's tag line is chrome that wants the world's voice.** It names the tag index
  and used to read, in the first world, "18 themes, from the Choir to the waygates" — which a theme
  cannot know. `site/src/pages/codex/index.astro` is synced, so a world can flavour every page but
  this one. Either a config string or a fourth world-owned page.
- [K13] **A fork's Open Graph image is missing.** `site/public/` ships a deliberately plain favicon;
  `og-default.jpg` and the hero are a world's own, so a fresh fork's social card is empty until it
  makes one. Harmless, permanent, and worth a line in the template's quickstart.
- [K14] **The strongest proof is still the most manual one.** `verify-kit.sh` and the template fork
  both need `MYTHICAL_FORGE_ROOT`, so the engine pipeline is proved locally before a tag and never in
  CI. `docs/extraction.md`'s first testing gap proposes the fix: a stub `packages/authored-content`,
  because the schemas are the contract and the engine is not.


- [OPEN] **Licence** (K1). The rule is intended to be permissive for a world that publishes its own
  codex; tooling and documentation may want different terms from the demo world's prose.
- [OPEN] **Is this repository public?** If it is, the fixture's prose is published with it and K2
  becomes urgent rather than tidy. The same question applies to the template (K8).
- [OPEN] **Does the theme ship the first world's visual direction as its default, or a neutral theme
  with that as an example?** (K6.) A neutral default with a documented example is the safer answer:
  a world that inherits another world's look is a world that looks like a copy.
- [OPEN] **Does the kit ship a `new-world` CLI at all?** (K9.) The counter-argument is that a
  template plus `init-world.sh` is enough, and a CLI is a second thing to maintain.
- [OPEN] **How does the agent protocol reach a world?** Settled as a synced region of `AGENTS.md`
  (`tools/sync-agent-protocol.py`, D36). Re-open only if a world's `AGENTS.md` turns out to be
  generated by something else.

## Links

- `AGENTS.md` — the brief for working here
- `CONTRIBUTING.md` — how to add a tool, change a rule, or cut a release
- `docs/conventions.md` — the rules a world follows
- `docs/engine-capability-register.md` — the platform requests, and where a release lands

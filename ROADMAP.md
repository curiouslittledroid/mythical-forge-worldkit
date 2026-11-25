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
| **K1** | Decide the licence | Decision | **Not started** | `LICENSE` exists and the README names it |
| **K2** | **De-brand the fixture.** Its places are the first world's: `Dustport`, `Saltmarch`, `Vigil`. Rename them to the demo world's own, and remove the three stub place notes they force (`world/places/`, `world/peoples/humans.md`) | Coding | **Not started** | `grep -ri hollowfall .` and the CI "no world literals" step are clean, and `verify-kit.sh` is still green |
| **K3** | ~~**Move the templates in.**~~ `meta/templates/` is already here; **Done.** The 15 templates are here, and the demo world is the single copy of the fixture: it used to sit beside the templates too, and two copies of a fixture drift | Coding | **Done** | — |
| **K4** | ~~**`verify-kit.sh` and the fixture.**~~ Generalise the last of the extraction's `verify-example.sh`: **Done.** It builds the demo world from this repository alone and runs the whole pipeline on it | Coding | **Done** | — |
| **K5** | **Versioning and the sync contract.** `tools/sync-tooling.sh` exists; `TOOLING_VERSION` is `1.0.0`, tagged `v1.0.0`. What remains is to **exercise it once**: sync the first world from the tag and read the diff | Coding | **In progress** | one command and one reviewable diff move a world between tags |
| **K6** | **The site theme as a kit asset.** Move `site/src/**`, `astro.config.mjs`, `package.json`, the deploy script and `image-prompts/_style.md`; strip the first world's branding into the config. **The theme stays in one directory behind the config seam**, so a world can replace it | Coding | **Not started** | a world whose only file is `world.config.yaml` plus content builds the site |
| **K7** | **The remaining doc splits.** `docs/site.md` (the publish axis, redaction, the audit, stack); `docs/thread-pattern.md` (why a thread is a state graph); `docs/testimony.md` and `docs/tag-vocabulary.md` (the mechanisms) | Coding | **Not started** | no rule is stated twice, and the first world holds only its own decisions |
| **K8** | **The world template.** A separate repository: the folder skeleton, the quickstart, `init-world.sh`. Its `AGENTS.md` is the third of the three (D36): a world's brief, with the protocol synced in | Coding | **Not started** | a fork runs the whole pipeline and the site build with **zero code edits** |
| **K9** | **A `new-world` CLI.** `npx`-style scaffolding, or `init-world.sh` grown up: ask the questions, write the config, set up the deploy variables, offer to remove the demo world | Decision then coding | **Blocked on K1** | — (open: does the kit ship one at all?) |

## 2. Open items

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

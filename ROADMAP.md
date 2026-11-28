# Worldkit Roadmap

**What this is.** The kit's own work plan. It starts as the second half of the extraction that lifted
the tooling out of the first world (`hollowfall-codex`), and continues as ordinary kit maintenance.
The kit's *users* are worlds; a world's own plan lives in its own `ROADMAP.md`.

**Read first:** `AGENTS.md`, `README.md`, `meta/conventions/conventions.md` §16 (the linter's codes).

## 0. Status

| | |
|---|---|
| Version | `3.3.0` (`TOOLING_VERSION`) |
| Origin | extracted from `hollowfall-codex`, 2026. D1–D36 of that repository's `ROADMAP-EXTRACTION.md` are the decisions; they were made there and are not repeated here |
| The proof | `./verify-kit.sh` — lint → transform → validate → thread-check → six scenarios, in a throwaway directory |
| The fixture | the **Ferryman's Debt**: `template/example-world/`. One copy only — it used to sit beside the templates as well, and two copies of a fixture drift |
| Known debt | the fixture's place names are borrowed from the first world (K2), which is why CI greps for that world's names. CI cannot run `verify-kit.sh` (the platform repository is private), so the end-to-end proof is a local step before a tag. The sync, the drift check and `export-template.sh` each keep their own list of what is vendored (K15) |

## 1. The plan

Ordered. Each task is one commit, verified before it lands (see `CONTRIBUTING.md`).

| # | Task | Kind | Status | Done when |
|---|---|---|---|---|
| **K1** | Decide the licence | Decision | **Done** (v1.2.0) — MIT for the tools, the theme and the scripts; CC BY 4.0 for the prose; the sync carries both into a world's `tools/`, because MIT requires its notice to travel with the copy. **The reasoning is `licensing.md`, world-facing at `template/meta/conventions/licensing.md`** | `LICENSE` and `LICENSE-CONTENT` exist, the README names them, and `tools/LICENSE` arrives at the next sync | - |
| **K2** | **De-brand the fixture.** Its places are the first world's: `Dustport`, `Saltmarch`, `Vigil`. Rename them to the demo world's own, and remove the three stub place notes they force (`world/places/`, `world/peoples/humans.md`) | Coding | **Not started** | the demo world carries no name that comes from another world, and `verify-kit.sh` is still green |
| **K3** | ~~**Move the templates in.**~~ `meta/templates/` is already here; **Done.** The 15 templates are here, and the demo world is the single copy of the fixture: it used to sit beside the templates too, and two copies of a fixture drift | Coding | **Done** | — |
| **K4** | ~~**`verify-kit.sh` and the fixture.**~~ Generalise the last of the extraction's `verify-example.sh` (now `tools/verify-world.sh`): **Done.** It builds the demo world from this repository alone and runs the whole pipeline on it | Coding | **Done** | — |
| **K5** | **Versioning and the sync contract.** ~~Exists and exercised once.~~ **Done** — the first world vendored its `tools/` and templates from the tag, and now differs from the kit only by `tools/local/` (its own scripts) and the kit documents it holds (then `tools/docs/`, now `meta/conventions/`). What it found: the script shipped non-executable, and a vendored test hardcoded the kit's layout | Coding | **Done** | — |
| **K10** | **The sync's safety rails** (`docs/extraction.md`'s third testing gap (its section 3.4)): refuse a dirty working tree, preview deletions before applying them, and offer `--dry-run`. `rsync --delete` on `tools/` silently removes a world's script that is not in `tools/local/` | Coding | **Done** (v1.1.0, and the rails then found three bugs in themselves: v1.1.1 the sync was deleting a world's `tools/docs/` on every run, v1.1.2 it refused every published world over the site's generated directories) | a sync on a dirty tree refuses; a deletion is shown before it happens — refuses a dirty tree (in the paths it replaces only: `tools/local/` is the world's), previews deletions by re-running in dry-run mode and refuses when there are any, and adds `--dry-run` |
| **K6** | **The site theme as a kit asset.** Done by K16: the theme is `site-theme/` in the kit, vendored into a world as `site/`, stripped of any world's branding behind the config seam, and its two image-prompt files (`README.md`, `_style.md`) travel with it | Coding | **Done** (v3.0.0) | a world whose only file is `world.config.yaml` plus content builds the site — proved by `template-fork.yml`'s site build |
| **K7** | ~~**The remaining doc splits.**~~ **Done**, plus `meta/conventions/atlas.md` (D38): `site.md` (keeping its section numbers, because worlds cite them), `thread-pattern.md`, `testimony.md`, `tag-vocabulary.md`. Each was extracted from the first world's note by line range and then de-branded, so the world kept only its own decisions and a pointer | Coding | **Done** | — |
| **K8** | **The world template.** Generated, not hand-edited: the kit's `template/` is the source, `export-template.sh` assembles the published repo (skeleton + vendored kit + embedded `example-world/`). Its `AGENTS.md` is the third of the three (D36): a world's brief, with the protocol synced in. **Every CI run exports the template and forks it** | Coding | **Done** (v3.0.0) | a fork runs the whole pipeline and the site build with **zero code edits**, and a fresh fork lints with 0 errors |
| **K16** | **One source of truth: the kit owns the example world and the template.** The demo world moved to `template/example-world/`; the template skeleton, the note templates (`template/meta/templates/`), the world-facing documents (`template/meta/conventions/`) and the agent prompts (`template/.pi/prompts/`) moved in beside it; `docs/` keeps only kit maintenance (`extraction.md`); `site/` became `site-theme/`; and the `template: true` switch was removed — the sync no longer mirrors anything into a template, because the template is an export. What this found: the export dropped the theme's three neutral pages, `_style.md` never shipped, the register linked the first world's notes, and a fresh fork carried a stray `meta/flags.md` that failed FN002 | Coding | **Done** (v3.0.0) | `./export-template.sh` produces a template whose fresh fork lints with 0 errors and builds its site; `verify-kit.sh` is green |
| **K17** | **Config coherence is a check, not a suite assertion** (`docs/extraction.md` §3.2: "removed the only assertions that a config is coherent with its vault"). `tools/check_config.py` asks the questions of *this* world's config — every `vault.notes` id resolves to a note carrying its block, the blocks are shaped right, no two site sections claim a kind, a published tag is in the vocabulary, a note kind nobody publishes is named, and the two readers agree on this config — and it answers in the author's terms, with `REPLACE` values as notes and errors as the only failure. It runs first in `verify-world.sh`, in `checks.yml`, on a fresh fork and in `verify-kit.sh`. What it found: the template's `flags` block is `[]`, which **both** readers refused, so `kit_config.py`, `kit_config.mjs` and every suite that loads the live config failed in a fresh fork | Coding | **Done** (v3.3.0) | a coherent world is silent, every fixture that breaks one thing is named, and `check_config.py` exits 0 on the template with only `REPLACE` notes |
| **K9** | **A `new-world` CLI.** `npx`-style scaffolding, or `init-world.sh` grown up: ask the questions, write the config, set up the deploy variables, offer to restore the demo world | Decision then coding | **Blocked on K1** | — (open: does the kit ship one at all?) |

## 2. Open items

- [K11] **A prose reference to a file that does not exist is checked by nothing.** `tools/check_citations.py`
  covers section *numbers*; the audit that found seven dangling path references (an agent prompt full
  of one world's creature rules, a tool name renamed two releases earlier, a config file that never
  existed) was a throwaway script. Making it permanent means encoding the categories by hand:
  generated artefacts, world-owned paths, illustrative names, forward references.
- [K15] **The sync's file list is duplicated in three places, and they drift.** The sync's `tools/`
  rsync excludes what the kit keeps at its root (`docs/`, `LICENSE`, `LICENSE-CONTENT`), the drift
  check repeats those exclusions, and the sync then copies those files beside them. Four bugs have
  come from one of the three lists being out of step. A better shape: have the drift check ask the
  sync what it would write (`--dry-run` already prints every change) and compare the world against
  that, so there is one list.
- [K12] **The codex index's tag line is chrome that wants the world's voice.** It names the tag index
  and used to read, in the first world, "18 themes, from the Choir to the waygates" — which a theme
  cannot know. `site/src/pages/codex/index.astro` is synced, so a world can flavour every page but
  this one. Either a config string or a fourth world-owned page.
- [K13] **A fork's Open Graph image is missing.** `site/public/` ships a deliberately plain favicon;
  `og-default.jpg` and the hero are a world's own, so a fresh fork's social card is empty until it
  makes one. Harmless, permanent, and worth a line in the template's quickstart.


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
- `meta/conventions/conventions.md` — the rules a world follows
- `meta/platform-requests/engine-capability-register.md` — the platform requests, and where a release lands

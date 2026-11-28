# Running the Tools

**Summary:** The kit ships many scripts, and each answers one question. This page is the map from
**what you just changed** to **what proves it**, plus the order to run them in, what each one writes,
and what it will not catch. The rules a script enforces are the other documents' business; this one
is only about which command to reach for.

## The one rule

Run everything from the repository root. Every command below assumes it, and every tool reads the
world's values from `world.config.yaml` rather than from the path you happen to be in.

If you remember one command, remember this one:

```bash
python3 tools/lint.py
```

It takes a second, it writes nothing, and it is the only check that belongs after **every** note.
Everything else is by **what changed** — not by habit.

## What you just changed → what to run

| You just… | Run | It catches |
|---|---|---|
| wrote or edited a note | `python3 tools/lint.py` (or `… world/places` for one folder) | frontmatter, ids, filenames, dead or ambiguous links, undeclared flags, spelling (conventions §16) |
| changed `world.config.yaml`, or the note a `vault.notes` id names | `python3 tools/check_config.py` | an id nothing has, a block that is missing or shaped wrong, a published tag outside the vocabulary, a note the site would never show, the two config readers disagreeing |
| added or renamed a lore `##` section | `python3 tools/disclosure.py --list`, then `--check` | a section no one has classified. Unclassified fails closed as `earned`, so a leak is silent (conventions §7) |
| renamed or renumbered a document's sections | `python3 tools/check_citations.py` | a `§N` citation that no longer resolves (conventions §16.1) |
| wrote an engine block, or moved an id or a flag | `node tools/transform.mjs`, then `node tools/validate-world.mjs`, then `node tools/thread-check.mjs` | a schema error, a reference to an id that does not exist, a flag nobody sets or reads, a thread whose interface and blocks disagree |
| wrote or edited a scenario | `node tools/simulate-world.mjs <campaign>/scenarios/<name>.yaml`, then `--coverage` | a thread that cannot be finished, cannot be fast-forwarded, or never goes idle |
| wrote testimony | `python3 tools/voice_lint.py` and `python3 tools/voice_stale.py` | a teller using a word or a place outside their voice sheet; an account the canon has moved under |
| moved a feature on the map | `python3 tools/atlas_yaml.py maps/atlas-features.yaml`, `python3 tools/atlas_tables.py`, `python3 tools/atlas_diff.py` | a schema error, a stale generated table, a move nobody meant (see the kit's atlas document) |
| changed a workflow | `python3 tools/check_workflows.py` | a duplicate key, which GitHub refuses — and then the workflow runs under its file path, failing every run |
| changed a YAML block in the authoring guide | `node tools/check-guide.mjs` | a tutorial teaching an engine block the schema rejects |
| want to know what CI will say | the gate below | the same four checks, in the same order |
| updated the worldkit | `tools/sync-tooling.sh <tag>`, then `tools/verify-world.sh` | a diff you did not review, then the whole pipeline on your content |
| changed lore in bulk, or anything in the pipeline | `tools/verify-world.sh` | everything the tools can prove |
| am about to publish the site | the publish order below | a leak, an unread audit, a dead link |

## The everyday loop

1. **After every note:** `python3 tools/lint.py`.
2. **After a lore section:** classify it — `disclosure.py --list` shows what is unreviewed.
3. **After an engine block, an id or a flag:** the three Node commands, in that order. `transform.mjs`
   writes the Game Ready Repository, `validate-world.mjs` reads it back against the engine's schemas,
   and `thread-check.mjs` checks what the schemas cannot: flags, guards, references, interfaces.
4. **After a scenario:** the simulator, for that file first, then `--coverage`.
5. **Stop.** Nothing else is a habit.

Lint does not read engine schemas, canon consistency, or prose quality; conventions §16 says so at
the end of its list. That is why the engine branch exists, and why "lint is clean" is never the last
word on a note with an `engine` block.

## Before a commit: the gate

```bash
python3 tools/check_config.py
python3 tools/lint.py
python3 tools/check_workflows.py
python3 tools/check_citations.py
python3 tools/disclosure.py --check
```

This is `.github/workflows/checks.yml` minus the pipeline. It
runs on every push, so running it locally only moves the failure earlier — which is the point. When
the change completes a roadmap step or touches a flag, an id or a scenario, run
`tools/verify-world.sh` before committing too: the vault's own proof is not in the fast gate.

Three tools have a `--strict`: `lint` and `voice_stale` turn warnings into failures, and
`site_audit_report` fails on the findings that are unambiguously bugs. The CI gate uses none of them,
and neither should a commit: a warning like `REPLACE left in prose` is a to-do, not a defect. Reach
for `--strict` when you want the warnings worked through, not when you want the gate.

The test suites (`tools/test_*.py`) are the kit's tests: fixtures asserting the kit's own code, and
the kit runs every one in its own CI on every commit. **Nothing runs them here**, on purpose. A
release cannot be tagged with one failing, the checks above cover what a suite could have told you
about your world, and a red run you cannot fix teaches you to ignore the tab. They ship because
`tools/` is copied whole, and they are worth running by hand when a *tool* misbehaves rather than a
note — `python3 tools/test_lint.py`, `python3 tools/test_check_config.py`, and so on. A vendored
copy that has drifted from its pin is not a suite's question: `tools/sync-tooling.sh --dry-run`
shows every file that differs, and `tooling-drift.yml` compares them with the tag every Monday.

## Before you publish the site

```bash
npm --prefix site install
npm --prefix site run build          # runs site_export.py, then Astro, then the search index
python3 tools/site_audit_report.py   # read it
python3 tools/site_audit_report.py --strict
python3 tools/site_link_check.py
```

Publishing is manual (`site.yml`, run from Actions): a run builds and stops unless you tick
`publish`. **Read the audit before you tick it** — the build is not the permission, the audit is (the
kit's site document says the same, and `site/audit/latest.json` is committed so the review is in the
history). The publish order above is the local copy of that workflow; the site document is the rules.

## The full proof

`tools/verify-world.sh` copies the vault into a throwaway directory and runs the pipeline on **your**
content:

```
citations → lint → disclosure --check → transform → validate → thread-check
          → voice (reported) → every scenario (or --coverage)
```

It never writes into the vault, and it needs the engine's schemas — one npm dependency,
`@curiouslittledroid/authored-content`, published on GitHub Packages. So the first time you run it,
install that once from the repository root:

```bash
export NODE_AUTH_TOKEN=<a GitHub token with read:packages on @curiouslittledroid>
npm install
```

The repository's `.npmrc` already points npm at that registry and hands it the token above; never
commit a token. A 401 from `npm.pkg.github.com` means it is missing, expired, or lacks
`read:packages`. Without the schemas a tool stops immediately and names these same lines — and note
what does **not** wait on them: lint, citations, disclosure and the site build all run, so a fork
with no token yet can still write and check its lore.

Its exit code gates on citations, lint, disclosure and the scenarios. The transform, validate,
thread-check and voice stages print what they find; read their lines rather than only the last one.

Run it: before a release or a sync, after a bulk edit, when a scenario behaves oddly, and whenever
CI's pipeline step was skipped for lack of a token. `--keep` leaves the temporary directory in place
for inspection; scenario files passed as arguments run those instead of the configured set.

A world with no scenarios yet is not a broken world: the script says so and passes. That changes the
moment the first `campaigns/**/scenarios/*.yaml` exists — then the simulator is expected to run.

## What a tool writes

Everything not listed as writing is read-only, and safe to run to look.

| Tool | Writes |
|---|---|
| `transform.mjs` | the **Game Ready Repository** (`--out`, default `world.game_ready_repo`). Generated; never commit it, never hand-edit it |
| `site_export.py` | `site/src/content/generated/`, `site/src/data/generated/` (both git-ignored), and the committed `site/audit/latest.json` + `history.json` |
| `atlas_tables.py` | `maps/atlas-features.md`. Commit it with the YAML it came from; `--check` writes nothing |
| `atlas_previews.sh` | the PNG previews in `maps/svg/preview/` |
| `sync-tooling.sh` | `tools/` (except `tools/local/`), `meta/conventions/`, `meta/templates/`, `.pi/prompts/`, the theme under `site/`, three workflows, and `TOOLING_VERSION`. `--dry-run` writes nothing |
| `sync-agent-protocol.py` | the marked protocol region of `AGENTS.md`. `--check` writes nothing and exits 1 on drift |
| `lore_export.py` | nothing, unless `--json PATH` names a file |
| `init-world.sh` | the identity values, the licence and (with `--init-git`) the history. Template only, once |

`tools/local/` is the world's own and no kit tool writes there.

## What runs without you

| Workflow | When | What it runs |
|---|---|---|
| `checks.yml` | every push and pull request | the gate above, and — with a `WORLDKIT_PACKAGES_TOKEN` secret — `verify-world.sh` |
| `tooling-drift.yml` | Mondays, and when `TOOLING_VERSION` moves | is the pin behind the kit, and do the vendored files still match it byte for byte? A hand-edit to `tools/` is caught here before the next sync reverts it |
| `site.yml` | manual, from Actions | the site build, the audit gate and the link check; deploys only when asked |

A red drift check is not a broken world: it is a behind or hand-edited pin. The fix is
`tools/sync-tooling.sh <tag>` and one commit, and the job says so.

## When a tool refuses

| Message | What it means |
|---|---|
| the schemas are missing | `@curiouslittledroid/authored-content` is not installed — it lives on GitHub Packages, so it needs a token: `export NODE_AUTH_TOKEN=<read:packages on @curiouslittledroid>`, then `npm install` in the repository root. `.npmrc` already has the registry; the tool prints the same two lines |
| `sync-tooling: refusing to run` | the tree is dirty in files the sync replaces, or the sync would **delete** a file inside a directory the kit owns. Read the list; `--force` is for when the list is right |
| `lint.py` exits 2 | a usage error (a bad path or flag), not a note. Nothing was read |
| `disclosure.py --check` fails on a section you consider fine | the class comes from the first rule that applies (conventions §7); `Hooks`, `Author Notes`, `Open questions`, `Links` and `Engine` are not lore. Fix the heading, or mark the section |
| `check_citations.py` prints a **NOTE** | the document is not in this repository (a kit prompt citing a world's note, say). It is visible, not an error. `citations: ignore` is for what is genuinely uncheckable |
| a workflow passes `check_workflows.py` and GitHub still refuses it | that check looks for duplicate keys only. Everything else about a workflow is GitHub's to validate, on push |
| `check_config.py` prints a **WARN** | consistent, but something declared is missing or something used is undeclared: a process document that is not there, a scenario directory that is not there, a published tag outside `tags-vocabulary`, or a note kind no `site.sections` entry lists (that note is not published). None of it fails the run; fix it or leave it, and lint lists the rest |
| `check_config.py` prints a **NOTE** | the value is still the template's `REPLACE`. It is your to-do list, not a failure — `init-world.sh` filled in the identity, not the vocabularies |
| `check_config.py` says the two readers disagree | `kit_config.py` and `kit_config.mjs` read your config differently. That is a defect in the tooling, not in the config: report it against the kit's pin rather than editing around it, because the two halves of the world would then be built from different answers |
| a tool says the site is switched off | `site_export.py` requires the `site` feature in `world.config.yaml` and refuses rather than guessing. The atlas, testimony and voice tools work from their own files, so an unused feature simply has nothing to read |

## Where the rules live

| Document | For |
|---|---|
| the kit's conventions §16 | every linter code, and what lint deliberately does not check |
| the kit's conventions §7 | disclosure classes, and how a section's class is decided |
| the kit's conventions §16.1 | how to cite a document by section |
| `meta/conventions/site.md` | what may be published, redaction, and the audit |
| `meta/conventions/atlas.md` | the map pipeline's four commands and its data |
| `meta/conventions/campaign-authoring-guide.md` | how to author a thread, a Campaign, its Modules and Quests |
| `meta/conventions/testimony.md` | voice sheets, and why an account goes stale |
| `tools/README.md` | each script in detail: what it reads, what it writes, its flags |
| `ROADMAP.md` | which step you are on, and its **Done when** — the step says which of these prove it |

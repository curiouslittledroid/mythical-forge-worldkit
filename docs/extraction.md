# The Extraction

This is the record of the work that turned **one world's repository into three**: this kit, a forkable
template, and the world repositories that vendor both. It is kept because the decisions in it explain
why the kit looks the way it does — why a world vendors files instead of installing a package, why
`tools/docs/` exists, why a document that keeps its section numbers keeps its name.

Two parts, written at different times and worth reading differently. **Section 2 is the decisions,
written as they were taken.** **Section 3 is the evaluation, written after the kit was built**, and it
is deliberately harder on the recent work: which decisions survived contact, which are weaker than
they read, and which were wrong.

The work itself — sixteen tasks across five phases — lives in the git history of the first world's
repository, which is where the diffs are.

---

## 1. The target shape

```
mythical-forge-worldkit          tooling, generic docs, site theme, note templates, the engine register
        │  vendored into tools/ at a pinned tag, synced by tools/sync-tooling.sh
        ├──► hollowfall-codex     (this repo: lore and world decisions only)
        └──► mythical-forge-world-template ──fork──► <new-world>-codex
```

| Repo | Owns | Never contains |
|---|---|---|
| `mythical-forge-worldkit` | Every script, the generic conventions, the site theme, the note templates, the engine-capability register, the agent protocol | Any world's lore |
| `mythical-forge-world-template` | An empty but valid vault: folders, stubs, `world.config.yaml`, `AGENTS.md`/`ROADMAP.md` skeletons, `init-world.sh` | Hollowfall's answers |
| `<world>-codex` (this repo) | Lore, principles, world decisions, world-specific scripts (`make_atlas.py`), the vendored tooling copy | Tool source of truth |

**Non-goals.** The Game Ready Repository stays a separate generated repo. The engine stays closed
over the SRD (Design 23 §1.1). No world lore is published by any of this.

---

---

## 2. The decisions

| # | Decision |
|---|---|
| **D1** | Three repos, as in Section 1. |
| **D2** | Names prefixed `mythical-forge-`: `mythical-forge-worldkit`, `mythical-forge-world-template`. |
| **D3** | A world consumes the tooling as a **vendored copy at `tools/`**, pinned by `TOOLING_VERSION`, updated by `tools/sync-tooling.sh`. Submodules and published packages are rejected: vendoring keeps every current path and command working, keeps the scripts greppable from Obsidian, works offline, and makes tool updates reviewable diffs. |
| **D4** | The worldkit owns the Astro theme **initially**. A world author must later be able to write their own theme; the theme therefore stays in one directory behind the `world.config.yaml` seam. |
| **D5** | **Doc ownership.** Worldkit: `conventions.md`, `campaign-authoring-guide.md`, `world-events-design.md`, `site.md`, `tag-vocabulary.md`, `meta/templates/`, the agent protocol. World: `canon-digest.md`, `names.md`, `naming-decisions.md`, `open-questions.md`, `pilot-findings.md`, `pilot-thread-findings.md`, `testimony-guide.md`. |
| **D5a** | **`mechanics-gap-register.md` splits.** Worldkit gets the *engine-capability register*: the A–D classification scheme, the closed-vocabulary facts, the **CP-** patterns in force, the live **PR/PF/BD/DT** catalogue, the spec-homes index. The world keeps its **M1–M24** rows, accepted lore reshapes, content fixes and corrections. One home per fact; the world's register links to the catalogue. |
| **D6** | `tools/pilot-gen/` is **deleted** (git history keeps it). The 16 pilot scenarios move to `campaigns/dustport-pilot/scenarios/`; one generic smoke scenario stays in the worldkit. |
| **D6a** | `maps/svg/preview/*.png` **stay tracked** (784 KB, rendered by macOS Chrome at a hardcoded path, so a clone cannot regenerate them; the atlas docs list them as the review surface). |
| **D7** | the worldkit's `the worldkit's meta/platform-requests/` moves to the worldkit for now. It may later be filed in the platform repo; the worldkit is the holding pen. |
| **D8** | The plan lived in the first world's `ROADMAP-EXTRACTION.md`; it is deleted, and this document is
  what it left behind. |
| **D9** | The template ships `ROADMAP.md` as a generic skeleton — the 0a→16 sequence with the model/cost guidance. **Refined in T10:** the worked examples point at `example-world/` (the demo world the template ships and mirrors) rather than at Hollowfall, which the template does not ship; and the step **numbers are the kit's**, because `docs/site.md` cites Step 16 and `docs/thread-pattern.md` cites Step 12. |

### 2.1 The config seam (round 1, agreed)

| # | Decision |
|---|---|
| **D10** | **Two layers.** The root `world.config.yaml` carries repo identity, note ids and feature switches. The world's closed vocabularies that are **lore words** live as fenced blocks inside vault notes, as `flags` and `tags-vocabulary` already do — Obsidian-editable, lint-enforced, versioned with the lore. The config is a non-note root file, like `maps/atlas-features.yaml`. |
| **D11** | **One root file**, with a `site:` section, not a separate `site.config.yaml`: the world's name, slug and description are needed by the site anyway, and splitting them gives identity two homes. The site tools fail with a clear message when the section is absent. |
| **D12** | **Notes are addressed by id, not path** (`flags: topic_world_flags`). Ids never change; paths do, and `disclosure.py:50` already hardcodes `world/flags.md` while `transform.mjs:32` uses the same note's id. |
| **D13** | **Directories are fixed by the kit**, not configurable. Renaming `world/` costs a config field and buys churn across every doc, link, example and both exporters. Only note ids are declared. |
| **D14** | **Feature switches:** `features: [site, atlas, testimony, voice]`. A world with no testimony device never configures `testimony_book`, `date_prefix` or the `## Testimony` heading. |
| **D15** | **Lore words become vault blocks** (`eras`, keystone terms, published tags); **tool plumbing** (feature switches, ids, the reviewed plot-web surfaces) stays in the root config; **atlas frames** stay in `maps/atlas-features.yaml`, which is already world data. |
| **D16** | **The kit owns `tools/`; `sync-tooling.sh` never touches `tools/local/`.** A world's own scripts live there. `make_atlas.py` (979 lines of hardcoded label placement and the map title) moves to it. |
| **D17** | **Delete `thread-check.mjs`'s `LEGACY` shim** — a migration-era set naming four Hollowfall flags. |
| **D18** | **`voice_stale.py` stops guessing the present year from the calendar's prose.** A fenced block in the calendar note carries `present` and `date_prefix`; the prose stays as the human-readable copy. |
| **D19** | **Correction to D5, twice over.** `meta/tag-vocabulary.md` and the world's site decisions are **world** notes: the linter reads the world's 68 tags out of a fenced `tags-vocabulary` block in the first (`TG001`/`TG002`), and every tag names Hollowfall's peoples, powers and places. The worldkit gets the *mechanism* (the `docs/conventions.md` §8.1 block type, the R1–R5 rules, the publish-gate rules); the world keeps the vocabulary and its decisions. |
| **D20** | `conventions.md` §8.1's block table is **already stale** — it omits `tags-vocabulary`, which ships and is enforced. Fix it in T3 while the table is generalised. |

| **D37** | **A world vendors the kit's docs too, at `tools/docs/`.** The rules are part of the tooling: a tool enforces a rule that the world's agent must be able to *read*, and an agent inside a world repository cannot follow a pointer into another repository. The by-name convention (D26/D33) survives — a pointer names the document **and** its vendored path — so all forty `conventions §N` citations stay valid. `sync-tooling.sh` writes them. |
| **D38** | **The kit owns `docs/atlas.md`; a world owns its atlas.** The pipeline, the data schema and the four commands are the kit's; the frame, the sheets, the drawing rules and `tools/local/make_atlas.py` are the world's (D16). Also a rule: **a kit document carries no vault wikilink** — a `[[ ]]` resolves in one repository only. Found by auditing what was actually in the kit: `tools/README.md` had a wikilink to a world's note, and the atlas documentation had never moved at all. |
| **D39** | **One testimony document, not two.** The specification (was `docs/site.md` §3.4–3.5; the numbers travel with it, so those sections are `docs/testimony.md` §3.4–3.5 now) and the procedure (was the world's testimony guide) merge into `docs/testimony.md`. A device documented in two repositories gets two contradictory rule sets. |
| **D40** | **A kit document keeps its section numbers where a world cites them by number.** `docs/site.md` keeps §2–§9; the world's `meta/site.md` keeps §1, §4, §5 and §10–§12 — a *world's* note, which this repository does not hold, so those numbers are history here and not a reference: `citations: ignore`. Same principle as D26, applied per document rather than by a rule about titles. |
| **D41** | **The CI gate asserts a world's *identity* in the kit's machinery, and nothing more.** Scoped to `docs/`, `tools/`, `meta/templates/`, the demo world and the config, for `world_hollowfall` / `hollowfall-` / `Hollowfall`. `README`, `CHANGELOG`, `ROADMAP`, `CONTRIBUTING` and `meta/platform-requests/` are **provenance** — they exist to say where the kit came from and who asked for what — and are excluded by name. The first version of this gate grepped the whole repository for three place names, matched 125 times, and could never have passed. |
| **D42** | **The fixture's borrowed place names are cosmetic debt, not an invariant.** The demo world's `Dustport`, `Saltmarch` and `Vigil` come from the first world. Renaming them is the kit's K2; a grep cannot enforce it, and pretending otherwise is what made D41's first version useless. |

---

---

## 3. Evaluation: which decisions hold, which do not

*Written after the kit was built, not before. Section 2 records what was decided; this section asks
which decisions survived contact with the work, which are weaker than they read, and which were
simply wrong. It is deliberately harder on the recent ones.*

### 3.1 Decisions that hold, and the evidence

| Decision | Why it holds | The evidence |
|---|---|---|
| **D1–D3** three repos; a world vendors `tools/` | The world keeps every existing path, command and Obsidian link; the update is a reviewable diff; nothing is installed | The kit's tools run unchanged in both repositories. The cost is real and is in 9.4: a bespoke sync, not a dependency |
| **D12** notes are addressed by id, not path | The one decision that made everything else possible: a note can move folder without a tool breaking | Every named note in both worlds' configs resolves (`test_the_named_notes_resolve`); no script holds a world path |
| **D10–D11, D14–D15** one root config, feature switches, lore words in vault blocks | Splits *identity* from *lore* along the line that actually differs between worlds | Six scripts became world-agnostic against one file; a world with no site never configures one |
| **D16** `tools/local/` is the world's | A world can add a script without forking the kit | `make_atlas.py` is the case that forced it, and the sync provably skips it |
| **D18** `voice_stale.py` reads a block, not prose | A tool that scrapes prose is a tool that breaks on a rewording | It reads `chronology`; the prose is free to change |
| **D21/D24** two readers, one parity test, a cache keyed on mtime | The Node and Python readers cannot diverge silently | The parity test compares them field by field on the live config; the cache was *found* by a test that rewrote a fixture |
| **D26/D40** the document that keeps the section numbers keeps the name | Roughly forty citations in this vault read `conventions §9.6`. Renumbering buys nothing and breaks all of them | Every `§N` citation still resolves unedited, across three split documents |
| **D28** spelling is a setting; metric is law | Spelling is a house style; the km→miles conversion is an engine fact | `vault.spelling` guards SP001; the transformer still converts once |
| **D34** the top-level contracts are fixed, `world/`'s interior is the world's | A world with no gods should not have a `gods/` folder to explain away | The kit's demo world has no `gods/` and lints clean |
| **D37–D39** the kit owns the rules, the world the lore; the docs are vendored | A tool enforces a rule the world's agent must be able to read; a device documented twice gets two rule sets | `tools/docs/` exists in the sync; testimony is now one document, not two |

### 3.2 Decisions that hold but are weaker than they look

**The test rewrite.** Eight assertions that named this world's values (`world_hollowfall`, its title,
its 18 published tags, the words `archmage`, `Lineage`, `Convenor`) now assert *shape*. That is the
right direction — a test that breaks when someone forks the kit is a test working against the kit's
purpose. But it removed the only assertions that a config is coherent with its vault. The suites
still check that every named note resolves; nothing checks that a world's `site.sections` covers
every kind actually used, or that its published tags are a subset of its vocabulary.

**Byte-identical verification.** T1 and T2 were accepted on "the site audit is byte-identical to the
baseline" plus identical atlas tables and SVGs. That is strong evidence of *no behaviour change* and
weak evidence of *correct behaviour*: it would preserve a bug perfectly.

**"`verify-kit.sh` is green."** It runs on a **36-entity** demo world. That world has one Resolvable
thread, three NPCs, one Campaign, two Modules, no Managed or Ratchet thread, no layered history
event, no `_known_by_groups` resolution, no testimony, no atlas. So the sentence means "the pipeline
runs end to end on the simplest possible world", not "the kit handles what a world actually
contains". The first world's 113-entity run is the stronger test, and it is not part of the kit's CI.

**The demo world is validated as a pipeline input, not as a world.** This is how a real defect
survived: its own Campaign block declared `world_id: world_hollowfall`, copied from this world's
fixture. The schema accepted it, the validator resolved it, all six scenarios passed, and the
generated manifest claimed to belong to another world. Nothing in the kit asked the one question that
would have caught it — *is the manifest's world id the one in the config?*

### 3.3 Decisions that were wrong

| # | What was wrong | Found by | Fixed by |
|---|---|---|---|
| 1 | **The CI gate could not pass.** It grepped the whole repository for `hollowfall\|dustport\|saltmarch` — 125 matches, mostly the demo world's borrowed place names. A gate that can never go green gets disabled, and then nothing is checked | Re-reading the decision, and running the command | D41: scoped to a world's **identity** in the kit's machinery, with the provenance files excluded by name |
| 2 | **A world's identity inside the kit**: the demo world's `world_id`, the `campaign` template, two examples in the authoring guide, the kit's `docs/site.md` §8 (the first world's bucket, distribution and IAM role), and `lint.py` describing itself as linting "the Hollowfall vault" | The same re-reading | Corrected; the gate now holds the identity line |
| 3 | **`sync-agent-protocol.py` was broken by a hand edit** — the region variable was left unreferenced, so it crashed rather than writing the protocol. It was committed in that state, and nothing ran it | Rehearsing the sync into a throwaway world | Fixed, and given a six-case suite: a tool whose job is catching a silent divergence must not fail silently itself |
| 4 | **The kit's own documents carried a vault wikilink** (`tools/README.md` pointed at a world's note), and the atlas documentation never moved at all — the tools shipped with no instructions | An inventory of what was actually in the repository | D38: `docs/atlas.md`, and the rule that a kit document carries no `[[ ]]` |
| 5 | **`verify-kit.sh`'s first version could not prove the kit.** It was a copy of this world's script, which overlays the fixture onto *a world's* vault — so the kit's proof depended on a world it does not have | Running it | Rewritten to build the demo world from the kit alone |

A pattern: 1, 3 and 4 were all found by *re-reading and inventorying*, not by a check. That is the
weakness this evaluation is really about — the extraction added good checks for what it was changing,
and almost none for what it was creating.

### 3.4 Testing: what was verified, and how strongly

| Claim | How it was checked | Strength | What would catch a regression |
|---|---|---|---|
| No world literal left in the tools | `grep -ri hollowfall tools/` plus review of all six couplings | **Good** | The scoped CI gate |
| The config seam changed no behaviour | Byte-identical site audit, atlas tables and 16 SVGs; 6/6 scenarios | **Strong for no-change**, weak for correctness | Semantic field assertions (below) |
| The kit is sound | `verify-kit.sh`: 36 entities, 0 schema errors, 0 dangling, thread-check consistent, 6/6 scenarios | **Weak** (3.2) | A second, deliberately different fixture; `verify-kit.sh` in CI |
| The sync works | One rehearsal into a throwaway copy of this repo; it found two bugs | **Good method, no protection** | A test that runs the sync into a temp world and asserts the file set, the pin and a skipped `tools/local/` |
| The docs are complete | An inventory: four documents referenced but missing | **Weak** | A check that every `docs/*.md` referenced by another kit document exists |
| The tests pass | Six suites, ~225 tests, all green | **Good** | Already covered |
| No world's identity in the kit | The CI gate (broken until today) | **Now adequate** | Already covered |

**The gaps, ranked by what they would cost a world author.**

1. **The end-to-end proof cannot run in CI.** `verify-kit.sh` needs `MYTHICAL_FORGE_ROOT` — the
   platform repository, which is private — because the transformer and the validator *are* the
   engine's code. So the strongest test is a local, pre-tag ritual, and a change that breaks the
   pipeline can be merged and tagged. *Fix:* a CI job against a **stub** `packages/authored-content`
   (the schemas are the contract; a stub that implements `parseAuthoredEntity`, or a published package
   if one exists, is enough to keep the pipeline honest), or a read-only token if the platform is
   willing.
2. **The Node tools have no unit tests.** `transform.mjs`, `validate-world.mjs`, `thread-check.mjs`
   and `simulate-world.mjs` are the largest and most intricate code in the kit, and they are covered
   only end to end. The extraction changed `transform.mjs` and relied on output comparison.
3. **`sync-tooling.sh` has no safety rails.** It does not refuse a dirty working tree, it does not
   preview deletions, and `rsync --delete` on `tools/` silently removes a world's script unless it is
   in `tools/local/`. A sync run on an uncommitted world produces a diff nobody can review — which
   defeats the one human control the vendoring model depends on. *Fix:* refuse unless the tree is
   clean, print the deletions and require an explicit `--force`, and offer `--dry-run`.
4. **The templates are excluded from lint.** A template with a malformed frontmatter field is caught
   only when someone copies it into a note. *Fix:* a test that substitutes the `REPLACE` placeholders
   and lints the result.
5. **Nothing checks the conventions against the linter.** `conventions.md` §16 documents the lint
   codes and the linter emits them; neither knows about the other. A new code can ship undocumented, or
   documented and never emitted.
6. **`verify-world.sh` depends on a fixture each world keeps its own copy of**, and nothing compares
   the two copies. They will drift.
7. **The `--check` flags are conventions, not gates.** `disclosure.py --check`, `voice_lint.py`, the
   audit's `--strict` and `sync-agent-protocol.py --check` all exist and all work; only `lint.py` is
   wired into a session by habit. A world's CI (T16) is what would make the rest real.

### 3.5 Human review: what a person is actually accountable for

| Thing reviewed | By whom | Enforced or convention |
|---|---|---|
| The publish audit before deploying | the author | **Convention.** The build gates on unresolved and ambiguous links only; the keystone hits, the internal references and the withheld tags are for a human to read |
| `voice_stale.py`'s list | the author | **Convention, and unowned.** By design a nag — but nobody is named as the reader, so in practice nobody reads it |
| The sync diff | the world's owner | **Convention.** It is the whole review surface for a tooling update, and it currently includes the vendored docs and templates |
| The disclosure classification of every lore section | the author, checked by `disclosure.py --check` | **Enforced**, and this is the strongest human-plus-machine control in the system |
| The engine-capability register's PR/PF/BD/DT dispositions | the platform owner at Step 2c | **Enforced by process** |
| The agent protocol in `AGENTS.md` | generated | **Enforced** (`--check`) |
| The fixture's de-brand | the kit's K2 | **Nothing.** It is debt, and it is honestly labelled as debt (D42) |

Two of these are load-bearing and only conventional. The first is the publish audit: the site's
no-spoilers promise rests on a person reading `site/audit/latest.json` before a deploy, and the
deploy workflow will happily publish without it. *Fix:* make the deploy workflow refuse to publish
when the committed audit is older than the last commit that touched a lore note, and put the keystone
hits in the job summary so acknowledging them is one click rather than one habit.

The second is the staleness list. *Fix:* give it an owner — the session protocol already refreshes
the site every session; the same step should print the list, and the open-questions note should carry
the outstanding accounts.

### 3.6 If four decisions were made again

1. **Put `verify-kit.sh` in CI from the first commit**, paying whatever it costs — a stub package, a
   token, a mirrored schema file. The extraction's best test is manual, and that is a decision nobody
   would make deliberately.
2. **Give the sync a dry-run and a dirty-tree refusal in its first version**, not after a rehearsal
   found it wanting. The vendoring model's entire safety argument is "the diff is reviewable", and an
   unreviewable diff is the failure mode.
3. **Do not only weaken the tests.** Assert shape *and* add a world-coherence test; the shape rewrite
   was correct and it removed coverage nobody replaced.
4. **Assert the semantic fields of generated artefacts, not only whole-file identity.** One line —
   *the manifest's `world_id` equals the config's* — would have caught the defect that survived six
   scenarios and a validator.

### 3.7 What this means for confidence

**Solid.** The config seam (T1/T2) and the document splits (T3). Evidence: byte-identical outputs,
0 lint errors across the first world's 398 notes, ~225 tests, the parity test, and the fact that the tools now run in
two repositories that share nothing but `world.config.yaml`.

**Newer and much less exercised.** The *tooling contract*: vendoring, the sync, the vendored docs and
the protocol region. It has been rehearsed once, by hand, and it found two bugs — which is an argument
for the rehearsal and against its being manual.

**The structural risk to watch.** Three repositories and a bespoke sync, with no published package and
no drift check, means a world can lag silently and a sync can delete a file nobody expected. Both are
fixable, neither is fixed: they are T16 and 3.4 item 3.

**The remaining build.** The site theme (T6), the world template (T9–T12), and this repository's
retreat (T13–T15) — the step that removed the duplicate: `worldkit/` is gone, and this repo vendors the kit's tools at `TOOLING_VERSION`.

---

---

## 4. What closed, and how

Carried from the plan's open-items list, kept because a closure is a decision too:

- ~~**How the agent protocol reaches a world**~~ — **closed** (D29/D36): a synced, marked region of `AGENTS.md`, written and checked by `tools/sync-agent-protocol.py`. The checker now has its own suite, because it silently did nothing for one commit while broken (see {S}9.3).

The items that were still OPEN when the extraction finished are in this kit's `ROADMAP.md`, where the
work now lives, along with `K10` (the sync's safety rails) which the evaluation above asks for
and which was the last task of the plan to land.

---

## Links

- `ROADMAP.md` — the kit's own work plan and open items
- `docs/conventions.md` — the rules the extraction settled
- `CONTRIBUTING.md` — how to change the kit, and what a release costs

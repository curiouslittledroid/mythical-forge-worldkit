# Changelog

A world pins the kit by copying its version into `TOOLING_VERSION` and updating with
`tools/sync-tooling.sh`. **A change a world cannot absorb silently is a major bump and gets a
migration note here.**

## 3.2.0 — a new world keeps the demo world, and the register leaves every world

`init-world.sh` no longer removes `example-world/`. Deleting it was the wrong default: it is the one
worked example of every note type, a complete thread and a running campaign, and a new author asks
"what does a finished note look like?" for months. The tools already leave a root `example-world/`
alone — the linter and the citation checker skip it, and the engine export reads only `world/` and
`campaigns/` — so keeping it costs a folder and nothing else.

- **`--keep-example` is gone**; keeping the example is what happens. `--fetch-example` puts it back
  at the repository's `TOOLING_VERSION` (or the kit's default branch when the pin is `unreleased`) —
  a repair, not an initialisation: it asks nothing, changes nothing else, and refuses to overwrite a
  copy that is still there. `WORLDKIT_REPO` points it at a local checkout, as with `sync-tooling.sh`.
- `template-fork.yml` now proves both halves on a fresh fork: the demo world survives `init-world.sh`,
  and `--fetch-example` restores it after a deletion and refuses to clobber a live copy.
- **The template's docs say keep it**: `README.md`, `AGENTS.md` and `ROADMAP.md` no longer tell an
  author to delete the example once their own notes exist.

**No migration.** `init-world.sh` lives in the template, not in a world's vendored `tools/`, so an
existing world is unaffected. A fork made after this change keeps `example-world/`; delete it by hand
if you really do not want it.

**New: `meta/conventions/tooling.md`, the runbook.** The tools were documented script by script
(`tools/README.md`) and step by step (`ROADMAP.md`), but nothing answered the question an author
actually has: *I changed this — what do I run now?* The new document is task-first: what you just
changed, the command that proves it, the order for the everyday loop and the pre-commit gate, the
publish order, what each tool writes, what runs in CI without you, what to do when a tool refuses,
and which document holds the rules. `tools/README.md` now points at it and keeps the
script-by-script reference.

It is a synced document: a world receives it at `meta/conventions/tooling.md` on its next
`tools/sync-tooling.sh`. The template's `AGENTS.md`, `README.md` and `ROADMAP.md` list it, and
`template-fork.yml` requires it in the export.

That workflow's completeness list also stopped demanding `tools/docs/conventions.md`, a path retired
in 3.0.0 — the export correctly does not contain it, so the check could never pass. Found while
adding the new document to the same list.

**`export-template.sh` no longer deletes the destination's `.git`.** The destination is normally a
checkout of the template repository on a branch, and the export replaced its tree with an
`rsync --delete` that took `.git` with it — leaving a working directory with no repository while the
finished export looked perfect. It also now *replaces* the tree rather than merging into it, prints
the paths it removes, refuses a directory that holds a repository (`<project>/{bare.git,main}`)
rather than being one, and says which branch the checkout it kept is on. `template-fork.yml` asserts
both halves — `.git` and history intact, tree equal to a fresh export — and `CONTRIBUTING.md` has the
publish procedure it never had, "Publish the template".

**The missing-schemas message speaks to an author.** It used to open "… is not installed, and
MYTHICAL_FORGE_ROOT is not set", then offer a `.npmrc` to write and two routes, one of which — a
checkout of the private platform repository — no world author has and none can follow. Now it names
one fix, in order: `export NODE_AUTH_TOKEN=<read:packages on @curiouslittledroid>`, `npm install`,
the fact that `.npmrc` already carries the registry, what a 401 means, and what does *not* wait on
any of it — lint, citations, disclosure and the site build. The checkout route moved to
`verify-kit.sh`, which is the kit's own script and its maintainer's audience. A test asserts the
world-facing message never names that variable, and the world-facing documents that repeated it
(`tooling.md`, `README.md`, `AGENTS.md`, the `ROADMAP`'s steps, `conventions.md`'s authority line,
the capability register, and the `transform`/`validate` headers that called it REQUIRED) now say
what an author can do instead.

The same audience test took **`Design 23`** out of the world-facing prose: an author holding a vault
cannot open the platform's design documents, so a section number is a dead reference, and reads as
something they are missing. 25 citations went from `thread-pattern.md` (which cited it a dozen
times), the campaign authoring guide, `conventions.md`, `AGENTS.md`, the template `ROADMAP`, and the
`tools/` headers and comments — each replaced by the rule it stood for ("the engine applies a source
exactly once per Sandbox"). **Kept deliberately:** `engine-capability-register.md` and
`meta/platform-requests/`, whose job is telling the platform *which spec text to change* — there
the section number is the payload, not decoration.

**A fork's site has a favicon again.** `BaseLayout.astro` links `/favicon.svg` and the kit's theme
had no `public/` at all, so every fork's pages 404'd their icon; the only copy in existence was in
the old hand-made template, and the export deleted it — correctly, since it does not produce it.
The theme now ships the neutral mark at `site-theme/public/favicon.svg` (ink ground, parchment
lozenge, ember core — the Dust Road tokens), the export copies `public/` and fails if the icon is
missing, and `template-fork.yml` requires it in the completeness list. `site/public/` is the
**world's** from here on: the sync never writes it, so a world's own favicon and its `img/` art
survive every release. `site.md` and the theme's README say so.

**The engine capability register moved out of the world.** `meta/conventions/engine-capability-register.md`
is now `meta/platform-requests/engine-capability-register.md`, in the kit, written for the platform it
describes. It was never an author's document: it classifies what the engine can express and holds the
platform requests, which is the kit owner's call as the platform's owner. Shipping it into every world
invited exactly the wrong reading — that a world's author has a say in what the platform supports, or
a document to consult for a decision only one person can make.

**Migration.** A world's next `tools/sync-tooling.sh` **deletes** `meta/conventions/engine-capability-register.md`
(an ordinary sync removes a kit document the kit no longer publishes). Nothing a world authored is
lost. What to do:

- **Keep any `PR-` / `CP-` id you already quote** — in `meta/mechanics-gap-register.md`, a thread card,
  a roadmap step. The ids are stable; the file is just no longer beside them.
- **Log a gap in your own `meta/mechanics-gap-register.md`**, with the workaround in use, and stop
  there. It is a request, not a decision: what the engine supports is not a world's to change, and the
  register no longer being in the vault is the point.
- **A note that cites it has to be edited.** After the sync, `check_citations.py` reports
  `ERROR: §4: no document matches meta/conventions/engine-capability-register.md` and `checks.yml`
  goes red on the push. Point the sentence at `meta/mechanics-gap-register.md` instead, or drop the
  citation. This is the one thing in the release a world must do by hand.
- **Do not invent vocabulary** in an `engine` block to work around a gap. `conventions.md` §13 says the
  closed vocabularies stay closed, and it now names your own register as where the request goes.
- **§13 answers "can the engine do this?" without the catalogue.** It opens with a `node -e` command
  that prints every closed vocabulary from the installed schema package — the authority, asked rather
  than transcribed — and its lists are corrected: entity kinds (18, including `SITE` and `ZONE`) and
  milestone types were missing. A value that is not in the list is not the engine's, and the section
  says what to do instead (§9.6, §9.7, your register) and that the decision is not a world's.

**What this changed in the documents.** A world's `AGENTS.md`, `conventions.md` §13, the agent protocol,
`thread-pattern.md`, the template `ROADMAP` and `mechanics-gap-register.md` all pointed at a file a
world no longer has. Each now says what an author can do (log it locally, use the workaround, do not
invent) instead of pointing at the catalogue. The kit's `check_citations.py` resolves the old aliases
to the new path, so a citation written against the old file still resolves here.

**`./verify-kit.sh` now checks citations in the layout a world holds the documents in.** It copied the
documents into a world shape only after its engine-schema gate, which fails on a machine without
the schemas — so the kit's own citation check saw `template/meta/conventions/…` and passed while a
fork's saw `meta/conventions/…` and failed, four times in a row on a §13 rewrite. The new step runs
before the gate, needs no engine, and builds `meta/conventions/` + `meta/templates/` in a throwaway
directory to check citations there. Verified by undoing one fix: it reports the two errors the fork did.

**More of the extracted world's residue, removed.** The same sweep that fixed site.md's keystones
found the rest of its shape:

- `thread-pattern.md` taught the pattern with the extraction source's pilot — its thread, its NPCs,
  its flags, its settlements. The examples are now the demo world's Ferryman's Debt where it can
  carry the pattern, and placeholders where the demo is too small (a Managed ladder, a long Ratchet).
- The same residue in smaller pieces: the campaign authoring guide's Managed-cycle blocks and its
  links, two note templates that named another world's epoch as `t0`'s reference, the capability
  register's overland id and a pilot count, the demo world's thread naming a thread it does not
  contain, and the simulate example in `tools/README.md`.
- The demo world's site note labelled eighteen tags belonging to another world and published three
  that were not among them; it now labels its own.

**A check, so this cannot come back quietly.** `tools/check_doc_examples.py` reads the world-facing
documents and fails on two things: an engine id the demo world does not have (unless it is an obvious
placeholder), and a phrase from the world the kit was extracted from. It is the id half of the rule
the kit's CI already greps for by name (`Hollowfall`), and the phrase half that would have caught
site.md's "current list". It runs in `ci.yml`, in the shipped `checks.yml`, and at the top of
`verify-kit.sh` — no schemas needed — and it skips with a clear message when a repository has no
demo world.

Still outside the list at that point: the atlas tools and the agent prompts. They are fixed in the
entry below.

**The atlas is data-driven, and the prompts are generic.** The atlas schema had one world's frames,
sections and type vocabulary baked into `atlas_yaml.py`, and `atlas_tables.py` wrote that world's
geography into the note it generated. The agent prompt `atlas-refresh.md` was that world's map
brief, down to its feature lists and note ids.

- **`atlas_yaml.py`** validates structure, not a world's taxonomy: the YAML declares `frames:`
  (each with `x`/`y`, and optionally `name`, `prefix`, `grid_km`) and a `default_frame:`; every
  list-valued top-level key is a section; an entry needs an `id`, a `name` (or a plate's `title`,
  or a route leg's `from`/`to`), a `status`, and well-formed geometry if it has any. `source` is
  no longer required by the tool — the world's register decides that.
- **`atlas_tables.py`** writes the generated note from the data: `title`, `summary`, `notes`,
  `labels`, `gm_sections`, `links` and `travel` are the world's, with generic fallbacks. Grid
  references come from each frame's `prefix` and `grid_km`; a frames table replaces the world
  prose. `atlas.md` documents the contract.
- **`atlas-refresh.md`** is rewritten as a procedure: read the YAML, the register and the
  feature-owning notes; extend the sections the file declares; never a list of one world's places.
- **The template ships `maps/atlas-register.md`** (a brief with the questions to answer), which is
  the note the prompt cites — so a fresh fork's citation check is now clean.
- **Fixtures and comments**: `test_lint.py`'s tag vocabulary, `voice_lint.py`'s example and a
  `kit_config.py` comment are neutral. The remaining names in `test_voice.py` and
  `test_site_export.py` are test prose (a fixture teller and her town), not guidance; they are left
  for a dedicated sweep rather than mixed into this one.

**`tools/check_doc_examples.py --all`** now also sweeps `tools/` and `template/` for the source
world's phrases (the list lives once, in that tool). `ci.yml` and `verify-kit.sh` run `--all`; the
shipped `checks.yml` keeps the document check. New `tools/test_atlas.py` (26 tests) covers the
schema, the view and `--check`.

**What a world must do, on syncing this (major bump, per the sync contract):**
regenerate `maps/atlas-features.md` and read the diff. To keep the old grid references, add
`prefix` and `grid_km` to the frames that had a local grid (`far_reach` was `FR` at 100 km, and so
on); the default frame keeps its 250 km master grid. The generated note's headings and preamble now
come from the data: set `title`, `summary`, `notes`, `labels`, `gm_sections` and `links` in the YAML
to keep the prose you had. The YAML's own `frames:` and sections are unchanged, so it still
validates; nothing in a place note moves.

## 3.0.0 — the kit owns the template; the template repo is generated

The refactor that makes `mythical-forge-worldkit` the single source of truth for both the demo world
and the world template, so the template repo is never edited by hand.

**The kit's layout changed.** The demo world (`world/`, `campaigns/`, and the demo's `meta/` notes)
now lives, complete with its own `world.config.yaml`, at `template/example-world/`. The kit root is no
longer a world; its `meta/` holds only `templates/` and `platform-requests/`. The theme directory is
renamed `site/` → `site-theme/` (it is still vendored into a world as `site/`).

**The template is generated.** `template/` is the source (the skeleton an author forks, plus the
embedded `example-world/` demo), and `export-template.sh` assembles the published
`mythical-forge-world-template` repo from it. `sync-tooling.sh` no longer mirrors `example-world/`
into a template — that is the export's job now.

**The documents split by reader, and they moved.** `docs/` now holds **only what it takes to
maintain the kit**: `extraction.md`. Every document a world author must read — `conventions.md`,
`campaign-authoring-guide.md`, `thread-pattern.md`, `site.md`, `testimony.md`, `tag-vocabulary.md`,
`atlas.md`, `engine-capability-register.md`, `agent-protocol.md`, and **`licensing.md`** (a world
has to know what it may not relicence) — moved to `template/meta/conventions/`, and a world now
holds them at **`meta/conventions/`**. `tools/docs/` is gone.

`extraction.md` deliberately does **not** travel: it is the record of extracting the kit from the
first world and names that world throughout. A world used to receive it; it no longer does. Two rules are unchanged and now easier to state: they are **prose, not notes** (no
frontmatter, no id; the linter does not read them as part of the vault), and they are **cited by name
and section, never by wikilink**. The move puts a rule one file away instead of one directory away,
and it keeps the folder wholly the kit's, so the sync replaces it wholesale.

**What a world does — two steps, once.** The sync re-execs itself onto the new script, so the renamed
theme source (`site-theme/`) needs nothing. The documents need one action:

1. `git rm -r tools/docs` — the folder is retired, and a sync that would delete it will refuse until
   you commit the removal (the rails are working as designed).
2. `tools/sync-tooling.sh v3.0.0` — this writes `meta/conventions/` and the pin.

A world's `meta/conventions/` is the kit's: never edit it, the sync replaces it. A world's own
decisions still live beside it in its own `meta/` notes, which the sync never touches.

**A change a world cannot absorb silently is a major bump.** The pin moves on its own, but
`tools/docs/` disappearing is not something a sync can do without a decision from the world — hence
the migration note.

**`template: true` is gone.** It existed so the sync could mirror the demo world into a template. The
template is an export now, so nothing reads the switch and it is no longer a config key — a
`world.config.yaml` that still carries it is an unknown-key error rather than a silent no-op. The
template no longer has it, and `init-world.sh` no longer removes it.

**What the export and the fork proof fixed.** `template-fork.yml` no longer syncs into the published
template; it **exports a template from the commit it is running on** and forks that, so a change that
breaks the export fails its own CI. Making that real found four defects, all fixed here:

- the export reused the *sync's* exclusions and dropped the theme's three neutral pages
  (`index.astro`, `about.astro`, `follow.astro`), so a generated template had no landing page and its
  site could not build;
- `site/image-prompts/_style.md` — the house style the image process calls authoritative — was never
  shipped, by the sync or by the export;
- a fresh fork carried a stray two-line `meta/flags.md`, which collided with `world/flags.md`: six
  lint errors, so a fork could never pass `tools/lint.py`;
- the engine-capability register's Links section pointed at the **first world's** notes. It names the
  kit's documents now.

## 2.0.1 — the fork workflow's check that could never pass, and a test for the new seam

Two things 2.0.0 left, both found by running the work rather than reading it.

- **`template-fork.yml`'s "nothing left behind" check failed on every run.** It greps the fork for
  `REPLACE_ME`, and `init-world.sh` contains that string by definition — it is the thing that replaces
  it. `--exclude=init-world.sh` now, plus `--exclude-dir=dist` for a build that happens to sit in the
  tree. The job had never passed, so nobody had seen it.
- **`tools/test_authored_content_resolution.py`** locks the seam down: the installed package is the
  default, a checkout wins when `MYTHICAL_FORGE_ROOT` is set, a wrong checkout names the missing
  `packages/authored-content/package.json`, and having neither produces one actionable message — not a
  stack trace, which is what a world actually sees first. Written in the kit's Python suite style, so
  CI runs it with the rest.

## 2.0.0 — the schemas are a package, so the pipeline runs anywhere (task 5.B4)

The engine's Zod schemas were reachable only through a checkout of the platform repository, named by
`MYTHICAL_FORGE_ROOT`. That is why `verify-kit.sh`, a world's `tools/verify-world.sh` and the template
fork could only be run by hand, on a machine with the platform installed and built: the strongest proof
this project has was its most manual one. Phase 5 task B4 published the schemas as
`@curiouslittledroid/authored-content` (ADR-0023 records why the scope is the maintainer's personal
one), and this release consumes it.

**A world cannot absorb this silently, so it is a major bump.** What a world does, once:

1. Take the repository's two new root files: `package.json` (the pin — `0.0.3`, **exact**) and
   `.npmrc` (the registry, and the token read from the environment, never committed).
2. `export NODE_AUTH_TOKEN=<a fine-grained PAT with read:packages on @curiouslittledroid>`, then
   `npm install`.
3. Nothing else. Every Node tool finds the schemas, and the world's own pipeline runs in CI as soon as
   a `WORLDKIT_PACKAGES_TOKEN` secret exists.

`MYTHICAL_FORGE_ROOT` still works and still **wins when set**, so a world mid-migration is not stuck:
the old behaviour is one environment variable away, and the new path is what CI uses.

What changed:

- `tools/kit_config.mjs` — `mfRoot()` now returns the checkout or `null`, and one new function,
  `authoredContent()`, loads the schemas from whichever source exists. `requireMf(spec)` keeps its
  name; in installed mode it resolves `yaml` through the package's own dependency closure, not by
  hoping for a hoist.
- `tools/validate-world.mjs`, `tools/check-guide.mjs` — ask `authoredContent()`, instead of reaching
  into a checkout by path.
- `verify-kit.sh`, `tools/verify-world.sh` — no longer require the variable. Each probes the schemas
  once, prints one message naming both fixes, and links the repository's `node_modules` into the
  throwaway copy its proof runs in.
- `checks.yml`, `ci.yml`, `template-fork.yml` — the pipeline is now part of CI, token-gated, with a
  warning that says what was skipped when the secret is absent. `ci.yml` running `verify-kit.sh`
  closes the last open testing item in the roadmap.
- `package.json`, `.npmrc` — new at the root, for the one runtime dependency.
- The documents that promised a checkout — `README.md`, `tools/README.md` (its Setup section is a
  two-row table now), `docs/conventions.md`, `docs/engine-capability-register.md`, `CONTRIBUTING.md` —
  say what is true. `docs/licensing.md` §6 records the dependency's FSL-1.1-ALv2 terms, which are not
  this kit's MIT.
- `ROADMAP.md` — K14 is closed and gone.

One deliberate non-change: **no lockfile is committed here.** Generated from a local tarball it would
record a `file:` path, and each world's lockfile is its own business; the pin is exact, which is what
determinism needs.

## 1.3.9 — the guard was on one step of two

`tooling-drift.yml` grew an "Is this a world?" step when it started failing on the kit, and I put the
condition on the *first* of the two checks it guards. The second — the file comparison, the one that
matters — kept running, and on the kit it reported `tools/docs`, `tools/LICENSE` and
`tools/LICENSE-CONTENT` "missing: the machinery has been deleted", which is a *true* statement about a
world and a meaningless one about the kit: a kit keeps its documents as a sibling of `tools/` and its
licences at its root, and it is the sync that puts them inside a world's `tools/`.

The lesson is smaller than the others in this run but the same shape: **when a condition is about a
place, put it on every use of that place** — or on the job, where it cannot be half-applied.

## 1.3.8 — the suite, and the rail that refused my own sync

Two things 1.3.7 left.

- The suite's line-number assertion named `12:` by hand; the duplicate is on line 10. It finds the line
  in the fixture now, so the number cannot drift.
- The sync **refused** to move this world to v1.3.7, and was right to: the rename left
  `tools/check-workflows.py` inside `tools/`, which the kit no longer has at that tag, and the rail's
  message says exactly that — a file inside a directory the kit owns that is not in the kit. That is
  the rail from v1.1.0 doing the job it was built for, on the person who built it. `--force` is the
  right answer here and only here: the file is a renamed kit file, not a world's work.

## 1.3.7 — the tool's own name made it unimportable

The reason 1.3.6 did not fix anything: the file was `check-workflows.py`, and a **hyphen is not
importable in Python**. `sys.path` was never the problem, and adding the insert changed nothing. It is
`check_workflows.py` now, which is what every other Python tool here does — `check_citations.py`,
`lore_export.py` — and what a hyphenated filename quietly forbids. (`.mjs` tools may hyphenate; nothing
imports them.)

Two releases, the same thread: a suite that could not run, then the reason it could not run. Both found
by running the suites by hand, neither by the workflow that would have failed on it minutes later.

## 1.3.6 — the new test could not import the new tool

`test_check_workflows.py` did `from check_workflows import duplicates`, and every other suite in this
kit begins with `sys.path.insert(0, ...)`. Mine did not, so the suite failed with a
`ModuleNotFoundError` — and `checks.yml` runs every `tools/test_*.py`, so this would have turned every
world red one release after the last red. The idiom is followed now.

1.3.5 was tagged and synced before this was noticed, which is the argument for running the suites
*before* the tag rather than in the workflow that follows it. `verify-kit.sh` does run them — and it
passed, because `verify-kit.sh` runs the suites from inside its temporary world, where the path is
different. Two callers, one of them correct by accident.

## 1.3.5 — a check for the check that GitHub refused to load

Fixing the drift check for the kit, I put **two `if:` keys on one step**. GitHub refuses such a file
outright: the workflow showed up in Actions named by its *path* instead of "Tooling drift", and every
run failed with nothing a reader could act on. My own validation — `ruby -ryaml` — parsed it happily,
keeping the last key, which is exactly the trap.

`tools/check-workflows.py` finds duplicate keys without a YAML library, and it is careful about the one
thing that makes a naive version useless: a list of steps repeats `run:` and `with:` at the same
indentation by design, so sequence items reset the chain. It runs in `verify-kit.sh`, in `checks.yml`
(standard library only, so it works on a runner), and it has tests — including the case that a naive
detector gets wrong.

That is three rails in this session written to catch a mistake of mine, and two of them then failed in
a way the third would have caught. The pattern worth naming: **validate with something that rejects
what the real consumer rejects.** A lenient parser is not a validator.

## 1.3.4 — the version rail, third time lucky, and what the three attempts cost

The rail that compares `TOOLING_VERSION` with the newest tag has been wrong twice, and both times it
false-alarmed on a normal release — which is the one thing a check must not do.

| Attempt | Rule | What it did |
|---|---|---|
| 1 | equal the newest tag | failed while *preparing* a release, the state CONTRIBUTING.md's own steps pass through |
| 2 | equal the tag when HEAD is tagged, else not behind | failed at the same moment: "preparing v1.3.4" and "just tagged v1.3.4" are indistinguishable until the tag exists |
| 3 | **not behind the newest tag** | asks the only question that is always well-defined, and answers the bug it was written for |

Each attempt was proved by breaking it, and each proof passed — because the proofs tested the *bug*,
not the *false alarm*. That is the gap: I checked that the check catches what it is for, never that it
stays quiet when nothing is wrong.

## 1.3.3 — the identity gate earns its keep, and the drift check stops applying to the kit

Two failures the kit's own CI found once it could run.

- **A world's name was in the kit's machinery.** Porting `main`'s platform-request text into
  `docs/engine-capability-register.md` brought the sentence "(Hollowfall supplies its own base map)"
  with it. The identity gate caught it in CI within a minute of the push — the second time that gate
  has caught something real, and both times it was a batch edit made after a local check.
- **`tooling-drift.yml` cannot pass on the kit**, and now says so and skips. It is a check for worlds:
  a kit keeps its licences at its ROOT and the sync is what copies them into a world's `tools/`, so
  `tools/LICENSE` does not exist here. The kit's proof is `ci.yml`.

## 1.3.2 — four failures, and one of them was a check that could never pass

The first runs of the newly published workflows found four defects. Three were real; the fourth was a
check of mine that was broken and *always failed*, which is the worse kind.

- **`tooling-drift.yml` compared two FILES with `-d`** (the licences the sync copies into `tools/`).
  `-d` is false for a file, so it reported "the machinery has been deleted, not vendored" for files
  sitting in the tree — on every world, every run, since the licences were added. `-e` now. It
  survived because the workflow had never executed: the same root cause as everything in 1.3.1.
- **`checks.yml` gated a kit and a template on a rule about worlds.** The disclosure gate fails on
  deliberately unreviewed fixture sections, and the suites assert a real world's vocabularies where a
  template has `REPLACE`. Both now run only when the repository IS a world: no `verify-kit.sh` at the
  root, and no `template: true`.
- **`ci.yml` gated itself on a private repository.** The guide check needs `MYTHICAL_FORGE_ROOT`; a
  runner cannot have it. A missing platform now skips it with a warning that says which checks were
  skipped, rather than failing for the rest of the repository's life.
- **`template-fork.yml` and the version rail:** fixed in 1.3.1, and the tag push itself is now in the
  release checklist (`git push origin main --tags`; `--follow-tags` carries only annotated tags).

The lesson, one more time and more sharply: **a check that has never run is not a check, and a check
that always fails is worse than none** — it teaches everyone to look away, and then the real alarm is
missed. Everything in this release was found within ten minutes of the workflows getting a remote.

## 1.3.1 — CI that had never run, and what it found in four runs

The kit and the template were pushed to GitHub today, which switched on four workflows that had only
ever been reasoned about. All four failed, and two of the failures were bugs that would have hit every
world the moment it added the workflows.

- **`checks.yml` ran a check no runner can pass.** `tools/check-guide.mjs` parses the authoring guide's
  blocks with the platform's own schema (`@mythical-forge/authored-content`, from `MYTHICAL_FORGE_ROOT`
  ), and the platform repository is private, so no runner can have it. It is **not** in the workflow
  now, and the workflow says why: run it locally, before a commit that touches the guide.
- **`checks.yml` gated a kit on a rule that is about worlds.** The disclosure check fails on any
  unreviewed lore section, and the kit's demo world has plenty — it is a fixture, not a world. The
  step now runs only when the repository is not a kit or an uninhabited template (read from
  `world.config.yaml`'s `template: true`). Every world keeps the gate.
- **`template-fork.yml` synced the empty string.** `actions/checkout` does not fetch tags unless told
  to, so `git tag --list 'v*'` was empty, and the workflow passed the empty tag to `sync-tooling.sh`
  (which refused — the rails held). It now fetches tags, and an empty tag is a loud failure naming the
  checkout option that fixes it.
- **`tooling-drift.yml` failed on the kit itself** for the same missing-tags reason, and now passes.

The lesson is the one this repository keeps learning: **a check that has never run is not a check.**
`verify-kit.sh` was green throughout, because everything it runs is local. The workflows were written,
reviewed and shipped to worlds without a single execution.

## 1.3.0 — the machinery a world had grown on its own

A world does not stop moving while its machinery is extracted. Three commits landed on the source
world's trunk while the extraction was in flight, and four of the things they added turned out to be
kit work: the Lore corpus export, a lint check, a template line and two sections of rules. They are
here now because the alternative — a world quietly keeping a tool the kit does not have — is drift,
and the drift check would have reported it on every release forever.

- **`tools/lore_export.py` and `tools/test_lore_export.py`** (Step 14, PR-14): one chunk per
  paragraph, layer-split history events, a derived audience, wikilink subjects, and the calibration
  report. Nothing in them was specific to the world they were written on — they import `disclosure`
  and `lint` and read `world/` — which is exactly why they belong here.
- **`tools/lint.py`:** `parent` joins `group_knowledge`, `groups`, `home` and `zone` as a frontmatter
  key whose ids must exist, so a region's `parent:` is checked.
- **`docs/conventions.md` §5.3 (Zones) and §7.5 (Lore chunks and prose audience):** the zone rules and
  the corpus rules, genericised. **The section numbers are kept** because the world's own notes cite
  them by number, and a document keeps its numbers where a world cites it by number.
- **`meta/templates/region.md`:** `parent:`, and a `coords` comment that says whose frame it is in.
- **`tools/README.md`:** the two new tools, in the tables. A world receives all of this by syncing.

The lesson worth keeping: **extraction has a moving target.** A branch that forks from a world's trunk
and lives for weeks will meet that trunk again, and everything the world learned in between has to be
sorted into "this world's" and "everyone's". The drift check is what makes that sorting visible
instead of silent — it is what found these four.

## 1.2.3 — the licence strategy, written down

Patch: a new document, plus two stale places it exposed. A world should sync — `docs/licensing.md`
arrives with the rest of `tools/docs/`, and it is worth a world author's ten minutes.

- **`docs/licensing.md`** is the strategy and the reasoning: why the machinery is MIT and not
  Apache-2.0 or the GPL, why the prose is CC BY 4.0 and not BY-SA, why a world is all rights reserved
  and why it should start that way, what a world decides and what it may not touch, the one place a
  third-party notice is needed (the fonts the built site serves), the alternatives considered and
  rejected, and how the notices are **enforced** — the sync copies them, the drift check compares them
  with the pin, the sync's test asserts they arrive — rather than declared in a file nobody reads.
- **`CONTRIBUTING.md`** says what a contribution is licensed under, which it never did.
- **The README's licence section still said "to be decided (K1)"** and its status line still said
  version 1.0.0. Both were written before K1 was decided and neither had been read since — by me,
  twice: the edit that was supposed to fix the first had a guard that skipped it silently.
- **The CI gate now excludes `docs/extraction.md`**, which is provenance: the record of an extraction
  names the world it extracted from, throughout. The gate caught this itself, on the push that would
  have failed for it.

## 1.2.2 — the drift check and the sync disagree about one list

Patch. Safe to sync.

1.2.0 made the sync copy the licences into a world's `tools/`, and taught the drift check to compare
them there — but not to exclude them from the `tools/` comparison, so the check that watches for
drift would have reported drift on every world, on every run. Same shape as `docs/` in 1.0.11 and
1.1.1, and the fourth time in one session.

The exclusions are in, and the shape itself is now a roadmap item (**K15**): the sync's file list
exists in three places — the `tools/` rsync's exclusions, the drift check's exclusions, and the
copies the sync makes — and every bug of this kind has been one of the three being out of step. The
fix is to have the drift check ask the sync what it would write (`--dry-run` already prints it) so
there is one list.

## 1.2.1 — the move left four warnings behind

Patch. A world should sync.

`docs/extraction.md` moved the decisions into the kit, and D40 cites the FIRST world's
`meta/site.md` — §1, §4, §5 and §10–§12 — for the rule that a document which keeps its section
numbers keeps its name. This repository does not hold that note, so the citation check was right to
warn: the numbers are history here, not a reference. The row says so now and opts out with
`citations: ignore`.

The opt-out itself was documented only in the checker's own docstring, which is not where a rule
lives. It is in `docs/conventions.md` §16.1 now, with the warning that it is for the genuinely
uncheckable and not for the inconvenient.

## 1.2.0 — the kit has licences, and they travel (K1)

Minor, and it touches every world. A world should sync.

**MIT** for the tools, the theme and the scripts; **CC BY 4.0** for the prose — the documents, the
note templates, the agent prompts and the example world. The prose is the part that exists to be
copied into other worlds, which is exactly what that licence is for; BY-SA would have forced a
world's adapted copy of the docs to be share-alike too, and MIT on the docs would let a world's
teaching material be sold without attribution.

**The part with a legal edge to it:** MIT requires its notice to travel with every copy, and a
world's `tools/` *is* a copy. Until now a world vendored the kit's code and never received its
licence, which is a violation, however minor. The sync now copies `LICENSE` and `LICENSE-CONTENT`
into `tools/`, the drift check compares them with the pin like everything else, and the sync's test
asserts they arrive.

**And that found a bug in the sync, immediately, before it shipped:** the kit keeps its licences at
its root and a world keeps them *inside* `tools/`, so the `tools/` rsync found them in the world,
not in the kit, and deleted them — the same asymmetry that had just cost 1.1.1 a release over
`docs/`, and 1.0.11 one over the drift check. The exclusions are in, and the rule is now written
where the next person will read it: **anything the sync places inside a world's `tools/` from the
kit's root must be excluded from that rsync.** The regression test that caught it stays.

Also: `site/LICENSES.md` lists the site's build dependencies and carries the SIL OFL notice the
bundled IBM Plex fonts require, since the built site serves those font files; `site/README.md`
names the theme's licence; and the demo world's footer sentence now matches its licence instead of
saying "all rights reserved" about a world that ships with an MIT toolkit.

## 1.1.2 — the rails cried wolf about the site's generated directories

Patch. A world should sync.

The site's `src/data/` and `src/content/` are the exporter's, and exist in any world that has built
its site and nowhere in the kit — so the theme rsync deleted them on every sync, and 1.1.0's new
deletion preflight therefore refused **every published world**. Excluding `data/generated` was not
enough; the parents have to go too.

This is the third release in a row where the same shape of bug appeared: a path that exists in a
world and not in the kit (or the reverse) being mistaken for a difference. The tests now cover both
cases — a world's rules in `tools/docs/`, and the generated directories — because a false alarm from
a rail is worse than no rail: it teaches everybody to pass `--force`, and then the real one is missed.

## 1.1.1 — the sync was deleting the world's rules

Patch. A world should sync.

**The bug:** the kit keeps `docs/` as a *sibling* of `tools/`; a world keeps it at `tools/docs/`. The
`tools/` rsync therefore found `docs/` in the world and not in the kit, and **deleted it on every
run** — and the next line re-created it from the kit's `docs/`. The end state was always correct, so
it never showed. But a run that stopped between those two lines left a world with **no rules at all**,
and 1.1.0's new refusals made that reachable, because a refusal is a stop. `docs/` is excluded from
that rsync now: the vendored docs are copied, and never removed.

This is the same asymmetry 1.0.11 had to fix in the drift check. It has now cost two releases, which
is why it is stated in the sync's own comments rather than left to be rediscovered.

**The ordering:** 1.1.0's refusals ran again after the script re-executed itself mid-upgrade, and
refused a tree its own first half had just changed. They run once now, at the start, on the tree the
user chose — never in the re-executed second half.

**Both were found by testing the rails on a throwaway copy of a real world, which is also how the
1.1.0 release was tested.** A rail nobody has watched fire is a rail that does not work.

## 1.1.0 — the sync has safety rails (K10)

Minor, and it can refuse. A world should sync: `tools/sync-tooling.sh` is replaced. Read the two
refusals before your next sync, because they can stop one.

Vendoring's whole safety argument is *the diff is reviewable*. Three ways it was not:

- **A dirty tree.** Syncing onto uncommitted work mixes the tooling upgrade with whatever the world
  was in the middle of, in one diff nobody can attribute. The sync now refuses when the world has
  uncommitted changes **in the paths it replaces** — `tools/`, `meta/templates/`, `site/src/`,
  `.pi/prompts/`, the workflows — and passes cleanly over the paths that are the world's own:
  `tools/local/`, its three site pages, its art, its deploy state. (`--force` overrides.)
- **A deletion nobody was shown.** `rsync --delete` on `tools/` silently removes a file a world put
  there, which is how a world's own script disappears. The sync now re-runs itself in dry-run mode
  first, lists what it *would* delete, and refuses — with the remedies: move it to `tools/local/`, or
  `--force` and let it go.
- **No rehearsal.** `--dry-run` prints every change and writes nothing: no rsync, no `cp`, no
  `TOOLING_VERSION`, no protocol re-sync.

The two refusals cost one extra fetch and one extra rsync pass, and they are the rails the
extraction's own evaluation asked for after a rehearsal found the failure mode by hand.

## 1.0.13 — the extraction's record moves here

Patch: a new document, and four open items. A world should sync — `docs/extraction.md` arrives with
the rest of `tools/docs/` — and a world with a `ROADMAP-EXTRACTION.md` of its own can now delete it.

The first world carried the extraction's plan as a temporary file, to be deleted when its last phase
landed. It has. What was worth keeping moves here:

- **`docs/extraction.md`** — the decisions (D1–D42) as they were taken, and **the evaluation**, which
  was written after the kit was built and asks which decisions survived contact, which are weaker
  than they read, and which were simply wrong. The plan's remaining open items are in `ROADMAP.md`
  now, where the work lives.
- Pointers follow: the kit's `tools/README.md` and `tools/lint.py` referred to a world's temporary
  file for their own design reasoning, which is the same defect in miniature as the citations 1.0.1
  to 1.0.7 kept finding.
- **K11–K14** are the four items the extraction left OPEN: the unchecked prose path reference, the
  codex index's tag line (chrome that wants a world's voice), a fork's missing Open Graph image, and
  the fact that the strongest proof of all — the engine pipeline — is still the most manual.

## 1.0.12 — a comment that told a small lie

Patch. A world should sync: `tools/verify-world.sh` is replaced.

The comment above the copy said the transform writes `codex-threads.yaml` into the vault, and that
this is why the checks run on a copy. It does not: it writes into the Game Ready Repository. The
copy is still right — a check should not be able to modify the world it is checking — but the reason
is now the real one rather than a plausible-sounding one. Nobody would have caught this by reading
the code; it was caught by grepping for the write the comment promised.

## 1.0.11 — the drift check failed on every world

Patch, and a lesson in shipping a check you have not run. `tooling-drift.yml` compared the kit's
`tools/` with a world's `tools/` — but a world keeps the kit's `docs/` at `tools/docs/`, inside
`tools/`, while in the kit it is a sibling. So the byte comparison reported "Only in tools: docs" on
every world, every run: an alarm that is always on is an alarm nobody reads. The comparison excludes
`docs` now, and compares `kit/docs` with `tools/docs/` as its own case, which it already did.

Found by running the check's own logic against a real world before trusting it — the same discipline
as the mutation test on the site exporter, and the reason both bugs were found by the tool rather
than by a user.

## 1.0.10 — the CI a world needed, shipped and synced

Minor: two new workflow files reach every world through the sync. A world should sync.

**`checks.yml`** runs on every push: the suites, the linter, the citation check, the disclosure check
and the guide check. Everything it runs needs neither the platform repository nor the engine, which
is why it can be CI at all. `tools/verify-world.sh` proves more and stays the local pre-commit step.

**`tooling-drift.yml`** answers the question vendoring makes easy to get wrong: is the pin behind the
kit, and do the vendored files still match the pin? Vendoring means a world commits the kit's files
as ordinary files, so a hand-edit to one is invisible until the next sync silently reverts it. The
check clones the pinned tag and diffs `tools/`, `tools/docs/` and `meta/templates/` against it, and
names the files that differ. A world that deliberately pins an older version can set the repository
variable `WORLDKIT_ALLOW_DRIFT=true` and get a warning instead of a failure. It reaches the kit over
HTTPS; a private kit needs a `WORLDKIT_TOKEN` secret, and if the kit cannot be reached the job warns
and passes rather than failing for the wrong reason.

**`template-fork.yml`** is the kit's own, and is not shipped: on a change to the machinery it fetches
the published template, syncs the newest kit tag into it, initialises a throwaway world with
`init-world.sh`, and runs the checks and the site build on the result. That is T12 run as a job
instead of by hand: the question "can somebody start a new world from the template today?" answered
on every release. It needs the template to be reachable; it warns and passes if it is not.

## 1.0.9 — a new world could not pass its own proof

Patch. A world should sync: `tools/verify-world.sh` is replaced.

`verify-world.sh` exited 2 with "no scenarios: name some, or set `vault.scenarios`" on a world that had
written no scenarios yet — which is every world for its first eleven steps, and the exact state the
template hands to a new author. The proof script now says so plainly and passes, and only when there
is genuinely nothing to run: if scenario files exist and the config does not name them, the
simulator's own error still fires.

The distinction matters because the template's promise is "fork it and the pipeline is green". A
green that requires inventing a fake campaign first is not a green.

## 1.0.8 — a prompt came from one world, and a check that never read the prompts

Patch. A world should sync: `.pi/prompts/` is replaced.

Six places in the kit's own prose referred to files that do not exist, or to the FIRST world's files
as if they were the kit's:

- **`.pi/prompts/new-creature.md` was one world's creature rules**, not a process: the water-hole
  rule, well-wyrms, the Grown, the Lineage, a closed list naming that world's peoples. It is now the
  generic sequence — read the world's own rules first (`world/creatures/_index.md`, usually), propose,
  interview, write, check — and it says plainly that the world's rules outrank it. Nothing was lost:
  every rule in the old version is in that world's notes, which is where a world's rules belong.
- `docs/campaign-authoring-guide.md` cited `tools/verify-example.sh`, which was replaced by
  `tools/verify-world.sh` in 1.0.0; `ROADMAP.md` and `CHANGELOG.md` now mark the old name as historic.
- `site/image-prompts/README.md` documented the first world's plate files as if they were the kit's.
  It documents the shape now; a world's plates are the world's.
- `docs/conventions.md`'s example filename, `CONTRIBUTING.md`'s example tool name and
  `world.config.yaml`'s note about the template's config all named something that does not exist
  (`world.config.example.yaml`) or something of the first world's.

**The identity gate did not read `.pi/prompts/`.** That is why a file of one world's monster rules
sat in the kit through eight releases. It does now. `site/` is still excluded, deliberately, until K6
settles whether the theme ships the first world's art direction as its default.

## 1.0.7 — the image prompts cited a world's note

Patch. A world should sync and re-run `tools/verify-world.sh`.

`.pi/prompts/image-accept.md` and `image-prompt.md` sent an author to `meta/site.md` section 6 for
the image deliverables and the colour rule. That path is the WORLD's own site note: in the first
world it numbers its sections, and in a new world it need not -- so the citation dangled in a
template and warned in every world that does not number its notes. The rules are the kit's, and they
are in the kit's `docs/site.md` §6.

This is the third variant of the same mistake (1.0.2, 1.0.3, here): a kit file citing a world's
document by path or number. The convention is in `docs/conventions.md` §16.1 -- a kit document cites
the kit's documents -- and the check reports the rest as NOTES.

## 1.0.6 — the re-exec guard never fired

Patch. No world needs to do anything, but a world more than one release behind should take this
one: it is what makes every later release safe.

`sync-tooling.sh` re-executes itself when a release replaces the running script, because bash keeps
executing the text it started with: without it, a release that adds a sync step does not run that
step when a world takes the release. **The guard could never fire.** It compared the kit's copy with
the world's copy -- and the rsync three lines earlier had just made those identical, so the test was
always false. It now compares a copy of the running script, saved before the copy, with the file
that replaces it. Three tests drive a fake kit and assert that a step added upstream really runs.

Two smaller fixes found while testing it:

- the re-exec runs the script through `bash`, so it works even if the copy on disk lost its execute
  bit. That was this script's first defect, and a re-exec that fails on permissions would be worse
  than no re-exec;
- the shell tools are `chmod +x` after the copy, and the kit's `docs/` copy is guarded like the
  others: a kit without a `docs/` directory no longer kills the run.

## 1.0.5 — the sync can now bootstrap a repository

Patch. No world needs to do anything.

`tools/sync-tooling.sh` assumed its destinations existed: it rsynced into `meta/templates/`,
`site/src/`, `.pi/prompts/` and `.github/workflows/` without creating them first. A world always has
those directories, so this never showed -- and the first repository that did not (the world template,
which is meant to start nearly empty) failed on its very first sync with

    rsync: mkdir ".../meta/templates" failed: No such file or directory

Every destination is now created with `mkdir -p` before anything is written into it, and
`example-world/` gets its three subdirectories for the same reason. Found by bootstrapping the
template through the sync rather than by copying files around it, which is the point of the template
existing at all.

## 1.0.4 — the check got stricter, and found more

Patch. A world should sync and re-run `tools/verify-world.sh`.

Three changes to `tools/check_citations.py`, each of which found citations that the previous
version accepted:

- **It now reads the site's markdown.** `site/` was skipped wholesale, so the art prompts -- which
  cite section numbers in a checks table -- were never checked. Three of them cited a section of the
  world's site note that does not exist; one cited the palette in the wrong section.
- **A reference to a document this repository does not have is reported, not skipped.** A kit prompt
  legitimately cites a world's atlas register, and in the kit that reference resolved to nothing and
  vanished. That silence is exactly how the `thread` template kept a stale citation until a world ran
  the check (1.0.3). These are printed as NOTES at the end of a run: visible, and not failures.
- **A reference that names a directory no longer falls back to a bare basename match.** `meta/site.md`
  was matching the kit's `docs/site.md`, which made a citation of the world's note look like a
  citation of the kit's -- and the same bug hid the palette citation named above.

Also fixed, all in the kit's own files: `tools/site_export.py`, `site/astro.config.mjs` and
`site/image-prompts/_style.md` cited `meta/site.md` where they meant `docs/site.md`. In a world the
first path is the world's own site note with different numbers.

## 1.0.3 — a template that cited a world note by number

Patch. A world should sync and re-run `tools/verify-world.sh`.

`meta/templates/thread.md` told an author that the thread classes were in a section of a world note.
The kit could not see the problem: that note lives in a world, so in the kit the citation resolved to
nothing and the check passed. In a world it resolved, and the number was wrong -- the note has been
cut back, and that section is no longer there. The classes are the kit's own concept, so the template
now cites the kit's `docs/thread-pattern.md` §6.

The rule this teaches: **a template cites the kit's documents, never a world's.** A template is
copied into a world whose notes are numbered differently or reduced, and the kit's own CI can only
see the citations that resolve inside the kit.

## 1.0.2 — two dozen citations the check found in the kit's own voice

Patch. Nothing a world authors changes; a world should sync and re-run `tools/verify-world.sh`.

The citation check's first findings were not only in a world's notes. Four of the kit's own tools
and docs cited the world's site note (`meta/site.md`) where they meant the kit's (`docs/site.md`) --
a path that resolves to a DIFFERENT document in a world, which is exactly the ambiguity
`docs/conventions.md` §16.1 forbids. In the kit the citation read correctly; in a world it pointed at
a note with different section numbers. Fixed by naming the path, not the basename.

## 1.0.1 — the citation check

Patch: no world's content changes and no section number moves. **Re-run your own proof**
(`tools/verify-world.sh`) — the check below is new, and it will report citations that were already
wrong before this release.

**New: `tools/check_citations.py`.** Every `§N` citation is resolved against the document it names.
It fails when the number does not exist, when the document numbers nothing, and when the document
cannot be found. Renumbering a document is the change it exists to catch: a section that moves takes
every citation of it with it, silently, here and in every world that synced the old numbers. Wired
into `verify-kit.sh`, `verify-world.sh` and CI. The rule it enforces is in `docs/conventions.md`
§16.1.

**Fixed — the check's first findings.** Twelve citations gave the testimony specification its old
document name (`docs/site.md`) although those sections are `docs/testimony.md` §3.4/3.5; the atlas
refresh prompt cited the register's corrections table and its build section by the numbers they had
before a renumbering; and a few citations in the kit's own docs pointed at sections that do not
exist. A world that cites these documents will see the same findings.

**Nothing else changed.** `template: true`, the `example-world` linter exclusion and the sync's
example mirror are groundwork for the world template and land in the next release.

## 1.0.0 — the extraction

The first release: the tooling and the general rules lifted out of the first world
(`hollowfall-codex`), with every world-specific value moved behind `world.config.yaml`.

**If you are migrating a world that predates the kit**, the changes that are not silent:

1. **A `world.config.yaml` is now required at the vault root.** It replaces the values that used to
   be hardcoded in the tools: the world's id, title, its overland entity, its game-ready repository,
   the ids of the notes the tools must find, and the site's navigation. See `docs/conventions.md`
   §2.
2. **`MYTHICAL_FORGE_ROOT` has no default.** It must point at the platform repository (the directory
   holding `packages/authored-content`). Every tool fails loudly and names the variable if it is
   unset; the old default silently produced `Cannot find module 'yaml'`.
3. **Scenarios live with their campaign**, not in `tools/`. `vault.scenarios` names the directory.
4. **`visibility` is gone.** The publish axis is the disclosure class (`open`, `earned`, `sealed`) on
   every lore section, and the site exports the `open` ones. A GM-only note is written in full and
   classified, never omitted.
5. **Spelling is a setting** (`vault.spelling`); the linter checks it. Metric stays mandatory.
6. The documents a world used to hold are now the kit's, cited **by name and section**. A world keeps
   a pointer note for each (see its `meta/campaign-authoring-guide.md` for the pattern).
7. **A world vendors the kit's documents at `tools/docs/`**, written by the sync: the rules are part
   of the tooling, because a tool enforces a rule the world's agent has to be able to read.
8. **`tools/verify-world.sh` replaced `verify-example.sh`**, and it overlays nothing: it runs the
   world's own vault and its own scenarios. A world no longer carries a copy of a fixture it does not
   own — delete `meta/templates/examples/ferryman/` and keep the world's examples in `meta/examples/`.
   `meta/templates/` is now wholly the kit's and is mirrored, so anything a world adds there is
   removed by the next sync.

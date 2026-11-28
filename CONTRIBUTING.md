# Contributing to the worldkit

Read `AGENTS.md` first: it states the boundary (the kit owns the rules, a world owns the lore) and
the rule that follows from it — **no world literals anywhere**.

## Add a tool

A tool is a script in `tools/` plus a test beside it. Keep both in the same commit. And say who
it is for: a world author runs `tools/` on their own content and never edits it, so a tool whose
output an author must act on belongs there (and in `meta/conventions/tooling.md`), while an
assertion about the toolchain belongs in a suite.

1. **Name it for what it does**, not for where it is used: `voice_stale.py`, not `myworld-voices.py`.
2. **Read the world through the config.** `import kit_config` (Python) or `./kit_config.mjs` (Node)
   and take the world's identity, its note ids and its feature switches from there. Never take a
   world's path, title or id as a default: if the tool needs one, the config is where it comes from,
   and a missing value is an error naming the key.
3. **Fail loudly.** One line, naming the variable or key a human must set. The old
   `MYTHICAL_FORGE_ROOT` default printed `Cannot find module 'yaml'`, which says nothing about the
   actual problem — that mistake is why the rule exists.
4. **Write the test first, with a fixture.** `testkit.py` builds a fixture vault: `write_config(root)`
   copies the live config, and the keyword arguments replace one vocabulary list. A test that
   asserts a world's *values* is a bug; assert the *shape* the tool requires, or set the value
   explicitly.
5. **If both languages read the config, prove they agree.** `check_config.py` runs `kit_config.mjs`
   beside `kit_config.py` on the live config and compares them field by field; a change to one
   reader without the other is caught there. It is a *tool* rather than a test on purpose: the kit's
   demo world is 36 entities, and every world can prove the agreement about its own config, where
   the subset's corners actually appear. `test_check_config.py` covers the comparison itself.
6. **Document it in `tools/README.md`** — one row in the table, in the order a reader would meet it.
7. **Run the proof:** `./verify-kit.sh` (green — with the schemas installed, or `MYTHICAL_FORGE_ROOT` set). It builds the demo
   world in a throwaway directory and runs the whole pipeline on it.

## Change a rule

The documents in `template/meta/conventions/` are the kit's interface: a world reads them (at
`meta/conventions/`), and its content is shaped by them. **`docs/` holds only what it takes to
maintain the kit** — today just the extraction record. If a world author must read it, it belongs in
`template/meta/conventions/`. The licensing reasoning is there, not here, because a world has to
know what it may not relicence.

- **A rule change is a code change.** If you change what `tools/lint.py` accepts, change the
  conventions section, the template and the linter's test **in the same commit**. A rule that exists
  in the linter but not in the conventions is invisible to an author; the reverse is a lie.
- **`meta/conventions/conventions.md` keeps its section numbering.** Sections are cited by number from worlds and from
  other kit documents. Add to the end, or deprecate a number in place — never renumber.
- **A closed vocabulary is closed.** Relationship kinds, judgement tags, effects, tactics and content
  descriptors belong to the engine. If the world needs something it cannot express, that is a
  **request** in `meta/platform-requests/engine-capability-register.md`, not a new value here.
- **Say it once.** One home per rule; link to it rather than restating it. If two documents need the
  same rule, one of them is the home and the other cites it by name and section.

## Change the engine contract

When the platform ships a release, `meta/platform-requests/engine-capability-register.md` is where it lands: move the
request out of the catalogue, record what actually shipped, and re-classify the rows it changes. A
world's own `meta/mechanics-gap-register.md` lists which requests **its** lore was waiting on, so it
can find its own work without re-reading the catalogue.

## Release

1. `./verify-kit.sh` green (it lints the demo world) and the Python suites green.
2. Bump `TOOLING_VERSION`.
3. Add a `CHANGELOG.md` entry. **A change a world cannot absorb silently is a major bump and needs a
   migration note** — state the change, why it is not silent, and what a world must do.
4. Tag it with exactly the string `TOOLING_VERSION` now holds (`v3.2.0`, `v` included) — the file and
   the tag are the same string, because a world's `sync-tooling.sh` copies the tag into its own
   `TOOLING_VERSION`. A world fetches a tag, so an untagged change is a change no world can take.
   **Push the tag itself**: `git push origin main --tags`.
   A plain `git push` does not carry tags, and `--follow-tags` carries only *annotated* ones — so a
   lightweight tag pushed with `--follow-tags` arrives nowhere, and `sync-tooling.sh` fetches tags.
5. `python3 tools/sync-agent-protocol.py` — if the protocol changed, every world's `AGENTS.md` region
   must be re-synced, and its `--check` is what notices.
6. `python3 tools/check_citations.py` — if a document's sections moved, every citation of it moved
   too, here and in every world that synced the old numbers. The check is the sweep; do not rely on
   reading the diff.
7. **Publish the template** at the milestone: see below. That repo is generated, so it moves on this
   schedule and not on every commit.

## Publish the template

`mythical-forge-world-template` is **generated**: `export-template.sh` assembles it from this repo's
`template/` (the skeleton, the world-facing conventions, the note templates, the embedded
`example-world/`), plus `tools/`, `site-theme/` (as the world's `site/`), the world's three
workflows, and the pin. **Never edit the template repo by hand**: a defect in it is a defect in
`template/`, fixed here and re-exported. `export-template.sh --help` is the flag reference; this is
the order.

1. **Export the released tag into the checkout, on a branch.** From this repo's root:

   ```bash
   git -C ../../mythical-forge-world-template/main switch -c export-v3.2.0
   ./export-template.sh v3.2.0 --force ../../mythical-forge-world-template/main
   ```

   - **The tree is replaced, not merged into.** Anything in the checkout that the export does not
     produce is deleted, and the export prints what: a path the kit retired cannot survive in a
     published template. `--force` is what says you meant it, and a checkout is never empty.
   - **`.git` is kept** — excluded at the root, and only at the root — so the checkout stays a
     repository on the branch you chose and the export tells you which. Do not "tidy that away": a
     version that did not exclude it left a working tree with no repository, and the finished export
     looked perfect.
   - **Name the checkout, not the directory holding it.** A container — `<project>/{bare.git,main}`,
     the layout these projects use — is refused by name, because replacing it would take the mirror
     and the worktree both.
   - **`--worktree`** exports *this* checkout instead of a tag and pins the newest local tag, or
     `unreleased`. It is for proving an uncommitted export (it is what `template-fork.yml` runs on
     every push), never for a published milestone.
   - **`WORLDKIT_REPO=/path/to/checkout ./export-template.sh …`** exports from a local clone with no
     network fetch.

2. **Read the pin.** `cat ../../mythical-forge-world-template/main/TOOLING_VERSION` must print the tag
   you passed. If it says `unreleased`, `git describe --tags` found no tags in that checkout:
   `git fetch --tags` and export again. A world's `sync-tooling.sh` writes the same string into its
   own `TOOLING_VERSION`, so a bogus pin is a bogus world — which is why `template-fork.yml`
   checks out with `fetch-depth: 0` and `fetch-tags: true`.

3. **Prove it as a new author would**, out of a throwaway copy of the export:

   ```bash
   rm -rf /tmp/fork-check
   rsync -a --exclude .git ../../mythical-forge-world-template/main/ /tmp/fork-check/
   cd /tmp/fork-check
   ./init-world.sh --title "Ashfall" --yes   # the questions a fork is asked; keep example-world/
   python3 tools/lint.py                     # 0 errors
   npm --prefix site install && npm --prefix site run build
   ```

   `tools/verify-world.sh` — the engine pipeline — needs the engine's schemas: the packaged install,
   or `MYTHICAL_FORGE_ROOT` on a machine that has a platform checkout. CI prints it as *not run*
   rather than pretending. The site build is the half that catches a missing neutral page, which the
   export has silently dropped before.

4. **Branch, commit and open a PR in the template repo**, so the generated tree arrives as a
   reviewable diff, and name the kit tag in the message (`Worldkit v3.2.0`). Merge it.

5. **Tag the template with the same string** — `git tag v3.2.0 && git push origin main --tags`, with
   the caveat in step 4 of the release list above. The kit tag and the template tag read alike, so
   "which kit is this template?" is answered by `git describe --tags` on either.

Between milestones a difference is normal and expected: `template-fork.yml` diffs a fresh export of
every push against the published repo and reports how far behind it is, without failing. A **broken
export** is the thing that fails, on its own, before anything is published.

## What a contribution is licensed under

By contributing, you agree that your contribution is licensed under the kit's own two licences:
**MIT** for code (`LICENSE`) and **CC BY 4.0** for prose (`LICENSE-CONTENT`). That is the whole
agreement — there is no CLA — which means you must have the right to contribute what you send: your
own work, or work whose licence permits this use.

The kit's `licensing.md` (vendored into a world at `meta/conventions/licensing.md`) explains the
split, and why it is a split.

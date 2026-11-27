# Contributing to the worldkit

Read `AGENTS.md` first: it states the boundary (the kit owns the rules, a world owns the lore) and
the rule that follows from it — **no world literals anywhere**.

## Add a tool

A tool is a script in `tools/` plus a test beside it. Keep both in the same commit.

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
5. **If both languages read the config, prove they agree.** `test_kit_config.py` has a parity test
   that loads the live config with both readers and compares them. A change to one reader without
   the other is caught there, not in a world.
6. **Document it in `tools/README.md`** — one row in the table, in the order a reader would meet it.
7. **Run the proof:** `./verify-kit.sh` (green — with the schemas installed, or `MYTHICAL_FORGE_ROOT` set). It builds the demo
   world in a throwaway directory and runs the whole pipeline on it.

## Change a rule

The documents in `docs/` are the kit's interface: a world reads them, and its content is shaped by
them.

- **A rule change is a code change.** If you change what `tools/lint.py` accepts, change the
  conventions section, the template and the linter's test **in the same commit**. A rule that exists
  in the linter but not in the conventions is invisible to an author; the reverse is a lie.
- **`docs/conventions.md` keeps its section numbering.** Sections are cited by number from worlds and from
  other kit documents. Add to the end, or deprecate a number in place — never renumber.
- **A closed vocabulary is closed.** Relationship kinds, judgement tags, effects, tactics and content
  descriptors belong to the engine. If the world needs something it cannot express, that is a
  **request** in `docs/engine-capability-register.md`, not a new value here.
- **Say it once.** One home per rule; link to it rather than restating it. If two documents need the
  same rule, one of them is the home and the other cites it by name and section.

## Change the engine contract

When the platform ships a release, `docs/engine-capability-register.md` is where it lands: move the
request out of the catalogue, record what actually shipped, and re-classify the rows it changes. A
world's own `meta/mechanics-gap-register.md` lists which requests **its** lore was waiting on, so it
can find its own work without re-reading the catalogue.

## Release

1. `./verify-kit.sh` green (it lints the demo world) and the Python suites green.
2. Bump `TOOLING_VERSION`.
3. Add a `CHANGELOG.md` entry. **A change a world cannot absorb silently is a major bump and needs a
   migration note** — state the change, why it is not silent, and what a world must do.
4. Tag it `v<TOOLING_VERSION>`. A world's `sync-tooling.sh` fetches a tag, so an untagged change is a
   change no world can take. **Push the tag itself**: `git push origin main --tags`.
   A plain `git push` does not carry tags, and `--follow-tags` carries only *annotated* ones — so a
   lightweight tag pushed with `--follow-tags` arrives nowhere, and `sync-tooling.sh` fetches tags.
5. `python3 tools/sync-agent-protocol.py` — if the protocol changed, every world's `AGENTS.md` region
   must be re-synced, and its `--check` is what notices.
6. `python3 tools/check_citations.py` — if a document's sections moved, every citation of it moved
   too, here and in every world that synced the old numbers. The check is the sweep; do not rely on
   reading the diff.
7. **Export the template** at the milestone: `./export-template.sh <tag>`, then create a branch in
   `mythical-forge-world-template`, commit the generated tree, merge, and tag it. The template repo
   is never edited by hand.

## What a contribution is licensed under

By contributing, you agree that your contribution is licensed under the kit's own two licences:
**MIT** for code (`LICENSE`) and **CC BY 4.0** for prose (`LICENSE-CONTENT`). That is the whole
agreement — there is no CLA — which means you must have the right to contribute what you send: your
own work, or work whose licence permits this use.

`docs/licensing.md` explains the split, and why it is a split.

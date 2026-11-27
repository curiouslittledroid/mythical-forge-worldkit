# AGENTS.md: the Worldkit

You are working **on the worldkit**, not on a world. Everything here is the machinery and the shared
rules that many worlds use; a world consumes it and adds lore. Getting that boundary wrong is the
only serious mistake available in this repository.

| | |
|---|---|
| **This repo owns** | the tools, the shared rules, the note templates, the site theme, the engine-capability register, the agent protocol |
| **A world owns** | its lore, its decisions, its vocabularies, its spelling, its note slugs — and its own copy of this repo's tools, vendored at `tools/` and pinned by `TOOLING_VERSION` |
| **Never here** | any world's place, person, faction or history. **No world literals anywhere**: not in a script, not in a default, not in a doc example. A doc example uses the Ferryman fixture; if it cannot, it uses a placeholder |

## Where things are

| Path | Purpose |
|---|---|
| `ROADMAP.md` | The kit's own work plan. **Start here for what to do next.** |
| `docs/extraction.md`, `docs/licensing.md` | **The kit's own documents.** The record of the extraction, and why MIT for the code and CC BY 4.0 for the prose. Nothing an author of a world reads. |
| `template/meta/conventions/` | **Every world-facing document.** A world holds them at `meta/conventions/` at the pinned tag, so this is where an author reads the rules. |
| ↑ `conventions.md` | **The rules** every world follows: layout contracts, ids, frontmatter, engine blocks, disclosure, status values, the linter's codes. The kit's most load-bearing document. |
| ↑ `engine-capability-register.md` | What the engine can express, the platform requests, and the dispositions. **Where a platform release lands.** |
| ↑ `agent-protocol.md` | The protocol a world's `AGENTS.md` carries verbatim. This repo is its source. |
| ↑ `campaign-authoring-guide.md` | The how-to for authoring threads, Campaigns, Modules and Quests. |
| ↑ `thread-pattern.md` | The reference behind the guide — **why** a thread is a state graph. |
| ↑ `site.md`, `testimony.md`, `tag-vocabulary.md`, `atlas.md` | How a site is generated, the first-person device, the tag rules, and the map pipeline. |
| `tools/` | The scripts, and the tests beside them. |
| `site-theme/` | The Astro theme a world installs (vendored into a world as `site/`). |
| `template/` | The generated world-template's source: the skeleton a new author forks, the world-facing documents (`template/meta/conventions/`), the note templates (`template/meta/templates/`), and the embedded `example-world/` demo. `export-template.sh` assembles the template repo from it. |
| `meta/platform-requests/` | Draft specs written for the platform repository. Not the kit's own backlog. |

## How to work here

1. **Read** `ROADMAP.md`, `template/meta/conventions/conventions.md` (section 16 is the linter) and this file before changing anything.
   **`docs/` is for kit maintenance only.** If you write something a world author must read, it goes in `template/meta/conventions/`, not `docs/` — that folder is exported into every world, and `docs/` is not.
2. **The tests are the contract.** A tool change lands with its test. `python3 -m unittest discover -s tools -p 'test_*.py'` runs the Python suites; the Node tools are exercised by `verify-kit.sh`.
3. **Every tool must run against the Ferryman fixture with no world literals.** `verify-kit.sh` is the proof, and it is what CI runs. If your change makes it depend on a world, it is wrong.
4. **Two readers, one contract.** Where a language needs the world config (Python and Node both do), the readers must agree and a parity test must say so. Never hand-edit the generated side.
5. **A doc change is a code change.** The templates, the conventions and the tools are one system: if you change what the linter accepts, change the conventions section and the template in the same commit.
6. **Do not fork the rules.** If a world needs an exception, it goes in that world's own override note, not in a conditional here.
7. **Versioning.** `TOOLING_VERSION` is the kit's; a world pins it. A change a world cannot absorb silently is a **major** bump plus a migration note in `CHANGELOG.md`. See the sync contract in `README.md`.
8. **Commit** with a clear message, keep the working tree clean, and keep `verify-kit.sh` green.

## What is not yours to decide

- **What a world looks like.** The kit supplies the shape; the world fills it. If a decision is about one world's lore, it belongs in that world's repo, and the answer here is a documented seam (a config key), not a default.
- **The engine's vocabulary.** Relationship kinds, flags, judgement tags, effects, tactics and content descriptors are fixed by the platform. Do not invent one here; add a request to `meta/conventions/engine-capability-register.md`.
- **The protocol's wording.** `meta/conventions/agent-protocol.md` is read by every world's agent: it must stay true for a world that shares none of this repo's other choices.

## The protocol itself

This file is the **kit's** brief. The shared protocol — how an agent works on a world, the vault and
engine rules, the writing conventions — is `meta/conventions/agent-protocol.md`, and it is *not* synced into this
file: this repo is its source, and a self-sync would say nothing. Read it before changing it.

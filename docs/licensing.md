# Licensing

Two licences, because there are two kinds of thing here: **machinery meant to be reused**, and
**prose meant to be copied and then built on**. One licence for both would either give away a world's
lore or encumber the tools, so the split is not a compromise — it is the shape of the problem.

This document is the strategy and the reasoning: what is licensed how, why those licences rather than
the obvious alternatives, what a world inherits and what it decides for itself, and how the whole
thing is enforced rather than merely declared in a file nobody reads.

## 1. What is licensed how

| Thing | Licence | Where it lives |
|---|---|---|
| The tools, the site theme, the scripts | **MIT** | `LICENSE` in the kit; `tools/LICENSE` in a world |
| The documents, the note templates, the agent prompts, the example world | **CC BY 4.0** | `LICENSE-CONTENT` in the kit; `tools/LICENSE-CONTENT` in a world |
| A world's own lore, notes, prose, maps and art | **All rights reserved**, by the world | the world's root `LICENSE` |
| The site's build dependencies and the bundled fonts | their own, all permissive | `site/LICENSES.md` |

A world repository therefore holds **two** licence files about the kit's material (`tools/LICENSE`,
`tools/LICENSE-CONTENT`) and **one** about its own (`LICENSE`). That is not redundancy: the two are
different grants, to different people, over different files.

## 2. Why MIT for the machinery

- **It is meant to be vendored and forked.** A world commits a copy of `tools/`; another world starts
  from the template. MIT is the licence that asks the least of the person doing that, and it is what
  Astro, Tailwind and Pagefind already use, so it adds no new obligation to the pile.
- **Copyleft would reach into a world's own work.** This kit's central promise is that `tools/local/`
  is the world's, unconditionally. A GPL-family licence on the kit would make a world's own scripts,
  built to call into it, a licensing question — for a toolkit whose whole point is that a world's
  work stays the world's.
- **Not Apache-2.0.** It is a fine licence and it adds an explicit patent grant, which matters for a
  project with patents to grant. The cost is bookkeeping (`NOTICE` files, per-file headers to be
  strictly correct) and a longer text, for a benefit no world has asked for. MIT is reviewable in a
  minute, which is worth more here.
- **Not public domain / CC0.** For prose, CC0 would be defensible. For code it drops the warranty
  disclaimer, and a toolkit that generates game content should not be handing out a blank cheque.

## 3. Why CC BY 4.0 for the prose, and not BY-SA

The documents exist **to be copied** — into a world's notes, into an agent's context, into another
worldkit's fork. Attribution-only is the licence that matches that sentence.

**Not BY-SA.** Share-alike is a considered position, and a defensible one: it keeps a commons a
commons. Here it would mean that a world which adapts a document to its own conventions must license
its adaptation the same way — imposing our terms on a world's own writing, which is precisely what §2
says we will not do.

**Not BY-NC.** Non-commercial is vague enough in practice to be a lawyer's question, it would forbid
uses nobody objects to, and it cannot be granted by a downstream user — the kit's author would end up
being the only party allowed to sell a document about the kit.

**Not no licence at all.** Without one, the default is "all rights reserved", so a world's agent
could read the rules but a world could not legally copy the note templates or the example world into
its own repository. That would quietly break the extraction this kit exists for.

## 4. Why a world is all rights reserved

A world's lore is the author's intellectual property, and its public site publishes what a resident
of the world could know — published to be read, not to be republished. A sentence in
`world.config.yaml` says so in the footer; `LICENSE` says it in full.

**The direction of travel matters more than the choice.** A licence, once granted, cannot be taken
back: everything already published keeps the licence it had, forever. So a world bible starts
restrictive and loosens if it wants to, rather than the other way around. That is why
`init-world.sh` writes all rights reserved rather than asking a new world to pick a licence in its
first minute, when it has no idea what it will become.

**The natural upgrade**, when a world wants others to reuse it, is **CC BY-NC-SA 4.0 for the `open`
material only** — the material a world has already decided to publish. The codex already sorts every
section along exactly that axis: `open`, `earned`, `sealed` (see the kit's `conventions.md`
§7). A world that takes this route is not inventing a boundary; it is drawing the licence along one
it already maintains.

## 5. How it is enforced, not just declared

A licence file that does not travel is a licence that does not apply, and MIT is explicit: *the
notice must be included in all copies or substantial portions*. A world's `tools/` **is** a copy, so:

- **The sync copies both licences** into `tools/` alongside the code they cover.
- **The drift check compares them with the pinned tag**, like every other vendored file — because a
  world that has drifted from its pin is distributing code under a notice that no longer matches it.
- **The sync's own test asserts they arrive**, so a future change to the copy list cannot quietly
  drop them.

And one thing that is *not* a licence: the `license:` line in `world.config.yaml`. That is the
sentence a world's site prints in its footer, for a reader. It should agree with `LICENSE`, and a
world that loosens its licence should change both — but it is prose, not a grant.

## 6. Third-party material

The kit ships **no** third-party code or assets: `tools/` is standard-library Python and Node, the
theme's dependencies are installed by npm and never committed, and there are no bundled fonts in the
repository.

The one place a notice is needed is the **built site**, which serves the web fonts the theme bundles.
Those are IBM Plex, under the **SIL Open Font License 1.1**, whose notice asks to travel with the
fonts. `site/LICENSES.md` carries it, lists every build dependency with its licence, and a world's
About page prints the one-line credit in its colophon.

If a world publishes text derived from the SRD, that text carries the SRD's own **CC BY 4.0**
attribution — separate from everything above and unaffected by it. Publishing *keys* or ids is not
that: they are names, not text.

### The engine's schemas — FSL-1.1-ALv2, and not ours

The toolchain has one runtime dependency that is neither ours nor MIT:
`@curiouslittledroid/authored-content` (Phase 5 task B4) — the engine's own Zod schemas, which the
transformer and the validator check a world's vault against. It is published from the platform
repository under the **Functional Source License 1.1, Apache-2.0 future licence** (`FSL-1.1-ALv2`):
any use is permitted except competing with the licensor, and the terms become Apache-2.0 after two
years. It is a *dependency*, so this kit's MIT says nothing about it — the notice travels with the
package into `node_modules/`, where `npm install` puts it.

Nothing else in this repository pulls anything at runtime: the site's build dependencies are the
site's own (`site/LICENSES.md`), and the Python is standard library.

## 7. What a world decides, and what it may not touch

**The world decides:** its own `LICENSE`; the `license:` sentence in `world.config.yaml`; whether to
grant anyone else anything at all; and whether to publish a fan policy alongside the licence.
Loosening later is always possible; tightening is not.

**The world may not relicence:** `tools/` (except `tools/local/`, which is its own),
`meta/conventions/`, `meta/templates/`, `.pi/prompts/`, or the theme under `site/`. Those are the
kit's, and a world
holding a copy of them does not hold the right to change their terms. A world that edits the licence
text itself will see it replaced at the next sync — which is the correct outcome, and the reason the
notices live beside the code rather than in a world's own file.

**A world's own scripts in `tools/local/`** are the world's, covered by the world's `LICENSE`. The
kit makes no claim on them, which is the point of that directory.

## 8. Alternatives considered, and why not

| Option | Why not |
|---|---|
| One licence for all three repositories | Either the lore is given away or the machinery is encumbered; the two are not the same kind of thing |
| MIT everywhere, including the prose | A world's teaching material could then be sold, badge removed, with no attribution — and attribution is the only thing the kit actually asks for |
| CC BY-SA for the prose | Forces share-alike onto a world's own adapted documents (§3) |
| GPL / AGPL for the tools | Reaches into the world's own scripts through `tools/local/`, which the kit promises are theirs |
| Apache-2.0 for the tools | Fine, and heavier: `NOTICE` bookkeeping and a longer text for a patent grant nobody has needed |
| CC0 / public domain | No warranty disclaimer on code; "no rights reserved" is also a harder position to reverse than it looks |
| A private, per-world commercial licence | Defeats the point of a kit other worlds can fork |

## 9. See also

- `LICENSE`, `LICENSE-CONTENT` — the texts themselves
- `README.md` — the one-paragraph version, for someone deciding whether to use the kit
- `site/LICENSES.md` — the site's dependencies and the fonts' notice
- `docs/extraction.md` — why the kit is three repositories, which is why there are three licences

# The Public Site

**Summary:** How a **public, player-facing site** is generated from a world's codex: what may be
published, in what shape, on what stack, and how it is refreshed. **The site is generated, never
hand-edited** — every page that shows canon comes from an `open` section of a note, so the codex
stays the only source of truth.

**This is the kit's mechanism.** A world owns §1 (audience and purpose), §4 (its landing page) and §5
(its visual direction); what is fixed here is the publish axis, the redaction rules, the audit, the
page shape, the stack and the deploy. **The section numbers are kept** from the document this was
split out of, because a world's notes cite them by number.

**Feature switch.** The subsystem is inert unless the world lists `site` in `world.config.yaml` →
`features:`. The config also supplies the world's URL and its section list — the first section whose
`kinds` contains a note's kind owns that note — so a world's navigation is data, not code.

## 2. What may be published

### 2.1 The publish axis is `disclosure`, not `visibility`

`visibility` was built for a printed player primer and is used by exactly one note. The site needs section granularity, which only `disclosure` has: an `open` section is *"public knowledge, what anyone of the player's culture knows"* (the kit's conventions §7). So:

- **Publish** every section whose effective class is `open`.
- **`mixed`** sections (a `HISTORY_EVENT` with Official/Myth/Rival layers) publish as split chunks; the `**Truth:**` line is dropped.
- **Drop** everything `earned` and `sealed`, including whole notes.
- **`visibility` is retired** (Step 2e, done): gone from every note, from lint and from the templates. The exporter has no special case for it.

The exporter **ports `disclosure.classify`** from `tools/disclosure.py`, never re-derives it: one classifier, two consumers.

Publishable at the time of writing: **464 open sections, ~32,400 words, 229 notes with an open section** (71 of them NPCs, which are deferred to Phase 4). Launch scope is roughly **160 pages plus ~18 layered history events**.

### 2.2 Redaction rules (inside an open section)

| Item | Rule |
|---|---|
| `**Want:**` / `**Wants:**` lines | strip **in an NPC note only** (an NPC's motive is `earned`, audience that NPC only). A god's `**Wants now:**` is public doctrine and stays. |
| Design/engine fields — `**SRD base:**`, `**Engine mapping:**`, `**Engine form:**`, or a table row with such a label | drop the whole line or row; log as `design_fields` |
| Design citations — `§9.7`, `CP-6`, `M3`, `PR-4`, `(conventions …)`, `(mechanics gap register)` | scrub the citation, keep the sentence; log as `internal_references`. **The right fix is to move the citation under `## Author Notes`**, which is not lore: the note keeps it and the page never sees it. This scrubber is the safety net for citations left in lore prose |
| `**Disclosure:**`, `**Reveal when:**`, `[OPEN]`, "decided, Step N Round M" | strip |
| Heading annotations — `## Culture (decided, Step 5, Round 1)` | reduce to the heading |
| `## Hooks`, `## Author Notes`, `## Open questions`, `## Links`, `## Engine`, fenced `engine`/`engine-example` blocks | drop |
| `## Named members` rosters | drop (group-tier input, not lore) |
| `\|` inside wikilinks (table escape) | unescape before resolution |
| Links to `campaigns/`, `world/plot-web/`, `meta/`, `maps/`, `principles/`, `world/flags.md` | **delete the link, keep the sentence**, log as `infrastructure`. With no label the target's title stands in and the entry is flagged `unlabelled` for review. |
| A plot-web thread's **name written as plain text** in published prose | log as `plot_web_text_mentions`. No link is involved, so the sentence survives and the reader gets an orphaned proper noun with no page. **Fix at source: a thread reference belongs under `## Hooks`** (conventions section 7.3), which never publishes. Thread titles that are also ordinary in-world vocabulary are listed in `REVIEWED_PLOT_WEB_SURFACES` and not reported. |
| Links to an `_index` map-of-content note | link to the **section landing page** (`[[gods/_index|the pantheon]]` → `/gods/`), log as `section-index` |
| Links to a note with no open content | **delete the link, keep the label**, log as `no-open-content` |
| Links that resolve to nothing | keep the label, log as `unresolved` (and fix the note later) |

Reference figure (first full build): of **1,155 wikilinks in published text, 1,077 point at a published page**. Of the 78 that do not, **31 are design infrastructure**, **26 are section-index jumps** and **21 are the seven open-face gaps** in section 11. **0 unresolved, 0 ambiguous.**

Reference figure (the session that closed the plot-web and design-citation leaks): **235 pages, 157 flattened links** — down from 196 — broken down as **deferred 97**, **no-open-content 26**, **section-index 34** and **infrastructure 0**. It was 43. Every plot-web thread reference moved under `## Hooks` and every design-doc citation under `## Author Notes`, which together took `internal_references` and `plot_web_text_mentions` to **0** as well. All three counts are now regression signals: any non-zero value is a new leak, not a known backlog.

### 2.3 The audit is part of publishing

Every build writes `site/audit/latest.json`, which is **committed** so there is a dated record of exactly what has been published:

```yaml
generated: <date>
pages: <n>              # published pages
sections: <n>           # published sections
words: <n>              # published body words
testimony_words: <n>    # of those, the words inside accounts
links: <n>              # wikilinks seen in published text
testimony:        [{ page, section, teller, taken, collected_on }]   # accounts published, and their volume
testimony_unplaced: [{ page, teller, taken }]                     # dated, but in no volume's years
testimony_undated:  [{ page, teller }]                            # no CY year: claims to be current
flattened_links:  [{ page, text, target, reason, unlabelled? }]   # infrastructure | section-index | no-open-content | navigation
plot_web_text_mentions: [{ page, target, text }]                  # thread names in published prose (fix at source)
unresolved_links: [{ page, text, target, reason }]                # reason: unresolved | ambiguous
ambiguous_links:  [...]                                           # the subset that fails --check
skipped_notes:    [{ note, reason }]                              # no open content | deferred kind | kind has no section
dropped_sections: [{ note, heading, class }]                      # earned | sealed only
dropped_lines:    [{ note, heading, text }]                       # truth lines and unlabelled lines in a layered section
design_fields:    [{ note, label, text }]                         # engine-facing fields removed
internal_references: [{ note, text }]                             # design citations scrubbed from prose
keyword_hits:     [{ page, section, term }]
pages_without_summary: [slug]
withheld_tags:    { tag: [note] }                                 # authored tags not published
empty_tags:       [tag]                                           # published but on no note: a config bug
```

`--check` fails on **ambiguous links only** — a genuine authoring bug. Everything else is for a human to read: the seven-gap links and the internal references are expected to shrink as the prose is fixed, and a build that publishes new lore should show them moving.

`keyword_hits` scans published text for the six sealed keystones (the kit's conventions §7.4). Current list: `compromised`, `Choir water`, `Convenor`, `body-hop`, `archmage`, `Gate-born`, `reopen the Gate`, `Halls`, `Lineage`, `Quiet Counsellor`. A hit is not automatically a leak — it is a line a human reads before deploying. **A build may be deployed only after the audit has been read.**

## 3. Information architecture

A world's navigation is its own and lives in `world.config.yaml` → `site.sections`: an ordered list of
`slug`, `label` and the note `kinds` each owns. **Section names are player-facing, not engine kinds**
(`FACTION` is "Powers"; an `ITEM` is a "Relic"), and the first section whose `kinds` contains a note's
kind owns it, so the list is read in order.

### 3.1 The Codex page

The directory, not a lore section. Four blocks on one page:

1. **Search** — Pagefind, built at compile time, no backend.
2. **Browse** — the seven sections with live counts.
3. **A–Z** — every published page with its open Summary as a one-line gloss.
4. **Recently added** — from `changelog.json`, dated.

**Words** (Phase 4) is a separate glossary page: a hand-maintained `term → note` list where **the note supplies the definition**. The site never authors canon, so it cannot drift from it.

### 3.2 Page anatomy

- Title, section, and an in-world **standfirst** from the open Summary.
- A **date stamp** — `T0 −22`, `T0 +400`, `T0` — read from the note's `t0` frontmatter, where
  **T0 is the Severing**. The sign hugs the number, so a negative offset reads as a negative
  number. The site formats it; it never authors a date. Undated pages show none.
- Body sections in note order, with a sticky table of contents.
- A **marginalia gutter** for cross-references and glosses.
- History events open with **"What people say"** (Official / Myth / Rival as attributed views). This is the layered model doing player-facing work for free.
- "Seen also in" strip: pages that link here.
- Footer of the page: last updated, and the no-spoilers line.

**Section index order.** A section whose pages are dated (History) is listed **oldest first**, with
undated pages last and ties broken by title; every tile repeats the page's date stamp, above its
title, so the grid reads as a timeline. A section without dates stays alphabetical. "Nearby"
(previous/next) follows the same order, so reading History forwards walks forward in time.

### 3.3 Themes (the public tag vocabulary)

A note's `tags:` are a hand-written index trail, not a taxonomy: 154 distinct tags across the vault, 66
of them used once, plus spelling variants (`gate`/`gates`, `wardstone`/`wardstones`). Published raw
they would make a tag meaningless. So **the exporter decides which tags publish**, the same
deny-by-default way it decides which sections do: `PUBLISHED_TAGS` in `tools/site_export.py`.

- **The public set is 18 cross-cutting themes**, drawn from the 68-tag vocabulary in
  [[tag-vocabulary]] — peoples (`elves`, `dwarves`, `gnomes`, `humans`,
  `fae`, `ketheri`), powers and places (`choir`, `gods`, `league`, `wardens`, `church`, `far-reach`,
  `heartland`, `saltmarch`), and broken machinery (`waygates`, `leylines`, `wardstones`, `ruins`).
- **Add one only when it earns a page:** it must cross sections (a theme that lives in one section is
  a worse copy of that section), be player-facing (never `truth-ledger`, `figures`, `plot`, `proof` —
  those are authoring labels), and never be a sealed keystone (`lineage`, `gate-born`). A published
  tag that no note carries fails `site_export.py --check` (`empty_tags`).
- **Everything else is withheld** and listed in the audit as `withheld_tags` (tag → notes). The vault
  stays the source of truth for the tags themselves; the site may change how a tag **reads**
  (`TAG_LABELS` in `site/src/lib/site.ts`: `league` → "The Crimson League") but never invents one.
- **Chips are links:** every published tag on a page links to `/tags/<tag>/`, which lists every entry
  carrying it, across sections. Chronological where dates exist, then A–Z (`byTimeThenTitle`), and
  each tile names its section. `/tags/` is the index of themes, linked from `/codex/`.
- **Tags are outside the changelog hash.** Refiling a note is not a lore revision. Tags are inside
  the keystone scan, though: a sealed term in a tag is a hit like any other.

**Voice:** lore pages in third person, present tense; the landing and About pages in direct address ("you"). **The one exception is testimony** (section 3.4), which is first person by definition and always attributed to a named teller.

**Testimony and voice sheets** (§3.4 and §3.5 of the document this was split out of) are the site's
one first-person device and the two checks that guard it. They are in `testimony.md`, because they
are about the *writing* rather than the page.

## 4. The landing page

**The world's.** What a landing page carries — the hero image, the wordmark, the tagline, the
doorways, the no-spoilers promise, the follow form — is a promise a world makes to its readers, and
one it keeps in its own note.

## 5. Visual direction

**The world's.** The palette, the type, the texture and the motion are in the world's own note. The
theme reads a world's look from its config and its stylesheet, so a world that wants another look
changes its own file, not the kit's.

## 6. Images


- Prompts live in **`site/image-prompts/`**, one note per image. Each note is both machine-readable and a checklist: frontmatter (model, aspect, resolution, count, crops), a `prompt` body, an `Avoid` list, a `Checks` table with a canon source per row, and an iteration log. The house style lives once, in `_style.md`; generated candidates live in `image-prompts/candidates/` and are **gitignored** (evidence, not deliverables). The process — four commands, the note shape, the prompt rules — is in `site/image-prompts/README.md`, which is the authority. Only accepted images reach `public/img/`.
- **One hero image for launch**, and it is a **drop-in**: a file named
  `site/public/img/hero-dust-road.{avif,webp,jpg,png,svg}` is used automatically; with no file the
  landing page draws an SVG scene instead. Alt text and credit live in `site/src/lib/site.ts`.
  Everything else is CSS until real art exists.
- Each accepted image yields three crops: 21:9 hero (≥3000 px), 16:9 social card, 4:5 mobile.
- **A plate reaches a page by being accepted, not by being placed.** The exporter (`tools/site_export.py`, `load_plates`) reads `site/image-prompts/*.md` and joins each plate whose frontmatter says `status: accepted` to the canon notes in its `canon:` list. It takes the crop named by `page_image:` (default `<output>-16x9.jpg`) and passes it into the page's generated frontmatter as `image` / `imageAlt`; `EntryLayout.astro` renders it above the body. The join is skipped when the crop file is missing, so a page can never carry a broken image, and an image path is never written into a lore note. To change which page shows a plate, edit its `canon:` list; to change the picture, edit `page_image:`; to pull it, set `status: iterating`.
- **Reject** any image that contradicts canon (metal towers, an ocean, green grass): the image is the first thing a reader trusts.
- Hand-drawn maps are the user's own work (later); the interim map may be generated as SVG from `maps/atlas-features.yaml` (see [[atlas-register]]) in Phase 4.

## 7. Stack and repository layout


```
site/                       Astro project; only this folder is published
  src/pages/                landing, about, follow, changelog, 404 (hand-written copy)
                            + codex/, [section]/, [section]/[slug]/ (templates)
                            + tags/, tags/[tag]/ (themes, built from published tags)
  src/components/           EntryCard, SearchBox, FollowForm
  src/layouts/              BaseLayout (nav, footer), EntryLayout (marginalia, TOC)
  src/lib/site.ts           site constants, inline-markdown helper, sort keys, date and tag labels
  src/styles/app.css        the Dust Road tokens and prose styles (Tailwind 4)
  src/content/generated/    exporter output (gitignored)
  src/data/generated/       navigation, changelog, redirects (gitignored)
  public/                   favicon and, later, art
  image-prompts/            the prompt library (tracked)
  audit/latest.json         the committed publish record
  audit/history.json        slug history and per-page dates
tools/site_export.py        the deterministic exporter
tools/test_site_export.py   its tests
```

`npm run dev` and `npm run build` both run the exporter first, so the generated collection is never
stale. Astro's static output is the only thing published; nothing in the vault is served directly.

**Stack:** Astro (static output) + Tailwind + **Pagefind** for search. Chosen over Eleventy and a hand-rolled Python generator for image handling, per-page social cards, and content collections. No CMS, no server, no database, no client-side framework.

The exporter reads the vault only. It writes `site/src/content/generated/`, plus `audit/latest.json`, `changelog.json`, `redirects.json` and `navigation.json`. **Slugs come from filenames**; when a page is renamed and its slug changes, the exporter writes a redirect stub (`<meta http-equiv="refresh">` + canonical) at the old path.

## 8. Deploy


- **AWS S3 + CloudFront**, set up in Phase 3. **Live at https://d13myumhho8nau.cloudfront.net** — no domain yet.
- Bucket `hollowfall-site` (private; CloudFront reads it through an origin access control) and distribution `E3R7X648RR10ZU`, both in `ap-southeast-2`. Setup, ids and commands: **`site/infra/README.md`**; the recorded state is `site/infra/state.json`.
- **Publishing is manual.** Nothing deploys on a push (`workflow_dispatch` only). A manual run builds and stops; ticking the `publish` input deploys: vault checks → export → build → **audit report into the job summary** → audit gate (fails on unresolved or ambiguous links) → internal link check → upload → sync → invalidate. It assumes **its own least-privilege role**, `hollowfall-site-deploy` (trust scoped to this repository, the `production` environment and `refs/heads/main`; permission to write the bucket and invalidate this one distribution, nothing else). No long-lived keys, and no dependency on any role another repository manages.
- **URLs:** an S3 REST origin has no directory index, so a CloudFront viewer-request function (`site/infra/index-rewrite.js`) appends `index.html` to directory requests; anything with a file extension passes through.
- **Caching:** hashed assets (`_astro/*`, pagefind fragments) immutable for a year; HTML, images and the pagefind entry files revalidate. Every deploy invalidates `/*`. 403 and 404 both serve `/404.html` with a 404 status.
- `./site/deploy.sh` is the workstation fallback; adding a domain is four steps in `site/infra/README.md`.
- Cache headers: hashed assets immutable for a year; HTML `no-cache`; invalidation of `/*` per deploy.
- Analytics: **none** in v1.

## 9. Refresh workflow


Lore changes every session, so publishing does too, but only when a human asks for it. `AGENTS.md` session protocol ends with a site refresh:

```
python3 tools/lint.py
python3 tools/disclosure.py --check
python3 tools/voice_lint.py           # every account against its teller's sheet; exit 1 on a break
python3 tools/voice_stale.py          # canon that moved after its account was written (a reading list)
python3 tools/site_export.py          # writes content + audit + changelog
npm --prefix site run build           # Pagefind runs here
# read site/audit/latest.json and the voice_stale list, then publish by hand:
gh workflow run site.yml -f publish=true
```

- `changelog.json` drives the site's changelog page, the "recently added" block in the Codex, each page's last-updated date, and the **RSS feed** (`/rss.xml`).
- A build that publishes nothing new is still a valid build (dates refresh, no changelog entry).
- **CI does not commit.** The session build on a workstation is what updates the committed `site/audit/*.json`; CI publishes the fresh audit to its job summary instead, which avoids commit loops.
- `python3 tools/site_audit_report.py` renders the audit; `--strict` fails on unresolved or ambiguous links. `python3 tools/site_link_check.py` walks `site/dist` and fails on any internal link to a file that does not exist.
- **`voice_stale.py` is a nag, not a gate.** Whether an account needs rewriting after a canon change is a judgement, and a check that blocks on judgement calls is disabled within a month. Run it, read the list, fix what matters.
- **`voice_lint.py` does fail the build-in-a-terminal**, like `lint.py`: a teller saying a word that is not hers, or naming a place she has never been, is unambiguously the author's error. It exits 0 when the only problem is a teller with no sheet (a warning).

## Links

- `conventions.md` §7 — the disclosure classes the publish axis rests on
- `testimony.md` — the accounts, the voice sheets and the two checks
- a world's own site note — its audience, its landing copy, its visual direction and its launch state

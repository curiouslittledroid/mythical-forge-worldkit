# Image prompts

The prompt library for a world's art. **One note per image**, and every note is both a machine-readable instruction and the checklist that judges the result.

Nothing here is published. Only accepted images move into `site/public/img/` and get wired into a page.

---

## 1. The loop in one picture

```
/image-prompt <slug>          author the note          site/image-prompts/NN-slug.md
        ↓
/image-run <slug>             compile → generate → look → score → log
        ↓                            candidates/           Iteration log
   you pick, and say what is wrong
        ↓
/image-iterate <slug> "<one change>"     new version, same checks
        ↓  (repeat until a candidate passes)
/image-accept <slug> <candidate>         crops, places, status: accepted
```

Four commands, all of them in this repo at `.pi/prompts/` (`image-prompt.md`, `image-run.md`, `image-iterate.md`, `image-accept.md`). Run `/reload` after changing any of them.

### What a session actually looks like

Real commands from the ward-post plate, in order. Each block is one thing you type.

```text
/image-prompt ward-post-plate 04
  → interview, then writes site/image-prompts/04-ward-post-plate.md
  → nothing is generated; it ends with the two things it expects to go wrong

/image-run ward-post-plate
  → one call, one candidate: candidates/ward-post-plate/v2-1.jpg
  → report: passes #2 #3 #4 #8; fails #1 (aperture is a niche, not a slot),
    #6 (far lane still lit), #7 (the run lid reads as an iron ladder)

/image-run ward-post-plate 4
  → same prompt, four candidates (only on a model that accepts n > 1)

/image-iterate ward-post-plate "strip the street-furniture nouns: a rough-cut standing stone, one iron cap, no straps, no rim, no steps, no finial"
  → v3, one clause changed and logged old → new, regenerated, compared to v2

/image-iterate ward-post-plate "make the moths larger and fewer" candidates/ward-post-plate/v2-1.jpg
  → v4 from v3's body, but with v2 fed in as a reference image,
    so the composition of v2 survives while the moths change

/image-accept ward-post-plate v2-1.jpg
  → checks, crops to 21:9, 16:9 and 4:5, writes site/public/img/plate-ward-post-*.webp,
    sets status: accepted and logs the accepted files
```

Short forms and variants worth knowing:

| You want | You type |
|---|---|
| Author and generate in one go | `/image-prompt ward-post-plate` then `/image-run ward-post-plate` — two commands; there is no combined shortcut, on purpose |
| Try another model on the same prompt | say so (`run it on riverflow`) rather than editing `model:` — the log's model column is only useful if the prompt stayed still |
| Append the `Avoid` list for one round | `run it with avoid appended` — the note's `avoid_appended` stays `false` |
| Change the look, not the content | edit `_style.md`, then `/reload`, then `/image-run` — **not** a new version of the plate |
| Look at the candidates yourself | `open -a Preview site/image-prompts/candidates/ward-post-plate/*.jpg`, then answer with the one you want and what is wrong with it |
| Park a plate | set `status: rejected` or `dropped` in the frontmatter; the note and its log stay |

---

## 2. The files

| Path | What it is |
|---|---|
| `README.md` | This file: the process and the rules. |
| `_style.md` | The house style blocks (`sketch`, `painted`, `plate`). The **only** place the look is defined. |
| `NN-slug.md` | One plate: frontmatter, `Must say`, `Prompt`, `Avoid`, `Checks`, `Variants`, `Notes`, `Iteration log`. |
| the world's reference plate | The plate it has already accepted. Every later plate copies its shape. |
| every other `NN-slug.md` | A world's own plate, one per image. **The world's file, never the kit's.** |
| `candidates/<slug>/v<N>-<i>.png` | Every generated candidate. **Ignored by git** — evidence, not deliverable. |

An accepted image is the only thing that leaves this folder: `site/public/img/<stem>-<ratio>.<ext>`.

---

## 3. The commands

### `/image-prompt <slug> [plate number]`

Interviews you, reads the canon notes the subject touches, and writes a new plate in the house shape. It picks a style block, sets the model, aspect, resolution and count, writes the prompt body in the fixed order, and builds the `Checks` table from canon. **It does not generate.**

Use it whenever a new image is wanted. If the image needs a fact the canon does not yet state — a height, a colour, a material — it adds one line to the canon note first, so the plate and the codex cannot drift apart.

### `/image-run <slug> [n]`

One round: **compile → generate → look → score → log**.

- Compiles the prompt: the note's ```prompt body + the style block named in `style:`, joined by a blank line. The `Avoid` list is **not** appended by default (`avoid_appended: false`), because naming a forbidden object summons it.
- Calls `generate_image` once with the note's model, aspect, resolution and count, writing to `candidates/<slug>/v<version>`.
- **Opens every candidate** and scores it against `Checks` and `Must say`, reporting what is *actually in the picture*.
- Appends a log row with verdict `pending`.

The run never edits the prompt. If a whole round fails the same check, the report names the clause responsible and proposes replacement words for the next version.

### `/image-iterate <slug> "<one change>" [reference candidate]`

One version is **one named change**, logged as `old clause → new clause` with the checks it is meant to reach. It edits only that clause, bumps `version:`, regenerates, and reports what moved — including regressions.

Pass a reference candidate when the **composition** is right and only a detail is wrong: the extension feeds it in as `input_references`, so the layout survives while the words change.

### `/image-accept <slug> <candidate>`

Verifies the checks and the crop rules one last time, crops to every ratio in `crops:` with `sips`, places the files in `site/public/img/`, wires the hero if it is plate 01, and sets `status: accepted`. It refuses to upscale: if a 21:9 crop needs 3000 px, you regenerate at `resolution: 4K` instead.

---

## 4. The shape of a plate

```markdown
---
plate: 04
slug: ward-post-plate
title: A ward-post at dusk
use: Chapter plate — Cosmology / Wardstones (Phase 4)
status: iterating          # proposed | iterating | accepted | rejected | dropped
version: 2
style: sketch              # a block name from _style.md
model: black-forest-labs/flux.2-pro
aspect: "3:2"
crops: ["21:9", "16:9", "4:5"]
resolution: 2K
n: 3
output: site/public/img/plate-ward-post
candidates: site/image-prompts/candidates/ward-post-plate
avoid_appended: false
canon: [world/cosmology/wardstones.md, world/places/settlements/stonehold.md]
---
```

| Section | Consumed by | How |
|---|---|---|
| `Must say` | `/image-run` critic | The claim a viewer must come away with |
| `Prompt` | `/image-run` | Sent verbatim. Content only — no style, no flags |
| `Avoid` | the critic, and you | A reviewer's list. Appended to the prompt only on recurrence |
| `Checks` | `/image-run`, `/image-iterate`, `/image-accept` | One row per canon claim, with its source note |
| `Variants` | humans | Deltas on the body, not whole prompts |
| `Notes` | humans | Rationale and canon anchors. Never sent to the API |
| `Iteration log` | the loop | Version, model, change, verdict, files |

---

## 5. Writing the prompt body

Order matters: late clauses get dropped.

**subject and scale → the object's parts → what is small and alive → the setting → light logic → composition and crop**

Then the style block, appended automatically.

- **Phrase positively.** Describe what is there. A forbidden object named in the body is a forbidden object supplied: `no glass panes` produced glazed lamp-posts twice. Prohibitions belong in `Avoid`.
- **Scale is a comparison.** "Waist high, a head shorter than a person" — not "small".
- **Count and size living things.** "A dozen moths, no larger than a thumbnail" — not "a drift of pale moths", which produced one moth the size of a dog.
- **State the light logic early.** "The only light in the scene comes from the posts; the sky is nearly black" is what makes the dark at the end of the street possible.
- **Name the one warm accent** where the light is, so it gets placed there.
- **No Midjourney flags.** `--ar`, `--v`, `--style`, `--stylize` are ignored by the OpenRouter image API and become literal prompt text. Aspect, resolution, model and count are tool parameters in the frontmatter.
- **Keep the body under ~250 words.** If it grows, something in it is not carrying canon.

---

## 6. Models

| Model | Good at | Use for | `n` |
|---|---|---|---|
| `black-forest-labs/flux.2-pro` | line work, hatching, strong sketch medium | sketch plates (the default here) | **1 only** — the API rejects `n > 1` |
| `sourceful/riverflow-v2.5-pro` | painted, atmospheric wide shots | establishing plates | check per call |
| `recraft/recraft-v4-pro` | illustration-trained, steady plate style | painted book plates | check per call |
| `google/gemini-3-pro-image` | following long, literal prompts | dense scenes with many clauses | multiple |

Models reject parameters they do not support, and the error names them (`No provider … supports the requested parameter(s)`). If `n > 1` fails, run the plate again rather than dropping the aspect ratio: variety for flux comes from repeated single calls.

The default model is whatever `/image-model-set` stored; a plate's `model:` field overrides it for that plate. Compare two models on the **same prompt** before changing a plate's model — the log's `model` column is only useful if the prompt stayed still.

---

## 7. Deliverables

| Use | Crop | Minimum |
|---|---|---|
| Hero | 21:9 | 3000 px wide |
| Social card / OG | 16:9 | 1200 × 630 |
| Mobile | 4:5 | 1200 wide — the subject must survive the centre crop |

Naming: `site/public/img/<stem>-<ratio>.<ext>`, for example `plate-ward-post-21x9.webp`. The hero is the exception: the landing page only picks up `site/public/img/hero-dust-road.{avif,webp,jpg,png,svg}` automatically, with `heroAlt` and `heroCredit` in `site/src/lib/site.ts`.

---

## 8. Rules that come from the canon

- **Colour:** bleached sand, bone, ash grey, charcoal, deep indigo and slate shadows, and **one** warm accent used sparingly. Nothing saturated, nothing neon.
- **Nothing modern.** No printed type, no glass-and-steel, no rubber-tyred wheels, no firearms.
- **No text in the image** — the wordmark is live text over the image, not painted into it.
- **Leave negative space** for the wordmark: the left third of any hero crop must survive being covered by a title.
- **Reject any image that contradicts canon:** an ocean where the Dry Sea is, green grassland in the Heartland, metal towers, floating rocks, glowing runes, a flame where the light comes from salt. The image is the first thing a reader trusts.
- **One cause per object.** If a detail cannot be traced to a note, it is not in the picture.

---

## 9. Troubleshooting (from real rounds)

| What you see | What caused it | What to do |
|---|---|---|
| Glazed panes, a framed window, a lamp housing | lamp vocabulary in the body (`vent`, `panel`, `housing`, `capstone`), or `no glass` in the prompt | delete the vocabulary; describe the emission positively: *a slot cut clean through the stone, open to the air* |
| Riveted machine casing, boilers, pipes | "iron-bound", "banded", "iron straps" read as industry | say **rusted iron straps over dressed stone**, and give the stone the detail instead |
| One huge moth, or a dense swarm | no size, no count | "a dozen, no larger than a thumbnail" |
| Gold, coins or gems at the base | "a smear of glowing dust" is ambiguous | "a thin dusting of scraped moth-dust on the paving, faintly glowing" |
| The far street is grey, not black | ambient dusk light in the prompt | state the light logic first, then "past the third post the lane is solid unbroken black" |
| Crops are wrong or square | flags in the prompt instead of parameters | set `aspect` in the frontmatter; never write `--ar` |
| Two versions look identical | the change was too small, or it was a style change in the body | change one clause that a `Checks` row tests; style changes go in `_style.md` |
| A fix breaks something that passed | the change reached further than its clause | log it as a regression; split the change into two versions next time |
| Gratings, manhole covers, mosaic bands, turned finials, a letterbox or gas-lamp silhouette | the body uses street-furniture nouns (`bollard`, `straps`, `iron rim`, `slab`, `steps`, `cap`) and the model's prior for "lit post" is Victorian | strip those nouns; write a **rough-cut standing stone** with a single iron cap and no turned shapes |
| The far end is bright although the prompt says black | a lit object was placed there (steps, a building, a wall lamp) | remove the object, not the adjective: light at the end of the lane must not exist in the body at all |
| Two versions differ unpredictably | two clauses moved in one version | one named change per version, logged `old → new`; revert the second to a separate version |
| A long flush metal strip becomes a ladder, rails or track | a **long linear metal feature in perspective**; the model reads rails into it every time | keep it **short and single**, cut off by the frame — never a line running to the horizon |
| The nearest object is dark and the light floats mid-frame | the prompt never says that the **near** post is the lit one | "the light leaves the slot in the near post and lies in a cone on the paving at its foot" |
| Two reference images produce a chimera | references import their pictures wholesale; text cannot override them | **one reference at a time**, and only for what it gets right. Everything else goes in text |
| The subject loses its body and becomes a pure light shape | a reference showed a bright aperture, and the aperture won the identity contest | drop that reference; describe the stone first, the glow second |
| **The one change you made does not appear at all** | a reference was passed, and it has no such object, so the model kept the reference's surfaces | run that round **without** a reference, or make the new object the largest thing in the foreground |
| A signature or squiggle sits in a corner | image models sign their output; not text you wrote | every style block ends `no signature`; crop it at accept time if it still appears |
| Adding content made the whole picture brighter | the model lights what it must show; new architecture becomes new ambient light | restate darkness positively in the same round: *the facades are black unlit shapes, the windows are black, there is no moonlight* |
| An object reads as a drain, a lamp, a bollard — generic, not specific | the object is shown **alone**, with no destination and no system around it | show it **repeated towards where it leads**: the same object in a line running to a lit post says *this feeds that*, where one object says *furniture*. The structural fix is usually worth more than any adjective |
| A small element in the body never appears | prompts drop late, small clauses first; and features compete for words | give it **its own paragraph, a position in the frame and a size**; if it still loses, shoot it as its own plate |

---

## 10. Putting an accepted plate on a page

The site does **not** hard-code images per page, and a lore note never holds an image path. The join happens at export time, from this library:

| Field in the plate note | What it does |
|---|---|
| `status: accepted` | the only status that publishes. `iterating`, `proposed`, `rejected` and `dropped` never do |
| `canon: [paths]` | the notes this image illustrates. **Every** note listed gets the plate, so list only the ones you want it on |
| `page_image:` | which crop to use on the page (default `<output stem>-16x9.jpg`) |
| `alt:` | the alt text. Write it as a sentence describing what is in the picture, not as a title |

What happens on `npm run export` (or `npm run build`, which runs it first):

1. `tools/site_export.py` (`load_plates`) reads every `*.md` here except `README.md` and `_`-prefixed files.
2. A plate is used only if it is `accepted` **and** the crop file exists in `site/public/img/`. Otherwise it is skipped silently — a missing crop cannot publish a broken `<img>`.
3. The page's generated frontmatter gains `image:` and `imageAlt:`; `EntryLayout.astro` renders it as a figure above the body.
4. `site/audit/latest.json` records `plates` as `{note, image}` pairs, so the publish record shows which images shipped.

So the whole procedure for a new page image is: accept the plate (`/image-accept`), make sure it has `canon:` and `alt:`, then `npm run build`. To take an image off the site again, set its status back to `iterating` — do not delete the files.

An accepted plate is the worked example: `status: accepted`, and its `canon:` lists the world's own notes
that license what the image shows, with `page_image:` naming the file it produced.

## 11. Housekeeping

- **Candidates are gitignored** (`candidates/`). They are evidence for the log, not deliverables — keep the ones a log row cites, delete the rest when a plate is accepted.
- **The note and the accepted image must agree.** If you accept something generated from a variant, update `## Prompt` to what actually produced it.
- **Older plates 01–03 are still in the pre-`Checks` shape.** Convert each to the current shape the next time it is touched; do not leave a new plate in the old shape.
- **`/reload`** after editing anything in `.pi/prompts/` or `_style.md`.

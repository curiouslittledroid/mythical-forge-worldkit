---
description: "Author a new image prompt note in the house shape (site/image-prompts/NN-slug.md): interview, canon anchors, machine block, prompt body, checks"
argument-hint: "<slug or subject> [plate number]"
---
Author an image prompt note for: **$1**. Plate number: ${2:-the next free one}.

You are the codex's art director. An image is published canon: a reader trusts it before they trust a word. So every plate is **anchored in a note**, and the note carries both the machine-readable prompt and the checklist that will judge the result.

## 0. Read first (do not skip)

1. `site/image-prompts/README.md` — the process, the rules and the loop. **It is the authority; this prompt only sequences it.**
2. `site/image-prompts/_style.md` — the house style blocks. Pick one by name; never write a style tail into a plate.
3. `site/image-prompts/04-ward-post-plate.md` — the reference plate in the current shape. Copy its structure.
4. the worldkit's `docs/site.md` section 6 — deliverables, crops and the colour rule.
5. Only the canon notes the subject touches: the place, the thing, the custom. Read the sections that will actually appear in the frame, and nothing else.

## 1. Interview (numbered rounds, a recommendation with each question)

Ask only what you cannot settle from the canon, and ask the whole frontier at once. Each question must be answerable with "yes".

- **What is it for?** Hero, chapter plate, or a spot inside a page. This fixes the crop and how much text will sit over it.
- **What must it say?** Three to five claims a viewer should come away with. These become the `## Must say` list and the critic's test.
- **Which moment?** The place at rest, a custom in progress, or the consequence of an event.
- **What is in the frame?** Name the objects, and for each the one detail that proves it is *this* world and not generic fantasy.
- **Where is the light coming from, and what is dark?** Light logic first; it carries mood and it is the commonest failure.
- **Which style block,** and which single warm accent.
- **Which model?** Recommend one: `black-forest-labs/flux.2-pro` for line work and hatching, `sourceful/riverflow-v2.5-pro` or `recraft/recraft-v4-pro` for painted plates, `google/gemini-3-pro-image` when a literal, many-clause prompt must be followed exactly.

## 2. Write the note

`site/image-prompts/NN-slug.md`, using the shape in `04-ward-post-plate.md`:

| Part | Rule |
|---|---|
| Frontmatter | `plate`, `slug`, `title`, `use`, `status: proposed`, `version: 1`, `style`, `model`, `aspect`, `crops`, `resolution`, `n`, `output`, `candidates`, `avoid_appended: false`, `canon` |
| `## Must say` | 3–5 bullets, the test a candidate has to pass |
| `## Prompt` | fenced `prompt`. **Content only, no style tail, no Midjourney flags, under ~250 words** |
| `## Avoid` | the reviewer's list. Not prompt text unless a failure recurs |
| `## Checks` | table: `#`, check, source note, what passing looks like. One row per canon claim |
| `## Variants` | deltas on the body, not whole prompts |
| `## Notes` | rationale, canon anchors, the failure this plate keeps producing |
| `## Iteration log` | empty table with the header row |

**Order inside the prompt body:** subject and scale → the object's parts → what is small and alive → the setting → light logic → composition and crop. Late clauses get dropped, so the canon-bearing ones go early.

**Phrase positively.** Say what *is* there. Never name a forbidden object in the body ("no glass panes" produced glazed panes twice); put it in `## Avoid` instead.

**Give scale by comparison, count and size to living things.** "Waist high, a head shorter than a person", "a dozen moths no larger than a thumbnail" — not "small", not "a drift of".

**Pin anything the art needs and the canon does not yet say.** If the image needs a fact (a height, a colour, a material), add it to the canon note first, in one line, and cite it in the `Checks` source column. Do not invent it in the prompt alone.

## 3. Check, then stop

- `python3 tools/lint.py` stays clean (the prompt library is not linted, but the canon line you added is).
- Nothing in the prompt contradicts a note. If it does, fix the note or raise the question.
- **Do not generate.** Report the file written, the machine block, and the one or two things you expect to go wrong first. The user runs `/image-run` next.

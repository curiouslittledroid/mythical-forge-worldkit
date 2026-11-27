---
description: "Accept a candidate: crop it to the declared ratios, place it under site/public/img, wire it if it is the hero, mark the note accepted"
argument-hint: "<plate slug> <candidate file or version>"
---
Accept a candidate for **$1**: **$2**

## 1. Verify first

Open the candidate and re-run the note's `## Checks` table one last time, plus the kit's `meta/conventions/site.md` section 6:

- Nothing in the image contradicts canon. The image is the first thing a reader trusts — reject rather than rationalise.
- Crops survive: the hero's **left third** stays uncluttered for the wordmark; the subject survives a 4:5 centre crop.
- **Resolution.** Ratios needing ≥3000 px wide cannot come from a 1024–1536 px generation. Do **not** upscale: regenerate the accepted prompt at `resolution: 4K`, or at the note's `aspect`, and start again from step 1.

## 2. Crops

Use `sips` (macOS, no dependencies). Name from the note's `output` stem:

```sh
# 21:9 hero: choose the centre band that keeps the subject
sips -c <h> <w> in.png --out site/public/img/<stem>-21x9.png
sips --resampleWidth 3000 site/public/img/<stem>-21x9.png
# then convert to webp for weight
sips -s format webp site/public/img/<stem>-21x9.png --out site/public/img/<stem>-21x9.webp
```

Produce every ratio in the note's `crops` list: `21x9`, `16x9`, `4x5`. Check each one by eye — a crop that decapitates the subject is not a crop, it is a new composition.

## 3. Place and wire

- Files go to `site/public/img/`, named `<stem>-<ratio>.<ext>` per the kit's `meta/conventions/site.md` section 6.
- **Only plate 01 is the hero.** For the hero, set `heroAlt` and `heroCredit` in `site/src/lib/site.ts`; the landing page picks the file up on the next build.
- Every other plate is a page asset: say which page uses it, and wire it in that page's frontmatter or component only if the site already supports a plate slot. If it does not, report where it will go and leave the file in place.

## 4. Record

- Frontmatter: `status: accepted`, and add the accepted files to the note's `## Iteration log` (verdict `accept`, with the crop paths).
- Keep the rejected candidates on disk. They are the evidence for why the prompt says what it says.
- If the accepted prompt differs from the note's current `## Prompt`, the note must be updated to match what was actually generated. Never leave a note whose prompt no longer produces its accepted image.

## 5. Verify the build

If the image is wired into a page: `npm --prefix site run build`, then confirm the file appears in the built output and the page still loads. Report the paths produced and any ratios you had to skip.

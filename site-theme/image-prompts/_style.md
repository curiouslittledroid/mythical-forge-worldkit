# House style tail

**What this file is:** the one home for the house medium, appended to every plate's own prompt body.
**How it is used:** `/image-run` and `/image-iterate` read the block named by a note's `style:` field and append it to the end of the prompt body, separated by one blank line.
**What never happens:** a style tail pasted into a plate note, or a plate edited to fix the look. Change the look here and the whole set moves together.

## Blocks

### `sketch` — the default for plates, maps and diagrams

```style
Artist's sketch, not photorealistic: confident graphite linework with visible construction lines, hatching and cross-hatching, ink wash for the shadow masses, warm toned grey paper with visible grain, restricted palette of graphite black and cool grey wash with one warm colour accent scumbled over the light only, rough unfinished edges at the margins, sketchbook study plate, no rendering, no airbrush, no photographic surfaces, no text, no logos, no watermark, no signature.
```

### `painted` — painted book plate, for wide establishing shots

```style
Painted book plate, muted oil on linen with visible brushwork, limited palette, gilded-age survey plate, soft varnish, soft edges, quiet and melancholy, no rendering, no airbrush, no photographic surfaces, no text, no logos, no watermark, no signature.
```

### `plate` — architectural study, for objects and mechanisms

```style
Architectural study sketch: fine ink over graphite construction, ruled survey lines, hatched shadow, one flat wash of warm grey, hand-lettered-free, measured and dry, warm toned grey paper with visible grain, no rendering, no airbrush, no photographic surfaces, no text, no logos, no watermark, no signature.
```

## Rules of thumb

- **Medium negations are safe, object negations are not.** `no rendering`, `not photorealistic` work: they steer the medium. `no glass panes` does the opposite — it supplies the object, and the model draws it. Object prohibitions belong in a plate's `## Avoid` section, which is a reviewer checklist, not prompt text.
- **One warm accent, always.** The site palette is bleached sand, bone, ash grey, charcoal, deep indigo and slate shadows, plus **one** warm accent (`docs/site.md` §5, visual direction). Name the accent in the plate body so it is scumbled where the light is: honey-amber for wardstone light, ember-orange for fire and gates.
- **Never write Midjourney flags.** `--ar`, `--style`, `--v`, `--stylize` are ignored by the OpenRouter image API and passed through as literal prompt text. Aspect ratio, resolution, model and count are tool parameters, set in the plate's machine block.
- **Never bake text into the image.** The wordmark and headings are live text over the image. Flux draws an artist's signature unprompted; every block ends `no signature`, and a signature that survives is cropped at accept time.
- **Keep it under about 250 words for the body.** The tail is around 60. Long prompts lose clauses; put the clauses that carry canon first.

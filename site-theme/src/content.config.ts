import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

/**
 * The generated collection. Written by tools/site_export.py, never edited by hand, and
 * gitignored — run `npm run export` (or `npm run build`, which does it first) to fill it.
 */
const pages = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/generated' }),
  schema: z.object({
    id: z.string(),
    kind: z.string(),
    title: z.string(),
    section: z.string(),
    slug: z.string(),
    summary: z.string().default(''),
    updated: z.string(),
    era: z.string().optional(),
    t0: z.string().optional(),
    tags: z.array(z.string()).default([]),
    // An accepted plate from site/image-prompts/, joined by tools/site_export.py.
    image: z.string().optional(),
    imageAlt: z.string().default(''),
    // Where 'From the Reader's book' links to: the hub page, resolved by the exporter from the
    // note that declares `testimony_source: true`. Never hard-coded in the layout.
    testimonySource: z.string().optional(),
    // An account quoted from the Reader's book, lifted out of a `## Testimony` section by the
    // exporter (meta/site.md section 3.4). The layout shows the quote at the head and the whole
    // account after the body.
    testimony: z
      .object({
        teller: z.string().default(''),
        transmission: z.string().default(''),
        // The entry heading exactly as he wrote it: date, then person, then place.
        heading: z.string().default(''),
        quote: z.string().default(''),
        // The year the account was taken, in Concord Years. 0 = undated, which the audit reports.
        taken: z.number().default(0),
        // He hedged the date ('or near it'), so the byline prints `c. CY 601`.
        approx: z.boolean().default(false),
        paragraphs: z.array(z.string()).default([]),
      })
      .optional(),
  }),
});

export const collections = { pages };

# Third-party notices

This site is the worldkit's theme, covered by the kit's MIT licence (`LICENSE` at the kit's root,
copied into a world as `tools/LICENSE`). What it *builds* depends on the packages below — all
permissive, all shipped by npm, whose copies in `site/node_modules/` carry their own full licence
texts.

| Package | Licence |
|---|---|
| `astro` | MIT |
| `tailwindcss`, `@tailwindcss/vite` | MIT |
| `@astrojs/rss` | MIT |
| `pagefind` | MIT |
| `@fontsource/ibm-plex-sans`, `-condensed`, `-serif` | SIL Open Font License 1.1 |

## The fonts, which need saying out loud

The bundled typefaces are **IBM Plex**, and the OFL asks that its notice travel with the fonts. The
built site copies the web fonts into `_astro/` and serves them, so here is the notice:

> Copyright 2019 IBM Corp. All rights reserved. This Font Software is licensed under the SIL Open
> Font License, Version 1.1. It is available with a FAQ at <https://scripts.sil.org/OFL>.

The full text is in `node_modules/@fontsource/ibm-plex-*/LICENSE`. A world's own About page should
carry the one-line credit in its colophon, which is where a reader of the site will look.

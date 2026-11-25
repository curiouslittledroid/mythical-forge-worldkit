# The site theme

The player-facing site for a world codex: an **Astro** project that renders the pages
`tools/site_export.py` generates. It is the kit's, and it carries **no world's branding** — every
world value arrives generated, in `src/data/generated/site.json`, from the world's
`world.config.yaml` and its `site-vocabulary` block. To change how the site reads, change the
world's config, not this theme.

The mechanism — the publish axis, the redaction rules, the audit, the page shape, the stack and the
deploy — is `docs/site.md`. A world's own page choices are its own note.

## Run it

From the world's root (the theme lives at `site/`):

```bash
npm --prefix site install
npm --prefix site run dev      # exports the vault, then serves on 0.0.0.0:4321
npm --prefix site run build    # export -> astro build -> pagefind index, into site/dist/
npm --prefix site run preview
```

`dev` and `build` both run the exporter first, so the generated collection is never stale; neither
works without it. `server.host: true` in `astro.config.mjs` binds the dev server to all interfaces,
so a draft can be read on a phone: `http://<your-ip>:4321/`. It never affects `astro build`.

## What is hand-written and what is generated

| Path | Provenance |
|---|---|
| `src/content/generated/` | **generated** (gitignored) — one page per `open` disclosure section |
| `src/data/generated/` | **generated** (gitignored): `site.json`, `navigation.json`, `changelog.json`, `redirects.json` |
| `audit/latest.json`, `audit/history.json` | **generated and committed**: the publish record and slug history |
| `src/pages/index.astro`, `about.astro`, `follow.astro` | **the world's copy**, and the sync leaves them alone: the landing text, About, Follow. The kit ships a neutral version of each |
| `src/pages/codex/`, `[section]/`, `tags/`, `changelog.astro`, `404.astro` | templates over generated content |
| `src/styles/app.css` | the design tokens — the world's look |
| `src/lib/site.ts` | pure logic (sorting, dates, inline markdown). It reads `site.json`; it authors nothing |

## The hero image

Drop-in, no code change: `site/public/img/<site.hero_file>.<avif|webp|jpg|png|svg>`, where
`hero_file` comes from the world's config (default `hero`). With no file present the landing page
draws an SVG scene. Alt text and credit are config values too (`hero_alt`, `hero_credit`).

The prompt that produces the art is the world's own note in `site/image-prompts/`; the process is
`site/image-prompts/README.md`, and the house style is `site/image-prompts/_style.md`.

## Deploying

`site/infra/README.md` is the process: a private S3 bucket read through CloudFront, set up once by
`bootstrap.sh`, with the ids recorded in `site/infra/state.json`. `.github/workflows/site.yml`
publishes **manually only** (Actions → Site → Run workflow), reading the publish audit first, and
takes every value from repository variables (`SITE_URL`, `SITE_BUCKET`, `AWS_DEPLOY_ROLE_ARN`,
`AWS_REGION`, `CLOUDFRONT_DISTRIBUTION_ID`).

From a workstation: `./site/deploy.sh`.

## Before deploying

1. `python3 tools/site_export.py` then the build.
2. `python3 tools/site_audit_report.py` — **read** the keyword hits and the design citations. A
   build may be deployed only after the audit has been read (`docs/site.md` section 2.3).
3. `python3 tools/site_link_check.py` — must report 0 dead links.

## Replacing the theme

A world that wants its own theme replaces `site/src/**` wholesale; the contract is small and written
down: the exporter writes `site/src/content/generated/`, `site/src/data/generated/site.json` and the
audit, and the theme reads them. The sync will overwrite `site/src/**`, so a replacement theme is
kept in `site/local-theme/` and pointed at, or the sync's theme step is dropped for that world.

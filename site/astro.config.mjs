// @ts-check
import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';

import { loadConfig } from '../tools/kit_config.mjs';

// The site URL is needed for absolute links in the RSS feed and the social card. It comes from
// the world's config; $SITE_URL overrides it (CI sets it to the deployed hostname, which may
// differ from the one a world has recorded). No domain yet is a normal state: a CloudFront
// hostname stands in until a real one lands (meta/site.md section 8).
const cfg = loadConfig();
const SITE_URL = process.env.SITE_URL || cfg.site?.url;
if (!SITE_URL) {
  throw new Error('no site URL: set site.url in world.config.yaml, or $SITE_URL');
}

export default defineConfig({
  site: SITE_URL,
  trailingSlash: 'always',
  build: { format: 'directory' },
  // Dev and preview bind 0.0.0.0 rather than localhost, so a phone or a second machine on the
  // LAN can read a draft: `http://<your-ip>:4321/`. No effect on `astro build` output. Access by
  // IP; a `.local` hostname would also need `allowedHosts: ['.local']` (Vite's host check).
  server: { host: true },
  vite: { plugins: [tailwindcss()] },
  markdown: {
    // The codex has no code samples on player pages; keep the output lean.
    syntaxHighlight: false,
  },
  devToolbar: { enabled: false },
});

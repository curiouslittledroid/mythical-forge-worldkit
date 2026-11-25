#!/usr/bin/env node
/**
 * Checks every ```yaml block in a guide that starts with `kind:` against the engine's own schema
 * (`@mythical-forge/authored-content`), so a tutorial cannot teach an invalid block.
 * Codex directives (keys that start with `_`) are stripped first, as the transformer does.
 *
 * Usage:  node tools/check-guide.mjs [guide.md ...]     (default: the authoring guide, see below)
 *
 * The guide is a worldkit document, so its home is `<kit>/docs/campaign-authoring-guide.md`. A world
 * vendors it at `tools/docs/`, so both layouts are resolved; the older staging path is still
 * accepted so an older checkout keeps working.
 */
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import { loadConfig, mfRoot, requireMf } from './kit_config.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, '..');
const cfg = loadConfig();
const YAML = requireMf('yaml');
const { parseAuthoredEntity } = requireMf(join(mfRoot(), 'packages', 'authored-content', 'dist', 'index.js'));

/** First path that exists, so one tool serves the worldkit, the staged kit and a world. */
const firstExisting = (...paths) => paths.find((p) => existsSync(p));
const DOC_DIRS = [join(ROOT, 'docs'), join(ROOT, 'tools', 'docs'), join(ROOT, 'worldkit', 'docs')];
const KIT_GUIDE = DOC_DIRS.map((d) => join(d, 'campaign-authoring-guide.md')).find(existsSync);
// In the kit this is the demo world; in a world it is that world's own vault. Same paths either way.
const SOURCES = [join(ROOT, 'world'), join(ROOT, 'campaigns'),
                 join(ROOT, 'meta', 'templates', 'examples')].filter(existsSync);

const strip = (v) => {
  if (Array.isArray(v)) return v.map(strip);
  if (v && typeof v === 'object') return Object.fromEntries(Object.entries(v).filter(([k]) => !k.startsWith('_')).map(([k, x]) => [k, strip(x)]));
  return v;
};

// Source blocks: the demo world's notes. A guide block with the same id must match the note it was
// copied from, so a tutorial cannot teach a block the kit does not ship.
const walk = (d) => (existsSync(d) ? readdirSync(d, { withFileTypes: true }).flatMap((e) => (e.isDirectory() ? walk(join(d, e.name)) : e.name.endsWith('.md') ? [join(d, e.name)] : [])) : []);
const sorted = (v) => (Array.isArray(v) ? v.map(sorted) : v && typeof v === 'object' ? Object.fromEntries(Object.keys(v).sort().map((k) => [k, sorted(v[k])])) : v);
const sources = new Map();
for (const f of SOURCES.flatMap(walk)) {
  for (const m of readFileSync(f, 'utf8').matchAll(/```engine\n([\s\S]*?)```/g)) {
    const obj = strip(YAML.parse(m[1]));
    if (obj?.id) sources.set(obj.id, JSON.stringify(sorted(obj)));
  }
}

if (!KIT_GUIDE) {
  console.error('check-guide: cannot find campaign-authoring-guide.md (looked in ./docs, ./tools/docs,' +
                ' ./worldkit/docs); pass the path as an argument');
  process.exit(2);
}
const files = process.argv.slice(2).length ? process.argv.slice(2) : [KIT_GUIDE];
let checked = 0;
let bad = 0;
for (const file of files) {
  const text = readFileSync(file, 'utf8');
  const fence = /```yaml\n([\s\S]*?)```/g;
  let m;
  while ((m = fence.exec(text)) !== null) {
    const body = m[1];
    const first = body.split('\n').find((l) => l.trim() && !l.trim().startsWith('#'));
    if (!first || !first.startsWith('kind:')) continue;
    const line = text.slice(0, m.index).split('\n').length + 1;
    const result = parseAuthoredEntity(strip(YAML.parse(body)));
    checked += 1;
    const parsed = strip(YAML.parse(body));
    if (parsed?.id && sources.has(parsed.id) && sources.get(parsed.id) !== JSON.stringify(sorted(parsed))) {
      bad += 1;
      console.error(`✗ ${file}:${line}  block ${parsed.id} differs from its source note (re-copy it)`);
    }
    if (!result.success) {
      bad += 1;
      console.error(`✗ ${file}:${line}  (${first})`);
      for (const i of result.issues) console.error(`    ${i.path}: ${i.message}`);
    }
  }
}
console.log(`${checked} block(s) checked: ${bad} invalid`);
process.exit(bad ? 1 : 0);

#!/usr/bin/env node
/**
 * The world config seam, in Node (T1). The counterpart of `kit_config.py`.
 *
 *   import { loadConfig, worldRoot, mfRoot } from './kit_config.mjs';
 *
 *   const cfg = loadConfig();          // world.config.yaml, parsed
 *   cfg.world.id, cfg.world.overland, cfg.vault.notes.flags
 *   cfg.gameReadyRepo                  // resolved absolute path
 *
 *   const root = mfRoot();             // $MYTHICAL_FORGE_ROOT, or a loud error
 *
 * ## Why there is a second YAML reader
 *
 * `world.config.yaml` uses the same strict subset as `yaml_subset.py`, and both languages need to
 * read it: the Python tools because the linter must not depend on Node, the Node tools because a
 * subprocess for every transform is worse than sixty lines of parser. The two must agree — a
 * parity test in `test_kit_config.py` runs this file with `--json` and compares it with the
 * Python parse, so a divergence fails the suite rather than corrupting a build.
 *
 * Anything outside the subset throws with a `file:line`, rather than being guessed at.
 */
import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

export const HERE = dirname(fileURLToPath(import.meta.url));
export const WORLD_ROOT = resolve(HERE, '..');

// ─── the subset reader ───────────────────────────────────────────────────────────────

const NUMBER_RE = /^-?\d+(\.\d+)?$/;
const KEY_RE = /^([A-Za-z_][A-Za-z0-9_.-]*)\s*:(?:\s|$)/;

/** Drop a trailing `# ...` comment: a `#` preceded by whitespace, outside quotes. */
function stripComment(raw) {
  let out = '';
  let quote = null;
  for (let i = 0; i < raw.length; i += 1) {
    const ch = raw[i];
    if (quote) {
      if (ch === quote) quote = null;
    } else if (ch === '"' || ch === "'") {
      quote = ch;
    } else if (ch === '#' && i > 0 && (raw[i - 1] === ' ' || raw[i - 1] === '\t')) {
      break;
    }
    out += ch;
  }
  return out;
}

function scalar(raw, where) {
  const v = raw.trim();
  if (!v) return null;
  if (v.startsWith('"') && v.endsWith('"') && v.length >= 2) return v.slice(1, -1).replace(/\\"/g, '"');
  if (v.startsWith("'") && v.endsWith("'") && v.length >= 2) return v.slice(1, -1).replace(/''/g, "'");
  if (v.startsWith('[') && v.endsWith(']')) {
    const inner = v.slice(1, -1).trim();
    if (!inner) return [];
    return inner.split(',').map((p) => scalar(p, where));
  }
  if (v === 'null' || v === '~') return null;
  if (v === 'true') return true;
  if (v === 'false') return false;
  if (NUMBER_RE.test(v)) return v.includes('.') ? Number.parseFloat(v) : Number.parseInt(v, 10);
  if (v.includes(': ') || v.endsWith(':')) {
    throw new Error(`${where}: unquoted colon in value: ${JSON.stringify(raw)}`);
  }
  return v;
}

/** Parse the strict YAML subset. `name` appears in every error message. */
export function parseSubset(text, name = '<text>') {
  const lines = text.split('\n');
  const content = (from) => {
    for (let i = from; i < lines.length; i += 1) {
      if (!lines[i].trim() || lines[i].trimStart().startsWith('#')) continue;
      return [i + 1, lines[i].trim()];
    }
    return null;
  };

  const first = content(0);
  const root = first && first[1].startsWith('- ') ? [] : {};
  const topKeys = new Map();
  const stack = [[-1, root]];

  lines.forEach((raw, idx) => {
    const lineno = idx + 1;
    const where = `${name}:${lineno}`;
    if (!raw.trim() || raw.trimStart().startsWith('#')) return;
    if (raw.includes('\t')) throw new Error(`${where}: tab character`);
    const indent = raw.length - raw.trimStart().length;
    const text_ = raw.trim();

    while (stack.length && indent <= stack[stack.length - 1][0] && stack[stack.length - 1][0] >= 0) {
      stack.pop();
    }
    const parent = stack[stack.length - 1][1];

    if (text_.startsWith('- ')) {
      if (!Array.isArray(parent)) throw new Error(`${where}: sequence item outside a list`);
      const body = stripComment(text_.slice(2)).trim();
      if (!body) {
        const item = {};
        parent.push(item);
        stack.push([indent, item]);
        return;
      }
      const m = KEY_RE.exec(body);
      if (!m) {
        parent.push(scalar(body, where)); // a scalar item carries no children
        return;
      }
      const item = { [m[1]]: scalar(body.slice(m[1].length + 1), where) };
      parent.push(item);
      stack.push([indent, item]);
      return;
    }

    if (!text_.includes(':')) throw new Error(`${where}: expected 'key: value'`);
    if (indent === 0 && !Array.isArray(root)) {
      const key0 = text_.split(':')[0].trim();
      if (topKeys.has(key0)) {
        throw new Error(`${where}: duplicate top-level key '${key0}' (first at line ${topKeys.get(key0)})`);
      }
      topKeys.set(key0, lineno);
    }
    const colon = text_.indexOf(':');
    const key = text_.slice(0, colon).trim();
    // Strip the comment BEFORE deciding block-vs-scalar, so `site:  # a note` still opens a block.
    const rest = stripComment(text_.slice(colon + 1)).trim();

    if (!(parent instanceof Object) || Array.isArray(parent)) {
      throw new Error(`${where}: key '${key}' outside a mapping`);
    }
    if (rest) {
      parent[key] = scalar(rest, where);
      return;
    }
    const nxt = content(lineno);
    const container = nxt && nxt[1].startsWith('- ') ? [] : {};
    parent[key] = container;
    stack.push([indent, container]);
  });

  return root;
}

// ─── the authored-content schemas: a checkout, or the installed package (T2, Phase 5 B4) ─────

/**
 * The engine's schemas come from one of two places, and this is the only code that decides which.
 *
 *   1. **`$MYTHICAL_FORGE_ROOT` set** — a local checkout of the platform repository, for developing
 *      an unreleased schema change. Set-but-wrong is a loud error, never `Cannot find module`.
 *   2. **unset** — the published `@curiouslittledroid/authored-content`, an ordinary dependency of
 *      this repository. This is what lets the whole pipeline run with no checkout of anything but
 *      the world itself, which is what makes `tools/verify-world.sh` usable in CI (task 5.B4).
 *
 * Nothing here reads a token: the package lives on GitHub Packages, so installing it is what needs
 * one. `authoredContent()` loads the schemas; `requireMf(spec)` loads `yaml` — which the package
 * depends on, so it is resolved through the package's own closure rather than by hoping for a
 * hoist.
 *
 * ## Who the error below is written for
 *
 * This file is vendored into every world, so its message is read by an AUTHOR — someone who has a
 * lorem vault and no checkout of the private platform repository. It therefore names one fix: the
 * packaged install. A checkout (`mfRoot`) is the kit maintainer's route, and the maintainer hears
 * about it from `verify-kit.sh`, which is the kit's own script. A message that offered both sent
 * authors looking for a directory they do not have, which is why the test asserts the variable is
 * NOT named here.
 */
const AUTHORED_CONTENT = '@curiouslittledroid/authored-content';

/** The checkout root, or null when the consumer did not ask for one. */
export function mfRoot() {
  const root = process.env.MYTHICAL_FORGE_ROOT;
  if (!root) return null;
  const hint = 'Point MYTHICAL_FORGE_ROOT at the directory that holds packages/authored-content, e.g.\n'
    + '  MYTHICAL_FORGE_ROOT=/path/to/mythical-forge/main node tools/transform.mjs\n'
    + 'In a bare-repo-plus-worktree checkout that is the worktree (…/mythical-forge/main), not the parent.\n'
    + 'Or unset it to use the installed package instead.';
  const pkg = join(root, 'packages', 'authored-content', 'package.json');
  if (!existsSync(pkg)) {
    throw new Error(`MYTHICAL_FORGE_ROOT is '${root}', but there is no ${pkg}.\n${hint}`);
  }
  return root;
}

/** The `require` the schemas and `yaml` are loaded through: the checkout's, or the package's own. */
function schemaRequire() {
  const root = mfRoot();
  if (root) return createRequire(join(root, 'packages', 'authored-content', 'package.json'));
  const own = createRequire(import.meta.url);
  let entry;
  try {
    entry = own.resolve(AUTHORED_CONTENT);
  } catch {
    throw new Error(
      `${AUTHORED_CONTENT} is not installed, so the engine pipeline cannot run yet.\n`
      + 'The engine’s own schemas are one ordinary npm dependency. Install it once,\n'
      + 'from the folder that holds this project’s package.json:\n'
      + '\n'
      + '  export NODE_AUTH_TOKEN=<a GitHub token with read:packages on @curiouslittledroid>\n'
      + '  npm install\n'
      + '\n'
      + '`.npmrc` already sends @curiouslittledroid to npm.pkg.github.com and hands npm the token\n'
      + 'above; never commit a token, and a 401 from that registry means it is missing, expired, or\n'
      + 'lacks read:packages. Writing and checking lore does not wait on this — lint, citations,\n'
      + 'disclosure and the site build all run without it. Transform, validate, thread-check and the\n'
      + 'scenarios are what need the schemas.');
  }
  // Anchored at the package's own entry so `yaml` comes from its dependency closure.
  return createRequire(entry);
}

/** Require a module by name — `yaml`, or anything else the engine's install provides. */
export function requireMf(spec) {
  return schemaRequire()(spec);
}

/** The schemas: `parseAuthoredEntity`, `parseWorldManifest`, `ENTITY_SCHEMAS`, `formatIssues`, … */
export function authoredContent() {
  const root = mfRoot();
  if (root) return schemaRequire()(join(root, 'packages', 'authored-content', 'dist', 'index.js'));
  return schemaRequire()(AUTHORED_CONTENT);
}

// ─── the scenario conventions (T4) ───────────────────────────────────────────────────

/**
 * The quest-gates sidecar beside a set of scenarios, or null.
 *
 * The sidecar is world content and sits next to the scenarios it belongs to, so the file is found
 * from the directory being run rather than from a fixed path. `pilot-` wins when a directory holds
 * more than one, which is how the pilot's sidecar has always been named.
 */
export function gatesFile(dir) {
  if (!dir || !existsSync(dir)) return null;
  const names = readdirSync(dir)
    .filter((f) => f.endsWith('.yaml') && f.includes('quest-gates'))
    .sort();
  if (!names.length) return null;
  return join(dir, names.find((f) => f.startsWith('pilot-')) ?? names[0]);
}

// ─── the world config ────────────────────────────────────────────────────────────────

const FEATURES = new Set(['site', 'atlas', 'testimony', 'voice']);
const SPELLING = new Set(['british', 'american', 'off']);
const BLOCK_INFO = {
  flags: 'flags',
  calendar: 'chronology',
  eras: 'eras',
  site_vocabulary: 'site-vocabulary',
};

/** Resolve the config path: $WORLD_CONFIG, then world.config.yaml beside this file. */
export function configPath(path) {
  return resolve(path ?? process.env.WORLD_CONFIG ?? join(WORLD_ROOT, 'world.config.yaml'));
}

/**
 * Load and validate the world's config. Throws on anything missing or unknown — a typo must not
 * become a silently ignored setting.
 */
export function loadConfig(path) {
  const file = configPath(path);
  if (!existsSync(file)) throw new Error(`no world config at ${file} (set $WORLD_CONFIG to point at one)`);
  const data = parseSubset(readFileSync(file, 'utf8'), file);
  const root = dirname(file);

  const bad = (msg) => {
    throw new Error(`${file}: ${msg}`);
  };
  if (data.version !== 1) bad(`version must be 1, found ${JSON.stringify(data.version)}`);
  const world = data.world;
  if (!world || typeof world !== 'object') bad('`world:` is missing');
  for (const key of ['id', 'title', 'slug']) if (!world[key]) bad(`world.${key} is required`);
  const vault = data.vault;
  if (!vault || typeof vault !== 'object') bad('`vault:` is missing');
  if (!vault.notes || !vault.notes.flags) bad('vault.notes.flags is required (by id)');

  const features = data.features ?? [];
  if (!Array.isArray(features)) bad('`features:` must be a list');
  for (const f of features) if (!FEATURES.has(f)) bad(`unknown feature '${f}'`);
  if (data.site && !features.includes('site')) bad('a `site:` section needs the `site` feature');
  if (features.includes('site') && !data.site) bad('the `site` feature needs a `site:` section');

  const gameReadyRepo = resolve(
    root,
    world.game_ready_repo ?? join('..', `${world.slug}-gameready`),
  );

  const spelling = String(vault.spelling ?? 'british').toLowerCase();
  if (!SPELLING.has(spelling)) bad(`vault.spelling must be one of ${[...SPELLING]}, found '${vault.spelling}'`);
  const scenariosDir = vault.scenarios ? resolve(root, vault.scenarios) : null;

  return {
    ...data,
    path: file,
    root,
    gameReadyRepo,
    /** The world's scenario directory, or null. The one world-declared directory (T4). */
    scenariosDir,
    spelling,
    /** `overland` defaults to overland_<id without its world_ prefix>. */
    overlandId: world.overland ?? `overland_${String(world.id).replace(/^world_/, '')}`,
    has: (feature) => features.includes(feature),
    require: (feature) => {
      if (!features.includes(feature)) {
        throw new Error(`${file}: this tool needs the '${feature}' feature; add it to \`features:\``);
      }
    },
  };
}

/** Every note id in the vault -> its path. Mirrors `Config.id_index()`. */
export function noteIndex(root = WORLD_ROOT) {
  const index = new Map();
  const walk = (dir) => {
    if (!existsSync(dir)) return;
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      const full = join(dir, entry.name);
      if (entry.isDirectory()) walk(full);
      else if (entry.name.endsWith('.md')) {
        const head = readFileSync(full, 'utf8').slice(0, 2000);
        const fm = /^---\s*\n([\s\S]*?)\n---\s*(\n|$)/.exec(head);
        const id = fm && /^id:\s*(\S+)\s*$/m.exec(fm[1]);
        if (id && !index.has(id[1])) index.set(id[1], full);
      }
    }
  };
  for (const scope of ['principles', 'world', 'campaigns', 'maps', 'meta']) walk(join(root, scope));
  return index;
}

/** The note a config name points at, resolved by id. */
export function notePath(cfg, name) {
  const id = cfg.vault?.notes?.[name];
  return id ? noteIndex(cfg.root).get(id) ?? null : null;
}

/** The text of the first fenced block whose info string is `info`. */
export function readBlock(path, info) {
  if (!path || !existsSync(path)) return null;
  const text = readFileSync(path, 'utf8');
  const re = /^```(\S+)[ \t]*\n([\s\S]*?)^```[ \t]*$/gm;
  let m;
  while ((m = re.exec(text)) !== null) {
    if (m[1] === info) return m[2];
  }
  return null;
}

/** Parse the block a config name carries (`flags`, `calendar`, `eras`, `site_vocabulary`). */
export function block(cfg, name) {
  const info = BLOCK_INFO[name];
  if (!info) return null;
  const path = notePath(cfg, name);
  const raw = readBlock(path, info);
  if (raw === null) return null;
  return parseSubset(raw, `${path} (${info} block)`);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const cfg = loadConfig();
  console.log(JSON.stringify({
    world_id: cfg.world.id,
    title: cfg.world.title,
    slug: cfg.world.slug,
    overland: cfg.overlandId,
    game_ready_repo: cfg.gameReadyRepo,
    features: cfg.features,
    notes: cfg.vault.notes,
    process_docs: cfg.vault.process_docs ?? [],
    scenarios_dir: cfg.scenariosDir,
    spelling: cfg.spelling,
    site: cfg.site ?? null,
    // Every block, so `test_kit_config.py` can prove the two readers agree.
    blocks: Object.fromEntries(Object.keys(BLOCK_INFO).map((n) => [n, block(cfg, n)])),
  }, null, 2));
}

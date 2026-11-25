#!/usr/bin/env node
/**
 * Step 2a pilot: validate a generated Game Ready Repository.
 *
 * Reads every YAML file in the repository and validates it with the platform's own schemas
 * (`@mythical-forge/authored-content`), so the codex is checked against the engine's reader
 * rather than a copy of it. It also does the reference-integrity check the package
 * deliberately leaves to the bundle validator (does every referenced id exist?).
 *
 * Usage:  node tools/validate-world.mjs [--repo <game-ready-repo>]
 * Env:    MYTHICAL_FORGE_ROOT  REQUIRED: the directory holding packages/authored-content
 *         WORLD_CONFIG         (default world.config.yaml beside this file)
 *         GAME_READY_REPO      (default world.game_ready_repo from the world config)
 */
import { readFileSync, readdirSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import { loadConfig, mfRoot, requireMf } from './kit_config.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const CODEX_ROOT = resolve(HERE, '..');
const cfg = loadConfig();

const YAML = requireMf('yaml');
const dist = join(mfRoot(), 'packages', 'authored-content', 'dist', 'index.js');
const { parseAuthoredEntity, parseWorldManifest } = requireMf(dist);

const args = process.argv.slice(2);
const outIndex = args.indexOf('--repo');
const GAME_READY_REPO = resolve(
  outIndex >= 0 ? args[outIndex + 1] : process.env.GAME_READY_REPO ?? cfg.gameReadyRepo,
);

function yamlFiles(dir) {
  const out = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) out.push(...yamlFiles(full));
    else if (entry.isFile() && entry.name.endsWith('.yaml')) out.push(full);
  }
  return out.sort();
}

let errors = 0;
let checked = 0;
const ids = new Set();
const references = []; // { from, field, id }

// Manifest first.
const manifestPath = join(GAME_READY_REPO, 'manifest.yaml');
const manifestResult = parseWorldManifest(YAML.parse(readFileSync(manifestPath, 'utf8')));
if (!manifestResult.success) {
  errors += 1;
  console.error(`✗ manifest.yaml`);
  for (const issue of manifestResult.issues) console.error(`    ${issue.path}: ${issue.message}`);
}
checked += 1;

// Every other YAML file is one authored entity.
import { existsSync } from 'node:fs';
const contentDirs = [join(GAME_READY_REPO, 'world'), join(GAME_READY_REPO, 'campaigns')].filter((d) => existsSync(d));
for (const path of contentDirs.flatMap((d) => yamlFiles(d))) {
  const raw = YAML.parse(readFileSync(path, 'utf8'));
  const result = parseAuthoredEntity(raw);
  checked += 1;
  if (raw && typeof raw.id === 'string') ids.add(raw.id);
  if (raw && raw.kind === 'OVERLAND_GRAPH') {
    for (const node of raw.nodes ?? []) if (node?.id) ids.add(node.id);
  }
  if (!result.success) {
    errors += 1;
    console.error(`✗ ${path.replace(GAME_READY_REPO + '/', '')}`);
    for (const issue of result.issues) console.error(`    ${issue.path}: ${issue.message}`);
    continue;
  }
  const e = result.data;
  if (e.kind === 'OVERLAND_GRAPH') {
    for (const edge of e.edges ?? []) {
      references.push({ from: e.id, field: 'edge.from', id: edge.from });
      references.push({ from: e.id, field: 'edge.to', id: edge.to });
    }
  }
  for (const field of ['npc_id', 'from', 'to', 'origin']) {
    if (typeof e[field] === 'string' && e[field] !== 'PLAYER') {
      references.push({ from: e.id ?? path, field, id: e[field] });
    }
  }
  for (const field of ['known_by', 'believed_by', 'subjects']) {
    for (const id of e[field] ?? []) {
      if (typeof id === 'string' && id !== 'PLAYER') references.push({ from: e.id ?? path, field, id });
    }
  }
}

// Reference integrity (the package leaves this to the bundle validator).
// In the pilot, world-layer entities deliberately reference factions and NPCs outside the
// slice, so dangling references are reported as warnings, not failures. Step 14's validator
// makes them hard errors.
let dangling = 0;
for (const ref of references) {
  if (!ids.has(ref.id)) {
    dangling += 1;
    console.warn(`⚠ ${ref.from}: ${ref.field} references '${ref.id}', which no entity in the slice defines`);
  }
}

console.log(
  `${checked} entities checked: ${errors} schema error(s), ${dangling} dangling reference(s)`,
);
if (errors > 0) process.exit(1);

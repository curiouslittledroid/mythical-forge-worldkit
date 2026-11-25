#!/usr/bin/env node
/**
 * Step 2a pilot: a minimal, deterministic codex → Game Ready Repository transformer.
 *
 * It scans `world/` and `campaigns/` for notes whose frontmatter says `engine: true`,
 * extracts the fenced `engine` blocks, assembles the overland fragments into one
 * OVERLAND_GRAPH entity, resolves `_known_by_groups` / `_believed_by_groups` to NPC ids,
 * converts km to whole miles, and writes the Design 23 §4.1 Game Ready Repository layout.
 *
 * It is deliberately NOT the Step 14 pipeline: no campaigns, overlays, migrations, CI or
 * canonical hashing. It exists to find friction points. See `meta/pilot-findings.md`.
 *
 * Usage:  node tools/transform.mjs [--out <game-ready-repo>]
 * Env:    MYTHICAL_FORGE_ROOT  REQUIRED: the directory holding packages/authored-content
 *         WORLD_CONFIG         (default world.config.yaml beside this file)
 *         GAME_READY_REPO      (default world.game_ready_repo from the world config)
 */
import { readFileSync, writeFileSync, mkdirSync, rmSync, readdirSync, statSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import { loadConfig, requireMf } from './kit_config.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const CODEX_ROOT = resolve(HERE, '..');
const cfg = loadConfig();

// Use the platform's own YAML implementation, so output matches the engine's reader.
const YAML = requireMf('yaml');

const KM_PER_MILE = 1.609344;
const RANK = { common: 0, select: 1, inner: 2 };
const FLAGS_NOTE_ID = cfg.vault.notes.flags;

const args = process.argv.slice(2);
const outIndex = args.indexOf('--out');
const GAME_READY_REPO = resolve(
  outIndex >= 0 ? args[outIndex + 1] : process.env.GAME_READY_REPO ?? cfg.gameReadyRepo,
);

const EMIT_THREAD_LABEL = process.env.EMIT_THREAD_LABEL === '1';
/** thread slug → entity ids (the codex's thread membership; PF-6). */
const threadMembers = new Map();
/** thread slug → { note, interface } from each thread note's frontmatter. */
const threadInfo = new Map();
const warnings = [];
const warn = (message) => warnings.push(message);

// ─── Reading the vault ──────────────────────────────────────────────────────────

function markdownFiles(dir) {
  const out = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (entry.name === 'node_modules' || entry.name.startsWith('.')) continue;
    const full = join(dir, entry.name);
    if (entry.isDirectory()) out.push(...markdownFiles(full));
    else if (entry.isFile() && entry.name.endsWith('.md')) out.push(full);
  }
  return out.sort();
}

function parseNote(path) {
  const raw = readFileSync(path, 'utf8');
  const fm = /^---\r?\n([\s\S]*?)\r?\n---\r?\n?/.exec(raw);
  if (!fm) return null;
  let frontmatter;
  try {
    frontmatter = YAML.parse(fm[1]) ?? {};
  } catch (error) {
    throw new Error(`${path}: frontmatter is not valid YAML: ${error.message}`);
  }
  const blocks = [];
  const fence = /^```([a-z0-9-]*)\r?\n([\s\S]*?)^```[ \t]*$/gm;
  let match;
  while ((match = fence.exec(raw)) !== null) {
    blocks.push({ info: match[1], body: match[2] });
  }
  return { path, frontmatter, blocks };
}

function parseBlock(note, block, index) {
  try {
    return YAML.parse(block.body);
  } catch (error) {
    throw new Error(`${note.path}: engine block #${index + 1} is not valid YAML: ${error.message}`);
  }
}

const notes = [
  ...markdownFiles(join(CODEX_ROOT, 'world')),
  ...markdownFiles(join(CODEX_ROOT, 'campaigns')),
].map(parseNote).filter(Boolean);

// ─── Group knowledge resolution (conventions §9.5) ──────────────────────────────

/** group id → [{ npc, rank }] from every NPC note, engine-ready or not. */
const factionMembers = new Map();
/** race id → [npc id] from the NPC frontmatter `race:` field. */
const raceMembers = new Map();

for (const note of notes) {
  const { id, kind, groups, race } = note.frontmatter;
  if (kind !== 'NPC' || typeof id !== 'string') continue;
  for (const group of Array.isArray(groups) ? groups : []) {
    if (!group || typeof group.id !== 'string') continue;
    const list = factionMembers.get(group.id) ?? [];
    list.push({ npc: id, rank: group.rank });
    factionMembers.set(group.id, list);
  }
  if (typeof race === 'string') {
    const list = raceMembers.get(race) ?? [];
    list.push(id);
    raceMembers.set(race, list);
  }
}

function resolveGroup(group, tier) {
  if (group.startsWith('race_')) {
    const members = raceMembers.get(group);
    if (!members || members.length === 0) {
      warn(`group knowledge: no named NPC has race '${group}' (a race has no tiers)`);
      return [];
    }
    return members;
  }
  const needed = RANK[tier] ?? 0;
  const members = factionMembers.get(group) ?? [];
  const known = members.filter((m) => (RANK[m.rank] ?? 0) >= needed).map((m) => m.npc);
  if (known.length === 0) {
    warn(`group knowledge: '${group}' has no named NPC at tier '${tier}' or above`);
  }
  return known;
}

function applyGroupDirectives(entity, note) {
  if (entity._known_by_groups !== undefined) {
    const ids = new Set(entity.known_by ?? []);
    for (const entry of entity._known_by_groups) {
      for (const npc of resolveGroup(entry.group, entry.tier)) ids.add(npc);
    }
    entity.known_by = [...ids].sort();
    delete entity._known_by_groups;
  }
  if (entity._believed_by_groups !== undefined) {
    const ids = new Set(entity.believed_by ?? []);
    for (const entry of entity._believed_by_groups) {
      for (const npc of resolveGroup(entry.group, entry.tier)) ids.add(npc);
    }
    entity.believed_by = [...ids].sort();
    delete entity._believed_by_groups;
    if (entity.believed_by.length === 0 && entity.believed_as !== undefined) {
      warn(
        `${note.path}: believed_as would be dropped — no named NPC resolves for _believed_by_groups ` +
          `(a Fact's believed_as is invalid without believed_by)`,
      );
      delete entity.believed_as;
    }
  }
  return entity;
}

/** `_thread` directive or the note's `thread:` frontmatter → membership (and, once the platform accepts it, a `thread:` label). */
function applyThread(entity, note) {
  const label = entity._thread ?? note.frontmatter.thread;
  delete entity._thread;
  if (entity.kind === 'CAMPAIGN_OVERLAY') {
    for (const add of entity.adds ?? []) applyThread(add, note);
    return entity;
  }
  if (typeof label === 'string' && entity.id && !['CAMPAIGN', 'MODULE', 'CAMPAIGN_OVERLAY'].includes(entity.kind)) {
    threadMembers.set(label, [...(threadMembers.get(label) ?? []), { id: entity.id, kind: entity.kind }]);
    if (EMIT_THREAD_LABEL) entity.thread = label;
  }
  return entity;
}

// ─── Extract and assemble ───────────────────────────────────────────────────────

const entities = [];
/** campaign slug (folder under campaigns/) → { id, entities: [] } — Step 12a: campaigns, overlays, modules, quests. */
const campaigns = new Map();
const nodes = new Map();
const edges = new Map();
let flags = [];

for (const note of notes) {
  const { frontmatter } = note;
  if (frontmatter.id === FLAGS_NOTE_ID) {
    const block = note.blocks.find((b) => b.info === 'flags');
    if (block) flags = parseBlock(note, block, 0) ?? [];
    continue;
  }
  if (frontmatter.kind === 'THREAD' && typeof frontmatter.thread === 'string') {
    threadInfo.set(frontmatter.thread, { note: frontmatter.id, interface: frontmatter.interface ?? {} });
  }
  if (frontmatter.engine !== true) continue;

  const rel = note.path.slice(CODEX_ROOT.length + 1).split('/');
  const campaignSlug = rel[0] === 'campaigns' && rel.length > 2 ? rel[1] : null;
  const noteModule = { id: null };

  note.blocks.forEach((block, i) => {
    if (block.info !== 'engine') return;
    const entity = parseBlock(note, block, i);
    if (!entity || typeof entity !== 'object') {
      throw new Error(`${note.path}: engine block #${i + 1} is not a mapping`);
    }
    if (campaignSlug) {
      if (!campaigns.has(campaignSlug)) campaigns.set(campaignSlug, { id: null, entities: [] });
      const camp = campaigns.get(campaignSlug);
      if (entity.kind === 'CAMPAIGN') camp.id = entity.id;
      if (entity.kind === 'MODULE') noteModule.id = entity.id;
      camp.entities.push({ entity: applyThread(applyGroupDirectives(entity, note), note), module: entity.kind === 'MODULE' ? entity.id : noteModule.id });
      return;
    }
    switch (entity.kind) {
      case 'OVERLAND_NODE':
        if (nodes.has(entity.id)) throw new Error(`duplicate overland node '${entity.id}'`);
        nodes.set(entity.id, {
          id: entity.id,
          name: entity.name,
          type: entity.type,
          ...(entity.description !== undefined ? { description: entity.description } : {}),
          ...(entity.zone_id !== undefined ? { zone_id: entity.zone_id } : {}),
        });
        break;
      case 'OVERLAND_EDGE': {
        const key = [entity.from, entity.to].sort().join('|');
        if (edges.has(key)) throw new Error(`duplicate overland edge '${key}' (edges are undirected)`);
        if (entity.distance_km === undefined) throw new Error(`edge ${key} has no distance_km`);
        edges.set(key, {
          from: entity.from,
          to: entity.to,
          distance_miles: Math.max(1, Math.round(entity.distance_km / KM_PER_MILE)),
          terrain: entity.terrain ?? 'STANDARD',
          ...(entity.danger !== undefined ? { danger: entity.danger } : {}),
        });
        break;
      }
      default:
        // YAML 1.2 reads a bare TRUE as a boolean; normalise so the Game Ready Repository is explicit.
        if (entity.kind === 'FACT' && entity.truth === true) entity.truth = 'TRUE';
        entities.push(applyThread(applyGroupDirectives(entity, note), note));
    }
  });
}

entities.push({
  kind: 'OVERLAND_GRAPH',
  id: cfg.overlandId,
  nodes: [...nodes.values()].sort((a, b) => a.id.localeCompare(b.id)),
  edges: [...edges.values()].sort((a, b) => `${a.from}|${a.to}`.localeCompare(`${b.from}|${b.to}`)),
});

function relationId(entity) {
  const strip = (id) => id.replace(/^[a-z]+_/, '');
  return `rel_${strip(entity.from)}_${String(entity.kind_of).toLowerCase()}_${strip(entity.to)}`;
}

// The compiler derives an id for an anonymous Relationship; do the same so files are stable.
for (const entity of entities) {
  if (!entity.id) entity.id = relationId(entity);
}
entities.sort((a, b) => a.id.localeCompare(b.id));

// ─── Emit the Game Ready Repository ──────────────────────────────────────────────────

if (statSync(GAME_READY_REPO, { throwIfNoEntry: false }) === undefined) {
  throw new Error(`Game Ready Repository not found: ${GAME_READY_REPO}`);
}

const DIR_FOR_KIND = {
  NPC: 'npcs',
  FACTION: 'factions',
  WANT: 'wants',
  FACT: 'facts',
  RELATIONSHIP: 'relationships',
  WORLD_EVENT: 'events',
  ITEM: 'items',
  MONSTER: 'monsters',
};

function yamlDoc(value) {
  return YAML.stringify(value, { lineWidth: 0 });
}

rmSync(join(GAME_READY_REPO, 'world'), { recursive: true, force: true });
rmSync(join(GAME_READY_REPO, 'campaigns'), { recursive: true, force: true });
rmSync(join(GAME_READY_REPO, 'manifest.yaml'), { force: true });
mkdirSync(join(GAME_READY_REPO, 'world'), { recursive: true });

const manifest = { schema_version: 1, world_id: cfg.world.id, title: cfg.world.title, flags };
writeFileSync(join(GAME_READY_REPO, 'manifest.yaml'), yamlDoc(manifest));

let written = 0;
for (const entity of entities) {
  let dir;
  let file;
  if (entity.kind === 'OVERLAND_GRAPH') {
    dir = 'world';
    file = 'overland.yaml';
  } else {
    dir = join('world', DIR_FOR_KIND[entity.kind] ?? 'misc');
    const id = entity.id;
    file = `${id}.yaml`;
  }
  mkdirSync(join(GAME_READY_REPO, dir), { recursive: true });
  writeFileSync(join(GAME_READY_REPO, dir, file), yamlDoc(entity));
  written += 1;
}

// Campaigns (Design 23 §4.1): campaign.yaml, overlay.yaml, modules/<id>/{module.yaml,quests/}.
for (const camp of campaigns.values()) {
  if (!camp.id) throw new Error('a campaigns/ folder has no CAMPAIGN entity');
  for (const { entity, module } of camp.entities) {
    let path;
    switch (entity.kind) {
      case 'CAMPAIGN': path = join('campaigns', camp.id, 'campaign.yaml'); break;
      case 'CAMPAIGN_OVERLAY': path = join('campaigns', camp.id, 'overlay.yaml'); break;
      case 'MODULE': path = join('campaigns', camp.id, 'modules', entity.id, 'module.yaml'); break;
      case 'QUEST': path = join('campaigns', camp.id, 'modules', module ?? '_unassigned', 'quests', `${entity.id}.yaml`); break;
      default: {
        const dir = DIR_FOR_KIND[entity.kind] ?? 'misc';
        path = join('campaigns', camp.id, 'modules', module ?? '_unassigned', dir, `${entity.id}.yaml`);
      }
    }
    mkdirSync(dirname(join(GAME_READY_REPO, path)), { recursive: true });
    writeFileSync(join(GAME_READY_REPO, path), yamlDoc(entity));
    written += 1;
    entities.push(entity); // counted in the summary
  }
}

// Codex tooling sidecar (NOT a Design 23 entity): which entities belong to which thread, and each thread's
// interface. It lives at the repository root, outside world/ and campaigns/, so the platform ignores it.
rmSync(join(GAME_READY_REPO, 'codex-threads.yaml'), { force: true });
if (threadMembers.size > 0) {
  const sidecar = {};
  for (const [slug, members] of [...threadMembers].sort()) {
    const byKindMap = {};
    for (const m of members) (byKindMap[m.kind] ??= []).push(m.id);
    for (const k of Object.keys(byKindMap)) byKindMap[k].sort();
    sidecar[slug] = { ...(threadInfo.get(slug) ?? {}), members: byKindMap };
  }
  writeFileSync(join(GAME_READY_REPO, 'codex-threads.yaml'), '# Generated by tools/transform.mjs. Codex tooling only; not an authored entity.\n' + yamlDoc(sidecar));
}

const byKind = entities.reduce((acc, e) => ({ ...acc, [e.kind]: (acc[e.kind] ?? 0) + 1 }), {});
console.log(`Wrote ${written} entities to ${GAME_READY_REPO}`);
console.log(`  ${Object.entries(byKind).map(([k, n]) => `${n} ${k}`).join(', ')}`);
console.log(`  ${flags.length} flags, ${nodes.size} overland nodes, ${edges.size} edges`);
for (const [slug, members] of [...threadMembers].sort()) console.log(`  thread ${slug}: ${members.length} entities${EMIT_THREAD_LABEL ? ' (label emitted)' : ''}`);
for (const message of warnings) console.log(`  warning: ${message}`);
if (warnings.length > 0) console.log(`  ${warnings.length} warning(s) — see meta/pilot-findings.md`);

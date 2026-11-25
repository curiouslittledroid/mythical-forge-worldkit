#!/usr/bin/env node
/**
 * Step 12a: static checks for plot-web threads, over a generated Game Ready Repository.
 *
 *  1. Flag registry   every flag is declared; every flag that is read has a producer; every flag
 *                     that is set has a consumer (or is a declared thread OUTPUT); every declared
 *                     flag is used. Producers include the `engine-example` blocks of notes that are
 *                     not converted yet (reported as "planned"), so a half-converted world does not
 *                     look broken.
 *  2. Own-stage guard every World Event (and every Want with a fallback flag) must test `not
 *                     flag_set X` for a flag X that it sets itself. That makes it safe to start a
 *                     Campaign past that stage (fast-forward) and safe against late re-evaluation.
 *  3. References      every id used inside a Condition or Effect resolves to an entity.
 *  4. Interface       the thread note's frontmatter `interface` (arms / reads / sets) matches what
 *                     the thread's blocks actually do.
 *
 * Usage:  node tools/thread-check.mjs [--repo <game-ready-repo>]
 */
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import { gatesFile, loadConfig, requireMf } from './kit_config.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const CODEX_ROOT = resolve(HERE, '..');
const cfg = loadConfig();
const YAML = requireMf('yaml');
const args = process.argv.slice(2);
const ri = args.indexOf('--repo');
const REPO = resolve(ri >= 0 ? args[ri + 1] : process.env.GAME_READY_REPO ?? cfg.gameReadyRepo);

function walk(dir, ext) {
  if (!existsSync(dir)) return [];
  const out = [];
  for (const e of readdirSync(dir, { withFileTypes: true })) {
    if (e.name.startsWith('.') || e.name === 'node_modules') continue;
    const full = join(dir, e.name);
    if (e.isDirectory()) out.push(...walk(full, ext));
    else if (e.name.endsWith(ext)) out.push(full);
  }
  return out.sort();
}

// ─── Load the repository ─────────────────────────────────────────────────────────

const entities = [];
for (const f of [...walk(join(REPO, 'world'), '.yaml'), ...walk(join(REPO, 'campaigns'), '.yaml')]) {
  const e = YAML.parse(readFileSync(f, 'utf8'));
  if (!e?.kind) continue;
  if (e.kind === 'CAMPAIGN_OVERLAY') for (const a of e.adds ?? []) entities.push({ ...a, _from: 'overlay' });
  entities.push(e);
}
const manifest = YAML.parse(readFileSync(join(REPO, 'manifest.yaml'), 'utf8'));
const declared = new Set((manifest.flags ?? []).map((f) => f.id));
const ids = new Set(entities.map((e) => e.id).filter(Boolean));
for (const g of entities.filter((e) => e.kind === 'OVERLAND_GRAPH')) for (const n of g.nodes ?? []) ids.add(n.id);
// The proposed Quest `available_when` sidecar, beside the world's scenarios (T4). Its reads are
// counted as *planned*, so a flag read only by a not-yet-available Quest is not reported as dead.
const GATES = gatesFile(cfg.scenariosDir);
const QUEST_GATES = GATES && existsSync(GATES) ? YAML.parse(readFileSync(GATES, 'utf8')) : {};

// Codex notes: thread interface frontmatter, and engine-example blocks (planned producers/consumers).
const threadNotes = [];
const plannedSet = new Set();
const plannedRead = new Set();
for (const f of walk(join(CODEX_ROOT, 'world'), '.md')) {
  const raw = readFileSync(f, 'utf8');
  const fm = /^---\r?\n([\s\S]*?)\r?\n---/.exec(raw);
  if (!fm) continue;
  let front = {};
  try { front = YAML.parse(fm[1]) ?? {}; } catch { continue; }
  if (front.kind === 'THREAD' && front.interface) threadNotes.push({ id: front.id, title: front.title, interface: front.interface, path: f });
  for (const m of raw.matchAll(/```engine-example\n([\s\S]*?)```/g)) {
    for (const s of m[1].matchAll(/set_flag:\s*\{\s*flag:\s*([a-z0-9_]+)/g)) plannedSet.add(s[1]);
    for (const s of m[1].matchAll(/flag_(?:set|count_gte):\s*\{\s*flag:\s*([a-z0-9_]+)/g)) plannedRead.add(s[1]);
  }
}

// ─── Walk Conditions and Effects ─────────────────────────────────────────────────

const sets = new Map(); // flag -> [source]
const reads = new Map();
const posReads = new Map(); // flag -> [source], counting only reads that are not under a `not`
const refs = []; // { source, id }
const push = (m, k, v) => m.set(k, [...(m.get(k) ?? []), v]);

function walkCond(c, source, neg = false) {
  if (!c) return;
  const [name] = Object.keys(c);
  const v = c[name];
  if (name === 'all' || name === 'any') v.forEach((x) => walkCond(x, source, neg));
  else if (name === 'not') walkCond(v, source, !neg);
  else if (name === 'flag_set' || name === 'flag_count_gte') { push(reads, v.flag, source); if (!neg) push(posReads, v.flag, source); }
  else if (name === 'edge_exists') { refs.push({ source, id: v.from }, { source, id: v.to }); }
  else if (name === 'npc_alive' || name === 'fact_revealed' || name === 'event_occurred') refs.push({ source, id: v });
  else if (name === 'in_location') { refs.push({ source, id: v.location }); if (v.entity !== 'PLAYER') refs.push({ source, id: v.entity }); }
  else if (name === 'quest_state') refs.push({ source, id: v.quest });
}
function walkEffects(list, source) {
  for (const e of list ?? []) {
    const [name] = Object.keys(e);
    const v = e[name];
    if (name === 'set_flag') push(sets, v.flag, source);
    else if (name === 'add_edge' || name === 'remove_edge' || name === 'reveal_edge') refs.push({ source, id: v.from }, { source, id: v.to });
    else if (['reveal_fact', 'activate_want', 'resolve_want', 'fail_want', 'start_quest', 'unlock_module'].includes(name)) refs.push({ source, id: v });
    else if (name === 'move_npc') refs.push({ source, id: v.npc }, { source, id: v.to });
    else if (name === 'emit_ripple') refs.push({ source, id: v.origin }, { source, id: v.event });
    else if (name === 'adjust_disposition') refs.push({ source, id: v.npc });
  }
}

// Wants from the Step 2a Dustport slice that belong to threads not yet written as cards. They are reported, not failed.
const LEGACY = new Set(['want_quillon_prove_registrar', 'want_tarwick_hold_inspection', 'gatewrights_go_dark', 'wardens_inspection_ordered']);
const legacyNotes = [];

for (const e of entities) {
  const src = e.id ?? e.kind;
  if (e.kind === 'WORLD_EVENT') {
    walkCond(e.when, src);
    walkEffects(e.then, src);
    refs.push({ source: src, id: e.origin }, ...(e.known_by ?? []).map((id) => ({ source: src, id })));
  } else if (e.kind === 'WANT') {
    if (e.urgent_when) walkCond(e.urgent_when, src);
    walkEffects(e.on_deadline, src);
    refs.push({ source: src, id: e.npc_id });
    for (const p of e.resolution_paths ?? []) if (typeof p === 'string') refs.push({ source: src, id: p });
  } else if (e.kind === 'QUEST') {
    for (const m of e.milestones ?? []) walkCond(m.when, src);
    walkEffects(e.on_complete, src);
    if (e.giver_npc_id) refs.push({ source: src, id: e.giver_npc_id });
    if (e.from_want) refs.push({ source: src, id: e.from_want });
  } else if (e.kind === 'CAMPAIGN') {
    for (const [m, c] of Object.entries(e.unlocks ?? {})) walkCond(c, `${src}.unlocks.${m}`);
  }
}
for (const [q, c] of Object.entries(QUEST_GATES)) walkCond(c, `gate:${q}`);

// ─── 1. Flag registry ────────────────────────────────────────────────────────────

const outputs = new Set(threadNotes.flatMap((t) => t.interface.sets ?? []));
const inputs = new Set(threadNotes.flatMap((t) => [...(t.interface.reads ?? []), ...(t.interface.arms ?? [])]));
const report = { readNeverSet: [], setNeverRead: [], undeclared: [], declaredUnused: [], plannedOnly: [] };
const allFlags = new Set([...sets.keys(), ...reads.keys()]);
for (const f of allFlags) {
  if (!declared.has(f) && f !== 'gate_born') report.undeclared.push(f);
  if (reads.has(f) && !sets.has(f)) {
    if (plannedSet.has(f)) report.plannedOnly.push(`${f} (set only by an unconverted engine-example block)`);
    else if (!inputs.has(f)) report.readNeverSet.push(f);
  }
  if (sets.has(f) && !reads.has(f)) {
    if (outputs.has(f)) continue;
    if (LEGACY.has(f)) { legacyNotes.push(`${f} (set by a legacy slice Want; its thread card is not written yet)`); continue; }
    if (plannedRead.has(f)) report.plannedOnly.push(`${f} (read only by an unconverted engine-example block)`);
    else report.setNeverRead.push(f);
  }
}
for (const f of declared) if (!allFlags.has(f) && !plannedSet.has(f) && !plannedRead.has(f)) report.declaredUnused.push(f);

// ─── 2. Own-stage guards ─────────────────────────────────────────────────────────

function negatedFlags(c, acc = new Set(), neg = false) {
  if (!c) return acc;
  const [name] = Object.keys(c);
  const v = c[name];
  if (name === 'all') v.forEach((x) => negatedFlags(x, acc, neg));
  else if (name === 'not') negatedFlags(v, acc, !neg);
  else if (name === 'flag_set' && neg) acc.add(v.flag);
  return acc;
}
const guardMisses = [];
for (const e of entities) {
  if (e.kind === 'WORLD_EVENT') {
    const own = [...(e.then ?? [])].filter((x) => x.set_flag && !/^(gate_born)$/.test(x.set_flag.flag)).map((x) => x.set_flag.flag);
    if (own.length === 0) continue;
    const neg = negatedFlags(e.when);
    if (!own.some((f) => neg.has(f))) guardMisses.push(`event ${e.id} sets [${own.join(', ')}] but does not test 'not flag_set' on any of them`);
  } else if (e.kind === 'WANT' && e.on_deadline) {
    if (LEGACY.has(e.id)) continue;
    const own = e.on_deadline.filter((x) => x.set_flag).map((x) => x.set_flag.flag);
    if (own.length === 0) continue;
    const neg = negatedFlags(e.urgent_when);
    if (!own.some((f) => neg.has(f))) guardMisses.push(`want ${e.id} fires [${own.join(', ')}] but its urgent_when does not test 'not flag_set' on it`);
  }
}

// ─── 3. References ───────────────────────────────────────────────────────────────

const dangling = [];
for (const r of refs) {
  if (!r.id || r.id === 'PLAYER') continue;
  if (!ids.has(r.id) && !dangling.some((d) => d.id === r.id && d.source === r.source)) dangling.push(r);
}

// ─── 4. Interface ────────────────────────────────────────────────────────────────

const ifaceProblems = [];
for (const t of threadNotes) {
  for (const f of t.interface.reads ?? []) if (!reads.has(f)) ifaceProblems.push(`${t.id}: interface reads '${f}', but no Condition reads it`);
  for (const f of t.interface.sets ?? []) if (!sets.has(f)) ifaceProblems.push(`${t.id}: interface sets '${f}', but no Effect sets it`);
  for (const f of t.interface.arms ?? []) if (!reads.has(f)) ifaceProblems.push(`${t.id}: interface arms '${f}', but nothing reads it`);
  // Every flag a thread's own events set should appear in its interface or be an internal stage flag (lin_*).
}

// ─── 5. Terminal events ──────────────────────────────────────────────────────────

const terminalProblems = [];
for (const t of threadNotes) {
  for (const evtId of t.interface.terminals ?? []) {
    const e = entities.find((x) => x.id === evtId && x.kind === 'WORLD_EVENT');
    if (!e) { terminalProblems.push(`${t.id}: terminal '${evtId}' is not a World Event`); continue; }
    const own = (e.then ?? []).filter((x) => x.set_flag).map((x) => x.set_flag.flag);
    if (own.length === 0) terminalProblems.push(`${evtId}: a terminal event must set a result flag`);
    for (const f of own) {
      const readers = (posReads.get(f) ?? []).filter((s) => s !== evtId);
      if (readers.length) terminalProblems.push(`${evtId} is declared terminal, but ${readers.join(', ')} still reads '${f}' (a terminal has no exits; a read of it must be a negated guard)`);
    }
  }
}

// ─── Report ──────────────────────────────────────────────────────────────────────

const section = (title, items) => {
  console.log(`\n${title}: ${items.length}`);
  for (const i of items) console.log(`  - ${i}`);
};
console.log(`Thread check over ${entities.length} entities (${declared.size} declared flags, ${allFlags.size} used)`);
section('Undeclared flags (EN007 should catch these)', report.undeclared);
section('Flags read but never set (unsatisfiable)', report.readNeverSet);
section('Flags set but never read (dead, and not a declared thread output)', report.setNeverRead);
section('Planned only (the other side is an unconverted engine-example block)', report.plannedOnly);
section('Declared but unused', report.declaredUnused);
section('Legacy (Step 2a slice, not yet in a thread card; reported, not failed)', legacyNotes);
section('Missing own-stage guard (unsafe to fast-forward past)', guardMisses);
section('Dangling references inside Conditions and Effects', dangling.map((d) => `${d.source} -> ${d.id}`));
section('Thread interface mismatches', ifaceProblems);
section('Terminal events that are not terminal', terminalProblems);

const hard = report.readNeverSet.length + report.setNeverRead.length + guardMisses.length + dangling.length + ifaceProblems.length + report.undeclared.length + terminalProblems.length;
console.log(hard === 0 ? '\nOK: the flag registry, guards, references and interface are consistent.' : `\n${hard} problem(s).`);
process.exit(hard > 0 ? 1 : 0);

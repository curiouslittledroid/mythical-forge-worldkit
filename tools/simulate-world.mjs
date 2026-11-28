#!/usr/bin/env node
/**
 * Step 12a: an idle-world and scenario simulator for a generated Game Ready Repository.
 *
 * It evaluates the authored Conditions and Effects of the World and one Campaign the way
 * the engine does (one-shot sources, snapshot-per-round cascades, Want
 * deadlines as relative timers), advances the Sandbox day counter, and lets a scenario script
 * what the player and other threads do. It proves that a thread's state graph is reachable,
 * robust to unscripted actions, and idle-stable BEFORE any engine exists.
 *
 * It is a model, not the engine. Every place where the specs are silent is a named
 * ASSUMPTION below and is recorded in meta/pilot-thread-findings.md.
 *
 * Usage:  node tools/simulate-world.mjs [scenario.yaml ...] [--repo <game-ready-repo>] [--quiet] [--coverage]
 *         (no scenario argument: run every scenario in the directory world.config.yaml names
 *          as `vault.scenarios`, whose quest-gates sidecar is read from the same place)
 *
 * ASSUMPTIONS (the design is silent on each; each is proposed as a spec clarification, A4):
 *  A-1  A Want starts its clock on the first day its `urgent_when` holds (or the day an
 *       `activate_want` Effect names it); with no `urgent_when` it is active from day 0.
 *  A-2  `urgent_when` only ACTIVATES a Want. Once active it stays active until resolved,
 *       failed, or its deadline fires. Authors must retire Wants explicitly.
 *  A-3  `on_deadline` fires once, only if the Want is still active at the deadline.
 *       `resolve_want` and `fail_want` both stop it.
 *  A-4  A dead NPC's own Wants are failed. Other NPCs' Wants are NOT retired automatically.
 *  A-5  Effects within one round do not see each other (snapshot per round); the follow-up
 *       state change starts the next round. Rounds are capped (limit placeholder: 8).
 *  T-1  (an invariant, checked in every scenario) Once a thread's terminal event (`interface.terminals`)
 *       has fired, none of that thread's Wants may still be active. A terminal closes the thread.
 *  A-6  A Quest can be started only if its Module is unlocked, it is not already complete,
 *       and its `available_when` holds. `available_when` is PROPOSED (A5): the pilot keeps it
 *       in the pilot's quest-gates sidecar because the Quest schema has no such field.
 */
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { dirname, join, resolve, basename } from 'node:path';
import { fileURLToPath } from 'node:url';

import { gatesFile, loadConfig, requireMf } from './kit_config.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const CODEX_ROOT = resolve(HERE, '..');
const cfg = loadConfig();
const YAML = requireMf('yaml');

const args = process.argv.slice(2);
const flagArg = (name) => {
  const i = args.indexOf(name);
  return i >= 0 ? args[i + 1] : undefined;
};
const REPO = resolve(flagArg('--repo') ?? process.env.GAME_READY_REPO ?? cfg.gameReadyRepo);
const QUIET = args.includes('--quiet');
const COVERAGE = args.includes('--coverage');
const MD = args.includes('--md');
const MAX_ROUNDS = 8;
const scenarioFiles = args.filter((a, i) => a.endsWith('.yaml') && args[i - 1] !== '--repo');

// ─── Loading ─────────────────────────────────────────────────────────────────────

function yamlFiles(dir) {
  if (!existsSync(dir)) return [];
  const out = [];
  for (const e of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, e.name);
    if (e.isDirectory()) out.push(...yamlFiles(full));
    else if (e.name.endsWith('.yaml')) out.push(full);
  }
  return out.sort();
}
const readYaml = (p) => YAML.parse(readFileSync(p, 'utf8'));
/** Codex thread sidecar written by transform.mjs: members and interface (incl. `terminals`) per thread. */
const THREADS = existsSync(join(REPO, 'codex-threads.yaml')) ? readYaml(join(REPO, 'codex-threads.yaml')) : {};
const SCENARIOS_DIR = cfg.scenariosDir;
/** Quest gates (PROPOSED `available_when`, PR-13). Resolved per scenario directory, below. */
let QUEST_GATES = {};

function loadWorld(campaignId) {
  const w = { events: new Map(), wants: new Map(), npcs: new Map(), quests: new Map(), modules: new Map(), facts: new Map(), edges0: new Set(), campaign: null };
  const add = (e, ctx = {}) => {
    switch (e.kind) {
      case 'WORLD_EVENT': w.events.set(e.id, e); break;
      case 'WANT': w.wants.set(e.id, e); break;
      case 'NPC': w.npcs.set(e.id, e); break;
      case 'FACT': w.facts.set(e.id, e); break;
      case 'RELATIONSHIP': w.edges0.add(`${e.from}|${e.kind_of}|${e.to}`); break;
      case 'QUEST': w.quests.set(e.id, { ...e, module: ctx.module }); break;
      case 'MODULE': w.modules.set(e.id, e); break;
    }
  };
  for (const f of yamlFiles(join(REPO, 'world'))) {
    const e = readYaml(f);
    if (e?.kind) add(e);
  }
  const cdir = join(REPO, 'campaigns', campaignId);
  w.campaign = readYaml(join(cdir, 'campaign.yaml'));
  const overlay = existsSync(join(cdir, 'overlay.yaml')) ? readYaml(join(cdir, 'overlay.yaml')) : { adds: [] };
  for (const e of overlay.adds ?? []) add(e);
  // Overlay `overrides`: field-level patches to World entities, keyed by id; a path may be dotted.
  for (const [id, patch] of Object.entries(overlay.overrides ?? {})) {
    const target = w.wants.get(id) ?? w.events.get(id) ?? w.npcs.get(id) ?? w.facts.get(id);
    if (!target) throw new Error(`overlay overrides unknown entity ${id}`);
    for (const [path, value] of Object.entries(patch)) {
      const keys = path.split('.');
      let o = target;
      for (const k of keys.slice(0, -1)) o = o[k];
      o[keys.at(-1)] = value;
    }
  }
  for (const mf of yamlFiles(join(cdir, 'modules'))) {
    const e = readYaml(mf);
    const mod = basename(dirname(mf)) === 'quests' ? basename(dirname(dirname(mf))) : basename(dirname(mf));
    add(e, { module: mod });
  }
  return w;
}

// ─── State ───────────────────────────────────────────────────────────────────────

function newState(w) {
  const st = {
    day: w.campaign.start_day ?? 0,
    flags: new Map(),
    fired: new Set(),
    wants: new Map(),
    edges: new Set(w.edges0),
    dead: new Set(),
    loc: new Map(),
    facts: new Set(),
    revealedEdges: new Set(),
    quests: new Map(),
    unlocked: new Set([w.campaign.opening_module]),
    moduleUnlockDay: new Map([[w.campaign.opening_module, 0]]),
    playerLoc: w.campaign.start_location,
    log: [],
    rejected: [],
    maxRounds: 0,
    firedOn: new Map(),
    deadlinesFired: new Set(),
    questsDone: new Set(),
  };
  for (const [id, n] of w.npcs) if (n.home) st.loc.set(id, n.home);
  for (const [id] of w.wants) st.wants.set(id, { status: 'dormant', since: null });
  return st;
}

const fkey = (flag, toward) => `${flag}|${toward ?? '*'}`;

// ─── Conditions ──────────────────────────────────────────────────────────────────

function cond(c, st, w) {
  const [name] = Object.keys(c);
  const v = c[name];
  switch (name) {
    case 'all': return v.every((x) => cond(x, st, w));
    case 'any': return v.some((x) => cond(x, st, w));
    case 'not': return !cond(v, st, w);
    case 'day_reached': return st.day >= v;
    case 'day_between': return st.day >= v.from && st.day <= v.to;
    case 'flag_set': return (st.flags.get(fkey(v.flag, v.toward))?.count ?? 0) >= 1;
    case 'flag_count_gte': return (st.flags.get(fkey(v.flag, v.toward))?.count ?? 0) >= v.count;
    case 'edge_exists': return st.edges.has(`${v.from}|${v.kind}|${v.to}`);
    case 'event_occurred': return st.fired.has(v);
    case 'npc_alive': return !st.dead.has(v);
    case 'fact_revealed': return st.facts.has(v);
    case 'quest_state': return (st.quests.get(v.quest) ?? 'NOT_STARTED') === v.state;
    case 'in_location': return (v.entity === 'PLAYER' ? st.playerLoc : st.loc.get(v.entity)) === v.location;
    default: throw new Error(`simulator does not model the '${name}' predicate`);
  }
}

// ─── Effects ─────────────────────────────────────────────────────────────────────

function apply(effect, st, w, source) {
  const [name] = Object.keys(effect);
  const v = effect[name];
  const note = (s) => st.log.push({ day: st.day, source, text: s });
  switch (name) {
    case 'set_flag': {
      const k = fkey(v.flag, v.toward);
      const cur = st.flags.get(k);
      st.flags.set(k, { count: (cur?.count ?? 0) + 1, first_day: cur?.first_day ?? st.day });
      note(`set ${v.flag}${v.toward ? ' toward ' + v.toward : ''}`);
      break;
    }
    case 'add_edge': st.edges.add(`${v.from}|${v.kind}|${v.to}`); note(`edge + ${v.from} ${v.kind} ${v.to}`); break;
    case 'remove_edge': st.edges.delete(`${v.from}|${v.kind}|${v.to}`); note(`edge - ${v.from} ${v.kind} ${v.to}`); break;
    case 'reveal_edge': st.revealedEdges.add(`${v.from}|${v.kind}|${v.to}`); note(`reveal edge ${v.from} ${v.kind} ${v.to}`); break;
    case 'reveal_fact': st.facts.add(v); note(`reveal ${v}`); break;
    case 'activate_want': {
      const s = st.wants.get(v);
      if (!s) note(`WARN activate_want: unknown ${v}`);
      else if (s.status === 'dormant') { s.status = 'active'; s.since = st.day; note(`activate ${v}`); }
      break;
    }
    case 'resolve_want': case 'fail_want': {
      const s = st.wants.get(v);
      if (!s) note(`WARN ${name}: unknown ${v}`);
      else if (s.status === 'dormant' || s.status === 'active') { s.status = name === 'resolve_want' ? 'resolved' : 'failed'; note(`${name === 'resolve_want' ? 'resolve' : 'fail'} ${v}`); }
      break;
    }
    case 'move_npc': st.loc.set(v.npc, v.to); note(`move ${v.npc} -> ${v.to}`); break;
    case 'unlock_module': st.unlocked.add(v); note(`unlock ${v}`); break;
    case 'start_quest': st.quests.set(v, 'ACTIVE'); note(`start ${v}`); break;
    case 'adjust_disposition': note(`disposition ${v.npc} ${v.delta >= 0 ? '+' : ''}${v.delta}`); break;
    case 'grant_reward': note('reward'); break;
    case 'emit_ripple': case 'spawn_encounter': case 'set_exit_state': note(name); break;
    default: throw new Error(`simulator does not model the '${name}' effect`);
  }
}

// ─── The day tick ────────────────────────────────────────────────────────────────

function settle(st, w) {
  for (let round = 1; round <= MAX_ROUNDS; round += 1) {
    const fires = [];
    // Module unlocks (Campaign `unlocks`).
    for (const [mod, c] of Object.entries(w.campaign.unlocks ?? {})) {
      if (!st.unlocked.has(mod) && cond(c, st, w)) fires.push({ type: 'module', mod });
    }
    // Want activation (A-1) and deadlines (A-3).
    for (const [id, want] of w.wants) {
      const s = st.wants.get(id);
      if (s.status === 'dormant' && (want.urgent_when === undefined || cond(want.urgent_when, st, w))) fires.push({ type: 'activate', id });
      else if (s.status === 'active' && want.deadline_days !== undefined && st.day >= s.since + want.deadline_days) fires.push({ type: 'deadline', id });
    }
    // World Events (one-shot per source).
    for (const [id, evt] of w.events) {
      if (!st.fired.has(id) && cond(evt.when, st, w)) fires.push({ type: 'event', id });
    }
    if (fires.length === 0) return;
    st.maxRounds = Math.max(st.maxRounds, round);
    for (const f of fires) {
      if (f.type === 'module') { st.unlocked.add(f.mod); st.moduleUnlockDay.set(f.mod, st.day); st.log.push({ day: st.day, source: 'campaign', text: `unlock ${f.mod}` }); }
      else if (f.type === 'activate') { const s = st.wants.get(f.id); if (s.status === 'dormant') { s.status = 'active'; s.since = st.day; } }
      else if (f.type === 'deadline') {
        const s = st.wants.get(f.id);
        s.status = 'expired';
        st.deadlinesFired.add(f.id);
        st.log.push({ day: st.day, source: `want:${f.id}`, text: 'DEADLINE' });
        for (const e of w.wants.get(f.id).on_deadline ?? []) apply(e, st, w, `want:${f.id}`);
      } else {
        st.fired.add(f.id);
        st.firedOn.set(f.id, st.day);
        st.log.push({ day: st.day, source: f.id, text: 'EVENT' });
        for (const e of w.events.get(f.id).then ?? []) apply(e, st, w, f.id);
      }
    }
  }
  throw new Error(`cascade did not settle within ${MAX_ROUNDS} rounds on day ${st.day}`);
}

// ─── Player and other-thread actions ─────────────────────────────────────────────

function doAction(a, st, w) {
  const note = (s) => st.log.push({ day: st.day, source: 'player', text: s });
  if (a.kill) {
    st.dead.add(a.kill);
    for (const [id, want] of w.wants) if (want.npc_id === a.kill) { const s = st.wants.get(id); if (s.status === 'dormant' || s.status === 'active') s.status = 'failed'; }
    note(`kill ${a.kill}`);
  }
  if (a.set_flag) { apply({ set_flag: { flag: a.set_flag } }, st, w, 'input'); }
  if (a.effects) for (const e of a.effects) apply(e, st, w, 'input');
  if (a.player_at) { st.playerLoc = a.player_at; note(`player at ${a.player_at}`); }
  if (a.move) for (const m of [].concat(a.move)) { st.loc.set(m.npc, m.to); note(`move ${m.npc} -> ${m.to}`); }
  if (a.quest) {
    const q = w.quests.get(a.quest);
    if (!q) throw new Error(`scenario names unknown quest ${a.quest}`);
    const modOk = st.unlocked.has(q.module);
    const gate = QUEST_GATES[a.quest];
    const startOk = (gate === undefined || cond(gate, st, w)) && st.quests.get(a.quest) !== 'COMPLETED';
    if (!modOk || !startOk) {
      st.rejected.push(a.quest);
      note(`quest ${a.quest} NOT AVAILABLE (${!modOk ? 'module ' + q.module + ' locked' : st.quests.get(a.quest) === 'COMPLETED' ? 'already complete' : 'the world has moved past it (available_when is false)'})`);
      return;
    }
    if (a.moves) for (const m of a.moves) st.loc.set(m.npc, m.to);
    st.quests.set(a.quest, 'COMPLETED');
    st.questsDone.add(a.quest);
    st.log.push({ day: st.day, source: 'player', text: `quest ${a.quest} COMPLETE` });
    for (const e of q.on_complete ?? []) apply(e, st, w, `quest:${a.quest}`);
  }
}

// ─── Running a scenario ──────────────────────────────────────────────────────────

function run(scn, w, { quiet = false } = {}) {
  const st = newState(w);
  let ffEffects = null;
  if (scn.start?.fast_forward) {
    ffEffects = fastForward(scn.start.fast_forward, w);
    for (const e of ffEffects) apply(e, st, w, 'fast-forward');
    st.log.push({ day: 0, source: 'start', text: `fast-forwarded: ${ffEffects.length} effects (stage flag ${scn.start.fast_forward})` });
  }
  const byDay = new Map();
  for (const a of [...(scn.inputs ?? []), ...(scn.actions ?? [])]) byDay.set(a.day, [...(byDay.get(a.day) ?? []), a]);
  const end = scn.run_days ?? 400;
  for (let d = st.day; d <= end; d += 1) {
    st.day = d;
    settle(st, w);
    for (const a of byDay.get(d) ?? []) { doAction(a, st, w); settle(st, w); }
  }
  return { st, ffEffects };
}

/** Net effects of the idle world up to the day `stageFlag` is first set (the Campaign start-state generator). */
function fastForward(stageFlag, w) {
  const st = newState(w);
  for (let d = 0; d <= 4000; d += 1) {
    st.day = d;
    settle(st, w);
    if ((st.flags.get(fkey(stageFlag))?.count ?? 0) >= 1) break;
    if (d === 4000) throw new Error(`fast-forward: ${stageFlag} is never set while idle`);
  }
  const eff = [];
  for (const [k, v] of st.flags) {
    const [flag, toward] = k.split('|');
    if (v.count >= 1) eff.push({ set_flag: toward === '*' ? { flag } : { flag, toward } });
  }
  for (const e of st.edges) {
    if (w.edges0.has(e)) continue;
    const [from, kind, to] = e.split('|');
    eff.push({ add_edge: { from, kind, to, sentiment: 0, visibility: 'SECRET' } });
  }
  for (const [npc, loc] of st.loc) if (w.npcs.get(npc)?.home !== loc) eff.push({ move_npc: { npc, to: loc } });
  return eff;
}

// ─── Reporting and assertions ────────────────────────────────────────────────────

const edgeStr = (s) => s.split('|').join(' ');

function check(scn, st) {
  const ex = scn.expect ?? {};
  const fails = [];
  const hasFlag = (f) => (st.flags.get(fkey(f))?.count ?? 0) >= 1 || [...st.flags.keys()].some((k) => k.startsWith(`${f}|`));
  for (const f of ex.flags ?? []) if (!hasFlag(f)) fails.push(`flag ${f} should be set`);
  for (const f of ex.not_flags ?? []) if (hasFlag(f)) fails.push(`flag ${f} should NOT be set`);
  for (const e of ex.events ?? []) if (!st.fired.has(e)) fails.push(`event ${e} should have fired`);
  for (const e of ex.not_events ?? []) if (st.fired.has(e)) fails.push(`event ${e} should NOT have fired (fired day ${st.firedOn.get(e)})`);
  for (const e of ex.edges ?? []) if (![...st.edges].some((x) => edgeStr(x) === e)) fails.push(`edge '${e}' should exist`);
  for (const e of ex.not_edges ?? []) if ([...st.edges].some((x) => edgeStr(x) === e)) fails.push(`edge '${e}' should NOT exist`);
  for (const [e, [a, b]] of Object.entries(ex.fired_between ?? {})) {
    const d = st.firedOn.get(e);
    if (d === undefined || d < a || d > b) fails.push(`event ${e} fired on day ${d}, expected ${a}..${b}`);
  }
  for (const [n, l] of Object.entries(ex.locations ?? {})) if (st.loc.get(n) !== l) fails.push(`${n} should be at ${l}, is at ${st.loc.get(n)}`);
  for (const m of ex.modules ?? []) if (!st.unlocked.has(m)) fails.push(`module ${m} should be unlocked`);
  for (const q of ex.rejected ?? []) if (!st.rejected.includes(q)) fails.push(`quest ${q} should have been rejected`);
  for (const q of ex.not_rejected ?? []) if (st.rejected.includes(q)) fails.push(`quest ${q} should NOT have been rejected`);
  // T-1: a fired terminal event must leave none of its thread's Wants running.
  for (const [slug, t] of Object.entries(THREADS)) {
    const fired = (t.interface?.terminals ?? []).filter((e) => st.fired.has(e));
    if (fired.length === 0) continue;
    for (const wid of t.members?.WANT ?? []) {
      if (st.wants.get(wid)?.status === 'active') fails.push(`terminal ${fired.join(', ')} of thread '${slug}' fired but want ${wid} is still active`);
    }
  }
  for (const [wid, status] of Object.entries(ex.wants ?? {})) if (st.wants.get(wid)?.status !== status) fails.push(`want ${wid} should be ${status}, is ${st.wants.get(wid)?.status}`);
  return fails;
}

function printRun(scn, st, ffEffects) {
  console.log(`\n── ${scn.name} ${'─'.repeat(Math.max(2, 70 - scn.name.length))}`);
  if (scn.description) console.log(`   ${scn.description}`);
  if (ffEffects) {
    console.log(`   fast-forward start state (${ffEffects.length} effects):`);
    for (const e of ffEffects) console.log(`     - ${JSON.stringify(e).replace(/"/g, '')}`);
  }
  let lastDay = -1;
  for (const l of st.log) {
    if (l.text.startsWith('disposition') || l.text === 'reward') continue;
    const main = l.text === 'EVENT' || l.text === 'DEADLINE' || l.source === 'player' || l.source === 'input' || l.source === 'campaign';
    if (!main && !l.text.startsWith('edge') && !l.text.startsWith('move') && !l.text.startsWith('set') && !l.text.startsWith('activate') && !l.text.startsWith('fail') && !l.text.startsWith('resolve') && !l.text.startsWith('reveal')) continue;
    const day = String(l.day).padStart(4, ' ');
    const dayStr = l.day === lastDay ? '    ' : day;
    lastDay = l.day;
    const tag = l.text === 'EVENT' ? 'EVENT   ' : l.text === 'DEADLINE' ? 'DEADLINE' : l.source === 'player' || l.source === 'input' ? 'ACTION  ' : '        ';
    const src = l.text === 'EVENT' || l.text === 'DEADLINE' ? l.source.replace('want:', '') : `   ${l.text}`;
    console.log(`   ${dayStr}  ${tag} ${l.text === 'EVENT' || l.text === 'DEADLINE' ? src : src}`);
  }
}

function printMd(scn, st) {
  console.log(`| Day | Source | What changes |\n|---|---|---|`);
  const rows = [];
  let cur = null;
  for (const l of st.log) {
    if (l.text === 'EVENT' || l.text === 'DEADLINE') { cur = { day: l.day, src: l.source.replace('want:', 'want '), what: [] }; rows.push(cur); }
    else if (cur && l.source === cur.src.replace('want ', 'want:') && /^(set|edge|move|unlock|activate)/.test(l.text)) cur.what.push(l.text.replace('set ', '`').replace(/$/, l.text.startsWith('set ') ? '`' : ''));
    else if (l.source === 'player' || l.source === 'input') { cur = { day: l.day, src: 'player', what: [l.text] }; rows.push(cur); }
  }
  for (const r of rows) console.log(`| ${r.day} | ${r.src} | ${r.what.join('; ')} |`);
}

// ─── Main ────────────────────────────────────────────────────────────────────────

if (!scenarioFiles.length && !SCENARIOS_DIR) {
  console.error('no scenarios: name some, or set vault.scenarios in world.config.yaml');
  process.exit(2);
}
const files = scenarioFiles.length
  ? scenarioFiles
  : yamlFiles(SCENARIOS_DIR).filter((x) => !basename(x).includes('quest-gates'));
let failed = 0;
const seenEvents = new Set();
const seenDeadlines = new Set();
const seenQuests = new Set();
let worldRef = null;
for (const f of files) {
  const scn = readYaml(f);
  // The sidecar belongs beside the scenarios being run, so a scenario set carries its own gates.
  const ownGates = scn.quest_gates_file
    ? resolve(dirname(f), scn.quest_gates_file)
    : gatesFile(dirname(f));
  QUEST_GATES = ownGates && existsSync(ownGates) ? readYaml(ownGates) : {};
  const w = loadWorld(scn.campaign ?? 'camp_dustport_pilot');
  worldRef = w;
  const { st, ffEffects } = run(scn, w);
  const fails = check(scn, st);
  if (MD) printMd(scn, st);
  else if (!QUIET) printRun(scn, st, ffEffects);
  const verdict = fails.length === 0 ? 'PASS' : 'FAIL';
  console.log(`   ${verdict}: ${scn.name} (max cascade ${st.maxRounds} rounds)`);
  for (const x of fails) console.log(`     ✗ ${x}`);
  if (fails.length) failed += 1;
  for (const e of st.fired) seenEvents.add(e);
  for (const e of st.deadlinesFired) seenDeadlines.add(e);
  for (const q of st.questsDone) seenQuests.add(q);
}
console.log(`\n${files.length} scenario(s): ${files.length - failed} passed, ${failed} failed`);

if (COVERAGE && worldRef) {
  console.log('\n── coverage across all scenarios ─────────────────────────────────────────');
  const unseen = (all, seen) => [...all].filter((x) => !seen.has(x));
  const evUnseen = unseen(worldRef.events.keys(), seenEvents);
  const dlUnseen = unseen([...worldRef.wants].filter(([, wnt]) => wnt.deadline_days !== undefined).map(([id]) => id), seenDeadlines);
  const qUnseen = unseen(worldRef.quests.keys(), seenQuests);
  console.log(`   events fired: ${seenEvents.size}/${worldRef.events.size}${evUnseen.length ? '   NEVER: ' + evUnseen.join(', ') : ''}`);
  console.log(`   want deadlines fired: ${seenDeadlines.size}/${[...worldRef.wants.values()].filter((x) => x.deadline_days !== undefined).length}${dlUnseen.length ? '   NEVER: ' + dlUnseen.join(', ') : ''}`);
  console.log(`   quests completed: ${seenQuests.size}/${worldRef.quests.size}${qUnseen.length ? '   NEVER: ' + qUnseen.join(', ') : ''}`);
  if (evUnseen.length || dlUnseen.length || qUnseen.length) failed += 1;
}
process.exit(failed > 0 ? 1 : 0);

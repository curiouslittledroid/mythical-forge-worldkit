# The Thread Pattern

**Summary:** How a plot web is built so that **each player's Sandbox can evolve differently**, and so
that the three story layers — the World, Campaigns, and Modules/Quests — share one world without
breaking each other. **This is the reference (the why).** The step-by-step tutorial is
`campaign-authoring-guide.md`.

**Status of the examples.** The pattern was proved on one long-lived thread with 22 events, 15 Wants,
9 Quests and 16 scripted scenarios, and the examples below come from that pilot: a boy, a debt and a
woman who owns him. They are illustrative, not canonical. A world's own thread cards live in its
`world/plot-web/`.

**Where the engine cannot yet follow**, the requests are `PR-9`…`PR-13` in
`engine-capability-register.md`.

## 1. The problem

A Sandbox is one player's copy of one Campaign, pinned to a World version (Design 23 §2, §3.3). Its state diverges: players kill the people the plot depends on, skip Quests, and hide, rescue or lose the same boy. So:

- A **shared calendar of dated events cannot exist**. Every Sandbox has its own day counter, and an event keyed to a day fires in every Sandbox of every Campaign.
- A **thread must survive what the player does** (a death, a skipped Quest, an unscripted act), not only what the author imagined.
- A **later Campaign must be able to start the same thread at a different stage**, and a Campaign set elsewhere must be able to leave it dormant.

## 2. The three layers

| Layer | Owns | Is written as |
|---|---|---|
| **World** | What is true and what is pushing: history, Facts, places, factions, NPCs, **Wants (the engines of motion)**, **thread World Events**, the flag vocabulary. Nothing in it mentions the player. | Thread cards (the-lineage-and-the-gate-born is the model), in `world/plot-web/` |
| **Campaign** | Purpose and starting point: which threads are armed and at what stage, which beats are `LOCKED`, which Modules unlock, the end state. | A Campaign, an overlay with a **genesis event**, and `unlocks` that read thread flags |
| **Module / Quest** | A bounded set of choices at a place. A Quest is a **Resolution Path** of a Want, so skipping it lets the Want's deadline fire instead. | Modules with Quests that apply a **quest contract** |

**Flags are the API between the layers.** The World publishes them; Campaigns and Modules read and set the ones a thread lists in its interface.

### 2.1 The Campaign and its Overlay

A Campaign is two engine entities, not one. A **Campaign block** says what the Campaign *is*; a **Campaign Overlay** says how it *changes the World* for its Sandboxes. Neither is a thread-style grouping: both are real engine entities (`kind: CAMPAIGN` and `kind: CAMPAIGN_OVERLAY`).

| | **Campaign** | **Campaign Overlay** |
|---|---|---|
| **Purpose** | the storyline a player picks | how the Campaign changes the shared World for its Sandboxes |
| **Contains** | title, summary, `start_level`, `start_day`, `start_location`, `opening_module`, the Module list, `unlocks`, content descriptors, Campaign flags | `adds`, `overrides`, `suppresses` |
| **Read by** | the Campaign picker, the Module Selector | the layered read, `Merge(World, Overlay, Sandbox Delta)` (Design 23 §2.1) |

The overlay has three operations only (Design 23 §3.2):
- **`adds`:** new entities that exist only in this Campaign (NPCs, Wants, Facts, World Events and so on). The pilot's genesis event is one.
- **`overrides`:** field-level patches to World entities, keyed by the entity's own id (for example a Want's `authority`, or an NPC's voice).
- **`suppresses`:** World entities that do not exist in this Campaign.

An overlay may touch authored fields only. It cannot change ids, kinds or structural fields, and it cannot add Campaigns, Modules or Migrations.

**Why they are separate.** Design 23 does not state the reason; this is the reading that fits the rest of the design:

1. **They answer different questions.** The manifest is what a player sees in the picker: a few fields and no World content. The overlay is a patch set aimed at World entities.
2. **The overlay drives the version rules.** An entity the overlay overrides counts as "overridden" in the adoption logic (Design 23.4 §3.2): a later World edit to it is pinned, not applied silently. An entity's effective hash is the World object plus any override. That logic needs the overlay as its own thing.
3. **They can grow and change independently.** An overlay can add hundreds of entities while the manifest stays small, and each can be hashed and versioned separately in the content store.
4. **The overlay is optional.** A Campaign that changes nothing in the World needs none, and the schema rejects an empty one ("an overlay must add, override or suppress something").

The two are tied by ids: the overlay carries `campaign_id`, and the Campaign does not list its overlay.

**In the pilot**, the-quay-boy is the Campaign block, and `overlay_dustport_pilot` adds one thing: the genesis event that sets `lin_armed` (section 8.2). The transformer writes them as `campaign.yaml` and `overlay.yaml` in the same folder.

## 3. The flag vocabulary

| Family | Meaning | Set by | Read by | Example |
|---|---|---|---|---|
| **Armed** | "This thread is live in this Sandbox." | a Campaign's start state | the thread's first Wants and events | `lin_armed` |
| **Stage** | History: the thread has reached stage N. One-way. | the thread's own events | everyone | `lin_s3_stonehold` |
| **Intent** | "A deadline passed; this *may* now happen." A proposal, not a fact. | a Want's `on_deadline` | the World Event that applies it, if the guards still hold | `lin_take_due` |
| **Outcome** | Which fork the player took. | a Quest contract | the thread, Campaigns, Modules | `lin_ennis_hidden` |
| **Counter** | Repeated acts counted to a threshold. | several sources, once each | a `flag_count_gte` Condition | `lin_ledger_page` |
| **Trait** | A property of one entity (CP-4). | the genesis event | Conditions that name `toward` | `gate_born` scoped to Ennis |
| **Input / Output** | A flag one thread reads that another sets. | other thread | this thread | `gate_fails_for_a_season` |

**Edges are the current state; flags are the history.** Custody of Ennis is the edge `faction_lineage CONTROLS Ennis` (or `Rusk GUARDS`, `Quillon GUARDS`, `Verran GUARDS`). A flag such as `lin_ennis_taken` stays set after he is rescued; the edge does not. Conditions that need "is it true now?" test the edge. Conditions that need "did it ever happen?" test the flag. A Fact carries what people know; a flag carries what happened.

### 3.1 What an armed flag is

An **armed flag** is a flag whose only job is to say *this thread is live in this Sandbox*. It is set once, by the Campaign's start state, and every opening Want and event in the thread is gated by it (`urgent_when: all: [lin_armed, ...]`).

- **Unarmed, a thread is dormant lore.** Its NPCs have Wants that never become urgent, and its events never fire. A Campaign set in the Far Reach, or a century later, simply never arms the Lineage thread, and it costs nothing.
- **Armed, a thread runs.** The world moves without the player.
- **Arming is not a stage.** It says *the thread is live*, not *it is at stage 1*. A Campaign can arm a thread and also set stage flags to start it mid-story (section 5).
- **Why not a date?** A `day_reached` start would fire in every Sandbox on the same day regardless of Campaign, and an event added in a later version would fire at once in any Sandbox already past that day (Design 23.4 §10).

## 4. Time

| What | How | Why |
|---|---|---|
| A season or festival | `season_is`, from the World calendar (Step 9) | it is genuinely calendar-shaped |
| "N days after X" | a **Want timer**: a Want whose `urgent_when` is X, with `deadline_days: N` (CP-9) | `deadline_days` is relative to activation, which is a native relative timer |
| "N days after X" for a non-NPC clock | `days_since` (**PR-9**; until then use an NPC anchor) | FLAG items already store `first_day` |
| "On day N" | only in a Campaign's own overlay | a Campaign owns its own clock |

A thread's **default pace** ("if left alone") is therefore the sum of its timers. It is generated by the idle simulation, not hand-written (section 9).

## 5. Guards and fast-forward

Design 23 §5.1 says a source applies **exactly once** per Sandbox. That is true of firing, but nothing records that an event "has occurred" for a Sandbox that was *started past it*. If a Campaign sets stage 3 directly, an earlier event whose Condition is still true would fire at day 0 and re-apply its Effects.

**The own-stage guard (CP-8):** every World Event, and every Want that sets an intent flag, tests `not flag_set <its own result flag>`. A Campaign that sets that flag, or any later one, silently retires the source. The pilot proved both directions: removing a guard makes `thread-check` fail (static) and makes the fast-forward scenario re-fire the event (dynamic).

**Fast-forward** is therefore just a list of flags, edges and NPC moves: the net state of the idle world up to a stage. `tools/simulate-world.mjs` generates it. A limit: timers in progress restart (a Want whose clock was half-run restarts at day 0), so fast-forward to a boundary where the next clock has not started.

## 6. Resolution classes

### 6.1 Resolvable

**The thread has terminal outcomes that stick. Once one is reached, the thread stops generating events, and later Campaigns inherit the result.**

- **Shape:** a short graph that ends in two to four terminals, with no loops. One terminal is the **idle terminal**: where the thread ends if nobody intervenes (usually the grimmest).
- **What the player can do:** pick a terminal. Each is a permanent shift (an edge added or removed, a flag set), never a restoration (permanence-rules).
- **Examples:** the Hundred's succession (a named First Wheel, or a split); the Wardens' secret (exposed, buried, or the Hushed freed at the cost of the lights); Far Reach contact (a Garden planted, or refused); the Concord (renewed or broken); the Conclave versus the delvers (the truth told, or kept).
- **Authoring rule:** every terminal must be reachable (validator producer analysis), and the idle terminal must be reached by the idle simulation.

### 6.2 Managed

**The pressure never ends, but the player can move the thread between states and buy bounded reprieves. Each reprieve costs something and the cycles are bounded; once they are spent, the pressure resumes unconditionally.**

- **Shape:** a pressure ladder with side-states ("reprieves") that restart a timer. Because engine events fire once, the cycles are **unrolled** and capped (the pilot allows two, then the hunt is `lin_hunt_exhausted`). A third is not authored.
- **What the player can do:** delay, redirect or hand the problem to someone else. They cannot remove it.
- **Examples:** the Church schism; the League's split; the elven enclave; the Graced; the gnome diaspora and the last waygate; the Lineage's custody loop.
- **Authoring rule:** the **floor** (what happens when reprieves run out) is authored and reached by the idle simulation. A reprieve must be bought with a Quest, a cost or a trade, never free.

### 6.3 Ratchet

**The thread only moves forward. No state in the graph restores anything. The best the player can do is slow it or redirect its effects.**

- **Shape:** a one-way ladder, often long. A reprieve replaces a timer with a longer one; it never goes back a stage.
- **What the player can do:** delay and mitigate. This is where the permanence rules live: because no Effect anywhere produces the restored state, the validator can *prove* the world cannot be fixed (a Condition with no producer is unsatisfiable, Design 23.3 §8).
- **Examples:** the water wars (the Long Ebb); the Uncovering (the relics are finite and get picked clean); the Quiet Trade; orc and goblin conflict; sentinels waking; the Gone's factions; the Choir's divisions (the Door-Warden's clock).
- **Authoring rule:** use `LOCKED` outcomes where the ratchet must not be avoidable, and test that the idle run reaches the last stage within the horizon.

### 6.4 Mixed threads

Most real threads mix shapes. Classify by the **dominant** shape and record the others. The Lineage thread is **Managed** (the custody loop), has a **Resolvable** terminal (`lin_programme_ended`), and has a **Ratchet** floor (`evt_lin_candidate_lost` is `LOCKED`: the Lineage always has a second candidate).

**A world's own threads are classified in its own note**, one row each, and a Campaign records which
class it is arming.

## 7. Threads

### 7.1 How is a thread stored

A **thread card** is the thread's **note** (for example `world/plot-web/the-lineage-and-the-gate-born.md`). It has two halves:

| Half | What is in it | Who reads it |
|---|---|---|
| **The document** | premise, actors and successors, the state graph, interface, quest contracts, the idle run, hooks | people and agents. This is the design. |
| **The `## Engine` section** | the thread's **World Events** and its **Facts**, as `engine` blocks | the transformer and the engine |

The note's frontmatter (`thread:` and `interface:`) is also part of the card, but it is codex-only and never reaches the engine.

**The card does not hold the whole thread.** Each block lives in the note of the thing it belongs to (conventions §9.1), so the thread is spread across the vault:

| Piece | Where it lives |
|---|---|
| World Events, Facts | the thread card |
| **Wants** | each NPC's note (the retriever's seven Wants are in `halvard-sorn.md`) |
| **Quests** | the Module notes in the Campaign |
| **The genesis event** that arms the thread | the Campaign's overlay note |
| **Flags** | `world/flags.md` |
| NPCs, factions, relationships | their own notes |

Two terms keep this clear:
- **Thread card** means the note: the design document plus its own event and Fact blocks.
- **Thread** means the whole set of linked pieces across all those notes. The card documents it but does not contain it.

The Step 14 thread compiler (section 10) changes this: the card would hold a compact graph, and the compiler would produce the events and Wants and place them in the right notes' output.

### 7.2 How a thread is linked (there is no thread entity)

**The engine has no `THREAD` entity, and has no grouping of any kind.** Design 23's kinds are NPC, WANT, FACT, RELATIONSHIP, WORLD_EVENT, QUEST, ROOM, ENCOUNTER, FACTION, ITEM, MONSTER, MODULE, CAMPAIGN, CAMPAIGN_OVERLAY, MIGRATION and OVERLAND_GRAPH. A thread is a **codex concept**.

When the transformer runs, a thread card becomes separate files (`world/events/evt_lin_*.yaml`, `world/facts/...`, `world/wants/...`, and Quests under `campaigns/...`). Nothing in those files says "I belong to the Lineage thread". The thread note's `kind: THREAD` and its `interface:` frontmatter are codex-only and are **not emitted**.

**The pieces are linked by shared ids and flags, not by a container.** Every source (a World Event, a Want's `urgent_when` or `on_deadline`, a Quest milestone, a Campaign `unlocks` entry) is a `when`/`then` pair. The compiler works out each source's **watch set**: the keys its Condition reads, such as `flag:lin_take_due` or `edge:faction_lineage:CONTROLS:npc_ennis_pell` (Design 23.3 §5.2). When an Effect changes a key, the engine re-evaluates only the sources that watch it. The chain is therefore a graph of names:

| Link | Written as |
|---|---|
| Want to event | `on_deadline: set_flag lin_take_due`; the event's `when` tests `flag_set lin_take_due` |
| Event to Want | the Want's `urgent_when: flag_set lin_s2_snatch`, or an `activate_want` / `fail_want` Effect naming the Want id |
| Event to event | one sets a flag the other tests, or `event_occurred evt_x` |
| Quest to Want | `from_want` and the Want's `resolution_paths` |
| Quest to thread | `on_complete` sets flags, adds or removes edges, and reveals Facts |
| Fact to thread | `reveal_fact` and `fact_revealed`; `known_by` through NPC ids |
| Campaign to thread | the genesis event sets `lin_armed`; `unlocks` read thread flags |

**The armed flag is the only switch for a whole thread.** The thread is "linked" because its sources share these names; remove the armed flag and nothing in the chain ever starts.

What follows:

- **A misspelt flag is a source that never fires.** The engine's validator checks that flags are declared and that references exist (Design 23.3 §8). The codex's `tools/thread-check.mjs` checks the same things now (flags set and read, references inside Conditions and Effects, own-stage guards). The platform's own `author-cli validate` does not exist yet (PR-1, PF-5).
- **The engine cannot answer thread-level questions.** It cannot tell the story agent which threads are active or how far each has advanced; it only holds the stage flags. Authoring tools, the DM Narrator and any plot-web view would have to reconstruct a thread from flag prefixes. A Campaign cannot suppress or version a thread as a unit either: `suppresses` takes entity ids and versioning is per entity hash, so disabling a thread means **not arming it**.
- **The grouping lives only in the codex:** in the thread note, its `interface` block, the `<thread>_` naming convention and the tools (and, later, the Step 14 compiler).
- **An optional `thread` label (PF-6, to be filed in Step 2c).** An optional `thread: <slug>` field on any authored entity, with no meaning to the rules, used only for tooling, observability, `author-cli diff` grouping and the narrator's context retrieval. It is not needed for correctness. **The codex records membership now:** the thread note's frontmatter carries `thread: lin` (its Events and Facts inherit it), and a block that lives in another note (a Want in its NPC's note, a Quest in its Module's note, a Campaign's genesis event) carries a `_thread: lin` directive. `tools/transform.mjs` strips the directive today, because the package rejects unknown fields, and writes `thread: lin` on the entity when `EMIT_THREAD_LABEL=1` and the platform accepts it.

### 7.3 Patterns that make a thread robust to the player

| Pattern | What it does | Pilot example |
|---|---|---|
| **Wants propose, events dispose** | A Want's fallback sets an *intent* flag. A World Event applies it only if the guards still hold. A late intent is inert. | `lin_take_due` does nothing if Ennis is guarded or no longer in the starting town |
| **Successors** | When the key actor is removed, a World Event brings the next. | Fell dies, and Sorn comes (`evt_lin_fell_removed`) |
| **Escalation sweep** | When the thread's hands are removed, the head sends heavier ones, which finish every open errand at once. Killing the retriever *speeds the thread up*. | `evt_lin_retriever_lost` sets all four intents |
| **Inference events** | An event turns *state evidence* (a location, a death) into the thread's canonical flags and edges, so an unscripted act is not a dead end. | `evt_lin_ennis_missing`: Ennis left the starting town, so someone hid him |
| **Unrolled cycles** | Events fire once, so a repeating beat is written as numbered cycles with a floor. | two reprieve cycles, then `lin_hunt_exhausted` |
| **Ratchet floor (LOCKED)** | The thread cannot be ended by killing one person. | the second candidate, 1,800 days on |
| **Explicit retirement** | A Quest that defeats a Want says so (`fail_want`). A Want is not retired by the world moving past it. | the rescue Quest fails four Wants |
| **Terminals close the thread** | A terminal event (listed in `interface.terminals`) leaves no Want of its thread running. The simulator checks this in every scenario. | `evt_ferry_settled` (campaign-authoring-guide 4.7) |

Each pattern was found by a scenario that stalled without it (pilot-thread-findings).

## 8. Quests, Campaigns and chaining

### 8.1 Quest contracts

A thread does not write Quests. It writes **contracts**: for each outcome, the effects any Resolution Path must apply and the Wants it must retire (a table in the thread card). A Campaign's Module writes the Quest and applies the contract in `on_complete`. This keeps the thread stable while Campaigns vary, and makes "skipped Quests" safe: the Want's deadline is the same fallback the contract replaces.

Until **PR-11**, a Quest has one ending. Alternative outcomes are **alternative Quests** that are Resolution Paths of the same Want. Until **PR-13**, a Quest cannot say it is no longer available; the pilot keeps the gates in `campaigns/dustport-pilot/scenarios/pilot-quest-gates.yaml` and the simulator refuses a Quest the world has moved past.

### 8.2 The Campaign's job

1. **Arm** the threads it uses (a genesis event in its overlay, guarded by `not <thread>_armed`).
2. **Set the stage** it begins at, by flags (fast-forward).
3. **Unlock Modules** from thread state (`unlocks: flag_set ...`).
4. **Override authority** on its key beats (`LOCKED`) through the overlay.
5. **Define outcomes** (end states) as flags. The Campaign reads thread outputs and sets its own.

### 8.3 Chaining Campaigns

Design 23 §2 gives a Sandbox exactly one Campaign. The target is a **Campaign Succession** (PR-10): Campaign B declares `follows: camp_A` and the outcome it requires, and a Sandbox adopts B at a safe point, keeping its character and world state; hydrated entities stay frozen (ADR-0002), and B's `transition` effects set up its start. **Until then**, the long arc is **one Campaign with Acts**: Modules grouped and unlocked by outcome flags. Both read the same thread flags, so a thread written now works for either.

### 8.4 Authority

| Level | Use in the plot web |
|---|---|
| `LOCKED` | permanence rules and ratchet floors; the truth of the past (Facts) |
| `GUIDED` (default) | stage events: the engine fixes *that* it happens; the LLM shapes *how* |
| `OPEN` | a Want the party can resolve however it likes, so long as a different Want holds the deterministic fallback (Rusk's Want, with Sorn's deadline as its fallback) |

## 10. The compact form (a Step 14 deliverable)

The pilot's 22 events and 15 Wants were generated from a small Python table (deleted at T4; git history keeps it as the compiler's seed), and every one carries the same boilerplate: the armed test, the own-stage guard, an intent flag, an `all:` wrapper. Hand-writing 18 threads at that scale (about 40 blocks each) invites mistakes. **The thread card should hold a compact `thread` block that the transformer compiles.** A sketch:

```yaml
kind: THREAD_GRAPH            # codex-only; compiled to WORLD_EVENT and WANT blocks
thread: lin
arm: lin_armed
stages:
  - id: lin_s2_snatch
    on: { flag: lineage_snatch_attempt }         # compiles to a guarded WORLD_EVENT
    then: [ { move_npc: ... } ]
  - id: lin_ennis_taken
    after: { want: want_sorn_take_ennis, days: 20, by: npc_halvard_sorn, urgent: lin_s2_snatch }
    unless: [ { edge: [npc_dagna_rusk, GUARDS, npc_ennis_pell] } ]
    then: [ { add_edge: ... } ]
```

The compiler adds the armed test, the own-stage guard, the intent flag, and the unrolled cycles. It is out of scope for Step 12; Step 12 writes the cards and, until the compiler exists, blocks where a thread is complex.

## 11. Engine assumptions to confirm (PR-12)

The simulator states six assumptions where Design 23.3 is silent (pilot-thread-findings, section 3). The load-bearing ones: a Want's clock starts when `urgent_when` first holds; `urgent_when` only activates; `resolve_want` and `fail_want` stop `on_deadline`; a dead NPC's own Wants fail but nobody else's do. Also to confirm: World Events with scope `MACRO` or `REGIONAL` are evaluated for **every** Sandbox regardless of where the player is (Design 23.3 §5.2 says "global sources" without defining them), and the platform's cascade-depth limit is at least five rounds (the pilot reaches four).

## Links

- `campaign-authoring-guide.md` — the how-to that follows this reference
- `conventions.md` §9.7 — CP-8, CP-9, CP-10 and CP-11, the authoring patterns this pattern needs
- `engine-capability-register.md` — PR-9…PR-13, the platform gaps it rests on

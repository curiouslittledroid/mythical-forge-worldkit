# The Thread Pattern

**Summary:** How a plot web is built so that **each player's Sandbox can evolve differently**, and so
that the three story layers — the World, Campaigns, and Modules/Quests — share one world without
breaking each other. **This is the reference (the why).** The step-by-step tutorial is
`campaign-authoring-guide.md`.

**Status of the examples.** The worked example is the demo world shipped at `example-world/`: **the
Ferryman's Debt**, a small Resolvable thread with a campaign, two modules and six scenarios. It is
**not canon**. Where a pattern needs something the demo does not have — a Managed ladder, a long
Ratchet — the example is described by shape rather than named. A world's own thread cards live in
its `world/plot-web/`.

**Where the engine cannot yet follow**, the requests are `PR-9`…`PR-13`, opened with the engine's
owner. They are not yours to decide, and nothing here waits on them.

## 1. The problem

A Sandbox is one player's copy of one Campaign, pinned to a World version. Its state diverges: players kill the people the plot depends on, skip Quests, and hide, rescue or lose the same person. So:

- A **shared calendar of dated events cannot exist**. Every Sandbox has its own day counter, and an event keyed to a day fires in every Sandbox of every Campaign.
- A **thread must survive what the player does** (a death, a skipped Quest, an unscripted act), not only what the author imagined.
- A **later Campaign must be able to start the same thread at a different stage**, and a Campaign set elsewhere must be able to leave it dormant.

## 2. The three layers

| Layer | Owns | Is written as |
|---|---|---|
| **World** | What is true and what is pushing: history, Facts, places, factions, NPCs, **Wants (the engines of motion)**, **thread World Events**, the flag vocabulary. Nothing in it mentions the player. | Thread cards (the demo's `the-ferrymans-debt.md` is the model), in `world/plot-web/` |
| **Campaign** | Purpose and starting point: which threads are armed and at what stage, which beats are `LOCKED`, which Modules unlock, the end state. | A Campaign, an overlay with a **genesis event**, and `unlocks` that read thread flags |
| **Module / Quest** | A bounded set of choices at a place. A Quest is a **Resolution Path** of a Want, so skipping it lets the Want's deadline fire instead. | Modules with Quests that apply a **quest contract** |

**Flags are the API between the layers.** The World publishes them; Campaigns and Modules read and set the ones a thread lists in its interface.

### 2.1 The Campaign and its Overlay

A Campaign is two engine entities, not one. A **Campaign block** says what the Campaign *is*; a **Campaign Overlay** says how it *changes the World* for its Sandboxes. Neither is a thread-style grouping: both are real engine entities (`kind: CAMPAIGN` and `kind: CAMPAIGN_OVERLAY`).

| | **Campaign** | **Campaign Overlay** |
|---|---|---|
| **Purpose** | the storyline a player picks | how the Campaign changes the shared World for its Sandboxes |
| **Contains** | title, summary, `start_level`, `start_day`, `start_location`, `opening_module`, the Module list, `unlocks`, content descriptors, Campaign flags | `adds`, `overrides`, `suppresses` |
| **Read by** | the Campaign picker, the Module Selector | the layered read, `Merge(World, Overlay, Sandbox Delta)` |

The overlay has three operations only:
- **`adds`:** new entities that exist only in this Campaign (NPCs, Wants, Facts, World Events and so on). The demo's genesis event is one.
- **`overrides`:** field-level patches to World entities, keyed by the entity's own id (for example a Want's `authority`, or an NPC's voice).
- **`suppresses`:** World entities that do not exist in this Campaign.

An overlay may touch authored fields only. It cannot change ids, kinds or structural fields, and it cannot add Campaigns, Modules or Migrations.

**Why they are separate.** The engine's design does not state the reason; this is the reading that fits the rest of it:

1. **They answer different questions.** The manifest is what a player sees in the picker: a few fields and no World content. The overlay is a patch set aimed at World entities.
2. **The overlay drives the version rules.** An entity the overlay overrides counts as "overridden" in the adoption logic: a later World edit to it is pinned, not applied silently. An entity's effective hash is the World object plus any override. That logic needs the overlay as its own thing.
3. **They can grow and change independently.** An overlay can add hundreds of entities while the manifest stays small, and each can be hashed and versioned separately in the content store.
4. **The overlay is optional.** A Campaign that changes nothing in the World needs none, and the schema rejects an empty one ("an overlay must add, override or suppress something").

The two are tied by ids: the overlay carries `campaign_id`, and the Campaign does not list its overlay.

**In the demo**, `camp_ferry_demo` is the Campaign block and `overlay_ferry_demo` adds the genesis event that sets `ferry_armed` and overrides one Want's deadline (section 8.2). The transformer writes them as `campaign.yaml` and `overlay.yaml` in the same folder.

## 3. The flag vocabulary

| Family | Meaning | Set by | Read by | Example |
|---|---|---|---|---|
| **Armed** | "This thread is live in this Sandbox." | a Campaign's start state | the thread's first Wants and events | `ferry_armed` |
| **Stage** | History: the thread has reached stage N. One-way. | the thread's own events | everyone | `<thread>_s3_<stage>` |
| **Intent** | "A deadline passed; this *may* now happen." A proposal, not a fact. | a Want's `on_deadline` | the World Event that applies it, if the guards still hold | `ferry_collect_due` |
| **Outcome** | Which fork the player took. | a Quest contract | the thread, Campaigns, Modules | `ferry_debt_paid` |
| **Counter** | Repeated acts counted to a threshold. | several sources, once each | a `flag_count_gte` Condition | `<thread>_<act>_count` |
| **Trait** | A property of one entity (CP-4). | the genesis event | Conditions that name `toward` | a trait flag, scoped to one NPC |
| **Input / Output** | A flag one thread reads that another sets. | other thread | this thread | `<other-thread>_<output>` |

**Edges are the current state; flags are the history.** Custody of Reed is the edge `faction_ferry_creditors CONTROLS npc_tomas_reed` (or `faction_dust_ferrymen GUARDS npc_tomas_reed`). A flag such as `ferry_sold_on` stays set after he is bought back; the edge does not. Conditions that need "is it true now?" test the edge. Conditions that need "did it ever happen?" test the flag. A Fact carries what people know; a flag carries what happened.

### 3.1 What an armed flag is

An **armed flag** is a flag whose only job is to say *this thread is live in this Sandbox*. It is set once, by the Campaign's start state, and every opening Want and event in the thread is gated by it (`urgent_when: all: [ferry_armed, ...]`).

- **Unarmed, a thread is dormant lore.** Its NPCs have Wants that never become urgent, and its events never fire. A Campaign set elsewhere, or a century later, simply never arms the thread, and it costs nothing.
- **Armed, a thread runs.** The world moves without the player.
- **Arming is not a stage.** It says *the thread is live*, not *it is at stage 1*. A Campaign can arm a thread and also set stage flags to start it mid-story (section 5).
- **Why not a date?** A `day_reached` start would fire in every Sandbox on the same day regardless of Campaign, and an event added in a later version would fire at once in any Sandbox already past that day.

## 4. Time

| What | How | Why |
|---|---|---|
| A season or festival | `season_is`, from the World calendar (Step 9) | it is genuinely calendar-shaped |
| "N days after X" | a **Want timer**: a Want whose `urgent_when` is X, with `deadline_days: N` (CP-9) | `deadline_days` is relative to activation, which is a native relative timer |
| "N days after X" for a non-NPC clock | `days_since` (**PR-9**; until then use an NPC anchor) | FLAG items already store `first_day` |
| "On day N" | only in a Campaign's own overlay | a Campaign owns its own clock |

A thread's **default pace** ("if left alone") is therefore the sum of its timers. It is generated by the idle simulation, not hand-written (the kit's `meta/conventions/campaign-authoring-guide.md` section 3.1).

## 5. Guards and fast-forward

The engine applies a source **exactly once** per Sandbox. That is true of firing, but nothing records that an event "has occurred" for a Sandbox that was *started past it*. If a Campaign sets stage 3 directly, an earlier event whose Condition is still true would fire at day 0 and re-apply its Effects.

**The own-stage guard (CP-8):** every World Event, and every Want that sets an intent flag, tests `not flag_set <its own result flag>`. A Campaign that sets that flag, or any later one, silently retires the source. `thread-check` catches a removed guard statically; only a fast-forward scenario shows the event re-firing dynamically, so write one whenever a thread can start mid-story.

**Fast-forward** is therefore just a list of flags, edges and NPC moves: the net state of the idle world up to a stage. `tools/simulate-world.mjs` generates it. A limit: timers in progress restart (a Want whose clock was half-run restarts at day 0), so fast-forward to a boundary where the next clock has not started.

## 6. Resolution classes

### 6.1 Resolvable

**The thread has terminal outcomes that stick. Once one is reached, the thread stops generating events, and later Campaigns inherit the result.**

- **Shape:** a short graph that ends in two to four terminals, with no loops. One terminal is the **idle terminal**: where the thread ends if nobody intervenes (usually the grimmest).
- **What the player can do:** pick a terminal. Each is a permanent shift (an edge added or removed, a flag set), never a restoration (permanence-rules).
- **Examples:** a succession that ends with a named heir or a split; a secret that is exposed, buried or bought off; a contact that is opened or refused; a pact renewed or broken; a truth told or kept. The demo's ferry thread is the smallest version: sold on (the idle terminal), debt paid, or fled.
- **Authoring rule:** every terminal must be reachable (validator producer analysis), and the idle terminal must be reached by the idle simulation.

### 6.2 Managed

**The pressure never ends, but the player can move the thread between states and buy bounded reprieves. Each reprieve costs something and the cycles are bounded; once they are spent, the pressure resumes unconditionally.**

- **Shape:** a pressure ladder with side-states ("reprieves") that restart a timer. Because engine events fire once, the cycles are **unrolled** and capped (author two reprieve cycles, then the thread's floor flag; a third is not authored).
- **What the player can do:** delay, redirect or hand the problem to someone else. They cannot remove it.
- **Examples:** a schism inside one institution; a succession dispute; a minority community under pressure; a diaspora; a custody loop.
- **Authoring rule:** the **floor** (what happens when reprieves run out) is authored and reached by the idle simulation. A reprieve must be bought with a Quest, a cost or a trade, never free.

### 6.3 Ratchet

**The thread only moves forward. No state in the graph restores anything. The best the player can do is slow it or redirect its effects.**

- **Shape:** a one-way ladder, often long. A reprieve replaces a timer with a longer one; it never goes back a stage.
- **What the player can do:** delay and mitigate. This is where the permanence rules live: because no Effect anywhere produces the restored state, the validator can *prove* the world cannot be fixed (a Condition with no producer is unsatisfiable).
- **Examples:** a war that is already lost; a resource that is finite and picked clean; a trade nobody can leave; a conflict older than either side; a watch that is waking; a faction splitting on a clock nobody can stop.
- **Authoring rule:** use `LOCKED` outcomes where the ratchet must not be avoidable, and test that the idle run reaches the last stage within the horizon.

### 6.4 Mixed threads

Most real threads mix shapes. Classify by the **dominant** shape and record the others. A thread can be **Managed** (a custody loop), have a **Resolvable** terminal, and still hold a **Ratchet** floor (a `LOCKED` event that guarantees a successor).

**A world's own threads are classified in its own note**, one row each, and a Campaign records which
class it is arming.

## 7. Threads

### 7.1 How is a thread stored

A **thread card** is the thread's **note** (`world/plot-web/the-ferrymans-debt.md` in the demo). It has two halves:

| Half | What is in it | Who reads it |
|---|---|---|
| **The document** | premise, actors and successors, the state graph, interface, quest contracts, the idle run, hooks | people and agents. This is the design. |
| **The `## Engine` section** | the thread's **World Events** and its **Facts**, as `engine` blocks | the transformer and the engine |

The note's frontmatter (`thread:` and `interface:`) is also part of the card, but it is codex-only and never reaches the engine.

**The card does not hold the whole thread.** Each block lives in the note of the thing it belongs to (conventions §9.1), so the thread is spread across the vault:

| Piece | Where it lives |
|---|---|
| World Events, Facts | the thread card |
| **Wants** | each NPC's note (the demo's collect, deliver and sell Wants are in `odo-marsh.md`; the debtor's own Want in `tomas-reed.md`) |
| **Quests** | the Module notes in the Campaign |
| **The genesis event** that arms the thread | the Campaign's overlay note |
| **Flags** | the flags note, the one `vault.notes.flags` names |
| NPCs, factions, relationships | their own notes |

Two terms keep this clear:
- **Thread card** means the note: the design document plus its own event and Fact blocks.
- **Thread** means the whole set of linked pieces across all those notes. The card documents it but does not contain it.

The Step 14 thread compiler (section 10) changes this: the card would hold a compact graph, and the compiler would produce the events and Wants and place them in the right notes' output.

### 7.2 How a thread is linked (there is no thread entity)

**The engine has no `THREAD` entity, and has no grouping of any kind.** Its kinds are NPC, WANT, FACT, RELATIONSHIP, WORLD_EVENT, QUEST, ROOM, ENCOUNTER, FACTION, ITEM, MONSTER, MODULE, CAMPAIGN, CAMPAIGN_OVERLAY, MIGRATION and OVERLAND_GRAPH. A thread is a **codex concept**.

When the transformer runs, a thread card becomes separate files (`world/events/evt_ferry_*.yaml`, `world/facts/...`, `world/wants/...`, and Quests under `campaigns/...`). Nothing in those files says "I belong to that thread". The thread note's `kind: THREAD` and its `interface:` frontmatter are codex-only and are **not emitted**.

**The pieces are linked by shared ids and flags, not by a container.** Every source (a World Event, a Want's `urgent_when` or `on_deadline`, a Quest milestone, a Campaign `unlocks` entry) is a `when`/`then` pair. The compiler works out each source's **watch set**: the keys its Condition reads, such as `flag:ferry_collect_due` or `edge:faction_ferry_creditors:CONTROLS:npc_tomas_reed`. When an Effect changes a key, the engine re-evaluates only the sources that watch it. The chain is therefore a graph of names:

| Link | Written as |
|---|---|
| Want to event | `on_deadline: set_flag ferry_collect_due`; the event's `when` tests `flag_set ferry_collect_due` |
| Event to Want | the Want's `urgent_when: flag_set <thread>_<stage>`, or an `activate_want` / `fail_want` Effect naming the Want id |
| Event to event | one sets a flag the other tests, or `event_occurred evt_x` |
| Quest to Want | `from_want` and the Want's `resolution_paths` |
| Quest to thread | `on_complete` sets flags, adds or removes edges, and reveals Facts |
| Fact to thread | `reveal_fact` and `fact_revealed`; `known_by` through NPC ids |
| Campaign to thread | the genesis event sets `ferry_armed`; `unlocks` read thread flags |

**The armed flag is the only switch for a whole thread.** The thread is "linked" because its sources share these names; remove the armed flag and nothing in the chain ever starts.

What follows:

- **A misspelt flag is a source that never fires.** The engine's validator checks that flags are declared and that references exist. The codex's `tools/thread-check.mjs` checks the same things now (flags set and read, references inside Conditions and Effects, own-stage guards). The platform's own `author-cli validate` does not exist yet (PR-1, PF-5).
- **The engine cannot answer thread-level questions.** It cannot tell the story agent which threads are active or how far each has advanced; it only holds the stage flags. Authoring tools, the DM Narrator and any plot-web view would have to reconstruct a thread from flag prefixes. A Campaign cannot suppress or version a thread as a unit either: `suppresses` takes entity ids and versioning is per entity hash, so disabling a thread means **not arming it**.
- **The grouping lives only in the codex:** in the thread note, its `interface` block, the `<thread>_` naming convention and the tools (and, later, the Step 14 compiler).
- **An optional `thread` label (PF-6, to be filed in Step 2c).** An optional `thread: <slug>` field on any authored entity, with no meaning to the rules, used only for tooling, observability, `author-cli diff` grouping and the narrator's context retrieval. It is not needed for correctness. **The codex records membership now:** the thread note's frontmatter carries `thread: ferry` (its Events and Facts inherit it), and a block that lives in another note (a Want in its NPC's note, a Quest in its Module's note, a Campaign's genesis event) carries a `_thread: ferry` directive. `tools/transform.mjs` strips the directive today, because the package rejects unknown fields, and writes the thread label on the entity when `EMIT_THREAD_LABEL=1` and the platform accepts it.

### 7.3 Patterns that make a thread robust to the player

| Pattern | What it does | Demo example |
|---|---|---|
| **Wants propose, events dispose** | A Want's fallback sets an *intent* flag. A World Event applies it only if the guards still hold. A late intent is inert. | `ferry_collect_due` does nothing if Reed is guarded or no longer in Dustport |
| **Successors** | When the key actor is removed, a World Event brings the next. | the clerk dies, and an enforcer arrives (`evt_ferry_collector_replaced`) |
| **Escalation sweep** | When the thread's hands are removed, the head sends heavier ones, which finish every open errand at once. Killing the collector *speeds the thread up*. | `evt_ferry_collector_replaced` sets all three intents |
| **Inference events** | An event turns *state evidence* (a location, a death) into the thread's canonical flags and edges, so an unscripted act is not a dead end. | `evt_ferry_missing`: the debtor left Dustport, so someone hid him |
| **Unrolled cycles** | Events fire once, so a repeating beat is written as numbered cycles with a floor. | two reprieve cycles, then the thread's floor flag |
| **Ratchet floor (LOCKED)** | The thread cannot be ended by killing one person. | a second claimant is guaranteed, however long it takes |
| **Explicit retirement** | A Quest that defeats a Want says so (`fail_want`). A Want is not retired by the world moving past it. | the buy-back Quest fails the delivery and sale Wants |
| **Terminals close the thread** | A terminal event (listed in `interface.terminals`) leaves no Want of its thread running. The simulator checks this in every scenario. | `evt_ferry_settled`, `evt_ferry_gone`, `evt_ferry_sold_on` |

Each pattern was found by a scenario that stalled without it; the demo's six scenarios are the small version of that method.

## 8. Quests, Campaigns and chaining

### 8.1 Quest contracts

A thread does not write Quests. It writes **contracts**: for each outcome, the effects any Resolution Path must apply and the Wants it must retire (a table in the thread card). A Campaign's Module writes the Quest and applies the contract in `on_complete`. This keeps the thread stable while Campaigns vary, and makes "skipped Quests" safe: the Want's deadline is the same fallback the contract replaces.

Until **PR-11**, a Quest has one ending. Alternative outcomes are **alternative Quests** that are Resolution Paths of the same Want. Until **PR-13**, a Quest cannot say it is no longer available; the demo keeps the gates in `campaigns/ferryman-demo/scenarios/quest-gates.yaml` and the simulator refuses a Quest the world has moved past.

### 8.2 The Campaign's job

1. **Arm** the threads it uses (a genesis event in its overlay, guarded by `not <thread>_armed`).
2. **Set the stage** it begins at, by flags (fast-forward).
3. **Unlock Modules** from thread state (`unlocks: flag_set ...`).
4. **Override authority** on its key beats (`LOCKED`) through the overlay.
5. **Define outcomes** (end states) as flags. The Campaign reads thread outputs and sets its own.

### 8.3 Chaining Campaigns

The engine gives a Sandbox exactly one Campaign. The target is a **Campaign Succession** (PR-10): Campaign B declares `follows: camp_A` and the outcome it requires, and a Sandbox adopts B at a safe point, keeping its character and world state; hydrated entities stay frozen (ADR-0002), and B's `transition` effects set up its start. **Until then**, the long arc is **one Campaign with Acts**: Modules grouped and unlocked by outcome flags. Both read the same thread flags, so a thread written now works for either.

### 8.4 Authority

| Level | Use in the plot web |
|---|---|
| `LOCKED` | permanence rules and ratchet floors; the truth of the past (Facts) |
| `GUIDED` (default) | stage events: the engine fixes *that* it happens; the LLM shapes *how* |
| `OPEN` | a Want the party can resolve however it likes, so long as a different Want holds the deterministic fallback |

## 10. The compact form (a Step 14 deliverable)

A long thread's events and Wants all carry the same boilerplate: the armed test, the own-stage
guard, an intent flag, an `all:` wrapper. Hand-writing many threads at that scale (about 40 blocks
each) invites mistakes. **The thread card should hold a compact `thread` block that the transformer compiles.** A sketch:

```yaml
kind: THREAD_GRAPH            # codex-only; compiled to WORLD_EVENT and WANT blocks
thread: ferry
arm: ferry_armed
stages:
  - id: ferry_s2_seized
    on: { flag: ferry_collect_due }              # compiles to a guarded WORLD_EVENT
    then: [ { move_npc: ... } ]
  - id: ferry_transit
    after: { want: want_marsh_deliver_reed, days: 30, by: npc_odo_marsh, urgent: ferry_s2_seized }
    unless: [ { edge: [faction_dust_ferrymen, GUARDS, npc_tomas_reed] } ]
    then: [ { add_edge: ... } ]
```

The compiler adds the armed test, the own-stage guard, the intent flag, and the unrolled cycles. It is out of scope for Step 12; Step 12 writes the cards and, until the compiler exists, blocks where a thread is complex.

## 11. Engine assumptions to confirm (PR-12)

The simulator states six assumptions where the engine's design is silent. The load-bearing ones: a Want's clock starts when `urgent_when` first holds; `urgent_when` only activates; `resolve_want` and `fail_want` stop `on_deadline`; a dead NPC's own Wants fail but nobody else's do. Also to confirm: World Events with scope `MACRO` or `REGIONAL` are evaluated for **every** Sandbox regardless of where the player is (the design says "global sources" without defining them), and the platform's cascade-depth limit is at least five rounds (a real cascade reaches four).

## Links

- `campaign-authoring-guide.md` — the how-to that follows this reference
- `campaign-authoring-guide.md` — the same patterns as a worked recipe
- this document's own CP- and PR- ids — the authoring patterns it needs, and the platform gaps it
  rests on

# Campaign and Thread Authoring Guide

**Summary:** A step-by-step tutorial for building a **thread**, a **Campaign**, its **Modules** and **Quests**, and every engine block they need. `docs/thread-pattern.md` is the reference (the *why*). This guide is the *how*: it walks one small example from a blank page to a passing test. It will be replaced by an authoring tool one day; until then it is the tool.

> **Status: staged, and not yet neutral.** This guide moved out of a world's `meta/` at extraction T3f
> (decision D31) and is de-branded at T7: its worked example is already the world-agnostic
> *Ferryman's Debt*, but Part 8 and a few asides still name one world's campaign and its threads. The
> engine rules below are correct for any world today; the examples are the ones T7 will swap.

## How to use this guide

- **Read Part 1 once.** Then follow Parts 3 to 6 with the example open, and copy the pattern for your own thread.
- **The running example is the Ferryman's Debt**, a small *Resolvable* thread (`world/plot-web/the-ferrymans-debt.md`). **It is the demo world this repository ships, not canon**, and it is laid out exactly as it would sit in a real vault: its people in `world/npcs/`, its factions in `world/factions/`, its Campaign, Modules and Quests in `campaigns/ferryman-demo/`. Run `./verify-kit.sh` to watch the whole pipeline build and test it.
- **Every block in this guide is copied from that example**, and the example is built and tested by a script: `tools/verify-example.sh` copies the vault to a throwaway directory, drops the example in, and runs lint, transform, validate, `thread-check` and six scenarios. `tools/check-guide.mjs` checks every `yaml` block in this guide against the engine's own schema. If a block here stops being valid, one of those fails.
- **For a Managed or Ratchet thread**, the demo world has only a *Resolvable* one. A real world's pilot thread is the next thing to read: 20 events and 16 scenarios is a reasonable size for a first Managed thread.

| Part | You will |
|---|---|
| 1 | learn the model: layers, block kinds, how things link |
| 2 | learn the rules every note follows (ids, flags, vocabularies) |
| 3 | design a thread on paper |
| 4 | write the World layer, block by block |
| 5 | write the Campaign layer: Campaign, overlay, Modules, Quests, sites |
| 6 | test it |
| 7 | review it, and fix common errors |
| 8 | scale up to the 18 threads |
| A to E | look things up (blocks, Conditions, Effects, vocabularies, files) |

---

# Part 1. The model

## 1.1 Three layers

| Layer | What it holds | You write |
|---|---|---|
| **World** | what is true and what is pushing: NPCs and their **Wants**, factions, Facts, relationships, and the **World Events** that move a thread | a *thread card* and the NPC notes |
| **Campaign** | purpose and starting point: which threads are *armed*, the Modules, how Modules unlock | a Campaign, an **overlay**, Modules |
| **Module / Quest** | a bounded set of choices at a place | Modules, **Quests**, rooms, encounters |

The World never mentions the player. A Campaign decides which of the World's threads are live. A Quest is one way the player can resolve a Want; if the player skips it, the Want's deadline fires instead, and the world moves on without them.

## 1.2 The block kinds, and where each lives

A **block** is a fenced `engine` code block of YAML inside a note. The transformer extracts it and writes one file per entity.

| Block `kind` | Lives in the note of | Part |
|---|---|---|
| `FLAGS` (a `flags` block, not an entity) | the world's flag register | 4.1 |
| `NPC` | the NPC | 4.2 |
| `FACTION` | the faction | 4.3 |
| `RELATIONSHIP` | its `from` entity | 4.4 |
| `FACT` | the topic or thread it is about | 4.5 |
| `WANT` | its NPC | 4.6 |
| `WORLD_EVENT` | its thread | 4.7 |
| `CAMPAIGN` | the Campaign note | 5.1 |
| `CAMPAIGN_OVERLAY` | the overlay note | 5.2 |
| `MODULE` | the Module note | 5.3 |
| `QUEST` | its Module's note | 5.4 |
| `ROOM`, `ENCOUNTER`, `ITEM`, `MONSTER` | the Module (or place) note | 5.5 |
| `OVERLAND_NODE`, `OVERLAND_EDGE` | the place note (fragments the transformer assembles) | conventions §9.2 |

## 1.3 How the pieces link (there is no thread entity)

The engine has no `THREAD` entity. **Pieces are linked by shared ids and flags.** A Want's deadline sets a flag; an event's `when` tests that flag; the event sets another flag; a Quest tests it. Read `docs/thread-pattern.md` section 7.2 for the full table. The one rule to remember: **the armed flag is the thread's switch.** A Campaign sets it; the thread's first Wants and events test it. No armed flag, no thread.

## 1.4 The loop

You write notes, then run the tools. Each tool catches a different kind of mistake.

| Step | Command | Catches |
|---|---|---|
| 1 | `python3 tools/lint.py` | frontmatter, ids, dead links, undeclared flags, unbalanced `[[ ]]`, ids referenced in blocks that nothing defines |
| 2 | `node tools/transform.mjs` | invalid YAML, unresolved group knowledge |
| 3 | `node tools/validate-world.mjs` | schema errors (the engine's own Zod schemas) |
| 4 | `node tools/thread-check.mjs` | flags set but never read (or the reverse), missing own-stage guards, ids inside Conditions and Effects that point at nothing, a thread interface that does not match its blocks |
| 5 | `node tools/simulate-world.mjs --coverage` | a thread that stalls, fires the wrong event, or never reaches a terminal; a block never exercised |

Run the whole chain after every change. It takes seconds.

---

# Part 2. Rules every note follows

## 2.1 Anatomy of a note

~~~markdown
---
id: npc_tomas_reed          # engine id; prefix matches the kind
kind: NPC
title: Tomas Reed           # the filename is the kebab-case slug: tomas-reed.md
name_status: working        # is the NAME final?
status: working             # working | agreed | engine-ready | deprecated
engine: true                # true once the note has real `engine` blocks
era: present
groups: [{ id: faction_dust_ferrymen, rank: common }]   # NPC only: factions and rank
home: loc_dustport
---

# Tomas Reed

**Summary:** ...

## Details / Secrets / Hooks / Links / Open questions
...

## Engine
(the engine blocks go here, each in a fenced `engine` block:
 kind: NPC
 id: npc_tomas_reed
 ...)
~~~

- **`engine-example`** is the same fence for blocks that are not real yet. The linter and `thread-check` read them; the transformer does not. A note with any real `engine` block must say `engine: true`.
- **Never author** `author_id`, `world_id` (except inside a `CAMPAIGN` block), or derived values (`hp`, `ac`, `bab`, `cr`). The linter and schema reject them.
- Write prose in **British English**. `toward` is a YAML key and is fine inside a block; in prose write *towards*.

## 2.2 Ids and filenames

- **Grammar:** lowercase tokens joined by single underscores, starting with a letter, at least two tokens, at most 100 characters: `npc_tomas_reed`. Ids never change once published.
- **Prefixes** (the engine checks them): `npc_` `want_` `fact_` `rel_` `evt_` `quest_` `room_` `enc_` `faction_` `item_` `mon_` `mod_` `camp_` `overlay_` `mig_` `loc_` `zone_` `srd_` `obj_`. Codex-only: `thread_` `hist_` `fig_` `god_` `race_` `topic_`.
- **Filenames** are the kebab-case slug of the title and are **unique vault-wide**.
- **Flags** are `lower_snake_case`, and may be a single token.
- **Milestone ids** follow the id grammar too (at least two tokens): `ms_ask`, not `ask`.

## 2.3 The closed vocabularies

You cannot extend these. If the world needs something else, log it in the engine-capability register and use the nearest pattern.

| Set | Values |
|---|---|
| Authority | `LOCKED` `GUIDED` `OPEN` |
| Want methods | `PERSUADE` `HIRE` `STEAL` `THREATEN` `VIOLENCE` `FLEE` |
| Relationship kinds (`kind_of`) | `KIN_OF` `ALLY_OF` `RIVAL_OF` `ENEMY_OF` `LOVES` `FEARS` `DISTRUSTS` `OWES` `MEMBER_OF` `LEADS` `SERVES` `SECRETLY_SERVES` `EMPLOYS` `RESIDES_AT` `GUARDS` `CONTROLS` `OWNS` `SEEKS` `KNOWS_SECRET_OF` `BELIEVES` |
| Visibility | `PUBLIC` `SECRET` `{ known_by: [npc_x] }` |
| Scope (World Event) | `LOCAL` `REGIONAL` `MACRO` |
| Alignment | `LAWFUL_GOOD` `NEUTRAL_GOOD` `CHAOTIC_GOOD` `LAWFUL_NEUTRAL` `TRUE_NEUTRAL` `CHAOTIC_NEUTRAL` `LAWFUL_EVIL` `NEUTRAL_EVIL` `CHAOTIC_EVIL` |
| Encounter tactics | `AMBUSH` `DEFEND_POSITION` `PURSUE` `FLEE_AT_HALF_HP` |
| Milestone types | `DIALOGUE` `FETCH` `DELIVER` (labels only — see §5.4) |
| Content descriptors | `VIOLENCE` `HORROR` `MATURE_THEMES` |
| Judgement tags (tested only, never set by you) | `CRUEL` `MERCIFUL` `DECEITFUL` `HONOURABLE` |
| Room | lighting `NORMAL` `SHADOWY` `DARK`; directions `NORTH` `SOUTH` `EAST` `WEST` `UP` `DOWN`; door states `OPEN` `CLOSED` `LOCKED` `SECRET` |

## 2.4 Text

Authored text is **untrusted prompt input** and **token-capped**: keep `desire`, `stakes`, `truth`, `persona.summary` and `description` to one or two sentences. The long version belongs in the prose of the note, not the block.

## 2.5 Flags

A **flag** is a named record that something happened. Conditions test it; only a `set_flag` Effect sets it. **Declare every flag before you use it**, in the `flags` block of the world's flag register. The linter fails an undeclared flag (EN007).

| Family | Name pattern | Meaning |
|---|---|---|
| **Armed** | `<thread>_armed` | the thread is live in this Sandbox; set by a Campaign |
| **Stage** | `<thread>_s<N>_<name>` | history: the thread reached stage N (one-way) |
| **Intent** | `<thread>_<thing>_due` | a deadline passed; the thing *may* now happen |
| **Outcome / terminal** | `<thread>_<thing>` | which way a fork went |
| **Counter** | `<thread>_<thing>` | counted with `flag_count_gte` |
| **Trait** | a plain name, with `toward` | a property of one entity (`gate_born`) |

Three rules the tools enforce:
1. **Every flag that is set is read, and every flag that is read is set** (or is declared as a thread output or input in its thread's `interface`).
2. **Judgement tags** (UPPERCASE) are set by the engine only. `set_flag` cannot name one.
3. **Never invent a flag inside a block.** Declare it first.

---

# Part 3. Design a thread on paper

Do this before you write a block. A thread that cannot be drawn in a table cannot be written.

## 3.1 The one-page design

Answer these in order. Each answer becomes a block.

1. **Premise, in one sentence, and what happens if nobody intervenes** (the *idle outcome*).
2. **Class:** Resolvable, Managed or Ratchet (`docs/thread-pattern.md` section 6). The class decides the shape of your graph.
3. **Actors, and who replaces each if the player removes them** (the *successors*).
4. **The state graph:** each state, what enters it, what changes, and its exits.
5. **Timers:** how many days between states, if left alone (these become Want deadlines).
6. **Couplings:** the flags this thread **reads** from other threads and the flags it **sets** for them (its *interface*).
7. **Quest contracts:** for each way the player can resolve it, the effects a Quest must apply and the Wants it must retire.
8. **Scenarios:** the idle run, one per terminal, one per death, and one unscripted act.

## 3.2 Worked example: the Ferryman's Debt

1. **Premise.** Tomas Reed, a Dustport ferryman, is three months behind on his water-chits. The creditors' clerk, Odo Marsh, has 25 days to collect or take the man. **Idle outcome:** Reed is seized, carried to the pans at Saltmarch, and his contract is sold on.
2. **Class: Resolvable.** It ends in a terminal that sticks. The idle terminal is *sold on*; the others are *debt paid* and *fled*.
3. **Successors.** If Marsh dies, the enforcer Idra Vance arrives and finishes every open errand at once. If Reed dies, the thread ends (his Wants fail).
4. **The graph.**

| State | Entered when | What changes | Exits |
|---|---|---|---|
| **S0 Armed** | a Campaign sets `ferry_armed` | Marsh's collect-Want starts (25 days) | Seized, Paid, Fled |
| **S1 Seized** | `evt_ferry_seized` | the creditors control Reed | In the pans, Paid |
| **S2 In the pans** | `evt_ferry_transit` | Reed moves to Saltmarch | Sold on, Paid |
| **Sold on** (idle terminal) | `evt_ferry_sold_on` | `ferry_sold_on`; the thread closes | |
| **Paid** | a Quest sets `ferry_debt_paid` | `evt_ferry_settled` retires the Wants | |
| **Fled** | a Quest, or `evt_ferry_missing` | `evt_ferry_gone` retires the Wants | |

5. **Timers (idle):** collect 25 days, move 30, sell 40.
6. **Interface:** arms `ferry_armed`; sets `ferry_sold_on`, `ferry_debt_paid`, `ferry_fled`. It reads nothing.
7. **Contracts:**

| Outcome | Quest's `on_complete` must | Retire |
|---|---|---|
| Stand surety (before the seizure) | set `ferry_debt_paid`; add `Guild GUARDS Reed` | resolve `want_reed_clear_his_debt` |
| Smuggle him out (before the seizure) | set `ferry_fled` | resolve `want_reed_clear_his_debt` |
| Buy him back (after the seizure) | set `ferry_debt_paid`; remove `Creditors CONTROLS Reed` | fail the move and sale Wants |

8. **Scenarios:** F1 idle, F2 surety, F3 smuggle, F4 buy back, F5 kill the clerk, F6 Reed walks out with no quest.

## 3.3 The four patterns you will use every time

| Pattern | Why | Written as |
|---|---|---|
| **Wants propose, events dispose** | a Want that fires late must not change a world that has moved on | a Want's `on_deadline` sets an **intent** flag only; a guarded World Event applies it |
| **Own-stage guard** | a Campaign that starts the thread past a stage must not re-fire it | every event and every Want that sets a flag tests `not flag_set <that flag>` |
| **Successor** | the player will kill the person the thread depends on | an event on `not npc_alive` brings the next, or sets every open intent at once |
| **Inference** | the player will do things no Quest covers | an event turns state (a location, a death) into the thread's flags and edges |

For Managed threads you also need **unrolled cycles** (an event fires once, so a repeating beat is written as numbered copies with a floor), and for Ratchets a **LOCKED** floor. See section 8.2 and `docs/thread-pattern.md` section 7.3.

---

# Part 4. Write the World layer

For every block: **what it is**, **where it lives**, **the fields**, **an example from the Ferryman's Debt**, and **the rules that catch people**.

## 4.1 Flags

**Where:** the `flags` block at the bottom of the world's flag register. One entry per flag.

```yaml
- id: ferry_armed
  description: "The Ferryman's Debt thread is live in this Sandbox."
- id: ferry_collect_due
  description: "Intent: the clerk's collection deadline passed."
```

Add all of a thread's flags at once, from your design table. `tools/transform.mjs` copies them into `manifest.yaml`.

## 4.2 NPC

**Where:** the NPC's note (`world/npcs/<name>.md`), frontmatter `groups` for factions and `home` for a place.

**Two ways to build one.** A **class build** (most NPCs) needs `race`, `levels` and `abilities`. A **monster build** uses `monster: srd_...` plus `advancement` or `templates`, and none of the class fields. You cannot mix them. **Never write** `hp`, `ac`, `bab` or `cr`: the engine computes them.

```yaml
kind: NPC
id: npc_tomas_reed
name: Tomas Reed
alignment: NEUTRAL_GOOD
race: HUMAN
levels: { EXPERT: 3 }
abilities: { str: 12, dex: 13, con: 12, int: 11, wis: 12, cha: 10 }
skill_ranks: { PROFESSION: 6, SWIM: 4 }
persona:
  summary: "A Dustport ferryman who poles stores out to the stranded ships. He is three months behind on his water-chits."
  voice_style: "Slow, dry, apologises before he asks."
base_disposition: 10
home: loc_dustport
```

| Field | Required | Notes |
|---|---|---|
| `kind`, `id`, `name`, `alignment`, `persona.summary` | yes | `persona.voice_style` is optional |
| `race`, `levels`, `abilities` | for a class build | SRD keys in UPPERCASE; all six abilities |
| `skill_ranks`, `feats`, `equipment` | no | feat and skill keys are SRD keys; `equipment` holds `item_` ids |
| `base_disposition` | no (default 0) | -100 to 100 towards the player |
| `home` | no | a `loc_` id |
| `simulation_tier` | no | `MAJOR` or `MINOR`; a Want of priority 1 makes the NPC Major anyway |

**Rules.** Non-combatants are class-built with `EXPERT` levels (CP-1); there is no civilian base. Class and SRD ids do not all exist in the engine's library yet (PR-4), so a build may validate and still not resolve until the library catches up. Give each **killable** thread actor a **successor** (see 4.7).

## 4.3 Faction

**Where:** the faction's note. A faction is a name and a summary; its power comes from relationships and from NPCs whose `groups` name it.

```yaml
kind: FACTION
id: faction_ferry_creditors
name: The Creditors' Clerks
summary: "The consortium's collection office. It binds defaulters and sells their contracts on."
```

## 4.4 Relationship

**Where:** the note of its `from` entity. `kind_of` is the relationship kind (the `kind` key is the entity discriminator). The `id` is optional; the transformer derives one.

```yaml
kind: RELATIONSHIP
from: npc_tomas_reed
to: faction_dust_ferrymen
kind_of: MEMBER_OF
sentiment: 50
visibility: PUBLIC
note: "A guild ferryman for nineteen years."
```

```yaml
kind: RELATIONSHIP
from: npc_odo_marsh
to: faction_ferry_creditors
kind_of: SECRETLY_SERVES
sentiment: 60
visibility: SECRET
note: "He presents himself as a private notary."
```

| Field | Notes |
|---|---|
| `from`, `to` | an entity id, or `PLAYER`; an edge cannot connect an entity to itself |
| `kind_of` | one of the 20 closed kinds (2.3) |
| `sentiment` | -100 to 100, required |
| `visibility` | `PUBLIC`, `SECRET`, or `{ known_by: [npc_x] }` |
| `permanent_secret` | `true` if no reveal path will ever exist; cannot be `PUBLIC` |

**Rules.**
- A **`SECRET`** edge needs a **reveal path**: an Effect `reveal_edge` that names it, or `permanent_secret: true`. In the example, the buy-back Quest reveals Marsh's secret service.
- **Edges are current state.** A thread that must ask "who holds Reed now?" tests the edge (`edge_exists`), not a flag. Effects can add and remove edges at runtime.

## 4.5 Fact

**Where:** the note about the topic or thread. A Fact is knowledge: true or a rumour, who knows it, and who believes a distorted version.

```yaml
kind: FACT
id: fact_ferry_debt_was_padded
text: "Reed's debt is padded: the creditors billed him for water that the Moot's own sluice-log shows was never drawn."
truth: TRUE
known_by: [npc_odo_marsh]
subjects: [npc_tomas_reed]
authority: GUIDED
```

```yaml
kind: FACT
id: fact_ferry_creditors_sell_debtors
text: "The creditors do not wait for debts to be paid. They sell defaulters' contracts to the Quiet Trade."
truth: TRUE
_known_by_groups:
  - { group: faction_ferry_creditors, tier: inner }
believed_by: [npc_tomas_reed]
believed_as: "A seized debtor works off his chits in the pans and is let go."
subjects: [faction_ferry_creditors]
authority: LOCKED
```

| Field | Notes |
|---|---|
| `text` | what is true (or, for a rumour, what is claimed) |
| `truth` | `TRUE` or `RUMOR`. **Quote it** or write it exactly as shown: a bare `TRUE` is a YAML boolean (the transformer normalises it) |
| `known_by` | NPC ids who know it. `[]` means "discoverable lore nobody knows yet", and then it **needs a reveal path** |
| `believed_by`, `believed_as` | a distorted version; `believed_as` is required if `believed_by` is non-empty, and an NPC cannot both know and believe a Fact |
| `subjects` | ids the Fact is about |
| `authority` | `LOCKED`, `GUIDED` (the default) or `OPEN`: how freely the LLM may handle the Fact's wording. See below |

**Authority.** Every authored Want, World Event, Fact, Encounter and text block carries an `authority` field (Design 23 §6). It says **who has the last word**: the engine and your text, or the LLM. The engine always validates every state change; authority governs the *text and the outcome*, never the rules.

| Value | Meaning | Use for a Fact |
|---|---|---|
| `LOCKED` | The outcome is engine-enforced and cannot change. Authored text is delivered **verbatim**; the LLM may not rewrite it. | Canon the world must never contradict: a ledger truth, the truth of the past. The example's `fact_ferry_creditors_sell_debtors` is `LOCKED`, so the narrator reveals exactly that sentence and nothing can overturn it |
| `GUIDED` (**default**) | The LLM may change **how**, not **whether**. The outcome is fixed; the text is a **seed** the narrator adapts to the scene. | Most Facts. What is true is fixed; the narrator chooses the wording. The example's `fact_ferry_debt_was_padded` is `GUIDED` |
| `OPEN` | The LLM may invent freely within the NPC's persona and the Want's `forbidden` list. | Loose colour and local knowledge you are happy for the narrator to extend. Use sparingly: the narrator may add detail you did not write |

Two notes:
- Design 23 §6 defines authority generally. How it applies to a Fact in particular (verbatim versus adapted wording) is **my reading of that definition**: the spec's own Fact example just writes `authority: GUIDED`.
- `LOCKED` carries an extra rule on a **Want** or **World Event**: it needs a deterministic fallback. A Fact has no outcome to enforce, so it needs none. Where each level is used in the plot web: `docs/thread-pattern.md` section 8.4.

**Group knowledge.** Write who knows a Fact **by group and tier**, and let the transformer resolve it to NPC ids:

```yaml
_known_by_groups:
  - { group: faction_ferry_creditors, tier: inner }
```

Tiers nest: `common` is known by all named members, `select` by select and `inner`, `inner` by inner only. An NPC declares its rank in frontmatter (`groups: [{ id: faction_ferry_creditors, rank: select }]`). A group with no named NPC at the tier resolves to nobody and the transformer warns. Fields beginning with `_` are codex directives and never reach the engine.

**Rules.** The player learns a Fact only through a `reveal_fact` Effect. Every Fact nobody knows needs one (the example reveals both in the buy-back Quest).

**An NPC telling the player is not recorded yet.** How a Fact told *in conversation* becomes a disclosure is an open platform item (Design 23 §14 items 10 and 11; PR-16). Until it lands, give every Fact the play depends on a **deterministic reveal path** (an event, a check or a Quest's `on_complete`), and do not make a `DIALOGUE` milestone's `when: fact_revealed` depend on an NPC speaking. Where the world's lore beyond Facts reaches NPCs and the narrator is a related open item (PR-14, PR-15).

## 4.6 Want

**Where:** its NPC's note. A Want is an NPC's motive; it is also the **engine of motion** in a thread, because its deadline fires whether or not the player does anything.

```yaml
kind: WANT
id: want_marsh_collect_reed
_thread: ferry
npc_id: npc_odo_marsh
priority: 1
desire: "Collect Tomas Reed's overdue water-debt, or take the man."
stakes: "A debtor who walks free teaches the others they can."
urgent_when:
  all:
    - { flag_set: { flag: ferry_armed } }
    - { not: { flag_set: { flag: ferry_collect_due } } }
deadline_days: 25
on_deadline:
  - { set_flag: { flag: ferry_collect_due } }
methods: [PERSUADE, HIRE, THREATEN]
forbidden: []
```

| Field | Notes |
|---|---|
| `npc_id`, `priority` | priority 1 is the NPC's main Want |
| `desire`, `stakes` | one sentence each |
| `urgent_when` | a Condition. **It only activates** the Want (the clock starts the first day it is true). Omit it to be active from day 0 |
| `deadline_days`, `on_deadline` | the relative timer, and the fallback Effects. **They go together**. A non-`OPEN` Want must have both |
| `methods`, `forbidden` | the closed Want methods; they must not overlap |
| `resolution_paths` | Quest ids, or `{ effects: [...] }` |
| `authority` | `GUIDED` by default |

**The pattern.** The `on_deadline` of a thread Want sets an **intent flag** and nothing else. The `urgent_when` ends with `not flag_set <that intent flag>`, which is the Want's own-stage guard. The next Want in a chain starts when the previous one's intent is applied:

```yaml
kind: WANT
id: want_marsh_deliver_reed
_thread: ferry
npc_id: npc_odo_marsh
priority: 2
desire: "Deliver the seized debtor to the pans at Saltmarch."
stakes: "A seized man is a loose end until his contract is sold."
urgent_when:
  all:
    - { flag_set: { flag: ferry_s1_seized } }
    - { not: { flag_set: { flag: ferry_transit_due } } }
deadline_days: 30
on_deadline:
  - { set_flag: { flag: ferry_transit_due } }
methods: [PERSUADE, HIRE]
forbidden: [VIOLENCE]
```

**An `OPEN` Want** has no deterministic fallback and may omit the deadline. Use it for a Want the player may resolve however they like, as long as a *different* Want holds the fallback (here Marsh's collect-Want is the fallback for Reed's):

```yaml
kind: WANT
id: want_reed_clear_his_debt
_thread: ferry
npc_id: npc_tomas_reed
priority: 1
desire: "Clear his water-debt before the clerk comes for him."
stakes: "He has no plan. The clerk has a deadline."
urgent_when: { flag_set: { flag: ferry_armed } }
methods: [PERSUADE, HIRE, STEAL, FLEE]
forbidden: []
resolution_paths: [quest_ferry_pay_the_debt, quest_ferry_smuggle_him_out, quest_ferry_buy_him_back]
authority: OPEN
```

**Rules.**
- **Retire what you defeat.** `resolve_want` and `fail_want` both stop `on_deadline`. A Quest that defeats a Want says so; the world moving past it does not retire it.
- **A dead NPC's own Wants fail**, but nobody else's do (a platform assumption, PR-12). If your thread depends on a Want held by someone killable, give it a successor.
- A deadline fires at most once.
- **A Want is resolved by an Effect, never by state.** `resolve_want` and `fail_want` run only when something applies them. If the player achieves the Want's `desire` by a route you did not write a Quest for (the debt cleared, the creditor dead, the debtor gone), the Want stays active and its `on_deadline` still fires. Write the **state test as a guarded World Event**: when the goal holds, it sets the outcome flag and retires the Want. `evt_ferry_missing` (turns "Reed left town" into `ferry_fled`) and `evt_ferry_settled` (turns `ferry_debt_paid`, however it was set, into `resolve_want`) in 4.7 are the pattern. List every way a player could meet the Want's `desire`, and cover each one (CP-11; a `resolved_when` field on the Want is PF-7).

## 4.7 World Event

**Where:** the thread note. A World Event is a `when`/`then` pair: when its Condition is true (evaluated by the engine, never by the LLM), its Effects apply **exactly once** per Sandbox.

```yaml
kind: WORLD_EVENT
id: evt_ferry_seized
scope: REGIONAL
origin: loc_dustport
when:
  all:
    - { flag_set: { flag: ferry_armed } }
    - { flag_set: { flag: ferry_collect_due } }
    - { not: { flag_set: { flag: ferry_s1_seized } } }
    - { npc_alive: npc_tomas_reed }
    - { in_location: { entity: npc_tomas_reed, location: loc_dustport } }
    - { not: { edge_exists: { from: faction_dust_ferrymen, kind: GUARDS, to: npc_tomas_reed } } }
    - { not: { flag_set: { flag: ferry_debt_paid } } }
then:
  - { set_flag: { flag: ferry_s1_seized } }
  - { add_edge: { from: faction_ferry_creditors, kind: CONTROLS, to: npc_tomas_reed, sentiment: -50, visibility: SECRET } }
truth: "No one stood surety in time. The clerk seizes Tomas Reed on the quay, with his papers in order."
rumor_seeds: ["They say the clerk has taken a ferryman for his chits."]
propagation: { propagates: true, speed_days_per_node: 2, decay: 0.8 }
known_by: [npc_odo_marsh]
```

| Field | Notes |
|---|---|
| `scope` | `LOCAL`, `REGIONAL` or `MACRO`. A LOCAL event does not propagate |
| `origin` | a `loc_` id, where it happens |
| `when` | a Condition (Appendix B) |
| `then` | an Effect list (Appendix C), at most 64 |
| `truth` | what really happened, one sentence (the rumour system distorts it) |
| `rumor_seeds`, `propagation` | author-written distortions, and how fast news travels: `{ propagates: true, speed_days_per_node: 2, decay: 0.8 }`. Rumours need `propagates: true` |
| `known_by` | NPCs who already know it when it happens |
| `authority` | `LOCKED` (engine-enforced, text verbatim), `GUIDED` (default), `OPEN` |

### The guard checklist

Read `evt_ferry_seized` above and tick every line. Every thread event has all of them.

1. **Armed:** `flag_set ferry_armed`.
2. **The intent it applies:** `flag_set ferry_collect_due`.
3. **Its own-stage guard:** `not flag_set ferry_s1_seized`, the flag it sets.
4. **The world still allows it:** `npc_alive`, `in_location`, and `not edge_exists` for any protection (the guild's surety).
5. **Its own result flag** is in `then`. `thread-check` fails an event that sets a flag it does not guard.

### Successors, sweeps and inference

When the thread's hands are removed, bring the next:

```yaml
kind: WORLD_EVENT
id: evt_ferry_collector_replaced
scope: REGIONAL
origin: loc_dustport
when:
  all:
    - { flag_set: { flag: ferry_armed } }
    - { not: { npc_alive: npc_odo_marsh } }
    - { not: { flag_set: { flag: ferry_collector_lost } } }
    - { not: { flag_set: { flag: ferry_sold_on } } }
    - { not: { flag_set: { flag: ferry_settled } } }
    - { not: { flag_set: { flag: ferry_gone } } }
then:
  - { set_flag: { flag: ferry_collector_lost } }
  - { set_flag: { flag: ferry_collect_due } }
  - { set_flag: { flag: ferry_transit_due } }
  - { set_flag: { flag: ferry_sale_due } }
  - { move_npc: { npc: npc_idra_vance, to: loc_dustport } }
truth: "The clerk is dead. The creditors send an enforcer, who closes every open errand at once."
known_by: [npc_idra_vance]
```

Killing Marsh brings Vance, and **every open intent is set at once**. Each intent still passes through its guarded event, so only the ones that still hold take effect. The result: killing the clerk *rushes* the sale (scenario F5). Design this on purpose.

When the player does something no Quest covers, turn the evidence into the thread's flags:

```yaml
kind: WORLD_EVENT
id: evt_ferry_missing
scope: REGIONAL
origin: loc_dustport
when:
  all:
    - { flag_set: { flag: ferry_armed } }
    - { flag_set: { flag: ferry_collect_due } }
    - { not: { flag_set: { flag: ferry_s1_seized } } }
    - { not: { flag_set: { flag: ferry_fled } } }
    - { npc_alive: npc_tomas_reed }
    - { not: { in_location: { entity: npc_tomas_reed, location: loc_dustport } } }
    - { not: { flag_set: { flag: ferry_debt_paid } } }
then:
  - { set_flag: { flag: ferry_fled } }
truth: "Tomas Reed is gone from Dustport before the clerk's deadline. Nobody says where."
known_by: [npc_odo_marsh]
```

If Reed leaves Dustport before the deadline, the seizure event is blocked by `in_location`, and this event records that he fled. Without it the thread would stall (try removing it and run scenario F6).

### Terminals close the thread

A **terminal** is an ending of the thread that **sticks**: once it has happened, the thread has nothing more to do. It is a design idea, not an engine concept. The engine has no "terminal" field; you mark one in the thread's `interface` (4.10), and the tools check it.

**How to identify a terminal event.** Walk the state graph. A terminal outcome is a state with **no exits**. The event that follows it is the terminal event. In the Ferryman's Debt there are three:

| Terminal outcome | Outcome flag | Terminal event | Who sets the outcome |
|---|---|---|---|
| Debt paid | `ferry_debt_paid` | `evt_ferry_settled` | a Quest |
| Fled | `ferry_fled` | `evt_ferry_gone` | a Quest, or `evt_ferry_missing` |
| Sold on (the idle terminal) | `ferry_sold_on` | `evt_ferry_sold_on` | the event itself |

A terminal event has three marks: it sets a **result flag** that guards it (like every event); **no other source in the thread reads that flag positively** (a negated guard, `not flag_set ferry_settled`, is fine, as the successor event uses it); and the thread's `interface.terminals` lists it.

**What it must do: leave no Want of the thread running.** This is not the same as "fail every Want the thread has". A terminal retires **whatever could still fire, or still ask the story agent to improvise**, and nothing else:

- `evt_ferry_settled` and `evt_ferry_gone` retire the three Wants of the clerk, which are the ones that could still go off, and the debtor's own Want (`resolve_want` when the debt is paid, `fail_want` when he fled).
- `evt_ferry_sold_on` retires only the debtor's Want. The clerk's three Wants have already expired, so there is nothing else to retire.
- A Want that has already been **resolved** or **failed** (by a Quest, say) needs no second call, and a second call does nothing.

The reason is practical. A Want's deadline fires at most once, but an unretired Want may still fire *after* the thread has ended, and an `OPEN` Want with no deadline stays active for ever and gives the story agent a motive for someone whose story is over. In the pilot's first draft, the buy-back Quest and `evt_ferry_gone` both left the debtor wanting to clear a debt that no longer existed.

```yaml
kind: WORLD_EVENT
id: evt_ferry_settled
scope: REGIONAL
origin: loc_dustport
when:
  all:
    - { flag_set: { flag: ferry_armed } }
    - { flag_set: { flag: ferry_debt_paid } }
    - { not: { flag_set: { flag: ferry_settled } } }
then:
  - { set_flag: { flag: ferry_settled } }
  - { resolve_want: want_reed_clear_his_debt }
  - { fail_want: want_marsh_collect_reed }
  - { fail_want: want_marsh_deliver_reed }
  - { fail_want: want_marsh_sell_the_contract }
truth: "The debt is paid. The clerk closes the file, and does not forget the name."
known_by: [npc_odo_marsh]
```

**How it is checked.**
1. **`thread-check`** fails a terminal that is not terminal: it must be a World Event that sets a result flag, and no other source may read that flag positively.
2. **The simulator** applies an invariant in **every** scenario: if a terminal event fired, none of that thread's Wants may still be `active` at the end of the run. A scenario can also assert the exact status (`wants: { want_reed_clear_his_debt: failed }`).
3. **Your own scenarios** (6.4) should include one per terminal.

A Managed or Ratchet thread usually has no terminal, only a floor (a final state the pressure settles at), and does not list `terminals`. A Resolvable thread has one for every ending.

## 4.8 Conditions: a short cookbook

Full list in Appendix B. A Condition is **one** object: a predicate, or `all`, `any` or `not` around more Conditions. Never put two keys in one object.

```yaml
when:
  all:
    - { flag_set: { flag: ferry_armed } }                         # a flag
    - { not: { flag_set: { flag: ferry_s1_seized } } }            # its negation
    - { npc_alive: npc_tomas_reed }                               # liveness
    - { in_location: { entity: npc_tomas_reed, location: loc_dustport } }
    - { edge_exists: { from: faction_dust_ferrymen, kind: GUARDS, to: npc_tomas_reed } }
    - any:
        - { flag_count_gte: { flag: ferry_pages, count: 3 } }     # a counter
        - { fact_revealed: fact_ferry_debt_was_padded }
```

- **Test the edge for "now", the flag for "ever".**
- `flag_set` with `toward: npc_x` tests a flag scoped to an entity.
- `day_reached` is **absolute**: use it only in a Campaign's genesis event. For "N days after X", use a Want timer.
- Conditions never read prose and never call the LLM.

## 4.9 Effects: a short cookbook

Full list in Appendix C. An Effect list is **ordered**, non-empty, and each Effect fires with its source exactly once.

```yaml
then:
  - { set_flag: { flag: ferry_s1_seized } }
  - { add_edge: { from: faction_ferry_creditors, kind: CONTROLS, to: npc_tomas_reed, sentiment: -50, visibility: SECRET } }
  - { move_npc: { npc: npc_tomas_reed, to: loc_saltmarch } }
  - { fail_want: want_marsh_collect_reed }
  - { reveal_fact: fact_ferry_debt_was_padded }
```

- **Within one cascade round, Effects do not see each other.** A flag you set is visible to the next round, not to the same list.
- `grant_reward` is allowed **only** in a Quest's `on_complete` and in Migrations. Amounts are never hand-entered: use the SRD tables.
- `set_flag` names only a **declared effect-only flag**.

## 4.10 The thread note

The thread card is the **document that explains the graph**; the blocks are the engine's copy. Use the `thread` template (`meta/templates/thread.md`) and copy the demo world's note (`world/plot-web/the-ferrymans-debt.md`). Its frontmatter carries two codex-only fields:

```yaml
thread: ferry
interface: { class: resolvable, arms: [ferry_armed], reads: [], sets: [ferry_sold_on, ferry_debt_paid, ferry_fled], terminals: [evt_ferry_settled, evt_ferry_gone, evt_ferry_sold_on], inputs_from: [], outputs_to: [thread_quiet_trade_in_motion] }
```

- `thread` labels every block in the note (and, through `_thread: ferry`, the blocks that live in other notes: Wants, Quests, a genesis event). The label is not sent to the engine yet (PF-6).
- `interface` is what `thread-check` compares to your blocks: every flag in `arms` and `reads` must be tested somewhere, and every flag in `sets` must be set somewhere. `terminals` lists the thread's terminal events (4.7); `thread-check` and the simulator check them.
- The card holds, in this order: premise, actors and successors, the state graph, the interface, quest contracts, the idle run, hooks.

---

# Part 5. Write the Campaign layer

A Campaign does four things to a thread: it **arms** it, it **starts it at a stage**, it **unlocks Modules** from its state, and it **tunes** it. It never edits a thread's events.

## 5.1 The Campaign block

**Where:** the Campaign note, `campaigns/<slug>/`. The folder name is the slug, and each Campaign has exactly one `CAMPAIGN` entity. (The `_seeds` and `_shared` folders hold seeds and shared design notes, not Campaigns.)

```yaml
kind: CAMPAIGN
id: camp_ferry_demo
world_id: world_hollowfall
title: "The Ferryman's Debt"
summary: "A teaching Campaign: a ferryman owes the creditors, and the party decides how the debt ends."
start_level: 1
start_day: 0
start_location: loc_dustport
opening_module: mod_ferry_dockside
content_descriptors: [MATURE_THEMES]
modules: [mod_ferry_dockside, mod_ferry_pans]
unlocks:
  mod_ferry_pans: { flag_set: { flag: ferry_s1_seized } }
```

| Field | Notes |
|---|---|
| `world_id` | the one place `world_id` is authored: `world_hollowfall` |
| `start_level`, `start_day`, `start_location` | the clock starts at `start_day` (default 0); `start_location` is a `loc_` id |
| `opening_module` | must be in `modules` |
| `content_descriptors` | required, at least one; informational only |
| `modules` | the Module ids, no repeats |
| `unlocks` | `module_id: Condition`. A Module with no entry is always available. Use it to unlock a Module **from thread state** |
| `flags` | Campaign-local effect-only flags (`{ id, description }`); the linter does not read them yet, so prefer World flags |
| `allowed_options`, `est_length_hours` | optional |

## 5.2 The overlay

**Where:** `overlay-<slug>.md`, `kind: OVERLAY` in frontmatter, id `overlay_...`, block `CAMPAIGN_OVERLAY`. It holds `adds`, `overrides` and `suppresses`, and must hold at least one. See `docs/thread-pattern.md` section 2.1 for why it is separate.

```yaml
kind: CAMPAIGN_OVERLAY
id: overlay_ferry_demo
campaign_id: camp_ferry_demo
adds:
  - kind: WORLD_EVENT
    id: evt_ferry_demo_genesis
    _thread: ferry
    scope: MACRO
    origin: loc_dustport
    when:
      all:
        - { day_reached: 0 }
        - { not: { flag_set: { flag: ferry_armed } } }
    then:
      - { set_flag: { flag: ferry_armed } }
    truth: "The Ferryman's Debt thread is live at Dustport."
overrides:
  want_marsh_collect_reed:
    deadline_days: 15
```

- **The genesis event arms the thread.** It fires once at day 0 and is guarded by `not flag_set ferry_armed`. A Campaign that never adds it never arms the thread. This is how a Campaign in another region or era leaves a thread dormant.
- **`adds`** may contain NPCs, Wants, Facts, Relationships, World Events, Factions, Items, Monsters and overland graphs. Their ids must not collide with World ids. Each add is a **full entity**.
- **`overrides`** patch one World entity by id, by field path (`deadline_days`, `persona.voice_style`). The example shortens Marsh's Want from 25 days to 15, so the **same thread runs faster in this Campaign** (scenario F1 asserts the new timing). You may override authored fields only, never `id`, `kind` or structural fields.
- **`suppresses`** lists World entities that do not exist in this Campaign:

```yaml
suppresses: [npc_idra_vance]
```

- **Authority.** To make a key beat unavoidable in one Campaign, override its `authority` to `LOCKED`. Keep that for the Campaign's own endgame, not for thread internals.
- **Hydrated entities are frozen.** Once a Sandbox has met an entity, a later Campaign version cannot silently change it (Design 23.4). Do not rely on an override changing a Sandbox mid-play; use Effects.

## 5.3 The Module

**Where:** a note per Module, `kind: MODULE`, block `MODULE`. A Module is the local frame of an adventure; its Quests, rooms and encounters are blocks in the same note.

```yaml
kind: MODULE
id: mod_ferry_dockside
title: "Dockside"
target_level_min: 1
target_level_max: 3
key_locations: [loc_dustport, loc_vigil]
key_npcs: [npc_tomas_reed, npc_odo_marsh]
```

Both `target_level_min` and `target_level_max` are required, and `min <= max`. `key_locations` and `key_npcs` are hints. Whether a Module is available is decided by the Campaign's `unlocks`.

## 5.4 The Quest

**Where:** its Module's note. A Quest is a **chain of milestones** that resolves a Want (a *Resolution Path*). It has one `on_complete` Effect list, and that list is where it **applies the thread's contract**.

```yaml
kind: QUEST
id: quest_ferry_pay_the_debt
_thread: ferry
title: "Stand Surety"
giver_npc_id: npc_tomas_reed
from_want: want_reed_clear_his_debt
level_recommendation: 1
milestones:
  - milestone_id: ms_ask
    type: DIALOGUE
    description: "Ask the ferrymen's guild to stand surety for Reed."
    when: { flag_set: { flag: ferry_armed } }
    next_milestone: ms_agree
  - milestone_id: ms_agree
    type: DIALOGUE
    description: "Settle the terms with the clerk."
    when: { edge_exists: { from: faction_dust_ferrymen, kind: GUARDS, to: npc_tomas_reed } }
    next_milestone: COMPLETED
on_complete:
  - { set_flag: { flag: ferry_debt_paid } }
  - { add_edge: { from: faction_dust_ferrymen, kind: GUARDS, to: npc_tomas_reed, sentiment: 60, visibility: PUBLIC } }
  - { resolve_want: want_reed_clear_his_debt }
  - { adjust_disposition: { npc: npc_tomas_reed, toward: PLAYER, delta: 25 } }
  - { grant_reward: { xp: { table: SRD_QUEST_XP, size: MODERATE } } }
```

| Field | Notes |
|---|---|
| `giver_npc_id`, `from_want` | who offers it, and which Want it resolves. List the Quest in that Want's `resolution_paths` |
| `level_recommendation` | 1 to 20 |
| `milestones` | at least one; a **single chain** (each names `next_milestone`, the last says `COMPLETED`). No branches |
| milestone `type` | `DIALOGUE`, `FETCH` or `DELIVER` |
| milestone `when` | a Condition that is true when the milestone is complete |
| `on_complete` | Effects; **the only place `grant_reward` is allowed** |

**Why milestones exist.** A Quest is one authored way to resolve a Want. The milestones are where its *sequencing* lives: they turn a resolution path into an ordered chain of checkable steps, so other content can gate on partial progress (`milestone_complete`) and the engine can apply the Quest's effects exactly once when the chain finishes. A milestone is the progress record, the completion test and the idempotency unit at once.

**How the engine uses a milestone.** The Sandbox tracks the Quest's active milestone. Only the active milestone's `when` is evaluated; when it becomes true the engine records the completion atomically — once per `(sandbox, quest, milestone)` — so a retried or racing completion cannot apply anything twice. It then moves to `next_milestone`, and when the chain reaches `COMPLETED` the Quest's `on_complete` list fires. There are **no per-milestone rewards**: `on_complete` is the only Effect list a Quest has. *(The local simulator models Quests whole — `start_quest` / `complete_quest` — and does not walk the chain; see Appendix B.)*

**`type` is a label, not a mechanic.** The engine never reads a milestone's `type`; the `when` Condition is what decides whether it is done. Treat the type as the taxonomy the journal and authoring tools read, and pair it with the matching `when` by convention:

| `type` | Means | The `when` it normally uses |
|---|---|---|
| `DIALOGUE` | resolve it by talking | `fact_revealed` (the player was told something), or `edge_exists` |
| `FETCH` | resolve it by getting an object | `has_item` |
| `DELIVER` | resolve it by taking an object somewhere | `all:` of `in_location` and `has_item` |

Nothing enforces the pairing — a `FETCH` whose `when` tests a location validates fine. Keep them consistent anyway, and remember the condition is the truth.

**At least one milestone.** `milestones` is required and must hold at least one entry; the schema rejects an empty or missing list. A milestone-less Quest could never complete — there would be nothing to evaluate and no path to `COMPLETED`, so `on_complete` would never fire and the Want it resolves would be unreachable by that Quest. A one-step Quest is a single milestone whose `next_milestone: COMPLETED`.

**Milestone conditions** are the usual predicates, and a condition may be compound:

```yaml
kind: QUEST
id: quest_ferry_the_ledger_page
_thread: ferry
title: "The Padded Ledger"
giver_npc_id: npc_tomas_reed
from_want: want_reed_clear_his_debt
level_recommendation: 2
milestones:
  - milestone_id: ms_search
    type: FETCH
    description: "Search the creditors' tally-house for the ledger page."
    when: { has_item: { item: item_ferry_ledger_page } }
    next_milestone: COMPLETED
on_complete:
  - { reveal_fact: fact_ferry_debt_was_padded }
  - { grant_reward: { xp: { table: SRD_QUEST_XP, size: MODERATE } } }
```

**Contracts, not freedom.** `on_complete` must do exactly what the thread card's contract table says: set the outcome flag, add or remove the custody edge, retire the Wants it defeats. The buy-back Quest (after the seizure) also removes the creditors' edge and fails the move and sale Wants:

```yaml
kind: QUEST
id: quest_ferry_buy_him_back
_thread: ferry
title: "Buy Him Back"
giver_npc_id: npc_odo_marsh
from_want: want_reed_clear_his_debt
level_recommendation: 2
milestones:
  - milestone_id: ms_find
    type: DIALOGUE
    description: "Find which buyer holds Reed's contract."
    when: { edge_exists: { from: faction_ferry_creditors, kind: CONTROLS, to: npc_tomas_reed } }
    next_milestone: ms_page
  - milestone_id: ms_page
    type: FETCH
    description: "Take the ledger page that proves the debt was padded."
    when:
      all:
        - { fact_revealed: fact_ferry_debt_was_padded }
    next_milestone: ms_deal
  - milestone_id: ms_deal
    type: DIALOGUE
    description: "Settle with the creditors."
    when:
      { not: { edge_exists: { from: faction_ferry_creditors, kind: CONTROLS, to: npc_tomas_reed } } }
    next_milestone: COMPLETED
on_complete:
  - { set_flag: { flag: ferry_debt_paid } }
  - { remove_edge: { from: faction_ferry_creditors, kind: CONTROLS, to: npc_tomas_reed } }
  - { resolve_want: want_reed_clear_his_debt }
  - { reveal_fact: fact_ferry_creditors_sell_debtors }
  - { reveal_edge: { from: npc_odo_marsh, kind: SECRETLY_SERVES, to: faction_ferry_creditors } }
  - { fail_want: want_marsh_deliver_reed }
  - { fail_want: want_marsh_sell_the_contract }
  - { grant_reward: { xp: { table: SRD_QUEST_XP, size: MAJOR } } }
```

**Alternative endings are alternative Quests.** A Quest has one ending, so "stand surety" and "smuggle him out" are two Quests, both in the Want's `resolution_paths` (until the platform adds Quest outcomes, PR-11).

**Availability.** A Quest cannot say it has stopped being possible (PR-13). Until it can, write the condition under which each Quest is available in a gates file beside your scenarios, and let the simulator refuse a Quest the world has moved past. The example keeps it in `scenarios/quest-gates.yaml`: for instance, you cannot stand surety once Reed is seized.

## 5.5 Sites: rooms, encounters, items, monsters

Put these in the Module note.

**Room.** One note block per room. The tactical grid is optional: omit `layout` and the engine derives an open rectangle from `size`. Each character in the grid is one 5 ft tile; the grid must match `size` exactly; a `door` legend entry must sit on the matching edge.

```yaml
kind: ROOM
id: room_ferry_tally_house
module_id: mod_ferry_pans
title: "The Tally-house"
lighting: SHADOWY
description:
  authority: GUIDED
  initial: "A low reed-roofed counting-house at the pans. Tally-sticks hang in bundles from the rafters, and a clerk's stool stands by a locked cabinet."
  detailed: "Salt has crusted every sill. The cabinet's hinges are new."
exits:
  - { direction: SOUTH, target_room_id: room_ferry_cellar, door_state: LOCKED, lock_dc: 15 }
size: { width_ft: 30, height_ft: 20 }
layout:
  legend: { "#": wall, ".": floor, "S": { door: SOUTH }, "c": { object: obj_ferry_cabinet } }
  grid:
    - "######"
    - "#.c..#"
    - "#....#"
    - "###S##"
objects:
  - object_id: obj_ferry_cabinet
    name: "The clerk's cabinet"
    interactable: true
    actions:
      - trigger: OPEN
        check_required: { skill: OPEN_LOCK, dc: 15 }
        success_text: "Among the tally-sticks lies a ledger page in a neat hand."
        spawn_items: [item_ferry_ledger_page]
```

- An exit's `door_state: LOCKED` needs `lock_dc` or `key_item_id`; an unlocked exit must not have either.
- An object's action may carry a skill check (`check_required`), `success_text`, `spawn_items` and an Effect list `then`.

```yaml
kind: ROOM
id: room_ferry_cellar
module_id: mod_ferry_pans
title: "The Cellar"
lighting: DARK
description:
  authority: GUIDED
  initial: "A brine cellar under the counting-house, where the creditors keep the contracts they have not yet sold."
exits:
  - { direction: NORTH, target_room_id: room_ferry_tally_house, door_state: OPEN }
size: { width_ft: 20, height_ft: 20 }
```

**Encounter.** *What is here and how it behaves.* The engine computes every number; counts are scaled to the party, and treasure comes from the SRD table, never from an amount you write.

```yaml
kind: ENCOUNTER
id: enc_ferry_clerks
module_id: mod_ferry_pans
trigger: { in_location: { entity: PLAYER, location: room_ferry_cellar } }
monsters:
  - { monster: srd_warrior_guard, count: 2 }
tactics: DEFEND_POSITION
treasure: { table: SRD_BY_LEVEL }
authority: GUIDED
```

**Item.** An SRD item plus a name and a description. You cannot add mechanical properties.

```yaml
kind: ITEM
id: item_ferry_ledger_page
base: srd_parchment
name: "A padded ledger page"
description: "A page of the creditors' ledger, in a clerk's hand, showing water billed to Tomas Reed that was never drawn."
```

**Monster** (not used in the example): an SRD base, an optional name, `advancement: { extra_hit_dice: n }` and `templates: [KEY]`. Same rule: no hand-built stat blocks.

> **Caution:** SRD ids (`srd_warrior_guard`, `srd_parchment`) are placeholders until the platform's SRD library and the package agree on one id form (PR-4). The schema checks the shape, not whether the id exists. Record the SRD base in the note's body (conventions §9.6) and mark an unknown one `[OPEN] (PR-4)`.

## 5.6 Unlocking Modules from thread state

The Campaign's `unlocks` is a Condition. In the example the second Module appears when Reed is seized:

```yaml
unlocks:
  mod_ferry_pans: { flag_set: { flag: ferry_s1_seized } }
```

This is the main link between the plot web and the Modules. Rules of thumb:
- Unlock a Module on a **stage flag or an edge**, never on a date.
- A Module whose first Quest is already moot is never offered; design Modules so that skipping one is safe, because the Want's deadline will fire.
- A Module that is no longer relevant cannot be retired yet (PR-13). Gate its Quests.

## 5.7 Choosing how a Campaign starts

| You want | Do this |
|---|---|
| The thread starts from the beginning | arm it with the genesis event (5.2) |
| The thread starts at stage N | arm it **and** set the stage flags and edges for stage N. The simulator generates the list: a scenario with `start: { fast_forward: <stage flag> }` prints it. Every event guards itself, so earlier stages cannot re-fire |
| A thread should not exist in this Campaign | do not arm it |
| The thread should run at another pace | override `deadline_days` on its Wants (5.2) |
| A long arc made of several Campaigns | **target:** a Campaign Succession (PR-10), where the next Campaign starts from the world state the last one left. **Until it lands:** one Campaign with Acts, i.e. Modules grouped and unlocked by outcome flags |

Fast-forward restarts any Want timer that was part-run; fast-forward to a boundary where the next clock has not started.

---

# Part 6. Test it

## 6.1 Run the pipeline

```
python3 tools/lint.py
node tools/transform.mjs
node tools/validate-world.mjs
node tools/thread-check.mjs
node tools/simulate-world.mjs --coverage
```

To try the Ferryman's Debt without touching the vault: `tools/verify-example.sh`. It copies the vault to a temporary directory, adds the example, and runs everything.

## 6.2 Reading the output

| Tool says | It means | Do |
|---|---|---|
| lint `EN007 flag 'x' is not declared` | the flag is not in the `flags` block | declare it (4.1) |
| lint `EN006 references id 'x' that no note defines` | a typo, or the note is missing | fix the id or write the note |
| validate `unrecognized field` | a field the schema does not allow (or a `_` directive that was not stripped) | remove it |
| validate `a Want with authority GUIDED must define a deterministic 'on_deadline'` | the Want has no fallback | add `deadline_days` and `on_deadline`, or make it `OPEN` |
| thread-check `Missing own-stage guard` | an event or Want can re-fire after a fast-forward | add `not flag_set <own result>` |
| thread-check `Terminal events that are not terminal` | a declared terminal is not an event, sets no flag, or something still reads its result flag | fix the graph, or take it out of `terminals` |
| thread-check `read but never set` | a flag is tested and nothing sets it | add the setter, or list it as an input in `interface` |
| thread-check `set but never read` | a flag has no consumer | read it, or list it as an output |
| simulate `FAIL ... should have fired` | the thread stalls or fires on another day | read the timeline and find the guard that is false |
| simulate `terminal evt_x of thread 'y' fired but want w is still active` | the terminal left a Want running | add `resolve_want` or `fail_want` for it to the terminal event (or the Quest) |
| simulate coverage `NEVER: evt_x` | an event no scenario reaches | write the scenario, or the event is unreachable |

## 6.3 Write scenarios

A scenario is a YAML file **you write by hand** — the script you would play if you were the player, plus the assertions you want to hold. Nothing generates it: `campaigns/dustport-pilot/scenarios/` and the example's `scenarios/` are all hand-written, and the generator scripts that wrote the pilot's *notes* never wrote a scenario. The simulator replays it — scripting the player and other threads, running the world day by day — and checks what you expect.

A scenario tests the **Conditions and Effects web**, not the game. It is a *model of the world layer, not the engine*: whether events fire on the days you designed, whether Want deadlines expire, whether flags and edges land where you meant, whether every terminal is reachable, and whether a thread closes cleanly when it ends. It does **not** cover rooms, encounters, combat, items or narration, and it skips the Conditions it cannot model — `has_item`, `disposition_*`, `faction_rep_gte`, `season_is`, `player_level_gte` and `milestone_complete` (Appendix B) — so a Quest is run whole rather than milestone by milestone. Where the specs are silent it follows a named assumption rather than the engine (A-1…A-6, pilot-thread-findings); a passing scenario therefore proves the design is coherent *before any engine exists*, not that the engine will behave the same.

```yaml
name: "F5 kill the clerk on day 20"
description: "The successor sweep."
campaign: camp_ferry_demo
quest_gates_file: quest-gates.yaml     # the availability sidecar (see below)
run_days: 120
inputs:                                 # other threads
  - { day: 5, set_flag: gate_fails_for_a_season }
actions:                                # the player
  - { day: 20, kill: npc_odo_marsh }
  - { day: 30, quest: quest_ferry_buy_him_back, moves: [{ npc: npc_tomas_reed, to: loc_saltmarch }] }
  - { day: 35, move: [{ npc: npc_tomas_reed, to: loc_vigil }] }
  - { day: 40, effects: [{ fail_want: want_marsh_deliver_reed }] }
  - { day: 50, player_at: loc_saltmarch }
expect:
  fired_between: { evt_ferry_transit: [20, 20] }   # an event fired on days 20 to 20
  events: [evt_ferry_sold_on]
  not_events: [evt_ferry_missing]
  flags: [ferry_sold_on]
  not_flags: [ferry_debt_paid]
  edges: ["faction_ferry_creditors CONTROLS npc_tomas_reed"]
  not_edges: []
  locations: { npc_tomas_reed: loc_saltmarch }
  wants: { want_marsh_collect_reed: expired }       # dormant | active | resolved | failed | expired
  modules: [mod_ferry_pans]
  rejected: [quest_ferry_pay_the_debt]              # refused because the world moved past it
```

**`quest_gates_file`: telling a Quest it is too late.** A Quest cannot say it has stopped being possible (PR-13; §5.4). Until it can, list each Quest's availability — the state in which the world has *not* moved past it — in a sidecar YAML file, and name that file here with `quest_gates_file`. It is a map of quest id to Condition, written in the ordinary vocabulary, and its path is resolved relative to the scenario file:

```yaml
quest_ferry_pay_the_debt:
  all:
    - { flag_set: { flag: ferry_armed } }
    - { not: { flag_set: { flag: ferry_s1_seized } } }
    - { not: { flag_set: { flag: ferry_debt_paid } } }
```

The simulator refuses a Quest whose gate is false — and likewise one whose Module is locked or that is already complete — and records it in `rejected`, which your `expect` block asserts. Omit `quest_gates_file` and it falls back to `campaigns/dustport-pilot/scenarios/pilot-quest-gates.yaml`. The gate file is a sidecar, not a scenario, so the runner skips it.

A scenario may also start with `start: { fast_forward: <stage flag> }`.

## 6.4 What to test, for every thread

| Scenario | Proves |
|---|---|
| **Idle** | the idle outcome happens, on the days you designed |
| **One per terminal / fork** | every ending is reachable |
| **Each killable actor dies** | the successor or sweep keeps the thread moving |
| **An unscripted act** | an inference event catches it |
| **A coupling input** (another thread's flag) | the pace changes the way you designed |
| **Fast-forward** | later stages do not re-fire |
| **A quest the world has moved past** | it is refused |

Run `--coverage`: it must show every event fired, every Want deadline fired and every Quest completed.

## 6.5 Break it on purpose

Two quick checks that the safety nets work:
- **Remove an own-stage guard** from a copy of the generated repository: `thread-check` fails, and the fast-forward scenario re-fires the event.
- **Delete an inference or successor event**: the matching scenario fails, because the thread stalls.

---

# Part 7. Review and fix

## 7.1 Thread checklist

- [ ] One-sentence premise and the idle outcome are written.
- [ ] The class is chosen, and the graph has the right shape (terminals; bounded cycles with a floor; forward only).
- [ ] Every killable actor has a successor or a sweep.
- [ ] Every Want's `on_deadline` sets **only an intent flag**.
- [ ] Every event passes the guard checklist (4.7), and `thread-check` is clean.
- [ ] Every Fact nobody knows is revealed by some Effect; every `SECRET` edge is revealed or `permanent_secret`. No milestone depends on an NPC *speaking* (PR-16).
- [ ] Every Want has a state test for each way the player could meet its `desire`, not only the Quests you wrote (CP-11).
- [ ] Every flag is declared; every flag is set and read or listed in the interface.
- [ ] Each terminal event is listed in `interface.terminals`, sets a result flag, is not read positively by anything else, and leaves **no Want of the thread running** (4.7).
- [ ] The interface names what other threads must read.
- [ ] The scenarios in 6.4 exist and pass; coverage is complete.
- [ ] Text is short, British English, and free of derived stats.

## 7.2 Campaign checklist

- [ ] The genesis event is guarded by `not <thread>_armed`.
- [ ] `opening_module` is in `modules`; every `unlocks` key is in `modules`.
- [ ] Each Quest is a Resolution Path of one Want and applies that thread's contract.
- [ ] Each Quest has an availability gate (until PR-13).
- [ ] Overrides name real entities and authored fields only.
- [ ] Rooms match their size; locked exits have a DC or key.
- [ ] Every unknown SRD id is noted `[OPEN] (PR-4)`.
- [ ] A scenario runs the Campaign with the thread armed, and another with it unarmed.

## 7.3 Common mistakes

| Mistake | Symptom | Fix |
|---|---|---|
| A Want's fallback changes the world directly | it fires late and undoes the player's work | set an intent flag; apply it in a guarded event |
| No own-stage guard | a Campaign that starts past the stage re-fires it | add `not flag_set <result>` |
| Using `day_reached` in a World event | fires in every Sandbox on the same day | use a Want timer |
| A terminal leaves a Want running | the story agent improvises for someone whose story is over; the simulator fails | retire it in the terminal event |
| Forgetting `fail_want` in a Quest | the Want's deadline still fires | retire it in `on_complete` |
| Killing the actor stalls the thread | a scenario fails | add a successor or a sweep |
| An unscripted act strands the thread | a scenario fails | add an inference event |
| An event that must repeat | it fires once | unroll numbered cycles with a floor |
| Two keys in one Condition object | `a condition must have exactly one key, but found 2` | wrap them in `all` |
| An empty `all`, `any` or Effect list | schema error | remove the field |
| A bare `truth: TRUE` or a colon in a string | YAML parses it wrongly | quote the value |
| Writing a derived stat (`hp`, `ac`) | rejected | delete it |
| A one-token milestone id (`ask`) | `id must be lowercase ASCII tokens joined by single underscores` | `ms_ask` |
| `grant_reward` in an event or Want | rejected | only in a Quest's `on_complete` |
| A flag that is set and never read | `thread-check` fails | read it, or list it as an output |

---

# Part 8. Scaling up

## 8.1 Writing the 18 threads

1. Take a thread from the plot web (the Plot Web) and do the one-page design (3.1).
2. Decide its **class**, and borrow the shape from the matching example: `the-ferrymans-debt.md` (Resolvable), the-lineage-and-the-gate-born (Managed, with a Resolvable terminal and a Ratchet floor). A Ratchet is a long forward-only ladder; write the stage events with long Want timers and a `LOCKED` last stage.
3. Convert the thread's existing Wants: `urgent_when` becomes the armed flag plus an own-stage guard; each fallback flag becomes an intent flag read by exactly one event.
4. Write the thread card, the blocks, the scenarios.
5. List the thread's `interface`. The interaction grid between threads is **generated** from the interfaces: where one thread's `sets` meets another's `reads`.

## 8.2 Bounded cycles (Managed threads)

An event fires once, so a repeatable beat ("the hunt closes in; the player moves the boy") is written as numbered cycles with a floor. In the Lineage thread, cycle 1 and its reprieve are:

```yaml
kind: WORLD_EVENT
id: evt_lin_hunt_closes_1
scope: REGIONAL
origin: loc_dustport
when:
  all:
    - { flag_set: { flag: lin_armed } }
    - { flag_set: { flag: lin_hunt_due_1 } }
    - { not: { flag_set: { flag: lin_hunt_closes_1 } } }
    - { not: { flag_set: { flag: lin_reprieve_1 } } }
    - { edge_exists: { from: npc_dagna_rusk, kind: GUARDS, to: npc_ennis_pell } }
    - { not: { flag_set: { flag: lin_ennis_convenor } } }
then:
  - { set_flag: { flag: lin_hunt_closes_1 } }
truth: "The retriever finds the first hiding place's trail."
known_by: [npc_halvard_sorn]
```

```yaml
kind: WORLD_EVENT
id: evt_lin_reprieve_1
scope: REGIONAL
origin: loc_dustport
when:
  all:
    - { flag_set: { flag: lin_armed } }
    - { flag_set: { flag: lin_hunt_due_1 } }
    - { flag_set: { flag: lin_reprieve_1 } }
    - { not: { flag_set: { flag: lin_s3_hunted_2 } } }
    - { edge_exists: { from: npc_dagna_rusk, kind: GUARDS, to: npc_ennis_pell } }
    - { not: { flag_set: { flag: lin_ennis_convenor } } }
then:
  - { set_flag: { flag: lin_s3_hunted_2 } }
truth: "Ennis was moved in time. The retriever starts again from nothing."
known_by: [npc_halvard_sorn]
```

The first fires if the player has **not** bought a reprieve; the second fires if they have, and starts cycle 2. After the second reprieve the hunt is exhausted and the pressure resumes unconditionally. A third reprieve is not authored.

## 8.3 When you need something the engine cannot do

Do not invent it. Find the nearest pattern in the engine-capability register (the `CP-` patterns) and, if none fits, add a gap there. The platform requests most likely to touch a thread: relative time (PR-9), Campaign outcomes and succession (PR-10), Quest outcomes (PR-11), Want semantics (PR-12), Quest availability (PR-13), and, for lore and secrets, dialogue disclosure, a lore corpus and the narrator's disclosure gate (PR-14 to PR-16).

## 8.4 Who does what

| Task | Model |
|---|---|
| Design the graph, the contracts, the couplings, the successors | a creative model, with the owner |
| Write the blocks from an agreed design, convert Wants, write scenarios | a coding model |
| Run the tools and fix errors | either |

---

# Appendices

## A. Block cheat sheet

| Kind | Required | Optional (default) |
|---|---|---|
| `NPC` | `id`, `name`, `alignment`, `persona.summary`; class build: `race`, `levels`, `abilities`; or `monster` | `persona.voice_style`, `base_disposition` (0), `home`, `simulation_tier`, `skill_ranks`, `feats`, `equipment`, `advancement`, `templates`, `authority` (GUIDED) |
| `FACTION` | `id`, `name` | `summary` |
| `RELATIONSHIP` | `from`, `to`, `kind_of`, `sentiment`, `visibility` | `id`, `note`, `permanent_secret` (false) |
| `FACT` | `id`, `text`, `truth` | `known_by` ([]), `believed_by` ([]), `believed_as`, `subjects`, `authority` |
| `WANT` | `id`, `npc_id`, `priority`, `desire`; and `deadline_days` with `on_deadline` unless `authority: OPEN` | `stakes`, `urgent_when`, `methods` ([]), `forbidden` ([]), `resolution_paths` ([]), `simulation_tier` |
| `WORLD_EVENT` | `id`, `scope`, `origin`, `when`, `truth` | `then`, `rumor_seeds`, `propagation`, `known_by` ([]), `authority` |
| `QUEST` | `id`, `title`, `milestones` | `giver_npc_id`, `from_want`, `level_recommendation`, `on_complete` |
| `MODULE` | `id`, `title`, `target_level_min`, `target_level_max` | `key_locations`, `key_npcs` |
| `CAMPAIGN` | `id`, `world_id`, `title`, `summary`, `start_level`, `start_location`, `opening_module`, `content_descriptors`, `modules` | `start_day` (0), `unlocks` ({}), `flags` ([]), `allowed_options`, `est_length_hours` |
| `CAMPAIGN_OVERLAY` | `id`, `campaign_id`, and at least one of `adds`, `overrides`, `suppresses` | |
| `ROOM` | `id`, `title`, `lighting`, `description.initial`, `size` | `exits`, `layout`, `objects`, `description.detailed`, `module_id` |
| `ENCOUNTER` | `id`, `trigger`, `monsters` (each `monster`, `count`), `tactics` | `treasure`, `placement` per monster |
| `ITEM` | `id`, `base`, `name` | `description` |
| `MONSTER` | `id`, `base` | `name`, `advancement`, `templates` |
| `MIGRATION` | `id`, `eligible_when`, `then` | `description`, `until` (a Condition) |

## B. Conditions

| Predicate | Argument | True when |
|---|---|---|
| `all` / `any` / `not` | a list, a list, one Condition | combinators; lists must not be empty |
| `day_reached` | `n` | the Sandbox day is at least `n` |
| `day_between` | `{ from, to }` | the day is in the range |
| `season_is` | `SEASON` | the World calendar maps the day to that season |
| `flag_set` | `{ flag, toward? }` | the flag has been set |
| `flag_count_gte` | `{ flag, toward?, count }` | the flag was set at least `count` times |
| `edge_exists` | `{ from, kind, to, min_sentiment? }` | the edge exists now |
| `event_occurred` | `evt_x` | the event has fired in this Sandbox |
| `npc_alive` | `npc_x` | the NPC is not dead |
| `in_location` | `{ entity, location }` | `PLAYER` or an NPC is at the location |
| `fact_revealed` | `fact_x` | the player has been told the Fact |
| `quest_state` | `{ quest, state }` | `ACTIVE`, `COMPLETED` or `ABANDONED` |
| `milestone_complete` | `{ quest, milestone }` | that milestone is done |
| `has_item` | `{ item, qty? }` | the character holds the item |
| `player_level_gte` | `n` | the character level is at least `n` |
| `disposition_gte` / `_lte` | `{ npc, toward?, value }` | the NPC's disposition towards the player (or towards `toward`) |
| `faction_rep_gte` | `{ faction, value }` | the player's reputation (storage model is still open) |

The simulator models all except `season_is`, `has_item`, `player_level_gte`, `disposition_*`, `faction_rep_gte` and `milestone_complete`.

## C. Effects

| Effect | Argument | Does |
|---|---|---|
| `set_flag` | `{ flag, toward? }` | sets a declared effect-only flag (counts up) |
| `add_edge` | `{ from, kind, to, sentiment, visibility }` | adds a relationship edge |
| `remove_edge` | `{ from, kind, to }` | removes it |
| `reveal_edge` | `{ from, kind, to }` | the player learns the edge |
| `reveal_fact` | `fact_x` | the player learns the Fact |
| `activate_want` | `want_x` | starts the Want's clock |
| `resolve_want` / `fail_want` | `want_x` | retires it; `on_deadline` will not fire |
| `adjust_disposition` | `{ npc, toward?, delta }` | changes disposition by -100 to 100 |
| `move_npc` | `{ npc, to }` | moves an NPC to a `loc_` |
| `emit_ripple` | `{ origin, severity, event }` | sends news outward (`MINOR`, `MODERATE`, `MAJOR`) |
| `spawn_encounter` | `enc_x` or `{ encounter, location }` | starts an encounter |
| `start_quest` | `quest_x` | starts a Quest |
| `unlock_module` | `mod_x` | makes a Module available |
| `set_exit_state` | `{ room, exit, state }` | changes a door |
| `grant_reward` | `{ xp: { table: SRD_QUEST_XP, size }, treasure: { table: SRD_BY_LEVEL }, items }` | **Quest `on_complete` and Migrations only** |

Region-scope Effects (an edge touching a place or faction) reach distant regions **lazily**, when the player nears them; flags apply immediately.

## D. Platform limits that bind you today

An Effect list holds at most 64 Effects. A Condition nests at most 16 deep and has at most 256 nodes. Any text is at most 20,000 characters (the real caps will be much lower). A cascade within one player action runs a limited number of rounds (the pilot needs four; the platform limit is not set yet).

## E. Where the files go

| You write | The transformer writes |
|---|---|
| a note under `world/` with `engine: true` | one YAML per entity under `world/<kind>/` |
| `flags` block in the world's flag register | `manifest.yaml` (`flags:`) |
| notes under `campaigns/<slug>/` | `campaigns/<camp_id>/campaign.yaml`, `overlay.yaml`, `modules/<mod_id>/module.yaml`, `modules/<mod_id>/quests/<quest_id>.yaml` |
| `_thread: x` on a block | stripped (emitted as `thread: x` once PF-6 lands) |
| `_known_by_groups` on a Fact | resolved to `known_by` NPC ids |

## Links
`docs/thread-pattern.md`, `the-ferrymans-debt.md`, the-lineage-and-the-gate-born, the engine-capability register, the kit's conventions, the world's flag register, the-quay-boy

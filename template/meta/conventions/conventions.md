# Vault Conventions (v2.0)

**Status:** the rules every world codex follows. World-specific choices are **not** here: they live in
that world's own `meta/world-conventions.md`, in `world.config.yaml`, and in its fenced vault blocks.
**Authority:** where this file lists an engine vocabulary, the platform package
`@curiouslittledroid/authored-content` is the authority, not this file.

## 1. Purpose

A **world codex** is a human-readable, Obsidian-style lore vault. It is the upstream source for the
game engine's generated **Game Ready Repository** — a separate Git repository of typed YAML entities.
A **deterministic transformer** extracts those entities from the codex.

- **Codex:** lore, rationale, secrets, history, design notes. Prose-first.
- **Game Ready Repository (separate, generated):** closed-vocabulary YAML the engine consumes.
  **Never hand-edited.** Fix the note and re-run the transformer.
- **Terminology:** the platform's glossary calls *any* author's generated repository a
  **World Repository**. In the codex that term is retired; each world names its own repository.

## 2. Decisions the kit implements

1. The **vault root is the repository root**.
2. Engine content lives in **its own generated repository**, never in the codex.
3. The transformer is **deterministic** (no LLM in extraction). An LLM may help draft blocks, and a
   human reviews them.
4. **Structure and ids first; convert only what a campaign uses.**
5. **Closed vocabularies are not extended in the codex.** If a note needs a relationship kind, flag,
   effect, tactic, descriptor or mechanic the engine lacks, log it in the world's
   `meta/mechanics-gap-register.md`. Never invent it in an engine block. The engine cannot author new
   spells, feats, classes or item properties.
6. **Never author derived or stamped values:** no `hp`, `ac`, `bab`, `cr`, and no `author_id` or
   `world_id` (except `world_id` inside a CAMPAIGN block, where the schema requires it).
7. **No canon in Dataview queries.** Agents cannot render them. Dashboards are convenience only.

Every other decision is the world's, and is recorded in its own conventions note.

## 3. Layout

The **top-level contracts** are fixed, because the tooling depends on them:

```
/                       (vault root = repo root)
├── AGENTS.md           the agent brief: the kit's protocol plus the world's own
├── README.md           what this repository is, and what plays in it
├── ROADMAP.md          ordered work plan and status
├── world.config.yaml   the world's identity, ids and feature switches
├── .obsidian/          shared Obsidian settings (templates, attachments)
├── principles/         the world's own ground rules: pillars, permanence, tone, guardrails
├── world/              THE LORE. The transformer scans this.
├── campaigns/<id>/     campaigns, modules, sites, quests. The transformer scans this.
├── maps/               coordinate data, the atlas and images
├── meta/               the world's own decisions, templates and registers. Never extracted.
├── site/               the public player-facing site, if the world publishes one. Never extracted.
└── tools/              the kit's scripts, plus tools/local/ for the world's own
```

- The transformer scans **`world/` and `campaigns/` only**. `meta/` (including templates and
  examples) is never extracted.
- **How `world/` is organised inside is the world's business.** The tooling needs the directory and
  nothing else: the folder names in a world describe that world's shape, and a world with no gods
  has no `gods/`.
- Each folder has an `_index.md` (a map of content) that links its notes.

## 4. Source-of-truth rules

1. **One home per fact.** A decision is recorded in the note of the entity it is about. Other notes
   link to it and do not restate it.
2. **The note is the source for the engine.** An entity's engine data lives in a fenced `engine`
   block in its note. There is no second copy.
3. **The Game Ready Repository is generated.** Never hand-edit it.
4. **The canon digest is a summary**, one to two pages, GM-level. It never holds the only copy of a
   decision. Update it at the end of each session.
5. **Closed vocabularies are not extended in the codex** (§2, item 5). Log the gap; do not invent it.
6. **Status is explicit** (§6), so a fresh session can see what is settled.
7. **Never author derived or stamped values** (§2, item 6).
8. **No canon in Dataview queries** (§2, item 7).

## 5. Ids and filenames

- **Ids** use the engine grammar: lowercase ASCII tokens joined by single underscores, starting with a
  letter, at least two tokens, max 100 characters (e.g. `npc_tomas_reed`). **Ids never change once
  published.**
- **Filenames are the kebab-case slug of the title** (a note titled *The Long Eclipse* is
  `the-long-eclipse.md`). The id lives in
  frontmatter, so renaming a title or file does not change the id. **Filenames are unique vault-wide**
  (the one deliberate exception is `_index.md`, one per folder — link it with its folder path, e.g.
  `[[gods/_index|Gods]]`); add a suffix when two titles collide. Link with wikilinks, using an alias
  for display: `[[the-example|The Example]]`.

### 5.1 Engine ids (from `@mythical-forge/authored-content`)

| Kind | Prefix | Example |
|---|---|---|
| NPC | `npc_` | `npc_tomas_reed` |
| WANT | `want_` | `want_reed_clear_his_debt` |
| FACT | `fact_` | `fact_ferry_debt_was_padded` |
| RELATIONSHIP | `rel_` (optional id) | `rel_<faction>_controls_<target>` |
| WORLD_EVENT | `evt_` | `evt_ferry_seized` |
| QUEST | `quest_` | |
| ROOM | `room_` | |
| ENCOUNTER | `enc_` | |
| FACTION | `faction_` | `faction_ferry_creditors` |
| ITEM | `item_` | |
| MONSTER | `mon_` | |
| MODULE | `mod_` | |
| CAMPAIGN | `camp_` | |
| CAMPAIGN_OVERLAY | `overlay_` | |
| MIGRATION | `mig_` | |
| OVERLAND_GRAPH | `overland_` | `overland_<world>` (generated) |

Other engine id forms: **locations** are overland-graph nodes with `loc_` ids; **zones** use `zone_`
ids; **SRD references** use `srd_` ids.

### 5.2 Codex-only ids (never sent to the engine)

| Note type | Prefix |
|---|---|
| History event | `hist_` |
| Historical figure | `fig_` |
| God | `god_` |
| Race (a people or species) | `race_` |
| Plot-web thread | `thread_` |
| Topic | `topic_` |

A region note uses a `zone_` id (it is the zone the engine nodes refer to).

### 5.3 Zones

A **zone** is the engine's lazy-hydration unit (Design 04.1 §3) and an authored entity kind
(ADR-0009): the unit of "how much world arrives at once". Three homes, and they must agree:

| Home | Holds |
|---|---|
| A **REGION note** — `world/places/regions/`, and `world/places/continents/` for the continents | **Identity and prose**: `coords` (the centre), `parent`, and the `**Magic class:**` body line |
| `maps/atlas-features.yaml` | **Geometry**: `bounds` or a polygon, in the continent's frame; an area feature's `zone:` says which zone it sits in |
| Every other note's frontmatter `zone:` (an NPC reaches it through `home`) | **Membership** |

Rules:

- **The region notes define the zones.** The atlas draws them; nothing else invents one.
  `python3 tools/atlas_yaml.py maps/atlas-features.yaml` plus the atlas check (`meta/conventions/atlas.md`)
  keeps the two homes in step.
- **Two scales, and a zone is never a site.** A continent is a zone, and each of its regions is too.
  A settlement, site or other place **is not a zone**: it carries `zone:` and its own `loc_` id. An
  **area** on the map that is not a zone (a crater, a storm ring, a fae band) is a `loc_` feature
  with a `zone:` pointer — never a minted `zone_` id.
- **A zone records its parent** in frontmatter: `parent: zone_<continent>` on every region note of
  that continent. A continent has no `parent`. Nesting is therefore in the note, not only in the
  polygons.
- **A zone is infrastructure, not content.** Convert all of them, even when a campaign uses only a
  few: every other entity resolves against a zone.
- **The zone is a widening filter for lore retrieval**, not a hard one: a scene's candidates are
  `subjects` ∩ (its zone ∪ its parent zone) ∩ audience, then ranked (section 7.5).
- **Every `zone_` id must resolve.** A region note's `id:` and every other note's `zone:` and
  `parent:` are checked by the linter (section 16), and the atlas check covers the map. A note and a
  map that disagree are a lint error, not a style question.

## 6. Frontmatter

```yaml
---
id: loc_example            # required. Section 5.
kind: SETTLEMENT           # required. The note type (section 12).
title: Example             # required
aliases: []                # optional
name_status: working       # required: working | agreed (is the name final?)
status: working            # required: working | agreed | engine-ready | deprecated
engine: false              # required: true if the note contains real engine blocks
era: <the world's era>     # optional; the vocabulary is the world's (`eras` block)
tags: []                   # optional; the vocabulary is the world's (`tags-vocabulary` block)
sources: []                # optional
coords: { x: 0, y: 0 }     # optional, in km, in whatever frame the world's maps use
---
```

Kind-specific fields are listed in the templates. Notable ones:
- **NPC:** `groups: [{ id: faction_x, rank: common|select|inner }]` (§9.5; **factions only**),
  `race: race_x` (the people, a codex race id), `home`.
- **History event:** `t0` (years relative to the world's own zero), `official`, `myth`, `rival`,
  `group_knowledge`.
- **Settlement or place:** `zone`, `coords`; a site also has `origin`, the era that built it — never
  a measure of danger or loot.
- **Race:** `srd_race` (the SRD key the engine uses).
- **Figure:** `t0`.

**Status values:** `working` (drafted, may use placeholders) → `agreed` (the user accepted it) →
`engine-ready` (has valid engine blocks that pass the validator) → `deprecated` (superseded; name the
replacement in the body).

**`name_status` tracks the *name* only**, so the placeholder-names table is generated from it and
never maintained by hand.

## 7. Audience and disclosure

Two separate questions, two separate fields. **Do not read one as the other.**

| Axis | Question | Where it lives |
|---|---|---|
| **Audience** | Who in the world knows this, and which version do they believe? | Facts, group knowledge (§9.5), a history event's `official` / `myth` / `rival` layers |
| **Disclosure** | How may the narrator release it to the player *in play*? | frontmatter `disclosure:` and `**Disclosure:**` lines (below) |

**GM-only is not "never tell".** GM-only material is codex knowledge the narrator may *selectively
disclose*. Disclosure decides how. The platform enforces it in code (the register's PR-14 to PR-16);
the codex only classifies.

**`visibility` is retired.** It was built for a printed player primer and a player-facing view needs
**section** granularity, which only `disclosure` has. It is gone from the frontmatter schema, from
`tools/lint.py` (`FM005` retired, the code never reused) and from the templates. **`disclosure` is the
only publish axis.** A note that still carries the field lints clean; nothing reads it.
**Engine-block `visibility: PUBLIC | SECRET` is a different vocabulary and stays.**

### 7.1 Disclosure classes

| Class | The narrator may | It reaches the player by |
|---|---|---|
| `open` | state it whenever relevant: public knowledge, what anyone of the player's culture knows | nothing: it is already known |
| `earned` | foreshadow with atmosphere and rumour, but not state it; may state it once its reveal path has been taken | an earned path: an NPC who knows it tells the player, a check, a found document, an event, or the narrator's own validated choice when the optional `**Reveal when:**` condition holds |
| `sealed` | use it only to stay consistent; never hint beyond the authored `rumor_seeds` | a specific authored event or Quest: a keystone truth |

### 7.2 How to mark it

- **A note default:** frontmatter `disclosure: open | earned | sealed`. Use it for a note whose whole
  body is one class (a note under `world/secrets/`).
- **A section:** a `**Disclosure:** <class>` line as the first line under a heading marks that
  heading's section (an H2 and its H3s).
- **A reveal condition (optional, `earned` only):** a `**Reveal when:**` line under the same heading,
  **in words** for now (a standard body line, §9.6). The platform will accept it as a Condition when
  PR-15 lands.
- `python3 tools/lint.py` checks the values (FM011, DS001). `python3 tools/disclosure.py` reports the
  effective class of every section.

### 7.3 Defaults (the first that applies wins)

| Order | Rule | Class |
|---|---|---|
| 1 | An explicit `**Disclosure:**` line | as marked |
| 2 | The section is `## Secrets` | `earned` |
| 3 | A history event's frontmatter `official`, `myth` and `rival`, and any **Official:**, **Myth:** or **Rival:** line | `open` (to the groups that believe it) |
| 4 | A history event's **Truth:** line | `earned` |
| 5 | The note's frontmatter `disclosure:` | as set |
| - | Hooks, Author Notes, Open questions, Links, Engine, and THREAD, CAMPAIGN, MODULE, OVERLAY and INDEX notes | not lore: left out of the corpus |
| - | A link to a plot-web thread (below an `## Hooks` heading) | not lore: **`## Hooks` is the only home for a thread reference.** The site cannot publish a thread, so a thread named in `## Details` reaches a player as an orphaned proper noun with no page |
| - | A design citation — a register id (`CP-6`, `PR-4`), a `§` reference, a step number, a note name in parentheses | not lore: **`## Author Notes` is the only home for authoring and engine citations.** They are worth keeping for the author but mean nothing to a player, and the site scrubber otherwise leaves a hole where the citation was |
| - | A `**Want:**` or `**Wants:**` line (an NPC's own motive) | `earned`, **audience that NPC only**: it always reaches that NPC's own agent, because it shapes how the NPC treats the player, but the narrator may not state it and no other NPC receives it |
| - | A line of design guidance ("the party is meant to meet him early") | not lore: move it to `## Hooks` |
| - | **Anything else is `unreviewed`: it fails closed as `earned`** | `earned` |

### 7.4 How a world keeps its secrets

- **A note's Summary and Details state only what the narrator may say (`open`).** The Summary is the
  first thing a retriever returns, so it is written as the public face. Hidden truth goes under
  `## Secrets` (class `earned`). A keystone is marked `**Disclosure:** sealed` as the first line; a
  note that has both uses `## Secrets` for the first and a second section for the second (the world
  names that heading; §10).
- **Moving text is not changing canon.** Review moves a clause; it never rewrites a decision.
- **Review is recorded in frontmatter.** A note whose Summary and Details are open-only carries
  `disclosure: open`; `## Secrets` stays `earned` and the keystone section `sealed`, because the
  section rules come first. A note that is hidden truth throughout carries `disclosure: earned`.
- **A truth-ledger note is the hidden truth.** It carries `disclosure: earned` (or `sealed`) in
  frontmatter; its open layers come from the frontmatter `official` / `myth` / `rival`.
- **Every lore section in `world/` is classified, and `python3 tools/disclosure.py --check` must stay
  clean.** A new or edited note gets a note-level `disclosure:` once its Summary and Details hold only
  what the narrator may state. A model may propose where a clause belongs; the user confirms, and a
  move is never a rewrite of canon.

**An NPC's own Wants always reach its own agent.** A Want is how the NPC reacts to the player, so the
agent needs it even though the NPC may never say it. The engine does this for an engine Want; until an
NPC is converted, the prose `**Want:**` line is the only source, so the export keeps it, with the NPC
as its only audience.

**What an NPC knows by default:** the common knowledge of its race and home region, plus its groups'
tiers (§9.5), each **at the layer it believes**. A believer of the myth is given the myth, never the
truth.

**Out of scope for the first version:** the player *inferring* a secret without being told, and an NPC
remembering what the player told it.

### 7.5 Lore chunks and prose audience

Every classified lore section becomes **Lore chunks** — the retrievable, audience-scoped form of the
prose that NPC agents and the narrator read. `tools/lore_export.py` implements these rules and
`tools/test_lore_export.py` tests them.

- **One chunk per paragraph.** A paragraph over **300 words** splits at sentence boundaries. Nothing
  is truncated, nothing is rejected, and no chunk is smaller than a sentence. A `**Summary:**` line is
  a chunk: it is the first thing a retriever returns.
- **The class is `disclosure.classify`'s**, never a second opinion: the `**Disclosure:**` line, then
  `## Secrets`, then a history event's layer lines, then the note's `disclosure:`. `python3
  tools/disclosure.py --check` stays the gate.
- **A history event's layer lines split into separate chunks**, each with its own `layer`:
  `**Official:**` → `official`, `**Myth:**` → `myth`, `**Rival:**` → `rival`, `**Truth:**` → `truth`.
  Merging them would hand a believer of the myth the truth. Every other section's layer is `truth`.
- **Not lore, so not chunked:** `## Hooks`, `## Author Notes`, `## Open questions`, `## Links`,
  `## Engine`, `Run it`, a `Named members` roster, and every THREAD, CAMPAIGN, MODULE, OVERLAY and
  INDEX note.
- **Audience is derived, not authored.** Who in the world could know the section:

| Section | Audience |
|---|---|
| an explicit `**Known by:** faction_x@inner, race_human` line under the heading | that |
| an NPC's `**Want:**` line, or its `## Secrets` / `## Keystone secrets` | **itself only** |
| `open` | everyone (`scope: world`) |
| a FACTION note's `earned` / `sealed` section | that faction, `select` / `inner` |
| a REGION, SETTLEMENT or SITE's `earned` / `sealed` section | that note's zone |
| anything else | everyone |

- **`**Known by:**` is the override**, written `faction_x@inner` (a `race_` group ignores tiers), or
  `self`. It names groups and tiers, never NPC ids — so a roster edit costs no re-embedding.
- **`subjects` are the `[[links]]`.** A chunk is about what its prose links to: every wikilink target
  that resolves to a note becomes a subject, plus any literal ids. **So link the things a sentence is
  about.** Measured from prose alone, almost no chunk had a subject beyond its own topic; from the
  links, the majority do. A paragraph with no link and no id is retrievable only by meaning.
- **Only `sealed` needs a named reveal path.** `earned` is reached by a generic authored path (an NPC
  in its audience, a document, a check), so it needs no per-chunk Condition; a keystone names its
  event or Quest. Writing `**Reveal when:**` on an `earned` section is encouraged and carried into the
  chunk, but not required.
- **A chunk id is logical**, `lore_<topic>_<heading>_<nn>`: stable, diffable, and never
  content-addressed. The platform's compiler owns the content hash.
- **Audience is a permission gate, not a selector.** It does not narrow the corpus much — most
  sections of a world are readable by everyone — so `subjects` and the scene's zone do the narrowing.
  Write a sentence so that its links say what it is about, and expect a top-k to be reached by
  subjects rather than by audience.

## 8. Fenced blocks and engine blocks

### 8.1 Fenced blocks

A **fenced block** is Markdown's triple-backtick code block. The word after the opening backticks is
the **info string**. Obsidian renders the contents as code (wikilinks inside it are not followed), and
the tools read the info string to decide what the block means:

| Info string | Meaning | Home |
|---|---|---|
| `engine` | Real engine YAML. The transformer extracts it, but only from notes with `engine: true`. | the entity's note |
| `engine-example` | An example that must validate but is never extracted. | templates and guides |
| `flags` | The world's flag declarations. | the note `vault.notes.flags` names |
| `tags-vocabulary` | What a `tags:` entry may be. | the world's tag-vocabulary note |
| `chronology` | The date prefix and the present year. | the note `vault.notes.calendar` names |
| `eras` | The values `era:` may take, in order. | the note `vault.notes.eras` names |
| `site-vocabulary` | Published tags, keystones and reviewed plot-web surfaces. | the note `vault.notes.site_vocabulary` names |
| `yaml`, `markdown` | Documentation only; ignored by the tools. | anywhere |

A block is **inert when absent**: a world that has not written one loses that check rather than
failing to build. All but `engine` and `engine-example` are read by `tools/kit_config.py` through the
`BLOCK_INFO` map, so a world declares *which note* and the kit knows *what to look for*. An empty
list is written `[]` — a world that has declared no flags yet says exactly that.

**Declared but missing is not absent.** The inert rule covers a world that never mentions eras; a
world that names a note in `vault.notes.eras` and whose note carries no block is a promise the vault
does not keep, and `tools/check_config.py` reports it as an error, naming the note (`conventions.md`
§16 has the check and its levels).

Opening and closing fences must match. To show a block *inside* a block, wrap it in a longer fence
(four backticks). A note may contain several blocks.

### 8.2 Engine blocks

A fenced code block whose info string is `engine`, containing YAML for **one entity**. A note may
contain several. The transformer reads only notes with `engine: true` and ignores blocks whose info
string is `engine-example`.

````markdown
```engine
kind: FACT
id: fact_example
text: "A short statement."
truth: TRUE
authority: LOCKED
```
````

Rules:
- Field names and enums come from the engine schemas. Do not invent fields.
- Free text in a block is **untrusted prompt input** and **token-capped**. Keep it short. The prose
  carries the long version.
- Every referenced id must exist in the codex.
- `authority` defaults to `GUIDED`. Use `LOCKED` for permanence-rule outcomes and hard truths.
- **Placeholders** are written `REPLACE`. A committed note with `REPLACE` in an `engine` block, or in
  required frontmatter, fails lint.
- **Templates** use `engine-example` blocks that always validate; rename the info string when the
  block is real.
- **Flags** are declared once, in the `flags` block the world config names. The transformer copies it
  into `manifest.yaml`; every `set_flag` / `flag_set` must name a flag declared there.

## 9. Where blocks live, fragments and directives

### 9.1 Block homes (one home per kind)

| Block kind | Lives in the note of |
|---|---|
| WANT | its NPC (`npc_id`) |
| RELATIONSHIP | its `from` entity |
| FACT | the note about its topic (a history event, place or thread) |
| WORLD_EVENT | its plot-web thread |
| OVERLAND_NODE | the settlement or place itself |
| OVERLAND_EDGE | the note of its `from` node (each pair once) |
| FACTION, NPC, ITEM, MONSTER, CAMPAIGN, MODULE | their own notes |
| FLAGS | the world's flags note, a `flags` block; not an engine entity |

### 9.2 Fragments

The engine's overland graph is one entity. Notes contribute **fragments** that the transformer
assembles into a single graph:

```yaml
kind: OVERLAND_NODE      # id, name, type (SETTLEMENT | SITE_ENTRANCE | POINT_OF_INTEREST | WILDERNESS), zone_id, description
kind: OVERLAND_EDGE      # from, to, distance_km, terrain (STANDARD | DIFFICULT | TRACKLESS), danger (0-10)
```

### 9.3 Units

**The codex uses kilometres.** The engine uses **whole miles** (`distance_miles`). The transformer
converts (1 mile = 1.609344 km, rounded, minimum 1). **Each route stores its own explicit km**,
because real routes meander. `coords` are for maps only.

### 9.4 Transformer directives

Fields beginning with `_` are **codex-level directives** that the transformer resolves and removes
before output (they are not engine fields):
- `_known_by_groups` and `_believed_by_groups` on FACT blocks (§9.5).
- `_thread: <slug>` on any block that lives outside its thread's note (a Want, a Quest, a genesis
  event). It records which thread the entity belongs to. A thread note's own blocks inherit the
  `thread:` slug from its frontmatter.

### 9.5 Group knowledge

The engine's `known_by` and `believed_by` accept **NPC ids only**, but the world's knowledge belongs
to groups. The codex expresses it by **group and tier**, and the transformer resolves it to NPC ids.

- **Tiers (nested):** `common` (well known by the group's members), `select` (known only by select
  members and the inner circle), `inner` (known only by the upper hierarchy).
- **A group** is a `faction_` or `race_` entity.
- **A `faction_` group** resolves by the NPC's declared rank. **A `race_` group** resolves to every
  NPC whose frontmatter `race` equals it, ignoring tiers (a people has no hierarchy).
- **An NPC** declares its standing in frontmatter: `groups: [{ id: faction_x, rank: inner }]`.
- **Resolution:** a fact at tier *T* for group *G* is known by every named NPC of *G* whose rank is
  *T* or higher (`inner` ≥ `select` ≥ `common`).
- **A fact block** writes `_known_by_groups: [{ group: faction_x, tier: inner }]` (and
  `_believed_by_groups`).
- **History-event notes** also record `group_knowledge` in frontmatter, as the prose-level record.
- **If a group has no named NPC at the needed tier**, the transformer warns and leaves `known_by`
  empty. The engine requires a reveal path for facts nobody knows, so such notes stay `engine: false`
  until representative NPCs exist.

### 9.6 Deferred engine fields (notes that are not yet `engine: true`)

A note may still be `engine: false` while the lore is settled. Record the values the engine block will
need, in a **standard body line**, so a later step can write the block without re-reading the prose.
The transformer reads the block, not the line.

| Note type | Standard line | Example |
|---|---|---|
| ITEM, relic | `**SRD base:** \`srd_…\`` | `**SRD base:** srd_longsword` |
| CREATURE (or an NPC built from a monster) | `**SRD base:** \`srd_…\``, `**templates:** \`TEMPLATE\`, …` | `**SRD base:** srd_satyr` |
| A place | `**Magic class:** well \| knot \| eddy \| sink \| normal` — one clause | `**Magic class:** well` |
| An `earned` section the narrator may choose to disclose | `**Reveal when:** <the condition, in words>` under the heading (§7.2) | `**Reveal when:** the player holds the relic and has met the Reeve` |

Rules:
- Write `[OPEN]` (not `REPLACE`) when the value is unknown; `REPLACE` in prose is a lint warning.
- The line is **not** frontmatter: frontmatter stays the fixed field list of §6.
- Once the matching engine block is written, the line stays: it is the human-readable record for the
  GM, and the block is the engine record.

### 9.7 Stand-in patterns (where the vocabulary is missing)

Some world properties have no engine field. **Do not invent one.** §9.6 covers a value the engine
will have later, and `thread-pattern.md` carries the structural patterns already in force as `CP-`
cards. Classify the rest in your own `meta/mechanics-gap-register.md`, which is where a world records
the gaps *it* hits and the workaround in force. What the engine does about them is the kit owner's
call, not a world's.

### 9.8 Threads, flags, Campaigns and Modules

The full pattern is in `meta/conventions/thread-pattern.md`. The rules the linter and tools enforce:

- **A thread is a state graph.** Its note is a *thread card* (template `thread`): premise, actors and
  successors, the state graph, an **interface**, quest contracts, the idle run. The thread note's
  frontmatter carries `interface: { class, arms, reads, sets, terminals, inputs_from, outputs_to }`
  (one line, codex-only); `tools/thread-check.mjs` compares it to the blocks, and checks that each
  listed **terminal event** is terminal. The transformer writes the interface and the thread's members
  to `codex-threads.yaml` in the Game Ready Repository (tooling only, not an entity).
- **Block homes (extended):** a thread's World Events live in the thread note; a Want in its NPC's
  note; a **Quest in its Module's note**; a Module, a Campaign and an overlay each in their own note
  under `campaigns/<slug>/` (`kind: MODULE`, `CAMPAIGN`, `OVERLAY`; the overlay id is `overlay_…`).
  The transformer writes them to
  `campaigns/<camp_id>/{campaign.yaml, overlay.yaml, modules/<mod>/{module.yaml, quests/}}`.
- **Flag families** (name and use): `<thread>_armed`; `<thread>_s<N>_<name>` (stage, one-way);
  `<thread>_<thing>_due` (intent); `<thread>_<thing>` (outcome or history); a counter
  (`<thread>_<thing>`, tested with `flag_count_gte`); a trait (with `toward`). Every flag a block sets
  or tests is declared in the world's flags block; `tools/thread-check.mjs` reports flags read but
  never set, set but never read, and declared but unused.
- **Own-stage guard:** every World Event, and every Want that sets an intent flag, tests `not flag_set`
  on a flag it sets itself. `thread-check` fails a source without one.
- **Wants propose, events dispose:** a Want's `on_deadline` sets an **intent** flag only. A guarded
  World Event applies the change.
- **Quests apply contracts** from the thread card; a Quest that defeats a Want retires it (`fail_want`
  or `resolve_want`).
- **A Campaign** arms threads with a genesis World Event in its overlay (`day_reached: 0`, guarded by
  `not <thread>_armed`). It never edits a thread's events.
- The step-by-step tutorial for writing a thread, Campaign, Modules and Quests, and every block, is
  `meta/conventions/campaign-authoring-guide.md`.

## 10. Note body

Seven headings are **recognised** by the tooling. This is the whole of the contract:

```
# Title
**Summary:** two or three sentences.
## Details
## Secrets          (GM-only; omit if none)
## Hooks            (scene hooks, and every plot-web thread reference)
## Author Notes     (engine and authoring citations; omit if none)
## Links            (related notes)
## Open questions   ([OPEN] items)
## Engine           (engine blocks, if any)
```

`## Hooks` and `## Author Notes` are the two **not-lore** homes in a note: the first is for the GM,
the second for whoever maintains it. Both are excluded from the corpus by `disclosure.classify`, so
nothing under them can reach the public site. Putting a thread link under `## Hooks` and a design
citation under `## Author Notes` is therefore the fix, not a workaround: the content stays in the
note, and the published page keeps only the lore.

**Any other `## heading` is lore.** It publishes, and it therefore needs a disclosure class — from the
note's frontmatter or a `**Disclosure:**` line — or `disclosure.py --check` fails. That is the whole
rule: **a world may add any heading it likes, and the tooling will treat it as world prose.** A world
declares the extra headings it uses, in its own conventions note, so a later session knows they are
deliberate rather than accidental.

## 11. Style

- **One language, one spelling, one system of units, per world** — declared in `world.config.yaml`.
  The kit's default is British English and metric; metric in the **codex** is not optional, because
  the transformer does exactly one km → miles conversion.
- **Dates** are written relative to the world's own zero, with "years before present" where useful.
  The world's date prefix is the `chronology` block's, not a literal the tools assume.
- 200–600 words per note. Split a note that grows beyond that.
- Prefer tables and short bullets. State numbers where they matter.
- Mark an undecided item `[OPEN]`, and list it in the world's open-questions note. A settled decision
  needs **no marker**: the note's `status` says it is settled. Do not write "(decided)" against a
  heading or a bullet.
- Link the first mention of another entity with a wikilink.
- **Names that collide** are ruled on in the world's naming-decisions note: an empty clash is renamed,
  a clash the world has a cause for is kept and disambiguated. Never rename one silently.

## 12. Note types and templates

All templates are the kit's, and their example engine blocks validate against the engine package.

| Template | `kind` | Id prefix | Engine output |
|---|---|---|---|
| `settlement` | SETTLEMENT | `loc_` | OVERLAND_NODE and edges |
| `place` | PLACE | `loc_` | OVERLAND_NODE (site, point of interest, wilderness) |
| `region` | REGION | `zone_` | none (a zone id) |
| `faction` | FACTION | `faction_` | FACTION, RELATIONSHIP |
| `npc` | NPC | `npc_` | NPC, WANT |
| `god` | GOD | `god_` | none (lore) |
| `race` | RACE | `race_` | none (maps to an SRD race key) |
| `creature` | CREATURE | `mon_` | MONSTER |
| `item` | ITEM | `item_` | ITEM |
| `history-event` | HISTORY_EVENT | `hist_` | FACT |
| `figure` | FIGURE | `fig_` | none (may become an NPC) |
| `thread` | THREAD | `thread_` | WORLD_EVENT, FACT (its Wants live in NPC notes, its Quests in Module notes) |
| `topic` | TOPIC | `topic_` | none |
| `campaign` | CAMPAIGN | `camp_` | CAMPAIGN |
| `module` | MODULE | `mod_` | MODULE |
| `index` | INDEX | `topic_` | none |

A world that needs a note type the kit lacks adds a template beside the kit's and says so in its own
conventions note. Rooms, encounters and quests get templates with the campaign pipeline.

## 13. Engine vocabularies (reference; the package is the authority)

Every list below is closed, and none of them is authoritative: the **schema package can be asked**,
and its answer is what `transform` and `validate` enforce. Once it is installed
(`meta/conventions/tooling.md` has the two lines), this prints the live lists at the version this
world pins:

```bash
node -e "const a = require('@curiouslittledroid/authored-content');
for (const k of ['ENTITY_KINDS', 'RELATIONSHIP_KINDS', 'AUTHORITY_LEVELS', 'WANT_METHODS',
                 'ENCOUNTER_TACTICS', 'CONTENT_DESCRIPTORS', 'JUDGEMENT_TAGS', 'MILESTONE_TYPES',
                 'NODE_TYPES', 'TERRAIN', 'SIMULATION_TIERS', 'EFFECT_NAMES', 'PREDICATE_NAMES',
                 'COMBINATOR_NAMES'])
  console.log(k.padEnd(20), (a[k] ?? []).join(', '))"
```

That is the answer to *"can the engine do this?"* — cheaper and truer than any list, including this
one, which is here so you can read rather than run.

- **Entity kinds:** `NPC`, `WANT`, `FACT`, `RELATIONSHIP`, `WORLD_EVENT`, `QUEST`, `ROOM`, `SITE`,
  `ENCOUNTER`, `FACTION`, `ITEM`, `MONSTER`, `MODULE`, `CAMPAIGN`, `CAMPAIGN_OVERLAY`, `MIGRATION`,
  `OVERLAND_GRAPH`, `ZONE`. The note type each corresponds to, and its id prefix, are in
  `conventions.md` §5.1.
- **Relationship kinds:** `KIN_OF`, `ALLY_OF`, `RIVAL_OF`, `ENEMY_OF`, `LOVES`, `FEARS`, `DISTRUSTS`,
  `OWES`, `MEMBER_OF`, `LEADS`, `SERVES`, `SECRETLY_SERVES`, `EMPLOYS`, `RESIDES_AT`, `GUARDS`,
  `CONTROLS`, `OWNS`, `SEEKS`, `KNOWS_SECRET_OF`, `BELIEVES`.
- **Authority:** `LOCKED`, `GUIDED`, `OPEN`.
- **Want methods:** `PERSUADE`, `HIRE`, `STEAL`, `THREATEN`, `VIOLENCE`, `FLEE`.
- **Encounter tactics:** `AMBUSH`, `DEFEND_POSITION`, `PURSUE`, `FLEE_AT_HALF_HP`.
- **Content descriptors:** `VIOLENCE`, `HORROR`, `MATURE_THEMES`.
- **Judgement tags** (engine-set only): `CRUEL`, `MERCIFUL`, `DECEITFUL`, `HONOURABLE`.
- **Overland node types:** `SETTLEMENT`, `SITE_ENTRANCE`, `POINT_OF_INTEREST`, `WILDERNESS`.
  **Terrain:** `STANDARD`, `DIFFICULT`, `TRACKLESS`.
- **Simulation tiers:** `MAJOR`, `MINOR`. **World Event scope:** `LOCAL`, `REGIONAL`, `MACRO`.
- **Milestone types:** `DIALOGUE`, `FETCH`, `DELIVER`.
- **Effects and conditions:** `EFFECT_NAMES`, `PREDICATE_NAMES` and `COMBINATOR_NAMES` are the live
  lists, so they are not transcribed here. The block's shape, and how sources, conditions and effects
  combine into a state graph, is `campaign-authoring-guide.md` and `thread-pattern.md`.

**When a value is not there, the engine does not have it — and that is not yours to decide.** The
closed vocabularies stay closed (`conventions.md` §2, item 5): a note that needs a mechanic the engine
lacks uses the vocabulary that does exist, writes the value it needs in the **standard body line** if
the field is coming (§9.6), uses the stand-in pattern in force if one exists (§9.7), and **logs it in
`meta/mechanics-gap-register.md`** with the workaround. That log is a **request**, not a decision: a
world cannot extend a closed vocabulary by naming what it is missing, and the catalogue of what the
platform has been asked for is the kit owner's, kept with the platform rather than in the vault. The
kit never assumes a gap is universal — a mechanic one world needs may be irrelevant to another.

## 14. Obsidian setup

- `.obsidian/` is committed with the core Templates plugin pointing at the world's templates,
  attachments in `maps/`, wikilinks on and "shortest path" links. **Local state is ignored, never
  committed:** `workspace*.json`, `community-plugins.json`, `.obsidian/plugins/` and caches. Each
  contributor's own plugin installs (for example Obsidian Git or a terminal plugin) stay on their
  machine.
- **Dataview is optional**, for non-canonical dashboards only. No other community plugins in the
  committed config.
- Plain Markdown, wikilinks and YAML frontmatter only. No plugin may store data in a non-Markdown
  format.

## 15. Commits

One commit per session or coherent change. Update the status table in `ROADMAP.md` in the same commit.

## 16. Linting

`tools/lint.py` checks the mechanical rules in this file. **Run it before every commit**, and after any
bulk or scripted edit, whichever model did the work. It uses only the Python standard library.

```
python3 tools/lint.py              # lint the whole vault
python3 tools/lint.py world/gods   # report on one folder (links still resolve vault-wide)
python3 tools/lint.py --strict     # warnings fail too
python3 tools/lint.py --json       # machine-readable
python3 tools/test_lint.py         # the linter's own tests
python3 tools/disclosure.py --check   # every lore section is classified (section 7); exit 1 if not
python3 tools/check_config.py      # world.config.yaml and its blocks agree with the vault
```

`check_config.py` asks the questions the linter cannot, because they are about the file the linter
reads rather than about a note: every id in `vault.notes` resolves to a note that carries its block,
which blocks are present and shaped the way their reader expects (§8.1), whether two site sections
claim the same kind, whether a published tag is in the world's `tags-vocabulary`, and whether
`kit_config.py` and `kit_config.mjs` agree about this config. It is the **first check on the vault** in
`tools/verify-world.sh`, because a config fault makes every later check quieter rather than louder.

Its levels draw the line the linter draws: an **error** is a config and a vault contradicting each
other; a **warning** is something declared that is not there or used that is not declared; a
**note** is a value still carrying the template's `REPLACE`, which is the author's to-do and never a
failure. Only errors fail the run — a world that was just forked is not red.

**Errors** (must be fixed; exit code 1):

| Code | Rule |
|---|---|
| FM001–FM011 | Frontmatter present with all required fields; valid `status`, `name_status`, `engine`; no `REPLACE` in required fields; `engine-ready` needs `engine: true`; `race` must be a `race_` id; `disclosure` must be `open`, `earned` or `sealed` |
| *(retired)* | FM005 (`visibility` vocabulary) is retired with the field itself (§7). The code is not reused. |
| DS001 | A `**Disclosure:**` line names a valid class (§7.2) |
| ID001–ID004 | Id grammar, id prefix matches `kind`, no duplicate ids |
| FN001–FN002 | Kebab-case filenames, unique vault-wide (except `_index.md`) |
| LK001–LK005 | Balanced `[[ ]]`, no leaked `§` separator, no dead or ambiguous links, no links to non-Markdown files without an extension |
| EN001–EN007 | `engine: true` iff real `engine` blocks exist, every block has a `kind`, no `hp`/`ac`/`bab`/`cr`/`author_id`, `world_id` only in a CAMPAIGN block, no `REPLACE` in real blocks, every referenced id exists, every `set_flag` names a declared flag |
| TG001 | A tag is not in the world's `tags-vocabulary` block |

**Warnings** (fix when convenient; `--strict` fails on them): unknown `era`/`kind`, unknown ids in
frontmatter group fields (`groups`, `home`, `zone`, `race`; REF001), missing or truncated
`**Summary:**` or `**Purpose:**` line, empty sections, `REPLACE` left in prose, non-British spellings
(when the world's `vault.spelling` is `british`), orphan notes.

The linter does **not** check engine schemas (the transformer does that with
`@mythical-forge/authored-content`), canon consistency, or whether prose is any good. Nor does it
read `world.config.yaml`: `check_config.py` is the check for the file, and the two are separate so
that a config fault is named once, in the terms of the key that is wrong.

### 16.1 Citing a document

When a note cites a rule by number, name the document in the same sentence:

- In the kit's own voice: `meta/conventions/conventions.md` §9.6. A world holds the same document
  at the same path and cites it as "the kit's `conventions.md` §9.6".
- **Never a wikilink** into the kit (the kit's documents are prose, not notes: no frontmatter, no id,
  and the linter does not read them as part of the vault) and **never a bare basename**: `site.md`
  is two different documents in a world — the kit's `meta/conventions/site.md` and the world's
  `meta/site.md`.
- **A number only if the document numbers its sections.** A document whose sections have names is
  cited by name: "the section on required reviewers".
- A citation of where something *used to be* says so: "formerly the `site.md` document, §3.4".
- **A citation this repository cannot check** ends its line with `citations: ignore`: a world's note
  named from the kit, or an example of a bad citation in prose. In the first five lines of a file it
  opts the whole file out. Use it for what is genuinely uncheckable, never for what is merely
  inconvenient — the check exists because a template's stale citation stayed invisible for two
  releases, and each of those releases fixed a hole in the check itself.

`tools/check_citations.py` enforces all five and fails on a number that does not exist. A citation
binds to the nearest document named **before** it, so name the document in the same sentence — and
in the kit, `--as-world` is the same check with this vault's neighbours in place, which is where a
binding that only the world layout produces shows up. **A document
that renumbers must sweep its citations** — in this repository and in every world that has synced it.
The check is what makes that sweep mechanical rather than a promise, and it is the only thing in the
toolchain that notices: a stale number reads exactly like a correct one.

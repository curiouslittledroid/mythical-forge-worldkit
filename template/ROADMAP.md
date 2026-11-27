# World Development Roadmap

This file tells a fresh session (human or AI) **what to do next, in what order, and with what
context**. Read the first part below, then pick the next step and follow its **Read first**.

It is a **skeleton**: the step order, the shape of each step and the map/cost guidance are the
worldkit's, because they hold for any world built this way. Everything about *this* world — its
status, its notes, its open items — is yours to fill in as you go. Sections 1, 4 and 5 start empty
on purpose.

**The step numbers are stable.** The worldkit's documents cite them by number (`meta/conventions/thread-pattern.md`
refers to "Step 12", `meta/conventions/site.md` to "Step 16"), so keep the numbering even if you rename a step.

---

## 0. How to use this roadmap

### 0.1 Where things are

The canon is the **vault** at the repository root. The top-level layout is fixed by the tooling (the
kit's `meta/conventions/conventions.md` §3); how `world/` is organised inside it is yours.

| Path | What it is |
|---|---|
| `AGENTS.md` | The agent brief: this world's orientation, then the worldkit's shared protocol. **Read first.** |
| `README.md` | What this repository is, and how to start. |
| `ROADMAP.md` | This file. |
| `world.config.yaml` | **The world's identity:** ids, title, slug, the notes the tools read, the feature switches, the site's navigation. |
| `TOOLING_VERSION` | The pinned worldkit version. Moved by `tools/sync-tooling.sh`; never hand-edited. |
| the kit's `meta/conventions/conventions.md` | **The rules:** layout, ids, frontmatter, engine blocks, disclosure, status. |
| `meta/conventions/` | Every world-facing kit document, at the pinned version. Written by the sync, never by hand. |
| `meta/world-conventions.md` | **This world's choices** on top of those rules: its folder shape, the headings it adds, its vocabularies, its keystones. |
| `meta/` | This world's own decisions: `meta/canon-digest.md`, `meta/names.md`, `meta/open-questions.md`, `meta/mechanics-gap-register.md`, the site notes. Never extracted by the transformer. |
| `principles/` | The four notes that decide what the world is. **Nothing else can be written well until they are answered.** |
| `world/`, `campaigns/` | The lore. **The transformer scans these two only.** |
| `maps/` | Coordinate data and the atlas. |
| `site/` | The public, player-facing site, if the world publishes one. |
| `tools/` | The worldkit's tools, vendored and pinned. **`tools/local/` is the world's own** and the sync never touches it. |
| `meta/templates/` | One template per note type, **mirrored from the kit**: never add a file here, it will be deleted. |
| `example-world/` | The demo world the kit ships, mirrored here so you have something to read. **Delete it once your own notes exist.** |

### 0.2 How to work

The session protocol, the persona, the vault and engine rules and the writing conventions are in
**`AGENTS.md`** (loaded automatically by most coding agents). They are the worldkit's, shared by
every world, and synced there by `tools/sync-agent-protocol.py`.

The short version: read the step's **Read first**, never contradict a settled decision, work by
**grilling rounds with recommended answers**, record **decisions** (not discussion) in the entity's
own note, one home per fact, lint after every bulk edit, and update the status tracker below
before you stop.

### 0.3 Which model to use (cost guidance)

The session protocol is the same for every step; only the class of work changes.

| Value | Use for | Example model class |
|---|---|---|
| **Creative** | Design judgement, interviewing (grilling), invention, tone, consistency with the canon. Quality matters more than price. | Claude Sonnet or similar |
| **Coding** | Mechanical or schema-driven work: file moves, format conversion, validation, scripts, YAML, reading specs and code. | A cheaper coding model |
| **Mixed** | Creative first, then mechanical write-up. Interview with a creative model, then hand the recorded decisions to a coding model. | Both, in two passes |

- Never use a coding model to **decide** canon. It records decisions the user has already made.
- In a Mixed step, hand bulk formatting (indexes, repeated notes from a table, `engine` blocks, link
  and lint repair) to a coding model once the decisions are fixed.
- Whatever does mechanical work, **run `python3 tools/lint.py` afterwards** (the worldkit's
  `meta/conventions/conventions.md` §16). A generator bug can scramble notes silently; the linter catches it.

### 0.4 The first moves in this repository

1. **Run the initialiser** (or do its four edits by hand): `./init-world.sh`. It asks for the world's
   name, title, id and site slug, rewrites `world.config.yaml`, drops `template: true`, removes
   `example-world/`, and re-initialises git.
2. **Read `AGENTS.md`**, then the four notes in `principles/`.
3. **Start at Step 0b.** Do not write lore before it: Step 0b is what makes the lore answerable.
4. **Keep the tooling current:** `tools/sync-tooling.sh v1.0.x` fetches a kit tag, replaces `tools/`,
   `meta/conventions/` and `meta/templates/`, rewrites `TOOLING_VERSION`, and re-syncs the `AGENTS.md`
   protocol region. It never touches `tools/local/`, and it excludes the site pages the world owns.
   One command, one commit; the diff *is* the upgrade. Then run `tools/verify-world.sh`.

---

## 1. Status tracker

**Update at the end of every session.** Status: `Not started` / `In progress` / `Done` / `Revisit`.

| # | Step | Model | Status | Produces | Depends on |
|---|---|---|---|---|---|
| 0a | Conventions and note templates | — | Done (the kit's) | the kit's `meta/conventions/conventions.md`, `meta/templates/` | — |
| 0b | Decide what this world is | Creative | Not started | `world.config.yaml`, `principles/pillars.md`, `principles/permanence-rules.md`, `principles/originality-guardrails.md`, `meta/canon-digest.md`, `meta/names.md` | — |
| 0c | Tone | Creative | Not started | `principles/tone.md`, `principles/what-to-expect.md` | 0b |
| 1 | The truth ledger and the history timeline | Creative | Not started | `world/history/`, `meta/timeline.md` | 0b, 0c |
| 1b | The conflicts between the fall and the present | Creative | Not started | `world/history/` era and war notes | 1 |
| 2 | Powers, places and their people | Creative | Not started | `world/places/`, `world/factions/`, `world/npcs/`, the interdependence matrix | 0b, 1 |
| 2a | Pilot one slice through the pipeline | Coding | Not started | a Game Ready Repository slice, `meta/pilot-findings.md` | 2 |
| 2b | Mechanics gap register | Coding | Not started | `meta/mechanics-gap-register.md` | 2a |
| 2c | Platform request hand-off | Mixed | Not started | the requests and their recorded answers | 2b |
| 2d | The lore and disclosure model | Mixed | Not started | `disclosure:` on every note, `tools/disclosure.py` green | 2b |
| 2e | Retire `visibility` (only a world older than the model has it) | Coding | Done (nothing to do) | — | 2d |
| 3 | The gods, or whatever the world worships | Creative | Not started | `world/gods/` | 0b |
| 4 | A region where the premise has already won | Creative | Not started | a second region, in full | 0b, 3 |
| 5 | Peoples' cultures | Creative | Not started | `world/peoples/` | 0b |
| 6 | The world's engine of change, in practice | Creative | Not started | the world's magic or technology notes | 3, 5 |
| 7 | Relics and objects of power | Creative | Not started | `world/items-materials/`, `world/relics/` | 0b, 6 |
| 8 | The antagonist, in detail | Creative | Not started | `world/factions/`, the world's cosmology notes | 0b, 3 |
| 9 | Daily life | Creative | Not started | `world/society/`, the ITEM notes the economy runs on | 2, 5 |
| 10 | Ecology and the bestiary | Mixed | Not started | `world/creatures/`, the ecology note | 8 |
| 11 | The rest of the world | Mixed | Not started | the other continents or regions, map-ready | 0b, 4, 8 |
| 12 | The plot web in motion | Creative | Not started | thread cards in `world/plot-web/` | 2, 3, 8, 12a |
| 12a | Pilot the thread pattern on one thread | Mixed | Not started | one complete thread card, `campaigns/<id>/`, the simulator's scenarios | 2a, 2b |
| 13 | Maps | Mixed | Not started | `maps/`, `tools/local/make_atlas.py` | 0b, 11 |
| 14 | The transformer pipeline | Coding | Not started (the kit's) | the Game Ready Repository, generated | 2a, 2b, 2d, 12a |
| 14a | The lore and disclosure eval set | Mixed | Not started | `tools/evals/` | 2d, 14 |
| 15 | Progressive engine conversion, per campaign | Mixed | Not started | `engine-ready` notes; the Game Ready Repository | 14 |
| 16 | The public codex site | Mixed | Not started | `tools/site_export.py`, `site/`, `meta/site.md` | 2d (can run beside 14) |

Steps can be done in any order where `Depends on` allows. The suggested order is the table's, top to
bottom. Every note from Step 2 on follows the kit's `meta/conventions/conventions.md` and the templates from
Step 0a.

---

## 2. The steps

Each step lists **Goal, Read first, Produce, Done when.** The worked example is `example-world/`
until you have notes of your own: it is a small, complete world (a campaign, its thread, its modules,
its scenarios, its engine blocks) and it passes the same checks yours will.

---

### Step 0a: Conventions and note templates

- **Goal:** none. The worldkit ships the rules and a template for every note type, and this vault
  already has them (`meta/conventions/conventions.md`, `meta/templates/`).
- **Read first:** the kit's `meta/conventions/conventions.md` — §3 (layout), §5 (ids and filenames), §6
  (frontmatter), §7 (disclosure), §9 (note bodies), §16 (the linter).
- **Produce:** nothing. A world never edits `meta/templates/` (the sync deletes it) and never edits
  the kit's rules: if a rule is wrong for your world, write your version in
  `meta/world-conventions.md`, and if the *engine* cannot express something, log it in Step 2b.
- **Done when:** you can write a valid note of any kind by copying its template.

---

### Step 0b: Decide what this world is

- **Goal:** answer the questions the whole canon depends on, before any lore is written: what the
  world is *for*, what is scarce, who holds power, what is permanently broken, what it is not.
- **Read first:** `principles/_index.md` and the four notes it lists; `world.config.yaml`; the
  kit's `meta/conventions/campaign-authoring-guide.md` (how to run the session); `example-world/world.config.yaml`
  for a filled-in config.
- **Method:** grilling rounds with recommended answers (the kit's `meta/conventions/agent-protocol.md`).
  Record the answers in `principles/`, not in this file.
- **Produce:** a filled `world.config.yaml` (id, title, slug, tagline, description, author, licence,
  spelling, feature switches); `principles/pillars.md` and `principles/permanence-rules.md` `agreed`;
  `principles/originality-guardrails.md` (the absences: what this world must never contain);
  `meta/canon-digest.md` as a skeleton; `meta/names.md` started.
- **Done when:** a stranger reads `principles/pillars.md` and can say what the world is for and what players do
  in it; `python3 tools/lint.py` is clean apart from the `REPLACE` placeholders you mean to keep.
- **Watch for:** a world with no absence list is a world with no flavour. Write down what it is *not*.

---

### Step 0c: Tone

- **Goal:** make tone a rule rather than a vibe: what grim dark (or whatever this world's dial is)
  means *here*, what horror it runs on, what it never shows, and what it asks of players.
- **Read first:** `principles/pillars.md`, `principles/permanence-rules.md`, `principles/originality-guardrails.md`.
- **Produce:** `principles/tone.md` — with a short test a session can apply to new material, the
  lines and veils, and the world's content descriptors (the engine's closed vocabulary; which of
  them apply is the world's decision, and they go in `world.config.yaml` under `site.content_descriptors`);
  `principles/what-to-expect.md`, the spoiler-free note a player may read.
- **Done when:** a fresh session can judge a new idea against the tone without asking, and the user
  confirms shared understanding.

---

### Step 1: The truth ledger and the history timeline

- **Goal:** for every major event, record the **official story**, the **popular myth**, the **rival
  versions** and the **real truth**, and place them on a dated timeline. This is the step that makes
  "layered secrets" mechanical: the same event, known differently by different people.
- **Read first:** the kit's `meta/conventions/conventions.md` §7 (audience and disclosure); `principles/pillars.md`;
  `meta/timeline.md`; `example-world/meta/timeline.md` (the demo world's dated events).
- **Context to carry:** decide the **era scale** and the anchors (the world's `T0`, the present, the
  big gaps). Decide which events need a note; most do not — one per event that somebody *lies about*.
- **Questions to grill:** which events need a ledger row; what each people, place and faction
  believes about each event; who knows the truth (nobody, one person, one order); which myths are
  accidentally close to the truth; the 8–12 named figures of the age, and what really happened to them.
- **Produce:** one note per event (kind `HISTORY_EVENT`, `hist_` ids) in `world/history/`, each with
  its official/myth/rival/truth sections and its `_known_by_groups`; `world/history/timeline.md`,
  dated and linked; the era notes the world needs; the named figures.
- **Done when:** every event on the timeline has a note, the "who knows what" is written down, and
  `python3 tools/disclosure.py --check` reports nothing unreviewed.

---

### Step 1b: The conflicts between the fall and the present

- **Goal:** fill the gap between the world's founding catastrophe and today with **conflict that
  explains something**, and fix the scale of conflict the world can actually support.
- **Read first:** Step 1's notes, especially the timeline and the era notes; the world's population
  and settlement notes.
- **Context to carry:** **the scale cap is arithmetic, not taste.** Work out what the region's
  population, food and roads can actually move — how many people can march, how far, for how long —
  and let that bound every war. Writing a war the world cannot feed is the most common way a
  low-technology setting stops being believable.
- **Questions to grill:** how many conflicts; what each one changed that is still true today; whether
  anything is still unresolved now; which one (if any) the world's antagonist steered, and which are
  simply people; the trace each leaves (a proverb, a ruin, a treaty clause, a grudge, a hook).
- **Produce:** one note per conflict plus the era notes; updates to the timeline, the settlements and
  the factions it explains.
- **Done when:** every named conflict explains a present-day fact, sits inside the scale cap, and
  leaves a trace a player can find.

---

### Step 2: Powers, places and their people

- **Goal:** profile every power centre in the starting region so a GM can run it tomorrow.
- **Read first:** the Steps 1 and 1b notes; the world's ecology and materials notes if they exist;
  `example-world/world/places/dustport.md`, `example-world/world/factions/the-creditors-clerks.md`,
  `example-world/world/npcs/idra-vance.md` (the demo world's shapes, including engine blocks).
- **Questions to grill, per place:** who rules and how succession works; population and how it is
  fed; law and punishment; what it needs from each neighbour and what it gives; its secret; its
  enemies and debts; three to five named NPCs; three hooks; what it looks, sounds and smells like.
- **Produce:** one note per place (kind `SETTLEMENT`, `PLACE` or `REGION`), faction and NPC, from the
  templates; an **interdependence matrix** in `world/factions/` (who needs what from whom — every
  world built this way has no self-sufficient power); each key NPC at least one **Want** with a
  deadline fallback; the world's flag register (`world/flags.md`) started with the flags you declare.
- **Context to carry:** use the engine's **closed relationship kinds** (`CONTROLS`, `SECRETLY_SERVES`,
  `OWES`, `MEMBER_OF`, ...) so the links convert; give each knowledge-holding faction **named
  representatives at each tier** (`common`, `select`, `inner`) or its group knowledge cannot resolve.
- **Done when:** every place has a ruler, a secret, a need, an enemy and three hooks; the matrix has
  no self-sufficient row; and `python3 tools/lint.py` passes. Engine blocks may stay `engine-example`
  until Step 2a.

---

### Step 2a: Pilot one slice through the pipeline

- **Goal:** prove the codex-to-engine path on one small slice and find the gaps cheaply, before
  converting more.
- **Read first:** the kit's `meta/conventions/conventions.md` §9–§11 (engine blocks, kinds, ids); the
  platform's Design 23 and `packages/authored-content` at `$MYTHICAL_FORGE_ROOT`; `example-world/campaigns/ferryman-demo/`.
- **Context to carry:** `MYTHICAL_FORGE_ROOT` has no default. The tools fail loudly and name it if it
  is unset — that is deliberate, so nobody silently builds against the wrong platform checkout.
- **Tasks:** choose a slice of a dozen or so entities (a place, its routes, two or three NPCs, their
  Wants, a handful of Facts, a few Relationships, one World Event, the flags they need); write the
  engine blocks; run the pipeline (`tools/transform.mjs`, then `tools/validate-world.mjs`, or the
  world's own `tools/verify-world.sh`); record every friction point.
- **Produce:** a validating slice in the Game Ready Repository (a separate, generated repository),
  and `meta/pilot-findings.md` — what worked, what broke, and which conventions need to change.
- **Done when:** every entity in the slice validates with no schema errors, and the findings are
  recorded and fed back into the world's notes and the kit.

---

### Step 2b: Mechanics gap register

- **Goal:** list every mechanic the world needs and classify whether the engine can express it, so
  you stop designing things it cannot run. **Design within what the engine can run.**
- **Read first:** the kit's `meta/conventions/engine-capability-register.md` (the catalogue of what exists),
  `meta/mechanics-gap-register.md` (this world's rows — start it here), the world's rule-heavy notes,
  `meta/pilot-findings.md`.
- **Context to carry:** the engine is **closed over the SRD**. It cannot author new spells, feats,
  classes or item properties. Flags, Facts, Effects, World Events and `authority` levels are what
  exist.
- **Classes:** **A** expressible with the current vocabulary; **B** needs a closed-vocabulary
  extension (a platform release); **C** needs rules-engine support; **D** reshape or drop it in lore.
- **Produce:** `meta/mechanics-gap-register.md` with one row per mechanic, and the load-bearing ones
  written up as platform requests.
- **Done when:** every mechanic is classified, and each B or C item has either a written request or a
  lore change.

---

### Step 2c: Platform request hand-off

- **Goal:** get the load-bearing requests in front of the platform repository, and record its answers
  so Steps 14 and 15 know what can be converted.
- **Read first:** `meta/mechanics-gap-register.md`; the platform's contribution rules at
  `$MYTHICAL_FORGE_ROOT` (find out whether it takes issues, specs or pull requests **before** writing).
- **Context to carry:** the platform is a separate repository. This step is **delivery and response**,
  not design: the register is the source, this step carries it.
- **Tasks:** deliver the requests in the form the platform accepts; record each accept, reject or
  defer **with a date** in the register; re-classify anything whose class changed; disagree explicitly
  rather than leaving an item ambiguous.
- **Produce:** the register updated with answers, and any spec text the platform asked for.
- **Done when:** every request has a recorded answer, and no converted note depends on an
  unclassified gap.

---

### Step 2d: The lore and disclosure model

- **Goal:** settle how the codex's knowledge reaches the agents, the narrator and the player: who **in
  the world** could know a thing, and **whether and how** the narrator may disclose it.
- **Read first:** the kit's `meta/conventions/conventions.md` §7 (the model, in full) and §9.5; the worldkit's
  `meta/conventions/campaign-authoring-guide.md`; `meta/mechanics-gap-register.md`.
- **Context to carry:** **audience** (who knows it, by group and tier) and **disclosure** (how the
  narrator may release it) are **separate axes**. The classes are `open`, `earned` and `sealed`;
  unmarked content fails closed as `earned`; a note's Summary and Details state only open content,
  and hidden truth moves under `## Secrets` or `## Keystone secrets`. Secrets are **disclosure, not
  deletion**: a secret is written in full and given a reveal path.
- **Method:** propose a default per note kind and have the user confirm before anything moves. Expect
  to find hidden truth in Summaries and Details — that is the point of the pass.
- **Produce:** `disclosure:` in every note's frontmatter and a `**Disclosure:**` line where the class
  is not the default; `python3 tools/disclosure.py --check` reporting nothing unreviewed; a short
  `## Folklore` line where an earned note needs an open face.
- **Done when:** the classification is complete, the user has confirmed the model, and lint passes.

---

### Step 2e: Retire `visibility` (a world older than the model only)

- **Goal:** nothing, in a new world. Older worlds carried a `visibility` field built for a printed
  player primer; `disclosure` replaced it, because a site needs per-*section* granularity.
- **Read first:** the kit's `meta/conventions/site.md` §2 and the kit's `meta/conventions/conventions.md` §6–§7.
- **Produce:** nothing here. A world that still carries the field deletes the line from every note and
  from the templates, and the linter's `REQUIRED` list shrinks by one.
- **Done when:** the vault mentions the field only inside fenced `engine` blocks, where it is the
  engine's own vocabulary.

---

### Step 3: The gods, or whatever the world worships

- **Goal:** name the powers and give each a cult, a doctrine and a place in the plot web.
- **Read first:** `world/gods/_index.md`; the world's cosmology and magic notes from Step 1.
- **Questions to grill, per power:** names and epithets; what it is and where it came from; what it
  *wants now*; the form of worship, the clergy and the taboos; its standing in each place (elite,
  tolerated, shunned); what its favour costs; its relics and holy sites; its festivals and sayings.
- **Produce:** one note per power (kind `GOD`), a matrix of cult standing per place, and a site note
  for any shrine that becomes a place a party can visit.
- **Done when:** every power has a name, a want, a cult and a hook, and the matrix has no blanks for
  the places in your starting region.

---

### Step 4: A region where the premise has already won

- **Goal:** build one region where the world's central threat has *already* succeeded, as a preview of
  where the starting region is heading. It is the cheapest way to make a threat real: the players can
  go and look at the ending.
- **Read first:** the Step 1 and Step 3 notes; the world's geography.
- **Questions to grill:** government and ruling class; how the threat's agents are placed and hidden;
  what ordinary people believe and how they live; why it *looks* prosperous and what that costs; who
  resists and how; what it exports and wants; what a visitor would see; the truth at its centre.
- **Produce:** the region note plus its settlements, factions and NPCs, with coordinates for Step 13.
- **Done when:** a GM could run a voyage there, and the reveal lands.
- **Note:** a world whose antagonist works differently may use this slot for whatever second region it
  needs. Keep the number.

---

### Step 5: Peoples' cultures

- **Goal:** a culture sheet per people, so a player can play one and a GM can voice one.
- **Read first:** the world's history and place notes; `example-world/world/peoples/humans.md`.
- **Questions to grill, per people:** lifespan and life stages; family and social structure; naming
  conventions and ten sample names; customs, taboos, dress and food; religion and attitude to the
  gods; attitude to each other people; languages; sayings and slang; what they carry; regional
  variations; the character options they give players.
- **Produce:** one note per people (kind `RACE`), a peoples matrix (who thinks what of whom) and a
  languages note.
- **Done when:** each people has naming rules, ten sample names, three customs and three taboos.

---

### Step 6: The world's engine of change, in practice

- **Goal:** describe how magic (or technology, or whatever moves this world) actually looks: how it is
  learned, what it costs, how it scars, who polices it, who is blamed.
- **Read first:** the world's magic notes; `meta/mechanics-gap-register.md` — **check every cost
  against it**, because the engine cannot author a new mechanic.
- **Questions to grill, per tradition:** how it is learned (schools, apprenticeships, inheritance,
  bargains); its signature costs (body, memory, years, sleep, luck); how it scars the land; the public
  view of it; who hunts its practitioners; the typical archetypes; the magical professions.
- **Produce:** one note per tradition, the vocabulary the world uses for a place's magical character
  (if it has one), and a standard line each region note carries.
- **Done when:** each tradition has a cost table, a public image, a danger, a sample practitioner and a
  link into the plot web.

---

### Step 7: Relics and objects of power

- **Goal:** what the old world left behind, what it does, what it costs and who wants it.
- **Read first:** the world's history and materials notes; `meta/mechanics-gap-register.md`.
- **Context to carry:** **relics are an SRD item plus narrative.** No new mechanical properties. Every
  relic records its **SRD base** in the standard body line (the kit's `meta/conventions/conventions.md` §9.6);
  if the library has no match, write `[OPEN]` with the nearest equivalent in words and keep
  `engine: false`.
- **Questions to grill:** the categories and grades; each grade's cost or side effect; named legendary
  objects and where they are; the black market and the licensing that surrounds salvage; what each
  faction wants buried.
- **Produce:** `world/items-materials/` (categories, trade goods and named relics) and the market note.
- **Done when:** every category has a source, a cost, a price, a faction that wants it and a recorded
  SRD base.

---

### Step 8: The antagonist, in detail

- **Goal:** make the world's central threat concrete enough to run as an antagonist *and* as a place.
- **Read first:** the Steps 1, 3 and 4 notes; the world's cosmology.
- **Context to carry:** decide how it works **mechanically in fiction** (how it spreads, what it needs,
  what it wants, what hurts it), and how it is *not* monolithic — a single-minded antagonist is a
  monster, not a plot.
- **Questions to grill:** how a victim or servant is made, and how one behaves; how its agents
  coordinate; its language and aesthetic; its factions and rivalries; its places and layers; its
  weaknesses, and why they are not a clean fix; what happens if it wins.
- **Produce:** the antagonist faction note, its cosmology notes, and notes for its agents, its places
  and its factions.
- **Done when:** a GM can describe an agent, a stronghold, each stage of its spread and an encounter
  with it, and knows why a victory only shifts the balance.

---

### Step 9: Daily life

- **Goal:** the texture of ordinary life: what people eat, drink, earn, fear and pay.
- **Read first:** the world's place, society and materials notes; `meta/mechanics-gap-register.md`;
  the kit's `meta/conventions/conventions.md` (the calendar maps onto the engine's day counter).
- **Questions to grill:** food and agriculture; water and fuel (scarcity is where the plots are);
  housing and clothing; disease and medicine; law and punishment; the calendar and its holidays;
  travel, inns and caravans; entertainment; money in practice (a price table); literacy; superstition.
- **Produce:** the daily-life, prices and calendar notes, plus an ITEM note for **every good the price
  table names** — starting with whatever the economy runs on — each with its SRD base or `[OPEN]`.
- **Done when:** a GM can price a meal, a bed, a night's shelter and a pack animal, name three local
  customs per place, and find a note for every good the price table names.

---

### Step 10: Ecology and the bestiary

- **Goal:** the living world and the monsters, each one a **consequence** of the history rather than a
  monster of the week.
- **Read first:** the world's geography, cosmology and antagonist notes; `world/creatures/_index.md`
  (**write its rules here first — the `_index` is the authority**); the worldkit's
  `meta/conventions/conventions.md` §9.6; the project prompt `.pi/prompts/new-creature.md`.
- **Context to carry:** every creature has **one cause** from the world's own list, and a **tell** — how
  a traveller recognises it. Keep the mix mundane-first; the strange ones only where the history puts
  them. Every creature records its **SRD base** or `[OPEN]`.
- **Produce:** one note per creature (kind `CREATURE`), the ecology note (per biome: flora, fauna, three
  monsters, a hazard), and the creatures-by-cause index.
- **Done when:** each biome in your starting region has flora, fauna, three monsters and a hazard, and
  every creature has a recorded SRD base.

---

### Step 11: The rest of the world

- **Goal:** map-ready breakdowns of the regions outside the starting area.
- **Read first:** the world's geography, continents and history notes; `maps/`.
- **Questions to grill, per continent or region:** the macro geography with coordinates; climate
  zones; five to ten key sites; ruins by origin; ley-line or resource remnants; who still lives there;
  what happened to it in the fall; the antagonist's presence and its stage; how a party gets there.
- **Produce:** one note per continent or region, with a coordinate table, and coordinate data in
  `maps/atlas-features.yaml`.
- **Done when:** each region has a coordinate table and can be drawn.

---

### Step 12: The plot web in motion

- **Goal:** make each thread **move without the player and survive what the player does**, in a world
  where play diverges. Not a calendar: a **state graph** per thread.
- **Read first:** the kit's `meta/conventions/campaign-authoring-guide.md` (**the how-to; follow it**) and
  `meta/conventions/thread-pattern.md` §6 (**the resolution classes**: Resolvable, Managed, Ratchet) and §10;
  `meta/world-events-design.md`; Step 12a's pilot card and findings; `world/flags.md`.
- **Context to carry:** three layers — the **World** owns pressure (threads, Wants), **Campaigns** own
  purpose (arming, stage, outcomes), **Modules** own choices (Quests apply the thread's contracts).
  **Flags are the API between them.** No shared calendar: a thread is armed by a Campaign's start
  state, never by a date.
- **Procedure, per cluster of threads:** one grilling round per thread for its actors and successors,
  its stages and forks, its pace, its couplings to other threads, its resolution class and its quest
  contracts. Then write the card, run `tools/thread-check.mjs`, and add an idle scenario plus one
  scenario per fork.
- **Produce:** one card per thread in `world/plot-web/`; an interaction grid compiled from the cards'
  interface blocks; every shared flag declared in `world/flags.md`; an idle scenario per thread.
- **Done when:** every card's interface passes `thread-check`, an idle run reaches its floor or idle
  terminal, each fork has a scenario, and a GM could run the world a year forward without the party.

---

### Step 12a: Pilot the thread pattern on one thread

- **Goal:** prove the pattern end to end on the **hardest** thread first, before writing the rest.
- **Read first:** `example-world/world/plot-web/the-ferrymans-debt.md` and
  `example-world/campaigns/ferryman-demo/` (a complete worked thread, its campaign, two modules, an
  overlay and six scenarios, all passing).
- **Produce:** one thread card written as a state graph; a pilot campaign under `campaigns/<id>/`; the
  scenarios that exercise every event, Want deadline and Quest; and the scripts to run them
  (`tools/thread-check.mjs`, `tools/simulate-world.mjs` — the kit's, vendored).
- **Done when:** the pilot thread's scenarios all pass, and the design errors they expose are fixed and
  recorded — **expect several**; that is what a pilot is for.

---

### Step 13: Maps

- **Goal:** drawable and shareable maps, for players and for the GM.
- **Read first:** the kit's `meta/conventions/atlas.md`; the world's coordinate data and `maps/`.
- **Context to carry:** keep a **GM version** and a **player version**. Decide the frame (what
  coordinates mean), the plate ladder (world → region → site) and the finish (a generated skeleton the
  world's own script renders, hand-finished at the end).
- **Tasks:** keep the feature register in authored YAML; render it with `tools/atlas_tables.py` and
  `tools/local/make_atlas.py`; re-derive it from the notes with the `/atlas-refresh` prompt; diff it
  against HEAD with `tools/atlas_diff.py` before re-rendering, so a note edit that moves a city is
  visible.
- **Produce:** the sheets in `maps/svg/`, the register note, and the world's own atlas script in
  `tools/local/`.
- **Done when:** the user confirms the map matches the geography, and the checks in the worldkit's
  `meta/conventions/atlas.md` pass before anything is hand-finished.

---

### Step 14: The transformer pipeline

- **Goal:** the deterministic path from the codex to the Game Ready Repository, reliably enough to run
  in CI.
- **Read first:** the kit's `meta/conventions/conventions.md` §9–§11; `meta/pilot-findings.md`;
  `meta/mechanics-gap-register.md`; the platform's Design 23 at `$MYTHICAL_FORGE_ROOT`.
- **Context to carry:** **the kit owns this.** `tools/transform.mjs`, `tools/validate-world.mjs`,
  `tools/thread-check.mjs` and `tools/simulate-world.mjs` are vendored, not written here; this step is
  the world supplying what they read (notes, config, flags, scenarios) and proving the result. A world
  that *edits* a vendored tool loses the edit at the next sync: put world-specific generation in
  `tools/local/` instead.
- **Context to carry (the rules):** the transformer is **deterministic — no LLM**. It reads only notes
  with `engine: true`, extracts their `engine` blocks, assembles the engine's layout, never writes
  `author_id` or `world_id`, and never writes back to the vault. The Game Ready Repository is separate
  and generated; **never hand-edit it.**
- **Produce:** the generated Game Ready Repository, and `tools/verify-world.sh` green end to end
  (lint → disclosure → transform → validate → thread-check → voice → every scenario).
- **Done when:** one command regenerates the Game Ready Repository from the codex and validates it
  with no manual edits.

---

### Step 14a: The lore and disclosure eval set

- **Goal:** prove, with an LLM in the loop, that the agents and the narrator respect audience and
  disclosure. The scenario simulator cannot: it tests the deterministic web, never language.
- **Read first:** the Step 2d output; the kit's `meta/conventions/campaign-authoring-guide.md`;
  `tools/simulate-world.mjs` (what scenarios already cover).
- **Case categories:** leakage (a direct question about a `sealed` truth; an indirect one; a
  prompt-injection attempt; pressure on an NPC for a secret outside its audience); under-knowledge;
  over-knowledge; belief fidelity (an NPC states the official story as *true*, not as rumour); canon
  drift; earned disclosure before and after a reveal; ledger fidelity (what has the player been told?);
  forgery ("the innkeeper already told me"); constraints (a `forbidden` method).
- **Produce:** one YAML file per case in `tools/evals/`, plus the runner contract for the platform.
- **Done when:** every category has cases from your own canon, and a run against the engine passes or
  its failures are filed as platform issues.

---

### Step 15: Progressive engine conversion, per campaign

- **Goal:** convert only the lore a campaign uses, and design that campaign's modules.
- **Read first:** the kit's `meta/conventions/campaign-authoring-guide.md` (the how-to); `world/flags.md`;
  `meta/mechanics-gap-register.md` (what the engine can express); the kit's `meta/conventions/thread-pattern.md` §8.
- **Context to carry:** campaigns are separate design sessions. Unconverted lore stays prose. A
  converted note's `status` moves to `engine-ready`.
- **Tasks, per campaign:** arm the threads it uses; set the stage each begins at; write Modules whose
  Quests apply the thread contracts; define its outcomes as flags; write its scenarios and run them;
  add the campaign, overlay and module notes under `campaigns/<id>/`.
- **Produce:** `campaigns/<id>/...` and the regenerated Game Ready Repository.
- **Done when:** the campaign validates and its scripted playthrough passes.

---

### Step 16: The public codex site

- **Goal:** publish the player-facing view of the codex — **open content only, no GM material** — as a
  static site that rebuilds whenever the lore does.
- **Read first:** the kit's `meta/conventions/site.md` (the whole document: rules, page anatomy, deploy);
  `meta/site.md` (this world's pages, navigation and visual direction — **write it in this step**);
  `world.config.yaml` (`site:` — url, doorways, sections, blurbs, the search placeholder, the content
  descriptors); `tools/disclosure.py`, `tools/lint.py`; `site/image-prompts/`.
- **Context to carry:** `disclosure` is the only publish axis, and the exporter **ports the
  classification** — it never re-derives it, so a typo cannot publish a secret. The codex repository
  stays private forever; only `site/dist` is published. **The site never authors canon**: the only
  hand-written prose is the three pages a world owns (`site/src/pages/index.astro`, `about.astro`,
  `follow.astro`). Those three are the world's files: the sync never overwrites them.
- **Tasks, in order:**
  1. Fill the `site:` section and write `meta/site.md`; set the world's own copy on the three pages.
  2. **Export:** `python3 tools/site_export.py` (stdlib only) — it applies every redaction rule in the
     kit's `meta/conventions/site.md` §2.2 and emits `content/`, `audit/latest.json`, `changelog.json`,
     `redirects.json` and `navigation.json`.
  3. **Build:** `npm --prefix site run build`, then `python3 tools/site_link_check.py` — the build fails
     on any internal link to a file that does not exist.
  4. **Read the audit** (`site/audit/latest.json`) before deploying: keyword hits and dangling
     references mean a secret or a process term leaked into the open face. Fix at source, then export
     again.
  5. **Publish:** the infrastructure in `site/infra/` (private bucket + CDN, OIDC deploy role) and the
     workflow in `.github/workflows/site.yml`. The worldkit's `site/infra/README.md` is the procedure;
     the world's own values go in `site/infra/state.json` and a note in `meta/`.
  6. **Later:** the art (one plate per image, `site/image-prompts/`), the glossary, the map, the people.
- **Produce:** `site/`, the audit, `meta/site.md`, and a live URL.
- **Done when:** every published word comes from an `open` section, the audit has been read and is
  clean, and a session's refresh step reproduces the live site from a clean checkout.

---

## 3. Beyond the roadmap

Separate sessions, once the steps above can support them:

- **Campaign design sessions**, one per campaign, drawing on `campaigns/_seeds/` and the plot web.
- **Rules and character options.**
- **Adventure and dungeon design.**
- **A player-facing handout** — now Step 16; the site supersedes a printed primer.

---

## 4. Known open items

Carry these into the step that settles them. Also keep `meta/open-questions.md` current; it is the
vault's own list, and this section is the roadmap's.

- `REPLACE` — nothing yet. Every open item this world opens should be added here with the step that
  will close it.

---

## 5. Changelog of this file

| Date | Change |
|---|---|
| — | Create this world from the template. |

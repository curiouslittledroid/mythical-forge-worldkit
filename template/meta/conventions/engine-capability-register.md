# Engine Capability Register

**What this is.** Every mechanic a world wants, classified against what the engine can actually
express — and the **single home for the platform requests**. It is the kit's, because it is a
statement about the engine: what the schemas and vocabularies in
`@curiouslittledroid/authored-content` (or a checkout named by `$MYTHICAL_FORGE_ROOT`) and the SRD data in `packages/shared-data` can do.
Each world keeps its **own** register (`meta/mechanics-gap-register.md`) listing the gaps *it* hits,
with its rows numbered `M1…`, and refers to the requests by id from here.

A world's register is the map; this is the territory. **When a platform release lands, it lands
here** — one edit, one place, and every world sees it.

## How to read this

| Class | Meaning |
|---|---|
| **A** | Expressible with the current vocabulary today. |
| **B** | Needs a closed-vocabulary extension (a platform release). |
| **C** | Needs rules-engine or rules-variant support. |
| **D** | Reshape or drop the mechanic — the world's business, not the engine's. |

**Load-bearing** means a world cannot convert the affected lore without it. A request is also
load-bearing when a world cannot be *played* as designed without it, even though conversion is not
blocked.

Every other mechanic in a world's register has a recorded disposition below: a **CP-** pattern in
force, a **PF-** non-blocking request, a **BD-** item closed as by design, or a **DT-** item deferred
with a named trigger.

## Platform requests (load-bearing)

Written so the platform repository can ingest them. Each is one request.

### PR-1
— `author-cli validate`
- **Class B (infra). Driver:** a world's transformer had to import the package `dist` directly; Design 23 §4.3 and Step 14 assume a CLI.
- **Build:** `author-cli validate <game-ready-repo>` doing offline schema validation plus bundle checks (reference integrity, reveal paths, flag declarations, derived-field rejection).
- **Acceptance:** one command, non-zero exit on error, machine-readable output; runs in CI.

### PR-2
— Cadenced and recurring World Events
- **Class B. Driver:** M19. Dustport's gate opens about three times a month; seed-site stages and the Whisper repeat.
- **Build:** a `repeat`/`cadence` field on `WORLD_EVENT`, or a documented repeatable form with a declared `fire_key`.
- **Acceptance:** an event may fire N times or on a cadence, each firing applied exactly once per `(sandbox_id, source_id, fire_key)` (Design 04.3 idempotency idiom).

### PR-3
— First-class ZONE / REGION entity
- **Codex status (corrected 2026-11-14):** the spec side is **accepted** (S47, S65, ADR-0009) but **not implemented**: `packages/authored-content` has no `ZONE` in `ID_PREFIX` or `BASE_ENTITY_SCHEMAS`, so a `zone_` entity cannot be emitted yet. The earlier claim that "all 15 referenced `zone_` ids already have region notes, so no content work" was **wrong**: the atlas names 30 `zone_` ids, 12 of which have no note, and one region note's id does not match the atlas's ([[game-ready-pipeline]] §10).
- **Class B. Driver:** M3. `zone_id` is already the lazy-hydration unit but has no entity; dangling `zone_` references remain in engine blocks and in `maps/atlas-features.yaml`.
- **Build:** a `zone_` entity kind the validator resolves, with an optional magic/leyline descriptor, and a Condition to test zone membership (for example `in_zone`).
- **Acceptance:** every `zone_id` in the repository resolves; a Condition can gate content on a zone.

### PR-4
— SRD library: id convention, coverage and structured material properties
- **Class B. Driver:** M8 and M20. `SrdRef` expects `srd_…` while the library ships `monster_…`/`item_…`/`spell_…`/`feat_…`/`skill_…`; the library is a 21-monster, 66-item sample; damage reduction is free text.
- **Build:** (a) one documented id form for SRD references, honoured by both the package and `shared-data`; (b) structured `damage_reduction` / `vulnerabilities` by material on monsters; (c) enough coverage to run the world's creatures and relics; **(d) a structured class/power table so `levels:` keys resolve** (there is no class source of truth today — the only class names in `shared-data` are the spell level keys `bard, cleric, druid, paladin, ranger, sorcerer, wizard`; there is no Warlock, and no psionics, M21–M22).
- **Acceptance:** a creature with an iron weakness and one with a silver weakness validate and resolve; no id-form mismatch between package and library; every authored `levels:` class key resolves against a shipped class table.
- **Step 10 evidence:** of 34 creatures, 12 record a library key (wolf, dire rat, spider swarm, owlbear, ogre, troll, dryad, shadow, skeleton, zombie, ghoul, young black dragon, several as proxy only) and **22 are `[OPEN] (PR-4)`**, each with a nearest SRD 3.5 monster in words. A fey-iron weakness (borderhound, M8) and a dragon above *young* have no library base.

### PR-5
— Item transfer, consumption and a generic trade good
- **Class B. Driver:** M10. Water-chits, resonant salt, relics and tribute cannot be handed over, spent or consumed; `grant_reward` is allowed only in Quests and Migrations; `ITEM` requires an SRD base that does not exist for trade goods.
- **Build:** Effects to give, remove and consume an item, a Condition to test ownership and quantity, and a generic trade-good item family (or an author-named item with a documented SRD base).
- **Acceptance:** an event can transfer a chit or a relic to the player, and a Quest milestone can require and consume a good.

### PR-6
— A magic-use hook
- **Class B. Driver:** M2. "Every casting costs the caster and scars the land" is core world identity, but authored content cannot observe a casting.
- **Build:** either a `WILD_MAGIC` judgement tag (engine-recorded from an agent proposal, like the existing four) or a `magic_used` predicate that a World Event can test.
- **Acceptance:** a World Event can fire once heavy casting has occurred in a zone, without an author-invented rule.

### PR-7
— Publish the group-knowledge resolution contract
- **Class B (small). Driver:** Step 2a frictions 5–6 and the two `who-knows` records. `known_by`/`believed_by` accept NPC ids only; the codex resolves group + tier itself; an empty `believed_by` currently invalidates `believed_as`.
- **Build:** either tiered `known_by_groups` in the schema, or a documented resolution contract (ids only) that all transformers implement; fix the empty-belief case.
- **Acceptance:** one documented contract; the package's validator agrees with it.

### PR-8
— Document the derived Relationship id
- **Class B (small). Driver:** the codex omits `id`; the compiler derives one; transformers must derive the same string.
- **Acceptance:** the derivation is specified (or a helper exported), so the codex transformer and the compiler cannot disagree.

### PR-9
— A relative-time Condition (`days_since`)
- **Class B. Driver:** M23, Step 12a. `day_reached` is absolute, so "30 days after stage 2" and "a reprieve, then resume" cannot be written. The data exists: FLAG items record `first_day` and `last_day` (Design 23.2 §7), and events record `occurred_on_day`.
- **Build:** `days_since: { flag: <flag>, toward?: <ref>, days: n }` and `days_since: { event: evt_x, days: n }`, with a watch key on `clock`.
- **Acceptance:** a World Event can fire a fixed number of days after a flag was first set or an event occurred, deterministically. Until it lands, **CP-9** (Want timers) does the job for NPC-driven clocks; environmental clocks cannot be expressed without an NPC anchor.

### PR-10
— Campaign start state, outcomes and succession
- **Class B. Driver:** M23, Step 12a; the owner's requirement that Campaigns chain inside one Sandbox. Design 23 §2 says a Sandbox belongs to exactly one Campaign, and a Campaign has no start state, no end state and no successor.
- **Build:** on `CAMPAIGN`: (a) `start_effects` (an Effect list applied once at `SANDBOX_CREATED`); (b) `outcomes` (named end states, each a Condition); (c) `follows: camp_x` with `requires_outcome` and a `transition` Effect list, so a Sandbox can adopt the next Campaign at a safe point while keeping its character and state (a Campaign Succession; hydrated entities stay frozen, ADR-0002). Update Design 23 §2, §12 and Design 23.4.
- **Acceptance:** a second Campaign can start a Sandbox from the world state the first one left, with no character import (out of scope in §1.1) and no re-firing of earlier events. Until it lands, **CP-10** (a genesis event in the overlay) gives start state, and outcomes are flags.

### PR-11
— Quest outcomes, failure and abandonment
- **Class B. Driver:** M23. A Quest has one linear milestone chain and one `on_complete`; there is no failure, abandonment or branching ending, so "depending on how a quest turns out" cannot be written.
- **Build:** `outcomes: [{ id, when, then }]` evaluated at completion (first match), plus `on_fail` and `on_abandon` Effect lists. Keep `on_complete` as the default outcome.
- **Acceptance:** one Quest can end three ways with different Effects. Until it lands, split the Quest into alternative **Resolution Paths** of one Want, each with its own `on_complete` (the pattern a pilot world invented).

### PR-12
— Want and NPC lifecycle semantics
- **Class B (clarification, plus one Effect). Driver:** M23, Step 12a. Design 23 §5.2 does not say when a Want's `deadline_days` clock starts, whether `urgent_when` only activates or also deactivates, what `fail_want` does to `on_deadline`, or what an NPC's death does to its Wants.
- **Build (clarify in Design 23 §5.2 and Design 03.2):** (a) the clock starts on the first day `urgent_when` holds or the day `activate_want` names the Want; (b) `urgent_when` only activates; (c) `resolve_want` and `fail_want` both prevent `on_deadline`; (d) a dead NPC's own Wants fail; (e) only **urgent** Wants count as Major for the tick (cost, Design 03.2 §2.2).
- **Acceptance:** the simulator's assumptions A-1…A-5 are stated in the spec.

### PR-13
— Quest and Module availability (`available_when`, `expires_when`)
- **Class B. Driver:** M23, Step 12a. There is no way to say a Quest or Module is *moot now*: a world that moves on cannot retire "hide the boy" after the boy is taken.
- **Build:** optional `available_when` and `expires_when` Conditions on `QUEST` and `MODULE` (or on a Campaign `unlocks` entry).
- **Acceptance:** the Module Selector and the Want path hide a Quest whose `available_when` is false. Until it lands, the pilot keeps the gates in `tools/pilot-quest-gates.yaml` and a quest that is no longer available is refused by the simulator.

### PR-14
— A retrievable Lore corpus
- **Codex status:** the codex side is **agreed and done** (Step 2d): every section of `world/` is classified and `python3 tools/disclosure.py --check` is clean. The platform has not yet answered (Step 2c).
- **Class B. Driver:** M24. The engine has no entity for prose lore. An NPC agent receives only its own Wants, Relationships and Facts and a token-capped persona, so a quay-hand knows nothing of the Choir unless a Fact says so; the narrator has no sanctioned source for a player's general questions about the world. Most of the codex stays prose and never reaches runtime ("unconverted lore stays prose", Step 15).
- **Build:** a compiled, chunked **Lore** corpus (a `LORE` entity kind, or a content-addressed document type indexed beside Facts). Each chunk carries `topic` (the note's id), `layer` (`truth`, `official`, `myth` or `rival`, the layers the codex already records), `audience` (groups and tiers, resolved to NPC ids exactly as Fact knowledge is, conventions §9.5; **agreed:** an NPC's default knowledge is the common knowledge of its race and home region plus its groups' tiers, at the layer it believes), `disclosure` (PR-15) and `subjects`. Two retrieval contracts, **enforced in code in the retriever, never in the prompt** (Design 23 §8.3):
  1. **NPC retrieval** returns the chunks whose audience includes the NPC, **at the layer that NPC believes**. A believer of the myth is handed the myth, not the truth. **An NPC's own Wants are always included** (self-audience), even when the NPC will never say them, because they shape its reaction to the player (agreed, Step 2d).
  2. **Narrator retrieval** follows PR-15.
  Chunks are token-capped and delimited as untrusted data (Design 23 §8.2), embedded at publish like authored memory seeds, and versioned like any authored entity (Design 23 §10).
- **Acceptance:** two NPCs asked about the same event answer from different layers according to their group and tier; neither is handed a chunk outside its audience; a chunk edit reaches a Sandbox by the unhydrated/hydrated rules.
- **Amendment requested 2026-11-14 (codex side; PR-14 / Design 24 §2.1).** Two changes, both from measuring the corpus ([[lore-corpus]]):
  1. **Keep the resolved NPC-id audience out of the chunk's content hash.** Design 24 §2.1 makes `audience` an authored field that is "resolved to NPC ids exactly as Fact knowledge is", and Design 23.2 §3.1 makes the object key the hash of its canonical bytes. Together, adding one NPC to one faction re-hashes and re-embeds **every chunk that faction can see**. Requested shape: the chunk carries `audience` as groups and tiers (stable, authored); resolution to NPC ids happens at seed or retrieval time against authored membership. Facts have the same latent issue, but there are a handful of them and there will be ~1,500 chunks.
  2. **Give the chunk a logical id** (`lore_<topic>_<heading>_<nn>`) alongside its content hash, for diffs and review. The hash stays the identity; the logical id is what a human reads in `author-cli diff`.
  3. **Add a zone narrowing step to the NPC retrieval contract** (Design 24 §2.3), as a *widening* filter: candidates are `subjects` ∩ (the scene's zone ∪ its parent zone) ∩ audience, then ranked. Without it the contract is unsatisfiable in practice — audience removes ~10% of the corpus and every NPC is in scope for ~1,390 chunks. Zones are already the lazy-hydration unit (Design 04.1 §3), so the retriever has the scene's zone in hand; the ask is that the contract names it rather than leaving "rank the audience" as the whole instruction.
- **Measured 2026-11-14** (`tools/lore_export.py`): 1,555 chunks, ~116k tokens, and — the finding that matters — **audience is a permission gate, not a selector**: 89% of chunks are `world`-scoped, so every NPC is in scope for ~1,390 of them. Top-k therefore cannot be reached by the audience filter, and the second narrowing axis must be `subjects` (a wikilink-derived subject selects a median of 7 chunks). A4's top-k acceptance criterion should say so explicitly, or it will be met by a filter that removes 10%.

### PR-15
— Disclosure classes and a code-enforced narrator gate
- **Codex status:** the classes, marking and defaults are **agreed and applied** (conventions section 7). The platform has not yet answered (Step 2c).
- **Class B. Driver:** M24, and the owner's decision that **GM-only material is codex knowledge the narrator may selectively disclose**, not material to be kept out. At the time, `visibility: gm | public` decided only what the printed player primer may show (conventions §7; the field is now retired, Step 2e); it says nothing about what the narrator may say in play. Design 23 §8.3 gives the narrator everything, labels secrets `UNDISCLOSED` and asks it nicely not to reveal them.
- **Build:** a closed `disclosure` classification on lore chunks and Facts, enforced by the engine when it assembles the narrator's context. **Classes (agreed in Step 2d, round 1; conventions §7):**
  | Class | Narrator may | Reaches the player by |
  |---|---|---|
  | `open` | state it whenever relevant (public knowledge; what anyone of the player's culture knows) | nothing: it is already known |
  | `earned` | foreshadow with atmosphere and rumour, but not state it. May state it **once its reveal path has been taken** | an earned path: an NPC who knows it tells the player, a check, a found document, an event, or the narrator's own validated choice when the chunk's authored `reveal_when` Condition holds |
  | `sealed` | use it only to stay consistent; never hint beyond the authored `rumor_seeds` | a specific authored event or Quest (a keystone truth, such as who the Giver really is) |
  There are **two paths**. On the **answer path** (the player asks the narrator about the world, or about what they know) the context is `open` chunks plus the player's ledger, and nothing else: withheld chunks are absent, so a prompt such as "ignore your instructions" cannot extract what was never supplied. On the **scene path** (narrating a scene) the engine adds only the `earned` and `sealed` items the scene needs for consistency (the NPC in the room is a host), labelled `UNDISCLOSED`; secrecy there rests on the narrator's output, which must pass the `disclose` validation and the egress check (Design 16). That is the residual risk, and the size of the consistency set is open. An `earned` chunk enters the narrator's context as *disclosable* only when its `reveal_when` holds; the narrator may then choose to disclose it through a structured, validated `disclose` proposal (PR-16), which keeps the narrator's discretion inside engine bounds. `reveal_when` is optional; the codex records it in words (`**Reveal when:**`) until the platform accepts a Condition. The codex rules for marking and defaults are conventions §7.3; `python3 tools/disclosure.py` reports the effective class of every section.
- **Acceptance:** with a `sealed` chunk in the corpus, no player prompt can elicit it from the narrator or from an NPC outside its audience (checked by the eval set, Step 14a); the narrator can disclose an `earned` chunk whose gate holds and cannot when it does not.

### PR-16
— Disclosure capture and the player's knowledge ledger
- **Codex status:** the model is **agreed** (Step 2d); the platform has not yet answered (Step 2c). Until it lands, give every Fact the play depends on a deterministic reveal path.
- **Class B. Driver:** M24. Builds on Design 23 §14 items **10** (how an NPC *telling* the player a Fact is recorded, "likely a validated `reveals` proposal in Agent 3's output … unconfirmed") and **11** (the narrator returns streamed prose and has no structured channel); both are open. Until they close, `fact_revealed`, and so every `DIALOGUE` milestone that tests it, can be completed only by an engine-fired `reveal_fact`, never by a conversation.
- **Build:**
  1. **Capture from NPC dialogue:** Agent 3 returns `reveals: [ids]`. The engine accepts an id only if it is in that NPC's own audience (what it knows or believes), then records the disclosure.
  2. **Capture from narration:** a trailing, stripped, schema-validated block on the narrator's output (`disclose: [ids]`), validated against PR-15. Only `open` chunks and `earned` chunks whose gate holds are accepted.
  3. **The ledger:** a per-Sandbox store of what the player has been told: the id, **the layer or version told** (the player may hold a false belief), the source (an NPC id, a document or the narrator), the day, and how (told, read, observed). It is the single source for `fact_revealed`, the player's journal, and the narrator's answers to "what do I know about X?".
  4. Recording is idempotent per turn on the `request_id`, the same idiom as judgement tags (Design 23 §5.1.1).
- **Out of scope for v1 (agreed, Step 2d):** the player *inferring* a secret without being told; an NPC remembering what the player told it.
- **Acceptance:** a `DIALOGUE` milestone with `when: { fact_revealed: … }` completes after an NPC tells the player in conversation; the ledger shows who said it, on which day, and which version; the narrator answers "what have I learned about X?" from the ledger alone; a retried turn records nothing twice.

## Spec homes (Step 2c hand-off)

The platform is spec-first: new work enters as **spec text**, not as a ticket. The drafts live in `meta/platform-requests/` (excluded from lint as they are not vault notes) and were **delivered to `mythical-forge` on 2026-11-02** (commit `1c70799`): `docs/specs/Design 24 - Lore, Disclosure & the Knowledge Ledger.md`, `docs/design-reviews/Design 24 - Amendments & Roadmap Delta.md` (S42–S72), ADR-0008 and ADR-0009 as `proposed`, and five new `GLOSSARY.md` terms. **Answer: applied 2026-11-02.** The owner approved the package and the amendments were applied to `docs/specs/` in one pass, together with Design 24's approval, ADR-0008 and ADR-0009 accepted, the roadmap delta applied to `docs/tasks/`, and the glossary terms landed. The batch is **S42–S72**; 29 of 31 were applied. **S49 was already present** (Design 07 §2D and Design 03.2 §3.4 both carry it), and **S52 was withdrawn** in favour of S72 (a `magic_used` predicate rather than a judgement tag). See `meta/platform-requests/Amendments & Roadmap Delta.md` §7 for the per-spec record.

| Item | Spec home | Amendment / task |
|---|---|---|
| PR-1 | Design 10 §3 | S56 |
| PR-2 | Design 23.3 §6.2–6.3 | implementation gap (F1), not an amendment |
| PR-3 | Design 07 §2, 23.2, 23.3 | S47, S65, S69 + ADR-0009 |
| PR-4 | Design 09 | S53, S54, S55 (S55 **plan required**) |
| PR-5 | Design 23.3 §6.1 | S70 |
| PR-6 | Design 23.3, Design 08 | S72, S52 |
| PR-7 | Design 23 §5.5.1, 23.2 | S59 |
| PR-8 | Design 23.2 | S64 |
| PR-9 | Design 23.3 §4 | S68 |
| PR-10 | Design 23 §2/§12, 23.4 | S60 + ADR-0008 |
| PR-11 | Design 04.3, Design 23 §5.7 | S45 |
| PR-12 | Design 23 §5.2, 03.2, 02 | S62, S43 |
| PR-13 | Design 04, Design 23 §5.7 | S44, S63 |
| PR-14 | **new Design 24 §2** | new spec |
| PR-15 | **new Design 24 §3** | new spec + S61, S42 |
| PR-16 | **new Design 24 §4–§6** | new spec + S50, S51, S46, S48, S58 |
| PF-1, PF-4 | — | closed; not requirements (Design 24 §10) |
| PF-2 | Design 23.2 | S66 |
| PF-3, PF-6 | Design 23.2 | S67 |
| PF-5 | Design 10 | S57 |
| PF-7 | Design 23.3, 23.2 | S71 |

**Answers** are recorded in this table as each item is accepted, rejected or deferred (add the date and the spec section). Until then the register's class column stands.

## Backlog: disposition, owner and trigger

The first version of this section was one table with **no owner and no trigger**, so the answer to "when do we fix these?" was "never". It also mixed four unlike things. **How to address them now:**

| Disposition | What it means | When it is addressed |
|---|---|---|
| **CP-** codex pattern | A permanent authoring rule, defined in conventions §9.7. Not a compromise to be undone. | **In force now.** Enforced where it applies. |
| **PF-** platform request | Platform-side, non-blocking. | **Step 2c**, batched with PR-1…PR-16. The platform may close it "won't fix". |
| **BD-** closed as by design | The workaround **is** the doctrine, for a stated reason. | **Closed.** Recorded so nobody re-opens it. |
| **DT-** deferred | Waiting on a named trigger. | **On its trigger**, not before. |

### CP- codex patterns in force

Patterns are defined once in **conventions §9.7**; this table is the register's record of what replaced what.

| # | Pattern | Applies to | Replaces |
|---|---|---|---|
| CP-1 | Non-combatants are **class-built** (`levels: { EXPERT: n }`). `monster: srd_…` is for real monsters; there is no civilian base in the library. | every NPC note (Steps 2, 15) | BL-5 (which was documented wrong — see the audit) |
| CP-2 | The Hushed and the Sung: one NPC per bound person + a `SECRET` edge + a Fact. | Steps 8, 12 | BL-6/older BL-7 |
| CP-3 | Body-hopping: one NPC per body, all `SECRETLY_SERVES` the same faction, tied by a Fact; **every body is pre-authored**. | Steps 8, 12 | older BL-6 |
| CP-4 | A testable lineage or taint: Fact + an NPC-scoped effect-only flag (`toward: npc_x`). | Steps 7, 12 | older BL-7 |
| CP-5 | Probabilistic content: a deterministic Condition + a GM random table. | Steps 12, 13 | older BL-2 |
| CP-6 | A material weakness with no damage type: a `has_item`-gated World Event + narration. | Steps 7, 8 | older BL-9 |
| CP-7 | A patron or pact with no Warlock class: the patron is a faction or NPC the caster `SECRETLY_SERVES`, tied by a Fact; a stat block proxies an existing SRD class. | Step 6 (occult), Steps 12, 15 | new in Step 6 (M22) |
| CP-8 | A **thread** is a state graph: an `<thread>_armed` flag, a one-way stage ladder, forks, bounded unrolled reprieve cycles, successors, and **intent flags** that Wants set and guarded World Events apply. Every source guards itself with `not flag_set <its own result>`. | Step 12 (every thread), Step 15 | new in Step 12a (M23) |
| CP-9 | Relative time is a **Want timer**: `deadline_days` from activation, chained by `on_deadline` flags. | Step 12, Step 15 | until PR-9 |
| CP-10 | A Campaign's start state is a **genesis World Event** in its overlay (`day_reached: 0`, guarded by `not <thread>_armed`); a later Campaign fast-forwards a thread by setting its stage flags. | Step 15 | until PR-10 |
| CP-11 | A Want is resolved by an Effect, never by state. **Write the state test as a guarded World Event** that sets the outcome flag and applies `resolve_want` or `fail_want`, so a player who achieves the Want's `desire` by a route no Quest covers still retires it and its `on_deadline` does not fire. | Step 12, Step 15 | until PF-7 |

### PF- platform requests, non-blocking (filed in Step 2c)

| # | Item | Worked around by | Note |
|---|---|---|---|
| PF-1 | Overland fragments and `distance_km` (pilot 2) | the Step 2a transformer assembles the world's overland graph (`world.overland`) and converts km → whole miles (conventions §9.2–9.3) | may be closed "by design": the codex owns conversion |
| PF-2 | `Fact.truth` rename (pilot 4) | the transformer writes the explicit string `TRUE` | cosmetic |
| PF-3 | Reveal-path and `permanent_secret` rules (pilot 6) | `permanent_secret: true` where no reveal path will exist | documentation only |
| PF-4 | A platform flag-declaration home (pilot 3) | declared in [[flags\|World Flags]] and copied into `manifest.yaml` | cosmetic |
| PF-5 | `author-cli validate` should run the codex's thread checks (Step 12a) | the codex's `tools/thread-check.mjs`: flag registry (set and read), own-stage guards, references inside Conditions and Effects | the validator's producer analysis (Design 23.3 §8) covers part of it |
| PF-6 | An optional `thread: <slug>` label on any authored entity (Step 12a, [[world-events-design]] section 7.2) | the codex records membership with a `_thread` directive and the thread note's `thread:` frontmatter; `tools/transform.mjs` strips it today and emits it as `thread:` when `EMIT_THREAD_LABEL=1` and the platform accepts the field (checked: the package rejects `thread` today as an unrecognized field) | metadata only, no rule meaning: for tooling, observability, `author-cli diff` grouping and the narrator's context retrieval |
| PF-7 | An optional `resolved_when` Condition on `WANT` (found in a design review of the guide): a Want that is resolved by state, not only by an Effect | CP-11: a guarded World Event per Want (`evt_ferry_missing` and `evt_ferry_settled` in [[campaign-authoring-guide]] section 4.7 are the pattern) | ergonomic; the watcher event does the same job at the cost of boilerplate on every Want |

### BD- closed as by design

The workaround is the doctrine, not a shortfall.

| # | Item | Doctrine | Home |
|---|---|---|---|
| BD-1 | No random-chance predicate (M15) | Conditions are engine-evaluated and deterministic by pillar; reachability analysis depends on it. Probabilistic content is a GM table (CP-5). | conventions §9.7 |
| BD-2 | No `has_trait` / lineage predicate (M7) | A Fact plus an NPC-scoped flag is testable by `flag_set` and keeps traits narrative (CP-4). | conventions §9.7, [[flags\|World Flags]] |
| BD-3 | No sanity / corruption track (M12) | The SRD carries no sanity subsystem; the Whisper is narration, Wants and flags. | [[the-conspiracy]] |
| BD-4 | No numeric zone magic-potency modifiers (M3, class C) | A rules-variant question, deferred with Design 09.1; scene gating is the world's design. Revisit only if a rules variant is adopted (DT-3). | Design 09.1 |

### DT- deferred, with a named trigger

| # | Item | Trigger | Action when triggered |
|---|---|---|---|
| DT-1 | A civilian SRD base (was BL-5) | the platform ships a civilian monster base | switch non-combatants to it; revise CP-1 |
| DT-2 | A COPPER material or an antifungal damage type (M9) | a campaign needs hard resistance rather than narration | request the material; revise CP-6 |
| DT-3 | Numeric zone magic potency (M3, class C) | a rules variant is adopted (Design 09.1) | re-classify M3 and add a zone modifier |

**Audit note (Step 2b follow-up).** The old backlog's BL-5 workaround was **wrong**: `srd_commoner` does not exist — the library's 21 monsters are all combat creatures, and the only "warrior" is `monster_skeleton_warrior`. The workaround actually in force is CP-1 (class-build with `EXPERT` levels), which the Step 2a NPCs already use. The old `BL-` numbers also drifted: the M4–M15 rows cited BL ids that did not match the backlog table. Both are corrected here, and the fix is recorded in the register's corrections list.

## Content fixes required

Gaps this classification created in the **existing codex**. Each has one owning step; do not create new steps for them.

Audited after Step 2b: the standard body line for deferred engine fields is now **conventions §9.6**, and the `item`, `creature` and `region` templates carry it. Each fix below is mechanically checkable at the owning step.

| Fix | Owning step and action |
|---|---|
| **SRD `base`** per relic and creature (conventions §9.6) | **Step 7** (relics) and **Step 10** (creatures). Write `**SRD base:** \`srd_…\``; if the library has no match, write `[OPEN] (PR-4)` and keep `engine: false`. Zero item/creature notes exist today, so nothing to backfill. |
| **Magic class** on every region/place note | **Step 6** defines the vocabulary (`well`, `knot`, `eddy`, `sink`, `normal`) in [[magic]]; **Step 3** applies it to holy sites that become places, **Step 11** to continent notes, **Step 13** to the map note. **Owner 3 and 13 added for this reason only** — they create no region notes otherwise. |
| **Flag declarations** | **Step 12** (17 thread notes) and **Step 15** (conversion) declare each flag in [[flags\|World Flags]] *before* the block that sets it. Expected set, none declared yet: `choir_host`, `gate_born`, `famine`, `fae_debt`, `scar_<place>`. Enforced by linter EN007. The Step 6 NPC Wants add `thessen_library_seized` ([[liora-of-thessen]]) and `nella_called` ([[nella-fitch]]) to declare. |
| **Trade-good ITEM notes** | **Step 9 ✔** created [[water-chit]], [[salt]] and [[resonant-salt]] under `world/items-materials/`. Each records `[OPEN] (PR-4)` for its SRD base and keeps `engine: false` (PR-5 for transfer and spending). |
| **`zone_` resolution** | **Step 14** emits a ZONE entity per `zone_` region note once PR-3 lands, and warns (does not fail) until then. Verified: all 15 referenced `zone_` ids already have region notes, so no content work. |
| **Disclosure and audience** on every secret and truth layer (PR-14, PR-15) | **Step 2d ✔** settled the classes and applied them to all 1,525 lore sections; **Step 14** exports the corpus; **Step 14a** tests it. |
| Conventions §13's stale descriptor sentence corrected | 2b ✔ |
| The register's old entry 4 (content descriptors) corrected | 2b ✔ |

## Corrections made in Step 2b

- The backlog was audited (Step 2b follow-up) and shown to be **inadequate as a hand-off**: one table with no owner or trigger, mixing platform requests, permanent patterns and by-design decisions; and its `BL-` cross-references had drifted. It is now four dispositions (CP/PF/BD/DT) with owners and triggers.
- The old `BL-5` workaround was **wrong**: `srd_commoner` does not exist in the SRD library (21 monsters, all combat). The real pattern is **CP-1** (class-build with `EXPERT` levels).
- The seeded entry "content descriptors need extending for trafficking, bondage and body horror" was **wrong**: `VIOLENCE`, `HORROR` and `MATURE_THEMES` are all in the closed enum. Conventions §13 and this note are corrected.
- The seeded entry "a relationship kind for being bound to or feeding something" is **downgraded** to BL-7: the `CONTROLS`/`SECRETLY_SERVES` + Fact pattern works today.
- The seeded entry "gate crossings that go wrong" is **downgraded**: the lore reshapes to a deterministic trigger (M15), and only the cadence needs the platform (PR-2).
- The seeded entry "body-hopping" is **downgraded to A** for a creature whose power is to take another's body, with BL-7 for the nicer kind.

## Open questions

- [OPEN] Whether the platform accepts the load-bearing set, and which of PR-1…PR-16 it will implement (Step 2c).
- [OPEN] Whether the SRD library is expanded per world (a world supplies its own base map) or the platform ships a full SRD.

## Links

Every one of these is a kit document, at `meta/conventions/`; the last is the world's own.

- `meta/conventions/conventions.md` — the rules the register's vocabularies feed
- `meta/conventions/thread-pattern.md` — the graph the Conditions and Effects move
- `meta/conventions/campaign-authoring-guide.md` — the authoring how-to
- `meta/conventions/site.md` — what reaches the public site
- `meta/mechanics-gap-register.md` — which of these requests **this** world's lore is waiting on
- `world/flags.md` — the world's declared effect-only flags

# Engine Capability Register

**What this is.** Every mechanic a world wants, classified against what the engine can actually
express — and the **single home for the platform requests**. It is the kit's, because it is a
statement about the engine: what the schemas and vocabularies in
`$MYTHICAL_FORGE_ROOT/packages/authored-content` and the SRD data in `packages/shared-data` can do.
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

### PR-1 — `author-cli validate`
- **Class B (infra). Driver:** a transformer has to import the package `dist` directly; the designs
  assume a CLI.
- **Build:** `author-cli validate <game-ready-repo>` doing offline schema validation plus bundle
  checks (reference integrity, reveal paths, flag declarations, derived-field rejection).
- **Acceptance:** one command, non-zero exit on error, machine-readable output; runs in CI.

### PR-2 — Cadenced and recurring World Events
- **Class B. Driver:** a World Event fires once per source, so anything that happens on a cadence —
  a gate that opens monthly, a stage that recurs, a rumour that returns — cannot be authored.
- **Build:** a `repeat`/`cadence` field on `WORLD_EVENT`, or a documented repeatable form with a
  declared `fire_key`.
- **Acceptance:** an event may fire N times or on a cadence, each firing applied exactly once per
  `(sandbox_id, source_id, fire_key)` (the platform's idempotency idiom).

### PR-3 — First-class ZONE / REGION entity
- **Class B. Driver:** `zone_id` is already the lazy-hydration unit but has no entity, so zone
  references dangle and regional mechanics have nothing to attach to.
- **Build:** a `zone_` entity kind the validator resolves, with an optional magic/leyline
  descriptor, and a Condition to test zone membership (for example `in_zone`).
- **Acceptance:** every `zone_id` in the repository resolves; a Condition can gate content on a zone.

### PR-4 — SRD library: id convention, coverage and structured material properties
- **Class B. Driver:** `SrdRef` expects `srd_…` while the library ships
  `monster_…`/`item_…`/`spell_…`/`feat_…`/`skill_…`; the library is a sample (21 monsters, 66
  items); damage reduction is free text; and there is no class source of truth, so authored
  `levels:` keys have nothing to resolve against.
- **Build:** (a) one documented id form for SRD references, honoured by both the package and
  `shared-data`; (b) structured `damage_reduction` / `vulnerabilities` by material on monsters;
  (c) enough coverage to run a world's creatures and relics; **(d) a structured class/power table so
  `levels:` keys resolve.**
- **Acceptance:** a creature with an iron weakness and one with a silver weakness validate and
  resolve; no id-form mismatch between package and library; every authored `levels:` class key
  resolves against a shipped class table.

### PR-5 — Item transfer, consumption and a generic trade good
- **Class B. Driver:** goods and relics cannot be handed over, spent or consumed; `grant_reward` is
  allowed only in Quests and Migrations; `ITEM` requires an SRD base that does not exist for trade
  goods.
- **Build:** Effects to give, remove and consume an item, a Condition to test ownership and
  quantity, and a generic trade-good item family (or an author-named item with a documented SRD
  base).
- **Acceptance:** an event can transfer a good or a relic to the player, and a Quest milestone can
  require and consume one.

### PR-6 — A magic-use hook
- **Class B. Driver:** "casting costs the caster and scars the land" is a common world identity, but
  authored content cannot observe a casting.
- **Build:** either a `WILD_MAGIC` judgement tag (engine-recorded from an agent proposal, like the
  existing four) or a `magic_used` predicate a World Event can test.
- **Acceptance:** a World Event can fire once heavy casting has occurred in a zone, without an
  author-invented rule.

### PR-7 — Publish the group-knowledge resolution contract
- **Class B (small). Driver:** `known_by`/`believed_by` accept NPC ids only, while knowledge belongs
  to groups; every transformer resolves group + tier itself. An empty `believed_by` currently
  invalidates `believed_as`.
- **Build:** either tiered `known_by_groups` in the schema, or a documented resolution contract (ids
  only) that all transformers implement; fix the empty-belief case.
- **Acceptance:** one documented contract; the package's validator agrees with it.

### PR-8 — Document the derived Relationship id
- **Class B (small). Driver:** the codex omits a Relationship's `id`; the compiler derives one;
  transformers must derive the same string.
- **Acceptance:** the derivation is specified (or a helper exported), so a codex transformer and the
  compiler cannot disagree.

### PR-9 — A relative-time Condition (`days_since`)
- **Class B. Driver:** `day_reached` is absolute, so "30 days after stage 2" and "a reprieve, then
  resume" cannot be written. The data exists: FLAG items record `first_day` and `last_day`, and
  events record `occurred_on_day`.
- **Build:** `days_since: { flag: <flag>, toward?: <ref>, days: n }` and
  `days_since: { event: evt_x, days: n }`, with a watch key on `clock`.
- **Acceptance:** a World Event can fire a fixed number of days after a flag was first set or an
  event occurred, deterministically. Until it lands, **CP-9** (Want timers) does the job for
  NPC-driven clocks; environmental clocks cannot be expressed without an NPC anchor.

### PR-10 — Campaign start state, outcomes and succession
- **Class B. Driver:** the designs say a Sandbox belongs to exactly one Campaign, and a Campaign has
  no start state, no end state and no successor — so Campaigns cannot chain inside one Sandbox.
- **Build:** on `CAMPAIGN`: (a) `start_effects` (an Effect list applied once at `SANDBOX_CREATED`);
  (b) `outcomes` (named end states, each a Condition); (c) `follows: camp_x` with
  `requires_outcome` and a `transition` Effect list, so a Sandbox can adopt the next Campaign at a
  safe point while keeping its character and state (hydrated entities stay frozen). Update the
  Campaign designs.
- **Acceptance:** a second Campaign can start a Sandbox from the world state the first one left, with
  no character import and no re-firing of earlier events. Until it lands, **CP-10** (a genesis event
  in the overlay) gives start state, and outcomes are flags.

### PR-11 — Quest outcomes, failure and abandonment
- **Class B. Driver:** a Quest has one linear milestone chain and one `on_complete`; there is no
  failure, abandonment or branching ending, so "depending on how a quest turns out" cannot be
  written.
- **Build:** `outcomes: [{ id, when, then }]` evaluated at completion (first match), plus `on_fail`
  and `on_abandon` Effect lists. Keep `on_complete` as the default outcome.
- **Acceptance:** one Quest can end three ways with different Effects. Until it lands, split the
  Quest into alternative **Resolution Paths** of one Want, each with its own `on_complete`.

### PR-12 — Want and NPC lifecycle semantics
- **Class B (clarification, plus one Effect). Driver:** the Want design does not say when a Want's
  `deadline_days` clock starts, whether `urgent_when` only activates or also deactivates, what
  `fail_want` does to `on_deadline`, or what an NPC's death does to its Wants.
- **Build (clarify in the Want design):** (a) the clock starts on the first day `urgent_when` holds
  or the day `activate_want` names the Want; (b) `urgent_when` only activates; (c) `resolve_want`
  and `fail_want` both prevent `on_deadline`; (d) a dead NPC's own Wants fail; (e) only **urgent**
  Wants count as Major for the tick.
- **Acceptance:** the simulator's assumptions are stated in the spec.

### PR-13 — Quest and Module availability (`available_when`, `expires_when`)
- **Class B. Driver:** there is no way to say a Quest or Module is *moot now*: a world that moves on
  cannot retire "hide the boy" after the boy is taken.
- **Build:** optional `available_when` and `expires_when` Conditions on `QUEST` and `MODULE` (or on
  a Campaign `unlocks` entry).
- **Acceptance:** the Module Selector and the Want path hide a Quest whose `available_when` is
  false. Until it lands, a world keeps its gates in a scenario sidecar and the simulator refuses a
  Quest the world has moved past.

### PR-14 — A retrievable Lore corpus
- **Class B. Driver:** the engine has no entity for prose lore. An NPC agent receives only its own
  Wants, Relationships and Facts and a token-capped persona, so a quay-hand knows nothing of the
  world's history unless a Fact says so; the narrator has no sanctioned source for a player's general
  questions. Most of a codex stays prose and never reaches runtime.
- **Build:** a compiled, chunked **Lore** corpus (a `LORE` entity kind, or a content-addressed
  document type indexed beside Facts). Each chunk carries `topic` (the note's id), `layer`
  (`truth`, `official`, `myth` or `rival`), `audience` (groups and tiers, resolved to NPC ids
  exactly as Fact knowledge is, conventions §9.5), `disclosure` (PR-15) and `subjects`. Two
  retrieval contracts, **enforced in code in the retriever, never in the prompt**:
  1. **NPC retrieval** returns the chunks whose audience includes the NPC, **at the layer that NPC
     believes**. An NPC's own Wants are always included (self-audience), even when it will never say
     them, because they shape its reaction to the player.
  2. **Narrator retrieval** follows PR-15.
  Chunks are token-capped and delimited as untrusted data, embedded at publish like authored memory
  seeds, and versioned like any authored entity.
- **Acceptance:** two NPCs asked about the same event answer from different layers according to their
  group and tier; neither is handed a chunk outside its audience; a chunk edit reaches a Sandbox by
  the unhydrated/hydrated rules.

### PR-15 — Disclosure classes and a code-enforced narrator gate
- **Class B. Driver:** **GM-only material is codex knowledge the narrator may selectively disclose**,
  not material to be kept out. The retired `visibility: gm | public` field decided only what a
  printed player primer may show; it said nothing about what the narrator may say in play. The
  narrator is given everything, secrets are labelled `UNDISCLOSED`, and it is asked politely not to
  reveal them.
- **Build:** a closed `disclosure` classification on lore chunks and Facts, enforced by the engine
  when it assembles the narrator's context. **Classes (conventions §7):**

  | Class | Narrator may | Reaches the player by |
  |---|---|---|
  | `open` | state it whenever relevant | nothing: it is already known |
  | `earned` | foreshadow with atmosphere and rumour, but not state it; may state it **once its reveal path has been taken** | an earned path: an NPC who knows it tells the player, a check, a found document, an event, or the narrator's own validated choice when the chunk's `reveal_when` Condition holds |
  | `sealed` | use it only to stay consistent; never hint beyond the authored `rumor_seeds` | a specific authored event or Quest |

  There are **two paths**. On the **answer path** (the player asks about the world, or about what they
  know) the context is `open` chunks plus the player's ledger, and nothing else: withheld chunks are
  absent, so a prompt such as "ignore your instructions" cannot extract what was never supplied. On
  the **scene path** (narrating a scene) the engine adds only the `earned` and `sealed` items the
  scene needs for consistency (the NPC in the room is a host), labelled `UNDISCLOSED`; secrecy there
  rests on the narrator's output, which must pass the `disclose` validation and the egress check.
  That is the residual risk, and the size of the consistency set is open. An `earned` chunk enters
  the narrator's context as *disclosable* only when its `reveal_when` holds; the narrator may then
  disclose it through a structured, validated `disclose` proposal (PR-16). `reveal_when` is
  optional; a codex records it in words (`**Reveal when:**`) until the platform accepts a Condition.
- **Acceptance:** with a `sealed` chunk in the corpus, no player prompt can elicit it from the
  narrator or from an NPC outside its audience (checked by an eval set); the narrator can disclose an
  `earned` chunk whose gate holds and cannot when it does not.

### PR-16 — Disclosure capture and the player's knowledge ledger
- **Class B. Driver:** builds on two open items in the design — how an NPC *telling* the player a
  Fact is recorded, and the fact that the narrator returns streamed prose with no structured channel.
  Until they close, `fact_revealed`, and so every `DIALOGUE` milestone that tests it, can be
  completed only by an engine-fired `reveal_fact`, never by a conversation.
- **Build:**
  1. **Capture from NPC dialogue:** the agent returns `reveals: [ids]`. The engine accepts an id only
     if it is in that NPC's own audience (what it knows or believes), then records the disclosure.
  2. **Capture from narration:** a trailing, stripped, schema-validated block on the narrator's
     output (`disclose: [ids]`), validated against PR-15. Only `open` chunks and `earned` chunks
     whose gate holds are accepted.
  3. **The ledger:** a per-Sandbox store of what the player has been told: the id, **the layer or
     version told** (the player may hold a false belief), the source (an NPC id, a document or the
     narrator), the day, and how (told, read, observed). It is the single source for
     `fact_revealed`, the player's journal, and the narrator's answers to "what do I know about X?".
  4. Recording is idempotent per turn on the `request_id`, the same idiom as judgement tags.
- **Out of scope for v1:** the player *inferring* a secret without being told; an NPC remembering what
  the player told it.
- **Acceptance:** a `DIALOGUE` milestone with `when: { fact_revealed: … }` completes after an NPC
  tells the player in conversation; the ledger shows who said it, on which day, and which version;
  the narrator answers "what have I learned about X?" from the ledger alone; a retried turn records
  nothing twice.

## Where the specs live

The platform is spec-first: new work enters as **spec text**, not as a ticket. The drafts are in
`meta/platform-requests/` (not vault notes, so excluded from lint) and were delivered to the platform
repository with a per-spec record in `Amendments & Roadmap Delta.md` §7.

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
| PF-1, PF-4 | — | closed; not requirements |
| PF-2 | Design 23.2 | S66 |
| PF-3, PF-6 | Design 23.2 | S67 |
| PF-5 | Design 10 | S57 |
| PF-7 | Design 23.3, 23.2 | S71 |

**Answers** are recorded in this table as each item is accepted, rejected or deferred (add the date
and the spec section). Until then the register's class stands for every world.

## The dispositions

| Disposition | What it means | When it is addressed |
|---|---|---|
| **CP-** codex pattern | A permanent authoring rule. Not a compromise to be undone. | **In force now.** Enforced where it applies. |
| **PF-** platform request | Platform-side, non-blocking. | Batched with PR-1…PR-16. The platform may close it "won't fix". |
| **BD-** closed as by design | The workaround **is** the doctrine, for a stated reason. | **Closed.** Recorded so nobody re-opens it. |
| **DT-** deferred | Waiting on a named trigger. | **On its trigger**, not before. |

### CP- patterns in force

Each is defined in `conventions.md` §9.7 and recorded here as the register's statement of what
replaced what. **The "where it applies" column names the capability need, not a world's feature**: a
world's register says which of its rows each pattern covers.

| # | Pattern | Where it applies |
|---|---|---|
| CP-1 | Non-combatants are **class-built** (`levels: { EXPERT: n }`). `monster: srd_…` is for real monsters; there is no civilian base in the library. | every non-combatant NPC |
| CP-2 | "X is bound to / feeds Y": one NPC per bound person + a `CONTROLS`/`SERVES` edge with `visibility: SECRET` or `permanent_secret: true`, plus a Fact. | bound or fed persons |
| CP-3 | Body-hopping (one mind, many bodies): one NPC per body, all `SECRETLY_SERVES` the same faction, tied by a Fact; **every body is pre-authored**. | a mind that moves between bodies |
| CP-4 | A testable lineage or taint: a Fact plus an NPC-scoped effect-only flag (`flag_set: { flag: x, toward: npc_x }`), tested with the same `toward`. | traits the engine has no predicate for |
| CP-5 | Probabilistic content: a **deterministic** Condition (`day_reached`, `flag_set`) plus a GM random table. | anything "1 in N" |
| CP-6 | A material weakness with no damage type: a `has_item`-gated World Event plus narration. | a weakness the SRD cannot express |
| CP-7 | A patron or pact with no Warlock class: the patron is a faction or NPC the caster `SECRETLY_SERVES`, tied by a Fact; a stat block proxies an existing SRD class. | classes the engine does not ship |
| CP-8 | A **thread** is a state graph: an `<thread>_armed` flag, a one-way stage ladder, forks, bounded unrolled reprieve cycles, successors, and **intent flags** that Wants set and guarded World Events apply. Every source guards itself with `not flag_set <its own result>`. | any plot that runs without the player |
| CP-9 | Relative time is a **Want timer**: `deadline_days` from activation, chained by `on_deadline` flags. | until PR-9 |
| CP-10 | A Campaign's start state is a **genesis World Event** in its overlay (`day_reached: 0`, guarded by `not <thread>_armed`); a later Campaign fast-forwards a thread by setting its stage flags. | until PR-10 |
| CP-11 | A Want is resolved by an Effect, never by state. **Write the state test as a guarded World Event** that sets the outcome flag and applies `resolve_want` or `fail_want`, so a player who achieves the Want's `desire` by a route no Quest covers still retires it and its `on_deadline` does not fire. | until PF-7 |

### PF- platform requests, non-blocking

| # | Item | Worked around by | Note |
|---|---|---|---|
| PF-1 | Overland fragments and `distance_km` | the transformer assembles the graph from fragments and converts km → whole miles (conventions §9.2–§9.3) | may be closed "by design": the codex owns conversion |
| PF-2 | `Fact.truth` rename | the transformer writes the explicit string `TRUE` | cosmetic |
| PF-3 | Reveal-path and `permanent_secret` rules | `permanent_secret: true` where no reveal path will exist | documentation only |
| PF-4 | A platform flag-declaration home | declared in the world's `flags` block and copied into `manifest.yaml` | cosmetic |
| PF-5 | `author-cli validate` should run the codex's thread checks | `tools/thread-check.mjs`: flag registry (set and read), own-stage guards, references inside Conditions and Effects | the validator's producer analysis covers part of it |
| PF-6 | An optional `thread: <slug>` label on any authored entity (conventions §9.8) | the codex records membership with a `_thread` directive and the thread note's `thread:` frontmatter; `tools/transform.mjs` strips it and emits it as `thread:` when `EMIT_THREAD_LABEL=1` and the platform accepts the field | metadata only, no rule meaning: for tooling, observability, `author-cli diff` grouping and the narrator's context retrieval |
| PF-7 | An optional `resolved_when` Condition on `WANT` — a Want resolved by state, not only by an Effect | CP-11: a guarded World Event per Want | ergonomic; the watcher event does the same job at the cost of boilerplate on every Want |

### BD- closed as by design

The workaround is the doctrine, not a shortfall.

| # | Item | Doctrine | Home |
|---|---|---|---|
| BD-1 | No random-chance predicate | Conditions are engine-evaluated and deterministic by pillar; reachability analysis depends on it. Probabilistic content is a GM table (CP-5). | conventions §9.7 |
| BD-2 | No `has_trait` / lineage predicate | A Fact plus an NPC-scoped flag is testable by `flag_set` and keeps traits narrative (CP-4). | conventions §9.7 |
| BD-3 | No sanity or corruption track | The SRD carries no sanity subsystem; such a mechanic is narration, Wants and flags. | conventions §9.7 |
| BD-4 | No numeric zone magic-potency modifiers | A rules-variant question, deferred with Design 09.1; scene gating is a world's design choice. Revisit only if a rules variant is adopted (DT-3). | Design 09.1 |

### DT- deferred, with a named trigger

| # | Item | Trigger | Action when triggered |
|---|---|---|---|
| DT-1 | A civilian SRD base | the platform ships a civilian monster base | switch non-combatants to it; revise CP-1 |
| DT-2 | A material the library lacks, or a missing damage type | a campaign needs hard resistance rather than narration | request the material; revise CP-6 |
| DT-3 | Numeric zone magic potency | a rules variant is adopted (Design 09.1) | re-classify the affected rows and add a zone modifier |

## Open items

- [OPEN] Which of PR-1…PR-16 the platform implements, and in what order. Each world's register says
  which requests its own lore is waiting on.
- [OPEN] Whether the SRD library is expanded per world (a world supplies its own base map) or the
  platform ships a full SRD.

## Links

- `conventions.md` §9.7 — the stand-in patterns, defined once
- `docs/thread-pattern.md` — CP-8, CP-9, CP-10 and CP-11 in full
- `meta/platform-requests/` — the spec drafts delivered to the platform

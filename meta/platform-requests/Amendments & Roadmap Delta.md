# Amendments & Roadmap Delta — Hollowfall platform requests (Step 2c)

> **Status:** **APPLIED 2026-11-02** (codex-authored; owner-approved and applied in `mythical-forge`). This is the delivery form of the Hollowfall codex's [Mechanics Gap Register](../mechanics-gap-register.md) (PR-1…PR-16, PF-1…PF-7, M1–M24). Nothing here is applied to any platform spec or task; the platform owner applies it. Modelled on `docs/design-reviews/Design 23 - Amendments & Roadmap Delta.md`.
> **Source:** `meta/mechanics-gap-register.md` (the register, which stays authoritative for *why*) and `meta/platform-requests/Design 24 - Lore, Disclosure & the Knowledge Ledger.md` (the new subsystem).
> **Companions:** Design 24 (§1–§11) · proposed ADRs 0008 and 0009 in `adr/`.
> **Legend:** `[ ]` open · `[~]` in progress · `[x]` applied · `[!]` blocked on a decision. All items start `[ ]`.
> **Verification:** every claim about the current code below was checked against `packages/authored-content` on **2026-11-02**. Re-check before applying.

---

## 0. Findings: spec gap vs implementation gap

The register (Step 2b) classified each mechanic from the **schemas**. Designs 23.2, 23.3 and 23.4 have since been written, so some register items are now **specified but not implemented**. That changes the home of the fix: an implementation gap needs a task, not an amendment. These are the differences found:

| # | Finding | Effect on the register |
|---|---|---|
| F1 | **Cadenced World Events.** Design 23.3 §6.3 already specifies `repeatable: true`, a required `fire_key` and a `max_fires`, and §6.2 the `FIRED#<source_id>#<fire_key>` key. `src/entities/world-event.ts` has **no** `repeatable`/`fire_key`/`max_fires`. | **PR-2 / M19 is an implementation gap, not a spec gap.** Task in Phase 4. |
| F2 | **`zone_` has no entity.** `src/entities/base.ts` and `world-content.ts` carry `zone_id` as a lazy-hydration unit; no `ZONE` kind, and no `in_zone` predicate in `condition.ts`. | PR-3 stands. Amendments S47, S65; ADR-0009. |
| F3 | **No `author-cli`.** `cli/` contains only `play-cli`. | PR-1 stands (S56). |
| F4 | **Psionics still absent.** No `.ts` in `packages/` mentions psionics. | M21 stands; position recorded in S55. |
| F5 | **Design 23.3 §7 lists two "required amendments (not applied)"**: Design 07 §2D `pending_world_ripples.payload` gains an optional `effects` array, and Design 03.2 §3.4 gains Engine B executing it. | Add them here as S49 (so one document carries every outstanding amendment). |
| F6 | **The empty-belief case of PR-7 is fixed.** `src/entities/fact.ts` now rejects `believed_as` without `believed_by`. `known_by` is still NPC ids only, with no group/tier form. | PR-7 narrows to the **documented resolution contract** (S59). |
| F7 | **Design 23 §14 item 11 is still open** (the narrator has no structured channel). | This package takes a position (S51) so Design 08 and Design 24 cannot diverge. |

**Disagreements, stated explicitly** (the register asks for this rather than a silent default): **PF-1** and **PF-4** are **not** platform requirements. The codex owns overland-fragment assembly and the km → miles conversion, and the codex declares effect-only flags in its own `world/flags.md`. They are recorded as *closed, not requirements* in Design 24 §10 rather than filed.

---

## 1. Routing — every register item to its spec home

| Register item | Owning spec | Amendment / task |
|---|---|---|
| PR-1 `author-cli validate` | Design 10 §3 | **S56** |
| PR-2 cadenced World Events | Design 03.2, Design 23.3 §6.2–6.3 | **F1 — task, not amendment** |
| PR-3 first-class ZONE entity | Design 07 §2, 23.2, 23.3 | **S47, S65, S69** + **ADR-0009** |
| PR-4 SRD ids, coverage, DR, class table | Design 09 | **S53, S54, S55** (S55 **PLAN REQUIRED**) |
| PR-5 item transfer/consumption/trade good | Design 23.3 §6.1 | **S70** |
| PR-6 a magic-use hook | Design 23.3, Design 08 | **S72**, **S52** |
| PR-7 group-knowledge resolution contract | Design 23 §5.5.1, Design 23.2 | **S59** |
| PR-8 derived Relationship id | Design 23.2 §(schemas) | **S64** |
| PR-9 `days_since` Condition | Design 23.3 §4 | **S68** |
| PR-10 Campaign start state, outcomes, succession | Design 23 §2/§12, Design 23.4 | **S60** + **ADR-0008** |
| PR-11 Quest outcomes, failure, abandonment | Design 04.3, Design 23 §5.7 | **S45** |
| PR-12 Want and NPC lifecycle semantics | Design 23 §5.2, Design 03.2 §2.2, Design 02 | **S62, S43** |
| PR-13 Quest and Module availability | Design 04, Design 23 §5.7 | **S44, S63** |
| PR-14 lore corpus | **Design 24 §2** | new spec (no amendment) |
| PR-15 disclosure classes, narrator gate | **Design 24 §3** | new spec + **S61, S42** |
| PR-16 disclosure capture, ledger | **Design 24 §4–§6** | new spec + **S50, S51, S46, S48, S58** |
| PF-1 overland fragments | — | not a requirement (Design 24 §10) |
| PF-2 `Fact.truth` rename | Design 23.2 | **S66** |
| PF-3 reveal-path / `permanent_secret` rules | Design 23.2 | **S67** |
| PF-4 flag-declaration home | — | not a requirement (Design 24 §10) |
| PF-5 validator runs the thread checks | Design 10 | **S57** |
| PF-6 optional `thread:` label | Design 23.2 | **S67** |
| PF-7 optional `resolved_when` on WANT | Design 23.3, Design 23.2 | **S71** |

---

## 2. Amendments

### Design 02 — NPC

- [x] **S42 — Retriever contract and disclosure on dialogue.** §(context/retriever): add that the NPC context assembler returns authored **Lore chunks** whose audience includes the NPC, at the layer it believes, plus its own Wants, and never anything else; and that when the NPC tells the player something, the engine records it in the knowledge ledger (Design 24 §2.3, §4.1). *Driver:* PR-14, PR-16. *Acceptance:* two NPCs, one event, different layers.

### Design 03.2 — Background World Simulation

- [x] **S43 — Cadence and relative time in the tick.** §(triggers/clock): state that a repeatable World Event is evaluated at `TIME_ADVANCED` with its `fire_key` (Design 23.3 §6.2–6.3), and that a relative-time Condition (`days_since`, S68) is evaluated for armed sources whose watch set contains `clock` or `flag:`. *Driver:* PR-2, PR-9, PR-12. *Acceptance:* "30 days after stage 2" fires deterministically.

### Design 04 — Story Manager

- [x] **S44 — Quest and Module availability.** §2: add optional `available_when` and `expires_when` Conditions to a Quest, a Module, and a Campaign `unlocks` entry; the Module Selector and the Want path hide a Quest whose `available_when` is false. *Driver:* PR-13. *Acceptance:* "hide the boy" is refused after the boy is taken.
- [x] **S45 — Quest outcomes, failure and abandonment.** §(quests) + Design 04.3: add `outcomes: [{ id, when, then }]` evaluated at completion (first match) with `on_fail` and `on_abandon`, `on_complete` remaining the default. *Driver:* PR-11. *Acceptance:* one Quest ends three ways with different Effects.

### Design 04.3 — Quest Completion & Reward Idempotency

- [x] **S46 — `DIALOGUE` milestones by captured disclosure.** §2 (milestone criteria): state that a `DIALOGUE` milestone testing `fact_revealed` is satisfied by a disclosure captured under Design 24 §4, not only by an engine-fired `reveal_fact`. *Driver:* PR-16. *Acceptance:* talking to the NPC completes the milestone.

### Design 07 — Database schemas

- [x] **S47 — A first-class `ZONE` node kind.** §2: add `ZONE` (or `REGION`) to the node kinds, with an optional magic/leyline descriptor, and state that `zone_id` references resolve to it. *Driver:* PR-3. *Acceptance:* every `zone_id` in a repository resolves. *ADR-0009.*
- [x] **S48 — The knowledge ledger's home.** §2: name the store for the player's disclosure ledger (proposed: a `DISCLOSURE#` item in `rpg_game_state`, reused by the existing Fact-disclosure path, rather than a new table). *Driver:* PR-16. *Acceptance:* the ledger answers "what have I learned about X?" alone.
- [x] **S49 — Ripple payload carries Effects.** §2D: `pending_world_ripples.payload` gains an optional `effects` array; Design 03.2 §3.4 gains the rule that Engine B executes `payload.effects` under the Design 23.3 §6.2 guard (`FIRED#<ripple_id>#<location_id>`). *Driver:* already required by Design 23.3 §7 (F5). *Acceptance:* a deferred `REGION` effect reaches a distant region exactly once.

### Design 08 — LLM Agents

- [x] **S50 — Agent 3 returns `reveals`.** §(Agent 3 output contract): add `reveals: [ids]`, accepted by the engine only if the id is in that NPC's own audience, then recorded in the ledger. *Driver:* PR-16, Design 23 §14 item 10. *Acceptance:* F4.4 of Design 24's acceptance list.
- [x] **S51 — The DM Narrator's structured `disclose` block.** §(narrator): add a trailing, stripped, schema-validated block on the narrator's output (`disclose: [ids]`), validated against Design 24 §3; only `open` chunks and `earned` chunks whose `reveal_when` holds are accepted; a malformed block discloses nothing. Record that this settles Design 23 §14 item 11. *Driver:* PR-15, PR-16. *Acceptance:* Design 24 §8 items 2–3.
- [x] **S52 — The magic-use judgement tag.** §(judgement tags): add `WILD_MAGIC` to the closed, engine-recorded, Agent-proposed tag set (ADR-0006) **or** state why a `magic_used` predicate is preferred (S72). *Driver:* PR-6, M2. *Acceptance:* a World Event can fire once heavy casting has scarred a zone.

### Design 09 — Game Rules Engines

- [x] **S53 — One SRD id convention.** §1: document one id form for SRD references honoured by both `packages/authored-content` (`SrdRef` expects `srd_…`) and `packages/shared-data` (`monster_…`, `item_…`, `spell_…`). *Driver:* PR-4, M20. *Acceptance:* no id-form mismatch; a written entity validates against a real SRD id.
- [x] **S54 — Structured material properties.** §(monsters/items): replace damage reduction free text with structured `damage_reduction` / `vulnerabilities` by material, and fill the library's coverage. *Driver:* PR-4, M8. *Acceptance:* a creature with an iron weakness and one with a silver weakness validate and resolve.
- [x] **S55 — A class and power table. PLAN REQUIRED.** §(progression/spells): define a structured class/power source of truth so authored `levels:` keys resolve (there is no Warlock and no psionics today, M21–M22), and state the psionics position. **This needs an analysis doc before tasks** (`docs/srd-analysis/`), per the platform's own guide. *Driver:* PR-4, M21, M22. *Acceptance:* every authored `levels:` class key resolves against a shipped class table.

### Design 10 — Author Tooling

- [x] **S56 — `author-cli validate`.** §3 + Design 21: specify `author-cli validate <game-ready-repo>`: offline schema validation plus bundle checks (reference integrity, reveal paths, flag declarations, derived-field rejection), one command, non-zero exit on error, machine-readable output, runs in CI. *Driver:* PR-1. *Acceptance:* CI fails on a broken repository.
- [x] **S57 — The validator runs the content checks.** §3: add the checks the codex's `tools/thread-check.mjs` already performs: flag registry (every set flag is declared and every read flag is set), own-stage guards, references inside Conditions and Effects. *Driver:* PF-5. *Acceptance:* an undeclared flag fails validation.

### Design 16 — Content Moderation

- [x] **S58 — Egress covers the narrator's structured block.** §7: the egress leak check and URL stripping apply to the `disclose` block (S51), and the block is stripped before the player sees the prose. *Driver:* PR-16. *Acceptance:* a link or a withheld id in the block is removed and logged.

### Design 23 — Authored Content Model

- [x] **S59 — Group knowledge and the resolution contract.** §5.5.1 / §5.6: either add tiered `known_by_groups` to `Fact` and World Event `known_by`, **or** document the resolution contract (ids only) that every transformer implements and fix the empty-belief case (already fixed in code, F6). *Driver:* PR-7. *Acceptance:* one documented contract that the package's validator agrees with.
- [x] **S60 — Campaign start state, outcomes and succession.** §2 and §12: on `CAMPAIGN`, add `start_effects` (applied once at `SANDBOX_CREATED`), `outcomes` (named end states, each a Condition), and `follows: camp_x` with `requires_outcome` and a `transition` Effect list, so a Sandbox adopts the next Campaign at a safe point while keeping its character and state. Update Design 23.4. *Driver:* PR-10. *Acceptance:* a second Campaign starts from the world state the first left, with no character import and no re-fired events. *ADR-0008.*
- [x] **S61 — §8.3 points at Design 24.** §8.3 ("Who sees authored secrets"): replace "the narrator is told not to reveal them" with a reference to Design 24 §3 for the code-enforced gate, keeping the existing Relationship-`visibility` rule for NPC agents. *Driver:* PR-15. *Acceptance:* no divergence between the two documents.
- [x] **S62 — Want lifecycle semantics.** §5.2 (and Design 03.2 §2.2): state (a) a Want's `deadline_days` clock starts on the first day `urgent_when` holds or the day `activate_want` names it; (b) `urgent_when` only activates; (c) `resolve_want` and `fail_want` both prevent `on_deadline`; (d) a dead NPC's own Wants fail; (e) only **urgent** Wants count as Major for the tick. *Driver:* PR-12. *Acceptance:* the simulator's assumptions A-1…A-5 are stated in the spec.
- [x] **S63 — §5.7 points at quest availability.** §5.7: cross-reference S44 for `available_when` / `expires_when`. *Driver:* PR-13. *Acceptance:* traceability from the Quest entity to the Conditions.

### Design 23.2 — Storage & Schemas

- [x] **S64 — The derived Relationship id is documented.** §(schemas): specify the derivation (or export a helper) so the codex transformer and the compiler cannot disagree. *Driver:* PR-8. *Acceptance:* one documented derivation.
- [x] **S65 — `zone_` in the schemas and the content index.** §3.3 / §9: add the `zone_` kind to the effective entity set and the index. *Driver:* PR-3. *Acceptance:* a `zone_` reference in a Condition is a resolvable reference. *ADR-0009.*
- [x] **S66 — `Fact.truth` spelling.** §(schemas) + README: settle the `TRUE`/`true` spelling. *Driver:* PF-2 (cosmetic). *Acceptance:* the package and the spec samples agree.
- [x] **S67 — Housekeeping: reveal-path rules and the thread label.** §(schemas): (a) document the reveal-path and `permanent_secret` rules (PF-3); (b) add an optional `thread: <slug>` label on any authored entity, metadata only, no rule meaning (PF-6). *Driver:* PF-3, PF-6. *Acceptance:* `EMIT_THREAD_LABEL` output validates.

### Design 23.3 — Condition & Effect Language

- [x] **S68 — `days_since`.** §4: add `days_since: { flag, toward?, days }` and `days_since: { event, days }`, watch key `clock`; the data exists (`FLAG` items record `first_day`/`last_day`; events record `occurred_on_day`). *Driver:* PR-9, M23. *Acceptance:* an event fires a fixed number of days after a flag was first set, deterministically.
- [x] **S69 — `in_zone`.** §4: add `in_zone: { entity, zone }`, watch key `loc:<entity>`. *Driver:* PR-3. *Acceptance:* a Condition can gate content on a zone.
- [x] **S70 — Item transfer, consumption and a trade good.** §6.1: add `give_item`, `remove_item` and `consume_item` Effects and extend `has_item` with quantity; allow a generic trade-good item family (or an author-named item with a documented SRD base). Keep `grant_reward` restricted (Design 23.3 §6.4). *Driver:* PR-5, M10. *Acceptance:* an event transfers a chit or relic to the player, and a milestone requires and consumes a good.
- [x] **S71 — `resolved_when` on a Want.** §2.3 (source list) + §4: add an optional `resolved_when` Condition to `WANT`, so a Want can be resolved by state and not only by an Effect; the guarded World Event pattern (the codex's CP-11) becomes unnecessary. *Driver:* PF-7. *Acceptance:* a Want resolves when its Condition holds, with no watcher event.
- [x] **S72 — The magic-use hook.** §4 or §6.1: either a `magic_used` predicate testable by a World Event, or state that the `WILD_MAGIC` judgement tag (S52) is the chosen mechanism. *Driver:* PR-6, M2. *Acceptance:* a World Event can fire once heavy casting has occurred in a zone, without an author-invented rule.

---

## 3. Roadmap delta (proposed)

For `docs/tasks/`. Each entry cites the spec section that answers "how"; several sections are the amendments above and only exist once applied.

| Task file | Epic | Proposed change | Spec ref |
|---|---|---|---|
| `02 - Deterministic Core.md` | SRD data | **New task: SRD reference reconciliation** (one id convention; migration of the library). | S53 |
| `02 - Deterministic Core.md` | SRD data | **New task: structured material properties** (DR/vulnerabilities by material + coverage). | S54 |
| `02 - Deterministic Core.md` | Progression | **New task (PLAN REQUIRED): class and power table.** Write `docs/srd-analysis/` first; do not prompt until it exists. | S55 |
| `03 - Single-Player Loop.md` | Narrator | **New task: the disclosure gate.** Answer path vs scene path, `reveal_when`, the narrator's validated `disclose` block, egress. Depends on Design 24. | S51, S58, Design 24 §3 |
| `04 - Persistence & World Model.md` | World events | **New task: repeatable/cadenced World Events.** Design 23.3 §6.3 describes them; the schema and executor do not implement them (F1). | 23.3 §6.2–6.3 |
| `04 - Persistence & World Model.md` | World events | **New task: `days_since` and `in_zone`** predicates in the evaluator. | S68, S69 |
| `04 - Persistence & World Model.md` | Ripples | **New task: Engine B executes `payload.effects`** (the outstanding Design 23.3 §7 amendment). | S49 |
| `04 - Persistence & World Model.md` | Knowledge | **New task: the knowledge ledger** + Agent 3 `reveals` capture; `DIALOGUE` milestones complete by disclosure. | S48, S50, S46, Design 24 §4–§5 |
| `04 - Persistence & World Model.md` | Wants | **Change: Want lifecycle semantics** (clock start, `urgent_when`, `fail_want`, death, Major criterion) + `resolved_when`. | S62, S71, S43 |
| `04 - Persistence & World Model.md` | Campaigns | **New task: Campaign start state, outcomes and succession**, guarded behind ADR-0008. | S60, ADR-0008 |
| `05 - Content Pipeline.md` | Author CLI | **New task: `author-cli validate`** and the extended content checks. | S56, S57 |
| `05 - Content Pipeline.md` | Schemas | **New task: the ZONE entity** (schema, index, `in_zone`, validator). | S47, S65, S69 |
| `05 - Content Pipeline.md` | Schemas | **New task: the lore corpus compiler** — chunk extraction, layer, audience resolution, disclosure class, embedding at publish. | Design 24 §2, §6 |
| `05 - Content Pipeline.md` | Schemas | **Housekeeping tasks:** derived Relationship id, `Fact.truth` spelling, reveal-path rules, optional `thread:` label. | S64, S66, S67 |
| `05 - Content Pipeline.md` | Quests | **Change: Quest/Module availability and Quest outcomes.** | S44, S45, S63 |
| `05 - Content Pipeline.md` | Effects | **New task: item transfer/consumption/trade good.** | S70 |
| `05 - Content Pipeline.md` | Manifest | **Change: group-knowledge resolution contract.** | S59 |
| `07 - Monetization & Moderation.md` | Moderation | **Change: egress covers the narrator's structured block.** | S58 |
| `00 - Roadmap Overview.md` | — | Add Design 24 to the phase-order table (its retrieval work is Phase 3/4; its compilation work is Phase 5). | Design 24 |

**Not added to the roadmap:** PR-2's *spec* work (already specified, F1), PF-1 and PF-4 (not requirements), and anything in the register's DT- items whose trigger has not fired.

---

## 4. Proposed ADRs

| ADR | Title | Decision | Status |
|---|---|---|---|
| `0008-campaign-succession-in-one-sandbox.md` | Campaign succession inside one Sandbox | Campaigns chain in one Sandbox through a declared successor and an outcome, keeping the character and the world state | `proposed` |
| `0009-first-class-zone-entity.md` | A first-class `ZONE` entity | Zones become a resolved entity kind with an optional magic descriptor, rather than an unresolved string on other entities | `proposed` |

An ADR for the **two-path disclosure model** (Design 24 §3.2–3.3) was considered and **not** proposed: the decision is forced by the threat model rather than a trade-off between real alternatives. If the owner disagrees, it should get one.

---

## 5. PF- dispositions

| # | Disposition |
|---|---|
| PF-1 | **Closed — not a requirement** (Design 24 §10). The codex owns fragment assembly and km → miles. |
| PF-2 | Amendment **S66**. |
| PF-3 | Amendment **S67a**. |
| PF-4 | **Closed — not a requirement** (Design 24 §10). The codex owns flag declaration. |
| PF-5 | Amendment **S57**. |
| PF-6 | Amendment **S67b**. |
| PF-7 | Amendment **S71**. |

---

## 6. Glossary additions

Proposed terms are listed in **Design 24 §9** (`Lore chunk`, `Disclosure class`, `Reveal path`, `Knowledge ledger`, `Consistency set`). `GLOSSARY.md` owns naming; the owner accepts them in the same change that approves Design 24.

---

## 7. Application record (applied 2026-11-02)

All amendments were applied to `docs/specs/` on **2026-11-02**, together with Design 24's approval, the acceptance of ADR-0008 and ADR-0009, and the roadmap delta in §3. Every amended spec section carries its `S<n>` marker.

| Spec | Amendments applied | Notes |
|---|---|---|
| Design 02 | S42 | Retriever contract + dialogue disclosure (Agent 3) |
| Design 03.2 | S43 | Repeatable/relative-time sources evaluated at `TIME_ADVANCED` |
| Design 04 | S44 | `available_when` / `expires_when`; Module Selector hides |
| Design 04.3 | S45, S46 | Quest `outcomes` / `on_fail` / `on_abandon`; `DIALOGUE` milestones by captured disclosure |
| Design 07 | S47 | `ZONE` node kind; node-kind comment list; ADR-0009 |
| Design 08 | S50, S51 | Agent 3 `reveals` confirmed and widened; narrator `disclose` block (closes Design 23 §14 item 11) |
| Design 09 | S53, S54, S55, S72 | SRD id form; structured DR/vulnerabilities + trade goods; class/power table (**plan required**); engine-recorded magic use backing `magic_used` |
| Design 10 | S56, S57 | `author-cli validate`; content-consistency checks as check 9 |
| Design 16 | S58 | `disclose` block stripped and checked |
| Design 23 | S59, S60, S61, S62, S63, S64 | Group-knowledge contract; Campaign succession (ADR-0008); §8.3 two-path secrecy; Want lifecycle; Quest availability pointer; derived Relationship id. §14 items 10 and 11 marked resolved |
| Design 23.2 | S48, S65, S66, S67 | `DISCLOSURE#<id>` ledger item; `ZONE` in the effective entity set; `Fact.truth` spelling; reveal-path rules + optional `thread:` label |
| Design 23.3 | S68, S69, S70, S71, S72 | `days_since`, `in_zone`, `magic_used` predicates; `give_item`/`remove_item`/`consume_item`; `resolved_when` on WANT |
| Docs (tasks) | §3 | Phase 2 A4–A6; Phase 3 F2, G2; Phase 4 C5, C6, F3–F8; Phase 5 A4–A6, D6, F4; Phase 7 F7; overview cross-cutting note |
| Docs (ADRs) | — | ADR-0008 and ADR-0009 accepted |
| Docs (GLOSSARY) | §6 | *Lore and knowledge* section added |

**Not applied:**

| # | Item | Reason |
|---|---|---|
| S49 | Ripple payload `effects` + Engine B execution | **Already present** when checked (Design 07 §2D and Design 03.2 §3.4 both carry it). Design 23.3 §7's "required amendments (not applied)" note is stale; the *task* remains (Phase 4 C2). |
| S52 | A `WILD_MAGIC` judgement tag | **Withdrawn** — resolved by **S72** instead: casting is a deterministic rules outcome, so the engine records it and the `magic_used` predicate reads it. Judgement tags stay about conduct (Design 23 §5.1.1). |

**Amendments applied:** S42–S72 except S49 (already present) and S52 (withdrawn) — **29 of 31**.

# Design 24 — Lore, Disclosure & the Knowledge Ledger

> **Status:** **DRAFT, not approved** (codex-authored 2026-11-02 from the Hollowfall codex's Step 2d and the Mechanics Gap Register M24, PR-14 to PR-16). This document is a *proposal*; it becomes authoritative only when the platform owner approves it. Field names and predicate lists are **proposed shapes**.
> **Vocabulary:** Terms in **bold** are defined in `GLOSSARY.md`. New terms are proposed in §9.
> **Companions:** [Design 23 — Authored Content Model](Design%2023%20-%20Authored%20Content%20Model.md) (§5.5.1 Facts, §8.2 authored text as untrusted input, §8.3 who sees authored secrets, §10 versioning) · [Design 23.2 — Storage & Schemas](Design%2023.2%20-%20Authored%20Content%20Storage%20%26%20Schemas.md) · [Design 23.3 — Condition & Effect Language](Design%2023.3%20-%20Condition%20%26%20Effect%20Language.md) · Design 02 (NPC) · Design 08 (LLM Agents) · Design 16 (Content Moderation) · Design 07 (Database schemas).
> **Decision records:** none yet. Two open questions in §11 may warrant one (the two-path disclosure model; whether a `sealed` class is worth its complexity).
> **How to read:** §2–§7 are the proposal. §10 lists what is deliberately *not* a requirement. §11 lists what is undecided.

---

## 1. Purpose and scope

Today the runtime knows only what authored **Facts** say. Most of a World's lore is prose: it reaches no NPC agent, and the narrator has no sanctioned source for a player's general questions about the world. Secrecy in play rests on a prompt instruction rather than code (Design 23 §8.3), and a Fact an NPC tells the player in conversation has no recorded disclosure (Design 23 §14 items 10 and 11). This spec closes that gap for a World whose entire knowledge model is layered: every important truth has an official story, a popular myth and a hidden truth, and *who knows what* is the content.

It defines three things:

1. **A Lore corpus** — the compiled, retrievable, audience-scoped form of authored prose lore (PR-14).
2. **Disclosure classes and a code-enforced narrator gate** — how withheld lore reaches the narrator and when it may be said (PR-15).
3. **Disclosure capture and the player's knowledge ledger** — what the player has been told, by whom, on which day, and in which version (PR-16).

### 1.1 Out of scope

| Not building | Why |
|---|---|
| Author-invented mechanics attached to lore | The rules engine stays closed over SRD data (Design 23 §5.3, Design 09). |
| The player *inferring* a secret without being told | Agreed with the codex as out of scope for v1 (Step 2d): the ledger records what was told, not what was deduced. |
| An NPC remembering what the player said to it | Out of scope for v1; episodic memory is Design 04's concern. |
| Prose generation from the corpus on the answer path | The answer path is retrieval and narration over supplied chunks, never free generation from the model's own world knowledge. |
| Gating content by Content Descriptors | Descriptors stay informational (ADR-0007, D1a); disclosure is a separate axis. |

---

## 2. The Lore corpus

### 2.1 What a Lore chunk is

A **Lore chunk** is one retrievable unit of authored prose lore. It is a compiled artefact, not a hand-authored entity.

| Field | Type | Meaning | Source |
|---|---|---|---|
| `id` | `lore_…` | Content-addressed id, stable across versions | compiler |
| `topic` | entity id | The authored note the chunk came from (a `loc_`, `npc_`, `faction_`, `hist_`, … id) | codex |
| `heading` | string | The section within the note (`Summary`, `Details`, `Secrets`, `Folklore`, …) | codex |
| `text` | authored text | The line or clause, token-capped and delimited as untrusted data (Design 23 §8.2) | codex |
| `layer` | enum | `truth` / `official` / `myth` / `rival` — the knowledge layers the codex already records | codex |
| `audience` | groups and tiers | Who in the world could know this, resolved to **NPC ids** exactly as Fact knowledge is (conventions §9.5 of the codex) | codex |
| `disclosure` | enum | `open` / `earned` / `sealed` (§3) | codex |
| `reveal_when` | Condition (optional) | When an `earned` chunk becomes disclosable (§3.4) | codex |
| `subjects` | entity ids | What the chunk is "about", for retrieval and for `resolved_when` style checks | compiler |

**Proposed shape.**

```yaml
kind: LORE
id: lore_hollowfall_choir_seed_site
topic: loc_the_crossing
heading: Secrets
layer: truth
disclosure: sealed
audience: { groups: [wardens_inner], tiers: [inner] }
reveal_when: { event_occurred: evt_crossing_root_found }
subjects: [the_choir, choir-roots-stages, the_crossing]
text: "Beneath the buried wardstone city lies the Choir's seed-site at Stage 1."
```

### 2.2 Where the corpus comes from

The codex already classifies **every** prose section of its vault: 1,525 sections across 330 notes, each with a disclosure class, and 40 notes carry a `## Keystone secrets` section (codex conventions §7). The compiler turns each classified section or clause into one or more chunks. The codex is the authoring side; this document is the runtime side. **How the analysis splits a section into chunks and resolves `_known_by_groups` to NPC ids is unchanged from the codex's own rules** — the platform must not invent its own grouping.

### 2.3 NPC retrieval contract — enforced in the retriever, never in the prompt

1. Return only chunks whose `audience` includes this NPC, **at the layer that NPC believes**. A believer of the myth is handed the myth, not the truth.
2. **An NPC's own Wants are always included** (self-audience), even when it will never say them, because they shape its reaction to the player.
3. No chunk outside the audience is ever placed in the agent's context, so the agent cannot reveal what it was not given. This is the same principle as Design 23 §8.3's Relationship `visibility`.

### 2.4 Narrator retrieval contract

Follows §3.

### 2.5 Caps, delimiters, embedding

Chunks are token-capped, delimited, and labelled as untrusted data (Design 23 §8.2). They are embedded at publish like authored memory seeds and versioned as any authored entity (Design 23 §10). Retrieval depth, chunk size, embedding model and top-k are calibration values, not set here.

---

## 3. Disclosure classes and the narrator gate

### 3.1 The three classes

| Class | The narrator may | The player reaches it by |
|---|---|---|
| `open` | state it whenever relevant (public knowledge) | nothing: it is already known |
| `earned` | foreshadow with atmosphere and rumour, but not state it; may state it once its reveal path has been taken | an earned path: an NPC who knows it tells the player, a check, a found document, an event, or the narrator's own validated choice once `reveal_when` holds |
| `sealed` | never hint beyond the authored `rumor_seeds`; use it only to stay consistent | a specific authored event or Quest (a keystone truth) |

**Fail closed.** An unclassified chunk is treated as `earned`. This matches the codex default and is the safe direction.

### 3.2 The answer path (the hardened one)

When the player **asks** the narrator about the world, or about what they know, the assembled context is `open` chunks **plus the player's ledger** (§5), and nothing else. Withheld chunks are **absent**, not labelled, so a prompt such as "ignore your instructions" cannot extract what was never supplied. This is the whole reason the two paths exist.

### 3.3 The scene path

When narrating a scene, the engine adds only the `earned` and `sealed` items the scene needs for *consistency* — the NPC in the room is a host, the well is a seed-site — and labels them `UNDISCLOSED`. Secrecy there rests on the narrator's output, which must pass the `disclose` validation (§4.2) and the egress check (Design 16 §7). **That is the residual risk**, and the size of the consistency set is open (§11).

### 3.4 `reveal_when`

An optional Condition. Until it holds, the chunk is not even labelled disclosable; once it holds, the narrator may disclose the chunk through a structured, validated `disclose` proposal (§4.2), which keeps the narrator's discretion inside engine bounds. The codex records this in words (`**Reveal when:**`) until the platform accepts the field.

### 3.5 Marking and defaults on the authoring side

The codex owns the authoring rules (its conventions §7.3): a note asks for `disclosure:` in frontmatter, a section may carry a `**Disclosure:**` line, and a note's `Summary` and `Details` state only `open` content. The platform contract is simply: accept a per-chunk class, default to `earned` when absent, and never let an LLM choose it.

---

## 4. Disclosure capture

### 4.1 From NPC dialogue

Agent 3 returns `reveals: [ids]`. The engine accepts an id only if it is in **that NPC's own audience** (what it knows or believes), then records the disclosure in the ledger (§5). This closes Design 23 §14 item 10, and it is what makes a `DIALOGUE` milestone with `fact_revealed` completable by conversation rather than only by an engine-fired `reveal_fact`.

### 4.2 From narration

The narrator returns streamed prose. Proposal: a **trailing, stripped, schema-validated block** (`disclose: [ids]`) on its output, validated against §3 — only `open` chunks, and `earned` chunks whose `reveal_when` holds, are accepted. This is Design 23 §14 item 11, which is undecided there; this spec takes a position and records it here so the two do not diverge. The block affects streaming and the Design 16 egress buffer, so Design 16 §7 and Design 08's narrator section both need the amendment in the companion document.

---

## 5. The knowledge ledger

### 5.1 Rows and fields

A per-Sandbox record of what the player has been told:

| Field | Meaning |
|---|---|
| `id` | The chunk or Fact id |
| `layer` / `version` | **Which version of the truth they were told** (the player may hold a false belief) |
| `source` | An NPC id, a document, an event, or the narrator |
| `day` | The Sandbox day (Design 23 §7) |
| `how` | `told` / `read` / `observed` |

### 5.2 Consumers

The ledger is the single source for `fact_revealed`, for the player's journal, and for the narrator's answers to "what do I know about X?". The latter is an answer-path query (§3.2) and must read the ledger alone.

### 5.3 Idempotency

Recording is idempotent per turn on the `request_id`, the same idiom as judgement tags (Design 23 §5.1.1, ADR-0006): a retried turn records nothing twice.

---

## 6. Storage and versioning

- **Authored side:** compiled chunks are immutable objects in the existing authored-content store, versioned like any entity (Design 23 §10, ADR-0003). No new store.
- **Sandbox side:** the ledger is `sandbox_id`-scoped state. Proposed home: the `FACT` disclosure path already contemplated by Design 07 §2 and Design 23.2, extended to a `DISCLOSURE#` item rather than a second graph. **Where exactly is open (§11)** — reusing the existing disclosure marker is cheaper and is the recommendation.
- Chunks resolve the same unhydrated/hydrated rules as everything else: a chunk edit reaches a Sandbox by the Design 23.4 adoption rules.

---

## 7. Threat model notes

- **Vectors:** the lore corpus is retrieved content, so it inherits Design 23.5's model for authored text as untrusted input. Two additional points:
  - **Indirect injection through lore.** An author (or a compromised World Repository) could embed instructions in a chunk. Chunks are delimited and labelled as data, and the answer path never includes withheld text, which bounds the damage.
  - **The `disclose` block is an integrity surface.** It must be schema-validated, stripped before the player sees the prose, and validated against §3 before acceptance. A malformed or absent block must be treated as "disclosed nothing", never as "disclose everything".
- **The ledger is a confidentiality asset.** It reveals what a player knows; it is `sandbox_id`-scoped.

---

## 8. Acceptance criteria

1. **Two NPCs, one event:** two NPCs asked about the same event answer from different layers according to their group and tier; neither is handed a chunk outside its audience.
2. **No extraction:** with a `sealed` chunk in the corpus, no player prompt can elicit it from the narrator or from an NPC outside its audience. This is the eval set of the codex's Step 14a.
3. **Gated disclosure:** the narrator can disclose an `earned` chunk whose `reveal_when` holds and cannot when it does not.
4. **Dialogue completion:** a `DIALOGUE` milestone with `when: { fact_revealed: … }` completes after an NPC tells the player in conversation.
5. **Ledger provenance:** the ledger shows who said it, on which day, and which version; the narrator answers "what have I learned about X?" from the ledger alone.
6. **Idempotency:** a retried turn records nothing twice.

---

## 9. Vocabulary to add to `GLOSSARY.md`

| Term | Proposed meaning | Avoid |
|---|---|---|
| **Lore chunk** | One retrievable unit of authored prose lore, with a topic, layer, audience and disclosure class | "lore document", "lore item" |
| **Disclosure class** | `open` / `earned` / `sealed`: what the narrator may say about a chunk, and how the player reaches it | "visibility" (already means the authoring/primer axis) |
| **Reveal path** | A single concrete way a chunk becomes disclosable to the player | "unlock" |
| **Knowledge ledger** | The per-Sandbox record of what the player has been told | "journal" (the player-facing view of it) |
| **Consistency set** | The `earned` and `sealed` items the narrator holds while narrating a scene, labelled `UNDISCLOSED` | "secrets context" |

`GLOSSARY.md` owns naming; this table is a proposal.

---

## 10. Not requirements

Recorded so they are not re-opened:

| Item | Position |
|---|---|
| **PF-1** — overland fragments and `distance_km` | The codex owns the fragment assembly and the km → miles conversion (its conventions §9.2–9.3). No platform requirement. |
| **PF-4** — a platform flag-declaration home | The codex declares effect-only flags in its own `world/flags.md` and copies them into the manifest. No platform requirement. |

---

## 11. Open items

| # | Item | Needed before |
|---|---|---|
| 1 | **The consistency set.** How much `earned` and `sealed` truth the narrator holds on the scene path. Too little and scenes are incoherent; too much and the residual risk grows. Proposal: the scene's *cast* (NPCs present), the scene's location and its immediate parents, and the chunk(s) the scene's authored beats cite. | Design 08 narrator amendment |
| 2 | Whether a `sealed` class earns its complexity, or whether `earned` with a stricter `reveal_when` suffices. The codex has 40 notes with keystone sections; the platform must judge the retriever cost. | Spec approval |
| 3 | The ledger's storage home (`DISCLOSURE#` item vs a new table) and whether it merges with the existing Fact `disclosed` marker. | Design 07 / 23.2 amendment |
| 4 | Whether the narrator's structured block can coexist with token streaming, or whether disclosure capture on the scene path is deferred to v2 with `reveal_fact` only. | Design 08 / 16 |
| 5 | The retrieval depth, chunk size, embedding model and top-k; and whether an NPC's chunk retrieval and the narrator's answer-path retrieval share an index. | Calibration (Design 08.1) |
| 6 | Whether the corpus is indexed beside Facts in the content index or in a dedicated one. | Design 23.2 |

---
status: proposed
date: 2026-11-02
---

# Campaigns chain inside one Sandbox through a declared successor

A Sandbox belongs to exactly one Campaign (Design 23 §2) and a Campaign has no start state, no end state and no successor. That is too small for a world designed to be played for hundreds of hours: multiple Campaigns are authored in one World, and a player should carry their character and the world they changed from one into the next.

The proposal is to keep one Sandbox and let Campaigns chain. On `CAMPAIGN`: `start_effects` applied once at `SANDBOX_CREATED`; named `outcomes`, each a Condition; and `follows: camp_x` with a `requires_outcome` and a `transition` Effect list, so the Sandbox adopts the next Campaign at a safe point. Hydrated entities stay frozen (ADR-0002).

## Considered options

- **A new Sandbox per Campaign** — the default today. It discards the world state the player caused, which is the whole point of a persistent world, and it forces character import, which is out of scope (Design 23 §1.1) and breaks `start_level`.
- **One Campaign with Acts** — the interim pattern the codex uses (its CP-10). It keeps the fiction but gives the platform no way to express an ending, an outcome or a successor.
- **Campaign succession in one Sandbox** — this ADR.

## Consequences

- A Sandbox must record its current Campaign and the outcome that carried it there.
- Events already fired must not re-fire; `FIRED#` markers survive succession.
- Migrations of a previous Campaign stay pinned to the entities they touched (Design 23.4).
- The authoring tool must refuse a `follows:` chain with a cycle.

**Implemented in (proposed):** Design 23 §2 and §12 (`CAMPAIGN` start state, outcomes, successor); Design 23.4 (transition timing); Design 23.3 §2.3 (a transition is a source). Requested by the Hollowfall codex as PR-10 (`meta/platform-requests/Amendments & Roadmap Delta.md` S60).

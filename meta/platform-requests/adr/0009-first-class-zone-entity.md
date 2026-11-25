---
status: proposed
date: 2026-11-02
---

# A `ZONE` is a first-class entity, not a string on other entities

`zone_id` already exists as the lazy-hydration unit, but it has no entity kind. Other authored entities (locations, NPCs, conditions) reference `zone_…` ids that nothing defines, and a Condition cannot test whether an entity is inside a zone. The Hollowfall codex's pilot left nine dangling `zone_` references, and every region note in the world needs a magic descriptor (well, knot, eddy, sink, normal) that has nowhere to live.

A `ZONE` (alias `REGION`) kind is proposed: resolvable by the validator, an optional magic/leyline descriptor, and an `in_zone` Condition. Retrieved and versioned like any other authored entity.

## Considered options

- **Keep `zone_id` as an opaque string** — cheapest, but every reference stays unvalidated, and zone-scoped content (magic potency, seed-site stage, the Whisper's audibility) has no home.
- **A `LOCATION` with a self-referencing parent** — reuses the overland graph, but a zone is not a place the player stands in; it is a region that contains places, with its own authored attributes.
- **A first-class `ZONE` kind** — this ADR.

## Consequences

- `zone_id` references become validated rather than dangling.
- The content index and the effective-entity set gain a kind; the compiler and validator both need it.
- Hard numeric magic-potency modifiers stay out (BD-4, DT-3): the descriptor is authored data, and a rules variant would be needed before the engine applies it numerically.

**Implemented in (proposed):** Design 07 §2 (node kinds); Design 23.2 §3.3 and §9 (effective entity set, index); Design 23.3 §4 (`in_zone`) and the scope rule. Requested by the Hollowfall codex as PR-3 (`meta/platform-requests/Amendments & Roadmap Delta.md` S47, S65, S69).

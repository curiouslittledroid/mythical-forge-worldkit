# Platform requests (Step 2c hand-off)

**This folder is the delivery form of the the world's Mechanics Gap Register.** The register is the source; these drafts are what the `mythical-forge` repo ingests. Nothing here is canon and nothing here changes the world: it is a *spec proposal* for the platform, written in the platform's own formats.

## Why not GitHub issues

`mythical-forge` is spec-first. `docs/specs/` is authoritative, `docs/tasks/` is the build order, and issues are used only for PR review findings. New work therefore enters as **spec text**, not as a ticket. The precedent is `docs/design-reviews/Design 23 - Amendments & Roadmap Delta.md`, which recorded amendments **S1–S41** grouped by owning spec plus a **roadmap delta** that was applied to `docs/tasks/`. Step 2c follows that shape.

## The ladder these drafts feed

| Layer | Location (platform) | What lands there |
|---|---|---|
| Spec | `docs/specs/Design NN*.md` | New subsystems and changed behaviour |
| ADR | `docs/adr/NNNN-slug.md` | Hard-to-reverse, surprising, real-trade-off decisions |
| Glossary | `GLOSSARY.md` | New vocabulary (same change that resolves it) |
| Analysis | `docs/srd-analysis/…` | Where a spec hand-waves a data model or algorithm |
| Roadmap | `docs/tasks/NN - *.md` | Phases → Epics → Tasks, each citing spec sections |
| Task prompt | `docs/task-prompts/` | Derived last; never source of truth |

## What is in this folder

| File | What it is |
|---|---|
| `engine-capability-register.md` | **The catalogue, and the dispositions.** Every mechanic a world asked for, classified against what the engine can express, with the PR- and PF- ids the other files here deliver. A platform release lands in this file, so it is the one place to edit when a spec ships. |
| `Design 24 - Lore, Disclosure & the Knowledge Ledger.md` | **New spec draft** for the one genuinely new subsystem (register M24, PR-14 to PR-16). Proposed as `Design 24` (highest existing is `Design 23.5`). |
| `Amendments & Roadmap Delta.md` | **Amendment list and roadmap delta** for the other 20 items (PR-1…PR-13, the PF- items), in the Design 23 format: S-numbered amendments grouped by owning spec, then the proposed Phase → Epic → Task changes. |
| `adr/0008-campaign-succession-in-one-sandbox.md` | Proposed ADR for PR-10 (owner accepts; an agent proposes only). |
| `adr/0009-first-class-zone-entity.md` | Proposed ADR for PR-3. |

## Hand-over sequence

1. **Codex drafts** (this folder). The register gains a `**Spec home:**` line per request.
2. **User reviews** the drafts here and approves what leaves the repo.
3. **Copy into the platform**: the spec into `docs/specs/`, the amendments doc into `docs/design-reviews/`, the ADRs into `docs/adr/` as `status: proposed`, the glossary terms into `GLOSSARY.md`.
4. **The platform owner applies**: approve the spec and amendments, apply them to `docs/specs/`, apply the roadmap delta to `docs/tasks/`, accept or reject each ADR, and answer the PF- items.
5. **Record back** in the register: `**Answer (date):**` per item, the owning spec section, and any class change (a rejected class B becomes a class D reshape). Then Step 2c closes.

## Rules

- **Never edit the platform's specs from here.** These are drafts. The platform applies them.
- **Field names and predicates below are proposed shapes**, as Design 23 marks its own. Anything the codex has not settled is listed in the *Open items* of each document, not silently decided.
- **Cite, do not paraphrase.** Each amendment names the exact section it changes.
- **A claim about the current code was verified against `packages/authored-content` on 2026-11-02**; re-check before applying, and never assert a gate outcome from memory.

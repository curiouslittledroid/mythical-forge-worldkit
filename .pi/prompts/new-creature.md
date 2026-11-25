---
description: "Design new creatures for a region or biome (the Step 10 process: the world's rules first, one cause each, interview, then notes)"
argument-hint: "<region, biome or continent> [how many]"
---
Design creatures for: **$1**. How many: ${2:-3 to 6}.

You are the codex's ecologist and bestiary designer. A creature here is not a "monster of the
week": it is a **consequence** of this world's history, and a reader should be able to work out the
cause from the evidence. Work by the interview method in `AGENTS.md`: propose, wait for the user,
then write.

## 0. Read first (do not skip)
1. `AGENTS.md`, `principles/tone.md` and `principles/originality-guardrails.md` — the world's own
   answers. They outrank anything in this prompt.
2. **Wherever the world keeps its creature rules** — usually `world/creatures/_index.md`, and the
   world's ecology or biome note if it keeps one. **Those are the authority; this prompt only
   sequences them.** If the world has written no creature rules yet, write them there first and come
   back: an unruled bestiary becomes a zoo.
3. The target's own notes: its region or continent note, its magic class, and whatever the world's
   rules name as relevant — its ecology, its leylines, its peoples, its materials.
4. Two or three existing creature notes, for the house style. Skim `world/creatures/` so you do not
   duplicate what is already there.
5. `meta/templates/creature.md` — the note shape, including the sections a creature must have.
6. The engine's library: ask the world's notes which SRD base keys are available, and use only those.
   A creature whose base is missing is `[OPEN]`, not invented.

## 1. Gap analysis (report briefly before proposing)
- **What do the world's rules require of a biome entry?** (Magic class, flora, fauna, hazards — the
  world's list, not one borrowed from another setting.) If the biome entry does not exist, write it
  as part of this work.
- **What does the world's rules say about how fauna follows terrain?** Apply it; do not invent a
  second ecology.
- State what people eat and what eats what in that place, in one or two lines.
- **Count what exists by cause**, using the world's own causes, and keep the mix what the world's
  rules say it should be: mostly mundane, with the strange ones only where the history puts them.
- Check the world's **closed list** — the absences in `principles/originality-guardrails.md`. Do not
  propose anything that breaks it.

## 2. Round 1 — propose seeds (then stop and wait)
Give a table of numbered proposals, each with a recommended answer worded so that "yes" accepts it:

| # | Creature (plain-English placeholder name) | Cause (one, from the world's list) | Where | SRD base (library key or `[OPEN]`) | One-line origin and the **tell** |

Also ask, as numbered questions with recommendations, any decision the biome needs (a new hazard, a
special case, a hook into an existing thread or faction). Ask the whole frontier at once. **Do not
write notes in this round.**

## 3. Write (after the user confirms)
One note per creature in `world/creatures/<slug>.md`, from `meta/templates/creature.md`:
- Frontmatter: `id: mon_<snake_case>`, `kind: CREATURE`, and the status, era, disclosure and tags the
  world's rules prescribe.
- **Summary and Details are the public face**: what a resident of this world could know and say —
  plain names, folk sayings, no insider vocabulary. The world's disclosure rules (the worldkit's
  `docs/conventions.md` §7) say what belongs under `## Secrets` instead.
- The standard Details lines the template lists (the worldkit's `docs/conventions.md` §9.6), then
  three to five bullets: habits, danger, what people do about it, what it is worth.
- `## Secrets` at the disclosure class the world's rules set, `## Hooks` with two hooks, and
  `## Links` back to the creature index and the biome note.
- British spelling unless `vault.spelling` says otherwise; metric units always. **No hit points, AC,
  CR, ability scores or stat blocks** — the engine derives them. If a template is named at all, it is
  the engine's own key.

Then update, each fact in **one home**:
- the biome's own note: its row and its hazards;
- `world/creatures/_index.md`: each creature added to the world's own index table;
- `meta/names.md` for a new placeholder, `meta/open-questions.md` for anything `[OPEN]`;
- `meta/mechanics-gap-register.md` only if the creature needs a mechanic the engine cannot express.

## 4. Check, then report
Run, and fix every failure: `python3 tools/lint.py`, `python3 tools/check_citations.py`, then
`python3 tools/disclosure.py --check` if the world publishes a site, then `python3 tools/site_export.py`
and read `site/audit/latest.json` — a keyword hit or an internal reference on a creature page means a
secret leaked into the open face: fix it at source. Do **not** deploy the site. Commit with a clear
message.

Report: the notes written, how the biome now stands against the world's own rules, the cross-links
added, the open questions, and anything that contradicts the canon (raise it; never silently change
a decision).

## The one rule that is the kit's, not the world's

**Everything here is a consequence of the world's history.** A creature with no cause is a monster;
a creature whose cause a reader can infer from its tell is part of the world. That is the whole
method, and the world's own rules are how it is applied.

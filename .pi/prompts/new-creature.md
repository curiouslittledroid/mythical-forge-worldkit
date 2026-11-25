---
description: "Design new creatures for a region or biome (the Step 10 process: ecology first, one cause each, interview, then notes)"
argument-hint: "<region, biome or continent> [how many]"
---
Design creatures for: **$1**. How many: ${2:-3 to 6}.

You are the codex's ecologist and bestiary designer. Creatures here are not "monsters of the week": each one is a **consequence** of the world's history, and the party should be able to read the cause from the evidence. Work by the interview method in `AGENTS.md`: propose, wait for the user, then write.

## 0. Read first (do not skip)
1. `AGENTS.md` and `principles/tone.md` (the grim dark test).
2. `world/creatures/_index.md` — **the rules live here. They are the authority; this prompt only sequences them.** Also `world/cosmology/ecology.md`.
3. The target's own notes: its region or continent note (`world/places/`), its **magic class**, the leylines (`world/cosmology/leylines.md`, `magic.md`), and `world/cosmology/choir-roots-stages.md` for any seed-site stage there.
4. `world/items-materials/metals.md`, `world/peoples/the-fae.md` and `world/factions/the-lineage.md` if the target touches iron, the fae or the Lineage.
5. A couple of existing creature notes of the cause you expect to use (for the house style). Skim `world/creatures/` for what already exists, so you do not duplicate.
6. SRD library: `/Users/phil/mythical-forge/packages/shared-data/src/data/monsters.json` (the only valid `SRD base` keys; `monster_…` ids).

## 1. Gap analysis (report briefly before proposing)
- Does the biome already have an entry in `ecology.md`? If not, you must write one: **magic class, flora, fauna, three or more monsters, a hazard**.
- Apply the three rules: the **water-hole rule**, **magic class sets the fauna**, and the Choir has its own separate ecology.
- State what people eat and what eats what in that place, in one or two lines.
- Count what exists by **cause** (Adapted, Scar, Choir, Fae/Between, Lineage, Relic). The mix should lean mundane: mostly Adapted, some Scar, and the Choir, Lineage and Relic only where the history puts them there (about one in six at most).
- Check the **Closed list** below. Do not propose anything that breaks it.

## 2. Round 1 — propose seeds (then stop and wait)
Give a table of numbered proposals, each with a recommended answer worded so that "yes" accepts it:

| # | Creature (plain-English placeholder name) | Cause (one) | Where | SRD base (library key or `[OPEN] (PR-4)`) | One-line origin and the **tell** |

Also ask, as numbered questions with recommendations, any decision the biome needs (a new hazard, a special case, a hook into an existing thread or faction). Ask the whole frontier at once. **Do not write notes in this round.**

## 3. Write (after the user confirms)
One note per creature in `world/creatures/<slug>.md`, from `meta/templates/creature.md`:
- Frontmatter: `id: mon_<snake_case>`, `kind: CREATURE`, `name_status: working`, `status: working`, `engine: false`, `era: present`, `disclosure: open`, tags.
- **Summary and Details are the public face**: what a resident of this world could know and say. Plain names and folk sayings. No Choir, Lineage, root, stage or chord vocabulary in the open face.
- Standard Details lines (conventions §9.6): `**SRD base:**` (library key, or `[OPEN] (PR-4)`), `**Nearest SRD 3.5:**` (only when `[OPEN]`, in words), `**Role:**`, `**Cause:**` (omit it for Choir and Lineage: it goes under Secrets), `**Where:**`, `**Tell:**`. Then 3–5 bullets: habits, danger, what people do, folk sayings, trade value.
- `## Secrets` (class `earned`): the true cause, the Choir or fae link, what copper and fire do, any wild-zone mechanism. Under `## Keystone secrets` with `**Disclosure:** sealed` **only** the six keystones in the kit's `conventions.md` §7.4 (for example anything that reveals the Gate-born or the Lineage's purpose).
- `## Hooks` (2), `## Links` (always `[[creatures/_index|Creatures]]` and `[[ecology]]`).
- British spelling. Metric units (a creature's size in metres, not feet). No hit points, AC, CR, ability scores or stat blocks: the engine derives them. A template, if any, is an SRD template key only.

Then update, each fact in **one home**:
- `world/cosmology/ecology.md`: the biome row (or the other-continents row) and the hazards table.
- `world/creatures/_index.md`: add each creature to the **Creatures by cause** table.
- `meta/names.md`: add any new placeholder name; `meta/open-questions.md` for anything `[OPEN]`.
- If a creature needs a library entry that does not exist, leave it `[OPEN] (PR-4)`; do not add to the gap register unless the mechanic is new.

## 4. Check, then report
Run, and fix every failure: `python3 tools/lint.py`, `python3 tools/disclosure.py --check`, then `python3 tools/site_export.py` and read `site/audit/latest.json` (keyword hits and internal references for any creature page mean a secret or a roadmap term leaked into the open face: fix at source). Do **not** deploy the site. Commit with a clear message.

Report: the notes written, the biome coverage now (flora, fauna, three monsters, hazard), cross-links added, open questions, and anything that contradicts the canon (raise it; never silently change a decision).

## Closed list (the rules in short; the full text is in `world/creatures/_index.md`)
- **One cause each:** Adapted, Scar, Choir, Fae/Between, Lineage, Relic. Every note has a one-line origin and a tell.
- **Mundane first.** Scarcity, then hungry gods, then magic, then the Choir. The Choir is the backdrop, not the monster of the week.
- **Water-hole rule.** Dangerous animals live at or between water; dead zones hold only hardy Adapted life, plus Choir, Relic and Lineage things.
- **Magic class sets the fauna:** well draws everything; eddy or wild zone breeds Scar creatures; a sink is a dead zone, and breeds **echoes** only where many died.
- **No clean fixes.** Killing a well-wyrm leaves a sink; burning a root leaves a sink. Victories shift the balance.
- **The dead do not rise** where the lines flow. Echoes (sinks), thread-puppets (near a Choir root) and the Hungered (living people) are the only "undead-like" things. No wights, wraiths, liches or vampires.
- **Dragons are well-wyrms** (about ten, bound to wells, starving). **Giants are the Grown** (the Choir's fruited thralls); ogres are the lesser Grown, trolls are the Rooted.
- **Ordinary fungus exists and nobody eats it.** The Choir's growth is told by its tells, not by being fungal.
- **Originality:** no mind flayers, illithids, gith, beholders, displacer beasts, owlbears by name in the world (use "bramble-bear"), or other protected creatures; no Dark Sun defilers or sorcerer-kings; no Tolkien orcs-as-evil, balrogs or ents. Kobolds, gnolls, bugbears and hobgoblins are not used. Orcs and goblins are peoples, not monsters.
- **Tone:** cruelty is systemic and implied, not lingered on. No on-screen sexual violence. Children are not shown as victims. Beauty is a lure, not a prize.
- **Names:** plain English for what commoners call a thing; an invented word only for ancient things. All names are placeholders until marked final.

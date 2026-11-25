---
id: npc_REPLACE
kind: NPC
title: {{title}}
aliases: []
name_status: working
status: working
engine: false
era: present
tags: []
sources: []
groups: []                   # factions only, e.g. [{ id: faction_example_order, rank: select }]  rank: common | select | inner
race: race_REPLACE           # the people, a codex race id; resolves race-level group knowledge (section 9.5)
home: loc_REPLACE
---

# {{title}}

**Summary:** REPLACE (two or three sentences).

## Details
REPLACE

## Secrets
*(GM-only. Delete this section if there are none. It is `earned` by default; mark a keystone truth with `**Disclosure:** sealed` as the first line. See the kit's `conventions.md` section 7.)*

## Hooks
- REPLACE

## Links
- [[REPLACE]]

## Open questions
- [OPEN] REPLACE

## Engine
*(Rename the info string from `engine-example` to `engine` and set `engine: true` in the frontmatter once the block is real and valid. See the kit's `conventions.md` section 9.)*

```engine-example
kind: NPC
id: npc_example_person
name: Example Person
race: GNOME                       # SRD key
levels: { EXPERT: 3 }             # SRD class keys. Never hand-enter hp, ac, bab or cr.
abilities: { str: 10, dex: 12, con: 11, int: 14, wis: 12, cha: 10 }
alignment: TRUE_NEUTRAL
persona:
  summary: "Short persona for the engine."
  voice_style: "How they speak."
base_disposition: 0
home: loc_example_town
simulation_tier: MINOR
```

```engine-example
kind: WANT                        # a Want lives in its NPC's note
id: want_example_person_goal
npc_id: npc_example_person
priority: 1
desire: "What they want."
stakes: "What happens if they don't get it."
urgent_when: { day_reached: 5 }
deadline_days: 20
on_deadline:
  - { set_flag: { flag: example_goal_failed } }
methods: [PERSUADE, HIRE]
forbidden: [VIOLENCE]
```


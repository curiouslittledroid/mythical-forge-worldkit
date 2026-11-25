---
id: faction_REPLACE
kind: FACTION
title: {{title}}
aliases: []
name_status: working
status: working
engine: false
era: present
tags: []
sources: []
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
kind: FACTION
id: faction_example_order
name: The Example Order
summary: "One or two sentences for the engine."
```

```engine-example
kind: RELATIONSHIP
from: faction_example_order       # a Relationship lives in the note of its 'from' entity
to: faction_example_rival
kind_of: ENEMY_OF                 # closed set: see the kit's conventions.md section 16
sentiment: -60                    # -100..100
visibility: PUBLIC                # PUBLIC | SECRET | { known_by: [npc_...] }
note: "Why, in one line."
```


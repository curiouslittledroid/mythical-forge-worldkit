---
id: loc_REPLACE
kind: SETTLEMENT
title: {{title}}
aliases: []
name_status: working
status: working
engine: false
era: present
tags: []
sources: []
coords: { x: 0, y: 0 }       # km east of the west coast, km north of the south coast
zone: zone_REPLACE
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
kind: OVERLAND_NODE
id: loc_example_town
name: Example Town
type: SETTLEMENT
zone_id: zone_example_region
description: "One or two sentences for the engine. Token-capped."
```

```engine-example
kind: OVERLAND_EDGE
from: loc_example_town
to: loc_example_site
distance_km: 120      # the transformer converts to whole miles
terrain: STANDARD     # STANDARD | DIFFICULT | TRACKLESS
danger: 2             # 0-10
```


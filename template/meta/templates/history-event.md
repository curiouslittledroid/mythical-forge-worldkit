---
id: hist_REPLACE
kind: HISTORY_EVENT
title: {{title}}
aliases: []
name_status: working
status: working
engine: false
era: present
tags: []
sources: []
t0: 0                          # years relative to the Severing (T0)
official: REPLACE
myth: REPLACE
rival: REPLACE
group_knowledge: []           # [{ group: faction_example_order, tier: inner }]  tier: common | select | inner
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
kind: FACT
id: fact_example_truth
text: "The real truth, short."
truth: TRUE
_known_by_groups:                 # transformer directive, resolved to NPC ids and removed
  - { group: faction_example_order, tier: inner }
subjects: [loc_example_town]
authority: LOCKED
```

```engine-example
kind: FACT
id: fact_example_official
text: "The official story, short."
truth: RUMOR
_believed_by_groups:              # transformer directive
  - { group: race_human, tier: common }
believed_as: "How believers hold it."
authority: GUIDED
```


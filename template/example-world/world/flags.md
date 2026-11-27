---
id: topic_world_flags
kind: TOPIC
title: World Flags
name_status: agreed
status: agreed
engine: false
era: present
tags: []
sources: []
---

# World Flags

**Summary:** The world's Author-declared **effect-only flags**. A `set_flag` Effect may name only a flag declared in the block at the bottom of this note, and the transformer copies the block into the generated `manifest.yaml`. What flags are for, the two kinds (effect-only and judgement tag) and the declare → set → test workflow are in the kit's `meta/conventions/conventions.md` section 9.4.

## The demo world's flags

The Ferryman's Debt declares twelve: three terminals, three intent flags the thread's World Events set and its scenarios assert, and the stage and history flags in between. `verify-kit.sh` appends the same list to this block when it builds the throwaway vault, so this note and the fixture cannot disagree.

```flags
- id: ferry_armed
  description: "The Ferryman's Debt thread is live in this Sandbox."
- id: ferry_collect_due
  description: "Intent: the clerk's collection deadline passed."
- id: ferry_s1_seized
  description: "Stage 1: Reed has been seized."
- id: ferry_transit_due
  description: "Intent: the move to the pans is due."
- id: ferry_s2_in_the_pans
  description: "Stage 2: Reed is in the pans at Saltmarch."
- id: ferry_sale_due
  description: "Intent: the sale of Reed's contract is due."
- id: ferry_sold_on
  description: "Terminal (output): Reed's contract was sold on."
- id: ferry_debt_paid
  description: "Terminal (outcome): Reed's debt was paid."
- id: ferry_fled
  description: "Terminal (outcome): Reed left Dustport."
- id: ferry_settled
  description: "History: the paid debt has been recorded and the Wants retired."
- id: ferry_gone
  description: "History: the creditors wrote the debt off and the Wants retired."
- id: ferry_collector_lost
  description: "The clerk is dead and the enforcer finishes his errands."
```

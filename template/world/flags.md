---
id: topic_world_flags
kind: TOPIC
title: World Flags
name_status: working
status: working
engine: false
era: present
---

# World Flags

**Summary:** The world's Author-declared **effect-only flags**. A `set_flag` Effect may name only a
flag declared in the block at the bottom of this note, and the transformer copies the block into the
generated `manifest.yaml`. What flags are for, the two kinds (effect-only and judgement tag) and the
declare → set → test workflow are in the kit's `conventions.md` section 9.4.

## Declared flags

A world starts with none. Add one when a thread needs it: declare it here first, then set it in an
Effect, then test it in a Condition or an `arms` list. A flag nobody reads is dead weight, and the
thread-check reports it.

```flags
[]
```

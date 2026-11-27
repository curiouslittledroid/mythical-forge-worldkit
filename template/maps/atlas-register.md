---
id: topic_atlas_register
kind: TOPIC
title: Atlas Register
name_status: working
status: working
engine: false
tags: []
---

# Atlas Register

**Summary:** The world's map brief: the frames, the sheets, the drawing rules and the corrections
history. The mechanism — the data schema, the commands, the rule that a rendered file is never
edited — is the kit's `meta/conventions/atlas.md`; **this note is the world's decisions.**

## Questions this note answers

1. **What are the frames?** A frame is a coordinate box in km. The YAML declares each one
   (`frames:`), and every entry names the frame it belongs to. Decide the world frame and the local
   frames before drawing anything.
2. **What sheets are there?** One row per plate: its title, paper, scale, grid step and file.
   The sheets are rendered by `tools/local/make_atlas.py`, which is this world's to write.
3. **How is a feature drawn?** The icon, the line style, the label rule, and what a blank space
   means. These are the world's, not the kit's.
4. **What has been corrected?** One numbered row per contradiction found and fixed, with what the
   notes now say. This is the audit trail a later session reads.

## The frames

REPLACE — the world's frames, and why each one exists (a continent, a city, a dungeon level).

## The sheets

REPLACE — one row per plate: `id`, title, frame or window, paper, scale, grid, file.

## Drawing rules

REPLACE — icons, line styles, label placement, and what is deliberately left blank.

## Corrections

REPLACE — numbered rows: what was wrong, what the canon says now, and the date.

## Links

[[maps/_index|Maps]] · `maps/atlas-features.yaml` (the data) · the kit's `meta/conventions/atlas.md`

---
id: topic_site_decisions
kind: TOPIC
title: Site Decisions
name_status: working
status: working
engine: false
tags: []
---

# Site Decisions

**Summary:** The demo world's site vocabularies: which tags earn an index page, which words must never appear on a public page, and which thread names are ordinary vocabulary rather than a spoiler. The mechanism is the kit's `meta/conventions/site.md` section 3.3.

```site-vocabulary
published_tags: [ferry, debt, town]

keystones: []

plot_web_surfaces: []
# The player-facing tone statement (the landing page and About). Ours: it is a promise we make to a
# reader, taken from [[what-to-expect]].
what_to_expect:
  - "The world is broken and stays broken. Your victories decide who survives, not whether the world heals."
  - "Scarcity is the real enemy. Water, food and safety are short, and ordinary people do shameful things to get them."
  - "Magic costs. It is regional and expensive; it takes something from the caster and scars the land."
  - "The gods are real and mostly hungry. Faith is a transaction. The comfort people actually get is from each other."
  - "The horror is quiet. It is usually people, and it is often something you notice before anyone explains it."
  - "Choices are between bad options. There is no clean path. Survival is a legitimate goal."
  - "There is beauty here, and it is usually a trap. There is also real joy - food, music, love, the taste of clean water - and it is worth protecting."

# How our tags read on a page. A tag with no entry falls back to its title-cased slug.
tag_labels:
  choir: The Choir
  gods: The Gods
  fae: The Fae
  ketheri: The Ketheri
  elves: Elves
  dwarves: Dwarves
  gnomes: Gnomes
  humans: Humans
  league: The Crimson League
  wardens: The Wardens of the Stone
  church: The Church of the Giver
  far-reach: The Far Reach
  heartland: The Heartland
  saltmarch: Saltmarch
  waygates: Waygates
  leylines: Leylines
  wardstones: Wardstones
  ruins: Ruins

```

---
id: topic_campaign_authoring_guide
kind: TOPIC
title: Campaign and Thread Authoring Guide
name_status: agreed
status: agreed
engine: false
tags: []
---

# Campaign and Thread Authoring Guide

**Summary:** The step-by-step tutorial for building a **thread**, a **Campaign**, its **Modules** and **Quests**, and every engine block they need. **It is the worldkit's, not this world's.** The text lives in the worldkit at `docs/campaign-authoring-guide.md`; the pinned version is recorded in `TOOLING_VERSION`. This note is the pointer, kept so that links and section citations keep resolving, and so this world can say what is specific to it.

**Where to read it.** The worldkit's `docs/campaign-authoring-guide.md`, by name and section. A wikilink cannot reach another repo, so this note does not link it. **Every section citation in this vault — `4.5`, `4.7`, `6.3`, `Parts 5 to 7` — refers to that copy.**

**Point by name, never by wikilink.** When a note here needs to send a reader to the guide, name the document and the section; do not add a link, and do not restate the guide's rules here.

## What is this world's

| Thing | Where it is |
|---|---|
| The thread pattern the guide implements | `docs/thread-pattern.md` in the worldkit (the reference: the why) |
| The flag register | [[flags\|World Flags]] |
| Which campaigns exist, and where their scenarios run | `campaigns/`; `world.config.yaml` key `vault.scenarios` |
| The demo thread itself | [[the-ferrymans-debt]] |

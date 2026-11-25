---
id: npc_tomas_reed
kind: NPC
title: Tomas Reed
aliases: []
name_status: working
status: working
engine: true
era: present
tags: []
race: race_human
groups: [{ id: faction_dust_ferrymen, rank: common }]
home: loc_dustport
---

# Tomas Reed

**Summary:** A Dustport ferryman three months behind on his water-chits, and the thread's debtor.


## Engine
```engine
kind: NPC
id: npc_tomas_reed
name: Tomas Reed
alignment: NEUTRAL_GOOD
race: HUMAN
levels: { EXPERT: 3 }
abilities: { str: 12, dex: 13, con: 12, int: 11, wis: 12, cha: 10 }
skill_ranks: { PROFESSION: 6, SWIM: 4 }
persona:
  summary: "A Dustport ferryman who poles stores out to the stranded ships. He is three months behind on his water-chits."
  voice_style: "Slow, dry, apologises before he asks."
base_disposition: 10
home: loc_dustport
```

```engine
kind: WANT
id: want_reed_clear_his_debt
_thread: ferry
npc_id: npc_tomas_reed
priority: 1
desire: "Clear his water-debt before the clerk comes for him."
stakes: "He has no plan. The clerk has a deadline."
urgent_when: { flag_set: { flag: ferry_armed } }
methods: [PERSUADE, HIRE, STEAL, FLEE]
forbidden: []
resolution_paths: [quest_ferry_pay_the_debt, quest_ferry_smuggle_him_out, quest_ferry_buy_him_back]
authority: OPEN
```

```engine
kind: RELATIONSHIP
from: npc_tomas_reed
to: faction_dust_ferrymen
kind_of: MEMBER_OF
sentiment: 50
visibility: PUBLIC
note: "A guild ferryman for nineteen years."

```

```engine
kind: RELATIONSHIP
from: npc_tomas_reed
to: faction_ferry_creditors
kind_of: OWES
sentiment: -30
visibility: PUBLIC
note: "Three months of water-chits."

```


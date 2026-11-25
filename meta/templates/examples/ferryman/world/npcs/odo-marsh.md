---
id: npc_odo_marsh
kind: NPC
title: Odo Marsh
aliases: []
name_status: working
status: working
engine: true
era: present
tags: []
race: race_human
groups: [{ id: faction_ferry_creditors, rank: select }]
home: loc_dustport
---

# Odo Marsh

**Summary:** The creditors' clerk who collects Reed's debt, and the thread's clock.


## Engine
```engine
kind: NPC
id: npc_odo_marsh
name: Odo Marsh
alignment: LAWFUL_EVIL
race: HUMAN
levels: { EXPERT: 4, ROGUE: 2 }
abilities: { str: 11, dex: 13, con: 12, int: 14, wis: 12, cha: 13 }
persona:
  summary: "The creditors' clerk who collects bad water-debt in Dustport. Courteous, patient, never raises his voice."
  voice_style: "Mild and exact. Calls every debtor 'friend'."
base_disposition: -10
home: loc_dustport
```

```engine
kind: WANT
id: want_marsh_collect_reed
_thread: ferry
npc_id: npc_odo_marsh
priority: 1
desire: "Collect Tomas Reed's overdue water-debt, or take the man."
stakes: "A debtor who walks free teaches the others they can."
urgent_when:
  all:
    - { flag_set: { flag: ferry_armed } }
    - { not: { flag_set: { flag: ferry_collect_due } } }
deadline_days: 25
on_deadline:
  - { set_flag: { flag: ferry_collect_due } }
methods: [PERSUADE, HIRE, THREATEN]
forbidden: []
```

```engine
kind: WANT
id: want_marsh_deliver_reed
_thread: ferry
npc_id: npc_odo_marsh
priority: 2
desire: "Deliver the seized debtor to the pans at Saltmarch."
stakes: "A seized man is a loose end until his contract is sold."
urgent_when:
  all:
    - { flag_set: { flag: ferry_s1_seized } }
    - { not: { flag_set: { flag: ferry_transit_due } } }
deadline_days: 30
on_deadline:
  - { set_flag: { flag: ferry_transit_due } }
methods: [PERSUADE, HIRE]
forbidden: [VIOLENCE]
```

```engine
kind: WANT
id: want_marsh_sell_the_contract
_thread: ferry
npc_id: npc_odo_marsh
priority: 2
desire: "Sell the debtor's contract to a buyer who asks no questions."
stakes: "A contract unsold is a debt unpaid."
urgent_when:
  all:
    - { flag_set: { flag: ferry_s2_in_the_pans } }
    - { not: { flag_set: { flag: ferry_sale_due } } }
deadline_days: 40
on_deadline:
  - { set_flag: { flag: ferry_sale_due } }
methods: [PERSUADE, HIRE]
forbidden: [VIOLENCE]
```

```engine
kind: RELATIONSHIP
from: npc_odo_marsh
to: faction_ferry_creditors
kind_of: SECRETLY_SERVES
sentiment: 60
visibility: SECRET
note: "He presents himself as a private notary."

```


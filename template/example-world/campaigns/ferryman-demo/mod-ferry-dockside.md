---
id: mod_ferry_dockside
kind: MODULE
title: Module - Dockside
aliases: []
name_status: working
status: working
engine: true
era: present
tags: []
---

# Module - Dockside

**Summary:** The opening Module: two quests that end the debt before the clerk acts.


## Engine
```engine
kind: MODULE
id: mod_ferry_dockside
title: "Dockside"
target_level_min: 1
target_level_max: 3
key_locations: [loc_dustport, loc_vigil]
key_npcs: [npc_tomas_reed, npc_odo_marsh]

```

```engine
kind: QUEST
id: quest_ferry_pay_the_debt
_thread: ferry
title: "Stand Surety"
giver_npc_id: npc_tomas_reed
from_want: want_reed_clear_his_debt
level_recommendation: 1
milestones:
  - milestone_id: ms_ask
    type: DIALOGUE
    description: "Ask the ferrymen's guild to stand surety for Reed."
    when: { flag_set: { flag: ferry_armed } }
    next_milestone: ms_agree
  - milestone_id: ms_agree
    type: DIALOGUE
    description: "Settle the terms with the clerk."
    when: { edge_exists: { from: faction_dust_ferrymen, kind: GUARDS, to: npc_tomas_reed } }
    next_milestone: COMPLETED
on_complete:
  - { set_flag: { flag: ferry_debt_paid } }
  - { add_edge: { from: faction_dust_ferrymen, kind: GUARDS, to: npc_tomas_reed, sentiment: 60, visibility: PUBLIC } }
  - { resolve_want: want_reed_clear_his_debt }
  - { adjust_disposition: { npc: npc_tomas_reed, toward: PLAYER, delta: 25 } }
  - { grant_reward: { xp: { table: SRD_QUEST_XP, size: MODERATE } } }
```

```engine
kind: QUEST
id: quest_ferry_smuggle_him_out
_thread: ferry
title: "Smuggle the Ferryman Out"
giver_npc_id: npc_tomas_reed
from_want: want_reed_clear_his_debt
level_recommendation: 1
milestones:
  - milestone_id: ms_plan
    type: DIALOGUE
    description: "Plan the way out with Reed."
    when: { flag_set: { flag: ferry_armed } }
    next_milestone: ms_go
  - milestone_id: ms_go
    type: DELIVER
    description: "Get Reed to Vigil."
    when: { in_location: { entity: npc_tomas_reed, location: loc_vigil } }
    next_milestone: COMPLETED
on_complete:
  - { set_flag: { flag: ferry_fled } }
  - { resolve_want: want_reed_clear_his_debt }
  - { grant_reward: { xp: { table: SRD_QUEST_XP, size: MODERATE } } }
```


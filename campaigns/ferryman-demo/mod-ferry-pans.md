---
id: mod_ferry_pans
kind: MODULE
title: Module - The Pans
aliases: []
name_status: working
status: working
engine: true
era: present
tags: []
---

# Module - The Pans

**Summary:** Unlocked when Reed is seized: a site with two rooms, an encounter and a ledger page, and two quests.


## Engine
```engine
kind: MODULE
id: mod_ferry_pans
title: "The Pans"
target_level_min: 1
target_level_max: 4
key_locations: [loc_saltmarch]
key_npcs: [npc_tomas_reed, npc_idra_vance]

```

```engine
kind: QUEST
id: quest_ferry_buy_him_back
_thread: ferry
title: "Buy Him Back"
giver_npc_id: npc_odo_marsh
from_want: want_reed_clear_his_debt
level_recommendation: 2
milestones:
  - milestone_id: ms_find
    type: DIALOGUE
    description: "Find which buyer holds Reed's contract."
    when: { edge_exists: { from: faction_ferry_creditors, kind: CONTROLS, to: npc_tomas_reed } }
    next_milestone: ms_page
  - milestone_id: ms_page
    type: FETCH
    description: "Take the ledger page that proves the debt was padded."
    when:
      all:
        - { fact_revealed: fact_ferry_debt_was_padded }
    next_milestone: ms_deal
  - milestone_id: ms_deal
    type: DIALOGUE
    description: "Settle with the creditors."
    when:
      { not: { edge_exists: { from: faction_ferry_creditors, kind: CONTROLS, to: npc_tomas_reed } } }
    next_milestone: COMPLETED
on_complete:
  - { set_flag: { flag: ferry_debt_paid } }
  - { remove_edge: { from: faction_ferry_creditors, kind: CONTROLS, to: npc_tomas_reed } }
  - { resolve_want: want_reed_clear_his_debt }
  - { reveal_fact: fact_ferry_creditors_sell_debtors }
  - { reveal_edge: { from: npc_odo_marsh, kind: SECRETLY_SERVES, to: faction_ferry_creditors } }
  - { fail_want: want_marsh_deliver_reed }
  - { fail_want: want_marsh_sell_the_contract }
  - { grant_reward: { xp: { table: SRD_QUEST_XP, size: MAJOR } } }
```

```engine
kind: QUEST
id: quest_ferry_the_ledger_page
_thread: ferry
title: "The Padded Ledger"
giver_npc_id: npc_tomas_reed
from_want: want_reed_clear_his_debt
level_recommendation: 2
milestones:
  - milestone_id: ms_search
    type: FETCH
    description: "Search the creditors' tally-house for the ledger page."
    when: { has_item: { item: item_ferry_ledger_page } }
    next_milestone: COMPLETED
on_complete:
  - { reveal_fact: fact_ferry_debt_was_padded }
  - { grant_reward: { xp: { table: SRD_QUEST_XP, size: MODERATE } } }
```

```engine
kind: ROOM
id: room_ferry_tally_house
module_id: mod_ferry_pans
title: "The Tally-house"
lighting: SHADOWY
description:
  authority: GUIDED
  initial: "A low reed-roofed counting-house at the pans. Tally-sticks hang in bundles from the rafters, and a clerk's stool stands by a locked cabinet."
  detailed: "Salt has crusted every sill. The cabinet's hinges are new."
exits:
  - { direction: SOUTH, target_room_id: room_ferry_cellar, door_state: LOCKED, lock_dc: 15 }
size: { width_ft: 30, height_ft: 20 }
layout:
  legend: { "#": wall, ".": floor, "S": { door: SOUTH }, "c": { object: obj_ferry_cabinet } }
  grid:
    - "######"
    - "#.c..#"
    - "#....#"
    - "###S##"
objects:
  - object_id: obj_ferry_cabinet
    name: "The clerk's cabinet"
    interactable: true
    actions:
      - trigger: OPEN
        check_required: { skill: OPEN_LOCK, dc: 15 }
        success_text: "Among the tally-sticks lies a ledger page in a neat hand."
        spawn_items: [item_ferry_ledger_page]
```

```engine
kind: ROOM
id: room_ferry_cellar
module_id: mod_ferry_pans
title: "The Cellar"
lighting: DARK
description:
  authority: GUIDED
  initial: "A brine cellar under the counting-house, where the creditors keep the contracts they have not yet sold."
exits:
  - { direction: NORTH, target_room_id: room_ferry_tally_house, door_state: OPEN }
size: { width_ft: 20, height_ft: 20 }
```

```engine
kind: ENCOUNTER
id: enc_ferry_clerks
module_id: mod_ferry_pans
trigger: { in_location: { entity: PLAYER, location: room_ferry_cellar } }
monsters:
  - { monster: srd_warrior_guard, count: 2 }
tactics: DEFEND_POSITION
treasure: { table: SRD_BY_LEVEL }
authority: GUIDED
```

```engine
kind: ITEM
id: item_ferry_ledger_page
base: srd_parchment
name: "A padded ledger page"
description: "A page of the creditors' ledger, in a clerk's hand, showing water billed to Tomas Reed that was never drawn."

```


---
id: camp_ferry_demo
kind: CAMPAIGN
title: The Ferryman's Debt (teaching Campaign)
aliases: []
name_status: working
status: working
engine: true
era: present
tags: []
---

# The Ferryman's Debt (teaching Campaign)

**Summary:** The teaching Campaign for the [[campaign-authoring-guide]]. It arms one thread and has two Modules.

## Details
- **Arms:** `ferry_armed`, in the overlay's genesis event.
- **Modules:** [[mod-ferry-dockside]] (opening) and [[mod-ferry-pans]] (unlocked when Reed is seized).
- **Pace:** the overlay shortens the collect-Want to 15 days.


## Engine
```engine
kind: CAMPAIGN
id: camp_ferry_demo
world_id: world_ferry_demo
title: "The Ferryman's Debt"
summary: "A teaching Campaign: a ferryman owes the creditors, and the party decides how the debt ends."
start_level: 1
start_day: 0
start_location: loc_dustport
opening_module: mod_ferry_dockside
content_descriptors: [MATURE_THEMES]
modules: [mod_ferry_dockside, mod_ferry_pans]
unlocks:
  mod_ferry_pans: { flag_set: { flag: ferry_s1_seized } }
```


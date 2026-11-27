---
id: overlay_ferry_demo
kind: OVERLAY
title: Overlay (ferry demo)
aliases: []
name_status: working
status: working
engine: true
era: present
tags: []
---

# Overlay (ferry demo)

**Summary:** The teaching Campaign's overlay: a genesis event and one pace override.


## Engine
```engine
kind: CAMPAIGN_OVERLAY
id: overlay_ferry_demo
campaign_id: camp_ferry_demo
adds:
  - kind: WORLD_EVENT
    id: evt_ferry_demo_genesis
    _thread: ferry
    scope: MACRO
    origin: loc_dustport
    when:
      all:
        - { day_reached: 0 }
        - { not: { flag_set: { flag: ferry_armed } } }
    then:
      - { set_flag: { flag: ferry_armed } }
    truth: "The Ferryman's Debt thread is live at Dustport."
overrides:
  want_marsh_collect_reed:
    deadline_days: 15
```


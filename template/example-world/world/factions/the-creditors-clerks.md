---
id: faction_ferry_creditors
kind: FACTION
title: The Creditors' Clerks
aliases: []
name_status: working
status: working
engine: true
era: present
tags: []
---

# The Creditors' Clerks

**Summary:** The consortium's collection office.


## Engine
```engine
kind: FACTION
id: faction_ferry_creditors
name: The Creditors' Clerks
summary: "The consortium's collection office. It binds defaulters and sells their contracts on."

```

```engine
kind: RELATIONSHIP
from: faction_ferry_creditors
to: faction_dust_ferrymen
kind_of: RIVAL_OF
sentiment: -20
visibility: PUBLIC
note: "The guild resents the creditors' collections."

```


---
id: thread_ferry
kind: THREAD
title: The Ferryman's Debt
aliases: []
name_status: working
status: working
engine: true
era: present
tags: []
thread: ferry
interface: { class: resolvable, arms: [ferry_armed], reads: [], sets: [ferry_sold_on, ferry_debt_paid, ferry_fled], terminals: [evt_ferry_settled, evt_ferry_gone, evt_ferry_sold_on], inputs_from: [], outputs_to: [] }
---

# The Ferryman's Debt

**Summary:** A small **Resolvable** teaching thread: a ferryman's water-debt, a clerk with a deadline, and three ways it ends. It is the worked example of the [[campaign-authoring-guide]]. It is **not canon**.

## Premise
Tomas Reed, a Dustport ferryman, is three months behind on his water-chits. The creditors' clerk, Odo Marsh, has 25 days to collect or take the man. Left alone, Reed is seized on the quay, carried to the pans at Saltmarch and sold on. **Class: Resolvable.** The idle terminal is **sold on**; the other terminals are **debt paid** and **fled**.

## Actors and successors
| Role | Primary | Successor if removed |
|---|---|---|
| Collector | [[odo-marsh]] | [[idra-vance]], the enforcer (`evt_ferry_collector_replaced`) |
| Debtor | [[tomas-reed]] | none: a dead debtor ends the thread (the Wants fail) |
| Surety | [[the-dust-ferrymen]] | none |

## The state graph
| State | Entered when | What changes | Exits |
|---|---|---|---|
| **S0 Armed** | a Campaign sets `ferry_armed` | Marsh's collect-Want starts (25 days) | Seized, Paid, Fled |
| **S1 Seized** | `evt_ferry_seized`: nobody stood surety in time | creditors CONTROL Reed | In the pans, Paid (buy him back) |
| **S2 In the pans** | `evt_ferry_transit` (30 days) | Reed moves to Saltmarch | Sold on, Paid |
| **Sold on** *(idle terminal, output)* | `evt_ferry_sold_on` (40 days) | `ferry_sold_on`; the thread closes | the buyer (a later thread's problem) |
| **Paid** *(terminal)* | a Quest sets `ferry_debt_paid` | `evt_ferry_settled` retires the Wants | |
| **Fled** *(terminal)* | a Quest, or `evt_ferry_missing` (Reed left Dustport unscripted) | `evt_ferry_gone` retires the Wants | |

## Interface
| | Flags |
|---|---|
| **Armed by** | `ferry_armed` |
| **Sets (outputs)** | `ferry_sold_on`, `ferry_debt_paid`, `ferry_fled` |
| **Terminal events** | `evt_ferry_settled`, `evt_ferry_gone`, `evt_ferry_sold_on` (each must leave no Want of this thread running) |

## Quest contracts
| Outcome | Contract (`on_complete` effects) | Retires |
|---|---|---|
| Stand surety (before the seizure) | set `ferry_debt_paid`; add `Guild GUARDS Reed` | resolves `want_reed_clear_his_debt` |
| Smuggle him out (before the seizure) | set `ferry_fled` | resolves `want_reed_clear_his_debt` |
| Buy him back (after the seizure) | set `ferry_debt_paid`; remove `Creditors CONTROLS Reed`; reveal a Fact | resolves `want_reed_clear_his_debt`; fails the delivery and sale Wants |

## Links
[[tomas-reed]], [[odo-marsh]], [[idra-vance]], [[the-dust-ferrymen]], [[the-creditors-clerks]]

## Engine
### Facts
```engine
kind: FACT
id: fact_ferry_debt_was_padded
text: "Reed's debt is padded: the creditors billed him for water that the Moot's own sluice-log shows was never drawn."
truth: TRUE
known_by: [npc_odo_marsh]
subjects: [npc_tomas_reed]
authority: GUIDED
```

```engine
kind: FACT
id: fact_ferry_creditors_sell_debtors
text: "The creditors do not wait for debts to be paid. They sell defaulters' contracts on to the buyers at the pans."
truth: TRUE
_known_by_groups:
  - { group: faction_ferry_creditors, tier: inner }
believed_by: [npc_tomas_reed]
believed_as: "A seized debtor works off his chits in the pans and is let go."
subjects: [faction_ferry_creditors]
authority: LOCKED
```

### World Events
```engine
kind: WORLD_EVENT
id: evt_ferry_seized
scope: REGIONAL
origin: loc_dustport
when:
  all:
    - { flag_set: { flag: ferry_armed } }
    - { flag_set: { flag: ferry_collect_due } }
    - { not: { flag_set: { flag: ferry_s1_seized } } }
    - { npc_alive: npc_tomas_reed }
    - { in_location: { entity: npc_tomas_reed, location: loc_dustport } }
    - { not: { edge_exists: { from: faction_dust_ferrymen, kind: GUARDS, to: npc_tomas_reed } } }
    - { not: { flag_set: { flag: ferry_debt_paid } } }
then:
  - { set_flag: { flag: ferry_s1_seized } }
  - { add_edge: { from: faction_ferry_creditors, kind: CONTROLS, to: npc_tomas_reed, sentiment: -50, visibility: SECRET } }
truth: "No one stood surety in time. The clerk seizes Tomas Reed on the quay, with his papers in order."
rumor_seeds: ["They say the clerk has taken a ferryman for his chits."]
propagation: { propagates: true, speed_days_per_node: 2, decay: 0.8 }
known_by: [npc_odo_marsh]
```

```engine
kind: WORLD_EVENT
id: evt_ferry_transit
scope: REGIONAL
origin: loc_dustport
when:
  all:
    - { flag_set: { flag: ferry_armed } }
    - { flag_set: { flag: ferry_transit_due } }
    - { not: { flag_set: { flag: ferry_s2_in_the_pans } } }
    - { edge_exists: { from: faction_ferry_creditors, kind: CONTROLS, to: npc_tomas_reed } }
then:
  - { set_flag: { flag: ferry_s2_in_the_pans } }
  - { move_npc: { npc: npc_tomas_reed, to: loc_saltmarch } }
truth: "The seized ferryman is taken to the salt-pans at Saltmarch to work off his debt."
known_by: [npc_odo_marsh]
```

```engine
kind: WORLD_EVENT
id: evt_ferry_sold_on
scope: MACRO
origin: loc_saltmarch
when:
  all:
    - { flag_set: { flag: ferry_armed } }
    - { flag_set: { flag: ferry_sale_due } }
    - { not: { flag_set: { flag: ferry_sold_on } } }
    - { edge_exists: { from: faction_ferry_creditors, kind: CONTROLS, to: npc_tomas_reed } }
then:
  - { set_flag: { flag: ferry_sold_on } }
  - { remove_edge: { from: faction_ferry_creditors, kind: CONTROLS, to: npc_tomas_reed } }
  - { fail_want: want_reed_clear_his_debt }
truth: "The creditors sell Reed's contract on. Whoever buys it does not keep ferrymen."
known_by: [npc_odo_marsh]
```

```engine
kind: WORLD_EVENT
id: evt_ferry_missing
scope: REGIONAL
origin: loc_dustport
when:
  all:
    - { flag_set: { flag: ferry_armed } }
    - { flag_set: { flag: ferry_collect_due } }
    - { not: { flag_set: { flag: ferry_s1_seized } } }
    - { not: { flag_set: { flag: ferry_fled } } }
    - { npc_alive: npc_tomas_reed }
    - { not: { in_location: { entity: npc_tomas_reed, location: loc_dustport } } }
    - { not: { flag_set: { flag: ferry_debt_paid } } }
then:
  - { set_flag: { flag: ferry_fled } }
truth: "Tomas Reed is gone from Dustport before the clerk's deadline. Nobody says where."
known_by: [npc_odo_marsh]
```

```engine
kind: WORLD_EVENT
id: evt_ferry_settled
scope: REGIONAL
origin: loc_dustport
when:
  all:
    - { flag_set: { flag: ferry_armed } }
    - { flag_set: { flag: ferry_debt_paid } }
    - { not: { flag_set: { flag: ferry_settled } } }
then:
  - { set_flag: { flag: ferry_settled } }
  - { resolve_want: want_reed_clear_his_debt }
  - { fail_want: want_marsh_collect_reed }
  - { fail_want: want_marsh_deliver_reed }
  - { fail_want: want_marsh_sell_the_contract }
truth: "The debt is paid. The clerk closes the file, and does not forget the name."
known_by: [npc_odo_marsh]
```

```engine
kind: WORLD_EVENT
id: evt_ferry_gone
scope: REGIONAL
origin: loc_dustport
when:
  all:
    - { flag_set: { flag: ferry_armed } }
    - { flag_set: { flag: ferry_fled } }
    - { not: { flag_set: { flag: ferry_gone } } }
then:
  - { set_flag: { flag: ferry_gone } }
  - { fail_want: want_reed_clear_his_debt }
  - { fail_want: want_marsh_collect_reed }
  - { fail_want: want_marsh_deliver_reed }
  - { fail_want: want_marsh_sell_the_contract }
truth: "With the debtor gone, the creditors write him off. The debt stays on the books."
known_by: [npc_odo_marsh]
```

```engine
kind: WORLD_EVENT
id: evt_ferry_collector_replaced
scope: REGIONAL
origin: loc_dustport
when:
  all:
    - { flag_set: { flag: ferry_armed } }
    - { not: { npc_alive: npc_odo_marsh } }
    - { not: { flag_set: { flag: ferry_collector_lost } } }
    - { not: { flag_set: { flag: ferry_sold_on } } }
    - { not: { flag_set: { flag: ferry_settled } } }
    - { not: { flag_set: { flag: ferry_gone } } }
then:
  - { set_flag: { flag: ferry_collector_lost } }
  - { set_flag: { flag: ferry_collect_due } }
  - { set_flag: { flag: ferry_transit_due } }
  - { set_flag: { flag: ferry_sale_due } }
  - { move_npc: { npc: npc_idra_vance, to: loc_dustport } }
truth: "The clerk is dead. The creditors send an enforcer, who closes every open errand at once."
known_by: [npc_idra_vance]
```


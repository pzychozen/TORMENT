# TORMENT Memory Substrate — Phase 7G5A3D4 Archaeology

## SRG enumeration order and collision durability

Status: architecture ruling required; no native mutation implementation.

This document records the mandatory A3D4 pre-implementation findings.  It
does not change production SRG behavior, native routing, or storage.

## A. Exact legacy enumeration order

`MemoryGraph.entities` is a Python insertion-ordered dictionary.  The SRG
collision loop consumes that order directly and replaces its selected candidate
only when similarity is strictly greater than the current best value.

For ordinary production creation, `SeedWorld` assigns monotonically increasing
EIDs and `spawn_memory()` inserts each entity once.  Therefore fresh normal
creates enumerate in creation/EID order.  `update_payload()` (including the
Fabric reinforcement path) appends a new JSONL record but does not remove or
reinsert the dict entry, so it preserves that order.  An aborted unflushed
entity is removed from the live dict; its EID is not reused, and a later
current memory appends after the surviving entries.

On process reload, `MemoryGraph._load()` walks `nodes.jsonl` linearly.  The
first record for an EID inserts its dict slot; later records for that EID update
the same slot in place because last record wins.  Consequently the complete
rule is:

```text
current-memory enumeration order
= first appearance order of each surviving EID in nodes.jsonl
```

It is not a generic ascending-EID rule.  A valid JSONL sequence whose first
records are EID 42 then EID 7 reconstructs `[42, 7]`; a later EID-42 record
updates EID 42 without moving it.  Equal-similarity SRG ties therefore select
the first qualifying EID under this precise order.

## B. Exact legacy SRG collision durability

The production collision site runs after the incoming memory has been
`flush_node()`-committed.  It directly mutates:

```text
existing_entity.payload["srg"]
own_entity.payload["srg"]
own_entity.payload["srg_collision"]
```

It does not call `update_payload()` or `flush_node()`.  The subsequent
post-write runtime tail does not flush either collision entity, and
`MemoryGraph.close()` releases storage handles only.

The focused characterization creates two committed, colliding SRG memories,
runs the actual `_run_srg_collision` path, confirms both live payload updates
and the collision report, closes the graph, and reloads it through the real
JSONL path.  Reloaded payloads retain their pre-collision SRG values and have
no `srg_collision` report.

```text
SRG_LEGACY_DURABILITY_SEMANTICS = process-local at the collision site
```

An unrelated later legacy payload write could incidentally persist the current
in-memory values, but none is part of the collision path.  That incidental
possibility is not a durable collision guarantee.

## Decision

A native immutable payload successor would make a successful collision durable
immediately, including new current revisions and representation-continuity
work.  That would materially strengthen legacy semantics.  A3D4 therefore
stops before implementing either native SRG mutation or the enumeration-based
SRG rewrite that would depend on its publication topology.

An explicit architecture ruling is required to choose between preserving the
process-local semantic, making legacy collision updates durable in a separately
authorized phase, or defining another approved cross-backend publication
model.  No arbitrary payload mutation primitive is introduced by this phase.

## Guard artifact

`tests/test_srg_memorygraph_archaeology.py` locks the observed fresh/create,
update, reload, JSONL current reconstruction, aborted-unflushed, and actual
collision close/reload behaviors.

```text
A3D4_SRG_ARCHAEOLOGY = COMPLETE
SRG_ENUMERATION_ORDER = QUALIFIED
SRG_LEGACY_DURABILITY_SEMANTICS = PROCESS_LOCAL_AT_COLLISION_SITE
SRG_NATIVE_MUTATION_CONTRACT = BLOCKED
SRG_DURABILITY_SEMANTICS_REQUIRE_ARCHITECTURE_RULING = YES

DEFAULT_FABRIC_BEHAVIOR_CHANGED = NO
NATIVE_ACTIVE = NO
DUAL_WRITE = NO
DUAL_READ = NO
CUTOVER_OPENED = NO
AUTHORITY_EXPANDED = NO
NATIVE_POST_WRITE_ADAPTER = NO
A3D_NATIVE_ROUTE_WIRED_INTO_FABRIC = NO
A3D_END_TO_END_FABRIC_ROUTE = BLOCKED
```

# TORMENT Memory Substrate — Phase 7G5A3D5

## Ordered transient SRG runtime boundary

Status: qualified in isolation. Production remains on the legacy Fabric path.

## Durable compatibility order

Phase A3D4 established that current legacy SRG enumeration is the first
appearance order of each surviving EID in `nodes.jsonl`, not numeric EID
order. No prior native fact carried that meaning: EID aliases are unordered,
revision ordinals identify revisions rather than runtime membership, and an
admission candidate's selected line is its last current record.

Schema v1.2 therefore adds the immutable structural carrier:

```text
memory_runtime_enumeration_orders
    legacy_source_namespace_id
    object_id
    runtime_ordinal
```

It has one namespace/object entry and one namespace/ordinal entry. It is not
payload, governance, provenance, an EID, a revision ordinal, or a
representation generation. It is published in the same semantic transaction
as compatibility-memory creation; legacy node admission calculates it from
the source's surviving first-appearance order. A native core must be
explicitly upgraded from v1.1 to v1.2. Opening a v1.1 core does not add the
carrier or silently change the core.

`NativePostWriteMemoryAccess.list_current()` exposes only a tuple of detached
current runtime views ordered by this carrier. It fails closed if aliases,
orders, current memory identities, or memory kinds disagree. It does not
append unqualified memory by EID, UUID, row order, or timestamp.

## SRG effective state

The collision consumer now receives exactly four backend-neutral capabilities:

```text
ordered current-memory enumeration
qualified current embedding read
effective SRG state
process-local SRG collision mutation
```

It preserves the legacy selection rules: current-EID exclusion, state and
embedding eligibility, near-zero skip, `best_similarity = 0.0`, strict `>`
candidate replacement, first-qualified-order tie selection, `>= 0.75`, and
the unchanged `collision()` band rule.

Legacy mutation is still direct live `SeedEntity.payload` mutation with no
collision-site flush. Native mutation is held only in a per-provider in-memory
overlay, internally witnessed against the exact native current revision from
which it was derived. A durable successor observed beneath an overlay fails
closed; no stale overlay is applied or rebased. Neither provider publishes a
revision, representation, operation, transition, governance fact, provenance
record, relationship, or temporary SQLite state for collision evolution.

A new native provider models restart and exposes the durable payload baseline
again. The qualification covers a nonascending-EID `[42, 7]` order and equal
similarities, proving that the first structural ordinal wins rather than the
numeric EID.

## Remaining materialization boundary

An independently qualified later durable successor may need to materialize an
effective native SRG overlay exactly where legacy would serialize a live
payload. A3D5 does not invent that successor-materialization operation and
does not modify A3C3 reinforcement semantics.

```text
SRG_DYNAMIC_STATE_CLASS = PROCESS_LOCAL_RUNTIME_OVERLAY
SRG_COLLISION_DURABLE_NATIVE_REVISION = NO
MEMORY_ENUMERATION_CONTRACT = QUALIFIED
SRG_TRANSIENT_OVERLAY_MATERIALIZATION_READY = NO
SRG_COLLISION_NATIVE_POST_WRITE_READY = YES

DEFAULT_FABRIC_BEHAVIOR_CHANGED = NO
NATIVE_ACTIVE = NO
DUAL_WRITE = NO
DUAL_READ = NO
CUTOVER_OPENED = NO
NATIVE_POST_WRITE_ADAPTER = NO
A3D_NATIVE_ROUTE_WIRED_INTO_FABRIC = NO
A3D_END_TO_END_FABRIC_ROUTE = BLOCKED
```

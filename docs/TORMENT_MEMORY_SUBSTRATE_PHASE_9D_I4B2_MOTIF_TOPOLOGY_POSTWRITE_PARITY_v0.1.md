# TORMENT Memory Substrate — Phase 9D I4B-2

## Motif topology and bounded post-write parity

**Status:** uncommitted offline qualification artifact for mandatory adversarial
review. This document is not a production activation, real-root contact, or
component-retirement decision.

**Frozen base:** `ce97dc418543fdc867d9edf7f9d845aec3b8ecea`.

**Scope:** the private native-public reachable attach-triggered true split, its
durable precommit residue/recovery/order facts, and the qualified `CREATED_NEW`
motif prefix selected for that result. Shared public ingest is not claimed by
the current native-public capability boundary. I4B-2 does not qualify shared
two-stage true-split parity and prevents shared requests from entering the
private-qualified I4B precommit path. Conflict, broad SRG successor work,
Hivemind, world, Character, checkpoint, compression/deep, proposals, bridges,
archive, and general post-write activation remain outside this slice.

```text
TRUE_SPLIT_REPRESENTATION = TWO_STAGE_EXISTING_SCHEMA
TRUE_SPLIT_I4B2_SCOPE = PRIVATE_NATIVE_PUBLIC_ONLY
I4B1_PRECOMMIT_EXTERNAL_OWNER_SCOPE = PRIVATE_QUALIFIED
SHARED_TRUE_SPLIT_I4B2_QUALIFICATION = NOT_CLAIMED
SHARED_POSTWRITE_DISPATCH = PRESERVED_WHEN_SEPARATELY_REACHED
SHARED_PRECOMMIT_EXTERNAL_OWNER_RESTORATION_REQUIRED = YES
SCHEMA_CHANGE_REQUIRED = NO
GLOBAL_OUTBOX_REQUIRED = NO
MOTIF_FORMULA_CHANGE_REQUIRED = NO
POST_WRITE_FORMULA_CHANGES_REQUIRED = NO
TORMENT_MATHEMATICS_PRESERVED = YES
POST_WRITE_NON_MOTIF_TAIL_MIGRATED = NO
RETIREMENT_ALLOWED = NO
REAL_PRODUCTION_ACTIVATION = NOT_AUTHORIZED
```

## Legacy archaeology

The relevant legacy path is `TormentFabric.ingest` followed by
`LegacyMotifRuntimeAdapter.attach_or_create`, which delegates to
`MotifRegistry.attach_or_create`.

For an existing selected motif, the legacy causal order is:

```text
incoming graph memory is spawned (not yet canonical JSONL-flushed)
  -> embed-audit observer
  -> selected parent receives ordinary attach state and incoming EID
  -> first motif-registry save
  -> MOTIF_ATTACH event append
  -> auto-split policy evaluates the now-attached parent
  -> parent is rewritten as cluster 0
  -> child is created as cluster 1
  -> second motif-registry save of the complete parent/child topology
  -> MOTIF_SPLIT event append
  -> symbol/resonance precommit work
  -> primary graph flush (canonical boundary)
```

`MotifRegistry._maybe_split_motif` changes the already-attached parent's
member list, centroid, strength and activity timestamp; creates a child with
the policy's cluster-1 centroid and membership list; preserves the existing
parent contributing agents/stability on the child; and calls `save()` once for
the completed split topology. It delegates the numerical partition to the
frozen `decide_motif_auto_split` owner. The native slice reuses that decision,
the existing attach-state realization, the existing state payload shape, and
the existing runtime reader. It changes neither formula nor tie rule.

The legacy process dictionary retains the parent at its existing insertion
position when Stage B adds the child. A newly created child follows normal
dictionary/live creation order. A fresh process loads current motif IDs in
lexical recovery order. No persistent live-order table exists or is added.

### Source failure denominator

`TRUE_SPLIT_FAILURE_STAGE_COUNT = 5` is the number of meaningful source
execution seams, not the number of coherent durable residue classes:

| Seam | Source boundary | Coherent restart residue | Native evidence/disposition |
|---|---|---|---|
| S0 | Stage-A parent mutation/save fails before it commits | T0 | reservation becomes `ABORTED`; no I4B2 motif operation/child |
| S1 | Stage-A `MOTIF_ATTACH` event append or interruption after its save | T1 | stored Stage-A operation supplies the frozen plan; retry executes Stage B |
| S2 | Stage-B topology save/transaction fails | T1 | Stage-B SQLite transaction rolls back; Stage A remains durable |
| S3 | Stage-B `MOTIF_SPLIT` event append or response loss after topology save | T2 | recover Stage-B operation outputs; do not rerun split math |
| S4 | primary canonical flush fails after Stage B | T2 + aborted primary | final parent/child persist; primary becomes noncanonical `ABORTED` |

Physical partial/truncated JSON while a legacy `json.dump()` is interrupted is
not a coherent semantic topology state. It is legacy corruption, not a native
state to recreate in SQLite.

## Native representation and residue

The existing atomic `split_motif_with_member()` remains unchanged for its
existing callers. It cannot express this precommit causal history because it
expects a candidate that is not yet a current parent member. I4B-2 therefore
adds two bounded operations over the existing operation, motif, object, and
membership tables:

```text
NATIVE_I4B2_PRECOMMIT_SPLIT_ATTACH
  Stage A: attach the PENDING incoming object to the selected parent.

NATIVE_I4B2_PRECOMMIT_SPLIT_FINALIZE
  Stage B: rewrite parent, create child, retire/recreate moved memberships,
  and publish final topology atomically.
```

Stage A's canonical operation intent contains the request identity, parent
object and expected predecessor revision, attached successor state, incoming
object, final parent/child states, moved existing members,
`candidate_in_child`, and child runtime ID. It also retains the exact
precommit enrichment context and original duplicate-path outcome truth needed
after recovery. No pending embedding, new schema table, queue, or alternate
canonical source operation is created.

```text
PENDING_PRIMARY_MEMORY_HAS_QUALIFIED_REPRESENTATION = NO
CANONICAL_SOURCE_OWNER = EXISTING_NATIVE_FABRIC_NEW_MEMORY_SOURCE_OPERATION
```

| Residue | Durable topology | Primary state | Retry/restart law |
|---|---|---|---|
| T0 — before Stage A | no changed parent membership; no child | reservation later aborted | ordinary planning is lawful only because no motif operation committed |
| T1 — Stage A | parent contains the incoming PENDING/failed object; no child | PENDING, then possibly ABORTED | recover the Stage-A intent and execute exact Stage B; never re-plan against the mutated parent |
| T2 — Stage B | final parent plus child and redistributed memberships | PENDING, then canonical `EXISTS` or `ABORTED` | recover exact Stage-B outputs for parent/child outcome; never infer it from membership scanning |

If `candidate_in_child` is true, Stage B retires the Stage-A candidate
membership and creates the child membership. If false, the Stage-A candidate
relationship remains current and Stage B does not duplicate it. Existing moved
members retain their relationship identity through one `RETIRED` successor and
one child relationship.

The primary outcome taxonomy is intentionally unchanged. A motif-stage error
raises `PRECOMMIT_MOTIF_ATTACH_FAILURE_RAISED`; the finer S0–S4/T0–T2 fact is
separate durable/evidence detail. After T2 plus canonical failure, no motif
rollback occurs: the primary is `ABORTED`, noncanonical and unqueryable, while
the consumed EID remains restart-stable under the I4B-1 identity-safety rule.

## Replay and order

| Situation | Authority | Result |
|---|---|---|
| retry after only reservation | existing precommit reservation | no Stage-A witness exists, so bounded ordinary planning may run |
| retry/restart after committed Stage A while the primary remains `PENDING` | Stage-A canonical intent/output | recover the frozen plan and finalize Stage B without a changed-catalog replan |
| retry/restart after a Stage-B exception has aborted the primary | abort operation | abort recovery returns the frozen failure; it does not perform a fresh Stage-B finalization |
| retry after Stage B before canonical result/response | Stage-B operation outputs | exact parent/child result is recovered without split math |
| canonical source recovery | Stage-B operation outputs plus source operation | `motifs == (parent, child)`, `created_motif is None` |
| aborted-primary recovery | Stage-B operation outputs plus abort operation | exact final topology is reported, primary remains noncanonical |

```text
LIVE_ORDER_PARENT = RETAINS_EXISTING_POSITION
LIVE_ORDER_CHILD = APPEND_AFTER_SUCCESSFUL_STAGE_B_ONLY
LIVE_ORDER_STAGE_B_FAILURE = NO_CHILD_APPEND
LIVE_ORDER_RESTART = LEXICAL_CURRENT_RUNTIME_IDS
```

The recovered Stage-A path now appends its child immediately after successful
Stage B, matching the initial path. This is process-local only and adds no
ordering persistence or tie rule.

## Created-motif truth

`created_motif` is a route-owned semantic fact; it is not derived from the
first affected motif.

| Route outcome | `motifs` | `created_motif` |
|---|---|---|
| ordinary `CREATE_NEW` motif | new motif | new runtime motif ID |
| ordinary attach | existing parent | `None` |
| attach-triggered true split | parent, child | `None` |
| reinforcement | none | `None` |

The recovery route reconstructs this from the durable operation kind/outputs.
The currently supported shared direct-ingest path projects the same route-owned
fact: shared `CREATE_NEW` reports its new motif, while shared
`ATTACH_EXISTING` reports `created_motif is None` even though `motifs` remains
nonempty. This compatibility correction does not qualify shared I4B-2
two-stage topology or post-write parity.

## Bounded post-commit motif tail

The I4B-2 execution profile is selected only for a successful private
native-public true-split `CREATED_NEW` primary result. It does not run the
broad private core-staging `run()` sequence. Its ordered and independently
fail-soft prefix is:

```text
NativeMotifMaintenanceAdapter.update_entropy_and_suggest
  -> merge suggestion workflow
  -> qualified auto-merge when the policy enables it
  -> NativeDerivedMemoryRuntime.maybe_emit_identity_anchor
  -> NativeDerivedMemoryRuntime.refine_identity_anchors
  -> stop
```

If the bound motif runtime is absent, the complete bounded tail is a no-op:
it performs no maintenance, identity-anchor emission, or identity-anchor
refinement. When the motif runtime is present, maintenance retains the existing entropy formula, merge candidate iteration,
stable equal-sim ordering, threshold/max-attempt/keep-drop laws, and the
external `motif_events.jsonl`/merge-suggestion owner. It does not move those
records into SQLite. Each of maintenance, anchor emission, and anchor
refinement catches and logs its own failure; a tail failure cannot invalidate
the already canonical primary.

The anchor boundary is deliberately narrow:

```text
ANCHOR_MOTIF_PARITY =
    BOUNDED_TO_EXISTING_DERIVED_CREATE_AND_N02_LIFECYCLE_SUCCESSOR
SRG_SUCCESSOR_EXPANSION = NO
UNQUALIFIED_SAME_ENTITY_SRG = STRUCTURALLY_REFUSED
```

The tail cannot invoke conflict, SRG collision, Hivemind, mood drift, world,
trajectory, Character, checkpoint, compression/deep, proposal, bridge, or
archive owners. It does not call the broad
`_run_motif_maintenance_and_anchors()` helper because that helper continues
into `maybe_emit_mood_drift`.

| Primary disposition | I4B-2 motif tail |
|---|---|
| private `CREATED_NEW` true split | runs the bounded motif/anchor prefix |
| shared true-split-shaped witness reaching the native post-write adapter | existing shared post-write dispatch; I4B-2 tail is not selected. This does not claim a shared native-public precommit route |
| `REINFORCED_EXISTING` | skipped |
| ordinary `NO_WRITE` | may reach its established general handoff; I4B-2 motif consumers skipped |
| canonical primary failure | executor returns before any post-write adapter/tail |

## Zero-member law

No I4B-2 path adds a `member_count > 0` liveness predicate. A true split
operates on the policy's nonempty two-way partition; it neither deletes nor
normalizes existing certified zero-member motifs. Existing zero-member
centroid, strength, stability, gravity and domain-geometry behavior remains
owned by the already-qualified reader/projection paths.

## Offline evidence

All evidence uses temporary native SQLite cores or synthetic public roots,
writable pytest bases outside the repository, and the `torment` Conda
environment. No service, provider, real root, Brainvision, or unrelated
cognitive function was used.

| Evidence | Coverage |
|---|---|
| `tests/test_p9d_i4b1_primary_precommit_parity.py` | private T0/T1/T2, source and aborted recovery, replay disposition, child/parent candidate contracts, transactional Stage-B rollback, created-motif truth, live/restart order |
| `tests/test_substrate_native_post_write_runtime.py` | private motif-only owner exclusion, null-motif-runtime no-op, independently fail-soft M1/anchor slots, REINFORCE/NO_WRITE tail exclusion |
| `tests/test_p9d_i4b1f_public_outcome_parity.py` | actual full private native-public true-split CREATE, handoff, and motif-only profile |
| shared public/direct post-write regressions | shared public route excludes the private-qualified I4B precommit opt-in; separately, existing shared post-write dispatch and route-owned `created_motif` remain reachable |
| `tests/test_substrate_derived_memory.py` | existing N02 identity-anchor lifecycle successor/replay contract |
| motif/runtime/zero-member/regression suites | formula, merge, reader, and zero-member preservation regressions |

## Bounded verdicts

```text
P9D_I4B2_MOTIF_TOPOLOGY_POSTWRITE_PARITY = PASS (offline bounded scope)
TRUE_SPLIT_PRECOMMIT_PARITY = PASS_PRIVATE_NATIVE_PUBLIC_ONLY
TRUE_SPLIT_NATIVE_PARITY = PASS_PRIVATE_NATIVE_PUBLIC_ONLY
TRUE_SPLIT_FAILURE_RESIDUE_PARITY = PASS_PRIVATE_NATIVE_PUBLIC_ONLY
TRUE_SPLIT_RESTART_PARITY = PASS_PRIVATE_NATIVE_PUBLIC_ONLY
TRUE_SPLIT_COGNITIVE_EFFECT_PARITY = PASS_PRIVATE_NATIVE_PUBLIC_ONLY
TRUE_SPLIT_FAILURE_STAGE_COUNT = 5
TRUE_SPLIT_FENCE = RETIRED_BY_QUALIFIED_PRIVATE_NATIVE_PUBLIC_PARITY
SHARED_TRUE_SPLIT_I4B2_QUALIFICATION = NOT_CLAIMED
SHARED_POSTWRITE_DISPATCH = PRESERVED_WHEN_SEPARATELY_REACHED
SHARED_PRECOMMIT_EXTERNAL_OWNER_RESTORATION_REQUIRED = YES
MOTIF_LIVE_ORDER_SPLIT_SCOPE = PASS
MOTIF_LIVE_ORDER_SPLIT_PARITY = PASS
POSTCOMMIT_MOTIF_MAINTENANCE_PARITY = PASS (private bounded true-split CREATED_NEW prefix)
POSTCOMMIT_MOTIF_FAILURE_DISPOSITION = PASS
REINFORCEMENT_MOTIF_TAIL_EXCLUSION = PASS
NO_WRITE_MOTIF_TAIL_DISPOSITION = PASS
CANONICAL_FAILURE_MOTIF_TAIL_DISPOSITION = PASS
ZERO_MEMBER_MOTIF_PARITY = PRESERVED
ANCHOR_MOTIF_PARITY = BOUNDED_TO_EXISTING_DERIVED_CREATE_AND_N02_LIFECYCLE_SUCCESSOR
MOTIF_REPLAY_MODEL = QUALIFIED_BOUNDED
POST_WRITE_FORMULA_CHANGES_REQUIRED = NO
TORMENT_MATHEMATICS_PRESERVED = YES
POST_WRITE_NON_MOTIF_TAIL_MIGRATED = NO
RETIREMENT_ALLOWED = NO
REAL_PRODUCTION_ACTIVATION = NOT_AUTHORIZED
```

## Future shared-scope prerequisite

```text
I4C_SHARED_SCOPE_PREREQUISITE =
    Do not infer shared precommit parity from the frozen private I4B-1
    receipts. Before any shared native-public activation or qualification that
    crosses the precommit route, restore and qualify the complete shared
    external-owner sequence explicitly.

SHARED_PRECOMMIT_EXTERNAL_OWNER_RESTORATION_REQUIRED = YES

The future proof must cover applicable spawn observation, symbol-state
ownership, resonance/external-owner behavior, and embed-audit dirty behavior.
It must also reconcile true-split fencing without suppressing already-qualified
shared post-write behavior. This is a prerequisite only; it does not authorize
or require I4C implementation when I4C remains private-scoped.
```

## Explicit exclusions

```text
CONFLICT_PERSISTENCE = NOT_MIGRATED
SRG_COLLISION_OR_SUCCESSOR_EXPANSION = NOT_MIGRATED
HIVEMIND_COLLECTIVE = NOT_MIGRATED
WORLD_TRAJECTORY = NOT_MIGRATED
CHARACTER_DRIFT_GRAVITY_REFLEX = NOT_MIGRATED
CHECKPOINT_COMPRESSION_DEEP = NOT_MIGRATED
PROPOSAL_BRIDGE_ARCHIVE = NOT_MIGRATED
```

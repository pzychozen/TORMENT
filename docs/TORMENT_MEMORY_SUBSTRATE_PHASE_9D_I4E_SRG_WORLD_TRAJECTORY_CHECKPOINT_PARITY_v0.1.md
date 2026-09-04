# TORMENT Memory Substrate — Phase 9D I4E

## SRG, world, trajectory, and checkpoint parity for the bounded private native-public route

**Status:** frozen bounded qualification artifact. This is not an activation,
a shared-route claim, a migration of external artifacts to SQLite, a new
exactly-once mechanism, a new Hivemind owner, or a retirement decision.

**Frozen implementation base:** `d68b1682ba5d60c5851d210641b43d6a5fa9df28`.

```text
I4E_SCOPE = BOUNDED_PRIVATE_NATIVE_PUBLIC
I4E_IMPLEMENTATION_SHAPE = SINGLE_BOUNDED_SLICE
I4E_ADVERSARIAL_REVIEW = FAIL_INITIAL / CORRECTED
I4E_DELTA_REVIEW = PASS
I4E_READY_TO_FREEZE = YES
I4E_FROZEN = YES
CONFLICT_READ_PARITY = FROZEN_PRESERVED
SHARED_I4E_PARITY = NOT_CLAIMED
SHARED_PRECOMMIT_EXTERNAL_OWNER_RESTORATION_REQUIRED = YES
HIVEMIND_BROAD_PRIVATE_EXTERNAL_OWNER = RETAINED
HIVEMIND_NEW_SCOPE = EXCLUDED
SQLITE_SHADOW_STATE = NO
EXACTLY_ONCE_CLAIM = NO
RETIREMENT_ALLOWED = NO
REAL_PRODUCTION_ACTIVATION = NOT_AUTHORIZED
```

The durable correction record is:

```text
initial adversarial review -> FAIL
bounded correction pass    -> implemented
focused delta review       -> PASS
```

## Archaeology and fit decision

The successful legacy post-write order is:

```text
CREATED_NEW only
  -> contradiction -> SRG collision -> Hivemind -> motif/anchors/mood
all successful post-write outcomes
  -> world -> Character -> checkpoint -> compression -> proposal -> bridges
```

The private native adapter already had qualified conflict, SRG, process-local
world, Character, and frozen derived seams, but a real private external
trajectory binding and a private checkpoint binding were absent. The true-split
continuation also ended after Character. I4E can fit the qualified reader and
legacy writer without a new table, global transaction, or shared-owner reuse:

```text
I4E_IMPLEMENTATION_SHAPE = SINGLE_BOUNDED_SLICE

SRG                    -> retained transient native owner
world                  -> retained NativeWorldProcessState owner
trajectory evidence    -> new, separately named private external binding
checkpoint             -> new, separately named private external binding
```

The binding pair is deliberately complete: a private I4E configuration rejects
trajectory without checkpoint, checkpoint without trajectory, a missing
binding, a non-private trajectory root, or a format that differs from the
current legacy selection. This is a composition guard, not atomicity. Each
writer remains independently fail-soft after canonical storage.

Hivemind is an existing external owner in the ordinary broad private
`CREATED_NEW` path. It has no causal input into the I4E targets: its
created-only routine reads current/local facts and appends collective packet or
proposal evidence; it does not mutate SRG, world, trajectory, Character, or
checkpoint inputs. I4E retains that qualified call and profile authority
unchanged. It adds no Hivemind call to the private true-split path, and makes no
new Hivemind ownership claim. Compression is after checkpoint and does not feed
its snapshot inputs; it remains outside this slice.

```text
HIVEMIND_ORDER_DEPENDENCY = INDEPENDENT_FOR_I4E_AND_RETAINED_BROAD_PRIVATE
POST_CHECKPOINT_COMPRESSION_DEPENDENCY = INDEPENDENT_FOR_I4E_AND_EXCLUDED
```

## Owner, identity, and durability map

| Surface | Qualified owner and identity | Durable truth / restart disposition |
|---|---|---|
| SRG collision | `NativeSRGProcessState`, keyed by native core, source namespace, EID, and current revision | Process-local overlay only. The current native payload remains unchanged unless an already-authorized exact successor materializes it. A fresh runtime returns durable baseline state. |
| SRG successor | Existing R2 reinforcement and frozen N02 identity-anchor lifecycle | `SRGSuccessorMaterialization` validates the exact predecessor revision and is acknowledged only after that successor is current. I4E adds no new successor category. |
| World | `NativeWorldProcessState` keyed by native core and source namespace | `SeedWorld` position, velocity, trail, history, liveness, and classification overlay are process-local. Fresh reconstruction starts from current qualified source payload and has no fabricated born-step/channel facts. |
| World diagnostics | Same process owner; existing R2/N02 typed successor path only | `traj_label` and `traj_last_classify_step` remain overlay facts until an existing exact successor accepts them. I4E creates no diagnostic SQLite shadow. |
| Private trajectory | `NativePrivateTrajectoryEvidenceProcessState`, keyed by native core + legacy private source namespace, binds `NativePrivateTrajectoryEvidenceBinding` to one `NativeTrajectoryEvidenceRuntime` | External only at `workspaces/<workspace>/agents/<agent>/private`; V2 uses the existing genesis/step/event writer and legacy mode uses `TrajectoryLogger`. The writer remains open across request adapters and is sealed only when its process/agent owner closes. It has no SQLite or canonical-memory authority. |
| Checkpoint | `NativePrivateCheckpointSnapshotBinding` plus the existing `save_checkpoint` writer | External only at `workspaces/<workspace>/agents/<agent>/private/checkpoints`. Snapshot files are non-authoritative convenience/recovery evidence; no load participates in routing or native recovery. |

The distinct shared D3/D4 bindings remain separate and unclaimed. The I4E
private binding rejects the shared domain root rather than treating an external
artifact format as common ownership.

## SRG writer/reader reconciliation

The frozen reader continues to consume `effective_srg_state`: current durable
payload first, with the current exact process overlay where present. The legacy
collision writer's selection law remains unchanged: enumerate current memories
in existing order, skip self/non-SRG/absent-or-zero-vector candidates, normalize
the dot product, take the first strict-best candidate, and use the existing
threshold. Neither threshold, tie behavior, candidate order, query ordering,
nor SRG mathematics changed.

```text
CREATED_NEW/private/qualified EID -> retained SRG collision call
REINFORCED_EXISTING               -> no collision call
NO_WRITE                          -> no collision call
canonical failure                 -> no post-write call
```

The historical durable boundary is preserved exactly:

```text
same process collision  -> effective overlay is visible immediately
restart before successor -> durable baseline; overlay/report absent
R2 or frozen N02 exact successor -> may serialize the authorized contribution
```

This is lawful reader/writer parity, not a durable collision claim. I4E does
not create a fake persistence record, recover a lost overlay, or invent a
general materialization route.

## Exact composition and outcome gates

For the ordinary private public adapter, the I4E slots preserve the existing
created-only and all-outcome partition:

```text
CREATED_NEW
  -> conflict -> SRG -> retained existing Hivemind -> retained motif/anchors/mood
  -> private world + external trajectory
  -> Character
  -> external checkpoint when legacy cadence is due
  -> pre-existing proposal boundary (unchanged; not I4E-qualified)

REINFORCED_EXISTING / NO_WRITE
  -> private world + external trajectory
  -> Character
  -> external checkpoint when legacy cadence is due
  -> pre-existing proposal boundary (unchanged; not I4E-qualified)

canonical failure
  -> no route witness and no I4E post-write owner
```

For an eligible private `CREATED_NEW` true split, I4E extends only the
previously qualified continuation:

```text
conflict -> SRG -> I4B-2 M1/anchor prefix -> I4D mood
-> private world + external trajectory -> Character -> external checkpoint
-> STOP
```

The true-split route omits Hivemind, compression, proposal, and bridges. Its
reinforcement and ordinary no-write paths still perform no true-split tail
work. Shared dispatch remains separate and is not inferred from this order.

The qualification profile is the authoritative admission boundary; route
composition determines which admitted slot is causally present on a particular
route. Therefore the selected true-split profile may declare Hivemind
`QUALIFIED` while its deliberately bounded continuation makes no newly-added
Hivemind call. The broad private route preserves the existing call; I4E does
not migrate a new I4F Hivemind/collective scope.

World first attempts V2 genesis only for `CREATED_NEW`, then advances physics
exactly once and writes the external step evidence. A trajectory runtime
construction failure or a genesis failure cannot suppress that advance: the
adapter selects the no-evidence world advance when construction fails, and the
same evidence-enabled advance when genesis fails. Legacy mode preserves its
existing no-op genesis behavior and per-entity step logging. Classification
remains at the legacy 50-step cadence after the physics step. Evidence step and
classification-event failures are independently soft inside the world runtime,
so Character and checkpoint remain reachable.

Checkpoint keeps its legacy gate exactly:

```text
owner._checkpoint_enable
and step > 0
and step % owner._checkpoint_interval == 0
```

It is after Character on every successful storage disposition. Motif-summary,
character-state, and filesystem/serialization reads retain their independent
soft boundaries. The established private
`workspaces/<workspace>/agents/<agent>/private/embeddings/manifest.json` is
read through `build_shard_snapshot`; absent, unreadable, or invalid manifests
produce `shard_snapshot = None`. The snapshot contains only the established
fields: version, step/time, model state, corridor monitor, kernel runtime
context, Character state, motif summary, and shard snapshot. It intentionally
does not claim SRG, world, trajectory, conflict, proposal, or bridge state as
checkpoint authority.

For V2, successful evidence frames retain the legacy last-observed step and
frame sequence in the external trajectory runtime. Native currently has no
qualified kinematic-reset mutation path, so I4E does not invent an
`ENTITY_KINEMATIC_RESET` call or a new reset owner.

## Failure, replay, and restart disposition

| Case | Preserved disposition |
|---|---|
| SRG collision error | Existing broad collision boundary is soft; source remains canonical and later independent slots run. |
| Trajectory construction or genesis error | The external failure is soft; exactly one native world physics advance still occurs, then Character/checkpoint remain reachable. |
| Evidence step or classification-event error | The world runtime catches the external error after physics; primary storage and subsequent Character/checkpoint work remain reachable. |
| Evidence root/format disagreement at external acquisition | It may degrade to the no-evidence world advance. World physics remains authoritative process-local behavior; trajectory remains external best-effort evidence. |
| World error | The native world boundary is soft. It cannot roll back primary storage or suppress Character/checkpoint. |
| Checkpoint component error | Missing/failing motif or Character component omits that snapshot part where the established writer allows it. |
| Checkpoint writer/containment error | Caught at the checkpoint post-write boundary; source, world, and earlier external evidence remain. |
| Public receipt replay | Existing public receipt replay returns its completed receipt without tail re-entry. I4E adds no replay key or receipt protocol. |
| Direct/recovery re-entry after incomplete tail | No exactly-once guarantee. The legacy-source world step is non-idempotent and advances again when re-entered; external evidence may receive another attempt. |
| Restart | SRG/world overlays and live world history are lost to their durable baseline; external trajectory/checkpoint files remain non-authoritative. |

The direct I4E test runs the same `NO_WRITE` context twice and observes a
second world step. This is intentional source behavior, not a defect hidden by
idempotency. Checkpoint filenames retain the existing step replacement and
retention behavior. No transaction spans native canonical storage, process
state, trajectory evidence, and checkpoint files.

## Implementation and evidence

Production composition is limited to:

```text
NativePostWriteQualificationProfile.core_staging_with_i4e_private_tail()
NativePrivateTrajectoryEvidenceBinding
NativePrivateCheckpointSnapshotBinding
NativePrivateTrajectoryEvidenceProcessState
NativeFabricPostWriteAdapter private/true-split composition
NativePublicTormentRuntime private configuration
```

There is no change to SRG collision math, native query order, world physics,
trajectory format selection, checkpoint serialization, source operation
identity, shared bindings, or any core schema.

Correction evidence was run under `conda activate torment` using disposable
bases outside the repository:

```text
tests/test_substrate_native_post_write_runtime.py
34 passed

tests/test_p9d_i4b1f_public_outcome_parity.py -k i4e
2 passed

tests/test_b5_a3_production_native_resource_owner.py
tests/test_substrate_fabric_native_routing.py
35 passed

tests/test_trajectory_v2.py
tests/test_substrate_native_shared_trajectory_evidence.py
tests/test_substrate_native_shared_checkpoint_snapshot.py
38 passed
```

The direct tests cover same-process SRG collision versus restart baseline,
independent trajectory/world/checkpoint failures, one V2 writer across request
adapters, V2 sealing/restart epochs, factual checkpoint manifest snapshots and
absence, no-write re-entry, private root ownership, and profile/configuration
refusal. The public tests cover ordinary
create/reinforcement/no-write/canonical-failure gates, retained broad-private
Hivemind packet emission, private checkpoint ownership, and exact true-split
continuation order.

## Bounded verdict

```text
P9D_I4E_SRG_WORLD_TRAJECTORY_CHECKPOINT_PARITY = PASS_BOUNDED_PRIVATE_NATIVE_PUBLIC_SCOPE
I4E_ADVERSARIAL_REVIEW = FAIL_INITIAL / CORRECTED
I4E_DELTA_REVIEW = PASS
I4E_READY_TO_FREEZE = YES
I4E_FROZEN = YES

SRG_COLLISION_PARITY = PASS_PRIVATE_NATIVE_PUBLIC_SCOPE
SRG_COLLISION_DURABILITY_MODEL = QUALIFIED_TRANSIENT_LEGACY_EQUIVALENT
SRG_SUCCESSOR_PARITY = PASS_BOUNDED_REACHABLE_PATHS
SRG_REPLAY_MODEL = QUALIFIED_BOUNDED

WORLD_POSTWRITE_PARITY = PASS_PRIVATE_NATIVE_PUBLIC_SCOPE
WORLD_STATE_OWNER_PARITY = QUALIFIED_PROCESS_LOCAL_OWNER_PRESERVED
WORLD_REPLAY_MODEL = QUALIFIED_BOUNDED

TRAJECTORY_OWNER_PARITY = QUALIFIED_EXTERNAL_OWNER_PRESERVED
TRAJECTORY_PARITY = PASS_BOUNDED_PRIVATE_SCOPE
PRIVATE_TRAJECTORY_WRITER_LIFETIME = LEGACY_EQUIVALENT_PROCESS_OWNER_SCOPE
TRAJECTORY_EXTERNAL_FAILURE_ISOLATION = QUALIFIED
WORLD_TRAJECTORY_FAILURE_ISOLATION = QUALIFIED

CHECKPOINT_OWNER_PARITY = QUALIFIED_EXTERNAL_OWNER_PRESERVED
CHECKPOINT_PARITY = PASS_PRIVATE_NATIVE_PUBLIC_SCOPE
CHECKPOINT_SHARD_SNAPSHOT = FACTUAL_LEGACY_EQUIVALENT
CHECKPOINT_REPLAY_MODEL = QUALIFIED_BOUNDED

HIVEMIND_ORDER_DEPENDENCY = INDEPENDENT_FOR_I4E
PREEXISTING_QUALIFIED_HIVEMIND = PRESERVED
NEW_I4F_HIVEMIND_COLLECTIVE_SCOPE = NOT_MIGRATED_BY_I4E
POSTWRITE_PROFILE_AUTHORITY = QUALIFICATION_PROFILE
POST_CHECKPOINT_COMPRESSION_DEPENDENCY = INDEPENDENT

SHARED_I4E_PARITY = NOT_CLAIMED
SHARED_PRECOMMIT_EXTERNAL_OWNER_RESTORATION_REQUIRED = YES

SRG_FORMULA_CHANGES = 0
SRG_THRESHOLD_CHANGES = 0
WORLD_FORMULA_CHANGES = 0
WORLD_THRESHOLD_CHANGES = 0
WORLD_CADENCE_CHANGES = 0
TRAJECTORY_FORMULA_CHANGES = 0
TRAJECTORY_CADENCE_CHANGES = 0
CHECKPOINT_SCHEMA_CHANGES = 0
QUERY_ORDER_CHANGES = 0
TORMENT_MATHEMATICS_PRESERVED = YES

I4F_SYSTEMS_NEWLY_MIGRATED = NO
RETIREMENT_ALLOWED = NO
REAL_PRODUCTION_ACTIVATION = NOT_AUTHORIZED
```

**Version:** 0.1

**Status:** frozen I4E preservation artifact. It records offline qualification
evidence only and does not authorize real-root contact, provider contact,
service start, selected-profile activation, shared activation, I4F work, or
component retirement.

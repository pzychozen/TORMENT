# TORMENT Memory Substrate — Phase 7G5A3D8

## Process-local world-state boundary

Status: qualified in the explicit STAGING-only A3D route.  The default Fabric
path remains legacy.  This phase resolves only `PROCESS_LOCAL_WORLD_STATE`;
`DERIVED_MEMORY_MUTATION` remains blocked and is not implemented here.

## Architecture ruling

`SeedWorld` dynamics are process-local runtime state, not native memory truth:

```text
pos / vel / vel0 (live entity fields)
trail
r_history / z_history / x_history / y_history
trajectory classification overlay
```

Advancing a native world creates no object, object revision, representation,
operation, transition, governance, provenance, relationship, runtime-order,
or authority effect.  It neither changes a durable payload's `pos`/`vel` nor
writes trajectory evidence.  A new process owner therefore starts over from
durable payload kinematics.

## Frozen legacy lifecycle

The characterization tests establish the actual legacy contract:

```text
fresh spawn
  seed_pos0 / seed_v0 -- MemoryGraph._vec3 --> durable pos / vel / vel0
  fresh r/z/x/y history and trail include the genesis point

reload
  durable node payload --> pos / vel / vel0
  trail and all geometry histories are empty

ordinary update_payload
  merge full live payload + ordinary patch
  reset live pos / vel / vel0 from payload even when the patch is non-kinematic
  retain trail, histories, and a live trajectory label
```

The exact legacy defaults remain `dt=1.0`, `drag=0.02`, zero drift, trail
length `200`, fresh `alive=True`, `born_step=logical step`, and `channel=0`.
The fresh `alive` quirk is preserved: an `alive=False` payload does not stop a
new `SeedWorld.spawn`, but it does control a reloaded entity.  Explicit `pos`
or `vel` update records the existing V2 kinematic-reset boundary; that
separate mutation surface is not opened natively by this phase.  Abort removes
the entity but never rewinds the legacy allocator.

At each `classify_every=50` step, legacy classifies `r_history` and keeps
`traj_label` / `traj_last_classify_step` in live payload only.  A later whole
payload serialization happens to capture those diagnostic fields.  This is
why a qualified native R2 can materialize them, but no standalone diagnostic
write exists.

## Native genesis and owner topology

The existing A3C2 source transaction now derives the same durable kinematic
payload facts as legacy:

```text
flexible seed_pos0 / seed_v0
  --> exact legacy _vec3 conversion
  --> payload pos / vel / vel0
```

Caller-supplied `pos`, `vel`, and `vel0` are overwritten by those derived
genesis values, matching `MemoryGraph.spawn_memory`.  The existing immutable
`memory_runtime_enumeration_orders` carrier is also published in that same
A3C2 transaction, alongside its EID alias.  It is not a new schema object or
a new semantic operation.

For a source committed in this process, `NativeWorldRuntime` receives the
exact A3C2 result plus `logical_step` and fixed channel `0`, immediately after
the source commit and before representation publication.  It creates a fresh
entity with its genesis histories and trail.  Same-process response recovery
is idempotent and does not add a second entity.

`NativeWorldProcessState` is keyed by `(core_id, legacy source namespace)` and
contains only the ordered live entity entries and exact current identity/
revision witnesses.  It owns no connection, cursor, path, selector, or
durable mutation authority.  A connection-scoped `NativeWorldRuntime` uses
the qualified A3D5 enumeration carrier and current compatibility reads to
check it.  It survives replacement of the connection adapter; replacement of
the process owner intentionally gives reload semantics.

For rows that pre-date this process, rehydration uses current durable
`pos`/`vel`/`vel0`, produces empty histories/trails, and leaves `born_step` and
`channel` as unknown rather than fabricating them from timestamps, UUIDs,
rowids, or enumeration order.  Those origin facts do not affect world physics
or classification.

```text
WORLD_PHYSICS_REHYDRATION_READY = YES
TRAJECTORY_ORIGIN_EVIDENCE_READY = NO
```

An unexpected appearance, disappearance, EID identity substitution, ambiguous
mapping, ordering change, or revision movement outside fresh-source and R2
synchronization fails closed.  The owner never silently rebuilds mid-process.

## Neutral post-write port

`LegacyFabricPostWriteAdapter` now consumes only:

```text
WorldRuntimePort.advance_for_post_write(step=...)
```

The legacy implementation is `LegacyWorldRuntime`, which delegates to the
already selected graph exactly as:

```python
graph.step_world(step=step, classify_every=50, log_every=1)
```

The post-write dependency still retains `graph` for Character and compression
work; this phase removes only the direct world-step knowledge.  No native
Fabric post-write adapter or production selector is introduced.

## R2 synchronization and diagnostics

After A3C3's source R2 commits, including a recovered source before E2 is
ready, the router invokes the world synchronizer.  It preserves entity
identity/order, histories, trail, and live `alive` state, but resets live
`pos`, `vel`, and `vel0` from R2's complete payload.  A revision witness makes
a repeated response retry a no-op rather than a second reset.

`WorldDiagnosticSuccessorMaterialization` is the only world transient allowed
to join an already-authorized R2.  It binds the exact predecessor revision and
can contribute only:

```text
traj_label
traj_last_classify_step
```

Its independent typed contract is held beside, never merged into, the typed
SRG materialization.  If both are present, the A3C3 source intent binds both
and one R2 receives both contributions.  Source interruption retains the
overlay; successful R2/E2 completion validates and consumes it.  There is no
world-only R2, R3, payload patch operation, or generic runtime patch dict.

Persistent V2/legacy trajectory evidence remains intentionally deferred:

```text
WORLD_RUNTIME_STATE_READY = YES
TRAJECTORY_EVIDENCE_PARITY_READY = NO
```

## Qualification declarations

```text
A3D8_PROCESS_LOCAL_WORLD_STATE = COMPLETE
WORLD_STATE_CLASS = PROCESS_LOCAL_RUNTIME_STATE

WORLD_RUNTIME_PORT = QUALIFIED
LEGACY_WORLD_RUNTIME_PARITY = PASS
NATIVE_WORLD_RUNTIME_PARITY = PASS
WORLD_DIRECT_POSTWRITE_GRAPH_CALL = NO

NATIVE_WORLD_PROCESS_OWNER = QUALIFIED
NATIVE_WORLD_STATE_SURVIVES_CONNECTION_BOUNDARY = PASS
NATIVE_WORLD_STATE_SURVIVES_PROCESS_RESTART = NO

WORLD_FRESH_CREATION_TOPOLOGY_PARITY = PASS
WORLD_RELOAD_TOPOLOGY_PARITY = PASS
WORLD_RUNTIME_ORDER_PARITY = PASS
WORLD_STEP_NO_WRITE_PARITY = PASS
WORLD_STEP_REINFORCEMENT_PARITY = PASS
WORLD_STEP_CREATED_NEW_PARITY = PASS
WORLD_REINFORCEMENT_KINEMATIC_RESET_PARITY = PASS

WORLD_STEP_CREATED_NATIVE_REVISIONS = 0
WORLD_STEP_CREATED_NATIVE_OPERATIONS = 0
WORLD_STEP_CREATED_NATIVE_TRANSITIONS = 0
WORLD_STEP_AUTHORITY_EXPANDED = NO

WORLD_DIAGNOSTIC_STATE_CLASS = PROCESS_LOCAL_RUNTIME_STATE
WORLD_DIAGNOSTIC_SUCCESSOR_MATERIALIZATION = QUALIFIED
TRAJECTORY_EVIDENCE_PARITY_READY = NO

PROCESS_LOCAL_WORLD_STATE_BLOCKER = COMPLETE
HARD_ROUTE_BLOCKER_GROUP_COUNT = 1
DEFAULT_REQUIRED_BLOCKER_GROUPS = DERIVED_MEMORY_MUTATION

DEFAULT_FABRIC_BEHAVIOR_CHANGED = NO
NATIVE_ACTIVE = NO
DUAL_WRITE = NO
DUAL_READ = NO
CUTOVER_OPENED = NO
NATIVE_POST_WRITE_ADAPTER = NO
A3D_NATIVE_ROUTE_WIRED_INTO_FABRIC = NO
A3D_END_TO_END_FABRIC_ROUTE = BLOCKED
```

Schema remains v1.2 before and after this phase.  No migration, real embedding
generation, MemoryGraph/Fabric/embedding-store native wiring, reconciliation,
derived-memory mutation, anchors, mood, Character routing, compression,
deep-memory, motif merge, checkpoint, bridge, activation, or cutover work is
included.

# 7G5E4D-D3 shared trajectory evidence parity

## Scope

D3 begins at `e48975b Qualify 7G5E4D shared Hivemind post-write` and closes
only the shared-domain trajectory evidence boundary.  It does not select
native storage for public ingest, activate the native path, alter world/SRG
mathematics, persist live coordinates, create a trajectory SQLite family, or
compose D3 with D1, D2, or B1.

The explicit profile is
`core_staging_with_shared_trajectory_evidence`.  It requires a claimed
`SHARED_DOMAIN`, an exact external artifact root, and the current legacy
format selection.  It refuses shared Hivemind, M1/mood, and B1 composition.

## Ownership and identity

The ownership split remains:

~~~text
NativeWorldRuntime process state
  position / velocity / trail / history / current classification
                  | read-only live entity observation
                  v
NativeTrajectoryEvidenceRuntime
  existing V2 files or legacy JSONL + memory_events.jsonl
~~~

The evidence runtime has no SQLite connection, native-ID conversion, source
route authority, vector owner, or `MemoryGraph` dependency.  It only wraps
the existing `TrajectoryV2Writer` or `TrajectoryLogger` and appends the
existing external classification event format.

Both artifact formats serialize a bare compatibility `eid`.  It is a
diagnostic field inside the exact root:

~~~text
<workspace.data_dir>/workspaces/<workspace_id>/domains/<domain_id>/shared
~~~

It is not a globally unique key and D3 neither resolves nor maps it into a
private scope.  The parity witness deliberately uses independently allocated
source namespaces (legacy EID `1`, native EID `0`) and compares the scoped
record semantics while asserting that each root consistently carries its own
current source EID.  No bare-EID cross-scope equivalence is claimed.

## Frozen legacy evidence law

`MemoryGraph` selects trajectory format as follows:

| Environment value | Selected writer |
| --- | --- |
| unset or `v2` | `TrajectoryV2Writer` |
| `legacy` | `TrajectoryLogger` daily JSONL |
| any other value | legacy JSONL fallback |

For every `LegacyWorldRuntime.advance_for_post_write(step)`, the selected
graph calls `step_world(step, classify_every=50, log_every=1)`.  Legacy
post-write invokes this world slot for all storage outcomes.  Within the
world method the order is fixed:

1. Advance `SeedWorld` physics.
2. Serialize every live entity after physics (`log_every=1`).
3. If `step % 50 == 0`, classify each live `r_history`, update its RAM
   payload label, and append `TRAJ_CLASSIFY` to `memory_events.jsonl`.

Thus a legacy JSONL record at step 50 carries the prior label; the event and
the live entity carry the newly calculated label.  V2 dynamic frames contain
kinematics only, so the same ordering is observable through the following
classification event.  There is no change to `SeedWorld` integration,
history/trail maintenance, or `classify_trajectory` mathematics.

V2 writes birth facts (`eid`, `born_step`, `channel`, `pos0`, `vel0`) at
creation and deduplicates them by bare EID within that artifact root.  Each
post-physics frame has `(epoch, frame_seq)` identity; `step` is diagnostic
metadata and may repeat.  V2 tails are `.partial` until close: close flushes,
fsyncs, closes, renames to `.trj2`, hashes it, then appends its manifest entry.
The legacy JSONL logger has no V2 tail/seal operation.

## D3 native binding

The router has already initialized the process world and registered a fresh
native source with its true route `born_step` and channel.  D3 uses that live
entity directly:

~~~text
current CREATED_NEW shared route witness
  -> write V2 genesis (when V2 is selected)
  -> NativeWorldRuntime advances existing process SeedWorld
  -> external writer snapshots current live entities
  -> every 50th step: existing classifier updates process overlay
  -> external TRAJ_CLASSIFY event
~~~

The D3 standalone profile runs evidence only for `CREATED_NEW`.  This is
intentional: a fresh native route carries the exact source birth facts, while
a cold rehydration intentionally has `born_step/channel = None`.  D3 does
not invent those facts merely to emit an artifact for a reinforced or
`NO_WRITE` context.  The legacy all-outcome world law is documented above;
broader shared profile composition belongs to the later direct-ingest slice.

The V2 evidence writer remains long-lived per prepared D3 adapter and the
adapter has an explicit fail-soft `close()` that seals its current V2 tail.
It is not a production lifecycle owner or selector.

## Parity and recovery evidence

`tests/test_substrate_native_shared_trajectory_evidence.py` establishes:

- V2 parity through steps 1..50: genesis facts, post-physics positions and
  velocities, frame sequence/order, chunk and manifest population facts,
  step-50 classifier output, and `TRAJ_CLASSIFY` event semantics.
- Explicit legacy JSONL fallback parity through the same trace, including the
  pre-classification step-50 snapshot order.
- A normal V2 live tail is verifier-valid and `close()` seals it.  A
  one-frame partial tail seals without adding frames; an empty V2 lifecycle
  closes with no semantic frame or tail.
- V2 artifact reload with `TrajectoryV2Verifier` is independent of the world
  and does not mutate native memory.
- After close and a recreated `NativeWorldProcessState`, external evidence
  remains readable, but native source payload reload restores original
  position/velocity and has no history or classification overlay.  It never
  takes the latest evidence frame or label as authoritative input.

The focused witness confirms:

~~~text
SHARED_TRAJECTORY_EVIDENCE_PARITY = PASS
TRAJECTORY_CLASSIFICATION_PARITY = PASS
TRAJECTORY_CLOSE_PARITY = PASS
TRAJECTORY_ARTIFACT_RELOAD = PASS
TRAJECTORY_RESTART_AUTHORITY = NONE
~~~

## Failure topology

The legacy world boundary is fail-soft and D3 retains that shape.

| External fault | D3 result |
| --- | --- |
| V2 genesis write | Logged/skipped; world stepping continues. A later V2 frame may retry the writer's normal genesis dedup/write path. |
| V2 frame write / legacy entity log | Logged/skipped; no world rollback and classification still occurs at the scheduled step. |
| `TRAJ_CLASSIFY` event append | Label remains only in the live process overlay; event loss does not roll back physics or source memory. |
| V2 chunk/manifest seal | Writer returns/raises failure to the external runtime, which logs it; the physical chunk may already be closed, but no native compensating mutation occurs. |
| V2 close | Logged/skipped; no source or world rollback. |

Injected D3 faults cover genesis, frame, event, and manifest/close paths.
In every case native object/revision, relationship, representation, operation,
provenance, and governance table counts remain fixed after the source route.

~~~text
TRAJECTORY_FAILURE_TOPOLOGY_PARITY = PASS
TRAJECTORY_NATIVE_MEMORY_MUTATION = NONE
TRAJECTORY_CLASSIFICATION_MEMORY_SUCCESSOR = NONE
TRAJECTORY_SQLITE_AUTHORITY = NONE
TRAJECTORY_ONLY_VECTOR_INVALIDATION = NO
~~~

Trajectory evidence creates no representation and does not call a vector
runtime, so it cannot independently request a rebuild.  The classifications
are the existing process-local diagnostic overlays and are not materialized
by D3.

## Remaining shared post-write disposition

| Consumer | Active/no-op | Trigger | Target owner | Durability | Native status |
| --- | --- | --- | --- | --- | --- |
| Contradiction | No-op | Shared source | None; private-only predicate | None | `SHARED_NO_OP` |
| SRG/world physics | Active process state | Legacy world slot | Claimed shared process world | Process-only | `PROCESS_ONLY`; math unchanged |
| Trajectory evidence | Active D3 standalone | Fresh `CREATED_NEW` route | Exact external shared-domain artifact root | External V2/JSONL/events | `QUALIFIED` |
| Hivemind | Active D2 standalone | Fresh `CREATED_NEW` route | Existing CollectiveField / bridge | External | `ALREADY_QUALIFIED` |
| M1/M2/D0/mood | Active D1 standalone | Fresh `CREATED_NEW` route | External shared workflow; optional private mood target | External / conditional private native row | `ALREADY_QUALIFIED` |
| B1 bridge | Active B1 standalone | Existing stored/random gate | Existing external bridge registry | External | `ALREADY_QUALIFIED` |
| Character | Blocked | Character cadence / state conditions | Mixed shared source and private Character owner | External and possibly shared correction | `BLOCKED` |
| Checkpoint | Blocked | Enabled interval | Existing external checkpoint owner | External | `BLOCKED` |
| Compression/deep | Blocked | Enabled compression gate | Triggering agent private graph/deep store | Private/external | `BLOCKED` |
| Ordinary proposal | No-op | Post-write slot | None; private-only predicate | None | `SHARED_NO_OP` |

## Verification posture

The D3 focused suite and the D2/D1/D0/B1/world regression set pass with the
native `torment-substrate` environment (SQLite 3.53.4): 66 tests total.

~~~text
KERNEL_FILES_CHANGED = 0
WORLD_MATHEMATICS_CHANGED = NO
TRAJECTORY_MATHEMATICS_CHANGED = NO
D2_HIVEMIND_REGRESSION = PASS
D1_REGRESSION = PASS
D0_REGRESSION = PASS
B1_REGRESSION = PASS
WORLD_PROCESS_ONLY_REGRESSION = PASS

PUBLIC_INGEST_BACKEND = LEGACY
PRODUCTION_SELECTOR_ADDED = NO
NATIVE_ACTIVE = NO
DUAL_WRITE = NO
DUAL_READ = NO
CUTOVER_OPENED = NO
~~~

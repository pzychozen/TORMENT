# TORMENT Memory Substrate — Phase 7G5A3D10

## Explicit native post-write adapter qualification

This slice qualifies `CORE_NATIVE_POST_WRITE_SEMANTICS` for an already
qualified native Fabric route. It does not claim full production feature
parity, select a backend in `TormentFabric`, or activate native storage.

Schema remains v1.2. No table, durable whole-tail ledger, migration, startup
hook, selector, auto-open path, dual write, or dual read is added.

## Construction and authority boundary

`prepare_native_fabric_post_write_adapter()` requires both an already
prepared `NativeFabricRoutingCapability` and an explicit
`NativePostWriteQualificationConfiguration`. Direct construction is rejected.
The resulting `NativeFabricPostWriteAdapter` carries no SQLite connection and
has no activation or selection authority.

For every `run()` it opens the existing qualified core, revalidates core
identity, STAGING role, deployment posture, lanes, and claimed namespace
facts, binds short-lived native ports, runs the allowed post-write work, and
closes the connection. The prepared routing capability remains the sole owner
of the process-local world, SRG, and motif-order states.

```text
native route result + explicit context/witness
    -> operation-scoped native readers/runtimes
    -> qualified post-write consumers
    -> FabricPostWriteOutcome
```

There is no `MemoryGraph`, shadow graph, legacy memory fallback, native
activation, authority transition, or `ACTIVE_AUTHORIZATION` path in this
adapter.

## Immutable qualification profile

The immutable `NativePostWriteQualificationProfile.core_staging()` declares:

| Behavior | A3D10 status |
| --- | --- |
| Conflict consumer, SRG, Hivemind, derived memory, world, proposal | `QUALIFIED` |
| Motif suggestion maintenance | `REQUIRED_NOOP` |
| Motif auto-merge, Character, compression, deep memory | `UNSUPPORTED` |
| Checkpoint, trajectory evidence, bridge suggestions | `DISABLED_FOR_PROFILE` |

The motif-maintenance slot remains present between Hivemind and derived
memory, but performs the stated required no-op. Derived calls therefore retain
their frozen position instead of moving across SRG or world.

Before opening a post-write connection or calling a consumer, the adapter
refuses a supplied posture that could materially execute excluded work:

```text
required motif suggestions
auto_merge_motifs policy
effective Character drift
enabled compression
effective/requested checkpoint
persistent trajectory evidence
bridge suggestions
deep-memory requirement
```

This is an explicit qualification refusal, not a feature skip. Character,
compression, deep-memory, auto-merge, checkpoint, trajectory persistence, and
bridges remain unimplemented native parity work.

## Route/context contract

For a storage result, the caller must supply a
`NativePostWriteRouteWitness` containing the result and the same stable native
operation key. The adapter checks, before consumer effects:

```text
claimed workspace/private-agent scope and adapter domain
stored truth
EID
route domain
created versus reinforced mapping
motif IDs
current native memory class
```

The only accepted mapping is:

```text
stored=True, reinforced=False -> CREATED_NEW
stored=True, reinforced=True  -> REINFORCED_EXISTING
```

`NO_WRITE` carries no route witness, EID, source operation, or native memory
mutation. It still uses the explicitly claimed scope, performs its one world
step, and invokes supported all-outcome proposal logic (which preserves the
existing `stored=False` no-proposal gate).

## Qualified sequence

For `CREATED_NEW`, the native adapter reuses bounded backend-neutral legacy
consumer helpers with explicitly bound native read/process ports:

```text
contradiction surface
SRG collision
Hivemind
motif-maintenance slot (required no-op)
identity-anchor emission
identity-anchor refinement
mood-drift emission
world step
proposal evaluation
```

Conflict retains its private/core gate, qualified current embedding search,
self exclusion, class filter, score and first-conflict break, while the
existing conflict registry remains its external side-store owner. SRG retains
ordered native enumeration, qualified embeddings, strict first-order tie
selection, 0.75 threshold, collision math, and process-local overlays.
Hivemind retains governance and collective-echo gates, packet construction,
telemetry, collective field append, and its existing proposal-bridge callback.

Derived memory is the A3D9 `NativeDerivedMemoryRuntime`: its three calls keep
their independent fail-soft boundaries and run before world. World is the
A3D8 process-local owner, so derived rows fresh-register before the one world
advance. Proposal creation retains the existing coupling, policy, registry,
embedding, identity-save, and result-ID behavior; it does not mutate native
memory.

For `REINFORCED_EXISTING`, created-only consumers are absent; world and
proposal retain their all-outcome behavior. `NO_WRITE` has the same all-outcome
scope without a source result. The production
`LegacyFabricPostWriteAdapter` remains the only Fabric-wired adapter. Its
existing motif/derived helper was only split at the fixed derived slot; the
legacy motif-runtime gate, order, fail-soft boundaries, and production
behavior are unchanged.

## Retry archaeology

This phase adds no whole-tail idempotency administration carrier. Existing
source/representation response-loss recovery remains distinct from a whole
external ingest retry:

```text
A3C2 source or E1 interruption
  -> same native operation key resumes storage
  -> exactly one subsequent post-write invocation

A3C3 R(n+1) source / PENDING / expectation interruption
  -> same native operation key resumes R(n+1)/E(n+1)
  -> exactly one subsequent post-write invocation
```

The derived R1 publisher inside the post-write slot has independently stable
child keys. A pending derived representation interruption can be retried
through the same adapter/witness without a duplicate derived object, revision,
representation, or world entity. This does not change legacy whole-tail retry
semantics for later external side effects such as proposal or bridge work.

## Qualification evidence

`tests/test_substrate_native_post_write_runtime.py` proves:

```text
explicit construction gate and no retained connection
CREATED_NEW native conflict/SRG/Hivemind/derived/world/proposal path
REINFORCED_EXISTING created-only exclusion and world step
NO_WRITE no-route/no-mutation world step
route-witness mismatch refusal before effects
all excluded executable postures refuse before effects
separate post-write connection with shared process owners
A3C2 source/E1 and A3C3 source/PENDING/expectation recovery before one tail
derived pending-representation recovery inside the post-write slot
native semantic-table before/after accounting
forbidden graph dependency by injected graph sentinel
```

The regression matrix also retains the A3C2/A3C3 routing, A3D1–A3D9,
post-write, schema-v1.2, and legacy default-path checks. Test fixtures use
native-only memory ports and fail immediately if the adapter reaches the
forbidden graph carrier.

## Qualification declarations

```text
A3D10_NATIVE_POST_WRITE_ADAPTER_QUALIFICATION = COMPLETE

NATIVE_POST_WRITE_ADAPTER_QUALIFIED = YES
NATIVE_POST_WRITE_ADAPTER_ACTIVE = NO

NATIVE_POST_WRITE_NO_WRITE_PARITY = PASS
NATIVE_POST_WRITE_REINFORCEMENT_PARITY = PASS
NATIVE_POST_WRITE_CREATED_NEW_PARITY = PASS

NATIVE_POST_WRITE_CONFLICT_PARITY = PASS
NATIVE_POST_WRITE_SRG_PARITY = PASS
NATIVE_POST_WRITE_HIVEMIND_PARITY = PASS
NATIVE_POST_WRITE_DERIVED_MEMORY_PARITY = PASS
NATIVE_POST_WRITE_WORLD_PARITY = PASS
NATIVE_POST_WRITE_PROPOSAL_PARITY = PASS

NATIVE_POST_WRITE_CROSS_CONNECTION_PARITY = PASS
NATIVE_POST_WRITE_STORAGE_RECOVERY_PARITY = PASS

NATIVE_POST_WRITE_MEMORYGRAPH_DEPENDENCY = NO
NATIVE_POST_WRITE_LEGACY_FALLBACK = NO

HARD_ROUTE_BLOCKER_GROUP_COUNT = 0
DEFAULT_REQUIRED_BLOCKER_GROUPS = NONE
A3D_CORE_STORAGE_RUNTIME_ROUTE = QUALIFIED

FULL_OPERATIONAL_POST_WRITE_PARITY_READY = NO
FULL_CONDITIONAL_FEATURE_PARITY_READY = NO
A3D_END_TO_END_FABRIC_ROUTE = QUALIFIED_IN_EXPLICIT_STAGING_PROFILE

PRODUCTION_NATIVE_ROUTE_READY = NO
CUTOVER_READY = NO
DEFAULT_FABRIC_BEHAVIOR_CHANGED = NO

NATIVE_ACTIVE = NO
DUAL_WRITE = NO
DUAL_READ = NO
CUTOVER_OPENED = NO
A3D_NATIVE_ROUTE_WIRED_INTO_FABRIC = NO
```

## Remaining inventory

```text
DEFAULT HARD BLOCKERS
  NONE for the explicit core STAGING profile.

CONDITIONAL FEATURE PARITY
  Character/memory-derived readers and gravity correction;
  compression typed successors; deep-memory export; motif auto-merge.

OPERATIONAL PARITY
  motif suggestions; persistent trajectory evidence; checkpoint snapshots;
  bridge suggestions.

DEPLOYMENT / MIGRATION / CUTOVER
  legacy admission/migration evidence, production activation selection,
  operational deployment qualification, authority authorization, and cutover.
```

No next phase is started by this qualification. The next choice should be
reassessed between conditional/default parity, operational parity, and
migration/admin qualification based on the desired deployment posture.

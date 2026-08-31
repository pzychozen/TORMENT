# TORMENT Memory Substrate — Phase 7G5C1A

## Native Character Drift Measurement Boundary

Phase 7G5C1A qualifies only the read/measurement portion of Character's
post-write drift work. Legacy production behavior remains authoritative.
Fabric receives no native route, selector, deployment state, cutover, dual
read, or dual write from this phase.

The neutral `CharacterDriftRuntimePort` accepts a narrow post-write request and
returns a measurement capability result. Its legacy implementation delegates
to the existing graph/cache semantics. Its native implementation accepts only
the already-qualified native memory enumeration/read ports and
`NativeMotifRuntimeReader`; it does not receive a SQLite connection,
MemoryGraph, MotifRegistry, or a semantic writer.

## Frozen behavior retained

The outer gate is unchanged:

```text
TORMENT_CHARACTER_ENABLE default true
AND stored
AND step > 0
AND step % character_drift_every == 0
```

`REINFORCED_EXISTING` still passes that outer gate but produces an effective
measurement no-op. Only `CREATED_NEW` can measure and persist CharacterState.
The native C1A configuration accepts only the default cache-enabled posture;
a request with `TORMENT_GRAPH_EMB_CACHE = 0` is refused rather than inventing
a second Character geometry contract.

Memory order is recovered from the A3D5
`memory_runtime_enumeration_orders` port. Filtering remains exact: seed canon
rows are skipped, `user_id` is compared exactly, tiers are counted before
recency exclusion, and recency continues to use only
`payload["born_step"]` with default zero. Missing qualified representation
bytes behave like an absent legacy cache entry.

The native read-side geometry is:

```text
current qualified raw float32 COMPAT_EMBEDDING
→ exact MemoryGraph cache normalization
  (float32, dimension adjustment, norm + 1e-12)
→ Character drift measurement
```

No normalized vector is persisted. Seed geometry retains the frozen fallback
order:

```text
current qualified seed motif centroid
→ namespace-bound Character seed EID cache vectors
→ recent-memory average
```

The EID fallback is scoped by `NativePostWriteMemoryAccess`; no bare or global
EID resolution exists.

The shared backend-neutral helper retains the existing weighting, cosine,
distance, score, explanation, tier-count, prior-state comparison, and strict
`0.03` direction threshold equations. CharacterState remains the external
`CharacterStore` JSON state. It is loaded, created when absent, updated,
appended with `(step, drift_score)`, capped to 50 entries, and saved through
the unchanged store API.

## C1A gravity boundary

When the measured legacy condition is true:

```text
drift_score < -seed.drift_correction_threshold
AND drift_direction == "away_seed"
```

native C1A returns `CHARACTER_GRAVITY_CORRECTION_REQUIRED` after CharacterState
persistence. It makes no drift-correction memory and no motif mutation. This
is an explicit C1B requirement, not a silently skipped claim of full parity.
The existing legacy Fabric adapter alone retains gravity correction and its
ordinary application-owned reflex callback boundary; the neutral/native
measurement ports do not call a reflex engine.

## Qualification declaration

```text
C1A_NATIVE_CHARACTER_DRIFT_MEASUREMENT = COMPLETE

CHARACTER_DEFAULT_ENABLE = TRUE
CHARACTER_DRIFT_RUNTIME_PORT = QUALIFIED

LEGACY_CHARACTER_DRIFT_PARITY = PASS
NATIVE_CHARACTER_DRIFT_PARITY = PASS

CHARACTER_RUNTIME_ORDER_PARITY = PASS
CHARACTER_CACHE_NORMALIZATION_PARITY = PASS
CHARACTER_PAYLOAD_BORN_STEP_PARITY = PASS
CHARACTER_SEED_GEOMETRY_PARITY = PASS

CHARACTER_STATE_STORE = RETAIN_EXTERNAL_UNCHANGED
CHARACTER_STATE_PERSISTENCE_PARITY = PASS

CHARACTER_REINFORCEMENT_EFFECTIVE_NOOP_PARITY = PASS

CHARACTER_GRAVITY_CORRECTION_QUALIFIED = NO
CHARACTER_GRAVITY_CORRECTION_NEXT = C1B

CHARACTER_MEASUREMENT_CREATED_NATIVE_REVISIONS = 0
CHARACTER_MEASUREMENT_CREATED_NATIVE_OPERATIONS = 0
CHARACTER_MEASUREMENT_CREATED_NATIVE_TRANSITIONS = 0

CHARACTER_AUTHORITY_EXPANDED = NO

FULL_CHARACTER_PARITY_READY = NO
FULL_PRODUCTION_BEHAVIOR_PARITY_READY = NO

SCHEMA_VERSION = 1.2

NATIVE_ACTIVE = NO
DUAL_WRITE = NO
DUAL_READ = NO
CUTOVER_OPENED = NO
A3D_NATIVE_ROUTE_WIRED_INTO_FABRIC = NO
```

## C1B composition assessment

C1B can compose a typed drift-correction memory creation, optional native
motif attach/create, and this unchanged CharacterStore state boundary. It must
remain a dedicated typed operation sequence: C1A grants no generic payload
mutation authority, and no C1B writer is implemented here.

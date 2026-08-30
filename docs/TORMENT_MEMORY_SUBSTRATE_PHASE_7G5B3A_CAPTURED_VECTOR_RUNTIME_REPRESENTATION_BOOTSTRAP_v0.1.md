# TORMENT Memory Substrate — Phase 7G5B3A

## Deterministic captured-vector runtime representation bootstrap

Phase 7G5B3A introduces the narrow administrative operation
`NativeMigrationRuntimeRepresentationBootstrapService.bootstrap_from_legacy_capture()`.
It is restricted to one existing B1 `BYTE_DERIVATION_POSSIBLE` vector whose
memory is already a qualified, current B2 R2. It neither admits evidence nor
normalizes object semantics, generates an embedding, opens runtime routing, or
activates the native core.

The durable shape is deliberately a new representation, not a promotion:

```text
7F LEGACY_EMBEDDING_CAPTURE (R1, UNKNOWN / RECONCILIATION_REQUIRED)
    + B2-normalized current R2
    -> CREATE_REPRESENTATION_PENDING
    -> ESTABLISH_REPRESENTATION_INTEGRITY_EXPECTATION (SHA256 / RAW)
    -> PUBLISH_REPRESENTATION_READY
    -> new R2 COMPAT_EMBEDDING (READY / USABLE)
```

The legacy capture remains frozen evidence. Its class, source R1, bytes,
readiness, disposition, and admission record are not changed. The new
`COMPAT_EMBEDDING` is source-bound to R2 only, uses generation `1`, contract
`compat-embedding-v1`, encoding `RAW_VECTOR`, and dtype `float32`.

## Closed eligibility and byte contract

The service re-verifies on every phase boundary:

- schema v1.2, the exact STAGING core, and `LEGACY_ACTIVE` deployment with no
  referenced core;
- the supplied manifest and all frozen snapshot bytes, persisted snapshot and
  nodes-artifact evidence, source namespace, canonical EID alias, and runtime
  enumeration order;
- exact legacy-admitted R1 and exact current R2;
- the complete B2 topology: `MIGRATION_RUNTIME_NORMALIZATION` operation,
  native transition, object-revision effect, matching operation output,
  `NATIVE_ORDINARY` R2 ordinal 2, predecessor R1, explicit governance,
  structural provenance, authoritative lifecycle facts, and
  `NOT_APPLICABLE` authority;
- exactly one genuine 7F `LEGACY_EMBEDDING_CAPTURE` for that object/R1 in
  `UNKNOWN / RECONCILIATION_REQUIRED`, with its 7F transition/admission
  evidence and the same snapshot;
- `NUMPY_NPY` capture origin, exact provider/model/dtype/dimension evidence,
  finite float32 bytes, and exact `dimension * sizeof(float32)` length.

The capture's historical derivation contract and encoding remain historical
facts. B3A makes a new, explicit administrative decision to republish those
verified bytes under the target runtime contract; it does not assert that the
legacy capture already had that contract.

The capture payload is read only via the explicit legacy-evidence read
boundary. B3A publishes those bytes byte-for-byte: no unit normalization,
conversion, reshape/re-serialization, rounding, fallback, or model call.

## Embedding-input continuity

Before bytes may move from R1 evidence to R2, B3A freezes the input identity
used by the legacy memory shape:

```text
R1 payload.summary, otherwise R1 payload.text
```

That selected string must be present and exactly equal in the normalized R2
JSON payload. Its canonical field/value SHA-256 is bound into the prepared
plan and administrative intent. A missing, non-string, or changed value
refuses with `B3A_EMBEDDING_INPUT_CONTINUITY_BLOCKED`; stale bytes are never
attached to changed semantic content.

## Idempotency and recovery

The marker-protected `PreparedLegacyCaptureRepresentationBootstrap` binds core,
snapshot/source namespace, object/EID, R1/R2, B2 operation/transition,
runtime order, capture identity/hash/length/provider/model/dtype/dimension/
historical contract/encoding, target lane, continuity digest, and idempotency
namespace. A deterministic UUIDv4-shaped representation identity is derived
from those facts.

The PENDING operation persists that complete canonical administrative witness
inside its normal representation canonical intent. Stable child keys are used
for PENDING, expectation, and READY. A reused key with a changed lane or R2
raises `SubstrateIdempotencyConflict`; immutable capture bytes cannot be
rewritten at all, and changed prepared capture facts conflict with the stored
PENDING intent. Interrupted calls after PENDING, expectation, or READY commit
recover the same single representation without duplicate expectations or READY
representations.

`NativeCompatEmbeddingReader.read_current()` is the final post-condition. A
current qualified vector is recoverable only when its representation identity,
R2 source, SHA-256, and bytes match the prepared B3A plan. Any other current
qualified candidate fails closed as a competing representation.

## Deliberate exclusions

This phase does not implement B3B re-embedding, reconciliation/H6, migration
replay, vector repair, a vector mapping table, schema changes, motif
normalization, side-store changes, governance/provenance/lifecycle/authority
changes, Fabric/DomainRouter/Character wiring, native activation, dual write,
dual read, or cutover.

## Qualification declarations

```text
B3A_CAPTURED_VECTOR_REPRESENTATION_BOOTSTRAP = COMPLETE
B3A_BOOTSTRAP_MODE = DETERMINISTIC_CAPTURED_BYTES_ONLY
B3A_EMBEDDER_CALLS = 0
B3A_REQUIRES_B2_NORMALIZED_CURRENT_REVISION = YES

LEGACY_CAPTURE_REWRITTEN = NO
LEGACY_CAPTURE_PROMOTED_TO_READY = NO
LEGACY_CAPTURE_REMAINS_EVIDENCE = YES

COMPAT_EMBEDDING_CREATED = YES
COMPAT_EMBEDDING_SOURCE_REVISION = B2_R2
COMPAT_EMBEDDING_BYTES_EQUAL_CAPTURE = YES
COMPAT_EMBEDDING_READY = YES
COMPAT_EMBEDDING_USABLE = YES
COMPAT_EMBEDDING_INTEGRITY_MATCH = YES

B3A_CREATES_OBJECT_REVISION = NO
B3A_CREATES_R3 = NO
B3A_EID_ALIAS_DELTA = 0
B3A_RUNTIME_ORDER_DELTA = 0
B3A_GOVERNANCE_CHANGED = NO
B3A_PROVENANCE_CHANGED = NO
B3A_LIFECYCLE_CHANGED = NO
B3A_AUTHORITY_EXPANDED = NO

POSITIVE_OBJECT_POST_B3A_CLASS = RUNTIME_READY_AS_IS
UNRESOLVED_OBJECTS_BOOTSTRAPPED = 0
REEMBED_REQUIRED_BOOTSTRAPPED = 0
NO_VECTOR_PRESENT_BOOTSTRAPPED = 0
UNUSABLE_VECTOR_EVIDENCE_BOOTSTRAPPED = 0
MOTIF_NORMALIZATION_PERFORMED = NO
SIDE_STORE_MUTATION = NO
SCHEMA_VERSION = 1.2

NATIVE_ACTIVE = NO
DUAL_WRITE = NO
DUAL_READ = NO
CUTOVER_OPENED = NO
A3D_CORE_STORAGE_RUNTIME_ROUTE = QUALIFIED
A3D_NATIVE_ROUTE_WIRED_INTO_FABRIC = NO
```

The separately authorized next step is B3B re-embedding for evidence that is
not already byte-derivable. It is not opened here.

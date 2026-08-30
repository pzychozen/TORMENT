# TORMENT Memory Substrate — Phase 7G5B2

## Evidence-bounded legacy core-memory runtime normalization

Phase 7G5B2 adds one narrow administrative-to-native normalization operation:
`NativeMigrationRuntimeNormalizationService.normalize_legacy_core_memory()`.
It is not a generic object transition API, a migration replay engine, a
representation bootstrapper, or a runtime activation path.

The operation accepts only immutable references: a verified snapshot and
manifest, exact source namespace/EID/R1, expected STAGING core, revalidated
`MigrationRuntimeScopePlan`, and an idempotency key. Callers cannot supply an
arbitrary object state, runtime payload, governance vector, or provenance row.
An internal marker-protected `PreparedLegacyMemoryNormalization` contains the
derived facts used by the single semantic transaction.

## Frozen initial eligibility

One object is eligible only when all of these facts are true at preparation
and immediately before commit:

- The native core is schema 1.2, `STAGING`, and deployment is
  `LEGACY_ACTIVE` with no referenced core.
- The supplied manifest is byte-verified and matches its persisted snapshot,
  source namespace, and exactly one `nodes.jsonl` evidence artifact.
- One source-namespaced canonical EID alias resolves to one admitted
  `LEGACY_CORE_NODE`; that object has no foreign EID alias.
- The source is exact R1, ordinal 1, `LEGACY_PREDECESSOR_UNKNOWN`, original
  7F evidence shape, and—when publishing a new operation—is still current.
- Its immutable first-surviving-JSONL runtime-order row agrees with the frozen
  admission record and verified snapshot selector.
- Exactly one supplied scope plan matches the source namespace; all referenced
  namespace/scope identities exist, its idempotency namespace matches the
  request, and the object identity namespace already equals the plan target.
  B2 never clones or rekeys an object.
- The legacy row has a real mapping-valued `payload`. Its runtime payload is
  derived by the existing `MemoryGraph._load()` law:

  ```text
  payload.pos       or payload.seed_pos0 or zero vector
  payload.vel       or payload.seed_v0   or zero vector
  payload.vel0      or normalized vel
  payload.alive     or True
  ```

  `born_step` and `channel` remain structural outer-node fields; B2 does not
  manufacture them inside R2 payload. No stepped world position or history is
  materialized.
- The payload has exactly the five explicit boolean governance facts.
- The payload has an exact canonical `ProvenanceV1`; B2 uses the existing
  `translate_provenance_v1()` translation and does not replace unknown origin
  with migration origin.
- The payload has an exact, row-authoritative canonical `lifecycle_status`.
  Its existing state/actor/via/time are preserved structurally on R2. The
  legacy protected-marker helper is deliberately not used as a new default:
  it would stamp a derivation time not present in the immutable evidence.

The only lifecycle rule implemented in this slice is therefore explicit
canonical lifecycle evidence. Missing lifecycle, malformed lifecycle,
non-authoritative lifecycle, or explicit-vs-protected-marker disagreement
refuses that object. No B2 lifecycle interpretation is invented.

## Publication topology

For an eligible object, one `SubstrateTx` / `execute_semantic` transaction
creates exactly:

```text
immutable translated provenance row
R2 NATIVE_ORDINARY (predecessor = exact R1, ordinal = 2)
R2 explicit revision-bound governance row
MIGRATION_RUNTIME_NORMALIZATION / NATIVE transition
R2 object-revision effect
MIGRATION_RUNTIME_NORMALIZATION object output
object current pointer -> R2
```

R1 remains immutable `TEXT` evidence. No EID alias, runtime-order row, memory
object, representation, expectation, measurement, motif, side-store fact, or
activation state is created or modified. `authority_category` is frozen to
`NOT_APPLICABLE` for this ordinary core-memory family.

The canonical intent binds the contract version, snapshot/source/core/object,
EID, exact R1, runtime order, scope-plan digest, target scope, payload digest,
governance, translated provenance, lifecycle, and authority. Same key plus
same intent recovers R2; a changed caller retry contract raises the existing
idempotency conflict. A rollback seam proves no partial provenance row; a
post-commit response-loss seam proves recovery never creates R3.

## Representation and activation boundary

B2 creates no `COMPAT_EMBEDDING`, does not promote
`LEGACY_EMBEDDING_CAPTURE`, and leaves captured bytes/class/source/readiness/
disposition unchanged. R2 semantic normalization alone is consequently
classified by B1 as `REPRESENTATION_BOOTSTRAP_REQUIRED`, not runtime-ready.

There is no Fabric/DomainRouter/Character routing change, native activation,
dual write/read, cutover, reconciliation/H6, migration replay, embedding
generation, side-store mutation, or motif normalization in this slice.

## Qualification declarations

```text
B2_RUNTIME_NORMALIZATION_SERVICE = COMPLETE
B2_NORMALIZATION_IS_EVIDENCE_BOUNDED = YES
B2_NORMALIZATION_REQUIRES_EXPLICIT_SCOPE_PLAN = YES

LEGACY_ADMISSION_R1_REWRITTEN = NO
LEGACY_ADMISSION_R1_IMMUTABLE = YES
NORMALIZATION_CREATES_NEW_OBJECT = NO
NORMALIZATION_CREATES_ONE_R2 = YES
NORMALIZATION_CREATES_MULTIPLE_SEMANTIC_REVISIONS = NO
NORMALIZATION_EID_ALIAS_DELTA = 0
NORMALIZATION_RUNTIME_ORDER_DELTA = 0
NORMALIZATION_GOVERNANCE_EXPLICIT = YES
NORMALIZATION_PROVENANCE_QUALIFIED = YES
NORMALIZATION_LIFECYCLE_QUALIFIED = YES
NORMALIZATION_AUTHORITY_EXPANDED = NO
NORMALIZATION_ACTIVE_AUTHORIZATION_CREATED = 0
UNRESOLVED_OBJECTS_NORMALIZED = 0
LEGACY_CAPTURE_PROMOTED_TO_READY = NO
COMPAT_EMBEDDINGS_CREATED = 0
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

The next bounded step, if separately authorized, is representation bootstrap
for a normal/current R2. It is not opened by this document.

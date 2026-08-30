# TORMENT Memory Substrate — Phase 7G5B1

## Legacy admission → native runtime readiness preflight

This slice freezes the administrative boundary between the completed 7F
legacy-evidence admissions and the qualified A3D STAGING runtime profile. It
adds a pure, read-only `NativeMigrationRuntimeReadinessPreflight`; it does not
start B2, migration, reconciliation, activation, cutover, or Fabric routing.

The preflight accepts only a typed immutable `MigrationRuntimeScopePlan` and a
qualified `NativeRepresentationLane`. The plan identifies the exact legacy
source namespace, workspace and private-agent/shared-domain target,
identity/semantic/motif/idempotency namespaces, and optional explicit motif
domain. Its canonical digest is included in every report. The plan is an
operator input, not a semantic fact and not B2 authority.

## Read-only contract

The preflight validates the current schema and then reads a named admitted
snapshot. It records no operation, transition, revision, representation,
integrity expectation, measurement, reconciliation case, migration marker,
side-store row, or file. It fingerprints the relevant durable carriers before
and after its reads and refuses if they differ. A report always declares
`durable_effect_count = 0` and `authority_expansion_count = 0`.

It only permits the existing qualified deployment posture:

```text
core_role = STAGING
deployment_state = LEGACY_ACTIVE
referenced_core_id = NULL
schema = 1.2
```

`CUTOVER_PENDING`, `NATIVE_ACTIVE`, `ACTIVE_CORE`, a referenced core, an
incorrect supplied core ID, and a non-v1.2 schema are reported as deploy-gate
failures. No process-local SQLite replacement or runtime-gate workaround is
part of the qualification.

## Frozen admission-to-runtime gap

7F imported core nodes as R1 `LEGACY_PREDECESSOR_UNKNOWN` evidence with an
unknown scope, unknown lifecycle/governance, no native provenance, and a
namespaced EID/order carrier. A 7F `LEGACY_EMBEDDING_CAPTURE` is deliberately:

```text
readiness = UNKNOWN
operational disposition = RECONCILIATION_REQUIRED
integrity expectation = absent
```

It remains that way. The preflight never promotes it to READY, attaches it to
a normal revision, or mutates/relabels the imported R1. A future usable vector
must be a new `COMPAT_EMBEDDING` bound to a normal/current revision (normally
R2) with the ordinary A3D expectation, measurement, READY and publication
facts.

Captured vectors receive one of these non-authorizing strategy labels:

```text
BYTE_DERIVATION_POSSIBLE
REEMBED_REQUIRED
UNUSABLE_VECTOR_EVIDENCE
NO_VECTOR_PRESENT
```

`BYTE_DERIVATION_POSSIBLE` requires valid finite float32 bytes, matching
dimension, NPY evidence, and matching provider/model metadata. It still says
only that a future B2 deterministic rule could be evaluated. Numeric equality
does not establish provider/model identity, and the 7F captured contract is
not silently converted to `compat-embedding-v1`.

## Classifications

Core objects retain one primary result:

```text
RUNTIME_READY_AS_IS
DETERMINISTIC_NORMALIZATION_REQUIRED
REPRESENTATION_BOOTSTRAP_REQUIRED
SEMANTIC_FACTS_UNRESOLVED
QUARANTINED_OR_UNSUPPORTED
EVIDENCE_ONLY_NOT_RUNTIME_OBJECT
```

The report keeps independent governance, provenance, lifecycle, scoped EID,
first-surviving-JSONL order, representation, and secondary-blocker evidence.
It exposes flattened representation rows as well as object rows, including a
separate `reembed_required_count`; `NO_VECTOR_PRESENT` is retained as an
object-level strategy when no capture exists to identify.
Missing governance is never projected as an all-false vector. There is no
frozen protected-marker default rule in 7F, so the report exposes the
`DERIVABLE_BY_FROZEN_LEGACY_RULE` vocabulary without inventing an instance.
Likewise descriptive provenance is not manufactured into `ProvenanceV1`.

Motifs are also assessed separately. A 7F
`LEGACY_DERIVED_MOTIF` and its admitted memberships are evidence, not an A3B
`DERIVED_MOTIF`; the object-kind, scope, identity, alias, and geometry gaps
are visible as blockers. When a row can actually be called ready as-is, the
preflight delegates the eligibility claim to the existing
`NativeCompatEmbeddingReader` and `NativeMotifRuntimeReader`; it does not
imitate either reader in SQL.

The side-store inventory explicitly retains the existing external owners for
conflicts, anchors, affect history, Hivemind/collective data and related
process state. Identity definitions and proposal effective state remain 7F
primary facts; deep-memory captures remain evidence only. Character,
bridges, checkpoints, and trajectory persistence are future parity work.

## B2 topology (not implemented here)

The report can recommend one of three future work sequences, but executes
none:

```text
semantic scope/governance/provenance/lifecycle normalization first
then representation bootstrap
```

Any B2 authority must be limited to valid legacy evidence, a frozen
deterministic rule, and an explicit revalidated scope plan. It must create a
new normal revision/representation topology and must not rewrite imported R1
admission facts. Reports are observational and can become stale; B2 must
revalidate the snapshot, core, plan, and current facts at execution time.

## Qualification evidence

`tests/test_substrate_migration_runtime_readiness.py` uses a real small 7F
rehearsal: namespaced core EIDs and first-appearance order, an UNKNOWN
captured vector, and an admitted legacy motif/membership. It proves the
preflight creates zero durable effects, classifies the missing semantic facts,
keeps the capture non-READY, reports byte derivation only as a future rule,
reports the legacy motif normalization gap, refuses an ambiguous scope plan,
classifies wrong dimension/dtype/provider/model or corrupt capture evidence,
proves a fully explicit current R2 plus READY representation is accepted only
through the existing A3D reader, and refuses a cutover deployment posture.

## Qualification declarations

```text
B1_MIGRATION_RUNTIME_READINESS_PREFLIGHT = COMPLETE
B1_PREFLIGHT_IS_READ_ONLY = YES
B1_PREFLIGHT_CREATED_DURABLE_EFFECTS = 0

LEGACY_ADMISSION_CONTRACT = FROZEN
A3D_RUNTIME_BOOTSTRAP_CONTRACT = FROZEN
ADMISSION_TO_RUNTIME_GAP = CLASSIFIED
RUNTIME_SCOPE_GAP_CLASSIFIED = YES
GOVERNANCE_GAP_CLASSIFIED = YES
PROVENANCE_GAP_CLASSIFIED = YES
LIFECYCLE_GAP_CLASSIFIED = YES
REPRESENTATION_GAP_CLASSIFIED = YES
MOTIF_GAP_CLASSIFIED = YES
SIDE_STORE_RETENTION_CLASSIFIED = YES

LEGACY_CAPTURE_PROMOTED_TO_READY = NO
LEGACY_ADMISSION_REVISION_REWRITTEN = NO
AUTHORITY_EXPANDED = NO
NORMALIZATION_TOPOLOGY = FROZEN
RUNTIME_REPRESENTATION_BOOTSTRAP_TOPOLOGY = FROZEN
SCHEMA_VERSION = 1.2

NATIVE_ACTIVE = NO
DUAL_WRITE = NO
DUAL_READ = NO
CUTOVER_OPENED = NO
A3D_CORE_STORAGE_RUNTIME_ROUTE = QUALIFIED
A3D_NATIVE_ROUTE_WIRED_INTO_FABRIC = NO
```

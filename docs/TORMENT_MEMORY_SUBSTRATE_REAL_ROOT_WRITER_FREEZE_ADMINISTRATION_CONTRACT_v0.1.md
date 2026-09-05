# TORMENT Memory Substrate — Real-Root Writer-Freeze Administration Contract v0.1

## Status and authority boundary

```text
FROZEN_ADMINISTRATION_CONTRACT
WRITER_FREEZE_NOT_YET_AUTHORIZED
REAL_ROOT_CONTACT_NOT_AUTHORIZED
ADMISSION_NOT_AUTHORIZED
NORMALIZATION_NOT_AUTHORIZED
ACTIVATION_NOT_AUTHORIZED
```

This is a repository and frozen-evidence reconciliation performed at
`1dd05afd985edae771926eed1a10f8cd9269a421`. It made no contact with
`data/`, started no service, loaded no provider or model, and did not inspect
Brainvision or a second cognitive function.

The future subject is the one production memory root:

```text
C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric\data
```

```text
WRITER_FREEZE = SOURCE_EPOCH_STABILIZATION
WRITER_FREEZE != ADMISSION
WRITER_FREEZE != NORMALIZATION
WRITER_FREEZE != CUTOVER
WRITER_FREEZE != ACTIVATION
WRITER_FREEZE != POINT_OF_NO_RETURN
```

The freeze is releasable before separately authorized admission. P6
`ACTIVATE_CORE`, not freeze, remains the durable point of no return.

## Existing witness and the required future freeze evidence

The existing canonical carrier is
`root_blocker5_binding.RootWriterFreezeWitness`. It binds:

```text
data_root_identity
writer_freeze_operation_identity
writer_evidence_digest
```

It is root-scoped writer-drain evidence, not a transaction or deployment
authority. Its digest must be the canonical digest of an operator-owned,
fresh, contents-safe writer-evidence payload. That payload is not a second
freeze authority; it is the evidence whose digest is carried by the existing
witness. It must identify, at minimum:

```text
data_root_identity
writer-freeze operation identity
operator identity
freeze epoch / time identity
each covered writer class
each writer's STOPPED or DRAINED result
the method and observation identity supporting that result
root-admission-description contract/version expected for the epoch
```

The covered class list must be regenerated from the freeze-time owner/runtime
census, rather than assuming that a `python -m torment_service` process is the
only writer. At minimum it must account for the legacy memory-graph persistence
path (nodes, edges, events, per-EID vectors and shard-backed embeddings), the
Fabric routes that invoke it, embedding-shard and trajectory writers, and every
freshly observed direct-writer or owner-specific source producer. Derived
SQLite indexes are not canonical memory authority, but any live process that
can cause a canonical-source write remains covered. A vague attestation such
as "service stopped" is insufficient.

The current code accepts the witness digest but provides neither a
root-wide process-controller nor a typed canonical schema for the payload it
hashes. Static source comments also retain direct-writer bypasses outside the
ordinary `TormentFabric.ingest` and `MemoryGraph.spawn_memory` choke points.
Therefore no future administration may claim complete writer coverage merely
from the current three-field witness.

```text
ROOT_WRITER_FREEZE_WITNESS = REQUIRED
ROOT_WIDE_WRITER_STOP_DRAIN_PROOF = REQUIRED
WRITER_EVIDENCE_PAYLOAD_SCHEMA = REQUIRED_BEFORE_EXECUTION
CURRENT_CODE_ENFORCES_ROOT_WIDE_DRAIN = NO
```

## Fresh frozen-epoch evidence

Once a future operator authorizes only the writer-freeze administration, the
covered writers must first be stopped or drained. While that condition holds,
fresh evidence—not historical reports—must be captured for:

1. bounded discovered root census;
2. declared root census;
3. explicit source manifest;
4. representation census;
5. external-owner observation set and digest;
6. owner-specific geometry-disposition table confirmation;
7. root runtime-scope plan and digest;
8. root/deployment profile evidence;
9. fresh eligibility of `EMPTY_PRIVATE`, `DECLARED_EMPTY_SHARED`,
   `UNKNOWN_IDENTITY`, and hash-normalization source postures; and
10. the `RootWriterFreezeWitness` above.

The discovered census is limited to the canonical root boundaries already
defined by `discover_canonical_root_layout`: workspaces, materialized private
scopes, and materialized shared scopes. It must be reconciled against the
complete declared plan; neither an undeclared materialized scope nor an
unaccounted declaration may be silently omitted.

Every declared root entry must have exactly one typed posture/disposition:

```text
MATERIALIZED_MEMORY_SCOPE
DECLARED_EMPTY_SHARED
EMPTY_PRIVATE
SOURCE_CAUSED_NONPUBLIC_ENTRY
```

The historical comparison values are not freeze-time truth:

```text
workspaces = 51
private directories = 76; canonical graphs = 75; EMPTY_PRIVATE = 1
materialized shared scopes = 48; declared-empty shared obligations = 30
target ST/BGE/384 scopes = 71; hash scopes = 50
UNKNOWN_IDENTITY scopes = 3
```

Any mismatch is an epoch invalidation, not a repair instruction.

## Scope, topology, and representation contract

The fresh plan must retain the public topology law:

```text
PUBLIC private scopes = 0..n
PUBLIC shared scopes = 1..n
DECLARED_EMPTY_SHARED counts as an admitted future shared obligation
NO public workspace may have zero admitted shared lanes
```

`orchard|PRIVATE|aria` may be planned only as `PUBLIC_NATIVE_EMPTY_PRIVATE`
after fresh evidence again proves valid identity, a private directory, absent
canonical nodes, and no canonical-memory contradiction. It receives no memory
content and creates no agent.

The fresh plan must retain these three source facts only after a fresh exact
Phase 9B recheck:

```text
ws3|PRIVATE|a1
ws4|PRIVATE|a1
ws5|PRIVATE|a1

SOURCE_REPRESENTATION_IDENTITY = UNKNOWN
NORMALIZATION_DISPOSITION = REEMBED_FROM_CANONICAL_SOURCE
```

No historical provider or model may be manufactured from dimensions, dtypes,
paths, or filenames. Known hash scopes remain `REEMBED_REQUIRED` under their
existing qualified normalization path.

## Runtime scope and namespace-binding contract

For every scope admitted by the fresh declaration, the immutable plan must use
the existing `MigrationRuntimeScopePlan` payload and bind:

```text
workspace_id, scope_kind, qualifier
legacy_source_namespace_id
target_identity_namespace_id
target_semantic_scope_id
motif_alias_namespace_id
motif_identity_namespace_id
membership_identity_namespace_id
idempotency_namespace_id
motif_domain_id where applicable
source posture and representation disposition
```

The following is pre-freeze bindable once fresh evidence exists: the complete
ordered `RootScopeKey` set, its qualifier, materialization posture, source
eligibility/disposition, required target lane, and the rule that one plan's
canonical `intent()` is included in the ordered root runtime-scope-plan digest.

The seven UUID namespace/scope bindings are not lawfully derivable from a
directory, human EID, or another lane. Existing admission code explicitly
treats source paths and native namespaces as caller-owned data, then validates
or creates those supplied identities during admission. No deterministic
root-key-to-UUID derivation law exists to apply now. The later binding rule is
therefore: generate or otherwise obtain the exact UUID bundle only in
freeze/admission preparation, validate it as one typed
`MigrationRuntimeScopePlan` per `RootScopeKey`, sort it canonically, and bind
the resulting `root_runtime_scope_plan_digest` into the immutable envelope
before any P2/P3 operation. It must never be reconstructed by an operator
afterward.

```text
REAL_ROOT_NAMESPACE_PLAN_PREPARABLE = PARTIALLY
PRE_FREEZE_BINDABLE = SCOPE_KEYS_POSTURES_DISPOSITIONS_AND_PLAN_SCHEMA
FREEZE_ADMISSION_DERIVED = ALL_CONCRETE_NAMESPACE_UUID_BINDINGS
```

## Immutable description and later-only envelope

After frozen evidence exists, but not in the first freeze administration, the
future `RootNativeProductionAdmissionDescription` must bind the root identity,
fresh declared census, explicit source manifest, external-owner observations,
feature posture, target lane, and declared runtime scope identities/postures.
Its current contract deliberately cannot self-witness writer freeze or carry
the concrete UUID plan.

The existing `RootAdmissionEnvelope` is the later P2-level immutable object
that completes the required freeze-to-admission binding. It adds the
`RootWriterFreezeWitness`, fresh discovered-census parity,
geometry-disposition-plan digest, qualified deployment-profile digest,
root-profile identity, membership-closure digest, and the ordered runtime-scope
plan digest. It is not created during the first freeze/evidence capture and it
does not authorize its own use.

No new root object is created by this phase.

## Epoch invalidation and safe release

The frozen epoch is void if any covered writer resumes; an admission-relevant
source file, census, manifest, required owner observation, representation
eligibility, profile, geometry table, or scope plan changes; or the operator
deliberately releases the freeze.

```text
FROZEN_EPOCH = VOID
OLD_CENSUS_MANIFEST_WITNESS = NOT_ADMISSION_AUTHORIZING
NEW_FREEZE = REQUIRES_ALL_FRESH_EVIDENCE
```

Before separately authorized admission/cutover, release is safe only by ending
the external drain and discarding the witness/evidence as non-authorizing. It
must perform none of the following:

```text
selector change
native core creation or activation
CUTOVER_PENDING
admission
normalization or re-embedding
source or geometry disposition execution
legacy deletion, retirement, or public-native activation
```

The first real administration therefore ends after fresh evidence capture and
human/architecture review. Claude review is needed only if the review finds
ambiguity or contradiction. A later, separate authorization is required for
admission; another is required for P6 activation.

## Persistence boundary and execution block

`RootWriterFreezeWitness` is an in-memory immutable evidence value. The
currently available persistent root-envelope record belongs to the later P2
cutover stream and is therefore forbidden during writer-freeze-only work. No
qualified, dedicated freeze-evidence file or database location exists in the
current repository. This contract does not invent one, and no mutation inside
legacy memory content is permitted.

Consequently, the exact future freeze administration is not yet executable as
a complete, mechanically verified root-wide operation: it lacks a qualified
writer-controller, exhaustive freeze-time writer-census schema, and approved
persistence semantics for the witness evidence. The architecture supports the
future shape, but this gap must be resolved and separately reviewed before any
real-root freeze may be attempted.

```text
STOP_FOR_ARCHITECTURE_REVIEW = YES
WRITER_FREEZE_ARCHITECTURALLY_READY = YES
WRITER_FREEZE_EXECUTION_MECHANISM_COMPLETE = NO
```

## This phase's non-claims

```text
PRODUCTION_CODE_CHANGES = 0
TEST_CODE_CHANGES = 0
TESTS_RUN = 0
REAL_ROOT_CONTACT = NONE
SERVICE_STARTED = NO
PROVIDER_CONTACT = NONE
MODEL_LOADING = NONE
BRAINVISION_OPENED = NO
SECOND_COGNITIVE_FUNCTION_INSPECTED = NO
TORMENT_MATHEMATICS_CHANGED = NO
```

The authorization string that may begin a future freeze-and-evidence-only
administration—after the architecture-review gap above is resolved—is exactly:

```text
REAL_ROOT_WRITER_FREEZE_EVIDENCE_ADMINISTRATION = YES
```

That authorization must be interpreted as freeze, fresh evidence capture, and
STOP only. It does not authorize admission, normalization, `CUTOVER_PENDING`,
or activation.

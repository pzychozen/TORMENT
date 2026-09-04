# TORMENT Memory Substrate — Post-I4 Root-Wide Convergence Ratification v0.1

## Status and authority

```text
STATUS = FROZEN_ARCHITECTURE_CONTRACT
IMPLEMENTATION_NOT_YET_QUALIFIED = YES
REAL_ROOT_NOT_AUTHORIZED = YES
REAL_PRODUCTION_ACTIVATION_AUTHORIZED = NO
```

This is the final architecture-contract freeze before bounded synthetic implementation of the generalized root-admission to existing Blocker-5 binding. It ratifies the Post-I4 convergence delta archaeology and Claude review `TORMENT_POST_I4_ROOT_WIDE_CONVERGENCE_SAFETY_ADVERSARIAL_REVIEW.md`; it does not reopen their historical investigations.

No selector, core, admission, root profile, external owner, service, model, or production runtime behavior is created or changed. No TORMENT kernel, SRG, Character, query, post-write, or other cognitive formula changes.

```text
SECOND_CUTOVER_CONTROLLER_REQUIRED = NO
NEW_DEPLOYMENT_AUTHORITY_REQUIRED = NO
NEW_PROGRESS_LEDGER_REQUIRED = NO
POST_ACTIVE_LEGACY_ROLLBACK = REFUSED
POINT_OF_NO_RETURN = P6_ACTIVATE_CORE_DURABLE_COMMIT
```

The existing `OfflineCutoverController`, deployment selector, core-maintenance authority, selector/core agreement model, and deployment diagnostic remain the surviving deployment-administration model. A future generalized root form binds into it; it must not add a controller, selector, active-core authority, mutable cutover ledger, dual read, or dual write authority.

## Initial production-profile posture

```text
compression_enabled = false
deep_memory_enabled = false

new_unadmitted_scope_creation = REFUSED
trace = EXPLICIT_BOUNDED_REFUSAL
shared_true_split = EXPLICIT_BOUNDED_REFUSAL
archive_recall = EXPLICIT_BOUNDED_REFUSAL
scoped_reference_foregrounding = EXPLICIT_BOUNDED_REFUSAL
legacy_only_public_operations = EXPLICIT_BOUNDED_REFUSAL
```

These are initial-profile boundaries, not deletion, deprecation, or a claim that the refused effects are unlawful in another qualified profile. Any future enablement requires separate parity, recovery, and profile qualification.

```text
INITIAL_DEEP_MEMORY_ENABLED = NO
ARCHIVE_RECALL_NATIVE = REFUSED
```

## Owner-specific geometry-state disposition model

```text
GEOMETRY_STATE_DISPOSITION_MODEL = OWNER_SPECIFIC
```

The disposition table is complete, immutable, digested, and bound in root-admission identity at or before P2. No owner remains `UNRESOLVED` at that boundary. Historical geometry provenance may be carried by the later disposition-execution receipt; historical owner records need not be rewritten solely to add epoch labels.

For concise status reporting, the labels below map directly to the fuller
dispositions in the frozen table.

```text
GEOMETRY_STATE_DISPOSITION_MODEL = OWNER_SPECIFIC
CHARACTER_BASELINE_DISPOSITION = RECOMPUTE_TARGET_GEOMETRY_BASELINE
SRG_PAYLOAD_DISPOSITION = RETAIN_EXACTLY
CHECKPOINT_CALIBRATION_DISPOSITION = REINITIALIZE_ONLY
PROPOSAL_REGISTRY_DISPOSITION = RETAIN_WITH_CONSUMER_GUARD
DEEP_MEMORY_INITIAL_POSTURE = DISABLED
```

| Owner/state | Frozen disposition | Contract |
|---|---|---|
| CharacterStore active baseline: `distance_to_seed`, `drift_direction` | `RECOMPUTE_TARGET_GEOMETRY_BASELINE` | Recompute `distance_to_seed` from normalized target-lane state. Keep `drift_direction` stable at transition, so a legacy-geometry distance is never compared with an ST/BGE distance for first post-transition direction. Do not reset Character identity or seed. |
| Character drift history | `RETAIN_AS_HISTORICAL_GEOMETRY_EPOCH_STATE` | Do not recompute historical observations. |
| Character seed | `RETAIN` | Preserve exactly. |
| SRG memory-payload markers | `RETAIN_EXACTLY` | Recompute and invalidation are forbidden. These frozen memory-payload facts may preserve legacy-derived bands alongside target-geometry future behavior. No kernel or SRG mathematics changes. |
| Checkpoint calibration: `disp_buffer`, `last_effective_scale` | `REINITIALIZE_CALIBRATION_ONLY` | Use the kernel's existing lawful cold-start/warm-up path. Preserve other lawful checkpoint cognitive state; no formula change. |
| Proposal registry | `RETAIN_UNMODIFIED` | Do not rewrite the append-only registry. Initial native profile refuses proposal-processing routes. Future consumers must refuse `ShareProposal.embedding` as active-lane geometry unless its representation identity matches the active lane, or re-embed from retained semantic source text. |
| Bridge decision/status | `RETAIN` | Preserve decision provenance. |
| Bridge legacy geometry confidence | `RETAIN_AS_HISTORICAL_GEOMETRY_EPOCH_STATE` | Do not recreate or destroy provenance. |
| Hivemind / collective historical geometry scores | `RETAIN_AS_HISTORICAL_GEOMETRY_EPOCH_STATE` | No history deletion. |
| World / trajectory | `RETAIN` | Preserve current owner semantics. |
| Deep memory / archive vectors | `RETAIN_UNTOUCHED` | Deep memory remains disabled and native archive recall remains refused. Future enablement needs separate representation-normalization, parity, and recovery qualification. |
| Conflict, Role, affect, identity | `GEOMETRY_DISPOSITION_REQUIRED = NO` | Preserve existing external ownership. |

## Two-stage activation contract

### P2 — `CUTOVER_PENDING`

At or before P2:

```text
owner-specific geometry disposition table = COMPLETE / IMMUTABLE / DIGESTED
BOUND_IN_ROOT_ADMISSION_IDENTITY = YES
UNRESOLVED_OWNER_DISPOSITION = NO
EXTERNAL_OWNER_DISPOSITION_MUTATION = NO
```

`CUTOVER_PENDING` is a maintenance fence, not the execution point for the disposition table.

### P6 precondition — root completion

Before `activate_core`, `ROOT_COMPLETION_VALID = YES` establishes at minimum:

```text
immutable root admission-envelope agreement
root-scoped writer-freeze witness
manifest byte recheck
DISCOVERED_CENSUS == DECLARED_CENSUS
root normalization closure
target representation agreement
staging core identity agreement
qualified deployment-profile agreement
root-profile revision identity
root-scope membership closure
owner-specific disposition PLAN fully resolved
no second asserting core
core never previously active
```

Disposition execution is deliberately not part of this completion proposition.

### P6 — durable point of no return

The durable `ACTIVATE_CORE` commit remains the point of no return. It must not move earlier. After it commits, return to legacy authority is refused.

### P6 to P7 — native-active, externally pending

```text
selector = CUTOVER_PENDING
resolver/public authority = MAINTENANCE_ONLY
legacy rollback = REFUSED
DISPOSITION_EXECUTION_BOUNDARY = AFTER_P6_ACTIVATE_CORE_COMMIT / BEFORE_P7_SELECTOR_NATIVE_ACTIVATION
```

Only the frozen owner-specific actions may run here. They must be idempotent and recoverable and produce one immutable `RootDispositionExecutionReceipt`, or equivalently narrow evidence. The receipt is evidence only, not deployment authority or a mutable progress ledger.

A retain-only result may bind `owner identity`, `writer-frozen owner/source digest`, `legacy geometry epoch`, `chosen disposition`, and `execution/no-mutation result` without rewriting history. After a P6 failure, recovery is repair-forward under native authority; legacy rollback is not a recovery path.

### P7 — selector activation

```text
P7_RECEIPT_BINDING_REQUIRED = YES
activate_selector_native BINDS disposition_execution_receipt_digest IN ITS OPERATION INTENT
MISSING_OR_INVALID_RECEIPT = P7_REFUSED
```

## Root completion witness

The generalized form is `AdmissionCompletionWitness v2`, or an equivalently named versioned successor of the same completion-evidence contract. It occupies the existing `ACTIVATE_CORE` completion-evidence role and creates no second completion authority.

```text
EXPLICIT_CONTRACT_DISCRIMINATOR = REQUIRED
EXPLICIT_VERSION = REQUIRED
V1_HISTORICAL_DECODING = PRESERVED
SENTINEL_WORKSPACE_ID = FORBIDDEN
ROOT_SCOPED_SEMANTICS = REQUIRED
```

It binds at minimum:

```text
data_root_identity
root admission-envelope digest
declared-census digest
discovered-census digest
manifest digest
external-owner observation digest
geometry-disposition-table digest
target representation identity
root writer-freeze witness digest
native staging core id
qualified deployment-profile digest
root-profile object/revision/ordinal
root-membership-closure digest
```

The root-profile object is not completion evidence; it is an identity input bound by the completion witness.

## Discovered census, writer freeze, and manifest law

```text
DISCOVERED_CENSUS_EQUALS_DECLARED_CENSUS_REQUIRED = YES
ROOT_SCOPED_WRITER_FREEZE_WITNESS_REQUIRED = YES
```

Discovery is bounded, structural, writer-frozen, and restricted to canonical TORMENT memory-layout doctrine. It discovers at least workspaces, materialized private scopes, materialized shared scopes, and canonical `RootScopeKey`s. It does not create a recursive whole-root content fingerprint, and unrelated co-located files do not become migration objects merely because they exist. A discovered canonical materialized scope absent from the declaration refuses root completion.

The generalized writer-freeze witness binds `data_root_identity` and replaces workspace-specific drain semantics for the generalized form. Manifest bytes must be verified at normalization start, P4 completion verification, and immediately before P6 `activate_core`. Drift at any required check refuses.

## Membership recovery

```text
RootScopeKey(workspace_id, scope_kind, qualifier)
```

Runtime scope bundles must recover from durable evidence bound to the same root completion identity. Operator-reconstructed namespace maps are not accepted. Recovery retains semantic-scope equality, profile-revision binding, duplicate-key refusal, retired-membership refusal, and cross-workspace isolation.

## P0 wording correction

I4G does not close real ST/BGE production merely because it closed its bounded synthetic deterministic-3 profile.

```text
EXTERNAL_OWNER_CENSUS =
    CLOSED_FOR_SYNTHETIC_I4G
    OPEN_FOR_REAL_ST_BGE_384_PROFILE_EVIDENCE

CHARACTER_PARITY =
    CLOSED_FOR_SYNTHETIC_I4G
    OPEN_FOR_REAL_ST_BGE_384_PROFILE_EVIDENCE
```

Real-root qualification, admission, and activation remain separately authorized operations.

## Boundaries and next phase

```text
PRODUCTION_CODE_CHANGES = 0
TESTS_RUN = 0
REAL_ROOT_ACCESS = NO
MODEL_OR_PROVIDER_CONTACT = NO
SELECTOR_OR_CORE_MUTATION = NO
ACTIVATION = NO
RETIREMENT = NO
BRAINVISION_SOURCE_CONTENT_OPENED = NO
BRAINVISION_FILES_TOUCHED = 0
SECOND_REPOSITORY_COGNITIVE_FUNCTION_INSPECTED = NO
TORMENT_MATHEMATICS_PRESERVED = YES
```

This contract does not modify deployment, admission, normalization, membership, Character, SRG, checkpoint, proposal, bridge, collective, deep-memory, or production-owner code. The next possible phase is bounded synthetic implementation of the generalized root-admission to existing Blocker-5 binding, subject to this contract and separate implementation qualification.

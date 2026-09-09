# TORMENT Database Convergence: Real-Root Corrective P1/P2 / Envelope D v0.1

## Result

`REAL_CORRECTIVE_P1_P2 = PASS`

The obsolete never-active P1/P2 proposition was superseded through the
canonical pre-P5 selector-only recovery seam. A distinct corrected P1 core
and immutable P2 Envelope D now hold the maintenance-only proposition. The
operation stopped at P2; no P3 or later phase was called.

## Starting and final authority

```text
STARTING_HEAD = 7bc367c936ab892e6f4633d957382b98cc83d1a1
ORIGIN_MAIN_AT_START = 7bc367c936ab892e6f4633d957382b98cc83d1a1
TRACKED_WORKTREE_AT_START = CLEAN

REAL_ROOT = C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric\data
REAL_ROOT_CONTACT = P1/P2 ADMINISTRATION; READ-ONLY SOURCE/FREEZE RECHECK

INITIAL_SELECTOR_STATE = CUTOVER_PENDING (generation 5)
INITIAL_PUBLIC_API_POSTURE = MAINTENANCE_ONLY
SAFE_ROOT_PENDING_ABORT = PRE_P5_CANONICAL_SPECIALIZATION
POST_ABORT_LEGACY_AUTHORITY = LEGACY_PUBLIC

FINAL_SELECTOR_STATE = CUTOVER_PENDING (generation 7)
FINAL_PUBLIC_API_POSTURE = MAINTENANCE_ONLY
PENDING_PROPOSITION_CORE = f21c730f-5222-4aa8-9a5f-1c1188456df3
PENDING_PROPOSITION_ENVELOPE = e4e510131cc341375485605bf1ead86aff684a1ca938e26fdbe221bbf0673ceb
```

`supersede_root_external_pending_pre_p5()` is the qualified specialization of
the requested safe pre-P6 pending abort. It proved the historical core inert,
changed only selector authority to legacy, and retained the historical core
and Envelope C.

## Historical predecessor preservation

```text
HISTORICAL_CORE_PATH = data\substrate\cores\root-native-staging-0e9cb4b7-cf57-49fa-b60a-0e5a25f9d288.db
HISTORICAL_CORE_ID = 0e9cb4b7-cf57-49fa-b60a-0e5a25f9d288
HISTORICAL_CORE_SHA256_BEFORE_AND_AFTER = 3e01e2a2e359f9e87e2a4b19b5a930763a28b75b7497cdc1574813e91a6d3ce4
HISTORICAL_CORE_UNCHANGED = YES
HISTORICAL_CORE_ROLE = STAGING
HISTORICAL_CORE_DEPLOYMENT = LEGACY_ACTIVE
HISTORICAL_CORE_EVER_ACTIVE = NO
HISTORICAL_CORE_NATIVE_ACTIVATION_WITNESS = NONE
HISTORICAL_CORE_SELECTED_AS_NATIVE = NO

ENVELOPE_C_DIGEST = d97c0545a538efca9657119abac133efc010bc41191b35f9e74ce9885f79b34b
ENVELOPE_C_PRESENT = YES
ENVELOPE_C_UNCHANGED = YES
ENVELOPE_C_REWRITTEN = NO
```

The current workspace freeze snapshot exactly remained the historical
1,748-file snapshot:

```text
WORKSPACE_TREE_DIGEST = 52ff2f04d839015d43ef73a0ad02415d19587126ff2e6e0b3fbe4737f4487275
WORKSPACE_MAX_MTIME_NS = 1788363578805346200
TOP_LEVEL_NODES_SHA256 = 4cfdf4c33dd2b14d6101f03c6218af997ebcbc02241eb1b9135dd3f01f406279
TOP_LEVEL_EMB_1_SHA256 = fd190080f525b22fb9c2609c1723d41c1c79162c4c99d7ac65185437e8a84507
SOURCE_SEMANTICS_CHANGED = NO
FROZEN_LEGACY_EVIDENCE_CHANGED = NO
```

## Corrected P1 and Envelope D

```text
CORRECTED_CORE_PATH = data\substrate\cores\root-native-staging-f21c730f-5222-4aa8-9a5f-1c1188456df3.db
CORRECTED_CORE_ID = f21c730f-5222-4aa8-9a5f-1c1188456df3
CORRECTED_CORE_DISTINCT = YES
CORRECTED_CORE_SCOPE_COUNT = 154
CORRECTED_CORE_ROLE = STAGING
CORRECTED_CORE_DEPLOYMENT = LEGACY_ACTIVE
CORRECTED_CORE_EVER_ACTIVE = NO
CORRECTED_CORE_NATIVE_ACTIVATION_WITNESS = NONE
CORRECTED_CORE_PUBLIC_AUTHORITY = NO

LEGACY_SOURCE_NAMESPACE_ID = preserved per-scope P1 namespace set (154)
MOTIF_ALIAS_NAMESPACE_ID = new per-scope UUIDv4 namespace set (154)
MOTIF_ALIAS_NAMESPACE_KEY_SCHEME = real-root-corrective-p1-p2-20260909:motif-alias:<canonical-scope-key>
MOTIF_ALIAS_NAMESPACE_SEPARATION = PASS (154 / 154 durable namespace records)

ENVELOPE_D_ID = RootAdmissionEnvelope/e4e510131cc341375485605bf1ead86aff684a1ca938e26fdbe221bbf0673ceb
ENVELOPE_D_DIGEST = e4e510131cc341375485605bf1ead86aff684a1ca938e26fdbe221bbf0673ceb
ENVELOPE_D_DESCRIPTION_DIGEST = d043f3d4a7303f055d0410bb655505791a02c8cf88f46a4bcf864b13694adff7
ENVELOPE_D_PROFILE_DIGEST = 35ec54a0d5d3a2c87fedc855f8964615e4472876c3698488ba925a41a2ae717a
ENVELOPE_D_DISTINCT_FROM_C = YES
ENVELOPE_D_WRITER_FREEZE_RECORD = PRESENT
```

The fresh pre-P2 census found zero root-target processes and zero listeners
at `127.0.0.1:8787`. Envelope D was durably reread from the corrected core;
the selector then bound that exact digest and core.

## Bounded corrective implementation and retained residue

The existing P2 carrier type incorrectly required P3 snapshots and B3/B4
children even though P2 may only bind P1 scope identities. A typed
`RootP2ScopePlanCarrier` now carries the exact P2 plan set without minting or
dispatching P3 work. P3 still requires a real `RootNormalizationRequest`.

The first real P1 attempt exposed a second boundary defect: UUIDv5 profile
namespace values were rejected by native UUIDv4 storage after schema creation
but before any namespace, profile, membership, envelope, selector, or
activation record was committed. The P1 boundary now rejects non-v4 native
identifiers before it can create a core. The schema-only failed-core residue
was retained rather than deleted or reused:

```text
RETAINED_FAILED_P1_CORE = data\substrate\cores\root-native-staging-61cf7c92-398f-49cc-bad3-c980fbf2aab4.db
RETAINED_FAILED_P1_CORE_ID = 61cf7c92-398f-49cc-bad3-c980fbf2aab4
RETAINED_FAILED_P1_CORE_ROLE = STAGING
RETAINED_FAILED_P1_CORE_DEPLOYMENT = LEGACY_ACTIVE
RETAINED_FAILED_P1_CORE_EVER_ACTIVE = NO
RETAINED_FAILED_P1_CORE_NAMESPACE_OBJECT_OPERATION_MAINTENANCE_RECORDS = 0
RETAINED_FAILED_P1_CORE_SELECTED = NO
RETAINED_FAILED_P1_CORE_DELETED = NO
```

After a disposable exact 154-scope P1 rehearsal passed, a fresh third core
was created for the corrected proposition. The residue carries no public or
native authority and does not create dual read or write authority.

## Negative proofs and validation

```text
OLD_CORE_MUTATED = NO
OLD_CORE_ACTIVATED = NO
ENVELOPE_C_REWRITTEN = NO
NATIVE_PUBLIC_ACTIVATION = NO
DUAL_WRITE_OCCURRED = NO
DUAL_READ_AUTHORITY_OCCURRED = NO

REAL_P3_EXECUTED = NO
P4_EXECUTED = NO
P5_EXECUTED = NO
P6_EXECUTED = NO
P7_EXECUTED = NO
P3_DURABLE_SNAPSHOTS = 0
P3_DURABLE_ADMISSION_RECORDS = 0
P3_DURABLE_ARTIFACT_RECORDS = 0
P3_DURABLE_REPRESENTATIONS = 0

FOCUSED_TESTS = 34 passed
BROADER_TESTS = 81 passed, 1 skipped
P1_EXACT_154_SCOPE_DISPOSABLE_REHEARSAL = PASS
GIT_DIFF_CHECK = PASS
```

The pytest runs used the `torment` Conda environment and external temporary
directories. Their only warning was the pre-existing repository
`.pytest_cache` permission denial; it did not affect test outcomes.

```text
REAL_CORRECTIVE_P1_P2 = PASS
CORRECTED_SUCCESSOR_PROPOSITION = ESTABLISHED
NEXT_AUTHORIZATION_BOUNDARY = REAL_P3_REVIEW
```

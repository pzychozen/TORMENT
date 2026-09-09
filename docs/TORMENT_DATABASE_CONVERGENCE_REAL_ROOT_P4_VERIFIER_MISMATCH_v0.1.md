# TORMENT Database Convergence: Real-Root P4 Verifier Mismatch v0.1

## Result

`REAL_P4 = STOPPED_FOR_VERIFIER_MISMATCH`

P4 did not find source drift, broken P3 durability, authority drift, or a
certified-refusal runtime leak.  It stopped because the canonical P4
completion predicate still requires `root_normalization_ready = TRUE`, while
the canonical P3 aggregation deliberately defines that field as false for the
lawful `P3_DISPOSITION_CLOSED_WITH_CERTIFIED_EXCEPTIONS` outcome present in
this root.  This is the exact stale-predicate condition named in the P4 work
order; no P3 route, P5--P7 behavior, or real-root state was changed to bypass
it.

## Authority and preflight receipt

```text
STARTING_HEAD = 5d8f3a8ef1f4c37caa748336b6d99d71f87fc98c
FINAL_HEAD = recorded by the terminal Git receipt accompanying this committed record
ORIGIN_MAIN_AT_START = 5d8f3a8ef1f4c37caa748336b6d99d71f87fc98c
ORIGIN_MAIN_FINAL = final committed HEAD after the terminal push
TRACKED_WORKTREE_AT_START = CLEAN

REAL_ROOT = C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric\data
REAL_ROOT_CONTACT = READ-ONLY P4 PREFLIGHT AND DURABILITY VERIFICATION
REAL_P4_EXECUTED = NO — CANONICAL COMPLETION EVIDENCE WAS NOT LAWFULLY CONSTRUCTIBLE

SELECTOR_GENERATION_INITIAL = 7
SELECTOR_GENERATION_FINAL = 7
SELECTOR_STATE_FINAL = CUTOVER_PENDING
PUBLIC_API_POSTURE_FINAL = MAINTENANCE_ONLY

ENVELOPE_D_DIGEST = e4e510131cc341375485605bf1ead86aff684a1ca938e26fdbe221bbf0673ceb
CORRECTED_CORE_ID = f21c730f-5222-4aa8-9a5f-1c1188456df3
CORRECTED_CORE_PATH = data\substrate\cores\root-native-staging-f21c730f-5222-4aa8-9a5f-1c1188456df3.db
CORRECTED_CORE_SCOPE_COUNT = 154

CORRECTED_CORE_ROLE = STAGING
CORRECTED_CORE_DEPLOYMENT = LEGACY_ACTIVE
CORRECTED_CORE_EVER_ACTIVE = NO
CORRECTED_CORE_NATIVE_ACTIVATION_WITNESS = NONE
CORRECTED_CORE_PUBLIC_AUTHORITY = NO
```

The committed record cannot contain its own final Git object ID without a
self-referential hash cycle.  The terminal delivery receipt records the exact
final `HEAD` and synchronized `origin/main` after commit and push.

```text
HISTORICAL_CORE_SHA256 = 3e01e2a2e359f9e87e2a4b19b5a930763a28b75b7497cdc1574813e91a6d3ce4
HISTORICAL_CORE_UNCHANGED = YES
ENVELOPE_C_DIGEST = d97c0545a538efca9657119abac133efc010bc41191b35f9e74ce9885f79b34b
ENVELOPE_C_UNCHANGED = YES
FAILED_SCHEMA_CORE_ID = 61cf7c92-398f-49cc-bad3-c980fbf2aab4
FAILED_SCHEMA_CORE_INERT = YES
FAILED_SCHEMA_CORE_SELECTED = NO
FAILED_SCHEMA_CORE_ACTIVATED = NO
ENVELOPE_D_REWRITTEN = NO
LEGACY_SOURCE_SEMANTICS_CHANGED = NO
FROZEN_SOURCE_EVIDENCE_CHANGED = NO
```

## Durable P3 re-verification

The P3 administrator's read-only source comparison again found no source
epoch drift: 383 frozen artifacts, 2,076 source memories, 450 source motifs,
and the qualified Character census were all identical to the frozen P3 model.

```text
B1M = 2076
B2_ADMITTED = 2041
B2_REFUSED_SOURCE_SEMANTIC_GAP = 35
B2_UNACCOUNTED = 0

B4A = 183
B4B = 233
B4C = 0
B4P = 11
B4_REFUSED_MEMBER_SEMANTIC_GAP = 23
B4_UNACCOUNTED = 0
B4_OVERLAP = 0

CHARACTER_DISPOSITION_CLOSED = TRUE (37 / 37)
CHARACTER_CURRENT_DIGEST_FORM = 36 / 37
CHARACTER_QUALIFIED_HISTORICAL_COMPATIBLE_DIGEST_FORM = 1 / 37
TRUE_CHARACTER_SEMANTIC_MISMATCH = 0

CERTIFIED_REFUSAL_MEMORY_RUNTIME_LEAK = NO
CERTIFIED_REFUSAL_MOTIF_RUNTIME_LEAK = NO
```

The direct read-only core proof rechecked the durable P3 operations:

```text
ADMIT_LEGACY_NODE_CURRENT = 2076
MIGRATION_RUNTIME_NORMALIZATION = 1953
MIGRATION_CHARACTER_SEED_NORMALIZATION = 88
P3_B2_REFUSED_SOURCE_SEMANTIC_GAP = 35
PUBLISH_REPRESENTATION_READY = 2041
MIGRATION_RUNTIME_MOTIF_PROJECTION = 183
MIGRATION_RUNTIME_MOTIF_REGEOMETRY_PROJECTION = 233
RECORD_LEGACY_MOTIF_ADMISSION_QUARANTINED = 11
P3_B4_REFUSED_MEMBER_SEMANTIC_GAP = 23
```

It also found 35 refusal records with zero native-ordinary successors, zero
other/runtime-compatible/ready representations, zero qualified-reader
results, zero vector candidates, and zero vector-search hits.  The 23 motif
refusals each retained rejection evidence while having no target alias and no
runtime-reader result.

## Canonical P4 contradiction

The current canonical completion path is
`OfflineCutoverController.verify_root_completion()`, which delegates to
`root_blocker5_binding.verify_root_completion()`.  Its required predicate
`_require_normalization_complete()` rejects any result for which
`root_normalization_ready` is false.

The canonical root normalizer computes that field as true only when completion
and generalized readiness are true **and** no terminal certified exception is
present.  The verified real P3 result contains 35 B2 and 23 B4 certified
exceptions, so its truthful values are:

```text
ROOT_MEMORY_DISPOSITION_CLOSED = TRUE
ROOT_CHARACTER_DISPOSITION_CLOSED = TRUE
ROOT_MOTIF_DISPOSITION_CLOSED = TRUE
ROOT_DISPOSITION_CLOSURE = TRUE
ROOT_NORMALIZATION_COMPLETE = TRUE
ROOT_NORMALIZATION_READY = FALSE
P3_COMPLETION_CLASS = P3_DISPOSITION_CLOSED_WITH_CERTIFIED_EXCEPTIONS
```

A read-only typed invocation of the canonical P4 predicate with those
already-durably-rechecked P3 facts produced exactly:

```text
CANONICAL_P4_PREDICATE = REFUSED
ROOT_NORMALIZATION_CLOSURE_INCOMPLETE
```

Consequently:

```text
ROOT_COMPLETION_VERIFIED = NO — VERIFIER MISMATCH
COMPLETION_EVIDENCE_ID = NONE
COMPLETION_EVIDENCE_DIGEST = NONE
COMPLETION_EVIDENCE = NOT CONSTRUCTED
CORRECTED_CORE_CUTOVER_CANDIDATE = NOT VERIFIED
```

The correction is not authorized in this order: it must preserve the existing
meaning of `ROOT_NORMALIZATION_READY`, introduce an explicit lawful
disposition-closure P4 predicate/evidence path, and be qualified against a
disposable root before any real-root P4 retry.

## Known post-activation rehearsal issue

```text
KNOWN_POST_ACTIVATION_REHEARSAL_FAILURE = PRESENT
TEST = tests\test_b5_a5_offline_cutover_rehearsal.py::test_offline_cutover_full_rehearsal_abort_and_post_active_refusal
ASSERTION = _tree_digest(workspace_root) == legacy_before
PHASE = after P6 core activation and P7/P8 selector/native-public activation
REQUIRES_P6_ACTIVATION = YES
REQUIRES_P7_SELECTOR_ACTIVATION = YES
LEGACY_AND_PUBLIC_BEHAVIOR_BEFORE_ACTIVATION = CORRECT IN THE REHEARSAL
BLOCKS_P4 = NO
BLOCKS_P6_AUTHORIZATION_REVIEW = YES
POST_ACTIVATION_REHEARSAL_ISSUE_CLOSED = NO
```

This issue remains visible and unresolved.  It was neither patched nor
weakened during P4.

## Boundaries and validation

```text
P5_EXECUTED = NO
P6_EXECUTED = NO
P7_EXECUTED = NO
NATIVE_ACTIVATION = NO

FOCUSED_TESTS = not run after hard-stop diagnosis; no implementation changed
READ_ONLY_VALIDATION = P3 source epoch recheck PASS; durable core/negative proofs PASS; canonical P4 predicate REFUSED as expected
BROADER_TESTS = not run; the real-P4 verifier mismatch is a required stop boundary
GIT_DIFF_CHECK = PASS

TERMINAL_STATUS = REAL_P4 = STOPPED_FOR_VERIFIER_MISMATCH
NEXT_AUTHORIZATION_BOUNDARY = P4_VERIFIER_RECONCILIATION_REVIEW
```

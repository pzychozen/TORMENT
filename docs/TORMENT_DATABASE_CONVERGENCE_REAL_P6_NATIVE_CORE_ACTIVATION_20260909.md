# TORMENT Database Convergence — Real P6 Native Core Activation

Date: 2026-09-09
Scope: **REAL P6 only.** This record authorizes and records no P7 operation.

## Terminal result

`REAL_P6 = PASS`

The one canonical P6 call activated only corrected core
`f21c730f-5222-4aa8-9a5f-1c1188456df3`. The durable terminal proposition is:

```text
core role                    = ACTIVE_CORE
core deployment              = NATIVE_ACTIVE
ever_active                  = YES
P6 activation witness        = PRESENT
selector generation/state    = 7 / CUTOVER_PENDING
P7_EXECUTED                  = NO
SELECTOR_NATIVE_ACTIVE        = NO
```

No raw SQLite update, normalizer replay, disposition execution, selector
activation, abort, or rollback call was made by the real-P6 runner.

## Authoritative start

```text
STARTING_HEAD                = 749deffd953815aceba5dd153c14197f173eacaa
STARTING_ORIGIN_MAIN         = 749deffd953815aceba5dd153c14197f173eacaa
TRACKED_WORKTREE_BEFORE_P6   = CLEAN
```

The live SQLite data files are intentionally not tracked by Git. The
documentation commit containing this record is the repository-side durable
record; its post-push `HEAD == origin/main` verification is recorded at
handoff.

## Fresh P4/P5 precondition gate

The runner constructed the typed P3 proposition and called only the shared
read-only `OfflineCutoverController.verify_root_core_activation_precondition`.
It did not invoke the mutation-capable B3/B4 normalization service.

```text
P6_PRECONDITION_GATE         = PASS
ENVELOPE_D_DIGEST             = e4e510131cc341375485605bf1ead86aff684a1ca938e26fdbe221bbf0673ceb
P4_CLOSURE_DIGEST             = 5e415920dc34d0721a950c5e44fe4d31429b2f65afe1f33b7e08a6259075122d
P5_RECEIPT_ID                 = 25676a63-daa2-4a60-95ca-5889bdbfe733
P5_BINDING_VALID              = YES
SCOPE_TOPOLOGY                = 154 runtime scopes
MODEL_D                        = 76 private plans; every motif_domain_id = None
```

Frozen disposition facts remained exact:

```text
2076 memories = 2041 admitted + 35 certified refusals
450 motifs    = 183 B4A + 233 B4B + 11 B4P + 23 certified refusals
B2_UNACCOUNTED = 0
B4_UNACCOUNTED = 0
B4_OVERLAP     = 0
ROOT_NORMALIZATION_READY      = FALSE
ROOT_DISPOSITION_CLOSURE      = TRUE
ROOT_COMPLETION_VERIFIED      = TRUE
```

## Canonical P6 receipt and binding

The sole lifecycle mutation was
`OfflineCutoverController.activate_root_core(cutover, normalization)` after
the successful gate.

```text
REAL_P6_EXECUTED              = YES, exactly once
P6_RECEIPT_ID                 = f5efc57f-28a0-4ce2-bfc4-2787c15bafb1
P6_RECEIPT_DIGEST             = fb6fa8c746b590288e847ebbb10aef9f25930a34d55dbeb9ebb16b780be2a13d
P6_EVENT_KIND                 = ACTIVATE_CORE
CORE_ID                        = f21c730f-5222-4aa8-9a5f-1c1188456df3
```

The core now contains exactly the preceding `ENTER_CUTOVER_PENDING` event and
this `ACTIVATE_CORE` event. The latter persists a
`TORMENT_ROOT_ADMISSION_COMPLETION_WITNESS / v2` whose core ID, Envelope D,
and normalization closure digest are exactly the values above. Its root
membership-closure digest is
`f76c9d580db818da18b57efabee4afd09765a59f7e97d53849b9b5157d4ce67a`.

The corrected core database changed as expected. The historical core and
selector database hashes remained unchanged:

```text
historical core SHA-256       = 3e01e2a2e359f9e87e2a4b19b5a930763a28b75b7497cdc1574813e91a6d3ce4
selector SHA-256              = ca6dd6d4c3f26028be54df76d5bbe2fc6a0daac5a1265eb91986fc0f94417f9b
```

## P6-to-P7 intermediate authority

The selector remains generation 7 / `CUTOVER_PENDING`, with the same corrected
core and Envelope D. Both resolver and diagnostic observations are exact:

```text
deployment resolution         = MAINTENANCE_ONLY
resolution reason             = cutover-pending-is-never-public-routing
diagnostic reason             = core-active-external-pending
public backend                = REFUSED
DUAL_WRITE                    = NO
DUAL_READ_AUTHORITY           = NO
HIDDEN_LEGACY_FALLBACK        = NO
```

The root-v2 diagnostic currently reports `admission_identity_matches = false`
and `completion_witness_valid = false` before P7. This is not an identity
mismatch: direct P6 binding is true. The diagnostic's internal root-v2 helper
also tries to read the P7 selector activation intent; that reader correctly
refuses with `native activation intent requires NATIVE_ACTIVE selector state`
while the selector is pending, and the helper maps that P7-only absence to the
two false diagnostic fields. No P7 disposition receipt or activation intent
exists, as required at this boundary. No product-code change was made to alter
that P7-oriented diagnostic behavior during the P6 work order.

## Recovery and certified-refusal checks

The qualified read-only recovery path reconstructs the durable state as:

```text
POST_P6_RECOVERY_RECOGNITION  = CORE_ACTIVE_EXTERNAL_PENDING
AUTOMATIC_POST_NATIVE_ROLLBACK = NO
```

The immediate read-only negative-authority audit passed:

```text
CERTIFIED_REFUSAL_MEMORY_RUNTIME_LEAK = NO
  certified refusals                  = 35
  native ordinary successors           = 0
  other representations                = 0
  runtime compat embeddings            = 0
  ready/usable runtime representations = 0

CERTIFIED_REFUSAL_MOTIF_RUNTIME_LEAK  = NO
  certified refusals                  = 23
  target-alias absences                = 23
  runtime-reader absences              = 23
```

## Validation and handoff boundary

```text
FOCUSED_TESTS =
  pytest -q tests\test_post_i4_generalized_root_blocker5_binding.py
    -k "read_only_p6_precondition_reuses_the_reconciled_p4_contract
       or p4_completion_distinguishes_runtime_readiness_from_lawful_disposition_closure"
    tests\test_substrate_root_normalization.py
    --basetemp C:\TORMENT\TORMENT_administration\real-p6-native-core-activation-20260909\pytest
    -p no:cacheprovider
  Result: 14 passed, 43 deselected in 3.63s

GIT_DIFF_CHECK = PASS
TERMINAL_STATUS = REAL_P6_PASS_STOP_BEFORE_P7
NEXT_AUTHORIZATION_BOUNDARY = EXPLICIT_REAL_P7_SELECTOR_LAST_ACTIVATION
```

This is a hard stop. P7 remains a separate explicit authorization.

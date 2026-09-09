# TORMENT Database Convergence — Real Root Disposition Adapter Architecture Review

Date: 2026-09-09

## Result

```text
TERMINAL_STATUS = STOPPED_FOR_ARCHITECTURE_REVIEW
REAL_ROOT_MUTATION = NONE
REAL_ROOT_DISPOSITION_EXECUTED = NO
REAL_P7_EXECUTED = NO
```

The post-P6 / pre-P7 order authorized production implementation and disposable
qualification of a real root disposition adapter. Bounded archaeology showed
that the current architecture deliberately supports only synthetic disposition
receipts, not production owner operations. A real adapter cannot be added
lawfully without inventing external-owner semantics that are not present in the
frozen plan or existing implementation.

## Start and preserved real state

```text
STARTING_HEAD = dd8c09fc5dcd56c7e5b6811734cfa3162a8614f9
STARTING_ORIGIN_MAIN = dd8c09fc5dcd56c7e5b6811734cfa3162a8614f9
TRACKED_WORKTREE_BEFORE_REVIEW = CLEAN

real corrected core = f21c730f-5222-4aa8-9a5f-1c1188456df3
real core state = ACTIVE_CORE / NATIVE_ACTIVE
real selector = generation 7 / CUTOVER_PENDING
real P6 receipt = f5efc57f-28a0-4ce2-bfc4-2787c15bafb1
```

No real SQLite, selector, core, source artifact, external owner, or lifecycle
operation was called by this review.

## Exact current call chain

```text
typed P3 proposition
  -> RootGeometryDispositionPlan
  -> OfflineCutoverController.execute_root_disposition_plan(...)
  -> execute_synthetic_root_disposition_plan(...)
  -> SyntheticRootDispositionAdapter.execute(...)
  -> RootDispositionExecutionReceipt
  -> P7 receipt precondition
  -> activate_root_external_selector(...)
```

`activate_root_external_selector(...)` correctly refuses with
`ROOT_OFFLINE_CUTOVER_P7_RECEIPT_REQUIRED` until that receipt exists. The
receipt is therefore a real P7 prerequisite, but its current producer is
synthetic-only.

## Evidence for the stop

`root_blocker5_binding.py` declares the only adapter seam as
`SyntheticRootDispositionAdapter` and documents it as a “narrow synthetic
owner seam” for which “real external owners are intentionally absent.” The
receipt builder calls the adapter once per plan entry and accepts only a
non-empty outcome string. It does not contain an external resource locator,
owner API, mutation implementation, versioned external receipt, or recovery
mechanism.

The only concrete adapters found are test/copy implementations:

```text
tests/test_post_i4_generalized_root_blocker5_binding.py
  _SyntheticDispositionAdapter

tests/test_post_i4_full_root_disposable_rehearsal_r1.py
  _DisposableDispositionAdapter

C:\TORMENT\TORMENT_administration\p4-verifier-reconciliation-20260909
  _NoopDispositionAdapter (explicitly synthetic/copy-only)
```

The authoritative generalized-root qualification document likewise says that
only deterministic synthetic adapters are accepted by that phase and that no
real owner implementation was changed.

## Frozen plan: declared work versus missing production contract

The frozen table has eleven declared owner/disposition pairs:

| Owner identity | Declared disposition |
| --- | --- |
| `bridge_registry` | `RETAIN_DECISION_STATUS_CONFIDENCE_HISTORICAL` |
| `character_active_baseline` | `RECOMPUTE_TARGET_GEOMETRY_BASELINE` |
| `character_drift_history` | `RETAIN_AS_HISTORICAL_GEOMETRY_EPOCH_STATE` |
| `character_seed` | `RETAIN` |
| `checkpoint_kernel_calibration` | `REINITIALIZE_CALIBRATION_ONLY` |
| `conflict_role_affect_identity` | `NO_GEOMETRY_DISPOSITION_REQUIRED` |
| `deep_archive_vector_state` | `RETAIN_UNTOUCHED_DISABLED` |
| `hivemind_historical_geometry_scores` | `RETAIN_HISTORICALLY` |
| `proposal_registry` | `RETAIN_UNMODIFIED_WITH_FUTURE_CONSUMER_GUARD` |
| `srg_payload_markers` | `RETAIN_EXACTLY` |
| `world_trajectory` | `RETAIN` |

For every entry, the current DTO supplies only:

```text
owner_identity
disposition
source_observation_digest
```

It does **not** supply the concrete target path or service, authority owner,
predecessor state, successor state, legal mutation, operation identifier,
idempotence key, partial-failure rule, external receipt, or recovery rule.
The source-observation digest is derived from the aggregate owner observation
digest plus the owner name; it is not a locator or operation authority.

In particular, implementing `RECOMPUTE_TARGET_GEOMETRY_BASELINE`,
`REINITIALIZE_CALIBRATION_ONLY`, or the proposal consumer guard would require
inventing the target and mutation law. Treating retention entries as success
without a defined owner operation would be the prohibited fake-success/no-op
implementation.

## Classification

```text
MISSING_REAL_ADAPTER_CONFIRMED = YES
"REAL_EXTERNAL_OWNERS_INTENTIONALLY_ABSENT"_CLASSIFICATION =
  B — production disposition is intentionally unsupported by the current design
  (with D — synthetic qualification prevents production contact — as context)

REAL_ADAPTER_CLASS = NOT_IMPLEMENTED
REAL_ADAPTER_MODULE = NOT_APPLICABLE
REAL_ADAPTER_IS_PRODUCTION_OWNER = NO
REAL_ADAPTER_IS_NOOP_WRAPPER = NO
```

The decisive factor is not merely the missing class name. There is no evidenced
production contract for the actions an adapter would perform. Implementing one
from the frozen labels would violate the order's prohibition on inventing
semantic or external-owner authority.

## Receipt and safety assessment

```text
RECEIPT_BUILDER = execute_synthetic_root_disposition_plan(...)
MANUAL_RECEIPT_CONSTRUCTION = NO
IDEMPOTENT_EXACT_REPLAY = only synthetic receipt persistence is defined
PARTIAL_FAILURE_BEHAVIOR = only synthetic adapter interruption is qualified
CONFLICTING_DISPOSITION_BEHAVIOR = core receipt conflict refusal is defined

SELECTOR_MUTATION_CAPABILITY = NONE in the adapter seam
LEGACY_REACTIVATION_CAPABILITY = NONE in the adapter seam
AUTOMATIC_POST_NATIVE_ROLLBACK = NO
DISPOSITION_IMPLIES_P7 = NO
```

The existing core-side receipt persistence is safely idempotent/conflict-aware,
but it cannot make an undefined external owner operation real. Adding a real
adapter now would also leave partial-external-operation recovery unspecified.

## Required architecture decision before implementation

A later implementation order needs a ratified, versioned contract for each of
the eleven owner entries, including:

1. Canonical target and authoritative owner API or storage location.
2. Exact corrected-core, Envelope D, P6 receipt, and source binding.
3. Predecessor and successor state, permitted mutation, and external outcome
   payload.
4. Idempotence key, exact replay behavior, partial-failure observation, and
   conflict refusal.
5. An external operation receipt that the existing root receipt can bind,
   without replacing P3/P4/P5/P6 evidence or mutating the selector.

Only after that contract exists can a concrete production adapter be wired
through the existing controller and qualified on disposable roots.

## Review and validation

```text
FOCUSED_ARCHAEOLOGY = PASS
  - controller P6 -> disposition -> P7 chain inspected
  - frozen plan DTO and receipt validation inspected
  - repository and administration adapter implementations searched
  - synthetic/copy-only implementations identified

ADVERSARIAL_REVIEW = PASS (internal)
  - no declared target means no hidden real mutation can be proven
  - no adapter has selector authority
  - no adapter has legacy reactivation or rollback authority
  - a non-empty synthetic outcome could fabricate success, so it is excluded
  - partial external failure cannot be safely classified by current contract

CLAUDE_REVIEW = UNAVAILABLE
GIT_DIFF_CHECK = PASS
```

## Next boundary

```text
NEXT_AUTHORIZATION_BOUNDARY =
  REAL_ROOT_DISPOSITION_OWNER_ARCHITECTURE_AND_OPERATION_CONTRACT
```

This is a hard stop. The already-active real core and pending selector are
preserved unchanged.

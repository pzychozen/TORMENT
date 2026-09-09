# TORMENT Database Convergence: Pre-P6 / P4 Verification-Path Reconciliation v0.1

## Result

`PRE_P6_P4_VERIFICATION_PATH_RECONCILIATION = PASS`.

The blocked final P6 review did not find an incomplete P3/P4 disposition. It
used a different operation before P4: it re-ran the mutation-capable
`NativeRootWideNormalizationService` through immutable, query-only SQLite.
Successful real P4 instead constructed the checked, P3-derived
`RootNormalizationResult`, then applied the canonical P4 verifier.

The repair adds the non-mutating
`OfflineCutoverController.verify_root_core_activation_precondition()` boundary.
It consumes the same typed normalization proposition as P4, performs the
canonical P4 and P5-pending checks, and does not dispatch B3/B4 normalization.
`activate_root_core()` delegates to that shared gate before its otherwise
unchanged transition. No P6 method was called during this work.

## Literal path comparison

| Step | Path A — successful real P4 | Path B — blocked final P6 preflight |
| --- | --- | --- |
| P3 carrier | `real-root-p3-production-20260909/carrier/p3_source_admission_carrier.json`, SHA-256 `83056ce7…a8cd35` | Same carrier and hash |
| Request constructor | Rebuild request, validate Character continuation, call `_build_normalization_request()` | Same reconstruction sequence |
| Continuations | Character carrier: 37 validated witnesses; partial-motif SHA-256 `b21e1a7…dbfab` | Same paths, bindings, scope counts, and predecessor checks |
| Result constructor | P3-derived `RootNormalizationResult`: closed 35-B2 / 23-B4 certified-exception disposition | `NativeRootWideNormalizationService.normalize()` on `mode=ro&immutable=1; query_only=ON` |
| Completion entry | `OfflineCutoverController.verify_root_completion()` | direct `verify_root_completion()` after the noncanonical normalizer attempt |
| Closure predicate | `_require_normalization_complete()` | Same predicate |
| Evidence source | returned `RootAdmissionCompletionWitness` v2, recorded in the Git P4 result record | no P4-eligible result from the read-only replay |

```text
FIRST_PATH_DIVERGENCE = normalization result construction / SQLite execution mode
RECONSTRUCTION_DIVERGENCE = YES
VERIFIER_ENTRYPOINT_DIVERGENCE = NO
```

The carrier and continuations are not the divergence. The reconciled recheck
validated their current identities before it called P4.

## Read-only replay classification

`NativeRootWideNormalizationService` owns B3/B4 bootstrap and projection.
Those services recover idempotent work but still run the semantic operation
path, which calls `BEGIN IMMEDIATE`. A small disposable regression opens an
already-normalized core with the blocked review's SQLite settings and proves:

```text
sqlite3.OperationalError: attempt to write a readonly database
```

Some child services surface domain refusals as incomplete receipts; others
surface this SQLite error directly. Neither form is P4 reconstruction. They
are P3-owned dispatch attempted through an invalid read-only handle.

```text
READ_ONLY_RECONSTRUCTION_CONTRACT_DEFECT = YES (superseded external preflight route)
P4_REPLAY_AFTER_P5_CONTRACT_DEFECT = NO
```

P5 added exactly one `ENTER_CUTOVER_PENDING` event and changed the deployment
posture from `LEGACY_ACTIVE` to `CUTOVER_PENDING`. The P4 verifier permits that
stage; P5 does not alter the P3 carrier, Envelope D, source, or normalizer
inputs.

## P4 predicate and effective result

`ROOT_NORMALIZATION_CLOSURE_INCOMPLETE` occurs only in
`_require_normalization_complete()` in
`torment_service/substrate/root_blocker5_binding.py`. Its first branch requires:

```text
source_manifest_recheck_passed
root_normalization_complete
reason_codes == ()
expected_workspace_count == observed_workspace_closure
expected_materialized_scope_count == observed_materialized_scope_closure
root_memory_disposition_closed
root_motif_disposition_closed
```

When generalized readiness is false, the second branch additionally requires
`P3_DISPOSITION_CLOSED_WITH_CERTIFIED_EXCEPTIONS`, a nonzero B2/B4 refusal
count, and closed partial authority when applicable.

The reconciled real-root P4 proposition had:

```text
root_memory_disposition_closed = TRUE
root_motif_disposition_closed = TRUE
root_normalization_complete = TRUE
root_normalization_ready = FALSE
reason_codes = ()
p3_completion_class = P3_DISPOSITION_CLOSED_WITH_CERTIFIED_EXCEPTIONS
partial_activation = TRUE
partial_motif_authority_closure = TRUE
B2 certified refusals = 35
B3 completed memory dispositions = 2041
B4 certified refusals = 23
workspace closure = 4 / 4
materialized-scope closure = 154 / 154
normalization_closure_digest = 5e415920dc34d0721a950c5e44fe4d31429b2f65afe1f33b7e08a6259075122d
```

The historic blocked runner did not preserve a P4-eligible object. Its output
was noncanonical before verification because it came from mutation-capable
dispatch on an immutable connection; it is not evidence that these operands
were false.

## P4 receipt and P5 evidence

```text
P4_RECEIPT_ID = TORMENT_ROOT_ADMISSION_COMPLETION_WITNESS / v2
P4_RECEIPT_DIGEST = 5e415920dc34d0721a950c5e44fe4d31429b2f65afe1f33b7e08a6259075122d
P4_RECEIPT_BINDING_VALID = YES
  Envelope D = e4e510131cc341375485605bf1ead86aff684a1ca938e26fdbe221bbf0673ceb
  corrected core = f21c730f-5222-4aa8-9a5f-1c1188456df3
  source epoch/carrier and both continuations = current and exact
  selector generation = 7, state = CUTOVER_PENDING

P5_RECEIPT_BINDING_VALID = YES
P5_RECEIPT_ID = 25676a63-daa2-4a60-95ca-5889bdbfe733
P5_PENDING_WITNESS_DIGEST = 606626775ffc029f11fcbdfe9e9992e5cbd22267a4e8f50699ea738f8cdd71cd
P5_EVENT_CHAIN = ENTER_CUTOVER_PENDING only
```

The P4 witness is returned by P4 and recorded in the Git P4 record. It is not
written into a machine-readable core-maintenance event until P6 writes an
`ACTIVATE_CORE` event. P5 persists a pending deployment witness, not P4's
completion witness. Therefore:

```text
CAN_P6_PRECONDITION_LAWFULLY_CONSUME_DURABLE_P4_RECEIPT = NO
```

`WHAT_IS_P4_FOR?` P4 checks frozen source/manifest/census/membership facts and
a P3 disposition-closure proposition, then constructs the v2 witness required
by P5/P6. It is not a root-completion ledger write. P6 therefore requires a
caller-supplied typed P3 proposition and freshly verifies it immediately before
the transition; the reconciled preflight does that without inventing receipt
storage or weakening P4.

## Verification

The reconciled real-root preflight used an immutable, query-only connection for
the P4 predicate and P5 event read. It did not dispatch normalization or call
P6/P7. Corrected-core, historical-core, and selector SHA-256 values were
identical before and after.

```text
canonical P4/P5/P6-precondition = PASS
selected core = STAGING / CUTOVER_PENDING / ever_active=NO
activation completion witness = NONE
public posture = MAINTENANCE_ONLY
```

Focused disposable verification:

```text
pytest -q tests\test_substrate_root_normalization.py \
  tests\test_post_i4_generalized_root_blocker5_binding.py \
  tests\test_post_i4_root_v2_production_recovery.py \
  --basetemp C:\TORMENT\TORMENT_administration\pre-p6-p4-reconciliation-20260909\pytest-regression-r2 \
  -p no:cacheprovider

62 passed in 34.96s
```

The new matrix proves valid P4+P5 and lawful `READY=FALSE` certified-exception
closure pass; corrupted P4, wrong core, altered Envelope D, incomplete closure,
and absent P5 each refuse.

## Required result record

```text
STARTING_HEAD = 296bdd0dd34720b0e5be008adee502858a38c15d
FINAL_HEAD = terminal Git receipt after this record is committed
ORIGIN_MAIN = 296bdd0dd34720b0e5be008adee502858a38c15d at start
TRACKED_WORKTREE = clean at start; terminal state recorded after commit

REAL_ROOT_WRITE = NONE
SUCCESSFUL_REAL_P4_PATH = P3-derived typed result -> canonical P4 verifier
BLOCKED_P6_PREFLIGHT_PATH = immutable read-only B3/B4 normalizer replay -> noncanonical result/refusal
FIRST_PATH_DIVERGENCE = normalization result construction / SQLite execution mode

P4_NORMALIZATION_OBJECT = completed lawful certified-exception closure
P6_PREFLIGHT_NORMALIZATION_OBJECT = noncanonical mutation-capable replay on immutable SQLite
RECONSTRUCTION_DIVERGENCE = YES
VERIFIER_ENTRYPOINT_DIVERGENCE = NO
READ_ONLY_RECONSTRUCTION_CONTRACT_DEFECT = YES (external preflight only)
P4_REPLAY_AFTER_P5_CONTRACT_DEFECT = NO

FAILED_PREDICATE = ROOT_NORMALIZATION_CLOSURE_INCOMPLETE first/second P4 closure branch
OBSERVED_OPERANDS = historic object noncanonical; reconciled P4 operands all pass
EXPECTED_OPERANDS = exact P4 closure expression above

P4_RECEIPT_ID = TORMENT_ROOT_ADMISSION_COMPLETION_WITNESS / v2
P4_RECEIPT_DIGEST = 5e415920dc34d0721a950c5e44fe4d31429b2f65afe1f33b7e08a6259075122d
P4_RECEIPT_BINDING_VALID = YES
P5_RECEIPT_BINDING_VALID = YES
CAN_P6_PRECONDITION_LAWFULLY_CONSUME_DURABLE_P4_RECEIPT = NO

ROOT_NORMALIZATION_READY = FALSE
ROOT_DISPOSITION_CLOSURE = TRUE
ROOT_COMPLETION_VERIFIED = TRUE
P3_SEMANTICS_CHANGED = NO
P4_SEMANTICS_CHANGED = NO
MODEL_D_CHANGED = NO

FOCUSED_TESTS = 62 passed
NEGATIVE_TESTS = corrupted P4/wrong core/altered Envelope D/incomplete closure/absent P5 refused
DISPOSABLE_P4_P5_P6_PREFLIGHT = PASS

FULL_REAL_ROOT_REPLAY_EXECUTED = NO
FULL_REAL_ROOT_REPLAY_REQUIRED = NO for the reconciled precondition
REAL_P6_EXECUTED = NO
REAL_P7_EXECUTED = NO
NATIVE_ACTIVATION = NO

TERMINAL_STATUS = PASS
NEXT_AUTHORIZATION_BOUNDARY = EXPLICIT_REAL_P6_EXECUTION_REVIEW
```

That next boundary is an authorization review only. This reconciliation grants
no authority to call real P6.

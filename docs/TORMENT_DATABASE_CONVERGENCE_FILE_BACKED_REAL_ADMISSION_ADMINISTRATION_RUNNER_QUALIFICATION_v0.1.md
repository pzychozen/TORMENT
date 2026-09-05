# TORMENT Database Convergence — File-Backed Real-Admission Administration Runner Qualification

**Date:** 2026-09-05
**Authorization:** `FILE_BACKED_REAL_ADMISSION_ADMINISTRATION_RUNNER_QUALIFICATION = YES`
**Completion starting revision:** `1b0d149243afdff951a702cdce17db57f7acba7a` (`HEAD == origin/main`)

## Result

`FILE_BACKED_REAL_ADMISSION_ADMINISTRATION_RUNNER_QUALIFICATION = QUALIFIED`

`FileBackedRealAdmissionAdministrationRunner` is a narrow administration
checkpoint recorder. It does not invoke direct-source grammar, migration,
writer-freeze capture, SQLite, P1 implementation, normalization, services, or
runtime authority. A future separately authorized caller supplies all such
work; this runner only retains caller-supplied administrative facts outside the
caller-supplied data root.

## Durable identity and checkpoint contract

The caller must provide an explicit result directory outside `data_root`, an
operation ID, expected repository head, data-root identity, and immutable P1
authorization. The canonical `administration_state.json` has the typed
`run_context` section with all of:

- `operation_id`
- `expected_repository_head`
- `data_root_identity`
- `P1_authorized`
- `P1_started`
- `durable_native_state_created`

alongside typed `state`, monotonic `sequence`, `recorded_at_ns`, and JSON
`detail`. Reopening a directory refuses if its operation ID, expected head,
data-root identity, or P1 authorization differs. `P1_authorized` cannot be
changed by a transition.

Each current-state update writes canonical JSON to a unique sibling temporary
file, flushes and file-syncs it, closes it, then uses `os.replace(...)`. The
temporary file is never authoritative; a failed replacement retains the prior
canonical state. The optional `administration_events.jsonl` is append-only,
written only after the current state commits, and holds the same context and
detail payload. It is simple administrative evidence, not a database,
provenance framework, or authority source.

The event detail contract retains capture facts—writer-freeze operation ID,
payload digest, writer-evidence/witness relationship, stability delta, file
count, tree digest, jobs, listener, and covered writer—and direct-preparation
facts—description identity/digest, counts, posture/dispositions, unknown-scope
keys, empty-private count, and geometry summary. Synthetic tests recover those
values from state/event files alone after the caller has completed.

## P1 boundary retention only

The runner has a synthetic callback seam for qualification of administrative
ordering only. It atomically records `P1_STARTED` before calling a supplied
callback. A callback that creates a caller-owned durable artifact must explicitly
record that fact while still in `P1_STARTED`. If that callback then raises, the
runner records `P1_FAILED_AFTER_DURABLE_STATE`, retains the artifact, and offers
no retry or cleanup path. This is not P1 implementation and does not grant P1
authority.

## Synthetic-only verification

All tests used disposable synthetic roots and synthetic child Python processes.
The detached-output test redirected child stdout/stderr to null, did not obtain
the result from terminal output, later reopened the result directory, and
recovered `FINAL_STOP`. The interruption test first observed a valid durable
`CAPTURE_STARTED`, terminated the child, then reopened the valid canonical
state with no later event. The callback tests used only fake artifacts outside
their synthetic data roots.

```text
python -m py_compile torment_service\substrate\file_backed_real_admission_administration_runner.py tests\test_file_backed_real_admission_administration_runner.py
pytest -q -p no:cacheprovider --basetemp C:\TORMENT\pdm11 tests\test_file_backed_real_admission_administration_runner.py
19 passed in 2.48s

pytest -q -p no:cacheprovider --basetemp C:\TORMENT\pdm12 \
  tests\test_file_backed_real_admission_administration_runner.py \
  tests\test_root_writer_freeze_evidence.py \
  tests\test_substrate_root_admission_description.py
46 passed, 1 skipped in 5.04s
```

The focused command emitted the host environment's intermittent Windows
subprocess access-violation traceback while waiting for the synthetic detached
child, but exited successfully with the complete passing summary above. That
host noise is not claimed as a runner property.

## Exact verdict ledger

```text
FILE_BACKED_REAL_ADMISSION_ADMINISTRATION_RUNNER = QUALIFIED
ATOMIC_CHECKPOINT_WRITE = PASS
RESULT_PATH_OUTSIDE_DATA_ENFORCED = PASS
DETACHED_OUTPUT_RESULT_RECOVERY = PASS
INTERRUPTED_RUN_LAST_CHECKPOINT_RECOVERABLE = PASS
CAPTURE_RESULT_RETENTION = PASS
DIRECT_PREPARATION_RESULT_RETENTION = PASS
SOURCE_REFUSAL_RETENTION = PASS
UNEXPECTED_EXCEPTION_RETENTION = PASS
P1_BOUNDARY_CHECKPOINT_ORDERING = PASS
P1_DURABLE_FAILURE_RETENTION = PASS
RUN_CONTEXT_HEAD_BOUND = PASS
RUN_CONTEXT_DATA_ROOT_IDENTITY_BOUND = PASS
P1_AUTHORIZATION_STATE_BOUND = PASS
STDOUT_DEPENDENCY = NONE
ATTACHED_HOST_DEPENDENCY = NONE
WRITER_FREEZE_SEMANTICS_CHANGED = NO
DIRECT_SOURCE_SEMANTICS_CHANGED = NO
DATABASE_SEMANTICS_CHANGED = NO
AUTHORITY_MODEL_CHANGED = NO
REAL_ROOT_CONTACT = NONE
SQLITE_PRODUCTION_WRITE = NONE
P1 = NOT_EXECUTED
P2 = NOT_EXECUTED
READY_FOR_DIRECT_REAL_PREPARATION_ATTEMPT_6 = YES
```

No production writer census, listener contact, SQLite, source mutation,
normalization, service operation, Brainvision, or cognitive-function work was
performed. Attempt 6 was not started.

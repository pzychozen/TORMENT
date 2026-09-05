# TORMENT Database Convergence — File-Backed Real-Admission Administration Runner Qualification

**Date:** 2026-09-05
**Authorization:** `FILE_BACKED_REAL_ADMISSION_ADMINISTRATION_RUNNER_QUALIFICATION = YES`
**Starting revision:** `1b3961a5af13fe9be07f3b74e05b68c563fc9c7e` (`HEAD == origin/main`)

## Result

`FILE_BACKED_REAL_ADMISSION_ADMINISTRATION_RUNNER_QUALIFICATION = PASS`

The new `FileBackedRealAdmissionAdministrationRunner` is an administrative
checkpoint recorder only. It contains no direct source adapter invocation,
writer/listener census, writer-freeze capture, SQLite connection, P1 bootstrap,
admission envelope, normalization, selector, service, or runtime authority.
The caller remains responsible for every future authorized operation and records
the resulting state explicitly.

## Result boundary and durability

The runner requires all of:

- an explicit `data_root` solely for destination containment checks;
- an explicit caller-owned `result_directory`; and
- a bounded `operation_id`.

It rejects a result directory that resolves inside the supplied data root, so it
cannot write to legacy source or `data/substrate`. It does not hard-code a
production path. The result directory is suitable for a caller-supplied layout
such as `administration_results/<operation-id>/` outside the data root.

`administration_state.json` is the one canonical current state. Each checkpoint
writes canonical JSON to a unique temporary sibling, flushes and file-syncs it,
closes it, then calls `os.replace(...)`. A failed replacement leaves the prior
canonical file current; temporary files are not authoritative.

The optional `administration_events.jsonl` is a small append-only audit aid. It
is written only after the canonical checkpoint commits, carries no hash chain,
and is never an authority source.

## State model

The typed state machine supports every required outcome:

```text
RUNNER_STARTED
PRECHECK_STARTED / PRECHECK_PASS / PRECHECK_REFUSED
CAPTURE_STARTED / CAPTURE_RETURNED / CAPTURE_REFUSED / CAPTURE_EXCEPTION
DIRECT_PREPARATION_PASS / DIRECT_PREPARATION_REFUSED
P1_NOT_AUTHORIZED / P1_READY / P1_STARTED / P1_PASS / P1_FAILED_AFTER_DURABLE_STATE
FINAL_VERIFICATION_PASS / FINAL_STOP
ADMINISTRATION_EXCEPTION
```

Legal transitions are intentionally bounded. A reopened runner requires the
same operation identity and continues the durable sequence; it cannot silently
reuse a result directory for another operation.

## Synthetic-only verification

The qualification used only pytest disposable roots. It covered result-directory
containment refusal, external-only state/event writes, every required normal and
P1-failure state path, exception retention without an event log, restart
sequence continuity, and failed atomic replacement preserving the prior state.

```text
python -m py_compile torment_service\substrate\file_backed_real_admission_administration_runner.py tests\test_file_backed_real_admission_administration_runner.py
pytest -q -p no:cacheprovider --basetemp C:\TORMENT\pdm9 tests\test_file_backed_real_admission_administration_runner.py
12 passed in 0.62s

pytest -q -p no:cacheprovider --basetemp C:\TORMENT\pdm10 \
  tests\test_file_backed_real_admission_administration_runner.py \
  tests\test_root_writer_freeze_evidence.py \
  tests\test_substrate_root_admission_description.py
39 passed, 1 skipped in 3.29s
```

The second command emitted the environment's intermittent Windows/Numpy access
violation traceback during import, but returned success and the test summary
above. This is recorded as host-environment noise, not a claimed runner
property. No real root, production process/listener, source model, production
SQLite database, P1/P2, normalization, service, Brainvision, or cognitive
function was contacted or changed.

## Authority boundary

This qualification changes only administrative result retention. It grants no
authority to repeat Attempt 5, prepare a real source, create a native core, or
advance P2 through P7. A future separately authorized administration must name
its result directory and operation ID before recording any real-run state.

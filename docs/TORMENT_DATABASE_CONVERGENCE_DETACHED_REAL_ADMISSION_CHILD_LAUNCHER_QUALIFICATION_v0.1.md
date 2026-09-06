# TORMENT Database Convergence — Detached Real-Admission Child Launcher Qualification

**Date:** 2026-09-06
**Starting revision:** `5bf64589c2131762b3b6522b24100f0e3c3c6263` (`HEAD == origin/main`)

## Result

`DETACHED_REAL_ADMISSION_CHILD_LAUNCHER = QUALIFIED`

The reusable `detached_real_admission_child_launcher` is launch plumbing only.
It validates an explicit repository root containing the importable
`torment_service` package, accepts only an explicit interpreter path, starts
the child with that repository as its exact CWD, and redirects stdin/stdout/
stderr to caller-supplied file paths. It neither searches `PATH` for Python
nor modifies `PYTHONPATH` or any user/system environment variable.

The child launch uses the platform detached-process flags plus `stdin=DEVNULL`.
The import-only probe uses that same launcher, interpreter, CWD, flags, and
stdio redirection as a future admission child. Its child writes an atomic,
file-backed result containing its actual CWD, `sys.executable`, and either
success or its exact exception. Parent terminal output is not a result source.

## Synthetic verification

All verification used repository code and disposable pytest result directories.
It did not instantiate an adapter or access a data root, process census,
listener, or SQLite database.

```text
python -m py_compile torment_service\substrate\detached_real_admission_child_launcher.py tests\test_detached_real_admission_child_launcher.py
pytest -q -p no:cacheprovider --basetemp C:\TORMENT\pdm16 \
  tests\test_detached_real_admission_child_launcher.py \
  tests\test_file_backed_real_admission_administration_runner.py
26 passed in 9.31s
```

The suite proves:

- a parent at the repository root starts an importable detached child;
- a parent changed to an unrelated disposable CWD still starts the child at the
  explicit repository root;
- an invalid repository root refuses before creating a probe artifact or child;
- a nonexistent or existing-but-wrong explicit executable fails closed with
  its exact requested executable, CWD, exception type, and message;
- stdout/stderr are detached files while the import result is recovered from a
  separate file-backed result; and
- the child records exactly the requested resolved interpreter and repository
  CWD.

The host emitted its known intermittent Windows subprocess access-violation
traceback while waiting for the synthetic detached children, but the command
returned success with the complete passing summary above. This host behaviour
is recorded as noise, not as a launcher property.

## Attempt 6 regression closure

The regression test deliberately places the parent in an unrelated disposable
directory and does not reproduce an uncontrolled import failure. Instead, it
proves the qualified helper supplies the deterministic repository CWD and
explicit `sys.executable` context required for `torment_service` imports. This
closes the `ModuleNotFoundError: torment_service` class observed in Attempt 6
without advancing or altering that attempt's `CAPTURE_STARTED` ledger.

## Verdict ledger

```text
DETACHED_REAL_ADMISSION_CHILD_LAUNCHER = QUALIFIED
REPOSITORY_ROOT_EXPLICIT = YES
PYTHON_EXECUTABLE_EXPLICIT = YES
CHILD_CWD_BOUND_TO_REPOSITORY_ROOT = YES

IMPORT_PROBE = PASS
PARENT_CWD_INDEPENDENCE = PASS
DETACHED_OUTPUT_IMPORT_RESULT_RECOVERY = PASS

ATTEMPT_6_IMPORT_FAILURE_CLASS = CLOSED

WRITER_FREEZE_SEMANTICS_CHANGED = NO
DIRECT_SOURCE_SEMANTICS_CHANGED = NO
DATABASE_SEMANTICS_CHANGED = NO
AUTHORITY_MODEL_CHANGED = NO

REAL_ROOT_CONTACT = NONE
SQLITE_PRODUCTION_WRITE = NONE
P1 = NOT_EXECUTED

READY_FOR_DIRECT_REAL_PREPARATION_ATTEMPT_7 = YES
```

Attempt 7 was not performed. Its future authorization must use a fresh
operation/result directory and run the qualified import-only probe before any
real-root contact.

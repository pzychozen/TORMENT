# TORMENT Database Convergence — Detached Real-Admission Exact Child Invocation Qualification

**Date:** 2026-09-06
**Scope:** administration plumbing only; synthetic qualification only

## Verdict

```text
DETACHED_REAL_ADMISSION_EXACT_CHILD_INVOCATION = QUALIFIED
ATTEMPT_7_MODULE_IMPORT_FAILURE_CLASS = CLOSED
REAL_CHILD_INVOCATION_MODE = PYTHON_MODULE
PROBE_REAL_CHILD_INVOCATION_PARITY = PASS
PARENT_CWD_INDEPENDENCE = PASS
EXTERNAL_ADMIN_SCRIPT_IMPORT_CONTEXT = PASS

REPOSITORY_ROOT_EXPLICIT = YES
PYTHON_EXECUTABLE_EXPLICIT = YES
PYTHONPATH_GLOBAL_MUTATION = NO

WRITER_FREEZE_SEMANTICS_CHANGED = NO
DIRECT_SOURCE_SEMANTICS_CHANGED = NO
DATABASE_SEMANTICS_CHANGED = NO
AUTHORITY_MODEL_CHANGED = NO

REAL_ROOT_CONTACT = NONE
SQLITE_PRODUCTION_WRITE = NONE
P1 = NOT_EXECUTED
READY_FOR_DIRECT_REAL_PREPARATION_ATTEMPT_8 = YES
```

This qualification does not authorize or perform Attempt 8.

## Attempt 7 exact failed invocation

Attempt 7's successful import-only probe and its failed capture child had
different Python invocation modes.

```text
explicit executable = C:\Users\Notandi\miniconda3\envs\torment\python.exe
repository cwd = C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric

passing probe argv =
  python.exe -c <repository-import probe program>

failed capture child argv =
  python.exe C:\TORMENT\TORMENT_administration\direct-real-admission-p1-attempt-7-20260906\attempt7_capture_and_preparation.py

external script location =
  C:\TORMENT\TORMENT_administration\direct-real-admission-p1-attempt-7-20260906\attempt7_capture_and_preparation.py
```

The capture child therefore used an external `.py` script path, not `-c`.
Python placed that script's external directory ahead of the repository import
context, and its first `torment_service` import failed with
`ModuleNotFoundError`. The failure happened before its `main()` function,
before any source API, writer/freezer API, or P1 callback.

## Qualified exact mode

`torment_service.substrate.detached_real_admission_child_entrypoint` is the
single repository-owned entrypoint. The qualified launcher builds only this
prefix, with the caller-supplied interpreter, repository root, detached flags,
and redirected external stdout/stderr:

```text
python.exe -m torment_service.substrate.detached_real_admission_child_entrypoint <operational arguments>
```

The exact-mode probe uses:

```text
-m torment_service.substrate.detached_real_admission_child_entrypoint
--import-probe-only --result-path <external result path>
```

It atomically records `sys.executable`, `cwd`, `sys.path[0]`,
`entry_invocation_mode = PYTHON_MODULE`, the entrypoint module identity, and
the imported repository package identity. It imports only the bounded
administrative dependencies required for future admission plumbing:

- `torment_service`
- `torment_service.substrate.real_root_typed_evidence`
- `torment_service.substrate.writer_freeze_evidence`
- `torment_service.substrate.file_backed_real_admission_administration_runner`

An external administration body, when needed, is invoked only through the
same module entrypoint:

```text
-m torment_service.substrate.detached_real_admission_child_entrypoint
--execute-external-script <explicit external .py path> [script arguments]
```

The entrypoint verifies the repository imports before executing that explicit
path. It does not set `PYTHONPATH`, alter the parent environment, search for
an interpreter, or grant any authority. A missing script, an invalid root, an
invalid entrypoint module, or a wrong/missing executable fails closed with the
bounded exact diagnostic; no alternate path is guessed.

## Synthetic proof

The regression creates an external `.py` administration body outside the
repository while the parent CWD is unrelated. It launches that body only via
the qualified external-script helper. The child durably records:

```text
sys.executable = explicitly requested interpreter
cwd = explicit repository root
sys.path[0] = explicit repository root
repository package importable = YES
repository module identity = torment_service/__init__.py under that root
entry invocation mode = PYTHON_MODULE
```

The test asserts that the real child argument vector begins with `-m` plus the
same repository entrypoint module as the probe. The executable, CWD, detached
flags, and entrypoint are identical; only the operation arguments differ. It
also asserts the raw `python <external-script.py>` shape and `-c` are absent
from the qualified real-child invocation.

Focused tests passed using disposable workspace-local test bases:

```text
tests/test_detached_real_admission_child_launcher.py = 10 passed
tests/test_file_backed_real_admission_administration_runner.py = 19 passed
```

Pytest could not update its shared `.pytest_cache` because of an existing
Windows access-denied condition; the test executions themselves passed.

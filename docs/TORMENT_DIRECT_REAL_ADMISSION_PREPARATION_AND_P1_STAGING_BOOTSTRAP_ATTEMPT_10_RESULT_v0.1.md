# TORMENT — Direct Real Admission Preparation and P1 Staging Bootstrap Attempt 10 Result

**Date:** 2026-09-06
**Authorization:** `DIRECT_REAL_ADMISSION_PREPARATION_AND_P1_STAGING_BOOTSTRAP_ATTEMPT_10 = YES`
**Required start revision:** `519945d8deb1010bb791c205d05192f7bf697205` (`HEAD == origin/main`)

## Authoritative result

```text
DIRECT_REAL_ADMISSION_PREPARATION_ATTEMPT_10 = PRECHECK_REFUSED
ADMINISTRATION_OPERATION_ID = direct-real-admission-p1-attempt-10-20260906
ADMINISTRATION_FINAL_STATE = FINAL_STOP
```

The first Python process used the required repository-owned module bridge:

```text
C:\Users\Notandi\miniconda3\envs\torment\python.exe
  -m torment_service.substrate.detached_real_admission_child_entrypoint
  --execute-external-script <Attempt-10 driver>
```

Inside that driver, the qualified detached import probe passed with the
explicit interpreter, repository CWD, `sys.path[0]`, entrypoint module, and
detached creation flags (`520`). The canonical probe result records
`REPOSITORY_PACKAGE_IMPORTABLE = YES`.

After `RUNNER_STARTED` and `PRECHECK_STARTED`, the fresh writer/listener
census refused. Its broad direct-writer pattern matched two ancestor command
shell processes (`pwsh.exe` PID `39636`; `cmd.exe` PID `54600`) because their
command lines contained this administration’s `bootstrap`/`admission` terms.
No REST, MCP, Fabric host, clone/repair job, or `127.0.0.1:8787` listener was
reported by that census.

The authorization requires a terminal stop on precheck failure. No recensus,
filter adjustment, retry, process control, real capture child, or source
contact was performed.

## Durable ledger

The external canonical administration ledger was reopened after stop. Its
ordered states are:

```text
1  RUNNER_STARTED
2  PRECHECK_STARTED
3  PRECHECK_REFUSED
4  FINAL_STOP
```

## Authority and mutation ledger

```text
IMPORT_PROBE = PASS
ENTRY_INVOCATION_MODE = PYTHON_MODULE
REPOSITORY_PACKAGE_IMPORTABLE = YES
PROBE_REAL_CHILD_INVOCATION_PARITY = PASS
OUTER_BOOTSTRAP_MODE = REPOSITORY_PYTHON_MODULE

WRITER_CENSUS = REFUSED
CAPTURE = NOT_EXECUTED
DIRECT_SOURCE_PREPARATION = NOT_EXECUTED
P1_READY = NOT_RECORDED
P1_STARTED = NO

REAL_SOURCE_CONTACT = NONE
SQLITE_CREATE_API_INVOKED = NO
REAL_NATIVE_STAGING_CORE_CREATED = NO
ROOT_ADMISSION_ENVELOPE_PERSISTED = NO
CUTOVER_PENDING = NO
NORMALIZATION_EXECUTED = NO
P2_EXECUTED = NO
P5_EXECUTED = NO
P6_EXECUTED = NO
P7_EXECUTED = NO
LEGACY_SOURCE_MUTATION = NONE
SERVICE_RESTART = NONE
```

## Stop boundary

Attempt 10 is closed at durable `FINAL_STOP` before capture and P1. The
external administration files are not repository artifacts. Any subsequent
attempt requires new explicit authorization, a fresh operation identity and
result directory; this result authorizes no retry or source repair.

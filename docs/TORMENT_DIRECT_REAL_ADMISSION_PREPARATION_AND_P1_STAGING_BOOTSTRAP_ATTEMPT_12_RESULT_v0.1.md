# TORMENT — Direct Real Admission Preparation and P1 Staging Bootstrap Attempt 12 Result

**Date:** 2026-09-06
**Authorization:** `DIRECT_REAL_ADMISSION_PREPARATION_AND_P1_STAGING_BOOTSTRAP_ATTEMPT_12 = YES`
**Required start revision:** `4c5541ce07c236c87c832beed25fd911f3d7e100` (`HEAD == origin/main`)

## Authoritative result

```text
DIRECT_REAL_ADMISSION_PREPARATION_ATTEMPT_12 = PRECHECK_REFUSED
ADMINISTRATION_OPERATION_ID = direct-real-admission-p1-attempt-12-20260906
ADMINISTRATION_FINAL_STATE = FINAL_STOP
```

The authorized first Python process used the required repository-owned module
bridge from the explicit repository working directory:

```text
C:\Users\Notandi\miniconda3\envs\torment\python.exe
  -m torment_service.substrate.detached_real_admission_child_entrypoint
  --execute-external-script <Attempt-12 driver>
```

The exact module-mode import probe passed. It recorded the explicit
interpreter, repository CWD, repository `sys.path[0]`, repository entrypoint
module, module identity, and detached flags (`520`).

After `RUNNER_STARTED` and `PRECHECK_STARTED`, the CMD-only administration
attempted the one authorized complete positive-PID process-table observation
using `wmic.exe`. The executable is unavailable on this host, producing the
exact precheck exception:

```text
FileNotFoundError: [WinError 2] The system cannot find the file specified
```

No complete process table was obtained. Attempt 12 forbids launching
`powershell.exe` or `pwsh.exe` as an alternative collector, so no substitute
process or listener observation was attempted. The positive-PID census rule
was therefore not invoked against a live table.

The authorization requires a terminal stop when the required live census
cannot be performed within the CMD-only boundary. No PowerShell launch,
recensus, collector substitution, code change, retry, capture-child launch,
source contact, or P1 action followed this refusal.

## Durable ledger

The external canonical administration ledger was reopened through CMD after
stop. Its ordered states are:

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

WINDOWS_CMD_ONLY_BOUNDARY = PRESERVED
WINDOWS_PROCESS_TABLE = NOT_OBTAINED
PROCESS_TABLE_FAILURE = WMIC_EXECUTABLE_UNAVAILABLE
WRITER_CENSUS = NOT_EXECUTED
LISTENER_OBSERVATION = NOT_EXECUTED
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

Attempt 12 is closed at durable `FINAL_STOP` before census classification,
capture, and P1. The external administration ledger, probe files, and
drivers are not repository artifacts. This result authorizes neither a
collector substitution nor another attempt; either requires separate explicit
authorization and a fresh operation identity.

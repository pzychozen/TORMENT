# TORMENT — Direct Real Admission Preparation and P1 Staging Bootstrap Attempt 11 Result

**Date:** 2026-09-06
**Authorization:** `DIRECT_REAL_ADMISSION_PREPARATION_AND_P1_STAGING_BOOTSTRAP_ATTEMPT_11 = YES`
**Required start revision:** `087a2070bf8772c116690dcee931de741bb66d59` (`HEAD == origin/main`)

## Authoritative result

```text
DIRECT_REAL_ADMISSION_PREPARATION_ATTEMPT_11 = PRECHECK_REFUSED
ADMINISTRATION_OPERATION_ID = direct-real-admission-p1-attempt-11-20260906
ADMINISTRATION_FINAL_STATE = FINAL_STOP
```

The authorized first Python process used the required repository-owned module
bridge from the explicit repository working directory:

```text
C:\Users\Notandi\miniconda3\envs\torment\python.exe
  -m torment_service.substrate.detached_real_admission_child_entrypoint
  --execute-external-script <Attempt-11 driver>
```

The exact module-mode import probe passed. It recorded the explicit
interpreter, repository CWD, repository `sys.path[0]`, repository entrypoint
module, module identity, and detached flags (`520`).

After `RUNNER_STARTED` and `PRECHECK_STARTED`, the one authorized live CIM
process-table observation was passed, without manual process removal, to the
qualified ancestry-aware direct-writer helper with the driver's exact
`os.getpid()` value. The helper returned the existing typed
`WriterProcessObservation` for `DIRECT_TORMENT_TOOL_OR_SCRIPT` with result
`UNRESOLVED` and exact refusal reason `INVALID_PROCESS_PID`.

The complete injected table therefore failed closed before writer classification
could be resolved. REST, MCP, Fabric-host, and nonterminal-job observations
were all `ABSENT`; the `127.0.0.1:8787` listener-table observation was also
`ABSENT`. No process command lines were retained in this repository result.

Attempt 11 requires an immediate terminal stop for either `RUNNING` or
`UNRESOLVED` direct-writer observations. No recensus, helper change, PID
exception, filter adjustment, retry, capture-child launch, source read, or P1
action followed this refusal.

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

WRITER_CENSUS = UNRESOLVED
DIRECT_WRITER_OBSERVATION = UNRESOLVED
DIRECT_WRITER_REFUSAL_REASON = INVALID_PROCESS_PID
ADMINISTRATION_ANCESTRY_DISAMBIGUATION = NOT_REACHED
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

Attempt 11 is closed at durable `FINAL_STOP` before capture and P1. The
external administration ledger, probe files, and drivers are not repository
artifacts. This result authorizes neither a revised census nor another attempt;
either requires separate explicit authorization and a fresh operation identity.

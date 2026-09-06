# TORMENT — Direct Real Admission Preparation and P1 Staging Bootstrap Attempt 8 Result

**Date:** 2026-09-06
**Authorization:** `DIRECT_REAL_ADMISSION_PREPARATION_AND_P1_STAGING_BOOTSTRAP_ATTEMPT_8 = YES`
**Required start revision:** `7b4352f4ab723cd481d7d8f51178d3de3b1001f3` (`HEAD == origin/main`)

## Authoritative result

```text
DIRECT_REAL_ADMISSION_PREPARATION_ATTEMPT_8 = SOURCE_REFUSED_BEFORE_P1
ADMINISTRATION_OPERATION_ID = direct-real-admission-p1-attempt-8-20260906
ADMINISTRATION_RESULT_DIRECTORY = C:\TORMENT\TORMENT_administration\direct-real-admission-p1-attempt-8-20260906
ADMINISTRATION_STATE_PATH = C:\TORMENT\TORMENT_administration\direct-real-admission-p1-attempt-8-20260906\administration_state.json
ADMINISTRATION_FINAL_STATE = FINAL_STOP
ADMINISTRATION_ATTACHED_HOST_DEPENDENCY = NONE
```

The external canonical `administration_state.json`, reopened through the
file-backed runner after the terminal checkpoint, is authoritative. Its
durable sequence is:

```text
1  RUNNER_STARTED
2  PRECHECK_STARTED
3  PRECHECK_PASS
4  CAPTURE_STARTED
5  CAPTURE_REFUSED
6  FINAL_STOP
```

The reread immutable context retains the authorized operation ID, required
head, canonical real-root identity
`TORMENT_REAL_ROOT_DIRECT_ADMISSION_P1_20260905`, `P1_authorized = YES`,
`P1_started = NO`, and `durable_native_state_created = NO`.

## Exact-mode probe and precheck

The required detached module-mode import probe passed before the ledger was
constructed or the data root was used:

```text
ENTRY_INVOCATION_MODE = PYTHON_MODULE
ENTRYPOINT = torment_service.substrate.detached_real_admission_child_entrypoint
CHILD_EXECUTABLE = C:\Users\Notandi\miniconda3\envs\torment\python.exe
CHILD_CWD = C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric
SYS_PATH_0 = C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric
REPOSITORY_PACKAGE_IMPORTABLE = YES
DETACHED_FLAGS = 520
```

The real capture body was launched once through
`launch_detached_real_admission_external_script_child(...)`. Its effective
argument shape was the qualified repository module bridge, not `python -c`
and not a raw external-script launch:

```text
python.exe -m torment_service.substrate.detached_real_admission_child_entrypoint
  --execute-external-script
  C:\TORMENT\TORMENT_administration\direct-real-admission-p1-attempt-8-20260906\attempt8_capture_and_preparation.py
```

The fresh precheck passed at the required revision, with all observations
absent:

```text
REST_SERVICE = ABSENT
MCP_SERVER = ABSENT
DIRECT_TORMENT_TOOL_OR_SCRIPT = ABSENT
AGENT_RUNNER_OR_OTHER_FABRIC_HOST = ABSENT
NONTERMINAL_ROOT_JOB = ABSENT
127.0.0.1:8787 = ABSENT
```

The process census used `WINDOWS_CIM_PROCESS_CENSUS_V1` and the listener
observation used `WINDOWS_TCP_LISTENER_TABLE_V1`. No process, listener, or
service was controlled.

## Legal source refusal

After durable `CAPTURE_STARTED`, the external body entered the existing
writer-freeze capture with `minimum_delta_seconds = 60` and ran direct
preparation only through its qualified `during_capture` seam. The canonical
event records this exact terminal refusal:

```text
phase = CAPTURE_OR_DIRECT_PREPARATION
exception_type = CorrectiveFreezePacketRefused
exception_message = typed evidence source must be a non-symlink regular file:
path=C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric\data\workspaces\ws3\agents\a1\private\embeddings\manifest.json
shape=ABSENT

FAILED_SOURCE_PATH = C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric\data\workspaces\ws3\agents\a1\private\embeddings\manifest.json
FAILED_SOURCE_SHAPE = ABSENT
```

No source repair, manifest creation, representation inference, alternate
probe, capture retry, or child relaunch was performed. Because capture did not
return, no writer-freeze payload/witness, direct-preparation result, complete
source census, or `P1_READY` checkpoint was created.

## Mutation and authority ledger

```text
IMPORT_PROBE = PASS
PROBE_REAL_CHILD_INVOCATION_PARITY = PASS
WRITER_CENSUS = PASS
SOURCE_STABILITY = NOT_RETAINED_AS_CAPTURE_SUCCESS
DIRECT_SOURCE_PREPARATION = REFUSED
REAL_SOURCE_CENSUS = NOT_CREATED
FRESH_WRITER_PAYLOAD = NOT_CREATED
FRESH_WRITER_WITNESS = NOT_CREATED
WRITER_RECHECK_BINDING = NOT_CREATED

P1_NATIVE_STAGING_CORE_BOOTSTRAP = NOT_EXECUTED
REAL_NATIVE_STAGING_CORE_CREATED = NO
P1_STARTED = NO
DURABLE_NATIVE_STATE_CREATED = NO
SQLITE_CREATE_API_INVOKED = NO
ROOT_ADMISSION_ENVELOPE_PERSISTED = NO
CUTOVER_PENDING = NO
NORMALIZATION_EXECUTED = NO
P2_EXECUTED = NO
P5_EXECUTED = NO
P6_EXECUTED = NO
P7_EXECUTED = NO

LEGACY_SOURCE_MUTATION = NONE
LEGACY_MEMORY_AUTHORITY = PRESERVED
SERVICE_RESTART = NONE
STOPPED_FOR_REVIEW = YES
```

Attempt 8 is closed at durable `FINAL_STOP`. Any future work requires new,
explicit authorization, a new operation ID, and a fresh external result
directory; it must not reuse or advance this ledger.

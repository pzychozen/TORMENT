# TORMENT — Direct Real Admission Preparation and P1 Staging Bootstrap Attempt 6 Result

**Date:** 2026-09-05
**Authorization:** `DIRECT_REAL_ADMISSION_PREPARATION_AND_P1_STAGING_BOOTSTRAP_ATTEMPT_6 = YES`
**Required start revision:** `4be3abd1f8ed43709ad784128c6de5875f6c98d9` (`HEAD == origin/main`)

## Authoritative result

```text
DIRECT_REAL_ADMISSION_PREPARATION_ATTEMPT_6 = INTERRUPTED_PRE_CAPTURE
ADMINISTRATION_OPERATION_ID = direct-real-admission-p1-attempt-6-20260905
ADMINISTRATION_RESULT_DIRECTORY = C:\TORMENT\TORMENT_administration\direct-real-admission-p1-attempt-6-20260905
ADMINISTRATION_STATE_PATH = C:\TORMENT\TORMENT_administration\direct-real-admission-p1-attempt-6-20260905\administration_state.json
ADMINISTRATION_FINAL_STATE = CAPTURE_STARTED
ADMINISTRATION_ATTACHED_HOST_DEPENDENCY = NONE
```

The external canonical `administration_state.json`, not terminal output, is
the authority for this result. It was reopened and validated after the child
was absent. Its durable sequence is:

```text
1  RUNNER_STARTED
2  PRECHECK_STARTED
3  PRECHECK_PASS
4  CAPTURE_STARTED
```

Its immutable run context retains the authorized operation ID, required head,
canonical existing data-root identity
`TORMENT_REAL_ROOT_DIRECT_ADMISSION_P1_20260905`, `P1_authorized = YES`,
`P1_started = NO`, and `durable_native_state_created = NO`.

## Completed precheck

Before the capture checkpoint, the required revision equality and fresh local
Windows process/listener observations passed:

```text
HEAD = 4be3abd1f8ed43709ad784128c6de5875f6c98d9
origin/main = 4be3abd1f8ed43709ad784128c6de5875f6c98d9

REST_SERVICE = ABSENT
MCP_SERVER = ABSENT
DIRECT_TORMENT_TOOL_OR_SCRIPT = ABSENT
AGENT_RUNNER_OR_OTHER_FABRIC_HOST = ABSENT
NONTERMINAL_ROOT_JOB = ABSENT
127.0.0.1:8787 = ABSENT
```

The process census used the retained Windows CIM observation shape; the
listener observation used the local TCP listener table. No process, listener,
or service was controlled.

## Interruption boundary

The child had its stdout/stderr redirected to the external administration
directory. Its non-authoritative diagnostic shows `ModuleNotFoundError` while
importing `torment_service`, before the child could invoke
`capture_root_writer_freeze_evidence(...)`. Therefore this record asserts no
source result, no source refusal, and no source census. The durable state did
not advance to `CAPTURE_RETURNED`, `CAPTURE_REFUSED`,
`DIRECT_PREPARATION_PASS`, `DIRECT_PREPARATION_REFUSED`, or `P1_READY`.

Under the Attempt 6 host-detachment law, an absent child with canonical
`CAPTURE_STARTED` is an interrupted capture state. No capture was rerun, no
transition was inferred, and no automatic retry was issued.

## Mutation and authority ledger

```text
WRITER_CENSUS = PASS
SOURCE_STABILITY = NOT_ENTERED
DIRECT_SOURCE_PREPARATION = NOT_ENTERED
REAL_SOURCE_CENSUS = NOT_CREATED
FRESH_WRITER_PAYLOAD = NOT_CREATED
FRESH_WRITER_WITNESS = NOT_CREATED
WRITER_RECHECK_BINDING = NOT_CREATED

P1_NATIVE_STAGING_CORE_BOOTSTRAP = NOT_EXECUTED
REAL_NATIVE_STAGING_CORE_CREATED_BY_ATTEMPT_6 = NO
P1_STARTED = NO
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

The file-backed runner's required containment check used the real-root path,
but no writer-freeze snapshot, direct-source read, or other source-content
observation was entered by the failed child. The child did not reach the P1
callback boundary, so no SQLite database, root profile, root-scope membership,
admission envelope, selector state, normalization record, or native authority
was created by Attempt 6.

## Next authority boundary

This attempt is closed at its durable `CAPTURE_STARTED` checkpoint. Any future
work requires a new, explicit operator authorization and must not reuse or
advance this operation's external ledger.

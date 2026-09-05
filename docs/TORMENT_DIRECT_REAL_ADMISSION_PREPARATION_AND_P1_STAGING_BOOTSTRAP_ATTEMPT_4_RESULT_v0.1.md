# TORMENT Direct Real Admission Preparation and P1 Staging Bootstrap — Attempt 4 Result

**Date:** 2026-09-05
**Authorization:** `DIRECT_REAL_ADMISSION_PREPARATION_AND_P1_STAGING_BOOTSTRAP_ATTEMPT_4 = YES`
**Authoritative revision:** `734b733d182133c5dcf18a2b1d114b1a8ea0d8a2` (`HEAD == origin/main` at start)

## Result

`DIRECT_REAL_ADMISSION_PREPARATION_ATTEMPT_4 = REFUSED`

The single authorized direct preparation entered the qualified real adapter's
`during_capture` callback after the required writer and source-stability gates.
It refused at a required regular-file boundary.  This is a terminal Attempt 4
result: no second source probe, parent traversal, content inspection, repair,
allowlist change, posture change, or preparation retry was performed.

## Exact refusal

```text
typed evidence source must be a non-symlink regular file:
path=C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric\data\workspaces\sim-ws\workspace_meta.json
shape=ABSENT
```

Natural adapter context: the refusal occurred while capturing the required
workspace metadata source for workspace `sim-ws`, before a root-native
production admission description, discovered census, source scope plans, or
geometry disposition plan could be produced.

## Gate ledger

| Gate / boundary | Result |
| --- | --- |
| Qualified real adapter factory | PASS — `build_real_direct_admission_source_adapter(...)` was used |
| Pre-capture REST / MCP / direct-writer / Fabric-host census | PASS — all absent |
| Pre-capture `127.0.0.1:8787` listener census | PASS — absent |
| Clone/repair job observation | PASS — no nonterminal job |
| Source stability | PASS — the `capture_root_writer_freeze_evidence(...)` T0/T1 interval met its 60-second minimum and reached `during_capture` |
| Direct source preparation | REFUSED — exact path and shape above |
| Root-native production admission description | NOT CREATED |
| Discovered census / source plans / external-owner closure / geometry plan | NOT CREATED |
| Writer payload / witness / fresh recheck binding | NOT CREATED — capture terminated in `during_capture` before payload construction |
| P1 native staging-core bootstrap | NOT EXECUTED |
| SQLite write | NONE |

## Nonmutation and stop ledger

```text
P1 = NOT_EXECUTED
SQLITE_WRITE = NONE
LEGACY_SOURCE_MUTATION = NONE
LEGACY_MEMORY_AUTHORITY = PRESERVED
ROOT_ADMISSION_ENVELOPE_PERSISTED = NO
CUTOVER_PENDING = NO
NORMALIZATION_EXECUTED = NO
P6_EXECUTED = NO
P7_EXECUTED = NO
STOPPED_FOR_REVIEW = YES
```

No `data/substrate/...` directory or SQLite core was created by Attempt 4.  No
service or listener was started, stopped, or restarted.  The next boundary is
blocked pending review of the exact missing required source above; this result
does not authorize source repair or a follow-up attempt.

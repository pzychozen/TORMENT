# TORMENT Post-P7 Native Production Validation - Stage 1 Result

Date: 2026-09-10

## Verdict

`POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1 = HELD_FOR_REVIEW`

The prescribed full-service launch failed during application startup, before
listening on port 8787 or accepting any production requests. The runtime raised:

```text
PublicRuntimeStartupRefused: public startup refused by durable deployment authority: effective-profile-is-not-the-qualified-selector-profile
```

The process runner returned exit code `3`. Stage 1 stopped at B (normal startup)
under the work order's stop/capture/classify instruction. No profile was injected,
no startup retry was attempted, and no production repair was performed.

This establishes a normal-launch host configuration problem for the prescribed
CMD/conda invocation. It does not establish a failed cutover, selector/core
disagreement, SQLite corruption, or a return to legacy authority. The refusal
prevented construction of a public runtime. P1-P7 remains closed.

## Repository and execution preflight

```text
STARTING_HEAD = de61fd44482725e382cba4e1aebb73ca24670270
ORIGIN_MAIN_AT_PREFLIGHT = de61fd44482725e382cba4e1aebb73ca24670270
HEAD_EQUALS_ORIGIN_MAIN_AT_PREFLIGHT = YES
TRACKED_WORKTREE_AT_PREFLIGHT = CLEAN
VALIDATION_END_HEAD = de61fd44482725e382cba4e1aebb73ca24670270
TRACKED_WORKTREE_AFTER_STARTUP_ATTEMPT = CLEAN
EXECUTION_SHELL = Windows CMD
CONDA_DEFAULT_ENV = torment
PYTHON = C:\Users\Notandi\miniconda3\envs\torment\python.exe
DATA_ROOT_OVERRIDE_PRESENT = NO
HOST_PROFILE_PRESENT = NO
HOST_DESCRIPTOR_PRESENT = NO
```

Repository: `C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric`.
The default service root therefore remained the repository's `data` directory.
No existing listener occupied port 8787 before launch. Existing untracked
artifacts were not staged, deleted, or otherwise changed by administration.

Normal command, executed from the repository through CMD:

```bat
call C:\Users\Notandi\miniconda3\condabin\conda.bat activate torment
python -m torment_service
```

A command file outside the repository captured the inherited environment and
redirected service output to a log. It did not import or replace the production
runtime, configure deployment facts, or set a backend/migration/test mode.
Environment capture was at `2026-09-10T04:54:34.811070+00:00`; the server log
identified PID `4696`. The runner returned after approximately 3.18 seconds.
At `2026-09-10T04:54:48.2397745Z`, port 8787 still had no listener.

## Interface discovery and failure classification

Existing interfaces were inspected before launch:

| Behavior | Existing production path and observed static boundary |
| --- | --- |
| Runtime health | `GET /health` reports public runtime mode after successful startup. |
| Memory query | `POST /agent/query`, `POST /retrieve`, and Spine `query_memory`. |
| Memory write | `POST /agent/ingest` and Spine `ingest`; native mutations require an idempotency key. |
| Reinforcement | Spine `reinforce` is the ordinary per-memory significance operation; feedback has different semantics. The native Spine allowlist currently admits only `ingest`, `tool_result_ingest`, and `query_memory`. |
| Character | Character state/seed REST routes and Spine `query_state` exist, but those direct routes/operations are outside the current native allowlists. Query/ingest also contain Character-linked runtime paths. |
| Trajectory | Native ingest's post-write configuration binds trajectory evidence; the normal service lifespan closes its runtime on shutdown. |

These are source observations, not successful runtime exercises or additional
production failure claims. No REST request was sent. No private/shared scope was
opened, no existing memory was reinforced, and no Stage-1 memory identifier was
created. The full service remained the object under test; no substitute harness
or lower-level native owner was executed.

The startup trace reaches `app.py`'s lifespan and runtime proxy, then
`public_runtime.py:create_public_runtime`, which refuses at line 1131.
Source inspection explains the observed result:

- `__main__.py` loads optional host proof configuration before running Uvicorn.
- `public_runtime.py:196` reads `TORMENT_DEPLOYMENT_PROFILE_JSON` and
  `TORMENT_ADMISSION_DESCRIPTOR_PATH`; neither was present after conda activation.
- With no configured profile, `create_public_runtime` supplies the legacy
  compatibility placeholder to the read-only deployment resolver (line 1075).
- `deployment_selector.py:626` refuses when the effective profile is unqualified
  or its digest differs from the qualified selector profile. This is the exact
  refusal reason in the production traceback.

Classification: missing host-qualified profile in the tested normal-launch
environment, rejected by the existing deployment guard. The compatibility
placeholder is not evidence that a legacy runtime acquired authority. No
qualified replacement profile was reconstructed or tested under this order.

The frozen expected core `f21c730f-5222-4aa8-9a5f-1c1188456df3`, selector generation
`8` / `NATIVE_ACTIVE`, and `ACTIVE_CORE` / `NATIVE_ACTIVE` / `ever_active = TRUE`
remain prior closeout evidence. Stage 1 did not complete running-owner
recognition or the requested authority confirmation, so those checks are not
reported as passed.

## Result matrix

`NOT_RUN` means startup prevented the exercise. It is neither a pass nor evidence
that the unexercised behavior itself failed. `NO` for a leak/fallback observation
is limited to this failed startup; no production query results were available.

```text
POST_P7_STAGE_1_PREFLIGHT = PASS
NORMAL_PRODUCTION_STARTUP = FAIL
SERVICE_LISTENING = NO
STARTUP_MAINTENANCE_ONLY = NOT_RUN
STARTUP_LEGACY_FALLBACK_OBSERVED = NO
NATIVE_OWNER_RECOGNITION = NOT_RUN
SELECTOR_CORE_AGREEMENT = NOT_RUN
LEGACY_PUBLIC_FALLBACK_OBSERVED = NO
PRIVATE_NATIVE_QUERY = NOT_RUN
SHARED_NATIVE_QUERY = NOT_RUN
TEXT_SEARCH = NOT_RUN
VECTOR_SEARCH = NOT_RUN
PRIVATE_SHARED_SCOPE_ISOLATION = NOT_RUN
NATIVE_MEMORY_WRITE = NOT_RUN
WRITE_THEN_READ = NOT_RUN
NATIVE_REINFORCEMENT = NOT_RUN
CHARACTER_CONTINUITY_PRE_RESTART = NOT_RUN
NATIVE_TRAJECTORY_WRITE = NOT_RUN
NORMAL_SHUTDOWN = NOT_RUN
RESTART_STARTUP = NOT_RUN
SELECTOR_STATE_AFTER_RESTART = NOT_RUN
ACTIVE_CORE_AFTER_RESTART = NOT_RUN
LEGACY_PUBLIC_FALLBACK_AFTER_RESTART = NOT_RUN
MAINTENANCE_ONLY_AFTER_RESTART = NOT_RUN
MEMORY_PERSISTENCE_AFTER_RESTART = NOT_RUN
REINFORCEMENT_PERSISTENCE_AFTER_RESTART = NOT_RUN
CHARACTER_CONTINUITY_AFTER_RESTART = NOT_RUN
PRIVATE_QUERY_AFTER_RESTART = NOT_RUN
SHARED_QUERY_AFTER_RESTART = NOT_RUN
TRAJECTORY_AUTHORITY_RECONSTRUCTION = NOT_RUN
POST_RESTART_NATIVE_TRAJECTORY_WRITE = NOT_RUN
MODEL_D_PRESERVED = NOT_OBSERVED
CERTIFIED_REFUSAL_RUNTIME_LEAK_OBSERVED = NO
STOPPED_AT_UNEXPECTED_PRODUCTION_BEHAVIOR = YES
FROZEN_AUTHORITY_INVARIANT_CONTRADICTION_OBSERVED = NO
POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1 = HELD_FOR_REVIEW
SQLITE_MIGRATION_FULLY_VALIDATED = NO
NEXT_AUTHORIZATION_BOUNDARY = POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1_REVIEW
```

The process exited on its own after failed startup. No service was killed and no
clean shutdown/restart cycle was attempted. No unit/integration tests were run:
the production traceback and existing source already explain the bounded
failure. No migration census, receipt regeneration, failure injection,
optimization, or data cleanup was performed.

## Frozen evidence and publication

Local evidence directory:
`C:\TORMENT\TORMENT_administration\post-p7-stage-1-20260910T0430Z`.
The actual execution timestamps are recorded above and in the files; the
directory name is only a run label.

| Evidence | SHA-256 |
| --- | --- |
| `startup.log` | `a56232e7b919a70709d2913027b807070865bfe99cbe879f8f44f34a6a826498` |
| `startup_environment.txt` | `365a2245bb8d7a79c73ad2ca05aea1996701157cf3029c91f3b78af2d1556fef` |
| `start_service.cmd` | `fc331aa5946a59be021d27aedd8c1c4a9730327ace21cbb1801c9a5eaeae4e4d` |
| `execution_receipt.json` | `db7b9b63d8acb3e482ab3333c7d8697f6f0225169b7eeabee3bd9d795ed16a4a` |

`preflight.json`, `post_startup_observation.json`, and `evidence_manifest.json`
retain repository/listener observations and artifact hashes. An ancillary CMD
`echo 3>` redirection left `service_exit_code.txt` empty; the authoritative exit
code is the process runner's `3`, preserved in `execution_receipt.json` and the
post-startup observation. This recording issue did not affect the service
command or its complete traceback. No memory payloads or credentials were
collected.

The only repository change is this evidence record. No production code or
semantics were modified. Publication uses an evidence-only commit after
`git diff --check` and a staged whitespace check.

`FINAL_HEAD` / `COMMIT` is the commit containing this record, identifiable with
`git log -1 --format=%H -- docs/TORMENT_POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1_RESULT_20260910.md`.
Its literal SHA cannot be embedded in its own committed contents. After push,
the exact `FINAL_HEAD`, `ORIGIN_MAIN`, remote main SHA, `HEAD_EQUALS_ORIGIN_MAIN`,
`TRACKED_WORKTREE`, and `COMMIT` are captured in `publication_verification.json`
in the evidence directory and returned with delivery.

Stage 1 is held at its review boundary. No Stage 2 work is authorized here.

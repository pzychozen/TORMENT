# TORMENT Post-P7 Native Production Validation - Stage 1R2 Result

Date: 2026-09-10

## Verdict

```text
ROOT_V2_STARTUP_CONTRACT = QUALIFIED
ROOT_V2_QUALIFIED_STARTUP = FAIL
POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1R2 = HELD_FOR_CONTRADICTORY_PRODUCTION_EVIDENCE
POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1 = HELD_FOR_REVIEW
STOPPED_AT_CONTRADICTORY_PRODUCTION_EVIDENCE = YES
SQLITE_MIGRATION_FULLY_VALIDATED = NO
```

One full-service launch followed the reconciled current root-v2 contract. The
exact host profile was accepted, and native-owner recovery returned successfully.
Startup then failed during ST/BGE embedder initialization, before listening or
accepting any production requests. The process exited with code 3.

The first logged error was TLS certificate validation while the model loader
requested Hugging Face metadata. The terminal exception was a closed HTTP
client error. Strict embedding startup propagated the failure instead of
degrading to hash embeddings. No alternate profile, descriptor, certificate
setting, offline mode, model path, dependency version, or service retry was tried.

This is the failed qualified startup classification required by R2 section 12.
It is not evidence of selector/core disagreement, a failed P7 disposition,
SQLite corruption, or legacy authority returning. The remaining Stage-1
behavior and restart checks were not reached.

## Git preflight and prior evidence

```text
STARTING_HEAD = 3c43d366a0fd3522cb12644b99dcc9cd145c296d
ORIGIN_MAIN_AT_PREFLIGHT = 3c43d366a0fd3522cb12644b99dcc9cd145c296d
HEAD_EQUALS_ORIGIN_MAIN_AT_PREFLIGHT = YES
TRACKED_WORKTREE_AT_PREFLIGHT = CLEAN
VALIDATION_END_HEAD = 3c43d366a0fd3522cb12644b99dcc9cd145c296d
STAGE_1_ATTEMPT_1 = INCOMPLETE_HOST_PROFILE_ENVIRONMENT / HELD_FOR_REVIEW
STAGE_1R1 = HELD_FOR_HOST_PROOF_EVIDENCE
PRIOR_RESULT_RECORDS_UNCHANGED = YES
R1_EXTERNAL_DESCRIPTOR_REQUIREMENT = WORK_ORDER_ASSUMPTION_NOT_APPLICABLE_TO_CURRENT_ROOT_V2_CONTRACT
```

Repository: `C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric`.
Preflight was captured at `2026-09-10T05:27:34.3959423Z`. Port 8787 had no
listener. After conda activation, no `TORMENT_*` environment variables were
inherited. The two previous records were hashed before work and checked again
after the attempt; neither was edited or superseded.

## Contract established before launch

The prelaunch contract was saved separately as `startup_contract.md` and its
hash/timestamp recorded in `prelaunch_contract_receipt.json` at
`2026-09-10T05:29:45.6716170Z`, before the service launch. Its classification
does not imply startup success.

The current path is:

1. `torment_service/__main__.py` loads host proof configuration and runs Uvicorn.
2. `app.py:156` constructs the public runtime during application lifespan.
3. `public_runtime.py:196` parses the exact seven-field host profile. At line
   1075, that profile is passed to the durable deployment resolver. Without it,
   the compatibility placeholder explains the original Stage-1 refusal.
4. `deployment_selector.py:607` requires selected-core native state, matching
   core/admission/profile witnesses, qualified profile, and SQLite 3.53.4. The
   original mismatch reason is emitted at line 626.
5. `public_runtime.py:1086` inspects the durable activation-completion witness.
   `RootAdmissionCompletionWitness` selects the root-v2 branch, which recovers
   the native owner before constructing Fabric.
6. `production_native_owner.py:564` consumes the selected core's immutable
   admission record. It binds core ID, selector state/generation, profile,
   completion witness, root-profile and runtime-scope bindings, membership
   closure, and the existing disposition receipt/P7 intent. This is normal
   recovery validation, not a regenerated migration proof.

```text
ROOT_V2_ADMISSION_EVIDENCE_SOURCE = SELECTED_CORE_IMMUTABLE_ROOT_ADMISSION_EVIDENCE
ROOT_V2_EXTERNAL_ADMISSION_DESCRIPTOR_REQUIRED = NO
ROOT_V2_EXTERNAL_ADMISSION_DESCRIPTOR_SUPPORTED = CONDITIONAL
```

`CONDITIONAL` describes the current host parser: an optional supplied path must
resolve to an existing file. Root-v2 recovery does not consume its contents or
use it to select authority. Missing admission evidence inside the selected core
cannot be replaced by that file. The v1 branch still requires and validates an
external descriptor; the old contract is not globally obsolete.

| Input | Current classification | Applied to this launch |
| --- | --- | --- |
| `TORMENT_DEPLOYMENT_PROFILE_JSON` | REQUIRED for native startup. Exact field set and qualified matching digest; missing/invalid/mismatched facts refuse. | Recovered unchanged from selected-core evidence into temporary CMD environment. |
| `TORMENT_ADMISSION_DESCRIPTOR_PATH` | OPTIONAL at host parser, then IGNORED as admission content by root-v2. Required in v1. Empty/non-file paths are INVALID; descriptor without profile is INVALID. | Absent. |
| `TORMENT_EMBED_PROVIDER` | Runtime option defaults to hash; `st` is REQUIRED for the selected lane. | `st`. |
| `TORMENT_EMBED_MODEL` | OPTIONAL for `st`: factory default is the exact selected BGE model. | Absent; `BAAI/bge-small-en-v1.5` default applied. |
| `TORMENT_EMBED_DEVICE` | OPTIONAL; ST factory defaults to CPU. | Absent; `cpu` default applied. |
| `TORMENT_EMBED_STRICT` | OPTIONAL in generic Fabric; REQUIRED for this fail-closed qualified launch because its absence permits hash degradation after model errors. | `1`. |

Model/device defaults are defined at `embeddings.py:240`; strict/fallback
behavior is defined at `fabric.py:1053`. The profile alone supplies deployment
proof; it does not configure the Fabric embedder. Only the three required
environment variables above were set. No data-root, feature, compression,
deep-memory, LLM, or migration-mode override was supplied.

## Exact recovered profile and authority

The existing read-only selector/core/envelope APIs recovered the seven-field
profile from `RootAdmissionEnvelopeRecord.effective_profile_payload`, using the
selected core and its completion witness. Its digest matches R1 and the current
selector, core witness, completion witness, and envelope payload.

```text
HOST_PROFILE_FOUND = YES
HOST_PROFILE_MATCHES_SELECTED_DEPLOYMENT = YES
HOST_PROFILE_DIGEST = 35ec54a0d5d3a2c87fedc855f8964615e4472876c3698488ba925a41a2ae717a
ADMISSION_IDENTITY_DIGEST = e4e510131cc341375485605bf1ead86aff684a1ca938e26fdbe221bbf0673ceb
SELECTOR_GENERATION = 8
SELECTOR_STATE = NATIVE_ACTIVE
ACTIVE_CORE_ID = f21c730f-5222-4aa8-9a5f-1c1188456df3
CORE_ROLE = ACTIVE_CORE
CORE_DEPLOYMENT_STATE = NATIVE_ACTIVE
EVER_ACTIVE = TRUE
COMPLETION_CONTRACT = TORMENT_ROOT_ADMISSION_COMPLETION_WITNESS
COMPLETION_VERSION = 2
READ_ONLY_DEPLOYMENT_RESOLUTION = NATIVE_AGREEMENT
SQLITE_RUNTIME = 3.53.4
```

The representation is `st` / `BAAI/bge-small-en-v1.5` / 384, with compression
and deep memory disabled. The raw profile was not persisted as configuration.
The CMD launcher consumed the recovery helper's one-line JSON into a `SETLOCAL`
variable. A separate prelaunch check used the actual host parser to confirm
profile equality, descriptor absence, and the exact three configured variable
names. No runtime owner was constructed by those inspection helpers.

## Full-service execution and failure

Execution used Windows CMD from the authoritative repository and
`conda activate torment`, with
`C:\Users\Notandi\miniconda3\envs\torment\python.exe`.
The production command was exactly `python -m torment_service`; its output was
redirected to `startup.log`. The external command file only managed temporary
environment values and evidence capture; it did not substitute a runtime
harness or intercept production calls.

Prelaunch environment validation completed at
`2026-09-10T05:29:55.406519+00:00`. Uvicorn reported server PID `54692` and
`Waiting for application startup.` It never reported completed startup or a
listening address.

The complete startup log records:

```text
[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1016)
```

This occurred while requesting HEAD metadata for the public model's
`BAAI/bge-small-en-v1.5/resolve/main/adapter_config.json` on `huggingface.co`.
The library logged `Retrying in 1s [Retry 1/5]`. Its terminal exception was:

```text
RuntimeError: Cannot send a request, as the client has been closed.
ERROR:    Application startup failed. Exiting.
```

The traceback reaches `public_runtime.py:1109` (Fabric construction), then
`fabric.py:1055`, `embeddings.py:244`, and `SentenceTransformer` at
`embeddings.py:147`. Because the root-v2 owner factory at line 1099 precedes
Fabric construction, reaching line 1109 establishes that owner recovery
returned. This is startup-time owner recognition, not a published public
runtime or a successful `/health` response. Existing exception handling closes
the native owner after the subsequent Fabric initialization failure.

At `2026-09-10T05:32:00.4066776Z`, the process had exited, the CMD exit file and
process runner both reported code `3`, and port 8787 had no listener. The one
logged HTTP retry was internal library behavior during the sole service launch;
no agent-directed retry, alternate configuration, or forced termination occurred.

Classification: embedding-provider initialization failed, with an initial TLS
issuer/certificate error and a subsequent closed-client exception. Their deeper
cause was not investigated or repaired under this order. No certificate bypass,
cache change, offline switch, or dependency change was made.

One narrow read-only post-exit observation at
`2026-09-10T05:33:03.020408+00:00` again found generation 8, the same active
native core, `ever_active = TRUE`, and exact selector/core/profile witnesses.
No migration census, normalization, receipt rewrite, or authority transition
was run.

## Behavioral and restart results

`NATIVE_OWNER_RECOGNITION = PASS` is limited to the factory-return evidence
above. `SELECTOR_CORE_AGREEMENT = PASS` is supported by durable read-only checks
and the startup path. All service-dependent checks are `NOT_RUN`, not failures
of those unexercised behaviors. Observation fields marked `NO` do not claim
coverage of unavailable query results.

```text
ROOT_V2_QUALIFIED_STARTUP = FAIL
NORMAL_PRODUCTION_STARTUP = FAIL
NATIVE_OWNER_RECOGNITION = PASS
SELECTOR_CORE_AGREEMENT = PASS
LEGACY_PUBLIC_FALLBACK_OBSERVED = NO
SERVICE_LISTENING = NO
MAINTENANCE_ONLY_POSTURE = NOT_RUN
PUBLIC_MEMORY_MODE = NOT_AVAILABLE
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
MEMORY_PERSISTENCE_AFTER_RESTART = NOT_RUN
REINFORCEMENT_PERSISTENCE_AFTER_RESTART = NOT_RUN
CHARACTER_CONTINUITY_AFTER_RESTART = NOT_RUN
PRIVATE_QUERY_AFTER_RESTART = NOT_RUN
SHARED_QUERY_AFTER_RESTART = NOT_RUN
TRAJECTORY_AUTHORITY_RECONSTRUCTION = NOT_RUN
POST_RESTART_NATIVE_TRAJECTORY_WRITE = NOT_RUN
MODEL_D_PRESERVED = NOT_OBSERVED
CERTIFIED_REFUSAL_RUNTIME_LEAK_OBSERVED = NO
POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1R2 = HELD_FOR_CONTRADICTORY_PRODUCTION_EVIDENCE
POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1 = HELD_FOR_REVIEW
STOPPED_AT_CONTRADICTORY_PRODUCTION_EVIDENCE = YES
SQLITE_MIGRATION_FULLY_VALIDATED = NO
NEXT_AUTHORIZATION_BOUNDARY = POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1R2_REVIEW
```

No HTTP production requests, memory writes, reinforcement, Character exercises,
or trajectory writes occurred. No unit/integration tests were run. The real
service failure is the primary evidence; no test suite was substituted for it.

## Evidence and publication

Evidence directory:
`C:\TORMENT\TORMENT_administration\post-p7-stage-1r2-20260910`.

| Evidence | SHA-256 |
| --- | --- |
| `startup_contract.md` | `31ae31e0ed1ca3b86e4afd55695c5e51bbdd19b952bc2e4ce3a0b9003c1e98ac` |
| `prelaunch_contract_receipt.json` | `aa202182a7f27536481399eb77d3223cf3fabb082d207d810091113ac012e690` |
| `prelaunch_environment.json` | `c81d7e33791dfb6b331c7da0cb69e38ea3a7089a2d65dd477c2a5d0eac51e264` |
| `startup.log` | `39bd940c28961fddfd6c9e1b0ef07602d6c44af696065ea82e047c44a42de084` |
| `execution_receipt.json` | `3c57cb7d019c6f665e6cdd20c7aba6a725d002a79d26775c095b50450a8719e1` |
| `authority_after_failed_startup.json` | `480a365e69b148a79ced426f20954422cca5fef5b872025e0ae4fb33bb1cc942` |

`evidence_manifest.json` also hashes the original preflight, launch/helper files,
profile observation, post-startup observation, and exit-code file. No secrets,
idempotency keys, or memory payloads were collected.

The only repository change is this new evidence record. Production code,
configuration defaults, `.env`, and prior records were not edited. No
pre-existing untracked artifacts were staged or cleaned. Publication follows
the existing evidence-only policy, with `git diff --check` and staged whitespace
validation before committing and pushing.

`FINAL_HEAD` / `COMMIT` identifies the commit containing this record, resolvable
with `git log -1 --format=%H -- docs/TORMENT_POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1R2_RESULT_20260910.md`.
Its literal SHA cannot be embedded in its own committed contents. Exact
`FINAL_HEAD`, `ORIGIN_MAIN`, remote main SHA, `HEAD_EQUALS_ORIGIN_MAIN`,
`TRACKED_WORKTREE`, and `COMMIT` are captured after publication in
`publication_verification.json` in the evidence directory and returned with
delivery. Work stops at the R2 review boundary.

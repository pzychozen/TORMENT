# TORMENT post-P7 native production validation: Stage 1R3

## Result

The legitimate cached-model recovery passed: the normal service started in
native mode with the real `st` / `BAAI/bge-small-en-v1.5` / 384 embedder and
without degradation. The first ordinary query returned no response within the
client's 240-second limit. Stage-1 administration stopped at that observation;
no write, reinforcement, or restart was attempted. This record distinguishes
successful startup recovery from incomplete production behavior validation.

R2's primary embedding startup failure is classified as
`PYTHON_CA_TRUST_CONFIGURATION_FAILURE`. A complete usable model was already
cached. The default named-model load remained remote-capable and attempted
optional adapter metadata over HTTPS; that request failed Python certificate
verification. The subsequent closed-client exception was secondary.

The recovery used only process-local `HF_HUB_OFFLINE=1`, an existing dependency
setting. It preserved the canonical model identifier and exact R2 root-v2
startup contract. No TLS bypass, model download, package change, persistent
configuration change, or production source change occurred.

## Git and scope

```text
STARTING_HEAD = 313bdcb183d1af76b90dfede84e8c8ff9bebcc8c
ORIGIN_MAIN_AT_START = 313bdcb183d1af76b90dfede84e8c8ff9bebcc8c
HEAD_EQUALS_ORIGIN_MAIN_AT_START = YES
TRACKED_WORKTREE_AT_START = CLEAN
POST_P7_STAGE_1_PREFLIGHT = PASS
VALIDATION_CODE_HEAD = 313bdcb183d1af76b90dfede84e8c8ff9bebcc8c
```

Preflight was recorded at `2026-09-10T05:47:02Z`. No process was listening on
port 8787. Existing untracked artifacts were preserved. The only repository
change for publication is this new result record; diagnostic scripts and raw
bounded observations reside outside the repository in
`C:\TORMENT\TORMENT_administration\post-p7-stage-1r3-20260910`.

The R2 record's preserved SHA-256 is
`57ff6a7f2da1dbafeaa28e7866eb88f2a23d9ed615e85b10e3c2f960b94a3a0e`.
The R2 external `startup_contract.md` remains unchanged, SHA-256
`31ae31e0ed1ca3b86e4afd55695c5e51bbdd19b952bc2e4ce3a0b9003c1e98ac`.
No P1-P7 proof campaign, historical refusal reclassification, migration repair,
selector transition, or direct database write was performed.

## Initialization and cache path

The unchanged path is service startup -> `create_public_runtime` -> root-v2
native owner recovery -> `TormentFabric` -> `build_embedder_from_env` ->
`STEmbedding` -> `SentenceTransformer(model, device=device)`.

Repository anchors at the validation commit:

- `torment_service/public_runtime.py:1099`: native owner factory, before
  Fabric construction at line 1109.
- `torment_service/fabric.py:1051`: embedding setup; strict mode propagates
  initialization failure instead of accepting a hash fallback.
- `torment_service/embeddings.py:127`: `STEmbedding` preserves the supplied
  model identifier and calls `SentenceTransformer` at line 147 without an
  explicit `local_files_only` or cache-directory argument.
- `torment_service/embeddings.py:242`: ST factory default model is
  `BAAI/bge-small-en-v1.5`; device is the unchanged CPU default.

R2 supplied `TORMENT_EMBED_PROVIDER=st` and `TORMENT_EMBED_STRICT=1` alongside
the exact selected deployment profile. It did not override the model, device,
cache, or offline settings. Hugging Face resolved its default cache under the
current user's home. A named-model request may consult remote metadata even
when weights are cached. The specific failed R2 request was HEAD for
`https://huggingface.co/BAAI/bge-small-en-v1.5/resolve/main/adapter_config.json`.
The observed failure was metadata resolution, not evidence of a weights
download or absent weights.

```text
BGE_MODEL_REQUEST = BAAI/bge-small-en-v1.5
BGE_SOURCE_MODE_BEFORE_RECOVERY = REMOTE_CAPABLE
BGE_SOURCE_MODE = CACHE (HF_HUB_OFFLINE=1 for recovery)
BGE_CACHE_ENTRY_FOUND = YES
BGE_CACHE_COMPLETE = YES
BGE_PARTIAL_DOWNLOAD_OBSERVED = NO
BGE_MODEL_FILES_APPEAR_USABLE_LOCALLY = YES
```

Cache root:
`C:\Users\Notandi\.cache\huggingface\hub\models--BAAI--bge-small-en-v1.5`.
`refs/main` resolves to snapshot
`5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`. Its 11 files include the
133,466,304-byte `model.safetensors`, model and sentence-transformer configs,
`modules.json`, tokenizer assets, and pooling configuration. All snapshot
symlinks resolve to existing blobs. The declared normalization module uses its
built-in implementation and needs no separate saved parameters. No incomplete
download was found in this model namespace.

Completeness was established by execution, beyond a filename census. In a
fresh CMD process after `conda activate torment`, the unchanged production
factory loaded the canonical model under `HF_HUB_OFFLINE=1` and embedded a
bounded diagnostic string. Provider/model/dimension remained exactly
`st` / `BAAI/bge-small-en-v1.5` / 384; the vector was finite with norm 1.0.
The check observed zero `socket.connect` audit events and identical before/after
SHA-256 and length fingerprints for all 29 cache and model-lock files. It did
not construct a service or native owner. Evidence:
`cached_model_usability.json`, SHA-256
`050d987411e9a35ee6db60f927d1d99268fcf374cf1d986170c00c57f08a8233`.

One earlier diagnostic invocation failed its environment assertion before
loading a model: inline CMD environment assignment through the command runner
did not supply `HF_HUB_OFFLINE`. A real external `.cmd` file corrected that
invocation. The failed diagnostic log was retained. It was neither a service
startup retry nor an embedding initialization failure.

## Runtime and verified TLS observations

All project Python execution used Windows CMD with `conda activate torment`.
The executable was
`C:\Users\Notandi\miniconda3\envs\torment\python.exe`.

| Component | Observed version |
| --- | --- |
| Python | 3.11.15, Anaconda, AMD64 |
| sentence-transformers | 5.5.0 |
| transformers | 5.8.1 |
| huggingface_hub | 1.14.0 |
| httpx | 0.28.1 |
| requests | 2.34.0 |
| certifi | 2026.4.22 |
| OpenSSL | 3.6.3, 9 Jun 2026 |
| torch | 2.12.0 |
| safetensors | 0.7.0 |
| truststore | 0.10.4, already installed |
| SQLite runtime | 3.53.4 |

The activated environment supplies:

```text
SSL_CERT_FILE = C:\Users\Notandi\miniconda3\envs\torment\Library\ssl\cacert.pem
SSL_CERT_DIR = C:\Users\Notandi\miniconda3\envs\torment\Library\ssl\certs
CUSTOM_CA_CONFIGURATION_PRESENT = YES
```

Here YES means explicit CA-path environment configuration is present; it does
not establish that a user installed a custom certificate. `REQUESTS_CA_BUNDLE`,
`CURL_CA_BUNDLE`, `HF_HOME`, `HF_HUB_CACHE`, `TRANSFORMERS_CACHE`, and
`SENTENCE_TRANSFORMERS_HOME` were absent. No proxy-variable names were present.
No unrelated environment values or secrets were dumped.

`ssl.get_default_verify_paths()` resolved cafile/capath to the two paths above;
its compiled fallback paths were
`C:\Program Files\Common Files\ssl\cert.pem` and
`C:\Program Files\Common Files\ssl\certs`.
Certifi's available bundle was
`C:\Users\Notandi\miniconda3\envs\torment\Lib\site-packages\certifi\cacert.pem`,
SHA-256 `16be3f6feb15408195dcfe3aa1a75ef9db72f646b96ebbefdc68f56255f799f8`.
The installed HTTPX `_config.py` selects `SSL_CERT_FILE` ahead of certifi when
trusting the environment. Hugging Face's default client uses HTTPX.

The minimal remote diagnostic targeted the same public host and optional
metadata URL. It used ordinary verified TLS; no model body was downloaded.

| Path | Result | Evidence |
| --- | --- | --- |
| Windows curl 8.21.0 / Schannel | PASS | Verified HEAD, exit 0, HTTP 404, `ssl_verify_result=0`; optional adapter metadata is absent. |
| Python default SSL context | FAIL | Context construction failed with `ASN1: NOT_ENOUGH_DATA`, before a handshake. |
| Python explicit configured CA file | FAIL | Verified handshake failed with code 20, `unable to get local issuer certificate`. |
| HTTPX default client | FAIL | `CERTIFICATE_VERIFY_FAILED`, code 20 / local issuer unavailable. |
| Hugging Face default session | FAIL | Same verified TLS failure through HTTPX. |

```text
SYSTEM_TLS_TO_MODEL_HOST = PASS
PYTHON_TLS_TO_MODEL_HOST = FAIL
MODEL_LIBRARY_TLS_TO_MODEL_HOST = FAIL
BGE_STARTUP_FAILURE_CLASS = PYTHON_CA_TRUST_CONFIGURATION_FAILURE
CLIENT_CLOSED_ERROR_IS_PRIMARY = NO
```

No peer issuer was captured from the failed verified Python connection. These
observations isolate the failure to the Python trust configuration/path;
they do not identify an exact missing certificate or authorize a trust-store
repair. No such repair was attempted.

The installed Hugging Face `_http.py` obtains `client = get_session()` before
its retry loop. On the initial connection exception it calls `close_session()`;
the next iteration can reuse the already-closed local client reference. This
explains the later closed-client exception in R2's sequence. The TLS failure
comes first and reproduces independently. No dependency code was patched.

## Comparison with prior success

The narrow comparison does not equate migration qualification with a full
production service boot:

- Actual BGE use is established in prior successful P3 production normalization.
  `scripts/real_root_p3_production.py:156` loads the existing snapshot by local
  path, checks ST/384, and restores the canonical model label for admission.
  Its main path also sets both HF and Transformers offline flags. The committed
  P3 result records successful B3B normalization.
- P6 relies on qualified admission evidence; it is not evidence of a fresh
  `SentenceTransformer` service initialization.
- Final P7's external `run_post_p7_bounded_native_smoke.py` uses `ProbeEmbedder`,
  which advertises admitted lane metadata but returns a deterministic test
  vector. The successful bounded native query did not load BGE or require its
  model cache/network. Its valid `audit_smoke_v0_2` / `smoke_runner` scope is
  reused for the R3 service request.

```text
WAS_THE_SAME_BGE_MODEL_USED_DURING_PRIOR_SUCCESS = YES (P3); NO (final P7 probe)
WAS_A_LOCAL_CACHE_USED_DURING_PRIOR_SUCCESS = YES (P3); NO (final P7 probe)
WAS_NETWORK_ACCESS_REQUIRED_DURING_PRIOR_SUCCESS = NO (these model/probe paths)
WAS_THE_SAME_CONDA_ENV_USED = UNESTABLISHED (historical process-level comparison)
```

The scoped evidence above establishes model-loading differences; it does not
establish historical package-version or process-environment identity. R3's own
activated environment is directly verified. P3's snapshot-path relabeling was
not copied into production: the normal embedder exposes its supplied model
string, and native binding checks that string against the admitted model.
Using a filesystem path as `TORMENT_EMBED_MODEL` would not preserve that
identity by itself.

## Recovery gate and one service retry

The installed dependencies already support `HF_HUB_OFFLINE=1`: Hugging Face's
HTTP request hook checks offline mode, and Transformers `utils/hub.py:363`
forces local-files-only resolution in offline mode. The successful production
factory diagnostic proved that this setting works for the current named model,
installed versions, and complete cache while preserving the admitted identity.

Before starting the service, at `2026-09-10T05:53:42.5686486Z`, the evidence
recorded:

```text
LEGITIMATE_RECOVERY_ESTABLISHED = YES
BGE_RECOVERY_RETRY_AUTHORIZED_BY_EVIDENCE = YES
SERVICE_RETRY_COUNT_BEFORE_LAUNCH = 0
PERMITTED_INITIAL_SERVICE_RETRY_COUNT = 1
RECOVERY = HF_HUB_OFFLINE=1 in SETLOCAL process environment
TLS_VERIFICATION_CHANGED = NO
PERSISTENT_CONFIGURATION_CHANGED = NO
MODEL_REDOWNLOAD = NO
```

The CMD launcher reused R2's exact seven-field host profile, recovered through
existing read-only selected-core APIs, and retained strict ST initialization.
The sole recovery addition was `HF_HUB_OFFLINE=1`. It did not set a model path,
external admission descriptor, data-root override, LLM override, or a new
compression/deep-memory mode. Prelaunch validation at
`2026-09-10T05:53:56.151491+00:00` confirmed:

```text
ROOT_V2_ADMISSION_EVIDENCE_SOURCE = SELECTED_CORE_IMMUTABLE_ROOT_ADMISSION_EVIDENCE
ROOT_V2_EXTERNAL_ADMISSION_DESCRIPTOR_REQUIRED = NO
HOST_PROFILE_MATCHES_SELECTED_DEPLOYMENT = YES
SELECTOR_GENERATION = 8
SELECTOR_STATE = NATIVE_ACTIVE
ACTIVE_CORE = f21c730f-5222-4aa8-9a5f-1c1188456df3
CORE_ROLE = ACTIVE_CORE
CORE_DEPLOYMENT_STATE = NATIVE_ACTIVE
EVER_ACTIVE = TRUE
COMPLETION_VERSION = 2
READ_ONLY_DEPLOYMENT_RESOLUTION = NATIVE_AGREEMENT
PROFILE_DIGEST = 35ec54a0d5d3a2c87fedc855f8964615e4472876c3698488ba925a41a2ae717a
ROOT_ADMISSION_ENVELOPE_DIGEST = e4e510131cc341375485605bf1ead86aff684a1ca938e26fdbe221bbf0673ceb
```

The production command was exactly `python -m torment_service`, run in the
authoritative repository after `conda activate torment`. PID 28044 reported
completed application startup and listened at `127.0.0.1:8787`. At
`2026-09-10T05:59:03.530838+00:00`, ordinary `GET /health` returned HTTP 200,
`ok=true`, `public_memory_mode=NATIVE`, provider `st`, canonical BGE model,
dimension 384, and `embedder_degraded=false`. The health field
`requested_embedder.model` was empty because the environment did not override
the factory default; the actual embedder identity was fully populated.

```text
R3_STARTUP_RETRY = PASS
NORMAL_PRODUCTION_STARTUP = PASS
NATIVE_OWNER_RECOGNITION = PASS
SELECTOR_CORE_AGREEMENT = PASS
LEGACY_PUBLIC_FALLBACK_OBSERVED = NO
MAINTENANCE_ONLY_POSTURE = NO
SERVICE_LISTENING_DURING_VALIDATION = YES
```

## Resumed behavior and stop

At `2026-09-10T05:59:09.911714+00:00`, the ordinary REST client sent one
`POST /agent/query` using workspace `audit_smoke_v0_2`, agent `smoke_runner`,
admitted shared domain `personal`, `top_k=8`, explanation and continuity-debug
enabled, and the safe retained P7 smoke-memory search text. This normal endpoint
accepts text and performs native retrieval with the real configured embedder;
the client did not inject a vector, use a lower-level owner, or fabricate a
private motif-domain identifier. No raw memory response was received or saved.

The client recorded `TimeoutError: timed out`, elapsed 240.0 seconds, no HTTP
status, and zero response bytes. This is the first unexpected behavior and the
Stage-1 stop point. It is a bounded client observation, not proof of an SQLite
authority defect, corruption, scope leak, or a failed search calculation.
Server completion and shutdown observations are recorded below separately.

The only service requests were one health check and this one query. No
`/agent/ingest`, feedback, direct SQLite mutation, trajectory write, or restart
request was issued. No second service retry or modified query was attempted.
Normal shutdown was requested once with Ctrl+C; the listener closed and Uvicorn
reported that it was waiting for the original background task to complete.
No second Ctrl+C or force kill was used.

Uvicorn subsequently logged `Waiting for application shutdown.`,
`Application shutdown complete.`, and `Finished server process [28044]`.
The log's final write time was `2026-09-10T06:07:44.9924330Z`. The application
and command runner returned code 0. After Python had finished, CMD asked whether
to terminate the batch job; answering N allowed only the remaining exit-code
capture and batch exit. This did not start another process or send another
service signal. The final observation found neither PID 28044 nor a listener
on port 8787.

There is no query HTTP access/result line, traceback, or error line in the
complete service log. Therefore the original query's eventual internal result
is not observable after the client disconnect. Shutdown completion does not
turn the timed-out request into a successful retrieval. The 240-second limit
was the diagnostic client's bound, not an asserted product latency invariant;
no performance diagnosis or tuning followed it.

At `2026-09-10T06:09:40.919509+00:00`, a narrow read-only post-exit observation
again confirmed generation 8, the same `ACTIVE_CORE` / `NATIVE_ACTIVE` core,
`ever_active=true`, v2 completion, exact profile/envelope identities, and
`NATIVE_AGREEMENT`. It constructed no service owner. A final cache comparison
at `2026-09-10T06:09:43.131476+00:00` found all 29 files unchanged, with no
added, removed, or changed cache/lock files across the diagnostic and service
execution.

## Behavioral matrix

`PRIVATE_NATIVE_QUERY = FAIL` means that the attempted ordinary query did not
produce a response within the bounded client's wait. It does not establish
an engine or authority failure. `NOT_ESTABLISHED` marks lane/search/isolation
results unavailable from that combined request; it does not assert that an
internal lane was never entered or that a search computation failed.
`NOT_RUN` marks later checks deliberately withheld at the stop boundary.

```text
POST_P7_STAGE_1_PREFLIGHT = PASS
R3_STARTUP_RETRY = PASS
NORMAL_PRODUCTION_STARTUP = PASS
NATIVE_OWNER_RECOGNITION = PASS
SELECTOR_CORE_AGREEMENT = PASS
LEGACY_PUBLIC_FALLBACK_OBSERVED = NO
MAINTENANCE_ONLY_POSTURE = NO
PRIVATE_NATIVE_QUERY = FAIL
SHARED_NATIVE_QUERY = NOT_ESTABLISHED
TEXT_SEARCH = NOT_ESTABLISHED
VECTOR_SEARCH = NOT_ESTABLISHED
PRIVATE_SHARED_SCOPE_ISOLATION = NOT_ESTABLISHED
NATIVE_MEMORY_WRITE = NOT_RUN
WRITE_THEN_READ = NOT_RUN
NATIVE_REINFORCEMENT = NOT_RUN
CHARACTER_CONTINUITY_PRE_RESTART = NOT_RUN
NATIVE_TRAJECTORY_WRITE = NOT_RUN
NORMAL_SHUTDOWN = PASS
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
SQLITE_AUTHORITY_FAILURE = NOT_ESTABLISHED
NATIVE_RECOVERY_FAILURE = NO
SELECTOR_CORE_FAILURE = NO
PRODUCTION_EMBEDDING_INITIALIZATION_FAILURE_AFTER_RECOVERY = NO
STOPPED_AT_UNEXPECTED_PRODUCTION_BEHAVIOR = YES
POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1R3 = HELD_FOR_REVIEW
POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1 = HELD_FOR_REVIEW
SQLITE_MIGRATION_FULLY_VALIDATED = NO
NEXT_AUTHORIZATION_BOUNDARY = POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1R3_REVIEW
```

The 35 certified memory refusals and 23 certified motif refusals were not
reopened. No leakage was observed, but no successful query-result coverage is
claimed. The model-D plan contract was not changed; runtime behavior coverage
remains limited by the query observation. No unit/integration suite, stress
test, failure injection, performance optimization, or substitute service
harness was used.

## Evidence and publication

Evidence directory:
`C:\TORMENT\TORMENT_administration\post-p7-stage-1r3-20260910`.
The complete `evidence_manifest.json` hashes the external scripts, launch file,
diagnostic outputs, request observations, cache checks, final authority check,
exit code, and behavioral matrix. Its SHA-256 is
`360afb731fe223ad2466d88b3596a41bdd9af0b6a9a0490e59b7b4901aaa9f81`.

| Evidence | SHA-256 |
| --- | --- |
| `environment_cache_observation.json` | `5718d3f5d018cbf55e99fef1d68e137d2ec4594bd889b9f47b02676ee4fa12cd` |
| `python_tls_observation.json` | `ea2dc1dd05c1302887291263389da9290ef8260af7a3146f14e280aa425e1b98` |
| `system_tls_observation.json` | `b47ccf3df3d6951f4c65a758ad208a2109f0717bf532135cb398c02b045f227a` |
| `recovery_authorization_before_retry.json` | `1af9deeb6b133d3d734c4451a755720401d056088aace546c64cc5c3c839f59f` |
| `prelaunch_environment.json` | `fa8ad326676fbb271b6b02bcc0fe70fcfc746fda424a40e687cbbe8b5f2d395b` |
| `startup.log` | `8185193f2a42b8c519439b74d94d7c3938cc9075bb5e35b1775c237954bb611c` |
| `health_before.json` | `0bd4ccc515c3b86a8d9e7eee220951a0bf763803a534d29c4800e753aa411ed7` |
| `initial_query.json` | `2ea63ae83a137985e648c52fe47ab1051e9fbf15c706f8c152a2545e3a6c7793` |
| `execution_receipt.json` | `8ebcebf56638b417d06d0bea606ef29d12b8590c7a07ffee9f19baec2a12cedb` |
| `host_proof_observation.json` | `d10dbcd0e52b3503b1036dec6468759a88579000db122efd70094697154a6d9b` |
| `cache_after_service.json` | `dd42e04f8c81c3f702e1523434298c715facf493eccc6bbe706dba3ac8d6db79` |
| `behavioral_matrix.json` | `f4a3c85b295f488f795c4980a74940d4bd59d214e6af36331edd320c8517cd82` |

The result record is the only file to stage and publish. Prior evidence and
production code/configuration remain unchanged. Publication uses
`git diff --check`, staged whitespace and scope checks, then the existing
evidence-only commit/push policy.

`FINAL_HEAD` / `COMMIT` identifies the commit containing this record, resolvable
with `git log -1 --format=%H -- docs/TORMENT_POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1R3_RESULT_20260910.md`.
Its literal SHA cannot be embedded in its own committed contents. Exact final
local, tracking, and remote main SHAs, tracked worktree state, and record hash
are captured after publication in external `publication_verification.json`
and returned with delivery.

Work stops at `POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1R3_REVIEW`.
`SQLITE_MIGRATION_FULLY_VALIDATED = NO`.

# Forge S4C — profile loader qualified; native identity route blocks setup

2026-09-12. **TORMENT_FORGE_S4C = BLOCKED.**

The authorized Windows profile-loader correction passed actual CMD execution,
preserved the exact seven profile values, and was committed and pushed as
`e5629d3a7e6ae77b6a32c2c02f5f68a23707ba55`:
`fix: load forge genesis profile correctly in Windows CMD`.

The same S4 root then started successfully through normal
`python -m torment_service`. Health returned HTTP 200, NATIVE public memory mode,
ST / BAAI/bge-small-en-v1.5 / 384, and embedder_degraded=false.

The next gate failed: the actual generated chat script's `setup()` passed its
health read, then received HTTP 409 for:

```text
GET /agent/forge_qualification/identity?workspace_id=forge_qualification
```

Execution stopped there. No ordinary query, ingest, conversational model call,
HTTP retry, alternative endpoint, or runtime repair followed. Ordinary Ctrl+C
completed Uvicorn shutdown. Port 8787 is absent, and all 19 root files are
byte-identical to their pre-service state.

## Preserved chronology and scope

1. S4 used the actual default Forge request with real cached BGE, successfully
   created the native root, and successfully replayed Genesis without replanting.
2. S4 correctly stopped because `set /p` loaded only `{` from the multiline I9
   profile. Its original record remains unchanged:
   `TORMENT_FORGE_S4_REAL_SOLO_USER_FLOW_QUALIFICATION_20260911.md`.
3. The original blocker had already been committed as
   `3811960f9572d37768d97450943237c42bc4dff6`; no duplicate record was created.
4. GPT authorized only a Forge Windows loader correction and focused regression
   coverage. The correction was qualified, committed and pushed before service
   qualification resumed. That push also published the existing blocker commit.
5. The same active root resumed. Startup and health passed; generated chat setup
   hit the native REST route boundary and stopped.

Only these implementation files changed:

- `start/torment_character_creator.html`: replace the Solo single-line reader
  with a Python JSON load/dump transported through interactive CMD `for /f`.
- `scripts/check_forge_genesis.py`: reject the old loader, require the complete
  loader, and execute it through real CMD with a multiline I9 profile.

No I9 serializer, Genesis source, deployment authority, native REST classification,
public runtime, identity store, Character behavior, or ordinary query/ingest
implementation was changed. Hivemind output was unchanged. The resumed service
qualification made no further implementation or test changes.

Every project command used Windows CMD with `conda activate torment`. No new
Genesis confirmation was requested. Genesis create/replay were not rerun.

## Complete-profile transport qualification

Forge now emits the authorized interactive CMD form:

```cmd
for /f "delims=" %P in ('python -X utf8 -c "import sys,json; print(json.dumps(json.load(open(sys.argv[1]))))" torment_genesis_profile.json') do @set "TORMENT_DEPLOYMENT_PROFILE_JSON=%P"
```

The existing I9 profile is read and parsed; Python only serializes the same
object onto one line. Forge does not construct a deployment profile. The broken
`set /p TORMENT_DEPLOYMENT_PROFILE_JSON=` alternative is absent from Solo output
and its Markdown export.

The Windows regression ran the actual generated command through `cmd.exe`, then
launched a child Python process from that same environment. Its assertions
parsed the environment JSON, compared all values with the actual I9 profile,
required exactly seven fields, and rejected embedded newlines. All passed.

The test consumed the unchanged S4 `profile.json` bytes, using the conventional
Forge filename in its external test directory. Batch execution adapted `%P` to
`%%P`; the interactive user output retains `%P`.

All 21 prior S3 request/validity/refusal cases passed, together with the new
Windows transport case, JavaScript syntax checking, emitted Python compilation,
verification-only setup checks, Solo Alignment guards and S1/S2 security checks.

Regeneration using the exact S4 fixture input, both before and after the correction
commit, produced byte-for-byte identical request JSON. The only changed output
block was `out-env`; Markdown reflects that block's corrected loader. The chat
script, Genesis command, prompt and query/ingest output were unchanged.

| Retained artifact | SHA-256 |
| --- | --- |
| request.json | eb3c5a3c957c9f217fe158c3a48218ad8caaf3b78f8a15ed1a2756eb885b0bba |
| intent.json | 1adac316dc60f1ee0d866e4f85faed64d6e475d46dd095a46b663978d7b9c059 |
| profile.json | 177fae72b163521a3be69ef496f060749907ea20a163dc19d61a03e69f3887ed |

## Same-root normal startup

Administration directory remains:

```text
C:\Users\Notandi\AppData\Local\Temp\torment-forge-s4-5c3gxxfn
```

Its original `request.json`, `intent.json`, `profile.json`, and `root` were reused.
Continuation evidence is under `evidence/s4c`. No new native root was created.

After the correction commit, Forge output was regenerated again. Its Windows
Step 3 was executed from the repository, with only the existing external profile
path substituted and `%P` adapted to `%%P` for the captured batch script.
The generated environment set the exact disposable data root, parsed profile,
ST provider, BGE model, CPU device, and strict embedding flag. It cleared
TORMENT_PROFILE and TORMENT_ADMISSION_DESCRIPTOR_PATH. Default Character,
compression-off and SRG settings remained as generated. HF_HUB_OFFLINE=1 remained
in force, and Python bytecode output was suppressed outside the product flow.

The final command was normal `python -m torment_service`, without a service
harness, direct ASGI construction, runtime monkeypatch or alternate factory.
Service PID **66380** loaded the existing local BGE weights and completed normal
Uvicorn startup. The first health response recorded:

```text
HTTP_STATUS = 200
public_memory_mode = NATIVE
embedder.provider = st
embedder.model = BAAI/bge-small-en-v1.5
embedder.dim = 384
embedder_degraded = false
requested_embedder.strict = true
profile.applied_count = 0
```

Read-only native recovery before and after service execution established:

```text
GENESIS_FENCE = NATIVE_AUTHORITY_WINS
DEPLOYMENT_RESOLUTION = NATIVE_AGREEMENT
SELECTOR_GENERATION = 2
SELECTOR_STATE = NATIVE_ACTIVE
CORE_ROLE = ACTIVE_CORE
CORE_DEPLOYMENT = NATIVE_ACTIVE
COMPLETION_TYPE = NativeGenesisCompletionWitness
COMPLETION_DIGEST = fcb133315fda029786b1a791809053137f33480614afae74614d7a7e3f115a3a
SEED_EIDS = [0, 1, 2]
READY_USABLE_SEED_REPRESENTATIONS = 3
```

The exact seven-field completion profile, seed completion, representation payload
hashes, native object/operation counts and all root file hashes were unchanged.
No Genesis phase or seed planting replay occurred during this continuation.

## First continuation mismatch: native REST classification

The actual emitted Python file was loaded through importlib without invoking
its `__main__` chat loop. Only its `setup()` was called. The script imported its
normal Anthropic SDK dependency, but constructed no conversational client and
made no model call.

The service access log contains exactly three requests:

| Origin | Request | Status |
| --- | --- | --- |
| S4C health gate | GET /health | 200 |
| Generated setup | GET /health | 200 |
| Generated setup | GET /agent/forge_qualification/identity?workspace_id=forge_qualification | 409 |

The generated error message reported that the onboarded identity could not be
verified, advised completing Genesis/checking the selected identity, and exited
with status 1. The ordinary query gate was not reached.

Read-only source inspection explains the refusal:

- `torment_service/app.py:70`, `_native_rest_route_is_classified`, uses an explicit
  native route allowlist. `/health` and `/agent/query` are listed; the dynamic
  `/agent/<agent>/identity` read is not.
- `app.py:180` checks that classification in native mode and returns HTTP 409
  before calling an unclassified endpoint. Its source-defined detail is
  `native public route is refused before legacy-memory effect`.
- The identity handler at `app.py:925` is therefore not reached in this flow.
  The existing persisted identity has the exact requested workspace and agent
  IDs. There is no evidence here of a mismatched or corrupted identity file.

The two pure classifier functions were evaluated from parsed source on the
observed route: identity GET classified=false, health GET classified=true.
This did not import the application, start another runtime, call an endpoint,
or retry HTTP. The original HTTP response body was not retained by the generated
error handler; the detail above is explicitly source-derived evidence.

This is a separate contract mismatch between Forge's verification endpoint and
the frozen native public route classification. It was not worked around by
removing verification, widening the allowlist, using legacy authority, or
substituting another endpoint. Further correction requires a separate review.

## Shutdown, boundaries and UX findings

Ordinary console Ctrl+C produced `Shutting down`, `Application shutdown complete`
and `Finished server process [66380]`. Answering Y to CMD's subsequent
`Terminate batch job (Y/N)?` prompt ended the wrapper with code 255. That wrapper
code is recorded separately from the completed Uvicorn shutdown. Port 8787 is
absent afterward; no forced process kill was used.

The 29 bounded BGE cache files retained their hashes, sizes and symlink
classifications. No download was observed. Real BGE was used for service
construction; the query embedding path was not reached. Prior S4 real seed
planting evidence remains retained. No inference total is invented.

No production root path or production SQLite connection was requested. Native
inspection was explicitly restricted to the same disposable root and its core.
No ordinary ingest, query, conversational model invocation, Brainvision access,
or Hivemind runtime operation occurred.

| ID | Class | Current finding |
| --- | --- | --- |
| S4C-B1 | BLOCKING | Generated setup requires an identity GET that the native REST boundary refuses with 409. The loader issue is fixed; full setup remains unqualified. |
| S4-F1 | FRICTION | External artifact placement and repository/module working directory remain split across instructions; explicit artifact paths were needed for this run. |
| S4-F2 | FRICTION | Shared copy blocks contain both shell families, and some Windows headings/credential guidance use POSIX comment syntax. |

Current counts: BLOCKING 1, MISLEADING 0, FRICTION 2, COSMETIC 0.
The original S4 loader blocker is resolved and is not counted again. The
generated Markdown includes the corrected loader and the expected step order,
but its integration cannot complete the current native identity check. No UX
corrections beyond the authorized loader change were made.

## Evidence and required return

Key external records under `evidence/s4c`:

- `baseline.json`, `request-immutability.json`, `correction-publication.json`.
- `contracts/contract-checks.json`, `contracts/windows-profile-env.json`,
  and actual CMD transport scripts/stdout/stderr.
- `forge-output.json`, `generated-setup.md`, `generated-chat.py`, `startup.cmd`.
- `before-service.json`, `service.log`, `health.json`, `chat-setup.stderr.log`.
- `native-route-classification.json`, `persisted-identity-declaration.json`.
- `stop-summary.json`, `after-stop.json`, `root-delta.json`, `cache-after.json`.

The original S4 record is preserved exactly. The evidence record does not revise
that history or claim complete product qualification. `FAIL (NOT_RUN)` below
marks an unexecuted downstream gate, not an observed query failure.

```text
TORMENT_FORGE_S4C = BLOCKED
S4_ORIGINAL_STOP = CORRECT
S4_GENESIS_CREATE_PREVIOUSLY_PASSED = YES
S4_GENESIS_REPLAY_PREVIOUSLY_PASSED = YES

WINDOWS_SET_P_LOADER_REMOVED = YES
WINDOWS_COMPLETE_PROFILE_LOADER = PASS
WINDOWS_PROFILE_ENV_JSON_PARSE = PASS
WINDOWS_PROFILE_ENV_EXACT_VALUE_EQUALITY = PASS
WINDOWS_PROFILE_ENV_FIELD_COUNT = 7
FORGE_REQUEST_CHANGED_BY_PROFILE_LOADER_FIX = NO

TORMENT_RUNTIME_SOURCE_CHANGED = NO
GENESIS_SOURCE_CHANGED = NO
FORGE_SOURCE_CHANGED = YES_BOUNDED_WINDOWS_PROFILE_FIX

NORMAL_SERVICE_START = PASS
HEALTH = PASS
PUBLIC_MEMORY_MODE = NATIVE
DEPLOYMENT_RESOLUTION = NATIVE_AGREEMENT

GENERATED_CHAT_SETUP = FAIL (IDENTITY_HTTP_409)
CHAT_SETUP_IS_VERIFY_ONLY = YES
CHAT_SETUP_MUTATING_CALLS = 0
ORDINARY_QUERY = FAIL (NOT_RUN_AFTER_STOP)
ORDINARY_INGEST_REQUESTS = 0
NORMAL_SHUTDOWN = PASS

EXPORTED_MARKDOWN_FLOW = FAIL (NATIVE_IDENTITY_GATE)
BLOCKING_UX_FINDINGS = 1
MISLEADING_UX_FINDINGS = 0
FRICTION_FINDINGS = 2
COSMETIC_FINDINGS = 0

REAL_EMBEDDING_MODEL_INVOKED = YES
SERVICE_BGE_CONSTRUCTION = YES
QUERY_BGE = NO
MODEL_DOWNLOAD_OBSERVED = NO
CONVERSATIONAL_MODEL_INVOKED = NO
PRODUCTION_ROOT_CONTACT = NO
PRODUCTION_SQLITE_CONNECTIONS = NO
SOLO_FORGE_PRODUCT_FLOW_QUALIFIED = NO

NEXT_AUTHORIZATION_BOUNDARY = GPT_REVIEW_OF_FORGE_S4C_AND_UX_FINDINGS
```

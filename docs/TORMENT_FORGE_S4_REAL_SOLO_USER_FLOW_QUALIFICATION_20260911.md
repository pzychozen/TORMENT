# TORMENT Forge S4 — Windows profile-loading blocker

2026-09-11. **TORMENT_FORGE_S4_REAL_SOLO_USER_FLOW = BLOCKED.**

The actual default Solo output successfully created a disposable native root
using the cached real BGE model. Active replay returned the same authority with
no seed embedding dependency or root changes. Qualification stopped at S4 §12:
the generated Windows profile-loading instruction loaded only `{` into
`TORMENT_DEPLOYMENT_PROFILE_JSON`.

I9 correctly exported nine lines of JSON containing the exact seven-field
qualified profile. Windows `set /p` consumed its first line. This is a Forge
instruction mismatch, not a Genesis creation failure. No service was started,
and no alternative loading command, profile rewrite, or runtime repair was tried.

## Accepted baseline and isolated artifacts

HEAD and origin/main at execution:
`5cb3953ce0d28baec38e5907533d65e73be8f3ec`,
`fix: align forge solo setup to native genesis`.

All project commands used Windows CMD with `conda activate torment`.
All 210 unrelated untracked entries remain unchanged. This result record is the
only repository change; source, tests, Genesis and runtime were not modified.

The user explicitly confirmed all six offline conditions using
`LOCAL_HUMAN_OPERATOR_CONFIRMATION_V1`, accepted the prepared preflight, and
authorized continuation at §9. Process/listener checks were supplemental and
were not substituted for that human statement.

Administration directory:

```text
C:\Users\Notandi\AppData\Local\Temp\torment-forge-s4-5c3gxxfn
```

The request, intent, profile and evidence are outside its `root` subdirectory.
The production data root was not accessed. The same prepared root and artifacts
were used throughout; no second installation or alternative domain was tried.

The existing `scripts/forge_solo_fixture.cjs` executed the actual inline Forge
JavaScript. The harmless synthetic Character is `Forge Qualification`, workspace
and agent `forge_qualification`, with the seed:

> Keeps careful records. Values patient reasoning. Remembers shared projects.

The configuration used Character enabled, personal domain/private motif domain,
default personality sliders, ST/BGE small English v1.5, dimension 384, CPU,
compression off, and the default SRG configuration. No conversational model was
invoked. The UI's LLM credential output remained a placeholder.

Step 1's exact UTF-8 JSON bytes were saved as `request.json`. Actual
`NativeGenesisOnboardingRequest.from_payload` validation and round-trip equality
passed. Request file SHA-256:
`eb3c5a3c957c9f217fe158c3a48218ad8caaf3b78f8a15ed1a2756eb885b0bba`.

The only generated-command substitutions were the three artifact names:

| Forge name | Executed external path suffix |
| --- | --- |
| torment_genesis_request.json | request.json |
| torment_genesis_intent.json | intent.json |
| torment_genesis_profile.json | profile.json |

Each was replaced with its quoted absolute administration path. Commands ran
from the repository so `python -m torment_service.native_genesis` resolved
normally. Activation, `HF_HUB_OFFLINE=1` and suppression of Python bytecode files
were execution context; declaration values and command arguments were unchanged.

## Successful Genesis creation and replay

The generated Windows Step 2 environment selected exactly:

```text
TORMENT_EMBED_PROVIDER=st
TORMENT_EMBED_MODEL=BAAI/bge-small-en-v1.5
TORMENT_EMBED_STRICT=1
TORMENT_EMBED_DEVICE=cpu
HF_HUB_OFFLINE=1
```

The actual `python -m torment_service.native_genesis create` command exited 0.
Local model weight loading was observed, and the result was NATIVE_ACTIVE with
selector generation 2. Independent read-only recovery established:

| Fact | Observed value |
| --- | --- |
| Genesis fence | NATIVE_AUTHORITY_WINS |
| Deployment resolution | NATIVE_AGREEMENT |
| Selector | generation 2 / NATIVE_ACTIVE |
| Core | ACTIVE_CORE / NATIVE_ACTIVE |
| Completion family/type | NATIVE_GENESIS / NativeGenesisCompletionWitness |
| Core ID | 90cfef54-6cf3-4be0-956a-3a4066ff4736 |
| Completion digest | fcb133315fda029786b1a791809053137f33480614afae74614d7a7e3f115a3a |
| Seed EIDs | [0, 1, 2] |
| Seed representations | Three READY / USABLE, float32, dimension 384 |
| Exported profile | Exactly seven fields; equal to activated completion |

Read-only SQLite inspection was restricted to the disposable core. Each
representation named by the completed seed witness was present and READY/USABLE.
Representation IDs, source revisions, payload hashes and the declared ST/BGE
lane are preserved in `after-create.json`.

The same generated create command ran a second time and exited 0, returning the
identical result. CPython's built-in import timing was enabled for this replay
only; no monkeypatch, alternate Genesis entry point, or model substitute was
used. The complete fresh-process import record contained no sentence_transformers,
torch or transformers import. Together with the frozen active-replay dependency
branch, this establishes zero seed embedding calls during replay.

All 19 root files matched byte-for-byte after creation, after replay, and after
the stop. Completion, selector, profile, seed witness, native counts and
representation payload hashes also matched. Active replay performed no Genesis
phase mutation or seed replant.

## First mismatch: generated Windows profile loading

The exact generated command, with only the permitted path substitution, was:

```cmd
set "TORMENT_DEPLOYMENT_PROFILE_JSON="
set /p TORMENT_DEPLOYMENT_PROFILE_JSON=<"C:\Users\Notandi\AppData\Local\Temp\torment-forge-s4-5c3gxxfn\profile.json"
```

The generated environment was executed in CMD before starting the service. An
external environment observer recorded the resulting value and compared it with
the exported profile. That comparison failed on its first run:

```text
EXPORTED_PROFILE_BYTES = 391
EXPORTED_PROFILE_LINES = 9
EXPORTED_PROFILE_FIELDS = 7
OBSERVED_ENVIRONMENT_VALUE = {
OBSERVED_ENVIRONMENT_LENGTH = 1
```

The profile file itself is valid and exactly matches the activated completion.
Its SHA-256 is
`177fae72b163521a3be69ef496f060749907ea20a163dc19d61a03e69f3887ed`.

The producer uses `owner_bytes`, which deliberately writes indented JSON with
native text newlines (`torment_service/external_owner_json.py`). The Forge emits
a single-line reader. The actual Markdown export contains that same command,
so the exported product flow is also blocked.

S4 stopped at this mismatch. No corrected loader was executed, and neither
`profile.json` nor any generated declaration was changed. The proposed next
correction is confined to Forge's Windows instructions: load the entire exported
JSON object into the environment while retaining the seven-field profile's
meaning. The I9 exporter and runtime contracts should remain unchanged. This
record does not implement or qualify a replacement command.

## Usability findings

| ID | Class | Finding |
| --- | --- | --- |
| S4-B1 | BLOCKING | Step 3 uses `set /p` for a multiline I9 profile, producing `{` instead of usable JSON. |
| S4-F1 | FRICTION | Artifact placement and working directory are split across instructions: Step 0 uses repository-relative requirements, while Step 2 refers to an external artifact directory and an environment where TORMENT is installed. Explicit absolute artifact paths allowed this run to proceed, but a human must reconcile those locations. |
| S4-F2 | FRICTION | Each create/startup copy block combines both shell families. The reader must select the appropriate part; the Windows startup heading and trailing credential guidance also use POSIX `#` comments. |

Counts: BLOCKING 1, MISLEADING 0, FRICTION 2, COSMETIC 0.
S4-B1 is counted once. S4-F1 and S4-F2 did not prevent this execution.

The actual Markdown has the required dependency, request, create, startup,
prompt and integration headings. It names all three external artifacts and
states the offline conditions. It contains no retired Solo workspace/agent
creation routes. Its Step 3 command prevents complete qualification.

## Unexecuted gates and model accounting

Normal service startup, health, generated chat `setup()`, ordinary query and
normal service shutdown were not executed. No service harness or direct ASGI
construction was used. Static inspection of the emitted `setup()` found exactly
two `t_get` calls and no `t_post` call; this is not a substitute for the required
real-service setup test.

The sole behavioral failure is Windows profile loading. Below, `FAIL (NOT_RUN)`
means the downstream gate is unqualified because execution stopped; it does not
claim a runtime behavioral failure. No health-derived public memory mode was
observed. Final durable deployment resolution was independently verified.

```text
GENESIS_SEED_BGE = YES
SERVICE_BGE_CONSTRUCTION = NO
QUERY_BGE = NO
MODEL_DOWNLOAD_OBSERVED = NO
CONVERSATIONAL_MODEL_CALLS = 0
ORDINARY_QUERY_REQUESTS = 0
ORDINARY_INGEST_REQUESTS = 0
```

All 29 bounded BGE cache files retained their hashes, sizes and symlink
classifications. HF Hub offline mode remained enabled. No exact seed inference
total is asserted. Port 8787 was absent after the stop; no service needed
shutdown. No ordinary Windows access-violation diagnostic was observed.

## Evidence

External evidence lives under the administration directory's `evidence` folder:

- `baseline.json`, `human-confirmation.json`, `fixture-input.json`,
  `forge-output.json`, `generated-setup.md`, `generated-chat.py`.
- `create.cmd`, `startup.cmd`, `path-substitutions.json`.
- `genesis-create-execution.json`, `genesis-create-result.json`,
  `genesis-create.stdout.log`, `genesis-create.stderr.log`.
- `after-create.json`, `genesis-replay-result.json`,
  `genesis-replay.stdout.log`, `genesis-replay.imports.log`, `after-replay.json`.
- `check-startup-env.cmd`, `check_startup_env.py`, `startup-env-observed.json`,
  `profile-load-mismatch.json`.
- `final-after-stop.json`, `cache-before.json`, `cache-after-stop.json`,
  `listener-after-stop.json`, `stop-summary.json`.

The existing S1/S2 and Solo Alignment checker passed during preflight. Source
has remained identical to that checked baseline. No browser credential input or
storage was used; credential templates remain placeholder-only and the known
fingerprinting signatures are absent.

## Required return

```text
TORMENT_FORGE_S4_REAL_SOLO_USER_FLOW = BLOCKED
S3_ACCEPTED = YES
ACTUAL_FORGE_JS_USED = YES
ACTUAL_FORGE_REQUEST_USED = YES
FORGE_REQUEST_I9_VALIDATION = PASS

REAL_BGE_AUTHORIZED = YES
REAL_BGE_MODEL = BAAI/bge-small-en-v1.5
REAL_EMBEDDING_MODEL_INVOKED = YES
MODEL_DOWNLOAD_OBSERVED = NO
CONVERSATIONAL_MODEL_INVOKED = NO

GENERATED_WINDOWS_GENESIS_COMMAND = PASS
GENESIS_CREATE = PASS
GENESIS_ACTIVE_REPLAY = PASS
GENESIS_ACTIVE_REPLAY_SEED_EMBEDDING_CALLS = 0
QUALIFIED_PROFILE_EXPORTED = PASS
QUALIFIED_PROFILE_EXACT = PASS

GENERATED_WINDOWS_STARTUP_ENV = FAIL
NORMAL_SERVICE_START = FAIL (NOT_RUN)
HEALTH = FAIL (NOT_RUN)
PUBLIC_MEMORY_MODE = OTHER (NOT_OBSERVED)
FINAL_DEPLOYMENT_RESOLUTION = NATIVE_AGREEMENT

GENERATED_CHAT_SETUP = FAIL (NOT_RUN)
CHAT_SETUP_IS_VERIFY_ONLY = YES (STATIC_INSPECTION)
CHAT_SETUP_MUTATING_CALLS = 0
ORDINARY_QUERY = FAIL (NOT_RUN)
ORDINARY_INGEST_REQUESTS = 0
NORMAL_SHUTDOWN = FAIL (NOT_RUN; NO_SERVICE_STARTED)

GENESIS_PHASE_REPLAY = NO
CHARACTER_SEED_REPLANTED = NO
EXPORTED_MARKDOWN_FLOW = FAIL
BLOCKING_UX_FINDINGS = 1
MISLEADING_UX_FINDINGS = 0
FRICTION_FINDINGS = 2
COSMETIC_FINDINGS = 0
S1_SECURITY_REGRESSION = PASS
S2_PROVIDER_SECRET_REGRESSION = PASS

PRODUCTION_ROOT_CONTACT = NO
PRODUCTION_SQLITE_CONNECTIONS = NO
PRODUCTION_RUNTIME_STARTED = NO
DISPOSABLE_PRODUCTION_SHAPED_SERVICE_STARTED = NO
FORGE_SOURCE_CHANGED = NO
TORMENT_RUNTIME_SOURCE_CHANGED = NO
BRAINVISION_ACCESSED = NO
HIVEMIND_RUNTIME_TOUCHED = NO
SOLO_FORGE_PRODUCT_FLOW_QUALIFIED = NO

NEXT_AUTHORIZATION_BOUNDARY = GPT_REVIEW_OF_FORGE_S4_AND_UX_FINDINGS
```

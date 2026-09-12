# Forge S4D — Native Solo product flow qualified

2026-09-12. **TORMENT_FORGE_S4D = COMPLETE.**

The Forge Solo generator no longer depends on the unsupported native identity
REST endpoint. The actual regenerated chat script completed health-only setup,
and the same S4 native root served one ordinary query with HTTP 200, all three
seed memories, and the expected Character context. No runtime or Genesis source
changed. No Genesis command or ordinary ingest was executed during S4D.

The correction was committed and pushed before continuation:
`050a7461da27e9fb92007a382cff286443535ea7`,
`fix: remove unsupported native identity check from forge solo`.
This record is the sole file in the completion commit,
`complete forge s4 native solo qualification`.

The authoritative starting HEAD, origin/main and live remote main all matched
`3fc79413f5eaf81f8ec5c4329710d74779634630`. Tracked state began clean.
All 210 unrelated untracked entries were preserved using the same collapsed
directory inventory. Both earlier S4 and S4C reports remain byte-identical.

The preserved chronology is:

1. S4 real BGE Genesis creation passed, followed by successful active replay.
2. S4 stopped at the incomplete Windows multiline-profile loader.
3. S4C fixed and qualified the complete-profile loader in real Windows CMD.
4. S4C startup and health passed, but the generated identity GET received the
   correct native REST refusal. S4C stopped before an ordinary query.
5. GPT rejected runtime route widening and authorized removing the unsupported
   dependency from Forge Solo.
6. S4D removed that dependency, qualified and published the correction, then
   resumed the same native root. Setup, ordinary query and product flow passed.

Only three implementation files changed in the correction commit:

- `start/torment_character_creator.html`: Solo setup now issues only GET /health;
  the identity helper, slash command, help entry and optional curl check were
  removed. The generated docstring explains that setup checks service
  reachability, while the first ordinary query exercises workspace/agent native
  authority. Health does not establish agent existence or membership.
- `scripts/check_forge_genesis.py`: execute the emitted setup with fake GETs and
  require exactly `[('/health',)]`; retain refusal testing for unreachable
  health and reject setup POSTs and identity calls. Check the emitted Markdown
  as well as output blocks, helper removal, retained slash commands and the
  legitimate query response field `identity_state`.
- `scripts/check_forge_output.py`: add Solo-only identity-route/slash-command
  prohibitions and retain the historical Hivemind identity endpoint requirement.

The Hivemind generator and all subsequent shared source were compared with the
baseline and remained identical. Source preceding the Solo generator was also
unchanged. The emitted `t_get`, `t_post`, `t_query` and `t_ingest` function ASTs
were identical to the prior S4C output. `/status`, `/debug`, `/memories <query>`
and `/clear` remain available. No replacement identity route, `/character`
command, setup query, automatic creation or Genesis subprocess was added.

The native REST allowlist, public runtime, identity owner, Genesis, deployment
authority, native owner and SQLite implementation were untouched. No
implementation changes followed the correction commit during live continuation.
Every project shell command used Windows CMD with `conda activate torment`.

Focused qualification passed without real model execution:

- `node --check` on the extracted actual Forge script.
- `python -B scripts/check_forge_output.py`: whole-file S1 signatures, S2 provider
  secret rules, Solo and all three Hivemind sections passed.
- `python -B scripts/check_forge_genesis.py`: 14 valid generated variants,
  seven required request refusals, and the Windows profile-loader case passed.
  Each valid emitted Python script was compiled and its setup was executed
  independently without imports, network, SDK calls or conversational execution.
- Actual Windows CMD loaded the retained multiline I9 profile, and a child
  Python process verified JSON parsing, exact value equality and seven fields.
  Interactive `%P` remains in Forge output; only batch evidence uses `%%P`.
- Three injected identity-route/command examples tripped the new Solo guards.
  Ordinary identity prose and `identity_state` remained allowed. Hivemind was
  excluded from the new guards and continued to pass its existing requirements.
- Exact S4 fixture regeneration before and after the correction commit produced
  byte-identical request JSON. Only `out-loop-curl` and `out-loop-python` differed
  from S4C output; Markdown reflects those two changes. The environment and
  Genesis command blocks remained identical.
- The actual postcommit generated chat script also passed `py_compile`.

The original artifacts remain unchanged:

| Artifact | SHA-256 |
| --- | --- |
| request.json | eb3c5a3c957c9f217fe158c3a48218ad8caaf3b78f8a15ed1a2756eb885b0bba |
| intent.json | 1adac316dc60f1ee0d866e4f85faed64d6e475d46dd095a46b663978d7b9c059 |
| profile.json | 177fae72b163521a3be69ef496f060749907ea20a163dc19d61a03e69f3887ed |

The administration directory remains
`C:\Users\Notandi\AppData\Local\Temp\torment-forge-s4-5c3gxxfn`.
The authorized root remains its existing `root` directory. New evidence resides
under `evidence/s4d`; neither older evidence directory was overwritten. No new
native root or local-human offline confirmation was needed or created.

After correction publication, the actual Forge generator and Markdown exporter
were executed again using the retained S4 fixture input. The captured CMD
startup used the generated environment with only the existing external profile
filename substituted and `%P` adapted to `%%P` for batch execution. It set the
exact disposable root and complete exported profile, ST / BGE / CPU, strict
embedding, and the generated Character/compression/SRG defaults. It cleared
TORMENT_PROFILE and TORMENT_ADMISSION_DESCRIPTOR_PATH. HF_HUB_OFFLINE=1 was set;
Python bytecode writes were suppressed. The final command was normal
`python -m torment_service`, without a harness, direct ASGI construction,
alternate factory or runtime patch.

Service PID **52536** loaded the existing local model weights and completed
normal Uvicorn startup. The first health gate returned HTTP 200 and:

```text
public_memory_mode = NATIVE
embedder.provider = st
embedder.model = BAAI/bge-small-en-v1.5
embedder.dim = 384
embedder_degraded = false
requested_embedder.strict = true
profile.applied_count = 0
```

Independent read-only recovery of the authorized root established
NATIVE_AGREEMENT before and after the run. It verified the exact seven-field
completion profile, NATIVE_AUTHORITY_WINS fence, selector NATIVE_ACTIVE at
generation 2, and ACTIVE_CORE / NATIVE_ACTIVE core state. Completion remained
NativeGenesisCompletionWitness, family NATIVE_GENESIS, digest
`fcb133315fda029786b1a791809053137f33480614afae74614d7a7e3f115a3a`.

The actual regenerated chat script was loaded through importlib, without running
its main loop, and only `setup()` was invoked. The service log delta proves one
GET /health with HTTP 200. There were no setup POSTs or identity calls. The normal
Anthropic SDK import did not construct a conversational client or invoke a model.

The one ordinary POST /agent/query used workspace and agent
`forge_qualification`, taken from the generated request, with top_k=8 and:

> How do you keep careful records and reason patiently about shared projects?

No embedding was supplied. The response returned HTTP 200 in approximately
2.09 seconds and identified the ST / BAAI/bge-small-en-v1.5 / 384 embedding lane.
It returned seed EIDs 2, 0, 1 with summaries “Remembers shared projects.”,
“Keeps careful records.” and “Values patient reasoning.” The observed order is
recorded, not required. Character context contained the exact combined seed
preamble, seed_id `forge_qualification_v1`, character name `Forge Qualification`,
three core-identity memories and stable drift. This proves the Forge-onboarded
agent can use the ordinary native public query operation with real BGE.

The complete service access log contains exactly:

| Origin | Request | Status |
| --- | --- | --- |
| Health gate | GET /health | 200 |
| Actual generated setup | GET /health | 200 |
| Ordinary query gate | POST /agent/query | 200 |

No ordinary ingest, retry, alternative domain or endpoint substitution occurred.
Console Ctrl+C produced Uvicorn's completed application shutdown and finished
server-process messages. Answering Y to the subsequent CMD batch termination
prompt closed the wrapper with exit code **255**. That wrapper code is recorded
separately from the clean Uvicorn shutdown. PID 52536 and the port 8787 listener
were both absent afterward. No forced process termination was used.

Before/after comparison found all **19 root files byte-identical**. The complete
native evidence record also matched the retained S4C after-stop record. Counts
remained six objects, eight object revisions, three representations, 19 operations
and 16 semantic transitions. Seed EIDs remained `[0, 1, 2]`; all three seed
representations remained READY, USABLE, dimension 384, float32, with unchanged
identifiers, revisions and payload hashes. There was no persisted read/runtime
side effect, new memory, EID, representation, Genesis phase, seed planting or
selector generation.

All **29 bounded BGE cache files** retained their sizes, hashes and symlink
classifications. HF_HUB_OFFLINE=1 remained in force and no download was observed.
Real BGE was used during normal service construction and ordinary query. No
conversational model was invoked. Inspection was restricted to source, external
evidence, the named model cache and the authorized disposable root; no production
root access or production SQLite connection was requested.

The regenerated Markdown no longer teaches an unsupported Solo identity route.
Its order remains Genesis request, Genesis creation/profile export, profile
loading, server startup, health, and chat/query integration. Each shell's loader,
server and health sequence was checked separately. The two known polish findings
remain unchanged:

| ID | Class | Finding |
| --- | --- | --- |
| S4-F1 | FRICTION | Artifact placement and the repository/module working directory remain split; explicit external artifact paths were needed. |
| S4-F2 | FRICTION | Shared copy blocks contain both shell families, and some Windows-facing headings/credential guidance use POSIX comments. |

Current counts are BLOCKING 0, MISLEADING 0, FRICTION 2, COSMETIC 0. The loader
and identity dependency blockers are resolved. No optional UX polish was made.

External evidence under `evidence/s4d` includes:

- `baseline.json`, `untracked-before.bin`, `correction-checks.json`,
  `correction-publication.json`, `check-forge-output.log`.
- `contracts/contract-checks.json`, actual Windows CMD transport evidence,
  all emitted variants, requests and compiled scripts.
- `precommit-forge-output.json`, `forge-output.json`, `generated-setup.md`,
  `generated-chat.py`, `startup.cmd`.
- `before-service.json`, `health.json`, `service.log`, `service-before-setup.log`,
  `setup-service-delta.log`, `setup-result.json`, and setup stdout/stderr logs.
- `query-request.json`, `query-response.json`, raw HTTP response bytes.
- `after-stop.json`, `root-delta.json`, `stop-summary.json`, listener and process
  absence records, `cache-before.json`, `cache-after.json`.
- `final-scope-checks.json`, `evidence-manifest.json`, and final publication
  verification in `final-publication.json`.

The required return is:

```text
TORMENT_FORGE_S4D = COMPLETE

S4_ORIGINAL_GENESIS = PASS
S4C_WINDOWS_PROFILE_FIX = PASS
S4C_IDENTITY_STOP = CORRECT

NATIVE_IDENTITY_ROUTE_WIDENED = NO
TORMENT_RUNTIME_SOURCE_CHANGED = NO
GENESIS_SOURCE_CHANGED = NO

SOLO_SETUP_IDENTITY_GET_REMOVED = YES
SOLO_CURL_IDENTITY_GET_REMOVED = YES
SOLO_IDENTITY_SLASH_COMMAND_REMOVED = YES
SOLO_T_IDENTITY_HELPER_REMOVED = YES

HIVEMIND_GENERATOR_SEMANTICS_CHANGED = NO
FORGE_GENESIS_REQUEST_CHANGED = NO
WINDOWS_COMPLETE_PROFILE_LOADER = PASS

GENERATED_CHAT_SETUP = PASS
SETUP_HTTP_REQUEST_COUNT = 1
SETUP_HTTP_REQUEST = GET_/health
SETUP_MUTATING_CALLS = 0
SETUP_IDENTITY_ROUTE_CALLS = 0

NORMAL_SERVICE_START = PASS
HEALTH = PASS
PUBLIC_MEMORY_MODE = NATIVE
DEPLOYMENT_RESOLUTION = NATIVE_AGREEMENT

ORDINARY_QUERY = PASS
FORGE_ONBOARDED_AGENT_NATIVE_QUERY_USABLE = YES
ORDINARY_INGEST_REQUESTS = 0
NORMAL_SHUTDOWN = PASS

GENESIS_PHASE_REPLAY = NO
CHARACTER_SEED_REPLANTED = NO
ORDINARY_MEMORY_CREATED = NO

EXPORTED_MARKDOWN_FLOW = PASS
BLOCKING_UX_FINDINGS = 0
MISLEADING_UX_FINDINGS = 0
FRICTION_FINDINGS = 2
COSMETIC_FINDINGS = 0

REAL_EMBEDDING_MODEL_INVOKED = YES
QUERY_BGE = YES
MODEL_DOWNLOAD_OBSERVED = NO
CONVERSATIONAL_MODEL_INVOKED = NO

S1_SECURITY_REGRESSION = PASS
S2_PROVIDER_SECRET_REGRESSION = PASS

PRODUCTION_ROOT_CONTACT = NO
PRODUCTION_SQLITE_CONNECTIONS = NO
SOLO_FORGE_PRODUCT_FLOW_QUALIFIED = YES

NEXT_AUTHORIZATION_BOUNDARY = GPT_REVIEW_OF_FORGE_S4D_THEN_OPTIONAL_UX_POLISH
```

Additional frozen checks: WINDOWS_SET_P_LOADER_REMOVED=YES;
WINDOWS_PROFILE_ENV_EXACT_VALUE_EQUALITY=PASS;
FORGE_FINGERPRINTING_SIGNATURES=ABSENT;
BROWSER_PROVIDER_SECRET_INPUTS=ABSENT;
PROVIDER_ENV_TEMPLATES=PLACEHOLDER_ONLY. S4D stops at the stated review boundary.

# TORMENT Native Genesis I10 — fresh-install service qualification blocker

2026-09-11 UTC. **NATIVE_GENESIS_I10 = BLOCKED.**

The first ordinary private ingest succeeded, returned EID 3, and persisted its
native object and READY BGE representation. The same request also caused the
existing post-write path to create a derived identity anchor at private EID 4.
The first durable inspection therefore found two new memory objects and five
READY representations, conflicting with I10 §29's one-new-memory requirement
and §43's expected four-representation closure.

Qualification stopped at this first observed mismatch. No read-after-write
request, post-write Genesis CLI status, service restart, or alternate request
was attempted. The service was shut down by ordinary console Ctrl+C, exited 0,
and left no service process or port-8787 listener. No runtime repair, policy
change, embedding substitution, or source/test modification was made.

This is a qualification-contract mismatch requiring GPT review. The observed
extra object has explicit derived-memory provenance; this record does not
classify it as a duplicate HTTP ingest or prescribe changing anchor semantics.

## Frozen baseline and operator boundary

- Starting HEAD and origin/main:
  `2b61e39c105aa953a3df459e8c5370b6aecd8649`.
- Starting commit: `native-genesis-i9-offline-operator-utility`.
- Tracked tree clean; all 210 unrelated untracked entries matched the I9
  inventory and remained unchanged through evidence freeze.
- Windows CMD with `conda activate torment` was used for project commands.
  Python: `C:\Users\Notandi\miniconda3\envs\torment\python.exe`.
- The local human operator explicitly confirmed all six offline conditions via
  `LOCAL_HUMAN_OPERATOR_CONFIRMATION_V1`. Independent process review found no
  TORMENT writer; port 8787 was absent at preflight and immediately before create.
- The production data root was not read, opened, fingerprinted, or started.

Administration directory, outside both repository and production root:

`C:\Users\Notandi\AppData\Local\Temp\torment-native-genesis-i10-4d5b09f_`

The initially absent disposable root is its `root\` child. Request, I9-generated
intent, exported profile, and `evidence\` are siblings outside that root.

## Request, native authority, and immutable closure

The real onboarding request contract validated the enabled synthetic Character:
workspace `genesis_i10_workspace`, agent `genesis_i10_agent`, shared domains
`research` and `personal`, and private motif domain `research`.
I1/I9 Character numeric settings and initial overlay values were retained.
The three harmless seed concepts were supplied as one line because the frozen
text contract excludes control characters. No personal memory was used.

The lane was ST / `BAAI/bge-small-en-v1.5` / 384, COMPAT_EMBEDDING, generation 1,
compat-embedding-v1, RAW_VECTOR, float32. Compression and deep memory were false.

| Fact | Exact value |
| --- | --- |
| Request digest | `30f1a5b17ead907ed6526a8cb2b3a5a160be58b31ac7c26ff30b0f3e7a30a236` |
| I9-generated intent digest | `218ed276950d10bc3d057f4ca314ce2a6328c00b890b0d2cb0549f0de84657d3` |
| Core ID | `a93c39cb-0977-48e1-84c2-6836f4fa174d` |
| Core relative path | `genesis-a93c39cb-0977-48e1-84c2-6836f4fa174d.db` |
| Completion digest | `0f321511c8e9cb58ceaa76c3e2a0abd503725d3bb85e9483ad5f45a5788966b6` |
| Qualified profile digest | `edfe4080f884018bd3fd315f6ef5e586cc89325b406c80c1b513e6cbfbd19923` |
| Character definition digest | `bbf9d3e4dcaed19914eb24f27513f308ec83322256e8189ab2c7d67b04ed559a` |
| Completed native seed result digest | `05f95782ea31234d0b00cc2c3b35eada489445c6e733a791c3bc6ba47dcdb790` |
| Seed motif | `motif_research_0001` |
| Private alias namespace | `27629d2d-a706-4f98-b0e1-885ba3c2a533` |
| Private semantic scope | `b3977bfc-470a-4192-a5ff-c08de6511aa2` |

Read-only recovery passed before service, after startup, after the write, and
after shutdown. Each check established NATIVE_AUTHORITY_WINS, NATIVE_AGREEMENT,
selector generation 2 / NATIVE_ACTIVE, ACTIVE_CORE / NATIVE_ACTIVE, and an actual
`NativeGenesisCompletionWitness`. Complete completion payload, profile, selector,
initial memberships, and Character seed-completion payload remained equal to the
activation baseline. Exported `profile.json` has exactly seven fields and equals
the completion's qualified profile. The service received its exact contents,
including formatting, without reconstruction.

Seed EIDs 0, 1, and 2 remained current with their original representation IDs,
three READY/USABLE 384-dimensional representations, and exact stable native and
external Character definition/linkage. Full I7 recovery verified profile,
membership, catalog, native completed seed result, and stable external owners.
Mutable runtime state was not required to remain byte-identical.

## Executed sequence and first failure

| Gate | Result and evidence |
| --- | --- |
| Pre-create actual I9 status | NOT_STARTED; root still absent; zero SQLite connections and no model modules loaded |
| Actual I9 create, PID 53860 | PASS; real cached BGE; NATIVE_ACTIVE, selector generation 2 |
| Seed closure and profile export | PASS; EIDs [0,1,2], three READY representations, exact seven-field profile |
| Identical active create replay, PID 33636 | PASS; root snapshot unchanged, no model modules loaded, zero seed embedding calls |
| Normal service start, PID 37472 | PASS; actual `python -m torment_service`, no admission descriptor |
| GET /health | HTTP 200; NATIVE, st/BGE, 384, not degraded |
| Independent startup authority | PASS; same Genesis core, completion, profile, generation 2 |
| First POST /agent/query | HTTP 200; valid native result, seed hits [0,1,2], zero authority-guard rejections |
| Exactly one POST /agent/ingest | HTTP 200; stored=true, reinforced=false, eid=3, result_code=stored, fast_allowed |
| Durable write inspection, I10 §29 | **FAIL: two new private EID aliases, two new memory objects, two new representations** |
| Normal shutdown for stop cleanup | PASS; Ctrl+C, application shutdown complete, process exit 0, no process/listener |
| Post-stop read-only evidence freeze | PASS; immutable Genesis authority and seed closure retained; SQLite integrity and foreign keys clean |
| Read-after-write, post-write CLI status, restart and subsequent gates | **NOT RUN after first mismatch; unqualified, not behavioral failures** |

The access log contains exactly one health request, one query, and one ingest.
No embedding, summary, native object ID, EID, or representation ID was supplied
by the HTTP client. The ingest used PRIVATE/research, logical step 1, one unique
synthetic marker, and one unique Idempotency-Key. Full harmless request/response
artifacts are retained outside the repository.

Durable object evidence:

| EID | Kind/provenance | Native object | Current revision | READY representation |
| --- | --- | --- | --- | --- |
| 3 | episode; user_input / direct_ingest | `977ddada-23d6-41a4-96da-8bb42d4daf27` | `708a7a92-adfd-4c99-aac8-c28851f088fe` (ordinal 2) | `b5266aa3-9bf4-4a7e-856c-58e97adcde74` |
| 4 | identity_anchor; derived / system / legacy_derived | `affd88e4-9e39-4455-aee3-7d207e391362` | `df176da7-7fba-41cf-9c79-35b8099603fd` (ordinal 1) | `884558b3-3b2c-4fa4-ac8c-39887c4d2d71` |

EID 4 records `anchor_origin=derived`, `anchor_source=motif_cluster`,
`anchor_member_count=4`, and `source_member_eids=[0,1,2,3]`. Its motif is
`motif_research_0001`. Both new objects belong to the exact private semantic
scope and alias namespace above, have the expected workspace/agent payload
authority, and have no shared/cross-scope aliases. EID 3's ordinary write and
representation durability passed. The aggregate one-new-memory cardinality
did not pass.

The unchanged source explains the additional effect:
`torment_service/substrate/native_post_write_runtime.py:683` and `:1148`
dispatch identity-anchor emission from existing post-write consumers.
`torment_service/substrate/native_derived_memory_runtime.py:136` checks motif
members and thresholds; lines 178–215 derive an anchor summary, obtain an
embedding, bind a child operation key, and commit native derived memory.
This source review is consistent with the persisted anchor evidence; it is not
a new traced call-count claim. Existing compatibility/provenance labels such as
LEGACY_CORE_NODE and LEGACY_DERIVED_MEMORY do not indicate public legacy fallback
or migration. Migration-admission/source tables remain empty.

## Real model accounting

Every authorized model process used:

```text
TORMENT_EMBED_PROVIDER=st
TORMENT_EMBED_MODEL=BAAI/bge-small-en-v1.5
TORMENT_EMBED_DEVICE=cpu
TORMENT_EMBED_STRICT=1
HF_HUB_OFFLINE=1
```

The existing query-timing diagnostic was enabled only for the service.
No model-count profiler or production-function monkeypatch was introduced.

| Activity | Accounting |
| --- | --- |
| Genesis model construction | OBSERVED; local weight-load log, ST/Torch imports, normal constructor dimension probe not independently counted |
| Genesis Character embedding | OBSERVED / NOT_EXACTLY_COUNTED; three committed real-BGE seed representations |
| Active CLI replay | 0 seed embedding calls; ST/Torch absent from completed-process module inventory |
| First service construction | OBSERVED; local weight-load log and st/BGE/384 health evidence; constructor probe not independently counted |
| Initial ordinary query | Existing diagnostic measured 3 bge.encode calls, 0 errors: agent preparation, query embedding, and vector text-encode entry |
| Ordinary ingest and derived anchor | OBSERVED / NOT_EXACTLY_COUNTED; EIDs 3 and 4 have READY real-BGE representations and st/model/384 metadata |
| Read-after-write query | NOT RUN |
| Restart model construction | NOT RUN |
| Post-restart marker and seed queries | NOT RUN |
| Conversational models | **0 calls; not invoked** |

There is no invented overall inference count. Hash and deterministic test
embedders were not substituted. No OpenAI, Anthropic, or Ollama model module was
loaded by the audited qualification processes, and no external socket connection
was observed. The sole service-initiated socket connection was the local asyncio
loopback pair, not a model/API connection. Deterministic internal advisory and
anchor-summary logic ran as existing TORMENT behavior.

The bounded cache
`C:\Users\Notandi\.cache\huggingface\hub\models--BAAI--bge-small-en-v1.5`
was fingerprinted before any loading and after shutdown: all 29 entries'
content hashes, sizes and symlink classifications compare equal. No new model
content or download was observed. No unrelated user cache was crawled.

## Mutation and path audit

External `sitecustomize.py` installed a passive Python audit hook for file-open,
directory/mutation, SQLite-connect, subprocess, and socket events. It logged
paths/events only, without replacing production functions, injecting runtime
objects, changing guards, or selecting another backend. The launcher supplied
the exact process environment and executed the normal module; the evidence
client used ordinary HTTP. Read-only inspectors did not construct a Fabric or
production native owner.

Across CLI, service, and independent native inspections, all **6,348 SQLite
connections** resolved either to `:memory:` or these paths beneath the
disposable root:

- `substrate/cores/genesis-a93c39cb-0977-48e1-84c2-6836f4fa174d.db`
- `substrate/deployment/selector.sqlite`
- `substrate/deployment/.selector-init-9eda84d6dc244525ae1feb3c3a1bf17a.sqlite`
- `substrate/deployment/genesis-core-bootstrap/core.db`

No production SQLite connection or production-root path contact was recorded.
Production was never started. No migration, historical-v1/root-v2 mutation,
Forge change, BrainVision access, or Hivemind operation was performed.

Genesis produced its expected core, selector/era marker, administrative record,
publication locks, bootstrap intent and external workspace/identity/seed files.
The existing Windows selector-initialization alias and sidecars were retained
without repair. Normal runtime changed the disposable native core and created
seven files: anchors, roles, symbol state, and four trajectory-v2 artifacts
(including the normally sealed chunk). Final root inventory contains 26 files.
Complete before/after file hashes and table counts are retained.

The core effects include the intended EID 3 write, native post-write metadata
and motif/relationship updates, and the additional derived EID 4 anchor. The
extra anchor is fully attributable to ordinary runtime behavior but is outside
I10's stated exact-memory-count expectation. Thus the strict aggregate
`AUTHORIZED_DURABLE_MUTATION_ONLY` qualification is FAIL for this cardinality
conflict; confinement to the disposable root passed.

Outside administration/root artifacts, model/runtime audit observed NUL opens,
two temporary-file probes that were removed, and mkdir attempts for an already
existing `%TEMP%\torchinductor_Notandi` directory. That directory's creation and
modification metadata predate this run and remained unchanged. These effects
introduced no durable model content. No unexplained external durable change
was found.

## Evidence and repository publication

Key external evidence files under `evidence\`:

- `operator-confirmation.json`, `baseline.json`, preflight process/port records,
  `request-validation.json`, `bge-cache-before.json`, `bge-cache-after.json`.
- `01-status-before.json`, `02-create.json`, `04-active-replay.json`.
- `03-pre-service-native.json`, `06-started-native.json`,
  `10-post-write-native.json`, `13-frozen-final-native.json`.
- `service-1-environment.json`, `service-1-process.json`, `service-1.log`,
  `service-1-exit.json`, `11-stop-shutdown.json`.
- `05-health-1.json`, `07-initial-query.json`, `write-request.json`,
  `09-ordinary-write.json`, `12-memory-findings.json`.
- All `*-audit.jsonl` files, `query-timing-summary.json`,
  `14-frozen-evidence-summary.json`, and
  `15-benign-runtime-temporary-effects.json`.
- `evidence-manifest.json` and final `publication.json` bind the evidence
  and documentation-only commit/push result.

Only this Markdown result record is authorized for commit:
`record-native-genesis-i10-qualification-blocker`.
Publication checks record the exact final HEAD, origin/main and remote HEAD,
the I9 parent, the single documentation-file diff, clean tracked state,
`git diff --check`, and the unchanged 210-entry untracked inventory.
Source and tests remain exactly at I9. No tests were added or run: I10 qualified
the actual operator command and normal service until the mandatory stop.

```text
SERVICE_LEVEL_FRESH_INSTALL_QUALIFIED = NO
LEGACY_FRESH_INSTALL_COMPATIBILITY_REMOVAL_AUTHORIZED = NO
NEXT_AUTHORIZATION_BOUNDARY = GPT_REVIEW_OF_NATIVE_GENESIS_I10
```

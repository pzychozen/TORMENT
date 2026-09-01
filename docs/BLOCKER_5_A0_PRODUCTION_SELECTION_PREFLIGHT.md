# Blocker-5 A0 — production selection / cutover preflight

## Verdict and scope

```text
BLOCKER_5_PREFLIGHT = READY

CURRENT_PUBLIC_BACKEND = LEGACY
QUALIFIED_PRODUCTION_PROFILE = compression/deep disabled
PRODUCTION_ENVIRONMENT_CONVERGENCE_REQUIRED = YES

CURRENT_NATIVE_CAPABILITY = STAGING / qualification-only
ACTIVE_CORE_ROLE_IMPLEMENTED = NO
DURABLE_DEPLOYMENT_SELECTOR_IMPLEMENTED = NO
CUTOVER_FENCE_IMPLEMENTED = NO

NATIVE_ACTIVE_RUNTIME_LEGACY_FALLBACK = NONE
AUTOMATIC_POST_NATIVE_ROLLBACK_TO_LEGACY = NO
ONE_DEPLOYMENT_AUTHORITY_PER_DATA_ROOT = REQUIRED

KERNEL_FILES_CHANGED = 0
PRODUCTION_SELECTOR_ADDED = NO
NATIVE_ACTIVE = NO
DUAL_WRITE = NO
DUAL_READ = NO
CUTOVER_OPENED = NO
```

This is archaeology and frozen deployment-selection design only. It implements
no selector, activation, cutover, rollback, environment upgrade, dual mode, or
live native service. The semantic closures remain [7G5E4D shared
write/lifecycle](7G5E4D_FINAL_CLOSURE.md) and [7G5E4E query/read
cognition](7G5E4E_FINAL_CLOSURE.md). The sole qualified profile is
`compression/deep disabled`; a request for compression or deep with native
selection must fail before normal service.

## Current public entrypoints

| Entrypoint | Fabric creation | Data root | Writes? | Queries? | Close path | Must understand selector? |
| --- | --- | --- | --- | --- | --- | --- |
| `python -m torment_service` | `__main__` starts Uvicorn; importing `torment_service.app` constructs module-global Fabric. | `TORMENT_DATA_DIR`, else `torment_service/../data`; Fabric canonicalizes it. | Yes: REST exposes ingest, proposal, bridge, promotion, compression, checkpoint, and other mutations. | Yes: query, retrieve, trace, archive, and diagnostics. | FastAPI lifespan calls `fabric.close()`. | Yes: primary public owner. |
| `python -m torment_service.mcp_server` | `main()` prewarms `_get_fabric()`; otherwise lazy singleton construction on first tool/resource. | `TORMENT_MCP_DATA_DIR`, else `./data`; Fabric canonicalizes it. | Yes: MCP Spine tools submit ingest, feedback, and other mutable operations. | Yes: MCP tools/resources read via Spine/Fabric. | No explicit shutdown close of `_fabric`; process exit is the practical boundary. | Yes: separate public process owner. |
| Direct `TormentFabric(data_dir=...)`, scripts, simulations | Any caller can construct one. Scripts/simulations are not current production owners. | Caller supplied. | Potentially. | Potentially. | Caller/context-manager owned; scripts vary. | Yes if authoritative root; otherwise future administration rejects it or marks it maintenance-only. |

REST applies profile defaults and reads environment before global Fabric creation.
MCP reads its own root/client environment during startup/lazy initialization.
Their defaults coincide only if MCP launches from repository root; that is not
durable agreement. REST synchronous handlers can run in FastAPI worker threads.
MCP is a separate stdio process whose concurrency belongs to the MCP runtime.

REST and MCP can point at the same legacy root today, but have no shared native
selector or lifecycle owner. Blocker-5 therefore requires:

```text
ONE_DURABLE_DEPLOYMENT_AUTHORITY_PER_DATA_ROOT = REQUIRED
```

Existing tests restart by closing/reconstructing Fabric or recovered readers at
the same root. There is no production-shaped REST/MCP restart controller.
`Fabric.close()` releases legacy graph/index/deep-store resources and tails,
but owns no native production resources.

## Current native capability archaeology

| Surface | Current state | Ownership | Capability / gap |
| --- | --- | --- | --- |
| `runtime_qualification.py` | Qualification-only exact runtime policy. | Per call; inspection opens no core. | No memory read/write; future startup calls it. |
| `runtime_binding.py` | Inert STAGING binding; requires STAGING + in-core `LEGACY_ACTIVE`. | Facts only; preparation connection is not retained. | No selection/read/write/activation method. |
| `fabric_native_routing.py` | Explicit qualification capability; `production_activation_allowed=False`, `qualification_only=True`. | Process motif order and process-local SRG/world, no long-lived SQLite connection. | Router can make explicit qualified writes using bounded existing-core connections; revalidation requires STAGING/legacy-active. |
| `native_direct_shared_ingest.py` | E1 qualification seam; not imported by Fabric. | Caller supplies capability, post-write adapter, warm lane runtimes. | Write-capable only after preflight; exact READY-lane invalidation; no public selector/failure policy. |
| `native_post_write_runtime.py` | Prepared STAGING-only post-write composition. | Bounded core connections; possibly closeable external trajectory tail. | Qualification writes only; no lifecycle owner. |
| Existing-workspace admission/recovery | STAGING/legacy-active snapshots, descriptors, lane plans, and readiness evidence. | Readers own closeable qualified connections. | Recovery is read-only, with no legacy fallback/writer. |
| `NativeMemoryVectorRuntime` | Rebuildable float32 lane cache. | Owns `check_same_thread=True` reader and immutable NumPy snapshot. | Read-only; cannot be startup-global across arbitrary REST workers. |
| `NativeQualifiedQueryReadModel` | Native qualification read adapter. | Lazily owns lane runtimes; closes them; SRG is process-local. | Read-only, no selection/fallback; needs operation-safe owner. |
| Native motif/world/SRG owners | Process-local qualified state. | Locks/in-memory state; short-lived adapters bind current core truth. | Restart recreates them; they are not SQLite authority. |

Use a **distinct production-owned capability type**. Do not transform the
prepared staging type: it deliberately hard-codes and revalidates STAGING,
legacy-active, and no production activation.

## Runtime environment and convergence

```text
QUALIFIED_SQLITE_RUNTIME = 3.53.4
KNOWN_INELIGIBLE_SQLITE_RUNTIME = 3.51.2
THIS_IS_NOT_A_GREATER_THAN_OR_EQUAL_RULE = YES
```

| Environment | Python / sqlite module | Loaded SQLite | Conda source |
| --- | --- | --- | --- |
| `torment-substrate` | Python `3.11.15` build `h1044e36_0`; module `2.6.0` | `3.53.4` | conda-forge `sqlite 3.53.4 hdb435a2_1`; `libsqlite 3.53.4 hf5d6505_1`. |
| `torment` | Python `3.11.15` same build; module `2.6.0` | `3.51.2` | `sqlite 3.51.2 hee5a0db_0`; no `libsqlite` package was listed. |

The executables are the respective Conda environment `python.exe` paths.
The repository has `requirements.txt`, but no tracked Conda spec/lock or
SQLite pin; loaded Conda packages supply the runtime.

Proposed B5-A1 commands only; A0 did not run them:

```cmd
conda activate torment
conda install --dry-run --override-channels -c conda-forge ^
  sqlite=3.53.4=hdb435a2_1 libsqlite=3.53.4=hf5d6505_1

:: after separately authorized solver-plan review
conda install --override-channels -c conda-forge ^
  sqlite=3.53.4=hdb435a2_1 libsqlite=3.53.4=hf5d6505_1
```

Record solver movement before accepting it. Then record loaded Python/module/
SQLite facts, and rerun runtime qualification, connection/WAL, schema, native
write, native query, and actual service-lifecycle tests in converged
`torment`. Existing `torment-substrate` evidence is scientific evidence,
not activation of a differently packaged production runtime.

## Deployment-profile eligibility

A future selector consumes one canonical, explicit profile. It names exact
admitted scopes, representation lane, and retained-owner requirements; no
feature is inferred just because code exists.

| Input / owner | Classification | Native-selection law |
| --- | --- | --- |
| `TORMENT_COMPRESS_ENABLE` | `REQUIRES_EXACT_VALUE` | Must be false; true refuses native startup. |
| Deep-memory use/state | `UNQUALIFIED_PROFILE` | No standalone deep-enable exists; compression creates/uses `DeepMemoryStore`. Any active/required deep profile refuses. |
| Embed provider/model, effective dimension, representation contract | `REQUIRES_EXACT_VALUE` | Exact admitted `NativeRepresentationLane`: compatibility embedding, generation 1, raw float32, exact provider/model/dimension. Requested values are insufficient because non-strict construction can fall back to hash. |
| Embed device/batch/cache/strictness/endpoint | `REQUIRES_EXACT_VALUE` unless later output-equivalent qualification | Profile records effective vector-producing configuration. |
| `TORMENT_CHARACTER_ENABLE`, seeds/state | `EXTERNAL_OWNER_REQUIRED` | Character remains `CharacterStore`-owned; required profile verifies descriptor seed witness and compatible state. |
| Workspace domains, domain order, shared lane plan | `REQUIRES_EXACT_VALUE` | Private/shared lanes and stable order are admitted facts; no guessed domain selection. |
| Domain motif policy including `auto_merge_motifs` | `QUALIFIED_VARIATION` | M1/M2 behavior is qualified, but workflow policy is external and profile-captured. |
| `BridgeRegistry` and geometry | `EXTERNAL_OWNER_REQUIRED` | Required bridge profile verifies registry and exact admitted geometry. |
| SRG flags/state | `EXTERNAL_OWNER_REQUIRED` | Record active configuration; transient overlay is recreated after restart. |
| Hivemind flags/state | `EXTERNAL_OWNER_REQUIRED` | Remains external/lazy; native selection does not silently disable it. |
| Checkpoints and trajectory | `EXTERNAL_OWNER_REQUIRED` / `QUALIFIED_VARIATION` | Preserve external ownership and current `legacy`/`v2` trajectory law. |
| `TORMENT_SQLITE_INDEX_ENABLE` | `IRRELEVANT_TO_NATIVE_SELECTION` | Legacy optional sidecar, not semantic-core authority. |
| `TORMENT_PROFILE` and remaining effective profile flags | `REQUIRES_EXACT_VALUE` when profile-bearing | Evaluate canonical effective config, not a partial late environment. |

```text
selector requests NATIVE_ACTIVE
AND profile is not exactly qualified
=> refuse before normal REST or MCP service
```

No silent feature disablement, partial legacy fallback, dual read, or dual write
is an eligible response.

## Fence, selector, and core-role gap

Current in-core vocabulary is:

```text
core_metadata.core_role = STAGING | ACTIVE_CORE | EVIDENCE_ONLY
deployment_metadata.deployment_state =
    LEGACY_ACTIVE | CUTOVER_PENDING | NATIVE_ACTIVE
```

Current constructors create STAGING/legacy-active; bindings/routing reject other
combinations. There is no active-role transition API, maintenance protocol,
external selector, public startup agreement, writer drain, or controller.
Therefore `ACTIVE_CORE_ROLE_IMPLEMENTED = NO`: the enum exists, but the
production concept does not.

The smallest future selector carrier is a service-owned administration database
external to every semantic core:

```text
<data_root>/substrate/deployment/selector.sqlite
```

It contains a versioned singleton and append-only ledger: state, selector
generation, core UUID, contained relative core path, descriptor digest, profile
digest, and core metadata witness. A sibling write-once marker has no selector
authority; it only distinguishes old roots from managed roots missing state:

```text
<data_root>/substrate/deployment/selector-era-v1.json
```

Cores are service-configured contained paths, for example
`<data_root>/substrate/cores/<core-uuid>.db`. Request, workspace, agent, MCP,
and URL values never control selector/core paths.

Backward-compatible bootstrap is exactly:

```text
no selector-era marker
AND no selector database
AND no discovered contained core claiming CUTOVER_PENDING, NATIVE_ACTIVE,
    or ACTIVE_CORE
=> pre-selector LEGACY_ACTIVE compatibility
```

An old STAGING/legacy-active core is inert and does not prevent compatibility.
If era marker, selector corruption/missing, or active/pending core evidence is
present without agreement, startup refuses. Loss of all deployment evidence is
an operator backup/recovery event, never permission to guess legacy authority.

| Selector | Core facts | Runtime / profile | Expected startup |
| --- | --- | --- | --- |
| `LEGACY_ACTIVE` | no core | ordinary legacy, supported legacy profile | legacy |
| `LEGACY_ACTIVE` | matching STAGING + in-core legacy-active | qualified or ineligible, legacy profile | legacy; native inert |
| `CUTOVER_PENDING(core)` | matching staging/maintenance core | exact runtime, eligible profile | maintenance/recovery only |
| `NATIVE_ACTIVE(core)` | matching `ACTIVE_CORE` + in-core native-active | 3.53.4, qualified | native |
| `NATIVE_ACTIVE(core)` | core missing, wrong UUID, or STAGING | any | refuse |
| `NATIVE_ACTIVE(core)` | matching active core | 3.51.2 or unqualified profile | refuse |
| missing/corrupt selector | pre-selector conditions above | supported legacy | explicit legacy compatibility only |
| missing/corrupt selector | era marker or active/pending evidence | any | fail closed / operator recovery |

The core and selector cannot share one transaction. \"Atomic cutover\" is an
ordered fail-closed protocol:

1. Drain REST, MCP, and direct writers; capture frozen legacy snapshot identity
   and backups.
2. Create era marker; commit external `CUTOVER_PENDING(core_id)`. Normal
   service is maintenance-only.
3. Commit matching in-core pending maintenance evidence; complete/recover scoped
   admission and verify descriptor, profile, external owners, and core.
4. In one core maintenance transaction, record cutover evidence and set matching
   `ACTIVE_CORE`/in-core `NATIVE_ACTIVE(core_id)`.
5. Commit external `NATIVE_ACTIVE(core_id)`; only then construct production
   capability.

A crash before step 5 stays pending. Core-active/external-pending mismatch is
maintenance-only, never legacy. After step 5, exact agreement is required.

## Fallback, mutation, resource lifecycle, and rollback

| Fence state | Normal authority |
| --- | --- |
| `LEGACY_ACTIVE` | Legacy public reads/writes; native staging/maintenance has no production authority. |
| `CUTOVER_PENDING(core)` | Legacy normal writes and native normal semantic writes forbidden; maintenance/recovery only. |
| `NATIVE_ACTIVE(core)` | Native reads/writes authoritative; legacy evidence only. |

```text
NATIVE_ACTIVE_RUNTIME_LEGACY_FALLBACK = NONE
NATIVE_QUERY_FAILURE_LEGACY_READ_FALLBACK = NO
```

A native write/query/vector/side-store/post-write failure may fail under its
existing topology, but cannot route to legacy. Future owner states are
monotonic:

| Path | PRE_EFFECT | MUTATED | COMMITTED/RECOVERABLE |
| --- | --- | --- | --- |
| Private ingest | Before first router operation. | First native source/reinforcement commit. | Native operation/idempotency evidence resolves retry. |
| Shared direct ingest | Before router source/tail preflight. | First shared source commit. | Post-write/derived effects and READY-lane invalidation resolve natively. |
| Derived memory | Before successor publish. | First successor commit. | Parent operation key/transition resolves retry. |
| Proposal materialization | Before production bridge invokes materializer. | First materialization commit. | Workflow receipt plus native operation resolves recovery. |
| Motif mutation/merge | Before native merge transaction. | First merge mutation commit. | Native effects/workflow receipt resolve recovery. |

`MUTATED` is the no-fallback point; it does not falsely claim every
post-write effect is one transaction.

During pending, abort may return to legacy only after proving native normal
authority never opened and legacy writes did not resume incorrectly. After
native writes, recovery is stop/repair/qualified-native-backup/forward
recovery:

```text
AUTOMATIC_POST_NATIVE_ROLLBACK_TO_LEGACY = NO
```

All native connections retain `check_same_thread=True`, foreign-key,
busy-timeout, WAL, and `synchronous=FULL` qualification. One execution thread
owns one complete operation. A startup-created vector runtime cannot serve
arbitrary FastAPI workers.

| Resource | Future owner / close rule |
| --- | --- |
| Selector + era marker | Service-global/data-root scoped; REST and MCP resolve same facts. Maintenance controller alone mutates. |
| Core facts, descriptor, profile | Immutable workspace/core resolution; revalidate on every core open. |
| Production routing capability | New service-global per-core type with no raw retained connection; discard on shutdown. |
| Native write connections | One synchronous request/maintenance operation and worker; close before return. |
| Query model/vector readers | Initially request- and lane-scoped, made/used/closed in same worker. Thread-local cache needs separate qualification. |
| Vector freshness | Invalidate only lanes whose usable READY truth changed; request-scoped caches discard at boundary, never global invalidation. |
| Motif readers | Operation scoped; reopen current truth. Process order is not core authority. |
| World/SRG | Service-global process-local owners keyed by core/scope; recreate/reconcile at restart. |
| Post-write/trajectory tail | Operation or bounded service owner by profile; close tail in owning context. |

Character seed mismatch blocks a Character-required profile. Required
BridgeRegistry/geometry or workflow facts refuse their profile. ConflictRegistry,
checkpoint/trajectory, Hivemind, and other side stores retain existing external
and fail-soft behavior unless directly required. Deep store is not initialized.

## Backup, admission, crash, and later rehearsal

No native backup API is implemented; `BACKUP` is current maintenance
vocabulary only. Before cutover require a frozen legacy snapshot/manifest for
every lane, verified SQLite-consistent native backup (never a live WAL main
`.db` copy), and consistent selector/era/descriptor/maintenance backup.

Existing admission already supplies snapshot IDs, manifests, fingerprints,
descriptor digests, lane plans, readiness reports, and recovery-ready
descriptors. Future controller consumes—not re-migrates—those artifacts:

```text
quiesce legacy writes
→ capture complete scoped snapshot
→ freeze manifest/fingerprint in cutover evidence
→ run or resume admission only against that snapshot
→ require complete descriptor, expected core, lane/profile/owner checks
→ recover and verify native truth
→ advance pending protocol
```

| Crash point | Restart result |
| --- | --- |
| Before pending persistence | Legacy remains authoritative. |
| After pending, before/after verification | Pending; maintenance/recovery only. |
| After in-core active, before external active | Mismatch; maintenance/recovery only, never legacy. |
| After external active, before first request | Require agreement, then native startup. |
| During first write or after commit before response | Resolve native operation/idempotency evidence; no legacy replacement. |
| During shutdown | Stop admissions/new requests, close owned resources/tails, restart from agreement. |

Later rehearsal uses actual service paths in converged `torment`:

```cmd
:: Window 1
conda activate torment
python -m torment_service

:: Window 2
health / create / ingest / query / controlled shutdown-restart administration
```

Sequence: legacy startup on disposable root; stop REST/MCP writers; backup and
enter pending; prove normal-service refusal; complete admission; activate core
then selector; REST ingest/query; restart/query; prove MCP resolves same
selector. Exercise crash points by controlled fault injection. A0 ran none.

A later redacted diagnostic may expose backend, fence state, core ID, runtime
admissibility/version, profile eligibility, and reason code. It must not expose
paths, secrets, selector contents, or request-controlled values.

## Dependency order and evidence

1. **B5-A1:** production environment convergence and complete requalification
   in `torment`; no selector/Fabric routing change.
2. **B5-A2:** external selector/era, pure agreement resolver, explicit
   active-core/pending maintenance transitions, and crash-refusal tests; public
   Fabric stays legacy-only.
3. **B5-A3:** distinct resource owner/lifecycle, same-thread request readers,
   process-local owners, REST/MCP close behavior; still legacy-only.
4. **B5-A4:** common REST/MCP startup selection and profile refusal; no dual
   authority/fallback.
5. **B5-A5:** offline cutover controller, backup/admission protocol, crash and
   restart rehearsal.
6. **B5-A6:** diagnostics and formal two-window administration rehearsal.
7. **B5-A7:** closure after selected-profile evidence is green.

```text
NEXT_IMPLEMENTATION_SLICE =
    B5-A1 production environment convergence + requalification in torment;
    no selector, activation, or cutover code
```

Focused A0 characterization ran under `torment-substrate` / SQLite 3.53.4:

```text
67 passed — connection, runtime qualification, STAGING binding/routing,
            REST/MCP legacy-only construction
31 passed — post-write lifecycle, multi-scope recovery/admission,
            native query read model
98 passed — bounded A0 characterization total
```

No production code, kernel, selector, active core, cutover, or environment was
changed by this preflight.

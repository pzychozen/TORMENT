# Blocker-5 A4R3 — Public backend selection and transport

## Result

R3 closes public backend selection without a production cutover. The public runtime has one cached owner per canonical data root and consults only B5-A2's read-only durable deployment resolver before it constructs either a `TormentFabric` or `NativeProductionResourceOwner`.

```text
PUBLIC_BACKEND_AUTHORITY_SOURCE = DURABLE_DEPLOYMENT_SELECTOR
LEGACY_PUBLIC                    -> PublicTormentRuntime(LEGACY, Fabric)
NATIVE_AGREEMENT                 -> NativePublicTormentRuntime(Fabric, B5-A3 owner)
MAINTENANCE_ONLY / REFUSED       -> startup refusal (503)
NORMAL_PUBLIC_SELECTOR_MUTATION  = NONE
```

Host startup may register the profile and admission descriptor needed to consume a native agreement, but those facts cannot select a backend. There is no request, workspace, agent, CLI, or environment-variable backend override. Importing `torment_service.app` or `torment_service.mcp_server` does not construct a runtime, resolve a selector, or mutate deployment state.

## Runtime and lifetime

`public_runtime.py` is the small facade used by REST, Spine, and MCP. It owns the Fabric cognition/external owners; native mode additionally owns exactly one B5-A3 production resource owner for its data root. REST constructs it in FastAPI lifespan and closes it at shutdown. MCP uses the same factory/cache entry and closes it on stdio exit.

Each native query opens a B5-A3 `NativeProductionQueryContext`, runs existing Fabric query cognition against that qualified read model, and closes the context before return. No global SQLite/vector query reader or query-algorithm fork exists. Native preparation receives an inert view with admitted domains, native routing geometry, read-only bridge/conflict/meta/policy evidence, but no legacy `MemoryGraph` or motif writer. Private writes are constrained to the recovered private lane's admitted motif domain; an unqualified shared target or auto-merge policy is refused before cognition.

## Public memory surface classification

Every public memory-touching surface is classified below. Grouped route entries cover every concrete route named in the cell. The native REST middleware denies every unlisted route before endpoint behavior can run.

| Public surface | Legacy behavior | Native equivalent | Native-mode disposition |
| --- | --- | --- | --- |
| `POST /agent/ingest` | Fabric ingest | R2 executor through Spine | NATIVE_SUPPORTED |
| `POST /tool/ingest` | Tool-result Fabric ingest | R2 executor through Spine with tool provenance | NATIVE_SUPPORTED |
| `POST /agent/query` | Fabric core query | B5-A3 reader plus existing Fabric query cognition | NATIVE_SUPPORTED |
| `POST /retrieve` | Fabric core query plus archive/reference/identity assembly | Native core query plus unchanged external assembly | NATIVE_SUPPORTED |
| `POST /spine/submit_task` for `ingest`, `tool_result_ingest`, `query_memory` | Governed Spine dispatch | Same Spine dispatch to native facade | NATIVE_SUPPORTED |
| `GET /health`, `/profiles`, `/config`, `/workspaces/meta`, `/embedder/check`, `/retrieve/profiles`, `/spine/operations` | Service/configuration view | No core-memory authority | READ_ONLY_NON_CORE_MEMORY |
| `GET /agent/{id}/identity`, `/roles`, `/character/state`, `/character/seed` | Identity/role/Character stores | Same external stores | EXTERNAL_OWNER_UNCHANGED |
| `GET /workspace/{id}/embed_audit`, `GET /workspaces/embed_audit_summary` | Embed audit evidence | Same read-only evidence | READ_ONLY_NON_CORE_MEMORY |
| `/archive/ingest_document`, `/archive/query`, `/archive/{workspace}/{agent}/documents*`, `/index/{workspace}/{agent}/archive/search` | Archive/document store | Same archive owner, never native core memory | EXTERNAL_OWNER_UNCHANGED |
| `POST /agent/ingest/route_probe` | Prediction only | No qualified native prediction route | REFUSED_BEFORE_EFFECT |
| `POST /agent/trace`, `/memory/chain`, `/memory/trace_full`, `/memory/trace_bundle`, `/memory/trace_view` | Legacy graph trace/read | No native trace contract | REFUSED_BEFORE_EFFECT |
| `POST /agent/feedback`, promotion/canon, proposals, bridges, conflicts, motif decisions | Legacy reinforcement or mutation | No stable public-native recovery contract | REFUSED_BEFORE_EFFECT |
| Workspace/agent create, clone, domains, repair, maintenance, and jobs | May construct/mutate legacy graph/configuration | No native public lifecycle/migration contract | REFUSED_BEFORE_EFFECT |
| Collective reingest/proposal/status/event/packet routes | Hivemind/shared legacy paths | No qualified public native collective contract | REFUSED_BEFORE_EFFECT |
| Active motif, bridge, proposal, motif entropy/merge, conflict read routes | Legacy registry read | No native public registry read contract | REFUSED_BEFORE_EFFECT |
| Checkpoint, compression, spirit-return/reflection, deep-memory, index rebuild, cognition-run, thinking debug, debug metrics/provenance, spine status | Legacy/deep/compression or graph-adjacent execution | Compression/deep disabled; no R3 contract | REFUSED_BEFORE_EFFECT |
| Any other REST route | Historical/default behavior | Fail-closed native allowlist | REFUSED_BEFORE_EFFECT |
| MCP `torment_ingest`, guarded `torment_tool_result_ingest`, and canonical supported submit | Spine tools | Same cached facade and native Spine route | NATIVE_SUPPORTED |
| MCP `torment_query_memory` and canonical `query_memory` | Spine query tool | B5-A3 reader plus Fabric cognition | NATIVE_SUPPORTED |
| MCP state, feedback, reinforce, and unsupported canonical operations | Legacy/core or unsupported operation | Native preflight refusal | REFUSED_BEFORE_EFFECT |
| MCP memory-summary, collective-status, guarded admin-status, provenance resources | Direct legacy graph/registry readers | No R3 native resource contract | REFUSED_BEFORE_EFFECT |

```text
PUBLIC_MEMORY_SURFACE_CLASSIFICATION_COMPLETE = YES
UNKNOWN_PUBLIC_MEMORY_ROUTES = 0
NATIVE_RETRIEVE_CORE_MEMORY = NATIVE
```

## Recovery, guards, and authorization

Native mutations require a caller `Idempotency-Key`; a missing key is rejected by native Spine preflight before advisory cognition or a handler. R2 remains the only retry/recovery system: COMPLETE replays return the exact stored public result without another kernel pass, source write, or post-write chain. A changed semantic request for a completed key is a 409 idempotency conflict before re-cognition. Recovery-required cases also have a 409 transport disposition.

Native preflight permits only fast `ingest`, `tool_result_ingest`, and `query_memory`. Spine trust/operation routing is preserved before the native operation fence; REST authentication runs first. Unsupported operations cannot reach legacy reinforcement, graph mutation, compression/deep memory, proposal materialization, or fallback.

Focused service tests replace every `MemoryGraph` construction, search, vector search, spawn, payload update, and flush with a failing instrument. REST ingest/query/retrieve, Spine, and MCP ingest/query pass with zero legacy calls and unchanged legacy private-node bytes.

```text
NATIVE_PUBLIC_LEGACY_MEMORY_ACCESS = REFUSED
NATIVE_PUBLIC_DUAL_AUTHORITY_DETECTED = NO
PUBLIC_NATIVE_LEGACY_FALLBACK = NONE
DUAL_WRITE = NO
DUAL_READ = NO
PUBLIC_NATIVE_POST_WRITE_PARITY = PASS
PUBLIC_NATIVE_FULL_QUERY_COGNITION_PARITY = PASS
```

## Evidence and retained boundary

Under `conda activate torment` and SQLite `3.53.4`, focused R3 tests cover factory dispositions, native startup/restart, REST ingest/query/retrieve, Spine, MCP, exact replay, changed-key conflict, no-write replay, reinforcement replay, shared ingress, missing-key refusal, and resource refusal. They are paired with B5-A2/A3/R1/R2 plus legacy REST/MCP/Spine regressions.

R3 only reads a pre-existing selector/core agreement. It does not snapshot legacy state, enter pending, admit production data, activate a core or selector, migrate/cut over the real root, dual-write, dual-read, roll back, or alter kernel files/mathematics/geometry/vectorisation. B5-A5 remains the separately authorized offline cutover controller and crash/restart rehearsal.

```text
B5_A4R3_PUBLIC_BACKEND_SELECTION = QUALIFIED
B5_A4_PUBLIC_BACKEND_SELECTION   = QUALIFIED
REAL_PRODUCTION_CUTOVER_PERFORMED = NO
CURRENT_REAL_PRODUCTION_BACKEND   = UNCHANGED / NOT CUT OVER BY THIS SLICE
KERNEL_FILES_CHANGED              = 0
```

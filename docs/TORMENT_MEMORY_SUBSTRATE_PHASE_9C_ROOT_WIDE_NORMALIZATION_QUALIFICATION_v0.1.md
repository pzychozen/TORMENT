# TORMENT Memory Substrate — Phase 9C-R4 Root-Wide Normalization Qualification v0.1

## Status

```text
PHASE_9C_ROOT_NORMALIZATION = PASS

MULTI_WORKSPACE_NORMALIZATION = PASS
MULTI_PRIVATE_NORMALIZATION = PASS
B3_DISPATCH_COMPOSITION = PASS
B4A_COMPOSITION = PASS
B4B_COMPOSITION = PASS
B4C_COMPOSITION = PASS
DECLARED_EMPTY_TOPOLOGY = PASS
TARGET_COMPATIBLE_EMPTY_MOTIF_ROOT = PASS
INCOMPATIBLE_EMPTY_MOTIF_ROOT = FAIL_CLOSED_AS_DESIGNED
SINGLE_TARGET_LANE = PASS
ROOT_CENSUS_CLOSURE = PASS
ROOT_ATOMIC_COMPLETION = PASS
INTERRUPTION_RECOVERY = PASS

ROOT_NORMALIZATION_READY = YES
GEOMETRY_DERIVED_EXTERNAL_STATE_GATE = STILL_UNRESOLVED
REAL_ROOT_ACTIVATION_READY = NO
```

Phase 9C-R4 closes the originally authorized synthetic root-normalization
composition. It adds one administrative coordinator over the already-qualified
Phase 9A description/evidence, Phase 9B adapter, B3A/B3B, B4A/B4B/B4C, and
Phase 9C-R3 generalized readiness owners. It does not create a root core,
admit a real source, select a runtime, or activate a public backend.

## Chronology and authority

```text
initial 9C = stopped at the zero-member motif contract
R0 = zero-member historical active-aggregate semantics resolved
R1 = B4C target-compatible zero-member projection qualified
R2 = stopped at the historical B5 topology limitation
R3 = generalized declared-topology readiness qualified
R4 = root-wide B3/B4/readiness composition qualified
```

R4 consumes `RootNativeProductionAdmissionDescription` directly. It does not
introduce another root-topology type. The Phase 9A description supplies the
immutable workspace plans, `RootScopeKey` identities, materialization posture,
representation disposition, frozen target lane, expected census, explicit
source manifest, feature posture, and geometry-derived external-state gate.

One request names one already-open synthetic STAGING core and one root. All
child requests must name that same core and the exact Phase 9A target lane.
`RootScopeKey` remains complete identity, so repeated EID `7`, agent ID, and
domain-like local labels in separate workspaces do not collide.

## Coordinator boundary

`NativeRootWideNormalizationService` accepts child requests only after the
existing frozen source-admission/B2 normalization boundary. It does not repeat
source admission, B2 memory normalization, vector generation, motif geometry,
or readiness calculations. The child B3/B4 services retain their own snapshot
verification, durable idempotency, and source-to-target proofs.

Before any child work or recovery result is trusted, the coordinator:

1. verifies the exact Phase 9A explicit-source manifest at the caller-supplied
   root;
2. checks a supplied recovery witness against root-description digest, census
   digest, manifest digest, staging-core identity, and target lane;
3. rechecks every Phase 9B metadata-less per-EID source through its qualified
   adapter; and
4. calls the existing B3/B4 services, whose own source-snapshot revalidation
   remains the per-child boundary.

The recovery witness is immutable evidence only. It is not persisted activation
authority. Existing B3/B4 durable idempotency records are the only completed
child work that may be recovered; a changed source manifest or metadata-less
source refuses before a child result can be reused.

## Exact dispatch and closure law

| Declared Phase 9A disposition / shape | R4 action |
| --- | --- |
| `TARGET_COMPATIBLE` `MEMORY_GRAPH` | Existing B3A only. |
| `REEMBED_REQUIRED`, `NO_VECTOR`, `UNUSABLE_VECTOR` | Existing B3B only, with the caller-injected qualified test embedder. |
| `UNKNOWN_IDENTITY` metadata-less private source | Phase 9B qualification/recheck, then existing B3B only. The historical vector is never passed to B3B or promoted. |
| Member-bearing target-compatible motif | Existing B4A only. |
| Member-bearing non-target motif with target member representations | Existing B4B only. |
| Exact target-compatible zero-member motif | Existing B4C only. |
| Hash or unknown zero-member motif | B4C refuses; the root result is incomplete and has no partial activation. |
| `EMPTY_SHARED_WITH_MOTIF` | No B3; target-compatible B4C is required. |
| No-memory workspace | No fabricated scope, binding, representation, or motif row. |

After all requested child operations, R4 invokes
`NativeGeneralizedRuntimeReadiness` exactly once over the complete declared
scope set. R3 remains the owner of B1 facts, declared-empty closure, B4C
reader certification, census closure, A3D binding/routing construction, and
the read-only readiness verdict.

The aggregate result is immutable and contains root admission identity, the
single native staging core identity, expected and observed workspace/scope
closure, per-scope B3 receipts, per-motif B4 receipts, generalized readiness,
source-manifest recheck status, the one target lane, unresolved activation
gates, and root completion status. `real_root_activation_ready` and
`partial_activation` are always false.

## Synthetic supported-root qualification

The new focused suite uses only `tmp_path` SQLite cores and deterministic
injected vectors. No production source layout is opened.

| Workspace | Synthetic topology | Qualified result |
| --- | --- | --- |
| WS-A | Five private target-compatible memory scopes; one target-compatible member-bearing shared motif scope; one non-target member-bearing shared motif scope | Five private B3A, shared B3A+B4A, and shared B3B+B4B complete. |
| WS-B | One private `REEMBED_REQUIRED` scope; one `EMPTY_SHARED_WITH_MOTIF` scope | Private B3B and empty shared B4C complete. |
| WS-C | One metadata-less per-EID private source | Phase 9B source recheck plus B3B complete; the synthetic source keeps canonical text continuous and its legacy vector remains historical UNKNOWN evidence. |
| WS-D | Identity-only agent and declared-unmaterialized domain | No materialized scope or fabricated runtime carrier. |

The supported root has four workspaces and ten materialized scopes. It closes
with one `st / BAAI/bge-small-en-v1.5 / 384` lane and
`ROOT_NORMALIZATION_READY = YES` while retaining the unresolved
geometry-derived external-state gate.

A separate negative root contains only an empty active shared motif whose
source lane is `hash / legacy-hash / 384`. B4C refuses it; the root has:

```text
ROOT_NORMALIZATION_COMPLETE = NO
ROOT_NORMALIZATION_READY = NO
REAL_ROOT_ACTIVATION_READY = NO
PARTIAL_ACTIVATION = NO
```

This is the required fail-closed result, not a B4C defect.

## Interruption and recovery evidence

The focused root test forces and resumes each non-semantic checkpoint:

```text
AFTER_FIRST_WORKSPACE
INSIDE_WORKSPACE_AFTER_REPRESENTATION_NORMALIZATION
AFTER_B3_BEFORE_B4
AFTER_B4_BEFORE_GENERALIZED_READINESS
AFTER_CHILD_COMPLETION_BEFORE_ROOT_WITNESS
```

Each resume passes the immutable recovery witness and rechecks source evidence
before the existing child services recover their deterministic/idempotent
records. The deterministic B3B test embedder is called exactly three times
over fresh work and not again during the resumed execution.

The suite separately refuses root-description drift, census drift, and named
source-manifest drift. Root target-lane and core drift are checked by the same
recovery-witness identity gate. A metadata-less source is rechecked on every
run; Phase 9A manifest failure is intentionally the earlier refusal when that
same named root artifact changes.

## Duplication review

| Function / role | Existing primitives called | Why it is not duplicate | Eventual survivor |
| --- | --- | --- | --- |
| `NativeRootWideNormalizationService.normalize` — root sequencing/checkpointing | Phase 9A manifest, Phase 9B recheck, B3A/B3B, B4A/B4B/B4C, R3 | It validates ordering and aggregates immutable receipts; it does not calculate a representation, motif, or readiness fact. | Root normalization orchestration. |
| `_recheck_metadata_less_sources` — Phase 9B recovery gate | `QualifiedMetadataLessPerEidLegacySource.recheck` | Delegates all parsing, canonical-text selection, vector evidence inspection, and source identity to Phase 9B. | Phase 9B source adapter. |
| `_dispatch_b3` — B3 selection by frozen disposition | `NativeMigrationRuntimeRepresentationBootstrapService`, `NativeMigrationRuntimeReembeddingBootstrapService` | It forwards typed requests; B3A owns capture-byte publication and B3B owns injected-embedder target derivation. | Existing B3A/B3B services. |
| `_dispatch_b4` — B4 selection by frozen motif request | Existing B4A, B4B, B4C services | It forwards typed requests; motif parsing, membership evidence, zero-member proof, centroid preservation, and regeometry remain the existing owners. | Existing B4A/B4B/B4C services. |
| `_run_generalized_readiness` — final root read-only gate | `NativeGeneralizedRuntimeReadiness` | It constructs only the qualified API input. R3 retains B1, B4C reader lineage, declared-empty, census, and A3D policy. | R3 generalized readiness. |
| Result/validation helpers | Existing child request/result contracts and Phase 9A description | They compare identities and format receipts only; no migration or cognitive formula is reproduced. | Root normalization orchestration. |

```text
DUPLICATED_B3_ALGORITHM_BODIES = 0
DUPLICATED_B4_ALGORITHM_BODIES = 0
DUPLICATED_READINESS_ALGORITHM_BODIES = 0
NEW_REEMBED_ENGINE = NO
NEW_VECTOR_ENGINE = NO
NEW_MOTIF_PERSISTENCE_ENGINE = NO
NEW_MOTIF_DECISION_ENGINE = NO
NEW_MOTIF_REGEOMETRY_ENGINE = NO
NEW_PARALLEL_PUBLIC_RUNTIME = NO
```

## Offline regression and safety evidence

The focused new suite completed:

```text
tests/test_substrate_root_normalization.py = 8 passed
```

The bounded Phase 9A/9B/B3/B4/R3/R4 composition batch passed `68` tests, and
the B1/B3/historical-B5 regression batch passed `58` tests (`126` total).

It was preceded by a port-8787 listener check with no output. Static vetting
of the selected R4 test and production paths found no HTTP client, URL,
socket, service startup, Uvicorn, FastAPI, loopback-port, subprocess, or
production-root construction. The only `embed` implementation is the local
deterministic test seam; no provider is constructed or contacted.

```text
PORT_8787_LISTENER_BEFORE_EACH_BATCH = NO
SELECTED_NETWORK_CAPABLE_TESTS = 0
NETWORK = NONE
LIVE_SERVICE = NONE
REAL_ROOT_CONTACT = NO
REAL_MEMORY_MODEL_CONTACT = 0
REAL_REEMBED_OPERATIONS = 0
SELECTOR_CREATED = NO
REAL_CORE_CREATED = NO
REAL_ADMISSION_RUN = NO
CUTOVER_RUN = NO
KERNEL_FILES_CHANGED = 0
BRAINVISION_FILES_READ = 0
BRAINVISION_FILES_TOUCHED = 0
BRAINVISION_DATA_TOUCHED = 0
BRAINVISION_EVIDENCE_TOUCHED = 0
```

No Character, role, bridge, conflict, workflow, checkpoint, trajectory, deep
memory, Hivemind, world/SRG, Brainvision, or kernel owner is absorbed or
changed. The geometry-derived external-state disposition remains
`UNRESOLVED_PRE_ACTIVATION_GATE`.

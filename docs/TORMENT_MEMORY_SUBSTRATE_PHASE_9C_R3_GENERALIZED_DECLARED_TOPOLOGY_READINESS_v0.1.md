# TORMENT Memory Substrate — Phase 9C-R3 Generalized Declared-Topology Readiness v0.1

## Status

```text
PHASE_9C_R3_GENERALIZED_READINESS = PASS
DECLARED_EMPTY_MEMORY_SCOPE = PASS
DECLARED_ZERO_MOTIF_WORKSPACE = PASS
B4C_READINESS_LINEAGE = PASS
NO_MEMORY_WORKSPACE = PASS
MULTI_PRIVATE_READINESS = PASS
ROOT_CENSUS_CLOSURE = PASS

HISTORICAL_B5_CONTRACT = PRESERVED
ACTIVATION_READY = NO
GEOMETRY_DERIVED_EXTERNAL_STATE_DISPOSITION = UNRESOLVED_PRE_ACTIVATION_GATE
```

This phase supplies a successor, root-profile readiness policy. It does not
reinterpret historical B5 as generalized topology authority, activate a native
route, create a selector/core, perform admission, ingest, re-embed, or touch a
real root.

## Problem and resolution

Historical `NativeWorkspaceRuntimeReadiness` is the qualified first-profile
authority: it expects materialized, nonempty memory and motif closure. Phase
9C-R2 correctly stopped rather than weakening that contract.

`NativeGeneralizedRuntimeReadiness` is the new read-only successor. It consumes
the existing Phase 9A `RootNativeProductionAdmissionDescription`, a separately
bound B1 request for each declared materialized scope, the native motif reader,
and the A3D binding/routing constructors. Its law is:

```text
OBSERVED_TOPOLOGY == DECLARED_TOPOLOGY
AND EVERY DECLARED MATERIALIZED FACT IS READY
```

It never treats an empty Python collection as readiness evidence.

## Declared topology rules

| Declared shape | Required closure |
| --- | --- |
| `MEMORY_GRAPH` | At least one B1 migrated-memory fact, each runtime-ready. |
| `EMPTY_SHARED_WITH_MOTIF` | Zero current target-scope memory objects and zero READY compatible representations; a declared motif must lawfully close. |
| No motif source | Zero B1 source motifs and no native runtime motif in the requested scope. |
| B4C motif | Native reader proves exact B4C evidence and current member count is zero. |
| No-memory workspace | Exactly zero materialized scope plans, with `no_memory_scope=True`; no memory binding is fabricated. |

The narrow current-target-scope inventory is topology-only. B1 continues to own
migration/source/representation readiness classification; the inventory merely
prevents an out-of-band memory or active representation from being invisible in
a scope explicitly declared empty.

## Reused primitives and semantic ownership

| New or extracted function | Existing primitives called | New semantic ownership | Why this is not duplication | Eventual survivor |
| --- | --- | --- | --- | --- |
| `NativeGeneralizedRuntimeReadiness` | B1 preflight, `NativeMotifRuntimeReader`, Phase 9A description, A3D construction helper | Root-wide declared-topology closure | It composes existing facts; it does not recalculate B1/B3/B4 evidence. | Generalized root-profile readiness |
| `read_core_runtime_readiness` | Existing B1 core/deployment checks | Shared B1 staging-gate read | Exact extraction from B1; B1 delegates to it. | B1 shared fact helper |
| `construct_read_only_runtime_capability` | `prepare_native_memory_runtime_binding`, `prepare_native_fabric_routing_capability`, embedder validation | Transient A3D construction result | Exact extraction from B5 private construction; B5 delegates to it. | Shared readiness construction helper |
| B4C reader methods | Existing motif state, alias, membership, transition/evidence validation | Certified source-to-target zero-member lineage resolution | Certification stays reader-owned; readiness does not reproduce transition queries. | Native motif reader |

The frozen core-staging generic post-write adapter applies to private memory
writes. For shared scopes it requires one separately qualified shared consumer;
R3 does not invent such a consumer while geometry state remains unresolved.
Binding and routing are still constructed for every materialized scope. A
private post-write configuration is therefore required only for a declared
private `MEMORY_GRAPH` scope.

```text
NEW_PARALLEL_PUBLIC_RUNTIME = NO
NEW_B1_ENGINE = NO
NEW_B3_ENGINE = NO
NEW_B4_ENGINE = NO
NEW_READINESS_SEMANTIC = DECLARED_TOPOLOGY_GENERALIZED_CLOSURE_ONLY
HISTORICAL_B5 = RETAINED_BOUNDED_FIRST_PROFILE_QUALIFICATION_IMPORT_SUPPORT
```

## Qualification evidence

All tests used fresh synthetic SQLite databases beneath an explicit temporary
test base. They used captured synthetic NumPy vectors only; the test embedder
raises if called.

```text
W1 = PASS  five private scopes + one member-bearing shared B4A motif
W2 = PASS  private-only workspace with zero motifs
W3 = PASS  EMPTY_SHARED_WITH_MOTIF with B4C-certified zero-member motif
W4 = PASS  no-memory identity-only workspace with no fabricated binding

N1 = PASS  declared MEMORY_GRAPH with no migrated memory is refused
N2 = PASS  declared zero motifs with a native runtime motif is refused
N3 = PASS  ordinary zero-member motif remains B1-blocked without B4C evidence
N4 = PASS  B4A/B4B empty-member projection remains refused

EMPTY_SCOPE_UNEXPECTED_MEMORY = PASS/REFUSED
ROOT_SCOPE_INPUT_OMISSION_OR_EXTRA = PASS/REFUSED
SOURCE_MANIFEST_DRIFT = PASS/REFUSED
READINESS_DURABLE_EFFECTS = 0
READINESS_AUTHORITY_EXPANSION = 0
```

Final selected regression execution:

```text
51 passed — generalized readiness, B4A/B4B/B4C, reader, root description
37 passed — B1, B3A, historical B5
TOTAL = 88 passed
```

The selected static vet found no HTTP, socket, service, Uvicorn, loopback-port,
or configured-root references in the selected tests/helpers/product paths.

## Boundary accounting

```text
PORT_8787_LISTENER_BEFORE_EACH_BATCH = NO
PORT_8787_LISTENER_AFTER = NO
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
BRAINVISION_FILES_READ = 0
BRAINVISION_FILES_TOUCHED = 0
KERNEL_FILES_CHANGED = 0
```

## Resumption boundary

Phase 9C-R2 may resume only under separately authorized root-normalization
work. This qualification is neither a production admission order nor an
activation/cutover authorization. Geometry-derived external state remains an
unresolved pre-activation gate.

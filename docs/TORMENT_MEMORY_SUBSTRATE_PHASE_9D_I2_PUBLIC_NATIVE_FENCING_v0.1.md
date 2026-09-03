# TORMENT Phase 9D-I2 — Public / Native Runtime Fencing

Status: QUALIFIED OFFLINE — 2026-09-03

## 1. Scope and preserved authority

I2 establishes a public-runtime boundary only. It does not migrate query,
post-write, Character, motif, SRG, reinforcement, or kernel mathematics.

The one authority that selects public root mode remains the existing Blocker-5
deployment resolver:

```text
resolve_deployment_agreement(data_root, effective_profile)
    LEGACY_PUBLIC       -> PublicTormentRuntime legacy compatibility
    NATIVE_AGREEMENT    -> NativePublicTormentRuntime
    MAINTENANCE/REFUSED  -> startup refusal
```

No I2 selector, request field, workspace field, membership row, or public
facade attribute makes an independent backend decision. `NativeProductionResourceOwner`
continues to revalidate the selected agreement and effective profile when an
explicit native scope is recovered.

```text
ROOT_PROFILE_GENERATION_CONTRACT = QUALIFIED
CURRENT_ROOT_PROFILE_DISCOVERY = QUALIFIED
ROOT_SCOPE_MEMBERSHIP = QUALIFIED
ROOT_QUALIFIED_RUNTIME_IDENTITY = QUALIFIED
```

## 2. Public fallthrough census

Before I2, `PublicTormentRuntime.__getattr__` delegated every missing attribute
to `TormentFabric`; the app proxy uses that facade too. I2 adds the maintained
`PUBLIC_TORMENT_FABRIC_FALLTHROUGH_CENSUS` denominator. It contains all 55
declared public `TormentFabric` methods/properties not already implemented by
the public facade. The M12 test compares that inventory against the live class
API, so an added public Fabric member fails qualification until classified.

Instance-only Fabric state is also covered: native `__getattr__` has no generic
pass-through, so an instance attribute that was not explicitly exposed is an
unclassified native refusal. Legacy mode retains its historical delegation.

### 2.1 Explicit native operations

| Public name | Legacy materialization | Legacy memory authority | Read only | Native explicit equivalent | I2 disposition |
|---|---|---|---|---|---|
| `get_workspace` | workspace/domain: YES | YES | NO | root-qualified `NativePublicWorkspaceView`; active membership required | `NATIVE_EXPLICIT_NOW`; absence refuses |
| `create_agent` | agent/private graph: YES | YES | NO | admitted existing identity/cognition preparation only | `NATIVE_EXPLICIT_NOW`; creation/admission refuses |
| `ingest` | workspace and agent: CONDITIONAL | YES | NO | qualified native public ingest executor | `NATIVE_EXPLICIT_NOW` |
| `query` | workspace and agent: CONDITIONAL | YES | YES | qualified native read model and workspace view | `NATIVE_EXPLICIT_NOW` |

`data_dir`, `kernel`, `locks`, `embedder_error`, `requested_embed_provider`,
and `requested_embed_model` are explicit facade properties rather than native
fallthrough. The last three are bounded health observability values only; they
do not create or resolve memory state.

### 2.2 Legacy workspace/agent and storage operations

| Public names | Materializes workspace | Materializes agent | Touches legacy memory authority | Read only | Native explicit equivalent | I2 disposition |
|---|---:|---:|---:|---|---|---|
| `clone_workspace`, `start_repair_embeddings_job`, `repair_embeddings` | YES/CONDITIONAL | CONDITIONAL | YES | MIXED | NO | `MUST_REFUSE_WHEN_ROOT_NATIVE` |
| `feedback`, `reinforce`, `reingest_convergence` | CONDITIONAL | YES | YES | NO | NO | `MUST_REFUSE_WHEN_ROOT_NATIVE` |
| `ingest_reference`, `load_reference`, `unload_reference`, `list_active_loads` | CONDITIONAL | CONDITIONAL | YES | MIXED | NO | `MUST_REFUSE_WHEN_ROOT_NATIVE` |
| `write_environment`, `consult_environment`, `probe_environment_on_fail` | CONDITIONAL | CONDITIONAL | YES | MIXED | NO | `MUST_REFUSE_WHEN_ROOT_NATIVE` |
| `propose_closure`, `ratify_closure`, `commit_closure`, `revise_closure`, `get_closure`, `get_closure_current`, `list_closures` | CONDITIONAL | CONDITIONAL | YES | MIXED | NO | `MUST_REFUSE_WHEN_ROOT_NATIVE` |
| `propose_share`, `process_proposals`, `decide_proposal`, `decide_bridge`, `approve_domain_suggestion` | YES/CONDITIONAL | CONDITIONAL | YES | MIXED | NO | `MUST_REFUSE_WHEN_ROOT_NATIVE` |
| `motif_entropy`, `list_motif_merges`, `decide_motif_merge`, `list_conflicts`, `decide_conflict`, `list_proposals`, `list_bridges` | CONDITIONAL | NO | YES | MIXED | NO | `MUST_REFUSE_WHEN_ROOT_NATIVE` |

All names in this table remain
`LEGACY_ONLY_ALLOWED_WHEN_ROOT_LEGACY`. They are not deleted. Their native
equivalents require future scope-specific parity and, for creation/admission,
the separately named external admission-owner authority.

### 2.3 Legacy nominal reads, compatibility state, and maintenance inspection

| Public names | Materializes workspace | Materializes agent | Touches legacy memory authority | Read only | Native explicit equivalent | I2 disposition |
|---|---:|---:|---:|---|---|---|
| `memory_chain`, `trace`, `trace_full_graph`, `trace_bundle`, `trace_view` | YES/CONDITIONAL | CONDITIONAL | YES | MIXED (`trace_bundle` writes) | NO | `MUST_REFUSE_WHEN_ROOT_NATIVE` |
| `get_kernel_runtime_context`, `get_srg_relational_signal`, `list_orphaned_deep_hits` | NO/CONDITIONAL | NO | CONDITIONAL | YES | NO | `MUST_REFUSE_WHEN_ROOT_NATIVE` |
| `list_workspaces_meta`, `list_clone_jobs`, `get_clone_job`, `list_repair_jobs`, `get_repair_job`, `cancel_repair_job` | NO | NO | CONDITIONAL | MIXED | NO | `MUST_REFUSE_WHEN_ROOT_NATIVE` |
| `list_active_batons`, `resolve_baton` | CONDITIONAL | CONDITIONAL | YES | MIXED | NO | `MUST_REFUSE_WHEN_ROOT_NATIVE` |
| `native_memory_binding`, `native_memory_binding_readiness`, `prepare_native_cognition_agent` | NO | CONDITIONAL | CONDITIONAL | MIXED | internal-only, never public | `MUST_REFUSE_WHEN_ROOT_NATIVE` |

This section is deliberately conservative. A nominal legacy read is not
treated as native-safe merely because it might return no rows: several begin
by calling `get_workspace`, which is a legacy creation seam. I2 retains no
generic safe native fallthrough.

```text
PUBLIC_FALLTHROUGH_CENSUS = COMPLETE
NATIVE_SAFE_FALLTHROUGH_SURFACES = NONE
PUBLIC_FACADE_LEGACY_FALLTHROUGH = STILL_PRESENT_FOR_LEGACY_MODE
PUBLIC_FACADE_NATIVE_FALLTHROUGH = FENCED
```

## 3. Central fence and legacy callee defense

The public facade first refuses every native `__getattr__` request. It
distinguishes a known, classified compatibility member from an unclassified
member in a stable `NativePublicOperationRefused` (HTTP 409) error, but neither
form reaches Fabric.

The facade-only fence is not the sole defense. When the existing deployment
resolver selects `NATIVE_AGREEMENT`, `NativePublicTormentRuntime` installs one
private refusal capability into that exact Fabric instance. The two legacy
lazy materialization primitives call it as their first operation:

```text
TormentFabric.get_workspace -> refuse before Workspace construction
TormentFabric.create_agent  -> refuse before identity/private graph creation
```

This blocks a forgotten convenience helper or direct Fabric call reachable
from the native public runtime. A legacy Fabric receives no capability, so its
historical creation behavior is unchanged.

```text
NATIVE_ACTIVE_LEGACY_MATERIALIZATION = STRUCTURALLY_BLOCKED
GET_WORKSPACE_NATIVE_FALLBACK = BLOCKED
CREATE_AGENT_NATIVE_FALLBACK = BLOCKED
LEGACY_MODE_BEHAVIOR = PRESERVED
```

## 4. Explicit native resolution and admission fence

Every explicit native public operation follows this sequence:

```text
current deployment agreement/profile
    -> NativeProductionResourceOwner revalidation
    -> current root-qualified runtime recovery
    -> active root-scope membership lookup
    -> existing native resource/view
```

The owner turns a stale or absent root/profile into the stable public refusal
`native public root/profile authority is absent or stale`; it never returns to
legacy routing. Missing private/shared membership produces an admission
refusal before workspace, domain, agent, graph, membership, or witness
creation.

`NativePublicTormentRuntime.create_agent` is identity resolution for an
already-admitted agent, not native admission. A supplied seed/witness-like
value is refused before effect. There is no public native `create_workspace`,
scope-admission, membership-creation, or witness-minting operation.

The REST native allowlist was correspondingly narrowed. Workspace creation,
clone, agent creation, domain approval, proposal processing, and legacy
workspace metadata are unclassified in native mode and are rejected by the
existing middleware before endpoint dispatch.

```text
NATIVE_SCOPE_ABSENCE = NON_MATERIALIZING_REFUSAL
NATIVE_PUBLIC_RESOLUTION = ROOT_QUALIFIED
PUBLIC_NATIVE_CREATE_WITHOUT_EXTERNAL_AUTHORITY = REFUSED
NAMED_EXTERNAL_ADMISSION_OWNER_GATE = OPEN
EXTERNAL_WITNESS_AUTHORITY_QUALIFIED = NO
```

## 5. Qualification evidence

All qualification used local synthetic roots, local SQLite fixtures, and the
existing test-only embedder. No production root, service process, MCP process,
or external embedding provider was used.

| Test slice | Result |
|---|---:|
| `tests/test_p9d_i2_public_native_fencing.py` (M1–M12; M10 has direct and REST classifications) | 13 passed |
| `tests/test_b5_a4r3_public_backend_selection.py` | 5 passed |
| `tests/test_b5_a4r1_public_mutation_identity.py` | 7 passed |
| `tests/test_b5_a4r2_native_public_ingest_recovery.py` | 23 passed (8 + 9 + 6 bounded batches) |
| `tests/test_substrate_root_scope_membership.py` | 21 passed |

The M12 inventory test is also the focused static materialization-boundary
invariant: no new declared public Fabric API can become native fallthrough
without an explicit census decision. The native public module has no import or
call path to a legacy materializer except the installed central refusal layer.

## 6. Temporary compatibility paths and retirement gates

| Path | Current owner | Why retained | Native replacement | Retirement gate | Eventual survivor |
|---|---|---|---|---|---|
| `PublicTormentRuntime.__getattr__` | public facade | legacy client compatibility | explicit native facade methods | all retained legacy surface parity classified | explicit public dispatch |
| `TormentFabric.get_workspace` | legacy Fabric | legacy root workspace lifecycle | root-qualified native workspace view | native workspace lifecycle/admission authority | native workspace resolver |
| `TormentFabric.create_agent` | legacy Fabric | legacy identity and private graph lifecycle | admitted identity preparation only | external admission owner plus native agent lifecycle | native admission-aware identity resolver |
| legacy public backend delegation | public facade | legacy-root service compatibility | `NativePublicTormentRuntime` | native parity per operation | selector-resolved explicit backend |

I2 does not authorize removal of any legacy path. It makes native mode fail
closed until each replacement has an explicit authority and semantic-parity
qualification.

## 7. Final I2 disposition

```text
PHASE_9D_I2_PUBLIC_NATIVE_FENCING = PASS
PUBLIC_FALLTHROUGH_CENSUS = COMPLETE
NATIVE_ACTIVE_LEGACY_MATERIALIZATION = STRUCTURALLY_BLOCKED
LEGACY_MODE_BEHAVIOR = PRESERVED
NATIVE_SCOPE_ABSENCE = NON_MATERIALIZING_REFUSAL
NATIVE_PUBLIC_RESOLUTION = ROOT_QUALIFIED
PUBLIC_NATIVE_CREATE_WITHOUT_EXTERNAL_AUTHORITY = REFUSED
PUBLIC_FACADE_NATIVE_FALLTHROUGH = FENCED
PUBLIC_FACADE_LEGACY_FALLTHROUGH = STILL_PRESENT_IF_REQUIRED_FOR_LEGACY_MODE
GET_WORKSPACE_NATIVE_FALLBACK = BLOCKED
CREATE_AGENT_NATIVE_FALLBACK = BLOCKED
QUERY_COGNITION_CHANGED = NO
POST_WRITE_COGNITION_CHANGED = NO
TORMENT_MATHEMATICS_PRESERVED = YES
BLOCKER_5_REOPEN_REQUIRED = NO
REAL_PRODUCTION_ACTIVATION = NOT_AUTHORIZED
```

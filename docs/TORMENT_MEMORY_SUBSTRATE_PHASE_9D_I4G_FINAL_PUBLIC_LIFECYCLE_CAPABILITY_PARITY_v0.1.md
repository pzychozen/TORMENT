# TORMENT Memory Substrate — P9D-I4G Final Public Lifecycle + Capability Reconciliation

**Status:** bounded private/native-public reconciliation. Offline synthetic
evidence only. This artifact neither selects a deployment nor authorizes
activation, cutover, retirement, service startup, provider contact, or a
real-root contact.

## 1. Decision

I4G finds a coherent bounded native public lifecycle without changing TORMENT
mathematics, query ordering, conflict scoring, or the selected post-write
formulae. The native facade remains deliberately small. It is not a generic
native replacement for `TormentFabric`.

One REST composition correction was required. Native `POST /retrieve` can use
the qualified public `query` route and then perform pure response assembly. It
cannot foreground a scoped reference because that optional branch calls the
legacy-only `list_active_loads` owner. A nonempty `scope_tag` now returns HTTP
409 before core query or reference access. The pre-existing archive-recall
refusal is preserved. The unscoped, archive-disabled native route remains
qualified.

```text
I4G_PUBLIC_LIFECYCLE = QUALIFIED_BOUNDED_NATIVE_PUBLIC
I4G_REST_REFERENCE_COMPOSITION_CORRECTION = APPLIED
LEGACY_QUERY_SEMANTICS_CHANGED = NO
CONFLICT_SCORING_FORMULA_CHANGES = 0
QUERY_ORDER_CHANGES = 0
TORMENT_MATHEMATICS_PRESERVED = YES
```

## 2. Deployment selection, startup, and revalidation

`resolve_deployment_agreement` is the only selector. It has three relevant
outcomes:

| Durable disposition | Public construction |
|---|---|
| `LEGACY_PUBLIC` | Construct the legacy facade over cognitive Fabric. |
| `NATIVE_AGREEMENT` | Require exact host-qualified profile and a real admission descriptor, then construct `NativeProductionResourceOwner`. |
| refused / maintenance / stale | Refuse startup; do not fall back to legacy. |

`PublicRuntimeConfiguration`, including the optional all-or-nothing host
environment facts, supplies proof facts only. It cannot select legacy or
native mode. A cached native runtime may be reused only with the same
qualified profile facts. Each native workspace, read, write, and post-write
context re-resolves the agreement and checks selector generation, core ID,
descriptor identity, profile digest, core witness, and SQLite runtime witness.
A stale or missing fact becomes a native refusal; it is never translated into
a legacy operation.

The selected native profile requires:

```text
compression_enabled = false
deep_memory_enabled = false
```

Compression and deep memory are therefore not mandatory dependencies of this
bounded profile. The shared compression slot is an explicit disabled no-op;
enabling either feature remains outside I4G and refuses before an unqualified
owner can run.

The exact admitted representation facts in the frozen I4G qualification
evidence are:

```text
REPRESENTATION_PROVIDER = b5-a3
REPRESENTATION_MODEL = deterministic-3
REPRESENTATION_DIMENSION = 3
```

I4G qualification applies only to this exact admitted representation
provider/model/dimension and selected profile. A different representation
provider, model, dimension, scope plan, external-owner map, compression
setting, or deep-memory setting requires separate qualification before
activation.

## 3. Public-operation census

The exact Fabric fallthrough denominator is 55 declared public methods or
properties, mechanically asserted against the live `TormentFabric` class.
There is no native generic fallthrough.

| Native public classification | Members | Count |
|---|---|---:|
| `EXPLICIT_NATIVE_QUALIFIED` | `get_workspace`, `create_agent`, `ingest`, `query` | 4 |
| `EXPLICIT_NATIVE_BOUNDED_REFUSAL` and `LEGACY_ONLY_WHEN_ROOT_LEGACY` | `approve_domain_suggestion`, `cancel_repair_job`, `clone_workspace`, `commit_closure`, `consult_environment`, `decide_bridge`, `decide_conflict`, `decide_motif_merge`, `decide_proposal`, `feedback`, `get_clone_job`, `get_closure`, `get_closure_current`, `get_kernel_runtime_context`, `get_repair_job`, `get_srg_relational_signal`, `ingest_reference`, `list_active_batons`, `list_active_loads`, `list_bridges`, `list_clone_jobs`, `list_closures`, `list_conflicts`, `list_motif_merges`, `list_orphaned_deep_hits`, `list_proposals`, `list_repair_jobs`, `list_workspaces_meta`, `load_reference`, `memory_chain`, `motif_entropy`, `native_memory_binding`, `native_memory_binding_readiness`, `prepare_native_cognition_agent`, `probe_environment_on_fail`, `process_proposals`, `propose_closure`, `propose_share`, `ratify_closure`, `reingest_convergence`, `reinforce`, `repair_embeddings`, `resolve_baton`, `revise_closure`, `start_repair_embeddings_job`, `trace`, `trace_bundle`, `trace_full_graph`, `trace_view`, `unload_reference`, `write_environment` | 51 |
| `INTERNAL_ONLY / SHOULD_NOT_BE_PUBLIC_NATIVE` | legacy graph and private-graph materialization internals; no safe fallthrough granted | 0 additional public members |
| `UNCLASSIFIED` | none | 0 |

`close` is a facade lifecycle operation outside that Fabric denominator. It is
qualified: it marks the facade closed, closes the native owner and all active
request contexts, and finally closes cognitive Fabric. Repeated close is safe.

The four explicit routes have these frozen bounds:

| Route | Bounded native contract |
|---|---|
| `get_workspace` | Revalidates authority and returns an inert read view of exactly the admitted shared domains, domain policy/meta/bridge projections, and qualified read-only conflict evidence. It refuses domain mutation. |
| `create_agent` | Resolves only an already-admitted private scope. A seed, missing scope, or workspace mismatch refuses before legacy graph creation. It grants no admission authority. |
| `ingest` | Requires a fast-path idempotency key, an admitted private motif domain or explicit admitted shared domain, and a policy-safe view before native cognition. |
| `query` | Revalidates, opens a request-scoped qualified read model, then calls the existing Fabric query formula over qualified private/shared evidence. Missing, malformed, or stale evidence is a refusal rather than an empty result or fallback. |

`trace` is `EXPLICIT_NATIVE_BOUNDED_REFUSAL`. I4C-R1 proved that legacy trace
does not apply private conflict evidence to private-hit scoring, and there is
no qualified native trace surface. A native trace is not required for this
bounded public profile. I4G therefore does not create one and does not alter
private-hit conflict scoring.

```text
NATIVE_PUBLIC_TRACE = EXPLICIT_BOUNDED_REFUSAL
I4G_NATIVE_TRACE_QUALIFICATION_QUESTION = ANSWERED_NO_FOR_BOUNDED_PROFILE
PRIVATE_HIT_CONFLICT_SCORING_CHANGE = NOT_AUTHORIZED
I4C_TRUE_SPLIT_CONFLICT_PARITY = FROZEN_PRESERVED
```

## 4. REST, Spine, and Python-facade agreement

The REST middleware resolves the same public facade before dispatch. In native
mode every unlisted endpoint returns HTTP 409 before legacy-memory effect.
The classified set is deliberately small:

| REST surface | Native disposition |
|---|---|
| `GET /health`, `/profiles`, `/config`, `/embedder/check`, `/retrieve/profiles`, `/spine/operations` | metadata/health only; no native memory authority is granted. |
| `POST /agent/ingest`, `POST /tool/ingest` | qualified keyed fast-path ingestion through the same Spine preflight and public facade. |
| `POST /agent/query` | qualified facade query. Advisory legacy-only probes are caught before use; they never become a fallback. |
| `POST /retrieve` | qualified only for core query plus pure assembly with archive recall disabled and no `scope_tag`; archive or reference composition returns HTTP 409 before effect. |
| `POST /spine/submit_task` | a single preflight gateway: only `ingest`, `tool_result_ingest`, and `query_memory` are supported; unqualified operations and non-fast paths refuse before effect. |
| every other REST route, including `/agent/trace` | middleware refusal before legacy-memory effect. |

This makes REST and direct-Python behavior agree: a route is qualified only
when it can remain inside the bounded native facade, and an unsupported
operation receives an explicit refusal instead of incidental legacy dispatch.

## 5. Write and post-canonical composition

Private and shared ingest share admission, key, capability, and canonical
source gates, but their approved post-write topology is intentionally not
broadened.

### Private

Private reinforcement is protected by an explicit existing guard in
`NativeFabricMemoryRouter._select_private_duplicate`: any non-private scope
returns `NOT_APPLICABLE` before embedding search. This is stronger than a
representation-side accident and requires no I4G code change.

```text
SHARED_REINFORCEMENT_GUARD = ROBUST_EXPLICIT_EXISTING_GUARD
SHARED_REINFORCEMENT_REPRESENTATION_DEPENDENCY = NO
SHARED_REINFORCEMENT_IMPLEMENTATION_CHANGE = 0
```

For a qualified private route, precommit external owners retain their frozen
order. A canonical failure returns before the native post-write tail; prior
precommit external residue is not rolled back or relabeled. Successful private
outcomes retain the qualified I4C/I4D/I4E/I4F sequence: applicable
create-only conflict/SRG and existing retained consumers, private
world/trajectory, Character, checkpoint, proposal, then private bridge.
Each existing owner keeps its documented independent fail-soft or propagating
failure boundary. Reinforcement and `NO_WRITE` preserve their existing gates;
this is not a claim of one global post-write transaction or exactly-once
execution across external owners.

### Shared

I4F-B remains the only shared composition authority. Ordinary non-true-split
shared create restores the frozen precommit owner sequence, performs canonical
storage, then enters the existing qualified shared-integrated E1 adapter.
`NO_WRITE` skips precommit and retains its all-outcome E1 disposition.
Canonical failure preserves its precommit residue and short-circuits E1.
Shared true split is refused before reservation, topology mutation, or
post-write.

```text
SHARED_PRECOMMIT_EXTERNAL_OWNER_RESTORATION = PRESERVED
SHARED_E1_COMPOSITION = PRESERVED
SHARED_TRUE_SPLIT = REFUSED_PENDING_SEPARATE_AUTHORITY
SHARED_CONFLICT_WRITER_PARITY = NOT_CLAIMED
```

The I4C broad-private conflict writer remains a legitimate retained external
writer. I4C-R1 closed its proposed read roundtrip because the frozen legacy
query/trace law scores only shared conflict hits. No reader widening or
private conflict penalty is introduced.

## 6. Receipts, replay, close, and restart

Public keyed mutations retain their durable receipt/recovery behavior. A
replay recovers the completed native result and does not redo a completed
qualified native source merely because process-local owners were recreated.
The evidence distinguishes that bounded recovery from an invented global
exactly-once promise: external retained owners preserve their own historical
re-entry and failure dispositions.

`NativeProductionResourceOwner` owns no long-lived SQLite connection. Query,
write, and post-write contexts are request-scoped and same-thread. Closing the
owner closes active contexts, the request-owned adapter/reader resources, and
the private trajectory process writer, then drops only process-local SRG,
world, trajectory, and motif-order state. A restart creates a new owner only
after exact agreement recovery; durable native core truth and valid receipts
remain readable, while intentionally process-local overlays reset.

```text
REPLAY_IDENTITY = DURABLE_QUALIFIED_RECEIPT_WHERE_DOCUMENTED
GLOBAL_EXACTLY_ONCE = NOT_CLAIMED
OWNER_CLOSE = QUALIFIED
RESTART = REVALIDATE_THEN_RECOVER_OR_REFUSE
```

## 7. Owner census and refusal taxonomy

SQLite remains the native owner only for qualified core identity, revisions,
representations, and the bounded native routing/receipt facts. It does not
absorb external authority. Retained external owners include the conflict
registry/evidence, RoleStore, affect and symbol state, Character state,
proposal and bridge registries, Hivemind/collective state, trajectory and
checkpoint artifacts, archive/reference stores, and their independent
failure/retry rules.

Representative native refusals are intentionally explicit:

| Condition | Disposition |
|---|---|
| selector/profile/core/descriptor witness absent or stale | refuse startup or next context; never legacy fallback |
| unadmitted workspace, agent, domain, or private motif domain | refuse before cognition/materialization |
| seed-based create, workspace domain mutation, unsupported Fabric member | native bounded refusal |
| unsupported Spine operation, full path, or missing mutation key | refuse before effect |
| unqualified auto-merge, archive recall, scoped reference composition, trace, or other REST route | HTTP 409 before legacy-memory effect |
| unreadable/malformed required native query evidence | public query refusal, not an empty result |
| shared true split | `shared_true_split_refused` before reservation or E1 |

## 8. Evidence and final verdict

I4G reuses the frozen I2 public-census assertion, B5-A3 owner selection and
restart fixtures, I3C query-read/refusal evidence, I4B1F primary
outcome/receipt/restart fixtures, and I4F-B shared create, `NO_WRITE`,
canonical-failure, true-split-refusal, and replay fixtures. I4G adds the
native REST scoped-reference refusal assertion to the synthetic configured
runtime transport test.

```text
PUBLIC_FABRIC_FALLTHROUGH_DENOMINATOR = 55
PUBLIC_FABRIC_UNCLASSIFIED = 0
NATIVE_PUBLIC_TRACE = EXPLICIT_BOUNDED_REFUSAL
COMPRESSION_DEEP_DEPENDENCY = NOT_MANDATORY_FOR_BOUNDED_SELECTED_PROFILE
FORMULA_CHANGES = 0
QUERY_ORDER_CHANGES = 0
TORMENT_MATHEMATICS_PRESERVED = YES

RETIREMENT_ALLOWED = NO
REAL_PRODUCTION_ACTIVATION = NOT_AUTHORIZED
CONVERGENCE_OR_CUTOVER = NOT_AUTHORIZED
```

The final bounded-selected-profile disposition is:

```text
P9D_I4G_FINAL_PUBLIC_LIFECYCLE_CAPABILITY_PARITY = PASS_BOUNDED_SELECTED_PROFILE
I4G_ADVERSARIAL_REVIEW = PASS
I4G_READY_TO_FREEZE = YES
PUBLIC_API_CENSUS = COMPLETE
UNCLASSIFIED_PUBLIC_SURFACES = 0
PRIVATE_NATIVE_PUBLIC_PARITY = PASS_BOUNDED_SELECTED_PROFILE
SHARED_NATIVE_PUBLIC_PARITY = PASS_BOUNDED_NON_TRUE_SPLIT_SCOPE
SHARED_TRUE_SPLIT_DISPOSITION = STRUCTURALLY_FENCED
SHARED_I4B2_TWO_STAGE_PARITY = NOT_CLAIMED
NATIVE_PUBLIC_QUERY = QUALIFIED
NATIVE_PUBLIC_TRACE = EXPLICIT_BOUNDED_REFUSAL
NATIVE_ACTIVE_LEGACY_FALLBACK = NONE
NATIVE_SCOPE_ABSENCE = NON_MATERIALIZING_REFUSAL
SHARED_REINFORCEMENT_GUARD = ROBUST_EXPLICIT_EXISTING_GUARD
PUBLIC_MUTATION_RECEIPT_MODEL = QUALIFIED
PUBLIC_CLOSE_RESTART_PARITY = PASS
REPLAY_MODEL = QUALIFIED_EFFECT_SPECIFIC
EXTERNAL_OWNER_CENSUS = QUALIFIED
UNDOCUMENTED_DUAL_AUTHORITY = NONE
COMPRESSION_DEEP_DEPENDENCY = NOT_MANDATORY_FOR_BOUNDED_SELECTED_PROFILE
SELECTED_PROFILE_BOUNDARY = QUALIFIED_EXACT_PROFILE
SELECTED_PROFILE_REPRESENTATION_PROVIDER = b5-a3
SELECTED_PROFILE_REPRESENTATION_MODEL = deterministic-3
SELECTED_PROFILE_REPRESENTATION_DIMENSION = 3
FORMULA_CHANGES = 0
TORMENT_MATHEMATICS_PRESERVED = YES
RETIREMENT_ALLOWED = NO
REAL_PRODUCTION_ACTIVATION = NOT_AUTHORIZED
```

## 9. Boundary

```text
PRODUCTION_ROOT_CONTACT = NO
SERVICE_START = NO
PROVIDER_CONTACT = NO
PORT_8787_LISTENER = NO
SECOND_REPOSITORY_COGNITIVE_FUNCTION_INSPECTED = NO
BRAINVISION_SOURCE_CONTENT_OPENED = NO
BRAINVISION_INFORMATION_USED = NO
BRAINVISION_FILES_TOUCHED = 0
```

# TORMENT Phase 9D-R0 — Root-Native Runtime and Scope-Lifecycle System-Fit Archaeology

**Status:** READ_ONLY / DOCUMENTATION_ONLY / NO IMPLEMENTATION
**Purpose:** Define the smallest lawful shape for one root-qualified native
runtime that preserves MAIN_TORMENT_COGNITION across many workspaces, private
agents, and shared domains, including later authorized native scope creation.

This is a read-only archaeology and design-convergence record. It creates no
selector, core, relationship, scope, admission, transport, service, provider,
or memory mutation. It changes no mathematical formula.

## 1. Executive finding

The repository has the required native routing, vector, motif, namespace, and
relationship building blocks. Its current public/native recovery is
deliberately qualified for one existing-workspace profile; it is not yet a
root-wide scope authority.

~~~
RootScopeKey := (workspace_id, scope_kind, qualifier)

scope_kind = PRIVATE_AGENT | SHARED_DOMAIN
qualifier  = agent_id      | domain_id
~~~

NativeMemoryRuntimeScope already carries this identity. NativeFabricRoutingScope
adds the scope-specific motif, membership, and idempotency namespaces. Native
vector lane identity includes the complete scope. The required work is a
bounded replacement of one-profile recovery maps with root membership lookup by
RootScopeKey. It is not a new memory model, query algorithm, or cognitive law.

Known corrections required before activation:

- private/shared recovery first looks up a bare agent/domain and only then
  compares workspace;
- NativeQualifiedQueryReadModel caches bare agent/domain keys;
- public workspace-view construction requires exactly one private scope in its
  recovered runtime;
- PublicTormentRuntime.__getattr__ delegates unlisted public operations to
  legacy Fabric;
- native public post-write is bounded. Several consumers are staging-only,
  disabled, or required no-op. Its workspace view offers a read-only conflict
  registry, so attempted legacy conflict append is caught and skipped.

These are authority/composition gaps, not evidence that a parallel substrate or
changed cognition is needed.

~~~
PRESERVE_THE_MACHINE_THAT_THINKS_WITH_THE_MEMORIES = YES
~~~

If a native runtime cannot faithfully preserve a lawful active TORMENT
behavior, it must fail closed rather than silently subtract that behavior.

## 2. Evidence boundary

The inspection was limited to the named TORMENT public runtime, Fabric, native
routing/recovery/query/post-write/identity/schema files and Phase 8/9 records.
No service, MCP process, external provider, model, real production root, or
test was run.

Every use of cognition, query cognition, cognitive mathematics, and cognitive
runtime below means MAIN_TORMENT_COGNITION: existing TORMENT
Fabric/kernel/query/post-write behavior. No other application's cognition was
read, compared, generalized from, classified, connected, or used as evidence.

### Cognition authority disambiguation

The repository boundary contains two distinct cognitive functions. Repository
co-location alone establishes no runtime, semantic, storage, query, or
post-write linkage.

~~~
MAIN_TORMENT_COGNITION =
IN_SCOPE
ACTIVE TORMENT SEMANTIC OWNER
MUST BE PRESERVED

SECOND_REPOSITORY_COGNITIVE_FUNCTION =
OUT_OF_SCOPE
NOT CONNECTED TO TORMENT
NOT A NATIVE-MEMORY MIGRATION TARGET
NOT A QUERY-COGNITION CONVERGENCE TARGET
NOT A POST-WRITE CONVERGENCE TARGET
NOT EVIDENCE OF DUPLICATE TORMENT COGNITION

ONE_ACTIVE_TORMENT_QUERY_COGNITION_IMPLEMENTATION = YES
ONE_COGNITIVE_FUNCTION_IN_THE_ENTIRE_REPOSITORY = NO
~~~

Accordingly, every use in this record of **query cognition**, **cognition
implementation**, **cognition owner**, **cognition convergence**, **cognitive
mathematics**, or **cognitive runtime** means specifically
MAIN_TORMENT_COGNITION unless this document explicitly states otherwise.

The proposed Phase 9D implementation sequence has no dependency on, import
of, call to, replacement of, merge with, or retirement of the second
repository-resident cognitive function. No R0 finding relied on it; no finding
requires retraction or reclassification.

## 3. R0-1 — Public runtime ownership

| Public surface | Classification | Current fact | Root-native disposition |
|---|---|---|---|
| configure/create public runtime, cached runtime, close | ADMINISTRATIVE | Resolves selector and owns Fabric/production-owner lifecycle. | Retain one selected root owner, not one per workspace. |
| mode, native mode, preflight | ADMINISTRATIVE | Selects/guards backend posture. | Extend from one profile to active root profile. |
| data directory, locks | NOT_MEMORY_SEMANTIC | Infrastructure only. | Profile/generation-aware invalidation if cached. |
| kernel | EXTERNAL_OWNER_PORT | Fabric-owned existing cognition and embedder. | Keep one owner; validate lane against active root agreement. |
| Native get_workspace | NATIVE_OWNED read-model resolution | Produces inert native workspace view and refuses domain mutation. | Resolve active members through root membership. |
| Native create_agent | EXTERNAL_OWNER_PORT / refusal | Refuses seed creation; prepares existing external identity only. | Remain non-creating; lifecycle administration creates a scope. |
| Native ingest and tool-result ingest | NATIVE_OWNED | Validates route, receipt, Fabric preparation, native executor/router. | Resolve scope by full key. |
| Native query/query-memory | NATIVE_OWNED storage adapter plus EXTERNAL_OWNER_PORT cognition | Injects native read model/view/identity into Fabric query. | Generalize reader/caches by full key; retain Fabric math. |
| Native private_graphs | ADMINISTRATIVE safety refusal | Rejects legacy MemoryGraph access. | Retain refusal. |
| Native public mutation receipt store | NATIVE_OWNED recovery evidence | Persists reservation/prepared/complete evidence only. | Select private namespace by workspace/private-agent/agent. |
| Base __getattr__, including unlisted graph, feedback, proposal, trace/retrieve-like, administration, and future Fabric calls | LEGACY_FALLTHROUGH | Unknown public names delegate to Fabric. | Give every surface named native, external-port, administrative, or refusal disposition. |

The explicit native allowlist is ingest, tool-result ingest, and query-memory.
That prevents accidental legacy storage and proves fallthrough retirement is
not complete.

## 4. R0-2 — Workspace semantics

The workspace is the enclosing semantic/process boundary:

- private agent state uses Fabric agent key workspace plus agent;
- shared domain graph/motif/policy/bridge/proposal/conflict structures are
  workspace-local;
- identity, role, character, derived side state, timers, and agent process
  state use workspace plus agent;
- collective/Hivemind state uses workspace because it is a workspace collective;
- world and SRG use the selected request workspace/scope in post-write.

Legacy get_workspace and create_agent are materializing operations, not lookups.
They can create workspace metadata, domains, shared structures, identity, role,
private graph, and seed/character state. Ordinary legacy query calls them when
native adapters are absent. Active native public paths must retain their
injected native workspace/identity/read-model path and never invoke these lazy
creation routes.

Request invariant:

~~~
request workspace = W
every private/shared lane read has workspace = W
every post-write external state access uses W and request agent/domain
~~~

The existing native query checks recovered scopes against requested workspace
and ranks only its workspace domains. Ordinary cross-workspace retrieval does
not exist. Any future cross-workspace cognition must be an explicit operation
with named contributing RootScopeKeys and provenance; it cannot arise from a
bare lookup, cache, or fallback.

## 5. R0-3 — Scope model and exact generalization

| Component | Current identity | System fit |
|---|---|---|
| NativeMemoryRuntimeScope | Workspace, private/shared kind, qualifier, source/identity/semantic namespaces | Already expresses RootScopeKey; retain. |
| NativeFabricRoutingScope | Runtime scope plus motif alias/identity, membership identity, idempotency namespaces | Correct scope carrier; retain. |
| NativeFabricMemoryRouter | Claims/routes workspace, kind, qualifier | Correct routing seam; provide root-wide capability. |
| Native vector runtime | Core plus complete scope/namespaces/lane | Already lane-local; retain. |
| NativeProductionResourceOwner | One selected root/core owner | Correct owner shape, but recovery is one-profile. |
| Native motif process order | Full routing key plus domain/motif namespace | Correctly qualified. |
| Native SRG state | Core/source namespace/EID/revision | Correct after membership supplies namespace. |
| Native world state | Core/source namespace | Correct after membership revalidation. |

Current recovered runtime operations are equivalent to:

~~~
lookup_private(agent_id)
lookup_shared(domain_id)
~~~

They match kind and bare qualifier. Workspace comparison is too late. Two
workspaces that share an agent or domain name are not safe.

Required root recovery operations:

~~~
lookup_scope(RootScopeKey) -> ActiveRootMemberScope
lookup_private(workspace_id, agent_id) -> ActiveRootMemberScope
lookup_shared(workspace_id, domain_id) -> ActiveRootMemberScope
list_workspace_members(workspace_id) -> ordered active members
~~~

ActiveRootMemberScope may wrap current recovered scope but must be obtained from
the active root membership relationship and bind core id, profile/deployment
generation, complete key, namespace bundle, lane, and external witness.

## 6. R0-4 — Query preservation

Current native public query route:

~~~
public query(W,A,text)
  -> native preflight
  -> prepare existing external identity W/A, with no graph creation
  -> recover native runtime and workspace view
  -> NativeQualifiedQueryReadModel with native vector readers
  -> Fabric query with injected native reader/view/identity
  -> existing MAIN_TORMENT_COGNITION math
  -> close request-local readers
~~~

Fabric remains query-cognition owner for embedding, domain ranking, score
composition, motif/SRG/character/role effects, governance, and response
assembly. Native code supplies qualified storage reads.

| Component | Classification | Required change |
|---|---|---|
| Fabric query/scoring/composition | Existing cognition owner | Direct reuse. |
| NativeQualifiedQueryReadModel | Native storage adapter | Full-key maps/lookups. |
| Native vector reader/runtime | Native storage adapter | Reuse after membership resolution. |
| Native motif reader/geometry | Native storage adapter using shared motif math | Reuse full routing scope. |
| Legacy MemoryGraph/workspace construction/ordinary query | Legacy storage adapter | Never call in active native request. |
| Kernel, role/character stores, Fabric process state | External-owner/existing cognition dependencies | Verify profile identity and workspace/agent key. |

No root query v2 is needed.

## 7. R0-5 — Post-write semantic map

| Consumer/state | Math owner | Durable owner today | Current native status | Root-native disposition |
|---|---|---|---|---|
| Canonical conflict | Fabric detector and legacy ordering | Per-domain legacy conflict files | Public native conflicts are read-only; append is skipped after caught exception. | If live in the frozen production profile, activation is blocked until a qualified conflict writer preserves it; only explicit policy evidence of inapplicability removes that blocker. |
| SRG collision | Existing SRG engine | Legacy payload historically; native transient overlay | Qualified access/overlay exists. | Reuse exact calculation with core/namespace/EID/revision witness. |
| Hivemind | Existing post-write logic | Workspace collective/proposal bridge | Adapter exists; shared integrated route is staging. | Named workspace external owner plus source key/profile provenance. |
| Motif maintenance/merge | Shared motif decision/geometry policy | Native motif carriers for native route | M1/M2/shared capability exists, public profile bounded. | Qualified profile and membership route. |
| Derived anchor/affect/mood | Existing derived-memory law | Native derived objects plus external anchor/affect state | Compatibility port; shared mood requires explicit private target. | Full target key and external workspace/agent witness. |
| World | Existing world runtime | External/process state | Native port exists. | Request workspace and validated namespace only. |
| Character drift/gravity | Existing character behavior | CharacterStore plus native observations | Base public profile marks unsupported. | If live in the frozen production profile, activation is blocked until exact drift/gravity behavior is preserved; only explicit policy evidence of inapplicability removes that blocker. |
| Checkpoint/trajectory | Existing writers | External artifacts | Base profile bounded; D3/D4 staged. | Named external owner and full scope/profile provenance. |
| Compression/deep memory | Existing policy | Legacy deep/compression state | Base profile disabled/no-op. | Prove disabled or retain/port exact owner. |
| Proposals | Existing eligibility/registry behavior | Legacy proposal/identity/collective state | Public native proposal allowed is false. | Named port or explicit policy prohibition. |
| Bridge suggestions | Existing suggestion/geometry logic | Workspace/domain external bridge data | B1/E1 staging capability. | Same-workspace source/target plus named external owner. |
| Public mutation recovery | Receipt protocol, not cognition math | Native operation ledger/private idempotency namespace | Native but bare-agent recovery seam. | Full private-key lookup. |

An active root profile must state every row. Unsupported/no-op is lawful only if
the active production policy makes the legacy effect inapplicable; it cannot
silently remove a live effect.

~~~
CONFLICT_PERSISTENCE_NOT_PRESERVED = ACTIVATION_BLOCKER
CHARACTER_DRIFT_GRAVITY_NOT_PRESERVED = ACTIVATION_BLOCKER
~~~

These gates apply whenever the frozen active production profile uses the named
TORMENT behavior. More generally: **every currently live production effect
must survive native activation.** Native post-write parity therefore covers
every effect enabled by that policy, potentially including reinforcement,
derived memory, motif attach/create, motif split/merge where qualified,
Character seed, Character drift, Character gravity, direct shared ingest,
proposal/materialization, conflict behavior, trajectory evidence, world state,
and SRG state. This list does not assert that every effect is currently enabled.

## 8. R0-6 — Mathematical duplication

TORMENT_MATHEMATICS_PRESERVED = YES.
MATHEMATICAL_FORMULA_CHANGES_REQUIRED = NO.
MATHEMATICAL_FORMULA_DUPLICATES_PRESENT = YES.

The formally identified duplicate debt is limited to these three areas. This
classification does not authorize consolidation during R0C and does not make a
duplicate a second cognition owner.

| Duplicate area | Current semantic owner | Duplicate owner | R0C disposition |
|---|---|---|---|
| Domain cosine ranking and stable ordering | MAIN_TORMENT_COGNITION Fabric query | Native domain router over qualified geometry | Preserve exact behavior; record future parity before any consolidation. |
| Vector normalization and half-life decay | MemoryGraph compatibility law used by MAIN_TORMENT_COGNITION | Native vector compatibility runtime | Preserve exact numerical/replay behavior. |
| Derived thresholds and gates | Fabric derived-memory behavior | Native derived-memory compatibility runtime | Preserve exact thresholds/gates; only storage realization may differ. |

For each duplicate, a future convergence record is mandatory and must name:

~~~
CURRENT_SEMANTIC_OWNER
DUPLICATE_OWNER
NAMED_PARITY_TEST
RETIREMENT_GATE
EVENTUAL_SURVIVOR
~~~

Its named parity test must cover numerical representation, ordering, stable
ordering, ties, and replay, as well as input/output and error behavior for
every applicable private/shared scope. Until that record passes, both forms are
qualification machinery and neither may be silently changed or retired.

ONE_ACTIVE_TORMENT_QUERY_COGNITION_IMPLEMENTATION = YES is the convergence
objective. It means one active MAIN_TORMENT_COGNITION implementation, not a
claim that every repository-resident cognitive-looking function is one system.

## 9. R0-7 — Cache/lookup safety

| Current map/lookup | Current key | Root-wide rule |
|---|---|---|
| Recovered private/shared lookup | Bare qualifier | Replace with RootScopeKey. |
| Query reader private/shared lanes | Bare agent/domain | Full key or workspace child map pinned to root generation. |
| Private motif-domain map/shared domain order | Bare agent/domain | Full key or explicit workspace partition. |
| Receipt scope recovery | Bare private lookup then workspace comparison | Atomic lookup_private(W,A). |
| Public workspace view | Workspace only | Key/invalidate by core, profile generation, workspace, membership revision. |
| Fabric private maps | Workspace plus agent | Correct private key; retain within profile generation. |
| Collective/proposal maps | Workspace | Workspace-local, but profile-generation-valid. |
| Native vector | Full scope/lane | Already safe; rebuild on membership/profile mismatch. |
| Any EID-addressed cache, lookup, alias, or SRG access | Numeric EID alone is insufficient | Resolve active membership first, then require workspace, semantic scope, source namespace, and EID; retain current revision where the consumer requires it. |
| SRG/world/motif state | Namespace-qualified | Retain; recover membership before opening. |

A process cache is not authority. It must recover active durable membership
before opening any native reader or writer.

### Numeric legacy EID isolation

~~~
NUMERIC_LEGACY_EID_IS_NOT_ROOT_GLOBAL = YES
~~~

An EID-addressed operation is only lawful after qualification by its workspace,
semantic scope, and source namespace. The same numeric EID may lawfully exist
in different workspaces or scopes:

~~~
workspace_A / eid_42 != workspace_B / eid_42
~~~

No root cache, alias map, recovery route, vector lookup, motif lookup, or SRG
operation may treat numeric EID as a root-global identity or cross-scope alias.
Where a caller also requires current object state, the revision witness remains
part of the key as it already is for native SRG.

## 10. R0-8 — Root-scope membership primitive

ROOT_SCOPE_MEMBERSHIP_PRIMITIVE = EXISTING_SCHEMA_RELATIONSHIP.

The existing native schema has immutable object revisions, relationship
revisions/endpoints, namespaces, semantic scopes, idempotency namespaces, and
semantic transactions. NativeRelationshipService can carry membership. A new
table or parallel registry is neither required nor desirable.

Root-scope membership owns exactly one semantic/runtime fact:

> This semantic memory scope is currently a lawful member of this root-native
> profile generation.

The relationship may retain only relationship/lifecycle facts required to
establish that fact: root/core generation identity, RootScopeKey identity,
external identity witness, lifecycle, and idempotency/recovery lineage.

It must not duplicate ownership of the complete namespace bundle or a
per-member representation lane. Existing namespace and semantic-scope
structures remain owners of their identifiers. The target representation lane
is a root-profile fact, not a membership fact. Membership also must not
duplicate memory objects, EIDs, vectors, selector facts, or external identity
files.

The existing schema relationship carrier remains the frozen direction. The
exact endpoint carrier is deliberately not frozen as a new permanent
abstraction. A root-profile control object may be needed to identify a profile
endpoint, but a separate scope-binding control object is only a candidate
compatibility carrier. Before implementation it must pass this test:

> No new runtime abstraction survives merely to repackage identity facts
> already owned elsewhere.

The same ownership/retirement gate applies to ActiveRootMemberScope. It is a
temporary compatibility-wrapper name in this archaeology, not a declared
surviving runtime type. A future design record must decide, with evidence,
whether generalized native scope identity can replace it; otherwise it must
name the unique runtime responsibility that justifies survival.

Scope retirement must define one crash-safe protocol for membership lifecycle,
runtime publication/removal, cache invalidation, recovery, and idempotency.
Durable lifecycle transition is authoritative; process publication/removal must
revalidate it before making a scope addressable. No half-retired scope may
remain addressable as active, and retirement never erases predecessor evidence.

## 11. R0-9 through R0-13 — Activation, creation, identity, atomicity

Future activation treats frozen 9A/9C description/admission evidence as input,
not a mutable registry. It creates root-profile membership relations for each
actually admitted scope and records the frozen evidence digest. Later creation
never edits that description.

| Legacy lazy path | Side effect | Active native rule |
|---|---|---|
| New get_workspace | Workspace metadata/default domain/shared structures | Refuse as lookup; authorized lifecycle operation only. |
| Missing domain passed to get_workspace | Appends declaration/shared structures | Refuse in query/ingest; authorized shared creation only. |
| create_agent | Identity/role/private graph, possible seed/character state | Native public call remains preparation-only. |
| Legacy query without injected adapters | Calls workspace/agent construction | Never reachable from native public query. |
| Legacy ingest | Can construct/write legacy state | Never reachable from native public ingest. |

| Scope/action | Existing witness | Required gate |
|---|---|---|
| Existing workspace | Workspace metadata/tree | Exact identity. Metadata-less historical evidence is not new-creation authority. |
| New workspace | No qualified native authority today | Explicit external administration and durable witness. |
| Existing private agent | IdentityStore, role/character as active | Exact workspace/agent identity before membership. |
| Character | CharacterStore and seed owner | Exact seed/state witness when active. |
| Existing shared domain | Domain declaration/policy | Exact workspace/domain declaration/policy witness. |
| New shared domain | No qualified native authority today | Authorized external declaration/policy witness. |
| Root/lane | Selector/core/profile/embedder agreement | Revalidate at preflight and transaction. |

Lawful post-activation creation, after Phase 0 policy freezes:

1. Receive authorized administrative request, idempotency key, complete
   RootScopeKey.
2. Recover/revalidate active selector, core, profile generation, lane, lifecycle.
3. Reject duplicate, retired, conflicting, unpermitted, or cross-workspace scope.
4. Verify external identity/policy witness; native code never mints it.
5. Build deterministic witness and membership plan that references
   separately-owned namespace/scope identities and the root-profile lane.
6. In one native SQLite semantic transaction create/verify only the necessary
   relationship control carrier, membership relationship, and idempotency
   operation; do not introduce a scope-binding abstraction unless its unique
   responsibility has passed the stated ownership gate.
7. Commit before process-cache publication; recover durable membership and open
   request-local handles.
8. Revalidate profile/membership on later requests; mismatch refuses and never
   falls back to legacy creation.

SQLite facts are atomic together. External identity is not secretly atomic with
SQLite: its owner acts first, membership stores immutable witness facts, and a
later mismatch withholds/refuses membership rather than rebinding it.

SEMANTIC_ADAPTER_OWNERSHIP != DURABLE_STORE_OWNERSHIP. Native adapters may
transport or translate TORMENT semantics without absorbing external stores into
SQLite. Where active policy requires them, durable ownership remains with the
applicable CharacterStore, role state, BridgeRegistry, ConflictRegistry,
proposal/workflow state, checkpoint/trajectory state, deep memory, Hivemind,
and world/SRG process state.

POST_ACTIVATION_SCOPE_CREATION = POLICY_REQUIRED. Mechanics are clear; the
trusted external actor and revocation/recovery contract for new workspace,
private-agent, and shared-domain membership is not yet defined.

When a root-native agreement is active, legacy lazy get_workspace/create_agent
style materialization must be structurally prohibited from becoming an
accidental fallback. Caller discipline alone is insufficient: future
implementation should prefer refusal at the legacy callee or another
centralized enforcement point that can see the active native agreement.

## 12. R0-14/R0-15 — First write and empty shared domains

First write follows ordinary native flow:

~~~
Fabric prepare-only cognition
  -> full RootScopeKey membership
  -> NativeFabricMemoryRouter
  -> native source/representation/motif realization
  -> qualified post-write composition
~~~

There is no special first-memory cognition. Empty motif catalog behavior,
duplicate/reinforcement, normalization, ranking, SRG, and post-write gates keep
their current rules.

| Domain state | Meaning | Rule |
|---|---|---|
| DECLARED_UNMATERIALIZED historical anomaly | Domain declaration without materialized shared legacy structure | Evidence only; never auto-route or auto-create native membership. |
| Initial admitted shared scope | Existing qualified root-description scope | Member only during future activation. |
| New shared domain | Authorized declared workspace/domain | Create MATERIALIZED_EMPTY_SHARED_SCOPE: namespaces/lane and zero memories/motifs, no legacy graph/artifact. |
| Retired/withheld | Historical/invalid member | Refuse routing, retain evidence. |

New shared domain materialization is not Workspace.add_domain and is not
deferred to first query.

## 13. R0-16/R0-17/R0-18 — World, SRG, character, motifs

World/SRG remain scope-local. World opens only through selected membership's
source namespace; SRG remains core/source-namespace/EID/revision keyed. No
global world or cross-workspace SRG cache is supported by current semantics.

Character seed/state remains externally owned. Private native use requires full
private membership, IdentityStore witness, active CharacterStore seed/state
witness with matching seed owner, and character-qualified profile. The base
public native profile currently marks character unsupported, so activation
cannot claim character parity until it selects/qualifies that behavior or
proves it disabled by active policy.

Native motif runtime is generally fit when it receives full routing scope:
catalogs restrict alias namespace/domain/semantic scope; members use native
object identity; composition reuses existing motif law; maintenance keys include
routing scope/namespaces. No global motif registry is permitted.

Automatic motif split is not asserted universally qualified by this record.
Before an active profile treats auto-split as guaranteed native behavior, its
standing qualification status, parity evidence, and recovery disposition must
be explicitly confirmed. This is a qualification gate, not new motif math.

## 14. R0-19/R0-20 — Fallthrough and legacy retirement

Public fallthrough retirement:

1. Freeze an explicit census of every public surface reachable through legacy
   fallthrough, including its discovery method and denominator.
2. Classify every censused delegated operation as native, named external owner,
   administration, or refusal.
3. Preflight before Fabric access; native query/ingest inject adapters and
   unsupported calls cannot reach __getattr__.
4. Qualify recovery/retry/non-interference.
5. Remove or refuse __getattr__ only after the complete frozen census has been
   replaced or explicitly retired.

~~~
PUBLIC_FALLTHROUGH_CENSUS_REQUIRED = YES
PUBLIC_FACADE_LEGACY_FALLTHROUGH = REMOVED (eventual target only)
~~~

No future claim ALL_PUBLIC_SURFACES_EXPLICIT = YES is valid without the frozen
census denominator. Native-active entry must also be structurally prevented
from re-entering legacy lazy materialization; enforcement belongs at a
centralized boundary, preferably the legacy callee when it can observe an
active root-native agreement, rather than relying on every caller.

Legacy graph/workspace/motif/query/ingest structures remain evidence and
rollback/reference material until every active member has full-key recovery,
native no-fallback query, complete post-write disposition including conflicts,
no fallthrough, authorized creation, external/lane gates, and successful
production-shaped restart/isolation rehearsal. Retirement is later lifecycle
work and does not delete legacy evidence.

## 15. R0-21/R0-22 — Phase 0 policy gates and eventual convergence

Architecture is frozen after R0C, but implementation is not the next action.
It is blocked on these two specification/policy decisions, which must not be
opportunistically mixed into implementation phases.

### Phase 0A — EXTERNAL_SCOPE_CREATION_AUTHORITY

Freeze the named external authority allowed to create a workspace, attest a
private-agent identity, and declare a shared domain. Define its witness,
authorization, revocation, and recovery contract.

> SQLite/native memory code may not invent external identity from request
> strings.

Post-activation scope creation remains blocked until this authority is frozen.

### Phase 0B — ACTIVE_PRODUCTION_POST_WRITE_PROFILE

Freeze which bounded TORMENT post-write behaviors are enabled in the intended
active production profile. This determines parity requirements for conflict
persistence, Character drift, Character gravity, and every other conditional
post-write behavior.

> A currently live TORMENT effect must be preserved unless explicit
> production-policy evidence proves it inapplicable.

Only after Phase 0A and 0B may an implementation order be selected: relationship
membership/recovery, full-key public/query generalization, centralized
fallthrough fencing, parity qualification, lawful lifecycle creation, and
production-shaped rehearsal. No actual implementation starts in this record.

The eventual convergence targets are doctrine, not achieved-state claims:

~~~
ONE_ACTIVE_TORMENT_QUERY_COGNITION_IMPLEMENTATION = YES
ONE_POST_WRITE_SEMANTIC_IMPLEMENTATION = YES
ONE_ACTIVE_MEMORY_AUTHORITY = YES
ONE_NATIVE_PUBLIC_RUNTIME_PATH = YES
ACTIVE_LEGACY_MEMORY_QUERY_AUTHORITY = NO
ACTIVE_LEGACY_MEMORY_WRITE_PATH = NO
PUBLIC_FACADE_LEGACY_FALLTHROUGH = NO
ONE_REQUEST_COGNITIVE_WORKSPACE = YES
~~~

Root-wide durable storage must not become root-wide cognition. Complete scope
identity protects the same agent_id across workspaces, the same domain_id
across workspaces, and the same numeric EID across workspaces/scopes.

## 16. Required verdicts

~~~
ROOT_NATIVE_RUNTIME_DIRECTION = CORRECTIONS_REQUIRED
ROOT_SCOPE_MEMBERSHIP_PRIMITIVE = EXISTING_SCHEMA_RELATIONSHIP
QUERY_COGNITION_PRESERVATION = BOUNDED_GENERALIZATION
POST_WRITE_COGNITION_PRESERVATION = BOUNDED_GENERALIZATION
POST_ACTIVATION_SCOPE_CREATION = POLICY_REQUIRED
ROOT_NATIVE_RUNTIME_ARCHITECTURE_FROZEN = YES
TORMENT_MATHEMATICS_PRESERVED = YES
MATHEMATICAL_FORMULA_CHANGES_REQUIRED = NO
MATHEMATICAL_FORMULA_DUPLICATES_PRESENT = YES
PUBLIC_FALLTHROUGH_RETIREMENT_PATH = PARTIAL
CONFLICT_CHARACTER_ACTIVATION_GATES_RECORDED = YES
NUMERIC_LEGACY_EID_IS_NOT_ROOT_GLOBAL = YES
PUBLIC_FALLTHROUGH_CENSUS_REQUIRED = YES
PHASE_0_POLICY_GATES_RECORDED = YES
ONE_REQUEST_COGNITIVE_WORKSPACE = YES
BLOCKER_5_REOPEN_REQUIRED = NO
IMPLEMENTATION_READY_AFTER_CORRECTIONS = YES
REAL_PRODUCTION_ACTIVATION = NOT_AUTHORIZED

CODE_CHANGES = 0
TEST_CHANGES = 0
REAL_ROOT_CONTACT = NO
BRAINVISION_FILES_READ = 0
BRAINVISION_FILES_TOUCHED = 0
BRAINVISION_DATA_READ = 0
BRAINVISION_EVIDENCE_READ = 0
BRAINVISION_COGNITION_READ = NO
BRAINVISION_COGNITION_TOUCHED = NO
BRAINVISION_COGNITION_USED_AS_TORMENT_EVIDENCE = NO
COGNITION_AUTHORITY_DISAMBIGUATED = YES
R0_ARCHITECTURE_VERDICTS_CHANGED = NO
SECOND_REPOSITORY_COGNITIVE_FUNCTION_INSPECTED = NO
~~~

CORRECTIONS_REQUIRED does not reject the root-native direction. It means
activation is premature until known recovery, post-write, public fallthrough,
and creation-policy gaps are closed. R0C freezes the corrected architecture,
so implementation is ready only after the separate Phase 0 policy decisions;
it is not authorized now. Blocker-5 remains the correct selector/core
foundation and does not need reopening.

## 17. Open policy decisions

1. Which named external administrative authority may create a workspace,
   declare a shared domain, and attest a private agent for post-activation
   membership? Its witness, authorization, revocation, and recovery contract
   need definition; public create_agent/get_workspace are intentionally not
   that authority.
2. Which bounded post-write behaviors are enabled in the active production
   profile, especially conflict persistence, character, proposals, bridges,
   checkpoint/trajectory, and compression/deep memory? Each enabled behavior
   needs a qualified native or named external owner; each disabled behavior
   needs explicit policy evidence.

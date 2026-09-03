# TORMENT Memory Substrate — Phase 9D I1

## Root-scope membership and root-qualified runtime identity

**Status:** qualified isolated implementation slice.  No real root, service,
provider, re-embedding, selector change, or production activation was used.

## 0. Scope and non-interference

I1 implements the identity rails required to represent this single fact:

> This already-qualified semantic memory scope is currently a lawful member of
> this root-native profile generation.

The implementation does not create a workspace, agent, domain, legacy graph,
external identity, external authority, selector, core, representation lane, or
query/post-write behavior.  It does not change MAIN TORMENT COGNITION or any
kernel, Character, motif, SRG, reinforcement, or query-ranking mathematics.

```text
QUERY_COGNITION_CHANGED = NO
POST_WRITE_COGNITION_CHANGED = NO
CHARACTER_BEHAVIOR_CHANGED = NO
MOTIF_MATH_CHANGED = NO
KERNEL_MATH_CHANGED = NO
SRG_MATH_CHANGED = NO
TORMENT_MATHEMATICS_PRESERVED = YES

REAL_ROOT_CONTACT = NO
REAL_MEMORY_MODEL_CONTACT = 0
SERVICE_START = NO
REAL_PRODUCTION_ACTIVATION = NO
```

## 1. Implemented owner and durable relationship

`RootScopeMembershipService` in
`torment_service/substrate/root_scope_membership.py` uses the existing
`NativeRelationshipService` and immutable relationship revisions.  It creates
no table, schema migration, or parallel durable registry.

The relationship owns only membership lifecycle and evidence necessary for the
fact above:

```text
ROOT_SCOPE_MEMBERSHIP_KIND = ROOT_SCOPE_MEMBERSHIP
relationship endpoint = exact root-profile control-object revision
effective semantic scope = admitted scope semantic_scope_id
payload = contract, root core/profile generation, RootScopeKey, witness reference/digest
lifecycle = ACTIVE | RETIRED
```

The relationship does not own or copy the complete namespace bundle, target
representation lane, workspace metadata, agent/domain identity, Character
state, motif state, memory objects, numeric EIDs, query cognition, or external
authority.

`RootScopeMembershipWitness` is shape-validated immutable evidence only.  It
does not mint or validate an external authority.  Its production authority and
revocation semantics remain the P0 named-external-admission-owner gate.

## 2. Root-qualified identity and runtime binding

Existing `RootScopeKey` remains the canonical workspace-local scope identity:

```text
PRIVATE = workspace_id + PRIVATE + agent_id
SHARED  = workspace_id + SHARED + domain_id
```

`RootProfileGenerationRef` identifies an existing root-profile control-object
revision plus core/profile generation.  It is a reference, not the owner of
the profile fact.  `RootQualifiedRuntimeKey` owns the combined runtime-cache
identity:

```text
core_id + profile_generation + profile_revision_id + profile_revision_ordinal
+ workspace_id + scope_kind + qualifier
```

`RootQualifiedMemberScope` is the surviving generalized runtime abstraction.
Its single responsibility is binding one recovered active relationship to the
existing `NativeMemoryRuntimeScope` resource supplied by the qualified runtime
descriptor.  Namespace ownership remains with that existing scope resource.

The prior `ActiveRootMemberScope` name was archaeology-only and was not a
production type.  It is therefore redundant rather than a retained compatibility
wrapper:

```text
ACTIVE_ROOT_MEMBER_SCOPE_DISPOSITION = REDUNDANT_ARCHAEOLOGY_NAME
SEMANTIC_OWNER = RootQualifiedMemberScope
RETIREMENT_GATE = NOT_APPLICABLE
EVENTUAL_SURVIVOR = RootQualifiedMemberScope
```

## 3. Resolution, cache, and lifecycle discipline

`RootScopeMembershipRuntime` is the sole I1 native resolver.  It accepts only
a complete `RootScopeKey` (or the complete private/shared convenience inputs),
recovers relationship state, validates it against supplied existing native
scope resources, and returns a `RootQualifiedMemberScope`.

```text
absent scope  -> RootScopeMembershipAbsent
retired scope -> RootScopeMembershipRetired
ambiguous/conflicting durable state -> RootScopeMembershipConflict
```

It imports neither Fabric nor legacy workspace/agent/graph construction.  A
scope lookup cannot invoke `get_workspace` or `create_agent` as a fallback.

The process cache uses only `RootQualifiedRuntimeKey`.  It is recovered from
committed relationship revisions on every resolution.  Publication therefore
happens only after the relationship transaction commits; cold cache recovery
reconstructs active members; and a retirement is observed before a later
resolution can return the old active member.

Retirement is a normal immutable relationship successor revision.  It retains
predecessor evidence while changing the authoritative lifecycle to `RETIRED`.
No active cache entry survives a subsequent resolution after that durable
transition.

## 4. EID isolation

I1 does not allocate EIDs.  `RootQualifiedMemberScope.legacy_eid_key()` creates
an identity key that includes root/profile, complete scope, the scope's existing
legacy source namespace, numeric EID, and optional object revision.

```text
NUMERIC_LEGACY_EID_IS_NOT_ROOT_GLOBAL = YES
EID_UNIQUENESS_SCOPE = LEGACY_SOURCE_NAMESPACE
ROOT_GLOBAL_EID_ALLOCATOR_REQUIRED = NO
```

## 5. Qualification inventory

Focused synthetic SQLite fixtures exercised only explicit test witnesses and
existing substrate primitives.

| Requirement | Evidence |
|---|---|
| Private collision isolation | Same `agent-7` in two workspaces resolves to distinct members/cache keys. |
| Shared collision isolation | Same `research` domain in two workspaces resolves to distinct members. |
| Numeric EID isolation | Same numeric EID produces distinct keys across source namespaces/scopes. |
| Idempotency | Replaying identical qualified membership/witness returns the existing relationship. |
| Admission race fence | A membership that appears between the initial read and the write transaction is recovered, not duplicated. |
| Contradiction | Changed immutable witness facts for the same member fail closed. |
| Absent scope | Resolution refuses with no object or relationship materialization. |
| Retirement | A warm resolver refuses a member after durable retirement. |
| Restart/recovery | Active members recover; retired members remain retired; no identity is recreated. |
| Publication/cache ordering | A member is not resolvable until its completed admission returns; every later resolve revalidates durable state. |

Focused I1 tests: `11 passed`.

Directly affected substrate relationship/root-identity regressions:
`13 passed`.

## 6. Remaining boundaries and gates

```text
NEW_EXTERNAL_AUTHORITY_COMPONENT_CREATED = NO
NAMED_EXTERNAL_ADMISSION_OWNER_AND_WITNESS = OPEN
FULL_DURABLE_OWNER_CENSUS = OPEN
PUBLIC_FALLTHROUGH_CENSUS_AND_RETIREMENT = OPEN
CONFLICT_NATIVE_PARITY_IF_APPLICABLE = OPEN
CHARACTER_NATIVE_PARITY_IF_APPLICABLE = OPEN
GEOMETRY_DERIVED_EXTERNAL_STATE_DISPOSITION = OPEN
REAL_PRODUCTION_PROFILE_MATCH = OPEN
REAL_ROOT_ACTIVATION = NOT_AUTHORIZED
```

No temporary duplicate durable owner was introduced.  Future work may wire this
resolver into public/query/post-write runtime slices only after each slice has
its own authorized preservation and qualification evidence.

## 7. Final verdicts

```text
PHASE_9D_I1_ROOT_SCOPE_MEMBERSHIP = PASS
ROOT_SCOPE_MEMBERSHIP_PRIMITIVE = QUALIFIED
ROOT_QUALIFIED_RUNTIME_IDENTITY = QUALIFIED
PRIVATE_SCOPE_COLLISION_ISOLATION = PASS
SHARED_SCOPE_COLLISION_ISOLATION = PASS
EID_SCOPE_ISOLATION = PASS
ABSENT_SCOPE_NON_MATERIALIZATION = PASS
MEMBERSHIP_IDEMPOTENCY = PASS
MEMBERSHIP_RETIREMENT = PASS
MEMBERSHIP_RECOVERY = PASS
RUNTIME_CACHE_SCOPE_ISOLATION = PASS

QUERY_COGNITION_CHANGED = NO
POST_WRITE_COGNITION_CHANGED = NO
TORMENT_MATHEMATICS_PRESERVED = YES
BLOCKER_5_REOPEN_REQUIRED = NO
REAL_PRODUCTION_ACTIVATION = NOT_AUTHORIZED
```

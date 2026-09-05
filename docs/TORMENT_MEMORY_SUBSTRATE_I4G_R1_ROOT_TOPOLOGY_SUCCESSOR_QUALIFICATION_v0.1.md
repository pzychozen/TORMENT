# TORMENT Memory Substrate — I4G-R1 Root Topology Successor Qualification

## Status

~~~text
FROZEN_SUCCESSOR_TOPOLOGY_CONTRACT

IMPLEMENTATION_NOT_YET_QUALIFIED

REAL_ROOT_OBSERVATION_NOT_AUTHORIZED
REAL_ROOT_WRITE_NOT_AUTHORIZED
WRITER_FREEZE_NOT_AUTHORIZED
ACTIVATION_NOT_AUTHORIZED
~~~

## Purpose and frozen predecessors

This document freezes the I4G-R1 successor topology contract. It qualifies the
semantic public topology that a later implementation qualification must
realize; it does not implement, activate, or admit that topology.

It is a successor to, and does not alter, the frozen I4G result in
[TORMENT_MEMORY_SUBSTRATE_PHASE_9D_I4G_FINAL_PUBLIC_LIFECYCLE_CAPABILITY_PARITY_v0.1.md](TORMENT_MEMORY_SUBSTRATE_PHASE_9D_I4G_FINAL_PUBLIC_LIFECYCLE_CAPABILITY_PARITY_v0.1.md).
The real-root observations used as predecessor evidence remain frozen in
[TORMENT_MEMORY_SUBSTRATE_POST_I4_REAL_ROOT_READ_ONLY_PREFLIGHT_v0.1.md](TORMENT_MEMORY_SUBSTRATE_POST_I4_REAL_ROOT_READ_ONLY_PREFLIGHT_v0.1.md).
The adversarial topology review named
TORMENT_I4G_R1_ROOT_TOPOLOGY_SEMANTIC_ADVERSARIAL_REVIEW.md is retained as
review evidence for this decision.

~~~text
REQUIRED_STARTING_HEAD = 6afa41e21d0e137bc93cddfc34891110104c7004

I4G_FROZEN_RESULT_REMAINS_TRUE = YES
REAL_ROOT_READ_ONLY_PREFLIGHT = PASS
ROOT_V2_LAYOUT_EXPRESSIBILITY = YES
FULL_ROOT_SCOPE_KEY_UNIQUENESS = PASS

REAL_ROOT_PUBLIC_TOPOLOGY =
    DOES_NOT_MATCH_CURRENT_QUALIFIED_PROFILE
~~~

I4G-R1 broadens only the former bounded public-workspace topology assumption
of exactly one private scope and at least one shared scope. It does not rewrite
I4G evidence for that original shape.

## Frozen successor public topology

~~~text
PUBLIC_WORKSPACE:

private PUBLIC scopes = 0..n
shared PUBLIC scopes  = 1..n

private identity =
    (workspace_id, PRIVATE, agent_id)

shared identity =
    (workspace_id, SHARED, domain_id)

shared order =
    explicit frozen admitted order
~~~

Consequently:

~~~text
I4G_R1 = SUCCESSOR_TOPOLOGY_QUALIFICATION

MULTI_PRIVATE_LAWFUL_TORMENT_BEHAVIOR = YES
MULTI_PRIVATE_ROOT_ROUTING_PRIMITIVE =
    ALREADY_SUPPORTED

MULTI_SHARED_LAWFUL_TORMENT_BEHAVIOR = YES
ZERO_PRIVATE_WORKSPACE_LAWFUL = YES
~~~

A private scope is identified by the complete
RootScopeKey(workspace_id, PRIVATE, agent_id). A shared scope is identified by
the complete RootScopeKey(workspace_id, SHARED, domain_id). There is no
root-global bare-qualifier lookup in the successor contract.

Multiple existing, admitted private agents in one workspace are lawful.
Recovery of those scopes is a qualified target; it is not authority to create
another scope after activation.

~~~text
RECOVER_EXISTING_ADMITTED_PRIVATE_SCOPES = QUALIFIED_TARGET

CREATE_NEW_UNADMITTED_PRIVATE_SCOPE = REFUSED
NEW_UNADMITTED_SCOPE_CREATION = REFUSED
~~~

Multiple admitted shared domains are likewise lawful. Their routing order must
be explicit, frozen, and deterministic.

## Shared-lane structural law and zero-shared policy

The following architecture-lead decision is frozen:

~~~text
ZERO_SHARED_RESOLUTION =
    PRE_FREEZE_LEGACY_MATERIALIZATION

DISCOVERY_AMENDMENT_FOR_ZERO_SHARED =
    NOT_SELECTED_FOR_INITIAL_PROFILE

PRIVATE_ONLY_PUBLIC_WORKSPACE =
    NOT_LAWFUL
~~~

For the initial native public profile, a public workspace must have at least
one shared public lane. A shared lane may have zero memory objects; it is still
structural to query routing and composition, private-ingest domain routing,
motif-registry attachment, and domain-scoped proposals and conflicts.

~~~text
PRIVATE_QUERY_REQUIRES_SHARED_CONTENT = NO
PRIVATE_QUERY_REQUIRES_SHARED_DOMAIN_LANE = YES

PRIVATE_INGEST_REQUIRES_SHARED_CONTENT = NO
PRIVATE_INGEST_REQUIRES_SHARED_DOMAIN_LANE = YES

EMPTY_SHARED_MEMORY_CONTENT = LAWFUL
ZERO_SHARED_DOMAIN_LANES = NOT_LAWFUL_FOR_PUBLIC_WORKSPACE
~~~

The prior semantic finding is retained:

~~~text
ZERO_SHARED_WORKSPACE_SEMANTICS =
    LAWFUL_UNMATERIALIZED_SHARED
~~~

Where a legitimate legacy workspace has declared domain lanes whose shared
graph has not been materialized, the selected initial-profile remedy is
ordinary lawful legacy opening/materialization before writer freeze and P2.
No native admission or migration code may invent the missing lane.

~~~text
PUBLIC_WORKSPACE_WITH_ZERO_SHARED =
    FORBIDDEN_INITIAL_PROFILE

PRE_FREEZE_LEGACY_MATERIALIZATION =
    SELECTED POLICY
    NOT CURRENTLY AUTHORIZED
~~~

The alternative NATIVE_DECLARED_EMPTY_SHARED_DISCOVERY_AMENDMENT is not
selected and must not be implemented. An operator may retain a whole
zero-shared workspace as non-public only through a separately recorded
decision with an acceptable source-side cause. Native topology-adapter
convenience is never an acceptable cause.

## Zero-private public workspaces

The public shape of zero admitted private scopes with one or more admitted
shared scopes is lawful under I4G-R1.

~~~text
0 admitted private scopes
>= 1 admitted shared scopes
~~~

For that shape:

~~~text
get_workspace = lawful under I4G-R1 workspace-view qualification

create_agent(existing admitted) =
    refuse / inapplicable because no admitted agent exists

create_agent(new) = REFUSED
ingest(agent) = REFUSED_NOT_ADMITTED
query(agent) = REFUSED_NOT_ADMITTED
~~~

The initial native profile deliberately refuses unadmitted creation. It must
not recreate legacy on-demand private-lane creation.

## Materialized authority and public disposition

The following distinction is frozen:

~~~text
NATIVE_DURABLE_AUTHORITY
!=
PUBLIC_RUNTIME_CAPABILITY
~~~

A materialized scope may be retained outside public routing only conditionally,
and only for a source-side cause. Initially permitted causes are:

~~~text
UNKNOWN_REPRESENTATION
NO_NODES_EVIDENCE
NON_WORKSPACE_DIRECTORY
OPERATOR_RETAINED_WHOLE_WORKSPACE
~~~

~~~text
MATERIALIZED_SCOPE_MAY_BE_RETAINED_NONPUBLIC = CONDITIONAL

NATIVE_CAPABILITY_DEFICIT_AS_NONPUBLIC_CAUSE = FORBIDDEN
~~~

No lawful TORMENT effect may disappear because native code lacks an adapter.
Every retained-non-public or explicitly-refused key must instead have one
explicit, frozen, lawful source cause.

## Root public completeness invariant

For the frozen canonical root layout, ROOT_PUBLIC_COMPLETENESS_VALID holds if
and only if all of the following hold:

1. Discovered layout equals declared layout.
2. Every discovered directory classified as a workspace is backed by lawful
   workspace evidence.
3. Every discovered RootScopeKey has exactly one explicit disposition.
4. Every PUBLIC_NATIVE key has a valid admission posture, is manifest-backed,
   is reconstructible from completion-bound runtime evidence, and has an
   ACTIVE RootScopeMembership for the frozen profile revision.
5. Every public workspace has zero to many private public scopes and one to
   many shared public scopes.
6. Every private public scope is recoverable by its complete RootScopeKey
   identity.
7. Every shared public scope is recoverable by its complete RootScopeKey
   identity and participates in the explicit admitted shared order.
8. Every RETAINED_NONPUBLIC or EXPLICITLY_REFUSED key has an explicit,
   frozen, lawful source cause.
9. No key retains live legacy read/write authority after native activation.
10. No workspace is partially served.

For item 10, partial service includes at least a public-native key that cannot
be reconstructed, a scope hidden for native-capability deficit, or a public
workspace with zero admitted shared lanes.

~~~text
ROOT_PUBLIC_COMPLETENESS_INVARIANT = FROZEN
~~~

## Successor workspace-view contract

The later implementation qualification must provide a semantic
WorkspaceNativeView equivalent to:

~~~text
workspace_id

private_scopes:
    Mapping[agent_id, PrivateScope]
    cardinality 0..n

shared_scopes:
    ordered Mapping[domain_id, SharedScope]
    cardinality 1..n

private_motif_domain:
    Mapping[agent_id, domain_id]

representation lane

retained per-domain owners/policies
~~~

Its lookup laws are:

~~~text
resolve_private(agent_id):
    return the exact admitted scope
    otherwise refuse not-admitted

resolve_shared(domain_id):
    return the exact admitted scope
    otherwise refuse

shared_scopes empty:
    workspace-view construction refuses

private_scopes empty:
    workspace-view construction remains lawful
~~~

All mapping must be built from completion-bound RootScopeKey evidence. This
semantic target does not claim that the multi-private execution path is
already implementation-qualified.

~~~text
MULTI_SCOPE_WORKSPACE_VIEW_CONTRACT = FROZEN
~~~

## Frozen operation/topology matrix

| Public workspace shape | get_workspace | create_agent existing | create_agent new | ingest | query |
| --- | --- | --- | --- | --- | --- |
| 0 private / 0 shared | Refuse / non-public | Refuse | Refuse | Refuse | Refuse |
| 0 private / >=1 shared | Qualify in I4G-R1 | Refuse / none admitted | Refuse | Refuse | Refuse |
| >=1 private / 0 shared | Refuse | Refuse | Refuse | Refuse | Refuse |
| 1 private / >=1 shared | Existing I4G qualification | Existing bounded qualification | Refuse unadmitted creation | Existing qualification | Existing qualification |
| >1 private / >=1 shared | I4G-R1 workspace view | I4G-R1 existing-admitted identity | Refuse unadmitted creation | I4G-R1 qualification target | I4G-R1 qualification target |

In particular, the final row is a frozen semantic target, not a claim that
the greater-than-one-private execution path is already qualified.

## Classification and representation gates

The generalized discovery algorithm is not amended by I4G-R1.

~~~text
DECLARED_DOMAIN_WITH_NO_SHARED_DIRECTORY =
    NOT YET ADMISSIBLE AS PUBLIC UNDER INITIAL PROFILE
~~~

Before a future frozen admission epoch, each such workspace must either have
its declared shared lane lawfully materialized under legacy authority or be
explicitly retained as a whole non-public workspace through a separately
recorded operator decision.

PRIVATE_DIRECTORY_WITHOUT_NODES_EVIDENCE remains an unresolved observational
class. It does not automatically qualify a materialized memory graph and
I4G-R1 does not invent an empty-private posture.

~~~text
PRIVATE_DIRECTORY_WITHOUT_NODES =
    UNRESOLVED_SOURCE_CLASSIFICATION

ADMISSION =
    REFUSED / SOURCE-CAUSED NONPUBLIC
~~~

A directory under workspaces is not itself evidence of a lawful workspace.
The later observation must classify it using the reviewed signals: domains.json,
meta.json or workspace_meta.json, agents children, and domains children.
Discovery code is unchanged.

The three unknown representation scopes remain source-classification gates.

~~~text
DIMENSION_EQUALITY_IS_NOT_REPRESENTATION_IDENTITY = YES
UNKNOWN_REPRESENTATION = SOURCE-CLASSIFICATION_GATE
UNKNOWN_REPRESENTATION_SCOPES = 3
~~~

I4G-R1 does not infer provider or model identity, and activation remains
refused while a required public scope has unknown representation.

## Fenced capabilities

~~~text
PROPOSAL_RECORDS_WITH_UNIDENTIFIED_VECTOR_GEOMETRY = 12
INITIAL_PROFILE_PROPOSAL_VECTOR_HAZARD = FENCED

DEEP_MEMORY_ENABLED = NO
ARCHIVE_RECALL_NATIVE = REFUSED
ARCHIVE_VECTOR_NORMALIZATION_REQUIRED_FOR_INITIAL_PROFILE = NO
~~~

Historical proposal processing remains refused. Proposal semantics are
unchanged. Deep memory remains disabled, archive recall remains refused, and
no archive data is deleted or normalized for this initial profile.

## Required successor observation, not authorized here

After this contract is frozen, a separately authorized minimal read-only phase
is required to establish the missing joint mapping. For each current workspace
directory it must obtain only:

- lawful-workspace versus non-workspace classification;
- declared domains;
- private materialized scope identities and whether the private directory has
  nodes evidence;
- shared materialized scope identities and whether a shared directory and
  shared nodes evidence exist;
- motif evidence; and
- exact joint private/shared topology.

For every unknown representation RootScopeKey, that later phase must obtain
only workspace embedding-lock metadata, representation-manifest metadata,
scope kind and qualifier, and NPY-header dimension/dtype. It must not load
vectors.

Following that mapping, any pre-freeze legacy materialization requires its own
work order deciding and authorizing the exact legacy writes.

~~~text
NEXT_REAL_ROOT_OBSERVATION_REQUIRED = YES
PRE_FREEZE_LEGACY_MATERIALIZATION_AUTHORIZED = NO
~~~

## I4G-R1 execution boundary and frozen result

This phase made only this documentation change. It did not contact the real
root, modify production or test code, run tests, perform writer freeze, admit
the real root, or activate native public operation.

~~~text
PRODUCTION_CODE_CHANGES = 0
TEST_CODE_CHANGES = 0
TESTS_RUN = 0
REAL_ROOT_CONTACT = NONE

WRITER_FREEZE_ARCHITECTURALLY_READY = NO
REAL_ROOT_ADMISSION_READY = NO
REAL_ROOT_ACTIVATION_READY = NO

I4G_R1_TOPOLOGY_SUCCESSOR_CONTRACT = FROZEN
I4G_FROZEN_RESULT_REMAINS_TRUE = YES

PUBLIC_PRIVATE_CARDINALITY = 0_TO_N
PUBLIC_SHARED_CARDINALITY = 1_TO_N
ZERO_SHARED_PUBLIC_WORKSPACE = REFUSED
ZERO_SHARED_RESOLUTION = PRE_FREEZE_LEGACY_MATERIALIZATION
ZERO_SHARED_DISCOVERY_AMENDMENT_SELECTED = NO

MULTI_PRIVATE_LAWFUL = YES
MULTI_SHARED_LAWFUL = YES
ZERO_PRIVATE_WITH_SHARED_LAWFUL = YES

MATERIALIZED_SCOPE_NONPUBLIC_DISPOSITION = SOURCE_CAUSE_ONLY
NATIVE_CAPABILITY_AS_NONPUBLIC_CAUSE = FORBIDDEN
~~~

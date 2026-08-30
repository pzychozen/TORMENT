# TORMENT Memory Substrate — Phase 7G5A3C1 Fabric Structural Translation v0.1

**Status:** BLOCKED — schema-v2 structural extension required before a faithful
ordinary-Fabric translation boundary can be implemented.

**Starting authority:** `682bc8bb82151e474acba05496b1b8d0ee96996b`.

## Decision

The existing Phase-7 schema has enough typed runtime-binding information to
translate the legacy `private` / `shared` labels, and its immutable
`provenance_records` row has appropriate fields for a deterministic
`ProvenanceV1` mapping. It cannot, however, carry the five independently
reasoned legacy governance facts structurally. `object_revisions` contains one
unconstrained `governance_state TEXT` column and no governance-fact child or
other typed carrier. Encoding the flag combination in that text would turn the
column into an opaque token, which this phase explicitly prohibits.

There is a second operation-closure gap for a standalone idempotent provenance
service: schema v1 has no `PROVENANCE` operation-output kind or provenance
transition-effect family. `operation_outputs` can name only objects,
relationships, representations, and reconciliation cases; the semantic helper
accepts effects only for those families plus legacy admission. A provenance row
therefore cannot be the recoverable published result of its own semantic
operation with the existing H2/H8 discipline. This must not be papered over by
embedding operation identity in descriptive text or by using an unrelated
output kind.

```text
CAN_CURRENT_SCHEMA_STRUCTURALLY_REPRESENT_RICH_GOVERNANCE = NO
CAN_CURRENT_SCHEMA_LOSSLESSLY_OR_SAFELY_MAP_RUNTIME_PROVENANCE = NO
A3C1_SCHEMA_EXTENSION_REQUIRED = YES
A3C1_GOVERNANCE_SCHEMA_BLOCKER = YES
```

The second answer is `NO` for the required *runtime translation service*, not
because the `ProvenanceV1` fields lack a safe row-level mapping. The mapping is
specified below so a schema-v2 implementation can preserve it without field
loss.

## Observed structural boundaries

- `NativeMemoryRuntimeScope` already requires a non-empty `workspace_id` and
  exactly one scope qualifier: `agent_id` for `PRIVATE_AGENT`, or `domain_id`
  for `SHARED_DOMAIN`.
- `NativeMemoryCompatibilityFacade` rejects `scope`, `governance`,
  `provenance`, lifecycle, authority, identity, revision, readiness, integrity,
  reconciliation, operation, and transition shadows from flexible payload.
- `MemoryGovernanceFlags` supplies five independent booleans; runtime behavior
  separately consults `protected`, `non_shareable`,
  `collective_export_blocked`, `collective_reingest_blocked`, and
  `decay_accelerated`. Lifecycle `PROTECTED` is deliberately a distinct
  lifecycle fact and can take precedence in the existing soft-migration reader.
- 7G3A already establishes that ordinary `signals.links` values are arbitrary
  legacy strings, not universally resolvable EIDs. A native `LINK` requires
  caller-supplied source namespace plus canonical target EID and exact alias
  resolution.

## Scope translation (frozen, not yet wired)

| Legacy value | Required native runtime scope | Required qualifier | Compatibility projection |
| --- | --- | --- | --- |
| `private` | `PRIVATE_AGENT` | non-empty `workspace_id`, `agent_id`; no `domain_id` | `scope: "private"`, `workspace_id`, `agent_id` |
| `shared` | `SHARED_DOMAIN` | non-empty `workspace_id`, `domain_id`; no `agent_id` | `scope: "shared"`, `workspace_id`, `domain_id` |

The structural `semantic_scope_id` from that verified binding is the only
native scope truth. A native flexible payload cannot supply or override it.
Missing, incompatible, or ambiguous bindings fail closed. No runtime-binding
DTO expansion is required to express this mapping.

## Provenance translation design for schema v2

The future provenance service receives a typed `ProvenanceV1`, caller-supplied
idempotency namespace, and stable operation key. It must use canonical intent,
produce an immutable native row, and recover the same `provenance_id` on retry.
It does not confer authority; ordinary memory remains
`authority_category="NOT_APPLICABLE"`.

| `ProvenanceV1` field | Native destination | Preservation rule |
| --- | --- | --- |
| `schema_version` | versioned descriptive encoding | Preserved exactly; it declares the source vocabulary. |
| `source_type` | `source_channel` | Preserved as the validated source class. |
| source record family | `origin_kind="RUNTIME_PROVENANCE_V1"` | Separates runtime provenance from legacy admission without inventing authority. |
| `source_role` | `source_role` | Preserved exactly, including required role-output role. |
| `write_path` | `derivation_status` plus descriptive encoding | The structural value distinguishes direct, cognition-writeback, collective-reingest, and other validated paths; the exact validated path is preserved descriptively. |
| uncertainty information | `uncertainty_state="UNKNOWN"` | `ProvenanceV1` makes no uncertainty assertion. |
| `created_at_ts` | `capture_time_ns` when canonically parseable; descriptive encoding always | The exact timestamp string is retained; source time remains unknown. |
| source time | `source_time_ns=NULL` | No `ProvenanceV1` field establishes it. |
| memory role | `memory_role=NULL` | No `ProvenanceV1` field establishes it. |
| `parent_eids` | versioned descriptive unresolved-lineage evidence | Preserve ordered canonical EIDs only; do not resolve a bare EID or create a relationship. First-class parent lineage needs a later qualified-lineage phase. |
| `created_at_step`, `tool_name`, `session_id`, `notes` | versioned descriptive encoding | Preserved exactly and non-authoritatively. |
| `asserted_by`, `observation_source`, `inference_rule` | versioned descriptive encoding | Preserved exactly as source-description evidence. |
| `character_id`, `character_name`, `character_scope` | versioned descriptive encoding | Preserved exactly and remains descriptive, never identity or routing authority. |
| `admission_refused`, `admission_reason`, `admission_policy_version` | versioned descriptive encoding | Preserved exactly; this ordinary-ingest phase does not reinterpret migration admission semantics. |

The descriptive carrier must be canonical JSON with an explicit format marker,
for example `TORMENT_PROVENANCE_V1_DESCRIPTIVE/1`. Structural columns always
win. It must contain no operation identity, routing state, native identifiers,
or hidden authority. That encoding is permitted only after the provenance
operation/effect/output schema family exists; no row is written in this phase.

## Governance blocker

The legacy default is the explicit permissive vector
`MemoryGovernanceFlags(False, False, False, False, False)`. It is not
`UNKNOWN`. The following facts must remain independently queryable without
parsing a string or flexible payload:

| Legacy fact | Current behavior that depends on it | Required schema-v2 fact |
| --- | --- | --- |
| `protected` | compression/decay protection fallback | `protected` boolean bound to exact object revision |
| `non_shareable` | packet-emission refusal | `non_shareable` boolean bound to exact object revision |
| `collective_export_blocked` | packet-emission refusal | `collective_export_blocked` boolean bound to exact object revision |
| `collective_reingest_blocked` | collective-reingest refusal | `collective_reingest_blocked` boolean bound to exact object revision |
| `decay_accelerated` | accelerated-decay decision, subject to protection | `decay_accelerated` boolean bound to exact object revision |

The smallest compliant extension is an immutable, exact-revision governance
fact carrier with all five non-null checked booleans and a foreign key to
`(object_id, object_revision_id, revision_ordinal)`. The semantic transaction
helper must publish and validate it as a closed child of the object revision.
The existing `governance_state` may remain a separate coarse state only if it
cannot disagree with the child facts; it cannot encode their combinations.
Lifecycle `PROTECTED` stays on the lifecycle carrier and is not merged with the
governance `protected` fact.

To complete standalone provenance creation, schema v2 also needs a typed
provenance publication family: a `PROVENANCE` operation output, a provenance
transition effect, and helper verification that the output and effect identify
the immutable row actually created by the idempotent operation. These are
schema-addressable typed additions, not a generic blob/effect escape hatch.

## Link classification (frozen, not yet wired)

| Input | A3C1 disposition |
| --- | --- |
| no links | `ABSENT`; no relationship intent |
| explicit `{target_legacy_source_namespace_id, target_eid}` that resolves exactly to a committed `LEGACY_CORE_NODE` | `RESOLVABLE_NATIVE_COMPAT_LINK`; future phase may create the qualified `LINK` |
| raw ordinary string, including `"memory-about-project-x"` or `"12"` | `UNRESOLVED_LEGACY_LINK_REFERENCE`; retain only non-semantic compatibility evidence if later schema/contract permits, never a native relationship |
| incomplete or non-resolving qualification | refusal or unresolved classification; no guessed target |

Generic `signals.links` strings are not automatically native relationships.

## Explicit non-changes and deferrals

This blocker freeze makes no Python, schema, migration, runtime-binding,
Fabric, DomainRouter, Character, MemoryGraph, persistence, or application
startup change. It introduces no relationship, provenance, governance, object,
representation, operation, or transition row.

Deferred: A3C2 atomic memory-plus-motif composition; A3C3 reinforcement
continuity; A3D Fabric routing; A4 Character work; native split/merge; cutover;
and the schema-v2 governance/provenance publication extension identified above.

# TORMENT Memory Substrate — Phase 7G5A3C1 Fabric Structural Translation v0.1

**Status:** COMPLETE — pure structural translation is qualified. It remains
unwired and has no persistence authority.

**Starting authority:** `b74cc10efe56adea1bfb824f0fbe14467240f517`.

## Decision

Phase 7G5A3C1S resolved the earlier schema blocker with the explicit v1.1
exact-revision governance carrier and the closed-child provenance model. This
phase now supplies a pure boundary in
`torment_service.substrate.fabric_translation`; it does not open a schema,
accept a connection, create a service, or write a row. Its immutable output is
directly usable by the prospective A3C2 semantic transaction.

The boundary accepts only the narrow structural inputs needed for a new memory:

- workspace/scope qualifiers and already-established namespace UUIDs;
- the caller-provided semantic-scope UUID, never inferred;
- a validated `ProvenanceV1` instance;
- `MemoryGovernanceFlags`;
- raw `signals.links` evidence and separately typed qualified link targets.

It returns a `NativeMemoryRuntimeScope`, `NativeProvenanceRecord`, explicit
`NativeMemoryGovernanceFacts`, a legacy scope projection, qualified link
intents, and ordered unresolved raw-link evidence. It creates no native
memory/object/revision/relationship/representation/operation/transition ID.

## Scope translation

| Legacy scope | Native runtime scope | Required facts | Projection |
| --- | --- | --- | --- |
| `private` | `PRIVATE_AGENT` | non-empty `workspace_id`, non-empty `agent_id`, no `domain_id` | `scope=private`, `workspace_id`, `agent_id` |
| `shared` | `SHARED_DOMAIN` | non-empty `workspace_id`, non-empty `domain_id`, no `agent_id` | `scope=shared`, `workspace_id`, `domain_id` |

The translator refuses an unknown scope or either mixed/missing qualifier
combination. Scope is structural: `prepare_flexible_payload()` uses the
existing compatibility writer's shared structural-key doctrine and refuses a
payload `scope` or `semantic_scope_id` shadow.

## Provenance translation

The provenance input must be a `ProvenanceV1`, not a dictionary. Translation
revalidates its serialized form and fails closed if mutable legacy state has
become invalid. No translation-time clock is used.

| `ProvenanceV1` fact | Native closed-child input |
| --- | --- |
| validated `source_type` | `source_channel` |
| `source_role` | `source_role` |
| validated `write_path` | `derivation_status`, plus exact descriptive copy |
| any valid source/write path | preserved without a new vocabulary or path remapping |
| `created_at_ts` | canonical UTC `capture_time_ns`; `NULL` when absent |
| source timestamp | `source_time_ns=NULL` (there is no separate validated source-time field) |
| `parent_eids` | ordered, deduplicated descriptive evidence classified `UNRESOLVED_NAMESPACED_LEGACY_LINEAGE_EVIDENCE` |
| step, tool, session, notes, environment, character, and admission fields | canonical descriptive evidence only |

The closed-child record is always:

```text
origin_kind = RUNTIME_PROVENANCE_V1
uncertainty_state = UNKNOWN
memory_role = NULL
```

`descriptive_notes` is canonical JSON (`sort_keys`, compact separators) with
the format marker `TORMENT_PROVENANCE_V1_DESCRIPTIVE/1`. It has no native ID,
operation/transition identity, authority, or routing field. Parent EIDs stay
unresolved: they never create relationships and bare EIDs are never searched.

`NativeProvenanceRecord` was moved to the small shared substrate DTO module so
translation can prepare the exact already-qualified closed-child type without
constructing the qualification writer. The qualification service continues to
re-export and use that same type; no standalone provenance publication was
introduced.

## Governance translation

Every `MemoryGovernanceFlags` field maps one-to-one to
`NativeMemoryGovernanceFacts`:

```text
protected
non_shareable
collective_export_blocked
collective_reingest_blocked
decay_accelerated
```

All five must be actual booleans. The all-false vector is explicitly emitted,
not interpreted as unknown or absent. The reverse projection is used only for
parity qualification and proves the existing decisions for packet emission,
collective reingest, decay acceleration, and compression's legacy-governance
fallback are unchanged.

Lifecycle remains separate. No lifecycle fact lives in the governance DTO, and
the flexible-payload helper refuses lifecycle shadows. Thus an A3C2 transaction
can independently supply lifecycle `PROTECTED` with all governance facts false,
or a non-protected lifecycle with governance `protected=true`.

## Link classification

| Input | Translation disposition |
| --- | --- |
| `None` or `[]` | `ABSENT`; no link intent or unresolved evidence |
| raw string such as `memory-about-project-x` or `12` | `UNRESOLVED_LEGACY_LINK_REFERENCE`, retained with `raw_reference` and input `source_index` |
| typed `QualifiedCompatibilityLinkTarget(namespace, non-negative EID)` | `QUALIFIED_COMPAT_LINK_INTENT` carrying exactly that namespace and EID |

Raw link order is retained for evidence fidelity but does not claim semantic
relationship order. A string is never parsed as an EID, namespaces are never
guessed, and no alias is read during this phase. Only A3C2's transaction-time
exact alias/object-kind resolution may promote the intent to
`RESOLVABLE_NATIVE_COMPAT_LINK` and publish a qualified relationship.

## Ordinary Fabric field classification

| Fabric fact | Native disposition |
| --- | --- |
| `scope` | structural runtime scope |
| `workspace_id` | runtime-scope qualifier / compatibility projection |
| `agent_id` | private-scope qualifier |
| `domain_id` | shared/domain qualifier |
| `provenance` | closed-child structural provenance input |
| `governance` | exact-revision governance facts |
| `embedding_provider` | non-authoritative compatibility/representation metadata |
| `embedding_model` | non-authoritative compatibility/representation metadata |
| `embedding_dim` | representation lane fact when publication occurs |
| `embedding_checksum` | representation/integrity-related evidence, not source authority |
| affect fields | flexible payload |
| metastability fields | flexible payload |
| seed motion fields | flexible payload |
| phase timing | flexible payload |
| SRG | flexible payload under the current contract |
| `signals.links` raw strings | unresolved legacy link evidence unless explicitly qualified |

The pure `prepare_flexible_payload()` helper uses the dependency-free shared
policy also used by the compatibility writer. It retains ordinary values but
refuses only the frozen native structural shadows (scope, provenance,
governance, lifecycle, authority, identity/revision, operation/transition, and
representation/readiness/integrity families); it does not silently strip
arbitrary payload content.

## Qualification

`tests/test_substrate_fabric_translation.py` proves:

- private/shared translation, round-trip projection, and scope-shadow refusal;
- all valid existing source and write values, canonical deterministic
  provenance encoding, malformed provenance refusal, and unresolved parent-EID
  retention;
- exact governance vectors including all false, legacy behavioral parity, and
  lifecycle/governance separation;
- absent/raw/qualified link classification with raw-order preservation and no
  string-to-EID inference;
- no change to `objects`, `object_revisions`, `object_revision_governance`,
  `relationships`, `relationship_revisions`, `provenance_records`,
  `representations`, `operations`, or `semantic_transitions` while translating.

## Explicit non-changes

This phase makes no Fabric, app, router, Character, runtime-binding, schema,
migration, persistence, representation, reconciliation, or deployment-state
change. It opens no Fabric/DomainRouter/Character native routing, no
provenance standalone operation/effect/output, no relationship write, no motif
composition/reinforcement/runtime motif-ID allocation, and no native
activation/cutover/dual read/dual write/authority expansion.

Deferred work remains A3C2 atomic native new-memory plus motif composition.
Do not begin it automatically.

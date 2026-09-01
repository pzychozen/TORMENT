# 7G5E4E-A2 Native Query Read-Model Qualification

## Status

`E4E_A2_NATIVE_QUERY_READ_MODEL = QUALIFIED`.

This change adds an internal, read-only query substrate.  It does not alter
`TormentFabric.query()`, `/agent/query`, or `/retrieve`; public query backend
selection remains legacy.  No selector, environment toggle, dual read, or
shadow comparison was added.

## Read-model contract

`torment_service.query_read_model` defines the narrow A3-facing surface:

```text
QualifiedQueryReadModel
  private_lane(workspace_id, agent_id) -> QualifiedQueryLane
  shared_lane(workspace_id, domain_id) -> QualifiedQueryLane
  domain_geometry(domain_id) -> QualifiedDomainGeometry
  active_motifs(domain_id, top_k=8) -> legacy-shaped summary
```

`LegacyQualifiedQueryReadModel` is a non-invasive reference over
`MemoryGraph` and `MotifRegistry`.  `NativeQualifiedQueryReadModel` accepts
only an already recovered native multi-scope runtime.  It opens no legacy
graph and grants no write, routing, scoring, continuity, SRG-breathing,
Character, or activation authority.

Native lane text search calls `NativeMemoryVectorRuntime.search(query_text,
...)` directly.  It does not call `search_by_embedding`, use a Fabric routing
embedding, or add a SQL cosine implementation.  Therefore the existing
trimmed-text, one lane-embedder-call behavior stays authoritative.

## Qualified identities and result shape

Each `QualifiedQueryHit` holds a copy of the existing flattened search hit
and private structural facts:

- `QueryMemoryIdentity(workspace_id, scope, qualifier, eid)`, reusing A1.
- Current `QualifiedQueryMotifIdentity(workspace_id, domain_id, motif_id,
  semantic_scope_id)` memberships.
- Native object/revision witnesses for native results.

`as_legacy_hit()` returns only the legacy-compatible flattened payload; none
of the structural identity leaks into the public result schema.  Native lane
scope facts are supplied from the recovered binding only if a direct native
writer did not carry the already-normalized compatibility fields.  A recovered
private lane obtains its motif domain strictly from the verified admission
descriptor's `motif_domain_id`; it never guesses from an agent ID.

The native vector runtime remains responsible for vector/current-row
selection.  Its current revision, usable READY representation, and stale
snapshot rejection rules are preserved without an additional projection race.
The qualified hit contains enough identity for A1 continuity and qualified
conflict joins.  Deep lanes are intentionally absent:

```text
A2_NATIVE_DEEP_QUERY = NOT_IMPLEMENTED
DEFAULT_NATIVE_QUERY_DEEP_PROFILE = DISABLED
```

## Motif and geometry reads

The native model reads current memberships through
`NativeMotifRuntimeReader`; retired membership revisions cannot appear.  A
same-string motif is retained as separate research/engineering identities,
including distinct semantic scopes and geometry.

Domain geometry uses the existing `NativeMotifGeometryAdapter`.  Shared domain
order comes from the recovered runtime's explicit admitted scope sequence,
not from SQL row order.  This exposes later A3 routing geometry without
performing routing.

`active_motifs` is a read-only projection matching the exact local
`MotifRegistry.active` surface and ordering:

```text
motif_id, label, strength, stability_score, density,
gravity_bonus, radius, members

sort: (strength + gravity_bonus, last_active_ts), descending
```

It reuses the current density/gravity equations and native current-member
radius reader.  It mutates no motif state.  Flexible payload fields, including
provenance, collective/tool-result flags, nested governance facts, and SRG,
remain the compatibility payload returned by the native vector runtime; A2
does not apply Fabric's later exclusions or discounts.

## Qualification evidence

Native qualification ran in `conda activate torment-substrate` with SQLite
`3.53.4`.

| Surface | Legacy | Native | Verdict |
| --- | --- | --- | --- |
| private lane search | `MemoryGraph.search` | text-native lane | PASS |
| shared research/engineering | separate graphs | recovered scope lanes | PASS |
| overlapping EID 1 | private/research/engineering | qualified identities | PASS |
| filters, `k < N`, `k >= N`, decay, reinforced memory | reference adapter | native adapter | PASS |
| READY/PENDING eligibility | legacy searchable vectors | current READY native rows | PASS |
| payload/SRG/provenance facts | flattened payload | flattened payload | PASS |
| motif membership/same-string collision | domain registry | current native membership | PASS |
| active motif summary | `MotifRegistry.active` | native projection | PASS |
| geometry and admitted domain order | legacy geometry adapter | native geometry adapter | PASS |
| cold vector rebuild | legacy stable result | close/reopen native lane | PASS |
| selection currentness/races | existing vector differential | reused unchanged runtime | PASS |
| per-lane trimmed embed call | one call | one call | PASS |

Executed suites:

```text
conda activate torment-substrate
python -m pytest tests/test_7g5e4e_native_query_read_model.py -q
# 4 passed

python -m pytest tests/test_substrate_existing_workspace_multi_scope_admission.py -q
# 3 passed

python -m pytest tests/test_substrate_native_memory_vector_runtime.py -q
# 10 passed, 12 skipped

conda activate torment
python -m pytest tests/test_7g5e4e_query_integration_preflight.py tests/test_query_explain_shape.py -q
# 15 passed
```

The A2-specific fixture uses actual native vector/motif readers and a
recovery-shaped three-scope binding: private `aria`, shared `research`, and
shared `engineering`.  It includes overlapping EIDs, multiple types,
half-life decay, a reinforced private R1/READY-to-R2/READY successor, a
non-READY representation, motif-less memory, and the `research/same-id` plus
`engineering/same-id` namespace collision.  Existing native vector tests
cover successor/current revision selection, stale-currentness rejection, and
cold reconstruction at the runtime boundary reused here.

## Deferred to A3

Only future orchestration may select this interface.  A3 still owns domain
routing, MemoryPlan candidate orchestration, bridge peeking, continuity,
reinforcement, SRG query behavior, governance/final ranking, Character, and
public API wiring.  SQLite remains durable/current memory truth, while those
Fabric decisions stay outside the native read model.

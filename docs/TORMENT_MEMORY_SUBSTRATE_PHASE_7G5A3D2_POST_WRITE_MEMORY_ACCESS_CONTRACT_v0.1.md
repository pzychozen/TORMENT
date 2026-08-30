# TORMENT Memory Substrate — Phase 7G5A3D2 Post-Write Memory Access Contract v0.1

## Status

`A3D2_POST_WRITE_MEMORY_ACCESS_CONTRACT = COMPLETE`.

This slice introduces a backend-neutral, read-only contract and independently
qualifies its current-view, raw-embedding, and post-write search behavior.

## Contract layers

```text
CORE READ
  get_current(eid)
  search_by_embedding(embedding, top_k, user_id)
    -> RuntimeMemorySearchOutcome(status, hits)
  read_current_embedding(eid, expected_dimension)

OPTIONAL ENUMERATION
  list_current()
  DEFERRED: ordering has not been qualified.

MUTATION
  DEFERRED
```

The core read port has no create, patch, delete, authorization, publication,
or transition operation.  Enumeration is deliberately a separate protocol so
the legacy `MemoryGraph.entities` ordering question cannot silently influence
the core read contract.

`RuntimeMemorySearchOutcome` has two statuses:

```text
SEARCHABLE  finite, correct-dimension query with norm > 0
ZERO_NORM   finite, correct-dimension query with norm == 0; hits == ()
```

Empty, wrong-dimension, NaN, and infinite vectors remain invalid.  A zero-norm
query is classified before either backend search is called.

## Backend mapping

```text
Legacy MemoryGraph -> LegacyPostWriteMemoryAccess
Native v1.1 core  -> NativePostWriteMemoryAccess
```

The legacy adapter receives the exact selected `MemoryGraph`; it neither
reloads the graph nor reconstructs an embedding locator.  Its raw embedding
path is the existing payload -> shard reader -> legacy `emb_<eid>.npy`
fallback.

The native adapter receives a caller-owned qualified v1.1 connection and one
fixed legacy-source namespace.  It delegates ranking, filtering, currentness,
and qualified candidate eligibility to the established native compatibility
search.  It delegates exact raw embedding qualification to
`NativeCompatEmbeddingReader`.  It opens no transaction and has no write
method.

## Structural separation

`RuntimeMemoryView` keeps ordinary immutable payload facts separate from:

```text
governance   RuntimeMemoryGovernanceView
provenance   RuntimeMemoryProvenanceView
embedding    RuntimeMemoryEmbedding byte witness
```

Payload is recursively copied and frozen.  Structural payload shadows and a
legacy embedding locator are excluded.  A returned view cannot change when
the underlying legacy payload later changes.

Governance carries all five existing flags plus `structurally_explicit`; this
preserves native missing-governance versus explicit all-false governance.
Provenance exposes only source type/channel, write path/derivation status,
collective-echo classification, and structural presence.  It does not invent
or reconstruct a complete `ProvenanceV1` from native descriptive evidence.

## Qualified facts

The focused A3D2 suite proves:

- legacy and native current-view parity for equivalent nonzero fixtures;
- immutable payload isolation;
- governance projection consistent with existing governance helpers;
- provenance and collective-echo projection sufficient for Hivemind read
  admission facts, resonance score, and loop type;
- conflict-read availability of EID, summary, memory class, and raw score;
- byte-identical raw current embedding reads, including a finite zero vector;
- native representation-gap behavior: current view remains available while
  current raw embedding read returns `None` and search excludes the memory;
- native adapter reads leave the counted object, relationship,
  representation, operation, transition, governance, provenance, integrity,
  and reconciliation tables unchanged.

Hivemind’s required read facts are therefore present independently of search:
current memory, governance/shareability, provenance classification,
`resonance_score`, and `loop_type`.

## Qualified post-write search parity

Raw backend behavior intentionally differs for a zero-norm *query*:

```text
legacy MemoryGraph search:
  finite (0.0, 0.0, 0.0) query is accepted
  -> all returned candidate raw_score values are 0.0

native qualified compatibility search:
  finite (0.0, 0.0, 0.0) query is invalid
  -> raises ValueError
```

`RAW_BACKEND_ZERO_QUERY_SEARCH_PARITY = NO` is frozen and deliberately not
repaired.  The neutral post-write contract has a narrower, consumer-relevant
semantic: it returns `ZERO_NORM` with no hits for both adapters without calling
either raw backend.  Legacy zero-query hits cannot meet the existing
reinforcement threshold (`raw_score >= 0.92`) or the existing conflict entry
threshold (`sim >= 0.88`), so the contract’s no-hit outcome preserves both
decisions exactly.  Nonzero search continues to delegate to the existing
backends and is qualified for EIDs, order, raw score, effective score, and
filters.

## Consumer readiness

```text
CONFLICT_SURFACING_READ_REQUIREMENTS = SATISFIED
HIVEMIND_READ_REQUIREMENTS           = SATISFIED
SRG_READ_REQUIREMENTS                = PARTIAL

POST_WRITE_PAYLOAD_MUTATION_CONTRACT = DEFERRED
SRG_NATIVE_POST_WRITE_READY          = NO
```

SRG still needs order-qualified enumeration and a separate
payload-successor/representation-continuity write contract.

## Search declarations

```text
RAW_BACKEND_ZERO_QUERY_SEARCH_PARITY      = NO
NONZERO_SEARCH_BY_EMBEDDING_PARITY        = PASS
ZERO_QUERY_CONTRACT_CLASSIFICATION        = PASS
ZERO_QUERY_REINFORCEMENT_DECISION_PARITY  = PASS
ZERO_QUERY_CONFLICT_DECISION_PARITY       = PASS
QUALIFIED_POST_WRITE_SEARCH_PARITY        = PASS
```

## Scope retained

```text
POST_WRITE_CONSUMERS_REWIRED       = NO
NATIVE_POST_WRITE_ADAPTER          = NO
A3D_NATIVE_ROUTE_WIRED_INTO_FABRIC = NO

DEFAULT_FABRIC_BEHAVIOR_CHANGED     = NO
POST_WRITE_RUNTIME_BEHAVIOR_CHANGED = NO
NATIVE_READS_CREATE_STATE           = NO
NEW_PERSISTENCE_ADDED               = NO
```

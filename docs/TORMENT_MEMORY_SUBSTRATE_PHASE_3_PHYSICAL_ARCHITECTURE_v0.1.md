# TORMENT Memory Substrate — Phase 3 Physical Architecture v0.1

**Status:** frozen physical-architecture requirements.

**Scope:** This document closes Phase 3. It freezes the initial physical shape required to implement the Phase 1 logical model and Phase 2 reliability, integrity, and recovery contract. It selects no database engine, schema, migration, representation encoding, durability configuration, integrity mechanism, benchmark, qualification result, or runtime implementation.

```text
MEMORY_SUBSTRATE_PHASE_0_RECONCILED = YES
MEMORY_SUBSTRATE_PHASE_1_LOGICAL_MODEL_FROZEN = YES
MEMORY_SUBSTRATE_PHASE_2_RELIABILITY_CONTRACT_FROZEN = YES
MEMORY_SUBSTRATE_PHASE_3_PHYSICAL_ARCHITECTURE_FROZEN = YES
PHYSICAL_ENGINE_SELECTED = NO
```

## 1. Initial physical shape

```text
INITIAL_PHYSICAL_SHAPE = SINGLE_TRANSACTIONAL_CORE
```

The initial TORMENT Memory Substrate uses one transactional physical core for authoritative durable semantics and initially retained materialized-representation payloads.

This is an implementation shape, not an ontology collapse. The core may initially contain physical representations of:

- `PRIMARY_DURABLE_STATE`;
- `MATERIALIZED_DERIVATION`; and
- `HISTORICAL_EVIDENCE`.

Those logical categories remain distinct. `ACCELERATION` remains rebuildable and non-authoritative whether physically colocated with the core or not.

## 2. Semantic core responsibilities

The transactional core must support the frozen logical contract for:

- logical objects and logical-object revisions;
- first-class logical relationships, relationship revisions, and declared endpoint-binding semantics;
- semantic scope;
- lifecycle and governance state;
- operation/idempotency identities;
- commit determinations and required commit evidence;
- predecessor and revision-conflict detection;
- required semantic history;
- representation identity;
- representation generation and dependency metadata;
- representation readiness;
- integrity metadata;
- reconciliation state; and
- current semantic visibility.

Required semantic history shares the transactional fate of semantic truth by default. No separate authoritative semantic-history engine is selected.

## 3. Representation payloads and physical colocation

Materialized-representation payloads, including exact retained embedding/vector generations, may initially reside physically in the same transactional core.

```text
PHYSICAL_COLOCATION != LOGICAL_IDENTITY
PHYSICAL_COLOCATION != SHARED_ONTOLOGICAL_ROLE
```

A vector remains a `MATERIALIZED_DERIVATION` when its bytes reside in the same physical database as its source carrier. Physical location does not convert a representation into primary durable truth, an independent logical object, or authority.

The core remains responsible for the representation's logical identity, source revision(s), generation, declared dependencies, readiness, integrity metadata, and operational disposition. The frozen Phase 1 and Phase 2 distinctions among commit truth, representation readiness, integrity measurement, and operational disposition remain orthogonal.

## 4. Future representation-payload separation

```text
SEPARATE_REPRESENTATION_PAYLOAD_LANE_COMPATIBLE = YES
SEPARATE_REPRESENTATION_PAYLOAD_LANE_REQUIRED = NO
```

Architecture with a separate representation payload lane remains a compatible future evolution. It is not required for the initial physical shape.

Physical separation may be reconsidered only through explicit authorized design work when evidence shows material benefit involving one or more of:

- backup or restore burden;
- representation-dominated core size;
- write or query pressure;
- different fate or encryption requirements;
- specialized numerical access; or
- retention or migration requirements.

These are decision signals, not automatic migration triggers.

### 4.1 Future cross-lane law

If a separate representation lane is adopted later, the protocol must be:

1. A semantic transaction commits the carrier and declares the exact representation generation `PENDING`.
2. The representation payload is produced.
3. Its integrity expectation is established independently of later verification.
4. The payload is durably published.
5. The published payload is verified against that pre-established expectation.
6. Only then may a semantic transaction mark that exact generation `READY`.

Consumers may consume only `READY` and compatible representations. A durably published but not-`READY` payload establishes no semantic readiness. No distributed transaction is required because incomplete representation state remains withheld rather than consumable as complete semantic state.

## 5. Locator, integrity, and placement law

Phase 1's distinction remains binding:

```text
identity = what the carrier or representation is
locator = where its current physical representation resides
```

Physical relocation does not change logical identity. A physical locator may be persisted as resolution or operational state, but it must not redefine semantic identity. Payload self-description may assist verification or forensics; it may not override the semantic core's authoritative resolution.

Integrity must be localizable at least to an individual logical representation. Larger container or segment integrity verification may additionally exist. Compaction, relocation, or erasure of one representation must not require unrelated representations to become semantically corrupt merely because they share physical storage. No hash or signature mechanism is selected.

State is not placed merely according to payload size or data type. A representation or derived payload may be physically separated only when its separation preserves all declared semantic dependencies, readiness rules, integrity rules, lifecycle/governance dependencies, and recovery obligations.

No externally stored payload may become an undeclared or unavailable sole basis for current semantic truth, governance, or authority. A semantic decision that depends on a representation must declare that dependency and require an acceptable representation state.

## 6. Motifs and representation retention

The Phase 1 motif model remains binding:

```text
motif = derived LOGICAL OBJECT
motif membership = derived LOGICAL RELATIONSHIP
MOTIF_RECONSTRUCTABILITY_PROVEN = NO
```

The motif carrier, its current semantic state, revisions, declared dependencies, and motif-membership relationships remain governed by the semantic core. Motifs are not disposable.

Not every vector-shaped motif-associated value is necessarily primary or core payload merely because it is vector-shaped. Any later physical separation of motif-associated derived payload requires explicit classification consistent with the frozen motif ontology.

A representation may not be destroyed while a retained semantic carrier explicitly depends on that exact representation for validity or for a declared recovery or reconstruction obligation. An unproven hypothetical future reconstruction does not by itself create an infinite-retention requirement. Retention and erasure remain separate from revocation and require later explicit design.

## 7. Transactional and current-state law

```text
ENGINE_WRITER_SERIALIZATION != PREDECESSOR_REVISION_VALIDATION
```

Even if a future transactional engine serializes physical writers, stale semantic transitions must fail their declared predecessor or current-revision compatibility checks. Engine concurrency behavior does not replace TORMENT logical concurrency semantics.

Current semantic state remains directly represented and queryable. Normal current-state reads do not reconstruct semantic truth by replaying history. History explains and supports recovery or lineage according to its declared role.

No event-sourcing architecture is selected.

## 8. Logical contract above storage model

```text
TORMENT_LOGICAL_CONTRACT_OWNS_ONTOLOGY = YES
```

Physical tables, rows, foreign keys, BLOBs, key/value entries, files, or other mechanisms implement the frozen logical contract. They do not redefine it.

In particular:

- logical relationships retain independent identity and revision semantics where frozen;
- `PRIMARY_DURABLE_STATE`, `MATERIALIZED_DERIVATION`, `HISTORICAL_EVIDENCE`, and `ACCELERATION` remain distinguishable; and
- `COMMIT_TRUTH`, `REPRESENTATION_READINESS`, `INTEGRITY_MEASUREMENT`, and `OPERATIONAL_DISPOSITION` remain orthogonal.

A future schema may not collapse these distinctions merely because a database representation makes collapse convenient.

## 9. Acceleration, analytics, and export

Search indexes, vector indexes, cached matrices, and analytical projections remain `ACCELERATION` when rebuildable. They do not establish carrier existence, representation truth, or commit fate. An acceleration may live inside or outside the same physical engine; physical colocation does not promote it to source truth.

A separate analytics or projection engine may later be used where useful. Hardened JSONL may remain useful for evidence, audit, diagnostics, experiments, and portable export. Neither analytics nor JSONL becomes authoritative semantic truth merely by existing. No analytics technology is selected.

## 10. Retention, physical reclamation, and autonomy

Logical retention, deletion, and erasure decisions remain governed by explicit TORMENT semantics and authorization. No new autonomous TORMENT actor or standing self-directed process may decide to destroy durable semantic or representation history.

Physical storage reclamation may occur only after semantic state already establishes that the physical material is reclaimable. Ordinary database-internal free-space or page management does not constitute an autonomous semantic decision.

## 11. One contract, not one engine

The Phase 1 and Phase 2 posture remains binding:

```text
ONE_CONTRACT_NOT_ONE_ENGINE = YES
MULTIPLE_ACCESS_MODELS_REQUIRED = YES
MULTIPLE_PHYSICAL_ENGINES_LIKELY_BUT_NOT_REQUIRED = YES
NEW_LOW_LEVEL_DATABASE_ENGINE_NOT_REQUIRED = YES
```

The initial single-core physical shape establishes that multiple engines are not required. The compatible future representation split establishes that multiple engines remain permitted.

```text
PHYSICAL_ENGINE_SELECTED = NO
```

The following is non-normative candidate context only:

- SQLite is the leading local-first transactional-core candidate.
- PostgreSQL remains a plausible future server or high-concurrency implementation.
- LMDB is technically capable but currently less natural for the relational logical model.
- DuckDB is more naturally an analytics or projection candidate than the semantic commit core.

No listed technology is selected by this document.

## 12. Architecture freeze, not qualification

```text
PHASE_3_IS_AN_ARCHITECTURE_FREEZE_NOT_IMPLEMENTATION_QUALIFICATION = YES
```

No benchmark is required for this freeze. The following remain deferred implementation or selection questions and must not be presented as verified:

- actual writer-concurrency profile;
- transaction and durability configuration;
- physical representation encoding;
- vector query and search acceleration;
- schema design;
- backup and restore objectives;
- legacy migration or admission;
- implementation crash qualification;
- integrity mechanism; and
- erasure versus retention.

## 13. Preservation and next phase

```text
PHASE_0_1_2_CONTRADICTION_FOUND = NO
```

No prior frozen doctrine is modified. The three pre-database invariants remain preserved: Memory-Optional Identity, Modality-Independent Ingest, and Agency / Authority Separation.

The next phase is:

```text
TORMENT MEMORY SUBSTRATE — PHASE 4
TRANSACTIONAL CORE TECHNOLOGY / PHYSICAL CONTRACT SELECTION
```

Phase 4 should evaluate and select the concrete transactional-core technology and physical contract. It may compare a very small shortlist, with SQLite as the leading local-first candidate. It may define:

- durability configuration;
- transaction semantics;
- concurrency and revision strategy;
- representation-byte storage approach;
- integrity-mechanism requirements;
- physical-schema principles; and
- bounded qualification required before implementation.

Phase 4 must not begin with a broad database survey.

## 14. Freeze verdict

```text
MEMORY_SUBSTRATE_PHASE_3_PHYSICAL_ARCHITECTURE_FROZEN = YES
PHASE_0_1_2_CONTRADICTION_FOUND = NO
INITIAL_PHYSICAL_SHAPE_SINGLE_TRANSACTIONAL_CORE = YES
SEPARATE_REPRESENTATION_PAYLOAD_LANE_REQUIRED = NO
SEPARATE_REPRESENTATION_PAYLOAD_LANE_COMPATIBLE = YES
PHYSICAL_ENGINE_SELECTED = NO
PHASE_3_IS_AN_ARCHITECTURE_FREEZE_NOT_IMPLEMENTATION_QUALIFICATION = YES
PRODUCTION_CODE_CHANGED = NO
TEST_CODE_CHANGED = NO
MEMORY_SUBSTRATE_PHASE_4_NEXT = YES
```

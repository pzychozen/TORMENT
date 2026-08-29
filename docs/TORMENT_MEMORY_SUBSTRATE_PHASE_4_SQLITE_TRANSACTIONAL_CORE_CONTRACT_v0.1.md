# TORMENT Memory Substrate — Phase 4 SQLite Transactional-Core Contract v0.1

**Status:** frozen engine selection and physical-contract requirements.

**Scope:** This document closes Phase 4. It selects SQLite as the initial transactional semantic-core engine and freezes the physical contract by which it implements the Phase 1 logical model, Phase 2 reliability/integrity/recovery contract, and Phase 3 physical architecture. It selects no detailed schema, exact table or column, index, query plan, identity encoding, vector binary encoding, intent fingerprint algorithm, integrity hash/signature algorithm, backup schedule, checkpoint policy, busy timeout, migration mapping, or production implementation.

```text
MEMORY_SUBSTRATE_PHASE_0_RECONCILED = YES
MEMORY_SUBSTRATE_PHASE_1_LOGICAL_MODEL_FROZEN = YES
MEMORY_SUBSTRATE_PHASE_2_RELIABILITY_CONTRACT_FROZEN = YES
MEMORY_SUBSTRATE_PHASE_3_PHYSICAL_ARCHITECTURE_FROZEN = YES
MEMORY_SUBSTRATE_PHASE_4_SQLITE_CORE_FROZEN = YES
```

## 1. Engine selection

```text
TRANSACTIONAL_CORE_ENGINE = SQLITE
INITIAL_PHYSICAL_SHAPE = SINGLE_TRANSACTIONAL_CORE
```

SQLite is selected as the initial TORMENT transactional semantic-core engine.

This does not make SQLite the TORMENT ontology. TORMENT owns logical identity, logical objects, logical relationships, revisions, semantic transitions, operation idempotency, semantic history, representation generations, integrity semantics, reconciliation, authority separation, and recovery semantics. SQLite supplies the low-level transactional storage mechanism implementing that contract.

## 2. One semantic commit set

```text
ONE_SEMANTIC_COMMIT_SET = ONE_SQLITE_CORE_DATABASE_TRANSACTION
```

Every member of one semantically atomic transition must participate in one SQLite core-database transaction. Cross-database `ATTACH` atomicity must not be relied on for semantic commit.

This is the initial physical realization, not a claim that TORMENT must use one database forever.

## 3. Required transition evidence

Every committed semantic transition requires immutable transition evidence committed in the same SQLite transaction as the successor semantic state it publishes. That evidence must bind sufficient information to establish:

- operation/idempotency identity;
- transition kind;
- affected carrier and scope;
- relevant predecessor revision; and
- successor revision or committed transition outcome.

Exact schema is deferred. State-row presence alone never establishes commit truth. No separately named generic `COMMIT` table is required merely for naming purposes: the required immutable transition/history record may itself be the durable commit evidence.

## 4. WAL and local-host scope

```text
SQLITE_JOURNAL_MODE = WAL
```

WAL mode is a database-level invariant and must be verified when the substrate opens the core. The selected initial core is restricted to a local-host filesystem compatible with SQLite WAL shared-memory semantics. Network-filesystem WAL deployment is outside the selected contract.

## 5. Durability

```text
SQLITE_SEMANTIC_COMMIT_SYNCHRONOUS_MINIMUM = FULL
```

Every write-capable semantic-core connection must explicitly establish or verify a synchronous setting meeting that minimum. TORMENT reports `COMMITTED` only after the transaction successfully commits under the qualified durability contract. A write API accepting bytes is not semantic commitment.

This contract does not claim protection from physical-media destruction or arbitrary hardware failure.

## 6. SQLite runtime eligibility

```text
SQLITE_WAL_RESET_FIX_REQUIRED = YES
SQLITE_RUNTIME_RELEASE_MUST_BE_ADMISSIBLE = YES
SQLITE_RUNTIME_QUALIFICATION_REQUIRED_AT_STARTUP = YES
CURRENT_ENV_SQLITE_ELIGIBLE_FOR_NEW_CORE = NO
```

The currently installed SQLite 3.51.2 is not eligible for the new WAL semantic core. The freeze requires the properties above, not a naive numeric predicate such as `sqlite_version >= 3.51.3`.

The concrete SQLite runtime/package used by the implementation is pinned during later implementation work. A maintained operational admissibility policy is separate from this architecture document. Startup qualification must fail closed when the linked SQLite runtime does not satisfy the substrate's admissibility requirements.

## 7. Connection initialization

Every semantic-core connection must pass through one substrate-controlled initialization and verification path before semantic use. No relevant SQLite default is trusted for correctness.

Where schema-declared foreign keys exist, `foreign_keys = ON` must be explicitly established before transaction work. Every connection must have an explicit busy/contention policy. Exact busy timeout or handler configuration is deferred.

## 8. Write transaction discipline

```text
SQLITE_SEMANTIC_WRITE_BEGIN = BEGIN_IMMEDIATE
```

Any semantic transaction that may write—including one that first reads current state to validate a predecessor—acquires SQLite write intent at transaction start. A semantic transition must not use a deferred read transaction followed by a write upgrade.

`BEGIN IMMEDIATE` is physical transaction discipline, not TORMENT ontology. Semantic correctness still requires operation-idempotency determination, predecessor/current-revision validation, and commit-set publication inside the same non-raceable transaction.

## 9. Serialization and revision validation

```text
ENGINE_WRITER_SERIALIZATION != PREDECESSOR_REVISION_VALIDATION
```

SQLite serializing physical writers does not make stale semantic state current. A transition based on a stale predecessor revision must fail declared compatibility checks even after SQLite grants it the writer lock. No correctness property may depend solely on SQLite's single-writer behavior.

## 10. Idempotency identity and intent binding

Every retryable durable semantic operation must possess a stable idempotency identity known to, supplied by, or deterministically recoverable from the initiating durable operation before semantic effects become ambiguous. A lost response must be retryable with that same identity.

No universal identity generator is frozen. A substrate-generated internal operation identifier is permitted only when the initiator can deterministically recover or reuse the durable idempotency identity required for retry. Physical contention, `SQLITE_BUSY`, timeout, lost response, or equivalent retry must not generate new semantic intent.

Operation identity must be immutably bound to canonical semantic intent. That intent projection must be deterministic and exclude execution-consequence values, including time-varying fields not part of requested semantics, substrate-assigned outputs, and non-canonical serialization or ordering artifacts.

```text
same idempotency identity + same canonical intent = idempotent recovery/result
same idempotency identity + conflicting canonical intent = conflict/reconciliation
```

Exact intent encoding or fingerprint algorithm is deferred.

## 11. Creation and logical identity

Creation has no predecessor revision. Logical identity uniqueness must therefore be transactionally enforced by the core and may not rely on process-local maximum-EID allocation. No one identity-allocation scheme is selected.

If an initiator requests a specific logical identity, that requested identity participates in operation intent. If an operation requests allocation of a new logical identity, the allocated identity is a durable output bound to the operation identity; a retry resolves to the same committed allocated identity rather than allocating another carrier. Exact logical-identity encoding remains deferred.

## 12. First-class relationships

Relationships remain first-class TORMENT carriers. Physical relational storage must preserve, as applicable, their independent identity, revision, scope, history, endpoint-binding semantics, and commit outcome.

SQLite foreign keys and constraints may reinforce structural validity. They do not define TORMENT relationship ontology.

## 13. Structural distinguishability and STRICT discipline

```text
STRICT_IS_TYPE_GUARD_NOT_SEMANTIC_STRUCTURE_GUARD = YES
```

`STRICT` is the normative default for substrate-owned relational/state structures where compatible. Every distinction frozen by earlier phases as structurally distinguishable without interpreting content must remain schema-addressable and machine-distinguishable without parsing opaque serialized natural-language or generic payload content.

This includes at least:

- logical state category;
- commit truth;
- representation readiness;
- integrity measurement;
- operational disposition;
- authority/agency record category;
- semantic scope; and
- required provenance dimensions.

The implementation may express these using typed columns, normalized relations, constraints, or equivalent explicit schema structures. It need not use literally one column per concept. It must not hide these distinctions solely inside JSON, TEXT, or BLOB payloads.

## 14. Logical categories and orthogonal axes

The following logical categories remain distinct despite physical colocation:

```text
PRIMARY_DURABLE_STATE
MATERIALIZED_DERIVATION
HISTORICAL_EVIDENCE
ACCELERATION
```

The following axes remain independently represented:

```text
COMMIT_TRUTH
REPRESENTATION_READINESS
INTEGRITY_MEASUREMENT
OPERATIONAL_DISPOSITION
```

One generic status field must not destroy these distinctions.

## 15. Current state and history

Current semantic state remains directly represented and queryable. Normal current-state reads do not reconstruct state by replaying semantic history. Required immutable transition/history evidence is committed atomically with the transitions it records.

No event-sourcing architecture is selected.

## 16. Representations and vector BLOBs

Exact retained embedding/vector generations may initially reside as BLOB payloads in the same SQLite core database. Their semantic metadata remains explicit and independently queryable, including:

- representation identity;
- source carrier revision;
- generation;
- derivation contract/version;
- dimension;
- dtype/encoding;
- declared dependencies;
- readiness; and
- integrity metadata.

Physical BLOB colocation never promotes an embedding from `MATERIALIZED_DERIVATION` to primary semantic truth. Vector/search indexes remain `ACCELERATION` unless later explicitly reclassified. No vector extension is selected.

## 17. Payload isolation principle

Even inside the single SQLite core database, large representation payload bytes must be structurally separable from frequently queried representation metadata. Metadata-only queries must not logically require loading or interpreting payload bytes. Exact table layout is deferred to Phase 5.

This preserves clean metadata queries, localized integrity, attribution of payload-related storage pressure, and a future representation-lane relocation without logical redesign.

## 18. Motif, payload, and retention preservation

The Phase 3 wording remains binding:

```text
motif = derived LOGICAL OBJECT
motif membership = derived LOGICAL RELATIONSHIP
MOTIF_RECONSTRUCTABILITY_PROVEN = NO
```

The motif logical carrier, current semantic state, revisions, declared dependencies, and membership relationships remain governed by the semantic core. Not every vector-shaped motif-associated value is necessarily primary or core payload merely because it is vector-shaped.

Any future physical separation of a derived payload must preserve all declared semantic dependencies, readiness rules, integrity rules, lifecycle/governance dependencies, and recovery obligations. An external representation may participate in semantic or governance decisions only through explicit declared dependencies and acceptable readiness/integrity state.

A representation may not be destroyed while a retained semantic carrier explicitly depends on that exact representation for validity or for a declared recovery/reconstruction obligation. An unproven hypothetical future reconstruction does not by itself create an infinite-retention requirement.

## 19. Integrity boundary and structural health gate

```text
SQLITE_STRUCTURAL_INTEGRITY != TORMENT_LOGICAL_INTEGRITY
```

SQLite structural/schema facilities may support database structural checks, `STRICT` type verification, constraint validation, and foreign-key validation where declared. TORMENT continues to own logical integrity for carrier/revision semantics, operation/transition consistency, representation expectations, generation/dependency validity, provenance invariants, relationship invariants, and reconciliation.

No content hash or signature algorithm is selected.

Before production migration, the substrate must define a structural-integrity verification policy. At minimum, structural verification is required for recovery-sensitive admission events such as:

- initial migrated-database admission;
- restore admission;
- detected unclean termination where substrate recovery policy requires verification;
- SQLite-reported structural/corruption errors; and
- other explicitly defined reconciliation conditions.

Failure may not silently continue as a healthy corpus. It must produce visible `WITHHELD` or `RECONCILIATION_REQUIRED` disposition appropriate to the affected scope.

Exact use of `quick_check`, `integrity_check`, `foreign_key_check`, or other SQLite facilities is deferred to Phase 5 and qualification. An expensive full-database scan is not required at every ordinary clean startup merely because Phase 4 selected SQLite.

## 20. Multi-carrier invariants and backup capability

Any semantically joint current transition requiring several objects or relationships may publish all required members through the same SQLite core transaction. No current frozen TORMENT invariant has been shown to require a transactional primitive SQLite lacks.

SQLite-supported backup/snapshot facilities are sufficient for engine selection. A future live backup process must use a SQLite-consistent mechanism. Copying only the live main database file must not be assumed to be a valid WAL backup protocol. Backup schedule, retention, restore operations, encryption, and off-host policy remain deferred.

## 21. PostgreSQL and LMDB

```text
POSTGRESQL_REQUIRED_NOW = NO
LMDB_REQUIRED_NOW = NO
```

PostgreSQL remains a compatible future transactional-core implementation if later requirements genuinely include multi-host writers, materially higher concurrent-write requirements, server-side availability, or another server capability absent from the selected SQLite deployment. No speculative PostgreSQL abstraction is authorized now.

LMDB is not rejected as technically incapable. It is not selected because it satisfies no current frozen requirement SQLite fails and would require TORMENT to own more indexing, relationship-query, and constraint machinery.

## 22. Future representation split

```text
SEPARATE_REPRESENTATION_PAYLOAD_LANE_REQUIRED = NO
SEPARATE_REPRESENTATION_PAYLOAD_LANE_COMPATIBLE = YES
```

SQLite selection does not logically bind representation bytes permanently to SQLite. Any future split requires explicit evidence and authorized design work.

## 23. Engine selection versus qualification

```text
SQLITE_SELECTION_REQUIRES_PRE_FREEZE_BENCHMARK = NO
```

Engine selection does not prove an implementation correct. Before production migration, bounded qualification must cover representative cases for at least:

- stale predecessor rejection;
- same-operation retry/idempotency;
- conflicting reuse of operation identity;
- creation retry/allocation behavior;
- competing writer and busy behavior;
- semantic transaction write-intent discipline;
- restart after acknowledged commit; and
- structural/logical integrity and reconciliation handling.

This must not become a large combinatorial fault campaign.

## 24. Phase 4 scope and Phase 5 handoff

```text
PHASE_4_IS_ENGINE_AND_PHYSICAL_CONTRACT_SELECTION_NOT_SCHEMA_IMPLEMENTATION = YES
```

Detailed schema remains deferred. No exact tables, columns, indexes, query plans, identity encoding, vector binary encoding, intent fingerprint algorithm, integrity hash algorithm, backup schedule, checkpoint policy, busy timeout, migration mapping, or production storage code is selected in this phase.

The next phase is:

```text
TORMENT MEMORY SUBSTRATE — PHASE 5
SCHEMA / TRANSACTION PROTOCOL / MIGRATION DESIGN
```

Phase 5 may design the actual TORMENT-owned SQLite schema and semantic transaction protocol. It must begin from the frozen logical model rather than translating current JSONL payloads directly into generic database blobs.

Phase 5 must specifically avoid a schema shape such as:

```text
id
type
status
payload_json
```

when that shape would silently recreate the structural weaknesses this substrate programme is replacing.

## 25. Freeze verdict

```text
MEMORY_SUBSTRATE_PHASE_4_SQLITE_CORE_FROZEN = YES
TRANSACTIONAL_CORE_ENGINE_SQLITE = YES
CURRENT_ENV_SQLITE_ELIGIBLE_FOR_NEW_CORE = NO
SQLITE_WAL_RESET_FIX_REQUIRED = YES
SQLITE_JOURNAL_MODE_WAL = YES
SQLITE_SEMANTIC_COMMIT_SYNCHRONOUS_MINIMUM_FULL = YES
SQLITE_SEMANTIC_WRITE_BEGIN_IMMEDIATE = YES
SQLITE_SELECTION_REQUIRES_PRE_FREEZE_BENCHMARK = NO
PHASE_0_1_2_3_CONTRADICTION_FOUND = NO
DETAILED_SCHEMA_SELECTED = NO
PRODUCTION_CODE_CHANGED = NO
TEST_CODE_CHANGED = NO
MEMORY_SUBSTRATE_PHASE_5_NEXT = YES
```

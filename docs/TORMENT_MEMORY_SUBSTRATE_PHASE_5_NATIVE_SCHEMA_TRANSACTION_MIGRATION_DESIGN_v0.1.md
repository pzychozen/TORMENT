# TORMENT Memory Substrate — Phase 5 Native Schema / Transaction / Migration Design v0.1

**Status:** frozen native-schema semantics, semantic-transaction design, and migration/cutover architecture.

**Scope:** This document closes Phase 5. It converts the frozen Phase 1 logical model, Phase 2 reliability/integrity/recovery contract, Phase 3 physical architecture, and Phase 4 SQLite transactional-core contract into the required native structural distinctions and semantic protocols. It does not select final DDL, table or column names, SQL affinities, concrete identity or idempotency encodings, hash algorithms, vector binary layout, indexes, connection tuning, backup policy, migration commands, or production implementation.

```text
MEMORY_SUBSTRATE_PHASE_5_NATIVE_SCHEMA_DESIGN_FROZEN = YES
PHASE_5_IS_NATIVE_SCHEMA_SEMANTICS_AND_TRANSACTION_MIGRATION_DESIGN = YES
CURRENT_SQLITE_3_51_2_USED_FOR_NEW_CORE = NO
```

## 1. Native schema anatomy

The following are required **structural distinctions**, not a mandated one-table-per-family design:

- substrate metadata and schema-migration ledger;
- semantic or identity-resolution namespaces;
- logical objects and object revisions;
- logical relationships, relationship revisions, and relationship-revision endpoints;
- durable operations;
- semantic transitions and transition effects;
- representations, representation payloads, and representation dependencies;
- structural provenance and structural lifecycle/governance;
- integrity expectations and integrity measurements;
- reconciliation;
- legacy aliases, legacy-admission records, and legacy-quarantine or immutable-evidence references.

The Phase 6 DDL may combine compatible families or use child structures where needed, provided these distinctions remain schema-addressable, typed, and enforceable without interpreting opaque content.

## 2. Object identity and selected current revision

An object identity row contains only immutable logical identity facts, including its identity-resolution namespace where applicable, object kind/class, creating or admission transition where applicable, and `current_revision_id`.

It must not duplicate mutable semantic truth. Current existence, lifecycle, governance, and effective semantic scope belong to the selected immutable revision when they are semantically mutable or versioned. Current semantic truth is the semantic state of the immutable revision selected by `current_revision_id`.

```text
CURRENT_REVISION_POINTER_IS_PRIMARY_CURRENT_SELECTION_STATE = YES
```

The pointer is selection state, not a second current-state payload. Normal reads follow it directly and do not replay history. The same principle applies to first-class relationships.

## 3. Semantic closure

Every committed object or relationship revision is semantically closed. Every structural fact required to interpret it must either be stored directly on that revision or reference an exact immutable/versioned record.

A revision must never resolve another entity's current version at read time when that referenced semantic affects the historical meaning of the revision. Later mutation or version advancement elsewhere cannot retroactively change what an earlier committed revision meant.

## 4. Revision identity and lineage

Every object and relationship revision has a stable logical revision identity, owning carrier identity, per-carrier ordinal, and exact predecessor where known.

- Revision identity is not SQLite `rowid`.
- Per-carrier ordinal orders a carrier's revisions; it is not logical identity.
- Current-revision and predecessor references must be engine-enforceably owned by the same carrier.
- Native ordinary successor semantics are linear by default. The schema and protocol must prevent unintended multiple ordinary successors from one predecessor.
- A future branching model requires separately authorized operations/relationship semantics and a schema-versioned change.
- Imported legacy current state may begin with `predecessor unknown`; that is an explicit admission/reconciliation fact, not fabricated ancestry.

## 5. First-class logical relationships

Logical relationships remain independent carriers with identity, immutable relationship revisions, selected current revision, typed endpoint bindings, scope, history, and applicable lifecycle/governance state.

Endpoints belong to the relationship revision. Their binding semantics explicitly distinguish logical-identity binding, exact-revision binding, and any other separately declared binding semantic. A relationship never silently means “whatever endpoint revision happens to be current.” Cross-scope references preserve scope explicitly.

### Cross-carrier lineage

Apply the Phase 1 relationship test. A parent, source, or lineage link is a first-class logical relationship when it carries durable semantic meaning, is traversed for semantic or governance decisions, requires independent revision/binding semantics, or must survive relocation independently.

Pure implementation pointers, material-provenance references, and representation dependencies are not promoted merely because they reference another carrier. Semantically meaningful cross-carrier lineage must not be hidden in opaque provenance content.

## 6. Structural payload boundary

```text
STRUCTURE_WHAT_TORMENT_REASONS_ABOUT_AS_STRUCTURE = YES
```

A datum may remain flexible or opaque content only when interpreting or changing it cannot determine or enforce a frozen substrate invariant, including identity, identity namespace, effective semantic scope, revision identity, current revision, relationship binding, commit truth, transition evidence, lifecycle, governance, authority category, required provenance, representation source/generation/readiness, integrity, or reconciliation.

Structural state wins over payload. Payload may never act as shadow identity, scope, lifecycle, governance, authority, revision, commit, readiness, integrity, or reconciliation state. Arbitrary user and domain content need not be relationally normalized merely because SQLite is available.

If a future feature needs to predicate, join, constrain, or transition on a datum currently treated as payload, it must first promote that datum into the structural contract before becoming authoritative.

## 7. Durable operations and idempotency

A durable operation represents stable retryable semantic intent. It structurally contains or binds an idempotency identity, canonical semantic-intent comparison identity, operation kind, required target/scope/predecessor intent, durable allocated outputs where applicable, and optional explicit rejection/result semantics where the product requires idempotent rejection.

An operation does **not** carry `COMMITTED` or `NOT_COMMITTED` as a second transition-truth axis. Ordinary rollback requires no synthetic negative operation row. A durable rejection or no-transition result is operation-result semantics, not historical transition commit truth.

The idempotency identity must be known to, supplied by, or deterministically recoverable from the initiating operation before repeat execution can create ambiguous semantic effects. Caller-generated identity is permitted but not mandatory. A substrate process may not mint an unrecoverable fresh identity after effects become ambiguous. Internally initiated durable work, including representation-state publication, uses a recoverably reproducible operation identity on retry. Exact encoding/derivation remains deferred.

## 8. Creation

Creation has no predecessor. Logical identity uniqueness is enforced transactionally; process-local maximum-EID allocation is forbidden.

When an initiator supplies the requested logical identity, that identity participates in canonical intent. When the operation requests allocation, the allocated logical identity is a durable operation output bound to the stable operation identity, and retry returns or resolves that same identity.

## 9. Transitions and commit evidence

Each committed semantic operation produces exactly one immutable semantic transition for that commit boundary. A retry produces no additional transition. One transition may contain multiple effects and thereby represent a genuine multi-carrier semantic commit; a workflow with several independently meaningful changes uses several commit boundaries.

The transition is required durable commit evidence. It structurally binds operation identity, transition kind, affected scope, relevant predecessor semantics, successor/effect semantics, and origin kind, including native versus legacy admission where relevant. State presence alone is never transition evidence.

### Legacy admission transitions

A transition publishing imported legacy state is structurally typed as an admission transition or equivalent. It records what TORMENT admitted during migration and never masquerades as the historical native transition that originally created the legacy state. Legacy ambiguity remains attached to the admitted unit.

### Transition effects

Transition effects identify all substrate-governed durable truth changed at one commit boundary, including object revision publication, relationship revision publication, representation-state change, integrity/reconciliation state, legacy-admission state, and later typed substrate-governed families. Effect subjects remain schema-defined and typed; adding a subject family is a schema-versioned change. The model must not become an untyped generic subject/blob merely to avoid evolution.

## 10. Representation model

Representation semantics are immutable at creation: representation identity, exact source revision, representation class, generation, derivation contract/version, encoding/dtype/dimension where applicable, and declared dependencies.

Current representation state directly represents readiness, integrity state or measurement, and operational disposition. It is queryable without history replay, while every durable change is still explained by the transition/history contract. Full representation-revision objects are not required unless later evidence establishes that need.

Representation payload bytes are physically separated from representation metadata inside the initial SQLite core. Metadata-only reads do not require loading or interpreting BLOB bytes. Colocation does not collapse source and representation truth, and later physical payload relocation remains compatible.

Representation dependencies are explicit dependency records. They are not automatically first-class semantic relationships. Consumers declare exact compatible generations and dependencies.

### Representation integrity timing

An integrity expectation for a generation is established at derivation time before publication. It enters the semantic transaction that stores or binds the payload and changes readiness; it must not be created by hashing or otherwise accepting the already-published payload as its own expected truth.

Integrity expectations for exact revisions or representation generations are immutable/versioned. Measurements are append-only observations against those expectations.

## 11. Current state, history, and reconciliation

Current state is directly represented. Normal reads do not reconstruct it by replaying history, and event sourcing is not selected. Transition/history evidence explains semantic change and provides commit/recovery evidence.

Reconciliation preserves four dimensions:

```text
CONDITION
SUBJECT
REASON
OPERATIONAL_DISPOSITION
```

Reconciliation is never a third commit-truth axis. Durable reconciliation-state changes use idempotent semantic operations and transition evidence. They may change determination, usability, or disposition, but never rewrite an historical transition outcome.

## 12. Provenance, lifecycle, governance, and authority

Frozen provenance, lifecycle, governance, and authority distinctions remain structural. Where a committed revision depends on them, they are revision-contained or exact-version referenced so semantic closure holds. Unknown provenance remains legitimate; admission does not fabricate it.

Legacy fields that merely name permission, policy, expiry, lifecycle, governance, or authority without established enforced semantics are admitted as evidence or unknown state. They do not automatically become active native governance or authorization. Active authorization arises only through legitimate authority semantics, never migration convenience.

The structural category model remains capable of distinguishing evidence, intent/proposal, decision record, active authorization, and execution record without implementing future autonomy or skill execution.

## 13. Motifs, deep memory, identity, and Character

The Phase 1/3 motif model remains binding:

```text
motif = derived LOGICAL OBJECT
motif membership = derived LOGICAL RELATIONSHIP
MOTIF_RECONSTRUCTABILITY_PROVEN = NO
```

Motifs use generic object/relationship structures unless actual semantics later require specialization. Not every vector-shaped motif-associated datum, including a possible centroid, is primary/core state merely because it is vector-shaped. Motifs remain non-disposable until reconstructability is established.

Deep-memory derived content uses representation semantics unless independently asserted state genuinely establishes a separate carrier. Use-history, lifecycle, and history may attach structurally without promoting deep payload to a second source truth.

```text
MEMORY_OPTIONAL_IDENTITY = YES
```

Identity and Character definition remain independently representable logical objects. Their existence and presentability do not depend on autobiographical memory, seed-memory rows, motifs, or another memory object. Adaptive/runtime CharacterState remains derivation/evidence, not ontological proof of identity. Character runtime redesign is out of scope.

## 14. Legacy aliases, history, and evidence

Legacy aliases structurally bind source namespace, alias kind, and alias value to native logical identity. Bare legacy EIDs remain source/graph-local aliases and never become universal TORMENT identity through migration. Aliases required by durable migrated references are compatibility state and are not deleted merely because a legacy snapshot later expires.

Legacy preservation does not normalize every old append record into native semantic history. Original immutable source artifacts may remain preserved evidence referenced through admission records. Only explicitly admitted semantic evidence becomes native history.

`MEMORY_CREATE`-like pre-commit events do not establish semantic commitment. Existing optional SQLite sidecar rows remain acceleration, not source truth. Motif events remain unproven for replay.

## 15. Migration and cutover

```text
MIGRATION_MODEL = OFFLINE_ONE_SHOT_ADMISSION_CUTOVER
```

Migration uses staged idempotent admission batches:

1. stop legacy semantic writes;
2. snapshot and preserve legacy artifacts;
3. inventory, classify, and admit into an eligible SQLite core;
4. quarantine ambiguity or corruption;
5. verify admitted aliases, relationships, representations, counts, and integrity;
6. designate the new core authoritative;
7. resume writes against the new core only; and
8. rebuild acceleration.

Indefinite dual-write is forbidden because it would create competing mutable authorities and semantic commit boundaries.

Before new-core semantic writes resume, cutover may be aborted and operation returned to the untouched legacy store. After new-core semantic writes resume, the legacy store is evidence only, not rollback authority. Any later return requires separately authorized reverse-migration/reconciliation design that accounts for every valid new-core committed transition.

## 16. Schema versioning

The database carries substrate schema identity, schema version, core identity, and applied migration/maintenance ledger as required. This is independent of SQLite library version.

Startup distinguishes known compatible schema, older supported but upgrade-required schema, and newer/unknown/incompatible schema:

- known current compatible schema may permit writes subject to normal substrate gates;
- older supported but not explicitly upgraded schema is read-only or refused, never writable; and
- newer, unknown, or incompatible schema refuses writable startup.

No generic automatic self-migration framework is authorized.

## 17. Phase 5 scope and Phase 6 handoff

This phase freezes required native schema semantics and transaction/migration design, not exact physical DDL. The following remain deferred: table and column names, SQL affinities beyond frozen requirements, composite-FK/deferred-constraint patterns, DDL, indexes, identity and idempotency encodings, canonical-intent representation, hash algorithms, vector binary format, busy timeout, checkpoint policy, backup schedule, and production migration commands.

No database was created and no implementation experiment was required. SQLite 3.51.2 remains ineligible for the production semantic core.

The next phase is:

```text
TORMENT MEMORY SUBSTRATE — PHASE 6
DETAILED SQLITE DDL / STORAGE API / IMPLEMENTATION ROADMAP
```

Phase 6 may turn these families into exact SQLite DDL; design same-carrier composite constraints, native identity encodings, canonical idempotency intent, storage APIs, transaction helpers, migration/admission tooling, the bounded qualification suite, and an implementation work breakdown. It remains subordinate to this frozen logical substrate.

## 18. Freeze verdict

```text
MEMORY_SUBSTRATE_PHASE_5_NATIVE_SCHEMA_DESIGN_FROZEN = YES
NATIVE_SQLITE_SCHEMA_RECOMMENDED = YES
OBJECT_REVISION_MODEL_FROZEN = YES
RELATIONSHIP_REVISION_MODEL_FROZEN = YES
OPERATION_TRANSITION_MODEL_FROZEN = YES
REPRESENTATION_MODEL_FROZEN = YES
OFFLINE_MIGRATION_CUTOVER_MODEL_FROZEN = YES
PHASE_0_1_2_3_4_CONTRADICTION_FOUND = NO
ADDITIONAL_REPOSITORY_ARCHAEOLOGY_REQUIRED = NO
PRE_FREEZE_IMPLEMENTATION_EXPERIMENT_REQUIRED = NO
CURRENT_SQLITE_3_51_2_USED_FOR_NEW_CORE = NO
PRODUCTION_CODE_CHANGED = NO
TEST_CODE_CHANGED = NO
MEMORY_SUBSTRATE_PHASE_6_NEXT = YES
```

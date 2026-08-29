# TORMENT Memory Substrate — Phase 1 Logical Model v0.1

**Status:** frozen requirement-level logical semantics.

**Scope:** This document closes Phase 1 of the TORMENT Memory Substrate programme. It defines logical carriers, identity, representation, state-transition, integrity, recovery, and boundary requirements. It selects no storage engine, schema, migration, transaction mechanism, recovery implementation, lock, hash, signature, or runtime change.

## 1. Phase 0 baseline

Phase 0 is reconciled with the following conclusions:

- `CURRENT_STORAGE_IS_AN_EMBRYONIC_CUSTOM_SUBSTRATE`
- `CANONICAL_OPERATIONAL_TRUTH_SHOULD_LEAVE_LOOSE_JSONL`
- `TORMENT_OWNED_LOGICAL_SUBSTRATE_REQUIRED`
- `MULTIPLE_ACCESS_MODELS_REQUIRED`
- `MULTIPLE_PHYSICAL_ENGINES_LIKELY_BUT_NOT_REQUIRED`
- `NEW_LOW_LEVEL_DATABASE_ENGINE_NOT_REQUIRED`

The problem is not that JSONL is inherently insecure. The current weakness is unmanaged canonical persistence without adequate durability discipline, cross-process exclusion, localized integrity, logical transaction boundaries, and recovery semantics. Hardened JSONL may remain appropriate for evidence, audit, and export lanes.

## 2. Substrate definition

> **The TORMENT Memory Substrate is a TORMENT-owned logical persistence contract governing durable identity, state transition, integrity, recovery, semantic relationships and representation dependencies for participating durable semantic state, independently of the physical files, tables or engines used underneath.**

`ONE CONTRACT — NOT ONE ENGINE`

## 3. Logical carriers

The substrate has two logical carrier classes.

### 3.1 Logical object

A logical object is an independently addressable semantic thing. Examples may include a memory, identity, character definition, motif, archive document, proposal, decision, or future skill definition.

### 3.2 Logical relationship

A logical relationship is an independently meaningful durable relationship among logical carriers. Examples may include an asserted graph link, motif membership, derivation relationship, lineage, successor relationship, or cross-object decision relationship.

> **Not every implementation pointer/reference is a logical relationship.**

A relationship becomes first-class only when the relationship itself carries durable semantic meaning, derivation semantics, lifecycle/history, or must survive relocation or migration independently. Shard-row references, cache pointers, and ordinary physical locators are not logical relationships merely because they point somewhere.

Both carrier classes may have current durable state, materialized derivations, semantic history, representations, and accelerations. No carrier is required to possess every category.

## 4. Logical identity

> **Every logical object and first-class logical relationship must possess an identity unambiguous across every namespace in which substrate references may legally resolve.**

Identity must be assignable before the state transition that makes the carrier real, stable under physical relocation, non-reusable within its permitted reference universe, and resolvable without relying on current physical location. Cross-scope references must preserve scope explicitly.

This does not require a flat globally dereferenceable namespace, UUIDs, or a prescribed encoding. It distinguishes:

- **Identity:** what the carrier is.
- **Locator:** where a current representation physically resides.
- **Alias / legacy identity:** an alternate historical identifier resolving to the same logical identity.

Current graph-qualified EIDs are legacy scope-qualified identities or aliases, not universal identities. Clone, move, merge, import, and export must be explicit operation semantics; recovery must never guess which occurred.

## 5. Representation and independent objecthood

> **A derived thing is a representation of carrier X when its semantic validity exists entirely in virtue of X and its derivation contract.**

A derived thing becomes an independent logical object only when state is independently asserted about it that is not merely entailed by its sources and derivation.

- An embedding is a representation.
- An archive chunk is a representation.
- A generated skill artifact is a representation of a skill definition.
- A compressed/deep form is a representation unless independently asserted or edited.
- A motif is a derived logical object because it spans multiple memories and has its own derived state.

Objecthood is not implied merely by an identifier, lifecycle metadata, or accumulated use-history.

## 6. Logical state taxonomy

### 6.1 `PRIMARY_DURABLE_STATE`

Committed state whose current value directly defines a carrier's semantic, lifecycle, governance, or authority condition rather than merely materializing an access or analysis computation. It may originate through assertion, legitimate policy decision, deterministic authorized rule, migration, or another legitimate state-transition mechanism. Primary state is not defined by irrecoverability.

### 6.2 `MATERIALIZED_DERIVATION`

Computed state or representation whose validity depends on declared source carrier revision(s), derivation contract, and generation/dependencies. Runtime may legitimately depend on it, but it never becomes source truth merely because it is operationally important. Derivations are not to be called canonical.

### 6.3 `HISTORICAL_EVIDENCE`

Intentional record of a prior semantic state, state transition, decision, derivation, or operation.

### 6.4 `ACCELERATION`

Performance-oriented projection, cache, or index. Its existence cannot establish semantic truth.

### 6.5 Semantic history and telemetry

Historical-looking records must be distinguished as either semantic history or operational telemetry. Semantic history may require completeness for recovery, revision lineage, authority lifecycle, deletion/revocation, reconstruction, derivation explanation, or commit evidence. It requires substrate-grade durability appropriate to the semantics it explains.

Operational telemetry is observation, debugging, or performance information whose incompleteness does not alter semantic truth. Current `motif_events.jsonl` is not proven-complete semantic history:

`MOTIF_EVENT_COMPLETENESS_FOR_REPLAY = UNPROVEN`

Phase 2 must test that question.

## 7. Representation generations

`DERIVATION_GENERATIONS_REQUIRED = YES`

Every materialized derivation or representation must be able to identify its source carrier revision(s), derivation contract, generation/version, material dependencies, compatibility assumptions, and integrity/readiness state. Representations need not enumerate downstream consumers.

Dependency direction is explicit:

> **Consumers declare the representation generation they depend upon.**

For example, a motif generation may depend on an embedding generation; the embedding generation does not need to maintain a list of every consumer.

### 7.1 Embeddings

> **An embedding is a `MATERIALIZED_DERIVATION` representing a specific memory revision under a specific geometry/derivation generation.**

It is not the memory claim. Changing geometry can change retrieval ordering, clustering, motif behavior, coherence/drift behavior, and downstream recursive behavior. It is therefore semantically consequential to runtime behavior even though it is derived. Multiple generations may coexist; consumers must declare which compatible generation they depend upon. No vector format, provider, or storage choice is made here.

### 7.2 Motifs

> **A motif is a derived logical object. Its membership links are derived logical relationships.**

`MOTIF_RECONSTRUCTABILITY_PROVEN = NO`

Motifs remain `MATERIALIZED_DERIVATION / RECONSTRUCTABILITY_UNPROVEN`. They are not disposable, and replay is not authorized by this document.

### 7.3 Deep memory

> **Deep-memory content derived or compressed from core-memory revisions is a `MATERIALIZED_DERIVATION`, not an independent second copy of source truth.**

Its representation may have identity, generation, lifecycle, and use-history without becoming independent source truth. Spirit Return, warmth, and use events are historical evidence associated with the deep representation. A derived representation becomes an independent logical object only when independently asserted state is added that its sources and derivation do not entail. Compression redesign is outside scope.

### 7.4 Derived relationships

Derived relationships must record the derivation generation and dependencies under which they were produced. A motif-membership relationship, for example, may depend on a motif generation and an embedding generation. This creates no graph schema or relationship ontology.

## 8. Identity and character

Invariant 1 remains preserved. Character definition and identity definition remain logically distinguishable from experiential memory. Adaptive character measurements, such as drift, coherence, or history-derived metrics, are `MATERIALIZED_DERIVATIONS` or `HISTORICAL_EVIDENCE`; they are not ontological proof of identity.

`IDENTITY EXISTS` may remain true while `EXPERIENTIAL MEMORY EXISTS` is false. Seed materialization into memory remains an implementation workflow, not an ontological requirement. No historyless-character implementation is opened.

## 9. Commit truth and representation readiness

> **Each durable state transition of a logical carrier becomes real at exactly one logical commit boundary.**

A workflow may contain several separately committed state transitions. Proposal creation, decision making, and promotion execution are conceptually separate transitions rather than one giant transaction.

Commit truth is `COMMITTED` or `NOT_COMMITTED`. Once determined for a transition, it is immutable historical fact. A failed or incomplete recovery investigation may be unable to determine the outcome immediately, but that uncertainty belongs to reconciliation or disposition, not to a mutable historical outcome.

`COMMITTED / VECTOR_PENDING` is valid when expressed on separate axes:

```text
commit = COMMITTED
vector_readiness = PENDING
```

> **Carrier existence and representation-dependent capability readiness are different facts.**

A committed memory exists without its vector. A capability requiring geometry remains unavailable until the required representation is ready. Periods of representation pendency may cause later derived-state divergence; their pendency and resolution must therefore be durably explainable.

## 10. Four orthogonal axes

The following distinctions are normative, without freezing exact schema enum names.

| Axis | Question | Conceptual values |
|---|---|---|
| Commit truth | Did the durable state transition become real? | `COMMITTED`, `NOT_COMMITTED` |
| Representation readiness | Is a particular representation class/generation usable? | `READY`, `PENDING`, `ABSENT`, `INCOMPATIBLE` |
| Integrity measurement | Did an artifact satisfy its verification expectation? | `VERIFIED`, `UNVERIFIED`, `FAILED` |
| Operational disposition | May normal runtime currently consume it? | `AVAILABLE`, `WITHHELD`, `RECONCILIATION_REQUIRED`; `QUARANTINED` may be retained here |

Commit truth is immutable once established. Integrity is a measurement; a repaired or replaced artifact receives a new measurement rather than rewriting historical verification. Operational disposition is a decision or policy outcome, not an integrity measurement.

## 11. Recovery and integrity

> **Recovery must determine logical commit truth from explicit durable evidence rather than inferring it from residue.**

Recovery must be non-guessing, idempotent, unable to create duplicate logical carriers from one interrupted transition, able to enumerate reconciliation-requiring conditions in advance, and able to localize integrity failures. This selects no rollback, write-ahead log, replay, roll-forward, or two-phase-commit mechanism.

> **A carrier or representation that fails required integrity verification may not silently enter trusted normal state.**

Failures must be localized to the affected carrier or representation wherever possible. A failed optional acceleration does not invalidate primary semantic state. Primary state failing required integrity cannot be silently skipped while the corpus appears healthy. Verification result and operational disposition remain distinct. No hashing or signing implementation is selected.

## 12. Scope, fate, current state, and absence

Semantic scope and fate domain are separate dimensions.

- **Semantic scope** answers whose state it is or within which logical namespace it resolves, such as workspace, agent, or shared domain.
- **Fate domain** answers what shares a storage or security destiny, including possible encryption, backup, migration, restore, and deletion/erasure requirements.

Potential future fate-domain concerns include vector lanes, authority lanes, per-agent memory, and archive, but no actual values are frozen. Access authorization remains governed separately by authority semantics. Filesystem paths are neither semantic scope nor fate domain.

Current state answers, “What is true/effective now?” History answers, “What transition, decision, or derivation occurred?” No event-sourcing requirement follows.

The minimum absence distinction is:

- **Absent:** no surviving evidence establishes current or historical existence; this does not prove a carrier never existed.
- **Present / active:** the carrier exists and normal disposition permits use.
- **Present / inactive or deleted:** historical evidence establishes existence plus later deletion, revocation, or inactivation.

`ABSENT_FROM_A_VIEW` is a query result, not object state. `REVOCATION_PRESERVES_HISTORY` versus `ERASURE_MAY_DESTROY_HISTORY` remains open. No erasure design is made.

## 13. Authority, modality, and future skills

Invariant 3 remains preserved. Evidence, intent, decision, active authorization, and execution must remain structurally distinguishable without interpreting natural-language content.

> **The existence of a carrier or representation never confers execution authority merely by existence.**

No stored representation is a capability. Inert authority-shaped legacy fields must not be migrated into active authority merely because they are persisted. No authorization implementation is opened.

Invariant 2 remains preserved. Future substrate semantics must be able to distinguish origin/authority, source channel, current representation, derivation status, material derivation provenance, relevant uncertainty, and optional source/capture time. Unknown is legitimate; raw media retention is not required. Brainvision integration remains held.

A future skill definition may be a versioned logical object. Its representations may include implementation artifacts, compiled/executable artifacts, tests, and documentation; its history may include provenance, revisions, and test results. The following remains binding:

```text
STORED != EXECUTABLE
EXECUTABLE != ACTIVATED
ACTIVATED != AUTHORIZED
```

> **No representation class, including an executable artifact representation, is itself an execution capability.**

No MCP or skill-runtime design is opened.

## 14. Substrate governance boundary

> **The logical substrate semantically governs durable state that participates in TORMENT's shared semantic truth or in state transitions that determine that truth. Durable state explicitly isolated from those semantics may remain outside semantic governance while still adopting compatible durability/fate protections.**

Governed examples include core memory, durable semantic relationships, archive/reference/environment truth, identity/character durable semantics, deep-memory representations, Hivemind durable semantic/decision state, closure/conflict/proposal state, and future authority records.

Brainvision under integration hold, kernel transient runtime, jobs as operational workflow state, and caches/indexes as acceleration remain outside current semantic governance. Trajectory remains observability/history rather than core semantic reconstruction truth unless a later explicit decision changes its role. Being governed does not mean sharing one physical engine.

## 15. Binding model

> TORMENT durable semantics are carried by logical objects and first-class logical relationships, not by files, rows or database engines. Each durable carrier state transition becomes real at one logical commit boundary. Primary durable state, materialized derivations, semantic history and acceleration remain distinct. Representations bind to committed carrier revisions through explicit derivation generations; downstream consumers declare the generations they depend upon.
>
> Commit truth, representation readiness, integrity measurement and operational disposition are orthogonal. A carrier may exist while a required optional representation remains pending. Integrity failure does not silently redefine commit truth, and quarantine/withholding is a disposition rather than a verification result.
>
> Semantic scope is separate from fate domain and from authority. Durable identity remains unambiguous across every namespace in which references may legally resolve, without requiring a globally dereferenceable namespace or tying identity to physical location.
>
> Derived content never becomes independent source truth merely because it has an identifier, lifecycle or use-history. Relationships spanning multiple carriers are modelled directly when the relationship itself carries durable semantic meaning.
>
> Stored state or representations never become execution authority merely through persistence.

## 16. Open Phase 2 questions

Phase 2 must explicitly address, through separate authorized work:

- exact motif reconstructability and motif-event completeness;
- embedding row-map reconstructability and exact vector-generation compatibility tests;
- asserted-versus-derived relationship inventory;
- recovery under interrupted legacy writes and concurrent-writer semantics;
- integrity acceptance rules;
- legacy EID migration/aliasing;
- fate-domain requirements and semantic-history retention;
- revocation versus future erasure; and
- legacy partial-artifact admission or quarantine.

No physical-engine recommendation is made.

## 17. Freeze verdict

```text
MEMORY_SUBSTRATE_PHASE_0_RECONCILED = YES
MEMORY_SUBSTRATE_PHASE_1_LOGICAL_MODEL_FROZEN = YES
LOGICAL_OBJECT_CARRIER_FROZEN = YES
LOGICAL_RELATIONSHIP_CARRIER_FROZEN = YES
COMMIT_READINESS_INTEGRITY_DISPOSITION_SEPARATED = YES
SEMANTIC_SCOPE_FATE_DOMAIN_SEPARATED = YES
AI_CREATED_SKILL_FUTURE_COMPATIBLE = YES
PRE_DATABASE_INVARIANTS_PRESERVED = YES
PHYSICAL_STORAGE_DESIGN_OPENED = NO
CODE_OR_TEST_CHANGE_COUNT = 0
```

**Current authorized activity:** `NONE / HOLD pending explicit Phase 2 opening`.

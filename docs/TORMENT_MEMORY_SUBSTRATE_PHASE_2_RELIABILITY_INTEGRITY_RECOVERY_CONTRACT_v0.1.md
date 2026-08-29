# TORMENT Memory Substrate — Phase 2 Reliability, Integrity, and Recovery Contract v0.1

**Status:** frozen requirement-level reliability, integrity, and recovery semantics.

**Scope:** This document closes Phase 2. It freezes logical requirements for a future physical substrate architecture; it does not choose a storage engine, schema, query language, vector format, transaction mechanism, lock, write-ahead log, recovery algorithm, hashing/signing mechanism, migration, or runtime implementation.

```text
MEMORY_SUBSTRATE_PHASE_0_RECONCILED = YES
MEMORY_SUBSTRATE_PHASE_1_LOGICAL_MODEL_FROZEN = YES
MEMORY_SUBSTRATE_PHASE_2_RELIABILITY_CONTRACT_FROZEN = YES
PHYSICAL_STORAGE_DESIGN_OPENED = NO
```

## 1. Commit determinacy

A logical carrier transition is `COMMITTED` only when the declared durable protocol contains sufficient durable evidence and semantic information for recovery, after loss of volatile process or OS state, to establish that the transition became semantically real and restore or complete its required semantic successor without guessing.

Residue never establishes commitment. The future-native protocol must make `NOT_COMMITTED` positively determinable rather than inferring it merely from failure to locate expected evidence.

If required evidence is missing, unreadable, damaged, or otherwise insufficient, the result is a reconciliation condition. It is not a third commit-truth value.

```text
COMMITTED
NOT_COMMITTED
```

## 2. Outcome versus determination

The historical outcome of a transition is immutable. The system's present determination of that historical outcome is an epistemic/recovery state and may change when valid evidence is recovered or verified. Reconciliation may update the determination; it never creates or rewrites the historical outcome.

## 3. Durability barrier

TORMENT may not report `COMMITTED` merely because a write API accepted data. Before commitment is acknowledged, sufficient commit evidence and semantic information must have crossed a durability barrier such that abrupt process or host failure and restart, with the durable medium intact, does not erase the transition, turn it into `NOT_COMMITTED`, or cause duplicate semantic application.

This selects no `fsync`, WAL, database transaction, filesystem, rollback, roll-forward, two-phase-commit, or physical-engine mechanism.

Optional downstream representations need not be `READY` when primary semantic commitment occurs:

```text
COMMITTED / REPRESENTATION_PENDING
```

remains valid.

## 4. Idempotency and revision compatibility

Every retryable durable operation requires a stable operation identity, or equivalent deterministic idempotency identity, that can be reused after interruption or a lost response.

The determinations “has this durable operation already committed?” and “is its predecessor/current revision still compatible?” must participate in one non-raceable logical commit decision.

A retry may return or recover the committed result, complete declared pending work, or report a genuine conflict. It may not create duplicate logical carriers, relationships, successor revisions, or derivation generations.

This document does not freeze who generates the operation identity. It may be caller-generated, coordinator-generated, substrate-issued before semantic side effects, or another later design, provided retry can reliably recover or reuse the same identity.

## 5. Creation and identity concurrency

Creation has no predecessor revision; predecessor compare-and-commit alone cannot protect it. Logical carrier identity must be established before publication, and future substrate semantics must prevent or detect conflicting identity allocation within every namespace where that identity may legally resolve.

Identity allocation need not be a separate durable transaction. This document selects neither an identity encoding nor an allocator.

## 6. Joint semantic invariants

Workflows are not converted into giant transactions. However, where one semantic transition asserts an invariant that exists only when several carriers or relationships become jointly true, either:

- the required set becomes atomically visible; or
- incomplete intermediate members remain operationally withheld until the joint invariant is complete.

Deterministic eventual recovery alone is insufficient if normal readers can consume partial state as though the joint invariant already holds. This requirement does not imply one physical engine or distributed transactions.

## 7. Localized integrity

Integrity must be measurable at useful granularity for:

- primary carrier revision/state;
- first-class logical relationship;
- required commit or semantic-history evidence;
- materialized derivation generation; and
- acceleration.

Integrity measurement and operational disposition never rewrite historical commit truth. Failure of an optional derivation preserves source truth and withholds only dependent capability. Failure of an acceleration preserves semantic truth and permits rebuild or withholding. Failure of required primary semantic state or required commit evidence may not be silently skipped while the corpus appears healthy.

## 8. Generation and relationship binding

Consumers of materialized derivations must establish compatibility with the representation generation they consume, including declared source revisions, derivation contract, material dependencies, and compatibility assumptions. A generation mismatch must not be silently consumed.

Each first-class logical relationship kind must additionally declare its endpoint-binding semantics. A relationship may bind to logical identity independent of current revision, a particular endpoint revision, or another explicitly declared endpoint condition. No particular relationship ontology is selected, and runtime readers may not guess binding semantics.

## 9. Semantic history

TORMENT is not converted to event sourcing. History becomes authoritative for a recovery or reconstruction function only when it is complete enough for that declared function and contains sufficient integrity and continuity evidence to detect material incompleteness.

A history stream whose gaps cannot be detected may not silently serve as authoritative reconstruction evidence. Operational telemetry does not become semantic recovery truth merely because it exists.

```text
MOTIF_RECONSTRUCTABILITY_PROVEN = NO
```

Motifs remain non-disposable.

## 10. Reconciliation model

No implementation enum spellings are frozen. The conceptual separation is:

```text
CONDITION
SUBJECT
REASON
OPERATIONAL_DISPOSITION
```

Recognizable condition families must include at least:

- uncommitted residue;
- committed transition requiring completion;
- commit determination unavailable;
- integrity failure;
- current-state/history conflict;
- generation/dependency mismatch;
- identity/scope conflict;
- operation/revision conflict; and
- legacy material requiring admission or reconciliation.

`CLEAN_CONSISTENT` is the absence of an active reconciliation condition, not a reconciliation condition itself. A future-native commit-determination-unavailable condition is a surfaced protocol or integrity defect, not a normal third commit outcome.

## 11. Recovery idempotence

Recovery must itself be restartable and idempotent. An interrupted recovery run re-enters the durable condition that still exists. It must not mint a new semantic transition because recovery restarted, duplicate semantic state, change durable operation identity, or create an unbounded family of new semantic reconciliation states.

## 12. Legacy admission

Legacy ambiguity must be attached to the smallest affected durable unit rather than automatically tainting an entire logical carrier forever. The unit may be a carrier revision, relationship revision, history record, representation generation, or legacy imported artifact.

A later future-native revision does not inherit legacy ambiguity unless it materially depends on the ambiguous state. Migration and recovery must never fabricate missing identity, semantic scope, provenance, history, authority, or commit truth.

## 13. Authority vocabulary

`COMMIT_AUTHORITY` is not normative terminology. Prefer:

```text
COMMIT_DECISION_POINT
COMMIT_DETERMINATION
AUTHORITATIVE_COMMIT_EVIDENCE_PATH
```

The commit decision is solely a persistence/durability determination. It confers no agency, intent, decision authorization, active authorization, capability, activation, or execution right. It is not one of the frozen Invariant-3 authority categories.

## 14. Physical-substrate constraint

> **The eventual physical architecture must provide atomic logical publication of the required commit set, or an equivalent crash-safe protocol whose recovery deterministically yields the same semantic committed/not-committed outcome and whose incomplete intermediate state is not consumable as complete semantic state.**

This selects no storage engine, schema, query language, WAL, locking algorithm, rollback model, roll-forward model, replay model, two-phase commit, vector format, or number of physical engines.

It preserves:

```text
ONE CONTRACT — NOT ONE ENGINE
MULTIPLE_ACCESS_MODELS_REQUIRED
MULTIPLE_PHYSICAL_ENGINES_LIKELY_BUT_NOT_REQUIRED
NEW_LOW_LEVEL_DATABASE_ENGINE_NOT_REQUIRED
```

## 15. Requirements versus verification

```text
PHASE_2_IS_A_REQUIREMENTS_FREEZE_NOT_AN_IMPLEMENTATION_VERIFICATION = YES
```

The following remain open evidence or design questions and must not be presented as verified by Phase 2:

- current legacy write behavior under abrupt host or power failure;
- exact motif replay completeness and deterministic equivalence;
- embedding row-map reconstructability;
- embedding/geometry generation compatibility mechanics;
- complete asserted-versus-derived relationship inventory;
- legacy EID alias/admission design;
- integrity acceptance criteria;
- actual competing-process behavior of legacy persistence;
- per-carrier semantic-history retention; and
- revocation versus future erasure.

They are not automatically mandatory Phase 3 experiments. Phase 3 investigates only questions materially necessary to choose or safely migrate to a physical substrate architecture.

## 16. Phase 1 preservation

```text
PHASE_1_CONTRADICTION_FOUND = NO
```

All three pre-database invariants remain preserved:

- `MEMORY-OPTIONAL IDENTITY`
- `MODALITY-INDEPENDENT INGEST`
- `AGENCY / AUTHORITY SEPARATION`

No persistence terminology may grant authority.

## 17. Phase 3 handoff

The next phase is:

```text
TORMENT MEMORY SUBSTRATE — PHASE 3
PHYSICAL SUBSTRATE ARCHITECTURE
```

Phase 3 may compare actual candidate physical architectures against the frozen Phase 0, Phase 1, and Phase 2 requirements. It must begin from architecture requirements, not from the question “which database should TORMENT use?”

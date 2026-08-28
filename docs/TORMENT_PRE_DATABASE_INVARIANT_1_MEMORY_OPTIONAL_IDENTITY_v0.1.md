# TORMENT Pre-Database Invariant 1 — Memory-Optional Identity v0.1

> **STATUS: REQUIREMENT-LEVEL / PRE-DATABASE INVARIANT / NON-IMPLEMENTING.**
>
> This document freezes a semantic requirement. No runtime mode is implemented or authorized, and no implementation lane, database lane, model/caller lane, or new kernel consumer is opened or authorized by it.

## 1. Purpose and current factual boundary

This invariant records the conclusion of the Memory-Optional Identity archaeology:

`IDENTITY_CORE_IS_SEPARABLE_BUT_RUNTIME_IS_MEMORY_BOUND`

Current TORMENT has independent seams for persistent agent identity, persistent CharacterSeed definition, CharacterState storage, seed-derived kernel initialization/modulation, and seed-derived presentation content. Its adaptive character operation remains coupled to seed-canon MemoryGraph rows, seed motif geometry, historical retrieval, drift, gravity correction, relational development, and derived identity anchors.

Therefore, a full present TORMENT character is not historyless without code changes. This finding does not authorize such changes.

## 2. Frozen terminology

### MEMORY-OPTIONAL IDENTITY

The architecture must permit character identity definition to exist independently of durable experiential history.

### HISTORYLESS CHARACTER

A reduced character form that retains explicit identity definition and permitted transient/session state while deliberately possessing no durable autobiographical or adaptive history.

The terms *memoryless character* and *stateless character* are rejected except when explaining this distinction: durable identity/configuration may persist, and transient kernel/session state may exist, without becoming experiential history.

## 3. Required conceptual decomposition

### L1 — Identity Definition

Declared identity: agent identity, seed ID, character name, seed text, and explicit character configuration. It does not require experiential history.

### L2 — Definition Materialization

The current implementation renders definition into `seed_canon` memory rows, a seed motif/basin, and seed EID/motif references. Definition materialized into memory is not the same thing as experienced history. This is a current implementation mechanism, not a requirement that identity always reside in historical memory.

### L3 — Computational Derivation

Seed-derived computational conditions, including current kernel modulation, do not themselves require MemoryGraph. Their currently load-bearing consequences primarily land in memory/collective processing. This does not claim that a historyless runtime already receives a meaningful independent behavioral effect from that derivation; whether it should later do so is parked.

### L4 — Identity Presentation

Seed-derived identity information may be presented to a caller or model without inherently requiring historical memory. Current orchestration nevertheless gates normal character-context presentation behind memory-derived seed-motif state. That coupling is a current implementation fact, not the invariant.

### L5 — Identity History

Durable accumulated experience—autobiographical memory, relational memory, situational history, and historical interactions—requires durable history by definition.

### L6 — Identity Adaptation

History-derived change—drift, gravity correction, derived identity anchors, relational development, and learned identity changes—requires history.

### L7 — Transient State

Current-turn, session, and kernel state is not durable experiential history. It may exist in a historyless character only if it is not silently carried forward as durable history.

## 4. Binding invariant

> **A TORMENT character's explicit identity definition must remain representable and expressible independently of durable autobiographical or adaptive history. Persistence of identity/configuration is not itself experiential memory. Current implementation may materialize identity into memory geometry, but those derived memory artifacts must not become the sole ontological proof that the character exists. Disabling durable history may remove drift, relational continuity, learned anchors and adaptation; those properties must then be represented as absent rather than falsely reported as zero or stable.**

> **Full adaptive TORMENT character semantics remain unchanged. Memory-optional identity permits a reduced historyless mode; it does not redefine the full character downward.**

The following rules are frozen:

1. Identity definition and experiential history are distinct.
2. Identity persistence and autobiographical memory are distinct.
3. Definition materialization and experienced memory are distinct.
4. Identity continuity and experiential continuity are distinct.
5. A historyless character must not claim remembered relationships, learned history, drift, adaptive anchors, or long-term experiential continuity.
6. Undefined historical/adaptive state must be represented as absent/undefined, never silently as `0`, `"stable"`, or an equivalent claim.
7. Ephemeral current-turn/session context is compatible with this invariant only when it is not durably carried forward as history.
8. The same character architecture must support reduced and full forms; this invariant implies no parallel character subsystem.
9. Existing `TORMENT_CHARACTER_ENABLE=0` behavior does not satisfy this invariant: it disables selected character machinery while memory remains available, so it operates on the wrong axis.
10. Future database/substrate work must preserve these distinctions.

## 5. Kernel clarification

Seed-derived kernel modulation is computable without MemoryGraph, and kernel state may evolve transiently during an operation. Production restart currently re-derives character conditions from seed rather than automatically restoring kernel experiential state. Same identity definition and same experiential continuity are therefore not the same thing.

The current character-conditioned kernel's load-bearing effects primarily land in memory/collective mechanics. This invariant does not authorize a new non-memory kernel consumer. Whether a future historyless character should have additional TORMENT-specific computational consequences is a separately gated runtime question.

## 6. Constraint carried into future Memory Substrate design

The future substrate must be capable of representing separately:

```text
DECLARED_IDENTITY
DEFINITION_MATERIALIZATION
EXPERIENTIAL_HISTORY
ADAPTIVE_DERIVATION
```

The exact schema and names are not selected here. This is semantic separation only. A database design must not force `character exists == historical memory rows exist`, and it must not interpret durable identity configuration as autobiographical history.

## 7. What this does not authorize

- No historyless runtime implementation.
- No character flag, new character class, or alternate Fabric.
- No prompt redesign, new model caller, or new kernel consumer.
- No memory migration, database schema, or storage-product selection.
- No deletion or alteration of existing seed-canon semantics.
- No change to full adaptive character behavior.

## 8. Closure posture

This invariant is closed at requirement level only. It records a constraint for later, explicitly authorized work; it opens neither an implementation lane nor a database design lane.

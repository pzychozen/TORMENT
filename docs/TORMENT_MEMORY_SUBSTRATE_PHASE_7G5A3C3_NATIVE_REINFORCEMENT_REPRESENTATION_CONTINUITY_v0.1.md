# TORMENT Memory Substrate — Phase 7G5A3C3

## Native reinforcement and representation continuity

Phase 7G5A3C3 adds an unwired, staging-safe, native-only reinforcement
primitive: `NativeMemoryReinforcementService`.  It owns mutation and embedding
continuity for an already selected memory.  It does not own duplicate search,
similarity thresholds, contradiction checks, reinforce-versus-create choice, or
incoming provenance choice; those remain outside A3C3 and remain legacy-owned
until a later qualified routing phase.

```text
selection = outside A3C3
mutation and E1 -> E2 continuity = A3C3
```

There is no Fabric, DomainRouter, Character, runtime-binding, startup, schema,
or activation integration in this phase.

## Source successor

The request fixes a scoped EID, exact expected R1 UUID, exact expected current
E1 UUID, and caller-supplied reinforcement timestamps.  On a first execution
the source operation requires all of the following:

```text
EID -> current LEGACY_CORE_NODE R1
R1 authority_category = NOT_APPLICABLE
explicit R1 governance child
explicit R1 provenance reference
exact current qualified E1
```

The source operation publishes one semantic transition containing one object
successor effect and output:

```text
R1 -> R2
same object UUID
same scoped EID alias
same scope, lifecycle, governance_state, authority, and provenance_id
exact copied R2 governance child
```

No provenance row is created or changed.  Missing governance or provenance
fails closed; `PROVENANCE_BACKFILL_ON_NATIVE_REINFORCEMENT = DEFERRED`.

The pure patch preserves frozen legacy mutation math:

```text
ordinary: strength = round(min(0.98, old + (1 - old) * 0.3), 4)
tool_result: strength = round(old, 4)
always: last_reinforced, last_reinforced_ts, reinforcement_count + 1
tool_result only: last_tool_refresh_ts
```

Tool-result classification comes only from the structural provenance row’s
`source_channel == "tool_result"`; no payload provenance shadow is read.
Symbol and resonance fields are inherited untouched.

## E1 to E2 continuity

R2 source publication and representation publication remain deliberately
separate.  After R2 is committed, E1 is historical evidence bound to R1 and is
not current-memory geometry.  A3C3 revalidates its known historical witness,
then uses the existing representation service operations:

```text
1. R2 reinforcement source operation
2. E2 PENDING, bound to R2
3. E2 SHA-256 expectation
4. E2 READY / USABLE
```

E2 copies E1’s bytes byte-for-byte, not by numerical equivalence,
normalization, serialization, or regeneration.  It preserves class,
generation, derivation contract, encoding, dtype, dimension, expected byte
length, and declared material dependencies.  E1 is not added as an invented
dependency.  E1 remains bound to R1 forever; it is never retargeted.

The shared `NativeCompatEmbeddingReader` has two intentional modes:

```text
current qualified selection       -> first R2 source qualification
exact known historical read       -> E1 continuity after R2 is current
```

This is also used by A3B’s motif reader, preserving its raw qualified float32
read contract and eligibility behavior.  Finite zero vectors remain valid
continuity inputs: A3C3 is not a duplicate-search decision layer.

## Partial workflow and retry

`R2 committed / E2 unavailable` is valid.  In that state current embedding
search and current motif geometry exclude the memory, while its identity-bound
motif membership remains intact.  Retrying the same base identity recovers R2,
revalidates historical E1, and resumes the first missing representation step.
It never creates R3 or E3.  A second independently authorized request may
create R3/E3 from R2/E2.

The durable source intent binds the caller retry contract, exact calculated
patch, current provenance/governance facts, and the complete E1 descriptor,
dependencies, byte length, and SHA-256 witness.  Changed caller input under
the same base idempotency identity conflicts rather than recalculating against
R2.

## Deliberate exclusions

```text
REINFORCEMENT_SELECTION_IMPLEMENTED = NO
CONTRADICTION_GUARD_MOVED_TO_NATIVE = NO
MOTIF ATTACH / CREATE / SUCCESSOR / MEMBERSHIP MUTATION = NO
R2 + E2 one semantic transaction = NO
incoming duplicate embedding replacement = NO
generic compatibility patch behavior change = NO
```

The phase does not alter legacy MemoryGraph or motif behavior and does not
open native routing, dual reads/writes, cutover, native activation, or
authority expansion.

# TORMENT Memory Substrate — Phase 9D P0

## Identity admission and TORMENT behavior/parity policy

**Status:** frozen Phase-0 policy authority.  Documentation only; it authorizes
neither a runtime change nor real-root activation.

**Basis:** Phase 9D-R0 root-native runtime architecture, P0A/P0B evidence
archaeology, adversarial review, and P0C factual reconciliation.

## 0. Freeze boundary

This document freezes policy, not a production profile or a claim about a real
root.  It creates no schema, migration, adapter, test, qualification harness,
selector, admission, or runtime behavior.

```text
PHASE_9D_P0_POLICY = PASS
DOCUMENTATION_ONLY = YES
REAL_ROOT_CONTACT = NO
REAL_MEMORY_MODEL_CONTACT = 0
REAL_MEMORY_REEMBED_AUTHORIZED = NO
REAL_PRODUCTION_ACTIVATION = NOT_AUTHORIZED

TORMENT_MATHEMATICS_PRESERVED = YES
MATHEMATICAL_FORMULA_CHANGES_REQUIRED = NO
MATHEMATICAL_FORMULA_DUPLICATES_PRESENT = YES
BLOCKER_5_REOPEN_REQUIRED = NO
```

Every use here of cognition, query cognition, cognition implementation, or
cognition owner means **MAIN TORMENT COGNITION**, unless the text expressly
states otherwise.  The policy makes no repository-wide one-cognition claim.

## 1. P0A — external identity and scope admission

### 1.1 Four distinct operations

The following operations are distinct and must not be collapsed:

| Operation | Frozen responsibility |
|---|---|
| **Origination** | An authorized caller requests identity or admission action. |
| **Workspace-local admission** | Workspace/scope machinery validates structural coherence, scope kind, qualifiers, and intra-workspace containment/collision rules. |
| **Root-membership admission** | A root-native membership relation records the narrow fact that a semantic memory scope is a lawful member of one root-native profile generation. |
| **Storage / enforcement** | Native storage persists admitted internal facts, derives qualified internal state, enforces constraints, and refuses invalid action. |

```text
AUTHORIZED_CALLER_OPERATION = IDENTITY / ADMISSION REQUEST ORIGINATOR
CALLER_MAY_SELF_LEGALIZE_NATIVE_SCOPE = NO
ROOT_MEMBERSHIP_REQUIRES_EXTERNAL_WITNESS = YES
```

Request authentication and caller identity do not, by themselves, make a caller
an independent authority over root membership.

### 1.2 Existing-fact recovery versus new-fact lawfulness

For existing facts, the following persistence surfaces may provide recovery
evidence, exact-match validation, collision detection, and continuity:

| Existing fact | Recovery/validation surface | Not established by that surface |
|---|---|---|
| Workspace | Workspace metadata | Lawfulness of a brand-new externally meaningful workspace identity |
| Private agent | `IdentityStore` | Lawfulness of a brand-new externally meaningful agent identity |
| Shared domain | Domain declarations and policies | Lawfulness of a brand-new externally meaningful domain declaration |

Workspace and scope machinery own workspace-local structural coherence,
scope-kind validity, qualifier validity, and intra-workspace containment and
collision rules.  They are not promoted by this policy into root-wide identity
or root-wide cognition ownership.

The root-native membership relation owns exactly this fact:

> This semantic memory scope is currently a lawful member of this root-native
> profile generation.

The repository does not currently identify a verified general external owner
that can originate the witness for that fact.  This is deliberately frozen as a
pre-activation gate rather than invented in Phase 0.

```text
NAMED_EXTERNAL_ADMISSION_OWNER = PRE_ACTIVATION_GATE
NEW_EXTERNAL_AUTHORITY_COMPONENT_REQUIRED = NO_CURRENT_EVIDENCE
```

`NO_CURRENT_EVIDENCE` is not `PROHIBITED`: later exact evidence may justify a
component, but this policy neither requires nor forecloses it.

### 1.3 SQLite/native-substrate authority boundary

```text
SQLITE_MAY_ORIGINATE_EXTERNAL_IDENTITY = NO
SQLITE_MAY_DECLARE_LAWFUL_ROOT_MEMBERSHIP_WITHOUT_WITNESS = NO
```

Once external authority and an admissible witness are present, SQLite/native
storage may create internal surrogate keys, revisions, aliases, indexes,
storage metadata, admitted internal relationships, qualified materialized
derivations, and constraint-driven refusals.  It may perform internal semantic
computation.  None of those actions may silently become the origin of an
externally asserted or externally owned TORMENT fact.

The boundary is semantic authority, not an overbroad prohibition on internal
values or computation.

```text
SQLITE_MAY_ORIGINATE_ANY_SEMANTIC_VALUE = NOT_A_FROZEN_CLAIM
```

## 2. P0B — lawful behavior, parity, and profile admission

Three objects remain separate.

### Object A — lawful TORMENT behavior contract

The behavior contract describes TORMENT itself.  For every behavior it records
what exists, its conditions, affected state/output/future behavior, and its
failure disposition.  Native implementation capability never defines the
contract.

```text
NATIVE_CAPABILITY_DEFINES_TORMENT_LAWFULNESS = NO
```

### Object B — native parity / deficit register

For every lawful behavior, native support is classified independently as:

```text
QUALIFIED | PARTIAL | NO_PARITY | UNRESOLVED
```

A deficit means native cannot yet faithfully preserve the behavior.  It does
not permit a redefinition of TORMENT that removes the behavior.

```text
NATIVE_DEFICIT_IS_NOT_PERMISSION_TO_REDEFINE_TORMENT = YES
NATIVE_DEFICIT_IS_PERMISSION_TO_REMOVE_TORMENT_EFFECT = NO
```

### Object C — selected active profile and admission fact

An active profile selects which lawful effects are applicable.  Native
activation is refused whenever an applicable effect lacks qualified native
parity; omission is allowed only when the selected policy explicitly makes the
effect inapplicable.

```text
EFFECT_APPLICABLE_UNDER_SELECTED_PROFILE
AND REQUIRED_NATIVE_PARITY_NOT_QUALIFIED
= ACTIVATION_REFUSED
```

Neither a disabled repository default, a missing native staging feature, nor
implementation inconvenience establishes inapplicability.

## 3. Behavior-classification policy

The classification vocabulary is:

```text
CORE_WRITE_SEMANTIC
PROFILE_CONDITIONAL_SEMANTIC
SEPARATE_PUBLIC_OPERATION
EXPLICITLY_INAPPLICABLE_UNDER_PROFILE
UNRESOLVED
```

Classification is based on verified behavior and profile conditions, never
solely on source defaults.

| Lawful behavior/effect | Frozen class | Policy consequence |
|---|---|---|
| Canonical create/reinforcement | `CORE_WRITE_SEMANTIC` | Preserve its write result and boundary semantics. |
| Motif attach/creation associated with canonical creation | `CORE_WRITE_SEMANTIC` | Preserve as part of the ordinary write behavior. |
| Canonical flush/commit boundary | `CORE_WRITE_SEMANTIC` | Preserve commit/abort visibility and result disposition. |
| World and ordinary trajectory behavior | `CORE_WRITE_SEMANTIC` | Its durable representation/owner remains profile-qualified; this is not a claim of completed native qualification. |
| Conflict persistence | `PROFILE_CONDITIONAL_SEMANTIC` | Parity is required whenever its lawful conditions apply. |
| Character seed/state, drift, and gravity | `PROFILE_CONDITIONAL_SEMANTIC` | Parity is required whenever Character applies. |
| SRG, Hivemind, derived/maintenance effects, and checkpoint behavior | `PROFILE_CONDITIONAL_SEMANTIC` | Each needs its own applicability and parity disposition. |
| Proposal submission under lawful coupling/policy conditions | `PROFILE_CONDITIONAL_SEMANTIC` | Its effect is not inferred merely from a default. |
| Direct shared ingest where applicable | `PROFILE_CONDITIONAL_SEMANTIC` | Requires profile-specific parity. |
| Proposal materialization/processing | `SEPARATE_PUBLIC_OPERATION` | It is not implied by ordinary ingest alone. |
| Compression/deep memory in the current qualified native core-staging profile | `EXPLICITLY_INAPPLICABLE_UNDER_PROFILE` | This is a current-profile fact, not a universal TORMENT law. |
| Auto motif split | `UNRESOLVED` | An applicable unresolved behavior blocks activation. |
| Unenumerated durable paths/owners | `UNRESOLVED` | An applicable unresolved owner blocks activation. |

If a future production profile enables compression or deep memory, current
core-staging qualification is insufficient for its activation.

## 4. Failure-disposition parity

```text
FAIL_SOFT_PARITY = PARITY OF FAILURE DISPOSITION, NOT TRY/EXCEPT SHAPE
FAILURE_DISPOSITION_PARITY_REQUIRED = YES
```

Parity must preserve the distinction between failure before or after canonical
commit; primary memory retained or aborted; secondary durable state missing;
reported versus suppressed failure; an error returned after durable primary
state; and whether a later read can detect an absence.  A shared exception
shape is not semantic parity.

### 4.1 Canonical commit failure

```text
CANONICAL_COMMIT_FAILURE_DISPOSITION = PRE_POSTWRITE_FAIL_CLOSED
```

The verified behavior aborts the unflushed node, returns
`canonical_commit_failed`, and does not expose uncommitted memory as successful
canonical state.

### 4.2 Conflict failure

```text
CONFLICT_FAILURE_DISPOSITION = POST_CANONICAL_COMMIT_FAIL_SOFT
```

The primary memory remains committed; the conflict record may be absent; and
the conflict failure is locally suppressed.  Conflict parity therefore includes
both conflict semantics and this post-commit failure boundary whenever conflict
is applicable.  It must not be conflated with canonical commit failure.

### 4.3 Other verified boundaries

Character drift/gravity, checkpoint, world/trajectory, derived effects, and
bridge suggestions each retain their own behavior and failure disposition.
In particular, bridge failure may be reported to a caller after primary memory
is already durable.  Post-write behavior is not normalized into one
transactional model by this policy.

## 5. Stochastic parity

```text
SINGLE_RANDOM_DRAW_EQUALITY_REQUIRED = NO
STOCHASTIC_DECISION_SEMANTICS_PARITY_REQUIRED = YES
```

Parity preserves the semantically relevant deterministic and distributional
structure: `p(input)`, inputs to `p`, clamps, scope, decision ordering, draw
mechanism semantics, and resulting state transition/durable effect.  The policy
does not invent deterministic production seeds or require equality of an
arbitrary individual process draw.

## 6. Interaction and query/post-write composition

```text
INTERACTION_PARITY_REQUIRED = YES
QUERY_POST_WRITE_COMPOSITION_REQUIREMENT = REQUIRED
```

Subsystem parity alone is insufficient where ordering or feedback changes
behavior.  Verified interaction classes include:

| Interaction | Frozen treatment |
|---|---|
| Character modulation ↔ MAIN TORMENT COGNITION initialization | Preserve the seed-derived initialization interaction.  The graph constructor is not claimed to consume Character state. |
| Character seed/context ↔ query-visible assembly | Preserve seed preamble/context and its query-visible consequences when applicable. |
| Stochastic write gate ↔ reinforcement/creation | Preserve decision ordering and durable-result consequences. |
| Conflict persistence ↔ later conflict-aware query | Preserve the effect of durable conflict evidence on later reads when applicable. |
| SRG post-write state ↔ SRG query-side writeback/subsequent query | Treat feedback as a composed behavior, not unrelated slice results. |

Query and post-write cognition may be implemented and qualified in separate
slices, but they are not globally semantically independent where read-path
mutation or shared durable state creates feedback.  This does not assert that
they are categorically inseparable.

## 7. Character policy

Character effects remain separate:

```text
CHARACTER_SEED = PARITY_REQUIRED_WHEN_PROFILE_APPLICABLE
CHARACTER_DRIFT = BLOCKING_UNLESS_EXPLICITLY_INAPPLICABLE
CHARACTER_GRAVITY = BLOCKING_UNLESS_EXPLICITLY_INAPPLICABLE
```

Character seed/seed context, Character modulation, Character drift, and
Character gravity have different inputs, state, and failure boundaries.  A
selected policy may make them genuinely inapplicable, but that fact must be
explicit.  Current native staging inability to preserve Character is not
evidence of inapplicability.

## 8. Conflict policy

```text
CONFLICT_PERSISTENCE = BLOCKING_UNLESS_EXPLICITLY_INAPPLICABLE
```

This applies whenever conflict conditions are lawful under the selected active
profile.  Conflict state is both post-write durable evidence and input to later
query/read behavior; its omission can change future MAIN TORMENT COGNITION.

## 9. Durable-owner census

```text
DURABLE_OWNER_CENSUS_REQUIRED = YES
UNENUMERATED_DURABLE_OWNER = ACTIVATION_BLOCKING_UNTIL_DISPOSITIONED
```

An explicit profile-relevant denominator is required before real native
activation.  The preliminary known surface includes, where applicable:

```text
canonical memory graph/store        motif state
Character seed/state                conflict state
BridgeRegistry                      proposal state
world/trajectory state              checkpoint state
SRG state                           Hivemind state
role/affect/derived artifacts       compression/deep-memory state
```

The set is not claimed complete.  Every durable state must eventually be
classified as one of:

```text
NATIVE_OWNER | EXTERNAL_OWNER | DERIVATION_ONLY |
EXPLICITLY_INAPPLICABLE | UNRESOLVED
```

## 10. EID policy

```text
NUMERIC_LEGACY_EID_IS_NOT_ROOT_GLOBAL = YES
EID_UNIQUENESS_SCOPE = LEGACY_SOURCE_NAMESPACE
ROOT_GLOBAL_EID_ALLOCATOR_REQUIRED = NO
```

Native routing qualifies a numeric EID with the necessary identity context:
root/profile, workspace/scope, source namespace, numeric EID, and revision as
needed.  This policy does not redesign EID identity.

## 11. B3 representation policy

```text
OMEGA_INIT_REEMBEDDING_DEPENDENCY = NO
B3A_B3B_PHASE0_DEPENDENCY = NO
TARGET_REPRESENTATION = st / BAAI/bge-small-en-v1.5 / 384
REAL_MEMORY_REEMBED_AUTHORIZED = NO
```

B3A and B3B remain governed by their existing frozen representation
architecture.  Phase 0 neither reopens them nor creates a representation
dependency for MAIN TORMENT COGNITION initialization.

## 12. Mathematical duplicates

```text
MATHEMATICAL_FORMULA_DUPLICATES_PRESENT = YES
```

R0 already requires every duplicate to have a named semantic owner, named
parity test, retirement gate, and eventual survivor.  That requirement is
present; Phase 0 neither consolidates formulas nor changes TORMENT mathematics.

## 13. Facts reserved for later production admission

Phase 0 does not claim real values for production environment overrides,
Character enablement, SRG enablement, Hivemind enablement, auto-merge policy,
coupling mode, the complete external durable-owner census, or the real-root
disposition of geometry-derived external state.  It freezes their required
treatment as later admission evidence only.

## 14. Pre-activation gates

```text
NAMED_EXTERNAL_ADMISSION_OWNER_AND_WITNESS = OPEN
FULL_DURABLE_OWNER_CENSUS = OPEN
PUBLIC_FALLTHROUGH_CENSUS_AND_RETIREMENT = OPEN
CONFLICT_NATIVE_PARITY_IF_APPLICABLE = OPEN
CHARACTER_NATIVE_PARITY_IF_APPLICABLE = OPEN
GEOMETRY_DERIVED_EXTERNAL_STATE_DISPOSITION = OPEN
REAL_PRODUCTION_PROFILE_MATCH = OPEN
REAL_ROOT_ACTIVATION = NOT_AUTHORIZED
```

These are scheduled pre-activation evidence gates, not failures of Phase 0.

## 15. Final verdicts

```text
PHASE_9D_P0_POLICY = PASS
P0A_EXTERNAL_IDENTITY_AND_SCOPE_ADMISSION_POLICY = FROZEN
P0B_TORMENT_BEHAVIOR_AND_NATIVE_PARITY_POLICY = FROZEN

NEW_EXTERNAL_AUTHORITY_COMPONENT_REQUIRED = NO_CURRENT_EVIDENCE
NAMED_EXTERNAL_ADMISSION_OWNER = PRE_ACTIVATION_GATE
SQLITE_MAY_ORIGINATE_EXTERNAL_IDENTITY = NO
NATIVE_CAPABILITY_DEFINES_TORMENT_LAWFULNESS = NO
NATIVE_DEFICIT_IS_PERMISSION_TO_REMOVE_TORMENT_EFFECT = NO

FAILURE_DISPOSITION_PARITY_REQUIRED = YES
STOCHASTIC_SEMANTIC_PARITY_REQUIRED = YES
INTERACTION_PARITY_REQUIRED = YES
DURABLE_OWNER_CENSUS_REQUIRED = YES
UNENUMERATED_DURABLE_OWNER = ACTIVATION_BLOCKING

NUMERIC_LEGACY_EID_IS_NOT_ROOT_GLOBAL = YES
ROOT_GLOBAL_EID_ALLOCATOR_REQUIRED = NO
OMEGA_INIT_REEMBEDDING_DEPENDENCY = NO
B3A_B3B_PHASE0_DEPENDENCY = NO

TORMENT_MATHEMATICS_PRESERVED = YES
MATHEMATICAL_FORMULA_CHANGES_REQUIRED = NO
BLOCKER_5_REOPEN_REQUIRED = NO
REAL_PRODUCTION_ACTIVATION = NOT_AUTHORIZED
```

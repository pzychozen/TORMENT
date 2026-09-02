# TORMENT Memory Substrate Phase 9C-R0 — Zero-Member Legacy Motif Semantics v0.1

## Status and authority

```text
DOCUMENT_KIND = PROPOSED_SUCCESSOR_B4_AUTHORITY_RECORD
IMPLEMENTATION_AUTHORIZATION = NO
PHASE_9C = BLOCKED_PENDING_BOUNDED_B4_SUCCESSOR
BLOCKER_5_REOPEN_REQUIRED = NO

REAL_ROOT_CONTACT = NO
REAL_MOTIF_CONTENT_READ = NO
REAL_MEMORY_MODEL_CONTACT = 0
REAL_REEMBED_OPERATIONS = 0
BRAINVISION_FILES_READ = 0
BRAINVISION_FILES_TOUCHED = 0
```

This record characterizes code and frozen-contract facts only.  It does not
change B4A/B4B, create a native core, admit a motif, select public authority,
or authorize a real-root operation.

The Phase 9C stop was correct.  The frozen B4A/B4B contracts require a
membership baseline, while the root-wide profile explicitly recognizes a
materialized shared graph with motif state and zero memories.  No fake memory,
EID, vector, or membership is a lawful repair.

## R0-A — Legacy zero-member semantics

`MotifRegistry._load()` accepts `members` as `list(md.get("members", []))`;
there is no non-empty validation.  `save()` round-trips the motif unchanged.
Once loaded, an empty motif remains a normal entry in `self.motifs`; it is not
marked retired, hidden, or otherwise disabled.

| Legacy consumer | Disposition | Code fact |
|---|---|---|
| Attach-or-create candidate selection | `ACTIVE` | `attach_or_create()` passes every current motif to `decide_attach_or_create()`.  That decision has no positive-member gate. |
| Motif gravity | `ACTIVE` | `motif_gravity_bonus()` retains strength and stability contributions when density is zero. |
| Domain centroid | `ACTIVE` | `domain_centroid()` includes every dimensionality-compatible motif, weighted by strength and gravity. |
| Active motif catalog / dominant-thread context | `ACTIVE` | `active()` ranks every motif by strength plus gravity; member count is reported as zero but is not a filter. |
| Query domain geometry | `ACTIVE` | The legacy geometry adapter exposes every registry motif, and query assembly records every exposed centroid. |
| Query motif alignment | `CONDITIONAL` | A zero-member motif has no current membership provenance, but the query fallback may infer the best motif from all domain centroids for a hit without motifs.  It can therefore contribute to alignment when that fallback crosses its threshold. |
| Ordinary post-write motif selection | `ACTIVE` | A stored memory enters `attach_or_create()` before the post-write context is assembled.  If the empty motif wins, it receives the first member and its ID is carried into post-write consumers. |
| Split | `NOT_APPLICABLE` while empty | The frozen automatic split policy refuses below 96 member evidence items; a successful split also requires each child to have at least 16. |
| Merge candidacy and merge mutation | `ACTIVE` | Maintenance compares all motif centroids without a member-count filter.  A merge can retire the empty motif as the drop, or preserve it as the keep and then union members. |
| Entropy / merge suggestion maintenance | `ACTIVE` | Entropy counts all motifs and merge-candidate iteration uses all compatible centroids. |
| Domain-suggestion heuristic | `ACTIVE` | It iterates all current motif geometry; a sufficiently strong empty motif can participate. |

An empty motif is therefore not semantically equivalent to an absent motif.
Its zero density reduces one gravity term, but its centroid, strength,
stability, label, timestamps, and contributors remain observable aggregate
state.  In particular, an ordinary future attach uses `max(1,
motif.member_count)` in its learning-rate calculation, so an existing empty
motif has defined revival behavior rather than dead-state behavior.

```text
ZERO_MEMBER_LEGACY_SEMANTICS =
    ACTIVE_AGGREGATE_STATE_WITH_ZERO_CURRENT_MEMBERS
```

## R0-B — Origin and mutation paths

The ordinary legacy creation path creates `members=[memory_eid]`.  Ordinary
attach appends one member.  There is no ordinary member-removal operation.

The other current mutation paths do not create an empty motif from a
non-empty motif:

| Path | Zero-member result |
|---|---|
| Load / save of `motifs.json` | Accepts and preserves an existing empty list. |
| Ordinary create | Impossible: first member is required. |
| Ordinary attach | Impossible: adds a member. |
| Automatic split | Impossible: the minimum-member and child-population gates preclude it. |
| Merge | Can preserve a pre-existing empty state (for example, merging two empty motifs leaves the survivor empty), can retire it as the drop, or can make an empty survivor non-empty by union.  It is not an independent empty-motif creator. |
| Current member retirement | No legacy mutation primitive exists. |

Thus the initial empty state is not produced by normal current creation or
removal semantics.  It is structurally loadable, persisted without repair,
and used by current cognition after load.  It may originate in historical
format/implementation behavior, an import, or manual/test residue, but the
present runtime supports rather than rejects it.

```text
ZERO_MEMBER_MOTIF_ORIGIN = HISTORICAL_BUT_SUPPORTED_STATE
CURRENT_DIRECT_EMPTY_MOTIF_CREATION = NO
CURRENT_EMPTY_MEMBER_RETIREMENT_PATH = NO
```

## R0-C — Native model capacity

Native `MotifState` stores aggregate fields only.  It intentionally forbids
`members` and `member_count` in the payload; membership truth is carried by
`MOTIF_MEMBERSHIP` relationships.  The underlying native motif object shape
can therefore structurally exist with zero relationship rows.

`NativeMotifService` deliberately exposes only
`create_motif_with_member()` for ordinary creation.  Its internal motif-object
publication helper can create the object carrier, but it is not an ordinary
runtime authority for a bare motif.

The reader is more precise than a simple structural check:

- `list_runtime_motifs()` always obtains the ordered current membership list.
- Ordinary, non-migration topology can produce an empty tuple if a lawful
  object existed with no relationship rows.
- B4A/B4B topology is recognized by its creation transition and operation.
  Its baseline verifier requires at least one membership output/effect and
  refuses an empty baseline.

The blocker is consequently not the JSON object carrier or the representation
of `member_count=0`; it is creation/import authority plus the reader's
specific migration-baseline proof.

```text
NATIVE_ZERO_MEMBER_STATE_CAPACITY = BOUNDED_EXTENSION_REQUIRED
ORDINARY_RUNTIME_MOTIF_CREATION_REQUIRES_FIRST_MEMBER = YES
ARBITRARY_ZERO_MEMBERSHIP_READER_ACCEPTANCE = NO
```

## R0-D through R0-F — Geometry cases and reconstruction

### Z1 — exact target-compatible geometry

Where explicit source evidence proves the motif centroid's source geometry is
exactly the declared target lane, preserving the aggregate state is faithful:

```text
centroid                 = copied, not recomputed
strength/stability       = copied
label/contributors       = copied
timestamps               = copied
memberships              = 0
fake memory/EID/vector   = 0
```

This retains the legacy motif's observable role in candidate selection,
gravity, domain geometry, query fallback, and maintenance.  It is more
faithful than retaining the motif only as inactive history.

```text
TARGET_COMPATIBLE_ZERO_MEMBER_DISPOSITION = ACTIVE_IMPORT
```

### Z2 — hash or otherwise non-target geometry

B4B derives a target centroid only from the ordered current target vectors of
the motif's members.  A zero-member motif supplies none.  The frozen B4B
contract forbids consuming the historical centroid numerically as target
geometry, and no qualified source provides a replacement target centroid.

`motif_events.jsonl` cannot cure this.  Current motif admission deliberately
never reads it for semantics and records `motif_reconstructability =
NOT_PROVEN`.  Its create/attach events may name a memory EID, but split events
store counts rather than complete partitions and merge events identify only
keep/drop motifs.  They do not establish a complete, immutable, ordered
history, canonical text continuity, qualified target vectors, or an exact
replay of state-dependent legacy attach updates.

```text
REPLAY_RECONSTRUCTION = NOT_PROVEN
NON_TARGET_ZERO_MEMBER_DISPOSITION = BLOCK
```

### Z3 — unknown source geometry

Unknown provider/model identity cannot be promoted by matching dimension.
It is neither B4A-exact nor B4B-qualified, and the same absence of target
member geometry prevents target derivation.

```text
UNKNOWN_ZERO_MEMBER_DISPOSITION = BLOCK
DIMENSION_EQUALITY_IS_NOT_REPRESENTATION_IDENTITY = YES
```

### No label re-embedding

No existing motif contract defines the motif label, domain name, or
contributing-agent names as canonical embedding input for a motif centroid.
The legacy label is generated as label text during ordinary motif creation;
it is not geometry provenance.  Re-embedding it would create new semantics
and cannot satisfy B4B's member-derived geometry law.

```text
LABEL_REEMBED_AS_MOTIF_CENTROID = NOT_AUTHORIZED
```

## R0-G — Disposition comparison

| Disposition | Assessment |
|---|---|
| Z-A active zero-member import | Required only for exact target-compatible source geometry; preserves demonstrated legacy behavior. |
| Z-B reconstructed target geometry | Not available under current qualified evidence; no approximation is lawful. |
| Z-C retained inactive history | Preserves evidence but changes legacy cognition by removing an active aggregate from selection and geometry.  It is not the default for Z1. |
| Z-D activation-blocking unresolved motif | Required for Z2 and Z3 unless a later independently qualified, exact reconstruction contract is established. |

The unresolved gate is staging/import evidence only.  It does not authorize
accepting stale external geometry-derived state, activation, or a public
runtime fallback.

## R0-I through R0-K — Minimum successor authority

The minimum extension is a new bounded **B4C zero-member projection case**,
not a modification of the historical B4A/B4B qualification and not a second
motif persistence engine.

The proposed B4C case is limited to Z1.  A subsequent implementation order
must use the existing `NativeMotifService` to publish one explicitly
migration-authorized zero-member baseline.  It must not write object or
relationship tables directly from a migration module, and it must not expose
an ordinary public/runtime empty-motif creator.

The operation/transition names are intentionally not frozen by this record.
They must be distinct from ordinary `create_motif_with_member()` and bind at
least:

```text
source snapshot and source namespace
source legacy motif object/revision/admission evidence
exact source motif artifact state and empty current-members witness
exact source provider/model/dimension and target-lane identity
complete target RootScopeKey-derived namespace identities
target motif alias and semantic scope
full idempotency identity and a stable result identity
```

It may publish exactly one native `DERIVED_MOTIF` R1 and its target alias with
zero membership relationships.  Its durable derivation metadata and canonical
operation intent must record that this is a source-preserving,
target-compatible, zero-member migration baseline—not an ordinary native
motif birth.

The reader extension must recognize only that explicit durable B4C topology.
For its R1 baseline it must prove:

```text
one matching motif object output/effect
zero membership outputs/effects
zero current or retired baseline membership relationships
the designated migration operation and transition kind
```

It may then allow later ordinary membership additions through the existing
native path.  It must not reinterpret any arbitrary `DERIVED_MOTIF` lacking
memberships as a lawful active motif.

```text
MINIMUM_B4_EXTENSION =
    NEW_BOUNDED_B4C_TARGET_COMPATIBLE_ZERO_MEMBER_PROJECTION

REEMBED_ENGINE_ADDED = NO
SECOND_MOTIF_PERSISTENCE_ENGINE = NO
B4A_B4B_HISTORICAL_CONTRACT_REOPENED = NO
```

## Result

```text
ZERO_MEMBER_LEGACY_SEMANTICS =
    HISTORICAL_BUT_SUPPORTED_ACTIVE_AGGREGATE_STATE

TARGET_COMPATIBLE_ZERO_MEMBER_DISPOSITION = ACTIVE_IMPORT
NON_TARGET_ZERO_MEMBER_DISPOSITION = BLOCK
UNKNOWN_ZERO_MEMBER_DISPOSITION = BLOCK

NATIVE_ZERO_MEMBER_STATE_CAPACITY = BOUNDED_EXTENSION_REQUIRED
MINIMUM_B4_EXTENSION = NEW_BOUNDED_B4C_TARGET_COMPATIBLE_ZERO_MEMBER_PROJECTION
PHASE_9C_RESUMABLE_AFTER_EXTENSION = PARTIALLY
```

“Partially” means that a B4C-qualified Z1 scope can enter the Phase 9C
orchestration.  Z2 and Z3 remain root-completion blockers, by design, until a
separate exact-evidence authority exists.  The actual root's per-motif source
geometry remains deliberately uninspected.

```text
CODE_CHANGES = 0
TEST_CHANGES = 0
REAL_ROOT_CONTACT = NO
BRAINVISION_FILES_READ = 0
```

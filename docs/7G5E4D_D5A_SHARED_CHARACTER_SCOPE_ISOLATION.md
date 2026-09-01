# 7G5E4D-D5A shared Character seed scope isolation

## Scope and ruling

D5A begins at `ab1f166 Qualify 7G5E4D shared checkpoint snapshot`. It repairs
only the prospective Character seed scope leak discovered during D5
archaeology. It adds neither a shared Character seed, a private-to-shared
mapping, SQLite mapping authority, a selector, activation, dual write/read,
or a historical rewrite.

```text
PRIVATE CHARACTER = unchanged

SHARED CHARACTER = no measurement unless an explicitly qualified shared
                   Character seed geometry exists

PRIVATE -> SHARED CHARACTER SEED MAPPING = none
CHARACTER SEED PROJECTION DESIGN = deferred
```

No qualified private-Character-seed to shared-domain identity mapping exists.
D5A does not invent one.

## Frozen pre-repair witness

The old path selected `workspace.shared_graphs[chosen_domain]` for a shared
trigger, while `CharacterSeed` retained bare EIDs that seed planting had
created in the agent's private graph. Each graph allocates EIDs independently.
The legacy `measure_drift()` fallback therefore performed the following when
the selected shared-domain motif registry lacked the private seed motif:

```text
private aria seed_eids = [1, 2]
shared research EID 1 = unrelated X = [1, 0, 0]
shared research EID 2 = unrelated Y = [1, 0, 0]
shared research EID 3 = ordinary current row = [0, 1, 0]

legacy cache reads = [1, 2, 3, 1, 2]
                         ^^^^^ shared observations
                                  ^^^^ wrongly treated as seed geometry
```

The direct frozen legacy measurement body selected the shared EID-1/EID-2
vectors as the seed centroid. Its deterministic witness produced
`distance_to_seed ~= 0.105573`, `drift_score ~= 0.577709`, and
`drift_direction = away_seed`. The values themselves are not a new
Character rule; they prove that unrelated shared rows were consumed as a
private seed identity relationship.

The old direct body also accepted a runtime-string collision:

```text
private Character seed_motif_id = "motif_x"
shared selected-domain motif runtime ID = "motif_x"
```

The deterministic witness reads the shared `motif_x` centroid, rather than a
private seed motif, and produces `distance_to_seed = 1.0`,
`drift_score = -1.0`, and `drift_direction = away_seed`. String equality is
not cross-scope identity and is now never accepted for a shared Character
trigger.

## Explicit trigger scope and no-op law

`FabricPostWriteContext.scope` is the original stored-memory trigger fact.
The existing post-write adapter now passes it explicitly as
`CharacterDriftPostWriteRequest.trigger_scope`; Character does not infer it
from a graph, domain, seed, or CharacterStore.

After the unchanged outer due gate, both the legacy and native C1A runtime
return the typed semantic no-op `NOT_APPLICABLE_SCOPE` for `trigger_scope =
shared`, before loading a Character seed, enumerating/reading a memory,
querying motif geometry, reading CharacterState, or beginning C1A's fallback
chain.

```text
Character outer gate reached
  -> trigger_scope = shared
  -> no qualified shared Character seed geometry
  -> NOT_APPLICABLE_SCOPE
  -> no CharacterState persistence
  -> no C1B gravity correction
  -> no reflex edge
  -> later post-write consumers continue
```

This is a scope-applicability change only. It does not alter the Character
weighting, cosine/distance/score equations, strict `0.03` direction
threshold, correction threshold, seed parsing, correction text, or any kernel
or world mathematics.

## Private preservation and external state

Private triggers still use the exact C1A geometry order:

```text
private seed motif centroid
  -> private seed-EID vectors
  -> recent private-memory average
```

They retain CharacterStore JSON loading, creation/update, history cap, C1B
gravity correction, motif composition, world fresh registration, and the
existing external reflex boundary. CharacterState remains external at
`workspaces/<workspace>/agents/<agent>/character_state.json`; D5A neither
migrates nor rewrites CharacterState, seed records, seed memories, existing
drift corrections, or history.

For a shared no-op, CharacterState is not loaded or saved. Consequently there
is no correction R1, motif operation, world registration, reflex edge, native
representation, or vector-lane effect.

```text
SHARED_PRIVATE_SEED_EID_LOOKUP = ZERO
SHARED_PRIVATE_SEED_MOTIF_LOOKUP = ZERO
SHARED_CHARACTER_RECENT_AVERAGE_AS_SEED = NO
SHARED_SCOPE_NOOP_CHARACTERSTATE_MUTATION = NONE
SHARED_SCOPE_NOOP_GRAVITY_CORRECTION = NONE
SHARED_CHARACTER_VECTOR_LANE_EFFECT = NONE
CHARACTER_MAPPING_AUTHORITY_IN_SQLITE = NONE
HISTORICAL_CHARACTER_REWRITE = NO
```

## Verification and remaining matrix

`tests/test_shared_character_scope_isolation.py` freezes the old bare-EID and
same-string motif-ID witnesses, proves independent EID and motif-ID collision
no-ops, confirms no CharacterState/gravity/reflex effects through the
post-write adapter, and checks private C1A seed-EID fallback/state persistence.
The native C1A suite also proves that a shared trigger stops before any private
seed, shared-memory, or motif access.

| Consumer family | D5A disposition |
| --- | --- |
| Private Character C1A/C1B | Qualified and unchanged. |
| Shared Character | Scope-guarded no-op pending an explicit shared Character geometry design. |
| Shared Character correction/vector effect | None because no shared measurement is applicable. |
| Compression/deep memory | Remaining isolated optional E4D consumer family; untouched. |

```text
SHARED_CHARACTER_SCOPE_ISOLATION = QUALIFIED
SHARED_CHARACTER_MEASUREMENT = NO_OP_WITHOUT_QUALIFIED_SHARED_SEED_GEOMETRY
SHARED_CHARACTER_EID_COLLISION = ELIMINATED
SHARED_CHARACTER_MOTIF_ID_COLLISION = ELIMINATED
PRIVATE_CHARACTER_REGRESSION = PASS
PRIVATE_C1A_GEOMETRY_FALLBACK_REGRESSION = PASS
CHARACTER_STATE_STORE = RETAIN_EXTERNAL_UNCHANGED
CHARACTER_MATHEMATICS_CHANGED = NO
KERNEL_FILES_CHANGED = 0

PUBLIC_INGEST_BACKEND = LEGACY
PRODUCTION_SELECTOR_ADDED = NO
NATIVE_ACTIVE = NO
DUAL_WRITE = NO
DUAL_READ = NO
CUTOVER_OPENED = NO
```

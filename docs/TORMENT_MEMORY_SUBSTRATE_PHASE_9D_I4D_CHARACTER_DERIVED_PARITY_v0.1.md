# TORMENT Memory Substrate — Phase 9D I4D

## Character and derived persistence parity for the bounded private native-public route

**Status:** uncommitted qualification artifact. This is not an activation, a
shared-route claim, a `CharacterStore` migration, an I4E world migration, or a
retirement decision.

**Frozen implementation base:** `bdac6c83b785d4a3c48b31a9d11afa5fa12064b0`.

```text
I4D_SCOPE = BOUNDED_PRIVATE_NATIVE_PUBLIC
CONFLICT_READ_PARITY = FROZEN_PRESERVED
DERIVED_IDENTITY_ANCHOR_PARITY = FROZEN_PRESERVED
SHARED_I4D_PARITY = NOT_CLAIMED
SHARED_PRECOMMIT_EXTERNAL_OWNER_RESTORATION_REQUIRED = YES
I4E_SYSTEMS_MIGRATED = NO
RETIREMENT_ALLOWED = NO
REAL_PRODUCTION_ACTIVATION = NOT_AUTHORIZED
```

## Archaeology and system-fit decision

The legacy successful post-write order is:

```text
CREATED_NEW consumers
  -> contradiction -> SRG collision -> Hivemind -> motif maintenance
  -> identity-anchor emit/refine -> mood drift
-> world step
-> Character measure/state -> high-drift gravity -> reflex edge
-> checkpoint -> compression/deep -> proposal -> bridges
```

World advancement remains an I4E system. I4D neither calls it in the
true-split continuation nor treats the absence of that call as world parity.
The pre-existing ordinary private adapter retains its old qualified world call;
I4D neither alters nor claims that behavior.

`NativeWorldRuntime.advance_for_post_write` reads current topology and mutates
only process-owned `SeedWorld` positions, velocities, trails, histories, and a
possible in-memory diagnostic overlay. It performs no native write. Mood drift
reads external affect state and qualified private memory; it calls
`ensure_initialized`, never world advancement. Character measurement reads
only qualified enumeration/representations/motifs and external Character state.
Gravity initializes/registers its own fresh correction but does not advance the
world. No mood or Character input reads a field changed by world advancement.

The direct true-split test forbids `_run_world_step` while observing exactly:

```text
conflict -> M1 -> anchor -> refine -> mood -> Character
```

```text
CHARACTER_WORLD_ORDER_DEPENDENCY = INDEPENDENT_FOR_I4D
```

This is continuation independence only, not complete world/trajectory parity.

## Owner and effect map

I4B-2's private identity-anchor emit/refine path, including its N02 lifecycle
successor, is frozen. I4D does not generalize anchor authority, thresholds,
side-store shape, lifecycle behavior, or source identity.

Mood drift is a separately qualified private derived child reached only after
the retained M1 gate. A predecessor with no motif runtime receives no
independent mood route. Its configuration is locked to prepared private
workspace/agent/domain/semantic scope and its child operation key derives from
the native public parent operation. It has no source-EID field and does not
consume SRG or create an SRG successor:

```text
MOOD_DRIFT_SRG_DEPENDENCY = NOT_APPLICABLE_NO_SRG_INPUT_OR_SUCCESSOR
MOOD_DRIFT_CHILD_IDENTITY = DERIVED_FROM_QUALIFIED_PRIVATE_PARENT_OPERATION
MOOD_DRIFT_OWNER_SCOPE = PRIVATE_WORKSPACE_AGENT_DOMAIN_CONFIGURATION
```

The unchanged mood gates are non-neutral affect, enabled flag, confidence at
least `TORMENT_MOOD_DRIFT_MIN_CONF`, changed prior tag, and the minimum step
gap. Strength, confidence, half-life, attribution, embedding, history-cap, and
recovery formulas are unchanged.

`CharacterStore` remains the external seed/state owner:

```text
workspaces/<workspace>/seeds/<seed>/seed.json
workspaces/<workspace>/agents/<agent>/character_state.json
CHARACTER_EXTERNAL_OWNER = PRESERVE
```

Native measurement preserves the seed-motif-first/namespaced-seed-EID fallback,
agent filter, seed-canon exclusion, recency-before-embedding read order,
weighting, centroid, score, direction, cadence, and 50-entry history cap. It
stores no Character state in SQLite.

High drift retains the existing gate and native additive gravity child:

```text
drift_score < -seed.drift_correction_threshold
and drift_direction == "away_seed"

correction strength = seed.drift_gravity_strength
confidence = 0.85
half-life = seed.core_half_life
```

Gravity never calls Fabric ingest or re-enters the full tail. Its motif substep
is best-effort. Reflex remains Fabric's existing process-local rising-edge
callback; callback failure is caught after the edge map update. I4D adds no
decision or autonomous control authority.

```text
NOTHING_IS_ALLOWED_TO_TAKE_CONTROL = YES
```

| Effect | Trigger / owner | Durable result and failure |
|---|---|---|
| Identity anchors | private `CREATED_NEW`, retained M1 | frozen native N02 child/lifecycle and side store; independent fail-soft slots |
| Mood drift | private `CREATED_NEW`, retained M1, affect/change/gap gates | native `mood_drift` child plus external `affect_state.json`; either affect save is fail-soft |
| Character measure/state | eligible public adapter boundary; actual measure requires enabled/stored/positive-step/cadence | external `character_state.json`; outer Character boundary is fail-soft |
| Gravity | measured high drift | additive native correction; best-effort motif work; gravity error prevents later reflex in the existing outer catch |
| Reflex | rising high-drift edge | process map and external callback; callback error independently logged |
| World/checkpoint/compression/proposal/bridges | later legacy systems | not migrated or claimed by I4D |

## Exact composition, outcomes, and recovery

The lawful true-split continuation is narrower than a complete legacy tail:

```text
canonical native source and current route witness
  -> I4C external conflict surface (fail soft)
  -> I4B-2 M1 / frozen identity-anchor slots (independent fail soft)
  -> I4D mood drift (fail soft)
  -> I4D Character measurement/state -> gravity -> reflex
  -> STOP BEFORE I4E WORLD / TRAJECTORY / CHECKPOINT / COMPRESSION / PROPOSAL / BRIDGES
```

For ordinary private public writes, `CREATED_NEW`, `REINFORCED_EXISTING`, and
`NO_WRITE` reach the existing Character adapter boundary. Its request gates make
reinforcement a seed-resolving effective no-op and no-write not due. Derived
mood remains `CREATED_NEW` only. Canonical commit failure returns before a route
witness or post-write adapter exists.

No global exactly-once mechanism was added. Mood's state-save, derived-create,
and history-save dispositions remain separate; both side-store saves are
fail-soft. Its exact-private lost-response recovery reuses a matching child and
adds only missing history. Character seed/state load, measurement, state save,
gravity, and outer orchestration retain their existing fail-soft boundary.
Public receipt replay returns the completed receipt without tail re-entry.
Lower-level mood/gravity retry retains its own child-operation recovery.

A fresh `CharacterStore` reloads persisted state. Existing Character cold
recovery and gravity READY-response recovery preserve private identities. The
reflex edge map is process-local, so its first later high measurement may
re-fire after a restart.

## Implementation and evidence

The only production composition changes are:

```text
ordinary private public configuration
  -> explicit core_staging_with_character profile

private true split
  -> explicit Character + M1/M2 profile
  -> retained I4C conflict -> retained I4B-2 M1 / anchors
  -> retained native mood -> retained Character
```

No conflict reader/writer mathematics, identity-anchor law, Character formula,
derived formula, query ordering, shared precommit owner, world step, trajectory,
checkpoint, compression/deep memory, Hivemind, proposal, bridge, archive,
service root, provider behavior, or SQLite Character-state owner changed.

Focused evidence, executed with `conda activate torment` against disposable
external pytest bases:

```text
tests/test_p9d_i4d_character_derived_parity.py
tests/test_substrate_native_post_write_runtime.py
33 passed

tests/test_substrate_native_character_drift_runtime.py
tests/test_substrate_native_character_gravity_runtime.py
tests/test_substrate_derived_memory.py
tests/test_substrate_character_seed_continuity.py
47 passed

tests/test_fabric_post_write_memory_consumers.py
tests/test_shared_character_scope_isolation.py
28 passed
```

The public tests prove external state save/reload, high-drift native gravity,
the existing reflex edge, mood creation/miss/fail-soft state failure, receipt
replay, and the outer outcome fences. The direct tail test proves exact order
while refusing world and later consumers. Existing drift/gravity/derived/
continuity suites lock formulas, low-drift exclusion, history semantics,
child recovery, cold Character continuity, gravity-error disposition, reflex
callback-error disposition, and shared Character non-entry.

## Bounded verdict

```text
P9D_I4D_CHARACTER_DERIVED_PARITY = PASS_BOUNDED_PRIVATE_NATIVE_PUBLIC_SCOPE

DERIVED_IDENTITY_ANCHOR_PARITY = FROZEN_PRESERVED
DERIVED_MOOD_DRIFT_PARITY = PASS_PRIVATE_NATIVE_PUBLIC_SCOPE
CHARACTER_WORLD_ORDER_DEPENDENCY = INDEPENDENT_FOR_I4D
CHARACTER_DRIFT_PARITY = PASS_PRIVATE_NATIVE_PUBLIC_SCOPE
CHARACTER_STATE_OWNER_PARITY = QUALIFIED
CHARACTER_GRAVITY_PARITY = PASS_PRIVATE_NATIVE_PUBLIC_SCOPE
CHARACTER_REFLEX_EDGE_PARITY = PASS_PRIVATE_NATIVE_PUBLIC_SCOPE
CHARACTER_FAILURE_DISPOSITION = PASS
CHARACTER_RESTART_PARITY = PASS
CHARACTER_REPLAY_MODEL = QUALIFIED_BOUNDED
SHARED_I4D_PARITY = NOT_CLAIMED

CHARACTER_FORMULA_CHANGES = 0
DERIVED_FORMULA_CHANGES = 0
TORMENT_MATHEMATICS_PRESERVED = YES
I4E_SYSTEMS_MIGRATED = NO
RETIREMENT_ALLOWED = NO
REAL_PRODUCTION_ACTIVATION = NOT_AUTHORIZED
I4D_READY_TO_FREEZE = YES
I4E_STARTED = NO
```

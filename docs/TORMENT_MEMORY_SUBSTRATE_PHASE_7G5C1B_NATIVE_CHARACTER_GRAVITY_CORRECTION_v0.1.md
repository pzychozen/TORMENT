# Phase 7G5C1B — Native Character Gravity Correction

## Boundary

C1B qualifies only the Character post-write high-drift correction path. It is
not a generic native memory writer, a generic motif writer, or a production
route. The legacy path remains active and authoritative.

The shared post-write orchestration is deliberately small:

```text
C1A measurement -> C1B correction when high -> existing Character reflex edge
```

`LegacyCharacterGravityCorrectionRuntime` delegates directly to the existing
`gravity_correction()` implementation. `NativeCharacterGravityCorrectionRuntime`
owns only the bounded C1B sequence.

## Native correction contract

The independent correction gate preserves the legacy comparison exactly:

```text
drift_score <= -seed.drift_correction_threshold
and drift_direction == "away_seed"
```

It uses `_split_seed_text()` and `random.choice()` semantics (with an
injectable test selector), freezes the chosen text as:

```text
[identity reinforcement] {concept}
```

and validates the caller-owned embedder's provider, model, and dimension
against the prepared compatibility lane. A source retry recovers the selected
concept and source-bound float32 hash; an incomplete representation retry
re-embeds only the stored exact text and refuses
`CHARACTER_CORRECTION_EMBEDDING_NOT_BYTE_STABLE` if its bytes differ.

The R1 is exactly a `drift_correction` core memory with `canon=true`, the
ordinary lifecycle helper and world-genesis helper, explicit ordinary
five-false governance, narrow runtime-derived Character provenance, and
`NOT_APPLICABLE` authority. C1B does not extend A3D9's public derived-memory
enum.

## Ordered effects and failure topology

```text
initialize current process-local world
-> correction R1
-> A3D8 fresh-world registration (zero world steps)
-> truthy seed_motif_id only: ordinary full-catalog motif decision at 0.50
-> COMPAT_EMBEDDING PENDING -> expectation -> READY/USABLE/MATCH
```

Motif planning or persistence is inner best effort: R1 remains, the ordinary
representation completes, and the reflex edge is eligible. An attach that
would reach a prospective member count of 96 returns
`CHARACTER_MOTIF_SPLIT_PARITY_REQUIRED`; it publishes no fake membership or
split. That bounded split outcome is recorded by a C1B motif-outcome operation,
so a later READY retry reports the same result without re-embedding or making
another random selection. Representation/source failures propagate to the existing outer
Character boundary, so they do not update the reflex edge.

The existing `NativeMotifProcessOrder` owns current-catalog process order.
`decide_attach_or_create`, `realize_attach_next_state`, and
`realize_create_next_state` remain the only motif decision/geometry math.

## Staging integration

`NativePostWriteQualificationProfile.core_staging()` remains frozen. The
separate `core_staging_with_character()` profile explicitly binds C1A's native
measurement reader and C1B's correction runtime after the normal world step.
It requires the caller-owned `CharacterStore` and embedder. No Fabric selector,
dual write/read, production activation, or schema work is introduced.

## Deliberate boundary

Auto-split, auto-merge, Character seed planting/context behavior, checkpoint,
trajectory, bridge, compression, deep-memory, migration, and cutover remain
out of scope. Schema remains v1.2.

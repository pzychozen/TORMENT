# TORMENT Memory Substrate — Phase 7G5A3D9

## Typed derived-memory mutation boundary

This qualification slice closes the default post-write hard blocker
`DERIVED_MEMORY_MUTATION`. It remains staging-only. It does not select native
storage in Fabric, add a post-write adapter, dual-write, dual-read, or alter
the legacy default path.

Schema remains v1.2.

## Frozen legacy topology

`_run_motif_maintenance_and_anchors()` retains its CREATED_NEW order:

```text
motif entropy/suggestions
identity-anchor emission
identity-anchor refinement
mood drift
world step
```

Each of the three derived calls has its own fail-soft boundary. An anchor
emission failure does not suppress refinement, mood drift, or the later world
step; a refinement failure does not suppress mood drift or world; a mood
failure does not suppress world. A native failure remains on the selected
native authority: there is no graph fallback.

### Identity anchors

The legacy decision visits supplied motif IDs in their existing order. It
requires a present private graph and motif, derives base thresholds from:

```text
TORMENT_ID_ANCHOR_MIN_COUNT = 3
TORMENT_ID_ANCHOR_MIN_GAP_STEPS = 50
TORMENT_ID_ANCHOR_MAX_EXAMPLES = 2
```

and applies the current role multipliers, then affect-sensitive count/gap
multipliers where at least four checked members are 60% non-neutral. It
requires the member count, minimum gap, and count-since-last-anchor gates.
It uses the final `max_examples` member summaries in member order and creates
the exact text:

```text
Identity anchor: recurring theme '<label>'.[ Examples: summary | summary]
```

The row is `identity_anchor`, `core`, `canon=False`, confidence `0.85`,
half-life `3650.0`, strength `min(1.0, .55 + .08 * member_count)`, and carries
the existing workspace/domain/private/agent, motif, affect-sensitive,
seed-overlap, source-member, and embedding metadata. Its seed overlap is the
intersection of current motif member EIDs and the existing character seed EID
set. It has no role/seed authority gate; role/seed lookup failures retain the
legacy best-effort defaults.

After the new memory commits, the prior state-bookkeeping `last_eid` is
best-effort retired with the closed `superseded` patch, then `anchors.json` is
written with `last_step`, `count_at_create`, and the new compatibility EID.
Thus memory may remain if the later side-store write fails; a side-store
failure occurs after creation and does not roll it back. A retirement failure
does not stop the side-store update.

The refinement pass iterates current memories in existing runtime order,
filters non-retired matching identity anchors, sorts `(member_count,
created_at)` descending, retains `max(1, TORMENT_ANCHOR_KEEP_PER_MOTIF)`, and
applies only these closed patches:

```text
superseded: anchor_retired, anchor_retired_reason,
            anchor_superseded_by, anchor_merged_into, last_reinforced
weak_old:   anchor_retired, anchor_retired_reason,
            anchor_superseded_by, last_reinforced
```

No generic payload map or mutation API is introduced.

### Mood drift

Neutral/absent affect, disabled mood drift, and below-minimum confidence return
before touching the affect side store. For a non-neutral qualified affect,
legacy first writes `last_tag`, `last_conf`, and `last_step` to
`affect_state.json`, even when no memory will be emitted. It then requires a
non-neutral prior tag, a changed tag, and the minimum gap. The state writer is
best-effort, so its failure does not prevent the memory decision.

On a qualifying change, the exact text is:

```text
Mood drift: from <previous> to <current>.
```

The row is `mood_drift`, `core`, `canon=False`, strength
`min(1.0, .50 + .20 * confidence)`, confidence
`min(.95, .60 + .35 * confidence)`, configured half-life (default `60`), and
carries the current affect attribution, from/to, scope and embedding metadata.
After durable memory creation, it reloads `affect_state.json`, appends the
bounded drift history, and saves it best-effort. Therefore the first affect
state can remain if later memory creation fails, and a memory can remain if
the later history save fails. SQLite and the JSON side store are intentionally
not made atomic.

## Native contracts

`DerivedMemoryRuntimePort` is now the post-write semantic dependency.
`LegacyDerivedMemoryRuntime` delegates to the exact original Fabric methods;
the production default writer, side stores, graph, motif registry, role store,
and character seed state are unchanged.

`NativeDerivedMemoryRuntime` is connection-scoped and uses only native current
memory reads, native motif/member reads, qualified embedding reads, and the
existing process-owned SRG/world owners. It receives existing side-store
ownership explicitly. `NativeFabricMemoryRouter.bind_derived_memory_runtime()`
only proves one prepared staging capability can provide that boundary; it is
not a post-write adapter or a production route.

### Shape A: closed no-motif creation

`NativeDerivedMemoryCreationService` accepts only:

```text
IDENTITY_ANCHOR_CREATE
MOOD_DRIFT_CREATE
```

Its source transaction atomically publishes one ordinary compatibility object,
R1, EID alias, immutable runtime-order fact, provenance child, governance
child, source transition/effect/output. There are no links, motif objects,
motif revisions, or motif memberships. It reuses
`legacy_world_genesis_payload()` for `seed_pos0/seed_v0 → pos/vel/vel0`.
The object is ordinary/derived/`NOT_APPLICABLE` and has no authority semantics.

After R1, representation publication is independently:

```text
PENDING → integrity expectation → READY
```

using the actual already-produced qualified raw float32 vector. The service
never calls an embedder. Stable child operations are derived from the parent
native key, the closed operation kind, and a frozen semantic discriminator.
Source and every representation stage recover idempotently; changed input
with the same key conflicts.

Immediately after source commit (including recovery), the native world is
fresh-registered before representation publication. The A3D8 owner makes that
idempotent, so a lost response cannot duplicate a world entity or discard its
fresh histories.

### Shape B: closed anchor lifecycle successor

`NativeTypedMemorySuccessorService.publish_identity_anchor_lifecycle()` accepts
only an `IdentityAnchorLifecyclePatch`. It reads the exact current Rn/E1,
requires identity-anchor type, ordinary authority, structural provenance and
governance, and produces exactly one R(n+1):

```text
complete predecessor payload
+ optional SRGSuccessorMaterialization
+ optional WorldDiagnosticSuccessorMaterialization
+ closed anchor lifecycle patch
```

It preserves object identity, EID alias, runtime-order fact, semantic scope,
provenance, governance, authority and the current raw E1 bytes. E2 is the
byte-for-byte representation-continuity copy; no re-embed or normalization is
performed. Its source callback uses the A3D8 full-payload kinematic reset,
retaining the same world entity and histories/trail. Matching SRG/world
overlays are acknowledged only after the durable successor workflow succeeds.

## Exclusions

Not implemented here: Character/character gravity native routing, compression,
deep memory, motif merge, checkpoint, trajectory persistence, bridges, schema
v1.3, generic mutation, generic graph facade, native post-write adapter,
production selection, dual-write, dual-read, shadow-read, or cutover.

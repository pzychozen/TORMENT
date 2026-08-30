# TORMENT Memory Substrate — Phase 7G5A2 Motif Decision / Persistence Separation v0.1

## Scope

Starting commit: `15838f870e7b8e4132800b20dfdc84326e273c49`.

7G5A2 separates the current motif attach-or-create selection and aggregate
next-state calculation from persistence. It is a behavior-preserving boundary,
not a clustering redesign and not runtime routing.

`torment_service.motif_decision` contains the ordered read model, candidate
selection, diagnostics, and attach/create aggregate realization. It preserves
the current float32 unit-vector and cosine behavior, constants, strict
first-in-order tie replacement, effective-threshold boundary, learning rate,
centroid blend, strength/stability rules, contributor behavior, and label
fallback. Time and a runtime motif ID are supplied by an adapter; the decision
layer owns neither.

## Legacy behavior retained

`MotifRegistry.attach_or_create()` remains the public caller surface and keeps
its compatibility ID allocator, recovery behavior, legacy duplicate-EID
append, JSON save/event ordering, event diagnostic derivation, and post-attach
auto-split behavior. In particular, the event density remains pre-mutation
while gravity diagnostics use the already-mutated motif. A post-attach child
still appears only in `affected_ids`; it never turns `created_id` from `None`.

## Native staging adapter

`NativeMotifDecisionAdapter` reads native motifs in the caller's supplied
order, derives member cardinality from current `MOTIF_MEMBERSHIP`
relationships, runs the same base decision, and delegates writes exclusively
to `NativeMotifService`.

For a create, the caller explicitly supplies the compatibility runtime motif
ID, native identity namespace, scope, and timestamps. No native UUID is used
as the runtime motif ID, and no new durable runtime-ID allocator is introduced.
For an attach, the adapter uses the selected motif's current native revision
and calls `add_motif_member`; the existing stale and duplicate protections are
therefore retained.

Native membership remains relationship truth; no `members` or `member_count`
payload authority is introduced. Legacy repeated EIDs remain append behavior,
while native duplicate membership is still rejected with no successor residue.
The native adapter supplies no split behavior: native membership repartition
requires a later semantic primitive and is explicitly deferred.

The base decision preserves legacy empty-vector behavior and does not add an
empty-vector rejection. The pre-existing 7G5A1 native `MotifState` contract
still requires a non-empty centroid, so such a legacy decision is not silently
reclassified or made persistable through native staging in this slice.

## Explicit exclusions

- Entropy, merges, bridges, and other maintenance policy remain outside the
  decision module.
- Fabric and Character still use the legacy registry and remain the live memory
  authority.
- No Fabric/Character native routing, dual write/read, shadow behavior,
  backend selector, activation, production native core, migration, or cutover
  is included.
- Motif centroids remain ordinary aggregate state; no representation or READY
  claim is created.
- Motifs and memberships remain non-authorizing derived content.

## Verification

Focused tests cover decision threshold/tie/dimension behavior, gravity and
successor equations, contributor and label behavior, legacy return/event/save/
duplicate/split behavior, and native create/attach/stale/duplicate/source/
representation/authority behavior. The qualified environment remains Python
3.11.15 with sqlite3 module 2.6.0 and SQLite 3.53.4. The release-focused run
of the new suite, 7G5A1 native regression, motif path suite, direct Character
seed/gravity checks, and Fabric ingest check passed 34 tests.

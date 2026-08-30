# TORMENT Memory Substrate — Phase 7G5A1 Native Motif Runtime Mutation Primitives v0.1

## Boundary

Phase 7G5A1 adds `NativeMotifService`, a persistence-only substrate service for
already-decided motif mutations. It does not invoke, port, or select logic from
`MotifRegistry.attach_or_create()`. Fabric, Character, `MotifRegistry`, live
ingest routing, dual write, backend activation, and motif event compatibility
remain unchanged.

Caller adaptation is deliberately paused until 7G5A2. Existing callers still
operate during the legacy pre-flush window; this slice supplies the native
durable primitive they will eventually call without changing that window.

## Current contract archaeology

`MotifRegistry.attach_or_create()` creates a new motif only with its first
member already present. There is no public empty-motif construction path.
Its normal attach path updates centroid, strength, stability, contributors, and
last-active time together with the member list. The native API therefore does
not invent a bare empty-motif operation: `create_motif_with_member()` publishes
motif R1 and the first `MOTIF_MEMBERSHIP` relationship in one transaction.

The runtime list append does not independently de-duplicate a repeated EID,
but the frozen 7F3D current-state admission contract rejects duplicate member
references as ambiguous evidence. Native current membership therefore adopts a
set-like rule: one current logical member relationship per motif and memory
identity. An independent duplicate add is refused; a retry with the same
idempotency identity returns the original result.

## Durable representation

Native motifs use object kind `DERIVED_MOTIF`; new publication transitions have
origin `NATIVE`. A motif state consists of explicit scope, runtime motif ID,
domain ID, label, centroid, strength, stability, contributors, timestamps,
optional derivation metadata, and non-structural flexible metadata.

`members` and `member_count` are not accepted in the motif payload. The
relationship set is authoritative for enumeration. A centroid is ordinary JSON
derived object state, not a representation: the service creates no
representation, READY state, payload, integrity expectation, or H4 claim.

The native UUID is semantic identity. The runtime string motif ID is only a
scoped compatibility alias (`MOTIF_ID`) held in the existing persisted alias
namespace table. Callers must provide that explicit namespace, so the same
runtime string can safely identify different native motifs in different
workspace/domain namespaces. This is an alias-storage reuse, not a claim that
new runtime motifs are legacy objects.

## Membership and state transitions

Membership accepts only an already committed `LEGACY_CORE_NODE` native memory
object. The member endpoint uses `IDENTITY` binding and its actual current
semantic scope. This permits the memory to advance R1 to R2 without retargeting
or changing the membership relationship. Motif membership never patches the
source memory or changes its lifecycle, governance, authority, or current
pointer.

`add_motif_member()` requires a caller-supplied successor `MotifState` because
the current attach path changes aggregate motif state. It atomically publishes
the motif successor and a new membership relationship under one native
transition. `advance_motif_state()` is the narrow no-membership counterpart;
it requires the expected current motif revision and cannot mutate an existing
revision. There is no membership removal primitive in this phase.

All mutations use `execute_semantic`, `SubstrateTx`, `NativeObjectService`, and
`NativeRelationshipService`. Each is idempotent against a stable caller
operation identity; an intent mismatch for that identity conflicts. Results
are reconstructed from durable outputs for lost-response retries.

## Invariants and authority

The combined create-first-member and add-member paths publish one transition,
the motif object effect, the membership relationship effect, durable outputs,
and both current pointers. `SubstrateTx.validate()` enforces H1, H2, H3, and
H8 for these carriers. The focused tests inject an omitted membership effect
and a motif-successor failure; both leave no successor or membership residue.

Motif objects and membership relationships use `NOT_APPLICABLE` authority.
They confer no active authorization. H4 is intentionally untouched; H6/H7 are
not widened by this native runtime slice.

## Explicit deferrals

- Motif clustering, routing, threshold selection, merging, splitting, and
  algorithm adaptation are deferred to 7G5A2.
- Fabric and Character native motif wiring are deferred.
- JSON/JSONL mirrors (`motifs.json`, `motif_events.jsonl`) are not written.
- No dual write, backend activation, production core creation, or cutover is
  included.

# TORMENT Memory Substrate — Phase 7G5B4B

## Target-lane motif re-geometry runtime projection

B4B is the cross-lane counterpart to B4A.  It preserves the admitted 7F
`LEGACY_DERIVED_MOTIF` and its memberships as immutable evidence, then creates
a separate native `DERIVED_MOTIF` R1 only when frozen workspace metadata proves
an explicit source provider/model/dimension that differs from the requested
qualified target lane.

If the source and target lanes match exactly, B4B refuses with
`B4A_LANE_PRESERVING_PROJECTION_AVAILABLE`.  Missing or malformed source lane
metadata refuses with `B4B_SOURCE_LANE_UNQUALIFIED`; unknown is never treated
as different.

## Geometry rule

The B4B target centroid never consumes the legacy centroid numerically.  The
old centroid and old stability remain evidence only.  B4B takes the frozen
legacy member order (which must equal 7F membership-output order), reads each
member's current qualified target-lane `COMPAT_EMBEDDING`, and applies:

```text
ORDERED_CURRENT_MEMBER_REGEOMETRY_V1
```

The first target vector becomes the float32 `_unit` centroid with stability
`0.5`.  Each following target vector uses the existing `_unit`, cosine,
learning-rate, and stability equations from current motif attach semantics.
The iteration calculates one baseline only: it does not publish synthetic
historical revisions or `NATIVE_MOTIF_ADD_MEMBER` events.

The native target state preserves motif ID, domain, label, strength,
contributing agents, and source historical timestamps.  It re-derives only
centroid and stability.  Durable `derivation_metadata` records the B4B
contract, source and target lanes, source motif references, member count, and
algorithm identity.  The prepared intent also binds member identities/current
revisions/representations/vector hashes and the computed geometry digest.

## Topology and reading

One `MIGRATION_RUNTIME_MOTIF_REGEOMETRY_PROJECTION` transaction publishes one
native motif R1, its target alias in a namespace distinct from the source,
and N membership R1 relationships.  Operation output 0 is the motif and
outputs 1..N carry the exact observed baseline member order.

`NativeMotifRuntimeReader` accepts only the two explicit baseline transition
kinds: B4A lane-preserving projection and B4B re-geometry projection.  Later
ordinary native member additions retain their standard publication ordering
after the fixed baseline.

B1 continues to report the legacy source object.  It may classify it
`RUNTIME_READY_AS_IS` when a B4A or B4B target passes the actual A3B reader,
has the correct target lane/scope/alias/member correspondence, and matches its
immutable projection witness.  B4B does not require centroid equality with the
legacy source.

No schema migration, embedding generation, side-store mutation, source
evidence mutation, Fabric/DomainRouter/Character routing, dual read/write,
cutover, authority, merge, or split is opened by B4B.

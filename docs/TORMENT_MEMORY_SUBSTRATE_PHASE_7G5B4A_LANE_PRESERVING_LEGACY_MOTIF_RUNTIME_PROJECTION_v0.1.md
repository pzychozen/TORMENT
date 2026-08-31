# TORMENT Memory Substrate — Phase 7G5B4A

## Lane-preserving legacy motif to native runtime projection

7F admission preserves a legacy motif as immutable evidence:

```text
LEGACY_DERIVED_MOTIF R1 + admitted MOTIF_MEMBERSHIP evidence
```

B4A does not turn that object into a native motif.  Object kind is identity
state, so B4A creates one separate `DERIVED_MOTIF` R1 when — and only when —
the verified snapshot's exact `workspaces/<workspace>/workspace_meta.json`
proves the requested provider, model, and dimension match the target qualified
`NativeRepresentationLane` exactly.

The projection copies only the justified current `MotifState` fields:
`motif_id`, `domain_id`, `label`, `centroid`, `strength`, `stability_score`,
`contributing_agents`, `created_ts`, and `last_active_ts`.  It does not replay
membership history, recompute or normalize the centroid, average embeddings,
or carry legacy-only payload fields into native state.

## Atomic carrier topology

One `MIGRATION_RUNTIME_MOTIF_PROJECTION` native transition publishes:

```text
output 0: DERIVED_MOTIF R1
output 1..N: MOTIF_MEMBERSHIP R1 in observed legacy member order
```

The source alias remains in its source namespace.  The same textual
`MOTIF_ID` is published for the new native object only in the plan's separate
target alias namespace.  B4A refuses alias sharing, alias collisions, missing
or malformed workspace metadata, source/evidence topology drift, an empty or
duplicate source list, order disagreement, non-ready members, or any lane
mismatch.

The source `members` artifact order must equal the 7F operation-output order.
For each member B4A verifies the source EID alias/evidence identity, current
runtime-semantic object state, and a `READY`/`USABLE`/`MATCH` current qualified
`COMPAT_EMBEDDING` at the requested dimension.  Native membership endpoints
use the existing `NativeMotifService` rule: the member's current semantic scope
is retained; the historical 7F endpoint scope is not copied.

## Reader and readiness behavior

`NativeMotifRuntimeReader` retains the old shared transition/effect ordering
for ordinary native motifs.  Only a native motif whose creation transition and
operation are both `MIGRATION_RUNTIME_MOTIF_PROJECTION` uses B4A operation
output ordinals for its baseline memberships.  Later
`NATIVE_MOTIF_ADD_MEMBER` transitions append through the ordinary real motif
revision sequence after that fixed baseline.  Invalid or ambiguous output,
effect, duplicate-member, or post-projection evidence fails closed.

B1 still reports the 7F `LEGACY_DERIVED_MOTIF` evidence object.  It calls the
actual A3B reader and validates the exact B4A intent correspondence before
classifying that source evidence as `RUNTIME_READY_AS_IS`; it never retypes the
legacy source object.

## Deliberate exclusions

No schema migration, reconciliation, re-geometry, embedding generation,
side-store write, Fabric/DomainRouter/Character routing, dual-write, dual-read,
cutover, authorization, merge, or split is opened by B4A.  The deployment
remains `STAGING` / `LEGACY_ACTIVE` and schema remains v1.2.

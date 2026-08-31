# TORMENT Memory Substrate 7G5E3 — Native Motif Split and Membership Retirement

## Boundary

7G5E3 closes the native motif-storage compatibility gap for legacy automatic
motif splitting. It is storage-only: it adds no production selector,
activation, cutover, shared-domain storage, or CharacterStore migration.

`NATIVE_ACTIVE = NO`
`DUAL_WRITE = NO`
`DUAL_READ = NO`
`CUTOVER_OPENED = NO`

## Frozen legacy law

The pure `torment_service.motif_split_policy` helper preserves the current
`MotifRegistry._maybe_split_motif()` law without I/O, clocks, identity
allocation, or mutation:

- enabled; minimum 96 usable, already unit-normalized member vectors;
- parent radius `mean(1 - clip(X @ parent_centroid, -1, 1))`, threshold `.22`;
- seed A is farthest from parent centroid; seed B is farthest from seed A;
- exactly twelve two-means iterations; `db < da` means ties stay in parent
  cluster 0;
- each child must have at least 16 members;
- SSE improvement must be at least `.08`;
- parent is cluster 0 and the new child is cluster 1.

The parent keeps its runtime ID and label. The child ID follows the recovered
global legacy numeric counter and parent prefix:
`{parent}_split_{counter:04d}`. Child order is the filtered legacy cluster
member order, never UUID, rowid, or a freshly sorted order. Parent and child
strength use the existing `0.12 + 0.88 * (1 - exp(-n / 24))` law with legacy
parent/child floors; stability and contributing agents retain the post-attach
legacy values.

## Membership existence semantics

Current membership is exactly a current `MOTIF_MEMBERSHIP` relationship
revision with `existence_state = EXISTS`.

Moving an existing parent member creates one `NATIVE_ORDINARY` successor on
the *same* relationship identity with `existence_state = RETIRED`. The
successor retains the same motif endpoint, member endpoint, semantic scope,
identity namespace, and payload. It is historical evidence only; it is not a
current member and cannot confer authority. A new child membership is a new
relationship identity with `EXISTS`.

The incoming candidate is created only in its final cluster. It is never
created on the parent merely to be retired immediately.

Both current-member readers exclude retired memberships and reject unknown
current membership existence states. B4A baseline ordering remains auditable:
each baseline R1 must be current active (R1 or successor) or have exactly one
current `RETIRED` ordinary successor pointing to that R1. A missing baseline
membership is still an invariant failure.

## Atomic topology and recovery

A true native attach-and-split is one semantic transaction. It publishes:

1. the source memory R1 (for composition), parent successor, and child R1;
2. the child `MOTIF_ID` alias;
3. every required retirement successor and child membership R1;
4. typed object/relationship effects and matching operation outputs; and
5. only then the current relationship and parent pointers.

Failure seams after the parent successor, child object, first retirement,
partial child memberships, and before pointer publication roll back entirely.
The stored split intent contains the partition and catalog witness. An exact
lost-response retry recovers the original parent/child result; a differing
partition or precommit catalog witness under the same key is refused.

## Reader and writer integration

`NativeMemoryMotifCompositionService`, the motif decision adapter, native
Character correction, and native Character seed planting use the same
qualified split preparation and persistence semantics. Incomplete qualified
historical vector evidence cannot safely imitate legacy JSON member omission,
so it leaves an ordinary attach unchanged. At or above 96, no-split geometry
also remains an ordinary attach.

The Fabric route reports parent plus child for a split and appends exactly the
new child to process order; the parent retains its position. Cold recovery
continues to use the documented lexicographic baseline. Existing-workspace
admission preserves an observed legacy motif at or above 96 and never forces a
split during migration; the next native attachment evaluates this law.

## Qualification evidence

Focused tests freeze below-radius, undersized-child, low-improvement,
deterministic true-split, and later-attach decisions, including the real
legacy `MotifRegistry` mutation result. Native tests prove retirement lineage,
active-reader exclusion, child alias recovery, idempotent recovery, immutable
retirement evidence, and rollback seams. Composition tests cover a qualified
96-member parent that splits into final 47/49 membership topology, with 48
retirement successors and no transient candidate membership; a qualified
96-member no-split geometry remains one active motif with no retirement or
child; and a later second split uses current active children only. The B4A
projection test closes, reopens, and recovers a retired baseline member with
its original child order and alias.

`SCHEMA_VERSION_CHANGE_REQUIRED = NO`: relationship revisions already accept
the required `RETIRED` existence-state text.

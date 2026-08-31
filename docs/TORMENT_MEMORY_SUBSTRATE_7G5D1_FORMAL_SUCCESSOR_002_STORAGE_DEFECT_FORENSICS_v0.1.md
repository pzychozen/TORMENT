# TORMENT Memory Substrate 7G5D1 — Formal Successor-002 Storage-Defect Forensics v0.1

## Status and evidence boundary

This is a documentation-only closure of the valid successor-002 result. It
does not modify the native substrate, migration, B-series material, formal
fixture, tolerances, Fabric, or the permanent external administration record.

| Item | Value |
|---|---|
| administration | `7g5d1-core-formal-successor-20260831-002` |
| harness validity | `VALID` |
| storage verdict | `STORAGE_SUBSTRATE_DEFECT` |
| qualified post-write verdict | `QUALIFIED_POST_WRITE_EQUIVALENT_IN_ADMINISTERED_PROFILE` |
| marker SHA-256 | `542040DAB6752709D20C6A59E7F6181C5AC65E770D84828C9928944AE3A8A97A` |
| result SHA-256 | `9575C37AF609FC8E651EA9D7E209A6FB465A5C41329F6AC095852ADE97C90C98` |
| frozen work-tree SHA-256 | `e8237a0384d2122a4ea9e98d907d3f0037b5e28ced4e0800d6354cb5069d4351` |
| immutable source | `C:\\TORMENT\\experiments\\7g5d1_core_formal_successor_20260831_002` |

The exact, machine-readable comparison table is
[TORMENT_MEMORY_SUBSTRATE_7G5D1_FORMAL_SUCCESSOR_002_STORAGE_DIFFERENCES_v0.1.json](TORMENT_MEMORY_SUBSTRATE_7G5D1_FORMAL_SUCCESSOR_002_STORAGE_DIFFERENCES_v0.1.json).
It contains all 53 emitted rows, each retaining arm, fixture id, field,
legacy value, native value, and comparison rule. It is a transcription of the
immutable result, not a revised result.

## Measured inventory

| Arm | Difference rows |
|---|---:|
| `M1_CREATE` | 3 |
| `M2_REINFORCE` | 7 |
| `M3_DISTINCT` | 6 |
| `M4_CONTRADICTION` | 14 |
| `M5_NO_WRITE` | 0 |
| `SEQUENTIAL` | 23 |
| **Total** | **53** |

| Comparison field | Rows |
|---|---:|
| `lifecycle` | 11 |
| `governance` | 11 |
| `provenance` | 11 |
| `strength` | 4 |
| `confidence` | 3 |
| `half_life_days` | 3 |
| `reinforced` | 2 |
| `summary` | 2 |
| `motif_membership` | 2 |
| `motif_geometry` | 2 |
| `reinforcement_count` | 2 |
| **Total** | **53** |

The individual event inventories are intentionally preserved rather than
summarized away:

| Arm / fixture | Fields differing | Row count |
|---|---|---:|
| `M1_CREATE` / `CORE-M1-create` | lifecycle, governance, provenance | 3 |
| `M2_REINFORCE` / `CORE-M2-create` | lifecycle, governance, provenance | 3 |
| `M2_REINFORCE` / `CORE-M2-reinforce` | lifecycle, governance, provenance, strength | 4 |
| `M3_DISTINCT` / `CORE-M3-create` | lifecycle, governance, provenance | 3 |
| `M3_DISTINCT` / `CORE-M3-distinct` | lifecycle, governance, provenance | 3 |
| `M4_CONTRADICTION` / `CORE-M4-create` | lifecycle, governance, provenance | 3 |
| `M4_CONTRADICTION` / `CORE-M4-contradiction` | reinforced, summary, lifecycle, governance, provenance, motif_membership, motif_geometry, strength, confidence, half_life_days, reinforcement_count | 11 |
| `M5_NO_WRITE` / `CORE-M5-no-write` | none | 0 |
| `SEQUENTIAL` / `CORE-S-create` | lifecycle, governance, provenance | 3 |
| `SEQUENTIAL` / `CORE-S-reinforce` | lifecycle, governance, provenance, strength, confidence, half_life_days | 6 |
| `SEQUENTIAL` / `CORE-S-distinct` | lifecycle, governance, provenance | 3 |
| `SEQUENTIAL` / `CORE-S-contradiction` | reinforced, summary, lifecycle, governance, provenance, motif_membership, motif_geometry, strength, confidence, half_life_days, reinforcement_count | 11 |

## M1 earliest differences

`CORE-M1-create` is the first administered event and therefore has no prior D1
storage operation that can explain its three differences. The immutable result
records the legacy lifecycle as `ACTIVE` and governance as `UNKNOWN`; native
records `ORDINARY` and `DERIVED`, with `authoritative=false` on both. The
legacy provenance is its original seven-field payload map, whereas native is
the normalized five-field `RUNTIME_PROVENANCE_V1` projection.

Read-only source inspection explains the comparison surface without changing
the result:

- `experiments/memory_substrate_d1_trace_replay_v1/native_replay.py` builds a
  `NativeFabricRouteRequest` from the frozen facts but passes neither
  lifecycle nor governance state. `NativeFabricRouteRequest` supplies
  `ORDINARY` and `DERIVED` defaults in
  `torment_service/substrate/fabric_native_routing.py`.
- `formal_core_ports._evidence_for_result()` reads native lifecycle and
  governance from the current compatibility view and projects provenance from
  `provenance_records` to five normalized columns. In contrast,
  `formal_core_legacy_worker._legacy_evidence()` reads lifecycle, governance,
  and provenance from the legacy payload map.

These are directly observed mapping/projection differences. This record does
not claim that the legacy broad payload or the native normalized provenance
model is semantically superior, nor does it treat either projection as proof
of corruption.

## Causal taxonomy and repair order

The labels below distinguish an observed result from a code-path inference.
Only the latter uses the cited source paths. None authorizes a repair.

| ID | Observed fields and events | Status | Current native owner / legacy semantic owner | B-series and repair implications |
|---|---|---|---|---|
| `D1-STORAGE-01` | lifecycle and governance on every stored event (22 rows) | Primary; direct at M1 | Frozen route request construction and `NativeFabricRouteRequest` defaults / legacy Fabric payload fields | Establish an explicit input-mapping decision first. It must preserve B-series identity, alias, provenance, and migration invariants; no migration is implicated or authorized here. |
| `D1-STORAGE-02` | provenance on every stored event (11 rows) | Primary comparison-surface incompatibility; direct at M1 | formal native evidence projection / legacy worker payload evidence | First decide whether the accepted contract compares semantic intent or exact retained payload shape. A future adapter change must not rewrite retained B-series evidence. |
| `D1-STORAGE-03` | strength on M2 reinforcement, sequential reinforcement, and both contradiction outputs; confidence and half-life on the sequential reinforcement and both contradiction outputs (10 rows) | Primary observable metric mismatch; deeper causal mechanism unresolved | `memory_reinforcement.realize_reinforcement_patch`, new-memory/world-state paths / legacy Fabric and MemoryGraph live state | The native and legacy source both visibly contain the capped strength rule, but the result still differs. Isolate pre-reinforcement state and process-world inputs before any formula change; preserve B-series migration outputs. |
| `D1-STORAGE-04` | reinforced, summary, motif membership/geometry, reinforcement count, and related metrics on both contradiction events (10 rows excluding shared fields) | Primary branch mismatch; direct flow inference | native duplicate selection in `fabric_native_routing._select_private_duplicate` / legacy Fabric contradiction guard | The frozen native facts have no callable contradiction guard, so the native selector can reinforce; legacy Fabric applies its canonical-conflict guard before reinforcement. Define an admissible, native-owned contradiction decision before changing routing or motif behavior. No legacy target selection is admitted. |

`D1-STORAGE-03` and `D1-STORAGE-04` overlap on strength, confidence, and
half-life where the contradiction takes the different branch; the table counts
each observed field once. The taxonomy is not a claim that count alone proves
causality.

Recommended future investigation/repair order, subject to a new explicit
workorder, is:

1. Resolve `D1-STORAGE-01` and `D1-STORAGE-02` at the M1 input/evidence
   boundary, because they are present before any prior D1 transition.
2. Define and qualify a native-owned contradiction decision for
   `D1-STORAGE-04`, then test its effect on creation, motif composition, and
   reinforcement selection.
3. Isolate the state inputs behind `D1-STORAGE-03`; do not change the shared
   reinforcement equation merely because its observed output differs.
4. Re-run only a newly authorized scientific administration after a coherent
   repair and preflight. Successor-002 itself is permanently consumed.

## Retrieval, structural, and out-of-scope classification

Retrieval evidence is characterization, not a closed-loop query-parity result:
M1, M3, M4, and M5 recorded no retrieval difference; M2 recorded a ranking
score difference (`1.0` legacy versus `0.9987793372628647` native); sequential
recorded ranking identity differences. The immutable result itself retains
`D1_CLOSED_LOOP_QUERY_PARITY_TESTED=NO`, so this closure does not classify
those observations as a repaired or separately proven query defect.

All 12 native structural rows remained valid. Restart evidence matched for all
six arms. Every post-write difference list was empty. M5 remained exact:
`router_not_invoked=true`, `route_witness_absent=true`,
`durable_storage_unchanged=true`, and `stored_object_created=false`.
Character remained outside the administration:
`CHARACTER_ARM_ADMINISTERED=NO` and
`CHARACTER_SUBARM_STATUS=DEFERRED_PENDING_PROVENANCE_VOCABULARY`.

## Closure declarations

```text
RESULT_CLOSURE_COMMIT = ddb589e5daebe1c1f66160e9293af126f680c1ee
TOTAL_STORAGE_DIFFERENCES = 53
BY_ARM_COUNTS = M1:3,M2:7,M3:6,M4:14,M5:0,SEQUENTIAL:23
PRIMARY_ROOT_CAUSE_COUNT = 4
POST_WRITE_EQUIVALENCE_PRESERVED = YES
M5_NO_WRITE_PRESERVED = YES
STRUCTURAL_INVARIANTS_PRESERVED = YES
RETRIEVAL_CLASSIFICATION = CHARACTERIZATION_ONLY_NOT_CLOSED_LOOP_QUERY_PARITY
PRODUCTION_FILES_CHANGED = 0
SUBSTRATE_FILES_CHANGED = 0
MIGRATION_FILES_CHANGED = 0
NO_NEW_ADMINISTRATION = YES

7G5D1M_RESULT_CLOSURE = YES
7G5D1M_STORAGE_FORENSICS_COMPLETE = YES
D1_SCIENCE_COMPLETE = YES
D1_STORAGE_REPAIR_IMPLEMENTED = NO
D1_PRODUCTION_ACTIVATION = NO
```

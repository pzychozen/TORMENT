# TORMENT Memory Substrate 7G5D1N — D1-Identified Defect Causal Adjudication v0.1

## Boundary

This record is additive to the valid successor-002 result. It neither changes
the immutable D1 fixture or tolerances nor reclassifies the historical
`STORAGE_SUBSTRATE_DEFECT` result. The successor-002 evidence remains at:

```text
C:\TORMENT\experiments\7g5d1_core_formal_successor_20260831_002
RESULT_SHA256 = 9575C37AF609FC8E651EA9D7E209A6FB465A5C41329F6AC095852ADE97C90C98
MARKER_SHA256 = 542040DAB6752709D20C6A59E7F6181C5AC65E770D84828C9928944AE3A8A97A
```

The separate `D1_IDENTIFIED_DEFECT_REGRESSION_V1` profile is a disposable
post-D1 instrument. It creates no formal marker, no formal result root, and
no production activation.

## Refined classifications

| ID | Classification | Causal adjudication | Disposition |
|---|---|---|---|
| `D1-STORAGE-01A` | `LIFECYCLE_COMPARISON_SEMANTIC_LAYER_MISMATCH` | Confirmed as a comparison-vocabulary mismatch. The legacy direct-ingest rows carry a production lifecycle envelope of `unset`, row-authoritative, with no join; the native route records `ORDINARY` in its separate structural vocabulary. The original string comparison was not a supported semantic comparison. | Add a narrow direct-ingest lifecycle behavior projection; do not create a universal mapping. |
| `D1-STORAGE-01B` | `GOVERNANCE_COMPARISON_SEMANTIC_LAYER_MISMATCH` | Confirmed as a comparison-surface mismatch. Legacy `resolve_governance(payload)` yields the five behavioral booleans; native stores those exact booleans revision-bound in `object_revision_governance`. `UNKNOWN` versus `DERIVED` is not the behavioral governance contract. | Compare all five booleans exactly; do not change native governance storage. |
| `D1-STORAGE-02` | `PROVENANCE_COMPARISON_PROJECTION_MISMATCH` | Confirmed as a comparison-projection mismatch. Native `translate_provenance_v1()` persists the validated seven-field `ProvenanceV1` value in `provenance_records.descriptive_notes` under `TORMENT_PROVENANCE_V1_DESCRIPTIVE/1`. | Read and validate the retained descriptive evidence; refuse the projection if it is absent or malformed. |
| `D1-STORAGE-04` | `CONTRADICTION_GUARD_INTEGRATION_BINDING_OMISSION` | Confirmed. The router already accepts and calls `NativeFabricRouteRequest.contradiction_guard`, but the original D1 input-to-request adapter left it `None`. Legacy production independently called `_detect_canon_conflict()` before duplicate reinforcement. | Bind a deterministic native-owned callback using that production semantic function. Never pass a legacy branch answer, selected EID, or observed guard answer. |
| `D1-STORAGE-03A` | `HIGH_STRENGTH_REINFORCEMENT_MONOTONICITY_DEFECT` | **Not confirmed.** The original comparator read legacy response signals rather than the durable successor payload. The retained legacy M2 node proves that the `0.999943` predecessor became `0.98`, matching the live production cap. | No patch to `memory_reinforcement.py`. Retain the characterization regression. |
| `D1-STORAGE-03B` | `SEQUENTIAL_REINFORCEMENT_STATE_INPUT_MISMATCH_UNRESOLVED` | Still unresolved until the corrected semantic projection and contradiction binding remeasure the actual persisted legacy/native successors. The original sequential metric comparison also used response signals rather than the legacy durable payload. | Do not tune strength, confidence, or half-life. The regression profile records pre/post payload facts and reports any residual difference. |

## High-strength reinforcement archaeology

The ordinary production reinforcement branch in `torment_service/fabric.py`
uses the exact expression:

```python
round(min(0.98, old_strength + (1.0 - old_strength) * 0.3), 4)
```

The retained successor-002 `M2_REINFORCE` legacy `nodes.jsonl` provides a
real persisted example, not merely a calculated expectation:

| Predecessor strength | Legacy persisted successor | Reduction allowed? |
|---:|---:|---|
| `0.50` | `0.65` | no reduction |
| `0.95` | `0.965` | no reduction |
| `0.9799` | `0.98` | no reduction |
| `0.98` | `0.98` | no reduction |
| `0.9801` | `0.98` | yes |
| `0.999943` | `0.98` | yes; retained `CORE-M2-reinforce` evidence |

`realize_reinforcement_patch()` implements the same capped branch. Therefore
the evidence contradicts the proposed monotonicity premise; no plausible
`max(...)` substitute is authorized.

## Narrow projection contract

The new regression profile compares only the following:

- Governance: `protected`, `non_shareable`, `collective_export_blocked`,
  `collective_reingest_blocked`, and `decay_accelerated` as exact booleans.
- Provenance: `source_type`, `source_role`, `write_path`,
  `created_at_step`, `created_at_ts`, `parent_eids`, and `schema_version`,
  recovered from actual native descriptive evidence.
- Lifecycle: direct-ingest ordinary/current visibility and protected versus
  non-protected disposition. The legacy row/join authority evidence and the
  native structural `lifecycle_authoritative` value are retained as separate
  observations, not asserted equal across the two vocabularies.
- Durable payload metrics: legacy values come from the current stored node,
  not response signals.

If the native descriptive provenance record is missing, malformed, or does
not carry the required validated fields, the profile reports a real
compatibility defect and refuses that projection rather than manufacturing a
value.

## Declarations

```text
D1_ORIGINAL_RESULT_UNCHANGED = YES
D1_ORIGINAL_DIFFERENCE_COUNT = 53
ORIGINAL_33_PROJECTION_ROWS = HISTORICAL_D1_DIFFERENCES

LIFECYCLE_ROOT_CAUSE_FINAL_CLASSIFICATION = D1-STORAGE-01A
GOVERNANCE_ROOT_CAUSE_FINAL_CLASSIFICATION = D1-STORAGE-01B
PROVENANCE_ROOT_CAUSE_FINAL_CLASSIFICATION = D1-STORAGE-02
CONTRADICTION_ROOT_CAUSE_FINAL_CLASSIFICATION = D1-STORAGE-04

HIGH_STRENGTH_MONOTONICITY_CONFIRMED = NO
03A_REPAIR_IMPLEMENTED = NO
03A_FILES_CHANGED = 0
03B_STATUS = UNRESOLVED_PENDING_REGRESSION_V1_REMEASUREMENT

NEW_FORMAL_ADMINISTRATION = NO
NATIVE_ACTIVE = NO
DUAL_WRITE = NO
DUAL_READ = NO
CUTOVER_OPENED = NO
```

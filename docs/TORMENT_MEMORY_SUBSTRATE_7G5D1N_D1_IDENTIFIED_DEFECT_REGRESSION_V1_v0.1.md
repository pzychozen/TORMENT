# TORMENT Memory Substrate — 7G5D1N D1-identified-defect regression V1

## Scope and preserved scientific result

This is the separate `D1_IDENTIFIED_DEFECT_REGRESSION_V1` profile requested
after the valid D1 successor-002 result. It is not a D1 formal
administration: it created no formal marker, no formal result root, and no
production activation. It used fresh disposable legacy and native clones of
the immutable CORE_ONLY fixture and removed those clones when complete.

The original successor-002 result remains unchanged:

```text
HARNESS_VALIDITY = VALID
STORAGE_SUBSTRATE_VERDICT = STORAGE_SUBSTRATE_DEFECT
QUALIFIED_POST_WRITE_VERDICT = QUALIFIED_POST_WRITE_EQUIVALENT_IN_ADMINISTERED_PROFILE
D1_ORIGINAL_DIFFERENCE_COUNT = 53
ORIGINAL_33_PROJECTION_ROWS = HISTORICAL_D1_DIFFERENCES
```

The 33 historical projection rows are not deleted, reclassified in the
original result, or used to claim a retroactive PASS.

## Regression V1 method

The profile preserves the immutable fixture and frozen tolerances. It differs
from the historical comparator only in these explicit, read-only comparison
surfaces:

- Lifecycle compares direct-ingest behavior: ordinary/current visibility and
  protected disposition. The retained authority observations remain visible as
  evidence, but `unset`/row-authoritative is not equated by string to native
  `ORDINARY`/structural state.
- Governance compares the five booleans from production `resolve_governance`
  to the exact `object_revision_governance` row bound to the native current
  revision.
- Provenance recovers all seven values from the actual native
  `provenance_records` row and its retained
  `TORMENT_PROVENANCE_V1_DESCRIPTIVE/1` evidence. It compares those values to
  the frozen `ProvenanceV1` intent. A newly replayed legacy HTTP write has a
  new wall-clock `created_at_ts`; that mutable observation is retained in the
  regression evidence, but is not substituted for the frozen administered
  intent.
- Native M4 and sequential routing bind only
  `_detect_canon_conflict(incoming, existing, similarity)[0]`. No legacy EID,
  branch result, selected target, or observed guard answer enters the native
  request.
- Legacy storage scalars use the selected current legacy node payload rather
  than the historical HTTP response-signal surface.

## Results

```text
REGRESSION_V1_RUN = PASS
REGRESSION_V1_DIFFERENCE_COUNT = 4
REGRESSION_V1_BY_FIELD = {"half_life_days": 4}
REGRESSION_V1_BY_EVENT = {
  "CORE-M3-distinct": 1,
  "CORE-M4-contradiction": 1,
  "CORE-S-distinct": 1,
  "CORE-S-contradiction": 1
}

POST_WRITE_PASS_PRESERVED = YES
M5_PASS_PRESERVED = YES
STRUCTURAL_PASS_PRESERVED = YES
```

The remaining values are all durable half-life differences, within the
already-declared 03B boundary:

| Fixture | Legacy durable half-life | Native durable half-life |
| --- | ---: | ---: |
| `CORE-M3-distinct` | 99.03724640692022 | 99.33128211275871 |
| `CORE-M4-contradiction` | 99.26763448262744 | 99.55574927563462 |
| `CORE-S-distinct` | 92.39835612104098 | 93.3092862907214 |
| `CORE-S-contradiction` | 91.96584731485419 | 93.19844095045838 |

No confidence or half-life formula was changed. The recorded M4 and sequential
contradiction outcomes are native `stored=True`, `reinforced=False`; their
summaries, motif membership/geometry, reinforcement count, strength, and
confidence are characterized by the profile without being made a new forced
equality rule.

## Root-cause status

```text
LIFECYCLE_ROOT_CAUSE_FINAL_CLASSIFICATION = D1-STORAGE-01A LIFECYCLE_COMPARISON_SEMANTIC_LAYER_MISMATCH; REGRESSION_V1_SEMANTIC_EQUIVALENT
GOVERNANCE_ROOT_CAUSE_FINAL_CLASSIFICATION = D1-STORAGE-01B GOVERNANCE_COMPARISON_SEMANTIC_LAYER_MISMATCH; REGRESSION_V1_SEMANTIC_EQUIVALENT
PROVENANCE_ROOT_CAUSE_FINAL_CLASSIFICATION = D1-STORAGE-02 PROVENANCE_COMPARISON_PROJECTION_MISMATCH; REGRESSION_V1_FROZEN_INTENT_EQUIVALENT
CONTRADICTION_ROOT_CAUSE_FINAL_CLASSIFICATION = D1-STORAGE-04 CONTRADICTION_GUARD_INTEGRATION_BINDING_OMISSION; REGRESSION_V1_CORRECTED

CONTRADICTION_GUARD_BOUND = YES
LEGACY_BRANCH_ANSWER_SUPPLIED_TO_NATIVE = NO

LEGACY_REINFORCEMENT_CHARACTERIZATION = 0.50->0.65; 0.95->0.965; 0.9799->0.98; 0.98->0.98; 0.9801->0.98; 0.999943->0.98
HIGH_STRENGTH_MONOTONICITY_CONFIRMED = NO
03A_REPAIR_IMPLEMENTED = NO
03A_FILES_CHANGED = NONE

03B_STATUS = UNRESOLVED; FOUR DURABLE HALF_LIFE_DAYS DIFFERENCES RETAINED FOR TRACE
```

The high-strength characterization establishes that the live legacy law caps
ordinary reinforcement at `0.98`; a predecessor of `0.999943` becomes
`0.98`. `realize_reinforcement_patch()` already reproduces this law, so no
native formula change was justified.

## Qualification and non-activation declaration

The profile’s focused semantic tests passed under `torment-substrate`
(Python 3.11.15, sqlite3 module 2.6.0, SQLite 3.53.4), followed by 144 passing
implicated D1, routing, reinforcement, and post-write tests. The profile also
validated M5 no-write absence and all 12 native structural witnesses.

```text
NEW_FORMAL_ADMINISTRATION = NO
7G5D1N_SLICE1_COMPLETE = YES
D1_IDENTIFIED_DEFECTS_REMAINING = 4 / D1-STORAGE-03B

NATIVE_ACTIVE = NO
DUAL_WRITE = NO
DUAL_READ = NO
CUTOVER_OPENED = NO
PRODUCTION_SELECTOR_ADDED = NO
```

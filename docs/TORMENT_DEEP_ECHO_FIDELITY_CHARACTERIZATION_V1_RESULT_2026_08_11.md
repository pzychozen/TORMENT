# TORMENT Deep Echo Fidelity Characterization V1 Result

Experiment label: `DEEP_ECHO_FIDELITY_CHARACTERIZATION_V1`

Frozen result: `CONTROLLED_TRANSFORM_CHARACTERIZED`

Date preserved: 2026-08-11

## Baseline

Authoritative repository:

`C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric`

Baseline:

`HEAD == origin/main == 1e3d04a3857c40df404d4f8f8d0d930e820f6f84`

Baseline commit:

`1e3d04a3857c40df404d4f8f8d0d930e820f6f84`

Tag / subject:

`v2.5.0` / `fix(security): enforce REST authentication boundary`

For this experiment, the v2.5.0 security work was verified as memory-neutral:
the transform-isolation result was produced at this baseline without modifying
memory production behavior, compression thresholds, DeepMemory persistence, or
the 200-character production transform.

## Experiment Type

`TRANSFORM_ISOLATION_CHARACTERIZATION`

Stage-1 had already established authentic `long_path` creation, persistence,
restart retrieval, and Spirit Return reachability. V1 isolated this production
path:

`persisted MemoryGraph source summary -> CompressionScorer -> CompressionRouter eligibility -> CompressionExecutor long_path -> persisted/reloaded DeepMemory.summary`

EventDetector was intentionally omitted from this V1 transform isolation because
it determines when compression fires and does not transform text.

## Production Finding

Production `CompressionScorer` derives:

`candidate.summary = source_summary[:200]`

Layer B did not reproduce that operation in its measurement/classification
logic. Layer B measured the actual returned echo boundary from production
output after real scorer/router/executor/deep-store execution and fresh
`DeepMemoryStore` reload.

`DeepMemoryStore` persistence added no further textual transformation before
the persisted/reloaded `DeepMemory.summary` was consumed as the deep echo.

## Source-Survival Boundary

Production `long_path` did not delete or truncate the source `MemoryGraph` row.

For all 10 Layer-B fixtures:

`post_execution_source_summary == graph_read_source_summary`

and:

`post_execution_source_strength == 0.1`

Therefore the allowed system-level interpretation is:

`ABSENT_FROM_DEEP_ECHO`

The following are not demonstrated by V1:

- `LOST_FROM_TORMENT`
- effective retrieval loss
- provider confusion
- false corroboration
- echo dominance

## Statistical Boundary

These fixtures were deliberately engineered to expose specific semantic
regimes. The experiment establishes mechanical reachability of those regimes.
It does not estimate natural prevalence.

Prohibited interpretations include:

- "70% of natural deep echoes fragment"
- "30% of production deep echoes are misleading"

Natural incidence was not measured.

## Verified Aggregate

F-label counts:

| Label | Count |
| --- | ---: |
| F0_FULL_SEMANTIC_PRESERVATION | 1 |
| F1_LOSSY_BUT_BOUNDARY_CLEAN | 2 |
| F2_NONCRITICAL_DETAIL_LOSS | 1 |
| F3_CAUSAL_OR_RELATIONAL_LOSS | 1 |
| F4_STATE_OR_NEGATION_LOSS | 3 |
| F5_BOUNDARY_BLIND_FRAGMENT | 7 |
| F6_SEMANTICALLY_MISLEADING_ECHO | 3 |

Boundary classes as produced by the harness:

| Boundary Class | Count |
| --- | ---: |
| BOUNDARY_BLIND_FRAGMENT | 7 |
| CLEAN_BOUNDARY | 2 |
| NO_ABSENT_CHARACTERS | 1 |

Critical facts:

| State | Count |
| --- | ---: |
| PRESERVED | 12 |
| PARTIAL | 1 |
| LOST | 10 |

Noncritical facts:

| State | Count |
| --- | ---: |
| LOST | 1 |

Combined LOST facts:

`11`

Correction/supersession loss:

`3 fixtures`

## CLEAN_BOUNDARY Correction

The harness predicate for `CLEAN_BOUNDARY` was:

`last.isspace() or last in ".!?"`

Therefore `CLEAN_BOUNDARY` merges:

- whitespace-aligned cuts
- sentence-terminator-complete cuts

Observed in this run:

- `2` CLEAN_BOUNDARY fixtures
- `2/2` ended on whitespace
- `0` ended on `.`, `!`, or `?`

Therefore `B06` and `B09` demonstrate whitespace-aligned lossy boundaries.
They do not demonstrate a sentence-complete plausible echo where no visible
signal of omission exists.

In particular:

`B09_CLEAN_BUT_MISLEADING_SENTENCE_BOUNDARY`

must be described historically as the fixture's authored/name intent, not as an
achieved result. Its echo ended in a long whitespace run.

Preserve the raw fixture ID unchanged for provenance, but freeze:

`SENTENCE_TERMINATOR_COMPLETE_MISLEADING_ECHO: NOT_DEMONSTRATED`

## F6 Interpretation

`F6` was mechanically derived from preregistered relations:

- `superseded_fact_id`
- `correcting_fact_id`

No provider and no post-hoc prose judgement assigned `F6`.

Safe result:

`CORRECTION_OR_SUPERSESSION_LOST: DEMONSTRATED`

Do not claim that all `F6` echoes necessarily read as naturally plausible or
sentence-complete.

## Non-ASCII Result

`B10` demonstrated a genuine Python code-point grapheme split: the base `e` of
an NFD `e + U+0301` sequence remained inside the echo while the combining acute
fell outside it.

Frozen results:

`CODEPOINT_GRAPHEME_SPLIT: DEMONSTRATED`

`UTF8_OR_PERSISTENCE_CORRUPTION: NOT_OBSERVED`

The harness `grapheme_split` detector only detects an orphaned combining mark.
It does not establish coverage for all Unicode grapheme-cluster forms, such as
ZWJ sequences or regional-indicator pairs.

## Classifier Scope Note

Latent but untriggered classifier asymmetry:

- `F2` evaluates `LOST` facts only.
- `F3` and `F4` evaluate `LOST_OR_PARTIAL` facts.

This did not affect the present result. The sole `PARTIAL` fact occurred in
`B10`. `B02`, the sole `F2` fixture, contained two critical `PRESERVED` facts
and one noncritical `LOST` fact.

Do not modify the historical classification. Record this before classifier
reuse.

## Tier Scope

All ten Layer-B fixtures derived:

`retention_tier == situational`

Tier-dependent routing behavior was therefore not characterized by V1.

## Per-Fixture Table

| Fixture | Route | Boundary / Correction | Labels |
| --- | --- | --- | --- |
| B01_FULL_PRESERVATION_AND_SENTENCE_CONTROL | long_path | NO_ABSENT_CHARACTERS | F0 |
| B02_NONCRITICAL_TAIL_LOSS | long_path | BOUNDARY_BLIND_FRAGMENT | F2,F5 |
| B03_ENTITY_LOCATION_LOSS | long_path | BOUNDARY_BLIND_FRAGMENT | F5 |
| B04_CAUSAL_REASON_SEVERING | long_path | BOUNDARY_BLIND_FRAGMENT | F3,F5 |
| B05_NEGATION_LOSS | long_path | BOUNDARY_BLIND_FRAGMENT | F4,F5,F6 |
| B06_STATE_REVERSAL_LOSS | long_path | WHITESPACE-ALIGNED according to the broad historical CLEAN_BOUNDARY predicate | F1,F4,F6 |
| B07_CHRONOLOGY_LOSS | long_path | BOUNDARY_BLIND_FRAGMENT | F5 |
| B08_QUALIFICATION_UNCERTAINTY_LOSS | long_path | BOUNDARY_BLIND_FRAGMENT | F5 |
| B09_CLEAN_BUT_MISLEADING_SENTENCE_BOUNDARY | long_path | historical fixture ID only; actually WHITESPACE-ALIGNED, not sentence-terminator complete | F1,F4,F6 |
| B10_NON_ASCII_BOUNDARY | long_path | BOUNDARY_BLIND_FRAGMENT; orphaned-combining-mark grapheme split demonstrated | F5 |

## Final Frozen Result

`DEEP_ECHO_FIDELITY_CHARACTERIZATION_V1`

`CONTROLLED_TRANSFORM_CHARACTERIZED`

| Result | Status |
| --- | --- |
| FULL_ECHO_PRESERVATION | DEMONSTRATED |
| CRITICAL_FACT_ABSENCE_FROM_DEEP_ECHO | DEMONSTRATED |
| CAUSAL_RELATIONAL_ABSENCE_FROM_DEEP_ECHO | DEMONSTRATED |
| STATE_NEGATION_CORRECTION_ABSENCE_FROM_DEEP_ECHO | DEMONSTRATED |
| CORRECTION_OR_SUPERSESSION_LOST | DEMONSTRATED |
| BOUNDARY_BLIND_FRAGMENT | DEMONSTRATED |
| WHITESPACE_ALIGNED_LOSSY_BOUNDARY | DEMONSTRATED |
| SENTENCE_TERMINATOR_COMPLETE_MISLEADING_ECHO | NOT_DEMONSTRATED |
| CODEPOINT_GRAPHEME_SPLIT | DEMONSTRATED |
| UTF8_OR_PERSISTENCE_CORRUPTION | NOT_OBSERVED |
| LOSS_FROM_TORMENT_AS_A_WHOLE | NOT_DEMONSTRATED |
| NATURAL_PREVALENCE | NOT_MEASURED |

## Provenance

Harness script:

`scripts/deep_echo_fidelity_characterization_v1.py`

SHA-256:

`3D6C3D0544B8D49F574426246BFF76F660FCC1DCE6F446F24C88482F45E8239B`

Raw result:

`outputs/experiments/deep_echo_fidelity_characterization_v1/20260811T072129Z/deep_echo_fidelity_characterization_v1_result.json`

Raw result timestamp:

`2026-08-11T07:21:30.784588+00:00`

SHA-256:

`BFAED6DE59C1D7DF97611A60648D0C1F05C4B9D7C57A5E020326FD139CDA811E`

Preservation note:

`docs/TORMENT_DEEP_ECHO_FIDELITY_CHARACTERIZATION_V1_RESULT_2026_08_11.md`

Final note SHA-256 is recorded in the operator return after this file is written.
It is not embedded here because embedding a file's own final digest changes the
bytes being digested.

## Non-Authorization Boundary

This note does not authorize:

- production behavior changes
- compression threshold changes
- repair of the 200-character transform
- provider replay
- retrieval-competition claims
- natural-prevalence claims
- Experiment #2


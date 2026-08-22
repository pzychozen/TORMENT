# TORMENT Brainvision Phase 13 — Corrected Qualification Instrument Amendment v1.0

## Status

FROZEN CORRECTED PRE-ADMINISTRATION INSTRUMENT AMENDMENT

## Historical-result boundary

The first Phase-13 administration remains permanently recorded as
`FAIL / V1A_QUALIFICATION_FAIL / FAIL_IMPLEMENTATION`. Brainvision v1a remains
`NOT_QUALIFIED`. This amendment neither modifies, replaces, supersedes, nor
re-grades its evidence, grading record, or result document.

## Forensic basis

The correction path is limited to four independently identified defects:

1. Root A was a production lifecycle implementation defect. During restoration
   of an already-active durable lineage, lazy runtime materialization could
   bind its process-local active-clock origin after manager reconstruction.
   Commit `9e1e3642aef08320fe2b366efa3c4dc0d4009e3f` repairs this by retaining a
   runtime-only manager reconstruction epoch for that lineage's first active
   restoration. It does not persist a monotonic origin or alter lifecycle
   durability, replay, watermark, VHE, or projection rules.
2. Root B was an E3 schedule-binding defect: the three contract-B observations
   inherited the global contract-A default despite the frozen contract-B
   lineage requirement.
3. Root C was an instrument-grader applicability defect: metric relations
   resolved nested metric fields before excluding `metrics = null` setup
   records. The same latent defect existed in the unused related relation.
4. Root D was an expected-evidence-shape defect: the two E10 lifecycle
   refusal maps omitted their frozen `durable_committed: false` field.

## Corrected instrument rules

- The three E3 contract-B observations explicitly bind
  `adapter_contract_id = bv13-contract-b`.
- Metric relations ignore only records whose `metrics` value is `null`; every
  metric-bearing mapping must contain the requested metric field, every such
  field must equal the frozen expected value, and at least one must exist.
- E10 suspended and disabled lifecycle refusals remain `MAPPING_EXACT` and now
  explicitly require `durable_committed: false`.
- Validation binds every arm's resolved observation contract to its lineage
  contract, validates all expected failure-map durability shapes, and freezes
  the `45 / 81 / 147 / 228` arm and criterion totals.

## Preserved scientific boundary

This amendment changes no fixture, source sequence, source time, theta value,
semantic event, fault semantic, formal arm, primary criterion, evidence
obligation, grading taxonomy, frozen expected scientific value, or claim
ceiling. The frozen E6 expected active time remains `2_000_000_000`.

Any future Phase-13 administration must use a newly frozen external
authorization artifact and a newly derived administration identity bound to
this corrected instrument revision. Neither artifact is created by this
amendment.

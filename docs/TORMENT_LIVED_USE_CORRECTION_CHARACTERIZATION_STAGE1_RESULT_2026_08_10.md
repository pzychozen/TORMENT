# TORMENT Lived-Use Correction Characterization Stage 1 Result

Date: 2026-08-10
Experiment label: `lived_use_correction_characterization_v1`
Status: `FREEZE_FINDING`

This note preserves the completed provider-free Stage 1 correction-characterization result. It does not authorize production behavior changes, tuning, provider replay, or natural lived-use escalation.

Primary evidence:

- Harness: `scripts/lived_use_correction_characterization_v1.py`
- Evidence JSON: `outputs/lived_use/lived_use_correction_characterization_v1/20260810T_stage1_manual/stage1_evidence.json`
- Entry points used: `POST /agent/ingest` and `POST /agent/query`
- No provider calls were made.

## Stage 1 Outcomes

Arm A - explicit reversal:

- Frozen pair: `My current drink preference is coffee.` -> `My current drink preference is not coffee anymore.`
- Rechecked cosine: `0.9118485451`
- Outcome: `S1_NEW_ROW_SPAWNED / L1_CONFLICT_LINK / C1_CONFLICT_RECORDED_NO_SCORE_EFFECT / R3_STALE_FIRST / P1_RESTART_EQUIVALENT`
- Interpretation: a private conflict was durably recorded, but private retrieval scoring remained neutral.

Arm B-HIGH - non-negating replacement, collapse regime:

- Frozen pair: `My favorite game is Portal 2.` -> `My favorite game is Portal currently.`
- Rechecked cosine: `0.9633285999`
- Outcome: `S2_COLLAPSED_INTO_OLD_ROW / L0_NO_LINK / C0_NO_CONFLICT_RECORDED / R5_ORDER_UNDEFINED / P1_RESTART_EQUIVALENT`
- Interpretation: correction ingest returned the old eid, reinforced the stale row, and did not store the correction summary or embedding as a distinct memory.

Arm B-LOW - non-negating replacement, coexistence regime:

- Frozen pair: `My favorite game is Dark Souls 3.` -> `My favorite game is Microsoft Flight Simulator currently.`
- Rechecked cosine: `0.6701988578`
- Outcome: `S1_NEW_ROW_SPAWNED / L0_NO_LINK / C0_NO_CONFLICT_RECORDED / R2_CORRECTION_FIRST_MARGIN_GT_0.01_COMPONENT_ATTRIBUTED / P1_RESTART_EQUIVALENT`
- Interpretation: both rows were stored; correction ranked first by a small component-attributed margin of about `0.011260`.

## Reachability Boundary

Mechanically demonstrated:

- Controlled supplied summaries can enter the conflict band and create a durable private conflict.
- Controlled supplied summaries can enter the duplicate-collapse band and reinforce an existing row while discarding distinct correction content.
- Controlled low-similarity non-negating replacement can coexist as a separate row.

Not demonstrated:

- Production-shaped semantic-correction reachability.
- Natural lived-use duplicate-collapse reachability for semantic correction.
- A lived-use defect claim based on ordinary production traffic.

Historical calibration remains:

- 113 recoverable A0/A1 natural ingests.
- Natural payload `>=0.88`: observed.
- Natural payload `>=0.92`: not observed in the recoverable corpus.
- Semantic-correction reachability: not demonstrated.

## Architectural Principle

TORMENT governs evidence integrity and availability, not the AI's beliefs or decisions.

The default system should preserve provenance, chronology, corrections, and contradictions without silently deciding what the AI must believe.

The user is presumed sincere by default. A later statement about the user's own state is evidence of change, while the provider remains free to interpret, question, reconcile, ignore, or challenge that evidence.

Historical information should remain historical rather than being destructively replaced merely because it is no longer current.

Any memory mechanism that silently discards, rewrites, merges, or strengthens evidence in a way that changes its semantic meaning should be marked for investigation.

TORMENT is not intended to become an ethical governor, truth-enforcement mechanism, anti-lying layer, or hidden behavioral controller.

## Parked Investigation Candidate

`HIGH_SIMILARITY_CORRECTION_COLLAPSE`

Status: `EVIDENCE_INTEGRITY_INVESTIGATION_CANDIDATE`

Reason: in the controlled `>=0.92` condition, new correction content was discarded while the stale row was reinforced.

Boundary: natural production-shaped semantic-correction reachability has not been demonstrated, so this is not yet a lived-use defect claim.

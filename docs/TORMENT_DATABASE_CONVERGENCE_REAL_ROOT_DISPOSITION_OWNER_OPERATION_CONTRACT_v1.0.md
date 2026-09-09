# TORMENT Database Convergence — Real-Root Disposition Owner Operation Contract v1.0

**Status:** **BLOCKED — NOT RATIFIED.** This is a discovery and blocker record,
not authority to implement or execute an adapter.

**Date:** 2026-09-09
**Start:** `8200974899d77f265c8b817161e238258a822415`
**Corrected core:** `f21c730f-5222-4aa8-9a5f-1c1188456df3`
**Envelope D:** `e4e510131cc341375485605bf1ead86aff684a1ca938e26fdbe221bbf0673ceb`

## Result

```text
CONTRACT_RATIFICATION                = BLOCKED
REAL_ROOT_MUTATION                   = NONE
REAL_ROOT_DISPOSITION_EXECUTED       = NO
REAL_P7_EXECUTED                     = NO
SELECTOR_ACTIVATION                  = NO
PRODUCTION_ADAPTER_IMPLEMENTED       = NO
MANUAL_EXTERNAL_MUTATION             = NO
ROLLBACK_OR_HISTORIC_REACTIVATION    = NO

FROZEN_PLAN_RECORDS                  = 11
CLASS_A_REAL_MUTATION_REQUIRED       = 2
CLASS_B_AUTHORITY_TRANSITION         = 2
CLASS_C_REAL_RECEIPT_ONLY            = 5
CLASS_D_ALREADY_SATISFIED_PRIOR      = 0
CLASS_E_SYNTHETIC_ONLY               = 1
CLASS_F_OTHER_UNRESOLVED             = 1
CLASSIFICATION_TOTAL                 = 11
```

`D = 0` is intentional. For a post-P6/P7 gate, a historical P2 assertion is
not current proof. When a retained external owner and artifact are known, its
contribution is a fresh, owner-authenticated, read-only receipt (C), not a
synthetic no-op. The one core-payload record is E. The collective record is F
because it lacks a uniquely identified owner, artifact set, and state model.

## Evidence and current seam

This review used repository reads and a SQLite `mode=ro` connection only. The
corrected core's `deployment_metadata` is `NATIVE_ACTIVE`; its maintenance
ledger contains four `CUTOVER` events and no
`TORMENT_ROOT_DISPOSITION_EXECUTION_RECEIPT`. The documented selector remains
generation 7 / `CUTOVER_PENDING`.

The existing seam is deliberately synthetic:

```text
RootGeometryDispositionPlanEntry =
  owner_identity + disposition + source_observation_digest

source_observation_digest = SHA-256(
  aggregate external_owner_observation_digest + owner_identity
)

execute_root_disposition_plan
  -> execute_synthetic_root_disposition_plan
  -> SyntheticRootDispositionAdapter.execute(...)
  -> non-empty outcome string
  -> RootDispositionExecutionReceipt
```

The derived digest is not a target locator or individual owner witness.
`RootDispositionOwnerResult` holds no owner actor, source/target state,
operation key, external receipt, or recovery state. Its protocol explicitly
says real external owners are intentionally absent. Synthetic/disposable
adapters therefore do not prove a production operation.

## Classification vocabulary

| Class | Meaning |
| --- | --- |
| A | Real external state mutation required; a narrow owner API, successor state, idempotence, and proof are mandatory. |
| B | Real authority transition required; it must identify every enabled/refused consumer or writer and prohibit dual authority. |
| C | No semantic mutation is permitted, but a fresh, owner-authenticated, read-only receipt is required. |
| D | Completely and independently satisfied before this boundary, with no P7 evidence obligation. |
| E | No external-owner operation exists; proof belongs to qualified native/core evidence. |
| F | Another named unresolved condition prevents a contract. |

## The complete eleven-record audit

All paths are canonical patterns under the selected root, not authority to
read, create, or alter arbitrary data. `CURRENT_SYNTHETIC_OUTCOME` is the same
for every record: an opaque non-empty adapter string, which is not a real
operation or owner receipt. P3 observed/admitted source evidence and P4
normalized core evidence; neither executed an external-owner disposition.

| ID / kind / class | Source scope, owner, artifact | Target scope, owner, expected action | P3 / P4 and blocker |
| --- | --- | --- | --- |
| `bridge_registry` / `RETAIN_DECISION_STATUS_CONFIDENCE_HISTORICAL` / **C** | Workspace `<ws>`; `BridgeRegistry`; `workspaces/<ws>/bridges.json` and `bridge_events.jsonl`. | Same external owner; attest exact retained or absent state, with no decision/status/confidence rewrite. | P3 only aggregate observation; preflight found bridge absent. P4 no bridge operation. `save`, `decide`, `update_confidence`, and `decay` are ordinary live APIs, not retention attestation. |
| `character_active_baseline` / `RECOMPUTE_TARGET_GEOMETRY_BASELINE` / **A BLOCKED** | Private agent `<ws>/<agent>`; `CharacterStore`; `agents/<agent>/character_state.json`. | Same state through an absent Character cutover owner; recompute `distance_to_seed` from qualified target-lane state while retaining seed/history and transition `drift_direction`. | P3 source observation only; P4 did not mutate Character. Existing `measure_drift` needs legacy graph/motif inputs; no native field-level successor law, CAS, target geometry API, or durable receipt exists. Generic `save_state` changes `updated_ts` and can overwrite unrelated fields. |
| `character_drift_history` / `RETAIN_AS_HISTORICAL_GEOMETRY_EPOCH_STATE` / **C** | Private agent; `CharacterStore`; `character_state.json.drift_history`. | Same state; owner-authenticated digest/field-digest attestation that history was not recomputed, relabeled, or truncated. | P3 observed source; P4 did not mutate history. Receipt must not disclose history values and must depend on successful/blocked class-A baseline truth. |
| `character_seed` / `RETAIN` / **C** | Workspace seed `<ws>/<seed>`; `CharacterStore`; `workspaces/<ws>/seeds/<seed>/seed.json`. | Same seed store; attest exact present/absent source digest, no reset, rewrite, or re-embedding. | P3 observed seed source; P4 no seed mutation. `save_seed` is forbidden for this record; aggregate digest reuse is insufficient. |
| `checkpoint_kernel_calibration` / `REINITIALIZE_CALIBRATION_ONLY` / **A BLOCKED** | Private agent; checkpoint persistence owner; `private/checkpoints/checkpoint_<step>.json`, especially `kernel_runtime_context.disp_buffer` and `last_effective_scale`. | Same checkpoint/runtime calibration through an absent narrow cutover owner; use lawful cold-start/warm-up for only calibration fields and preserve all other cognitive state. | P3 structural checkpoint census; P4 no restore/reset. `checkpoint.py` can load/save whole checkpoints and default missing payloads, but has no atomic calibration-only transition, pre-state check, exact replay, or receipt. |
| `conflict_role_affect_identity` / `NO_GEOMETRY_DISPOSITION_REQUIRED` / **C** | Workspace/domain/agent; `ConflictRegistry`, `RoleStore`, affect and identity owners; `conflicts.jsonl`, `roles.json`, `affect_state.json`, `identity.json`, retained anchor/symbol artifacts. | Same owners; per-present-artifact proof that no geometry disposition was attempted. | P3 captures conflict/role/identity unevenly and retains affect/anchor/symbol opaque; P4 no mutation. One synthetic result cannot honestly stand for these distinct owners. |
| `deep_archive_vector_state` / `RETAIN_UNTOUCHED_DISABLED` / **C** | Agent archive/deep lanes; `ArchiveStore` and retained deep owner; `memory_archive/` artifacts; no canonical deep-memory artifact was observed. | Same owners plus qualified profile policy; attest artifact inventory/digests, `deep_memory_enabled=false`, and native archive recall refused. | P3 retained/admitted applicable evidence; P4 no mutation. Do not call ArchiveStore, rebuild indexes, or create a missing deep path. |
| `hivemind_historical_geometry_scores` / `RETAIN_HISTORICALLY` / **F BLOCKED** | Workspace collective/Hivemind tree; owner unresolved among `CollectiveField`, collective policy, and proposal components; retained opaque `collective/` directory. | Unresolved. | P3 reports seven collective directories, not score fields; P4 no operation. The frozen phrase does not identify score-bearing artifacts or readers, so no target digest, receipt, or successor policy can be named. |
| `proposal_registry` / `RETAIN_UNMODIFIED_WITH_FUTURE_CONSUMER_GUARD` / **B BLOCKED** | Domain `<ws>/<domain>`; `ProposalRegistry`; `proposals.jsonl`, `proposal_events.jsonl`, and `ShareProposal.embedding`. | Every proposal consumer in the selected native profile; retain append-only source and refuse vector use unless representation identity matches active lane or retained semantic text is qualifiedly re-embedded. | P3 admitted effective proposal state but vectors lack representation identity; P4 no consumer grant. Public native route refusal does not prove all consumers are fenced; no universal active-lane guard or semantic re-embedding contract is defined. |
| `srg_payload_markers` / `RETAIN_EXACTLY` / **E** | Admitted private/shared memory payloads; qualified native/core object-revision payload evidence, not an external store. | Same core evidence; no post-P6 external disposition action. | P3 admitted scoped payload evidence; P4 closure retains qualified facts. Preflight calls motif/core artifacts scoped core evidence, so an external adapter call would be fictional. |
| `world_trajectory` / `RETAIN` / **B BLOCKED** | Private/shared runtime scopes; legacy `TrajectoryLogger`/`TrajectoryV2Writer` and process-local world owner; `trajectories/`, `trajectories.jsonl`, related external evidence roots. | Same roots under `NativeTrajectoryEvidenceRuntime` plus an absent cutover/quiescence coordinator; retain history and establish exactly one lawful future writer. | P3 layout census only; P4 no handoff. Existing native runtime is a fail-soft writer, not a legacy-writer quiescence, predecessor-tail, ownership-transfer, or partial-recovery protocol. |

The table supplies every required field: `DISPOSITION_ID`, `KIND`,
`SOURCE_SCOPE`, `SOURCE_OWNER`, `SOURCE_ARTIFACT`, `TARGET_SCOPE`,
`TARGET_OWNER`, `EXPECTED_ACTION`, `CURRENT_SYNTHETIC_OUTCOME`, `REASON`, and
the P3/P4 position. Records 2, 5, 8, 9, and 11 independently block
ratification.

## Required future owner-receipt contract

No DTO, schema, adapter, or owner code is authorized here. A later separately
authorized phase must make every real operation/receipt bind:

```text
contract/version and frozen disposition ID
real owner type + owner-instance identity
canonical present/absent source locator(s) and per-artifact digest(s)
owner-level source-freeze or equivalent stable-observation identity
Envelope D, root-completion witness, corrected core ID, and P6 receipt/digest
target scope/owner, operation key, and retry identity
predecessor + successor state digests for A/B, attested state + policy digest for C
owner authority identity, time, outcome, partial/recovery state, and refusal reason
```

The contract must forbid selector mutation, legacy reactivation, rollback,
generic raw SQLite, caller-selected arbitrary paths, and broad whole-store save
operations. A core aggregate receipt may bind validated per-owner receipts; it
cannot replace them.

For A, exact changed and unchanged fields are required. For B, every consumer
or writer and each pre-effect refusal must be named. For C, no owner write is
allowed. For E, the bundle references existing P3/P4/core proof. For F, owner
and state discovery must complete first.

## Idempotence, partial failure, and recovery

1. A later execution starts only after P6 binding and a new owner-level freeze
   or equivalent stable observation. The aggregate P2 digest is not a lock.
2. Its idempotence key derives from envelope, P6 receipt, disposition, target
   owner, artifact digest set, and contract version. Reuse with different
   intent is a conflict; exact replay returns the same verified receipt.
3. A/B verify the exact predecessor before effect. Drift, owner replacement,
   missing target, or policy mismatch refuses before effect.
4. A partial bundle is durable only as partial and can never produce the
   global P7 receipt. Retry may resume only still-valid completed records.
5. There is no post-P6 compensating legacy rollback. Recovery must be a
   separately defined forward operation and cannot mutate the selector.

## P7 reassessment

```text
P7_ALLOWED =
  P6/root-completion binding verifies
  AND selector remains CUTOVER_PENDING until this complete gate passes
  AND all 11 records have verified class-appropriate resolution
  AND every A/B/C record has an owner-authenticated receipt
  AND E references qualified P3/P4/core proof without an adapter call
  AND F count is zero
  AND no partial, stale, conflicting, or synthetic global receipt exists
  AND existing selector authority activates exactly once afterwards

P7_PRECONDITION_REASSESSED = FAIL
P7_REMAINS_BLOCKED         = YES
```

The present `RootDispositionExecutionReceipt` cannot prove this: it lacks
classification, locator, owner receipt, per-artifact state, P6 receipt
binding, predecessor/successor evidence, and recovery state. A future
versioned verifier must reject the legacy synthetic shape for real-root P7
while preserving the immutable P2 table and P3/P4/P5/P6 evidence.

## Disposable-fixture and adversarial requirements

No fixture was created. A later implementation qualification needs a disposable
root, never the production `data/` state, with:

- present and absent bridges, Character state/seed/native geometry fixtures,
  and tests for exact field preservation, stale refusal, and replay;
- multiple checkpoints containing unrelated cognitive state plus interruption
  between owner action and receipt persistence;
- proposal vectors of unknown, matching, and mismatched representation with
  every consumer refusing before effect unless a qualified re-embed is used;
- archive/deep, conflict/role/affect/identity, and trajectory fixtures proving
  no write for C and no dual writer for B;
- a semantic inventory fixture identifying each collective score artifact and
  reader before record 8 can pass; and
- negative tests for synthetic strings, manually assembled receipts, aggregate
  digest substitution, source drift, partial success, premature P7, rollback,
  and historic reactivation.

```text
AGGREGATE_DIGEST_AS_PER_OWNER_PROOF             = REFUSED
NONEMPTY_SYNTHETIC_OUTCOME_AS_SUCCESS           = REFUSED
GENERIC_CHARACTER_OR_CHECKPOINT_SAVE_AS_CUTOVER = REFUSED
PUBLIC_PROPOSAL_REFUSAL_AS_ALL_CONSUMER_PROOF   = REFUSED
UNQUIESCED_DUAL_TRAJECTORY_WRITERS               = REFUSED
OPAQUE_COLLECTIVE_DIRECTORY_AS_SCORE_CONTRACT   = REFUSED
MANUAL_RECEIPT_OR_MANUAL_EXTERNAL_EDIT          = REFUSED
PARTIAL_BUNDLE_AS_P7_AUTHORITY                   = REFUSED
POST_P6_ROLLBACK_OR_HISTORIC_REACTIVATION       = REFUSED
CLAUDE_REVIEW                                   = UNAVAILABLE
```

## Review validation

```text
READ_ONLY_CORE_LEDGER_INSPECTION = PASS
CONTRACT_COMPLETENESS_CHECK      = PASS (all 11 frozen IDs present)
GIT_WHITESPACE_CHECK             = PASS

FOCUSED_PYTEST = ENVIRONMENT_BLOCKED_AT_FIXTURE_SETUP
  attempted files = generalized root binding, full-root disposable rehearsal,
                    Character drift boundary, checkpoint compatibility, and
                    migration runtime readiness
  result          = 7 passed; 59 fixture-based cases could not start
  host cause      = WinError 5 on
                    C:\Users\Notandi\AppData\Local\Temp\pytest-of-Notandi
  interpretation  = no test assertion failure was observed; the blocked cases
                    require a writable disposable pytest base directory
```

## Required next decision

A separate owner-contract phase must resolve records 2, 5, 8, 9, and 11;
approve a versioned real receipt/verifier for records 1, 3, 4, 6, and 7; and
accept the core-proof mapping for record 10. Only after that work is ratified
may another order authorize production adapter implementation, a real
disposition, or P7.

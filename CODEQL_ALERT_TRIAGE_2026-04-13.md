# CodeQL Alert Triage (April 13, 2026)

Scope: alerts listed in the latest maintainer note. Grouped for controlled cleanup.

## Group A — Directly actionable in current branch

These map to files currently present in this checkout.

1. `cognition/pipeline.py` (alert #716: unused import)
   - Action: removed unused imports (`RoutingDecision`, `MemoryContext`) and removed unused exception binding in `except Exception as exc`.
   - Status: fixed in this branch.

2. `cognition/apertures.py` (alerts #720, #722: unused imports)
   - Review result: current file uses all imported symbols in this checkout.
   - Status: no code change applied here yet; re-check against exact CodeQL snapshot/commit if alert remains on `main`.

## Group B — Test-file alerts not present in this checkout

Alerts referenced files that do not exist in the current branch working tree:

- `tests/test_spine_escalation_re...` (#729, #730, #728)
- `tests/test_spine_drift_enforce...` (#727)
- `tests/test_mcp_resource_gating...` (#726, #723)
- `tests/test_query_provenance_al...` (#725)
- `tests/test_memory_presentation...` (#724)
- `tests/test_read_surface_classi...` (#721)
- `tests/test_phase_d_runtime_wir...` (#718)
- `tests/test_aperture_lane_separ...` (#717)
- `tests/test_lane_helpers.py` (#714)

Status: needs branch/commit alignment with the CodeQL run that produced these alerts (likely `main` divergence).

## Group C — Migration constants alert path mismatch

- Alert #690 references `torment_service/migration/constants.py:115`, but that path is not present in this checkout.

Status: unresolved in this branch due to path mismatch; requires locating the corresponding file in the commit scanned by CodeQL.

## Recommended next execution order

1. Re-run CodeQL (or equivalent lint) on this branch to confirm Group A clear.
2. Align with the exact `main` commit SHA from the CodeQL alerts.
3. Apply Group B/C fixes on that aligned branch in small PRs:
   - PR-1: test-only import/unused var cleanup
   - PR-2: module-level import style cleanup
   - PR-3: migration constants usage/retention decision

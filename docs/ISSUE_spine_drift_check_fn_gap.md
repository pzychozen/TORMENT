# Spine `_full_cognition` omits `drift_check_fn`, bypassing live drift enforcement for identity-sensitive cognition

**Status:** RESOLVED — `drift_check_fn` now wired in `_full_cognition()` (2026-04-12)  
**Severity:** Was live Spine-path divergence; now closed  
**Filed:** 2026-04-12  
**Fix:** `spine.py::_full_cognition()` passes `make_live_drift_check(fabric)` to `run_cognition_pipeline()`, mirroring `app.py /cognition/run`. Regression test in `tests/test_spine_drift_enforcement.py`.  
**Related but distinct from:** `lookup_fn` / `ingest_fn` writeback divergence (still parked behind `TORMENT_ARCHIVIST_WRITEBACK=0`; separate ratification needed)

---

## Classification

Live Spine-path divergence: identity-sensitive full-cognition through Spine
currently bypasses drift enforcement because `_full_cognition()` does not wire
`drift_check_fn`, even though the pipeline requests drift checking for
protected identity routes.

This is a **separate, higher-priority issue** from the parked writeback seam.
The `lookup_fn` / `ingest_fn` omissions are gated behind
`TORMENT_ARCHIVIST_WRITEBACK=0` and have no live behavioral effect today.
The `drift_check_fn` omission is live now.

---

## Runtime effect

1. Identity-sensitive input enters Spine via `submit_task()`.
2. Spine routes to `_full_cognition()` (spine.py:917) — either directly
   (always-full ops) or via escalation.
3. `_full_cognition` calls `run_cognition_pipeline()` **without**
   `drift_check_fn` (spine.py:972–977).
4. Router detects identity mode → sets `require_drift_check=True`,
   aperture `APERTURE_PROTECTED`.
5. Reintegration calls `_run_drift_check(task, drift_check_fn=None)`.
6. With `None`, reintegration defaults to `DriftReport(total_drift=0.0)` —
   permanent green zone.
7. Invariant E (`drift_report.requires_block`) is structurally unreachable.

**Contrast:** The `/cognition/run` endpoint (app.py:2187–2210) passes
`drift_check_fn=make_live_drift_check(fabric)`. Invariant E is live there.

---

## Affected entrypoints

All callers that reach `_full_cognition` through `submit_task()`:

- **MCP server** (`mcp_server.py:196`) — all MCP tool calls route here
- **`/spine/submit_task` HTTP endpoint** (`app.py:2277`)
- **Always-full operations:** `cognition_run`, `identity_rewrite`,
  `seed_change`, `collective_policy_change`, `proposal_review`,
  `role_conflict_resolution`, `architecture_review`
- **Escalated fast operations:** `ingest`, `collective_reingest`,
  `query_memory` — when identity keywords, high drift score, or protected
  memory flag triggers escalation

---

## Missing test coverage

No existing test exercises the `drift_check_fn` omission through Spine:

- `test_spine.py` tests escalation mechanics and operation registration but
  never calls `submit_task` with an always-full operation. The one
  identity-content escalation test (line 388) checks `resp.escalated` and
  reason codes, not drift behavior.
- `test_cognition_pipeline.py`, `test_cognition_reintegration.py`,
  `test_acceptance_scenarios.py` all call `run_cognition_pipeline()` directly
  with an explicit `drift_check_fn`. They never go through Spine.
- `test_cognition_reintegration.py:536` (`test_no_drift_fn_when_required_defaults_zero`)
  explicitly tests and asserts that `drift_check_fn=None` produces green zone.
  This is correct defensive behavior for the reintegration layer but means the
  Spine caller's omission is silently absorbed.

---

## Smallest future patch shape

In `spine.py _full_cognition()`, after the `character_fn` definition and
before the `run_cognition_pipeline()` call:

```python
from cognition.drift import make_live_drift_check
drift_check_fn = make_live_drift_check(fabric)
```

Add to the pipeline call:

```python
result = run_cognition_pipeline(
    task=task,
    query_fn=query_fn,
    character_fn=character_fn,
    primary_domains=primary_domains,
    drift_check_fn=drift_check_fn,  # <-- added
)
```

This mirrors exactly what `app.py:2187–2210` does. Leave `ingest_fn` /
`lookup_fn` additions parked until writeback gate ratification.

---

## Recommendation

**Ratify-then-fix, not silent patching.**

This changes live behavior: today's permanent-green becomes real drift
measurement. A character undergoing genuine identity drift can currently write
durable identity-shaping content through Spine without Invariant E ever
intervening. The fix is two lines mirroring an already-proven pattern, but the
behavioral change should be a conscious decision.

Two valid outcomes:

1. **Ratify and patch** — add `drift_check_fn` to `_full_cognition`, closing
   the divergence for drift enforcement while leaving writeback parked.
2. **Document as intentional** — explicitly state that Spine full-cognition is
   a lighter path than `/cognition/run` and does not enforce drift, with
   reasoning for why that's acceptable.

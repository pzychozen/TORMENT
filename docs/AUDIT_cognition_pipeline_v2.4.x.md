# COGNITION PIPELINE AUDIT — v2.4.x

**Status:** Filed 2026-04-12
**Scope:** Pipeline quality, role handoff, reintegration semantics, writeback cleanliness.
**Prerequisite context:** Provenance read-surface stabilization (briefs 1–5) is complete.

---

## 1. Executive conclusion

**The cognition pipeline has one high-risk enforcement gap and is otherwise mostly coherent with a few fixable seams.**

The pipeline structure itself is clean: deterministic single-pass, sequential role execution, explicit reintegration circuit-breaker, well-bounded writeback with a real recursion guard. Role handoff uses a fixed `RoleOutput` contract enforced at the base class. Reintegration is replace-semantics (not chain), which matches the current doctrine even though one doc paragraph implies otherwise.

The **highest-severity issue** is the `drift_check_fn` gap in Spine's `_full_cognition()`. This is a live enforcement bypass: identity-sensitive cognition through Spine (MCP tools, `/spine/submit_task`, escalated operations) runs with drift permanently reading zero, making Invariant E (drift hard-block) structurally unreachable. The companion `lookup_fn`/`ingest_fn` omission is gated behind `TORMENT_ARCHIVIST_WRITEBACK=0` and has no live effect today.

Everything else is lower severity: proposal provenance becomes stale during archivist review, derivation depth never accumulates (all roles emit depth=1), and the Archivist mutates shared proposal objects in-place. These are real seams but none bypass a safety gate.


## 2. Pipeline map

```
Entrypoint
  ├─ app.py /cognition/run  (passes ingest_fn, lookup_fn, drift_check_fn, lane_provider)
  └─ spine.py _full_cognition (passes query_fn, character_fn only — MISSING drift/ingest/lookup)
        │
        ▼
pipeline.py: run_cognition_pipeline()
        │
        ├─1─ router.py: route(task, primary_domains) → RoutingDecision
        │      detect_mode() → identity / strategic / engineering / auto
        │      Sets: roles_to_activate, aperture, require_drift_check, require_skeptic_pass
        │
        ├─2─ apertures.py: build_memory_context(aperture, ...) → MemoryContext
        │      Lane-aware retrieval (private/shared/deep) or legacy single query_fn
        │      Character context (full / seed-only / full+drift by aperture)
        │      _stamp_provenance_type() on all hits (canonical helper)
        │
        ├─3─ Role loop (sequential, immutable order)
        │      interpreter → engineer → skeptic → archivist
        │      Each: role.run(task, memory_context, prior_outputs) → RoleOutput
        │      RoleOutput: summary, findings, recommendations, memory_proposals,
        │                  contradictions (skeptic), confidence, provenance (mandatory)
        │
        ├─4─ reintegration.py: reintegrate(task, routing, role_outputs, memory_context, drift_check_fn)
        │      _merge_findings()       → deduplicated, role-prefixed findings
        │      _detect_dissent()       → opposition pairs + skeptic contradictions
        │      _collect_proposals()    → dedup by proposal_id, prefer archivist version
        │      _run_drift_check()      → DriftReport (or zero-drift default if fn=None)
        │      _apply_governance()     → Invariant B (provenance), Invariant E (drift block)
        │      _build_final_answer()   → concatenated role summaries
        │      → ReintegrationResult
        │
        ├─5─ pipeline.py: _write_back_approved() [only if TORMENT_ARCHIVIST_WRITEBACK=1]
        │      Filter approved proposals, skip archivist-origin re-circulation
        │      Cap at 5 per run
        │      Extract parent EIDs from memory_context
        │      recursion_guard_check() per proposal (Rules A–F, bounded DFS depth 3)
        │      ProvenanceV1.for_cognition_writeback() → source_type=role_output, source_role=archivist_writeback
        │      ingest_fn() call
        │
        └─6─ pipeline.py: _build_response() → JSON result
```

### Key files

| File | Role |
|---|---|
| `cognition/pipeline.py` | Orchestrator: route → aperture → roles → reintegrate → writeback → response |
| `cognition/router.py` | Mode detection + route table (roles, aperture, drift/skeptic flags) |
| `cognition/apertures.py` | Memory context assembly, lane-aware retrieval, provenance stamping |
| `cognition/reintegration.py` | Findings merge, dissent detection, proposal dedup, governance circuit-breaker |
| `cognition/recursion_guard.py` | Bounded-DFS ancestry walk enforcing Rules A–F |
| `cognition/roles/base.py` | RoleBase with mandatory provenance enforcement |
| `cognition/roles/interpreter.py` | Parse task, extract intent |
| `cognition/roles/engineer.py` | Propose implementation |
| `cognition/roles/skeptic.py` | Audit prior roles, flag contradictions |
| `cognition/roles/archivist.py` | Review proposals, governance decisions |
| `cognition/task_models.py` | TaskPacket, RoutingDecision, ReintegrationResult |
| `cognition/drift.py` | `make_live_drift_check()` wrapper |
| `torment_service/spine.py` | `_full_cognition()` — Spine's entry into the pipeline |
| `torment_service/app.py` | `/cognition/run` — HTTP entry into the pipeline |


## 3. Role handoff findings

### What is solid

**Output shape consistency.** All four roles return the same fixed `RoleOutput` dataclass. No ad-hoc variants. The `RoleBase.run()` wrapper at `roles/base.py:50-55` enforces mandatory provenance: if a role's `execute()` forgets it, the wrapper auto-attaches. This is well-designed.

**Execution order is immutable.** `ROLE_EXECUTION_ORDER = ["interpreter", "engineer", "skeptic", "archivist"]` at `roles/__init__.py:23`. No runtime reordering.

**Prior outputs are visible.** Each role receives `prior_outputs: List[RoleOutput]` — the full list of outputs from roles that ran before it. This is explicit, not hidden.

### What is fragile

**Engineer assumes Interpreter has run.** Degrades gracefully (empty prior_outputs → reduced context), but the dependency is implicit, not declared.

**Skeptic expects all prior proposals accessible.** Works because execution order guarantees it, but there's no structural guard — if someone reordered roles, skeptic would silently produce empty contradiction lists.

**Archivist mutates shared proposal objects in-place.** `proposal.approve()` and `proposal.reject()` mutate the same Python objects that reintegration later reads. No defensive copy. Non-idempotent if reintegration were ever called twice on the same `role_outputs`. Low risk today (single-pass pipeline), but a latent fragility.

**Proposal provenance becomes stale during review.** The Archivist updates the `decision` field but does NOT update the proposal's `provenance`. Provenance stays frozen as `source_role=engineer, derivation_depth=1` even after archivist approval/rejection. The review decision lives in a separate `decision` field. This means lineage tracking is incomplete — the archivist's work is invisible to anyone reading just provenance. Writeback itself is unaffected because it checks `decision`, not provenance, and it creates fresh `ProvenanceV1.for_cognition_writeback()` at write time.


## 4. Reintegration findings

### Semantics: replace, not chain

Reintegration uses **replace semantics**. It does not implement chained derivation.

The actual logic:

1. **Collect & dedup by proposal_id** (`reintegration.py:196-219`). When the same `proposal_id` appears from multiple roles (engineer creates, archivist reviews), prefer the archivist's version (last occurrence in execution order).

2. **Merge findings** with role prefixes, deduplicate (`reintegration.py:112-129`).

3. **Detect dissent** via opposition-pair matching + explicit skeptic contradictions (`reintegration.py:149-189`). Both sides preserved, never flattened.

4. **Governance circuit-breaker** (`reintegration.py:222-269`):
   - Invariant B: missing provenance → reject.
   - Invariant E: drift hard-block (`drift_report.requires_block`) → reject all.
   - Respects archivist's prior rejections. Does NOT override archivist approvals except for hard-safety.

5. **Build final answer** by concatenating role summaries.

Reintegration is a **dedup + circuit-breaker pass**, not a synthesis layer. It does not compose outputs, chain derivations, or build on prior proposals.

### What is preserved through reintegration

| Field | Preserved? | Notes |
|---|---|---|
| Role origin | Yes | Role-prefixed in findings, role_outputs list intact |
| Confidence | Yes | Passed through in RoleOutput, not aggregated |
| Verification status | Yes | Skeptic mutations survive (in-place on shared objects) |
| Proposal identity | Yes | proposal_id stable, dedup prefers archivist version |
| Provenance | Yes (stale) | Frozen at creation time, not updated by archivist review |
| Derivation depth | Decorative | All roles emit depth=1; never incremented across pipeline |
| Dissent | Yes | Structured, not collapsed |


## 5. Writeback findings

### 5.1 drift_check_fn gap — CRITICAL, LIVE

**The issue is real, confirmed at source level.** This is the highest-severity finding.

`spine.py:990-995` calls `run_cognition_pipeline()` without `drift_check_fn`. When identity-mode requests reach Spine through `submit_task()`:

1. Router sets `require_drift_check=True` (identity mode).
2. Reintegration calls `_run_drift_check(task, drift_check_fn=None)`.
3. With `None`, reintegration returns `DriftReport(total_drift=0.0)` — permanent green zone.
4. Invariant E (`drift_report.requires_block`) is structurally unreachable.

**Contrast:** The `/cognition/run` endpoint (`app.py:2178,2234`) correctly passes `drift_check_fn=make_live_drift_check(fabric)`. Invariant E is live there.

**Affected callers:** All MCP tool calls, `/spine/submit_task` HTTP endpoint, always-full operations (cognition_run, identity_rewrite, seed_change, collective_policy_change, proposal_review, role_conflict_resolution, architecture_review), and any escalated operations that trigger full cognition.

**Practical risk:** Identity-sensitive operations through Spine can produce proposals and summaries without drift measurement. If `TORMENT_ARCHIVIST_WRITEBACK` were flipped on, those proposals could be written back without the drift safety net. Even with writeback off, the *cognitive output* (final_answer, findings) is produced without identity-drift awareness.

### 5.2 lookup_fn / ingest_fn omission — MEDIUM, gated

`spine.py:990-995` also omits `lookup_fn` and `ingest_fn`. This means even if `TORMENT_ARCHIVIST_WRITEBACK=1`, Spine's path silently produces no writes (`_write_back_approved` returns `[]` when `ingest_fn is None`). The divergence is flagged in a doctrine comment at `spine.py:975-988` but not resolved.

**No live effect today** (gate is off). But creates inconsistent behavior if gate is flipped: `/cognition/run` would write back, Spine would not.

### 5.3 Archivist gate — SOLID

`TORMENT_ARCHIVIST_WRITEBACK` is cleanly gated at `pipeline.py:122`. Default off. Pre-filter rejects archivist-origin proposals to prevent re-circulation. The gate is in one place, not scattered.

### 5.4 Recursion guard — SOLID

`recursion_guard.py:106-253` implements bounded-DFS ancestry walk with clear rules:

| Source type | Admitted? |
|---|---|
| `user_input` | Yes |
| `tool_result` | Yes |
| `memory` | Yes |
| `role_output` | Yes, if `source_role` is non-archivist |
| `collective_echo` | No |
| `derived` | No |
| `gate1_unrecoverable` | No |

Archivist blocking is decisive at any depth (`"archivist" in source_role.lower()`). Migration refusal short-circuits via `admission_refused=True` check. Depth cap is 3. Unknown/malformed provenance → conservative rejection. This is well-implemented.

### 5.5 Provenance production — SOLID

Writeback uses `ProvenanceV1.for_cognition_writeback()` factory at `pipeline.py:289-293`. Sets `source_type=SOURCE_ROLE_OUTPUT`, `source_role="archivist_writeback"`, `write_path=WRITE_COGNITION_WRITEBACK`, includes `parent_eids`. Does not use raw dict construction. Correct.


## 6. Doc vs reality mismatches

| Claim (in docs) | Reality | Severity |
|---|---|---|
| `AGENT_SPINE_OVERVIEW.md` implies depth=2 for derived insight replacing depth=0 user statement | All roles emit depth=1 via `from_role()`. Depth never increments across the pipeline. The scenario described cannot occur in practice. | Low — misleading but not dangerous |
| `DOCTRINE_v2.4.x.md` rule #5 "no provenance, no self-writing" | Enforced at reintegration (Invariant B) and writeback (recursion guard). Holds. | None — accurate |
| `ISSUE_spine_drift_check_fn_gap.md` describes drift bypass | Confirmed exactly as documented. Accurate. | None — correctly flagged |
| Spine doctrine comment (spine.py:975-988) describes writeback divergence | Accurate but not promoted to a doc-level issue. Lives only as a code comment. | Low — should be a companion to the drift issue doc |
| Implicit assumption that reintegration "composes" outputs | Reintegration is dedup + circuit-breaker, not composition. No chained derivation exists. | Low — terminology ambiguity, not a safety issue |


## 7. Highest-value next fix

**The `drift_check_fn` gap.** One fix, one place.

Add `drift_check_fn=make_live_drift_check(fabric)` to the `_full_cognition()` call at `spine.py:990-995`. This mirrors what `app.py:2178,2234` already does. The fix is two lines: one import, one kwarg.

This restores Invariant E (drift hard-block) for all Spine-routed identity-sensitive cognition, which is the primary real-world entry path (MCP tools route through Spine, not through `/cognition/run`).

The `lookup_fn`/`ingest_fn` divergence is a separate, lower-priority decision that should be ratified (Spine intentionally read-only, or mirror `/cognition/run`?) before the writeback gate is flipped. It can wait.

Everything else — stale proposal provenance, decorative derivation depth, in-place mutation — is real technical debt but none of it bypasses a safety gate.

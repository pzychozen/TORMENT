# Checkpoint — Tier 2 Runtime Evidence

**Date:** 2026-05-24
**Status:** Closed / Ratified — PASS
**Cluster:** v0.1 Runtime Envelope — Phase 1 Tier 2 scale-up
**Commit range:** `032aaf8` (telemetry restore, cherry-picked from `ee0f93f`) → this checkpoint

---

## Summary

This checkpoint closes Tier 2 of the long-iteration evidence ladder
specified in `scratch/AGENT_RUNTIME_LONG_ITERATION_TEST_PLAN_DRAFT.md`.
Three Tier 2 runs at 300 iterations × 6 scenarios = 1800 turns each,
covering Batch A (no pack), Batch B (debugging pack), and a Tier 2-depth
pack-composability probe under the research pack. Total: **5,400 turns,
0 aborts, all nine doctrine invariants stable.**

This is the 3× scale-up of Tier 1 (1,200 turns across Batch A + Batch B
at 100 iterations each, closed PASS 2026-05-17). No new failure modes
surfaced at the larger scale. Every invariant scaled linearly with
iteration count. The runtime envelope holds under sustained iteration
pressure across all three pack regimes.

Verdict: **Tier 2 runtime evidence closes PASS. The v0.1 runtime
envelope is operationally proven at 3× scale across no-pack, debugging-
pack, and research-pack (EMPTY_CONTRACT) regimes.**

Tier 3 (1000 iter × 6 = 6000 turns) is **not** triggered. The plan was
explicit: Tier 3 runs only if Tier 2 surfaces a question that requires
more data. Nothing did.

---

## Goal recap

Prove the v0.1 agent runtime (`AgentRunner.run_turn`, 8-phase outer
loop) holds the nine doctrine invariants from
`docs/TORMENT_AGENT_DOCTRINE_v0.1.md` Part 9 across long-iteration
runs, scaled 3× from Tier 1, with telemetry that maps every turn to
invariant compliance. No new architecture, no new tool families, no
harness expansion — pure scale-up.

---

## HEAD lineage and telemetry recovery

Tier 2 surfaced a branch-coupled wrapper compatibility failure on the
first iteration of the first run. The wrapper
(`do_not_touch_torment_test_rig/harness/tier0_smoke.py`, the
parameterized "Option B-clean" wrapper ratified 2026-05-17) drives
`examples/agent_runner_demo.py` as a subprocess with `--provider` and
`--jsonl-out` flags. These flags were added by commit `ee0f93f` ("Add
agent runner JSONL OpenRouter telemetry") on the
`tier0-agent-runtime-telemetry` branch on 2026-05-17, used in-place for
Tier 1 evidence, and then deliberately scoped out of PR #52 (authority-
lane matrix tests) via `b7584d1` ("Remove agent runner demo changes
from authority-lane PR") so the PR could stay focused. The PR landed on
main as squash-merge `624015e`, and the agent_runner_demo telemetry
never made it to main.

When Tier 2 attempted to run against current main, the demo's main-
branch CLI rejected `--provider` and `--jsonl-out` with argparse error
`rc=2`, causing all subprocess invocations to abort immediately.

Recovery: `ee0f93f` was cherry-picked onto main as `032aaf8` ("Add
agent runner JSONL OpenRouter telemetry"). The commit touches only
`examples/agent_runner_demo.py` (+560 / -12) and applied cleanly with
no conflicts. A direct demo smoke probe confirmed:

```
python examples\agent_runner_demo.py --scenario 1 --pack none ^
  --provider openrouter --workspace probe_ws --agent runner ^
  --jsonl-out C:\TORMENT\probe_out.jsonl
```

— ran cleanly, exit 0, Phase 5 effective action `answer`, drift 0.0
stable, review approved. No argparse error, no import failure, no
behavioral regression visible. Tier 2 evidence was then produced
against current main (including all Q2-D + Level 3 + Cluster 5 work),
not against the stale `tier0-agent-runtime-telemetry` branch state.

**HEAD lineage at Tier 2 close (pre-this-checkpoint):**

```
032aaf8  Add agent runner JSONL OpenRouter telemetry  (cherry-pick of ee0f93f)
f599e0e  docs(cluster-5): checkpoint Level 3 ST retrieval smoke
90b0e98  docs(cluster-5/q2): checkpoint Q2-D tool-result doctrine
8733662  feat(spine): suppress auto-canon for tool_result_ingest (Q2-D doctrine)
87b4796  test(external): align inference smoke default URL with TORMENT service
```

---

## Tier 2a — Batch A (no pack)

```
Iterations:       300
Scenarios:        [1, 2, 3, 4, 5, 6]
Provider:         openrouter (google/gemini-2.5-flash)
Pack:             none (bare runner)
Workspace prefix: tier2a_baseline_20260524T121134Z
Rows captured:    1800 / 1800
Aborts:           0
Wall time:        ~1h19min
Verdict:          PASS
```

Invariants:

| # | Invariant | Result | Notes |
|---|---|---|---|
| 1 | Memory not exposed as open search | PASS | |
| 2 | Tool narrowed to single family | PASS | |
| 3 | Drift veto in scenario 3 | PASS | 300/300 fires, min required 75 |
| 4 | Assimilation not model-chosen | PASS | |
| 5 | Reflex without LLM | PASS | 300/300 fires, min required 1 |
| 6 | Governance narrows not widens | PASS | |
| 7 | TOOL mode pre/post | NOT EXERCISED | pack=none → no permitted tool family, no code_exec narrowed rows |
| 8 | Review no re-enter | PASS | |
| 9 | Fallback chain closed | PASS | 600/1800 turns: drift_high=300, tool_narrowing_no_permitted_family=300 |

---

## Tier 2b — Batch B (debugging pack)

```
Iterations:       300
Scenarios:        [1, 2, 3, 4, 5, 6]
Provider:         openrouter (google/gemini-2.5-flash)
Pack:             debugging (DEBUGGING_SESSION_PACK)
Workspace prefix: tier2b_debugging_pack_20260524T133810Z
Rows captured:    1800 / 1800
Aborts:           0
Wall time:        ~1h30min
Verdict:          PASS
```

Invariants:

| # | Invariant | Result | Notes |
|---|---|---|---|
| 1 | Memory not exposed as open search | PASS | |
| 2 | Tool narrowed to single family | PASS | |
| 3 | Drift veto in scenario 3 | PASS | 300/300 fires, min required 75 |
| 4 | Assimilation not model-chosen | PASS | |
| 5 | Reflex without LLM | PASS | 300/300 fires, min required 1 |
| 6 | Governance narrows not widens | PASS | |
| 7 | TOOL mode pre/post | **PASS** | **exercised on 300 scen-6 rows narrowed to code_exec** |
| 8 | Review no re-enter | PASS | |
| 9 | Fallback chain closed | PASS | 300/1800 turns: drift_high=300 (no tool_narrowing because debugging pack permits code_exec) |

The substantive new evidence at this tier: invariant #7 verified at
300/300 code_exec narrowed rows. Every scen-6 turn under the debugging
pack passed all three post-execute claims:

- `execution_outcome.tool_called == True`
- `observability.executor_calls == 1`
- `review_outcome.notes` contains `self_review_required`

No widening of TOOL legality. No silent re-entry. No drift in
post-execute mode behavior.

---

## Tier 2 pack-composability probe — research pack

```
Iterations:       300
Scenarios:        [1, 2, 3, 4, 5, 6]
Provider:         openrouter (google/gemini-2.5-flash)
Pack:             research (RESEARCH_ASSISTANT_PACK)
Workspace prefix: tier2_pack_compose_research_20260524T151456Z
Rows captured:    1800 / 1800
Aborts:           0
Wall time:        ~1h15min
Verdict:          PASS
```

Invariants:

| # | Invariant | Result | Notes |
|---|---|---|---|
| 1 | Memory not exposed as open search | PASS | |
| 2 | Tool narrowed to single family | PASS | |
| 3 | Drift veto in scenario 3 | PASS | 300/300 fires, min required 75 |
| 4 | Assimilation not model-chosen | PASS | |
| 5 | Reflex without LLM | PASS | 300/300 fires, min required 1 |
| 6 | Governance narrows not widens | PASS | |
| 7 | TOOL mode pre/post | NOT EXERCISED | research pack has no tool family (EMPTY_CONTRACT) → no code_exec narrowed rows |
| 8 | Review no re-enter | PASS | |
| 9 | Fallback chain closed | PASS | 600/1800 turns: drift_high=300, tool_narrowing_no_permitted_family=300 |

The discriminating result: **scenario 6 every iteration shows
`mode=tool, eff=defer, llm_calls=0` for 300/300 turns.** The research
pack declares the retrieval contract but has no tool family
(EMPTY_CONTRACT). Under iteration pressure, the runtime:

- never widened legality to invent a tool family;
- never silently downgraded mode away from `tool`;
- never produced a `use_tool` effective action;
- consistently fell back to `defer` via the
  `tool_narrowing_no_permitted_family` reason in the closed fallback set.

This proves the v0.1 proof slice's "declared capability absent, system
still behaves coherently" claim at 300-iteration depth.

---

## Cross-tier scaling — Tier 1 → Tier 2

| Metric | Tier 1a | Tier 2a | Tier 1b | Tier 2b | Scaling |
|---|---|---|---|---|---|
| Total turns | 600 | 1800 | 600 | 1800 | 3.0× clean |
| Drift veto scen 3 | 100/100 | 300/300 | 100/100 | 300/300 | linear, 100% |
| Reflex without LLM scen 3 | 100/100 | 300/300 | 100/100 | 300/300 | linear, 100% |
| Fallback fires total | 200 | 600 | 100 | 300 | linear, exactly 3× |
| `drift_high_regime_veto` fires | 100 | 300 | 100 | 300 | linear |
| `tool_narrowing_no_permitted_family` fires | 100 | 300 | 0 | 0 | pack-dependent, scales linearly within pack |
| code_exec narrowed rows | n/a | n/a | 100 | 300 | linear, all PASS |
| Aborts | 0 | 0 | 0 | 0 | none introduced at 3× |

Every measured metric scaled linearly with iteration count. No new
failure modes, no new abort categories, no new drift between invariant
predicate and observed behavior. The runtime envelope is stable under
3× pressure.

---

## Aggregate Tier 2 set

```
Tier 2a (no pack):                  1800 turns, 0 aborts, PASS
Tier 2b (debugging pack):           1800 turns, 0 aborts, PASS
Tier 2 pack-compose (research):     1800 turns, 0 aborts, PASS

Total turns:                        5,400
Total aborts:                       0
Total wall time:                    ~4h04min
LLM spend (estimated):              well under $10
New failure modes:                  none
Invariant pass rate:                100% on all exercised invariants
Halt conditions triggered:          none
```

---

## Load-bearing findings preserved

1. **Runtime envelope scales cleanly from Tier 1 to Tier 2.** 3× iteration pressure produces no new failure modes, no new abort categories, no widening of legality, no silent use_tool firings.
2. **Drift veto is robust.** 300/300 fires in scenario 3 across all three pack regimes; never fires in low/normal regime; respects the high-regime + `away_seed` precondition.
3. **Reflex-no-LLM behavior is stable.** 300/300 fires across all three regimes; zero LLM calls in reflex turns confirmed.
4. **Debugging pack tool boundary holds.** 300/300 scen-6 rows narrow to code_exec, execute, and emit `self_review_required` — invariant #7 PASS at 3× scale.
5. **EMPTY_CONTRACT is real and stable.** Research pack scenario 6 stays `mode=tool, eff=defer` for 300/300 — no legality widening, no invented tool family.
6. **Fallback chain stays closed.** All fallback effective actions remain in the declared closed set (`governance_review / defer / ask_clarification / no_op`) across all three regimes.
7. **Cherry-pick recovery was valid.** Tier 2 evidence is produced against current main (with all Q2-D + Level 3 + Cluster 5 work), not against the stale `tier0-agent-runtime-telemetry` branch state.

---

## What Tier 2 did NOT test (intentionally deferred)

| Item | Status | Why deferred |
|---|---|---|
| **Batch C — accumulating workspace** | Not run | Wrapper creates fresh workspace per iteration; supporting accumulation requires a wrapper code change. Treated as a separate ratifiable slice. Plan §3 Batch C placement remains valid as a future arc. |
| **Tier 3 — endurance (1000 iter × 6 = 6000 turns)** | Not run | Plan was explicit: "Optional. Recommend only if Tier 2 surfaced a question that requires more data, not by default." Nothing surfaced. Defer unless a specific question emerges. |
| **W6 wrapper denylist** | Not implemented | Per `AGENT_RUNTIME_LONG_ITERATION_TEST_PLAN_DRAFT.md` §1.5, W6 should prevent workspace prefix collisions against an explicit denylist. The wrapper relies on timestamped prefixes (collision risk effectively zero in practice). Implementing the predicate is a separate slice. |
| **Lifecycle telemetry per turn** | Not added | Q2-D + Level 3 already proved lifecycle/tool-result doctrine separately. Adding lifecycle envelope capture to the wrapper before this scale-up would have changed the test harness right before measurement; "one variable at a time" discipline rules. Useful enhancement for a later arc. |
| **ST embedder under runtime** | Not exercised | Tier 2 ran on hash embedder for comparability with Tier 1. Level 3 already proved ST retrieval works for tool-result rows; runtime testing under ST is a separate question. |
| **New tool families beyond `code_exec`** | Not added | Doctrinally blocked per `ROADMAP_v2.4.x.md` §3. Each new tool family would need its own narrowing pass; no proven need beyond `code_exec` yet. |
| **Pack-composability under debugging pack scen 6** | Implicitly covered in Tier 2b | Tier 2b's 300/300 code_exec narrowed rows already demonstrate the pack permits the tool family and the narrowing path closes. The discriminating composability probe is under research pack (covered above). |
| **Track A truthfulness envelope promotion** | Not opened | Brainstorm posture: "framing docs come later." Track A promotion is a separate Phase-0 audit. |
| **Cluster 2 authority gate promotion** | Already promoted on main per `e527562` | Mentioned for completeness; not a Tier 2 concern. |
| **Cluster 4 / Dream / offline reflection** | Not opened | Explicitly deferred per brainstorm. |
| **Multi-agent runtime (v0.2 territory)** | Not opened | Premature without v0.2 framing. |

---

## Ratified decisions (additive to prior checkpoints)

1. **The v0.1 runtime envelope is operationally proven at 3× scale across three pack regimes.** Tier 1 PASS is reinforced and extended by Tier 2 PASS.
2. **The cherry-pick of `ee0f93f` onto main as `032aaf8` is the canonical recovery for branch-coupled wrapper compatibility.** The telemetry-capable demo (`--provider`, `--jsonl-out`) now lives on main and matches what the long-iteration wrapper requires.
3. **The `do_not_touch_torment_test_rig/harness/tier0_smoke.py` parameterized wrapper is operationally proven across Tier 0, Tier 1, and Tier 2.** Reading and running the existing wrapper is doctrinally fine. Editing it is a separate ratifiable slice.
4. **Tier 3 is not triggered automatically.** It runs only on a specific question that Tier 2 evidence cannot answer. None such has been named.

---

## Non-goals preserved through this checkpoint

- No Tier 3 endurance run by default.
- No Batch C accumulating workspace (separate slice if needed).
- No wrapper modifications (W6 denylist, lifecycle telemetry, or otherwise).
- No new tool families beyond `code_exec`.
- No multi-agent runtime work.
- No Cluster 4 lift.
- No autonomy loops, no scheduled tasks, no background sweeps.
- No archivist writeback (`TORMENT_ARCHIVIST_WRITEBACK` stays at 0).
- No promotion of scratch audit/plan drafts to `docs/` as part of this checkpoint (separate slice).

---

## Recommendation: stop here, decide next gate separately

Tier 2 closure is a major evidence win. The disciplined move is to lock
it in and decide the next move with a fresh head. Concretely:

- **Do not** auto-run Tier 3.
- **Do not** auto-promote brainstorm tracks (Track A, Cluster 2 next, etc.).
- **Do not** bundle the scratch audit/plan promotion into this commit.
- **Do not** implement Batch C, W6, or any wrapper enhancement in the same arc.

The next decision should be a separate planning moment. Candidates include:

- A. Promote/update the scratch audit + long-iteration plan drafts into `docs/` with "Closures since draft" sections noting Tier 1 / Q2-D / Level 3 / Tier 2 closures.
- B. Open Track A truthfulness envelope or Cluster 2 authority gate as a fresh Phase-0 audit.
- C. Design Batch C accumulating workspace as a narrow separate slice.
- D. Rest the system after a major evidence close.

---

## References

- Plan: `scratch/AGENT_RUNTIME_LONG_ITERATION_TEST_PLAN_DRAFT.md`
- Audit: `scratch/AGENT_AUTOMATION_NEXT_STEP_AUDIT_DRAFT.md`
- Predecessor checkpoints: `docs/CHECKPOINT_2026-05_Q2D_TOOL_RESULT_DOCTRINE.md`, `docs/CHECKPOINT_2026-05_LEVEL_3_ST_RETRIEVAL.md`
- Doctrine: `docs/TORMENT_AGENT_DOCTRINE_v0.1.md`
- Runtime: `torment_service/agent_loop.py`, `torment_service/action_policy.py`, `torment_service/behavior_packs.py`, `torment_service/thinking_controller.py`
- Demo substrate: `examples/agent_runner_demo.py` (telemetry restored via cherry-pick of `ee0f93f` as `032aaf8`)
- Wrapper: `do_not_touch_torment_test_rig/harness/tier0_smoke.py`
- Tier 2 reports:
  - `scratch/iteration_runs/tier2a_baseline/20260524T121134Z/report.md`
  - `scratch/iteration_runs/tier2b_debugging_pack/20260524T133810Z/report.md`
  - `scratch/iteration_runs/tier2_pack_compose_research/20260524T151456Z/report.md`

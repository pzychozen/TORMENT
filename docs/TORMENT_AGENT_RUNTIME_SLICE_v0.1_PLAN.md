# TORMENT Agent Runtime Slice — v0.1 Implementation Plan

**Status: RATIFIED 2026-04-17.** Two rounds of GPT pressure-test (initial five-fronts audit + revision-2 wording-level review) concluded with explicit sign-off: "This plan is ratifiable." Next artifact is code — implementation begins with M1 on a fresh branch off `v2.4.5`.

**Date:** 2026-04-17
**Precedent:** `docs/TORMENT_AGENT_DOCTRINE_v0.1.md` (ratified 2026-04-17, commit `6fc167f` merged as `8ce3241`, ratification amendment `7afc630`, tagged `v2.4.5`)
**Scope:** The minimum viable runtime slice that proves the doctrine holds under real code.

---

## 1. Objective

Prove the doctrine is real in code, not just on paper. This slice is **not** a shippable agent. It is the smallest implementation that demonstrates:

- The outer runtime loop (phases 1–8) can complete a turn end-to-end, with the runner visibly owning Phases 5–8 rather than delegating them to inner deliberation.
- `thinking_controller` components serve as the inner deliberation scaffold (Phase 2–4), accessed through a **clean seam** — either component-level calls from the runner, or an extracted `deliberate_only()` helper (see S1).
- The Mode→legal-intents contract is enforceable in code.
- Drift in the high regime can veto outward action (the load-bearing math claim).
- An external tool can be policy-gated and narrowed to a single family before the LLM ever sees it.
- A behavior pack exists as a concrete five-object bundle, instantiated directly in code (no registry — that's v0.2).
- At least one internal reflex runs an agent turn with no LLM call.

**Success criterion:** all nine doctrinal invariants (doctrine Part 9) hold under this slice's implementation, each verified by an explicit test or a named code-review step. No invariant is allowed to coast on "architectural review" language alone.

---

## 2. Invariants this slice must preserve

From `docs/TORMENT_AGENT_DOCTRINE_v0.1.md` Part 9. Repeated here so the acceptance checks can map one-to-one.

1. Memory is never exposed as open-ended search to the LLM.
2. The model never receives an open tool-choice menu.
3. Drift in the high regime can veto outward action.
4. Assimilation outcomes are not model-chosen intents.
5. Internal reflexes may run without an LLM call.
6. Governance can narrow legality but never widen it.
7. TOOL mode legality differs pre- and post-execution by declared rule.
8. Review may veto or revise on declared grounds but may not re-enter earlier phases.
9. Fallback chain runs closed, not open.

Each slice component (section 4) maps to at least one invariant it makes concrete. The acceptance checks (section 8) verify each mapping. **No invariant is covered by informal review only — every one of the nine has a named test or named code-audit step.**

---

## 3. Migration tasks (prerequisites)

These are the two soft contradictions the contradiction check found. Both must be resolved **before** the new slice components are built.

### M1 (SC-1) — Move assimilation outcomes out of `choose_action`

**Current problem:** `thinking_controller.py:428-442` emits `PROPOSE_SHARE` and `CREATE_ARCHIVE_NOTE` as primary Phase-4 outputs based on text hints. Doctrine Part 3 classifies both as assimilation outcomes belonging at Phase 7.

**Migration:**
1. Remove the two branches (lines ~428–442) from `choose_action`. The function's declared primary intents become: `ANSWER`, `ASK_CLARIFICATION`, `DEFER`, `USE_TOOL`, `NO_OP`, `GOVERNANCE_REVIEW` only.
2. Move the detection logic into a new Phase 7 dispatch helper (e.g. `agent_loop._assimilation_outcomes(turn_context)`) that runs after execution and emits outcomes based on turn-result state and controller-side signals, never on text hints from user input.
3. `PROPOSE_SHARE` and `CREATE_ARCHIVE_NOTE` in the flat `ActionType` enum are retained; no enum refactor.

**Files touched:**
- `torment_service/thinking_controller.py` — remove branches.
- `torment_service/agent_loop.py` (new) — add Phase 7 dispatcher.

**Risk:** any caller of `think()` that treated `PROPOSE_SHARE`/`CREATE_ARCHIVE_NOTE` as deliberation output will stop seeing them there. Need to grep for callers before landing.

**Acceptance:** after migration, `choose_action` output set excludes the two outcome types; unit test confirms that input containing "please share this proposal" routes via `ANSWER` (default Phase 4), not `PROPOSE_SHARE`.

### M2 (SC-2) — Mode-legality enforcement on `choose_action` output

**Current problem:** `thinking_controller.py:444-448` defaults to `ANSWER` unconditionally when no specific branch matches. Silently violates the Mode→legal-intents table when mode is `TOOL` or `GOVERNED`.

**Migration:**
1. Add a mode-legality check after `choose_action` returns, applied inside the runner (not inside `choose_action` itself, to keep the function pure).
2. The check consults the Mode→legal-intents table (new module: `torment_service/action_policy.py`) and:
   - If the proposed action is legal for the current mode → pass through.
   - If illegal → apply the Part 2.5 fallback chain:
     1. If governance-sensitive → `GOVERNANCE_REVIEW`
     2. Else if `DEFER` or `ASK_CLARIFICATION` is legal for the mode → choose `DEFER` (default) or `ASK_CLARIFICATION` (if ambiguity high)
     3. Else → `NO_OP` with explicit `reason` field populated
3. Emit the fallback application in `ThinkingResult.debug` (or equivalent field on the runner's TurnResult) so downstream observability can see "action was downgraded from X to Y because Z."

**Files touched:**
- `torment_service/action_policy.py` (new) — houses the Mode→legal-intents table + fallback chain.
- `torment_service/agent_loop.py` — calls `action_policy` after `choose_action`.

**Acceptance:** a unit test with `mode=TOOL` and no tool-need-detected input receives `NO_OP` or `DEFER` (per fallback), never `ANSWER`.

---

## 4. Slice components

Five components. Each has a candidate concrete choice and an **explicit scope contract**.

### S1 — Outer-loop runner (single-turn) with clean inner/outer seam

**Picked answer on the seam (resolves GPT pushback #1):**

The runner does **not** wrap `thinking_controller.think()` monolithically. `think()` today runs `frame_task → choose_mode → build_memory_plan → choose_action → review`, which bundles Phases 2, 3, 4, and part of Phase 6 (review) into a single call. Wrapping it black-box would blur the doctrine's inner/outer phase seam.

Instead: **extract a `deliberate_only()` helper** from `thinking_controller` that runs:
```
frame_task → choose_mode → build_memory_plan → choose_action
```
and returns `(TaskFrame, CognitiveModeDecision, MemoryPlan, ActionDecision)` — **no review, no draft, no stance**. Review moves out of the inner deliberation (per doctrine R6.a) and runs at the **close of Phase 6** as a runner-owned sub-gate. `think()` itself is preserved as a backward-compat wrapper so existing callers (if any) aren't broken; the runner never calls it.

**In scope:**
- Entry point: `agent_loop.run_turn(workspace_id, agent_id, observation) -> TurnResult`.
- Phases 1 through 8 executed sequentially with visible runner ownership of 5–8.
- Phase 2 (Frame) and Phase 3 (Aperture) via `deliberate_only()` (inner).
- Phase 4 (Intent) is the `choose_action` output returned from `deliberate_only()`.
- Phase 5 (Action Policy) via new `action_policy` module (S3 scaffolding + S2 drift regime).
- Phase 6 (Execute) dispatches: LLM synthesis OR policy-approved tool call OR no-op, followed by a `review` sub-gate (declared grounds only, no loop-back).
- Phase 7 (Assimilate) calls ingest + the new Phase-7 outcome dispatcher from M1.
- Phase 8 (Stabilize) calls `character.measure_drift` + conditional `gravity_correction`.
- `TurnResult` surfaces mode, memory_plan, action_decision, action_policy_decision, execution_outcome, review_outcome, assimilation_outcomes, drift state after stabilize.

**Out of scope:**
- Multi-turn iteration (runner handles exactly one turn).
- Hivemind coordination (single agent only).
- Cross-agent signaling.
- Behavior pack composition beyond one primary pack (S4).

**Invariants exercised:** 5 (no-LLM reflex turns work), 7 (pre/post TOOL legality differs), 8 (review respected, no loop-back — verified by explicit test), 9 (fallback chain applied).

**Module:** `torment_service/agent_loop.py` (new) + `torment_service/thinking_controller.py` (add `deliberate_only()`).

### S2 — Drift veto path

**Candidate:** high-drift blocks outward tool/action and forces stabilization/defer.

**In scope:**
- Phase 5 Action Policy reads `agent_state.drift_score` via `character.measure_drift` (or cached state, whichever is cheaper).
- If `drift_score >= TORMENT_CHARACTER_CORRECTION_THRESHOLD` (Appendix A high regime, default 0.35):
  - `USE_TOOL` is refused (raised to fallback chain).
  - Any outward assimilation-outcome emission (PROPOSE_SHARE / CREATE_ARCHIVE_NOTE) is suppressed.
  - Primary intent forced to `DEFER` unless `GOVERNANCE_REVIEW` is active.
  - Phase 8 runs `gravity_correction` as it already does today.
- Override: if observation carries `urgency > 0.7` and `governance_sensitive = True`, veto is bypassed; governance review takes precedence.

**Out of scope:**
- Moderate-regime intent promotion (not yet — one regime at a time; moderate regime is a later deliverable).
- Coherence-based vetoes (drift only for this slice).
- Per-pack stabilization program overrides (the pack in S4 uses the default regime; per-pack override is v0.1.x).

**Invariants exercised:** 3 (load-bearing — this is the test), 6 (governance override narrows but doesn't widen), 9 (closed fallback).

**Module:** extends `torment_service/action_policy.py` with drift-regime logic.

### S3 — Narrow tool-policy gate (one action family, stubbed executor)

**Picked answer on sandbox scope (resolves GPT pushback #4c):**

The tool family is `code_exec`, but **the proof slice does NOT include a hardened subprocess sandbox**. A hardened sandbox is implementation weight that obscures the doctrine point. Instead:
- Implementation uses a **minimal adapter** with a well-named contract.
- **Tests use a stub executor** — the adapter is monkeypatched to return a fixed-shape result without actually running subprocess code.
- Hardened subprocess sandboxing is a post-slice increment (section 11).

**In scope:**
- One action family: `code_exec(language='python', scope='sandbox', timeout_seconds=10)` declared in the tool registry.
- Phase 5 narrowing: when `choose_action` returns `USE_TOOL` in mode `TOOL`, `action_policy` checks the active behavior pack's action contract (S4). If the contract permits `code_exec`, the LLM receives **exactly one tool signature** at Phase 6 — no menu, no alternatives. If the contract does not permit any family, `USE_TOOL` is refused and falls through to `DEFER`/`NO_OP`.
- Tool-result provenance: the result is assimilated at Phase 7 as a tool-result memory with `provenance: "tool"` and `tool_family: "code_exec"`.

**Out of scope:**
- Any other tool family (web, file, external API, shell).
- Multi-step tool chains within one turn.
- Hardened subprocess sandboxing (see post-slice increments).
- Real `code_exec` execution in tests — stub only.

**Invariants exercised:** 2 (no open tool menu — LLM sees one signature, verified by test), 7 (pre/post TOOL legality, verified by test), 4 (assimilation outcome path for tool-result memory).

**Module:** `torment_service/action_policy.py` (tool-family narrowing) + `torment_service/tool_registry.py` (new, minimal — declares `code_exec` signature) + a stub executor fixture in tests. **No `tool_sandbox/` subprocess implementation in this slice.**

### S4 — Primary behavior pack (direct instantiation, no registry)

**Picked answer on registry scope (resolves GPT pushback #4a):**

For one pack, there is no need for a registry skeleton. The pack is a **plain Python object / dataclass cluster instantiated directly** at runner construction. No registry API, no pack loading mechanism, no file-format spec. Those belong to v0.2.

**Candidate:** a minimal "debugging-session" pack.

**In scope — all five objects of a v0.1 behavior pack, instantiated as code:**
1. **Aperture recipe** — `MemoryPlan` profile with `retrieve_core=True`, `retrieve_relational=True`, `retrieve_deep=True`, `top_k_by_lane={core: 8, relational: 4, deep: 3}`.
2. **Intent grammar** — the standard Mode→legal-intents table, with one tightening: `PROPOSE_SHARE` as an assimilation outcome is forbidden for this pack (debug state should not cross domains automatically).
3. **Stabilization program** — drift thresholds at the Appendix A defaults (0.15 / 0.35). Override: `high_regime_action` is `DEFER` (not `self_correct` — debugging already is self-correct, so forcing another layer of self-correct is pointless in this pack).
4. **Action contract** — one approved action family: `code_exec` (S3 signature). No others.
5. **Event reflex** — one declared reflex: `on_drift_score_crosses_high_regime → force intent=DEFER at next turn, emit debug-log note`. No LLM call.

**Out of scope:**
- Pack registry / registration API (v0.2).
- Pack file format.
- Overlay system.
- Other packs.

**Invariants exercised:** 4 (assimilation outcomes are controller-decided — pack demonstrates a pack can forbid an outcome class), 9 (fallback-closed behavior when drift goes high).

**Module:** `torment_service/behavior_packs/debugging_session.py` (new — direct dataclass cluster, no `__init__.py` registry).

### S5 — Drift-triggered stabilization reflex (no LLM)

**Rename applied (resolves GPT pushback #2):** "self-correct reflex" → **"stabilization reflex"**. The scoped behavior (forced `IDENTITY_SENSITIVE` mode, forced `DEFER` intent, no LLM call, Phase 8 runs `gravity_correction`) is stabilization, not outward self-correction. The rename matches S4's stabilization program, invariant 5's language, and the doctrine's non-LLM-authority framing.

**Candidate:** drift-threshold reflex that triggers a no-LLM stabilization turn.

**Picked answer on live fabric hookup (resolves GPT pushback #4b):**

The proof slice proves invariant 5 through an **explicit `enter_reflex()` entry point + a synthetic trigger in tests.** The live `fabric.py:2939-2988` drift-check hookup is a separate integration step, **deferred to a post-slice increment** (section 11). Proving the doctrine does not require immediate production blast radius.

**In scope:**
- Entry point: `agent_loop.enter_reflex(workspace_id, agent_id, reason)` — triggers a new turn at Phase 1 with a synthetic observation marked `source_type="reflex"` and `reason` as provided.
- Trigger condition (logic only, not wired to live code): when `character.measure_drift` returns `drift_score >= high_regime_threshold` (default 0.35) and `direction == "away_seed"`, the reflex is eligible. In the slice, the trigger is fired **manually from tests**, not from fabric's drift check.
- The reflex turn runs phases 1–8 with:
  - Mode forced to `IDENTITY_SENSITIVE` (via `choose_mode` reading the synthetic observation's source type).
  - Intent forced to `DEFER` by S4's stabilization program.
  - Phase 6 Execute is a **no-op** — no LLM synthesis, no tool call.
  - Phase 8 Stabilize runs `gravity_correction`.
- The reflex completes a full agent turn with **zero LLM calls** (verified by test).

**Out of scope:**
- Live `fabric.py` hookup — deferred to post-slice.
- Convergence-triggered reflexes.
- Governance-triggered reflexes.
- Motif/phase reflexes.
- Multi-reflex collision handling (only one reflex exists in this slice).

**Invariants exercised:** 5 (the whole point — reflexes run without LLM, verified by test that monkeypatches the LLM client to raise on any call), 3 (drift regime triggers it), 8 (review is not called when synthesis is skipped — verified).

**Module:** extends `torment_service/agent_loop.py` with `enter_reflex` entry. `fabric.py` is NOT modified in this slice.

---

## 5. Dependency order

1. **M1** (SC-1 migration) — unblocks clean deliberation output.
2. **M2** (SC-2 migration) — requires Mode→legal-intents table, which also feeds S3. Build `action_policy.py` scaffold with the table first.
3. **S1** (outer-loop runner + `deliberate_only()` helper) — depends on M1 and M2. Wraps the clean inner deliberation in an outer-owned loop.
4. **S4** (behavior pack instantiated directly) — depends on S1. The pack is instantiated by the runner at construction.
5. **S2** (drift veto) — depends on S1 + S4 (action contract tells the veto what's blockable).
6. **S3** (tool-policy gate) — depends on S1 + S4 + S2 (drift veto precedes tool check).
7. **S5** (stabilization reflex via `enter_reflex`) — depends on S1 + S4. Live fabric hookup deferred.

**No component can skip its dependencies.** If S2 is built before M2, the drift veto can't use mode-legality enforcement and violates invariant 9. If S1 is built as a `think()` monolith wrapper, Phase 5–8 ownership is unclear and S2/S3 have no clean seam to hang off.

No deadlock after GPT's S1 seam fix.

---

## 6. Files expected to change or be created

### New files

- `torment_service/agent_loop.py` — outer-loop runner (S1), reflex entry (S5), Phase 7 outcome dispatcher (M1 target).
- `torment_service/action_policy.py` — Mode→legal-intents table, fallback chain (M2), drift-regime logic (S2), tool-family narrowing (S3).
- `torment_service/tool_registry.py` — minimal; declares the `code_exec` signature (S3). No executor implementation.
- `torment_service/behavior_packs/debugging_session.py` — the one reference pack (S4), plain dataclass cluster.
- `tests/test_agent_loop_smoke.py` — end-to-end smoke test for one turn.
- `tests/test_action_policy_legality.py` — Mode→legal-intents enforcement (invariant 7).
- `tests/test_fallback_chain.py` — Part 2.5 fail-closed behavior (invariant 9).
- `tests/test_drift_veto.py` — high-regime veto blocks USE_TOOL (invariant 3).
- `tests/test_tool_surface_whitelist.py` — internal agent tool surface excludes open memory search (invariant 1).
- `tests/test_governance_narrowing.py` — governance narrows never widens (invariant 6).
- `tests/test_review_no_loopback.py` — review does not re-enter earlier phases (invariant 8).
- `tests/test_tool_narrowing.py` — LLM sees one tool signature, not a menu (invariant 2).
- `tests/test_assimilation_outcomes_not_deliberative.py` — outcomes never emitted from Phase 4 (invariant 4).
- `tests/test_reflex_no_llm.py` — reflex turn completes without calling LLM (invariant 5).

### Modified files

- `torment_service/thinking_controller.py` — `choose_action` branch removal (M1), extract `deliberate_only()` helper (S1). `think()` itself is preserved as backward-compat wrapper.
- `torment_service/thinking_models.py` — possibly a new `ActionPolicyDecision` dataclass.

### Not changed (explicitly preserved)

- `torment_service/mcp_server.py` — secondary external interface per R5.
- `torment_service/memory_kernel.py` — kernel math intact.
- `torment_service/collective_field.py`, `torment_service/collective_policy.py` — hivemind unchanged.
- `torment_service/character.py` — interface unchanged; slice calls existing functions.
- `torment_service/fabric.py` — live reflex hookup deferred to post-slice increment.

---

## 7. Testing strategy

### Unit tests per critical contract

- **`test_action_policy_legality.py`** (invariant 7) — for each mode × each primary intent, assert pre-execution legality matches the doctrine Part 3 table.
- **`test_fallback_chain.py`** (invariant 9) — illegal intent proposals route through the Part 2.5 chain to `GOVERNANCE_REVIEW`/`DEFER`/`ASK_CLARIFICATION`/`NO_OP`-with-reason. Never silently re-legalized.
- **`test_drift_veto.py`** (invariant 3) — with `drift_score >= 0.35` and `direction == "away_seed"`, `USE_TOOL` is refused even when `frame.tool_need = True` and mode is `TOOL`. Outward assimilation outcomes suppressed.
- **`test_tool_narrowing.py`** (invariant 2) — when pack contract permits only `code_exec`, Phase 6 LLM call receives exactly one tool signature. With no permitted family, `USE_TOOL` falls through.
- **`test_assimilation_outcomes_not_deliberative.py`** (invariant 4) — input "please share this proposal" does not cause `choose_action` to return `PROPOSE_SHARE`; if share is warranted, it fires in Phase 7 instead.

### New tests added per GPT pressure-test (invariants 1, 6, 8)

- **`test_tool_surface_whitelist.py`** (invariant 1) — asserts the internal agent's LLM-visible tool surface:
  - Does NOT expose `torment_query_memory(query: str)` or any open-ended memory search primitive.
  - If any LLM-visible tool's name matches a memory-adjacency pattern, it must be one of the declared closed primitives (`trace`, `deepen`, `conflict_check`, `continuity_expand`).
  - A blacklist assertion covers known-forbidden names (`search_memory`, `fetch_memory_by_id`, `recall`, `torment_query_memory`).
- **`test_governance_narrowing.py`** (invariant 6) — given a governance-sensitive input whose non-governance proposed action would be `ANSWER` or `USE_TOOL`, the final action must narrow to `GOVERNANCE_REVIEW`, `DEFER`, or `NO_OP`. Never a more permissive outcome.
- **`test_review_no_loopback.py`** (invariant 8) — monkeypatches `frame_task`, `choose_mode`, `build_memory_plan`, `choose_action` with call counters. Runs `run_turn` including a review-escalation scenario. Each Phase 2–4 function is called exactly once per turn. Review can veto, revise, or pass through — but it cannot cause re-entry.

### Smoke test

- **`test_agent_loop_smoke.py`** — one turn end-to-end with debugging-session pack active, normal user input, mode FAST or REFLECTIVE. Assert all 8 phases execute, `TurnResult` populated, no exception.

### Reflex test

- **`test_reflex_no_llm.py`** (invariant 5) — monkey-patch the LLM client to raise on any call. Fire `enter_reflex(..., reason="drift_high")`. Assert the reflex turn completes without raising and `TurnResult` reflects no_llm_call=True.

### Invariant scorecard (every invariant has a named test)

| Invariant | Test(s) that exercise it |
|-----------|--------------------------|
| 1 | `test_tool_surface_whitelist.py` |
| 2 | `test_tool_narrowing.py` |
| 3 | `test_drift_veto.py` |
| 4 | `test_assimilation_outcomes_not_deliberative.py` |
| 5 | `test_reflex_no_llm.py` |
| 6 | `test_governance_narrowing.py` |
| 7 | `test_action_policy_legality.py` |
| 8 | `test_review_no_loopback.py` |
| 9 | `test_fallback_chain.py` |

**No invariant coasts on informal review.**

---

## 8. Acceptance checks (the ratification test for the slice)

The slice is complete when **every box below is green**:

- [ ] M1 committed: `choose_action` no longer emits `PROPOSE_SHARE` or `CREATE_ARCHIVE_NOTE`; Phase 7 dispatcher emits them instead.
- [ ] M2 committed: `choose_action` output is mode-legality-checked in the runner; illegal proposals flow through Part 2.5 fallback chain.
- [ ] S1 committed: `agent_loop.run_turn` executes all 8 phases end-to-end via `deliberate_only()` + runner-owned Phase 5–8; smoke test passes.
- [ ] S2 committed: `drift_score >= 0.35` with `away_seed` direction vetoes `USE_TOOL` and suppresses outward assimilation outcomes; test passes.
- [ ] S3 committed: `code_exec` is the single approved tool family; LLM receives exactly one tool signature when `USE_TOOL` is admitted; test passes with stub executor.
- [ ] S4 committed: debugging-session pack is instantiable with all five objects directly in code; pack's intent-grammar tightening (forbid `PROPOSE_SHARE`) holds.
- [ ] S5 committed: `enter_reflex(..., reason="drift_high")` runs a full agent turn with zero LLM calls; test passes.
- [ ] All 9 invariants have a named test passing (section 7 table).
- [ ] `mcp_server.py` is unchanged (R5 unbroken — the slice does not dogfood MCP).
- [ ] `memory_kernel.py`, `collective_field.py`, `collective_policy.py`, `character.py`, `fabric.py` are unchanged by this slice.
- [ ] Smoke test + all unit tests pass in CI.

When all boxes are green, **v0.1 is proven real**. The next increment builds the deferred items (live fabric hookup, hardened sandbox) + further reflexes/tools/packs — on proven doctrine, not on hope.

---

## 9. What's explicitly NOT in this slice

Each is a valid future deliverable; none belongs in v0.1's proof slice.

- Moderate-drift-regime intent promotion (one regime enforced, not three).
- Multiple tool families (one only).
- Multiple behavior packs (one only).
- Pack overlays.
- **Pack registration API / file format / registry skeleton** (packs instantiated directly in code).
- **Hardened subprocess sandboxing for `code_exec`** (stub executor in tests; minimal adapter in impl; real sandbox is post-slice).
- **Live `fabric.py` hookup for the drift reflex** (reflex proven via `enter_reflex` + synthetic trigger; production wiring is post-slice).
- Convergence / governance / identity / motif-phase reflexes (drift-only for now).
- Reflex priority rule (only one reflex exists).
- Multi-turn iteration (single-turn runner).
- Hivemind / two-agent signaling (single agent only).
- Parallel-branches-of-one-brain (v0.2).
- Subagent / delegation (no `DELEGATE` ActionType).
- Evaluation framework (post-slice).
- Live/personal layer integration (v0.2).
- Continuity expansion primitives beyond declared set (v0.2).

---

## 10. Estimated volume

Not a plan commitment — rough scale:

- Migrations (M1 + M2): ~1 day. Small, localized changes.
- S1 outer-loop runner + `deliberate_only()`: ~1.5 days. Seam cleanup is the care cost.
- S2 drift veto: ~0.5 day. Thin layer on `action_policy.py`.
- S3 tool-policy gate + stub executor: ~0.5 day (sandbox deferred = big reduction).
- S4 behavior pack skeleton (direct instantiation): ~0.5 day (no registry = reduction).
- S5 reflex via `enter_reflex`: ~0.5 day (no fabric hookup = reduction).
- Tests: ~2 days spread across components (three new invariant tests add about half a day over revision 1).
- **Total rough order:** 6–7 days of focused implementation work.

Smaller than revision 1's 9-day estimate because GPT's scope-trimming removed real weight (sandbox hardening, registry skeleton, live fabric hook).

---

## 11. Post-slice next steps (not in scope, for orientation)

When v0.1 slice is proven real, the natural next increments are:

- **v0.1.0a — live `fabric.py` drift-reflex hookup.** Wire the existing drift check at `fabric.py:2939-2988` to call `agent_loop.enter_reflex`. Trivial code change; meaningful production behavior change. Worth being its own small increment so blast radius is controlled.
- **v0.1.0b — hardened `code_exec` subprocess sandbox.** Replace the stub executor with a real sandboxed Python subprocess (restricted PATH, no network, bounded memory, timeout enforcement). Substantial implementation weight, but the doctrine is already proven by the time this lands.
- **v0.1.1 — second behavior pack** (e.g. companion, research-assistant) to verify pack composition doesn't drift into spaghetti. May require the registry skeleton depending on how composition is approached.
- **v0.1.2 — second and third reflexes** (convergence, governance) to exercise the reflex priority rule.
- **v0.1.3 — moderate-drift regime** (intent promotion) to complete the three-regime doctrine.
- **v0.1.4 — second tool family** (probably `read_file`, sandboxed, small) to validate family narrowing under multi-family contracts.
- **v0.2 — structural expansions** (pack registration API, subagent/delegation decision, parallel-branches architecture).

Eval framework + live/personal layer integration fit somewhere in the v0.1.x series once the runtime is stable.

---

## Ratification record

**Ratified 2026-04-17** after two rounds of GPT pressure-testing (initial five-fronts audit + revision-2 wording-level review).

All fourteen positions below were accepted:

- [x] Objective (section 1) accepted — proof slice, not product.
- [x] Invariant-to-component mapping (section 2 + section 7 scorecard) accepted as the scorecard; every invariant has a named test.
- [x] M1 and M2 migration scopes accepted.
- [x] S1 seam fix (extract `deliberate_only()`, runner owns Phase 5–8) accepted.
- [x] S2 drift veto scope accepted (high regime only; moderate deferred).
- [x] S3 `code_exec` with stub executor accepted; hardened sandbox explicitly deferred.
- [x] S4 direct pack instantiation accepted; registry explicitly deferred.
- [x] S5 renamed to "stabilization reflex"; `enter_reflex` path accepted; live `fabric.py` hookup explicitly deferred.
- [x] Dependency order (section 5) accepted.
- [x] File-change list (section 6) accepted.
- [x] Testing strategy (section 7) accepted — nine invariant tests + smoke + reflex test.
- [x] Acceptance checks (section 8) accepted as the slice-done gate.
- [x] Not-in-scope list (section 9) accepted — all three GPT-flagged creep items explicitly excluded.
- [x] Post-slice increment sketch (section 11) accepted as orientation.

**Sign-off:**
- GPT (via user, 2026-04-17): *"This plan is ratifiable... Ratify this plan, commit it to `docs/TORMENT_AGENT_RUNTIME_SLICE_v0.1_PLAN.md`, and begin implementation with M1."*
- Claude (revision 2 drafting, 2026-04-17): all four GPT-required tightenings integrated — S1 seam fix via `deliberate_only()`, S5 rename to stabilization reflex, hardened invariant coverage for invariants 1/6/8, scope trimming on registry skeleton / live `fabric.py` hookup / hardened sandbox.

**Deferred to post-slice increments (logged, not blocking):**
- **v0.1.0a** — live `fabric.py` drift-reflex hookup. Wire the existing drift check at `fabric.py:2939-2988` to call `agent_loop.enter_reflex`. Trivial code change, meaningful production behavior change; worth isolating as its own increment.
- **v0.1.0b** — hardened `code_exec` subprocess sandbox. Replaces the stub executor with a real sandboxed Python subprocess (restricted PATH, no network, bounded memory, timeout enforcement).
- **v0.1.1+** — second behavior pack, additional reflexes (convergence, governance), moderate drift regime, second tool family.
- **v0.2** — pack registration API, subagent/delegation decision, parallel-branches-of-one-brain architecture.

**Next artifact:** Implementation. Starts with M1 (SC-1 migration) on a fresh branch off `v2.4.5`, followed by M2 → S1 → S4 → S2 → S3 → S5. Slice is proven when the nine-invariant acceptance scorecard (section 7 table) goes green.

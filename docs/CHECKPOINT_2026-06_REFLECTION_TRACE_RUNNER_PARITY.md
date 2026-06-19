# Checkpoint — Runner-Path ReflectionTrace Parity (Live-Seam Observability)

**CODE-SLICE CHECKPOINT — docs-only record of a landed code slice. No new gate, no authority doctrine,
no registry amendment beyond a single minimal orientation-map pointer.**

**Anchor:** `df6ffce` *feat(cognition): add runner reflection trace parity*. **Date:** 2026-06-19.

**Prior related slices:** `ca40036` *fix(cognition): harden reflection trace immutability* · `69e2c2a`
*docs(cognition): checkpoint reflection trace observability* · `3d0ba1a` *feat(cognition): enrich
ephemeral reflection trace* · `d15d9c5` *feat(cognition): add ephemeral reflection trace*.

---

## 1. What landed

`ReflectionTrace` now exists on **both** cognition paths:

- the backward-compat `think()` path — surfaced via `ThinkingResult.to_dict()` / `/thinking/debug`
  (unchanged from v0.2); and
- the runner-preferred path — `AgentRunner.run_turn()` now attaches a trace to
  **`TurnResult.reflection_trace`**.

The runner trace is an **end-of-turn, observation-only** record, built from already-computed runner
locals **after review** (the Phase-6 sub-gate) and before the `TurnResult` is returned. It uses the
**Phase-5 effective action** (`effective_action = policy_decision.action`), **not** the original
Phase-4 `bundle.action_decision` — so a Phase-5 downgrade (legality fallback, pack intent-tightening,
drift-regime veto, or tool-narrowing) is what the trace observes.

## 2. Validation evidence (Windows-authoritative)

Windows full suite passed before commit; working tree clean after push. Categories exercised:

- focused runner-parity suite (`tests/test_reflection_trace_runner_parity.py`);
- `ReflectionTrace` suite (`tests/test_reflection_trace.py`) — the production non-reentry source scan
  stayed green **without modification**;
- agent-loop smoke (`tests/test_agent_loop_smoke.py`);
- cognition pipeline (`tests/test_cognition_pipeline.py`);
- Gate A regression (`tests/test_gate_a_tests_only_locks_c1_c5.py`);
- full suite.

## 3. Files changed in the slice

- `torment_service/agent_loop.py` — import of `ReflectionTrace` / `build_reflection_trace`; new
  `TurnResult.reflection_trace: Optional[ReflectionTrace] = None` field; the trace is built in
  `run_turn()` and attached **only** to the returned `TurnResult`.
- `tests/test_reflection_trace_runner_parity.py` (new) — locks effective-action semantics, non-reentry
  (no `.reflection_trace` attribute read anywhere in `agent_loop.py`), no `TurnContext` channel, no
  side-effect leakage, and independent per-turn traces.

## 4. What did NOT change

- **`DeliberationBundle`** — unchanged. No trace was added to the bundle; there is no second trace.
- **`TurnContext`** — unchanged. No `reflection_trace` field or channel.
- **`ReflectionTrace` schema** — unchanged. No new fields.
- **`thinking_models.py` / `thinking_controller.py` / `reflection_trace.py`** — unchanged.
- **The non-reentry AST scan** — unchanged. No production read was introduced; construction is a
  constructor keyword, not an attribute read, so the existing scan remains the gate as-is.

## 5. Safety boundaries (held)

- No persistence; no database / schema / storage.
- No prompt / retrieval / `fabric` / writer / output-control / model-visible route. The trace is
  attached only to `TurnResult` and is never read back inside `agent_loop.py`, never placed on
  `TurnContext` / `metadata`, and never passed to `fabric.ingest` / `fabric.query` / `measure_drift` /
  `gravity_correction`, the LLM system-prompt / messages / tools, the tool executor, the execution
  outcome, the response text, or `assimilation_outcomes`.
- No canon / identity writes.
- No Gate B / `gravity_correction` logic.
- Coarse labels / flags / counts / scores only — no raw reasoning, raw input, prompt text, memory
  content, seed text, retrieved context, or raw kernel/SRG values.

## 6. Review

Codex reviewed the design and returned **APPROVE WITH CORRECTIONS**. The corrections are reflected in
the landed slice: (a) the trace tracks the **Phase-5 `effective_action`**, not the Phase-4 bundle
action; and (b) the change is confined to `agent_loop.py` (no `thinking_models.py` change, since
`TurnResult` lives in `agent_loop.py`).

## 7. Direction / next step

ReflectionTrace observability is now covered on **both** the debug path and the runner-preferred path.
It is treated as **closed for now** unless a future, separately-authorized behavior slice naturally
needs it. Database / substrate remains **last**. Any slice crossing persistence, canon/identity,
model-visible cognition, or authority boundaries is a separate, explicitly-authorized step.

---

*Code-slice checkpoint only. Opens no gate, selects no mechanic, amends no registry beyond a single
minimal orientation-map pointer, and changes no authority. Memory may guide context; memory may not
seize authority.*

# TORMENT — Memory-to-Prompt / Live-Caller Architecture Decision Frame v0.1

## 1. Purpose and scope

This is a **paper-only architecture question selector.** Its entire job is to choose the
**single next architecture question** for the memory-to-prompt / live-caller lane — nothing
more. It selects **no** live caller, trigger, endpoint, seam, provider path, AgentRunner
path, schema, mechanism, test, or implementation, and it authorizes **no** wiring. It does
**not** continue the non-Spine provider integration.

It is **NON-AUTHORIZING** and changes no code, no tests, and no manual harnesses.

## 2. Source-review anchor

This frame stands on the filed, source-grounded review
`docs/TORMENT_MEMORY_TO_PROMPT_LIVE_CALLER_SOURCE_REVIEW_AFTER_NON_SPINE_PROVIDER_HANDOFF_v0.1.md`
(inspected edge `7ab2c7b`), which established by source inspection:

- The non-Spine provider lane is **CLOSED / HOLD / manual-only**: `non_spine_llm_runtime.py`
  and the three manual harnesses are imported only by `tests/` + `tests/manual/` — no
  production caller.
- `app.py` / `mcp_server.py` / `character.py` carry **zero** `AgentRunner` / `run_turn` /
  non-Spine references; the provider-name strings in `agent_loop.py` / `tool_registry.py`
  are documentation-only.
- **AgentRunner / Terrain B remains HOLD and disjoint** (`fabric.py:684` is a comment, not
  wiring).
- **Spine / cognition remains deterministic and model-boundary-free** (`spine.py` has no
  model/provider reference; cognition's only "provider" is the retrieval `LaneQueryProvider`).
- **`/retrieve` remains read-only context-source terrain** (`assemble_context` →
  `AssembledContext` / `ContextBlock`; no write/persist in `retrieval_assembler.py`).
- No output-control / write / persistence / transcript / model-output-to-memory feedback /
  identity / canon / automatic-provider-call / live-wiring path exists.
- The three ownership regions (context-source / generation / non-Spine) are **disjoint**;
  candidate questions were identified but **no mechanism was selected**.

## 3. Lane distinction: provider lane vs memory-to-prompt / live-caller lane

These are two different lanes and this frame belongs only to the second:

- **Non-Spine provider lane (CLOSED / HOLD this phase):** "can a separate off-Spine runtime
  reach a real provider under explicit, gated, operator-only, fail-closed conditions?" That
  question is answered and handed off
  (`docs/TORMENT_NON_SPINE_LLM_CHARACTER_PROVIDER_HANDOFF_v0.1.md`). This frame does **not**
  reopen or extend it.
- **Memory-to-prompt / live-caller lane (this frame):** "*who* may combine governed memory
  context with generation, on *what* boundary, under *what* contract — without touching the
  live app/server/MCP/Spine/character production paths?" This lane is about ownership and
  admissibility of a same-turn context→generation combination, not about provider plumbing.

The lanes only share vocabulary; the disjointness in §2 is exactly why the second lane is its
own question.

## 4. Current closed / HOLD boundaries (restated, unchanged)

- **AgentRunner / Terrain B remains HOLD.** No live caller; the `memory_context_text` seam
  stays dormant.
- **Spine / cognition remains deterministic and model-boundary-free.** Not a candidate
  generation boundary for this lane unless a separate, future decision says otherwise.
- **`/retrieve` and retrieval/assembly remain read-only context-source terrain.** They
  produce candidate context blocks; they do not generate and do not write.
- **The non-Spine runtime stays dormant / manual-only**, default fake, real adapter
  gated/operator-only, no automatic provider call.

## 5. Candidate next questions (enumerated; NONE is a mechanism, and only one is selected)

- **C-A (boundary question):** Which generation boundary, if any, should ever consume memory
  context — the dormant AgentRunner `memory_context_text` seam (Terrain B), the dormant
  non-Spine runtime, or neither (Spine stays deterministic)?
- **C-B (owner question):** Who is the same-turn owner allowed to assemble governed context
  and hand it to a generation boundary, given that `/retrieve` ownership and generation
  ownership are disjoint today?
- **C-C (contract question):** What governed, source-grounded, fence-preserving admissibility
  contract must such an owner satisfy before any wiring?
- **C-D (surface-shape question):** Should the next decision evaluate a **new explicit
  operator-invoked, non-endpoint orchestration surface** that can combine governed context
  and LLM generation **manually**, while keeping app/server/MCP/Spine/character production
  paths closed?
- **C-E (HOLD):** Decide nothing further this phase and keep the lane parked.

None of C-A…C-E selects a caller, owner, boundary, provider path, schema, or implementation.
They are framings of *what to decide next*, not decisions.

## 6. Selected next question

**Selected: C-D.**

> "Should the next memory-to-prompt/live-caller architecture decision evaluate a new explicit
> operator-invoked, non-endpoint orchestration surface that can combine governed context and
> LLM generation manually, while keeping app/server/MCP/Spine/character production paths
> closed?"

This frame selects **only this question to decide later.** It does **not** answer it. It does
not assert that such a surface should exist, where it would live, what it would call, or how
it would be built. C-A, C-B, and C-C remain live as sub-questions *inside* a future C-D
evaluation; C-E (HOLD) remains the always-available alternative for that future decision.

## 7. Why this question is admissible now

- **It is the smallest evaluable unit that touches no live production path.** An explicit,
  operator-invoked, non-endpoint surface — evaluated on paper — keeps app / server / MCP /
  Spine / character closed by construction, matching the fences the source review verified.
- **It matches the already-proven safe pattern.** The non-Spine provider lane established
  that operator-invoked, off-Spine, manual, fail-closed surfaces can be examined without live
  wiring; C-D asks the analogous question for the context→generation combination, one level
  up, without reopening provider integration.
- **It respects the disjointness finding.** Because `/retrieve` ownership and generation
  ownership are disjoint, the honest next question is precisely *whether to even evaluate* a
  manual surface that could hold both halves — not which existing site to wire.
- **It selects a question, not a mechanism.** Choosing C-D commits nothing: no owner, no
  boundary, no provider, no schema, no code, no test. A future, separately-gated decision
  (with Codex review) would answer C-D and could still land on C-E (HOLD).

## 8. No-go / non-authority footer

Selecting C-D authorizes nothing and builds nothing. Explicitly still forbidden / NOT
selected by this frame:

- **writes** of any kind;
- **persistence / logging / transcripts;**
- **output control** / review steering;
- **model-output-to-memory feedback;**
- **identity / canon mutation;**
- **automatic provider calls;**
- **live wiring** of any caller / trigger / endpoint / seam / provider path / AgentRunner
  path / schema;
- continuation of **non-Spine provider integration;**
- any **test or implementation** slice.

No live caller, trigger, endpoint, seam, provider path, AgentRunner path, schema, mechanism,
test, or implementation is chosen here. AgentRunner / Terrain B stays HOLD; Spine / cognition
stays deterministic and model-boundary-free; `/retrieve` stays read-only context-source
terrain. Any move beyond selecting this question is a separate, separately-gated Hilmir +
Codex decision. §0 of `docs/PROJECT_ORIENTATION_MAP.md` remains the active frontier and wins
on any conflict.

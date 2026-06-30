# TORMENT — Memory-to-Prompt / Live-Caller C-D Bounded Implementation Proposal v0.1

## 1. Purpose and scope

This document proposes, **on paper only**, the narrowest shape a future C-D
operator-orchestration surface *could* take, so a later gate has a concrete, bounded thing to
review. It is **NON-AUTHORIZING**: it builds nothing, authorizes nothing, and creates no code,
tests, or manual harnesses. Any file or test names below are **candidates for a later gate**,
not declarations that they exist or are approved.

## 2. Anchors and current edge

Current pushed edge: `86ff6d6`. This proposal stands on three filed docs and adds no new
source claims:

- `docs/TORMENT_MEMORY_TO_PROMPT_LIVE_CALLER_SOURCE_REVIEW_AFTER_NON_SPINE_PROVIDER_HANDOFF_v0.1.md`
  (topology / disjointness; inspected edge `7ab2c7b`);
- `docs/TORMENT_MEMORY_TO_PROMPT_LIVE_CALLER_ARCHITECTURE_DECISION_FRAME_v0.1.md` (selected
  C-D as the next question);
- `docs/TORMENT_MEMORY_TO_PROMPT_LIVE_CALLER_C_D_OPERATOR_ORCHESTRATION_EVALUATION_v0.1.md`
  (decision **YES** as a future, separately-gated candidate only).

## 3. C-D YES boundary

C-D was evaluated **YES only as a future, separately-gated paper-to-implementation
candidate.** **YES does not authorize building.** This proposal stays at the same level: it
sketches a bounded shape and the proof bars a later gate would impose; it does **not** cross
into authorization. Nothing here may be read as approval to write code or tests.

## 4. Narrowest proposed shape

The smallest shape that fits the C-D constraints, described as a direction only:

- **A single manual, operator-invoked surface** — a module or harness-like surface that a
  human runs deliberately. **Non-endpoint by definition:** never registered into `app.py` /
  `mcp_server.py`, never a route or MCP tool, never scheduled, never autostarted.
- **Inputs are primitive + operator-supplied**, plus *already-produced* read-only context
  (i.e. context the operator already obtained from existing read surfaces) — the surface does
  **not** perform or own retrieval/assembly itself.
- **Generation reuses the existing dormant non-Spine runtime direction:** **default
  fake / no-provider**; any real-provider path requires an **explicit operator flag/env** and
  goes only through the existing gated, fail-closed, operator-constructed adapter. **No
  automatic provider call.**
- **If it can invoke real provider behavior, it is pytest-refusing** (refuses the real path
  when `pytest` is importable), mirroring the proven non-Spine harness posture.
- **Output is returned to the operator's terminal/session only** — one-way, inert, drives no
  branch.

This is one surface doing one thing: let an operator manually combine context they already
hold with a manual generation call, off every production path.

## 5. Candidate file/test shapes for a later gate ONLY

Named purely so a later gate has concrete review targets. **These are candidates, not
authorized, and are not created by this doc:**

- Candidate manual surface: `tests/manual/<c_d_operator_orchestration_surface>.py` (illustrative
  name only).
- Candidate guard tests: `tests/test_<c_d_operator_orchestration_surface>.py` (illustrative
  name only) — source/AST guards plus fake-only behavior tests in the established style
  (import allowlist, forbidden-substring scan, pytest-refusal of the real path, default-fake
  assertions, no-live-wiring scan).

Placing them under `tests/manual/` + `tests/` (never under `torment_service/` production
modules) is itself part of the boundary: the surface stays outside the production package.

## 6. Boundary preservation proof (of the proposed shape)

The proposed shape would preserve every verified closure **by construction**:

- **Separate from app/server/MCP/Spine/character (Obligation 3).** Non-endpoint by definition;
  no `app.py` / `mcp_server.py` registration; no `spine.py` / `cognition/*` / `character.py`
  touch. It lives under `tests/manual/`, outside the production service package, exactly like
  the existing non-Spine harnesses the source review found to have **no production caller**.
- **Does not revive AgentRunner / Terrain B (Obligation 4).** No `AgentRunner.run_turn` caller,
  no import of `agent_loop`, no use of the dormant `memory_context_text` seam. AgentRunner /
  Terrain B stays HOLD / disjoint.
- **No retrieval/assembly authority expansion; `/retrieve` unchanged (Obligation 5).** The
  surface consumes context the operator already holds; it does not call or modify
  `assemble_context`, adds no retrieval path, and changes no `/retrieve` behavior. Retrieval/
  assembly stays read-only context-source terrain.
- **No automatic provider call (Obligation 6).** Default path is fake; the real path is gated
  behind an explicit operator flag/env and the existing fail-closed adapter; tests would use
  fake env + fake SDK only.

## 7. Forbidden behaviors (Obligation 7 + the full no-go set)

The proposed shape would forbid, and a later gate would have to prove the absence of:

- **transcript / log / output files** of any kind, and any stdout capture-to-store;
- **persistence** of prompts, context, or model output;
- **memory-output feedback** — model output never re-enters ingest / `assemble_context` /
  retrieval / writers / memory; the boundary is one-way to the operator;
- **output-control / review / ranking / retry / suppression** branches — output drives no
  decision;
- **identity / canon mutation** — no `character.py` / seed / canon writer touched;
- **hidden finalizer / refusal / identity rewrite** — no covert post-processing; behavior is
  fully visible to the invoking operator.

## 8. Failure conditions forcing HOLD

If, at a later gate, any of the following is true, the gate must fall back to **HOLD** rather
than build:

- the surface cannot be kept non-endpoint (any pull toward `app.py` / `mcp_server.py` /
  route / MCP-tool / scheduler registration);
- it cannot obtain context **without** owning retrieval/assembly or expanding `/retrieve`;
- the real-provider path cannot be kept explicit + gated + fail-closed + pytest-refusing
  (any automatic or default provider call);
- a one-way output boundary cannot be guaranteed (any path from output back to memory /
  retrieval / writers / review-control);
- it cannot be proven free of writes / persistence / logs / transcripts / output files;
- it would require touching any forbidden production surface, AgentRunner, Spine, or schema;
- the guards needed to prove the above cannot be expressed as tests/AST checks.

Any one of these forces HOLD; none is resolved here.

## 9. Later-gate recommendation

If a later gate is ever opened (separately authorized by Hilmir + Codex), the cleaner first
step is likely **tests-first / characterization-first before any production-shaped surface**:
land the source/AST guards and fake-only behavior expectations that pin the boundary
(non-endpoint, default-fake, pytest-refusing, no-wiring, no-writes, one-way output) **before**
writing the surface itself — so the guardrails exist before the thing they guard. Given the
number of fences C-D must hold, treat **tests-only first as the probable preferred path**.
This is a recommendation for a future gate, not an authorization to start it.

## 10. No-go / non-authority footer

This proposal authorizes nothing and builds nothing. It selects no production caller, trigger,
endpoint, seam, provider path, AgentRunner path, schema, or wiring; it creates no file and no
test; the candidate names in §5 are illustrative review targets for a later gate, **not
approved artifacts.** Still forbidden / NOT done: writes; persistence / logging / transcripts /
output files; output control; model-output-to-memory feedback; identity / canon mutation;
automatic provider calls; live wiring; non-Spine provider-integration continuation; and any
actual test or implementation slice. The non-Spine provider lane stays CLOSED / HOLD /
manual-only; AgentRunner / Terrain B stays HOLD / disjoint; Spine / cognition stays
deterministic and model-boundary-free; `/retrieve` and retrieval/assembly stay read-only
context-source terrain. Any move beyond this paper proposal is a separate, separately-gated
Hilmir + Codex decision, with Codex review before any code or test. §0 of
`docs/PROJECT_ORIENTATION_MAP.md` remains the active frontier and wins on any conflict.

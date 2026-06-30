# TORMENT — Memory-to-Prompt / Live-Caller Source Review After Non-Spine Provider Handoff v0.1

## 1. Purpose and scope

After the non-Spine provider lane was handed off and put on HOLD, the source topology
changed: a separate non-Spine runtime, a real (gated) Anthropic adapter, a manual Anthropic
harness, and a manual character-shaped harness now exist. **This document is a source-only
inventory/review** of the actual topology at the current pushed edge (`7ab2c7b`), so that the
*next* memory-to-prompt / live-caller architecture decision starts from verified facts
rather than memory.

It is **not** a decision frame, **not** provider integration, **not** a harness extension,
**not** production wiring, and **not** a test slice. It changes no code, no tests, and no
manual harnesses. Every claim below is grounded in a named source surface (`file:line`).

## 2. Source surfaces inspected

Read-only inspection (Grep/Read) of:

- `torment_service/non_spine_llm_runtime.py` (the dormant non-Spine runtime).
- `tests/manual/non_spine_llm_{anthropic_provider,character_operator,callable_adapter}_harness.py`
  and their test guards under `tests/`.
- `torment_service/app.py`, `torment_service/mcp_server.py`, `torment_service/spine.py`,
  `torment_service/character.py`.
- `torment_service/agent_loop.py` (AgentRunner / Terrain B), `torment_service/tool_registry.py`.
- `torment_service/retrieval_assembler.py` (`assemble_context`).
- `torment_service/memory_context_orchestrator.py` (dormant orchestrator).
- `cognition/*.py` (deterministic pipeline) — `pipeline.py`, `apertures.py`.
- Existing characterization locks: `tests/test_spine_cognition_memory_context_characterization_lock.py`,
  `tests/test_audit_live_owner_candidate_inventory.py`.

## 3. Current topology map

Three ownership regions exist and **do not meet** in any live production path:

- **Context-source region (live, read-only):** `/retrieve` → `store.retrieve(...)` →
  `assemble_context(...)` produces `AssembledContext` / `ContextBlock` objects. This region
  owns *candidate context material*; it does not generate and does not write.
- **Authoritative generation region (Terrain B, HOLD):** `AgentRunner` in
  `torment_service/agent_loop.py` owns `run_turn` / `_execute` / prompt build + model
  completion, including the **dormant** `memory_context_text` seam. It is not wired into the
  live app/server/MCP surface.
- **Separate non-Spine runtime region (dormant / manual-only):**
  `torment_service/non_spine_llm_runtime.py` with a fake default path and a gated,
  operator-constructed Anthropic adapter; reachable only from tests and manual harnesses.

The live deterministic Spine/cognition path is a fourth, separate region with **no model
boundary** at all.

## 4. Live caller inventory

What actually runs on the app/server/MCP surface:

- **`/retrieve` (live):** `torment_service/app.py:1341` `@app.post("/retrieve")` →
  `retrieve_assembled(...)`; imports `assemble_context` at `app.py:1319`; calls
  `store.retrieve(...)` (`app.py:1278`, `1366`) and `assemble_context(...)` (`app.py:1449`);
  `/retrieve/profiles` at `app.py:1524`. **Output is assembled context blocks** — a context
  *source*, not a generation step.
- **Spine/cognition (live, deterministic):** `cognition/pipeline.py` + `cognition/apertures.py`
  route via `LaneQueryProvider` / `build_memory_context`. The only token matching "provider"
  here is `LaneQueryProvider` (a *retrieval* lane provider), not a model/LLM provider.
- **No live caller reaches the non-Spine runtime or the AgentRunner generation path.**
  `torment_service/app.py` has **0** references to `AgentRunner`, `run_turn`, or
  `non_spine_llm`/`NonSpineLLM`. `torment_service/mcp_server.py` has **0** references to
  `non_spine` / `NonSpine` / `AgentRunner` / `run_turn`. `torment_service/character.py` has
  **0** references to `non_spine` / `NonSpine` / `AgentRunner` / `run_turn` / `anthropic`.

## 5. Dormant / manual-only inventory

- **Non-Spine runtime is manual-only.** Every importer of
  `torment_service.non_spine_llm_runtime` is a test or manual harness
  (`tests/manual/non_spine_llm_*_harness.py`, `tests/test_non_spine_llm_*`); the only
  non-test reference is the module itself. **No production module imports it.**
- **Fake default / gated real adapter** (`non_spine_llm_runtime.py`):
  `FakeNonSpineLLMProviderAdapter` (`:206`) returns `_FAKE_RESPONSE_TEXT` (`:194`) with
  `provider_called=False` / `is_fake=True` (`:215`–`:216`); `NonSpineLLMRuntime` (`:300`)
  defaults to the fake path; `AnthropicNonSpineLLMProviderAdapter` (`:415`) is a separate
  class gated on `TORMENT_NON_SPINE_LLM_REAL_PROVIDER` (`GATE_ENV`, `:441`) and is
  operator-constructed only; `run_non_spine_callable_provider_manual(...)` (`:378`) is a
  manual helper. **No automatic provider call exists.**
- **The three manual harnesses** (`non_spine_llm_anthropic_provider_harness`,
  `non_spine_llm_character_operator_harness`, `non_spine_llm_callable_adapter_harness`) are
  imported **only** by tests and tests/manual — no production caller.
- **`memory_context_orchestrator.py` is dormant.** Its callers are the module itself, the
  `memory_to_prompt_*` manual harnesses, and tests. The lock
  `tests/test_spine_cognition_memory_context_characterization_lock.py:285` asserts
  spine/app/cognition/roles must **not** import it (`agent_loop` excluded).

## 6. Disjoint / HOLD surfaces

- **AgentRunner / Terrain B remains HOLD and disjoint.** `AgentRunner` is **not** referenced
  in `app.py`, `spine.py`, or `mcp_server.py`. The reference in `torment_service/fabric.py:684`
  is a comment ("External consumers (typically an AgentRunner owner) set this"), not an
  instantiation or wiring. Existing locks
  (`tests/test_audit_live_owner_candidate_inventory.py`,
  `tests/test_spine_cognition_memory_context_characterization_lock.py:218`+) pin `run_turn`
  callers to the `agent_loop` reflex self-call plus the dead-end selected-items bridge.
- **Spine stays deterministic and model-boundary-free.** `torment_service/spine.py` has **0**
  matches for `anthropic` / `openai` / `llm_client` / `.complete(` / `httpx` / `requests.` /
  `provider` / `AgentRunner` / `non_spine`. `cognition/*.py` contains no model/provider call;
  the `test_spine_cognition_memory_context_characterization_lock` test enforces this.
- **Provider-name strings in production are documentation only.** `agent_loop.py:256` and
  `:292` mention "Anthropic"/"OpenAI"/"Ollama" as examples of tool-calling/adapter
  conventions; `tool_registry.py:61` notes the "OpenAI/Anthropic tools-array convention."
  These are comments/docstrings — **not** imports of, or calls into, the non-Spine runtime,
  and not live provider calls.

## 7. Boundary preservation findings

Verified still-true at `7ab2c7b`:

- **No output-control path** introduced; the non-Spine result is returned to test/manual
  callers only and drives no review/branch.
- **No write path.** `retrieval_assembler.py` exposes `assemble_context` (`:370`) plus block
  builders and the `AssembledContext`/`ContextBlock` dataclasses (`:77` / `:63`); it has no
  `ingest` / `persist` / `.write(` / `open(` / `jsonl` / `promote` / `reinforce` / `.save`.
  The non-Spine runtime writes nothing.
- **No persistence / logging / transcripts** — the non-Spine runtime stores no provider
  output, transcript, or file; the handoff/receipt evidence is sanitized.
- **No model-output-to-memory feedback** — no path routes non-Spine (or AgentRunner) model
  output back into ingest/retrieval/memory.
- **No identity / canon rewrite** — `character.py` references none of these surfaces.
- **No automatic provider calls** — the only real-provider path is gated + operator-built
  (§5).

## 8. Next architecture question candidates (NOT selected)

The open question is unchanged in shape but now better grounded: the three regions in §3 are
**disjoint** — no live site both owns same-turn memory context (`/retrieve` /
`assemble_context`) **and** owns a generation boundary. Candidate questions, none selected
here:

1. **Which generation boundary** would ever consume memory context — the dormant `AgentRunner`
   `memory_context_text` seam (Terrain B), the dormant non-Spine runtime, or neither
   (Spine stays deterministic)?
2. **Who is the same-turn owner** allowed to assemble context and hand it to that boundary,
   given that `/retrieve` ownership and generation ownership are disjoint today?
3. **What is the admissibility contract** (governed, source-grounded, fence-preserving) for
   such an owner before any wiring?

These are recorded as candidates for a *separate* future architecture frame. **No option is
chosen, no owner is named, no seam is selected, no wiring is proposed.**

## 9. Non-authority / no-mechanics footer

This document authorizes nothing and builds nothing. It selects no caller, owner, seam,
boundary, mechanism, schema, or wiring. All HOLD boundaries stand: production code, live
endpoint / MCP / API / schema, app / server / character production integration, retrieval /
assembly changes, memory writes, persistence / logging / transcripts, model-output-to-memory
feedback, identity / canon rewrite, database / substrate, dream / private-cognition runtime,
AgentRunner / Terrain B, output-control paths, and automatic provider calls. Any next move is
a separate, separately-gated Hilmir + Codex decision. §0 of
`docs/PROJECT_ORIENTATION_MAP.md` remains the active frontier and wins on any conflict.

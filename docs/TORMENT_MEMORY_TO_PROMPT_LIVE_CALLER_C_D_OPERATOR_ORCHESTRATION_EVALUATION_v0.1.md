# TORMENT — Memory-to-Prompt / Live-Caller C-D Operator-Orchestration Evaluation v0.1

## 1. Purpose and scope

This document **evaluates the C-D question** selected by the decision frame and chooses one of
**YES / NO / HOLD** for that question only. It is **paper-only and NON-AUTHORIZING.** It does
**not** choose — and must not be read as choosing — a concrete implementation, file layout,
CLI shape, caller, endpoint, provider path, AgentRunner path, schema, wiring shape, test, or
any production behavior. It changes no code, no tests, and no manual harnesses.

A YES here means only "this is the right *next direction to evaluate toward*, under a future
separate gate" — not "build it."

## 2. Exact C-D question

> "Should the next memory-to-prompt/live-caller architecture decision evaluate a new explicit
> operator-invoked, non-endpoint orchestration surface that can combine governed context and
> LLM generation manually, while keeping app/server/MCP/Spine/character production paths
> closed?"

## 3. Source anchors

- **Source review** `docs/TORMENT_MEMORY_TO_PROMPT_LIVE_CALLER_SOURCE_REVIEW_AFTER_NON_SPINE_PROVIDER_HANDOFF_v0.1.md`
  (inspected edge `7ab2c7b`): established that the non-Spine runtime + manual harnesses are
  imported only by `tests/` + `tests/manual/`; `app.py` / `mcp_server.py` / `character.py`
  carry zero `AgentRunner` / `run_turn` / non-Spine references; `spine.py` + `cognition/*`
  carry no model boundary; `/retrieve` → `assemble_context` is read-only context-source; the
  three ownership regions (context-source / generation / non-Spine) are **disjoint**.
- **Decision frame** `docs/TORMENT_MEMORY_TO_PROMPT_LIVE_CALLER_ARCHITECTURE_DECISION_FRAME_v0.1.md`:
  enumerated C-A…C-E and selected **C-D** as the next architecture question to decide.

This evaluation stands on those two filed docs and adds no new source claims.

## 4. Evaluation criteria

C-D is assessed against four bars, all framed to preserve the verified closures:

- **Closure preservation.** Does evaluating an *explicit operator-invoked, non-endpoint*
  surface keep app / server / MCP / Spine / character production paths closed **by
  construction**? Yes — "non-endpoint" and "operator-invoked" mean no live request path,
  scheduler, or autonomous trigger is implied.
- **Problem fit.** Does it address the actual gap the source review found — the **missing
  same-turn owner** that could hold both governed context and a generation boundary — rather
  than re-litigating provider plumbing? Yes; the disjointness is precisely an ownership gap.
- **Precedent safety.** Does it match an already-proven safe shape? Yes — the non-Spine
  provider lane established that operator-invoked, off-Spine, manual, fail-closed, pytest-
  refusing surfaces can exist dormant without live wiring; C-D asks the analogous question one
  level up (context→generation combination).
- **Evaluation-level containment.** Can it be examined without committing any mechanism? Yes —
  C-D is a *direction*, decomposable later into C-A (boundary) / C-B (owner) / C-C (contract)
  sub-questions under a separate gate.

### Boundary distinction (operator-invoked non-endpoint vs live production wiring)

These are explicitly different and the evaluation depends on the difference:

- **Operator-invoked, non-endpoint orchestration** = a surface a human runs deliberately,
  off the request/MCP/Spine paths, with no registration into `app.py` / `mcp_server.py`, no
  scheduler/autonomy, and no automatic provider call. It is examined here only as a
  *direction*.
- **Live production wiring** = any `app.py` / `mcp_server.py` endpoint, `/retrieve` behavior
  change, Spine/cognition path, `AgentRunner.run_turn` caller, schema, or automatic trigger.
  **None of this is in scope and none is authorized.**

## 5. Hazard evaluation

Each hazard is named with how the C-D *framing* contains it and what a later gate must still
guard. Listing a guard does **not** authorize building it.

- **Accidental endpoint drift** — risk that a "manual surface" quietly acquires an endpoint /
  MCP registration. Contained by the "non-endpoint, operator-invoked" definition; a later gate
  must prove zero `app.py` / `mcp_server.py` registration and zero route/tool decoration.
- **Implicit provider integration** — risk of a new always-on provider path. Contained because
  C-D references the *existing* gated, operator-only non-Spine adapter direction, not a new
  provider; a later gate must prove no new provider integration and **no automatic provider
  call** (default fake; real path gated + explicit).
- **Transcript / log creation** — risk of writing prompts/outputs to disk. A later gate must
  prove no file/transcript/log creation and no stdout capture-to-store.
- **Memory-output feedback** — risk that generated text re-enters ingest / retrieval / memory.
  A later gate must prove a one-way boundary: model output is returned to the operator only and
  never routed to ingest / `assemble_context` / writers.
- **Output-control laundering** — risk that an "audit/observe" surface silently steers review,
  ranking, retries, suppression, or style. A later gate must prove the surface drives no
  branch and influences no review/output/eligibility path.
- **Identity / canon mutation** — risk of writing identity/seed/canon. A later gate must prove
  no `character.py` / seed / canon writer is touched.
- **Hidden finalizer / refusal behavior** — risk of an undisclosed post-processing/refusal
  step. A later gate must prove the path has no hidden finalizer, no covert refusal rewrite,
  and no identity rewrite, with behavior fully visible to the invoking operator.

No hazard is resolved here; they are recorded as the guard surface a future gate would own.

## 6. Decision: YES / NO / HOLD

**Decision: YES** — **but only as a future, separately-gated paper-to-implementation
candidate, not as authorization to build.**

Rationale: C-D is the **smallest bounded architecture direction** that can preserve **all**
verified live-production closures (app / server / MCP / Spine / character / `/retrieve` read-
only / AgentRunner HOLD / no automatic provider call) while still engaging the real open
problem the source review surfaced — the **missing same-turn context→generation owner** under
disjoint ownership. NO would discard the only bounded direction that fits the fences; HOLD
remains valid but is strictly weaker than a constrained YES that commits nothing. The YES is
therefore a **direction selection at evaluation level**, decomposable later into C-A/C-B/C-C
under a separate Hilmir + Codex gate.

## 7. What the decision does NOT authorize

This YES selects a direction to evaluate further. It does **not** choose or authorize: a
concrete implementation, file layout, CLI shape, caller, endpoint, provider path, AgentRunner
path, schema, wiring shape, tests, or any production behavior. It does **not** reopen or
extend the non-Spine provider lane. No surface is designed, named, located, or built.

## 8. Later implementation-gate proof obligations (IF ever opened; not authorized here)

If a future, separately-authorized gate ever proposes such a surface, that gate — not this
doc — would have to prove, before any code:

- **Operator-invoked only:** runs solely by deliberate human invocation; no endpoint / MCP /
  route / tool registration; no scheduler / autonomy / startup trigger; **pytest-refusing**.
- **Production paths stay closed:** no change to `app.py` / `mcp_server.py` / `spine.py` /
  `character.py` / `cognition/*` / `/retrieve` behavior; no `AgentRunner.run_turn` caller;
  Spine stays deterministic and model-boundary-free.
- **Governed context, read-only:** context comes from existing read-only assembly outputs; it
  introduces no new retrieval authority and mutates no assembled context.
- **Generation is explicit + gated:** any LLM call uses the existing gated, operator-only,
  fail-closed adapter direction; **default remains fake; no automatic provider call.**
- **One-way, inert output:** model output returns to the operator only — no writes, no
  persistence / logging / transcripts, no memory-output feedback, no output-control, no
  identity / canon mutation, no hidden finalizer / refusal.
- **Provable + reviewed:** lands with tests + source/AST guards demonstrating the above, under
  Codex review, before any wiring is even discussed.

Meeting these is a **precondition to propose**, not a grant. The surface stays unbuilt until a
separate gate authorizes it.

## 9. No-go / non-authority footer

This evaluation authorizes nothing and builds nothing. Still forbidden / NOT chosen: writes;
persistence / logging / transcripts; output control; model-output-to-memory feedback;
identity / canon mutation; automatic provider calls; live wiring of any caller / trigger /
endpoint / seam / provider path / AgentRunner path / schema; non-Spine provider-integration
continuation; and any test or implementation slice. The non-Spine provider lane stays CLOSED /
HOLD / manual-only; AgentRunner / Terrain B stays HOLD / disjoint; Spine / cognition stays
deterministic and model-boundary-free; `/retrieve` and retrieval/assembly stay read-only
context-source terrain. Any move beyond this evaluation is a separate, separately-gated
Hilmir + Codex decision. §0 of `docs/PROJECT_ORIENTATION_MAP.md` remains the active frontier
and wins on any conflict.

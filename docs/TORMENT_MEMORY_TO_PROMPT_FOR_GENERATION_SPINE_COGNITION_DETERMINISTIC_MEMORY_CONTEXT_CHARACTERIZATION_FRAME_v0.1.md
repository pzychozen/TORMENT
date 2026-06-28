# TORMENT — Memory-to-Prompt-for-Generation Spine Cognition Deterministic Memory Context Characterization Frame v0.1

## 1. Status / non-authorization

**Docs-only / NON-AUTHORIZING / characterization frame / no code / no tests / no wiring /
design HOLD.** This frame characterizes the live source flow and locks invariants ON PAPER. It
writes **no code and no tests**, implements **nothing**, wires **nothing**, makes **no endpoint /
schema / API / public-surface change**, authorizes **no provider runtime**, designs **no model
boundary**, revives **no** AgentRunner and **no** Terrain B, and opens **no** database/substrate
work. Terrain B, AgentRunner live wiring, and any design/architecture move remain **HOLD**. Where
this frame and any parent contract/guard differ, the contract/guard wins.

Standing posture carried verbatim:

> Memory may shape context. Memory may not seize authority.
> Audit observes authority. Audit must not become authority.

Anchor: `db5c61e` (docs(project): close Spine cognition memory-to-prompt evidence).

## 2. Parent finding / why this frame exists

`9384c19` established **Option B**: the live Spine / `cognition.pipeline` path has same-turn
memory/context shaping, but no safe model-visible memory-to-prompt seam, because the path is
deterministic and has no LLM/model/prompt boundary. Before any design/architecture question is
reopened, this frame **locks the source facts** of the deterministic `memory_context` flow.

## 3. Source survey (source-grounded at `db5c61e`)

```text
A. torment_service/spine.py
   - submit_task(...) routes a SpineRequest; _full_cognition(fabric, ctx, req) [L986] is the full
     cognition path. It builds a TaskPacket from SpineRequest (user_input from payload), a query_fn
     wrapping fabric.query(...), a character_fn (drift/seed state), a drift_check_fn, and calls
     run_cognition_pipeline(task, query_fn, character_fn, primary_domains, drift_check_fn) [L1051].
   - INTENTIONALLY READ-ONLY: it passes NO lookup_fn / ingest_fn, so archivist writeback is
     structurally disabled on the Spine path (only /cognition/run can writeback, under an env gate).
   - the Spine does NOT generate itself; it delegates to cognition.pipeline.

B. cognition/pipeline.py — run_cognition_pipeline [L28]
   - exact execution order:
       route(task) → build_memory_context(...) → execute deterministic roles
       (ROLE_REGISTRY / ROLE_EXECUTION_ORDER; role.run(task, memory_context, role_outputs)) →
       reintegrate(...) → result dict.
   - inputs: task, query_fn, character_fn, drift_check_fn, primary_domains, ingest_fn, lookup_fn,
     lane_provider. result fields: ok, task_id, final_answer, merged_findings, dissent,
     memory_effects, drift_report, governance_rejections, role_summaries, routing.
   - NO LLM / model / prompt / provider-client boundary (see §6).

C. cognition/apertures.py — build_memory_context [L199]
   - returns a MemoryContext of private_memories / shared_memories / deep_memories (retrieved memory
     dicts, lane-separated), character_context (dict), drift_snapshot (dict).
   - source: lane_provider (lane-separated retrieval) or query_fn (legacy fabric.query) + character_fn
     + drift_fn; aperture-budgeted via get_config(aperture_name) ("narrow"/"broad"/"protected").
   - it is structured retrieval/context data for roles — NON-MODEL-VISIBLE, advisory/internal.
   - NOTE: the "provider" matches here are `lane_provider` / `LaneQueryProvider` (a RETRIEVAL
     provider), NOT a model/LLM provider.

D. cognition/router.py — route [L155]
   - route(task, primary_domains) → RoutingDecision (aperture + roles_to_activate + flags).
   - deterministic; calls no model / provider / prompt.

E. roles package (roles/) — role registry / role execution
   - ROLE_REGISTRY / ROLE_EXECUTION_ORDER (imported by pipeline from `roles`). Roles (archivist,
     engineer, interpreter, skeptic, base) run via role.run(task, memory_context, role_outputs)
     → RoleOutput.
   - a grep across the WHOLE roles/ package finds NO llm / .complete( / prompt / model / provider
     client / .chat / messages= — roles are DETERMINISTIC. memory_context is treated as advisory
     context, NOT a control signal or write path.

F. cognition/reintegration.py — reintegrate [L43]
   - reintegrate(task, routing, role_outputs, memory_context, drift_check_fn) builds the result;
     final_answer = _build_final_answer(task, role_outputs, dissent) [L94/L334].
   - _build_final_answer DETERMINISTICALLY concatenates role summaries (interpreter/engineer summary,
     skeptic contradiction count, archivist summary, dissent note) into a " | "-joined string. Its
     docstring states: "v0.1: concatenates role summaries. Future versions MAY use LLM synthesis."
     => no model today; LLM synthesis is an explicitly FUTURE (unimplemented) possibility.
   - reintegrate performs no model call, no review/ranking/retry/suppression/style steering of model
     output, and no file/transcript write.

G. torment_service/fabric.py — query/retrieval source only
   - TormentFabric.query(...) returns rescored core hits ("results"); retrieval evidence/context
     only; NO generation; NO model boundary.

H. torment_service/app.py — live endpoints
   - /agent/query, /cognition/run, /spine/submit_task enter the Spine / cognition.pipeline;
     /retrieve (retrieve_assembled) is read-only / context-source and is NOT the live Spine memory
     path. No endpoint/public-surface change is implied by this characterization.

I. torment_service/retrieval_assembler.py
   - assemble_context(...) → AssembledContext.assembled_text is the /retrieve assembler. It is NOT
     imported or called by run_cognition_pipeline (the pipeline uses build_memory_context, a
     DIFFERENT builder). assembled_text is /retrieve-only and EXCLUDED from the live Spine path.

J. Excluded negative terrain
   - agent_loop.py (AgentRunner LLM path), memory_context_orchestrator.py, PrivateGenerationOwner,
     selected-items bridge / audit / private-owner surfaces — EXCLUDED negative terrain only. No
     AgentRunner / Terrain B route on the live path; memory_context_orchestrator is referenced only
     by its own file (no production call).
```

## 4. Invariants locked (ON PAPER)

```text
- Live flow is DETERMINISTIC:
  Spine → run_cognition_pipeline → route → build_memory_context → deterministic roles →
  reintegrate → result dict.
- memory_context is SAME-TURN (built per task inside run_cognition_pipeline).
- memory_context is ADVISORY / INTERNAL / NON-MODEL-VISIBLE (structured retrieval+character+drift
  data consumed by deterministic roles).
- NO LLM / model / provider / prompt boundary exists in the live cognition package or the roles
  package.
- /retrieve and AssembledContext.assembled_text are NOT the live Spine path.
- AgentRunner and Terrain B remain disjoint and HOLD.
- NO output-control / review / suppression / retry / ranking / style steering of model output
  (there is no model output to steer).
- NO write / persistence / logging / transcript on the Spine path (read-only; writeback disabled).
```

## 5. Same-turn memory_context flow

```text
1. endpoint (/agent/query | /cognition/run | /spine/submit_task) → SpineRequest.
2. _full_cognition builds a TaskPacket (user_input from payload) — same turn.
3. query_fn wraps fabric.query(...) (retrieval evidence/context); character_fn loads character
   state; drift_check_fn provides a drift snapshot.
4. build_memory_context(aperture, ..., lane_provider/query_fn, character_fn, drift_fn) → MemoryContext
   (private/shared/deep memory dicts + character_context + drift_snapshot), aperture-budgeted.
5. deterministic roles execute: role.run(task, memory_context, role_outputs) → RoleOutput (no model).
6. reintegrate(...) → result; final_answer = deterministic concatenation of role summaries.
7. result dict (ok, task_id, final_answer, merged_findings, dissent, memory_effects, drift_report,
   governance_rejections, role_summaries, routing) returns to the endpoint.

- Public payload: the result dict is the endpoint response; memory_context itself is INTERNAL
  pipeline data, not a public payload field.
- Persistence/write/log: NONE on the Spine path (writeback structurally disabled; no ingest_fn).
- Model-visible prompt: NONE — no part of this flow reaches a model-visible prompt (none exists).
```

## 6. Absence proofs (source-grounded)

```text
- NO LLM / model / provider-client / prompt boundary in the cognition package: the only matches for
  model-ish tokens in cognition/ are `lane_provider` / `LaneQueryProvider` (a RETRIEVAL provider in
  apertures.py / pipeline.py), not a model provider; no `.complete(` / `.chat` / `messages=` /
  `openai` / `anthropic` / model client exists.
- NO LLM / model / prompt boundary in the roles package: a grep across roles/ finds no such tokens.
- final_answer is DETERMINISTIC: _build_final_answer concatenates role summaries; LLM synthesis is
  an explicitly FUTURE (unimplemented) note in its docstring.
- NO AgentRunner / run_turn in spine.py / cognition / roles (the live path).
- NO production call into memory_context_orchestrator (referenced only by its own file).
- NO retrieval_assembler / AssembledContext.assembled_text in the live Spine flow (the pipeline uses
  build_memory_context).
- NO output-control / review / retry / ranking / suppression / style steering of model output: the
  only gates are governance_rejections + the drift hard-block (Invariant E) — identity/governance
  gates, not model-output steering; reintegrate is deterministic synthesis.
- NO write / persistence / logging / transcript on the Spine path: _full_cognition passes no
  ingest_fn / lookup_fn (writeback disabled); the result is an in-memory dict.
```

## 7. Future tests / guards to name only (not implemented now)

```text
- characterization tests for the flow shape: route → build_memory_context → roles → reintegrate;
- tests / AST guards for the ABSENCE of a model boundary in the cognition AND roles packages;
- guards for no AgentRunner / Terrain B revival;
- guards for /retrieve read-only and NOT on the live Spine path;
- guards for no endpoint / API / public-surface drift;
- guards for no persistence / write / logging / transcripts on the Spine path;
- guards for no output-control / review / suppression / retry / ranking / style steering;
- guards for memory_context being same-turn / advisory / internal / non-model-visible.
```

## 8. Forbidden scope (this step)

```text
- code; tests; wiring; endpoint edits; provider runtime; model-boundary design;
- AgentRunner live wiring; Terrain B runtime; database/substrate work;
- /agent/query retrofit; /retrieve generation; schema/API/public-surface drift;
- persistence/write/logging/transcripts;
- output review/control/suppression/retry/ranking/style steering;
- autonomy/monitoring expansion;
- U1/audit/private-owner/selected-items paths;
- Gate D/dream/Envelope Audit runtime.
```

## 9. Decision / final verdict

**Characterization complete — the source facts of the live deterministic Spine / cognition.pipeline
`memory_context` flow are locked ON PAPER** (§3–§6). The live flow is deterministic
(route → build_memory_context → deterministic roles → reintegrate → result dict); `memory_context`
is same-turn, advisory, internal, and non-model-visible; there is no LLM/model/prompt boundary in
the cognition or roles packages; `final_answer` is a deterministic concatenation (LLM synthesis is a
future, unimplemented note); `/retrieve` / `AssembledContext.assembled_text` are excluded from the
live path; AgentRunner / Terrain B / `memory_context_orchestrator` are disjoint and uncalled.

This is characterization, so it chooses **no implementation**. The recommended next move — **not
code, not implementation, not live wiring** — is one of:

```text
- a tests-only characterization-lock slice (AST/source guards for the deterministic flow + model
  absence + no-revival + read-only Spine path), OR
- a design / architecture frame (whether a model-visible generation boundary — e.g. the FUTURE
  "_build_final_answer LLM synthesis" point — should ever exist in the live path, or whether
  prompt-based memory-to-generation belongs to a separate LLM-bearing path), OR
- HOLD.
```

Terrain B, AgentRunner live wiring, and the design/architecture move remain HOLD.

## 10. Anti-drift footer

TORMENT — MEMORY-TO-PROMPT-FOR-GENERATION SPINE COGNITION DETERMINISTIC MEMORY CONTEXT
CHARACTERIZATION FRAME / DOCS-ONLY / NON-AUTHORIZING / CHARACTERIZATION ONLY / DESIGN HOLD.
Source-grounded at `db5c61e`: the live flow is Spine → `run_cognition_pipeline` → `route` →
`build_memory_context` → deterministic roles → `reintegrate` → result dict; `memory_context`
(private/shared/deep memory dicts + character + drift, aperture-budgeted) is same-turn, advisory,
internal, and non-model-visible; a grep across cognition/ AND roles/ finds no LLM/model/prompt
boundary (the cognition "provider" hits are `lane_provider`, a retrieval provider); `final_answer`
is deterministic concatenation (LLM synthesis is a future, unimplemented note); `/retrieve` /
`AssembledContext.assembled_text` are excluded from the live path; AgentRunner / Terrain B /
`memory_context_orchestrator` are disjoint and uncalled; the Spine path is read-only (no writeback).
**Verdict: characterization complete; invariants locked on paper; next is a tests-only
characterization lock OR a design/architecture frame OR HOLD — not code.** It authorizes no code,
no tests, no wiring, no endpoint/API/schema/public-surface change, no provider runtime, no
model-boundary design, no AgentRunner live wiring, and no Terrain B runtime, all under separate
Hilmir + Codex authorization. Memory remains guidance, not authority; audit observes authority and
does not become authority; nothing rewrites identity / canon / seed / soul.

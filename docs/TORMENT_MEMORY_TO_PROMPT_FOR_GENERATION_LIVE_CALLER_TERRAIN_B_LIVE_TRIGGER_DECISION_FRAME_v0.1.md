# TORMENT — Memory-to-Prompt-for-Generation Live Caller Terrain B Live-Trigger Decision Frame v0.1

## 1. Status / non-authorization

**Docs-only / NON-AUTHORIZING / Terrain B live-trigger decision frame / no code / no tests /
no wiring / HOLD preserved.** This frame writes **no code and no tests**, implements
**nothing**, wires **nothing**, introduces **no runtime behavior**, makes **no endpoint /
schema / API / public-surface change**, does **not** modify `/agent/query` or `/retrieve`,
and authorizes **no provider runtime**, no persistence/write/logging/transcripts, and no
output-control/review/suppression/retry/ranking/style steering. It may survey reachable
live-trigger terrain ON PAPER ONLY, decide whether a later live-trigger proposal/code path is
admissible, conclude HOLD, or define future proof obligations and tests/AST guards ON PAPER
ONLY. HOLD is preserved. Where this frame and any parent contract/guard differ, the
contract/guard wins.

Standing posture carried verbatim:

> Memory may shape context. Memory may not seize authority.
> Audit observes authority. Audit must not become authority.

Anchor: `d9dac36` (docs(project): close Terrain B implementation proposal). Parent state:
`9043540` established only that the internal Terrain B module shape is admissible ON PAPER; it
explicitly left live production reachability / live trigger **unresolved and separately
gated**. No implementation, code, tests, wiring, endpoint behavior, provider runtime, public
surface, or persistence was authorized.

## 2. The exact decision question

> Who or what, if anything, may later invoke the proposed internal Terrain B caller in live
> production WITHOUT endpoint/schema/API/public-surface drift, WITHOUT modifying `/agent/query`
> or `/retrieve`, and WITHOUT giving memory output authority?

## 3. Current-edge source survey (source-grounded at `d9dac36`)

```text
torment_service/app.py
  - @app.post("/agent/query"); def query(...)  builds a SpineRequest and calls
    submit_task(spine_req, fabric, ctx)                                   [L679-690]
  - @app.post("/retrieve"); def retrieve_assembled(...)  read-only / context-source; no
    generation.
  - @app.post("/cognition/run"); def cognition_run(...)  runs run_cognition_pipeline(...)
    (cognition package)                                                   [L2262-2270]
  - @app.post("/spine/submit_task"); def spine_submit_task(...) → submit_task(...)  [L2398-2437]
  - the module references NO AgentRunner, NO run_turn, NO memory_context_orchestrator.
  => EVERY production endpoint routes to the SPINE (submit_task) or run_cognition_pipeline —
     NONE invokes AgentRunner.run_turn or the Terrain B caller.

torment_service/spine.py
  - class SpineRequest [L568]; submit_task(...) [L1164]; _full_cognition(...) [L986] calls
    run_cognition_pipeline(...) [L1051] (from cognition.pipeline).
  - it references NO AgentRunner, NO run_turn, NO enter_reflex.
  => the live cognition path is the cognition.pipeline (Router → Apertures → Roles →
     Reintegration → Response) — a DIFFERENT mechanism from AgentRunner.run_turn.

torment_service/fabric.py
  - self.drift_reflex_callback: Optional[Callable[[str,str,Dict],None]] = None  [L692];
    invoked ONLY when drift is high AND the callback is not None [L3413-3425]. Comment [L684]:
    "External consumers (typically an AgentRunner owner) set this."
  - NO assignment to drift_reflex_callback exists anywhere in torment_service (grep = 0).
  => drift_reflex_callback is a DORMANT runtime hook, never set in production; it is a
     drift-REFLEX (autonomy) notification, returning None.

torment_service/mcp_server.py
  - references NO AgentRunner / run_turn / orchestrator (grep = 0).
  => MCP is a memory surface, not a generation trigger (MCP capability boundary holds).

torment_service/agent_loop.py
  - AgentRunner.run_turn(...) exposes the optional memory_context_text seam; references no
    assemble_context / AssembledContext / retrieval_assembler / .query(). CONSUMER-ONLY.

torment_service/memory_context_orchestrator.py
  - owns assembly + run_turn(..., memory_context_text=...); referenced ONLY by its own file
    across torment_service => CALLED NOWHERE in production.

NEGATIVE / forbidden terrain (unchanged):
  - PrivateGenerationOwner (own generation boundary, not authoritative AgentRunner); excluded.
  - audit_selected_items_runner_bridge (passes audit items, never memory_context_text);
    called nowhere; negative.
  - no live U1 / audit-owner / private-owner production route exists.
  - tests/manual memory-to-prompt harnesses are NEGATIVE EVIDENCE only.
```

**Decisive architectural finding:** the LIVE production cognition path is the **Spine /
`run_cognition_pipeline`** (reached by `/agent/query`, `/cognition/run`, `/spine/submit_task`).
The **AgentRunner.run_turn** runtime (which carries the `memory_context_text` seam and is the
target of the Terrain B caller) is **architecturally disjoint** from that live path — no
production endpoint, Spine path, MCP tool, or set callback reaches it.

Survey answers: `/agent/query` invokes neither AgentRunner nor the orchestrator (it routes to
the Spine); `/retrieve` performs no generation; `/spine/submit_task` and `/cognition/run` are
Spine / cognition-pipeline triggers, **not** AgentRunner triggers; `spine.py` exposes a
non-endpoint task chain that runs `run_cognition_pipeline`, **not** an AgentRunner invocation;
`mcp_server.py` exposes no AgentRunner/generation tool; `fabric.drift_reflex_callback` is a
dormant, never-set, drift-reflex hook; `AgentRunner` remains consumer-only; the orchestrator is
called nowhere; harnesses / `PrivateGenerationOwner` / selected-items bridge / U1 remain
forbidden/negative.

## 4. Trigger terrains evaluated ON PAPER ONLY

```text
A. Existing internal Spine / governed-task terrain (submit_task / _full_cognition)
   - Production-reachable, BUT it routes to run_cognition_pipeline (cognition package), NOT to
     AgentRunner. To make it invoke the Terrain B caller would mix Spine task/governance terrain
     with a SEPARATE generation mechanism and change the Spine's behavior/response — and the
     Spine is reached via endpoints, so altering it is public-surface/response drift.
   - It also risks hidden autonomy by turning a governed-task path into a generation trigger.
   => REJECTED (endpoint/response drift + mechanism-mixing + autonomy risk).

B. Existing non-endpoint runtime callback terrain (fabric.drift_reflex_callback)
   - It is DORMANT: never set anywhere in torment_service production (set only by external
     AgentRunner owners). It fires on HIGH DRIFT — a reflex/autonomy notification returning None.
   - Coupling memory-to-generation to it would create drift-reflex/autonomy expansion and an
     output-coupled reflex loop; and it is not a real production trigger today anyway.
   => REJECTED (forbidden autonomy/reflex coupling + not production-set).

C. Existing app endpoint terrain (NEGATIVE / constraint)
   - /agent/query retrofit FORBIDDEN; /retrieve generation FORBIDDEN; endpoint wrapper
     FORBIDDEN; MCP public-tool expansion requires separate authorization and is NOT selected.
   => NEGATIVE terrain only.

D. New internal trigger terrain
   - Has NO existing production reachability: something must invoke it, and that something is
     either an endpoint (drift) or the reflex callback (autonomy). So it does not solve the live
     trigger today.
   => Does NOT solve live trigger.

E. HOLD
   - Selected when every reachable trigger requires endpoint/public-surface drift, forbidden
     autonomy, or unsupported source assumptions. (See §6 verdict.)
```

## 5. Exact caller-chain proof (result)

The required chain is:

```text
live trigger → approved internal Terrain B caller → TormentFabric.query(...) →
memory_context_orchestrator.run_turn_with_memory_context(...) → assemble_context(...) /
AssembledContext.assembled_text → AgentRunner.run_turn(..., memory_context_text=...)
```

**This chain cannot be source-proven for any reachable trigger today.** The right-hand end
(`AgentRunner.run_turn`) is not on any live production path: the live path is the Spine /
`run_cognition_pipeline`, which is a different mechanism. Every candidate trigger fails the
no-drift / no-autonomy obligations:

```text
- Spine/governed-task terrain → reaches run_cognition_pipeline, not AgentRunner; bridging it to
  AgentRunner changes Spine/endpoint behavior (drift) and mixes mechanisms;
- drift_reflex_callback → dormant + autonomy-coupled;
- endpoints → retrofit = drift (forbidden);
- new internal terrain → no production reachability.
```

Because the exact chain cannot be source-proven without endpoint/public-surface drift or
forbidden autonomy coupling, the verdict is **HOLD**.

## 6. Forbidden trigger routes

```text
- /agent/query retrofit;
- /retrieve generation;
- endpoint wrapper;
- schema / API change;
- provider / manual harness;
- MCP public-tool expansion without separate authorization;
- PrivateGenerationOwner;
- selected-items bridge;
- U1 / audit-owner / private-owner route;
- AgentRunner owning retrieval / assembly;
- hidden autonomy / monitoring expansion;
- write-feedback loop;
- output-control / review / ranking / retry / suppression / style steering.
```

## 7. Decision options

```text
- Option A: existing internal Spine/governed-task terrain may later trigger Terrain B.
- Option B: existing non-endpoint runtime callback terrain may later trigger Terrain B.
- Option C: new internal trigger terrain may later trigger Terrain B without public drift.
- Option D: HOLD — no live trigger selected because all reachable triggers require
            endpoint/public-surface drift or forbidden autonomy/output-control coupling.
- Option E: source-gap — more source evidence is required before live-trigger selection.
(Select at most one. Do not force selection.)
```

Verdict:

```text
=> SELECT Option D — HOLD. No live trigger is selected.
   - A rejected: the Spine/governed-task path runs run_cognition_pipeline, not AgentRunner;
     bridging it is endpoint/response drift + mechanism-mixing + autonomy risk.
   - B rejected: drift_reflex_callback is dormant (never set in production) and autonomy-coupled.
   - C rejected: endpoint terrain is forbidden/negative (retrofit = drift).
   - The new-internal-terrain option does not solve reachability (it needs an endpoint or the
     reflex callback to be reached).
   - Not Option E: this is not merely missing evidence — the survey shows a definite
     architectural disjointness (live cognition = Spine/cognition.pipeline; the Terrain B caller
     drives the separate, unwired AgentRunner runtime). The gap is structural, not evidential.
```

**Parked observation (out of scope, not opened here):** because the memory-to-prompt arc was
built around `AgentRunner.run_turn` while the live production path runs the Spine /
`cognition.pipeline`, a future direction — *separate from this lane and requiring its own
decision* — could either (a) frame memory-to-prompt for the `cognition.pipeline` path, or
(b) take a larger architecture decision about whether `AgentRunner` should ever sit on a live
production path. Both are distinct future questions; neither is selected, opened, or
authorized here.

## 8. Future tests / AST guards to name only (not implemented now)

```text
- sanctioned trigger only;
- sanctioned internal Terrain B caller only;
- no endpoint retrofit;
- /agent/query unchanged;
- /retrieve performs no generation;
- /spine/submit_task no hidden generation unless separately authorized;
- /cognition/run no hidden generation unless separately authorized;
- mcp_server no public-tool expansion;
- no provider / manual harness import;
- no PrivateGenerationOwner;
- no selected-items bridge;
- AgentRunner imports no retrieval / assembly;
- no public exposure of memory_context_text;
- no persistence / write / feedback / promote;
- no logging / transcript writers;
- no output-control / review / ranking / retry / suppression / style steering;
- no hidden autonomy / monitoring expansion.
```

## 9. Required no-go list (this step)

```text
No code, tests, wiring, endpoint edits, provider runtime, persistence / write / logging /
transcripts, output-control, audit / private-owner / Gate D / database / substrate work; no
/agent/query modification; no /retrieve modification; no schema / API / public-surface change;
no live production wiring; no Terrain B runtime.
```

## 10. Must remain HOLD

```text
- implementation;
- the code / tests slice;
- live production wiring;
- Terrain B runtime;
- /agent/query;
- /retrieve;
- public surface;
- provider runtime;
- write paths;
- all audit / private-owner / Gate D / database lanes.
```

## 11. Final verdict

**HOLD — no live trigger is selected.** Source at `d9dac36` shows the live production cognition
path is the Spine / `run_cognition_pipeline`, architecturally disjoint from the
`AgentRunner.run_turn` runtime the Terrain B caller drives; every reachable trigger requires
endpoint/public-surface drift (endpoints, Spine/governed-task) or forbidden drift-reflex
autonomy coupling (`drift_reflex_callback`, itself dormant), so the exact caller-chain cannot
be source-proven. No production code is authorized. No tests are authorized. No wiring is
authorized. No runtime is authorized. The next move, if any, is **HOLD or a narrower,
separately-authorized architecture/evidence frame** examining the Spine/`cognition.pipeline`
-vs-`AgentRunner` disjointness — **not code**, and not unless Codex explicitly authorizes it
later.

## 12. Anti-drift footer

TORMENT — MEMORY-TO-PROMPT-FOR-GENERATION LIVE CALLER TERRAIN B LIVE-TRIGGER DECISION FRAME /
DOCS-ONLY / NON-AUTHORIZING / HOLD. Source-grounded at `d9dac36`: every production endpoint
(`/agent/query`, `/retrieve`, `/cognition/run`, `/spine/submit_task`) routes to the Spine
(`submit_task`) / `run_cognition_pipeline` — NONE invokes `AgentRunner.run_turn`; `spine.py`
runs the cognition pipeline, not AgentRunner; `mcp_server.py` exposes no generation tool;
`fabric.drift_reflex_callback` is a dormant, never-set, drift-reflex hook; `AgentRunner` is
consumer-only; `memory_context_orchestrator` is called nowhere. The live cognition path
(Spine/`cognition.pipeline`) and the AgentRunner memory-seam runtime are DISJOINT, so the
Terrain B caller has no fence-preserving live trigger: Spine/governed-task triggering = drift +
mechanism-mixing, `drift_reflex_callback` = forbidden autonomy coupling, endpoints = forbidden
retrofit, new internal terrain = no reachability. **Verdict: Option D — HOLD; no live trigger
selected.** It authorizes no code, no tests, no wiring, no endpoint/API/schema/public-surface
change, no provider runtime, and no Terrain B runtime; the orchestrator stays dormant; any
future move requires a separately authorized architecture/evidence frame under Hilmir + Codex.
Memory remains guidance, not authority; audit observes authority and does not become authority;
nothing rewrites identity / canon / seed / soul.

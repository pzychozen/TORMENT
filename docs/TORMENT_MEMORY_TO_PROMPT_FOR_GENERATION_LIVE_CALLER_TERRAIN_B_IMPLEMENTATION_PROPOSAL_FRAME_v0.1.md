# TORMENT — Memory-to-Prompt-for-Generation Live Caller Terrain B Implementation Proposal Frame v0.1

## 1. Status / non-authorization

**Docs-only / NON-AUTHORIZING / Terrain B implementation-proposal frame / no code / no tests /
no wiring / HOLD preserved.** This frame writes **no code and no tests**, implements **nothing**,
wires **nothing**, introduces **no runtime behavior**, makes **no endpoint / schema / API /
public-surface change**, and authorizes **no provider runtime**. It may propose a future code
shape **ON PAPER ONLY**, define future tests/AST guards **ON PAPER ONLY**, define forbidden
implementation shapes, or conclude **HOLD**. It authorizes no code, no tests, no implementation,
no wiring, no endpoint behavior, no provider runtime, and no public-surface/schema/API change.
HOLD is preserved. Where this frame and any parent contract/guard differ, the contract/guard
wins.

Standing posture carried verbatim:

> Memory may shape context. Memory may not seize authority.
> Audit observes authority. Audit must not become authority.

Anchor: `4ebbf88` (docs(project): close memory-to-prompt live caller proposal). Parent paper
verdict: `229b43c` selected **Terrain B ON PAPER ONLY** — a new internal, non-endpoint
production orchestration caller driving the existing dormant `memory_context_orchestrator`;
implementation, wiring, and code/tests were **not** authorized. **This frame proposes that
terrain's future code shape on paper; it authorizes none of it.**

## 2. The exact question

> How, if at all, could a new internal non-endpoint production orchestration caller later drive
> `memory_context_orchestrator.run_turn_with_memory_context(...)` in live production WITHOUT
> endpoint/schema/API/public-surface drift, WITHOUT making `AgentRunner` own retrieval/assembly,
> and WITHOUT giving memory output authority?

## 3. Current-edge source survey (source-grounded at `4ebbf88`)

```text
torment_service/app.py
  - @app.post("/agent/query"); def query(req)                       [L907-908]
  - @app.post("/retrieve");    def retrieve_assembled(req)          [L1341-1342]
  - the module references NO AgentRunner, NO run_turn, NO memory_context_orchestrator
    (grep count = 0).
  => /agent/query invokes NEITHER AgentRunner NOR the orchestrator; /retrieve performs NO
     generation (read-only / context-source).

torment_service/agent_loop.py
  - run_turn(...) exposes the optional keyword-only memory_context_text=None [L511], threaded
    into the dormant seam.
  - it references NO assemble_context / AssembledContext / retrieval_assembler and makes NO
    .query(...) call (grep count = 0). (TormentFabric appears only in a deferred-note comment.)
  => AgentRunner is CONSUMER-ONLY; it owns no retrieval / assembly.

torment_service/memory_context_orchestrator.py
  - run_turn_with_memory_context(...) [L63] OWNS assembly (assemble_context) and invokes
    AgentRunner.run_turn(..., memory_context_text=...) — the same-turn owner shape.
  => referenced ONLY by its own file across torment_service => CALLED NOWHERE in production.

torment_service/fabric.py
  - TormentFabric.query(workspace_id, agent_id, query_text, top_k=8, domain_id=None, ...)
    returns a dict whose "results" key carries the rescored core hits — the core-hits source.

torment_service/retrieval_assembler.py
  - assemble_context(...) → AssembledContext.assembled_text remains the governed memory text
    source (stdlib-only; no generation).

NEGATIVE / forbidden terrain (unchanged):
  - audit_private_generation_owner.py / PrivateGenerationOwner — calls its OWN generation
    boundary, not the authoritative AgentRunner; excluded / unwired.
  - audit_selected_items_runner_bridge.py — passes audit_admitted_context_items (never
    memory_context_text); called nowhere; negative terrain.
  - no live U1 / audit-owner / private-owner production route exists.
  - tests/manual memory-to-prompt harnesses are EVIDENCE ONLY, not production terrain.
```

Survey answers: `/agent/query` invokes neither `AgentRunner` nor the orchestrator; `/retrieve`
performs no generation; `AgentRunner` imports/owns no retrieval/assembly; the orchestrator owns
assembly + `run_turn(..., memory_context_text=...)` and is called nowhere in production;
`TormentFabric.query(...)` supplies core hits; `assemble_context`/`AssembledContext.assembled_text`
remain the governed memory text source; `PrivateGenerationOwner`, the selected-items bridge,
U1/audit-owner, and the harnesses remain forbidden/negative terrain.

## 4. Terrain B proposed future code shape — ON PAPER ONLY

```text
PROPOSED (not authorized, not written, not named for real):
- a NEW internal, non-endpoint module only — proposed neutral name (PAPER-ONLY, NOT authorized):
    torment_service/memory_to_prompt_live_caller.py
- exposing ONE internal function only — proposed neutral name (PAPER-ONLY):
    run_live_memory_context_turn(...)
- it MAY call TormentFabric.query(...) to obtain core hits;
- it MAY call memory_context_orchestrator.run_turn_with_memory_context(...) — which owns
  assembly (assemble_context) and the AgentRunner.run_turn(..., memory_context_text=...) call;
- it MUST NOT call provider APIs directly;
- it MUST NOT call /agent/query;
- it MUST NOT call /retrieve;
- it MUST NOT import app.py;
- it MUST NOT modify schemas, API, or public payloads;
- it MUST NOT perform persistence / write / logging / transcript output;
- it MUST NOT create output-control / review / ranking / retry / suppression / style steering;
- it MUST NOT create write feedback from model output back into memory.
```

The proposed filename and function name are illustrative and **not authorized**; a later,
separately authorized code+tests slice would finalize them.

## 5. Same-turn ownership model (how the future shape preserves ownership)

```text
- the NEW internal caller owns the same-turn PRODUCTION path;
- TormentFabric.query(...) supplies core hits (retrieval source);
- memory_context_orchestrator owns assembly AND the call into
  AgentRunner.run_turn(..., memory_context_text=...);
- assemble_context(...) / AssembledContext.assembled_text remain the ONLY governed memory text
  source;
- AgentRunner remains CONSUMER-ONLY;
- AgentRunner imports/owns NO retrieval / assembly;
- /retrieve remains read-only / context-source;
- the memory text passes ONLY through memory_context_text;
- memory remains bounded, labelled, read-only, non-authoritative, turn-local, non-public,
  non-persistent.
```

## 6. Critical unresolved live-trigger question (explicit)

Terrain B can define the internal caller's SHAPE, but **live production reachability is still
UNRESOLVED.** Because `/agent/query` cannot be modified in this frame and endpoint/public-surface
drift remains forbidden, the live-trigger question is **deferred**:

```text
- WHO or WHAT invokes the new internal caller in live production?
- Can it be reached WITHOUT endpoint / schema / API drift?
- Is a separate EXISTING internal caller available, or would endpoint wiring be unavoidable?
- IF endpoint wiring is unavoidable, implementation remains HOLD.
```

**Most important safety point:** this proposal may describe the internal module shape, but it
**must NOT pretend production reachability is solved.** Source does not yet show a fence-preserving
live trigger — today no production endpoint invokes `AgentRunner` generation, and the
orchestrator is called nowhere. So the module shape is proposable on paper, but **its production
reachability is unsolved and is a separate, later-gated question.**

## 7. Future tests / AST guards to name only (not implemented now)

```text
- sanctioned internal caller only;
- no production caller except the approved internal caller;
- no endpoint imports / routes;
- app.py unchanged;
- /agent/query behavior unchanged unless separately authorized later;
- /retrieve performs no generation;
- AgentRunner imports no assembler / retrieval;
- the orchestrator is called only by the sanctioned caller in production;
- no public exposure of memory_context_text;
- no provider runtime;
- no persistence / write / feedback / promote;
- no logging / transcript writers;
- no output-control / review / ranking / retry / suppression / style steering;
- the memory block stays bounded / labelled / read-only / non-public / non-persistent;
- no PrivateGenerationOwner;
- no selected-items / audit bridge route;
- no U1 / private-owner route.
```

## 8. Forbidden implementation shapes

```text
- endpoint wrapper;
- /agent/query retrofit;
- /retrieve generation;
- AgentRunner importing retrieval / assembly;
- a harness promoted to production;
- PrivateGenerationOwner;
- selected-items / audit bridge route;
- provider-backed runtime;
- public payload / schema / API change;
- a writeback loop from model output;
- a ranking / retry / review / suppression / style steering layer;
- logging / transcript persistence.
```

## 9. Decision options

```text
- Option A: the Terrain B implementation-proposal SHAPE is admissible ON PAPER, but the
            live-trigger remains DEFERRED.
- Option B: Terrain B is inadmissible unless a live-trigger source is found first.
- Option C: HOLD — any implementation would require endpoint / public-surface drift.
```

Verdict (source decides; cautious):

```text
- The internal MODULE SHAPE is safe to propose on paper: it is a new internal non-endpoint
  function that calls TormentFabric.query(...) for hits and the dormant orchestrator for
  assembly + run_turn(..., memory_context_text=...); it touches no endpoint/schema/public
  surface, keeps AgentRunner consumer-only, leaves /retrieve read-only, and gives memory no
  output authority.
- BUT live production reachability (the live trigger) is UNSOLVED in source today; a
  fence-preserving trigger has not been shown, and endpoint wiring would be drift (forbidden).
=> SELECT Option A: the Terrain B implementation-proposal SHAPE is admissible ON PAPER ONLY,
   with the live-trigger DEFERRED and separately gated. Options B and C are not selected
   because the internal module shape itself can be safely proposed on paper; the live trigger
   is the unresolved sub-question, not the module shape.
```

**Option A is selected ON PAPER ONLY. It authorizes no code, no tests, no implementation, and no
wiring.** A later code+tests slice (and the live trigger before it) require separate Hilmir +
Codex authorization. If a fence-preserving live trigger cannot be found, implementation remains
HOLD.

## 10. Required no-go list (this step)

```text
No code, tests, wiring, endpoint changes, /agent/query modification, /retrieve modification,
schema / API / public-surface change, provider runtime, persistence / write / logging /
transcripts, output-control / review / suppression / retry / ranking / style steering,
U1 / audit-owner / private-owner / selected-items route, Gate D / private cognition / dream /
Envelope Audit runtime, database / substrate work.
```

## 11. Must remain HOLD

```text
- all code;
- all tests;
- implementation;
- wiring;
- endpoint behavior;
- public surface;
- provider runtime;
- persistence / write paths;
- all audit / private-owner / Gate D / database lanes;
- the live trigger, unless separately proven and authorized.
```

## 12. Final verdict

**The Terrain B implementation-proposal SHAPE is admissible ON PAPER ONLY, with the live-trigger
DEFERRED.** No production code is authorized. No tests are authorized. No wiring is authorized.
The proposed internal module shape (a new internal non-endpoint caller driving the dormant
orchestrator) preserves every fence on paper, but its production reachability is unsolved and
separately gated. The next move, if pursued, is a **Codex review for a later code+tests slice OR
a live-trigger decision frame** — not immediate code, and not unless separately authorized. If
no fence-preserving live trigger is found, implementation remains HOLD.

## 13. Anti-drift footer

TORMENT — MEMORY-TO-PROMPT-FOR-GENERATION LIVE CALLER TERRAIN B IMPLEMENTATION-PROPOSAL FRAME /
DOCS-ONLY / NON-AUTHORIZING / PAPER-ONLY / HOLD PRESERVED. Source-grounded at `4ebbf88`:
`/agent/query` (`query`) and `/retrieve` (`retrieve_assembled`) invoke no generation and
reference no orchestrator; `AgentRunner` is consumer-only (memory_context_text seam only, no
assembler/retrieval/`TormentFabric.query`); `memory_context_orchestrator` owns assembly + the
same-turn `run_turn(..., memory_context_text=...)` invocation but is called nowhere in
production; `assemble_context`/`AssembledContext.assembled_text` remain the governed memory
source; `PrivateGenerationOwner`, the selected-items bridge, U1/audit-owner, and the harnesses
remain forbidden/negative terrain. It proposes, ON PAPER ONLY, a new internal non-endpoint module
(illustrative `memory_to_prompt_live_caller.run_live_memory_context_turn`) that drives the
dormant orchestrator — selecting Option A (shape admissible on paper, live-trigger deferred);
the live trigger / production reachability is explicitly UNSOLVED and separately gated. **It
authorizes no code, no tests, no implementation, no wiring, no endpoint/API/schema/public-surface
change, and no provider runtime; the orchestrator stays dormant; any code+tests slice and any
live trigger require separate Hilmir + Codex authorization.** Memory remains guidance, not
authority; audit observes authority and does not become authority; nothing rewrites identity /
canon / seed / soul.

# TORMENT — Memory-to-Prompt-for-Generation Live Caller Proposal Frame v0.1

## 1. Status / non-authorization

**Docs-only / NON-AUTHORIZING / source-first LIVE-CALLER-PROPOSAL / no implementation / no
wiring / no endpoint change / HOLD preserved.** This frame writes **no code and no tests**,
introduces **no runtime behavior**, implements **no live caller**, makes **no endpoint /
schema / API / public-surface change**, performs **no production wiring**, and authorizes **no
provider runtime**. It may select **at most ONE** proposed live-caller terrain **ON PAPER**, or
conclude **HOLD**. HOLD remains until a later, separately authorized implementation-proposal /
code slice. Where this frame and any parent contract/guard differ, the contract/guard wins.

Standing posture carried verbatim:

> Memory may shape context. Memory may not seize authority.
> Audit observes authority. Audit must not become authority.

Anchor: `a675c07` (docs(cognition): frame memory-to-prompt live wiring decision). Parent
decision: the live-wiring decision frame selected **Option B only** — a later
LIVE-CALLER-PROPOSAL is admissible, but live wiring remains HOLD; no caller was selected and
no implementation was authorized. **This frame is that proposal.**

## 2. The exact proposal question

> Which single production live-caller terrain, if any, may be proposed ON PAPER as the owner
> of the same-turn path
> `TormentFabric.query(...) → assemble_context(...) / AssembledContext.assembled_text →
> AgentRunner.run_turn(..., memory_context_text=...)`,
> while preserving every current authority fence?

This proposal may select exactly ONE proposed live-caller terrain ON PAPER, or conclude HOLD.
It may NOT authorize implementation, tests, wiring, endpoint edits, runtime behavior, or
provider runtime; it does not modify `/agent/query` or `/retrieve`; it changes no schema / API
/ public surface.

## 3. Current-edge source survey (source-grounded at `a675c07`)

```text
torment_service/app.py
  - @app.post("/agent/query"); def query(req) -> Dict[str, Any]            [L907-908]
  - @app.post("/retrieve");    def retrieve_assembled(req) -> Dict[...]    [L1341-1342]
  - The module references NO AgentRunner, NO run_turn, and NO
    memory_context_orchestrator (grep-negative).
  => /agent/query does NOT call AgentRunner.run_turn and does NOT call the orchestrator.
  => /retrieve owns governed assembly (assemble_context) and performs NO generation;
     it remains read-only / context-source terrain.

torment_service/agent_loop.py
  - run_turn(...) exposes the optional keyword-only memory_context_text=None [L511], threaded
    into the dormant seam (_execute_with_prompt_request → _execute → _build_llm_prompt_request
    → _build_memory_context_message) [L607, L1044, L1057, L1072, L1096+].
  - It references NO assemble_context / AssembledContext / retrieval_assembler and makes NO
    .query(...) call. (TormentFabric appears ONLY in a deferred-note comment [L221], never as
    an import or call.)
  => AgentRunner remains CONSUMER-ONLY: it owns no retrieval / assembly.

torment_service/memory_context_orchestrator.py
  - run_turn_with_memory_context(...) [L63] OWNS assembly (calls assemble_context(...) as a
    function), derives a bounded read-only string from AssembledContext.assembled_text, and
    invokes AgentRunner.run_turn(..., memory_context_text=...) — the SAME-TURN owner shape.
  => Referenced ONLY by its own file across torment_service => CALLED NOWHERE in production.

torment_service/retrieval_assembler.py
  - assemble_context(...) → AssembledContext.assembled_text remains the governed memory text
    source (stdlib-only; no generation).

torment_service/fabric.py
  - TormentFabric.query(workspace_id, agent_id, query_text, top_k=8, domain_id=None, ...)
    returns a dict whose "results" key carries the rescored core hits — a valid retrieval
    source for core_hits.

NEGATIVE surfaces (unchanged):
  - torment_service/audit_private_generation_owner.py — PrivateGenerationOwner calls its OWN
    generation boundary, NOT the authoritative AgentRunner; excluded / unwired.
  - torment_service/audit_selected_items_runner_bridge.py — passes audit_admitted_context_items
    (never memory_context_text); called nowhere in production; negative terrain.
  - tests/manual memory-to-prompt harnesses are NON-PRODUCTION evidence only — NOT caller
    terrain.
```

Survey answers: `/agent/query` does **not** call `run_turn` or the orchestrator; `/retrieve`
performs **no** generation; `AgentRunner` imports/owns **no** assembler / retrieval /
`TormentFabric.query`; the orchestrator owns assembly + calls
`run_turn(..., memory_context_text=...)` and is **called nowhere** in production;
`TormentFabric.query(...)` returns usable core hits; `assemble_context` /
`AssembledContext.assembled_text` remain the governed memory text source;
`PrivateGenerationOwner` and the selected-items bridge remain **negative** terrain.

## 4. Candidate terrain comparison

```text
A. Existing app.py / /agent/query as possible live orchestration terrain
   - It is the existing live query entry terrain (returns a retrieval / MemoryPlan dict).
   - To own the same-turn path it would have to invoke AgentRunner generation and return a
     generated turn instead of (or alongside) the current retrieval response — a CHANGE to
     its response / schema / public surface (drift).
   - It must NOT make /retrieve generation terrain; it must NOT make AgentRunner own assembly.
   - It cannot be selected unless source proof shows it owns the same-turn path WITHOUT
     public-surface / schema / API drift — which it cannot today.

B. New internal, non-endpoint production orchestration caller
   - It can own the same-turn path internally — invoking the existing dormant orchestrator
     (memory_context_orchestrator.run_turn_with_memory_context), which already holds governed
     assembly + the run_turn(..., memory_context_text=...) invocation — WITHOUT changing any
     endpoint / schema / API / public surface.
   - It must be SEPARATELY wired later by some caller; this frame cannot wire it, and its live
     trigger is a deferred implementation-proposal question.
   - It must NOT become a hidden output-control / review / ranking layer.
   - It is the only terrain that can own the same-turn path with NO endpoint drift.

C. Existing memory_context_orchestrator.py itself as the live caller
   - It is the dormant callee / assembly owner and is ALREADY the same-turn path OWNER
     (assembly + run_turn(..., memory_context_text=...)).
   - But it is not self-triggering: a production caller must invoke it. It cannot become live
     merely because harnesses call it. As a standalone "live caller" it is insufficient — it
     needs B's caller.

D. Component path ownership
   - TormentFabric.query(...), assemble_context(...) / AssembledContext.assembled_text, and
     AgentRunner.run_turn(..., memory_context_text=...) are COMPONENTS, not the same-turn owner.
   - A selected terrain must prove WHO owns the same-turn path; the components alone do not.

E. /retrieve as NEGATIVE terrain
   - /retrieve remains read-only / context-source; it must NOT invoke AgentRunner and must NOT
     become generation terrain.
```

## 5. Exact same-turn ownership proof (obligations for any selected paper terrain)

```text
- it owns governed retrieval/assembly AND the authoritative run_turn invocation in ONE turn;
- the governed memory text source is ONLY AssembledContext.assembled_text or a bounded
  derivative of it;
- the memory text passes ONLY through memory_context_text;
- AgentRunner remains CONSUMER-ONLY (imports/owns no assembler / retrieval);
- /retrieve remains read-only / context-source;
- memory remains bounded, labelled, read-only, non-authoritative, turn-local, non-public,
  non-persistent.
If no candidate satisfies this proof, the verdict is HOLD.
```

Terrain B satisfies this on paper: the existing orchestrator already owns governed assembly
+ the same-turn `run_turn(..., memory_context_text=...)` invocation (proven dormant in code
and exercised by the three closed harnesses); a new internal non-endpoint caller can drive
that owner without endpoint/schema/public-surface drift, with the runner staying
consumer-only and `/retrieve` untouched.

## 6. Forbidden terrains

```text
- /retrieve as generation terrain
- AgentRunner owning retrieval / assembly
- PrivateGenerationOwner
- selected-items audit bridge / U1 / audit-owner routes
- harnesses as production callers
- provider / manual paths as production runtime
- endpoint / API / schema / public-surface change
- output-control / review / suppression / retry / ranking / style steering
- persistence / write / logging / transcripts
- database / substrate
```

## 7. Proposed verdict options

```text
- Option A: select existing app.py / /agent/query terrain ON PAPER as proposed live caller.
- Option B: select a NEW internal, non-endpoint production orchestration caller ON PAPER.
- Option C: select existing memory_context_orchestrator.py itself as live caller.
- Option D: HOLD — no terrain satisfies the proof.
(Select AT MOST ONE.)
```

Verdict (source decides; not forced):

```text
- A REJECTED: owning the same-turn path at /agent/query would change its response / schema /
  public surface (drift); the fence forbids that here.
- C REJECTED-as-standalone: the orchestrator is the same-turn OWNER but is not self-triggering;
  it needs a production caller, so it is insufficient on its own.
- D REJECTED: the source supports a safe paper terrain (B), so HOLD-for-lack-of-terrain is too
  strong.
- B SELECTED — ON PAPER ONLY: a NEW internal, non-endpoint production orchestration caller
  that drives the existing dormant orchestrator owns the same-turn path with NO endpoint /
  schema / API / public-surface drift, runner consumer-only, /retrieve untouched.
```

**B is selected ON PAPER ONLY. It authorizes no implementation.** The orchestrator remains
dormant; B's live trigger / wiring is a SEPARATE, later, separately-authorized
implementation-proposal question (today no production endpoint invokes AgentRunner
generation, so HOW B is reached in the live request flow without endpoint drift is the next
question — explicitly deferred, not answered here).

## 8. Future tests / AST guard obligations (named only; not implemented now)

```text
- sanctioned caller only;
- no forbidden imports / routes;
- AgentRunner imports no assembler / retrieval;
- /retrieve performs no generation;
- no provider runtime;
- no public exposure of memory_context_text;
- no persistence / write / feedback / promote;
- no review / ranking / retry / suppression / style steering;
- the memory block stays bounded / labelled / read-only / non-public / non-persistent;
- an orchestrator call-count / terrain guard, if a future implementation proposes one.
```

## 9. Required no-go list (this step)

```text
No code, tests, wiring, endpoint changes, /agent/query modification, /retrieve modification,
schema / API / public-surface change, provider runtime, persistence / write / logging /
transcripts, output-control / review / suppression / retry / ranking / style steering,
U1 / audit-owner / private-owner / selected-items route, Gate D / private cognition / dream /
Envelope Audit runtime, database / substrate work.
```

## 10. Must remain HOLD

```text
- live production wiring;
- the implementation proposal;
- the code / tests slice;
- /agent/query behavior;
- /retrieve;
- provider runtime;
- public surface;
- write / persistence paths;
- all audit / private-owner / Gate D / database lanes.
```

## 11. Final verdict

**Proposed paper terrain: a NEW internal, non-endpoint production orchestration caller
(terrain B), driving the existing dormant `memory_context_orchestrator` — ON PAPER ONLY, with
implementation still NOT authorized.** No production wiring is authorized. No code or tests are
authorized. The orchestrator stays dormant and `/agent/query` / `/retrieve` stay unmodified.
The next move, if any, is a **separately authorized implementation-proposal review**, not
code; that review must resolve how terrain B is reached in the live request flow without
endpoint / schema / public-surface drift, and must discharge the §5 same-turn ownership proof
and the §8 guard obligations.

## 12. Anti-drift footer

TORMENT — MEMORY-TO-PROMPT-FOR-GENERATION LIVE CALLER PROPOSAL FRAME / DOCS-ONLY / SOURCE-FIRST
/ NON-AUTHORIZING / HOLD PRESERVED. Source-grounded at `a675c07`: `/agent/query` (`query`) and
`/retrieve` (`retrieve_assembled`) invoke no generation and reference no orchestrator;
`AgentRunner` is consumer-only (memory_context_text seam only, no assembler/retrieval/
`TormentFabric.query`); the `memory_context_orchestrator` owns assembly + the same-turn
`run_turn(..., memory_context_text=...)` invocation but is called nowhere in production;
`assemble_context` / `AssembledContext.assembled_text` remain the governed memory source;
`PrivateGenerationOwner` and the selected-items bridge remain negative terrain. It selects, ON
PAPER ONLY, terrain B (a new internal non-endpoint production orchestration caller driving the
dormant orchestrator) as the same-turn path owner with NO endpoint/schema/public-surface
drift; A is rejected (response/schema drift), C-as-standalone is insufficient (callee, not
self-triggering), and HOLD (D) is too strong. **It authorizes no code, no tests, no wiring, no
endpoint/API/schema/public-surface change, and no provider runtime; implementation is not
authorized; the orchestrator stays dormant; any live wiring requires a separately authorized
implementation proposal under Hilmir + Codex.** Memory remains guidance, not authority; audit
observes authority and does not become authority; nothing rewrites identity / canon / seed /
soul.

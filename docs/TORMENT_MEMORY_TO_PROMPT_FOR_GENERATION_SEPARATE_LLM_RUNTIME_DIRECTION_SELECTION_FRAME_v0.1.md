# TORMENT — Memory-to-Prompt-for-Generation Separate LLM-Runtime Direction-Selection Frame v0.1

## 1. Status / non-authorization

**Docs-only / SOURCE-FIRST / NON-AUTHORIZING / runtime-product DIRECTION selection / no code /
no tests / no wiring / no implementation / implementation HOLD.**

This frame answers a runtime/product **direction** question ON PAPER and records a paper-only
selection. Selecting a direction here is a planning/architecture act — it names the future
terrain that later work should be scoped against — and it is **not** an implementation
authorization. This frame writes **no code and no tests**, designs and wires **no** runtime,
makes **no endpoint / MCP / schema / API / public-surface change**, authorizes **no** provider
or model runtime, runs **no** live LLM generation, persists **nothing**, opens **no**
database/substrate work, opens **no** autonomy lane, and revives **no** `AgentRunner` /
Terrain B live wiring or dream/private-cognition runtime. Where this frame and any parent
contract, doctrine, lock, or guard differ, **the contract/guard wins**.

Standing posture, carried verbatim:

> Memory may shape context. Memory may not seize authority.
> Audit observes authority. Audit does not become authority.
> Automatic is allowed. Autonomous is not.

Anchors. Current pushed edge: `21ded2a` (docs(project): align orientation head after autonomy
closure). Parent decision this frame discharges: `3e4bc2d` (Spine model-boundary architecture
decision — Option D HOLD, which named "a broader runtime/product decision" as the next move).
Evidence lock both rest on: `f480b69`
(`tests/test_spine_cognition_memory_context_characterization_lock.py`, 11 source/AST tests).

## 2. Decision question

> Should TORMENT select **Option C** as the future runtime/product direction — keep the live
> Spine / `cognition.pipeline` deterministic and governed, while placing memory-to-prompt
> generation, private-cognition, and dream-adjacent LLM work in a **separate, non-Spine,
> LLM-bearing runtime** — or should Option C be rejected and the lane remain HOLD?

This is a terrain/direction question, not a build order. It chooses *where* future LLM-bearing
work should live if it is ever built; it does not build it.

## 3. Why this follows from the `3e4bc2d` HOLD

The model-boundary decision frame (`3e4bc2d`) deliberately stopped at **Option D — HOLD**,
recording that the choice among keeping the Spine deterministic (A), a model boundary inside
`cognition/reintegration` (B), a separate non-Spine LLM-bearing runtime (C), or permanent
rejection (E) "turns on whether and where TORMENT wants live LLM generation — a product/runtime
decision that is the operator's fork, not a source-derivable fact," and that "the next move is a
broader runtime/product decision frame ... NOT code." It also recorded a reasoned, non-selecting
lean: **if** live generation is ever wanted, **C is cleaner than B**, **E is too strong**, and
**A is the current state preserved under HOLD**.

This frame is that broader runtime/product decision frame. It does not reopen the test-locked
facts (`f480b69`); it renders the operator-level terrain selection the HOLD was waiting on. The
options below are the same A/B/C/E; what is new is that the operator-product fork is now being
decided at the **direction** level (still paper-only), not the implementation level.

## 4. Source-grounded baseline (re-verified at `21ded2a`)

All claims are grounded in the committed tree at `21ded2a`. Nothing here is reopened or
re-decided; it is the terrain the verdict stands on.

```text
LIVE SPINE / COGNITION IS DETERMINISTIC AND TEST-LOCKED (f480b69)
- tests/test_spine_cognition_memory_context_characterization_lock.py (11 source/AST tests)
  locks: the live path is route -> build_memory_context -> role.run(memory_context) ->
  reintegrate(memory_context) -> result dict; memory_context is same-turn / advisory /
  internal / NON-model-visible; cognition/ AND roles/ contain NO LLM / model / prompt
  boundary; final_answer is deterministic (a " | ".join in _build_final_answer; LLM
  synthesis is a FUTURE docstring note, not a call); /retrieve and
  AssembledContext.assembled_text are NOT the live path; AgentRunner and Terrain B are
  excluded from the live path.
- Re-confirmed at 21ded2a: a fresh grep across cognition/ + roles/ finds no model/provider/
  completion boundary (only LaneQueryProvider, a memory-query object).

SPINE COGNITION IS STRUCTURALLY READ-ONLY
- torment_service/spine.py `_full_cognition` (ratified Decision D1) passes no lookup_fn /
  ingest_fn to run_cognition_pipeline(): "MCP-surface cognition observes but does not
  self-write." cognition/pipeline.py self-write stays default-off (TORMENT_ARCHIVIST_WRITEBACK=0).

ENDPOINTS / MCP ROUTE TO SPINE-OR-RETRIEVE; MCP IS A MEMORY SURFACE
- torment_service/app.py endpoints (/agent/query, /cognition/run, /spine/submit_task,
  /retrieve) route to the Spine / cognition.pipeline / retrieval; app.py references no
  AgentRunner and has no startup lifecycle owner / scheduler (per the autonomy frame).
- torment_service/mcp_server.py exposes memory operations only (submit_task, ingest, query,
  state, feedback, reinforce, tool_result_ingest), capped by TORMENT_MCP_EXPOSURE_TIER
  (open|guarded); no generation tool, no tool dispatch. docs/MCP_CAPABILITY_BOUNDARY.md:
  "There is no action execution layer. This is intentional." Future capability "must ... be
  implemented as a separate governed phase, not folded into the memory system."

THE MEMORY-TO-PROMPT MACHINERY ALREADY EXISTS — DORMANT AND DISJOINT FROM THE SPINE
- torment_service/agent_loop.py (AgentRunner) holds the 8-phase loop, a single model-call
  boundary (_build_llm_prompt_request / _LLMPromptRequest), and the optional runner-local
  memory_context_text seam — and is referenced by NO production endpoint (app.py / spine.py /
  mcp_server.py: zero references).
- torment_service/memory_context_orchestrator.py is an internal, non-endpoint, DORMANT /
  test-called owner-of-assembly: it calls assemble_context(...) as a FUNCTION (never via
  /retrieve), derives a bounded read-only string from AssembledContext.assembled_text, and
  invokes AgentRunner.run_turn(..., memory_context_text=...). It passes ONLY
  memory_context_text (never audit items), writes/persists nothing, creates no retrieval
  authority, performs no output-control, exposes no public surface, and is "CALLED NOWHERE in
  production. Wiring a live production entrypoint is a SEPARATE, separately-authorized gate."
- torment_service/retrieval_assembler.py: assemble_context(...) -> AssembledContext
  .assembled_text is pure deterministic assembly (hard identity-precedence ordering); it
  contains no LLM / completion / run_turn / AgentRunner.

PRIVATE-COGNITION / DREAM TERRAIN IS A SEPARATE, GATED INTERIOR CONTRACT
- docs/TORMENT_PRIVATE_COGNITION_UNIFIED_REFLECTION_BLUEPRINT_v0.1.md (Document B) is a
  docs-only requirement-level interior contract (no runtime, no scheduler, no trigger, no
  budget, no model API, no autonomy). It routes runtime conformance + mechanics to a
  "separately authorized implementation track" (§11), keeps Regime B (dream/incubation)
  bounded by an EXTERNAL budget/trigger it cannot self-set (B-O7), and holds "Autonomous
  remains unopened." Its Layer-2 interior is the natural future tenant of a separate
  LLM-bearing runtime — still separately gated by Document A's wall, P4's read boundary, and
  Document B's obligations.

AUTONOMY IS PARKED (this is terrain selection, not autonomy)
- docs/TORMENT_OPTIONAL_AUTONOMY_LAYER_READINESS_BOUNDARY_DECISION_FRAME_v0.1.md keeps Mode 0
  (automatic-only) current/live and parks any unprompted/autonomous layer. Selecting a runtime
  terrain here grants no startup, no scheduler, no self-trigger, and no tool dispatch.
```

## 5. Option evaluation (A / B / C / E)

### Option A — keep the live Spine deterministic; keep all LLM-bearing work HOLD
```text
- What: no future terrain chosen; LLM-bearing generation / private-cognition / dream stay HOLD
  with no named home.
- Source: this is the current live state (f480b69 lock; deterministic Spine; dormant machinery
  unwired). Maximal safety, zero new risk.
- As a DIRECTION: insufficient if TORMENT wants memory-guided generation, private-cognition, or
  dream-adjacent work — it names no terrain, so every future attempt must re-litigate the Spine
  model-boundary question (the exact loop `3e4bc2d` and the cognition-ceiling frame asked to
  stop). A is preserved as the current state, not selected as the forward direction.
```

### Option B — a bounded model-visible synthesis boundary inside `cognition/reintegration`
```text
- What: turn the FUTURE "_build_final_answer LLM-synthesis" docstring hint into a real
  model-visible synthesis stage on the live cognition path.
- Source: the seam is named, and reintegrate already owns final_answer — so it is mechanically
  plausible.
- RISK (decisive against it as a direction): it places a model boundary on the DETERMINISTIC,
  governed, identity-bearing Spine path; couples the endpoint response to LLM output
  (response / schema / public-surface drift); risks model output gaining authority over the
  governed result; and muddies the clean deterministic/LLM separation that the f480b69 lock
  just established. It would need heavy guards and a separate implementation proposal anyway.
- Verdict: REJECTED / PARKED as a direction. (Not foreclosed forever — but not the chosen
  terrain, because it pollutes the governed path.)
```

### Option C — select a separate, non-Spine, LLM-bearing runtime as the future terrain
```text
- What: keep the Spine deterministic and governed; place memory-to-prompt generation,
  private-cognition, and dream-adjacent LLM work in a SEPARATE, internal, non-Spine,
  LLM-bearing runtime, each piece still separately gated.
- Source fit: the dormant machinery already sits OFF the Spine (AgentRunner + the
  memory_context_orchestrator owner-of-assembly + the runner-local memory_context_text seam,
  all called nowhere in production); retrieval_assembler provides a governed
  AssembledContext.assembled_text source; Document B already routes its private-cognition
  interior runtime to a "separately authorized implementation track"; the MCP boundary already
  demands that future capability be "a separate governed phase, not folded into the memory
  system." C names the home these already point to.
- Benefit: preserves the governed path free of model-output authority (the lock holds), keeps
  separation of concerns (Spine = deterministic cognition/governance; separate runtime = LLM
  generation), and lets future scoping target one terrain instead of reopening the Spine.
- Risk (manageable, deferred to proof obligations): a separate LLM runtime could become a
  hidden parallel product surface if ungoverned; it requires explicit ownership/observability,
  no public-surface drift, no autonomy, and AST guards preserving Spine determinism (§9).
- Verdict: SELECTED as the future runtime/product DIRECTION, ON PAPER ONLY.
```

### Option E — permanently reject live LLM-bearing generation
```text
- What: declare that TORMENT will never host LLM-bearing generation anywhere; abandon the
  memory-to-prompt / private-cognition / dream direction permanently.
- Source: the evidence proves only that no model boundary exists today and that one on the
  Spine path would be risky — NOT that LLM-bearing generation is inherently wrong or unsafe in
  a separate, governed runtime. Permanent rejection over-constrains future architecture.
- Verdict: TOO STRONG — not selected, unless Hilmir explicitly wants permanent rejection.
```

## 6. Direction verdict

**Option C is SELECTED as the future runtime/product direction — ON PAPER ONLY, as a terrain
selection, not an implementation authorization.** Concretely:

- **Option C — selected as the direction.** Future memory-to-prompt generation,
  private-cognition, and dream-adjacent LLM work should be scoped against a separate, internal,
  non-Spine, LLM-bearing runtime, each piece still separately gated. This authorizes no code.
- **Option B — rejected / parked**, because it would put a model boundary on the governed,
  deterministic Spine path and risk endpoint/authority drift.
- **Option A — preserved as the current live state**, but insufficient as the forward direction
  if memory-guided generation / private-cognition / dream is desired; it remains exactly what is
  live today under this selection.
- **Option E — too strong**; not selected unless Hilmir explicitly chooses permanent rejection.
- **Autonomy remains parked.** This is runtime-terrain selection, not autonomous operation: no
  startup, no scheduler, no self-trigger, no tool dispatch is granted or implied.

The selection is load-bearing only as a planning anchor: it tells future slices *where* to aim
and *what not to touch* (the Spine). It moves no code and lifts no fence.

## 7. What Option C authorizes ON PAPER ONLY

```text
- The Spine / cognition.pipeline remains deterministic and test-locked (f480b69 stands).
- No LLM/model/prompt boundary goes into cognition.pipeline, roles, or reintegrate.
- Future memory-to-prompt-for-generation work SHOULD target a separate, internal, non-Spine,
  LLM-bearing runtime (the terrain where AgentRunner + the dormant orchestrator already sit).
- Private-cognition / dream-adjacent work (Document B's Layer-2 interior) MAY be conceptually
  routed toward that separate runtime — still separately gated by Document A / P4 / Document B.
- The next implementation path MAY be scoped against this selected terrain instead of
  repeatedly reopening the Spine model-boundary question.
- Nothing above is code, a wiring instruction, a schema, or a runtime. It is a direction.
```

## 8. What Option C still leaves HOLD

```text
- AgentRunner / Terrain B live wiring;
- implementation; tests; provider runtime;
- startup autonomy; tool-dispatch autonomy;
- database / substrate;
- memory writes;
- public MCP / API / schema drift;
- identity / canon / seed mutation;
- dream / private-cognition runtime;
- output-control / review / suppression / retry / ranking / style steering.
```

## 9. Proof obligations before any code

```text
A later, separately-authorized implementation proposal or dormant skeleton for the separate
LLM-bearing runtime would have to specify and prove, with tests and AST/source guards, ALL of:
- a named runtime owner (the explicit module/object that owns the separate runtime);
- the exact NON-Spine boundary (where the runtime begins and how it stays off the Spine path);
- prompt/request capture rules (how the model-visible request is built and captured);
- a governed memory-source contract (governed AssembledContext.assembled_text or a bounded
  derivative only — never raw hits / private / unadmitted / audit-packet / substrate-only);
- no public-surface drift (no endpoint / MCP / API / schema change);
- no model-output-to-memory feedback;
- no hidden autonomy (no startup, scheduler, self-trigger, tool dispatch);
- no writes / persistence;
- no output-control path (no review / suppression / retry / ranking / style steering);
- AST/source guards preserving Spine determinism;
- an explicit proof that cognition.pipeline / roles / reintegration remain model-boundary-free;
- an explicit proof that app.py / mcp_server.py endpoints are not changed;
- an explicit proof that AgentRunner / Terrain B live wiring remains HOLD unless separately gated.
```

## 10. First later implementation-slice shape (possible next gate only — not authorized)

```text
If — and only if — Hilmir + Codex separately authorize a next step, the first slice could be
EITHER:
  (a) a docs-only, source-first IMPLEMENTATION PROPOSAL for the separate LLM-bearing runtime
      (names owner, non-Spine boundary, capture rules, governed memory-source, guards), OR
  (b) a dormant internal-runtime SKELETON proposal landed dormant / test-called only.
Either way it MUST NOT: wire endpoints, call providers, write memory, revive Terrain B live
wiring, create public API / MCP / schema surface, or run autonomously.
Note (fact, not authorization): a skeletal, test-called shape already exists today — the dormant
memory_context_orchestrator (owner-of-assembly) + the AgentRunner memory_context_text seam — so
a future skeleton has prior art to build against. Selecting/wiring any of it is a SEPARATE gate
and is NOT done here.
```

## 11. Not authorized by this frame

```text
This frame authorizes NONE of the following. It records a paper-only direction selection only:
- no code; no tests; no wiring; no implementation;
- no separate-runtime build, owner, module, or skeleton;
- no provider / model runtime; no live LLM generation; no model boundary anywhere;
- no AgentRunner / Terrain B live wiring; no memory_context_orchestrator production wiring;
- no endpoint / MCP / API / schema / public-surface change;
- no startup autonomy / scheduler / self-trigger / tool dispatch;
- no memory writes; no persistence / logging / transcripts;
- no model-output-to-memory feedback;
- no database / substrate work; no dream / private-cognition runtime;
- no identity / canon / seed mutation;
- no output-control / review / suppression / retry / ranking / style steering.
```

## 12. Anti-drift footer

TORMENT — MEMORY-TO-PROMPT-FOR-GENERATION SEPARATE LLM-RUNTIME DIRECTION-SELECTION FRAME /
DOCS-ONLY / SOURCE-FIRST / NON-AUTHORIZING / RUNTIME-PRODUCT DIRECTION SELECTION / IMPLEMENTATION
HOLD. Discharges the `3e4bc2d` Option-D HOLD (which named "a broader runtime/product decision" as
the next move) over the test-locked baseline `f480b69` on current edge `21ded2a`. It grounds, in
committed source, that the live Spine/cognition path is deterministic with no LLM/model boundary
in `cognition/` or `roles/` (re-verified at `21ded2a`), that the Spine is structurally read-only
(`spine.py` D1) and self-write default-off (`TORMENT_ARCHIVIST_WRITEBACK=0`), that `app.py` /
`mcp_server.py` route to Spine-or-retrieve and MCP is a memory surface with no action layer, that
the memory-to-prompt machinery (`AgentRunner` + the dormant `memory_context_orchestrator` +
the runner-local `memory_context_text` seam over `retrieval_assembler.assemble_context`) already
exists OFF the Spine and is called nowhere in production, and that Document B routes the
private-cognition interior runtime to a separately authorized implementation track. It evaluates
options A/B/C/E and **selects Option C — a separate, non-Spine, LLM-bearing runtime — as the
future runtime/product DIRECTION, ON PAPER ONLY**: B is rejected/parked (model boundary on the
governed deterministic path), A is preserved as the current live state but insufficient as a
forward direction, E is too strong unless Hilmir explicitly wants permanent rejection, and
autonomy remains parked (this is terrain selection, not autonomous operation). It authorizes no
code, no tests, no wiring, no implementation, no separate-runtime build, no provider/model
runtime, no live LLM generation, no model boundary, no AgentRunner/Terrain B live wiring, no
endpoint/MCP/API/schema/public-surface change, no startup autonomy/scheduler/tool dispatch, no
memory writes, no persistence/logging/transcripts, no model-output-to-memory feedback, no
database/substrate, no dream/private-cognition runtime, and no identity/canon/seed mutation; the
next move is a separately authorized implementation proposal or dormant skeleton under Hilmir +
Codex, not code. Memory remains guidance, not authority; audit observes authority and does not
become authority; automatic is allowed, autonomous is not; nothing rewrites identity / canon /
seed / soul.

# TORMENT — Memory-to-Prompt-for-Generation Same-Turn Dual-Ownership CALLER IMPLEMENTATION-PROPOSAL Frame v0.1

## 1. Status / non-authorization

**Implementation-proposal frame ONLY. Docs-only / NON-AUTHORIZING / no lane opened / fence
closed / seam dormant.** Hilmir authorized **only this proposal frame**; Codex PASS. It answers
exactly one question: may **candidate 6** be implemented in a later, separately authorized
**code+tests** slice — by adding an optional runner-local `memory_context_text` parameter to
`AgentRunner.run_turn(...)` and a new internal non-endpoint same-turn memory-orchestration
caller — while preserving every current fence; or must the lane remain **HOLD**.

It **names exact files/functions to change ON PAPER only.** It writes **no code and no tests**,
**wires nothing**, makes **no runtime behavior change**, and makes **no endpoint/API/schema/
public-surface change**. A proposed patch shape is **not implementation authorization.** Where
this frame and any parent contract/guard differ, the contract/guard wins.

Standing posture carried verbatim:

> Memory may shape context. Memory may not seize authority.
> Audit observes authority. Audit must not become authority.

Anchor: `12148dc` (repo edge). Subordinate to, and may not contradict: the CALLER-PROPOSAL
frame (`4fa96ea` / recorded `4cd0c7c`) which selected candidate 6 on paper, the orchestration
decision frame (`e037ad1` / `5373dac`), the live-caller eligibility frame (`2cc5210` /
`669de81`), the landed dormant slice (`5d04658`), the production implementation proposal, the
candidate proof-contract lock, the caller-owned same-turn provenance contract, and the
PW-1…PW-8 pre-wiring guard.

## 2. Current edge and chain

```text
- 12148dc  docs(project): clean memory-to-prompt caller proposal pointer   (current edge / anchor)
- 4cd0c7c  docs(project): record memory-to-prompt caller proposal frame
- 4fa96ea  docs(cognition): propose memory-to-prompt orchestration caller
           — selected candidate 6 ON PAPER (new internal non-endpoint same-turn caller).
- daf824c  docs(project): clean memory-to-prompt orchestration pointer
- 5373dac  docs(project): record memory-to-prompt orchestration decision frame
- e037ad1  docs(cognition): frame memory-to-prompt orchestration decision
- 5d04658  feat(cognition): add runner-local memory prompt context
           — landed the dormant runner-local memory_context_text seam below run_turn.
```

This frame adds **no commit-bearing source change** beyond itself and its §0 pointer.

## 3. The exact decision question (Codex-approved, verbatim)

> May candidate 6 be implemented in a later code+tests slice by adding an optional
> runner-local `memory_context_text` parameter to `AgentRunner.run_turn(...)` and adding a new
> internal non-endpoint same-turn memory-orchestration caller that calls `assemble_context(...)`,
> derives bounded read-only memory text from `AssembledContext.assembled_text`, and invokes
> authoritative `AgentRunner.run_turn(...)` in the same turn, while preserving every current
> fence; or must the lane remain HOLD?

## 4. Non-authorization / allowed scope

```text
ALLOWED:
- docs-only implementation-proposal frame;
- name exact files/functions to change ON PAPER;
NOT AUTHORIZED by this frame:
- code;            - tests;           - wiring;
- runtime behavior change;            - endpoint/API/schema/public-surface change;
- implementation authorization of any kind.
```

## 5. Source re-survey (current source, re-verified at edge `12148dc`)

### 5.1 `torment_service/agent_loop.py`

```text
- run_turn(self, workspace_id, agent_id, observation, step, *,
           audit_admitted_context_items=None) -> TurnResult            [L503-511]
    · CONFIRMED: run_turn does NOT accept memory_context_text (only the audit-staging kw).
    · its single Phase-6 call is self._execute_with_prompt_request(frame=..., mode=...,
      action=...) with NO memory_context_text                          [~L601-606]
- THE DORMANT SEAM ALREADY EXISTS BELOW run_turn:
    · _execute(..., *, _prompt_request_capture=None, _memory_context_text=None)  [L792-799]
        builds the request via _build_llm_prompt_request(..., memory_context_text=
        _memory_context_text) on ANSWER [L845] and USE_TOOL [L887].
    · _execute_with_prompt_request(..., *, memory_context_text=None)   [L1036-1056]
        forwards _memory_context_text=memory_context_text into _execute.
    · _build_llm_prompt_request(..., *, tools, memory_context_text=None) [L1064-1090]
        when non-empty, prepends ONE bounded labelled guidance message before the raw user
        input; _build_system_prompt unchanged.
    · _build_memory_context_message(memory_context_text)               [L1092-1115]
        None/non-str/empty/whitespace -> None; else stripped, capped at 1200 with a truncation
        marker, prefixed with the read-only guidance label; turn-local; not stored on self;
        not exposed; drives no review/output/retry/ranking/style/write/persistence/retrieval.
- CONFIRMED: agent_loop.py references NO assemble_context / AssembledContext /
  retrieval_assembler (grep negative) — AgentRunner owns no governed assembled context.
```

### 5.2 `torment_service/retrieval_assembler.py`

```text
- imports only stdlib (math, dataclasses, typing)                      [L22-26]
- class AssembledContext: assembled_text: str = ""                     [L77-83]
- def assemble_context(...): builds assembled_text [L546], returns AssembledContext [L557]
- CONFIRMED: no AgentRunner / run_turn / llm_client / generation. Read-only context-source.
```

### 5.3 `torment_service/app.py`

```text
- @app.post("/agent/query"); def query(req)                            [L907-908]
- from .retrieval_assembler import assemble_context ...                 [L1319]
- @app.post("/retrieve"); def retrieve_assembled(req)                  [L1341-1342]
- CONFIRMED: the module references NO AgentRunner and NO run_turn (grep negative);
  assemble_context is called only inside the /retrieve handler.
- /agent/query behavior is NOT part of this proposal; /retrieve remains endpoint/context-source
  terrain only; the proposed orchestrator consumes assemble_context(...) as a FUNCTION, never
  via the /retrieve endpoint.
```

### 5.4 `torment_service/audit_private_generation_owner.py` — NEGATIVE terrain (unchanged)

```text
- class PrivateGenerationOwner [L63]; __init__(self, assembled_context, generation_boundary)
  [L70-72]; run(self, user_input) calls self._gen.complete(...) [L83].
- CONFIRMED: its generation is its OWN boundary, NOT the authoritative AgentRunner (no
  run_turn). Remains excluded / unwired / not authoritative.
```

### 5.5 `torment_service/audit_selected_items_runner_bridge.py` — NEGATIVE terrain (unchanged)

```text
- run_turn_with_selected_items_observation(runner, assembled_context, ...) [L53]
  calls runner.run_turn(..., audit_admitted_context_items=selected_items)  [L73-78];
  "called nowhere in production (observation-only)" [L44].
- CONFIRMED: passes audit_admitted_context_items, NEVER memory_context_text. Remains negative
  terrain only.
```

## 6. Proposed later code-change shape (ON PAPER — no code authorized)

```text
CHANGE A — parameter threading in agent_loop.py (two edits, no new behavior by default):
  A1. run_turn(...) signature gains an optional KEYWORD-ONLY memory_context_text:
      Optional[str] = None (placed after audit_admitted_context_items).
  A2. run_turn's single Phase-6 call passes it through:
      self._execute_with_prompt_request(frame=..., mode=..., action=...,
                                        memory_context_text=memory_context_text).
  · NOTHING BELOW run_turn changes — _execute_with_prompt_request / _execute /
    _build_llm_prompt_request / _build_memory_context_message ALREADY accept and thread the
    parameter (the dormant seam landed in 5d04658). A1+A2 are the ONLY agent_loop.py edits.
  · memory_context_text is NOT stored on self and NOT placed on TurnResult / ExecutionOutcome /
    metadata / logs / endpoints / schemas / persistence / any public payload.
  · DEFAULT-PRESERVING: when memory_context_text is absent / None / non-str / empty / whitespace,
    behavior is byte-identical to today's memory-blind run_turn (the seam already omits it).

CHANGE B — a NEW internal, non-endpoint orchestrator module (proposed name, on paper):
  torment_service/memory_context_orchestrator.py  (illustrative; finalized in the slice)
  · A plain internal function/class, e.g.
      run_turn_with_memory_context(runner, *, assembled_context | assemble_params, ...)
    that, in ONE turn:
      B1. owns assembly — calls assemble_context(...) [retrieval_assembler] as a FUNCTION, or
          receives a caller-owned AssembledContext, to obtain AssembledContext.assembled_text;
      B2. derives a BOUNDED, read-only memory text ONLY from assembled_text (or a bounded
          derivative) — governed assembled content only;
      B3. invokes authoritative runner.run_turn(..., memory_context_text=<bounded text>)
          for that same turn.
  · The ORCHESTRATOR module (not agent_loop.py) holds the assemble_context / AssembledContext
    import, so AgentRunner stays free of retrieval/assembly imports.
  · DORMANT-BY-DEFAULT landing (mirrors 5d04658 and PrivateGenerationOwner): the code+tests
    slice lands CHANGE A + CHANGE B as test-called / called-nowhere-in-production. LIVE
    PRODUCTION WIRING of the orchestrator's entrypoint is a SEPARATE later gate, not part of
    the code+tests slice and not authorized here. This keeps the slice itself free of any
    endpoint / runtime behavior change.
```

## 7. Exact files/functions proposed on paper

```text
MODIFY  torment_service/agent_loop.py
  · AgentRunner.run_turn(...)          — add keyword-only memory_context_text=None [sig L509-511]
  · AgentRunner.run_turn(...) body     — pass memory_context_text into the single
                                         _execute_with_prompt_request(...) call [~L601-606]
  · NO other edit; the seam (_execute_with_prompt_request L1036, _execute L792,
    _build_llm_prompt_request L1064, _build_memory_context_message L1092) is UNCHANGED.

ADD     torment_service/<memory_context_orchestrator>.py  (proposed name, on paper)
  · internal non-endpoint same-turn caller: assemble_context(...) -> bounded read-only text
    from AssembledContext.assembled_text -> runner.run_turn(..., memory_context_text=...).

UNCHANGED (explicitly named, must not be touched):
  · torment_service/retrieval_assembler.py  (assemble_context / AssembledContext stay as-is)
  · torment_service/app.py  (/agent/query, /retrieve, retrieve_assembled — behavior untouched)
  · torment_service/audit_private_generation_owner.py  (PrivateGenerationOwner stays excluded)
  · torment_service/audit_selected_items_runner_bridge.py  (audit bridge stays excluded)
  · AgentRunner._build_system_prompt(...), _LLMPromptRequest, TurnResult, ExecutionOutcome
```

## 8. Required test/source guards for the later code+tests slice (same slice)

```text
- valid memory-context inclusion (non-empty -> exactly ONE bounded labelled guidance message
  BEFORE the raw user input);
- empty/invalid memory-context omission (None / non-str / empty / whitespace -> no message);
- default memory-blind behavior unchanged (run_turn without memory_context_text -> byte-identical
  messages to today);
- _build_system_prompt(...) unchanged;
- raw user input remains its own SEPARATE and LATER message;
- truncation/bounding preserved (<=1200 chars + truncation marker);
- NO exposure of memory_context_text on TurnResult / ExecutionOutcome / metadata / logs /
  endpoints / schemas / persistence / public payloads (source + AST guards);
- AgentRunner owns NO assembly imports (grep/AST guard: agent_loop.py has no assemble_context /
  AssembledContext / retrieval_assembler);
- NO endpoint/app/schema behavior change (app.py /agent/query and /retrieve unchanged; AST guards);
- NO PrivateGenerationOwner route (orchestrator does not import/call it; owner stays unwired);
- NO selected-items audit bridge / U1 route (orchestrator passes memory_context_text, NOT
  audit_admitted_context_items; bridge unchanged);
- NO memory write/persistence;
- NO retrieval-authority expansion (orchestrator consumes existing assemble_context; no new
  store/write/authority);
- NO output-control/review/suppression/retry/ranking/style steering;
- NO hidden finalizer/refusal/identity rewrite;
- NO hidden chain-of-thought storage or exposure.
```

## 9. Candidate-failure conditions (candidate 6 FAILS before any code if the shape requires any of)

```text
- an endpoint behavior change;
- /retrieve becoming generation terrain;
- /agent/query becoming the live implementation path;
- AgentRunner owning retrieval/assembly;
- raw hits / audit / private / unadmitted / substrate-only content as the memory source;
- public exposure of memory context;
- memory writes / persistence;
- retrieval-authority expansion;
- output-control / review / suppression / retry / ranking / style steering;
- inability to define an internal entrypoint without crossing fences.

ASSESSMENT against the §6 shape: NONE is required. The shape adds an optional param + a new
internal non-endpoint module landed DORMANT (test-called); consumes assemble_context as a
function (/retrieve untouched, not generation terrain); leaves /agent/query untouched (not the
live path); keeps AgentRunner free of assembly imports (the orchestrator owns assembly);
derives memory text ONLY from governed assembled_text; exposes nothing publicly; writes no
memory; expands no retrieval authority; steers no output; and DOES define a fence-preserving
internal entrypoint (the orchestrator function itself, dormant by default). Therefore candidate
6 does NOT trip any failure condition at the proposal level.
```

## 10. Forbidden crossings (this step)

```text
- no code            - no tests             - no wiring
- no runtime behavior change
- no endpoint/API/schema/public-surface change
- no implementation authorization
- no retrieval-authority expansion
- no memory write/persistence
- no review/output-control/suppression/retry/ranking/style steering
- no U1/audit-owner reopening
- no PrivateGenerationOwner
- no Gate D/private cognition/dream/Envelope Audit runtime
- no database/substrate/carrier/schema/storage/migration
- no Gate B/R-field/Probe-v1/shaping
- no hidden finalizer/refusal/identity rewrite
- no hidden chain-of-thought storage or exposure
```

This document proposes a patch shape on paper only. Nothing above is coded, tested, wired, or
authorized.

## 11. Final verdict

**PASS to a later, separately authorized code+tests same-slice — conditional, no code now.**
Candidate 6 **may** proceed to a later code+tests slice **if and only if** that slice realizes
the §6 shape while preserving every fence: CHANGE A is the two-edit optional keyword-only
`memory_context_text` threaded only into the existing dormant seam (default-preserving,
unexposed, not on `self`); CHANGE B is a new internal non-endpoint orchestrator that owns
assembly via `assemble_context(...)`, derives bounded read-only text from
`AssembledContext.assembled_text`, and invokes authoritative `AgentRunner.run_turn(...)` — both
landed **DORMANT / test-called**, with the orchestrator's live production wiring deferred to a
**further separate gate**. `/agent/query` and `/retrieve` stay untouched; `AgentRunner` stays
free of assembly imports; `PrivateGenerationOwner` and the audit bridge stay excluded. The §9
assessment confirms the shape trips **no** failure condition. **This frame authorizes no code,
no tests, and no wiring; the later code+tests same-slice is admissible only under separate
Hilmir + Codex authorization, and live production wiring remains a still-further separate gate.
The live-caller / implementation / runtime lane remains HOLD until then.**

## 12. Anti-drift footer

TORMENT — MEMORY-TO-PROMPT-FOR-GENERATION SAME-TURN DUAL-OWNERSHIP CALLER IMPLEMENTATION-PROPOSAL
FRAME / DOCS-ONLY / NON-AUTHORIZING / NO LANE OPENED / FENCE CLOSED / SEAM DORMANT. It re-surveys
current source at edge `12148dc` (run_turn [L503-511] still lacks memory_context_text; the
dormant seam `_execute_with_prompt_request → _execute → _build_llm_prompt_request →
_build_memory_context_message` already exists below run_turn, bounded ≤1200 / labelled /
read-only / turn-local / non-exposed; AgentRunner references no assemble_context /
AssembledContext / retrieval_assembler; retrieval_assembler is stdlib-only read-only
context-source; app.py /agent/query + /retrieve hold no AgentRunner / run_turn;
PrivateGenerationOwner calls its own generation_boundary.complete, not AgentRunner; the
selected-items bridge passes audit_admitted_context_items, never memory_context_text, called
nowhere) and proposes, ON PAPER, the candidate-6 code shape: CHANGE A = add an optional
keyword-only `memory_context_text` to run_turn threaded only into the existing seam
(default-preserving, unexposed, not on `self`); CHANGE B = a new internal non-endpoint
orchestrator module that owns assembly (assemble_context → bounded read-only derivative of
assembled_text) and invokes authoritative run_turn — both landed DORMANT / test-called, with
live production wiring a further separate gate. It names the required same-slice tests/guards
and the candidate-failure conditions, and finds the shape trips none. **Verdict: PASS to a
later separately authorized code+tests same-slice IFF all fences are preserved — it authorizes
no code, no tests, no wiring, no runtime behavior change, and no endpoint/API/schema/public
surface change; AgentRunner stays runner-local and free of assembly; /retrieve stays
read-only/context-source; /agent/query is untouched; PrivateGenerationOwner and the audit
bridge stay excluded; the implementation/runtime lane remains HOLD until separately
authorized.** Guidance not control; audit observes authority and does not become authority;
nothing rewrites identity / canon / seed / soul.

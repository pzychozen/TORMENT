# TORMENT — Memory-to-Prompt-for-Generation Live-Caller Eligibility Frame v0.1

## 1. Status / non-authorization

**Live-caller eligibility frame. Docs-only / NON-AUTHORIZING / no lane opened. The
memory-to-prompt fence stays closed; the runner-local `memory_context_text` seam stays
dormant.** Hilmir authorized **only this inspection frame**. It inspects whether any
existing source site is already eligible to become the live caller for the dormant
`AgentRunner` `memory_context_text` seam. It **selects no caller**, **wires nothing**,
writes **no code and no tests**, makes **no endpoint / API / schema / public-surface
change**, and **invents no orchestration site**. Where this frame and any parent
contract/guard differ, the contract/guard wins.

Standing posture carried verbatim:

> Memory may shape context. Memory may not seize authority.
> Audit observes authority. Audit must not become authority.

Anchor: `8540dca` (repo edge). Subordinate to, and may not contradict: the
memory-to-prompt decision frame, design frame, the source-baseline lock + correction
(`tests/test_memory_to_prompt_generation_boundary_characterization.py`), the
implementation-proposal frame, the candidate proof-contract lock
(`tests/test_memory_to_prompt_candidate_proof_contract.py`), the production
implementation proposal, the landed dormant slice (`5d04658`), the caller-owned
same-turn provenance contract, and the PW-1…PW-8 pre-wiring guard.

## 2. Current implemented seam (source-verified)

`5d04658` landed the **first production prompt-path slice** — a dormant, optional,
runner-local `memory_context_text` seam inside `AgentRunner`:

```text
- `AgentRunner.run_turn(...)` builds its frame from `observation.text` via
  `self.controller.deliberate_only(raw_input=observation.text, ...)` and calls
  `self._execute_with_prompt_request(frame=..., mode=..., action=...)` — with NO
  `memory_context_text` argument.
- `_execute_with_prompt_request(..., *, memory_context_text=None)` forwards into
  `_execute(..., _memory_context_text=memory_context_text)`.
- `_execute(..., _memory_context_text=None)` forwards into
  `_build_llm_prompt_request(..., memory_context_text=_memory_context_text)` on both the
  ANSWER and USE_TOOL paths.
- `_build_llm_prompt_request(..., *, tools, memory_context_text=None)` calls
  `_build_memory_context_message(memory_context_text)`; a VALID context becomes ONE
  bounded, labelled, read-only guidance message placed BEFORE the raw user input
  (`messages`), the raw user input remaining its own later message.
- `_build_memory_context_message(...)` strips the text, omits empty/whitespace/non-string,
  caps it at 1200 chars with a truncation marker, and prefixes the read-only guidance
  label. `_build_system_prompt(...)` and `_LLMPromptRequest` are unchanged;
  `_LLMPromptRequest` stays runner-local.
```

**Dormant by default: no live caller passes `memory_context_text`.** `run_turn(...)` does
not pass it; `app.py` / `/agent/query` is not wired; the seam is exercised only by tests.
Live caller wiring remains separately unauthorized.

## 3. Eligibility rule

A live-caller candidate is **eligible only if an existing source site already owns BOTH,
in the same turn**:

```text
1. GOVERNED ASSEMBLED MEMORY CONTEXT
   - specifically eligible `assembled_text` (or a bounded derivative of it) produced
     through existing governed read/assembly paths; AND
2. AUTHORITATIVE AgentRunner GENERATION INVOCATION
   - specifically a path that can pass `memory_context_text` into the dormant
     runner-local seam (i.e. it invokes `AgentRunner` generation for that same turn).
```

If **no** existing source site owns both halves in one turn, this frame must say so and
**HOLD**. A site that owns only one half is **not** eligible. Producing context is not
the same as invoking generation; invoking generation is not the same as owning governed
assembled context. **No orchestration site may be invented to bridge the two.**

## 4. Terrain inventory (source-verified)

For each allowed terrain, what it owns (✓) and does not own (✗) of the two required
halves:

```text
SITE                                           | governed assembled_text | AgentRunner generation invocation
-----------------------------------------------+-------------------------+----------------------------------
AgentRunner.run_turn / _execute (agent_loop.py)| ✗ (frame = observation  | ✓ (calls _execute_with_prompt_
                                               |    .text only; no        |    request → _execute →
                                               |    assemble_context /    |    _complete_llm_prompt_request →
                                               |    AssembledContext)     |    llm_client.complete)
_build_llm_prompt_request / _build_memory_     | ✗                       | seam owner (consumes the optional
context_message (agent_loop.py)                |                         |    memory_context_text), NOT a caller
/agent/query (app.py)                          | ✗ (returns fabric.query; | ✗ (no AgentRunner / run_turn)
                                               |    no assembled_text)    |
/retrieve · retrieve_assembled (app.py)        | ✓ (fabric.query +        | ✗ (no AgentRunner / run_turn /
                                               |    assemble_context →    |    llm_client.complete)
                                               |    assembled_text)       |
assemble_context / AssembledContext            | ✓ (produces             | ✗ (imports only stdlib; no
(retrieval_assembler.py)                       |    assembled_text)       |    AgentRunner / generation)
```

No row owns **both** columns. (Negative terrain in §8.)

## 5. `agent_loop.py` assessment

```text
- AgentRunner OWNS authoritative generation: run_turn → _execute_with_prompt_request →
  _execute → _complete_llm_prompt_request → self.llm_client.complete(...).
- AgentRunner OWNS the dormant memory-context seam: the optional runner-local
  `memory_context_text` threaded through _execute_with_prompt_request / _execute /
  _build_llm_prompt_request into one bounded labelled guidance message.
- AgentRunner does NOT own governed assembled context today: run_turn builds the frame
  from `observation.text` via controller.deliberate_only(...); there is no
  assemble_context / AssembledContext / assembled_text anywhere in run_turn or the
  prompt-request path. It has no governed assembled_text to pass into its own seam.
- run_turn(...) does NOT pass `memory_context_text` (the seam stays dormant); the
  pre-existing `audit_admitted_context_items` keyword is a separate audit-staging field
  routed ONLY to TurnResult, never into the prompt path.
```

So `AgentRunner` owns one half (generation + seam) but not the other (governed assembled
context). It cannot, by itself, be the eligible live caller.

## 6. `app.py` assessment

```text
- /agent/query (`query`): may run ThinkingController to produce a MemoryPlan, then
  returns `fabric.query(...)`. It does NOT call AgentRunner / run_turn and does NOT
  produce `assembled_text`. It owns retrieval + MemoryPlan shaping only — neither
  required half.
- /retrieve (`retrieve_assembled`): runs `fabric.query(...)` + archive retrieval +
  `assemble_context(...)` and returns the assembled context. It OWNS governed assembled
  context (`assembled_text`) but does NOT invoke AgentRunner generation (no AgentRunner /
  run_turn / llm_client.complete in the handler).
- `app.py` imports `assemble_context` but never imports or instantiates `AgentRunner`;
  no app endpoint owns BOTH assembled memory context and same-turn AgentRunner
  generation.
```

`app.py` / `/agent/query` is **inspection terrain only — not selected here**. Choosing any
app endpoint as a future live caller would require an endpoint / public-surface /
orchestration change (e.g. an endpoint that both assembles context and invokes
`AgentRunner` generation in one turn). **That is a separate future decision, not an
authorization, and is not made in this frame.**

## 7. `retrieval_assembler.py` assessment

```text
- `AssembledContext.assembled_text` is the eligible source terrain (the governed
  assembled context the seam's proposal named).
- `assemble_context(...)` builds `assembled_text` and returns an `AssembledContext`. The
  module imports only stdlib (`math`, `dataclasses`, `typing`); it contains no
  `AgentRunner`, no `run_turn`, no `llm_client.complete`, and no generation invocation.
- The assembler therefore owns CONTEXT PRODUCTION only. It owns no generation invocation.
```

The assembler **must not be treated as a live caller merely because it produces context.**
Producing `assembled_text` is the first half of eligibility, never the second.

## 8. Negative terrain

```text
- `audit_selected_items_runner_bridge.py`
  (`run_turn_with_selected_items_observation(runner, assembled_context, ...)`):
  extracts `selected_admitted_items(assembled_context)` and passes them as
  `audit_admitted_context_items=` into `run_turn(...)`. This is AUDIT OBSERVATION-ONLY
  staging — it passes audit item dicts, NEVER `memory_context_text`, and routes nothing
  into the prompt path. It is called NOWHERE in production. It is not a memory
  prompt-context caller and selecting it would not feed the seam.

- `audit_private_generation_owner.py` / `PrivateGenerationOwner`: a SEPARATE owner that
  holds its own `assembled_context` + `generation_boundary`, renders its OWN prompt, and
  calls `observe_prompt_inclusion_packet(...)`. It remains EXCLUDED — unwired /
  test-called — and is NOT the authoritative `AgentRunner` path.
```

Using either as the live caller would risk **reopening U1 / audit-owner / dual-ownership
by implication** (the bridge wires the audit-staging seam; the owner is a parallel
non-authoritative generator). Both are out of bounds for feeding the runner-local
`memory_context_text` seam.

## 9. Eligibility conclusion

**No existing source site is eligible as the live caller.** Across the inspected terrain,
the two required halves are owned by **disjoint** sites in any given turn:

```text
- governed assembled context (`assembled_text`) is owned by `/retrieve` +
  `assemble_context(...)` — which do NOT invoke AgentRunner generation;
- authoritative AgentRunner generation (+ the dormant `memory_context_text` seam) is
  owned by `AgentRunner.run_turn` / `_execute` — which do NOT own governed assembled
  context.
```

No current site owns **both** halves in the same turn, so **there is no existing eligible
live caller.** This matches the earlier disjoint-ownership characterizations (`206c5c3`,
`f04b319`). No candidate is selected here; this frame opens no caller.

## 10. Required next gate

```text
- Because no eligible caller exists today, the move is HOLD — or, if pursued, a
  SEPARATELY FRAMED orchestration / caller-design decision that explicitly answers WHO
  owns both halves in one turn and HOW, under Codex/Hilmir review.
- This frame does NOT invent that site. A future live caller would require a new
  same-turn dual-ownership orchestration, which is itself a separate framed decision (it
  would touch endpoint / public-surface / orchestration shape — not authorized here).
- Only AFTER such a site is framed and approved could a separately authorized
  LIVE-CALLER-PROPOSAL (and later, code + tests together) follow. No code is authorized
  by this frame.
```

## 11. Forbidden crossings (this step)

```text
- no code, tests, wiring, or caller selection
- no endpoint / API / schema / public-surface change
- no retrieval-authority expansion
- no memory write / persistence
- no review / output-control / suppression / retry / ranking / style steering
- no U1 / audit-owner reopening
- no PrivateGenerationOwner wiring
- no dual-ownership orchestration unless separately framed later
- no Gate D / private cognition / dream / Envelope Audit runtime
- no database / substrate / carrier / schema / storage / migration
- no Gate B / R-field / Probe-v1 / shaping slice
```

This document inspects caller terrain only. Nothing above is selected, wired, or
authorized.

## 12. Anti-drift footer

TORMENT — MEMORY-TO-PROMPT-FOR-GENERATION LIVE-CALLER ELIGIBILITY FRAME / DOCS-ONLY /
NON-AUTHORIZING / NO LANE OPENED / FENCE CLOSED / SEAM DORMANT. It records the current
implemented seam (`5d04658`: a dormant optional runner-local `memory_context_text` through
`_execute_with_prompt_request → _execute → _build_llm_prompt_request →
_build_memory_context_message`, one bounded labelled guidance message before the raw user
input, ≤1200 stripped chars, `_build_system_prompt` / `_LLMPromptRequest` unchanged and
runner-local), states the eligibility rule (same-turn dual ownership: governed
`assembled_text` AND authoritative AgentRunner generation invocation), and inventories the
allowed terrain from source: `AgentRunner.run_turn` / `_execute` own generation + the
dormant seam but NOT governed assembled context (frame = `observation.text`); `/agent/query`
owns retrieval + MemoryPlan only; `/retrieve` + `assemble_context` own governed
`assembled_text` but NOT generation; `retrieval_assembler` produces context with no
generation invocation; the audit bridge passes `audit_admitted_context_items` (never
`memory_context_text`) and is called nowhere; `PrivateGenerationOwner` stays
excluded/unwired/non-authoritative. **Conclusion: generation ownership and
assembled-context ownership are disjoint — no existing source site owns both halves in one
turn — so no existing live caller is eligible; HOLD.** Any future live caller requires a
separately framed same-turn dual-ownership orchestration/caller-design decision under
Codex/Hilmir review, then a separately authorized live-caller proposal, then code + tests
together. **It selects no caller, wires nothing, writes no code/tests, changes no
endpoint/API/schema/public surface, invents no orchestration site, opens no lane, and
lifts no fence.** Guidance not control; audit observes authority and does not become
authority; nothing rewrites identity / canon / seed / soul.

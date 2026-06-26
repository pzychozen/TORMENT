# TORMENT Audit — Exact Prompt-Request Carry-Through Tests-Only Characterization Proposal v0.1

## 0. Status / authorization scope

**Docs-only PROPOSAL. NON-AUTHORIZING.** It proposes the shape of a *future*
tests-only characterization for exact-request carry-through. **Landing this proposal
authorizes no actual tests and no production code.** It writes no test, edits no
production source, resolves no W-7, selects no Shape B, and wires / imports / calls /
constructs no `PrivateGenerationOwner`. It changes no prompt surface, adds no
endpoint / API / schema, and opens no memory write, retrieval feedback, output
control, Gate A / Gate D, database / substrate, or private-cognition path.

**Any actual test implementation requires separate Hilmir authorization plus Codex
review.** This is a proposal for what such a tests-only characterization would
prove — not permission to write it.

Standing posture carried verbatim:

> Memory may shape context. Memory may not seize authority.
> Audit observes authority. Audit must not become authority.

Anchor: `dc9799f` (origin/main; private owner refactor frame pointer corrected).

## 1. Subordination

Subordinate to, and may not contradict:

```text
docs/TORMENT_AUDIT_PRIVATE_OWNER_W1_W8_LIVE_OWNER_REFACTOR_PROPOSAL_FRAME_v0.1.md   (the W-1…W-8 frame; W-7 unresolved; owner unwired)
docs/TORMENT_AUDIT_PRIVATE_OWNER_LIVE_WIRING_DECISION_FRAME_v0.1.md                (verdict + W-1…W-8 gate)
docs/TORMENT_AUDIT_PRIVATE_OWNER_LIVE_WIRING_GATE_FRAME_v0.1.md                    (§5 proof shape, §6 stop rule)
torment_service/agent_loop.py                                                     (the live topology)
the current guards: pre-wiring guard; handoff-boundary; live-owner inventory / path-selection; audit packet sink / staging; prompt-request extraction
```

Where this proposal and any contract appear to differ, the contracts win.

## 2. Doctrine filter

> A proposal for a future test names what that test would prove and what it must not
> cross. It writes no test and crosses nothing. A tests-only characterization
> observes source; it does not implement the refactor it characterizes.

## 3. Scope (named terrain; nothing implemented)

```text
Source symbols in scope (read-only terrain):
  torment_service/agent_loop.py::AgentRunner._execute(...)
  torment_service/agent_loop.py::AgentRunner._execute_with_prompt_request(...)
  torment_service/agent_loop.py::_ExecutionWithPromptRequest
  torment_service/agent_loop.py::_LLMPromptRequest
  torment_service/agent_loop.py::AgentRunner._complete_llm_prompt_request(...)

Future possible test file (PROPOSED TERRAIN ONLY — not created, not authorized):
  tests/test_audit_exact_prompt_request_carry_through_characterization.py
```

The test file name is recorded as proposed terrain only. This proposal does not
create it, and naming it authorizes nothing.

## 4. What the future tests-only characterization would establish

A future, separately-authorized tests-only characterization would record / lock the
following. Points 1 and 3–10 are current facts it would CHARACTERIZE and lock as
carry-forward guards; point 2 is the proof TARGET a later carry-through refactor's
own tests would have to add (carry-through is not implemented today, so the
characterization records it as an obligation, not a present fact).

```text
1. CURRENT GAP / TERRAIN.
   _execute_with_prompt_request(...) currently RECONSTRUCTS the prompt request after
   _execute(...) returns (via _build_llm_prompt_request(frame, mode, tools=None) when
   outcome.llm_called); exact-object carry-through is NOT implemented today.

2. EXACT-REQUEST PROOF TARGET (future obligation, recorded not proven now).
   A future refactor would need `_ExecutionWithPromptRequest.prompt_request` to carry
   the SAME `_LLMPromptRequest` built before `_complete_llm_prompt_request(...)` in
   `_execute` — the exact object sent to the model — NOT a post-execution
   reconstruction. The characterization records this as the carry-through proof
   target; it does not implement or pre-assert it.

3. PROMPT-SURFACE NO-CHANGE.
   Same system_prompt, messages, and tools: still _build_system_prompt(frame, mode)
   and messages = [{"role": "user", "content": frame.raw_input}], with the explicit
   tools argument only (None on ANSWER, [signature_spec] on USE_TOOL). The model sees
   exactly what it sees today.

4. NO PROMPT EXPOSURE.
   The prompt request (or its fields) must not appear on TurnResult, ExecutionOutcome,
   metadata, logs / debug, endpoint, schema, API, persistence, or `self` state.

5. PACKET REMAINS INERT.
   `_audit_evidence_packet` drives no branch (no If / While / conditional test) and
   routes only into TurnResult(...).

6. OBSERVATION REMAINS DOWNSTREAM.
   `observe_prompt_inclusion_packet(...)` stays confined downstream inside
   `_observe_audit_evidence_from_prompt_request(...)`, called only from run_turn after
   generation + final reviewed response — never inside _execute / the generation path.

7. OWNER REMAINS UNWIRED.
   `PrivateGenerationOwner` stays unwired and unconstructed in production (no import /
   call / construction from agent_loop.py or any service module).

8. APP.PY / ENDPOINTS REMAIN NON-CALLERS.
   app.py and public endpoints do not own generation + assembled context and are not
   callers of the runner ownership paths or of PrivateGenerationOwner.

9. NO FORBIDDEN REACHABILITY.
   No writer, memory, persistence, retrieval, Gate A carrier/admission/promotion,
   Gate D / private-cognition, database / substrate, review / output-control,
   retry / ranking / suppression / style path becomes reachable from the terrain.

10. FAIL-SOFT / ABSENCE-NON-PUNITIVE.
    Observer / builder failure yields None and no error path; packet absence remains
    non-punitive (no dishonesty / unsupportedness / suppression / retrieval / authority
    / memory meaning).
```

## 5. What this proposal does and does not do

```text
DOES:    name the read-only source terrain (§3); name the future possible test file as
         terrain only; record what a future tests-only characterization would establish
         (§4, points 1–10), including the exact-request proof TARGET (point 2) as a future
         obligation.

DOES NOT (and does not authorize by implication):
  - write or edit any test (incl. the named file); edit production code; run git
  - implement or pre-assert exact-request carry-through
  - resolve W-7; select Shape B; select a live owner wiring site
  - wire / import / call / construct PrivateGenerationOwner
  - change the prompt surface; add endpoint / API / schema
  - add memory writes, retrieval feedback, output control, Gate A / Gate D,
    database / substrate, or private cognition
  - claim that landing this proposal authorizes any actual tests or code
```

## 6. Gating and stop rule

```text
- The next admissible step would be the actual tests-only characterization (the §3
  file), which requires SEPARATE Hilmir authorization + Codex review before any test
  is written.
- That characterization, if authorized, lands tests/source-FIRST and must not weaken
  any existing guard, expose prompt material, make prompt text model-visible by audit
  path, or let packet output affect behavior — else it fails and nothing proceeds.
- The carry-through REFACTOR itself, and any live-owner wiring / W-7 resolution, are
  further separate gates beyond that characterization. None is opened here.
- Stable resting state remains valid: reconstruction in place, owner unwired, bridge
  dead-end, packet optional and observation-only.
```

## 7. Anti-drift footer

TORMENT AUDIT — EXACT PROMPT-REQUEST CARRY-THROUGH TESTS-ONLY CHARACTERIZATION
PROPOSAL / DOCS-ONLY / NON-AUTHORIZING. It proposes the shape of a future tests-only
characterization over the read-only terrain `AgentRunner._execute(...)` /
`_execute_with_prompt_request(...)` / `_ExecutionWithPromptRequest` / `_LLMPromptRequest`
/ `_complete_llm_prompt_request(...)`, naming the future possible test file
`tests/test_audit_exact_prompt_request_carry_through_characterization.py` as terrain
only. It records that such a characterization would lock the current gap (reconstruction
today, carry-through not implemented), the exact-request proof TARGET as a future
obligation, prompt-surface no-change, no prompt exposure, an inert packet, downstream
observation, an unwired `PrivateGenerationOwner`, non-caller endpoints, no forbidden
reachability, and fail-soft / non-punitive absence. **Landing this proposal authorizes
no actual tests and no production code; it resolves no W-7, selects no Shape B, wires no
owner, changes no prompt surface, and opens no endpoint / API / schema / memory /
retrieval / output-control / Gate A / Gate D / database / substrate / private-cognition
path. Any actual test implementation requires separate Hilmir authorization plus Codex
review.** Guidance not control; audit observes authority and does not become authority;
nothing rewrites identity / canon / seed / soul.

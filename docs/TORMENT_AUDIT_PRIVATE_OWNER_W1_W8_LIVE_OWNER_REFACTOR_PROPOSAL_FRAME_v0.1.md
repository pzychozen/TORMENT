# TORMENT Audit - Private Owner W-1..W-8 Live-Owner / Refactor Proposal Frame v0.1

## 0. Status / Authorization Scope

Docs-only proposal frame. This document answers the W-1..W-8 questions against
the current source terrain at `c0d8b1e` and proposes the next admissible proof
shape only. It authorizes no production code, no test edits, no live
`PrivateGenerationOwner` wiring, no prompt mutation, no endpoint / API / schema
surface, no memory write, no retrieval feedback, no output control, no Gate A /
Gate D / database / substrate movement, and no audit-as-control behavior.

Passing tests, satisfying this document, or landing this document does not
authorize wiring. Any movement from this frame into tests or code requires a
separate explicit Hilmir authorization plus Codex review under the decision
frame's W-1..W-8 gate.

Subordinate to:

```text
docs/TORMENT_AUDIT_PRIVATE_OWNER_LIVE_WIRING_DECISION_FRAME_v0.1.md
docs/TORMENT_AUDIT_PRIVATE_OWNER_LIVE_WIRING_GATE_FRAME_v0.1.md
docs/TORMENT_AUDIT_MODEL_VISIBLE_CONTEXT_OWNER_SEAM_DESIGN_v0.1.md
docs/TORMENT_AUDIT_CALLER_OWNED_SAME_TURN_PROVENANCE_CONTRACT_v0.1.md
torment_service/agent_loop.py
torment_service/audit_private_generation_owner.py
tests/test_audit_private_owner_pre_wiring_guard.py
tests/test_audit_private_owner_handoff_boundary_characterization.py
tests/test_audit_live_owner_path_selection_characterization.py
tests/test_audit_live_owner_candidate_inventory.py
```

Standing doctrine:

```text
Memory may shape context. Memory may not seize authority.
Audit observes authority. Audit must not become authority.
```

## 1. Current Source Facts

At `c0d8b1e`, the live runner terrain is:

```text
AgentRunner.run_turn(...)
  -> self._execute_with_prompt_request(frame, mode, action)
       -> self._execute(frame, mode, action)
            -> self._build_llm_prompt_request(frame, mode, tools=...)
            -> self._complete_llm_prompt_request(req)
                 -> self.llm_client.complete(
                        system_prompt=req.system_prompt,
                        messages=req.messages,
                        tools=req.tools,
                    )
       -> reconstructs prompt_request with _build_llm_prompt_request(..., tools=None)
          when outcome.llm_called
  -> review / ingest / stabilize complete
  -> self._observe_audit_evidence_from_prompt_request(
         _prompt_request,
         audit_admitted_context_items,
         final reviewed response_text,
     )
       -> observe_prompt_inclusion_packet(...)
  -> TurnResult(..., audit_evidence_packet=_audit_evidence_packet)
```

The two landed extraction seams are closed as behavior-preserving:

```text
AgentRunner._complete_llm_prompt_request(...)
  Thin model-call helper. Calls only self.llm_client.complete(...) with the
  captured request fields. It references no owner, audit packet, admitted item,
  assembler, writer, retrieval, endpoint, Gate A, Gate D, or control surface.

AgentRunner._observe_audit_evidence_from_prompt_request(...)
  Thin observation helper. Receives only the captured prompt request, caller-
  supplied admitted context items, and final reviewed response text. Calls only
  observe_prompt_inclusion_packet(...), fail-soft to None, and returns a packet
  only for the caller to place on TurnResult.audit_evidence_packet.
```

The current guards also prove:

```text
- PrivateGenerationOwner remains unwired in production.
- app.py and endpoint handlers do not own generation plus assembled context.
- The built audit packet value drives no branch and routes only to TurnResult.
- Prompt request material is not exposed on TurnResult, ExecutionOutcome,
  metadata, endpoint, schema, API, logs, or debug surfaces.
- AgentRunner does not import retrieval_assembler, selected_admitted_items,
  AssembledContext, candidate_types, database packages, Gate A carrier types,
  or Gate D / private-cognition entrypoints for this lane.
```

## 2. Proposal Question

The accepted Codex HOLD identified exactly one tempting next refactor:

```text
Make AgentRunner._execute_with_prompt_request(...) carry the exact
_LLMPromptRequest built inside AgentRunner._execute(...), instead of
reconstructing a request after _execute returns.
```

This document does not authorize that refactor. It classifies it as the exact
internal refactor terrain that a future source-first proposal would have to
prove before any live-owner wiring question can proceed.

This document does not select a live owner integration shape.

## 3. W-1 - Exact Internal Non-Endpoint Site

The exact internal refactor site is:

```text
torment_service/agent_loop.py::AgentRunner._execute_with_prompt_request(...)
torment_service/agent_loop.py::AgentRunner._execute(...)
torment_service/agent_loop.py::_ExecutionWithPromptRequest
```

The only admissible future refactor proposal in this terrain would make
`_ExecutionWithPromptRequest.prompt_request` carry the same `_LLMPromptRequest`
that was built for the model call and passed to `_complete_llm_prompt_request`.
It must remove the need for post-execution prompt reconstruction without changing
the prompt surface, the completion arguments, review behavior, ingest behavior,
tool behavior, exception behavior, or the public `TurnResult` surface.

The exact live wiring site is not selected here. In particular, this document
does not name any production caller that may invoke `PrivateGenerationOwner`,
does not change `audit_selected_items_runner_bridge.py`, and does not make
`app.py`, any endpoint, or `AgentRunner.run_turn(...)` a live owner.

Therefore W-1 is answered only for the internal refactor terrain. W-1 remains
unanswered for live owner invocation, and production owner wiring must remain
blocked until a later proposal names that site by source.

## 4. W-2 - Evidence-Only Ownership

A future exact-request carry-through refactor would remain evidence-only only if
all of the following stay true:

```text
- The prompt request is the already-existing model-call request.
- The request is kept private to the runner's execution/observation frame.
- The request is not returned, stored on self, logged, exposed, persisted, or
  surfaced on TurnResult / ExecutionOutcome / metadata / endpoint / schema / API.
- The request is not a carrier for selected admitted items, assembled context,
  audit packets, packet snippets, provenance flags, truth flags, or authority
  markers.
- AgentRunner still makes no same-turn provenance claim. The caller remains
  responsible for any admitted-context claim.
- The audit helper may observe only the request fields plus caller-supplied
  item dicts plus final reviewed response text, and may return only packet or
  None.
```

Evidence-only means the runner may preserve a private record of what was already
sent to the model boundary for the purpose of the existing observation sink. It
does not mean the audit layer can alter what is sent, influence what is returned,
or decide what is true.

## 5. W-3 / W-4 - Packet Output Cannot Steer

The packet must remain downstream and inert:

```text
- The packet is composed only after generation and final review produce a final
  response text.
- The packet is composed by _observe_audit_evidence_from_prompt_request(...) and
  observe_prompt_inclusion_packet(...), not by _execute(...) or
  _complete_llm_prompt_request(...).
- Packet presence or absence must not be read by review, retry, ranking,
  suppression, style steering, output selection, tool execution, retrieval,
  memory writes, ingest, fabric calls, gravity correction, Gate A, Gate D, or
  any authority path.
- _audit_evidence_packet must not appear in any If / While / conditional
  expression test.
- _audit_evidence_packet may route only into TurnResult(...).
- Observer or builder failure must yield None and no error path. Packet absence
  remains non-punitive and carries no dishonesty / unsupportedness / suppression
  meaning.
```

The response remains finalized independently of the packet. Review remains the
only existing suppressor in this runner path; audit evidence cannot become a
second suppressor.

## 6. W-5 - No Reachability By Implication

A future source-first refactor in this terrain must preserve or tighten the
current closed reachability shape:

```text
- No new import of audit_private_generation_owner from agent_loop.py.
- No construction or call of PrivateGenerationOwner in production.
- No import or call of selected_admitted_items, assemble_context,
  retrieval_assembler, AssembledContext, candidate_types, sqlite3, sqlalchemy,
  database/substrate packages, Gate A carrier/admission/promotion types, or Gate D
  / private-cognition entrypoints from the runner boundary.
- _execute(...), _complete_llm_prompt_request(...), and any exact-request
  carry-through helper must reach no writer / memory / persistence / retrieval /
  ranking / retry / suppression / style / review / endpoint / schema / API path.
- The selected-items bridge remains packet-blind and unwired except from tests.
- app.py and endpoint handlers remain non-callers of AgentRunner ownership paths
  and non-callers of PrivateGenerationOwner.
```

No writer, memory, retrieval feedback, Gate A, Gate D, database, substrate, or
private-cognition path may become reachable merely because the exact prompt
request is carried farther inside the private runner frame.

## 7. W-6 - Prompt Surface

The exact-request carry-through refactor, by itself, must not change the live
prompt surface.

The prompt surface remains:

```text
system_prompt = self._build_system_prompt(frame, mode)
messages = [{"role": "user", "content": frame.raw_input}]
tools = the explicit tools argument supplied by the ANSWER or USE_TOOL path
```

Any future proposal that causes selected admitted item text, assembled context,
packet snippets, provenance markers, truth flags, authority flags, or audit
evidence to become model-visible is a prompt-surface change. That question must
be explicitly named and separately gated under W-6. It cannot be bundled into an
"exact request carry-through" refactor and cannot be justified by passing tests.

If a live owner later needs selected item text to appear in the model-visible
context, that is not this refactor. It is a separate prompt-surface proposal.

## 8. W-7 - Integration Shape

This frame leaves the live integration shape unresolved.

It selects neither:

```text
1. PrivateGenerationOwner becomes the live generation path.
2. PrivateGenerationOwner runs beside the existing generation path.
```

Reason:

```text
- Option 1 may avoid duplicate generation, but it likely raises a separate W-6
  prompt-surface question if the owner renders selected context into what the
  model sees.
- Option 2 risks duplicate or divergent generation/output control unless it is
  proven not to create a second response, second review path, retry path, ranking
  path, style path, or hidden control edge.
- Shape B / private runner delegation remains deferred and separately
  unauthorized by the decision frame.
```

The exact-request carry-through terrain is a prerequisite-like internal
observation refactor candidate, not a live owner integration decision. Any later
proposal must resolve W-7 by source before production wiring.

## 9. W-8 - Required Tests / Source-First Proof Shape Before Wiring

Before any production wiring, a future authorized tests/source-first slice must
land proof at least as strict as the following. These are proposed proof
obligations only; this document does not create or edit tests.

Exact request carry-through proof:

```text
- Behavioral proof with a fake LLM / fake completion helper that the prompt
  request carried by _ExecutionWithPromptRequest is the request built for the
  model call on ANSWER.
- Equivalent proof for USE_TOOL, including tools=[signature_spec].
- Proof that no-model-call paths carry prompt_request=None.
- AST/source guard that _execute_with_prompt_request(...) does not reconstruct a
  prompt request after _execute(...) returns.
- AST/source guard that any request carrier is private and does not reach
  TurnResult, ExecutionOutcome, metadata, logs, debug, endpoint, schema, API,
  persistence, retrieval, writer, or self state.
```

Existing guard carry-forward:

```text
- complete(...) remains confined to _complete_llm_prompt_request(...), and that
  helper calls only self.llm_client.complete(...).
- _execute(...) may pass the request only to the completion helper or to the
  private exact-request carrier selected by the authorized refactor.
- _complete_llm_prompt_request(...) references no audit packet, admitted items,
  selected items, assembler, PrivateGenerationOwner, review, writer, retrieval,
  endpoint, Gate A, Gate D, ranking, retry, suppression, style, or output-control
  surface.
- observe_prompt_inclusion_packet(...) remains confined to
  _observe_audit_evidence_from_prompt_request(...), called only downstream from
  run_turn.
- _audit_evidence_packet drives no branch and routes only to TurnResult.
- PrivateGenerationOwner remains unwired unless the later proposal explicitly
  names and proves the live wiring site under W-1..W-8.
- app.py and public endpoints remain non-callers.
- Prompt shape remains pinned unless a separate W-6 prompt-surface proposal is
  explicitly authorized.
- No forbidden imports/calls appear for writer, memory, retrieval feedback,
  Gate A, Gate D, database, substrate, private cognition, endpoint, API, schema,
  review/output control, ranking, retry, suppression, or style steering.
- Fail-soft / absence-non-punitive packet behavior remains behaviorally proven.
```

If any proof requires weakening an existing guard, exposing prompt material,
making prompt text model-visible by audit path, or letting packet output affect
behavior, the proposal fails and the owner remains unwired.

## 10. Stop Rule

Stop and hold if any of the following is true:

```text
- The exact internal refactor site cannot carry the real request without prompt
  exposure or prompt mutation.
- The proposal needs AgentRunner to own retrieval, assembly, selected-item
  extraction, same-turn provenance, or AssembledContext.
- The packet or inclusion result would be read by any control path.
- W-7 remains unresolved for a proposed wiring slice.
- The live prompt surface would change without a separately authorized W-6
  prompt-surface proposal.
- app.py, an endpoint, a writer, retrieval feedback, Gate A, Gate D, database,
  substrate, or private cognition becomes reachable by implication.
- The source-first proof shape is skipped or weakened.
```

The stable resting state remains valid: owner unwired, bridge dead-end, packet
optional and observation-only.

## 11. Non-Authorization

This document does not authorize:

```text
- production code
- test edits
- live PrivateGenerationOwner wiring
- prompt mutation
- endpoint / API / schema changes
- memory writes, writer paths, persistence, database, or substrate
- retrieval feedback, ranking, retry, suppression, or style steering
- review/output control
- Gate A carrier / representation / admission / promotion / transform mechanics
- Gate D / private cognition / dream / Envelope Audit runtime
- same-turn provenance flags, truth flags, authority flags, or public evidence
  schema
- treating packet absence as punitive or meaningful
```

## 12. Anti-Drift Footer

TORMENT AUDIT - PRIVATE OWNER W-1..W-8 LIVE-OWNER / REFACTOR PROPOSAL FRAME /
DOCS-ONLY / NON-AUTHORIZING. Exact internal refactor terrain is named:
`AgentRunner._execute_with_prompt_request(...)`, `AgentRunner._execute(...)`, and
`_ExecutionWithPromptRequest` in `torment_service/agent_loop.py`, for a possible
future exact prompt-request carry-through proof. Live owner wiring site is not
selected. Integration shape W-7 is unresolved. Prompt-surface changes are
separately gated under W-6 and not bundled here. `PrivateGenerationOwner` remains
unwired; Shape B remains deferred; app.py and endpoints remain non-callers; the
packet remains optional, non-punitive, and control-blind; no writer / memory /
retrieval / Gate A / Gate D / database / substrate / private-cognition path is
opened. Passing tests or landing this document authorizes nothing.

# TORMENT Audit — Private-Owner Sidecar-Owner Shape Proposal v0.1

## 1. Title / status

**Sidecar-owner shape proposal. Docs-only / NON-AUTHORIZING. No implementation
authorized. No tests authorized.** This document determines only whether a
precondition-satisfying beside-generation audit-owner shape exists *on paper* before
the W-1 caller-path question could ever reopen. It selects no caller path, selects no
Shape B, authorizes no production or tests or live wiring, and wires / imports /
calls / constructs / modifies no `PrivateGenerationOwner`.

**Decision recorded here: OPTION B — no precondition-satisfying sidecar-owner shape
is proposed yet; HOLD is unchanged.** (See §5.)

**Subordinate to, and may not contradict:**

```text
docs/TORMENT_AUDIT_PRIVATE_OWNER_W7_SIDECAR_ONLY_DECISION_FRAME_v0.1.md            (W-7: owner-as-generation-path CLOSED)
docs/TORMENT_AUDIT_PRIVATE_OWNER_SIDECAR_CALLER_PATH_DECISION_FRAME_v0.1.md        (W-1 caller-path: Option A / HOLD — none selected)
docs/TORMENT_AUDIT_PRIVATE_OWNER_SIDECAR_OWNER_SHAPE_PRECONDITION_FRAME_v0.1.md    (preconditions any future sidecar-owner shape must satisfy)
```

Where this document and any parent frame / contract / guard appear to differ, the
parent / contract / guard wins. This document narrows; it relaxes nothing.

Standing posture carried verbatim:

> Memory may shape context. Memory may not seize authority.
> Audit observes authority. Audit must not become authority.

Anchor: `d26a9f2` (HEAD; precondition §0 pointer recorded). Substantive precondition
artifact: `f4d7118`.

## 2. Scope

```text
DETERMINES:
  - ONLY whether a precondition-satisfying beside-generation sidecar-owner shape
    exists on paper (Option A names one; Option B concludes none yet).

DOES NOT:
  - Reopen or select the W-1 caller path.
  - Select Shape B (private runner delegation seam).
  - Authorize production, tests, or live wiring.
  - Reopen the exact prompt-request carry-through or packet semantics.
```

This is a paper-only existence question, not a design and not a wiring step. "Does a
safe exact shape exist on paper?" — nothing more.

## 3. Closed constraints carried forward

```text
- W-7 sidecar-only remains CLOSED; owner-as-generation-path remains FORBIDDEN.
- The existing AgentRunner generation path remains AUTHORITATIVE:
  AgentRunner._execute(...) builds the request and calls the model boundary via
  AgentRunner._complete_llm_prompt_request(...); AgentRunner.run_turn(...) carries
  the request to the downstream observer.
- Exact prompt-request carry-through remains OBSERVATION terrain only, NOT a control
  hook: AgentRunner._execute_with_prompt_request(...) reads back the SAME
  _LLMPromptRequest object _execute built (paired in _ExecutionWithPromptRequest);
  the capture stays runner-local and drives no branch.
- The audit packet remains DOWNSTREAM / INERT / FAIL-SOFT / ABSENCE-NON-PUNITIVE /
  TurnResult-ONLY (composed by _observe_audit_evidence_from_prompt_request(...)).
- PrivateGenerationOwner remains UNWIRED / UNIMPORTED / UNCALLED / UNCONSTRUCTED.
- The W-1 caller path remains HOLD / none-selected.
- Shape B remains DEFERRED.
```

## 4. Source terrain classification (read-only; not modified or reopened)

```text
torment_service/agent_loop.py — AUTHORITATIVE generation + downstream observation terrain.
  AgentRunner.run_turn(...)                          — authoritative turn entry; carries the request to the downstream observer
  AgentRunner._execute(...)                          — authoritative generation execution (builds the request)
  AgentRunner._execute_with_prompt_request(...)      — captures the SAME _LLMPromptRequest object for observation; capture stays RUNNER-LOCAL
                                                       ("never on self / TurnResult / ExecutionOutcome / metadata / endpoint / schema / persistence")
  _ExecutionWithPromptRequest                        — runner-local pairing (outcome + exact prompt_request)
  _LLMPromptRequest                                  — the exact model-visible request value object
  AgentRunner._observe_audit_evidence_from_prompt_request(...)
                                                     — a METHOD ON AgentRunner; receives the captured request + caller items + final response
                                                       and composes the inert packet; drives no branch; result returned only to TurnResult.audit_evidence_packet

torment_service/audit_private_generation_owner.py — NEGATIVE / foreclosed terrain AS-IS.
  PrivateGenerationOwner.run(...) calls generation_boundary.complete(system_prompt=..., messages=...) (self._gen.complete(...)).
  It OWNS / IS a generation path → W-7-foreclosed as an owner. Not eligible as-is.

torment_service/audit_selected_items_runner_bridge.py — OBSERVATION-ONLY non-owner terrain.
  run_turn_with_selected_items_observation(...) forwards selected_admitted_items(...) into
  AgentRunner.run_turn(..., audit_admitted_context_items=...) and returns TurnResult unchanged.
  A bridge around the existing run_turn observation seam — NOT an owner object.

existing guard tests — read-only resting-state locks only.
```

## 5. Shape proposal decision — OPTION B SELECTED

**Option B is selected. No precondition-satisfying beside-generation sidecar-owner
shape is proposed in this document. The W-1 caller path remains HOLD / none-selected.
Shape B remains deferred.** Option A (naming one exact paper-only shape) is **not**
taken, because the source terrain does not support a safe exact shape today (see the
blocker below). No shape is fabricated here.

### 5.1 The blocker (precise, source-grounded)

A *meaningful* beside-generation audit-owner — one that does more than the already-
foreclosed co-location shape — must prove that selected admitted-item text was present
in the **exact model-visible context the authoritative path sent to the model this
turn** (the A-prime bar established by `464320a` and the owner-seam ADR `d2f405f`).
That exact context is the `_LLMPromptRequest` (`system_prompt` + `messages`) captured
inside `AgentRunner._execute(...)` and carried by
`AgentRunner._execute_with_prompt_request(...)`. Two binding requirements collide on
that object:

```text
R1  (owner-seam ADR d2f405f + W-7): the owner must be SEPARATE from AgentRunner — it
    must not own, wrap, replace, intercept, or be silently absorbed into the
    authoritative generation path.

R2  (locked runner-local invariant + precondition "do not expose prompts"): the exact
    _LLMPromptRequest must stay RUNNER-LOCAL — "never on self / TurnResult /
    ExecutionOutcome / metadata / endpoint / schema / persistence" — i.e. it must not
    leave AgentRunner's own frame.
```

No exact shape nameable from current source satisfies both R1 and R2:

```text
- A SEPARATE owner object that performs the inclusion proof would require AgentRunner
  to hand the exact _LLMPromptRequest outside its runner-local frame → PROMPT EXPOSURE
  (forbidden; violates R2 and a §8 crossing).

- The only beside-generation observer that proves real inclusion today
  (_observe_audit_evidence_from_prompt_request) works PRECISELY BECAUSE it is an
  internal AgentRunner method, not a separate object → it is the existing runner-
  internal observation SEAM, not a separate "sidecar-owner shape" (fails R1 as an
  "owner"; and it already exists, so it is not a new shape to propose).

- A co-location-only observer (final response + selected item dicts, NOT the exact
  request) avoids R2 but proves no model-visible inclusion → exactly the co-location
  shape the arc already rejected as not meaningful provenance.

- A self-rendering owner that builds its OWN prompt/messages either (i) does not call
  generation → its captured prompt is NOT the context the model actually saw, so its
  inclusion proof says nothing about the authoritative turn (meaningless); or
  (ii) calls generation → it becomes PrivateGenerationOwner
  (generation_boundary.complete(...)), which W-7 forecloses.
```

Each candidate fails a precondition or a forbidden crossing. Therefore no safe exact
beside-generation sidecar-owner shape exists on paper today.

## 6. Non-selection statement

```text
- No caller path is selected.
- No Shape B is selected.
- No production / test proposal is authorized.
- No live wiring is authorized.
- Option B is chosen: NO sidecar-owner shape exists on paper yet. No shape is named,
  designed, or authorized in this document.
```

## 7. Future gate

```text
Because Option B is chosen:
  - Before the W-1 caller path can reopen, a future, SEPARATELY AUTHORIZED docs-only
    SHAPE proposal must first satisfy the preconditions — i.e. it must resolve the
    R1/R2 collision above by naming an exact shape that proves real model-visible
    inclusion WITHOUT exposing the runner-local prompt request and WITHOUT owning /
    wrapping / replacing / intercepting / calling generation. Until such a shape is
    filed and reviewed, the W-1 caller path stays HOLD.
  - This document does NOT design that resolution; it only records that today's
    terrain does not support one.

Any later tests or production require SEPARATE Hilmir authorization AND Codex review.
No §0 pointer is added until after review and commit.
```

## 8. Forbidden crossings (explicit)

```text
- no production code
- no tests
- no caller path
- no live wiring
- no Shape B selection
- no endpoint / API / schema
- no prompt mutation / exposure
- no memory / retrieval / output-control
- no Gate A / Gate D
- no database / substrate / private-cognition
```

This list is a hard boundary on anything this document could be read to imply. None of
it is opened here.

## 9. Anti-drift footer

TORMENT AUDIT — PRIVATE-OWNER SIDECAR-OWNER SHAPE PROPOSAL / DOCS-ONLY /
NON-AUTHORIZING. Subordinate to the W-7 sidecar-only decision frame, the W-1
caller-path HOLD decision frame, and the sidecar-owner shape precondition frame. It
answers one paper-only question — does a precondition-satisfying beside-generation
audit-owner shape exist on paper? — and records **Option B: none does yet.**
Source-grounded blocker: a meaningful beside-generation owner must prove selected-item
text was present in the exact model-visible `_LLMPromptRequest` the authoritative
`AgentRunner` path sent to the model, but that request is captured runner-local and
must never leave AgentRunner's frame, while the owner-seam ADR requires the owner to be
separate from AgentRunner — so a separate object proving inclusion would expose the
prompt request (forbidden), the only working observer is the existing runner-internal
`_observe_audit_evidence_from_prompt_request` seam (not a separate owner), a
co-location-only observer is not meaningful provenance, and a self-rendering owner
either proves against a prompt the model never saw or becomes the W-7-foreclosed
`PrivateGenerationOwner` (`generation_boundary.complete(...)`). No shape is fabricated.
**The W-1 caller path remains UNOPENED and UNSELECTED; Shape B remains DEFERRED; the
existing `AgentRunner` generation path remains authoritative; exact prompt-request
carry-through stays observation terrain only; the packet stays downstream / inert /
fail-soft / absence-non-punitive / TurnResult-only.** It authorizes no production code,
no tests, no live wiring, no caller path, no endpoint / API / schema, no prompt
mutation or exposure, and no memory / retrieval / output-control / Gate A / Gate D /
database / substrate / private-cognition movement. Guidance not control; audit observes
authority and does not become authority; nothing rewrites identity / canon / seed /
soul.

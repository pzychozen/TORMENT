# TORMENT Audit — Private-Owner Sidecar-Owner Shape Precondition Frame v0.1

## 1. Title / status

**Sidecar-owner shape precondition frame. Docs-only / NON-AUTHORIZING. No
implementation authorized.** This frame defines only the preconditions a future
beside-generation audit-owner shape would have to satisfy *before* the W-1
caller-path question may be reopened. It selects no caller path, selects no Shape B,
authorizes no tests or production, and wires / imports / calls / constructs /
modifies no `PrivateGenerationOwner`.

**Subordinate to, and may not contradict:**

```text
docs/TORMENT_AUDIT_PRIVATE_OWNER_W7_SIDECAR_ONLY_DECISION_FRAME_v0.1.md      (W-7: owner-as-generation-path CLOSED; future owner only beside-generation / sidecar)
docs/TORMENT_AUDIT_PRIVATE_OWNER_SIDECAR_CALLER_PATH_DECISION_FRAME_v0.1.md  (W-1 caller-path: Option A / HOLD — no caller path selected)
```

Where this frame and any parent frame / contract / guard appear to differ, the
parent / contract / guard wins. This frame **narrows**; it relaxes nothing.

Standing posture carried verbatim:

> Memory may shape context. Memory may not seize authority.
> Audit observes authority. Audit must not become authority.

Anchor: `4b7544d` (HEAD; W-1 caller-path HOLD §0 pointer recorded). Substantive
caller-path decision artifact: `f924c0a`.

## 2. Scope

```text
DEFINES:
  - Preconditions ONLY: what a future beside-generation audit-owner shape must be
    before any caller-path selection can be reopened.

DOES NOT:
  - Reopen W-7 (sidecar-only owner decision stays closed).
  - Reopen the W-1 caller path (stays HOLD / none-selected).
  - Select a caller path.
  - Select Shape B (private runner delegation seam).
  - Reopen the exact prompt-request carry-through (observation terrain only).
  - Reopen packet semantics (downstream / inert / fail-soft / absence-non-punitive /
    TurnResult-only).
```

This frame is a precondition envelope, not a design. The safe question it answers is
"what must any future sidecar-owner shape be — and be forbidden from becoming —
before W-1 can reopen?", not "which owner do we build?".

## 3. Closed constraints carried forward

```text
- Owner-as-generation-path is FORBIDDEN (W-7). An audit owner may not be the
  generation path.
- The existing AgentRunner generation path remains AUTHORITATIVE:
  AgentRunner._execute(...) builds the request and calls the model boundary via
  AgentRunner._complete_llm_prompt_request(...); AgentRunner.run_turn(...) carries
  the request to the downstream observer. A future owner does not take that role.
- Exact prompt-request carry-through remains OBSERVATION terrain only, NOT a control
  hook: AgentRunner._execute_with_prompt_request(...) carries the same
  _LLMPromptRequest object (paired in _ExecutionWithPromptRequest) for observation;
  it drives no branch and reaches no writer / review / retrieval / output / authority
  path.
- The audit packet remains DOWNSTREAM / INERT / FAIL-SOFT / ABSENCE-NON-PUNITIVE /
  TurnResult-ONLY (composed via _observe_audit_evidence_from_prompt_request(...)).
- PrivateGenerationOwner remains UNWIRED / UNIMPORTED / UNCALLED / UNCONSTRUCTED.
- Shape B (private runner delegation seam) remains DEFERRED.
```

Read-only anchors (cited, not reopened, not modified):

```text
torment_service/agent_loop.py
  AgentRunner.run_turn(...)                          — authoritative turn entry; carries request to the downstream observer
  AgentRunner._execute(...)                          — authoritative generation execution (builds the request)
  AgentRunner._execute_with_prompt_request(...)      — carries the exact _LLMPromptRequest for observation (the only caller of _execute)
  _ExecutionWithPromptRequest                        — runner-local pairing (outcome + exact prompt_request)
  _LLMPromptRequest                                  — the exact request value object
  AgentRunner._observe_audit_evidence_from_prompt_request(...)  — downstream / fail-soft observer seam
torment_service/audit_private_generation_owner.py    — PrivateGenerationOwner (negative / foreclosed terrain; see §4)
torment_service/audit_selected_items_runner_bridge.py — run_turn_with_selected_items_observation(...) (observation-only bridge; see §4)
existing guard tests                                 — read-only resting-state locks
```

## 4. Negative source terrain

```text
PrivateGenerationOwner is NOT eligible as-is as a sidecar-owner shape.
  Reason (source): PrivateGenerationOwner.run(...) calls
  generation_boundary.complete(system_prompt=..., messages=...) (it holds
  self._gen = generation_boundary and calls self._gen.complete(...)). It therefore
  OWNS / IS a generation path. Under W-7 an audit owner may not be the generation
  path, so PrivateGenerationOwner as built is foreclosed terrain, not a sidecar owner.

Any object that CALLS generation, WRAPS generation, REPLACES generation, INTERCEPTS
generation, or becomes OUTPUT AUTHORITY is NOT a sidecar-owner shape under W-7.

The selected-items runner bridge is NOT an owner object.
  Source: run_turn_with_selected_items_observation(...) forwards
  selected_admitted_items(...) into the existing
  AgentRunner.run_turn(..., audit_admitted_context_items=...) observation seam and
  returns TurnResult unchanged. It is OBSERVATION-ONLY around the existing
  authoritative AgentRunner.run_turn, owns no generation, and is not an owner object.
  It is cited as terrain only and is neither a candidate owner nor a selected caller.
```

## 5. Required sidecar-owner shape preconditions

A future beside-generation audit-owner shape, **if it is ever proposed**, must
satisfy every precondition below. These are stated as preconditions only: **no such
shape is selected, designed, named, or authorized here.**

```text
A future sidecar-owner shape MUST:
  - not call generation
  - not wrap generation
  - not replace generation
  - not intercept generation
  - not become output authority
  - not mutate prompts
  - not expose prompts
  - not read packet presence / absence as control
  - not feed packet output back into the turn
  - not affect user output, review, retry, ranking, suppression, style, memory,
    retrieval, Gate A, Gate D, endpoint / API / schema, database, substrate, or
    private cognition
  - operate ONLY beside the already-authoritative AgentRunner generation path
  - remain fail-soft and absence-non-punitive
  - be proposed later, with exact source terrain named, BEFORE the W-1 caller path
    can be reopened
```

Until a future proposal demonstrates a shape satisfying all of the above, **no such
shape exists** and the W-1 caller-path question cannot be reopened.

## 6. Non-selection statement

```text
- The W-1 caller path remains UNSELECTED (HOLD / none-selected).
- Shape B (private runner delegation seam) remains DEFERRED.
- No sidecar-owner object is selected or designed in this frame.
- No production / test proposal is authorized in this frame.
```

## 7. Future gate

```text
Before caller-path selection can reopen, a future, SEPARATELY AUTHORIZED docs-only
proposal must name:
  - the exact sidecar-owner shape;
  - the exact source terrain it touches (read-only anchors by source);
  - how it remains beside-generation (it does not call / wrap / replace / intercept
    generation and is not output authority);
  - how it avoids all forbidden crossings (§5 / §8).

Only after such a precondition-satisfying proposal is filed and reviewed may the W-1
caller-path question be reopened. Any later tests or production require SEPARATE
Hilmir authorization AND Codex review. No §0 pointer is added until after review and
commit.
```

## 8. Forbidden crossings (explicit)

```text
- no production code
- no tests
- no caller path
- no Shape B selection
- no live wiring
- no endpoint / API / schema
- no prompt mutation
- no prompt exposure
- no memory / retrieval / output-control
- no Gate A / Gate D
- no database / substrate / private-cognition
```

This list is a hard boundary on anything this frame could be read to imply. None of
it is opened here.

## 9. Anti-drift footer

TORMENT AUDIT — PRIVATE-OWNER SIDECAR-OWNER SHAPE PRECONDITION / DOCS-ONLY /
NON-AUTHORIZING. Subordinate to the W-7 sidecar-only decision frame and the W-1
caller-path HOLD decision frame. It defines **preconditions only** — what a future
beside-generation audit-owner shape must be, and must be forbidden from becoming,
before the W-1 caller-path question may be reopened. It records the negative terrain:
`PrivateGenerationOwner` is foreclosed as-is because `PrivateGenerationOwner.run(...)`
calls `generation_boundary.complete(...)` (an owned generation path, which W-7
forbids); any object that calls / wraps / replaces / intercepts generation or becomes
output authority is not a sidecar shape; and `run_turn_with_selected_items_observation(...)`
is an observation-only bridge around the existing authoritative `AgentRunner.run_turn`,
not an owner object. The existing `AgentRunner._execute(...)` /
`_complete_llm_prompt_request(...)` / `run_turn(...)` generation path remains
authoritative; exact prompt-request carry-through stays observation terrain only, not
a control hook; the packet stays downstream / inert / fail-soft / absence-non-punitive
/ TurnResult-only. **It selects no caller path, selects no Shape B, designs no owner,
and authorizes no production code, no tests, no live wiring, no endpoint / API /
schema, no prompt mutation or exposure, and no memory / retrieval / output-control /
Gate A / Gate D / database / substrate / private-cognition movement.** The W-1 caller
path stays HOLD and Shape B stays deferred. Any future precondition-satisfying
proposal, and any later tests or production, requires separate Hilmir authorization
plus Codex review. Guidance not control; audit observes authority and does not become
authority; nothing rewrites identity / canon / seed / soul.

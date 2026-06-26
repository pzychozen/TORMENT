# TORMENT Audit — Private-Owner W-7 Sidecar-Only Decision Frame v0.1

## 0. Title / status

**W-7 sidecar-only decision frame. Docs-only / NON-AUTHORIZING. No implementation
authorized.** This frame records a Hilmir/operator decision that narrows the W-7
("integration shape") question left open by
`docs/TORMENT_AUDIT_PRIVATE_OWNER_W1_W8_LIVE_OWNER_REFACTOR_PROPOSAL_FRAME_v0.1.md`.
It writes no production code, edits no tests, selects no caller path, selects no
Shape B, and wires / imports / calls / constructs no `PrivateGenerationOwner`. It
resolves no implementation detail and authorizes no live-owner wiring.

Standing posture carried verbatim:

> Memory may shape context. Memory may not seize authority.
> Audit observes authority. Audit must not become authority.

Anchor: `9a3532b` (origin/main; exact prompt-request carry-through refactor recorded).

## 1. Subordination

Subordinate to, and may not contradict:

```text
docs/TORMENT_AUDIT_PRIVATE_OWNER_W1_W8_LIVE_OWNER_REFACTOR_PROPOSAL_FRAME_v0.1.md   (W-1…W-8; W-7 was UNRESOLVED)
docs/TORMENT_AUDIT_PRIVATE_OWNER_LIVE_WIRING_DECISION_FRAME_v0.1.md                (verdict + W-1…W-8 gate; §9 flip-to-forbidden)
docs/TORMENT_AUDIT_PRIVATE_OWNER_LIVE_WIRING_GATE_FRAME_v0.1.md                    (gate criteria + stop rule)
docs/TORMENT_AUDIT_MODEL_VISIBLE_CONTEXT_OWNER_SEAM_DESIGN_v0.1.md                 (owner separate from AgentRunner; hidden-authority line)
torment_service/agent_loop.py                                                     (existing terrain)
the existing guard tests                                                          (resting-state locks)
```

Where this frame and any contract/guard appear to differ, the contract/guard wins.
This frame **narrows** W-7; it relaxes nothing.

## 2. Decision

```text
HILMIR / OPERATOR DECISION (W-7):
  - The audit owner MUST NOT become the generation path. "Owner becomes the
    generation path" is no longer an admissible W-7 integration shape.
  - Any future audit-owner proposal may ONLY be a BESIDE-GENERATION / SIDECAR
    direction: it observes around the existing generation path; it does not own,
    replace, wrap, or intercept generation.
  - The existing generation path remains AUTHORITATIVE: `AgentRunner._execute(...)`
    builds the request and calls the model via `_complete_llm_prompt_request(...)`;
    `run_turn(...)` carries the request to the downstream observer. The owner does
    not take that role.
```

This forecloses the "owner-as-generation-owner" branch of W-7 (the
`d2f405f` seam design's "owner separate from `AgentRunner`" intent is preserved and
sharpened: separate AND beside, never the generator). Shape B (private runner
delegation seam) is **not** selected by this decision and remains deferred.

## 3. What this decision ALLOWS

```text
- Only FUTURE PROPOSALS or TESTS may explore sidecar-only audit-owner constraints
  (what a beside-generation observer must and must not do).
- Any later artifact (docs, tests, or production) still requires SEPARATE Hilmir
  authorization AND Codex review before any line is written.
- HOLD remains a valid terminal state: nothing here obliges a next step.
```

## 4. What this decision DOES NOT allow

```text
- No PrivateGenerationOwner wiring / import / call / construction.
- No Shape B (private runner delegation seam) selection.
- No caller-path selection.
- No production code.
- No endpoint / API / schema movement.
- No prompt mutation or prompt exposure.
- No memory / retrieval / output-control / Gate A / Gate D / database / substrate /
  private-cognition movement.
```

## 5. Source terrain (existing terrain only — cited, not reopened)

```text
torment_service/agent_loop.py (existing observation terrain):
  AgentRunner._execute(...)                            — builds the request, calls the model boundary
  AgentRunner._execute_with_prompt_request(...)        — carries the EXACT request object back to run_turn
  _ExecutionWithPromptRequest                          — runner-local pairing (outcome + exact prompt_request)
  _LLMPromptRequest                                    — the exact request value object
  _observe_audit_evidence_from_prompt_request(...)     — downstream, fail-soft observer seam
  run_turn(...)                                         — composes the observation-only packet, returns it on TurnResult

Cited but NOT reopened (no change proposed or authorized):
  torment_service/audit_private_generation_owner.py    — PrivateGenerationOwner (unwired / test-called only)
  torment_service/app.py                               — endpoints; non-callers of the terrain
  endpoint callers                                     — non-callers
  existing guard tests                                 — resting-state locks
```

Recorded facts (from the closed `9d2a6dc` refactor):

```text
- Exact prompt-request carry-through exists ONLY as OBSERVATION terrain.
- _execute_with_prompt_request carries the SAME _LLMPromptRequest object built in
  _execute before _complete_llm_prompt_request(...); it is a runner-local capture.
- This terrain is NOT a control hook: the carried request and the downstream packet
  drive no branch and reach no writer / review / retrieval / output / authority path.
```

## 6. Sidecar constraints (requirement-level only)

A future beside-generation / sidecar audit-owner, if ever proposed, must satisfy
these constraints. Stated here as constraints; **no such owner is selected, designed,
or authorized**.

```text
Sidecar output CANNOT become:
  - user output
  - review input
  - retry / ranking / suppression / style input
  - memory / retrieval feedback
  - endpoint / API / schema surface
  - Gate A or Gate D authority
  - database / substrate / private-cognition input

Sidecar absence must remain NON-PUNITIVE (its absence carries no dishonesty /
unsupportedness / suppression / retrieval / authority / memory meaning).
Sidecar failure must remain FAIL-SOFT (an error yields no packet and no error path).
```

The sidecar is, by definition, **beside** generation: it cannot own, replace, wrap,
or intercept the generation path, and it cannot feed anything back into the turn.

## 7. Packet preservation

```text
- The audit packet remains DOWNSTREAM (composed after execution + review), INERT
  (drives no branch), FAIL-SOFT, ABSENCE-NON-PUNITIVE, and TurnResult-ONLY.
- The packet must not drive branches or control behaviour.
```

A sidecar direction must preserve these packet properties unchanged; it may not turn
the packet into a control signal.

## 8. Forbidden crossings (explicit)

```text
- no production code
- no tests
- no endpoint / API / schema
- no prompt mutation
- no prompt exposure
- no memory / retrieval / output-control
- no Gate A / Gate D
- no database / substrate / private-cognition
- no Shape B selection
- no live-owner wiring
```

This list is a hard boundary on anything this decision could be read to imply. None
of it is opened here.

## 9. Future gate

```text
- Any later docs / test / production step must be SEPARATELY proposed and pass Codex
  review under explicit Hilmir authorization.
- This doc authorizes NO implementation. It records a constraint (sidecar-only) that
  narrows W-7; it does not start work.
- §9 of the live-wiring decision frame still applies: any feedback edge from audit
  output back into the turn flips the owner direction to FORBIDDEN.
```

## 10. Anti-drift footer

TORMENT AUDIT — PRIVATE-OWNER W-7 SIDECAR-ONLY DECISION / DOCS-ONLY /
NON-AUTHORIZING. It records the Hilmir/operator decision that the audit owner must
NOT become the generation path: any future audit-owner proposal may only be a
beside-generation / sidecar direction, and the existing `AgentRunner._execute(...)` /
`_complete_llm_prompt_request(...)` / `run_turn(...)` generation path remains
authoritative. It cites the existing observation terrain (`_execute_with_prompt_request`
carries the SAME `_LLMPromptRequest` object; `_observe_audit_evidence_from_prompt_request`;
the TurnResult packet) as terrain only and reopens nothing — `PrivateGenerationOwner`
stays unwired, Shape B unselected, no caller path chosen. It pins sidecar constraints
(output may never become user output / review / retry / ranking / suppression / style /
memory / retrieval / endpoint / Gate A / Gate D / database / substrate /
private-cognition input; absence non-punitive; failure fail-soft) and packet
preservation (downstream / inert / fail-soft / absence-non-punitive / TurnResult-only;
drives no branch). **It authorizes no production code, no tests, no endpoint / API /
schema, no prompt mutation or exposure, no memory / retrieval / output-control / Gate A
/ Gate D / database / substrate / private-cognition movement, no Shape B selection, and
no live-owner wiring. Any later docs / test / production step requires separate Hilmir
authorization plus Codex review.** Guidance not control; audit observes authority and
does not become authority; nothing rewrites identity / canon / seed / soul.

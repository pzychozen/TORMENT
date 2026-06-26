# TORMENT Audit — Exact Prompt-Request Carry-Through Production-Refactor Proposal v0.1

## 0. Status / authorization scope

**Docs-only PROPOSAL. NON-AUTHORIZING.** It describes the shape of a *future*
behavior-preserving production refactor that would make exact prompt-request
carry-through real, and names the tests a future authorized refactor would have to
change. **Landing this proposal authorizes no production code and no test edits.**
It resolves no W-7, selects no Shape B, and wires / imports / calls / constructs no
`PrivateGenerationOwner`. It changes no prompt surface, adds no endpoint / API /
schema, and opens no memory write, retrieval feedback, output control, Gate A /
Gate D, database / substrate, or private-cognition path.

**Any actual refactor or test change requires separate Hilmir authorization plus
Codex review.** This is a proposal for *what such a refactor would do and prove* —
not permission to do it.

Standing posture carried verbatim:

> Memory may shape context. Memory may not seize authority.
> Audit observes authority. Audit must not become authority.

Anchor: `4390585` (origin/main; gap characterization recorded).

## 1. Subordination

Subordinate to, and may not contradict:

```text
docs/TORMENT_AUDIT_EXACT_PROMPT_REQUEST_CARRY_THROUGH_TEST_PROPOSAL_v0.1.md           (the tests-only proposal)
tests/test_audit_exact_prompt_request_carry_through_characterization.py               (0acd7df + 5b3ab8d; the proven gap)
docs/TORMENT_AUDIT_PRIVATE_OWNER_W1_W8_LIVE_OWNER_REFACTOR_PROPOSAL_FRAME_v0.1.md      (W-1…W-8 frame; W-7 unresolved; owner unwired)
docs/TORMENT_AUDIT_PRIVATE_OWNER_LIVE_WIRING_DECISION_FRAME_v0.1.md                   (verdict + W-1…W-8 gate)
torment_service/agent_loop.py                                                         (the live terrain)
the current guards: pre-wiring guard; handoff-boundary; live-owner inventory / path-selection; audit packet sink / staging; prompt-request extraction; the carry-through gap characterization
```

Where this proposal and any contract or guard appear to differ, the contract/guard
wins.

## 2. Doctrine filter

> A refactor proposal names what a future change would do, what it would prove, and
> what it must not cross. It writes no production code and changes no test. It is
> behavior-preserving by intent: it makes an existing capture exact, and changes no
> observable turn behavior.

## 3. Scope (exact source site; nothing implemented)

```text
Source symbols in scope (read-only terrain; torment_service/agent_loop.py only):
  AgentRunner._execute(...)
  AgentRunner._execute_with_prompt_request(...)
  _ExecutionWithPromptRequest
  _LLMPromptRequest
  AgentRunner._complete_llm_prompt_request(...)
```

No other module, endpoint, or symbol is in scope. `app.py`, the endpoints,
`PrivateGenerationOwner`, the writers, retrieval/assembly, Gate A / Gate D, and the
database/substrate are explicitly out of scope.

## 4. The proven gap this proposal addresses

Established by `tests/test_audit_exact_prompt_request_carry_through_characterization.py`
(`0acd7df` + `5b3ab8d`; focused bundle 98 tests passed):

```text
- _execute(...) builds the exact _LLMPromptRequest (via _build_llm_prompt_request)
  and passes it to _complete_llm_prompt_request(...) for the model call.
- _execute_with_prompt_request(...) currently calls _execute(...) and THEN
  RECONSTRUCTS the request via _build_llm_prompt_request(frame, mode, tools=None),
  gated on outcome.llm_called; it reads no request off the ExecutionOutcome.
- ANSWER path: the reconstructed request matches the sent system_prompt / messages —
  VALUE-EQUAL but a DISTINCT object (equal values, not the same object).
- USE_TOOL path: the model boundary receives tools=[sig], but the reconstructed
  prompt_request.tools is None — an asymmetry on the tools axis.
- => exact-object carry-through is NOT implemented today.
```

The reconstruction is a faithful-enough copy for ANSWER-path observation, but it is
(a) a different object than the one actually sent, and (b) not even value-faithful on
the USE_TOOL tools axis. A future owner/observer that must reason about *the exact
request sent* therefore cannot rely on today's carried object.

## 5. Future refactor target (what a separately-authorized change would do)

```text
TARGET (behavior-preserving):
  _execute_with_prompt_request(...).prompt_request becomes the SAME _LLMPromptRequest
  object built inside _execute(...) before _complete_llm_prompt_request(...) — the
  exact object sent to the model — instead of a post-execution reconstruction.

  - ANSWER path preserves tools=None on the carried object.
  - USE_TOOL path preserves the exact sent tools=[signature_spec] on the carried
    object (closing the tools-axis asymmetry).
  - The carried object is None exactly when no model call occurred (unchanged).

PROMPT SURFACE UNCHANGED:
  Still _build_system_prompt(frame, mode) for system_prompt and
  messages = [{"role": "user", "content": frame.raw_input}], with explicit tools only
  (None on ANSWER, [signature_spec] on USE_TOOL). The model sees exactly what it sees
  today; only the OBSERVATION-side object identity changes, not generation behaviour.

NO PROMPT EXPOSURE:
  The prompt request stays runner-local. It is NOT exposed on TurnResult,
  ExecutionOutcome, metadata, logs / debug, endpoint / schema / API, persistence, or
  `self`. (A likely mechanism: _execute returns the request alongside its outcome
  through a private/internal carrier so _execute_with_prompt_request can hold the
  exact object — WITHOUT placing it on any public/observable surface. The exact
  carrier mechanism is NOT selected here.)

PACKET / OBSERVER UNCHANGED:
  - The audit packet remains downstream, inert, fail-soft, absence-non-punitive, and
    TurnResult-only; it drives no branch.
  - observe_prompt_inclusion_packet(...) remains confined to
    _observe_audit_evidence_from_prompt_request(...).

BOUNDARIES UNCHANGED:
  - PrivateGenerationOwner remains unwired / unconstructed in production.
  - app.py and endpoints remain non-callers.
  - No writer / memory / retrieval / Gate A / Gate D / database / substrate /
    private-cognition / review-output-control / retry-ranking-suppression-style path
    becomes reachable from the terrain.
```

The refactor is purely about making the *already-captured* request *exact* (same
object, tools included). It adds no new capability, no new surface, and no new
authority.

## 6. Tests a future authorized refactor would need to change (future obligations only)

Named here as **future obligations**, not as edits authorized by this doc. In
`tests/test_audit_exact_prompt_request_carry_through_characterization.py`:

```text
WOULD FLIP (current-gap → carry-through):
  - The current-gap tests that expect RECONSTRUCTION after _execute(...) would flip
    to expect exact-object carry-through (e.g.
    test_carry_reconstructs_after_execute / test_carry_does_not_read_a_request_off_
    the_outcome would be re-expressed for the carry-through topology).
  - The identity-gap expectations (equal values, distinct object) would be replaced
    with EXACT-OBJECT identity expectations (the carried prompt_request IS the object
    sent to the model).
  - The USE_TOOL asymmetry test
    (test_use_tool_reconstruction_drops_tools_today_carry_through_future_only) would
    be replaced so the carried prompt_request.tools == [sig].

MUST REMAIN UNCHANGED (safety tests — carry forward, not weakened):
  - no prompt exposure
  - packet inertness (drives no branch; TurnResult-only)
  - downstream observer confinement
  - owner unwired
  - app.py / endpoints non-callers
  - no forbidden reachability from the terrain
  - fail-soft / absence-non-punitive
```

A future refactor that flips a safety test (rather than only the gap/identity tests)
is out of bounds and would fail review.

## 7. What this proposal does and does not do

```text
DOES:    name the exact source terrain (§3); record the proven gap (§4); describe the
         behavior-preserving carry-through target (§5); name, as future obligations
         only, the tests that would flip and the safety tests that must not (§6).

DOES NOT (and does not authorize by implication):
  - write or edit any production code or test; run git
  - implement exact-request carry-through or select a carrier mechanism
  - resolve W-7; select Shape B; select a live owner wiring site
  - wire / import / call / construct PrivateGenerationOwner
  - change the prompt surface; add endpoint / API / schema
  - add memory writes, retrieval feedback, output control, Gate A / Gate D,
    database / substrate, or private cognition
  - claim that landing this proposal authorizes any production refactor or tests
```

## 8. Gating and stop rule

```text
- The next admissible step would be the actual behavior-preserving refactor PLUS the
  paired test changes (§6), which require SEPARATE Hilmir authorization + Codex review
  before any production line or test line is written.
- That refactor, if authorized, lands source/tests together, preserves all §5/§6
  safety invariants, exposes no prompt material, makes no prompt text model-visible by
  audit path, and lets no packet output affect behaviour — else it fails and nothing
  proceeds.
- Live-owner wiring and W-7 resolution remain further separate gates beyond this
  refactor. None is opened here.
- Stable resting state remains valid: reconstruction in place, owner unwired, bridge
  dead-end, packet optional and observation-only. HOLD is an acceptable terminal state.
```

## 9. Anti-drift footer

TORMENT AUDIT — EXACT PROMPT-REQUEST CARRY-THROUGH PRODUCTION-REFACTOR PROPOSAL /
DOCS-ONLY / NON-AUTHORIZING. It describes a future behavior-preserving refactor over
the terrain `AgentRunner._execute(...)` / `_execute_with_prompt_request(...)` /
`_ExecutionWithPromptRequest` / `_LLMPromptRequest` / `_complete_llm_prompt_request(...)`
that would make `_execute_with_prompt_request(...).prompt_request` the SAME object
built before `_complete_llm_prompt_request(...)` (ANSWER preserves `tools=None`;
USE_TOOL preserves exact `tools=[signature_spec]`), with the prompt surface unchanged,
no prompt exposure, the packet downstream/inert/fail-soft/TurnResult-only, the observer
confined to `_observe_audit_evidence_from_prompt_request(...)`, `PrivateGenerationOwner`
unwired, `app.py`/endpoints non-callers, and no writer / memory / retrieval / Gate A /
Gate D / database / substrate / private-cognition / review-output-control /
retry-ranking-suppression-style reachability. It names the tests that would flip
(current-gap, identity-gap, USE_TOOL asymmetry) as **future obligations only** and the
safety tests that must remain unchanged. **Landing this proposal authorizes no
production code and no tests; it resolves no W-7, selects no Shape B, wires no owner,
changes no prompt surface, and opens no endpoint / API / schema / memory / retrieval /
output-control / Gate A / Gate D / database / substrate / private-cognition path. Any
actual refactor or test change requires separate Hilmir authorization plus Codex
review.** Guidance not control; audit observes authority and does not become authority;
nothing rewrites identity / canon / seed / soul.

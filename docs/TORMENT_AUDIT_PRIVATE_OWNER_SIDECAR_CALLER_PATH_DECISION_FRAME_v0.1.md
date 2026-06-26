# TORMENT Audit — Private-Owner Sidecar Caller-Path Decision Frame v0.1

## 1. Title / status

**Sidecar caller-path decision frame. Docs-only / NON-AUTHORIZING. No
implementation authorized.** This frame resolves only the W-1 caller-path question
under the closed W-7 sidecar-only constraint. It writes no production code, edits
no tests, implements no caller, and wires / imports / calls / constructs no
`PrivateGenerationOwner`. It opens no endpoint / API / schema, mutates / exposes no
prompt, and opens no memory / retrieval / output-control / Gate A / Gate D /
database / substrate / private-cognition movement.

**Subordinate to the W-7 sidecar-only decision frame**
(`docs/TORMENT_AUDIT_PRIVATE_OWNER_W7_SIDECAR_ONLY_DECISION_FRAME_v0.1.md`) and may
not contradict it. Where this frame and any contract / guard / parent frame appear
to differ, the parent / contract / guard wins. This frame **narrows**; it relaxes
nothing.

Standing posture carried verbatim:

> Memory may shape context. Memory may not seize authority.
> Audit observes authority. Audit must not become authority.

Anchor: `b301938` (HEAD; W-7 §0 pointer recorded). Substantive W-7 decision
artifact: `6f45091`.

## 2. Scope

```text
RESOLVES:
  - Only the W-1 caller-path question, and only under W-7 sidecar-only.
  - The narrow question: under W-7 sidecar-only, is any private/internal sidecar
    caller path admissible for later proposal, or is no caller path selected and
    the lane remains HOLD?

DOES NOT REOPEN:
  - W-7 (the sidecar-only owner decision is closed and is carried forward, not
    re-litigated).
  - The exact prompt-request carry-through refactor (observation terrain only).
  - Packet semantics (downstream / inert / fail-soft / absence-non-punitive /
    TurnResult-only).

SHAPE B:
  - This frame does NOT resolve Shape B (private runner delegation seam). Shape B
    remains separately framed and DEFERRED, exactly as left by W-7. No Shape B
    selection is made or implied here.
```

Subordination chain (cited, not reopened):

```text
docs/TORMENT_AUDIT_PRIVATE_OWNER_W7_SIDECAR_ONLY_DECISION_FRAME_v0.1.md   (parent; owner = generation path CLOSED)
docs/TORMENT_AUDIT_PRIVATE_OWNER_W1_W8_LIVE_OWNER_REFACTOR_PROPOSAL_FRAME_v0.1.md   (W-1 answered for internal refactor terrain only; UNANSWERED for live owner invocation)
docs/TORMENT_AUDIT_PRIVATE_OWNER_LIVE_WIRING_DECISION_FRAME_v0.1.md       (verdict + W-1..W-8 gate; §9 flip-to-forbidden)
docs/TORMENT_AUDIT_PRIVATE_OWNER_LIVE_WIRING_GATE_FRAME_v0.1.md           (gate criteria + stop rule)
docs/TORMENT_AUDIT_MODEL_VISIBLE_CONTEXT_OWNER_SEAM_DESIGN_v0.1.md        (owner separate from AgentRunner; hidden-authority line)
torment_service/agent_loop.py                                            (existing terrain)
the existing guard tests                                                 (resting-state locks)
```

## 3. W-7 constraints carried forward

```text
- Owner-as-generation-path is CLOSED. "Owner becomes the generation path" is no
  longer an admissible integration shape.
- Any future audit-owner direction may ONLY be BESIDE-GENERATION / SIDECAR: it
  observes around the existing generation path; it does not own, replace, wrap, or
  intercept generation.
- The existing AgentRunner generation path remains AUTHORITATIVE: AgentRunner._execute(...)
  builds the request and calls the model boundary via _complete_llm_prompt_request(...);
  run_turn(...) carries the request to the downstream observer. The owner does not
  take that role.
- Exact prompt-request carry-through remains OBSERVATION terrain only, NOT a control
  hook: the carried _LLMPromptRequest and the downstream packet drive no branch and
  reach no writer / review / retrieval / output / authority path.
- The audit packet remains DOWNSTREAM / INERT / FAIL-SOFT / ABSENCE-NON-PUNITIVE /
  TurnResult-ONLY.
```

## 4. Current source terrain inventory (read-only — cited, not reopened)

```text
torment_service/agent_loop.py (existing generation + observation terrain):
  AgentRunner._execute(...)                          — owns existing generation execution: builds the request
  AgentRunner._complete_llm_prompt_request(...)      — calls the model boundary (authoritative generation call)
  AgentRunner._execute_with_prompt_request(...)      — carries the EXACT _LLMPromptRequest object back to run_turn for observation
  _ExecutionWithPromptRequest                        — runner-local pairing (outcome + exact prompt_request)
  _LLMPromptRequest                                  — the exact request value object
  AgentRunner._observe_audit_evidence_from_prompt_request(...)  — DOWNSTREAM / FAIL-SOFT observer seam; touches no owner, reaches no writer/memory/retrieval
  AgentRunner.run_turn(...)                          — composes the observation-only packet; returns it on TurnResult.audit_evidence_packet;
                                                       accepts keyword-only audit_admitted_context_items (observation seam only)

torment_service/audit_private_generation_owner.py:
  PrivateGenerationOwner / PrivateGenerationOwnerResult
    - PRIVATE / INTERNAL; called NOWHERE in production; exercised by tests only; UNWIRED.
    - By construction it IS a generation path: run() renders + captures the exact prompt/messages and
      sends them to a caller-supplied generation_boundary.complete(system_prompt=..., messages=...).
    - Therefore, under W-7, a caller that invokes this owner would make the owner the generation path —
      the exact shape W-7 closed.

torment_service/audit_selected_items_runner_bridge.py:
  run_turn_with_selected_items_observation(...)
    - The single, already-approved PRIVATE OBSERVATION-ONLY bridge.
    - Forwards assembler-SELECTED admitted item dicts into run_turn(..., audit_admitted_context_items=...) —
      the EXISTING inert observation seam of the EXISTING authoritative generation path.
    - It is NOT an owner caller (it never calls PrivateGenerationOwner; it returns TurnResult unchanged and
      inspects nothing on it). Called NOWHERE in production (observation-only).

torment_service/app.py:
  - Endpoint surfaces import / call NEITHER PrivateGenerationOwner NOR the selected-items bridge.
  - /agent/query is a RETRIEVAL / QUERY path (ThinkingController -> MemoryPlan -> lane-specific retrieval),
    not a generation-owner caller.
  - app.py and its endpoints MUST NOT become the caller through this doc.

existing guard tests:
  - Resting-state locks: production never calls / constructs PrivateGenerationOwner; the bridge stays
    packet-blind and unwired except from tests; app.py / endpoints remain non-callers.
```

## 5. Caller-path decision — OPTION A SELECTED

**Option A is selected. No caller path is selected. HOLD remains.** Future work
must first propose a narrower caller-path / test frame before any caller-path tests
or production proposal.

Option B (selecting a private/internal sidecar caller path as a future docs/test
proposal direction) is **NOT** selected.

Source-grounded reasoning:

```text
1. The only owner object in source (PrivateGenerationOwner) is, by construction, a
   GENERATION PATH: its run() sends the captured prompt/messages to a generation
   boundary. Under W-7, owner-as-generation-path is CLOSED. So no caller that
   invokes PrivateGenerationOwner is admissible — calling it is the forbidden shape.

2. The only existing beside-generation / sidecar surface in source
   (run_turn_with_selected_items_observation) is an OBSERVATION bridge around the
   EXISTING authoritative generation path (run_turn). It is not an owner caller and
   already exists; it requires no caller-path selection for the owner, and treating
   it as "the owner caller path" would conflate observation with ownership and
   reach into the separately gated live-wiring lane.

3. No BESIDE-GENERATION OWNER object exists in source to call. The only owner
   artifact is the generation-owning PrivateGenerationOwner (W-7-foreclosed as a
   callee); there is no sidecar owner whose caller site could be named.

Therefore there is no admissible owner caller path to select under W-7 sidecar-only.
The lane remains HOLD.
```

## 6. Option B constraints — NOT ENGAGED (recorded as forward guard-rails only)

Option B is not selected (see §5). The constraints below are recorded for
completeness only: they are the guard-rails that **would** bind any future
private/internal sidecar caller **if** one were ever proposed under a separately
authorized frame. They bind nothing now, select nothing, and authorize nothing.

```text
A future caller, IF ever proposed (separately, under Hilmir authorization + Codex
review), would have to remain:
  - private / internal (not an endpoint; not app.py);
  - non-prompt-mutating and non-prompt-exposing;
  - non-feedback: it must not feed packet output back into the turn;
  - non-control: it must not read packet presence / absence as control;
  - inert with respect to user output, review, retry, ranking, suppression, style,
    memory, retrieval, Gate A, Gate D, database, substrate, and private cognition.
Later tests / production still require SEPARATE Hilmir authorization AND Codex
review before any line is written.
```

## 7. Option A HOLD statement — ENGAGED

```text
EXACT BLOCKER:
  The only owner object in source (PrivateGenerationOwner) is itself a generation
  path (it calls generation_boundary.complete(...)). Wiring any caller to it would
  make the owner the generation path — the shape W-7 closed. The only existing
  beside-generation / sidecar surface (run_turn_with_selected_items_observation) is
  observation-only around the EXISTING authoritative run_turn path, not an owner
  caller. No beside-generation OWNER object exists in source whose caller site could
  be named. Hence no admissible owner caller path can be selected now.

MUST BE RESOLVED BEFORE ANY CALLER-PATH TESTS OR PRODUCTION PROPOSAL:
  A future, separately authorized proposal must FIRST:
    (a) define a beside-generation owner SHAPE that is distinct from the
        generation-owning PrivateGenerationOwner (an observer that does not own,
        replace, wrap, or intercept generation); and
    (b) name that shape's exact internal, non-endpoint caller SITE by source,
  under explicit Hilmir authorization and Codex review. Until both exist, the lane
  stays HOLD.
```

## 8. Forbidden crossings (explicit)

```text
- no production code
- no tests
- no live wiring
- no caller implementation
- no endpoint / API / schema
- no prompt mutation
- no prompt exposure
- no memory / retrieval / output-control
- no Gate A / Gate D
- no database / substrate / private-cognition
- no Shape B selection (Shape B remains separately framed / deferred)
- no live-owner wiring
```

This list is a hard boundary on anything this decision could be read to imply. None
of it is opened here.

## 9. Future gate

```text
- This doc authorizes NO implementation.
- Any later tests-only or production proposal must be SEPARATELY authorized by
  Hilmir AND reviewed by Codex.
- No §0 pointer (docs/PROJECT_ORIENTATION_MAP.md) is added until after review and
  commit.
```

## 10. Anti-drift footer

TORMENT AUDIT — PRIVATE-OWNER SIDECAR CALLER-PATH DECISION / DOCS-ONLY /
NON-AUTHORIZING. Subordinate to the W-7 sidecar-only decision frame. It resolves
only the W-1 caller-path question under W-7 sidecar-only and selects **Option A**:
no caller path is selected; the lane remains HOLD. Source-grounded basis: the only
owner object (`PrivateGenerationOwner`) is by construction a generation path
(`generation_boundary.complete(...)`), which W-7 forecloses as a caller target; the
only existing beside-generation / sidecar surface
(`run_turn_with_selected_items_observation`) is an observation-only bridge around
the existing authoritative `run_turn` path, not an owner caller; and no
beside-generation owner object exists in source whose caller site could be named.
The existing `AgentRunner._execute(...)` / `_complete_llm_prompt_request(...)` /
`run_turn(...)` generation path remains authoritative; exact prompt-request
carry-through stays observation terrain only; the packet stays downstream / inert /
fail-soft / absence-non-punitive / TurnResult-only. **It authorizes no production
code, no tests, no live wiring, no caller implementation, no endpoint / API /
schema, no prompt mutation or exposure, no memory / retrieval / output-control /
Gate A / Gate D / database / substrate / private-cognition movement, no Shape B
selection (Shape B remains separately framed / deferred), and no live-owner
wiring.** Any later tests-only or production proposal requires separate Hilmir
authorization plus Codex review; no §0 pointer until after review and commit.
Guidance not control; audit observes authority and does not become authority;
nothing rewrites identity / canon / seed / soul.

# TORMENT Audit — Audit-Evidence U1 Caller-Path Admissibility Frame v0.1

## 1. Title / status

**Audit-evidence caller-path admissibility frame (U1). Docs-only / NON-AUTHORIZING.
No live wiring, no caller selected, no tests, no implementation.** This frame resolves
only the narrow *caller-path admissibility* question for the already-existing inert
audit-evidence seam. It selects no caller, authorizes no production wiring, authorizes
no tests, and makes no same-turn provenance claim. Filed after Codex returned **REVISE**
on the informal "U1 activation" framing: U1 is **not** activation and does **not** avoid
the audit/provenance lane — it reopens exactly one narrow slice of it (below).

**Subordinate to, and may not contradict:**

```text
docs/TORMENT_AUDIT_CALLER_OWNED_SAME_TURN_PROVENANCE_CONTRACT_v0.1.md      (what an out-of-AgentRunner caller must satisfy; co-location ≠ provenance)
docs/TORMENT_AUDIT_PRIVATE_OWNER_LIVE_WIRING_GATE_FRAME_v0.1.md            (gate criteria + stop rule)
docs/TORMENT_AUDIT_PRIVATE_OWNER_LIVE_WIRING_DECISION_FRAME_v0.1.md        (W-1…W-8 gate; §9 flip-to-forbidden)
docs/TORMENT_AUDIT_PRIVATE_OWNER_W7_SIDECAR_ONLY_DECISION_FRAME_v0.1.md    (owner = generation path CLOSED)
docs/TORMENT_AUDIT_PRIVATE_OWNER_SIDECAR_CALLER_PATH_DECISION_FRAME_v0.1.md (W-1 caller-path Option A / HOLD)
docs/TORMENT_AUDIT_PRIVATE_OWNER_SIDECAR_OWNER_SHAPE_PROPOSAL_v0.1.md      (Option B: no safe owner shape on paper)
the audit-owner lane is PARKED by Hilmir Option C — this frame does NOT reopen it.
```

Where this frame and any parent contract / guard appear to differ, the contract / guard
wins. This frame narrows; it relaxes nothing.

Standing posture carried verbatim:

> Memory may shape context. Memory may not seize authority.
> Audit observes authority. Audit must not become authority.

Anchor: `bc63e39` (repo edge). Source terrain verified at this anchor (line numbers in §4).

## 2. Scope / required stance

```text
U1 reopens ONLY the narrow audit-evidence CALLER-PATH question:
  "Who, if anyone, may live-supply `audit_admitted_context_items` to the existing
   inert observation seam, and under what admissibility conditions?"

U1 does NOT:
  - reopen audit-owner / private-owner wiring (the W-7 / W-1 / Option C lane stays parked);
  - select a caller path (no caller is named as selected unless Hilmir explicitly
    accepts a named caller AS the decision in a later step);
  - authorize production wiring;
  - authorize tests (a later step may select tests; this frame writes none);
  - make a same-turn provenance claim, or define any truth / authority / ownership flag.
```

**Honest correction (per Codex REVISE):** U1 is *not* provenance-free. The seam is inert,
but the act of feeding it real `audit_admitted_context_items` from a live caller is the
**caller-owned same-turn provenance question** governed by
`docs/TORMENT_AUDIT_CALLER_OWNED_SAME_TURN_PROVENANCE_CONTRACT_v0.1.md`. U1 resolves only
the *admissibility* of that caller-path on paper; it does not resolve the provenance
obligation and does not claim to.

## 3. Current live-but-dormant seam (content #1)

```text
- TurnResult carries two optional fields, both default None:
    audit_admitted_context_items   (agent_loop.py:200)
    audit_evidence_packet          (agent_loop.py:209)
- AgentRunner.run_turn(...) (agent_loop.py:503) accepts keyword-only
    audit_admitted_context_items=None (agent_loop.py:510).
- Every turn, run_turn calls
    _audit_evidence_packet = self._observe_audit_evidence_from_prompt_request(
        prompt_request, audit_admitted_context_items, final_response)   (agent_loop.py:728)
  and returns the result ONLY on TurnResult.audit_evidence_packet (agent_loop.py:756).
- The observer (_observe_audit_evidence_from_prompt_request, agent_loop.py:999) returns
  None unless final response AND caller-supplied items AND a captured request all exist;
  otherwise it composes the observation-only packet, fail-soft.

The seam is therefore LIVE (wired into run_turn) but DORMANT in production: no production
caller passes `audit_admitted_context_items`, so the packet is always None on real turns.
```

## 4. Why the seam itself is inert / observation-only (content #2)

Locked today by the pre-wiring guard `tests/test_audit_private_owner_pre_wiring_guard.py`
(PW-1…PW-8) and siblings — these are **already green** and must stay green:

```text
PW-2  PrivateGenerationOwner remains unwired / unimported / uncalled / unconstructed.
PW-3  No prompt-surface mutation is bundled into the handoff site.
PW-4  The built packet value drives NO branch (module-wide) and routes ONLY to TurnResult.
PW-5  Packet absence is non-punitive; the observation sits under try/except (fail-soft).
PW-6  No writer / memory / retrieval / Gate A / Gate D / DB reachability.
PW-7  Evidence is observed AROUND generation, never inside it; composed from the FINAL response.
Plus: exact prompt-request carry-through stays observation terrain only (request runner-local,
      never on TurnResult / ExecutionOutcome / metadata / self / endpoint / schema / persistence).
```

So the seam cannot, by construction, steer output, review, retry, ranking, style, memory,
retrieval, or authority. Its inertness is a property of the seam, independent of any caller.

## 5. Why making it live is still a caller-path authorization problem (content #3)

The inertness of the seam does **not** make a live caller free. Three facts make the
caller-path its own authorization question:

```text
(a) No honest live caller path exists yet. Characterized green:
    tests/test_audit_provenance_caller_inventory.py — app.py does not import/call run_turn;
      /retrieve has assembled context but no generated response_text; /agent/query returns
      fabric.query(...) not generated text; no production caller passes audit_admitted_context_items.
    tests/test_audit_selected_items_caller_path_characterization.py (ec17d2e) — current topology.
(b) The only approved bridge is a dead-end. run_turn_with_selected_items_observation(...)
    (audit_selected_items_runner_bridge.py) forwards selected_admitted_items into
    run_turn(..., audit_admitted_context_items=...) but is CALLED NOWHERE in production
    (verified: sole non-test reference is its own definition).
(c) Supplying items is a PROVENANCE act, not a free observation. Per the caller-owned
    provenance contract, the caller — not AgentRunner — owns the claim that the supplied
    items were selected/admitted for the SAME turn that produced response_text. Structural
    co-location on TurnResult is NOT provenance. So "just wire a caller" silently makes a
    same-turn claim the system is not yet authorized to make.
```

Therefore making the seam live is gated on **caller-path admissibility**, not on the
seam's inertness.

## 6. Four-way distinction (content #4)

```text
1. AUDIT-EVIDENCE CALLER-PATH ADMISSIBILITY  ← THIS frame's only subject.
   Whether/how a caller may live-supply audit_admitted_context_items to the inert seam.
   Observation-only target; no owner; no provenance claim resolved here.

2. AUDIT-OWNER / PRIVATE-OWNER PROVENANCE  ← PARKED (Hilmir Option C); NOT reopened.
   A separate owner proving selected item text is present in the model-visible context
   (W-1…W-8 / PrivateGenerationOwner). Hard-HOLD: no safe owner shape on paper (Option B).

3. FULL ENVELOPE AUDIT RUNTIME  ← DEFERRED.
   A real truthfulness/evidence envelope over model cognition (Document B §7). Needs a
   model-API track or duplicates ReflectionTrace; not opened here.

4. GATE D / PRIVATE COGNITION  ← DEFERRED, substrate-gated.
   Durable private-cognition / Document B interior runtime; blocked behind the A-wall
   enforcement path (carrier = substrate). Not opened here.

U1 is strictly item 1. It does not advance, imply, or authorize items 2–4.
```

## 7. Candidate admissibility conditions for any future caller (content #5)

A future caller, **if ever proposed** (separately, under Hilmir authorization + Codex
review), would have to satisfy all of:

```text
- Be a single, sanctioned, named internal caller (not app.py, not an endpoint).
- Own the same-turn provenance claim per the caller-owned provenance contract — supply
  ONLY pre-extracted admitted item dicts for the SAME turn, never an AssembledContext.
- Pass items ONLY into run_turn(audit_admitted_context_items=...); never into prompt /
  review / ingest / writer / model-visible context.
- Read nothing back off the result to drive behavior (packet stays observation-only).
- Add no endpoint / API / schema, no new TurnResult field, no prompt exposure.
- Keep absence non-punitive and failure fail-soft.
- Make no truth / authority / ownership / same_turn_verified claim.
No such caller is selected, designed, or authorized in this frame.
```

## 8. Tests required before any production wiring (content #6)

These are **named as future obligations only** — this frame writes none. Existing locks
that MUST remain green (cite, do not duplicate): PW-1…PW-8
(`test_audit_private_owner_pre_wiring_guard.py`), `test_audit_provenance_caller_inventory.py`,
`test_audit_selected_items_caller_path_characterization.py`,
`test_audit_selected_items_runner_bridge.py`, `test_audit_live_owner_candidate_inventory.py`.

A future wiring step would additionally need:

```text
- SANCTIONED-CALLER AST guard: EXACTLY the one approved caller may pass
  audit_admitted_context_items; all other service / endpoint / runner-owner paths remain
  forbidden (extends the ec17d2e "exactly one approved bridge" invariant to a live caller).
- No endpoint / app.py expansion unless separately authorized (app.py / endpoints remain
  non-callers of run_turn-with-audit-items).
- Prompt surface unchanged; no selected item text injected into prompt / messages.
- Packet routes ONLY to TurnResult.audit_evidence_packet (reaffirm PW-4).
- Packet presence/absence drives NO branch and changes NO response / review / retry /
  ranking / style / write / retrieval behavior (reaffirm PW-4).
- Absent selected text yields None, fail-soft and non-punitive (reaffirm PW-5).
- No prompt-request exposure on TurnResult / ExecutionOutcome / metadata / logs / debug /
  endpoint / schema / persistence / self.
- PrivateGenerationOwner remains unwired / unimported / uncalled / unconstructed (reaffirm PW-2).
```

## 9. Forbidden crossings (explicit)

```text
- no production code
- no tests (in this artifact)
- no activation / no live wiring
- no caller selected (unless a later step explicitly frames a named caller AS the decision)
- no same-turn provenance claim
- no same_turn_verified / truth / authority / ownership flag
- no endpoint / API / schema change
- no prompt mutation / exposure
- no output-control / review / suppression
- no memory-write path
- no retrieval-authority expansion
- no database / substrate / carrier / schema / storage / migration
- no Gate D / private cognition runtime
- no dream / incubation runtime
- no Envelope Audit runtime beyond discussing this inert seam
- no R-field
- no Gate B writer-authority
- no Probe-v1
- no new shaping slice
- no reopening of the audit-owner owner/provenance lane (Option C stays)
```

## 10. Future gate

```text
- This frame authorizes NO implementation, tests, or wiring.
- Resolving the caller-path admissibility one way (a named future caller) requires a
  SEPARATE Hilmir decision that explicitly accepts that caller AS the decision, plus
  Codex review; only THEN may the sanctioned-caller test be written, and only after that
  may any production wiring be proposed — each a separate authorization.
- The caller-owned provenance contract and PW-1…PW-8 remain binding throughout.
- No §0 pointer beyond the minimal Last-closed record after review + commit.
```

## 11. Anti-drift footer

TORMENT AUDIT — AUDIT-EVIDENCE U1 CALLER-PATH ADMISSIBILITY / DOCS-ONLY /
NON-AUTHORIZING. It resolves only the narrow question of whether a future caller may
live-supply `audit_admitted_context_items` to the already-existing inert observation seam
(`AgentRunner.run_turn` → `_observe_audit_evidence_from_prompt_request` →
`TurnResult.audit_evidence_packet`), which is LIVE-but-DORMANT (no production caller). It
records that the seam is inert/observation-only by the green PW-1…PW-8 guard, but that
making it live is still a **caller-path provenance authorization problem** — supplying
items is a same-turn provenance act owned by the caller (co-location ≠ provenance), and no
honest live caller exists today; the only approved bridge is a dead-end. It separates
audit-evidence caller-path admissibility (this frame) from audit-owner/private-owner
provenance (PARKED, Option C), full Envelope Audit runtime (deferred), and Gate D / private
cognition (deferred, substrate-gated). It lists candidate admissibility conditions and the
tests a future wiring would need — naming the new sanctioned-caller AST guard and citing
PW-1…PW-8 rather than duplicating them. **It authorizes no production code, no tests, no
activation, no live wiring, no caller selection, no same-turn provenance claim, no truth /
authority / ownership flag, no endpoint / API / schema, no prompt mutation / exposure, no
output-control / review / suppression, no memory-write, no retrieval-authority expansion,
no database / substrate, no Gate D / private cognition, no dream runtime, no Envelope Audit
runtime, no R-field, no Gate B writer-authority, no Probe-v1, and no new shaping slice; it
does not reopen the audit-owner lane.** Any next step requires separate Hilmir authorization
plus Codex review. Guidance not control; audit observes authority and does not become
authority; nothing rewrites identity / canon / seed / soul.

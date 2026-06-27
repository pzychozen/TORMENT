# TORMENT — Memory-to-Prompt-for-Generation Same-Turn Dual-Ownership / Orchestration Decision Frame v0.1

## 1. Status / non-authorization

**Decision frame. Docs-only / NON-AUTHORIZING / no lane opened / fence closed / seam
dormant.** Hilmir authorized **only this decision frame**; Codex PASS. It answers exactly
one question: whether the memory-to-prompt live-caller lane may advance **later** to a
separately authorized CALLER-PROPOSAL, or must remain **HOLD**. It **selects no caller**,
**invents no orchestration site**, **wires nothing**, writes **no code and no tests**, and
makes **no endpoint / API / schema / public-surface change**. Where this frame and any
parent contract/guard differ, the contract/guard wins.

Standing posture carried verbatim:

> Memory may shape context. Memory may not seize authority.
> Audit observes authority. Audit must not become authority.

Anchor: `669de81` (repo edge). Subordinate to, and may not contradict: the
memory-to-prompt live-caller eligibility frame (`2cc5210`), the landed dormant slice
(`5d04658`), the production implementation proposal, the design frame, the source-baseline
lock + correction (`tests/test_memory_to_prompt_generation_boundary_characterization.py`),
the candidate proof-contract lock
(`tests/test_memory_to_prompt_candidate_proof_contract.py`), the caller-owned same-turn
provenance contract, and the PW-1…PW-8 pre-wiring guard.

## 2. Current edge and source chain

```text
- 5d04658  feat(cognition): add runner-local memory prompt context
           — landed the dormant, optional, runner-local `memory_context_text` seam inside
             AgentRunner (_execute_with_prompt_request → _execute → _build_llm_prompt_request
             → _build_memory_context_message); one bounded labelled read-only guidance
             message before the raw user input; ≤1200 stripped chars; _build_system_prompt /
             _LLMPromptRequest unchanged and runner-local. Dormant by default: no live caller
             passes memory_context_text.
- 8540dca  docs(project): record runner-local memory prompt-context slice (5d04658)
- 2cc5210  docs(cognition): frame memory-to-prompt live caller eligibility
           — source-verified terrain audit; conclusion HOLD, no existing eligible live
             caller (generation ownership and assembled-context ownership are disjoint).
- 669de81  docs(project): record memory-to-prompt live-caller eligibility frame (2cc5210)
           — current repo edge; this frame's anchor.
```

This frame adds **no commit-bearing source change** beyond itself and its §0 pointer. It
renders only the decision the eligibility frame (`2cc5210`) explicitly left open.

## 3. The exact decision question (Codex-approved, verbatim)

> Given that no existing source site owns both governed `AssembledContext.assembled_text`
> or a bounded derivative and authoritative `AgentRunner` generation invocation in the same
> turn, may TORMENT proceed to a later, separately authorized caller proposal for a
> same-turn orchestration owner that owns both halves, while preserving all current fences;
> or must the memory-to-prompt live-caller lane remain HOLD?

## 4. What changed and what did not change

```text
CHANGED since the eligibility frame (2cc5210):
- Nothing in source. No code, no tests, no wiring landed.
- The only delta is this decision document and its §0 pointer.

DID NOT CHANGE:
- The runner-local memory_context_text seam stays DORMANT (no live caller passes it).
- Ownership stays DISJOINT (see §5): no site owns both halves in one turn.
- Every fence from 2cc5210 and the prior chain stays CLOSED.
- The live-caller lane stays HOLD.
```

This frame is a **process / admissibility decision ABOUT a possible future move** — it is
not itself a move on the lane. It decides whether a later CALLER-PROPOSAL is admissible; it
does not make, design, or authorize that proposal.

## 5. Current ownership split (source-grounded, carried from `2cc5210`)

The two required halves of an eligible same-turn live caller:

```text
HALF 1 — GOVERNED ASSEMBLED MEMORY CONTEXT
   eligible AssembledContext.assembled_text (or a bounded derivative) produced through
   existing governed read/assembly paths.
HALF 2 — AUTHORITATIVE AgentRunner GENERATION INVOCATION
   a path that can pass memory_context_text into the dormant runner-local seam
   (i.e. it invokes AgentRunner generation for that same turn).
```

Source-verified ownership today (unchanged from the eligibility frame):

```text
SITE                                            | HALF 1 (assembled_text) | HALF 2 (generation invocation)
------------------------------------------------+-------------------------+-------------------------------
AgentRunner.run_turn / _execute (agent_loop.py) | ✗ frame = observation   | ✓ owns generation + the
                                                |   .text via             |   dormant memory_context_text
                                                |   controller            |   seam; run_turn does NOT
                                                |   .deliberate_only;      |   pass memory_context_text
                                                |   no assemble_context /  |
                                                |   AssembledContext /     |
                                                |   assembled_text         |
_build_llm_prompt_request /                     | ✗                       | seam owner (consumes the
_build_memory_context_message (agent_loop.py)   |                         |   optional arg), NOT a caller
/agent/query (app.py)                           | ✗ returns fabric.query;  | ✗ no AgentRunner / run_turn
                                                |   retrieval + MemoryPlan |
/retrieve · retrieve_assembled (app.py)         | ✓ fabric.query +         | ✗ no AgentRunner / run_turn /
                                                |   assemble_context →     |   llm_client.complete
                                                |   assembled_text         |
assemble_context / AssembledContext             | ✓ produces assembled_   | ✗ stdlib-only; no generation
(retrieval_assembler.py)                        |   text                   |   invocation
```

No row owns **both** halves. `audit_admitted_context_items` on `run_turn(...)` is separate
audit-staging routed **only** to `TurnResult`, never into the prompt path. **Conclusion
(unchanged): no existing eligible live caller → HOLD.**

## 6. Eligible future orchestration-owner requirements

A future same-turn orchestration owner could become a live-caller **CANDIDATE** only if a
**separately authorized** proposal proves ALL of:

```text
R1  SAME-TURN DUAL OWNERSHIP — in one turn it owns BOTH
      (a) governed AssembledContext.assembled_text or a bounded derivative produced
          through existing governed read/assembly paths; AND
      (b) an authoritative AgentRunner generation invocation able to pass
          memory_context_text into the dormant runner-local seam.
R2  FENCE PRESERVATION — it preserves every fence in §9; specifically:
      - AgentRunner stays runner-local and does NOT acquire retrieval/assembly authority;
      - /retrieve stays read-only / context-source terrain, NOT generation terrain;
      - app.py / endpoints make no wiring / endpoint-behavior / API / schema /
        public-surface change;
      - PrivateGenerationOwner stays excluded / unwired / non-authoritative;
      - the selected-items audit bridge stays negative terrain only.
R3  SOURCE-GROUNDED — every claim about the owner's terrain is verified against actual
      source, not assumed.
R4  SEPARATE AUTHORIZATION — Hilmir authorizes and Codex reviews the CALLER-PROPOSAL
      BEFORE any caller is selected; code + tests come together only in a later,
      separately authorized slice.
R5  GUIDANCE-NOT-AUTHORITY — supplied context stays one bounded, labelled, read-only,
      turn-local, non-authoritative guidance block; no exposure, no control, no feedback,
      no persistence.
```

This frame **defines** R1–R5 as requirements for any future proposal. It **satisfies none
of them and selects nothing.**

## 7. Terrain comparison

```text
AgentRunner.run_turn / _execute
  - Owns HALF 2 (generation + the dormant seam), NOT HALF 1.
  - Cannot self-become the owner without acquiring retrieval/assembly authority — which is
    FORBIDDEN (must stay runner-local). NOT the owner.

/retrieve · retrieve_assembled · assemble_context
  - Own HALF 1 (governed assembled_text), NOT HALF 2.
  - Making them invoke generation would expand read-only / context-source terrain into
    generation terrain — FORBIDDEN. NOT the owner.

app.py / /agent/query
  - Today owns neither both halves (retrieval + MemoryPlan only).
  - May be INSPECTED as a possible future orchestration locus ONLY; remains EXCLUDED from
    wiring / endpoint behavior / API / schema / public-surface change / caller selection
    here. NOT selected.

audit bridge (audit_selected_items_runner_bridge.py)
  - Passes audit_admitted_context_items (never memory_context_text); routes nothing into
    the prompt path; called nowhere in production.
  - NEGATIVE TERRAIN only; selecting it would risk reopening U1 / audit-owner. EXCLUDED.

PrivateGenerationOwner (audit_private_generation_owner.py)
  - A separate, generation-path-shaped owner (calls its own generation boundary).
  - Excluded / unwired / non-authoritative; W-7 forecloses owner-as-generation. EXCLUDED.

possible NEW same-turn caller
  - Admissible ONLY as a FUTURE POSSIBILITY, to be specified and separately authorized
    later. NOT invented, named, designed, or selected here.
```

## 8. Decision options

```text
(A) HOLD as the sole outcome
    Keep the lane closed indefinitely; admit no future caller proposal.
    REJECTED as the sole outcome — it would foreclose a legitimate, separately-authorizable
    future move with no source reason to do so.

(B) Later CALLER-PROPOSAL admissible
    The lane may advance LATER to a separately authorized CALLER-PROPOSAL for a same-turn
    orchestration owner that owns both halves (R1) and preserves all fences (R2–R5).
    SELECTED — with the strict constraint that nothing is selected or wired now and HOLD
    persists until such a proposal is filed and approved.

REJECTED ROUTES (now):
  - selecting any caller;
  - inventing / naming / designing an orchestration site;
  - wiring app.py / endpoints;
  - reusing PrivateGenerationOwner;
  - reusing the audit bridge;
  - expanding AgentRunner to own retrieval/assembly;
  - turning /retrieve into a generation owner;
  - any code / tests / endpoint / schema / public-surface change.
```

**Net answer to §3, in order:** the lane **REMAINS HOLD now**, AND a later separately
authorized CALLER-PROPOSAL is **ADMISSIBLE** (not foreclosed). This frame decides only that
admissibility — never the proposal, the caller, or the wiring.

## 9. Non-authority / forbidden list (this step)

```text
- no code
- no tests
- no wiring
- no caller selection
- no endpoint / API / schema / public-surface change
- no retrieval-authority expansion
- no memory write / persistence
- no review / output-control / suppression / retry / ranking / style steering
- no U1 / audit-owner reopening
- no PrivateGenerationOwner
- no dual-ownership orchestration implementation
- no Gate D / private cognition / dream / Envelope Audit runtime
- no database / substrate / carrier / schema / storage / migration
- no Gate B / R-field / Probe-v1 / shaping
```

This document decides admissibility of a FUTURE proposal only. Nothing above is selected,
wired, designed, or authorized.

## 10. Final verdict

**A later CALLER-PROPOSAL for a same-turn orchestration owner that owns both halves is
ADMISSIBLE — but ONLY if separately authorized by Hilmir + Codex, source-grounded, and
fence-preserving.** Until such a proposal is filed and approved, the memory-to-prompt
live-caller lane **REMAINS HOLD**: no caller is selected, no orchestration site is invented,
nothing is wired, no code or tests are written, and no endpoint / API / schema /
public-surface changes. **This frame selects no caller now.**

## 11. Anti-drift footer

TORMENT — MEMORY-TO-PROMPT-FOR-GENERATION SAME-TURN DUAL-OWNERSHIP / ORCHESTRATION DECISION
FRAME / DOCS-ONLY / NON-AUTHORIZING / NO LANE OPENED / FENCE CLOSED / SEAM DORMANT. It
renders only the decision the eligibility frame (`2cc5210`) left open — whether the lane may
advance later to a separately authorized CALLER-PROPOSAL, or must remain HOLD. It carries the
source-verified ownership split unchanged (AgentRunner owns generation + the dormant
`memory_context_text` seam but NOT governed assembled context; `/retrieve` + `assemble_context`
own governed `assembled_text` but NOT generation; `/agent/query` owns retrieval + MemoryPlan
only — so no site owns both halves in one turn), states the requirements any future
orchestration owner must satisfy (R1 same-turn dual ownership; R2 fence preservation; R3
source-grounded; R4 separate Hilmir + Codex authorization; R5 guidance-not-authority), and
selects option (B): **a later CALLER-PROPOSAL is admissible ONLY if separately authorized,
source-grounded, and fence-preserving — it is not foreclosed, but no caller is selected,
invented, or wired now, and the lane remains HOLD until that proposal lands.** It selects no
caller, invents no orchestration site, wires nothing, writes no code/tests, changes no
endpoint/API/schema/public surface, expands no retrieval authority, reopens no U1/audit-owner,
wires no PrivateGenerationOwner, opens no lane, and lifts no fence. Guidance not control;
audit observes authority and does not become authority; nothing rewrites identity / canon /
seed / soul.

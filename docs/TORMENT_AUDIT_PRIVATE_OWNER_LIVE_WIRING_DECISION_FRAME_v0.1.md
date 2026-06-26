# TORMENT Audit — Private Owner Live-Wiring Decision Frame v0.1

## 0. Status / authorization scope

**Docs-only decision frame. This document renders the live-wiring gate VERDICT for
Shape A and defines the exact preconditions a future slice must satisfy; it
authorizes no code, tests, wiring, endpoint, schema, prompt mutation, memory write,
admission mechanism, or runtime control.** It selects no caller path and builds
nothing. Crossing any precondition into implementation requires a separate, explicit
Hilmir authorization plus Codex review.

This is the decision the live-wiring **gate frame** left open: that frame defined the
admissibility *criteria* (§3–§5) and the stop rule (§6) but rendered no verdict. This
frame renders the verdict (§7) and consolidates the preconditions (§8). It does
**not** re-run the topology proof (already green — §4) or re-state the gate frame's
criteria beyond citing them.

Held true throughout: no production code; no tests; no git; no endpoint / API /
schema expansion; no database / substrate; no memory writes; no writer paths; no
retrieval feedback; no ranking / suppression / retry / style steering / review /
output control; no audit-as-control; no prompt mutation (named only as a future
separately-gated question); no Gate A carrier / representation / admission /
promotion / transform mechanics; no Gate D / private cognition; no identity / canon /
seed / tier writes; no hidden output control.

Standing posture carried verbatim:

> Memory may shape context. Memory may not seize authority.
> Audit observes authority. Audit must not become authority.

Anchor: `3d0feaf` (origin/main; clean).

## 1. Subordination

Subordinate to, and may not contradict:

```text
docs/TORMENT_AUDIT_PRIVATE_OWNER_LIVE_WIRING_GATE_FRAME_v0.1.md         (the gate: §3 admissibility criteria, §4 forbidden surfaces, §5 proof shape, §6 stop rule)
docs/TORMENT_AUDIT_MODEL_VISIBLE_CONTEXT_OWNER_SEAM_DESIGN_v0.1.md       (owner responsibilities, call order, §4 non-reentry, §5 hidden-authority line)
docs/TORMENT_AUDIT_CALLER_OWNED_SAME_TURN_PROVENANCE_CONTRACT_v0.1.md    (caller owns the same-turn claim; pre-extracted item dicts only; co-location != provenance; packet absence non-punitive)
docs/TORMENT_MODEL_API_TRUTHFULNESS_AUDIT_ADMISSIBLE_EVIDENCE_PACKET_CONTRACT_v0.1.md   (§2/§5 same-turn, §4/§4A exclusions, §6 incomplete-evidence, §7 non-reentry)
tests/test_audit_live_owner_candidate_inventory.py + tests/test_audit_live_owner_path_selection_characterization.py   (topology proof — green)
torment_service/audit_private_generation_owner.py (Shape A) / audit_selected_items_runner_bridge.py (bridge)
```

Where this frame and any contract appear to differ, the contracts win. The Ledger
Observational-Boundary doctrine governs: *audit observes authority; audit does not
become authority.*

## 2. Doctrine filter

> Declaring conditional admissibility is a VERDICT about a candidate, not a wiring.
> "Admissible-for-future-guarded-wiring" authorizes nothing to be built; it records
> that the owner is a clean enough candidate that a future slice meeting the exact
> preconditions could be *considered* — under separate authorization.

## 3. The decision question

```text
Is `PrivateGenerationOwner` (torment_service/audit_private_generation_owner.py,
Shape A) admissible as a future internal, non-endpoint, observation-only live owner,
and what exact preconditions must be satisfied before any later tests or code slice?
```

## 4. What already exists (not duplicated here)

```text
- TOPOLOGY PROOF — already green; not re-run or re-stated:
    tests/test_audit_live_owner_candidate_inventory.py (20 tests) +
    tests/test_audit_live_owner_path_selection_characterization.py (11 tests).
    They prove: the five owner-relevant call sites' exact caller inventory; no endpoint /
    app.py / agent_loop.py is a live owner; AgentRunner owns prompt-capture only (not
    retrieval / assembly / extraction); the bridge is a dead-end, packet-blind forwarder;
    two-and-only-two candidate shapes; the audit packet is observation-only and drives no
    branch.
- ADMISSIBILITY CRITERIA — already defined by the gate frame §3 (the eight items a future
    proposal must specify), §4 (forbidden surfaces), §5 (required proof shape), §6 (stop
    rule). This frame REUSES them; it does not re-author them.
- CLOSED-AS-BUILT baseline — the observe-authority lane is built and dormant: Shape A exists
    unwired; the live observation spine in agent_loop.py is dormant (no live caller feeds
    audit_admitted_context_items); the packet is optional and non-punitive.
```

## 5. Shape A status (existing but unwired)

```text
- Shape A (`PrivateGenerationOwner`) EXISTS as a private module, CALLED NOWHERE in production
  (test-called only). Closed import surface: `__future__` / `typing` / `dataclasses` + the
  pure `selected_admitted_items` extractor + the inert `observe_prompt_inclusion_packet`
  observer. No model / provider / endpoint / agent_loop / retrieval_assembler / writer /
  persistence import.
- By construction it: holds ONE explicit AssembledContext in its own frame; extracts selected
  item dicts from that SAME object; renders + CAPTURES its exact prompt/messages before
  generation; sends only the captured prompt/messages to a duck-typed generation boundary;
  composes the observation-only packet ONLY after a final response exists and ONLY on observed
  inclusion (fail-closed otherwise); returns ONLY response text + optional packet — never the
  captured prompt/messages, never metadata; and BRANCHES ON NOTHING (the packet drives no
  control).
```

## 6. Why Shape B remains deferred / absent

```text
- Shape B (a private runner delegation seam) does NOT exist as a module and is DEFERRED. The
  selected-items runner bridge is a delegation-style FORWARDER, not a generation owner: it
  forwards selected item dicts into AgentRunner.run_turn and is a dead-end (called only by
  tests), packet-blind.
- Shape B sits closer to the runner boundary and risks AgentRunner silently owning retrieval /
  assembly / provenance (forbidden by the seam ADR §1 and gate frame §4). It is therefore NOT
  the admissible shape; if ever revisited it requires its own separate authorization.
- Consequence: of the two recorded shapes, exactly ONE exists as an internal non-endpoint
  candidate owner today — Shape A. This decision concerns Shape A only.
```

## 7. Decision

**OUTCOME: `admissible-for-future-guarded-wiring`.**

```text
`PrivateGenerationOwner` (Shape A) IS admissible as a FUTURE internal, non-endpoint,
observation-only live owner — under guarded wiring only, gated by separate Hilmir
authorization + Codex review, and ONLY if every precondition in §8 is met.

Basis: it is observation-only by construction (§5) — packet drives no branch, no memory
write, no output steering by the audit side, fail-closed, closed import surface — and the
gate frame's criteria already exist (§4). There is NO named blocker preventing a CONDITIONAL
admissibility verdict; what remains are PRECONDITIONS for the wiring itself, not blockers to
the verdict. (`not-admissible` is rejected: observation-only wiring can in principle be made
safe. `hold-pending-named-blocker` is rejected: no blocker prevents the conditional verdict.)

THIS AUTHORIZES NO WIRING NOW. It records that a future slice MAY be considered if §8 holds.
```

## 8. Exact preconditions before any future tests or code

A future wiring slice is admissible to *propose* only if it satisfies ALL of the gate
frame §3–§5 **and** the following (which sharpen them); a proposal missing any item
is inadmissible and the owner remains unwired (gate frame §6 stop rule):

```text
W-1  EXACT WIRING SITE NAMED. The precise internal, non-endpoint module + function that would
     invoke the owner in a live turn, and the call sequence around it, must be named by source.
     app.py and all public endpoints must remain non-callers. (This frame names no site — naming
     it is the future proposal's job.)
W-2  EVIDENCE-ONLY OWNERSHIP. The owner must record/prove MODEL-VISIBLE CONTEXT EVIDENCE ONLY —
     extract selected items from the SAME AssembledContext, capture the exact prompt/messages
     before generation, prove inclusion against the captured context, compose the packet only
     after the final response, fail closed otherwise (seam ADR §2/§3).
W-3  NO OUTPUT STEER. The owner must not steer output: the audit/inclusion result must not
     revise, block, rank, suppress, retry, style-steer, or affect review; the response is
     finalized independently of the packet, and review remains the only suppressor (seam ADR
     §5 hidden-authority line).
W-4  PACKET DRIVES NOTHING. The audit packet's presence or absence must drive no branch / retry
     / ranking / suppression / style / review / output / retrieval / write behavior; absence is
     non-punitive; observer/builder failure yields no packet and no error path.
W-5  NO REACHABILITY BY IMPLICATION. No writer / memory / persistence / retrieval-feedback /
     Gate A carrier-representation-admission-promotion-transform / Gate D / private-cognition
     path may become reachable from the owner by implication; the closed import surface must be
     preserved or tightened, never widened.
W-6  PROMPT-SURFACE CHANGE SEPARATELY GATED. Any change to the live model-visible prompt surface
     (what the model actually sees) must be EXPLICITLY NAMED and SEPARATELY PROVEN not to steer
     behavior beyond the plain response, as its own gated question — never bundled into this
     wiring admissibility. The owner renders its own prompt; if a live path's prompt surface
     would change, that is a separate authorization.
W-7  INTEGRATION SHAPE NAMED. The future proposal must name whether the owner BECOMES the live
     generation path or runs beside the existing one, and prove the chosen shape expands no
     AgentRunner retrieval/assembly/provenance ownership (seam ADR §1) and introduces no
     duplicate/divergent output control. (This is the open fork the live-owner path-selection
     characterization recorded; it must be resolved by source in the proposal, not here.)
W-8  TESTS/SOURCE FIRST. The §5 proof shape must land tests/source-first BEFORE any production
     wiring: a tests-only characterization of the named live caller path against a test-local
     generation boundary; source/AST guards (sanctioned-caller-only; app.py/endpoints
     non-callers; packet drives no branch; no prompt exposure; no AgentRunner ownership
     expansion; fail-soft/absence-non-punitive) extended to the new caller, never weakened.
```

## 9. What would make live wiring FORBIDDEN

```text
Live wiring is FORBIDDEN (the verdict flips to inadmissible for that proposal) if it would:
  - feed the audit packet/inclusion result into any control edge — revise / block / rank /
    suppress / retry / style-steer / affect review / change eligibility / become model-visible
    feedback / influence writer / retrieval / persistence / memory / fabric / authority (seam
    ADR §5; this is THE line);
  - make packet absence punitive or evidence of dishonesty/unsupportedness;
  - expose the captured prompt/messages on result / metadata / log / debug / endpoint / schema;
  - expand AgentRunner retrieval/assembly/extraction/provenance ownership, or silently absorb it;
  - add an endpoint / API / schema field, or make app.py / a public endpoint a caller;
  - introduce Shape B without its own separate authorization;
  - reach a writer / memory / persistence / database / substrate / retrieval-feedback / Gate A
    mechanics / Gate D / private-cognition path by any implicit edge;
  - change the live prompt surface without W-6's separate naming + proof;
  - skip the W-8 tests/source-first proof, or weaken any existing audit-lane guard.
Any one of these is disqualifying; failing to demonstrate §8 keeps the owner unwired (stop rule).
```

## 10. Non-authorization

```text
This document DOES NOT, and does not authorize by implication:
  - wire, select a caller path, or build anything; production code; tests; git
  - endpoint / API / schema expansion; prompt mutation (named only as a future gated question)
  - memory writes; writer paths; retrieval feedback; persistence; database / substrate
  - ranking / suppression / retry / style steering / review / output control; audit-as-control
  - Gate A carrier / representation / admission / promotion / transform mechanics
  - Gate D / private cognition; identity / canon / seed / tier writes; hidden output control
  - a §0 orientation-map pointer (added only if the decision lands AND Hilmir asks after review)
```

## 11. Anti-drift footer

TORMENT AUDIT — PRIVATE OWNER LIVE-WIRING DECISION FRAME / DOCS-ONLY / RENDERS A
VERDICT, AUTHORIZES NO WIRING. **Decision: `admissible-for-future-guarded-wiring`.**
Shape A (`PrivateGenerationOwner`) is admissible as a FUTURE internal, non-endpoint,
observation-only live owner — observation-only by construction (packet drives no
branch, no memory write, fail-closed, closed import surface), with no named blocker
to a conditional verdict — but ONLY under guarded wiring gated by separate Hilmir
authorization + Codex review, and ONLY if every §8 precondition holds (named wiring
site; evidence-only ownership; no output steer; packet drives nothing; no writer /
memory / Gate A / Gate D reachable by implication; prompt-surface change separately
gated; integration shape named; tests/source first). Shape B remains deferred /
absent; the topology proof already exists (green) and is not duplicated; the gate
frame's criteria are reused, not re-authored. Crossing the §9 forbidden conditions —
above all any feedback edge from audit output back into the turn — flips the verdict
to inadmissible. **This document authorizes no code, tests, wiring, endpoint, schema,
prompt mutation, memory write, admission mechanism, or runtime control.** The owner
remains unwired. Guidance not control; audit observes authority and does not become
authority; nothing rewrites identity / canon / seed / soul.

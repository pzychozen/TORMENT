# TORMENT Gate A — Containment Wall Enforcement-Path Proposal v0.1

## 1. Status / non-authorizing scope

**Docs/design only. PROPOSAL. NON-AUTHORIZING. Selects no mechanics.** This
artifact proposes *how a future Document A containment wall enforcement path could
be approached* and what it would have to prove. It **authorizes no
implementation**, selects no carrier / store / schema / field / API / runtime
wiring / code path, opens no gate, and changes no behavior. Every step it
describes is a **candidate** that requires **separate authorization** before any
code or test is written.

It uses, deliberately: *proposal*, *candidate seam*, *future proof obligation*,
*non-authorizing*, *separately authorized*. It avoids any wording implying an
implementation has been selected or that safety has already been achieved. The
terms **candidate store**, **admission crossing**, **promotion crossing**, and
**inspection surface** are used here as **requirement-level design vocabulary
only** — they are *not* collapsed into mechanics, and naming them is not selecting
or building them.

Standing posture carried verbatim:

> Memory may shape context. Memory may not seize authority.
> Audit observes authority. Audit must not become authority.

## 2. Subordination to Document A and the Gate A wall frame

This proposal is **subordinate** to, and may not contradict:

- Document A — Candidate Containment + Writer Authority Contract
  (`docs/TORMENT_CANDIDATE_CONTAINMENT_WRITER_AUTHORITY_CONTRACT_v0.1.md`):
  A-C1 / A-C2 / A-C3, A-O2 / A-O3, A-I1, A-D1 / A-D2 (admission/promotion
  separation), and the governed admission / governed promotion definitions.
- The Gate A containment-wall enforcement frame
  (`docs/TORMENT_GATE_A_DOCUMENT_A_CONTAINMENT_WALL_ENFORCEMENT_FRAME_v0.1.md`):
  wall boundary, live fan-out roots, §6 proof bars, Gate D dependency.

Where this proposal and those contracts could appear to differ, **the contracts
win.** This proposal proposes; it does not rule.

## 3. What the current resting-state proofs already establish

Tests-only / source-only characterizations have established the **resting state**
(no live private-cognition producer, no built wall mechanism):

- **Structural non-reachability by absence/topology** (`2732f32`): no live
  Document B / chamber entrypoint; the reflection-adjacent audit lane reaches no
  fan-out sink; the private generation owner and selected-items bridge are
  unwired; `/agent/query` stays retrieval/advisory; audit packets are non-control.
- **No-tag-dependence by absence** (`8f8fa7a`, A-C2): the scoped fan-out roots and
  the whole service tree gate on **zero** reflection-exclusion tags in gate
  positions — current non-reachability is by topology/absence, not honored tags.
- **Read-side projection-safety** (P4 O3/O4, `c73add5`) and **MemoryPlan shaping
  non-control** (`c67046b`): retrieval/projection surfaces are read/projection
  surfaces, not generation owners; shaping is bounded guidance, not authority.
- **Audit observe-authority lane sealed**: observation-only, unwired, packet-blind.

## 4. What they do NOT establish

The resting-state proofs characterize **a system with no candidate producer and
no wall mechanism.** They do **not** establish:

- that a wall would still hold **once an unadmitted-candidate producer exists**
  (the resting proofs hold partly *because nothing is produced*);
- **admission-sole-exit** with a real admission crossing present (A-O3 / A-D1);
- **staging ≠ admission ≠ promotion** with real staging/admission/promotion
  vocabulary present (A-D2);
- **structural non-reachability at the ingest fan-out root under a live chamber**
  (A-C1 / A-C2 against an actual producer, not against absence);
- **inspection ≠ projection** for real candidate inspection (A-I1 / A-C3 against
  actual contained artifacts, not only against today's general debug surfaces).

These remain **future proof obligations** for a separately authorized enforcement
slice. Nothing here closes them.

## 5. Future wall invariants (proposed, non-authorizing)

A future wall, if separately authorized, would have to hold these invariants
**by construction** (restating Document A as enforcement targets, selecting no
mechanism):

- **I-1 Structural non-reachability at the ingest fan-out root** — an unadmitted
  candidate cannot enter ordinary ingest or anything it fans out to (motif /
  drift / gravity / mood / role / deep / SRG / reinforcement / retrieval /
  projection / promotion), held at the ingest entry itself (A-C1).
- **I-2 No-tag-dependence** — non-reachability does not depend on downstream
  readers honoring an exclusion tag (A-C2); the `ws_section_2a_v1` precedent.
- **I-3 Throughout-containment inspectability without re-entry** — candidates stay
  inspectable / contestable / resettable / recoverable, and that inspectability is
  itself non-reentrant (A-C3 / A-I1).
- **I-4 Admission is the sole exit, capped at released / low-authority** — the only
  path out of containment into ordinary memory is a governed admission crossing,
  landing at no higher than released / low-authority; no side path converts a
  candidate (A-O3 / A-D1).
- **I-5 Staging / admission / promotion / inspection / projection / live-visibility
  kept distinct** — staging is not authority; admission is not promotion;
  promotion is a *separate* governed crossing; inspection is not projection;
  caller-visible is not prompt-visible (A-D2 / A-I1).
- **I-6 No silent canon / identity-tier / seed / long-half-life writes from
  cognition or reflection paths** — such writes require a governed promotion
  crossing (A-O2).

## 6. Candidate seam comparison (non-selecting)

Where a future wall *could* live. These are **design candidates only**; none is
selected, and a real design may combine or reject them. For each, the proposal
records only *what it would have to prove*.

- **Candidate Seam A — producer-side containment boundary.** The reflection
  chamber's output is held entirely within a candidate boundary that never touches
  the ordinary fan-out; only a governed admission crossing emits a released /
  low-authority ordinary write. *Would have to prove:* the producer has no edge to
  ingest/graph except through the admission crossing (I-1, I-4), by construction
  (I-2). *Trade-off to weigh later:* depends on a clean producer/boundary
  separation that does not yet exist.
- **Candidate Seam B — ingest-entry structural gate.** A single structural
  chokepoint at the ordinary-ingest fan-out root that only ordinary (non-candidate)
  material can pass, with contained artifacts structurally unable to arrive there.
  *Would have to prove:* the fan-out root is the *only* entry and is closed to
  candidates without tag-honoring (I-1, I-2). *Trade-off:* must demonstrate the
  root is genuinely the sole entry.
- **Candidate Seam C — class-bound writer-authority gate.** Writers reject
  cognition/reflection-origin `canon=True` / identity-tier / seed / long-half-life
  writes unless a governed promotion crossing authorized them. *Would have to
  prove:* A-O2 by construction at the writer, independent of payload flags or
  source presence (A-O1 is the matched obligation). *Trade-off:* this is
  write-side authority work (currently parked) and would need its own gate.
- **Cross-cutting candidate — inspection surface.** An observation surface modeled
  on the existing sealed audit owner/bridge posture (observation-only, unwired,
  packet-blind). *Would have to prove:* inspection is operator/governance-auditable
  only and non-reentrant (A-I1 / A-C3), reusing the proven non-control posture
  rather than inventing a new exposure.

The proposal **does not choose** among Seams A/B/C or any blend, and selects no
store/carrier/schema/field/API for any of them.

## 7. Proof-obligation matrix (non-selecting)

Each row maps a Document A obligation to the future proof a wall must satisfy and
the candidate seam(s) that would bear it. **No seam is selected; multiple are
listed where applicable.**

| Obligation | What a future wall must prove | Candidate seam(s) | Future guard class |
|---|---|---|---|
| **A-C1** non-reachability | a contained candidate reaches none of the fan-out roots, held at the ingest entry | Seam A, Seam B | structural source/AST + behavioral, against a real producer |
| **A-C2** structural not tag-honoring | non-reachability holds by construction, not by honored exclusion tags | Seam A, Seam B | no-tag-dependence guard (extends `8f8fa7a` to a live producer) |
| **A-C3** throughout-containment inspectability | candidates stay inspectable/contestable/resettable/recoverable without re-entry | inspection surface | read-only + non-reentry guard |
| **A-O2** no silent canon/identity from cognition | no cognition/reflection writer emits canon / identity-tier / seed / long-half-life directly | Seam C | writer-class guard (write-side; separately authorized) |
| **A-O3 / A-D1** admission sole exit, ≤ released/low-authority | the only candidate→ordinary path is a governed admission crossing capped at released/low-authority | Seam A, Seam B | admission-sole-exit guard (needs the crossing to exist) |
| **A-D2** admission ≠ promotion | any upgrade beyond released/low-authority is a separate governed promotion crossing; reversal needs its own crossing | Seam C | staging/admission/promotion distinctness guard |
| **A-I1** inspection ≠ projection | inspection is operator/governance-auditable only; not prompt/caller/retrieval/cognition/MemoryPlan visible unless separately surface-classified | inspection surface | projection-safety guard (extends `c73add5` O3/O4) |

## 8. Required future tests/source guards before any code

A future enforcement slice (separately authorized) must land, **tests/source
first, before any production code**, guards covering at least:

- structural non-reachability of a live candidate producer at the ingest fan-out
  root (A-C1) — by construction;
- no-tag-dependence under that live producer (A-C2);
- admission-sole-exit with the admission crossing present, capped at
  released / low-authority (A-O3 / A-D1);
- staging ≠ admission ≠ promotion distinctness, with reversal requiring its own
  crossing (A-D2);
- no silent canon / identity-tier / seed / long-half-life writes from
  cognition/reflection paths (A-O2);
- inspection read-only and non-reentrant (A-I1 / A-C3);
- deliberation-room containment: any private-thinking room is reachable only
  inside the wall, and `AgentRunner` / `/agent/query` gain no contained-artifact
  input — preserving the existing unwired, observation-only posture.

These are **future proof obligations only.** This proposal creates no tests and no
code.

## 9. Gate D dependency and stop condition

**Gate D dependency (carried):** no private-cognition runtime / Gate D runtime is
admissible until the wall enforcement path is **separately approved and proved**
by construction (the §8 guards landed in a later authorized slice). Building the
inhabitant before the wall would place unadmitted reflection one step from the
live fan-out root. Roadmap order **A-wall → P4 gates → Document B interior** is a
dependency, not a preference.

**Stop condition for this artifact:** it ends at *proposal*. The next substantive
move is a **separate Codex/operator authorization decision** on whether to open a
wall enforcement-path slice (and, if so, which candidate seam(s) and which §8
guards to require first). No mechanics, seam selection, or code follow from this
document by implication.

## 10. No-go list (verbatim, in force)

```
No production code.
No tests.
No Gate D runtime.
No Envelope Audit runtime.
No private-owner live wiring.
No Shape B.
No endpoint/schema/API changes.
No prompt exposure.
No AgentRunner ownership expansion.
No database/substrate mechanics.
No carrier/schema/field selection.
No writer fixes.
No P4 O1/O2 mechanics.
No Seed-Gov mechanics.
No retrieval feedback.
No persistence changes.
No autonomy.
No audit-to-control feedback.
No candidate store.
No governed admission implementation.
No promotion-crossing implementation.
```

---

**Anti-drift footer.** PROPOSAL / NON-AUTHORIZING / OPENS NOTHING. It proposes a
future enforcement path and maps proof obligations; it selects no mechanics, opens
no gate, writes no code or tests, and changes no runtime. Guidance not control;
audit observes authority and does not become authority; nothing rewrites identity
/ canon / seed / soul. Any next step requires separate trio/operator authorization.

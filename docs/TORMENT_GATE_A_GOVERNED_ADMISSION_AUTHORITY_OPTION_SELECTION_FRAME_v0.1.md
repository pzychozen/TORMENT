# TORMENT Gate A — Governed Admission Authority-Option Selection Frame v0.1

## 0. Status / authorization scope

**Requirement-level authority-option selection only. This document selects the
requirement-level authority floor that future governed admission must require; it
designs no workflow, actor, UI, API, schema, record, carrier, runtime, persistence,
policy engine, admission mechanism, transform mechanism, or promotion mechanism, and
claims no wall completion. Admission remains unbuilt. Any tests, code, representation,
or crossing mechanism requires separate Hilmir authorization plus Codex review.**

The governed-admission authority model frame listed four authority options and
selected none (Document A §14 OPEN). Codex identifies this as the **one safe
remaining Gate A blocker**: the governed admission crossing is the *sole exit* from
containment, and the authority it must require has been undefined. This frame
**decides** that — it selects the requirement-level authority floor (§5) and
nothing else. It answers one question (§3).

Held true throughout: no production code; no tests; no git; no carrier / store /
schema / field / enum / ID / API / runtime / persistence; no producer; no policy
engine; no governed admission, transform, or promotion mechanism; no workflow /
actor / UI; no Gate A wall completion; no Gate D; no Gate B; no writer fixes; no
database / substrate; no endpoint expansion; no Layer 4 reopening; no second brick
series; no audit-as-control; no identity / canon / seed / tier writes.

Standing posture carried verbatim:

> Memory may shape context. Memory may not seize authority.
> Audit observes authority. Audit must not become authority.
> Automatic remains allowed only where separately ratified. Autonomous remains unopened.

Anchor: `466df83` (origin/main; Gate A meta-candidate admission decision recorded).

## 1. Subordination

Subordinate to, and may not contradict:

```text
docs/TORMENT_CANDIDATE_CONTAINMENT_WRITER_AUTHORITY_CONTRACT_v0.1.md   (Document A: A-O1/A-O3, A-D1/A-D2, §8 admission, §14 OPEN admission-authority)
docs/TORMENT_GATE_A_GOVERNED_ADMISSION_AUTHORITY_MODEL_FRAME_v0.1.md   (the four options; admission != promotion; authority is a crossing requirement)
docs/CLUSTER_2_AUTHORITY_GATE_v0.1.md                                  (promotion-rights vocabulary §7.1: operator-required / user-co-sign / governance-required / not-promotable / self-promotable)
docs/TRACK_B_DISAGREEMENT_RUNTIME_v0.1.md                             (operator-scope asymmetry; contestant_actor=user DEFERRED to Cluster 3 / Track C)
docs/TORMENT_GATE_A_FORK3_PER_ARTIFACT_ADMISSION_REFINEMENT_FRAME_v0.1.md + the C4b/C4c decision   (only a C4a may face admission; meta never admits-as-self)
docs/TORMENT_GATE_A_PRE_CARRIER_REPRESENTATION_CONSTRAINTS_FRAME_v0.1.md   (representation unbuilt; inert)
```

Where this frame and any contract appear to differ, the contracts win. This frame
**closes Document A §14's admission-authority open question** at requirement level.

## 2. Doctrine filter

> Selecting an authority floor is a requirement-level rule about *which class of
> governed decision may admit* — not a workflow, actor implementation, or policy
> engine. "A governed operator decision is necessary" fixes a floor; it designs no
> decision procedure.

## 3. The question and options

```text
Which requirement-level authority option should future governed admission require?
  operator-only          a governed operator decision admits.
  user co-sign           admission requires a user co-signature alongside a governed decision.
  governance-required    admission requires a governed governance condition (policy / quorum / gate).
  remain future-policy-unselected   keep Document A §14 OPEN.
```

## 4. Evaluation (source-grounded)

```text
operator-only  (Cluster 2: operator-required)
  + Strongest single-party human gate; clearest accountability; smallest attack surface.
  + Source-grounded precedent for operator-decision crossings: decide_proposal,
    /workspace/.../decide, governance set (set_governance_flags) are operator decisions.
  + Forecloses the unsafe readings directly (self / automatic / retrieval / audit-derived /
    user-only admission).
  + A FLOOR: it can only be made STRICTER later (add co-sign / governance) by separate
    ratification, never accidentally weakened.
  - Heavier than strictly necessary for <= released/low-authority admission — but admission is
    the SOLE exit from containment, rare, and a human gate at the one entry into ordinary
    memory is the conservative default for a sensitive system.

user co-sign  (Cluster 2: user-co-sign)
  - PRESUPPOSES a "user authority" actor model that is explicitly DEFERRED: Track B defers
    contestant_actor=user to Cluster 3 / Track C; no user-authority model exists. Selecting it
    now leans on an undefined actor. PREMATURE.
  + Remains available as a future STRENGTHENING on top of the operator floor.

governance-required  (Cluster 2: governance-required)
  - "governance condition / policy / quorum" risks IMPLYING a policy-engine / quorum MECHANISM
    (forbidden here), and is vaguer than a single accountable operator. RISKS MECHANICS BY
    IMPLICATION.
  + Remains available as a future STRENGTHENING on top of the operator floor.

remain future-policy-unselected
  - Leaves the SOLE-EXIT authority undefined — LESS safe than pinning the floor, because a
    future admission step could then be proposed under a weaker authority model. Does not
    resolve the named blocker.
  + Maximally non-committal (the prior status).
```

## 5. Decision

**DECISION — select `operator-only` (Cluster 2 `operator-required`) as the
requirement-level authority FLOOR for governed admission.**

```text
Future governed admission MUST require a governed operator decision as a NECESSARY
condition. This is a FLOOR, not a ceiling:
  - it may be STRENGTHENED later (e.g. add user co-sign and/or a governance condition,
    making admission two-party / multi-condition) ONLY by a separate ratified decision;
  - it may NEVER be weakened below a governed operator decision without a separate ratified
    decision;
  - it is satisfiable by NOTHING LESS — explicitly NOT by self-promotion, automatic /
    side-effect emission, retrieval or reinforcement, audit / inspection observation, a
    user-only act, or a quorum / governance condition WITHOUT a governed operator decision.
```

This closes Document A §14's admission-authority open question conservatively: the
strongest single-party human gate is the floor; the weaker-leaning or
mechanism-implying options (user co-sign, governance-required) are reserved as
future *strengthenings*, and "unselected" is retired because it left the sole-exit
authority dangerously open. **No decision procedure, actor implementation, UI, API,
schema, or policy engine is selected or implied.**

## 6. Preserved invariants

```text
- Candidate-shaped outputs remain NOT-SELF-PROMOTABLE — the operator floor reinforces this
  (the candidate's producer is never the admitting authority).
- Authority is a CROSSING REQUIREMENT, not a property of payload / source / flag / artifact
  (A-O1) — the floor attaches to the crossing, not to the item.
- C4b contradiction/risk flags and C4c unresolved questions may NEVER admit-as-self; only a
  separate transformed C4a positive proposal may later face governed admission at <= released
  / low-authority — and that C4a crossing now carries the operator-required floor.
- AUDIT / INSPECTION remains observation-only and CANNOT authorize a crossing (Ledger
  directionality) — the floor explicitly excludes audit-derived admission.
- `/promote` force remains PARKED force-bypass anti-pattern territory — it is the opposite of
  this floor (force BYPASSES the governed decision; this floor REQUIRES it). Not fixed here.
- Admission != promotion (A-D2): this floor governs the admission crossing only; promotion is
  a separate authority decision, unselected here.
```

## 7. What remains deferred / unbuilt

```text
- the admission decision PROCEDURE / workflow / actor implementation / UI / API — none designed.
- the candidate PRODUCER (Document B), CARRIER / representation (Stage B / pre-carrier), and
  RUNTIME crossing (Layer 4) — all deferred / gated.
- the C4b/C4c -> C4a TRANSFORM mechanism — deferred (requirement-level only).
- the PROMOTION authority option (beyond released/low-authority) — separate, unselected.
- whether to later STRENGTHEN the floor to user co-sign and/or governance-required — a future
  ratified decision; not opened here.
- This decision binds future design; it builds nothing and presupposes no built mechanism.
```

## 8. Non-authorization

```text
This document DOES NOT, and does not authorize by implication:
  - design a workflow, actor, UI, API, schema, record, carrier, runtime, persistence, policy
    engine, admission mechanism, transform mechanism, or promotion mechanism
  - select the promotion authority option, or strengthen the admission floor (that is a later
    ratified decision)
  - production code; tests; git
  - Gate A wall completion; Gate D; Gate B; writer fixes (incl. /promote force)
  - candidate producer / store; database / substrate; Stage B; Document B interior
  - endpoint / API / schema expansion; reopening the Layer 4 brick series; a second brick series
  - audit / inspection turned into control; identity / canon / seed / tier writes
  - any actual admission of any artifact (none exist to admit)
```

## 9. Anti-drift footer

GATE A GOVERNED ADMISSION AUTHORITY-OPTION SELECTION FRAME / REQUIREMENT-LEVEL ONLY /
SELECTS A FLOOR, NO MECHANISM. **Decision: governed admission must require a governed
operator decision (Cluster 2 `operator-required`) as a NECESSARY FLOOR — strengthenable
later (user co-sign / governance condition) only by separate ratification, never
weakened below it, and satisfiable by nothing less (not self / automatic / retrieval /
audit-derived / user-only / quorum-without-operator admission).** This closes Document
A §14's admission-authority open question conservatively; user co-sign is rejected as
leaning on the deferred user actor and governance-required as risking a policy-engine by
implication (both reserved as future strengthenings), and "unselected" is retired as
leaving the sole exit dangerously open. Candidate-shaped outputs stay not-self-promotable;
authority is a crossing requirement, not a payload property; C4b/C4c never admit-as-self
(only a transformed C4a faces admission, now under this floor); audit / inspection stays
observation-only and cannot authorize a crossing; `/promote` force stays parked.
**This document selects the requirement-level authority floor that future governed
admission must require; it designs no workflow, actor, UI, API, schema, record, carrier,
runtime, persistence, policy engine, admission mechanism, transform mechanism, or
promotion mechanism, and claims no wall completion. Admission remains unbuilt. Any tests,
code, representation, or crossing mechanism requires separate Hilmir authorization plus
Codex review.** Gate A stays paused; Gate D parked; the parked writer non-conformances
stay parked. Guidance not control; audit observes authority and does not become authority;
nothing rewrites identity / canon / seed / soul.

# TORMENT Gate A — Fork 3 C4b/C4c Residual Admission Decision Frame v0.1

## 0. Status / authorization scope

**Docs-only per-artifact disposition decision frame. This document may decide
requirement-level admission eligibility for C4b/C4c artifact classes, but selects no
carrier, schema, store, enum, field, ID, API, runtime path, producer, authority
option, admission workflow, or promotion mechanism. Admission remains unbuilt. Any
tests, code, representation, or crossing mechanism requires separate Hilmir
authorization plus Codex review.**

The per-artifact admission refinement frame set C4b/C4c to a stricter-than-admission
DEFAULT and flagged a **residual open sub-question**: may contradiction/risk-flag
(C4b) and unresolved-question (C4c) candidates ever cross governed admission *as
themselves*, or only after transformation into a separate C4a proposed write? This
frame **decides** that residual question at requirement level (§6). It answers one
question (§3) and nothing else.

Held true throughout: no production code; no tests; no git; no carrier / store /
schema / field / enum / ID / API / runtime / persistence; no producer; no governed
admission; no promotion; no authority-option selection; no Gate A wall completion;
no Gate D; no Gate B; no writer fixes; no database / substrate; no endpoint
expansion; no Layer 4 reopening; no second brick series; no audit-as-control; no
identity / canon / seed / tier writes; no hidden output control.

Standing posture carried verbatim:

> Memory may shape context. Memory may not seize authority.
> Audit observes authority. Audit must not become authority.

Anchor: `2349dac` (origin/main; CandidateShapedValue inertness lock recorded).

## 1. Subordination

Subordinate to, and may not contradict:

```text
docs/TORMENT_CANDIDATE_CONTAINMENT_WRITER_AUTHORITY_CONTRACT_v0.1.md   (Document A: §3/§4 taxonomy; A-O2/A-O3, A-D1/A-D2; creation != admission != promotion)
docs/TORMENT_GATE_A_CANDIDATE_BOUNDARY_ADMISSION_REQUIREMENTS_v0.1.md  (Layer-3: admission = crossing condition; nothing automatic; ceiling not guarantee)
docs/TORMENT_GATE_A_FORK3_PER_ARTIFACT_ADMISSION_REFINEMENT_FRAME_v0.1.md   (the classes C1-C4 + the residual open sub-question this frame closes)
docs/TORMENT_GATE_A_GOVERNED_ADMISSION_AUTHORITY_MODEL_FRAME_v0.1.md   (outcome categories; admission != promotion; authority option UNSELECTED)
docs/TORMENT_GATE_A_FORK3_CANDIDATE_BOUNDARY_GOVERNED_ADMISSION_DESIGN_FRAME_v0.1.md   (boundary = property)
docs/TORMENT_GATE_A_PRE_CARRIER_REPRESENTATION_CONSTRAINTS_FRAME_v0.1.md   (representation unbuilt; inert)
```

Where this frame and any contract appear to differ, the contracts win.

## 2. Doctrine filter

> A disposition decision is a **requirement-level rule** that constrains future
> design — not a mechanism. Deciding "a warning may never admit as itself" selects
> no carrier, crossing, or workflow; it fixes a property a future design must honor.

## 3. The question this frame answers (and only this)

```text
Can C4b contradiction/risk flags and C4c unresolved questions ever cross governed
admission AS THEMSELVES, or must they remain stricter-than-admission unless
transformed into a separate C4a proposed write?
```

## 4. Working distinction (preserved)

```text
C4a  proposed write / staged synthesis  a POSITIVE CONTENT proposal (object-level content).
C4b  contradiction / risk flag          a warning / objection — META about content, not content.
C4c  unresolved question                an open question — META about content, not content.
```

C4b/C4c are **meta artifacts**: they are *about* content, they are not content. That
type difference is the hinge of the decision.

## 5. The disposition options considered

```text
admit-as-self            the meta artifact itself crosses governed admission into ordinary
                         memory at <= released/low-authority.
never-admit-as-self      the meta artifact may NEVER cross as itself.
transform-then-propose   if a durable ordinary-memory effect is wanted, a SEPARATE C4a positive
                         content proposal is authored and IT goes through future governed
                         admission; the meta artifact itself never crosses.
audit-only               observable on an audit surface only; no admission.
operator-visible-only    operator/governance inspection only; no admission.
chamber-only             stays in the bounded chamber; no admission.
refused / no-persist     admission denied (operator-scope; Track B asymmetry).
retired                  dropped/expired; no cognition effect.
```

## 6. Decision

**DECISION — Option 2: C4b and C4c may NEVER admit-as-self. They remain
stricter-than-admission. If a durable ordinary-memory effect is ever wanted, the
meta artifact must first be TRANSFORMED INTO A SEPARATE C4a proposed write that
states a positive content proposal, and only that C4a goes through future governed
admission (at no higher than released / low-authority). The C4b/C4c artifact itself
never crosses.**

Per-class disposition (requirement-level; no mechanism):

```text
C4b contradiction / risk flag
  admit-as-self          FORBIDDEN.
  never-admit-as-self    DECIDED.
  transform-then-propose the ONLY route to durable ordinary-memory effect: author a NEW C4a
                         positive proposal (e.g. "record/assert <the substantive claim>"); that
                         C4a — not the flag — faces future governed admission, capped at
                         released/low-authority. The flag is the trigger, never the admitted item.
  audit-only             ALLOWED (default home — governance attention).
  operator-visible-only  ALLOWED (default home).
  chamber-only           ALLOWED.
  refused / no-persist   ALLOWED (operator-scope).
  retired                ALLOWED.

C4c unresolved question
  (identical disposition to C4b — same meta-artifact reasoning; the transform is a NEW C4a
   positive proposal that answers or operationalizes the question, never the question itself.)
```

## 7. Reasoning

```text
R1  Category integrity. A warning / objection / question is ABOUT content; it is not content.
    Admitting it as itself collapses the meta level into the object level — the exact
    creation != admission and meta != content non-collapse Document A §2 protects.
R2  Authority direction. Meta candidates may only route authority DOWN or hold it, never raise
    it (Track B Invariant 10 analog). Admitting-as-self would let a meta artifact INJECT
    ordinary-memory authority — raising, not lowering. Forbidden by direction.
R3  Steelman reduction. Every legitimate "durable flag/question" need reduces to a POSITIVE
    content proposal — "record that X was flagged risky", "assert the contradiction between X
    and Y", "register the open question Q for later". Each of those IS a C4a. So no case
    actually requires a meta-admission path; transform-then-propose covers all legitimate needs
    without one.
R4  Visibility without admission. audit-only / operator-visible-only already satisfy "make the
    flag/question visible to governance" WITHOUT ordinary-memory entry. Governance attention
    needs no admission, so the meta artifact needs no admit-as-self route to be useful.
R5  Smaller attack surface. A never-admit-as-self rule means a future wall needs NO
    meta-admission mechanism at all — one fewer crossing kind, one fewer way for non-content to
    acquire cognition-shaping authority. Conservative by construction.
```

## 8. Why not the other options

```text
Option 1 (C4b/C4c may admit-as-self) — REJECTED. It would require a meta-admission crossing
  whose only legitimate uses already reduce to C4a (R3), adding mechanism, a new crossing kind,
  and authority-direction risk (R2) for no unique benefit. The audit-only / operator-visible-only
  outcomes already cover visibility (R4).

Option 3 (undecidable) — REJECTED. The question is a requirement-level DISPOSITION (a rule that
  constrains future design), decidable now exactly as the per-artifact frame already set
  defaults. It does NOT depend on the producer / carrier / crossing existing — those are
  DOWNSTREAM of the rule, not prerequisites for it. Nothing is missing to decide the rule; what
  is missing (producer, carrier, crossing) is what the rule will later constrain.
```

## 9. What remains deferred / unbuilt

```text
- the TRANSFORM itself (authoring a C4a from a C4b/C4c) — requirement-level only; no mechanism,
  producer, or workflow is selected here.
- the C4a governed admission crossing it would then face — deferred (authority option UNSELECTED;
  admission UNBUILT).
- the candidate producer (Document B interior), carrier/representation (Stage B / pre-carrier),
  and runtime (Layer 4) — all deferred / gated.
- per-class contest/recovery specifics — Track B runtime (deferred).
- This decision binds future design; it builds nothing and presupposes no built mechanism.
```

## 10. Non-authorization

```text
This document DOES NOT, and does not authorize by implication:
  - select / design a carrier, schema, store, enum, field, ID, API, runtime path, producer,
    authority option, admission workflow, promotion mechanism, or a transform mechanism
  - production code; tests; git
  - Gate A wall completion; Gate D; Gate B; writer fixes
  - candidate producer / store; database / substrate; Stage B; Document B interior
  - endpoint / API / schema expansion; reopening the Layer 4 brick series; a second brick series
  - audit / inspection turned into control; identity / canon / seed / tier writes; hidden output
    control
  - any actual admission, transform, refusal, retirement, or promotion of any artifact (none
    exist to act on)
```

## 11. Anti-drift footer

GATE A FORK 3 — C4b/C4c RESIDUAL ADMISSION DECISION FRAME / REQUIREMENT-LEVEL ONLY /
DECIDES A DISPOSITION, SELECTS NO MECHANISM. **Decision: C4b (contradiction / risk
flag) and C4c (unresolved question) may NEVER admit-as-self; they remain
stricter-than-admission (audit-only / operator-visible-only / chamber-only / refused
/ retired), and the only route to a durable ordinary-memory effect is to transform
the meta artifact into a SEPARATE C4a positive content proposal that itself faces
future governed admission at no higher than released / low-authority — the flag /
question never crosses as itself.** Grounded in category integrity (meta != content),
authority direction (meta routes down, never up), the steelman reduction (every
durable need is already a C4a), visibility-without-admission, and a smaller attack
surface. Option 1 rejected (no unique need; adds a crossing); Option 3 rejected (the
rule is decidable now; the missing mechanics are downstream, not prerequisites).
**This document may decide requirement-level admission eligibility for C4b/C4c
artifact classes, but selects no carrier, schema, store, enum, field, ID, API,
runtime path, producer, authority option, admission workflow, or promotion mechanism.
Admission remains unbuilt. Any tests, code, representation, or crossing mechanism
requires separate Hilmir authorization plus Codex review.** Gate A stays paused;
Gate D parked; the parked writer non-conformances stay parked. Guidance not control;
audit observes authority and does not become authority; nothing rewrites identity /
canon / seed / soul.

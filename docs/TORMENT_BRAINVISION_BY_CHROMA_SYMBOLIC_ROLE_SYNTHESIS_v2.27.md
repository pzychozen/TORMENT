# TORMENT Brainvision BY/Chroma Symbolic Role Synthesis & Boundary Decision v2.27

## 1. Status / Scope

**DOCS-ONLY synthesis and boundary DECISION.** This is a synthesis note only. It opens **no** code, **no** tests, **no**
runtime, and **no** integration lane; it authorizes **no** implementation, and it is not corrective. It sits over the
accepted v2.26 edge (`35d3707 research(brainvision): add by chroma symbolic role reporting`) and changes none of the
accepted files.

**v2.27 synthesizes v2.22–v2.26 and decides the next safe direction.** It reads the arc as a whole, states what has and
has not been established, treats Role D (BY/chroma entangled) as a **central warning rather than a failure to hide**,
and recommends a single docs-only next path. It decides a direction; it implements nothing.

**v2.27 authorizes nothing.** It introduces and authorizes **no** implementation, tests, fixture instances, fixture
data, descriptor, coordinate system, numeric geometry, metric, equation, threshold, scoring, pass/fail gate,
validation, closure, real clip, screen / camera / live / sensor / streaming path, runtime path, memory path, prompt /
context / action / render-body / autonomy contact, classifier (form B), or neural encoder (form C). It makes **no**
production vision claim, **no** "Brainvision sees" claim, **no** temporal-order claim, and **no** descriptor-validity /
geometry-validity / screen-readiness / memory-readiness / runtime-readiness / integration-readiness claim. Everything
stays offline under `research/brainvision/` + `tests/research/`, HELD per v0.6. **HOLD / HELD means held for analysis
and claim control — not abandoned.**

```text
flat_field_validated                        = False
role_validated                              = False
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed                      = False
descriptor_validity_claim_allowed           = False
geometry_validity_claim_allowed             = False
screen_readiness_claim_allowed              = False
runtime_readiness_claim_allowed             = False
memory_readiness_claim_allowed              = False
integration_readiness_claim_allowed         = False
vision_claim_allowed                        = False
verdict                                      = HOLD
```

**No `§0` pointer; no tags.**

## 2. The Arc, Stated Plainly (v2.22 → v2.26)

```text
v2.22  FRAMED THE QUESTION.
       "Can future synthetic design distinguish BY-axis residual behavior from generic chroma proxy effects without
        adopting metrics or closure claims?"  (Formulation A -- in force)
       And bound it: "Residual localization must not imply descriptor validity."  (Formulation C -- in force)

v2.23  BOUNDED FIXTURE DESIGN WITHOUT DESIGNING FIXTURES.
       Fixed what a future design document may contain (conceptual roles) and may not contain (fixtures, data
       structures, formulas, metrics, thresholds, expected outputs, pass/fail criteria).

v2.24  PROPOSED SIX SYMBOLIC FAMILY ROLES.
       A BY-dominant chroma residual; B generic chroma proxy; C matched non-BY chroma; D BY/chroma entangled;
       E fixture-family artifact; F null / reporting-boundary. Names for what a case would be FOR. No fixtures.

v2.25  REVIEWED THE IMPLEMENTATION BOUNDARY.
       Specified the ALLOWED shape of a possible v2.26 (static symbolic role reporting + a conservative canonical
       checker), the FORBIDDEN shape (data, descriptors, coordinates, metrics, scores, thresholds, validation,
       screen / runtime / memory, classifier / neural, vision), and five mandatory guard conditions. A gate, not a
       green light.

v2.26  IMPLEMENTED STATIC SYMBOLIC ROLE REPORTING ONLY.  (committed 35d3707)
       A deterministic builder over exactly the six roles + a conservative canonical check_protocol. Every role is
       role_generated = True and role_validated = False. Every claim lock, adoption flag, and authorization guard is
       False and its group is CLOSED. verdict = HOLD. Outcome label
       BRAINVISION_BY_CHROMA_SYNTHETIC_FIXTURE_ROLES_REPORTING_ONLY.
```

## 3. What v2.26 Established — And What It Did Not

```text
ESTABLISHED (and only this):
  E1. The six roles are EXPRESSIBLE as guarded static symbolic objects with no fixture, no data, no coordinate, no
      descriptor, no metric, no score, no threshold, and no pass/fail surface. Expressibility is a fact about NAMING.
  E2. GENERATED IS NOT VALIDATED, held in code and in tests: role_generated = True, role_validated = False, and the
      checker breaches on any role marked validated.
  E3. A conservative BOUNDARY-COMPLIANCE gate exists over that expression. Protocol greenness means the boundary held
      (v2.14) -- nothing else.
  E4. The claim surface did NOT need to grow. No number, no comparison, and no gate was required to say what each role
      is FOR -- evidence that the v2.24 role set was conceptual rather than covertly metric.

NOT ESTABLISHED (explicitly):
  N1. v2.26 did NOT resolve the BY/chroma isolation question. Naming roles is not distinguishing residual from proxy.
  N2. v2.26 did NOT validate roles, descriptors, geometry, metrics, or visual structure. Nothing was measured.
  N3. v2.26 produced NO closure, NO validation, and NO vision readiness. None of these follow from it, and none may be
      inferred from it later.
  N4. v2.26 produced NO evidence about colour AT ALL. It is an artifact about LANGUAGE and CLAIM CONTROL, not about
      BY-axis behavior.
```

**v2.26 is useful because it exposed the decision point.** Its value is not that it advanced the colour question — it
did not, and could not. Its value is that, once the six roles were forced into a guarded static form, the fork the
programme was walking toward became visible *before* any fixture was built: the design cannot proceed to concrete
fixtures without first deciding what it will do when the honest answer is **entangled**.

## 4. Role D Is The Result, Not The Residue

```text
ROLE D -- BY/CHROMA ENTANGLED ROLE -- is the CENTRAL WARNING of this arc.

It says: BY-axis residual pressure and generic chroma proxy pressure MAY NOT BE SEPARABLE AT ALL. It is not a gap in
the design, not a caveat, not an unfinished corner, and not a failure to be hidden, minimised, or engineered around. It
is the possibility the entire v2.22 question must survive.

THE PROJECT MUST NOT COLLAPSE ROLE D INTO ANY OF THESE:
  - into NOISE      ("entanglement just means our cases were sloppy; tighten them and it will separate")
  - into FAILURE    ("we could not separate them, so the work failed / the branch is dead")
  - into SUCCESS    ("entanglement is itself an interesting positive finding about colour")
Each collapse is a claim. None is licensed. Entanglement, if it is real, is a statement about the QUESTION, not a
result about the WORLD -- and v2.26 measured nothing, so nothing about the world is known here either way.

ENTANGLEMENT MAY BE THE HONEST RESULT. A design that can only emit "BY-dominant" or "generic proxy" cannot express
that; it would be forced to pick a bucket, and a forced pick is a manufactured separation (v2.24 Role E: the fixtures
may manufacture the effect). The prior frozen evidence -- directional / spectral / centroid entanglement that survived
every matched-pair and residual audit from v1.1 through v2.9 -- is exactly what a forced bucket would launder into a
false distinction.
```

## 5. The Decision Point v2.26 Exposed

```text
The programme now stands at a fork, and it must be taken CONSCIOUSLY:

  PATH 1 (REFUSED FOR NOW): go straight to concrete fixture implementation.
    A fixture bank built today would have to assign cases to BY-dominant / generic-proxy roles in order to be a bank at
    all. Whatever came out would be reported in a vocabulary that has no way to say "entangled" as a FIRST-CLASS
    outcome -- only as a leftover. The result would be a separation that the reporting language, not the colour,
    produced. This is the v2.22 Formulation-B hazard and the v2.24 Role E suspicion, arriving as an implementation.

  PATH 2 (RECOMMENDED): decide FIRST how entanglement gets reported, and only then consider fixtures.
    Until the programme can report "unresolved / entangled / proxy-confounded" as a VALID, NON-DEFICIENT outcome, it is
    not ready to generate cases whose reporting would silently exclude that outcome.

DECISION: the next safe direction is NOT concrete fixture implementation. Fixtures stay CLOSED until the project has
defined how to report entanglement WITHOUT PRETENDING SEPARATION.
```

## 6. Standing Of The Six-Role Scaffold

```text
The six-role symbolic scaffold (v2.24 proposed; v2.26 reported) is ALLOWED AS REPORTING LANGUAGE ONLY.

  IT MAY BE:  a vocabulary for naming what a conceptual case would be FOR; a claim-control scaffold; a reporting frame
              that a later document may reuse BY IDENTITY.
  IT IS NOT:  a fixture taxonomy, a case-assignment scheme, a label set for classifying anything, a partition of any
              space, an ontology of visual structure, a validated set of categories, or evidence that six roles are the
              right number, or that any one of them is realizable, useful, or correct.

Reusing the scaffold's WORDS is permitted. Reusing it as a SORTING MECHANISM is not: the moment a case is placed into
role A or role B, the scaffold has become a bucket, and Role D has become a leftover. That is precisely the drift v2.27
exists to refuse.
```

## 7. Recommended Next Path (one; docs-only)

```text
RECOMMEND (primary, and the only recommended path):

  v2.28  ENTANGLEMENT-AWARE REPORTING-BOUNDARY PLAN  (DOCS-ONLY)

  It would ask -- and only ask:
    "Can BY/chroma residual behavior be reported in a way that preserves ENTANGLEMENT as a FIRST-CLASS OUTCOME, rather
     than forcing separation into BY vs generic chroma buckets?"

  IN SCOPE for v2.28 (planning language only):
    - what a reporting frame would have to be able to SAY for "entangled" to be a first-class outcome rather than a
      residue or a failure;
    - what non-claim outcomes must be permanently expressible: UNRESOLVED, ENTANGLED, PROXY-CONFOUNDED;
    - what would make a reporting frame DISHONEST (any frame in which "entangled" can only appear as noise, error,
      leftover, or deficiency);
    - which claim locks stay False, and what stays unmeasured;
    - the conditions under which the question may be UNANSWERABLE, and how that would be said out loud.

  OUT OF SCOPE for v2.28 (all of it):
    - fixtures, fixture data, case banks, stimuli; data structures, arrays, images, pixels;
    - descriptors, coordinates, numeric geometry, metrics, equations, thresholds, scores, weights, ratios;
    - pass/fail gates, acceptance criteria, expected outputs, validation, closure;
    - screen / real-clip / camera / live / sensor / streaming / runtime / memory paths;
    - classifier (form B), neural (form C), vision;
    - any implementation, any test, any code.

  v2.28 STAYS DOCS-ONLY unless separately reviewed and operator-approved otherwise. v2.27 does not open it: the
  operator chooses whether v2.28 opens at all, and any v2.28 must be separately bounded, Codex-reviewed, and
  operator-approved.

NOT RECOMMENDED (explicitly): concrete fixture implementation; descriptor / coordinate / numeric-geometry / metric /
equation / threshold / scoring / pass-fail work; validation or closure work; screen / real-clip / runtime / memory
work; classifier (B) or neural (C) work; any vision work.
```

## 8. Binding Constraint On Any Later Fixture Work

```text
IF a fixture implementation is ever approved -- and none is approved here -- it must carry this constraint from the
start, not retrofit it:

  "UNRESOLVED", "ENTANGLED", and "PROXY-CONFOUNDED" must remain VALID NON-CLAIM OUTCOMES.

  - VALID: they are permitted terminal outcomes of the work, not error states.
  - NON-CLAIM: they assert nothing about colour, nothing about a descriptor, nothing about geometry, and nothing about
    vision. "Entangled" is not a finding; it is a refusal to manufacture a distinction.
  - NOT DEFICIENT: a run that ends entangled has not failed, has not underperformed, and does not indicate that the
    cases need tightening until they separate. Tightening cases until they separate IS the manufacturing hazard.
  - NOT PROVISIONAL: they may not be treated as placeholders awaiting a "real" answer, and may not be silently
    upgraded, averaged away, or excluded from reporting.

Any design in which these three outcomes cannot be reported as first-class is OUT OF BOUNDS by construction.
```

## 9. Forbidden Drift Register

```text
- Role D becoming NOISE, FAILURE, or SUCCESS (Section 4). All three are claims; none is licensed.
- "entangled" becoming a LEFTOVER BUCKET -- the label applied to whatever did not sort cleanly into A or B.
- the six-role scaffold becoming a FIXTURE TAXONOMY, a case-assignment scheme, a classifier label set, a neural target
  set, or a visual ontology.
- v2.26's protocol greenness becoming VALIDATION, correctness, distinguishability, descriptor validity, or readiness.
- v2.26 becoming an IMPLEMENTATION LICENCE (it licenses nothing; it reported six names).
- "the roles are expressible" becoming "the roles are right / useful / real".
- a synthesis note becoming an AUTHORIZATION; a decision to plan becoming a decision to build.
- residual localization becoming DESCRIPTOR VALIDITY; isolation becoming CLOSURE; falsification becoming VALIDATION.
- prior BY / color / chroma evidence becoming SOLVED PROOF (it stays FROZEN UNRESOLVED evidence).
```

## 10. Non-Claim Interpretation

```text
WHAT v2.27 MAY ESTABLISH (and only this):
  - a SYNTHESIS of what v2.22-v2.26 did and did not establish;
  - a DECISION that concrete fixture implementation is not the next safe direction;
  - a single recommended docs-only next path (v2.28), gated on operator approval;
  - a binding constraint on any later fixture work, should any ever be approved.

WHAT IT DOES NOT ESTABLISH:
  not an implementation     not a fixture / data / metric        not a descriptor / coordinate
  not validation            not closure                          not that the residual is distinguishable
  not that the residual is INDISTINGUISHABLE                     not readiness
  not vision                not authorization of anything

The v2.22 question REMAINS UNRESOLVED. v2.27 does not answer it, does not narrow it, and does not measure anything. It
observes that the programme cannot honestly ask it with a reporting vocabulary that has no first-class word for
ENTANGLED -- and that supplying that word is a matter of language and claim control, not of evidence.
```

## 11. Verdict

```text
verdict                                      = HOLD
flat_field_validated                         = False
role_validated                               = False
first_pass_structure_validity_claim_allowed  = False
temporal_claim_allowed                       = False
descriptor_validity_claim_allowed            = False
geometry_validity_claim_allowed              = False
screen_readiness_claim_allowed               = False
runtime_readiness_claim_allowed              = False
memory_readiness_claim_allowed               = False
integration_readiness_claim_allowed          = False
vision_claim_allowed                         = False

OUTCOME_LABEL: BRAINVISION_BY_CHROMA_SYMBOLIC_ROLE_SYNTHESIS_ONLY
```

v2.27 is a docs-only synthesis and boundary decision. It states what v2.22–v2.26 established (six roles are expressible
as guarded static symbolic objects; generated is not validated; a boundary-compliance gate exists) and what they did
not (no resolution of the BY/chroma isolation question; no validation of roles, descriptors, geometry, metrics, or
visual structure; no closure; no vision readiness); treats Role D as the central warning rather than a failure to hide;
holds the six-role scaffold to reporting language only; decides that concrete fixture implementation is **not** the
next safe direction until the project defines how to report entanglement without pretending separation; recommends one
docs-only next path (a v2.28 entanglement-aware reporting-boundary plan); and binds any later fixture work to preserve
"unresolved / entangled / proxy-confounded" as valid non-claim outcomes. It authorizes nothing and is not
self-authorizing. All claim locks and the frozen verdict **HOLD** are preserved and unmoved.

## 12. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_BY_CHROMA_SYMBOLIC_ROLE_SYNTHESIS_v2.27.md
(new, docs-only, untracked; over the accepted v2.26 edge
 "35d3707 research(brainvision): add by chroma symbolic role reporting").

Verify that this synthesis:
- is docs-only and authorizes NOTHING (no code / tests / schema; no torment_service/; no fixture data; no descriptors /
  coordinates / numeric geometry / metrics / equations / thresholds / scores / pass-fail gates; no validation /
  closure; no screen / real-clip / camera / live / sensor / streaming / runtime / memory paths; no classifier (form B)
  / neural (form C); no vision); adds no §0 pointer and no tags;
- grounds the arc correctly: v2.22 framed the question (distinguish BY-axis residual behavior from generic chroma
  proxy effects without adopting metrics or closure claims) and its Formulation-C constraint; v2.23 bounded fixture
  design without designing fixtures; v2.24 proposed six symbolic family roles; v2.25 reviewed the implementation
  boundary; v2.26 implemented static symbolic role reporting only;
- states plainly that v2.26 did NOT resolve the BY/chroma isolation question and did NOT validate roles, descriptors,
  geometry, metrics, or visual structure; and that no closure, validation, or vision readiness follows from it;
- says explicitly that v2.26 is USEFUL BECAUSE IT EXPOSED THE DECISION POINT;
- treats Role D (BY/chroma entangled) as a CENTRAL WARNING, not a failure to hide; forbids collapsing Role D into
  noise, failure, or success; and states that ENTANGLEMENT MAY BE THE HONEST RESULT;
- holds the six-role symbolic scaffold to REPORTING LANGUAGE ONLY (not a fixture taxonomy, case-assignment scheme,
  classifier label set, neural target set, or visual ontology);
- concludes the v2.22 question REMAINS UNRESOLVED, and DECIDES that the next safe direction is NOT concrete fixture
  implementation unless the project first defines how to report entanglement without pretending separation;
- recommends exactly ONE primary next path -- a DOCS-ONLY "v2.28 entanglement-aware reporting-boundary plan" asking
  whether BY/chroma residual behavior can be reported in a way that preserves entanglement as a first-class outcome
  rather than forcing separation into BY vs generic chroma buckets -- and keeps it docs-only unless separately
  reviewed; is NOT self-authorizing;
- binds any later fixture implementation to preserve "unresolved / entangled / proxy-confounded" as VALID NON-CLAIM
  outcomes (valid, non-claim, not deficient, not provisional);
- preserves the locks and verdict (Section 11): flat_field_validated = False; role_validated = False;
  first_pass_structure_validity_claim_allowed = False; temporal_claim_allowed = False;
  descriptor_validity_claim_allowed = False; geometry_validity_claim_allowed = False;
  screen_readiness_claim_allowed = False; runtime_readiness_claim_allowed = False;
  memory_readiness_claim_allowed = False; integration_readiness_claim_allowed = False; vision_claim_allowed = False;
  verdict = HOLD; interprets HOLD/HELD as held for analysis, not abandoned.

Flag any fixture / instance / bank / data structure / schema / formula / metric / score / threshold / coordinate /
descriptor / expected output / pass-fail criterion defined anywhere; any treatment of Role D as noise, failure, or
success; any use of the six roles as a sorting or classification mechanism; any implication that v2.26 validated,
closed, separated, or measured anything; any authorization of implementation; any claim that the residual IS
distinguishable or IS indistinguishable; any readiness / vision / capability claim; or any claim-lock / verdict
movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`flat_field_validated = False`, `role_validated = False`, all claim locks False, and the frozen verdict **HOLD** are
unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision BY/Chroma Symbolic Role Synthesis & Boundary Decision v2.27. Docs-only synthesis and
direction decision over the accepted v2.26 edge. Opens no implementation lane, no tests, and no fixture generation;
opens no classifier / neural / screen / real-clip / runtime / memory work; adopts no descriptor / coordinate system /
numeric geometry / metric / equation / threshold / scoring / pass-fail rule; defines no fixture, data structure,
formula, numeric parameter, score, threshold, or expected output; synthesizes v2.22 (question framed), v2.23 (fixture
design bounded without designing fixtures), v2.24 (six symbolic family roles proposed), v2.25 (implementation boundary
reviewed), and v2.26 (static symbolic role reporting implemented, committed 35d3707); states that v2.26 resolved
nothing about BY/chroma isolation and validated no role, descriptor, geometry, metric, or visual structure, and that it
is useful precisely because it exposed the decision point; treats Role D (BY/chroma entangled) as the central warning
and forbids collapsing it into noise, failure, or success; holds the six-role scaffold to reporting language only;
decides that concrete fixture implementation is not the next safe direction until entanglement can be reported without
pretending separation; recommends one docs-only next path (v2.28 entanglement-aware reporting-boundary plan); binds any
later fixture work to preserve "unresolved / entangled / proxy-confounded" as valid non-claim outcomes; keeps prior BY /
color / chroma work FROZEN EVIDENCE, the flat opponent-field symbolic branch PAUSED HELD, and the v2.22 question
UNRESOLVED and possibly unanswerable; is not self-authorizing; preserves all claim locks and the frozen verdict HOLD;
makes no vision / "Brainvision sees" / descriptor-validity / geometry-validity / temporal-order / readiness claim;
outcome label BRAINVISION_BY_CHROMA_SYMBOLIC_ROLE_SYNTHESIS_ONLY; no `§0` pointer added; no tags.*

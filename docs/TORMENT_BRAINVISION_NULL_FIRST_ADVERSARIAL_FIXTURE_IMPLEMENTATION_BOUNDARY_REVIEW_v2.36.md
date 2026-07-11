# TORMENT Brainvision Null-First Adversarial Fixture Implementation-Boundary Review v2.36

## 1. Status / Scope

**DOCS-ONLY implementation-boundary REVIEW.** This is a review note only. It opens **no** code, **no** tests, **no**
artifact, **no** fixtures, **no** data, **no** runtime, and **no** integration lane. **It implements nothing and it does
not self-authorize implementation.** It sits over the accepted v2.35 edge (`537ee8b docs(research): propose null-first
adversarial fixture families`) and changes none of the accepted files.

**v2.36 reviews whether a future v2.37 may safely implement a tiny deterministic static symbolic family-role artifact**
for the six v2.35 null-first adversarial roles. It may only **recommend**. Any v2.37 requires Codex acceptance of this
review **and** explicit operator approval, separately given.

**Explicitly authorized: nothing.**

```text
NO IMPLEMENTATION, NO ARTIFACT, NO FIXTURES, NO INSTANCES, NO DATA.
NO GENERATION RULES, SCHEMAS, DATA SHAPES, DECISION RULES, OR ARRIVAL RULES.
NO DESCRIPTORS, COORDINATES, METRICS, SCORES, THRESHOLDS, FORMULAS, PASS/FAIL GATES, OR VALIDATION.
NO CLASSIFIER (FORM B) OR NEURAL (FORM C) WORK. NO SCREEN / REAL-CLIP / RUNTIME / MEMORY PATH.
NO VISION CLAIM AND NO READINESS CLAIM.
ANY NEXT PATH REQUIRES SEPARATE OPERATOR APPROVAL AND SEPARATE CODEX REVIEW.
NO §0 POINTER; NO TAGS.
```

```text
flat_field_validated                        = False      null_rejected                 = False
role_validated                              = False      artifact_ruled_out            = False
schema_validated                            = False      proxy_ruled_out               = False
entanglement_resolved                       = False      confound_controlled           = False
by_residual_isolated                        = False      control_collapse_ruled_out    = False
generic_chroma_proxy_ruled_out              = False      control_collapse_detected     = False
                                                         candidate_structure_validated = False
first_pass_structure_validity_claim_allowed = False      candidate_structure_survived  = False
temporal_claim_allowed                      = False      candidate_structure_detected  = False
descriptor_validity_claim_allowed           = False
geometry_validity_claim_allowed             = False
screen_readiness_claim_allowed              = False
runtime_readiness_claim_allowed             = False
memory_readiness_claim_allowed              = False
integration_readiness_claim_allowed         = False
vision_claim_allowed                        = False
verdict                                      = HOLD
```

## 2. Grounding

```text
v2.33  TARGET SCAN (bcd3404): criterion "what could this target FAIL at?"; null-first recommended; NULL SINK named.
v2.34  NULL-FIRST PLAN (424b5a8): null / artifact / proxy / confound / unresolved outcomes are the ADVERSARIAL FLOOR.
       Adversary fixed BEFORE any candidate and never weakened (S2). "The nulls behaved" is the floor, not evidence.
       S1-S5 stand; S3 (pre-stated, reachable survival path) is binding.
v2.35  FAMILY-ROLE PROPOSAL (537ee8b): six symbolic roles (A null / no-structure; B fixture-artifact; C proxy-confound;
       D entangled / unresolved; E control-collapse; F candidate-structure-survival).

CODEX FINDING ON v2.35, treated here as BINDING:
  - the six roles are SYMBOLIC and NON-PARTITIONING;
  - D remains UNRESOLVED;
  - E / control-collapse remains REACHABLE;
  - F / candidate-structure-survival remains ONLY A FUTURE QUESTION;
  - CONCRETE REACHABILITY (S3 in a real design) remains a BINDING FUTURE OBLIGATION -- undischarged, and NOT
    discharged by anything reviewed here.
```

## 3. Primary Review Question

```text
"Can v2.37 implement a static symbolic null-first adversarial family-role artifact without creating fixture instances,
 generation rules, validation categories, decision semantics, or positive-structure evidence?"
```

**Answer posture: CONDITIONALLY YES on SAFETY — with a separate and serious caution about WORTH (Section 8).** An
artifact that names six adversarial roles, takes no input, generates nothing, decides nothing, and validates nothing is
implementable safely; the v2.26 and v2.31 precedents show exactly how. But *safe* and *worth building* are different
questions, and this review declines to let the first answer smuggle in the second.

## 4. Allowed Future v2.37 Shape (if approved)

```text
A TINY, DETERMINISTIC, STATIC SYMBOLIC FAMILY-ROLE ARTIFACT, on the accepted v2.26 / v2.31 pattern (a deterministic
builder with NO PARAMETERS + a conservative canonical checker), offline, outside torment_service/, stdlib-only, under
research/brainvision/ + tests/research/.

It may generate EXACTLY the six symbolic family roles -- no more, no fewer:

    A_null_no_structure_role
    B_fixture_artifact_role
    C_proxy_confound_role
    D_entangled_unresolved_role
    E_control_collapse_role
    F_candidate_structure_survival_role

Each role may carry ONLY these static conceptual / reporting fields:

    role_id
    role_label
    conceptual_purpose
    adversarial_focus
    safe_reporting_language
    forbidden_interpretations
    non_claim_constraints
    role_generated  = True
    role_validated  = False

Every field is a NAME or canonical reporting prose. None is a value, a datum, a rule, a criterion, or a container for
one. The artifact takes NO INPUT: with nothing to feed it, there is nothing it could generate, evaluate, assign,
decide, or validate.
```

## 5. Implementation-Boundary Warnings (mandatory; each independently disqualifying)

```text
W1. E_control_collapse_role MUST REMAIN REACHABLE IN LANGUAGE ONLY.
    v2.37 may report the role as GENERATED. It must NOT claim -- in any field, string, flag, test name, or doc line --
    that control-collapse has been TESTED, DETECTED, RULED OUT, AVOIDED, or HANDLED.
    control_collapse_ruled_out = False AND control_collapse_detected = False, both.
    THE TRAP: "the artifact carries a control-collapse role" reads, on a tired day, as "the design has a
    control-collapse check". It has no such thing. It has a NOUN. Naming the way your controls could fail is not
    checking whether they did, and an artifact that blurs the two has manufactured a safety property out of vocabulary.

W2. F_candidate_structure_survival_role MUST REMAIN ONLY A FUTURE QUESTION.
    v2.37 must NOT imply that candidate structure survived, was detected, was validated, or is EXPECTED.
    candidate_structure_survived = False; candidate_structure_detected = False; candidate_structure_validated = False.
    THE TRAP: F is a slot. Slots invite filling. A green artifact containing an empty F reads as a project that has
    built the frame and now merely awaits the picture -- which is an expectation, and an expectation is a claim about
    the world made in advance of any evidence. F names a BURDEN, not an entitlement, and its emptiness is a legitimate
    PERMANENT state, not a to-do item.

W3. THE SIX ROLES MUST REMAIN SYMBOLIC AND NON-PARTITIONING.
    They are NOT fixture classes, measured classes, classifier labels, validation groups, pass/fail categories, or
    visual categories. They do not partition any space, they are not exhaustive, more than one may stand at once, and
    NOTHING is ever sorted into them. The artifact must SAY SO IN ITSELF (an explicit non-exhaustive / non-partitioning
    marker), not merely have it said about it in a doc.
    THE TRAP: six named roles in a data structure LOOK like a category system. The only thing preventing that reading
    is that nothing can be put into them -- which must hold structurally (no input, no assignment), not by convention.

W4. A CLEAN PROTOCOL CHECK VERIFIES CANONICAL SYMBOLIC STRUCTURE AND FORBIDDEN-SURFACE ABSENCE. NOTHING ELSE.
    It must NOT verify -- and its greenness must never be read as -- scientific validity, fixture quality, control
    quality, detection, survival, or falsification success.
    THE TRAP, AND IT IS THE WORST ONE IN THIS SLICE: on a NULL-FIRST artifact, a green check reads as "the adversary is
    in place". It is not. A green check means the artifact SAID ONLY WHAT IT WAS PERMITTED TO SAY. There is no
    adversary yet -- there are six nouns. Nothing has been tested, nothing has been controlled, and "the nulls behaved"
    cannot even be asserted, because no null has behaved in any way at all.
```

## 6. Forbidden Future v2.37 Shape (exhaustive; any one disqualifies)

```text
    fixture instances          fixture data            generation rules        schemas / data shapes
    arrays / images            descriptors             coordinates             metrics
    scores                     thresholds              formulas                decision rules
    arrival rules              evidence fields         confidence fields       classification fields
    validation fields          pass/fail fields        survival fields         positive-structure fields
    screen / runtime / memory fields                   real-clip fields        vision fields

AND, structurally:
  - any input; any function taking an argument and returning a role or an outcome; any assignment, selection, routing,
    ranking, ordering, matching, or generation of anything;
  - any container that could hold a case, a stimulus, a datum, an array, or an image;
  - any numeric value (booleans excepted); any equation; any comparison;
  - role_validated = True; any claim lock True; a non-HOLD verdict; a validation-positive outcome label;
  - any lock / flag / guard group that is OPEN (an extra key, even one set False, must breach -- v2.26 Codex MODIFY);
  - any torment_service/ touch; any runtime, memory, screen, real-clip, camera, live, sensor, or streaming path.

If a proposed v2.37 needs ANY item above to express the roles, it is out of bounds and this review does not
contemplate it.
```

## 7. A Structural Point The Review Had To Settle: Should F Exist In The First Artifact?

v2.30 dropped `related_role_ids` from the first v2.31 artifact on the principle that *a field that can only be made safe
by rules about how to read it is not safe — it is deferred*. F invites the same treatment. The review considered it and
**rejects the analogy**, for a reason that matters:

```text
DROPPING F WOULD CREATE THE WORSE HAZARD.

  With F present : A-E are visibly NOT the whole story. There is an explicit, first-class place where survival could
                   be asked about -- empty, unexpected, and unfilled, but PRESENT. The role set is visibly
                   non-exhaustive.
  With F absent  : A-E become, by construction, everything the artifact can say. Survival is then reachable only by
                   ELIMINATION from A-E -- which is exactly the ELSE-BRANCH structure v2.35 P2 forbids, and exactly
                   the NULL SINK v2.33 / v2.34 named. Removing the dangerous slot would make the design guaranteed to
                   report "nothing survived", whatever is true.

So F STAYS -- and is guarded by W2 instead. This is the inverse of the v2.30 call, and deliberately so: there, the
dangerous field added a relation that did not need to exist; here, the dangerous slot is what keeps the adversary from
becoming unfalsifiable. The hazard is not that F exists. The hazard is that F gets READ AS AN EXPECTATION.
```

## 8. Safe Is Not The Same As Worth Building

```text
This review recommends v2.37 as SAFE. It does not tell the operator it is VALUABLE, and it will not pretend the two
questions are one.

Apply the v2.32 test: WHAT COULD v2.37 FAIL AT?
  Honestly: nothing. It would be boundary-clean, or it would be fixed until it was. It would be the THIRD artifact of
  the same shape (v2.26 roles; v2.31 schema; v2.37 roles), and it would advance S3 -- the binding reachability
  obligation, the only thing standing between this programme and a real null-first study -- BY EXACTLY NOTHING.

WHAT v2.37 WOULD BUY: the six roles held canonically in code, under a guard, so that a later design cannot quietly
  redefine them. That is real, and it is small.
WHAT IT WOULD NOT BUY: any step toward knowing whether survival is reachable, whether structure exists, or whether the
  adversary can be built at all.

THE HONEST ALTERNATIVE, WHICH THE OPERATOR SHOULD WEIGH AGAINST v2.37: skip the artifact and spend the next slice on
  S3 ITSELF -- can a null-first design be described in which survival is genuinely reachable, and if not, say so. That
  slice CAN fail. v2.37 cannot. By the criterion this programme adopted in v2.32 and v2.33, the slice that can fail is
  the better one.

This review states that plainly and then defers: the operator may want the roles frozen in code before any design
touches them, and that is a legitimate reason to build v2.37. It is just not a scientific one.
```

## 9. Recommendation

```text
RECOMMEND (conditional): a future v2.37 STATIC SYMBOLIC NULL-FIRST ADVERSARIAL FAMILY-ROLE ARTIFACT may be pursued --
IF AND ONLY IF it is strictly the Section-4 allowed shape, contains NONE of the Section-6 forbidden shape, and holds
every Section-5 warning (W1-W4) STRUCTURALLY rather than by promise.

  v2.37 IS CONDITIONAL ON: CODEX ACCEPTANCE of this v2.36 review, AND EXPLICIT OPERATOR APPROVAL. Both, separately.
  This review is a GATE, not a green light. It authorizes nothing by itself, is NOT self-authorizing, and starts no
  v2.37.

  It is also conditional on the operator having read Section 8 and chosen the artifact ANYWAY, with open eyes. v2.37 is
  a freezing of vocabulary, not a step toward a result.

IF THE BOUNDARY IS NOT SAFE -- if any of W1-W4 cannot be held structurally, if the role set cannot be kept
non-partitioning inside a data structure, if F cannot be prevented from reading as an expectation, or if a green check
cannot be prevented from reading as "the adversary is in place" -- then the correct move is NOT to implement with extra
guards. It is to HOLD AT DOCS-ONLY AND REVISE v2.35 INSTEAD. A role set that needs guards to stay honest is the wrong
role set; revise the proposal, do not fortify the artifact.

NOT RECOMMENDED: fixtures, instances, data, generation rules, schemas, decision rules; descriptor / coordinate /
metric / score / threshold / formula / pass-fail / validation work; screen / real-clip / runtime / memory work;
classifier or neural work; any vision work. The v2.33 fallback (cross-family synthetic falsification) and the v2.33
honest stop (pause the Brainvision synthetic branch) both remain available at any time.
```

## 10. Forbidden Drift Register

```text
- a family-role ARTIFACT becoming a FIXTURE CLASS SYSTEM, a category scheme, or a label set.
- E being read as a CONTROL-COLLAPSE CHECK. It is a noun. control_collapse_detected stays False (W1).
- F being read as an EXPECTATION, a goal, a to-do, or a slot the project intends to fill (W2).
- F being DROPPED, which would make A-E exhaustive and survival reachable only by elimination -- the null sink
  (Section 7).
- the six roles becoming a PARTITION, an exhaustive taxonomy, or a claim of coverage (W3).
- a green protocol check becoming "the adversary is in place", scientific validity, control quality, detection,
  survival, or falsification success (W4).
- "the nulls behaved" being asserted at all -- no null has behaved, because no null exists.
- a REVIEW becoming an AUTHORIZATION; "safe to build" becoming "worth building"; scaffolding momentum becoming an
  implicit licence.
- S3 being treated as advanced, weakened, or discharged by v2.37. It would be untouched (Section 8).
```

## 11. Non-Claim Interpretation

```text
WHAT v2.36 MAY ESTABLISH (and only this):
  - a CONDITIONAL boundary under which a future v2.37 static symbolic family-role artifact could be pursued;
  - the ALLOWED shape, the FORBIDDEN shape, and the four mandatory warnings (W1-W4);
  - a settled structural point: F STAYS, guarded (Section 7);
  - an honest separation of SAFE from WORTH BUILDING (Section 8);
  - the fallback if the boundary cannot be held: revise v2.35, do not fortify an artifact.

WHAT IT DOES NOT ESTABLISH:
  not an implementation    not an artifact       not fixtures / data    not a descriptor / coordinate / metric
  not a decision rule      not validation        not closure            not readiness            not vision
  not that control-collapse has been tested, detected, ruled out, avoided, or handled
  not that candidate structure survived, was detected, was validated, or is expected
  not that survival is reachable (S3 remains a BINDING, UNDISCHARGED obligation)
  not authorization of anything by itself

Even a fully-approved, fully-guarded v2.37 would write down SIX ADVERSARIAL NOUNS. It would test nothing, control
nothing, detect nothing, and survive nothing.
```

## 12. Verdict

```text
verdict                                      = HOLD
flat_field_validated                         = False
role_validated                               = False
schema_validated                             = False
entanglement_resolved                        = False
by_residual_isolated                         = False
generic_chroma_proxy_ruled_out               = False
null_rejected                                = False
artifact_ruled_out                           = False
proxy_ruled_out                              = False
confound_controlled                          = False
control_collapse_ruled_out                   = False
control_collapse_detected                    = False
candidate_structure_validated                = False
candidate_structure_survived                 = False
candidate_structure_detected                 = False
first_pass_structure_validity_claim_allowed  = False
temporal_claim_allowed                       = False
descriptor_validity_claim_allowed            = False
geometry_validity_claim_allowed              = False
screen_readiness_claim_allowed               = False
runtime_readiness_claim_allowed              = False
memory_readiness_claim_allowed               = False
integration_readiness_claim_allowed          = False
vision_claim_allowed                         = False

OUTCOME_LABEL: BRAINVISION_NULL_FIRST_ADVERSARIAL_FIXTURE_IMPLEMENTATION_BOUNDARY_REVIEW_ONLY
```

v2.36 is a docs-only implementation-boundary review. It implements nothing and does not self-authorize. It grounds
itself in v2.33 (target scan), v2.34 (null-first plan; S1–S5), v2.35 (six symbolic family roles), and the binding Codex
finding on v2.35 (roles symbolic and non-partitioning; D unresolved; E reachable; F only a future question; concrete
reachability an undischarged obligation). It answers the primary review question **conditionally yes on safety**, fixes
the allowed and forbidden v2.37 shapes, states four mandatory warnings (W1 control-collapse reachable **in language
only** and never tested / detected / ruled out / avoided / handled; W2 candidate-structure-survival only a future
question and never expected; W3 roles symbolic and non-partitioning, never fixture / measured / classifier /
validation / pass-fail / visual categories; W4 a clean protocol check verifies canonical symbolic structure and
forbidden-surface absence and NOTHING else), settles that role F must **stay** because dropping it would make A–E
exhaustive and recreate the null sink, and separates **safe** from **worth building** — noting that v2.37 could fail at
nothing and would advance the binding S3 reachability obligation by exactly nothing. It conditions any v2.37 on Codex
acceptance **and** explicit operator approval, and recommends holding at docs-only and revising v2.35 if the boundary
cannot be held. All claim locks and the frozen verdict **HOLD** are preserved and unmoved.

## 13. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_NULL_FIRST_ADVERSARIAL_FIXTURE_IMPLEMENTATION_BOUNDARY_REVIEW_v2.36.md
(new, docs-only, untracked; over the accepted v2.35 edge
 "537ee8b docs(research): propose null-first adversarial fixture families").

Verify that this review:
- is docs-only, implements NOTHING, and does NOT self-authorize implementation: no code, no tests, no artifact, no
  fixtures, no fixture data, no generation rules, no schemas / data shapes, no arrays / images, no descriptors, no
  coordinates, no metrics, no scores, no thresholds, no formulas, no decision rules, no pass/fail gates, no
  validation, no screen / runtime / memory paths, no classifier / neural work, no real clips, no vision claims; adds
  no §0 pointer and no tags; states that any next path requires separate operator approval and separate review;
- grounds itself in v2.33, v2.34, v2.35, and the binding Codex v2.35 finding (six roles symbolic and non-partitioning;
  D unresolved; E reachable; F only a future question; concrete reachability a binding future obligation);
- poses the primary review question verbatim ("Can v2.37 implement a static symbolic null-first adversarial
  family-role artifact without creating fixture instances, generation rules, validation categories, decision
  semantics, or positive-structure evidence?");
- specifies the ALLOWED v2.37 shape: a deterministic static symbolic builder (NO PARAMETERS) generating EXACTLY the
  six roles (A_null_no_structure_role, B_fixture_artifact_role, C_proxy_confound_role, D_entangled_unresolved_role,
  E_control_collapse_role, F_candidate_structure_survival_role), each with ONLY role_id, role_label,
  conceptual_purpose, adversarial_focus, safe_reporting_language, forbidden_interpretations, non_claim_constraints,
  role_generated = True, role_validated = False;
- states the four mandatory warnings: W1 E_control_collapse_role reachable IN LANGUAGE ONLY -- may be reported as
  generated, but control-collapse must never be claimed as tested, detected, ruled out, avoided, or handled
  (control_collapse_ruled_out = False AND control_collapse_detected = False); W2 F_candidate_structure_survival_role
  remains ONLY a future question -- no implication of survival, detection, validation, or EXPECTATION; W3 the six
  roles remain symbolic and NON-PARTITIONING -- not fixture classes, measured classes, classifier labels, validation
  groups, pass/fail categories, or visual categories; W4 a clean protocol check may verify ONLY canonical symbolic
  structure and forbidden-surface absence, and must never verify or imply scientific validity, fixture quality,
  control quality, detection, survival, or falsification success;
- specifies the FORBIDDEN v2.37 shape (fixture instances; fixture data; generation rules; schemas / data shapes;
  arrays / images; descriptors; coordinates; metrics; scores; thresholds; formulas; decision rules; arrival rules;
  evidence, confidence, classification, validation, pass/fail, survival, positive-structure, screen / runtime /
  memory, real-clip, and vision fields; plus any input, assignment, numeric value, open lock group, or
  torment_service/ touch);
- settles the F question: role F STAYS (dropping it would make A-E exhaustive and make survival reachable only by
  elimination -- the null sink), and is guarded by W2 instead;
- separates SAFE from WORTH BUILDING: v2.37 could fail at nothing and would advance the binding S3 reachability
  obligation by nothing; the operator is told this plainly before being asked to approve;
- conditions v2.37 on CODEX ACCEPTANCE of this review AND EXPLICIT OPERATOR APPROVAL, and recommends HOLDING AT
  DOCS-ONLY AND REVISING v2.35 if the boundary cannot be held structurally;
- preserves the locks and verdict (Section 12): flat_field_validated, role_validated, schema_validated,
  entanglement_resolved, by_residual_isolated, generic_chroma_proxy_ruled_out, null_rejected, artifact_ruled_out,
  proxy_ruled_out, confound_controlled, control_collapse_ruled_out, control_collapse_detected,
  candidate_structure_validated, candidate_structure_survived, candidate_structure_detected,
  first_pass_structure_validity_claim_allowed, temporal_claim_allowed, descriptor_validity_claim_allowed,
  geometry_validity_claim_allowed, screen_readiness_claim_allowed, runtime_readiness_claim_allowed,
  memory_readiness_claim_allowed, integration_readiness_claim_allowed, vision_claim_allowed -- all False;
  verdict = HOLD; HOLD/HELD read as held for analysis, not abandoned.

Flag any implementation / artifact / fixture / instance / data / generation rule / schema / decision rule; any
UNCONDITIONAL authorization of v2.37; any allowed-shape element carrying an input, a datum, a number, a rule, or a
criterion; any suggestion that control-collapse has been tested, detected, ruled out, avoided, or handled; any
suggestion that candidate structure survived, was detected, was validated, or is expected; any role set treated as
partitioning, exhaustive, or as fixture / measured / classifier / validation / pass-fail / visual categories; any
protocol greenness read as scientific validity, control quality, detection, survival, or falsification success; any
treatment of "safe to build" as "worth building"; any claim that S3 has been advanced or discharged; or any claim-lock
/ verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
All claim locks False — including `control_collapse_ruled_out`, `control_collapse_detected`,
`candidate_structure_validated`, `candidate_structure_survived`, and `candidate_structure_detected` — and the frozen
verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Null-First Adversarial Fixture Implementation-Boundary Review v2.36. Docs-only boundary
review over the accepted v2.35 edge. Implements nothing; authorizes nothing; is not self-authorizing. Opens no
implementation lane, no tests, no artifact, no fixtures, no instances, and no data; defines no generation rule, schema,
data shape, descriptor, coordinate, metric, score, threshold, formula, decision rule, arrival rule, pass-fail gate, or
validation criterion; opens no classifier / neural / screen / real-clip / runtime / memory path; makes no vision or
readiness claim. Reviews whether a future v2.37 may implement a tiny deterministic static symbolic family-role artifact
for the six v2.35 null-first adversarial roles; answers CONDITIONALLY YES on safety; fixes the allowed shape (a
no-parameter deterministic builder over exactly six roles, each carrying only role_id, role_label, conceptual_purpose,
adversarial_focus, safe_reporting_language, forbidden_interpretations, non_claim_constraints, role_generated = True,
role_validated = False) and the forbidden shape (fixture instances, fixture data, generation rules, schemas / data
shapes, arrays / images, descriptors, coordinates, metrics, scores, thresholds, formulas, decision rules, arrival
rules, evidence / confidence / classification / validation / pass-fail / survival / positive-structure / screen /
runtime / memory / real-clip / vision fields); states four mandatory warnings (W1 control-collapse reachable in
LANGUAGE ONLY, never tested / detected / ruled out / avoided / handled; W2 candidate-structure-survival only a future
question, never an expectation; W3 roles symbolic and non-partitioning; W4 a clean protocol check verifies canonical
symbolic structure and forbidden-surface absence and nothing else); settles that role F must STAY because dropping it
would make A–E exhaustive and recreate the NULL SINK; separates SAFE from WORTH BUILDING and states that v2.37 could
fail at nothing and would advance the binding S3 reachability obligation by nothing; conditions any v2.37 on Codex
acceptance of this review and explicit operator approval; recommends holding at docs-only and revising v2.35 if the
boundary cannot be held structurally; keeps prior BY / color / chroma work FROZEN EVIDENCE, the BY/chroma scaffold
REPORTING LANGUAGE ONLY, the flat opponent-field symbolic branch PAUSED HELD, and the v2.22 question UNRESOLVED and
possibly unanswerable; preserves all claim locks and the frozen verdict HOLD; outcome label
BRAINVISION_NULL_FIRST_ADVERSARIAL_FIXTURE_IMPLEMENTATION_BOUNDARY_REVIEW_ONLY; no `§0` pointer added; no tags.*

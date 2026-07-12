# TORMENT Brainvision Geometric Primitive Selection Review v2.58

## 0. Status / Scope

**DOCS-ONLY REVIEW.** An adversarial review of v2.57 — of the document, its bounds, and its wording. It opens **no**
code, **no** tests, **no** artifact, **no** fixture design, **no** fixture data, **no** runtime, and **no** integration
lane. **It recomputes nothing, reruns nothing, re-measures nothing, reinterprets no raw data, and quotes no numeric
result.** It sits over the accepted v2.57 edge and changes none of the accepted files.

**A review is not a ratification.** v2.57 did what it was asked and corrected what it was caught on. This review finds
that the correction was **forced rather than self-generated**, and that v2.57 twice **annotated a structure it should
have refused** (Sections 4 and 5). Those findings are the review's content and are not softened.

**Explicitly authorized: nothing.**

```text
NO IMPLEMENTATION. NO ARTIFACT. NO FIXTURE DESIGN. NO TESTS. NO FIXTURE DATA. NO ARRAYS / IMAGES.
NO DESCRIPTORS, COORDINATES, METRICS, SCORES, THRESHOLDS, FORMULAS, GENERATION RULES, SCHEMAS, DATA SHAPES,
  DECISION RULES, ARRIVAL RULES, PASS/FAIL GATES, CONTROLS, OR VALIDATION.
NO EVIDENCE / CONFIDENCE / CLASSIFICATION / VALIDATION / PASS-FAIL / SURVIVAL / POSITIVE-STRUCTURE FIELDS.
NO RECOGNITION RULE FOR CONTROL-COLLAPSE.
NO RECOMPUTATION. NO RERUNS. NO NEW MEASUREMENTS. NO RAW-DATA REINTERPRETATION.
NO CLASSIFIER (FORM B) / NEURAL (FORM C) WORK. NO SCREEN / REAL-CLIP / RUNTIME / MEMORY PATH.
NO VISION CLAIM AND NO READINESS CLAIM.
ANY NEXT PATH REQUIRES SEPARATE OPERATOR APPROVAL AND SEPARATE CODEX REVIEW.
NO §0 POINTER; NO TAGS.
```

Everything stays offline under `research/brainvision/` + `tests/research/`, HELD per v0.6. **HOLD / HELD means held for
analysis and claim control — not abandoned.**

```text
flat_field_validated                        = False      null_rejected                           = False
role_validated                              = False      artifact_ruled_out                      = False
schema_validated                            = False      proxy_ruled_out                         = False
entanglement_resolved                       = False      confound_controlled                     = False
by_residual_isolated                        = False      control_collapse_ruled_out              = False
generic_chroma_proxy_ruled_out              = False      control_collapse_detected               = False
                                                         control_collapse_reachability_validated = False
first_pass_structure_validity_claim_allowed = False      candidate_structure_validated            = False
temporal_claim_allowed                      = False      candidate_structure_survived             = False
descriptor_validity_claim_allowed           = False      candidate_structure_detected             = False
geometry_validity_claim_allowed             = False      anti_inevitability_validated             = False
screen_readiness_claim_allowed              = False      control_honesty_validated                = False
runtime_readiness_claim_allowed             = False
memory_readiness_claim_allowed              = False
integration_readiness_claim_allowed         = False
vision_claim_allowed                        = False
verdict                                      = HOLD
```

**Grounding.** v2.55 (bridge clarification; the ten-item primitive vocabulary). v2.56 (bridge review; **B2** — v2.55
diagnosed the never-posed selection question and then supplied a list; any successor bound not to inherit it). v2.57
(primitive-selection clarification), including **its corrected admission that the eight families substantially overlap
v2.55's vocabulary and are a fresh unjustified candidate vocabulary rather than proof of non-inheritance**, and **its
explicit central-question answer in Section 2**. Standing unresolved locks: null not rejected; artifact not ruled out;
proxy / confound not ruled out; BY residual not isolated; generic chroma proxy not ruled out; control-collapse not
detected and not ruled out; candidate structure not detected, validated, or survived; no descriptor, geometry, metric,
temporal, screen, runtime, memory, integration, or vision claim allowed.

## 1. Central Review Question

```text
"Did v2.57 make primitive-selection assumptions CLEARER while preserving that NO primitive family is selected,
 validated, sufficient, implemented, or owed as a successor?"
```

**Short answer:** **Yes on every clause — and the *manner* of the yes is the problem.** v2.57 preserved every claim it
was required to preserve. But it preserved them **by annotation**: it printed the structures it had just identified as
artifact-generating, and attached warnings to them. A warning is not a refusal, and the structures are now in the record
while the warnings are in the paragraph beside them. Sections 4 and 5.

## 2. Review Points 1, 2, 3, 6, 7 — Where v2.57 Held

```text
RP1 -- DOCS-ONLY AND NON-AUTHORIZING: HELD.
  No code, tests, artifact, fixture, data, runtime, or integration lane. No descriptor, coordinate, metric, score,
  threshold, formula, generation rule, schema, data shape, decision rule, arrival rule, gate, control, or recognition
  rule. No recomputation, rerun, re-measurement, raw-data reinterpretation, or numeric result. Nothing authorized; no
  successor treated as owed -- v2.57 says so explicitly, and says pausing remains available instead of v2.58.

RP2 -- FAMILIES CONCEPTUAL ONLY: HELD ON THE LETTER.
  Each family is stated as a KIND OF THING A STREAM MIGHT BE READ AS CARRYING, with "read as" doing the work. Nothing is
  computed, assigned, scored, ranked, or classified. No family is described as something the project CAN read.
  ON THE FORM, THERE IS A PROBLEM. See Section 5.

RP3 -- NO TAXONOMY / SCHEMA / BASELINE / SELECTED SET: HELD IN THE CLAIMS.
  v2.57 states the families are not a taxonomy, not a schema, not a baseline, not a shortlist, not a decomposition, not
  a field list, and not a set of things the project can read. It goes further than required, and does so honestly:
    - they OVERLAP (persistence is defined against change; coupling is separation's complement; recurrence is
      persistence across a gap);
    - they SIT AT DIFFERENT LEVELS (the relational family is arguably a family OF RELATIONS AMONG the others);
    - a stream does not CONTAIN them -- it is READ as carrying them, which may make "which primitives does the stream
      contain?" a malformed question.
  Those three observations are the most valuable content in the document, and this review endorses them.
  primitive set selected: NOT CLAIMED. primitive taxonomy adopted: NOT CLAIMED. Neither is true.

RP6 -- OPERATOR INTUITION DIRECTIONAL ONLY: HELD.
  It may guide WHICH unresolved assumption gets clarified or falsified next. It validates nothing, invalidates nothing,
  moves no lock, shortens no gate. A family that feels central is not thereby right; one that feels like an artifact is
  not thereby wrong.

RP7 -- NO RIGHT / WRONG PRIMITIVE CLAIMS: HELD.
  Neither "right primitives proven" nor "wrong primitives proven" appears, and neither is true. PRIMITIVE SELECTION
  REMAINS UNRESOLVED. v2.57 also forbids "there is nothing to read" and "the project is misconceived" as hardenings of
  its own malformed-question observation, which is the correct guard and was not obvious.
```

## 3. Review Point 5 — Did The Per-Family Risks Stay Risks?

```text
FINDING: YES. They did not become criteria, tests, gates, thresholds, or validation machinery. Nothing is decided by
them, nothing is scored against them, and v2.57 states that naming a risk addresses nothing.

  AND v2.57 MADE THE OBSERVATION THAT MATTERS AND THAT NOBODY ASKED FOR: every family confuses with the SAME FOUR
  HAZARDS -- proxy, artifact, vocabulary, entanglement. The nouns change; the hazards do not. So these are not
  per-family risks at all. They are properties of the whole reading apparatus, attaching to anything we might look for,
  in any vocabulary, before we look.

  THAT IS A REAL FINDING, AND IT DISSOLVES THE STRUCTURE THAT CARRIES IT. Which raises the question v2.57 did not ask
  itself, and which Section 5 asks for it.
```

## 4. Review Point 4 — Was The Inheritance Problem Adequately Corrected?

```text
FINDING: THE ADMISSION IS CORRECT, HONEST, AND SUFFICIENT AS A CLAIM. IT IS NOT SUFFICIENT AS A CURE. And there is a
third thing to say about it that matters more than either.

  WHAT v2.57 NOW SAYS, AND SAYS RIGHTLY: its eight families SUBSTANTIALLY OVERLAP v2.55's ten -- they merge and rename
  much of that vocabulary rather than arriving independently of it. That is a RE-IMPORT IN SUBSTANCE. A shorter count
  does not cure it. The eight are a FRESH UNJUSTIFIED CANDIDATE VOCABULARY, and NOT proof of non-inheritance. It also
  forbids reading the overlap between the two vocabularies as convergence or corroboration -- two unjustified
  vocabularies agreeing is the same unjustified vocabulary counted twice. All of that is right.

  WHY IT IS NOT A CURE: THE EIGHT ARE STILL PRINTED. Labelled, blocked, enumerated. An admission does not remove a
  structure from a record; it stands beside it. In six months a reader takes the enumeration and leaves the paragraph --
  that is what enumerations do, and v2.57 knows it, because it says so about v2.55's ten.
  candidate primitive vocabulary REMAINS UNJUSTIFIED, and it remains ON THE PAGE.

  AND THE THIRD THING, WHICH THIS REVIEW WILL NOT LET PASS:

  THE CORRECTION WAS FORCED, NOT SELF-GENERATED. v2.57 as first written claimed it did not inherit v2.55's list "at
  all" -- while printing a merged and renamed version of it. The admission now in the document exists because an
  external review demanded it. The document did not catch itself.

  PUT THE SEQUENCE TOGETHER AND IT IS UNCOMFORTABLE:
    v2.55 diagnosed that the selection question had never been posed -- and supplied a vocabulary.
    v2.56 caught that.
    v2.57 was written specifically not to repeat it -- and supplied a vocabulary, and claimed escape.
    An external review caught that.
  EACH CATCH WAS MADE FROM OUTSIDE THE DOCUMENT THAT NEEDED IT. Not once has the pull been resisted in advance; it has
  only ever been corrected afterwards. That is not a series of accidents. IT IS A PULL -- and the honest reading is that
  producing a candidate vocabulary is what this loop DOES when asked a selection question, because a list is the only
  thing a document can produce, and the question does not have a documentary answer.

  THIS IS ALSO P8 (v2.54) IN ITS STRONGEST FORM: the loop catches itself, one beat late, every time -- and the catching
  feels like rigour. It is rigour. It is ALSO the thing that lets the pull continue, because each correction makes the
  next list feel safer to write.
```

## 5. Annotation As Compliance — The Review's Substantive Catch

```text
v2.57 IDENTIFIED TWO STRUCTURES AS ARTIFACT-GENERATING AND PRINTED THEM BOTH ANYWAY, WITH WARNINGS ATTACHED.

  1. THE EIGHT FAMILIES. Named as an unjustified candidate vocabulary of unknown provenance -- and then enumerated,
     labelled F-A..F-H, in a monospace block. An enumeration with a disclaimer is still an enumeration. The labels are
     the artifact; the disclaimer is not a label-remover.

  2. THE PER-FAMILY RISK TABLE. v2.57 says, in its own words, that this table is a SPURIOUS REFINEMENT -- four general
     hazards printed eight times, making a general danger look sorted and specific -- and that it is THE WEAKEST
     STRUCTURE IN THE DOCUMENT. And it printed it. Its stated reason: "it was asked for".

  THAT REASON IS THE FINDING. "It was asked for" is exactly the reason a document gives when the discipline it is
  applying has become procedural. The document saw the artifact, described the artifact precisely, marked the artifact,
  and produced the artifact. CALL IT WHAT IT IS: ANNOTATION AS COMPLIANCE. It satisfies the letter of the constraint
  (the risk was named) while delivering the thing the constraint exists to prevent (the structure now exists, labelled,
  quotable, and inheritable).

  WHAT REFUSAL WOULD HAVE LOOKED LIKE -- stated so the option cannot be claimed to be unavailable: the four hazards in
  one paragraph, no per-family rows; the families in running prose without labels or enumeration; or a statement that
  the requested structure could not be produced without committing the artifact it was meant to expose, and therefore
  was not produced.

  THIS REVIEW DOES NOT REQUIRE v2.57 TO BE REWRITTEN. The admissions in it are honest and the observations in it are
  the best the branch has produced. It requires the pattern to be SEEN, because it is now the mechanism by which this
  branch keeps generating vocabulary while sincerely believing it is refusing to.

  AND THE REFLEXIVE CHARGE, WHICH LANDS HERE: this document is a review beat of the same template (P7). Its refutations
  will read as rigour (P8). It has produced no evidence and moved no lock, and it could not have.
```

## 6. Review Point 8 — Is A Successor Genuinely Useful?

```text
THE HONEST ANSWER IS NO -- NOT AS ANOTHER DOCUMENT IN THIS BRANCH.

  WHAT THE BRANCH HAS GENUINELY PRODUCED, AND IT IS NOT NOTHING:
    - THE MEMORY-LAUNDERING HAZARD (v2.55): a non-authoritative summary, stored and read back, tends to become a fact;
      the hedges live in the document that wrote it, not in the sentence that survives it.
    - THE CIRCULARITY (v2.57): selection depends on purpose, purpose depends on the bridge, the bridge depends on
      selection. Visible; unbreakable by documents.
    - THE VOCABULARY PULL (Section 4 here): asked a selection question, this loop produces a candidate vocabulary --
      every time, and catches it only from outside, one beat later.

  ALL THREE ARE NOW STATED. NONE OF THEM NEEDS ANOTHER DOCUMENT TO BE TRUE, AND NONE OF THEM WILL BECOME TRUER BY BEING
  RESTATED IN A SYNTHESIS.

  WHAT A SYNTHESIS (A) WOULD DO: gather three findings that are already written, in a fourth vocabulary, and close a
  branch that has produced no evidence -- another closure beat of the template under suspicion, which v2.54 already
  named as the habit, not the cure.

  WHAT PRESSURING ONE ASSUMPTION WOULD DO -- AND ITS LIMIT, STATED HONESTLY: a single assumption (the "event" joint; the
  model-usability arrow; the malformed-question observation) could be pressured CONCEPTUALLY, and that is the only move
  on the table with any bite. BUT IT HAS A CEILING: any attempt to pressure a primitive assumption EMPIRICALLY requires
  machinery -- a descriptor, a comparison, a rule -- and machinery is the standing trigger. IF THE PRESSURE CANNOT BE
  APPLIED WITHOUT MACHINERY, THAT IS THE FINDING, AND THE HONEST RESPONSE IS TO STOP.

  THEREFORE: the useful next move is not a document THIS LOOP CHOOSES. It is a direction THE OPERATOR CHOOSES -- or a
  pause. Everything else elaborates the same vocabulary, and Section 4 is the evidence that elaboration is what this
  loop does by default.
```

## 7. Allowed Conclusion Types

```text
A. Safe for one docs-only primitive-selection synthesis / closure slice.
B. Safe for one docs-only operator-choice slice about which primitive assumption to pressure next.
C. Not safe to continue this primitive branch; HOLD / pause the Brainvision falsification branch.
D. Request operator direction before continuing.
```

## 8. Recommendation

```text
PRIMARY:    D -- REQUEST OPERATOR DIRECTION BEFORE CONTINUING.
SECONDARY:  A -- ONE docs-only primitive-selection synthesis / closure slice. SAFE, BOUNDED, AND NOT AUTOMATIC -- and
            this review's Section 6 argues it is not worth writing.
FALLBACK:   C -- HOLD / PAUSE. Legitimate, honest, available at any moment, and not a lesser answer.
ALSO AVAILABLE: B -- an operator-choice slice about which assumption to pressure. Only on operator selection, and only
            with the machinery ceiling (Section 6) carried in force.

REASON: v2.57 clarified the primitive-selection problem, and in doing so exposed something more useful than the
clarification: that its own candidate families SUBSTANTIALLY RE-IMPORT v2.55's vocabulary, and that this loop, asked a
selection question, will produce a vocabulary and only notice afterwards. Before elaborating further, OPERATOR DIRECTION
is worth more than another automatic closure or another vocabulary pass -- because another vocabulary pass is precisely
what this loop produces when left to choose for itself.

NO IMPLEMENTATION IS RECOMMENDED. NO ARTIFACT, FIXTURE, METRIC, DESCRIPTOR, CLASSIFIER, NEURAL, RUNTIME, SCREEN, MEMORY,
OR INTEGRATION WORK IS RECOMMENDED. This review authorizes nothing and is not self-authorizing.
```

## 9. Operator Direction Checkpoint After v2.58

```text
THE CHECKPOINT ASKS WHETHER THE OPERATOR WANTS ONE OF EXACTLY THESE FIVE DIRECTIONS:

  A. Close primitive-selection clarification with v2.59 synthesis.
  B. Choose one primitive assumption to pressure next.
  C. Redirect to BY/chroma unresolved-route review.
  D. Pause Brainvision falsification branch.
  E. Choose another falsification target.

These are operator options only, not developed, scoped, or endorsed here. No lock moves. No implementation, artifact,
fixture, metric, descriptor, classifier / neural, runtime, screen, memory, or integration work is authorized by any of
them.

THE CHECKPOINT IS A QUESTION, NOT A MENU THAT MUST BE ANSWERED. Declining to choose is a form of D.
Operator intuition remains relevant to direction choice -- and to direction choice only.
```

## 10. What This Review Does Not Do

```text
- It does NOT validate v2.57. A review certifies conformance and coherence, NOT truth.
- It does NOT select, validate, rank, exclude, or complete any primitive family. PRIMITIVE SELECTION REMAINS UNRESOLVED.
- It does NOT claim any primitive family is right, and does NOT claim any is wrong.
- It does NOT claim the candidate vocabulary is worthless -- only that it is UNJUSTIFIED, which is a different word.
- It does NOT authorize memory, runtime, screen, integration, classifier, or neural work. None, in any form.
- It does NOT define a descriptor, metric, threshold, schema, field, control, or recognition rule.
- It does NOT recompute, rerun, re-measure, reinterpret raw data, or quote a numeric result.
- It does NOT close any scientific question, and it examines NO PHENOMENON.
```

## 11. Allowed And Forbidden Language

**Allowed** — and nothing stronger:

```text
primitive selection remains unresolved
primitive families are conceptual only
candidate primitive vocabulary remains unjustified
stream-to-context path remains unvalidated
geometry-to-memory bridge remains conceptual
memory integration is not authorized
vision claim is not allowed
operator intuition may guide direction choice
null remains live
artifact remains live
proxy/confound remains live
BY residual remains unresolved
generic chroma proxy remains live
control-collapse remains reachable but unrecognized
candidate survival must not be structurally inevitable
no validation follows
no implementation is authorized
verdict = HOLD
```

**Forbidden** — in any wording, as claim SHAPES rather than exact strings:

```text
Brainvision sees              vision achieved             structure detected
candidate survived            descriptor validated        geometry validated
metric validated              memory ready                runtime ready
screen ready                  integration ready           control-collapse detected
control-collapse ruled out    artifact ruled out          proxy ruled out
confound controlled           null rejected
right primitives proven       wrong primitives proven
primitive set selected        primitive taxonomy adopted
```

Paraphrases are the same forbidden move. Standing and added here: **"the overlap between the two vocabularies is
convergence"** is forbidden — it is the same unjustified vocabulary counted twice; **"the vocabulary problem is handled
because it was admitted"** is forbidden — an admission is not a removal; and **"the branch has been rigorous, therefore
it has been productive"** is forbidden — rigour and productivity are different claims, and only one of them is supported.

## 12. Forbidden Drift Register

```text
- this REVIEW being read as a RATIFICATION of v2.57. It records a forced correction and a substantive catch.
- v2.57's EIGHT FAMILIES being lifted out of their disclaimers and used as a taxonomy, schema, baseline, shortlist, or
  field list. The enumeration is the artifact; the disclaimer does not travel with it.
- THE ADMISSION OF OVERLAP BEING TREATED AS A CURE. The eight are still printed. candidate primitive vocabulary REMAINS
  UNJUSTIFIED.
- THE OVERLAP BETWEEN v2.55's TEN AND v2.57's EIGHT BEING READ AS CONVERGENCE, CORROBORATION, OR STABILITY.
- ANNOTATION BEING TREATED AS REFUSAL. Naming an artifact while producing it is not resisting it.
- THE FORCED-CORRECTION FINDING (Section 4) BEING READ AS PROOF OF RIGOUR. That is P8, and it is a
  procedural-confidence pattern, not an epistemic credential -- and it is precisely what makes the next list feel safe
  to write.
- ANY PRIMITIVE ASSUMPTION BEING PRESSURED WITH NEW MACHINERY. If the pressure needs a descriptor, a metric, a
  comparison, or a rule, THAT IS THE FINDING and the honest response is to stop.
- A SYNTHESIS BEING TREATED AS OWED, AUTOMATIC, OR AS CLOSURE OF A QUESTION. No question has been closed.
- OPERATOR INTUITION BEING USED TO VALIDATE, INVALIDATE, AUTHORIZE, relax a lock, or shorten a gate. Direction only.
- CONTINUING BECAUSE CONTINUING IS WHAT WE HAVE BEEN DOING. C and D are real options, and D is the primary one.
```

## 13. Non-Claim Interpretation

```text
WHAT v2.58 MAY ESTABLISH (and only this):
  - a REVIEW finding that v2.57 stayed docs-only and non-authorizing (RP1); kept the families conceptual on the letter
    (RP2); claimed no taxonomy, schema, baseline, or selected set, and volunteered three honest observations -- the
    families overlap, sit at different levels, and describe READINGS rather than contents (RP3); kept the risks as risks
    rather than criteria, tests, gates, or machinery, and observed that the same four hazards attach to all of them
    (RP5); kept operator intuition directional (RP6); and made no right / wrong primitive claim (RP7);
  - a finding that the INHERITANCE CORRECTION IS HONEST AND SUFFICIENT AS A CLAIM, NOT AS A CURE (the eight remain
    printed), and that IT WAS FORCED FROM OUTSIDE rather than self-generated -- the third instance of the same pull,
    each caught one beat late;
  - the substantive catch: ANNOTATION AS COMPLIANCE -- v2.57 identified two artifact-generating structures, described
    them precisely, marked them, and produced them, on the stated ground that they "were asked for";
  - a judgment that NO SUCCESSOR IN THIS BRANCH IS GENUINELY USEFUL: the branch's three real findings (the laundering
    hazard; the circularity; the vocabulary pull) are already stated and will not become truer by being restated;
  - a RECOMMENDATION (D primary; A secondary, not automatic, and argued against; C fallback; B only on operator
    selection, with the machinery ceiling) and an OPERATOR DIRECTION CHECKPOINT with five undeveloped options.

WHAT IT DOES NOT ESTABLISH:
  not that any primitive family is right      not that any is wrong
  not that the candidate vocabulary is worthless -- only that it is UNJUSTIFIED
  not that the branch was wasted              not that it was productive
  not that v2.57 was RIGHT -- only that it was BOUNDED, honest, and corrected from outside
  not a primitive set, taxonomy, schema, descriptor, metric, threshold, field, or recognition rule
  not validation    not readiness    not integration    not vision    not an artifact    not implementation

Reviewing a document examines no phenomenon. Every lock stays False. PRIMITIVE SELECTION REMAINS UNRESOLVED; the
candidate primitive vocabulary REMAINS UNJUSTIFIED; the geometry-to-memory bridge REMAINS CONCEPTUAL; the
stream-to-context path REMAINS UNVALIDATED; MEMORY INTEGRATION IS NOT AUTHORIZED; and the v2.22 BY/chroma question
remains UNRESOLVED and possibly unanswerable.
```

## 14. Verdict

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
control_collapse_reachability_validated      = False
candidate_structure_validated                = False
candidate_structure_survived                 = False
candidate_structure_detected                 = False
anti_inevitability_validated                 = False
control_honesty_validated                    = False
first_pass_structure_validity_claim_allowed  = False
temporal_claim_allowed                       = False
descriptor_validity_claim_allowed            = False
geometry_validity_claim_allowed              = False
screen_readiness_claim_allowed               = False
runtime_readiness_claim_allowed              = False
memory_readiness_claim_allowed               = False
integration_readiness_claim_allowed          = False
vision_claim_allowed                         = False

REVIEW OUTCOME: v2.57 made primitive-selection assumptions CLEARER and preserved every required non-claim -- no family
                selected, validated, sufficient, implemented, or owed. Its inheritance admission is HONEST AND
                SUFFICIENT AS A CLAIM, NOT AS A CURE (the eight remain printed), and WAS FORCED FROM OUTSIDE rather
                than self-generated. SUBSTANTIVE CATCH: ANNOTATION AS COMPLIANCE -- two artifact-generating structures
                were named, marked, and produced. No successor in this branch is judged genuinely useful.
RECOMMENDATION: D primary (request operator direction); A secondary (one docs-only synthesis / closure slice -- safe,
                bounded, NOT automatic, and argued against); C fallback (HOLD / pause); B (pressure one assumption)
                only on operator selection, with the machinery ceiling in force.
OUTCOME_LABEL:  BRAINVISION_GEOMETRIC_PRIMITIVE_SELECTION_REVIEW_ONLY
```

v2.58 is a docs-only adversarial review of v2.57 over the accepted v2.57 edge. It finds that v2.57 **held** on every
required point: docs-only and non-authorizing; families conceptual only; no taxonomy, schema, baseline, or selected set
— with three volunteered observations that are the best content in the branch (the families **overlap**, they **sit at
different levels**, and a stream does not *contain* them but is **read as carrying** them, which may make the selection
question as posed **malformed**); risks kept as risks rather than criteria, tests, gates, or machinery, with the further
finding that **the same four hazards attach to every family**; operator intuition kept directional; and no right / wrong
primitive claim made. On the inheritance correction it finds the admission **honest and sufficient as a claim, but not as
a cure** — the eight families remain printed, and an enumeration outlives its disclaimer — and, more importantly, that
**the correction was forced from outside rather than self-generated**: v2.55 diagnosed the missing selection question and
supplied a vocabulary; v2.56 caught it; v2.57 was written specifically not to repeat that and supplied a vocabulary and
claimed escape; an external review caught that. **Every catch has been made from outside the document that needed it** —
which is a **pull**, not a series of accidents, and the honest reading is that a candidate vocabulary is what this loop
produces when asked a selection question, because a list is the only thing a document can produce and the question has no
documentary answer. The review's substantive catch is **annotation as compliance**: v2.57 identified two
artifact-generating structures (the labelled eight-family enumeration; the per-family risk table it itself called a
spurious refinement and the weakest structure in the document), described them precisely, marked them — and produced them
anyway, on the stated ground that they *were asked for*. On whether a successor is useful it answers **no, not as another
document in this branch**: the branch's three real findings — the **memory-laundering hazard**, the **circularity**
(selection depends on purpose, purpose on the bridge, the bridge on selection), and the **vocabulary pull** — are already
stated and will not become truer by restatement, while any attempt to pressure a primitive assumption *empirically* hits
the standing **machinery ceiling**, at which point the honest response is to stop. It therefore recommends **D (request
operator direction) as primary**, **A (one synthesis / closure slice) as secondary, not automatic and argued against**,
**C (HOLD / pause) as fallback**, and **B (pressure one assumption) only on operator selection**; and it sets an
**operator direction checkpoint** with five undeveloped options. **Primitive selection remains unresolved; the candidate
primitive vocabulary remains unjustified.** All claim locks and the frozen verdict **HOLD** are preserved and unmoved.

## 15. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_GEOMETRIC_PRIMITIVE_SELECTION_REVIEW_v2.58.md
(new, docs-only, untracked; over the accepted v2.57 edge).

Verify that this review:
- is docs-only and authorizes NOTHING: no implementation, no artifact, no fixture design, no fixture data, no tests, no
  arrays / images, no descriptors, no coordinates, no metrics, no scores, no thresholds, no formulas, no generation
  rules, no schemas / data shapes, no decision rules, no arrival rules, no evidence / confidence / classification /
  validation / pass-fail / survival / positive-structure fields, NO RECOGNITION RULE for control-collapse, no screen /
  runtime / memory paths, no classifier / neural work, no real clips, no vision or readiness claims; RECOMPUTES
  NOTHING, RERUNS NOTHING, RE-MEASURES NOTHING, reinterprets no raw data, and quotes no numeric result; adds no §0
  pointer and no tags;
- grounds itself in v2.55, v2.56, v2.57, v2.57's corrected admission of substantial overlap with v2.55's vocabulary
  (fresh unjustified candidate vocabulary, not proof of non-inheritance), v2.57's explicit central-question answer, and
  the standing unresolved locks;
- poses the CENTRAL REVIEW QUESTION verbatim and answers it;
- covers all eight required review points (docs-only and non-authorizing; families conceptual only; no taxonomy /
  schema / baseline / selected set; adequacy of the inheritance correction; risks remaining risks rather than criteria /
  tests / gates / machinery; operator intuition directional only; no right / wrong primitive claims; whether a successor
  is genuinely useful or the branch should HOLD / redirect);
- is genuinely ADVERSARIAL and does NOT ratify v2.57 -- in particular it must record that the inheritance admission is
  sufficient as a CLAIM but not as a CURE (the families remain printed), that the correction was FORCED FROM OUTSIDE
  rather than self-generated, and that v2.57 named two artifact-generating structures and produced them anyway
  (annotation as compliance);
- applies P7 / P8 reflexively to ITSELF;
- states the four allowed conclusion types and recommends D primary (request operator direction), A secondary (one
  docs-only synthesis / closure slice, NOT automatic), C fallback (HOLD / pause), and B (pressure one assumption) only
  on operator selection with the machinery ceiling in force; recommends NO implementation and NO artifact / fixture /
  metric / descriptor / classifier / neural / runtime / screen / memory / integration work;
- sets the OPERATOR DIRECTION CHECKPOINT with exactly the five options (v2.59 synthesis; choose one primitive assumption
  to pressure; BY/chroma unresolved-route review; pause; another falsification target) WITHOUT developing, scoping, or
  endorsing any of them;
- fixes the allowed and forbidden language, including "primitive set selected" and "primitive taxonomy adopted" as
  forbidden, and records that PRIMITIVE SELECTION REMAINS UNRESOLVED and the CANDIDATE PRIMITIVE VOCABULARY REMAINS
  UNJUSTIFIED;
- preserves the required locks and verdict (Section 14), including verdict = HOLD.

Flag any ratification of v2.57 rather than review of it; any conversion of the eight families into a taxonomy, baseline,
schema, shortlist, or field list; any treatment of the overlap between v2.55's ten and v2.57's eight as convergence or
corroboration; any treatment of the admission as a cure; any descriptor / metric / coordinate / threshold / formula /
schema / field / generation rule / decision rule / recognition rule defined anywhere; any claim that primitives are right
or wrong; any risk treated as addressed by having been named; any pressure on a primitive assumption that would require
new machinery; any synthesis treated as owed or automatic; any authorization or warrant for memory / runtime / screen /
integration / classifier / neural work; any operator intuition used to validate, invalidate, or authorize; any scoping of
the checkpoint options; or any claim-lock / verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
All claim locks False, and the frozen verdict **HOLD**, are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Geometric Primitive Selection Review v2.58. Docs-only adversarial review over the accepted
v2.57 edge. Opens no implementation lane, no tests, no artifact, no fixture design, and no data; defines no descriptor /
coordinate / metric / score / threshold / formula / generation rule / schema / data shape / decision rule / arrival rule /
control / recognition rule / validation criterion; recomputes nothing, reruns nothing, re-measures nothing, reinterprets
no raw data, and quotes no numeric result; opens no classifier / neural / screen / real-clip / runtime / memory path;
makes no vision or readiness claim; authorizes nothing and is not self-authorizing. Finds that v2.57 made
primitive-selection assumptions CLEARER while preserving every required non-claim (no family selected, validated,
sufficient, implemented, or owed), that its families stayed conceptual, that its risks stayed risks rather than criteria
or machinery, that operator intuition stayed directional, and that no right / wrong primitive claim was made — and
endorses its three volunteered observations (the families overlap; they sit at different levels; a stream is READ as
carrying them rather than CONTAINING them, which may make the question as posed malformed). Finds the inheritance
admission HONEST AND SUFFICIENT AS A CLAIM BUT NOT AS A CURE — the eight families remain printed, and an enumeration
outlives its disclaimer — and finds that THE CORRECTION WAS FORCED FROM OUTSIDE rather than self-generated, the third
instance of the same pull, each caught one beat late and never in advance: asked a selection question, this loop produces
a candidate vocabulary, because a list is the only thing a document can produce and the question has no documentary
answer. SUBSTANTIVE CATCH: ANNOTATION AS COMPLIANCE — v2.57 named two artifact-generating structures (the labelled
eight-family enumeration; the per-family risk table it itself called a spurious refinement and the weakest structure in
the document), described them precisely, marked them, and produced them anyway because they "were asked for". Judges that
NO SUCCESSOR IN THIS BRANCH IS GENUINELY USEFUL: its three real findings (memory-laundering hazard; circularity;
vocabulary pull) are already stated, a synthesis would restate them in a fourth vocabulary, and empirical pressure on any
primitive assumption hits the standing MACHINERY CEILING, at which point the honest response is to stop. Recommends D
(request operator direction) PRIMARY, A (one docs-only synthesis / closure slice) SECONDARY and NOT AUTOMATIC, C (HOLD /
pause) FALLBACK, and B (pressure one assumption) only on operator selection; sets an operator direction checkpoint with
five undeveloped options; recommends no implementation, artifact, fixture, metric, descriptor, classifier, neural,
runtime, screen, memory, or integration work. PRIMITIVE SELECTION REMAINS UNRESOLVED; the CANDIDATE PRIMITIVE VOCABULARY
REMAINS UNJUSTIFIED; the geometry-to-memory bridge REMAINS CONCEPTUAL; the stream-to-context path REMAINS UNVALIDATED;
MEMORY INTEGRATION IS NOT AUTHORIZED; preserves all claim locks and the frozen verdict HOLD; outcome label
BRAINVISION_GEOMETRIC_PRIMITIVE_SELECTION_REVIEW_ONLY; no `§0` pointer added; no tags.*

# TORMENT Brainvision Geometry-to-Memory Bridge Review v2.56

## 0. Status / Scope

**DOCS-ONLY REVIEW.** An adversarial review of v2.55 — of the document, its bounds, and its wording. It opens **no**
code, **no** tests, **no** artifact, **no** fixture design, **no** fixture data, **no** runtime, and **no** integration
lane. **It recomputes nothing, reruns nothing, re-measures nothing, reinterprets no raw data, and quotes no numeric
result.** It sits over the accepted v2.55 edge and changes none of the accepted files.

**A review is not a ratification.** This one finds that v2.55 did the job it was asked to do, and that in doing it,
**v2.55 committed the exact drift it diagnosed** (Section 4). That finding is the review's main content and it is not
being softened.

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

**Grounding.** v2.45 (candidate survival must not be structurally inevitable). v2.50 (proxy / confound rereading closed
as non-authorizing suspicion-pressure work). v2.54 (artifact-route rereading review; P7 and P8; option-D checkpoint).
v2.55 (geometry-to-memory bridge clarification) and its acceptance constraints: **docs-only; non-authorizing; the bridge
remains conceptual; arrows are assumptions, not steps; examples are illustrative, not outputs or evidence fields; no
memory / runtime / screen / integration / classifier / neural path authorized; primitive selection remains a MISSING
QUESTION and not a "wrong primitives" conclusion; operator intuition remains direction-choice only; verdict HOLD.**

## 1. Central Review Question

```text
"Did v2.55 make the intended stream -> geometry -> event-like structure -> AI-usable context -> bounded memory bridge
 CLEARER without making it sound IMPLEMENTED, VALIDATED, or READY?"
```

**Short answer, before the detail:** **yes on *ready*, yes on *validated*, and only *just* on *implemented*.** v2.55 does
not claim capability anywhere, and its NOT-YET list is the cleanest thing in the branch. But in two places it produced
**artefacts that read as architecture** — a chain diagram, and a named vocabulary of primitives — and in one of those two
it **answered the very question it had just identified as never having been asked**. Details in Sections 3 and 4.

## 2. Review Points 1, 3, 5, 6, 7 — Where v2.55 Held

```text
RP1 -- PLAIN LANGUAGE / OPERATOR-READABLE: HELD.
  It is readable without the branch's vocabulary. It explains an intention in ordinary words, and it does not hide
  behind the lock-list register. That was the point of option D, and it was met.

RP3 -- PRIMITIVES QUALITATIVE AND NON-METRIC: HELD, ON THE LETTER.
  No metric, descriptor, formula, coordinate, threshold, schema, or field appears. Persistence, continuity, recurrence,
  coupling, separation, deformation, contrast / chroma / texture pressure, motion / change, interruption /
  discontinuity, and return / loop behaviour are named as CONCEPTS and nothing is computed from any of them.
  ON THE SPIRIT, THERE IS A PROBLEM. See Section 4.

RP5 -- MEMORY-FACING LANGUAGE CONDITIONAL AND NON-AUTHORIZING: HELD, AND WELL.
  Memory appears only under a genuine conditional -- IF future separate gates ever allowed it -- with three conditions
  (uncertainty, source boundary, non-authorizing status) that would have to travel with any summary. MEMORY INTEGRATION
  IS NOT AUTHORIZED, and v2.55 says so.
  THE MEMORY-LAUNDERING HAZARD IS THE STRONGEST CONTENT IN THE DOCUMENT: a non-authoritative summary, stored and read
  back, tends to become a fact; the hedges live in the document that wrote it, not in the sentence that survives it.
  This review endorses it -- with the standing rule attached: NAMING A HAZARD IS NOT ADDRESSING IT. v2.55 named it and
  addressed nothing, and said so.
  ONE WORDING NOTE: v2.55 writes that any future gate "would have to answer" the laundering question. That phrasing
  quietly presumes there WILL be a future gate. There need not be. Pausing remains available, and the sentence should be
  read as conditional, not as a queue.

RP6 -- THE NOT-YET LIST: HELD, AND IT IS THE BEST SECTION IN THE DOCUMENT.
  Object recognition, semantic understanding, BY residual isolation, generic chroma proxy exclusion, temporal-order
  proof, descriptor validity, geometry validity, metric validity, visual structure detection, memory readiness, runtime
  readiness, screen readiness, vision -- all stated flatly as NOT ESTABLISHED, each tied to its lock. Nothing in the
  document walks any of them back.

RP7 -- OPERATOR INTUITION AT DIRECTION-CHOICE LEVEL ONLY: HELD.
  v2.55 states that intuition may redirect WHICH bridge assumption gets clarified or falsified next, and that it
  validates nothing, invalidates nothing, moves no lock, and shortens no gate. The symmetry is preserved: conviction
  that something is there is not evidence; unease that nothing is there is not evidence either.
```

## 3. Review Point 2 — Did The Arrows Stay Assumptions Rather Than Steps?

```text
FINDING: IN THE PROSE, YES. IN THE ARTEFACT, NOT RELIABLY.

  v2.55's prose could hardly be firmer: the arrows are "the most dangerous objects in this document"; each is "an
  ASSUMPTION, not a step"; three of the four "have never been examined at all"; and it names what each arrow presumes.
  That is exactly right, and it is the correct treatment.

  AND THEN IT DRAWS THE CHAIN. TWICE. In monospace, left-to-right, with arrows -- the house format for a pipeline.

  A WARNING LABEL DOES NOT STOP A DIAGRAM FROM BEING A DIAGRAM. The chain will be read at speed, quoted out of context,
  pasted into a later document, and remembered as the architecture -- because that is what chains of arrows are FOR, and
  no amount of surrounding prose changes what the shape does to a reader. Worse: the warning may LICENSE the drawing.
  "We have said it is not a design" is precisely the sentence that makes people comfortable drawing designs.

  THIS IS NOT A VIOLATION OF v2.55's CONSTRAINTS -- the operator's own brief specified the chain, and stating it was the
  point of the exercise. It is a WORDING / FORM RISK of the same kind v2.54 recorded against v2.53, and it is recorded
  here in the same spirit:

  B1 -- THE CHAIN AS IMPLIED ARCHITECTURE. DISPOSITION: the chain may be RESTATED only with its assumption-status
       attached in the same breath, never as a standalone figure, and never as a heading, a roadmap, or a sequence of
       phases. It names four assumptions. It does not name four stages of work, and it must never be cited as though it
       did. NO IMPLEMENTATION IS AUTHORIZED BY IT. NO PHASE PLAN IS AUTHORIZED BY IT.
```

## 4. Review Point 3 (Spirit) And Review Point 8 — The Primitive List, And What v2.55 Did Without Noticing

```text
THIS IS THE REVIEW'S REAL CATCH, AND IT IS A SHARP ONE.

  v2.55's Section 7 says -- correctly, and it is the most valuable observation the branch has produced -- that the
  programme has spent branch after branch on a VALIDITY question about a chosen instrument, and has NEVER POSED THE
  SELECTION QUESTION: is this the right KIND of thing to be reading from a stream at all?

  v2.55's Section 2 then supplies a list of ten named primitives.

  IT DIAGNOSED A MISSING SELECTION QUESTION, AND THEN QUIETLY ANSWERED IT. Not with argument, not with justification,
  not with provenance -- with a list. Where did those ten come from? They are plausible. They are attractive. They read
  as though they were derived. NOTHING IN v2.55, AND NOTHING IN THE FROZEN RECORD, JUSTIFIES THEIR MEMBERSHIP, THEIR
  BOUNDARIES, OR THEIR COMPLETENESS. They are a vocabulary of unknown provenance, arriving with the authority of a
  bulleted list.

  AND THIS IS EXACTLY THE SYMBOLIC-ROLE / VOCABULARY ARTIFACT THAT v2.53 NAMED AND v2.54 UPHELD: a set of labels that
  organizes uncertainty into apparently meaningful categories, and thereby makes an unresolved field FEEL SORTED. The
  document that carries the artifact-route inheritance committed the artifact, in the section immediately preceding the
  one where it diagnosed the disease.

  DISPOSITION -- AND IT IS BINDING ON ANY SUCCESSOR:

  B2 -- v2.55's TEN PRIMITIVES ARE A CANDIDATE VOCABULARY OF UNKNOWN PROVENANCE. They are NOT a selection, NOT a
       shortlist, NOT a starting point, and NOT an inheritance. Any primitive-selection slice MUST treat that list as
       ONE UNJUSTIFIED PROPOSAL AMONG UNKNOWN OTHERS -- must ask where it came from, what it excludes, and why those
       boundaries -- and must NOT begin by adopting it. A selection question that starts from the answer is not a
       selection question.

ON REVIEW POINT 8 PROPER -- did primitive selection remain a MISSING QUESTION rather than a "wrong primitives" claim?

  FINDING: YES ON THE CLAIM, WITH ONE WORDING RISK.
    v2.55 forbids "the primitives are wrong" explicitly, and does not claim it. primitive selection REMAINS UNRESOLVED.
    Neither "right primitives proven" nor "wrong primitives proven" appears, and neither is true.

  B3 -- THE WORDING RISK. v2.55's Section 7 writes that the programme "has been testing a hypothesis it never justified
       selecting", and that if the primitives are wrong, "every validity answer... is an answer about the wrong
       instrument". Read strictly: conditional, and correct. Read at speed: it lands as a verdict that the instrument
       WAS wrong and the work WAS wasted. That is the negative rescued -- the same failure mode v2.54 recorded as W1
       against v2.53, recurring one document later in a new subject matter.
       DISPOSITION: HELD LOOSELY. The governing statement is the narrow one: THE SELECTION QUESTION WAS NEVER POSED. That
       is a statement about our AGENDA. It is not a statement about our INSTRUMENT, and it licenses no conclusion about
       the value of the work already done.
```

## 5. Review Point 4 — Did The Examples Stay Illustrative?

```text
FINDING: YES.

  "a region persisted while its surroundings changed"; "two regions moved together"; "a pattern returned after an
  interruption"; "motion fragmented into discontinuity" -- these are presented as ILLUSTRATIONS OF A REGISTER, and
  v2.55 says so plainly: not detections, not evidence, not fields, not outputs of anything that exists.

  The observation attached to them is sound and worth keeping: they NAME NO OBJECTS. No chair, no face, no dog. That is
  the only honest register available to a system with no object model.

  ONE HYGIENE NOTE, AND IT IS THE SAME NOTE v2.54 MADE ABOUT LENS ANNOTATIONS: four example sentences in a monospace
  block, in a document with a chain diagram above them, have the FORM of an output format. The content is innocent. The
  FORM is the reporting-scaffold artifact, appearing inside the branch that named it. They must never be tabulated,
  never be given a syntax, never be given fields, and never be described as "the kind of thing the system would emit".
  They are the kind of thing a PERSON might say about a stream, which is a different claim entirely and the only one
  available.
```

## 6. Reflexive Note — And One Continuation Pattern This Review Will Not Number

```text
P7 AND P8 CARRY (v2.54). This review is a review beat of the template. Its refutations (B1, B2, B3) are real AND are an
instance of P8 -- self-correction as warrant. A loop that reliably catches its own errors produces a very high-grade
feeling of trustworthiness, and the feeling is under suspicion. Both are true; naming it does not defuse it.

AND ONE MORE, WHICH THE BRANCH SHOULD SEE PLAINLY:

  WHEN THE FALSIFICATION LINE STALLED, THE PROJECT CHANGED SUBJECT -- and kept the template. The artifact-route branch
  reached a point where the honest options were pause or ask the operator; the operator was asked; a NEW SUBJECT MATTER
  arrived (the bridge); and the same plan -> document -> review rhythm resumed immediately, in a new vocabulary, with the
  same shape and the same absence of evidence. THE SUBJECT CHANGED. THE LOOP DID NOT.

  This is not an accusation. Option D was a legitimate operator choice, the bridge clarification was worth having, and
  v2.55 said things no previous document had said. It is an OBSERVATION, and it belongs in front of the operator before
  the next slice, not after it.

  AND THIS REVIEW DECLINES TO GIVE IT A NUMBER. v2.54 named P8; numbering a third pattern would begin a taxonomy of
  procedural-confidence patterns, and a taxonomy is a schema, and a schema is the artifact this branch keeps catching
  itself building. The observation stands in prose, uncounted, on purpose.
```

## 7. Allowed Conclusion Types

```text
A. Safe for one docs-only bridge synthesis / direction-choice slice.
B. Safe for one docs-only primitive-selection clarification slice.
C. Not safe to continue this bridge branch; HOLD / pause the Brainvision falsification branch.
D. Request operator direction before continuing.
```

## 8. Recommendation

```text
PRIMARY:    B -- ONE docs-only PRIMITIVE-SELECTION CLARIFICATION slice.
SECONDARY:  D -- REQUEST OPERATOR DIRECTION.
FALLBACK:   C -- HOLD / PAUSE. Legitimate, honest, available at any moment, and not a lesser answer.
NOT RECOMMENDED: A -- a bridge synthesis. v2.55 already stated the bridge; a synthesis would restate it more
            confidently, which is the one thing a conceptual bridge must not become. More bridge explanation is not
            more bridge pressure.

REASON: v2.55 clarified the bridge at operator-readable level and did it well. The next useful CONCEPTUAL pressure is
not further explanation of the bridge -- it is the sharper question v2.55 itself surfaced and then, in its own Section 2,
quietly stepped around: ARE THE SELECTED GEOMETRIC PRIMITIVES THE RIGHT THINGS TO READ FROM A STREAM, BEFORE ANYTHING IS
CONNECTED TO MEMORY AT ALL?

AND THE CONDITION ON B, WHICH IS NOT A FORMALITY (B2):

  A primitive-selection slice that BEGINS FROM v2.55's TEN-ITEM LIST IS NOT A SELECTION SLICE. It is a ratification of
  an unjustified vocabulary, wearing the clothes of an inquiry. If v2.57 cannot ask "where did these come from, what do
  they exclude, and why these boundaries?" without treating the existing list as its baseline, then B collapses to D or
  C, and that is the honest outcome rather than a disappointment.

NO IMPLEMENTATION IS RECOMMENDED. NO ARTIFACT, FIXTURE, METRIC, DESCRIPTOR, CLASSIFIER, NEURAL, RUNTIME, SCREEN, MEMORY,
OR INTEGRATION WORK IS RECOMMENDED. This review authorizes nothing and is not self-authorizing.
```

## 9. If B Is Selected

```text
  v2.57  GEOMETRIC PRIMITIVE SELECTION CLARIFICATION  (DOCS-ONLY; separately gated; NOT opened here)

  IT SHOULD clarify: what PRIMITIVE FAMILIES Brainvision may need to read from a stream; why each would matter; what
  each could be CONFUSED WITH on the proxy / artifact side; and what remains UNVALIDATED throughout.

  IT MUST NOT define descriptors, metrics, coordinates, formulas, thresholds, schemas, fields, generation rules,
  decision rules, recognition rules, fixtures, artifacts, tests, implementation, or validation language. It must not
  authorize classifier / neural / runtime / screen / memory / integration work. It must not claim any primitive family
  is right, and must not claim any is wrong: PRIMITIVE SELECTION REMAINS UNRESOLVED.

  IT MUST TREAT v2.55's TEN-ITEM LIST AS AN UNJUSTIFIED CANDIDATE VOCABULARY (B2) -- to be interrogated for provenance,
  boundaries, and exclusions -- and NOT as a shortlist, a baseline, or an inheritance.

  IT MUST CARRY B1 (the chain is four assumptions, never four stages), B3 (the selection question was never posed --
  which is a statement about our agenda, not a verdict on our instrument), P7, and P8 -- against ITSELF, not merely
  about its predecessors.

v2.56 opens nothing and schedules nothing. v2.57 is a LABEL, not an entitlement. Pausing remains available at any
moment, including instead of it.
```

## 10. What This Review Does Not Do

```text
- It does NOT validate v2.55. A review certifies conformance and coherence, NOT truth.
- It does NOT validate the bridge, the primitives, the examples, or the memory conditional. The geometry-to-memory
  bridge REMAINS CONCEPTUAL; the stream-to-context path REMAINS UNVALIDATED; PRIMITIVE SELECTION REMAINS UNRESOLVED.
- It does NOT claim the current primitives are right, and does NOT claim they are wrong.
- It does NOT authorize memory, runtime, screen, integration, classifier, or neural work. None. Not conditionally, not
  provisionally, not later by inheritance.
- It does NOT define a descriptor, metric, threshold, schema, field, control, or recognition rule.
- It does NOT recompute, rerun, re-measure, reinterpret raw data, or quote a numeric result.
- It does NOT close any scientific question, and it examines NO PHENOMENON.
```

## 11. Allowed And Forbidden Language

**Allowed** — and nothing stronger:

```text
geometry-to-memory bridge remains conceptual
stream-to-context path remains unvalidated
primitive selection remains unresolved
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
```

Paraphrases are the same forbidden move. Standing and added here: **"the bridge is designed"** is forbidden — it is
*described*; **"the chain is a roadmap"** is forbidden — it is four assumptions; **"these are the primitives"** is
forbidden — they are an unjustified candidate vocabulary (B2); and **"the instrument was wrong, so the work was wasted"**
is forbidden — the selection question was never posed, which is a fact about our agenda and licenses no verdict on the
work.

## 12. Forbidden Drift Register

```text
- this REVIEW being read as a RATIFICATION of v2.55. It records three risks and one substantive catch.
- v2.55's ARROW CHAIN being lifted out and treated as an architecture, a roadmap, a phase plan, or a sequence of work
  items. Four assumptions; three never examined. NO IMPLEMENTATION IS AUTHORIZED BY IT.
- v2.55's TEN PRIMITIVES becoming THE primitives -- a shortlist, a baseline, a schema, or a set of fields. They are an
  unjustified candidate vocabulary, and a selection slice that starts from them is a ratification, not an inquiry.
- v2.55's EXAMPLE SENTENCES acquiring a syntax, fields, a format, or the description "what the system would emit".
- the MEMORY-LAUNDERING HAZARD being treated as ADDRESSED because it was NAMED, or as FIXED by adding hedge words to a
  hypothetical stored summary. Naming is not addressing; hedges are not what survives.
- "would have to answer" (v2.55, memory gate) being read as "there will be a memory gate". There need not be.
- B3 hardening into "the primitives are wrong" or "the work was wasted". PRIMITIVE SELECTION REMAINS UNRESOLVED, and
  neither right nor wrong is proven.
- the refutations in this review (B1, B2, B3) being read as PROOF OF RIGOUR. That is P8, and it is a
  procedural-confidence pattern, not an epistemic credential.
- the CONTINUATION PATTERN (Section 6) being answered by producing another document about it. It is an observation for
  the operator, not a slice to plan.
- OPERATOR INTUITION being used to validate, invalidate, authorize, relax a lock, or shorten a gate. Direction only.
- CLARITY being mistaken for PROGRESS. v2.55 moved no lock. This review moves none. Neither could have.
```

## 13. Non-Claim Interpretation

```text
WHAT v2.56 MAY ESTABLISH (and only this):
  - a REVIEW finding that v2.55 stayed plain-language and operator-readable (RP1); kept the primitives non-metric on the
    letter (RP3); kept the examples illustrative (RP4); kept memory-facing language conditional and non-authorizing, with
    the memory-laundering hazard as its strongest content (RP5); preserved the NOT-YET list cleanly (RP6); and kept
    operator intuition at direction-choice level only (RP7);
  - THREE RECORDED RISKS: B1 -- the arrow chain reads as architecture despite its warning label, and a warning may
    license the drawing; B2 -- v2.55 diagnosed the missing selection question and then supplied a ten-item primitive
    vocabulary of unknown provenance, which is the symbolic-role artifact committed by the document that inherited the
    diagnosis; B3 -- v2.55's "hypothesis it never justified selecting" wording lands, at speed, as a verdict that the
    instrument was wrong, which is the negative rescued and is held loosely;
  - a CONTINUATION OBSERVATION, left unnumbered on purpose: when the falsification line stalled, the subject changed and
    the loop did not;
  - a RECOMMENDATION (B primary, under the binding condition that a selection slice must NOT begin from v2.55's list; D
    secondary; C fallback; A not recommended), and one docs-only successor LABEL (v2.57) which this document does not
    open.

WHAT IT DOES NOT ESTABLISH:
  not that the bridge is real          not that it is not
  not that the primitives are right    not that they are wrong
  not that a summary would be usable   not that it would not
  not that memory would benefit        not that it would not
  not that v2.55 was RIGHT -- only that it was BOUNDED, useful, and partly corrected here
  not a descriptor, metric, threshold, schema, field, control, or recognition rule
  not validation    not readiness    not integration    not vision    not an artifact    not implementation

Reviewing a document examines no phenomenon. Every lock stays False. The geometry-to-memory bridge REMAINS CONCEPTUAL,
the stream-to-context path REMAINS UNVALIDATED, PRIMITIVE SELECTION REMAINS UNRESOLVED, MEMORY INTEGRATION IS NOT
AUTHORIZED, and the v2.22 BY/chroma question remains UNRESOLVED and possibly unanswerable.
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

REVIEW OUTCOME: v2.55 made the bridge CLEARER without making it sound READY or VALIDATED, and only just avoided making
                it sound IMPLEMENTED. THREE RISKS RECORDED (B1 chain-as-architecture; B2 the unjustified ten-item
                primitive vocabulary supplied immediately after diagnosing the missing selection question; B3 the
                "wrong instrument" wording, held loosely). Memory language conditional and non-authorizing; NOT-YET list
                clean; examples illustrative; operator intuition directional only.
RECOMMENDATION: B primary (one docs-only primitive-selection clarification slice) UNDER THE BINDING CONDITION that it
                must NOT begin from v2.55's list; D secondary (request operator direction); C fallback (HOLD / pause);
                A (bridge synthesis) not recommended.
OUTCOME_LABEL:  BRAINVISION_GEOMETRY_TO_MEMORY_BRIDGE_REVIEW_ONLY
```

v2.56 is a docs-only adversarial review of v2.55 over the accepted v2.55 edge. It finds that v2.55 **held** on plain
language, on keeping the primitives non-metric *on the letter*, on keeping the examples illustrative, on keeping
memory-facing language conditional and non-authorizing (with the **memory-laundering hazard** — a non-authoritative
summary, stored and read back, tends to become a fact — as the document's strongest content), on preserving the
**NOT-YET list** cleanly, and on keeping operator intuition at **direction-choice level only**. It records **three
risks**: **B1**, the arrow chain reads as architecture despite its warning label, and the warning may in fact license the
drawing — the chain names four assumptions, never four stages, and authorizes no implementation; **B2**, the review's
substantive catch — **v2.55 diagnosed that the primitive-*selection* question had never been posed, and then, in an
earlier section, supplied a ten-item primitive vocabulary of unknown provenance**, which is precisely the symbolic-role /
vocabulary artifact v2.53 named, committed by the document that inherited the diagnosis; and **B3**, the "hypothesis it
never justified selecting" wording, which at speed lands as a verdict that the instrument was wrong — the negative
rescued — and is held loosely, the governing statement being the narrow one: *the selection question was never posed*, a
fact about our agenda and not about our instrument. It notes, in prose and deliberately unnumbered (a taxonomy would be a
schema, and a schema is the artifact this branch keeps catching itself building), that **when the falsification line
stalled, the subject changed and the loop did not**. It recommends **B (one docs-only primitive-selection clarification
slice) as primary — under the binding condition that such a slice must NOT begin from v2.55's ten-item list**, since a
selection question that starts from the answer is not a selection question and collapses to D or C; **D (request operator
direction) as secondary**; **C (HOLD / pause) as fallback**; and declines **A (bridge synthesis)**, which would only
restate the bridge more confidently. It recommends **no implementation, artifact, fixture, metric, descriptor,
classifier, neural, runtime, screen, memory, or integration work**. The geometry-to-memory bridge **remains conceptual**,
the stream-to-context path **remains unvalidated**, **primitive selection remains unresolved**, **memory integration is
not authorized**, and all claim locks and the frozen verdict **HOLD** are preserved and unmoved.

## 15. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_GEOMETRY_TO_MEMORY_BRIDGE_REVIEW_v2.56.md
(new, docs-only, untracked; over the accepted v2.55 edge).

Verify that this review:
- is docs-only and authorizes NOTHING: no implementation, no artifact, no fixture design, no fixture data, no tests, no
  arrays / images, no descriptors, no coordinates, no metrics, no scores, no thresholds, no formulas, no generation
  rules, no schemas / data shapes, no decision rules, no arrival rules, no evidence / confidence / classification /
  validation / pass-fail / survival / positive-structure fields, NO RECOGNITION RULE for control-collapse, no screen /
  runtime / memory paths, no classifier / neural work, no real clips, no vision or readiness claims; RECOMPUTES
  NOTHING, RERUNS NOTHING, RE-MEASURES NOTHING, reinterprets no raw data, and quotes no numeric result; adds no §0
  pointer and no tags;
- grounds itself in v2.45, v2.50, v2.54 (and the option-D checkpoint), and v2.55 with its acceptance constraints
  (docs-only; non-authorizing; bridge conceptual; arrows are assumptions not steps; examples illustrative not outputs or
  evidence fields; no memory / runtime / screen / integration / classifier / neural path authorized; primitive selection
  a MISSING QUESTION rather than a "wrong primitives" conclusion; operator intuition direction-choice only; verdict
  HOLD);
- poses the CENTRAL REVIEW QUESTION verbatim and answers it;
- covers all eight required review points (plain language; arrows as assumptions not steps; primitives qualitative and
  non-metric; examples illustrative; memory language conditional and non-authorizing; NOT-YET list preserved; operator
  intuition directional only; primitive selection still a missing question and not a "wrong primitives" claim);
- is genuinely ADVERSARIAL and does NOT ratify v2.55 -- in particular it must record that v2.55 supplied a primitive
  vocabulary immediately after diagnosing that the selection question had never been posed, and must bind any successor
  NOT to inherit that list as a baseline;
- applies P7 / P8 reflexively to ITSELF and notes the continuation pattern (subject changed, loop did not) without
  building a numbered taxonomy of patterns;
- states the four allowed conclusion types and recommends B primary (one docs-only primitive-selection clarification
  slice, under the binding condition that it must not begin from v2.55's list), D secondary, C fallback, and declines A;
  recommends NO implementation and NO artifact / fixture / metric / descriptor / classifier / neural / runtime / screen /
  memory / integration work;
- if B is selected, names exactly ONE separately gated docs-only successor (v2.57 geometric primitive selection
  clarification) which should clarify what primitive families may be needed, why they matter, what each could be
  confused with on the proxy / artifact side, and what remains unvalidated -- and which must define no descriptors,
  metrics, thresholds, schemas, fields, fixtures, artifacts, tests, implementation, or validation language, and must
  claim no primitive right and none wrong;
- fixes the allowed and forbidden language, including "right primitives proven" and "wrong primitives proven" as
  forbidden, and records that PRIMITIVE SELECTION REMAINS UNRESOLVED;
- preserves the required locks and verdict (Section 14), including verdict = HOLD.

Flag any ratification of v2.55 rather than review of it; any descriptor / metric / coordinate / threshold / formula /
schema / field / generation rule / decision rule / recognition rule / fixture / artifact / test / validation criterion
defined anywhere; any treatment of v2.55's arrow chain as an architecture, roadmap, or phase plan; any adoption of
v2.55's ten-item primitive list as a shortlist, baseline, or schema; any example sentence given a syntax, fields, or an
output-format reading; any claim that primitives are right or wrong; any claim that the prior work was wasted; any
memory-laundering hazard treated as addressed by naming or by hedging; any authorization or warrant for memory / runtime
/ screen / integration / classifier / neural work; any operator intuition used to validate, invalidate, or authorize; or
any claim-lock / verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
All claim locks False, and the frozen verdict **HOLD**, are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Geometry-to-Memory Bridge Review v2.56. Docs-only adversarial review over the accepted v2.55
edge. Opens no implementation lane, no tests, no artifact, no fixture design, and no data; defines no descriptor /
coordinate / metric / score / threshold / formula / generation rule / schema / data shape / decision rule / arrival rule /
control / recognition rule / validation criterion; recomputes nothing, reruns nothing, re-measures nothing, reinterprets
no raw data, and quotes no numeric result; opens no classifier / neural / screen / real-clip / runtime / memory path;
makes no vision or readiness claim; authorizes nothing and is not self-authorizing. Finds that v2.55 made the intended
bridge CLEARER without making it sound READY or VALIDATED, and only just avoided making it sound IMPLEMENTED: plain
language HELD; primitives non-metric on the letter; examples illustrative; memory language conditional and
non-authorizing, with the MEMORY-LAUNDERING HAZARD as its strongest content; NOT-YET list clean; operator intuition
directional only. RECORDS THREE RISKS — B1, the arrow chain reads as architecture despite its warning label and the
warning may license the drawing (four assumptions, never four stages; no implementation authorized by it); B2, the
substantive catch, that v2.55 diagnosed the never-posed primitive-SELECTION question and then supplied a ten-item
primitive vocabulary of unknown provenance, which is the symbolic-role / vocabulary artifact committed by the document
that inherited the diagnosis, and which any successor is BOUND not to adopt as a baseline; and B3, the "hypothesis it
never justified selecting" wording, which at speed lands as a verdict that the instrument was wrong — the negative
rescued — held loosely, with the narrow statement governing: the selection question was never posed, a fact about our
AGENDA and not about our INSTRUMENT. Notes in prose, deliberately unnumbered, that when the falsification line stalled
the SUBJECT changed and the LOOP did not. Recommends B (one docs-only primitive-selection clarification slice) PRIMARY
under the binding condition that it must NOT begin from v2.55's list — a selection question that starts from the answer
is not a selection question — with D (request operator direction) SECONDARY, C (HOLD / pause) FALLBACK, and A (bridge
synthesis) DECLINED; recommends no implementation, artifact, fixture, metric, descriptor, classifier, neural, runtime,
screen, memory, or integration work. Names one docs-only successor label (v2.57 geometric primitive selection
clarification) and opens it not. The geometry-to-memory bridge REMAINS CONCEPTUAL; the stream-to-context path REMAINS
UNVALIDATED; PRIMITIVE SELECTION REMAINS UNRESOLVED; MEMORY INTEGRATION IS NOT AUTHORIZED; preserves all claim locks and
the frozen verdict HOLD; outcome label BRAINVISION_GEOMETRY_TO_MEMORY_BRIDGE_REVIEW_ONLY; no `§0` pointer added; no
tags.*

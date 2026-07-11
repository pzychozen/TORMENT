# TORMENT Brainvision Proxy / Confound Rereading Review v2.49

## 1. Status / Scope

**DOCS-ONLY review.** This is a review note only. It opens **no** code, **no** tests, **no** artifact, **no** fixture
design, **no** fixture data, **no** runtime, and **no** integration lane. **It recomputes nothing, reruns nothing,
re-measures nothing, and reinterprets no raw data.** It sits over the accepted v2.48 edge (`d691f10 docs(research):
scan frozen evidence proxy confounds`) and changes none of the accepted files.

**v2.49 exists to stop a scan from becoming a conclusion.** v2.48's value is **suspicion pressure only, not proof** —
and the direction of the drift risk has now flipped. For twenty slices the danger was rescuing a residual. In v2.48 the
danger became rescuing a *negative*. The review below treats both as the same error.

**Explicitly authorized: nothing.**

```text
NO IMPLEMENTATION. NO ARTIFACT. NO FIXTURE DESIGN. NO TESTS. NO FIXTURE DATA. NO ARRAYS / IMAGES.
NO DESCRIPTORS, COORDINATES, METRICS, SCORES, THRESHOLDS, FORMULAS, GENERATION RULES, SCHEMAS, DATA SHAPES,
  DECISION RULES, ARRIVAL RULES, PASS/FAIL GATES, CONTROLS, OR VALIDATION.
NO RECOMPUTATION. NO RERUNS. NO NEW MEASUREMENTS. NO NEW INTERPRETATION OF RAW DATA.
NO RECOGNITION RULE FOR CONTROL-COLLAPSE. NO CLASSIFIER (FORM B) / NEURAL (FORM C) WORK.
NO SCREEN / REAL-CLIP / RUNTIME / MEMORY PATH. NO VISION CLAIM. NO READINESS CLAIM.
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

## 2. Grounding And Central Review Question

```text
v2.46  Direction scan: proxy / confound route selected, bounded to frozen-evidence rereading; "what survives the
       proxies" FORBIDDEN as a framing.
v2.47  Question plan: seven proxy / confound families as question targets; boundary (no new machinery, no
       re-computation, no ruling-out, no rescuing); negative answer PRE-ACCEPTED as legitimate.
v2.48  Frozen-evidence rereading scan, under acceptance constraints: docs-only; no recomputation / reruns /
       re-measurement; no quoted numeric values; no new machinery; NO THRESHOLD-ARTIFACT CONCLUSION; negative reading
       legitimate but NOT CONCLUDED; P6 (vocabulary / schema lens) preserved; all locks False; verdict HOLD.
```

```text
CENTRAL REVIEW QUESTION:
"Did v2.48 make proxy / confound explanations easier to SEE in the frozen record without claiming those explanations
 are true, controlled, ruled out, or resolved?"
```

## 3. Review Point 1 — Did v2.48 Stay Within Frozen-Evidence Rereading?

```text
FINDING: YES.

  It reread branch conclusions and frozen summaries. It examined no phenomenon, opened no data, and made no statement
  about colour, structure, or the world -- only about the RECORD and its LANGUAGE. That distinction is stated in the
  scan itself and is held throughout.

  ONE BOUNDARY WORTH NAMING, BECAUSE IT IS THIN: restating a frozen summary ("the confound was not dissolved") is
  rereading. SHARPENING it ("the confound dominates") would be reinterpretation. v2.48 stays on the correct side of
  that line, but the line is one adjective wide, and v2.50 will be standing on it.
```

## 4. Review Point 2 — Recomputation, Measurement, Evidence Fields, Raw-Data Reinterpretation

```text
FINDING: NONE FOUND.

  No recomputation. No rerun. No re-measurement. No raw file opened for values. No evidence table. NO NUMERIC VALUE
  QUOTED ANYWHERE -- a deliberate choice by the scan, on the reasoning that quoting a number invites re-deriving one.
  That choice is sound and should be carried into v2.50 unchanged.

  The scan characterises frozen results qualitatively ("recorded as unresolved", "returned a negative result on its own
  prerequisite", "attributed its separation to construction"). These are RESTATEMENTS OF THE RECORD'S OWN SUMMARY
  LANGUAGE, not new interpretations. Accepted -- with the standing caution from Section 3.
```

## 5. Review Point 3 — Did The Families Stay Suspicion Lenses?

```text
FINDING: YES.

  Nothing is sorted into L1-L7. No branch is assigned to a lens, no lens is exhaustive, and several branches sit under
  more than one. They are used as ways of READING, not as bins. No lens is treated as ruled out by having been named,
  and none is treated as established by having been applied.
```

## 6. Review Point 4 — Residual Wording Risk (the important one)

```text
FINDING: ONE SLIP OCCURRED AND WAS CORRECTED. TWO SENTENCES REMAIN THE STRONGEST IN THE DOCUMENT AND SHOULD BE WATCHED.

  THE SLIP: v2.48 as first written said, of a platform-sensitive statistic, that it "is not structure -- it is a
  threshold artifact, and the record says so." That is a CONCLUSION, not a vulnerability. It was refused and replaced
  with vulnerability language ("this scan does not conclude that explanation").

  WHY THIS MATTERS MORE THAN A LINE EDIT: this is the SECOND time in three slices that a document drifted toward the
  thing it was enthusiastic about. In v2.43 an anti-machinery document labelled its own instruments "TEST". In v2.48 an
  anti-claim scan reached for an anti-claim CLAIM. THE DRIFT ALWAYS RUNS TOWARD THE DOCUMENT'S OWN THESIS. It is not a
  positive-structure bias or a negative-structure bias -- it is a CONCLUSION bias, and it is indifferent to sign.
  Rescuing a negative is the same error as rescuing a residual, performed by people who feel more virtuous while doing
  it.

  REMAINING STRONG SENTENCES (accepted, but flagged for v2.50):
    - L6: "Not one of them examined anything." This is a claim about our own documents, and the documents say it about
      themselves. It is supportable AS A STATEMENT ABOUT THE RECORD. It must not be allowed to widen into "the
      programme was worthless" -- which would be a claim about VALUE, not about evidence, and is out of scope.
    - L1: "The record contains no sentence that answers them." Supportable as a reading of the record. It must not
      become "therefore there is nothing to answer."

  NO OTHER WORDING RISK FOUND. The scan is otherwise disciplined: it says COULD, MAY BE, VULNERABLE TO -- not IS.
```

## 7. Review Point 5 — Is The Negative Reading Legitimate But Not Concluded?

```text
FINDING: YES, AND THE REFUSAL TO CONCLUDE IS THE BEST THING IN THE SCAN.

  v2.48 states that "the frozen record can mostly be reread as proxy / confound vulnerability" would be a LEGITIMATE
  outcome -- and then explicitly declines to conclude it, on the ground that the scan was performed by the same
  programme whose vocabulary it accuses, and that A SELF-ACCUSATION IS NOT MORE TRUSTWORTHY THAN A SELF-CONGRATULATION.

  THIS REVIEW ENDORSES THAT REASONING AND ADDS ONE HONESTY QUESTION:
    IS THE NEGATIVE BEING REACHED BECAUSE IT IS TRUE, OR BECAUSE THE PROGRAMME IS TIRED?
    Twenty slices of vocabulary is exhausting, and "it was all confounded anyway" is a comfortable exit that ends the
    work while feeling rigorous. The scan's own §6 asks this question about itself. Asking it is not the same as
    answering it, and v2.50 must ask it again, and answer it in writing.

  NEGATIVE READING REMAINS LEGITIMATE BUT NOT CONCLUDED. The locks are unmoved: no proxy is ruled out, no confound is
  controlled, nothing is explained.
```

## 8. Review Point 6 — Was "What Survives The Proxies" Avoided?

```text
FINDING: YES. The forbidden framing does not appear, and the scan names it as forbidden in its own text. No residual is
rescued, no proxy is ruled out, and proxy INSUFFICIENCY is explicitly NOT read as evidence for structure -- which is
the subtler half of the same rule, and the scan gets it right.
```

## 9. Review Point 7 — Enough Falsification Pressure To Justify A Closure?

```text
FINDING: YES -- AND v2.48 IS THE FIRST SLICE IN ROUGHLY TWENTY THAT COULD HAVE BEEN WRONG.

  Every slice from v2.24 to v2.47 was safe, careful, and unable to be wrong about anything. v2.48 made a claim about
  the record that a reviewer could refute -- AND A PART OF IT WAS REFUTED (Section 6). That is not a defect of the
  scan. IT IS THE EVIDENCE THAT THE DIRECTION HAS TEETH. A slice that can be corrected is a slice that was saying
  something.

  THE PRESSURE IT ADDED IS REAL AND IT IS ALREADY DELIVERED: the vulnerability is broad, it is documented in the
  record's own words, and it is not confined to one branch. That is what the proxy route was selected to produce.

  THEREFORE: ANOTHER SCAN IS NOT WARRANTED. A second rereading would find the same vulnerability in different words --
  suspicion-vocabulary expansion, which is the vocabulary loop with a minus sign. Conclusion type B is REFUSED for that
  reason. What remains worth writing is ONE synthesis that states what the rereading branch did and did not establish,
  and closes it.

  ONE UNDER-SUSPECTED ITEM, FLAGGED FOR THE SYNTHESIS: L2 (intensity / contrast). v2.48 flags it precisely because the
  record is QUIET about it. The review agrees the silence is EXPOSURE -- and warns that silence cuts both ways: "we
  never discussed it" must never become "it explains everything". Absence of examination is not presence of
  explanation.
```

## 10. Conclusion And Recommendation

```text
CONCLUSION TYPE: A -- SAFE FOR ONE DOCS-ONLY PROXY / CONFOUND REREADING SYNTHESIS / CLOSURE SLICE.

  Not B (another docs-only rereading scan): REFUSED. It would restate the same vulnerability in new words. No
  implementation or artifact is authorized under B or under anything else.
  Not C -- yet. C remains live, and Section 11 states what would trigger it.

PRIMARY:  A -- one docs-only proxy / confound rereading SYNTHESIS / CLOSURE slice.
FALLBACK: C -- HOLD / PAUSE the Brainvision falsification branch. Legitimate and honest at any moment.

REASON: v2.47 planned the question, v2.48 performed the bounded scan and delivered the suspicion pressure it was
selected to deliver. The next step should SYNTHESIZE AND CLOSE this rereading branch -- not keep expanding suspicion
vocabulary indefinitely.

IF A IS SELECTED:

  v2.50  PROXY / CONFOUND REREADING SYNTHESIS / CLOSURE  (DOCS-ONLY)

  v2.50 MUST: synthesize what the rereading branch (v2.46-v2.49) accomplished and did NOT accomplish; carry the
  no-numeric-value discipline unchanged; keep the negative reading LEGITIMATE BUT NOT CONCLUDED; answer, in writing,
  whether the negative is being reached because it is true or because the programme is tired; and keep L2's silence as
  EXPOSURE, never as explanation.

  v2.50 MUST NOT: claim proxy / confound EXPLANATION, RULE-OUT, CONTROL, or VALIDATION; claim candidate survival or
  implementation readiness; recompute, rerun, or re-measure anything; reinterpret raw data; sharpen a restatement into
  a characterisation the record does not itself make (Section 3); define any metric, threshold, descriptor, control,
  recognition rule, fixture, test, artifact, or implementation.

v2.49 opens nothing. The operator chooses.
```

## 11. What Would Trigger C (stated in advance)

```text
- v2.50 finds itself restating v2.48 rather than closing it (suspicion-vocabulary expansion);
- v2.50 cannot answer the tiredness question honestly, or answers it and the answer is "tired";
- any further step requires recomputation, a metric, a threshold, or a recognition rule to be meaningful;
- the operator judges that the rereading's suspicion pressure is sufficient and nothing further is owed.

ANY ONE OF THESE MEANS THE BRANCH HAS DELIVERED WHAT IT HAD, and HOLD / pause is the honest outcome -- not a defeat.
```

## 12. Allowed And Forbidden Language

**Allowed** — and nothing stronger:

```text
null remains live
artifact remains live
proxy/confound remains live
generic chroma proxy remains live
BY residual remains unresolved
candidate survival must not be structurally inevitable
no recognition rule is defined
no validation follows
no artifact is authorized
no implementation is authorized
frozen evidence is reread only as suspicion pressure
the record may be vulnerable to proxy/confound rereading
negative reading remains legitimate but not concluded
```

**Forbidden** — in any wording, as claim SHAPES rather than exact strings:

```text
control-collapse detected       control-collapse ruled out      controls passed
candidate survived              structure detected              null rejected
artifact ruled out              proxy ruled out                 confound controlled
descriptor validated            geometry validated              metric validated
screen ready                    runtime ready                   memory ready
vision achieved                 Brainvision sees
threshold artifact concluded    proxy explanation proven
```

Paraphrases are the same forbidden move. Standing: **"what survives the proxies"** is forbidden as a FRAMING; **"the
record is explained"** is forbidden (it *may be vulnerable* to a rereading); and — added here — **"it was all
confounded anyway"** is forbidden, because it is a conclusion wearing the costume of humility.

## 13. Forbidden Drift Register

```text
- a SCAN becoming a CONCLUSION. The slip happened once already and was corrected (Section 6).
- CONCLUSION BIAS, in either direction: rescuing a negative is the same error as rescuing a residual.
- restatement being SHARPENED into characterisation the record does not itself make.
- L2's silence ("intensity / contrast barely discussed") becoming "intensity / contrast explains it".
- proxy INSUFFICIENCY being read as evidence FOR structure.
- any proxy being read as ruled out, controlled, addressed, or dissolved by having been named.
- L6 widening from "these documents examined nothing" into "the programme was worthless" -- a claim about VALUE, not
  about evidence, and out of scope.
- the negative reading being ADOPTED without the tiredness question being answered in writing.
- ANOTHER rereading scan. It would be the vocabulary loop with a minus sign.
- a REVIEW becoming an AUTHORIZATION; v2.50 becoming a formality; jumping to an artifact "to settle it".
```

## 14. Non-Claim Interpretation

```text
WHAT v2.49 MAY ESTABLISH (and only this):
  - that v2.48 stayed bounded (frozen-evidence rereading; no recomputation, measurement, evidence fields, or raw-data
    reinterpretation; lenses kept as lenses; forbidden framing avoided);
  - that one wording slip toward a conclusion occurred and was corrected, and that the underlying failure mode is
    CONCLUSION BIAS, indifferent to sign;
  - that the negative reading remains LEGITIMATE BUT NOT CONCLUDED;
  - that the scan delivered real suspicion pressure -- and that the honest next step is ONE synthesis / closure, not
    another scan;
  - a recommendation (A primary; C fallback), and nothing more.

WHAT IT DOES NOT ESTABLISH:
  not that proxies DO account for the record          not that they DO NOT
  not that any proxy is ruled out, controlled, or addressed
  not that any residual exists                        not that none does
  not a metric, threshold, descriptor, control, or recognition rule
  not validation    not closure    not readiness    not vision    not an artifact    not implementation

Reviewing a rereading examines no phenomenon. Every lock stays False. Frozen evidence remains reread ONLY as suspicion
pressure. The v2.22 BY/chroma question remains UNRESOLVED and possibly unanswerable.
```

## 15. Verdict

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

CONCLUSION TYPE: A -- one docs-only proxy/confound rereading SYNTHESIS / CLOSURE slice (another scan REFUSED; artifact
and implementation REFUSED; C / HOLD-pause live)
OUTCOME_LABEL: BRAINVISION_PROXY_CONFOUND_REREADING_REVIEW_ONLY
```

v2.49 is a docs-only review. It finds that v2.48 **stayed bounded** (frozen-evidence rereading only; no recomputation,
rerun, re-measurement, evidence fields, or raw-data reinterpretation; no numeric value quoted; lenses used as ways of
reading rather than as bins; the forbidden *"what survives the proxies"* framing avoided; proxy insufficiency correctly
**not** read as evidence for structure); that **one wording slip toward a conclusion occurred and was corrected** — a
platform-sensitive statistic briefly declared a threshold artifact — and that the underlying failure mode is
**CONCLUSION BIAS, indifferent to sign**: rescuing a negative is the same error as rescuing a residual, and this is the
second slice in three to drift toward its own thesis; that the **negative reading remains legitimate but not
concluded**, with the scan's refusal to conclude (a self-accusation is not more trustworthy than a self-congratulation)
endorsed and extended by one further honesty question — *is the negative being reached because it is true, or because
the programme
is tired?*; and that v2.48 **delivered real suspicion pressure** and is **the first slice in roughly twenty that could
have been wrong** — part of it *was* refuted, which is evidence the direction has teeth. It therefore **refuses another
scan** (suspicion-vocabulary expansion is the vocabulary loop with a minus sign), concludes **TYPE A**, and recommends
one separately gated docs-only next slice (**v2.50 proxy / confound rereading synthesis / closure**), which must answer
the tiredness question in writing, keep L2's silence as **exposure** rather than explanation, and claim no proxy
explanation, rule-out, control, validation, candidate survival, or implementation readiness. **C (HOLD / pause) remains
live** with pre-stated triggers. All claim locks and the frozen verdict **HOLD** are preserved and unmoved.

## 16. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_PROXY_CONFOUND_REREADING_REVIEW_v2.49.md
(new, docs-only, untracked; over the accepted v2.48 edge "d691f10 docs(research): scan frozen evidence proxy
confounds").

Verify that this review:
- is docs-only and authorizes NOTHING: no implementation, no artifact, no fixture design, no tests, no fixture data,
  no arrays / images, no descriptors, no coordinates, no metrics, no scores, no thresholds, no formulas, no generation
  rules, no schemas / data shapes, no decision rules, no arrival rules, no evidence / confidence / classification /
  validation / pass-fail / survival / positive-structure fields, NO RECOGNITION RULE, no screen / runtime / memory
  paths, no classifier / neural work, no real clips, no vision or readiness claims; RECOMPUTES NOTHING, RERUNS NOTHING,
  RE-MEASURES NOTHING, and reinterprets no raw data; adds no §0 pointer and no tags;
- grounds itself in v2.46, v2.47, and v2.48 and in v2.48's acceptance constraints (docs-only; no recomputation /
  reruns / re-measurement; no quoted numeric values; no new machinery; NO threshold-artifact conclusion; negative
  reading legitimate but not concluded; P6 preserved; all locks False; verdict HOLD);
- poses the central review question verbatim;
- reviews all seven required points: (1) frozen-evidence rereading only; (2) no recomputation / new measurements / new
  evidence fields / raw-data reinterpretation; (3) each proxy / confound family kept as a SUSPICION LENS only; (4) any
  residual wording risk where vulnerability could be mistaken for conclusion; (5) the negative reading legitimate but
  NOT concluded; (6) the "what survives proxies" framing avoided; (7) whether falsification pressure justifies one
  synthesis / closure slice or a HOLD / pause;
- reports the corrected wording slip (a platform-sensitive statistic briefly declared a threshold artifact) and names
  the underlying failure mode as CONCLUSION BIAS, indifferent to sign -- rescuing a negative is the same error as
  rescuing a residual;
- selects a conclusion from the allowed types (A one docs-only synthesis / closure slice; B another docs-only rereading
  scan with no implementation / artifact authorized; C HOLD / pause) -- selects A, REFUSES B as suspicion-vocabulary
  expansion, and keeps C live with pre-stated triggers;
- recommends exactly ONE separately gated docs-only next slice (v2.50 proxy / confound rereading synthesis / closure)
  which must synthesize what the branch did and did not accomplish, answer the tiredness question in writing, keep L2's
  silence as EXPOSURE not explanation, and claim NO proxy / confound explanation, rule-out, control, validation,
  candidate survival, or implementation readiness;
- fixes the allowed and forbidden language, including "threshold artifact concluded" and "proxy explanation proven" as
  forbidden, and "it was all confounded anyway" as a forbidden conclusion wearing the costume of humility;
- preserves the locks and verdict (Section 15), including verdict = HOLD.

Flag any recomputation, rerun, re-measurement, or raw-data reinterpretation; any numeric value; any proxy treated as
ruled out, controlled, addressed, or dissolved; any residual rescued; any "what survives the proxies" framing; any
proxy insufficiency read as evidence FOR structure; any lens converted into a bin, criterion, test, or gate; any
negative reading CONCLUDED rather than held legitimate-but-unconcluded; any claim about the programme's VALUE rather
than about the record's evidence; any recommendation of implementation, an artifact, or another scan; or any claim-lock
/ verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
All claim locks False, and the frozen verdict **HOLD**, are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Proxy / Confound Rereading Review v2.49. Docs-only review over the accepted v2.48 edge.
Recomputes nothing, reruns nothing, re-measures nothing, reinterprets no raw data, quotes no numeric value; opens no
implementation lane, no tests, no artifact, and no fixture design; defines no descriptor / coordinate / metric / score
/ threshold / formula / control / recognition rule / validation criterion; opens no classifier / neural / screen /
real-clip / runtime / memory path; makes no vision or readiness claim; authorizes nothing and is not self-authorizing.
Finds v2.48 bounded (frozen-evidence rereading only; lenses kept as ways of reading, not bins; forbidden framing
avoided; proxy insufficiency correctly not read as evidence for structure; no numeric value quoted, a discipline to be
carried forward); reports the corrected wording slip in which a platform-sensitive statistic was briefly declared a
threshold artifact, and names the underlying failure mode as CONCLUSION BIAS, INDIFFERENT TO SIGN — the drift always
runs toward the document's own thesis, and rescuing a negative is the same error as rescuing a residual, performed by
people who feel more virtuous while doing it; flags the two strongest remaining sentences (L6 "not one of them examined
anything"; L1 "the record contains no sentence that answers them") as supportable statements ABOUT THE RECORD that must
not widen into claims about the programme's VALUE or about there being nothing to answer; endorses the scan's refusal
to conclude the negative and adds the honesty question the synthesis must answer in writing — is the negative being
reached because it is TRUE, or because the programme is TIRED; finds that v2.48 delivered real suspicion pressure and
is the first slice in roughly twenty that COULD HAVE BEEN WRONG, part of it having in fact been refuted, which is
evidence the direction has teeth; refuses another scan as suspicion-vocabulary expansion (the vocabulary loop with a
minus sign); concludes TYPE A and recommends one separately gated docs-only next slice (v2.50 proxy / confound
rereading synthesis / closure) which must claim no proxy explanation, rule-out, control, validation, candidate
survival, or implementation readiness, and must keep L2's silence as EXPOSURE and never as explanation; keeps C (HOLD /
pause) live with pre-stated triggers. Keeps prior BY / color / chroma work FROZEN EVIDENCE, the BY/chroma scaffold
REPORTING LANGUAGE ONLY, the null-first role scaffold PAUSED HELD, the anti-inevitability branch CLOSED as
non-authorizing review work, and the v2.22 question UNRESOLVED and possibly unanswerable; preserves all claim locks and
the frozen verdict HOLD; outcome label BRAINVISION_PROXY_CONFOUND_REREADING_REVIEW_ONLY; no `§0` pointer added; no
tags.*

# TORMENT Brainvision Synthetic Falsification Design Scan v2.21

## 1. Status / Scope

**DOCS-ONLY synthetic falsification design SCAN.** This is a comparison note only. It opens **no** code, **no** tests,
**no** runtime, and **no** integration lane; it authorizes **no** implementation, **no** validation, **no** readiness
claim, and **no** capability claim, and it is not corrective. It sits over the accepted v2.20 edge (`a06580a`) and
changes none of the accepted files. It executes the Area C recommended by v2.20: a docs-only comparison of synthetic
falsification design questions.

**v2.21 scans synthetic falsification design questions only.** It defines and compares candidate offline synthetic
falsification questions to identify which would be most useful next while preserving every non-claim boundary. It does
**not** design implementation yet: no fixture family is built, no descriptor / coordinate / metric is defined, and no
question is turned into code. It compares questions and makes a recommendation; the recommendation is
**operator-gated and non-self-authorizing** — any recommended future implementation must be separately planned,
Codex-reviewed, and operator-approved.

**v2.21 authorizes no implementation, validation, readiness, or capability claim.** It introduces and authorizes
**no** descriptor, coordinate system, numeric geometry, metric, equation, threshold, control metric, pass/fail gate,
validation, screen analysis, real clip, camera / live / sensor / streaming path, runtime path, memory path, prompt /
context / action / render-body / autonomy contact, classifier (form B), or neural encoder (form C). It makes **no**
production vision claim, **no** "Brainvision sees" claim, **no** temporal-order claim, and **no** descriptor-validity /
geometry-validity / screen-readiness / memory-readiness / runtime-readiness / integration-readiness claim. The flat
opponent-field symbolic branch stays **HELD**. Everything stays offline under `research/brainvision/` +
`tests/research/`, HELD per v0.6. **HOLD / HELD means held for analysis and claim control — not abandoned.**

```text
flat_field_validated                        = False
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

## 2. Current Brainvision Position

```text
OLDER BY / COLOR / CHROMA EVIDENCE (UNRESOLVED localization evidence, NOT closure):
  Prior work localized the residual difficulty -- the color-structure descriptor's response is spectrum-explained, the
  directional / per-channel-spectral axis is entangled, the by_std residual was a pool-composition artifact, and a
  best-effort matched search could not close all cheap-baseline shortcuts at once (the "proxy wall" stands; no unique
  color-structure advantage shown; forms B/C CLOSED). This is where the unresolved SCIENTIFIC pressure sits. It is
  useful localization evidence, NOT proof of closure, and must not be treated as solved. FROZEN EVIDENCE.

FLAT OPPONENT-FIELD SYMBOLIC BRANCH (PAUSED scaffold evidence, NOT validation):
  v2.6-v2.18 built a generated/reporting fixture layer + a minimal guarded static symbolic representation artifact +
  eight boundary-hardening reviews, then paused HELD (v2.19-v2.20 kept it paused). Useful, bounded, non-authorizing
  scaffold with a documented non-claim wall. Validates NOTHING; its symbolic identities are NOT geometry truth.

OPEN CLAIMS: none. flat_field_validated = False; all claim locks False; verdict HOLD. The programme sits at a clean
pause with unresolved BY/color/chroma pressure and a paused non-validating scaffold, and asks: what is the next safest,
most useful SYNTHETIC FALSIFICATION QUESTION?
```

## 3. Candidate Falsification Question Comparison

Each candidate is evaluated across the required dimensions: what the question would examine; what it would not
authorize; primary benefit; primary risk; boundary risk; required guardrails; recommended now?; operator choice
needed before follow-up.

```text
====================================================================================================================
CANDIDATE A -- OPPONENT-FIELD SYMBOLIC-TO-SYNTHETIC CONSISTENCY QUESTION
  question : can a future synthetic fixture set preserve A-F symbolic identities while remaining generated/reporting-
             only and NON-validating?
  examine  : whether the paused scaffold can INFORM a future synthetic fixture design without being treated as
             validation.
  not auth : does NOT build fixtures; does NOT expand the scaffold; adopts no descriptor / coordinate / metric; opens
             no screen / runtime / memory / vision.
  benefit  : reuses the v2.6-v2.18 scaffold discipline without expanding it into descriptors or geometry.
  risk     : accidentally treating the symbolic representation as a SOURCE OF GEOMETRY TRUTH.
  boundary : MEDIUM-HIGH -- "consistency with the scaffold" invites reading the scaffold as ground truth.
  guard    : scaffold stays non-validating (v2.18 wall); consistency is reporting-only; no geometry / descriptor.
  now?     : NO -- ties the next question to the paused scaffold rather than to the unresolved scientific pressure.
  choice   : if pursued, a docs-only consistency-question note, separately approved.

====================================================================================================================
CANDIDATE B -- BY / CHROMA RESIDUAL ISOLATION QUESTION (docs-first)                                    [PREFERRED]
  question : can a future synthetic fixture SEPARATE BY-axis residual behavior from generic color/chroma proxy effects
             WITHOUT claiming closure?
  examine  : a sharper synthetic falsification question around the UNRESOLVED residual localization (BY-axis vs generic
             proxy), reconnecting scaffold discipline to the original failure.
  not auth : does NOT re-run old fixtures; adopts no metric / descriptor / coordinate; claims no closure; opens no
             screen / runtime / memory / vision; a QUESTION only.
  benefit  : HIGHEST-VALUE -- points at where the unresolved SCIENTIFIC pressure actually is (the proxy wall / BY-axis
             residual), and asks a falsifiable, reporting-only separation question without reviving prior failures as
             solved.
  risk     : reviving prior fixture-metric FAILURES as if solvable-with-one-tweak.
  boundary : MEDIUM -- "separate BY residual from proxy" is close to a metric; must be posed as a reporting-only
             DISTINCTION question, not a scored separation.
  guard    : prior evidence stays FROZEN (no re-run / no closure claim); the separation is a reporting-only DISTINCTION,
             NOT a metric or a validation; wording per v2.17; generated-vs-validated separation preserved.
  now?     : YES (PREFERRED) -- reconnects the paused-scaffold discipline to the real open pressure.
  choice   : the operator approves opening a docs-only v2.22 BY/chroma residual-isolation QUESTION-DESIGN note; no code.

====================================================================================================================
CANDIDATE C -- DIRECTIONAL / STRUCTURAL CONTRAST QUESTION
  question : can future reporting-only fixtures DISTINGUISH symbolic structural-contrast cases from null/control
             scaffolds WITHOUT adopting measured geometry?
  examine  : a synthetic question around directional / structural contrast while avoiding coordinates, metrics,
             descriptors, and temporal-order claims.
  not auth : adopts no coordinate / metric / descriptor; makes no temporal-order claim; opens no screen / runtime /
             memory / vision.
  benefit  : may sharpen the "structure before descriptor" question.
  risk     : "directional" and "structural" DRIFTING into geometry, topology, or metric claims.
  boundary : HIGH -- these terms are the closest to geometry of any candidate; drift risk is the highest here.
  guard    : structure stays SYMBOLIC (v2.11/v2.17); no coordinate / topology / metric; distinction is reporting-only.
  now?     : NO -- highest boundary risk, and the directional/structural axis is exactly the entangled one prior work
             could not cleanly separate; premature as a question without the residual-isolation framing (B) first.
  choice   : if pursued, a docs-only structural-question note with firm wording guards, separately approved.

====================================================================================================================
CANDIDATE D -- GUARD-HARDENING FALSIFICATION QUESTION
  question : can future synthetic cases be designed to test BOUNDARY-DISCIPLINE failure modes rather than visual
             capability?
  examine  : whether future fixtures can BREAK the boundary guards (not whether they validate vision).
  not auth : tests guards only; adopts no descriptor / coordinate / metric / validation; opens no screen / runtime /
             memory / vision.
  benefit  : SAFEST from claim drift -- it targets discipline, not capability.
  risk     : becoming too governance-heavy and NOT advancing the scientific question.
  boundary : LOW -- it is about guard discipline, not vision; least claim risk.
  now?     : NO -- v2.13 already reviewed mutation/guard failure modes; another guard-focused question is low scientific
             yield right now.
  choice   : if pursued, folds into a future implementation-hardening plan (v2.20 Area A / Path A), separately approved.

====================================================================================================================
CANDIDATE E -- PAUSE SYNTHETIC DESIGN AND DO QUESTION-FRAMING ONLY (fallback)
  question : what EXACT failure would a future synthetic falsifier need to expose?
  examine  : whether even synthetic design is premature, and the next slice should SHARPEN the research question before
             proposing any fixture families.
  not auth : proposes no fixture family; adopts nothing; opens no screen / runtime / memory / vision.
  benefit  : avoids premature fixture design; forces the target failure to be named first.
  risk     : over-documenting without moving toward a testable falsification.
  boundary : LOW -- pure framing; minimal claim risk.
  now?     : FALLBACK -- recommend ONLY IF the scan concludes the target failure is still TOO VAGUE to design a
             question against; otherwise Candidate B already names a concrete enough target.
  choice   : if pursued, a docs-only target-failure framing note, separately approved.
====================================================================================================================
```

## 4. Cross-Candidate Risks

Risks that span the candidates, each to be refused regardless of which is chosen:

```text
- SYMBOLIC SCAFFOLD MISTAKEN FOR GEOMETRY TRUTH: the A-F symbolic identities are names, not measured geometry (v2.18
  wall); no candidate may treat scaffold consistency as ground truth (esp. Candidate A).
- RESIDUAL EVIDENCE MISTAKEN FOR CLOSURE: the BY/color/chroma localization is unresolved, not closed; no candidate may
  claim closure or treat the proxy wall as solved (esp. Candidate B).
- SYNTHETIC FIXTURES MISTAKEN FOR VALIDATION: a reporting-only fixture question validates nothing; generation is not
  validation and does not imply descriptor validity.
- GUARD-HARDENING REPLACING SCIENTIFIC FALSIFICATION: discipline questions (Candidate D) must not crowd out the
  scientific question; governance is not a result.
- QUESTION-FRAMING BECOMING ENDLESS DOCUMENTATION: framing (Candidate E) must converge on a NAMED target failure, not
  recurse indefinitely.
- ADDING MATH BEFORE THE TARGET FAILURE IS CLEAR: no "more math" / metric / descriptor until the target failure a
  falsifier must expose is named; the question comes before the machinery.
- DRIFTING TOWARD SCREEN / RUNTIME / MEMORY / VISION: no candidate may open a screen / real-clip / camera / live /
  runtime / memory / classifier / neural / vision path; Brainvision stays offline / quarantined.
```

## 5. Recommendation

```text
RECOMMEND: CANDIDATE B -- BY / chroma residual isolation question (docs-first).

Reason: the flat opponent-field symbolic branch is now safely paused, and the OLDER BY/color/chroma route is where the
unresolved SCIENTIFIC pressure actually sits (the proxy wall stands; the BY-axis residual and directional/per-channel
entanglement were localized but never closed). The next useful move is a docs-first synthetic falsification QUESTION
that asks whether a future fixture could SEPARATE BY-axis residual behavior from generic color/chroma proxy effects --
posed as a reporting-only DISTINCTION, not a scored separation, and claiming NO closure. This reconnects the
scaffold-discipline lessons to the original failure without reviving prior fixture-metric failures as solved, and it
names a concrete enough target that framing-only (Candidate E) is not yet necessary.

SECONDARY (fallback) option: CANDIDATE E -- question-framing only -- IF the scan concludes the target failure is still
TOO VAGUE to design a question against. If, on operator review, "separate BY residual from proxy" cannot be stated as a
crisp reporting-only distinction, frame the exact target failure first (E) before B.

NOT recommended now: Candidate A (ties the question to the paused scaffold rather than the open pressure; scaffold-as-
truth risk); Candidate C (highest boundary/geometry drift risk; the directional/structural axis is the entangled one --
premature without B's residual framing); Candidate D (guard failure modes already reviewed in v2.13; low scientific
yield now). No descriptor / coordinate / metric / validation / screen / real-clip / runtime / memory / classifier (B) /
neural (C) / vision work is recommended or authorized by this scan.
```

## 6. Operator Decision Needed

```text
The next ACTUAL slice must be chosen by the OPERATOR. This scan makes a clear recommendation (Candidate B, with
Candidate E as a fallback if the target failure is still too vague) but is NOT self-authorizing: it starts no work,
proposes no fixture family, and commits to no candidate. Whichever candidate the operator picks becomes a SEPARATE,
docs-first slice with its own boundary, Codex review, and (for anything beyond docs) explicit operator approval. Until
then, the flat opponent-field symbolic branch stays PAUSED HELD, the prior BY/color/chroma work stays FROZEN EVIDENCE,
and Brainvision stays offline / quarantined.
```

## 7. Verdict

```text
verdict                                      = HOLD
flat_field_validated                         = False
first_pass_structure_validity_claim_allowed  = False
temporal_claim_allowed                       = False
descriptor_validity_claim_allowed            = False
geometry_validity_claim_allowed              = False
screen_readiness_claim_allowed               = False
runtime_readiness_claim_allowed              = False
memory_readiness_claim_allowed               = False
integration_readiness_claim_allowed          = False
vision_claim_allowed                         = False

OUTCOME_LABEL: BRAINVISION_SYNTHETIC_FALSIFICATION_DESIGN_SCAN_ONLY
```

v2.21 is a docs-only synthetic falsification design scan. It summarizes the current position (older BY/color/chroma
work as unresolved localization evidence; the flat opponent-field symbolic branch as paused scaffold evidence; no open
claim), compares five candidate falsification question families (A symbolic-to-synthetic consistency, B BY/chroma
residual isolation, C directional/structural contrast, D guard-hardening, E question-framing only) across what each
would examine and not authorize, its benefit, primary and boundary risks, required guardrails, whether to recommend
now, and the operator choice needed, addresses the cross-candidate risks, and recommends **Candidate B** (with
Candidate E as a fallback). It designs no implementation, proposes no fixture family, selects no work, and is not
self-authorizing. All claim locks and the frozen verdict **HOLD** are preserved and unmoved.

## 8. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_SYNTHETIC_FALSIFICATION_DESIGN_SCAN_v2.21.md
(new, docs-only, untracked; over the accepted v2.20 edge a06580a).

Verify that this scan:
- is docs-only and authorizes NO implementation, NO test expansion, NO fixture design, NO validation, NO readiness
  claim, and NO capability claim (no code / tests / schema, no torment_service/, no runtime, no memory, no camera /
  live / sensor / screen-capture / streaming, no real clips, no pixels / images); keeps form B (classifier) and form C
  (neural) CLOSED; opens no screen-analysis / numeric-geometry; changes no field / value / family / lock; keeps the
  flat opponent-field symbolic branch HELD; designs NO implementation yet;
- frames the central question as WHAT is the next safest and most useful synthetic falsification QUESTION for
  Brainvision given the localized-but-unresolved BY/color/chroma routes and the paused non-validating symbolic scaffold;
- summarizes the current position: older BY/color/chroma work as UNRESOLVED localization evidence (proxy wall stands;
  forms B/C closed; not closure), the flat opponent-field symbolic branch as PAUSED scaffold evidence (not validation;
  symbolic identities are not geometry truth), and no open claim;
- compares the five required candidates (A opponent-field symbolic-to-synthetic consistency; B BY/chroma residual
  isolation; C directional/structural contrast; D guard-hardening falsification; E pause synthetic design and do
  question-framing only) across ALL required dimensions (what the question would examine; what it would not authorize;
  primary benefit; primary risk; boundary risk; required guardrails; whether recommended now; what operator choice
  would be needed before follow-up), with each candidate's allowed/forbidden scope respected;
- preserves the required lessons: synthetic falsification is safer than screen/real-clip/runtime/memory/classifier/
  neural/vision work; synthetic falsification still does not imply validation; reporting-only fixture generation does
  not imply descriptor validity; symbolic scaffold identity does not imply geometry truth; BY/color/chroma residual
  evidence remains useful but unresolved; prior fixture-metric failures must not be treated as solved; the next
  implementation (if any) needs a sharper falsification question before code; no "more math" until the target failure
  is clear;
- addresses the cross-candidate risks (symbolic scaffold mistaken for geometry truth; residual evidence mistaken for
  closure; synthetic fixtures mistaken for validation; guard-hardening replacing scientific falsification; question-
  framing becoming endless documentation; adding math before the target failure is clear; drifting toward screen/
  runtime/memory/vision);
- RECOMMENDS Candidate B unless a stronger reason is found, explains why, and mentions Candidate E as a fallback if the
  target failure remains too vague; recommends NO descriptor / coordinate / metric / validation / screen / real-clip /
  runtime / memory / neural / classifier / vision work;
- states that the next actual slice must be chosen by the OPERATOR and that the scan is not self-authorizing;
- preserves the locks and verdict (Section 7): flat_field_validated = False; first_pass_structure_validity_claim_allowed
  = False; temporal_claim_allowed = False; descriptor_validity_claim_allowed = False; geometry_validity_claim_allowed =
  False; screen_readiness_claim_allowed = False; runtime_readiness_claim_allowed = False; memory_readiness_claim_allowed
  = False; integration_readiness_claim_allowed = False; vision_claim_allowed = False; verdict = HOLD; outcome label
  BRAINVISION_SYNTHETIC_FALSIFICATION_DESIGN_SCAN_ONLY; interprets HOLD/HELD as held for analysis, not abandoned;
- adds NO §0 pointer and NO tags, and makes no vision / "Brainvision sees" / descriptor-validity / geometry-validity /
  temporal-order / readiness claim.

Flag any candidate recommended in a way that authorizes work without separate operator approval, any prior failed path
treated as solved / auto-resumable, any scaffold cited as geometry truth or validation, any reporting-only distinction
posed as a scored metric / separation, any adopted descriptor / coordinate / metric / validation / pass-fail rule, any
screen / real-clip / camera / live / runtime / memory authorization, any classifier (B) / neural (C) opening, any
"Brainvision sees" / vision / descriptor-validity / geometry-validity / temporal-order / readiness / capability claim,
or any claim-lock / verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`flat_field_validated = False`, all claim locks False, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Synthetic Falsification Design Scan v2.21. Docs-only design scan. Opens no implementation
lane, no test expansion, and no fixture design; opens no classifier / neural / screen / real-clip / runtime / memory
work; adopts no descriptor / coordinate system / numeric geometry / metric / equation / threshold / control metric /
pass-fail rule; changes no field / value / family / lock; compares five candidate synthetic falsification question
families (A symbolic-to-synthetic consistency, B BY/chroma residual isolation, C directional/structural contrast, D
guard-hardening, E question-framing only) across what each would examine and not authorize, its benefit, primary and
boundary risks, guardrails, recommend-now, and operator-choice-needed; preserves the frozen-evidence, scaffold-not-
geometry-truth, and question-before-math lessons; recommends Candidate B (Candidate E a fallback); keeps the flat
opponent-field symbolic branch PAUSED HELD and prior BY/color/chroma work FROZEN EVIDENCE; is not self-authorizing and
leaves the next slice to the operator; preserves all claim locks and the frozen verdict HOLD; makes no vision /
"Brainvision sees" / descriptor-validity / geometry-validity / temporal-order / readiness claim; outcome label
BRAINVISION_SYNTHETIC_FALSIFICATION_DESIGN_SCAN_ONLY; no `§0` pointer added; no tags.*

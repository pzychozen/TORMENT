# TORMENT Brainvision Flat Opponent-Field Protocol Wording Hardening Review v2.17

## 1. Status / Scope

**DOCS-ONLY protocol wording hardening REVIEW.** This is a wording review only. It opens **no** code, **no** tests,
**no** runtime, and **no** integration lane; it authorizes **no** implementation, **no** expansion, **no** validation,
**no** readiness claim, and **no** capability claim, and it is not corrective. It sits over the accepted v2.16 edge
(`4ae6156`) and changes none of the accepted files.

**v2.17 reviews wording only.** After v2.10-v2.16 fixed the substantive boundaries (representation, vocabulary,
null/control, mutation, protocol semantics, family identity, non-claim invariants), a residual risk remains at the
level of *language*: even when code and docs preserve every lock, casual phrasing around `protocol_ok`, `breaches=[]`,
`fixture_represented`, `representation_validated`, `outcome_label`, `HOLD`, "symbolic representation", and "guarded"
can imply success, proof, validation, readiness, capability, visual structure, or "Brainvision sees". This review
defines safe wording and forbidden wording patterns. It reviews language; it changes no field, term, family, value, or
behavior.

**v2.17 authorizes no implementation, expansion, validation, readiness, or capability claim.** It introduces and
authorizes **no** descriptor, coordinate system, numeric geometry, metric, null/control metric, equation, threshold,
control metric, pass/fail gate, validation, closure, screen analysis, real clip, camera / live / sensor / streaming
path, runtime path, memory path, prompt / context / action / render-body / autonomy contact, classifier (form B), or
neural encoder (form C), and it authorizes **no** family or vocabulary expansion. It makes **no** production vision
claim, **no** "Brainvision sees" claim, **no** temporal-order claim, and **no** descriptor-validity /
geometry-validity / screen-readiness / memory-readiness / runtime-readiness / integration-readiness claim. Everything
stays offline under `research/brainvision/` + `tests/research/`, HELD per v0.6. **HOLD / HELD means held for analysis
and claim control — not abandoned.**

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

## 2. Why Wording Drift Matters

Every substantive boundary in this arc can be preserved in the code and still be defeated in a sentence. Wording is the
last, softest surface: a field that means "boundary compliance" gets written up as "passed", a family that is a name
gets called a "class", a checker that withholds claims gets described as "verified". None of that requires touching a
value or a lock — it is the *prose* that carries the claim, and prose travels further than code (into summaries,
commit messages, decks, conversations).

Wording drift is especially dangerous because it is deniable and cumulative: any single loose phrase looks harmless,
but a habit of calling `protocol_ok=True` "success", `breaches=[]` "clean", and `F_null_control_fields` "the control"
adds up to an implied result nobody authorized. This review fixes, per term, the safe wording that preserves the
non-authorizing boundary, the forbidden wording that breaches it, why the forbidden wording is dangerous, and the
replacement rule future docs must follow — so the discipline lives in the language as well as the code.

## 3. Term-by-Term Wording Review

```text
For each term: SAFE wording (preserves the boundary), FORBIDDEN wording (implies validation / success / readiness /
evidence / vision), the DANGER, and the REPLACEMENT rule.

--------------------------------------------------------------------------------------------------------------------
protocol_ok
  safe      : "boundary-compliant", "the checker detected no boundary breach", "protocol_ok = True (boundary compliance)".
  forbidden : "passed", "passed validation", "succeeded", "verified", "proven", "correct".
  danger    : turns a boundary check into a validation / proof of the world.
  replace   : say the object is boundary-compliant among KNOWN checks; never "passed / succeeded / verified".

breaches=[]
  safe      : "no checker-defined breach detected", "no KNOWN boundary breach".
  forbidden : "clean", "no issues", "no risk", "nothing wrong", "all good".
  danger    : reads an empty KNOWN-breach list as absence of UNKNOWN risk or as a positive result.
  replace   : bound it to the KNOWN checks; never imply completeness or risk-freedom.

verdict=HOLD
  safe      : "held for analysis and claim control", "HOLD (not abandoned, not passed)".
  forbidden : "passed", "failed", "validated", "ready", "abandoned", "done".
  danger    : converts a claim-control state into a pass / fail / validation / capability state.
  replace   : use HOLD as claim-control language only; state it stays HOLD until separately re-decided.

outcome_label
  safe      : "conservative boundary classification", "names where the artifact sits on the boundary".
  forbidden : "result", "grade", "capability class", "performance", "readiness result", "score".
  danger    : reads a boundary label as a capability / performance / readiness grade.
  replace   : describe the label as a boundary classification, never a result or grade.

fixture_represented=True
  safe      : "the family is represented as a scaffold identity only", "named as a static symbolic object".
  forbidden : "the fixture is real", "detected", "present", "built", "valid", "recognized".
  danger    : reads "named" as "visually real / detected / built / valid".
  replace   : say "represented as scaffold identity only"; never "real / detected / built / valid".

representation_validated=False
  safe      : "the representation is not validated", "representation_validated stays explicitly False".
  forbidden : "pending validation", "not yet validated" (implying it will be), "awaiting a run".
  danger    : implies validation is a scheduled next step of THIS artifact (it is not).
  replace   : state it is False and that validation would be a separate, later, separately-preregistered protocol.

flat_field_validated=False
  safe      : "the flat opponent-field is not validated by this artifact", "stays explicitly False".
  forbidden : "not yet validated", "validation in progress", "close to validated".
  danger    : implies the artifact is a step toward flat-field validation (it is not).
  replace   : state it is False and that no validation exists or is authorized.

claim locks
  safe      : "anti-claim constraints", "each False forbids the corresponding claim".
  forbidden : "tested and absent", "evidence that X is not there", "controls", "gates".
  danger    : inverts an anti-claim guard into false evidence of a tested absence.
  replace   : say a False lock WITHHOLDS a claim; never that it TESTS or EVIDENCES anything.

adoption flags
  safe      : "anti-adoption constraints", "each False records non-adoption".
  forbidden : "tested and rejected", "evaluated", "controls", "gates".
  danger    : reads non-adoption as a measured / decided rejection.
  replace   : say a False adoption flag records non-adoption only.

authorization guards
  safe      : "anti-authorization constraints", "each False withholds authorization".
  forbidden : "capability", "controls", "gates", "proof", "cleared".
  danger    : reads a withheld authorization as evidence of capability or a passed gate.
  replace   : say a False guard WITHHOLDS authorization; never that it grants or evidences capability.

symbolic representation
  safe      : "static symbolic representation", "a naming of structure", "symbolic/static only".
  forbidden : "symbolic detector", "representation of the image", "encodes the structure", "captures the field".
  danger    : reads a naming as a detector / encoder / capture of measured content.
  replace   : say it NAMES structure symbolically; never "detects / encodes / captures".

guarded representation
  safe      : "non-authorizing guarded representation", "guarded = anti-claim guarded".
  forbidden : "verified representation", "certified", "validated", "safe-to-integrate".
  danger    : reads "guarded" as "certified / validated / integration-safe".
  replace   : say "guarded" means anti-claim / boundary-guarded; never certified / validated / integration-safe.

static symbolic object layer
  safe      : "a static symbolic object layer (labels only, no data)".
  forbidden : "an object model", "a scene layer", "a feature layer", "a detection layer".
  danger    : reads a label layer as an object / feature / detection model.
  replace   : say "static symbolic object layer of labels only"; never object / feature / detection model.

A-F family coverage
  safe      : "coverage of six symbolic scaffold NAMES", "the six families are named".
  forbidden : "visual coverage", "we cover the visual cases", "complete scaffold", "the six classes".
  danger    : reads coverage of six names as visual completeness or a class system.
  replace   : say "six named scaffold identities"; never "visual coverage / classes / complete".

null_control
  safe      : "the symbolic null/control ROLE", "a control BY NAMING only" (per v2.12).
  forbidden : "the control passed", "null control succeeded", "the baseline", "the negative control".
  danger    : reads a symbolic role as a passed/failed validation control or scored baseline.
  replace   : say null_control is a symbolic role; never "passed / succeeded / baseline / negative control".
--------------------------------------------------------------------------------------------------------------------
```

## 4. Forbidden Phrase Register

Compact register of phrase classes future docs / reviews must AVOID:

```text
"passed validation" / "validated fixture" / "verified geometry" / "detected boundary" / "detected gradient" /
"screen-ready" / "runtime-ready" / "memory-ready" / "vision-ready" / "Brainvision sees" / "control passed" /
"null control succeeded" / "proof" / "evidence of visual structure" / "descriptor works" / "coordinates are implicit" /
"metric-free validation" / "symbolic detector" / "object category" / "segmentation category" / "classifier label" /
"neural target" / "complete visual scaffold" / "closed" / "ready for integration".
```

## 5. Safe Phrase Register

Compact register of PREFERRED wording patterns:

```text
"boundary-compliant" / "non-authorizing" / "symbolic/static only" / "fixture represented as scaffold identity only" /
"generated-vs-validated separation preserved" / "no checker-defined breach detected" / "claim locks remain false" /
"held for analysis and claim control" / "does not validate geometry" / "does not imply descriptor validity" /
"does not imply screen/runtime/memory readiness" / "does not support a vision claim".
```

## 6. Review Rule for Future Docs

```text
- Never say "passed" unless explicitly discussing pytest/software tests AS software tests -- never as validation of
  opponent structure, geometry, or vision.
- Never call A-F families visual classes, object categories, segmentation categories, classifier labels, or neural
  targets; they are fixed symbolic scaffold identities (v2.15).
- Never call protocol_ok = True "success" outside BOUNDARY COMPLIANCE; never call breaches = [] "clean" / "no risk".
- Never describe null_control as a passed or failed control, a baseline, or a negative control (v2.12).
- Never describe the symbolic representation as a detector, descriptor, geometry, encoder, or vision.
- Use HELD / HOLD as claim-control language, not capability language; HOLD is not "not-yet-ready" and not "done".
- When in doubt, prefer the Safe Phrase Register (Section 5) and append an explicit non-claim ("does not validate /
  does not imply readiness / does not support a vision claim").
```

## 7. Expansion Recommendation

```text
Recommendation: REMAIN HELD.

This is a wording review; it changes no code, field, value, family, or lock, and it authorizes nothing. Future
hardening or any wording ENFORCEMENT (e.g. a lint rule, a docstring change, a wording checklist wired into the
artifact) must be SEPARATELY planned (docs-first), reviewed by Codex, and operator-approved, naming the exact change,
what it must never become, and how every claim lock and the generated-vs-validated separation are preserved. No
descriptor / coordinate / metric / validation / screen / real-clip / runtime / memory / classifier (B) / neural (C) /
vision work is recommended or authorized here. Held for analysis and claim control -- not abandoned.
```

## 8. Possible Next Slices

Docs-first candidates only; **none opened, none authorized, and none recommended for implementation here**. This review
recommends **no** direct descriptor, coordinate, metric, validation, screen, real-clip, runtime, memory, neural,
classifier, or vision work. Up to three possible docs-first directions the operator could choose from:

```text
A. v2.18 REPRESENTATION EXPANSION READINESS HOLD REVIEW (docs-only)
   Review, on paper, whether the boundary-review family (v2.10-v2.17) is now SATURATED and the branch should stay HELD
   as-is, and what a FUTURE bounded expansion plan would minimally have to contain before it could even be considered.
   Adopts nothing; authorizes no expansion.

B. v2.18 SYMBOLIC ARTIFACT IMPLEMENTATION HARDENING PLAN (docs-only)
   Plan, on paper only, whether any additional check_protocol guard is warranted (e.g. a deny-list refinement) given
   the v2.13 mutation classes -- as a PROPOSAL requiring separate operator approval and Codex review before any code.
   Adopts nothing; writes no code; authorizes no implementation.

C. v2.18 BRANCH CLOSURE / PAUSE SYNTHESIS (docs-only)
   Synthesize, on paper, that the flat opponent-field symbolic-representation line and its boundary-review family are
   complete for now, and pause the branch HELD -- recording the state so it can be resumed later without re-derivation.
   Adopts nothing; authorizes nothing; opens no new lane.
```

## 9. Verdict

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

OUTCOME_LABEL: FLAT_OPPONENT_FIELD_PROTOCOL_WORDING_HARDENING_REVIEW_ONLY
```

v2.17 is a docs-only protocol wording hardening review. It records, for each protocol term and phrase around the v2.9
artifact, the safe wording, the forbidden wording, why the forbidden wording is dangerous, and the replacement rule;
it provides a forbidden phrase register and a safe phrase register; it states the wording rules for future docs; and
it recommends the branch REMAIN HELD. It changes no code, field, value, family, or lock, and it adopts, expands, and
relaxes nothing. All claim locks and the frozen verdict **HOLD** are preserved and unmoved.

## 10. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_FLAT_OPPONENT_FIELD_PROTOCOL_WORDING_HARDENING_REVIEW_v2.17.md
(new, docs-only, untracked; over the accepted v2.16 edge 4ae6156).

Verify that this review:
- is docs-only and authorizes NO implementation, NO test expansion, NO family / vocabulary expansion, NO validation,
  NO readiness claim, and NO capability claim (no code / tests / schema, no torment_service/, no runtime, no memory, no
  camera / live / sensor / screen-capture / streaming, no real clips, no pixels / images); keeps form B (classifier)
  and form C (neural) CLOSED; opens no screen-analysis / numeric-geometry; changes no field / value / family / lock;
- frames the central question as WHAT wording is safe and what wording must be avoided so the symbolic representation
  artifact remains non-authorizing;
- reviews wording around every required term/phrase (protocol_ok; breaches=[]; verdict=HOLD; outcome_label;
  fixture_represented=True; representation_validated=False; flat_field_validated=False; claim locks; adoption flags;
  authorization guards; symbolic representation; guarded representation; static symbolic object layer; A-F family
  coverage; null_control) with: safe wording, forbidden wording, why it is dangerous, and a replacement rule;
- explicitly REJECTS the required forbidden phrases ("passed validation" / "validated fixture" / "verified geometry" /
  "detected boundary" / "detected gradient" / "screen-ready" / "runtime-ready" / "memory-ready" / "vision-ready" /
  "Brainvision sees" / "control passed" / "null control succeeded" / "proof" / "evidence of visual structure" /
  "descriptor works" / "coordinates are implicit" / "metric-free validation" / "symbolic detector" / "object category" /
  "segmentation category" / "classifier label" / "neural target" / "complete visual scaffold" / "closed" / "ready for
  integration") and recommends the required safe wording ("boundary-compliant" / "non-authorizing" / "symbolic/static
  only" / "fixture represented as scaffold identity only" / "generated-vs-validated separation preserved" / "no
  checker-defined breach detected" / "claim locks remain false" / "held for analysis and claim control" / "does not
  validate geometry" / "does not imply descriptor validity" / "does not imply screen/runtime/memory readiness" / "does
  not support a vision claim");
- states the review rules for future docs (never say "passed" except for software tests as software tests; never call
  A-F visual classes / object / segmentation categories / classifier labels / neural targets; never call protocol_ok =
  True success outside boundary compliance; never call null_control a passed/failed control; never describe the
  symbolic representation as a detector / descriptor / geometry / vision; use HELD/HOLD as claim-control language);
- recommends the branch REMAIN HELD; requires any wording enforcement to be separately planned + Codex-reviewed +
  operator-approved; lists up to three docs-first next slices (v2.18 representation expansion readiness HOLD review /
  symbolic artifact implementation hardening plan / branch closure-pause synthesis); recommends NO descriptor /
  coordinate / metric / validation / screen / real-clip / runtime / memory / neural / classifier / vision work;
- preserves the locks and verdict (Section 9): flat_field_validated = False; first_pass_structure_validity_claim_allowed
  = False; temporal_claim_allowed = False; descriptor_validity_claim_allowed = False; geometry_validity_claim_allowed =
  False; screen_readiness_claim_allowed = False; runtime_readiness_claim_allowed = False; memory_readiness_claim_allowed
  = False; integration_readiness_claim_allowed = False; vision_claim_allowed = False; verdict = HOLD; outcome label
  FLAT_OPPONENT_FIELD_PROTOCOL_WORDING_HARDENING_REVIEW_ONLY; interprets HOLD/HELD as held for analysis, not abandoned;
- adds NO §0 pointer and NO tags, and makes no vision / "Brainvision sees" / descriptor-validity / geometry-validity /
  temporal-order / readiness claim.

Flag any recommended wording that implies validation / success / pass-fail / readiness / evidence / proof / visual
structure / descriptor validity / geometry truth / screen / runtime / memory / classifier-neural readiness / vision,
any adopted descriptor / coordinate / metric / pass-fail rule, any recommendation to expand, or any claim-lock /
verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`flat_field_validated = False`, all claim locks False, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Flat Opponent-Field Protocol Wording Hardening Review v2.17. Docs-only wording review. Opens
no implementation lane, no test expansion, and no family / vocabulary expansion; opens no classifier / neural / screen
/ real-clip / runtime / memory work; adopts no descriptor / coordinate system / numeric geometry / metric / equation /
threshold / control metric / pass-fail rule; changes no field / value / family / lock; reviews wording around every
required protocol term/phrase with safe wording, forbidden wording, danger, and replacement rule; provides a forbidden
phrase register and a safe phrase register; states the review rules for future docs; recommends the branch REMAIN HELD;
preserves all claim locks and the frozen verdict HOLD; makes no vision / "Brainvision sees" / descriptor-validity /
geometry-validity / temporal-order / readiness claim; outcome label FLAT_OPPONENT_FIELD_PROTOCOL_WORDING_HARDENING_REVIEW_ONLY;
no `§0` pointer added; no tags.*

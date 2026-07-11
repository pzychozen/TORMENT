# TORMENT Brainvision Flat Opponent-Field Family Identity Audit v2.15

## 1. Status / Scope

**DOCS-ONLY A-F family identity preservation AUDIT.** This is an audit note only. It opens **no** code, **no** tests,
**no** runtime, and **no** integration lane; it authorizes **no** implementation, **no** test expansion, **no** family
expansion, **no** validation, and **no** readiness claim, and it is not corrective. It sits over the accepted v2.14
edge (`e99a661`) and changes none of the accepted files.

**v2.15 audits A-F family identity only.** It examines the identity of the six fixture families introduced in v2.6 and
represented symbolically in v2.9 — `A_uniform_opponent_patches`, `B_adjacent_opponent_patches`, `C_gradient_fields`,
`D_edge_discontinuity_fields`, `E_region_field_separation_fixtures`, `F_null_control_fields` — and asks whether each
can remain a fixed symbolic scaffold identity without drifting into a hidden visual class, segmentation category,
screen object, validation fixture, descriptor family, expandable ontology, classifier label, neural target, or
evidence category. It audits identity; it changes no family, adds none, renames none, and removes none.

**v2.15 authorizes no implementation, test expansion, family expansion, or readiness claim.** It introduces and
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

## 2. Why Family Identity Drift Matters

The six A-F families are a fixed, closed symbolic scaffold: named categories of *what a flat opponent-field fixture
could conceptually be*, nothing more. But a named family is an inviting shell. The very words — "uniform patches",
"gradient fields", "edge/discontinuity fields", "region-field separation" — are the vocabulary of image analysis, and
the default reading of "we have six families" in a perception context is "we have six visual classes we can detect,
segment, or classify." That default is the drift: a scaffold identity silently becomes a visual class, a segmentation
category, a classifier label, or a validation group, and the closed set of six names becomes an *ontology* someone
feels free to extend.

The danger needs no code. It is enough for a reader or a later doc to treat "family A" as "the uniform-region class we
recognize" for the scaffold to carry a hidden vision, descriptor, or validation claim; and it is enough to add a
"family G" for the closed, canonical, exactly-six set to become an open ontology that the whole v2.9 identity
enforcement was built to prevent. This audit fixes, per family, the narrow allowed identity, the specific drift to
refuse, a safe-use invariant, and a conservative risk level — and forbids both the reinterpretation and the expansion.

## 3. A-F Family Identity Audit

```text
For each family: allowed identity (the narrow symbolic scaffold identity from v2.6/v2.9), forbidden drift, safe-use
rule, and a conservative drift-risk level (Low / Medium / High = how easily it is misread as geometry, validation, or
vision progress).

--------------------------------------------------------------------------------------------------------------------
A_uniform_opponent_patches                                                                             [risk: HIGH]
  identity : names the SCAFFOLD CATEGORY "a single uniform opponent patch, symbolically"; a fixed name, not a class.
  drift    : -> a "valid uniform VISUAL REGION" (a recognized/segmented uniform area that is measured or validated).
  safe     : A names a symbolic scaffold category; it recognizes no region, measures none, and validates none.

B_adjacent_opponent_patches                                                                            [risk: HIGH]
  identity : names the SCAFFOLD CATEGORY "neighboring opponent patches, symbolically"; a fixed name.
  drift    : -> COORDINATE-ADJACENT SCREEN PATCHES (positioned tiles on a screen with an adjacency computation).
  safe     : B names a symbolic scaffold category; adjacency is a NAME, with no coordinate, position, screen, or tile.

C_gradient_fields                                                                                      [risk: HIGH]
  identity : names the SCAFFOLD CATEGORY "a smooth opponent transition, symbolically"; a fixed name.
  drift    : -> a MEASURED NUMERIC GRADIENT FIELD (an array of values with a computed slope).
  safe     : C names a symbolic scaffold category; "gradient" is a NAME, with no value, array, slope, or derivative.

D_edge_discontinuity_fields                                                                            [risk: HIGH]
  identity : names the SCAFFOLD CATEGORY "a sharp opponent boundary, symbolically"; a fixed name.
  drift    : -> DETECTED EDGE / DISCONTINUITY EVIDENCE (a found, located, or scored edge).
  safe     : D names a symbolic scaffold category; nothing is detected, located, scored, or proven.

E_region_field_separation_fixtures                                                                     [risk: HIGH]
  identity : names the SCAFFOLD CATEGORY "local region vs global field, symbolically"; a fixed name.
  drift    : -> SEGMENTATION or OBJECT-REGION SEPARATION (a proven split of measured content into objects/regions).
  safe     : E names a symbolic scaffold category; "separation" is a NAME, proving no split and measuring no content.

F_null_control_fields                                                                                  [risk: MEDIUM]
  identity : names the SCAFFOLD CATEGORY "the null / control role, symbolically" (per v2.12); a fixed name.
  drift    : -> a VALIDATION CONTROL / BASELINE / PASS-FAIL NULL EVIDENCE (F used to validate or score A-E).
  safe     : F names a symbolic scaffold role; it adjudicates nothing, scores nothing, and validates nothing (v2.12).
--------------------------------------------------------------------------------------------------------------------
```

## 4. Cross-Family Drift Risks

Individual families can each stay disciplined yet combine into an implied capability. The dangerous combinations, each
to be refused:

```text
- A + B          -> reads as a hidden COORDINATE LATTICE (uniform tiles placed and indexed with adjacency). Refuse:
                    both are symbolic scaffold names; together they carry no coordinate, index, position, or lattice.
- B + D          -> reads as EDGE-DETECTION / ADJACENCY EVIDENCE (neighbors with a detected boundary between them).
                    Refuse: both symbolic; no edge is detected and no adjacency is computed or measured.
- C + D          -> reads as NUMERIC GRADIENT / DISCONTINUITY MEASUREMENT (a slope and a jump magnitude). Refuse: both
                    symbolic; no slope, magnitude, or numeric change exists.
- E + F          -> reads as SEGMENTATION VALIDATION / CONTROL LOGIC (a segmented split scored against a null control).
                    Refuse: both symbolic; nothing is segmented, scored, or adjudicated (E names a relation, F a role).
- A-F completeness -> reads as VISUAL COMPLETENESS (the six families cover "all the visual cases"). Refuse: covering
                    A-F means six symbolic categories are NAMED, not that any visual space is covered or measured.
- A-F labels      -> reads as CLASSIFIER LABELS (the six as output classes of a classifier). Refuse: the labels are
                    fixed symbolic names, not classes; form B (classifier) stays CLOSED.
- A-F labels      -> reads as NEURAL TRAINING TARGETS (the six as supervision targets). Refuse: the labels train
                    nothing; form C (neural) stays CLOSED.
- A-F coverage    -> reads as VALIDATION COVERAGE (the six as a validated test matrix). Refuse: coverage of the six
                    NAMES is not validation of anything; nothing is tested, scored, or proven.
```

## 5. Family Non-Implication Invariants

Invariant rules over the family identities. Each is a **non-implication** that must hold regardless of any future
step:

```text
F1. family EXISTENCE does NOT imply visual-class existence.
F2. A-F COVERAGE does NOT imply visual completeness.
F3. family LABELS do NOT imply descriptor categories.
F4. family LABELS do NOT imply classifier / neural targets.
F5. family LABELS do NOT imply validation coverage.
F6. F-family PRESENCE does NOT validate A-E (or anything).
F7. fixture family IDENTITY is SCAFFOLD IDENTITY ONLY (a fixed symbolic name, never a measured / detected / valid class).
```

Any reading, doc, or artifact that violates an invariant above has left the accepted boundary and is inadmissible.

## 6. Expansion Boundary

```text
- NO new family may be added. The set is exactly, canonically six (A-F); v2.9 identity enforcement makes an extra or
  missing family a protocol breach, and this audit reaffirms that the six are closed. Any NEW family would require a
  SEPARATE docs-first plan, a Codex review, and explicit operator approval naming the exact addition, what it must
  never become, and how every claim lock and the generated-vs-validated separation are preserved.
- NO existing family may be renamed or broadened into a screen, descriptor, metric, coordinate, validation, classifier,
  neural, segmentation, or vision category. The canonical family_id / family_label / components / relations are fixed
  (v2.9); broadening any of them is a canonical-drift protocol breach and, at the docs level, an inadmissible
  reinterpretation.
- No descriptor / coordinate / metric / validation / screen / real-clip / runtime / memory / classifier (B) / neural
  (C) / vision work is recommended or authorized here. The branch stays HELD -- held for analysis and claim control,
  not abandoned.
```

## 7. Possible Next Slices

Docs-first candidates only; **none opened, none authorized, and none recommended for implementation here**. This audit
recommends **no** direct descriptor, coordinate, metric, validation, screen, real-clip, runtime, memory, neural,
classifier, or vision work. Up to three possible docs-first directions the operator could choose from:

```text
A. v2.16 SYMBOLIC REPRESENTATION NON-CLAIM INVARIANTS REVIEW (docs-only)
   Consolidate, on paper, the full set of non-claim invariants across v2.10-v2.15 into one reviewable list, so the
   "representation / protocol / vocabulary / null-control / family = NOT validation / descriptor / coordinate / metric
   / screen / vision" discipline is stated in one place. Adopts nothing; builds nothing.

B. v2.16 PROTOCOL WORDING HARDENING REVIEW (docs-only)
   Review, on paper, the exact wording of the protocol outputs and docstrings for any phrasing that could be read as
   validation / capability, and define wording invariants -- WITHOUT changing any field, value, or behavior. Adopts
   nothing; changes no code.

C. v2.16 REPRESENTATION EXPANSION READINESS HOLD REVIEW (docs-only)
   Review, on paper, whether the review family (v2.10-v2.15) is now saturated and the branch should stay HELD as-is,
   and what a FUTURE bounded expansion plan would minimally have to contain before it could even be considered.
   Adopts nothing; authorizes no expansion.
```

## 8. Verdict

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

OUTCOME_LABEL: FLAT_OPPONENT_FIELD_FAMILY_IDENTITY_AUDIT_ONLY
```

v2.15 is a docs-only A-F family identity preservation audit. It records, for each of the six fixture families, the
allowed symbolic scaffold identity, the forbidden drift (into a visual class, screen object, descriptor / coordinate
class, segmentation, validation control, classifier / neural target, or vision claim), a safe-use invariant, and a
conservative risk level; it addresses the dangerous cross-family combinations; it states the family non-implication
invariants and the expansion boundary (exactly six, closed, canonical, un-renamed, un-broadened); and it recommends
the branch REMAIN HELD. It adopts, expands, and relaxes nothing. All claim locks and the frozen verdict **HOLD** are
preserved and unmoved.

## 9. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_FLAT_OPPONENT_FIELD_FAMILY_IDENTITY_AUDIT_v2.15.md
(new, docs-only, untracked; over the accepted v2.14 edge e99a661).

Verify that this audit:
- is docs-only and authorizes NO implementation, NO test expansion, NO family expansion, NO vocabulary expansion, NO
  validation, and NO readiness claim (no code / tests / schema, no torment_service/, no runtime, no memory, no camera /
  live / sensor / screen-capture / streaming, no real clips, no pixels / images); keeps form B (classifier) and form C
  (neural) CLOSED; opens no screen-analysis / numeric-geometry;
- frames the central question as WHETHER the A-F families can remain fixed symbolic scaffold identities without
  becoming screen-object categories, visual classes, descriptor categories, validation groups, or expandable ontology;
- audits EXACTLY the six required families (A_uniform_opponent_patches, B_adjacent_opponent_patches, C_gradient_fields,
  D_edge_discontinuity_fields, E_region_field_separation_fixtures, F_null_control_fields) with: allowed symbolic
  scaffold identity, forbidden drift, safe-use rule, and a conservative risk level;
- explicitly addresses the required per-family drift examples (A -> valid uniform visual region; B -> coordinate-adjacent
  screen patches; C -> measured numeric gradient field; D -> detected edge/discontinuity evidence; E -> segmentation /
  object-region separation; F -> validation control / baseline / pass-fail null evidence) and the cross-family risks
  (A+B coordinate lattice; B+D edge-detection/adjacency evidence; C+D numeric gradient/discontinuity measurement; E+F
  segmentation validation/control; A-F completeness -> visual completeness; A-F labels -> classifier labels; A-F labels
  -> neural training targets; A-F coverage -> validation coverage);
- states the family non-implication invariants (F1-F7: family existence != visual class; A-F coverage != visual
  completeness; labels != descriptor categories; labels != classifier/neural targets; labels != validation coverage;
  F presence != validates A-E; family identity is scaffold identity only);
- states the expansion boundary: NO new family without a separate docs-first plan + Codex review + operator approval;
  NO existing family renamed or broadened into screen / descriptor / metric / coordinate / validation / classifier /
  neural / segmentation / vision categories;
- recommends the branch REMAIN HELD; lists up to three docs-first next slices (v2.16 non-claim invariants review /
  protocol wording hardening review / representation expansion readiness HOLD review); recommends NO descriptor /
  coordinate / metric / validation / screen / real-clip / runtime / memory / neural / classifier / vision work;
- preserves the locks and verdict (Section 8): flat_field_validated = False; first_pass_structure_validity_claim_allowed
  = False; temporal_claim_allowed = False; descriptor_validity_claim_allowed = False; geometry_validity_claim_allowed =
  False; screen_readiness_claim_allowed = False; runtime_readiness_claim_allowed = False; memory_readiness_claim_allowed
  = False; integration_readiness_claim_allowed = False; vision_claim_allowed = False; verdict = HOLD; outcome label
  FLAT_OPPONENT_FIELD_FAMILY_IDENTITY_AUDIT_ONLY; interprets HOLD/HELD as held for analysis, not abandoned;
- adds NO §0 pointer and NO tags, and makes no vision / "Brainvision sees" / descriptor-validity / geometry-validity /
  temporal-order / readiness claim.

Flag any family renamed / broadened / added, any family treated as a visual class / screen object / descriptor category
/ segmentation / classifier label / neural target / validation group, any adopted descriptor / coordinate / numeric
geometry / metric / equation / threshold / control metric / pass-fail rule, any validation / segmentation claim, any
screen / real-clip / camera / live / runtime / memory authorization, any classifier (B) / neural (C) opening, any
"Brainvision sees" / vision / descriptor-validity / geometry-validity / temporal-order / readiness claim, any
recommendation to expand, or any claim-lock / verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`flat_field_validated = False`, all claim locks False, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Flat Opponent-Field Family Identity Audit v2.15. Docs-only audit. Opens no implementation
lane, no test expansion, and no family / vocabulary expansion; opens no classifier / neural / screen / real-clip /
runtime / memory work; adopts no descriptor / coordinate system / numeric geometry / metric / equation / threshold /
control metric / pass-fail rule; audits the six A-F fixture families for drift into visual class / screen object /
descriptor category / coordinate-geometry / segmentation / validation control / classifier label / neural target /
vision claim and records allowed scaffold identity, forbidden drift, safe-use rule, and conservative risk per family
plus the cross-family risks; fixes the family non-implication invariants and the exactly-six closed-canonical expansion
boundary; recommends the branch REMAIN HELD; preserves all claim locks and the frozen verdict HOLD; makes no vision /
"Brainvision sees" / descriptor-validity / geometry-validity / temporal-order / readiness claim; outcome label
FLAT_OPPONENT_FIELD_FAMILY_IDENTITY_AUDIT_ONLY; no `§0` pointer added; no tags.*

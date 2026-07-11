# TORMENT Brainvision BY/Chroma Synthetic Fixture ROLES Findings v2.26

## 1. Status / Scope

**REPORTING-ONLY implementation + findings.** v2.26 implements the artifact conditionally allowed by the v2.25
implementation-boundary review, in exactly the Section-4 shape and with none of the Section-5 forbidden shape: a
**deterministic, static, symbolic, offline research-only** report of the **six** v2.24 BY/chroma conceptual family
ROLES, guarded by a conservative canonical protocol checker.

**v2.26 generates no fixtures.** It generates no fixture data, no fixture instances, and no fixture bank. It adopts and
defines **no** descriptor, coordinate system, numeric geometry, metric, equation, threshold, score, weight, ratio,
distance, pass/fail gate, acceptance criterion, expected output, validation, closure, classifier (form B) feature,
neural (form C) encoding, real clip, screen / camera / live / sensor / streaming path, runtime path, or memory path. It
makes **no** production vision claim, **no** "Brainvision sees" claim, **no** temporal-order claim, and **no**
descriptor-validity / geometry-validity / screen-readiness / memory-readiness / runtime-readiness /
integration-readiness claim. Everything stays offline under `research/brainvision/` + `tests/research/`, HELD per v0.6.
**HOLD / HELD means held for analysis and claim control — not abandoned.**

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

role_validity_claim_allowed                 = False
residual_localization_claim_allowed         = False
proxy_resolved_claim_allowed                = False
metric_separation_claim_allowed             = False
closure_claim_allowed                       = False
validation_claim_allowed                    = False

descriptor_adopted                          = False
coordinate_system_adopted                   = False
metric_adopted                              = False
threshold_adopted                           = False
scoring_adopted                             = False
pass_fail_gate_adopted                      = False

verdict                                      = HOLD
```

**No `§0` pointer; no tags.**

## 2. Boundary Preserved

```text
PRIMARY QUESTION (v2.22 Formulation A) -- in force, and UNANSWERED by this slice:
  "Can future synthetic design distinguish BY-axis residual behavior from generic chroma proxy effects without adopting
   metrics or closure claims?"

MANDATORY NON-CLAIM CONSTRAINT (v2.22 Formulation C) -- in force:
  "Residual localization must not imply descriptor validity."

v2.23 fixed the conceptual-only design boundary. v2.24 proposed the six finite conceptual ROLES (A BY-dominant chroma
residual; B generic chroma proxy; C matched non-BY chroma; D BY/chroma entangled; E fixture-family artifact; F null /
reporting-boundary). v2.25 CONDITIONALLY allowed a v2.26 reporting-only role artifact, modeled on the accepted v2.9
symbolic pattern (deterministic builder + conservative canonical check_protocol), IF AND ONLY IF its five mandatory
guard conditions were met.

ALSO PRESERVED:
  - REPORTING-ONLY: "distinguish / isolate / separate / matched / entangled / artifact / null" are CONCEPTUAL /
    REPORTING language ONLY. "Distinguish" means "report whether a distinction can be POSED", never "measure how
    separated".
  - PRIOR EVIDENCE: prior BY / color / chroma work stays FROZEN UNRESOLVED localization evidence, not solved proof.
  - FLAT-FIELD SCAFFOLD: the paused flat opponent-field symbolic branch informs DISCIPLINE only; it validates nothing
    here, and it stays PAUSED HELD.
```

## 3. What Was Implemented (three files; nothing else)

```text
research/brainvision/by_chroma_synthetic_fixture_roles_v2_26.py
  - build_by_chroma_synthetic_fixture_roles_v2_26() -> deterministic static symbolic report.
  - check_protocol(report=None) -> {"protocol_ok": bool, "breaches": [...]}, conservative and CANONICAL.
  - stdlib only (`__future__` only); no torment_service; no numeric / imaging / capture library anywhere.

tests/research/test_brainvision_by_chroma_synthetic_fixture_roles_v2_26.py
  - locks provenance, the six-role identity, the symbolic field allow-list, generated-not-validated, every lock / flag /
    guard present-and-False in a CLOSED group, the clean-report green, 50 mutation probes that must each flip
    protocol_ok False, named-breach assertions for the canonical gate, the wording gate, and the closed-group gate,
    and determinism.

docs/TORMENT_BRAINVISION_BY_CHROMA_SYNTHETIC_FIXTURE_ROLES_FINDINGS_v2.26.md  (this file)
```

Each role object carries **only** symbolic / reporting fields:

```text
role_id | role_label | conceptual_purpose | reporting_focus | non_claim_constraints | forbidden_interpretations |
safe_reporting_language | role_generated = True | role_validated = False
```

`reporting_focus` is drawn from a **closed label set** (`by_residual_reporting_focus`, `generic_proxy_confound_focus`,
`non_by_chroma_focus`, `entanglement_possibility_focus`, `artifact_suspicion_focus`, `null_reporting_boundary_focus`).
It is a NAME, never a quantity.

## 4. The Six Roles As Reported (names, not measurements)

```text
====================================================================================================================
ROLE                                   ID  REPORTING FOCUS (label only)         GENERATED  VALIDATED
--------------------------------------------------------------------------------------------------------------------
A_BY_dominant_chroma_residual_role     A   by_residual_reporting_focus          True       False
B_generic_chroma_proxy_role            B   generic_proxy_confound_focus         True       False
C_matched_non_BY_chroma_role           C   non_by_chroma_focus                  True       False
D_BY_chroma_entangled_role             D   entanglement_possibility_focus       True       False
E_fixture_family_artifact_role         E   artifact_suspicion_focus             True       False
F_null_reporting_boundary_role         F   null_reporting_boundary_focus        True       False
====================================================================================================================

Role D is encoded HONESTLY: entanglement is a conceptual POSSIBILITY and a reason the v2.22 question may be
UNANSWERABLE -- never a quantity, never a degree, never a finding.
Role E is encoded HONESTLY: the fixtures-may-manufacture-the-effect suspicion is permanent; the case family may never
be declared free of artifacts.
Role F is encoded HONESTLY: it is an ANTI-CLAIM SCAFFOLD (v2.12 N1-N6), never evidence, never a baseline, and never a
null that succeeded.
```

## 5. The Protocol Checker (conservative; canonical; boundary-compliance only)

`check_protocol` returns `protocol_ok = True` with `breaches = []` **only** for a clean report. It marks a breach —
and, if uncertain, marks a breach — on any of:

```text
- a missing role, an extra role, or a wrong role name (exactly the six v2.24 role ids, no more, no fewer);
- role_validated = True anywhere; role_generated not True; flat_field_validated = True;
- a verdict other than HOLD (a PASS verdict is a breach); a non-conservative / drifted outcome label; a bad version;
- a MISSING, EXTRA, or NON-FALSE key in `claim_locks`, `adoption_flags`, or `authorization_guards`. All three groups
  are CLOSED: an unknown key breaches even when its value is False, because an extra False key silently widens the
  lock / adoption / authorization surface. Breach names: `claim_lock_missing:<key>` / `claim_lock_extra:<key>` /
  `claim_lock_true:<key>`, and likewise `adoption_flag_*` and `authorization_guard_*`;
- a forbidden CONCRETE FIELD (coordinate, pixel, grid, vector, array, distance, magnitude, formula, equation,
  threshold, score, metric, weight, ratio, classifier, neural, embedding, descriptor, image, screen, clip, camera,
  runtime, memory, pass-fail, numeric, geometry, data / fixture-data field) on a role object;
- any numeric value, container value, nested structure, or non-string list entry inside a role;
- a reporting_focus outside the closed label set; an empty or missing reporting list;
- CANONICAL DRIFT: any deviation of the top-level note or of a role's id / label / purpose / focus / constraints /
  forbidden interpretations / safe language from the builder's approved static report;
- FORBIDDEN WORDING in any string: validation / closure / readiness wording ("is validated", "closure achieved",
  "is ready"...), claim forms ("proxy is controlled", "not an artifact", "null control passed", "residual is
  distinct", "descriptor is valid", "separation score"...), and screen / runtime / memory / classifier / neural /
  vision wording ("screen path", "runtime path", "memory path", "classifier label", "neural target",
  "brainvision sees", "real clip", "pixel data"...).
```

The wording gate is not decorative: during construction it **rejected the artifact's own first draft**, because a role
string phrased a denial as "a scored or measured separation" and tripped the `measured separation` guard. The draft was
rephrased, not the guard. A test now asserts the canonical report is free of every forbidden phrase, so the guard
cannot be quietly hollowed out to accommodate future text.

**Greenness means BOUNDARY COMPLIANCE ONLY (v2.14).** `protocol_ok = True` is not validation, not correctness, not
distinguishability, not descriptor validity, not closure, and not readiness.

## 6. Findings

```text
F1. The six v2.24 roles CAN be expressed as deterministic static symbolic objects with no fixture, no data, no
    coordinate, no descriptor, no metric, no threshold, no score, and no pass/fail surface. Expressibility is a fact
    about NAMING, and about nothing else.
F2. Generated is NOT validated. Every role reports role_generated = True and role_validated = False, and the checker
    breaches on any role marked validated. Naming a role neither measures it nor makes it real.
F3. The honest roles survived implementation UNSOFTENED. D (may be inseparable), E (permanent artifact suspicion), and
    F (anti-claim boundary) are encoded as constraints, not as positive results. Nothing in the implementation pressure
    forced them into a result-shaped form.
F4. The claim surface did not grow. The artifact needed no number, no comparison, and no gate to say what each role is
    FOR -- which is evidence that the v2.24 role set was, as claimed, conceptual rather than covertly metric.
F5. The v2.22 primary question is UNTOUCHED. Reporting six roles does not distinguish BY-axis residual behavior from
    generic chroma proxy effects, and cannot: naming is not distinguishing. The question remains UNRESOLVED, and Role D
    keeps open that it may be unanswerable.
F6. The self-suspicion gate FIRED ON ITSELF (Section 5) -- the wording guard caught claiming phrasing inside the
    artifact's own denial text. Treat this as the expected behavior of a conservative gate, not as a proof of safety.
```

## 7. Forbidden Drift Register

```text
- role REPORTING becoming role VALIDATION (role_generated = True read as "the role is real / valid / useful").
- static symbolic role becoming CONCRETE FIXTURE / fixture data / stimulus / bank.
- reporting_focus LABEL becoming a DESCRIPTOR / feature / channel / axis / measured quantity.
- "distinguish / separate / matched / entangled" becoming a SCORED or MEASURED term.
- generic proxy role becoming a SOLVED or CONTROLLED proxy; artifact role becoming "not an artifact".
- null / reporting-boundary role becoming a VALIDATION CONTROL, a baseline, or a passed null.
- protocol_ok = True becoming VALIDATION / correctness / distinguishability / descriptor validity / readiness (v2.14).
- six-role completeness becoming VALIDATION COVERAGE, or a visual / classifier / neural ontology.
- this artifact becoming an IMPLEMENTATION LICENCE beyond exactly the v2.25 Section-4 shape.
- residual localization becoming DESCRIPTOR VALIDITY; isolation becoming CLOSURE; falsification becoming VALIDATION.
```

## 8. Non-Claim Interpretation

```text
WHAT v2.26 MAY ESTABLISH (and only this):
  - that the six v2.24 roles are EXPRESSIBLE as guarded static symbolic reporting objects;
  - a canonical, conservative BOUNDARY-COMPLIANCE gate over that expression;
  - the generated-vs-validated separation, held in code and in tests.

WHAT IT DOES NOT ESTABLISH:
  not fixtures              not fixture data            not a descriptor / coordinate
  not a metric / threshold  not metric separation       not validation
  not closure               not readiness               not vision
  not that the residual is distinguishable at all       not that any role is realizable, useful, or correct

Reporting six roles measures nothing, separates nothing, and validates nothing. The v2.22 question remains UNRESOLVED,
and it remains genuinely possible (Role D) that BY residual and generic chroma proxy are not separable at all.
```

## 9. Verification

```text
Focused suite: 81 tests over the v2.26 module (builder + canonical checker + 50 mutation probes + determinism), all
passing in a reconstructed tree. WINDOWS pytest remains the SOURCE OF TRUTH; the operator should re-run the focused
file and the full suite on Windows before treating this slice as verified. Nothing in the v2.26 logic is numeric or
boundary-valued, so no platform-boundary hazard is expected -- but the Windows run is still the one that counts.

CODEX REVIEW (MODIFY, patched in place): the first v2.26 checker rejected MISSING and TRUE keys in claim_locks /
adoption_flags / authorization_guards, but silently ACCEPTED an unknown key whose value was False -- so the guarded
surface could be widened without breaching. The three groups are now CLOSED sets: an extra key breaches regardless of
its value (claim_lock_extra / adoption_flag_extra / authorization_guard_extra). No boundary was relaxed to fix this;
the gate was tightened. Every other v2.26 boundary is unchanged.

The three files are the ONLY files added. No existing file is touched, no §0 pointer is added, and no tag is created.
```

## 10. Verdict

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
role_validity_claim_allowed                  = False
residual_localization_claim_allowed          = False
proxy_resolved_claim_allowed                 = False
metric_separation_claim_allowed              = False
closure_claim_allowed                        = False
validation_claim_allowed                     = False
descriptor_adopted                           = False
coordinate_system_adopted                    = False
metric_adopted                               = False
threshold_adopted                            = False
scoring_adopted                              = False
pass_fail_gate_adopted                       = False

OUTCOME_LABEL: BRAINVISION_BY_CHROMA_SYNTHETIC_FIXTURE_ROLES_REPORTING_ONLY
```

v2.26 is a reporting-only implementation of exactly the six v2.24 BY/chroma conceptual roles, in exactly the v2.25
Section-4 allowed shape. It generates no fixtures and no data; adopts no descriptor, coordinate system, metric,
threshold, scoring, or pass/fail gate; opens no screen / runtime / memory / classifier / neural / vision path; keeps
every claim lock, adoption flag, and authorization guard False; keeps every role generated and NOT validated; and
leaves the v2.22 primary question UNRESOLVED and possibly unanswerable. All claim locks and the frozen verdict **HOLD**
are preserved and unmoved.

## 11. Codex review prompt

```text
Please review the v2.26 slice (new, untracked; over the accepted v2.25 edge):
  research/brainvision/by_chroma_synthetic_fixture_roles_v2_26.py
  tests/research/test_brainvision_by_chroma_synthetic_fixture_roles_v2_26.py
  docs/TORMENT_BRAINVISION_BY_CHROMA_SYNTHETIC_FIXTURE_ROLES_FINDINGS_v2.26.md

Verify that this slice:
- adds EXACTLY these three files and touches nothing else; is offline research-only, outside torment_service/,
  stdlib-only, deterministic, static, and symbolic; adds no §0 pointer and no tags;
- exposes build_by_chroma_synthetic_fixture_roles_v2_26() returning a report with EXACTLY the six v2.24 role ids
  (A_BY_dominant_chroma_residual_role, B_generic_chroma_proxy_role, C_matched_non_BY_chroma_role,
  D_BY_chroma_entangled_role, E_fixture_family_artifact_role, F_null_reporting_boundary_role) -- no more, no fewer;
- gives each role ONLY symbolic / reporting fields (role_id, role_label, conceptual_purpose, reporting_focus,
  non_claim_constraints, forbidden_interpretations, safe_reporting_language, role_generated = True,
  role_validated = False), and carries NO fixture data, arrays, images, coordinates, descriptors, metrics, scores,
  thresholds, formulas, pass/fail gates, validation, expected outputs, classifier labels, neural targets, screen
  paths, real clips, runtime paths, memory paths, or vision claims ANYWHERE;
- carries a conservative CANONICAL check_protocol returning protocol_ok = True / breaches = [] ONLY for a clean report,
  and breaching on: missing / extra / wrong roles; role_validated True; a PASS (non-HOLD) verdict; a missing, EXTRA, or
  non-False key in claim_locks / adoption_flags / authorization_guards (the three groups are CLOSED: an extra key
  breaches even when its value is False); forbidden concrete fields; forbidden wording; validation / closure /
  readiness wording; and screen / runtime / memory / classifier / neural / vision wording;
- keeps the required locks False (flat_field_validated, first_pass_structure_validity_claim_allowed,
  temporal_claim_allowed, descriptor_validity_claim_allowed, geometry_validity_claim_allowed,
  screen_readiness_claim_allowed, runtime_readiness_claim_allowed, memory_readiness_claim_allowed,
  integration_readiness_claim_allowed, vision_claim_allowed) and the role-specific flags False
  (role_validity_claim_allowed, residual_localization_claim_allowed, proxy_resolved_claim_allowed,
  metric_separation_claim_allowed, closure_claim_allowed, validation_claim_allowed, descriptor_adopted,
  coordinate_system_adopted, metric_adopted, threshold_adopted, scoring_adopted, pass_fail_gate_adopted);
- encodes Role D (may be inseparable), Role E (permanent artifact suspicion; "not an artifact" may never be concluded)
  and Role F (anti-claim boundary; never a passed null) HONESTLY, with none softened into a positive result;
- keeps verdict = HOLD and outcome label BRAINVISION_BY_CHROMA_SYNTHETIC_FIXTURE_ROLES_REPORTING_ONLY; interprets
  protocol greenness as BOUNDARY COMPLIANCE ONLY (v2.14); leaves the v2.22 question UNRESOLVED.

Flag any concrete fixture / instance / bank / data / array / image / coordinate / descriptor / metric / score /
threshold / equation / expected output / pass-fail criterion anywhere; any role treated as validated, real, or useful;
any proxy or artifact treated as controlled or ruled out; any null treated as a baseline or a passed control; any
"distinguish / separate / matched / entangled" used as a scored term; any residual localization implying descriptor
validity; any closure, readiness, or vision claim; any authorization of further implementation; any weakening of the
wording gate to accommodate the artifact's own text; or any claim-lock / verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`flat_field_validated = False`, all claim locks False, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision BY/Chroma Synthetic Fixture ROLES Findings v2.26. Reporting-only implementation of exactly
the six v2.24 conceptual roles as deterministic static symbolic objects, in exactly the v2.25 Section-4 allowed shape,
guarded by a conservative canonical protocol checker. Generates no fixtures and no fixture data; adopts no descriptor /
coordinate system / numeric geometry / metric / equation / threshold / scoring / pass-fail gate; defines no data
structure, formula, numeric parameter, score, threshold, or expected output; opens no classifier / neural / screen /
real-clip / camera / live / sensor / streaming / runtime / memory / autonomy path; every role generated and NOT
validated; every claim lock, adoption flag, and authorization guard False; keeps prior BY / color / chroma work FROZEN
EVIDENCE, the flat opponent-field symbolic branch PAUSED HELD, and the v2.22 question UNRESOLVED and possibly
unanswerable (Role D); is not self-authorizing; makes no vision / "Brainvision sees" / descriptor-validity /
geometry-validity / temporal-order / readiness claim; outcome label
BRAINVISION_BY_CHROMA_SYNTHETIC_FIXTURE_ROLES_REPORTING_ONLY; no `§0` pointer added; no tags.*

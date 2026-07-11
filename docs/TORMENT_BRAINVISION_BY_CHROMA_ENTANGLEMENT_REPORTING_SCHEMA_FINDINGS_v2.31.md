# TORMENT Brainvision BY/Chroma Entanglement-Aware Reporting Schema Findings v2.31

## 1. Status / Scope

**SCHEMA-GENERATION-ONLY implementation + findings.** v2.31 implements the artifact conditionally allowed by the v2.30
implementation-boundary review, in exactly the Section-5 allowed shape and with none of the Section-6 forbidden shape,
under **Option A: `related_role_ids` DROPPED**.

**v2.31 is offline research-only.** It lives under `research/brainvision/` + `tests/research/`, outside
`torment_service/`, stdlib-only, HELD per v0.6. **HOLD / HELD means held for analysis and claim control — not
abandoned.**

**v2.31 is static symbolic schema generation only.** It writes down six ways of saying *we do not know*, under a
conservative guard. That is the entire artifact.

**What v2.31 does not do — and structurally cannot do:**

```text
- it DOES NOT ACCEPT INPUTS. The builder takes no argument. There is nothing to feed it, so there is nothing it could
  evaluate. A test asserts the signature has zero parameters.
- it DOES NOT ASSIGN, MAP, CLASSIFY, VALIDATE, SCORE, THRESHOLD, OR DECIDE outcomes. There is no arrival rule, no
  decision rule, no selection, routing, ranking, ordering, or matching of any kind, and nothing an outcome could be
  attached to.
- it EXCLUDES related_role_ids. The field is absent, not guarded. Per v2.30: a field that can only be made safe by
  rules about how to read it is not safe -- so it does not exist here.
- it EXCLUDES role-to-outcome mapping in every form. No v2.24 role appears anywhere in the schema.
- it adopts NO descriptor, coordinate system, numeric geometry, metric, score, threshold, formula, equation,
  comparison, pass/fail gate, acceptance criterion, or expected output.
- it opens NO screen / real-clip / camera / live / sensor / streaming path, NO runtime path, NO memory path, NO
  classifier (form B) path, NO neural (form C) path; it makes NO vision claim and NO "Brainvision sees" claim.
```

```text
flat_field_validated                        = False
role_validated                              = False
schema_validated                            = False
entanglement_resolved                       = False
by_residual_isolated                        = False
generic_chroma_proxy_ruled_out              = False
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed                      = False
descriptor_validity_claim_allowed           = False
geometry_validity_claim_allowed             = False
screen_readiness_claim_allowed              = False
runtime_readiness_claim_allowed             = False
memory_readiness_claim_allowed              = False
integration_readiness_claim_allowed         = False
vision_claim_allowed                        = False

descriptor_adopted        = False    coordinate_system_adopted = False    metric_adopted        = False
threshold_adopted         = False    scoring_adopted           = False    formula_adopted       = False
pass_fail_gate_adopted    = False    validation_adopted        = False    classifier_adopted    = False
neural_path_adopted       = False

screen_path_authorized    = False    runtime_path_authorized   = False    memory_path_authorized      = False
integration_path_authorized = False  real_clip_path_authorized = False    vision_claim_authorized     = False

verdict                                      = HOLD
```

**No `§0` pointer; no tags.**

## 2. What Was Implemented (three files; nothing else)

```text
research/brainvision/by_chroma_entanglement_reporting_schema_v2_31.py
  - build_by_chroma_entanglement_reporting_schema_v2_31()  -> deterministic static symbolic schema. NO PARAMETERS.
  - check_protocol(report=None) -> {"protocol_ok": bool, "breaches": [...]}, conservative and CANONICAL.
  - stdlib only (`__future__` only); no torment_service; no numeric / imaging / capture library anywhere.

tests/research/test_brainvision_by_chroma_entanglement_reporting_schema_v2_31.py
  - 115 tests: provenance; zero-parameter builder; exactly six canonical stances; generated-not-validated;
    absence of related_role_ids / role-to-outcome mapping / input / evidence / decision / arrival / assignment /
    metric / score / threshold / formula / pass-fail / validation / classifier / descriptor / coordinate /
    fixture-instance / screen / runtime / memory / vision fields; closed lock, flag, and guard groups all False;
    verdict HOLD; clean-report green; 53 mutation probes each flipping protocol_ok False; named-breach assertions;
    determinism.

docs/TORMENT_BRAINVISION_BY_CHROMA_ENTANGLEMENT_REPORTING_SCHEMA_FINDINGS_v2.31.md  (this file)
```

Top-level schema fields: `version`, `reporting_only`, `offline_research_only`, `symbolic_schema_only`,
`schema_generated`, `schema_validated`, `outcome_label`, `allowed_outcomes`, `claim_locks`, `adoption_flags`,
`authorization_guards`, `protocol`, `verdict`.

Each stance carries only: `outcome_id`, `outcome_label`, `reporting_stance`, `entanglement_status`,
`non_claim_status`, `allowed_language`, `forbidden_language`, `outcome_generated = True`, `outcome_validated = False`.

## 3. The Six Reporting Stances (stances, not classes)

```text
====================================================================================================================
OUTCOME ID                          LABEL                              ENTANGLEMENT STATUS
--------------------------------------------------------------------------------------------------------------------
BY_LEANING_UNRESOLVED               BY-leaning unresolved              entanglement not excluded
GENERIC_CHROMA_LEANING_UNRESOLVED   generic-chroma-leaning unresolved  entanglement not excluded
MATCHED_NON_BY_UNRESOLVED           matched-non-BY unresolved          entanglement not excluded
ENTANGLED_INSEPARABLE               entangled / inseparable            entanglement is the reported outcome
FIXTURE_ARTIFACT_SUSPECTED          fixture-artifact suspected         entanglement not addressed
NULL_REPORTING_BOUNDARY             null / reporting-boundary          entanglement not addressed
====================================================================================================================

THE SIX OUTCOME IDS ARE REPORTING STANCES ONLY. They are NOT classifier labels, NOT measured classes, NOT fixture
classes, NOT validation groups, NOT pass/fail results, and NOT visual categories. They are conceptual,
NON-EXHAUSTIVE and NON-PARTITIONING -- and the artifact SAYS SO IN ITSELF, in the protocol block:
outcome_set_is_exhaustive = False; outcome_set_is_partitioning = False;
unresolved_is_part_of_the_outcome_name = True; entangled_endpoint_is_first_class = True.

Nothing is ever sorted into them, because there is nothing to sort and no way to sort it.
```

## 4. `ENTANGLED_INSEPARABLE` Remains A First-Class Unresolved Endpoint

```text
Its non_claim_status is carried IN THE ARTIFACT, and a test asserts every clause of it:

  NOT failure                    NOT success                    NOT noise
  NOT an implementation defect   NOT an else-branch             NOT hidden BY evidence
  NOT a confound that was resolved                              NOT validation                  NOT closure

Its reporting_stance states that BY residual pressure and generic chroma proxy pressure COULD NOT BE TOLD APART here,
and stops -- a COMPLETE, TERMINAL, NON-DEFICIENT endpoint, reachable on its own terms and never only by elimination.

It is not harder to reach than any other stance, and it is not cheaper either -- because NO stance is reachable at all
by this artifact. That is the point: v2.31 makes "we could not tell" SAYABLE. It does not make it, or anything else,
CONCLUDABLE.
```

## 5. The Protocol Checker

`check_protocol` returns `protocol_ok = True` with `breaches = []` **only** for the clean canonical report. It breaches
on — and, if uncertain, breaches:

```text
- a missing or extra top-level key; a wrong version; reporting_only / offline_research_only / symbolic_schema_only /
  schema_generated not True; schema_validated True; a wrong outcome label; a verdict other than HOLD;
- a missing outcome, an extra outcome, a wrong outcome id (a stance filed under a key that is not its own id);
- outcome_generated not True; outcome_validated True; a missing or extra outcome field;
- CANONICAL DRIFT in any stance field (id, label, stance, entanglement status, non-claim status, allowed language,
  forbidden language) -- so a wrong outcome label is caught even when it is innocuous-looking ("BY-leaning" for
  "BY-leaning unresolved" is a breach: UNRESOLVED is part of the name);
- any forbidden field name, at top level, in a stance, or in the protocol block -- including related_role, role_id,
  role_to_outcome, mapping, input, evidence, decision, arrival, assign, classif, confidence, score, metric, threshold,
  formula, pass_fail, validation_result, descriptor, coordinate, fixture_instance, screen, runtime, memory, vision,
  neural, clip, pixel, array, image;
- any numeric value, nested container, or non-string list entry;
- FORBIDDEN CLAIM WORDING in an outcome label, reporting stance, entanglement status, non-claim status, allowed
  language, or protocol string -- the twelve forbidden claims and their paraphrases, plus surface tokens that must
  never appear in a stance;
- a missing, EXTRA (even when False), or non-False key in claim_locks / adoption_flags / authorization_guards. All
  three groups are CLOSED, per the v2.26 Codex MODIFY: an extra False key silently widens the guarded surface.
```

**Greenness means BOUNDARY COMPLIANCE ONLY (v2.14).** `protocol_ok = True` is not schema validity, not correctness,
not distinguishability, not descriptor validity, not closure, and not readiness. **`schema_validated = False` even when
every test is green** — and the checker breaches if anything flips it True.

## 6. One Design Tension, Stated Rather Than Hidden

```text
The `forbidden_language` field must CITE the twelve claims that may never be made ("descriptor validated", "screen
ready", "Brainvision sees", ...). But the wording gate exists precisely to reject those phrases in schema strings. A
naive gate would therefore reject the artifact for NAMING the very claims it forbids.

RESOLUTION: forbidden_language is guarded by EXACT-SET MEMBERSHIP against the canonical citation list -- every entry
must be a canonical citation, and every canonical citation must be present -- while every OTHER string field is guarded
by the assertion scan. Adding a phrase to forbidden_language, or dropping one, breaches. Asserting a forbidden claim
anywhere else breaches.

WHY THIS IS HONEST: citing a claim is not making it. But that distinction cannot be left to the reader's good faith, so
it is enforced structurally: exactly one field may contain those phrases, its contents are frozen, and nothing else in
the artifact may contain them. Tests assert both halves -- the canonical citation list is exact, and the rest of the
canonical text is free of every forbidden phrase.
```

## 7. Findings

```text
F1. A reporting schema CAN be written down without acquiring mapping, arrival, decision, validation, or classifier
    semantics -- the v2.30 primary question, answered in the affirmative FOR THIS ARTIFACT ONLY. The proof is
    structural, not textual: the builder has no parameters, so there is no input; with no input there is nothing to
    evaluate, nothing to assign, and nothing to decide.
F2. DROPPING related_role_ids COST NOTHING. Every stance says what it is for without reference to any v2.24 role. The
    cross-reference lives in the docs, where it was already. Option A removed a hazard and lost no expressiveness --
    which is evidence the field was never load-bearing, only tempting.
F3. GENERATED IS NOT VALIDATED, at two levels: schema_generated = True / schema_validated = False, and
    outcome_generated = True / outcome_validated = False on every stance. The checker breaches on either flip.
F4. The honest endpoint SURVIVED IMPLEMENTATION UNSOFTENED. ENTANGLED_INSEPARABLE is carried with all nine denials
    intact, and no implementation pressure pushed it toward a result-shaped form.
F5. The artifact ADVANCED NOTHING ABOUT COLOUR. It measured nothing, separated nothing, and validated nothing. The
    v2.22 question -- can BY-axis residual behavior be distinguished from generic chroma proxy effects without metrics
    or closure claims -- REMAINS UNRESOLVED, and remains possibly unanswerable (v2.24 Role D).
F6. What v2.31 changes is what the project CAN SAY, not what it knows. "Entangled / inseparable" is now a structured,
    first-class thing to report rather than a leftover. That is a claim-control improvement. It is not evidence, and it
    must never be cited as progress toward the v2.22 question.
```

## 8. Forbidden Drift Register

```text
- the schema acquiring an INPUT, an arrival rule, or an assignment -- becoming a decision system in vocabulary.
- related_role_ids or any role-to-outcome relation returning in any form.
- outcome ids becoming CLASSIFIER LABELS, measured classes, fixture classes, validation groups, pass/fail outputs, or
  visual categories; outcome ids being APPLIED to anything.
- the stance set becoming EXHAUSTIVE, a PARTITION, or a claim of COVERAGE.
- "UNRESOLVED" dropped from an outcome name (BY_LEANING_UNRESOLVED -> BY_LEANING -> BY).
- reporting_stance / entanglement_status acquiring a degree, weight, score, confidence, strength, or resolution state.
- non_claim_status becoming a validation flag ("cleared", "checked", "passed").
- forbidden_language being edited -- entries added, dropped, or softened.
- protocol greenness becoming SCHEMA VALIDITY (v2.14); schema_validated drifting True.
- ENTANGLED_INSEPARABLE becoming failure, success, noise, defect, else-branch, hidden BY evidence, proxy-resolved,
  validation, or closure.
- this artifact becoming an IMPLEMENTATION LICENCE beyond exactly the v2.30 Section-5 shape.
```

## 9. Non-Claim Interpretation

```text
WHAT v2.31 MAY ESTABLISH (and only this):
  - that the six reporting stances are EXPRESSIBLE as a guarded, deterministic, static symbolic schema with no input,
    no arrival rule, no assignment, and no role relation;
  - a conservative BOUNDARY-COMPLIANCE gate over that expression;
  - the generated-vs-validated separation, held in code and in tests, at both the schema and the stance level.

WHAT IT DOES NOT ESTABLISH:
  not fixtures / data      not a descriptor / coordinate    not a metric / score / threshold
  not a decision rule      not validation                   not closure
  not readiness            not vision                       not that the residual is distinguishable
  not that the residual is indistinguishable                not that entanglement IS the answer
  not that this schema is correct, useful, or worth having

Writing down six ways of saying "we do not know" measures nothing. NO CLOSURE, NO VALIDATION, AND NO VISION READINESS
FOLLOWS FROM v2.31.
```

## 10. Verification

```text
Focused suite: 115 tests (builder + canonical checker + 53 mutation probes + named-breach assertions + determinism),
all passing in a reconstructed tree; the clean report is protocol_ok = True with breaches = [].

WINDOWS pytest remains the SOURCE OF TRUTH; the operator should re-run the focused file and the full suite on Windows
before treating this slice as verified. Nothing in the v2.31 logic is numeric or boundary-valued, so no
platform-boundary hazard is expected -- but the Windows run is still the one that counts.

The three files are the ONLY files added. No existing file is touched, no §0 pointer is added, and no tag is created.
```

## 11. Verdict

```text
verdict                                      = HOLD
flat_field_validated                         = False
role_validated                               = False
schema_validated                             = False
entanglement_resolved                        = False
by_residual_isolated                         = False
generic_chroma_proxy_ruled_out               = False
first_pass_structure_validity_claim_allowed  = False
temporal_claim_allowed                       = False
descriptor_validity_claim_allowed            = False
geometry_validity_claim_allowed              = False
screen_readiness_claim_allowed               = False
runtime_readiness_claim_allowed              = False
memory_readiness_claim_allowed               = False
integration_readiness_claim_allowed          = False
vision_claim_allowed                         = False
[all adoption flags]                         = False
[all authorization guards]                   = False

OUTCOME_LABEL: BRAINVISION_BY_CHROMA_ENTANGLEMENT_REPORTING_SCHEMA_ONLY
```

v2.31 is a deterministic, static, symbolic, offline research-only, reporting-only schema artifact for BY/chroma
entanglement-aware reporting, in exactly the v2.30 Section-5 allowed shape under Option A. It accepts no inputs;
assigns, maps, classifies, validates, scores, thresholds, and decides nothing; excludes `related_role_ids` and every
role-to-outcome mapping; carries the six outcome ids as reporting stances only; preserves `ENTANGLED_INSEPARABLE` as a
first-class unresolved endpoint; keeps `schema_validated = False` and every claim lock, adoption flag, and
authorization guard False in closed groups; and leaves the v2.22 question UNRESOLVED and possibly unanswerable. All
claim locks and the frozen verdict **HOLD** are preserved and unmoved.

## 12. Codex review prompt

```text
Please review the v2.31 slice (new, untracked; over the accepted v2.30 edge
 "d47bc56 docs(research): review by chroma entanglement schema boundary"):
  research/brainvision/by_chroma_entanglement_reporting_schema_v2_31.py
  tests/research/test_brainvision_by_chroma_entanglement_reporting_schema_v2_31.py
  docs/TORMENT_BRAINVISION_BY_CHROMA_ENTANGLEMENT_REPORTING_SCHEMA_FINDINGS_v2.31.md

Verify that this slice:
- adds EXACTLY these three files and touches nothing else; is offline research-only, outside torment_service/,
  stdlib-only, deterministic, static, and symbolic; adds no §0 pointer and no tags;
- exposes build_by_chroma_entanglement_reporting_schema_v2_31() with NO PARAMETERS (takes no input), and a
  conservative canonical check_protocol returning protocol_ok = True / breaches = [] ONLY for the clean report;
- carries EXACTLY the allowed top-level fields (version, reporting_only, offline_research_only, symbolic_schema_only,
  schema_generated, schema_validated, outcome_label, allowed_outcomes, claim_locks, adoption_flags,
  authorization_guards, protocol, verdict) and EXACTLY the six outcome ids (BY_LEANING_UNRESOLVED,
  GENERIC_CHROMA_LEANING_UNRESOLVED, MATCHED_NON_BY_UNRESOLVED, ENTANGLED_INSEPARABLE, FIXTURE_ARTIFACT_SUSPECTED,
  NULL_REPORTING_BOUNDARY), each with only outcome_id / outcome_label / reporting_stance / entanglement_status /
  non_claim_status / allowed_language / forbidden_language / outcome_generated = True / outcome_validated = False;
- contains NO related_role_ids, NO role-to-outcome mapping, and NO input / evidence / decision / arrival / assignment /
  metric / score / threshold / formula / pass-fail / validation / classifier / descriptor / coordinate /
  fixture-instance / screen / runtime / memory / vision field ANYWHERE (noting that the claim-lock, adoption-flag, and
  authorization-guard MEMBER NAMES are locks AGAINST those things, held False, and are not themselves such fields);
- keeps the outcome ids as REPORTING STANCES ONLY (not classifier labels, measured classes, fixture classes,
  validation groups, pass/fail results, or visual categories), non-exhaustive and non-partitioning, with "UNRESOLVED"
  part of the names;
- preserves ENTANGLED_INSEPARABLE as a first-class unresolved endpoint that is not failure, success, noise,
  implementation defect, else-branch, hidden BY evidence, proxy resolved, validation, or closure;
- guards forbidden_language by EXACT-SET membership (it cites the twelve forbidden claims; it may never assert them),
  and guards every other string field by the assertion scan; asserts the canonical text is free of every forbidden
  phrase;
- keeps schema_generated = True, schema_validated = False, every claim lock / adoption flag / authorization guard
  present and False in CLOSED groups (an extra key, even one set False, breaches), and verdict = HOLD;
- interprets protocol greenness as BOUNDARY COMPLIANCE ONLY (v2.14) and leaves the v2.22 question UNRESOLVED.

Flag any input, arrival rule, decision rule, assignment, selection, routing, ranking, or matching; any role-to-outcome
relation; any outcome id treated as a class, label, or assignment; any outcome set treated as exhaustive or
partitioning; any "UNRESOLVED" dropped from a name; any degree / weight / score / confidence in a stance; any softening
of ENTANGLED_INSEPARABLE; any edit to forbidden_language; any protocol greenness read as schema validity; any open
lock / flag / guard group; any claim that anything was isolated, ruled out, resolved, validated, detected, or seen; or
any claim-lock / verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`flat_field_validated = False`, `role_validated = False`, `schema_validated = False`, `entanglement_resolved = False`,
`by_residual_isolated = False`, `generic_chroma_proxy_ruled_out = False`, all claim locks, adoption flags, and
authorization guards False, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision BY/Chroma Entanglement-Aware Reporting Schema Findings v2.31. Deterministic, static,
symbolic, offline research-only, reporting-only schema artifact in exactly the v2.30 Section-5 allowed shape, Option A
(related_role_ids dropped). Accepts no inputs (zero-parameter builder); assigns, maps, classifies, validates, scores,
thresholds, and decides nothing; excludes related_role_ids and every role-to-outcome mapping; adopts no descriptor /
coordinate system / numeric geometry / metric / equation / threshold / scoring / formula / pass-fail gate; opens no
screen / real-clip / camera / live / sensor / streaming / runtime / memory / classifier / neural path; carries the six
outcome ids as reporting stances only -- not classifier labels, measured classes, fixture classes, validation groups,
pass/fail results, or visual categories -- non-exhaustive and non-partitioning; preserves ENTANGLED_INSEPARABLE as a
first-class, terminal, non-deficient unresolved endpoint that is not failure, success, noise, implementation defect,
else-branch, hidden BY evidence, proxy resolved, validation, or closure; guards forbidden_language by exact-set
citation membership so the artifact may name what it forbids without asserting it; keeps schema_generated = True and
schema_validated = False, and every claim lock, adoption flag, and authorization guard False in closed groups; protocol
greenness means boundary compliance only; keeps prior BY / color / chroma work FROZEN EVIDENCE, the flat opponent-field
symbolic branch PAUSED HELD, and the v2.22 question UNRESOLVED and possibly unanswerable; makes no vision /
"Brainvision sees" / descriptor-validity / geometry-validity / temporal-order / readiness claim; no closure, no
validation, and no vision readiness follows from v2.31; outcome label
BRAINVISION_BY_CHROMA_ENTANGLEMENT_REPORTING_SCHEMA_ONLY; no `§0` pointer added; no tags.*

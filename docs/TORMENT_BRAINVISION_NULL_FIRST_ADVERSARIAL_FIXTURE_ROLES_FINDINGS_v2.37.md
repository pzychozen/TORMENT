# TORMENT Brainvision Null-First Adversarial Fixture-Role Findings v2.37

## 1. Status / Scope

**ROLE-GENERATION-ONLY implementation + findings.** v2.37 implements the artifact conditionally allowed by the v2.36
implementation-boundary review, in exactly the Section-4 allowed shape and with none of the Section-6 forbidden shape,
holding warnings W1–W4 structurally.

**v2.37 is offline research-only.** It lives under `research/brainvision/` + `tests/research/`, outside
`torment_service/`, stdlib-only, HELD per v0.6. **HOLD / HELD means held for analysis and claim control — not
abandoned.**

**v2.37 is static symbolic role generation only.** It writes down six adversarial **nouns**. That is the whole
artifact.

**v2.37 defines none of the following:**

```text
fixtures            fixture instances    fixture data         generation rules
schemas             data shapes          arrays / images      descriptors
coordinates         metrics              scores               thresholds
formulas            decision rules       arrival rules        pass/fail gates
validation          classifier (form B)  neural (form C)      screen / runtime / memory paths
real clips          vision
```

**It accepts no input.** The builder takes no argument — a test asserts a zero-parameter signature. With nothing to
feed it, there is nothing it could build, evaluate, assign, choose, classify, detect, rule out, or validate.

**v2.37 advances S3 by exactly nothing beyond symbolic vocabulary.** S3 — a pre-stated, *reachable* survival path — is
the binding obligation standing between this programme and a real null-first study. This artifact does not touch it.
It is a freezing of language, not a step toward a result. v2.36 §8 said so before the artifact was approved, and the
artifact does not now say otherwise.

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
geometry_validity_claim_allowed             = False      [all 12 adoption flags]       = False
screen_readiness_claim_allowed              = False      [all 7 authorization guards]  = False
runtime_readiness_claim_allowed             = False
memory_readiness_claim_allowed              = False
integration_readiness_claim_allowed         = False
vision_claim_allowed                        = False
verdict                                      = HOLD
```

**No `§0` pointer; no tags.**

## 2. What Was Implemented (three files; nothing else)

```text
research/brainvision/null_first_adversarial_fixture_roles_v2_37.py
  - build_null_first_adversarial_fixture_roles_v2_37()  -> deterministic static symbolic report. NO PARAMETERS.
  - check_protocol(report=None) -> {"protocol_ok": bool, "breaches": [...]}, conservative and CANONICAL.
  - stdlib only (`__future__` only); no torment_service; no numeric / imaging / capture library anywhere.

tests/research/test_brainvision_null_first_adversarial_fixture_roles_v2_37.py
  - 122 tests: provenance; zero-parameter builder; exactly six canonical roles with canonical ids and labels;
    generated-not-validated; absence of every forbidden field family; W1 / W2 / W3 asserted in the artifact itself;
    closed lock, flag, and guard groups all False; verdict HOLD; clean-report green; 61 mutation probes each flipping
    protocol_ok False; named-breach assertions; determinism.

docs/TORMENT_BRAINVISION_NULL_FIRST_ADVERSARIAL_FIXTURE_ROLES_FINDINGS_v2.37.md  (this file)
```

Top-level fields: `version`, `reporting_only`, `offline_research_only`, `symbolic_role_reporting_only`,
`roles_generated`, `outcome_label`, `roles`, `claim_locks`, `adoption_flags`, `authorization_guards`, `protocol`,
`verdict`.

Each role carries only: `role_id`, `role_label`, `conceptual_purpose`, `adversarial_focus`, `safe_reporting_language`,
`forbidden_interpretations`, `non_claim_constraints`, `role_generated = True`, `role_validated = False`.

**`role_id` carries the FULL canonical v2.35 role ID** — `A_null_no_structure_role`, `B_fixture_artifact_role`,
`C_proxy_confound_role`, `D_entangled_unresolved_role`, `E_control_collapse_role`,
`F_candidate_structure_survival_role` — **never a short letter**, and it must equal the key the role is filed under. A
first draft used short letters `A`–`F`; Codex rejected it (MODIFY) as drift from the accepted v2.35 names, and the
artifact and tests now pin the full IDs. Short letters would have been a quiet re-identification of the roles: the
v2.35 names carry their meaning, and a letter carries none.

## 3. The Six Adversarial Roles (nouns, not categories)

The `role_id` column below is the value carried in each role object's `role_id` field — the full canonical v2.35 ID,
identical to the key it is filed under.

```text
====================================================================================================================
ROLE ID (full canonical v2.35 ID)      LABEL                              STANDING
--------------------------------------------------------------------------------------------------------------------
A_null_no_structure_role               null / no-structure role           VALID ENDPOINT -- not failure, not a null
                                                                          that was rejected, not measured absence
B_fixture_artifact_role                fixture-artifact role              artifact NOT ruled out; the absence of an
                                                                          artifact may never be concluded
C_proxy_confound_role                  proxy-confound role                proxy and confound NOT ruled out; naming a
                                                                          confound neither controls nor removes it
D_entangled_unresolved_role            entangled / unresolved role        VALID TERMINAL ENDPOINT -- not noise, not
                                                                          hidden evidence, not failure, not success
E_control_collapse_role                control-collapse role              REACHABLE IN LANGUAGE ONLY (W1)
F_candidate_structure_survival_role    candidate-structure-survival role  ONLY A FUTURE QUESTION (W2)
====================================================================================================================

The six roles are SYMBOLIC and NON-PARTITIONING. They are NOT fixture classes, measured classes, classifier labels,
validation groups, pass/fail categories, or visual categories. The artifact says so IN ITSELF:
roles_are_exhaustive = False; roles_are_partitioning = False. Nothing is ever sorted into them, because there is
nothing to sort and no way to sort it.
```

## 4. W1 — `E_control_collapse_role` Is Reachable In Language Only

```text
The role is reported as GENERATED. Control-collapse is NOT tested, NOT detected, NOT ruled out, NOT avoided, and NOT
handled. Both locks stay False and the checker breaches on either:

    control_collapse_ruled_out = False
    control_collapse_detected  = False

The artifact carries this in its own non_claim_constraints: "this role is a NOUN; naming the way the controls could
fail is not checking whether they did", and "a design that cannot report the collapse of its own controls is not
adversarial, only defended".

THE TRAP THIS CLOSES: "the artifact has a control-collapse role" reads, on a tired day, as "the design has a
control-collapse check". It has no such thing. It has a noun.
```

## 5. W2 — `F_candidate_structure_survival_role` Is Only A Future Question

```text
Nothing in the artifact implies that candidate structure survived, was detected, was validated, or is EXPECTED. Three
locks stay False and the checker breaches on any of them:

    candidate_structure_survived  = False
    candidate_structure_detected  = False
    candidate_structure_validated = False

F's only safe reporting language is the single line "candidate structure remains only a future question". Its
non_claim_constraints state that its emptiness is a legitimate PERMANENT state, not a shortfall, and that it names a
BURDEN, not an entitlement.

WHY F EXISTS AT ALL (v2.36 §7): if F were dropped, roles A-E would be exhaustive by construction, and survival would
be reachable only by ELIMINATION from them -- the NULL SINK, in which "nothing survived" is guaranteed whatever is
true. F is kept precisely so that A-E are visibly not the whole story. The artifact records this in F's own
non_claim_constraints. The hazard is not that F exists; the hazard is that F gets read as an expectation.
```

## 6. W4 — What A Green Check Means, And What It Does Not

`check_protocol` verifies **canonical symbolic structure** and **forbidden-surface absence**. Nothing else. It breaches
on:

```text
- a missing or extra top-level key; a wrong version; reporting_only / offline_research_only /
  symbolic_role_reporting_only / roles_generated not True; a wrong outcome label; a verdict other than HOLD;
- a missing role, an extra role, a wrong role id, a wrong role label (canonical drift in ANY role field);
- role_generated not True; role_validated True; a missing or extra role field;
- any forbidden field name at top level, in a role, or in the protocol block -- fixture_instance, fixture_data,
  generation, schema, data_shape, array, image, descriptor, coordinate, metric, score, threshold, formula, decision,
  arrival, evidence, confidence, classif, validation, pass_fail, survival, positive_structure, screen, runtime,
  memory, real_clip, vision, neural, pixel, input, assign, mapping;
- any numeric value, nested container, or non-string list entry;
- FORBIDDEN CLAIM WORDING in any string: structure detected; candidate survived; fixture passed; null rejected;
  artifact ruled out; proxy ruled out; confound controlled; control passed; descriptor validated; geometry validated;
  metric validated; screen ready; runtime ready; memory ready; vision achieved; Brainvision sees -- plus paraphrases
  ("the nulls behaved", "not an artifact", "something real is there", "positive structure", ...) and surface tokens;
- a missing, EXTRA (even when False), or non-False key in claim_locks / adoption_flags / authorization_guards. All
  three groups are CLOSED, per the v2.26 Codex MODIFY.
```

**A green check does NOT mean:** scientific validity, fixture quality, control quality, detection, survival,
falsification success, or *"the adversary is in place"*. **There is no adversary here — there are six nouns.** Nothing
has been tested and nothing controlled; *"the nulls behaved"* cannot even be asserted, because no null has behaved in
any way at all. `role_validated = False` everywhere, even with all 122 tests green.

## 7. Findings

```text
F1. The six adversarial roles are EXPRESSIBLE as a guarded, deterministic, static symbolic artifact with no input, no
    generation rule, no schema, no assignment, no decision path, and no positive-structure surface. The guarantee is
    structural, not textual: a zero-parameter builder cannot evaluate what it is never given.
F2. GENERATED IS NOT VALIDATED, at two levels: roles_generated = True with every role_validated = False, and the
    checker breaching on either flip. Naming an adversary is not defeating one.
F3. THE TWO DANGEROUS ROLES SURVIVED IMPLEMENTATION UNSOFTENED. E stayed a noun (W1) and F stayed a question (W2).
    Notably, no implementation pressure pushed F toward being a slot to fill -- but the artifact does not treat that
    as reassurance: the locks, not the good intentions, are what hold it.
F4. THE NULL-FIRST FLOOR HELD. A / B / C / D are carried as VALID ENDPOINTS, not cleanup categories: null_rejected,
    artifact_ruled_out, proxy_ruled_out, confound_controlled and entanglement_resolved all stay False, and the wording
    gate rejects every claim shape that would flip them in prose.
F5. S3 IS UNTOUCHED. The binding reachability obligation -- can a null-first design be described in which survival is
    genuinely reachable? -- is exactly where it was before this artifact existed. v2.37 could not fail at anything,
    and it did not.
F6. WHAT THIS BOUGHT: the six roles are now frozen canonically in code, so a later design cannot quietly redefine
    them. That is real, and it is small, and it is not scientific progress. It is vocabulary hygiene.
```

## 8. Forbidden Drift Register

```text
- E being read as a CONTROL-COLLAPSE CHECK. It is a noun (W1).
- F being read as an EXPECTATION, a goal, or a slot the project intends to fill (W2).
- F being DROPPED, which would make A-E exhaustive and survival reachable only by elimination -- the NULL SINK.
- the six roles becoming FIXTURE CLASSES, measured classes, classifier labels, validation groups, pass/fail
  categories, or visual categories; or becoming a PARTITION or an exhaustive taxonomy (W3).
- protocol greenness becoming scientific validity, fixture quality, control quality, detection, survival,
  falsification success, or "the adversary is in place" (W4).
- "the nulls behaved" being asserted at all. No null has behaved; no null exists.
- A / B / C / D becoming obstacles to explain away rather than valid endpoints.
- the artifact being cited as EVIDENCE, as progress toward S3, or as an implementation licence beyond the v2.36
  Section-4 shape.
- the adversary being weakened, retuned, or excused in any future slice after a candidate fails against it (v2.34 S2).
```

## 9. Non-Claim Interpretation

```text
WHAT v2.37 MAY ESTABLISH (and only this):
  - that the six null-first adversarial roles are EXPRESSIBLE as a guarded static symbolic artifact with no input, no
    generation, no assignment, no decision path, and no positive-structure surface;
  - a conservative BOUNDARY-COMPLIANCE gate over that expression;
  - the generated-vs-validated separation, held in code and in tests, at both the report and the role level.

WHAT IT DOES NOT ESTABLISH:
  not fixtures / data      not a generation rule / schema      not a descriptor / coordinate / metric
  not a decision rule      not validation                      not closure          not readiness      not vision
  not that control-collapse has been tested, detected, ruled out, avoided, or handled
  not that candidate structure survived, was detected, was validated, or is expected
  not that any structure exists to be found; not that any could survive; not that none could
  not that survival is REACHABLE (S3 remains binding and undischarged)
  not that these six roles are the right ones, complete, useful, or realizable

Writing down six adversarial nouns tests nothing, controls nothing, detects nothing, rules nothing out, and survives
nothing. NO CLOSURE, NO VALIDATION, AND NO READINESS FOLLOWS FROM v2.37.
```

## 10. Verification

```text
Focused suite: 122 tests (builder + canonical checker + 61 mutation probes + W1/W2/W3 artifact assertions +
named-breach assertions + determinism), all passing in a reconstructed tree; the clean report is protocol_ok = True
with breaches = [].

WINDOWS pytest remains the SOURCE OF TRUTH; the operator should re-run the focused file and the full suite on Windows
before treating this slice as verified. Nothing in the v2.37 logic is numeric or boundary-valued, so no
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
[all 12 adoption flags]                      = False
[all 7 authorization guards]                 = False

OUTCOME_LABEL: BRAINVISION_NULL_FIRST_ADVERSARIAL_FIXTURE_ROLES_REPORTING_ONLY
```

v2.37 is a deterministic, static, symbolic, offline research-only, reporting-only null-first adversarial family-role
artifact, in exactly the v2.36 Section-4 allowed shape. It accepts no inputs; generates no fixture, fixture instance,
or fixture data; defines no generation rule, schema, data shape, descriptor, coordinate, metric, score, threshold,
formula, decision rule, arrival rule, pass/fail gate, or validation criterion; opens no classifier / neural / screen /
runtime / memory / real-clip path; makes no vision or readiness claim. It carries the six roles as symbolic,
non-partitioning nouns; keeps `E_control_collapse_role` reachable in **language only** (not tested, detected, ruled
out, avoided, or handled) and `F_candidate_structure_survival_role` as **only a future question** (not survived,
detected, validated, or expected); keeps every role `role_validated = False` and every claim lock, adoption flag, and
authorization guard False in closed groups; and advances the binding S3 reachability obligation by **exactly nothing**
beyond symbolic vocabulary. All claim locks and the frozen verdict **HOLD** are preserved and unmoved.

## 12. Codex review prompt

```text
Please review the v2.37 slice (new, untracked; over the accepted v2.36 edge
 "582a972 docs(research): review null-first adversarial fixture boundary"):
  research/brainvision/null_first_adversarial_fixture_roles_v2_37.py
  tests/research/test_brainvision_null_first_adversarial_fixture_roles_v2_37.py
  docs/TORMENT_BRAINVISION_NULL_FIRST_ADVERSARIAL_FIXTURE_ROLES_FINDINGS_v2.37.md

Verify that this slice:
- adds EXACTLY these three files and touches nothing else; is offline research-only, outside torment_service/,
  stdlib-only, deterministic, static, and symbolic; adds no §0 pointer and no tags;
- exposes build_null_first_adversarial_fixture_roles_v2_37() with NO PARAMETERS (takes no input), and a conservative
  canonical check_protocol returning protocol_ok = True / breaches = [] ONLY for the clean report;
- carries EXACTLY the allowed top-level fields (version, reporting_only, offline_research_only,
  symbolic_role_reporting_only, roles_generated, outcome_label, roles, claim_locks, adoption_flags,
  authorization_guards, protocol, verdict) and EXACTLY the six roles (A_null_no_structure_role,
  B_fixture_artifact_role, C_proxy_confound_role, D_entangled_unresolved_role, E_control_collapse_role,
  F_candidate_structure_survival_role), each with only role_id / role_label / conceptual_purpose / adversarial_focus /
  safe_reporting_language / forbidden_interpretations / non_claim_constraints / role_generated = True /
  role_validated = False;
- contains NO fixture / fixture-data / generation-rule / schema / data-shape field; NO array / image; NO descriptor /
  coordinate / metric / score / threshold / formula field; NO decision / arrival / evidence / confidence /
  classification field; NO validation / pass-fail / survival / positive-structure field; NO screen / runtime / memory /
  real-clip / vision field (noting that the claim-lock, adoption-flag, and authorization-guard MEMBER NAMES are locks
  AGAINST those things, held False, and that the canonical role id F_candidate_structure_survival_role is a v2.35 NAME,
  not a field);
- holds W1 (E reachable in LANGUAGE ONLY -- control_collapse_ruled_out = False AND control_collapse_detected = False;
  no string claims collapse was tested, detected, ruled out, avoided, or handled), W2 (F is ONLY a future question --
  candidate_structure_survived / _detected / _validated all False; no implication of survival, detection, validation,
  or expectation; F retained so A-E are not exhaustive, avoiding the null sink), W3 (roles symbolic and
  NON-PARTITIONING; roles_are_exhaustive = False, roles_are_partitioning = False), and W4 (protocol greenness =
  canonical symbolic structure + forbidden-surface absence ONLY -- never scientific validity, fixture quality, control
  quality, detection, survival, or falsification success);
- keeps roles_generated = True, every role_validated = False, every claim lock / adoption flag / authorization guard
  present and False in CLOSED groups (an extra key, even one set False, breaches), and verdict = HOLD;
- states in the findings doc that v2.37 advances S3 by exactly nothing beyond symbolic vocabulary.

Flag any input, generation rule, schema, data shape, fixture, fixture instance, or fixture data; any assignment,
selection, decision, or arrival semantics; any descriptor / coordinate / metric / score / threshold / formula; any
evidence / confidence / classification / validation / pass-fail / survival / positive-structure field; any suggestion
that control-collapse was tested, detected, ruled out, avoided, or handled; any suggestion that candidate structure
survived, was detected, was validated, or is expected; any role set treated as exhaustive, partitioning, or as fixture
/ measured / classifier / validation / pass-fail / visual categories; any protocol greenness read as validity, control
quality, detection, survival, or falsification success; any assertion that "the nulls behaved"; any open lock / flag /
guard group; any claim that S3 has been advanced; or any claim-lock / verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
All claim locks False — including `null_rejected`, `artifact_ruled_out`, `proxy_ruled_out`, `confound_controlled`,
`control_collapse_ruled_out`, `control_collapse_detected`, `candidate_structure_validated`,
`candidate_structure_survived`, and `candidate_structure_detected` — and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Null-First Adversarial Fixture-Role Findings v2.37. Deterministic, static, symbolic, offline
research-only, reporting-only role artifact in exactly the v2.36 Section-4 allowed shape. Accepts no inputs
(zero-parameter builder); generates no fixture, fixture instance, or fixture data; defines no generation rule, schema,
data shape, array, image, descriptor, coordinate, metric, score, threshold, formula, decision rule, arrival rule,
pass/fail gate, or validation criterion; opens no classifier / neural / screen / runtime / memory / real-clip path;
makes no vision or readiness claim. Carries the six v2.35 null-first adversarial family roles as symbolic,
non-partitioning NOUNS -- A null / no-structure (a valid endpoint, not failure, not a null that was rejected);
B fixture-artifact (artifact not ruled out; its absence may never be concluded); C proxy-confound (proxy and confound
not ruled out); D entangled / unresolved (a valid terminal endpoint, not noise, not hidden evidence, not success);
E control-collapse (REACHABLE IN LANGUAGE ONLY -- not tested, detected, avoided, handled, or ruled out);
F candidate-structure-survival (ONLY A FUTURE QUESTION -- not survived, detected, validated, expected, or evidenced,
and retained so that A-E are not exhaustive by construction, avoiding the null sink) -- each generated and NOT
validated; keeps every claim lock, adoption flag, and authorization guard False in closed groups; protocol greenness
means canonical symbolic structure and forbidden-surface absence ONLY, never scientific validity, fixture quality,
control quality, detection, survival, or falsification success; advances the binding S3 reachability obligation by
EXACTLY NOTHING beyond symbolic vocabulary; keeps prior BY / color / chroma work FROZEN EVIDENCE, the BY/chroma
scaffold REPORTING LANGUAGE ONLY, the flat opponent-field symbolic branch PAUSED HELD, and the v2.22 question
UNRESOLVED and possibly unanswerable; preserves all claim locks and the frozen verdict HOLD; outcome label
BRAINVISION_NULL_FIRST_ADVERSARIAL_FIXTURE_ROLES_REPORTING_ONLY; no `§0` pointer added; no tags.*

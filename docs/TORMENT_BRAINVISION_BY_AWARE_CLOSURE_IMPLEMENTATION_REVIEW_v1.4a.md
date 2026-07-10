# TORMENT Brainvision BY-Aware Closure Implementation Review v1.4a

## 1. Status / non-claims

**DOCS-ONLY implementation authorization review. It MAY recommend implementation, but it implements nothing.**
Opens no code, no tests, no runtime, no integration lane here. It reviews whether a future **v1.5** reporting-only
implementation harness of the v1.4 preregistration may be authorized, and defines the **exact boundary** v1.5
would have to respect if the operator later approves it. Recommending authorization is **not** performing it: this
document writes no `.py`, runs nothing, and authorizes nothing by itself — a separate, explicit operator decision
is required to open v1.5.

It adopts **no** closure metric, **no** equation, invents **no** threshold, **redefines no `TOL`**, adds **no**
pass/fail validity rule, changes no formula / §7 anti-proxy logic / §8 verdict logic, deletes or weakens no
control, redesigns no descriptor, reopens no spectral group as a closure group, expands no generator family, and
opens **no classifier (form B) and no neural encoder (form C)**. It does **not** pivot to flat / screen geometry
and opens **no flat-geometry / screen-analysis implementation**. Everything stays offline under
`research/brainvision/` + `tests/research/`, HELD per v0.6.

This note makes **no** vision claim, **no** "Brainvision sees" claim, **no** temporal-order claim, **no**
descriptor-validity claim, **no** memory-readiness claim, **no** runtime-readiness claim, and **no**
integration-readiness claim. It touches no `torment_service/`, runtime, camera / sensor / live-capture /
screen-capture / streaming, or prompt / context / memory / action / render-body / autonomy paths, and makes
**no real-clip / local-clip move** and **no memory-system integration**. A review alone moves nothing: **no claim
lock and no verdict changes here.**

```text
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed                      = False
descriptor_validity_claim_allowed           = False
verdict                                      = HOLD
```

**No `§0` pointer; no tags.**

## 2. Relation to v1.4 preregistration

```text
v1.3a (8f1706e)  SELECTION plan: PRIMARY A + D + G; SUPPORT (report-only) B / C / E.
v1.4  (da946ed)  finite audit PREREGISTRATION: A + D + G reporting obligations + structural acceptance checks;
                 B / C / E report-only; adopting none; authorizing no code.
v1.4a (this doc) implementation AUTHORIZATION review: may a v1.5 reporting-only harness of v1.4 be authorized,
                 and what is its EXACT boundary? Recommends; authorizes nothing by itself.
```

v1.4 fixed WHAT a conformant audit must report and what makes its protocol acceptable. v1.4a asks the narrower
question: is that structure ready to be IMPLEMENTED as a reporting-only harness, and if so, under what precise,
bounded scope? It changes nothing v1.4 froze and adopts nothing.

## 3. Implementation-readiness question

```text
QUESTION:
  Is the v1.4-preregistered A + D + G audit (B / C / E report-only) ready to be implemented as a v1.5 reporting-only
  harness -- WITHOUT that implementation adopting any metric / equation / threshold / pass-fail rule, and WITHOUT
  authorizing runtime / memory / integration / real clips / vision?

ASSESSMENT (docs-only):
  - The v1.4 spine is REPRESENTABLE by identity over the frozen records: A reuses the signed offset + sign
    consistency + |smd|/TOL; D reuses the aggregation coexistence; G is a standing nine-flag guard. Nothing in the
    spine requires a new statistic, so a reporting-only harness can generate it without inventing a metric.
  - Precedent exists and is accepted: v1.2 already generated panels A-G reporting-only, non-authorizing, with a
    generic guard that breaches on any authorizing flag. v1.5 would RE-EXPRESS that under the explicit v1.4 A + D + G
    spine framing (B / C / E marked report-only) -- a structural re-presentation, not new machinery.
  - Therefore the structure appears READY for a reporting-only implementation, conditional on the exact boundary in
    §4-§9 and on explicit operator + Codex approval. Readiness of the STRUCTURE is not authorization of the CODE.
```

## 4. What v1.5 may implement (if later authorized)

```text
If -- and only if -- the operator explicitly authorizes v1.5 after this review is accepted, v1.5 MAY:
  - generate the A signed BY offset report (per by_centroid / by_spread / by_std: sign direction, sign
    consistency, magnitude relative to the frozen TOL as a DESCRIPTIVE reference);
  - generate the D aggregation anti-hiding report (whether group residual / TOL matching coexists with a systematic
    BY signed ordering; hidden closure impossible in the reporting);
  - generate the G non-authorizing guard (nine authorization flags present and False);
  - include B / C / E as REPORT-ONLY support (BY-vs-RG comparison; residual annotated by binding stat; region /
    family stratification with the single-family caveat);
  - set closure_achieved = False (UNLESS a separate, explicitly preregistered later protocol changes this -- not v1.5);
  - set frozen_brainvision_verdict = HOLD and keep all claim locks False;
  - define protocol_ok to mean ONLY that the required reporting panels and guards are present (NOT closure).
v1.5 would reuse the v0.7b / v0.8a / v0.9b / v1.0b / v1.2 records BY IDENTITY; reporting-only, form A, non-learning.
```

## 5. What v1.5 may not implement

```text
FORBIDDEN in v1.5 (any of these makes it non-conformant):
  - NO closure metric adoption; NO equation adoption; NO threshold invention.
  - NO TOL redefinition; NO offset-vs-TOL gate; NO binding gate; NO pass/fail validity gate.
  - NO descriptor redesign; NO _stats / GROUPS change; NO generator-family expansion; NO spectral reopening as closure.
  - NO promotion of B / C / E from report-only to a decision input / gate; proxy_match_residual stays frozen (C).
  - NO classifier (form B); NO neural encoder (form C).
  - NO flat-geometry / screen-analysis implementation; NO camera / live / sensor / screen-capture / streaming.
  - NO torment_service/; NO runtime / memory / integration wiring; NO real / local clips.
  - NO descriptor-validity claim; NO temporal-order claim; NO vision / "Brainvision sees" claim; NO runtime /
    memory / integration-readiness claim.
  - NO §0 pointer; NO tags; NO claim-lock or verdict movement.
```

## 6. Required files for v1.5

```text
EXACTLY two files, both offline research surfaces (no others):
  research/brainvision/run_by_aware_closure_audit_v1_5.py
  tests/research/test_brainvision_by_aware_closure_audit_v1_5.py
No other file may be created or modified by v1.5 (no torment_service/, no runtime, no docs beyond an optional
findings note gated separately). Imports limited to quarantined research surfaces (reuse of v0.8a / v0.9b / v1.0b /
v1.2 by identity); stdlib only otherwise; no torment* / service imports.
```

## 7. Required output fields

The v1.5 result object MUST expose (field names indicative; reusing the v1.2 / v1.4 shape by identity):

```text
- panels: A_signed_offset (per-BY signed_offset, sign_consistency, dominant_sign, magnitude_frac_TOL,
  offset_vs_tol_gate = False); the D aggregation record (aggregation_warning, hidden_closure_claim = False);
  the G guard (visibility_is_diagnostic_only = True + the nine authorization flags, all False);
  and B / C / E report-only panels.
- reporting_obligations: the A / D / G spine mapping + B / C / E marked support/report-only.
- protocol_ok (bool; present required reporting/guards only, NOT closure); breaches (list);
  outcome_label (reporting label); by_wall_persists (bool); closure_achieved = False (hard-wired).
- freeze / provenance flags, all as specified: reuses_*_by_identity = True; TOL = 0.0634; tol_redefined = False;
  new_closure_metric_adopted = False; pass_fail_gate_introduced = False; new_threshold_introduced = False;
  descriptor_redesign_authorized = False; generator_family_expansion_authorized = False;
  spectral_closure_reopened = False; flat_geometry_authorized = False; screen_analysis_authorized = False;
  runtime_authorized = False; memory_authorized = False; vision_claim_allowed = False;
  reporting_only = True; visibility_is_non_authorizing = True.
- claim locks (all False) + frozen_brainvision_verdict = HOLD.
These are REQUIRED FIELDS, not equations; magnitude_frac_TOL is descriptive, not a gate.
```

## 8. Required tests

`tests/research/test_brainvision_by_aware_closure_audit_v1_5.py` MUST lock only platform-independent robust facts:

```text
[ ] provenance: imports only quarantined research surfaces (no torment* / service); reuses v0.7b / v0.8a / v0.9b /
    v1.0b / v1.2 BY IDENTITY; no new samples / seeds / families / candidate generation.
[ ] spine present: A + D + G panels present; A has sign direction + consistency + magnitude_frac_TOL and
    offset_vs_tol_gate False; D has the coexistence record with hidden_closure_claim False.
[ ] guard: nine authorization flags present and False; ANY authorizing flag True (or absent) -> protocol_ok False /
    invalid_protocol_breach (a parametrized breach test over multiple flags, incl. temporal_order and
    live_or_screen_use).
[ ] support report-only: B / C / E present as support; none acts as a gate; proxy_match_residual frozen (C); no
    family expansion (E).
[ ] no adoption: TOL == 0.0634; tol_redefined / new_closure_metric_adopted / pass_fail_gate_introduced /
    new_threshold_introduced all False; closure_achieved False; label set contains no closure-positive label.
[ ] non-finite / breach / non-reproduction / incomplete panels -> invalid_protocol_breach (never evidence).
[ ] claim locks False; verdict HOLD.
Windows pytest is the source of truth; the known spectral_centroid Linux/Windows knife-edge is unrelated.
```

## 9. Protocol failure conditions

```text
v1.5 MUST return invalid_protocol_breach (protocol_ok False) on ANY of:
  - non-reproduction of the v0.7b sealed matching / non-identity reuse of the frozen records;
  - missing or incomplete A / D / G spine panels;
  - a guard that is absent, not diagnostic-only, or carries ANY authorization flag True;
  - a non-finite / extreme value in a required panel field;
  - any adopted metric / equation / threshold / TOL change / pass-fail gate / offset-vs-TOL or binding gate;
  - any promotion of B / C / E to a decision input.
A breach can NEVER become evidence, a closure, a pass, a validity claim, or a claim / verdict movement.
```

## 10. Claim-lock preservation

```text
Under EVERY v1.5 outcome (reporting_generated / gap_visible / invalid_protocol_breach):
  first_pass_structure_validity_claim_allowed = False
  temporal_claim_allowed                      = False
  descriptor_validity_claim_allowed           = False
  frozen_brainvision_verdict                  = HOLD
  vision_claim = memory_readiness_claim = runtime_readiness_claim = integration_readiness_claim = False
v1.5 moves NO claim lock and NO verdict; it is reporting-only and non-authorizing by construction.
```

## 11. Risks / ambiguity notes

```text
- REDUNDANCY vs v1.2: v1.5 re-expresses much of the accepted v1.2 panels A-G under the explicit A + D + G spine.
  Risk: divergence or drift from v1.2. Mitigation: v1.5 reuses v1.2 by identity and its tests assert value-match
  with v1.2 for the shared quantities; v1.5 adds the spine framing, not new statistics.
- SPINE-VS-PANEL LETTERING: v1.4 obligation letters (D = aggregation, F/region-family) differ from the frozen panel
  keys (D_region_family, F_residual_aggregation_warning). v1.5 must keep frozen panel keys and map the spine
  explicitly (as v1.2 did) to avoid a mislabel that looks like a new component.
- THRESHOLD CREEP VIA A / D: magnitude_frac_TOL (A) must stay descriptive with offset_vs_tol_gate False; the D
  coexistence record must stay an anti-hiding statement, not a pass/fail. Tests must assert both False.
- SUPPORT CREEP (B / C / E): the highest risk is C touching proxy_match_residual. v1.5 must keep C annotation-only
  and the residual frozen; a test must assert no residual redefinition.
- "READY" IS NOT "PROVEN": recommending v1.5 authorization says the STRUCTURE is implementable reporting-only; it
  says nothing about closure, descriptor validity, or vision. If v1.5 later cannot represent the spine without a
  threshold, that is the escalation signal to the flat opponent-plane / spatial-field question, not a metric.
- AUTHORIZATION IS THE OPERATOR'S: this review recommends; only the operator opens v1.5. No code is authorized by
  this document.
```

## 12. Recommendation

**Recommend authorizing the v1.5 reporting-only implementation harness — but ONLY IF Codex accepts this review
as-is, and ONLY on the operator's explicit approval.** The v1.4 A + D + G spine is representable reporting-only by
identity over the frozen records, precedent exists (v1.2, accepted), and the boundary in §4-§10 is precise enough
to keep v1.5 non-authorizing and metric-free. If Codex requires changes, resolve them here (docs-only) before any
code. If review finds the spine cannot be represented without an invented threshold or a family expansion,
escalate to the flat opponent-plane / spatial-field proposal instead of implementing.

```text
1. Codex review THIS implementation authorization review (docs-only; over committed edge da946ed).
2. If Codex ACCEPTS AS-IS and the operator explicitly approves, open v1.5 as a SEPARATE reporting-only
   implementation limited to the two files in §6, conforming to §4-§10 exactly (A + D + G spine; B / C / E
   report-only; closure_achieved False; protocol_ok = presence-only; claim locks False; verdict HOLD).
3. If Codex requires changes, revise THIS review (docs-only) and re-review before any code.
4. Otherwise the Brainvision prototype line stays HELD. No code, classifier (B), neural (C), runtime, memory,
   real-clip, screen, flat-geometry, §0, or tag work is recommended or authorized here.
```

Claim locks and verdict are unchanged: `first_pass_structure_validity_claim_allowed = False`,
`temporal_claim_allowed = False`, `descriptor_validity_claim_allowed = False`, `verdict = HOLD`.

## 13. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_BY_AWARE_CLOSURE_IMPLEMENTATION_REVIEW_v1.4a.md
(new, docs-only, untracked; over committed edge da946ed, reviewing whether a v1.5 reporting-only harness of the
v1.4 preregistration may be authorized and defining its exact boundary; recommends, authorizes nothing itself).

Verify that this review:
- is docs-only and implements nothing (no code/tests, no torment_service/, no runtime, no memory, no
  camera/live/sensor/screen/streaming, no real clips); keeps form B (classifier) and form C (neural) CLOSED; and
  authorizes NO flat-geometry and NO screen-analysis implementation;
- MAY recommend implementation but ADOPTS NOTHING itself -- no metric, no equation, no threshold, no TOL change, no
  pass/fail validity rule, no descriptor redesign, no family expansion, no spectral reopening;
- defines the EXACT v1.5 boundary: allowed files are exactly research/brainvision/run_by_aware_closure_audit_v1_5.py
  and tests/research/test_brainvision_by_aware_closure_audit_v1_5.py; allowed scope = generate A (signed BY offset:
  sign direction + consistency + magnitude relative to frozen TOL, offset_vs_tol_gate False) + D (aggregation
  anti-hiding; hidden closure impossible; no validity gate) + G (nine authorization flags present and False; ANY True
  -> protocol_ok False), with B / C / E report-only; closure_achieved False; verdict HOLD; claim locks False;
  protocol_ok = required reporting/guards present, NOT closure;
- forbids in v1.5: closure metric / equation / threshold / TOL change / offset-vs-TOL gate / binding gate / pass-fail
  validity gate / descriptor-validity / temporal-order / vision / runtime / memory / integration claim / B-C-E
  promotion / residual redefinition (C) / family expansion (E);
- specifies required output fields (§7), required tests (§8: provenance / spine present / guard-any-True-breaches /
  support-report-only / no-adoption / non-finite-breach / locks-verdict), protocol failure conditions (§9), and
  claim-lock preservation under every outcome (§10);
- lists the risks (§11: v1.2 redundancy / spine-vs-panel lettering / threshold creep / support creep / ready != proven
  / authorization is the operator's) and recommends authorizing v1.5 ONLY IF Codex accepts as-is AND the operator
  explicitly approves, escalating to the flat opponent-plane / spatial-field question if the spine needs a threshold /
  family;
- preserves all claim locks (first_pass_structure_validity_claim_allowed = False; temporal_claim_allowed = False;
  descriptor_validity_claim_allowed = False) and verdict = HOLD; adds no §0 pointer and no tags.

Flag any adopted metric / equation / threshold / pass-fail rule, any TOL redefinition, any descriptor redesign, any
family expansion, any spectral reopening, any offset-vs-TOL / binding gate, any B / C / E promotion, any file outside
the two allowed v1.5 files, any flat-geometry / screen-analysis / runtime / memory / real-clip authorization, any
ACTUAL implementation in this doc, any claim that closure is ACHIEVED, any descriptor-validity / vision /
temporal-order claim, or any claim-lock/verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False`, `temporal_claim_allowed = False`,
`descriptor_validity_claim_allowed = False`, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision BY-Aware Closure Implementation Review v1.4a. Docs-only authorization review; may
recommend implementation but implements nothing. Opens no implementation lane by itself; opens no classifier /
neural / screen / flat-geometry work; changes no frozen formula, gate, evaluator, or verdict; deletes or weakens no
control; redesigns no descriptor; invents no threshold; redefines no TOL; adopts no closure metric or equation;
defines the exact v1.5 reporting-only boundary (A + D + G spine, B / C / E report-only, closure_achieved False,
protocol_ok = presence-only) for SEPARATE operator authorization; keeps the gap visible not closed; makes no vision /
descriptor-validity / temporal-order / memory / runtime / integration claim; no `§0` pointer added; no tags.*

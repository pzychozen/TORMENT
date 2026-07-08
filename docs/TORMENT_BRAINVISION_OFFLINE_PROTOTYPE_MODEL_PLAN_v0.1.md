# TORMENT Brainvision Offline Prototype Model Plan v0.1

## 1. Status / quarantine and non-claims

**DOCS-ONLY plan. Non-authorizing, non-implementing. Opens no runtime, integration, or implementation lane.**
It plans a **quarantined offline prototype model** that would use the accepted Path B color-structure findings
as **one feature family**, and defines the next research direction — it **implements none of it**. Concretely
this note is:

```text
docs-only
offline / quarantined
no code yet
no torment_service/
no runtime
no camera / live capture / sensor / screen-capture / streaming
no prompt / context / memory / action / render-body / autonomy
no real clips unless separately opened later
no memory-system integration
no vision claim
no temporal-order claim
```

It **authorizes no code and no tests**, invents no threshold, defines no replacement acceptance criteria,
changes no formula / §7 anti-proxy logic / §8 verdict logic, deletes or weakens no control, and redesigns no
descriptor. `first_pass_structure_validity_claim_allowed` remains **False**, `temporal_claim_allowed` remains
**False**, `descriptor_validity_claim_allowed` remains **False**, and `verdict` remains **HOLD**. Brainvision
remains **offline / quarantined**, HELD per v0.6; it is **not proven vision** and is **not a functioning vision
layer for TORMENT memory**. **No `§0` pointer; no tags.**

## 2. Accepted inputs from Path B

Carried forward by identity from the accepted Path B closure:

```text
Path B closed at 57a57ab.
Directional axis:            directional_B_strengthened   (validity-surface mismatch candidate; unresolved)
                            directional_proxy_failure_resolved = False
Per-channel-spectral axis:   per_channel_C_strengthened    (bank-composition artifact candidate; unresolved)
                            per_channel_proxy_failure_resolved = False
Descriptor limitation:       A_descriptor_limitation_supported = False
Overall:                     verdict = HOLD
                            first_pass_structure_validity_claim_allowed = False
                            temporal_claim_allowed = False
                            descriptor_validity_claim_allowed = False
```

Path B is used here only as **evidence that the color-structure primitive is worth testing as a feature
family** — the coherent color-winding signal survived broader matched-pair attacks. It is **not** treated as
proof of vision, descriptor validity, or integration readiness. Both axes remain unresolved, the frozen §7 gate
still HOLDs, and no validity / vision / runtime / memory claim follows.

**What Path B did NOT prove:** vision; temporal order; real-video understanding; descriptor validity; memory
integration readiness; runtime readiness; "Brainvision sees".

## 3. New research question

```text
Can Brainvision descriptor families become useful input to a small offline synthetic visual-structure model?
```

Equivalently: can a small offline prototype model use Brainvision descriptor families to classify or encode
**synthetic** visual structure **better than cheap baselines**? The question is deliberately
**synthetic-first and offline**.

It is **not** asking: "Does Brainvision see?"; "Is Brainvision ready for memory?"; "Is Brainvision valid on
real clips?"; "Can it be connected to runtime?" Those remain out of scope and disallowed.

## 4. Prototype model boundary

Any future prototype (if ever implemented after a separate opening) must be:

```text
offline
deterministic
synthetic-first
under research/brainvision/  only if later implemented
under tests/research/        only if later implemented
reporting-only
non-authoritative
```

**No output may write memory, affect runtime, alter prompts, control actions, or claim perception.** The
prototype is a research probe over synthetic fixtures, not a perception system, and it carries no authority
over any TORMENT surface.

## 5. Candidate feature families

Possible feature groups a later prototype could draw from (reusing the frozen descriptors by identity if ever
implemented; nothing is built here):

```text
color-structure:
  PSC
  AIC
  S

directional:
  u_directional_delta_rms
  angular_increment_mag

per-channel-spectral:
  RG/BY centroid
  RG/BY spread
  null-relative variants

recurrence / temporal summaries (LATER-ONLY):
  DET
  RR
  LAM
  entropy-like summaries

baseline controls:
  raw movement amount
  frame-diff-style descriptors
  plain FFT / spectral summaries
  randomized / shuffled controls
```

The **recurrence / temporal summaries are later-only** and are listed for completeness only. Including them
would **not** authorize any temporal-order claim; `temporal_claim_allowed = False` stays in force, and no
feature may be used to assert temporal order.

## 6. Candidate prototype forms

```text
A. Non-learning scoring model      (fixed, interpretable scoring over the feature families)
B. Tiny classical classifier       (e.g. a small linear / tree model over the features)
C. Tiny neural encoder             (a small learned encoder)
```

**Recommended first branch: A or B first. Do not start with a neural encoder (C) unless the plan gives a
strong reason.**

**Reasoning.** A / B are **transparent, easier to falsify, and better for exposing cheap shortcuts** — exactly
what this arc has been guarding against (a feature that separates classes for the wrong reason). C has more
representation power, but is **easier to overfit and harder to interpret**, which would make shortcut detection
and honest falsification harder. Start where the evidence is most legible.

## 7. Baseline doctrine

Every future prototype must compare against **cheap baselines**:

```text
random labels / shuffled labels
movement-only
direction-only
spectral-only
per-channel-only
descriptor ablations
simple frame-diff proxy
```

State clearly:

```text
If the Brainvision feature model does not beat cheap baselines, it is not evidence of useful visual structure.
```

And equally clearly:

```text
Beating baselines is still NOT proof of vision, descriptor validity, temporal order, or memory readiness.
```

A win over baselines is a **necessary but not sufficient** signal; it advances the research question only, and
moves no claim lock and no verdict.

## 8. Synthetic task families

Start **synthetic-only**. Possible task families:

```text
coherent winding vs cancellation
smoothness-without-winding vs true winding
per-channel matched controls
directional matched controls
multi-family structure classification
held-out fixture families
cross-family generalization
```

**Important requirement.** Do **not** train and test only on trivially separable variants of the **same**
fixture family. **Prefer held-out fixture families** where possible, and report cross-family generalization —
a model that only separates within-family variants of its training set is demonstrating fixture memorization,
not useful visual structure.

## 9. Reporting rules

Future findings must report:

```text
accuracy / balanced accuracy
per-class confusion
baseline comparisons
ablation results
held-out family results
failure cases
shortcut analysis
claim locks
research-only verdict
```

**None** of the following jumps is allowed:

```text
"prototype works"            ->  "Brainvision sees"
"synthetic classifier works" ->  "memory integration"
"beats baseline"             ->  "descriptor validity"
"descriptor helps"           ->  "temporal order"
```

Every findings note must restate the claim locks
(`first_pass_structure_validity_claim_allowed = False`, `temporal_claim_allowed = False`,
`descriptor_validity_claim_allowed = False`, `verdict = HOLD`) and keep its verdict **research-only**.

## 10. Recommended next step after plan

After this docs-only v0.1 plan is accepted, the possible next slice **may** be a reporting-only prototype
implementation — **not opened here**:

```text
research/brainvision/run_offline_prototype_model_v0_2.py
tests/research/test_brainvision_offline_prototype_model_v0_2.py
docs/TORMENT_BRAINVISION_OFFLINE_PROTOTYPE_MODEL_FINDINGS_v0.2.md
```

Such a slice, if ever opened, would start with form **A or B**, compare against the §7 baselines, use §8
synthetic task families with held-out families, and report under §9 rules with all claim locks restated. It
must be **separately opened after review and explicit operator approval**; **v0.1 itself opens no code.** Real
clips / local-clip manifest and memory-system integration stay disallowed, and no §7/§8/threshold/control/
descriptor change may be made without a fresh freeze and adversarial review.

- **Codex review** of this plan and of whether it stays a bounded, offline, synthetic-first, reporting-only
  prototype plan (form A/B first, baseline-gated, claim-locked) rather than a route to a vision / validity /
  temporal / memory / runtime claim.
- **If the operator explicitly opens the next slice, it should be the v0.2 prototype (A or B first);
  otherwise HOLD.**

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False`, `temporal_claim_allowed = False`,
`descriptor_validity_claim_allowed = False`, and `verdict = HOLD` are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Offline Prototype Model Plan v0.1. Docs-only, non-authorizing. Opens no
implementation lane; changes no frozen formula, gate, or verdict; deletes or weakens no control; invents no
threshold; redesigns no descriptor; makes no vision / descriptor-validity / temporal-order claim; no `§0`
pointer added; no tags.*

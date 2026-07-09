# TORMENT Brainvision All-Shortcuts-Closed Synthesis v0.3

## 1. Status / quarantine and non-claims

**DOCS-ONLY synthesis / decision note. Non-authorizing, non-implementing. Opens no runtime, integration, or
implementation lane.** It summarizes what the v0.3 all-shortcuts-closed falsifier means, what it does not mean,
and why the current prototype line should be HELD. It **authorizes no code and no tests**, invents no
threshold, changes no formula / §7 anti-proxy logic / §8 verdict logic, deletes or weakens no control,
redesigns no descriptor, and opens **no classifier (form B) and no neural encoder (form C)**. Everything stays
offline under `research/brainvision/` + `tests/research/`, HELD per v0.6.

This note makes **no** vision claim, **no** "Brainvision sees" claim, **no** temporal-order claim, **no**
descriptor-validity claim, **no** memory-readiness claim, **no** runtime-readiness claim, and **no**
integration-readiness claim. `first_pass_structure_validity_claim_allowed` remains **False**,
`temporal_claim_allowed` remains **False**, `descriptor_validity_claim_allowed` remains **False**, and
`verdict` remains **HOLD**. It touches no `torment_service/`, runtime, camera / sensor / live-capture /
screen-capture / streaming, or prompt / context / memory / action / render-body / autonomy paths, and makes
**no real-clip / local-clip move** and **no memory-system integration**. Brainvision Path B is **not proven
vision** and is **not a functioning vision layer for TORMENT memory**. **No `§0` pointer; no tags.**

## 2. Inputs and committed edge

```text
Path B closed:            57a57ab  docs(research): close brainvision color structure path b
v0.1 plan:                0611aff  docs(research): plan brainvision offline prototype model
v0.2 scoring prototype:   06b36ce  research(brainvision): add offline prototype scoring model
v0.2 synthesis:           07752c8  docs(research): synthesize brainvision offline prototype model
v0.3 falsifier:           9877f35  research(brainvision): test all-shortcuts-closed synthetic falsifier
```

## 3. What v0.3 tested

v0.3 attempted to match or neutralize **all** cheap shortcut groups **simultaneously** between the two labels:

```text
movement / channel energy
directional proxies
spectral proxies
per-channel proxies
frame-diff proxies
```

while keeping the SAME fixed frozen rule (no learning, no label fit, no classifier, no neural encoder):

```text
structure iff PSC >= PSC_FLOOR and AIC >= AIC_FLOOR
```

## 4. What v0.3 found

```text
all_shortcuts_closed = False
construction_feasible = False
outcome = Outcome_4  (all-shortcuts-closed construction INFEASIBLE; residual shortcuts remain)
research_signal = unresolved_proxy_wall_remains
```

Key numbers (Windows source-of-truth):

```text
fixed color rule BA = 1.000        confusion = {tp:8, fn:0, fp:0, tn:5}
cheap baselines still separate:
  per_channel             = 0.9375
  movement_channel_energy = 0.8125
  directional             = 0.7375
  frame_diff              = 0.675
  spectral                = 0.700  (ill-defined: constant-chroma FFT centroid/spread are numerical noise)
ablations:
  PSC_only        = 1.000   (PSC carries the separation)
  AIC_only        = 0.500   (AIC alone fails)
  S_best_threshold = optimistic / diagnostic only (NOT the fixed model)
shuffled_label_control = 0.5011   (~chance)
```

The fixed color rule still separates the synthetic family, but the best-effort matched construction could
**not** close all five shortcut groups at once (a geometric obstruction: matching the directional per-step
increment conflicts with matching full symmetric channel coverage, leaving residual per-channel/BY differences).
Residual cheap proxies still separate, so the **proxy wall remains**.

## 5. What v0.3 did not prove

```text
not vision
not descriptor validity
not temporal order
not real-video understanding
not memory readiness
not runtime readiness
not integration readiness
not a unique color-structure advantage
```

The fixed rule's perfect separation is the **same coherent-winding-vs-cancellation signal** established in
Path B; v0.3 adds no new evidence of validity or perception, and — because cheap baselines also separate —
isolates no advantage the cheap proxies lack.

## 6. Why the prototype line should be HELD

```text
v0.2 showed a research signal (a single fixed rule generalizing across families).
v0.3 tested the decisive proxy closure.
v0.3 could not construct a clean all-shortcuts-closed family with the current generators.
Cheap residual proxies still separate.
Adding classifier / neural capacity now would LEARN or HIDE shortcuts rather than solve the proxy wall.
More code along this exact generator route risks fixture-chasing.
```

**Decision.** The current prototype line should be **HELD**. **Do not open v0.4 code immediately. Do not
proceed to form B (classifier) or form C (neural encoder).** The honest state is: the fixed color rule
separates, the proxy wall stands, and no synthetic construction available here isolates a unique
color-structure advantage.

## 7. Future-only construction proposal option

Allowed **only** as a future, separately-opened, **docs-only** proposal (not opened here):

```text
A fundamentally different synthetic construction might target the directional-increment / channel-coverage
obstruction that made the all-shortcuts-closed family infeasible.
It must be proposed FIRST (docs-only), not implemented immediately.
It must remain form A, non-learning, baseline-gated, fixed-rule, offline / quarantined.
It must report infeasibility honestly if the obstruction cannot be broken.
```

This synthesis **does not open** that proposal. It is recorded as a possibility, to be opened only if the
operator explicitly instructs it; otherwise the line stays HELD.

## 8. Claim locks and verdict

```text
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed                      = False
descriptor_validity_claim_allowed           = False
verdict                                      = HOLD
```

The frozen Brainvision §8 verdict is unchanged at **HOLD**; the v0.3 research signal
(`unresolved_proxy_wall_remains`) moves no lock and no verdict. Brainvision remains **offline / quarantined**,
HELD per v0.6. **No `§0` pointer; no tags.**

## 9. Recommended next

- **Codex review** this synthesis.
- **If accepted,** commit the synthesis doc.
- **After that,** either **HOLD** the Brainvision prototype line or **separately open a docs-only construction
  proposal** (§7). No code, classifier, neural, runtime, memory, real-clip, `§0`, or tag work is recommended.

## 10. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_ALL_SHORTCUTS_CLOSED_SYNTHESIS_v0.3.md
(new, docs-only, untracked; over committed edge 9877f35, closing the v0.3 falsifier).

Verify that this synthesis:
- is docs-only and opens no implementation (no code/tests, no new files);
- closes v0.3 as Outcome 4 (all-shortcuts-closed construction infeasible; residual shortcuts remain);
- preserves the proxy-wall-remains conclusion and does NOT overclaim the fixed color rule's BA = 1.000
  (states it is the same winding-vs-cancellation signal, not a unique advantage or validity/vision result);
- does NOT hide cheap-baseline success (per_channel 0.9375, movement 0.8125, directional 0.7375,
  frame_diff 0.675; spectral 0.700 flagged ill-defined on constant chroma) or the AIC_only = 0.500 ablation;
- keeps form B (classifier) and form C (neural encoder) CLOSED, and keeps runtime / memory / real clips /
  §0 / tags CLOSED;
- records the fundamentally-different construction only as a FUTURE, separately-opened, docs-only proposal,
  not opened here;
- preserves all claim locks (first_pass_structure_validity_claim_allowed = False; temporal_claim_allowed =
  False; descriptor_validity_claim_allowed = False) and verdict = HOLD;
- makes no vision / "Brainvision sees" / temporal-order / descriptor-validity / memory-readiness /
  runtime-readiness / integration-readiness claim.

Flag any overclaim, any implicit opening of B/C or runtime/memory/real-clips, any weakening of the
cheap-baseline caveat or the Outcome-4 infeasibility framing, or any claim-lock/verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False`, `temporal_claim_allowed = False`,
`descriptor_validity_claim_allowed = False`, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision All-Shortcuts-Closed Synthesis v0.3. Docs-only, non-authorizing. Opens no
implementation lane; opens no classifier / neural work; changes no frozen formula, gate, or verdict; deletes or
weakens no control; redesigns no descriptor; makes no vision / descriptor-validity / temporal-order / memory /
runtime / integration claim; no `§0` pointer added; no tags.*

# TORMENT Brainvision Offline Prototype Model Synthesis v0.2

## 1. Status / quarantine and non-claims

**DOCS-ONLY synthesis / decision note. Non-authorizing, non-implementing. Opens no runtime, integration, or
implementation lane.** It summarizes what the v0.2 offline prototype scoring result means, what it does not
mean, and why the next slice should stay form A. It **authorizes no code and no tests**, invents no threshold,
defines no replacement acceptance criteria, changes no formula / §7 anti-proxy logic / §8 verdict logic,
deletes or weakens no control, redesigns no descriptor, and opens **no classifier and no neural encoder**.
Everything stays offline under `research/brainvision/` + `tests/research/`, HELD per v0.6.

This note makes **no** vision claim, **no** "Brainvision sees" claim, **no** temporal-order claim, **no**
descriptor-validity claim, **no** memory-readiness claim, and **no** runtime-readiness claim.
`first_pass_structure_validity_claim_allowed` remains **False**, `temporal_claim_allowed` remains **False**,
`descriptor_validity_claim_allowed` remains **False**, and `verdict` remains **HOLD**. It touches no
`torment_service/`, runtime, camera / sensor / live-capture / screen-capture / streaming, or prompt / context /
memory / action / render-body / autonomy paths, and makes **no real-clip / local-clip move** and **no
memory-system integration**. Brainvision Path B is **not proven vision** and is **not a functioning vision layer
for TORMENT memory**. **No `§0` pointer; no tags.**

## 2. Inputs: Path B, v0.1 plan, v0.2 scoring prototype

```text
Path B closed:            57a57ab  docs(research): close brainvision color structure path b
v0.1 plan committed:      0611aff  docs(research): plan brainvision offline prototype model
v0.2 scoring prototype:   06b36ce  research(brainvision): add offline prototype scoring model
```

Path B is carried only as evidence that the color-structure primitive is worth **testing** as one feature
family (directional B strengthened but unresolved; per-channel C strengthened but unresolved;
A_descriptor_limitation_supported = False; verdict HOLD) — not as proof of vision, descriptor validity, or
integration readiness.

## 3. What v0.2 actually showed

v0.2 was a deterministic, **non-learning** form-A scoring probe (no trained weights, no label fit). The fixed
rule is:

```text
model = A_non_learning_scoring   (learning = False)
fixed_rule: structure iff PSC >= PSC_FLOOR and AIC >= AIC_FLOOR   (frozen floors; no label fit)
```

Observed (reporting-only):

- The fixed color-structure rule **separated all five synthetic families** and **generalized across families
  without fitting labels**: pooled `color_ba = 1.000`, confusion `{tp: 15, fn: 0, fp: 0, tn: 16}`.
- **No single cheap baseline generalized across all held-out families** (a movement / channel-energy threshold
  learned on the reference family generalized to F2/F3/F4 but failed on F5; a spectral threshold covered F5 but
  not F2–F4).
- The **shuffled-label control was near chance** (`shuffled_label_control_ba = 0.4982`, averaged over many
  shuffles), confirming the fixed rule carries no signal on scrambled labels.

Read minimally: a single, interpretable, non-learning rule separates these synthetic tasks and generalizes
across them, and no single cheap baseline does the same cross-family.

## 4. What v0.2 did not show

Explicitly:

```text
not vision
not descriptor validity
not temporal order
not real-video understanding
not memory readiness
not runtime readiness
not proof of a unique color-structure advantage
```

The separation is the **same coherent-winding-vs-cancellation signal Path B already established**; v0.2 adds no
new evidence of validity or perception.

## 5. Shortcut analysis

The decisive caveat: **every family was still separable by *some* cheap baseline.** v0.2 therefore does **not**
isolate a color-structure contribution that no cheap proxy can achieve.

- **F2 / F3 / F4** remain vulnerable to the **movement / channel-energy** shortcut: a cheap channel-std /
  chroma-energy threshold learned on the reference family generalizes to them.
- **F5** (channel-energy-matched) **closes the movement / channel-energy shortcut** (that baseline drops to
  chance) **but exposes other cheap shortcuts, including directional / spectral** proxies, which still separate
  it.
- **No single synthetic family closes all cheap shortcuts at once.**
- **AIC-only BA = 0.500**: angular concentration alone does not separate; **PSC carries the separation.**
- **Within-family best-threshold baselines are optimistic and overfit-prone at small N** (they can perfectly
  separate ~1e-3 feature differences on tiny samples), so cross-family generalization — not within-family — is
  the reliable comparison. (The specific optimistic baseline figures are platform-sensitive small-N stats;
  Windows pytest is the source of truth for them. The color-structure result, the research signal, and all
  claim locks are platform-independent.)

## 6. Why not classifier / neural yet

Forms B (tiny classical classifier) and C (tiny neural encoder) are **not** opened, because they would add
capacity **before the proxy wall is closed**:

- A **classifier** could **learn fixture shortcuts** — exactly the cheap proxies §5 shows are still present.
- A **neural encoder** could **hide confounds** inside a learned representation, making shortcut detection and
  honest falsification harder.
- The honest next step is therefore **not more model power; it is better falsification** — a task that removes
  the cheap proxies, tested with the same non-learning rule.

## 7. Recommended next slice (not opened here)

Recommend a separate, future, **still form-A** slice:

```text
Brainvision all-shortcuts-closed larger-N synthetic task
```

It should attempt to **match or neutralize simultaneously**:

```text
movement / channel energy
directional proxies
spectral proxies
per-channel proxies
frame-diff proxies
```

using:

```text
larger N
held-out fixture families
cross-family generalization
the fixed frozen color rule (PSC >= PSC_FLOOR and AIC >= AIC_FLOOR; no label fit)
the same claim locks
the same baseline doctrine (must beat cheap baselines; beating them is still not proof)
```

Only if the fixed color rule still separates when **all** cheap proxies are simultaneously neutralized (at
larger N, cross-family) would there be a first honest signal of a color-structure contribution beyond cheap
proxies — and even then it would remain a research signal, not a vision / validity / temporal / memory /
runtime claim. This synthesis **opens no implementation**; it only records the recommended next slice, to be
separately opened after review. If any all-shortcuts-closed family proves infeasible to construct, that must be
reported as infeasible, not worked around. Classifier / neural (forms B / C), real clips, and memory-system
integration stay disallowed until a separate future gate.

## 8. Claim locks and verdict

```text
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed                      = False
descriptor_validity_claim_allowed           = False
verdict                                      = HOLD
```

The frozen Brainvision §8 verdict is unchanged at **HOLD**; the v0.2 research signal moves no lock and no
verdict. Brainvision remains **offline / quarantined**, HELD per v0.6. **No `§0` pointer; no tags.**

## 9. Recommended next

- **Codex review** of this synthesis, checking that it: is docs-only; opens no implementation; opens no
  classifier / neural work; does not overclaim v0.2; preserves the cheap-baseline caveat (every family still
  separable by some cheap baseline); recommends the all-shortcuts-closed larger-N synthetic task **only** as a
  future, separately-opened, still-form-A slice; and preserves all claim locks and HOLD.
- **If the operator explicitly opens the next slice, it should be that all-shortcuts-closed larger-N form-A
  task; otherwise HOLD.**

*End — TORMENT Brainvision Offline Prototype Model Synthesis v0.2. Docs-only, non-authorizing. Opens no
implementation lane; opens no classifier / neural work; changes no frozen formula, gate, or verdict; deletes or
weakens no control; redesigns no descriptor; makes no vision / descriptor-validity / temporal-order / memory /
runtime claim; no `§0` pointer added; no tags.*

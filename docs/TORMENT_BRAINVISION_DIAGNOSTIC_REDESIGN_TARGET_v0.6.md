# TORMENT Brainvision Diagnostic-Redesign Target v0.6

## 1. Status / why this is a target note (not implementation)

**DOCS-ONLY planning/target note. Non-authorizing, non-implementing. Opens no implementation lane and no
service integration.** Its only job is to **freeze the acceptance target before any future tuning or math
redesign**, so that a later diagnostic cannot be judged against goalposts moved after the fact. It adds no
math, changes no code, touches no tests. Work stays quarantined under `research/brainvision/` +
`tests/research/`; no `torment_service/` imports; no service / runtime / camera / sensor / live-capture /
prompt / context / memory / action / render-body / autonomy contact. **No `§0` pointer; no tags.**

## 2. What v0.4 / v0.5 taught

The v0.3 observation — repeatable κ>0 SAG amplification across clip1–clip9 (69/72 true windows amplified,
κ=0 coherent at 1.000) — **remains observed and repeatable under the current offline descriptor-field
diagnostic.** But the v0.4/v0.5 controls showed it is **not temporal-order-specific.** Across clip1–clip9:

| Condition       | Windows amplifying |
|-----------------|:------------------:|
| true            | 69/72              |
| time_shuffled   | 71/72              |
| time_reversed   | 71/72              |
| circular_shift  | 70/72              |

with `time_shuffled` median ≥ `true` median on **9/9** real clips. Conclusion carried forward: the current
SAG diagnostic supports **repeatable descriptor-field amplification, not temporal-order-specific
recursive-time survival**, and it is (at most) *compatible with* sensitivity to properties preserved under
shuffle / reversal / shift. Any future diagnostic must clear the bar the current one failed.

## 3. Future diagnostic acceptance criteria (predeclared)

A future Brainvision diagnostic may only claim temporal-order sensitivity if, **predeclared before it is
run**, it satisfies all of:

- **Controls predeclared:** true / time-shuffled / time-reversed / circular-shift controls are declared and
  run for every clip, before results are inspected.
- **True must beat the temporal controls by robust statistics — especially the median:** true windows must
  exceed the temporal/null controls on median (and other robust summaries), not merely tie or lose as they
  do now.
- **Spike-heavy means are insufficient:** a large mean driven by one or few extreme windows does not count;
  the effect must hold on medians and amplifying-window counts, not on outlier maxima.
- **κ=0 must remain coherent:** the fixed-clock baseline must stay at/near 1.000; a diagnostic whose κ=0
  baseline itself amplifies is invalid.
- **Heterogeneous clips:** success must be shown across a heterogeneous set of prerecorded clips (varied
  content, motion, cuts, lengths, degraded/low-structure), not a single favorable clip.
- **Empirical disruption is mandatory:** temporal-order claims may resume only if the diagnostic is
  **empirically disrupted by shuffle/reversal controls** — i.e., destroying temporal order must measurably
  destroy the effect. If shuffled/reversed still amplify, no temporal-order claim.

## 4. Explicit forbidden moves

Until a diagnostic meeting §3 is predeclared and reviewed, the following are forbidden: no runtime
integration; no live capture; no service / prompt / context / memory / action / render-body / autonomy
contact; **no `§0` pointer; no tags;** and **no theory inflation** — no new mechanism claims (e.g.
"spectral richness", "return structure", "recursive-time survival") beyond what controls establish, and no
new math or parameter tuning introduced under cover of this planning note.

## 5. Recommended state after this note

**Brainvision HOLD** — remain at the offline research boundary, with the controls-downgraded interpretation
of record (v0.4/v0.5), until a **predeclared diagnostic redesign is proposed** that targets the §3
criteria. Reopening the temporal-order line is a deliberate, reviewed step, not a momentum continuation.
The harness, controls wrapper, and findings notes stand as-is; nothing new is opened by this note.

*End — TORMENT Brainvision Diagnostic-Redesign Target v0.6. Docs-only, non-authorizing. Opens no
implementation lane; no `§0` pointer added; no tags.*

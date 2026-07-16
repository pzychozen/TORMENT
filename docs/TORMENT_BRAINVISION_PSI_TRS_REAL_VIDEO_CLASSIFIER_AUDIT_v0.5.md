# TORMENT Brainvision ΨTRS Real-Video Classifier Audit v0.5

## 1. Status / quarantine

**DOCS-ONLY research audit note. Non-authorizing, non-implementing. Opens no implementation lane and no
service integration.** This note records the current **bounded interpretation** of the prerecorded
true-versus-shuffled *classifier* (the reported balanced-accuracy values) produced by
`research/brainvision/run_real_video_descriptors.py`. It **complements** — and does not erase — the
historical findings in `TORMENT_BRAINVISION_PSI_TRS_REAL_VIDEO_FINDINGS_v0.1/v0.2/v0.3.md` (which already
flagged classification as *secondary / saturated*) and the SAG-controls downgrade in
`TORMENT_BRAINVISION_PSI_TRS_REAL_VIDEO_CONTROLS_FINDINGS_v0.4.md`. Those documents' historical outputs
stand as recorded; this note only adds the classifier's present standing. Work stays quarantined under
`research/brainvision/` + `tests/research/`; no `torment_service/` imports; no service / runtime / camera /
sensor / live-capture / prompt / context / memory / action / render-body / autonomy contact. **No new
math, no parameters tuned, no code / tests / `.npz` inputs / result artifacts / benchmark output touched.
No `§0` pointer added; no tags.**

## 2. What was audited

A **read-only source-and-data audit** of the prerecorded true-versus-shuffled classifier in
`research/brainvision/run_real_video_descriptors.py`. Scope is the classifier construction and its reported
balanced accuracies only — not the SAG amplification numbers (covered by v0.3/v0.4) and not any other
Brainvision evaluation family.

## 3. Classifier construction (as built in source)

The self-supervised true-versus-shuffled task is assembled as:

```text
Xr = one feature vector from each true 64-row descriptor window
Xs = one feature vector from the same window after deterministic row permutation
X  = Xr + Xs
y  = [1] * 8 + [0] * 8
```

with windowing `window length = 64`, `stride = 32`. It follows that:

- adjacent windows **overlap by 32 rows**;
- each true/shuffled pair **shares all 64 source rows** (same window, one permuted);
- the paired opposite-class sample **remains in the training set during every leave-one-out (LOO) fold**;
- standardization is **fitted on the complete 16-sample matrix before LOO**.

## 4. Audit disposition

```text
C. TASK HAS PAIRED-SAMPLE OR VALIDATION DEPENDENCE
```

## 5. Bounded interpretation of the reported balanced accuracies

The existing prerecorded balanced-accuracy values are valid **only** as:

```text
paired shuffle-disruption engineering diagnostics
```

They are **not** valid as, and must not be cited as:

- independent cross-validation estimates;
- recursive-time contribution estimates;
- temporal-order validation;
- arrow-of-time evidence;
- perception or visual-understanding evidence.

## 6. Observed consequences

```text
psi_trs beats psi_trs_k0 on 0/9 clips
psi_trs ties  psi_trs_k0 on 8/9 clips
psi_trs loses to psi_trs_k0 on 1/9 clips

external SAG-control context (outside this classifier audit's scope):
time-shuffled SAG median exceeds true SAG median on 9/9 clips
```

`frame_diff` and `plain_fft` frequently **saturate** because the permutation introduces artificial adjacent
discontinuities and spectral redistribution — an artifact of the shuffle, not a discrimination of temporal
order. (This is consistent with the "classification saturated / secondary" note already in v0.2 §4 and v0.3
§5, and with v0.4's finding that shuffled/reversed controls amplify like true windows.)

## 7. `descriptor_only` — corrected standing

`descriptor_only` is **not** dead or information-free. The audit established that its true and shuffled
paired feature vectors are **equal to floating tolerance**. In LOO the paired counterpart remains
associated with the **opposite** class, producing complete prediction inversion:

```text
tn = 0
fp = 8
fn = 8
tp = 0
balanced accuracy          = 0.000
inverted balanced accuracy = 1.000
```

Standing:

```text
descriptor_only = ORDER-INVARIANT PAIRED-TASK DEGENERACY
0.000 BA = systematic evaluation artifact
```

The inverted accuracy (1.000) is **not** a valid recovered result — it is the mechanical mirror of the same
paired-task degeneracy and must not be treated as recovered signal.

## 8. `clip5_static` — corrected standing

`clip5_static.npz` is **not** byte-identical static input:

```text
300 raw frames
300 unique raw frame rows
300 unique derived descriptor rows
```

"Static" is only a **source-content category**, not a statement that the frames or descriptor rows repeat.
Its perfect shuffled separation is explained by **permutation-induced discontinuities and
spectral/trajectory redistribution**, including separation that also appears in the **non-recursive**
`psi_trs_k0`. Therefore:

```text
clip5_static perfect classification
  != recursive-time evidence
  != temporal-order evidence
```

## 9. Scope limitation

This correction applies **only** to the prerecorded real-video classifier path
(`run_real_video_descriptors.py`) and its reported balanced accuracies. It does **not** automatically
invalidate:

- synthetic falsifier balanced accuracies;
- recurrence / DET analysis;
- SAG numeric amplification;
- other Brainvision evaluation families.

Each of those requires **separate construction-specific analysis**.

## 10. Standing to preserve

```text
engineering replay health           = STRONG
recursive-time isolation            = ABSENT
temporal-order specificity          = NOT DEMONSTRATED
prerecorded classifier independence = FALSE
classifier scientific standing      = DIAGNOSTIC ONLY

FORMAL HOLD active
Mode 0 active
verdict = HOLD

bounded_experiment_ready            = False
Brainvision_perceptual_claim_ready  = False
runtime_integration_authorized      = False
new_scientific_claim_authorized     = False
```

## 11. Non-claims

This note does **not**: prove ΨTRS classifier superiority; prove a working vision system; prove video or
visual understanding; establish recursive-time isolation or temporal-order specificity; authorize runtime
integration; authorize camera / sensor / live capture; authorize prompt / context / memory / action /
render-body / autonomy contact. Brainvision remains offline research on prerecorded `.npz` under
`research/brainvision/` + `tests/research/`. Historical results in v0.1–v0.4 are preserved as recorded;
only their current bounded interpretation is added here.

*End — TORMENT Brainvision ΨTRS Real-Video Classifier Audit v0.5. Docs-only, non-authorizing. Opens no
implementation lane; no `§0` pointer added; no tags.*

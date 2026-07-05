# TORMENT Brainvision ΨTRS Real-Video Controls Findings v0.4

## 1. Status / quarantine

**DOCS-ONLY research findings update. Non-authorizing, non-implementing. Opens no implementation lane and
no service integration.** This note **caveats and downgrades the interpretation** of
`TORMENT_BRAINVISION_PSI_TRS_REAL_VIDEO_FINDINGS_v0.3.md`; it does **not** erase v0.3's numbers. Work stays
quarantined under `research/brainvision/` + `tests/research/`; no `torment_service/` imports; no service /
runtime / camera / sensor / live-capture / prompt / context / memory / action / render-body / autonomy
contact. **No `§0` pointer added; no tags.** No new math; no parameters tuned.

## 2. What v0.3 claimed numerically

v0.3 recorded that κ>0 multi-window SAG amplified in 69/72 windows across clip1–clip9 (v0.2 clips + a
five-clip adversarial stress set), while the fixed clock `G(k=0)` stayed coherent at 1.000. Those counts
**remain numerically true.** v0.3's temporal-order interpretation of that survival is what this note corrects.

## 3. What v0.4 controls tested

A research-only controls wrapper (`research/brainvision/run_real_video_sag_controls.py`, with
`tests/research/test_brainvision_sag_controls_v0_4.py`; existing v0.5.1 route untouched; 52 tests pass)
re-runs the **existing** multi-window SAG on each descriptor window and on temporal/null controls of that
window: **true / time-shuffled / time-reversed / circular-shift** (plus channel-shuffle and
descriptor-dropout as extras). The question: does κ>0 amplification require *true temporal order*, or does
it survive destroying/altering that order? If shuffled/reversed windows amplify like true windows, the
temporal-order interpretation fails.

Controls were run on the **v0.3 stress set (clip5_static through clip9_degraded), not on clip1–clip4.**
This is enough to force the caveat because the adversarial stress set itself failed the temporal-order
specificity test; it does **not** imply all nine clips were control-tested.

## 4. Controls results — stress set (median G(k>0), amplifying windows)

| Clip           | true med (amp) | time_shuffled med (amp) | time_reversed med (amp) | circular_shift med (amp) |
|----------------|:--------------:|:-----------------------:|:-----------------------:|:------------------------:|
| clip5_static   | 11.204 (7/8)   | 56.379 (8/8)            | 25.736 (8/8)            | 33.352 (8/8)             |
| clip6_chaotic  | 16.963 (8/8)   | 23.843 (8/8)            |  9.756 (8/8)            | 11.130 (8/8)             |
| clip7_hardcut  | 40.023 (8/8)   | 49.544 (8/8)            | 24.406 (8/8)            | 14.947 (8/8)             |
| clip8_periodic | 17.040 (8/8)   | 45.729 (8/8)            | 22.299 (8/8)            | 18.068 (7/8)             |
| clip9_degraded | 37.185 (8/8)   | 42.473 (7/8)            | 15.666 (8/8)            | 83.518 (8/8)             |

`G(k=0)` stayed coherent at 1.000 across all controls. (channel_shuffle and descriptor_dropout also
amplified in 7–8/8 windows on every clip.)

## 5. Key finding

**Shuffled, reversed, and circular-shifted controls amplify like true windows.** Every control amplified in
7–8 of 8 windows on every stress clip, and **`time_shuffled` median ≥ `true` median on 5/5 stress clips**
(clip5 56.4 ≥ 11.2, clip6 23.8 ≥ 17.0, clip7 49.5 ≥ 40.0, clip8 45.7 ≥ 17.0, clip9 42.5 ≥ 37.2).
`time_reversed` still amplified 8/8 on all five clips even where its median was lower than true. Therefore
the κ>0 amplification is **not specific to true temporal order** under the current diagnostic.

## 6. Downgrade / caveat to v0.3

> κ>0 SAG amplification remains repeatable, but current SAG controls show the amplification is **not
> specific to true temporal order**. The current diagnostic appears sensitive to descriptor-field
> properties preserved under shuffle/reversal/shift, so v0.3 should be interpreted as **field-amplification
> evidence, not temporal-order evidence.**

Accordingly, the following v0.3-style phrasings are **not supported by controls** and must be avoided or
explicitly marked unsupported: "return structure", "temporal recurrence", "ordered recursive-time signal",
"time-structure survival", and any claim that SAG survival demonstrates temporal-order sensitivity.

What still survives: the offline harness and controls wrapper work; `G(k=0)` stays coherent at 1.000; κ>0
amplification is repeatable; the amplification is repeatable under the current offline descriptor-field diagnostic; and Brainvision has
produced useful **falsification** evidence about its own claim. **Mechanism is not proven** — this is
*compatible with* field / spectral-richness sensitivity (properties preserved by the temporal controls),
but we do not assert spectral richness as the established cause.

## 7. Non-claims

This does **not**: prove a working vision system; prove classifier superiority; prove temporal-order
sensitivity; authorize runtime integration; authorize service / camera / sensor / live capture; authorize
prompt / context / memory / action / render-body / autonomy contact. **No `§0` pointer; no tags.**
Brainvision remains offline research on prerecorded `.npz` under `research/brainvision/` + `tests/research/`.

## 8. Recommended next

- **Codex review of the downgrade wording** — confirm §5/§6 do not over- or under-state what the controls
  establish.
- **Optional: run the controls wrapper on clip1–clip4** for completeness (the v0.2 clips were not
  control-tested here), so the caveat can speak to all nine clips if desired.
- **No new math** until this v0.4 caveat is documented and reviewed. A future direction, if pursued, would
  need a diagnostic that is predeclared and empirically disrupted by shuffle/reversal controls before any temporal-order claim can be
  made again.

*End — TORMENT Brainvision ΨTRS Real-Video Controls Findings v0.4. Docs-only, non-authorizing. Opens no
implementation lane; no `§0` pointer added; no tags.*

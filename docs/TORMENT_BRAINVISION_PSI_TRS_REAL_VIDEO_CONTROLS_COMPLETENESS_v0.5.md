# TORMENT Brainvision ΨTRS Real-Video Controls Completeness v0.5

## 1. Status / quarantine

**DOCS-ONLY research findings update. Non-authorizing, non-implementing. Opens no implementation lane and
no service integration.** This note extends the v0.4 controls caveat
(`TORMENT_BRAINVISION_PSI_TRS_REAL_VIDEO_CONTROLS_FINDINGS_v0.4.md`) from the stress set (clip5–clip9) to
the **full clip1–clip9 real-video arc**. Work stays quarantined under `research/brainvision/` +
`tests/research/`; no `torment_service/` imports; no service / runtime / camera / sensor / live-capture /
prompt / context / memory / action / render-body / autonomy contact. **No `§0` pointer added; no tags.**
No new math; no parameters tuned.

## 2. Purpose

v0.4 ran the controls wrapper on the stress set only. It has now also been run on the earlier clip1–clip4
set, so the temporal-order downgrade can be stated over **all nine real clips** rather than five. This note
records that completeness; it changes no interpretation direction, only its scope.

## 3. Controls results — clip1–clip4 (median G(k>0), amplifying windows)

| Clip  | true med (amp) | time_shuffled med (amp) | time_reversed med (amp) | circular_shift med (amp) |
|-------|:--------------:|:-----------------------:|:-----------------------:|:------------------------:|
| clip1 | 13.999 (8/8)   | 57.291 (8/8)            | 28.690 (8/8)            | 19.462 (8/8)             |
| clip2 | 21.810 (8/8)   | 27.544 (8/8)            |  8.890 (8/8)            | 17.282 (7/8)             |
| clip3 |  9.124 (7/8)   | 34.314 (8/8)            | 11.344 (7/8)            | 30.138 (8/8)             |
| clip4 | 21.965 (7/8)   | 59.243 (8/8)            | 34.365 (8/8)            | 28.133 (8/8)             |

(channel_shuffle and descriptor_dropout also amplified in 7–8/8 windows on each clip.) Consistent with all
prior summaries, `G(k=0)` stayed coherent at 1.000.

## 4. Combined real-video arc (clip1–clip9)

| Condition       | Windows amplifying |
|-----------------|:------------------:|
| true            | 69/72              |
| time_shuffled   | 71/72              |
| time_reversed   | 71/72              |
| circular_shift  | 70/72              |

**`time_shuffled` median ≥ `true` median on 9/9 real clips.** By amplifying-window count, temporal/null controls match or exceed true windows across the whole arc; additionally, `time_shuffled` median >= `true` median on 9/9 real clips.

## 5. Interpretation (downgrade now spans all nine clips)

- v0.3's **numeric amplification result remains observed and repeatable under the current offline descriptor-field
  diagnostic** (κ>0 amplification is repeatable; κ=0 stays coherent at 1.000).
- The **temporal-order interpretation is now downgraded across all nine clips**, not only the stress set.
- The current SAG diagnostic **does not distinguish true temporal order from shuffled / reversed / shifted
  controls**; time-shuffled controls amplify at least as strongly as true by median on 9/9 real clips.
- Therefore the current evidence supports **repeatable descriptor-field amplification under the current SAG diagnostic, not
  temporal-order-specific recursive-time survival.**

**Mechanism is not proven.** This is *compatible with* the diagnostic being **sensitive to properties
preserved under shuffle / reversal / shift**; we do **not** assert spectral richness as the established
cause. Brainvision is neither dead nor solved — the harness produced useful **falsification** evidence
about its own claim, and the confound is now documented over the full arc.

## 6. Non-claims

This does **not**: prove classifier superiority; prove working vision; prove video understanding; prove
temporal-order sensitivity; authorize runtime integration; authorize service / camera / sensor / live
capture; authorize prompt / context / memory / action / render-body / autonomy contact. **No `§0` pointer;
no tags.** Brainvision remains offline research on prerecorded `.npz` under `research/brainvision/` +
`tests/research/`.

## 7. Recommended next

- **Codex adversarial review of this v0.5 downgrade wording** — confirm §4/§5 neither over- nor
  under-state what the full-arc controls establish.
- **Then HOLD, or a predeclared diagnostic-redesign planning note** (docs-only), stating the failure
  target explicitly.
- **No new math or tuning** until that failure target is defined: any future diagnostic must be
  **predeclared and empirically disrupted by shuffle/reversal controls** before temporal-order claims
  resume.

*End — TORMENT Brainvision ΨTRS Real-Video Controls Completeness v0.5. Docs-only, non-authorizing. Opens no
implementation lane; no `§0` pointer added; no tags.*

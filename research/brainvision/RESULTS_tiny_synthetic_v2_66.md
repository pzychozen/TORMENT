# Tiny Synthetic Target — Repaired-Control Cheap-Baseline Run Report (v2.66 preregistration)

**Offline / quarantined. Cheap baselines only. NO Brainvision-style reading was implemented, imported, or run.**

Harness: `research/brainvision/tiny_relational_synth_v2_66.py`
Tests: `tests/research/test_brainvision_tiny_relational_synth_v2_66.py`
Rule applied: **v2.66 only**, unchanged. Fresh seeds (the v2.65 target scores had been seen). No threshold, chance band,
sample count, split, or decision rule was altered. The two declared modifications (M1 B6 identity repair; M2 B5 spectral
repair) were fixed **before** any new data existed and both **strengthen** cheap baselines only.

---

## 1. Repaired positive control (v2.66 §3)

Repaired control: relation **not lockstep** and **not swap-invariant** (φ = π/2); the two elements kept **distinct**
throughout by rejection sampling on minimum separation (R1); matching switched off **only** on axes irrelevant to the
certified capability (class-TWO brightness and speed).

Bar: every cheap baseline **≥ 0.90**; the random control **must** sit at chance in `[0.40, 0.60]`.

```text
B1  colour / intensity                 1.0000   PASS
B2  frame-difference                   1.0000   PASS
B3  static single-frame descriptor     1.0000   PASS
B4  random / control                   0.5087   at chance (harness OK)
B5  simple spectral (FFT)              0.7544   FAIL  -- below the 0.90 bar
B6  cheap relational  (repaired)       1.0000   PASS
B7  combined cheap baseline            1.0000   PASS

POSITIVE CONTROL: FAILED (B5)
```

**M1 worked.** The repaired B6 clears the control at 1.0000 — on a control that, unlike v2.65's, *requires* the two
elements to be told apart. **M2 did not.** The strengthened B5 moved from one side of the bar to further below it
(0.886 → 0.7544 on a different, harder control); it does not meet the bar it was strengthened to meet.

## 2. Target task — cheap baselines (all reported, losers included)

```text
B1  colour / intensity                 0.4695
B2  frame-difference                   0.5402
B3  static single-frame descriptor     0.4848
B4  random / control                   0.5087   at chance (harness OK)
B5  simple spectral (FFT)              0.5106
B6  cheap relational  (repaired)       0.9653
B7  combined cheap baseline            0.9598

Chance = 0.5000    DEAD bar = 0.6500
```

## 3. Verdict — by the v2.66 rule, and nothing else

```text
VERDICT = UNINFORMATIVE
```

The rule is explicit and ordered: **if any required positive-control check fails, the verdict is UNINFORMATIVE.** B5
failed the bar, so the run stops there. **The failure is not banked**, and no repair is made now. Any further repair
belongs in another preregistration, before more data.

**No Brainvision-style reading was run.** Not on the control, not on the target, not informally.

## 4. Target-task scores are reported, not interpreted

The target-task scores above are reported because v2.66 requires all baselines to be reported, including losers.

Because the repaired positive control failed, those target-task scores are not interpreted. They do not make the task
DEAD, do not show that the task is cheaply solvable, do not count as evidence for or against the target, and do not
support any Brainvision claim. The only assigned verdict is UNINFORMATIVE.

## 5. Two harness observations — not results about the task

**(a) B5 has now missed the bar twice.** Its strengthening (M2) did not reach 0.90 on the repaired control. That is the
preregistration failing to specify a capable spectral baseline, twice — a defect in **our** design, recorded and not
repaired here.

**(b) The failed control gate prevents target-task interpretation.** The control gate runs before DEAD / NO CONCLUSION /
ELIGIBLE assignment, so this run provides no target verdict. The target scores are reported for completeness only; they
are not decisive in either direction and are not a basis for changing the order here. Any proposal to alter the order
belongs only in a separate preregistration and must not treat this run as support.

## 6. What this run does not claim

```text
No Brainvision claim.            No vision claim.           No primitive validation.
No geometry validation.          No descriptor validation.  No memory-bridge validation.
No stream-to-context validation. No runtime / screen / integration readiness.
No evidence about streams, colour, or the world.
No eligibility of any kind was created. ELIGIBLE was not returned and is not implied.

PRIMITIVE SELECTION REMAINS UNRESOLVED.
MEMORY INTEGRATION IS NOT AUTHORIZED.
verdict = HOLD -- all claim locks unchanged and False.
```

# Tiny Synthetic Target — Cheap-Baseline Run Report (v2.65 preregistration)

**Offline / quarantined. Cheap baselines only. NO Brainvision-style reading was implemented, imported, or run.**

Harness: `research/brainvision/tiny_relational_synth_v2_65.py`
Tests: `tests/research/test_brainvision_tiny_relational_synth_v2_65.py`
Rule applied: **v2.65 only**, unchanged. No threshold, seed, sample count, split, baseline, or rule was altered at any
point after data existed.

**Conformance fix (not a retune).** The first implementation checked the random control B4 only for being *above*
chance. v2.65 requires B4 to sit **at chance on both variants**, and a **below-chance** random control is
harness-broken exactly as an above-chance one is. The check is now a two-sided band, `[0.40, 0.60]`, applied to the
easy variant **and** to the target task; either side, or either variant, forces `UNINFORMATIVE`. This corrects the
*implementation* to match the preregistration; it changes **no** preregistered constant, threshold, seed, sample count,
split, baseline, or rule. **It does not move the verdict** — B4 scored 0.5083 on both variants, inside the band. Had it
moved the verdict, the honest response would have been to stop and re-preregister, not to keep a post-result change that
altered the outcome.

---

## 1. Easy-control positive check (v2.65 §3a)

Easy variant: relation made blatant (lockstep), matching constraints switched off.
Bar: every cheap baseline **≥ 0.90** test balanced accuracy; the random control **must** sit at chance.

```text
B1  colour / intensity                 1.0000   PASS
B2  frame-difference                   1.0000   PASS
B3  static single-frame descriptor     1.0000   PASS
B4  random / control                   0.5083   at chance, inside [0.40, 0.60] (exempt from the bar; harness OK)
B5  simple spectral (FFT)              0.8860   FAIL  -- below the 0.90 bar
B6  cheap relational                   0.9950   PASS
B7  combined cheap baseline            1.0000   PASS

POSITIVE CONTROL: FAILED (B5)
```

## 2. Target task — cheap baselines (all reported, losers included)

```text
B1  colour / intensity                 0.4955
B2  frame-difference                   0.5258
B3  static single-frame descriptor     0.5054
B4  random / control                   0.5083   at chance, inside [0.40, 0.60] (harness OK)
B5  simple spectral (FFT)              0.5133
B6  cheap relational                   0.5087
B7  combined cheap baseline            0.5269

Chance = 0.5000
```

## 3. Verdict — by the v2.65 rule, and nothing else

```text
VERDICT = UNINFORMATIVE
```

**Because B5 failed the easy-control check, no baseline failure on the target task can be interpreted.** We do not know
that B5 *could* have succeeded, so its result — and, by the preregistered rule, the run — carries no information.

Per v2.65 §3a and §5: **stop this run; do not bank the failure.** A repaired baseline belongs only in a **later,
separately gated preregistration, before new data exists.** Nothing here is repaired, retuned, or rerun.

**No Brainvision-style reading was run.** Not on the target, not on the easy variant, not informally, and not to look.

## 4. Two observations about the harness — not about the task

Recorded for a possible future preregistration. **Neither is a result about streams, and neither may be treated as
one.**

**(a) The preregistration was too weak — an outcome v2.65 pre-accepted.** The bar for B5 was fixed in advance and B5
landed just under it. That is exactly what a preregistered bar is for: it is arbitrary, it was fixed before data, and it
is binding. It cannot now be relaxed to 0.88 because 0.886 is the number we happened to see.

**(b) The easy control does not exercise the capability the target requires.** The easy variant makes the relation
blatant by putting the two elements in lockstep. In that case the cheap relational baseline (B6) does not need to keep
the two elements *distinct* to see the relation. On the target task, where the relation is a constant angular offset,
it does — and the target scores show B6 at chance despite passing the easy control at 0.995. **A baseline can pass this
positive control and still be incapable on the target.** That is a defect in the *control*, not a finding about the
task, and it means the run could not have been informative even if B5 had passed.

**Consequence, stated plainly:** the preregistered positive control did not do the job it was added to do. Any future
preregistration would need an easy variant that exercises the same capability the target demands. **That is a decision
for the operator and a separate gated slice. It is not taken here.**

## 5. What this run does not claim

```text
No Brainvision claim.            No vision claim.           No primitive validation.
No geometry validation.          No descriptor validation.  No memory-bridge validation.
No stream-to-context validation. No runtime / screen / integration readiness.
No evidence about streams, colour, or the world. These are facts about ONE artificial task and ONE harness.

PRIMITIVE SELECTION REMAINS UNRESOLVED.
MEMORY INTEGRATION IS NOT AUTHORIZED.
verdict = HOLD -- all claim locks unchanged and False.
```

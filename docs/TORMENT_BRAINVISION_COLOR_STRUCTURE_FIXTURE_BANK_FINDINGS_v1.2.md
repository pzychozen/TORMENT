# TORMENT Brainvision Color Structure Fixture-Bank Findings v1.2

## 1. Status / quarantine and non-claims

**DOCS-ONLY findings / reflection note. Non-authorizing, non-implementing.** It records what the accepted
v1.1 fixture-bank implementation (commit `58cd57f`) shows, what it does not show, and what next
research decision should be considered. It **authorizes no code and no tests**, changes no formula, and modifies no
existing diagnostic. Everything discussed stays offline under `research/brainvision/` + `tests/research/`,
HELD per v0.6.

This note makes **no** vision claim, **no** "Brainvision sees" claim, and **no** temporal-order claim.
`first_pass_structure_validity_claim_allowed` remains **False** and `temporal_claim_allowed` remains
**False**. It touches no `torment_service/`, runtime, camera / sensor / live-capture / screen-capture /
streaming, or prompt / context / memory / action / render-body / autonomy paths, and makes **no real-clip /
local-clip move**. **No `§0` pointer; no tags.**

## 2. What the v1.1 implementation is

The v1.1 fixture-bank slice (implementation commit `58cd57f`) added two quarantined files:

- `research/brainvision/run_color_structure_fixture_bank_v1_1.py`
- `tests/research/test_brainvision_color_structure_fixture_bank_v1_1.py`

It **reuses the frozen v0.8 diagnostic logic rather than reimplementing it** — `structure_score` (`PSC`,
`AIC`, `S`), the anti-proxy statistic set and Spearman gauntlet, the trajectory-order-permuted null
semantics, the neutral controls, and the §7/§8 pass/HOLD/FAIL rule are all imported by identity from
`run_color_structure_v0_8`. **No formula, constant, gate, or verdict rule was changed.** The only new
thing is the *contents* of the fixture bank: the predeclared A–H families from the v1.1 implementation
spec (`8335395`), instantiated to intentionally separate winding coherence from directional smoothness,
chroma magnitude, and per-channel spectral spread/centroid (A↔D paired over chroma magnitude, B↔E paired
over spectral spread; C smooth non-winding; F winding with centroid/spread perturbation; G
trajectory-order-permuted nulls with a bounded predeclared guard; H neutral/floor reused from v0.8 and
excluded from the anti-proxy bank).

Two fixture defects were caught and fixed **before** commit (adversarial review):

- **Class D leak.** One `D_struct_mid` draw crossed the `PSC` floor (reported as winding), violating
  Class D's "high-chroma structureless / non-winding" role; its predeclared seed was changed so all three
  Class-D fixtures are non-winding by the signed-turn `c(t)` (now locked by a dedicated test).
- **Class E exact-zero-channel trap.** An E fixture used an exactly-zero opponent channel, which made the
  BY per-channel spectral centroid/spread numerically unstable; the E specs were moved to off-axis
  collinear oscillations (nonzero RG **and** BY, still verified non-winding by `c(t)`), with the E test
  strengthened to require nonzero RG/BY std and narrow RG/BY spread.

**Windows validation at `58cd57f`:** v1.1 fixture-bank tests **14 passed**; v0.8 regression **11 passed**;
full Brainvision research suite **138 passed**.

## 3. Key result (honest)

Reporting through the **unchanged** §8 logic, the accepted run is:

- **`VERDICT: HOLD`.**
- `anti_proxy_ok = False`.
- `in_scope_ok = 10/10` (every in-scope winding fixture beats its trajectory-order-permuted null, the
  continuity control, and the structureless control, with both component floors met).
- `neutral_ok = True`.
- `bank_size = 41`.
- `first_pass_structure_validity_claim_allowed = False`; `temporal_claim_allowed = False`.

## 4. What improved vs v0.8

The redesigned bank brought the magnitude / CHROMA-spectrum proxies that failed (or were marginal) in v0.8
**below** the frozen `MAGNITUDE_CORR_CEIL = 0.30`, with the descriptor logic untouched:

| anti-proxy stat | Spearman(S, stat) | ok |
| --- | --- | --- |
| `chroma_mag` | +0.035 | true |
| `rg_std` | +0.062 | true |
| `by_std` | +0.096 | true |
| `delta_rms` | −0.220 | true |
| `spectral_centroid` | −0.286 | true |
| `spectral_spread` | −0.237 | true |

Interpretation: the redesigned fixture bank **reduced the earlier magnitude / CHROMA-spectrum
proxy entanglement in this fixture-bank run without changing frozen descriptor logic.** In particular `chroma_mag` (v0.8 +0.335) and
`delta_rms` (v0.8 −0.486) are now well inside the ceiling — the A↔D magnitude pairing and the varied-envelope
/ varied-spread winders did what they were predeclared to do.

## 5. What still failed

The remaining anti-proxy failures (all `|Spearman| ≥ 0.30`) are concentrated on the directional / angular /
per-channel RG-BY spectral geometry, including the null-relative (`nr_`) versions:

| anti-proxy stat | Spearman(S, stat) |
| --- | --- |
| `u_directional_delta_rms` | −0.838 |
| `angular_increment_mag` | −0.768 |
| `rg_centroid` | −0.747 |
| `by_centroid` | −0.773 |
| `rg_spread` | −0.709 |
| `by_spread` | −0.678 |
| `nr_u_directional_delta_rms` | −0.838 |
| `nr_angular_increment_mag` | −0.769 |
| `nr_rg_centroid` | −0.748 |
| `nr_by_centroid` | −0.774 |
| `nr_rg_spread` | −0.713 |
| `nr_by_spread` | −0.681 |

Interpretation: the remaining HOLD is now **concentrated in directional motion / angular-increment /
per-channel RG-BY spectral geometry and their null-relative versions.** This is a sharper, narrower failure
than v0.8's mixed magnitude/spectrum failure — and it **should not be tuned away**. (Numbers are the
Windows-validated values from the accepted `58cd57f` run; an independent offline re-run reproduces them to
within platform floating-point noise, same six-pass / twelve-fail split and same HOLD.)

## 6. Research meaning

- **v1.1 is a useful finding, not a failure.** It demonstrated that the fixture-bank redesign can
  **dissolve some of the v0.8 confounds** (magnitude and CHROMA-spectrum) under the frozen descriptor.
- It also showed that the current `PSC / AIC / S` score **remains strongly associated with directional
  movement geometry when high-`S` winders and low-`S` non-winders are both present in the bank.** Where the
  v0.8 bank (winders + their nulls) did not span directional movement, the v1.1 bank does — and across that
  span `S` tracks directional / angular / per-channel-spectral movement.
- This residual entanglement may be any of:
  - a legitimate **Direction C** signal — the descriptor itself may need redesign to read joint winding
    structure without tracking directional movement magnitude;
  - a **Direction B** question — the anti-proxy logic may be **over-penalizing near-definitional
    directional properties** of a winding descriptor (a coherent winder *must* move its hue direction, so
    some association between `S` and angular movement is expected by construction);
  - or a **fixture-construction** question — the low-`S` / high-`S` families may still be confounding
    "amount of directional movement" with "winding coherence," resolvable by one more targeted diagnostic.
- **The point of a decision frame is that these three readings are genuinely different and lead to
  different work.** We do **not** choose an implementation direction here.

## 7. Candidate next directions

- **A. Docs-only residual-entanglement decision frame — recommended next.** Decide whether the remaining
  directional-axis failures are descriptor defects (C), a validity-logic question (B), or a
  fixture-construction artifact — *before* any new descriptor, threshold, null, or fixture is built. Lowest
  risk, and it is the fork every other direction depends on.
- **B. Null-relative / anti-proxy logic redesign — possible but dangerous.** Reframing how the
  directional/angular stats are allowed to correlate would change the **frozen v0.7 §7/§8 validity logic**,
  which is load-bearing. It must not be undertaken before the decision frame decides that the directional
  penalty is genuinely mis-aimed, and only then through a fresh formula-freeze and adversarial review.
- **C. Descriptor redesign — premature.** Replacing/augmenting `PSC / AIC / S` is a real option **only if**
  the residual entanglement is judged a true descriptor defect. Doing it before the residual-entanglement
  meaning is framed risks discarding a working, correctly-gated diagnostic to chase an association that may
  be near-definitional.
- **D. More fixture code — not recommended immediately.** Another fixture family might help isolate
  "movement amount" from "winding coherence," but building it should wait for the decision frame to say it
  is the right question.
- **E. Real clips / local-clip manifest — explicitly not allowed yet.** The offline local-clip manifest
  remains a strictly later step and must not start until the synthetic residual-entanglement question is
  understood.

## 8. Recommendation

**Next slice: a docs-only residual-entanglement decision frame (Direction A).** It should decide **how to
treat the directional-axis anti-proxy failures** — descriptor defect vs validity-logic question vs
fixture-construction artifact — **before any new descriptor, threshold, null, or fixture implementation
work.** It authorizes no code, invents no threshold, and changes no frozen logic; Directions B, C, and D
remain recorded but unopened, and E stays disallowed.

## 9. Recommended next

- **Codex review** of this findings note and of the recommendation to open a docs-only residual-entanglement
  decision frame next (Direction A), keeping B / C / D recorded-but-unopened and E disallowed.
- **If the operator explicitly opens the next docs-only slice,** it should be that decision frame; **otherwise HOLD.** Brainvision
  remains **offline / quarantined**, HELD per v0.6. `first_pass_structure_validity_claim_allowed = False`
  and `temporal_claim_allowed = False` are unchanged. **No `§0` pointer; no tags.**

*End — TORMENT Brainvision Color Structure Fixture-Bank Findings v1.2. Docs-only, non-authorizing. Opens no
implementation lane; implements no fixture; writes no test; changes no frozen formula; no `§0` pointer added;
no tags.*

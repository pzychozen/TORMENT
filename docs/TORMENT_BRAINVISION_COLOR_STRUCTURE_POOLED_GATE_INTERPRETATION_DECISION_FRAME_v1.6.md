# TORMENT Brainvision Color Structure Pooled-Gate Interpretation Decision Frame v1.6

## 1. Status / quarantine and non-claims

**DOCS-ONLY decision frame. Non-authorizing, non-implementing. Opens no runtime, integration, or
implementation lane.** It frames how to interpret the mismatch and recommends the next docs-only audit question between the v1.4
movement-matched pairwise
result and the frozen pooled §7 anti-proxy gate, before any descriptor redesign, anti-proxy redesign,
fixture implementation, or real-clip move. It **authorizes no code and no tests**, invents no threshold,
changes no formula, and modifies no existing diagnostic. Everything discussed stays offline under
`research/brainvision/` + `tests/research/`, HELD per v0.6.

This note makes **no** vision claim, **no** "Brainvision sees" claim, and **no** temporal-order claim.
`first_pass_structure_validity_claim_allowed` remains **False** and `temporal_claim_allowed` remains
**False**. It touches no `torment_service/`, runtime, camera / sensor / live-capture / screen-capture /
streaming, or prompt / context / memory / action / render-body / autonomy paths, and makes **no real-clip /
local-clip move**. **No `§0` pointer; no tags.**

## 2. Accepted facts

- Implementation edge: `cf4b4d6` (`research(brainvision): add movement-matched chroma diagnostic`).
- Findings edge: `913758d` (`docs(research): record brainvision chroma movement-matched findings`).
- Validation: v1.4 movement-matched tests **12 passed**; v1.1 fixture-bank regression **14 passed**; v0.8
  regression **11 passed**; full Brainvision research suite **150 passed**.

```text
verdict HOLD
anti_proxy_ok False
in_scope_ok 4/4
neutral_ok True
bank_size 21
match_quality_reporting_only True
first_pass_structure_validity_claim_allowed False
temporal_claim_allowed False
```

Matched-pair readout (reporting-only): the predeclared pairs were matched on movement **exactly**, yet `S` /
`PSC` separated sharply.

```text
u_ddr_abs_diff = 0.0        winders:     S = 1.000   PSC = 1.00
ang_abs_diff   = 0.0        non-winders: S ≈ 0.17–0.18   PSC ≈ 0.03
```

## 3. Accepted interpretation (preserved)

- `S` is **not merely movement amount** in these synthetic matched pairs: at exactly matched
  `u_directional_delta_rms` and `angular_increment_mag`, `S` still separates coherent winding from
  cancelling / non-winding motion.
- This **weakens the strongest bad reading from v1.3** (that `S` is only a movement-amount proxy).
- It does **not** establish descriptor-control validity.
- It does **not** establish temporal-order sensitivity.
- It does **not** establish vision.
- The frozen pooled §7 anti-proxy gate **still HOLDs** (`anti_proxy_ok = False`).

## 4. The mismatch to interpret

Two accepted facts point in different directions and must be reconciled without editing anything frozen:

- **Pairwise:** with movement matched to numerical precision, `S` and `PSC` cleanly separate winders from
  non-winders — so on the matched pairs, `S` is not a movement-amount proxy.
- **Pooled:** the full-bank §7 anti-proxy Spearman still exceeds its ceiling on the directional /
  per-channel-spectral stats, because the nulls and controls (trajectory-order nulls, structureless /
  continuity controls — high movement with low `S`) **reintroduce movement / `S` covariance across the
  whole bank**, so the pooled gate stays HOLD.

The question this frame decides is **how to read that mismatch** — which of three interpretations to pursue
**first**, without opening any of them for implementation here.

## 5. Reading A — pooled-gate / Direction B validity-surface issue

**Possible because.** Pairwise exact movement matching shows `S` is not merely movement amount, so the
pooled failure may be an artifact of the **validity surface** rather than the descriptor. The pooled gate
may be **over-penalizing** controls / nulls that **necessarily** introduce movement / `S` covariance (a
scrambled winder has high movement and low `S` by construction), and the frozen §7 anti-proxy surface may
need later docs-only scrutiny as a validity surface for a winding / coherence descriptor.

**Risk.** Changing §7 can **define the confound away** — relaxing exactly the stats a movement-proxy would
fail is externally indistinguishable from hiding a real defect. The gate must **not** be loosened without a
fresh freeze and adversarial review.

**Disposition.** Recorded as a **possible interpretation, not opened directly.**

## 6. Reading B — fixture / control composition issue

**Possible because.** The pairwise matched fixtures look clean, but the full pooled bank includes nulls and
controls that may **reintroduce movement / `S` covariance**. A better **fixture / control composition**
might produce a cleaner pooled test **without changing the descriptor or the gate** — i.e. the problem may
be *what is in the bank*, not the descriptor or the §7 rule.

**Risk.** More fixture work can become **endless tuning**; it must **not** cherry-pick or delete hard
controls (the structureless / continuity / null controls are load-bearing), and a clean pooled result on a
re-composed bank must **not** be converted into a broad validity claim.

**Disposition.** Recorded as a **possible interpretation, not opened directly.**

## 7. Reading C — residual descriptor limitation

**Still possible because.** Even after the movement-matched pair success, the pooled gate **still HOLDs**.
`PSC / AIC / S` may still fail as a general descriptor-control-valid signal **beyond planted synthetic
pairs**; the pairwise success is meaningful but **narrow**.

**Risk.** Immediate redesign is **premature** because the pairwise evidence is now positive (it argues
against a pure movement-amount defect). But **refusing to acknowledge a possible descriptor limitation**
would be **overfitting to the clean synthetic pairs** — the narrow pairwise win must not be over-read as
descriptor validity.

**Disposition.** Recorded as **still possible; not resolved either way here.**

## 8. Recommended conclusion

- **Do not redesign the descriptor yet.**
- **Do not change §7 anti-proxy logic yet.**
- **Do not implement more fixtures immediately.**
- **Do not move to real clips.**

The three readings are genuinely different and lead to different work; none is opened by this frame. The
next step is to find out **which pooled components actually cause the remaining HOLD** before choosing among
A, B, and C.

## 9. Recommendation — next slice

**Next slice: a docs-only pooled-gate audit plan / validity-surface framing review plan.**

Its purpose is to **identify which pooled components cause the remaining HOLD** and whether they represent:

1. **legitimate descriptor blockers** (Reading C),
2. **fixture / control-composition artifacts** (Reading B), or
3. **validity-surface mismatch** in the pooled anti-proxy logic (Reading A).

The audit plan must remain **docs-only** and must **not** change thresholds, gates, formulas, descriptor
logic, fixture code, or tests. It predeclares *what to look at* (e.g. which bank entries and which anti-proxy
stats drive the pooled Spearman above the ceiling, reported under the unchanged gate) — it does not decide
the fork; it gathers the evidence to decide it. It must not propose §7 edits, delete controls, or define
replacement acceptance criteria; any such move would require a separate freeze after this audit.

This decision frame authorizes no implementation. Readings A, B, and C remain recorded-but-unopened; the
real-clip / local-clip move stays disallowed.

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False` and `temporal_claim_allowed = False` are unchanged.
**No `§0` pointer; no tags.**

## 10. Recommended next

- **Codex review** of this decision frame and of the recommendation to open a docs-only pooled-gate audit /
  validity-surface framing review plan next, keeping Readings A, B, and C recorded-but-unopened and the real-clip
  move disallowed.
- **If the operator explicitly opens the next docs-only slice, it should be that pooled-gate audit plan;
  otherwise HOLD.**

*End — TORMENT Brainvision Color Structure Pooled-Gate Interpretation Decision Frame v1.6. Docs-only,
non-authorizing. Opens no implementation lane; changes no frozen formula or gate; no `§0` pointer added; no
tags.*

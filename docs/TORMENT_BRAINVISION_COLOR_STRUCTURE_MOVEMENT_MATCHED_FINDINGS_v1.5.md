# TORMENT Brainvision Color Structure Movement-Matched Findings v1.5

## 1. Status / quarantine and non-claims

**DOCS-ONLY findings / reflection note. Non-authorizing, non-implementing.** It records what the accepted
v1.4 movement-matched diagnostic (implementation edge `cf4b4d6`) shows, what it does not show, and what the
next research decision should consider. It **authorizes no code and no tests**, invents no threshold, changes
no formula, and modifies no existing diagnostic. Everything discussed stays offline under
`research/brainvision/` + `tests/research/`, HELD per v0.6.

This note makes **no** vision claim, **no** "Brainvision sees" claim, and **no** temporal-order claim.
`first_pass_structure_validity_claim_allowed` remains **False** and `temporal_claim_allowed` remains
**False**. It touches no `torment_service/`, runtime, camera / sensor / live-capture / screen-capture /
streaming, or prompt / context / memory / action / render-body / autonomy paths, and makes **no real-clip /
local-clip move**. **No `§0` pointer; no tags.**

## 2. The accepted v1.4 implementation

The v1.4 movement-matched diagnostic (edge `cf4b4d6`) added two quarantined files:

- `research/brainvision/run_color_structure_movement_matched_v1_4.py`
- `tests/research/test_brainvision_color_structure_movement_matched_v1_4.py`

It **reuses the frozen v0.8 / v1.1 logic by identity / direct import** — `structure_score` (`PSC`, `AIC`,
`S`), `_stats`, the trajectory-order-permuted null, `is_winding`, the bounded null guard, the anti-proxy
statistic set and Spearman gauntlet, the neutral handling, and the §7/§8 pass/HOLD/FAIL verdict rule are all
imported and reused verbatim. **No descriptor, constant, gate, null semantic, or verdict rule was changed.**
The only new thing is the *contents* of the fixture bank plus a reporting-only movement-match readout.

Movement-matched fixture families (predeclared, parameters fixed before any run):

- **A. Movement-matched winders** — coherent winding at controlled per-step angular movement.
- **B. Non-winding backtrackers** — same per-step movement magnitude with cancelling signs (out-and-back /
  alternating), so net winding cancels.
- **C. High-motion closed non-winders** — figure-eight / circle-out-and-back closed paths, each verified
  non-winding by `PSC` before inclusion.
- **D. Low-increment winders** — coherent winding with small per-step angular movement.
- **E. Trajectory-order-permuted matched null pairs** — pure reordering that preserves the multiset of
  `u(t)` directions and `CHROMA(t)` values and destroys only order/adjacency; no new null type; independent
  phase-randomized null stays reporting-only.
- **F. Neutral / chroma-floor carry-forward** — reused from v0.8; excluded from the anti-proxy bank.

The construction principle: a winder from constant same-sign increments `+g` and a non-winder from the same
`|g|` with cancelling signs share the **identical multiset of `|Δθ|` increments**, hence identical
`u_directional_delta_rms` and `angular_increment_mag`, while `PSC` is ~1 (winder) vs ~0 (non-winder).

**Accepted validation:** v1.4 tests **12 passed**; v1.1 regression **14 passed**; v0.8 regression **11
passed**; full Brainvision research suite **150 passed**.

## 3. Key result (accepted)

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

## 4. The matched-pair finding

The predeclared matched pairs were matched on directional movement **exactly**:

- `u_ddr_abs_diff = 0.0`
- `ang_abs_diff = 0.0`

Yet `S` and `PSC` separated sharply at that matched movement:

- **winders** stayed high: `S = 1.000`, `PSC = 1.00`;
- **non-winders** stayed low: `S ≈ 0.17–0.18`, `PSC ≈ 0.03`.

The non-winders were **structurally non-winding by signed-turn / `PSC` behavior** (verified before use, not
inferred from `S`), and the **match quality was reporting-only and did not gate** (no threshold invented, no
pass/fail surface created).

**Interpretation.** This supports the **narrow** claim that `S` is **not merely movement amount** in the
movement-matched synthetic pairs: under exact matching of `u_directional_delta_rms` and
`angular_increment_mag`, `S` separates **coherent winding** from **cancelling / non-winding motion**. It is a
statement about these synthetic pairs, not a validity claim.

## 5. The pooled-gate result

The frozen pooled §7 anti-proxy gate still **remains HOLD**:

- `anti_proxy_ok = False`;
- the full-bank pooled anti-proxy still fails;
- the nulls and controls (trajectory-order nulls, structureless / continuity controls — high movement with
  low `S`) **reintroduce movement / `S` covariance across the whole bank**, so the pooled Spearman still
  exceeds its ceiling on the directional / per-channel-spectral stats;
- therefore **no descriptor-control validity claim is allowed**.

**Accepted interpretation.** The pairwise result strongly supports the narrow statement that `S` is not merely movement amount in
these synthetic pairs; a fixture/control-composition explanation for the residual pooled failure is now more
plausible, **but the pooled-gate framing / Direction B remains open**,
because the unchanged full-bank anti-proxy still HOLDs. (The directional/angular pooled correlations did move
sharply toward the ceiling relative to v1.1, but not below it.)

## 6. What v1.5 does not show

This note, and the accepted v1.4 result it records, does **not**:

- establish descriptor-control validity;
- establish temporal-order sensitivity;
- establish vision;
- show "Brainvision sees";
- validate on real or local clips;
- authorize threshold changes;
- authorize anti-proxy redesign;
- authorize descriptor redesign;
- make the pooled **HOLD** go away.

## 7. Research meaning

- This is a **meaningful positive diagnostic result under quarantine**.
- The strongest bad interpretation from v1.3 — *"`S` is merely movement amount"* — is **weakened**: at
  exactly matched movement, `S` still separates winders from non-winders.
- The current descriptor separates planted coherent-winding pairs from structurally non-winding matched pairs
  in this synthetic diagnostic.
- However, the frozen pooled anti-proxy gate still treats the **whole bank** as invalid / HOLD, because
  movement / `S` covariance reappears through the nulls and controls.
- Therefore the next research fork is **no longer simply "descriptor redesign."** The pairwise evidence
  argues against a pure descriptor defect.
- The **sharper question** is whether the frozen §7 pooled anti-proxy logic is the **correct validity
  surface** for a winding / coherence descriptor, or whether the **fixture / control composition** needs
  another planned adjustment — a question to be decided in docs, not by editing the gate.

## 8. Candidate next directions

- **A. Docs-only pooled-gate interpretation decision frame — recommended next.** Decide whether the
  remaining full-bank HOLD should be treated as a **validity-logic / Direction B** issue, a **fixture /
  control composition** issue, or **still a possible descriptor defect** despite the matched-pair result.
- **B. Immediate descriptor redesign — not recommended yet.** The movement-matched pairs show `S` is not
  merely movement amount, which argues against a pure descriptor defect.
- **C. Immediate anti-proxy logic redesign — not recommended yet.** Changing §7 could **define the confound
  away**; it needs a docs-only decision first and a fresh freeze / review.
- **D. More implementation immediately — not recommended.** This important result should be frozen in
  findings and interpreted before more code.
- **E. Real clips / local-clip manifest — still disallowed.**

## 9. Recommendation

**Next slice: a docs-only pooled-gate interpretation decision frame (Direction A).** It should decide **how
to treat the mismatch** between:

- the **pairwise** movement-matched evidence that `S` separates winding coherence from non-winding
  cancellation (at exact movement matching), and
- the frozen **pooled** §7 gate still producing **HOLD**.

It authorizes no implementation, invents no threshold, changes no frozen formula or gate, and builds nothing.
Directions B, C, and D remain recorded-but-unopened; E stays disallowed.

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False` and `temporal_claim_allowed = False` are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Color Structure Movement-Matched Findings v1.5. Docs-only, non-authorizing. Opens
no implementation lane; implements no fixture; writes no test; changes no frozen formula; no `§0` pointer
added; no tags.*

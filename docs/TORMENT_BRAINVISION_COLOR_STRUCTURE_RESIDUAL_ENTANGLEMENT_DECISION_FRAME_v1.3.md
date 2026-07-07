# TORMENT Brainvision Color Structure Residual-Entanglement Decision Frame v1.3

## 1. Status / quarantine and non-claims

**DOCS-ONLY decision frame. Non-authorizing, non-implementing. Opens no runtime, integration, or
implementation lane.** It frames how to interpret the residual anti-proxy entanglement recorded in the v1.2
findings note and recommends the next docs-only question to plan before any new descriptor, threshold, null,
or fixture is built. It **authorizes no code and
no tests**, invents no threshold, changes no formula, and modifies no existing diagnostic. Everything
discussed stays offline under `research/brainvision/` + `tests/research/`, HELD per v0.6.

This note makes **no** vision claim, **no** "Brainvision sees" claim, and **no** temporal-order claim.
`first_pass_structure_validity_claim_allowed` remains **False** and `temporal_claim_allowed` remains
**False**. It touches no `torment_service/`, runtime, camera / sensor / live-capture / screen-capture /
streaming, or prompt / context / memory / action / render-body / autonomy paths, and makes **no real-clip /
local-clip move**. **No `§0` pointer; no tags.**

## 2. Accepted v1.1 / v1.2 facts

- Implementation edge: `58cd57f` (the v1.1 fixture-bank diagnostic, frozen v0.8 logic reused by identity).
- Findings edge: `a16df67` (the v1.2 findings/reflection note).
- **`VERDICT: HOLD`**; `anti_proxy_ok = False`; `in_scope_ok = 10/10`; `neutral_ok = True`;
  `bank_size = 41`; `first_pass_structure_validity_claim_allowed = False`; `temporal_claim_allowed = False`.

Improved / passing anti-proxy stats (`|Spearman| < MAGNITUDE_CORR_CEIL = 0.30`), the magnitude /
CHROMA-spectrum axis that failed in v0.8:

| stat | Spearman(S, stat) | ok |
| --- | --- | --- |
| `chroma_mag` | +0.035 | true |
| `rg_std` | +0.062 | true |
| `by_std` | +0.096 | true |
| `delta_rms` | −0.220 | true |
| `spectral_centroid` | −0.286 | true |
| `spectral_spread` | −0.237 | true |

Still-failing anti-proxy stats (`|Spearman| ≥ 0.30`), the directional / angular / per-channel RG-BY spectral
axis and its null-relative versions:

| stat | Spearman(S, stat) |
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

## 3. The residual-entanglement question

The v1.1 bank decorrelated magnitude / CHROMA-spectrum but left `S` strongly (inversely) associated with
directional movement geometry. **The remaining failures may mean one of three genuinely different things,
which lead to different work:**

- **A. Descriptor defect / Direction C.** `PSC / AIC / S` may **inherently** score directional-movement
  geometry rather than isolating winding coherence — i.e. the descriptor is a movement-amount proxy.
- **B. Validity-logic question / Direction B.** The anti-proxy gauntlet may be **over-penalizing
  near-definitional** directional-movement properties of a *winding* descriptor — a coherent winder must
  move its hue direction, so some `S`↔movement association is expected by construction.
- **C. Fixture-construction artifact.** The v1.1 bank may **still couple "amount of directional movement"
  with "winding coherence,"** so one more targeted fixture diagnostic may be needed before touching the
  descriptor or the validity logic.

The purpose of this decision frame is to choose which of these to test **first**, without opening any of
them for implementation here.

## 4. Direction C — descriptor redesign

**Why it is plausible.** `S` is built from signed directional increments (the plane cross product `c(t)`)
and circular increment agreement (`AIC` on wrapped hue increments), so it is arithmetically a function of
how the hue direction moves. High-`S` winders necessarily have coherent directional movement; low-`S`
non-winders in the bank tend to have either less directional movement (E collinear / narrowband) or
cancelling movement (C back-and-forth). Across a bank that spans both, `S` and directional-movement
statistics move together — which is what the failing stats show.

**Why it is risky / premature.** A descriptor redesign could **discard a working, correctly-gated
diagnostic** before the validity-logic question (Direction B) is even settled — if the directional
association is near-definitional rather than a defect, redesign would be solving the wrong problem. No new
`PSC / AIC / S` formula may be opened without a **separate formula-freeze** and adversarial review.

**Verdict.** Recorded as **plausible but not opened.**

## 5. Direction B — anti-proxy / validity-logic review

**Why it is plausible.** Penalizing `u_directional_delta_rms` and `angular_increment_mag` may punish the
**necessary substrate** of any winding score: a winding descriptor that did *not* correlate with directional
movement would arguably not be measuring winding at all. Likewise, per-channel RG/BY spread / centroid may
be too strict when the descriptor is **intentionally a joint-plane directional** measure — the anti-proxy
bank was frozen (v0.7 §7) before the joint-plane descriptor's directional nature was this clearly exposed.

**Why it is dangerous.** Changing the anti-proxy rules can **define the confound away** — relaxing exactly
the stats a movement-proxy would fail is indistinguishable, from the outside, from hiding a real defect. Any
such change would require **fresh review and a new freeze** of the §7/§8 validity logic, which is
load-bearing and must not be edited to make a failing run pass.

**Verdict.** Recorded as **plausible but dangerous; not opened yet.**

## 6. Fixture-construction artifact

**Why it is plausible.** The v1.1 bank now contains high-`S` winders and low-`S` non-winders, but that
composition may **still couple movement amount with winding coherence**: the winders are also the
movement-heavy fixtures and the non-winders are also the movement-light (or movement-cancelling) fixtures. A
bank can decorrelate magnitude / spectrum (as v1.1 did) while **still structurally separating movement-heavy
winders from movement-light non-winders**, so the directional stats would fail even if the descriptor were
reading winding coherence correctly.

**What a targeted diagnostic might test later** (predeclared here only as questions, not built):

- high-directional-motion **non-winders** (lots of hue movement, no coherent net winding);
- low-amplitude or low-increment **winders** (coherent winding, small per-step angular movement);
- backtracking / cancelling-turn paths with **similar angular-increment magnitude** to true winders;
- winders and non-winders **matched on `u_directional_delta_rms` and `angular_increment_mag`**, so that if
  `S` still separates them the separation is winding coherence and not movement amount.

**Verdict.** This is the **recommended next interpretation to frame for a possible later test** — it can distinguish a real
descriptor defect (Direction C) from a near-definitional penalty (Direction B) empirically, under the
**unchanged** descriptor and validity logic. **v1.3 itself authorizes no code.**

## 7. Options compared

- **A. Immediate descriptor redesign — not recommended yet.** Premature before the movement-matched
  question is tested; risks discarding a working diagnostic (see §4).
- **B. Immediate anti-proxy / validity-logic redesign — not recommended yet.** Changes frozen §7/§8 logic
  and can define the confound away; must wait for evidence that the directional penalty is genuinely
  mis-aimed (see §5).
- **M — movement-matched fixture diagnostic plan. One targeted docs-only fixture diagnostic plan for
  movement-matched winders / non-winders — recommended next.** Predeclares (no code) the fixtures that would separate "winding coherence" from
  "movement amount" under the unchanged descriptor and gates.
- **D. More implementation immediately — not recommended.** No new code should be written before the
  decision frame's chosen question is planned and reviewed.
- **E. Real clips / local-clip manifest — explicitly disallowed.** Remains a strictly later step; must not
  start until the synthetic residual-entanglement question is understood.

## 8. Recommendation

**Next slice: a docs-only movement-matched fixture diagnostic plan (Option M).** It should **predeclare,
without code**, a small synthetic diagnostic that would test whether high-`S` winders and low-`S`
non-winders can be **matched on directional movement amount** (`u_directional_delta_rms`,
`angular_increment_mag`) — so that if `S` still separates the matched families, the separation is winding
coherence rather than movement amount, and if it does not, the residual failure points at the descriptor.
This is the cleanest question to plan next, **under the unchanged descriptor and validity logic**,
whether the residual failure is a **descriptor defect (Direction C)** or a **validity-logic issue (Direction
B)** — before either is opened.

**This decision frame authorizes no implementation.** Directions B and C, and Option D, remain
recorded-but-unopened; Option E stays disallowed. The plan slice itself must invent no threshold, change no
frozen formula or gate, and build nothing until it is itself reviewed.

## 9. Recommended next

- **Codex review** of this decision frame and of the recommendation to open a docs-only movement-matched
  fixture diagnostic plan next (Option M), keeping Directions B and C recorded-but-unopened, Option D not
  recommended, and Option E disallowed.
- **If the operator explicitly opens the next docs-only slice, it should be that movement-matched fixture
  diagnostic plan; otherwise HOLD.** Brainvision remains **offline / quarantined**, HELD per v0.6.
  `first_pass_structure_validity_claim_allowed = False` and `temporal_claim_allowed = False` are unchanged.
  **No `§0` pointer; no tags.**

*End — TORMENT Brainvision Color Structure Residual-Entanglement Decision Frame v1.3. Docs-only,
non-authorizing. Opens no implementation lane; implements no fixture; writes no test; changes no frozen
formula; no `§0` pointer added; no tags.*

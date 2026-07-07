# TORMENT Brainvision Color Structure Movement-Matched Fixture Plan v1.4

## 1. Status / quarantine and non-claims

**DOCS-ONLY plan. Non-authorizing, non-implementing. Opens no runtime, integration, or implementation
lane.** It predeclares — without code — a small synthetic diagnostic recommended by the v1.3 residual-
entanglement decision frame (`e67a333`). It **authorizes no code and no tests**, invents no threshold,
changes no formula, and modifies no existing diagnostic. Everything discussed stays offline under
`research/brainvision/` + `tests/research/`, HELD per v0.6.

This note makes **no** vision claim, **no** "Brainvision sees" claim, and **no** temporal-order claim.
`first_pass_structure_validity_claim_allowed` remains **False** and `temporal_claim_allowed` remains
**False**. It touches no `torment_service/`, runtime, camera / sensor / live-capture / screen-capture /
streaming, or prompt / context / memory / action / render-body / autonomy paths, and makes **no real-clip /
local-clip move**. **No `§0` pointer; no tags.**

## 2. Accepted reason for this plan

- v1.1 implementation edge: `58cd57f` (the fixture-bank diagnostic; frozen v0.8 logic reused by identity).
- v1.2 findings edge: `a16df67` (recorded the accepted run).
- v1.3 residual-entanglement decision edge: `e67a333` (framed the residual failure and recommended this
  plan).
- **`VERDICT: HOLD`**; `anti_proxy_ok = False`; `first_pass_structure_validity_claim_allowed = False`;
  `temporal_claim_allowed = False`.
- In the v1.1 fixture-bank run the **magnitude / CHROMA-spectrum** anti-proxy stats improved into the frozen
  ceiling (`chroma_mag`, `rg_std`, `by_std`, `delta_rms`, `spectral_centroid`, `spectral_spread` all
  `|Spearman| < 0.30`).
- The **residual failures remain concentrated** on directional movement / angular increment / per-channel
  RG-BY spectral geometry and their null-relative versions: `u_directional_delta_rms`,
  `angular_increment_mag`, `rg_centroid`, `by_centroid`, `rg_spread`, `by_spread`, and the corresponding
  `nr_` variants (all `|Spearman| ≈ 0.68–0.84`).

## 3. The diagnostic question

**Can winders and non-winders be constructed so they are matched on directional movement amount while
differing in winding coherence?** If yes, a later implementation could report whether `S` still separates winding-coherent from non-winding fixtures
after movement matching, without establishing validity by itself; if matching proves impossible without collapsing the
winder / non-winder distinction, that is itself useful evidence.

Three properties must be kept **conceptually separate**:

- **Movement amount** — how much the chroma direction `u(t)` moves frame-to-frame (captured by
  `u_directional_delta_rms` and `angular_increment_mag`).
- **Winding coherence** — whether the signed turns `c(t)` keep a coherent same-sign / net-winding structure
  (captured by `PSC`).
- **Spectral / per-channel geometry** — RG/BY centroid / spread effects that may **follow from the path
  shape** rather than from winding itself.

This diagnostic answers **no** vision question, **no** temporal-order question, and **no** natural-video
question. It is a synthetic separability probe only.

## 4. Predeclared fixture families (conceptual only)

Described here as roles and construction *ideas* — no generators, parameters, counts, or numeric ranges are
fixed, and none may be built by this note.

- **A. Movement-matched coherent winders.** High winding coherence with **intentionally controlled**
  `u_directional_delta_rms` and `angular_increment_mag`, varying speed / step profile **without** changing
  the net-winding class. Conceptual examples: slow full winders with many small increments; winders with
  controlled step-size profiles; winders designed to match the movement amount of selected non-winders.
- **B. Movement-matched non-winding backtrackers.** High movement amount but **low `PSC` / cancelling signed-turn structure, not merely zero net
  rotation**, with `u_directional_delta_rms` and `angular_increment_mag` **similar to family A**. Conceptual
  examples: forward/backward turn paths; oscillating arcs; alternating signed-turn paths; high-motion paths
  with near-zero `PSC`.
- **C. High-motion closed non-winders.** Lots of chroma-direction movement on closed or near-closed paths
  with **no coherent same-sign winding**. Conceptual examples: figure-eight-like chroma paths; two-lobe
  paths; alternating loops that cancel signed winding. Every non-winder must be verified structurally by
  signed turns / `PSC` before inclusion; closed paths or zero-net paths that still produce coherent
  same-sign winding are invalid or reclassified.
- **D. Low-increment coherent winders.** Coherent winding with **smaller reported per-step angular movement where possible under the frozen
  fixture/sample contract**, to test
  whether winding can stay high-`S` at low `angular_increment_mag` — separating total winding coherence
  from angular-increment magnitude.
- **E. Matched null pairs.** For **each** planted fixture, a trajectory-order-permuted null that preserves
  the multiset of `u(t)` directions and `CHROMA(t)` values and **destroys only order / adjacency**. **No
  new null type**; the independent phase-randomized null is **not** a gate (reporting-only, per the frozen
  v0.7/v0.8 null semantics).
- **F. Neutral / floor carry-forward.** Preserve the v0.8 neutral behavior; **do not** include neutral
  fixtures in the anti-proxy bank (handled by the neutral-ceiling gate); no luminance / chroma-collapse
  cross-fire.

Intended separability: families A and D populate high-`S` **winders** across a movement range, while B and C
populate low-`S` **non-winders** across an **overlapping** movement range — so `u_directional_delta_rms` and
`angular_increment_mag` are spanned by **both** winders and non-winders.

## 5. Predeclared matching targets

A later implementation (not authorized here) should try to **match or report**, without inventing any
threshold:

- `u_directional_delta_rms`,
- `angular_increment_mag`,
- optionally RG/BY spectral centroid / spread,
- optionally the null-relative (`nr_`) movement stats,

while preserving a **clear distinction in winding coherence**:

- **winders** — high coherent same-sign signed-turn structure (`PSC` high),
- **non-winders** — cancelling / alternating signed turns (`PSC` low).

**v1.4 invents no final numeric thresholds.** The plan may require **reporting match quality** (e.g. how
close the movement stats of matched winder / non-winder pairs are), but it must **not** define any new
pass/fail threshold beyond the frozen v0.7/v0.8 gates. Match quality is reporting-only unless a later
reviewed plan explicitly freezes a non-gating diagnostic definition; it must not become a new pass/fail
surface. The only acceptance surface remains the unchanged §8
logic and its frozen constants.

## 6. Expected interpretive outcomes (honest)

- **Outcome 1 — fixture-bank artifact more likely.** If matched winders stay high-`S` and matched
  non-winders stay low-`S` **while their movement stats are similar**, then the residual directional-axis
  failures may be more likely a **fixture-bank artifact** (movement amount and winding coherence were
  co-varying in the v1.1 bank), and more careful fixture-bank design may be justified.
- **Outcome 2 — Direction C stronger.** If `S` **tracks movement amount even after matching attempts**,
  that supports **Direction C**: descriptor redesign may be needed later.
- **Outcome 3 — Direction B stronger.** If matching is **impossible without collapsing** the winder /
  non-winder distinction, that supports **Direction B**: the anti-proxy logic may be penalizing
  **near-definitional** properties of a winding descriptor.
- **Outcome 4 — stop and review.** If the diagnostic turns out to **require changing `PSC / AIC / S`,
  thresholds, nulls, or gates**, **stop and return to docs / review** — that is a frozen-logic change,
  out of scope for a fixture diagnostic.

No expected outcome is predeclared as the "right" one, and none may be tuned toward.

## 7. Risk controls

- **No tuning fixtures after seeing `S`** — fixtures and their parameters must be predeclared before any run.
- **No selecting only successful matches** — report all matched pairs, not just the flattering ones.
- **No deleting hard non-winders** — families B and C (the high-motion non-winders) must be retained, not
  dropped to clean a result.
- **No changing the descriptor or gates** — `PSC / AIC / S`, constants, and §7/§8 logic stay frozen and
  reused by identity.
- **No redefining anti-proxy logic** — that is Direction B and is not opened here.
- **No pretending movement-matching proves temporal order** — the trajectory-order-permuted null stays a
  structure control; `temporal_claim_allowed` stays False.
- **No real-clip / local-clip move** — remains a strictly later step, disallowed here.
- **No validity claim even if the later diagnostic looks promising** — the verdict stays HOLD and
  `first_pass_structure_validity_claim_allowed` stays False until a full, separately authorized run says
  otherwise.

## 8. Options compared after v1.4

- **A. Codex review and commit this docs-only plan — recommended immediate next.**
- **B. Implement the movement-matched diagnostic later — only if explicitly opened** after review and
  explicit operator authorization.
- **C. Descriptor redesign — still unopened** (Direction C; premature until this diagnostic reports).
- **D. Anti-proxy / validity-logic redesign — still unopened** (Direction B; changes frozen §7/§8 logic).
- **E. Real clips / local-clip manifest — still disallowed.**

## 9. Recommendation

**Accept v1.4 as a docs-only plan if Codex review passes.** After that, the next *possible* slice could be
a possible later **narrow offline research implementation**, if explicitly opened — building families A–F and reporting their
movement stats and `S` through the **unchanged** frozen v0.7/v0.8 descriptor and §7/§8 gates — **but only
after explicit operator authorization and Codex review.** This plan authorizes none of it: it invents no
threshold, changes no frozen formula or gate, and builds nothing. Directions C and D remain
recorded-but-unopened; E stays disallowed.

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False` and `temporal_claim_allowed = False` are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Color Structure Movement-Matched Fixture Plan v1.4. Docs-only, non-authorizing.
Opens no implementation lane; implements no fixture; writes no test; changes no frozen formula; no `§0`
pointer added; no tags.*

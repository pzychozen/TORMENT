# TORMENT Brainvision Color Structure Directional Validity-Surface Review v2.5

## 1. Status / quarantine and non-claims

**DOCS-ONLY validity-surface review. Non-authorizing, non-implementing. Opens no runtime, integration, or
implementation lane.** It scrutinizes, in docs only, whether the surviving **directional** residual is a true
proxy problem or whether frozen §7 is over-penalizing geometry that is near-definitional for coherent winding.
It **authorizes no code and no tests**, invents no threshold, defines no replacement acceptance criteria,
changes no formula / §7 anti-proxy logic / §8 verdict logic, deletes no control, and implements no fixture.
Everything discussed stays offline under `research/brainvision/` + `tests/research/`, HELD per v0.6.

This note makes **no** vision claim, **no** "Brainvision sees" claim, and **no** temporal-order claim.
`first_pass_structure_validity_claim_allowed` remains **False** and `temporal_claim_allowed` remains **False**.
It touches no `torment_service/`, runtime, camera / sensor / live-capture / screen-capture / streaming, or
prompt / context / memory / action / render-body / autonomy paths, and makes **no real-clip / local-clip move**
and **no memory-system integration**. Brainvision Path B is **not proven vision** and is **not a functioning
vision layer for TORMENT memory**. **No `§0` pointer; no tags.**

Scope of this review is the **directional axis only**:

```text
u_directional_delta_rms
angular_increment_mag
nr_u_directional_delta_rms
nr_angular_increment_mag
```

The per-channel-spectral axis (v2.4 reading C) is **out of scope here** and is deferred to a separate docs-only
review (§8).

## 2. Accepted v2.4 directional facts

Carried forward by identity from the accepted v2.4 audit (edge `a658719`,
`research(brainvision): audit directional spectral residual causes`; findings receipt v2.4). The verdict
**remains HOLD**.

Directional drivers lead the pooled §7 wall (frozen gate, `|rho| >= 0.30` fails):

```text
nr_u_directional_delta_rms   rho ~ -0.862   fail
u_directional_delta_rms      rho ~ -0.858   fail
angular_increment_mag        rho ~ -0.850   fail
nr_angular_increment_mag     rho ~ -0.847   fail
```

Matched pairs still separate `S` / `PSC` at nearly fixed directional blockers:

```text
movement family mean |Δblocker| <= 0.0036
ΔS   ~ +0.822
ΔPSC ~ +0.968
```

Null-relative decomposition: the directional association **survives among the primaries** (winders +
nonwinders), i.e. it is not merely reintroduced by the nulls/controls:

```text
nr_u_directional_delta_rms   primaries_only ~ -0.803
nr_angular_increment_mag     primaries_only ~ -0.686
```

v2.4 classified the directional axis as **B_validity_surface_mismatch / near-definitional co-movement**;
**A_descriptor_limitation was NOT supported** because the matched pairs separate `S` / `PSC` at fixed blocker.
That classification is **reporting-only and cannot change the verdict**, which stays **HOLD**.

## 3. The validity-surface question

A winding / coherence descriptor (`PSC` / `AIC` / `S`) may **naturally** correlate with directional smoothness
and angular structure: a coherent chroma-plane winder traces a regular, low-jitter path with a characteristic
per-step angular increment, so directional regularity moves **with** the target by construction.

The question is whether the frozen §7 anti-proxy gate, which flags any `S`↔stat correlation above the ceiling as
a proxy failure, is here catching a **real proxy shortcut** or is **over-penalizing** a property that is
near-definitional for the target behaviour. Both framings are live:

- If the directional statistics are a genuine shortcut — separating classes **without requiring coherent
  winding** — then the §7 failure is correct and must stand.
- If the directional statistics are simply what coherent winding **must** produce, then §7 is penalizing
  target-adjacent geometry, and the "failure" is a property of the **validity surface**, not the descriptor.

Crucially, **relaxing §7 would be dangerous**: loosening exactly the stats a movement/directional proxy would
fail is externally indistinguishable from **defining a true confound away**. This review therefore only
**frames** the question in docs; it proposes **no** §7 change.

## 4. Distinguish target geometry from proxy geometry

Docs-only definitions to keep the question honest:

- **Target-adjacent geometry** — directional regularity that coherent winding **must** carry: a smooth
  monotonic sweep of the chroma-plane angle produces low unit-vector jitter (`u_directional_delta_rms`) and a
  stable per-step angular increment (`angular_increment_mag`). A genuine winder cannot avoid these; they are
  downstream of winding, not a substitute for it.
- **Proxy geometry** — directional statistics that separate the classes **without requiring coherent winding**:
  a trajectory could, in principle, present low jitter or a particular angular increment while **not** winding
  coherently (low `PSC` / `AIC`). If such a construction scored high `S` on directional smoothness alone, the
  directional stat would be a proxy.
- **Forbidden shortcut** — using low jitter / angular smoothness **alone** as a substitute for the `PSC` / `AIC`
  / `S` winding-coherence signal. §7 exists to forbid exactly this. The validity-surface question is whether the
  observed directional correlation is the forbidden shortcut, or the unavoidable shadow of the target.

The discriminator is therefore: **at matched directional geometry, does the winding signal still separate?** If
yes, that supports a target-adjacent reading in the current synthetic matched-pair evidence, rather than showing
that directional smoothness alone is doing the separating work.

## 5. Evidence for B_validity_surface_mismatch

The v2.4 facts point toward the directional residual being a validity-surface mismatch rather than a pure proxy:

- **High directional pooled `rho`** (`|rho|` 0.847–0.862) confirms a strong pooled association between `S` and
  the directional stats — the wall is real and directional-led.
- **Primaries-only directional association survives** (`-0.803` / `-0.686`): the association is present among
  the actual winders and nonwinders, not merely reintroduced by nulls/controls — so it is a property of the
  fixtures, consistent with directional geometry moving with winding.
- **Matched pairs still separate `S` / `PSC` at fixed blocker** (mean `|Δblocker|` ≤ 0.0036, `ΔS` ≈ +0.822,
  `ΔPSC` ≈ +0.968): when the directional geometry is held nearly constant, the winding signal **still**
  separates coherent winding from cancellation. Directional smoothness is therefore **weakened as the sole
  separating mechanism** in this matched-pair evidence; the **forbidden-shortcut reading is weakened, but not
  resolved**.
- **Directional motion is near-definitional for coherent winding**: winders occupy a tight directional region
  (winding forces low jitter and a stable angular increment) with `S` / `PSC` pinned high, while cancellation
  controls separate cleanly.
- **Therefore** §7 may be detecting **target-adjacent structure**, not a pure proxy: the directional stats
  correlate with `S` because winding produces them, not because `S` is substituting them for coherence.

## 6. Evidence against over-reading B

Countervailing cautions, recorded so B is not over-read into a validity claim:

- **The high `rho` is real and must not be ignored.** A strong, robust pooled correlation is exactly what a
  proxy defect would also produce; "target-adjacent" is a hypothesis about *why*, not a dismissal of the
  number.
- **Near-definitional does not mean automatically valid.** That winding *implies* certain directional geometry
  does not establish that the descriptor is a valid winding detector on anything beyond the constructed
  fixtures; the implication runs one way.
- **Matched-pair coverage is still synthetic and narrow.** The separation-at-fixed-blocker evidence comes from
  a small predeclared family of synthetic trajectories; it is suggestive, not general.
- **No §7 relaxation is authorized.** Nothing here licenses loosening, re-weighting, or exempting the
  directional stats in the anti-proxy gate. The gate stays exactly as frozen.
- **No descriptor-validity claim is allowed.** This review classifies the *residual*, not the descriptor; it
  makes no statement that `PSC` / `AIC` / `S` is a valid structure detector.

## 7. Decision outcome

The directional axis should be treated as a **validity-surface mismatch candidate** — **not** a descriptor
limitation, and **not** a gate pass. The pooled §7 failure on the directional stats is best explained, on the
current synthetic evidence, as §7 detecting target-adjacent directional geometry rather than a forbidden
shortcut; but this remains a *candidate* reading pending broader (still docs-gated) scrutiny, and it changes
nothing frozen.

Recorded outcome flags (reporting-only; none of these move the verdict or any gate):

```text
directional_validity_surface_mismatch_candidate = True
directional_proxy_failure_resolved              = False
descriptor_validity_claim_allowed               = False
verdict                                          = HOLD
first_pass_structure_validity_claim_allowed      = False
temporal_claim_allowed                           = False
```

`directional_proxy_failure_resolved = False` is deliberate: the residual is **not** resolved, only better
characterized. The frozen §7 gate still HOLDs on the directional stats, and no relaxation, threshold, or
descriptor claim follows from this review.

## 8. Recommended next step

After v2.5, the recommended next step is a **separate docs-only per-channel bank-composition review** — **not
code** — addressing the other v2.4 sub-axis (reading C). Possible next file:

```text
docs/TORMENT_BRAINVISION_COLOR_STRUCTURE_PER_CHANNEL_BANK_COMPOSITION_REVIEW_v2.6.md
```

Purpose:

```text
Review whether the per-channel RG/BY centroid / spread residual is mostly null / control-bank geometry,
based on the v2.4 classification C (primaries-only association collapses to ~0; failure reintroduced by
the null / control geometry). Docs-only; no §7/§8 edit, no threshold, no control deletion, no code.
```

The v2.6 review is recorded as the next **possible** step; it is **not opened here**. Real clips / local-clip
manifest and memory-system integration stay disallowed, and no §7/§8/threshold/control/descriptor change may be
made without a fresh freeze and adversarial review.

- **Codex review** of this directional validity-surface review and of the recommendation to open the docs-only
  v2.6 per-channel bank-composition review next, keeping the directional axis a validity-surface-mismatch
  **candidate** (not resolved, not a validity claim), the verdict at HOLD, and all disallowed moves disallowed.
- **If the operator explicitly opens the next docs-only slice, it should be that v2.6 review; otherwise HOLD.**

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False` and `temporal_claim_allowed = False` are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Color Structure Directional Validity-Surface Review v2.5. Docs-only, non-authorizing.
Opens no implementation lane; changes no frozen formula, gate, or verdict; deletes no control; invents no
threshold; relaxes no §7; makes no descriptor-validity claim; no `§0` pointer added; no tags.*

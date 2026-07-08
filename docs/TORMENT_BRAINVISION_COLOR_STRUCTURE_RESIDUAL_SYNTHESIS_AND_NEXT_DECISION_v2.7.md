# TORMENT Brainvision Color Structure Residual Synthesis and Next-Decision Frame v2.7

## 1. Status / quarantine and non-claims

**DOCS-ONLY synthesis-and-next-decision frame. Non-authorizing, non-implementing. Opens no runtime,
integration, or implementation lane.** It synthesizes the accepted v2.4 + v2.5 + v2.6 results and recommends
which next branch to pursue, **without opening any implementation**. It **authorizes no code and no tests**,
invents no threshold, defines no replacement acceptance criteria, changes no formula / §7 anti-proxy logic / §8
verdict logic, deletes or weakens no control, and implements no fixture. Everything discussed stays offline
under `research/brainvision/` + `tests/research/`, HELD per v0.6.

This note makes **no** vision claim, **no** "Brainvision sees" claim, and **no** temporal-order claim.
`first_pass_structure_validity_claim_allowed` remains **False** and `temporal_claim_allowed` remains **False**.
It touches no `torment_service/`, runtime, camera / sensor / live-capture / screen-capture / streaming, or
prompt / context / memory / action / render-body / autonomy paths, and makes **no real-clip / local-clip move**
and **no memory-system integration**. Brainvision Path B is **not proven vision** and is **not a functioning
vision layer for TORMENT memory**. **No `§0` pointer; no tags.**

## 2. Accepted closed evidence

Carried forward by identity from the three accepted slices (edge `efbccec`,
`docs(research): review brainvision per-channel bank composition`, and its predecessors):

**v2.4 reporting-only diagnostic** (decomposition under unchanged frozen §7):

```text
headline:                 mixed_or_unresolved
directional axis ->       B_validity_surface_mismatch
per-channel-spectral ->   C_bank_composition_artifact
A_descriptor_limitation:  NOT supported (matched pairs separate S/PSC at fixed blocker)
verdict:                  HOLD
```

**v2.5 directional validity-surface review:**

```text
directional_validity_surface_mismatch_candidate = True
directional_proxy_failure_resolved              = False
(no §7 relaxation)
verdict                                          = HOLD
```

**v2.6 per-channel bank-composition review:**

```text
per_channel_bank_composition_artifact_candidate = True
per_channel_proxy_failure_resolved              = False
control_deletion_allowed                        = False
verdict                                          = HOLD
```

## 3. Current residual map

- The old `by_std` and `spectral_centroid` blockers are **controlled / explained** (v2.0 / v2.1).
- The **directional** residual is best treated as a **validity-surface mismatch candidate, unresolved** (v2.5).
- The **per-channel-spectral** residual is best treated as a **bank-composition artifact candidate, unresolved**
  (v2.6).
- A **direct descriptor limitation is not supported** by the current matched-pair evidence (v2.4: matched pairs
  separate `S` / `PSC` at fixed blocker on both sub-axes).
- The **frozen pooled §7 gate still HOLDs**.
- **No descriptor-validity claim is allowed.**

Both surviving sub-axes are therefore *characterized but unresolved*: each has a leading candidate reading
(B for directional, C for per-channel), neither is resolved, and neither licenses a gate, control, or validity
move. The remaining uncertainty in both is that the supporting matched-pair evidence is **narrow and synthetic**
(a small predeclared family; the per-channel matches are collinear).

## 4. Candidate next branches

### A. Broader matched-pair diagnostic

**Purpose.** Expand matched-pair coverage beyond the current narrow families — specifically **non-collinear
per-channel centroid / spread matches**, **broader directional matched pairs**, and **more target-preserving vs
blocker-preserving decompositions**.

**Pros.** Directly tests the remaining uncertainty; can **strengthen or weaken both** the v2.5 (directional) and
v2.6 (per-channel) candidates with new evidence rather than argument.

**Risks.** Can become a **fixture chase / gate-gaming** if steered toward a pass; **must be reporting-only** if
opened, under the unchanged gate.

### B. Validity-surface doctrine review

**Purpose.** Review, in docs, whether §7 is appropriately shaped for **target-adjacent directional geometry** —
the deepest conceptual issue raised by v2.5.

**Pros.** Addresses the most fundamental question in the arc (whether the anti-proxy surface over-penalizes
near-definitional winding geometry).

**Risks.** Could **drift toward relaxing §7 or defining away a confound**; should **not** happen before broader
evidence unless kept narrowly docs-only.

### C. Null / control-bank redesign plan

**Purpose.** Study whether the null / control bank should be **decomposed or balanced differently for
interpretation** — the direct follow-up to v2.6.

**Pros.** Addresses the v2.6 finding directly (the pooled per-channel failure is carried by cross-group
null / control geometry).

**Risks.** Could become **control deletion or re-weighting to pass the gate**; must **not** edit controls or the
gate without a fresh freeze and adversarial review.

### D. HOLD

**Purpose.** Stop this arc until stronger operator direction or a broader research target is selected.

**Pros.** Prevents **overfitting and endless synthetic tuning**.

**Risks.** Leaves a **useful signal unexplored**.

## 5. Recommended branch

**Recommended: A — Broader matched-pair diagnostic — but only as a predeclared reporting-only plan first, not
immediate code.**

**Reason.** It is the most **evidence-generating** next step and is the one branch that can test **both**
unresolved candidates at once:

- the directional **validity-surface mismatch candidate** (v2.5), and
- the per-channel **bank-composition artifact candidate** (v2.6).

By expanding to non-collinear per-channel matches and broader directional pairs, and by contrasting
target-preserving vs blocker-preserving decompositions, it can strengthen or weaken each candidate on evidence
rather than argument, while B (doctrine) and C (control-bank) both risk touching the gate or the controls before
the evidence justifies it. A is preferred **as a plan**; it must:

- **not try to pass §7**,
- **not relax §7**,
- **not delete or weaken controls**,
- **not claim validity**,

and must remain **reporting-only** under the unchanged frozen gate. B and C remain recorded as later
possibilities; D (HOLD) remains available if the operator prefers to stop the arc.

## 6. Decision outcome flags

Recorded outcome (reporting-only; none of these move the verdict or any gate):

```text
next_recommended_branch                     = broader_matched_pair_diagnostic_plan
implementation_opened                       = False
gate_change_allowed                         = False
control_deletion_allowed                    = False
descriptor_validity_claim_allowed           = False
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed                      = False
verdict                                      = HOLD
```

`implementation_opened = False` is deliberate: this frame recommends a **plan**, not code. The frozen §7/§8
machinery, thresholds, and controls are unchanged, and the verdict stays **HOLD**.

## 7. Recommended next file

The recommended next step is a **docs-only v2.8 plan** — **not opened here**:

```text
docs/TORMENT_BRAINVISION_COLOR_STRUCTURE_BROADER_MATCHED_PAIR_DIAGNOSTIC_PLAN_v2.8.md
```

Purpose:

```text
Predeclare a broader matched-pair diagnostic that tests both unresolved candidates without gate-gaming:
- directional matched expansion
- non-collinear per-channel centroid / spread matches
- target-preserving vs blocker-preserving comparisons
- reporting-only classification
- no gate / verdict / threshold / control / descriptor changes
```

The v2.8 plan is recorded as the next **possible** step; it is **not opened here**, and any technical slice it
might later predeclare stays disallowed until separately opened after review. Real clips / local-clip manifest
and memory-system integration stay disallowed, and no §7/§8/threshold/control/descriptor change may be made
without a fresh freeze and adversarial review.

- **Codex review** of this synthesis frame and of the recommendation to open the docs-only v2.8 broader
  matched-pair diagnostic **plan** next (branch A as a predeclared reporting-only plan), keeping branches B, C,
  and D recorded-but-unopened, the verdict at HOLD, and all disallowed moves disallowed.
- **If the operator explicitly opens the next docs-only slice, it should be that v2.8 plan; otherwise HOLD.**

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False` and `temporal_claim_allowed = False` are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Color Structure Residual Synthesis and Next-Decision Frame v2.7. Docs-only,
non-authorizing. Opens no implementation lane; changes no frozen formula, gate, or verdict; deletes or weakens
no control; invents no threshold; makes no descriptor-validity claim; no `§0` pointer added; no tags.*

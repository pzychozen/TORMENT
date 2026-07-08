# TORMENT Brainvision Color Structure Pooled-Gate Audit Plan v1.7

## 1. Status / quarantine and non-claims

**DOCS-ONLY audit plan. Non-authorizing, non-implementing. Opens no runtime, integration, or implementation
lane.** It plans *what an audit would inspect* to identify which pooled components drive the remaining §7
HOLD under the **unchanged** frozen gate. It **authorizes no code and no tests**, invents no threshold,
proposes no replacement acceptance criteria, changes no formula / gate / verdict, and deletes no control.
Everything discussed stays offline under `research/brainvision/` + `tests/research/`, HELD per v0.6.

This note makes **no** vision claim, **no** "Brainvision sees" claim, and **no** temporal-order claim.
`first_pass_structure_validity_claim_allowed` remains **False** and `temporal_claim_allowed` remains
**False**. It touches no `torment_service/`, runtime, camera / sensor / live-capture / screen-capture /
streaming, or prompt / context / memory / action / render-body / autonomy paths, and makes **no real-clip /
local-clip move** and **no memory-system integration**. **No `§0` pointer; no tags.**

**Memory-system pointer (explicit):**

```text
Brainvision Path B is not proven vision and is not a functioning vision layer for TORMENT memory.
It remains offline/quarantined descriptor research and has no memory/context/runtime authority.
```

## 2. Accepted v1.6 decision

v1.6 (edge `ac0fb9d`) framed the mismatch between the pairwise movement-matched evidence and the pooled §7
HOLD, and recorded **three possible readings**, **none opened for implementation**:

- **A. Pooled-gate / validity-surface framing issue** — the frozen §7 anti-proxy surface may need later
  docs-only scrutiny as a validity surface for a winding / coherence descriptor.
- **B. Fixture / control-composition issue** — the pooled bank's nulls / controls may reintroduce movement
  / `S` covariance that a better (still-uncherry-picked) composition would not.
- **C. Residual descriptor limitation** — `PSC / AIC / S` may still fail as a general
  descriptor-control-valid signal beyond the planted synthetic pairs.

## 3. Accepted facts (restated)

- Current edge: `ac0fb9d` (`docs(research): frame brainvision pooled gate interpretation`).
- Prior implementation edge: `cf4b4d6` (`research(brainvision): add movement-matched chroma diagnostic`).
- Prior findings edge: `913758d` (`docs(research): record brainvision chroma movement-matched findings`).
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

Matched-pair readout (reporting-only): exact movement match, yet `S` / `PSC` separated sharply.

```text
u_ddr_abs_diff = 0.0        winders:     S = 1.000       PSC = 1.00
ang_abs_diff   = 0.0        non-winders: S ≈ 0.17–0.18   PSC ≈ 0.03
```

**Accepted interpretation (preserved):** `S` is **not merely movement amount** in these synthetic matched
pairs, which **weakens the strongest bad reading from v1.3**; but this does **not** establish
descriptor-control validity, does **not** establish temporal-order sensitivity, does **not** establish
vision, and does **not** establish a functioning vision layer for the memory system. The frozen pooled §7
anti-proxy gate **still HOLDs**.

## 4. Audit question

```text
Which pooled components drive the remaining §7 HOLD under the unchanged gate,
and do those failures look like legitimate descriptor blockers, fixture/control-composition artifacts,
or validity-surface framing mismatches?
```

The audit only **observes and attributes** the existing pooled Spearman result under the frozen gate. It
does not change the gate, and its output cannot move the verdict.

## 5. Audit objects to inspect later (categories only; not implemented here)

Predeclared *categories* of what a later audit could look at — no metric is built or authorized by this
note:

- **Bank-entry / fixture-class contribution** to the failing Spearman stats (which entries move `S` and the
  failing stat together).
- **Null / control contribution** to movement / `S` covariance (how much the trajectory-order nulls and
  the structureless / continuity controls drive the pooled association).
- **Directional-stats contribution:** `u_directional_delta_rms`, `angular_increment_mag`, and their
  null-relative (`nr_`) versions.
- **Per-channel spectral-stats contribution:** `rg_centroid`, `by_centroid`, `rg_spread`, `by_spread`, and
  their null-relative (`nr_`) versions.
- **Subset comparison** of the pooled Spearman across: the **matched-pair subset**, the **full pooled
  bank**, the **null / control subset**, the **coherent-winder subset**, and the
  **non-winder / cancelling subset**.

Any view beyond re-reading the existing frozen stats must be explicitly marked a **"possible reporting-only
audit view"** and is **not** acceptance criteria; no new metric is invented as a gate.

## 6. Non-goals

The audit (and this plan) explicitly does **not**:

- edit §7;
- redesign acceptance criteria;
- change any threshold;
- delete any fixture / control;
- cherry-pick fixtures or subsets to obtain a pass;
- redesign the descriptor;
- implement anything;
- touch real clips;
- integrate with the memory system;
- make any vision claim.

## 7. Classification frame (reporting-only)

The audit should classify each major pooled failure as exactly one of:

1. **likely legitimate descriptor blocker** (Reading C),
2. **likely fixture / control-composition artifact** (Reading B),
3. **likely validity-surface framing mismatch** (Reading A),
4. **unresolved / needs adversarial review**.

**Important:** this classification is **reporting-only** and **cannot change the verdict**. A failure
classified "artifact" or "framing mismatch" still leaves the frozen gate at **HOLD**; the classification is
a hypothesis to review, not a re-grade.

## 8. Required future-implementation guardrails

If a later implementation slice is opened *after* this docs-only plan (and only after review + operator
approval), it must:

- **report under the unchanged frozen §7 gate**;
- **produce decomposition tables only** (attribution of the existing pooled Spearman, not a new score);
- **preserve all existing controls**;
- **not remove any failing control to obtain a pass**;
- **not modify formulas**;
- **not modify thresholds**;
- **not define replacement acceptance criteria**;
- **preserve HOLD unless the existing frozen gate actually passes**;
- **keep all outputs offline** under `research/brainvision/` and `tests/research/`.

## 9. Recommended next after v1.7

- **Codex review first** — of this audit plan and of whether it stays diagnostic (attribution under the
  unchanged gate) rather than becoming a route to loosening the gate.
- **If accepted**, the next *possible* slice may be a **narrow audit implementation**, but only after review
  and explicit operator approval. It must be framed as:

```text
decompose pooled HOLD causes under unchanged §7
```

and **not** as:

```text
make the pooled gate pass
```

Readings A, B, and C remain recorded-but-unopened; the real-clip / local-clip move and any memory-system
integration stay disallowed.

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False` and `temporal_claim_allowed = False` are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Color Structure Pooled-Gate Audit Plan v1.7. Docs-only, non-authorizing. Opens no
implementation lane; changes no frozen formula, gate, or verdict; deletes no control; invents no threshold;
no `§0` pointer added; no tags.*

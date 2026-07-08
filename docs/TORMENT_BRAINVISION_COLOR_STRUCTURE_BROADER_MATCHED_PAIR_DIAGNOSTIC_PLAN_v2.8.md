# TORMENT Brainvision Color Structure Broader Matched-Pair Diagnostic Plan v2.8

## 1. Status / quarantine and non-claims

**DOCS-ONLY diagnostic plan. Non-authorizing, non-implementing. Opens no runtime, integration, or
implementation lane.** It predeclares *what a later reporting-only diagnostic would test* to broaden the
matched-pair evidence for the two unresolved v2.7 candidates, under the **unchanged** frozen §7/§8 machinery. It
**authorizes no code and no tests**, invents no threshold, proposes no replacement acceptance criteria, changes
no formula / §7 anti-proxy logic / §8 verdict logic, deletes or weakens no control, and implements no fixture.
Everything discussed stays offline under `research/brainvision/` + `tests/research/`, HELD per v0.6.

This note makes **no** vision claim, **no** "Brainvision sees" claim, and **no** temporal-order claim.
`first_pass_structure_validity_claim_allowed` remains **False** and `temporal_claim_allowed` remains **False**.
It touches no `torment_service/`, runtime, camera / sensor / live-capture / screen-capture / streaming, or
prompt / context / memory / action / render-body / autonomy paths, and makes **no real-clip / local-clip move**
and **no memory-system integration**. Brainvision Path B is **not proven vision** and is **not a functioning
vision layer for TORMENT memory**. **No `§0` pointer; no tags.**

**This is a PLAN only. No implementation.** `implementation_opened = False`, `gate_change_allowed = False`,
`control_deletion_allowed = False`, `descriptor_validity_claim_allowed = False`.

## 2. Accepted premise from v2.7

Carried forward by identity from the accepted synthesis (edge `b39a549`,
`docs(research): synthesize brainvision residual next decision`). The verdict **remains HOLD**.

v2.7 recommendation:

```text
next_recommended_branch = broader_matched_pair_diagnostic_plan
implementation_opened   = False
verdict                 = HOLD
```

Closed residual map (v2.4 / v2.5 / v2.6):

```text
directional axis:
  directional_validity_surface_mismatch_candidate = True
  directional_proxy_failure_resolved              = False
per-channel-spectral axis:
  per_channel_bank_composition_artifact_candidate = True
  per_channel_proxy_failure_resolved              = False
  control_deletion_allowed                        = False
A_descriptor_limitation:
  not supported by current matched-pair evidence
```

Both sub-axes are *characterized but unresolved*, and the supporting matched-pair evidence is narrow and
synthetic (a small predeclared family; the per-channel matches are collinear). This plan predeclares how to
broaden that evidence.

## 3. Diagnostic objective

v2.8 predeclares a **later possible reporting-only diagnostic** to broaden the matched-pair coverage. Its
objective is explicitly bounded:

- The objective is **not** to pass §7.
- The objective is **not** to relax §7.
- The objective is **not** to delete or weaken controls.
- The objective is **not** to prove descriptor validity.
- The objective **is** to test whether the current **B** (directional validity-surface mismatch) and **C**
  (per-channel bank-composition artifact) candidate readings **survive broader matched-pair coverage** — i.e. to
  strengthen or weaken each candidate on evidence, under the unchanged gate, reporting-only.

No output of the later diagnostic can move the verdict; it can only re-characterize the two unresolved
candidates.

## 4. Required matched-pair expansions

Predeclared *families* a later diagnostic would build (no fixture is implemented or authorized here).

**Family-list predeclaration rule (applies to families A–C).** v2.9 must **predeclare the intended family list
before implementation**. Any **omitted, failed, or infeasible** construction must be **reported as such**;
failed constructions must **not** be silently dropped or replaced by friendlier pairs. The reported result set
must correspond to the predeclared list, with feasibility annotated per family.

### A. Directional matched expansion

**Purpose.** Test the directional validity-surface mismatch candidate beyond the current single movement family.

**Required properties.**

- vary coherent winding vs cancellation;
- hold `u_directional_delta_rms` and `angular_increment_mag` matched to a **predeclared tolerance**: v2.9 must
  fix the matching tolerance **before implementation**, or explicitly reuse an existing descriptive tolerance
  (e.g. `MATCH_REPORT_DELTA`) as **reporting-only**. That tolerance must **not** become a §7/§8 threshold, a
  pass/fail criterion, or a verdict-moving acceptance rule. **All residual deltas must be reported, including
  imperfect matches** — the "matched" label is descriptive only;
- include a **predeclared list** of angular speeds / radii / phase offsets (see the family-list rule below);
- include cases of **smoothness without coherent winding**, defined operationally as: a smooth directional
  trajectory (low directional blockers `u_directional_delta_rms` / `angular_increment_mag`) with a
  **low-`PSC` and/or low-`AIC` nonwinder** criterion. For each such case report `S`, `PSC`, `AIC`,
  `u_directional_delta_rms`, and `angular_increment_mag`. If the case **cannot be constructed**, report it as
  **infeasible / unresolved** rather than forcing a substitute.

**Reporting (reporting-only).**

- delta `S`;
- delta `PSC`;
- delta directional blockers;
- whether `S` / `PSC` separates at fixed blocker;
- whether smoothness-alone cases stay **low** `S` / `PSC`.

### B. Non-collinear per-channel centroid / spread matches

**Purpose.** Test the per-channel bank-composition artifact candidate beyond the `collinear_1` / `collinear_2`
matches used in v2.4.

**Required properties.**

- match RG/BY centroid **without using only collinear cancellers**;
- match RG/BY spread **without using only collinear cancellers**;
- include **non-collinear** cancellation partners;
- include controls that occupy similar RG/BY centroid / spread regions as winders **without** coherent winding.

**Reporting (reporting-only).**

- delta `S`;
- delta `PSC`;
- delta centroid / spread blockers;
- whether `S` / `PSC` separates at fixed per-channel blocker;
- whether per-channel null / control geometry still drives the pooled association.

### C. Target-preserving vs blocker-preserving comparisons

**Purpose.** Separate target variation from blocker variation.

**Include.**

- target-preserving / blocker-varying cases;
- blocker-preserving / target-varying cases;
- within-family and cross-family Spearman tables;
- pairwise deltas;
- null-relative decomposition.

## 5. Predeclared interpretation rules

Reporting-only categories (declared **before** any implementation so results cannot be fitted to a preferred
conclusion):

```text
directional_B_strengthened
directional_B_weakened
per_channel_C_strengthened
per_channel_C_weakened
A_descriptor_limitation_supported
mixed_or_unresolved
```

Rules:

- **directional_B_strengthened** if broader directional matched pairs **still separate** `S` / `PSC` at fixed
  directional blockers, **and** smoothness-alone nonwinders stay **low** `S` / `PSC`.
- **directional_B_weakened** if smoothness-alone or matched-direction nonwinders score **high** `S` / `PSC`, or
  if separation collapses when the directional blockers are matched.
- **per_channel_C_strengthened** if non-collinear per-channel matched pairs **still separate** `S` / `PSC` at
  fixed centroid / spread, **and** the primaries-only association remains **low** while the pooled / null-control
  association drives the failure.
- **per_channel_C_weakened** if non-collinear matched pairs collapse, or the primaries-only per-channel
  association becomes **high**.
- **A_descriptor_limitation_supported** only if `S` / `PSC` **repeatedly fails to separate** under matched
  blockers across **both** axes, or tracks the blockers directly in within-family decompositions.
- **mixed_or_unresolved** if the results split.

**Predeclared-criteria rule.** The qualitative terms above — "still separate", "low", "high", "repeatedly" —
must be given **predeclared numerical or descriptive criteria before implementation**. v2.9 must fix, up front:

- what counts as `S` / `PSC` **separation**;
- what counts as **low** / **high** `S`, `PSC`, `AIC`;
- what counts as a blocker being **matched**;
- what counts as **repeated support** across families;
- how **mixed evidence** maps to `mixed_or_unresolved`.

These criteria are **reporting-only**. They **cannot** become §7/§8 thresholds, they **cannot** move the
verdict, and they **cannot** be tuned after seeing the results. Any construction or comparison that does not
meet a predeclared criterion is reported as such (including `infeasible` / `unresolved`), never relabelled to a
friendlier category.

The classification is **reporting-only** and **cannot change the verdict**; a "strengthened" or "weakened"
label re-characterizes a candidate, it does not re-grade the frozen gate.

## 6. Guardrails against gate-gaming

The diagnostic (and any later implementation of it) explicitly must not:

- **chase random fixtures** to move a number;
- **select only friendly pairs** (predeclare the families; report all, including unfavorable ones);
- **delete any hard control** (trajectory-order nulls, structureless / continuity controls are load-bearing);
- **re-weight controls**;
- **invent any new threshold** or replacement acceptance criteria;
- **edit §7 or §8**;
- **redesign the descriptor**;
- **convert clean matched evidence into a validity claim**;
- **move to real clips or memory integration after clean results**;
- proceed without separate opening: **later code requires separate opening and adversarial review**, with a
  fresh freeze, before anything is written.

## 7. Recommended later implementation shape

Only as a *possible* **v2.9 reporting-only diagnostic** — **not opened here**. Possible later files:

```text
research/brainvision/run_color_structure_broader_matched_pair_diagnostic_v2_9.py
tests/research/test_brainvision_color_structure_broader_matched_pair_diagnostic_v2_9.py
docs/TORMENT_BRAINVISION_COLOR_STRUCTURE_BROADER_MATCHED_PAIR_DIAGNOSTIC_FINDINGS_v2.9.md
```

Such a diagnostic would, if ever opened, reuse the frozen v0.7/v0.8 machinery and the existing bank by identity,
implement the §4 families, apply the §5 interpretation rules, and report under the unchanged gate — producing
decomposition tables only, with the verdict taken from the frozen §8 logic (HOLD) and structurally barred from
upgrading.

**v2.8 opens none of this.** It is a plan; the v2.9 slice is recorded as the next **possible** step and must not
begin until separately opened after review and explicit operator approval.

## 8. Decision outcome flags

Recorded outcome (reporting-only; none of these move the verdict or any gate):

```text
broader_matched_pair_plan_ready             = True
implementation_opened                       = False
gate_change_allowed                         = False
control_deletion_allowed                    = False
descriptor_redesign_allowed                 = False
descriptor_validity_claim_allowed           = False
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed                      = False
verdict                                      = HOLD
```

`broader_matched_pair_plan_ready = True` records that the plan is predeclared; `implementation_opened = False`
records that no code, fixture, test, gate, threshold, control, or descriptor change is opened by it. The frozen
§7/§8 machinery, thresholds, and controls are unchanged, and the verdict stays **HOLD**.

- **Codex review** of this plan and of whether it stays a bounded, reporting-only, predeclared broadening
  (strengthen / weaken the B and C candidates under the unchanged gate) rather than a route to passing or
  relaxing §7, deleting controls, or making a validity claim.
- **If the operator explicitly opens the next docs-only-then-code slice, it should be the v2.9 diagnostic;
  otherwise HOLD.**

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False` and `temporal_claim_allowed = False` are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Color Structure Broader Matched-Pair Diagnostic Plan v2.8. Docs-only,
non-authorizing. Opens no implementation lane; changes no frozen formula, gate, or verdict; deletes or weakens
no control; invents no threshold; implements no fixture; makes no descriptor-validity claim; no `§0` pointer
added; no tags.*

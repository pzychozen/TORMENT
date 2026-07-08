# TORMENT Brainvision Color Structure Pooled-Gate Audit Findings v1.8

## 1. Status / quarantine and non-claims

**DOCS-ONLY findings receipt. Non-authorizing, non-implementing.** It records what the v1.8 pooled-gate
audit actually found, using **Windows repo truth as authoritative**. It **authorizes no code and no tests**,
invents no threshold, defines no replacement acceptance criteria, changes no formula / §7 gate / §8 verdict,
and deletes or weakens no control. Everything discussed stays offline under `research/brainvision/` +
`tests/research/`, HELD per v0.6.

This note makes **no** vision claim, **no** "Brainvision sees" claim, and **no** temporal-order claim.
`first_pass_structure_validity_claim_allowed` remains **False** and `temporal_claim_allowed` remains
**False**. It touches no `torment_service/`, runtime, camera / sensor / live-capture / screen-capture /
streaming, or prompt / context / memory / action / render-body / autonomy paths, and makes **no real-clip /
local-clip move** and **no memory-system integration**. **No `§0` pointer; no tags.**

## 2. What was run

- v1.7 plan edge: `f267f07` (`docs(research): plan brainvision pooled gate audit`).
- v1.8 implementation edge: `af39175` (`research(brainvision): audit pooled gate hold causes`).
- v1.8 files:
  - `research/brainvision/run_color_structure_pooled_gate_audit_v1_8.py`
  - `tests/research/test_brainvision_color_structure_pooled_gate_audit_v1_8.py`
- **Windows validation (authoritative):** v1.8 audit tests **13 passed**; full Brainvision research suite
  **163 passed**.
- Verdict remains **HOLD**. The audit is **reporting-only** and **cannot convert HOLD to pass** — the
  verdict is taken verbatim from `mm.run()`, and every subset / leave-one-out / classification output is an
  attribution view, not a gate.

## 3. Split result

The audit did **not** show "everything is clean." It **split** the remaining pooled §7 HOLD into two
qualitatively different kinds of failure:

```text
Directional pooled failures mostly look null/control-driven.
Spectral/std blockers survive exact movement matching.
```

## 4. Four matched-subset blockers (Windows truth)

The audit surfaced four stats that fail the movement-matched primary-pair subset (the controlled-movement
comparison), each reported as `likely legitimate descriptor blocker`:

```text
spectral_centroid: pooled fail, matched fail
by_std:            pooled pass, matched fail
rg_spread:         pooled pass, matched fail
nr_rg_spread:      pooled pass, matched fail
```

Interpretation:

- `spectral_centroid` is **not merely a masked blocker**: on Windows truth it fails **both** the pooled and
  the movement-matched views. (Its pooled `|rho|` sits near the 0.30 ceiling and is numerically
  platform-marginal; Windows is the source of truth and reads it as a pooled failure.)
- `by_std`, `rg_spread`, and `nr_rg_spread` are **masked by the pooled view** (they pass the pooled gate)
  but **fail the movement-matched subset**.
- All four are **reporting-only** `likely legitimate descriptor blocker` evidence — the classification is a
  hypothesis for review, not a re-grade, and it does not move the verdict.
- Because these stats fail even when directional movement is exactly matched, this **strengthens Reading C
  specifically on the spectral / std axis**: `S` carries a per-channel spectral / std dependency that
  survives movement matching.

## 5. Directional failures

Most of the pooled directional failures (the `u_directional_delta_rms` / `angular_increment_mag` /
per-channel centroid family and their null-relative versions) appear **driven by the null / control
structure** of the pooled bank and do **not** behave like the matched-subset blockers — they are below the
ceiling on the clean matched-pairs subset but exceed it on the null / control subset.

This must **not** be overstated. It does **not** show "the pooled gate is wrong," and it must **not** be
used to delete controls. The correct framing is:

```text
The audit localizes the source of different failures; it does not resolve the validity-surface question.
```

## 6. What this means

```text
The descriptor is not merely movement amount.
But it still carries spectral/std dependencies under exact movement matching.
Therefore the next functional target is spectral/std deconfounding, not real clips and not memory integration.
```

## 7. Recommended next slice

**Next possible implementation slice, if explicitly opened: `v1.9 spectral/std blocker diagnostic`.**

Possible files:

```text
research/brainvision/run_color_structure_spectral_std_blocker_v1_9.py
tests/research/test_brainvision_color_structure_spectral_std_blocker_v1_9.py
```

Purpose:

```text
test whether S/PSC can still separate coherent winding from cancellation when spectral_centroid, by_std,
rg_spread, and nr_rg_spread are explicitly matched, neutralized, or orthogonalized
```

Not:

```text
make the gate pass
delete controls
change §7
claim vision
```

This is recorded as the next **possible** slice; it is not opened here. Any such slice must report under the
unchanged frozen §7 gate, preserve all controls, invent no threshold, define no replacement acceptance
criteria, and keep the verdict at HOLD unless the existing frozen gate actually passes. Real clips /
local-clip manifest and memory-system integration stay disallowed.

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False` and `temporal_claim_allowed = False` are unchanged.
**No `§0` pointer; no tags.**

## 8. Recommended next

- **Codex review** of this findings receipt.
- **If the operator explicitly opens the next slice**, it should be the `v1.9 spectral/std blocker
  diagnostic`; otherwise HOLD.

*End — TORMENT Brainvision Color Structure Pooled-Gate Audit Findings v1.8. Docs-only, non-authorizing.
Opens no implementation lane; changes no frozen formula, gate, or verdict; deletes no control; invents no
threshold; no `§0` pointer added; no tags.*

# TORMENT Brainvision ΨTRS Boundary-Neutral Companion Implementation Decision v0.8

## 1. Status / quarantine

**DOCS-ONLY decision note. Non-authorizing, non-implementing.** It closes the operational and reporting
forks identified by the read-only implementation-readiness scan for the boundary-neutral companion, so that
the companion is fully specified *and* operationally decided before any future implementation. It builds
nothing. Governing sources:
`TORMENT_BRAINVISION_PSI_TRS_BOUNDARY_NEUTRAL_COMPANION_FORMAL_SPECIFICATION_v0.7.md` (the O1+A3 contract),
`TORMENT_BRAINVISION_PSI_TRS_REAL_VIDEO_BOUNDARY_NEUTRAL_DUAL_REPORTING_DESIGN_v0.6.md` (the raw+companion
dual-reporting design), and `research/brainvision/run_prerecorded_paired_analysis_v0_1.py` (the current
analyzer and CLI). The decision basis is the operator-supplied implementation-readiness findings.

**Implementation remains unauthorized.** Work stays quarantined under `research/brainvision/` +
`tests/research/`. No `torment_service` change; no live capture; no camera or sensor route; no provider or
live-model route; no prompt / context / memory / action contact; no MCP, movement, autonomy, or
render-body route; no database, substrate, carrier, or Stage-B route; no classifier claim; no
temporal-order claim; no perception claim. **No `§0` pointer update; no tags.** No Python, tests, analyzer,
`.npz` inputs, generated outputs, or the v0.7 specification are changed by this note; no experiment is run.

## 2. Decision 1 — CLI execution policy

The companion is an **explicit opt-in**:

```text
CLI policy = explicit opt-in
flag       = --with-boundary-neutral-companion
default    = disabled
```

**When the flag is absent:**

- the companion is not evaluated;
- no companion descriptor calls occur;
- existing raw analysis behavior remains unchanged;
- existing human output remains unchanged;
- existing JSON structure remains unchanged;
- **no `boundary_neutral_companion` key and no disabled stub are emitted**.

The absence of a disabled stub is **deliberate**: it preserves the existing default serialized output
rather than changing every default result merely to report that an optional, expensive analysis was not
requested.

**When the flag is present:**

- raw analysis still runs normally;
- raw numerical values, keys, and meanings remain unchanged;
- the companion is computed under the complete v0.7 **O1 + A3** contract;
- the companion is emitted as a structurally separate sibling section.

**The flag controls execution only.** It must not change: offset count; offset ordering; descriptor
domain; pairing; aggregation; nonfinite policy; diagnostics; raw semantics; or scientific interpretation.

### 2.1 Rationale

```text
the current nine-clip run would add approximately 55,296 companion descriptor calls
silent default activation would impose a large execution-cost change
historical default analyzer behavior and deterministic replay should remain stable
explicit opt-in makes the additional analysis intentional and visible
```

(The ~55,296 figure is the operator-supplied readiness estimate: 9 clips × 4 blocks × 6 controls × 2
companion descriptors × 64 starts × 2 feature evaluations per matched start. It is recorded as the cost
basis for the opt-in decision, not as a new experimental result.)

This is a **current-fixture estimate** derived from the present nine clips, four blocks per clip, six
controls, two companion descriptors, 64 starts, and true/control feature evaluation. It is **not** a
universal fixed cost: actual cost scales with the number of clips, 64-row blocks, and controls while the
O1 per-block/control semantics remain fixed.

Additionally:

- explicit opt-in **does not weaken** the accepted raw-plus-companion reporting design;
- when companion mode is enabled, **raw and companion results must both be reported**;
- the companion **may never replace** raw results.

The opt-in decision is **not** a reduced scientific candidate and **not** an approximation. **O1 still
evaluates all 64 starts whenever the companion is enabled.**

## 3. Decision 2 — JSON reporting

```text
JSON is the complete machine-readable companion report
```

When the flag is enabled, add **one separate per-clip sibling key** named `boundary_neutral_companion`. Its
narrow structural form (conceptual, not a frozen Python object layout):

```text
boundary_neutral_companion:
  included: true
  descriptor_domain:
    - psi_trs
    - psi_trs_k0
  offset_policy: O1 — all 64 starts
  aggregation_policy: A3 — mean normalized response across matched starts
  per_control:
    <control>:
      per_block:
        - block: <block_index>
          psi_trs:
            per_start_responses
            finite_count
            nonfinite_count
            offending_nonfinite_offsets
            mean
            median
            IQR
            minimum
            maximum
            mean_median_ratio
            epsilon_hit_count
            near_epsilon_hit_count
            minimum_denominator
            maximum_denominator
            number_of_starts
            offset_policy
            aggregation_policy
          psi_trs_k0:
            per_start_responses
            finite_count
            nonfinite_count
            offending_nonfinite_offsets
            mean
            median
            IQR
            minimum
            maximum
            mean_median_ratio
            epsilon_hit_count
            near_epsilon_hit_count
            minimum_denominator
            maximum_denominator
            number_of_starts
            offset_policy
            aggregation_policy
          companion_response_psi_trs
          companion_response_psi_trs_k0
          companion_recursive_delta
          raw_minus_companion_psi_trs
          raw_minus_companion_psi_trs_k0
          raw_minus_companion_recursive_delta
```

This is a **structural decision, not an implementation schema** frozen down to incidental object layout;
any conforming implementation must preserve an explicit block identifier or an equivalent unambiguous
block-indexed structure.

**Block-level scope contract:**

```text
Every companion descriptor report, companion response, recursive delta, and
raw-minus-companion value is defined and emitted at the block/control level.

No clip-level or cross-block companion aggregation is authorized by this
decision or by v0.7.

Multiple block-level companion distributions must never be silently averaged,
pooled, merged, or collapsed into one control-level scalar or distribution.

Any future cross-block aggregation would require a separate mathematical
specification, decision, and authorization.
```

The six derived scalars —

```text
companion_response_psi_trs
companion_response_psi_trs_k0
companion_recursive_delta
raw_minus_companion_psi_trs
raw_minus_companion_psi_trs_k0
raw_minus_companion_recursive_delta
```

— live **inside each block/control record**. They must not appear directly as clip-level or control-level
scalars unless a future, separately authorized aggregation contract exists. The existing raw and companion
separation is preserved.

It must also require:

- all 64 `per_start_responses` present in JSON, for **every block/control descriptor evaluation**;
- canonical offset order `0..63`;
- semantic unavailable values serialized as `null`;
- no `NaN` or `Infinity`;
- raw and companion sections visibly separate.

The companion section **must not be emitted when the flag is absent**.

## 4. Decision 3 — Human reporting

```text
human output does not print all 64 per-start response values by default
```

When the flag is enabled, human output must show at minimum, **for every block and control** (each block
identified explicitly by its block index or an equivalent unambiguous identifier):

```text
raw psi_trs response
companion psi_trs response
raw_minus_companion_psi_trs

raw psi_trs_k0 response
companion psi_trs_k0 response
raw_minus_companion_psi_trs_k0

raw recursive_delta
companion_recursive_delta
raw_minus_companion_recursive_delta

finite_count
nonfinite_count
offending_nonfinite_offsets
mean
median
IQR
minimum
maximum
mean_median_ratio
epsilon_hit_count
near_epsilon_hit_count
minimum_denominator
maximum_denominator
```

These fields are shown at **block/control granularity**; the existing required raw, companion, raw-minus,
recursive-delta, distribution, and denominator fields are unchanged in content but must be reported per
block and control.

```text
Human reporting must list block-level results separately.

It must not silently average, pool, merge, or collapse companion results across
blocks.

No cross-block human summary is authorized unless it is clearly derived from a
separately specified and authorized aggregation rule.
```

It must also state clearly:

```text
Full per-start responses are emitted by JSON-format output. When running with
`--format human`, rerun with `--format json` or `--format both` to emit the
complete 64-start response lists.
```

For `--format both`, both the human summary and the complete JSON companion report are emitted. For
`--format json`, only the complete JSON-format report is emitted. For `--format human`, only the
block/control human summaries are emitted; no hidden JSON artifact or file is created. Default no-write
behavior is preserved.

The human wording must remain **descriptive** and must not imply descriptor superiority, temporal-order
sensitivity, arrow of time, perception, inference, significance, or mechanism proof.

When the flag is absent, human output remains exactly on the existing raw path and contains **no companion
placeholders**.

## 5. Orthogonality to existing CLI behavior

The new flag must remain **orthogonal** to `--format json`, `--format human`, `--format both`, `--no-sag`,
and the default no-write behavior:

```text
--with-boundary-neutral-companion --no-sag
  computes the companion normally and omits SAG only

--format json
  includes the full companion section when enabled

--format human
  includes companion summaries when enabled

--format both
  includes both corresponding reports when enabled
```

The companion flag **must not introduce file writing**; default no-write behavior is unchanged.

## 6. Descriptor and helper architecture standing (readiness recommendation, not implemented)

```text
future implementation should use one isolated companion helper
descriptor domain must be structurally restricted to {psi_trs, psi_trs_k0}
existing raw descriptor_responses behavior must not be widened or changed
current finite-filtering statistical helpers must not be reused where they
  would violate the all-64-valid companion contract
```

The safest initial implementation **recomputes start `s = 0` within the companion path** rather than
reusing raw fixed-start outputs. This avoids coupling historical raw behavior to companion internals.

```text
s=0 reuse is not authorized in the first implementation
```

This is an **engineering conservatism** decision, not a mathematical requirement. A later optimization that
reused `s=0` raw outputs would require **separate proof** that it preserves exact arrays, diagnostics,
ordering, and raw independence.

## 7. Non-claims and boundaries

Every existing Brainvision quarantine and non-claim is preserved. This decision opens no runtime route; no
live capture route; no camera or sensor route; no prompt / context / memory / action contact; no MCP or
movement route; and no classifier, inferential, temporal-order, or perception claim. The companion, when
enabled, measures only the mean normalized matched transform sensitivity across all 64 circular starts, as
bounded by v0.6 and v0.7.

## 8. Required future tests (specified, not implemented)

A future implementation must add tests proving:

1. Default invocation remains on the historical raw-only path.
2. Default JSON contains no companion key.
3. Default human output contains no companion placeholders.
4. The opt-in flag activates the complete v0.7 companion.
5. JSON emits all 64 values.
6. Human output emits summaries and points to JSON for the full distribution.
7. `--no-sag` remains orthogonal.
8. All `--format` modes remain compatible.
9. Default no-write behavior remains unchanged.
10. `s = 0` is independently recomputed in the initial implementation.
11. Every companion result retains explicit block identity.
12. Every descriptor distribution is emitted separately for each block/control.
13. All six companion, recursive-delta, and raw-minus scalar fields live at the block/control level.
14. Multiple blocks are never silently averaged, pooled, merged, or collapsed.
15. JSON contains all 64 per-start responses for every block/control descriptor evaluation.
16. Human output identifies each block and control separately.
17. `--format human` does not claim that JSON was emitted and instead explains how to request JSON-format output.
18. No cross-block aggregation exists without a separately authorized contract.

(No tests are added by this note.)

## 9. Implementation standing

```text
implementation_readiness = READY_AFTER_RECORDED_OPERATIONAL_DECISION

cli_policy_resolved            = True
human_reporting_policy_resolved = True
json_reporting_policy_resolved  = True
s0_reuse_authorized            = False

candidate_implemented          = False
implementation_authorized      = False
experiment_authorized          = False

FORMAL_HOLD_active             = True
Mode_0_active                  = True
verdict                        = HOLD
```

No unresolved operational or reporting fork remains: CLI execution policy, JSON reporting, and human
reporting are all decided; companion results are scoped to the block/control level and cross-block
aggregation is prohibited absent a separate mathematical specification, decision, and authorization.
Implementation, when it happens, remains a separate authorization.

*End — TORMENT Brainvision ΨTRS Boundary-Neutral Companion Implementation Decision v0.8. Docs-only,
non-authorizing, non-implementing. Opens no implementation lane; no `§0` pointer added; no tags.*

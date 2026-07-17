# TORMENT Brainvision N=64 Falsifier First-Evaluation Findings v0.1

## 1. Status / quarantine

**DOCS-ONLY findings synthesis. Non-authorizing, non-implementing.** This note records a bounded,
descriptive engineering reading of an existing, already-generated first evaluation of the exact independent
N=64 homometric falsifier against the ΨTRS descriptor. It builds nothing and changes nothing. It records and
describes what the canonical output already contains; it selects no threshold, comparability policy, or
success criterion.

Work stays quarantined under `research/brainvision/` + `tests/research/`. This note does **not**: change
code; change tests; change `psi_trs.py`; change any production TORMENT file; rerun the evaluation; create new
fixtures, controls, or inputs; mutate the accepted N=64 fixture; tune thresholds; copy the canonical output
into the repository; commit or push; update `§0`; update registry or orientation pointers; or open any
runtime, live-capture, camera, sensor, memory, prompt, context, action, MCP, movement, autonomy,
render-body, database, substrate, carrier, or Stage-B route. It makes no higher-order-detection,
triple-correlation-specificity, temporal-order, arrow-of-time, perception, vision, classification, causality,
recursive-mechanism, or statistical-significance claim.

Governing standing (preserved exactly):

```text
FORMAL_HOLD_active                 = True
Mode_0_active                      = True
verdict                            = HOLD

documentation_authorized           = True
existing_output_recording_authorized = True
new_experiment_authorized          = False
implementation_change_authorized   = False
scientific_claim_authorized        = False
temporal_order_claim_authorized    = False
perception_or_vision_claim_authorized = False
runtime_integration_authorized     = False
production_kernel_modification_authorized = False
```

## 2. Governing sources

Method and evaluation semantics are authoritatively defined by the committed prototype, contract,
implementation specification, runner, fixture, and descriptor; the canonical stdout captures are treated as
generated evidence, not repository authority.

```text
docs/TORMENT_BRAINVISION_N64_INDEPENDENT_EXTERNAL_HOMOMETRIC_FALSIFIER_MATHEMATICAL_PROTOTYPE_v0.1.md
  (commit 753aade "docs(research): record N64 external homometric falsifier")
docs/TORMENT_BRAINVISION_N64_FALSIFIER_EVALUATION_CONTRACT_v0.1.md
  (commit 5323e58 "docs(research): specify N64 falsifier evaluation contract")
docs/TORMENT_BRAINVISION_N64_FALSIFIER_IMPLEMENTATION_SPECIFICATION_v0.1.md
  (commit a85b80c "docs(research): specify N64 falsifier implementation")
research/brainvision/n64_falsifier_fixture_v0_1.py
research/brainvision/run_n64_falsifier_v0_1.py
tests/research/test_brainvision_n64_falsifier_v0_1.py
  (commit 688709a "research(brainvision): implement N64 falsifier evaluation")
research/brainvision/psi_trs.py   (descriptor; unmodified; no defect found)
```

The runner writes the canonical wrapper to stdout only and imports nothing from `torment_service`. Feature
names used below (`rho_mean`, `rho_std`, `psi_traj_mean`, `psi_traj_std`, `psi_traj_last`) are the
contract's source-derived documentation convention for the positional feature list, not a source-named
schema. All standard deviations are population standard deviation (`ddof = 0`) per contract.

## 3. Evidence provenance and same-environment replay standing

The findings below are recorded from an existing first evaluation produced by exactly **two same-environment
authorized executions** of the committed runner at `688709a`. Both canonical stdout captures were SHA-256
identical and byte-identical under Windows `fc /b`; both stderr captures were empty. The gated candidate test
also passed.

```text
source_commit =
  688709ab49eb3586bac70ede5c1e0a074720981c

canonical_file_sha256 =
  a6637acc48dd8073ad436621eae2ac17019f14fc42e6a2211905228540cc918b

payload_sha256 =
  5b8aa656f135544074c304ec0a759a7b9f1637467a9cfd61c82ae3a7b539cfba

fixture_sha256 =
  41ff48c9a6f92b8d9bf92fc7b6014da9e2a469b83bf0ab633eb9f6b3ba533853

configuration_sha256 =
  2fda2366790a431beb54dd8ec903219d267eed5bfdb42382ac4c2d5880c2dea4

environment_fingerprint_sha256 =
  e2d353e73b09728d48051ac80cff7429d382f810f56c65a0c01db3e9ada9d2a4
```

The two runs establish `B6 = SAME_ENVIRONMENT_BYTE_REPLAY` for this evaluation: identical canonical bytes,
identical SHA-256, empty stderr, `fc /b` clean. Per the implementation specification this external replay
comparison is a match status and does **not** itself contribute to `overall_valid`; internal numerical
validity is a separate object (§4). The canonical outputs are held outside the repository and are **not**
copied into it.

## 4. Validity and numerical-health findings

The canonical `validity` object reports every internal validity boolean true and no error codes:

```text
overall_valid                = True
fixture_valid                = True
schema_valid                 = True
input_valid                  = True
descriptor_valid             = True
self_pair_valid              = True
role_swap_valid              = True
control_completeness_valid   = True
placement_completeness_valid = True
environment_capture_valid    = True
serialization_valid          = True
payload_hash_valid           = True
replay_material_valid        = True

error_code_namespace = torment_brainvision_n64_falsifier_v0_1
error_code_version   = 0.1
error_codes          = []
```

`overall_valid` is the logical AND of every internal validity boolean, excluding error-code metadata. The
exact self-pair (`r = 0`) produced exact finite feature-vector equality, exact-zero numerator, exact-zero
symmetric distance, and exact-zero directional responses under the implementation's
`EXACT_FINITE_IN_PROCESS_SELF_PAIR_EQUALITY` policy. Role-swap left the symmetric primary unchanged; both
validity preconditions held. Self-shift placement (§9) never invalidates numerical validity. This is an **engineering-validity** fact about this exact fixture, encoding, metric,
starts, and implementation only; it is not a scientific result.

## 5. Accepted fixture (recap, not re-derived here)

The evaluation was run against the exact accepted N=64 homometric witness; the fixture layer recomputes these
certificates before interpretation.

```text
N = 64
U = {0,1,3}
V = {0,4,12}
A = U + V     = {0,1,3,4,5,7,12,13,15}
B = U + (−V)  = {0,1,3,52,53,55,60,61,63}

weight(A) = weight(B) = 9
complete periodic autocorrelation identical at all 64 lags
directed one-step table: c00=50, c01=5, c10=5, c11=4
T_A(4,12) = 3 , T_B(4,12) = 0
ordered labeled triple-array disagreements = 264
```

Under the declared certificate scope, `A` and `B` match on value multiset, weight, complete periodic
autocorrelation, absolute transition-magnitude multiset, and complete directed one-step transition table.
Their complete labeled triple-correlation arrays differ, while their complete unlabeled triple-value
histograms match. This does not claim that the labeled triple arrays are their only possible mathematical
difference. The labeled triple array is a pre-run fixture-admissibility
certificate, kept strictly separate from any ΨTRS response.

## 6. Headline findings

The following are accepted findings-synthesis labels derived from the canonical output and bounded
interpretation. They are not canonical runner fields, statistical tests, or predeclared pass/fail thresholds.

```text
N64_EVALUATION_ENGINEERING_PASS       = True
N64_AB_RESPONSE_NONZERO               = True
N64_KAPPA_COMPANION_INCREASE_ALL_STARTS = True

N64_AB_EXTREME_AGAINST_BOTH_SELF_SHIFT_ORBITS = False
N64_STRONG_FALSIFIER_SUCCESS_ESTABLISHED      = False

result_status =
  VALID_DESCRIPTIVE_MIXED_RESULT_REQUIRING_INDEPENDENT_VALIDATION
```

Read exactly: the run is engineering-valid and reproducible; the A/B symmetric response is finite and nonzero
at every matched start; the full ΨTRS variant exceeds its `kappa=0` companion at all 64 starts. But the
all-start A/B response is **not** extreme against both members' own self-shift orbits (§7), so no strong
falsifier success is established. Under the contract's conservative outcome semantics this is a response to
some evaluated A/B difference — consistent with dependence on components changed by the `kappa=0` ablation —
and is explicitly **not** evidence of triple-correlation specificity, higher-order detection, or
temporal-order sensitivity. It is a mixed, descriptive result that requires independent validation.

## 7. Symmetric A/B aggregates

Symmetric primary metric `d_sym` (§7 of the contract), reported separately per descriptor variant across the
64 common starts:

```text
psi_trs:
  minimum                        = 0.00248834
  median                         = 0.0328561
  mean                           = 0.0380199
  maximum                        = 0.136354
  population_standard_deviation  = 0.0272103
  argmin_start                   = 24
  argmax_start                   = 63

psi_trs_k0:
  minimum                        = 0.0000154075
  median                         = 0.000938991
  mean                           = 0.00129125
  maximum                        = 0.00529897
  population_standard_deviation  = 0.00137052
  argmin_starts                  = [27, 43]
  argmax_start                   = 16
```

Directional means (§8; each direction defined separately, both retained):

```text
psi_trs  member_A_to_member_B  mean = 0.0383197
psi_trs  member_B_to_member_A  mean = 0.0377998
```

Fixed start zero (`s = 0`):

```text
psi_trs    = 0.0182141
psi_trs_k0 = 0.00163011
```

The fixed-start-zero response and the all-start aggregate materially differ (fixed `psi_trs = 0.0182141`
versus all-start mean `0.0380199`). The fixed-start and all-start interpretations therefore materially
differ, confirming that the accepted all-64-start aggregation (F5) was necessary and that a single fixed
start would misrepresent the response for this fixture.

## 8. κ-companion comparison

Orientation `psi_trs_minus_psi_trs_k0`. Symmetric per-start κ differences across the 64 common starts:

```text
minimum         = 0.00215739
median          = 0.0318036
mean            = 0.0367287
maximum         = 0.135472
positive_starts = 64
zero_starts     = 0
negative_starts = 0
```

The full ΨTRS variant produces a larger A/B symmetric response than its `kappa=0` companion at **all 64
starts** for this exact fixture (`N64_KAPPA_COMPANION_INCREASE_ALL_STARTS = True`). The full ΨTRS mean
response was approximately **29.44 times** the `kappa=0` mean response (`0.0380199 / 0.00129125`). Under the
contract's conservative semantics this is "a response consistent with dependence on components removed or
changed by the `kappa=0` ablation." It is **not** a measurement of a recursive contribution and does **not**
validate a recursive mechanism.

## 9. Self-shift orbit placement

Descriptive placement of the A/B all-start mean symmetric distance within each member's own self-shift orbit,
policy `COMPLETE_ORBIT_PLUS_TIE_AWARE_DESCRIPTIVE_PLACEMENT`. The reference distribution for each placement is
the member's **63 nonzero relative-shift aggregates** (`r = 1..63`; the exact self-pair `r = 0` is excluded
from the reference distribution but retained in the orbit). `midrank_fraction = (lower + 0.5·equal) / 63`.

```text
psi_trs against member_A:
  lower / equal / higher = 8 / 0 / 55
  midrank_fraction       = 0.12698412698412698

psi_trs against member_B:
  lower / equal / higher = 33 / 0 / 30
  midrank_fraction       = 0.5238095238095238

psi_trs_k0 against member_A:
  lower / equal / higher = 26 / 0 / 37
  midrank_fraction       = 0.4126984126984127

psi_trs_k0 against member_B:
  lower / equal / higher = 30 / 0 / 33
  midrank_fraction       = 0.47619047619047616
```

Member-local reference summaries (`psi_trs` self-shift responses):

```text
member_A / psi_trs:
  minimum = 0.0270685
  median  = 0.0443932
  mean    = 0.0439916
  maximum = 0.0525508

member_B / psi_trs:
  minimum = 0.0219028
  median  = 0.0365727
  mean    = 0.0372800
  maximum = 0.0482617
```

The all-start A/B `psi_trs` response (mean `0.0380199`) lies relatively **low** within member_A's nonzero
self-shift distribution (midrank `0.127`) and near the **center** of member_B's (midrank `0.524`).
Consequently `N64_AB_EXTREME_AGAINST_BOTH_SELF_SHIFT_ORBITS = False`: the A/B response does not stand out
beyond the members' own circular self-shift responses against both members. Self-shift comparability policy
remains unselected (`self_shift_comparability_policy_selected = False`); this section is a descriptive
placement only, member_A and member_B and the two variants are not pooled, and no specific attribution of the
A/B response to the higher-order distinction is made.

## 10. Feature-difference dominance (descriptive)

Descriptive share of the summed squared matched-feature differences, by source-derived feature name:

```text
psi_trs:
  psi_traj_last                 ≈ 49.22%
  psi_traj_mean                 ≈ 41.29%
  psi_traj_std                  ≈ 8.86%
  all other features combined   ≈ 0.62%

psi_trs_k0:
  rho_mean                      ≈ 61.39%
  rho_std                       ≈ 38.60%
```

Under the accepted encoding (`F9 = RAW_NO_EXTERNAL_NORMALIZATION`) the feature vector is used with raw,
externally unnormalized feature scale. That raw scale contributes to the numerical dominance shown above:
larger-magnitude features contribute disproportionately to the summed squared difference. This decomposition
is descriptive of where the numerical response magnitude sits across features for this exact fixture and
implementation. It does **not** validate a recursive mechanism, does not decompose a mechanism, and is not a
direct measurement of a recursive contribution.

## 11. Bounded interpretation

Permitted (descriptive, for this exact fixture and implementation only):

```text
The A/B response is finite and nonzero for every matched start.

The selected ΨTRS variant produces a larger A/B response than its
kappa=0 companion at all 64 starts for this exact fixture.

The all-start A/B response lies relatively low within member_A's
nonzero self-shift distribution and near the center of member_B's.

The result is descriptive for this exact fixture and implementation.
```

Not permitted (no run under this contract may claim any of these):

```text
higher-order detection
triple-correlation specificity
temporal-order proof
arrow-of-time
perception
vision
classification
statistical significance
causality
recursive-mechanism validation
general descriptor sensitivity or insensitivity
```

A nonzero response is not, by itself, falsifier success. The reported non-extreme placements do not establish
separation from the member-local self-shift reference distributions under a predeclared comparability rule,
because no such rule was selected. They are not proof of insensitivity.

## 12. Disposition

```text
n64_first_evaluation_status =
  BOUNDED_DESCRIPTIVE_ENGINEERING_FINDINGS_RECORDED
evaluation_engineering_pass =
  TRUE (overall_valid, error_codes empty)
same_environment_replay_status =
  BYTE_IDENTICAL_PASS (two runs, SHA-256 equal, fc /b clean, stderr empty)
gated_candidate_test =
  PASS
ab_response =
  FINITE_NONZERO_AT_EVERY_MATCHED_START
kappa_companion_increase =
  ALL_64_STARTS (≈29.44× mean)
ab_extreme_against_both_self_shift_orbits =
  FALSE
strong_falsifier_success =
  NOT_ESTABLISHED
result_status =
  VALID_DESCRIPTIVE_MIXED_RESULT_REQUIRING_INDEPENDENT_VALIDATION
temporal_order_claim =
  NOT_AUTHORIZED
perception_or_vision_claim =
  NOT_AUTHORIZED
new_experiment_status =
  NOT_AUTHORIZED
runtime_integration_status =
  NOT_AUTHORIZED
```

## 13. Next justified direction (recorded, not authorized, not scheduled)

The next justified direction is to **freeze this result** and evaluate an **independently constructed witness
family** — a distinct homometric construction, not derived from this one — to test whether the observed
mixed pattern (nonzero A/B response, all-start κ increase, non-extreme self-shift placement) reproduces. This
direction is recorded only and requires separate review and authorization. It must not:

```text
change the accepted N=64 fixture
mutate this fixture
tune or introduce thresholds
select a self-shift comparability policy to make the current result look decisive
make any result-driven implementation change to the runner, fixture, tests, or descriptor
```

*End — TORMENT Brainvision N=64 Falsifier First-Evaluation Findings v0.1. Docs-only, non-authorizing,
non-implementing. Canonical stdout captures treated as generated evidence, not repository authority;
committed prototype, contract, implementation specification, runner, fixture, and descriptor remain
authoritative for method semantics. `psi_trs.py` and the production TORMENT memory kernel are unmodified. No
`§0` pointer; no registry or orientation update; no tags.*

# TORMENT Brainvision Algebraic N=64 PRIMARY_V0_1 Frozen K=3 Family Evidence and F3 Evaluation Binding v0.1

## 0. Disposition

```text
A. BIND THE FROZEN K=3 FAMILY TO THE EXISTING F3 DOWNSTREAM EVALUATION CONTRACT
```

This document records the exact immutable witness family selected by the completed authoritative freezer and binds that family, without modification, to the already-specified F3 downstream evaluation contract.

This document is:

```text
docs-only
non-implementing
non-executing
offline
quarantined
non-production
descriptor-blind with respect to family construction and selection
```

This document does not authorize:

```text
freezer rerun
candidate-generator rerun
candidate-stream mutation
witness replacement
witness reordering based on response
PsiTRS evaluation
evaluator implementation
descriptor execution
SAG execution
prerecorded operational-harness execution
N64 falsifier rerun
threshold tuning
scientific inference
production integration
production-kernel modification
live capture
```

---

## 1. Governing evidence and specifications

Authoritative freezer findings:

```text
docs/TORMENT_BRAINVISION_ALGEBRAIC_N64_PRIMARY_V0_1_AUTHORITATIVE_FREEZER_FINDINGS_v0.1.md
```

Findings commit:

```text
cdda6c06448d3f4600494093c89c887450823df5
```

Authoritative freezer execution commit:

```text
6ddd02f9f6fdf74721dc9cd620cbb2a0aa0fecc8
```

Existing family and F3 evaluation specification:

```text
docs/TORMENT_BRAINVISION_INDEPENDENT_DESCRIPTOR_BLIND_HIGHER_ORDER_WITNESS_FAMILY_IMPLEMENTATION_SPECIFICATION_v0.1.md
```

This binding document does not amend the existing mathematical witness predicates, family requirements, response object, start policy, self-shift reference policy, validity rules, numerical comparison rule, pair verdicts, family verdicts, or claim boundary.

The existing F3 contract remains authoritative.

---

## 2. Canonical freezer evidence identity

Canonical freeze-result path:

```text
research/brainvision/results/algebraic_n64_primary_v0_1_freeze_v0_1/
  algebraic_n64_primary_v0_1_freeze_result.json
```

Canonical freeze-result payload SHA-256:

```text
35e03a83fee83b7fc13514397e10115b3f6b99f847bf17d20772a0e61376796e
```

Freeze-result whole-file SHA-256:

```text
97af61ea4debf9d66146f3e33f035c17c60965c1d9fed0ebbf3d09ead58cbca5
```

Summary whole-file SHA-256:

```text
d20002382f877ad91df8d27e8943ac90881bdf5c30b2f9b65bf4299841274066
```

Family-manifest SHA-256:

```text
352a49bc8d06a35b41b8783f8a869a1645d93c76ddb91df379492b37106d8151
```

Candidate-decision-ledger SHA-256:

```text
151af61422e34829dd8043bdb4308c1ad775b991eab223b74607db69f8bd9bfb
```

Family-verifier certificate SHA-256:

```text
416d32bba578856b5122402186860643071070c946829020799138da13ee764e
```

Retained candidate-stream payload SHA-256:

```text
70763a2ebbf7ea71267553debee2bf79c2ed3b7b0c016d9a903161074e7bf8c5
```

Replay record:

```text
byte_identical = True

run1_sha256 =
9c848062b9b49ac94225bf39c98c69d4c93c61e82a8a6eb2451fb6806fb28651

run2_sha256 =
9c848062b9b49ac94225bf39c98c69d4c93c61e82a8a6eb2451fb6806fb28651
```

---

## 3. Frozen family identity

```text
N = 64
K = 3 pairs
six members total
accepted candidate indices = [478, 479, 480]
accepted order indices = [0, 1, 2]
raw A/B naming = A_LEX_SMALLER_OR_EQUAL
verification mode = PRIMARY_CANDIDATE_N64
```

The exact evaluation order is frozen:

```text
pair 0 = candidate 478
pair 1 = candidate 479
pair 2 = candidate 480
```

The exact member orientation is frozen from the raw-support lexicographic naming rule.

No canonical representative may replace a raw evaluation support.

No affine, reflected, translated, complemented, rotated, reordered, padded, tiled, embedded, resampled, or otherwise transformed support may replace a frozen raw support.

---

## 4. Frozen pair 0 — candidate 478

Pair-verifier certificate SHA-256:

```text
51e72030237da850757979588b4c4107de69a6098ce7c9a3559243b5545edf2b
```

Raw support A:

```text
{0,1,2,4,5,6,7,9,11,12,13,15}
```

Raw support B:

```text
{0,1,3,4,5,7,9,10,11,60,62,63}
```

Member weight:

```text
12
```

Complete periodic autocorrelation, identical for A and B:

```text
[12,7,8,6,7,6,6,5,4,4,3,4,2,2,1,1,
 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
 0,1,1,2,2,4,3,4,4,5,6,6,7,6,8,7]
```

Directed one-step table, identical for A and B:

```text
c00 = 47
c01 = 5
c10 = 5
c11 = 7
```

Absolute transition multiset, identical for A and B:

```text
0 -> 54
1 -> 10
```

Exact verifier results:

```text
pair_valid = True
autocorrelation_equal = True
one_step_table_equal = True
transition_multiset_equal = True
affine_inequivalent = True
affine_plus_complement_inequivalent = True
direct_complement_image = False
triple_G_nonaligned = True
triple_disagreement_count = 240
primitive_period_A = 64
primitive_period_B = 64
ordered_failure_codes = []
```

---

## 5. Frozen pair 1 — candidate 479

Pair-verifier certificate SHA-256:

```text
3b3475fc9bd2264fd17035f62ddbbc03d584a1fa94f5f28db712941f6e683408
```

Raw support A:

```text
{0,1,2,4,5,6,7,9,12,13,14,16}
```

Raw support B:

```text
{0,1,3,4,5,8,10,11,12,60,62,63}
```

Member weight:

```text
12
```

Complete periodic autocorrelation, identical for A and B:

```text
[12,7,7,6,6,6,4,6,4,4,3,3,4,2,2,1,
 1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
 1,1,2,2,4,3,3,4,4,6,4,6,6,6,7,7]
```

Directed one-step table, identical for A and B:

```text
c00 = 47
c01 = 5
c10 = 5
c11 = 7
```

Absolute transition multiset, identical for A and B:

```text
0 -> 54
1 -> 10
```

Exact verifier results:

```text
pair_valid = True
autocorrelation_equal = True
one_step_table_equal = True
transition_multiset_equal = True
affine_inequivalent = True
affine_plus_complement_inequivalent = True
direct_complement_image = False
triple_G_nonaligned = True
triple_disagreement_count = 276
primitive_period_A = 64
primitive_period_B = 64
ordered_failure_codes = []
```

---

## 6. Frozen pair 2 — candidate 480

Pair-verifier certificate SHA-256:

```text
d4bbb7d8d8958cca261728721115de21efa154c50930bf787e4153fcb28ddfd9
```

Raw support A:

```text
{0,1,2,4,5,6,7,9,13,14,15,17}
```

Raw support B:

```text
{0,1,3,4,5,9,11,12,13,60,62,63}
```

Member weight:

```text
12
```

Complete periodic autocorrelation, identical for A and B:

```text
[12,7,7,5,6,5,4,4,5,4,3,3,3,4,2,2,
 1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,
 1,2,2,4,3,3,3,4,5,4,4,5,6,5,7,7]
```

Directed one-step table, identical for A and B:

```text
c00 = 47
c01 = 5
c10 = 5
c11 = 7
```

Absolute transition multiset, identical for A and B:

```text
0 -> 54
1 -> 10
```

Exact verifier results:

```text
pair_valid = True
autocorrelation_equal = True
one_step_table_equal = True
transition_multiset_equal = True
affine_inequivalent = True
affine_plus_complement_inequivalent = True
direct_complement_image = False
triple_G_nonaligned = True
triple_disagreement_count = 336
primitive_period_A = 64
primitive_period_B = 64
ordered_failure_codes = []
```

---

## 7. Frozen family certificate

Family-verifier certificate:

```text
family_valid = True
members_non_reused = True
mutual_G_inequivalent = True
distinct_autocorrelation_classes = True
ordered_failure_codes = []
```

Bound pair-certificate hashes, in frozen family order:

```text
0:
51e72030237da850757979588b4c4107de69a6098ce7c9a3559243b5545edf2b

1:
3b3475fc9bd2264fd17035f62ddbbc03d584a1fa94f5f28db712941f6e683408

2:
d4bbb7d8d8958cca261728721115de21efa154c50930bf787e4153fcb28ddfd9
```

The family certificate establishes, under the committed verifier:

```text
all three pairs individually valid
no member reused
all six members mutually G-inequivalent
all three pairs in distinct complete-autocorrelation classes
```

It does not establish:

```text
statistical independence
unique construction lineage
optimality
exhaustiveness
descriptor response
temporal-order detection
vision or perception
```

---

## 8. Why this family is a valid downstream falsifier family

Within each pair:

```text
complete periodic autocorrelation is identical
directed one-step tables are identical
absolute transition multisets are identical
member weights are identical
both raw members have primitive period 64
the pair is not related by the forbidden affine/complement equivalences
the complete labeled triple arrays are G-nonaligned
```

Across the family:

```text
all six members are mutually G-inequivalent
no raw member is reused
the three complete-autocorrelation classes are distinct
```

Therefore, a downstream A/B response cannot be attributed merely to unequal complete periodic autocorrelation of the raw circular binary members.

It still may depend on other differences, including:

```text
higher-order structure
boundary conventions
representation geometry
normalization
generic cross-member disruption
descriptor-specific behavior
```

No attribution is authorized before the frozen evaluation is executed and interpreted under its exact contract.

---

## 9. Binding to the existing F3 response contract

For each frozen pair, downstream evaluation must use the exact existing F3 contract without modification.

### 9.1 Input object

Each raw support is converted directly into:

```text
a binary field D
shape = (64, 1)
dtype = float
values = {0.0, 1.0}
encoding = DIRECT_SCALAR_BINARY_0_1
```

No centering, complement channel, extra feature, spatial embedding, 3D projection, padding, or learned transform is permitted.

### 9.2 Member and pair order

```text
pair order = [478, 479, 480]
within each pair = frozen raw A followed by frozen raw B
```

The symmetric primary response is role-swap invariant, but the raw A/B naming remains frozen for provenance, directional diagnostics if any, and exact artifact identity.

### 9.3 Rotation and start policy

```text
rotate(x, s)[t] = x[(t + s) mod 64]
all matched starts s = 0..63
same offset applied to both members
O1 = all 64 starts
A3 = arithmetic mean across matched starts
```

No reduced start subset is permitted.

### 9.4 Descriptor variants

Exactly:

```text
psi_trs:
psi_trs_features(field, kappa=0.5)

psi_trs_k0:
psi_trs_features(field, kappa=0.0)
```

No descriptor source change, parameter change, feature deletion, feature weighting, normalization change, or response-driven adjustment is permitted.

### 9.5 Response object

Exactly the existing symmetric joint-mean-norm normalized L2 response:

```text
numerator = ||f_a - f_b||_2
joint_scale = (||f_a||_2 + ||f_b||_2) / 2
effective_joint_scale = max(joint_scale, 1e-12)
distance = numerator / effective_joint_scale
```

Raw unrounded finite floats must be retained and canonically serialized.

### 9.6 Complete self-shift references

For each pair member, each variant, each nonidentity shift `r = 1..63`, and each matched start `s = 0..63`, evaluate the complete self-shift response.

Identity shift `r = 0` remains an exact self-pair validity control and must equal `0.0`.

No quantile, rank, median, trimmed mean, or subset may replace the predeclared complete self-shift maximum gates.

---

## 10. Frozen pair gates

For each pair:

```text
full_dual_orbit_extreme =
    full_cross_mean > max_r(full_self_A_mean[r])
    AND
    full_cross_mean > max_r(full_self_B_mean[r])

k0_not_extreme_against_either_member =
    k0_cross_mean <= max_r(k0_self_A_mean[r])
    AND
    k0_cross_mean <= max_r(k0_self_B_mean[r])

recursive_positive_all_starts =
    for every matched start s:
    full_cross_s - k0_cross_s > 0
```

Primary pair gate:

```text
PAIR_STRONG_PASS =
    valid_run
    AND full_dual_orbit_extreme
    AND k0_not_extreme_against_either_member
    AND recursive_positive_all_starts
```

Comparison tolerance:

```text
0.0
```

All strict gates use exact finite raw-float comparison.

No result-driven tolerance, rescue statistic, threshold, or alternate comparison rule may be introduced.

---

## 11. Frozen family verdicts

```text
all 3 pairs pass
    -> STRONG_FAMILY_FALSIFIER_SUCCESS

1 or 2 pairs pass
    -> VALID_MIXED_FAMILY_RESULT

0 pairs pass, with every pair valid
    -> STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY

any pair or family validity failure
    -> INVALID_FAMILY_EVALUATION
```

These verdict labels are bound before evaluation.

A witness may not be replaced after any pass, failure, invalidity, or unexpected response.

---

## 12. Required validity binding

A downstream implementation must verify before interpreting any response:

```text
family-manifest hash exact
family-verifier certificate hash exact
all three pair-certificate hashes exact
raw supports exact
raw-support hashes exact when frozen by the evaluator specification
accepted order exact
candidate indices exact
all six members binary, finite, and length 64
all pair and family witness certificates independently reverified
generator identities exact
verifier identities exact
freezer evidence identities exact
evaluator identity exact
descriptor identity and kappa parameters exact
complete 64-start cross coverage
complete 63-shift x 64-start self-orbit coverage
identity self-pair controls exact zero
all response values finite
all normalization denominators valid
canonical serialization successful
same-environment replay byte-identical
canonical replay SHA-256 equal
```

Any validity failure yields:

```text
PAIR_INVALID
INVALID_FAMILY_EVALUATION
```

It must not be counted as a failed scientific gate.

---

## 13. Claim boundary

Permitted after a valid future evaluation:

```text
report exact per-pair response objects
report exact self-shift references
report exact predeclared pair gates
report the exact frozen family verdict
report descriptive numerical margins and diagnostics
```

Not permitted from this family or its future evaluation alone:

```text
true vision
perception
spatial continuity
3D understanding
continuous world modeling
absence of context drift
absence of safety filtering
physics-based emergence
general temporal-order detection
general higher-order detection
recursive-time mechanism proof
scientific superiority
production readiness
```

Even `STRONG_FAMILY_FALSIFIER_SUCCESS` would mean only that all three frozen pairs passed the exact preregistered F3 contract under the exact evaluator, descriptor, environment, self-shift references, and comparison rules.

---

## 14. Implementation and execution state

```text
FROZEN_K3_FAMILY_EVIDENCE_RECORDED = True
FROZEN_K3_FAMILY_BOUND_TO_EXISTING_F3_CONTRACT = True

EVALUATOR_IMPLEMENTATION_SPECIFICATION_AUTHORIZED = not by this document
EVALUATOR_IMPLEMENTATION_AUTHORIZED = False
F3_EVALUATION_AUTHORIZED = False
PsiTRS_EVALUATION_AUTHORIZED = False

FREEZER_RERUN_AUTHORIZED = False
CANDIDATE_GENERATOR_RERUN_AUTHORIZED = False
WITNESS_REPLACEMENT_AUTHORIZED = False
THRESHOLD_TUNING_AUTHORIZED = False

SCIENTIFIC_INFERENCE_AUTHORIZED = False
PRODUCTION_INTEGRATION_AUTHORIZED = False
KERNEL_MODIFICATION_AUTHORIZED = False
LIVE_CAPTURE_AUTHORIZED = False
```

The production TORMENT memory kernel remains immutable.

Brainvision remains:

```text
offline
quarantined
non-runtime
non-production
descriptive-only
```

`FORMAL_HOLD` and `Mode_0` remain active.

---

## 15. Next justified direction

```text
A. SPECIFY THE FROZEN-FAMILY F3 EVALUATOR IMPLEMENTATION
```

The next document should freeze:

```text
evaluator module and runner paths
input loading from canonical freezer evidence
exact raw-support extraction and hash binding
pair and family result schemas
complete cross and self-orbit storage
validity and failure-code namespace
descriptor and source identity binding
canonical serialization
same-environment replay procedure
publication paths
runtime/resource diagnostics
pre-contact refusal and execution-consumption semantics
```

That later implementation specification must not authorize execution.

A separate docs-only execution authorization must be required after:

```text
implementation
tests
adversarial review
Windows authoritative validation
source-identity freeze
```

---

## 16. Final disposition

```text
A. EXACT FROZEN K=3 FAMILY EVIDENCE RECORDED
A. EXISTING F3 EVALUATION CONTRACT BOUND TO THE FROZEN FAMILY
```

The immutable downstream family is:

```text
candidate 478
candidate 479
candidate 480
```

with the exact raw supports and certificate identities recorded above.

No implementation or evaluation occurred while preparing this document.

No PsiTRS, descriptor, SAG, operational harness, candidate generator, freezer, production service, or production-kernel contact occurred while preparing this document.

*End — TORMENT Brainvision Algebraic N=64 PRIMARY_V0_1 Frozen K=3 Family Evidence and F3 Evaluation Binding v0.1.*

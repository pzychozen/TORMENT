# TORMENT Brainvision Algebraic N=64 PRIMARY_V0_1 Frozen-Family F3 Read-Only Asymmetry Audit Specification v0.1

## 0. Decision

```text
A. SPECIFY READ-ONLY RETAINED-EVIDENCE F3 ASYMMETRY AUDIT
```

This document specifies, but does not implement or execute, a descriptive post-result audit over the retained canonical F3 evaluation evidence.

Audit classification:

```text
post-result
descriptive
read-only with respect to retained evidence
non-gating
non-rescue
offline
quarantined
non-production
non-scientific-claim
```

The audit must not amend or reconsider the authoritative F3 verdict:

```text
STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY
```

The audit must not create a new success criterion for the completed run. It localizes and describes the already-recorded failure. It does not reevaluate it.

This document does not authorize implementation, execution, descriptor recomputation, PsiTRS contact, or any modification of retained evidence.

---

## 1. Governing findings

Bound findings record:

```text
docs/TORMENT_BRAINVISION_ALGEBRAIC_N64_PRIMARY_V0_1_F3_EVALUATION_FINDINGS_v0.1.md
```

Findings commit:

```text
f0c5fdbc6f75e3749323de9e2b13c77b3710df82
```

Closed authoritative result recorded by the findings:

```text
valid_run = True
replay_byte_identical = True
strong_pass_count = 0
failure_code = absent
F3_EXECUTION_AUTHORIZED = consumed
F3_RERUN_AUTHORIZED = False
```

All three frozen pairs produced:

```text
full_dual_orbit_extreme = False
k0_not_extreme = True
recursive_positive_all_starts = True
```

For all three pairs:

```text
full_margin_vs_A < 0
full_margin_vs_B > 0
```

Therefore member A was the blocking complete self-orbit reference for every frozen pair. This audit describes the structure of that blocking. It does not question the verdict it produced.

---

## 2. Exact retained input

Read only:

```text
research/brainvision/results/algebraic_n64_primary_v0_1_f3_evaluation_v0_1/
  algebraic_n64_primary_v0_1_f3_evaluation_result.json
```

Expected size:

```text
10,784,993 bytes
```

Expected whole-file SHA-256:

```text
51e7cd8087050428c2559262764044624fcb84e19576b5f682bae3ca5b59fd7b
```

The future analyzer must refuse before analysis if any of the following differs:

```text
path
size
whole-file hash
envelope
execution identity
replay status
validity
pair order
family verdict
```

Expected top-level key set exactly:

```text
family_evaluation_result
family_evaluation_result_sha256
```

Expected payload:

```text
schema_name =
torment_brainvision_algebraic_n64_f3_family_evaluation

schema_version =
0.1
```

The analyzer must recompute the payload identity using:

```python
json.dumps(
    payload,
    ensure_ascii=True,
    sort_keys=True,
    separators=(",", ":"),
    allow_nan=False,
).encode("utf-8")
```

with no trailing newline, followed by SHA-256. The recomputed value must equal the retained `family_evaluation_result_sha256`.

Also bind:

```text
execution_commit_identity =
c4f489c439d4190611e8e0c5b3034ead3353c26d

family_verdict =
STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY

pair order =
[478, 479, 480]

valid_run =
True

replay byte_identical =
True
```

Any mismatch must refuse before audit calculations and produce no derived output directory.

The input must be opened read-only.

No in-place write, temporary rewrite, canonical rewrite, formatting rewrite, normalization, or replacement copy of the retained input is permitted.

---

## 3. Future implementation boundary

The later analyzer must be a new standalone offline module under:

```text
research/brainvision/
```

Recommended path:

```text
research/brainvision/analyze_algebraic_n64_f3_asymmetry_v0_1.py
```

It must use only retained JSON values.

It must not import:

```text
research.brainvision.psi_trs
research.brainvision.algebraic_n64_f3_evaluator_v0_1
research.brainvision.algebraic_n64_f3_frozen_identity_v0_1
torment_service
```

It must not call:

```text
psi_trs_features
build_production_feature_cache
evaluate_from_feature_cache
```

Prefer Python standard-library parsing and arithmetic. No NumPy dependency is required unless a later reviewed implementation specification proves it necessary.

The analyzer may produce new derived audit artifacts, but those artifacts must be separate from the retained F3 directory and may never overwrite retained evidence.

Recommended derived-output directory:

```text
research/brainvision/results/
  algebraic_n64_primary_v0_1_f3_asymmetry_audit_v0_1/
```

This specification does not authorize creating that directory. It is created only under a later reviewed implementation-and-execution authorization.

---

## 4. Frozen audit scope

The audit must examine only retained response-level objects.

Included:

```text
member self_orbits_by_variant
nonidentity shift aggregates
nonidentity per-start responses
pair cross_by_variant aggregates
pair cross per-start responses
recorded pair gates and margins
recorded recursive companion summaries
```

Excluded from v0.1:

```text
individual 11-dimensional feature-coordinate attribution
new descriptor calculations
new rotations
new witnesses
new controls
new thresholds
new pair gates
new family verdicts
statistical significance tests
model fitting
clustering
optimization
search over alternative criteria
```

---

## 5. Shift-class convention

The retained self orbit contains relative shifts `1..63`.

Because the response is symmetric and the starts cover the full circular orbit, the audit compares inverse-shift classes:

```text
{d, 64-d}
```

using canonical representative:

```text
q = min(d, 64-d)
```

This yields:

```text
q = 1..32
```

where `q=32` is self-inverse.

The future analyzer must first verify the expected inverse-shift symmetry for each member and variant.

The exact inverse-shift validation procedure is:

```text
For each member and variant, and for each q=1..31:

raw shift 1 = q
raw shift 2 = 64-q

Extract the 64 retained per-start distance values for both raw shifts.
Sort both numeric lists ascending.
Require exact elementwise equality of the sorted lists.

For q=32, treat raw shift 32 as the single self-inverse class.

Also compare the retained aggregate fields:

mean
median
minimum
maximum
population_standard_deviation

Aggregate differences must be recorded diagnostically, but the exact sorted
per-start distance-multiset equality is the governing inverse-shift validation.
```

On validation failure:

```text
If either raw shift is missing, has other than 64 retained distances, contains
a nonfinite value, or the sorted distance multisets differ:

inverse_shift_validation = False
audit disposition = D
do not calculate class-collapsed rank, breadth, or A/B class metrics
retain all available raw-shift diagnostics
```

When validation succeeds:

```text
use raw shift q as the canonical class representative
do not average q with 64-q
retain both raw-shift objects in diagnostics
```

---

## 6. Audit Question 1 — isolated maximum versus broad elevation

For each of the six members and each variant:

```text
psi_trs
psi_trs_k0
```

record over the 32 inverse-shift classes:

```text
maximum shift-class mean
argmax inverse-shift classes
minimum shift-class mean
median of shift-class means
mean of shift-class means
population standard deviation of shift-class means
top-2 shift-class means
top-5 shift-class means
maximum-minus-second gap
maximum-minus-median gap
maximum-to-median ratio when the median is nonzero
```

Also record the number and fraction of inverse-shift classes lying within:

```text
99% of the maximum
95% of the maximum
90% of the maximum
```

These are descriptive concentration diagnostics only. They are not new gates.

---

## 7. Audit Question 2 — exact blocking classes

For each frozen pair under full `psi_trs`, record separately for member A and member B:

```text
full cross mean
self-orbit maximum
margin = cross mean - self maximum
argmax inverse-shift classes
all inverse-shift classes whose mean is greater than the full cross mean
count and fraction of inverse-shift classes greater than the full cross mean
rank of the cross mean relative to the 32 self-shift class means
```

Do not reinterpret equality. Preserve the frozen comparison tolerance:

```text
0.0
```

The purpose is descriptive localization of the already-recorded failure, not reevaluation of the pair verdict.

---

## 8. Audit Question 3 — A/B shiftwise asymmetry

For each pair and variant, compare member A and member B at each matching inverse-shift class.

Record:

```text
A mean - B mean for every class
count of classes where A > B
count of classes where A = B
count of classes where A < B
mean paired difference
median paired difference
minimum paired difference
maximum paired difference
classes with the five largest A-minus-B differences
classes with the five largest B-minus-A differences
```

Also record whether A's maximum exceeds B's maximum and by how much.

This is descriptive orbit asymmetry only. Do not infer a causal role for raw role A or B.

---

## 9. Audit Question 4 — per-start concentration at blocking shifts

For each pair's full-variant member-A blocking argmax class, use the retained per-start distances for the corresponding raw shift or shifts.

Record:

```text
count = 64
mean
median
minimum
maximum
population standard deviation
mean-minus-median
maximum-to-mean ratio when mean is nonzero
top-8-distance contribution share
top-16-distance contribution share
argmax starts
argmin starts
```

Compare those retained member-A self-shift per-start distances with the retained full cross per-start distances at the same starts.

Record the aligned differences:

```text
self_blocking_distance[start] - cross_distance[start]
```

and summarize:

```text
count positive
count zero
count negative
mean
median
minimum
maximum
population standard deviation
largest positive starts
largest negative starts
```

When an inverse class contains two raw shifts, report each raw shift separately before any class-level summary.

This determines whether the blocking maximum is broad across starts or driven by a small start subset. It does not create a new pass condition.

---

## 10. Audit Question 5 — k0 structural comparison

Repeat Questions 1–3 for `psi_trs_k0`.

Record particularly:

```text
k0 cross mean
k0 self A maximum
k0 self B maximum
k0 margins
A/B shiftwise asymmetry
breadth of each k0 self-orbit maximum
```

The audit must preserve:

```text
k0_not_extreme = True
```

for all three pairs.

The k0 audit is a structural comparator only.

---

## 11. Audit Question 6 — recursive companion context

Use only the already-retained full-minus-k0 cross differences.

Record for each pair:

```text
minimum
maximum
mean
median
population standard deviation
argmin starts
argmax starts
count positive
count zero
count negative
```

Confirm whether:

```text
count positive = 64
count zero = 0
count negative = 0
```

Do not recompute features. Do not compare against an invented threshold.

---

## 12. Deterministic rank, threshold, top-k, and tie semantics

All audit metrics use the following deterministic definitions:

```text
cross insertion rank =
1 + count(inverse_shift_class_mean > cross_mean)

The rank range is 1..33.
Values equal to the cross mean do not count as greater.

All ranked class lists sort by:
1. value descending
2. canonical q ascending for exact ties

Counts within 99%, 95%, and 90% of maximum use:
class_mean >= fraction * maximum

top-k-distance contribution share =
sum of the k largest retained distances / sum of all 64 retained distances

For top-k distance sorting:
1. distance descending
2. start ascending for ties

If the total distance is zero:
contribution_share = null
zero_total = True

largest positive aligned-difference starts:
exactly 8 entries, ordered by difference descending then start ascending

largest negative aligned-difference starts:
exactly 8 entries, ordered by difference ascending then start ascending

If fewer than 8 values satisfy the requested sign, return all matching values
and record the returned count.
```

The fields `top-2 shift-class means` and `top-5 shift-class means` are ordered lists of `{q, mean}` objects. They are not averages of the top two or top five values.

---

## 13. Deterministic output requirements

The later analyzer must produce deterministic derived output with:

```text
schema name
schema version
input path as repository-relative path
input whole-file SHA-256
execution commit identity
source findings commit identity
audit configuration
audit configuration SHA-256
pair order [478,479,480]
member order
variant order
complete audit tables
validation record
non-claim boundary
```

Recommended files:

```text
algebraic_n64_primary_v0_1_f3_asymmetry_audit_result.json

algebraic_n64_primary_v0_1_f3_asymmetry_audit_summary.txt
```

The later implementation must use canonical deterministic JSON.

No timestamps, durations, hostname, absolute paths, randomness, environment-dependent ordering, or scientific interpretation may enter the machine result.

---

## 14. Audit dispositions

The eventual findings may choose exactly one descriptive disposition:

```text
A. BLOCKING SELF-ORBIT MAXIMUM IS NARROWLY CONCENTRATED

B. BLOCKING SELF-ORBIT ELEVATION IS BROAD

C. MIXED BLOCKING STRUCTURE ACROSS THE FROZEN FAMILY

D. RETAINED EVIDENCE IS INSUFFICIENT OR INTERNALLY INCONSISTENT
```

Disposition selection is deterministic:

```text
For each frozen pair define:

blocking_class_count =
the number of member-A full-variant inverse-shift class means
strictly greater than that pair's retained full cross mean.

Pair classification:

narrow:
blocking_class_count <= 2

intermediate:
blocking_class_count is 3 through 7 inclusive

broad:
blocking_class_count >= 8

Family disposition:

A. BLOCKING SELF-ORBIT MAXIMUM IS NARROWLY CONCENTRATED
only when all three pairs are narrow.

B. BLOCKING SELF-ORBIT ELEVATION IS BROAD
only when all three pairs are broad.

C. MIXED BLOCKING STRUCTURE ACROSS THE FROZEN FAMILY
for every other validation-clean combination, including any intermediate pair.

D. RETAINED EVIDENCE IS INSUFFICIENT OR INTERNALLY INCONSISTENT
whenever any required input, envelope, replay, inverse-shift, coverage,
or audit validation fails.
```

The threshold values `2` and `8` define descriptive audit vocabulary only. They are not F3 gates, scientific thresholds, or rescue criteria.

These are descriptive audit dispositions only. They must not replace or weaken:

```text
STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY
```

The audit may recommend:

```text
close the branch
prepare a genuinely new preregistered hypothesis
perform a separate role-symmetry study
perform a separate witness-construction study
```

It must not recommend rerunning or rescuing the completed F3 evaluation.

---

## 15. Project boundaries

Preserve:

```text
offline
quarantined
non-runtime
non-production
non-live
non-scientific-claim lane
FORMAL_HOLD active
Mode_0 active
```

The production kernel remains immutable:

```text
torment_service/kernel/
torment_service/memory_kernel.py
torment_service/fabric.py
```

The audit contacts no descriptor, no feature cache, no live surface, and no production module. It reads exactly one retained JSON file and writes only separate derived artifacts under a later authorization.

---

## 16. Authority state

```text
F3_EVALUATION_COMPLETE = True
F3_EVALUATION_VALID = True
F3_RERUN_AUTHORIZED = False

READ_ONLY_ASYMMETRY_AUDIT_SPECIFIED = True
READ_ONLY_ASYMMETRY_AUDIT_IMPLEMENTATION_AUTHORIZED = False
READ_ONLY_ASYMMETRY_AUDIT_EXECUTION_AUTHORIZED = False

PSITRS_CONTACT_AUTHORIZED = False
DESCRIPTOR_RECOMPUTATION_AUTHORIZED = False
RETAINED_EVIDENCE_MODIFICATION_AUTHORIZED = False
SCIENTIFIC_INFERENCE_AUTHORIZED = False
PRODUCTION_INTEGRATION_AUTHORIZED = False
KERNEL_MODIFICATION_AUTHORIZED = False
```

`FORMAL_HOLD` and `Mode_0` remain active.

---

## 17. Disposition

```text
A. SPECIFY READ-ONLY RETAINED-EVIDENCE F3 ASYMMETRY AUDIT
```

The next permitted step after this specification is accepted, adversarially reviewed, committed, and pushed is a separate docs-only implementation authorization.

The required sequence is:

1. accept and commit this specification;
2. perform focused adversarial review of the specification;
3. create and commit a separate docs-only implementation authorization;
4. implement the standalone analyzer;
5. run non-contact tests over synthetic fixtures and read-only retained-evidence fixtures;
6. perform focused adversarial implementation review;
7. freeze the analyzer and test source identities;
8. create and commit a separate docs-only execution authorization;
9. execute the analyzer once against the retained canonical JSON;
10. record the resulting descriptive findings.

This specification authorizes none of steps 3 through 10.

Recommended commit subject after review:

```text
docs(research): specify frozen N64 F3 asymmetry audit
```

No analyzer was implemented while preparing this specification. No audit calculation was executed. No descriptor or feature cache was recomputed. No PsiTRS contact occurred. The environment gate remained unset. The retained canonical F3 artifacts were not modified. The production TORMENT kernel remained untouched.

*End — TORMENT Brainvision Algebraic N=64 PRIMARY_V0_1 Frozen-Family F3 Read-Only Asymmetry Audit Specification v0.1. Docs-only. Specifies a descriptive, non-gating, read-only audit of retained F3 evidence. It does not implement or execute the analyzer, does not amend the authoritative negative verdict, and authorizes no rerun, rescue, descriptor recomputation, or retained-evidence modification.*

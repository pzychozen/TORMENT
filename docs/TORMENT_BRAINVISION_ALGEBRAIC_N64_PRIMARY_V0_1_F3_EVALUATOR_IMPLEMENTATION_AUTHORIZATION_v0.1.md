# TORMENT Brainvision Algebraic N=64 PRIMARY_V0_1 Frozen-Family F3 Evaluator Implementation Authorization v0.1

## 0. Authorization decision

```text
A. AUTHORIZE THE FROZEN-FAMILY F3 EVALUATOR IMPLEMENTATION
```

This document authorizes implementation and bounded non-contact testing of the already-specified frozen-family F3 evaluator.

This authorization becomes effective only after this document:

```text
passes focused adversarial review
is committed
is pushed
is the synchronized main-branch HEAD
```

This document does not authorize the frozen-family F3 evaluation.

---

## 1. Governing baseline

Authoritative implementation specification:

```text
docs/TORMENT_BRAINVISION_ALGEBRAIC_N64_PRIMARY_V0_1_F3_EVALUATOR_IMPLEMENTATION_SPECIFICATION_v0.1.md
```

Specification commit:

```text
f3ca182e44677d7daf900dce2a3f77486242cc61
```

Frozen-family binding:

```text
docs/TORMENT_BRAINVISION_ALGEBRAIC_N64_PRIMARY_V0_1_FROZEN_K3_FAMILY_EVIDENCE_AND_F3_EVALUATION_BINDING_v0.1.md
```

Binding commit:

```text
0397c8ee203dd31937064938cac963d1951ca5f0
```

The implementation must conform exactly to the committed implementation specification.

This authorization does not amend:

```text
the frozen family
the F3 mathematics
the pair order
the response formula
the all-start policy
the complete self-shift reference policy
the zero-tolerance comparisons
the pair verdicts
the family verdicts
the one-run later execution model
```

---

## 2. Exact authorized production files

Creation and modification are authorized only for:

```text
research/brainvision/algebraic_n64_f3_frozen_identity_v0_1.py

research/brainvision/algebraic_n64_f3_evaluator_v0_1.py

research/brainvision/run_algebraic_n64_f3_evaluation_v0_1.py
```

No other production source file may be created or modified under this authorization.

---

## 3. Exact authorized test files

Creation and modification are authorized only for:

```text
tests/research/test_brainvision_algebraic_n64_f3_frozen_identity_v0_1.py

tests/research/test_brainvision_algebraic_n64_f3_evaluator_v0_1.py

tests/research/test_brainvision_run_algebraic_n64_f3_evaluation_v0_1.py
```

No other test file may be created or modified under this authorization.

---

## 4. Authorized implementation scope

The implementation may provide only the behavior frozen by the specification, including:

```text
constants-only frozen identity binding

canonical freeze-result preflight

whole-file and canonical payload identity validation

exact family-manifest and certificate identity validation

exact six-support and candidate-order validation

integer-exact pair and family reverification before descriptor contact

direct scalar binary (64,1) field construction

local rotation implementation

local symmetric joint-mean-norm normalized L2 response

pure feature-cache evaluation

complete cross-pair response assembly

identity self-pair controls

complete nonidentity self-shift orbit assembly

recursive-companion difference assembly

exact F3 pair gates

exact frozen family verdict mapping

canonical finite-only result assembly

two-pass replay comparison

source and environment identity capture

closed-by-default production authorization gate

pre-contact refusal

exclusive staging and atomic two-file publication

stable failure-code reporting
```

No metric, threshold, response object, start policy, family rule, or verdict may be invented or altered.

---

## 5. Frozen family identity

Implementation must bind exactly:

```text
N = 64
K = 3
candidate order = [478, 479, 480]
six members total
```

The exact raw supports and hashes are those recorded in the committed binding and specification.

No implementation may:

```text
replace a member
replace a pair
reorder pairs based on any response
transform raw supports into canonical representatives
translate, reflect, rotate, complement, pad, tile, resample, embed, or otherwise substitute a support
consult descriptor behavior when selecting or validating family membership
```

Read-only extraction and validation of the canonical freezer result are authorized.

Mutation, deletion, renaming, rewriting, or regeneration of freezer evidence are not authorized.

---

## 6. Descriptor-contact boundary

The production descriptor entry point is:

```python
psi_trs.psi_trs_features(...)
```

Implementation may import `psi_trs` as required by the specification.

Import must perform no evaluation.

During implementation and testing under this authorization:

```text
no production call to psi_trs.psi_trs_features is authorized through the new F3 evaluator

no call on any of the six frozen family members is authorized

no call on any rotation of a frozen family member is authorized

no F3 production feature cache may be constructed

no 768-call pass may begin

no 1536-call replay may begin
```

The exact environment gate:

```text
ALGEBRAIC_N64_F3_EVALUATION_AUTHORIZED
```

must remain absent or non-authorizing.

It must not be set to:

```text
1
```

during implementation or testing.

The first later production descriptor call on a frozen family member requires a separate docs-only execution authorization.

---

## 7. Authorized test behavior

The six authorized files may be tested using:

```text
synthetic binary arrays
synthetic finite feature vectors
synthetic complete feature caches
temporary directories
temporary JSON fixtures
monkeypatched descriptor entry points
monkeypatched evaluator pass results
monkeypatched Git and environment captures
malformed and mismatched evidence copies in temporary directories
```

Tests may read the canonical freezer result read-only to validate:

```text
schema navigation
hash bindings
candidate order
certificate envelopes
raw supports
integer-exact reverification
pre-descriptor refusal behavior
```

Tests must not use that evidence to contact PsiTRS.

The descriptor entry point must be monkeypatched to raise in tests that could otherwise reach it.

Authorized pure-function parity tests may import the old N64 runner and compare only:

```text
rotate
symmetric_response
```

using synthetic arrays and finite synthetic feature vectors.

Parity tests must not call:

```text
features
psi_trs.psi_trs_features
main
the old N64 evaluation path
```

---

## 8. Authorized test commands

After implementation, the following focused test command is authorized:

```bat
python -m pytest ^
  tests\research\test_brainvision_algebraic_n64_f3_frozen_identity_v0_1.py ^
  tests\research\test_brainvision_algebraic_n64_f3_evaluator_v0_1.py ^
  tests\research\test_brainvision_run_algebraic_n64_f3_evaluation_v0_1.py ^
  -q
```

After focused tests pass, the existing Brainvision research test suite may be run:

```bat
python -m pytest tests\research -q
```

The wider run does not authorize:

```text
setting ALGEBRAIC_N64_F3_EVALUATION_AUTHORIZED=1
running the new production F3 runner
publishing a canonical F3 result
rerunning the freezer
rerunning the candidate generator
```

Existing unrelated gated tests retain their established behavior; this document grants no new experimental execution authority beyond implementation verification.

---

## 9. Required test protections

Tests must prove:

```text
module import performs no descriptor call

module import creates no files

the production gate defaults closed

the runner rejects command-line arguments

the runner refuses before descriptor contact when unauthorized

no authorized ordinary test contacts PsiTRS through the F3 evaluator

the frozen identity module contains constants only

all six supports and all frozen hashes are exact

rotation and symmetric-response parity hold

feature-cache mathematics uses no descriptor calls

cross coverage is exactly 384 responses per pass

identity coverage is exactly 768 controls per pass

nonidentity self-shift coverage is exactly 48,384 responses per pass

descriptor-call accounting is 768 per complete pass and 1536 per complete replay

pair gates are exact

family verdict mapping is exact

zero-tolerance equality behavior is exact

invalidity remains distinct from a failed F3 hypothesis

replay mismatch yields INVALID_FAMILY_EVALUATION

publication never overwrites, merges, or resumes

evidence-bearing staging is retained after post-contact failure

production modules do not import torment_service or a generator
```

Call-count tests must use instrumentation or synthetic cache builders.

They must not perform the counted production descriptor calls.

---

## 10. Authorized read-only source contact

The implementation and tests may read or import, without modification:

```text
research/brainvision/psi_trs.py

research/brainvision/run_n64_falsifier_v0_1.py
  pure-function parity reference only

research/brainvision/witness_family_verifier_v0_1.py

research/brainvision/witness_canonical_json_v0_1.py

research/brainvision/results/algebraic_n64_primary_v0_1_freeze_v0_1/
  algebraic_n64_primary_v0_1_freeze_result.json
```

They may also read committed governing documentation.

The old N64 runner must not become the new evaluator’s production engine.

The freezer and generator must not be imported or executed.

---

## 11. Immutable and prohibited files

The following must not be modified:

```text
research/brainvision/psi_trs.py
research/brainvision/run_n64_falsifier_v0_1.py
research/brainvision/witness_family_verifier_v0_1.py
research/brainvision/witness_family_freeze_v0_1.py
research/brainvision/witness_canonical_json_v0_1.py

all candidate-generator modules

all existing freezer evidence
all existing N64 evaluation evidence
all prerecorded operational-harness code and evidence

torment_service/kernel/
torment_service/memory_kernel.py
torment_service/fabric.py
```

No file under `torment_service/` may be contacted for implementation reuse or modified.

---

## 12. Output prohibition during implementation

The canonical production output directory must remain absent:

```text
research/brainvision/results/algebraic_n64_primary_v0_1_f3_evaluation_v0_1/
```

The production staging directory must remain absent:

```text
research/brainvision/results/.algebraic_n64_primary_v0_1_f3_evaluation_v0_1.staging/
```

Tests may exercise publication logic only inside temporary directories.

No canonical F3 result or summary may be generated under repository `research/brainvision/results/`.

No implementation test artifact may be committed.

---

## 13. Implementation validity is not evaluation validity

Passing implementation tests may establish only:

```text
the code conforms to the frozen implementation specification
the pure response mathematics is wired correctly
the family evidence is validated before contact
the production gate defaults closed
the cache, orbit, gate, replay, and publication machinery behave as specified
```

Passing implementation tests does not establish:

```text
that the real frozen-family evaluation is numerically valid
that replay will be byte-identical under real descriptor contact
that any pair will pass
that the family will pass
higher-order detection
temporal-order detection
vision
perception
recursive-time mechanism validation
scientific significance
production readiness
```

---

## 14. Required implementation workflow

After this authorization is reviewed, committed, and pushed:

```text
1. create only the three authorized production modules
2. create only the three authorized test modules
3. run the focused synthetic/non-contact tests
4. run the existing Brainvision research test suite
5. inspect git status and the six authorized files directly
6. perform one focused adversarial implementation review
7. correct only genuine implementation blockers
8. rerun the focused and wider tests
9. commit and push only the six implementation/test files
10. record exact Git blob and raw-byte SHA-256 source identities
11. prepare a separate one-run F3 execution authorization
```

The production F3 runner must not be invoked in this workflow.

---

## 15. Stop conditions

Implementation work must stop and return to review if:

```text
the specification requires changing an immutable source

a real frozen-family descriptor call occurs

the production authorization gate is accidentally set to 1

a test writes to the canonical production output path

canonical freezer evidence is modified

the six-file boundary is insufficient

the exact F3 contract cannot be implemented without inventing a new policy

the old N64 runner would need to become the new production engine

a production-kernel import or modification appears

a test cannot be made non-contact
```

No stop condition authorizes weakening the contract or running the evaluation.

---

## 16. Authority state

Upon committed and synchronized acceptance of this document:

```text
DOCUMENTATION_AUTHORIZED = True

F3_EVALUATOR_IMPLEMENTATION_AUTHORIZED = True
F3_EVALUATOR_AUTHORIZED_FILE_COUNT = 6
F3_EVALUATOR_SYNTHETIC_TEST_EXECUTION_AUTHORIZED = True
F3_EVALUATOR_READ_ONLY_EVIDENCE_VALIDATION_AUTHORIZED = True
F3_EVALUATOR_PURE_PARITY_TESTS_AUTHORIZED = True

F3_PRODUCTION_RUNNER_INVOCATION_AUTHORIZED = False
F3_PRODUCTION_FEATURE_CACHE_AUTHORIZED = False
F3_EVALUATION_AUTHORIZED = False
PsiTRS_FROZEN_FAMILY_CONTACT_AUTHORIZED = False

ALGEBRAIC_N64_F3_EVALUATION_AUTHORIZED_VALUE_1_ALLOWED = False

FREEZER_RERUN_AUTHORIZED = False
GENERATOR_RERUN_AUTHORIZED = False
N64_FALSIFIER_RERUN_AUTHORIZED = False
WITNESS_REPLACEMENT_AUTHORIZED = False
THRESHOLD_TUNING_AUTHORIZED = False

SCIENTIFIC_INFERENCE_AUTHORIZED = False
PRODUCTION_INTEGRATION_AUTHORIZED = False
KERNEL_MODIFICATION_AUTHORIZED = False
LIVE_CAPTURE_AUTHORIZED = False
```

`FORMAL_HOLD` and `Mode_0` remain active.

---

## 17. Final authorization

```text
A. IMPLEMENTATION OF THE SIX SPECIFIED F3 EVALUATOR FILES IS AUTHORIZED

A. SYNTHETIC, MONKEYPATCHED, READ-ONLY-EVIDENCE, AND PURE-PARITY TESTING IS AUTHORIZED

F3 PRODUCTION EXECUTION IS NOT AUTHORIZED

PsiTRS CONTACT WITH THE FROZEN FAMILY IS NOT AUTHORIZED
```

A later execution authorization must bind:

```text
the final implementation commit
all six implementation/test blob identities
all production raw-byte SHA-256 identities
the unchanged descriptor identity
the unchanged verifier and serializer identities
the exact canonical freezer evidence
the exact command
the exact environment gate
the absent final and staging output paths
the one-run authority-consumption boundary
```

*End — TORMENT Brainvision Algebraic N=64 PRIMARY_V0_1 Frozen-Family F3 Evaluator Implementation Authorization v0.1.*

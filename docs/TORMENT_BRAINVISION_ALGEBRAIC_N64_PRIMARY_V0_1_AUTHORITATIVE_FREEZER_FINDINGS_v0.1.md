# TORMENT Brainvision Algebraic N=64 PRIMARY_V0_1 Authoritative Freezer Findings v0.1

## 0. Disposition

```text
A. RECORD POSITIVE AUTHORITATIVE RETAINED-STREAM FREEZE
```

The exact one-run authoritative retained-stream freezer invocation completed successfully under the committed execution authorization.

The committed offline greedy freezer:

```text
selected a K=3 witness family
verified the selected family
completed its internal two-pass replay
published byte-identical replay evidence
published the exact canonical two-file result set
```

This findings record is evidence documentation only.

It does not authorize:

```text
a second freezer invocation
a freezer retry
candidate-generator execution
candidate-stream regeneration or mutation
verifier-cost benchmark rerun
N64 falsifier rerun
PsiTRS evaluation
descriptor or SAG execution
prerecorded operational-harness execution
live capture
production integration
production-kernel modification
scientific inference
a perception, vision, or temporal-order claim
```

---

## 1. Governing execution authorization

Execution authorization document:

```text
docs/TORMENT_BRAINVISION_ALGEBRAIC_N64_PRIMARY_V0_1_FREEZER_EXECUTION_AUTHORIZATION_v0.1.md
```

Execution authorization commit:

```text
6ddd02f9f6fdf74721dc9cd620cbb2a0aa0fecc8
```

Commit subject:

```text
docs(research): authorize algebraic N64 freezer execution
```

The invocation was performed only after confirming:

```text
branch = main
HEAD = origin/main
working tree clean
authorization committed and pushed
all frozen source blob identities exact
retained input size and whole-file hash exact
final output directory absent
staging output directory absent
```

The authorization was consumed when the committed runner entered its sole:

```python
freezer.freeze_with_replay(...)
```

No second invocation is authorized.

---

## 2. Exact operator invocation

Executed exactly once from the authoritative Windows repository root:

```bat
python research\brainvision\run_algebraic_n64_primary_freeze_v0_1.py
```

Captured runner exit code:

```text
FREEZER_EXIT_CODE = 0
```

Runner classification:

```text
classification = POSITIVE
runner_validation_failure = none
published_artifact_set = result+summary
```

No command-line argument or environment override was used.

No outer replay was performed.

---

## 3. Bound repository and source identities

Resolved execution commit:

```text
6ddd02f9f6fdf74721dc9cd620cbb2a0aa0fecc8
```

Repository agreement recorded by the runner:

```text
branch main
origin/main == HEAD
working tree clean
```

Freezer runner path and Git blob identity:

```text
research/brainvision/run_algebraic_n64_primary_freeze_v0_1.py

cad8af6bdd133c9e84e85332c6ca5cefd566b43a
```

Freezer-runner test path and Git blob identity:

```text
tests/research/test_brainvision_run_algebraic_n64_primary_freeze_v0_1.py

cf0e38b3fe7fa3af27e7d4e4bf751313d96c736b
```

Freezer path, Git blob identity, and committed-byte SHA-256:

```text
research/brainvision/witness_family_freeze_v0_1.py

Git blob:
cf4ea57890fbbbdf9593879cf648b84c6c68d9b0

SHA-256:
b0c24472e448f5f8ac7bd0c9f12a6f7ac57aa4980256ee5f463d451d3f32a5a9
```

Verifier path, Git blob identity, and committed-byte SHA-256:

```text
research/brainvision/witness_family_verifier_v0_1.py

Git blob:
db1e1fa606bdbf17fda62cd998aeb2a29d47d59a

SHA-256:
2d17b775b15174963a8f98e2dcfe4f6b9d25db7c99024846ec52ff8bc3ead94d
```

Canonical serializer path, Git blob identity, and committed-byte SHA-256:

```text
research/brainvision/witness_canonical_json_v0_1.py

Git blob:
6eb382b314325033443fc7331cae5050ee6e6ed2

SHA-256:
fad2d09a3a75c884e50f3e8cd2e9cce3f976cd8f3b6c931ae74578891f6c1170
```

No production source was contacted or modified.

---

## 4. Exact retained input

Retained candidate-stream path:

```text
research/brainvision/results/algebraic_n64_primary_v0_1/
  algebraic_n64_primary_v0_1_candidate_stream.json
```

Exact size:

```text
6,421,010 bytes
```

Whole-file SHA-256:

```text
00a816364ddcfc9d06dc8ce1225f58bca013e96a8914ff1eb665004b39ed949b
```

Canonical candidate-stream payload SHA-256:

```text
70763a2ebbf7ea71267553debee2bf79c2ed3b7b0c016d9a903161074e7bf8c5
```

Structural identity:

```text
schema_name = brainvision_descriptor_blind_candidate_stream
schema_version = 0.1
verification_mode = PRIMARY_CANDIDATE_N64
N = 64
candidate_count = 20000
terminal_status = budget_exhausted
candidate_generation_index sequence = 0..19999
```

The retained input was not modified.

---

## 5. Published artifact set

Final publication directory:

```text
research/brainvision/results/algebraic_n64_primary_v0_1_freeze_v0_1/
```

Published files:

```text
algebraic_n64_primary_v0_1_freeze_result.json
algebraic_n64_primary_v0_1_freeze_summary.txt
```

Observed file sizes:

```text
freeze result:
4,919,161 bytes

summary:
2,306 bytes

total:
4,921,467 bytes
```

Final staging state:

```text
research/brainvision/results/.algebraic_n64_primary_v0_1_freeze_v0_1.staging/

absent after completed publication
```

This is consistent with the committed staging-to-final atomic rename contract.

---

## 6. Published artifact identities

Canonical freeze-result payload SHA-256:

```text
35e03a83fee83b7fc13514397e10115b3f6b99f847bf17d20772a0e61376796e
```

Freeze-result whole-file SHA-256:

```text
97af61ea4debf9d66146f3e33f035c17c60965c1d9fed0ebbf3d09ead58cbca5
```

The runner-reported whole-file hash exactly matched the independently captured `certutil` hash.

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

---

## 7. Authoritative result

Published result state:

```text
authoritative_operation = True
family_frozen = True
provisional_k3_valid = True
failure_record = null
```

Accepted candidate indices:

```text
[478, 479, 480]
```

The accepted family size is:

```text
K = 3
```

The exact accepted pair records, accepted pair-certificate envelopes, and family-certificate envelope remain embedded in the canonical freeze-result and family manifest.

This findings document does not replace those canonical objects.

---

## 8. Replay identity

Published replay record:

```text
byte_identical = True

run1_sha256 =
9c848062b9b49ac94225bf39c98c69d4c93c61e82a8a6eb2451fb6806fb28651

run2_sha256 =
9c848062b9b49ac94225bf39c98c69d4c93c61e82a8a6eb2451fb6806fb28651
```

The two internal authoritative freezer passes produced byte-identical canonical freeze payloads.

This is deterministic replay identity under the exact:

```text
execution commit
source identities
retained stream
stream order
greedy selection policy
verification configuration
serialization configuration
```

It is not a claim of universal reproducibility across changed sources, changed inputs, changed platforms, or changed policies.

---

## 9. Manifest binding

The embedded family manifest records:

```text
repository_commit_identity =
6ddd02f9f6fdf74721dc9cd620cbb2a0aa0fecc8

candidate_stream_sha256 =
70763a2ebbf7ea71267553debee2bf79c2ed3b7b0c016d9a903161074e7bf8c5
```

The manifest repository identity exactly matches the synchronized docs-only authorization execution commit.

The manifest retained-stream identity exactly matches the authorized canonical candidate-stream payload identity.

The manifest includes bindings for:

```text
K
N
verification mode
accepted candidate indices
accepted pair records
accepted pair-certificate envelopes
family-certificate envelope
candidate-decision-ledger hash
generator identity
generator configuration
budget identity
freeze configuration
verifier configuration
serializer configuration
freezer source
verifier source
serializer source
resource policy
terminal stream status
```

---

## 10. Result interpretation

Permitted conclusion:

```text
The frozen offline authoritative greedy freezer selected and verified
a replay-identical K=3 witness family from the exact retained PRIMARY_V0_1
candidate stream under the recorded source identities, stream order,
configuration, and selection policy.
```

The selected family is the family encountered by the committed:

```text
authoritative stream-order scan
first-fit policy
greedy acceptance rule
K=3 target
non-backtracking procedure
```

The result does not establish:

```text
that the selected family is unique
that the selected family is optimal
that no earlier alternative acceptance policy could select another family
that all possible families were enumerated
that the complete generator domain was exhaustively searched
that Brainvision works
that PsiTRS distinguishes the family
that temporal order was detected
that visual perception was demonstrated
that a production system is authorized
```

The result is an authoritative offline infrastructure and witness-family result, not a Brainvision scientific result.

---

## 11. Boundary confirmation

```text
freezer_invoked = True
freezer_invocation_count = 1
outer_replay_performed = False
candidate_generator_invoked = False
verifier_cost_benchmark_rerun = False
N64_falsifier_invoked = False
PsiTRS_invoked = False
descriptors_invoked = False
SAG_invoked = False
prerecorded_operational_harness_invoked = False
scientific_interpretation_performed = False
production_integration_performed = False
production_kernel_modified = False
live_capture_performed = False
```

The production TORMENT memory kernel remained untouched.

Brainvision remains:

```text
offline
quarantined under research/brainvision
non-runtime
non-production
descriptive-only
```

`FORMAL_HOLD` and `Mode_0` remain active.

---

## 12. Authority state after execution

```text
DOCUMENTATION_AUTHORIZED = True

PRIMARY_V0_1_CANDIDATE_STREAM_PRODUCED = True
PRIMARY_V0_1_DOWNSTREAM_FREEZE_ELIGIBLE = consumed by completed freeze

VERIFIER_COST_BENCHMARK_EXECUTION_AUTHORIZED = consumed
VERIFIER_COST_BENCHMARK_EXECUTED = True
VERIFIER_COST_BENCHMARK_STATUS = BENCHMARK_COMPLETE

AUTHORITATIVE_FREEZER_EXECUTION_AUTHORIZED = consumed
AUTHORITATIVE_FREEZER_EXECUTION_AUTHORIZATION_COUNT = 1
AUTHORITATIVE_FREEZER_EXECUTED = True
AUTHORITATIVE_FREEZER_EXECUTION_COUNT = 1

FREEZER_INVOCATION_ON_GENERATOR_OUTPUT_AUTHORIZED = consumed
N64_WITNESS_FAMILY_FREEZE_AUTHORIZED = consumed
N64_WITNESS_FAMILY_FROZEN = True

PRIMARY_V0_1_GENERATOR_RERUN_AUTHORIZED = False
VERIFIER_COST_BENCHMARK_RERUN_AUTHORIZED = False
AUTHORITATIVE_FREEZER_RERUN_AUTHORIZED = False
N64_FALSIFIER_RERUN_AUTHORIZED = False

PsiTRS_EVALUATION_AUTHORIZED = False
SCIENTIFIC_INFERENCE_AUTHORIZED = False
PRODUCTION_INTEGRATION_AUTHORIZED = False
KERNEL_MODIFICATION_AUTHORIZED = False
LIVE_CAPTURE_AUTHORIZED = False
```

No second freezer execution is authorized.

---

## 13. Recommended next direction

```text
A. PREPARE FROZEN K=3 FAMILY EVIDENCE AND DOWNSTREAM EVALUATION CONTRACT
```

The next phase should remain docs-only and should:

```text
treat the canonical freeze result and embedded family manifest as immutable evidence
bind the accepted candidate indices [478, 479, 480]
extract and record the exact accepted pair records and family certificate without rewriting them
define the scientific question for any downstream evaluation before authorizing execution
keep descriptor-blind witness validity separate from PsiTRS response
specify controls, outputs, failure semantics, and interpretation limits
require a separate explicit execution authorization for any PsiTRS evaluation
preserve the production-kernel boundary
```

This findings record does not authorize that downstream evaluation.

---

## 14. Final disposition

```text
A. POSITIVE AUTHORITATIVE RETAINED-STREAM FREEZE RECORDED
```

The one authorized freezer invocation completed successfully.

The exact retained `PRIMARY_V0_1` stream produced a verified, replay-identical, frozen K=3 witness family at candidate indices:

```text
478
479
480
```

Canonical result and summary evidence were published under the exact authorization commit and frozen source identities.

No rerun, PsiTRS evaluation, scientific inference, production integration, or kernel modification is authorized by this findings document.

*End — TORMENT Brainvision Algebraic N=64 PRIMARY_V0_1 Authoritative Freezer Findings v0.1.*

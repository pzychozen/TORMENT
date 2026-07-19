# TORMENT Brainvision Algebraic N=64 PRIMARY_V0_1 Verifier-Cost Benchmark Findings v0.1

## 0. Disposition

```text
A. RECORD NON-AUTHORITATIVE VERIFIER-COST BENCHMARK COMPLETION
```

The exact one-run verifier-cost benchmark completed successfully under the committed execution authorization.

This findings record is engineering evidence only.

It does not authorize or report:

```text
authoritative freezer execution
family selection
family verification
family freezing
full-stream verifier timing
PsiTRS evaluation
production integration
scientific inference
```

---

## 1. Governing identities

Execution authorization commit:

```text
43dc0a75630bf63a46c47107565868c7736c157b
```

Benchmark implementation commit:

```text
ecbcfe593cc626e88cb6552d05a800d4286cdc52
```

Benchmark runner blob:

```text
72d1bb529441ac714ac49692b01f13bf8b23ae76
```

Verifier blob:

```text
db1e1fa606bdbf17fda62cd998aeb2a29d47d59a
```

Canonical serializer blob:

```text
6eb382b314325033443fc7331cae5050ee6e6ed2
```

Retained input whole-file SHA-256:

```text
00a816364ddcfc9d06dc8ce1225f58bca013e96a8914ff1eb665004b39ed949b
```

Retained input payload SHA-256:

```text
70763a2ebbf7ea71267553debee2bf79c2ed3b7b0c016d9a903161074e7bf8c5
```

---

## 2. Published artifact identities

Result whole-file SHA-256:

```text
4fe70713c52b805754e64de5a6205469b8a054d8256091ea6f5736dbf6a61c72
```

Canonical result-payload SHA-256:

```text
0e50d1999fdb4b75f6ec638212ffed4c3411e8b316f67ff44306d7f06e4cfcfd
```

Summary whole-file SHA-256:

```text
3caf733620061df5c664f29693ef459f07c2d9910f2ebd2cd08f53629b9bc6ed
```

Published benchmark status:

```text
BENCHMARK_COMPLETE
```

Failure record:

```text
absent
```

---

## 3. Exact executed profile

```text
benchmark_profile = PRIMARY_V0_1_FIXED_16_TWO_PASS
planned_call_count = 32
completed_call_count = 32
```

Exact sample order per pass:

```text
0, 1, 2, 3, 4, 5, 6, 7,
2499, 4999, 7499, 9999, 12499, 14999, 17499, 19999
```

Execution completed:

```text
pass 1 = 16 verify_candidate calls
pass 2 = 16 verify_candidate calls
total = 32 verify_candidate calls
```

No warmup, retry, third pass, randomization, parallelism, or full-stream continuation occurred.

---

## 4. Replay identity

```text
pass_to_pass_identity.checked = True
pass_to_pass_identity.all_match = True
mismatched_indices = []
```

For every sampled candidate, the canonical verifier-result SHA-256 from pass 1 exactly matched pass 2.

This is deterministic sampled verifier-output identity.

It is not authoritative freezer replay.

---

## 5. Timing findings

Combined overall:

```text
count = 32
minimum_ns = 33413100
maximum_ns = 54497500
mean_ns = 348062525/8
median_ns = 43872600/1
total_ns = 1392250100
```

Approximate overall mean:

```text
43.507816 ms per verify_candidate call
```

Pass means:

```text
pass 1 mean = 42.361731 ms
pass 2 mean = 44.653900 ms
```

Panel means:

```text
PREFIX_8 mean = 34.921031 ms
SPREAD_8 mean = 52.094600 ms
```

The sampled `SPREAD_8` calls were approximately:

```text
49.18% slower than PREFIX_8
```

The benchmark's published linear projections are:

```text
overall mean × 16 = 696125050 ns
overall mean × 20,000 = 870156312500 ns
overall mean × 40,000 = 1740312625000 ns
prefix mean × 40,000 = 1396841250000 ns
spread mean × 40,000 = 2083784000000 ns
```

Approximate two-pass verifier-component projection:

```text
overall center = 29.005 minutes
PREFIX_8 sensitivity = 23.281 minutes
SPREAD_8 sensitivity = 34.730 minutes
```

These are linear engineering projections only.

They are:

```text
not measured full-stream runtime
not total freezer runtime
not confidence intervals
not guarantees
```

---

## 6. Sampled verifier outcomes

Sampled pair-invalid candidates:

```text
0, 1, 2, 3, 4, 5, 6, 7
```

For all eight sampled prefix candidates, the ordered failure codes were:

```text
CANDIDATE_AFFINE_EQUIVALENT
CANDIDATE_TRIPLE_G_ALIGNABLE
```

Sampled pair-valid candidates:

```text
2499, 4999, 7499, 9999, 12499, 14999, 17499, 19999
```

All eight sampled spread candidates were pair-valid in both passes.

This establishes only that pair-valid candidates occur at multiple sampled positions throughout the retained stream.

It does not establish:

```text
that a valid three-candidate family exists
that the greedy freezer will accept the first three pair-valid candidates
that family-level cross-candidate exclusions will pass
that the freezer will terminate early
that the freezer will return a positive result
```

Family-level requirements such as member reuse, group-equivalence exclusion, and distinct autocorrelation classes were not evaluated by this benchmark.

---

## 7. Operational interpretation

The verifier component is operationally tractable on the authoritative Windows environment.

Observed evidence supports:

```text
a full two-pass verifier component is plausibly on the order of tens of minutes
the exact fixed sample produced stable verifier outputs
pair-valid candidates are present beyond the stream prefix
```

The benchmark does not measure:

```text
stream-loading overhead at full freezer scale
incremental family-eligibility costs
family verification costs
ledger construction
manifest construction
canonical publication overhead
total authoritative freezer runtime
```

The full freezer could terminate earlier than the 40,000-call projection if the greedy selector accepts a compatible family before stream exhaustion.

It could also incur additional non-verifier overhead.

---

## 8. Boundary confirmation

```text
authoritative_operation = False
family_selection_performed = False
family_verification_performed = False
family_freeze_performed = False
freezer_invoked = False
retained_stream_modified = False
scientific_inference_authorized = False
```

No production kernel or live TORMENT functionality was contacted.

---

## 9. Authority state after execution

```text
VERIFIER_COST_BENCHMARK_EXECUTION_AUTHORIZED = consumed
VERIFIER_COST_BENCHMARK_EXECUTION_AUTHORIZATION_COUNT = 1
VERIFIER_COST_BENCHMARK_EXECUTED = True
VERIFIER_COST_BENCHMARK_STATUS = BENCHMARK_COMPLETE

FREEZER_INVOCATION_ON_GENERATOR_OUTPUT_AUTHORIZED = False
N64_WITNESS_FAMILY_FREEZE_AUTHORIZED = False
N64_WITNESS_FAMILY_FROZEN = False

PsiTRS_EVALUATION_AUTHORIZED = False
SCIENTIFIC_INFERENCE_AUTHORIZED = False
```

---

## 10. Recommended next direction

```text
A. PREPARE EXACT AUTHORITATIVE RETAINED-STREAM FREEZER INVOCATION AUTHORIZATION
```

The next phase should:

```text
bind the committed freezer runner and freezer/verifier/serializer identities
bind the exact retained candidate stream
require main, HEAD == origin/main, and a clean tree
authorize exactly one authoritative freezer-runner invocation
forbid retries after verifier contact
preserve staged/final evidence
keep PsiTRS and production integration closed
record the resulting family or bounded greedy negative without overclaiming
```

No freezer execution is authorized by this findings document.

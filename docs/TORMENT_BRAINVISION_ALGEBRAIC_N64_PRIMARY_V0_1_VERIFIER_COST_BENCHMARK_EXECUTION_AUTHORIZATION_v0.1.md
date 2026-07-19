# TORMENT Brainvision Algebraic N=64 PRIMARY_V0_1 Verifier-Cost Benchmark Execution Authorization v0.1

## 0. Decision

```text
A. AUTHORIZE EXACT NON-AUTHORITATIVE VERIFIER-COST BENCHMARK EXECUTION
```

This document authorizes exactly one execution of the committed algebraic N=64 `PRIMARY_V0_1` verifier-cost benchmark under the frozen identity, profile, input, repository, publication, and interpretation boundaries below.

It does not authorize:

```text
the authoritative freezer runner
freeze(...)
freeze_with_replay(...)
family selection
family verification
family freezing
a full 20,000-record verifier benchmark
a full 40,000-call replay benchmark
a different sample
a third pass
a retry
PsiTRS
production integration
scientific inference
```

---

## 1. Governing specification

```text
docs/TORMENT_BRAINVISION_ALGEBRAIC_N64_PRIMARY_V0_1_VERIFIER_COST_BENCHMARK_SPECIFICATION_v0.1.md
```

The specification is accepted.

This authorization does not amend its semantics.

---

## 2. Accepted implementation identity

Implementation commit:

```text
ecbcfe593cc626e88cb6552d05a800d4286cdc52
```

Commit subject:

```text
research(brainvision): implement algebraic N64 verifier benchmark
```

Benchmark runner path:

```text
research/brainvision/run_algebraic_n64_primary_verifier_cost_benchmark_v0_1.py
```

Benchmark runner Git blob identity:

```text
72d1bb529441ac714ac49692b01f13bf8b23ae76
```

Verifier path and frozen Git blob identity:

```text
research/brainvision/witness_family_verifier_v0_1.py

db1e1fa606bdbf17fda62cd998aeb2a29d47d59a
```

Canonical serializer path and frozen Git blob identity:

```text
research/brainvision/witness_canonical_json_v0_1.py

6eb382b314325033443fc7331cae5050ee6e6ed2
```

The execution-authorization commit created from this document must be docs-only.

It must not alter:

```text
benchmark runner
benchmark tests
verifier
canonical serializer
retained candidate stream
freezer
freezer runner
generator
falsifier
PsiTRS
torment_service
```

The benchmark runner shall resolve and record the full execution `HEAD` dynamically. Therefore, the final execution commit identity will be the docs-only authorization commit, while the runner blob must remain exactly the identity above.

---

## 3. Frozen retained input

Path:

```text
research/brainvision/results/algebraic_n64_primary_v0_1/
  algebraic_n64_primary_v0_1_candidate_stream.json
```

Expected size:

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

Frozen structural identity:

```text
schema_name = brainvision_descriptor_blind_candidate_stream
schema_version = 0.1
verification_mode = PRIMARY_CANDIDATE_N64
N = 64
candidate_count = 20000
terminal_status = budget_exhausted
candidate_generation_index sequence = 0..19999
```

The input is read-only evidence.

No copying, rewriting, normalization, renaming, mutation, or replacement is authorized.

---

## 4. Exact authorized profile

```text
BENCHMARK_PROFILE = PRIMARY_V0_1_FIXED_16_TWO_PASS
```

Exact sample order per pass:

```text
0, 1, 2, 3, 4, 5, 6, 7,
2499, 4999, 7499, 9999, 12499, 14999, 17499, 19999
```

Exact execution count:

```text
pass 1 = 16 verify_candidate calls
pass 2 = 16 verify_candidate calls
maximum total = 32 verify_candidate calls
```

Authorized witness-side call:

```python
verifier.verify_candidate(record, 64)
```

Not authorized:

```text
warmup calls
third pass
adaptive extension
retry
parallelism
randomized order
different indices
full-stream continuation
verify_family
incremental_family_eligibility
freezer import or call
```

---

## 5. Exact operator command

From the authoritative Windows repository root:

```bat
python research\brainvision\run_algebraic_n64_primary_verifier_cost_benchmark_v0_1.py
```

No command-line argument is authorized.

No environment override is authorized.

Run the command exactly once.

A pre-contact refusal with exit code `2` does not consume the authorization only when:

```text
verify_candidate calls = 0
staging directory created = False
final directory created = False
```

Once any `verify_candidate` call occurs, the authorization is consumed regardless of exit code.

No automatic or manual retry is authorized after verifier contact.

A separate docs-only decision would be required for any second attempt.

---

## 6. Required pre-execution state

Immediately before execution require:

```text
branch = main
HEAD = origin/main
working tree clean, including untracked files
authorization document committed
benchmark runner blob = 72d1bb529441ac714ac49692b01f13bf8b23ae76
verifier blob = db1e1fa606bdbf17fda62cd998aeb2a29d47d59a
serializer blob = 6eb382b314325033443fc7331cae5050ee6e6ed2
final benchmark output directory absent
staging benchmark output directory absent
retained input identity exact
```

The exact full `HEAD` after committing this authorization document shall be recorded before execution and compared with the repository commit identity published by the benchmark result.

Do not run the benchmark while the authorization document is uncommitted.

---

## 7. Expected output boundary

Final directory:

```text
research/brainvision/results/
  algebraic_n64_primary_verifier_cost_benchmark_v0_1/
```

Staging directory:

```text
research/brainvision/results/
  .algebraic_n64_primary_verifier_cost_benchmark_v0_1.staging/
```

Exact final files on successful publication:

```text
algebraic_n64_primary_verifier_cost_benchmark_v0_1_result.json

algebraic_n64_primary_verifier_cost_benchmark_v0_1_summary.txt
```

The benchmark result is non-authoritative engineering evidence.

It must not create or publish:

```text
freeze_result
family manifest
family certificate
candidate decision ledger
modified candidate stream
```

---

## 8. Exit handling

```text
exit 0:
BENCHMARK_COMPLETE with exact two-file publication

exit 1:
verifier execution-invalid result, verifier exception, malformed result,
serialization failure, output mismatch, publication failure, I/O failure,
or post-publication stdout failure

exit 2:
pre-contact refusal
```

After verifier contact:

```text
do not retry
preserve staged or final evidence according to the committed runner
do not delete evidence
do not modify the retained candidate stream
```

After successful publication:

```text
do not rerun
do not overwrite
do not rename or edit result files
```

---

## 9. Required operator capture

Before execution, record:

```bat
git status --short --branch
git rev-parse HEAD
git rev-parse origin/main
git rev-parse HEAD:research/brainvision/run_algebraic_n64_primary_verifier_cost_benchmark_v0_1.py
git rev-parse HEAD:research/brainvision/witness_family_verifier_v0_1.py
git rev-parse HEAD:research/brainvision/witness_canonical_json_v0_1.py
```

Execute once:

```bat
python research\brainvision\run_algebraic_n64_primary_verifier_cost_benchmark_v0_1.py
```

Then record without editing artifacts:

```bat
echo EXIT_CODE=%ERRORLEVEL%
git status --short --branch
```

Inspect the published or retained result and summary directly.

Record whole-file hashes using:

```bat
certutil -hashfile research\brainvision\results\algebraic_n64_primary_verifier_cost_benchmark_v0_1\algebraic_n64_primary_verifier_cost_benchmark_v0_1_result.json SHA256

certutil -hashfile research\brainvision\results\algebraic_n64_primary_verifier_cost_benchmark_v0_1\algebraic_n64_primary_verifier_cost_benchmark_v0_1_summary.txt SHA256
```

If execution exits `1` before final publication, inspect and hash the retained staging artifacts instead.

Do not run a second invocation.

---

## 10. Permitted interpretation

Permitted:

```text
the fixed 16-record two-pass benchmark completed or failed
32 or fewer sampled verifier calls occurred
observed sampled call durations were recorded
pass-to-pass verifier-output hashes matched or differed
the published linear projections are engineering projections
```

Not permitted:

```text
the full freezer will take exactly the projected time
the full stream was benchmarked
the benchmark found a family
the benchmark failed to find a family
the retained stream contains or lacks a valid family
a freezer execution is now automatically authorized
Brainvision works
PsiTRS was validated
scientific perception or temporal order was demonstrated
```

---

## 11. Authority state

```text
DOCUMENTATION_AUTHORIZED = True

VERIFIER_COST_BENCHMARK_SPECIFICATION_ACCEPTED = True
VERIFIER_COST_BENCHMARK_IMPLEMENTED = True

VERIFIER_COST_BENCHMARK_EXECUTION_AUTHORIZED = True
VERIFIER_COST_BENCHMARK_EXECUTION_AUTHORIZATION_COUNT = 1
VERIFIER_COST_BENCHMARK_EXECUTED = False

FREEZER_INVOCATION_ON_GENERATOR_OUTPUT_AUTHORIZED = False
N64_WITNESS_FAMILY_FREEZE_AUTHORIZED = False
N64_WITNESS_FAMILY_FROZEN = False

PsiTRS_EVALUATION_AUTHORIZED = False
SCIENTIFIC_INFERENCE_AUTHORIZED = False
```

---

## 12. Disposition

```text
A. EXACT ONE-RUN VERIFIER-COST BENCHMARK EXECUTION AUTHORIZED
```

This authorization becomes operational only after this document is committed and pushed on `main`, with `HEAD == origin/main` and a clean working tree.

The benchmark may then be executed exactly once using the command in §5.

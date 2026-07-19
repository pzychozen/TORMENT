# TORMENT Brainvision Algebraic N=64 PRIMARY_V0_1 Verifier-Cost Benchmark Specification v0.1

## 0. Status

**DOCS-ONLY benchmark specification. Non-implementing and non-executing.**

This document specifies a separate, non-authoritative benchmark of the committed N=64 witness-pair verifier over a fixed subset of the retained algebraic `PRIMARY_V0_1` candidate stream.

It does not:

```text
implement the benchmark
authorize benchmark implementation
authorize benchmark execution
invoke the retained candidate stream
invoke verify_candidate
invoke the freezer
invoke freeze_with_replay
select a witness family
verify a witness family
freeze a witness family
authorize the authoritative freezer runner
contact PsiTRS
contact the production TORMENT kernel
support scientific inference
```

Prepared after accepted freezer-runner implementation:

```text
branch:
main

commit:
34d12b0ccf5914bd15578f70cbb047c1b23bab9e
```

Current authority:

```text
DOCUMENTATION_AUTHORIZED = True

VERIFIER_COST_BENCHMARK_SPECIFICATION_DRAFTED = True
VERIFIER_COST_BENCHMARK_SPECIFICATION_ACCEPTED = True

VERIFIER_COST_BENCHMARK_IMPLEMENTATION_AUTHORIZED = False
VERIFIER_COST_BENCHMARK_EXECUTION_AUTHORIZED = False
VERIFIER_COST_BENCHMARK_EXECUTED = False

FREEZER_INVOCATION_ON_GENERATOR_OUTPUT_AUTHORIZED = False
N64_WITNESS_FAMILY_FREEZE_AUTHORIZED = False
N64_WITNESS_FAMILY_FROZEN = False

PsiTRS_EVALUATION_AUTHORIZED = False
SCIENTIFIC_INFERENCE_AUTHORIZED = False
```

---

## 1. Purpose

The retained candidate stream contains 20,000 deterministic algebraic candidate records. The committed freezer performs a greedy linear scan and calls `verify_candidate(record, 64)` once per examined record in each of two internal replay passes.

The number of verifier calls is outcome-dependent:

```text
best path:
3 calls per internal pass
6 calls total

full-scan path:
20,000 calls per internal pass
40,000 calls total
```

No measured wall-clock cost currently exists.

The benchmark shall measure the dominant isolated operation:

```python
verifier.verify_candidate(record, 64)
```

over a fixed, explicit set of retained candidate records and two identical passes.

Its purpose is to produce bounded engineering evidence about:

```text
observed verifier latency
pass-to-pass output identity
prefix-versus-spread timing variation
linear full-scan cost projections
whether a later authoritative full-stream execution appears operationally reasonable
```

The benchmark is not an authoritative freezer run and cannot establish a witness-family outcome.

---

## 2. Governing documents and code

Governing documents:

```text
docs/TORMENT_BRAINVISION_ALGEBRAIC_N64_PRIMARY_V0_1_FREEZER_INVOCATION_PROTOCOL_v0.1.md

docs/TORMENT_BRAINVISION_ALGEBRAIC_N64_PRIMARY_V0_1_FREEZER_RUNNER_IMPLEMENTATION_SPECIFICATION_v0.1.md
```

Committed code whose behavior motivates the benchmark:

```text
research/brainvision/witness_family_verifier_v0_1.py
research/brainvision/witness_canonical_json_v0_1.py
research/brainvision/witness_family_freeze_v0_1.py
research/brainvision/run_algebraic_n64_primary_freeze_v0_1.py
```

Project-local imports are limited to:

```text
witness_family_verifier_v0_1
witness_canonical_json_v0_1
```

Permitted standard-library imports are limited to modules needed for:

```text
CLI handling
paths
hashing
JSON loading
Git subprocess checks
timing
platform and environment metadata
publication
tests
```

No project-local freezer, generator, PsiTRS, descriptor, falsifier, or production-service import is permitted.

The benchmark shall not import or call the freezer or the authoritative freezer runner.

Frozen source blob identities at the specification baseline:

```text
verifier:
db1e1fa606bdbf17fda62cd998aeb2a29d47d59a

canonical serializer:
6eb382b314325033443fc7331cae5050ee6e6ed2
```

---

## 3. Benchmark identity

Implementation filename:

```text
research/brainvision/run_algebraic_n64_primary_verifier_cost_benchmark_v0_1.py
```

Test filename:

```text
tests/research/test_brainvision_run_algebraic_n64_primary_verifier_cost_benchmark_v0_1.py
```

Document filename:

```text
docs/TORMENT_BRAINVISION_ALGEBRAIC_N64_PRIMARY_V0_1_VERIFIER_COST_BENCHMARK_SPECIFICATION_v0.1.md
```

Identity constants:

```text
BENCHMARK_NAME = run_algebraic_n64_primary_verifier_cost_benchmark_v0_1
BENCHMARK_VERSION = 0.1
BENCHMARK_CLASS = NON_AUTHORITATIVE_VERIFIER_COST_BENCHMARK
BENCHMARK_PROFILE = PRIMARY_V0_1_FIXED_16_TWO_PASS
```

---

## 4. Boundary classification

The benchmark shall be:

```text
offline
prerecorded
quarantined
service-disconnected
descriptor-blind
non-runtime
non-production
non-authoritative
engineering-only
```

It shall not:

```text
call freeze(...)
call freeze_with_replay(...)
call incremental_family_eligibility(...)
call verify_family(...)
call select_family(...)
assemble accepted candidates
construct a family certificate
construct a family manifest
publish a freeze_result
report family_frozen
claim a valid or invalid family
modify the candidate stream
contact PsiTRS
contact descriptors or SAG
contact torment_service
```

Calling `verify_candidate` is authorized only by a later benchmark-execution authorization and only for the exact records specified here.

---

## 5. Exact operator interface

The future implementation shall expose exactly:

```bat
python research\brainvision\run_algebraic_n64_primary_verifier_cost_benchmark_v0_1.py
```

No command-line arguments are permitted.

No environment-variable override is permitted.

The operator cannot choose:

```text
input path
result path
record indices
record count
number of passes
N
timeout
worker count
parallelism
warmup count
source path
repository identity
overwrite behavior
projection formula
```

Any command-line argument is a pre-contact refusal:

```text
exit code = 2
verifier calls = 0
published artifacts = 0
staging directory created = False
```

An internal `run_operation(...)` may accept test-only repository/result roots, output streams, timers, and clock providers. These hooks must be unreachable from the CLI and may not change production constants.

---

## 6. Exact retained input

Input path:

```text
research/brainvision/results/algebraic_n64_primary_v0_1/
  algebraic_n64_primary_v0_1_candidate_stream.json
```

Frozen identity:

```text
whole-file size:
6,421,010 bytes

whole-file SHA-256:
00a816364ddcfc9d06dc8ce1225f58bca013e96a8914ff1eb665004b39ed949b

candidate-stream payload SHA-256:
70763a2ebbf7ea71267553debee2bf79c2ed3b7b0c016d9a903161074e7bf8c5
```

Frozen structure:

```text
schema_name = brainvision_descriptor_blind_candidate_stream
schema_version = 0.1
verification_mode = PRIMARY_CANDIDATE_N64
N = 64
candidate_count = 20000
terminal_status = budget_exhausted
candidate_generation_index sequence = 0..19999
```

The benchmark shall load the retained file once in binary mode and perform the same identity class of checks as the authoritative runner:

```text
exact path
regular non-symlink file
exact size
whole-file SHA-256
strict UTF-8
duplicate-key rejection
nonfinite-token rejection
canonical-byte equality
payload-hash equality
validate_stream_envelope(...)
exact structural identity
contiguous candidate indices
```

It shall not rewrite, normalize, copy, rename, or change the retained artifact.

---

## 7. Exact benchmark sample

The benchmark shall use exactly 16 unique records divided into two frozen panels.

### 7.1 Prefix panel

```text
panel name:
PREFIX_8

candidate_generation_indices:
0
1
2
3
4
5
6
7
```

Purpose:

```text
measure the exact start of the greedy authoritative stream
capture the region most likely to be examined if K=3 is reached early
```

### 7.2 Spread panel

```text
panel name:
SPREAD_8

candidate_generation_indices:
2499
4999
7499
9999
12499
14999
17499
19999
```

Purpose:

```text
measure implementation cost across the retained stream
detect large cost variation not visible in the first eight records
```

### 7.3 Frozen verification order

Each pass shall use:

```text
0, 1, 2, 3, 4, 5, 6, 7,
2499, 4999, 7499, 9999, 12499, 14999, 17499, 19999
```

No random sampling, shuffling, replacement, adaptive selection, or operator-selected index is allowed.

For each expected frozen index `i` in the sample list, require:

```text
stream["records"][i]["candidate_generation_index"] == i
```

Record the sample-order position separately as `0..15`.

The stored `candidate_generation_index` is never required to equal the sample-order position except where that happens accidentally in `PREFIX_8`.

---

## 8. Two-pass execution profile

The benchmark shall perform exactly two measured passes.

```text
pass 1:
the 16 frozen records in frozen order

pass 2:
the same 16 records in the same order
```

Total planned calls:

```text
16 calls per pass
32 calls total
```

There is no separate warmup call.

Reason:

```text
pass 1 records cold-start and first-use effects
pass 2 records repeated-use effects
the two passes mirror the committed freezer's replay count without invoking freezer semantics
```

The benchmark shall not perform a third pass, automatic retry, adaptive extension, or full-stream continuation.

---

## 9. Exact timed region

Timing primitive:

```python
time.perf_counter_ns()
```

For each record, the timed region shall contain exactly one call:

```python
started_ns = perf_counter_ns()
result = verifier.verify_candidate(record, 64)
completed_ns = perf_counter_ns()
duration_ns = completed_ns - started_ns
```

Outside the timed region, the benchmark may:

```text
validate result shape
canonically serialize the result
hash the canonical result
record diagnostics
update aggregate statistics
```

The timed region shall not include:

```text
input loading
JSON parsing
stream validation
Git checks
source hashing
output canonicalization
output writing
summary writing
projection calculation
```

No threading, multiprocessing, asynchronous execution, subprocess worker, CPU affinity manipulation, or priority manipulation is permitted in v0.1.

---

## 10. Verifier-output handling

For every verifier call, require a top-level mapping containing at least:

```text
execution_invalid
execution_code
pair_certificate
ordered_failure_codes
primary_failure_code
pair_valid
```

The benchmark shall require strict Boolean values for:

```text
execution_invalid
pair_valid
```

The exact returned object shall be canonically serialized using `witness_canonical_json_v0_1` and hashed.

Per-call evidence:

```text
pass number
panel
position within pass
candidate_generation_index
duration_ns
execution_invalid
execution_code
pair_valid
primary_failure_code
ordered_failure_codes
canonical_result_sha256
```

The full pair certificate may be omitted from the benchmark artifact to avoid duplicating large verifier output. Its canonical hash remains recorded.

No verifier return may be interpreted as a family result.

---

## 11. Pass-to-pass identity

For each of the 16 candidate indices, require:

```text
pass_1 canonical_result_sha256 == pass_2 canonical_result_sha256
```

Aggregate identity:

```text
all 16 per-index hashes match
```

If any per-index result differs:

```text
benchmark_status = OUTPUT_REPLAY_MISMATCH
exit code = 1
result artifact may be published
scientific inference = prohibited
authoritative execution implication = none
```

This is benchmark-output identity only.

It is not the freezer's internal replay record and must not be named or reported as an authoritative freezer replay.

---

## 12. Execution-invalid verifier return

If `verify_candidate` returns:

```text
execution_invalid = True
```

the benchmark shall:

```text
record the exact index, pass, execution_code, duration, and result hash
stop before any later verifier call
publish a benchmark failure result when possible
return exit code 1
```

It shall not:

```text
retry the record
continue to other records
translate the result into a freezer failure_record
claim the full stream is execution-invalid
```

A benchmark execution-invalid return is evidence only about the sampled call that produced it.

---

## 13. Exceptions

If `verify_candidate` raises:

```text
stop immediately
do not retry
retain any staged evidence
record VERIFIER_CALL_EXCEPTION
return exit code 1
```

If result canonicalization fails:

```text
stop immediately
record RESULT_SERIALIZATION_FAILURE
retain staged evidence
return exit code 1
```

No exception may trigger fallback mathematics or a different verifier path.

---

## 14. Statistics

For completed calls, report integer nanoseconds and derived seconds.

Per panel and overall, for each pass and both passes combined:

```text
count
total_ns
minimum_ns
maximum_ns
mean_ns
median_ns
p25_ns
p75_ns
```

Median shall use the exact deterministic rule:

```text
odd count:
the middle sorted duration

even count:
the arithmetic mean of the two middle sorted durations
```

If an even-count median is non-integer, canonical evidence shall emit it as either:

```text
an exact numerator and denominator

or

a decimal string with no binary floating-point ambiguity
```

Percentiles shall use one exact, documented deterministic rule:

```text
nearest-rank on the sorted integer duration list
rank = ceil(p * count)
1-based rank, clamped to [1, count]
```

No confidence interval, normality assumption, random-sample inference, or statistical significance claim is permitted.

---

## 15. Linear projections

Only after all 32 calls complete successfully, calculate descriptive linear projections.

Let:

```text
overall_mean_ns = arithmetic mean of all 32 measured durations
prefix_mean_ns = arithmetic mean of PREFIX_8 durations across both passes
spread_mean_ns = arithmetic mean of SPREAD_8 durations across both passes
```

Report:

```text
observed 16-record one-pass equivalent:
overall_mean_ns * 16

projected 20,000-call full-scan single pass:
overall_mean_ns * 20,000

projected 40,000-call full-scan two-pass verifier component:
overall_mean_ns * 40,000

prefix-panel two-pass full-scan sensitivity:
prefix_mean_ns * 40,000

spread-panel two-pass full-scan sensitivity:
spread_mean_ns * 40,000
```

Convert projections to seconds, minutes, and hours.

Every projection must be labeled:

```text
linear engineering projection
not measured full-stream runtime
not total freezer runtime
not a confidence interval
not a guarantee
```

The projections exclude:

```text
stream loading and validation
freezer self-checks
incremental family eligibility
decision-ledger construction
family verification
result and manifest construction
canonical replay construction
publication
```

The authoritative freezer may stop after K=3 and therefore may perform far fewer than 40,000 verifier calls.

The sample is deterministic and nonrandom. No population-generalization claim is permitted.

---

## 16. Environment record

The benchmark artifact shall record non-secret environment facts needed to interpret timing:

```text
Python version
Python implementation
operating-system name
operating-system release
machine architecture
logical CPU count
benchmark process bitness
`time.get_clock_info("perf_counter")` resolution
`time.get_clock_info("perf_counter")` monotonic flag
`time.get_clock_info("perf_counter")` adjustable flag
```

It shall not record:

```text
user name
computer name
home directory
absolute repository path
network identity
IP address
environment-variable dump
```

No environment fact may change benchmark control flow.

---

## 17. Repository and source provenance

Before verifier contact, require:

```text
repository root derived from benchmark runner path
Git toplevel equals derived root
branch = main
HEAD resolves to full lowercase commit
origin/main = HEAD
tracked and untracked working tree clean
```

Ignored retained evidence under `research/brainvision/results/` remains compatible with the clean-tree check.

The benchmark shall not call `verifier.validate_local_configuration(...)` in v0.1.

Instead, before verifier contact it shall perform direct repository and source checks for:

```text
verifier:
research/brainvision/witness_family_verifier_v0_1.py

serializer:
research/brainvision/witness_canonical_json_v0_1.py

benchmark runner:
research/brainvision/run_algebraic_n64_primary_verifier_cost_benchmark_v0_1.py
```

For each of these three sources require:

```text
exact relative path
regular non-symlink file
path remains under research/brainvision
HEAD tree entry is a blob
expected Git blob identity where frozen by this specification
local raw bytes equal committed blob bytes
raw-byte SHA-256 recorded
```

Strict local-byte equality to committed Git blob bytes is intentional on Windows. A CRLF-normalized checkout whose working-tree bytes differ from the committed LF blob bytes must refuse rather than silently benchmark different source bytes.

The benchmark may record `verifier.verifier_configuration()` and its canonical hash as descriptive configuration evidence, but it must not validate or read the freezer source as part of this cost benchmark.

A later benchmark-execution authorization commit must be docs-only and must modify none of:

```text
benchmark runner
benchmark tests
verifier
canonical serializer
retained candidate-stream input
```

The full execution HEAD shall be recorded dynamically in the benchmark result.

---

## 18. Pre-contact order

The runner shall refuse before any `verify_candidate` call unless all checks pass in this order:

```text
1. no CLI arguments
2. final output directory absent
3. staging directory absent
4. repository root valid
5. runner path ownership valid
6. branch main
7. HEAD resolved
8. origin/main equals HEAD
9. working tree clean
10. benchmark runner committed and local bytes equal committed bytes
11. verifier path/blob/local bytes valid
12. serializer path/blob/local bytes valid
13. direct verifier, serializer, and runner source checks valid
14. retained input path valid
15. input size and whole-file hash valid
16. strict canonical JSON valid
17. payload hash valid
18. stream envelope valid
19. frozen stream structure valid
20. selected indices resolve exactly
```

A pre-contact refusal shall:

```text
call verify_candidate zero times
create no staging directory
publish no artifact
write a concise diagnostic to stderr
return exit code 2
```

---

## 19. Output paths

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

Exact artifact set:

```text
algebraic_n64_primary_verifier_cost_benchmark_v0_1_result.json
algebraic_n64_primary_verifier_cost_benchmark_v0_1_summary.txt
```

The benchmark shall not create:

```text
freeze_result.json
family_manifest.json
family_certificate.json
candidate_decision_ledger.json
modified candidate stream
```

---

## 20. Canonical benchmark result

The result shall use:

```text
schema_name = brainvision_verifier_cost_benchmark_result
schema_version = 0.1
benchmark_class = NON_AUTHORITATIVE_VERIFIER_COST_BENCHMARK
benchmark_profile = PRIMARY_V0_1_FIXED_16_TWO_PASS
authoritative_operation = False
family_selection_performed = False
family_verification_performed = False
family_freeze_performed = False
```

The top-level envelope shall be:

```json
{
  "verifier_cost_benchmark_result": { ... },
  "verifier_cost_benchmark_result_sha256": "<canonical payload SHA-256>"
}
```

The exact canonical returned result shall include at least:

```text
repository_commit_identity
source_identities
input_identity
sample_definition
environment
planned_call_count
completed_call_count
call_records
statistics
linear_projections
pass_to_pass_identity
benchmark_status
failure_record
boundary_declarations
```

Canonical JSON rules:

```text
UTF-8
ensure_ascii=True
sorted keys
compact separators
allow_nan=False
no trailing newline
```

Durations and derived values must be finite.

Prefer integer nanoseconds and integer projected nanoseconds as canonical evidence. Human-readable decimal seconds/minutes/hours may be derived in the summary.

---

## 21. Benchmark statuses

Successful complete benchmark:

```text
BENCHMARK_COMPLETE
```

Failure statuses:

```text
OUTPUT_REPLAY_MISMATCH
VERIFIER_EXECUTION_INVALID
VERIFIER_CALL_EXCEPTION
RESULT_SERIALIZATION_FAILURE
BENCHMARK_RESULT_INVALID
PUBLICATION_FAILURE
```

A complete benchmark requires:

```text
completed_call_count = 32
all planned indices evaluated in exact order twice
no verifier execution-invalid return
no exception
all per-index pass hashes identical
all durations strict nonnegative integers
statistics complete
projections complete
```

No benchmark status may be translated into a witness-family result.

---

## 22. Exit contract

```text
0
A complete two-file benchmark artifact set was published with
benchmark_status = BENCHMARK_COMPLETE.

1
Verifier execution-invalid result, verifier exception, output mismatch,
result-validation failure, serialization failure, I/O failure,
publication failure, or post-publication stdout failure.

2
Pre-contact refusal.
```

Exit code `0` means only that the benchmark completed under this profile.

It does not authorize or predict a freezer outcome.

---

## 23. Publication

All files shall be completed inside staging.

Use:

```text
exclusive binary creation
exact staged two-file set
same-parent staging-to-final rename
never overwrite final
never overwrite staging
never overwrite files
```

The JSON result is canonical evidence.

The UTF-8/LF summary is human convenience and shall state:

```text
benchmark is non-authoritative
verify_candidate calls completed
freezer calls = 0
family-selection calls = 0
family-verification calls = 0
family frozen = not evaluated
retained stream modified = False
```

After successful rename, final output shall never be rolled back.

---

## 24. Failure retention

Before verifier contact:

```text
no evidence exists
empty staging may be removed
```

After verifier contact:

```text
no automatic retry
retain staged evidence bytes
retain complete staging after rename failure
retained staging blocks another execution
```

If the final directory is published and stdout mirroring fails:

```text
final output remains authoritative benchmark evidence
exit code = 1
no rollback
```

---

## 25. Test requirements

All tests shall use:

```text
temporary Git repositories
synthetic canonical candidate streams
synthetic verifier results
temporary result roots
injected deterministic timers
injected deterministic UTC clocks where needed
```

The real retained stream shall never be read by tests.

The real results directory shall never be written by tests.

### 25.1 Absolute call guards

An autouse fixture shall replace at least:

```text
verifier.verify_candidate
verifier.verify_family
```

with raising guards.

Tests that need verifier output may explicitly replace only `verifier.verify_candidate` with a synthetic stub.

AST tests shall prove the benchmark runner has:

```text
exactly one verify_candidate call site
zero incremental_family_eligibility call sites
zero verify_family call sites
zero freeze call sites
zero freeze_with_replay call sites
zero import of witness_family_freeze_v0_1
zero import of run_algebraic_n64_primary_freeze_v0_1
```

### 25.2 Profile tests

Prove:

```text
exact frozen 16 indices
exact pass order
exactly two passes
exactly 32 successful calls
no warmup
no third pass
no adaptive extension
```

### 25.3 Timed-region test

Using an event-logging timer and verifier stub, prove each call order is:

```text
timer start
one verify_candidate call
timer end
```

and that canonicalization/hashing occurs outside the measured interval.

### 25.4 Output-identity tests

Cover:

```text
all pass hashes equal -> BENCHMARK_COMPLETE
one per-index mismatch -> OUTPUT_REPLAY_MISMATCH
```

### 25.5 Verifier failure tests

Cover:

```text
execution_invalid on pass 1 -> stop, publish failure, exit 1, no retry
execution_invalid on pass 2 -> stop, publish failure, exit 1, no retry
exception -> stop, retain evidence, exit 1, no retry
unserializable result -> stop, retain evidence, exit 1
malformed result shape -> BENCHMARK_RESULT_INVALID
```

### 25.6 Pre-contact tests

Cover at least:

```text
CLI argument
final exists
staging exists
wrong root
wrong branch
detached HEAD
origin/main mismatch
dirty tracked file
untracked file
runner not committed
runner local-byte mismatch
verifier blob mismatch
verifier local-byte mismatch
serializer blob mismatch
serializer local-byte mismatch
invalid local configuration
missing input
input symlink
wrong size
wrong whole-file hash
invalid UTF-8
duplicate key
nonfinite token
noncanonical bytes
wrong payload hash
wrong schema
wrong mode
wrong N
wrong count
wrong terminal status
noncontiguous indices
missing sampled index
sampled index mismatch
```

### 25.7 Statistics and projections

Use deterministic durations to verify exact:

```text
count
sum
minimum
maximum
mean
median
nearest-rank p25
nearest-rank p75
20,000-call projection
40,000-call projection
prefix sensitivity projection
spread sensitivity projection
```

### 25.8 Publication tests

Cover:

```text
exact two-file output set
canonical JSON no trailing newline
summary LF with one trailing LF
never overwrite
partial staging retained after post-contact write failure
complete staging retained after rename failure
published final survives stdout failure
```

### 25.9 Real-path protection

Tests shall fail immediately on any attempt to:

```text
open the real retained candidate stream
create the real benchmark final directory
create the real benchmark staging directory
write under the real results root
```

---

## 26. Focused test command

Future implementation testing:

```bat
python -m pytest -q ^
  tests\research\test_brainvision_run_algebraic_n64_primary_verifier_cost_benchmark_v0_1.py
```

A combined suite may include:

```text
freezer runner tests
witness verifier tests
witness freezer tests
primary generator-runner tests
```

No test may execute real witness mathematics.

---

## 27. Benchmark implementation acceptance

Implementation may be accepted only when review confirms:

```text
exact fixed sample and order
two passes and 32 calls only
timed region contains only verify_candidate
no family selection or family verification
no freezer import or call
exact retained input binding
exact verifier/serializer source binding
clean repository and dynamic HEAD binding
canonical benchmark result, not freeze_result
honest projections and limitations
never-overwrite atomic publication
post-contact evidence retention
tests cannot touch real verifier mathematics, stream, or results paths
```

---

## 28. Benchmark execution authorization gate

Even after implementation is committed, benchmark execution remains unauthorized until a separate docs-only decision records:

```text
exact benchmark runner commit
exact benchmark runner blob identity
exact verifier and serializer blob identities
exact retained input hashes
exact profile PRIMARY_V0_1_FIXED_16_TWO_PASS
expected maximum 32 verify_candidate calls
no freezer/family-selection authorization
```

That authorization commit must be `HEAD == origin/main` with a clean tree when execution begins.

---

## 29. Interpretation contract

Permitted post-benchmark statements:

```text
the fixed 16-record, two-pass benchmark completed or failed
observed per-call durations were X under the recorded environment
pass outputs did or did not match
linear full-scan verifier-component projections were X
```

Prohibited statements:

```text
the full freezer will take exactly X
the benchmark found or failed to find a witness family
the full stream contains or lacks a valid family
the authoritative run is safe merely because the benchmark completed
Brainvision works
temporal order was detected
PsiTRS was validated
scientific perception was demonstrated
```

A later full-stream authorization decision must separately weigh:

```text
observed timing
projection uncertainty
available operator time
failure-retention behavior
the possibility of early K=3 termination
the possibility of a full 40,000-call path
```

---

## 30. Immutable boundaries

The benchmark implementation and execution must not modify or contact:

```text
research/brainvision/psi_trs.py
research/brainvision/run_n64_falsifier_v0_1.py
research/brainvision/algebraic_direct_sum_n64_candidate_generator_v0_1.py
research/brainvision/run_algebraic_n64_primary_v0_1.py
research/brainvision/run_algebraic_n64_primary_freeze_v0_1.py
research/brainvision/witness_family_freeze_v0_1.py
torment_service/kernel/
torment_service/memory_kernel.py
torment_service/fabric.py
```

The benchmark may read only the exact retained candidate-stream file and the exact committed verifier, serializer, and benchmark-runner source bytes required by this specification after separate execution authorization. It must not read or bind the freezer source.

---

## 31. Disposition

```text
A. VERIFIER_COST_BENCHMARK_SPECIFICATION_ACCEPTED
```

The focused adversarial review is complete and all required corrections have been applied.

This accepts the specification as the governing contract for later implementation.

It does not authorize implementation or execution.

---

## 32. Authority state after this draft

```text
DOCUMENTATION_AUTHORIZED = True

VERIFIER_COST_BENCHMARK_SPECIFICATION_DRAFTED = True
VERIFIER_COST_BENCHMARK_SPECIFICATION_ACCEPTED = True

VERIFIER_COST_BENCHMARK_IMPLEMENTATION_AUTHORIZED = False
VERIFIER_COST_BENCHMARK_IMPLEMENTED = False

VERIFIER_COST_BENCHMARK_EXECUTION_AUTHORIZED = False
VERIFIER_COST_BENCHMARK_EXECUTED = False

FREEZER_RUNNER_IMPLEMENTED = True
FREEZER_INVOCATION_ON_GENERATOR_OUTPUT_AUTHORIZED = False
N64_WITNESS_FAMILY_FREEZE_AUTHORIZED = False
N64_WITNESS_FAMILY_FROZEN = False

PsiTRS_EVALUATION_AUTHORIZED = False
SCIENTIFIC_INFERENCE_AUTHORIZED = False
```

---

## 33. Conclusion

The next unknown is computational, not mathematical.

The committed verifier and greedy freezer semantics already exist. The benchmark shall therefore isolate the dominant verifier call over a fixed, reproducible 16-record sample, repeat that exact sample twice, and report measured cost without performing family selection or freezing.

This gives the project enough engineering evidence to make a later full-stream authorization decision while preserving every existing quarantine, provenance, and scientific-claim boundary.

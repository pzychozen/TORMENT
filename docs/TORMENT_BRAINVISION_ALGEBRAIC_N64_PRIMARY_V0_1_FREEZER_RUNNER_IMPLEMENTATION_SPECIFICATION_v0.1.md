# TORMENT Brainvision Algebraic N=64 PRIMARY_V0_1 Freezer Runner Implementation Specification v0.1

## 0. Status

**DOCS-ONLY implementation specification. Non-implementing, non-executing, non-authorizing.**

This document specifies a dedicated operator runner that may later submit the retained algebraic `PRIMARY_V0_1` candidate stream to the committed witness-family freezer.

It does not:

```text
invoke the verifier
invoke the freezer
evaluate any candidate
search for a family
freeze a family
run a benchmark
authorize implementation
authorize execution
contact PsiTRS
contact the production TORMENT kernel
```

Current authority:

```text
DOCUMENTATION_AUTHORIZED = True

FREEZER_RUNNER_IMPLEMENTATION_AUTHORIZED = False
FREEZER_INVOCATION_ON_GENERATOR_OUTPUT_AUTHORIZED = False
N64_WITNESS_FAMILY_FREEZE_AUTHORIZED = False
PsiTRS_EVALUATION_AUTHORIZED = False
SCIENTIFIC_INFERENCE_AUTHORIZED = False
```

Prepared against repository baseline:

```text
branch:
main

commit:
541b47f7b2c4f1a00139d7ba8915f2c98a46ead8
```

---

## 1. Purpose

The runner shall provide the missing operational boundary between:

```text
retained ignored candidate-stream file
        ↓
exact provenance and input validation
        ↓
one call to freeze_with_replay(...)
        ↓
canonical freeze-result publication
```

The runner is not a mathematical component.

It must not:

```text
reimplement verifier predicates
preselect candidates
enumerate candidate triples
add backtracking
alter greedy selection
call verify_candidate directly
call verify_family directly
call freeze(...)
perform an outer replay
interpret Brainvision usefulness
```

The committed freezer remains the sole owner of:

```text
candidate verification
incremental family eligibility
greedy first-K selection
family verification
internal two-pass replay
configuration self-check
independence self-check
regression self-check
family-manifest construction
```

The runner may perform pre-contact container and identity validation, including
`verifier.validate_stream_envelope(...)`, solely to refuse malformed or wrong input before freezer contact.
It must not evaluate candidate or family witness predicates.

---

## 2. Governing artifacts

The implementation shall be governed by:

```text
docs/TORMENT_BRAINVISION_ALGEBRAIC_N64_PRIMARY_V0_1_FREEZER_INVOCATION_PROTOCOL_v0.1.md

docs/TORMENT_BRAINVISION_INDEPENDENT_DESCRIPTOR_BLIND_HIGHER_ORDER_WITNESS_FAMILY_IMPLEMENTATION_SPECIFICATION_v0.1.md

docs/TORMENT_BRAINVISION_INDEPENDENT_HIGHER_ORDER_WITNESS_VERIFIER_AND_FREEZE_INFRASTRUCTURE_IMPLEMENTATION_SPECIFICATION_v0.1.md
```

Committed implementation sources:

```text
research/brainvision/witness_family_verifier_v0_1.py
research/brainvision/witness_canonical_json_v0_1.py
research/brainvision/witness_family_freeze_v0_1.py
```

Their Git blob identities at the governing baseline are:

```text
verifier:
db1e1fa606bdbf17fda62cd998aeb2a29d47d59a

serializer:
6eb382b314325033443fc7331cae5050ee6e6ed2

freezer:
cf4ea57890fbbbdf9593879cf648b84c6c68d9b0
```

These blob identities are runner pre-contact constants. They prevent a later authorization-only commit from silently changing the mathematical implementation.

---

## 3. Exact implementation artifact

The implementation filename is frozen as:

```text
research/brainvision/run_algebraic_n64_primary_freeze_v0_1.py
```

Test filename:

```text
tests/research/test_brainvision_run_algebraic_n64_primary_freeze_v0_1.py
```

Runner identity:

```text
RUNNER_NAME = run_algebraic_n64_primary_freeze_v0_1
RUNNER_VERSION = 0.1
```

The implementation shall be:

```text
offline
prerecorded
quarantined
service-disconnected
descriptor-blind
non-runtime
non-production
descriptive-only
stdlib-based except for the committed serializer, verifier, and freezer
```

---

## 4. Operator interface

The complete operator interface shall be:

```bat
python research\brainvision\run_algebraic_n64_primary_freeze_v0_1.py
```

The runner shall accept no command-line arguments.

It shall expose no operator-controlled:

```text
input path
output path
repository path
commit identity
candidate prefix
candidate count
selector
budget
timeout
worker count
source path
hash override
overwrite flag
resume flag
benchmark mode
environment-variable override
```

Any command-line argument is a pre-contact refusal and shall return exit code `2` without contacting the freezer, publishing anything, or creating a staging directory.

An internal `run_operation(...)` may accept test-only repository/result roots and diagnostic streams. Those parameters must be unreachable from the CLI and must not alter production defaults.

---

## 5. Import boundary

Permitted imports:

```text
__future__
hashlib
json
os
shutil
stat
subprocess
sys
typing

witness_canonical_json_v0_1
witness_family_verifier_v0_1
witness_family_freeze_v0_1
```

The verifier import may be used only for:

```text
validate_stream_envelope(...)
validate_local_configuration(...)
published failure-code constants
```

The runner shall never call:

```text
verify_candidate(...)
verify_family(...)
member_certificate(...)
triple_array(...)
```

Forbidden imports or contacts include:

```text
algebraic_direct_sum_n64_candidate_generator_v0_1
psi_trs
run_n64_falsifier_v0_1
descriptors
SAG
paired prerecorded analysis
torment_service
network libraries
```

---

## 6. Repository-root ownership

The production repository root shall be derived from the runner’s own real path.

Expected relationship:

```text
<repository root>\
  research\
    brainvision\
      run_algebraic_n64_primary_freeze_v0_1.py
```

The runner shall use fixed-argument, non-shell Git subprocesses only. It shall make no network request and shall not run `git fetch`, `git pull`, or any modifying Git operation.

Before freezer contact, it must establish:

```text
git rev-parse --show-toplevel
    resolves exactly to the derived repository root

git symbolic-ref --short -q HEAD
    equals main

git rev-parse --verify HEAD^{commit}
    returns one full lowercase commit identity

git rev-parse --verify refs/remotes/origin/main^{commit}
    equals HEAD

git status --porcelain=v1 --untracked-files=all
    is empty
```

Ignored evidence under `research/brainvision/results/` does not invalidate the clean-tree check.

Failure to establish any repository condition is a pre-contact refusal.

### 6.1 Runtime commit identity

The runner shall not hard-code the later execution commit.

Instead, immediately before execution it shall resolve the full current `HEAD` commit and pass that exact value as:

```python
repository_commit_identity=resolved_head_commit
```

This avoids a self-referential commit constant.

A later execution may be authorized only after:

```text
the runner implementation and tests are committed
focused review is complete
a separate docs-only authorization decision is committed
the authorization commit modifies none of:
  runner
  runner tests
  verifier
  serializer
  freezer
  retained candidate-stream input
that authorization commit is pushed
HEAD == origin/main
the tree is clean
```

The manifest will thereby record the exact authorization-state repository commit used by the operation.

---

## 7. Source-path and source-byte binding

Exact source paths from the resolved repository root:

```text
verifier:
research/brainvision/witness_family_verifier_v0_1.py

serializer:
research/brainvision/witness_canonical_json_v0_1.py

freeze:
research/brainvision/witness_family_freeze_v0_1.py
```

For each source, the runner shall refuse before freezer contact unless:

```text
the relative path is exact
the resolved path remains inside research/brainvision/
the entry is a regular file
the path is not a symlink
the HEAD tree entry is a regular blob
the HEAD blob identity equals the frozen blob identity in §2
the local raw file bytes equal the committed Git blob bytes
```

The runner shall compute SHA-256 over each committed blob’s raw bytes.

It shall then call:

```python
verifier.validate_local_configuration(
    repository_root=repository_root,
    source_paths=explicit_source_paths,
    expected_source_hashes=git_derived_source_sha256,
)
```

This call performs configuration and source-ownership validation only. It must not evaluate any candidate.

The returned result must be valid before freezer contact.

The same explicit absolute `source_paths` mapping shall later be passed to `freeze_with_replay`.

---

## 8. Frozen input artifact

Exact input path:

```text
research/brainvision/results/algebraic_n64_primary_v0_1/
  algebraic_n64_primary_v0_1_candidate_stream.json
```

Frozen file identity:

```text
expected size:
6,421,010 bytes

whole-file SHA-256:
00a816364ddcfc9d06dc8ce1225f58bca013e96a8914ff1eb665004b39ed949b

candidate-stream payload SHA-256:
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

The input must be a non-symlink regular file at the exact path. The runner shall read it once in binary mode and must never rewrite, rename, normalize, relocate, copy, or change it.

---

## 9. Strict input loading

The pre-contact input sequence is frozen as:

1. Resolve and validate the exact path.
2. Read all bytes once.
3. Verify exact byte count.
4. Verify whole-file SHA-256.
5. Decode as strict UTF-8.
6. Parse JSON while rejecting duplicate object keys.
7. Reject `NaN`, `Infinity`, and `-Infinity`.
8. Require a top-level mapping.
9. Canonically serialize the parsed object with `witness_canonical_json_v0_1`.
10. Require canonical bytes to equal the loaded bytes exactly.
11. Require the top-level envelope hash field to equal the frozen payload SHA-256.
12. Recompute the payload hash and require exact equality.
13. Call `verifier.validate_stream_envelope(...)`.
14. Require its result to be valid.
15. Independently require every frozen structural identity from §8.

Any failure is a pre-contact refusal.

The in-memory object produced from these exact loaded bytes is the only object permitted to reach the freezer.

---

## 10. Pre-contact refusal order

Before calling the freezer, the runner shall check:

```text
1. no CLI arguments
2. final output directory absent
3. staging output directory absent
4. repository root valid
5. branch is main
6. HEAD resolves exactly
7. origin/main resolves and equals HEAD
8. tracked and untracked working tree clean
9. runner path ownership valid
10. verifier/serializer/freezer paths exact
11. source Git blob identities exact
12. local source bytes equal committed bytes
13. verifier local-configuration precheck valid
14. input path exact
15. input is a non-symlink regular file
16. input byte count exact
17. whole-file input hash exact
18. input canonical JSON valid
19. payload hash exact
20. frozen stream structure exact
```

No staging directory shall be created before these checks complete.

A refusal shall write a concise diagnostic to stderr, return exit code `2`, publish nothing, create no staging directory, and leave the input untouched.

---

## 11. Staging reservation

After all pre-contact checks pass, the runner shall atomically create:

```text
research/brainvision/results/
  .algebraic_n64_primary_v0_1_freeze_v0_1.staging/
```

Creation must fail if the path appeared after the initial absence check. A pre-existing or concurrently created staging path is a refusal and must not be deleted automatically.

The staging directory is a concurrency guard, crash marker, rerun blocker, and post-contact evidence-retention location.

---

## 12. Sole authoritative freezer call

The runner shall contain exactly one call site to:

```python
freezer.freeze_with_replay(
    candidate_stream_envelope,
    repository_commit_identity=resolved_head_commit,
    source_paths=explicit_source_paths,
)
```

It shall call that operation at most once per process.

It shall never call `freezer.freeze(...)`, directly invoke candidate/family verification, or perform an outer replay.

---

## 13. Freezer-call exception handling

If the freezer raises before returning a result:

```text
exit code = 1
no canonical freeze-result artifact exists
stderr records FREEZER_CALL_EXCEPTION
```

The runner shall never retry automatically. Empty staging may be cleaned; staging containing evidence bytes must be retained.

---

## 14. Returned-result validation

The first gate is canonical serializability of the exact returned object.

If the returned object is not canonically serializable, no canonical freeze-result artifact shall be published.

If the returned object is canonically serializable, the runner shall preserve those exact canonical bytes. It
shall then validate whether the object is a structurally valid `freeze_result` envelope whose payload hash
recomputes correctly and whose payload satisfies the required `PRIMARY_V0_1` fields.

The runner must require:

```text
schema_name = brainvision_witness_freeze_result
schema_version = 0.1
verification_mode = PRIMARY_CANDIDATE_N64
N = 64
candidate_stream_sha256 = frozen input payload hash
candidate_count = 20000
terminal_stream_status = budget_exhausted
authoritative_operation = True
resource_policy_status = UNBOUNDED_BY_V0_1_SPECIFICATION
replay_record present
replay_record.byte_identical is a strict boolean
family_frozen is a strict boolean
```

The result must bind the same source paths and source SHA-256 identities established before contact.

On `family_frozen = True`, require byte-identical replay, no failure record, a valid family manifest, matching repository commit identity, matching stream hash, and exactly three accepted indices and certificates.

On `family_frozen = False`, require `family_manifest = null` and a failure record.

A structurally valid positive or valid-negative result exits `0`.

A canonical execution-invalid freezer result exits `1`.

A canonically serializable but runner-invalid result is retained and published with runner-validation failure
diagnostics and exits `1`.

An unserializable return cannot be published as canonical evidence.

---

## 15. Mathematical outcome classes

A positive result establishes only that the committed greedy selector assembled a valid K=3 family under the committed verifier and replay/self-check contract.

A valid mathematical negative is any non-execution-invalid freezer failure produced under the committed
greedy semantics, including but not limited to `FAMILY_NOT_FREEZABLE`. It is not a runner failure. It means only
that the greedy, non-backtracking first-fit scan did not freeze a family under its exact semantics. It does not
establish that no valid triple exists elsewhere in the 20,000-record stream or in the complete generator
domain.

Execution-invalid codes include:

```text
CANDIDATE_STREAM_INVALID
CANDIDATE_STREAM_HASH_MISMATCH
CANDIDATE_N_MODE_INVALID
SERIALIZATION_FAILURE
VERIFIER_CONFIGURATION_INVALID
FORBIDDEN_IMPORT_DETECTED
HASH_IDENTITY_FAILURE
VERIFIER_INTERNAL_DISAGREEMENT
VERIFIER_REGRESSION_FAILURE
REPLAY_MISMATCH
```

Canonical execution-invalid results shall be retained and published but exit `1`.

---

## 16. Output paths

Final directory:

```text
research/brainvision/results/
  algebraic_n64_primary_v0_1_freeze_v0_1/
```

Staging directory:

```text
research/brainvision/results/
  .algebraic_n64_primary_v0_1_freeze_v0_1.staging/
```

Exact final artifact set:

```text
algebraic_n64_primary_v0_1_freeze_result.json
algebraic_n64_primary_v0_1_freeze_summary.txt
```

No separate family-manifest file shall be extracted; it remains embedded in the freeze-result envelope.

---

## 17. Canonical freeze-result artifact

The result file shall contain exactly:

```python
cjson.canonical_json_bytes(returned_freeze_result_envelope)
```

It shall have no trailing newline and no runner-added fields, timestamps, durations, host identity, or absolute paths.

---

## 18. Human summary

The UTF-8/LF summary is operator convenience only. It shall report the runner identity, governing specification, resolved commit, repository agreement, input path/size/hashes, source paths/hashes, result payload and whole-file hashes, manifest/ledger hashes, replay status, family status, accepted indices, failure information, runner validation failures, and published artifact set.

It shall state:

```text
freezer invoked = True
outer replay performed = False
PsiTRS invoked = False
descriptors invoked = False
scientific interpretation performed = False
```

For a negative outcome it shall explicitly preserve the greedy/non-backtracking limitation.

---

## 19. Publication protocol

All files shall be completed in staging using exclusive binary creation. The staged filenames must equal the exact two-file set. Publication is one rename from staging to final within the same parent directory.

The runner shall never overwrite an existing final directory, staging directory, or output file.

---

## 20. Failure retention

Before freezer contact, no evidence exists and empty staging may be removed.

After freezer contact, no automatic retry is permitted. Staging containing any evidence bytes shall be retained. Complete staging shall be retained after rename failure. A successfully published final directory shall never be rolled back, even if stdout mirroring fails.

---

## 21. Exit contract

```text
0
Complete two-file publication with either family_frozen=True or a valid
mathematical negative under the committed greedy semantics.

1
Runner failure, malformed returned result, execution-invalid freezer result,
serialization failure, I/O/publication failure, or post-publication stdout failure.

2
Pre-contact refusal, including argument, path, repository, source identity,
cleanliness, or input identity failure.
```

Exit `0` does not imply a family was frozen. The authoritative outcome is in `freeze_result.family_frozen` and `freeze_result.failure_record`.

---

## 22. Stdout and stderr

On successful publication, stdout mirrors the summary exactly. Normal mathematical negatives do not produce stderr merely because no family froze.

Stderr is reserved for refusals, runner failures, execution-invalid outcomes, publication problems, retained-staging diagnostics, and post-publication stdout failures.

No progress meter, elapsed time, or periodic status output is specified.

---

## 23. Required tests

All tests must use temporary repositories, inputs, and result roots. The real retained stream and real results root must never be accessed.

An autouse fixture shall guard both `freeze_with_replay` and `freeze`; individual tests may explicitly stub only `freeze_with_replay`.

AST tests must prove:

```text
exactly one freeze_with_replay call site
zero freeze call sites
zero verify_candidate call sites
zero verify_family call sites
explicit repository_commit_identity
explicit source_paths
no outer replay
```

Tests shall cover CLI refusal, repository and source provenance failures, all input identity/JSON failures, input immutability, positive and valid-negative publication, execution-invalid publication, malformed/unserializable returns, freezer exception/no retry, staging retention, rename failure, stdout failure after publication, and prevention of real-path access.

Focused test target:

```bat
python -m pytest -q ^
  tests\research\test_brainvision_run_algebraic_n64_primary_freeze_v0_1.py
```

No test may execute the real 20,000-record freezer operation.

---

## 24. Benchmark sequencing decision

The benchmark shall occur after runner implementation and focused review but before full-stream execution authorization.

It requires a separate docs-only specification and authorization. It shall not invoke the authoritative runner, freeze a family, publish an authoritative result, consume later execution authorization, claim a complete-stream result, or alter the candidate stream.

---

## 25. Immutable project boundaries

The implementation and tests must not modify or contact:

```text
research/brainvision/psi_trs.py
research/brainvision/run_n64_falsifier_v0_1.py
torment_service/kernel/
torment_service/memory_kernel.py
torment_service/fabric.py
```

No live capture, PsiTRS, descriptors, SAG, falsifier evaluation, production services, memory integration, prompt integration, or action integration is allowed.

The retained candidate stream remains ignored local evidence and must never be committed.

---

## 26. Implementation acceptance criteria

Implementation may be accepted only when focused review confirms:

```text
no witness mathematics in runner
all provenance checks precede freezer contact
exact retained bytes bound
source bytes bound to governing baseline
resolved full HEAD passed explicitly
source_paths passed explicitly
freeze_with_replay called exactly once
freeze never called
no outer replay
atomic never-overwriting publication
post-contact evidence retained on failure
tests cannot contact the real freezer
tests cannot touch real result paths
negative language preserves greedy limitation
```

---

## 27. Disposition

```text
A. FREEZER_RUNNER_IMPLEMENTATION_SPECIFICATION_ACCEPTED
```

The focused adversarial review is complete and all required corrections have been applied.

This accepts the specification as the governing contract for a later implementation. It does not itself authorize implementation, benchmark execution, freezer execution, or scientific inference.

---

## 28. Authority state

```text
DOCUMENTATION_AUTHORIZED = True
FREEZER_RUNNER_SPECIFICATION_DRAFTED = True
FREEZER_RUNNER_SPECIFICATION_ACCEPTED = True

FREEZER_RUNNER_IMPLEMENTATION_AUTHORIZED = False
FREEZER_RUNNER_IMPLEMENTED = False

FREEZER_BENCHMARK_SPECIFIED = False
FREEZER_BENCHMARK_AUTHORIZED = False
FREEZER_BENCHMARK_EXECUTED = False

FREEZER_INVOCATION_ON_GENERATOR_OUTPUT_AUTHORIZED = False
N64_WITNESS_FAMILY_FREEZE_AUTHORIZED = False
N64_WITNESS_FAMILY_FROZEN = False

PsiTRS_EVALUATION_AUTHORIZED = False
SCIENTIFIC_INFERENCE_AUTHORIZED = False
```

---

## 29. Conclusion

The candidate stream, verifier, greedy selector, family verifier, replay gate, self-checks, and manifest construction already exist.

The missing component is a narrow operator runner that binds the exact repository/source/input state, calls `freeze_with_replay` once, publishes the returned result safely, distinguishes runner success from mathematical success, and preserves evidence without retrying expensive work.

No mathematical route is reopened and no Brainvision behavior is claimed.

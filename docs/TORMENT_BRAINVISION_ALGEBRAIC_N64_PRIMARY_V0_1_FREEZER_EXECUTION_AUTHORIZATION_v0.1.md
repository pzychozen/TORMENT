# TORMENT Brainvision Algebraic N=64 PRIMARY_V0_1 Authoritative Freezer Execution Authorization v0.1

## 0. Decision

```text
A. AUTHORIZE EXACT ONE-RUN AUTHORITATIVE RETAINED-STREAM FREEZER EXECUTION
```

This document authorizes exactly one operator-controlled execution of the committed algebraic N=64 `PRIMARY_V0_1` freezer runner over the exact retained 20,000-record candidate stream, under the repository, source, input, selection, replay, publication, failure-retention, and interpretation boundaries below.

This document is:

```text
docs-only
non-executing during preparation
offline
quarantined
non-production
descriptor-blind
```

Preparing, reviewing, committing, or pushing this document does not itself invoke the verifier or freezer.

This authorization becomes operational only after this document is committed and pushed on `main`, with:

```text
HEAD == origin/main
working tree clean
all frozen source identities unchanged
```

It does not authorize:

```text
a verifier-cost benchmark rerun
candidate-generator execution
candidate-stream regeneration
candidate-stream mutation
direct freezer-module invocation
direct verifier invocation
an alternative selector
backtracking or exhaustive family search
a retry after authoritative freezer contact
PsiTRS evaluation
N64 falsifier execution
descriptor or SAG execution
prerecorded operational-harness execution
live capture
production integration
production-kernel modification
scientific inference
a perception, vision, or temporal-order claim
```

---

## 1. Governing documents and completed prerequisite

Governing documents:

```text
docs/TORMENT_BRAINVISION_ALGEBRAIC_N64_PRIMARY_V0_1_FREEZER_INVOCATION_PROTOCOL_v0.1.md

docs/TORMENT_BRAINVISION_ALGEBRAIC_N64_PRIMARY_V0_1_FREEZER_RUNNER_IMPLEMENTATION_SPECIFICATION_v0.1.md

docs/TORMENT_BRAINVISION_INDEPENDENT_DESCRIPTOR_BLIND_HIGHER_ORDER_WITNESS_FAMILY_IMPLEMENTATION_SPECIFICATION_v0.1.md

docs/TORMENT_BRAINVISION_INDEPENDENT_HIGHER_ORDER_WITNESS_VERIFIER_AND_FREEZE_INFRASTRUCTURE_IMPLEMENTATION_SPECIFICATION_v0.1.md
```

The governing specifications are accepted and are not amended by this authorization.

Completed engineering prerequisite:

```text
docs/TORMENT_BRAINVISION_ALGEBRAIC_N64_PRIMARY_V0_1_VERIFIER_COST_BENCHMARK_FINDINGS_v0.1.md
```

Benchmark findings commit:

```text
c754058bd8eddf953d81bc9514ea709747b9ee86
```

Recorded benchmark status:

```text
BENCHMARK_COMPLETE
32 sampled verify_candidate calls completed
sampled pass-to-pass verifier outputs byte-identical
```

Recorded two-pass verifier-component projection:

```text
overall center:
approximately 29.005 minutes

PREFIX_8 sensitivity:
approximately 23.281 minutes

SPREAD_8 sensitivity:
approximately 34.730 minutes
```

These figures are engineering projections only.

They are not:

```text
measured authoritative freezer runtime
a runtime guarantee
a family-existence result
a freezer-execution authorization
```

The verifier-cost benchmark authorization is consumed.

The benchmark must not be rerun under this authorization.

---

## 2. Reviewed repository baseline

This authorization was prepared against:

```text
branch:
main

reviewed baseline commit:
c754058bd8eddf953d81bc9514ea709747b9ee86

reviewed baseline subject:
docs(research): record algebraic N64 verifier benchmark
```

The reviewed baseline is not necessarily the execution `HEAD`.

The execution `HEAD` will be the later docs-only commit containing this authorization document.

The committed runner resolves the full execution `HEAD` dynamically and passes it to the freezer as:

```python
repository_commit_identity=resolved_head_commit
```

Therefore:

```text
the authorization commit identity must not be guessed or precomputed
the full authorization commit must be recorded after commit and push
the published positive family manifest must bind that exact execution HEAD
```

---

## 3. Accepted implementation and source identities

### 3.1 Freezer-runner implementation

Implementation commit:

```text
34d12b0ccf5914bd15578f70cbb047c1b23bab9e
```

Commit subject:

```text
research(brainvision): implement algebraic N64 freezer runner
```

Runner path:

```text
research/brainvision/run_algebraic_n64_primary_freeze_v0_1.py
```

Current runner Git blob identity:

```text
cad8af6bdd133c9e84e85332c6ca5cefd566b43a
```

Runner identity:

```text
RUNNER_NAME = run_algebraic_n64_primary_freeze_v0_1
RUNNER_VERSION = 0.1
```

Runner-test path:

```text
tests/research/test_brainvision_run_algebraic_n64_primary_freeze_v0_1.py
```

Current runner-test Git blob identity:

```text
cf0e38b3fe7fa3af27e7d4e4bf751313d96c736b
```

### 3.2 Mathematical and serialization sources

Freezer path:

```text
research/brainvision/witness_family_freeze_v0_1.py
```

Freezer Git blob identity:

```text
cf4ea57890fbbbdf9593879cf648b84c6c68d9b0
```

Verifier path:

```text
research/brainvision/witness_family_verifier_v0_1.py
```

Verifier Git blob identity:

```text
db1e1fa606bdbf17fda62cd998aeb2a29d47d59a
```

Canonical serializer path:

```text
research/brainvision/witness_canonical_json_v0_1.py
```

Canonical serializer Git blob identity:

```text
6eb382b314325033443fc7331cae5050ee6e6ed2
```

### 3.3 Docs-only authorization-commit boundary

The commit containing this authorization must add exactly one documentation file.

It must not alter:

```text
freezer runner
freezer-runner tests
freezer
verifier
canonical serializer
candidate generator
candidate-generator runner
verifier-cost benchmark
verifier-cost benchmark tests
retained candidate stream
PsiTRS
N64 falsifier
descriptors
SAG
prerecorded analysis tooling
torment_service
production-kernel files
```

Any source-identity change requires a new review and a new authorization decision.

---

## 4. Frozen retained input

Exact path:

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
candidate_generation_index sequence = exactly 0..19999
```

The retained stream is ignored, read-only local evidence.

This authorization permits the committed runner to read it for the sole authorized operation.

It does not permit:

```text
rewriting
normalizing
reformatting
reserializing
renaming
relocating
copying as a replacement input
truncating
appending
editing
regenerating
committing
pushing
```

The runner must refuse before freezer contact if any frozen input identity differs.

---

## 5. Exact authorized operation

The complete authorized operator command is:

```bat
python research\brainvision\run_algebraic_n64_primary_freeze_v0_1.py
```

The command must be issued:

```text
from the authoritative Windows repository root
in the torment conda environment
using python
exactly once
with no command-line arguments
with no environment-variable override
```

No alternative invocation is authorized.

In particular, this authorization does not permit:

```text
python -c direct freezer calls
interactive imports followed by freezer calls
calling freeze_with_replay from another script
calling freeze(...)
calling verify_candidate directly
calling verify_family directly
changing the input path
changing the output path
changing K
changing N
setting a prefix or budget
setting a timeout
setting worker count or parallelism
resuming a previous operation
overwriting or merging prior evidence
```

---

## 6. Internal operation authorized through the runner

The committed runner may perform its frozen pre-contact validation sequence, including:

```text
repository-root ownership checks
main-branch check
HEAD resolution
origin/main agreement
clean-tree check
runner path ownership
source blob and local-byte binding
verifier local-configuration validation
exact input file loading
whole-file input hashing
strict UTF-8 and JSON validation
canonical-byte validation
payload-hash validation
stream-envelope validation
frozen structural validation
staging-directory reservation
```

The pre-contact calls:

```python
verifier.validate_local_configuration(...)
verifier.validate_stream_envelope(...)
```

are authorized only as non-candidate-evaluating provenance and container checks.

They do not authorize witness evaluation outside the freezer.

After every pre-contact check passes, the runner is authorized to enter its sole authoritative freezer call exactly once:

```python
freezer.freeze_with_replay(
    candidate_stream_envelope,
    repository_commit_identity=resolved_head_commit,
    source_paths=source_paths,
)
```

Through this single committed call, the freezer is authorized to perform its existing frozen behavior:

```text
configuration self-check
source-independence self-check
regression self-check
two internal deterministic freeze passes
candidate verification over retained records
incremental family eligibility
greedy first-K selection
family verification when K=3 is reached
internal canonical replay comparison
decision-ledger construction
family-manifest construction when positive
canonical freeze-result construction
```

The retained-stream scan remains:

```text
authoritative stream order
first-fit
greedy
K = 3
non-backtracking
non-exhaustive
```

The number of retained-stream candidate verifications is outcome-dependent:

```text
best retained-stream path:
3 records per internal pass
6 retained-stream verify_candidate calls total

full retained-stream path:
20,000 records per internal pass
40,000 retained-stream verify_candidate calls total
```

The committed fixed regression self-check may perform its own internal fixture checks in addition to the retained-stream calls.

No third internal pass, outer replay, retry, backtracking, candidate-triple enumeration, selector substitution, or exhaustive search is authorized.

---

## 7. Required pre-execution state

Immediately before execution, all of the following must hold:

```text
branch = main
HEAD = origin/main
working tree clean, including ordinary untracked files
authorization document committed and pushed
authorization commit is docs-only
runner blob = cad8af6bdd133c9e84e85332c6ca5cefd566b43a
runner-test blob = cf0e38b3fe7fa3af27e7d4e4bf751313d96c736b
freezer blob = cf4ea57890fbbbdf9593879cf648b84c6c68d9b0
verifier blob = db1e1fa606bdbf17fda62cd998aeb2a29d47d59a
serializer blob = 6eb382b314325033443fc7331cae5050ee6e6ed2
retained input path and identity exact
final output directory absent
staging output directory absent
```

The exact full execution `HEAD` must be captured after this authorization is committed and pushed.

That exact commit must later match the repository commit identity recorded in any positive family manifest.

The freezer must not be run:

```text
while the authorization document is untracked
while the authorization document is staged but uncommitted
before the authorization commit is pushed
while HEAD differs from origin/main
with a dirty working tree
after changing any frozen source
when either output directory already exists
```

---

## 8. One-run authority and consumption semantics

### 8.1 Pre-contact refusal

A runner exit code `2` is a pre-contact refusal.

The authorization may remain unconsumed only when it is established that:

```text
freeze_with_replay call count = 0
retained candidate verify_candidate calls = 0
family verification calls = 0
final publication created = False
staging contains authorized evidence bytes = False
```

The runner’s pre-contact provenance functions:

```text
validate_local_configuration
validate_stream_envelope
```

do not consume the authorization because they evaluate no retained witness candidate.

A later attempt under the same authorization is permitted only after:

```text
the refusal reason is understood
no source or authorization semantic is changed
no freezer contact occurred
no result evidence exists
the exact required pre-execution state is restored
```

Any required code, source, input, selector, or authorization change closes this authority and requires a new docs-only decision.

### 8.2 Consumption threshold

The authorization is consumed at the moment the committed runner enters:

```python
freezer.freeze_with_replay(...)
```

Once that call begins, the authorization is consumed regardless of:

```text
exit code
freezer exception
self-check failure
candidate-verification failure
replay mismatch
serialization failure
malformed returned result
publication failure
rename failure
stdout failure
positive result
valid negative result
absence of publishable result bytes
```

### 8.3 Post-contact failure

After the consumption threshold:

```text
do not retry
do not invoke the runner again
do not invoke the freezer directly
do not delete retained evidence
do not edit retained evidence
do not replace the input
do not regenerate the stream
```

Retain the final or staging evidence exactly as the committed runner leaves it.

When no canonical evidence bytes exist and the runner removes an empty staging directory according to its committed contract:

```text
record the absence
record stderr and exit code
do not recreate synthetic evidence
do not retry
```

Any second post-contact attempt requires a new docs-only authorization.

### 8.4 Successful completion

A complete positive or valid-negative publication consumes the authorization.

After successful publication:

```text
do not rerun
do not overwrite
do not rename the result directory
do not edit either output file
do not extract and replace the embedded family manifest
```

---

## 9. Exact output boundary

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

Exact successful final file set:

```text
algebraic_n64_primary_v0_1_freeze_result.json

algebraic_n64_primary_v0_1_freeze_summary.txt
```

The result JSON must contain exactly the committed freezer’s canonical freeze-result envelope.

The runner must not add:

```text
timestamps
durations
host identity
absolute paths
runner-only metadata
scientific interpretation
```

No separate family-manifest file is authorized.

A positive family manifest remains embedded inside the canonical freeze-result envelope.

The summary is operator convenience only and is not a replacement for canonical freezer evidence.

Publication must preserve the committed protocol:

```text
exclusive file creation in staging
exact two-file set
single staging-to-final rename
no overwrite
no merge
no automatic rollback of published final evidence
```

---

## 10. Exit handling

Runner exit contract:

```text
exit 0:
complete two-file publication with either:
  family_frozen = True
or:
  a structurally valid mathematical negative under the committed greedy semantics

exit 1:
post-contact runner failure, freezer exception, execution-invalid result,
malformed or unserializable result, I/O failure, publication failure,
rename failure, or post-publication stdout failure

exit 2:
pre-contact refusal
```

Exit `0` does not itself mean that a family was frozen.

The authoritative mathematical status is recorded in:

```text
freeze_result.family_frozen
freeze_result.failure_record
freeze_result.accepted_candidate_indices
freeze_result.family_manifest
freeze_result.replay_record
```

A published final directory remains authoritative evidence even when the process exits `1` because stdout mirroring failed after publication.

---

## 11. Required operator capture

### 11.1 Before execution

Record:

```bat
git status --short --branch

git rev-parse HEAD

git rev-parse origin/main

git rev-parse HEAD:research/brainvision/run_algebraic_n64_primary_freeze_v0_1.py

git rev-parse HEAD:tests/research/test_brainvision_run_algebraic_n64_primary_freeze_v0_1.py

git rev-parse HEAD:research/brainvision/witness_family_freeze_v0_1.py

git rev-parse HEAD:research/brainvision/witness_family_verifier_v0_1.py

git rev-parse HEAD:research/brainvision/witness_canonical_json_v0_1.py
```

Confirm output-path absence:

```bat
if exist research\brainvision\results\algebraic_n64_primary_v0_1_freeze_v0_1 (
  echo FINAL_DIRECTORY_EXISTS
) else (
  echo FINAL_DIRECTORY_ABSENT
)

if exist research\brainvision\results\.algebraic_n64_primary_v0_1_freeze_v0_1.staging (
  echo STAGING_DIRECTORY_EXISTS
) else (
  echo STAGING_DIRECTORY_ABSENT
)
```

Record the retained input’s whole-file identity:

```bat
for %I in (research\brainvision\results\algebraic_n64_primary_v0_1\algebraic_n64_primary_v0_1_candidate_stream.json) do @echo INPUT_SIZE=%~zI

certutil -hashfile research\brainvision\results\algebraic_n64_primary_v0_1\algebraic_n64_primary_v0_1_candidate_stream.json SHA256
```

Expected:

```text
INPUT_SIZE=6421010

SHA-256:
00a816364ddcfc9d06dc8ce1225f58bca013e96a8914ff1eb665004b39ed949b
```

Do not execute if any pre-execution identity differs.

### 11.2 Exact single execution

Run exactly once:

```bat
python research\brainvision\run_algebraic_n64_primary_freeze_v0_1.py
```

Capture the exit code immediately:

```bat
set FREEZER_EXIT_CODE=%ERRORLEVEL%

echo FREEZER_EXIT_CODE=%FREEZER_EXIT_CODE%
```

Do not issue the runner command again.

### 11.3 After execution

Record repository state:

```bat
git status --short --branch
```

Inspect both possible evidence locations without modifying them:

```bat
dir /a research\brainvision\results\algebraic_n64_primary_v0_1_freeze_v0_1

dir /a research\brainvision\results\.algebraic_n64_primary_v0_1_freeze_v0_1.staging
```

When final publication exists, hash both final files:

```bat
certutil -hashfile research\brainvision\results\algebraic_n64_primary_v0_1_freeze_v0_1\algebraic_n64_primary_v0_1_freeze_result.json SHA256

certutil -hashfile research\brainvision\results\algebraic_n64_primary_v0_1_freeze_v0_1\algebraic_n64_primary_v0_1_freeze_summary.txt SHA256
```

When final publication does not exist but retained staging exists, inspect and hash every retained staging file instead.

When neither exists after a post-contact failure:

```text
record that no publishable evidence bytes were produced
retain stdout and stderr
do not retry
```

---

## 12. Result adjudication contract

### 12.1 Positive authoritative freeze

A positive result requires:

```text
family_frozen = True
authoritative_operation = True
internal replay byte_identical = True
valid embedded family manifest
exactly K = 3 accepted pair certificates
exactly three accepted candidate indices
repository commit identity = exact authorization execution HEAD
candidate-stream payload identity exact
frozen source identities exact
failure_record = null
```

Permitted description:

```text
The frozen offline authoritative greedy freezer selected and verified
a K=3 witness family from the exact retained PRIMARY_V0_1 stream under
the recorded source identities, stream order, and replay policy.
```

A positive result does not establish:

```text
Brainvision behavior
PsiTRS usefulness
visual perception
temporal-order detection
production readiness
optimality of the selected family
uniqueness of the selected family
exhaustiveness over all possible families
```

### 12.2 Bounded greedy negative

A valid negative means only:

```text
the frozen greedy non-backtracking first-fit procedure did not freeze
a K=3 family under the exact retained stream order and policy
```

It does not establish:

```text
that no valid triple exists elsewhere in the retained stream
that a different first acceptance would not succeed
that backtracking would fail
that exhaustive triple search would fail
that the complete generator domain lacks a valid family
```

### 12.3 Execution-invalid result

An execution-invalid result is operational evidence only.

It authorizes no conclusion about family existence or absence.

Examples include:

```text
configuration invalid
forbidden import detected
hash identity failure
verifier internal disagreement
regression failure
replay mismatch
serialization failure
```

### 12.4 Publication or runner failure

A publication or runner failure does not authorize a second attempt.

Any retained final or staging evidence must be preserved exactly.

### 12.5 Pre-contact refusal

A pre-contact refusal produces no freezer result.

It supports no mathematical conclusion.

Authority may remain available only under §8.1.

---

## 13. Closed boundaries and immutable production surface

This authorization does not modify or permit modification of:

```text
research/brainvision/psi_trs.py
research/brainvision/run_n64_falsifier_v0_1.py
torment_service/kernel/
torment_service/memory_kernel.py
torment_service/fabric.py
```

The production TORMENT memory kernel remains immutable.

The operation must not contact:

```text
production memory functionality
prompt construction
model context
caller ownership
actions or tools
live models
network services
camera or screen capture
live sensors
runtime integration
```

Brainvision remains:

```text
offline
quarantined under research/brainvision
non-runtime
non-production
descriptive-only
```

Preserve:

```text
FORMAL_HOLD = active
Mode_0 = active
```

---

## 14. Authority state

After this document is committed and pushed under the required synchronized state:

```text
DOCUMENTATION_AUTHORIZED = True

PRIMARY_V0_1_CANDIDATE_STREAM_PRODUCED = True
PRIMARY_V0_1_DOWNSTREAM_FREEZE_ELIGIBLE = True

VERIFIER_COST_BENCHMARK_EXECUTION_AUTHORIZED = consumed
VERIFIER_COST_BENCHMARK_EXECUTED = True
VERIFIER_COST_BENCHMARK_STATUS = BENCHMARK_COMPLETE

AUTHORITATIVE_FREEZER_EXECUTION_AUTHORIZATION_DOCUMENTED = True
AUTHORITATIVE_FREEZER_EXECUTION_AUTHORIZED = True
AUTHORITATIVE_FREEZER_EXECUTION_AUTHORIZATION_COUNT = 1
AUTHORITATIVE_FREEZER_EXECUTED = False

FREEZER_INVOCATION_ON_GENERATOR_OUTPUT_AUTHORIZED = True
N64_WITNESS_FAMILY_FREEZE_AUTHORIZED = True
N64_WITNESS_FAMILY_FROZEN = False

PRIMARY_V0_1_GENERATOR_RERUN_AUTHORIZED = False
VERIFIER_COST_BENCHMARK_RERUN_AUTHORIZED = False
N64_FALSIFIER_RERUN_AUTHORIZED = False

PsiTRS_EVALUATION_AUTHORIZED = False
SCIENTIFIC_INFERENCE_AUTHORIZED = False
PRODUCTION_INTEGRATION_AUTHORIZED = False
KERNEL_MODIFICATION_AUTHORIZED = False
LIVE_CAPTURE_AUTHORIZED = False
```

Once `freeze_with_replay(...)` begins:

```text
AUTHORITATIVE_FREEZER_EXECUTION_AUTHORIZED = consumed
AUTHORITATIVE_FREEZER_EXECUTED = True
```

The final family-frozen status remains determined exclusively by the retained canonical result.

---

## 15. Disposition

```text
A. EXACT ONE-RUN AUTHORITATIVE RETAINED-STREAM FREEZER EXECUTION AUTHORIZED
```

The authorization is operational only after:

```text
this document is accepted
one focused adversarial review finds no blocker
the authorization is committed as the sole changed file
the commit is pushed to main
HEAD == origin/main
the working tree is clean
all frozen identities match
the retained input matches
both output directories are absent
```

Recommended authorization-document path:

```text
docs/TORMENT_BRAINVISION_ALGEBRAIC_N64_PRIMARY_V0_1_FREEZER_EXECUTION_AUTHORIZATION_v0.1.md
```

Recommended commit subject:

```text
docs(research): authorize algebraic N64 freezer execution
```

No freezer execution occurred while preparing this authorization.

No retained candidate was evaluated while preparing this authorization.

No output or staging directory was created while preparing this authorization.

No PsiTRS, falsifier, descriptor, operational-harness, production-service, or production-kernel contact occurred while preparing this authorization.

*End — TORMENT Brainvision Algebraic N=64 PRIMARY_V0_1 Authoritative Freezer Execution Authorization v0.1. Docs-only during preparation. Authorizes exactly one later operator-controlled invocation of the committed freezer runner after synchronized docs-only commit and push. The authority is consumed when the sole `freeze_with_replay` call begins. No post-contact retry, scientific inference, PsiTRS evaluation, production integration, or kernel modification is authorized.*

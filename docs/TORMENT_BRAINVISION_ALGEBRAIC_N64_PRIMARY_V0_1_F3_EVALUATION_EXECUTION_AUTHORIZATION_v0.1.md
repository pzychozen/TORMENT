# TORMENT Brainvision Algebraic N=64 PRIMARY_V0_1 Frozen-Family F3 Evaluation Execution Authorization v0.1

## 0. Decision

```text
A. AUTHORIZE EXACT ONE-RUN FROZEN-FAMILY F3 EVALUATION
```

This document authorizes exactly one operator-controlled execution of the committed frozen-family F3 evaluator runner over the exact immutable K=3 witness family selected at candidate indices `[478, 479, 480]`, under the repository, source, input, reverification, descriptor, pass, replay, publication, failure-retention, consumption, and interpretation boundaries below.

This document is:

```text
docs-only
non-executing during preparation
non-executing during review
non-executing during commit
non-executing during push
offline
quarantined
non-production
```

Preparing, reviewing, committing, or pushing this document does not itself invoke the evaluator, build any feature cache, or call PsiTRS.

This authorization becomes operational only after this document is committed and pushed on `main`, with:

```text
HEAD == origin/main
working tree clean
all frozen source, dependency, and evidence identities unchanged
```

It does not authorize:

```text
direct build_production_feature_cache invocation
direct psi_trs.psi_trs_features invocation
old N64 runner invocation
freezer invocation
candidate-generator invocation
candidate replacement
family replacement
witness reordering based on response
threshold tuning
median substitution
alternate ranking
alternate controls
alternate rotation
partial starts
parallel execution
a third pass
a retry after frozen-witness descriptor contact
scientific inference
a perception, vision, temporal-order, or recursive-time claim
production integration
production-kernel modification
live capture
```

---

## 1. Governing documents and preserved contracts

Governing documents, accepted and not amended by this authorization:

```text
docs/TORMENT_BRAINVISION_ALGEBRAIC_N64_PRIMARY_V0_1_FROZEN_K3_FAMILY_EVIDENCE_AND_F3_EVALUATION_BINDING_v0.1.md

docs/TORMENT_BRAINVISION_ALGEBRAIC_N64_PRIMARY_V0_1_F3_EVALUATOR_IMPLEMENTATION_SPECIFICATION_v0.1.md

docs/TORMENT_BRAINVISION_ALGEBRAIC_N64_PRIMARY_V0_1_F3_EVALUATOR_IMPLEMENTATION_AUTHORIZATION_v0.1.md
```

The frozen-family binding fixes the immutable family, the exact raw supports, the pair order, the F3 response formula, the all-start policy, the complete self-shift reference policy, the zero-tolerance gates, and the preregistered pair and family verdicts. This authorization preserves every one of those contracts without modification.

The implementation specification fixes the module boundary, the identity binding, the preflight, the integer-exact reverification, the descriptor binding, the feature-cache/call-count contract, the pure cache-evaluation interface, the two-pass replay, the canonical schema and serialization, the publication paths, the exit-code contract, and the authority-consumption boundary. This authorization preserves every one of those contracts without modification.

The implementation authorization fixed the exact six authorized files, the descriptor-contact boundary during implementation and testing, and the requirement that the first later production descriptor call on a frozen family member requires a separate docs-only execution authorization. This document is that separate execution authorization.

This authorization amends none of the frozen mathematics. It grants only the single later operator-controlled invocation defined in §8.

---

## 2. Reviewed baseline

This authorization was prepared against the accepted evaluator implementation commit.

```text
branch:
main

accepted implementation commit:
d225a3f3bd3eda8185006d3f386953f119ed6007

accepted implementation subject:
research(brainvision): implement frozen N64 F3 evaluator
```

The reviewed implementation commit is not the execution `HEAD`.

The execution `HEAD` will be the later docs-only commit that adds this authorization document. It will not be the implementation commit.

The committed runner resolves the full execution `HEAD` dynamically and records it in the canonical result payload as:

```text
execution_commit_identity = resolved_head_commit
```

Therefore:

```text
the authorization commit identity must not be guessed or precomputed
the full authorization commit must be captured after commit and push
the canonical result must bind that exact synchronized execution HEAD
```

The runner additionally refuses unless `HEAD == origin/main` before descriptor contact, so the recorded `execution_commit_identity` is the synchronized authorization commit and nothing else.

---

## 3. Six committed implementation identities

The commit that adds this authorization document must add exactly the one new documentation file and must not alter any of the six files below.

### 3.1 Production modules

```text
research/brainvision/algebraic_n64_f3_frozen_identity_v0_1.py

Git blob:
c409c32b4a1e205ddc093e9734ec8292e1fd876c

Raw-byte SHA-256:
332021c77eb5327c6a7098513c125466069026e2fdbc2530606353cd70340487
```

```text
research/brainvision/algebraic_n64_f3_evaluator_v0_1.py

Git blob:
4d6f8db93c8c159e16e54786bfafa3ecd363a0e7

Raw-byte SHA-256:
42f350a4a20157f02f1cffbf8147e5ee696b87a9ec3fa485f1a71088ca93fb41
```

```text
research/brainvision/run_algebraic_n64_f3_evaluation_v0_1.py

Git blob:
f8103c37569f9b1eb3ca19533d0374bd2b80ada9

Raw-byte SHA-256:
505316892cf8b02548da2a4dab6796b7bc70e7d55067076712d3ad10279b0a17
```

### 3.2 Tests

```text
tests/research/test_brainvision_algebraic_n64_f3_frozen_identity_v0_1.py

Git blob:
5bfd3b3c05968aea696629d798830c4e5a4e143f
```

```text
tests/research/test_brainvision_algebraic_n64_f3_evaluator_v0_1.py

Git blob:
1b31dab597b6dfaae228edfef450283cbc3fe2fb
```

```text
tests/research/test_brainvision_run_algebraic_n64_f3_evaluation_v0_1.py

Git blob:
74b31f9d84dfad764846b766a377f4a704d991be
```

The authorization commit must add exactly the new documentation file and must not alter any of these six files.

---

## 4. Frozen dependency identities

The evaluator consumes these files by import and read. Each must remain exactly the reviewed identity.

Exact unchanged descriptor source:

```text
research/brainvision/psi_trs.py

Git blob:
42634cb7c1c3537d3e4e6f907c8a9c19dcddfd4c

Raw-byte SHA-256:
a3b514ef6e098babfa227488272eb38b0ef9cf916b4854e70d8df8f94d1f7fa6
```

Exact unchanged independent verifier:

```text
research/brainvision/witness_family_verifier_v0_1.py

Git blob:
db1e1fa606bdbf17fda62cd998aeb2a29d47d59a

Raw-byte SHA-256:
2d17b775b15174963a8f98e2dcfe4f6b9d25db7c99024846ec52ff8bc3ead94d
```

Exact unchanged canonical serializer:

```text
research/brainvision/witness_canonical_json_v0_1.py

Git blob:
6eb382b314325033443fc7331cae5050ee6e6ed2

Raw-byte SHA-256:
fad2d09a3a75c884e50f3e8cd2e9cce3f976cd8f3b6c931ae74578891f6c1170
```

Any change to any implementation identity in §3 or any dependency identity in §4 closes this authority and requires a new review and a new docs-only authorization.

---

## 5. Frozen evidence identities

The evaluator reads exactly the canonical freezer result, read-only.

Exact canonical freezer-result path:

```text
research/brainvision/results/algebraic_n64_primary_v0_1_freeze_v0_1/
  algebraic_n64_primary_v0_1_freeze_result.json
```

Whole-file SHA-256:

```text
97af61ea4debf9d66146f3e33f035c17c60965c1d9fed0ebbf3d09ead58cbca5
```

Freeze-result payload SHA-256:

```text
35e03a83fee83b7fc13514397e10115b3f6b99f847bf17d20772a0e61376796e
```

Family-manifest SHA-256:

```text
352a49bc8d06a35b41b8783f8a869a1645d93c76ddb91df379492b37106d8151
```

Family-verifier-certificate SHA-256:

```text
416d32bba578856b5122402186860643071070c946829020799138da13ee764e
```

Candidate-stream payload SHA-256:

```text
70763a2ebbf7ea71267553debee2bf79c2ed3b7b0c016d9a903161074e7bf8c5
```

Pair certificate hashes, in exact frozen order:

```text
candidate 478:
51e72030237da850757979588b4c4107de69a6098ce7c9a3559243b5545edf2b

candidate 479:
3b3475fc9bd2264fd17035f62ddbbc03d584a1fa94f5f28db712941f6e683408

candidate 480:
d4bbb7d8d8958cca261728721115de21efa154c50930bf787e4153fcb28ddfd9
```

Bound frozen family identity:

```text
N = 64
K = 3
accepted candidate order = [478, 479, 480]
six members
member weight = 12
```

The freezer result is immutable and read-only.

This authorization does not authorize its rerun, regeneration, editing, renaming, deletion, replacement, or reserialization.

Any change to any evidence identity in §5 closes this authority and requires a new review and a new docs-only authorization.

---

## 6. Completed review and test prerequisites

Focused Codex blocker-closure verdict:

```text
ACCEPT AS-IS
```

Focused F3 suite:

```text
71 passed
```

Wider authoritative Windows research suite:

```text
1435 passed
1 skipped
2 deselected
```

The two deselected tests are known stale global result-path absence assertions outside the six-file F3 implementation boundary:

```text
tests/research/test_brainvision_run_algebraic_n64_primary_freeze_v0_1.py::
test_real_result_paths_are_never_created_by_this_suite

tests/research/test_brainvision_run_algebraic_n64_primary_verifier_cost_benchmark_v0_1.py::
test_real_result_paths_never_created_by_this_suite
```

Those tests incorrectly require already-authorized freezer and verifier-benchmark evidence directories to remain globally absent. They do not assert the absence of the new F3 modules. They do not justify deleting, editing, or weakening any existing authorized evidence, and they are not counted as failures against this authorization. No evidence or source file may be removed to make those stale assertions pass under this document.

These prerequisites are engineering acceptance records only. They are not a family-evaluation result and do not themselves authorize execution.

---

## 7. Required pre-execution state

Immediately before the later invocation, all of the following must hold.

```text
branch = main
HEAD = origin/main
working tree clean, including untracked files
authorization document committed and pushed
authorization commit contains exactly one docs file
all six implementation blob identities exact
all three production-module raw-byte SHA-256 identities exact
PsiTRS blob and raw-byte identities exact
verifier blob and raw-byte identities exact
serializer blob and raw-byte identities exact
freezer-result whole-file identity exact
frozen payload and certificate identities exact
authorization environment gate initially unset
final output directory absent
staging output directory absent
```

Exact final directory:

```text
research/brainvision/results/algebraic_n64_primary_v0_1_f3_evaluation_v0_1/
```

Exact staging directory:

```text
research/brainvision/results/.algebraic_n64_primary_v0_1_f3_evaluation_v0_1.staging/
```

Do not execute when any identity or state differs.

---

## 8. Exact authorized operation

The complete authorized operator sequence is exactly:

```bat
set ALGEBRAIC_N64_F3_EVALUATION_AUTHORIZED=1
python research\brainvision\run_algebraic_n64_f3_evaluation_v0_1.py
```

The sequence must be issued:

```text
from the authoritative Windows repository root
in the torment conda environment
using python, not py
with zero command-line arguments
with no path override
with no threshold override
with no metric override
with no start subset
with no worker override
with no configuration override
with no direct module call
with no interactive call
with no alternate script
exactly one operator invocation
```

No alternative invocation is authorized.

In particular, this authorization does not cover:

```text
direct build_production_feature_cache invocation
direct psi_trs.psi_trs_features invocation
old N64 runner invocation
freezer invocation
generator invocation
candidate replacement
family replacement
threshold tuning
median substitution
alternate ranking
alternate controls
alternate rotation
partial starts
parallel execution
a third pass
a retry after frozen-witness descriptor contact
```

---

## 9. Exact internal evaluation authority

Through the committed runner only, this authorization permits its frozen pre-contact validation sequence:

```text
pre-contact repository validation
source blob and local-byte validation
frozen freezer-result loading
whole-file hash validation
strict UTF-8 and JSON validation
payload and envelope validation
pair-certificate validation
family-certificate validation
independent integer-exact witness reverification
staging-directory reservation
```

These pre-contact operations do not themselves consume the F3 authority, because they do not call PsiTRS on a frozen witness.

After all pre-contact checks pass, this authorization permits at most two fresh complete production passes within the single runner invocation.

For each successfully completed pass:

```text
6 members
2 descriptor variants
64 matched starts
768 completed descriptor calls
```

For a successfully completed two-pass replay:

```text
1536 completed descriptor calls
```

A descriptor exception, raw descriptor schema failure, or nonfinite descriptor value may terminate the current pass before 768 calls complete and may prevent the second pass from beginning. Once the first frozen-witness PsiTRS call has begun, such termination is a consumed post-contact failure. It does not authorize completion through a retry, second invocation, replacement pass, or direct descriptor call.

Therefore:

```text
768 calls per pass and 1536 calls total are exact for a complete successful two-pass replay
fewer calls may be recorded only when a consumed post-contact failure terminates execution early
no third pass or compensating invocation is authorized
```

All response, control, orbit, aggregation, gate, verdict, replay, and serialization mathematics must derive from the feature caches built in those two passes. None of that later mathematics may call PsiTRS.

Bound exact response counts per pass:

```text
384 cross responses
768 identity controls
48,384 nonidentity self-shift responses
```

No third pass, retry, hidden cache rebuild, alternate witness, or alternate start set is authorized.

---

## 10. Consumption boundary

The semantic consumption threshold is exactly:

```text
The one-run authority is consumed when the first real production call to
psi_trs.psi_trs_features(...)
begins on any frozen family member at any matched start.
```

Before that first descriptor call, a runner refusal does not consume the authority.

The following are pre-contact refusals:

```text
gate absent or incorrect
unexpected CLI arguments
final path exists
staging path exists before invocation
repository root invalid
branch not main
HEAD != origin/main
dirty working tree
source identity failure
freezer-result identity failure
frozen evidence validation failure
witness reverification failure
staging reservation failure before production-pass entry
```

A later attempt under the same authorization is permissible only when it is definitively established that:

```text
zero frozen-witness PsiTRS calls began
no canonical result exists
no retained staging evidence from descriptor contact exists
the refusal cause is understood
no source or authorization semantic changed
the exact required state is restored
```

If execution reaches production-pass entry and it is not possible to prove that zero PsiTRS calls began, treat the authority conservatively as consumed.

After the first real frozen-witness PsiTRS call begins, the authority remains consumed regardless of:

```text
descriptor exception
wrong descriptor schema
nonfinite descriptor value
incomplete cache
response invalidity
identity-control failure
normalization failure
gate-input failure
pair failure
family failure
replay mismatch
serialization failure
publication failure
rename failure
stdout failure
process interruption
positive result
mixed result
strong negative result
invalid evaluation
absence of final evidence
```

After consumption:

```text
do not rerun
do not retry
do not invoke PsiTRS directly
do not invoke the evaluator directly
do not replace witnesses
do not tune thresholds
do not delete evidence
do not edit evidence
do not manufacture replacement evidence
```

Any second post-contact attempt requires a new docs-only authorization.

---

## 11. Exact output and publication boundary

Final successful file set:

```text
algebraic_n64_primary_v0_1_f3_evaluation_result.json
algebraic_n64_primary_v0_1_f3_evaluation_summary.txt
```

Publication must preserve the committed runner contract exactly:

```text
exclusive staging creation
exact two-file staged set
canonical result envelope
deterministic two-pass replay record
single staging-to-final rename
no overwrite
no merge
no rollback of published final evidence
```

The summary is operator convenience only.

The canonical JSON result is authoritative.

No timestamps, durations, absolute paths, host names, scientific interpretation, or extra files may be added outside the committed runner contract.

---

## 12. Verdict interpretation

Preserve the exact frozen family outcomes:

```text
3 passing pairs:
STRONG_FAMILY_FALSIFIER_SUCCESS

1 or 2 passing pairs:
VALID_MIXED_FAMILY_RESULT

0 passing pairs with all pairs valid:
STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY

any validity failure:
INVALID_FAMILY_EVALUATION
```

A valid result may describe only the behavior of this exact frozen family under this exact offline PsiTRS F3 contract.

It must not be described as proof of:

```text
higher-order perception
temporal-order perception
true vision
spatial continuity
recursive-time mechanism
scientific significance
physics emergence
production readiness
generalization beyond the frozen family
```

An invalid result authorizes no pair or family hypothesis conclusion.

Even `STRONG_FAMILY_FALSIFIER_SUCCESS` would mean only that all three frozen pairs passed the exact preregistered F3 contract under the exact evaluator, descriptor, environment, self-shift references, and zero-tolerance comparison rules.

---

## 13. Operator capture

All commands are Command Prompt syntax. Use `python`, not `py`. Do not introduce PowerShell.

### 13.1 Final pre-run repository and identity capture

```bat
git status --short --branch

git rev-parse HEAD

git rev-parse origin/main

git rev-parse HEAD:research/brainvision/algebraic_n64_f3_frozen_identity_v0_1.py
git rev-parse HEAD:research/brainvision/algebraic_n64_f3_evaluator_v0_1.py
git rev-parse HEAD:research/brainvision/run_algebraic_n64_f3_evaluation_v0_1.py
git rev-parse HEAD:tests/research/test_brainvision_algebraic_n64_f3_frozen_identity_v0_1.py
git rev-parse HEAD:tests/research/test_brainvision_algebraic_n64_f3_evaluator_v0_1.py
git rev-parse HEAD:tests/research/test_brainvision_run_algebraic_n64_f3_evaluation_v0_1.py

git rev-parse HEAD:research/brainvision/psi_trs.py
git rev-parse HEAD:research/brainvision/witness_family_verifier_v0_1.py
git rev-parse HEAD:research/brainvision/witness_canonical_json_v0_1.py

certutil -hashfile research\brainvision\algebraic_n64_f3_frozen_identity_v0_1.py SHA256
certutil -hashfile research\brainvision\algebraic_n64_f3_evaluator_v0_1.py SHA256
certutil -hashfile research\brainvision\run_algebraic_n64_f3_evaluation_v0_1.py SHA256
certutil -hashfile research\brainvision\psi_trs.py SHA256
certutil -hashfile research\brainvision\witness_family_verifier_v0_1.py SHA256
certutil -hashfile research\brainvision\witness_canonical_json_v0_1.py SHA256

certutil -hashfile research\brainvision\results\algebraic_n64_primary_v0_1_freeze_v0_1\algebraic_n64_primary_v0_1_freeze_result.json SHA256
```

Expected identities are those recorded in §3, §4, and §5. Do not execute if any pre-execution identity differs.

### 13.2 Authorization-gate state check before setting it

```bat
if defined ALGEBRAIC_N64_F3_EVALUATION_AUTHORIZED (
  echo GATE_ALREADY_SET=[%ALGEBRAIC_N64_F3_EVALUATION_AUTHORIZED%]
) else (
  echo GATE_UNSET_GOOD
)
```

The gate must read `GATE_UNSET_GOOD` before §13.4. Do not proceed if it is already set.

### 13.3 Final and staging path absence

```bat
if exist research\brainvision\results\algebraic_n64_primary_v0_1_f3_evaluation_v0_1 (
  echo FINAL_DIRECTORY_EXISTS
) else (
  echo FINAL_DIRECTORY_ABSENT
)

if exist research\brainvision\results\.algebraic_n64_primary_v0_1_f3_evaluation_v0_1.staging (
  echo STAGING_DIRECTORY_EXISTS
) else (
  echo STAGING_DIRECTORY_ABSENT
)
```

Both must read absent. Do not proceed otherwise.

### 13.4 Exact two-line invocation

Run exactly once:

```bat
set ALGEBRAIC_N64_F3_EVALUATION_AUTHORIZED=1
python research\brainvision\run_algebraic_n64_f3_evaluation_v0_1.py
```

### 13.5 Immediate exit-code capture

```bat
set F3_EXIT_CODE=%ERRORLEVEL%
echo F3_EXIT_CODE=%F3_EXIT_CODE%
```

Do not issue the runner command again.

### 13.6 Clear the environment variable without rerunning

```bat
set ALGEBRAIC_N64_F3_EVALUATION_AUTHORIZED=

if defined ALGEBRAIC_N64_F3_EVALUATION_AUTHORIZED (
  echo GATE_STILL_SET
) else (
  echo GATE_CLEARED
)
```

Clearing the gate must not be followed by any second invocation.

### 13.7 Post-run repository status

```bat
git status --short --branch
```

### 13.8 List final and staging directories

```bat
dir /a research\brainvision\results\algebraic_n64_primary_v0_1_f3_evaluation_v0_1

dir /a research\brainvision\results\.algebraic_n64_primary_v0_1_f3_evaluation_v0_1.staging
```

### 13.9 Hash any final or retained staging files

When final publication exists:

```bat
certutil -hashfile research\brainvision\results\algebraic_n64_primary_v0_1_f3_evaluation_v0_1\algebraic_n64_primary_v0_1_f3_evaluation_result.json SHA256

certutil -hashfile research\brainvision\results\algebraic_n64_primary_v0_1_f3_evaluation_v0_1\algebraic_n64_primary_v0_1_f3_evaluation_summary.txt SHA256
```

When final publication does not exist but retained staging exists, hash every retained staging file instead, without modifying it.

### 13.10 Record stdout/stderr and absence of evidence if applicable

Retain the full console transcript of the §13.4 invocation, including stdout and stderr, together with the captured `F3_EXIT_CODE`. Do not alter the exact §13.4 invocation by adding shell redirection, piping, command chaining, or script arguments. Retain the visible Command Prompt transcript as displayed, together with the immediately captured F3_EXIT_CODE. When neither a final directory nor evidence-bearing staging exists after a post-contact failure:

```text
record that no publishable evidence bytes were produced
retain stdout, stderr, and the exit code
do not retry
do not recreate synthetic evidence
```

---

## 14. Closed project boundaries

Brainvision remains:

```text
offline
quarantined
non-runtime
non-production
non-live
non-scientific-claim lane
```

Preserve:

```text
FORMAL_HOLD active
Mode_0 active
```

This authorization explicitly prohibits any modification of, or contact involving:

```text
torment_service/kernel/
torment_service/memory_kernel.py
torment_service/fabric.py
production memory
prompt construction
model context
actions
tools
live models
network services
camera capture
screen capture
live sensors
service integration
```

The production TORMENT memory kernel remains immutable. The authorized operation is a self-contained offline PsiTRS descriptor evaluation of a family that was selected and frozen descriptor-blindly. It contacts none of the prohibited production or live surfaces above.

---

## 15. Final authority state

Before this document is committed:

```text
F3_EXECUTION_AUTHORIZATION_DOCUMENTED = False
F3_EXECUTION_AUTHORIZED = False
F3_EXECUTED = False
FROZEN_FAMILY_PSITRS_CONTACT = False
```

After this document is accepted, committed as the sole changed file, pushed, and synchronized:

```text
F3_EXECUTION_AUTHORIZATION_DOCUMENTED = True
F3_EXECUTION_AUTHORIZED = True
F3_EXECUTION_AUTHORIZATION_COUNT = 1
F3_EXECUTED = False
FROZEN_FAMILY_PSITRS_CONTACT = False
```

After the first real frozen-witness PsiTRS call begins:

```text
F3_EXECUTION_AUTHORIZED = consumed
F3_EXECUTED = True
FROZEN_FAMILY_PSITRS_CONTACT = True
```

The final mathematical and operational status must be determined exclusively from the retained canonical evidence and the committed runner's exit and publication contract.

`FORMAL_HOLD` and `Mode_0` remain active.

---

## 16. Disposition

```text
A. AUTHORIZE EXACT ONE-RUN FROZEN-FAMILY F3 EVALUATION
```

The authorization is operational only after:

```text
this document is accepted
the authorization is committed as the sole changed file
the commit is pushed to main
HEAD == origin/main
the working tree is clean, including untracked files
all six implementation identities match
all three production-module raw-byte identities match
the PsiTRS, verifier, and serializer identities match
the freezer-result and frozen evidence identities match
the environment gate is unset
both output directories are absent
```

Recommended authorization-document path:

```text
docs/TORMENT_BRAINVISION_ALGEBRAIC_N64_PRIMARY_V0_1_F3_EVALUATION_EXECUTION_AUTHORIZATION_v0.1.md
```

Recommended commit subject:

```text
docs(research): authorize frozen N64 F3 evaluation
```

---

## 17. Preparation-time assurances

```text
No F3 execution occurred while preparing this authorization.
No frozen witness contacted PsiTRS while preparing this authorization.
The environment gate remained unset.
No final or staging F3 result directory was created.
The production TORMENT kernel remained untouched.
```

*End — TORMENT Brainvision Algebraic N=64 PRIMARY_V0_1 Frozen-Family F3 Evaluation Execution Authorization v0.1. Docs-only during preparation, review, commit, and push. Authorizes exactly one later operator-controlled invocation of the committed F3 evaluator runner after synchronized docs-only commit and push. The one-run authority is consumed when the first real `psi_trs.psi_trs_features(...)` call begins on a frozen family member. No post-contact retry, scientific inference, production integration, or kernel modification is authorized.*

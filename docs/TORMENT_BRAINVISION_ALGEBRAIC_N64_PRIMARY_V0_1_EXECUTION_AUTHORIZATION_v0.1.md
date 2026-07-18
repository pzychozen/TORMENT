# TORMENT Brainvision Algebraic N=64 PRIMARY_V0_1 Execution Authorization v0.1

## 0. Status

**DOCS-ONLY authorization record.** This document authorizes exactly one operator-controlled execution of the
committed `PRIMARY_V0_1` runner. It executes nothing itself, produces no artifact, and changes no source. It
is the first Brainvision document in this lineage to grant an execution authorization; every other closed
stage remains closed.

```text
FORMAL_HOLD_active = True
Mode_0_active      = True
```

Prepared after synchronization to `HEAD = 493271b` (branch `main`, `origin/main = 493271b`). Repository state
was checked with `git status --short --branch`, the recent commit log, and direct inspection of the committed
tree. At review time the sole new working-tree entry is this untracked authorization document.

Brainvision remains offline, prerecorded, quarantined, service-disconnected, non-runtime, non-production,
descriptor-blind, and descriptive-only.

## 1. Governing committed artifacts

Authoritative and unamended by this record:

```text
docs/TORMENT_BRAINVISION_ALGEBRAIC_N64_PRIMARY_V0_1_EXECUTION_PROTOCOL_v0.1.md
research/brainvision/algebraic_direct_sum_n64_candidate_generator_v0_1.py
research/brainvision/run_algebraic_n64_primary_v0_1.py
```

All three are committed at `493271b` and were confirmed present in the tracked tree before this record was
drafted. The runner and its focused test suite entered the tree at `493271b`; the generator at `6a38598`; the
protocol at `8bc5458`.

## 2. Decision

Exactly one operator-controlled execution is authorized, from the repository root:

```text
python research\brainvision\run_algebraic_n64_primary_v0_1.py
```

The execution must use the runner **exactly as committed at `493271b`**.

The commit that records this authorization will necessarily advance repository `HEAD` beyond `493271b`.
That authorization-only advance is permitted. It must not modify the runner, generator, serializer, protocol,
tests, or any other tracked file.

No source, test, protocol, budget, path, profile, traversal, serializer, or artifact rule may be changed
before or during the authorized operation. If any such change is made, this authorization lapses and a new
record is required.

## 3. Authorization state after this document

```text
DOCUMENTATION_AUTHORIZED = True

PRIMARY_V0_1_EXECUTION_AUTHORIZED = True
CANDIDATE_STREAM_PRODUCTION_AUTHORIZED = True

RUNNER_MODIFICATION_AUTHORIZED = False
GENERATOR_MODIFICATION_AUTHORIZED = False
SERIALIZER_MODIFICATION_AUTHORIZED = False
FREEZER_INVOCATION_ON_GENERATOR_OUTPUT_AUTHORIZED = False
N64_WITNESS_GENERATION_AUTHORIZED = False
PsiTRS_EVALUATION_AUTHORIZED = False
SCIENTIFIC_INFERENCE_AUTHORIZED = False
```

**Clarification of `CANDIDATE_STREAM_PRODUCTION_AUTHORIZED = True`.** This authorizes only the runner's
outcome-dependent artifact production as already specified by the protocol. It is permission to write
whichever permitted artifact set the replay outcome yields. It does **not** assert, predict, or require that a
standalone candidate-stream artifact will be produced.

A failed or non-freeze-eligible replay — route incomplete, dependency unavailable, pre-hash null stream, or
replay mismatch — validly produces only the replay-result JSON plus the summary. That two-file outcome is a
complete and correct discharge of this authorization, not a partial or failed one.

## 4. Frozen preconditions

Immediately before execution, the operator confirms all of the following.

**4.1 Clean tree.** `git status --short --branch` shows only:

```text
## main...origin/main
```

Any tracked or untracked entry cancels the authorization until investigated.

**4.2 Authorization commit and lineage recorded.** The current clean `HEAD` must be the commit that adds only
this authorization document, and its immediate parent must be `493271b`.

The operator records:

```text
git log --oneline --decorate -6
git rev-parse HEAD^
git show --name-only --format= HEAD
```

Required results:

```text
HEAD^ resolves to 493271b
the current HEAD commit contains exactly one changed path:
docs/TORMENT_BRAINVISION_ALGEBRAIC_N64_PRIMARY_V0_1_EXECUTION_AUTHORIZATION_v0.1.md
```

The runner, generator, serializer, protocol, tests, and every other tracked file therefore remain exactly as
they were at `493271b`. Any different parent or any additional path in the authorization commit cancels the
authorization until investigated.

**4.3 Both output paths absent:**

```text
research/brainvision/results/algebraic_n64_primary_v0_1/
research/brainvision/results/.algebraic_n64_primary_v0_1.staging/
```

Either path existing cancels the authorization until separately investigated. The runner will independently
refuse in that case, but the operator must not rely on the runner to catch a condition the operator was
required to check: an unexplained pre-existing path is evidence of a prior operation nobody recorded, and that
question must be answered before a new operation begins.

## 5. Exact execution

The only authorized command is:

```text
python research\brainvision\run_algebraic_n64_primary_v0_1.py
```

Prohibited, without exception:

```text
python -c
direct generate_candidate_stream(...)
direct generate_candidate_stream_with_replay(...)
custom imports or interactive calls
alternative output paths
budget changes
profile changes
retries
second executions
manual artifact rewriting
```

**5.1 Single-attempt semantics.** This authorization covers exactly one attempted runner operation.

If the runner refuses before generator execution because an output path already exists — exit code 2 — that
refusal does **not** consume the authorization, because no generator work occurred. The blocking path must
still be investigated before any further attempt.

Any operation that reaches the committed replay call **consumes** the authorization, regardless of outcome:
whether the replay succeeds, fails canonically, publishes a two-file set, publishes a three-file set, or exits
0 or 1. Consumption is determined by whether the generator was contacted, not by whether the result was
useful.

**5.2 No automatic retry.** No retry is authorized under any outcome. A disappointing result is not a reason
to run again; it is the result.

## 6. Required operator transcript

```text
pre-run git status --short --branch
pre-run git log --oneline --decorate -6
pre-run git rev-parse HEAD^
pre-run git show --name-only --format= HEAD
confirmation that the authorization commit has parent 493271b and changes only this authorization document
confirmation that final and staging paths do not exist
exact runner command
complete stdout
complete stderr
process exit code
post-run git status --short --branch
post-run git log --oneline --decorate -6
directory listing of the final artifact directory
certutil SHA-256 verification for every JSON artifact written
```

Hash verification:

```text
certutil -hashfile research\brainvision\results\algebraic_n64_primary_v0_1\algebraic_n64_primary_v0_1_replay_result.json SHA256
```

Run the following **only if** the candidate-stream artifact exists:

```text
certutil -hashfile research\brainvision\results\algebraic_n64_primary_v0_1\algebraic_n64_primary_v0_1_candidate_stream.json SHA256
```

Each value must match the whole-file SHA-256 the runner printed and wrote into the summary. A mismatch
invalidates the operation: the bytes on disk would not be the bytes the runner believed it wrote, and no later
stage may consume the artifacts.

The post-run `git status` is expected to remain **clean**, because `research/brainvision/results/` is covered
by `research/brainvision/.gitignore`. If the artifact directory instead appears as an untracked entry, the
ignore configuration has changed; the operator stops and reports rather than accepting the transcript.

## 7. Outcome boundaries

Whatever the generator returns:

```text
do not invoke the freezer
do not invoke the verifier separately
do not run PsiTRS
do not run the N64 falsifier
do not run descriptors or SAG
do not interpret the records scientifically
do not classify any candidate as a witness
do not claim that a family exists
do not commit generated artifacts automatically
```

A successful replay establishes **only** deterministic primary candidate generation: the runner called the
generator once, the generator reproduced itself byte for byte, and the artifacts were published atomically.
It establishes nothing about witness validity, family validity, homometric admissibility beyond what the
construction theorem already gave, perception, temporal order, production vision, or scientific meaning.

A standalone candidate stream, if produced, is merely **eligible** for a later separately authorized freezer
operation. Eligibility is a property of the artifact's shape, not a finding about its contents. Whether any
six of its records form a freezable family is undecided and remains a question for the independent verifier
under an authorization that does not yet exist.

A canonical route failure or replay mismatch is retained as valid operational evidence. It is a real result
about the generator's behaviour under the frozen budget, and it must not be rerun automatically or discarded.

## 8. Immutable files

The authorized execution may not modify:

```text
research/brainvision/algebraic_direct_sum_n64_candidate_generator_v0_1.py
research/brainvision/run_algebraic_n64_primary_v0_1.py
research/brainvision/witness_canonical_json_v0_1.py
research/brainvision/witness_family_verifier_v0_1.py
research/brainvision/witness_family_freeze_v0_1.py
research/brainvision/psi_trs.py
research/brainvision/run_n64_falsifier_v0_1.py
torment_service/kernel/
torment_service/memory_kernel.py
torment_service/fabric.py
```

The runner writes only inside `research/brainvision/results/`, never overwrites, and publishes by a single
atomic rename. Any modification to a file above during the operation invalidates the transcript.

## 9. Conclusion

```text
DOCUMENTATION_AUTHORIZED = True
PRIMARY_V0_1_EXECUTION_AUTHORIZATION_DOCUMENTED = True

PRIMARY_V0_1_EXECUTION_AUTHORIZED = True
CANDIDATE_STREAM_PRODUCTION_AUTHORIZED = True

FREEZER_INVOCATION_ON_GENERATOR_OUTPUT_AUTHORIZED = False
N64_WITNESS_GENERATION_AUTHORIZED = False
PsiTRS_EVALUATION_AUTHORIZED = False
SCIENTIFIC_INFERENCE_AUTHORIZED = False
```

Explicitly, in the preparation of this authorization:

```text
no PRIMARY_V0_1 execution occurred while preparing this authorization
no primary candidate stream was produced
no replay artifact was produced
no freezer was invoked
no witness family was frozen
no PsiTRS evaluation occurred
no production-kernel file was modified
```

*End — TORMENT Brainvision Algebraic N=64 PRIMARY_V0_1 Execution Authorization v0.1. Docs-only. Authorizes
exactly one operator-controlled runner execution at `493271b` and nothing else. Freezing, verification, ΨTRS
evaluation, and scientific interpretation remain separate closed stages requiring separate authorization. The
governing protocol and specifications are unamended; the generator, runner, serializer, verifier, freezer,
`psi_trs.py`, `run_n64_falsifier_v0_1.py`, and the production TORMENT memory kernel are immutable. No `§0`
pointer; no registry or orientation update; no tags; no commit; no push.*

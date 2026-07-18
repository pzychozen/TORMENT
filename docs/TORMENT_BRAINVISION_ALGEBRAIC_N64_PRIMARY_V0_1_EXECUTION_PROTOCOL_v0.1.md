# TORMENT Brainvision Algebraic N=64 PRIMARY_V0_1 Execution Protocol v0.1

## 0. Status / authority

**DOCS-ONLY operational protocol. Non-implementing, non-executing.** This document specifies how a future
`PRIMARY_V0_1` candidate-stream generation operation must be performed, what it must write, and what it may
never do. It implements no runner, executes no generator, produces no candidate stream, produces no replay
artifact, freezes no family, and evaluates no descriptor. It authorizes documentation only.

```text
FORMAL_HOLD_active = True
Mode_0_active      = True

documentation_authorization                = True
runner_implementation_authorization        = False
PRIMARY_V0_1_execution_authorization       = False
candidate_stream_production_authorization  = False
freezer_invocation_authorization           = False
witness_generation_authorization           = False
PsiTRS_evaluation_authorization            = False
scientific_inference_authorization         = False
```

Prepared after synchronization to `HEAD = 6a38598` (branch `main`, `origin/main = 6a38598`). Repository state
was checked with `git status --short --branch`, the recent commit log, and direct file inspection. At review
time the sole new working-tree entry is this untracked protocol document.

Brainvision remains offline, prerecorded, quarantined, service-disconnected, non-runtime, non-production,
descriptor-blind, and descriptive-only.

## 1. Governing documents and inspected sources

Authoritative and **unamended** by this protocol:

```text
docs/TORMENT_BRAINVISION_ALGEBRAIC_DIRECT_SUM_N64_CANDIDATE_GENERATOR_IMPLEMENTATION_SPECIFICATION_v0.1.md
docs/TORMENT_BRAINVISION_N64_CANDIDATE_GENERATOR_ROUTE_DECISION_v0.1.md
docs/TORMENT_BRAINVISION_INDEPENDENT_DESCRIPTOR_BLIND_HIGHER_ORDER_WITNESS_FAMILY_IMPLEMENTATION_SPECIFICATION_v0.1.md
docs/TORMENT_BRAINVISION_INDEPENDENT_HIGHER_ORDER_WITNESS_VERIFIER_AND_FREEZE_INFRASTRUCTURE_IMPLEMENTATION_SPECIFICATION_v0.1.md
```

Sources read directly at `6a38598` before drafting:

```text
research/brainvision/algebraic_direct_sum_n64_candidate_generator_v0_1.py    (complete)
research/brainvision/witness_canonical_json_v0_1.py                          (complete)
research/brainvision/.gitignore                                              (complete)
research/brainvision/witness_family_verifier_v0_1.py                         (public interface only)
research/brainvision/witness_family_freeze_v0_1.py                           (public interface only)
```

The verifier and freezer were inspected for boundary confirmation only. Neither is modified, proposed for
modification, invoked, nor relied upon by this protocol.

## 2. Verified interface facts

Every rule below rests on these facts, each read directly from the committed generator at `6a38598`. A future
runner author must re-verify them rather than trusting this restatement.

**2.1 Return shape.** `generate_candidate_stream_with_replay(profile_name, ...)` returns
`cjson.envelope("generator_replay_result", payload)`, i.e. exactly two top-level keys:

```text
generator_replay_result          the replay payload mapping
generator_replay_result_sha256   SHA-256 over the canonical bytes of that payload only
```

This document calls the complete two-key object the `generator_replay_result_envelope`.

**2.2 Replay payload fields.** The payload always carries:

```text
schema_name                        "brainvision_generator_replay_result"
schema_version                     "0.1"
authoritative_operation            bool
downstream_freeze_eligible         bool
byte_identical                     bool
run1_candidate_stream_sha256       str or null
run2_candidate_stream_sha256       str or null
generator_identity_envelope        mapping or null
generator_configuration_envelope   mapping or null
structural_budget_envelope         mapping or null
source_identity_envelope           mapping or null
run1_structural_counters           mapping (always present)
run2_structural_counters           mapping (always present)
candidate_stream_envelope          mapping or null
failure_record                     mapping or null
```

**2.3 Counters are exposed; termination reason is not.** `run1_structural_counters` and
`run2_structural_counters` are present in every returned replay payload, including pre-hash failure payloads
(where they are the zero-counter mapping). This is a direct read of the constructed `base` dictionary and it
means §11 of this protocol requires **no** additional generator call.

By contrast, `termination_reason` appears nowhere in the replay payload. The replay operation compares run1 and
run2 termination reasons internally when deciding `byte_identical`, but does not surface either value. This
absence is the entire reason §9 exists.

**2.4 Freeze-eligibility is computed, not supplied.** The generator sets:

```text
authoritative_operation    = True only when both runs produced a stream and canonical bytes,
                             structural counters, terminal status, and termination reason all matched
downstream_freeze_eligible = authoritative_operation and terminal_status in
                             {stream_completed, budget_exhausted}
```

Consequently the five extraction conditions in §8 are partially redundant against the implementation. They are
retained as defence in depth: the runner must not infer any one of them from any other.

**2.5 PRIMARY_V0_1 budget.** `structural_budget_payload("PRIMARY_V0_1")` yields:

```text
max_parameter_tuples_examined = 3395616     (equal to the complete normalized parameter domain)
max_candidate_records_emitted = 20000
termination_precedence        = DOMAIN_EXHAUSTED
                                MAX_CANDIDATE_RECORDS_EMITTED
                                MAX_PARAMETER_TUPLES_EXAMINED
```

**2.6 Core termination branch order.** The pure core evaluates, after each examined tuple, in this exact order:
one-tuple lookahead exhaustion (`DOMAIN_EXHAUSTED`), then the record ceiling
(`MAX_CANDIDATE_RECORDS_EMITTED`), then the tuple ceiling (`MAX_PARAMETER_TUPLES_EXAMINED`). The derivation in
§9 was written against this branch order and reproduces the unexposed value rather than merely approximating
it.

**2.7 Results path is already ignored.** `research/brainvision/.gitignore` line 2 is `results/`. Confirmed by
`git check-ignore -v` resolving a path under the proposed artifact directory to that rule. The post-run
repository status in §14 is therefore expected to be **clean**, not to show the artifact directory. A future
operator who observes the artifact directory appearing as untracked has encountered an unexplained change in
ignore configuration and must stop and report it rather than accepting the transcript.

## 3. Stage separation

This protocol governs exactly one stage. The stages are distinct, and completion of an earlier one confers no
authority over a later one.

```text
implementation validation:
    COMPLETE — committed generator source review and 53 focused tests at 6a38598
    establishes: the generator behaves as specified
    establishes nothing about any witness, family, or perceptual claim

primary candidate-stream generation:
    FUTURE, SEPARATELY AUTHORIZED — one bounded PRIMARY_V0_1 replay operation
    governed by this document
    establishes: a deterministic, replay-confirmed candidate stream exists

family freezing:
    SEPARATE CLOSED STAGE — requires separate authorization
    the accepted verifier and freezer remain the sole deciders of every witness predicate

PsiTRS evaluation:
    SEPARATE CLOSED STAGE — requires separate authorization

scientific interpretation:
    SEPARATE CLOSED STAGE — requires separate authorization
```

Replay authority means **only** that generator execution was deterministic and reproduced itself byte for byte.
It does not establish witness validity, family validity, homometric admissibility beyond what the construction
theorem already gives, perception, temporal order, production vision, or any scientific meaning whatsoever. A
`downstream_freeze_eligible = True` result means the artifact is *shaped* such that a freezer could later be
asked to consider it. It is not a finding.

## 4. Dedicated runner

A minimal dedicated runner is required. `python -c` is prohibited: it leaves no reviewable source, cannot be
hashed into a transcript, and cannot be tested.

```text
future runner path:
    research/brainvision/run_algebraic_n64_primary_v0_1.py

implementation authorization for that runner:
    NOT GRANTED BY THIS DOCUMENT
```

**4.1 Sole authoritative generator call.** The runner's only generator call is:

```python
generate_candidate_stream_with_replay("PRIMARY_V0_1")
```

The runner must never call `generate_candidate_stream()` separately — not for output, not for diagnostics, not
to recover a termination reason, not for comparison, not under any conditional branch. A third provisional call
would be a third independent execution whose relationship to the two replayed runs is unestablished, and any
value recovered from it would be an unverified attribution. The replay operation already performs both
authoritative runs internally.

**4.2 Exact operator invocation.** From the repository root:

```text
python research\brainvision\run_algebraic_n64_primary_v0_1.py
```

**4.3 No configuration surface.** v0.1 admits no argument, flag, or environment override for profile name,
output path, budget, source path, worker count, overwrite behaviour, or record limit. The invocation above is
the complete interface. A configurable runner would make the transcript insufficient to reconstruct what was
executed.

## 5. Artifact directory

```text
research/brainvision/results/algebraic_n64_primary_v0_1/
```

Permitted artifacts, exactly:

```text
algebraic_n64_primary_v0_1_candidate_stream.json     (conditional — see §8)
algebraic_n64_primary_v0_1_replay_result.json        (see §9)
algebraic_n64_primary_v0_1_summary.txt               (see §11)
```

Filenames contain no hash, no timestamp, and no run counter. A hash in a filename invites treating the name as
evidence; the hash belongs in the transcript and the summary, where it can be checked against the file bytes.

Generated evidence is retained **locally first**. It is not automatically staged, committed, pushed, frozen,
verified, or evaluated. Per §2.7 the path is already ignored, so retention is local by default rather than by
operator discipline alone.

## 6. Set-level atomic publication

The permitted artifacts are one outcome-dependent evidential set. When §8 permits standalone
candidate-stream extraction, the set contains replay-result JSON, candidate-stream JSON, and summary.
Otherwise the complete permitted set contains replay-result JSON and summary only. Directory-level atomicity
applies to whichever two- or three-file set the replay outcome permits. A partially written set is not weaker evidence — it is
uninterpretable, because a reader cannot tell whether a missing candidate-stream file means "not eligible" or
"write failed". Publication is therefore all-or-nothing at the directory level.

```text
staging directory:
    research/brainvision/results/.algebraic_n64_primary_v0_1.staging/
```

**6.1 Pre-execution refusal.** Before the generator is invoked, the runner hard-refuses when **either** the
final directory or the staging directory already exists. It refuses before execution, not after, so that a
refusal costs nothing and cannot be confused with a generation failure.

**6.2 Publication sequence.**

```text
1. verify neither final nor staging directory exists          (else hard refusal, §13)
2. create the staging directory
3. run generate_candidate_stream_with_replay("PRIMARY_V0_1")
4. write the complete permitted artifact set into staging
5. flush and close every file
6. atomically rename staging -> final
```

The rename is the single publication event. Nothing outside the staging directory is written before it.

**6.3 Never overwrite.** No overwrite, truncate-in-place, merge, append, or force operation is admitted at any
step. If the final directory exists, the operation refuses; it never replaces an earlier operation's evidence.

**6.4 Failure before publication.** On any runner-level serialization or I/O failure occurring before the
rename:

```text
remove the staging directory when this can be done safely
leave no final output directory
print the runner failure to stderr
do not fabricate a replay artifact, candidate stream, hash, or generator failure record
```

"When safely possible" is deliberate: if staging cleanup itself fails, the runner reports both failures to
stderr and leaves the staging directory in place. A leftover staging directory is a visible, self-announcing
condition that blocks the next run by §6.1. That is the correct outcome — silently deleting state after an
unexplained I/O failure is worse than refusing to proceed.

## 7. Canonical JSON writing

Both JSON artifacts are written with exactly:

```python
witness_canonical_json_v0_1.canonical_json_bytes(...)
```

which is the same helper the generator itself used to compute every hash it reports. Using any other
serialization path — even one that appears equivalent — would break the correspondence between the reported
payload hashes and the file bytes.

```text
UTF-8
ensure_ascii=True
sorted keys
compact separators (",", ":")
allow_nan=False
no trailing newline
exactly one complete JSON document per file
no JSONL
no pretty printing
no indentation
no reserialization through a different JSON configuration
no post-write text transformation of any kind
```

Files are opened in binary mode and `canonical_json_bytes(...)` is written unmodified so the exact
serializer-produced bytes are preserved without encoding, newline, or text-layer transformation. Text-mode
writing is prohibited.

```text
replay-result file contents:
    the complete returned generator_replay_result_envelope (both top-level keys)

candidate-stream file contents:
    the exact unchanged embedded candidate_stream_envelope (both of its keys),
    written only under the extraction rule in §8
```

## 8. Candidate-stream extraction rule

The separate candidate-stream artifact is written only when **all** of the following hold:

```text
authoritative_operation      = True
downstream_freeze_eligible   = True
byte_identical               = True
candidate_stream_envelope    is a mapping
terminal_status              in {stream_completed, budget_exhausted}
```

Each is checked independently. Per §2.4 the implementation already couples several of them; the runner must not
exploit that coupling, because the coupling is a property of the current generator rather than of the protocol.

**8.1 Verbatim retention.** The embedded envelope is written exactly as returned. The runner must not
post-filter, truncate, reorder, deduplicate, reinterpret, rebuild, re-key, prune, or annotate its records, and
must not strip generator diagnostics. Every record emitted by the frozen primary operation is retained, up to
the existing 20,000-record ceiling. Any modification would invalidate the embedded `candidate_stream_sha256`
and would substitute the runner's judgement for the generator's frozen behaviour.

**8.2 Both successful outcomes are retained.**

```text
stream_completed    the complete normalized parameter domain was traversed
budget_exhausted    a deterministic prefix of that traversal was emitted
```

A `budget_exhausted` artifact is a valid deterministic prefix under a frozen budget and a frozen traversal
order. It must not be discarded, downgraded, or marked provisional merely because the full parameter domain was
not exhausted. Whether such a prefix contains a freezable family is a question for the freezer under separate
authorization, not for the runner.

## 9. Replay-result retention, terminal status, and derived termination reason

**9.1 Retention.** Whenever the returned replay result can be canonically serialized, the replay-result
artifact is written — regardless of whether the operation was authoritative or freeze-eligible. The replay
result is the primary record of what the generator did, including when what it did was fail. Retained cases:

```text
successful replay
valid zero-record route_incomplete replay
valid zero-record dependency_unavailable replay
pre-hash null-stream failure
replay mismatch
any other canonically serializable replay failure
```

For every non-freeze-eligible case:

```text
do not write the separate candidate-stream artifact
do not invoke the freezer
```

A non-null zero-record stream embedded inside a route-incomplete or dependency-unavailable replay remains
**embedded in the replay artifact only**. It is never promoted to a standalone candidate-stream file. Promoting
it would produce a file whose name asserts a candidate stream and whose contents contain none.

**9.2 Terminal status.** Reported as:

```text
if candidate_stream_envelope exists:
    terminal_status = candidate_stream_envelope["candidate_stream"]["terminal_status"]
otherwise:
    terminal_status = null
```

**9.3 Derived termination reason.** Because the replay payload does not expose `termination_reason` (§2.3), the
runner derives it and must label the derived value explicitly as `derived_termination_reason` everywhere it
appears. It is never labelled `termination_reason`. It is never written into a canonical generator artifact.

Frozen derivation, evaluated in order:

```text
terminal_status == stream_completed
    -> DOMAIN_EXHAUSTED

terminal_status == budget_exhausted
and candidate_records_emitted == max_candidate_records_emitted
    -> MAX_CANDIDATE_RECORDS_EMITTED

terminal_status == budget_exhausted
and candidate_records_emitted != max_candidate_records_emitted
and parameter_tuples_examined == max_parameter_tuples_examined
    -> MAX_PARAMETER_TUPLES_EXAMINED

terminal_status in {route_incomplete, dependency_unavailable}
and failure_record exists
    -> failure_record.failure_code

candidate_stream_envelope is null
and failure_record exists
    -> failure_record.failure_code
       reported as replay_failure_reason, while terminal_status remains null
```

Counter values are read from `run1_structural_counters`; ceilings are read from
`structural_budget_envelope["structural_budget"]`. The ordered evaluation encodes the frozen terminal
precedence, so when more than one numerical ceiling appears satisfied the record ceiling wins, matching §2.5
and §2.6.

**9.4 PRIMARY_V0_1 unreachability note.** For `PRIMARY_V0_1` the tuple ceiling equals the complete normalized
parameter domain (3,395,616) and `DOMAIN_EXHAUSTED` takes precedence via the core's one-tuple lookahead.
Therefore `MAX_PARAMETER_TUPLES_EXAMINED` is **unreachable during valid PRIMARY_V0_1 execution**: exhausting the
tuple budget and exhausting the domain are the same event, and the lookahead resolves it as completion. The
branch is retained in the derivation because the runner must not assume the budget payload it received matches
the value documented here. If it is ever reached, the discrepancy is itself the finding.

**9.5 Unresolved derivation.** If no unique reason can be derived from the replay artifact, this is a
runner-level protocol-validation failure, not a generator failure:

```text
do not extract a candidate stream
retain the canonical replay artifact if it was already validly produced
report DERIVED_TERMINATION_REASON_UNRESOLVED only as runner-level human diagnostics
do not insert that string into any canonical generator artifact
```

Inspection of the committed generator indicates every null-stream return path sets `failure_record`, so this
branch is expected to be unreachable. It is defence in depth against a future generator change, and reaching it
would mean the runner's model of the generator is wrong — which must be surfaced, never papered over with a
guessed reason.

## 10. Identity and hash reporting

**10.1 Two distinct kinds of hash.** These must never be conflated, and the summary must label each:

```text
envelope payload hash:
    the existing *_sha256 field produced by witness_canonical_json_v0_1.envelope(...)
    computed over the canonical bytes of the PAYLOAD ONLY, nonrecursively

artifact file SHA-256:
    SHA-256 over the complete canonical JSON FILE BYTES as written to disk
```

The candidate-stream file contains the *envelope* (`candidate_stream` plus
`candidate_stream_sha256`), whereas `candidate_stream_sha256` is computed over the inner payload alone. The
two hashes cover different byte sequences and must never be treated as interchangeable. Equality must not be
assumed or used as validation; each value must be verified against its own defined byte domain. Describing an
envelope payload hash as the whole-file hash is prohibited, and any transcript doing so is rejected.

**10.2 Reported values.** The summary and stdout report, when present:

```text
generator_identity_sha256
generator_configuration_sha256
structural_budget_sha256
source_identity_sha256

run1_candidate_stream_sha256
run2_candidate_stream_sha256
candidate_stream_sha256

generator_replay_result_sha256
```

Each of the first four is read from its corresponding envelope's hash field; a null envelope is reported as
absent rather than as an empty or zero hash. Complete-file SHA-256 values are reported for every JSON artifact
actually written, and only for those actually written.

## 11. Human summary

```text
research/brainvision/results/algebraic_n64_primary_v0_1/algebraic_n64_primary_v0_1_summary.txt
```

This file is **operator convenience, not canonical generator evidence**. It carries no authority, and no
downstream stage may parse it as input. Deterministic UTF-8 text, LF line endings, exactly one trailing
newline. It contains no timestamp, duration, hostname, username, process ID, temporary path, absolute path, or
memory statistic — so that two runs of the same operation produce byte-identical summaries.

Required contents:

```text
profile name
authoritative_operation
downstream_freeze_eligible
byte_identical

generator_identity_sha256
generator_configuration_sha256
structural_budget_sha256
source_identity_sha256
run1_candidate_stream_sha256
run2_candidate_stream_sha256
candidate_stream_sha256                     (when a stream exists)
generator_replay_result_sha256
whole-file SHA-256 for each JSON artifact written

terminal_status
derived_termination_reason                  (or replay_failure_reason)

run1 structural counters
run2 structural counters
candidate_count                             (when a stream exists)
failure code and stage                      (when present)

candidate-stream artifact written = True / False
freezer invoked = False
PsiTRS invoked = False
scientific interpretation performed = False
```

Stdout mirrors this summary exactly. No separate redirected-stdout artifact is required, because the operator
transcript already captures stdout in full (§14).

## 12. Structural counters

Both runs are reported independently and never merged, averaged, or reported once:

```text
parameter_tuples_examined
colliding_parameter_tuples_rejected
direct_tuples_found
exact_duplicate_candidates_skipped
candidate_records_emitted
```

The runner must require equality of the run1 and run2 counter mappings before accepting the operation as
authoritative, consistent with `authoritative_operation` as returned. This is a redundant cross-check of the
generator's own comparison, held deliberately: it is the one place where the runner can detect a replay
regression without performing any witness mathematics.

The runner performs no witness mathematics. It does not compute autocorrelation, difference multisets, triple
arrays, primitive periods, affine images, or equivalence classes, and it does not independently validate any
candidate predicate. Those belong exclusively to the independent verifier, reached only through the freezer,
under separate authorization.

## 13. Failure policy

There is no separate canonical `failure.json`. Adding one would create a second, competing canonical record of
the same operation.

```text
generator or replay failure:
    represented only by the canonical replay-result artifact and the human summary

runner failure before a canonical replay result exists:
    stderr only; no fabricated generator artifact of any kind

artifact publication failure:
    no final output directory; staging directory cleaned when safely possible (§6.4)

existing final or staging directory:
    hard refusal before generator execution (§6.1)
```

An earlier operation's evidence is never overwritten, merged with, appended to, or reconciled against a later
one. Two operations mean two directories, and the second one must be given a different governing document.

## 14. Repository and transcript requirements

**14.1 Before execution** the operator records, from `torment_fabric/`:

```text
git status --short --branch
git log --oneline --decorate -6
```

The pre-run status must contain only the branch-status line and no tracked or untracked working-tree entries;
ignored files are naturally absent. Any tracked or untracked entry prevents starting the operation.

**14.2 After execution** the operator records the same two commands. No tracked source or documentation
modification is permitted during execution. Per §2.7 the results path is already covered by
`research/brainvision/.gitignore`, so the expected post-run status is **clean**. If instead the artifact
directory appears as an untracked entry, the ignore configuration has changed and the operator must stop and
report rather than accept the transcript. Any unrelated working-tree entry, tracked or untracked, prevents
accepting the operator transcript.

**14.3 Required transcript contents:**

```text
pre-run repository status
pre-run recent commit log
exact runner command
complete stdout and stderr
post-run repository status
post-run recent commit log
artifact hash-verification commands and their outputs
```

`git diff` and `git diff --check` are deliberately **not** required and must not be prioritized. On this
repository CRLF handling makes diff output an unreliable indicator; `git status` plus the commit log is the
dependable pair.

**14.4 Hash verification:**

```text
certutil -hashfile research\brainvision\results\algebraic_n64_primary_v0_1\algebraic_n64_primary_v0_1_replay_result.json SHA256

certutil -hashfile research\brainvision\results\algebraic_n64_primary_v0_1\algebraic_n64_primary_v0_1_candidate_stream.json SHA256
```

The second command is run only when the candidate-stream artifact exists. Both values must match the
whole-file SHA-256 values printed by the runner and written into the human summary. A mismatch invalidates the
operation: it means the bytes on disk are not the bytes the runner believed it wrote, and no further stage may
consume the artifacts.

## 15. Prohibitions

The following are prohibited without exception:

```text
calling generate_candidate_stream() as the authoritative run
calling generate_candidate_stream() for extra diagnostic or termination-reason recovery
making any third generator call for any purpose
changing PRIMARY_V0_1 budgets, traversal order, normalization, or dedup policy
running the operation through python -c or any inline invocation
writing noncanonical JSON, pretty-printed JSON, JSONL, or trailing-newline JSON
opening a JSON artifact in text mode
overwriting, merging with, or appending to existing artifacts
committing or pushing generated evidence automatically
invoking witness_family_freeze_v0_1
invoking the verifier outside the freezer
running psi_trs.py
running run_n64_falsifier_v0_1.py
running descriptors, SAG, paired prerecorded analysis, or any operational harness
modifying any production-kernel file
making any scientific, perceptual, or vision claim from this operation
```

## 16. Immutable files

This protocol neither modifies nor proposes modification of:

```text
research/brainvision/psi_trs.py
research/brainvision/run_n64_falsifier_v0_1.py
research/brainvision/algebraic_direct_sum_n64_candidate_generator_v0_1.py
research/brainvision/witness_canonical_json_v0_1.py
research/brainvision/witness_family_verifier_v0_1.py
research/brainvision/witness_family_freeze_v0_1.py
torment_service/kernel/
torment_service/memory_kernel.py
torment_service/fabric.py
```

## 17. Conclusion

```text
DOCUMENTATION_AUTHORIZED                          = True
PRIMARY_V0_1_EXECUTION_PROTOCOL_DOCUMENTED        = True

PRIMARY_V0_1_EXECUTION_AUTHORIZED                 = False
CANDIDATE_STREAM_PRODUCTION_AUTHORIZED            = False
FREEZER_INVOCATION_ON_GENERATOR_OUTPUT_AUTHORIZED = False
N64_WITNESS_GENERATION_AUTHORIZED                 = False
PsiTRS_EVALUATION_AUTHORIZED                      = False
SCIENTIFIC_INFERENCE_AUTHORIZED                   = False
```

Explicitly, in the preparation of this document:

```text
no PRIMARY_V0_1 execution occurred
no primary candidate stream was produced
no replay artifact was produced
no freezer was invoked
no witness family was frozen
no PsiTRS evaluation occurred
no production-kernel file was modified
```

*End — TORMENT Brainvision Algebraic N=64 PRIMARY_V0_1 Execution Protocol v0.1. Docs-only, non-implementing,
non-executing, non-authorizing. Specifies a future bounded operation only; produces no artifact, freezes no
family, evaluates no descriptor, and makes no scientific claim. The generator, verifier, freezer, and
serializer are unmodified; the governing specifications are unamended; `psi_trs.py`,
`run_n64_falsifier_v0_1.py`, and the production TORMENT memory kernel are immutable. No `§0` pointer; no
registry or orientation update; no tags; no commit; no push.*

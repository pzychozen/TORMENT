# TORMENT Brainvision Algebraic N=64 PRIMARY_V0_1 Freezer Invocation Protocol v0.1

## 0. Status

**DOCS-ONLY protocol. Non-implementing, non-executing, non-authorizing.** This document specifies how the
retained 20,000-record `PRIMARY_V0_1` candidate stream *could* later be submitted to the committed freezer in
one bounded operator-controlled operation. It invokes nothing, evaluates no predicate, searches for no family,
freezes nothing, and modifies no file.

```text
FORMAL_HOLD_active = True
Mode_0_active      = True
```

Prepared at `HEAD = 1240121` (branch `main`, `origin/main = 1240121`), tracked working tree clean. At review
time the sole new working-tree entry is this untracked protocol document.

## 1. Governing result and documents inspected

Read completely:

```text
docs/TORMENT_BRAINVISION_ALGEBRAIC_N64_PRIMARY_V0_1_EXECUTION_RESULT_v0.1.md
research/brainvision/witness_family_freeze_v0_1.py
research/brainvision/witness_family_verifier_v0_1.py
research/brainvision/witness_canonical_json_v0_1.py
tests/research/test_brainvision_witness_family_freeze_v0_1.py
tests/research/test_brainvision_witness_family_verifier_v0_1.py
```

Committed Brainvision documents governing witness-family verification, family freezing, canonical evidence,
freeze eligibility, K=3 selection, failure records, artifact paths, and replay/deterministic-selection
requirements — the exact paths found:

```text
docs/TORMENT_BRAINVISION_INDEPENDENT_DESCRIPTOR_BLIND_HIGHER_ORDER_WITNESS_FAMILY_IMPLEMENTATION_SPECIFICATION_v0.1.md
docs/TORMENT_BRAINVISION_INDEPENDENT_HIGHER_ORDER_WITNESS_VERIFIER_AND_FREEZE_INFRASTRUCTURE_IMPLEMENTATION_SPECIFICATION_v0.1.md
docs/TORMENT_BRAINVISION_N64_CANDIDATE_GENERATOR_ROUTE_DECISION_v0.1.md
docs/TORMENT_BRAINVISION_ALGEBRAIC_DIRECT_SUM_N64_CANDIDATE_GENERATOR_IMPLEMENTATION_SPECIFICATION_v0.1.md
docs/TORMENT_BRAINVISION_ALGEBRAIC_N64_PRIMARY_V0_1_EXECUTION_PROTOCOL_v0.1.md
docs/TORMENT_BRAINVISION_ALGEBRAIC_N64_PRIMARY_V0_1_EXECUTION_AUTHORIZATION_v0.1.md
docs/TORMENT_BRAINVISION_ALGEBRAIC_N64_PRIMARY_V0_1_EXECUTION_RESULT_v0.1.md
```

The first two are the authoritative specifications for the verifier, the freezer, and the witness-family
predicates. They are **not amended** by this protocol. Related but non-governing for this operation:
`docs/TORMENT_BRAINVISION_N64_FALSIFIER_EVALUATION_CONTRACT_v0.1.md` and the N64 falsifier specification
govern the ΨTRS-facing evaluator, which this operation must never contact.

## 2. Exact public operation

Determined from the committed code, not by analogy.

```text
module path:
    research/brainvision/witness_family_freeze_v0_1.py

sole authoritative public operation:
    freeze_with_replay(envelope_obj,
                       repository_commit_identity="UNSPECIFIED_IN_V0_1",
                       source_paths=None)

non-authoritative public operation:
    freeze(envelope_obj)
        single pass; forces family_frozen=False and authoritative_operation=False;
        can NEVER report an authoritative freeze

exact required argument:
    envelope_obj = the candidate_stream_envelope object, i.e. the two-key mapping
                   {"candidate_stream": {...}, "candidate_stream_sha256": "<64 hex>"}

exact return object:
    cjson.envelope("freeze_result", payload)
      -> {"freeze_result": {...}, "freeze_result_sha256": "<64 hex>"}

verifier called internally:
    YES. verify_candidate(record, n) is invoked by the freezer for every evaluated record, and
    verify_family(accepted_certificates, n) once K=3 candidates have been accepted. The freezer
    never trusts supplied certificates, summaries, or generator diagnostics.

replay operation exists:
    YES, INTERNAL. freeze_with_replay calls the pure _freeze_once(envelope_obj) TWICE and compares
    canonical bytes; family_frozen=True requires byte identity plus a valid K=3 family plus three
    passing self-checks.
```

**No operator CLI exists.** `witness_family_freeze_v0_1.py` has no `__main__` block, no argument parser, and
performs **no file I/O whatsoever**. It accepts an in-memory object and returns an in-memory object. It does
not load the candidate-stream file, does not know its path, does not write any artifact, and does not exit
with a process code.

Consequently a separate future **freezer-runner specification is required** before freezer execution could be
authorized. This protocol does not authorize implementing that runner; see §13.

**Self-checks performed by `freeze_with_replay` before freezing**, in this exact order:

```text
verifier.validate_local_configuration(source_paths=...)   -> VERIFIER_CONFIGURATION_INVALID / HASH_IDENTITY_FAILURE
verifier.independence_self_check(source_paths)            -> FORBIDDEN_IMPORT_DETECTED
verifier.regression_self_check()                          -> VERIFIER_REGRESSION_FAILURE
```

These require the verifier, serializer, and freezer sources to be resolvable at their expected repository
paths. `regression_self_check` runs a frozen N=12 positive and negative fixture through `verify_candidate`; it
is internal to the freezer's own integrity gate and touches no candidate from the primary stream.

## 3. Input binding

The future operation is bound to exactly this input identity:

```text
candidate-stream path:
    research/brainvision/results/algebraic_n64_primary_v0_1/algebraic_n64_primary_v0_1_candidate_stream.json

whole-file SHA-256:
    00a816364ddcfc9d06dc8ce1225f58bca013e96a8914ff1eb665004b39ed949b

candidate-stream payload SHA-256:
    70763a2ebbf7ea71267553debee2bf79c2ed3b7b0c016d9a903161074e7bf8c5

schema_name        = brainvision_descriptor_blind_candidate_stream
schema_version     = 0.1
verification_mode  = PRIMARY_CANDIDATE_N64
N                  = 64
candidate_count    = 20000
terminal_status    = budget_exhausted
candidate_generation_index sequence = exactly 0..19999
```

**Which of these the committed code already enforces.** `verifier.validate_stream_envelope`, called first
inside `_freeze_once`, independently recomputes `payload_sha256(candidate_stream)` and rejects on mismatch
with `CANDIDATE_STREAM_HASH_MISMATCH`; it also enforces schema name/version, the three 64-hex generator hashes,
`terminal_status` membership, `candidate_count == len(records)`, per-record
`candidate_generation_index == position`, and `MODE_N[mode] == N`. The **payload** hash is therefore already
bound by the committed verifier.

**What the committed code does not bind.** The whole-file SHA-256, the file path, and the file's read-only
status are outside the freezer entirely, because the freezer never opens a file. Binding
`00a81636…` to the bytes actually loaded is a **future runner responsibility**.

The future operation must refuse **before verification** if any frozen identity or structural precondition
differs. The input artifact must remain read-only: it must not be rewritten, normalized, relocated,
reserialized, pretty-printed, or re-hashed into a new file.

## 4. Eligibility versus authorization

```text
PRIMARY_V0_1_DOWNSTREAM_FREEZE_ELIGIBLE = True
```

This means only that the artifact **may be considered by the freezer interface** — it is an authoritative,
byte-identical, accepted-schema, non-empty stream with an extractable terminal status. Eligibility describes
the container.

It does **not** mean:

```text
freezer execution is currently authorized
any candidate is a witness
a K=3 family exists
a family can necessarily be frozen
PsiTRS evaluation is authorized
scientific inference is authorized
```

## 5. Exact verifier predicates

Taken from the committed verifier using its exact implementation names. **None was evaluated in preparing this
document.**

### 5.1 Artifact-level (`validate_stream_envelope`, before any candidate is touched)

```text
CANDIDATE_STREAM_INVALID          envelope shape, schema, hash fields, terminal status, counts, index order
CANDIDATE_STREAM_HASH_MISMATCH    recomputed payload hash != supplied candidate_stream_sha256
SERIALIZATION_FAILURE             payload not canonically serializable (e.g. nonfinite diagnostics)
CANDIDATE_N_MODE_INVALID          verification_mode / N disagreement
```

A stream-level failure short-circuits the whole operation with `stage = "stream_validation"`; no candidate is
verified.

### 5.2 Per-record and pairwise (`verify_candidate`), evaluated in this gating order

```text
1. record is a mapping carrying raw_support_A and raw_support_B   -> CANDIDATE_SCHEMA_INVALID
2. validate_support(A, n) and validate_support(B, n)              -> CANDIDATE_SUPPORT_INVALID
     (strictly ascending, strict ints, 0 <= x < n, non-empty)
3. sorted(A) != sorted(B)                                          -> CANDIDATE_SUPPORT_INVALID
4. normalize_pair(A, B)  (lexicographic role fixing; roles_swapped recorded)
5. member_certificate(A), member_certificate(B)
6. internal consistency gate: if autocorrelation_equal but not
   (one_step_table_equal and transition_multiset_equal)            -> VERIFIER_INTERNAL_DISAGREEMENT
                                                                      (EXECUTION INVALID, not a rejection)
```

Then the flag set is computed and ordered by the frozen precedence `_CANDIDATE_PRECEDENCE`:

```text
CANDIDATE_SCHEMA_INVALID
CANDIDATE_N_MODE_INVALID
CANDIDATE_SUPPORT_INVALID
CANDIDATE_NOT_HOMOMETRIC                        autocorrelation(A) != autocorrelation(B)
CANDIDATE_MEMBER_NOT_PRIMITIVE                  primitive_period(A) != n or primitive_period(B) != n
CANDIDATE_AFFINE_EQUIVALENT                     affine_equivalent(A, B, n)
CANDIDATE_COMPLEMENT_IMAGE                      direct_complement_image(A, B, n)
CANDIDATE_AFFINE_PLUS_COMPLEMENT_EQUIVALENT     affine_to_complement_equivalent(A, B, n)
CANDIDATE_TRIPLE_G_ALIGNABLE                    triple_g_aligned(A, B, n)
CANDIDATE_CERTIFICATE_INVALID                   certificate envelope failed its own schema validation
```

`pair_valid` is True only when the ordered failure list is empty. `primary_failure_code` is the first entry in
precedence order. Rejection is a **valid execution outcome**; only the execution-invalid codes abort.

Certificates are self-validated: the produced `pair_verifier_certificate` envelope is passed through
`validate_pair_certificate_envelope` on the same production path used for supplied or replayed certificates.

### 5.3 Incremental family predicates (`incremental_family_eligibility`, applied during selection)

Applied to a newly `pair_valid` candidate against already-accepted certificates:

```text
FAMILY_MEMBER_REUSED                  a raw_support already accepted, or A == B within the candidate
FAMILY_MEMBER_G_EQUIVALENT            a member_G_equivalence_key already accepted, or equal keys within the pair
FAMILY_AUTOCORRELATION_CLASS_REUSED   member_certificate_A autocorrelation already accepted
```

Failing these does **not** invalidate the candidate; it records `family_reject_reasons` and moves on.

### 5.4 Family-level (`verify_family`, once exactly K=3 accepted)

```text
FAMILY_PAIR_COUNT_INVALID             len(pair_certificates) != K_FAMILY (= 3)
FAMILY_MEMBER_REUSED                  6 raw supports not all distinct
FAMILY_MEMBER_G_EQUIVALENT            6 member_G_equivalence_keys not all distinct
FAMILY_AUTOCORRELATION_CLASS_REUSED   3 autocorrelation classes not all distinct
FAMILY_NOT_FREEZABLE                  fewer than K accepted after the scan, or family invalid with no
                                      more specific code
```

`family_valid` requires all three distinctness properties **and** `pair_valid` on all three certificates.

### 5.5 Operation-aborting codes

These outcomes terminate the operation rather than functioning as ordinary candidate or family rejections.

stream_validation:

```text
CANDIDATE_STREAM_INVALID
CANDIDATE_STREAM_HASH_MISMATCH
SERIALIZATION_FAILURE
CANDIDATE_N_MODE_INVALID
```

self-check / candidate-execution / result / replay:

```text
VERIFIER_CONFIGURATION_INVALID
FORBIDDEN_IMPORT_DETECTED
HASH_IDENTITY_FAILURE
VERIFIER_INTERNAL_DISAGREEMENT
VERIFIER_REGRESSION_FAILURE
REPLAY_MISMATCH
SERIALIZATION_FAILURE
```

A stream-validation abort occurs before candidate verification.

A self-check abort occurs before or outside primary candidate evaluation.

`VERIFIER_INTERNAL_DISAGREEMENT` aborts immediately during candidate verification and is not a candidate
rejection. `_freeze_once` breaks out of the record loop on `execution_invalid`, recording
`stage = "candidate_verification"` and the offending `candidate_generation_index`.

A result-serialization or replay abort invalidates authoritative freezing even if an earlier internal pass
assembled a provisional K=3 family.

`SERIALIZATION_FAILURE` appears in more than one stage because serialization can fail while validating input
payloads or while constructing canonical result evidence.

By contrast, ordinary candidate rejections (§5.2) and incremental-family rejections (§5.3) are **ledgered and
the scan continues**. They are valid execution outcomes, not aborts.

## 6. Deterministic family-selection policy

The committed freezer's selection policy, read directly from `_freeze_once` and `freeze_configuration()`:

```text
accepts an explicitly supplied family:  NO
searches the candidate stream:          YES
uses candidate_generation_index order:  YES  (ordering_policy = "authoritative_stream_order_first_k")
uses first-valid-family semantics:      YES  (greedy first-K accumulation)
uses combination order:                 NO   (no triple enumeration of any kind)
short-circuits:                          YES  (records after K=3 are marked NOT_EVALUATED_AFTER_K_REACHED)
has a search or verification budget:     NO   (RESOURCE_POLICY_STATUS = "UNBOUNDED_BY_V0_1_SPECIFICATION")
```

Precisely: the freezer iterates `stream["records"]` in index order; for each record it calls
`verify_candidate`; if `pair_valid` and `incremental_family_eligibility` passes against the already-accepted
set, the candidate is accepted; once three are accepted, every remaining record is ledgered as
`NOT_EVALUATED_AFTER_K_REACHED` without verification. This behaviour is test-locked by
`test_selection_first_k_reuse_stop_and_not_evaluated` and
`test_selection_rejects_g_equivalent_and_class_reuse`.

**A deterministic selector therefore already exists and is not missing.** The freezer must not be described as
requiring a preselected family, and equally must not be described as an exhaustive family-search engine.

**Decisive scope limitation — greedy, without backtracking.** Selection is first-fit in stream order and never
reconsiders an earlier acceptance. If the scan accepts candidates *i* and *j* and no later candidate is
compatible with **both**, the operation reports `FAMILY_NOT_FREEZABLE` even if some other triple within the
same 20,000 records would have been mutually compatible. The greedy result is a sound *positive* — anything it
freezes genuinely passed every predicate — but it is **not** a complete negative. §10 depends entirely on this
distinction.

Whether to add an exhaustive or backtracking selector is a separate future question. It is **not** a
precondition for one bounded first operation, provided the negative outcome is reported with the exact bound
stated in §10.

## 7. Computational feasibility

Naive enumeration of all unordered triples of 20,000 candidates would involve:

```text
C(20000, 3) = 1,333,133,340,000        (one trillion, three hundred thirty-three billion, ...)
C(20000, 2) =       199,990,000        (for reference)
```

**The committed freezer avoids this entirely.** It performs a single linear scan, so the number of
`verify_candidate` calls per pass is bounded by the number of records examined, not by any combination count:

```text
best case  (first three records accepted):    3 verifications per pass,        6 total
worst case (K never reached):            20,000 verifications per pass,   40,000 total
                                          (freeze_with_replay runs two passes)
```

The cost is **outcome-dependent and not bounded in advance**, exactly as
`RESOURCE_POLICY_STATUS = "UNBOUNDED_BY_V0_1_SPECIFICATION"` declares.

Per-candidate cost is dominated by integer-exact structure over `Z_64`: two `autocorrelation` computations
(O(N·w) each), two `triple_array` constructions of N×N = 4096 entries, `triple_g_aligned` comparing triple
arrays across `{identity, complement} × U(64)` (2 × φ(64) = 64 relabelings), `affine_equivalent` and
`affine_to_complement_equivalent` over the same unit set with translations, and two
`member_G_equivalence_key` minimizations over a group of size 2·N·φ(N) = 4096. That is on the order of
10⁵–10⁶ elementary Python operations per candidate.

No timing measurement was taken. Cost is potentially substantial and must be measured before full-stream
authorization; no wall-clock estimate is established by this protocol.

Any pilot must be a separately specified, separately authorized, non-authoritative benchmark over an explicit
subset or prefix. It must not freeze a family, must not be reported as the authoritative freezer run, and must
not alter the frozen full-stream semantics.

Specifically:

```text
the benchmark may exercise implementation cost only under its own future authorization
its result cannot consume or satisfy a later authoritative freezer authorization
its subset outcome cannot be reported as a family-search result for the complete stream
the authoritative freezer runner must still use the exact full retained stream unless a later protocol
    changes that scope
```

This protocol neither designs nor authorizes such a benchmark.

**No unbounded brute-force triple search is authorized by freeze eligibility.** Eligibility says the artifact
has the right shape; it says nothing about affordability.

## 8. Output artifact contract

### 8.1 What the committed freezer produces (in memory only)

```text
canonical serializer:   witness_canonical_json_v0_1
                        ensure_ascii, sort_keys, compact separators, allow_nan=False, no trailing newline
                        nonrecursive external payload hashing

success/failure schema: a SINGLE schema for both outcomes -
                        "brainvision_witness_freeze_result" v0.1, returned as
                        {"freeze_result": {...}, "freeze_result_sha256": "<64 hex>"}

  key payload fields:
    verification_mode, N, candidate_stream_sha256, candidate_count, terminal_stream_status
    generator_identity_hash, generator_configuration_hash, budget_identity_hash
    candidate_decision_ledger, candidate_decision_ledger_sha256
    accepted_candidate_indices, accepted_pair_certificate_envelopes
    family_certificate, family_manifest
    provisional_k3_valid, family_frozen, authoritative_operation
    regression_mode_no_primary_manifest, resource_policy_status
    replay_record {run1_sha256, run2_sha256, byte_identical}
    local_source_identities, verifier_configuration_sha256
    failure_record {failure_code, stage, ordered_failure_codes[, candidate_generation_index]}

on success additionally:
    family_manifest = cjson.envelope("family_manifest", {...})   schema "brainvision_witness_family_manifest"
    binding the candidate_stream_sha256, the three generator hashes, the verifier/serializer/freeze source
    paths and SHA-256s, their configuration payloads and hashes, the accepted indices, the accepted pair
    certificate envelopes, the family certificate envelope, the decision-ledger hash, and
    repository_commit_identity (default "UNSPECIFIED_IN_V0_1")

payload hashes:  present (freeze_result_sha256, family_manifest_sha256, candidate_decision_ledger_sha256,
                 per-certificate hashes). verify_manifest_identity() recomputes the manifest hash and
                 reports HASH_IDENTITY_FAILURE on tampering.
```

**Explicit provenance binding — no default argument may be relied upon.** The public function currently
exposes two defaults, `repository_commit_identity="UNSPECIFIED_IN_V0_1"` and `source_paths=None`. That the
implementation default exists is a fact about the committed code; authorized operational use of either default
is prohibited.

```text
repository_commit_identity must be the exact authorized commit identity supplied by the future freezer
runner. The default "UNSPECIFIED_IN_V0_1" is implementation-only and is not acceptable for an authorized
PRIMARY_V0_1 freezer run.

The future runner specification must freeze and pass source_paths explicitly from the authorized repository
root to:

  verifier   -> research/brainvision/witness_family_verifier_v0_1.py
  serializer -> research/brainvision/witness_canonical_json_v0_1.py
  freeze     -> research/brainvision/witness_family_freeze_v0_1.py

source_paths=None is not acceptable for the authorized runner.
```

Operational consequence:

```text
A future runner must refuse before freezer contact if the authorized repository commit identity cannot be
resolved exactly, if any frozen source path differs, or if the bytes at those paths do not satisfy the
committed freezer's configuration and identity checks.
```

A manifest carrying `repository_commit_identity = "UNSPECIFIED_IN_V0_1"` would be an unbound artifact: it
would record which verifier sources were used but not which repository state authorized the operation, and no
later reader could tie it to a commit. **No change to the committed freezer is required** — the defaults may
remain exactly as they are; the obligation falls entirely on the future runner to supply both arguments
explicitly.

### 8.2 What the committed freezer does **not** provide

```text
whole-file hashes:        NOT IMPLEMENTED (no file is written)
human summary:            NOT IMPLEMENTED
overwrite protection:     NOT APPLICABLE (no file is written)
atomic publication:       NOT IMPLEMENTED
staging directory:        NOT IMPLEMENTED
process exit codes:       NOT IMPLEMENTED
input file loading:       NOT IMPLEMENTED
```

These are **requirements for a future freezer runner**, not existing behaviour. This protocol does not claim
any of them exists today.

### 8.3 Proposed future paths — protocol-level design only, not current behaviour

Consistent with the generator-runner convention, a future runner would publish to:

```text
final:    research/brainvision/results/algebraic_n64_primary_v0_1_freeze_v0_1/
staging:  research/brainvision/results/.algebraic_n64_primary_v0_1_freeze_v0_1.staging/
```

Both sit under the already-ignored `research/brainvision/results/`. **These paths are proposed future design.
No committed code writes to them, and nothing in this protocol creates them.**

## 9. Success semantics

A successful freeze may establish **only**:

```text
the exact selected K=3 records passed the committed verifier
the frozen family artifact is canonical and bound to the exact source stream
the family satisfies the implemented N64 witness-family predicates
```

It must **not** be read as establishing:

```text
PsiTRS usefulness
perception
temporal order
vision
production readiness
scientific significance
uniqueness of the family
absence or presence of additional families
full-domain coverage
```

"The implemented predicates" is the exact scope: the family would satisfy the predicates listed in §5 as
implemented at the frozen verifier source hash — no more. Equal complete periodic autocorrelation would be
independently recomputed by the verifier rather than inherited from the generator's construction theorem, which
is a genuine strengthening of that one property, and of that one property only.

## 10. Negative and incomplete outcomes

Distinct outcomes the future operation must distinguish:

```text
input identity mismatch          runner-level refusal before any verification (path / whole-file hash /
                                 structural precondition differs)
invalid candidate-stream         CANDIDATE_STREAM_INVALID | CANDIDATE_STREAM_HASH_MISMATCH |
  structure                      CANDIDATE_N_MODE_INVALID | SERIALIZATION_FAILURE, stage stream_validation
no supplied family               NOT APPLICABLE — the committed freezer never accepts a supplied family
candidate failure                per-record ordered_failure_codes in the decision ledger; the scan continues
pairwise failure                 same mechanism: pairwise predicates are per-candidate (A against B)
family-level failure             verify_family ordered_failure_codes, stage family_verification
no valid family found            FAMILY_NOT_FREEZABLE, stage family_selection
dependency / serialization       SERIALIZATION_FAILURE (stage result_serialization), or a self-check code
  failure                        (VERIFIER_CONFIGURATION_INVALID / FORBIDDEN_IMPORT_DETECTED /
                                 VERIFIER_REGRESSION_FAILURE / HASH_IDENTITY_FAILURE)
replay mismatch                  REPLAY_MISMATCH, stage replay
publication failure              runner-level only; not implemented today
pre-existing output path         runner-level refusal before invocation; not implemented today
```

**Three negatives that must never be conflated**, in strictly increasing strength:

```text
1. no valid family in the examined subset
   The greedy scan (§6) did not assemble K=3 in stream order. Because selection is first-fit without
   backtracking, and because records after K are never evaluated, this is the WEAKEST negative. It does
   not even establish claim 2.

2. no valid family in the 20,000-record stream
   NOT established by any outcome of the committed freezer. Establishing it would require an exhaustive
   or backtracking selector that does not exist.

3. no valid family in the complete 3,395,616-tuple construction domain
   NOT establishable from this artifact at all. The stream covers 35,505 examined parameter tuples,
   approximately 1.05 percent of the frozen domain, and terminated at the record ceiling.
```

Any report of a negative outcome must state which of these three it is. In every foreseeable case it is the
first.

## 11. One-operation and replay semantics

`_freeze_once` is a pure deterministic function of the envelope: no randomness, clock, environment, filesystem,
or iteration-order dependence. Identical input therefore necessarily yields identical canonical output within
one environment.

**Replay is already implemented inside the authoritative operation.** `freeze_with_replay` runs `_freeze_once`
twice and compares canonical bytes, gating `family_frozen` on identity.

**Recommendation, grounded in the committed code and expected cost:** a future runner must invoke
`freeze_with_replay` **exactly once** and must not wrap it in an outer double invocation. The generator-runner
pattern of "call the replay operation once" already applies; but the reasoning here is stronger than analogy.
An outer double invocation would execute `_freeze_once` **four** times — up to 80,000 `verify_candidate` calls
— to re-test a property the inner comparison already tests, on a function with no identified nondeterminism
source. That is a duplication of the single most expensive component of the operation for no additional
evidential value.

What a runner should add instead is cheap and currently absent: binding the loaded bytes to the expected
whole-file hash, refusing on pre-existing output paths, atomic publication, and an exit contract.

## 12. Pre-execution state for a future operation

Execution authorization remains **False**. Should it later be granted, these preconditions would apply:

```text
clean tracked AND untracked working tree (branch-status line only)
committed protocol, and a later separate authorization commit in lineage
source stream present at the frozen path with whole-file SHA-256
    00a816364ddcfc9d06dc8ce1225f58bca013e96a8914ff1eb665004b39ed949b
and canonical payload SHA-256
    70763a2ebbf7ea71267553debee2bf79c2ed3b7b0c016d9a903161074e7bf8c5
final output path absent
staging path absent
no source or test changes
verifier, serializer, and freezer sources resolvable at their expected repository paths
    (required by the freezer's own configuration and independence self-checks)
```

**Explicit provenance arguments are part of the precondition set.** Neither default may be relied upon:

```text
repository_commit_identity must be the exact authorized commit identity supplied by the future freezer
runner. The default "UNSPECIFIED_IN_V0_1" is implementation-only and is not acceptable for an authorized
PRIMARY_V0_1 freezer run.

The future runner specification must freeze and pass source_paths explicitly from the authorized repository
root to:

  verifier   -> research/brainvision/witness_family_verifier_v0_1.py
  serializer -> research/brainvision/witness_canonical_json_v0_1.py
  freeze     -> research/brainvision/witness_family_freeze_v0_1.py

source_paths=None is not acceptable for the authorized runner.

A future runner must refuse before freezer contact if the authorized repository commit identity cannot be
resolved exactly, if any frozen source path differs, or if the bytes at those paths do not satisfy the
committed freezer's configuration and identity checks.
```

Refusal here is pre-contact: it must occur before `freeze_with_replay` is called, so that a provenance defect
costs nothing and can never be confused with a verification or family outcome.

## 13. Immutable boundaries

The future operation must not modify or contact:

```text
research/brainvision/psi_trs.py
research/brainvision/run_n64_falsifier_v0_1.py
torment_service/kernel/
torment_service/memory_kernel.py
torment_service/fabric.py
```

It must not run:

```text
PsiTRS
descriptors
SAG
N64 falsifier evaluation
production services
live capture
```

It must not modify the generator, the runner, the verifier, the serializer, the freezer, the committed
specifications, or the retained candidate-stream artifact.

## 14. Implementation-readiness disposition

```text
B. FREEZER_RUNNER_SPECIFICATION_REQUIRED_BEFORE_AUTHORIZATION
```

**Why B and not A.** The committed freezer is mathematically complete and self-replaying, but it has no
operator-invocable surface at all: no CLI, no `__main__`, no file I/O, no input loading, no identity binding to
the artifact's path or whole-file hash, no explicit provenance contract binding `repository_commit_identity`
and `source_paths` (§8.1, §12), no pre-existing-output refusal, no staging, no atomic publication, no human
summary, and no exit codes. Authorizing execution today would require driving it from `python -c` or an
interactive session, which every protocol in this lineage explicitly prohibits and which would leave no
reviewable source and no reproducible transcript.

**Why B and not C or D.** A deterministic family selector is **not missing**. The freezer implements greedy
first-K selection in authoritative stream order, declares it in `freeze_configuration()`, ledgers every
decision, and is test-locked. Its greedy, non-backtracking nature is a documented scope limitation that bounds
how a negative may be reported (§10), not an absent component. Specifying a different selector is a separate
future decision and is not a precondition for one bounded first operation.

**Why B and not E.** The retained stream conforms to every structural precondition the committed verifier
enforces — schema, mode, N, terminal status, count, index sequence, and payload hash — and
`PRIMARY_CANDIDATE_N64` is a supported mode that produces a family manifest on success. The freezer path is
admissible for this artifact; only the operational wrapper is absent.

The required next artifact is therefore a **freezer-runner implementation specification**, drafted and
adversarially reviewed before any execution authorization is considered. Drafting it is **not** authorized by
this document.

## 15. Authority state

```text
DOCUMENTATION_AUTHORIZED = True
FREEZER_INVOCATION_PROTOCOL_DOCUMENTATION_AUTHORIZED = True

PRIMARY_V0_1_EXECUTION_AUTHORIZED = False
CANDIDATE_STREAM_PRODUCTION_AUTHORIZED = False

PRIMARY_V0_1_DOWNSTREAM_FREEZE_ELIGIBLE = True

FREEZER_INVOCATION_ON_GENERATOR_OUTPUT_AUTHORIZED = False
FREEZER_RUNNER_IMPLEMENTATION_AUTHORIZED = False
FAMILY_SELECTOR_IMPLEMENTATION_AUTHORIZED = False
N64_WITNESS_GENERATION_AUTHORIZED = False
N64_WITNESS_FAMILY_FREEZE_AUTHORIZED = False
PsiTRS_EVALUATION_AUTHORIZED = False
SCIENTIFIC_INFERENCE_AUTHORIZED = False
```

## 16. Conclusion

Explicitly, in the preparation of this protocol:

```text
no generator rerun occurred
no candidate-stream artifact was modified
no verifier was invoked
no freezer was invoked
no witness predicate was evaluated
no family search occurred
no family was frozen
no PsiTRS evaluation occurred
no production-kernel file was modified
```

*End — TORMENT Brainvision Algebraic N=64 PRIMARY_V0_1 Freezer Invocation Protocol v0.1. Docs-only,
non-implementing, non-executing, non-authorizing. Specifies a possible future bounded freezer operation and
selects disposition B; invokes nothing, verifies nothing, freezes nothing, and makes no scientific claim. The
verifier, freezer, serializer, generator, runner, and governing specifications are unamended and unmodified;
the retained candidate stream is untouched ignored local evidence; `psi_trs.py`, `run_n64_falsifier_v0_1.py`,
and the production TORMENT memory kernel are immutable. No `§0` pointer; no registry or orientation update; no
tags; no commit; no push.*

# TORMENT Brainvision Algebraic N=64 PRIMARY_V0_1 Execution Result v0.1

## 0. Status

**DOCS-ONLY execution-result record.** This document records the outcome of the one authorized `PRIMARY_V0_1`
runner operation. It reruns nothing, invokes no verifier or freezer, evaluates no descriptor, and modifies no
source, test, protocol, authorization, artifact, or production-kernel file. It reports and bounds a completed
operation; it authorizes nothing further.

```text
FORMAL_HOLD_active = True
Mode_0_active      = True
```

Prepared at `HEAD = 12e27d3` (branch `main`, `origin/main = 12e27d3`), tracked working tree clean. At review
time the sole new working-tree entry is this untracked result document.

Brainvision remains offline, prerecorded, quarantined, service-disconnected, non-runtime, non-production,
descriptor-blind, and descriptive-only.

## 1. Lineage

```text
12e27d3  docs(research): authorize algebraic N64 primary execution     <- HEAD, authorization commit
493271b  research(brainvision): implement algebraic N64 primary runner  <- authorization parent
8bc5458  docs(research): specify algebraic N64 primary execution protocol
6a38598  research(brainvision): implement algebraic N64 candidate generator
```

The authorization commit `12e27d3` changed exactly one path:

```text
docs/TORMENT_BRAINVISION_ALGEBRAIC_N64_PRIMARY_V0_1_EXECUTION_AUTHORIZATION_v0.1.md
```

Confirmed by `git show --name-only --format= 12e27d3` and `git rev-parse HEAD^ = 493271b`. The runner,
generator, serializer, protocol, and tests therefore stood exactly as committed at `493271b` throughout the
operation, satisfying authorization precondition §4.2.

## 2. Sources and artifacts inspected

Read completely for this record:

```text
docs/TORMENT_BRAINVISION_ALGEBRAIC_N64_PRIMARY_V0_1_EXECUTION_PROTOCOL_v0.1.md
docs/TORMENT_BRAINVISION_ALGEBRAIC_N64_PRIMARY_V0_1_EXECUTION_AUTHORIZATION_v0.1.md
research/brainvision/run_algebraic_n64_primary_v0_1.py
research/brainvision/algebraic_direct_sum_n64_candidate_generator_v0_1.py
research/brainvision/witness_canonical_json_v0_1.py
```

Generated artifacts inspected read-only:

```text
research/brainvision/results/algebraic_n64_primary_v0_1/algebraic_n64_primary_v0_1_replay_result.json
research/brainvision/results/algebraic_n64_primary_v0_1/algebraic_n64_primary_v0_1_candidate_stream.json
research/brainvision/results/algebraic_n64_primary_v0_1/algebraic_n64_primary_v0_1_summary.txt
```

These are ignored local evidence under `research/brainvision/.gitignore`. They were not modified,
reserialized, relocated, staged, committed, or pushed.

## 3. Authoritative execution transcript

```text
pre-run path checks:
    FINAL_PATH_ABSENT
    STAGING_PATH_ABSENT

exact command:
    python research\brainvision\run_algebraic_n64_primary_v0_1.py

PROCESS_EXIT_CODE = 0

post-run repository state:
    ## main...origin/main

post-run HEAD = 12e27d3
```

Exit code 0 means the runner published a complete permitted artifact set atomically with no runner-level
validation failure. Per the runner's own contract it is a statement about the runner, not a scientific
outcome. No staging directory remains, confirming the publication rename completed cleanly.

## 4. Frozen replay outcome

```text
profile = PRIMARY_V0_1

authoritative_operation = True
downstream_freeze_eligible = True
byte_identical = True

terminal_status = budget_exhausted
derived_termination_reason = MAX_CANDIDATE_RECORDS_EMITTED

candidate_count = 20000
candidate-stream artifact written = True

failure_code = absent
failure_stage = absent
runner_validation_failure = none
```

`derived_termination_reason` is a runner-derived human-only label, not a generator field. It is confirmed by
the artifact data: `candidate_records_emitted = 20000` equals the frozen record ceiling, while
`parameter_tuples_examined = 35505` does not equal the tuple ceiling `3395616`. The record ceiling therefore
uniquely determines the reason under the frozen precedence, and the protocol §9.4 expectation that
`MAX_PARAMETER_TUPLES_EXAMINED` is unreachable for `PRIMARY_V0_1` is not contradicted.

## 5. Envelope payload hashes

These are SHA-256 over canonical **payload** bytes only, nonrecursively. They are **not** whole-file hashes
and must never be substituted for one.

```text
generator_identity_sha256 =
adb06d286bced1e127d413510efb78187076f326c1b6377e6e4d92c2ebc819b8

generator_configuration_sha256 =
0d534874c91e904e869bfa379422cf64082b024a1f51f3b00f3c8ca196d4d5d0

structural_budget_sha256 =
d4a840de6cf0621af2b8ba12821ca5e0773e00388ab4c25936a16c606d6d3c21

source_identity_sha256 =
19ebd55d99adeb0481a570fb26d272bbfb314fd3c2bb01177b765d8489ff0408

run1_candidate_stream_sha256 =
70763a2ebbf7ea71267553debee2bf79c2ed3b7b0c016d9a903161074e7bf8c5

run2_candidate_stream_sha256 =
70763a2ebbf7ea71267553debee2bf79c2ed3b7b0c016d9a903161074e7bf8c5

candidate_stream_sha256 =
70763a2ebbf7ea71267553debee2bf79c2ed3b7b0c016d9a903161074e7bf8c5

generator_replay_result_sha256 =
5fd2cff72950fd3c5207a4d72950d8f5094ef0b61092ea25bd7d2e668e9c3632
```

The equality of `run1_candidate_stream_sha256`, `run2_candidate_stream_sha256`, and `candidate_stream_sha256`
is the replay identity: both authoritative runs produced the same canonical payload bytes, and the retained
stream is that payload.

## 6. Whole-file hashes

SHA-256 over the complete canonical JSON **file** bytes as written to disk — a different byte domain from
§5.

```text
algebraic_n64_primary_v0_1_replay_result.json =
ad90eb43bfb907f7aac2b615910b0b77dc71c8d1fd10e89c02e6d0f8fa02f8fc

algebraic_n64_primary_v0_1_candidate_stream.json =
00a816364ddcfc9d06dc8ce1225f58bca013e96a8914ff1eb665004b39ed949b
```

**Both `certutil` results matched the runner summary.** The operator verified each JSON artifact with
`certutil -hashfile ... SHA256`, and each value equals the whole-file hash the runner printed to stdout and
wrote into `algebraic_n64_primary_v0_1_summary.txt`. The bytes on disk are the bytes the runner believed it
wrote.

The committed protocol requires whole-file hashes for JSON artifacts only. It establishes no canonical hash
for the summary, and this record creates none.

## 7. Independent verification performed for this record

Read-only recomputation from the retained artifacts, without rerunning the generator:

```text
all four identity/configuration/budget/source envelope payload hashes  recomputed and matched
candidate_stream_sha256 recomputed from the inner payload               matched
generator_replay_result_sha256 recomputed from the replay payload       matched
both whole-file digests recomputed from file bytes                      matched §6
replay file bytes == canonical_json_bytes(parsed replay envelope)       True
stream file bytes == canonical_json_bytes(parsed stream envelope)       True
standalone stream file bytes == canonical bytes of the EMBEDDED
    candidate_stream_envelope inside the replay result                  True
replay envelope has exactly two top-level keys                          True
both JSON files end at the final closing token, no trailing newline     True
summary uses LF endings and exactly one trailing newline                True
```

Structural conformance of the retained stream:

```text
records present                       20000
candidate_count                       20000   (equals len(records))
candidate_generation_index sequence   exactly 0..19999, zero-based, monotone, gap-free
raw_support_A / raw_support_B weight  12 for every record
distinct raw (A,B) pairs              20000   (no duplicate pair retained)
maximum parameter_tuple_index         35504   (consistent with 35505 tuples examined)
schema_name                           brainvision_descriptor_blind_candidate_stream
verification_mode / N                 PRIMARY_CANDIDATE_N64 / 64
failure_record                        null
```

These are structural and serialization conformance checks only. **No witness predicate was computed**: no
autocorrelation, difference multiset, one-step table, transition multiset, triple array, primitive period,
affine image, or equivalence class was evaluated at any point in preparing this record.

## 8. Structural counters

Both runs, reported independently and exactly as retained:

```text
run 1:
  parameter_tuples_examined = 35505
  colliding_parameter_tuples_rejected = 15505
  direct_tuples_found = 20000
  exact_duplicate_candidates_skipped = 0
  candidate_records_emitted = 20000

run 2:
  parameter_tuples_examined = 35505
  colliding_parameter_tuples_rejected = 15505
  direct_tuples_found = 20000
  exact_duplicate_candidates_skipped = 0
  candidate_records_emitted = 20000
```

The two mappings are identical, conform to the exact five-key strict-integer nonnegative schema, and the
arithmetic identity holds:

```text
15505 rejected + 20000 direct = 35505 examined
```

`exact_duplicate_candidates_skipped = 0` means every direct parameter tuple in the traversed prefix produced a
raw pair not already emitted; it is a statement about deduplication, not about distinctness under any
equivalence group. These counters describe traversal bookkeeping only. **No witness validity is inferred from
them.**

## 9. Artifact inventory

```text
research/brainvision/results/algebraic_n64_primary_v0_1/
  algebraic_n64_primary_v0_1_candidate_stream.json    6 421 010 bytes
  algebraic_n64_primary_v0_1_replay_result.json       6 424 723 bytes
  algebraic_n64_primary_v0_1_summary.txt                    2 226 bytes

research/brainvision/results/.algebraic_n64_primary_v0_1.staging/    absent
```

Three files: the complete permitted set for a freeze-eligible outcome. The summary size and listing are
descriptive inventory only.

## 10. What this operation established

```text
the replay operation was deterministic
the two candidate streams were byte-identical
the frozen 20,000-record ceiling was reached
the retained candidate stream is a deterministic prefix
the stream is downstream-freeze eligible
```

Equal complete periodic autocorrelation for each retained `(A, B)` pair is the **construction property already
supplied by the accepted algebraic direct-sum generator route**, holding by theorem for collision-free
`A = U+V`, `B = U−V` in `Z_64`. This operation neither strengthened nor independently confirmed it, and it is
not complete witness validity. It is one predicate among several, and the remaining predicates were not
evaluated.

## 11. What this operation did not establish

```text
the full 3,395,616-tuple domain was not exhausted
the 20,000 records are not declared witnesses
no primitive-period predicate was evaluated by this operation
no affine or affine-plus-complement inequivalence was established
no direct-complement predicate was established
no triple-array G-nonalignment was established
no mutual family G-inequivalence was established
no three-class autocorrelation diversity was established
no K=3 witness family was frozen
no PsiTRS evaluation occurred
no scientific, perceptual, temporal-order, or production-vision inference is authorized
```

Quantitatively, `35505` of `3395616` normalized parameter tuples were examined — approximately **1.05 percent**
of the frozen domain. The retained stream is the deterministic prefix of a traversal that stopped at the record
ceiling, not a survey of the construction family. A later negative result from any downstream stage would be
bounded by this prefix, and nothing here licenses a claim about the unexamined remainder.

## 12. Authorization consumption

```text
PRIMARY_V0_1 execution authorization at 12e27d3 = consumed
automatic retry = prohibited
second execution = not authorized
```

The operation reached the committed replay call, which consumes the authorization by the rule recorded in
authorization §5.1. Success does not preserve, renew, or extend it. Any further execution requires a new
authorization record.

## 13. Authority state after this result record

```text
DOCUMENTATION_AUTHORIZED = True
PRIMARY_V0_1_EXECUTION_RESULT_DOCUMENTED = True

PRIMARY_V0_1_EXECUTION_AUTHORIZED = False
CANDIDATE_STREAM_PRODUCTION_AUTHORIZED = False

PRIMARY_V0_1_REPLAY_AUTHORITATIVE = True
PRIMARY_V0_1_REPLAY_BYTE_IDENTICAL = True
PRIMARY_V0_1_CANDIDATE_STREAM_PRODUCED = True
PRIMARY_V0_1_DOWNSTREAM_FREEZE_ELIGIBLE = True

FREEZER_INVOCATION_ON_GENERATOR_OUTPUT_AUTHORIZED = False
N64_WITNESS_GENERATION_AUTHORIZED = False
N64_WITNESS_FAMILY_FREEZE_AUTHORIZED = False
PsiTRS_EVALUATION_AUTHORIZED = False
SCIENTIFIC_INFERENCE_AUTHORIZED = False
```

**Clarification of `PRIMARY_V0_1_DOWNSTREAM_FREEZE_ELIGIBLE = True`.** This is an artifact-interface state: the
retained stream has the shape a freezer could later be asked to consider — authoritative, byte-identical, an
accepted-schema non-empty stream with an extractable terminal status. It is **not** authorization to invoke the
freezer, and it is **not** a finding about any candidate in the stream. Eligibility describes the container,
never its contents.

## 14. Immutable and untouched surfaces

No modification occurred to:

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

```text
freezer invoked = False
verifier separately invoked = False
PsiTRS invoked = False
scientific interpretation performed = False
generated artifacts committed = False
```

The post-run repository status remained clean because `research/brainvision/results/` is ignored, exactly as
the protocol anticipated.

## 15. Conclusion

```text
DOCUMENTATION_AUTHORIZED = True
PRIMARY_V0_1_EXECUTION_RESULT_DOCUMENTED = True

PRIMARY_V0_1_EXECUTION_AUTHORIZED = False
CANDIDATE_STREAM_PRODUCTION_AUTHORIZED = False

PRIMARY_V0_1_REPLAY_AUTHORITATIVE = True
PRIMARY_V0_1_REPLAY_BYTE_IDENTICAL = True
PRIMARY_V0_1_CANDIDATE_STREAM_PRODUCED = True
PRIMARY_V0_1_DOWNSTREAM_FREEZE_ELIGIBLE = True

FREEZER_INVOCATION_ON_GENERATOR_OUTPUT_AUTHORIZED = False
N64_WITNESS_GENERATION_AUTHORIZED = False
N64_WITNESS_FAMILY_FREEZE_AUTHORIZED = False
PsiTRS_EVALUATION_AUTHORIZED = False
SCIENTIFIC_INFERENCE_AUTHORIZED = False
```

Explicitly:

```text
one authorized PRIMARY_V0_1 runner operation occurred
the authorization was consumed
the replay was authoritative and byte-identical
a 20,000-record budget-exhausted candidate stream was produced
both JSON whole-file hashes were independently verified
no retry occurred
no freezer was invoked
no witness or family was accepted
no PsiTRS evaluation occurred
no production-kernel file was modified
```

*End — TORMENT Brainvision Algebraic N=64 PRIMARY_V0_1 Execution Result v0.1. Docs-only, non-executing,
non-authorizing. Records one completed generator operation and its bounds; accepts no witness, freezes no
family, evaluates no descriptor, and makes no scientific claim. The retained artifacts are ignored local
evidence and were not modified, staged, committed, or pushed. Freezing, verification, ΨTRS evaluation, and
scientific interpretation remain separate closed stages requiring separate authorization. No `§0` pointer; no
registry or orientation update; no tags; no commit; no push.*

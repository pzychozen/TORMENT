# TORMENT P4 verifier reconciliation

Starting HEAD and `origin/main` were `ce2fac96ddaa84d7a788a2133a9be706199b30b4`; the tracked worktree was clean.

## Finding and dependency map

`RootNormalizationResult.root_normalization_ready` is produced by
`migration/root_normalization.py`.  Its canonical meaning is **generalized staging-runtime
readiness**: all required source semantics became usable native runtime semantics.  History
(`0246c53a`, then the certified-exception clarification in `7bc367c9`) shows that this is
not the later-cutover disposition predicate.  P3 correctly makes it false when terminal B2
or B4 certified exceptions exist.

```
root_normalization_ready -> root_blocker5_binding._require_normalization_complete
                         -> RootCompletionVerification / completion witness digest
                         -> P5 enter_root_core_pending, P6 activate_root_core,
                            P7 activate_root_external_selector (transitive P4 gate)
```

The old P4 predicate required `ready` and rejected every `partial_activation`.  The new
predicate requires source-manifest/topology closure, no reason codes, memory and motif
disposition closure, then accepts either (a) ready/non-partial runtime closure or (b) the
exact `P3_DISPOSITION_CLOSED_WITH_CERTIFIED_EXCEPTIONS` class with at least one certified
B2/B4 refusal and, when partial, certified partial-motif authority closure.  This preserves
the stored readiness and P3/certified-refusal semantics; it does not alter P3 routing,
runtime-leak proofs, P5, P6, or P7.

No downstream source consumer separately required `root_normalization_ready`; completion
receipts retain the raw readiness fact only within their closure digest.  P5/P6/P7 therefore
have no separate stale source predicate.  The known generic post-activation B5-A5 failure is
`NOT_ESTABLISHED` as related: it occurs in a distinct generic controller after activation.

## Validation

`P4_VERIFIER_MISMATCH_CONFIRMED = YES`.

The focused A--G contract passed (`7 passed`): full normalization and lawful certified
exception closure pass; incomplete closure, runtime leak reason, unaccounted memory,
motif-closure failure, and unexpected native public authority refuse.  Actual disposable
P3 B2 and B4 semantic-gap tests passed (`2 passed`) and retain the negative-runtime proof.

The copied P4-only rehearsal bound the preserved real-P3 carrier to a fresh copied root and
produced a P4 completion witness digest
`5e415920dc34d0721a950c5e44fe4d31429b2f65afe1f33b7e08a6259075122d` with:

- 2076 B1M; 2041 admitted; 35 certified B2 refusals
- 450 motifs: B4A 183, B4B 233, B4C 0, B4P 11, 23 certified B4 refusals
- `root_complete=true`, `root_ready=false`, memory/motif closure true,
  class `P3_DISPOSITION_CLOSED_WITH_CERTIFIED_EXCEPTIONS`, selector generation 7 /
  `CUTOVER_PENDING`.

Changing copied fixture `root_memory_disposition_closed` to false produced
`ROOT_OFFLINE_CUTOVER_COMPLETION_REFUSED`.

`CLAUDE_ADVERSARIAL_REVIEW = UNAVAILABLE` (no Claude connector was installed). Independent
bounded review found the new predicate fail-closed: no false-ready blanket pass, no accepted
reason code, incomplete partition, unclosed motif, uncertified partial authority, or changed
public authority.

The attempted broader pytest aggregate hit a Windows interpreter `pathlib` access violation
during collection; it is recorded as an environment failure, not a patch result. `git diff
--check` is required before commit.

`REAL_ROOT_WRITE = NONE`; `REAL_P4_RETRY = NO`; `P5_EXECUTED = NO`; `P6_EXECUTED = NO`;
`P7_EXECUTED = NO`; `NATIVE_ACTIVATION = NO`.  The initial full copied-P3 replay was stopped
after excessive local re-embedding time; the completed rehearsal is P4-only and uses the
preserved, independently verified P3 carrier.

Terminal law: `DISPOSITION_CLOSURE_WITH_LAWFUL_CERTIFIED_EXCEPTIONS_IS_COMPLETE`.
`ROOT_NORMALIZATION_READY_SEMANTICS_PRESERVED = YES`.
Next authorization boundary: `REAL_P4_READMINISTRATION`.

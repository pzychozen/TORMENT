# TORMENT SQLite Database Convergence — Post-P4 / Pre-P6 Activation-Rehearsal Review

## Result

This review closes the previously known P0–P8 rehearsal failure as a stale
test expectation.  It also found a separate, production-shaped post-P7
runtime-contract defect.  The defect is fail-closed, introduces no legacy
fallback or dual authority, and does not alter the completed P4 evidence; it
does block real P6 until the P2/P3-to-native-public private-motif-domain
contract is reconciled.

```text
POST_P4_PRE_P6_REVIEW = BLOCKED
KNOWN_POST_ACTIVATION_FAILURE = CLOSED
KNOWN_FAILURE_PRIMARY_CLASSIFICATION = STALE_TEST_EXPECTATION
SEPARATE_POST_P7_RUNTIME_BLOCKER = PRIVATE_MOTIF_DOMAIN_CONTINUATION_GAP
P5_READINESS = READY
P6_READINESS = BLOCKED
REAL_ROOT_UNCHANGED = YES
```

## Required result record

```text
STARTING_HEAD = 5c25bf6aa23b6e405e5f1436814c3e79df9d175e
FINAL_HEAD = recorded by the commit which adds this review
ORIGIN_MAIN = 5c25bf6aa23b6e405e5f1436814c3e79df9d175e at review start
TRACKED_WORKTREE = clean at start; this review changes only the stale-test assertion and this record

KNOWN_FAILURE_TEST = tests/test_b5_a5_offline_cutover_rehearsal.py::test_offline_cutover_full_rehearsal_abort_and_post_active_refusal
KNOWN_FAILURE_ASSERTION = _tree_digest(workspace_root) == legacy_before
KNOWN_FAILURE_FIRST_PHASE = ordinary native runtime behavior immediately after POST /agent/ingest, after P7
KNOWN_FAILURE_EXPECTED = 6a092… (pre-native full workspace-tree digest)
KNOWN_FAILURE_OBSERVED = 484a… (post-ingest full workspace-tree digest)

FAILURE_REPRODUCED = YES
FAILURE_PRIMARY_CLASSIFICATION = STALE_TEST_EXPECTATION
P4_RECONCILIATION_CAUSAL = NO

P5_STALE_NORMALIZATION_ASSUMPTION = NO
P6_STALE_NORMALIZATION_ASSUMPTION = NO
P7_STALE_NORMALIZATION_ASSUMPTION = NO

DUAL_WRITE_OBSERVED = NO
DUAL_READ_AUTHORITY_OBSERVED = NO
LEGACY_FALLBACK_EXPECTED_BY_TEST = NO
LEGACY_FALLBACK_PRESENT_IN_RUNTIME = NO

POST_ACTIVATION_CERTIFIED_REFUSAL_MEMORY_LEAK = NO
POST_ACTIVATION_CERTIFIED_REFUSAL_MOTIF_LEAK = NO

POST_ACTIVATION_MEMORY_RETRIEVAL = FAIL_CLOSED_ON_PRODUCTION_SHAPED_COPY
POST_ACTIVATION_TEXT_SEARCH = FAIL_CLOSED_ON_PRODUCTION_SHAPED_COPY
POST_ACTIVATION_VECTOR_SEARCH = FAIL_CLOSED_ON_PRODUCTION_SHAPED_COPY
POST_ACTIVATION_WRITE_CREATE = FAIL_CLOSED_ON_PRODUCTION_SHAPED_COPY
POST_ACTIVATION_REINFORCEMENT = NOT_REACHED_AFTER_FAIL_CLOSED_QUERY_CONTEXT
POST_ACTIVATION_CHARACTER = NOT_REACHED_AFTER_FAIL_CLOSED_QUERY_CONTEXT
POST_ACTIVATION_MOTIF = NEGATIVE_PROOF_PASS; positive active-reader sweep not reached
POST_ACTIVATION_RESTART_RECOVERY = NOT_REACHED_AFTER_FAIL_CLOSED_QUERY_CONTEXT

IMPLEMENTATION_CHANGE_REQUIRED = YES, before P6
IMPLEMENTATION_CHANGE_SCOPE = cross-phase P2/P3-to-B5-A3/native-public private-motif-domain continuation; no change made under this order
CLAUDE_ADVERSARIAL_REVIEW = NOT_REQUIRED (no production P5/P6/P7 change proposed or made)

DISPOSABLE_P0_P8_REHEARSAL = PASS
GIT_DIFF_CHECK = PASS

REAL_ROOT_WRITE = NONE
REAL_P5_EXECUTED = NO
REAL_P6_EXECUTED = NO
REAL_P7_EXECUTED = NO
REAL_NATIVE_ACTIVATION = NO

P5_READINESS = READY
P6_READINESS = BLOCKED
TERMINAL_STATUS = BLOCKED_ON_PRIVATE_MOTIF_DOMAIN_CONTINUATION_GAP
NEXT_AUTHORIZATION_BOUNDARY = REAL_P5_ONLY, if separately authorized; real P6 remains prohibited
```

The abbreviated two tree-digest values above identify the original recorded
assertion; the exact pre/post strings are retained in the failed disposable
pytest output.  They are intentionally not treated as a memory-authority
digest.

## 1. The known post-activation failure

The original test froze a digest of every workspace file before P0 and
required that the whole tree be byte-identical after native public behavior.
Instrumentation at every lifecycle boundary showed no divergence through P0,
P2, P3, P4, P5, P6, P7 selector activation, native health, `/agent/query`, or
`/retrieve`.  The first difference was immediately after the ordinary native
`POST /agent/ingest`.

The write did not touch legacy private nodes, embeddings, memory events, or
motif source bytes.  It lawfully created or advanced retained external-owner
facts:

- private trajectory chunks, manifest/boundaries, and diagnostics;
- `bridge_events.jsonl` and `bridges.json`; and
- the existing external `roles.json` owner.

The native public path was separately guarded so every `MemoryGraph`
construction, read, and writer call would fail the test.  The guard reported
zero legacy calls.  Those retained JSON/JSONL owners are explicitly outside
SQLite canonical-memory authority, so the full-tree equality was the stale
expectation.

The test now retains the full-tree comparison at P0, where legacy public
health is the subject, and uses `_legacy_memory_authority_digest` after P7.
The new digest covers private legacy-memory files and shared legacy motif
sources while intentionally excluding retained trajectory, bridge, and role
owners.  It does not weaken native-memory or legacy-fallback checks.

On a fresh external `--basetemp`, the corrected exact rehearsal passed:

```text
tests/test_b5_a5_offline_cutover_rehearsal.py::test_offline_cutover_full_rehearsal_abort_and_post_active_refusal
1 passed in 13.14s
```

This is the one and only primary classification for the known assertion:
`STALE_TEST_EXPECTATION`.

## 2. Production-shaped P4 to P7 copy rehearsal

No real-root lifecycle function was called.  A 1.082 GB read-only copy of the
real `data/` root was made beneath
`C:\TORMENT\TORMENT_administration\post-p4-pre-p6-review-20260909\production-shaped-copy-run2\data`.
The copy used the actual P4 closure: 35 B2 certified memory refusals, 23 B4
dependent motif refusals, corrected core
`f21c730f-5222-4aa8-9a5f-1c1188456df3`, Envelope D
`e4e510131cc341375485605bf1ead86aff684a1ca938e26fdbe221bbf0673ceb`, and
P4 closure digest
`5e415920dc34d0721a950c5e44fe4d31429b2f65afe1f33b7e08a6259075122d`.

The copy crossed P5, P6, execution of the frozen disposition plan through a
disposable no-mutation adapter, and P7.  It demonstrated the intended
selector-last and no-rollback transition:

| Stage | Core role / deployment | Ever active | Selector / public posture | Authority |
| --- | --- | --- | --- | --- |
| P4 | `STAGING` / `LEGACY_ACTIVE` | false | generation 7, `CUTOVER_PENDING`, maintenance-only | no native public authority |
| P5 | `STAGING` / `CUTOVER_PENDING` | false | generation 7, `CUTOVER_PENDING`, maintenance-only | reversible pending core only |
| P6 | `ACTIVE_CORE` / `NATIVE_ACTIVE` | true | generation 7, `CUTOVER_PENDING`, maintenance-only | core active; selector still excludes public traffic |
| P7 | `ACTIVE_CORE` / `NATIVE_ACTIVE` | true | generation 8, `NATIVE_ACTIVE` | selector-owned native public authority |

At P6, `safe_root_pending_abort` refused, confirming the durable point of no
return.  P7 was the final selector operation and binds the exact disposition
receipt.  No stage exposed two public owners, two write owners, or two read
owners.  There is no automatic post-native rollback.

Static tracing confirms that P5 entry, P6 core activation/disposition, and P7
selector activation use the canonical P4 verification binding; none checks
`ROOT_NORMALIZATION_READY == TRUE`.  The reconciled state remains correct:
`ROOT_DISPOSITION_CLOSURE=TRUE`, `ROOT_COMPLETION_VERIFIED=TRUE`, and
`ROOT_NORMALIZATION_READY=FALSE` for the certified P3 exception class.

## 3. Certified exceptions after the disposable activation

The activated copy retained the 35 B2 refusal objects only as historical R1
evidence.  A read-only structural audit found:

```text
certified refusals = 35
current historical R1 = 35
native ordinary successors = 0
other representations = 0
COMPAT_EMBEDDING runtime representations = 0
READY/USABLE runtime representations = 0
historical embedding captures = 32
lawful no-capture historical records = 3
```

The three no-capture cases are allowed by the frozen refusal proof; the proof
requires no native runtime representation, not a capture for every historical
record.  The staging-only vector proof correctly refuses an `ACTIVE_CORE` and
was not misreported as an active-runtime result.

The active copy's native motif reader independently passed the complete B4
negative proof:

```text
ACTIVE_SELECTOR = generation 8 / NATIVE_ACTIVE
B4 refused motifs = 23
target alias absences = 23
runtime reader absences = 23
```

Thus activation did not convert certified historical evidence into native
memory/motif authority.  The separate query-context blocker below is
fail-closed, so it cannot expose a refused result through a fallback path.

## 4. Newly discovered post-P7 runtime blocker

The production-shaped activated copy successfully created a
`NativeProductionResourceOwner` from the exact native agreement.  Opening a
query context for an exact admitted workspace then failed with:

```text
QualifiedQueryReadModelError:
admitted private lane lacks truthful motif-domain evidence
```

This is systemic, not an isolated `ryuki` fixture.  A read-only check of the
real P4 root (which remains generation 7 / `CUTOVER_PENDING`) found 76 private
runtime plans and all 76 carry `motif_domain_id=None`, including
`orchard/aria` and real source-bearing `ryuki/ryuki_nox`.

The absence is intentional at P2 source-plan recovery:
`root_p2_source_plan_recovery.py` states that private scopes deliberately
retain `motif_domain_id=None`, with Character witness-domain derivation kept
separate.  But root-v2 recovery in `production_native_owner.py` reconstructs
the active descriptor directly from that frozen P2 plan tuple.  In turn,
`query_read_model._private_motif_domains` requires every private plan to
carry a nonempty domain.  `NativePublicTormentRuntime._workspace_view`,
`query`, private ingest, and the native private post-write route call the
same helper.

Therefore P5/P6/P7 correctly preserve authority and P4 reconciliation, but
their resulting native-public route is not internally usable for the real
P4 plan.  This is a direct cross-phase continuation contradiction, not a
reason to change the meaning of `ROOT_NORMALIZATION_READY`, and not an
argument to restore legacy fallback.

The correct repair needs a separately authorized P2/P3-to-B5-A3 continuation
decision: either persist an authoritative private motif-domain binding that
the root-v2 recovery can verify, or explicitly establish a different
qualified no-private-motif public contract.  Choosing a legacy domain by
heuristic after activation would violate the frozen authority model.  No such
production change was made here.

## 5. Validation and environment notes

The following focused suites were run under `conda activate torment`, with a
fresh external pytest base and cache provider disabled:

```text
tests/test_b5_a3_production_native_resource_owner.py
tests/test_b5_a4r2_native_public_ingest_recovery.py
31 passed in 20.48s

tests/test_b5_a5_offline_cutover_rehearsal.py::test_offline_cutover_full_rehearsal_abort_and_post_active_refusal
1 passed in 13.14s
```

An initial owner-suite command used the machine-default pytest base and was
blocked by an ACL on `C:\Users\Notandi\AppData\Local\Temp\pytest-of-Notandi`
before test setup.  It was an environment-only test-launch artifact; the
fresh external base produced the passing result above.

Earlier focused P4/P5/P6/P7 synthetic contracts, exact P0–P8 rehearsal, and
external-pending admission recovery remain passing evidence.  The synthetic
owner/public fixtures all supply a private motif domain; they do not cover
the real-root P2 continuation where every private plan intentionally omits
one.  That is the coverage gap exposed by this review.

`git diff --check` passes.  The only repository changes are the bounded
stale-test expectation repair and this review record.  All audits and
rehearsals used disposable external state; there was no real-root write,
activation, selector mutation, or core-authority mutation.

## 6. Readiness decision

P5 remains ready because it only enters the reversible pending-core state and
its real-root P4 input is complete.  It does not grant public native traffic,
and the checked controller preserves safe pending abort before P6.

P6 is blocked.  It would make the core irrevocably active while the current
real-root P2/P3 continuation cannot satisfy the native public/private query
contract.  The next permitted work is a bounded cross-phase contract
reconciliation and disposable regression suite for authoritative private
motif-domain continuation.  Only after that work passes may real P6 be
reconsidered.

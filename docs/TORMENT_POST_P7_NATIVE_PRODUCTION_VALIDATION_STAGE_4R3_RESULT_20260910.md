# TORMENT — Stage 4R3 trajectory crash-partial reconciliation

2026-09-10 UTC. **CASE A — verifier expectation was wrong.**
`POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_4R3 = PASS` and
`POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_4 = PASS`.
`SQLITE_MIGRATION_FULLY_VALIDATED = CANDIDATE_YES`, pending final review.

The frozen lifecycle intentionally retains prior-epoch crash partials in the
ordinary artifact root as non-authoritative evidence. Restart creates a new
epoch and lawful writer session; it does not adopt or seal the predecessor's
tail. A recovered native deployment therefore need not have a wholly SEALED
trajectory root. Both ordinary whole-root verifier modes continue to refuse
the preserved A/B roots. Their refusals have not been suppressed or repaired.

R3 qualifies the separate facts required by this order: preserved and classified
orphans, valid published chunk hashes/frames, accounted physical sequence gaps,
lawful replacement authority and ordinary-consumer refusal. This is a bounded
test/evidence composition, not a new production state or verifier mode. The R2
report and its SQLite conclusions remain unchanged.

## Git and execution boundary

Starting HEAD = origin/main = actual remote main =
`5e2bf2ac449a91f60613d554a4a65f7ddd1d08ef`, branch `main`, tracked worktree clean.
The only repository additions are this report and
`tests/test_trajectory_v2_crash_contract.py`. There is no production correction.
The final commit, remote equality, clean tracked worktree and preserved unrelated
untracked listing are recorded in external `publication.json` and the final return.

All project Python ran through Windows CMD with `conda activate torment`, using
`C:\Users\Notandi\miniconda3\envs\torment\python.exe` and SQLite 3.53.4.
No service was launched in R3. No BGE, conversational model, generative provider
or external AI API was used. Native memory transactions, selector/core authority,
writer fencing, generations, Model D, Character and world/kernel mathematics
were not changed.

## Frozen sources and ownership

The narrow review is bound by hashes in external `source_review.json`.

| Source at starting HEAD | Governing facts |
| --- | --- |
| `torment_service/kernel/trajectory_v2.py`, lines 1, 350–586 | V2 is non-authoritative, best-effort evidence. Writer startup discovers physical sequences and epochs; preserves prior partials; opens a new file exclusively; appends frames; seals only its own active chunk. |
| Same file, lines 589–825 | Only `sealed` and `live` verifier modes exist. Both check manifests, hashes, frame identities and boundaries. Sealed rejects every partial; live permits only one current structurally complete tail. Both ordinary iterators verify before yielding. |
| `tests/test_trajectory_v2.py`, lines 108–140 | A current live tail is accepted only in live mode; clean close makes it sealed. The existing restart test deliberately retains a crash partial and expects invalid live verification with `ORPHANED_CRASH_PARTIAL`. Both tests were freshly run in R3. |
| `torment_service/substrate/native_trajectory_evidence_runtime.py`, lines 38–145, 157–209 | External writer owns no canonical memory. Initialization, step and close use the writer authority guard. It never refreshes an already-fenced token; close seals only the selected writer's V2 tail and failures remain diagnostic. |
| `torment_service/substrate/trajectory_writer_handoff.py`, lines 719–890 | An artifact effect validates current scope/family/writer/session/generation before entry. A different native session advances generation; stale tokens are refused. These are write permissions, not authority granted to trajectory contents. |
| `torment_service/substrate/native_world_runtime.py`, lines 217–262, 400–443 | Reconstruction obtains current native source snapshots. Trajectory evidence is an output after physics, never a source for world reconstruction. |
| `torment_service/sqlite_index.py`, lines 750–761 | The optional diagnostic cache rebuild validates complete V2 history before clearing/replacing cache tables. A refused crash root cannot silently become committed cache history. |
| `docs/TRAJECTORY_V2_QUALIFICATION.md` | V2 changes diagnostic persistence only. Qualified sealed runs closed gracefully with finalized chunks and no partials. |
| `docs/7G5E4D_D3_SHARED_TRAJECTORY_EVIDENCE.md`, frozen evidence law and recovery sections | Seal order is flush, fsync, close, rename, hash, manifest publication. Recreated world state loads native payload, never the latest trajectory frame/label. |
| `docs/TORMENT_MEMORY_SUBSTRATE_PHASE_9D_I4E_SRG_WORLD_TRAJECTORY_CHECKPOINT_PARITY_v0.1.md`, owner and restart tables | Private evidence is process-owned and external; restart loses live overlays to their durable native baseline. External trajectory files remain non-authoritative. |

No frozen requirement to seal, move, quarantine, delete or retire an orphan on
restart was found in these directly governing records and implementations.
The explicit preserving writer and expected-invalid restart test establish the
bounded contract; a globally SEALED post-crash root is not its recovery target.

## Actual lifecycle and state machine

`SEALED` is a verification predicate, not an authority-database phase. Likewise,
the labels below describe existing artifacts or existing verifier diagnostics;
R3 adds no production state enum.

| State / existing diagnostic | Writer may append? | Included in sealed chain? | Runtime authoritative? | Must be preserved? | Correct verification |
| --- | --- | --- | --- | --- | --- |
| `ACTIVE_OPEN_TAIL` | Only the owning open writer, with current native authority when governed | No; it has no sealed manifest entry | NO | Retain until that writer lawfully seals it; no discard-to-pass | `live` can PASS for one current, complete tail plus otherwise valid evidence; `sealed` refuses |
| `SEALED_CHUNK` (`CHUNK_FINALIZED`) | No append to the finalized file | Yes, when its manifest/hash/frame checks pass | NO; diagnostic history only | Retain under existing `full_v1` evidence behavior | Entry checks, plus whole-root `sealed` only if all root conditions pass |
| `ORPHANED_CRASH_PARTIAL` | New writer does not reopen it; old native token is fenced | No | NO | YES, in place; startup preserves it and records its prior epoch | Ordinary `sealed` and `live` refuse; R3 separately accounts for this bounded crash witness |
| `ORPHAN_CHUNK` | No; this is a physical `.trj2` absent from the manifest | No published chain membership | NO | No automatic deletion/disposition is implemented | Both root modes refuse; R3 also refuses this unaccounted condition |

The actual transitions are:

1. Startup chooses the next sequence from the maximum manifest/physical
   `.partial`/`.trj2` sequence and the next epoch from persisted boundary/chunk
   evidence. It preserves and diagnoses earlier partials, then records the new
   `EPOCH_START` where boundary evidence permits it.
2. The first successful frame opens a new epoch-local `.partial` with `xb`.
   Each emitted frame is flushed and uses `(epoch, frame_seq)` identity;
   logical `step` remains diagnostic. Frame append is not a chunk seal.
3. Chunk rollover or clean close flushes and fsyncs the owner's handle, closes
   it, renames to `.trj2`, hashes the bytes and publishes the manifest entry.
   The previous hash is the last **published sealed** hash, never an orphan hash.
4. Death before that seal leaves the partial. A later lawful writer chooses a
   later epoch/sequence, diagnoses the old partial and creates a separate file.
   The old artifact has no transition into a new writer's active tail.
5. Clean close of the successor seals the successor's tail only. It leaves the
   prior crash remnant and its corresponding manifest sequence gap intact.

A finalize failure after rename but before manifest publication can leave an
`ORPHAN_CHUNK`; that is a separate existing rejection condition, not what A/B
contain. Unreadable headers and malformed/incomplete frames are also rejected
or diagnosed, not silently skipped into valid history. R3's accepting witness
is deliberately limited to the complete, independently hash-bound A/B partials.
It does not certify recovery of every possible torn-frame/finalize failure.

## Answers to the ten lifecycle questions

| Question | Established answer |
| --- | --- |
| 1. `ACTIVE_OPEN_TAIL` | Live verification recognizes one current-epoch partial with complete frames and correct next sequence/frame identities. Full report validity is required; a notice alone grants no authority. |
| 2. `ORPHANED_CRASH_PARTIAL` | Startup diagnoses an existing partial whose header epoch precedes the new epoch. Live verification reports an epoch mismatch with the current epoch. A/B have older epoch 1 and successor epoch 2. |
| 3. Retention required? | YES for this frozen restart path: `_report_prior_epoch_partials` explicitly preserves crash remnants. |
| 4. Ordinary artifact root? | YES, at the original path under `trajectories/v2/chunks/epoch-.../`; no quarantine path is used. |
| 5. Authority-bearing? | NO. Neither an orphan nor a sealed trajectory is a canonical-memory/world reconstruction authority. Writer tokens separately authorize filesystem effects. |
| 6. Sealed-chain participation? | NO. An orphan has no sealed manifest entry and its hash is not used as a previous sealed hash. |
| 7. Normal restart action? | Acquire/reconstruct lawful native writer authority, advance epoch/sequence, preserve/diagnose the old tail, open a new tail exclusively when a frame is emitted. |
| 8. Post-recovery root? | Preserved prior-epoch crash evidence plus later writer evidence, possibly with intact earlier sealed history. The aggregate root remains unsealed while the orphan remains. This description is not a new production state. |
| 9. Correct verifier? | Existing whole-root `sealed` and `live` remain diagnostic refusals. The authorized bounded R3 assessment composes existing entry/frame/hash checks, exact orphan identity/classification, physical ordering, ordinary-consumer refusal and retained authority evidence. |
| 10. When is whole-root SEALED possible again? | When no partial or unmanifested chunk remains and complete manifest sequence, hashes, frames and boundaries pass the unchanged verifier. A clean root reaches that through normal close. No current automatic path makes the A/B root wholly sealed after orphan retention; later close alone does not do so. |

The structural live classifier does not probe OS process liveness. Immediately
after death, before any newer epoch is recorded, a complete tail can still look
current to that classifier. It is not a liveness/authority attestation. A/B's
preserved death, session and later epoch evidence establish their orphan status.

```text
TRAJECTORY_CRASH_RECOVERY_CONTRACT = EXPECTED_NONSEALED_CRASH_EVIDENCE
ORPHANED_CRASH_PARTIAL_ALLOWED_AFTER_RECOVERY = YES
POST_CRASH_ROOT_EXPECTED_TO_BE_SEALED = NO
TRAJECTORY_RECOVERY_IMPLEMENTATION_GAP = NO
R2_SEALED_VERIFICATION_REQUIREMENT = NOT_APPLICABLE_TO_POST_CRASH_STATE
```

## Exact R2 verifier and preserved A/B evidence

R2 `inspect_state.py` called
`torment_service.kernel.trajectory_v2.TrajectoryV2Verifier(<private artifact root>).verify(mode="sealed")`
for final A/B snapshots. R3 reproduces those complete report objects exactly.
Each still reports `MANIFEST_SEQUENCE_GAP` (expected 1, actual 2) and
`INCOMPLETE_FINAL_CHUNK`. Live mode reports the same sequence gap and
`ORPHANED_CRASH_PARTIAL` instead; neither mode passes.

`R2_VERIFIER_PRECONDITION_SATISFIED_AFTER_CRASH = NO` means the precondition for
expecting a valid **sealed root** was absent. Calling the verifier to diagnose
that state was legitimate. Its refusal is `EXPECTED_STATE_MISMATCH`, not a
SQLite recovery failure, memory transaction failure or demonstrated trajectory
corruption. The strict SEALED predicate is retained exactly.

R2 roots remain at
`C:\TORMENT\TORMENT_administration\post-p7-stage-4r2-20260910\<A or B>\root`.
Each subject artifact root is `workspaces\north\agents\same-agent\private`
under its root. Each retained orphan is
`trajectories/v2/chunks/epoch-00000001/chunk-00000000000000000001.partial`:
213 bytes, one complete frame, two dynamic records.

| Case | Original orphan SHA-256 | Successor sealed chunk SHA-256 |
| --- | --- | --- |
| A | `4a2ee50fc7b12d89c6a054cd47e8c2cdc598529ae0cea1fedf8381206dc623c7` | `6dc904290796cf553898ea1f1f0c4d59ffcf27d9cd37ee9b8b8533b7d79738fa` |
| B | `93e8c63391200bb2fa130d7f64f0cc9cfa1afda481bd5e14080d9268fe40e6c0` | `c0066ee9e0fb10b9c81b15caf96df7f45e9fbf9da3802be431d97108003f729b` |

Both successors are epoch 2, chunk sequence 2, one frame and three records.
Their `previous_chunk_sha256` is empty because no chunk was sealed before the
crash. The physical sequence 1 is accounted for by the retained orphan; it is
not inserted into the sealed manifest or its hash chain.

**Sealed-prefix qualification:** A/B's pre-crash sealed prefix is empty. R3
does not represent that as a nonempty historical-chain demonstration. Every
published successor entry independently passes the existing schema, path,
header, hash, previous-hash link, frame sequence, population and EID checks.
The focused test separately establishes a nonempty pre-crash prefix: seal chunk
1, leave chunk 2 partial, then seal successor chunk 3 in a new epoch. Original
prefix manifest entries and chunk hashes remain identical, and chunk 3 links
to sealed chunk 1. Whole-root verification still refuses its sequence gap and
orphan. `SEALED_PREFIX_HASH_CHAIN_VALID = PASS` has this bounded meaning; it
does not assert complete whole-root sealed continuity for A/B.

| A/B crash-partial fact | Result |
| --- | --- |
| Explicit prior-epoch diagnostic matches path/header | YES |
| Runtime authoritative | NO |
| Referenced by sealed manifest | NO |
| Reused/appended by new writer | NO |
| Can surface as committed trajectory through ordinary consumers | NO |

Both `iter_v2_dynamic_records` and `iter_v2_boundaries`, in both modes, refuse
before yielding from A/B. `TrajectoryChunkReaderV2` can parse a partial for
inspection; this raw parser does not certify it as sealed history. Ordinary
full-history reads/cache rebuilds remain unavailable for these retained crash
roots under current semantics. R3 does not enable partial exports or alter that
consumer behavior.

## Replacement authority and preservation accountability

The unchanged R2 manifests bind the before/final authority snapshots and roots.
R3 checks the same exclusivity key, scope payload, binding and absolute artifact
root before and after recovery. Native generation advances from 4 to 5 in each
case; the sessions are distinct:

| Case | Crashed native session | Recovered native session |
| --- | --- | --- |
| A | `pid:37864:1b51269b-9c67-4cc8-88c6-6687c2f33b0a` | `pid:64644:1a784c37-d4bb-4732-bbbc-1c6e2eb4eaa8` |
| B | `pid:34940:31cab2b3-ae80-4776-b286-a8b32e994aae` | `pid:32108:3f5016c1-ed11-443a-98cd-54d0eb773c8a` |

Recovered initialization, genesis, step and close intents are SETTLED under
the exact successor session/generation. Handoff remains HANDOFF_COMPLETE,
native owner NATIVE_TRAJECTORY_EVIDENCE, legacy session absent and legacy fence
2 unchanged. These retained facts, the ordinary R2 new writes, and the focused
fencing tests establish `POST_CRASH_NEW_WRITER_AUTHORITY = PASS`,
`POST_CRASH_GENERATION_MONOTONICITY = PASS`, `POST_CRASH_ORPHAN_REUSE = NO`.

The `.partial` binary itself carries sequence/epoch/frame identities, not an
embedded coordinator session token. R3 does not invent such a field. The saved
R2 death records, exact scope/session intents, baseline/final hashes, original
paths and new-epoch diagnostics jointly retain the crash's accountability and
the reason the tail is non-authoritative. No R2 authority database was mutated
to perform this reassessment.

## Focused and adversarial qualification

`tests/test_trajectory_v2_crash_contract.py` adds 13 focused cases. Its read-only
`inspect_retained_crash` test composition reuses production verifier entry/frame
checks and requires an independently captured orphan hash. It accepts only its
defined bounded witness; it always returns `whole_root_sealed=false` and retains
the complete failed root reports. It rejects unexplained gaps, extra closed
chunks, unexpected verifier errors, active tails and malformed evidence.

| Coverage | Evidence |
| --- | --- |
| Current live tail / clean close | Live accepts one complete current tail; sealed refuses it; clean close removes that partial through normal seal and makes sealed verification pass. The crash assessment refuses a current live tail. |
| Empty and nonempty pre-crash sealed prefixes | Fresh trajectory-only witnesses preserve orphan bytes and existing prefix hashes/manifest records, create a separate successor and retain ordinary-consumer refusal. |
| New native session and stale refusal | Existing qualified coordinator setup issues a predecessor token. Normal native runtime acquisition creates a later session/generation; the stale effect is refused before entry, current step/close succeeds, the old partial is unchanged, and legacy remains fenced. |
| Nine adversarial copies | Changed orphan, broken previous-hash link, unexplained sequence/header mismatch, manifest pointing to partial, absent diagnostic, absent epoch boundary, changed sealed bytes, truncated orphan frame even with a supplied matching hash, and unmanifested closed chunk are refused. Originals remain retained. |
| Four existing governing tests | Current live/clean-close distinction; expected orphan restart refusal; native-session replacement fencing; shared evidence failure/restart remaining non-authoritative. |

Final result: **17 passed in 3.51 seconds**, zero failures, errors or skips,
under `conda activate torment`. Exact invocation, stdout and JUnit are in
`run_focused.py`, `focused-2.json`, `focused-2.log` and `focused-2.xml`.
The first attempt stopped at collection because a numeric literal in the new
test entity helper was mistyped; `focused-1.*` retains that error. The typo was
corrected in the test only, and the full selected suite then passed.

The fresh tests model handle loss without application sealing, plus qualified
session replacement. Actual process-death evidence remains the already-executed
R2 A/B runs. No full SQLite scenario was repeated, no actual service restart
was needed, and no crash-root repair or new recovery disposition was applied.

`A_trajectory_audit.json` and `B_trajectory_audit.json` each contain 13 passing
checks against the preserved R2 evidence. The R3 change is tests and evidence
only: `CORRECTION_IMPLEMENTED = NO`, `CORRECTION_SCOPE = NONE`.

## Production and R2 unchanged proof

R3 evidence directory:
`C:\TORMENT\TORMENT_administration\post-p7-stage-4r3-20260910`.
Evidence filenames in this report are relative to that directory unless
explicitly identified as R2 or repository sources.

The production root was contacted only for read-only fingerprints and authority
observations. Preflight was recorded at `2026-09-10T17:07:53.022073+00:00`;
final comparison at `2026-09-10T17:15:54.698407+00:00`. Both contain 2,093 files,
1,163,889,969 bytes and tree SHA-256:
`345d29441220273acc1371641be08e4e0dfd0fc381018b16a601b16dfb648776`.
File hashes were compared before and after even the read-only authority call.

Production remains core `f21c730f-5222-4aa8-9a5f-1c1188456df3`, selector generation
8, NATIVE_ACTIVE/NATIVE_AGREEMENT; trajectory lifecycle generation 10 and legacy
fence 2 are unchanged. `real_before.json`, `real_after.json` and
`real_postcheck.json` establish all requested production postchecks as PASS/YES.

All 204 R2 manifest-bound evidence/helper files, all four R2 root inventories
(A 81, B 81, C 79, D 81 files) and the R2 report still match their sealed hashes.
The R2 manifest remains
`eea9f3af0ce802b3c05d73629a363a0038b64f1274d21936f13c3ee55727a068`;
the R2 report remains
`63814601df88f0e6a1ac637c8c6ff22ad771ef2b03a94227720ddc6b46e443df`.

R3 `evidence_manifest.json` binds 181 observation/helper/test-artifact files,
including both test attempts and the retained adversarial copies. Its SHA-256:
`0b91408144b01bf271bd55d3a4b9e7ec1600da65415330bb57ec71cb69c1ad19`.
It excludes its own hash, `__pycache__` and later `publication.json`.
`source_review.json` binds the exact tested source and eleven frozen governing
sources. Publication verification checks these bindings and the bounded Git diff.

## Decision and next boundary

CASE A is established for the preserved, fully characterized A/B crash tails.
The missing condition was the expectation of a wholly sealed artifact root
after a crash, not a frozen recovery disposition omitted by implementation.
The successful bounded recovery assessment leaves every strict verifier rule,
consumer refusal and retained forensic artifact intact.

R2's committed-memory recovery, atomic memory recovery, clean lock contention,
scope isolation, SQLite/FK integrity and native authority conclusions remain
frozen. Combined with this trajectory reconciliation, Stage 4 passes.

```text
STAGE4_TRAJECTORY_RECOVERY_QUALIFICATION = PASS
POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_4R3 = PASS
POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_4 = PASS
SQLITE_MIGRATION_FULLY_VALIDATED = CANDIDATE_YES
NONEMPTY_SHARED_RANKING = NOT_YET_VALIDATED
NEXT_AUTHORIZATION_BOUNDARY = POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_4R3_REVIEW
```

STOP for the requested final review. Final migration YES is not frozen here.

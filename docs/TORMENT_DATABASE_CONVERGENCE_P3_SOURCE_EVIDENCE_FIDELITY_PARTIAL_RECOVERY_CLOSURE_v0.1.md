# TORMENT Database Convergence — P3 Source-Evidence Fidelity + Partial-Recovery Closure v0.1

## Scope and boundary

This qualification repairs the source-evidence and carrier assumptions exposed
by the preserved first P3 B1 stop. It uses disposable production-shaped
fixtures only. It does not read, write, or otherwise inspect the real root,
and it does not modify the preserved real carrier, its 154 snapshots, or its
manifests.

Logical legacy memory identity is the canonical EID. Physical JSONL history is
retained, while admission selects the last current record for each EID. No
text, byte, vector, or similarity deduplication is introduced.

## Qualified changes

- The typed root-evidence adapter now captures every validated compact-store
  map and shard leaf explicitly. `workspace_meta.json` remains representation
  identity authority; the seven-key embedding manifest remains storage
  metadata only.
- Ordinary compact `MEMORY_GRAPH` P3 snapshots now include the required
  workspace metadata regardless of motif presence. A production-shaped fixture
  proves retention of nodes, workspace metadata, the storage manifest, map,
  and shard evidence.
- B1 preserves each admitted canonical EID and its individual legacy-vector
  strategy. B3 routing is consequently per EID: exact target bytes use B3A;
  re-embedding, absent, and unusable vector evidence use B3B. Metadata-less
  routing remains one dispatch per qualified `(scope_key, eid)`.
- All admitted motifs are retained in deterministic order. Empty shared motifs
  use B4C, target-compatible geometry uses B4A, and re-geometry uses B4B.
- A completion carrier is distinct from its predecessor. It cross-binds the
  immutable predecessor record and digest, preserves predecessor artifacts
  exactly, and permits only a strict same-snapshot-ID source-evidence
  superset containing the corrected source roles. Inherited snapshots must be
  listed by the predecessor; predecessor drift or a mismatched requested
  predecessor refuses.
- The narrow pre-P5 pending supersession clears only the selector from
  `CUTOVER_PENDING` to `LEGACY_ACTIVE` after proving the core is still inert.
  It neither changes the core nor claims activation rollback. A disposable
  fixture proves a corrected source description requires a distinct immutable
  successor P2 envelope while selecting the same inert staging core.

The typed `RootP3SourceAdmissionRefused` code remains available to the
administration boundary as the refusal reason; it is not reduced to a generic
unexpected-exception classification.

## Regression evidence

The directly implicated suites completed with **192 passed, 5 skipped**:

- typed-evidence adapter and root admission description;
- legacy representation admission and runtime readiness/bootstrap paths;
- root P3 source admission, normalization, generalized readiness, and module
  import-cycle coverage;
- root-v2 production recovery and generalized blocker-5 binding coverage.

Focused fixtures prove four canonical EIDs with mixed vector strategies produce
two B3A and two B3B requests; appended historical input remains physical
history rather than a fifth logical memory; three motifs survive B1 and produce
the appropriate B4 requests; and a B1-committed/carrier-null predecessor
recovers under a completion manifest without duplicating aliases or objects.

## Verdict

```text
P3_HISTORICAL_EID_IDENTITY_RECONCILED = YES

P3_NORMAL_EMBEDDING_STORAGE_EVIDENCE_OMISSION = CONFIRMED
P3_NORMAL_EMBEDDING_STORAGE_EVIDENCE_REPAIR = QUALIFIED
P3_COMPACT_WORKSPACE_LOCK_CAPTURE_REPAIR = QUALIFIED

P3_MULTI_EID_CARRIER_REPAIR = QUALIFIED
P3_PER_EID_B3_ROUTING = QUALIFIED
P3_MULTI_MOTIF_CARRIER_REPAIR = QUALIFIED
P3_B4A_B4B_B4C_ROUTING = QUALIFIED

P2_CORRECTED_DESCRIPTION_CHANGES_ENVELOPE = YES
PRE_P5_PENDING_SUPERSESSION = QUALIFIED
SAME_CORE_CORRECTED_P2_SUCCESSOR = QUALIFIED

P3_MONOTONIC_SNAPSHOT_EVIDENCE_COMPLETION = QUALIFIED
REAL_PARTIAL_P3_RECOVERY_SHAPE = QUALIFIED

DISTINCT_EIDS_ARE_NOT_MERGED = YES
APPEND_HISTORY_IS_NOT_ADMITTED_AS_EXTRA_MEMORY = YES
TARGET_VECTOR_BYTES_REQUIRE_EXACT_EVIDENCE = YES
HASH_VECTOR_BYTES_ARE_NOT_RELABELLED_AS_ST_BGE = YES
DIMENSION_EQUALITY_IS_NOT_REPRESENTATION_IDENTITY = YES
OLD_PHYSICAL_HISTORY_IS_NOT_DELETED = YES

REAL_ROOT_CONTACT = NONE
REAL_ROOT_WRITE = NONE
REAL_P3_RECOVERY_EXECUTED = NO
P4_P7_EXECUTED = NO
```

## Stop

This is a qualification result only. The real selector supersession, corrected
real P2 envelope, and real P3 recovery/resumption were not performed and each
requires a new explicit authorization.

# TORMENT Database Convergence — Direct EMPTY_PRIVATE Source Grammar Qualification v0.1

## Scope

This is a static/synthetic qualification of the direct-admission source reader only.
No production root, writer process, listener, or production SQLite database was
contacted.  P1 was not executed.

## Revision boundary

```text
STARTING_HEAD = bc622a9b724cdc159f39fe1e0f55d5c1266f332f
ORIGIN_MAIN  = bc622a9b724cdc159f39fe1e0f55d5c1266f332f
FINAL_HEAD   = the commit containing this qualification record
```

## Change qualified

`RealRootTypedEvidenceAdapter.prepare_direct_admission_source()` now enables a
bounded `allow_known_empty_private_residue` path.  With `nodes.jsonl` absent, the
direct reader keeps the existing private child grammar and side-store validation,
records the actual embedding-manifest row counters and memory-event observation, and
classifies the scope as `EMPTY_PRIVATE` / `NO_VECTOR`.

Known residue remains storage or retained audit evidence, not canonical memory.  The
compatibility `capture_typed_evidence()` path retains its historical strict empty
private rule, including the zero-row/zero-next-row requirement.  No corrective-packet
code, schema, or version changed.

## Synthetic evidence exercised

- absent `nodes.jsonl` with `total_rows=0` / `next_row=0`;
- absent `nodes.jsonl` with `total_rows=1` / `next_row=1` and a recognized orphan
  shard artifact;
- nonempty retained `memory_events.jsonl`;
- recognized `edges.jsonl`, logs, trajectories, checkpoints, and legacy trajectory
  residue;
- unknown empty-private direct child refusal;
- direct preparation through the writer callback into the existing root-envelope
  qualification fixture.

The empty-private source plan remains `EMPTY_PRIVATE` / `NO_VECTOR`; the existing
normalization qualification accepts its corresponding empty private input only with
zero B3 and zero B4 requests.  The direct reader emits no canonical node source for
that scope, and the existing agent is recorded as identity-only rather than creating a
new agent.

## Test result

Run in the `torment` Conda environment with disposable test roots:

```text
python -m pytest \
  tests/test_real_root_typed_evidence_adapter.py \
  tests/test_substrate_root_admission_description.py \
  tests/test_substrate_root_normalization.py \
  tests/test_post_i4_generalized_root_blocker5_binding.py \
  -q --basetemp _pytest_tmp_direct_empty_private_full

58 passed, 1 skipped
```

The only warning was pytest's denied shared cache write; it did not affect test
execution.

## Required verdicts

```text
DIRECT_EMPTY_PRIVATE_GRAMMAR = QUALIFIED
FROZEN_EMPTY_PRIVATE_LAW_PRESERVED = YES
ORPHAN_VECTOR_ROWS_CLASSIFICATION = HISTORICAL_UNREACHABLE_RESIDUE
ORPHAN_VECTOR_PROMOTED_TO_MEMORY = NO
NONZERO_EMBEDDING_ROWS_ALLOWED_FOR_DIRECT_EMPTY_PRIVATE = YES
NONEMPTY_MEMORY_EVENTS_ALLOWED_AS_RETAINED_AUDIT = YES
KNOWN_PRIVATE_SIDE_STORES_REUSED = YES
UNKNOWN_PRIVATE_ARTIFACT_STILL_REFUSES = YES
EMPTY_PRIVATE_B3_REQUESTS = 0
EMPTY_PRIVATE_B4_REQUESTS = 0
CORRECTIVE_PACKET_SCHEMA_CHANGED = NO
PACKET_VERSION_CHANGED = NO
NEW_HASH_LAW = NO
NEW_BYTE_IDENTICAL_LAW = NO
NEW_CANONICALIZATION_LAW = NO
REAL_ROOT_CONTACT = NONE
WRITER_CONTACT = NONE
SQLITE_PRODUCTION_WRITE = NONE
P1 = NOT_EXECUTED
READY_FOR_NEW_DIRECT_REAL_PREPARATION_AND_P1_ATTEMPT = YES (fresh authority required)
```

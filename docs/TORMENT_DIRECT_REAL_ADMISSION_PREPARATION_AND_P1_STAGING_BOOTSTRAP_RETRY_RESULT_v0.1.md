# TORMENT — Direct Real Admission Preparation + P1 Staging Bootstrap Retry Result v0.1

## Authority and boundary

This record is the result of the operator-authorized retry:

```text
DIRECT_REAL_ADMISSION_PREPARATION_AND_P1_STAGING_BOOTSTRAP_RETRY = YES
```

The authorized production root was `data/`.  The procedure was limited to a fresh
writer census, a real >=60-second stability capture, direct source preparation through
the required factory, and P1 only if every predecessor gate passed.  It did not
authorize P2, envelope construction, selection, normalization, cutover, activation,
restart, P5/P6/P7, source writes, or legacy-store writes.

## Start state

At start, both `HEAD` and `origin/main` were:

```text
ae4f053a17ba54074ac90f08186ec971e159d237
```

The fresh Windows CIM process census found zero qualifying root-writer candidates.
The fresh `Get-NetTCPConnection` listener census found zero listeners at
`127.0.0.1:8787`.

The capture was run through Command Prompt with the authorized environment activation:

```text
call C:\Users\Notandi\miniconda3\condabin\conda.bat activate torment && python -
```

## Exact direct-adapter configuration

The caller used `build_real_direct_admission_source_adapter(...)`, not a direct
`RealRootTypedEvidenceAdapter` constructor.  The factory bound exactly:

| locator | role / handling |
| --- | --- |
| `nodes.jsonl` | `TOP_LEVEL_UNSCOPED_NODES` |
| `emb_1.npy` | `TOP_LEVEL_UNSCOPED_EMBEDDINGS` |
| `lived_use` | `ALTERNATE_SELECTED_ROOT`; presence-only |

No `lived_use` child enumeration, read, or hash was requested by this procedure.

## Real capture result

The fresh capture reached its `during_capture` callback only after the real
60-second minimum stability interval and the capture's t0/t1 workspace snapshots had
been accepted.  Direct source preparation then refused with the exact typed error:

```text
CorrectiveFreezePacketRefused: empty private scope contains an unclassified durable artifact
```

The exception originated at `_validate_direct_children` while
`_capture_private_scope` was preparing an empty private scope.  The procedure did not
perform another source probe to identify or classify the artifact: the authority
requires stopping on this refusal.

An initial local harness construction error was corrected before any root snapshot or
source contact: `WriterProcessObservation` requires
`observation_mechanism`, not `mechanism`.  It did not start a capture, create evidence,
or access the production root.  The subsequent capture above was the single real
authorized source attempt.

## Stop ledger

| gate / action | result |
| --- | --- |
| Start revision equality | PASS |
| Fresh writer and public-listener census | PASS |
| Required factory configuration | PASS |
| Real >=60-second t0/t1 stability interval | PASS before callback |
| Direct source preparation | REFUSED — unclassified durable artifact in empty private scope |
| Fresh writer-freeze payload | NOT CREATED |
| Fresh writer-freeze witness | NOT CREATED |
| Fresh writer-freeze recheck | NOT CREATED |
| P1 native staging-core bootstrap | NOT ATTEMPTED |
| SQLite write / staging-core path creation | NONE |
| Final post-P1 writer census | NOT APPLICABLE; P1 did not begin |
| P2 or later phases | NOT ATTEMPTED |

The retry is therefore stopped without a native staging core.  A future administrative
authority would need to address the refused source grammar before a new preparation
attempt.  `P2_ROOT_ADMISSION_ENVELOPE_AND_CUTOVER_PENDING` remains pending and was not
entered.

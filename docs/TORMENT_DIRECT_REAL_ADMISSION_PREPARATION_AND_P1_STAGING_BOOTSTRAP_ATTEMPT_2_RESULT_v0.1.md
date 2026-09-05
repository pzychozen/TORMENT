# TORMENT — Direct Real Admission Preparation + P1 Staging Bootstrap Attempt 2 Result v0.1

## Authority and stop boundary

This record covers the operator-authorized attempt:

```text
DIRECT_REAL_ADMISSION_PREPARATION_AND_P1_STAGING_BOOTSTRAP_ATTEMPT_2 = YES
```

The attempt was limited to a fresh writer/listener gate, real source stability,
direct source preparation through the required factory, and P1 only after every
read-only prerequisite passed.  It stopped during direct source preparation.  P1 and
all later phases were not entered.

## Start state

```text
HEAD        = dbd3b74f9fe8f09a6d8d7520fcade1ebb25e402e
origin/main = dbd3b74f9fe8f09a6d8d7520fcade1ebb25e402e
```

The final fresh Windows CIM / listener census found zero covered writer candidates
and zero listeners at `127.0.0.1:8787`.  It explicitly excluded the command's own
process ancestry.  An earlier broad preliminary matcher was not used as evidence: it
matched the executing PowerShell command text and the unrelated Windows
`webthreatdefusersvc` service on the substring `REST`; the refined covered-process
census did not match either process.

## Required factory configuration

The only source adapter used was
`build_real_direct_admission_source_adapter(...)`.  Its exact bindings were:

| locator | role / handling |
| --- | --- |
| `nodes.jsonl` | `TOP_LEVEL_UNSCOPED_NODES` |
| `emb_1.npy` | `TOP_LEVEL_UNSCOPED_EMBEDDINGS` |
| `lived_use` | `ALTERNATE_SELECTED_ROOT`; presence-only |

No `lived_use` descendant enumeration, read, or hash was requested.

## Real capture result

The capture was run through Command Prompt in the authorized environment:

```text
call C:\Users\Notandi\miniconda3\condabin\conda.bat activate torment && python -
```

Its actual t0/t1 interval met the 60-second minimum and reached the
`during_capture` direct-preparation callback.  The direct adapter then refused with
the exact typed error:

```text
CorrectiveFreezePacketRefused: typed evidence source must be a non-symlink regular file
```

The stack reached this refusal while capturing a shared-scope motif source.  No
follow-up source inspection was performed to identify or classify the underlying
artifact, because the authorization requires stopping on a preparation refusal.

## Stop ledger

| gate / action | result |
| --- | --- |
| Start revision equality | PASS |
| Required real-root factory | PASS |
| Fresh covered writer / listener census | PASS |
| Real >=60-second t0/t1 source stability | PASS before direct callback |
| Direct source preparation | REFUSED — required source is not a non-symlink regular file |
| Root admission description / census / source-plan closure | NOT CREATED |
| Fresh writer payload / witness / recheck | NOT CREATED |
| P1 native staging-core bootstrap | NOT ATTEMPTED |
| SQLite write / native staging core | NONE |
| Root admission envelope persistence | NONE |
| CUTOVER_PENDING / normalization / P5 / P6 / P7 | NOT ATTEMPTED |
| Legacy source mutation | NONE |
| Final post-P1 writer recheck | NOT APPLICABLE; P1 did not begin |

```text
DIRECT_REAL_ADMISSION_PREPARATION_ATTEMPT_2 = STOPPED
QUALIFIED_REAL_ADAPTER_FACTORY_USED = YES
WRITER_CENSUS = PASS
SOURCE_STABILITY = PASS
DIRECT_SOURCE_PREPARATION = REFUSED
FRESH_WRITER_PAYLOAD = NOT_CREATED
FRESH_WRITER_WITNESS = NOT_CREATED
FRESH_WRITER_RECHECK = NOT_CREATED
P1 = NOT_EXECUTED
SQLITE_WRITE = NONE
ROOT_ADMISSION_ENVELOPE_PERSISTED = NO
NORMALIZATION_EXECUTED = NO
```

No retry, grammar widening, deletion, cleanup, service restart, or additional
real-root probe was performed.  A future administration requires fresh authority.

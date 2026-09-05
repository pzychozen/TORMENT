# TORMENT direct real admission preparation and P1 staging bootstrap — Attempt 3 result

```text
AUTHORIZATION = DIRECT_REAL_ADMISSION_PREPARATION_AND_P1_STAGING_BOOTSTRAP_ATTEMPT_3
STARTING_HEAD = ba74076b626d400165c05aa1f06d1c2df04a6d40
STARTING_ORIGIN_MAIN = ba74076b626d400165c05aa1f06d1c2df04a6d40
REAL_ROOT = C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric\data
ENVIRONMENT = command prompt / conda activate torment
```

## Read-only result

```text
QUALIFIED_REAL_ADAPTER_FACTORY_USED = YES
FACTORY = build_real_direct_admission_source_adapter(...)
ROOT_EXCLUSIONS =
  nodes.jsonl = TOP_LEVEL_UNSCOPED_NODES
  emb_1.npy = TOP_LEVEL_UNSCOPED_EMBEDDINGS
  lived_use = ALTERNATE_SELECTED_ROOT / PRESENCE_ONLY

WRITER_CENSUS = PASS
REST_OR_TORMENT_SERVICE = ABSENT
MCP_TARGETING_PRODUCTION_ROOT = ABSENT
DIRECT_TORMENT_WRITER = ABSENT
AGENTRUNNER_OR_FABRIC_HOST = ABSENT
NONTERMINAL_CLONE_REPAIR_JOB = ABSENT
127.0.0.1:8787_LISTENER = ABSENT

SOURCE_STABILITY = PASS
SOURCE_STABILITY_MINIMUM = 60_SECONDS
DIRECT_SOURCE_PREPARATION = REFUSED
REFUSAL_TYPE = CorrectiveFreezePacketRefused
REFUSAL = typed evidence source must be a non-symlink regular file
REFUSAL_PHASE = RealRootTypedEvidenceAdapter.prepare_direct_admission_source
```

The direct preparation callback was invoked only after the writer-freeze
capture accepted its fresh `t0`/`t1` workspace stability interval and its
clone/repair-job observation. The adapter then refused before it could return
a `DirectAdmissionSourcePreparation`. This administration did not inspect the
refused path further, alter source grammar, or retry the preparation.

## P1 result

```text
DIRECT_REAL_ADMISSION_PREPARATION_ATTEMPT_3 = REFUSED
ROOT_NATIVE_PRODUCTION_ADMISSION_DESCRIPTION = NOT_CREATED
REAL_SOURCE_CENSUS = NOT_CREATED
REAL_SOURCE_DISPOSITIONS = NOT_CREATED
REAL_SOURCE_POSTURES = NOT_CREATED
FRESH_WRITER_PAYLOAD = NOT_CREATED
FRESH_WRITER_WITNESS = NOT_CREATED
FRESH_WRITER_RECHECK = NOT_CREATED
WRITER_RECHECK_BINDING = NOT_CREATED

P1_NATIVE_STAGING_CORE_BOOTSTRAP = NOT_EXECUTED
REAL_NATIVE_STAGING_CORE_CREATED = NO_BY_THIS_ATTEMPT
REAL_NATIVE_STAGING_CORE_PATH = NONE
REAL_NATIVE_STAGING_CORE_ID = NONE
SQLITE_WRITE = NONE
ROOT_PROFILE_IDENTITY = NOT_CREATED
MEMBERSHIP_SUMMARY = NOT_CREATED
```

No staging-core directory, database, root-profile record, membership/runtime
prerequisite, root admission envelope, selector, or cutover state was created
by this attempt. The P1 preflight and all P1 code paths remained unreached.

## Authority and stop boundary

```text
LEGACY_SOURCE_WRITE_CONTACT = NONE
LEGACY_SOURCE_MUTATION = NONE
LEGACY_MEMORY_AUTHORITY = PRESERVED
ROOT_ADMISSION_ENVELOPE_PERSISTED = NO
CUTOVER_PENDING = NO
NORMALIZATION_EXECUTED = NO
P5_EXECUTED = NO
P6_EXECUTED = NO
P7_EXECUTED = NO
FINAL_WRITER_RECHECK = NOT_EXECUTED
STOPPED_FOR_P1_REVIEW = YES
```

The exact refusal is recorded without interpreting its path or attempting a
repair. A future operation requires separate operator authorization.

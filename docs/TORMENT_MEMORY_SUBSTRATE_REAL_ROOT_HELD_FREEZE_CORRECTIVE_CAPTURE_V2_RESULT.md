# TORMENT Memory Substrate — Real-Root Held-Freeze Corrective Capture V2 Result

## Result

```text
REAL_ROOT_HELD_FREEZE_CORRECTIVE_CAPTURE_V2 = STOPPED
CONTINUOUS_FREEZE_RECERTIFIED = NO
FAILURE_CLASS = TYPED_ADAPTER_REFUSAL
```

This is a failure record, not a replacement freeze epoch.  The V2 authority's
failure law requires a stop on a typed-adapter refusal.  No admission,
normalization, re-embedding, writer restart, or expected-evidence update was
performed.

## Authority and starting state

```text
AUTHORIZATION = REAL_ROOT_HELD_FREEZE_CORRECTIVE_CAPTURE_V2 = YES
OPERATOR_IDENTITY = desktop-v9e8ir5\notandi
CAPTURE_HEAD = b205446adb28bf2b02bfc29b9eed0fd8858f07ab
ORIGIN_MAIN_AT_START = b205446adb28bf2b02bfc29b9eed0fd8858f07ab
RESOLVED_REAL_ROOT = C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric\data
FAILURE_RECORDED_UTC = 2026-09-05T14:30:45.7631167Z
```

Tracked repository state was clean at the start.  Pre-existing untracked
pytest temporary directories and the unrelated draft document were observed
and left untouched.

## Completed pre-capture gates

```text
WRITER_CENSUS = PASS
REST_SERVICE = ABSENT
MCP_SERVER = ABSENT
DIRECT_TORMENT_TOOL_OR_SCRIPT = ABSENT
AGENT_RUNNER_OR_OTHER_FABRIC_HOST = ABSENT
NONTERMINAL_CLONE_REPAIR_JOBS = NONE
LOOPBACK_127.0.0.1_8787 = ABSENT

PREDECESSOR_STATE_EQUALITY = PASS
PREDECESSOR_OPERATION = ROOT_WRITER_FREEZE_STOP_AND_VERIFY_V1_20260905T035646Z_C7482AE
PREDECESSOR_PAYLOAD_DIGEST = 6f7d654780355c05003ba00bf73c69287020c77e89d6dcc1b7f579959f8fe7fa
PREDECESSOR_WITNESS_DIGEST = 69ec66af8a69a84fe8a2c8a4e9c0a085cf7f97b52829458d37ecd289dbd05774
PREDECESSOR_TREE_DIGEST = 52ff2f04d839015d43ef73a0ad02415d19587126ff2e6e0b3fbe4737f4487275
PREDECESSOR_FILE_COUNT = 1748
PREDECESSOR_MAXIMUM_MTIME_NS = 1788363578805346200
TOP_LEVEL_UNSCOPED_NODES_SHA256 = 4cfdf4c33dd2b14d6101f03c6218af997ebcbc02241eb1b9135dd3f01f406279
TOP_LEVEL_UNSCOPED_EMB_SHA256 = fd190080f525b22fb9c2609c1723d41c1c79162c4c99d7ac65185437e8a84507

EXCLUDED_ALTERNATE_ROOT_CLASS = PASS
EXCLUDED_ALTERNATE_ROOT = lived_use
EXCLUDED_ALTERNATE_ROOT_ROLE = ALTERNATE_SELECTED_ROOT
EXCLUDED_ALTERNATE_ROOT_CONTACT = PRESENCE_ONLY; NO_DESCENDANT_READ
```

The capture passed its internal t0/t1 minimum-60-second stability gate: the
typed-evidence callback is invoked only after that gate.  It then refused
during the bounded typed adapter, before t2, packet serialization, or packet
reload.  Because the failure path produces no payload, it provides no
successor timestamps or successor witness to record.

## Exact refusal

```text
torment_service.substrate.corrective_freeze_packet.CorrectiveFreezePacketRefused:
agent contains an unclassified durable artifact
```

The refusal arose at
`RealRootTypedEvidenceAdapter._validate_agent_children`, through
`_validate_direct_children`, while capturing typed evidence.  The V2 stop law
prohibits probing to identify or classify the artifact, so this administration
did not inspect the affected agent directory further.

```text
T0_T1_STABILITY = PASS
T2_STABILITY = NOT_REACHED
TYPED_ADAPTER = REFUSED
SOURCE_MANIFEST_VERIFICATION = NOT_REACHED
SUCCESSOR_FREEZE_WITNESS = NOT_CREATED
PACKET_V3_SERIALIZATION = NOT_REACHED
PACKET_OFFLINE_RELOAD = NOT_REACHED
FINAL_WRITER_RECHECK = NOT_RUN_AFTER_REFUSAL
REAL_ROOT_WRITE_CONTACT = NONE
```

## Final authority ledger

```text
REAL_ADMISSION_AUTHORIZED = NO
NORMALIZATION_AUTHORIZED = NO
CUTOVER_PENDING_AUTHORIZED = NO
P6_AUTHORIZED = NO
P7_AUTHORIZED = NO
WRITER_RESTART_AUTHORIZED = NO

PRODUCTION_CODE_CHANGES = 0
TEST_CODE_CHANGES = 0
TESTS_RUN_FOR_V2_REAL_ROOT_CAPTURE = 0
PROVIDER_CONTACT = NONE
MODEL_LOADING = NONE
```

No retry was made.  The next action requires separate operator authorization
for a static reconciliation of the typed-adapter refusal; this V2
administration is complete and stopped.

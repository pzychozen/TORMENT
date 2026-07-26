# TORMENT Brainvision Stage S3B v0.3
# BLOCKER-2 Wrapper Post-Commit Identity and Path Preparation Findings v0.1

## 0. Document Status

document_class = BLOCKER-2 wrapper post-commit identity and path preparation findings
document_version = v0.1
document_mode = docs-only findings and activation-preparation record
authorization_status = PREPARED_NOT_ACTIVE

Machine-readable status block:

```text
wrapper_commit = "605fc5c0ec1b3900c65bd40fef4c1cc003fd7a80"
prepare_paths_executed = true
prepare_paths_terminal_label = "PREPARATION_COMPLETE"
authoritative_retained_run_executed = false
global_authority_consumed = false
local_gate_created = false
run_result_created = false
retained_completion_created = false
blocker_2_state = "OPEN"
blocker_4_started = false
```

This document records post-commit identity binding for the committed BLOCKER-2
operator wrapper and the non-authoritative `PREPARE_PATHS` admission of the
three fixed Windows roots. It is not an execution authorization and is not
retained scientific evidence.

## 1. Preparation Question

Question:

```text
Are the committed wrapper identities bound and are the exact fixed roots
prepared and admitted for the later inactive final authorization phase?
```

Answer:

```text
Yes. The committed wrapper and execution-surface file identities were bound,
the wrapper accepted a PREPARED_NOT_ACTIVE preparation input, and PREPARE_PATHS
returned PREPARATION_COMPLETE without creating authority, gate, run-result, or
completion evidence.
```

The committed wrapper requires the canonical input's `authoritative` field to
be `true` even for `PREPARE_PATHS`; this is a future retained-authorization
object selector in the committed schema, not proof that an authoritative run
was activated. Execution activation remained false because the input status
and execution authorization document status were both `PREPARED_NOT_ACTIVE`,
and neither `PREFLIGHT_ONLY` nor `EXECUTE_EXACT_SINGLE_RUN` was invoked.

## 2. Authoritative Baseline

| Field | Value |
| --- | --- |
| branch | `main` |
| HEAD | `605fc5c0ec1b3900c65bd40fef4c1cc003fd7a80` |
| origin/main | `605fc5c0ec1b3900c65bd40fef4c1cc003fd7a80` |
| HEAD == origin/main | `true` |
| initial working tree | `clean` |
| `.git/index.lock` | `absent` |

Reviewed lineage top:

```text
605fc5c research(brainvision): implement blocker 2 operator wrapper
377f599 docs(research): authorize blocker 2 operator wrapper
e9608c5 docs(research): assess blocker 2 exact retained run authorization
0e8e8d1 research(brainvision): complete blocker 2 retained runtime
b647814 docs(research): authorize blocker 2 retained runtime correction
```

## 3. Preserved Boundaries

Preserved:

```text
FORMAL_HOLD = active
Mode_0 = active
STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY
```

Brainvision remains offline, quarantined, synthetic-only, non-production,
non-service, non-kernel, non-memory-integrated, non-cognitive, and
non-autonomous.

No production, kernel, service, memory, autonomy, prompt, action, or BLOCKER-4
surface was modified. BLOCKER-2 remains open.

## 4. Controlling Documents

Read in full before path preparation:

```text
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_OPERATOR_WRAPPER_AND_PATH_PREPARATION_AUTHORIZATION_v0.1.md
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_EXACT_AUTHORITATIVE_RETAINED_SINGLE_RUN_AUTHORIZATION_v0.1.md
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_POST_COMMIT_RUNTIME_CORRECTION_AUTHORIZATION_v0.1.md
```

The preparation document used as the inactive preparation document identity was:

| Field | Value |
| --- | --- |
| path | `docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_OPERATOR_WRAPPER_AND_PATH_PREPARATION_AUTHORIZATION_v0.1.md` |
| Git blob | `3680795472de8f0f14fe0365fca5ec1d39ff6069` |
| checked-out SHA-256 | `1a395b394db777af0f88953d33dd27f7cc9b245cc2472f19c2304e416eb35d8a` |
| byte length | `19747` |
| canonical authorization declaration identity | `94fd95c21fe43746feead9c6ebf6febc6928caa1eb9c2963a690436bbd66b702` |
| authorization status | `PREPARED_NOT_ACTIVE` |

## 5. Committed Wrapper

| Wrapper file | HEAD blob | `git hash-object` | checked-out SHA-256 | bytes |
| --- | --- | --- | --- | ---: |
| `research/brainvision/run_blocker2_authoritative_retained_single_run_v0_1.py` | `01677a77f20f120f12b2b0e1c43284ece50b112b` | `01677a77f20f120f12b2b0e1c43284ece50b112b` | `56387ea481ac7daaceb046558b535229587765530c7732a084c7c5bfef4fb31a` | 45966 |
| `research/brainvision/test_run_blocker2_authoritative_retained_single_run_v0_1.py` | `ba0a4e734b51068d1d0ad209b432c96865078f20` | `ba0a4e734b51068d1d0ad209b432c96865078f20` | `9880111fd510e874e33b668fde2344ea34c98a62b78e66d2f5470a841235bd1a` | 19419 |
| `research/brainvision/test_run_blocker2_authoritative_retained_single_run_integration_v0_1.py` | `9621d6c4ac88291030332eec818c687e5113feb5` | `9621d6c4ac88291030332eec818c687e5113feb5` | `1eb4110572ca22acfd15053d7bd7250ba58bfe6f9ff02aaa8dfaf6152878a766` | 3997 |

Decision:

```text
WRAPPER_COMMITTED_IDENTITY_BOUND
```

No wrapper identity is `UNAVAILABLE_UNTIL_COMMIT`, and every wrapper HEAD blob
matches `git hash-object`.

## 6. Nine-File Git Blob Inventory

| File | Git blob at HEAD |
| --- | --- |
| `research/brainvision/run_blocker2_authoritative_retained_single_run_v0_1.py` | `01677a77f20f120f12b2b0e1c43284ece50b112b` |
| `research/brainvision/test_run_blocker2_authoritative_retained_single_run_v0_1.py` | `ba0a4e734b51068d1d0ad209b432c96865078f20` |
| `research/brainvision/test_run_blocker2_authoritative_retained_single_run_integration_v0_1.py` | `9621d6c4ac88291030332eec818c687e5113feb5` |
| `research/brainvision/blocker2_retained_absolute_path_control_v0_1.py` | `99976d61f23145e36277d89a4d2db2bf45e8a010` |
| `research/brainvision/test_blocker2_retained_absolute_path_control_v0_1.py` | `fd90aca033cee89864841ae7ca993e94c35b1c1f` |
| `research/brainvision/test_blocker2_retained_absolute_path_control_integration_v0_1.py` | `89de880f4d5c51bb0b055c584d53a79fe006d54f` |
| `research/brainvision/validate_windows_same_volume_no_replace_promotion_v0_1.py` | `5a662d0a6c7d56f53e20ba4b8db56fee731c8057` |
| `research/brainvision/test_validate_windows_same_volume_no_replace_promotion_v0_1.py` | `471baebc50d08d38c68042486ef0eb3fb6d0d186` |
| `research/brainvision/test_validate_windows_same_volume_no_replace_promotion_integration_v0_1.py` | `c9435db7ca1b7e418494b4f9ff224823a8b6ba38` |

All nine `git hash-object` values matched the listed HEAD blobs.

## 7. Nine-File Checked-Out SHA-256 Inventory

| File | Checked-out SHA-256 | bytes |
| --- | --- | ---: |
| `research/brainvision/run_blocker2_authoritative_retained_single_run_v0_1.py` | `56387ea481ac7daaceb046558b535229587765530c7732a084c7c5bfef4fb31a` | 45966 |
| `research/brainvision/test_run_blocker2_authoritative_retained_single_run_v0_1.py` | `9880111fd510e874e33b668fde2344ea34c98a62b78e66d2f5470a841235bd1a` | 19419 |
| `research/brainvision/test_run_blocker2_authoritative_retained_single_run_integration_v0_1.py` | `1eb4110572ca22acfd15053d7bd7250ba58bfe6f9ff02aaa8dfaf6152878a766` | 3997 |
| `research/brainvision/blocker2_retained_absolute_path_control_v0_1.py` | `878511058fc221858718febfd8979fc0d9c2e752d81e5c2580bcc6dbc119d8f7` | 137543 |
| `research/brainvision/test_blocker2_retained_absolute_path_control_v0_1.py` | `eff1e225136bccf49393f8098628527a0bd5c5b73c5565b75b62389eab1d9ecb` | 37182 |
| `research/brainvision/test_blocker2_retained_absolute_path_control_integration_v0_1.py` | `193dfac7db9b4c9683cfdd36b71a549b0a012975be090a433ef839c0b8bb90b6` | 5755 |
| `research/brainvision/validate_windows_same_volume_no_replace_promotion_v0_1.py` | `d4c7de5bf04a8928b3d6ce18125fddbcdf1e68555c9a5d8322b0a7a30b833da7` | 134529 |
| `research/brainvision/test_validate_windows_same_volume_no_replace_promotion_v0_1.py` | `f559355e927688ed078f9f38ae25578c7b1654ac0c539b0843a107f5fb8fbae2` | 21162 |
| `research/brainvision/test_validate_windows_same_volume_no_replace_promotion_integration_v0_1.py` | `8c1ebc0c58cbc88883cdd77c4220e525a21dafca7c5b4fe7c2c76878acbc81b7` | 11476 |

## 8. Runtime Declaration Identities

Runtime identities were recomputed from the committed runtime and wrapper helpers,
not copied from prior documents.

| Declaration | Identity |
| --- | --- |
| retained orchestration policy | `3d9b66a180fabf00c8bb6695c74fc9d69d21cd3ac9335cc5d2dc3a1169417531` |
| native helper policy | `e1094b40c5f312e32c48e6ac125c2e961996f52656b951646cecbf7432419928` |
| retained schema | `a82515184f99862dbf9be23730114ad6df81d6ab2b223df1293c7416f4a5ff66` |
| default case set | `b24057bb7ec233414d670a3e1e2aabb90f8a2728ff590b0ed4e811faf8e5f1b1` |
| fixture profile | `3c2f65092fc6efcf58726390e4b4b9ff9ba00a73dbad68eb5b612d49a788a5a1` |
| authority-registry profile | `aa3368028954f86d294fce0dbcf61117be5750dd87202971ae4a2a8d456c2734` |
| evidence chain | `185e4dea85abf436ac93a01632f0b1ab4895086177e2de073608a0c08b2d174b` |
| retained mode identity | `611e626ca0ce858be4a9b8bf594ea7606dcea4048ceba156764f5b32529f1399` |

## 9. Wrapper Declaration Identities

The wrapper does not expose named helpers for every declaration below. These
were derived by applying `wrapper.canonical_json_bytes` and SHA-256 to explicit
canonical declarations of the committed wrapper constants.

| Declaration | Identity |
| --- | --- |
| wrapper schema identity | `fb48da2f80dbe977431551dea6ac5b9869ef506088b57cad1a1752e5c12183b6` |
| wrapper version identity | `8b1287240ec8aa62a18813e565234962d25305931575b24387e1a92e190e7264` |
| real-executor selector identity | `2bf7cd9d8186541c847be151f3a1f13db1278b083b1868421caf4dcbef76cbb2` |
| fixed-path-profile identity | `c92e5906b98e5e3fa497ac86abaa57660a93c44ae8cc663685ed01bc87a7fbb6` |
| wrapper authorization-input schema identity | `5ae200411efaccb9fc847a213566d158740396020007dfb42b595081d369a327` |

## 10. Exact Fixed Paths

| Role | Exact path |
| --- | --- |
| authority registry root | `C:\TORMENT\brainvision_authority\blocker2_s3b_v0_3` |
| fixture root | `C:\TORMENT\brainvision_authoritative_fixture\blocker2_s3b_v0_3` |
| result parent | `C:\TORMENT\brainvision_retained_results\blocker2_s3b_v0_3` |
| future result directory | `C:\TORMENT\brainvision_retained_results\blocker2_s3b_v0_3\9888fd0b1ed0f392df98690eaecaa2b593cfe867a58115ea4661a7d6f2a1ea92` |

The future result directory remains absent.

## 11. Preparation Input

| Field | Value |
| --- | --- |
| path | `C:\TORMENT\brainvision_retained_results\blocker2_s3b_v0_3_preparation\PREPARE_PATHS_INPUT.canonical.json` |
| SHA-256 | `fa0bf1b02acea1a4c52d3724f1d9dbdcbeaf748ca21a32a07faf7d42398322aa` |
| byte length | `19521` |
| wrapper mode | `PREPARE_PATHS` |
| authorization status | `PREPARED_NOT_ACTIVE` |
| execution authorization identity | `9888fd0b1ed0f392df98690eaecaa2b593cfe867a58115ea4661a7d6f2a1ea92` |
| real executor selector | `REAL_EXISTING_ABSOLUTE_PATH_A1_A2_A3_A5_V0_1` |
| A6 selected | `false` |
| fault injection disabled | `true` |

The input was stored outside the repository and is not the final ACTIVE
execution authorization input.

## 12. PREPARE_PATHS Invocation

The only wrapper mode invoked was:

```bat
python -m research.brainvision.run_blocker2_authoritative_retained_single_run_v0_1 --mode PREPARE_PATHS --authorization-input C:\TORMENT\brainvision_retained_results\blocker2_s3b_v0_3_preparation\PREPARE_PATHS_INPUT.canonical.json --format both
```

No `PREFLIGHT_ONLY` or `EXECUTE_EXACT_SINGLE_RUN` invocation was performed.

## 13. Path Admission Results

| Role | Canonical path | Path identity | st_dev | st_ino | Reparse | Repository containment |
| --- | --- | --- | ---: | ---: | --- | --- |
| authority registry root | `C:\TORMENT\brainvision_authority\blocker2_s3b_v0_3` | `8cf4a6200aa912977fc7f63df057f467f8d2238a38f7f9b7cee76b253210afba` | 2698958771 | 3096224745139732 | `NOT_REPARSE_POINT` | `OUTSIDE_REPOSITORY` |
| fixture root | `C:\TORMENT\brainvision_authoritative_fixture\blocker2_s3b_v0_3` | `f9c5f5b62524f345cbb4f5b46cad89553a6054d87bb1048fe4ae61a478be0934` | 2698958771 | 5066549582114327 | `NOT_REPARSE_POINT` | `OUTSIDE_REPOSITORY` |
| result parent | `C:\TORMENT\brainvision_retained_results\blocker2_s3b_v0_3` | `edecbab40b38808b992a9ccde3ebcd233266eef03e8cff02fd46f9aa7e2c83d6` | 2698958771 | 8162774325931544 | `NOT_REPARSE_POINT` | `OUTSIDE_REPOSITORY` |

Volume evidence for all three admitted roots:

| Field | Value |
| --- | --- |
| drive root | `C:\` |
| drive type | `DRIVE_FIXED` |
| drive type code | `3` |
| filesystem name | `NTFS` |
| max component length | `255` |
| volume serial number | `2698958771` |

Decision:

```text
EXACT_PATHS_PREPARED_AND_ADMITTED
```

## 14. Preparation Result Record

| Field | Value |
| --- | --- |
| external canonical result path | `C:\TORMENT\brainvision_retained_results\blocker2_s3b_v0_3_preparation\PREPARE_PATHS_RESULT.canonical.json` |
| stdout capture path | `C:\TORMENT\brainvision_retained_results\blocker2_s3b_v0_3_preparation\PREPARE_PATHS_STDOUT.txt` |
| result SHA-256 | `51600a85ee8e49187e3c443e337ea8a23688ecdd19e47aa843b64ed17ce33a16` |
| result byte length | `3726` |
| terminal label | `PREPARATION_COMPLETE` |
| wrapper version | `v0.1` |
| retained execution | `false` |
| authority consumed | `false` |
| authoritative result field | `false` |
| detail | `OK` |
| error classification | `NONE` |

The retained result record is non-authoritative operator evidence. It is not a
`GLOBAL_AUTHORITY_ENTRY`, `RUN_RESULT`, `RETAINED_COMPLETION`, scientific
completion, or BLOCKER-2 closure artifact.

## 15. Evidence-Object Absence

| Evidence object | Exact path | State |
| --- | --- | --- |
| result directory | `C:\TORMENT\brainvision_retained_results\blocker2_s3b_v0_3\9888fd0b1ed0f392df98690eaecaa2b593cfe867a58115ea4661a7d6f2a1ea92` | `ABSENT` |
| global authority entry | `C:\TORMENT\brainvision_authority\blocker2_s3b_v0_3\9888fd0b1ed0f392df98690eaecaa2b593cfe867a58115ea4661a7d6f2a1ea92.global_authority_entry.canonical.json` | `ABSENT` |
| local gate | `C:\TORMENT\brainvision_retained_results\blocker2_s3b_v0_3\9888fd0b1ed0f392df98690eaecaa2b593cfe867a58115ea4661a7d6f2a1ea92\gate_entry.canonical.json` | `ABSENT` |
| RUN_RESULT | `C:\TORMENT\brainvision_retained_results\blocker2_s3b_v0_3\9888fd0b1ed0f392df98690eaecaa2b593cfe867a58115ea4661a7d6f2a1ea92\run_result.canonical.json` | `ABSENT` |
| RETAINED_COMPLETION | `C:\TORMENT\brainvision_retained_results\blocker2_s3b_v0_3\9888fd0b1ed0f392df98690eaecaa2b593cfe867a58115ea4661a7d6f2a1ea92\retained_completion.canonical.json` | `ABSENT` |

## 16. Authority-Consumption State

Decision:

```text
AUTHORITY_UNCONSUMED
```

The wrapper result reported:

```text
authority_consumed = false
retained_execution = false
authoritative = false
```

No global authority entry exists at the derived path.

## 17. Remaining Activation Requirements

Before any later final execution preflight or retained run:

```text
prepare final inactive authorization input
bind this findings document after commit if it is selected as controlling input
commit and synchronize the final inactive authorization material
collect post-commit Git blob and checked-out-byte identities
review the exact final inactive input
run only the authorized non-consuming preflight in a later phase
activate only after independent authorization
invoke EXECUTE_EXACT_SINGLE_RUN at most once only if later authorized
```

Activation readiness decision:

```text
READY_TO_PREPARE_FINAL_INACTIVE_AUTHORIZATION
```

## 18. Claims Supported

Supported:

```text
the committed wrapper identity is bound
all nine execution-surface file identities are recorded
the runtime declaration identities were recomputed
the wrapper declaration identities were derived from committed constants
the three exact fixed roots were created or admitted by PREPARE_PATHS
the admitted roots are ordinary non-reparse outside-repository directories
the admitted roots are on a local fixed NTFS volume
the future result directory is absent
authority remains unconsumed
BLOCKER-2 remains open
```

## 19. Claims Not Supported

Not supported:

```text
authoritative retained execution occurred
PREFLIGHT_ONLY accepted a final execution authorization
native A1/A2/A3/A5 executed
global authority was consumed
LOCAL_GATE_ENTRY was created
RUN_RESULT was created
RETAINED_COMPLETION was created
BLOCKER-2 is closed
BLOCKER-4 has started
production readiness
general Windows support
rename atomicity
rename durability
power-loss persistence
scientific completion
```

## 20. Readiness Decisions

| Readiness item | Decision |
| --- | --- |
| Wrapper committed identity | `WRAPPER_COMMITTED_IDENTITY_BOUND` |
| Path preparation | `EXACT_PATHS_PREPARED_AND_ADMITTED` |
| Authority state | `AUTHORITY_UNCONSUMED` |
| Activation readiness | `READY_TO_PREPARE_FINAL_INACTIVE_AUTHORIZATION` |

## 21. Final Verdict

```text
A. ACCEPT_COMMITTED_WRAPPER_AND_PREPARED_PATHS
```

This verdict is selected because all nine committed identities match their
checked-out files, the wrapper declaration identities were computed from the
committed wrapper constants, all three fixed roots are prepared and admitted,
the future result directory is absent, all evidence objects are absent, and
authority remains unconsumed.

## 22. Exact Next Step

Exact next step:

```text
Prepare the final inactive authorization input and post-commit identity binding
materials for later review, without running PREFLIGHT_ONLY against a final
authorization and without invoking EXECUTE_EXACT_SINGLE_RUN.
```

Return control to Hilmir.

# TORMENT Brainvision Stage S3B v0.3
# BLOCKER-2 Exact Authoritative Retained Single-Run Authorization v0.1

## 0. Document Status

document_class = BLOCKER-2 exact authoritative retained single-run authorization
document_version = v0.1
document_mode = docs-only prepared authorization assessment
authorization_status = PREPARED_NOT_ACTIVE

This document binds the committed BLOCKER-2 retained runtime at
`0e8e8d1d331792036c96db87477db5023919f05e` to final source, document,
schema, policy, case-set, fixture-profile, authority-registry, and
evidence-chain identities. It does not execute the retained run, does not
create an authority entry, does not create a local gate, does not create a
`RUN_RESULT`, does not create a `RETAINED_COMPLETION`, and does not consume
authority.

Machine-readable status block:

```text
authorization_status = "PREPARED_NOT_ACTIVE"
repository_commit = "0e8e8d1d331792036c96db87477db5023919f05e"
head_equals_origin_main = true
working_tree_clean = true
a6_selected = false
authoritative_retained_run_executed = false
global_authority_consumed = false
local_gate_created = false
run_result_created = false
retained_completion_created = false
blocker_2_state = "OPEN"
blocker_4_started = false
```

## 1. Authorization Question

Question:

```text
Can one exact authoritative retained BLOCKER-2 absolute-path control run be
authorized now from the committed runtime and committed identity inventory?
```

Answer:

```text
No direct execution authorization is active. The committed runtime is
identity-bindable and the intended one-run contract can be specified, but
operator path preparation, post-commit authorization self-identity activation,
and a stable operator execution surface are not complete.
```

This document therefore prepares an inactive identity-bound authorization model
and records the blockers that prevent direct execution.

## 2. Authoritative Baseline

Read-only baseline verified before this document was written:

| Field | Value |
| --- | --- |
| branch | `main` |
| HEAD | `0e8e8d1d331792036c96db87477db5023919f05e` |
| origin/main | `0e8e8d1d331792036c96db87477db5023919f05e` |
| HEAD == origin/main | `true` |
| working tree | `clean` |
| `.git/index.lock` | `absent` |

Reviewed lineage:

```text
0e8e8d1 research(brainvision): complete blocker 2 retained runtime
b647814 docs(research): authorize blocker 2 retained runtime correction
0503f1c docs(research): assess blocker 2 retained runtime readiness
e144752 research(brainvision): implement blocker 2 retained-run preparation
4a9d58a docs(research): authorize blocker 2 retained-run preparation
23504da docs(research): assess blocker 2 retained single-run readiness
82d6fce docs(research): record blocker 2 absolute-path control findings
03727e7 research(brainvision): implement blocker 2 absolute-path control
e34d3d4 docs(research): authorize blocker 2 absolute-path control
9ab500f docs(research): assess blocker 2 absolute-path control
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

This document does not modify or authorize modification of
`torment_service/kernel/`, production TORMENT memory functionality, live
service behavior, prompt surfaces, action surfaces, autonomy, identity, truth
selection, or memory cognition.

This document does not open live visual capture, real gameplay, real video
execution, production publication, production recovery, general live-test lanes,
or BLOCKER-4.

BLOCKER state remains:

| Blocker | State |
| --- | --- |
| BLOCKER-1 | closed within its exact bounded Windows durability profile |
| BLOCKER-2 | `OPEN` |
| BLOCKER-3 | already closed |
| BLOCKER-4 | open and separate, not active |

## 4. Controlling Documents

The controlling documents read for this authorization are:

```text
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_AUTHORITATIVE_RETAINED_SINGLE_RUN_ASSESSMENT_v0.1.md
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_RETAINED_SINGLE_RUN_IMPLEMENTATION_PREPARATION_AUTHORIZATION_v0.1.md
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_POST_COMMIT_IDENTITY_BINDING_AND_EXECUTION_READINESS_ASSESSMENT_v0.1.md
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_POST_COMMIT_RUNTIME_CORRECTION_AUTHORIZATION_v0.1.md
```

Their committed identities are bound in section 9.

## 5. Final Committed Runtime

The final committed runtime and focused tests reviewed are:

```text
research/brainvision/blocker2_retained_absolute_path_control_v0_1.py
research/brainvision/test_blocker2_retained_absolute_path_control_v0_1.py
research/brainvision/test_blocker2_retained_absolute_path_control_integration_v0_1.py
research/brainvision/validate_windows_same_volume_no_replace_promotion_v0_1.py
research/brainvision/test_validate_windows_same_volume_no_replace_promotion_v0_1.py
research/brainvision/test_validate_windows_same_volume_no_replace_promotion_integration_v0_1.py
```

Supporting public API surfaces reviewed where needed:

```text
durable_evidence_schema_v0_3 canonicalization and SHA-256 helpers
durable_evidence_windows_adapter_v0_3 directory durability interfaces
validate_windows_same_volume_no_replace_promotion_v0_1 native A-case helpers
```

The retained runtime exposes `run_retained_single_run`,
`build_execution_authorization_identity_block`, and
`execute_existing_absolute_path_retained_case_set`. The reviewed committed
retained files do not expose a stable command-line operator interface with
argument parsing for the complete identity block.

## 6. Repository Identity

Repository identity:

```text
repository_commit = "0e8e8d1d331792036c96db87477db5023919f05e"
branch = "main"
HEAD = "0e8e8d1d331792036c96db87477db5023919f05e"
origin_main = "0e8e8d1d331792036c96db87477db5023919f05e"
head_equals_origin_main = true
working_tree_clean_at_baseline = true
index_lock_absent_at_baseline = true
```

## 7. Git Blob Identity Inventory

Git blob IDs were collected from `HEAD:<path>` and rechecked with
`git hash-object <path>`.

| File | Git blob |
| --- | --- |
| `research/brainvision/blocker2_retained_absolute_path_control_v0_1.py` | `99976d61f23145e36277d89a4d2db2bf45e8a010` |
| `research/brainvision/test_blocker2_retained_absolute_path_control_v0_1.py` | `fd90aca033cee89864841ae7ca993e94c35b1c1f` |
| `research/brainvision/test_blocker2_retained_absolute_path_control_integration_v0_1.py` | `89de880f4d5c51bb0b055c584d53a79fe006d54f` |
| `research/brainvision/validate_windows_same_volume_no_replace_promotion_v0_1.py` | `5a662d0a6c7d56f53e20ba4b8db56fee731c8057` |
| `research/brainvision/test_validate_windows_same_volume_no_replace_promotion_v0_1.py` | `471baebc50d08d38c68042486ef0eb3fb6d0d186` |
| `research/brainvision/test_validate_windows_same_volume_no_replace_promotion_integration_v0_1.py` | `c9435db7ca1b7e418494b4f9ff224823a8b6ba38` |

No source identity is `UNAVAILABLE_UNTIL_COMMIT`.

## 8. Checked-Out-Byte SHA-256 Inventory

Checked-out-byte SHA-256 values were computed from exact filesystem bytes
without line-ending or encoding normalization.

| File | Checked-out SHA-256 | Bytes |
| --- | --- | ---: |
| `research/brainvision/blocker2_retained_absolute_path_control_v0_1.py` | `878511058fc221858718febfd8979fc0d9c2e752d81e5c2580bcc6dbc119d8f7` | 137543 |
| `research/brainvision/test_blocker2_retained_absolute_path_control_v0_1.py` | `eff1e225136bccf49393f8098628527a0bd5c5b73c5565b75b62389eab1d9ecb` | 37182 |
| `research/brainvision/test_blocker2_retained_absolute_path_control_integration_v0_1.py` | `193dfac7db9b4c9683cfdd36b71a549b0a012975be090a433ef839c0b8bb90b6` | 5755 |
| `research/brainvision/validate_windows_same_volume_no_replace_promotion_v0_1.py` | `d4c7de5bf04a8928b3d6ce18125fddbcdf1e68555c9a5d8322b0a7a30b833da7` | 134529 |
| `research/brainvision/test_validate_windows_same_volume_no_replace_promotion_v0_1.py` | `f559355e927688ed078f9f38ae25578c7b1654ac0c539b0843a107f5fb8fbae2` | 21162 |
| `research/brainvision/test_validate_windows_same_volume_no_replace_promotion_integration_v0_1.py` | `8c1ebc0c58cbc88883cdd77c4220e525a21dafca7c5b4fe7c2c76878acbc81b7` | 11476 |

## 9. Document Identity Inventory

| Document | Git blob | Checked-out SHA-256 | Bytes |
| --- | --- | --- | ---: |
| `docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_AUTHORITATIVE_RETAINED_SINGLE_RUN_ASSESSMENT_v0.1.md` | `103d66aaff200bb7cc35271f2f7d74d11ce5663b` | `71b4e96da222461c16caea6494719183504e758b6e883b44c4db8df9b636f51d` | 30551 |
| `docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_RETAINED_SINGLE_RUN_IMPLEMENTATION_PREPARATION_AUTHORIZATION_v0.1.md` | `e54d9badc18a9503edd8fb540a7c43782f084e71` | `0ea41794b6d6503576afa84a14f629ca25baff5b7d78c0a2f8a4bbb806d1959e` | 44275 |
| `docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_POST_COMMIT_IDENTITY_BINDING_AND_EXECUTION_READINESS_ASSESSMENT_v0.1.md` | `dbd56f3d17f3da68e4a19334dd2e09192998277e` | `b5defa92d46f7cf98499e843a5910af4ca737ebd53ada9b36a3de01cc2c83a6f` | 24970 |
| `docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_POST_COMMIT_RUNTIME_CORRECTION_AUTHORIZATION_v0.1.md` | `e67891dbdf1ca063a02d0e05cb397f97ee097ca8` | `6e593ca45773f8fab880ba3cf3209dcd8db1e6e9dcf17bf1f2c6d69535a29a92` | 17710 |

This new authorization document is self-excluding at creation time. Its own
future committed identity must be bound after Hilmir commits and synchronizes it:

```text
post_commit_authorization_git_blob = REQUIRED_BEFORE_EXECUTION
post_commit_authorization_checked_out_sha256 = REQUIRED_BEFORE_EXECUTION
post_commit_authorization_repository_head = REQUIRED_BEFORE_EXECUTION
```

The run must remain non-executable until those post-commit identities are
available and accepted by the execution authorization identity block.

## 10. Runtime Declaration Identities

Runtime declaration identities were recomputed from the committed module.

| Runtime declaration | Identity |
| --- | --- |
| retained orchestration policy | `3d9b66a180fabf00c8bb6695c74fc9d69d21cd3ac9335cc5d2dc3a1169417531` |
| native helper policy | `e1094b40c5f312e32c48e6ac125c2e961996f52656b951646cecbf7432419928` |
| retained schema | `a82515184f99862dbf9be23730114ad6df81d6ab2b223df1293c7416f4a5ff66` |
| default case set | `b24057bb7ec233414d670a3e1e2aabb90f8a2728ff590b0ed4e811faf8e5f1b1` |
| case set with A6 | `0b9c7f22cf7f7b4e927c7be76bc559ad780891126003b6129fd2a83c375756af` |
| fixture profile | `3c2f65092fc6efcf58726390e4b4b9ff9ba00a73dbad68eb5b612d49a788a5a1` |
| authority registry profile | `aa3368028954f86d294fce0dbcf61117be5750dd87202971ae4a2a8d456c2734` |
| evidence chain | `185e4dea85abf436ac93a01632f0b1ab4895086177e2de073608a0c08b2d174b` |
| retained mode string | `BLOCKER2_ABSOLUTE_PATH_CONTROL_RETAINED_SINGLE_RUN_V0_1` |
| authorization-declaration retained mode identity | `611e626ca0ce858be4a9b8bf594ea7606dcea4048ceba156764f5b32529f1399` |

The final item is not a separate exported runtime helper. It is the canonical
SHA-256 of:

```text
schema = "torment.brainvision.blocker2.retained.mode_identity.v0.1"
retained_mode = "BLOCKER2_ABSOLUTE_PATH_CONTROL_RETAINED_SINGLE_RUN_V0_1"
```

## 11. Exact Case Set and Order

Authorized completion-gating case set:

```text
A1
A2
A3
A5
```

Execution order:

```text
A1
A2
A3
A5
```

Selected optional diagnostic cases:

```text
none
```

Machine-readable selection:

```text
a6_selected = false
case_set_identity = "b24057bb7ec233414d670a3e1e2aabb90f8a2728ff590b0ed4e811faf8e5f1b1"
```

Cases A4, A7, and A8 are prohibited for this retained run.

## 12. Exact Path Bindings

Preferred operator path model:

| Role | Proposed path |
| --- | --- |
| authority registry root | `C:\TORMENT\brainvision_authority\blocker2_s3b_v0_3` |
| fixture root | `C:\TORMENT\brainvision_authoritative_fixture\blocker2_s3b_v0_3` |
| result parent | `C:\TORMENT\brainvision_retained_results\blocker2_s3b_v0_3` |
| result directory | `<result parent>\<execution-authorization-derived immutable directory>` |

Read-only path observation during this document creation:

```text
C:\TORMENT\brainvision_authority\blocker2_s3b_v0_3 = ABSENT
C:\TORMENT\brainvision_authoritative_fixture\blocker2_s3b_v0_3 = ABSENT
C:\TORMENT\brainvision_retained_results\blocker2_s3b_v0_3 = ABSENT
```

Because those roots are absent, this document cannot honestly bind ordinary,
non-reparse, local fixed NTFS path identities for them. The following are
therefore required before execution:

```text
authority_registry_root_identity = REQUIRED_AFTER_OPERATOR_PATH_PREPARATION
fixture_root_identity = REQUIRED_AFTER_OPERATOR_PATH_PREPARATION
result_parent_identity = REQUIRED_AFTER_OPERATOR_PATH_PREPARATION
result_directory_identity = REQUIRED_AFTER_AUTHORIZATION_DERIVATION
authority_entry_path = REQUIRED_AFTER_AUTHORIZATION_DERIVATION
local_gate_path = REQUIRED_AFTER_AUTHORIZATION_DERIVATION
RUN_RESULT_path = REQUIRED_AFTER_AUTHORIZATION_DERIVATION
RETAINED_COMPLETION_path = REQUIRED_AFTER_AUTHORIZATION_DERIVATION
```

Changing any prepared path must produce a different execution authorization and
run identity.

## 13. Execution Authorization Identity

Required canonical execution-authorization declaration:

```text
schema = "torment.brainvision.blocker2.retained.execution_authorization_identity.v0.1"
retained_mode = "BLOCKER2_ABSOLUTE_PATH_CONTROL_RETAINED_SINGLE_RUN_V0_1"
authoritative = true
repository_commit = "0e8e8d1d331792036c96db87477db5023919f05e"
branch = "main"
origin_main = "0e8e8d1d331792036c96db87477db5023919f05e"
six_git_blob_identities = section_7
six_checked_out_byte_sha256_identities = section_8
four_controlling_document_identities = section_9
post_commit_authorization_document_identity = REQUIRED_BEFORE_EXECUTION
retained_orchestration_policy_sha256 = "3d9b66a180fabf00c8bb6695c74fc9d69d21cd3ac9335cc5d2dc3a1169417531"
native_helper_policy_sha256 = "e1094b40c5f312e32c48e6ac125c2e961996f52656b951646cecbf7432419928"
retained_schema_sha256 = "a82515184f99862dbf9be23730114ad6df81d6ab2b223df1293c7416f4a5ff66"
case_set_sha256 = "b24057bb7ec233414d670a3e1e2aabb90f8a2728ff590b0ed4e811faf8e5f1b1"
fixture_profile_sha256 = "3c2f65092fc6efcf58726390e4b4b9ff9ba00a73dbad68eb5b612d49a788a5a1"
authority_registry_profile_sha256 = "aa3368028954f86d294fce0dbcf61117be5750dd87202971ae4a2a8d456c2734"
evidence_chain_sha256 = "185e4dea85abf436ac93a01632f0b1ab4895086177e2de073608a0c08b2d174b"
retained_mode_identity = "611e626ca0ce858be4a9b8bf594ea7606dcea4048ceba156764f5b32529f1399"
authority_registry_root_identity = REQUIRED_AFTER_OPERATOR_PATH_PREPARATION
fixture_root_identity = REQUIRED_AFTER_OPERATOR_PATH_PREPARATION
result_parent_identity = REQUIRED_AFTER_OPERATOR_PATH_PREPARATION
result_directory_identity = REQUIRED_AFTER_AUTHORIZATION_DERIVATION
operator_identity = "Hilmir"
process_contract = "one Windows Command Prompt process"
conda_environment = "torment"
single_attempt = true
a6_selected = false
```

The committed runtime currently derives an execution authorization identity
from a narrower identity block. It binds source identities and path identities,
but it does not accept this authorization document's future Git blob and
checked-out-byte identities as runtime-validated inputs. That gap prevents this
document from activating direct execution without a runtime or wrapper
correction that validates the post-commit authorization identity.

## 14. Run Identity

Required canonical run-identity declaration:

```text
schema = "torment.brainvision.blocker2.retained.run_identity.v0.1"
execution_authorization_identity = REQUIRED_AFTER_SECTION_13_COMPLETION
authority_registry_root_identity = REQUIRED_AFTER_OPERATOR_PATH_PREPARATION
fixture_root_identity = REQUIRED_AFTER_OPERATOR_PATH_PREPARATION
result_parent_identity = REQUIRED_AFTER_OPERATOR_PATH_PREPARATION
result_directory_identity = REQUIRED_AFTER_AUTHORIZATION_DERIVATION
repository_commit = "0e8e8d1d331792036c96db87477db5023919f05e"
case_set_sha256 = "b24057bb7ec233414d670a3e1e2aabb90f8a2728ff590b0ed4e811faf8e5f1b1"
execution_order = "A1,A2,A3,A5"
a6_selected = false
```

The run identity is not computed here because the required path identities and
post-commit authorization document identity are not yet available.

## 15. Operator Contract

Authorized operator after all activation blockers are resolved:

```text
operator = "Hilmir"
host_context = "authorized Windows workstation"
process = "one Windows Command Prompt process"
conda_environment = "torment"
invocations = 1
attempts = 1
authority_registry_root = one admitted prepared root
fixture_root = one admitted prepared root
result_directory = one authorization-derived absent directory
```

Not authorized:

```text
rerun
retry
resume
force
overwrite
repair
release
reset
ignore-existing
second process
parallel execution
```

If preflight fails before the durable global authority entry, authority remains
unconsumed. Once the global authority entry is durably verified, all later
failure or interruption spends the authorization.

## 16. Exact Execution Command

No exact execution command is ready.

Source review found an importable retained execution path but did not find a
committed retained operator CLI that can supply:

```text
explicit retained mode
authoritative request
execution-authorization identity block
authority-registry root
fixture root
result parent/result directory
exact case set
A6 false
post-commit authorization document identities
```

Ad hoc `python -c` snippets are not authorized as the operator surface. A
narrow committed operator wrapper or equivalent stable CLI is required before
execution can be authorized.

## 17. Preflight Contract

Before any execution, the operator must verify:

```text
branch == main
HEAD == 0e8e8d1d331792036c96db87477db5023919f05e
origin/main == 0e8e8d1d331792036c96db87477db5023919f05e
HEAD == origin/main
working tree clean
.git/index.lock absent
all six Git blobs match section 7
all six checked-out-byte hashes match section 8
all controlling-document identities match section 9
this authorization document's post-commit identities are supplied and verified
all runtime declaration identities match section 10
no UNAVAILABLE_UNTIL_COMMIT source identities
authority registry root admitted
fixture root admitted
result parent admitted
result directory absent
global authority entry absent
local gate absent
RUN_RESULT absent
RETAINED_COMPLETION absent
fault injection disabled
real executor selected
A6 false
```

Any mismatch before durable global authority entry leaves authority unconsumed.

## 18. Real Executor Binding

Required executor:

```text
execute_existing_absolute_path_retained_case_set
```

This binds to the committed native helper lane:

```text
SetFileInformationByHandle
FileRenameInfo
ReplaceIfExists = FALSE
RootDirectory = NULL
canonical drive-qualified absolute Win32 DOS destination
```

Prohibited executor forms:

```text
synthetic executor
mock executor
test executor
lambda
in-memory fabricated case outcomes
fault-injection executor
fallback native primitive
```

## 19. Expected Gating Outcomes

A1 must show positive absolute-path transition success, coherent source/final
evidence, retained identity evidence, and content continuity.

A2 must retain `ERROR_ALREADY_EXISTS / 183`, preserve source, preserve the
destination directory, and retain raw numeric and symbolic error evidence.

A3 must retain `ERROR_ALREADY_EXISTS / 183`, preserve source, preserve the
destination file, and retain raw numeric and symbolic error evidence.

A5 must verify:

```text
source identity == retained source-handle identity == reopened final-path identity
```

and content continuity must pass.

Any gating mismatch prevents completion. Unexpected native errors fail closed.

## 20. Global Authority Consumption

Authorized evidence-chain first record:

```text
GLOBAL_AUTHORITY_ENTRY
```

The global authority entry must be exclusive-created from the execution
authorization identity, flushed, parent-directory synced through the bounded
BLOCKER-1 durability adapter, reread, and hash-verified before the local gate.

After this record is verified, the authority is consumed.

## 21. Local Gate

Authorized evidence-chain second record:

```text
LOCAL_GATE_ENTRY
```

The local gate must bind:

```text
global authority entry path
global authority entry hash
execution authorization identity
fixture root
result parent
result directory identity
attempt identity
retained mode
expected identity values
```

Native execution is prohibited unless the local gate is durably verified.

## 22. RUN_RESULT

Authorized evidence-chain third record:

```text
RUN_RESULT
```

The run result records native case observations, retained envelopes, execution
status, and upstream hashes. It must report:

```text
retained_execution = false
completion_receipt = "ABSENT"
```

The run result is not allowed to claim final retained completion.

## 23. RETAINED_COMPLETION

Authorized evidence-chain fourth record:

```text
RETAINED_COMPLETION
```

This is the only record permitted to declare:

```text
retained_execution = true
```

It may exist only after durable verification of the global authority entry,
local gate, native case run, and `RUN_RESULT`, and only after the retained
evaluator accepts every required identity and gating outcome.

## 24. Evidence-Chain Linkage

Required chain:

```text
GLOBAL_AUTHORITY_ENTRY
->
LOCAL_GATE_ENTRY
->
RUN_RESULT
->
RETAINED_COMPLETION
```

Every downstream record must bind the hash of the upstream record it depends
on. Missing, mismatched, or unverifiable linkage fails the run and spends the
authorization if the global authority entry has already been verified.

## 25. Success Contract

Successful terminal status equivalent:

```text
AUTHORITATIVE_RETAINED_RUN_COMPLETE
```

Success requires durable verified global authority entry, durable verified
local gate, accepted A1/A2/A3/A5 gating outcomes, dual-policy evidence, raw
errors retained, identity continuity, content continuity, durable verified
`RUN_RESULT`, durable verified `RETAINED_COMPLETION`, matching chain hashes and
shared identities, and fault injection inactive.

Process exit code zero is insufficient.

## 26. Failure and Rerun Contract

Pre-consumption failure:

```text
failure before durable verified GLOBAL_AUTHORITY_ENTRY
same authorization may remain unused only if no durable global entry exists
```

Post-consumption failure:

```text
failure after durable verified GLOBAL_AUTHORITY_ENTRY
same authorization may never be reused
fresh docs-only authorization required
```

The operator must not interpret a missing terminal artifact as permission to
retry.

## 27. Pre-Execution Test Replay

Immediately before any future authority-consuming command, require focused
read-only replay:

```bat
python -B -m py_compile research\brainvision\blocker2_retained_absolute_path_control_v0_1.py research\brainvision\test_blocker2_retained_absolute_path_control_v0_1.py research\brainvision\test_blocker2_retained_absolute_path_control_integration_v0_1.py research\brainvision\validate_windows_same_volume_no_replace_promotion_v0_1.py research\brainvision\test_validate_windows_same_volume_no_replace_promotion_v0_1.py research\brainvision\test_validate_windows_same_volume_no_replace_promotion_integration_v0_1.py
```

Required focused inventory:

```text
19 retained unit
1 retained integration
48 legacy regression
68 combined
```

The test replay must occur before the authority-consuming command and must not
create real authority objects. If any test fails or skips unexpectedly, do not
execute the authoritative run.

## 28. Post-Commit Activation

Stage 1:

```text
authorization_status = PREPARED_NOT_ACTIVE
```

Stage 2, after Hilmir commits and synchronizes this document, must collect:

```text
authorization Git blob ID
authorization checked-out-byte SHA-256
final repository HEAD
origin/main
working-tree cleanliness
```

The run becomes executable only if the committed authorization's own
identities are supplied to and validated by the runtime identity block. Current
source review indicates the committed runtime does not yet accept this
authorization document's post-commit identities as execution-authorization
inputs.

## 29. Claims Supported

Supported:

```text
the final retained runtime is committed and identity-bound
one bounded authoritative run contract is procedurally prepared
the authority remains unconsumed
the evidence chain and success contract are specified
BLOCKER-2 remains OPEN
```

## 30. Claims Not Supported

Not supported:

```text
the retained run succeeded
rename atomicity
rename durability
power-loss persistence
general Windows FileRenameInfo support
production readiness
BLOCKER-2 closure
real-world Brainvision readiness
strong order sensitivity
IMMUTABLE_SCIENTIFIC_BUNDLE
SCIENTIFIC_COMPLETION
publication
scientific truth transition
```

## 31. Authorization Decisions

| Decision | Value | Reason |
| --- | --- | --- |
| Identity completeness | `FINAL_IDENTITY_BINDING_INCOMPLETE` | This document's post-commit identities are unavailable and the runtime does not yet accept them as validated inputs. |
| Operator-path readiness | `OPERATOR_PATH_PREPARATION_REQUIRED` | Preferred roots are currently absent and no ordinary/non-reparse/local-fixed-NTFS path evidence was collected. |
| CLI readiness | `NARROW_OPERATOR_WRAPPER_REQUIRED` | The committed retained runtime exposes functions, not a stable operator CLI for the complete identity block. |
| Runtime readiness | `RUNTIME_REQUIRES_NARROW_CORRECTION` | The exact authorization contract requires post-commit authorization-document identity validation that the current runtime does not expose. |
| Authorization outcome | `REQUIRE_RUNTIME_CORRECTION_BEFORE_AUTHORIZATION` | Direct authority-consuming execution is not justified. |

## 32. Final Verdict

```text
C. REQUIRE_NARROW_RUNTIME_CORRECTION
```

This verdict is selected because the exact one-run contract cannot become
active merely through this document. The missing stable operator surface,
operator path preparation, and runtime acceptance of this document's
post-commit identities must be resolved first.

## 33. Exact Next Step

Return control to Hilmir.

Exact next step:

```text
Prepare operator paths and a narrow committed operator/runtime activation
surface that can validate this authorization document's post-commit identities
before any authoritative retained run is attempted.
```

No commit, push, authoritative run, authority consumption, retained evidence
creation, BLOCKER-2 closure, or BLOCKER-4 work is authorized by this document.

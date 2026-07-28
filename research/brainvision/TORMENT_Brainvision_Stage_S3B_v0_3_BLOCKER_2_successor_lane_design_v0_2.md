# TORMENT Brainvision Stage S3B v0.3 BLOCKER-2 Successor-Lane Design v0.2

## 1. Executive disposition

This document completes a documentation-only successor-lane design and final baseline identity verification for BLOCKER-2 after acceptance of the v0.3 post-correction assessment.

Version disposition:

```text
v0.1: superseded and absent as an untracked operational candidate
v0.2: current untracked design candidate pending independent acceptance
```

v0.2 supersedes v0.1 because v0.1 hardcoded the accepted assessment HEAD into future `PREPARE_PATHS` bindings and treated the design commit/push path as conditional. v0.2 makes the design commit-and-push sequence mandatory and uses symbolic `ACCEPTED_SUCCESSOR_DESIGN_HEAD` for future live canonical input binding.

The accepted repository baseline for this design is:

```text
branch: main
HEAD: 94cf0b9a4d4f1e83b00178ccca3363f4e6eed73f
origin/main: 94cf0b9a4d4f1e83b00178ccca3363f4e6eed73f
working tree before this design document: clean
corrective implementation provenance: 3e516bd3714b75b0a7c6b760e44fd02439837700
accepted successor-assessment commit: 94cf0b9a4d4f1e83b00178ccca3363f4e6eed73f
future accepted design baseline: ACCEPTED_SUCCESSOR_DESIGN_HEAD, not yet created
FORMAL_HOLD: active
Mode 0: active
BLOCKER-2: open
BLOCKER-4: inactive
```

Static identities and authorized implementation-surface identities were recomputed from the accepted assessment baseline. No predicted-stable identity changed. The successor lane may proceed only to independent review, design commit/push by Hilmir, final design-baseline reconfirmation, and then separate governance. No canonical input is ready to be prepared or invoked in this task.

Conclusion:

```text
B. DESIGN_COMPLETE_WITH_GOVERNANCE_PREREQUISITES
```

## 2. Scope and prohibitions

This task is documentation-only. It did not invoke `PREPARE_PATHS`, `PREFLIGHT_ONLY`, or `EXECUTE_EXACT_SINGLE_RUN`. It did not create canonical inputs, authority entries, governance artifacts, path-preparation records, result directories, gate entries, run results, retained-completion artifacts, or execution-capable artifacts.

The only file produced by this task is this Markdown design candidate. While it remains untracked, it is a dirty unrelated surface and blocks any repository-validated runner mode.

The next executable action is not authorized here. Hilmir must independently accept the design, resolve the repository-state binding issue described below, and authorize any canonical preparation separately.

## 3. Accepted repository baseline

Safety checks performed before creating this document:

```text
git rev-parse HEAD
94cf0b9a4d4f1e83b00178ccca3363f4e6eed73f

git rev-parse origin/main
94cf0b9a4d4f1e83b00178ccca3363f4e6eed73f

git merge-base --is-ancestor 3e516bd3714b75b0a7c6b760e44fd02439837700 HEAD
success

.git/index.lock
absent

git status --short --branch --untracked-files=all
## main...origin/main
```

The accepted assessment file at HEAD is:

```text
research/brainvision/TORMENT_Brainvision_Stage_S3B_v0_3_BLOCKER_2_post_correction_successor_lane_assessment_v0_3.md
```

Its current accepted file identity is:

```text
Git blob OID: 8b6e35e5add4f4c020429d9d3d1c422637fb35b2
byte length: 57230
SHA-256: 09240632a8b27ff5ce6cd001d89aef59211c0399f5084cfcfc73fcd234c5214a
```

## 4. Corrective provenance and accepted binding HEAD

Three repository identities are distinct and must not be collapsed.

Corrective implementation provenance:

```text
CORRECTIVE_IMPLEMENTATION_COMMIT:
3e516bd3714b75b0a7c6b760e44fd02439837700
```

This commit is permanent provenance and an ancestry anchor only. It is not the successor repository-state binding.

Accepted assessment baseline:

```text
ACCEPTED_ASSESSMENT_BASELINE_HEAD:
94cf0b9a4d4f1e83b00178ccca3363f4e6eed73f
```

This is the clean synchronized baseline against which design v0.2 is drafted and reviewed. It is not the future live `PREPARE_PATHS` binding after design v0.2 is accepted, committed, and pushed.

Future accepted design baseline:

```text
ACCEPTED_SUCCESSOR_DESIGN_HEAD:
the exact Git commit created by Hilmir after independent acceptance of design v0.2,
pushed to origin/main, and verified as
HEAD == origin/main == ACCEPTED_SUCCESSOR_DESIGN_HEAD
```

The value of `ACCEPTED_SUCCESSOR_DESIGN_HEAD` is not known in this design-only task and must not be invented or hardcoded. All future canonical `PREPARE_PATHS`, `PREFLIGHT_ONLY`, and `EXECUTE_EXACT_SINGLE_RUN` input bindings must use:

```text
expected_head: ACCEPTED_SUCCESSOR_DESIGN_HEAD
expected_origin_main: ACCEPTED_SUCCESSOR_DESIGN_HEAD
repository_identity.head: ACCEPTED_SUCCESSOR_DESIGN_HEAD
repository_identity.origin_main: ACCEPTED_SUCCESSOR_DESIGN_HEAD
required invariant: HEAD == origin/main == ACCEPTED_SUCCESSOR_DESIGN_HEAD
```

This value becomes known only after independent design acceptance, Hilmir's design commit, push to `origin/main`, and clean synchronized baseline verification.

The accepted design binding must be carried or validated by all of the following repository-state surfaces:

```text
top-level repository_identity.head
top-level repository_identity.origin_main
top-level repository_identity.head_equals_origin_main
top-level repository_state.head
top-level repository_state.origin_main
retained_authorization.expected_head
retained_authorization.expected_origin_main
execution_authorization_identity_block.expected_head
execution_authorization_identity_block.expected_origin_main
execution_authorization_identity_declaration.expected_head
execution_authorization_identity_declaration.expected_origin_main
run_identity_declaration.expected_head
run_identity_declaration.expected_origin_main
source_identity_inventory Git blobs and checked-out bytes
document_identity_inventory Git blobs and checked-out bytes
source_observations Git blobs and checked-out bytes
authorization_input_identity, because it hashes the non-circular canonical authorization payload
```

Any later documentation commit changes `HEAD` and, after push, `origin/main`. A documentation-only design commit is expected to change `HEAD`, `origin/main` after push, `repository_state.head`, `repository_state.origin_main`, `expected_head`, `expected_origin_main`, and the tracked design-document identity inventory. It is not expected to change the nine static runtime identities, the six authorized source blob OIDs, or the six authorized source byte SHA-256 identities if no relevant source file changes. Nevertheless, all identities must be recomputed at `ACCEPTED_SUCCESSOR_DESIGN_HEAD` before any canonical input preparation.

## 5. Final static identity inventory

The nine static identities were recomputed from the accepted repository baseline:

```text
retained_schema_sha256:
81a6a21e06b397b1accd228fb37308945ebc926cb409f816789a22df39e94b3c

case_set_sha256:
b24057bb7ec233414d670a3e1e2aabb90f8a2728ff590b0ed4e811faf8e5f1b1

retained_orchestration_policy_sha256:
3d9b66a180fabf00c8bb6695c74fc9d69d21cd3ac9335cc5d2dc3a1169417531

native_helper_policy_sha256:
8104bfe29a677cea4107f0b4eea8382b7b0096968af57891090cdbec6184eded

fixture_profile_sha256:
3c2f65092fc6efcf58726390e4b4b9ff9ba00a73dbad68eb5b612d49a788a5a1

authority_registry_profile_sha256:
aa3368028954f86d294fce0dbcf61117be5750dd87202971ae4a2a8d456c2734

evidence_chain_sha256:
185e4dea85abf436ac93a01632f0b1ab4895086177e2de073608a0c08b2d174b

operator_wrapper_sha256:
624db34f9fcf076429751eba8f1aeff3a6a3be6e1917488173cee9e8349f86db

retained_mode_identity:
611e626ca0ce858be4a9b8bf594ea7606dcea4048ceba156764f5b32529f1399
```

Determination:

```text
STATIC_IDENTITIES_RECOMPUTED: YES
STATIC_IDENTITY_STABILITY_CLASSIFICATION: STABLE_AT_ACCEPTED_ASSESSMENT_BASELINE_HEAD
```

## 6. Authorized source-surface identity inventory

The six authorized implementation-surface identities were recomputed from accepted HEAD and checked-out bytes:

| Path | Git blob OID | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| `research/brainvision/blocker2_retained_absolute_path_control_v0_1.py` | `1779715ed17fffe3a927d24eb445eec51f3d42d6` | 144698 | `dc4a6e3f1169c33a2379c3506d107893cb8a48c977300c22bda14db0bf19e3d5` |
| `research/brainvision/test_blocker2_retained_absolute_path_control_integration_v0_1.py` | `73994082fd0e20365b2dd548f8bedf9b9480b898` | 8097 | `062a8d2e93ce627ff81fb7feb4a727adbcfa205d1a10e64dac28cf7578653af1` |
| `research/brainvision/test_blocker2_retained_absolute_path_control_v0_1.py` | `eecc2f62dc6763c2ecc86e8de39179ead6076c73` | 50608 | `70d70e0005060b0cb6908a7e663a1f37b13f9046cb64845f89d49cf6eb9bad8d` |
| `research/brainvision/test_validate_windows_same_volume_no_replace_promotion_integration_v0_1.py` | `d479fef6010c0ab9fda34b6e9e72d699471d7d43` | 11888 | `1a876eb454aa152f245334e75d14e902998265a4657e3ef96087bad82f740623` |
| `research/brainvision/test_validate_windows_same_volume_no_replace_promotion_v0_1.py` | `471baebc50d08d38c68042486ef0eb3fb6d0d186` | 21162 | `f559355e927688ed078f9f38ae25578c7b1654ac0c539b0843a107f5fb8fbae2` |
| `research/brainvision/validate_windows_same_volume_no_replace_promotion_v0_1.py` | `cac72051ecfc4af0dd6b53c0415248f9e6f7ea51` | 134881 | `1a1acfaf6706e340acb3d326172d392069612c6a81d504d163f27e142d9242cc` |

Determination:

```text
AUTHORIZED_SOURCE_IDENTITIES_RECOMPUTED: YES
AUTHORIZED_SOURCE_IDENTITY_STABILITY_CLASSIFICATION: STABLE_AT_ACCEPTED_ASSESSMENT_BASELINE_HEAD
```

## 7. Broad-root reuse determination

Repository-established broad roots may be reused as namespaces if they are or become admissible ordinary Windows directories outside the repository:

```text
authority root:
C:\TORMENT\brainvision_authority\blocker2_s3b_v0_3

retained-results root:
C:\TORMENT\brainvision_retained_results\blocker2_s3b_v0_3

fixture root:
C:\TORMENT\brainvision_authoritative_fixture\blocker2_s3b_v0_3
```

The wrapper's fixed-root and path-evidence checks require drive-qualified DOS paths, local fixed NTFS volume evidence, outside-repository containment, ordinary directory status, and non-reparse status.

These classes remain governance-only in repository evidence:

```text
active-authorization root: INSUFFICIENT_EVIDENCE_IN_REPOSITORY_CODE
external-assessments root: INSUFFICIENT_EVIDENCE_IN_REPOSITORY_CODE
```

They may be treated only as externally governed broad namespaces. The repository code does not define a reusable root policy for them.

## 8. Fresh child-identity requirements

The broad roots may be reused if admissible. Identity-bound children must be fresh and absent for the successor lane:

```text
global_authority_entry_path:
C:\TORMENT\brainvision_authority\blocker2_s3b_v0_3\<fresh_execution_authorization_identity>.global_authority_entry.canonical.json

result_directory:
C:\TORMENT\brainvision_retained_results\blocker2_s3b_v0_3\<fresh_execution_authorization_identity>

local_gate_path:
<result_directory>\gate_entry.canonical.json

run_result_path:
<result_directory>\run_result.canonical.json

retained_completion_path:
<result_directory>\retained_completion.canonical.json
```

Fresh repository-bound children are also required for any active authorization document, external assessment artifact, canonical `PREPARE_PATHS` input, canonical `PREFLIGHT_ONLY` input, and canonical `EXECUTE_EXACT_SINGLE_RUN` input.

Historical children prohibited from operational reuse include the consumed global authority entry, local gate, run result, historical result directory, any historical retained-completion path, historical canonical inputs, historical active authorization documents, and any child path derived from the consumed historical identity.

## 9. PREPARE_PATHS input contract

`PREPARE_PATHS` uses the same canonical operator-wrapper authorization input schema as the later modes:

```text
schema:
torment.brainvision.blocker2.operator_wrapper.authorization_input.v0.2

wrapper_mode:
PREPARE_PATHS
```

The exact top-level fields required by repository code are:

```text
schema
authorization_status
wrapper_mode
operator_identity
single_process_declaration
single_attempt_declaration
real_executor_selector
retained_mode
authoritative
repository_identity
source_identity_inventory
document_identity_inventory
runtime_declaration_identities
path_model
execution_authorization_identity_block
retained_authorization
repository_state
source_observations
case_set
a6_selected
authorization_input_identity
execution_authorization_document_identity
fault_injection_disabled
```

Required values before a `PREPARE_PATHS` input can be frozen:

```text
schema exactly matches wrapper schema
authorization_status is real and non-placeholder
wrapper_mode is PREPARE_PATHS
operator_identity is Hilmir
single_process_declaration is one Windows Command Prompt process
single_attempt_declaration is one authoritative attempt
real_executor_selector matches repository locked selector
retained_mode is BLOCKER2_ABSOLUTE_PATH_CONTROL_RETAINED_SINGLE_RUN_V0_1
authoritative is true
repository_identity.branch is main
repository_identity.head is ACCEPTED_SUCCESSOR_DESIGN_HEAD
repository_identity.origin_main is ACCEPTED_SUCCESSOR_DESIGN_HEAD
repository_state is collected from the same clean repository state
repository_state.head is ACCEPTED_SUCCESSOR_DESIGN_HEAD
repository_state.origin_main is ACCEPTED_SUCCESSOR_DESIGN_HEAD
retained_authorization.expected_head is ACCEPTED_SUCCESSOR_DESIGN_HEAD
retained_authorization.expected_origin_main is ACCEPTED_SUCCESSOR_DESIGN_HEAD
execution_authorization_identity_block expected HEAD/origin fields match
HEAD == origin/main == ACCEPTED_SUCCESSOR_DESIGN_HEAD
all nine runtime_declaration_identities match Section 5
case_set selects and executes A1/A2/A3/A5, with A6 false
source_identity_inventory and source_observations match Section 6 and current disk/Git state
document_identity_inventory matches current disk/Git state for controlling documents
execution_authorization_document_identity points to a real tracked document identity
path_model equals derived_path_model(execution_authorization_identity)
authorization_input_identity is derived from the canonical authorization payload excluding the authorization_input_identity field itself
fault_injection_disabled is true
```

`ACCEPTED_SUCCESSOR_DESIGN_HEAD` becomes known only after independent design acceptance, Hilmir commit, push to `origin/main`, and clean synchronized baseline verification. No `PREPARE_PATHS` canonical input may be prepared or frozen before that sequence completes.

Repository code requires `authorization_status: ACTIVE` only for `PREFLIGHT_ONLY` and `EXECUTE_EXACT_SINGLE_RUN`. For `PREPARE_PATHS`, the field must exist and must not be placeholder text. External governance may still require an explicitly non-invocable preparation status for any document that is not yet authorized for later modes.

Values that may remain symbolic in this design document, but not in the canonical `PREPARE_PATHS` input, are:

```text
fresh execution authorization identity
fresh authorization-input identity
fresh run identity
fresh result-directory identity
fresh path-preparation result identity
fresh active authorization document identity
fresh canonical input file identity
```

The canonical input itself must contain concrete, canonical JSON values and cannot contain placeholder, synthetic, or unavailable-until-commit values. The `authorization_input_identity` derivation is non-circular: repository code builds the canonical authorization declaration from the payload with the `authorization_input_identity` field excluded, hashes that declaration payload, then compares the supplied identity fields to the computed result.

## 10. PREPARE_PATHS creation and prohibition boundaries

`PREPARE_PATHS` may create only the fixed broad roots if absent:

```text
C:\TORMENT\brainvision_authority\blocker2_s3b_v0_3
C:\TORMENT\brainvision_authoritative_fixture\blocker2_s3b_v0_3
C:\TORMENT\brainvision_retained_results\blocker2_s3b_v0_3
```

It may return a non-authoritative `PREPARATION_COMPLETE` result record containing path evidence. That record is output, not consumed authority.

`PREPARE_PATHS` must not create:

```text
result_directory
global_authority_entry_path
local_gate_path
run_result_path
retained_completion_path
native retained-run evidence
canonical PREFLIGHT input
canonical EXECUTION input
governance acceptance artifacts
active authorization documents
```

Repository fail-closed conditions include:

```text
non-canonical JSON input
duplicate JSON keys
missing or unknown top-level fields
placeholder or synthetic text
wrong schema
wrong wrapper mode
wrong operator identity
wrong single-process declaration
wrong single-attempt declaration
wrong real executor selector
authoritative flag not true
fault injection enabled
A6 selected
wrong case set or order
runtime identity mismatch
source identity mismatch
document identity mismatch
execution authorization document identity mismatch
path model mismatch
repository branch mismatch
repository HEAD mismatch
repository origin/main mismatch
HEAD differs from origin/main
.git/index.lock present
dirty authorized surfaces
dirty unrelated surfaces when allow_unrelated_outside_surfaces is false
fixed root inside repository
fixed root exists as non-directory
fixed root path not drive-qualified
fixed root not local fixed NTFS during path evidence
fixed root is reparse
result directory already exists
global authority entry already exists
```

Repository code does not encode one-attempt governance specifically for `PREPARE_PATHS` in the same way external governance does for later PREFLIGHT and execution. The input schema still requires `single_attempt_declaration: one authoritative attempt`, and external governance may impose single-use handling on the preparation authorization. A failed `PREPARE_PATHS` does not consume authority by repository code, but an identity, path, repository-state, result-directory, or global-authority-entry collision can retire that candidate identity under governance because the same identity cannot safely be reused without reassessment.

## 11. Governance requirements

Before any canonical preparation:

```text
independent review accepts this design
Hilmir commits and pushes accepted design v0.2
the repository binding is refreshed to ACCEPTED_SUCCESSOR_DESIGN_HEAD
HEAD equals origin/main equals ACCEPTED_SUCCESSOR_DESIGN_HEAD
working tree is fully clean
.git/index.lock is absent
corrective commit 3e516bd3714b75b0a7c6b760e44fd02439837700 remains in ancestry
accepted assessment baseline 94cf0b9a4d4f1e83b00178ccca3363f4e6eed73f remains in ancestry
all static identities are rechecked at the binding commit
all source and document identities are generated from the binding commit and checked-out bytes
no successor canonical input already exists for the candidate identity
no successor result directory/global authority entry exists for the candidate identity
```

Repository code defines the wrapper payload schema and repository validation. It does not define the full external governance schema for design acceptance, active-authorization root policy, external-assessment root policy, or Hilmir/GPT review artifacts. Those remain external governance requirements.

Hilmir must accept this design and commit/push it before any canonical `PREPARE_PATHS` preparation. The next exact state transition after independent design acceptance is:

```text
SUCCESSOR_DESIGN_v0_2_COMPLETE -> INDEPENDENT_DESIGN_REVIEW_ACCEPTED -> SUCCESSOR_DESIGN_COMMITTED_AND_PUSHED -> FINAL_DESIGN_BASELINE_RECONFIRMED
```

The design commit-and-push path is mandatory, not conditional:

```text
SUCCESSOR_DESIGN_COMMITTED_AND_PUSHED -> FINAL_DESIGN_BASELINE_RECONFIRMED -> SUCCESSOR_DESIGN_ACCEPTED -> PREPARE_PATHS_INPUT_PREPARATION_AUTHORIZED
```

Controlling document and governance identities required by the execution-authorization identity declaration:

| Identity | Classification | Direct input to execution_authorization_identity | Design-only availability |
| --- | --- | --- | --- |
| `retained_run_assessment_identity` | Repository constant / historical precedent for existing retained assessment identity; future design may need fresh tracked-document rebinding if governance requires it | Yes | Existing repository constant available; successor governance-specific value not newly created here |
| `implementation_preparation_authorization_identity` | Repository constant / historical precedent only for prior implementation preparation authorization | Yes | Existing repository constant available; no fresh successor governance artifact created |
| `runtime_correction_authorization_identity` | Repository constant / historical corrective authorization precedent | Yes | Existing repository constant available; no fresh successor governance artifact created |
| `identity_derivation_cycle_correction_authorization_identity` | Repository constant for prior identity-derivation correction authorization | Yes | Existing repository constant available |
| `execution_authorization_document_identity` | Fresh tracked document identity required by wrapper payload; must remain absent until later governance creates and commits a real active authorization document | No, but it is a required top-level wrapper payload identity validated before mode execution | Unavailable during this design-only phase |

No missing controlling identity is fabricated here. Fresh governance artifact identities, tracked authorization document identity, and canonical input identities remain unavailable until later governance.

## 12. Identity derivation order

Fresh identities required before canonical `PREPARE_PATHS` invocation:

| Identity | Fresh before PREPARE input freeze | Derivable before path creation | Requires authoritative Windows host or volume | Known only after PREPARE output | Must remain absent until later governance |
| --- | --- | --- | --- | --- | --- |
| Authorization-input identity | Yes | Yes, from canonical authorization payload excluding `authorization_input_identity` | No | No | No |
| Execution-authorization identity | Yes | Yes, after source/doc/root/host/volume inputs exist | Yes | No | No |
| Run identity | Yes for the retained identity block | Yes, after execution auth and derived result directory identity | Yes | No | Not authorized for execution |
| Result-directory identity | Yes as absent-child path identity | Yes, from derived path | Indirectly via result parent volume | No | Result directory itself must remain absent |
| Host identity | Yes | No | Yes | No | No |
| Volume identity | Yes | No | Yes | No | No |
| Path-manifest or path-preparation result identity | No | No | Yes | Yes | No |
| Fixture identity | Static fixture profile yes; fixture root path identity must be fresh/verified | Fixture root path identity can be computed before creation only as absent path identity | Volume evidence requires host | Path evidence after PREPARE | Fixture contents must remain later-run controlled |
| Case-set identity | No new identity required | Yes | No | No | No |

The execution authorization identity and run identity are machine-bound through `host_identity` and `volume_identity`. They are not portable across hosts or target volumes. If the authoritative Windows host, drive root, broad roots, source identities, document identities, accepted HEAD, or governance documents change, the identity chain must be regenerated.

## 13. Successor-lane state transition

Current state after this document is produced:

```text
CLEAN_SYNCHRONIZED_ASSESSMENT_BASELINE
-> SUCCESSOR_DESIGN_v0_2_COMPLETE
```

Mandatory state sequence:

```text
CLEAN_SYNCHRONIZED_ASSESSMENT_BASELINE
-> SUCCESSOR_DESIGN_v0_2_COMPLETE
-> INDEPENDENT_DESIGN_REVIEW_ACCEPTED
-> SUCCESSOR_DESIGN_COMMITTED_AND_PUSHED
-> FINAL_DESIGN_BASELINE_RECONFIRMED
-> SUCCESSOR_DESIGN_ACCEPTED
-> PREPARE_PATHS_INPUT_PREPARATION_AUTHORIZED
-> PREPARE_PATHS_INPUT_PREPARED
-> PREPARE_PATHS_INPUT_INDEPENDENTLY_REVIEWED
-> PREPARE_PATHS_GOVERNANCE_ACCEPTED
-> PREPARE_PATHS_AUTHORIZED_FOR_INVOCATION
-> PREPARE_PATHS_INVOKED
-> PATHS_PREPARED
```

This design task stops before `PREPARE_PATHS_INPUT_PREPARED`. Later states are described for governance ordering only; this document does not create or authorize them.

| Transition | Allowed actor | Required inputs | Required identities | Created artifacts | Authority consumed | Runner mode | Failure disposition | Retry or identity-retirement rule |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `CLEAN_SYNCHRONIZED_ASSESSMENT_BASELINE -> SUCCESSOR_DESIGN_v0_2_COMPLETE` | Documentation agent | Clean assessment baseline, correction order D1/N2/N3, repository inspection | `ACCEPTED_ASSESSMENT_BASELINE_HEAD`, `CORRECTIVE_IMPLEMENTATION_COMMIT`, recomputed static/source identities | This untracked v0.2 design candidate only | None | None | Stop if baseline mismatch, dirty extra path, or index lock appears | Retry only after baseline restored |
| `SUCCESSOR_DESIGN_v0_2_COMPLETE -> INDEPENDENT_DESIGN_REVIEW_ACCEPTED` | Independent reviewer / Hilmir governance | v0.2 design candidate | v0.2 document byte identity, assessment baseline, corrective ancestry | Review acceptance record, external to repository unless later committed | None | None | Reject design if binding model or inventories are wrong | Revise design to new candidate identity |
| `INDEPENDENT_DESIGN_REVIEW_ACCEPTED -> SUCCESSOR_DESIGN_COMMITTED_AND_PUSHED` | Hilmir only | Accepted v0.2 design candidate | Accepted v0.2 document identity | Git commit containing accepted design v0.2, pushed to origin/main | None | None | If commit/push fails, no canonical preparation | Resolve Git issue; no runner mode |
| `SUCCESSOR_DESIGN_COMMITTED_AND_PUSHED -> FINAL_DESIGN_BASELINE_RECONFIRMED` | Hilmir/GPT governance | Pushed design commit | `ACCEPTED_SUCCESSOR_DESIGN_HEAD`, `3e516bd...` ancestry, `94cf0b9...` ancestry | Clean synchronized baseline confirmation | None | None | Stop if HEAD/origin mismatch, dirty tree, index lock, missing ancestry, or identity mismatch | Restore clean synchronized baseline or revise design if identities changed |
| `FINAL_DESIGN_BASELINE_RECONFIRMED -> SUCCESSOR_DESIGN_ACCEPTED` | Hilmir/GPT governance | Clean final design baseline | Nine static identities recomputed, six source blob/byte identities recomputed, tracked design-document identity recorded | Successor design acceptance artifact | None | None | Stop if any required identity is stale or missing | Recompute/review; new governance if binding changes |
| `SUCCESSOR_DESIGN_ACCEPTED -> PREPARE_PATHS_INPUT_PREPARATION_AUTHORIZED` | Hilmir/GPT governance | Accepted design and final baseline confirmation | `ACCEPTED_SUCCESSOR_DESIGN_HEAD`, controlling document/governance identity decisions | Authorization to prepare one `PREPARE_PATHS` input | None | None | Stop if governance rejects or unresolved identity remains blocking | Fresh governance after correction |
| `PREPARE_PATHS_INPUT_PREPARATION_AUTHORIZED -> PREPARE_PATHS_INPUT_PREPARED` | Hilmir/operator under governance | Preparation authorization, final identity inventory, host/volume selection | Fresh execution authorization identity, path model, authorization-input identity | Draft canonical `PREPARE_PATHS` input | None | None | Stop if placeholders, stale binding, missing doc identity, or path collision appears | Candidate identity may retire if collision/stale binding cannot be repaired |
| `PREPARE_PATHS_INPUT_PREPARED -> PREPARE_PATHS_INPUT_INDEPENDENTLY_REVIEWED` | Independent reviewer | Draft canonical input | Input SHA, source/document identities, repository binding | Review record | None | None | Reject stale or non-canonical input | Prepare fresh input after correction |
| `PREPARE_PATHS_INPUT_INDEPENDENTLY_REVIEWED -> PREPARE_PATHS_GOVERNANCE_ACCEPTED` | Hilmir/GPT governance | Reviewed input | Input identity and `ACCEPTED_SUCCESSOR_DESIGN_HEAD` | Governance acceptance for PREPARE only | None | None | Reject if governance missing | Fresh governance required |
| `PREPARE_PATHS_GOVERNANCE_ACCEPTED -> PREPARE_PATHS_AUTHORIZED_FOR_INVOCATION` | Hilmir/GPT governance | Final operator checks | Clean repo, index-lock absence, absent result/global authority paths | Invocation authorization for one command | None | None | Stop on any failed immediate check | Repair and re-review; do not invoke under stale authorization |
| `PREPARE_PATHS_AUTHORIZED_FOR_INVOCATION -> PREPARE_PATHS_INVOKED` | Hilmir only | Exact command and frozen input | Frozen input SHA and binding | Command invocation event | None | `PREPARE_PATHS` | If invocation fails before creating broad roots, classify result and stop | Identity may retire for path/repository/input collision |
| `PREPARE_PATHS_INVOKED -> PATHS_PREPARED` | Wrapper under Hilmir invocation | Valid `PREPARE_PATHS` input | Path evidence identities, result/global authority absence | Non-authoritative preparation record and broad roots if absent | None | `PREPARE_PATHS` | `PREPARATION_COMPLETE`, `PREFLIGHT_REJECTED_UNCONSUMED`, `AUTHORITY_ALREADY_CONSUMED`, or invalid input | This state is reached only after Hilmir invokes `PREPARE_PATHS` under separately accepted governance; this design does not authorize that invocation |

`FINAL_DESIGN_BASELINE_RECONFIRMED` requires:

```text
HEAD == origin/main == ACCEPTED_SUCCESSOR_DESIGN_HEAD
working tree fully clean
.git/index.lock absent
3e516bd3714b75b0a7c6b760e44fd02439837700 present in HEAD ancestry
94cf0b9a4d4f1e83b00178ccca3363f4e6eed73f present in HEAD ancestry
all nine static identities recomputed
all six authorized source blob and byte identities recomputed
tracked design-document identity recorded
no canonical PREPARE_PATHS input yet exists
```

No transition in this task reaches `PREPARE_PATHS_INPUT_PREPARED`, `PREFLIGHT_INPUT_FROZEN`, `EXECUTION_INPUT_FROZEN`, or `SUCCESSOR_EXECUTION_AUTHORIZED`.

## 14. Preconditions for preparing a PREPARE_PATHS input

A canonical `PREPARE_PATHS` input may be prepared only after:

```text
this design is independently accepted
Hilmir accepts the design
Hilmir commits and pushes accepted design v0.2
HEAD equals origin/main equals ACCEPTED_SUCCESSOR_DESIGN_HEAD
working tree is fully clean under git status --short --untracked-files=all
.git/index.lock is absent
corrective commit 3e516bd3714b75b0a7c6b760e44fd02439837700 remains in ancestry
accepted assessment baseline 94cf0b9a4d4f1e83b00178ccca3363f4e6eed73f remains in ancestry
static identities are recomputed at the binding commit
authorized source identities are recomputed at the binding commit
document identities are generated from tracked, committed documents at the binding commit
all broad roots intended for identity derivation have admissible governance status
the authoritative Windows host and target volume are selected
ACCEPTED_SUCCESSOR_DESIGN_HEAD is bound into expected_head and expected_origin_main
no canonical successor PREPARE input has already been frozen for the candidate identity
no existing result directory or global authority entry exists for the candidate identity
```

The next input that may safely be prepared after these prerequisites is a canonical `PREPARE_PATHS` input only. `PREFLIGHT_ONLY` and `EXECUTE_EXACT_SINGLE_RUN` inputs remain prohibited.

## 15. Preconditions for invoking PREPARE_PATHS

`PREPARE_PATHS` may be invoked only after the canonical `PREPARE_PATHS` input is frozen and immediately rechecked:

```text
wrapper_mode is PREPARE_PATHS
authorization input bytes are canonical JSON
authorization_input_identity matches canonical bytes
authorization_input_identity was derived excluding the authorization_input_identity field itself
repository binding equals current HEAD and origin/main, with HEAD == origin/main == ACCEPTED_SUCCESSOR_DESIGN_HEAD
working tree is fully clean
.git/index.lock is absent
source identity inventory matches current Git blobs and disk bytes
document identity inventory matches current Git blobs and disk bytes
runtime declaration identities match Section 5 at the binding commit
case lock is A1/A2/A3/A5, A6 false
path model derives from the fresh execution authorization identity
result directory is absent
global authority entry is absent
command is run by Hilmir in one Windows Command Prompt process under conda environment torment
```

`PREPARE_PATHS_READY_TO_INVOKE` remains `NO` in this task because no canonical input exists, this design is not independently accepted, the mandatory design commit/push has not happened, `ACCEPTED_SUCCESSOR_DESIGN_HEAD` is not yet created, and this new untracked document makes the working tree dirty.

## 16. Prohibited later-stage artifacts

This design does not authorize creating:

```text
canonical PREFLIGHT input
canonical EXECUTION input
PREFLIGHT result
execution result
global authority entry
local gate
run result
retained completion
result directory
active authorization document
external governance acceptance artifact
native execution evidence
```

The shared input structure can support `PREPARE_PATHS`, `PREFLIGHT_ONLY`, and `EXECUTE_EXACT_SINGLE_RUN`, but mode-specific restrictions apply:

```text
PREPARE_PATHS:
  wrapper_mode must be PREPARE_PATHS.
  repository code does not require ACTIVE status for invocation, but all fields must be real and non-placeholder.
  terminal result is non-authoritative and authority_consumed is false.

PREFLIGHT_ONLY:
  wrapper_mode must be PREFLIGHT_ONLY.
  authorization_status and execution_authorization_document_identity.authorization_status must be ACTIVE.
  result/global authority/gate/run/retained-completion paths must be absent.
  terminal result is non-authoritative and authority_consumed is false.

EXECUTE_EXACT_SINGLE_RUN:
  wrapper_mode must be EXECUTE_EXACT_SINGLE_RUN.
  authorization_status and execution_authorization_document_identity.authorization_status must be ACTIVE.
  internal PREFLIGHT_ONLY must pass first.
  authority may be consumed and any consumed result is terminal for that identity.
```

Prepared, frozen, governance-accepted, and authorized-for-invocation are distinct states. A payload may be drafted without being frozen. A frozen payload has exact canonical bytes and identity. Governance acceptance records permission for a defined state transition. Authorized-for-invocation is the final operator permission to run a specific command against a specific frozen input.

## 17. Remaining unresolved questions

The following remain unresolved by repository code and require external governance:

```text
active-authorization broad root reuse policy
external-assessments broad root reuse policy
formal external governance schema for design acceptance
whether this design document will be committed before PREPARE_PATHS preparation
if committed, the exact new repository binding commit after push
the authoritative Windows host and target volume for identity derivation
the final fresh active authorization document path and status semantics for PREPARE_PATHS
```

None of these unresolved questions authorizes runner invocation.

## 18. Final recommended next action

Recommended next sequence:

```text
1. Independently review this design document.
2. Hilmir/GPT accepts or rejects the design.
3. If accepted, Hilmir commits and pushes design v0.2.
4. Define that pushed commit as ACCEPTED_SUCCESSOR_DESIGN_HEAD.
5. Reconfirm HEAD equals origin/main equals ACCEPTED_SUCCESSOR_DESIGN_HEAD, clean tree, index-lock absence, and corrective/assessment ancestry.
6. Recompute static, source, and tracked design/document identities at ACCEPTED_SUCCESSOR_DESIGN_HEAD.
7. Select the authoritative Windows host and target volume.
8. Authorize preparation of one canonical PREPARE_PATHS input only.
9. Prepare and then independently review the PREPARE_PATHS input.
10. Accept PREPARE_PATHS governance.
11. Perform immediate operator checks.
12. Only then show the PREPARE_PATHS command to Hilmir.
```

No PREFLIGHT or execution input should be prepared next.

## 19. Terminal disposition

```text
B. DESIGN_COMPLETE_WITH_GOVERNANCE_PREREQUISITES
```

Required terminal fields:

```text
ACCEPTED_ASSESSMENT_BASELINE_HEAD:
94cf0b9a4d4f1e83b00178ccca3363f4e6eed73f

ACCEPTED_SUCCESSOR_DESIGN_HEAD:
NOT_YET_CREATED

STATIC_IDENTITIES_RECOMPUTED:
YES

AUTHORIZED_SOURCE_IDENTITIES_RECOMPUTED:
YES

PREPARE_PATHS_INPUT_READY_TO_BE_PREPARED:
NO

LIVE_PREPARE_PATHS_BINDING_READY:
NO

PREPARE_PATHS_READY_TO_INVOKE:
NO

PREFLIGHT_INPUT_READY:
NO

EXECUTION_INPUT_READY:
NO

SUCCESSOR_EXECUTION_AUTHORIZED:
NO
```

Commands and tests:

```text
Tests run: none.
Runner modes invoked: none.
Inspection commands only: git status, git rev-parse, git log, git ls-tree, git merge-base, rg searches, targeted source reads, static Python identity imports, byte/hash calculations.
Execution-capable artifacts created: none.
```

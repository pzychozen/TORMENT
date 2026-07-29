# TORMENT Brainvision Stage S3B v0.3 BLOCKER-2 R4 PREPARE_PATHS Corrected Active-Ready Layer-B Canonical-Input Preparation Decision v0.1

## 1. Status

This document is a draft corrected active-ready Layer-B canonical-input preparation decision for the quarantined TORMENT Brainvision Stage S3B v0.3 BLOCKER-2 R4 PREPARE_PATHS lane.

It incorporates the committed path-creation governance correction and supersedes the retired R4 Layer-B preparation lane as a fresh governance route.

It is active-ready in design only. It is not active, not committed, not pushed, not post-commit identity-bound, and not self-authorizing.

It does not create external directories, create a path-creation record, publish canonical-input bytes, invoke `PREPARE_PATHS`, invoke `PREFLIGHT_ONLY`, invoke `EXECUTE_EXACT_SINGLE_RUN`, create execution authority, consume execution authority, close BLOCKER-2, or activate BLOCKER-4.

Brainvision remains:

```text
OFFLINE
QUARANTINED
SYNTHETIC-RESEARCH ONLY
FORMAL_HOLD ACTIVE
MODE 0
```

## 2. Accepted Correction Chain

The path-creation correction decision is committed, pushed, and post-commit identity-bound by its committed identity record.

Path-creation correction decision:

```text
path: docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_PREPARE_PATHS_PATH_CREATION_GOVERNANCE_CORRECTION_DECISION_v0.1.md
containing commit: 06ae816ab30de667b9af06df3d753de2183af873
Git blob OID: b76e6708f9810f8571642a6993bc2457709ad21c
index mode: 100644
Git object size: 19028
checked-out byte count: 19028
checked-out SHA-256: cf29273ed70b71266bd8231d9cbb77500b691f0bf5d2e5fdc55e4859ea674e75
CR byte count: 0
LF count: 360
maximum byte: 124
final-newline count: 1
```

Path-creation correction decision post-commit identity record:

```text
path: docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_PREPARE_PATHS_PATH_CREATION_GOVERNANCE_CORRECTION_DECISION_POST_COMMIT_IDENTITY_RECORD_v0.1.md
containing commit: 864a3c2d486ee22b0af2e9d956df544e805927ba
commit message: docs(brainvision): bind blocker 2 R4 path creation correction identity
Git blob OID: a063c483c89c7a4387859f29aa00d1209ed881b0
index mode: 100644
Git object size: 5714
checked-out byte count: 5714
checked-out SHA-256: dfcac9fa32a423add02e0ef465fa94e819a2b4cdaf48b99e38e5d01b6eac325c
CR byte count: 0
LF count: 290
maximum byte: 124
tab count: 4
final-newline count: 1
commit inventory: EXACTLY_ONE_ADDED_FILE
commit file status: A
```

The correction decision identity record is committed and pushed, but this document does not claim that identity record's own post-commit identity is bound yet.

Governing Layer-A authorization document:

```text
path: docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_PREPARE_PATHS_CANONICAL_INPUT_PREPARATION_AUTHORIZATION_v0.1.md
Git blob OID: 1bbb7b0448b1c7b587c53c2c5105a36134da49f3
checked-out byte count: 27028
checked-out SHA-256: e49e978126520ea0224407b7052c291f9710e0d156133fb2bcaa700086f244c6
canonical authorization declaration identity: a19908c3ab6b447383dabcbc98cf7c0c6ce232f9414e857231003b9988b509d9
authorization status: PREPARED_NOT_ACTIVE
```

This governing Layer-A authorization identity is content-addressed and remains unaffected by retirement of the earlier lane.

Governing Layer-B governance design:

```text
path: docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_PREPARE_PATHS_LAYER_B_CANONICAL_INPUT_PREPARATION_GOVERNANCE_DECISION_DRAFT_v0.1.md
Git blob OID: 9bbc524c030054ce2cb754e8a0cd776446a4332e
checked-out SHA-256: 6247cd5fd541b3ace60514348aa71bd019469131d05a0b52c4e2d359da4a139d
```

## 3. Retired-Lane Supersession

The earlier R4 preparation lane is historical and non-reusable.

Retired lane bindings:

```text
retired accepted invocation HEAD: 4b0754825d7f0443a4ee696945995bcf6c63230b
retired commit-free window: CLOSED
retired Layer-B preparation authority: RETIRED UNCONSUMED
selected-path contact: NONE
canonical-input publication: NONE
PREPARE_PATHS: NOT INVOKED
one-shot PREPARE_PATHS attempt: UNCONSUMED
execution authority: NOT CREATED NOT CONSUMED
```

Prior in-memory candidate bytes and identities are:

```text
NON-AUTHORITATIVE
MUST NOT BE REUSED
MUST BE REGENERATED
```

This corrected decision does not edit, reactivate, or reuse the retired lane. It requires a fresh accepted invocation HEAD and regenerated canonical-input bytes and identities.

## 4. Corrected Operational Sequence

The corrected future operational sequence has distinct stages and must not merge them into a single act:

```text
1. Fresh governance chain completion
2. Fresh accepted invocation HEAD establishment
3. Corrected commit-free window opening
4. Directory-creation authority activation
5. Three ordered one-component directory creations
6. External path-creation evidence record creation/publication and validation
7. Canonical-input preparation authority activation
8. In-memory canonical-input construction
9. Direct canonical-input publication
10. External validation
11. PREPARE_PATHS invocation under separate Layer-C authority
```

This document only prepares an active-ready Layer-B decision candidate. It grants no current authority for any listed stage.

## 5. Corrected Path Hierarchy

Required existing root:

```text
C:\TORMENT
```

Authorized future one-component creations, in exact order:

```text
1. C:\TORMENT\brainvision_authoritative_inputs
2. C:\TORMENT\brainvision_authoritative_inputs\blocker2_s3b_v0_3
3. C:\TORMENT\brainvision_authoritative_inputs\blocker2_s3b_v0_3\r4_prepare_paths
```

Governed canonical input:

```text
C:\TORMENT\brainvision_authoritative_inputs\blocker2_s3b_v0_3\r4_prepare_paths\r4_prepare_paths_authorization_input_v0_1.canonical.json
```

`C:\TORMENT` is an ancestor of the authoritative repository path, but it is outside the repository under the controlling containment test. The first authorized creation produces a sibling namespace beside `TORMENT_repo`; it does not create content inside the repository.

## 6. Ordered Directory-Creation Authority

This decision defines a distinct future authority:

```text
CORRECTED R4 ORDERED DIRECTORY-CREATION AUTHORITY
```

The authority is:

```text
NOT ACTIVE at document creation
activated only through a later explicit non-commit governance act
single-use
separate from canonical-input preparation authority
separate from PREPARE_PATHS invocation authority
```

Each directory creation must be exactly one path component. The immediate parent must already exist. The selected child must be absent. Create-new semantics are required.

The following are prohibited:

```text
recursive creation
parents=True
mkdir -p semantics
OS-created unspecified intermediates
legalizing effects by command text alone
```

Actual filesystem effects govern legality, not command text.

Before each creation, verify the immediate parent:

```text
exists
absolute drive-qualified DOS path
local fixed drive
NTFS
outside repository
not UNC
not device path
not volume-GUID path
not reparse point
```

Before each creation, verify the selected child:

```text
absent
intended path is absolute drive-qualified DOS
outside repository
not UNC
not device path
not volume-GUID path
```

The selected child is absent before creation, so filesystem, NTFS, local-fixed-drive, and reparse-point properties must not be asserted for the child until after it exists.

Before each creation, verify the environment:

```text
repository clean
HEAD == origin/main == fresh accepted invocation HEAD
.git/index.lock absent
canonical-input file absent
all earlier ordered-creation evidence valid
```

After each creation, verify the created directory itself:

```text
exists
exactly the selected path for that step
absolute drive-qualified DOS path
local fixed drive
NTFS
outside repository
not UNC
not device path
not volume-GUID path
not reparse point
no unintended sibling, child, or ancestor was created
repository clean
HEAD == origin/main == fresh accepted invocation HEAD
.git/index.lock absent
canonical-input file absent
all earlier ordered-creation evidence valid
```

Successful completion of all three ordered creations consumes only the directory-creation opportunity. It does not consume canonical-input publication authority, the PREPARE_PATHS one-shot attempt, or execution authority.

## 7. Directory Failure Semantics

Directory-creation failure semantics are:

```text
pre-contact failure before any directory creation: no directory authority consumed
unexpected pre-existing selected child: fail closed
one component created but later component fails: opportunity retired
post-creation validation failure: opportunity retired
reparse discovery: opportunity retired
repository drift: opportunity retired
HEAD/origin drift: opportunity retired
index-lock discovery: opportunity retired
operator interruption before first creation: no authority consumed
operator interruption after any creation: opportunity retired
cleanup: not authorised
deletion: not authorised
rename: not authorised
move: not authorised
reuse: not authorised
continuation: not authorised
retry: not authorised without fresh committed governance
```

Any partial hierarchy must remain preserved as historical evidence until separate governance addresses it.

## 8. External Path-Creation Record

After the third directory is successfully created and validated, a separate external evidence object is required before canonical-input publication may proceed.

The external path-creation record must bind, for each creation:

```text
exact path
creation-order index
immediate-parent path or identity
create-before absence evidence
create-after existence evidence
creation timestamp
local-fixed-drive status
NTFS status
reparse status
volume profile or identity
directory filesystem identity/file ID where available
operator environment declaration
branch
HEAD
origin/main
index-lock state
```

The evidence must distinguish three ordered one-component creations from one recursive hierarchy creation.

The record remains separate from the wrapper-consumed canonical input. It must not be added to the wrapper authorization input unless a separately committed runtime/schema change authorizes that field.

The future corrected Layer-C authorization must define fail-closed semantics for:

```text
path-creation-record construction failure
path-creation-record publication failure
incomplete record
record identity mismatch
record absence after directory creation
```

Canonical-input publication must not proceed without a complete validated external path-creation record.

## 9. Canonical-Input Preparation Authority

This decision defines a distinct future authority:

```text
CORRECTED R4 LAYER-B CANONICAL-INPUT PREPARATION AUTHORITY
```

It remains inactive until:

```text
fresh accepted invocation HEAD established
corrected commit-free window open
three directory acts completed successfully
external path-creation record complete and validated
repository still frozen
canonical-input file absent
```

Activation must be a distinct non-commit governance act.

The authority authorizes exactly one later direct canonical-input publication at the governed path. It is separate from ordered directory-creation authority and separate from PREPARE_PATHS invocation authority.

## 10. Canonical-Input Construction And Publication

The future canonical-input construction and publication model remains:

```text
construct full bytes in memory first
validate before path contact
no external temporary candidate
no rename workflow
no copy workflow
no atomic replacement
no overwrite
no append
create-new semantics
first selected-file byte begins publication
partial publication fails closed
cleanup prohibited
published bytes must remain PREPARED_NOT_ACTIVE
```

All prior in-memory candidate bytes and identities must be regenerated after the future fresh accepted invocation HEAD is established.

## 11. Required Canonical-Input Bindings

The future canonical input must bind the current authoritative runtime, schema, and governance requirements, including where required:

```text
wrapper schema: torment.brainvision.blocker2.operator_wrapper.authorization_input.v0.2
nested retained schema: torment.brainvision.blocker2.retained.authorization_input.v0.1
authorization_status: PREPARED_NOT_ACTIVE
wrapper_mode: PREPARE_PATHS
operator: Hilmir
expected_branch: main
expected_head: future fresh accepted invocation HEAD
expected_origin_main: future fresh accepted invocation HEAD
selected cases: A1 A2 A3 A5
a6_selected: false
fault injection: disabled
selector: REAL_EXISTING_ABSOLUTE_PATH_A1_A2_A3_A5_V0_1
```

It must also bind exact runtime, schema, source, policy, governance-document, identity-record, case-set, freshness, non-reuse, and execution-authorization-document identities consumed by the implementation.

The execution-authorization-document identity that the future canonical input must carry is the exact five-field Layer-A identity bound in Section 2.

The execution-authorization identity derivation, declaration-envelope rule, mandatory top-level field set, and nested identity shapes remain those bound by the governing Layer-B governance design identified in Section 2 and incorporated by that exact committed identity.

Nothing in this corrected decision narrows or substitutes those requirements.

This draft does not embed a future accepted HEAD value because the future accepted invocation HEAD is not currently available.

## 12. Corrected Commit-Free Window

The future corrected Layer-C authorization must explicitly supersede the retired single-mutation rule. Supersession must be explicit, not implied.

The corrected commit-free window must permit only these exact external mutations:

```text
1. creation of C:\TORMENT\brainvision_authoritative_inputs
2. creation of C:\TORMENT\brainvision_authoritative_inputs\blocker2_s3b_v0_3
3. creation of C:\TORMENT\brainvision_authoritative_inputs\blocker2_s3b_v0_3\r4_prepare_paths
4. creation or publication of the external path-creation record
5. publication of exactly one canonical input at the governed path
```

No other external filesystem mutation is authorised.

No repository file, index entry, branch, ref, tag, Git metadata state, or commit may change during the corrected window.

## 13. Fresh Governance Prerequisites

This corrected Layer-B decision remains inactive until the full fresh chain exists:

```text
1. Path-creation correction decision committed and pushed
2. Correction decision identity record committed and pushed
3. Corrected Layer-B decision committed and pushed
4. Corrected Layer-B post-commit identity record committed and pushed
5. Corrected Layer-C authorisation committed and pushed
6. Corrected Layer-C post-commit identity record committed and pushed
7. Fresh accepted invocation HEAD explicitly established
8. Corrected commit-free window opened
```

Current completion state:

```text
steps 1 and 2: COMPLETE
steps 3 through 8: FUTURE
```

## 14. Non-Authorisation Ruling

Creating, reviewing, accepting, or later committing this decision must not:

```text
activate directory-creation authority
activate canonical-input preparation authority
establish a fresh accepted invocation HEAD
open a fresh commit-free window
create external directories
create the path-creation record
publish canonical-input bytes
invoke PREPARE_PATHS
invoke PREFLIGHT_ONLY
invoke EXECUTE_EXACT_SINGLE_RUN
create or consume execution authority
close BLOCKER-2
activate BLOCKER-4
```

## 15. Canonical Embedded Declaration

This section carries the single canonical embedded declaration for this corrected active-ready Layer-B canonical-input preparation decision draft.

Extraction excludes the final LF immediately preceding the closing declaration fence under LF checkout and excludes the complete CRLF pair immediately preceding the closing declaration fence under CRLF checkout.

```CORRECTED_ACTIVE_READY_LAYER_B_DECISION_CANONICAL_JSON
{"accepted_invocation_head_predeclared":false,"accepted_invocation_head_value_available":false,"actual_filesystem_effects_control_legality":true,"append_authorized":false,"atomic_replace_authorized":false,"blocker_2":"OPEN","blocker_2_closure_authorized":false,"blocker_4":"INACTIVE","blocker_4_activation_authorized":false,"canonical_input_preparation_authority_active":false,"canonical_input_publication_authorized":false,"canonical_input_status_after_publication":"PREPARED_NOT_ACTIVE","cleanup_authorized":false,"construct_in_memory_before_path_contact":true,"copy_authorized":false,"corrected_commit_free_window":{"no_other_external_filesystem_mutation_authorized":true,"permitted_external_mutations":["create C:\\TORMENT\\brainvision_authoritative_inputs","create C:\\TORMENT\\brainvision_authoritative_inputs\\blocker2_s3b_v0_3","create C:\\TORMENT\\brainvision_authoritative_inputs\\blocker2_s3b_v0_3\\r4_prepare_paths","create or publish the external path-creation record","publish exactly one canonical input at C:\\TORMENT\\brainvision_authoritative_inputs\\blocker2_s3b_v0_3\\r4_prepare_paths\\r4_prepare_paths_authorization_input_v0_1.canonical.json"],"repository_mutation_during_window_authorized":false},"corrected_layer_b_decision_status":"DRAFT_NOT_COMMITTED_NOT_PUSHED_NOT_IDENTITY_BOUND_NOT_ACTIVE","correction_chain_identities":{"governing_layer_a_authorization":{"authorization_status":"PREPARED_NOT_ACTIVE","canonical_authorization_declaration_identity":"a19908c3ab6b447383dabcbc98cf7c0c6ce232f9414e857231003b9988b509d9","checked_out_byte_count":27028,"checked_out_sha256":"e49e978126520ea0224407b7052c291f9710e0d156133fb2bcaa700086f244c6","git_blob_oid":"1bbb7b0448b1c7b587c53c2c5105a36134da49f3","observed_at_head":"864a3c2d486ee22b0af2e9d956df544e805927ba","path":"docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_PREPARE_PATHS_CANONICAL_INPUT_PREPARATION_AUTHORIZATION_v0.1.md"},"governing_layer_b_governance_design":{"checked_out_sha256":"6247cd5fd541b3ace60514348aa71bd019469131d05a0b52c4e2d359da4a139d","git_blob_oid":"9bbc524c030054ce2cb754e8a0cd776446a4332e","observed_at_head":"864a3c2d486ee22b0af2e9d956df544e805927ba","path":"docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_PREPARE_PATHS_LAYER_B_CANONICAL_INPUT_PREPARATION_GOVERNANCE_DECISION_DRAFT_v0.1.md"},"path_creation_correction_decision":{"checked_out_byte_count":19028,"checked_out_sha256":"cf29273ed70b71266bd8231d9cbb77500b691f0bf5d2e5fdc55e4859ea674e75","containing_commit":"06ae816ab30de667b9af06df3d753de2183af873","cr_byte_count":0,"final_newline_count":1,"git_blob_oid":"b76e6708f9810f8571642a6993bc2457709ad21c","git_object_size":19028,"index_mode":"100644","lf_count":360,"maximum_byte":124,"path":"docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_PREPARE_PATHS_PATH_CREATION_GOVERNANCE_CORRECTION_DECISION_v0.1.md"},"path_creation_correction_decision_post_commit_identity_record":{"checked_out_byte_count":5714,"checked_out_sha256":"dfcac9fa32a423add02e0ef465fa94e819a2b4cdaf48b99e38e5d01b6eac325c","commit_file_status":"A","commit_inventory":"EXACTLY_ONE_ADDED_FILE","commit_message":"docs(brainvision): bind blocker 2 R4 path creation correction identity","containing_commit":"864a3c2d486ee22b0af2e9d956df544e805927ba","cr_byte_count":0,"final_newline_count":1,"git_blob_oid":"a063c483c89c7a4387859f29aa00d1209ed881b0","git_object_size":5714,"index_mode":"100644","lf_count":290,"maximum_byte":124,"path":"docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_PREPARE_PATHS_PATH_CREATION_GOVERNANCE_CORRECTION_DECISION_POST_COMMIT_IDENTITY_RECORD_v0.1.md","tab_count":4}},"declaration_role":"CORRECTED_ACTIVE_READY_LAYER_B_CANONICAL_INPUT_PREPARATION_DECISION","deferred_invocation_head_rules":{"accepted_invocation_head_predeclared":false,"accepted_invocation_head_value_available":false,"expected_head_must_equal_final_accepted_invocation_head":true,"expected_origin_main_must_equal_final_accepted_invocation_head":true,"override_authorized":false},"directory_semantics":{"actual_filesystem_effects_control_legality":true,"cleanup_authorized":false,"immediate_parent_must_exist":true,"implicit_intermediate_creation_authorized":false,"one_component_create_new_only":true,"recursive_creation_authorized":false,"retry_without_fresh_governance_authorized":false,"reuse_authorized":false,"selected_child_must_be_absent":true},"execute_exact_single_run_authorized":false,"execution_authority_consumed":false,"execution_authority_created":false,"expected_head_must_equal_final_accepted_invocation_head":true,"expected_origin_main_must_equal_final_accepted_invocation_head":true,"external_directory_creation_authorized":false,"external_temporary_candidate_authorized":false,"first_selected_file_byte_begins_publication":true,"formal_hold":"ACTIVE","governed_canonical_input_path":"C:\\TORMENT\\brainvision_authoritative_inputs\\blocker2_s3b_v0_3\\r4_prepare_paths\\r4_prepare_paths_authorization_input_v0_1.canonical.json","immediate_parent_must_exist":true,"implicit_intermediate_creation_authorized":false,"mode":0,"non_authorizations":{"blocker_2_closure_currently_authorized":false,"blocker_4_activation_currently_authorized":false,"canonical_input_publication_currently_authorized":false,"execute_exact_single_run_currently_authorized":false,"external_directory_creation_currently_authorized":false,"path_creation_record_creation_currently_authorized":false,"preflight_only_currently_authorized":false,"prepare_paths_currently_authorized":false},"one_component_create_new_only":true,"ordered_creation_paths":["C:\\TORMENT\\brainvision_authoritative_inputs","C:\\TORMENT\\brainvision_authoritative_inputs\\blocker2_s3b_v0_3","C:\\TORMENT\\brainvision_authoritative_inputs\\blocker2_s3b_v0_3\\r4_prepare_paths"],"ordered_directory_creation_authority_active":false,"overwrite_authorized":false,"partial_publication_fails_closed":true,"path_creation_record_creation_authorized":false,"path_creation_record_is_separate_from_wrapper_consumed_input":true,"path_creation_record_must_be_complete_and_validated_before_canonical_input_authority_activation":true,"path_creation_record_required":true,"path_model":{"governed_canonical_input_path":"C:\\TORMENT\\brainvision_authoritative_inputs\\blocker2_s3b_v0_3\\r4_prepare_paths\\r4_prepare_paths_authorization_input_v0_1.canonical.json","ordered_creation_paths":["C:\\TORMENT\\brainvision_authoritative_inputs","C:\\TORMENT\\brainvision_authoritative_inputs\\blocker2_s3b_v0_3","C:\\TORMENT\\brainvision_authoritative_inputs\\blocker2_s3b_v0_3\\r4_prepare_paths"],"required_existing_root":"C:\\TORMENT"},"preflight_only_authorized":false,"prepare_paths_invocation_authority_active":false,"prepare_paths_invocation_authorized":false,"prior_candidate_identities":"NON_AUTHORITATIVE_MUST_NOT_BE_REUSED_MUST_BE_REGENERATED","publication_rule":{"append_authorized":false,"atomic_replace_authorized":false,"canonical_input_status_after_publication":"PREPARED_NOT_ACTIVE","construct_in_memory_before_path_contact":true,"copy_authorized":false,"external_temporary_candidate_authorized":false,"first_selected_file_byte_begins_publication":true,"overwrite_authorized":false,"partial_publication_fails_closed":true,"rename_authorized":false},"recursive_creation_authorized":false,"rename_authorized":false,"required_existing_root":"C:\\TORMENT","retired_accepted_invocation_head":"4b0754825d7f0443a4ee696945995bcf6c63230b","retired_canonical_input_publication":"NONE","retired_commit_free_window":"CLOSED","retired_layer_b_preparation_authority":"RETIRED_UNCONSUMED","retired_prepare_paths":"NOT_INVOKED","retired_prepare_paths_attempt":"UNCONSUMED","retired_selected_path_contact":"NONE","retry_without_fresh_governance_authorized":false,"reuse_authorized":false,"schema":"torment.brainvision.blocker2.r4.prepare_paths.corrected_active_ready_layer_b_decision_declaration.v0.1","selected_child_must_be_absent":true}
```

## 16. Terminal State

This draft ends with:

```text
FORMAL_HOLD:
ACTIVE

MODE:
0

BLOCKER-2:
OPEN

BLOCKER-4:
INACTIVE

path-creation correction decision:
COMMITTED
PUSHED
POST-COMMIT IDENTITY-BOUND

correction decision identity record:
COMMITTED
PUSHED
NOT YET POST-COMMIT IDENTITY-BOUND

corrected Layer-B decision:
DRAFT
NOT COMMITTED
NOT PUSHED
NOT IDENTITY-BOUND

fresh accepted invocation HEAD:
NOT ESTABLISHED

corrected commit-free window:
NOT OPEN

ordered directory-creation authority:
NOT ACTIVE

canonical-input preparation authority:
NOT ACTIVE

external directories:
NOT CREATED

path-creation record:
NOT CREATED

canonical input:
NOT CREATED
NOT PUBLISHED

PREPARE_PATHS:
NOT INVOKED

PREFLIGHT_ONLY:
NOT INVOKED

EXECUTE_EXACT_SINGLE_RUN:
NOT INVOKED

execution authority:
NOT CREATED
NOT CONSUMED
```

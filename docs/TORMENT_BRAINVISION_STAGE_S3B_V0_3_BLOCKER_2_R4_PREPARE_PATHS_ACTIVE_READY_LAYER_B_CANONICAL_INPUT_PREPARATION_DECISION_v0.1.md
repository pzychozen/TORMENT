# TORMENT Brainvision Stage S3B v0.3 BLOCKER-2 R4 PREPARE_PATHS Active-Ready Layer-B Canonical Input Preparation Decision v0.1

## 1. Document Status

This document is a draft active-ready Layer-B canonical-input preparation decision candidate for BLOCKER-2 R4 PREPARE_PATHS.

It is not itself a canonical input file. It does not create authority, activate authority, consume authority, prepare canonical input bytes, create Layer C, or authorize PREPARE_PATHS/PREFLIGHT/EXECUTE invocation.

The document is intentionally prepared as a single new untracked candidate. Its authority can only be considered further after it is committed, pushed, and bound by a separate post-commit identity record.

## 2. Governing Inputs

This candidate is derived from the committed Layer-B governance design document and its post-commit identity record:

- Governance design document path: `docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_PREPARE_PATHS_LAYER_B_CANONICAL_INPUT_PREPARATION_GOVERNANCE_DECISION_DRAFT_v0.1.md`
- Governance design document commit: `167ebc657d370e14b2cadc0ae0ccf81b7eafe823`
- Governance design document blob: `9bbc524c030054ce2cb754e8a0cd776446a4332e`
- Governance design document checked-out byte SHA-256: `6247cd5fd541b3ace60514348aa71bd019469131d05a0b52c4e2d359da4a139d`
- Governance identity record path: `docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_PREPARE_PATHS_LAYER_B_GOVERNANCE_DECISION_POST_COMMIT_IDENTITY_RECORD_v0.1.md`
- Governance identity record commit: `86d9d5d51dc6c36f0d736beebbaec56d8a7bf72f`
- Governance identity record blob: `0da79f325d7a2f0b19f02399bb77ab74744d61c8`
- Governance identity record checked-out byte SHA-256: `b78f514fd535ef6df9b642884c8633933da26dd15326d6fc6d20e0f3f9e56161`

This candidate also carries forward the accepted Layer-A authorization document identity:

- Authorization document path: `docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_PREPARE_PATHS_CANONICAL_INPUT_PREPARATION_AUTHORIZATION_v0.1.md`
- Authorization document accepted head: `b9219ca9dbc6bc7608f1aa2356f7f21874fcb524`
- Authorization document blob: `1bbb7b0448b1c7b587c53c2c5105a36134da49f3`
- Authorization document checked-out byte SHA-256: `e49e978126520ea0224407b7052c291f9710e0d156133fb2bcaa700086f244c6`
- Authorization document canonical declaration identity: `a19908c3ab6b447383dabcbc98cf7c0c6ce232f9414e857231003b9988b509d9`
- Authorization document status: `PREPARED_NOT_ACTIVE`

## 3. Decision

This draft decision accepts the Layer-B governance design as the controlling design for the later canonical-input preparation candidate, subject to the remaining activation chain.

The canonical input path governed by this decision is:

`C:\TORMENT\brainvision_authoritative_inputs\blocker2_s3b_v0_3\r4_prepare_paths\r4_prepare_paths_authorization_input_v0_1.canonical.json`

The selected operation remains `PREPARE_PATHS`. The future wrapper payload must represent `wrapper_mode` as `PREPARE_PATHS`, `authorization_status` as `PREPARED_NOT_ACTIVE`, `operator_identity` as `Hilmir`, selected cases as `A1`, `A2`, `A3`, and `A5` in that exact order, `a6_selected` as false, `fault_injection_disabled` as true, and the real executor selector as `REAL_EXISTING_ABSOLUTE_PATH_A1_A2_A3_A5_V0_1`.

This draft does not authorize any wrapper invocation. It only records the Layer-B active-ready decision candidate that a later Layer-C authorization may reference if this document is committed, pushed, and identity-bound.

## 4. Canonical Embedded Declaration

The following is the only canonical embedded JSON declaration in this document. Its extraction rule is the byte sequence between the line immediately following the opening fence and the line immediately preceding the closing fence. For an LF checkout, extraction excludes the final LF immediately preceding the closing declaration fence. For a CRLF checkout, extraction excludes the complete CRLF pair immediately preceding the closing declaration fence. The extracted canonical declaration bytes remain identical across LF and CRLF representations. The extracted bytes are intended to be canonical JSON using sorted keys, compact separators, UTF-8, and no BOM.

```ACTIVE_READY_LAYER_B_DECISION_CANONICAL_JSON
{"a6_selected":false,"accepted_invocation_head_predeclared":false,"active_ready_layer_b_decision_post_commit_identity_record_required":true,"active_ready_layer_b_decision_status":"DRAFTED_NOT_COMMITTED_NOT_ACTIVE","authority_consumed":false,"authority_created":false,"authorization_document_identity":{"accepted_head":"b9219ca9dbc6bc7608f1aa2356f7f21874fcb524","authorization_status":"PREPARED_NOT_ACTIVE","checked_out_byte_count":27028,"checked_out_byte_sha256":"e49e978126520ea0224407b7052c291f9710e0d156133fb2bcaa700086f244c6","checked_out_line_ending_representation":"LF","git_blob_oid":"1bbb7b0448b1c7b587c53c2c5105a36134da49f3","path":"docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_PREPARE_PATHS_CANONICAL_INPUT_PREPARATION_AUTHORIZATION_v0.1.md"},"canonical_input_path":"C:\\TORMENT\\brainvision_authoritative_inputs\\blocker2_s3b_v0_3\\r4_prepare_paths\\r4_prepare_paths_authorization_input_v0_1.canonical.json","canonical_input_preparation_authorized_by_draft":false,"canonical_input_prepared":false,"case_execution_order":["A1","A2","A3","A5"],"commit_free_window_status":"NOT_STARTED","document_path":"docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_PREPARE_PATHS_ACTIVE_READY_LAYER_B_CANONICAL_INPUT_PREPARATION_DECISION_v0.1.md","document_role":"ACTIVE_READY_LAYER_B_CANONICAL_INPUT_PREPARATION_DECISION","execution_authorization_identity_derivation":{"accepted_invocation_head_value_available":false,"declaration_function":"execution_authorization_identity_declaration","derivation_function":"execution_authorization_identity_from_declaration","expected_branch":"main","expected_head_must_equal_final_accepted_invocation_head":true,"expected_origin_main_must_equal_final_accepted_invocation_head":true,"implementation_field_names":["schema","retained_mode","authoritative","retained_run_assessment_identity","implementation_preparation_authorization_identity","runtime_correction_authorization_identity","identity_derivation_cycle_correction_authorization_identity","controlling_document_identities.retained_run_assessment","controlling_document_identities.implementation_preparation_authorization","controlling_document_identities.post_commit_runtime_correction_authorization","controlling_document_identities.identity_derivation_cycle_correction_authorization","expected_branch","expected_head","expected_origin_main","retained_orchestration_policy_sha256","native_helper_policy_sha256","retained_schema_sha256","case_set_sha256","fixture_profile_sha256","authority_registry_root_identity","fixture_root_identity","result_parent_identity","result_directory_derivation_rule","operator_wrapper_identity","operator_identity","single_process_declaration","single_attempt_declaration","real_executor_selector","fault_injection_disabled","host_identity","volume_identity","case_execution_order","selected_a6","source_identities"],"override_authorized":false,"result_directory_derivation_rule":{"caller_selectable":false,"result_child_input":"execution_authorization_identity","result_parent_input":"result_parent_identity","rule":"result_directory = result_parent / execution_authorization_identity","schema":"torment.brainvision.blocker2.retained.result_directory_derivation_rule.v0.1"}},"external_path_rules":{"absolute_drive_qualified_dos_path":true,"copy_into_path_authorized":false,"device_path_authorized":false,"external_directory_creation_authorized_by_this_draft":false,"external_directory_may_be_created_before_preparation":true,"historical_path_reuse_authorized":false,"local_fixed_ntfs_required":true,"outside_repository_required":true,"selected_file_must_be_absent_before_preparation":true,"selected_path":"C:\\TORMENT\\brainvision_authoritative_inputs\\blocker2_s3b_v0_3\\r4_prepare_paths\\r4_prepare_paths_authorization_input_v0_1.canonical.json","symlink_or_reparse_authorized":false,"unc_path_authorized":false,"volume_guid_path_authorized":false,"write_mode":"DIRECT_FIRST_BYTE_PUBLICATION_ONLY"},"formal_hold":"ACTIVE","formal_hold_effect":"DO_NOT_PREPARE_CANONICAL_INPUT","governing_design_document_identity":{"byte_count":33853,"containing_commit":"167ebc657d370e14b2cadc0ae0ccf81b7eafe823","git_blob_oid":"9bbc524c030054ce2cb754e8a0cd776446a4332e","line_count":871,"line_endings":"LF","path":"docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_PREPARE_PATHS_LAYER_B_CANONICAL_INPUT_PREPARATION_GOVERNANCE_DECISION_DRAFT_v0.1.md","sha256":"6247cd5fd541b3ace60514348aa71bd019469131d05a0b52c4e2d359da4a139d"},"governing_design_identity_record":{"byte_count":11255,"containing_commit":"86d9d5d51dc6c36f0d736beebbaec56d8a7bf72f","git_blob_oid":"0da79f325d7a2f0b19f02399bb77ab74744d61c8","line_count":347,"line_endings":"LF","path":"docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_PREPARE_PATHS_LAYER_B_GOVERNANCE_DECISION_POST_COMMIT_IDENTITY_RECORD_v0.1.md","sha256":"b78f514fd535ef6df9b642884c8633933da26dd15326d6fc6d20e0f3f9e56161"},"historical_non_reuse_required":true,"layer_b_preparation_authority_active":false,"layer_c_created":false,"layer_c_required_before_preparation":true,"mode":0,"preflight_authorized":false,"prepare_paths_invocation_authorized":false,"publication_rule":{"cleanup_authorized":false,"direct_write_required":true,"maximum_retry_count":1,"publication_definition":"FIRST_BYTE_AT_SELECTED_PATH","temporary_file_publication_authorized":false},"schema":"torment.brainvision.blocker2.r4.prepare_paths.active_ready_layer_b_decision_declaration.v0.1","selected_cases":["A1","A2","A3","A5"],"true_per_event_identity_available":false,"wrapper_mode_represented_in_future_payload":"PREPARE_PATHS","wrapper_modes_authorized":[]}
```

## 5. Binding Limits

This declaration intentionally excludes this document's own future commit SHA, future git blob OID, checked-out byte SHA-256, checked-out byte count, and canonical embedded declaration identity. Those values do not exist while this file is an untracked draft and must be established only by a later post-commit identity record.

This declaration also excludes future canonical input bytes, canonical input SHA-256, authorization input identity, execution authorization identity, result directory identity, run identity, run result identity, retained completion identity, and any downstream invocation or result identity.

## 6. Activation Chain

Before canonical-input preparation can occur, the following must all be true:

1. This active-ready Layer-B decision candidate is committed and pushed.
2. The active-ready Layer-B decision post-commit identity record is COMMITTED, PUSHED, and IDENTITY-BINDING.
3. Layer C PREPARE_PATHS invocation authorization is COMMITTED and PUSHED.
4. The Layer-C post-commit identity record is COMMITTED and PUSHED.
5. The final accepted invocation HEAD is established after all required pre-invocation governance commits.
6. `HEAD`, `origin/main`, and the required branch agree with the accepted invocation HEAD.
7. The working tree is clean and no git index lock is present.
8. The selected external canonical-input path is absent, and all historical non-reuse checks pass, immediately before preparation.
9. The commit-free window begins only after the final required pre-invocation governance commit.

## 7. Non-Authorizations

This draft does not authorize:

- Creating `C:\TORMENT\brainvision_authoritative_inputs\blocker2_s3b_v0_3\r4_prepare_paths` under this draft is not authorized. Per Section 17 of the committed governance design, the operator may create that directory before preparation once preparation authority is active; this draft grants no such authority now.
- Creating `C:\TORMENT\brainvision_authoritative_inputs\blocker2_s3b_v0_3\r4_prepare_paths\r4_prepare_paths_authorization_input_v0_1.canonical.json`; the selected canonical-input file must remain absent before preparation
- Writing, copying, renaming, appending, atomically replacing, or cleaning up any canonical input candidate
- Invoking wrapper mode `PREPARE_PATHS`
- Invoking wrapper mode `PREFLIGHT_ONLY`
- Invoking wrapper mode `EXECUTE_EXACT_SINGLE_RUN`
- Creating, consuming, or mutating authority registry entries
- Selecting case `A4`, `A6`, `A7`, or `A8`
- Enabling fault injection
- Changing implementation code, schema, tests, configuration, git attributes, or line endings

## 8. Final-Head Binding Gap

The committed Layer-B governance design requires `expected_head` and `expected_origin_main` in the execution authorization identity declaration to equal the accepted invocation HEAD.

At this draft stage, that accepted invocation HEAD does not yet exist because this document, its post-commit identity record, Layer C authorization, and Layer C identity record have not yet been committed. The wrapper implementation also rejects non-commit symbolic values in those fields.

Therefore this decision can bind the rule that both fields must equal the final accepted invocation HEAD, but it cannot truthfully predeclare the concrete commit value or any identity derived from that value. That concrete value must be supplied only after the final pre-invocation governance commit establishes the accepted invocation HEAD.

## 9. Live-Head and Commit-Free Sequencing

This decision preserves Model 3.

All pre-invocation governance commits must occur before canonical-input preparation. The commit-free window begins only after the final required pre-invocation governance commit and includes activation, preparation, any permitted retry, independent validation, and any later PREPARE_PATHS invocation.

Any commit during that commit-free window voids activation, retires the accepted invocation HEAD, retires any published candidate, retires Layer-B authority, and requires a fresh committed and pushed Layer-B baseline.

This active-ready decision commit, if later performed, is a pre-window governance commit.

## 10. Publication and Consumption Semantics

If canonical-input preparation is later authorized, publication is defined as the first byte written to the selected canonical-input path. Direct write is required. Temporary-file rename, copy, and atomic replacement are prohibited.

A partial selected-path write is consumed. A published candidate later rejected by validation is consumed. A successful write followed by identity-reporting failure is consumed. A genuine pre-contact failure is not consumed.

At most one retry is permitted, and only in the same operator session. Any failure record belongs outside the repository during the commit-free window. Published candidate cleanup is prohibited.

This draft records those rules only; it does not activate them.

## 11. Layer-C Constraint

Layer C must be committed before canonical-input preparation.

Layer C cannot bind canonical-input SHA-256, canonical-input byte count, canonical declaration identity, or other post-publication candidate identities.

Layer C may bind the selected external path, governing Layer-B identities, required schema and validation constraints, PREPARE_PATHS mode, and invocation-time durable capture requirements.

## 12. Historical Non-Reuse

This decision prohibits reuse of historical authorization documents, canonical inputs, canonical-input identities, execution-authorization identities, run identities, result directories, authority-registry entries, historical successor-lane paths, and historical Layer-B artifacts.

Same-HEAD repeat remains prohibited. True per-event identity remains unavailable under the current schema.

## 13. Future Post-Commit Identity Record

A separate future post-commit identity record must bind at least this decision path, containing commit SHA, git blob OID, index mode, checked-out byte count, checked-out SHA-256, line-ending representation, canonical embedded declaration identity, HEAD at record time, origin/main at record time, branch, working-tree state, and `.git/index.lock` state.

This draft does not include that future record's commit identity.

## 14. Candidate Outcome

This document prepares a reviewable Layer-B active-ready decision candidate only.

The terminal classification of this corrected draft is:

`BLOCKER_2_R4_PREPARE_PATHS_ACTIVE_READY_LAYER_B_DECISION_CORRECTED_DRAFT_NOT_COMMITTED_NOT_ACTIVE`

The required terminal state is:

`DRAFTED_NOT_COMMITTED_NOT_ACTIVE`

Final required state preserved by this draft:

- `FORMAL_HOLD`: `ACTIVE`
- `FORMAL_HOLD` effect: `DO_NOT_PREPARE_CANONICAL_INPUT`
- `MODE`: `0`
- `BLOCKER-2`: `OPEN`
- `BLOCKER-4`: `INACTIVE`
- Layer-B governance design document: committed, pushed, identity-bound
- Layer-B design identity record: committed and pushed
- active-ready Layer-B decision: corrected draft, not committed, not active (`CORRECTED_DRAFT_NOT_COMMITTED_NOT_ACTIVE`; underlying decision status remains `DRAFTED_NOT_COMMITTED_NOT_ACTIVE`)
- active-ready Layer-B decision post-commit identity record: not created
- Layer-B preparation authority: not active
- canonical input: not prepared
- Layer C: not created
- accepted invocation HEAD: not yet established
- commit-free window: not started
- PREPARE_PATHS: not invoked
- authority: not created and not consumed

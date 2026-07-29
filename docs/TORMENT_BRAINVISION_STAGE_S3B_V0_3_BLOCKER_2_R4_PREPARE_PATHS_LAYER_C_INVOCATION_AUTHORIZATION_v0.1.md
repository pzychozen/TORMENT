# TORMENT Brainvision Stage S3B v0.3 BLOCKER-2 R4 PREPARE_PATHS Layer-C Invocation Authorization v0.1

## 1. Draft Status

This document is a draft Layer-C governance artifact for the future `PREPARE_PATHS` invocation boundary.

It is not committed, not pushed, not active, and not identity-bound.

Brainvision remains `OFFLINE`, `QUARANTINED`, and `SYNTHETIC-RESEARCH ONLY`.

Layer C is not the canonical input. Layer C is not the wrapper-consumed authorization input. Layer C is not execution authority, not a PREPARE_PATHS result, and not an authority-consumption event.

## 2. Governing Layer-B Identities

Active-ready Layer-B decision:

- path: `docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_PREPARE_PATHS_ACTIVE_READY_LAYER_B_CANONICAL_INPUT_PREPARATION_DECISION_v0.1.md`
- containing commit: `adb8cd1ee06977e731b016d9cf8a9a1400bb71b0`
- index mode: `100644`
- git blob OID: `40143e922308455c5b1bff4def6dfa19f98ca337`
- checked-out byte count: `17237`
- checked-out SHA-256: `dea5810af30b83d6903f979f478fb4088a74c77208ef2269369ead96813d7f3a`
- embedded declaration byte count: `5591`
- embedded declaration SHA-256: `f5cba3e71b41600f8f87b067358d04a3099aead0f81b170de476b94df2cce9f5`
- source schema: `torment.brainvision.blocker2.r4.prepare_paths.active_ready_layer_b_decision_declaration.v0.1`

Active-ready Layer-B decision post-commit identity record:

- path: `docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_PREPARE_PATHS_ACTIVE_READY_LAYER_B_DECISION_POST_COMMIT_IDENTITY_RECORD_v0.1.md`
- containing commit: `8b1bc66816a7457d110c04feb939355f9dc684de`
- index mode: `100644`
- git blob OID: `b42de195f31edc493961c44efd30883766cbc09f`
- checked-out byte count: `4966`
- checked-out SHA-256: `af5bb232a88999fd47e6f0420b15ab86d9627129fd1fa14374ce325a3f721cd9`

## 3. Layer-C Purpose

Layer C governs only the future invocation boundary for one `PREPARE_PATHS` invocation after all Layer-B and Layer-C gates pass.

It distinguishes:

- Layer-B canonical-input preparation authority
- Layer-C PREPARE_PATHS invocation authorization
- the future canonical input itself
- the final accepted invocation HEAD
- the commit-free window
- runtime invocation
- authority creation or consumption

Layer C is the final repository governance artifact that must later be post-commit identity-bound before the accepted invocation HEAD can be established.

## 4. Deferred Invocation-HEAD Architecture

At draft time, the final accepted invocation HEAD is `NOT YET ESTABLISHED`.

The concrete accepted invocation HEAD is deferred until after:

1. Layer-C authorization is committed.
2. Layer-C post-commit identity record is committed.
3. `HEAD` and `origin/main` are verified equal at the final pre-invocation governance commit.

This draft does not predeclare its own future containing commit. It does not invent `expected_head`, `expected_origin_main`, `repository_identity.head`, `repository_identity.origin_main`, `execution_authorization_identity`, `authorization_input_identity`, or an accepted invocation HEAD.

Normative future rules:

- `accepted_invocation_head_predeclared`: `false`
- `accepted_invocation_head_value_available`: `false`
- `expected_head_must_equal_final_accepted_invocation_head`: `true`
- `expected_origin_main_must_equal_final_accepted_invocation_head`: `true`
- `override_authorized`: `false`

## 5. Preconditions for Future Activation

Layer-C invocation authorization may become active only after all of the following are true:

1. The active-ready Layer-B decision is committed and identity-bound.
2. The Layer-B decision post-commit identity record is committed and verified.
3. This Layer-C authorization is committed.
4. The Layer-C authorization post-commit identity record is committed.
5. `HEAD` equals `origin/main` at the final accepted invocation HEAD.
6. The working tree is clean.
7. `.git/index.lock` is absent.
8. The final accepted invocation HEAD is explicitly established.
9. The commit-free window begins only after that establishment.
10. Runtime and historical non-reuse gates pass.
11. The canonical input path is the exact governed absolute path.
12. The selected canonical input file did not exist before authorized preparation.
13. Exactly one canonical input is prepared.
14. The prepared input is externally validated.
15. No repository commit occurs during the commit-free window before PREPARE_PATHS.

All historical non-reuse rules, freshness-proof requirements, execution-authorization derivation constraints, and runtime policy, schema, and identity requirements bound by the active-ready Layer-B decision identified in Section 2 remain in full force and are incorporated into Layer C by that exact committed identity. Nothing in this document narrows, replaces, or supersedes them.

Inherited Layer-B rules include, at minimum, non-reuse or fresh identity binding for earlier PREPARE_PATHS inputs, earlier PREFLIGHT inputs, earlier execution inputs, earlier authorization documents, earlier execution authority, earlier accepted invocation HEADs, earlier external paths, earlier case-set identities, earlier results and receipts, canonical-input bytes, authorization-input bytes, execution-authorization identity, repository HEAD, governed path, runtime policy identities, and runtime schema identities.

These conditions are not claimed to be satisfied by this draft.

## 6. Governed Canonical Input Path

The governed future path is:

`C:\TORMENT\brainvision_authoritative_inputs\blocker2_s3b_v0_3\r4_prepare_paths\r4_prepare_paths_authorization_input_v0_1.canonical.json`

Path rules:

- absolute
- drive-qualified DOS path
- local fixed NTFS
- outside repository
- not UNC
- not device path
- not volume-GUID path
- not reparse point

Directory creation before preparation authority becomes active is `NOT AUTHORIZED`.

Directory creation after preparation authority becomes active is `PERMITTED IF ABSENT AND ALL PATH GATES PASS`.

The selected canonical-input file before preparation `MUST BE ABSENT`.

Layer C does not create the directory or the file.

## 7. Commit-Free Window

At draft time, the commit-free window is `NOT STARTED`.

The commit-free window begins only after the Layer-C post-commit identity record has been committed and the final accepted invocation HEAD has been established.

Once started:

- no repository commit of any kind may occur before PREPARE_PATHS invocation
- `HEAD` must remain equal to the accepted invocation HEAD
- `origin/main` must remain equal to the accepted invocation HEAD
- the repository working tree and index must remain completely unmutated; canonical-input preparation is an external filesystem operation outside the repository and is not a repository mutation
- the working tree remains clean
- the index remains clean
- `.git/index.lock` remains absent
- no unrelated mutation is permitted

The only mutation permitted during the commit-free window is publication of the single canonical input at the governed external path. No repository file, index entry, ref, branch pointer, tag, Git metadata state, or commit may change.

Committing Layer C alone does not start the commit-free window.

## 8. Future Authorization Scope

The maximum future scope is one `PREPARE_PATHS` invocation against exactly one externally validated canonical input, bound to the final accepted invocation HEAD, under the governed external path, after all Layer-B and Layer-C gates pass.

Layer C does not authorize:

- `PREFLIGHT_ONLY`
- `EXECUTE_EXACT_SINGLE_RUN`
- a second `PREPARE_PATHS` invocation
- retry after a partial, interrupted, crashed, or non-terminating `PREPARE_PATHS` invocation
- automatic regeneration of the canonical input
- input reuse
- historical authorization reuse
- authorization substitution
- path substitution
- HEAD drift
- origin/main drift
- repository commits during the commit-free window
- runtime code changes
- test changes
- schema changes
- BLOCKER-4
- production integration

Any `PREPARE_PATHS` invocation that begins exhausts the single authorized invocation attempt, whether or not it reaches a terminal record. A partial, interrupted, crashed, or non-terminating invocation is not retried under this authorization. Recovery requires a fresh committed and pushed governance baseline and new explicit authorization. The invocation attempt count is one, successful completion count is at most one, a begun attempt counts even when no terminal record is produced, no automatic retry is authorized, no automatic canonical-input regeneration is authorized, and no implicit continuation is authorized.

No authority is created or consumed by drafting or later committing Layer C.

## 9. Fail-Closed Conditions

The authorization fails closed on:

- repository baseline mismatch
- `HEAD != origin/main`
- unexpected HEAD
- working-tree contamination
- staged changes
- `.git/index.lock` present
- Layer-B identity mismatch
- Layer-C identity record absent
- canonical input path mismatch
- canonical input pre-existence
- multiple candidate inputs
- external path inadmissible
- reparse-point involvement
- non-local or non-fixed drive
- historical input reuse
- authorization identity reuse
- runtime gate mismatch
- commit during the commit-free window
- unresolved placeholder
- non-canonical declaration
- non-finite JSON
- duplicate JSON keys

No repair, fallback, inference, substitution, closest-match behavior, retry, automatic regeneration, or normalization of mismatched identity is authorized.

## 10. Canonical Embedded Governance Declaration

The following is a governance declaration describing future constraints. It is not the canonical input, not the wrapper authorization input, not execution authority, not the PREPARE_PATHS result, and not a consumed declaration.

Extraction excludes the final LF immediately preceding the closing declaration fence under LF checkout, and excludes the complete CRLF pair immediately preceding the closing declaration fence under CRLF checkout.

```LAYER_C_INVOCATION_AUTHORIZATION_DECLARATION_CANONICAL_JSON
{"authority_payload_embedded":false,"automatic_regeneration_authorized":false,"canonical_input_path":"C:\\TORMENT\\brainvision_authoritative_inputs\\blocker2_s3b_v0_3\\r4_prepare_paths\\r4_prepare_paths_authorization_input_v0_1.canonical.json","canonical_input_payload_embedded":false,"canonical_input_state":"NOT_PREPARED","commit_free_window":{"begin_condition":"AFTER_LAYER_C_IDENTITY_RECORD_COMMITTED_AND_FINAL_ACCEPTED_INVOCATION_HEAD_ESTABLISHED","commit_before_prepare_paths_authorized":false,"commits_during_window_authorized":false,"external_preparation_is_repository_mutation":false,"head_must_remain_final_accepted_invocation_head":true,"origin_main_must_remain_final_accepted_invocation_head":true,"repository_mutation_during_window_authorized":false,"state_at_draft":"NOT_STARTED"},"declaration_role":"GOVERNANCE_DECLARATION_DESCRIBING_FUTURE_CONSTRAINTS","deferred_invocation_head_rules":{"accepted_invocation_head_predeclared":false,"accepted_invocation_head_value_available":false,"concrete_accepted_invocation_head_embedded":false,"expected_head_must_equal_final_accepted_invocation_head":true,"expected_origin_main_must_equal_final_accepted_invocation_head":true,"override_authorized":false},"fail_closed_conditions":["repository_baseline_mismatch","head_origin_main_mismatch","unexpected_head","working_tree_contamination","staged_changes","git_index_lock_present","layer_b_identity_mismatch","layer_c_identity_record_absent","canonical_input_path_mismatch","canonical_input_pre_existence","multiple_candidate_inputs","external_path_inadmissible","reparse_point_involvement","non_local_or_non_fixed_drive","historical_input_reuse","authorization_identity_reuse","runtime_gate_mismatch","commit_during_commit_free_window","repository_mutation_during_commit_free_window","partial_invocation_retry_attempted","automatic_regeneration_attempted","unresolved_token","non_canonical_declaration","non_finite_json","duplicate_json_keys"],"formal_hold":"ACTIVE","layer_b_decision_identity":{"canonical_declaration_byte_count":5591,"canonical_declaration_sha256":"f5cba3e71b41600f8f87b067358d04a3099aead0f81b170de476b94df2cce9f5","checked_out_byte_count":17237,"checked_out_sha256":"dea5810af30b83d6903f979f478fb4088a74c77208ef2269369ead96813d7f3a","containing_commit":"adb8cd1ee06977e731b016d9cf8a9a1400bb71b0","git_blob_oid":"40143e922308455c5b1bff4def6dfa19f98ca337","index_mode":"100644","path":"docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_PREPARE_PATHS_ACTIVE_READY_LAYER_B_CANONICAL_INPUT_PREPARATION_DECISION_v0.1.md","source_schema":"torment.brainvision.blocker2.r4.prepare_paths.active_ready_layer_b_decision_declaration.v0.1"},"layer_b_identity_record_identity":{"checked_out_byte_count":4966,"checked_out_sha256":"af5bb232a88999fd47e6f0420b15ab86d9627129fd1fa14374ce325a3f721cd9","containing_commit":"8b1bc66816a7457d110c04feb939355f9dc684de","git_blob_oid":"b42de195f31edc493961c44efd30883766cbc09f","index_mode":"100644","path":"docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_PREPARE_PATHS_ACTIVE_READY_LAYER_B_DECISION_POST_COMMIT_IDENTITY_RECORD_v0.1.md"},"layer_c_authorization_status":"DRAFT_ONLY_NOT_ACTIVE_NOT_COMMITTED_NOT_IDENTITY_BOUND","mode":0,"non_authorizations":["layer_b_preparation_authority_activation","canonical_input_preparation","canonical_input_creation","layer_c_identity_record_creation","final_accepted_invocation_head_establishment","commit_free_window_start","immediate_prepare_paths_invocation","preflight_only","execute_exact_single_run","wrapper_authority_creation","authority_consumption","automatic_canonical_input_regeneration","partial_prepare_paths_invocation_retry","implicit_invocation_continuation","blocker_2_closure","blocker_4_activation"],"non_reuse_rules":{"authorization_reuse_authorized":false,"canonical_input_reuse_authorized":false,"historical_authorization_reuse_authorized":false,"input_reuse_authorized":false,"path_substitution_authorized":false},"path_rules":{"absolute":true,"device_path_authorized":false,"directory_creation_after_active_preparation_authority":"PERMITTED_IF_ABSENT_AND_ALL_PATH_GATES_PASS","directory_creation_before_active_preparation_authority":"NOT_AUTHORIZED","drive_qualified_dos_path":true,"local_fixed_ntfs":true,"not_reparse_point":true,"outside_repository":true,"selected_file_must_be_absent_before_preparation":true,"unc_path_authorized":false,"volume_guid_path_authorized":false},"permanent_state":{"accepted_invocation_head":"NOT_YET_ESTABLISHED","authority":"NOT_CREATED_NOT_CONSUMED","blocker_2":"OPEN","blocker_4":"INACTIVE","canonical_input":"NOT_PREPARED","commit_free_window":"NOT_STARTED","execute_exact_single_run":"UNAUTHORIZED","formal_hold":"ACTIVE","layer_b_preparation_authority":"NOT_ACTIVE","layer_c_authorization":"DRAFT_ONLY_NOT_ACTIVE_NOT_COMMITTED_NOT_IDENTITY_BOUND","mode":0,"preflight":"BLOCKED","prepare_paths":"NOT_INVOKED"},"prohibited_modes":["PREFLIGHT_ONLY","EXECUTE_EXACT_SINGLE_RUN"],"retry_after_partial_invocation_authorized":false,"schema":"torment.brainvision.blocker2.r4.prepare_paths.layer_c_invocation_authorization_declaration.v0.1","single_invocation_scope":{"canonical_input_count":1,"canonical_input_validation_required":true,"head_binding_required":true,"invocation_attempt_count":1,"invocation_count":1,"invocation_mode":"PREPARE_PATHS","path_binding_required":true},"wrapper_consumed":false}
```

## 11. Explicit Non-Authorization Ruling

Drafting, reviewing, accepting, or later committing Layer C does not by itself:

- activate Layer-B preparation authority
- prepare the canonical input
- create the canonical input file
- create the Layer-C post-commit identity record
- establish the final accepted invocation HEAD
- start the commit-free window
- authorize immediate PREPARE_PATHS invocation
- authorize `PREFLIGHT_ONLY`
- authorize `EXECUTE_EXACT_SINGLE_RUN`
- create wrapper authority
- consume authority
- close BLOCKER-2
- activate BLOCKER-4

The Layer-C post-commit identity record and final invocation-HEAD establishment remain distinct later steps.

## 12. Permanent State Preserved

- `FORMAL_HOLD`: `ACTIVE`
- `MODE`: `0`
- `BLOCKER-2`: `OPEN`
- `BLOCKER-4`: `INACTIVE`
- Layer-B preparation authority: `NOT ACTIVE`
- canonical input: `NOT PREPARED`
- Layer-C authorization: `DRAFT ONLY`, `NOT ACTIVE`, `NOT COMMITTED`, `NOT IDENTITY-BOUND`
- accepted invocation HEAD: `NOT YET ESTABLISHED`
- commit-free window: `NOT STARTED`
- `PREPARE_PATHS`: `NOT INVOKED`
- `PREFLIGHT`: `BLOCKED`
- `EXECUTE_EXACT_SINGLE_RUN`: `UNAUTHORIZED`
- authority: `NOT CREATED`, `NOT CONSUMED`

## 13. Terminal Classification

`BLOCKER_2_R4_LAYER_C_PREPARE_PATHS_INVOCATION_AUTHORIZATION_DRAFT_COMPLETE_NOT_REVIEWED_NOT_COMMITTED_NOT_ACTIVE`

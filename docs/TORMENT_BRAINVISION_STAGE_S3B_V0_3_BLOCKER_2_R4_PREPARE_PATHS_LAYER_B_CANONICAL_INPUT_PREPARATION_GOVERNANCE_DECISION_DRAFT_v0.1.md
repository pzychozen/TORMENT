# TORMENT Brainvision Stage S3B v0.3 BLOCKER-2 R4 PREPARE_PATHS Layer-B Canonical-Input Preparation Governance Decision Draft v0.1

## 1. Document Status

This document is a governance draft.

It does not authorize canonical-input preparation.

It does not authorize `PREPARE_PATHS`, `PREFLIGHT_ONLY`, or `EXECUTE_EXACT_SINGLE_RUN`.

Terminal classification for this draft:

```text
BLOCKER_2_R4_LAYER_B_CANONICAL_INPUT_PREPARATION_GOVERNANCE_DECISION_FINAL_CORRECTED_DRAFT_NOT_AUTHORIZED
```

Mandatory terminal posture after this draft is created:

```text
FORMAL_HOLD: ACTIVE
MODE: 0
BLOCKER-2: OPEN
BLOCKER-4: INACTIVE
layer-B: FINAL_CORRECTED_DRAFT_NOT_AUTHORIZED
canonical input: NOT PREPARED
layer-C: NOT AUTHORIZED
PREPARE_PATHS: NOT INVOKED
PREFLIGHT: BLOCKED
EXECUTE_EXACT_SINGLE_RUN: UNAUTHORIZED
execution authority: NOT CREATED
execution authority: NOT CONSUMED
```

## 2. Purpose and Scope

This draft designs the Layer-B governance decision required before preparing exactly one new external canonical JSON authorization input for the BLOCKER-2 R4 `PREPARE_PATHS` remediation path.

The proposed Layer-B decision, if later accepted, committed, pushed, identity-bound, and activated by Hilmir, would authorize only this action:

```text
Prepare exactly one fresh external canonical JSON input for wrapper_mode PREPARE_PATHS, for the R4 remediation attempt, bound to the accepted R4 authorization-document governance chain, for later independent validation.
```

The Layer-B decision would not authorize invoking the wrapper in any mode. The future JSON payload may contain `"wrapper_mode":"PREPARE_PATHS"` because the implementation requires that value for a `PREPARE_PATHS` candidate input, but that field value is input content only. It is not invocation authority.

Brainvision remains offline, quarantined, and synthetic-research-only.

## 3. Authoritative Drafting Baseline

This draft was prepared against the required repository baseline:

```text
branch: main
HEAD: a222217026ac8f74bddabd07ea9d6a73a33dd9e6
origin/main: a222217026ac8f74bddabd07ea9d6a73a33dd9e6
working tree before drafting: clean
.git/index.lock before drafting: absent
```

This baseline is the analysis baseline for this draft. It is not itself an active Layer-B governance baseline.

## 4. Source Artifact Identities

The accepted Layer-A authorization-document path is:

```text
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_PREPARE_PATHS_CANONICAL_INPUT_PREPARATION_AUTHORIZATION_v0.1.md
```

The accepted authorization-document HEAD is:

```text
b9219ca9dbc6bc7608f1aa2356f7f21874fcb524
```

The complete five-field authorization-document identity preserved by the post-commit identity record is:

```text
path: docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_PREPARE_PATHS_CANONICAL_INPUT_PREPARATION_AUTHORIZATION_v0.1.md
git_blob_oid: 1bbb7b0448b1c7b587c53c2c5105a36134da49f3
checked_out_byte_sha256: e49e978126520ea0224407b7052c291f9710e0d156133fb2bcaa700086f244c6
canonical_authorization_declaration_identity: a19908c3ab6b447383dabcbc98cf7c0c6ce232f9414e857231003b9988b509d9
authorization_status: PREPARED_NOT_ACTIVE
```

The representation binding recorded outside the five-field object is:

```text
checked_out_byte_count: 27028
checked_out_line_ending_representation: LF
```

The checked-out byte SHA-256 and byte count are representation-dependent. They must be recomputed before any future preparation if checkout, branch, reset, line-ending conversion, file rewrite, or Git configuration changes affect the checked-out bytes. The five-field object does not contain `checked_out_byte_count`.

The descriptive post-commit identity record path is:

```text
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_PREPARE_PATHS_AUTHORIZATION_DOCUMENT_POST_COMMIT_IDENTITY_RECORD_v0.1.md
```

That record grants no Layer-B or Layer-C authority.

## 5. Review Provenance

Accepted review provenance for this governance chain:

```text
Codex: drafted the Layer-A post-commit identity record
Claude: independently reviewed that record
Codex: drafted and corrected the current Layer-B governance decision
Claude: independently reviewed the current Layer-B draft
```

This provenance statement corrects reviewer context only. It does not alter the accepted technical findings from independent review.

## 6. Governance-Layer Separation

Layer A is the authorization-document creation and post-commit identity layer. Layer A is complete for the R4 authorization-document artifact, but its status `PREPARED_NOT_ACTIVE` does not prepare or activate a canonical wrapper input.

Layer B is the canonical-input preparation layer. Layer B may only authorize preparation of one external canonical JSON file and its independent validation artifacts. Layer B does not create path directories through the wrapper and does not touch execution authority.

Layer C is the wrapper-invocation layer. Layer C remains unauthorized by this draft and by the proposed Layer-B decision.

No governance layer may reuse a historical successor-lane authority merely because this new R4 chain exists.

## 7. Proposed Layer-B Lifecycle

A future Layer-B decision should use distinct lifecycle labels for the document, the preparation authority, the candidate input, and invocation authority.

Recommended lifecycle:

```text
document_lifecycle_state: DRAFT_UNCOMMITTED, COMMITTED_IDENTITY_PENDING, COMMITTED_IDENTITY_BOUND
preparation_authority_state: NOT_AUTHORIZED, ACTIVE_SINGLE_USE, CONSUMED, RETIRED, SUPERSEDED
canonical_input_state: NOT_PREPARED, PREPARED_PENDING_VALIDATION, VALIDATED, REJECTED_HISTORICAL
invocation_authority_state: NOT_AUTHORIZED
```

Document acceptance may occur before Layer C exists.

Document commitment and identity binding may occur before Layer C exists.

Preparation authority activation must not occur until Layer C and its post-commit identity record are committed and pushed.

The Layer-B decision must itself be committed and pushed before becoming active. A draft, uncommitted file, locally modified file, or committed file without post-commit identity binding cannot activate Layer-B preparation.

Activation requires all of:

```text
Layer-B decision committed and pushed
Layer-B post-commit identity record committed and pushed
Layer-C PREPARE_PATHS invocation authorization committed and pushed
Layer-C post-commit identity record committed and pushed
HEAD == origin/main
tracked tree clean
.git/index.lock absent
exact external input path fixed and verified absent
all identity derivations fixed
historical non-reuse checks passed
```

Activation grants authority only to prepare one canonical input. It grants no authority to invoke any wrapper mode.

The accepted invocation HEAD is the repository HEAD after the final required pre-invocation governance commit, with HEAD equal to origin/main, tracked tree clean, and `.git/index.lock` absent.

## 8. Canonical Embedded Declaration Requirement

The active Layer-B decision should contain exactly one embedded canonical JSON declaration.

The declaration must be canonical JSON with UTF-8 bytes, no BOM, sorted keys recursively, separators `,` and `:`, `ensure_ascii=false`, `allow_nan=false`, no duplicate object keys, exactly one top-level object, no comments, no trailing data, and no trailing newline inside the extracted canonical byte range.

To avoid circular dependency, the embedded Layer-B declaration must exclude:

```text
the Layer-B document git_blob_oid
the Layer-B document checked_out_byte_sha256
the Layer-B document checked_out_byte_count
the accepted Layer-B containing commit SHA
future canonical input bytes
future canonical input checked-out or external byte SHA-256
future authorization_input_identity
future canonical input declaration identity
future PREPARE_PATHS result identity
future PREFLIGHT result identity
future execution authorization consumption identity
future run identity generated by execution
future result stdout or stderr hashes
```

The declaration may include stable governance inputs, intended status labels, the accepted Layer-A authorization-document five-field identity, required wrapper schema names, fixed root constraints, case lock, and prohibitions.

## 9. Post-Commit Identity Record Requirement

A separate Layer-B post-commit identity record is required.

The record should bind:

```text
Layer-B document path
Layer-B git_blob_oid
Layer-B checked_out_byte_sha256
Layer-B checked_out_byte_count
Layer-B checked-out line-ending representation
Layer-B canonical embedded declaration identity
accepted Layer-B HEAD
accepted Layer-B origin/main
branch main
tree cleanliness at record time
.git/index.lock absence at record time
```

The Layer-B post-commit identity record must be committed before input preparation. The record is descriptive and identity-binding only. It does not activate Layer B by itself, grants no Layer-C authority, and grants no wrapper invocation authority.

The post-commit identity record must be descriptive only unless a later governance order explicitly grants it additional status. It must not contain future canonical input bytes or a future canonical input identity unless the governance sequence is deliberately changed and independently reviewed.

## 10. Proposed Authorized Action After Activation

If and only if the future Layer-B decision is active, it may authorize a single operator action:

```text
Create one fresh external canonical JSON authorization input file for wrapper_mode PREPARE_PATHS.
```

The action must be performed in the `torment` Command Prompt conda environment or an equivalently declared Windows operator environment, by Hilmir or by a governance-approved operator acting for Hilmir.

The action may calculate required current identities and write the single external canonical JSON file. It may not run:

```text
research/brainvision/run_blocker2_authoritative_retained_single_run_v0_1.py --mode PREPARE_PATHS
research/brainvision/run_blocker2_authoritative_retained_single_run_v0_1.py --mode PREFLIGHT_ONLY
research/brainvision/run_blocker2_authoritative_retained_single_run_v0_1.py --mode EXECUTE_EXACT_SINGLE_RUN
```

It may not create or consume execution authority.

## 11. Mandatory Wrapper Input Schema

The future canonical input must use:

```text
schema: torment.brainvision.blocker2.operator_wrapper.authorization_input.v0.2
authorization_input_declaration_schema: torment.brainvision.blocker2.operator_wrapper.authorization_input_declaration.v0.2
authorization_input_identity_schema: torment.brainvision.blocker2.operator_wrapper.authorization_input_identity.v0.1
wrapper_version: v0.2
```

The complete mandatory top-level wrapper fields are:

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

Missing top-level fields and unknown top-level fields are both prohibited.

Required fixed values include:

```text
authorization_status: PREPARED_NOT_ACTIVE
wrapper_mode: PREPARE_PATHS
operator_identity: Hilmir
single_process_declaration: one Windows Command Prompt process
single_attempt_declaration: one authoritative attempt
real_executor_selector: REAL_EXISTING_ABSOLUTE_PATH_A1_A2_A3_A5_V0_1
retained_mode: BLOCKER2_ABSOLUTE_PATH_CONTROL_RETAINED_SINGLE_RUN_V0_1
authoritative: true
fault_injection_disabled: true
a6_selected: false
```

For `PREPARE_PATHS`, `authorization_status == PREPARED_NOT_ACTIVE` is governance-enforced, not wrapper-enforced. `PREFLIGHT_ONLY` and `EXECUTE_EXACT_SINGLE_RUN` later require an `ACTIVE` authorization-document state and new governance identities. The current Layer-A `PREPARED_NOT_ACTIVE` identity does not grant or satisfy those later modes. The Layer-B-prepared `PREPARE_PATHS` candidate must not claim `ACTIVE` merely to satisfy future modes.

## 12. Required Nested Identity Shapes

The future `authorization_input_identity` object must contain exactly:

```text
schema
authorization_input_sha256
canonical_authorization_declaration_identity
```

The declaration payload is the complete future authorization payload with only the `authorization_input_identity` key removed.

The declaration envelope is this pseudo-JSON structure:

```text
{
  "schema": "torment.brainvision.blocker2.operator_wrapper.authorization_input_declaration.v0.2",
  "authorization_input": declaration_payload
}
```

The `authorization_input` value is the complete `declaration_payload` object. The literal string `"<declaration_payload object>"` is not present and must not be hashed.

The `authorization_input_sha256` must be the SHA-256 of `canonical_json_bytes(declaration_payload)`.

The `canonical_authorization_declaration_identity` must be the SHA-256 of `canonical_json_bytes(declaration)`.

The payload hash and declaration-envelope hash are different identities. They must not be calculated from the same byte object.

The future `execution_authorization_document_identity` object must contain exactly the five fields preserved in Section 4:

```text
path
git_blob_oid
checked_out_byte_sha256
canonical_authorization_declaration_identity
authorization_status
```

No byte count, line-ending label, accepted HEAD, or extra field may be added to that nested object unless the wrapper schema is changed by a separately authorized code change. Byte count and line-ending representation must remain governance-side bindings or inventory-side observations.

The future `runtime_declaration_identities` object must contain exactly:

```text
retained_orchestration_policy_sha256
native_helper_policy_sha256
retained_schema_sha256
case_set_sha256
fixture_profile_sha256
authority_registry_profile_sha256
evidence_chain_sha256
retained_mode_identity
```

The future `path_model` object must contain exactly:

```text
authority_registry_root
fixture_root
result_parent
result_directory
global_authority_entry_path
local_gate_path
run_result_path
retained_completion_path
```

The future `execution_authorization_identity_block` and `retained_authorization` structures must be internally consistent with each other and with the derived path model. The retained authorization identity must equal the execution authorization identity in the execution block.

## 13. Execution-Authorization Identity Derivation

The following future payload fields must be identical:

```text
retained_authorization.authorization_identity
execution_authorization_identity_block.execution_authorization_identity
```

They must equal the result of the current implementation's `execution_authorization_identity_from_declaration()` applied to the declaration generated by `execution_authorization_identity_declaration()` in:

```text
research/brainvision/blocker2_retained_absolute_path_control_v0_1.py
```

The declaration object contains these implementation field names and shapes:

```text
schema
retained_mode
authoritative
retained_run_assessment_identity
implementation_preparation_authorization_identity
runtime_correction_authorization_identity
identity_derivation_cycle_correction_authorization_identity
controlling_document_identities.retained_run_assessment
controlling_document_identities.implementation_preparation_authorization
controlling_document_identities.post_commit_runtime_correction_authorization
controlling_document_identities.identity_derivation_cycle_correction_authorization
expected_branch
expected_head
expected_origin_main
retained_orchestration_policy_sha256
native_helper_policy_sha256
retained_schema_sha256
case_set_sha256
fixture_profile_sha256
authority_registry_root_identity
fixture_root_identity
result_parent_identity
result_directory_derivation_rule
operator_wrapper_identity
operator_identity
single_process_declaration
single_attempt_declaration
real_executor_selector
fault_injection_disabled
host_identity
volume_identity
case_execution_order
selected_a6
source_identities
```

`result_directory_derivation_rule` must be the implementation default returned by `result_directory_derivation_rule_declaration()`. No override, substituted mapping, or caller-supplied alternative is authorized. Independent validation must verify that the declaration contains the implementation-default rule exactly.

Each item in `source_identities` must use the `SourceIdentityExpectation.as_payload()` shape:

```text
relative_path
checked_out_byte_sha256
checked_out_byte_length
git_blob_oid
```

The `source_identities` sequence must be complete and sorted by `relative_path` as the implementation declaration sorts it. The `case_execution_order` must be the implementation's native execution order for A1, A2, A3, A5. `selected_a6` must be false.

Required HEAD binding:

```text
expected_head: accepted invocation HEAD
expected_origin_main: accepted invocation HEAD
expected_branch: main
```

Independent validation must recompute the derived execution authorization identity and verify:

```text
derived execution authorization identity: not equal to any historical consumed-lane identity
derived result directory: not equal to any historical result directory
derived global authority entry: not equal to any historical authority entry
derived result directory: absent before preparation and invocation
derived global authority entry: absent before preparation and invocation
```

The wrapper does not fully recompute this derivation during `PREPARE_PATHS` candidate validation. This derivation requirement is governance-enforced and must be independently validated.

## 14. Repository and HEAD Bindings

The future input must preserve `REMEDIATION_ATTEMPT_HEAD_UNIQUENESS`.

Required R4 authorization-document binding:

```text
accepted authorization-document HEAD: b9219ca9dbc6bc7608f1aa2356f7f21874fcb524
same-HEAD repeat: PROHIBITED
later remediation attempt: requires a new committed and pushed governance baseline
true per-event identity: NOT AVAILABLE UNDER CURRENT SCHEMA
```

Repository-state-bound freshness must not be represented as a true event discriminator.

Supported sequencing model:

```text
Model 3 only
```

The wrapper compares `payload.repository_identity.head` against the live repository HEAD at validation time. Therefore every repository artifact that must exist before invocation must be committed and pushed before canonical-input preparation, including:

```text
active Layer-B governance decision
Layer-B post-commit identity record
Layer-C PREPARE_PATHS invocation authorization
Layer-C post-commit identity record
```

The accepted invocation HEAD is the repository HEAD after the final required pre-invocation governance commit, with:

```text
HEAD == origin/main
tracked tree clean
.git/index.lock absent
```

The canonical input must bind this accepted invocation HEAD in:

```text
repository_identity.head
retained_authorization.expected_head
retained_authorization.expected_origin_main
execution_authorization_identity_block.expected_head
execution_authorization_identity_block.expected_origin_main
```

From the final required pre-invocation governance commit through `PREPARE_PATHS` invocation, no commit of any kind is permitted. This window opens the moment the accepted invocation HEAD is established and closes only after invocation. It spans activation, preparation, any permitted retry, and independent validation of the candidate. This prohibition includes:

```text
review records
candidate findings
identity records
lifecycle records
documentation corrections
unrelated repository commits
```

Any intervening commit after accepted invocation HEAD establishment and before invocation invalidates the accepted invocation HEAD and all derived identities bound to it. The effect is:

```text
current activation: VOID
accepted invocation HEAD: RETIRED
current candidate, if one exists: RETIRED
Layer-B authority: RETIRED
further preparation: PROHIBITED
recovery: fresh committed and pushed Layer-B governance baseline required
```

Simply recomputing the canonical input against a new HEAD is not permitted under the existing Layer-B authority.

This R4 sequencing supersedes the intuitive ordering in the accepted Layer-A governance sequence only where required by the current wrapper's live-HEAD validation.

Rejected sequencing models:

```text
Model 1: unsupported because Layer-C commit after preparation changes HEAD
Model 2: unsupported because a future commit identity cannot be bound as live HEAD
Model 4: unsupported by current implementation and would require a code change
```

No implementation change is authorized.

## 15. Case Lock

The future input must select exactly:

```text
selected_cases: A1, A2, A3, A5
execution_order: A1, A2, A3, A5
```

The future input must prohibit:

```text
A4
A6
A7
A8
duplicate cases
case reordering
generic callable executor selectors
```

The implementation-enforced real executor selector is:

```text
REAL_EXISTING_ABSOLUTE_PATH_A1_A2_A3_A5_V0_1
```

## 16. Canonicalization and Duplicate-Key Rules

The future external input file must be canonical JSON bytes, not pretty-printed JSON and not JSON with a trailing newline.

Required canonicalization:

```text
UTF-8
no BOM
top-level exactly one JSON object
duplicate keys prohibited at every object level
non-finite JSON numbers prohibited
sort keys recursively
separators "," and ":"
ensure_ascii=false
allow_nan=false
raw file bytes exactly equal canonical_json_bytes(parsed_object)
```

Whole-file canonical JSON byte equality must be independently reproduced. Independent reproduction must parse the candidate with duplicate-key rejection, regenerate canonical JSON bytes from the parsed object, verify byte-for-byte equality with the file, and compute SHA-256 over the exact file bytes.

The candidate must contain no string equal to `UNAVAILABLE_UNTIL_COMMIT` and no string containing `placeholder` or `synthetic` in any case variation.

## 17. External Root and Path Constraints

The wrapper fixed roots are:

```text
authority_registry_root: C:\TORMENT\brainvision_authority\blocker2_s3b_v0_3
fixture_root: C:\TORMENT\brainvision_authoritative_fixture\blocker2_s3b_v0_3
result_parent: C:\TORMENT\brainvision_retained_results\blocker2_s3b_v0_3
```

These roots must be drive-qualified DOS paths, fixed-root, NTFS-compatible, non-reparse, outside the repository, not UNC paths, not device paths, not NT internal paths, and not volume GUID paths.

The external canonical input file is fixed exactly as:

```text
C:\TORMENT\brainvision_authoritative_inputs\blocker2_s3b_v0_3\r4_prepare_paths\r4_prepare_paths_authorization_input_v0_1.canonical.json
```

The selected directory is:

```text
C:\TORMENT\brainvision_authoritative_inputs\blocker2_s3b_v0_3\r4_prepare_paths\
```

The directory must be absolute, drive-qualified DOS, on a local fixed NTFS drive, outside the repository, not UNC, not a device path, not a volume-GUID path, and not a reparse point. The operator may create the directory before preparation if absent.

The selected file path itself must not exist before the authorized preparation event. The filename is governance-selected and must not embed the accepted HEAD or canonical-input SHA-256. Those identities are recorded after publication.

The external input path restriction and outside-repository requirement are governance-enforced, not wrapper-enforced. Input file freshness is operator-attested and independently validated.

Prohibited file operations:

```text
overwrite
append
edit in place
rename into selected path
copy into selected path
atomic replacement
replacement of any existing file
historical path reuse
```

## 18. Historical Non-Reuse

The future Layer-B decision must explicitly prohibit reuse of:

```text
historical authorization-document path
historical authorization-document identity
historical canonical-input bytes
historical canonical-input identity
historical execution-authorization identity
historical run identity
historical result-directory identity
historical result-directory path
historical global authority entry path
historical local gate path
historical run result path
historical retained completion path
```

The future input must be proven fresh by:

```text
using a new R4-specific external path
deriving bytes from current committed wrapper and retained schema code
deriving source and document identity inventories from the current checked-out files
binding the accepted Layer-A authorization-document five-field identity
recording the candidate input byte count and SHA-256 after publication
confirming the candidate input SHA-256 differs from every known historical canonical input SHA-256
confirming the authorization_input_identity differs from every known historical canonical input identity
rejecting copied or edited historical input files as invalid provenance
```

## 19. Downstream-Identity Prohibitions

Layer B may compute schema-required candidate payload fields, including the path model and inactive execution-authorization identity block, because the wrapper schema requires them.

Layer B must not create, activate, or consume downstream effects. The future Layer-B decision and candidate input must not include or imply:

```text
PREPARE_PATHS invocation result
PREFLIGHT_ONLY result
EXECUTE_EXACT_SINGLE_RUN result
ACTIVE invocation authority
created global authority entry
created local gate
created run result
created retained completion marker
execution stdout or stderr evidence
runtime consumption evidence
live production integration
```

Stale downstream identities from earlier successor-lane attempts are prohibited.

## 20. Single-Use Semantics

An active Layer-B decision may authorize at most one preparation event that publishes one candidate canonical JSON file.

Publication is the moment the first byte is written to the selected canonical-input path.

Preparation must write directly to the exact selected path. Temporary-file publication workflows are prohibited, including:

```text
write elsewhere then rename
write elsewhere then copy
atomic replace
editor swap-file replacement
```

Layer-B authority is consumed or terminated by the earliest of:

```text
successful publication of the single candidate input
publication of any candidate bytes at the selected path
candidate validation rejection after publication
operator retirement of the Layer-B authority
superseding governance decision
discovery that repository or document identities no longer match the accepted bindings
discovery that the selected external path is not fresh or safe
```

After consumption, retirement, or supersession, the Layer-B decision must transition to a historical non-reusable state by a committed and pushed lifecycle record before any new preparation attempt is authorized.

## 21. Failure and Retry Semantics

Consumption outcomes are defined exactly:

```text
serialization failure before any selected-path write: NOT CONSUMED
validation failure before any selected-path write: NOT CONSUMED
operator interruption before any selected-path write: NOT CONSUMED
unexpected exception before any selected-path write: NOT CONSUMED
candidate generated only in memory and rejected: NOT CONSUMED
partial or truncated selected-path write: CONSUMED
write failure after any byte reached selected path: CONSUMED
successful write followed by failed identity reporting: CONSUMED
published candidate later rejected: CONSUMED
selected path existed before preparation: CONSUMED AND EVENT VOID
```

Maximum retries:

```text
one
```

A retry is permitted only after a genuine `NOT CONSUMED` result, in the same operator session, with a failure record created before retry.

The failure record must state:

```text
failure classification
timestamp
selected-path pre-existence result
whether any bytes reached selected path
operator environment declaration
```

The failure record required before a retry must not be committed to the repository while the commit-free window of Section 14 is open. It must be retained as an external operator artifact under the directory selected in Section 17, and committed only after `PREPARE_PATHS` invocation, together with the independent validation record.

If any commit occurs after the accepted invocation HEAD is established and before invocation, including a failure record, the activation is void. The accepted invocation HEAD must be re-established, the Layer-B authority must be retired, and a fresh committed and pushed Layer-B baseline is required before any further preparation attempt.

This rule applies to:

```text
retry failure records
independent validation records
candidate identity reports
operator notes intended for later repository commitment
any unrelated repository work
```

External retention during the commit-free window does not itself authorize creation of the canonical input or invocation of the wrapper.

A second `NOT CONSUMED` failure retires the Layer-B authority and requires a fresh committed and pushed Layer-B baseline.

If any candidate bytes are published, the event counts as the single preparation event. The candidate must not be edited in place to repair validation defects.

If a candidate input is generated and later rejected during independent validation, that candidate becomes a rejected historical artifact. Correction requires a fresh committed and pushed Layer-B governance baseline, unless a later accepted governance design explicitly creates a narrower correction path.

Published candidates, including partial, failed, or rejected published candidates, remain retained historical evidence. A published candidate must never be:

```text
edited
deleted
moved
renamed
truncated
cleaned up
```

## 22. Validation Requirements

Before any future input is accepted as prepared, independent validation must verify:

```text
file path is the exact selected external path
file did not exist before the authorized preparation event
file is UTF-8 without BOM
file bytes are canonical JSON and contain no trailing newline
duplicate keys are rejected
authorization_input_identity recomputes exactly
authorization_input_identity self-excludes authorization_input_identity
execution_authorization_document_identity has exactly five fields
execution_authorization_document_identity matches the current checked-out authorization document bytes
document byte count and line-ending representation are separately recorded
runtime_declaration_identities match current implementation-derived identities
path_model exactly matches the derivation from execution_authorization_identity
fixed roots are outside the repository and not reparse paths
result_directory is absent
global_authority_entry_path is absent
case_set selects exactly A1, A2, A3, A5 in that order
A6 is false
forbidden cases are absent
real_executor_selector is exact
fault_injection_disabled is true
repository_identity matches live branch, HEAD, and origin/main for the selected validation state
HEAD equals origin/main
.git/index.lock is absent
no placeholder or synthetic sentinel strings exist anywhere in the payload
no historical canonical input bytes or identities are reused
```

Implementation case-lock defence is verified by inspecting the current wrapper validation code and the committed wrapper tests that reject wrong case order, A6 selection, generic executor selectors, wrong authorization status for execute, noncanonical JSON, duplicate keys, missing or unknown fields, placeholder values, stale document identities, and path-model mismatches.

## 23. Explicit Non-Implications

This draft does not imply:

```text
Layer-B active authority
canonical input prepared
canonical input valid
PREPARE_PATHS authorized
PREPARE_PATHS invoked
PREFLIGHT_ONLY authorized
PREFLIGHT_ONLY invoked
EXECUTE_EXACT_SINGLE_RUN authorized
EXECUTE_EXACT_SINGLE_RUN invoked
execution authority created
execution authority consumed
historical authority reusable
production integration permitted
BLOCKER-2 closed
BLOCKER-4 active
```

Downstream Layer-C design constraint:

Because Layer C must be committed before the canonical input exists, Layer C cannot bind:

```text
canonical-input SHA-256
canonical-input byte count
canonical-input declaration identity
any other post-publication candidate identity
```

Layer C may bind:

```text
the exact selected external path
the accepted invocation HEAD
the governing Layer-B identities
the required schema and constraints
the invocation mode
the required validation and capture procedure
```

Actual canonical-input identities may only be recorded externally before invocation and committed after invocation.

Forward-looking non-implication reserved for later governance:

```text
PREFLIGHT_ONLY and EXECUTE_EXACT_SINGLE_RUN will later require an ACTIVE authorization-document state and new governance identities.
The current Layer-A PREPARED_NOT_ACTIVE identity does not grant or satisfy those later modes.
```

## 24. Recommended Next Governance Step

The next governance step is independent review of this draft.

If accepted, the next implementation order should create an active-ready Layer-B decision document from this draft, include exactly one canonical embedded declaration, commit and push it, create a separate post-commit identity record, commit and push that record, and then create and identity-bind the Layer-C `PREPARE_PATHS` invocation authorization before Layer-B preparation authority is activated.

No unresolved activation blocker remains inside the Layer-B design itself after the corrections in this draft. The remaining downstream questions are reserved for Layer C: the exact Layer-C invocation authorization content, its post-commit identity record, and the final accepted invocation HEAD produced after those commits.

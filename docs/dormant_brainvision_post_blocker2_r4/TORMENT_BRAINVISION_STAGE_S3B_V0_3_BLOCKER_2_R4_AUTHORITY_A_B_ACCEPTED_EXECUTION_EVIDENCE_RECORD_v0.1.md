# TORMENT Brainvision Stage S3B v0.3 BLOCKER-2 R4 Authority-A/B Accepted Execution Evidence Record v0.1

## 1. Record Status

This document is an uncommitted repository documentation draft recording the accepted BLOCKER-2 R4 Authority-A/Authority-B execution evidence.

Record artifact status:

- `DRAFT ONLY`
- `NOT COMMITTED`
- `NOT PUSHED`
- `NOT POST-COMMIT VERIFIED`

This document is evidence documentation only. It is not Authority C activation, not Authority D activation, not Authority E activation, not canonical-input preparation, not canonical-input publication, not a PREPARE_PATHS invocation, not PREFLIGHT_ONLY, not EXECUTE_EXACT_SINGLE_RUN, not another A/B orchestrator invocation, not cleanup, not replacement, not deletion, not a corrected-window closure declaration, and not BLOCKER-4 commencement.

This document does not modify production TORMENT memory or kernel code.

## 2. Repository and Invocation Binding

Accepted repository branch:

```text
main
```

Accepted invocation HEAD:

```text
1f915e29119cd58ea39e8cf355f7364118c71043
```

Local remote-tracking reference observed at pre-opening verification:

```text
refs/remotes/origin/main:
1f915e29119cd58ea39e8cf355f7364118c71043
```

The `refs/remotes/origin/main` value above is the local remote-tracking reference observed during the accepted pre-opening verification. It is not an independently queried live remote branch state. No fetch was performed as part of the accepted pre-opening verification.

## 3. Accepted Execution Result

The accepted same-process Authority-A/Authority-B orchestrator process result was:

```text
process exit:
0

accepted:
true

classification:
CORRECTED_PATH_CREATION_EVIDENCE_ACCEPTED

accepted_invocation_head:
1f915e29119cd58ea39e8cf355f7364118c71043

cli_fixed_path_binding:
true

operator_assertions_do_not_activate_authority:
true

machine_verified_governance_assertions:
false
```

The CLI operator-assertion flags asserted the already-established operator governance state. They did not themselves create authority.

## 4. Authority-A Result

Authority-A returned a publishable evidence body candidate:

```text
classification:
CORRECTED_PATH_CREATION_EVIDENCE_READY_FOR_PUBLICATION

classification_kind:
DERIVED_NON_TERMINAL

terminal:
false

sequence_terminal:
false

contact_started:
true

opportunity_consumed:
true

mutation_succeeded_count:
3

required_authority_gate_satisfied:
true

execution_mode:
AUTHORITATIVE_DEFAULT_ADAPTERS
```

Authority-A body identity:

```json
{
  "body_byte_count": 24287,
  "body_sha256": "7d7b0fee5db0bb7fda57db0c1eddbb6f93cd3f51aeeff3656395d7a4f5342140",
  "identity_scope": "canonical evidence_body bytes only",
  "whole_record_identity_stored_inside_record": false
}
```

This identity covers only the canonical `evidence_body` bytes. It is not the whole evidence-record identity.

## 5. Authority-A Ordered Directory Mutations

Authority-A recorded three successful ordered directory creations.

### 5.1 Operation 1

Exact absolute path:

```text
C:\TORMENT\brainvision_authoritative_inputs
```

Accepted evidence summary:

- strict ordinal order: `1`
- target was positively absent before creation
- `os.mkdir` returned success
- target was present afterward
- target was an ordinary directory
- target was not a reparse point
- drive was local fixed
- filesystem was NTFS
- volume and directory file identities were observed
- immediate parent identity continuity was observed
- repository pre-state remained bound to branch `main` and accepted HEAD `1f915e29119cd58ea39e8cf355f7364118c71043`
- `.git/index.lock` was absent
- no staged, tracked-modified, or unmerged entries existed
- the only untracked entry was the known inert design draft
- unexpected intermediate creation check passed
- no custom seams were present
- authoritative default adapters were used

### 5.2 Operation 2

Exact absolute path:

```text
C:\TORMENT\brainvision_authoritative_inputs\blocker2_s3b_v0_3
```

Accepted evidence summary:

- strict ordinal order: `2`
- target was positively absent before creation
- `os.mkdir` returned success
- target was present afterward
- target was an ordinary directory
- target was not a reparse point
- drive was local fixed
- filesystem was NTFS
- volume and directory file identities were observed
- immediate parent identity continuity was observed
- repository pre-state remained bound to branch `main` and accepted HEAD `1f915e29119cd58ea39e8cf355f7364118c71043`
- `.git/index.lock` was absent
- no staged, tracked-modified, or unmerged entries existed
- the only untracked entry was the known inert design draft
- unexpected intermediate creation check passed
- no custom seams were present
- authoritative default adapters were used

### 5.3 Operation 3

Exact absolute path:

```text
C:\TORMENT\brainvision_authoritative_inputs\blocker2_s3b_v0_3\r4_prepare_paths
```

Accepted evidence summary:

- strict ordinal order: `3`
- target was positively absent before creation
- `os.mkdir` returned success
- target was present afterward
- target was an ordinary directory
- target was not a reparse point
- drive was local fixed
- filesystem was NTFS
- volume and directory file identities were observed
- immediate parent identity continuity was observed
- repository pre-state remained bound to branch `main` and accepted HEAD `1f915e29119cd58ea39e8cf355f7364118c71043`
- `.git/index.lock` was absent
- no staged, tracked-modified, or unmerged entries existed
- the only untracked entry was the known inert design draft
- unexpected intermediate creation check passed
- no custom seams were present
- authoritative default adapters were used

The accepted record limits held Windows handles to evidence continuity. It does not claim that the held handles prevented rename or deletion.

## 6. Authority-B Result

Authority-B accepted the evidence record:

```text
classification:
CORRECTED_PATH_CREATION_EVIDENCE_ACCEPTED

accepted:
true

detail:
record reread, validation, and external identity completed

authority_c_active:
false

authority_d_active:
false

authority_e_active:
false
```

Publication result:

```text
classification:
AUTHORITY_B_RECORD_DURABLY_PUBLISHED

accepted_for_validation:
true

contact_started:
true

create_new_attempted:
true

write_attempt_count:
1

handle_closed:
true

byte_count:
37582
```

Evidence-record path:

```text
C:\TORMENT\brainvision_authoritative_inputs\blocker2_s3b_v0_3\r4_prepare_paths\r4_prepare_paths_path_creation_evidence_record_v0_1.canonical.json
```

Intended and validated whole-record SHA-256:

```text
4129bd85d86cc8ee38b5ccf5f29453a8352306b4c3dbface89b4fd03fcb86f07
```

## 7. Directory Durability Result

Directory durability was bound as:

```text
status:
DIRECTORY_DURABILITY_CONFIRMED

operation:
win32-createfilew-flushfilebuffers-directory-entry-v0.1

platform:
windows

target_role:
ARTIFACT_PARENT_DIRECTORY
```

Adapter identity:

```text
durable_evidence_windows_adapter_v0_3.Win32DirectoryDurabilityAdapter
```

Policy identity:

```json
{
  "policy_schema_identity": "durable-evidence-windows-directory-durability-policy-v0.1",
  "policy_sha256": "491ec6dc5704d26f97b58f155434e8f81fe424ee3f9bba997f6ed800298cbba4"
}
```

Validation profile:

```text
windows-10-11-local-fixed-ntfs-pytest-tmp-directory-v0.1
```

This durability result is not generalized beyond the stated Windows/local-fixed-NTFS validation profile.

## 8. Record Validation and Whole-Record Identity

Record validation result:

```text
validation accepted:
true

stored record schema:
torment.brainvision.blocker2.r4.corrected_path_creation_evidence_record.v0.1

canonical_input_status:
NOT_PREPARED_NOT_PUBLISHED_AUTHORITIES_C_D_INACTIVE

whole_record_byte_count:
37582

whole_record_sha256:
4129bd85d86cc8ee38b5ccf5f29453a8352306b4c3dbface89b4fd03fcb86f07
```

The whole-record byte count and SHA-256 appeared and agreed at all three required result locations:

1. top-level orchestrator result
2. `authority_b_result`
3. `authority_b_result.validation_result`

The whole-record identity was calculated externally from the exact reread bytes. The whole-record identity is not stored inside the evidence record.

Authority-A body identity and Authority-B whole-record identity are distinct:

- Authority-A body identity covers only canonical `evidence_body` bytes
- Authority-B whole-record identity covers the externally reread canonical evidence-record bytes

## 9. Canonical-Input Absence

Canonical-input path:

```text
C:\TORMENT\brainvision_authoritative_inputs\blocker2_s3b_v0_3\r4_prepare_paths\r4_prepare_paths_authorization_input_v0_1.canonical.json
```

Accepted absence result:

```text
canonical-input path positively absent:
true
```

Canonical input was not prepared. Canonical input was not published. Mutation 5 did not occur. Authority C was not activated. Authority D was not activated. Authority E was not activated.

## 10. Mutation Accounting

The total governed mutation count is an operator derivation from accepted result facts:

```text
3 successful Authority-A directory creations
+
1 accepted Authority-B create-new evidence-record publication
=
4 governed mutations
```

The result does not contain an explicit total-mutation field. Mutation 5 remained unauthorized and did not occur.

## 11. Post-Success Governance Posture

The accepted result preserves this post-result posture:

```text
Authority A:
successful and opportunity consumed for its one-shot operation

Authority B:
evidence accepted

Authority C:
INACTIVE

Authority D:
INACTIVE

Authority E:
INACTIVE

execution authority:
NOT CREATED
NOT CONSUMED

FORMAL_HOLD:
ACTIVE

BLOCKER-2:
OPEN

BLOCKER-4:
INACTIVE

corrected commit-free window:
REMAINS OPEN
```

This document does not describe the corrected commit-free window as closed and does not create a successful-window closure declaration. Successful closure remains reserved for later successful canonical-input publication and verification under Authority D.

## 12. Scope and Non-Claims

This record binds the accepted governed A/B execution and its evidence path only.

It does not claim:

- BLOCKER-2 closure
- BLOCKER-4 activation
- Authority C activation
- canonical-input preparation
- canonical-input publication
- PREPARE_PATHS invocation
- Brainvision scientific validation
- live LLM usefulness
- production readiness
- security of unrelated systems
- production TORMENT memory or kernel modification

This record is evidence-based, fail-closed, and limited to the accepted Authority-A/Authority-B execution result bound above.

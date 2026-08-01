# TORMENT Brainvision Stage S3B v0.3 BLOCKER-2 R4 Authority-C Implementation Opening Acceptance For Issuance Non-Commit Record Draft v0.1

## 1. Document Status

```text
classification:
AUTHORITY_C_IMPLEMENTATION_OPENING_ACCEPTANCE_FOR_ISSUANCE_RECORD_DRAFT_PREPARED_FOR_INDEPENDENT_REVIEW

document state:
DRAFT ONLY
NOT ISSUED
NOT ACTIVE
NOT COMMITTED
NOT PUSHED

record operation:
ACCEPTANCE-FOR-ISSUANCE RECORD PREPARATION ONLY
```

ACCEPTANCE FOR ISSUANCE DOES NOT ISSUE THE DECLARATION.

ACCEPTANCE FOR ISSUANCE DOES NOT AUTHORIZE IMPLEMENTATION CONTACT.

This record draft does not open the implementation window, suspend the corrected
commit-free window, activate Authority C, begin implementation contact, consume
the implementation opportunity, stage, commit, or push.

## 2. Schema And Operation

```text
schema:
torment.brainvision.blocker2.r4.authority_c.implementation_opening_acceptance_for_issuance_non_commit_record_draft.v0.1

operation_label:
AUTHORITY_C_IMPLEMENTATION_OPENING_ACCEPTANCE_FOR_ISSUANCE_NON_COMMIT_RECORD_DRAFT

record_classification:
AUTHORITY_C_IMPLEMENTATION_OPENING_ACCEPTANCE_FOR_ISSUANCE_RECORD_DRAFT_PREPARED_FOR_INDEPENDENT_REVIEW
```

## 3. Accepted Declaration Identity

The acceptance applies only to the exact frozen declaration bytes below.

```text
accepted_declaration_path:
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_AUTHORITY_C_IMPLEMENTATION_OPENING_NON_COMMIT_DECLARATION_DRAFT_v0.1.md

accepted_declaration_byte_count:
20088

accepted_declaration_sha256:
76afe53c19b1dd1115732c7835c61743eed2975e1cc18d4ba6c99f9836dec6b7

accepted_declaration_line_count:
937

accepted_declaration_lf_count:
937

accepted_declaration_cr_count:
0

accepted_declaration_crlf_count:
0

accepted_declaration_bom:
absent

accepted_declaration_final_newline:
present
```

Any byte change invalidates this acceptance-for-issuance record and requires a
new frozen identity and fresh independent review.

## 4. Independent Review Classification

```text
independent_review_classification:
B. AUTHORITY_C_IMPLEMENTATION_OPENING_DECLARATION_CORRECTED_DRAFT_ACCEPTED_WITH_NON_BLOCKING_CLARIFICATIONS

review_determination:
the exact frozen draft may proceed unchanged
no blocking findings remain
no regression was introduced
F-01 through F-10 are resolved
F-11 through F-13 do not require a new frozen identity
```

The review acceptance is interpretive and identity-bound. It does not silently
amend the accepted declaration bytes.

## 5. Controlling Identity Bindings

Implementation authorization:

```text
path:
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_AUTHORITY_C_IMPLEMENTATION_NON_COMMIT_AUTHORIZATION_DESIGN_v0.1.md

SHA-256:
2a06ee4aae319d72e3447195b1adbba8703ea6d23a49ae4fec6d08460e2e749a

byte count:
48193

line count:
1849
```

Invocation-form design:

```text
path:
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_AUTHORITY_C_INVOCATION_FORM_DESIGN_v0.1.md

SHA-256:
bde299d389572c8cd25d2a0e9a7aa60f56009edd8cf96311f2c1abc100749f58

byte count:
59456
```

Authority-C activation declaration draft:

```text
path:
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_AUTHORITY_C_NON_COMMIT_ACTIVATION_DECLARATION_DRAFT_v0.1.md

SHA-256:
2c2500e624d77c70d33a6c5d29db6f5f04442fbc6a75a5930e90b89f0df64750

byte count:
22726

status:
DRAFT ONLY
NOT ISSUED
```

Accepted invocation baseline:

```text
branch:
main

accepted invocation HEAD:
1f915e29119cd58ea39e8cf355f7364118c71043
```

## 6. Accepted Implementation Surface

Exact authorised future implementation surface:

```text
research/brainvision/blocker2_r4_authority_c_candidate_v0_1.py
research/brainvision/run_blocker2_authoritative_retained_single_run_v0_1.py
research/brainvision/test_blocker2_r4_authority_c_candidate_v0_1.py
```

The runner modification is limited to extracting or exposing the shared
mode-independent validation core, making the runner-facing validator delegate
to that core, retaining one shared validation truth, and not copying shared
validation logic.

No other source or test modification is accepted.

## 7. Accepted Prohibited Surface

The accepted declaration prohibits modification or contact for:

```text
research/brainvision/blocker2_retained_absolute_path_control_v0_1.py
research/brainvision/blocker2_r4_ordered_directory_creation_helper_v0_1.py
research/brainvision/blocker2_r4_authority_b_evidence_publisher_v0_1.py
research/brainvision/blocker2_r4_ab_orchestrator_v0_1.py
AUTHORIZED_SURFACE_PATHS
torment_service/
torment_service/kernel/
production service code
live memory surfaces
prompt surfaces
action surfaces
autonomy surfaces
cognition surfaces
truth-selection surfaces
governed runner invocation
Authority-C activation
Authority-D activation
Authority-E activation
candidate payload construction
candidate byte construction
canonical-input path contact
staging
Git-index modification
commit
push
```

Any need for an additional source or test file requires STOP, no expansion by
implementer discretion, and return for governance review.

## 8. Accepted Corrected-Window State Machine

Accepted window model:

```text
before valid issuance:
OPEN

after valid non-commit issuance, frozen bytes, external byte count, external
SHA-256, and issued identity verification:
SUSPENDED_FOR_BOUNDED_IMPLEMENTATION

after source/test edit closure on successful sequence:
CLOSED_TO_FURTHER_EDITS
AWAITING_RESTORATION_DECLARATION

after any non-success terminal sequence after issuance:
AWAITING_INDEPENDENT_DISPOSITION
```

`SUSPENDED_FOR_BOUNDED_IMPLEMENTATION` is active and transitional only. It is
never terminal. `AWAITING_INDEPENDENT_DISPOSITION` is non-terminal and requires
separately governed independent disposition. No automatic retry is permitted.

## 9. Accepted Non-Self-Reference Properties

The accepted declaration:

```text
does not contain its own SHA-256
contains no whole-declaration identity field
contains no computed opportunity-key value
requires external declaration identity computation after issuance and byte
freezing
forbids post-hash rewrite
```

The displayed opportunity-key construction is explanatory only. The future key
is computed externally after valid issuance and external identity capture.

## 10. Accepted Git And Repository Protections

Accepted protections include:

```text
GIT_OPTIONAL_LOCKS=0
git --no-optional-locks
no network fetch required or authorized
.git/index.lock absent
staged entries none
tracked deletions none
unmerged entries none
genuine tracked diff none
exact expected R4 Markdown governance inventory at issuance
unexpected untracked entries require STOP
no repository __pycache__
no repository .pyc
no repository .pytest_cache
Git-index mutation prohibited
staging prohibited
commit prohibited
push prohibited
```

The declaration may later be issued only if its exact identity is re-verified
and every issuance-time repository prerequisite passes.

## 11. Accepted Result-Write And Restoration/Disposition Model

The accepted declaration authorizes exactly one future governance-result
document write after source/test edit closure:

```text
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_AUTHORITY_C_IMPLEMENTATION_RESULT_v0.1.md
```

That result document is governance Markdown, not source, not a test, outside
the bounded three-file implementation surface, admitted by the R4 Markdown
governance pattern, without a whole-document identity field, and externally
identified after byte freezing.

Successful sequence:

```text
restoration declaration
```

Every other post-issuance terminal sequence:

```text
independent disposition
```

The applicable restoration or independent-disposition governance record later
binds the external result identity if such a result document exists on that
path.

## 12. Non-Blocking Review Clarifications

F-11:

```text
Sections 7 and 16 contain under-qualified references to the restoration
declaration, while Sections 10 and 15 provide the controlling branch-aware
rule:

successful sequence:
restoration declaration

every other post-issuance terminal sequence:
independent disposition
```

The controlling branch-aware reading governs. No change to the accepted bytes
is required.

F-12:

```text
governed candidate construction
test-environment contamination
implementation-result write failure
```

These are governed in their dedicated sections even though they are not
duplicated in the consolidated fail-closed list. No byte correction is
required.

F-13:

```text
AWAITING_RESTORATION_DECLARATION
or
AWAITING_INDEPENDENT_DISPOSITION
```

These lifecycle entries are branches, not consecutive mandatory states. No
byte correction is required.

These notes are interpretive review records only. They do not silently amend
the accepted declaration.

## 13. Current Governance State

```text
opening declaration:
NOT ISSUED

implementation:
NOT AUTHORIZED TO START

implementation contact:
NOT STARTED

implementation opportunity:
NOT CONSUMED

corrected commit-free window:
OPEN

Authority C:
INACTIVE

Authority D:
INACTIVE

Authority E:
INACTIVE

canonical-input path:
NOT CONTACTED

FORMAL_HOLD:
ACTIVE

BLOCKER-2:
OPEN

BLOCKER-4:
INACTIVE
```

## 14. Acceptance Boundary

This record is draft-only and non-commit. It records the independent review
classification for later non-commit issuance consideration only.

It does not:

```text
issue the declaration
open the implementation window
suspend the corrected commit-free window
begin implementation contact
consume the implementation opportunity
compute an opportunity-key value
modify source
modify tests
run implementation tests
invoke any governed runner mode
activate Authority C/D/E
construct candidate payloads or bytes
contact the canonical-input path
prepare or publish canonical input
modify .git/index
stage
commit
push
```

## 15. Formatting

```text
UTF-8
LF only
no BOM
final newline present
```

This draft contains no self-identity field for its own complete bytes and no
computed implementation-opportunity-key value.

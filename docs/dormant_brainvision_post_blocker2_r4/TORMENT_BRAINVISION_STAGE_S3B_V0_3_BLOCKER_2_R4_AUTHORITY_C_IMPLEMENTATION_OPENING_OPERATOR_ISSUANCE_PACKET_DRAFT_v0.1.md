# TORMENT Brainvision Stage S3B v0.3 BLOCKER-2 R4 Authority-C Implementation Opening Operator Issuance Packet Draft v0.1

## 1. Document Status

```text
classification:
AUTHORITY_C_IMPLEMENTATION_OPENING_OPERATOR_ISSUANCE_PACKET_CORRECTED_DRAFT_PREPARED_FOR_INDEPENDENT_REVIEW

document state:
DRAFT ONLY
NOT EXECUTED
NOT ISSUED
NOT ACTIVE
NOT COMMITTED
NOT PUSHED

operator:
Hilmir
```

This packet prepares a future operator act for Hilmir. It does not perform
that act.

It does not issue the declaration, open the implementation window, suspend the
corrected commit-free window, begin implementation contact, consume the
implementation opportunity, compute an opportunity-key value, activate
Authority C/D/E, stage, commit, or push.

## 2. Schema And Operation

```text
schema:
torment.brainvision.blocker2.r4.authority_c.implementation_opening_operator_issuance_packet_draft.v0.1

operation_label:
AUTHORITY_C_IMPLEMENTATION_OPENING_OPERATOR_ISSUANCE_PACKET_DRAFT

packet_classification:
AUTHORITY_C_IMPLEMENTATION_OPENING_OPERATOR_ISSUANCE_PACKET_CORRECTED_DRAFT_PREPARED_FOR_INDEPENDENT_REVIEW
```

## 3. Future Issuance Preconditions

All checks in this packet must occur before issuance.

Read-only repository verification must use:

```text
set GIT_OPTIONAL_LOCKS=0
git --no-optional-locks ...
```

No network fetch is required or authorized.

Repository baseline to verify:

```text
repository root:
C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric

branch:
main

HEAD:
1f915e29119cd58ea39e8cf355f7364118c71043

local origin/main:
1f915e29119cd58ea39e8cf355f7364118c71043

.git/index.lock:
ABSENT

staged entries:
NONE

tracked deletions:
NONE

unmerged entries:
NONE

filtered Git apparent tracked diff:
NONE

repository-wide raw-byte CRLF safety proof:
REQUIRED

decisive issuance condition:
substantive exceptions: 0
missing or unreadable tracked files: 0

currently accepted evidence to re-prove at issuance:
tracked files: 1339
raw byte-identical files: 1036
CRLF-only raw-different files: 303
substantive exceptions: 0
missing or unreadable: 0

unexpected untracked entries:
NONE

new repository __pycache__:
NONE

new repository .pyc:
NONE

repository .pytest_cache:
ABSENT

governed external path state:
ADMISSIBLE

Authority C:
INACTIVE

Authority D:
INACTIVE

Authority E:
INACTIVE

canonical-input path:
NOT CONTACTED
```

Observation-vantage clarification:

```text
git status and git diff output may differ depending on core.autocrlf and
filter vantage

a filtered Windows view may report 0 apparent modifications

an unfiltered raw view may report 303 CRLF-only differences

neither count alone is the safety proof
```

Issuance-time CRLF proof procedure:

```text
1. Enumerate every tracked file at HEAD.

2. Read each existing working-tree file as raw bytes without Git clean filters.

3. Compare raw working-tree bytes against the exact HEAD blob bytes.

4. For each raw-different file, normalize only CRLF byte pairs to LF in memory.

5. Compute the Git blob identity of the normalized bytes.

6. Require the normalized identity to equal the exact HEAD blob OID.

7. Require:
   missing or unreadable tracked files == 0

8. Require:
   substantive exceptions == 0
```

The check must perform no repository write. It must not rewrite line endings,
modify `.git/index`, or invoke checkout, restore, reset, add, update-index,
clean, fetch, pull, or any command that alters repository state.

A changed benign raw-different or CRLF-only count may not be accepted
automatically. It must be explained and independently dispositioned before
issuance. The decisive issuance condition is zero substantive exceptions and
zero missing or unreadable tracked files.

## 4. Future Issuance-Time Governance Inventory

Admitting pattern:

```text
?? docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_*.md
```

The exact R4 governance Markdown inventory must be captured at issuance time.
This packet intentionally does not freeze a guessed future inventory as an
unconditional current fact.

Any unexpected untracked entry requires STOP.

## 5. Declaration Identity Re-Verification

Before issuance, directly verify the authoritative Windows checkout bytes of:

```text
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_AUTHORITY_C_IMPLEMENTATION_OPENING_NON_COMMIT_DECLARATION_DRAFT_v0.1.md
```

Expected identity:

```text
byte count:
20088

SHA-256:
76afe53c19b1dd1115732c7835c61743eed2975e1cc18d4ba6c99f9836dec6b7

line count:
937

LF count:
937

CR count:
0

CRLF count:
0

BOM:
absent

final newline:
present
```

Any mismatch requires STOP.

Do not trust stale staged, mounted, copied, or cached representations. The
identity must be computed against the authoritative Windows checkout bytes.

## 6. Controlling Before-Identities

Runner:

```text
path:
research/brainvision/run_blocker2_authoritative_retained_single_run_v0_1.py

Git blob OID:
79d0c89575919c8506c8b9f1278efd5d63b1e813

checked-out byte SHA-256:
c61de2f7829e3eb2bb938701f98bbafe54f09f03dab8abd718d421a81b56e976

checked-out byte length:
46788
```

Retained-control source:

```text
path:
research/brainvision/blocker2_retained_absolute_path_control_v0_1.py

Git blob OID:
1779715ed17fffe3a927d24eb445eec51f3d42d6

checked-out byte SHA-256:
dc4a6e3f1169c33a2379c3506d107893cb8a48c977300c22bda14db0bf19e3d5

checked-out byte length:
144698
```

Any mismatch requires STOP.

The retained-control source remains reference-only and byte-identical.

## 7. Operator-Window Interpretation Gate

Future unresolved operator decision:

```text
Has the operator-window interpretation been independently accepted for issuance?
```

Permitted responses:

```text
YES - proceed with the separately explicit non-commit issuance act

NO - do not issue; corrected commit-free window remains OPEN; formal Layer-C
closure is required; a new accepted invocation HEAD must be established

UNKNOWN - STOP; do not issue
```

This packet preparation task does not answer this gate for Hilmir.

## 8. Prepared Future Issuance Statement

```text
PREPARED ONLY
NOT ISSUED
```

Prepared future operator statement:

```text
I, Hilmir, acting as authoritative Windows operator, issue the Authority-C
implementation-opening declaration as a non-commit operator declaration for one
one-shot bounded implementation opening only after all issuance-time checks have
passed.

accepted declaration path:
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_AUTHORITY_C_IMPLEMENTATION_OPENING_NON_COMMIT_DECLARATION_DRAFT_v0.1.md

accepted declaration byte count:
20088

accepted declaration SHA-256:
76afe53c19b1dd1115732c7835c61743eed2975e1cc18d4ba6c99f9836dec6b7

accepted invocation HEAD:
1f915e29119cd58ea39e8cf355f7364118c71043

branch:
main

issuance-time checks:
SUCCESSFULLY COMPLETED

independent acceptance-for-issuance result:
B. AUTHORITY_C_IMPLEMENTATION_OPENING_DECLARATION_CORRECTED_DRAFT_ACCEPTED_WITH_NON_BLOCKING_CLARIFICATIONS

operator-window interpretation:
ACCEPTED FOR ISSUANCE

issuance:
ISSUED_NON_COMMIT

bounded implementation opening:
ONE-SHOT

THIS ISSUANCE DOES NOT ACTIVATE AUTHORITY C

corrected commit-free window transitions from:
OPEN

to:
SUSPENDED_FOR_BOUNDED_IMPLEMENTATION

because all required issuance and identity checks have passed.

implementation contact:
NOT STARTED

implementation opportunity:
NOT CONSUMED
```

Implementation contact has not begun in this prepared statement. The
implementation opportunity has not been consumed. Those transitions occur only
immediately before the first authorized repository source/test write and are
recorded externally.

## 9. Issuance-Time External Identity Record

Immediately after valid future issuance, record externally:

```text
implementation_opening_declaration_path:
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_AUTHORITY_C_IMPLEMENTATION_OPENING_NON_COMMIT_DECLARATION_DRAFT_v0.1.md

implementation_opening_declaration_byte_count:
20088

implementation_opening_declaration_sha256:
76afe53c19b1dd1115732c7835c61743eed2975e1cc18d4ba6c99f9836dec6b7

accepted_invocation_head:
1f915e29119cd58ea39e8cf355f7364118c71043

branch:
main

issuance_timestamp:
<FUTURE_OPERATOR_VALUE>

issuance_operator:
Hilmir

issuance_state:
ISSUED_NON_COMMIT
```

This evidence must be held outside the repository working tree.

## 10. External Opportunity-Key Computation

After valid issuance and external identity capture only, compute externally:

```text
implementation_opportunity_key =
SHA-256(
  canonical_json_bytes(
    {
      "schema":
        "torment.brainvision.blocker2.r4.authority_c.implementation_opportunity_key.v0.1",

      "implementation_authorisation_sha256":
        "2a06ee4aae319d72e3447195b1adbba8703ea6d23a49ae4fec6d08460e2e749a",

      "implementation_opening_declaration_sha256":
        "76afe53c19b1dd1115732c7835c61743eed2975e1cc18d4ba6c99f9836dec6b7",

      "accepted_invocation_head":
        "1f915e29119cd58ea39e8cf355f7364118c71043",

      "authorised_new_files": [
        "research/brainvision/blocker2_r4_authority_c_candidate_v0_1.py",
        "research/brainvision/test_blocker2_r4_authority_c_candidate_v0_1.py"
      ],

      "authorised_modified_files": [
        "research/brainvision/run_blocker2_authoritative_retained_single_run_v0_1.py"
      ]
    }
  )
)
```

Canonicalization:

```text
UTF-8
no BOM
sorted mapping keys
compact separators
repository-relative POSIX paths
case-sensitive exact spelling
file lists sorted lexicographically
no duplicates
```

The displayed object is illustrative. Only canonicalized bytes are hashed.

Do not compute the key during this drafting task. Do not embed a future
computed key value into this packet or into the acceptance record.

## 11. Post-Issuance Stopping Boundary

After future issuance and external opportunity-key computation, stop before
implementation contact.

At that point:

```text
opening declaration:
ISSUED_NON_COMMIT

corrected commit-free window:
SUSPENDED_FOR_BOUNDED_IMPLEMENTATION

implementation contact:
NOT STARTED

implementation opportunity:
NOT CONSUMED

Authority C:
INACTIVE

Authority D:
INACTIVE

Authority E:
INACTIVE

canonical-input path:
NOT CONTACTED
```

A separate implementation-operation packet or explicit next governance act is
required before the first authorized repository write.

Do not combine issuance and implementation contact into one act.

## 12. Fail-Closed Conditions

Require STOP for:

```text
declaration identity mismatch
branch mismatch
HEAD mismatch
local origin/main mismatch
index lock present or created
staged entry
tracked deletion
unmerged entry
unexpected filtered Git apparent tracked diff
CRLF/raw-byte safety proof not run repository-wide
missing or unreadable tracked file
substantive exception in raw-byte CRLF safety proof
raw-different or CRLF-only count change not independently dispositioned
unexpected untracked entry
unexpected cache artefact
external-path inadmissibility
controlling source identity mismatch
Authority C/D/E unexpectedly active
prior canonical-input path contact
operator-window interpretation not accepted
operator-window interpretation unknown
inability to prove any required issuance condition
```

No automatic retry is authorized.

## 13. Current Task Boundary

This task creates only this governance Markdown draft and the companion
acceptance-for-issuance record draft.

It does not:

```text
accept the declaration by operator act
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

Current state remains:

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

## 14. Formatting

```text
UTF-8
LF only
no BOM
final newline present
```

This draft contains no self-identity field for its own complete bytes and no
computed implementation-opportunity-key value.

# TORMENT Brainvision Stage S3B v0.3 BLOCKER-2 R4 Authority-C Implementation Opening Non-Commit Declaration Draft v0.1

## 1. Document Status

```text
classification:
AUTHORITY_C_IMPLEMENTATION_OPENING_DECLARATION_CORRECTED_DRAFT_PREPARED_FOR_INDEPENDENT_REVIEW

document state:
DRAFT ONLY
NOT ISSUED
NOT ACTIVE
NOT COMMITTED
NOT PUSHED

implementation-opening declaration:
DRAFT ONLY
NOT ISSUED

implementation window:
NOT OPENED
```

THIS DRAFT DOES NOT OPEN THE IMPLEMENTATION WINDOW.

THIS DECLARATION DOES NOT ACTIVATE AUTHORITY C.

This document is a draft suitable for independent review. It is not accepted,
not issued, and not authority to begin implementation contact, modify source or
test files, run implementation tests, invoke governed runner modes, stage,
commit, or push.

## 2. Schema And Operation

```text
schema:
torment.brainvision.blocker2.r4.authority_c.implementation_opening_non_commit_declaration_draft.v0.1

operation_label:
AUTHORITY_C_IMPLEMENTATION_OPENING_NON_COMMIT_DECLARATION_DRAFT

document_classification:
AUTHORITY_C_IMPLEMENTATION_OPENING_DECLARATION_CORRECTED_DRAFT_PREPARED_FOR_INDEPENDENT_REVIEW
```

This draft is non-commit governance material. It is distinct from the
Authority-C activation declaration and does not issue that declaration.

## 3. Current Governance State Preserved

```text
implementation authorization:
ACCEPTED BY DESIGN IDENTITY
NOT OPENED FOR EXECUTION

implementation-opening declaration:
DRAFT ONLY
NOT ISSUED

implementation window:
NOT OPENED

implementation contact:
NOT STARTED

implementation opportunity:
NOT CONSUMED

Authority-C activation declaration:
DRAFT ONLY
NOT ISSUED

Authority C:
INACTIVE

Authority D:
INACTIVE

Authority E:
INACTIVE

candidate payload:
NOT CONSTRUCTED

candidate bytes:
NOT CONSTRUCTED

canonical-input path:
NOT CONTACTED

canonical input:
NOT PREPARED
NOT PUBLISHED

corrected commit-free window:
OPEN

FORMAL_HOLD:
ACTIVE

BLOCKER-2:
OPEN

BLOCKER-4:
INACTIVE
```

## 4. Controlling Identity Bindings

Implementation authorization:

```text
path:
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_AUTHORITY_C_IMPLEMENTATION_NON_COMMIT_AUTHORIZATION_DESIGN_v0.1.md

implementation_authorisation_sha256:
2a06ee4aae319d72e3447195b1adbba8703ea6d23a49ae4fec6d08460e2e749a

byte count:
48193

line count:
1849

format:
LF only
BOM absent
final newline present
```

The accepted bytes of that document are themselves the implementation
authorization. Acceptance alone does not authorize implementation contact or
source modification.

Accepted invocation-form design:

```text
path:
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_AUTHORITY_C_INVOCATION_FORM_DESIGN_v0.1.md

SHA-256:
bde299d389572c8cd25d2a0e9a7aa60f56009edd8cf96311f2c1abc100749f58

byte count:
59456

independent classification:
A. AUTHORITY_C_INVOCATION_FORM_DESIGN_ACCEPTED_AS_IS
```

Authority-C activation declaration draft:

```text
path:
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_AUTHORITY_C_NON_COMMIT_ACTIVATION_DECLARATION_DRAFT_v0.1.md

SHA-256:
2c2500e624d77c70d33a6c5d29db6f5f04442fbc6a75a5930e90b89f0df64750

byte count:
22726

state:
DRAFT ONLY
NOT ISSUED
```

Accepted invocation HEAD:

```text
branch:
main

accepted_invocation_head:
1f915e29119cd58ea39e8cf355f7364118c71043
```

## 5. Required Future Issuance Lifecycle

The only permitted lifecycle for this declaration is:

```text
DRAFT

INDEPENDENT_REVIEW

ACCEPTED_FOR_ISSUANCE

ISSUED_NON_COMMIT

exact bytes frozen

byte count captured externally

SHA-256 captured externally

issued identity verified before first authorised repository write

SUSPENDED_FOR_BOUNDED_IMPLEMENTATION

CLOSED_TO_FURTHER_EDITS

AWAITING_RESTORATION_DECLARATION

AWAITING_INDEPENDENT_DISPOSITION

RESTORED / RESUMED / separately closed / new accepted HEAD required
```

The declaration is:

```text
non-commit
one-shot
limited to exactly one bounded implementation operation
distinct from the Authority-C activation declaration
```

This corrected draft remains at:

```text
DRAFT
```

Independent review acceptance is not issuance. Issuance is not Authority-C
activation. Window suspension is not terminal.

No source or test write may occur before the exact issued declaration identity
exists and is verified externally.

## 6. Non-Self-Reference Requirements

This declaration draft does not contain its own SHA-256.

The declaration must not contain:

```text
its own SHA-256
a whole-declaration identity field
any opportunity-key value
any value derived from its future complete SHA-256
```

After valid issuance and byte freezing, the declaration identity is computed
externally. No post-hash rewrite is permitted.

Explanatory references to the external opportunity-key construction name are
not declaration fields and are not embedded key values.

## 7. External Opportunity-Key Construction

After issuance and external declaration identity capture, the external
opportunity key is computed as:

```text
external opportunity key =
SHA-256(
  canonical_json_bytes(
    {
      "schema":
        "torment.brainvision.blocker2.r4.authority_c.implementation_opportunity_key.v0.1",

      "implementation_authorisation_sha256":
        "2a06ee4aae319d72e3447195b1adbba8703ea6d23a49ae4fec6d08460e2e749a",

      "implementation_opening_declaration_sha256":
        "<issued declaration SHA-256>",

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

The displayed object is illustrative. Only the canonicalized byte form defined
by the canonicalization rules is hashed.

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

The resulting key is held externally in operation evidence. It is later bound
by the implementation result and by the restoration declaration. It is never
written into this opening declaration.

## 8. Authorised Future Implementation Surface

The future bounded implementation operation may involve exactly these three
source/test paths.

Authorised new source file:

```text
research/brainvision/blocker2_r4_authority_c_candidate_v0_1.py
```

Authorised existing runner file for narrow modification:

```text
research/brainvision/run_blocker2_authoritative_retained_single_run_v0_1.py
```

Permitted purpose only:

```text
extract or expose the shared mode-independent validation core
make the runner-facing validator delegate to that core
retain one shared validation truth
do not copy shared validation logic
```

Authorised new test file:

```text
research/brainvision/test_blocker2_r4_authority_c_candidate_v0_1.py
```

No other source or test modification is authorized.

## 9. Prohibited Surface

Modification is explicitly prohibited for:

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
```

Any discovered need for additional source or test changes requires:

```text
STOP
NO EXPANSION BY IMPLEMENTER DISCRETION
RETURN FOR GOVERNANCE REVIEW
```

## 10. Corrected Commit-Free-Window Transition

Before valid issuance:

```text
corrected commit-free window:
OPEN
```

Only after all of the following:

```text
valid non-commit issuance
exact declaration bytes frozen
external declaration byte count captured
external declaration SHA-256 captured
issued identity verified
```

may the window become:

```text
corrected commit-free window:
SUSPENDED_FOR_BOUNDED_IMPLEMENTATION
```

This is an active transitional state only. It may never be a terminal resting
state.

Any terminal condition after valid issuance moves the corrected commit-free
window to:

```text
AWAITING_INDEPENDENT_DISPOSITION
```

unless the successful sequence has already moved it to:

```text
AWAITING_RESTORATION_DECLARATION
```

Examples of terminal conditions include, without narrowing the general rule:

```text
pre-contact termination after issuance
abort after implementation contact
test failure after modification
scope expansion discovered after contact
repository-state failure after contact
unknown write outcome
unknown implementation-contact state
unknown implementation-opportunity state
implementation-result write failure
any inability to prove safe continuation
```

`AWAITING_INDEPENDENT_DISPOSITION` is itself non-terminal. It may be resolved
only through separately governed independent disposition.

Independent disposition may determine one of:

```text
restore the corrected commit-free window to OPEN
restore or mark the corrected commit-free window RESUMED
close the corrected Layer-C window under separately satisfied closing conditions
require establishment of a new accepted invocation HEAD
```

Independent disposition must not infer that retry is safe. No automatic retry
is permitted.

The opening declaration does not amend or replace committed corrected Layer-C
authority.

Future bounded implementation mutations are considered expected only because
they are:

```text
enumerated in advance
independently reviewed
bound to exact identities
restricted to the accepted surface
captured before and after modification
```

If the operator-window interpretation is not independently accepted:

```text
implementation must not begin
corrected commit-free window remains OPEN
formal Layer-C closure is required
a new accepted invocation HEAD must be established
```

Because this corrected document remains draft-only:

```text
corrected commit-free window remains OPEN
```

## 11. Implementation Contact And One-Shot Consumption

One-shot implementation enforcement is governance-only.

There is:

```text
no process-local implementation latch
no cross-process lock
no lock file
no technical prevention of a second repository write
```

Immediately before the first future authorised repository write, external
operation evidence must record:

```text
implementation_contact_started:
true

implementation_opportunity_consumed:
true
```

This transition:

```text
is not a repository write
is not a technical latch
is not a lock
is not a cross-process mechanism
```

The following do not begin implementation contact:

```text
read-only inspection
identity capture
pre-write validation
in-memory replacement preparation, provided nothing is written to the repository
```

No automatic retry is permitted after contact is consumed or its state becomes
unknown.

This draft operation does not begin contact and does not consume the
opportunity.

All external operation evidence is held outside the repository working tree,
including:

```text
issued declaration identity
external opportunity key
implementation contact transition
opportunity-consumption transition
before-identity captures
write-outcome evidence
terminal classification evidence
```

External operation evidence must not create repository entries. The only
separately authorized repository governance write after source/test edit
closure is the one implementation-result document.

## 12. Git And Repository Prohibitions

Throughout the future bounded implementation operation:

```text
staging:
PROHIBITED

Git-index modification:
PROHIBITED

commit:
PROHIBITED

push:
PROHIBITED
```

Prohibited commands include:

```text
git add
git rm
git mv
git update-index
index-rewriting git reset
any command that refreshes, locks, or rewrites .git/index
```

Read-only Git inspection must use:

```text
GIT_OPTIONAL_LOCKS=0
git --no-optional-locks
```

Any creation of:

```text
.git/index.lock
```

requires:

```text
STOP
repository-state failure
independent disposition
```

## 13. Required Future Opening-State Checks

Before issuance and again before the first future source/test write, verify:

```text
branch == main

HEAD ==
1f915e29119cd58ea39e8cf355f7364118c71043

local origin/main == HEAD

no network fetch required or authorized

.git/index.lock absent

staged entries none

tracked deletions none

unmerged entries none

genuine tracked diff none

known 303-line CRLF-view artefact set unchanged

exact expected R4 Markdown governance inventory

no unexpected untracked entries

no new repository __pycache__

no new repository .pyc

no repository .pytest_cache

governed external path state admissible

Authority C inactive

Authority D inactive

Authority E inactive

canonical-input path not contacted
```

The admissible R4 governance Markdown pattern is:

```text
?? docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_*.md
```

Before implementation contact, admissible untracked repository entries are only
the exact expected R4 governance Markdown drafts matching that pattern.

After the first authorized write, the only additional admissible untracked
entries are:

```text
research/brainvision/blocker2_r4_authority_c_candidate_v0_1.py
research/brainvision/test_blocker2_r4_authority_c_candidate_v0_1.py
```

The authorized modified runner remains tracked.

Any other untracked entry requires STOP.

The implementation-result governance document becomes admissible only when its
one authorized post-edit write is reached.

The declaration binds these controlling source before-identities.

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

All six identity values must be re-verified immediately before the first
authorized repository write.

Any mismatch requires:

```text
STOP
CONTROLLING_IDENTITY_MISMATCH
NO IMPLEMENTATION CONTACT
```

or, if contact is already consumed:

```text
AWAITING_INDEPENDENT_DISPOSITION
```

The retained-control source is reference-only and must remain byte-identical.

## 14. Governed Execution Prohibitions

The opening declaration must not authorize or perform:

```text
governed runner invocation
PREFLIGHT_ONLY
PREPARE_PATHS
EXECUTE_EXACT_SINGLE_RUN
Authority-C activation
Authority-D activation
Authority-E activation
candidate payload construction
candidate byte construction
canonical-input path contact
canonical-input preparation
canonical-input publication
```

No implementation test may run during this draft-only task.

Ordinary unit and conformance test execution may occur only inside a validly
opened bounded implementation window and only if:

```text
no governed runner mode is invoked
no governed Authority-C candidate construction is invoked
no canonical-input path is contacted
no Authority C/D/E activation occurs
```

Testing must leave no repository:

```text
__pycache__
.pyc
.pytest_cache
```

Any such artifact must be removed without Git-index contact, or the operation
must stop if clean removal cannot be proven.

No implementation test may run during this correction task.

## 15. One Post-Edit Governance-Result Write Authority

The declaration authorizes exactly one future governance-result document write
after source/test edit closure:

```text
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_AUTHORITY_C_IMPLEMENTATION_RESULT_v0.1.md
```

That document is:

```text
governance Markdown
not source
not a test
outside the bounded three-file implementation surface
admitted by the existing R4 Markdown governance pattern
```

The one result write is available after source and test edit closure, whether
closure occurs by:

```text
successful completion
terminal stop
abort
failure
unknown outcome
```

At that point:

```text
implementation window:
CLOSED_TO_FURTHER_EDITS

corrected commit-free window:
AWAITING_RESTORATION_DECLARATION
for the successful sequence

or:

AWAITING_INDEPENDENT_DISPOSITION
for every non-success terminal sequence after issuance
```

The implementation-result document must contain no whole-document identity
field.

Its exact identity is computed externally only after its bytes are frozen.

That external identity is later bound by the applicable restoration or
independent-disposition governance record.

No second result-document write is authorized.

For a pre-contact termination where no implementation-result document exists,
independent disposition may resolve the window without requiring a nonexistent
result document. A frozen implementation-result document is not an
unconditional prerequisite for every independent-disposition path.

## 16. Restoration Requirement

The bounded operation cannot terminally rest in either:

```text
SUSPENDED_FOR_BOUNDED_IMPLEMENTATION
AWAITING_RESTORATION_DECLARATION
```

A separately governed restoration declaration must resolve the corrected
commit-free window after the implementation result is frozen and externally
identified.

The opening declaration itself does not restore the window.

## 17. Repository State At Opening

Repository state at opening is a future issuance binding. Issuance must verify
and record:

```text
repository:
C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric

branch:
main

HEAD:
1f915e29119cd58ea39e8cf355f7364118c71043

local origin/main:
1f915e29119cd58ea39e8cf355f7364118c71043

network fetch:
NOT REQUIRED
NOT AUTHORIZED

.git/index.lock:
ABSENT

staged entries:
NONE

tracked deletions:
NONE

unmerged entries:
NONE

genuine tracked diff:
NONE

known CRLF-view artefact set:
303 pre-existing presentation lines, unchanged

untracked entries:
exact expected R4 Markdown governance inventory at issuance
```

## 18. Stopping And Fail-Closed Conditions

Immediate STOP and independent disposition are required for:

```text
branch mismatch
HEAD mismatch
local origin/main mismatch
.git/index.lock present or created
staged entries present
tracked deletion present
unmerged entry present
unexpected genuine tracked diff
changed CRLF-view artefact set
unexpected untracked entry
unexpected cache artefact
governed external path inadmissible
controlling identity mismatch
authorized-surface ambiguity
need for an additional source or test file
prohibited-path contact
Authority C, D, or E unexpectedly active
canonical-input path previously contacted
unknown implementation-contact state
unknown opportunity-consumption state
any Git-index mutation
any attempted staging, commit, or push
any governed runner invocation
any inability to prove the required state
```

No automatic retry is authorized after implementation contact is consumed or
becomes unknown.

## 19. Current Correction Task Stopping Boundary

During this correction task:

```text
revise only the existing implementation-opening declaration draft
do not issue it
do not suspend the corrected commit-free window
do not modify source or tests
do not run implementation tests
do not invoke governed runner modes
do not issue the Authority-C activation declaration
do not activate Authority C, D, or E
do not construct candidate payloads or bytes
do not contact the canonical-input path
do not stage, commit, or push
leave FORMAL_HOLD active
leave BLOCKER-2 open
leave BLOCKER-4 inactive
```

## 20. Draft Formatting

This draft is deterministic UTF-8 Markdown with:

```text
LF-only line endings
no BOM
final newline present
```

The draft itself does not claim acceptance or issuance.

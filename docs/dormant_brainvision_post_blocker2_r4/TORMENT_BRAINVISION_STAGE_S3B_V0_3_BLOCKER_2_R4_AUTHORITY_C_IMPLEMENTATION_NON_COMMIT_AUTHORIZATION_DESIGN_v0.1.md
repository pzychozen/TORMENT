# TORMENT Brainvision Stage S3B v0.3
# BLOCKER-2 R4 - Authority-C Implementation Non-Commit Authorization Design v0.1

```text
DRAFT ONLY
NON-EXECUTING
NOT ISSUED
NOT ACTIVE
NOT COMMITTED
NOT PUSHED
```

## 1. Document Status

This document is a non-executing implementation-authorization design draft.

It does not implement the Authority-C invocation form.

It does not authorize implementation by itself.

It does not issue an implementation-opening declaration.

It does not issue or activate the Authority-C non-commit activation
declaration.

It does not activate Authority C, Authority D, or Authority E.

It does not construct candidate payloads.

It does not construct canonical candidate bytes.

It does not contact the governed canonical-input path.

It does not invoke PREPARE_PATHS, PREFLIGHT_ONLY, EXECUTE_EXACT_SINGLE_RUN, the
A/B orchestrator, or any governed runner mode.

It does not create, consume, publish, move, delete, stage, commit, or push any
implementation, canonical input, execution authority, or governed artifact.

It leaves the current corrected commit-free window open.

## 2. Current Draft Classification

Current draft classification:

```text
AUTHORITY_C_IMPLEMENTATION_AUTHORIZATION_DESIGN_DRAFT_PREPARED_FOR_INDEPENDENT_REVIEW
```

This is not an independent acceptance classification. Independent review must
assign one of the design-stage classifications in Section 16 before this design
can support any later implementation-opening declaration.

## 3. Binding Inputs

Accepted invocation-form design:

```text
path:
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_AUTHORITY_C_INVOCATION_FORM_DESIGN_v0.1.md

byte count:
59456

SHA-256:
bde299d389572c8cd25d2a0e9a7aa60f56009edd8cf96311f2c1abc100749f58

independent review classification:
A. AUTHORITY_C_INVOCATION_FORM_DESIGN_ACCEPTED_AS_IS
```

Accepted Authority-C declaration draft:

```text
path:
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_AUTHORITY_C_NON_COMMIT_ACTIVATION_DECLARATION_DRAFT_v0.1.md

byte count:
22726

SHA-256:
2c2500e624d77c70d33a6c5d29db6f5f04442fbc6a75a5930e90b89f0df64750
```

Accepted invocation HEAD:

```text
1f915e29119cd58ea39e8cf355f7364118c71043
```

Branch:

```text
main
```

Controlling runner source identity:

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

Controlling retained-control source identity:

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

The retained-control source is reference-only and must remain byte-identical.

The runner may change only within the narrow shared-validation delegation scope
defined in this design.

These identities must be recaptured and checked before any future
implementation-opening declaration opens a bounded implementation window.

## 4. Core Objective

The future implementation authorization may permit only the narrow source and
test changes required to implement the accepted Authority-C invocation form.

It exists to resolve this governance conflict:

```text
The accepted implementation requires repository file creation and one narrow
runner edit.

The corrected Layer-C commit-free window currently prohibits repository source
modification.
```

Authority basis for any future suspension:

```text
The corrected commit-free window was established through an operator-governed
non-commit opening under the corrected Layer-C sequence.

The future implementation-opening declaration does not amend, replace, or
reinterpret the committed corrected Layer-C authorization.

It is a separate operator-governed declaration whose sole effect is to suspend
the active commit-free window for one explicitly bounded implementation surface.
```

The future declaration may exercise that effect only after:

```text
1. the implementation-authorization design is independently accepted;
2. the exact implementation-opening declaration is independently reviewed and
   accepted;
3. the accepted invocation HEAD remains:
   1f915e29119cd58ea39e8cf355f7364118c71043;
4. HEAD equals local origin/main;
5. the repository and governed external state satisfy the opening declaration;
6. no commit has occurred since establishment of the accepted invocation HEAD.
```

The suspension preserves the accepted invocation HEAD rather than replacing it.

Relationship to corrected Layer-C Section 13 unexpected-mutation handling:

```text
Authorized implementation mutations under this design are not unexpected
mutations because they are enumerated in advance, limited to the exact
authorized surface, independently reviewed, bound by the accepted
implementation authorization, bound by the issued implementation-opening
declaration, identity-checked before first write, and captured exactly after
final edit.

Suspension is a property of the operator-governed commit-free-window instance.
It is not an amendment to the committed corrected Layer-C authorization, does
not redefine the corrected Layer-C closing conditions, and does not create a
native corrected Layer-C suspension/resumption terminal label.

Any mutation outside the exact authorized implementation surface remains an
unexpected mutation and triggers STOP, terminal handling, and independent
disposition.
```

If independent review determines that the operator-governed window cannot be
suspended under the controlling corrected Layer-C authority, implementation must
not begin.

In that case:

```text
STOP
leave the corrected commit-free window open
await formal closure under the corrected Layer-C closing conditions
establish a new accepted invocation HEAD before any implementation work
```

This design does not claim inherent, automatic, or implementer-controlled
suspension power. The authority is conditional, explicit, independently
reviewable, and fail-closed.

The resolution is fail-closed:

```text
independent acceptance of this implementation-authorization design does not
itself permit source modification

a separate implementation-opening declaration must be issued before source or
test modification

that declaration explicitly suspends the corrected commit-free window for the
bounded implementation surface only
```

No document may claim that the corrected commit-free window remains open while
authorized source files are being modified.

Implementation authorization identity model:

```text
The independently reviewed and accepted implementation-authorization design
document is itself the implementation authorization.

No second implementation-authorization document is created.

Before independent acceptance it is:
DESIGN DRAFT ONLY
NOT AUTHORISATION

After independent acceptance under classification:
A. AUTHORITY_C_IMPLEMENTATION_AUTHORIZATION_DESIGN_ACCEPTED_AS_IS

or:
B. AUTHORITY_C_IMPLEMENTATION_AUTHORIZATION_DESIGN_ACCEPTED_WITH_NON_BLOCKING_NOTES

its exact accepted bytes and SHA-256 become the implementation authorization.
```

`implementation_authorisation_sha256` equals the accepted SHA-256 of:

```text
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_AUTHORITY_C_IMPLEMENTATION_NON_COMMIT_AUTHORIZATION_DESIGN_v0.1.md
```

Acceptance still does not permit repository modification. A separately reviewed
and issued implementation-opening declaration remains mandatory.

## 5. Sequencing Model

### State I - Current Accepted Design State

```text
corrected commit-free window:
OPEN

repository source modification:
PROHIBITED

Authority C:
INACTIVE

Authority-C opportunity:
NOT CONSUMED

implementation:
NOT AUTHORISED
```

This current task remains in State I except for creation of this untracked
design draft.

### State II - Implementation Authorization Draft

```text
authorization document:
DRAFT ONLY

repository source modification:
STILL PROHIBITED

Authority C:
INACTIVE

implementation-opening declaration:
NOT CREATED
```

The present document is State II material only. It is not an implementation
opening.

### State III - Independently Accepted Implementation Authorization

Independent acceptance of this design may classify the implementation
authorization design as accepted, but it does not itself permit source
modification.

Required State III binding:

```text
independent acceptance:
DESIGN ACCEPTANCE ONLY

corrected commit-free window:
OPEN

repository source modification:
STILL PROHIBITED

next required act:
separate implementation-opening declaration
```

The later implementation-opening declaration must bind:

```text
schema and operation label
accepted implementation_authorisation_sha256
accepted invocation-form design SHA-256
accepted declaration draft SHA-256
accepted invocation HEAD
branch
repository state at opening
controlling source before-identities
exact authorized new files
exact authorized modified files
explicit prohibited files
opportunity-key externalization statement
implementation contact boundary
corrected commit-free-window transition
one post-edit governance result-document write authority
no governed runner execution statement
no Authority-C activation statement
no Authority-D or Authority-E activation statement
no canonical-input path contact statement
no commit, push, staging, or Git-index-modification statement
```

Minimum fixed binding values:

```text
accepted invocation-form design SHA-256:
bde299d389572c8cd25d2a0e9a7aa60f56009edd8cf96311f2c1abc100749f58

accepted Authority-C declaration draft SHA-256:
2c2500e624d77c70d33a6c5d29db6f5f04442fbc6a75a5930e90b89f0df64750

accepted invocation HEAD:
1f915e29119cd58ea39e8cf355f7364118c71043

branch:
main
```

External implementation opportunity key model:

```text
implementation_opportunity_key:
computed externally only after the implementation-opening declaration has been
issued and its exact bytes, byte count, and SHA-256 have been frozen.

The key is never carried inside the implementation-opening declaration.

The implementation-opening declaration contains no implementation_opportunity_key
field, no whole-declaration identity field, and no field derived from the
complete declaration SHA-256.

The implementation-opening declaration SHA-256 is observed externally after
issuance and is represented in the key preimage only by
implementation_opening_declaration_sha256.

Key preimage:
SHA-256(canonical_json_bytes over mapping:
{
  "schema": "torment.brainvision.blocker2.r4.authority_c.implementation_opportunity_key.v0.1",
  "implementation_authorisation_sha256": "<accepted implementation authorization SHA-256>",
  "implementation_opening_declaration_sha256": "<issued declaration SHA-256>",
  "accepted_invocation_head": "1f915e29119cd58ea39e8cf355f7364118c71043",
  "authorised_new_files": [
    "research/brainvision/blocker2_r4_authority_c_candidate_v0_1.py",
    "research/brainvision/test_blocker2_r4_authority_c_candidate_v0_1.py"
  ],
  "authorised_modified_files": [
    "research/brainvision/run_blocker2_authoritative_retained_single_run_v0_1.py"
  ]
})

Canonicalization rules:
UTF-8
no BOM
sorted mapping keys
compact separators
repo-relative POSIX paths
case-sensitive exact spelling
file lists lexicographically sorted
no duplicate list entries
SHA-256 over the exact canonical bytes

The key is non-self-referential. It uses no self-excluding hash, no recursive
hash, no fixed-point construction, no placeholder rewrite, and no post-hoc
rewrite of the opening declaration.
```

Implementation-opening declaration lifecycle:

```text
DRAFT
independently reviewed
ACCEPTED FOR ISSUANCE
issued as a non-commit operator declaration
exact byte count and SHA-256 captured
identity bound before the first authorized write
```

Rules:

```text
The implementation-opening declaration must be independently reviewed and
accepted before issuance.

It is non-commit.

It is one-shot for exactly one bounded implementation operation.

It is distinct from the Authority-C activation declaration.

It must state prominently:
THIS DECLARATION DOES NOT ACTIVATE AUTHORITY C

It does not activate Authority D or E.

It does not authorize governed candidate construction.

It does not authorize canonical-input path contact.

It cannot be mistaken for the Authority-C activation declaration.

No repository write may occur until the exact issued declaration identity has
been captured and verified.

Any proposed implementation-opening declaration that carries an
implementation_opportunity_key field, a whole-declaration identity field, a
field derived from the complete declaration SHA-256, or an unexpected
in-declaration opportunity-key field is invalid.
```

### State IV - Bounded Implementation Window

State IV begins only when a separately issued implementation-opening declaration
explicitly opens it.

Chosen governance model:

```text
implementation window:
OPEN

corrected commit-free window:
SUSPENDED_FOR_BOUNDED_IMPLEMENTATION

authorized modifications:
only the listed implementation surface

Authority C:
INACTIVE

Authority-C declaration:
NOT ISSUED

candidate construction:
PROHIBITED

governed path contact:
PROHIBITED

commit and push:
PROHIBITED unless separately authorized after implementation review

staging:
PROHIBITED

Git index modification:
PROHIBITED
```

The corrected commit-free window is not represented as open during authorized
repository source modification. It is suspended only for the bounded
implementation surface named in the opening declaration.

### State V - Implementation Completion And Review Hold

After code and tests are written:

```text
implementation window:
CLOSED TO FURTHER EDITS

corrected commit-free window:
AWAITING_RESTORATION_DECLARATION

Authority C:
INACTIVE

candidate construction:
PROHIBITED

implementation:
AWAITING INDEPENDENT REVIEW
```

The implementer must capture:

```text
exact modified-file identities
exact new-file identities
exact diffs
exact test commands
exact test results
repository state before and after
bytecode/cache state before and after
```

No further source edit is permitted without independent disposition.

The corrected commit-free window is not permanently closed merely because the
bounded implementation occurred. It is not automatically resumed by the
implementer.

It may resume only through a separate explicit operator restoration declaration
issued after independent implementation acceptance.

The restoration declaration must re-verify:

```text
branch == main
HEAD == 1f915e29119cd58ea39e8cf355f7364118c71043
local origin/main equals HEAD
.git/index.lock absent
no staged entries
no tracked deletions
no unmerged entries
actual modified and new files equal the accepted implementation result
known CRLF-view artefact set unchanged
governed external path state remains admissible
Authority C/D/E remain inactive
no canonical-input path contact occurred
```

The restoration declaration must bind:

```text
implementation_opportunity_key
implementation_opening_declaration_sha256
externally computed accepted implementation-result identity
```

Upon valid restoration:

```text
corrected commit-free window:
RESUMED
```

The four previously completed governed mutations remain completed. The
remaining canonical-input publication opportunity remains governed and is not
consumed by implementation.

If restoration cannot be established:

```text
corrected commit-free window:
AWAITING_INDEPENDENT_DISPOSITION

Authority C and Authority D:
MAY NOT PROCEED
```

### State VI - Accepted Implementation

Independent implementation acceptance establishes readiness only.

After independent implementation acceptance:

```text
corrected commit-free window:
AWAITING_RESTORATION_DECLARATION

next required act:
separate operator restoration declaration
```

It does not automatically:

```text
issue the Authority-C declaration
activate Authority C
construct candidate payloads
construct canonical candidate bytes
contact the canonical-input path
invoke Authority D
invoke Authority E
publish canonical input
create execution authority
commit
push
```

A later, separately issued Authority-C activation declaration remains required
before Authority C can become active.

Implementation neither destroys nor consumes the remaining Authority-D
publication opportunity.

## 6. Authorized Implementation Surface

The future implementation-opening declaration may authorize only this surface.

Authorized new module:

```text
research/brainvision/blocker2_r4_authority_c_candidate_v0_1.py
```

Expected contents:

```text
AuthorityCAssertions
AuthorityCInvocationLatch
_AUTHORITY_C_LATCHES
module-level threading.Lock
PrecomputedImmutableFileIdentityProvider
RepositoryState injection adapter as required
absence-observation injection adapter as required
build_authority_c_candidate_payload(...)
run_authority_c_candidate_construction(...)
Authority-C result schema and result builders
safe candidate-holder repr and str behavior
process/write/Git/cache traps or enforcement seams required by the accepted
design
```

Authorized narrow runner edit:

```text
research/brainvision/run_blocker2_authoritative_retained_single_run_v0_1.py
```

Purpose:

```text
extract or expose the shared mode-independent validation core
make the existing runner-facing validator delegate to that core
retain one source of shared validation truth
do not copy validation logic
```

Authorized new test module:

```text
research/brainvision/test_blocker2_r4_authority_c_candidate_v0_1.py
```

The implementation must satisfy the accepted minimum 136-test normative plan
from the accepted invocation-form design, either in this module or through
clearly identified existing tests plus new tests.

No other source or test file may be modified unless a strict dependency is
identified and independently reviewed before the surface expands.

## 7. Prohibited Surface

The following files remain outside the authorized implementation surface:

```text
research/brainvision/blocker2_retained_absolute_path_control_v0_1.py
research/brainvision/blocker2_r4_ordered_directory_creation_helper_v0_1.py
research/brainvision/blocker2_r4_authority_b_evidence_publisher_v0_1.py
research/brainvision/blocker2_r4_ab_orchestrator_v0_1.py
```

In particular:

```text
AUTHORIZED_SURFACE_PATHS must not be edited.
```

Also prohibited:

```text
torment_service modification
kernel modification
production service integration
live memory contact
prompt contact
action contact
autonomy contact
cognition contact
canonical-input publication
PREPARE_PATHS invocation
PREFLIGHT_ONLY invocation
EXECUTE_EXACT_SINGLE_RUN invocation
A/B orchestrator invocation
Authority-D work
Authority-E work
staging
Git index modification
commit or push unless separately authorized after implementation review
```

Staging and Git-index modification are prohibited. This includes:

```text
git add
git rm
git mv
git update-index
git reset operations that rewrite the index
any command that refreshes, locks, or rewrites .git/index
```

All Git status and identity inspection must use:

```text
GIT_OPTIONAL_LOCKS=0
git --no-optional-locks
```

No staging is necessary for the bounded implementation operation. Commit and
push remain separately prohibited. Any `.git/index.lock` creation is an
implementation repository-state failure and requires STOP and independent
disposition.

## 8. Repository-State Contract

The implementation-opening declaration must capture the exact repository state
at the opening boundary.

The design must account for:

```text
the six authorized retained Python surfaces in the frozen classifier
the five current R4 Markdown drafts
the 303 known CRLF-view artefact lines
this implementation-authorization design draft
any later explicit implementation-opening declaration
```

The implementation-opening contract must not freeze an obsolete exact untracked
list prematurely.

R4 Markdown governance documents are admitted by pattern:

```text
?? docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_*.md
```

The future implementation-result document is governance Markdown admitted by
that R4 pattern at the exact path:

```text
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_AUTHORITY_C_IMPLEMENTATION_RESULT_v0.1.md
```

The exact inventory must be captured at the implementation-opening boundary.

Repository-state requirements at opening:

```text
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

genuine tracked diff:
NONE before implementation opening

known CRLF-view artefact set:
303 pre-existing " M" lines, unchanged

untracked entries:
exact boundary inventory of R4 Markdown governance drafts and any explicit
implementation-opening declaration draft admitted by the opening governance
```

`dirty_authorized_surfaces` and `dirty_unrelated_surfaces` remain outputs of the
frozen retained classifier. This implementation authorization does not redefine
those lists.

Implementation-file admissibility is governed by the separate bounded
implementation-authorization surface, not by changing
`AUTHORIZED_SURFACE_PATHS`.

The authorized implementation files will appear in `dirty_unrelated_surfaces`
because the frozen `AUTHORIZED_SURFACE_PATHS` constant does not include them.
This is expected. It must not be corrected by editing
`AUTHORIZED_SURFACE_PATHS`.

Unexpected means any path or genuine modification outside the explicitly
authorized implementation set and the R4 Markdown governance pattern.

### Opening Check

At implementation opening:

```text
implementation window:
NOT YET OPEN until declaration identity is captured

staged entries:
NONE

tracked deletions:
NONE

unmerged entries:
NONE

.git/index.lock:
ABSENT

genuine tracked modifications:
NONE before implementation contact

admissible untracked entries:
R4 Markdown governance drafts matching
?? docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_*.md

known CRLF-view artefact set:
exactly 303 accepted " M" lines, unchanged

new repository __pycache__ or .pyc:
NONE

new repository .pytest_cache:
NONE
```

### In-Progress Check

During the bounded implementation window, admissible untracked entries are only:

```text
1. entries matching:
?? docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_*.md

2. exactly these authorized new files:
research/brainvision/blocker2_r4_authority_c_candidate_v0_1.py
research/brainvision/test_blocker2_r4_authority_c_candidate_v0_1.py

3. nothing else
```

Genuine tracked modifications during implementation:

```text
research/brainvision/run_blocker2_authoritative_retained_single_run_v0_1.py
and nothing else
```

Invariant rules during implementation:

```text
staged entries:
NONE

tracked deletions:
NONE

unmerged entries:
NONE

.git/index.lock:
ABSENT

known CRLF-view artefact set:
exactly 303 accepted " M" lines, unchanged

new repository __pycache__ or .pyc:
NONE

new repository .pytest_cache:
NONE
```

### Edit-Closure Check

At implementation edit closure, admissible repository state is:

```text
actual new files:
exactly the two authorized implementation files

actual modified files:
exactly the runner file

unexpected untracked files:
NONE

unexpected tracked modifications:
NONE

staged entries:
NONE

tracked deletions:
NONE

unmerged entries:
NONE

.git/index.lock:
ABSENT

new repository __pycache__ or .pyc:
NONE

new repository .pytest_cache:
NONE
```

A narrower no-op determination before first write is a pre-contact terminal or
independent-disposition path. It is not an implementation edit-closure state
and does not itself authorize the post-edit implementation-result document
write.

### Result-Capture Check

At implementation-result capture, admissible repository state is limited to:

```text
1. R4 Markdown governance drafts matching:
?? docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_*.md

2. exactly these authorized new implementation files:
research/brainvision/blocker2_r4_authority_c_candidate_v0_1.py
research/brainvision/test_blocker2_r4_authority_c_candidate_v0_1.py

3. exactly this implementation-result governance Markdown file:
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_AUTHORITY_C_IMPLEMENTATION_RESULT_v0.1.md

4. no other untracked files
```

At implementation-result capture, the sole admissible genuine tracked
modification is:

```text
research/brainvision/run_blocker2_authoritative_retained_single_run_v0_1.py
```

No other genuine tracked modification is admissible.

At implementation-result capture, the external Result-Capture Check report must
bind:

```text
opening repository state
in-progress repository-state observations if any
edit-closure repository state
result-capture repository state
dirty_authorized_surfaces exactly as measured
dirty_unrelated_surfaces exactly as measured
actual new files
actual modified files
unexpected files
known CRLF-view artefact set
bytecode/cache state
index-lock state
staging state
externally computed implementation-result document path
externally computed implementation-result byte count
externally computed implementation-result SHA-256
externally computed implementation-result line count
externally computed implementation-result formatting identity
```

Those externally computed implementation-result identity fields are recorded in
the Result-Capture Check report outside the implementation-result document.

Any mismatch at any checkpoint is an implementation repository-state failure
requiring STOP and independent disposition.

## 9. Safety Boundaries Preserved From Accepted Invocation Design

The future implementation must preserve all accepted invocation-form
requirements, including:

```text
python -B
PYTHONDONTWRITEBYTECODE=1 before interpreter startup
import sys then sys.dont_write_bytecode = True before all other imports
no repository __pycache__ creation
no repository .pyc creation
no repository .pytest_cache creation
no process launch after Authority-C activation
no Git after Authority-C activation
no filesystem discovery after Authority-C activation
no filesystem writes during Authority-C construction
no canonical-input path contact during Authority C
process-local one-shot latch
strict pre-contact versus post-contact exit-code boundary
candidate secrecy across every diagnostic channel
external non-self-referential absence-observation identity
pre_existing_kind null for final_child_absent
one shared validation core
exact 23-field candidate contract
mandatory rejection-class conformance corpus
```

Implementation work may use Git and filesystem writes only before Authority C
exists and only inside the explicitly opened bounded implementation window.

## 10. Implementation Test Authorization

Ordinary read-only test execution is permitted during the bounded
implementation window if and only if it does not invoke governed Authority-C
candidate construction or any governed runner mode.

```text
unit and conformance tests:
PERMITTED

write/process/Git/cache trap tests using synthetic seams:
PERMITTED

threaded and re-entrant latch tests:
PERMITTED

governed Authority-C invocation:
PROHIBITED

PREPARE_PATHS:
PROHIBITED

PREFLIGHT_ONLY:
PROHIBITED

EXECUTE_EXACT_SINGLE_RUN:
PROHIBITED

A/B orchestrator:
PROHIBITED
```

The implementation is not accepted merely because a total count of 136 tests
passes.

Acceptance requires:

```text
every normative requirement mapped to one or more named tests
all tests pass
all rejection classes represented in the conformance corpus
runner-facing validator and extracted core return identical outcomes
write/process/Git/cache traps exercised
threaded and re-entrant latch tests pass
pre-contact versus post-contact exit boundaries pass
candidate secrecy tests pass
absence-observation identity and retained-model tests pass
no governed runner mode invoked
```

The implementation report must include:

```text
exact test commands
exact pass/fail/skip totals
platform
Python version
environment variables
whether python -B was used
repository cache state before and after
```

Skip admissibility:

```text
A skipped test is admissible only when all of the following are true:

1. the test is explicitly platform-gated;
2. the current reporting platform is not the platform required by the test;
3. the exact skip reason is recorded verbatim;
4. the report identifies the platform on which the test must execute;
5. the normative requirement is also covered by at least one test that executed
   and passed on the current reporting platform, unless the requirement is
   inherently platform-specific;
6. every inherently platform-specific requirement must later execute and pass on
   the authoritative required platform before implementation acceptance.
```

Every other skip is a test failure.

No normative requirement may be declared satisfied solely because its tests were
skipped.

A raw test total with unexplained or inadmissible skips is insufficient for
implementation acceptance.

The implementation result must enumerate for each test:

```text
test name
status
skip reason
platform gate
required execution platform
whether the requirement has an executed passing test
```

Independent review or normative validation evidence must also confirm:

```text
the implementation-opening declaration contains no implementation_opportunity_key
field
unexpected in-declaration opportunity-key fields are rejected
the external implementation_opportunity_key equals the exact canonical
computation defined in Section 5
authorized file-list ordering is deterministic and lexicographic
repo-relative POSIX path form is enforced
changing any key preimage member changes the key
identical key preimages produce the same key
no self-referential, self-excluding, recursive, fixed-point, placeholder, or
post-hoc rewrite key construction is used
window_status_history contains exactly four entries
window_status_history entry order is exact
window_status_history contains no duplicate or missing checkpoint
NOT_REACHED semantics are applied exactly
terminal table window values equal the RESULT_CAPTURE history entry
no implementation result infers restoration or RESUMED
implementation-result schema contains no whole-result-document identity field
unexpected in-document implementation-result SHA-256 field is rejected
unexpected in-document implementation-result byte-count identity field is
rejected
unexpected in-document implementation-result line-count identity field is
rejected
external result identity is computed only after bytes are frozen
changing any result-document byte changes the external SHA-256
identical frozen result bytes produce the same external identity
no self-excluding, recursive, fixed-point, placeholder, or post-hoc rewrite
model is used for implementation-result document identity
restoration declaration binds the externally computed result identity
```

## 11. Change-Control Model

Authorized new files:

```text
research/brainvision/blocker2_r4_authority_c_candidate_v0_1.py
research/brainvision/test_blocker2_r4_authority_c_candidate_v0_1.py
```

Authorized modified files:

```text
research/brainvision/run_blocker2_authoritative_retained_single_run_v0_1.py
```

Prohibited files include every repository file outside the authorized surface,
with explicit prohibition for the reference-only retained-control source and
the R4 helper, publisher, and orchestrator files named in Section 7.

Maximum scope-expansion procedure:

```text
STOP
NO EXPANSION BY IMPLEMENTER DISCRETION
RETURN FOR GOVERNANCE REVIEW
```

Any need to modify a file outside the authorized surface triggers that
procedure.

Before and after implementation, the implementer must capture:

```text
exact diff
diff SHA-256
before identities
after identities
unexpected untracked files
unexpected tracked modifications
staged entries
Git index modification state
tracked deletions
unmerged entries
.git/index.lock state
new bytecode
new pytest cache
canonical-input path contact state
```

## 12. Implementation Contact And Opportunity Semantics

Implementation contact is distinct from Authority-C candidate contact.

Implementation one-shot enforcement is governance-only.

```text
There is no process-local latch.

There is no cross-process lock.

There is no lock file.

There is no technical mechanism that prevents a second repository write attempt,
because the authorized implementation writes may be performed by an operator
through multiple tools and processes.
```

Enforcement is supplied solely by:

```text
the accepted implementation authorization
the independently accepted and issued implementation-opening declaration
the bounded implementation opportunity key
operator discipline
repository evidence
independent review
```

This deliberately differs from the Authority-C candidate-construction latch,
which is technically enforced inside one process.

Affirmative non-contact acts:

```text
Read-only repository inspection does not begin implementation contact.

Before-identity capture does not begin implementation contact.

Pre-write validation does not begin implementation contact.

Preparation of in-memory replacement text does not begin implementation contact
provided it is not written to the repository.
```

Implementation contact begins immediately before the first authorized
repository write in the bounded implementation surface.

Immediately before the first repository write, the operator records or emits
the implementation-contact transition in operation evidence:

```text
implementation_contact_started:
true

implementation_opportunity_consumed:
true
```

This transition is governance evidence only. It is not a repository write, not
a technical latch, not a lock file, and not a cross-process mechanism. It must
not create a repository write solely for the transition; it may be held in
operation memory or operator evidence until result capture. If the write
outcome is unknown after the transition, the opportunity remains consumed or
UNKNOWN and no retry is authorized without independent disposition.

Pre-modification abort:

```text
implementation_contact_started:
false

implementation_opportunity_consumed:
false

terminal state:
IMPLEMENTATION_ABORTED_PRE_MODIFICATION
```

After implementation contact:

```text
implementation_contact_started:
true

implementation_opportunity_consumed:
true or UNKNOWN according to available evidence
```

If the first authorized repository write is known to have occurred, the
implementation opportunity is consumed.

If the implementation process terminates after the implementation-opening
declaration but before it can be established whether a repository write
occurred, the opportunity status is UNKNOWN and independent disposition is
required.

No second implementation attempt may occur without independent disposition
after:

```text
implementation contact
unknown termination after opening
scope-expansion discovery
test failure after modification
unexpected repository mutation
```

These semantics do not activate Authority C and do not consume the Authority-C
candidate-construction opportunity.

The implementation-result governance-document write occurs only after
implementation contact has already been consumed or classified UNKNOWN. It does
not convert a consumed or UNKNOWN implementation opportunity back to
unconsumed, does not create a second implementation opportunity, and does not
permit later source or test modification. Failure while writing the result
document is an after-modification or unknown terminal condition requiring
independent disposition.

## 13. Future Implementation Result Schema

Future implementation-result document path:

```text
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_AUTHORITY_C_IMPLEMENTATION_RESULT_v0.1.md
```

The implementation-result document is governance Markdown. It is not source or
test code, is admitted by the R4 Markdown governance-document pattern, and is
not part of the bounded three-file implementation surface.

The issued implementation-opening declaration authorizes exactly one post-edit
governance result-document write at that exact path. This permission is
separate from source/test implementation contact. It is available only after
implementation edit closure while:

```text
implementation_window_status:
CLOSED_TO_FURTHER_EDITS

corrected_commit_free_window_status:
AWAITING_RESTORATION_DECLARATION
```

That result-document write is the sole repository write permitted while those
two window statuses hold. It does not reopen the implementation window, does
not authorize source or test edits, does not create a second implementation
opportunity, and cannot convert an already consumed or UNKNOWN implementation
opportunity back to unconsumed.

If the result-document write fails or has an unknown outcome, the operation
must classify as an after-modification or unknown terminal condition and await
independent disposition.

The future implementation-result record must contain at least:

```text
schema
operation
classification
accepted_invocation_head
accepted_design_sha256
accepted_declaration_sha256
implementation_authorisation_sha256
implementation_opening_declaration_sha256
implementation_opportunity_key
window_status_history
implementation_contact_started
implementation_opportunity_consumed
repository_state_before
repository_state_after
authorised_new_files
authorised_modified_files
actual_new_files
actual_modified_files
unexpected_files
before_identities
after_identities
diff_sha256
test_commands
test_results
bytecode_created
pytest_cache_created
canonical_input_path_contacted
governed_runner_invoked
authority_c_activated
authority_d_activated
authority_e_activated
commit_created
push_performed
detail
```

Minimum field count:

```text
34
```

The `window_status_history` field replaces the former scalar
`implementation_window_status` and `corrected_commit_free_window_status`
top-level fields. The minimum field count remains 34 because two scalar fields
are removed and two fields, `implementation_opportunity_key` and
`window_status_history`, are added.

`window_status_history` must be an ordered list of exactly four entries:

```text
1. OPERATION_START
2. FIRST_WRITE
3. EDIT_CLOSURE
4. RESULT_CAPTURE
```

Each entry must contain exactly these status fields:

```text
checkpoint
implementation_window_status
corrected_commit_free_window_status
observation_basis
```

Permitted `checkpoint` values are exactly:

```text
OPERATION_START
FIRST_WRITE
EDIT_CLOSURE
RESULT_CAPTURE
```

Admissible per-entry `implementation_window_status` values:

```text
NOT_OPENED
OPEN
CLOSED_TO_FURTHER_EDITS
UNKNOWN
NOT_REACHED
```

Admissible per-entry `corrected_commit_free_window_status` values:

```text
OPEN
SUSPENDED_FOR_BOUNDED_IMPLEMENTATION
AWAITING_RESTORATION_DECLARATION
RESUMED
AWAITING_INDEPENDENT_DISPOSITION
UNKNOWN
NOT_REACHED
```

History rules:

```text
All four entries are mandatory; omission is invalid.

The entries must appear in the exact order:
OPERATION_START, FIRST_WRITE, EDIT_CLOSURE, RESULT_CAPTURE.

Duplicate checkpoints are invalid.

Missing checkpoints are invalid.

For an unreached checkpoint, both status fields must be NOT_REACHED and
observation_basis must explain why the checkpoint was not reached.

No later checkpoint may be marked reached if an earlier required checkpoint is
NOT_REACHED, except that RESULT_CAPTURE may be reached to record an early
terminal result.

Section 14 terminal-state window values must equal the RESULT_CAPTURE
window_status_history entry.

No implementation result may infer RESUMED. Only a later explicit restoration
declaration may establish RESUMED.
```

Implementation-result document identity

The implementation-result document contains no whole-document identity field.

Its identity is computed externally only after:

1. the implementation-result document content is complete;
2. its exact bytes are frozen;
3. no further change to the document is permitted.

The externally computed identity consists of:

path
byte count
SHA-256
line count
formatting identity, including:
- LF or CRLF status
- BOM state
- final-newline state

The external identity is recorded in the Result-Capture Check report defined in
Section 8.

The later restoration declaration defined in Section 5 must bind that
externally computed implementation-result identity.

Because the identity lies outside the bytes it identifies, the construction is
non-self-referential.

The implementation-result document must not contain:

- its own complete-file SHA-256;
- its own complete-file byte count;
- its own complete-file line count;
- its own complete-file formatting identity;
- a placeholder for any such identity;
- a self-excluding whole-file identity;
- a recursive or fixed-point identity;
- any field requiring the document to be rewritten after its external identity
  is computed.

No post-identity rewrite is permitted.

The implementation-result record must not itself authorize later governance
actions.

## 14. Future Implementation Terminal States

Future bounded implementation operation terminal states:

```text
IMPLEMENTATION_COMPLETED_AWAITING_REVIEW
IMPLEMENTATION_ABORTED_PRE_MODIFICATION
IMPLEMENTATION_ABORTED_AFTER_MODIFICATION
IMPLEMENTATION_SCOPE_EXPANSION_REQUIRED
IMPLEMENTATION_REPOSITORY_STATE_INVALID_PRE_CONTACT
IMPLEMENTATION_REPOSITORY_STATE_INVALID_POST_CONTACT
IMPLEMENTATION_TEST_FAILURE
IMPLEMENTATION_UNKNOWN_TERMINAL_STATE
```

Normative terminal-state attribute table:

```text
IMPLEMENTATION_COMPLETED_AWAITING_REVIEW:
implementation_contact_started:
true

implementation_opportunity_consumed:
true

files_changed:
true

retry_prohibited:
true

independent_disposition_required:
true

implementation_window_status:
CLOSED_TO_FURTHER_EDITS

corrected_commit_free_window_status:
AWAITING_RESTORATION_DECLARATION

IMPLEMENTATION_ABORTED_PRE_MODIFICATION:
implementation_contact_started:
false

implementation_opportunity_consumed:
false

files_changed:
false

retry_prohibited:
true pending independent disposition

independent_disposition_required:
true

implementation_window_status:
NOT_OPENED or CLOSED_TO_FURTHER_EDITS, according to detection point

corrected_commit_free_window_status:
OPEN if the opening declaration had not issued.
AWAITING_INDEPENDENT_DISPOSITION if the opening declaration had issued.

IMPLEMENTATION_ABORTED_AFTER_MODIFICATION:
implementation_contact_started:
true

implementation_opportunity_consumed:
true or UNKNOWN according to evidence

files_changed:
true or UNKNOWN according to evidence

retry_prohibited:
true

independent_disposition_required:
true

implementation_window_status:
CLOSED_TO_FURTHER_EDITS

corrected_commit_free_window_status:
AWAITING_INDEPENDENT_DISPOSITION

IMPLEMENTATION_SCOPE_EXPANSION_REQUIRED:
if discovered before first write:
  implementation_contact_started: false
  implementation_opportunity_consumed: false
  files_changed: false
  retry_prohibited: true
  independent_disposition_required: true
  implementation_window_status: NOT_OPENED or CLOSED_TO_FURTHER_EDITS,
    according to detection point
  corrected_commit_free_window_status: OPEN if the opening declaration had not
    issued; AWAITING_INDEPENDENT_DISPOSITION if the opening declaration had
    issued

if discovered after first write:
  also classify as IMPLEMENTATION_ABORTED_AFTER_MODIFICATION
  do not continue

IMPLEMENTATION_REPOSITORY_STATE_INVALID_PRE_CONTACT:
implementation_contact_started:
false

implementation_opportunity_consumed:
false

files_changed:
false

retry_prohibited:
true pending independent disposition

independent_disposition_required:
true

implementation_window_status:
NOT_OPENED or CLOSED_TO_FURTHER_EDITS, according to detection point

corrected_commit_free_window_status:
OPEN if the opening declaration had not issued.
AWAITING_INDEPENDENT_DISPOSITION if the opening declaration had issued.

IMPLEMENTATION_REPOSITORY_STATE_INVALID_POST_CONTACT:
implementation_contact_started:
true

implementation_opportunity_consumed:
true or UNKNOWN

files_changed:
true or UNKNOWN

retry_prohibited:
true

independent_disposition_required:
true

implementation_window_status:
CLOSED_TO_FURTHER_EDITS

corrected_commit_free_window_status:
AWAITING_INDEPENDENT_DISPOSITION

also treated as:
IMPLEMENTATION_ABORTED_AFTER_MODIFICATION

IMPLEMENTATION_TEST_FAILURE:
implementation_contact_started:
true

implementation_opportunity_consumed:
true

files_changed:
true

retry_prohibited:
true

independent_disposition_required:
true

implementation_window_status:
CLOSED_TO_FURTHER_EDITS

corrected_commit_free_window_status:
AWAITING_INDEPENDENT_DISPOSITION

IMPLEMENTATION_UNKNOWN_TERMINAL_STATE:
implementation_contact_started:
UNKNOWN unless exact evidence establishes true or false

implementation_opportunity_consumed:
UNKNOWN unless exact evidence establishes consumed

files_changed:
UNKNOWN unless exact evidence establishes state

retry_prohibited:
true

independent_disposition_required:
true

implementation_window_status:
UNKNOWN or CLOSED_TO_FURTHER_EDITS conservatively

corrected_commit_free_window_status:
AWAITING_INDEPENDENT_DISPOSITION or UNKNOWN

uncertainty:
must never be interpreted as unconsumed or safe to retry
```

Every terminal classification has exactly one normative attribute binding above
or a clearly defined evidence-dependent branch. No terminal state permits
automatic retry after consumed or unknown implementation contact.

`SUSPENDED_FOR_BOUNDED_IMPLEMENTATION` is an active transitional status only.
It is never a terminal resting status. Any terminal condition after an
implementation-opening declaration has issued moves the corrected commit-free
window to `AWAITING_INDEPENDENT_DISPOSITION`, unless the successful sequence has
already moved it to `AWAITING_RESTORATION_DECLARATION`.

Independent disposition after any pre-contact termination may restore the
corrected commit-free window to `OPEN` or `RESUMED` as appropriate, close under
the corrected Layer-C closing conditions, or require a new accepted invocation
HEAD. It may not infer that retry is safe.

## 15. Immediate Stopping Boundary For This Draft

During creation of this design draft:

```text
create only the implementation-authorization design draft
do not issue the authorization
do not create an implementation-opening declaration
do not modify source or tests
do not run implementation tests
do not invoke governed runner modes
do not issue the Authority-C declaration
do not activate Authority C, D, or E
do not construct candidate payloads or bytes
do not contact the canonical-input path
do not stage, commit, or push
leave the corrected commit-free window open
leave BLOCKER-2 open
leave BLOCKER-4 inactive
```

## 16. Design-Stage Review Classifications

Independent review of this implementation-authorization design must use one of:

```text
A. AUTHORITY_C_IMPLEMENTATION_AUTHORIZATION_DESIGN_ACCEPTED_AS_IS

B. AUTHORITY_C_IMPLEMENTATION_AUTHORIZATION_DESIGN_ACCEPTED_WITH_NON_BLOCKING_NOTES

C. AUTHORITY_C_IMPLEMENTATION_AUTHORIZATION_DESIGN_CORRECTION_REQUIRED

D. AUTHORITY_C_IMPLEMENTATION_AUTHORIZATION_DESIGN_REJECTED
```

B classification is eligible only when every non-blocking note is non-executing
and cannot alter authorized files, identity computation, repository gates,
window transitions, contact/opportunity semantics, test acceptance, or terminal
handling. Any note that can affect one of those matters requires
classification C.

Acceptance of this design is not an implementation-opening declaration.

## 17. Terminal State Of This Draft

After creation of this design draft:

```text
Authority C:
INACTIVE
OPPORTUNITY NOT CONSUMED

Authority D:
INACTIVE

Authority E:
INACTIVE

execution authority:
NOT CREATED
NOT CONSUMED

canonical input:
NOT PREPARED
NOT PUBLISHED

implementation-opening declaration:
NOT CREATED

bounded implementation window:
NOT OPEN

corrected commit-free window:
OPEN

FORMAL_HOLD:
ACTIVE

BLOCKER-2:
OPEN

BLOCKER-4:
INACTIVE
```

This draft is design-only and is not authority to implement, execute, publish,
stage, commit, or push.

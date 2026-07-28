# TORMENT Brainvision Stage S3B v0.3 BLOCKER-2 R4 PREPARE_PATHS Authorization Document Design v0.1

## 1. Document Scope

This Markdown document is a draft-stage design for a future tracked R4
`PREPARE_PATHS` authorization document.

It is not itself that authorization document.

Created design path:

```text
research/brainvision/TORMENT_Brainvision_Stage_S3B_v0_3_BLOCKER_2_R4_prepare_paths_authorization_document_design_v0_1.md
```

Document status:

```text
DRAFT_UNCOMMITTED
```

Terminal classification:

```text
BLOCKER_2_R4_PREPARE_PATHS_AUTHORIZATION_DOCUMENT_DESIGN_DRAFTED_PENDING_INDEPENDENT_REVIEW_GOVERNANCE_ACCEPTANCE_COMMIT_AND_PUSH
```

This design draft does not create, approve, or activate the future R4
authorization document. It defines the required structure, boundaries,
identity bindings, lifecycle states, and review requirements that a later
separately authorized document must satisfy before any canonical-input
preparation may begin.

## 2. Authority, Baseline, And Operating Controls

Authoritative repository:

```text
C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric
```

Accepted baseline for this design draft:

```text
branch: main
HEAD: fbc2eec782478ff0f4e13c004cc58d316f367ed8
origin/main: fbc2eec782478ff0f4e13c004cc58d316f367ed8
working tree before this draft: clean
.git\index.lock: absent
```

Operating controls preserved:

```text
FORMAL_HOLD: ACTIVE
MODE: 0
BLOCKER-2: OPEN
BLOCKER-4: INACTIVE
R4: NOT AUTHORIZED
PREFLIGHT: BLOCKED
EXECUTE_EXACT_SINGLE_RUN: UNAUTHORIZED
BRAINVISION: OFFLINE, QUARANTINED, SYNTHETIC/RESEARCH ONLY
```

This draft does not modify or integrate `torment_service/kernel/`, live
TORMENT memory, production cognition, autonomy, truth-selection, or
service/runtime execution.

## 3. Controlling Accepted Governance Chain

This design is bound to the following accepted governance chain:

```text
accepted historical preservation HEAD:
fbc2eec782478ff0f4e13c004cc58d316f367ed8

accepted historical lifecycle record:
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_SUCCESSOR_PREPARE_PATHS_AUTHORIZATION_LIFECYCLE_PRESERVATION_RECORD_v0.1.md

accepted governance-remediation design:
research/brainvision/TORMENT_Brainvision_Stage_S3B_v0_3_BLOCKER_2_successor_prepare_paths_governance_remediation_design_v0_1.md

accepted governance-remediation design HEAD:
d8b513f8c93d87f8019d0412c92124af5edde018

accepted post-PREPARE_PATHS assessment:
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_POST_PREPARE_PATHS_PATHS_PREPARED_AND_AUTHORIZATION_PRESERVATION_ASSESSMENT_v0.1.md

accepted post-PREPARE_PATHS assessment HEAD:
125955187061a60124d3df28e8e3c9fc41c8d369
```

The historical lane is immutable and non-reusable. R4 must not alter,
consume, edit, reopen, normalize, or inherit the historical lane.

## 4. Design Purpose

The future R4 authorization document must permit only:

```text
preparation of one fresh canonical PREPARE_PATHS input

for one separately governed R4 remediation attempt

bound to one distinct accepted repository HEAD
```

The future R4 authorization document must not authorize:

```text
the PREPARE_PATHS invocation itself
PREFLIGHT
EXECUTE_EXACT_SINGLE_RUN
retained execution
successor authority consumption
BLOCKER-2 closure
BLOCKER-4 activation
```

The future document is therefore an authority source for later canonical-input
preparation only after its own acceptance and identity recomputation. It is
not invocation authority.

## 5. R4 Attempt Uniqueness Rule

This design adopts the following mandatory governance rule:

```text
REMEDIATION_ATTEMPT_HEAD_UNIQUENESS
```

Definition:

```text
each separately authorized R4 remediation attempt binds one distinct accepted HEAD

no two remediation attempts may share an accepted HEAD

if an attempt fails, is rejected, or becomes unusable, a later attempt requires
a new committed and pushed governance baseline

same-HEAD repeat is prohibited by governance

distinct HEAD provides fresh repository-state-bound identity

distinct HEAD does not provide true per-event identity
```

Schema limitation preserved:

```text
true per-event identity: NOT AVAILABLE UNDER CURRENT SCHEMA
```

The future R4 authorization document must not claim to repair this schema-level
identity limitation. A distinct HEAD is a governance substitute for missing
per-event identity, not a cryptographic invocation-event discriminator.

## 6. Fresh Authorization-Document Requirements

The future R4 authorization document must:

```text
use a new repository-relative path
be distinct from the original PREPARE_PATHS authorization document
be independently reviewed
be governance accepted
be committed and pushed
have its identity recomputed at the accepted post-commit HEAD
exist before canonical-input preparation begins
```

Required five-field identity:

```text
path
git_blob_oid
checked_out_byte_sha256
canonical_authorization_declaration_identity
authorization_status
```

The five-field identity is not valid while the document is uncommitted, while
governance acceptance is pending, or while it has not been recomputed at the
final accepted post-commit and pushed HEAD.

The recomputation must occur after commit, push, and checkout-state
confirmation at the final accepted HEAD that governs the R4 remediation
attempt.

The recomputed five-field identity must correspond to the exact checked-out
bytes present at the moment canonical-input preparation begins.

If any checkout, branch change, reset, line-ending rewrite, or other
working-tree representation change occurs between identity recomputation and
canonical-input preparation, the five-field identity must be recomputed again
before the canonical input is prepared.

## 7. Original Authorization Non-Reuse Boundary

Original authorization document:

```text
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_SUCCESSOR_PREPARE_PATHS_EXECUTION_AUTHORIZATION_v0.1.md
```

Lifecycle disposition for R4:

```text
historical: YES
preserved: YES
non-reusable: YES
valid as R4 authority: NO
editable in place: NO
```

Implementation acceptance of the unchanged historical document does not
override governance prohibition. If current wrapper validation would accept the
historical document when supplied with a matching five-field identity, that is
implementation permissiveness only. Governance still prohibits reuse.

The future R4 document must not reuse:

```text
the original path
the original document identity
the original canonical input identity
the original execution authorization identity
the original run identity
the original result-directory identity
```

All original successor-lane identities remain historical-only and
non-reusable for remediation.

## 8. Authorization-Document Status Model

The future R4 authorization document must use a fail-closed status model.

Minimum statuses:

```text
DRAFT_UNCOMMITTED
REVIEWED_NOT_ACCEPTED
GOVERNANCE_ACCEPTED_PENDING_COMMIT
PREPARED_NOT_ACTIVE
HISTORICAL_NON_REUSABLE
```

Fail-closed status table:

| Status | Entered by | Required evidence | Allowed actions | Prohibited actions | Next transition and whether commit/push is required |
| --- | --- | --- | --- | --- | --- |
| DRAFT_UNCOMMITTED | Initial drafting of the proposed authorization-document text before independent review. | Exact draft path and draft bytes. | Draft correction under separate authorization. | Governance acceptance inference; commit; push; canonical-input preparation; PREPARE_PATHS invocation; PREFLIGHT; EXECUTE_EXACT_SINGLE_RUN. | DRAFT_UNCOMMITTED -> REVIEWED_NOT_ACCEPTED; commit/push required: NO. |
| REVIEWED_NOT_ACCEPTED | Completion of independent review of the drafted text. | Independent review record identifying the exact draft path and reviewed bytes. | Correction of the uncommitted draft under separate authorization. | Governance acceptance inference; commit; push; canonical-input preparation; PREPARE_PATHS invocation; PREFLIGHT; EXECUTE_EXACT_SINGLE_RUN. | REVIEWED_NOT_ACCEPTED -> GOVERNANCE_ACCEPTED_PENDING_COMMIT, commit/push required: NO; or REVIEWED_NOT_ACCEPTED -> SUPERSEDED_DRAFT on rejection, commit/push required: NO, with next valid state DRAFT_UNCOMMITTED for the superseding draft. |
| GOVERNANCE_ACCEPTED_PENDING_COMMIT | Explicit governance acceptance of the reviewed text. | Accepted independent review; explicit governance acceptance decision; exact accepted draft identity. | Separately authorized staging and commit preparation. | Canonical-input preparation; PREPARE_PATHS invocation; PREFLIGHT; EXECUTE_EXACT_SINGLE_RUN. | GOVERNANCE_ACCEPTED_PENDING_COMMIT -> PREPARED_NOT_ACTIVE; commit/push required: YES. |
| PREPARED_NOT_ACTIVE | Successful commit and push, accepted HEAD and origin/main reconfirmation, clean-tree confirmation, .git/index.lock absence, and five-field identity recomputation over the exact checked-out representation. | Commit identity; push result; HEAD equality with origin/main; final five-field authorization-document identity. | Use as the source document for one separately authorized canonical-input preparation action. | PREPARE_PATHS invocation; PREFLIGHT; EXECUTE_EXACT_SINGLE_RUN; execution-authority creation; execution-authority consumption; canonical-input preparation without separate authorization; any second canonical-input preparation. PREPARED_NOT_ACTIVE does not mean invocation active, execution authority active, PREFLIGHT active, or authority consumable. | PREPARED_NOT_ACTIVE -> HISTORICAL_NON_REUSABLE after single-use exhaustion or explicit governance retirement; commit/push required for the record effecting this transition: YES. |
| HISTORICAL_NON_REUSABLE | Consumption of the document's single preparation purpose when one canonical PREPARE_PATHS input has been prepared under separately granted authority, or explicit governance retirement of the remediation attempt before input preparation. | Canonical-input preparation record or explicit governance-retirement record; exact authorization-document identity; exact accepted HEAD; lifecycle disposition record. | Historical reference and audit only. | All renewed authority use; all canonical-input preparation reuse; all invocation-authority inference; editing in place to restore authority; PREPARE_PATHS invocation authority inference; PREFLIGHT authority inference; execution authority inference. | No live transition from this document is valid. Any further R4 attempt requires a new authorization document at a new repository-relative path and a distinct accepted HEAD; commit/push required for that separate future route: YES. |

Complete transition set:

```text
DRAFT_UNCOMMITTED -> REVIEWED_NOT_ACCEPTED

  entry event:
  completion of independent review of the drafted text

  resulting state:
  REVIEWED_NOT_ACCEPTED

  required evidence for the resulting state:
  independent review record identifying the exact draft path and reviewed bytes

  allowed actions in the resulting state:
  correction of the uncommitted draft under separate authorization

  prohibited actions in the resulting state:
  governance acceptance inference
  commit
  push
  canonical-input preparation
  PREPARE_PATHS invocation
  PREFLIGHT
  EXECUTE_EXACT_SINGLE_RUN

  commit and push required for this transition:
  NO

REVIEWED_NOT_ACCEPTED -> GOVERNANCE_ACCEPTED_PENDING_COMMIT

  entered by:
  explicit governance acceptance of the reviewed text

  required evidence:
  accepted independent review
  explicit governance acceptance decision
  exact accepted draft identity

  allowed actions:
  separately authorized staging and commit preparation

  prohibited actions:
  canonical-input preparation
  PREPARE_PATHS invocation
  PREFLIGHT
  EXECUTE_EXACT_SINGLE_RUN

  commit and push required for this transition:
  NO

REVIEWED_NOT_ACCEPTED -> SUPERSEDED_DRAFT

  entry event:
  review rejection or governance rejection

  required evidence:
  independent review rejection record or governance rejection record identifying
  the exact rejected draft path and rejected bytes

  effect:
  the rejected text is not carried forward as accepted authority

  allowed actions:
  preparation of a superseding uncommitted draft under separate authorization

  prohibited actions:
  commit as accepted authority
  canonical-input preparation
  PREPARE_PATHS invocation
  PREFLIGHT
  EXECUTE_EXACT_SINGLE_RUN

  next valid state:
  DRAFT_UNCOMMITTED for the superseding draft

  SUPERSEDED_DRAFT is a terminal effect for the rejected text, not an
  authorization status.

  It confers no authority and must not appear as a live authorization-status
  value.

  commit and push required for this transition:
  NO

GOVERNANCE_ACCEPTED_PENDING_COMMIT -> PREPARED_NOT_ACTIVE

  entered by:
  successful commit and push
  accepted HEAD and origin/main reconfirmation
  clean-tree confirmation
  .git/index.lock absence
  five-field identity recomputation over the exact checked-out representation

  required evidence:
  commit identity
  push result
  HEAD equality with origin/main
  final five-field authorization-document identity

  allowed actions:
  use as the source document for one separately authorized canonical-input
  preparation action

  prohibited actions:
  PREPARE_PATHS invocation
  PREFLIGHT
  EXECUTE_EXACT_SINGLE_RUN
  execution-authority creation
  execution-authority consumption
  canonical-input preparation without separate authorization

  commit and push required for this transition:
  YES

PREPARED_NOT_ACTIVE -> HISTORICAL_NON_REUSABLE

  entered by either:

  A. consumption of the document's single preparation purpose when one canonical
     PREPARE_PATHS input has been prepared under separately granted authority

  or

  B. explicit governance retirement of the remediation attempt before input
     preparation

  required evidence:
  canonical-input preparation record or explicit governance-retirement record
  exact authorization-document identity
  exact accepted HEAD
  lifecycle disposition record

  effect:
  the document must not serve as the authority source for any further
  canonical-input preparation

  required next-attempt rule:
  any further R4 attempt requires a new authorization document at a new
  repository-relative path and a distinct accepted HEAD under
  REMEDIATION_ATTEMPT_HEAD_UNIQUENESS

  allowed actions:
  historical preservation and audit reference only

  prohibited actions:
  reuse for canonical-input preparation
  editing in place for renewed authority
  PREPARE_PATHS invocation authority inference
  PREFLIGHT authority inference
  execution authority inference

  commit and push required for the record effecting this transition:
  YES

No transition other than those listed above is valid.

Any status not reached through a defined transition is invalid and fails closed.
```

Consumption terminology:

```text
"Consumption" in this status model means only exhaustion of the authorization
document's single documentation-lifecycle preparation purpose.

It does not mean, and must never be recorded as:

  wrapper field authority_consumed = true

  successor execution-authority creation

  successor execution-authority consumption

  historical consumed-lane authority

Those states remain false, absent, or unchanged throughout the R4
authorization-document lifecycle.
```

Exact usable transition for canonical-input preparation support:

```text
GOVERNANCE_ACCEPTED_PENDING_COMMIT
-> commit and push
-> accepted HEAD and origin/main reconfirmed
-> five-field identity recomputed over the checked-out representation
-> status recorded as PREPARED_NOT_ACTIVE
-> separate canonical-input preparation authority issued
-> usable only for one fresh canonical PREPARE_PATHS input preparation
```

`PREPARED_NOT_ACTIVE` does not itself authorize canonical-input preparation.
It may support that action only after a separate governance decision.

No ambiguity is permitted between:

```text
document preparation authority
canonical-input preparation authority
PREPARE_PATHS invocation authority
```

These are three separate governance actions. Completion of one does not imply
the next.

## 9. Required Future Authorization-Document Content

The future R4 authorization document must bind at minimum:

```text
document schema and version
purpose
scope
accepted baseline HEAD
accepted origin/main
required clean-tree state
required .git/index.lock absence
REMEDIATION_ATTEMPT_HEAD_UNIQUENESS
historical lifecycle record path and commit
historical authorization non-reuse declaration
new authorization-document path
expected five-field identity placeholders
permitted action: future canonical-input preparation only
prohibited actions
external root paths
external root admissibility requirements
expected executor selector
selected case-set, execution-order, A6, and case_set_sha256 requirements:
see the canonical Case-set binding block in this section
required output format for later invocation: json
durable invocation-time capture requirement
stdout versus canonical-result byte distinction
pre- and post-invocation absence requirements:
see the canonical Absence-check binding block in this section
authority_consumed expected: false
retained_execution expected: false
PREFLIGHT blocked
EXECUTE_EXACT_SINGLE_RUN unauthorized
BLOCKER-2 open
BLOCKER-4 inactive
FORMAL_HOLD active
MODE 0
```

Expected external roots to be bound by the future document, unless later
separate governance changes them:

```text
authority_registry_root: C:\TORMENT\brainvision_authority\blocker2_s3b_v0_3
fixture_root: C:\TORMENT\brainvision_authoritative_fixture\blocker2_s3b_v0_3
result_parent: C:\TORMENT\brainvision_retained_results\blocker2_s3b_v0_3
```

Expected root admissibility properties to be bound by the future authorization
document as pre-invocation verification requirements, not as asserted
invocation-time evidence:

```text
drive_type:
DRIVE_FIXED

filesystem_name:
NTFS

reparse_status:
NOT_REPARSE_POINT

repository_containment:
OUTSIDE_REPOSITORY
```

These properties are requirements that the later invocation must satisfy and
that the wrapper enforces.

This design asserts no invocation-time observation of those properties.

Expected executor selector:

```text
REAL_EXISTING_ABSOLUTE_PATH_A1_A2_A3_A5_V0_1
```

Case-set binding:

```text
selected cases:
A1
A2
A3
A5

execution order:
A1
A2
A3
A5

A6 selected:
false unless separately governed otherwise

case_set_sha256:
recomputed at canonical-input preparation time
```

The case-set identity must not be inferred only from the executor-selector
name.

The future authorization document must bind the selected cases, execution
order, and the recomputed `case_set_sha256` explicitly.

No A6 case or additional case is introduced by this design.

Absence-check binding:

```text
required pre-invocation absence checks, covering exactly:

  successor result directory

  successor global authority entry

  local gate

  run result

  retained completion

required post-invocation absence checks, covering the same five surfaces, plus:

  authority_consumed:
  false

  retained_execution:
  false

  successor global authority entry created:
  NO

  execution authority created:
  NO

  execution authority consumed:
  NO
```

PREPARE_PATHS is a path-preparation mode only.

The sole filesystem effect PREPARE_PATHS may produce is creation of the three
fixed broad roots if absent, using mkdir(parents=True, exist_ok=True).

The three fixed broad roots are:

```text
authority_registry_root

fixture_root

result_parent
```

All three roots already exist in the accepted current state, so this operation
is expected to be a no-op.

No other filesystem mutation is a legitimate PREPARE_PATHS effect.

It must not create:

```text
the successor result directory

a successor global authority entry

a local gate

a run result

retained completion
```

Path-preparation effects and execution effects are separate and must not be
conflated in the evidence record.

The future document may contain placeholders for values that cannot exist
before commit. Those placeholders must be replaced or validated by
post-commit, post-push recomputation before canonical-input preparation begins.

## 10. Line-Ending And Byte-Identity Doctrine

The accepted checkout-fragility finding is preserved:

```text
checked_out_byte_sha256 is representation-sensitive

repository currently has no governing .gitattributes rule for the path

The file's `text` and `eol` attributes are therefore unspecified.

The operator host's Git line-ending configuration governs the checked-out
representation.

LF and CRLF representations have different byte identities

future five-field identity recomputation must record the exact checked-out
representation

the representation must be recorded as LF or CRLF

identity must be recomputed after final commit and checkout state

no .gitattributes or Git configuration change is authorized by this design

neither LF nor CRLF is declared universally authoritative
```

This design does not propose silently normalizing historical identities. It
does not redesign repository line-ending policy. It remains neutral and
fail-closed.

A future separate governance action may address `.gitattributes`, but this
design does not authorize that action and does not depend on it.

## 11. Durable Capture Boundary

Any later authorized R4 invocation must use:

```text
--format json
```

Invocation-time capture must be directed into a pre-authorized immutable
external target. The capture must be contemporaneous with invocation and must
not depend on manual post-event console copying.

The future authorization document and later invocation authorization must
distinguish:

```text
stdout bytes: canonical JSON plus one trailing newline

canonical result bytes: canonical JSON without the stdout trailing newline
```

The evidence package must separately record:

```text
byte counts
SHA-256 values
representation labels
retention paths
schema validation results
```

The later R4 route must prohibit:

```text
--format human
--format both
manual post-event console copying as authoritative evidence
retrospective reconstruction as acceptance evidence
```

Retrospective analysis may be useful for audit explanation only. It must not
be substituted for invocation-time stdout bytes or canonical-result bytes.

## 12. Required Governance Sequence

The following sequence must be preserved without collapsing stages:

```text
R4 authorization-document design drafted
-> independent review
-> governance acceptance
-> design committed and pushed
-> fresh R4 authorization document separately authorized
-> authorization document drafted uncommitted
-> independent review
-> governance acceptance
-> authorization document committed and pushed
-> new accepted HEAD reconfirmed
-> five-field identity recomputed
-> canonical-input preparation separately authorized
-> canonical input prepared
-> canonical input independently reviewed
-> governance accepted
-> PREPARE_PATHS invocation separately authorized
-> durable invocation-time capture performed
-> post-R4 evidence assessed
-> formal PATHS_PREPARED acceptance decided
-> only then may successor PREFLIGHT governance be considered
```

No stage in this sequence is authorized merely because this design draft
exists.

## 13. Required Review Requirements

Independent review of the future authorization document must confirm at least:

```text
new repository-relative path is not the historical path
accepted HEAD is distinct from every prior separately authorized R4 attempt
HEAD equals origin/main at acceptance
working tree is clean at acceptance
.git\index.lock is absent at acceptance
historical non-reuse declaration is explicit
five-field identity placeholders are marked invalid until post-commit recomputation
line-ending representation must be recorded
permitted action is canonical-input preparation only
PREPARE_PATHS invocation authority is absent
PREFLIGHT authority is absent
EXECUTE_EXACT_SINGLE_RUN authority is absent
durable capture requirements are fail-closed
stdout and canonical-result byte identities are separated
authority_consumed expectation is false
retained_execution expectation is false
BLOCKER-2 remains open
BLOCKER-4 remains inactive
```

Review acceptance must not be inferred from formatting, path presence, or
implementation parseability alone.

## 14. Required Non-Claims

This design explicitly states that it:

```text
does not authorize creation of the R4 authorization document
does not authorize canonical-input preparation
does not authorize PREPARE_PATHS invocation
does not authorize PREFLIGHT
does not authorize EXECUTE_EXACT_SINGLE_RUN
does not create execution authority
does not consume execution authority
does not formally accept PATHS_PREPARED
does not close BLOCKER-2
does not activate BLOCKER-4
does not modify the identity schema
does not create true per-event identity
does not modify .gitattributes
does not modify Git configuration
does not alter the historical consumed lane
```

## 15. Terminal Classification And Draft State

Terminal classification:

```text
BLOCKER_2_R4_PREPARE_PATHS_AUTHORIZATION_DOCUMENT_DESIGN_DRAFTED_PENDING_INDEPENDENT_REVIEW_GOVERNANCE_ACCEPTANCE_COMMIT_AND_PUSH
```

Current state:

```text
document status: DRAFT_UNCOMMITTED

R4 authorization-document creation:
NOT AUTHORIZED BY THIS DESIGN DRAFT

R4 canonical-input preparation:
NOT AUTHORIZED

R4 PREPARE_PATHS invocation:
NOT AUTHORIZED

PREFLIGHT:
BLOCKED

BLOCKER-2:
OPEN

BLOCKER-4:
INACTIVE
```

## 16. Draft Creation Boundaries

During creation of this design draft:

```text
existing files modified: NO
Brainvision runner invoked: NO
external artifact created or modified: NO
R4 authorization document created: NO
R4 canonical input prepared: NO
PREFLIGHT work performed: NO
EXECUTE_EXACT_SINGLE_RUN work performed: NO
.gitattributes modified: NO
Git configuration modified: NO
commit performed: NO
push performed: NO
```

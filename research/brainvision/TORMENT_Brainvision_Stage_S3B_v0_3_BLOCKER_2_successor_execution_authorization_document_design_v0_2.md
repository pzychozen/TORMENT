# TORMENT Brainvision Stage S3B v0.3 BLOCKER-2 Successor Execution-Authorization Document Design v0.2

## 1. Executive Disposition

This v0.2 design supersedes v0.1. v0.1 is absent as an operational
candidate. v0.2 is the sole untracked design candidate.

v0.1 is superseded because it:

```text
did not explicitly exclude canonical_authorization_declaration_identity from
its own declaration preimage

placed PREPARE_PATHS invocation authorization before input preparation and
review in the lifecycle table

omitted required-identities and per-transition retry/retirement columns

did not fully pin canonical JSON extraction and parsing rules
```

Recommended tracked authorization-document path:

```text
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_SUCCESSOR_PREPARE_PATHS_EXECUTION_AUTHORIZATION_v0.1.md
```

Recommended first authorization status:

```text
PREPARED_NOT_ACTIVE
```

Terminal classification:

```text
B. AUTHORIZATION_DOCUMENT_DESIGN_COMPLETE_WITH_GOVERNANCE_DECISIONS
```

The design is complete enough to guide the next artifact, but the actual
authorization document must not be created until governance explicitly accepts
the declaration self-exclusion rule, canonical JSON and extraction rules,
PREPARED_NOT_ACTIVE PREPARE_PATHS-only status semantics, and the separate-path
later ACTIVE strategy.

## 2. Scope And Prohibitions

This task is documentation-only.

Created artifact:

```text
research/brainvision/TORMENT_Brainvision_Stage_S3B_v0_3_BLOCKER_2_successor_execution_authorization_document_design_v0_2.md
```

Not created:

```text
actual execution authorization document
canonical PREPARE_PATHS input
active authorization artifact
external active projection
authority entry
gate entry
result directory
run result
retained completion
```

Not derived:

```text
successor execution_authorization_identity
successor run_identity
successor result_directory_identity
successor path_model
successor child paths
authorization_input_identity for a future canonical input
execution_authorization_document_identity for the future document
```

No PREPARE_PATHS, PREFLIGHT_ONLY, or EXECUTE_EXACT_SINGLE_RUN runner mode is
authorized or invoked by this design.

## 3. Accepted Baseline And Ancestry

Authoritative baseline:

```text
branch: main
HEAD: 068c486ceba8e62efc866508dbecaec4fe6d9718
origin/main: 068c486ceba8e62efc866508dbecaec4fe6d9718
starting working tree: exactly one untracked authorization-document design v0.1
.git/index.lock: absent
```

Required ancestry verified:

```text
corrective implementation:
3e516bd3714b75b0a7c6b760e44fd02439837700

accepted successor assessment:
94cf0b9a4d4f1e83b00178ccca3363f4e6eed73f

accepted successor design:
e8b7e626905e391c5d34c6e4b3a3e90fe998bc88

accepted governance-identity blocker assessment:
068c486ceba8e62efc866508dbecaec4fe6d9718
```

Accepted document identities at this baseline:

| Document | Git blob | Bytes | Checked-out SHA-256 |
| --- | --- | ---: | --- |
| `research/brainvision/TORMENT_Brainvision_Stage_S3B_v0_3_BLOCKER_2_post_correction_successor_lane_assessment_v0_3.md` | `8b6e35e5add4f4c020429d9d3d1c422637fb35b2` | 57230 | `09240632a8b27ff5ce6cd001d89aef59211c0399f5084cfcfc73fcd234c5214a` |
| `research/brainvision/TORMENT_Brainvision_Stage_S3B_v0_3_BLOCKER_2_successor_lane_design_v0_2.md` | `42fa65134ddf7f76eb788737bc5ffac10e65ce58` | 36662 | `af31ec736f96a1038dfbda37505e61f7a57915c2eaaa21629fa1d3b67c5c8b20` |
| `research/brainvision/TORMENT_Brainvision_Stage_S3B_v0_3_BLOCKER_2_prepare_paths_input_preparation_blocked_by_governance_identity_v0_2.md` | `4316a8bd5098213e855ec8346588b9db9d2e706f` | 15212 | `ab5287bad985c6866f75eab579de906ca771b79890ab4f8ad290276e1cd7a226` |

## 4. Repository-Required Identity Object

The repository wrapper requires this top-level object for every wrapper payload,
including PREPARE_PATHS:

```text
execution_authorization_document_identity
```

Required fields:

```text
path
git_blob_oid
checked_out_byte_sha256
canonical_authorization_declaration_identity
authorization_status
```

Field classification:

| Field | Source | Wrapper validation | Classification |
| --- | --- | --- | --- |
| `path` | Supplied in canonical input; identifies the tracked authorization document | Resolved under repository root; external paths are rejected by current identity lookup | DIRECTLY_ESTABLISHED |
| `git_blob_oid` | Derived after document commit from `HEAD:<path>` | Must be 40 lowercase hex and equal current Git blob lookup | DIRECTLY_ESTABLISHED |
| `checked_out_byte_sha256` | Derived from exact checked-out file bytes | Must be 64 lowercase hex and equal current file bytes | DIRECTLY_ESTABLISHED |
| `canonical_authorization_declaration_identity` | Governance-defined declaration hash; see Section 7 | Must be 64 lowercase hex; wrapper does not recompute it against document contents | DIRECTLY_ESTABLISHED for validation, GOVERNANCE_DECISION_REQUIRED for preimage rule |
| `authorization_status` | Supplied in canonical input and declared in the document by governance | For later modes must equal ACTIVE; for PREPARE_PATHS any non-placeholder non-ACTIVE status is acceptable to repository code | DIRECTLY_ESTABLISHED for mode validation, GOVERNANCE_DECISION_REQUIRED for meaning |

Repository code could structurally accept a real historical tracked document
identity for PREPARE_PATHS if shape, blob, and bytes match. Successor-lane
governance prohibits historical reuse because it would misattribute historical
lane governance and provenance.

## 5. Repository Validation Semantics

Repository code establishes:

```text
execution_authorization_document_identity is mandatory for PREPARE_PATHS
field shape must match the five repository-defined fields
path, git_blob_oid, and checked_out_byte_sha256 are validated against the current repository working tree and HEAD
canonical_authorization_declaration_identity is validated only as 64 lowercase hex
authorization_status is ACTIVE-gated only for PREFLIGHT_ONLY and EXECUTE_EXACT_SINGLE_RUN
document contents are identity-bound but not Markdown-parsed by the wrapper
filename, directory, and document schema are governance conventions, not wrapper-enforced
Markdown can lawfully serve as the tracked identity source because the wrapper needs path, Git blob, and bytes, not Markdown structure
```

Repository code does not recompute the document declaration identity. Governance
must define and enforce that rule before accepting a future canonical input.

## 6. Governance Requirements

The fresh successor authorization document must satisfy governance requirements
not enforced by repository code:

```text
fresh successor-lane provenance
no historical authorization document identity reuse
no historical canonical declaration identity reuse
human-readable authorization scope
explicit authorized runner mode: PREPARE_PATHS only
explicit prohibited modes: PREFLIGHT_ONLY and EXECUTE_EXACT_SINGLE_RUN
document status that cannot be mistaken for later-mode active authority
review status separated from invocation authorization
governance acceptance separated from document creation
single-use or retry policy for the future canonical input
supersession and retirement rules
clear declaration identity rule
deterministic Markdown extraction rule
canonical JSON parse and serialization rule
```

Governance must not treat a structurally valid canonical input as authorized
for invocation until the canonical input has been prepared, frozen,
independently reviewed, governance-accepted, and explicitly authorized for
invocation.

## 7. Canonical Declaration Identity Rule

The exact governance rule recommended by this design is:

```text
canonical_authorization_declaration_identity
=
SHA-256(
    canonical_json_bytes(
        SUCCESSOR_AUTHORIZATION_DECLARATION
        excluding canonical_authorization_declaration_identity
    )
)
```

The canonical declaration object MUST NOT contain a
`canonical_authorization_declaration_identity` key.

Equivalently, if a drafting representation contains that key, it MUST be
removed before canonicalization and hashing.

This rule is non-circular. It mirrors the repository analogue:

```text
authorization_input_identity is derived from the authorization payload excluding
authorization_input_identity itself
```

The declaration preimage must exclude all post-commit and downstream identities,
including:

```text
document Git blob OID
document checked-out byte SHA-256
containing Git commit SHA
future canonical input identity
execution_authorization_identity
run identity
result-directory identity
path_model
authority-entry path
result-directory path
canonical_authorization_declaration_identity
```

Those identities are unavailable before declaration freezing or would create
unnecessary coupling to downstream lane instantiation. No fresh declaration
identity is derived in this correction.

## 8. Canonical JSON Rules

The future document's canonical declaration bytes must be produced by the same
canonical byte convention as repository `canonical_json_bytes`:

```text
UTF-8 encoding
sorted object keys
separators "," and ":"
ensure_ascii false
allow_nan false
no trailing newline
duplicate object keys rejected
exactly one JSON value
no trailing data
no comments
no placeholders
no synthetic or sentinel values
```

The declaration must be reparsed before accepting its identity using constraints
equivalent to the repository's canonical JSON loader:

```text
UTF-8 bytes only
UTF-8 BOM rejected
duplicate JSON object keys rejected
non-finite JSON numbers rejected
top-level value must be exactly one JSON object
raw extracted bytes must equal canonical_json_bytes(parsed_object)
```

Numeric guidance:

```text
prefer integers or strings where possible
do not use floating-point values unless a repository-defined canonical
representation exists
```

If any parser, serializer, or byte comparison result differs, the declaration
identity is not accepted and the document must not be used in a canonical input.

## 9. Deterministic Markdown Extraction Rule

The future Markdown authorization document must contain exactly one fenced code
block whose info string is exactly:

```text
SUCCESSOR_AUTHORIZATION_DECLARATION_CANONICAL_JSON
```

Required fence form:

````text
```SUCCESSOR_AUTHORIZATION_DECLARATION_CANONICAL_JSON
{...canonical JSON...}
```
````

Extraction rule:

```text
exactly one matching fence is required
zero matching fences reject
more than one matching fence rejects
fence contents are UTF-8 JSON bytes only
no prose inside the fence
the Markdown newline immediately before the closing fence is excluded from the declaration bytes
extracted bytes are reparsed and reserialized canonically
reserialized bytes must be byte-identical to extracted bytes
no trailing newline inside the canonical payload
```

The declaration bytes are the bytes between the newline after the opening fence
and the byte immediately before the Markdown newline that precedes the closing
fence. The closing-fence line and its preceding Markdown line break are not part
of the declaration bytes.

## 10. Authorization Status Recommendation

Recommended first status:

```text
PREPARED_NOT_ACTIVE
```

Semantics:

```text
PREPARED_NOT_ACTIVE is governance-defined.
Repository code treats any non-ACTIVE status as acceptable for PREPARE_PATHS if other validation passes.
PREFLIGHT_ONLY and EXECUTE_EXACT_SINGLE_RUN require ACTIVE and therefore reject PREPARED_NOT_ACTIVE.
```

Status assessment:

| Status | Repository acceptance for PREPARE_PATHS | Governance meaning | Later-mode reuse risk | Later revision required | Rebinding consequence |
| --- | --- | --- | --- | --- | --- |
| `PREPARED_NOT_ACTIVE` | Accepted if otherwise valid | Prepared for PREPARE_PATHS review and possible invocation only | Low; later modes reject non-ACTIVE | Yes, separate ACTIVE artifact required | Later ACTIVE inputs bind a distinct document |
| `PREPARE_PATHS_ONLY` | Likely accepted if non-placeholder | Clear scope but no historical precedent | Low | Yes | Requires new governance vocabulary |
| `PREPARE_PATHS_AUTHORIZED` | Likely accepted if non-placeholder | Risks collapsing document status with invocation authorization | Medium operator-confusion risk | Yes | Requires new governance vocabulary |
| `ACTIVE` | Accepted | Overstates later-mode readiness for a path-preparation document | High | Not for status, but unsafe | Avoid for first document |

Recommended later ACTIVE strategy:

```text
separate-path later ACTIVE authorization document
```

Rationale:

```text
preserves immutability
preserves historical auditability
avoids changing the PREPARE_PATHS document blob and byte identity
prevents accidental semantic upgrade of the original document
forces later canonical inputs to bind a distinct ACTIVE governance artifact
```

This is a recommended governance decision, not repository enforcement.

## 11. AUTHORIZED_PREPARATION_DOCUMENTS Interaction

The retained module defines `AUTHORIZED_PREPARATION_DOCUMENTS` as a fixed set of
historical preparation/governance document paths. The proposed successor path is
not currently included:

```text
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_SUCCESSOR_PREPARE_PATHS_EXECUTION_AUTHORIZATION_v0.1.md
```

Determinations:

| Question | Determination |
| --- | --- |
| Is inclusion required for direct `execution_authorization_document_identity` validation? | NO. The wrapper validates `execution_authorization_document_identity` through path, Git blob, and checked-out byte SHA validation, not through `AUTHORIZED_PREPARATION_DOCUMENTS`. |
| Is inclusion required for `document_identity_inventory` validation? | NO for current wrapper validation. `_validate_identity_inventory` validates each supplied path/blob/SHA/optional length and does not consult `AUTHORIZED_PREPARATION_DOCUMENTS`. |
| Is inclusion required by another retained identity inventory? | INSUFFICIENT_EVIDENCE. Future canonical input construction or governance may require the document in a controlling-document inventory, but current wrapper validation does not prove that requirement. |
| Would adding the document to `AUTHORIZED_PREPARATION_DOCUMENTS` require implementation change? | YES if that exact fixed constant must include the path, because it is source code. NO for merely adding the document to a future canonical input's `document_identity_inventory`. |
| Can the successor PREPARE_PATHS payload bind the tracked document directly without inventory amendment? | YES for direct `execution_authorization_document_identity` validation, based on path/blob/byte validation. |

This task does not modify the inventory or implementation. If future canonical
input construction requires the document in another fixed inventory, that is a
later blocker and must not be silently assumed away.

## 12. Tracked Source And Active Projection

Tracked repository document:

```text
governance source of truth
```

External active-authorization projection:

```text
not required for PREPARE_PATHS unless separately approved
```

External path alone:

```text
cannot satisfy Git blob validation
```

Recommended separation:

```text
tracked docs/ Markdown = governance source of truth
external active root = later projection/invocation artifact location only, if separately approved
```

The active-root projection policy is deferred. It is not a prerequisite for
creating the tracked PREPARE_PATHS authorization document.

## 13. HEAD-Binding Layers

Baseline and symbolic states:

```text
ACCEPTED_GOVERNANCE_BLOCKER_BASELINE_HEAD:
068c486ceba8e62efc866508dbecaec4fe6d9718

ACCEPTED_AUTHORIZATION_DOCUMENT_DESIGN_HEAD:
NOT_YET_CREATED

ACCEPTED_AUTHORIZATION_DOCUMENT_HEAD:
NOT_YET_CREATED

PREPARE_PATHS_CANONICAL_INPUT_BINDING_HEAD:
NOT_YET_AVAILABLE
```

Before PREPARE_PATHS canonical input preparation:

```text
HEAD == origin/main == ACCEPTED_AUTHORIZATION_DOCUMENT_HEAD
working tree clean
.git/index.lock absent
```

At that HEAD, recompute:

```text
authorization-document Git blob OID
authorization-document checked-out byte SHA-256
canonical declaration identity
all static identities
all authorized source identities
all tracked governing document identities
repository-state fields
```

No canonical input may bind to:

```text
068c486ceba8e62efc866508dbecaec4fe6d9718
```

after the design and authorization documents are committed.

## 14. Mandatory Lifecycle Sequence

Mandatory sequence:

```text
AUTHORIZATION_DOCUMENT_DESIGN_v0_2_COMPLETE
-> INDEPENDENT_DESIGN_REVIEW_ACCEPTED
-> DESIGN_COMMITTED_AND_PUSHED
-> FINAL_DESIGN_BASELINE_RECONFIRMED
-> AUTHORIZATION_DOCUMENT_PREPARED_NOT_ACTIVE
-> AUTHORIZATION_DOCUMENT_INDEPENDENTLY_REVIEWED
-> AUTHORIZATION_DOCUMENT_COMMITTED_AND_PUSHED
-> AUTHORIZATION_DOCUMENT_IDENTITY_RECOMPUTED
-> PREPARE_PATHS_INPUT_PREPARATION_AUTHORIZED
-> PREPARE_PATHS_INPUT_PREPARED
-> PREPARE_PATHS_INPUT_INDEPENDENTLY_REVIEWED
-> PREPARE_PATHS_GOVERNANCE_ACCEPTED
-> PREPARE_PATHS_AUTHORIZED_FOR_INVOCATION
-> PREPARE_PATHS_INVOKED
-> PATHS_PREPARED
-> AUTHORIZATION_DOCUMENT_RETIRED_OR_PRESERVED_AS_CONSUMED_PREPARATION_RECORD
```

Invocation authorization occurs only after:

```text
canonical input prepared
canonical input frozen
canonical input independently reviewed
PREPARE_PATHS governance accepted
```

This design task stops before:

```text
AUTHORIZATION_DOCUMENT_PREPARED_NOT_ACTIVE
```

## 15. Transition Table

| Transition | Allowed actor | Required inputs | Required identities | Created artifacts | Status change | Authority consumed | Runner mode | Failure disposition | Retry or retirement rule |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `AUTHORIZATION_DOCUMENT_DESIGN_v0_2_COMPLETE -> INDEPENDENT_DESIGN_REVIEW_ACCEPTED` | Independent reviewer / Hilmir governance | v0.2 design exact bytes | v0.2 byte SHA-256 and path | Review acceptance record if approved | Design becomes independently accepted | None | None | Reject or request v0.3 | Retry by superseding design, not editing accepted bytes |
| `INDEPENDENT_DESIGN_REVIEW_ACCEPTED -> DESIGN_COMMITTED_AND_PUSHED` | Hilmir | Accepted v0.2 design | v0.2 path and byte SHA-256 | Git commit and push | Design becomes tracked | None | None | Stop on Git mismatch, dirty tree, or push failure | Retry only after clean state reconfirmation |
| `DESIGN_COMMITTED_AND_PUSHED -> FINAL_DESIGN_BASELINE_RECONFIRMED` | Hilmir / operator | Pushed design commit | HEAD and origin/main equality | Baseline verification record | `ACCEPTED_AUTHORIZATION_DOCUMENT_DESIGN_HEAD` becomes known | None | None | Stop if HEAD != origin/main | Retry after synchronization |
| `FINAL_DESIGN_BASELINE_RECONFIRMED -> AUTHORIZATION_DOCUMENT_PREPARED_NOT_ACTIVE` | Separately authorized docs task | Accepted design HEAD and governance decisions | Design HEAD, accepted document path, declaration rule | Future PREPARED_NOT_ACTIVE Markdown candidate | Authorization document candidate exists but is untracked | None | None | Stop on unresolved governance or wrong path | Supersede candidate before review |
| `AUTHORIZATION_DOCUMENT_PREPARED_NOT_ACTIVE -> AUTHORIZATION_DOCUMENT_INDEPENDENTLY_REVIEWED` | Independent reviewer / Hilmir governance | Future document exact bytes | Document byte SHA-256, declaration preimage hash candidate | Review acceptance if approved | Document becomes independently reviewed | None | None | Reject on content, status, or declaration-rule defect | Retry by producing a new document candidate |
| `AUTHORIZATION_DOCUMENT_INDEPENDENTLY_REVIEWED -> AUTHORIZATION_DOCUMENT_COMMITTED_AND_PUSHED` | Hilmir | Independently reviewed document | Document path and reviewed byte SHA-256 | Git commit and push | Document becomes tracked | None | None | Stop on dirty tree, mismatch, or push failure | Retry after clean state reconfirmation |
| `AUTHORIZATION_DOCUMENT_COMMITTED_AND_PUSHED -> AUTHORIZATION_DOCUMENT_IDENTITY_RECOMPUTED` | Hilmir / operator | Clean synchronized document HEAD | HEAD, origin/main, document path | Identity report | `ACCEPTED_AUTHORIZATION_DOCUMENT_HEAD` and document blob/SHA become known | None | None | Stop on mismatch or untracked document | Recompute only after synchronization; supersede on content change |
| `AUTHORIZATION_DOCUMENT_IDENTITY_RECOMPUTED -> PREPARE_PATHS_INPUT_PREPARATION_AUTHORIZED` | Governance | Identity report and accepted declaration rule | Document path, Git blob, byte SHA, declaration identity, HEAD | Authorization to prepare canonical PREPARE_PATHS input | Input preparation becomes authorized | None | None | Stop if governance rejects | Retry requires fresh governance acceptance |
| `PREPARE_PATHS_INPUT_PREPARATION_AUTHORIZED -> PREPARE_PATHS_INPUT_PREPARED` | Separately authorized preparation task | Clean repo at authorization-document HEAD and Windows identities | Static identities, source identities, document identities, root identities, repository state | Canonical PREPARE_PATHS input candidate | Input exists and is frozen candidate | None | None | Stop on identity mismatch or path collision | Supersede candidate; do not repair in place |
| `PREPARE_PATHS_INPUT_PREPARED -> PREPARE_PATHS_INPUT_INDEPENDENTLY_REVIEWED` | Independent reviewer | Frozen canonical input bytes | Input SHA-256, authorization_input_identity, document identity | Review acceptance if approved | Input becomes independently reviewed | None | None | Reject on byte or identity defect | Retry by preparing a new canonical input candidate |
| `PREPARE_PATHS_INPUT_INDEPENDENTLY_REVIEWED -> PREPARE_PATHS_GOVERNANCE_ACCEPTED` | Hilmir governance | Independently reviewed input | Reviewed input identity and document identity | Governance acceptance record | PREPARE_PATHS governance accepted | None | None | Stop if not accepted | Retry requires new review or governance correction |
| `PREPARE_PATHS_GOVERNANCE_ACCEPTED -> PREPARE_PATHS_AUTHORIZED_FOR_INVOCATION` | Hilmir governance | Governance-accepted canonical PREPARE_PATHS input | Frozen input SHA-256, authorization_input_identity, accepted HEAD | Invocation authorization record | Invocation becomes authorized | None | None | Stop if authorization not exact | Retry only under explicit fresh governance |
| `PREPARE_PATHS_AUTHORIZED_FOR_INVOCATION -> PREPARE_PATHS_INVOKED` | Hilmir only | Independently reviewed and governance-accepted canonical PREPARE_PATHS input | Exact input path, input SHA-256, authorization_input_identity, accepted HEAD | Wrapper invocation output | Invocation attempted | None | PREPARE_PATHS | Fail closed | Retry only under explicit fresh governance; identity/path collisions may retire candidate lane |
| `PREPARE_PATHS_INVOKED -> PATHS_PREPARED` | Wrapper result only | PREPARE_PATHS invocation result | Wrapper terminal result identity and output bytes | Path-preparation result record | Paths prepared only if wrapper result establishes it | None | PREPARE_PATHS | Fail closed unless wrapper reports preparation complete | No manual promotion; retry requires fresh governance |
| `PATHS_PREPARED -> AUTHORIZATION_DOCUMENT_RETIRED_OR_PRESERVED_AS_CONSUMED_PREPARATION_RECORD` | Governance | Wrapper-established PATHS_PREPARED state | PREPARE result identity, input identity, document identity | Retirement or preservation record | PREPARE document no longer authorizes invocation | None | None | Stop if evidence incomplete | Preserve as consumed preparation record; later ACTIVE uses separate path |

Every transition row includes required identities and an explicit retry or
retirement rule. No global retry rule substitutes for the table.

## 16. PREPARE_PATHS Relationship

The future PREPARE_PATHS canonical input may bind the recommended document only
after:

```text
the document is independently reviewed
the document is committed and pushed
HEAD == origin/main == ACCEPTED_AUTHORIZATION_DOCUMENT_HEAD
the document path, Git blob, and checked-out SHA-256 are recomputed
the declaration identity rule is governance-accepted
the canonical input is prepared and frozen
the canonical input is independently reviewed
PREPARE_PATHS governance is accepted
Hilmir authorizes invocation
```

The PREPARE_PATHS document status remains:

```text
PREPARED_NOT_ACTIVE
```

PREPARE_PATHS may only be established by wrapper invocation and wrapper result.
Manual filesystem state, reviewer expectation, or design text cannot establish
PATHS_PREPARED.

## 17. Later PREFLIGHT And Execution Relationship

PREFLIGHT_ONLY and EXECUTE_EXACT_SINGLE_RUN require:

```text
payload authorization_status = ACTIVE
execution_authorization_document_identity.authorization_status = ACTIVE
```

The PREPARE_PATHS document must not be reused or edited in place as later-mode
active authority. Later PREFLIGHT/execution should require:

```text
a separate-path ACTIVE successor authorization document committed at a later HEAD
```

That separate ACTIVE document changes the tracked document path, Git blob,
checked-out SHA-256, declaration identity, document inventory, and repository
binding HEAD. Later active canonical inputs must be regenerated and
independently reviewed after that commit.

## 18. Historical Precedent

Verified historical facts:

```text
historical PREPARE_PATHS wrapper mode: PREPARE_PATHS
historical top-level authorization_status: PREPARED_NOT_ACTIVE
historical execution_authorization_document_identity.authorization_status: PREPARED_NOT_ACTIVE
historical result: PREPARATION_COMPLETE
historical authoritative: false
historical authority consumed: false
historical retained execution: false
```

Historical records:

| Record | Path | Role | Blob | Bytes | SHA-256 |
| --- | --- | --- | --- | ---: | --- |
| Operator wrapper/path-preparation authorization | `docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_OPERATOR_WRAPPER_AND_PATH_PREPARATION_AUTHORIZATION_v0.1.md` | Historical PREPARED_NOT_ACTIVE preparation identity | `3680795472de8f0f14fe0365fca5ec1d39ff6069` | 19747 | `1a395b394db777af0f88953d33dd27f7cc9b245cc2472f19c2304e416eb35d8a` |
| Post-commit path-preparation findings | `docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_WRAPPER_POST_COMMIT_IDENTITY_AND_PATH_PREPARATION_FINDINGS_v0.1.md` | Reported PREPARE_PATHS accepted PREPARED_NOT_ACTIVE input | `9bde4e64f2e38805aa606879fd1c48c237a8c507` | 17508 | `add055b3c142c8f3cd4a54fdbba54902b50f89c8c1ec4f78efa0a63f3df8685c` |
| Exact inactive execution authorization | `docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_EXACT_INACTIVE_EXECUTION_AUTHORIZATION_v0.1.md` | Historical inactive artifact review | `814409af32f80ed0c1f9f00622bc5f7d087bd2f5` | 18027 | `e12b53849862b24d3905587ddf1fa9ce5d420428d30187973802fd3e02a1aa23` |
| Exact active execution authorization | `docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_EXACT_ACTIVE_EXECUTION_AUTHORIZATION_v0.1.md` | Historical ACTIVE Markdown design | `391ae715936f249deeb983bf506a2fe2f49efbbd` | 18941 | `8c4716a7b69153e72f6789e86ff07614211109e414001f843922713274448adb` |
| Active sequencing preparation authorization | `docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_POST_COMMIT_ACTIVE_SEQUENCING_IDENTITY_BINDING_AND_ACTIVE_MARKDOWN_PREPARATION_AUTHORIZATION_v0.1.md` | Historical later ACTIVE sequencing design | `5f638ec42ef01486746aedf4e964f2901f0f01a4` | 17820 | `31a934373db99c39b804dcaf2a980c4c5fa89935ca605e5087282ca0298120f4` |

Historical declaration identity:

```text
opaque governance-assigned value
whole-file hash: not equal
in-document preimage: not found
successor: must not copy this undocumented method
```

Precedent is evidence, not repository law.

## 19. Governance Decisions Recommended For Explicit Acceptance

Recommended governance decisions:

```text
1. canonical declaration self-exclusion rule
2. canonical JSON and deterministic extraction rules
3. PREPARED_NOT_ACTIVE as the first document status
4. separate-path later ACTIVE document strategy
5. tracked docs/ source-of-truth path
6. no external active projection required for PREPARE_PATHS
7. independent review before commit
8. separate invocation-governance acceptance after canonical input review
```

No artifact implementing these decisions is created during this correction.

## 20. Recommended Next Artifact

Recommended next artifact after this design is independently accepted and
committed:

```text
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_SUCCESSOR_PREPARE_PATHS_EXECUTION_AUTHORIZATION_v0.1.md
```

That artifact must be a tracked Markdown authorization document containing:

```text
document schema/version
successor-lane purpose
accepted design-head bindings
accepted blocker-assessment binding
PREPARE_PATHS-only scope
authorization_status = PREPARED_NOT_ACTIVE
exactly one SUCCESSOR_AUTHORIZATION_DECLARATION_CANONICAL_JSON fence
canonical declaration object excluding canonical_authorization_declaration_identity
explicit no-PREFLIGHT and no-execution authority
review/governance/invocation state fields
supersession and retirement fields
```

It must stop before canonical input creation, runner invocation, external active
projection, and authority creation.

## 21. Terminal Disposition

```text
ACCEPTED_GOVERNANCE_BLOCKER_BASELINE_HEAD:
068c486ceba8e62efc866508dbecaec4fe6d9718

ACCEPTED_AUTHORIZATION_DOCUMENT_DESIGN_HEAD:
NOT_YET_CREATED

ACCEPTED_AUTHORIZATION_DOCUMENT_HEAD:
NOT_YET_CREATED

PREPARE_PATHS_CANONICAL_INPUT_BINDING_HEAD:
NOT_YET_AVAILABLE

AUTHORIZATION_DOCUMENT_DESIGN_CREATED:
YES

AUTHORIZATION_DOCUMENT_CREATED:
NO

AUTHORIZATION_DOCUMENT_TRACKED:
NO

AUTHORIZATION_DOCUMENT_ACTIVE:
NO

EXECUTION_AUTHORIZATION_DOCUMENT_IDENTITY_AVAILABLE:
NO

PREPARE_PATHS_INPUT_CREATED:
NO

PREPARE_PATHS_AUTHORIZED:
NO

PREPARE_PATHS_INVOKED:
NO

PREFLIGHT_AUTHORIZED:
NO

EXECUTION_AUTHORIZED:
NO
```

Terminal classification:

```text
B. AUTHORIZATION_DOCUMENT_DESIGN_COMPLETE_WITH_GOVERNANCE_DECISIONS
```

Validation performed:

```text
git status
git rev-parse
git merge-base ancestry checks
targeted rg searches
targeted source reads of wrapper validation logic
targeted reads of AUTHORIZED_PREPARATION_DOCUMENTS
targeted historical governance document reads
hash and byte-length calculations for accepted and historical documents
static repository-versus-governance classification
```

No runner mode was invoked. No canonical input was created. No authorization
document was created. No external artifact was created.

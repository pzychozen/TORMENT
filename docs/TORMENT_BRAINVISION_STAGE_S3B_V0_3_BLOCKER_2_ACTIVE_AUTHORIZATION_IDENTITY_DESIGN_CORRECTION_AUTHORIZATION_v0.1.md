# TORMENT Brainvision Stage S3B v0.3
# BLOCKER-2 Active-Authorization Identity Sequencing Correction Authorization v0.1

## 0. Document Status

document_class = BLOCKER-2 active-authorization identity sequencing correction authorization
document_version = v0.1
document_scope = docs-only correction authorization
repository_commit_identity = 4673b7d9507b122d432ba77ea3e481ee570275e3
authorization_status = PREPARED_NOT_ACTIVE
active_execution_authorization_markdown_created = false
active_canonical_json_created = false
PREPARE_PATHS_executed = false
PREFLIGHT_ONLY_executed = false
EXECUTE_EXACT_SINGLE_RUN_executed = false
global_authority_consumed = false
local_gate_created = false
run_result_created = false
retained_completion_created = false
blocker_2_state = OPEN
blocker_4_started = false

This document authorizes the identity sequencing design for a later ACTIVE
authorization lane. It does not create ACTIVE authority, does not create the
future ACTIVE execution authorization Markdown, does not create the future
ACTIVE canonical JSON input, and does not authorize preflight or execution.

## 1. Purpose

The purpose of this document is to correct the activation identity sequence
after post-commit review found that a committed ACTIVE canonical JSON artifact
would stale its own `expected_head` by construction.

Selected design:

```text
commit and review an immutable ACTIVE execution authorization Markdown first
freeze the resulting synchronized repository commit as H_ACTIVE
generate the ACTIVE canonical JSON outside the repository after H_ACTIVE exists
keep that JSON external, uncommitted, exact-byte canonical, and supplied through
an operator-selected absolute CLI path
run no preflight or execution until later separate authorization
```

This is a sequencing correction. It is not a runtime implementation
authorization and not a schema-change authorization.

## 2. Baseline

Baseline verified before this document was created:

| Field | Value |
| --- | --- |
| repository root | `C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric` |
| branch | `main` |
| HEAD | `4673b7d9507b122d432ba77ea3e481ee570275e3` |
| origin/main | `4673b7d9507b122d432ba77ea3e481ee570275e3` |
| HEAD == origin/main | `true` |
| tracked modifications | `none` |
| staged changes | `none` |
| untracked files at start | exactly the post-commit inactive assessment |
| `.git/index.lock` | `absent` |

Starting untracked file:

```text
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_POST_COMMIT_INACTIVE_ARTIFACT_IDENTITY_AND_ACTIVE_PREPARATION_ASSESSMENT_v0.1.md
```

Expected final local inventory for this task:

```text
1 modified untracked assessment document
1 newly created untracked correction-authorization document
```

No file is staged, committed, or pushed by this authorization.

## 3. Scope

This document authorizes only:

```text
recording the active-authorization identity sequencing design
correcting malformed hex strings in the existing untracked post-commit inactive assessment
creating this docs-only correction-authorization document
authorizing a later separate task to prepare a distinct ACTIVE authorization Markdown
```

This document does not authorize:

```text
runtime code changes
wrapper code changes
schema changes
test changes
ACTIVE canonical JSON creation
future ACTIVE execution authorization Markdown creation
PREPARE_PATHS
PREFLIGHT_ONLY
EXECUTE_EXACT_SINGLE_RUN
authority activation
evidence-chain object creation
BLOCKER-2 closure
BLOCKER-4 start
```

## 4. Permanent Boundaries

Preserved:

```text
FORMAL_HOLD = active
Mode_0 = active
STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY
```

Brainvision remains:

```text
offline
quarantined
synthetic-only
non-production
non-service
non-kernel
non-memory-integrated
non-cognitive
non-autonomous
```

This document does not modify or authorize modification of:

```text
torment_service/kernel/
production TORMENT memory functionality
live service behaviour
prompt surfaces
action surfaces
autonomy
identity
truth selection
memory cognition
```

This document does not claim:

```text
rename atomicity
rename durability
power-loss persistence
general Windows support
production readiness
BLOCKER-2 closure
real-world Brainvision readiness
strong order sensitivity
scientific completion
```

## 5. BLOCKER State

| Blocker | State |
| --- | --- |
| BLOCKER-1 | closed within its exact bounded local-fixed-NTFS profile |
| BLOCKER-2 | `OPEN and active` |
| BLOCKER-3 | closed |
| BLOCKER-4 | open but inactive |

BLOCKER-4 is not begun by this document.

## 6. Accepted Review Finding

Claude independently accepted the substantive finding:

```text
ACTIVE_PREPARATION_REQUIRES_SEPARATE_IDENTITY_DESIGN_CORRECTION
```

Precise classification:

| Classification item | Value |
| --- | --- |
| repository-sequencing defect | `yes` |
| missing activation layer | `yes` |
| mathematical or cryptographic cycle | `no` |
| mandatory runtime/schema correction | `no` |

The defect is the ordering of Git commit identity versus the execution input's
bound `expected_head`. It is not a failure of the corrected Stage A -> Stage B
-> Stage C derivation graph.

## 7. Exact Dependency Chain

The execution identity dependency remains:

```text
expected_head
-> execution_authorization_identity
-> result_directory
-> result_directory_identity
-> run_identity
```

Separately, wrapper preflight and execution require:

```text
live HEAD == repository_identity.head
live origin/main == repository_identity.origin_main
HEAD == origin/main
```

The corrected retained identity graph remains acyclic because Stage A derives
`execution_authorization_identity` only from upstream authorization inputs and
does not include `result_directory_identity`, `run_identity`, or the derived
child result path. Stage B derives the result directory and
`result_directory_identity` after Stage A. Stage C derives `run_identity` after
Stage B. Stage C does not feed back into Stage A.

No fixed-point hashing, iterative convergence, placeholder substitution, or
self-hash process is required.

## 8. Why A Committed ACTIVE JSON Is Stale

A committed ACTIVE canonical JSON that binds the commit containing itself is
stale by construction:

```text
ACTIVE JSON binds HEAD = H
-> commit ACTIVE JSON
-> live HEAD becomes H+1
-> wrapper rejects because H+1 != H
```

The wrapper rejects this because it validates the live repository state against
the input's `repository_identity` before preflight or execution. The defect is
therefore a repository sequencing defect, not a cryptographic cycle in the
authorization identity graph.

Trying to solve this by amending, rebasing, mutating the JSON after commit, or
substituting a working-tree hash for a Git object identity is prohibited.

## 9. Why No Runtime Or Schema Correction Is Required

No runtime or schema correction is required for the selected design because the
wrapper already accepts an authorization-input JSON by filesystem path and
validates the canonical bytes and supplied identities. It does not require that
the authorization-input JSON be a committed Git artifact.

The wrapper binds and checks:

```text
authorization-input canonical JSON bytes
authorization_input_identity
payload authorization_status
payload wrapper_mode
repository state
source identities
controlling authorization document identity
prepared roots and path model
operator identity
execution plan
one-shot authority and evidence absence before use
```

The wrapper additionally validates the controlling authorization Markdown
through `HEAD:<path>` Git blob identity and checked-out SHA-256. That Git object
binding applies to the authorization document, not to the external ACTIVE JSON
input file.

Therefore the correction is an authorized sequencing architecture:

```text
commit the ACTIVE Markdown first
freeze H_ACTIVE
generate external ACTIVE JSON after H_ACTIVE exists
keep repository HEAD unmoved until preflight and execution
```

## 10. Selected Architecture

### 10.1 Immutable Committed ACTIVE Authorization Markdown

A future, separately authorized task will create an ACTIVE authorization
Markdown inside the repository. That future Markdown will:

```text
declare authorization_status = ACTIVE
bind the exact execution plan
bind the exact repository baseline
bind the prepared roots
bind the execution surface
bind the operator identity
bind one-shot semantics
remain non-executable by itself
```

That Markdown must be independently reviewed and committed before generation of
the ACTIVE canonical JSON. Its repository-relative path, committed Git blob,
checked-out SHA-256, authorization status, and canonical authorization
declaration identity will be bound through
`execution_authorization_document_identity`. Its byte length is not inherently
part of `execution_authorization_document_identity`; the future ACTIVE
authorization Markdown must also be included in `document_identity_inventory`
with exact path, Git blob, checked-out SHA-256, and byte length.

### 10.2 External Uncommitted ACTIVE Canonical JSON

After the ACTIVE authorization Markdown is committed, the operator will freeze:

```text
H_ACTIVE = HEAD == origin/main
```

A future, separately authorized task will then generate the ACTIVE canonical
JSON outside the repository. The external JSON must:

```text
use wrapper authorization-input schema v0.2
set authorization_status = ACTIVE
set wrapper_mode = EXECUTE_EXACT_SINGLE_RUN
retain authoritative = true
bind H_ACTIVE as expected_head
bind H_ACTIVE as expected_origin_main
bind the committed ACTIVE authorization Markdown identity
include the committed ACTIVE authorization Markdown in document_identity_inventory
recompute execution_authorization_identity
recompute result_directory
recompute result_directory_identity
recompute run_identity
recompute authorization_input_identity
remain outside the Git repository
remain uncommitted
remain exact-byte canonical
be supplied through an operator-selected absolute CLI path
```

The external JSON input location is not chosen by this document. It must be
separately recorded and authorized later as an operator-selected and
independently reviewed absolute CLI path. That path is an operational control;
the current wrapper does not include the authorization-input file path in
`authorization_input_identity` or another wrapper identity block.

### 10.3 Frozen Execution Baseline

After the ACTIVE authorization Markdown is committed and the external ACTIVE
JSON is generated, the following are prohibited before `PREFLIGHT_ONLY` and,
if later accepted, `EXECUTE_EXACT_SINGLE_RUN`:

```text
commit
amend
rebase
merge
source modification
document modification
branch movement
```

The live repository must remain:

```text
HEAD == origin/main == H_ACTIVE
working tree clean
.git/index.lock absent
```

### 10.4 Optional Post-Run Receipt

A post-run committed receipt may be produced only after the one-shot execution
and evidence assessment. It is an audit projection, not activation authority.

It must not retroactively modify:

```text
the ACTIVE authorization Markdown
the external ACTIVE JSON
execution_authorization_identity
result_directory
result_directory_identity
run_identity
authority-consumption truth
```

## 11. External JSON Control

The wrapper does not require the authorization-input JSON to be a committed Git
artifact.

The wrapper binds:

```text
repository state
source identities
controlling authorization document identity
prepared roots
operator identity
execution plan
canonical input identity
```

It does not require the ACTIVE JSON to bind its own Git blob.

Therefore:

```text
ACTIVE JSON Git blob identity = MUST NOT BE BOUND AT THIS LAYER
```

This avoids:

```text
self-reference
fixed-point hashing
post-commit mutation
commit amendment
stale expected_head
```

The external JSON is not less controlled merely because it is uncommitted. Its
control comes from:

```text
exact canonical bytes
exact-byte SHA-256
authorization_input_identity
operator-selected and independently recorded absolute CLI path
frozen HEAD
bound ACTIVE Markdown
wrapper validation
operator/process/attempt locks
one-shot authority registry
```

The operator-selected CLI path is a procedural review and invocation control,
not a cryptographic identity field. The wrapper does not reject identical valid
canonical bytes solely because they are supplied from another path.

## 12. Identity Impact Matrix

| Identity element | Status | Handling |
| --- | --- | --- |
| historical inactive execution_authorization_identity | historical only | Must not be reused as ACTIVE execution authority. |
| historical inactive result_directory | historical only | Must not be reused as ACTIVE result location. |
| historical inactive result_directory_identity | historical only | Must not be reused as ACTIVE result-directory identity. |
| historical inactive run_identity | historical only | Must not be reused as ACTIVE run identity. |
| current-HEAD projection from `4673b7d...` | analysis only | Useful sequencing evidence, not final ACTIVE authority. |
| future ACTIVE authorization Markdown identity | recompute after commit | Requires repository-relative path, `HEAD:<path>` Git blob, byte SHA-256, ACTIVE status, and declaration identity through `execution_authorization_document_identity`; byte length is additionally bound through `document_identity_inventory`. |
| future external ACTIVE JSON identity | recompute after H_ACTIVE | Requires canonical byte SHA-256 and authorization_input_identity. |
| future execution_authorization_identity | recompute after H_ACTIVE | Depends on final expected_head and active document identity. |
| future result_directory | recompute after H_ACTIVE | Derived from final execution_authorization_identity. |
| future result_directory_identity | recompute after H_ACTIVE | Derived after final result_directory is known. |
| future run_identity | recompute after H_ACTIVE | Derived after final result_directory_identity is known. |
| repository-state identity | recompute after H_ACTIVE | Must bind live HEAD/origin/main and clean state. |
| ACTIVE JSON Git blob identity | `MUST NOT BE BOUND AT THIS LAYER` | The input remains external and uncommitted by design. |

## 13. Historical Inactive Identities

The committed inactive identities remain valid historical evidence only:

```text
execution_authorization_identity:
66028ecbdaceb94b1789225c7752fa9ac9796c5fea41e11017264d17c0752785

result_directory:
C:\TORMENT\brainvision_retained_results\blocker2_s3b_v0_3\66028ecbdaceb94b1789225c7752fa9ac9796c5fea41e11017264d17c0752785

result_directory_identity:
31072e5528843492aa4666174f171460f3ad65602ace60fa56ec4eceeb1c2721

run_identity:
889090b759549449daa6b06f2e72dbf97564ce55fc18448271915e3d3c1354ad
```

They must not be reused as ACTIVE execution identities.

## 14. Current Projection Status

The current-HEAD projection from:

```text
4673b7d9507b122d432ba77ea3e481ee570275e3
```

may remain recorded as analysis only:

```text
projected execution_authorization_identity:
bbf5b68dbf5dadff20de14c20d3778259a5dad439a6866fc099b64d1d18cbf9b

projected result_directory_identity:
eda036e3dea9da43770d478ef6a9c212a23f4926fc1b9e406aff3d28b71cf4ae

projected run_identity:
ea1bb3a6765cbd1cf97dde5c3fff37853f7565492dabd119293d81b2cd9aa70d
```

This projection is not final ACTIVE authority. Committing this correction
authorization document will change HEAD again, and the future ACTIVE identities
must be recomputed only after the future ACTIVE authorization Markdown is
committed and `H_ACTIVE` is frozen.

## 15. Future ACTIVE Identity Timing

The following must be recomputed only after the future ACTIVE authorization
Markdown is committed and `H_ACTIVE` is frozen:

```text
execution_authorization_identity
result_directory
result_directory_identity
run_identity
authorization_input_identity
execution_authorization_document_identity
repository-state identity
```

`execution_authorization_document_identity` for the ACTIVE Markdown becomes
available after the ACTIVE Markdown is committed because the committed
`HEAD:<path>` Git blob and checked-out SHA-256 can then be observed. After
`H_ACTIVE` is frozen, the external ACTIVE JSON incorporates that document
identity and the `document_identity_inventory` entry carrying the Markdown byte
length. The ACTIVE Markdown does not need to know `H_ACTIVE` while being
authored, so this requirement introduces no self-reference.

The following may remain unchanged if implementation and environment remain
unchanged:

```text
retained orchestration policy identity
native-helper policy identity
retained schema identity
case-set identity
case order
A6 false
executor selector
fault-injection setting
prepared-root identities
host identity
volume identity
operator identity
single-attempt declaration
execution-surface identities
```

Every supposedly unchanged identity must still be reverified at `H_ACTIVE`.

## 16. Security Invariants

The selected design preserves:

```text
one-shot global authority consumption
no retry
no resume
no overwrite
no repair after authority consumption
no executor substitution
exact case set A1,A2,A3,A5
exact case order A1,A2,A3,A5
A6 = false
fault injection disabled
fixed prepared local NTFS roots
cross-location replay resistance
repository/source identity binding
operator identity binding
single-process lock
single-attempt lock
four-object evidence chain
RUN_RESULT cannot declare retained_execution=true
RETAINED_COMPLETION is the sole record permitted to declare retained_execution=true
authoritative completion requires durable verified RUN_RESULT plus durable verified RETAINED_COMPLETION
```

The correction must not introduce:

```text
self-hash
fixed-point hashing
placeholder identities
post-commit mutation
commit amendment to chase identity
working-tree hash substituted for Git blob identity
authorization by file presence
authorization by branch name
authorization by unbound current HEAD
```

## 17. Prohibited Alternatives

Rejected alternatives:

| Alternative | Reason rejected |
| --- | --- |
| committed ACTIVE JSON binding its containing commit | Stales `expected_head` because committing the JSON changes HEAD. |
| amend until identity appears to match | Prohibited commit amendment and identity chasing. |
| fixed-point hashing | Not required and not authorized. |
| self-hash of ACTIVE JSON Git blob | The JSON must not bind its own Git blob at this layer. |
| placeholder expected_head | Prohibited placeholder identity. |
| working-tree SHA substituted for Git blob | Would conflate byte SHA with committed Git object identity. |
| authorization by file presence | The wrapper must validate canonical bytes and identities. |
| authorization by branch name only | Branch name is insufficient without exact HEAD/origin binding. |
| authorization by unbound current HEAD | Current HEAD must be explicitly frozen and bound as H_ACTIVE. |

## 18. Future Sequencing

This document authorizes only the sequencing design and later preparation of a
distinct ACTIVE authorization Markdown. It conceptually authorizes no operation
after step 2 below.

Required future sequence:

```text
1. Commit the corrected assessment and this correction-authorization document.
2. Collect their committed identities.
3. Prepare a separate work authorization for the ACTIVE authorization Markdown.
4. Create and adversarially review the ACTIVE authorization Markdown.
5. Commit the ACTIVE authorization Markdown.
6. Freeze HEAD == origin/main as H_ACTIVE.
7. Generate the external ACTIVE canonical JSON outside the repository.
8. Independently review its bytes, identities, path, and ACTIVE semantics.
9. Run PREFLIGHT_ONLY only under a separate explicit authorization.
10. Review preflight evidence.
11. Run EXECUTE_EXACT_SINGLE_RUN exactly once only under a separate explicit authorization.
12. Assess the four-object evidence chain.
13. Assess BLOCKER-2 closure.
14. Prepare a fresh-chat handoff before BLOCKER-4.
```

This task authorizes none of steps 3 through 14 operationally.

## 19. Real Evidence State

No real evidence-chain object is created by this document. The historical
inactive evidence paths remain absent:

| Object | Path | Required state |
| --- | --- | --- |
| derived result directory | `C:\TORMENT\brainvision_retained_results\blocker2_s3b_v0_3\66028ecbdaceb94b1789225c7752fa9ac9796c5fea41e11017264d17c0752785` | `ABSENT` |
| GLOBAL_AUTHORITY_ENTRY | `C:\TORMENT\brainvision_authority\blocker2_s3b_v0_3\66028ecbdaceb94b1789225c7752fa9ac9796c5fea41e11017264d17c0752785.global_authority_entry.canonical.json` | `ABSENT` |
| LOCAL_GATE_ENTRY | `C:\TORMENT\brainvision_retained_results\blocker2_s3b_v0_3\66028ecbdaceb94b1789225c7752fa9ac9796c5fea41e11017264d17c0752785\gate_entry.canonical.json` | `ABSENT` |
| RUN_RESULT | `C:\TORMENT\brainvision_retained_results\blocker2_s3b_v0_3\66028ecbdaceb94b1789225c7752fa9ac9796c5fea41e11017264d17c0752785\run_result.canonical.json` | `ABSENT` |
| RETAINED_COMPLETION | `C:\TORMENT\brainvision_retained_results\blocker2_s3b_v0_3\66028ecbdaceb94b1789225c7752fa9ac9796c5fea41e11017264d17c0752785\retained_completion.canonical.json` | `ABSENT` |

Authority consumed:

```text
false
```

## 20. Limitations

This document is local and uncommitted until Hilmir commits it. The future
ACTIVE authorization Markdown identity, operator-selected external ACTIVE JSON
CLI location, authorization_input_identity, execution_authorization_identity,
result_directory, result_directory_identity, run_identity, and repository-state
identity are all unavailable until their proper future sequence points.

This document does not authorize direct ACTIVE JSON generation. It does not
authorize any wrapper mode invocation. It does not close BLOCKER-2.

## 21. Exact Stop Boundary

Stop after:

```text
correcting the four malformed hex strings in the existing untracked assessment
creating this docs-only correction-authorization document
validating canonical JSON parsing, hex lengths, evidence absence, and narrow tests
leaving both documents untracked
```

Do not stage, commit, push, amend, rebase, reset, stash, activate authority,
create ACTIVE JSON, create the future ACTIVE authorization Markdown, run
`PREPARE_PATHS`, run `PREFLIGHT_ONLY`, or run `EXECUTE_EXACT_SINGLE_RUN`.

## 22. Next Separately Authorized Task

After Hilmir commits the corrected assessment and this correction-authorization
document and collects their committed identities, prepare a separate work
authorization for the future ACTIVE execution authorization Markdown.

That next task must still be docs-only unless it explicitly receives a later
operational authorization. It must not create the external ACTIVE JSON, run
preflight, or execute the retained single run.

## 23. Final Disposition

```text
A. ACTIVE_IDENTITY_SEQUENCING_CORRECTION_AUTHORIZED_AND_READY_FOR_REVIEW
```

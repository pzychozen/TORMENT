# TORMENT Brainvision Stage S3B v0.3
# BLOCKER-2 Authoritative Retained Single-Run Assessment v0.1

## 0. Document Status

document_class = BLOCKER-2 authoritative retained single-run assessment

document_version = v0.1

document_mode = docs-only assessment

retained_run_executed = false

retained_artifact_created = false

implementation_modified = false

authorization_created = false

blocker_4_started = false

This document assesses whether the committed BLOCKER-2 absolute-path
`FileRenameInfo` control is scientifically and procedurally ready for a future
authoritative retained single-run authorization.

This document does not execute the control, does not invoke Windows integration
cases, does not create retained evidence, does not consume a one-run gate, does
not modify implementation or tests, does not authorize execution, and does not
close BLOCKER-2.

## 1. Assessment Question

Assessment question:

```text
Is the existing committed BLOCKER-2 absolute-path FileRenameInfo control ready
for a future authoritative retained single-run authorization, and what exact
boundary must such a later authorization adopt?
```

Answer:

```text
The evidence is scientifically useful and justifies preserving the retained-run
lane, but the current runner is not yet a retained-execution harness.
```

Distinctions:

| Category | Assessment |
|---|---|
| implementation readiness | The absolute-path control implementation is suitable as focused ephemeral implementation evidence, but it lacks retained-run machinery. |
| scientific usefulness | A retained single run would preserve bounded platform evidence for one admitted Windows fixture. |
| procedural readiness | Immediate run authorization is premature until narrow retained-execution preparation exists and is reviewed. |
| platform evidence value | High, but bounded to one exact Windows 10/11 local fixed NTFS fixture and selected A-cases. |
| BLOCKER-2 closure value | Supportive only. It can inform a later closure decision, but cannot close BLOCKER-2 by itself. |

Ephemeral success is not treated as automatic justification for retained
execution.

## 2. Authoritative Baseline

Baseline verified before this document was created:

```text
branch:
main

HEAD:
82d6fce1a6253fffd0bd2339415beefb1c8410ff

origin/main:
82d6fce1a6253fffd0bd2339415beefb1c8410ff

working tree:
clean

.git/index.lock:
absent
```

Relevant lineage:

```text
82d6fce docs(research): record blocker 2 absolute-path control findings
03727e7 research(brainvision): implement blocker 2 absolute-path control
e34d3d4 docs(research): authorize blocker 2 absolute-path control
9ab500f docs(research): assess blocker 2 absolute-path control
8af0ab8 docs(research): record blocker 2 promotion primitive findings
89f41a5 research(brainvision): implement blocker 2 promotion primitive validation
6c8b113 docs(research): authorize blocker 2 promotion primitive validation
5593640 docs(research): research blocker 2 Windows promotion primitive
031b06c docs(research): assess blocker 2 promotion ownership
d147624 docs(research): close blocker 1 directory durability
```

Reviewed committed documents:

```text
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_1_WINDOWS_DIRECTORY_DURABILITY_CLOSURE_ASSESSMENT_v0.1.md
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_SAME_VOLUME_NO_REPLACE_PROMOTION_AND_FINAL_OWNERSHIP_ASSESSMENT_v0.1.md
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_WINDOWS_SAME_VOLUME_NO_REPLACE_DIRECTORY_PROMOTION_PRIMARY_SOURCE_PRIMITIVE_RESEARCH_v0.1.md
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_BOUNDED_WINDOWS_SAME_VOLUME_NO_REPLACE_DIRECTORY_PROMOTION_PRIMITIVE_VALIDATION_AUTHORIZATION_v0.1.md
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_BOUNDED_WINDOWS_PROMOTION_PRIMITIVE_VALIDATION_IMPLEMENTATION_FINDINGS_v0.1.md
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_ABSOLUTE_PATH_FILERENAMEINFO_ISOLATING_CONTROL_ASSESSMENT_v0.1.md
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_NARROW_ABSOLUTE_PATH_FILERENAMEINFO_CONTROL_SPECIFICATION_AND_IMPLEMENTATION_AUTHORIZATION_v0.1.md
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_NARROW_ABSOLUTE_PATH_FILERENAMEINFO_CONTROL_IMPLEMENTATION_FINDINGS_v0.1.md
```

Reviewed committed implementation and tests:

```text
research/brainvision/validate_windows_same_volume_no_replace_promotion_v0_1.py
research/brainvision/test_validate_windows_same_volume_no_replace_promotion_v0_1.py
research/brainvision/test_validate_windows_same_volume_no_replace_promotion_integration_v0_1.py
```

Committed bytes and Git history are authoritative.

## 3. Preserved Boundaries

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

This assessment does not modify or propose integration with:

```text
torment_service/kernel/
production TORMENT memory functionality
live service behavior
prompt surfaces
action surfaces
autonomy
identity
truth selection
memory cognition
```

This assessment does not open:

```text
live capture
real gameplay
real video execution
production publication
production recovery
general live-test lanes
BLOCKER-4
```

Current blocker state remains:

```text
BLOCKER-1:
BLOCKER_1_CLOSED_WITHIN_AUTHORIZED_SYNTHETIC_OFFLINE_WINDOWS_LOCAL_FIXED_NTFS_TMP_PATH_SCOPE

BLOCKER-2:
OPEN

BLOCKER-3:
CLOSED_WITHIN_AUTHORIZED_SYNTHETIC_OFFLINE_STAGE_S3B_V0_3_SCOPE

BLOCKER-4:
OPEN AND SEPARATE
```

Publication remains a projection of the authoritative scientific result.

The authoritative durable scientific result remains:

```text
verified IMMUTABLE_SCIENTIFIC_BUNDLE
+
linked valid SCIENTIFIC_COMPLETION
```

Promotion and durability evidence remain linked platform evidence, not
scientific completion evidence.

J2 recovery must never reconstruct or claim an original J1 completion that was
not durably established.

## 4. Existing Evidence

RootDirectory-relative experiment:

```text
SetFileInformationByHandle
+
FileRenameInfo
+
FILE_RENAME_INFO
+
ReplaceIfExists = FALSE
+
non-NULL destination-parent RootDirectory
+
simple relative final name
```

Observed result:

```text
ERROR_INVALID_PARAMETER
87
```

Accepted classification:

```text
PRIMITIVE_VALIDATION_INDETERMINATE
```

The RootDirectory-relative primitive was neither validated nor falsified.

Prior policy identity:

```text
df91a9bcc3c5b37e938a086801dd2bca42f0290533a6cf2682055df475f663f3
```

Absolute-path control:

```text
RootDirectory = NULL
canonical fully qualified drive-qualified Win32 DOS absolute destination path
```

Control-policy identity:

```text
3d9b66a180fabf00c8bb6695c74fc9d69d21cd3ac9335cc5d2dc3a1169417531
```

Absolute-path implementation commit:

```text
03727e738bdb5dcd94ca63e958a9de39de25be43
```

Absolute-path findings commit:

```text
82d6fce1a6253fffd0bd2339415beefb1c8410ff
```

Accepted findings verdict:

```text
A. ACCEPT_ABSOLUTE_PATH_CONTROL_IMPLEMENTATION_FINDINGS_WITH_BLOCKER_2_REMAINING_OPEN
```

Ephemeral observations:

```text
A1:
CONTROL_VALIDATED_FOR_BOUNDED_EPHEMERAL_PROFILE

A2:
ERROR_ALREADY_EXISTS / 183
CONTROL_COLLISION_OBSERVED

A3:
ERROR_ALREADY_EXISTS / 183
CONTROL_COLLISION_OBSERVED

A4:
ERROR_ALREADY_EXISTS / 183
CONTROL_COLLISION_OBSERVED

A5:
source identity
==
retained source-handle identity
==
reopened final-path identity

A6:
ERROR_ALREADY_EXISTS / 183
CONTROL_COLLISION_OBSERVED
raw native error retained

A7:
rejected locally before native invocation

A8:
CONTROL_SKIPPED_FIXTURE_UNAVAILABLE
SECOND_VOLUME_UNAVAILABLE
```

Ephemeral test evidence:

```text
python -m py_compile:
passed

unit suite:
47 passed

focused Windows integration selection:
3 passed
```

This evidence is focused ephemeral implementation-test evidence only. No
authoritative retained execution has occurred.

## 5. Retained-Run Purpose

Proper retained-run purpose:

```text
Produce identity-bound retained platform evidence that the absolute-path
FileRenameInfo control behaves as observed under one exact admitted Windows
fixture and selected A-case subset.
```

The retained run should preserve:

```text
the exact repository identity
the exact control-policy identity
the exact source bytes used
the exact selected cases
the exact fixture profile
the exact path form
the exact native outcomes
the exact source/final/collision identities and manifests
the exact terminal status
the exact retained artifact hash
```

The retained-run purpose must not be framed as:

```text
proving general Windows rename support
proving atomicity
proving durability
proving power-loss persistence
closing BLOCKER-2 automatically
```

The narrow purpose is justified because the absolute-path control reached
positive transition and collision behavior ephemerally while the prior
RootDirectory-relative form returned `ERROR_INVALID_PARAMETER / 87`.

## 6. Case-by-Case A1-A8 Assessment

| Case | Decision | Gating role | Rationale |
|---|---|---|---|
| A1 | INCLUDE_IN_RETAINED_RUN | completion-gating | A1 is the minimal positive absolute-path same-volume directory transition. Without A1, the retained artifact would not preserve evidence that the native transition succeeds under the admitted fixture. |
| A2 | INCLUDE_IN_RETAINED_RUN | completion-gating | A2 covers existing destination directory preservation under `ReplaceIfExists = FALSE`, directly relevant to no-replace directory-set promotion. |
| A3 | INCLUDE_IN_RETAINED_RUN | completion-gating | A3 covers the occupied-final-name case where the existing destination is a file. This is bounded no-replace evidence for an alternate existing target type and should be retained with raw native error evidence. |
| A4 | EXCLUDE_FROM_RETAINED_RUN | not included | A4 is a concurrent destination-creation race. It is diagnostically interesting but introduces timing and ownership nondeterminism that is not needed for a single retained platform-evidence run. |
| A5 | INCLUDE_IN_RETAINED_RUN | completion-gating | A5 is the required source-to-final identity-continuity check after successful transition. It binds source identity, retained handle identity, final path identity, and content manifest continuity. |
| A6 | OPTIONAL_BUT_NON_GATING | diagnostic-only if selected | A6 overlaps A2/A3 collision evidence but explicitly exercises raw-error characterization against a collision fixture. It may be included to enrich evidence, but it must not be required for completion if A2/A3 already preserve raw collision errors. |
| A7 | EXCLUDE_FROM_RETAINED_RUN | not included | A7 is local pre-native validation. It should remain bound by source review and tests, not upgraded into authoritative native platform evidence. |
| A8 | EXCLUDE_FROM_RETAINED_RUN | not included | A8 currently reports `SECOND_VOLUME_UNAVAILABLE`. Including it would risk turning an unavailable diagnostic fixture into apparent retained success. Cross-volume rejection requires a separately admitted second-volume fixture and separate authorization. |

Selected retained case subset for a later authorization:

```text
completion-gating:
A1
A2
A3
A5

optional diagnostic:
A6

excluded:
A4
A7
A8
```

## 7. Proposed Gating Model

Completion-gating cases:

```text
A1
A2
A3
A5
```

Expected bounded outcomes:

```text
A1:
CONTROL_VALIDATED_FOR_BOUNDED_EPHEMERAL_PROFILE
source identity equals retained-handle identity equals final identity
content manifest preserved

A2:
CONTROL_COLLISION_OBSERVED
raw native error retained
destination directory identity and manifest preserved

A3:
CONTROL_COLLISION_OBSERVED
raw native error retained
existing file destination preserved

A5:
CONTROL_VALIDATED_FOR_BOUNDED_EPHEMERAL_PROFILE
source identity equals retained-handle identity equals final identity
content manifest preserved
```

Diagnostic-only case:

```text
A6:
optional raw-error characterization if selected by the later authorization
```

Skippability:

```text
No completion-gating included case may be skipped.

A6 may be omitted only if the later authorization excludes it from the selected
case set. If selected, its outcome must be recorded truthfully and must not
silently promote a skipped or unavailable result into completion evidence.

A4, A7, and A8 are excluded from the proposed retained run and must not affect
completion.
```

The gating model prevents a skipped or unavailable diagnostic case from
becoming successful retained completion.

## 8. Proposed Retained Artifact

Preferred artifact form:

```text
one immutable directory containing one canonical JSON terminal record and any
narrowly referenced evidence required by that record
```

The minimum required canonical JSON contents are:

```text
schema/version identity
run mode
retained_execution flag
terminal status
case selection
case outcomes
raw numeric native errors
raw symbolic native errors
fixture profile
path form
RootDirectory semantics
ReplaceIfExists semantics
source identity
destination-parent identity
fixture-root identity
same-volume evidence
filesystem evidence
drive-type evidence
content-manifest evidence
source-to-final identity evidence
collision-destination preservation evidence
policy declaration
policy identity
implementation source identities
test source identities where relevant
repository commit identity
execution environment declaration
timestamp semantics
artifact hash
artifact durability evidence
post-write reread verification evidence
```

Timestamp semantics should record wall-clock observation time as contextual
metadata only. Timestamps must not be part of the scientific identity unless a
later authorization gives a precise reason.

Artifact hash:

```text
The canonical JSON terminal record must include or be paired with a hash over
the canonical terminal payload. The artifact must be reread after persistence,
recanonicalized or byte-compared as specified, and rehashed to prove stability.
```

The artifact must not require unstable or unnecessary data such as machine
username, ambient environment variables unrelated to the fixture profile, or
full console logs unless a later authorization specifically binds them.

## 9. Required Identity Bindings

Mandatory before a retained run can be valid:

```text
repository HEAD
origin/main equality
working-tree cleanliness
control-policy declaration
control-policy identity
runner source blob identity
runner checked-out byte SHA-256
unit-test source blob identity
unit-test checked-out byte SHA-256
integration-test source blob identity
integration-test checked-out byte SHA-256
assessment identity
future authorization identity
fixture-profile identity
retained schema identity
selected case-set identity
execution environment declaration
```

Mandatory current identities verified here:

```text
repository HEAD:
82d6fce1a6253fffd0bd2339415beefb1c8410ff

origin/main:
82d6fce1a6253fffd0bd2339415beefb1c8410ff

prior RootDirectory-relative policy identity:
df91a9bcc3c5b37e938a086801dd2bca42f0290533a6cf2682055df475f663f3

absolute-path control-policy identity:
3d9b66a180fabf00c8bb6695c74fc9d69d21cd3ac9335cc5d2dc3a1169417531
```

Committed source blob identities verified here:

```text
research/brainvision/validate_windows_same_volume_no_replace_promotion_v0_1.py
Git blob:
1d892f7c8ab9571eae2ca55d22d1c13d7ba358e8

research/brainvision/test_validate_windows_same_volume_no_replace_promotion_v0_1.py
Git blob:
3eb2486cccf6b9e5daab8e4e5971f593779c7589

research/brainvision/test_validate_windows_same_volume_no_replace_promotion_integration_v0_1.py
Git blob:
5ccb5ea6bb4bd386f1329a10069b875e5a3daee4

docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_NARROW_ABSOLUTE_PATH_FILERENAMEINFO_CONTROL_IMPLEMENTATION_FINDINGS_v0.1.md
Git blob:
ac1111ee654a369675f43e88a2cf1e748774f7b7
```

Checked-out byte SHA-256 values verified here:

```text
research/brainvision/validate_windows_same_volume_no_replace_promotion_v0_1.py
d980d778c3cacd43841784cbc1e201f6e92d3bbe7d60f56472999b33913b605d

research/brainvision/test_validate_windows_same_volume_no_replace_promotion_v0_1.py
b6a23a227ac36019a32c80d941eadb8e467c4d0ede8ac4175856cb0c5ddf5246

research/brainvision/test_validate_windows_same_volume_no_replace_promotion_integration_v0_1.py
f904e037854d56f55b9d668392aa9d2c49248f3fd4f19b28ab566ccea4660743

docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_NARROW_ABSOLUTE_PATH_FILERENAMEINFO_CONTROL_IMPLEMENTATION_FINDINGS_v0.1.md
4d2a72311aa23397d39f88c1c2863c624aa01e4720b0e844015f6e881b2e49b7
```

Future identities not yet available:

```text
this assessment identity after commit
future authorization identity
retained schema identity
selected case-set identity
retained artifact identity
```

Those identities must be bound by the later preparation and authorization
chain before any retained execution.

A modified or dirty working tree must fail closed.

## 10. Repository and Environment Gate

Pre-run repository requirements:

```text
branch main
HEAD equals the exact authorized commit
HEAD equals origin/main
working tree clean
no .git/index.lock
no modified tracked source
no source blob mismatch
no checked-out byte SHA-256 mismatch
no untracked files inside authorized implementation, test, docs, or retained
evidence surfaces unless explicitly authorized as the output artifact path
```

Unrelated untracked files outside authorized evidence surfaces should not
invalidate the run by default, but they must be listed in preflight evidence and
must not be inside:

```text
research/brainvision/
docs/
retained result directory
torment_service/
production or publication surfaces
```

Supported execution profile:

```text
Windows 10/11 workstation
Windows Command Prompt
conda environment torment
local fixed drive
NTFS
ordinary existing non-reparse fixture root
isolated temporary root outside the repository
same-volume source and destination
absolute canonical drive-qualified Win32 DOS destination path
```

Exact OS build data should be recorded as contextual evidence. It must not be
used as a broad compatibility claim.

## 11. Single-Run and Gate-Consumption Semantics

Single run means:

```text
one process invocation
one admitted fixture root
one attempt per selected case
one retained terminal record
no rerun after native invocation begins
```

Authority states:

| State | Meaning |
|---|---|
| unconsumed | Authorization exists, but local preflight has not crossed the gate-consumption boundary. |
| entered | Local preflight passed and the gate-entry marker has been durably established immediately before the first native transition. |
| consumed successfully | The terminal artifact is durably established, reread, reverified, and all gating outcomes are satisfied. |
| consumed unsuccessfully | Any failure, interruption, or unexpected result occurs after the gate-entry marker or first native transition. |
| not consumed due to preflight rejection | Local repository, identity, environment, fixture, policy, or source checks fail before the gate-entry marker and before native transition. |

Chosen gate-consumption boundary:

```text
after all local preflight has passed, when a durable gate-entry marker is
established immediately before the first native transition
```

Justification:

```text
This boundary does not consume authority for purely local preflight rejection.
It does consume authority before any native transition can be retried, which
prevents repeated native attempts after an informative failure.
```

The current implementation does not provide this gate-entry marker or state
machine.

## 12. Successful Completion Contract

`AUTHORITATIVE_RETAINED_RUN_COMPLETE` requires more than process exit code zero.

Required conditions:

```text
repository gate satisfied
source identity gate satisfied
policy identity gate satisfied
environment and fixture gate satisfied
selected case-set identity matched
all completion-gating cases reached expected bounded outcomes
identity continuity verified
collision destinations preserved
raw numeric and symbolic native errors retained
canonical terminal record serialized
artifact hash computed
artifact written to the authorized immutable directory
artifact persistence checked through the already closed BLOCKER-1 directory
durability profile where applicable
artifact reread and reverified
artifact hash stable after reread
terminal status internally consistent
retained_execution truth condition satisfied
```

Only after every condition above is satisfied may the retained terminal record
report:

```text
retained_execution = true
```

Any terminal record that lacks those conditions must either report
`retained_execution = false` or fail closed without admitting the retained
artifact.

The artifact durability check concerns retained evidence persistence only. It
must not be upgraded into rename durability, rename atomicity, or power-loss
persistence.

## 13. Failure and Rerun Semantics

Failure taxonomy:

| Failure class | Authority consumed? | Artifact may exist? | BLOCKER-2 state | Rerun rule |
|---|---|---|---|---|
| PREFLIGHT_REJECTED | No | Optional preflight diagnostic only if authorized; no retained execution artifact. | OPEN | Same authorization may remain unused if the rejection is fully pre-gate and operator review confirms no native transition. |
| IDENTITY_MISMATCH | Pre-gate: no. Post-gate: yes. | Yes if post-gate terminal record can be written. | OPEN | Post-gate rerun requires fresh authorization. |
| POLICY_MISMATCH | No | Optional preflight diagnostic only. | OPEN | Same authorization may remain unused after correction only if no gate entry occurred. |
| SOURCE_MISMATCH | No | Optional preflight diagnostic only. | OPEN | Same authorization may remain unused after correction only if no gate entry occurred. |
| REPOSITORY_STATE_INVALID | No | Optional preflight diagnostic only. | OPEN | Same authorization may remain unused after operator review only if no gate entry occurred. |
| FIXTURE_INVALID | Usually no; yes only if discovered after gate entry. | Phase-dependent. | OPEN | Post-gate rerun requires fresh authorization. |
| UNSUPPORTED_PLATFORM_PROFILE | No if detected before gate entry. | Optional preflight diagnostic only. | OPEN | Same authorization may remain unused if no gate entry occurred. |
| NATIVE_ERROR_INDETERMINATE | Yes | Yes, or partial artifact if terminal persistence fails. | OPEN | Fresh authorization required. |
| COLLISION_EXPECTATION_MISMATCH | Yes | Yes, or partial artifact if terminal persistence fails. | OPEN | Fresh authorization required. |
| IDENTITY_CONTINUITY_FAILURE | Yes | Yes, or partial artifact if terminal persistence fails. | OPEN | Fresh authorization required. |
| ARTIFACT_SERIALIZATION_FAILURE | Pre-gate: no. Post-gate: yes. | Possibly no complete artifact. | OPEN | Post-gate rerun requires fresh authorization. |
| ARTIFACT_HASH_FAILURE | Yes if after gate entry. | Yes, but invalid or unstable. | OPEN | Fresh authorization required. |
| ARTIFACT_PERSISTENCE_FAILURE | Yes if after gate entry. | Partial or missing artifact possible. | OPEN | Fresh authorization required. |
| ARTIFACT_REVERIFY_FAILURE | Yes | Yes, but not admitted. | OPEN | Fresh authorization required. |
| RUN_INTERRUPTED | Pre-gate: no. Post-gate: yes. | Partial artifact or gate marker may exist. | OPEN | Post-gate rerun requires fresh authorization. |
| UNEXPECTED_INTERNAL_ERROR | Pre-gate: no. Post-gate: yes. | Phase-dependent. | OPEN | Post-gate rerun requires fresh authorization. |

No failed or interrupted post-gate native attempt may be repeated under the
same consumed authorization.

## 14. Relationship to BLOCKER-1

The closed BLOCKER-1 directory-durability mechanism may support retained
artifact persistence by syncing the directory entry that contains the retained
terminal record and any required evidence files under the same bounded Windows
local fixed NTFS temporary-path profile.

BLOCKER-1 may support:

```text
retained artifact directory-entry durability evidence
artifact reread and reverify workflow
fail-closed classification if persistence cannot be confirmed
```

BLOCKER-1 must not be extended into proof of:

```text
rename atomicity
rename durability
source-parent durability
destination-parent rename persistence
power-loss persistence
```

BLOCKER-1 closure remains intact and does not close BLOCKER-2.

## 15. Relationship to Scientific Completion

The retained promotion-control artifact is platform evidence only.

It is not itself:

```text
IMMUTABLE_SCIENTIFIC_BUNDLE
SCIENTIFIC_COMPLETION
publication readiness
```

It may later be linked to scientific-completion or publication objects only as
bounded supporting platform evidence. That link must preserve separate
identities for:

```text
scientific result
promotion-control platform evidence
directory-durability evidence
publication projection
```

The retained artifact must not become the scientific completion by name,
schema, implication, or recovery behavior.

## 16. Relationship to BLOCKER-2 Closure

One successful retained absolute-path run could:

```text
partially satisfy BLOCKER-2
support a later closure decision
preserve diagnostic platform evidence
```

It could not by itself:

```text
close BLOCKER-2
prove general FileRenameInfo support
prove rename atomicity
prove rename durability
prove power-loss persistence
establish production readiness
```

Narrowest defensible conclusion:

```text
A successful retained run would provide identity-bound retained evidence for
the selected absolute-path control under one admitted fixture. It would support
but not complete a later BLOCKER-2 closure assessment.
```

BLOCKER-2 remains OPEN.

## 17. Implementation Readiness

Readiness classification:

```text
NARROW_IMPLEMENTATION_CHANGE_REQUIRED_BEFORE_AUTHORIZATION
```

Reason:

The current runner can execute the absolute-path control and build an in-memory
control record with:

```text
retained_execution = false
```

The current runner does not yet provide the retained-run capabilities required
for authoritative execution:

```text
canonical artifact persistence
authorized immutable result directory
durability invocation for retained artifact persistence
repository and source identity preflight gate
selected case-set identity binding
gate-consumption recording
terminal-state truthfulness
single-run enforcement
interruption handling
post-write reread verification
stable artifact hash admission
failure taxonomy recording
```

No implementation change is authorized by this document. The missing capability
must be specified and authorized in a separate narrow docs-only preparation
authorization before any retained single-run authorization.

## 18. Claims Supported

Supported:

```text
The absolute-path FileRenameInfo control succeeded under the bounded ephemeral
fixture.
```

Supported:

```text
The RootDirectory-relative form returned ERROR_INVALID_PARAMETER / 87.
```

Supported:

```text
The comparison narrows suspicion toward differences between the two forms,
including relative destination resolution, destination-parent handle setup,
destination-parent access rights, or another distinguishing parameter
interaction.
```

Supported:

```text
A retained run may preserve bounded platform evidence for selected A-cases
under one exact admitted Windows fixture after narrow retained-execution
preparation.
```

## 19. Claims Not Supported

Not supported:

```text
RootDirectory-relative FileRenameInfo is invalid
the absolute form is generally supported
Microsoft documentation is wrong
rename is atomic
rename is durable
parent flush proves rename persistence
power-loss persistence is established
BLOCKER-2 is closed
production readiness exists
real-world Brainvision readiness exists
strong order sensitivity exists
```

Not supported by a future retained artifact alone:

```text
IMMUTABLE_SCIENTIFIC_BUNDLE
SCIENTIFIC_COMPLETION
publication readiness
BLOCKER-4 progress
```

## 20. Risks and Unresolved Questions

Risks:

```text
current implementation lacks retained artifact persistence
current implementation lacks gate-consumption state
current implementation lacks terminal retained_execution truth machinery
current implementation lacks single-run enforcement
current implementation lacks post-write reread verification
A4 is nondeterministic and should not gate a single retained run
A8 currently lacks a second-volume fixture and should not be included as a skip
```

Unresolved questions:

```text
whether a later closure assessment will require former-source-parent durability
whether A6 should be selected as optional retained diagnostic evidence
whether a later retained schema should include a separate pre-native gate marker
inside the immutable artifact directory
whether a later authorization will bind expected checked-out byte SHA-256 values
directly or bind a reviewed source-identity manifest
```

None of these unresolved questions authorize execution or close BLOCKER-2.

## 21. Final Decision

Machine-readable decision block:

```text
assessment_verdict = "B. REQUIRE_NARROW_IMPLEMENTATION_PREPARATION_BEFORE_RUN_AUTHORIZATION"
blocker_2_state = "OPEN"
retained_run_executed = false
retained_artifact_created = false
implementation_modified = false
authorization_created = false
blocker_4_started = false
selected_completion_gating_cases = "A1,A2,A3,A5"
selected_optional_diagnostic_cases = "A6"
excluded_cases = "A4,A7,A8"
implementation_readiness = "NARROW_IMPLEMENTATION_CHANGE_REQUIRED_BEFORE_AUTHORIZATION"
gate_consumption_boundary = "durable gate-entry marker immediately before first native transition"
```

Final verdict:

```text
B. REQUIRE_NARROW_IMPLEMENTATION_PREPARATION_BEFORE_RUN_AUTHORIZATION
```

The retained-run lane remains scientifically useful, but immediate retained
single-run authorization is not procedurally ready.

## 22. Exact Next Authorized Step

Exact next authorized step:

```text
Prepare a separate docs-only narrow retained-execution preparation
authorization for the absolute-path control runner.
```

That preparation authorization should cover only the missing retained-run
machinery identified in this assessment:

```text
canonical artifact persistence
authorized immutable result directory
artifact durability and reread verification
repository and source identity gates
selected case-set identity
gate-consumption state
terminal-state truthfulness
single-run enforcement
failure taxonomy recording
```

That next step must not authorize the authoritative retained run itself unless
and until the preparation implementation and findings are separately reviewed.

This document returns control to Hilmir for review.

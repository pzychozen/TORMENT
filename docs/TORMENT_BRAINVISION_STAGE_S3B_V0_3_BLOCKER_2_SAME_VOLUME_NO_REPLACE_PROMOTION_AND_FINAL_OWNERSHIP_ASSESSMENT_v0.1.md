# TORMENT Brainvision Stage S3B v0.3 BLOCKER-2 Same-Volume No-Replace Promotion and Final Ownership Assessment v0.1

## 1. Assessment Identity and Current Status

document_class = BLOCKER-2 assessment

document_version = v0.1

assessment_scope = same-volume no-replace promotion, promotion ownership, final artifact ownership semantics, and post-promotion final-parent durability ordering

baseline_commit = d147624a855012280503f505d2347b7e9495b505

baseline_branch = main

baseline_origin = origin/main

primary_assessment_result =
BLOCKER_2_REQUIRES_PRE_SPECIFICATION_PRIMITIVE_RESEARCH

This assessment is docs-only. It implements no promotion primitive, selects no
implementation primitive, authorizes no implementation, opens no live-test lane,
and changes no scientific state.

FORMAL_HOLD remains active.

Mode_0 remains active.

The scientific state remains:
STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY.

Brainvision remains offline, quarantined, synthetic-only, non-production,
non-service, non-kernel, non-memory-integrated, non-cognitive, and
non-autonomous.

## 2. Authoritative Baseline and Blocker State

The required synchronized baseline is present:

```text
branch      = main
HEAD        = d147624a855012280503f505d2347b7e9495b505
origin/main = d147624a855012280503f505d2347b7e9495b505
latest      = d147624 docs(research): close blocker 1 directory durability
```

The inspected evidence chain includes:

1. d147624 docs(research): close blocker 1 directory durability
2. 38cde99 docs(research): record blocker 1 directory durability findings
3. 82b78fc research(brainvision): implement blocker 1 Windows directory durability
4. 9ca92f9 docs(research): specify blocker 1 Windows directory durability
5. 6897fc8 docs(research): assess blocker 1 Windows directory durability
6. ac5dd26 docs(research): record durable evidence implementation findings v0.3

Current blocker state:

```text
BLOCKER-1:
BLOCKER_1_CLOSED_WITHIN_AUTHORIZED_SYNTHETIC_OFFLINE_WINDOWS_LOCAL_FIXED_NTFS_TMP_PATH_SCOPE

BLOCKER-2:
OPEN

BLOCKER-3:
CLOSED_WITHIN_AUTHORIZED_SYNTHETIC_OFFLINE_STAGE_S3B_V0_3_SCOPE

BLOCKER-4:
OPEN
```

BLOCKER-1 remains closed and is not reopened.

BLOCKER-3 remains closed within its authorised scope.

BLOCKER-4 remains open and separate.

No live or production publication lane is opened.

No implementation is authorized by this assessment.

## 3. Exact Assessment Question

Assessment question:

What must be proven and implemented before a completely verified staged
scientific publication set may be promoted into its final location without
replacement, without ownership ambiguity, without cross-volume substitution, and
without claiming completion before final directory-entry durability is confirmed?

Answer:

BLOCKER-2 requires a real, validated, same-volume, no-replace directory-set
promotion primitive plus schema-bound promotion evidence, source-to-final
identity continuity, final-path ownership proof, and final-parent directory
durability gating before `PUBLICATION_COMPLETED` can be admitted.

The current repository contains promotion vocabulary, an abstract adapter seam,
a fail-closed default adapter, test-only positive promotion adapters, and
publication orchestration that expects a promotion status. It does not contain a
real operating-system same-volume no-replace promotion implementation, a
replay-verifiable promotion evidence record, or final-parent durability gating
after promotion.

The repository evidence is not sufficient to responsibly select or constrain a
Windows primitive. BLOCKER-2 therefore requires pre-specification primary-source
Windows API primitive research before a formal implementation-neutral
specification can be written.

## 4. Existing Promotion Architecture

The current publication object model is:

```text
publication chain directory =
root/.iososv_v0_3.publication_chain/<publication_chain_identity>

staging directory =
root/.iososv_v0_3.publication_staging/<publication_chain_identity>

final directory =
root/iososv_v0_3.publication/<publication_chain_identity>
```

The staged and final publication set is the exact three-file artifact directory
defined by `PUBLICATION_ARTIFACT_FILENAMES`:

```text
iososv_v0_3_result.json
iososv_v0_3_execution_envelope.json
iososv_v0_3_summary.txt
```

Current orchestration:

1. validates publication authority and anchors;
2. writes durable publication authority and attempted records;
3. writes the complete staged artifact set;
4. confirms staging-parent and staging-directory durability through BLOCKER-1;
5. re-reads and verifies the staged artifact set;
6. rejects if the final directory path already exists;
7. calls `promotion_adapter.promote_verified_directory_no_replace(staging, final)`;
8. rejects unless the returned status is `PROMOTION_CONFIRMED`;
9. re-reads and verifies the final artifact set;
10. writes `PUBLICATION_COMPLETED` if the final readback and completed-record durability pass.

This is an orchestration seam, not a real promotion implementation.

## 5. Existing Seams Versus Missing Implementation

| Current-state item | Present state | Finding |
|---|---:|---|
| Abstract promotion interface | Present | `SameVolumeNoReplacePromotionAdapter.promote_verified_directory_no_replace(source, destination)` exists. |
| Fail-closed default promotion adapter | Present | `FailClosedSameVolumeNoReplacePromotionAdapter` returns `PROMOTION_UNCONFIRMED` with detail that the primitive is unvalidated. |
| Test-only positive promotion adapters | Present | `PositiveTmpPromotionAdapter` uses pytest-local `Path.rename`; `CorruptingPromotionAdapter` can return confirmed while corrupting final artifacts to test final readback rejection. |
| Publication orchestration expects promotion evidence | Partial | Orchestration requires a `PROMOTION_CONFIRMED` status before final readback, but the returned `DirectoryPromotionResult` has only status and detail. |
| Real same-volume no-replace operating-system promotion | Absent | No Windows promotion primitive is implemented. Current real default fails closed. |
| Final-parent durability sequencing after promotion | Absent | `FINAL_PARENT_DIRECTORY` exists in schema and BLOCKER-1 handoff documents, but current publication completion does not sync the final parent after promotion. |
| Verified final-path ownership transfer | Absent | Current final readback verifies artifact bytes, not namespace ownership continuity from the staged directory object to the final directory object. |
| Replay-verifiable promotion identity | Absent | `PUBLICATION_COMPLETED` payload currently contains projection identity, chain identity, and artifact SHA-256s only; no promotion policy, primitive, source identity, destination identity, or final-parent durability evidence is replayed. |

Vocabulary and test fakes must not be classified as a validated primitive.

## 6. Promotion Object and Ownership Analysis

Current repository structure shows the promotion object is the complete staging
directory:

```text
paths.staging_directory -> paths.final_directory
```

The staging directory contains the exact publication artifact set. The
publication envelope is an artifact file inside that set, not an envelope
directory. The immutable scientific bundle is the scientific input projected
into publication artifacts, not the filesystem directory being promoted.

Therefore the next specification should treat the promotion target as the
complete verified staging directory unless later primary-source primitive
research proves that the primitive must operate on a different repository object
and the architecture is explicitly revised.

Ownership before promotion:

1. The staging directory is provisional publication evidence, not final
   publication ownership.
2. The staged set must be reverified immediately before promotion.
3. The source directory object identity and source parent identity must be bound
   into the promotion request.
4. The request must link the verified immutable scientific bundle identity and
   linked valid scientific completion identity.
5. No other actor may be allowed to mutate the staged set after verification and
   before promotion; if exclusivity cannot be proven, promotion must fail closed.

Ownership after promotion:

1. A successful namespace transition may make the final path visible.
2. Final ownership is not admitted merely because the final path is visible.
3. Final ownership requires final-path object identity, continuity from the
   verified staging object, destination absence before promotion, no competing
   owner, and final-parent directory durability.
4. Successful namespace transition and durable final namespace transition are
   distinct claims.

## 7. Same-Volume and No-Replace Requirements

The promotion requirement is:

```text
same-volume
directory-set promotion
no replacement
destination must not pre-exist
source must be the verified staged set
failure must preserve evidence and avoid ambiguous ownership
```

The no-replace guarantee must reject:

```text
overwrite
replacement
merge
partial population
silent reuse of an existing directory
path-string-only destination absence
```

The no-replace guarantee must be enforced by the operating-system primitive or
by an equivalently atomic kernel-level operation. A check-then-act path
existence test is insufficient because another actor can create the destination
between the check and the operation.

Same-volume proof must not rely on path-root string comparison alone. The next
specification must evaluate opened parent-directory handles, volume serial
identity, filesystem-object identity, or another stable Windows volume identity
that can prove the source and destination parents are on the same filesystem
volume before promotion.

Required fail-closed cases include:

```text
cross-volume source/destination
unavailable volume identity
identity changing during promotion
unsupported filesystem
source or destination reparse involvement
destination already exists
source not matching the verified staged set
native operation failure
native result indeterminate
```

## 8. Source and Destination Identity Requirements

Required source identity evidence:

1. source staging path;
2. source directory object identity;
3. source parent directory identity;
4. source volume identity;
5. staged artifact hashes from immediate pre-promotion verification;
6. link to immutable scientific bundle identity;
7. link to scientific completion logical record identity.

Required destination identity evidence:

1. destination final path;
2. destination parent directory identity;
3. pre-promotion destination absence evidence;
4. post-promotion final object identity;
5. continuity from source object identity to final object identity;
6. absence of replacement or competing owner;
7. final artifact hashes from post-promotion verification.

Unsafe evidence:

1. path strings without object identity;
2. destination absence checked only before a path-based rename;
3. status booleans without native result detail;
4. native error text without the numeric native error code;
5. test-only `Path.rename` behavior treated as Windows primitive evidence.

If identity is unavailable or changes at any mandatory stage, the promotion
claim must fail closed.

## 9. Final-Parent Durability Ordering

BLOCKER-1 provides the reusable `FINAL_PARENT_DIRECTORY` directory-durability
role. BLOCKER-2 must order it after promotion and final object verification.

Required ordering:

```text
verify staged set
prove source/destination support profile
prove same volume
perform no-replace promotion
confirm promotion result
open and verify final object
sync FINAL_PARENT_DIRECTORY
require DIRECTORY_DURABILITY_CONFIRMED
admit final ownership durability
write and durably admit PUBLICATION_COMPLETED
```

Current code does not yet perform this sequence. Current publication tests show
directory durability roles for record parents, staging parent, and staging
directory; they do not show a post-promotion `FINAL_PARENT_DIRECTORY` sync.

Additional directory synchronization:

1. The final parent is mandatory for admitting durable final namespace
   ownership.
2. The former staging parent may also require synchronization if the BLOCKER-2
   ownership claim includes durable disappearance of the staging name or
   no-duplicate source/final evidence.
3. The final object directory itself should not be silently added as a new
   requirement; current staged-set contents are already file-synced and the
   staging directory is synced before promotion. If primary-source primitive
   research shows an additional final object directory sync is required, that
   must be specified explicitly.

Because this assessment cannot select the Windows primitive, it cannot finally
settle the additional staging-parent/final-object synchronization question.

## 10. Evidence and Policy Identity Requirements

BLOCKER-2 needs a separately declared and digested promotion policy identity. It
must not silently reuse the directory-durability policy identity because
promotion semantics differ from directory-entry durability semantics.

The promotion policy declaration should belong in the platform-neutral schema
module and bind:

```text
same-volume definition
no-replace primitive contract
directory-set source object
reparse policy
supported filesystem profile
identity rules
source validation
destination validation
error taxonomy
post-promotion verification
final-parent durability ordering
```

Promotion evidence fields:

| Field | Assessment |
|---|---|
| promotion policy identity | Necessary; schema-owned and digest-bound. |
| promotion utility identity | Necessary if a platform utility implementation participates in the chain; must be canonical, not hidden. |
| source staging path | Necessary, but insufficient alone. |
| source object identity | Necessary. |
| source parent identity | Necessary for same-volume and namespace-change evidence. |
| destination final path | Necessary, but insufficient alone. |
| destination parent identity | Necessary. |
| volume identity | Necessary. |
| pre-promotion destination absence evidence | Necessary, but must be tied to the primitive or an atomic no-replace guarantee. |
| post-promotion final object identity | Necessary. |
| promotion native result | Necessary. |
| native error code | Necessary on failure; must remain numeric and fail closed when unknown. |
| final-parent directory-durability evidence | Necessary before final ownership completion. |
| linked immutable scientific bundle identity | Necessary link to the authoritative durable result. |
| linked scientific completion identity | Necessary link to the authoritative durable result. |
| wall-clock timestamp | Optional at most; unsafe as proof of ordering or identity. |
| path-root string comparison | Unsafe as same-volume proof. |

Publication is a projection of the authoritative scientific result.

Authoritative durable result =
verified IMMUTABLE_SCIENTIFIC_BUNDLE
+
linked valid SCIENTIFIC_COMPLETION

Promotion evidence is platform evidence linked to that authoritative pair; it
does not become a new scientific result.

## 11. Status and Failure Taxonomy

The current promotion taxonomy has only:

```text
PROMOTION_CONFIRMED
PROMOTION_UNCONFIRMED
```

This is insufficient for BLOCKER-2 specification because it cannot distinguish
unsupported platform, denied operation, destination exists, cross-volume
attempt, identity change, operation failure, post-verification failure, or
final-parent durability failure.

The next specification should consider semantic statuses equivalent to:

```text
PROMOTION_CONFIRMED
PROMOTION_UNSUPPORTED
PROMOTION_DENIED
PROMOTION_INDETERMINATE
PROMOTION_SOURCE_INVALID
PROMOTION_DESTINATION_EXISTS
PROMOTION_CROSS_VOLUME
PROMOTION_IDENTITY_CHANGED
PROMOTION_OPERATION_FAILED
PROMOTION_POST_VERIFY_FAILED
PROMOTION_FINAL_PARENT_DURABILITY_FAILED
```

These exact names are not mandated by this assessment. The required point is
that the grammar must distinguish these failure modes and fail closed on unknown
native errors while preserving numeric native error codes.

Existing publication classifications such as `PUBLICATION_PROMOTION_FAILED`,
`PUBLICATION_PROMOTION_OUTCOME_INDETERMINATE`, and
`PUBLICATION_FINAL_DIRECTORY_INVALID` are useful but not sufficient as the only
promotion evidence taxonomy.

## 12. Windows Primitive Candidate Analysis

No web research was authorized or performed. The repository contains references
to `MoveFileExW`, `ReplaceFileW`, and `MOVEFILE_WRITE_THROUGH` as explicit
non-BLOCKER-1 primitives delegated to BLOCKER-2 territory, but it does not
contain primary-source Windows API documentation sufficient to select or
constrain a BLOCKER-2 primitive.

Candidate comparison from repository evidence only:

| Candidate | Repository evidence | Assessment |
|---|---|---|
| `MoveFileExW` | Mentioned in BLOCKER-1 assessment/specification/authorization as not part of BLOCKER-1 and belonging to BLOCKER-2 promotion semantics. | Viable candidate class, but local evidence does not prove no-replace directory semantics, destination-exists behavior, same-volume behavior, handle identity support, or interaction with final-parent `FlushFileBuffers`. Requires primary-source API review. |
| `MoveFileW` | Not materially specified locally. | Cannot be selected from repository evidence. Requires primary-source API review for directory support, no-replace behavior, and cross-volume behavior. |
| `SetFileInformationByHandle` with an appropriate rename information class | Not materially specified locally. | Potentially relevant because a handle-based primitive could reduce path-race exposure, but repository evidence does not identify the required information class, Windows 10/11 support, no-replace semantics, or directory behavior. Requires primary-source API review. |
| Other documented Windows no-replace rename mechanisms | No local committed evidence found. | Cannot be selected without primary-source research. |

For each candidate, the formal specification must prove or reject:

```text
same-volume behavior
destination-exists behavior
directory support
no-replace semantics
atomic namespace transition properties
handle-based versus path-based operation
reparse risk
error observability
Windows 10 and Windows 11 compatibility
unsupported flag avoidance
interaction with final-parent FlushFileBuffers
```

Because this proof is absent locally, BLOCKER-2 is not ready for formal
specification.

## 13. Race and Reparse Analysis

Hazards that BLOCKER-2 must close:

1. destination checked absent and then created by another actor;
2. source mutated after verification;
3. source identity changed after verification;
4. destination parent redirected or replaced;
5. source or destination reparse-point substitution;
6. cross-volume fallback copy;
7. partial copy behavior;
8. replacement of an existing destination;
9. post-promotion object differing from the verified source;
10. native success reported for a result that cannot be identity-verified.

The no-replace destination guarantee must be closed by the primitive itself, not
by a separate check-then-act sequence.

Pre/post identity verification must close source mutation, destination parent
substitution, reparse involvement, and source-to-final continuity hazards.

Cross-volume fallback copy must be forbidden. If a candidate primitive can copy
across volumes, that behavior is disqualifying unless it can be disabled and
proved disabled.

## 14. Crash and Recovery-State Analysis

| State | Required deterministic outcome |
|---|---|
| Crash before promotion | J1 remains authoritative; publication projection remains incomplete; staging evidence may remain provisional; no `PUBLICATION_COMPLETED` may be reconstructed. |
| Crash during promotion | Outcome is indeterminate unless durable evidence proves otherwise; recovery must fail closed or record separate recovery evidence only. |
| Crash after promotion but before final-parent sync | Final path may be visible, but durable final ownership is not admitted; recovery must not reconstruct an original `PUBLICATION_COMPLETED` event. |
| Crash after final-parent sync but before promotion evidence record completion | Namespace durability may have occurred, but the publication chain lacks durable promotion/completion evidence; recovery may verify final artifacts under separate recovery evidence only. |
| Crash after promotion evidence durability but before `PUBLICATION_COMPLETED` durability | Promotion evidence may be replayable, but publication completion remains absent until the completed record itself is durably accepted. |
| Crash after `PUBLICATION_COMPLETED` durability | Replay must validate promotion evidence, source-to-final continuity, final-parent durability, directory-durability policy identity, promotion policy identity, and completed-record durability before returning completed. |

J1 evidence and the authoritative scientific result remain unchanged in every
state. Recovery evidence must not reconstruct a completion event that was never
durably established.

## 15. Publication Completion and Replay Implications

Future `PUBLICATION_COMPLETED` admission should require the current architecture
plus BLOCKER-2 evidence:

```text
verified immutable scientific bundle
linked valid scientific completion
valid publication projection authorization
resource admissibility confirmed with matching active resource policy identity
durable publication authority and attempted records
staging artifacts written as exact bounded artifact set
staging parent durability confirmed
staging directory durability confirmed
staged artifact set immediately reverified
same-volume no-replace promotion confirmed
source/final identity continuity confirmed
post-promotion final artifact set verified
final-parent directory durability confirmed
matching active promotion policy identity
matching active directory-durability policy identity
durable PUBLICATION_COMPLETED record
```

Publication replay and publication-recovery replay must verify:

```text
promotion policy identity
promotion evidence structure
source-to-final identity continuity
same-volume evidence
no-replace result
post-promotion final identity
final-parent durability
completion-gating decision
```

Replay must fail closed on missing, malformed, foreign, mismatched, incomplete,
or contradictory promotion evidence.

Current replay does not perform these checks because current records do not
contain promotion evidence.

## 16. BLOCKER-1/BLOCKER-3/BLOCKER-4 Interaction

BLOCKER-1:

BLOCKER-1 remains closed. BLOCKER-2 must reuse the `FINAL_PARENT_DIRECTORY`
directory-durability role after promotion, but it must not reopen or weaken
BLOCKER-1's directory-entry durability closure.

BLOCKER-3:

BLOCKER-3 remains closed within its authorized synthetic-offline
resource-admissibility scope. BLOCKER-2 may introduce bounded evidence-size and
verification-cost questions for promotion evidence, but no current finding
reopens BLOCKER-3.

BLOCKER-4:

Committed documents describe BLOCKER-4 as the absence of separate future
real-operation authorizations. BLOCKER-4 remains open and separate.

BLOCKER-2 has no implementation or closure dependency on BLOCKER-4 for this
assessment or for pre-specification primitive research. A later live or
protected invocation would have an authorization-ordering dependency on
BLOCKER-4, but no such lane is opened here.

## 17. Residual Uncertainties

Residual uncertainties before specification:

1. Which Windows primitive can provide same-volume no-replace directory
   promotion with sufficient evidence.
2. Whether a handle-based primitive is required to avoid path-race exposure.
3. Which stable Windows volume and object identity fields must be bound.
4. Whether former staging-parent durability is required for final ownership or
   only for source-retirement evidence.
5. Whether any final object directory sync is required after promotion.
6. Exact promotion policy declaration fields and digest grammar.
7. Exact promotion status names and mapping from numeric native errors.
8. Exact replay record shape for promotion evidence.
9. Whether current `PUBLICATION_COMPLETED` payload must be extended directly or
   preceded by a separate promotion evidence record.

These are specification inputs, not implementation authority.

## 18. Hilmir Decision Points

No genuine Hilmir system-design decision is presently required before the next
step.

The blocker at this assessment stage is technical: the repository lacks
primary-source Windows API evidence sufficient to select or constrain the
promotion primitive. Ordinary technical details should be resolved by
pre-specification primitive research and then encoded in a formal specification.

Potential future Hilmir decisions may arise only if primitive research exposes a
real architecture fork, such as incompatible ownership models or incompatible
recovery semantics. The recommended default if such a fork appears is:

```text
final ownership remains namespace identity plus publication identity;
promotion evidence remains platform evidence linked to SCIENTIFIC_COMPLETION;
final-path visibility before final-parent durability does not imply completion;
recovery may record separate recovery evidence but may not reconstruct original completion.
```

Those defaults are not implementation authorization.

## 19. Derived Assessment Result

Derived primary assessment result:

B. BLOCKER_2_REQUIRES_PRE_SPECIFICATION_PRIMITIVE_RESEARCH

Rationale:

1. BLOCKER-2 is not already satisfied because no real validated same-volume
   no-replace operating-system promotion implementation exists.
2. Abstract seams, fail-closed adapters, vocabulary, and test fakes are
   insufficient to close BLOCKER-2.
3. The current architecture is clear enough to identify the promotion object,
   missing evidence, and completion gating requirements.
4. The repository evidence is not sufficient to select or constrain a Windows
   primitive among `MoveFileExW`, `MoveFileW`,
   `SetFileInformationByHandle`, or any other documented mechanism.
5. A primary-source Windows API review is required before formal specification.

The rejected alternatives are:

```text
A. BLOCKER_2_READY_FOR_FORMAL_SPECIFICATION
   Rejected because primitive semantics cannot be responsibly specified from local evidence alone.

C. BLOCKER_2_REQUIRES_ARCHITECTURAL_DECISION
   Rejected for now because no Hilmir-level architecture decision blocks primitive research.

D. BLOCKER_2_ALREADY_SATISFIED
   Rejected because the real promotion primitive, final ownership proof, promotion policy identity, and final-parent durability chain are absent.
```

## 20. Recommended Next Procedural Step

Recommended next procedural step:

Prepare a docs-only pre-specification Windows primitive research order for
BLOCKER-2.

That order should authorize primary-source review of Windows directory rename
and no-replace primitives, including at minimum:

```text
MoveFileExW
MoveFileW
SetFileInformationByHandle with the appropriate rename information class
documented no-replace directory rename behavior
destination-exists error behavior
same-volume behavior
cross-volume fallback avoidance
reparse handling
Windows 10/11 support
final-parent FlushFileBuffers interaction
```

After that research is accepted, prepare a separate formal BLOCKER-2
specification. Do not implement promotion, do not authorize implementation, do
not open BLOCKER-4, and do not open live publication testing from this
assessment.

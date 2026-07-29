# TORMENT Brainvision Stage S3B v0.3 BLOCKER-2 R4 PREPARE_PATHS Path-Creation Governance Correction Decision v0.1

## 1. Status

This document is a draft governance correction decision candidate for the retired BLOCKER-2 R4 PREPARE_PATHS canonical-input preparation lane.

It is not committed, not pushed, not post-commit identity-bound, not active, and not self-authorizing.

It does not create any external directory, create or publish canonical-input bytes, invoke `PREPARE_PATHS`, invoke `PREFLIGHT_ONLY`, invoke `EXECUTE_EXACT_SINGLE_RUN`, create execution authority, consume execution authority, close BLOCKER-2, or activate BLOCKER-4.

Brainvision remains `OFFLINE`, `QUARANTINED`, `SYNTHETIC-RESEARCH ONLY`, `FORMAL_HOLD ACTIVE`, and `MODE 0`.

## 2. Retired Lane Baseline

The retired accepted invocation HEAD for the blocked R4 preparation attempt was:

```text
4b0754825d7f0443a4ee696945995bcf6c63230b
```

That lane is retired by Hilmir's non-commit declaration after a fail-closed pre-publication path-governance blocker.

The retired lane state is:

```text
prior publication: NONE
prior selected-path contact: NONE
prior canonical-input bytes: NOT PUBLISHED
prior governed leaf directory: ABSENT
prior governed parent directory: ABSENT
prior PREPARE_PATHS attempt: UNCONSUMED
prior Layer-B preparation authority: RETIRED UNCONSUMED
prior execution authority: NOT CREATED NOT CONSUMED
```

The previously derived in-memory candidate bytes and identities are non-authoritative, non-durable, and must be regenerated under any fresh accepted invocation HEAD.

## 3. Controlling Prior Governance

This correction is derived from the following committed governance and runtime surfaces at the retired HEAD:

| Surface | Git blob OID | Checked-out SHA-256 | Role |
| --- | --- | --- | --- |
| `docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_PREPARE_PATHS_ACTIVE_READY_LAYER_B_CANONICAL_INPUT_PREPARATION_DECISION_v0.1.md` | `40143e922308455c5b1bff4def6dfa19f98ca337` | `dea5810af30b83d6903f979f478fb4088a74c77208ef2269369ead96813d7f3a` | Retired active-ready Layer-B decision |
| `docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_PREPARE_PATHS_ACTIVE_READY_LAYER_B_DECISION_POST_COMMIT_IDENTITY_RECORD_v0.1.md` | `b42de195f31edc493961c44efd30883766cbc09f` | `af5bb232a88999fd47e6f0420b15ab86d9627129fd1fa14374ce325a3f721cd9` | Retired Layer-B identity record |
| `docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_PREPARE_PATHS_LAYER_C_INVOCATION_AUTHORIZATION_v0.1.md` | `8f5817931bd2c406f3b8c03e3303b0438aaa7b11` | `f14a96cc88ed3423e8258e7ffef7ca300ab933f57c407fab54b03492e2056bdb` | Retired Layer-C invocation authorization |
| `docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_PREPARE_PATHS_LAYER_C_INVOCATION_AUTHORIZATION_POST_COMMIT_IDENTITY_RECORD_v0.1.md` | `63f3e49ee6be78539870f827b5d3f90fd9bc6279` | `3061ef822647fa0ee21ecdc32a4e79c3f867f0212597480982f0233b5ff659db` | Retired Layer-C identity record |
| `docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_PREPARE_PATHS_LAYER_B_CANONICAL_INPUT_PREPARATION_GOVERNANCE_DECISION_DRAFT_v0.1.md` | `9bbc524c030054ce2cb754e8a0cd776446a4332e` | `6247cd5fd541b3ace60514348aa71bd019469131d05a0b52c4e2d359da4a139d` | Prior Layer-B governance design |
| `docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_PREPARE_PATHS_CANONICAL_INPUT_PREPARATION_AUTHORIZATION_v0.1.md` | `1bbb7b0448b1c7b587c53c2c5105a36134da49f3` | `e49e978126520ea0224407b7052c291f9710e0d156133fb2bcaa700086f244c6` | R4 preparation authorization document |
| `research/brainvision/run_blocker2_authoritative_retained_single_run_v0_1.py` | `79d0c89575919c8506c8b9f1278efd5d63b1e813` | `c61de2f7829e3eb2bb938701f98bbafe54f09f03dab8abd718d421a81b56e976` | Operator wrapper runtime |
| `research/brainvision/blocker2_retained_absolute_path_control_v0_1.py` | `1779715ed17fffe3a927d24eb445eec51f3d42d6` | `dc4a6e3f1169c33a2379c3506d107893cb8a48c977300c22bda14db0bf19e3d5` | Retained helper runtime |

The retired governance named the selected leaf directory:

```text
C:\TORMENT\brainvision_authoritative_inputs\blocker2_s3b_v0_3\r4_prepare_paths
```

It did not explicitly enumerate every missing ancestor directory that a Windows directory-creation operation might create before reaching that leaf.

## 4. Defect Statement

The retired lane failed before path contact because the selected leaf directory was absent and at least one required ancestor was absent.

A Windows command naming the leaf can create more than the final named directory if intermediate ancestors do not exist. Governance authority is measured by filesystem effects, not by the final textual argument to a command.

Therefore, the retired authority did not safely authorize the observed path state. The prior accepted HEAD is retired for this R4 attempt, and the prior in-memory candidate identities must not be reused.

## 5. Corrected External Path-Creation Model

Read-only drafting-time observation found that the preferred root:

```text
C:\TORMENT\brainvision_authoritative_inputs
```

is absent. This correction therefore selects the nearest observed existing fixed ancestor as the required existing root:

```text
C:\TORMENT
```

`C:\TORMENT` is an ancestor of the authoritative repository path, but it is outside the repository under the controlling containment test. The first authorized creation produces a sibling namespace beside `TORMENT_repo`; it does not create content inside the repository.

Future path creation under this correction may create only these directories, in this order:

```text
1. C:\TORMENT\brainvision_authoritative_inputs
2. C:\TORMENT\brainvision_authoritative_inputs\blocker2_s3b_v0_3
3. C:\TORMENT\brainvision_authoritative_inputs\blocker2_s3b_v0_3\r4_prepare_paths
```

The selected canonical input file remains:

```text
C:\TORMENT\brainvision_authoritative_inputs\blocker2_s3b_v0_3\r4_prepare_paths\r4_prepare_paths_authorization_input_v0_1.canonical.json
```

No other external canonical-input directory may be created by this correction.

## 6. Ordered Directory-Creation Semantics

Directory creation and canonical-input publication are separate explicit operational acts.

The corrected directory-creation act must:

```text
1. verify C:\TORMENT exists and is admissible
2. verify C:\TORMENT\brainvision_authoritative_inputs is absent
3. create only C:\TORMENT\brainvision_authoritative_inputs
4. validate C:\TORMENT\brainvision_authoritative_inputs
5. verify C:\TORMENT\brainvision_authoritative_inputs\blocker2_s3b_v0_3 is absent
6. create only C:\TORMENT\brainvision_authoritative_inputs\blocker2_s3b_v0_3
7. validate C:\TORMENT\brainvision_authoritative_inputs\blocker2_s3b_v0_3
8. verify C:\TORMENT\brainvision_authoritative_inputs\blocker2_s3b_v0_3\r4_prepare_paths is absent
9. create only C:\TORMENT\brainvision_authoritative_inputs\blocker2_s3b_v0_3\r4_prepare_paths
10. validate C:\TORMENT\brainvision_authoritative_inputs\blocker2_s3b_v0_3\r4_prepare_paths
11. stop
```

Each creation must use create-new semantics for exactly one path component. It must fail if the selected child already exists. It must fail if the selected child's immediate parent is absent. It must not ask the operating system to create any unspecified intermediate directory.

Recursive directory creation is prohibited. `mkdir`, `md`, `New-Item -Force`, library calls with `parents=True`, or any equivalent command/API mode are prohibited unless the caller has already proven that the operation can create only the single selected component for that step and cannot create any missing ancestor.

`C:\TORMENT` admissibility must be verified using the immediate-parent property set before the first creation.

Before each one-component creation, the operator must verify that the immediate parent:

```text
exists
is an absolute drive-qualified DOS path
is on a local fixed drive
is on NTFS
is outside the repository
is not UNC
is not a device path
is not a volume-GUID path
is not a reparse point
```

Before each one-component creation, the operator must verify that the selected child:

```text
is absent
has an intended absolute drive-qualified DOS path
lies outside the repository
is not UNC
is not a device path
is not a volume-GUID path
```

The selected child is absent before creation, so filesystem, NTFS, local-fixed-drive, and reparse-point properties must not be asserted for the child until after it exists.

Before each one-component creation, the operator must verify the environment:

```text
selected canonical-input file absent
repository clean
HEAD == origin/main == fresh accepted invocation HEAD
.git/index.lock absent
all prior ordered creation evidence remains valid
```

After each creation, the operator must apply the full filesystem property set to the newly created directory itself:

```text
created directory exists
created directory is exactly the selected path for that step
absolute drive-qualified DOS path
local fixed drive
NTFS
outside repository
not UNC
not device path
not volume-GUID path
not reparse point
no extra sibling or child was created
selected canonical-input file absent
repository clean
HEAD == origin/main == fresh accepted invocation HEAD
.git/index.lock absent
all prior ordered creation evidence remains valid
```

## 7. Failure, Retry, And Cleanup Semantics

Failure before any directory is created is a pre-contact failure for the directory-creation act. It creates no canonical-input publication, consumes no PREPARE_PATHS attempt, and creates no execution authority.

If any directory is created and a later required creation or validation fails, the hierarchy is partially mutated. Partial mutation fails closed. Cleanup, deletion, truncation, renaming, moving, reuse, and silent retry are prohibited.

If operator interruption occurs before any directory is created, no filesystem authority is consumed.

If operator interruption occurs after any authorized directory creation, the directory-creation opportunity is retired. Continuation, cleanup, reuse, and retry are prohibited, and fresh committed governance is required before any further path mutation or canonical-input publication.

The following outcomes retire the current directory-creation opportunity and require fresh committed governance before any further path mutation or canonical-input publication:

```text
operator interruption after any authorized directory creation
unexpected pre-existing authorized child directory
unauthorized intermediate directory creation
ancestor creation succeeds but validation fails
ancestor creation succeeds and leaf creation fails
leaf creation succeeds but validation fails
reparse-point discovery
non-local or non-fixed drive discovery
non-NTFS discovery
repository drift
HEAD/origin_main drift
.git/index.lock discovery
any partial filesystem mutation not exactly matching the ordered model
```

No cleanup authority is created by this correction. Any later cleanup or reuse of a partially created hierarchy requires a separate committed and pushed governance baseline that names the exact path state and preserves historical evidence.

## 8. Authority-Consumption Model

Directory creation is not canonical-input publication.

Directory creation does not:

```text
publish canonical-input bytes
consume the PREPARE_PATHS attempt
invoke PREPARE_PATHS
invoke PREFLIGHT_ONLY
invoke EXECUTE_EXACT_SINGLE_RUN
create execution authority
consume execution authority
close BLOCKER-2
activate BLOCKER-4
```

A successful full directory-creation act consumes only the distinct directory-creation opportunity authorized for that act. It does not consume the later canonical-input publication opportunity.

Canonical-input preparation authority is consumed only by publication of canonical-input bytes at the selected canonical-input file, publication failure after any byte reaches that selected file, candidate validation rejection after publication, operator retirement, or superseding governance.

## 9. Supersession And Non-Reuse Bindings

This correction supersedes the retired lane only as a fresh governance route. It does not edit, reactivate, or reuse the retired lane.

The following retired values are historical only:

```text
prior accepted invocation HEAD: 4b0754825d7f0443a4ee696945995bcf6c63230b
prior publication: NONE
prior selected-path contact: NONE
prior PREPARE_PATHS attempt: UNCONSUMED
prior candidate bytes: NON-AUTHORITATIVE
prior authorization-input identity: NON-AUTHORITATIVE
prior declaration identity: NON-AUTHORITATIVE
prior execution-authorization identity: NON-AUTHORITATIVE
prior run identity: NON-AUTHORITATIVE
```

All future canonical-input bytes, authorization-input identities, declaration identities, execution-authorization identities, run identities, path models, and repository-state bindings must be regenerated after the final fresh accepted invocation HEAD is established.

Any directory created under this correction becomes historical path evidence. Its path, create-before evidence, create-after evidence, filesystem metadata, reparse status, volume profile, and directory identity must be preserved in an external path-creation record during the commit-free window and later committed only when governance permits repository evidence commitment.

For each of the three ordered directory acts, the external path-creation record must bind:

```text
exact path
creation-order index: 1, 2, or 3
immediate-parent identity/path
create-before absence evidence
create-after existence evidence
creation timestamp
local-fixed-drive status
NTFS status
reparse-point status
volume profile or volume identity
directory filesystem identity/file ID where available
operator environment declaration
repository HEAD
origin/main
branch
index-lock state
```

The external path-creation record must make it possible to distinguish three ordered one-component creations from one recursive creation that produced the same final hierarchy.

The current wrapper authorization-input schema must not be expanded by this document. Directory metadata must not be inserted into a wrapper-consumed canonical input unless a separately committed runtime/schema change authorizes that field. In the current schema, directory evidence belongs in the external path-creation record and later governance/result records, not in the wrapper authorization input.

## 10. Required Fresh Governance Chain

This draft is the first correction artifact only. It cannot collapse stages that require post-commit Git identities.

The minimum fresh chain after this draft is reviewed is:

```text
1. Commit and push this path-creation governance correction decision.
2. Create, review, commit, and push a post-commit identity record for this correction decision.
3. Create, review, commit, and push a corrected active-ready Layer-B canonical-input preparation decision that incorporates this correction and supersedes the retired lane.
4. Create, review, commit, and push a post-commit identity record for the corrected active-ready Layer-B decision.
5. Create, review, commit, and push a corrected Layer-C PREPARE_PATHS invocation authorization that explicitly supersedes the retired Layer-C single-mutation restriction, carries the exact corrected commit-free-window mutation model in Section 11, incorporates the corrected path-creation model, and preserves the separation between directory creation, path-creation evidence, canonical-input publication, and PREPARE_PATHS invocation.
6. Create, review, commit, and push a post-commit identity record for the corrected Layer-C authorization.
7. Verify HEAD == origin/main after the final pre-invocation governance commit.
8. Establish a fresh accepted invocation HEAD by explicit non-commit operator declaration.
9. Activate fresh Layer-B canonical-input preparation authority by explicit non-commit operator declaration.
10. Activate the distinct directory-creation act by explicit non-commit operator declaration.
11. Perform only the ordered directory-creation act.
12. Create or publish the external path-creation record inside the corrected commit-free window, after successful validation of all three ordered directory acts and before canonical-input publication.
13. Stop before canonical-input publication.
```

The external path-creation record must not be committed during the corrected commit-free window. Any later repository evidence commitment may occur only after the relevant invocation lane has ended and separate governance permits it.

Canonical-input publication requires a later distinct operational act after fresh candidate bytes are regenerated and validated under the fresh accepted invocation HEAD.

## 11. Fresh Accepted Invocation HEAD And Commit-Free Window

The retired accepted invocation HEAD must not be reused for this correction.

The fresh accepted invocation HEAD can be established only after all required correction governance artifacts and their post-commit identity records are committed and pushed, and after `HEAD` and `origin/main` are verified equal.

The corrected Layer-C authorization must explicitly supersede the retired Layer-C authorization's restriction that commit-free-window mutation is limited to publication of the single canonical input. The corrected Layer-C authorization must carry the exact enumerated mutation model below before the fresh accepted invocation HEAD is established. Supersession must be explicit; it must not rely on implication.

The new commit-free window begins only after the fresh accepted invocation HEAD is explicitly established.

The only permitted external filesystem mutations during the corrected commit-free window are exactly:

```text
1. creation of:
   C:\TORMENT\brainvision_authoritative_inputs

2. creation of:
   C:\TORMENT\brainvision_authoritative_inputs\blocker2_s3b_v0_3

3. creation of:
   C:\TORMENT\brainvision_authoritative_inputs\blocker2_s3b_v0_3\r4_prepare_paths

4. creation or publication of the external path-creation record required by this governance

5. publication of exactly one canonical input at:
   C:\TORMENT\brainvision_authoritative_inputs\blocker2_s3b_v0_3\r4_prepare_paths\r4_prepare_paths_authorization_input_v0_1.canonical.json
```

No other external filesystem mutation is authorized.

No repository file, index entry, branch, ref, tag, Git metadata state, or commit may change during the corrected commit-free window.

Any repository commit during the corrected commit-free window voids activation, retires the accepted invocation HEAD, retires any prepared candidate, retires active preparation authority, and requires a fresh committed and pushed governance baseline.

## 12. Terminal State Of This Draft

This document prepares a correction candidate for review and later commit only.

It ends with:

```text
external directory creation: NOT PERFORMED
canonical input: NOT CREATED NOT PUBLISHED
PREPARE_PATHS: NOT INVOKED
PREFLIGHT_ONLY: NOT INVOKED
EXECUTE_EXACT_SINGLE_RUN: NOT INVOKED
execution authority: NOT CREATED NOT CONSUMED
BLOCKER-2: OPEN
BLOCKER-4: INACTIVE
classification: CORRECTION_DECISION_DRAFT_READY_FOR_REVIEW
```

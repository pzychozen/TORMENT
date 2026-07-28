# TORMENT Brainvision Stage S3B v0.3 BLOCKER-2 Successor PREPARE_PATHS Governance Remediation Design v0.1

## 1. Executive Disposition

This document is a narrow governance-remediation design for the accepted successor `PREPARE_PATHS` evidence gap.

Central question:

```text
Can formal PATHS_PREPARED governance acceptance be reached through honest
retrospective records without rerunning PREPARE_PATHS, or is a separately
governed repeat invocation required?
```

Disposition:

```text
B. RETROSPECTIVE_RECORDS_PRESERVE_HISTORY_BUT_FORMAL_ACCEPTANCE_REQUIRES_SEPARATELY_GOVERNED_REPEAT
```

Retrospective records are useful and should preserve the historical truth: an operator-observed successor `PREPARE_PATHS` invocation reportedly returned `PREPARATION_COMPLETE`. They cannot become the missing invocation-time stdout bytes, the missing invocation-time result artifact, or a separately retained invocation-authorization record. Formal `PATHS_PREPARED` governance acceptance therefore remains blocked until a separately governed remediation route produces durable invocation-time evidence. The scientifically clean route is a fresh, separately governed `PREPARE_PATHS` repeat with fresh accepted-HEAD-bound identities under the remediation-attempt HEAD-uniqueness rule and durable result capture.

This design does not authorize that repeat.

## 2. Scope And Prohibitions

This task is documentation and governance design only.

Created artifact:

```text
research/brainvision/TORMENT_Brainvision_Stage_S3B_v0_3_BLOCKER_2_successor_prepare_paths_governance_remediation_design_v0_1.md
```

Not created:

```text
code implementation
Brainvision runner output
external evidence artifact
retrospective stdout capture
canonical result artifact
lifecycle or preservation record
successor PREFLIGHT authorization document
successor PREFLIGHT canonical input
successor EXECUTE_EXACT_SINGLE_RUN authorization or input
commit
push
```

Preserved controls:

```text
FORMAL_HOLD: ACTIVE
MODE: 0
BLOCKER-2: OPEN
BLOCKER-4: INACTIVE
BRAINVISION: OFFLINE, QUARANTINED, SYNTHETIC/RESEARCH ONLY
```

This design does not modify or integrate `torment_service/kernel/`, live TORMENT memory, production cognition, autonomy, truth-selection, or service/runtime execution.

## 3. Authoritative Baseline And Accepted Inputs

Repository baseline for this design:

```text
repository: C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric
branch: main
HEAD: 125955187061a60124d3df28e8e3c9fc41c8d369
origin/main: 125955187061a60124d3df28e8e3c9fc41c8d369
HEAD == origin/main: true
.git\index.lock: absent
starting status: ## main...origin/main
```

Accepted assessment:

```text
path: docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_POST_PREPARE_PATHS_PATHS_PREPARED_AND_AUTHORIZATION_PRESERVATION_ASSESSMENT_v0.1.md
commit: 125955187061a60124d3df28e8e3c9fc41c8d369
git_blob_oid: 4187226c8b2ab370b661651ee03e3fc56b31a7b1
checked_out_byte_count: 25881
checked_out_byte_sha256: dc404b448a6b2fb96ecd654ad0498abb59b14907518b12ae2665d9075cbb84f3
classification: B. PATHS_PREPARED_SUPPORTED_BY_OPERATOR_TRANSCRIPTION_PENDING_DURABLE_RESULT_AND_INVOCATION_GOVERNANCE_PROVENANCE
```

Accepted assessment findings bound by this design:

```text
technical PATHS_PREPARED semantics: SUPPORTED
formal PATHS_PREPARED governance acceptance: PENDING
operator-observed PREPARATION_COMPLETE: RECORDED
durable successor result artifact: ABSENT
durable successor stdout capture: ABSENT
independent result re-verification: NOT CURRENTLY POSSIBLE
reported pre-invocation governance gates: COMPLETE ACCORDING TO ACCEPTED HANDOFF
separately retained invocation-authorization record: NOT IDENTIFIED
recommended authorization-document lifecycle disposition: PRESERVED_AS_CONSUMED_PREPARATION_RECORD
recommended disposition formally effected: NO
PREFLIGHT progression: BLOCKED
BLOCKER-2: OPEN
```

Accepted `PREPARE_PATHS` authorization document:

```text
path: docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_SUCCESSOR_PREPARE_PATHS_EXECUTION_AUTHORIZATION_v0.1.md
accepted_authorization_document_HEAD: 0762e97b575db50a9266aeb932b2ba382d28b02f
git_blob_oid: 9f1c62bc992cff69c7c857882e8a3dc0f539b4c6
checked_out_byte_count: 16680
checked_out_byte_sha256: b7b1c693193038a2ac4807f8e3bb4a94aa37a39026cc07dce0dabb0c9bc33375
canonical_authorization_declaration_identity: 44dbfb12d0ceea6881bd184d9c3d0ff47c1ae89302236790750f1712151157c5
authorization_status: PREPARED_NOT_ACTIVE
```

Accepted successor `PREPARE_PATHS` input:

```text
path: C:\TORMENT\brainvision_external_assessments\blocker2_s3b_v0_3\SUCCESSOR_PREPARE_PATHS_INPUT_0762e97b575db50a9266aeb932b2ba382d28b02f_5081755497fbc02a1e2f7c52b9b8361e135d9a49d3f602c0b17dfbde0310eead.canonical.json
stored_file_byte_count: 21029
stored_canonical_file_sha256: 9914988c682cd3f0c1ef44dce3ec1d2c525bd8d3127e3b37673618232acc1b84
embedded_schema_derived_authorization_input_identity: 5081755497fbc02a1e2f7c52b9b8361e135d9a49d3f602c0b17dfbde0310eead
candidate_level_declaration_identity: c978c29fe1eb8ca0864d35d3c78f338d95d614add84a1b585427da0be2b9ed02
execution_authorization_identity: 65cc1e581856ec52c8c04a3f5e280e1405f176ad11c10c33d8fcba8b8d1dc3df
run_identity: d740897a74140b3674ee62987d7c98596917fac31b9c760aeaddc37c022c3ae5
result_directory_identity: fcc7db7050e0107e29044d14b4b1aa4d525721cd828bf46b127ea5ec34823c1b
case_set_identity: b24057bb7ec233414d670a3e1e2aabb90f8a2728ff590b0ed4e811faf8e5f1b1
```

Operator-observed but non-retained terminal result:

```text
schema: torment.brainvision.blocker2.operator_wrapper.result.v0.1
wrapper_version: v0.2
mode: PREPARE_PATHS
terminal_label: PREPARATION_COMPLETE
detail: OK
error_classification: NONE
authoritative: false
authority_consumed: false
retained_execution: false
authorization_input_sha256: 9914988c682cd3f0c1ef44dce3ec1d2c525bd8d3127e3b37673618232acc1b84
real_executor_selector: REAL_EXISTING_ABSOLUTE_PATH_A1_A2_A3_A5_V0_1
a6_selected: false
```

Provenance limitation:

```text
result_record_retained: false
successor_result_artifact: absent
successor_stdout_capture: absent
source: authoritative Windows operator console transcription
independent_durable_reverification: not currently possible
```

This design must not silently upgrade that transcription into invocation-time durable evidence.

## 4. Repository And Design Evidence Rules

The operator wrapper implementation returns `PREPARE_PATHS` output from `prepare_paths()` through the CLI stdout path. The inspected code builds a result record, adds path-preparation evidence to it, returns that object to `main()`, and `_print_record()` writes canonical JSON to stdout. The wrapper does not itself persist the returned `PREPARE_PATHS` result object or stdout bytes.

The accepted successor execution-authorization document design states:

```text
PREPARE_PATHS may only be established by wrapper invocation and wrapper result.
Manual filesystem state, reviewer expectation, or design text cannot establish PATHS_PREPARED.
```

The accepted post-`PREPARE_PATHS` assessment currently establishes:

```text
technical interpretation: supported
formal governance acceptance: pending
result evidence level: operator transcription without durable successor stdout/result bytes
invocation governance provenance: reported complete, but no separate durable invocation-authorization record identified
```

Therefore the remediation design must preserve historical truth without creating false evidence. It may recommend future records. It may not transform later narrative, reconstruction, or current filesystem state into the missing invocation-time result bytes.

Historical retained `PREPARE_PATHS` evidence exists in:

```text
C:\TORMENT\brainvision_retained_results\blocker2_s3b_v0_3_preparation\PREPARE_PATHS_RESULT.canonical.json
C:\TORMENT\brainvision_retained_results\blocker2_s3b_v0_3_preparation\PREPARE_PATHS_STDOUT.txt
```

Those files are structural precedent only. They are historical-lane evidence and must not be substituted for the successor-lane returned result or stdout capture.

## 5. Evidence Taxonomy

| Class | Evidence class | Description | Technical support | Formal PATHS_PREPARED acceptance | PREFLIGHT governance eligibility | Scientific or authoritative execution claims |
| --- | --- | --- | --- | --- | --- | --- |
| E0 | Later narrative or recollection | Unbound later statement without exact console text, command, byte counts, hashes, or artifact identity | Insufficient alone | No | No | No |
| E1 | Operator console transcription after invocation | Console output copied after the event without retained original bytes | Supports a bounded technical interpretation if consistent with input, code, and absence checks | No, because the original stdout/result bytes cannot be independently reverified | No | No |
| E2 | Retrospective reconstruction | Later object computed from input, current code/current state, and transcription | Can be a non-authoritative analytical aid only | No, because it is not the original returned object | No | No |
| E3 | Invocation-time stdout capture | Exact stdout bytes captured during invocation, with immediate byte count and SHA-256 | Yes | No alone; only with E4 result capture and E5 authorization/assessment binding | No alone; requires formal acceptance and a separate later PREFLIGHT governance route | No retained execution claim; still only PREPARE evidence |
| E4 | Invocation-time canonical result artifact | Parsed canonical result bytes retained, schema-validated, hash-bound, and independently recomputed from captured stdout | Yes | No alone; only with E5 authorization/assessment binding | No alone; requires formal acceptance and a separate later PREFLIGHT governance route | No retained execution claim; still only PREPARE evidence |
| E5 | Durable governance chain | Tracked or externally immutable chain binding authorization, exact command, invocation event, input bytes, stdout/result bytes, pre/post absence evidence, review, and assessment | Yes | Yes | Yes, if later separate ACTIVE PREFLIGHT governance exists | Only for claims matching the authorized mode; EXECUTE claims require later execution evidence |

Minimum sufficiency conclusions:

```text
technical support: E1 plus accepted input identity, code inspection, and absence checks can support a bounded technical interpretation
formal PATHS_PREPARED acceptance: requires E3, E4, and E5-style authorization and assessment binding together
PREFLIGHT governance eligibility: requires formal PATHS_PREPARED acceptance plus separate ACTIVE PREFLIGHT governance route
scientific or authoritative execution claims: require mode-specific E5 evidence; PREPARE_PATHS evidence never establishes retained execution
```

## 6. Candidate Lane Decision Table

| Lane | What evidence it creates | What it resolves | What it cannot resolve | Risk of historical falsification | Identity implications | Formal PATHS_PREPARED acceptance possible | PREFLIGHT eligibility possible | Required governance prerequisites | Recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R1: retrospective operator attestation only | A tracked attestation binding command, input identity, observed stdout, circumstances, non-retention, current absence checks, and best available invocation timestamp or bounded invocation time window clearly labelled as operator-attested unless supported by contemporaneous metadata | Preserves operator testimony and makes provenance limitation explicit | Cannot become the missing invocation-time wrapper result, stdout bytes, durable invocation timestamp, or invocation authorization record | Medium if later readers treat testimony as captured result bytes; low if labelled E1 | Must reference original identities as historical only; must not create fresh result identity | No; supports technical interpretation only | No | Independent review; exact non-retention language; no claim of replay or contemporaneous capture | Audit preservation only |
| R2: retrospective reconstruction of result object | A clearly labelled reconstruction from canonical input, current implementation/current state, and transcription, displaying `NON_AUTHORITATIVE`, `RETROSPECTIVE`, `ANALYTICAL_ONLY`, `NOT_ORIGINAL_RESULT`, and `NOT_ACCEPTANCE_EVIDENCE`, with its own reconstruction identity | Can show what the result object would look like under stated assumptions | Cannot prove byte identity with lost stdout; cannot prove invocation-time filesystem state or implementation identity if HEAD changed | High if presented as original result; acceptable only if labelled E2 non-authoritative | Must not reuse the original result identity as if retained; any reconstruction needs its own reconstruction identity and labels | No | No | Governance must prohibit use as substitute; must disclose current-state and current-code dependencies | Non-authoritative retrospective analysis only |
| R3: retrospective governance and preservation record without result reconstruction | A tracked record preserving the accepted PREPARE document as non-reusable consumed preparation history, binding accepted assessment and limitations | Resolves lifecycle non-reuse and historical auditability; records no successor execution authority was created or consumed | Cannot establish the missing wrapper result or invocation-authorization provenance; cannot unlock PREFLIGHT | Low if it states formal PATHS_PREPARED remains pending; medium if title/body imply acceptance | References original identities as historical; does not authorize reuse; does not generate new execution/run/result-directory identity | No | No | Independent review; acceptance of documentation-lifecycle meaning only; explicit PREFLIGHT blocked state | Create later as governance remediation, but not in this task |
| R4: separately governed repeat of PREPARE_PATHS | New invocation-time authorization, command, canonical input, stdout/result bytes, hashes, pre/post evidence, and post-run assessment | Can create E3/E4/E5 evidence needed for formal acceptance while preserving original event as historical | Cannot recover original stdout bytes; cannot make repeat the original event | Low if fresh accepted-HEAD-bound identities are used and original invocation remains historical; high if identities are reused to masquerade | Fresh accepted-HEAD-bound execution authorization, run, result-directory and authorization-input identities are required under the current governance rule; this is repository-state freshness, not cryptographic proof of unique invocation events | Yes, if repeat returns `PREPARATION_COMPLETE` and durable evidence validates | Possible only after formal acceptance and later separate ACTIVE PREFLIGHT governance | Fresh governance design/authorization; independent review; exact capture plan; no PREFLIGHT authority | Recommended route if formal acceptance remains required, but not authorized |

Decision:

```text
R1: useful but insufficient
R2: non-authoritative retrospective analysis only
R3: historical preservation and non-reuse governance; no formal acceptance
R4: recommended route if formal acceptance remains required, but not authorized
```

## 7. Identity-Reuse Analysis

The original reported invocation is historical and immutable. A remediation invocation must not masquerade as the original event. Absence of `authority_consumed=true` does not automatically permit historical invocation identity reuse.

| Identity surface | IMPLEMENTATION | GOVERNANCE |
| --- | --- | --- |
| Logical input reuse | The same logical case set, roots, host/volume, policies, and repository-state inputs can produce the same semantic payload when the accepted HEAD and source identities are unchanged. The implementation has no separate logical-invocation discriminator. | Historical logical input may be referenced for analysis only. A remediation repeat must be bound to a distinct accepted HEAD and fresh governance route under the HEAD-uniqueness rule. |
| Stored canonical input-byte reuse | Old bytes may fail current accepted-HEAD validation or may remain parseable depending on their bindings. That is an implementation property. | Historical stored bytes must not be reused as the live repeat input, even where the implementation would accept them, because doing so would blur the original operator-observed event and the remediation event. |
| Authorization-input identity reuse | The identity is computed from the canonical authorization payload excluding `authorization_input_identity`. If the payload is identical, the identity is identical. The implementation does not add an event discriminator. | Reuse is prohibited for remediation. A fresh canonical repeat input must bind a distinct accepted HEAD and fresh tracked authorization-document identity, producing a fresh repository-state-bound authorization-input identity. |
| Execution-authorization identity reuse | The current execution-authorization identity preimage has no timestamp, nonce, attempt counter, invocation identifier, governance-route identity, remediation marker, execution_authorization_document_identity, or authorization_input_identity. Same accepted HEAD, source identities, roots, case set, host/volume, and policies produce the same identity. | Reuse is prohibited for remediation. Fresh accepted-HEAD-bound execution authorization identity is required under the remediation-attempt HEAD-uniqueness rule, but this remains repository-state freshness, not true event identity. |
| Run-identity reuse | The run identity derives from execution authorization identity, expected branch/HEAD/origin, case set/order, root identities, result-directory identity, selector controls, and A6 exclusion. If those are unchanged, it repeats. | Reuse is prohibited for remediation. Fresh accepted-HEAD-bound run identity is required through the fresh execution authorization identity and fresh derived result-directory identity. |
| Result-directory identity reuse | The result-directory identity is a path-identity hash for role `result_directory` over the derived absent child path. Same execution authorization identity and result parent produce the same child path and identity. `PREPARE_PATHS` does not create that child directory. | Reuse is prohibited for remediation. Fresh accepted-HEAD-bound result-directory path and identity are required to keep the repeat from masquerading as the original event. |
| Authorization-document identity reuse | PERMITS CURRENT REUSE. The original authorization document remains tracked at the current HEAD with git blob `9f1c62bc992cff69c7c857882e8a3dc0f539b4c6`. The wrapper's current-identity validation would accept that unchanged tracked document if its five-field identity were supplied correctly. | PROHIBITS REUSE. The document's single preparation purpose is exhausted. It is historical documentation-lifecycle authority only and must not become live repeat authority. A remediation repeat requires a fresh tracked PREPARE authorization document at a new path, with a new declaration and independently recomputed five-field identity. |

The authorization-document identity is the clearest surface where implementation permissiveness and governance prohibition diverge.

The prohibition must therefore be enforced by governance review and exact artifact binding rather than assumed from wrapper rejection.

Identity disposition:

```text
original_execution_authorization_identity: HISTORICAL_ONLY_DO_NOT_REUSE_FOR_REPEAT
original_run_identity: HISTORICAL_ONLY_DO_NOT_REUSE_FOR_REPEAT
original_result_directory_identity: HISTORICAL_ONLY_DO_NOT_REUSE_FOR_REPEAT
original_authorization_input_identity: HISTORICAL_ONLY_DO_NOT_REUSE_FOR_REPEAT
original_authorization_document_identity: HISTORICAL_REFERENCE_ONLY_NOT_REPEAT_AUTHORITY
```

### Identity Freshness Is Repository-State Freshness, Not Event Freshness

The retained identity model contains no invocation-event discriminator.

It does not include an invocation timestamp, nonce, attempt counter, invocation identifier, remediation identifier, governance-route identity, authorization-document identity or authorization-input identity in the execution-authorization identity preimage.

Under the current schema, identity freshness is achievable only transitively through a distinct accepted repository HEAD and any source identities changed by that HEAD.

It distinguishes repository states, not invocation events.

Implementation analysis:

```text
execution_authorization_identity preimage: 31 fields
event timestamp: NOT PRESENT
nonce: NOT PRESENT
attempt counter: NOT PRESENT
invocation identifier: NOT PRESENT
governance route: NOT PRESENT
remediation marker: NOT PRESENT
execution_authorization_document_identity: NOT PRESENT
authorization_input_identity: NOT PRESENT
only invocation-variable preimage inputs: expected_head, expected_origin_main, source_identities
```

Therefore two `PREPARE_PATHS` invocations at the same accepted HEAD, with the same roots, case set, host/volume and policy identities, produce the same:

```text
execution_authorization_identity
run_identity
result_directory_identity
authorization_input_identity
```

`PREPARE_PATHS` creates neither the successor result directory nor the global authority entry, so the implementation has no repetition guard that distinguishes a second same-HEAD invocation.

```text
SAME_HEAD_REMEDIATION_REPEAT: PROHIBITED_BY_GOVERNANCE
```

Remediation attempt rule:

```text
REMEDIATION_ATTEMPT_HEAD_UNIQUENESS:

Each separately authorized remediation attempt must bind a distinct accepted HEAD.

No two remediation attempts may share an accepted HEAD.

If an attempt fails before durable capture or formal assessment completes, a
later attempt requires a new committed and pushed governance baseline before
new authorization is prepared.
```

This HEAD-uniqueness rule is a governance substitute for missing per-event identity. It does not create true event identity.

A true per-event identity would require a separately designed, reviewed and authorized schema and implementation change adding an event discriminator to the identity preimage.

No such implementation change is designed or authorized here.

Identity conclusion:

```text
true per-event identity: not available under current schema
fresh repository-state-bound identity: available only through a distinct accepted HEAD
same-HEAD remediation repeat: prohibited by governance
implementation change for true event identity: identified but not designed or authorized
```

## 8. Future Repeat Evidence Capture Design

If R4 is selected by later governance, the minimum durable evidence package must be designed before invocation and must prevent the current provenance problem from recurring.

Required package:

Mandatory first artifact:

```text
Artifact:
Fresh tracked PREPARE remediation authorization document

Location:
Tracked in Git at a new repository-relative path

Required timing:
Designed, independently reviewed, accepted, committed and pushed before the
repeat canonical input is prepared

Required binding:
Five-field identity independently recomputed at the accepted HEAD:
path
git_blob_oid
checked_out_byte_sha256
canonical_authorization_declaration_identity
authorization_status

Governance requirement:
Mandatory. The wrapper requires execution_authorization_document_identity for
PREPARE_PATHS and validates the tracked file's blob and checked-out bytes
against the current accepted HEAD.

Reuse rule:
The existing PREPARE_PATHS authorization document remains historical,
preserved and non-reusable. It must not be edited in place or supplied as live
authorization for the remediation repeat.
```

| Evidence item | Location class | Timing | Independent recomputation | Notes |
| --- | --- | --- | --- | --- |
| Fresh tracked PREPARE remediation authorization document | Tracked in Git at a new repository-relative path | Designed, independently reviewed, accepted, committed and pushed before the repeat canonical input is prepared | Five-field identity independently recomputed at the accepted HEAD: path, git_blob_oid, checked_out_byte_sha256, canonical_authorization_declaration_identity, authorization_status | Mandatory. The wrapper requires `execution_authorization_document_identity` for `PREPARE_PATHS` and validates the tracked file's blob and checked-out bytes against the current accepted HEAD. The existing `PREPARE_PATHS` authorization document remains historical, preserved and non-reusable. It must not be edited in place or supplied as live authorization for the remediation repeat. |
| Exact authorized command record | Tracked in Git or immutable external record referenced by Git | Before invocation | Reviewer verifies exact command and input path | Must bind mode `PREPARE_PATHS` only |
| Authorization decision record | Tracked in Git or immutable external record referenced by Git | Before invocation | Governance review verifies decision scope | Must name Hilmir/operator authority and prohibit PREFLIGHT/EXECUTE |
| Canonical input bytes | Immutable external artifact with tracked reference | Before invocation | Byte count, SHA-256, schema, embedded identity recomputed | Must be fresh and bound to then-current accepted HEAD |
| Canonical input byte count and SHA-256 | Tracked assessment/reference plus external artifact metadata | Before invocation | Independent hash recomputation | Must distinguish stored file SHA from embedded input identity |
| Embedded input identity | Tracked reference and canonical input | Before invocation | Recomputed by read-only identity rule | Must exclude self-field per wrapper rule |
| Accepted repository HEAD/origin-main evidence | Tracked or immutable pre-invocation record | Immediately before invocation | `git rev-parse` values independently checked | Must show `HEAD == origin/main` |
| Clean-tree evidence | Tracked or immutable pre-invocation record | Immediately before invocation | `git status --short --branch --untracked-files=all` reviewed | Must include untracked-file state |
| Index-lock absence | Tracked or immutable pre-invocation record | Immediately before invocation | `Test-Path .git\index.lock` reviewed | Must be absent |
| Pre-invocation successor-surface absence | Immutable external or tracked record | Immediately before invocation | File existence checks independently reviewed | Result directory, authority entry, gate, run result, completion all absent |
| Invocation timestamp | Immutable external record and post-run assessment | During invocation | Operator/host clock context recorded | Must be contemporaneous enough to bind event |
| Exact stdout bytes | Immutable external artifact | During invocation | Byte count and SHA-256 immediately computed | Copying console text later is insufficient |
| Stdout byte count and SHA-256 | Tracked reference and immutable external artifact metadata | Immediately after invocation | Independent hash recomputation | Must bind exact bytes emitted by wrapper |
| Parsed canonical result bytes | Immutable external artifact | Immediately after invocation | Parse, canonical reserialize, byte count, SHA-256 | Must be derived from captured stdout, not later narrative |
| Result schema validation result | Tracked post-run assessment and/or immutable validation log | Immediately after invocation | Independent read-only validation | Must validate wrapper result schema and fields |
| Path/root evidence | Immutable external artifact or tracked record | During/after invocation | Independent review of reported path evidence | Must bind fixed roots and path identities using exact field names where structured: `drive_type`, `reparse_status`, `filesystem_name`, `volume_serial_number` |
| Successor identity bindings | Tracked post-run assessment | After invocation | Independent recomputation from fresh input/result | Execution, run, result-directory, case-set, input identities |
| Post-invocation successor-surface absence | Immutable external or tracked record | Immediately after invocation | File existence checks independently reviewed | PREPARE should not create successor child surfaces |
| `authority_consumed=false` and `retained_execution=false` | Captured stdout/result artifact and tracked assessment | Immediately after invocation | Parsed result validates fields | Must remain preparation-only |
| Operator identity | Authorization and invocation records | Before/during invocation | Governance review | Must bind Hilmir/operator role without inventing missing facts |
| Review disposition | Tracked assessment or immutable external review record | Before and after invocation as appropriate | Independent review | Must separate input review, invocation authorization, and post-run acceptance |

Artifact placement rule:

```text
created_before_invocation: fresh tracked PREPARE remediation authorization document, committed and pushed; authorization decision; exact command record; canonical input; immediate clean/absence checks for PREPARE only
created_during_invocation: exact stdout byte capture and timestamped invocation log
created_immediately_after_invocation: stdout hash, parsed canonical result artifact, result hash, post-invocation absence checks
tracked_in_Git: governance decisions, references to immutable external artifacts, post-run assessment, lifecycle disposition
external_and_immutable: canonical input bytes, stdout bytes, parsed result bytes, raw command transcript/log where large or host-specific
independently_recomputed: byte hashes, embedded identities, repository binding, source/document identities, path/root evidence, absence checks
```

Required governance ordering before a repeat input exists:

```text
fresh remediation authorization-document design
-> independent review
-> governance acceptance
-> commit and push
-> identity recomputation at the new accepted HEAD
-> separate authorization for repeat-input preparation
-> fresh canonical repeat input preparation
```

Do not create or draft that document in this correction task.

Capture mechanism requirement:

```text
For any future repeat, --format json must be used.

Stdout must be redirected or tee-captured directly during invocation into a
pre-authorized immutable external target.

The exact stdout byte stream includes the canonical JSON record followed by one
newline emitted by _print_record().

The parsed canonical result artifact must contain canonical_json_bytes(record)
without the stdout trailing newline.

Therefore stdout SHA-256 and canonical-result SHA-256 are expected to differ
unless the capture procedure deliberately normalizes and separately records
both representations.

--format human and --format both are prohibited for the authoritative capture
because they introduce non-JSON stdout lines.
```

Manual copying from the console after completion is E1 retrospective transcription and is insufficient.

No executable Windows command is provided or authorized by this design revision.

Risk control:

```text
copying console text after the event recreates the current E1 problem
future capture must preserve exact bytes during invocation
post-hoc reconstruction may be included only as E2 non-authoritative analysis
```

## 9. Preservation Record Design

A future tracked preservation/lifecycle record for the existing `PREPARE_PATHS` authorization document should bind:

```text
authorization_document_path: docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_SUCCESSOR_PREPARE_PATHS_EXECUTION_AUTHORIZATION_v0.1.md
authorization_document_five_field_identity: path, git_blob_oid, checked_out_byte_sha256, canonical_authorization_declaration_identity, authorization_status
accepted_authorization_document_HEAD: 0762e97b575db50a9266aeb932b2ba382d28b02f
canonical_PREPARE_PATHS_input_identities: stored file SHA-256, embedded authorization input identity, declaration identity, execution authorization identity, run identity, result-directory identity, case-set identity
accepted_post_PREPARE_PATHS_assessment_path: docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_POST_PREPARE_PATHS_PATHS_PREPARED_AND_AUTHORIZATION_PRESERVATION_ASSESSMENT_v0.1.md
accepted_post_PREPARE_PATHS_assessment_commit: 125955187061a60124d3df28e8e3c9fc41c8d369
accepted_assessment_classification: B. PATHS_PREPARED_SUPPORTED_BY_OPERATOR_TRANSCRIPTION_PENDING_DURABLE_RESULT_AND_INVOCATION_GOVERNANCE_PROVENANCE
operator_observed_invocation: recorded as E1 operator transcription
durable_result_limitation: successor result/stdout artifacts absent
invocation_governance_provenance_limitation: separate invocation-authorization record not identified
recommended_lifecycle_disposition: PRESERVED_AS_CONSUMED_PREPARATION_RECORD
authority_consumed: false
successor_execution_authority_created: false
successor_global_authority_entry_absent: true
historical_lane_unchanged: true
PREFLIGHT_blocked: true
BLOCKER-2: OPEN
```

Recommended behavior for the future record:

```text
effect_preservation_as_non_reusable_documentation_lifecycle_history: YES
effect_formal_PATHS_PREPARED_acceptance: NO
record_formal_PATHS_PREPARED_acceptance_as_pending: YES
depend_on_remediation_lane_decision_for_PREFLIGHT_progression: YES
```

Rationale: preserving the original `PREPARE_PATHS` authorization document as historical and non-reusable is conservative because it prevents a second use of the same preparation authority. That preservation must not be cited as formal `PATHS_PREPARED` acceptance. Formal acceptance depends on the remediation-lane decision, and this design recommends R4 if formal acceptance is required.

Historical preservation records existing fact and must not depend on a future remediation event succeeding.

The preservation record may therefore be separately effected before R4.

Formal `PATHS_PREPARED` acceptance and PREFLIGHT eligibility remain dependent on successful remediation and later independent governance acceptance.

This document does not create that preservation record.

## 10. Central Decision

Formal `PATHS_PREPARED` governance acceptance cannot be reached by retrospective records alone under the accepted evidence rules, because:

```text
the original returned stdout/result bytes were not retained
the wrapper does not itself persist PREPARE_PATHS result output
the accepted design requires wrapper result evidence for PATHS_PREPARED
operator transcription is useful but is not the original result artifact
reconstruction is useful only as non-authoritative analysis
the separate invocation-authorization record path and identity are not identified
```

A separately governed repeat can be scientifically and governance-valid if it:

```text
preserves the original invocation as historical, non-retained operator-observed evidence
uses a fresh governance route and fresh accepted-HEAD-bound identities under the remediation-attempt HEAD-uniqueness rule
does not reuse old canonical input bytes or old successor invocation identities
captures exact stdout/result bytes during invocation
hashes and validates the result immediately
keeps PREFLIGHT prohibited until remediation evidence is independently accepted
```

Repeat recommendation:

```text
recommended_for_formal_PATHS_PREPARED_acceptance: YES
authorized_by_this_design: NO
```

## 11. Safety Conclusions

This design explicitly preserves:

```text
no rerun authorized by the design
no external artifact creation authorized
no preservation record created or authorized for creation by this task
no repeat authorization document created
no repeat canonical input created
no PREFLIGHT artifact preparation authorized
no PREFLIGHT authorization document designed, drafted, created, or authorized
no PREFLIGHT canonical input designed, drafted, created, or authorized
no PREFLIGHT invocation authorized
EXECUTE_EXACT_SINGLE_RUN unauthorized
BLOCKER-2 open
BLOCKER-4 inactive
FORMAL_HOLD active
MODE 0
```

PREFLIGHT remains blocked until remediation is completed and independently accepted through a separate governance path.

## 12. Read-Only Analysis Log

Read-only commands and observations used for this design:

```text
git status --short --branch --untracked-files=all
result: ## main...origin/main

git rev-parse --abbrev-ref HEAD
result: main

git rev-parse HEAD
result: 125955187061a60124d3df28e8e3c9fc41c8d369

git rev-parse origin/main
result: 125955187061a60124d3df28e8e3c9fc41c8d369

Test-Path .git\index.lock
result: False

git log -1 --oneline
result: 1259551 docs(brainvision): assess blocker 2 successor path preparation

rg over accepted assessment
result: accepted classification, durable-result gap, invocation-governance gap, and PREFLIGHT blocked state inspected

rg/Get-Content over successor lane design and execution-authorization document design
result: lifecycle transition rules, PREPARE/PREFLIGHT split, ACTIVE requirement for later modes, identity-freshness requirements, and preservation rules inspected

rg/Get-Content over operator wrapper and retained identity code
result: result_record, prepare_paths, stdout printing path, input identity, execution authorization identity, run identity, and result-directory identity preimage categories inspected without invoking a runner

Get-FileHash and stdlib Python JSON read of canonical successor PREPARE_PATHS input
result: stored byte count 21029, SHA-256 9914988c682cd3f0c1ef44dce3ec1d2c525bd8d3127e3b37673618232acc1b84, schema/mode/status and embedded identities matched accepted values

Get-ChildItem over historical retained preparation directory
result: historical PREPARE_PATHS_RESULT.canonical.json and PREPARE_PATHS_STDOUT.txt observed as structural precedent only

git ls-tree HEAD over accepted assessment and accepted authorization document
result: accepted assessment blob 4187226c8b2ab370b661651ee03e3fc56b31a7b1 and authorization-document blob 9f1c62bc992cff69c7c857882e8a3dc0f539b4c6 observed
```

No Brainvision wrapper mode, helper mutation path, or authoritative runner was invoked.

## 13. Terminal Disposition

```text
B. RETROSPECTIVE_RECORDS_PRESERVE_HISTORY_BUT_FORMAL_ACCEPTANCE_REQUIRES_SEPARATELY_GOVERNED_REPEAT
```

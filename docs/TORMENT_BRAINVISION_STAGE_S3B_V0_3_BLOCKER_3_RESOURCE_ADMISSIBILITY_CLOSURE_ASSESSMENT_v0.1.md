# TORMENT Brainvision Stage S3B v0.3 BLOCKER-3 Resource-Admissibility Closure Assessment v0.1

## 1. DOCUMENT STATUS

```text
document_class                    = closure assessment (docs-only)
selected_blocker                  = BLOCKER-3
authority_created                 = none
implementation_authorized         = false
execution_authorized              = false
resource_stress_execution_authorized = false
platform_probe_authorized         = false
manifest_contact_authorized       = false
real_publication_authorized       = false
real_recovery_authorized          = false
source_modified_by_this_document  = false
tests_modified_by_this_document   = false
prior_docs_modified               = false
git_mutations_by_this_document    = none
```

This assessment is descriptive and evidence-driven. It does not modify
implementation or tests. It does not automatically enact closure merely because
implementation, review, and findings are complete.

## 2. ASSESSMENT QUESTION

Question assessed:

```text
Has BLOCKER-3 established a complete, fail-closed, bounded, identity-bound,
cross-platform-tested resource-admissibility boundary for the authorized
synthetic Stage S3B v0.3 durable publication and recovery surfaces, with no
presently identified binding defect requiring further BLOCKER-3 implementation?
```

Assessment answer:

```text
YES, within the authorized synthetic/offline Stage S3B v0.3 publication and
recovery scope only.
```

This assessment separates that answer from platform readiness, production
readiness, real publication or recovery, BLOCKER-1, BLOCKER-2, BLOCKER-4, and
scientific closure.

## 3. GOVERNING LINEAGE

Full BLOCKER-3 lineage assessed:

```text
0d52dc0 docs(research): select resource bounds as first platform blocker
35d7b6e docs(research): specify blocker 3 resource admissibility
01a720c docs(research): authorize blocker 3 resource admissibility implementation
164680b docs(research): correct blocker 3 implementation surface
c03d5f9 research(brainvision): implement blocker 3 resource admissibility
843f861 docs(research): record blocker 3 resource admissibility findings
```

Current baseline:

```text
843f86132bd30e05ccbed757743c038024ba58e8
```

Reviewed governing evidence:

```text
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_3_RESOURCE_ADMISSIBILITY_IMPLEMENTATION_SPECIFICATION_v0.1.md
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_3_RESOURCE_ADMISSIBILITY_IMPLEMENTATION_AUTHORIZATION_v0.1.md
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_3_RESOURCE_ADMISSIBILITY_IMPLEMENTATION_SURFACE_CORRECTION_v0.1.md
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_3_RESOURCE_ADMISSIBILITY_IMPLEMENTATION_FINDINGS_v0.1.md
committed source and tests at c03d5f90342f0d17705a9b73c88252e05afcfb8f
```

## 4. AUTHORIZED SCOPE

BLOCKER-3 is assessed only for the authorized synthetic, offline Stage S3B v0.3
durable publication and recovery resource-admissibility boundary.

The implementation commit changed exactly these eight authorized paths:

```text
research/brainvision/durable_evidence_schema_v0_3.py
research/brainvision/durable_evidence_publication_v0_3.py
research/brainvision/durable_evidence_publication_recovery_v0_3.py
research/brainvision/test_durable_evidence_publication_v0_3.py
research/brainvision/test_durable_evidence_publication_recovery_v0_3.py
research/brainvision/test_durable_evidence_resource_admissibility_v0_3.py
research/brainvision/test_durable_evidence_publication_resource_bounds_v0_3.py
research/brainvision/test_durable_evidence_publication_recovery_resource_bounds_v0_3.py
```

The separate findings record changed exactly one docs path:

```text
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_3_RESOURCE_ADMISSIBILITY_IMPLEMENTATION_FINDINGS_v0.1.md
```

No production, kernel, service, memory, descriptor, PsiTRS, scientific-runner,
manifest, result-tree, real-publication, or real-recovery path is within this
closure scope.

## 5. CLOSURE CRITERIA MATRIX

| Criterion | Result | Assessment |
|---|---|---|
| C1. Authorized surface fidelity | SATISFIED | The implementation commit changed exactly eight authorized paths, no ninth implementation path was included, the findings record changed one docs path, and no prohibited surface changed. |
| C2. Binding resource ceilings | SATISFIED | Explicit deterministic ceilings cover structural, object, artifact, aggregate, staging, and recovery budgets and are included in the resource-policy declaration. |
| C3. Policy identity | SATISFIED | The policy schema identity and SHA-256 match the required values, the digest is computed from canonical policy material, and publication and recovery bind it explicitly. |
| C4. Publication sequencing | SATISFIED | Durable authority and attempt precede resource work; complete resource and capacity admission precedes staging-directory creation and artifact writes. |
| C5. Recovery sequencing | SATISFIED | Exact inventory, type/read admission, bounded reads, per-artifact limits, cumulative budget, canonical validation, semantic validation, regenerated bytes, and expected hashes are ordered fail-closed. |
| C6. Exact failure mappings | SATISFIED | J1/J2 resource failure families and precedence are deterministic and tested; no resource failure path is identified that reaches success, retry, partial completion, or incorrect completion state. |
| C7. Non-mutation | SATISFIED | Rejection preserves final artifacts, final inventory, the original J1 chain, and absence of J2 verified/completed records; recovery does not claim original J1 completion. |
| C8. Compatibility preservation | SATISFIED | Existing durable-evidence, boundary, classification, replay, and Windows adapter behavior were preserved by the recorded passing evidence. |
| C9. Cross-platform evidence | SATISFIED | Corrected Windows and Linux/POSIX suites passed, with the expected Windows symlink skip and Linux symlink execution. |
| C10. Independent review | SATISFIED | The initial fixture-only objection was corrected inside authority, corrected Linux/POSIX review was accepted, GPT reconciled the authoritative Windows bytes, and no binding review objection remains recorded. |
| C11. Scope completeness | SATISFIED | No required BLOCKER-3 resource-admissibility obligation from the specification remains unimplemented. |
| C12. Residual risks | SATISFIED | Residual risks are assigned to other blockers, non-binding future hardening, or out-of-scope domains rather than BLOCKER-3 binding defects. |

## 6. RESOURCE POLICY COMPLETENESS

Binding ceilings assessed as present and explicit:

```text
MAX_RESOURCE_NESTING_DEPTH                    = 32
MAX_RESOURCE_CONTAINER_MEMBERS_PER_CONTAINER = 4096
MAX_STORED_RECORD_OBJECT_BYTES                = 65536
MAX_STORED_BUNDLE_OBJECT_BYTES                = 4194304
MAX_RESOURCE_TOTAL_NODE_COUNT                 = 16384
MAX_RESOURCE_SINGLE_STRING_ASCII_BYTES        = 1048576
MAX_RESOURCE_TOTAL_STRING_ASCII_BYTES         = 4194304
MAX_RESOURCE_INTEGER_ABS                      = 9223372036854775807
MAX_PUBLICATION_SOURCE_BUNDLE_BYTES           = 4194304
MAX_PUBLICATION_ARTIFACT_COUNT                = 3
MAX_PUBLICATION_RESULT_ARTIFACT_BYTES         = 16384
MAX_PUBLICATION_EXECUTION_ENVELOPE_BYTES      = 8388608
MAX_PUBLICATION_SUMMARY_BYTES                 = 1024
MAX_PUBLICATION_ARTIFACT_SET_BYTES            = 8406016
MAX_PUBLICATION_STAGING_WRITE_BYTES           = 8406016
MAX_PUBLICATION_RECOVERY_VERIFICATION_BYTES   = 8406016
```

Aggregate arithmetic remains exact:

```text
16384 + 8388608 + 1024 = 8406016
```

The equal source-bundle and stored-bundle ceilings remain independently
enforced. All binding values are explicit, deterministic, and included in the
ordered policy declaration.

Policy identity:

```text
policy_schema_identity =
durable-evidence-resource-admissibility-policy-v0.3

policy_sha256 =
d845ac1475051c21da1a65fefb3551fdc29af87f53ec4fc21ec12625b64f5ae8
```

The implementation computes the digest from canonical policy material via the
policy declaration and canonical JSON bytes. It does not rely on an unexplained
hardcoded predicted digest.

## 7. PUBLICATION BOUNDARY ASSESSMENT

Publication sequencing is assessed as satisfied:

```text
durable authority acceptance
durable publication attempt
resource preflight
complete in-memory artifact generation
per-artifact validation
aggregate validation
explicit synthetic staging-capacity validation
staging-directory creation
artifact writes
staging verification
durability
promotion
final verification
durable publication completion
```

The publication path validates the explicit
`resource_admissibility_policy_identity`, applies bounded canonical source
validation, generates the complete artifact byte map in memory, validates
per-artifact and aggregate budgets, and validates the synthetic capacity result
before staging-directory creation.

Capacity handling fails closed by default. Only an explicitly supplied
pytest-local synthetic positive adapter can confirm capacity. No real
disk-capacity probing is introduced or claimed.

Resource rejection can leave durable authority and attempted records, as
authorized, but it cannot create `PUBLICATION_COMPLETED`.

## 8. RECOVERY BOUNDARY ASSESSMENT

Recovery sequencing is assessed as satisfied:

```text
exact inventory admission
file-type/readability admission
bounded read
per-artifact limit
cumulative recovery budget
canonical validation
semantic validation
regenerated-byte comparison
expected-hash comparison
```

The reviewed recovery path performs exact final-directory inventory admission
before artifact type and read admission. Artifact reads use bounded
`lstat`/open/`fstat` admission and reject symlinks, directories, non-regular
files, identity changes, read indeterminacy, and oversized inputs before
canonical or semantic parsing.

No unbounded final-artifact `Path.read_bytes()` route remains in the reviewed
recovery path. The remaining `read_bytes()` use identified in source is a
publication final read-back route, not the recovery final-artifact admission
route assessed for BLOCKER-3 recovery.

J2 remains evidence-only. It does not generate, stage, promote, repair,
replace, delete, or mutate publication artifacts and does not reconstruct or
claim original J1 completion.

## 9. FAILURE-MAPPING ASSESSMENT

J1 top-level resource classifications remain deterministic:

```text
PUBLICATION_RESOURCE_ADMISSIBILITY_FAILED
PUBLICATION_STAGING_SPACE_BUDGET_UNAVAILABLE
PUBLICATION_RESOURCE_ADMISSIBILITY_INDETERMINATE
```

J2 top-level resource classifications remain deterministic:

```text
PUBLICATION_RECOVERY_RESOURCE_ADMISSIBILITY_FAILED
PUBLICATION_RECOVERY_VERIFICATION_BUDGET_EXCEEDED
PUBLICATION_RECOVERY_RESOURCE_ADMISSIBILITY_INDETERMINATE
```

The implemented secondary-code mappings match the specification for resource
limit failures, artifact-size failures, artifact-set failures, summary-size
failures, structure/string/integer failures, staging-capacity failure, recovery
verification budget failure, policy identity mismatch, and type/read
indeterminacy.

No assessed resource failure silently falls into:

```text
generic success
unbounded retry
partial completion
incorrect publication-completed state
incorrect recovery-completed state
```

## 10. NON-MUTATION ASSESSMENT

Resource rejection preserves:

```text
final artifacts
final inventory
original J1 chain
absence of J2 verified/completed records after rejection
```

The corrected POSIX symlink case established that:

```text
the final directory retained exactly three expected names
the summary artifact path was replaced by a symlink
the symlink target was outside final_directory
inventory admission passed
type admission rejected the symlink
primary classification =
PUBLICATION_RECOVERY_RESOURCE_ADMISSIBILITY_INDETERMINATE
secondary failure =
RECOVERY_ARTIFACT_TYPE_INVALID
```

The non-mutation evidence is sufficient for BLOCKER-3's authorized synthetic
scope. It does not prove crash consistency, post-crash attribution, or platform
durability.

## 11. COMPATIBILITY AND REGRESSION EVIDENCE

Recorded compatibility evidence:

```text
pre-existing durable-evidence tests:
172 passed

boundary tests:
17 passed
```

Recorded complete Windows evidence before the POSIX fixture correction:

```text
full Stage S3B v0.3 suite:
233 passed, 1 skipped - twice
```

Existing classifications, replay behavior, and Windows adapter behavior are
assessed as preserved because the implementation did not modify replay modules
or Windows adapters, and the existing durable-evidence and boundary suites
remained green.

## 12. CROSS-PLATFORM EVIDENCE

Corrected Windows evidence:

```text
Windows corrected full suite:
233 passed, 1 skipped - twice

Windows focused resource suite:
61 passed, 1 skipped - twice
```

Corrected Linux/POSIX evidence:

```text
Linux/POSIX corrected full suite:
234 passed

Linux/POSIX focused resource suite:
62 passed
```

The Windows skip is the synthetic symlink case, skipped when the host does not
permit symlink creation. The Linux/POSIX run executed that symlink case and
therefore has one additional passing test.

The initial Linux/POSIX result was:

```text
233 passed, 1 failed
```

The sole failure was a test-fixture defect: the symlink target was inside the
final publication directory, creating a fourth inventory entry and correctly
triggering inventory rejection before type admission. The authorized correction
changed the target to:

```python
replacement = tmp_path / "external_symlink_target.txt"
```

Stale cloud-mounted file reconciliation is assessed as sufficient for this
closure assessment. The record ties the reconstructed Linux evidence to the
authoritative Windows file by corrected line, exact eight-file surface, Windows
test evidence, file size, and SHA-256:

```text
stale copy size:
13951 bytes

corrected authoritative Windows size:
13931 bytes

authoritative corrected Windows SHA-256:
a352598c20b2f3e18fe34a4fdddda9f4a11d7faad4f944b2edba48b350e610b7
```

## 13. INDEPENDENT-REVIEW EVIDENCE

Independent review evidence assessed:

```text
Claude initial verdict found one fixture-only defect
Codex corrected only the authorized test fixture
Claude corrected Linux/POSIX verdict accepted the candidate
GPT independently reconciled the authoritative Windows bytes and accepted Claude's review
Claude independently accepted the findings record
```

Accepted GPT review verdict:

```text
A. ACCEPT_CLAUDE_CORRECTED_IMPLEMENTATION_REVIEW
```

No binding review objection remains unresolved in the governing evidence. The
only identified defect was fixture-only, was corrected within the authorized
test path, and did not require production source, classification, precedence,
assertion, policy-identity, replay, boundary, hidden-test, or capacity-probe
changes.

## 14. RESIDUAL-RISK CLASSIFICATION

| Residual risk | Classification | Assessment |
|---|---|---|
| Real filesystem capacity | OTHER_BLOCKER | BLOCKER-3 uses explicit synthetic capacity admission and does not claim real free-space availability. |
| Platform-specific durability semantics | OTHER_BLOCKER | Directory durability remains BLOCKER-1. |
| Concurrent interference | NON_BINDING_FUTURE_HARDENING | Not assigned to BLOCKER-3 beyond fail-closed type/read admission and non-mutation in synthetic scope. |
| Post-admission filesystem races | NON_BINDING_FUTURE_HARDENING | The recovery path detects observed type/identity changes fail-closed but does not claim race-free filesystem security. |
| Crash consistency | OTHER_BLOCKER | Crash survival and attribution are outside BLOCKER-3 and remain platform/durability concerns. |
| Real publication integration | OTHER_BLOCKER | Same-volume no-replace promotion and real finalization remain BLOCKER-2 or later real-operation authorization. |
| Recovery from real evidence | OTHER_BLOCKER | Real recovery remains unauthorized and outside this synthetic closure. |
| Broader malicious-input surface | NON_BINDING_FUTURE_HARDENING | The authorized bounded synthetic surface is covered; broader adversarial production surfaces are not imported into BLOCKER-3. |
| Production readiness | OUT_OF_SCOPE | Explicitly not established. |
| Scientific closure | OUT_OF_SCOPE | Scientific truth remains bound to the durable scientific bundle plus completion receipt, not publication/recovery resource bounds. |

No residual risk is classified as:

```text
BLOCKER_3_BINDING
```

## 15. BLOCKER-SEPARATION ANALYSIS

BLOCKER-3 closure within authorized synthetic scope does not establish:

```text
production readiness
platform readiness
real publication
real recovery
scientific closure
BLOCKER-1 closure
BLOCKER-2 closure
BLOCKER-4 closure
```

BLOCKER-1 remains open:

```text
BLOCKER-1 = Windows directory durability is not established.
```

BLOCKER-2 remains open:

```text
BLOCKER-2 = real same-volume no-replace directory promotion is not established.
```

BLOCKER-4 remains open:

```text
BLOCKER-4 = separate future real-operation authorizations are absent.
```

Do not import BLOCKER-1, BLOCKER-2, or BLOCKER-4 obligations into BLOCKER-3
merely because they remain open. BLOCKER-3 was selected because resource
admissibility could be bounded and tested independently before platform
durability and real-operation claims.

## 16. FORMAL-HOLD AND MODE-0 BOUNDARIES

Preserved exactly:

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

Publication remains only a projection of the authoritative scientific result.

The authoritative durable scientific result remains:

```text
verified IMMUTABLE_SCIENTIFIC_BUNDLE
+
valid linked SCIENTIFIC_COMPLETION receipt
```

J2 recovery evidence remains separate and may not reconstruct or claim original
J1 completion.

## 17. BLOCKER-3 ASSESSMENT

Candidate state assessment:

```text
State A =
BLOCKER_3_CLOSED_WITHIN_AUTHORIZED_SYNTHETIC_SCOPE
```

State A is selected because:

```text
all BLOCKER-3 binding criteria are satisfied
no binding implementation or evidence defect remains
residual risks belong to other blockers, future hardening, or out-of-scope domains
```

Recommended assessment state:

```text
blocker_3_assessment =
READY_FOR_FORMAL_CLOSURE

blocker_3_scope =
AUTHORIZED_SYNTHETIC_OFFLINE_STAGE_S3B_V0_3_ONLY

binding_defects =
NONE_PRESENTLY_IDENTIFIED
```

This assessment recommends formal closure. It does not itself enact closure
unless the project's documentation protocol treats the committed closure
assessment as the closure act.

## 18. RECOMMENDED NEXT SEQUENCING

Open blocker state after this assessment:

```text
BLOCKER-1 = open
BLOCKER-2 = open
BLOCKER-4 = open
```

Recommended next lane:

```text
NEXT_STEP =
SEPARATE_DOCS_ONLY_BLOCKER_1_WINDOWS_DIRECTORY_DURABILITY_ASSESSMENT_OR_SPECIFICATION
```

BLOCKER-1 is the next logical open technical blocker because the blocker
decomposition identifies Windows directory durability as foundational below
durable record acceptance, while BLOCKER-2 promotion semantics depend on a
related platform-durability question. BLOCKER-4 remains open but concerns later
real-operation authorization and should not be used to authorize work in this
document.

This assessment does not authorize BLOCKER-1, BLOCKER-2, or BLOCKER-4 work.

## 19. CONCLUSION

BLOCKER-3 resource admissibility is ready for formal closure within the
authorized synthetic/offline Stage S3B v0.3 durable publication and recovery
scope.

No BLOCKER-3 binding implementation defect is presently identified.

The remaining risks are assigned to other blockers, non-binding future
hardening, or out-of-scope domains. This assessment does not establish
production readiness, platform readiness, real publication, real recovery,
scientific closure, BLOCKER-1 closure, BLOCKER-2 closure, or BLOCKER-4 closure.

Assessment verdict:

```text
A. BLOCKER_3_READY_FOR_FORMAL_CLOSURE
```

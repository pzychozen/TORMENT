# TORMENT Brainvision Stage S3B v0.3 BLOCKER-3 Resource-Admissibility Implementation Findings v0.1

## 1. Document Status

```text
document_class                    = implementation findings (docs-only)
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

This findings record is descriptive only. It records the completed, committed,
synchronized, and independently accepted BLOCKER-3 resource-admissibility
implementation review state. It does not create new authority, modify the
implementation, modify tests, or close BLOCKER-3.

## 2. Governing Lineage

Exact lineage:

```text
35d7b6e docs(research): specify blocker 3 resource admissibility
01a720c docs(research): authorize blocker 3 resource admissibility implementation
164680b docs(research): correct blocker 3 implementation surface
c03d5f9 research(brainvision): implement blocker 3 resource admissibility
```

Full implementation commit:

```text
c03d5f90342f0d17705a9b73c88252e05afcfb8f
```

## 3. Implementation Surface

The implementation candidate modified exactly eight authorized files:

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

Implemented capabilities, without closure overstatement:

```text
binding resource ceilings
deterministic structural preflight
bounded canonical serialization
artifact resource-map validation
computed resource-policy identity
explicit publication and recovery policy identities
fail-closed staging-capacity handling
pytest-local positive capacity adapter
complete in-memory admission before staging
exact J1/J2 failure mappings
bounded recovery reads
lstat/open/fstat type admission
non-regular-file rejection
cumulative recovery verification budget
final-artifact and original J1-chain non-mutation
```

Computed policy identity:

```text
policy_schema_identity =
durable-evidence-resource-admissibility-policy-v0.3

policy_sha256 =
d845ac1475051c21da1a65fefb3551fdc29af87f53ec4fc21ec12625b64f5ae8
```

The policy digest is computed from the policy identity material. It is not
hardcoded as an implicit policy identity.

## 4. Binding Limits

Binding resource limits:

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

Exact aggregate arithmetic:

```text
16384 + 8388608 + 1024 = 8406016
```

The equal source-bundle and stored-bundle ceilings remain independently
enforced. Passing one ceiling does not override the other.

## 5. Sequencing Findings

Publication sequence:

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

No staging directory or artifact file is created before complete resource and
capacity admission.

Recovery sequence:

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

No unbounded final-artifact `Path.read_bytes()` route remains in the reviewed
recovery path.

## 6. Test and Review Evidence

Windows evidence before the POSIX fixture correction:

```text
full Stage S3B v0.3 suite:
233 passed, 1 skipped - twice

pre-existing durable-evidence tests:
172 passed

boundary tests:
17 passed
```

Initial independent Linux/POSIX finding:

```text
233 passed, 1 failed
```

The sole failure was a test-fixture defect: the symlink target was placed
inside the final publication directory, adding a fourth inventory entry and
correctly triggering inventory rejection before type admission.

Exact correction:

```python
replacement = tmp_path / "external_symlink_target.txt"
```

Corrected Windows evidence:

```text
focused recovery resource file:
19 passed, 1 skipped - twice

three focused resource files:
61 passed, 1 skipped - twice

full Stage S3B v0.3 suite:
233 passed, 1 skipped - twice
```

Corrected Linux/POSIX evidence:

```text
focused recovery resource file:
20 passed

three focused resource files:
62 passed

full Stage S3B v0.3 suite:
234 passed
```

Independent Linux reviewer environment:

```text
Python 3.11.15
pytest 9.1.1
Linux cloud container
```

Stale cloud-mounted file reconstruction and reconciliation:

```text
stale copy size:
13951 bytes

corrected authoritative Windows size:
13931 bytes

authoritative corrected Windows SHA-256:
a352598c20b2f3e18fe34a4fdddda9f4a11d7faad4f944b2edba48b350e610b7
```

GPT reconciled the corrected line, file size, exact eight-file surface, Windows
evidence, and reconstructed Linux evidence and accepted the corrected
independent review. This record does not claim that Claude independently
reported the authoritative corrected Windows SHA-256.

Accepted GPT review verdict:

```text
A. ACCEPT_CLAUDE_CORRECTED_IMPLEMENTATION_REVIEW
```

## 7. Semantic Findings

The corrected POSIX symlink case established:

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

Rejection preserved:

```text
final artifacts
final inventory
original J1 chain
absence of J2 verified/completed records after rejection
```

## 8. Required Boundary Language

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

The implementation does not establish:

```text
production readiness
platform readiness
real publication
real recovery
scientific closure
BLOCKER-3 closure
BLOCKER-1 closure
BLOCKER-2 closure
BLOCKER-4 closure
```

Publication remains only a projection of the authoritative scientific result.

The authoritative durable scientific result remains:

```text
verified IMMUTABLE_SCIENTIFIC_BUNDLE
+
valid linked SCIENTIFIC_COMPLETION receipt
```

J2 recovery evidence remains separate and does not reconstruct or claim
original J1 completion.

## 9. Conclusion

BLOCKER-3 resource-admissibility implementation is implemented, committed,
synchronized, and independently accepted at the implementation-review level.

No binding implementation defect is presently identified.

This findings record does not by itself close BLOCKER-3. Closure or further
platform-blocker sequencing requires a separate explicit assessment and
authorization.

Recommended state:

```text
implementation_status =
IMPLEMENTED_COMMITTED_SYNCHRONIZED_AND_INDEPENDENTLY_ACCEPTED

binding_defects =
NONE_PRESENTLY_IDENTIFIED

blocker_3_status =
IMPLEMENTATION_COMPLETE_CLOSURE_PENDING_SEPARATE_ASSESSMENT
```

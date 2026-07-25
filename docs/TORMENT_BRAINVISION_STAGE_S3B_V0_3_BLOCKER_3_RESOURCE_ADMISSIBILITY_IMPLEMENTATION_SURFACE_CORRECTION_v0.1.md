# TORMENT Brainvision — Stage S3B v0.3 BLOCKER-3 Resource-Admissibility Implementation-Surface Correction v0.1

## 1. Document Status

```text
document_class                         = separate docs-only implementation-surface correction
selected_blocker                       = BLOCKER-3
correction_reason                      = accepted six-file authorization is source-incompatible with preserved existing tests
implementation_status                  = HELD pending correction effectiveness
implementation_authorized_by_this_draft = false
source_modified                        = false
tests_modified                         = false
prior_docs_modified                    = false
real_publication_authorized            = false
real_recovery_authorized               = false
platform_probe_authorized              = false
manifest_contact_authorized            = false
descriptor_execution_authorized        = false
scientific_execution_authorized        = false
production_modification                = false
kernel_modification                    = false
service_runtime_modification           = false
```

This document corrects only the authorized implementation file surface for the
already accepted BLOCKER-3 resource-admissibility specification and
implementation authorization.

It does not implement BLOCKER-3. It does not change any resource ceiling,
resource-policy identity rule, sequencing rule, failure mapping, scientific
invariant, operational boundary, or non-claim.

Until this correction becomes effective under Section 15:

```text
BLOCKER-3 implementation must not begin
source files must not be modified
test files must not be modified or created
resource tests must not be executed
```

## 2. Governing Baseline and Inputs

Authoritative repository:

```text
C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric
```

Branch:

```text
main
```

Correction input baseline:

```text
HEAD        = 01a720c55f45638ee6046317ca2c6c88866536cc
origin/main = 01a720c55f45638ee6046317ca2c6c88866536cc
subject     = docs(research): authorize blocker 3 resource admissibility implementation
```

Governing specification:

```text
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_3_RESOURCE_ADMISSIBILITY_IMPLEMENTATION_SPECIFICATION_v0.1.md
```

Governing specification Git blob:

```text
3fc24c03fd85b530e585e52b0e94d8f92c4002f9
```

Accepted implementation authorization:

```text
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_3_RESOURCE_ADMISSIBILITY_IMPLEMENTATION_AUTHORIZATION_v0.1.md
```

Accepted implementation authorization Git blob:

```text
7a72a726d99cde5021fa8fb554597b9af814de26
```

The original authorization was independently accepted and became effective at
`01a720c55f45638ee6046317ca2c6c88866536cc`. Its implementation authority is
now HELD because subsequent read-only source inspection established that its
exact six-file surface cannot preserve all existing tests without a prohibited
implicit resource-admission bypass.

## 3. Read-Only Adversarial Finding

A separate Codex read-only admissibility review returned:

```text
B. SIX_FILE_SURFACE_HAS_COMPATIBILITY_GAP
```

The review verified:

```text
main was clean and synchronized at 01a720c55f45638ee6046317ca2c6c88866536cc
specification blob matched 3fc24c03fd85b530e585e52b0e94d8f92c4002f9
authorization blob matched 7a72a726d99cde5021fa8fb554597b9af814de26
no file or Git mutation occurred
```

The incompatibility is specific:

1. Existing publication tests construct `publication_utility_identities`
   without `resource_admissibility_policy_identity`.
2. Existing publication tests call `project_publication(...)` without the new
   explicit synthetic staging-capacity adapter.
3. Existing recovery tests construct
   `publication_recovery_utility_identity` without
   `resource_admissibility_policy_identity`.
4. The existing publication and recovery replay/boundary suites import or reuse
   those two compatibility helpers transitively.
5. No compliant source-only mechanism can supply the missing test inputs while
   preserving all of the following:

```text
default capacity behaviour fails closed
only explicit pytest-local positive adapters confirm capacity
policy identity mismatch remains detectable
utility identity evidence remains explicit
validation layers remain separate
existing expected classifications remain unchanged
no hidden pytest or environment detection exists
```

Therefore the original six-file surface is insufficient. This is an
authorization-surface defect, not an implementation defect and not a defect in
the accepted resource policy.

## 4. Exact Correction Effect

This document supersedes only these parts of the accepted authorization:

```text
authorized_test_files  = exactly 3
authorized_total_files = exactly 6
No seventh file is authorized.
```

They are replaced by:

```text
authorized_source_files          = exactly 3
authorized_modified_test_files   = exactly 2
authorized_new_test_files        = exactly 3
authorized_test_files_total      = exactly 5
authorized_total_files           = exactly 8
No ninth file is authorized.
```

The original authorization remains binding in every other respect.

This correction does not alter:

```text
binding resource ceilings
independent-limit semantics
four-layer validation separation
structural accounting
deterministic failure precedence
serialized-artifact precedence
resource-policy declaration or identity shape
J1 or J2 grammar
J1 or J2 failure mappings
publication sequencing
no-staging-before-admission invariant
bounded recovery-read requirements
result-field semantics
exception-handling limits
replay scope
permanent Brainvision boundaries
existing-test preservation requirements
required Windows and Linux validation runs
BLOCKER-1, BLOCKER-2, or BLOCKER-4 state
```

## 5. Corrected Exact Eight-File Surface

Implementation authority, after this correction becomes effective, is limited
to exactly these eight files.

### 5.1 Modified source files — exactly three

```text
research/brainvision/durable_evidence_schema_v0_3.py
research/brainvision/durable_evidence_publication_v0_3.py
research/brainvision/durable_evidence_publication_recovery_v0_3.py
```

Baseline Git blobs at the correction input commit:

```text
durable_evidence_schema_v0_3.py
  7d201645da6896fcdd61926b0ae7e21e230ddc7d

durable_evidence_publication_v0_3.py
  4c348487ca819e0d15e341262c3c272bdc4e6d76

durable_evidence_publication_recovery_v0_3.py
  5a9514c32d7263db3f5cbd71f1d193fcb5465842
```

### 5.2 Modified existing compatibility-test files — exactly two

```text
research/brainvision/test_durable_evidence_publication_v0_3.py
research/brainvision/test_durable_evidence_publication_recovery_v0_3.py
```

Baseline Git blobs at the correction input commit:

```text
test_durable_evidence_publication_v0_3.py
  00a38fef3af9ff45088058709dd1a638a24f29f4

test_durable_evidence_publication_recovery_v0_3.py
  3f2986c2be1dfa8dfa32813870c43ede73cfa7a0
```

### 5.3 New focused test files — exactly three

```text
research/brainvision/test_durable_evidence_resource_admissibility_v0_3.py
research/brainvision/test_durable_evidence_publication_resource_bounds_v0_3.py
research/brainvision/test_durable_evidence_publication_recovery_resource_bounds_v0_3.py
```

No ninth file is authorized.

No replay file, boundary-test file, Windows adapter, helper module, fixture
module, documentation amendment, production file, kernel file, service file,
manifest reader, descriptor file, scientific runner, or real-results file may
be modified or created during implementation.

If the implementation cannot honestly remain inside these exact eight files, it
must stop for renewed specification and authorization review.

## 6. Purpose of the Two Added Compatibility-Test Files

The two newly authorized existing test files may be modified only to provide the
explicit test inputs required by the accepted resource policy while preserving
the tests' existing semantic expectations.

They are not authorized for broad cleanup, refactoring, fixture relocation,
assertion weakening, or expected-classification changes.

### 6.1 Publication compatibility-test authority

Within:

```text
research/brainvision/test_durable_evidence_publication_v0_3.py
```

implementation may only make compatibility changes substantially equivalent to:

```text
1. define a pytest-local synthetic positive staging-capacity adapter;
2. make that adapter return the exact required result fields:
   status, required_bytes, available_bytes, detail;
3. make the adapter explicitly return STAGING_CAPACITY_CONFIRMED only for
   test-local calls;
4. require returned required_bytes to equal the caller-computed exact logical
   artifact-set bytes;
5. provide available_bytes >= required_bytes;
6. include the exact resource_admissibility_policy_identity under the existing
   publication_utility_identities mapping;
7. pass the explicit positive capacity adapter through the existing publication
   helper and all direct project_publication(...) calls in this file that are
   intended to proceed beyond capacity admission;
8. preserve every existing expected classification and assertion;
9. preserve the existing synthetic durability and promotion adapter semantics;
10. avoid changing replay or boundary tests that import these helpers.
```

The positive capacity adapter must be visibly test-private. Production source
must not import it, discover it, construct it, or select it automatically.

Tests intentionally exercising unavailable, indeterminate, malformed, or
inconsistent capacity results must use focused test-local adapters in the new
resource-bound test file rather than weakening the positive compatibility
adapter.

### 6.2 Recovery compatibility-test authority

Within:

```text
research/brainvision/test_durable_evidence_publication_recovery_v0_3.py
```

implementation may only make compatibility changes substantially equivalent to:

```text
1. include the exact resource_admissibility_policy_identity under the existing
   publication_recovery_utility_identity mapping;
2. preserve all existing recovery expected classifications and assertions;
3. preserve J2 evidence-only behaviour and final-artifact non-mutation checks;
4. preserve all replay and boundary tests that import or reuse these helpers;
5. update direct identity constructions in this file consistently;
6. avoid any implicit source-side insertion of the policy identity.
```

Recovery has no staging-capacity adapter. This correction does not create one.

## 7. Existing-Test Expectations Must Not Be Rewritten

The two existing test files are authorized to supply newly required explicit
inputs. They are not authorized to change the meaning of the existing tests.

Forbidden existing-test changes include:

```text
changing PUBLICATION_COMPLETED to an earlier resource failure
changing PUBLICATION_PROMOTION_FAILED to a capacity failure
changing staging-collision, final-collision, staging-incomplete, or
final-invalid expectations to resource failures
changing successful recovery to policy-identity failure
removing replay assertions
removing non-mutation assertions
weakening exact record-kind assertions
marking tests skipped or expected-failure
reducing test coverage
catching unexpected exceptions merely to preserve green status
```

The compatibility edits must allow existing tests to reach the same intended
post-admission branch they reached before BLOCKER-3 implementation.

The new focused tests must independently prove that omitted, malformed, or
mismatched policy identities and omitted/default capacity confirmation fail
closed under the new contract.

## 8. Explicit Resource-Policy Identity Rule

The exact policy identity remains:

```json
{
  "policy_schema_identity": "durable-evidence-resource-admissibility-policy-v0.3",
  "policy_sha256": "<SHA-256 of canonical resource-policy declaration>"
}
```

Exact key order remains:

```text
policy_schema_identity
policy_sha256
```

The compatibility-test helpers must obtain the identity from the authoritative
schema-layer policy declaration/identity helper implemented under the accepted
specification. They must not hardcode a predicted policy SHA-256.

Required carried locations remain:

```text
publication_utility_identities[
  "resource_admissibility_policy_identity"
]

publication_recovery_utility_identity[
  "resource_admissibility_policy_identity"
]
```

Production source must not silently insert the identity when callers omit it.
Omission, malformed shape, wrong key order, wrong schema identity, or wrong hash
must fail with:

```text
RESOURCE_ADMISSIBILITY_POLICY_IDENTITY_MISMATCH
```

under the applicable fixed J1 or J2 mapping.

## 9. Explicit Synthetic Staging-Capacity Rule

The publication source may add an injectable staging-capacity adapter parameter
with a fail-closed default, as already authorized by the accepted specification.

Default behaviour must never confirm capacity.

Only an explicitly supplied pytest-local positive adapter may return:

```text
STAGING_CAPACITY_CONFIRMED
```

The adapter response must contain exactly the required fields:

```text
status
required_bytes
available_bytes
detail
```

The exact validation contract remains binding:

```text
status is known
required_bytes is a strict non-negative int
bool is rejected
returned required_bytes equals caller-computed required bytes
available_bytes is a strict non-negative int for CONFIRMED/UNAVAILABLE
available_bytes is null only for INDETERMINATE
CONFIRMED requires available_bytes >= required_bytes
UNAVAILABLE requires available_bytes < required_bytes
unknown or inconsistent response is RESOURCE_ADMISSIBILITY_INDETERMINATE
```

The test-positive adapter must not claim real disk capacity, filesystem
allocation, durability, or promotion safety.

## 10. Transitive Replay and Boundary-Test Preservation

The read-only review established that existing publication/recovery replay and
boundary tests import or reuse the two compatibility helpers.

Therefore these files remain outside the authorized mutation surface:

```text
research/brainvision/test_durable_evidence_publication_replay_v0_3.py
research/brainvision/test_durable_evidence_publication_boundary_v0_3.py
research/brainvision/test_durable_evidence_publication_recovery_replay_v0_3.py
research/brainvision/test_durable_evidence_publication_recovery_boundary_v0_3.py
```

The two compatibility-helper changes must be sufficient transitively.

If any replay or boundary test requires direct modification, implementation must
stop. A ninth file is not authorized.

Replay modules remain outside implementation scope. Existing replay still does
not independently execute or revalidate the complete resource policy. The
accepted bounded claim remains only:

```text
resource-aware writers append no publication/recovery completion after rejection
existing replay truthfully observes the resulting incomplete chain
```

## 11. Preserved Failure and Sequencing Semantics

This correction creates no permission to alter any processing order or failure
mapping.

Publication must still perform:

```text
durable PUBLICATION_PROJECTION_AUTHORITY_ACCEPTED
durable PUBLICATION_ATTEMPTED
resource preflight
complete in-memory artifact generation
per-artifact and aggregate validation
explicit synthetic staging-capacity validation
staging-directory creation
artifact writes
staging verification
durability adapter
promotion adapter
final verification
durable PUBLICATION_COMPLETED
```

The complete in-memory artifact set and capacity result must be accepted before
staging-directory creation.

Recovery must still perform exact inventory admission, file-type admission,
bounded reads, per-artifact and cumulative budgets, canonical-byte validation,
semantic validation, regenerated-byte comparison, and expected-hash comparison
in the accepted order.

No test compatibility mechanism may change the first-failure-wins rule.

## 12. Forbidden Workarounds

The corrected eight-file authority expressly forbids:

```text
pytest environment-variable detection
PYTEST_CURRENT_TEST detection
call-stack inspection
test-module-name detection
tmp-path-name detection
class-name detection
automatic capacity confirmation
real disk-space probing
durability status reused as capacity status
promotion status reused as capacity status
synthetic context reused as capacity confirmation
source-side automatic policy-identity insertion
legacy caller bypass
resource-policy skip for old callers
publication success with null or missing policy identity
publication success without explicit confirmed capacity
recovery success with null or missing policy identity
production import of test code
monkeypatching test behaviour from production source
replay modification
Windows-adapter modification
production, kernel, service, manifest, descriptor, or real-data contact
assertion weakening
expected-classification rewriting
```

Any such need requires stopping, not improvising.

## 13. Test and Validation Requirements

All requirements from the accepted specification and authorization remain
binding.

The implementation must preserve at least:

```text
172 existing durable-evidence tests
17 existing boundary tests
```

The three focused resource test files are additive. Their final count must not
be predicted in advance.

Required implementation validation remains:

```text
two complete authoritative Windows runs
one independent Linux review run where available
```

The implementation review must additionally verify:

```text
exactly eight changed paths
exactly the three authorized source files modified
exactly the two authorized compatibility-test files modified
exactly the three authorized focused test files added
no ninth file
no changed expected classification in existing tests
no removed or weakened existing assertion
no replay or boundary file modification
no test-to-production import
no hidden test-environment detection
explicit test-local positive capacity injection
explicit policy identity in both compatibility helpers
default production capacity path remains fail closed
```

Tests must remain synthetic, pytest-local, bounded, and safe for host memory.

## 14. Stop Conditions

Implementation must stop if:

```text
any ninth file is needed
any replay or boundary test requires modification
any existing expected classification must change
any existing assertion must be removed or weakened
policy identity cannot remain explicit at caller input
capacity confirmation cannot remain explicit and test-local
production source would need to detect pytest or test context
real filesystem capacity probing becomes necessary
Windows adapter modification becomes necessary
replay implementation modification becomes necessary
a helper or fixture module outside the eight files becomes necessary
resource tests risk attacker-proportional allocation
real manifest, result-tree, descriptor, scientific, publication, or recovery contact becomes necessary
production, kernel, service, memory, cognition, or autonomy contact becomes necessary
canonical bytes or existing scientific identity semantics would change
```

## 15. Correction Effectiveness

This correction is not effective merely because a draft exists.

It becomes effective only when all of the following are true:

```text
1. this exact correction receives an independent docs-only review;
2. the final independent verdict is A. ACCEPT;
3. the accepted correction is committed as a docs-only successor of
   01a720c55f45638ee6046317ca2c6c88866536cc;
4. the correction commit contains only this correction document;
5. the correction commit is pushed to origin/main;
6. the authoritative Windows working tree is clean and synchronized at that
   pushed correction commit.
```

After effectiveness, the accepted specification, accepted implementation
authorization, and this correction jointly authorize only the exact eight-file
implementation described above.

No implementation may begin before effectiveness.

## 16. Permanent Boundaries and Blocker State

Preserve exactly:

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

The durable-evidence architecture must not be integrated into AI cognition,
autonomy, memory, belief formation, truth-selection behaviour, identity, prompt
handling, action selection, the production TORMENT kernel, or live memory-system
functionality.

Current blocker state remains:

```text
BLOCKER-1 = open
BLOCKER-2 = open
BLOCKER-3 = selected and specified; implementation HELD pending correction
BLOCKER-4 = open
```

This correction does not implement, prove, partially close, or close BLOCKER-3.

## 17. Required Successor

```text
CORRECTION_STATUS = READY_FOR_INDEPENDENT_DOCS_ONLY_REVIEW
SELECTED_BLOCKER = BLOCKER_3
CORRECTED_IMPLEMENTATION_FILE_COUNT = 8
IMPLEMENTATION_MAY_BEGIN = False
BLOCKER_3_IMPLEMENTED = False
BLOCKER_3_CLOSED = False

NEXT_STEP =
INDEPENDENT_DOCS_ONLY_REVIEW_OF_BLOCKER_3_IMPLEMENTATION_SURFACE_CORRECTION
```

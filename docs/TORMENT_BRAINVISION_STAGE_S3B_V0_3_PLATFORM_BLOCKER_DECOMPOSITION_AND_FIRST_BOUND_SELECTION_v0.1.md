# TORMENT Brainvision Stage S3B v0.3 Platform Blocker Decomposition and First Bound Selection v0.1

## 1. Document Status

```text
document_class                 = platform-blocker decomposition and selection (docs-only)
authority_created              = none
implementation_authorized      = false
execution_authorized           = false
real_publication_authorized    = false
real_recovery_authorized       = false
manifest_contact_authorized    = false
platform_probe_authorized      = false
source_modified                = false
tests_modified                 = false
prior_docs_modified            = false
```

This document may select the next bounded research/implementation target, but
it does not itself authorize implementation.

Bound governing record:

```text
commit = ac5dd261843f8433a366a9d668c04fbce6a3dac3
subject = docs(research): record durable evidence implementation findings v0.3
```

Governing sources include the committed architecture review, architecture
decision record, implementation specification, implementation authorization,
and implementation findings documents. This record does not amend or reinterpret
those documents.

## 2. Permanent Boundaries

```text
FORMAL_HOLD = active
Mode_0 = active
STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY
```

The work remains:

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

This phase performs no real publication, recovery, manifest contact, scientific
execution, descriptor execution, or results-tree write.

## 3. BLOCKER-1 Decomposition

```text
BLOCKER-1 = Windows directory durability is not established.
```

The exact directory state that would need to become durable is the namespace
state linking a validated object name to the intended object bytes or linking a
validated directory name to the intended directory tree. For immutable record
objects this means the parent directory entry for the new file. For bundle
objects it means the bundle directory entry. For publication evidence this means
the relevant chain directory entries. For promotion, directory state is also
involved, but promotion has additional no-replace and attribution concerns and
is decomposed separately under BLOCKER-2.

File-data durability and directory-entry durability are distinct. The governing
sources already distinguish write/flush/file read-back from the later
directory-entry durability step. A byte-perfect file read-back can prove that a
process can currently observe the intended bytes; it does not by itself prove
that the directory entry will survive an interruption or crash.

Windows APIs that might be relevant to a later proof obligation include narrowly
scoped file handles, directory handles where supported, file-data flushing,
volume/filesystem query APIs, rename/move APIs, and read-back/stat APIs. This
document does not claim that `fsync`, `FlushFileBuffers`, directory handles,
NTFS, ReFS, or Windows rename behavior provide the required guarantee. A later
specification would have to cite platform documentation or empirical acceptance
criteria for the exact claim it asks an implementation to rely on.

Python-level guarantees are absent for the central property. The standard
library can help with exclusive file creation, bytes writing, file flushing,
file descriptor syncing where supported, read-back, and path handling. The
governing specification treats Windows directory-entry durability as
Win32-specific or uncertain and requires fail-closed behavior when it is not
confirmed.

A capability adapter is required if this blocker is selected later. The adapter
boundary must be explicit, narrow, and injectable. It must return a positive
confirmed state only for the exact property it can establish; unsupported,
ambiguous, or partially observed systems must return an unconfirmed failure
classification and leave the caller fail closed.

Required synthetic fault tests would include at least: create success but
directory durability unconfirmed; file-data read-back success but directory
sync failure; directory handle unavailable; filesystem kind unsupported;
extended-length path accepted and rejected cases; duplicate immutable object
candidates; torn or empty candidate objects; and replay that refuses to treat
unconfirmed objects as authoritative.

What remains impossible to prove from process-local replay alone: survival of a
directory entry across power loss, host crash, storage controller behavior,
filesystem journal behavior, antivirus/filter-driver interference, or volume
loss. Process-local replay can validate bytes and chain structure that are
present; it cannot prove the absent crash history of the platform.

## 4. BLOCKER-2 Decomposition

```text
BLOCKER-2 = real same-volume no-replace directory promotion is not established.
```

The source staging directory requirement is strict: staging must belong to the
expected publication chain, contain exactly the three verified artifact names,
and have byte/hash verification completed before promotion is attempted.

The destination absence requirement is separate from atomicity. The final
destination must not exist before promotion. A collision must fail closed; it
must not merge, overwrite, replace, delete, or select a winner.

The same-volume requirement is distinct. Cross-volume behavior can degrade into
copy/delete semantics or other behavior outside the intended primitive. A later
adapter must verify same-volume eligibility before any promotion attempt.

The no-overwrite/no-replace requirement is also distinct. Even a namespace
transition that appears atomic is not acceptable if it can replace an existing
final directory. The operation must preserve collision evidence and fail closed
on any pre-existing destination.

Crash ambiguity must be classified before, during, and after promotion. Before
promotion, the correct state is a verified staging directory without final
ownership. During promotion, the state can become indeterminate. After an
observed destination appears, the implementation still needs attribution: did
this invocation create that final directory, or was it pre-existing or foreign?

Rename success does not by itself prove post-transition durability. Destination
observation does not by itself prove promotion ownership. These are separate
claims:

```text
atomic namespace transition
no replacement
same-volume enforcement
post-transition durability
post-crash attribution
```

Required recovery classifications include staging incomplete, final directory
collision, promotion failed, promotion outcome indeterminate, promotion
ambiguous, final directory invalid, and artifacts verified while completion
evidence is incomplete. Recovery must not repair the original publication chain.

The adapter boundary must be narrow: `promote_verified_directory_no_replace`
or equivalent, with explicit preconditions, explicit same-volume verification,
explicit no-replace semantics, explicit post-observation verification, and
explicit failure classes. It must be test-injectable and fail closed when the
platform primitive is absent or ambiguous.

Required adversarial subprocess tests would need to exercise separate processes
attempting final-directory collision, stale staging, foreign final directory,
cross-volume rejection, interruption windows, and post-promotion replay. These
tests are necessarily platform-specific and carry a higher false-confidence
risk than pure canonical resource-bound tests.

## 5. BLOCKER-3 Decomposition

```text
BLOCKER-3 = authoritative artifact and result size bounds are not established.
```

This blocker concerns resource admissibility, not scientific truth and not
platform crash consistency. It asks which byte and structural bounds must be
enforced before evidence objects, publication artifacts, or recovery verification
can be accepted as admissible.

Required bound dimensions:

```text
per-artifact maximum bytes
combined artifact-set maximum bytes
canonical JSON structural limits
summary-text maximum bytes
maximum nesting depth
maximum mapping/list cardinality
maximum string length
numeric representation constraints
pre-generation versus post-generation enforcement
streaming versus full-memory validation
staging-space budget
recovery verification budget
denial-of-service and unbounded-allocation risk
failure taxonomy
```

The existing committed implementation already has partial structural controls:
canonical ASCII JSON discipline, duplicate-key rejection, float/null rejection,
strict int-not-bool validation, `MAX_NESTING_DEPTH = 32`,
`MAX_CONTAINER_MEMBER_COUNT = 4096`, `MAX_STORED_RECORD_OBJECT_BYTES = 65536`,
and `MAX_STORED_BUNDLE_OBJECT_BYTES = 4194304`. The findings record preserves
that three fixed artifact names do not close BLOCKER-3, and the authorization
preserves that the real v0.2 pass-bundle size class was not retained and must
not be reconstructed through manifest contact or v0.2 rerun.

This blocker must distinguish four validations:

```text
semantic schema validity      = keys, field meanings, identities, result-kind vocabulary
canonical-byte validity       = deterministic bytes, ASCII, no BOM, no CR, terminal LF, ordering
resource admissibility        = configured byte/count/depth/string/allocation budgets
storage-capacity admissibility = enough pytest-local staging/recovery scratch capacity before writing
```

Pre-generation enforcement should reject known-overlarge inputs before building
large objects. Post-generation enforcement should verify exact canonical byte
lengths and artifact-set budgets before staging or recovery acceptance. Streaming
validation may be required for future larger inputs, but the first bounded target
can choose full-memory validation for pytest-local synthetic fixtures if that
choice is itself bounded and tested. The contract must fail closed when a future
input exceeds the declared resource budget.

Failure taxonomy should separate semantic invalidity from canonical-byte
invalidity, resource limit exceeded, artifact-set budget exceeded,
staging-space budget unavailable, recovery verification budget exceeded, and
unexpected allocation failure. None of these failures may weaken scientific
truth or authorize publication/recovery.

## 6. Comparative Decision Matrix

| Criterion | BLOCKER-1 Windows directory durability | BLOCKER-2 no-replace promotion | BLOCKER-3 size bounds |
|---|---|---|---|
| Security importance | High: required before durable acceptance can be trusted. | High: required before real publication finalization can be trusted. | High: prevents unbounded allocation and resource-amplification failures. |
| Dependency position | Foundational below all durable records. | Downstream of publication staging and artifact verification; depends on some BLOCKER-1-like durability question. | Mostly independent of platform crash guarantees and can run before real publication. |
| Implementation complexity | High because platform primitive and evidence semantics must be separated. | High because same-volume, no-replace, ownership, and durability must not be collapsed. | Moderate because it is primarily schema/resource contract work with synthetic fixtures. |
| Platform specificity | High Windows/filesystem specificity. | High Windows/filesystem and volume specificity. | Low to moderate; mostly platform-neutral, with filesystem free-space checks kept synthetic. |
| Proof difficulty | High; process-local replay cannot prove crash survival. | High; crash attribution and post-transition durability are hard. | Moderate; bounds are independently falsifiable with generated synthetic payloads. |
| Synthetic testability | Partial; many tests simulate negative states but cannot prove real crash durability. | Partial; adversarial subprocess tests can find defects but can overstate atomicity. | Strong; over-limit, at-limit, malformed, and budget-exhaustion cases are pytest-local. |
| Risk of false confidence | High if a successful read-back is mistaken for crash durability. | High if rename success is mistaken for no-replace durable promotion. | Lower if claims are limited to declared resource admissibility. |
| Risk of scope expansion | High; can drift into platform research and OS claims. | High; can drift into real publication machinery. | Lower; can be bounded to validators, constants, and synthetic tests. |
| Independence from real publication | Strong for negative adapter work, weak for final confidence. | Weaker because it is tied to the real publication finalization path. | Strong; no real publication or recovery is needed. |
| Ability to fail closed | Good, but leaves many authoritative operations unconfirmed. | Good, but leaves successful publication finalization unavailable. | Good; reject oversized or unbudgeted objects before staging or acceptance. |
| Value of closing it first | Valuable but may not be honestly closable without platform documentation/probes. | Valuable after size/resource contracts are bounded. | Highest first value: reduces DoS/resource ambiguity before platform-specific work. |

## 7. Selected Blocker

```text
selected blocker = BLOCKER-3
```

BLOCKER-3 is selected because it offers the most precise and independently
falsifiable first proof obligation. It can be specified and later implemented
using pytest-local synthetic paths only, without real publication, real recovery,
manifest contact, descriptor execution, production kernel/service contact, or
platform crash claims. It has a small reviewable surface and does not depend on
BLOCKER-1 or BLOCKER-2 being solved.

BLOCKER-1 and BLOCKER-2 remain important, but selecting either first would risk
scope expansion into platform proof claims that the governing documents have
explicitly kept open. BLOCKER-3 can reduce resource ambiguity before those
platform-specific blockers are attempted.

## 8. Selected Target Contract

### 8.1 Exact Problem Statement

The durable-evidence system has fixed canonical byte disciplines and some
existing object limits, but it does not yet have a separately reviewed,
authoritative resource admissibility contract for publication artifacts,
artifact sets, summaries, bundle/result payloads, staging space, and recovery
verification budgets.

### 8.2 Exact Property to Be Established

A future separately authorized implementation should establish that every
synthetic durable-evidence artifact or result object accepted by the bounded
validators is:

```text
semantically valid
canonically byte-valid
within declared per-object and aggregate resource bounds
within declared staging and recovery verification budgets
rejected fail-closed before publication/recovery evidence is strengthened if any bound fails
```

### 8.3 Properties Explicitly Not Established

The selected target will not establish:

```text
Windows directory durability
same-volume no-replace promotion
post-crash publication attribution
real publication safety
real recovery safety
scientific validity
v0.2 result size reconstruction
manifest-derived size confirmation
production readiness
memory integration readiness
```

### 8.4 Future Source Surface for Separate Authorization

This document does not authorize implementation. A later selected-blocker
implementation specification may propose a bounded future source surface limited
to:

```text
research/brainvision/durable_evidence_schema_v0_3.py
research/brainvision/durable_evidence_publication_v0_3.py
research/brainvision/durable_evidence_publication_recovery_v0_3.py
new or existing synthetic tests under research/brainvision/test_durable_evidence_*_v0_3.py
```

The later specification should prefer shared schema/resource-bound helpers over
duplicated limits. Any actual implementation authority must be granted by a
separate document.

### 8.5 Prohibited Source Surface

A future BLOCKER-3 implementation must not touch:

```text
torment_service/
production kernel or service code
memory-system code
manifest reader or descriptor execution surfaces
real results tree
publication promotion adapter implementation, except for reading declared budget types if separately justified
platform durability adapter implementation, except for test-independent import stability if separately justified
```

### 8.6 Test-Only Boundaries

Tests must use pytest-local synthetic paths only. They must not contact the real
manifest, execute descriptors, perform real publication, perform real recovery,
write the real results tree, or rely on platform crash behavior. Overlarge inputs
must be generated synthetically and kept within safe test memory budgets.

### 8.7 Required Success Cases

```text
accepted minimum artifact set
accepted exact current three publication artifacts
accepted at-limit canonical JSON object
accepted at-limit summary text
accepted at-limit stored-record object
accepted at-limit stored-bundle object using synthetic payloads
accepted recovery verification within budget
accepted staging-space budget when synthetic free-space adapter reports sufficient space
```

### 8.8 Required Failure Cases

```text
per-artifact byte limit exceeded
combined artifact-set byte limit exceeded
summary-text byte limit exceeded
maximum nesting depth exceeded
mapping/list cardinality exceeded
string length exceeded
float/null/noncanonical numeric representation rejected
canonical-byte limit exceeded after generation
pre-generation estimate exceeds budget
staging-space budget unavailable
recovery verification budget exceeded
unexpected allocation failure mapped to fail-closed classification
```

### 8.9 Required Fault Injections

```text
synthetic object expands beyond estimate during canonicalization
artifact generator returns bytes over declared budget
artifact generator returns noncanonical JSON under byte limit
summary generator returns CR/BOM/no-terminal-LF under byte limit
recovery final directory contains oversized artifact
staging budget adapter reports insufficient capacity
read-back verifier receives bytes larger than accepted budget
validator interruption after one artifact but before set-level budget acceptance
```

### 8.10 Required Classifications

The later specification should define explicit classifications for:

```text
RESOURCE_LIMIT_EXCEEDED
ARTIFACT_SIZE_LIMIT_EXCEEDED
ARTIFACT_SET_SIZE_LIMIT_EXCEEDED
SUMMARY_SIZE_LIMIT_EXCEEDED
CANONICAL_STRUCTURE_LIMIT_EXCEEDED
STAGING_SPACE_BUDGET_UNAVAILABLE
RECOVERY_VERIFICATION_BUDGET_EXCEEDED
RESOURCE_ADMISSIBILITY_INDETERMINATE
```

Names may be refined in the later specification, but each distinct condition
must remain distinguishable from semantic schema invalidity and from platform
durability or promotion failures.

### 8.11 Required Replay Evidence

Replay evidence must show that over-limit objects are not accepted as durable
authoritative facts and do not conceal a valid contradictory tail. For recovery,
oversized or over-budget final artifacts must not produce
`PUBLICATION_RECOVERY_EVIDENCE_COMPLETED`. For publication, over-budget staging
must not produce `PUBLICATION_COMPLETED`.

### 8.12 Platform Assumptions

The selected target assumes only ordinary pytest-local file I/O sufficient to
construct and reject synthetic fixtures. It assumes no Windows directory
durability, no same-volume no-replace promotion, and no real free-space
guarantee beyond a synthetic test adapter's declared response.

### 8.13 Stop Conditions

Stop and fail closed if:

```text
the required bound cannot be named precisely
the test requires real manifest contact
the test requires v0.2 result reconstruction
the proof depends on Windows crash consistency
the proof depends on real publication or recovery
the implementation surface expands into production/kernel/service code
resource testing itself risks unbounded allocation
```

### 8.14 Acceptance Criteria

The selected blocker can be considered closed only by a future separately
authorized implementation and review that demonstrates:

```text
all declared byte/count/depth/string/numeric/staging/recovery budgets are enforced
at-limit cases pass
over-limit cases fail closed with the right classifications
publication and recovery evidence do not strengthen on resource failure
no real manifest, descriptor, publication, recovery, results-tree, service, kernel, or memory contact occurs
BLOCKER-1, BLOCKER-2, and BLOCKER-4 remain explicitly open
```

## 9. BLOCKER-4 Preservation

```text
BLOCKER-4 = separate future real-operation authorizations are absent
```

BLOCKER-4 is not a candidate for implementation in this phase. It remains open
regardless of which technical blocker is selected. Selecting BLOCKER-3 for a
future specification does not authorize real publication, real recovery,
durability reconfirmation, manifest contact, scientific execution, or any
real-operation lane.

## 10. Explicit Non-Claims

This document does not claim:

```text
production readiness
real publication safety
real recovery safety
Windows crash consistency
directory durability
atomic promotion
bounded resource safety
scientific validity
Brainvision readiness
memory integration readiness
```

Any future implementation may establish only the exact bounded property that a
separate specification and authorization define.

## 11. Recommendation

```text
SELECT_BLOCKER_3_FOR_NEXT_SPECIFICATION

NEXT_STEP =
SEPARATE_DOCS_ONLY_SELECTED_BLOCKER_IMPLEMENTATION_SPECIFICATION
```

# TORMENT Brainvision Independent Order-Sensitive Synthetic-Validation v0.2 Implementation Authorization v0.1

## 1. Document status and activation rule

```text
document_type = docs-only implementation authorization
authorization_stage = S3B v0.2 (implementation + bounded non-authoritative testing)
document_status = READY_FOR_ADVERSARIAL_REVIEW
posture = docs-only, non-executing, non-manifest-contacting, offline, quarantined,
          non-production, non-service, non-kernel, non-memory-integrated
```

Authorization activation semantics. The mere existence of this uncommitted document does NOT make implementation active. This authorization has no effect until an explicit activation condition is met:

```text
authorization_effective_condition =
    explicit Hilmir acceptance of the exact reviewed document
    AND
    commit of those exact accepted bytes to synchronized main
```

Only once that condition is satisfied does this document authorize the following, and nothing more:

```text
implementation of the exact three-file allowlist (Section 4)
bounded non-authoritative test execution (Section 14)
read-only source review of the named frozen providers and governing documents (Section 5)
```

This document MUST NEVER authorize, at any stage:

```text
authoritative runner execution
real frozen-manifest contact
scientific evaluation against the real frozen family
publication into the real v0.2 result paths
```

Status vocabulary:

```text
IMPLEMENTATION_AUTHORIZED_IF_EFFECTIVE = True
BOUNDED_NONAUTHORITATIVE_TESTS_AUTHORIZED_IF_EFFECTIVE = True

AUTHORITATIVE_RUNNER_EXECUTION_AUTHORIZED = False
REAL_MANIFEST_CONTACT_AUTHORIZED = False
SCIENTIFIC_RESULT_PUBLICATION_AUTHORIZED = False
```

The `_IF_EFFECTIVE` flags describe capability that becomes real only after the activation condition; until then, this is a reviewable draft that grants nothing.

---

## 2. Purpose

This document authorizes, conditionally on the activation rule of Section 1, the implementation and bounded non-authoritative testing of the corrected Stage S3B v0.2 synthetic-validation lane exactly as fixed by the accepted v0.2 correction specification. Its purpose is to permit the creation of three reviewable, identity-freezable implementation files that make no real-manifest contact, so that a later, separate execution authorization can bind their frozen identities and authorize exactly one authoritative run.

This document creates one documentation file only. It implements no Python code, edits no test, runs nothing, contacts no real manifest, performs no Git operation, and modifies no v0.1 artifact. It confers no execution authority, no manifest-contact authority, and no scientific-publication authority. Acceptance of this document advances only to the implementation-and-bounded-test stage.

---

## 3. Governing specification and repository baseline

Governing specification (accepted):

```text
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_VALIDATION_V0_2_CORRECTION_SPECIFICATION_v0.1.md
```

Specification review status:

```text
SPECIFICATION_REVIEW = ACCEPTED
ATOMICITY_FINDING = CLOSED
```

Authoritative repository baseline:

```text
branch = main
working tree = clean
HEAD = origin/main
HEAD = d3f8e08
commit = docs(research): specify synthetic validation v0.2 correction
```

Where this authorization is less detailed than the accepted correction specification, the correction specification governs. This authorization binds implementation to that accepted specification exactly and weakens no requirement in it. The commit that carries this authorization (if accepted) must contain exactly this one new documentation file and nothing else.

---

## 4. Exact implementation allowlist

When effective, this authorization permits creation or modification of exactly these three files, and no others:

```text
research/brainvision/independent_order_sensitive_synthetic_validation_schema_contract_v0_2.py
research/brainvision/run_independent_order_sensitive_synthetic_validation_v0_2.py
research/brainvision/test_independent_order_sensitive_synthetic_fixtures_v0_2.py
```

No fourth implementation file is authorized. The entire bounded test suite MUST remain inside the single authorized v0.2 test file unless a later separate authorization explicitly changes the allowlist. No helper module, no additional script, no additional test file, no fixture data file, and no configuration file may be created under cover of this authorization.

---

## 5. Read-only dependency allowlist

Dependency authority is split into two closed categories. Runtime import authority is distinct from read-only source-inspection authority:

```text
runtime import authority != read-only source inspection authority
```

Read-only source inspection does not authorize import, execution, mutation, manifest contact, or transitive runtime dependency. No arbitrary repository-wide inspection is authorized under any undefined "required dependency" category; only the exact paths enumerated below are permitted.

### 5.A Runtime import allowlist (closed)

At authoritative runner runtime, only these modules may be imported beyond the Python standard library:

```text
research/brainvision/independent_order_sensitive_descriptor_v0_1.py
research/brainvision/independent_order_sensitive_synthetic_validation_schema_contract_v0_2.py
```

The v0.2 test module may import, only for bounded non-authoritative testing:

```text
research/brainvision/independent_order_sensitive_synthetic_validation_schema_contract_v0_2.py
research/brainvision/run_independent_order_sensitive_synthetic_validation_v0_2.py
research/brainvision/independent_order_sensitive_descriptor_v0_1.py
```

No other Brainvision implementation module may enter the runner's runtime or transitive import graph.

### 5.B Read-only source/AST inspection allowlist (closed)

Implementation and bounded tests may inspect, but MUST NOT runtime-import or execute, exactly these frozen source providers:

```text
research/brainvision/independent_order_sensitive_synthetic_fixture_freeze_v0_1.py
research/brainvision/independent_order_sensitive_synthetic_fixture_verifier_v0_1.py
research/brainvision/run_independent_order_sensitive_synthetic_fixture_freeze_v0_1.py
research/brainvision/test_independent_order_sensitive_descriptor_v0_1.py
```

The first three of these are the authoritative schema providers named by the accepted specification: the freeze library (top-level, accepted-fixture, source-identity, and diagnostics key contracts), the verifier (the fixed-fixture record with `binary_H0`/`binary_H1` members), and the freeze runner (the configuration-identity payload). Read-only inspection MUST be performed by parsing source text or AST directly from these exact paths, never by importing or executing them.

Read-only inspection of exactly these governing documents is also permitted, and no others:

```text
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_VALIDATION_V0_2_CORRECTION_SPECIFICATION_v0.1.md
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_VALIDATION_EXECUTION_AUTHORIZATION_v0.1.md
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_VALIDATION_EXECUTION_FAILURE_FINDINGS_v0.1.md
```

Any additional governing document is permitted only if its exact repository path is genuinely required and explicitly enumerated here; no open-ended "governing documents" class is authorized. No read-only dependency may be modified.

This authorization does NOT authorize importing, executing, or using:

```text
torment_service/kernel/
historical F3
PsiTRS
prerecorded challenger bridges
live service code
memory-system behavior
prompt or action surfaces
```

### 5.C Repository-state and identity verification (bounded, read-only)

Only narrowly bounded, read-only Git and filesystem-metadata operations are permitted, solely to verify:

```text
repository root
branch
clean working tree
HEAD = origin/main
committed identities of authorized files
raw identities of authorized files
the exact three-file implementation change set
absence of unauthorized created or modified files
```

These operations:

```text
are not general repository source-inspection authority
must use fixed commands and fixed authorized paths
must not inspect arbitrary source contents
must not use caller-supplied paths or commands
must not mutate Git state
must not use shell=True
```

The implementation and bounded tests may inspect filesystem metadata for the exact authorized paths and temporary test paths only. Runtime import authority does not grant mutation authority.

---

## 6. Frozen evidence preservation

The following artifacts are frozen consumed-run evidence and SHALL NOT be edited, cleaned, reused, executed, reconstructed, renamed, or deleted by the v0.2 lane or its tests:

```text
research/brainvision/run_independent_order_sensitive_synthetic_validation_v0_1.py
research/brainvision/test_independent_order_sensitive_synthetic_fixtures_v0_1.py
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_VALIDATION_EXECUTION_AUTHORIZATION_v0.1.md
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_VALIDATION_EXECUTION_FAILURE_FINDINGS_v0.1.md
research/brainvision/results/.independent_order_sensitive_synthetic_validation_v0_1.staging
```

The following MUST remain unchanged:

```text
the frozen Stage S1 manifest
the Stage S1 freezer and frozen provider sources
the independent Stage S2 descriptor and descriptor test
the accepted v0.2 correction specification
```

The fixture freezer MUST NOT be rerun. The v0.1 retained empty staging directory MUST NOT be inspected for reuse, promoted into, cleaned, or depended on.

---

## 7. Schema-contract implementation obligations

When effective, the schema-contract module `research/brainvision/independent_order_sensitive_synthetic_validation_schema_contract_v0_2.py` is authorized only if it implements the accepted provider-bound schema contract. It MUST:

```text
remain outside the runner
be independently owned (imported by both the runner and the tests)
be a static, explicit normative representation of the accepted provider-bound schema
contain the normative v0.2 representation of the frozen schema
be authored from read-only source/AST inspection of the exact provider-source allowlist (Section 5.B), never by importing or executing providers
runtime-import only the Python standard library, if any
preserve exact key names and contractual ordering
provide the fixed-fixture contract using binary_H0 / binary_H1
provide the accepted-fixture contract using binary_A / binary_B
cover the complete top-level, nested, certificate, lower-order evidence,
  family-order, source-identity, diagnostics, validation, and configuration contracts
```

It MUST NOT:

```text
runtime-import, dynamically import, execute, or call the freeze library, the verifier, or the freeze runner
import the frozen descriptor
derive its schema at runtime by executing provider functions
derive its schema at runtime by importing provider constants
open provider-generated result files
open or locate the real manifest
derive schema by inspecting result JSON
run Git, read environment variables, or perform filesystem discovery
invent alternate fixture aliases
rename frozen fields
define scientific thresholds
contain descriptor logic
contain execution authority
```

Runtime boundary model:

```text
schema-contract module =
  static explicit normative contract used by runner runtime

provider parity =
  proved only by bounded tests and direct source/AST inspection
  against the exact closed provider-source allowlist (Section 5.B)

authoritative runner runtime =
  does not import or execute provider modules directly or transitively
```

Source/AST tests MUST prove that the schema-contract module does not import provider modules, that the runner's transitive runtime import graph does not include provider modules, and that provider parity is checked without executing provider top-level code — by parsing source text or AST directly from the exact allowed paths (Section 5.B) rather than importing the providers. The schema-contract module MUST itself be import-pure (Section 8).

The module's new Git-blob and raw SHA-256 identities MUST be calculated and bound only after the implementation is complete and reviewed (Section 16). This authorization MUST NOT fabricate those identities.

---

## 8. Runner implementation obligations

When effective, the v0.2 runner `research/brainvision/run_independent_order_sensitive_synthetic_validation_v0_2.py` MUST implement the accepted specification exactly and fail closed. It MUST consume the independent schema-contract module and MUST NOT define competing fixture-key constants or alternate field aliases. It MUST be offline, quarantined, standard-library only except importing the frozen descriptor and the schema-contract module, deterministic, integer-exact, single-process, single-threaded, and disconnected from network, service, and production surfaces.

Pre-contact boundary. Before any arming-directory creation or any real-manifest contact, the runner MUST validate, fail-closed and in a fixed order, only information genuinely available pre-contact:

```text
repository root
branch
clean working tree
HEAD = origin/main
supported Python environment
later execution-authorization identity
runner, test, schema-contract, descriptor, and descriptor-test identities
expected frozen manifest path and already-bound expected identities
CLI shape
stdin emptiness
absence of every v0.2 arming, journal, staging, and final path
production and evidence-contact boundaries
```

The implementation and bounded tests MUST NEVER inspect the real manifest to perform pre-contact validation. Pre-contact checks cannot validate unread real-manifest contents.

Import-time purity. Importing any of the three authorized implementation files —

```text
research/brainvision/independent_order_sensitive_synthetic_validation_schema_contract_v0_2.py
research/brainvision/run_independent_order_sensitive_synthetic_validation_v0_2.py
research/brainvision/test_independent_order_sensitive_synthetic_fixtures_v0_2.py
```

— MUST NOT:

```text
read or poll stdin
parse authoritative CLI arguments
invoke main()
call sys.exit()
inspect Git state
run subprocesses
read environment configuration or identities
open, locate, stat, hash, or parse the real manifest
open any result or evidence artifact
create, rename, remove, or modify any file or directory
create an arming, journal, staging, or final path
consume or arm authority
load or evaluate frozen fixtures
call the descriptor
perform scientific evaluation
contact network, service, production, kernel, prompt, action, autonomy, capture, sensor, or live-ingestion surfaces
```

Module-level execution MUST be limited to side-effect-free definitions only:

```text
constants
immutable contract data
classes
functions
type aliases
```

The runner's authoritative entry point MUST remain protected by `if __name__ == "__main__":`, and importing the runner MUST NEVER execute that entry point. The bounded tests MUST prove import purity in a fresh isolated Python process (or an equivalent controlled import harness), and MUST fail if importing any new v0.2 module causes filesystem writes, directory creation, subprocess calls, Git inspection, stdin access, environment-derived configuration, manifest contact, descriptor calls, scientific evaluation, authority-state transitions, or process exit. All import-safety tests MUST use OS temporary directories and injected guards, and MUST NOT contact the real manifest or create actual repository result paths.

---

## 9. Authority-consumption and contact-accounting contract

Exact authority-consumption operation. The runner MUST use:

```text
execution_arming_path =
  temporary directory

execution_arming_path/current_state.json =
  durably written, read back, and verified intended CONTACT_ARMED state
```

The intended serialized state MUST contain:

```text
phase = CONTACT_ARMED
authority_consumed = true
contact_armed = true
manifest_contact_attempt_count = 0
manifest_read_success_count = 0
```

While still located in the temporary arming directory, that serialized state is non-authoritative and actual authority remains unconsumed. The sole consumption operation MUST be:

```text
one atomic same-filesystem directory rename:
    execution_arming_path  ->  execution_journal_dir
```

The runner MUST require:

```text
execution_journal_dir absent before rename
no separate journal mkdir
no file-only move
no copy-and-delete
no merge
no overwrite
no destination replacement
no reuse
```

The successful durable completion and verification of that single directory rename is the exact authority-consumption point. After success:

```text
authority permanently consumed
no rollback
no cleanup
no retry
no restart
no reuse
no second v0.2 operation
```

No manifest contact may occur before the successful rename.

Contact accounting. The runner MUST maintain two separate durable counters:

```text
manifest_contact_attempt_count
manifest_read_success_count
```

with the rules:

```text
attempt count increments and is durably verified before every open/read
success count increments only after all bytes are read successfully
success_count <= attempt_count
attempt_count <= 2
success_count <= 2
```

A third attempt or a third successful read is prohibited and MUST be rejected.

---

## 10. Post-contact and two-pass validation contract

For each pass independently (pass 1 and pass 2), after the authorized real-manifest read for that pass and before any descriptor call or gate evaluation for that pass, the runner MUST perform complete independent processing:

```text
fresh manifest open/read
fresh external-hash comparison
fresh parse
fresh payload-hash comparison
fresh complete schema validation
fresh fixed-fixture validation
fresh accepted-family validation
fresh certificate and lower-order validation
fresh family identity and order validation
fresh descriptor evaluation
```

Pass 2 MUST NOT reuse pass 1's:

```text
manifest bytes object
parsed object
fixture objects
validation result
descriptor outputs
scientific comparison bundle
```

If pass 1 fails before valid scientific evaluation, pass 2 MUST NOT be attempted. The maxima are `manifest_contact_attempt_count = 2` and `manifest_read_success_count = 2`.

Every post-contact schema or identity error MUST produce a controlled invalid outcome (Section 12), not a pre-contact refusal and not an uncaught exception.

Descriptor input boundary. The descriptor may receive only validated raw 64-entry integer binary vectors:

```text
fixed fixture:
  binary_H0
  binary_H1

accepted fixtures:
  binary_A
  binary_B
```

The runner MUST NOT pass into the descriptor:

```text
fixture labels
indices
seed tuples
certificates
manifest metadata
lower-order evidence
expected result labels
```

Hash handling: recomputing hashes to revise, replace, normalize, or newly bind historical identities is prohibited; computing the observed external and payload hashes for comparison against the already-bound expected identities is permitted only after authorized contact.

---

## 11. Scientific gate preservation

The runner MUST preserve the preregistered gate exactly:

```text
fixed positive distinguished
8 of 8 generated pairs distinguished
7 of 8 is scientific failure
all controls unchanged
full nuisance enumeration
no sampling
two complete pass bundles byte-identical
all boundary, serialization, and publication checks valid
```

No tuning, threshold adjustment, tolerance addition, fixture removal, family reordering, majority rule, or scientific rescue is authorized. The exhaustive nuisance controls use the preregistered Method B exactly as frozen; the runner-local integer-exact reference recomputation MUST NOT reuse descriptor implementation helpers. Permanent posture is preserved:

```text
STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY
FORMAL_HOLD = active
Mode_0 = active
```

---

## 12. Failure and exit-code contract

The runner MUST implement the exact exit model:

```text
0 = published scientific PASS
1 = published scientific FAIL
2 = unconsumed pre-contact refusal
3 = consumed controlled validation invalidity
4 = consumed implementation/infrastructure failure
5 = consumed publication/verification failure
```

For post-contact schema or identity invalidity, the runner MUST record exactly:

```text
controlled_outcome_available = true
controlled_outcome_kind = SYNTHETIC_GATE_INVALID

scientific_result_available = false
scientific_result_kind = null
scientific_evaluation_reached = false
descriptor_evaluation_reached = false

terminal_status = INVALID_POST_CONTACT
exit_code = 3
no three-file scientific publication
```

No post-consumption outcome may be routed as:

```text
UNAUTHORIZED_EXECUTION
exit 2
```

The runner MUST use the canonical failure vocabulary from the accepted specification, including:

```text
EVIDENCE_ARMING_FAILED
CONTACT_ARM_PROMOTION_FAILED
MANIFEST_READ_FAILED_AFTER_CONSUMPTION
POSTCONTACT_SCHEMA_INVALID
POSTCONTACT_IDENTITY_INVALID
POSTCONTACT_IMPLEMENTATION_EXCEPTION
SCIENTIFIC_EVALUATION_EXCEPTION
RESULT_CONSTRUCTION_FAILED
STAGING_WRITE_FAILED
STAGING_VERIFICATION_FAILED
PROMOTION_FAILED
FINAL_VERIFICATION_FAILED
EVIDENCE_UPDATE_FAILED_AFTER_CONSUMPTION
```

`EVIDENCE_ARMING_FAILED` and `CONTACT_ARM_PROMOTION_FAILED` are pre-consumption refusals (exit 2, authority unconsumed). Arbitrary traceback serialization into scientific or terminal evidence is not authorized; a bounded, sanitized implementation diagnostic (exception class name and bounded message) is permitted for triage only.

---

## 13. Evidence and publication architecture

Evidence architecture. The runner MUST use:

```text
execution_journal_dir/current_state.json =
  atomically replaceable current durable state (initial contents carried in by the arming-directory
  rename of Section 9, not a separately created file)

execution_journal_dir/terminal_evidence.json =
  exclusive-once immutable terminal record
```

Terminal evidence MUST use the self-reference-safe wrapper:

```text
{
  "payload": { ... },
  "payload_sha256": "<digest of canonical payload bytes only>"
}
```

with the digest computed over the canonical serialized payload bytes only (excluding the `payload_sha256` field). Writing terminal evidence MUST use:

```text
deterministic canonical serialization
durable write
read-back verification
payload digest verification
truthful phase and scientific flags
exclusive-once creation of terminal_evidence.json
```

For evidence-update failure after consumption:

```text
failure code = EVIDENCE_UPDATE_FAILED_AFTER_CONSUMPTION
exit = 4
last_verified_durable_state remains authoritative
bounded console fallback required
no claim that a failed evidence medium records its own failure
```

Scientific publication architecture. The implementation MAY construct code for the new v0.2 publication paths, but bounded tests MUST redirect every write to operating-system temporary directories. This authorization prohibits the creation, during implementation or bounded tests, of the actual repository paths:

```text
research/brainvision/results/.independent_order_sensitive_synthetic_validation_v0_2.arming
research/brainvision/results/.independent_order_sensitive_synthetic_validation_v0_2.execution_journal
research/brainvision/results/.independent_order_sensitive_synthetic_validation_v0_2.staging
research/brainvision/results/independent_order_sensitive_synthetic_validation_v0_2
```

No authoritative result directory, journal directory, staging directory, or arming directory may be created before a later execution authorization and a separate explicit Hilmir execution order. A successful scientific result (exit 0 or 1) publishes exactly the three reserved final files; a controlled invalid (exit 3) produces durable terminal evidence and no three-file scientific publication.

---

## 14. Bounded-test authorization and required coverage

When this authorization becomes effective, it authorizes bounded non-authoritative tests only, inside the single authorized v0.2 test file. All tests MUST:

```text
use injected synthetic manifest bytes or objects
use operating-system temporary directories
avoid the real frozen manifest
avoid authoritative result paths
avoid the authoritative CLI against the real manifest
avoid v0.1 files and staging evidence
avoid production and kernel paths
```

Bounded test seam. The authoritative main / CLI MUST use frozen paths, identities, and configuration only:

```text
no caller-supplied alternate manifest path
no caller-supplied alternate output path
no environment identity or configuration override
```

Bounded tests may exercise internal functions only through explicit in-process dependency injection, such as:

```text
injected manifest bytes or read callable
injected temporary path bundle
injected Git-state results
injected filesystem-operation functions
injected clock/timestamp provider
injected descriptor callable where a failure path must be tested
```

These test seams MUST:

```text
be callable only directly by bounded tests
not be selectable through the authoritative CLI
not be selectable through environment variables
not alter authoritative constants
not permit real-manifest or real-result-path substitution at runtime
```

No separate helper file is created; all implementation remains inside the exact three-file allowlist.

The tests MUST cover every acceptance item from Section 16 of the accepted correction specification, including:

```text
literal binary_H0 / binary_H1 assertions
literal binary_A / binary_B assertions
schema-provider parity proved by source/AST inspection (not by executing providers)
runner-owned alias rejection
missing/unexpected/malformed schema fields
arming path is a complete temporary directory
verified CONTACT_ARMED state before promotion
one same-filesystem atomic directory rename
no separate execution_journal_dir creation
no file-only move into a pre-created journal directory
no copy-and-delete promotion
no merge
no overwrite
no destination replacement
no reuse of an existing journal directory
rename failure leaves authority unconsumed
rename success consumes authority
no manifest contact before rename success
no rollback or retry after rename success
import purity of all three v0.2 modules in a fresh isolated process
contact attempt/read-success counters
both-pass independent validation
controlled invalid exit 3
post-contact exception exit 4
journal and terminal-evidence behavior
evidence-medium failure fallback
staging and promotion failures
no post-consumption UNAUTHORIZED_EXECUTION
no v0.1, kernel, service, or live-system contact
```

The tests MUST include source/AST boundary checks sufficient to prove that:

```text
the runner imports the independent schema-contract module
the runner defines no competing fixture-key constants
the runner defines no alternate field aliases
the schema-contract module does not import provider modules
the runner's transitive runtime import graph does not include provider modules
provider parity is checked without executing provider top-level code
the real manifest path is not contacted by bounded tests
the implementation change set contains only the three allowlisted files (no file outside the three-file allowlist is created or modified)
```

Bounded tests are non-authoritative: they consume no execution authority, contact no real manifest, and create none of the actual v0.2 repository paths.

---

## 15. Source and production-boundary checks

The runner source and the schema-contract module source MUST pass source/AST boundary checks that reject genuine executable routes involving:

```text
production imports (torment_service/, kernel)
historical F3
historical asymmetry-audit modules
PsiTRS
prerecorded challenger bridges
network, HTTP, external APIs
camera, screen capture, sensors, live ingestion
environment-supplied identities or configuration overrides
unbounded subprocess routes
alternate manifest paths
alternate result paths
dynamic import of prohibited modules
runtime import (direct or transitive) of the frozen provider modules (freeze library, verifier, freeze runner)
runtime import or execution of any read-only source-inspection-only dependency
import-time side effects in any of the three authorized modules
runner-owned fixture-key constants or field aliases
```

The runner's and the schema-contract module's transitive runtime import graphs MUST exclude every frozen provider module; provider parity is established only by read-only source/AST inspection of the exact Section 5.B paths, never by importing or executing them. Import of any of the three authorized modules MUST be side-effect-free per the Section 8 import-time purity contract.

Only narrowly bounded, read-only Git subprocess use is permitted, and only for committed-identity and repository-state verification (frozen by the later execution authorization); no general subprocess facility, no caller-supplied command, and no mutating Git command. These operations use fixed commands and fixed authorized paths only, must not use `shell=True`, and constitute the bounded repository-state / identity-verification category (Section 5.C), not general source-inspection authority. The runner MUST read no environment variable as an identity or configuration input, and environment values cannot override the frozen identities, configuration, control plan, manifest path, or publication paths.

---

## 16. Identity-binding and review sequence

All new identities remain unbound during implementation:

```text
runner Git blob = UNBOUND
runner raw SHA-256 = UNBOUND
runner-test Git blob = UNBOUND
runner-test raw SHA-256 = UNBOUND
schema-contract Git blob = UNBOUND
schema-contract raw SHA-256 = UNBOUND
configuration identity = UNBOUND
```

This authorization MUST NOT invent or predict any hash. After implementation and bounded tests, the sequence is, in order:

```text
direct source review
Codex adversarial implementation review
identity calculation and binding
new execution-authorization document
latest-commit authorization binding
final pre-contact review
separate explicit Hilmir execution order
```

No v0.1 identity or authority carries forward. The descriptor and descriptor-test identities are the frozen Stage S2 identities recorded in the governing documents and are reused unchanged; this authorization does not restate, recompute, or alter them.

Implementation environment and workflow (for future implementation work). Future Codex Python implementation and test work uses:

```text
Command Prompt
conda activate torment
cd /d C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric
```

Routine `python --version` or `where python` checks are not required unless there is a specific interpreter or environment concern. Claude performs no Git operations; Hilmir performs commits and pushes.

---

## 17. Explicit prohibitions

Even when effective, this authorization SHALL NOT permit:

```text
authoritative runner execution
real frozen-manifest contact (open, read, hash, parse, or evaluate)
scientific evaluation against the real frozen family
runtime import or execution of any frozen provider module (freeze library, verifier, freeze runner), directly or transitively
import-time side effects in any of the three authorized modules (filesystem, subprocess, Git, stdin, environment, manifest, descriptor, authority, or scientific evaluation on import)
read-only inspection or metadata access outside the exact categories authorized by Sections 4, 5.A, 5.B, and Section 5.C (repository-state / identity verification)
creation of any actual v0.2 arming, journal, staging, or final repository path
publication into the real v0.2 result paths
a fourth implementation file or a second test file
modification of any read-only dependency or any frozen v0.1 artifact
rerun of the Stage S1 fixture freezer
modification of the frozen manifest, descriptor, descriptor-test, or provider sources
renaming, rewriting, remapping, aliasing, or normalizing any frozen manifest field
runner-owned competing fixture-key constants or field aliases
tuning, relaxing, sampling, aggregating, or otherwise weakening the scientific gate
altering fixture membership, order, or the accepted count of 8
reinterpreting, rescuing, strengthening, or reviving the strong-order hypothesis
storing SYNTHETIC_GATE_INVALID as a scientific_result_kind or publishing it as a scientific result
producing the three-file scientific bundle for a controlled invalid (exit 3) outcome
serializing UNAUTHORIZED_EXECUTION (or any refusal-class label) as a post-consumption terminal status
serializing arbitrary traceback text into evidence
claiming guaranteed terminal-evidence-file creation on a failed evidence medium
inventing, recalculating, normalizing, or altering any existing hash or Git-blob identity
fabricating any v0.2 hash before implementation review
```

Inspection authority is exactly four closed categories; nothing outside them is authorized:

```text
implementation targets (Section 4) =
  editable and inspectable

runtime dependencies (Section 5.A) =
  importable and inspectable, immutable unless also an implementation target

frozen inspection-only dependencies (Section 5.B) =
  source/AST inspectable only, never imported, executed, or modified

repository-state and identity verification (Section 5.C) =
  fixed read-only metadata/Git operations, not arbitrary source inspection
```

Permanent production boundary. This authorization MUST NOT authorize modification or contact involving:

```text
torment_service/kernel/
production memory behavior
live service/runtime behavior
prompt surfaces
action surfaces
autonomy surfaces
live ingestion
historical F3
PsiTRS
prerecorded challenger bridges
```

Everything remains quarantined under `research/brainvision/` and `docs/`. Brainvision remains offline, quarantined, non-production, non-service, non-kernel, and non-memory-integrated, and MUST NOT be integrated into the production TORMENT memory system or kernel without a later explicit architectural discussion with Hilmir and his approval of the integration route. The v0.2 lane does not amend, rescue, rerun, weaken, replace, or reinterpret the frozen historical F3 result.

---

## 18. Authorization checklist

This authorization is acceptable for adversarial review only if all of the following hold:

```text
[ ] docs-only, non-executing, non-manifest-contacting, offline, quarantined, non-production/service/kernel/memory
[ ] activation rule requires explicit Hilmir acceptance AND commit of the exact accepted bytes to synchronized main
[ ] IMPLEMENTATION_AUTHORIZED_IF_EFFECTIVE and BOUNDED_NONAUTHORITATIVE_TESTS_AUTHORIZED_IF_EFFECTIVE both True
[ ] AUTHORITATIVE_RUNNER_EXECUTION / REAL_MANIFEST_CONTACT / SCIENTIFIC_RESULT_PUBLICATION all False
[ ] exact three-file allowlist; no fourth file; whole test suite in the single v0.2 test file
[ ] dependency allowlists are exact and closed; runtime imports are distinct from read-only source inspection
[ ] runner runtime imports only descriptor_v0_1 + schema_contract_v0_2 (beyond stdlib); no provider module in the runtime/transitive graph
[ ] read-only source/AST inspection limited to the closed provider-source + named governing-document allowlist; no open-ended class; no dependency modified
[ ] frozen v0.1 artifacts and retained staging preserved; freezer not rerun; manifest/descriptor/providers unaltered
[ ] schema-contract module: runner-external, STATIC, provider-free at runtime (stdlib-only imports), no real-manifest access, exact keys/order, binary_H0/H1 + binary_A/B
[ ] provider parity is source/AST-based (parse allowed paths), not runtime execution of providers
[ ] all three new modules are import-pure (side-effect-free module level; runner entry under if __name__ == "__main__"; import purity proved in a fresh isolated process)
[ ] bounded-test seams are in-process dependency injection only, unavailable through the authoritative CLI or environment
[ ] runner: pre-contact boundary validates only unread-manifest-independent expectations
[ ] consumption = one atomic same-filesystem arming-directory rename; journal never separately created; no rollback/retry after
[ ] split attempt/read-success counters; attempt before open/read; success after full read; both <= 2; success <= attempt
[ ] both passes fully validate independently; pass 2 reuses no pass-1 object; pass 2 skipped if pass 1 fails pre-evaluation
[ ] descriptor receives only raw 64-entry binary_H0/H1 and binary_A/B vectors; no metadata/certificates/labels
[ ] scientific gate unchanged; 8-of-8; 7-of-8 is failure; no weakening
[ ] exit model 0/1/2/3/4/5; controlled invalid exit 3, not a scientific result, no three-file publish
[ ] no post-consumption UNAUTHORIZED_EXECUTION/exit 2; canonical failure vocabulary required; no arbitrary traceback in evidence
[ ] current_state.json atomic-replace; terminal_evidence.json exclusive-once immutable with {payload, payload_sha256}
[ ] EVIDENCE_UPDATE_FAILED_AFTER_CONSUMPTION exit 4 + last_verified_durable_state + bounded console fallback; no impossible guarantee
[ ] bounded tests: injected fixtures, OS temp dirs, no real manifest / no actual v0.2 paths / no v0.1 / no kernel-service-live contact
[ ] AST/source checks prove the runner imports the independent schema-contract module, defines no competing fixture-key constants or aliases, imports no provider module directly or transitively, and the implementation change set contains only the three allowlisted files
[ ] bounded tests cover every Section-16 acceptance item and the full atomicity prohibitions
[ ] inspection authority is exactly four closed categories (impl targets §4, runtime deps §5.A, frozen inspection-only §5.B, bounded repo-state/identity verification §5.C); no inspection or metadata access outside them
[ ] no fourth file = no file outside the exact three-file change allowlist is created or modified (not a claim that the repository has only three Brainvision files)
[ ] all new v0.2 identities UNBOUND; no fabricated hashes; identity binding only after implementation and review
[ ] review sequence: source review -> Codex adversarial review -> identity binding -> execution authorization -> Hilmir order
[ ] FORMAL_HOLD, Mode_0, STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY preserved
[ ] permanent kernel/service/memory/F3/PsiTRS/prerecorded/live-ingestion boundary preserved
[ ] closing verdict distinguishes proposed implementation authority from current execution prohibition
```

---

## 19. Authorization verdict

```text
DOCUMENT_STATUS = READY_FOR_ADVERSARIAL_REVIEW

IMPLEMENTATION_AUTHORIZED_IF_EFFECTIVE = True
BOUNDED_NONAUTHORITATIVE_TESTS_AUTHORIZED_IF_EFFECTIVE = True

AUTHORITATIVE_RUNNER_EXECUTION_AUTHORIZED = False
REAL_MANIFEST_CONTACT_AUTHORIZED = False
SCIENTIFIC_RESULT_PUBLICATION_AUTHORIZED = False

AUTHORIZATION_EFFECTIVE_ONLY_AFTER =
    EXPLICIT_HILMIR_ACCEPTANCE_AND_COMMIT_OF_EXACT_REVIEWED_BYTES
```

*End — TORMENT Brainvision Independent Order-Sensitive Synthetic-Validation v0.2 Implementation Authorization v0.1. Docs-only, non-executing, non-manifest-contacting, offline, quarantined, non-production, non-service, non-kernel, non-memory-integrated. Conditional on explicit Hilmir acceptance and commit of these exact reviewed bytes to synchronized main, it authorizes only the implementation of the exact three-file allowlist (`independent_order_sensitive_synthetic_validation_schema_contract_v0_2.py`, `run_independent_order_sensitive_synthetic_validation_v0_2.py`, `test_independent_order_sensitive_synthetic_fixtures_v0_2.py`), bounded non-authoritative testing inside that single test file, and read-only review of the named frozen providers and governing documents. It binds implementation to the accepted v0.2 correction specification exactly: the atomic same-filesystem arming-directory rename as the sole authority-consumption point; split `manifest_contact_attempt_count`/`manifest_read_success_count` counters (both <= 2, success <= attempt); full independent two-pass validation with no pass-1 reuse; the descriptor receiving only raw 64-entry `binary_H0`/`binary_H1` and `binary_A`/`binary_B` vectors; the unchanged 8-of-8 scientific gate; the 0/1/2/3/4/5 exit model with `SYNTHETIC_GATE_INVALID` as a controlled exit-3 outcome that is never a scientific result and never a three-file publication; `current_state.json` atomic replacement and exclusive-once immutable `terminal_evidence.json` with a `{payload, payload_sha256}` digest; and `EVIDENCE_UPDATE_FAILED_AFTER_CONSUMPTION` (exit 4) with a `last_verified_durable_state` and bounded console fallback. It NEVER authorizes authoritative runner execution, real frozen-manifest contact, scientific evaluation against the real frozen family, or publication into the real v0.2 result paths, and it forbids creating any actual v0.2 arming/journal/staging/final path during implementation or bounded tests. All new v0.2 identities are UNBOUND; no hash is invented or predicted; identity binding, a new execution authorization, and a separate explicit Hilmir execution order remain future steps. No v0.1 identity or authority carries forward. The dependency allowlists are exact and closed, runtime imports are distinct from read-only source inspection, the schema-contract runtime is static and provider-free, provider parity is source/AST-based rather than runtime execution, all three new modules are import-pure, the bounded-test seams are unavailable through the CLI or environment, and "no fourth file" means no file outside the three-file change allowlist is created or modified. Claude performs no Git operations; Hilmir performs commits and pushes. FORMAL_HOLD and Mode_0 remain active; the frozen F3 result is neither amended nor reinterpreted; Brainvision remains offline and quarantined.*

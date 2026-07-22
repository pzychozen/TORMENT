# TORMENT Brainvision — Independent Order-Sensitive Synthetic Validation v0.2 — Implementation Findings v0.1

## 1. Document status

This is a docs-only implementation-findings record for the completed and committed TORMENT Brainvision Stage S3B v0.2 synthetic-validation implementation. It records observed facts from a read-only review of the synchronized committed repository state. It creates no executable authority.

```text
document_class      = implementation findings (docs-only)
authority_created   = none
code_modified        = none
tests_modified       = none
frozen_providers_modified = none
prior_docs_modified  = none
result_paths_created = none
git_mutations        = none
runner_executed      = false
real_manifest_contact = none
identities_bound      = none (deferred to a future separately reviewed phase)
```

This record does not amend, rescue, rerun, weaken, replace, or reinterpret the frozen historical F3 result.

## 2. Purpose

Record, for the committed v0.2 implementation, the exact committed surface, the implementation and scientific-gate findings, the atomicity/evidence/contact-accounting posture, the bounded-test and committed-replay results, the review and correction history, the non-contact/non-publication confirmations, the current identity status, the remaining execution prohibitions, and the next separately reviewed phase — while preserving all permanent boundaries.

This document is descriptive only. It does not calculate, invent, predict, or bind any implementation identity, and it does not authorize execution or real-manifest contact.

## 3. Governing documents and baseline

### 3.1 Accepted governing documents

```text
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_VALIDATION_V0_2_CORRECTION_SPECIFICATION_v0.1.md
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_VALIDATION_V0_2_IMPLEMENTATION_AUTHORIZATION_v0.1.md
```

### 3.2 Authorization effectivity

The implementation authorization became effective at:

```text
4dd7784
docs(research): authorize synthetic validation v0.2 implementation
```

### 3.3 Authoritative completed baseline

Recorded synchronized implementation commit:

```text
short HEAD    = 1530037
commit subject = research(brainvision): implement synthetic validation v0.2
branch         = main
HEAD           = origin/main
working tree   = clean
```

### 3.4 Read-only Git observation (full commit identity)

Command form used (read-only):

```cmd
set GIT_OPTIONAL_LOCKS=0
git rev-parse HEAD
git rev-parse origin/main
git status --short --branch
```

Observed:

```text
git rev-parse HEAD      = 153003782b69f9c3a384df5a149bdc3eda53b0fb
git rev-parse origin/main = 153003782b69f9c3a384df5a149bdc3eda53b0fb
git status --short --branch (first line) = ## main...origin/main
HEAD == origin/main     = true (branch synchronized with remote)
index.lock              = absent
```

Note on working-tree cleanliness: `git status --short` additionally lists whole-repository ` M` markers that are the known CRLF line-ending mount artifact only. A real-content comparison (`git diff --numstat --ignore-all-space`) shows zero changed tracked lines, so the working tree is clean with respect to committed content. Individual file Git blobs and raw SHA-256 identities were deliberately NOT calculated; those remain a future separately reviewed phase.

## 4. Exact committed implementation surface

The three committed files (now tracked in the repository at HEAD `1530037`):

```text
research/brainvision/independent_order_sensitive_synthetic_validation_schema_contract_v0_2.py
research/brainvision/run_independent_order_sensitive_synthetic_validation_v0_2.py
research/brainvision/test_independent_order_sensitive_synthetic_fixtures_v0_2.py
```

Recorded surface facts:

```text
implementation file count       = 3
fourth implementation file       = absent
frozen dependency modifications  = none
production/kernel modifications   = none
```

## 5. Implementation findings

### 5.1 Static schema contract

The v0.2 schema-contract module is:

```text
static
provider-free at runtime
import-pure
standard-library only
ordered and exact
strict int-not-bool where required
```

Fixed and accepted vector-key contracts:

```text
fixed fixture:
  binary_H0
  binary_H1

accepted fixtures:
  binary_A
  binary_B
```

Test-only fixture builders (`make_manifest`, `make_fixed_fixture`, `make_accepted_fixture`, and their supporting synthetic helpers) were removed from the runtime schema module and now live only in the bounded test file. The runtime schema surface exposes no fixture builders.

### 5.2 Scientific distinction

Scientific distinction now uses exact equality or inequality of:

```text
descriptor.affine_plus_complement_signature(vector)
```

Decision rule:

```text
equal exact signatures   = not distinguished
unequal exact signatures = distinguished
```

The following do NOT determine scientific PASS or FAIL:

```text
canonical_sha256
serialized descriptor payload identity
raw binary inequality
manifest lower-order metadata equality
transport hashes
```

### 5.3 Control implementation

The gate performs real observed controls rather than hardcoded success fields.

Malformed and degenerate controls include:

```text
sequence below required length
sequence above required length
non-integer entry
bool entry
negative entry
entry greater than 1
all-zero sequence
all-one sequence
```

The expected descriptor validation codes/stages are checked exactly (each case's observed `failure_code` and `failure_stage` are compared against the descriptor's canonical input-validation codes; correctness is derived from those observations, not asserted as a constant).

Identity controls include:

```text
repeat determinism
independently allocated equal vectors
raw signature identity behavior
affine signature identity behavior
affine-plus-complement signature identity behavior
```

### 5.4 Method-B enumeration

Complete exhaustive nuisance-control counts:

```text
rotations                        = 64
affine transforms                = 2048
affine-plus-complement transforms = 4096
```

Enumeration posture:

```text
sampling = false
full enumeration = derived from completed counts
no majority shortcut
no tolerance
no probabilistic route
runner-local transform construction is independent of descriptor transformation helpers
descriptor receives only the resulting raw binary vectors
```

## 6. Scientific-gate findings

### 6.1 Preserved scientific gate

```text
fixed positive must be distinguished
8 of 8 generated accepted pairs must be distinguished
7 of 8 = scientific FAIL
full controls required
two independently computed pass bundles must be byte-identical
no scientific rescue or weakening
```

### 6.2 Two-pass independence

Each pass freshly performs:

```text
manifest-byte acquisition through the accounted reader
external and payload hashing
JSON parsing
complete schema and family validation
malformed/degenerate controls
identity controls
full Method-B enumeration
exact descriptor-signature evaluation
fixed and accepted-pair comparisons
scientific-bundle construction
```

No pass-1 scientific object, transformed vector, signature, control result, or bundle is reused by pass 2. The two independently computed pass bundles must serialize byte-identically; any divergence is a consumed implementation failure, never a scientific rescue.

### 6.3 Dormant authoritative route

The complete authoritative route now exists:

```text
main
-> strict CLI/stdin validation
-> pre-contact validation
-> fixed authoritative paths and dependencies
-> accounted manifest reader
-> shared arming/read/two-pass/publication core
-> canonical exit code
```

It remains intentionally unavailable because required identities and the later execution authorization remain:

```text
UNBOUND
```

While unbound:

```text
exit                        = 2
authority unconsumed
manifest contact             = 0
descriptor evaluation        = 0
scientific evaluation        = 0
authoritative path creation   = 0
```

The authoritative CLI was NOT executed during implementation or validation.

## 7. Atomicity, evidence, and contact accounting

### 7.1 Atomicity of authority consumption

Authority consumption is implemented as:

```text
complete temporary arming directory
verified CONTACT_ARMED current_state.json
one same-filesystem directory rename to execution journal
```

At the consumption boundary:

```text
journal destination absent
no separate journal creation
no copy/delete
no merge
no overwrite
no replacement
no reuse
```

### 7.2 Evidence model

```text
current_state.json   = atomically replaceable durable state
terminal_evidence.json = exclusive-once immutable terminal record
payload_sha256        = SHA-256 of canonical payload bytes only
```

Windows directory synchronization is honestly best-effort; no stronger durability guarantee is claimed.

### 7.3 Contact accounting

```text
manifest_contact_attempt_count
manifest_read_success_count

0 <= success <= attempt <= 2
attempt durably recorded before read
success recorded only after full read
```

### 7.4 Exit model

```text
0 = published scientific PASS
1 = published scientific FAIL
2 = unconsumed pre-contact refusal
3 = consumed controlled validation invalidity
4 = consumed implementation/infrastructure failure
5 = consumed publication/verification failure
```

No post-consumption failure can become `UNAUTHORIZED_EXECUTION` or exit 2.

### 7.5 Publication architecture

The implementation contains the reserved exact three-file scientific publication path, but no authoritative publication occurred. Controlled-invalid exit 3 produces operational evidence only and no scientific bundle.

## 8. Bounded-test and committed-replay findings

### 8.1 Committed-state replay — operator command form

```cmd
python -m pytest -q -p no:cacheprovider ^
  --basetemp="%TORMENT_S3B_PYTEST_BASE%" ^
  research/brainvision/test_independent_order_sensitive_synthetic_fixtures_v0_2.py ^
  research/brainvision/test_independent_order_sensitive_descriptor_v0_1.py
```

### 8.2 Authoritative observed result

```text
114 passed in 17.31s
```

### 8.3 Replay conditions

```text
test run occurred after commit and push
HEAD = origin/main
working tree remained clean
temporary pytest base was outside the repository root
```

## 9. Review and correction history

Material review sequence (recorded accurately):

```text
initial bounded implementation:
  100 tests passed
  direct review found scientific-gate incompleteness

confirmed corrections:
  exact affine-plus-complement signature distinction
  real malformed/degenerate controls
  real identity controls
  complete Method-B enumeration
  real-descriptor gate tests
  dormant authoritative wiring
  schema runtime-surface reduction
  stronger import-purity and change-set tests

corrected bounded implementation:
  114 tests passed

final independent source-review verdict:
  ACCEPT_IMPLEMENTATION_READY_TO_COMMIT
```

Review-integrity caveat:

```text
an initially staged review snapshot was stale and contained the pre-correction files;
the reviewer detected the mismatch and issued the final acceptance only after reading
the genuinely current Windows repository files that were subsequently committed
at 1530037
```

This was a review-input snapshot mismatch that was detected and corrected before acceptance. It was NOT a scientific failure and NOT a repository failure.

## 10. Non-contact and non-publication findings

```text
real frozen manifest bytes read           = 0
real frozen fixtures evaluated            = 0
authoritative v0.2 CLI invocation         = 0
actual v0.2 arming path created           = false
actual v0.2 execution journal created     = false
actual v0.2 staging path created          = false
actual v0.2 final publication path created = false
scientific result published                = false
```

## 11. Identity status

```text
runner Git blob                       = UNBOUND
runner raw SHA-256                     = UNBOUND
runner-test Git blob                   = UNBOUND
runner-test raw SHA-256                 = UNBOUND
schema-contract Git blob               = UNBOUND
schema-contract raw SHA-256             = UNBOUND
configuration identity                 = UNBOUND
later execution-authorization identity  = UNBOUND
```

These identities are NOT calculated, invented, predicted, or bound in this findings document.

## 12. Remaining execution prohibitions

Implementation is complete and committed, but execution remains prohibited. No step below has yet authorized execution or real-manifest contact.

```text
authoritative v0.2 CLI execution   = prohibited
real frozen Stage S1 manifest contact = prohibited
scientific publication              = prohibited
identity binding                    = not yet performed
execution authorization             = not yet present
explicit Hilmir execution order      = not yet given
```

## 13. Next separately reviewed phase

```text
calculate committed file identities
bind the v0.2 implementation/configuration identities
prepare a separate docs-only v0.2 execution authorization
bind that authorization to the latest synchronized implementation commit
perform a final pre-contact adversarial review
obtain a separate explicit Hilmir execution order
```

None of those steps has yet authorized execution or real-manifest contact.

## 14. Permanent boundaries

```text
FORMAL_HOLD = active
Mode_0 = active
STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY
```

Brainvision remains:

```text
offline
quarantined
non-production
non-service
non-kernel
non-memory-integrated
```

This implementation does not amend, rescue, rerun, weaken, replace, or reinterpret the frozen historical F3 result.

## 15. Findings verdict

```text
IMPLEMENTATION_STATUS = COMPLETE_AND_COMMITTED
IMPLEMENTATION_REVIEW = ACCEPTED
COMMITTED_REPLAY = 114_PASSED

IMPLEMENTATION_IDENTITIES_BOUND = False
EXECUTION_AUTHORIZATION_PRESENT = False
AUTHORITATIVE_EXECUTION_AUTHORIZED = False
REAL_MANIFEST_CONTACT_AUTHORIZED = False
SCIENTIFIC_PUBLICATION_AUTHORIZED = False

NEXT_PHASE =
COMMITTED_IDENTITY_CALCULATION_AND_SEPARATE_EXECUTION_AUTHORIZATION
```

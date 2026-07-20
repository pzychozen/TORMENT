# TORMENT Brainvision Independent Order-Sensitive Synthetic-Fixture Freeze-Runner Implementation Authorization v0.1

## 0. Decision

```text
A. IMPLEMENTATION AND BOUNDED TESTING OF THE AUTHORITATIVE SYNTHETIC-FIXTURE
   FREEZE RUNNER ARE AUTHORIZED.
```

This document authorizes only the future implementation and bounded testing of the authoritative synthetic-fixture freeze runner for the independent order-sensitive descriptor challenger branch.

It does not authorize, and explicitly withholds:

```text
canonical seed scanning
actual fixture discovery
two-pass authoritative execution
family freezing
manifest publication
runner invocation
challenger implementation
challenger validation
retained F3 contact
frozen K=3 contact
PsiTRS contact
production integration
TORMENT memory-system integration
kernel modification
```

The authority to execute the runner (the single authoritative two-pass operation, its one-run consumption threshold, and manifest publication) is a separate later docs-only decision: the S1C execution authorization. This document is a docs-only implementation authorization. No runner or library function was executed while preparing it, and no Git command was run while preparing it.

---

## 1. Governing documents and completed prerequisites

This authorization is governed by the independent synthetic-fixture specifications, not by the older algebraic freezer branch:

```text
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_DESCRIPTOR_CHALLENGER_SPECIFICATION_v0.1.md
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_FIXTURE_FREEZE_SPECIFICATION_v0.1.md
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_FIXTURE_IMPLEMENTATION_AUTHORIZATION_v0.1.md
```

The accepted S1B implementation (verifier, generator/reducer, freeze library, and their two bounded test files) is complete and accepted. The prior algebraic freezer execution authorization was reviewed only for execution-authorization structure and one-run consumption semantics; none of its retained-stream-specific facts are carried into this branch. The synthetic-fixture branch has no retained candidate stream: the authoritative operation scans the canonical seed space directly under the frozen configuration.

Completed prerequisite state:

```text
S1A specifications accepted
S1B verifier / generator / freeze library implemented and accepted
S1B bounded tests implemented and accepted (focused suite green)
```

---

## 2. Reviewed repository baseline

This authorization was prepared against:

```text
branch = main
HEAD = 9c74c4bc271812e0489505224ad2f8360b84db44
origin/main = 9c74c4bc271812e0489505224ad2f8360b84db44
working tree = clean
commit subject = research(brainvision): implement synthetic fixture infrastructure
Python version = 3.11.15
```

The reviewed baseline is not necessarily the runner-implementation HEAD or the eventual execution HEAD.

The runner-authorization (this document's docs-only) commit will become a later docs-only HEAD. The exact runner-implementation commit and the eventual execution HEAD are separate later commits.

```text
the runner-authorization commit identity must not be guessed or precomputed
the runner-implementation commit identity must not be guessed or precomputed
the eventual execution HEAD must not be guessed or precomputed
each exact commit identity must be recorded only after that commit and push
```

---

## 3. Frozen accepted S1B source identities

The five accepted S1B implementation files are frozen at the reviewed baseline. Git-object identity and Windows raw-file SHA-256 identity are recorded separately.

Verifier

```text
path = research/brainvision/independent_order_sensitive_synthetic_fixture_verifier_v0_1.py
Git blob = 74e25002db4e45870ee20397cbc9e5416f108cb0
Windows raw SHA-256 = 15e31e50319daaf8e45704c5e3b339e876a0e2949927365928b32f5c412ba95c
```

Generator

```text
path = research/brainvision/independent_order_sensitive_synthetic_fixture_generator_v0_1.py
Git blob = 77bc2e319e1283ce5d00b283f99a1d1d56732d83
Windows raw SHA-256 = 001317367d5f8e3c06ae3da177901b88f94560ae555eeca54247464e2cb9ed78
```

Freeze library

```text
path = research/brainvision/independent_order_sensitive_synthetic_fixture_freeze_v0_1.py
Git blob = a06a80ac1a253a6b85f2c3e6bf4bf712b0d78d8a
Windows raw SHA-256 = ef78cc21a3a6e139a781ce4f8c356c88b9a132ab89771d8250dc57ea375b2fca
```

Verifier test

```text
path = research/brainvision/test_brainvision_independent_order_sensitive_synthetic_fixture_verifier_v0_1.py
Git blob = 97f2605284c53dedfec43d8e65112d30418877a8
Windows raw SHA-256 = af0a798d5195e78ad2e051cc0ec2846ec82d20c8d796f448e355f77ec4d76032
```

Generator/freeze test

```text
path = research/brainvision/test_brainvision_independent_order_sensitive_synthetic_fixture_freeze_v0_1.py
Git blob = a7774cfc49e05e75c1d49355a28166fd2375abae
Windows raw SHA-256 = a02c613f2620755611c3e86914458c4f72bfa2a7d3cfce55f94748bafef0fa0c
```

Identity doctrine:

```text
Git blob identity and Windows raw-file SHA-256 identity are distinct identities.
Neither may substitute for the other.
A mismatch in either identity blocks later execution authorization.
```

Any change to any of the five S1B source identities requires a new review and a new authorization decision.

---

## 4. Docs-only authorization-commit boundary

The commit containing this authorization must add exactly one documentation file:

```text
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_FIXTURE_FREEZE_RUNNER_IMPLEMENTATION_AUTHORIZATION_v0.1.md
```

It must not create, modify, rename, or delete any existing source, test, result, evidence, or documentation file, including but not limited to:

```text
the five frozen S1B implementation files
any research/brainvision results or retained evidence
research/brainvision/results/results.csv
research/brainvision/results/results.json
the challenger descriptor
historical F3 modules and their retained evidence
historical asymmetry-audit modules and their retained evidence
frozen candidates 478, 479, 480
PsiTRS
torment_service and production-kernel files
the TORMENT memory system
```

Any source-identity change requires a new review and a new authorization decision.

---

## 5. Exact future runner implementation scope

The following, and only the following, two files are authorized for future creation:

```text
research/brainvision/run_independent_order_sensitive_synthetic_fixture_freeze_v0_1.py
research/brainvision/test_brainvision_run_independent_order_sensitive_synthetic_fixture_freeze_v0_1.py
```

No third implementation, helper, configuration, manifest, result, or convenience file is authorized by this document.

The runner may have an explicit execution boundary:

```python
if __name__ == "__main__":
```

because the runner is the future execution boundary. The presence of this entry point does not itself authorize invocation. No runner execution is permitted during its implementation, review, testing, commit, or push. Execution requires the separate S1C execution authorization.

Runner identity (to be bound by the later S1C execution authorization by Git blob and Windows raw SHA-256):

```text
RUNNER_NAME = run_independent_order_sensitive_synthetic_fixture_freeze_v0_1
RUNNER_VERSION = 0.1
RUNNER_TEST_NAME = test_brainvision_run_independent_order_sensitive_synthetic_fixture_freeze_v0_1
```

---

## 6. Runner dependency boundary

The runner and runner test must use Python standard-library source only.

The runner may import only:

```text
research/brainvision/independent_order_sensitive_synthetic_fixture_verifier_v0_1.py
research/brainvision/independent_order_sensitive_synthetic_fixture_generator_v0_1.py
research/brainvision/independent_order_sensitive_synthetic_fixture_freeze_v0_1.py
```

plus narrowly necessary standard-library modules only (for example: os and pathlib for path handling, hashlib for on-disk re-read hashing, json for reading its own written bytes back for comparison, sys for exit codes, tempfile only within the runner test).

The runner may use subprocess only for exact, read-only Git identity and repository-state commands frozen by the later execution authorization (for example: resolve HEAD, resolve origin/main, report working-tree/porcelain status, resolve the frozen source blobs). It must not expose a general subprocess facility, accept a caller-supplied command, or run any mutating Git command. At implementation and test time no real subprocess Git call is made; runner tests mock all Git command responses.

The runner and runner test must not import or contact:

```text
independent_order_sensitive_descriptor_v0_1 (the challenger descriptor)
historical F3 modules
historical asymmetry-audit modules
retained F3 evidence
frozen candidates 478, 479, 480
PsiTRS
torment_service
production services
network resources
camera or screen capture
randomness sources
timestamps
host or user identity
```

Brainvision-to-TORMENT integration remains prohibited and requires a later explicit discussion with Hilmir.

Note on source-boundary scope: `validate_source_boundary` (freeze library) has an allowlist of exactly the five S1B source files. The runner uses it to validate the five frozen S1B source texts. The runner's own integrity and the runner test's integrity are bound instead by Git blob and Windows raw SHA-256 identity recorded in the later S1C execution authorization. These are two separate, complementary integrity mechanisms; neither substitutes for the other.

### 6.1 Project-module import ordering (frozen provenance rule)

The runner may import standard-library modules at module load.

The runner must not import the verifier, generator, or freeze library before all of the following identity pre-contact checks succeed:

```text
repository ownership (execution begins from the authoritative repository root)
branch is main
HEAD equals origin/main
working tree is clean, including ordinary untracked files
all five frozen S1B implementation paths are exact
all five frozen Git blob identities are exact
all five frozen Windows raw-file SHA-256 identities are exact
Python version is exact (3.11.15)
the final output directory is absent
the staging output directory is absent
```

The three S1B project modules must be imported locally (inside the runner's operation body, not at module load), and only after those identity checks pass. Importing them must still precede:

```text
fixed-fixture verification
configuration construction
source-boundary validation using the accepted library
canonical seed-iterator construction
```

This ordering prevents an altered project source from executing before its frozen Git-blob and Windows raw-file identity are established.

Bounded runner tests must prove that each of the following leaves the three project modules unimported (using injected import callbacks or mocks, never real dynamic repository discovery):

```text
dirty tree -> no project-module import
wrong branch -> no project-module import
HEAD/origin mismatch -> no project-module import
Git blob mismatch -> no project-module import
Windows raw-file mismatch -> no project-module import
output directory exists -> no project-module import
```

---

## 7. Runner pre-contact responsibilities

The runner must implement an exact fail-closed pre-contact sequence that completes, in full, before the canonical seed iterator is ever requested. Every check below must pass; the first failure refuses fail-closed.

```text
execution begins from the authoritative repository root
branch is main
HEAD equals origin/main
working tree is clean, including ordinary untracked files
the final S1C execution-authorization document exists in committed HEAD
all five frozen S1B implementation paths are exact
all five frozen Git blob identities are exact
all five frozen Windows raw-file SHA-256 identities are exact
Python version is exact (3.11.15)
runner and runner-test identities match the later execution authorization
configuration identity (payload plus SHA-256) is exact
the final output directory is absent
the staging output directory is absent
all five supplied S1B source texts pass validate_source_boundary
the fixed fixture verifies exactly (verify_fixed_fixture, valid true)
the 288-of-3906 fixed-fixture triple-disagreement certificate passes
```

These checks are ordered per Section 6.1: the identity checks (repository ownership, branch, HEAD/origin, clean tree, frozen paths, Git blobs, Windows raw SHA-256, Python version, output-path absence) run first and gate the local import of the three S1B project modules; only after the import succeeds do the library-backed checks run (configuration construction and identity, `validate_source_boundary` over the five S1B source texts, `verify_fixed_fixture`, and the 288-of-3906 certificate). `pre_contact_status` becomes `PASSED` only after every check in both groups — including the project-module import, the static source-boundary check, the configuration check, and the fixed-fixture positive-control check — succeeds.

No canonical seed may be requested before every pre-contact check succeeds.

A pre-contact refusal must not consume any later one-run execution authority (the consumption threshold is defined in the later S1C execution authorization, at the moment of first canonical-iterator contact). A pre-contact refusal must create no staging directory and no output files.

---

## 8. Exact configuration payload

The runner must construct exactly one canonical configuration object, in exactly this field order, with exactly these scalar values:

```text
configuration_schema = "torment-brainvision-independent-order-sensitive-synthetic-fixture-freeze-configuration-v0.1"
configuration_version = "0.1"
N = 64
K_synthetic = 8
seed_enumeration_policy = "canonical-lexicographic-c1-lt-c2-d1-lt-d2-mod-64-v0.1"
construction_policy = "c-plus-d-and-c-minus-d-mod-64-collision-collapsed-v0.1"
eligibility_policy = "first-failure-eight-predicate-descriptor-blind-v0.1"
duplicate_policy = "member-orbit-affine-plus-complement-slot-invariant-pair-key-v0.1"
fixed_fixture_duplicate_key_seeding = true
selection_rule = "first-eight-unique-eligible-pairs"
descriptor_blind_selection = true
pass_count = 2
parallelism = 1
backtracking = false
challenger_contact = false
frozen_F3_contact = false
```

The four policy strings are exactly the accepted freeze-library policy constants (`SEED_ENUMERATION_POLICY`, `CONSTRUCTION_POLICY`, `ELIGIBILITY_POLICY`, `DUPLICATE_POLICY`), so the configuration binds the same policies the canonical manifest embeds.

Canonical serialization rule (identical to the accepted freeze-library canonical serialization): UTF-8; ASCII-escaped; compact separators exactly `(",", ":")`; base-10 integers; JSON `true`/`false`; no NaN/Inf/negative-zero; fixed insertion order (never sorted); one terminal LF appended. The exact single-line canonical form is:

```text
{"configuration_schema":"torment-brainvision-independent-order-sensitive-synthetic-fixture-freeze-configuration-v0.1","configuration_version":"0.1","N":64,"K_synthetic":8,"seed_enumeration_policy":"canonical-lexicographic-c1-lt-c2-d1-lt-d2-mod-64-v0.1","construction_policy":"c-plus-d-and-c-minus-d-mod-64-collision-collapsed-v0.1","eligibility_policy":"first-failure-eight-predicate-descriptor-blind-v0.1","duplicate_policy":"member-orbit-affine-plus-complement-slot-invariant-pair-key-v0.1","fixed_fixture_duplicate_key_seeding":true,"selection_rule":"first-eight-unique-eligible-pairs","descriptor_blind_selection":true,"pass_count":2,"parallelism":1,"backtracking":false,"challenger_contact":false,"frozen_F3_contact":false}
```

The runner must derive the configuration SHA-256 by calling the accepted freeze-library canonical configuration function on this exact object:

```python
configuration_sha256 = freeze.canonical_configuration_sha256(configuration_payload)
configuration_identity = freeze.build_configuration_identity(configuration_payload)
```

No configuration value is left to runtime choice. This implementation authorization does not compute and does not freeze the resulting SHA-256; the later S1C execution authorization will freeze the exact `configuration_sha256` value and require the pre-contact check to match it.

---

## 9. Exact two-pass architecture

The runner's sole authoritative operation is a deterministic two-pass freeze-with-replay. Each pass must independently perform, from scratch:

```text
create a fresh canonical seed iterator (iter_canonical_seed_tuples)
verify the fixed fixture (verify_fixed_fixture)
seed seen_pair_keys with exactly the fixed-fixture pair key (fixed_fixture_pair_key)
scan from the first canonical seed
compute construction and certificates via the accepted mathematics
apply first-failure eight-predicate eligibility
apply duplicate diagnostics (including fixed-fixture-key duplicate suppression)
accept the first eight unique eligible pairs
stop immediately after the eighth acceptance
build a family_frozen=false candidate manifest (build_candidate_manifest)
derive canonical payload bytes (canonical_payload_bytes)
derive manifest_payload_sha256
derive canonical complete-manifest bytes (canonical_manifest_bytes)
derive external manifest SHA-256 (external_manifest_sha256)
derive the candidate-pass comparison bundle (build_candidate_pass_bundle)
```

Pass 2 must not reuse any pass-1 object:

```text
seed iterator
supports
binary arrays
certificates
triple evidence
member keys
pair keys
seen-key state
accepted records
search diagnostics
manifest objects
serialized bytes
hash values
```

No third pass, retry, resume, parallel scan, backtracking, alternative selector, fixture replacement, or challenger-informed selection is authorized. Selection is descriptor-blind: the challenger descriptor is never constructed, imported, executed, or consulted.

### 9.1 Canonical result kinds and two-pass replay (all kinds)

Two independent passes and replay agreement are required for every canonical result kind, not only for a positive accepted-eight result. A pass produces exactly one `canonical_result_kind`:

```text
ACCEPTED_EIGHT
FIXED_FIXTURE_FAILURE
SEED_SPACE_EXHAUSTED
```

Pass behavior:

```text
if pass 1 produces FIXED_FIXTURE_FAILURE, pass 2 still starts with fresh state and
  independently reruns fixed-fixture verification
if pass 1 produces SEED_SPACE_EXHAUSTED, pass 2 independently rescans from the first
  canonical seed using fresh state
pass 2 must reproduce the same canonical result kind and the same candidate manifest
  independently
```

For any of `ACCEPTED_EIGHT`, `FIXED_FIXTURE_FAILURE`, or `SEED_SPACE_EXHAUSTED`, both passes must produce complete candidate bundles (a candidate manifest and its `build_candidate_pass_bundle`) and the runner must call:

```python
comparison_result = freeze.compare_candidate_passes(bundle_pass_1, bundle_pass_2)
```

Publication requires exact replay success across all six compared fields: canonical payload bytes, `manifest_payload_sha256`, canonical manifest bytes, external manifest SHA-256, accepted-fixture order, and search diagnostics.

### 9.2 Positive versus canonical-negative completion

For `ACCEPTED_EIGHT`, an exact comparison success — exactly `{"matches": true, "failure_code": null, "failure_stage": null, "mismatch_reasons": []}` — permits:

```python
finalized = freeze.finalize_authoritative_manifest(candidate_manifest_pass_1, comparison_result)
```

and only then may the published final manifest have `family_frozen = true`.

For `FIXED_FIXTURE_FAILURE` and `SEED_SPACE_EXHAUSTED`, an exact comparison success does not call positive finalization. The published canonical failure manifest is the exact replay-matched `family_frozen = false` candidate failure manifest (from `build_fixed_fixture_failure_manifest` / `build_seed_exhaustion_failure_manifest`); its canonical bytes must equal the replay-matched pass bytes.

### 9.3 Failure-result disagreement

If two canonical failure results differ in any compared field:

```text
failure_code = REPLAY_MISMATCH
failure_stage = replay_comparison
```

No canonical manifest is published. The outcome becomes a post-contact process failure with the exact process-failure two-file evidence set (Section 11.1), subject to successful publication. Neither pass's unmatched failure manifest is published.

---

## 10. Runner / execution-envelope boundary

The runner writes an execution envelope that is separate from the canonical S1A manifest. The execution envelope contains only deterministic operational provenance and outcome fields, in exactly this field order:

```text
envelope_schema
envelope_version
operation_identity
authoritative_operation
repository_execution_head
authorization_document_path
authorization_document_git_blob
python_version
runner_identity
runner_test_identity
source_identities
configuration_identity
pre_contact_status
canonical_contact_status
pass_1_identity_summary
pass_2_identity_summary
comparison_result
finalization_status
family_frozen
manifest_payload_sha256
external_manifest_sha256
failure_code
failure_stage
publication_status
```

`source_identities` holds the five frozen S1B identities in the frozen order (see Section 10.6). `pass_1_identity_summary` and `pass_2_identity_summary` hold only deterministic identity digests for each pass — never seed values, supports, or challenger-adjacent evidence (see Section 10.8). The exact type, nullability, and nested-key contract for every top-level field is given in Sections 10.4 through 10.11; no implementation may invent a key, key order, representation, or null case.

The execution envelope must not contain:

```text
timestamps
durations
host identity
username
absolute paths
machine identity
random IDs
free-form exception text
scientific interpretation
challenger values
F3 values
```

A process failure retains the exact canonical failure code and failure stage (from the accepted `SyntheticFixtureProcessFailure` contract) in `failure_code` / `failure_stage`. The runner must not invent a canonical manifest when the accepted library contract forbids one: for serialization, hash-identity, source-boundary, replay-comparison, and finalization process failures, no canonical manifest is written — the intended evidence set is exactly the execution-envelope JSON and the summary TXT (see Section 11.1). The library's own canonical failure-manifest builders (`build_fixed_fixture_failure_manifest`, `build_seed_exhaustion_failure_manifest`) are the only source of a `family_frozen=false` failure manifest, and only for their exact conditions.

### 10.1 Exact contact-state semantics

`pre_contact_status` is one of exactly:

```text
NOT_STARTED
PASSED
REFUSED
```

`canonical_contact_status` is one of exactly:

```text
NOT_CONTACTED
PASS_1_STARTED
PASS_1_COMPLETE
PASS_2_STARTED
PASS_2_COMPLETE
```

Rules:

```text
pre_contact_status begins as NOT_STARTED
pre_contact_status becomes REFUSED when any pre-contact check fails
pre_contact_status becomes PASSED only after every pre-contact check, the
  project-module import, the static source-boundary check, the configuration
  check, and the fixed-fixture positive-control check succeeds
canonical_contact_status remains NOT_CONTACTED until the runner begins
  authoritative pass 1
PASS_1_STARTED is recorded immediately before the first complete pass pipeline begins
PASS_1_COMPLETE requires a complete candidate or canonical failure result for pass 1
PASS_2_STARTED occurs only after pass 1 completes and fresh pass-2 state is established
PASS_2_COMPLETE requires complete pass-2 evidence
```

The later S1C execution authorization defines the authority-consumption threshold; this document neither redefines nor prematurely opens that authority.

### 10.2 Double fixed-fixture check

The fixed fixture is verified twice, for two distinct purposes:

```text
pre-contact fixed-fixture verification is an implementation/provenance positive-control
  gate; it writes no canonical failure manifest and its failure is a pre-contact refusal
each authoritative pass independently verifies the fixed fixture again
a pass-level fixed-fixture failure may use the accepted canonical fixed-fixture
  failure-manifest function (build_fixed_fixture_failure_manifest)
```

Thus a pre-contact fixed-fixture failure and a canonical pass fixed-fixture failure remain distinct outcomes with distinct evidence.

### 10.3 Frozen runner-level failure vocabulary

`failure_stage` is one of exactly:

```text
pre_contact
pass_1
pass_2
replay_comparison
finalization
publication
```

`failure_code` is drawn only from the committed S1A vocabulary. Exact runner-level mapping (at minimum):

```text
wrong CLI shape / wrong repository root / wrong branch / HEAD != origin/main /
dirty tree / authorization document absent or uncommitted / output or staging path
already exists
-> UNAUTHORIZED_EXECUTION / pre_contact

frozen Git blob mismatch / Windows raw-file SHA-256 mismatch / Python-version mismatch /
runner or runner-test identity mismatch / configuration identity mismatch /
on-disk publication hash mismatch
-> HASH_IDENTITY_FAILURE / applicable stage

static source-boundary rejection
-> the exact code raised by validate_source_boundary / pre_contact

fixed-fixture positive-control rejection before pass 1
-> the exact fixed-fixture S1A failure code / pre_contact

seed validation or generator integrity failure in a pass
-> the exact deterministic generator failure code / pass_1 or pass_2

structurally malformed candidate bundle
-> MANIFEST_SCHEMA_FAILURE / replay_comparison

valid pass disagreement
-> REPLAY_MISMATCH / replay_comparison

finalization without exact successful comparison
-> REPLAY_MISMATCH / finalization

final identity recomputation failure
-> HASH_IDENTITY_FAILURE / finalization

staging creation / file write / byte encoding failure during publication
-> SERIALIZATION_FAILURE / publication

file close / re-read / verification / identity disagreement / final rename failure
-> HASH_IDENTITY_FAILURE / publication
```

`SERIALIZATION_FAILURE` is used for byte creation, write, or encoding failure; `HASH_IDENTITY_FAILURE` is used for re-read or identity disagreement. No free-form exception text enters the envelope or the summary. Any unexpected exception is normalized to exactly one authorized code/stage according to the operation boundary at which it occurred.

### 10.4 Common identity formats

```text
repository-relative path: JSON string; forward slashes only; no leading slash;
  no drive prefix; no "." or ".." segments; case-sensitive; never null where an
  identity object exists. Absolute paths are prohibited from every envelope field.
Git blob: JSON string; exactly 40 lowercase hexadecimal characters.
raw SHA-256: JSON string; exactly 64 lowercase hexadecimal characters.
repository commit: JSON string; exactly 40 lowercase hexadecimal characters.
canonical SHA-256: JSON string; exactly 64 lowercase hexadecimal characters.
```

### 10.5 `runner_identity` and `runner_test_identity`

`runner_identity` is an object with keys in exactly this order:

```text
artifact_role
artifact_id
source_path
git_blob
raw_sha256
```

with exact values (git_blob 40-hex, raw_sha256 64-hex; no field nullable in an emitted post-contact envelope; actual blob/raw hash frozen later by the execution authorization):

```text
artifact_role = "runner"
artifact_id = "independent-order-sensitive-synthetic-fixture-freeze-runner-v0.1"
source_path = "research/brainvision/run_independent_order_sensitive_synthetic_fixture_freeze_v0_1.py"
```

`runner_test_identity` has the same key order and formats, with:

```text
artifact_role = "runner_test"
artifact_id = "independent-order-sensitive-synthetic-fixture-freeze-runner-test-v0.1"
source_path = "research/brainvision/test_brainvision_run_independent_order_sensitive_synthetic_fixture_freeze_v0_1.py"
```

### 10.6 `source_identities`

An array of exactly five objects, in exactly this order:

```text
verifier
generator
freeze_library
verifier_test
generator_freeze_test
```

Each object has keys in exactly this order:

```text
artifact_role
source_path
git_blob
raw_sha256
```

with the exact role/path mapping (and each `git_blob` / `raw_sha256` equal to the identities already frozen in Section 3 of this document):

```text
verifier                research/brainvision/independent_order_sensitive_synthetic_fixture_verifier_v0_1.py
generator               research/brainvision/independent_order_sensitive_synthetic_fixture_generator_v0_1.py
freeze_library          research/brainvision/independent_order_sensitive_synthetic_fixture_freeze_v0_1.py
verifier_test           research/brainvision/test_brainvision_independent_order_sensitive_synthetic_fixture_verifier_v0_1.py
generator_freeze_test   research/brainvision/test_brainvision_independent_order_sensitive_synthetic_fixture_freeze_v0_1.py
```

No object or field is nullable. No runtime sorting is permitted; the declared order is authoritative.

### 10.7 `configuration_identity`

Object with keys in exactly this order:

```text
configuration_payload
configuration_sha256
```

`configuration_payload` is the exact ordered 16-field configuration object of Section 8. `configuration_sha256` is exactly 64 lowercase hexadecimal characters over the exact canonical configuration bytes. Neither field is nullable after pre-contact configuration validation succeeds.

### 10.8 `pass_1_identity_summary` and `pass_2_identity_summary`

In every emitted post-contact execution envelope, both `pass_1_identity_summary` and `pass_2_identity_summary` are always objects — never `null` — with keys in exactly this order:

```text
pass_label
pass_status
canonical_result_kind
manifest_payload_sha256
external_manifest_sha256
accepted_fixture_order
search_diagnostics
failure_code
failure_stage
```

No emitted envelope may set `pass_1_identity_summary = null` or `pass_2_identity_summary = null`. Before a pass begins, its summary is the exact `NOT_STARTED` object below (not `null`).

Exact pass-1 not-started object:

```json
{
  "pass_label":"PASS_1",
  "pass_status":"NOT_STARTED",
  "canonical_result_kind":null,
  "manifest_payload_sha256":null,
  "external_manifest_sha256":null,
  "accepted_fixture_order":null,
  "search_diagnostics":null,
  "failure_code":null,
  "failure_stage":null
}
```

Exact pass-2 not-started object:

```json
{
  "pass_label":"PASS_2",
  "pass_status":"NOT_STARTED",
  "canonical_result_kind":null,
  "manifest_payload_sha256":null,
  "external_manifest_sha256":null,
  "accepted_fixture_order":null,
  "search_diagnostics":null,
  "failure_code":null,
  "failure_stage":null
}
```

A pre-contact refusal produces no execution-envelope file at all (Section 11.1); therefore no pass-summary representation is needed for a refusal that occurs before staging or evidence creation. For every envelope that is actually serialized, both pass-summary objects are mandatory.

Value domains:

```text
pass_label = "PASS_1" in pass_1_identity_summary; "PASS_2" in pass_2_identity_summary
pass_status = NOT_STARTED | COMPLETE | FAILED
canonical_result_kind = null | ACCEPTED_EIGHT | FIXED_FIXTURE_FAILURE | SEED_SPACE_EXHAUSTED
accepted_fixture_order = null, or an array in acceptance order whose every element is
  exactly a two-entry array [key_0,key_1], each key exactly 64 ASCII "0"/"1"
  characters with key_0 < key_1
search_diagnostics = null, or the exact S1A search-diagnostics object with keys in order:
  total_seeds_visited, eligibility_rejection_counts, eligible_duplicate_count,
  accepted_seed_order_positions, terminal_seed_tuple, terminal_status
  (eligibility_rejection_counts retains the exact eight committed rejection-reason key order)
```

Nullability by `pass_status` (the object is never partially populated):

```text
NOT_STARTED: canonical_result_kind, manifest_payload_sha256, external_manifest_sha256,
  accepted_fixture_order, search_diagnostics, failure_code, failure_stage are all null
COMPLETE: canonical_result_kind = one of the three kinds; manifest_payload_sha256 = 64-hex;
  external_manifest_sha256 = 64-hex; accepted_fixture_order = array (empty only for
  FIXED_FIXTURE_FAILURE); search_diagnostics = complete exact object;
  failure_code = null; failure_stage = null
FAILED: canonical_result_kind, manifest_payload_sha256, external_manifest_sha256,
  accepted_fixture_order, search_diagnostics are all null; failure_code = one canonical
  allowed code; failure_stage = pass_1 or pass_2
```

### 10.9 `comparison_result`

Either `null`, or exactly the accepted freeze-library comparison object with keys in order `matches, failure_code, failure_stage, mismatch_reasons`. Exact success:

```json
{"matches":true,"failure_code":null,"failure_stage":null,"mismatch_reasons":[]}
```

Exact mismatch: `matches = false`, `failure_code = REPLAY_MISMATCH`, `failure_stage = replay_comparison`, `mismatch_reasons` a nonempty array containing only the accepted library vocabulary, in the accepted order:

```text
canonical_payload_bytes_mismatch
manifest_payload_sha256_mismatch
canonical_manifest_bytes_mismatch
external_manifest_sha256_mismatch
accepted_fixture_order_mismatch
search_diagnostics_mismatch
```

`comparison_result` is `null` until two complete candidate bundles exist, and remains `null` when either pass ends in a process failure without a canonical bundle.

### 10.10 Other top-level field nullability

```text
envelope_schema = fixed non-null string
envelope_version = fixed non-null string "0.1"
operation_identity = fixed non-null string
authoritative_operation = JSON boolean, never null
repository_execution_head = non-null 40-hex string after pre-contact success
authorization_document_path = fixed non-null repository-relative path
authorization_document_git_blob = non-null 40-hex string after pre-contact success
python_version = exact string "3.11.15"
pre_contact_status = never null
canonical_contact_status = never null
finalization_status = never null
family_frozen = JSON boolean, never null
manifest_payload_sha256 = 64-hex string only when a canonical manifest exists; otherwise null
external_manifest_sha256 = 64-hex string only when a canonical manifest exists; otherwise null
failure_code = null on successful canonical result publication; otherwise one exact authorized code
failure_stage = null when failure_code is null; otherwise one exact runner stage
publication_status = never null
```

### 10.11 Canonical execution-envelope serialization

The execution envelope is serialized exactly as:

```text
UTF-8; without BOM; ASCII-escaped JSON; compact separators exactly "," and ":";
declared top-level key order preserved; declared nested-key order preserved;
declared array order preserved; base-10 integers; JSON true/false/null;
no floating-point values; no NaN; no Infinity; no negative zero;
no whitespace outside JSON strings; exactly one LF byte after the closing brace;
no additional bytes.
```

The exact equivalent standard-library operation is:

```python
json.dumps(envelope, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode("utf-8") + b"\n"
```

The runner must validate all envelope value types before serialization. `sort_keys=True` is never permitted; declared insertion order is authoritative. The execution-envelope SHA-256 may be computed for publication verification but must not be inserted into the envelope (no twenty-fifth top-level field is added). The canonical S1A manifest is written using the exact canonical manifest bytes returned by the accepted freeze library; the runner must not parse and reserialize it.

---

## 11. Exact future output paths and write policy

Final output directory (quarantined under `research/brainvision/results/`):

```text
research/brainvision/results/independent_order_sensitive_synthetic_fixture_freeze_v0_1/
```

Sibling staging directory (hidden, dot-prefixed):

```text
research/brainvision/results/.independent_order_sensitive_synthetic_fixture_freeze_v0_1.staging/
```

Exact canonical file names (frozen):

```text
independent_order_sensitive_synthetic_fixture_freeze_manifest_v0_1.json
independent_order_sensitive_synthetic_fixture_freeze_execution_envelope_v0_1.json
independent_order_sensitive_synthetic_fixture_freeze_summary_v0_1.txt
```

The summary is deterministic operator convenience only. It is not canonical evidence and does not replace either JSON file. No output file is optional; each outcome has an exact, complete published set.

### 11.1 Exact outcome-specific published sets

Pre-contact refusal:

```text
final directory absent
staging directory absent
files written = none
```

Completed canonical result — any one of: positive `family_frozen=true` finalization, canonical fixed-fixture failure manifest, or canonical seed-exhaustion failure manifest — published set (all three required):

```text
independent_order_sensitive_synthetic_fixture_freeze_manifest_v0_1.json
independent_order_sensitive_synthetic_fixture_freeze_execution_envelope_v0_1.json
independent_order_sensitive_synthetic_fixture_freeze_summary_v0_1.txt
```

Post-contact process failure with no canonical manifest (serialization / hash-identity / source-boundary / replay / finalization process failure) — intended evidence set (both required):

```text
independent_order_sensitive_synthetic_fixture_freeze_execution_envelope_v0_1.json
independent_order_sensitive_synthetic_fixture_freeze_summary_v0_1.txt
```

When publication itself fails, retain the staging directory exactly as the runner leaves it. A partial staging set is failure evidence, not a permitted successful file set; it is never promoted and never repaired.

The canonical S1A manifest is retained as its exact canonical bytes, separate from the execution envelope. The summary never replaces canonical evidence.

### 11.2 Exact publication write order (frozen)

```text
1. create the staging directory exclusively (fail if it already exists)
2. write the manifest JSON when a canonical manifest exists for the outcome
3. write the execution-envelope JSON
4. write the summary TXT
5. close every file
6. re-read every file
7. compare exact bytes and SHA-256 identities against the intended bytes
8. confirm the staging directory contains exactly the expected outcome-specific set
9. atomically rename the staging directory to the final directory
```

No overwrite, no merge, no append, no reuse of prior outputs, and no automatic overwrite or destructive rollback of promoted final evidence. Runner tests may use operating-system temporary directories with automatic cleanup; runner tests must not write anywhere under the repository tree.

### 11.3 Exact publication_status vocabulary

`publication_status` is one of exactly:

```text
NOT_STARTED
STAGING_CREATED
EVIDENCE_WRITTEN
VERIFIED_FOR_PROMOTION
PROMOTED
FAILED
```

Because the canonical execution-envelope bytes cannot be rewritten after promotion, the execution envelope written into staging (and therefore the exact bytes atomically promoted) stores:

```text
published envelope value = VERIFIED_FOR_PROMOTION
```

`PROMOTED` is a runtime/operator adjudication state only: after the atomic staging-to-final rename, stdout may report publication success, but no promoted file may be reopened and rewritten merely to change the envelope from `VERIFIED_FOR_PROMOTION` to a post-rename state. `NOT_STARTED`, `STAGING_CREATED`, `EVIDENCE_WRITTEN`, and `FAILED` are runtime/staging states; only `VERIFIED_FOR_PROMOTION` is ever serialized into a promoted canonical envelope.

The staged and promoted envelope value `VERIFIED_FOR_PROMOTION` means exactly, and only:

```text
all intended files were written
all files were closed
all files were re-read
all intended bytes and SHA-256 identities matched
the staged file set was exact for the outcome
the staging directory was ready for the single rename attempt
```

It does not claim that the rename succeeded. Staging is immutable after verification: no staged envelope or summary is rewritten to reflect a post-verification state.

### 11.4 Exact runner exit codes

```text
exit 0 = atomic promotion succeeded for a complete canonical result
exit 1 = post-contact mathematical, replay, finalization, or process failure whose
         deterministic failure evidence was successfully promoted
exit 2 = pre-contact refusal; no staging or final evidence created
exit 3 = publication operation failed or atomic rename failed
```

No other exit code is an authorized runner outcome.

### 11.5 Exact publication-failure stderr protocol

For `exit 3`, stdout must be empty. Stderr must contain exactly one ASCII line with one terminal LF and nothing else — no operating-system message, exception string, path, filename, host detail, or traceback.

For staging creation, encoding, or write failure:

```text
SYNTHETIC_FIXTURE_FREEZE_PUBLICATION_FAILURE SERIALIZATION_FAILURE publication
```

For close, re-read, byte verification, hash verification, exact-set verification, or atomic rename failure:

```text
SYNTHETIC_FIXTURE_FREEZE_PUBLICATION_FAILURE HASH_IDENTITY_FAILURE publication
```

Rename failure specifically: `exit = 3`; stdout empty; stderr the `HASH_IDENTITY_FAILURE` line above; the staging directory remains unchanged; the staged envelope remains `publication_status = VERIFIED_FOR_PROMOTION`. This is coherent — the envelope certifies readiness for promotion, while the external exit/stderr channel records that promotion failed. No staged file is reopened, rewritten, removed, renamed individually, or replaced.

Earlier publication failures (before an envelope or summary can be completed): the runner does not promise those files exist; any partial staging directory is retained exactly as left; the exit code and stderr are the authoritative operational failure record; no synthetic replacement envelope or summary is fabricated. A partial staging set is never a successful evidence set.

The later execution authorization must require the operator to capture: exit code; stdout; stderr; final-directory presence or absence; staging-directory presence or absence; and the staging file listing and hashes when staging exists.

### 11.6 Exact summary TXT template

The summary is a deterministic derivative of the execution envelope. Encoding: UTF-8; without BOM; ASCII content only; LF line endings only; no blank lines; exactly one terminal LF; no additional bytes. Every line is `key=value` with no spaces around `=`, in exactly this line order:

```text
summary_schema=torment-brainvision-independent-order-sensitive-synthetic-fixture-freeze-summary-v0.1
operation_identity=<operation_identity>
authoritative_operation=<true-or-false>
repository_execution_head=<40-hex-or-null>
pre_contact_status=<value>
canonical_contact_status=<value>
pass_1_status=<NOT_STARTED-or-COMPLETE-or-FAILED>
pass_2_status=<NOT_STARTED-or-COMPLETE-or-FAILED>
canonical_result_kind=<ACCEPTED_EIGHT-or-FIXED_FIXTURE_FAILURE-or-SEED_SPACE_EXHAUSTED-or-PROCESS_FAILURE>
comparison_status=<NOT_RUN-or-MATCH-or-MISMATCH>
finalization_status=<value>
family_frozen=<true-or-false>
manifest_payload_sha256=<64-hex-or-null>
external_manifest_sha256=<64-hex-or-null>
failure_code=<canonical-code-or-null>
failure_stage=<runner-stage-or-null>
publication_status=VERIFIED_FOR_PROMOTION
```

Exact derivation rules:

```text
true and false are lowercase; null is the four ASCII characters "null"
pass_1_status = pass_1_identity_summary.pass_status (the summary is always an object; there is
  no fallback-from-null path)
pass_2_status = pass_2_identity_summary.pass_status (the summary is always an object; there is
  no fallback-from-null path)
comparison_status = NOT_RUN when comparison_result is null; MATCH when comparison_result.matches
  is true; MISMATCH when comparison_result.matches is false
canonical_result_kind = the common replay-matched canonical result kind when one exists;
  PROCESS_FAILURE when no canonical result is publishable
family_frozen = true only for a successfully finalized ACCEPTED_EIGHT result; false for every
  other outcome
```

No free-form text, error details, timestamps, durations, paths, filenames, host information, or scientific interpretation may appear in the summary. For a publication failure before summary completion, no replacement summary is fabricated.

### 11.7 Exact finalization_status vocabulary

`finalization_status` is one of exactly:

```text
NOT_STARTED
NOT_APPLICABLE
COMPLETE
FAILED
```

Exhaustive mapping (every outcome resolves to exactly one value):

```text
NOT_STARTED = comparison_result is null and no finalization decision is yet possible.
  This includes: pass 1 not complete; pass 2 not complete; a pass-level process failure
  before two complete candidate bundles exist.

NOT_APPLICABLE = comparison completed but positive finalization must not occur. This is
  exactly: replay-matched FIXED_FIXTURE_FAILURE; replay-matched SEED_SPACE_EXHAUSTED; and
  REPLAY_MISMATCH / replay_comparison (comparison_result.matches = false,
  failure_code = REPLAY_MISMATCH, failure_stage = replay_comparison). In all three cases
  finalize_authoritative_manifest is never called.

COMPLETE = canonical_result_kind = ACCEPTED_EIGHT and comparison_result.matches = true and
  finalize_authoritative_manifest completed successfully and family_frozen = true.

FAILED = positive finalization was actually attempted and failed (for example
  REPLAY_MISMATCH / finalization or HASH_IDENTITY_FAILURE / finalization). A replay mismatch
  discovered during comparison is NOT FAILED, because finalization was never attempted.
```

Summary-TXT `finalization_status` derivation examples:

```text
comparison not run                    -> NOT_STARTED
matched fixed-fixture failure         -> NOT_APPLICABLE
matched seed exhaustion               -> NOT_APPLICABLE
replay mismatch (replay_comparison)   -> NOT_APPLICABLE
successful positive finalization      -> COMPLETE
attempted positive finalization fails -> FAILED
```

---

## 12. Failure and one-run semantics

The runner implementation must distinguish, deterministically:

```text
pre-contact refusal
post-contact process failure
canonical fixed-fixture failure
seed-space exhaustion
replay mismatch
finalization / hash failure
publication failure
positive frozen-family completion
```

The exact one-run consumption threshold (the moment authority is consumed, and its exact post-contact prohibitions) will be defined by the later S1C execution authorization, not by this document. The runner implementation must expose enough deterministic evidence (via `pre_contact_status`, `canonical_contact_status`, and the per-pass identity summaries) to establish, unambiguously, whether canonical seed contact occurred.

A future retry must never occur automatically. No runner implementation test may invoke the real complete canonical iterator.

---

## 13. Bounded runner-test authority

The runner test is authorized to use only:

```text
unittest
unittest.mock
plain assertions
temporary directories outside the repository tree (tempfile) with automatic cleanup
hand-authored finite seed iterables
hand-authored candidate bundles
mocked Git command responses
mocked source and raw-hash inputs
mocked publication failures
```

The runner test must not import `pytest` (an external pytest collector may run it). No test module may contain an executable `if __name__ == "__main__":` block except that the runner itself (not its test) may contain the single execution-boundary block described in Section 5.

Runner tests must cover at least:

```text
pre-contact checks occur before any iterator contact
dirty-tree refusal
HEAD / origin mismatch refusal
wrong-branch refusal
Git blob mismatch refusal
Windows raw-file SHA-256 mismatch refusal
Python-version mismatch refusal
source-boundary failure refusal
fixed-fixture failure refusal
output-path-exists refusal (final or staging already present)
configuration mismatch refusal
no seed requested after any pre-contact refusal
pass 1 and pass 2 receive fresh iterator and state objects
no pass-1 object enters pass 2
exact candidate comparison
replay mismatch blocks finalization
exact success permits exactly one finalization
final manifest differs from the candidate only by family_frozen and derived identities
staging-only writes
exclusive staging creation
on-disk re-read and hash verification before promotion
atomic staging-to-final rename
no overwrite of existing final evidence
publication-failure retention
execution-envelope field order
absence of timestamps, host identity, absolute paths, and free-form text
no project-module import before identity pre-contact checks pass (Section 6.1)
exact runner_identity key order and validation
exact runner_test_identity key order and validation
exact five-entry source_identities order
Git blob format rejection (not 40 lowercase hex)
raw SHA-256 format rejection (not 64 lowercase hex)
absolute-path rejection in identity fields
configuration_identity key order
pass-summary key order
all pass-summary nullability states (NOT_STARTED / COMPLETE / FAILED)
comparison_result null and exact-object cases
envelope top-level and nested key order
envelope one-terminal-LF serialization
envelope no-BOM behavior
envelope rejection of floats, NaN, and Infinity
summary exact byte-for-byte template
summary exact line order
summary one-terminal-LF behavior
summary contains no free-form text
two-pass replay of a fixed-fixture failure
two-pass replay of seed exhaustion
failure-manifest replay mismatch blocks manifest publication
positive result alone invokes finalization
canonical failures do not invoke positive finalization
rename failure retains unchanged staged bytes
rename failure returns exit 3
rename failure emits exactly the one-line HASH_IDENTITY_FAILURE stderr
rename failure produces empty stdout
write failure before envelope creation does not fabricate an envelope
partial staging is retained and not treated as success
exit-code vocabulary (0 / 1 / 2 / 3) is exact
pass_1_identity_summary cannot be null in an emitted envelope
pass_2_identity_summary cannot be null in an emitted envelope
the PASS_1 and PASS_2 NOT_STARTED objects serialize byte-identically to the frozen forms
PASS_1 and PASS_2 pass_label values are fixed
no summary-TXT fallback-from-null path exists for pass_1_status / pass_2_status
finalization_status = NOT_STARTED when comparison has not run
finalization_status = NOT_APPLICABLE for replay-matched FIXED_FIXTURE_FAILURE
finalization_status = NOT_APPLICABLE for replay-matched SEED_SPACE_EXHAUSTED
finalization_status = NOT_APPLICABLE for REPLAY_MISMATCH / replay_comparison
finalization_status = COMPLETE for successful positive finalization
finalization_status = FAILED only when positive finalization was attempted and failed
replay mismatch never invokes finalize_authoritative_manifest
replay mismatch never produces finalization_status = FAILED
```

Runner tests must not:

```text
consume the complete canonical iterator
discover the actual first eight fixtures
retain a generated family
write repository-tree output
produce authoritative evidence
contact frozen candidates 478, 479, 480
contact the challenger descriptor
contact PsiTRS
contact production or the TORMENT memory system
```

Instrumentation must prove non-consumption: bounded hand-authored seed iterables and injected candidate bundles only; the real full canonical iterator is never driven in any test.

---

## 14. Authority ledger

```text
S1B_IMPLEMENTATION_COMPLETE = True
S1B_IMPLEMENTATION_ACCEPTED = True

RUNNER_IMPLEMENTATION_SPECIFICATION_COMPLETE = True
RUNNER_IMPLEMENTATION_AUTHORIZED = True
BOUNDED_RUNNER_TESTS_AUTHORIZED = True

RUNNER_EXECUTION_AUTHORIZED = False
CANONICAL_SEED_SCAN_AUTHORIZED = False
FIXTURE_GENERATION_AUTHORIZED = False
AUTHORITATIVE_REPLAY_AUTHORIZED = False
FAMILY_FREEZE_AUTHORIZED = False
MANIFEST_PUBLICATION_AUTHORIZED = False
RERUN_AUTHORIZED = False

CHALLENGER_IMPLEMENTATION_AUTHORIZED = False
CHALLENGER_VALIDATION_AUTHORIZED = False
FROZEN_F3_CONTACT_AUTHORIZED = False
PsiTRS_CONTACT_AUTHORIZED = False
PRODUCTION_INTEGRATION_AUTHORIZED = False
TORMENT_MEMORY_INTEGRATION_AUTHORIZED = False
KERNEL_MODIFICATION_AUTHORIZED = False
```

---

## 15. Disposition

```text
A. RUNNER IMPLEMENTATION AND BOUNDED TESTING AUTHORIZED.
   RUNNER EXECUTION, CANONICAL SEED SCAN, FIXTURE GENERATION, FAMILY FREEZE,
   AND MANIFEST PUBLICATION REMAIN CLOSED PENDING THE S1C EXECUTION AUTHORIZATION.
```

The runner implementation is operational-as-code only after:

```text
this document is accepted
one focused adversarial review finds no blocker
this document is committed as the sole changed file
the commit is pushed to main
HEAD == origin/main
the working tree is clean
```

Recommended runner-authorization commit subject:

```text
docs(research): authorize independent order-sensitive synthetic-fixture freeze runner implementation
```

No runner or library function was executed while preparing this authorization. No canonical seed was requested. No fixture was discovered. No output or staging directory was created. No Git command was run. No challenger, PsiTRS, retained-F3, frozen-K=3, production-service, TORMENT-memory-system, or production-kernel contact occurred while preparing this authorization.

*End — TORMENT Brainvision Independent Order-Sensitive Synthetic-Fixture Freeze-Runner Implementation Authorization v0.1. Docs-only. Authorizes only the future implementation and bounded testing of the freeze runner. Runner execution, canonical seed scanning, fixture discovery, two-pass authoritative execution, family freezing, and manifest publication remain closed and require the separate S1C execution authorization.*

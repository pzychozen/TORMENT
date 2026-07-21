# TORMENT Brainvision Independent Order-Sensitive Synthetic-Validation Runner Implementation Authorization v0.1

## Document status

```text
document_type = docs-only implementation authorization
authorization_stage = S3A (synthetic-validation runner implementation)
runner_implementation_authorized = True (exactly the two-file allowlist below)
runner_bounded_non_authoritative_test_execution_authorized = True
synthetic_validation_execution_authorized = False
real_frozen_manifest_contact_authorized = False
```

Authoritative repository baseline:

```text
branch = main
HEAD = origin/main = 2458afc033e2c54dcdd089a0341d982093301ca1
working tree = clean
commit subject = research(brainvision): implement independent order-sensitive descriptor
Python = 3.11.15 (activated torment Conda environment)
```

This document authorizes only future implementation and bounded, non-authoritative testing of the synthetic-validation runner. It does not authorize the actual synthetic validation run, and it does not authorize any contact with the real frozen synthetic manifest. No runner or project function was executed while preparing it, and no Git command was run.

---

## 0. Decision

```text
A. IMPLEMENTATION AND BOUNDED, NON-AUTHORITATIVE TESTING OF THE SYNTHETIC-
   VALIDATION RUNNER ARE AUTHORIZED, LIMITED TO EXACTLY TWO FILES. THE ACTUAL
   SYNTHETIC VALIDATION RUN AND ALL CONTACT WITH THE REAL FROZEN SYNTHETIC
   MANIFEST REMAIN CLOSED, RESERVED FOR A SEPARATE STAGE S3B EXECUTION
   AUTHORIZATION.
```

This authorizes only the future creation and bounded testing of the runner module and its test module. It withholds synthetic-validation execution, real manifest contact, fixed-positive-fixture evaluation, frozen-eight-pair evaluation, result publication, and any frozen-family, F3, PsiTRS, production, service, memory, or kernel contact. Acceptance of this document does not advance execution authority.

---

## 1. Why Stage S3 is split

```text
S3A = runner and runner-test implementation authorization
S3B = later one-run synthetic-validation execution authorization
```

The split does not weaken or amend the challenger specification. It ensures, in order:

```text
runner implementation exists and is adversarially reviewed
runner and runner-test identities are committed and frozen
only then is one-run synthetic exposure authorized
```

The implementation identity must be frozen before the synthetic gate is exposed. S3A produces reviewable, testable, identity-frozen runner code that makes no real-manifest contact; S3B (separate) binds the frozen runner and runner-test identities and authorizes exactly one authoritative synthetic-validation invocation.

---

## 2. Governing documents and completed prerequisites

Governing documents:

```text
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_DESCRIPTOR_CHALLENGER_SPECIFICATION_v0.1.md
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_DESCRIPTOR_IMPLEMENTATION_AUTHORIZATION_v0.1.md
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_FIXTURE_FREEZE_SPECIFICATION_v0.1.md
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_FIXTURE_FREEZE_FINDINGS_v0.1.md
```

Where this authorization is less detailed, the challenger specification governs. The specification's control classes (§8), synthetic validation fixtures (§9), serialization contract (§10), leakage prevention (§11), and staged-authorization policy (§12, its Stage S3) are authoritative for the gate the future runner implements.

Completed prerequisite state:

```text
S0 specification accepted
S1 synthetic fixture family frozen and its findings recorded (family_frozen = true)
S2 descriptor implemented, bounded-tested, adversarially reviewed, committed, and frozen
CHALLENGER_DESCRIPTOR_IMPLEMENTATION_FROZEN = True
```

---

## 3. Reviewed repository baseline

```text
branch = main
HEAD = origin/main = 2458afc033e2c54dcdd089a0341d982093301ca1
working tree = clean
Python = 3.11.15 (activated torment Conda environment)
```

The commit that carries this authorization must contain exactly one changed file and nothing else — the addition of this document at its path below. It must not create, modify, rename, or delete any source, test, result, evidence, configuration, or other documentation file. The future runner-implementation commit and the future S3B authorization commit are separate later commits whose identities must not be guessed or precomputed here.

---

## 4. Frozen Stage S2 identities

The descriptor and its test are frozen at the committed Stage S2 implementation. This authorization must not permit their modification.

```text
implementation commit = 2458afc033e2c54dcdd089a0341d982093301ca1

descriptor path = research/brainvision/independent_order_sensitive_descriptor_v0_1.py
descriptor Git blob = f9a369e6c7f09204092155b99638f8cec4e8b1ae
descriptor raw SHA-256 = cdd313a0dfc3c71b33c4b9964397a5d0710427d612b4d781a46353a4d2522be9

descriptor-test path = research/brainvision/test_independent_order_sensitive_descriptor_v0_1.py
descriptor-test Git blob = 9054b36aebf32014053d2a877b0cb7eb42dce6fc
descriptor-test raw SHA-256 = 3eed5c7e482bad65ab662941bc3b3bc04477e9669ae6e067d93bea4e524f3a94
```

Stage S2 acceptance record:

```text
Stage S2 bounded suite = 38 passed, 0 failed
authoritative interpreter = Python 3.11.15
Codex adversarial review = ACCEPT
synthetic exposure before commit = false
```

Git-object identity and Windows raw-file SHA-256 identity are separate and both mandatory. The future runner imports the frozen descriptor module by its committed identity; it must not modify, wrap, or shadow it. The descriptor and descriptor-test files are outside every allowlist in this document.

---

## 5. Frozen synthetic-manifest identities

Recorded and bound for the future runner (S3B only). During S3A implementation and bounded tests, the real manifest must not be opened, parsed, copied, hashed, imported, or evaluated. Its path and hashes may exist as frozen constants in the runner source.

```text
manifest path = research/brainvision/results/independent_order_sensitive_synthetic_fixture_freeze_v0_1/independent_order_sensitive_synthetic_fixture_freeze_manifest_v0_1.json

external manifest SHA-256 = 05ce02af1c1a4b508e9a6566c9ff638849039df5caa45479858e634e2a117404
manifest payload SHA-256 = 56a141bd13937caa6ac800ab8c9c12229f6bf75ee97ab490a26844664a65b4b9
freeze configuration SHA-256 = 5f3a568bc4286136a93d9b9bac74985af4b68202373a56210eddbcfbf2625263

family_frozen = true
canonical_result_kind = ACCEPTED_EIGHT
comparison_status = MATCH
K_synthetic = 8
```

These are provenance/binding constants only. Embedding them as frozen literals in the runner source is permitted; opening or reading the real manifest bytes is not permitted before Stage S3B execution.

---

## 6. Exact future implementation allowlist

Exactly two future files are authorized for creation or modification, and no others:

```text
research/brainvision/run_independent_order_sensitive_synthetic_validation_v0_1.py
research/brainvision/test_independent_order_sensitive_synthetic_fixtures_v0_1.py
```

No third helper file is authorized. The following must not be modified:

```text
research/brainvision/independent_order_sensitive_descriptor_v0_1.py
research/brainvision/test_independent_order_sensitive_descriptor_v0_1.py
```

The following are NOT authorized:

```text
fixture regeneration
freezer rerun
manifest replacement
alternate fixture files
frozen-K3 adapters
candidate 478/479/480 access
historical F3 adapters
PsiTRS adapters
production integration
```

---

## 7. Future sole runner invocation and CLI boundary

Reserved — but NOT yet authorized — future invocation:

```text
python research/brainvision/run_independent_order_sensitive_synthetic_validation_v0_1.py
```

The future runner must accept:

```text
no arguments
no flags
no configuration path
no environment-supplied identity
empty stdin
```

Any argument, flag, configuration path, environment-supplied identity, or non-empty stdin is a fail-closed pre-contact refusal (`UNAUTHORIZED_EXECUTION`). Neither S3A implementation nor its tests may execute that authoritative invocation against the real manifest. The presence of an execution entry point does not itself authorize invocation.

---

## 8. Runner architecture and import/side-effect boundary

The future runner must be:

```text
offline
quarantined
standard-library only except importing the frozen descriptor module
deterministic
integer-exact
single-process
single-threaded
network-disconnected
service-disconnected
production-disconnected
```

The runner may perform filesystem access only for:

```text
the exact frozen synthetic manifest during later S3B execution
the exact authorized output/staging paths during later S3B execution
read-only source and authorization identity verification
```

The runner must not import:

```text
torment_service
PsiTRS
historical F3 modules
historical asymmetry-audit modules
synthetic generator
synthetic freezer
production or service modules
```

It must not use:

```text
camera
screen capture
sensors
network
HTTP
external APIs
benchmark metadata
candidate IDs
historical retained evidence
```

Module-level work is limited to small immutable constants (identities, paths, the frozen control-plan constants, the failure vocabulary, the preregistered generator set). No real-manifest read, no fixture evaluation, and no expensive computation may occur at import time.

---

## 9. Pre-contact future execution boundary and one-run threshold

Before opening the real frozen manifest, the future authoritative runner (S3B) must verify, fail-closed and in a fixed order:

```text
Python = 3.11.15
repository root is exact
branch = main
working tree is clean
HEAD = origin/main
future S3B execution authorization is committed and current
authorization-path latest commit = HEAD
descriptor Git/raw identities match
descriptor-test Git/raw identities match
runner Git/raw identities match
runner-test Git/raw identities match
manifest file exists as a regular file
final output directory is absent
staging output directory is absent
stdin is empty
argv shape is exact
static source boundaries pass
```

A refusal before opening or reading the real manifest is pre-contact and does not consume future S3B authority. The future one-run authority becomes consumed at the first read of any real frozen-manifest byte. After that threshold:

```text
no retry
no rerun
no resume
no replacement run
```

regardless of pass, failure, invalidity, process failure, or publication failure. S3A does not grant that authority; it only requires the runner to implement the boundary and threshold for later S3B. The exact non-circular authorization-HEAD mechanics and the one-run consumption semantics are frozen by the S3B authorization; the runner implements the check, S3B binds the identities and opens the single run.

---

## 10. Exact manifest acceptance (S3B)

During later S3B execution, the runner must:

```text
read only the exact bound manifest path
verify external file SHA-256 before parsing
parse canonical JSON
reconstruct and verify manifest_payload_sha256
verify schema and fixed configuration identity
require family_frozen = true
require exactly one fixed fixture
require exactly eight accepted fixtures
preserve frozen accepted-fixture order
extract only validated raw 64-entry binary vectors for descriptor calls
```

No fixture may be removed, reordered, replaced, edited, reconstructed from another source, selected by descriptor output, or skipped after failure. The descriptor function receives only raw binary vectors; it must never receive manifest metadata, fixture indices, seed tuples, certificates, or pair labels. Manifest metadata may be attached to a comparison record only after the exact descriptor comparison has completed.

---

## 11. Complete synthetic gate

The future authoritative gate must include all specification-required classes with no sampling, subset reduction, random selection, or early-stop shortcut.

### 11.1 Malformed and degenerate controls

Exactly:

```text
length 63
length 65
non-integer element
bool element
negative element
element greater than 1
all-zero sequence
all-one sequence
```

Each must produce its exact first-failure code and no valid descriptor payload.

### 11.2 Identity negative controls

For every admitted valid sequence, compare it against an independently materialized exact copy:

```text
raw descriptors equal
affine-only signatures equal
affine-plus-complement signatures equal
classification = NO_DECLARED_DISTINCTION
```

Any distinction is `SYNTHETIC_NEGATIVE_CONTROL_FAILURE`.

### 11.3 Nuisance-equivalent controls (exact cardinalities)

For every admitted valid sequence, preserve the exact specification cardinalities:

```text
64 rotations
explicit reflection
32 units × 64 translations = 2048 affine relabelings
admissible complements
4096 affine-plus-complement self-orbit elements
```

Required:

```text
rotation raw tensor invariance
reflection exact lag mapping
affine exact inverse-lag permutation
complement exact antisymmetry
affine-only signature invariance where applicable
affine-plus-complement signature invariance
no self-orbit member classified as a positive distinction (classification = NUISANCE_ORBIT_EQUIVALENT)
```

No sampling, subset reduction, random selection, or early-stop shortcut is permitted.

### 11.4 Exact execution method for exhaustive controls (PREREGISTERED: METHOD B)

After inspecting the frozen descriptor API (which exposes `third_order_tensor`, `raw_labeled_signature`, `affine_only_signature`, `affine_plus_complement_signature`, `second_order_autocorrelation`, `transition_table`, and the constants `UNITS`, `UNIT_INVERSE`, `LAG_DOMAIN`, `LAG_INDEX`), this authorization preregisters exactly:

```text
METHOD B — exhaustive group-element materialization with exact theorem-derived
tensor/signature expectations, plus direct frozen-descriptor evaluation of a
fixed preregistered generator set sufficient to verify the implementation action.
```

Under Method B, for every admitted valid sequence:

```text
all 64 rotation elements, all 2048 affine relabelings, and all 4096 affine-plus-
  complement self-orbit elements are enumerated (full coverage; no sampling)
each group element's expected raw tensor / canonical vector / signature is derived
  by the exact transformation theorems of the specification:
    rotation (translation)  -> raw tensor invariant
    reflection (u = -1)     -> lag map (a,b) -> (-a mod 64, -b mod 64)
    affine unit u           -> lag permutation (a,b) -> (u^-1*a mod 64, u^-1*b mod 64)
    complement              -> exact tensor negation, D unchanged
each expected vector/signature is compared exactly (denominator-and-vector), never
  by hash and never by tolerance
```

Direct frozen-descriptor evaluation is performed on exactly this completely-stated preregistered generator set (and no other, and never result-dependent):

```text
G0 = identity                (unit u = 1, translation v = 0)
G1 = translation by 1        (unit u = 1, translation v = 1)   [rotation generator]
G2 = affine unit u = 3       (translation v = 0)               [generates the order-16 unit factor]
G3 = affine unit u = 63      (translation v = 0)               [= -1 mod 64; order-2 unit factor and the reflection]
G4 = complement              (x_i -> 1 - x_i)                  [sign generator]
```

The units group of Z_64 is Z_2 × Z_16, generated by {3, 63}; translations are generated by rotation-by-1; the admissible sign action is generated by the complement. Therefore {G1, G2, G3, G4} generate the entire 4096-element affine-plus-complement self-orbit under composition, and G0 is the identity baseline. Directly evaluating the frozen descriptor on this generator set verifies that the descriptor actually implements each generator's transformation law exactly, so the theorem-derived expectations used across the full enumeration are validated against the descriptor's real output on generators.

Observed comparison object. For every admitted valid sequence and every exhaustively materialized transformation in the 64 rotations, the 2048 affine relabelings, and the 4096 affine-plus-complement self-orbit elements, the runner must perform these exact steps:

```text
1. materialize the transformed raw 64-entry binary sequence;

2. independently recompute from that transformed raw sequence, using runner-local
   integer-exact reference mathematics:
   - centered sequence;
   - complete 3906-entry third-order tensor;
   - normalization denominator;
   - gcd-reduced labeled numerator vector;
   - theorem-relevant exact signature expectation;

3. separately derive the expected transformed tensor/vector/signature from the
   original member using the preregistered rotation, affine inverse-lag, reflection,
   and complement transformation laws;

4. compare the independent raw-sequence recomputation against the theorem-derived
   expectation using exact denominator-and-complete-vector equality.
```

The runner-local reference recomputation (step 2) must:

```text
not call the frozen descriptor
not reuse descriptor implementation helpers
not import synthetic generator or freezer code
not use hashes as equality
not use floats
not sample orbit members
```

The independent full-orbit reference computation provides the observed side of each exhaustive comparison. Without that observed side, merely deriving and reserializing theorem expectations would not count as an executed nuisance control: an executed control requires an independently computed observation to compare against the derived expectation. The frozen descriptor itself remains directly evaluated only on G0, G1, G2, G3, and G4 for each admitted valid sequence, plus the actual original members used in every scientific positive-pair comparison. Memoization remains permitted only for byte-identical transformed raw sequences and must preserve full transformation multiplicity and coverage accounting.

Justification. A single frozen-descriptor evaluation is a full integer-exact 3906-entry third-order tensor (order 250,000 integer multiplications) plus a 32-unit affine canonicalization. Method A (direct descriptor evaluation of every one of the 4096 self-orbit members per admitted sequence, across the fixed fixture and eight frozen pairs and identity/nuisance controls) is on the order of 10^10–10^11 integer operations in pure Python and yields no assurance beyond Method B. Method B enumerates every group element and compares every expected vector/signature exactly — preserving coverage, multiplicity, and exact equality with no sampling policy — while directly evaluating the descriptor only on the stated generator set. This exactly preserves the specification's nuisance-orbit semantics (§8.1–§8.5) while avoiding an undeclared sampling policy.

Constraints on Method B:

```text
all 64 / 2048 / 4096 group elements must still be enumerated
all expected vectors/signatures must be compared exactly
the direct generator set is stated completely above (G0..G4); it is fixed
no random or result-dependent generator selection is allowed
no scientific positive-pair comparison may use derived output instead of the frozen
  descriptor's actual output on the original pair members
memoization is allowed only for byte-identical transformed raw sequences and must not
  change multiplicity or coverage accounting
```

### 11.5 Fixed positive fixture

The bound manifest's fixed fixture must be independently checked for:

```text
weight 9/9
full A2 equality
step-one transition-table equality
affine inequivalence certificate present and valid
affine-plus-complement inequivalence certificate present and valid
nonzero direct triple disagreement
```

Certificate information must not be passed into the descriptor. The required actual frozen-descriptor result, computed on the two original fixed-fixture members:

```text
affine-only signatures differ
affine-plus-complement signatures differ
classification = DECLARED_THIRD_ORDER_DISTINCTION_DETECTED
```

Failure is `SYNTHETIC_POSITIVE_CONTROL_FAILURE`.

### 11.6 Frozen eight-pair positive gate

For each of the eight accepted fixtures, in frozen order:

```text
validate both raw vectors
recompute lower-order signatures independently
require exact lower-order equality
require exact transition-table equality
compute both descriptors independently (frozen descriptor, actual output on the members)
compare exact affine-only signatures
compare exact affine-plus-complement signatures
attach fixture metadata only after comparison
```

Required:

```text
8 of 8 affine-plus-complement signature distinctions
```

Anything below `8 of 8` is `SYNTHETIC_POSITIVE_CONTROL_FAILURE`. No aggregate score, majority criterion, tolerance, or partial pass is allowed. Every positive comparison uses the frozen descriptor's actual output on the original pair members — never derived output.

---

## 12. Deterministic replay

The sole future authoritative invocation must run two fully fresh synthetic-validation passes. Each pass must freshly:

```text
load and verify the exact manifest
construct controls
run the complete gate
serialize its complete canonical pass bundle
```

The two complete canonical pass bundles are compared byte-for-byte:

```text
matches = true
mismatch_reasons = []
```

Any mismatch is `REPLAY_MISMATCH`. No third pass, retry, resume, or tie-breaker is permitted. Pass 2 must reuse no pass-1 object; both passes independently reload and re-verify the manifest and re-run the complete gate.

---

## 13. Canonical result states

Exactly three top-level scientific/integrity result kinds:

```text
SYNTHETIC_GATE_PASSED
SYNTHETIC_GATE_FAILED
SYNTHETIC_GATE_INVALID
```

Meaning:

```text
SYNTHETIC_GATE_PASSED =
  all malformed/degenerate controls correct
  all identity/nuisance controls correct
  fixed positive fixture distinguished
  8 of 8 frozen synthetic pairs distinguished
  exact replay match
  all boundaries and serialization valid

SYNTHETIC_GATE_FAILED =
  execution valid, but one or more preregistered negative or positive scientific
  controls fail

SYNTHETIC_GATE_INVALID =
  input identity, execution integrity, serialization, boundary, replay, or lower-order
  eligibility is invalid
```

A failed or invalid gate does not authorize descriptor modification, fixture removal, threshold changes, lag selection, normalization changes, or automatic rerun. A v0.1 failure is a valid negative result. Any future v0.2 must be separately specified and must not overwrite v0.1.

---

## 14. Ordered failure vocabulary

The existing exact 24-code vocabulary is used in its frozen order (the canonical ordering source is the descriptor module's `FAILURE_CODES`). Relevant S3 codes include:

```text
INPUT_LENGTH_INVALID
INPUT_ELEMENT_TYPE_INVALID
INPUT_BINARY_DOMAIN_INVALID
DEGENERATE_SEQUENCE
NORMALIZATION_INVALID
INTEGER_BOUND_INVARIANT_FAILURE
LOWER_ORDER_CONTROL_MISMATCH
ROTATION_INVARIANCE_FAILURE
REFLECTION_EQUIVARIANCE_FAILURE
AFFINE_EQUIVARIANCE_FAILURE
COMPLEMENT_ANTISYMMETRY_FAILURE
SELF_ORBIT_CANONICALIZATION_FAILURE
SYNTHETIC_NEGATIVE_CONTROL_FAILURE
SYNTHETIC_POSITIVE_CONTROL_FAILURE
FORBIDDEN_IMPORT_DETECTED
PROHIBITED_EVIDENCE_CONTACT_DETECTED
PRODUCTION_BOUNDARY_VIOLATION
SERIALIZATION_FAILURE
NONFINITE_DIAGNOSTIC
REPLAY_MISMATCH
FROZEN_INPUT_IDENTITY_MISMATCH
BENCHMARK_METADATA_LEAKAGE
UNAUTHORIZED_EXECUTION
```

Multiple failures must be emitted in canonical vocabulary order. No free-form exception text may replace canonical machine-readable codes.

`FROZEN_INPUT_IDENTITY_MISMATCH` is a relevant Stage S3 code. It applies to fail-closed mismatches involving the bound frozen synthetic input, including:

```text
wrong manifest path or unexpected input source
external manifest SHA-256 mismatch
manifest payload SHA-256 mismatch
freeze configuration identity mismatch
schema or family identity mismatch
family_frozen not true
wrong fixed-fixture count
wrong accepted-fixture count
raw fixture-vector identity or structure mismatch
```

Where the accepted-fixture order or structure differs from the bound manifest contract, the operation is classified as:

```text
SYNTHETIC_GATE_INVALID
failure_code = FROZEN_INPUT_IDENTITY_MISMATCH
```

`FROZEN_CANDIDATE_ORDER_MISMATCH` must not be repurposed for synthetic-fixture order. It remains candidate-specific and inactive in Stage S3 unless a later governing document explicitly broadens it. `BENCHMARK_METADATA_LEAKAGE`, if detected by an applicable boundary check, remains available under its frozen canonical meaning and is emitted rather than silently deferred. Only `FROZEN_CANDIDATE_ORDER_MISMATCH` remains reserved for later frozen-family stages; it is part of the frozen ordering but inactive here.

---

## 15. Reserved publication paths and write policy

Frozen future paths (created only during S3B execution, never by S3A):

```text
final directory   = research/brainvision/results/independent_order_sensitive_synthetic_validation_v0_1
staging directory = research/brainvision/results/.independent_order_sensitive_synthetic_validation_v0_1.staging
```

Exact future files:

```text
independent_order_sensitive_synthetic_validation_result_v0_1.json
independent_order_sensitive_synthetic_validation_execution_envelope_v0_1.json
independent_order_sensitive_synthetic_validation_summary_v0_1.txt
```

The runner must use:

```text
exclusive staging creation
exact file-set verification
close and re-read verification
SHA-256 verification
atomic staging-to-final promotion
no overwrite
no merge with existing output
```

S3A tests must not create these repository paths; all bounded-test output goes to operating-system temporary directories.

---

## 16. Bounded S3A tests

Authorize bounded tests using only:

```text
temporary directories
injected synthetic manifest bytes
neutral hand-built N=64 sequences
test doubles for source/Git identity checks where needed
small injected control plans
failure injection
```

The tests must not:

```text
open the real frozen manifest
evaluate the real fixed fixture
evaluate any of the real eight frozen pairs
run the authoritative CLI
create final or staging repository output paths
contact candidates 478/479/480
contact historical F3 or PsiTRS
```

Required bounded test categories:

```text
exact argv and stdin rejection
pre-contact refusal ordering
authority-consumption threshold
descriptor/test/runner identity verification
external and payload manifest hash validation
manifest schema and family_frozen validation
exact fixed-plus-eight structure validation
raw-vector-only descriptor calls
metadata attachment only after comparison
lower-order mismatch handling
identity-control classification
nuisance-control cardinality accounting
fixed-positive gate logic with injected fixtures
8-of-8 gate logic with injected fixtures
7-of-8 failure
negative-control failure
ordered failure codes
two-pass exact replay
replay mismatch
canonical JSON serialization
summary derivation
exclusive staging
atomic promotion
existing staging/final refusal
no rerun/resume path
static source-boundary validation
forbidden evidence-path protection
production/kernel/service isolation
```

Tests may use injected reduced control plans solely to test orchestration mechanics, but the authoritative runtime constants must remain frozen at:

```text
64 rotations
2048 affine relabelings
4096 affine-plus-complement self-orbit elements
fixed positive count = 1
generated positive count = 8
pass count = 2
```

Tests must prove the authoritative path cannot accept reduced values from CLI, environment, files, or injected runtime configuration: the frozen constants are internal module constants, and there is no CLI, environment, file, or stdin route to override them.

---

## 17. Static source-boundary requirements

The runner test must inspect the runner and descriptor source text and AST, and reject genuine executable routes involving:

```text
production imports
kernel imports
PsiTRS
historical F3
historical asymmetry audit
candidate 478/479/480 metadata
retained evidence paths
network
camera or screen capture
environment-supplied identities
unbounded subprocess routes
alternate manifest paths
alternate result paths
dynamic import of prohibited modules
```

Only narrowly bounded Git subprocess use is permitted, and only for committed-identity and repository-state verification (read-only Git commands frozen by S3B); no general subprocess facility, no caller-supplied command, and no mutating Git command. The checker must be bounded to genuine executable/source contact (imports, dynamic-import calls, attribute access, file/path/vocabulary literals in executable positions), must avoid self-triggering on its own prohibition vocabulary (sensitive markers assembled from fragments per the accepted self-boundary convention), and must preserve direct-literal and dynamic-route detection. The runner source and the frozen descriptor source must both pass the checker.

---

## 18. Authority state after this authorization

```text
CHALLENGER_DESCRIPTOR_IMPLEMENTATION_FROZEN = True
CHALLENGER_SYNTHETIC_VALIDATION_RUNNER_IMPLEMENTATION_AUTHORIZED = True
CHALLENGER_SYNTHETIC_VALIDATION_RUNNER_TEST_IMPLEMENTATION_AUTHORIZED = True
CHALLENGER_SYNTHETIC_VALIDATION_BOUNDED_TEST_EXECUTION_AUTHORIZED = True
```

Kept false:

```text
CHALLENGER_SYNTHETIC_VALIDATION_EXECUTION_AUTHORIZED = False
CHALLENGER_REAL_SYNTHETIC_MANIFEST_CONTACT_AUTHORIZED = False
CHALLENGER_FIXED_POSITIVE_FIXTURE_EVALUATION_AUTHORIZED = False
CHALLENGER_FROZEN_SYNTHETIC_FAMILY_EVALUATION_AUTHORIZED = False
CHALLENGER_SYNTHETIC_RESULT_PUBLICATION_AUTHORIZED = False
CHALLENGER_FROZEN_FAMILY_INPUT_ACCESS_AUTHORIZED = False
CHALLENGER_FROZEN_FAMILY_EVALUATION_AUTHORIZED = False
CHALLENGER_FROZEN_FAMILY_RERUN_AUTHORIZED = False
FROZEN_F3_CONTACT_AUTHORIZED = False
PSITRS_CONTACT_AUTHORIZED = False
PRERECORDED_CHALLENGER_BRIDGE_AUTHORIZED = False
PRODUCTION_INTEGRATION_AUTHORIZED = False
TORMENT_MEMORY_INTEGRATION_AUTHORIZED = False
KERNEL_MODIFICATION_AUTHORIZED = False
```

Permanent posture is preserved:

```text
FORMAL_HOLD = active
Mode_0 = active
STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY
```

Brainvision remains offline, quarantined, non-production, non-service, non-kernel, and non-memory-integrated. It must not be integrated into the production TORMENT memory system or kernel without a later explicit architectural discussion with Hilmir and his approval of the integration route.

---

## 19. Staging sequence

Recorded for orientation only; no step is triggered automatically, and nothing beyond S3A implementation and bounded testing is authorized here:

```text
1. commit this S3A authorization alone;
2. implement exactly the runner and runner-test allowlist;
3. run bounded injected-input tests only;
4. adversarially review code, control coverage, cost, and boundaries;
5. commit runner implementation;
6. record runner and runner-test Git/raw identities;
7. draft a separate S3B one-run execution authorization;
8. commit S3B authorization alone;
9. wait for Hilmir's separate explicit final invocation order;
10. execute once, capture exit code, and never rerun after manifest contact.
```

---

## 20. Final disposition

```text
A. SYNTHETIC-VALIDATION RUNNER IMPLEMENTATION AND BOUNDED, NON-AUTHORITATIVE
   TESTING AUTHORIZED, LIMITED TO EXACTLY TWO FILES, WITH METHOD B PREREGISTERED
   FOR THE EXHAUSTIVE NUISANCE CONTROLS. THE ACTUAL SYNTHETIC RUN, REAL MANIFEST
   CONTACT, FIXED-FIXTURE AND FROZEN-EIGHT-PAIR EVALUATION, AND RESULT PUBLICATION
   REMAIN CLOSED PENDING A SEPARATE STAGE S3B EXECUTION AUTHORIZATION AND A
   SEPARATE EXPLICIT INVOCATION ORDER FROM HILMIR.
```

*End — TORMENT Brainvision Independent Order-Sensitive Synthetic-Validation Runner Implementation Authorization v0.1. Docs-only, Stage S3A. Authorizes only future implementation and bounded, non-authoritative testing of the synthetic-validation runner across exactly two files (`research/brainvision/run_independent_order_sensitive_synthetic_validation_v0_1.py` and `research/brainvision/test_independent_order_sensitive_synthetic_fixtures_v0_1.py`). The frozen Stage S2 descriptor and its test are bound by identity and must not be modified. The real frozen synthetic manifest must not be opened, parsed, copied, hashed, imported, or evaluated during S3A; its path and hashes may appear only as frozen constants. Method B is preregistered for the exhaustive 64/2048/4096 nuisance controls, with the complete direct generator set {identity, translation-by-1, unit 3, unit 63, complement} and exact theorem-derived comparison over all group elements; every positive-pair comparison uses the frozen descriptor's actual output on the original members. No synthetic-validation execution, no manifest contact, no publication, and no F3/PsiTRS/production/service/memory/kernel contact are authorized. No runner or project function was executed and no Git command was run while preparing this document. FORMAL_HOLD and Mode_0 remain active; the frozen F3 result is neither amended nor reinterpreted.*

# TORMENT Brainvision Independent Order-Sensitive Descriptor Implementation Authorization v0.1

## Document status

```text
document_type = docs-only implementation authorization
authorization_stage = S2 (challenger implementation)
descriptor_id = n64-normalized-labeled-third-order-cyclic-correlation-v0.1
implementation_authorized = True (exactly the two-file allowlist below)
bounded_non_gating_test_execution_authorized = True
synthetic_validation_authorized = False
frozen_family_evaluation_authorized = False
runner_implementation_authorized = False
authoritative_execution_authorized = False
```

Authoritative repository baseline:

```text
branch = main
HEAD = origin/main = cae2f64
working tree = clean
commit subject = docs(research): record synthetic fixture freeze findings
Python = 3.11.15 (activated torment Conda environment)
```

This is Stage S2 only. It authorizes implementation and bounded, non-gating unit testing of the exact already-specified v0.1 descriptor, and nothing else. No runner or project function was executed while preparing it, and no Git command was run.

---

## 0. Decision

```text
A. IMPLEMENTATION AND BOUNDED, NON-GATING UNIT TESTING OF THE EXACT v0.1
   INDEPENDENT ORDER-SENSITIVE DESCRIPTOR ARE AUTHORIZED, LIMITED TO EXACTLY
   TWO FILES. SYNTHETIC VALIDATION, ANY FIXTURE/MANIFEST/FROZEN-FAMILY CONTACT,
   RUNNER IMPLEMENTATION, AND AUTHORITATIVE EXECUTION REMAIN CLOSED.
```

This document authorizes only the future creation and bounded testing of the descriptor module and its test module. It explicitly does not authorize, and withholds:

```text
synthetic validation execution
access to the frozen eight-fixture synthetic manifest by challenger code or tests
evaluation of the fixed homometric positive-control pair
evaluation of the frozen eight synthetic pairs
frozen N64/K=3 candidate access
candidate 478/479/480 evaluation
runner implementation
authoritative execution
result publication
historical F3 contact
PsiTRS contact
production, service, memory, or kernel contact
```

Completion or acceptance of this document does not advance authority automatically. Implementation becomes operational-as-code only after this authorization is committed alone, the two authorized files are implemented, bounded non-gating tests pass, and an adversarial review finds no blocker. Synthetic exposure requires the separate Stage S3 authorization.

---

## 1. Governing documents and completed prerequisites

Authoritative governing documents:

```text
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_DESCRIPTOR_CHALLENGER_SPECIFICATION_v0.1.md
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_FIXTURE_FREEZE_SPECIFICATION_v0.1.md
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_FIXTURE_FREEZE_FINDINGS_v0.1.md
```

The descriptor challenger specification is authoritative for the descriptor mathematics, the transformation laws, the canonical signatures, the lower-order control envelope, the deterministic serialization contract, the ordered failure vocabulary, and the staged-authorization policy (its Stage S2 defines the exact permitted scope). This document authorizes implementation of that specification without amendment; where any wording here appears looser than the specification, the specification governs.

Completed prerequisite state:

```text
S0 specification accepted (descriptor fixed as v0.1, no amendment)
S1 synthetic fixture family frozen and its findings recorded
INDEPENDENT_CHALLENGER_SPECIFIED = True
SYNTHETIC_FIXTURE_FAMILY_FROZEN = True
```

---

## 2. Reviewed repository baseline

This authorization was prepared against:

```text
branch = main
HEAD = origin/main = cae2f64
working tree = clean
commit subject = docs(research): record synthetic fixture freeze findings
Python = 3.11.15 (activated torment Conda environment)
```

The commit that carries this authorization must contain exactly one changed file and nothing else — the addition of this document at its path below. It must not create, modify, rename, or delete any source, test, result, evidence, configuration, or other documentation file.

---

## 3. Prerequisite freeze state and identities (record-only)

The completed freeze state, recorded as prerequisite context only:

```text
family_frozen = true
canonical_result_kind = ACCEPTED_EIGHT
comparison_status = MATCH
one-run freezer authority = consumed
freezer rerun authorized = false
```

Published synthetic-manifest identities, recorded only as prerequisite identities:

```text
external_manifest_sha256  = 05ce02af1c1a4b508e9a6566c9ff638849039df5caa45479858e634e2a117404
manifest_payload_sha256   = 56a141bd13937caa6ac800ab8c9c12229f6bf75ee97ab490a26844664a65b4b9
configuration_sha256      = 5f3a568bc4286136a93d9b9bac74985af4b68202373a56210eddbcfbf2625263
```

These identities are recorded for provenance only. Stage S2 code and tests must not open, parse, import, copy, read, or evaluate the published manifest, its payload, its configuration, or any of its bytes. The identities above must not be embedded into, referenced by, or consumed by the descriptor module or its tests. They exist in this authorization solely to document the prerequisite that the synthetic family is frozen.

---

## 4. Exact Stage S2 implementation allowlist

Exactly two future files are authorized for creation or modification, and no others:

```text
research/brainvision/independent_order_sensitive_descriptor_v0_1.py
research/brainvision/test_independent_order_sensitive_descriptor_v0_1.py
```

No third helper file is authorized. In particular, the following are NOT authorized for creation:

```text
generate_independent_order_sensitive_synthetic_fixtures_v0_1.py
run_independent_order_sensitive_synthetic_validation_v0_1.py
run_independent_order_sensitive_frozen_n64_evaluation_v0_1.py
fixture adapters
manifest readers
result writers
CLI runners
execution envelopes
authorization gates
output directories
```

Neither authorized file may contain a CLI or an authoritative runner. Neither may perform module-level fixture evaluation or expensive execution at import time.

---

## 5. Exact descriptor implementation contract

The descriptor module must implement the accepted specification (§4–§6) without amendment.

Identity and input contract:

```text
descriptor_id = n64-normalized-labeled-third-order-cyclic-correlation-v0.1
N = 64
input = exactly 64 strict integers in {0,1}
bool is rejected (Python bool is not accepted as a binary element)
constant (degenerate) sequences are rejected
```

Integer centering and tensor:

```text
w = sum(x_i)
z_i = 64*x_i - w                       (exact integers; sum(z_i) = 0)
T_x(a,b) = sum_i z_i * z_(i+a mod 64) * z_(i+b mod 64)
```

Lag domain (fixed lexicographic order):

```text
all ordered (a,b) with a in 1..63, b in 1..63, a != b
entry_count = 3906
lag_domain_id = n64-distinct-position-ordered-lag-pairs-lexicographic-v0.1
```

Normalization and exact rational representation:

```text
D_x = sum_i abs(z_i)^3            (positive for every admitted nonconstant sequence)
normalization = exact rational only
integer-bound invariant checked as abs(T_x(a,b)) <= D_x   (integer cross-multiplication)
canonical common-denominator reduction:
  g_x = gcd(D_x, abs(T_x(a,b)) for every (a,b))   (zero entries contribute zero)
  canonical_denominator = D_x / g_x
  canonical_numerator(a,b) = T_x(a,b) / g_x
primary equality = exact denominator-and-vector equality
```

No float may enter descriptor computation, normalization, canonical reduction, orbit comparison, signature equality, or classification. Floating-point conversion is prohibited for equality, orbit comparison, canonicalization, and classification.

### 5.1 Required canonical signatures

Implement exactly three, per §6:

```text
raw labeled 3906-entry numerator vector (in fixed L3 order), with the positive
  canonical_denominator serialized separately

affine-only canonical signature = ( canonical_denominator,
  lexicographic minimum over the 32 units u in U_64 of the relabeled numerator vector )

affine-plus-complement canonical signature = ( canonical_denominator,
  lexicographic minimum over u in U_64 and s in {-1,+1} of s * relabeled numerator vector )
```

Transformation-law obligations (implemented and, in §10, tested):

```text
translation is eliminated by cyclic invariance (rotation: T unchanged)
reflection remains an explicit transformation test even though -1 is a unit:
  T_reflected(a,b) = T_original(-a mod 64, -b mod 64)
affine relabeling: T_(g_(u,v)x)(a,b) = T_x(u^-1*a mod 64, u^-1*b mod 64)
complement exact antisymmetry:
  z_complement_i = -z_i
  D_complement = D_original
  T_complement(a,b) = -T_original(a,b)
  affine-plus-complement signature unchanged under complement
```

Hashes (e.g. SHA-256) may be emitted for transport/identity only. Exact signature equality (denominator-and-vector) must never be replaced by hash equality, and a hash-collision assumption must never substitute for exact vector comparison.

No learned or selected compression is admitted: no lag subsets, top-k, PCA, learned projections, trained classifiers, thresholding, binning, rank-only reduction, summary-statistic-only comparison, or frozen-family/certificate-selected coordinates.

---

## 6. Pure-implementation boundary

The primary descriptor module must be:

```text
standard-library only
pure after input delivery
deterministic
integer-exact
import-inert
filesystem-independent
environment-independent
service-disconnected
network-disconnected
```

The primary descriptor module must not:

```text
read files
write files
read environment variables
invoke subprocesses
inspect Git
import project production modules
accept paths
accept candidate IDs
accept pair labels
accept support certificates
accept precomputed autocorrelation
accept triple disagreement counts
accept benchmark metadata
```

The public descriptor function must receive only a raw binary sequence and fixed constants internal to the implementation. It must not receive, and must not be reachable through, any fixture, manifest, candidate metadata, or precomputed diagnostic. No module-level fixture evaluation or expensive execution is permitted at import time; importing the module must be inert.

---

## 7. Canonical serialization contract

Implement the exact deterministic per-sequence payload contract from the specification (§10). Serialization functions may return bytes but must not write them to disk in Stage S2.

Encoding:

```text
UTF-8
no BOM
LF
one terminal LF
compact separators
base-10 integers
no NaN
no Infinity
no negative zero
JSON literals true / false / null only
stable exact key order
stable lag order (fixed L3)
stable failure-code order
```

Top-level fields in exactly this order (no additional field permitted):

```text
schema
descriptor_id
N
weight
lag_domain_id
entry_count
canonical_denominator
raw_labeled_numerators
affine_canonical_numerators
affine_complement_canonical_numerators
lower_order_signature
transition_table
validation
ordered_failure_codes
```

Fixed constants:

```text
schema = torment-brainvision-independent-order-sensitive-descriptor-result-v0.1
descriptor_id = n64-normalized-labeled-third-order-cyclic-correlation-v0.1
N = 64
lag_domain_id = n64-distinct-position-ordered-lag-pairs-lexicographic-v0.1
entry_count = 3906
```

Nested key order is fixed: `lower_order_signature` = { N, weight, A2 }; `validation` = { valid, failure_code, failure_stage, detail }; `transition_table` = [[n00,n01],[n10,n11]]. First-failure per-sequence validation order (input length → element type → binary domain → degenerate → normalization validity → integer-bound invariant) is preserved. The payload SHA-256, if emitted, is over the complete canonical UTF-8 JSON bytes including the single terminal LF, and is transport identity only.

---

## 8. Lower-order diagnostics

Computed independently from the raw input (never supplied as descriptor inputs), per §7:

```text
N
weight w
A2(d) for d = 0..63    (exact periodic second-order autocorrelation)
step-one 2x2 transition table
```

These diagnostics are emitted in the payload (`lower_order_signature`, `transition_table`) but are derived internally from the raw sequence, not accepted as arguments. Pair comparison, matched lower-order eligibility, and synthetic-gate classification are not Stage S2 responsibilities and must not be implemented here.

---

## 9. Ordered failure vocabulary

The implementation must preserve the exact specification ordering as the canonical ordering source:

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
FROZEN_CANDIDATE_ORDER_MISMATCH
FROZEN_INPUT_IDENTITY_MISMATCH
BENCHMARK_METADATA_LEAKAGE
UNAUTHORIZED_EXECUTION
```

The Stage S2 implementation may expose only the codes relevant to Stage S2 operations (per-sequence input, normalization, invariant, serialization, and static-boundary codes), but it must retain the full ordered vocabulary above as the single canonical ordering source. Codes tied to pair/family/replay/publication/execution belong to later stages and must not be exercised as live gate outcomes here.

---

## 10. Bounded Stage S2 tests

Authorize bounded unit tests that prove implementation mechanics without exposing preregistered gate outcomes.

Allowed test inputs:

```text
malformed values
degenerate sequences
small hand-constructed N=64 binary sequences
deterministically generated neutral sequences not taken from the frozen manifest
identity copies
rotations
reflections
affine relabelings
complements
```

Required test categories:

```text
strict input validation
bool rejection
degenerate rejection
3906-entry ordering
exact integer tensor calculation
normalization positivity
integer bound invariant
common-denominator reduction
lower-order diagnostics
rotation invariance
reflection lag mapping
affine lag permutation
complement antisymmetry
affine-only canonicalization
affine-plus-complement canonicalization
self-orbit collapse
exact deterministic replay
canonical JSON byte stability
static forbidden-import and prohibited-vocabulary checks
import inertness
no filesystem/environment/subprocess/network behavior
```

Tests may use direct independent reference calculations (recomputing the tensor, the autocorrelation, or a canonicalization by an independent route and asserting exact integer equality).

Tests must not evaluate:

```text
the fixed C={0,25,55}, D={0,49,57} positive fixture
any of the eight frozen synthetic pairs
the published synthetic manifest
historical candidates 478, 479, or 480
historical F3 evidence
```

The reason is methodological: the implementation identity must be frozen before the synthetic gate is exposed. No synthetic success or failure may be learned during Stage S2. Tests are bounded and non-gating — they prove mechanics (exact arithmetic, invariance/equivariance laws, canonicalization, serialization stability, boundary hygiene), never preregistered synthetic or frozen-family outcomes.

---

## 11. Static source-boundary checks

The test file must inspect the authorized source text and reject:

```text
prohibited imports (torment_service, PsiTRS modules, F3 evaluator, F3 asymmetry analyzer)
dynamic import routes targeting prohibited modules
filesystem reads
environment reads
subprocess use
network use
production-module references
historical F3 references
PsiTRS references
frozen-manifest paths
candidate metadata
```

The checker must be bounded to genuine executable/source contact (imports, dynamic-import calls, attribute access, path/vocabulary literals in executable positions). It must avoid false positives caused solely by prohibition vocabulary appearing inside the checker's own test declarations — that is, the test's own marker strings, assembled from fragments where necessary, must not trip the boundary scan, exactly as in the accepted freeze-library/test convention. The descriptor module must remain self-clean under this scan.

Runtime enforcement for later synthetic execution (an execution-time boundary gate, envelope, and one-run consumption) belongs to the separately authorized Stage S3 runner and is not authorized here.

---

## 12. Explicitly withheld authority

The following remain unauthorized. This document opens none of them:

```text
synthetic validation execution
challenger access to the frozen eight-fixture synthetic manifest (open/parse/import/copy/evaluate)
evaluation of the fixed homometric positive-control pair
evaluation of the frozen eight synthetic pairs
frozen N64/K=3 candidate access
candidate 478/479/480 evaluation
runner implementation
authoritative execution
result publication
historical F3 contact
PsiTRS contact
production, service, memory, or kernel contact
```

Never modify, import, instantiate, wrap, call, or route through:

```text
torment_service/kernel/
torment_service/memory_kernel.py
torment_service/fabric.py
SRG
TriOctaMemoryKernel
PsiTRS
historical F3 evaluator
historical F3 asymmetry analyzer
production memory or model surfaces
network services
camera, screen capture, or sensors
```

---

## 13. Permanent Brainvision and TORMENT boundary

Preserved permanently:

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

This descriptor implementation is independent, descriptor-blind-of-outcome research infrastructure. It does not amend, rescue, rerun, weaken, replace, or reinterpret the frozen historical F3 result, and it does not observe any frozen-family or synthetic-gate outcome. Brainvision must not be integrated into the production TORMENT memory system or kernel without a later explicit architectural discussion with Hilmir and his approval of the integration route.

---

## 14. Authority state after this authorization

```text
INDEPENDENT_CHALLENGER_SPECIFIED = True
SYNTHETIC_FIXTURE_FAMILY_FROZEN = True

CHALLENGER_DESCRIPTOR_IMPLEMENTATION_AUTHORIZED = True
CHALLENGER_DESCRIPTOR_TEST_IMPLEMENTATION_AUTHORIZED = True
CHALLENGER_BOUNDED_NON_GATING_TEST_EXECUTION_AUTHORIZED = True
```

Everything below remains false:

```text
CHALLENGER_SYNTHETIC_VALIDATION_AUTHORIZED = False
CHALLENGER_FIXED_POSITIVE_FIXTURE_ACCESS_AUTHORIZED = False
CHALLENGER_FROZEN_SYNTHETIC_MANIFEST_ACCESS_AUTHORIZED = False
CHALLENGER_FROZEN_SYNTHETIC_FAMILY_EVALUATION_AUTHORIZED = False
CHALLENGER_FROZEN_FAMILY_INPUT_ACCESS_AUTHORIZED = False
CHALLENGER_FROZEN_FAMILY_EVALUATION_AUTHORIZED = False
CHALLENGER_FROZEN_FAMILY_RERUN_AUTHORIZED = False
CHALLENGER_RUNNER_IMPLEMENTATION_AUTHORIZED = False
CHALLENGER_RESULT_PUBLICATION_AUTHORIZED = False
FROZEN_F3_CONTACT_AUTHORIZED = False
PSITRS_CONTACT_AUTHORIZED = False
PRERECORDED_CHALLENGER_BRIDGE_AUTHORIZED = False
PRODUCTION_INTEGRATION_AUTHORIZED = False
TORMENT_MEMORY_INTEGRATION_AUTHORIZED = False
KERNEL_MODIFICATION_AUTHORIZED = False
```

---

## 15. Staging sequence after acceptance

The next intended sequence is stated for orientation only; this document does not authorize any step beyond Stage S2 implementation and bounded non-gating testing, and none of the steps below is triggered automatically:

```text
1. commit the S2 authorization alone;
2. implement the exact two-file allowlist;
3. run only bounded non-gating tests;
4. adversarially review implementation and boundaries;
5. commit implementation and record Git/raw identities;
6. draft a separate Stage S3 synthetic-validation runner and execution authorization;
7. only then expose the fixed positive fixture and frozen eight-pair family to the frozen implementation.
```

No source modification is permitted after a successful Stage S3 synthetic gate unless a later docs-only adjudication explicitly handles an integrity defect without tuning against results. The implementation identity must be frozen before the synthetic gate is exposed; any change after synthetic exposure follows the specification's Stage S5 no-tuning discipline.

---

## 16. Final disposition

```text
A. DESCRIPTOR IMPLEMENTATION AND BOUNDED NON-GATING TESTING AUTHORIZED,
   LIMITED TO EXACTLY TWO FILES. SYNTHETIC VALIDATION, FIXTURE/MANIFEST/
   FROZEN-FAMILY CONTACT, RUNNER IMPLEMENTATION, AND AUTHORITATIVE EXECUTION
   REMAIN CLOSED PENDING SEPARATE STAGE S3+ AUTHORIZATION.
```

*End — TORMENT Brainvision Independent Order-Sensitive Descriptor Implementation Authorization v0.1. Docs-only, Stage S2. Authorizes only the future implementation and bounded, non-gating unit testing of the exact v0.1 descriptor across exactly two files (`research/brainvision/independent_order_sensitive_descriptor_v0_1.py` and its test). No synthetic validation, no fixed-positive-fixture or frozen-eight-pair or published-manifest contact, no frozen N64/K=3 or candidate 478/479/480 access, no runner, no authoritative execution, no result publication, no F3/PsiTRS/production/service/memory/kernel contact. The frozen synthetic-manifest identities are recorded for provenance only and must not be opened, parsed, imported, copied, or evaluated by Stage S2 code or tests. No runner or project function was executed and no Git command was run while preparing this document. FORMAL_HOLD and Mode_0 remain active; the frozen F3 result is neither amended nor reinterpreted.*

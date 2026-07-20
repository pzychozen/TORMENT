# TORMENT Brainvision Independent Order-Sensitive Descriptor Challenger Specification v0.1

## Document status

```text
document_type = docs-only specification
specification_version = v0.1
implementation_authorized = False
execution_authorized = False
synthetic_validation_authorized = False
frozen_family_evaluation_authorized = False
production_contact_authorized = False
```

Authoritative repository baseline:

```text
abf138f0a5b5287090fa183cca908e020f45e086
```

Recommended path:

```text
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_DESCRIPTOR_CHALLENGER_SPECIFICATION_v0.1.md
```

This document specifies a new, independent Brainvision research branch:

```text
INDEPENDENT ORDER-SENSITIVE DESCRIPTOR CHALLENGER v0.1
```

It does not authorize implementation, testing, execution, evidence modification, production integration, or contact with the frozen N64 benchmark.

## 0. Fixed authority and historical disposition

The completed frozen N64/K=3 F3 result remains permanently:

```text
STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY
```

The completed read-only F3 asymmetry audit remains descriptive only and has the fixed family disposition:

```text
B. BLOCKING SELF-ORBIT ELEVATION IS BROAD
```

Nothing in this challenger branch may:

```text
amend the F3 verdict
weaken the F3 verdict
reinterpret the F3 verdict
rescue the F3 descriptor
replace the F3 evaluation
rerun the F3 evaluator
rerun the F3 asymmetry analyzer
modify retained F3 evidence
use retained F3 responses as challenger features
use the asymmetry-audit output as challenger input
```

The following historical authority state remains closed:

```text
F3_EVALUATION_COMPLETE = True
F3_RERUN_AUTHORIZED = False

READ_ONLY_ASYMMETRY_AUDIT_EXECUTION_AUTHORIZED = consumed
READ_ONLY_ASYMMETRY_AUDIT_COMPLETED = True
READ_ONLY_ASYMMETRY_AUDIT_VALID = True
READ_ONLY_ASYMMETRY_AUDIT_RERUN_AUTHORIZED = False

PSITRS_CONTACT_AUTHORIZED = False
DESCRIPTOR_RECOMPUTATION_AUTHORIZED = False
RETAINED_EVIDENCE_MODIFICATION_AUTHORIZED = False
PRODUCTION_INTEGRATION_AUTHORIZED = False
KERNEL_MODIFICATION_AUTHORIZED = False
```

A future success by the independent challenger would be a result about the new descriptor only. It would not retroactively change the completed F3 result.

`FORMAL_HOLD` remains active.

`Mode_0` remains active.

## 1. Research question

The branch asks exactly:

Can a separately specified, service-disconnected, explicitly order-sensitive descriptor distinguish declared higher-order structure in controlled binary cyclic sequences whose admitted lower-order invariants are matched?

After independent synthetic validation, a later separately authorized evaluation may ask:

Does the frozen N64/K=3 benchmark family produce distinct challenger descriptors after quotienting the declared nuisance transformations?

The branch does not ask whether PsiTRS can be repaired.

The branch does not compare the challenger's numerical scale with F3 responses.

The branch does not use F3 outcomes to select lags, weights, thresholds, transforms, normalizations, or success criteria.

### 1.1 Meaning and limitation of independence

The word independent means independent from PsiTRS, the historical F3 implementation, retained F3 responses, runtime certificate leakage, production services, and post-result v0.1 tuning.

It does not mean benchmark-blind descriptor discovery.

The v0.1 descriptor family is benchmark-aware. It was selected with prior knowledge that the frozen benchmark witnesses have declared labeled third-order or triple-count certificate disagreements while matching the admitted lower-order controls.

The exact descriptor definition, normalization, lag domain, nuisance quotient, synthetic gate, frozen-family criterion, and failure language are nevertheless preregistered before any v0.1 challenger contact with the frozen family.

Any future success may therefore be reported only as a preregistered benchmark-aware third-order descriptor check on the exact tested family.

It must not be reported as:

```text
benchmark-blind discovery
a rescue or amendment of F3
evidence that PsiTRS was nearly correct
an independently discovered property of the frozen witnesses
general order understanding
```

## 2. Immutable isolation boundary

All future challenger code must remain under:

```text
research/brainvision/
```

The challenger must never modify, import, instantiate, wrap, call, or route through:

```text
torment_service/kernel/
torment_service/memory_kernel.py
torment_service/fabric.py
SRG
TriOctaMemoryKernel
PsiTRS
the historical F3 evaluator
the historical F3 asymmetry analyzer
```

The challenger must not contact:

```text
production memory
prompt construction
model context
identity
actions
tools
live models
network services
camera capture
runtime video capture
screen capture
sensors
service endpoints
production configuration
```

The primary descriptor implementation must be:

```text
offline
pure
deterministic
integer-exact
service-disconnected
filesystem-independent after input delivery
non-production
non-live
non-authoritative
```

The descriptor function must accept only a raw binary sequence and fixed specification constants.

It must not receive a candidate number, pair label, certificate object, file path, F3 response, or benchmark metadata.

## 3. Exact input contract

### 3.1 Mathematical domain

The descriptor domain is:

```text
x : Z_64 -> {0, 1}
```

represented as an ordered sequence:

```text
x = [x_0, x_1, ..., x_63]
```

Requirements:

```text
length(x) = 64
type(x_i) = integer
x_i in {0, 1}
bool values are not accepted as integers
```

Constant sequences are outside the admitted descriptor domain:

```text
sum(x) not in {0, 64}
```

A constant sequence must produce a deterministic validation failure and no descriptor.

### 3.2 Frozen benchmark order

A future frozen-family adapter must preserve exactly:

```text
candidate order = [478, 479, 480]
```

Each candidate contains two raw binary cyclic sequences.

Inside the descriptor path, the two sequences must be represented only as:

```text
slot_0
slot_1
```

The descriptor must not receive or infer semantic `A` and `B` labels.

The candidate number may be attached to the final report only after both descriptors have been computed and serialized.

### 3.3 Prohibited descriptor inputs

The descriptor must not read or receive:

```text
candidate index
stored certificate verdict
known A/B label
accepted support list
precomputed disagreement count
precomputed autocorrelation
precomputed triple array
F3 response
F3 payload
asymmetry-audit classification
blocking-class count
historical evaluation verdict
```

A raw support list is not an admitted descriptor input.

An evaluation adapter may materialize an independently validated 64-entry binary vector before descriptor invocation, but the descriptor itself must receive only that vector.

## 4. Exact descriptor choice

The v0.1 challenger is fixed as:

```text
N64 normalized labeled nondegenerate third-order cyclic correlation tensor
```

Descriptor identifier:

```text
n64-normalized-labeled-third-order-cyclic-correlation-v0.1
```

No alternative descriptor, bispectral variant, lag subset, learned projection, threshold, weighting scheme, or dimensionality reduction is admitted under v0.1.

### 4.1 Weight and integer centering

Let:

```text
N = 64
w = sum(x_i)
```

Define the integer-centered sequence:

```text
z_i = N * x_i - w
```

Therefore:

```text
sum(z_i) = 0
```

The values of `z_i` are exact integers.

No floating-point centering is permitted in the primary descriptor path.

### 4.2 Nondegenerate labeled lag domain

Define:

```text
L3 = {
    (a, b) in Z_64 x Z_64
    such that
    a != 0,
    b != 0,
    a != b
}
```

The ordered serialization of `L3` is lexicographic:

```text
a = 1, 2, ..., 63
b = 1, 2, ..., 63
omit b = a
```

The resulting primary tensor has:

```text
63 * 62 = 3906
```

labeled entries.

The lag pair is ordered and retained as labeled information.

No lag may be selected or removed after observing any frozen-family result.

### 4.3 Third-order cyclic numerator

For each `(a, b) in L3`, define:

```text
T_x(a, b) =
    sum over i in Z_64 of
    z_i * z_(i+a mod 64) * z_(i+b mod 64)
```

`T_x(a,b)` must be computed with exact integer arithmetic.

### 4.4 Exact normalization

Define the positive normalization denominator:

```text
D_x =
    sum over i in Z_64 of abs(z_i)^3
```

For every admitted nonconstant sequence:

```text
D_x > 0
```

The normalized labeled tensor entry is:

```text
C_x(a, b) = T_x(a, b) / D_x
```

The primary representation must remain rational and exact.

Floating-point conversion is not permitted for equality, orbit comparison, canonicalization, or scientific classification.

By Hölder's inequality:

```text
abs(C_x(a, b)) <= 1
```

This bound must be checked as an implementation invariant using integer cross-multiplication:

```text
abs(T_x(a, b)) <= D_x
```

### 4.5 Canonical common-denominator representation

Let:

```text
g_x = gcd(
    D_x,
    abs(T_x(a,b)) for every (a,b) in L3
)
```

with the ordinary convention that zero tensor entries contribute zero to the `gcd`.

Define:

```text
canonical_denominator = D_x / g_x
canonical_numerator(a,b) = T_x(a,b) / g_x
```

The descriptor payload therefore contains:

```text
one positive integer denominator
3906 exact integer numerators
the fixed lexicographic lag ordering
```

This reduction is representational only. It must not change the descriptor's mathematical value.

### 4.6 Why this is beyond second order

Define the exact periodic second-order autocorrelation:

```text
A2_x(d) =
    sum over i in Z_64 of
    x_i * x_(i+d mod 64)
```

Define the direct labeled triple count:

```text
M3_x(a,b) =
    sum over i in Z_64 of
    x_i * x_(i+a mod 64) * x_(i+b mod 64)
```

The challenger numerator satisfies the exact identity:

```text
T_x(a,b)
=
N^3 * M3_x(a,b)
-
N^2 * w * (
    A2_x(a)
    + A2_x(b)
    + A2_x(b-a mod N)
)
+
2 * N * w^3
```

Therefore, for two sequences with identical `w` and identical full `A2` vectors:

```text
T_x(a,b) - T_y(a,b)
=
N^3 * (
    M3_x(a,b) - M3_y(a,b)
)
```

A difference in the challenger tensor under matched lower-order controls is consequently an exact labeled third-order distinction.

No claim beyond that identity is authorized.

## 5. Transformation laws and nuisance orbit

### 5.1 Affine relabeling

Let:

```text
U_64 = {u in Z_64 : gcd(u,64) = 1}
```

`U_64` contains the 32 odd residues modulo 64.

For:

```text
u in U_64
v in Z_64
```

define the affine-relabelled sequence:

```text
(g_(u,v) x)_j =
    x_(u^-1 * (j-v) mod 64)
```

This maps a support `S` to:

```text
uS + v
```

The exact tensor transformation law is:

```text
T_(g_(u,v)x)(a,b)
=
T_x(u^-1*a mod 64, u^-1*b mod 64)
```

Translation `v` disappears from the tensor because the descriptor is cyclically translation invariant.

### 5.2 Rotation

A rotation by `r` is:

```text
u = 1
v = r
```

For every rotation:

```text
T_rotated(a,b) = T_original(a,b)
```

The raw tensor must be exactly rotation invariant.

### 5.3 Reflection

Reflection is represented by:

```text
u = -1 mod 64
v = 0
```

The required transformation law is:

```text
T_reflected(a,b)
=
T_original(-a mod 64, -b mod 64)
```

Reflection remains an explicit test category even though `-1` is already a unit in `U_64`.

### 5.4 Complement

Define:

```text
complement(x)_i = 1 - x_i
```

Then:

```text
z_complement_i = -z_i
D_complement = D_x
T_complement(a,b) = -T_x(a,b)
```

Complement is therefore exact antisymmetry, not ordinary raw-tensor invariance.

Complement quotienting is used only where the declared benchmark equivalence relation admits complement.

The frozen N64 family was certified under affine and affine-plus-complement checks. A future frozen-family challenger report must therefore emit both:

```text
affine-only canonical signature
affine-plus-complement canonical signature
```

The family-level primary comparison must use the affine-plus-complement signature.

## 6. Exact canonical signatures

### 6.1 Raw labeled vector

Let `V_x` be the 3906-entry canonical numerator vector in the fixed lag order.

The positive canonical denominator is serialized separately.

### 6.2 Affine-only signature

For every `u in U_64`, form:

```text
V_(x,u)[a,b]
=
canonical_numerator_x(
    u^-1*a mod 64,
    u^-1*b mod 64
)
```

The affine-only canonical vector is the lexicographically smallest vector across all 32 units:

```text
V_affine(x) =
    lexicographic_minimum over u in U_64 of V_(x,u)
```

The exact affine-only signature is:

```text
(
    canonical_denominator,
    V_affine(x)
)
```

### 6.3 Affine-plus-complement signature

For every:

```text
u in U_64
s in {-1, +1}
```

form:

```text
s * V_(x,u)
```

The affine-plus-complement canonical vector is:

```text
V_affine_complement(x)
=
lexicographic_minimum over
u in U_64 and s in {-1,+1}
of s * V_(x,u)
```

The exact affine-plus-complement signature is:

```text
(
    canonical_denominator,
    V_affine_complement(x)
)
```

A hash may be emitted for identity and transport checking, but scientific equality must be established by exact denominator-and-vector equality.

A SHA-256 collision assumption must never substitute for exact vector comparison.

### 6.4 No learned or selected compression

The canonicalization above is the only admitted v0.1 compression.

The following are prohibited:

```text
selected lag subsets
top-k entries
PCA
learned projections
trained classifiers
random mappings
thresholding
binning
rank-only reduction
summary-statistic-only comparison
frozen-family-selected coordinates
certificate-selected coordinates
```

## 7. Lower-order control envelope

For every proposed comparison pair, compute independently from the raw sequences:

```text
N
binary-domain validity
support weight w
full A2(d) vector for d = 0..63
step-one 2x2 transition table
```

Define:

```text
L2(x) =
(
    N,
    w,
    A2_x(0),
    A2_x(1),
    ...,
    A2_x(63)
)
```

A comparison is admitted as a matched lower-order comparison only when:

```text
L2(slot_0) = L2(slot_1)
```

The step-one transition table must also match exactly as a redundant diagnostic.

A lower-order mismatch makes the pair ineligible. It must not be reclassified as challenger success or challenger failure.

No tolerance is permitted.

No floating-point comparison is permitted.

## 8. Required control classes

### 8.1 Rotation controls

For every synthetic validation fixture, test all:

```text
64 rotations
```

Requirements:

```text
raw tensor unchanged
normalization unchanged
affine signature unchanged
affine-plus-complement signature unchanged
serialized canonical payload unchanged
```

### 8.2 Reflection controls

For every synthetic validation fixture, test reflection explicitly.

Requirements:

```text
raw tensor obeys the exact reflected lag map
both canonical signatures remain unchanged
```

### 8.3 Affine relabeling controls

For every synthetic validation fixture, test exhaustively:

```text
32 units * 64 translations = 2048 affine relabelings
```

Requirements:

```text
raw tensor obeys the induced lag permutation
affine-only canonical signature remains unchanged
affine-plus-complement canonical signature remains unchanged
```

### 8.4 Complement controls

For every admitted nonconstant synthetic fixture:

```text
D_complement = D_original
T_complement = -T_original
affine-plus-complement signature unchanged
```

The affine-only signature is not required to equal the original affine-only signature.

### 8.5 Self-orbit controls

A sequence and every sequence in its declared affine nuisance orbit must collapse to the same applicable canonical signature.

Where complement is admitted, the exhaustive self-orbit contains:

```text
2048 affine relabelings
plus their 2048 complements
=
4096 transformed inputs
```

No member of a self-orbit may be reported as a positive distinction from its source.

### 8.6 Exact deterministic replay

Identical raw input must produce byte-identical canonical output across repeated clean invocations.

Required replay checks include:

```text
exact payload equality
exact SHA-256 equality
stable entry ordering
stable line endings
stable integer formatting
stable failure-code ordering
```

## 9. Synthetic validation fixtures

Frozen-family contact is prohibited until the complete synthetic gate has passed and been committed separately.

### 9.1 Malformed and degenerate fixtures

The validation suite must include:

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

Each fixture must produce its exact specified failure code and no descriptor payload.

### 9.2 Identity negative control

For each valid fixture `x`, compare:

```text
x against an exact independent copy of x
```

Required result:

```text
raw descriptors equal
affine-only signatures equal
affine-plus-complement signatures equal
classification = NO_DECLARED_DISTINCTION
```

### 9.3 Nuisance-equivalent negative controls

For every valid fixture, compare it against selected and exhaustive members of its rotation, reflection, affine, and admissible complement orbit.

Required result:

```text
canonical signatures equal
classification = NUISANCE_ORBIT_EQUIVALENT
```

Any reported distinction is a synthetic negative-control failure.

### 9.4 Fixed homometric positive fixture

The following fixed construction is admitted as an implementation-validation fixture independent of the frozen K=3 family.

Define:

```text
C = {0, 25, 55}
D = {0, 49, 57}
```

Construct on `Z_64`:

```text
H0 = C + D
H1 = C - D
```

The resulting supports are:

```text
H0 = {0, 10, 18, 25, 40, 48, 49, 55, 57}

H1 = {0, 6, 7, 15, 25, 32, 40, 55, 62}
```

Required independently checked properties:

```text
weight(H0) = weight(H1) = 9
full periodic second-order autocorrelation vectors are equal
step-one transition tables are equal
the pair is not affine equivalent
the pair is not affine-plus-complement equivalent
the direct labeled triple-count arrays differ
```

The direct nondegenerate triple-count arrays differ at:

```text
288 of 3906 labeled lag pairs
```

This disagreement count is a fixture certificate only.

It must not be supplied to the challenger implementation.

During Stage S1, all listed fixed-fixture certificates, including the exact `288 of 3906` disagreement count, must be independently recomputed from the raw supports by fixture-verification code that does not import or call the challenger descriptor.

A mismatch in any listed certificate blocks synthetic fixture freezing.

The certificate value in this specification is not treated as verified merely because it appears in this docs-only document.

Required challenger result:

```text
affine-only signatures differ
affine-plus-complement signatures differ
classification = DECLARED_THIRD_ORDER_DISTINCTION_DETECTED
```

### 9.5 Independently generated homometric controls

Before challenger implementation is evaluated, a separate deterministic fixture-generation specification must freeze at least:

```text
K_synthetic = 8
```

unique homometric positive-control pairs.

The generator must operate without importing the challenger descriptor.

The admitted construction family is:

```text
C = {0, c1, c2}
D = {0, d1, d2}

A = sorted ascending tuple of distinct residues
    {(c+d) mod 64 : c in C, d in D}

B = sorted ascending tuple of distinct residues
    {(c-d) mod 64 : c in C, d in D}
```

Collisions are collapsed by set construction before cardinality checks.

Seed tuples are enumerated by exact nested lexicographic order:

```text
c1 increasing
then c2 increasing
then d1 increasing
then d2 increasing
```

subject to:

```text
1 <= c1 < c2 <= 63
1 <= d1 < d2 <= 63
```

For a support `S`, define its binary sequence by:

```text
binary(S)_i = 1 when i is in S
binary(S)_i = 0 otherwise
```

A candidate pair is eligible only when:

```text
cardinality(A) = 9
cardinality(B) = 9
A != B
L2(binary(A)) = L2(binary(B))
no affine relabeling maps A to B
no affine-plus-complement relabeling maps A to B
the direct labeled triple-count arrays differ in fixed L3 order
```

Eligibility and duplicate removal must be computed from raw supports and lower-order or direct-certificate mathematics only.

They must not import, call, hash, compare, or otherwise use challenger descriptor values.

For any support `S`, define its raw-support nuisance-orbit key as follows.

For every:

```text
u in U_64
v in Z_64
q in {0,1}
```

construct:

```text
S_(u,v,0) =
    {(u*s+v) mod 64 : s in S}

S_(u,v,1) =
    Z_64 \ S_(u,v,0)
```

Serialize each transformed support as exactly 64 ASCII characters:

```text
b_0 b_1 ... b_63
```

where:

```text
b_j = "1" when j is in the transformed support
b_j = "0" otherwise
```

Define:

```text
member_orbit_key(S) =
    lexicographic minimum of those 4096 binary strings
```

Reflection requires no separate transformation pass because it is already included by:

```text
u = -1 mod 64
```

For an eligible pair `(A,B)`, define:

```text
key_A = member_orbit_key(A)
key_B = member_orbit_key(B)

pair_duplicate_key(A,B) =
    (key_A,key_B) when key_A <= key_B
    (key_B,key_A) otherwise
```

This makes slot exchange irrelevant and independently quotients each member by the same affine-plus-complement nuisance relation used by the primary descriptor comparison.

A seed is unique exactly when its `pair_duplicate_key` has not appeared for any earlier eligible seed.

The generator scans seeds in the exact declared seed order, records each previously unseen eligible key, and freezes the first eight such pairs.

No pair may be skipped, replaced, reordered, or removed because of a challenger result.

The fixture manifest must be committed before synthetic challenger execution and must include:

```text
generator version
generator source hash
enumeration policy
seed tuples
raw sequences
member orbit keys
pair duplicate keys
accepted seed-order positions
lower-order certificates
direct triple-count certificates
equivalence certificates
canonical manifest hash
```

Required synthetic-family success:

```text
8 of 8 positive-control pairs distinguished
```

Anything below `8 of 8` is a failed synthetic positive-control gate for v0.1.

It may not be repaired by dropping fixtures, selecting lag coordinates, changing normalization, or weakening the threshold.

## 10. Deterministic serialization contract

The primary payload must be canonical UTF-8 JSON.

Required encoding:

```text
UTF-8 without BOM
LF line ending
one terminal LF
no NaN
no Infinity
no negative zero
integers serialized in base 10
object keys in the exact specified order
compact separators
```

The schema in this section is the canonical per-sequence descriptor-result payload.

Pair comparison, synthetic-family validation, frozen-family evaluation, publication, authorization, and process-level failure envelopes are outside this per-sequence schema and require later separately authorized specifications.

Every serialized per-sequence payload must contain exactly these top-level fields in exactly this order:

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

No additional top-level field is permitted.

Required constants:

```text
schema =
torment-brainvision-independent-order-sensitive-descriptor-result-v0.1

descriptor_id =
n64-normalized-labeled-third-order-cyclic-correlation-v0.1

N =
64

lag_domain_id =
n64-distinct-position-ordered-lag-pairs-lexicographic-v0.1

entry_count =
3906
```

JSON booleans and null must be serialized only as the JSON literals:

```text
true
false
null
```

### Valid per-sequence payload

For a valid payload:

```text
weight =
an integer in 1..63

canonical_denominator =
a positive integer

raw_labeled_numerators =
a flat array of exactly 3906 integers in fixed L3 order

affine_canonical_numerators =
a flat array of exactly 3906 integers in fixed L3 order

affine_complement_canonical_numerators =
a flat array of exactly 3906 integers in fixed L3 order
```

`lower_order_signature` must be exactly one object with keys in this order:

```text
N
weight
A2
```

with:

```text
N = 64
weight = the same integer as the top-level weight
A2 = a flat 64-entry integer array ordered by d = 0..63
```

`transition_table` must be:

```text
[[n00,n01],[n10,n11]]
```

where rows are indexed by:

```text
x_i = 0,1
```

and columns are indexed by:

```text
x_(i+1 mod 64) = 0,1
```

`validation` must be exactly one object with keys in this order:

```text
valid
failure_code
failure_stage
detail
```

and exact value:

```json
{"valid":true,"failure_code":null,"failure_stage":null,"detail":null}
```

For a valid payload:

```text
ordered_failure_codes = []
```

### Invalid per-sequence payload

Per-sequence validation uses first-failure semantics in this exact order:

```text
1. input length
2. input element type
3. binary domain
4. degenerate constant sequence
5. normalization validity
6. integer-bound invariant
```

An invalid per-sequence payload must retain all top-level fields in the fixed order.

Its values must be:

```text
schema =
the fixed schema string

descriptor_id =
the fixed descriptor identifier

N =
64

weight =
null

lag_domain_id =
the fixed lag-domain identifier

entry_count =
3906

canonical_denominator =
null

raw_labeled_numerators =
null

affine_canonical_numerators =
null

affine_complement_canonical_numerators =
null

lower_order_signature =
null

transition_table =
null
```

`ordered_failure_codes` must contain exactly one code, selected by the first-failure order above.

The permitted invalid per-sequence codes are:

```text
INPUT_LENGTH_INVALID
INPUT_ELEMENT_TYPE_INVALID
INPUT_BINARY_DOMAIN_INVALID
DEGENERATE_SEQUENCE
NORMALIZATION_INVALID
INTEGER_BOUND_INVARIANT_FAILURE
```

`validation.failure_code` must equal the sole member of `ordered_failure_codes`.

`validation.failure_stage` must be:

```text
input_validation
```

for:

```text
INPUT_LENGTH_INVALID
INPUT_ELEMENT_TYPE_INVALID
INPUT_BINARY_DOMAIN_INVALID
DEGENERATE_SEQUENCE
```

It must be:

```text
normalization
```

for:

```text
NORMALIZATION_INVALID
```

It must be:

```text
descriptor_invariant
```

for:

```text
INTEGER_BOUND_INVARIANT_FAILURE
```

`validation` must otherwise be exactly:

```text
{
    "valid": false,
    "failure_code": the canonical first failure code,
    "failure_stage": the canonical stage above,
    "detail": null
}
```

No free-form exception text is permitted in the canonical payload.

### Failure before canonical payload completion

A failure that prevents canonical serialization cannot be represented inside the canonical payload whose creation failed.

Therefore:

```text
SERIALIZATION_FAILURE
UNAUTHORIZED_EXECUTION
FORBIDDEN_IMPORT_DETECTED
PROHIBITED_EVIDENCE_CONTACT_DETECTED
PRODUCTION_BOUNDARY_VIOLATION
```

and other runner-, boundary-, pair-, family-, replay-, or publication-level failures must be represented only in a later separately specified execution envelope or process failure channel.

No partial canonical descriptor payload may be published.

### Hash scope

The canonical payload hash is SHA-256 over the complete canonical UTF-8 JSON bytes, including the required single terminal LF.

`raw_labeled_numerators` must use fixed L3 order.

All nested object-key orders and array orders are fixed above.

Human-readable output, if later authorized, must be derived from the canonical payload and must not replace or amend it.

## 11. Static and runtime leakage prevention

A future implementation must undergo a source-level boundary scan before execution.

The scan must reject:

```text
imports from torment_service
imports from historical PsiTRS modules
imports from the F3 evaluator
imports from the F3 asymmetry analyzer
dynamic imports targeting prohibited modules
subprocess calls to production services
network libraries in the descriptor execution path
camera or screen-capture libraries
access to retained F3 result files
access to retained F3 payload files
access to the published asymmetry-audit result
access to historical execution-gate environment variables
```

The primary descriptor module must not read environment variables.

The primary descriptor function must not perform filesystem I/O.

The future runner may read an explicitly authorized raw fixture file and write an explicitly authorized result path, but it must pass only a validated 64-entry binary vector into the descriptor function.

The frozen benchmark adapter must keep candidate metadata outside the descriptor call.

## 12. Staged authorization policy

### Stage S0 — specification

Current stage:

```text
docs-only
no implementation
no execution
no benchmark contact
```

Completion of this document does not advance authority automatically.

### Stage S1 — synthetic fixture freeze

Requires a separate docs-only authorization.

Permitted future scope:

```text
create and verify synthetic fixture generator
freeze deterministic synthetic manifest
do not implement challenger
do not contact frozen K=3 family
```

### Stage S2 — challenger implementation

Requires a separate docs-only authorization after the synthetic fixture manifest is frozen.

Permitted future scope:

```text
implement the exact v0.1 descriptor
implement static boundary checks
implement deterministic serialization
implement unit tests
do not read frozen K=3 sequences
do not evaluate frozen K=3 family
```

### Stage S3 — synthetic validation

Requires a separate execution authorization.

The implementation identity must be frozen before synthetic results are exposed.

Synthetic validation must pass completely.

No source modification is permitted between the successful synthetic run and the decision to authorize frozen-family evaluation, except documentation that records immutable identities and results.

### Stage S4 — frozen-family authorization

Requires a new docs-only authorization containing at minimum:

```text
challenger source Git blob
challenger raw SHA-256
runner source Git blob
runner raw SHA-256
synthetic manifest SHA-256
synthetic result SHA-256
canonical serialization identity
exact input fixture identity
exact candidate order [478, 479, 480]
exact output path
one-run authority
```

### Stage S5 — frozen-family execution

A future authorization may permit exactly one authoritative frozen-family invocation.

Before that invocation:

```text
descriptor implementation is frozen
serialization is frozen
controls are frozen
success criteria are frozen
candidate order is frozen
no v0.1 challenger frozen-family output has been observed
```

After that invocation:

```text
no tuning is permitted
no lag selection is permitted
no normalization change is permitted
no threshold change is permitted
no fixture removal is permitted
no result-driven v0.1 patch is permitted
```

A v0.1 failure remains a valid negative result.

Any future v0.2 must be a genuinely new preregistered branch and must not replace or overwrite v0.1.

## 13. Frozen-family evaluation contract

The future evaluator must process candidates exactly in this order:

```text
478
479
480
```

For each candidate:

1. Validate both raw 64-entry binary sequences.
2. Compute both lower-order signatures independently.
3. Reject the pair as invalid if the lower-order signatures do not match.
4. Compute each raw descriptor independently.
5. Compute affine-only canonical signatures.
6. Compute affine-plus-complement canonical signatures.
7. Compare exact signatures.
8. Attach candidate metadata only after comparison.
9. Serialize the complete per-pair evidence.
10. Preserve slot order without assigning semantic meaning to either slot.

The primary per-pair classification uses the affine-plus-complement signature:

```text
DECLARED_HIGHER_ORDER_DISTINCTION_DETECTED
```

only when the exact signatures differ.

It uses:

```text
DECLARED_HIGHER_ORDER_DISTINCTION_NOT_DETECTED
```

when the exact signatures are equal.

No epsilon, tolerance, score threshold, rank threshold, or approximate comparison is permitted.

## 14. Success, partial result, and failure language

### 14.1 Family-level success

The exact v0.1 success criterion is:

```text
all 3 frozen candidate pairs
have valid matched lower-order controls

and

all 3 affine-plus-complement canonical signatures differ
between slot_0 and slot_1
```

The only admitted family-level success disposition is:

```text
INDEPENDENT_CHALLENGER_DETECTS_DECLARED_HIGHER_ORDER_DISTINCTION_ON_EXACT_FROZEN_K3_FAMILY
```

Its meaning is limited to:

The exact v0.1 descriptor detected the declared labeled third-order distinction, after the specified nuisance quotient, on all three members of the exact frozen benchmark family.

It does not prove:

```text
vision
perception
consciousness
physics
energy
the geometric Z intuition
a derivation of N64/K=3
production readiness
general temporal understanding
general order understanding
prerecorded-video usefulness
superiority over other descriptors
```

### 14.2 Partial distinction

If exactly one or two valid frozen pairs are distinguished:

```text
INDEPENDENT_CHALLENGER_PARTIAL_DISTINCTION_ON_EXACT_FROZEN_K3_FAMILY
```

This is not family-level success.

Per-pair results remain reportable.

No post-result subset claim may replace the preregistered three-pair criterion.

### 14.3 Valid negative result

If zero valid frozen pairs are distinguished:

```text
INDEPENDENT_CHALLENGER_NOT_SUPPORTED_BY_EXACT_FROZEN_K3_FAMILY
```

This is a valid negative result.

It must not be retried or rescued under v0.1.

### 14.4 Control-invalid result

If any frozen pair fails the previously certified lower-order input contract or another execution-integrity condition:

```text
FROZEN_FAMILY_CHALLENGER_EVALUATION_INVALID
```

An invalid execution is not a scientific success or failure.

It does not authorize an automatic rerun.

Any proposed rerun requires a new docs-only adjudication that identifies the exact integrity failure without inspecting or tuning against scientific output.

## 15. Explicit falsification criteria

The v0.1 challenger is falsified as an implementation candidate before frozen contact if any of the following occurs:

```text
the fixed homometric positive fixture is not distinguished
fewer than 8 of 8 generated positive controls are distinguished
an identity control is distinguished
a nuisance-equivalent control is distinguished
rotation invariance fails
reflection equivariance fails
affine equivariance fails
complement antisymmetry fails
self-orbit canonicalization fails
exact replay is not byte-identical
serialization is nondeterministic
a primary comparison uses floating point
a prohibited import or evidence dependency exists
```

The frozen-family-wide detection claim is falsified if:

```text
any one of candidates 478, 479, or 480
has equal valid affine-plus-complement canonical signatures
```

No aggregate score may override this criterion.

## 16. Ordered failure codes

A future implementation must use deterministic ordered failure codes.

The v0.1 code vocabulary is reserved as:

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

When multiple failures occur, codes must be emitted in the vocabulary order above.

No free-form exception text may replace the canonical codes in the machine-readable payload.

## 17. Separation from geometric intuition

Hilmir's geometric intuition remains available for hypothesis generation:

```text
three closed tri-octagonal structures
an enclosing circular phase structure
three upper gaps
three lower gaps
six polarity/orientation locations
central Z circulation or rotor-like behavior
binary projection from geometric orientation
```

The v0.1 challenger is not specified as a derivation of that geometry.

The descriptor is a general, explicit, labeled third-order cyclic statistic under controlled lower-order matching, but its selection for v0.1 is benchmark-aware as disclosed in §1.1.

A successful result would not demonstrate the geometric model.

A failed result would not disprove or abandon the geometric intuition.

Any future geometry-derived descriptor must be specified as a separate challenger and must not overwrite v0.1.

## 18. Prerecorded Brainvision bridge remains closed

No application of this descriptor to prerecorded visual sequences is authorized.

A future bridge would require a separate specification defining at minimum:

```text
how visual data becomes a cyclic or windowed sequence
what labels and channels mean
how temporal boundaries are handled
what lower-order controls are matched
what normalization is used
what nuisance transformations are admitted
how leakage from the binary benchmark is prevented
what synthetic visual controls are required
what falsification criterion applies
```

The prerecorded bridge must not be opened merely because the binary challenger succeeds.

Current state:

```text
PRERECORDED_CHALLENGER_BRIDGE_AUTHORIZED = False
LIVE_CHALLENGER_BRIDGE_AUTHORIZED = False
PRODUCTION_CHALLENGER_BRIDGE_AUTHORIZED = False
```

## 19. Reserved future artifact names

The following names are reserved only to prevent naming drift. They do not authorize file creation:

```text
research/brainvision/independent_order_sensitive_descriptor_v0_1.py

research/brainvision/generate_independent_order_sensitive_synthetic_fixtures_v0_1.py

research/brainvision/run_independent_order_sensitive_synthetic_validation_v0_1.py

research/brainvision/run_independent_order_sensitive_frozen_n64_evaluation_v0_1.py

research/brainvision/test_independent_order_sensitive_descriptor_v0_1.py

research/brainvision/test_independent_order_sensitive_synthetic_fixtures_v0_1.py
```

No historical F3 module may be renamed, copied, wrapped, or imported to implement these artifacts.

## 20. Current authority ledger

At acceptance of this specification, the authority state remains:

```text
INDEPENDENT_CHALLENGER_SPECIFIED = True

SYNTHETIC_FIXTURE_GENERATION_AUTHORIZED = False
SYNTHETIC_FIXTURE_EXECUTION_AUTHORIZED = False
CHALLENGER_IMPLEMENTATION_AUTHORIZED = False
CHALLENGER_SYNTHETIC_VALIDATION_AUTHORIZED = False
CHALLENGER_FROZEN_FAMILY_INPUT_ACCESS_AUTHORIZED = False
CHALLENGER_FROZEN_FAMILY_EVALUATION_AUTHORIZED = False
CHALLENGER_FROZEN_FAMILY_RERUN_AUTHORIZED = False
PRERECORDED_CHALLENGER_BRIDGE_AUTHORIZED = False
PSITRS_CONTACT_AUTHORIZED = False
RETAINED_EVIDENCE_MODIFICATION_AUTHORIZED = False
PRODUCTION_INTEGRATION_AUTHORIZED = False
KERNEL_MODIFICATION_AUTHORIZED = False
```

No execution gate is created or opened by this document.

## 21. Specification disposition

This specification chooses exactly:

```text
descriptor =
full normalized labeled nondegenerate third-order cyclic correlation tensor

arithmetic =
exact integer and rational arithmetic

primary lag domain =
all 3906 ordered distinct-position lag pairs

nuisance quotient =
affine-only and affine-plus-complement canonical signatures

primary frozen-family comparison =
affine-plus-complement exact signature equality

synthetic positive threshold =
fixed fixture passes and 8 of 8 generated homometric controls pass

frozen-family success threshold =
3 of 3 valid frozen pairs distinguished

post-result tuning =
prohibited
```

The next permitted project action is a docs-only review of this specification.

No implementation or execution follows automatically.

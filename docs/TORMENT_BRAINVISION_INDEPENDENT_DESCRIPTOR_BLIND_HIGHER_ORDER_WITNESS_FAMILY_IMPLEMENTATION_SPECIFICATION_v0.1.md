# TORMENT Brainvision Independent Descriptor-Blind Higher-Order Witness Family Implementation Specification v0.1

## 1. Scope and authority

**DOCS-ONLY specification. Non-implementing.** This document governs a new, independent, descriptor-blind
validation lane (route A) that is separate from and non-gating to the operational lanes. It changes no code,
no test, and no existing document, and it authorizes no execution.

```text
documentation_authorization    = True
implementation_authorization   = False
witness_generation_authorization = False
PsiTRS_evaluation_authorization = False
scientific_inference_authorization = False
```

Preserved route standing (unchanged by this document):

```text
B: prerecorded operational harness remains the usable offline system
C: descriptor understanding remains non-gating diagnostics
A: independent descriptor-blind validation advances as a separate lane
```

Global boundaries (preserved exactly):

```text
offline ; prerecorded ; quarantined ; service-disconnected ; non-runtime ; non-production ; descriptive-only
FORMAL_HOLD = active
Mode_0      = active
runtime_integration      = unauthorized
scientific_claims        = unauthorized
perception_or_vision_claims = unauthorized
temporal_order_claims    = unauthorized
```

Immutable — never modified or proposed for modification:

```text
research/brainvision/psi_trs.py
research/brainvision/run_n64_falsifier_v0_1.py
torment_service/kernel/
torment_service/memory_kernel.py
torment_service/fabric.py
```

**This specification must not alter, replace, reinterpret, or retroactively strengthen the original N64
evaluation.** That result remains, verbatim:

```text
VALID_DESCRIPTIVE_MIXED_RESULT_REQUIRING_INDEPENDENT_VALIDATION
```

The original N64 evaluation did **not** preselect an A/B-versus-self-shift comparability rule. The F3 gate
defined in §11 is a **new, forward-only** contract for this new family; it must **never** be applied
retroactively to the original N64 result.

## 2. Mathematical domain

```text
alphabet                 = {0,1}
index_domain             = Z_N
indexing                 = circular
primary_evaluation_length = N = 64
reference_verifier_length = N = 12
```

Definitions (support-set formalism; all indices mod N):

```text
support set S            = { t in Z_N : x(t) = 1 }
indicator sequence x     = x(t) in {0,1}
weight                   = w = |S|
complete periodic autocorrelation:
  r(k) = sum over t in Z_N of x(t)*x(t+k)  =  |{ (i,j) in S x S : i - j = k mod N }|,  for all k in Z_N
directed one-step table:
  c_{ab} = |{ t in Z_N : x(t)=a and x(t+1)=b }|,  a,b in {0,1}
absolute binary transition multiset:
  multiset of |x(t+1) - x(t)| over t in Z_N   (values in {0,1})
complete labeled triple array:
  T(k,l) = sum over t in Z_N of x(t)*x(t+k)*x(t+l)  =  |{ t : t, t+k, t+l in S }|,  (k,l) in Z_N x Z_N
```

**Binary-domain implication (recorded and used, not assumed).** For binary circular sequences:

```text
c11 = r(1)
c10 = weight - r(1)
c01 = weight - r(1)
c00 = N - 2*weight + r(1)
```

Therefore, **in this exact binary circular domain, equal complete periodic autocorrelation implies equal
directed one-step tables and equal absolute binary transition multisets.** These certificates are thus
mathematically implied by the autocorrelation certificate; nevertheless they **must still be emitted and
independently recomputed and checked** (§9), never skipped on the grounds of implication.

## 3. Transform group

The affine index group is:

```text
AGL(1, Z_N) = Z_N  semidirect_product  U(N)
maps:  t -> u*t + a  (mod N),  with  a in Z_N,  u in U(N)   (U(N) = units of Z_N)
translations : u = 1
reflections  : u = -1 mod N   (contained in AGL; not a separate factor)
```

The binary symbol complement is a central C2 factor giving the effective sequence-transform group:

```text
G = C2 x ( Z_N  semidirect_product  U(N) )
```

**Complement acts on the sequence, not on indices/lags.** A complement transform must first replace the
sequence by its symbol complement (S -> Z_N \ S) and then **all invariants are recomputed** on the
transformed sequence. Complement must never be represented as a mere index or lag relabeling.

### 3.1 Equivalence identity versus frozen evaluation supports

Three explicitly separate objects are defined and must not be conflated:

```text
member_G_equivalence_key:
  the lexicographically minimal representation obtained over all permitted G transforms, including complement.

canonical_pair_key:
  the ordered pair of the two member_G_equivalence_keys, sorted lexicographically.

frozen_evaluation_supports:
  the actual raw supports emitted by the deterministic generator and accepted by the verifier.
```

```text
Complement-inclusive canonical keys are used only for equivalence testing, deduplication, deterministic
ordering, and certificate identity.

The actual supports selected for evaluation must not be silently replaced by their complement, affine,
reflected, translated, or otherwise transformed canonical representatives.

The frozen family manifest must contain both:
  - the raw evaluation supports
  - their canonical equivalence keys
```

Deterministic pair orientation: within a pair, the two **raw** supports are named A and B by a fixed
**raw-support lexicographic ordering** (sorted ascending support tuple; the lexicographically smaller raw
support is A). This orientation names members **without transforming them**; it is distinct from the
canonical equivalence keys, which are used only for identity/ordering.

### 3.2 Group-orbit enumeration and stabilizers

```text
The verifier enumerates all 2*N*|U(N)| group elements.
At N=64 this is 4096 group elements.
At N=12 this is 96 group elements.
The de-duplicated orbit of a particular sequence may be smaller when the sequence has a nontrivial stabilizer.
```

Primitive circular period 64 (§5) excludes rotational (translation) stabilizers for the N=64 primary members,
but does **not** necessarily eliminate every affine or complement-related stabilizer. Equivalence tests
therefore enumerate the full group and compare, rather than assuming a free orbit of size 2*N*|U(N)|.

## 4. Reference witness

Proposed minimal mathematical reference witness (recomputed and confirmed at draft time):

```text
N = 12
A = {0,1,3,5,6}
B = {0,1,2,4,7}
```

Expected certificates (all recomputed from the raw supports):

```text
complete periodic autocorrelation (A and B identical):
  (5,2,2,2,1,2,2,2,1,2,2,2)

directed one-step table (each member):
  c00 = 4 ; c01 = 3 ; c10 = 3 ; c11 = 2

absolute transition multiset (each member):
  0 -> 6
  1 -> 6

labeled triple-array disagreements:
  48 of 144

affine equivalent                : False
affine-plus-complement equivalent : False
triple-G-alignable                : False
```

Bounded search statement:

```text
No valid witness was found by exhaustive search for N in {4,5,6,7,8,9,10,11} under the selected predicates
(homometric, G-inequivalent, third-order G-nonalignable).

Lengths N in {1,2,3} are excluded as trivial/degenerate domains for this witness definition and were not part
of the recorded exhaustive search. Therefore the document does not claim a literal exhaustive result over
every positive N below 12.
```

This is a **computationally verified bounded result, not a general theorem**.

The N=12 witness has exactly three roles:

```text
reference verifier fixture
mathematical construction witness
small-N regression object
```

It is **not** a primary Brainvision evaluation fixture. The following operations on the N=12 pair are
**prohibited** (they would alter its autocorrelation/triple structure and are a confound):

```text
tiling ; padding ; repetition ; embedding ; resampling ; lifting   (into N=64 or any other length)
```

## 5. Primary N=64 witness predicates

Each accepted N=64 pair (A,B) must satisfy **all** of:

```text
equal complete periodic autocorrelation
equal directed one-step table
equal absolute transition multiset
full labeled triple-array G-nonalignment
affine inequivalence
affine-plus-complement inequivalence
neither member is the complement image of the other
both members have primitive circular period 64
```

Primitive circular period 64:

```text
rotate(x, r) != x   for every r in {1,...,63}
```

**Third-order G-nonalignment (single coherent formulation).** Sequence-level G-inequivalence alone is
insufficient; third-order G-nonalignment is verified as follows:

```text
For full labeled triple-array G-nonalignment, translation need not be enumerated separately because the
complete cyclic triple array is translation-invariant.

For each c in {identity, complement} and each u in U(N):
  1. Let X be A when c=identity and complement(A) when c=complement.
  2. Compute the complete triple array T_X from X.
  3. Compare T_B(k,l) against T_X(u^{-1}k, u^{-1}l) for every (k,l) in Z_N x Z_N.

No pair (c,u) may produce complete equality.

An equivalent implementation may transform the raw sequence by the unit-affine action, recompute its complete
triple array, and compare the recomputed arrays directly. The verifier must use exactly one of these
formulations and must not apply both.

Complement is handled only by complementing the sequence and recomputing its triple array. Complement is
never represented as a lag relabeling.
```

The translation parameter `a` disappears from the triple-array comparison because the complete cyclic triple
array is translation-invariant; `a` remains relevant only to sequence-level G-equivalence and to member
canonicalization (§3), not to third-order alignment.

**Theorem boundary.** This specification does **not** claim a theorem that complete third-order cyclic
correlation reconstructs every binary support up to G. For the N=12 fixture, triple-array G-nonalignment is
computationally verified; for future N=64 candidates it is an exact verifier predicate; its general
reconstruction power remains unclaimed.

## 6. Family requirements

Freeze exactly:

```text
K = 3 primary pairs   (six members total)
```

Requirements:

```text
no member reused across pairs
all six members mutually G-inequivalent
all members have primitive circular period 64
each pair belongs to a distinct complete-autocorrelation class
all three pairs satisfy every §5 witness predicate
```

"Distinct autocorrelation class" means the complete periodic autocorrelation vector of pair 1 differs from
that of pair 2 and of pair 3, and likewise for every pairwise comparison (all three pairs are pairwise
autocorrelation-distinct).

```text
Distinct autocorrelation classes provide construction-diversity pressure only.

They do not prove distinct algebraic construction families, statistical independence, or broad scientific
generality.

Failure to obtain three such classes within the frozen budget is an accepted route failure and does not
authorize weakening the rule.
```

## 7. Descriptor-blind construction route

Primary route:

```text
exact SAT/SMT-style candidate generation followed by exact independent verification
```

Solver-versus-verifier division (the solver need not encode every witness predicate):

```text
The solver should encode at minimum:
  binary support variables
  frozen weight/range policy if selected
  equal complete periodic autocorrelation
  primitive-period constraints or sufficient symmetry-breaking
  deterministic model-order constraints

The following may be implemented as exact post-generation verifier filters rather than solver clauses:
  complete G-inequivalence
  affine-plus-complement inequivalence
  full triple-array G-nonalignment
  member non-reuse
  all-six-member mutual G-inequivalence
  distinct autocorrelation classes
  complete family uniqueness

A candidate is not valid merely because the solver produced it. Only an independently verified candidate may
enter the family stream. A probabilistic or approximate verifier is not permitted.
```

The generator must **never** import, call, inspect, or use outputs from:

```text
psi_trs ; psi_trs_k0 ; SAG ; recursive_delta ; paired prerecorded analysis ; operational harness ;
N64 response evaluator ; descriptor responses ; self-shift response orbits
```

Deterministic bounded enumeration and selection (replaces any global-sort rule):

```text
Before implementation, freeze:
  - a bounded candidate-generation domain
  - a deterministic total candidate order
  - solver version and configuration
  - worker count
  - random seed, fixed even when randomness is disabled
  - model-enumeration policy
  - symmetry-breaking policy
  - compute/model budget

Candidates are produced in that frozen deterministic order.

For each candidate pair:
  1. preserve the raw generated supports
  2. compute canonical equivalence keys
  3. run the independent verifier
  4. reject invalid or duplicate candidates
  5. accept the candidate if all pair and current-family predicates pass

Stop when K=3 pairs have been accepted or the frozen budget is exhausted.

No sorting over unknown or unenumerated global candidates is required.
```

Replay determinism (required):

```text
The same generator identity, configuration, candidate domain, and budget must reproduce the same ordered
candidate stream and the same accepted family.

Solver seed, worker scheduling, hash iteration order, unordered set iteration, filesystem order, or
nondeterministic parallel model discovery must not affect family membership.
```

If the chosen solver cannot guarantee deterministic bounded enumeration under this contract, it is **not
admissible** for the primary route. No candidate may be selected using ΨTRS behavior.

Fallback route:

```text
deterministic theorem-backed difference-multiset or direct-sum enumeration
```

The fallback must use the **same** verifier, canonicalization, family requirements, and deterministic
selection/enumeration contract. It must **not** be seeded from:

```text
the existing N64 fixture ; the balanced-complement control family ; PsiTRS outputs ; self-shift orbit behavior
```

The previous N=64 five-pair set is classified only as `BALANCED_COMPLEMENT_HOMOMETRIC_CONTROL_FAMILY_v0`
(every pair had B = 1 - A, weight 32; B is a complement image, i.e. a G-operation). It is retained solely as a
control and is never a seed or a primary witness.

## 8. Route stop conditions

A compute/model budget is **predeclared and frozen before implementation** (concrete budget selected in the
implementation authorization step, not here).

Primary-route stop:

```text
If three valid distinct-autocorrelation-class pairs are not produced within the frozen budget, stop and report:
  PRIMARY_N64_CONSTRUCTION_ROUTE_INCOMPLETE
```

The following must **not** be done silently (each would weaken the witness definition):

```text
increase the budget ; reduce K ; drop primitive-period requirements ; drop an equivalence exclusion ;
reuse an autocorrelation class ; replace failed candidates ; consult descriptor outputs
```

Fallback-route stop:

```text
If the frozen fallback budget also fails:
  N64_PRIMARY_FAMILY_NOT_CONSTRUCTED
```

This is a **valid negative engineering result**, not permission to weaken the witness definition.

## 9. Independent verification

A verifier **independent from the generator** must recompute from the **raw supports** (never trusting
generator summaries):

```text
all 64 autocorrelation entries
one-step table
absolute transition multiset
all 4096 labeled triple-array entries
primitive circular period
complete G orbit
affine inequivalence
affine-plus-complement inequivalence
triple-array G-nonalignment
mutual family inequivalence
distinct autocorrelation classes
```

Independent verifier means precisely:

```text
- a separate module from the generator;
- no imports from the generator;
- no shared witness-predicate helper functions;
- no trust in generator summaries or certificates;
- invariant calculations independently re-derived from raw supports;
- separate canonicalization/equivalence implementation logic;
- regression verification against the frozen N=12 reference witness;
- negative regression fixtures for non-homometric, affine-equivalent, complement-equivalent, non-primitive,
  and triple-alignable cases.

Shared low-level standard-library or serialization utilities are permitted only when they do not implement
witness mathematics.
```

Tests must prove the verifier does **not** import the generator or any shared mathematical predicate helper.

Require deterministic canonical serialization and SHA-256 hashes for:

```text
raw supports
per-pair certificates
complete family manifest
generator identity/configuration
verifier identity/configuration
```

Require a **second identical replay and byte comparison** (byte-identical canonical output, equal SHA-256)
before the family may be frozen.

## 10. Freeze rule

The family must be **frozen before any Brainvision descriptor or ΨTRS evaluation**. After freeze:

```text
no pair replacement ; no member replacement ; no reorder based on response ; no threshold adjustment ;
no family-size adjustment ; no construction rerun to seek stronger responses
```

A response failure does **not** authorize replacing a witness. If a frozen witness produces invalid numerical
inputs or violates the predeclared evaluation schema, the **evaluation** is classified invalid — the witness
is **not** substituted with the next candidate.

## 11. F3 evaluation contract

This contract is defined now but its execution is unauthorized.

### 11.1 Response object binding (exact existing mathematics; no new metric)

The evaluator reuses the accepted N64 / boundary-neutral normalized **symmetric** L2 response object. After
inspecting the committed sources, the exact bindings are:

```text
input encoding and shape:
  raw binary field D of shape (64, 1), dtype float, values in {0.0, 1.0}
raw binary value encoding:
  DIRECT_SCALAR_BINARY_0_1 (support indicator used directly; not centered to +/-1; no complement channel added)
member orientation:
  members named A, B by the fixed raw-support lexicographic order (§3.1)
rotation convention:
  rotate(x, s)[t] = x[(t + s) mod 64] = np.roll(x, -s mod 64, axis=0)
  bound to  research/brainvision/run_n64_falsifier_v0_1.py :: rotate
matched-start extraction rule:
  a common start s is applied identically to both members (SAME_OFFSET, all 64 starts)
64-start O1 policy:
  all 64 starts s in {0,...,63}
A3 aggregation:
  arithmetic mean over the 64 matched-start responses
full PsiTRS feature call identity and parameters:
  run_n64_falsifier_v0_1.py :: features(field, "psi_trs")  ->  psi_trs.psi_trs_features(field, kappa=0.5)
  (length-11 float vector)
k0 feature call identity and parameters:
  run_n64_falsifier_v0_1.py :: features(field, "psi_trs_k0")  ->  psi_trs.psi_trs_features(field, kappa=0.0)
  (recursive-time channel collapses at kappa=0)
normalized response formula:
  run_n64_falsifier_v0_1.py :: symmetric_response(f_a, f_b), field "distance":
    numerator             = ||f_a - f_b||_2
    joint_scale           = (||f_a||_2 + ||f_b||_2) / 2
    effective_joint_scale = max(joint_scale, EPSILON)
    distance              = numerator / effective_joint_scale
  (this is the F2 = JOINT_MEAN_NORM_NORMALIZED_L2 object; not a new metric)
denominator definition and floor:
  denominator = joint_scale ;  floor  EPSILON = 1e-12
  (NEAR_EPSILON_THRESHOLD = 1e-9 is a diagnostic threshold; psi_trs internal _EPS = 1e-8 is NOT this floor
   and is never reused as a gate band)
whether response is symmetric:
  yes (role-swap invariant)
how A/B orientation is handled if the primitive is directional:
  the primitive is symmetric, not directional; member orientation is therefore immaterial to the cross values
raw finite-float storage and serialization:
  raw unrounded floats stored and canonically serialized (ensure_ascii, sort_keys, compact separators,
  allow_nan=False); finite checks precede all comparisons
expected identity self-pair response:
  0.0 exactly (numerator == 0 for identical feature vectors; EXACT_FINITE_IN_PROCESS_SELF_PAIR_EQUALITY)
```

Concretely, for a frozen pair (A,B) and variant v in {"psi_trs","psi_trs_k0"}:

```text
cross_s(v)      = symmetric_response(features(rotate(A,s),v),        features(rotate(B,s),v))["distance"]
self_A[r,s](v)  = symmetric_response(features(rotate(A,s),v),        features(rotate(A,(s+r) mod 64),v))["distance"]
self_B[r,s](v)  = symmetric_response(features(rotate(B,s),v),        features(rotate(B,(s+r) mod 64),v))["distance"]
full_* uses v="psi_trs" ;  k0_* uses v="psi_trs_k0"
```

The implementation must **not** silently choose alternative normalization, averaging, orientation, or
denominator semantics. Any deviation from these exact bindings is a specification violation, not an
implementation detail.

### 11.2 Start / shift objects and aggregation

For every matched start `s in {0,...,63}`:

```text
full_cross_s ; k0_cross_s
```

For every nonidentity circular shift `r in {1,...,63}` and every matched start `s`:

```text
full_self_A[r,s] ; full_self_B[r,s] ; k0_self_A[r,s] ; k0_self_B[r,s]
```

Identity shift `r = 0` is **excluded from reference extrema** but must be evaluated as an **exact self-pair
validity control** (must equal the exact expected identity self-pair response, 0.0).

O1/A3 aggregation:

```text
full_cross_mean     = mean over all 64 matched starts of full_cross_s
k0_cross_mean       = mean over all 64 matched starts of k0_cross_s
full_self_A_mean[r] = mean over all 64 matched starts of full_self_A[r,s]
full_self_B_mean[r] = mean over all 64 matched starts of full_self_B[r,s]
k0_self_A_mean[r]   = mean over all 64 matched starts of k0_self_A[r,s]
k0_self_B_mean[r]   = mean over all 64 matched starts of k0_self_B[r,s]
```

Duplicate rotations retain multiplicity in emitted distributions and summaries. Because the primary witnesses
have primitive period 64, no nonidentity rotation is sequence-identical to its source.

### 11.3 Gates and the primary pair pass

```text
full_dual_orbit_extreme =
    full_cross_mean > max_r( full_self_A_mean[r] )  AND  full_cross_mean > max_r( full_self_B_mean[r] )

k0_not_extreme_against_either_member =
    k0_cross_mean <= max_r( k0_self_A_mean[r] )     AND  k0_cross_mean <= max_r( k0_self_B_mean[r] )

recursive_positive_all_starts =
    for every start s:  full_cross_s - k0_cross_s > 0
```

```text
PAIR_STRONG_PASS =
    valid_run
    AND full_dual_orbit_extreme
    AND k0_not_extreme_against_either_member
    AND recursive_positive_all_starts
```

Exact bounded hypothesis:

```text
The full representation must exceed both members' complete nonidentity self-shift references.
The k0 representation must exceed neither member's complete nonidentity self-shift reference.
This is intentionally stronger than merely requiring k0 to fail the joint dual-orbit condition.
```

`recursive_positive_all_starts` is classified only as **a cross-pair recursive companion sign condition**. It
does **not** establish delta-orbit specificity, because it is not compared with full-minus-k0 self-shift
margins. No new delta-orbit gate is added in this specification.

A single nonidentity full self-shift mean equaling or exceeding the full cross mean **defeats** the strict
pair gate. No quantile, rank, trimmed mean, median, or secondary summary may rescue a failed primary gate; all
secondary summaries remain descriptive only.

### 11.4 valid_run (exact finite validity list)

```text
valid_run = conjunction of every frozen validity check below:

family manifest hash matches the frozen family
raw support hashes match
all six members have length 64 and binary finite values
all pair/family witness certificates reverify
generator identity/configuration hashes match
verifier identity/configuration hashes match
analyzer/module identity matches the frozen contract
descriptor identity and parameters match
complete 64-start cross coverage exists
complete 63-rotation x 64-start self-orbit coverage exists
identity self-pair controls exist and equal the exact expected result (0.0)
all response values and aggregates are finite
no denominator/normalization validity failure occurs
all required result fields are present
canonical serialization succeeds
same-environment replay is byte-identical
canonical output SHA-256 agrees across replay
```

Any failed validity check must produce `PAIR_INVALID` and `INVALID_FAMILY_EVALUATION`; it must **never** be
counted as a failed scientific or strong-hypothesis gate. If some exact field names depend on a future
evaluator schema, the evaluator implementation specification must freeze those field names before execution
and may **not** omit any validity category listed here.

## 12. Numerical tolerance

Existing Brainvision/N64 numerical conventions inspected:

```text
run_prerecorded_paired_analysis_v0_1.py:  EPSILON = 1e-12 (denominator normalization floor, recorded)
                                          NEAR_EPSILON_THRESHOLD = 1e-9 (diagnostic threshold, >= EPSILON)
run_n64_falsifier_v0_1.py:                EPSILON = 1e-12 ; NEAR_EPSILON_THRESHOLD = 1e-9
psi_trs.py (internal):                    _EPS = 1e-8 (descriptor-internal; NOT a comparison band)
N64 self-pair discipline:                 EXACT_FINITE_IN_PROCESS_SELF_PAIR_EQUALITY (exact-zero)
```

These constants are the reused descriptor's internal normalization / diagnostic values; they are not gate
bands, and this specification does **not** reintroduce any of them as a comparison tolerance. Introducing a
fresh nonzero gate band would add an unjustified free parameter that could be tuned after seeing responses.
There is no principled non-zero response scale at which "greater" becomes meaningful, and the N64 self-pair
discipline is already exact. Therefore:

```text
COMPARISON_TOLERANCE = 0.0   (exact finite-float strictly-greater comparison for all §11 strict gates)
```

Requirements (satisfied):

```text
tolerance is frozen in this specification (0.0)
raw unrounded values are emitted
finite checks occur before every comparison (nonfinite -> valid_run = False)
difference <= tolerance (i.e. <= 0.0) counts as equality
equality fails every strict greater-than gate
tolerance cannot be changed after seeing responses
```

Authority and near-tie distinctions:

```text
authoritative operational environment:
  the frozen Windows environment used by the operator

mathematical equality:
  exact equality of integer combinatorial certificates

floating-point replay equality:
  byte-identical canonical serialized output in the same frozen environment

strict gate comparison:
  finite raw float comparison using tolerance 0.0

near-tie diagnostic:
  a separately emitted descriptive margin that neither rescues nor invalidates the formal gate

cross-platform disagreement:
  non-authoritative evidence of numerical fragility; it must be reported and must not silently replace the
  Windows verdict
```

```text
A positive but extremely small margin may formally pass under the frozen 0.0 contract while being explicitly
labeled numerically fragile.

Near-tie reporting is descriptive only and cannot alter the primary Boolean unless a separate non-tunable
invalidation diagnostic is specified and frozen before any response evaluation.

No such invalidation diagnostic is authorized by this v0.1 specification.
```

Windows authority does **not** turn a platform-sensitive near-tie into strong cross-platform evidence; it only
fixes which environment's verdict is authoritative.

## 13. Pair and family verdicts

Pair verdicts (multiple failure flags may be emitted; the primary pass remains a single Boolean):

```text
PAIR_STRONG_PASS
PAIR_FULL_NOT_DUAL_ORBIT_EXTREME
PAIR_K0_ALSO_DUAL_ORBIT_EXTREME
PAIR_RECURSIVE_SIGN_FAILURE
PAIR_INVALID
```

Family verdict:

```text
all 3 pairs pass                          -> STRONG_FAMILY_FALSIFIER_SUCCESS
1 or 2 pairs pass                         -> VALID_MIXED_FAMILY_RESULT
0 pairs pass, with every pair valid       -> STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY
any pair or family validity failure       -> INVALID_FAMILY_EVALUATION
```

The unqualified word "falsified" must **not** be used for broad ΨTRS, temporal-order, vision, or perception
claims. The zero-pass outcome rejects **only** the preregistered strong hypothesis under:

```text
this frozen family ; this N=64 construction ; this evaluator ; this self-shift reference ; this strict F3 contract
```

## 14. Claim boundary

```text
Homometry means an A/B difference cannot be attributed to unequal complete periodic autocorrelation of the
raw circular binary sequences.

It does not establish independence from every finite representation, boundary convention, normalization,
transform geometry, or generic cross-member disruption.

Even a family-wide strict pass would not establish perception, vision, temporal-order detection, a
recursive-time mechanism, scientific superiority, runtime suitability, or production readiness.
```

Theorem boundary (restated):

```text
This specification does not claim a theorem that complete third-order cyclic correlation reconstructs every
binary support up to G. For the N=12 fixture, triple-array G-nonalignment is computationally verified. For
future N=64 candidates, it is an exact verifier predicate. Its general reconstruction power remains unclaimed.
```

Role separation:

```text
N=12 validates the mathematical witness and verification route.
N=64 tests the preregistered Brainvision response contract.
Neither role may be substituted for the other.
```

## 15. Required conclusion

```text
SPECIFICATION_STATUS  = READY_FOR_ADVERSARIAL_DOCUMENT_REVIEW
IMPLEMENTATION_AUTHORIZED = False
```

*End — TORMENT Brainvision Independent Descriptor-Blind Higher-Order Witness Family Implementation
Specification v0.1. Docs-only, non-authorizing, non-implementing. This lane is independent of and non-gating
to the operational harness; it does not alter the original N64 result. `psi_trs.py`, `run_n64_falsifier_v0_1.py`,
and the production TORMENT memory kernel are immutable. No `§0` pointer; no registry or orientation update; no
tags.*

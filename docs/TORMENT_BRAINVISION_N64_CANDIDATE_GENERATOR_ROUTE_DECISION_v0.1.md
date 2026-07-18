# TORMENT Brainvision N=64 Candidate Generator Route Decision v0.1

## 0. Status / authority

**DOCS-ONLY route decision. Non-implementing.** This note records the selected construction route for the
independent descriptor-blind N=64 higher-order witness family. It implements nothing, generates no candidate
stream, searches no witness, installs no dependency, and runs no ΨTRS or descriptor evaluation. It selects a
route; it does **not** freeze the generator implementation (§8) and it authorizes no execution.

```text
FORMAL_HOLD_active = True
Mode_0_active      = True

documentation_authorization            = True
generator_implementation_authorization = False
witness_generation_authorization       = False
PsiTRS_evaluation_authorization         = False
scientific_inference_authorization      = False
```

Prepared after synchronization to `HEAD = a527d2d` (branch `main`, `origin/main = a527d2d`). The tracked
working tree was clean before drafting. At review time the sole working-tree entry is this untracked
route-decision document. Brainvision remains offline, prerecorded, quarantined, service-disconnected,
non-runtime, non-production, and descriptive.

Immutable — never modified or proposed for modification:

```text
research/brainvision/psi_trs.py
research/brainvision/run_n64_falsifier_v0_1.py
torment_service/kernel/
torment_service/memory_kernel.py
torment_service/fabric.py
```

## 1. Governing documents

```text
docs/TORMENT_BRAINVISION_INDEPENDENT_DESCRIPTOR_BLIND_HIGHER_ORDER_WITNESS_FAMILY_IMPLEMENTATION_SPECIFICATION_v0.1.md
docs/TORMENT_BRAINVISION_INDEPENDENT_HIGHER_ORDER_WITNESS_VERIFIER_AND_FREEZE_INFRASTRUCTURE_IMPLEMENTATION_SPECIFICATION_v0.1.md
```

Both remain authoritative and are **not** amended by this document. The accepted independent verifier and
freezer (`witness_family_verifier_v0_1.py`, `witness_family_freeze_v0_1.py`, `witness_canonical_json_v0_1.py`)
remain the sole deciders of every witness predicate and the sole authority for freezing a family.

## 2. Accepted route decision

```text
GENERATOR_ROUTE_REVIEW_DISPOSITION =
  C. SELECT_ALGEBRAIC_PRIMARY

PRIMARY_ROUTE =
  deterministic theorem-backed collision-free direct-sum construction,
  evaluated directly in Z_64

PRIMARY_FORM =
  A = U + V mod 64
  B = U + (-V) mod 64

INITIAL_PRIMARY_PARAMETER_SHAPE =
  |U| = 3
  |V| = 4
  candidate weight = 12

WEIGHT_9_PRIMARY_USE =
  EXCLUDED_FROM_NEW_PRIMARY_FAMILY

WEIGHT_32 =
  EXCLUDED

SMALL_N_FEASIBILITY_PILOT =
  NOT_SELECTED

DEPENDENCY_DECISION =
  NO_NEW_DEPENDENCY

SAT_SMT_STATUS =
  FUTURE_OPTIONAL_ROUTE_NOT_SELECTED

CUSTOM_BACKTRACKING_STATUS =
  OPTIONAL_LOW_WEIGHT_COMPLETENESS_STUDY,
  NOT_FORMAL_CONSTRUCTION_FALLBACK

GENERATOR_FALLBACK_STANDING =
  FALLBACK_HELD_PENDING_PRIMARY_RESULT
```

## 3. Required mathematical boundary

Collision-free packing, for the selected form, may be written in either equivalent form:

```text
all |U|*|V| sums  u + v  are distinct mod 64
all |U|*|V| sums  u - v  are distinct mod 64
```

For fixed `U,V`, these two collision-free statements are equivalent: a collision

```text
u1 + v1 = u2 + v2
```

corresponds, by exchanging the two `V` witnesses, to

```text
u1 - v2 = u2 - v1,
```

and conversely. A future generator may still compute and report both forms explicitly as a deterministic
consistency guard, but they are not independent hypotheses.

When this directness condition holds, `A = U+V` and `B = U-V` are binary supports of weight 12.

The multiplicity-bearing difference multiset of `A` is:

```text
(A-A) = (U-U) + (V-V)
```

while the difference multiset of `B` is:

```text
(B-B) = (U-U) - (V-V).
```

Because `V-V` is symmetric under negation as a multiplicity-bearing multiset, `A` and `B` have equal complete
periodic autocorrelation.

In the accepted binary circular domain, equal complete periodic autocorrelation also entails the equal directed
one-step table and equal absolute transition multiset. These certificates must still be emitted and
independently recomputed by the verifier.

The construction is claimed to guarantee **nothing further**. In particular it does **not** guarantee:

```text
primitive period 64
affine inequivalence
triple-array G-nonalignment
three distinct autocorrelation classes
six-member mutual G-inequivalence
```

Each of those remains an exact predicate of the independent verifier and freezer, recomputed from raw supports.
A candidate is admissible only after that independent recomputation, and a family may be frozen only through
the accepted authoritative replay-gated freeze operation.

## 4. Weight-9 boundary (independence policy)

The previously evaluated N64 fixture was itself a weight-9 direct-sum construction:

```text
U = {0,1,3}
V = {0,4,12}
```

Because that construction shape and its evaluated result are already frozen evidence, the new primary family
begins at **weight 12** to preserve a clean structural separation from prior evaluated evidence.

This exclusion is:

```text
not based on PsiTRS response strength
not a descriptor-derived exclusion
not a claim that all weight-9 pairs are invalid
not a universal mathematical necessity
```

It is an **independence policy for the new family**. Weight 12 is reached by a fixture-blind structural rule
(`|U| = 3, |V| = 4`), so no inspection of prior evidence is required to satisfy it.

A future generator must **not** import, enumerate, inspect, or encode the prior fixture. The parameters above
are recorded here solely as documentation of why the new primary family starts at weight 12; they are not a
seed, an exclusion list to be consulted at runtime, or an input to any generator.

As a standing rule for any future expansion of the algebraic parameter domain, weight 32 remains excluded
because a support and its complement then have equal cardinality, removing cardinality as a structural
separation from complement images. This does not claim that every weight-32 pair is complement-equivalent.

## 5. Route standing

```text
R1 SAT/SMT:
  exact in principle
  unavailable in current dependency posture
  deterministic model enumeration is solver/version-sensitive
  retained only as a future optional route

R2 custom backtracking:
  exact and dependency-free
  useful for bounded low-weight completeness
  realistically exhaustive only below the known productive direct-sum region
  not designated as the construction fallback

R3 direct algebraic:
  selected because homometry holds by construction
  deterministic and dependency-free
  directly auditable
  compatible with the accepted candidate-stream and verifier/freezer
```

R3 is selected because it removes the hardest predicate from the search entirely: equal complete periodic
autocorrelation holds by construction rather than by discovery, leaving a bounded deterministic parameter
enumeration whose remaining predicates are decided independently. It adds no dependency, is re-derivable by an
independent reviewer, and emits candidates that conform to the already-accepted candidate-stream envelope.

## 6. Failure interpretation

```text
generator stream fully completes but freezer obtains fewer than K=3:
  FAMILY_NOT_FREEZABLE

structural enumeration budget reached:
  budget_exhausted

invalid generator configuration or precondition:
  route_incomplete

an algebraic-route negative means only:
  no family was constructed within the frozen direct-sum domain and budget

it never means:
  no valid N64 witness family exists
```

A generator terminal status is not a family verdict, and a family verdict is not a mathematical impossibility
result. An R3 negative is bounded by its construction family, its weight policy, and its frozen budget.

## 7. Route separation

Route identity must remain visible in the generator identity and configuration hashes recorded in every
candidate stream and family manifest. The verifier pair/family certificates remain route-agnostic mathematical
certificates under the accepted schema.

Outputs from different routes may not be combined into a single family unless a future specification explicitly
authorizes that. One family, one route.

## 8. Implementation authorization boundary

This document selects a route. It does **not** freeze the complete implementation. The following are
explicitly deferred to a later implementation specification and are not decided here:

```text
exact parameter-tuple normalization
symmetry-breaking rules
exact deterministic tuple order
exact structural tuple/node/candidate budget
candidate de-duplication policy
generator module and test filenames
complete configuration payload
terminal-record details
performance diagnostics
```

No generator may be implemented, and no N=64 candidate stream may be produced, until that specification is
drafted, adversarially reviewed, and separately authorized.

## 9. Conclusion

```text
DOCUMENTATION_AUTHORIZED = True
GENERATOR_ROUTE_SELECTED = ALGEBRAIC_DIRECT_SUM_Z64
GENERATOR_IMPLEMENTATION_AUTHORIZED = False
N64_WITNESS_GENERATION_AUTHORIZED = False
PsiTRS_EVALUATION_AUTHORIZED = False
SCIENTIFIC_INFERENCE_AUTHORIZED = False
```

*End — TORMENT Brainvision N=64 Candidate Generator Route Decision v0.1. Docs-only, non-authorizing,
non-implementing. Selects a construction route only; freezes no generator, produces no candidate stream,
searches no witness, and makes no scientific claim. The accepted witness-family and verifier/freeze
specifications are unamended and remain authoritative; `psi_trs.py`, `run_n64_falsifier_v0_1.py`, and the
production TORMENT memory kernel are immutable. No `§0` pointer; no registry or orientation update; no tags.*

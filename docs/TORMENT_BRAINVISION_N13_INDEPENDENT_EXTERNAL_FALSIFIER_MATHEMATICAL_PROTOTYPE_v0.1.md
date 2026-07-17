# TORMENT Brainvision N=13 Independent External Falsifier — Mathematical Prototype v0.1

```text
MATHEMATICAL_PROTOTYPE_ONLY
INDEPENDENT_EXTERNAL_FALSIFIER
NOT_KERNEL_DERIVED
NO_LITERAL_Z13_KERNEL_CARRIER
NOT_DESCRIPTOR_COMPATIBLE
NOT_EXPERIMENT_READY
QUOTIENT_CONTINGENT
N64_COMPATIBILITY_UNRESOLVED
NO ΨTRS EVALUATION AUTHORIZED
```

## 1. Authority and status

This is a docs-only mathematical prototype record. It exhibits an exact finite-sequence construction and its
verified properties. It builds nothing, changes no code, and authorizes no evaluation. It is **not** derived
from any TORMENT kernel, is **not** compatible with the current ΨTRS analyzer fixture contract, and is
**not** experiment-ready. Its admissibility as a *nontrivial* falsifier pair is contingent on an unselected
quotient policy (Section 6).

```text
FORMAL_HOLD_active = True
Mode_0_active = True

implementation_authorized = False
experiment_authorized = False
scientific_claim_authorized = False
temporal_order_claim_authorized = False
perception_or_vision_claim_authorized = False
runtime_integration_authorized = False
```

## 2. Subsystem relationship (corrected)

```text
torment_service/kernel/
  = production TORMENT memory/physics subsystem

research/brainvision/psi_trs.py
  = separate offline Brainvision spectral-recursion descriptor

N=13 witness
  = independent external finite-sequence construction
```

- No runtime import relationship exists between the production kernel and the offline Brainvision ΨTRS
  descriptor (`psi_trs.py` is re-derived offline, no service imports).
- No literal thirteen-state carrier, one-hinge-plus-twelve-state object, or `Z_13` arithmetic is
  implemented in ΨTRS.
- The earlier hinge-plus-twelve interpretation is **not** adopted as repository authority; it is an
  analogy only and is not used below.

## 3. Exact mathematical witness

```text
N = 13

A = {0, 1, 3, 9}
B = {0, 2, 5, 6}

B = 2A mod 13
```

Binary characteristic sequences (index 0 … 12; a `1` at each support position):

```text
A = 1 1 0 1 0 0 0 0 0 1 0 0 0
B = 1 0 1 0 0 1 1 0 0 0 0 0 0
```

Exact certificates.

Weights:

```text
weight(A) = weight(B) = 4
```

Complete periodic (circular) autocorrelation, `r_S(k) = |S ∩ (S − k)|`:

```text
r_A(0) = r_B(0) = 4
r_A(k) = r_B(k) = 1   for every nonzero k in Z_13
```

Difference certificate (the twelve ordered differences `a − a'`, `a ≠ a'`, taken mod 13, each nonzero
residue occurring exactly once):

```text
A: 1−0=1  3−1=2  3−0=3  9−0=9→ ... full list:
   {1−0, 3−1, 3−0, 0−9, 1−9, 9−3, 9−1, 9−0, 0−3, 0−1, 1−3, 3−9}
   = {1, 2, 3, 4, 5, 6, 8, 9, 10, 12, 11, 7}
   = {1,2,3,4,5,6,7,8,9,10,11,12}   (each once)

B: {2−0, 5−2, 6−5, 6−2, 5−0, 6−0, 0−6, 0−5, 2−5, 0−2, 2−6, 5−6}
   = {2, 3, 1, 4, 5, 6, 7, 8, 10, 11, 9, 12}
   = {1,2,3,4,5,6,7,8,9,10,11,12}   (each once)
```

Because each nonzero residue occurs exactly once as a difference, both supports are `(13, 4, 1)` **cyclic
difference sets**. They are distinct as supports but are **multiplier-equivalent**: `B = 2A mod 13` (see
Section 6). They are therefore **not** described here as inequivalent difference sets.

## 4. Circular binary S1 / S2 / S3 dependency

Definitions (this scope: real scalar, binary, circular):

```text
S1 = same value multiset
   + same complete periodic autocorrelation

S2 = S1
   + same absolute transition-magnitude multiset

S3 = S2
   + same complete directed one-step transition table
```

For a circular binary sequence of length `N`, weight `w`, with lag-1 autocorrelation `r(1)`, the directed
one-step transition counts are fixed by `(N, w, r(1))` alone:

```text
c11 = r(1)
c10 = w − r(1)
c01 = w − r(1)
c00 = N − 2w + r(1)
```

Since S1 fixes the value multiset (hence `w`) and the complete autocorrelation (hence `r(1)`), in **this
narrow scope**:

```text
S1 ⇒ S2
S1 ⇒ S3
```

For the witness (`N = 13`, `w = 4`, `r(1) = 1`):

```text
c00 = 6
c01 = 3
c10 = 3
c11 = 1
```

This implication is **prohibited from transfer** to:

```text
linear sequences        (boundary/endpoint terms break the count identities)
nonbinary alphabets      (transition table is not a function of (N, w, r(1)) alone)
multichannel sequences   (cross-channel structure is uncontrolled by these scalars)
```

## 5. Exact higher-order distinction

Fixed-lag triple correlation:

```text
T_S(k, l) = | S ∩ (S − k) ∩ (S − l) |
```

Verified at lag pair `(1, 3)`:

```text
T_A(1, 3) = 1     (only t = 0 satisfies t, t+1, t+3 ∈ A)
T_B(1, 3) = 0     (no t satisfies t, t+1, t+3 ∈ B)
```

Demonstrated property:

```text
LABELED_FIXED_LAG_NONLOCAL_TRIPLE_CORRELATION_DIFFERENCE
```

This property is **not** generalized to: generic temporal order; time-reversal asymmetry; contiguous
trigram grammar; scene understanding; perception; causality.

Two structural facts bound the reach of the distinction:

- The complete labeled triple-correlation arrays of A and B differ, but they are related by an **affine lag
  relabeling**:

```text
T_B(k, l) = T_A(7k, 7l) mod 13        (7 = 2^{-1} mod 13)
```

  Consequently any target that is invariant under affine lag relabeling (an unlabeled orbit or the multiset of
  triple-correlation values) is **matched** by this pair and cannot serve as the distinguishing target. The
  same holds for the bispectrum:

```text
Any permutation-invariant aggregate or multiset of bispectral
magnitudes that discards the affine-relabelled frequency/lag
coordinates is matched by this pair. A labeled
bispectral-magnitude array may be relabeled rather than literally
identical.
```

  Only a **labeled**, fixed-lag object separates A and B, and the established distinction remains
  `LABELED_FIXED_LAG_NONLOCAL_TRIPLE_CORRELATION_DIFFERENCE`.

- The circular **contiguous trigram-count histograms are identical**. This witness therefore does **not**
  distinguish local three-symbol motif counts; the distinguishing structure is nonlocal (gapped) triple
  correlation, not contiguous grammar.

## 6. Equivalence and quotient contingency

```text
distinct supports        = True
translation-equivalent   = False
dihedrally equivalent    = False
affine-equivalent        = True
```

The multiplier relationship, with the full verified multiplier coset (each fixes 0, so no translation is
needed):

```text
B = 2A = 5A = 6A   (mod 13)
```

Dihedral inequivalence and affine equivalence are established by a complete affine enumeration (the
multiplier values `{2,5,6}` classify the nonzero multiplier *images*, not the supports as abstract objects):

```text
The nonzero elements of A are {1,3,9}, and the nonzero elements
of B are {2,5,6}.

A complete affine enumeration gives exactly:

(u,a) = (2,0), (5,0), (6,0)

for maps t ↦ ut+a carrying A to B.

No pure translation t ↦ t+a and no reflected translation
t ↦ −t+a maps A to B.

Therefore the supports are translation-inequivalent and
dihedrally inequivalent, while affine-equivalent.
```

```text
The witness survives quotient policies no larger than the dihedral group.
It collapses under an affine index-relabeling quotient.
The project target H and the trivial-equivalence group G remain unselected and mutually dependent.
```

Narrow explanation (no project quotient is selected here):

- A **labeled fixed-lag target** treats affine multiplication `u ≠ ±1` as an order-rearranging transform
  (it does not preserve adjacency or the identity of lag 1), so A and B are genuinely distinct under it.
- An **affine-orbit-invariant target** treats A and B as equivalent and therefore removes the demonstrated
  distinction.

The target and the quotient are two sides of one unresolved decision; neither is made in this record.

## 7. Relationship to ΨTRS

Verified boundary of the offline descriptor (`research/brainvision/psi_trs.py`):

```text
psi_trs.py accepts finite real 2-D descriptor-time arrays (T rows × C channels);

psi_trs_k0 is the kappa = 0 ablation, removing the state-dependent internal-clock warp and the
  desync channel while retaining the spectral recursion and the rho (spectral-spread) features;

the N=13 witness was not generated by ΨTRS and is not a kernel state.
```

Hypothesis only (not a prediction, not a claim):

```text
The external witness may test whether ΨTRS responds to a labeled higher-order arrangement difference
after lower-order circular binary properties (S1/S2/S3) are matched.
```

There is no claim that ΨTRS is expected to separate A and B.

## 8. Role of 64

```text
BLOCK_LEN = 64
```

This is the current prerecorded-analyzer and boundary-neutral-companion fixture contract (the temporal
observation-window length), **not** native ΨTRS mathematics; `psi_trs.py` itself imposes no length of 13,
64, or any phase count.

```text
N = 13 is not directly compatible with the current 64-row analyzer fixture contract.

Zero-padding exposes unequal aperiodic autocorrelation for this pair; simple repetition cannot tile
length 64 because 13 does not divide 64; truncation and interpolation alter the object; concatenation
or embedding currently has no specified exact preservation certificate.

No padding, repetition, truncation, interpolation, concatenation, or embedding is authorized.

This does not rule out an independent exact N=64 witness or a theorem-backed exact lift.

No N=64-compatible witness has been established.
```

Two future mathematical routes are kept open, with no preference and no search authorized:

```text
independent exact N=64 witness
theorem-backed exact construction or lift
```

## 9. Falsifier semantics

```text
no observed ΨTRS separation
  = failure to observe separation under the declared setup;

it is not automatically proof of insensitivity.
```

Future response objects to be reported separately (never merged under one word):

```text
raw psi_trs response
raw psi_trs_k0 response
psi_trs − psi_trs_k0 recursive contribution
O1/A3 boundary-neutral companion response
```

A nonzero response alone must **not** count as success; the meaningful object is the differential across
the declared comparisons, and any apparent separation would additionally have to survive the `psi_trs_k0`,
boundary/start, and construction-artifact checks before it could be read as evidence for the hypothesis in
Section 7.

## 10. Mandatory non-claims

```text
no vision claim
no perception claim
no temporal-order proof
no arrow-of-time claim
no recursive-mechanism validation
no classifier claim
no statistical-significance claim
no generalization claim
no descriptor-readiness claim
no experiment authorization
no runtime integration
```

## 11. Final disposition

```text
prototype_status =
  EXACT_INDEPENDENT_EXTERNAL_MATHEMATICAL_WITNESS

scope =
  REAL_SCALAR_BINARY_CIRCULAR_N13

matched_properties =
  S1_S2_S3

demonstrated_difference =
  LABELED_FIXED_LAG_NONLOCAL_TRIPLE_CORRELATION

quotient_status =
  SURVIVES_TRANSLATION_AND_DIHEDRAL
  COLLAPSES_UNDER_AFFINE

kernel_relationship =
  NOT_KERNEL_DERIVED

descriptor_compatibility =
  FALSE

N64_compatibility =
  UNRESOLVED

implementation_authorized =
  False

experiment_authorized =
  False
```

*End — TORMENT Brainvision N=13 Independent External Falsifier Mathematical Prototype v0.1. Docs-only,
non-authorizing, non-implementing. Not kernel-derived; not descriptor-compatible; not experiment-ready;
admissibility quotient-contingent. No `§0` pointer; no registry or orientation update; no tags.*

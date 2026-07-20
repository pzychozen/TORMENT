"""Independent order-sensitive synthetic-fixture verifier (v0.1).

Pure, integer-only, deterministic mathematics for the S1B synthetic-fixture
infrastructure. Standard-library only. Importing this module is inert: it performs
no filesystem, environment, Git, subprocess, network, or descriptor access, and no
fixture generation. It never imports or calls the challenger descriptor.

Governing documents (committed):
  docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_DESCRIPTOR_CHALLENGER_SPECIFICATION_v0.1.md
  docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_FIXTURE_FREEZE_SPECIFICATION_v0.1.md
  docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_FIXTURE_IMPLEMENTATION_AUTHORIZATION_v0.1.md

This module owns only descriptor-blind mathematics over raw binary circular
supports on Z_64. It does not evaluate the challenger tensor.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

N = 64
REQUIRED_WEIGHT = 9
L3_ENTRY_COUNT = 3906

# Fixed positive-control fixture (from the committed freeze specification).
FIXED_C: Tuple[int, ...] = (0, 25, 55)
FIXED_D: Tuple[int, ...] = (0, 49, 57)
FIXED_H0: Tuple[int, ...] = (0, 10, 18, 25, 40, 48, 49, 55, 57)
FIXED_H1: Tuple[int, ...] = (0, 6, 7, 15, 25, 32, 40, 55, 62)
FIXED_TRIPLE_DISAGREEMENT_COUNT = 288

# Exact first-failure eligibility-rejection vocabulary.
ELIGIBILITY_REJECTION_ORDER: Tuple[str, ...] = (
    "A_CARDINALITY_NOT_9",
    "B_CARDINALITY_NOT_9",
    "IDENTICAL_SUPPORTS",
    "A2_MISMATCH",
    "TRANSITION_TABLE_MISMATCH",
    "AFFINE_EQUIVALENT",
    "AFFINE_COMPLEMENT_EQUIVALENT",
    "TRIPLE_ARRAY_EQUAL",
)

# Fixed-fixture certificate failure codes (S1A §16 vocabulary).
FIXED_FIXTURE_RECONSTRUCTION_FAILURE = "FIXED_FIXTURE_RECONSTRUCTION_FAILURE"
FIXED_FIXTURE_LOWER_ORDER_CERTIFICATE_FAILURE = "FIXED_FIXTURE_LOWER_ORDER_CERTIFICATE_FAILURE"
FIXED_FIXTURE_AFFINE_CERTIFICATE_FAILURE = "FIXED_FIXTURE_AFFINE_CERTIFICATE_FAILURE"
FIXED_FIXTURE_AFFINE_COMPLEMENT_CERTIFICATE_FAILURE = "FIXED_FIXTURE_AFFINE_COMPLEMENT_CERTIFICATE_FAILURE"
FIXED_FIXTURE_TRIPLE_CERTIFICATE_FAILURE = "FIXED_FIXTURE_TRIPLE_CERTIFICATE_FAILURE"


# --------------------------------------------------------------------------- #
# Lazily-memoized constant lookup tables (kept out of import to stay inert)
# --------------------------------------------------------------------------- #

_L3_LAGS: Optional[Tuple[Tuple[int, int], ...]] = None
_U64: Optional[Tuple[int, ...]] = None


def l3_lags() -> Tuple[Tuple[int, int], ...]:
    """Fixed lexicographic L3 lag order: a=1..63, b=1..63, omit b == a (3906)."""
    global _L3_LAGS
    if _L3_LAGS is None:
        _L3_LAGS = tuple((a, b) for a in range(1, N) for b in range(1, N) if b != a)
    return _L3_LAGS


def units_mod_64() -> Tuple[int, ...]:
    """The 32 odd residues mod 64 (the multiplicative units)."""
    global _U64
    if _U64 is None:
        _U64 = tuple(u for u in range(N) if u % 2 == 1)
    return _U64


# --------------------------------------------------------------------------- #
# Support validation and basic conversions
# --------------------------------------------------------------------------- #

def _is_strict_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def normalize_support(support: Any) -> Tuple[int, ...]:
    """Strictly validate a raw support and return a sorted unique tuple.

    A support is a collection of distinct residues in Z_64. Booleans are never
    accepted as integers. Raises ValueError on any malformed input.
    """
    if isinstance(support, (str, bytes, dict)):
        raise ValueError("support must be a sequence of integers, not %s" % type(support).__name__)
    try:
        items = list(support)
    except TypeError:
        raise ValueError("support is not iterable")
    seen = set()
    for element in items:
        if not _is_strict_int(element):
            raise ValueError("support element is not a strict integer: %r" % (element,))
        if not (0 <= element < N):
            raise ValueError("support element out of range 0..63: %r" % (element,))
        if element in seen:
            raise ValueError("support contains a duplicate residue: %r" % (element,))
        seen.add(element)
    return tuple(sorted(seen))


def support_to_binary(support: Any) -> Tuple[int, ...]:
    """Return the 64-entry {0,1} indicator vector of a validated support."""
    normalized = set(normalize_support(support))
    return tuple(1 if i in normalized else 0 for i in range(N))


def weight(support: Any) -> int:
    return len(normalize_support(support))


# --------------------------------------------------------------------------- #
# Lower-order invariants
# --------------------------------------------------------------------------- #

def periodic_autocorrelation(support: Any) -> Tuple[int, ...]:
    """Full periodic second-order autocorrelation A2(d) for d = 0..63."""
    binary = support_to_binary(support)
    out = []
    for d in range(N):
        total = 0
        for i in range(N):
            total += binary[i] * binary[(i + d) % N]
        out.append(total)
    return tuple(out)


def step_one_transition_table(support: Any) -> List[List[int]]:
    """Step-one 2x2 transition counts [[n00,n01],[n10,n11]].

    Rows indexed by x_i in {0,1}; columns by x_(i+1 mod 64) in {0,1}.
    """
    binary = support_to_binary(support)
    table = [[0, 0], [0, 0]]
    for i in range(N):
        a = binary[i]
        b = binary[(i + 1) % N]
        table[a][b] += 1
    return table


def direct_triple_array(support: Any) -> Tuple[int, ...]:
    """Direct labeled third-order triple counts M3(a,b) in fixed L3 order."""
    binary = support_to_binary(support)
    out = []
    for (a, b) in l3_lags():
        total = 0
        for i in range(N):
            if binary[i]:
                total += binary[(i + a) % N] * binary[(i + b) % N]
        out.append(total)
    return tuple(out)


def triple_disagreement_indices(support_a: Any, support_b: Any) -> List[List[int]]:
    """Ordered [a,b] lag pairs where M3 differs between the two supports."""
    m3a = direct_triple_array(support_a)
    m3b = direct_triple_array(support_b)
    lags = l3_lags()
    out = []
    for index, (a, b) in enumerate(lags):
        if m3a[index] != m3b[index]:
            out.append([a, b])
    return out


# --------------------------------------------------------------------------- #
# Transformations and equivalence
# --------------------------------------------------------------------------- #

def affine_support(support: Any, u: int, v: int) -> Tuple[int, ...]:
    """Return the sorted unique affine relabelling {(u*s + v) mod 64}."""
    if not _is_strict_int(u) or not _is_strict_int(v):
        raise ValueError("affine parameters must be strict integers")
    if u % 2 != 1:
        raise ValueError("affine multiplier must be an odd unit modulo 64")
    normalized = normalize_support(support)
    return tuple(sorted({(u * s + v) % N for s in normalized}))


def complement_support(support: Any) -> Tuple[int, ...]:
    """Return the sorted complement Z_64 \\ support."""
    normalized = set(normalize_support(support))
    return tuple(i for i in range(N) if i not in normalized)


def _binary_string(support_set: frozenset) -> str:
    return "".join("1" if i in support_set else "0" for i in range(N))


def _affine_equivalence(support_a: Any, support_b: Any) -> Tuple[bool, Optional[List[int]]]:
    """Return (equivalent, first_mapping) for affine equivalence A -> B."""
    a_set = frozenset(normalize_support(support_a))
    b_set = frozenset(normalize_support(support_b))
    for u in units_mod_64():
        for v in range(N):
            if frozenset((u * s + v) % N for s in a_set) == b_set:
                return True, [u, v]
    return False, None


def _affine_complement_equivalence(support_a: Any, support_b: Any) -> Tuple[bool, Optional[List[Any]]]:
    """Return (equivalent, first_mapping) for affine-plus-complement equivalence."""
    a_set = frozenset(normalize_support(support_a))
    b_set = frozenset(normalize_support(support_b))
    full = frozenset(range(N))
    for u in units_mod_64():
        for v in range(N):
            image = frozenset((u * s + v) % N for s in a_set)
            if image == b_set:
                return True, [u, v, 0]
            if (full - image) == b_set:
                return True, [u, v, 1]
    return False, None


def member_orbit_key(support: Any) -> str:
    """Lexicographically smallest 64-character binary string across the 4096
    transforms (32 units x 64 translations x {identity, complement})."""
    a_set = frozenset(normalize_support(support))
    full = frozenset(range(N))
    best: Optional[str] = None
    for u in units_mod_64():
        for v in range(N):
            image = frozenset((u * s + v) % N for s in a_set)
            candidate = _binary_string(image)
            if best is None or candidate < best:
                best = candidate
            complement = _binary_string(full - image)
            if complement < best:
                best = complement
    return best  # type: ignore[return-value]


def pair_duplicate_key(support_a: Any, support_b: Any) -> Tuple[str, str]:
    """Slot-exchange-invariant pair key: sorted pair of member orbit keys."""
    key_a = member_orbit_key(support_a)
    key_b = member_orbit_key(support_b)
    if key_a <= key_b:
        return (key_a, key_b)
    return (key_b, key_a)


# --------------------------------------------------------------------------- #
# Fixed-fixture verification
# --------------------------------------------------------------------------- #

def _sumset(c: Sequence[int], d: Sequence[int]) -> Tuple[int, ...]:
    return tuple(sorted({(x + y) % N for x in c for y in d}))


def _difference_set(c: Sequence[int], d: Sequence[int]) -> Tuple[int, ...]:
    return tuple(sorted({(x - y) % N for x in c for y in d}))


def _affine_certificate(equivalent: bool, search_space_size: int,
                        first_mapping: Optional[Any]) -> Dict[str, Any]:
    return {
        "equivalent": bool(equivalent),
        "search_space_size": search_space_size,
        "first_equivalence_mapping": first_mapping,
    }


def verify_fixed_fixture() -> Dict[str, Any]:
    """Independently reconstruct and certify the fixed positive-control fixture.

    Returns the canonical ``fixed_fixture`` manifest object (keys in the exact
    S1A order), including a ``validation`` sub-object. All certificates are
    recomputed from the raw supports; the written constants are never trusted.
    """
    failure_code: Optional[str] = None

    reconstructed_h0 = _sumset(FIXED_C, FIXED_D)
    reconstructed_h1 = _difference_set(FIXED_C, FIXED_D)

    support_h0 = normalize_support(reconstructed_h0)
    support_h1 = normalize_support(reconstructed_h1)

    if support_h0 != FIXED_H0 or support_h1 != FIXED_H1:
        failure_code = FIXED_FIXTURE_RECONSTRUCTION_FAILURE
    elif len(support_h0) != REQUIRED_WEIGHT or len(support_h1) != REQUIRED_WEIGHT:
        failure_code = FIXED_FIXTURE_RECONSTRUCTION_FAILURE

    binary_h0 = support_to_binary(support_h0)
    binary_h1 = support_to_binary(support_h1)
    weight_h0 = len(support_h0)
    weight_h1 = len(support_h1)
    a2_h0 = periodic_autocorrelation(support_h0)
    a2_h1 = periodic_autocorrelation(support_h1)
    table_h0 = step_one_transition_table(support_h0)
    table_h1 = step_one_transition_table(support_h1)

    if failure_code is None and (a2_h0 != a2_h1 or table_h0 != table_h1):
        failure_code = FIXED_FIXTURE_LOWER_ORDER_CERTIFICATE_FAILURE

    affine_equivalent, _affine_map = _affine_equivalence(support_h0, support_h1)
    if failure_code is None and affine_equivalent:
        failure_code = FIXED_FIXTURE_AFFINE_CERTIFICATE_FAILURE

    ac_equivalent, _ac_map = _affine_complement_equivalence(support_h0, support_h1)
    if failure_code is None and ac_equivalent:
        failure_code = FIXED_FIXTURE_AFFINE_COMPLEMENT_CERTIFICATE_FAILURE

    disagreement_indices = triple_disagreement_indices(support_h0, support_h1)
    disagreement_count = len(disagreement_indices)
    if failure_code is None and (
            disagreement_count == 0 or disagreement_count != FIXED_TRIPLE_DISAGREEMENT_COUNT):
        failure_code = FIXED_FIXTURE_TRIPLE_CERTIFICATE_FAILURE

    valid = failure_code is None
    validation = {
        "valid": valid,
        "failure_code": failure_code,
        "detail": None,
    }

    key_h0 = member_orbit_key(support_h0)
    key_h1 = member_orbit_key(support_h1)
    pair_key = list(pair_duplicate_key(support_h0, support_h1))

    return {
        "C": list(FIXED_C),
        "D": list(FIXED_D),
        "support_H0": list(support_h0),
        "support_H1": list(support_h1),
        "binary_H0": list(binary_h0),
        "binary_H1": list(binary_h1),
        "weight_H0": weight_h0,
        "weight_H1": weight_h1,
        "A2_H0": list(a2_h0),
        "A2_H1": list(a2_h1),
        "transition_table_H0": table_h0,
        "transition_table_H1": table_h1,
        "affine_inequivalence_certificate": _affine_certificate(affine_equivalent, 2048, _affine_map),
        "affine_complement_inequivalence_certificate": _affine_certificate(ac_equivalent, 4096, _ac_map),
        "triple_disagreement_count": disagreement_count,
        "triple_disagreement_indices": disagreement_indices,
        "member_orbit_key_H0": key_h0,
        "member_orbit_key_H1": key_h1,
        "pair_duplicate_key": pair_key,
        "validation": validation,
    }


# --------------------------------------------------------------------------- #
# Generated-pair eligibility
# --------------------------------------------------------------------------- #

def evaluate_pair_eligibility(support_a: Any, support_b: Any) -> Dict[str, Any]:
    """Ordered first-failure eligibility evaluation over two raw supports.

    Returns a deterministic result. For an ineligible pair exactly one
    ``eligibility_rejection_reason`` from ``ELIGIBILITY_REJECTION_ORDER`` is set.
    For an eligible pair the full evidence certificates are computed.
    """
    a = normalize_support(support_a)
    b = normalize_support(support_b)

    def reject(reason: str) -> Dict[str, Any]:
        return {"eligible": False, "eligibility_rejection_reason": reason}

    if len(a) != REQUIRED_WEIGHT:
        return reject("A_CARDINALITY_NOT_9")
    if len(b) != REQUIRED_WEIGHT:
        return reject("B_CARDINALITY_NOT_9")
    if a == b:
        return reject("IDENTICAL_SUPPORTS")

    a2_a = periodic_autocorrelation(a)
    a2_b = periodic_autocorrelation(b)
    if a2_a != a2_b:
        return reject("A2_MISMATCH")

    table_a = step_one_transition_table(a)
    table_b = step_one_transition_table(b)
    if table_a != table_b:
        return reject("TRANSITION_TABLE_MISMATCH")

    affine_equivalent, _affine_map = _affine_equivalence(a, b)
    if affine_equivalent:
        return reject("AFFINE_EQUIVALENT")

    ac_equivalent, _ac_map = _affine_complement_equivalence(a, b)
    if ac_equivalent:
        return reject("AFFINE_COMPLEMENT_EQUIVALENT")

    disagreement_indices = triple_disagreement_indices(a, b)
    if len(disagreement_indices) == 0:
        return reject("TRIPLE_ARRAY_EQUAL")

    key_a = member_orbit_key(a)
    key_b = member_orbit_key(b)
    if key_a <= key_b:
        pair_key = [key_a, key_b]
    else:
        pair_key = [key_b, key_a]

    return {
        "eligible": True,
        "eligibility_rejection_reason": None,
        "weight_A": len(a),
        "weight_B": len(b),
        "A2_A": list(a2_a),
        "A2_B": list(a2_b),
        "transition_table_A": table_a,
        "transition_table_B": table_b,
        "affine_inequivalence_certificate": _affine_certificate(False, 2048, None),
        "affine_complement_inequivalence_certificate": _affine_certificate(False, 4096, None),
        "triple_disagreement_count": len(disagreement_indices),
        "triple_disagreement_indices": disagreement_indices,
        "member_orbit_key_A": key_a,
        "member_orbit_key_B": key_b,
        "pair_duplicate_key": pair_key,
        "support_A": list(a),
        "support_B": list(b),
        "binary_A": list(support_to_binary(a)),
        "binary_B": list(support_to_binary(b)),
    }

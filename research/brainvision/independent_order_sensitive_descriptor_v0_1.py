"""Independent order-sensitive descriptor v0.1 (Stage S2 implementation).

Pure, integer-exact implementation of the accepted v0.1 challenger descriptor:
the N=64 normalized labeled nondegenerate third-order cyclic correlation tensor.

This module is standard-library only, deterministic, integer-exact, import-inert,
filesystem-independent, environment-independent, and network-disconnected. The
public descriptor entry points accept only a raw binary sequence plus fixed
constants internal to this module. No float enters any descriptor, normalization,
canonicalization, equality, orbit, or classification path. Hashes are transport
identity only and never replace exact signature equality.

Stage S2 scope: descriptor mathematics, canonical signatures, lower-order
diagnostics, and the canonical per-sequence serialization contract. This module
does not read the frozen synthetic manifest, does not evaluate any frozen fixture
or candidate, implements no pair eligibility or synthetic-gate classification,
exposes no CLI or runner, and performs no I/O.
"""

import hashlib
import json
import math

# --------------------------------------------------------------------------- #
# Fixed identity constants
# --------------------------------------------------------------------------- #

N = 64
SCHEMA = "torment-brainvision-independent-order-sensitive-descriptor-result-v0.1"
DESCRIPTOR_ID = "n64-normalized-labeled-third-order-cyclic-correlation-v0.1"
LAG_DOMAIN_ID = "n64-distinct-position-ordered-lag-pairs-lexicographic-v0.1"
ENTRY_COUNT = 3906

# Full ordered failure vocabulary (canonical ordering source). Stage S2 exercises
# only the per-sequence and serialization codes; the remainder are retained as the
# frozen canonical ordering for later stages.
FAILURE_CODES = (
    "INPUT_LENGTH_INVALID",
    "INPUT_ELEMENT_TYPE_INVALID",
    "INPUT_BINARY_DOMAIN_INVALID",
    "DEGENERATE_SEQUENCE",
    "NORMALIZATION_INVALID",
    "INTEGER_BOUND_INVARIANT_FAILURE",
    "LOWER_ORDER_CONTROL_MISMATCH",
    "ROTATION_INVARIANCE_FAILURE",
    "REFLECTION_EQUIVARIANCE_FAILURE",
    "AFFINE_EQUIVARIANCE_FAILURE",
    "COMPLEMENT_ANTISYMMETRY_FAILURE",
    "SELF_ORBIT_CANONICALIZATION_FAILURE",
    "SYNTHETIC_NEGATIVE_CONTROL_FAILURE",
    "SYNTHETIC_POSITIVE_CONTROL_FAILURE",
    "FORBIDDEN_IMPORT_DETECTED",
    "PROHIBITED_EVIDENCE_CONTACT_DETECTED",
    "PRODUCTION_BOUNDARY_VIOLATION",
    "SERIALIZATION_FAILURE",
    "NONFINITE_DIAGNOSTIC",
    "REPLAY_MISMATCH",
    "FROZEN_CANDIDATE_ORDER_MISMATCH",
    "FROZEN_INPUT_IDENTITY_MISMATCH",
    "BENCHMARK_METADATA_LEAKAGE",
    "UNAUTHORIZED_EXECUTION",
)

# Fixed lexicographic lag domain: (a, b) with a, b in 1..63 and a != b.
LAG_DOMAIN = tuple(
    (a, b) for a in range(1, N) for b in range(1, N) if a != b
)
LAG_INDEX = {ab: i for i, ab in enumerate(LAG_DOMAIN)}

# The 32 units of Z_64 (odd residues) and their exact modular inverses.
UNITS = tuple(u for u in range(1, N) if math.gcd(u, N) == 1)
UNIT_INVERSE = {u: pow(u, -1, N) for u in UNITS}

# Lazily-built affine relabeling permutations over the lag domain (one index map
# per unit). Built on first canonicalization to keep module import inert.
_AFFINE_PERMUTATIONS = {}


class DescriptorInputError(ValueError):
    """Raised by exact-compute helpers when the raw input is not admissible.

    Deterministic; carries the canonical failure code and stage. No free-form
    system text is attached.
    """

    def __init__(self, failure_code, failure_stage):
        super().__init__(failure_code)
        self.failure_code = failure_code
        self.failure_stage = failure_stage


# --------------------------------------------------------------------------- #
# Input validation (first-failure order)
# --------------------------------------------------------------------------- #

def validate_input(x):
    """Return (failure_code, failure_stage) for the first violation, else None.

    First-failure order: length, element type, binary domain, degenerate.
    ``bool`` is rejected as a non-strict integer element type.
    """
    if not isinstance(x, (list, tuple)) or len(x) != N:
        return ("INPUT_LENGTH_INVALID", "input_validation")
    for value in x:
        if isinstance(value, bool) or not isinstance(value, int):
            return ("INPUT_ELEMENT_TYPE_INVALID", "input_validation")
    for value in x:
        if value != 0 and value != 1:
            return ("INPUT_BINARY_DOMAIN_INVALID", "input_validation")
    total = 0
    for value in x:
        total += value
    if total == 0 or total == N:
        return ("DEGENERATE_SEQUENCE", "input_validation")
    return None


def _require_admissible(x):
    fault = validate_input(x)
    if fault is not None:
        raise DescriptorInputError(fault[0], fault[1])


# --------------------------------------------------------------------------- #
# Exact integer descriptor mathematics
# --------------------------------------------------------------------------- #

def weight(x):
    """Support weight w = sum(x_i) for an admissible sequence."""
    _require_admissible(x)
    return sum(x)


def centered_sequence(x):
    """Integer-centered sequence z_i = N*x_i - w (exact integers, sum zero)."""
    _require_admissible(x)
    w = sum(x)
    return tuple(N * xi - w for xi in x)


def _rotations(z):
    return [tuple(z[(i + a) % N] for i in range(N)) for a in range(N)]


def _tensor_from_centered(z):
    rot = _rotations(z)
    base = rot[0]
    out = []
    append = out.append
    for a in range(1, N):
        ra = rot[a]
        for b in range(1, N):
            if a == b:
                continue
            rb = rot[b]
            s = 0
            for i in range(N):
                s += base[i] * ra[i] * rb[i]
            append(s)
    return out


def third_order_tensor(x):
    """Raw labeled third-order tensor T_x(a,b) in fixed lag order (3906 ints)."""
    z = centered_sequence(x)
    return tuple(_tensor_from_centered(list(z)))


def normalization_denominator(x):
    """Positive normalization denominator D_x = sum_i abs(z_i)^3."""
    z = centered_sequence(x)
    return sum(abs(zi) ** 3 for zi in z)


def _gcd_all(denominator, numerators):
    g = denominator
    for t in numerators:
        if t:
            g = math.gcd(g, t if t >= 0 else -t)
    return g


def canonical_reduction(x):
    """Return (canonical_denominator, canonical_numerators) via exact gcd reduction.

    Also enforces the exact normalization and integer-bound invariants; raises
    DescriptorInputError with the canonical code/stage on violation (defensive:
    admissible binary input never triggers these by Hoelder's inequality).
    """
    z = list(centered_sequence(x))
    denominator = sum(abs(zi) ** 3 for zi in z)
    if denominator <= 0:
        raise DescriptorInputError("NORMALIZATION_INVALID", "normalization")
    numerators = _tensor_from_centered(z)
    for t in numerators:
        if (t if t >= 0 else -t) > denominator:
            raise DescriptorInputError(
                "INTEGER_BOUND_INVARIANT_FAILURE", "descriptor_invariant")
    g = _gcd_all(denominator, numerators)
    canonical_denominator = denominator // g
    canonical_numerators = tuple(t // g for t in numerators)
    return canonical_denominator, canonical_numerators


# --------------------------------------------------------------------------- #
# Affine action and canonical signatures
# --------------------------------------------------------------------------- #

def _affine_permutations():
    """Tuple of 32 lag-domain permutations, one per unit (built lazily, cached).

    For unit u with inverse u1, position (a,b) draws from (u1*a mod N, u1*b mod N).
    """
    if not _AFFINE_PERMUTATIONS:
        perms = []
        for u in UNITS:
            u1 = UNIT_INVERSE[u]
            perm = tuple(
                LAG_INDEX[((u1 * a) % N, (u1 * b) % N)] for (a, b) in LAG_DOMAIN
            )
            perms.append(perm)
        _AFFINE_PERMUTATIONS["perms"] = tuple(perms)
    return _AFFINE_PERMUTATIONS["perms"]


def _affine_relabeled_vectors(canonical_numerators):
    perms = _affine_permutations()
    return [tuple(canonical_numerators[p] for p in perm) for perm in perms]


def raw_labeled_signature(x):
    """Exact raw labeled signature (canonical_denominator, canonical_numerators)."""
    denom, numerators = canonical_reduction(x)
    return (denom, numerators)


def affine_only_signature(x):
    """Exact affine-only signature: denominator with the lexicographic minimum
    canonical numerator vector across all 32 affine relabelings."""
    denom, numerators = canonical_reduction(x)
    vectors = _affine_relabeled_vectors(numerators)
    return (denom, min(vectors))


def affine_plus_complement_signature(x):
    """Exact affine-plus-complement signature: denominator with the lexicographic
    minimum across every affine relabeling and both signs in {-1, +1}."""
    denom, numerators = canonical_reduction(x)
    vectors = _affine_relabeled_vectors(numerators)
    pool = list(vectors)
    for vec in vectors:
        pool.append(tuple(-value for value in vec))
    return (denom, min(pool))


# --------------------------------------------------------------------------- #
# Lower-order diagnostics (computed independently from raw input)
# --------------------------------------------------------------------------- #

def second_order_autocorrelation(x):
    """Periodic second-order autocorrelation A2(d) = sum_i x_i * x_(i+d), d=0..63."""
    _require_admissible(x)
    return tuple(sum(x[i] * x[(i + d) % N] for i in range(N)) for d in range(N))


def transition_table(x):
    """Step-one periodic 2x2 transition table [[n00,n01],[n10,n11]].

    Counts the transition from each index i to (i+1) mod N, including 63 -> 0.
    """
    _require_admissible(x)
    counts = [[0, 0], [0, 0]]
    for i in range(N):
        counts[x[i]][x[(i + 1) % N]] += 1
    return [[counts[0][0], counts[0][1]], [counts[1][0], counts[1][1]]]


def lower_order_signature(x):
    """Ordered lower-order signature object {N, weight, A2}."""
    return {
        "N": N,
        "weight": weight(x),
        "A2": list(second_order_autocorrelation(x)),
    }


# --------------------------------------------------------------------------- #
# Canonical per-sequence payload and serialization
# --------------------------------------------------------------------------- #

def _empty_valid_validation():
    return {"valid": True, "failure_code": None, "failure_stage": None, "detail": None}


def _invalid_validation(code, stage):
    return {"valid": False, "failure_code": code, "failure_stage": stage, "detail": None}


def _invalid_payload(code, stage):
    payload = {}
    payload["schema"] = SCHEMA
    payload["descriptor_id"] = DESCRIPTOR_ID
    payload["N"] = N
    payload["weight"] = None
    payload["lag_domain_id"] = LAG_DOMAIN_ID
    payload["entry_count"] = ENTRY_COUNT
    payload["canonical_denominator"] = None
    payload["raw_labeled_numerators"] = None
    payload["affine_canonical_numerators"] = None
    payload["affine_complement_canonical_numerators"] = None
    payload["lower_order_signature"] = None
    payload["transition_table"] = None
    payload["validation"] = _invalid_validation(code, stage)
    payload["ordered_failure_codes"] = [code]
    return payload


def descriptor_result(x):
    """Canonical per-sequence descriptor payload (valid or invalid).

    Returns an ordered dict-shaped mapping whose top-level and nested key order
    matches the canonical serialization contract. Input faults are represented as
    a canonical invalid payload (first-failure semantics), never as exceptions.
    """
    fault = validate_input(x)
    if fault is not None:
        return _invalid_payload(fault[0], fault[1])
    try:
        denom, numerators = canonical_reduction(x)
    except DescriptorInputError as exc:
        return _invalid_payload(exc.failure_code, exc.failure_stage)

    affine_vectors = _affine_relabeled_vectors(numerators)
    affine_min = min(affine_vectors)
    complement_pool = list(affine_vectors)
    for vec in affine_vectors:
        complement_pool.append(tuple(-value for value in vec))
    affine_complement_min = min(complement_pool)

    payload = {}
    payload["schema"] = SCHEMA
    payload["descriptor_id"] = DESCRIPTOR_ID
    payload["N"] = N
    payload["weight"] = sum(x)
    payload["lag_domain_id"] = LAG_DOMAIN_ID
    payload["entry_count"] = ENTRY_COUNT
    payload["canonical_denominator"] = denom
    payload["raw_labeled_numerators"] = list(numerators)
    payload["affine_canonical_numerators"] = list(affine_min)
    payload["affine_complement_canonical_numerators"] = list(affine_complement_min)
    payload["lower_order_signature"] = {
        "N": N,
        "weight": sum(x),
        "A2": list(second_order_autocorrelation(x)),
    }
    payload["transition_table"] = transition_table(x)
    payload["validation"] = _empty_valid_validation()
    payload["ordered_failure_codes"] = []
    return payload


def canonical_bytes(x):
    """Canonical UTF-8 JSON bytes for the per-sequence payload.

    UTF-8, no BOM, compact separators, base-10 integers, no NaN/Infinity,
    deterministic key order, exactly one terminal LF. Returns bytes; never writes.
    """
    payload = descriptor_result(x)
    text = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), allow_nan=False)
    return text.encode("utf-8") + b"\n"


def canonical_sha256(x):
    """SHA-256 hex digest of the complete canonical bytes (transport identity only).

    Exact signature equality is never replaced by hash equality.
    """
    return hashlib.sha256(canonical_bytes(x)).hexdigest()

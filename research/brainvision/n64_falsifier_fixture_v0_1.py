"""TORMENT Brainvision exact N=64 homometric falsifier - fixture + certificate module v0.1.

Offline, quarantined, descriptive. Implements exactly the accepted evaluation contract v0.1, implementation
specification v0.1, and mathematical prototype v0.1. Owns ONLY: exact fixture construction, direct scalar
binary (64,1) encoding, lower-order certificates, complete labeled triple arrays, fixture-provenance
inequivalence checks, canonical-sequence hashing, and a deterministic fixture object/hash.

No torment_service import. No psi_trs import. No runtime. No file output. stdlib + numpy only.
"""
from __future__ import annotations

import hashlib
import json
from typing import Dict, List, Tuple

import numpy as np

N: int = 64
U: Tuple[int, ...] = (0, 1, 3)
V: Tuple[int, ...] = (0, 4, 12)
ACCEPTED_MEMBER_A: Tuple[int, ...] = (0, 1, 3, 4, 5, 7, 12, 13, 15)
ACCEPTED_MEMBER_B: Tuple[int, ...] = (0, 1, 3, 52, 53, 55, 60, 61, 63)
FIXTURE_NAME: str = "torment_brainvision_n64_falsifier_fixture"
FIXTURE_VERSION: str = "0.1"
ENCODING: str = "direct_scalar_binary_0_1"


class FixtureError(ValueError):
    """Raised when fixture construction or certification fails an accepted invariant."""


def _canonical_bytes(value: object) -> bytes:
    """UTF-8 canonical JSON bytes (compact, sorted, finite-only) for hashing."""
    return json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def canonical_sequence_sha256(value: object) -> str:
    """SHA-256 hexdigest over the canonical bytes of the bare canonical JSON sequence `value`."""
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _direct_sum(low: Tuple[int, ...], high: Tuple[int, ...]) -> List[int]:
    """Collision-free unique-sum packing in Z_N; returns ascending sorted representatives."""
    sums = [(a + b) % N for a in low for b in high]
    if len(set(sums)) != len(sums):
        raise FixtureError("collision_free_unique_sum_packing failed: U/V sums are not pairwise distinct")
    return sorted(sums)


def build_supports() -> Tuple[List[int], List[int]]:
    """Construct member_A = U+V and member_B = U+(-V) (mod N); validate against accepted supports."""
    neg_v = tuple((-b) % N for b in V)
    member_a = _direct_sum(U, V)
    member_b = _direct_sum(U, neg_v)
    if tuple(member_a) != ACCEPTED_MEMBER_A:
        raise FixtureError("constructed member_A support does not equal accepted member_A")
    if tuple(member_b) != ACCEPTED_MEMBER_B:
        raise FixtureError("constructed member_B support does not equal accepted member_B")
    return member_a, member_b


def encode(support: List[int]) -> np.ndarray:
    """Direct scalar binary 0/1 encoding as a finite (N,1) float field."""
    field = np.zeros((N, 1), dtype=float)
    for s in support:
        field[s, 0] = 1.0
    return field


def periodic_autocorrelation(support: List[int]) -> List[int]:
    """Complete periodic autocorrelation r(k) = |S cap (S-k)| for lag k = 0..N-1 (ascending)."""
    members = set(support)
    return [sum(1 for t in range(N) if t in members and (t + k) % N in members) for k in range(N)]


def directed_one_step_table(support: List[int]) -> Dict[str, int]:
    """Directed one-step transition counts for the circular binary sequence."""
    members = set(support)
    weight = len(support)
    c11 = sum(1 for t in range(N) if t in members and (t + 1) % N in members)
    return {"c00": N - 2 * weight + c11, "c01": weight - c11, "c10": weight - c11, "c11": c11}


def absolute_transition_magnitude_multiset(support: List[int]) -> Dict[str, int]:
    """Multiset of |x[t+1]-x[t]| in {0,1} for the circular binary sequence."""
    members = set(support)
    ones = sum(1 for t in range(N) if (t in members) != ((t + 1) % N in members))
    return {"0": N - ones, "1": ones}


def value_multiset(support: List[int]) -> Dict[str, int]:
    """Multiset of the N binary values."""
    return {"0": N - len(support), "1": len(support)}


def triple_array(support: List[int]) -> List[List[int]]:
    """Complete labeled triple-correlation array T_S(k,l) with ascending k (rows), l (cols); lags mod N."""
    members = set(support)
    array: List[List[int]] = []
    for k in range(N):
        row: List[int] = []
        for l in range(N):
            row.append(
                sum(1 for t in range(N) if t in members and (t + k) % N in members and (t + l) % N in members)
            )
        array.append(row)
    return array


def ordered_disagreement_count(triple_a: List[List[int]], triple_b: List[List[int]]) -> int:
    """Number of ordered lag pairs (k,l) where the labeled triple arrays differ."""
    return sum(1 for k in range(N) for l in range(N) if triple_a[k][l] != triple_b[k][l])


def unlabeled_triple_histogram(triple: List[List[int]]) -> Dict[str, int]:
    """Permutation-invariant histogram of triple-correlation values (keys are stringified integers)."""
    hist: Dict[str, int] = {}
    for row in triple:
        for value in row:
            key = str(value)
            hist[key] = hist.get(key, 0) + 1
    return hist


def _units_mod_n() -> List[int]:
    """Units of Z_N (N = 64 = 2^6): the odd residues."""
    return [u for u in range(N) if u % 2 == 1]


def _is_translate(source: List[int], target: List[int]) -> bool:
    src = set(source)
    tgt = set(target)
    return any(set((x + a) % N for x in src) == tgt for a in range(N))


def _affine_maps(source: List[int], target: List[int]) -> List[Tuple[int, int]]:
    """All affine maps t -> u*t + a (u a unit, a in Z_N) carrying source onto target as a set."""
    src = list(source)
    tgt = set(target)
    maps: List[Tuple[int, int]] = []
    for u in _units_mod_n():
        for a in range(N):
            if set((u * x + a) % N for x in src) == tgt:
                maps.append((u, a))
    return maps


def provenance(member_a: List[int], member_b: List[int]) -> Dict[str, bool]:
    """Fixture-provenance certificates: inequivalence under translation/dihedral/affine/affine+complement."""
    reflected_a = [(-x) % N for x in member_a]
    complement_a = [x for x in range(N) if x not in set(member_a)]
    translation = _is_translate(member_a, member_b)
    dihedral = translation or _is_translate(reflected_a, member_b)
    affine = len(_affine_maps(member_a, member_b)) > 0
    affine_plus_complement = affine or len(_affine_maps(complement_a, member_b)) > 0
    return {
        "translation_equivalent": translation,
        "dihedral_equivalent": dihedral,
        "affine_equivalent": affine,
        "affine_plus_complement_equivalent": affine_plus_complement,
    }


def _fixture_without_hash(fixture: Dict[str, object]) -> Dict[str, object]:
    return {key: value for key, value in fixture.items() if key != "fixture_sha256"}


def build_fixture() -> Dict[str, object]:
    """Deterministic structured fixture object with certificate hashes and a canonical fixture_sha256.

    The complete 64x64 triple arrays are NOT inlined; they are represented by hashes plus required summaries
    (fixed-lag values, ordered disagreement count, unlabeled histograms). The `fixture` object contains no
    `replay` object and no reference back to `fixture_sha256`.
    """
    member_a, member_b = build_supports()

    for field, support in ((encode(member_a), member_a), (encode(member_b), member_b)):
        if field.shape != (N, 1):
            raise FixtureError("encoded field shape is not (64,1)")
        if not np.all(np.isfinite(field)):
            raise FixtureError("encoded field contains nonfinite values")
        if not set(np.unique(field).tolist()).issubset({0.0, 1.0}):
            raise FixtureError("encoded field is not binary 0/1")

    autocorr_a = periodic_autocorrelation(member_a)
    autocorr_b = periodic_autocorrelation(member_b)
    table_a = directed_one_step_table(member_a)
    table_b = directed_one_step_table(member_b)
    trans_a = absolute_transition_magnitude_multiset(member_a)
    trans_b = absolute_transition_magnitude_multiset(member_b)

    lower_order_match = (
        autocorr_a == autocorr_b
        and len(member_a) == len(member_b)
        and table_a == table_b
        and trans_a == trans_b
    )
    lower_order: Dict[str, object] = {
        "weight_A": len(member_a),
        "weight_B": len(member_b),
        "value_multiset_A": value_multiset(member_a),
        "value_multiset_B": value_multiset(member_b),
        "periodic_autocorrelation_A": autocorr_a,
        "periodic_autocorrelation_B": autocorr_b,
        "absolute_transition_magnitude_multiset_A": trans_a,
        "absolute_transition_magnitude_multiset_B": trans_b,
        "directed_one_step_table_A": table_a,
        "directed_one_step_table_B": table_b,
        "lower_order_match": bool(lower_order_match),
    }

    triple_a = triple_array(member_a)
    triple_b = triple_array(member_b)
    histogram_a = unlabeled_triple_histogram(triple_a)
    histogram_b = unlabeled_triple_histogram(triple_b)
    higher_order: Dict[str, object] = {
        "triple_definition": "T_S(k,l) = |{ t in Z64 : t in S, (t+k) mod 64 in S, (t+l) mod 64 in S }|",
        "triple_array_sha256_A": canonical_sequence_sha256(triple_a),
        "triple_array_sha256_B": canonical_sequence_sha256(triple_b),
        "fixed_lag": [4, 12],
        "fixed_lag_value_A": triple_a[4][12],
        "fixed_lag_value_B": triple_b[4][12],
        "ordered_disagreement_count": ordered_disagreement_count(triple_a, triple_b),
        "unlabeled_triple_histogram_A": histogram_a,
        "unlabeled_triple_histogram_B": histogram_b,
        "unlabeled_histogram_match": bool(histogram_a == histogram_b),
    }

    prov = provenance(member_a, member_b)

    if higher_order["fixed_lag_value_A"] != 3 or higher_order["fixed_lag_value_B"] != 0:
        raise FixtureError("fixed-lag (4,12) certificate mismatch (expected A=3, B=0)")
    if higher_order["ordered_disagreement_count"] != 264:
        raise FixtureError("ordered labeled disagreement count is not 264")
    if not higher_order["unlabeled_histogram_match"]:
        raise FixtureError("unlabeled triple histograms differ")
    if not lower_order_match:
        raise FixtureError("lower-order certificates do not match between members")
    if any(prov.values()):
        raise FixtureError("provenance inequivalence violated (a trivial equivalence was found)")

    fixture: Dict[str, object] = {
        "name": FIXTURE_NAME,
        "version": FIXTURE_VERSION,
        "N": N,
        "member_A_support": list(member_a),
        "member_B_support": list(member_b),
        "encoding": ENCODING,
        "lower_order": lower_order,
        "higher_order": higher_order,
        "provenance": prov,
    }
    fixture["fixture_sha256"] = canonical_sequence_sha256(_fixture_without_hash(fixture))
    return fixture

"""Independent order-sensitive synthetic-fixture generator and shared reducer (v0.1).

Pure, deterministic, standard-library-only generation logic for the S1B
synthetic-fixture infrastructure. It depends only on the verifier module and the
Python standard library. Importing this module is inert: it performs no filesystem,
environment, Git, subprocess, network, or descriptor access, and no seed scan.

There is exactly one behavioural implementation of duplicate handling, acceptance
ordering, first-eight stopping, and search-diagnostic reduction; it lives in
``reduce_scan_records``. ``scan_seed_stream`` builds scan records from real seeds
and feeds them through that single reducer.

No zero-argument complete-canonical-scan convenience function is exposed.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple

import independent_order_sensitive_synthetic_fixture_verifier_v0_1 as verifier

N = 64
ACCEPTANCE_LIMIT = 8

SCAN_RECORD_KEYS: Tuple[str, ...] = (
    "seed_tuple",
    "eligible",
    "eligibility_rejection_reason",
    "pair_duplicate_key",
    "fixture_record",
)

FIXTURE_RECORD_KEYS: Tuple[str, ...] = (
    "seed_tuple",
    "C",
    "D",
    "support_A",
    "support_B",
    "binary_A",
    "binary_B",
    "weight_A",
    "weight_B",
    "A2_A",
    "A2_B",
    "transition_table_A",
    "transition_table_B",
    "affine_inequivalence_certificate",
    "affine_complement_inequivalence_certificate",
    "triple_disagreement_count",
    "triple_disagreement_indices",
    "member_orbit_key_A",
    "member_orbit_key_B",
    "pair_duplicate_key",
)

# The reducer's accepted-record wrapper. Acceptance metadata (family_index,
# seed_order_position) is kept strictly OUTSIDE the opaque carried fixture
# record, which is preserved unchanged as a distinct nested sub-object. The
# flat committed S1A manifest accepted-fixture object (freeze specification
# §10.2) is a downstream projection built by the manifest/S1C layer, not by
# this reducer; the reducer never injects, prepends, appends, removes, renames,
# reorders, or otherwise mutates the opaque fixture-record mapping.
ACCEPTED_RECORD_KEYS: Tuple[str, ...] = ("family_index", "seed_order_position", "fixture_record")

SEED_ENUMERATION_FAILURE = "SEED_ENUMERATION_FAILURE"
GENERATOR_CONFIGURATION_INVALID = "GENERATOR_CONFIGURATION_INVALID"


# --------------------------------------------------------------------------- #
# Canonical seed enumeration and pair construction
# --------------------------------------------------------------------------- #

def iter_canonical_seed_tuples() -> Iterator[Tuple[int, int, int, int]]:
    """Lazily yield canonical seed tuples in exact lexicographic order.

    Order: c1 = 1..62, c2 = c1+1..63, d1 = 1..62, d2 = d1+1..63. The first tuple
    is (1, 2, 1, 2). This generator is lazy; it performs no work until iterated.
    """
    for c1 in range(1, 63):
        for c2 in range(c1 + 1, 64):
            for d1 in range(1, 63):
                for d2 in range(d1 + 1, 64):
                    yield (c1, c2, d1, d2)


def _is_strict_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def validate_seed_tuple(seed: Any) -> Dict[str, Any]:
    """First-failure seed-shape validation. Returns a deterministic diagnostic."""
    def bad() -> Dict[str, Any]:
        return {
            "valid": False,
            "failure_code": SEED_ENUMERATION_FAILURE,
            "failure_stage": "seed_validation",
        }
    if not isinstance(seed, tuple):
        return bad()
    if len(seed) != 4:
        return bad()
    for element in seed:
        if isinstance(element, bool):
            return bad()
    for element in seed:
        if not _is_strict_int(element):
            return bad()
    for element in seed:
        if not (1 <= element <= 63):
            return bad()
    c1, c2, d1, d2 = seed
    if c1 >= c2:
        return bad()
    if d1 >= d2:
        return bad()
    return {"valid": True, "failure_code": None, "failure_stage": None}


def construct_pair_from_seed(seed: Tuple[int, int, int, int]) -> Tuple[Tuple[int, ...], Tuple[int, ...]]:
    """Construct (A, B) from a validated seed via C+D and C-D with collision collapse."""
    validation = validate_seed_tuple(seed)
    if not validation["valid"]:
        raise ValueError("construct_pair_from_seed requires a valid seed tuple")
    c1, c2, d1, d2 = seed
    c = (0, c1, c2)
    d = (0, d1, d2)
    a = tuple(sorted({(x + y) % N for x in c for y in d}))
    b = tuple(sorted({(x - y) % N for x in c for y in d}))
    return a, b


# --------------------------------------------------------------------------- #
# Scan-record construction and validation
# --------------------------------------------------------------------------- #

def _build_fixture_record(seed: Tuple[int, int, int, int], eligibility: Dict[str, Any]) -> Dict[str, Any]:
    c1, c2, d1, d2 = seed
    return {
        "seed_tuple": (c1, c2, d1, d2),   # actual tuple: the exact seed-tuple contract
        "C": [0, c1, c2],
        "D": [0, d1, d2],
        "support_A": eligibility["support_A"],
        "support_B": eligibility["support_B"],
        "binary_A": eligibility["binary_A"],
        "binary_B": eligibility["binary_B"],
        "weight_A": eligibility["weight_A"],
        "weight_B": eligibility["weight_B"],
        "A2_A": eligibility["A2_A"],
        "A2_B": eligibility["A2_B"],
        "transition_table_A": eligibility["transition_table_A"],
        "transition_table_B": eligibility["transition_table_B"],
        "affine_inequivalence_certificate": eligibility["affine_inequivalence_certificate"],
        "affine_complement_inequivalence_certificate": eligibility["affine_complement_inequivalence_certificate"],
        "triple_disagreement_count": eligibility["triple_disagreement_count"],
        "triple_disagreement_indices": eligibility["triple_disagreement_indices"],
        "member_orbit_key_A": eligibility["member_orbit_key_A"],
        "member_orbit_key_B": eligibility["member_orbit_key_B"],
        "pair_duplicate_key": tuple(eligibility["pair_duplicate_key"]),
    }


def build_scan_record(seed: Tuple[int, int, int, int], eligibility: Dict[str, Any]) -> Dict[str, Any]:
    """Construct the exact public scan record (ordered mapping) for one seed.

    The public scan record's top-level ``seed_tuple`` is an actual four-integer
    tuple, exactly as the seed-tuple contract requires and as
    ``validate_scan_record`` step 4 enforces without coercion. (The fixture
    record's own ``seed_tuple`` field is the committed manifest array form.)
    """
    c1, c2, d1, d2 = seed
    if eligibility["eligible"]:
        return {
            "seed_tuple": (c1, c2, d1, d2),
            "eligible": True,
            "eligibility_rejection_reason": None,
            "pair_duplicate_key": tuple(eligibility["pair_duplicate_key"]),
            "fixture_record": _build_fixture_record(seed, eligibility),
        }
    return {
        "seed_tuple": (c1, c2, d1, d2),
        "eligible": False,
        "eligibility_rejection_reason": eligibility["eligibility_rejection_reason"],
        "pair_duplicate_key": None,
        "fixture_record": None,
    }


def _valid_binary_key_string(value: Any) -> bool:
    return isinstance(value, str) and len(value) == N and all(ch in "01" for ch in value)


def _valid_pair_key(value: Any) -> bool:
    # Exactly a built-in tuple ``(key_0, key_1)``; no list, other sequence, or
    # tuple subclass is accepted or coerced.
    if type(value) is not tuple or len(value) != 2:
        return False
    key_0, key_1 = value
    if not _valid_binary_key_string(key_0) or not _valid_binary_key_string(key_1):
        return False
    return key_0 < key_1


def _valid_eligible_fixture_record(fixture_record: Any, enclosing_pair_key: Any) -> bool:
    if not isinstance(fixture_record, dict) or len(fixture_record) == 0:
        return False
    if "pair_duplicate_key" not in fixture_record:
        return False
    # Exact equality including representation type: the enclosing key is a
    # validated tuple, so a list with equivalent elements is not equal here.
    return fixture_record["pair_duplicate_key"] == enclosing_pair_key


def validate_scan_record(record: Any) -> Dict[str, Any]:
    """Exact eleven-step first-failure synthetic scan-record validation."""
    def bad() -> Dict[str, Any]:
        return {
            "valid": False,
            "failure_code": GENERATOR_CONFIGURATION_INVALID,
            "failure_stage": "scan_record_validation",
        }
    # 1. record is not an ordered mapping
    if not isinstance(record, dict):
        return bad()
    # 2. key set is not exactly the declared five keys
    if set(record.keys()) != set(SCAN_RECORD_KEYS):
        return bad()
    # 3. key iteration order is not exactly the declared order
    if tuple(record.keys()) != SCAN_RECORD_KEYS:
        return bad()
    # 4. seed_tuple does not satisfy the exact seed-tuple contract.
    # The value is passed through unchanged: the exact contract requires an
    # actual tuple of length four (impl-authorization §6, "the item is not a
    # tuple"). No list is coerced, normalized, copied, or converted; a list
    # therefore fails this step.
    if not validate_seed_tuple(record["seed_tuple"])["valid"]:
        return bad()
    eligible = record["eligible"]
    # 5. eligible is not exactly the JSON-style boolean true or false
    if eligible is not True and eligible is not False:
        return bad()
    if eligible is True:
        # 6. eligible true and eligibility_rejection_reason is not null
        if record["eligibility_rejection_reason"] is not None:
            return bad()
        # 7. eligible true and pair_duplicate_key is malformed
        if not _valid_pair_key(record["pair_duplicate_key"]):
            return bad()
        # 8. eligible true and fixture_record is malformed
        if not _valid_eligible_fixture_record(record["fixture_record"], record["pair_duplicate_key"]):
            return bad()
    else:
        # 9. eligible false and eligibility_rejection_reason is not one canonical reason
        if record["eligibility_rejection_reason"] not in verifier.ELIGIBILITY_REJECTION_ORDER:
            return bad()
        # 10. eligible false and pair_duplicate_key is not null
        if record["pair_duplicate_key"] is not None:
            return bad()
        # 11. eligible false and fixture_record is not null
        if record["fixture_record"] is not None:
            return bad()
    return {"valid": True, "failure_code": None, "failure_stage": None}


# --------------------------------------------------------------------------- #
# The single shared reducer
# --------------------------------------------------------------------------- #

def _empty_rejection_counts() -> Dict[str, int]:
    return {reason: 0 for reason in verifier.ELIGIBILITY_REJECTION_ORDER}


def reduce_scan_records(
    scan_records: Iterable[Dict[str, Any]],
    initial_seen_pair_keys: Iterable[Tuple[str, str]],
    acceptance_limit: int = ACCEPTANCE_LIMIT,
) -> Dict[str, Any]:
    """Single deterministic reducer for duplicate handling, acceptance ordering,
    first-eight stopping, and reduction diagnostics.

    Consumes records lazily; never requests a record after the acceptance limit is
    reached or after a malformed record. On a malformed record it stops immediately
    and returns the prior valid reduction state.
    """
    seen = set(initial_seen_pair_keys)
    accepted: List[Dict[str, Any]] = []
    accepted_seed_order_positions: List[int] = []
    rejection_counts = _empty_rejection_counts()
    eligible_duplicate_count = 0
    records_consumed = 0
    index = 0  # seed-order position of the next successfully-processed record

    iterator = iter(scan_records)
    while len(accepted) < acceptance_limit:
        try:
            record = next(iterator)
        except StopIteration:
            break
        records_consumed += 1
        validation = validate_scan_record(record)
        if not validation["valid"]:
            return {
                "valid": False,
                "failure_code": GENERATOR_CONFIGURATION_INVALID,
                "failure_stage": "scan_record_validation",
                "accepted_records": accepted,
                "accepted_seed_order_positions": accepted_seed_order_positions,
                "eligibility_rejection_counts": rejection_counts,
                "eligible_duplicate_count": eligible_duplicate_count,
                "records_consumed": records_consumed,
                "reached_acceptance_limit": False,
            }
        if record["eligible"] is True:
            # Already validated as an exact tuple; used without coercion.
            pair_key = record["pair_duplicate_key"]
            if pair_key in seen:
                eligible_duplicate_count += 1
            else:
                seen.add(pair_key)
                # Preserve the complete fixture record unchanged as opaque
                # carried data. Acceptance metadata is kept strictly outside the
                # opaque mapping in a separate accepted-record wrapper; the
                # fixture record itself is referenced without injection,
                # prepending, appending, removal, renaming, reordering, or any
                # mutation of its keys, order, values, or nested values.
                accepted_record = {
                    "family_index": len(accepted),
                    "seed_order_position": index,
                    "fixture_record": record["fixture_record"],
                }
                accepted.append(accepted_record)
                accepted_seed_order_positions.append(index)
        else:
            rejection_counts[record["eligibility_rejection_reason"]] += 1
        index += 1

    return {
        "valid": True,
        "failure_code": None,
        "failure_stage": None,
        "accepted_records": accepted,
        "accepted_seed_order_positions": accepted_seed_order_positions,
        "eligibility_rejection_counts": rejection_counts,
        "eligible_duplicate_count": eligible_duplicate_count,
        "records_consumed": records_consumed,
        "reached_acceptance_limit": len(accepted) >= acceptance_limit,
    }


# --------------------------------------------------------------------------- #
# Seed-stream scanning (real pipeline feeding the single reducer)
# --------------------------------------------------------------------------- #

def fixed_fixture_pair_key() -> Tuple[str, str]:
    """The canonical fixed-fixture pair duplicate key (seed for seen_pair_keys)."""
    return verifier.pair_duplicate_key(verifier.FIXED_H0, verifier.FIXED_H1)


def scan_seed_stream(
    seed_iterable: Iterable[Tuple[int, int, int, int]],
    initial_seen_pair_keys: Optional[Iterable[Tuple[str, str]]] = None,
) -> Dict[str, Any]:
    """Scan an explicit iterable of seed tuples through the real mathematical
    pipeline and the single ``reduce_scan_records`` reducer.

    Each valid seed is run through construct_pair_from_seed, evaluate_pair_eligibility,
    pair_duplicate_key, scan-record construction, and reduction. A malformed seed
    stops the scan with a deterministic SEED_ENUMERATION_FAILURE diagnostic without
    constructing supports, evaluating eligibility, constructing a scan record,
    accepting a fixture, or raising the process exception.
    """
    if initial_seen_pair_keys is None:
        initial_seen_pair_keys = [fixed_fixture_pair_key()]

    state: Dict[str, Any] = {
        "total_seeds_visited": 0,
        "terminal_seed_tuple": None,
        "seed_failure": None,
    }

    def record_generator() -> Iterator[Dict[str, Any]]:
        for seed in seed_iterable:
            state["total_seeds_visited"] += 1
            state["terminal_seed_tuple"] = list(seed) if isinstance(seed, (list, tuple)) else seed
            # Validate the supplied item exactly as received: no coercion. A list
            # (or any non-tuple) fails the exact seed-tuple contract here, before
            # any support construction, eligibility evaluation, pair-key
            # calculation, scan-record construction, or reducer consumption of it.
            seed_validation = validate_seed_tuple(seed)
            if not seed_validation["valid"]:
                state["seed_failure"] = seed_validation
                return
            seed_tuple = seed
            support_a, support_b = construct_pair_from_seed(seed_tuple)
            eligibility = verifier.evaluate_pair_eligibility(support_a, support_b)
            yield build_scan_record(seed_tuple, eligibility)

    reduction = reduce_scan_records(record_generator(), initial_seen_pair_keys, ACCEPTANCE_LIMIT)

    base = {
        "accepted_records": reduction["accepted_records"],
        "eligibility_rejection_counts": reduction["eligibility_rejection_counts"],
        "eligible_duplicate_count": reduction["eligible_duplicate_count"],
        "accepted_seed_order_positions": reduction["accepted_seed_order_positions"],
        "total_seeds_visited": state["total_seeds_visited"],
        "terminal_seed_tuple": state["terminal_seed_tuple"],
    }

    if not reduction["valid"]:
        return {
            "valid": False,
            "failure_code": reduction["failure_code"],
            "failure_stage": reduction["failure_stage"],
            **base,
        }

    if state["seed_failure"] is not None:
        return {
            "valid": False,
            "failure_code": SEED_ENUMERATION_FAILURE,
            "failure_stage": "seed_validation",
            **base,
        }

    reached_eight = len(reduction["accepted_records"]) >= ACCEPTANCE_LIMIT
    terminal_status = "ACCEPTED_EIGHT" if reached_eight else "SEED_SPACE_EXHAUSTED"
    search_diagnostics = {
        "total_seeds_visited": state["total_seeds_visited"],
        "eligibility_rejection_counts": reduction["eligibility_rejection_counts"],
        "eligible_duplicate_count": reduction["eligible_duplicate_count"],
        "accepted_seed_order_positions": reduction["accepted_seed_order_positions"],
        "terminal_seed_tuple": state["terminal_seed_tuple"],
        "terminal_status": terminal_status,
    }
    return {
        "valid": True,
        "failure_code": None,
        "failure_stage": None,
        "accepted_records": reduction["accepted_records"],
        "search_diagnostics": search_diagnostics,
    }

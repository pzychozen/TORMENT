"""TORMENT Brainvision algebraic direct-sum N=64 candidate generator v0.1 (offline; descriptor-blind).

Deterministic, dependency-free candidate generator implementing exactly:
  docs/TORMENT_BRAINVISION_ALGEBRAIC_DIRECT_SUM_N64_CANDIDATE_GENERATOR_IMPLEMENTATION_SPECIFICATION_v0.1.md

Route: A = U + V mod 64, B = U + (-V) mod 64, with |U| = 3, |V| = 4, candidate weight 12. The construction is
relied upon for exactly one property (equal complete periodic autocorrelation of A and B) and claims nothing
else: primitive period, affine / affine-plus-complement inequivalence, direct-complement status, triple-array
G-nonalignment, family uniqueness, and every pair/family validity decision remain exclusively the independent
verifier's and freezer's to recompute. This module is NOT a verifier.

Offline, prerecorded, quarantined, service-disconnected, non-runtime, non-production, descriptor-blind. The
only project-local import is the zero-witness-mathematics canonical serializer; everything else is stdlib. No
ΨTRS, descriptor, SAG, verifier, freezer, N64-evaluator, operational-harness, or torment_service contact
exists anywhere in this module.
"""
from __future__ import annotations

import ast
import os
from itertools import combinations
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

import witness_canonical_json_v0_1 as cjson

# --------------------------------------------------------------------- 1. constants and frozen identities
GENERATOR_NAME = "brainvision-algebraic-direct-sum-z64-candidate-generator-v0.1"
GENERATOR_VERSION = "0.1"
ROUTE_IDENTITY = "ALGEBRAIC_DIRECT_SUM_Z64"

N = 64
U_SIZE = 3
V_SIZE = 4
CANDIDATE_WEIGHT = 12

PRIMARY_PROFILE = "PRIMARY_V0_1"
TEST_PROFILE = "TEST_TINY_V0_1"

NORMALIZED_U_COUNT = 651
TRANSLATION_NORMALIZED_V_COUNT = 9936
NEGATION_FIXED_V_COUNT = 496
SIGN_REDUCED_V_COUNT = 5216
NORMALIZED_PARAMETER_DOMAIN_SIZE = 3_395_616

PARAMETER_ORDER_IDENTITY = "V_LEXICOGRAPHIC_OUTER_U_LEXICOGRAPHIC_INNER"
VERIFICATION_MODE = "PRIMARY_CANDIDATE_N64"

STREAM_SCHEMA_NAME = "brainvision_descriptor_blind_candidate_stream"
STREAM_SCHEMA_VERSION = "0.1"
IDENTITY_SCHEMA_NAME = "brainvision_generator_identity"
CONFIGURATION_SCHEMA_NAME = "brainvision_generator_configuration"
BUDGET_SCHEMA_NAME = "brainvision_generator_structural_budget"
SOURCE_IDENTITY_SCHEMA_NAME = "brainvision_generator_source_identity"
RUN_RESULT_SCHEMA_NAME = "brainvision_generator_run_result"
REPLAY_RESULT_SCHEMA_NAME = "brainvision_generator_replay_result"
SCHEMA_VERSION = "0.1"

TERMINATION_PRECEDENCE = ("DOMAIN_EXHAUSTED", "MAX_CANDIDATE_RECORDS_EMITTED", "MAX_PARAMETER_TUPLES_EXAMINED")

STREAM_COMPLETED = "stream_completed"
BUDGET_EXHAUSTED = "budget_exhausted"
ROUTE_INCOMPLETE = "route_incomplete"
DEPENDENCY_UNAVAILABLE = "dependency_unavailable"

# failure codes (aligned with the accepted infrastructure where semantics match)
GENERATOR_CONFIGURATION_INVALID = "GENERATOR_CONFIGURATION_INVALID"
HASH_IDENTITY_FAILURE = "HASH_IDENTITY_FAILURE"
SERIALIZATION_FAILURE = "SERIALIZATION_FAILURE"
FORBIDDEN_IMPORT_DETECTED = "FORBIDDEN_IMPORT_DETECTED"
REPLAY_MISMATCH = "REPLAY_MISMATCH"
GENERATOR_DIRECTNESS_CONSISTENCY_DISAGREEMENT = "GENERATOR_DIRECTNESS_CONSISTENCY_DISAGREEMENT"
GENERATOR_SUPPORT_NORMALIZATION_FAILURE = "GENERATOR_SUPPORT_NORMALIZATION_FAILURE"
GENERATOR_INDEX_ORDER_FAILURE = "GENERATOR_INDEX_ORDER_FAILURE"
GENERATOR_COUNTER_INCONSISTENCY = "GENERATOR_COUNTER_INCONSISTENCY"
GENERATOR_UNEXPECTED_DEPENDENCY_UNAVAILABLE = "GENERATOR_UNEXPECTED_DEPENDENCY_UNAVAILABLE"

_EXPECTED_GENERATOR_MODULE = "algebraic_direct_sum_n64_candidate_generator_v0_1.py"
_EXPECTED_SERIALIZER_MODULE = "witness_canonical_json_v0_1.py"
_BRAINVISION_RELATIVE = ("research", "brainvision")

_ALLOWED_GENERATOR_IMPORT_ROOTS = frozenset(
    {"__future__", "ast", "os", "itertools", "typing", "witness_canonical_json_v0_1"})
_ALLOWED_SERIALIZER_IMPORT_ROOTS = frozenset({"__future__", "hashlib", "json", "typing"})
_PROJECT_LOCAL_ALLOWED = frozenset({"witness_canonical_json_v0_1"})

_COUNTER_KEYS = ("parameter_tuples_examined", "colliding_parameter_tuples_rejected", "direct_tuples_found",
                 "exact_duplicate_candidates_skipped", "candidate_records_emitted")

_SENTINEL = object()


# --------------------------------------------------------------------- 2. narrowly scoped internal errors
class _GeneratorError(Exception):
    """Base for narrowly scoped internal errors. Class names are never serialized."""

    failure_code = GENERATOR_CONFIGURATION_INVALID

    def __init__(self, failure_code: str, stage: str) -> None:
        super().__init__(failure_code)
        self.failure_code = failure_code
        self.stage = stage


class GeneratorIdentityError(_GeneratorError):
    """Identity or source-hash establishment failed."""


class GeneratorConfigurationError(_GeneratorError):
    """Configuration or budget payload construction failed."""


class GeneratorSerializationError(_GeneratorError):
    """Canonical serialization or hashing failed."""


class GeneratorInvariantError(_GeneratorError):
    """A structural invariant of the enumeration was violated."""


# --------------------------------------------------------------------- 3. strict validation / failure helpers
def is_strict_int(value: object) -> bool:
    """True iff value is an int and NOT a bool."""
    return isinstance(value, int) and not isinstance(value, bool)


def _failure_record(failure_code: str, stage: str) -> Dict[str, object]:
    return {"failure_code": failure_code, "stage": stage, "ordered_failure_codes": [failure_code]}


def _zero_counters() -> Dict[str, int]:
    return {key: 0 for key in _COUNTER_KEYS}


def _payload_hash(payload: object, stage: str) -> str:
    try:
        digest = cjson.payload_sha256(payload)
    except (ValueError, TypeError) as error:  # narrow: canonical serialization failure only
        raise GeneratorSerializationError(SERIALIZATION_FAILURE, stage) from error
    if not cjson.is_lower_hex_64(digest):
        raise GeneratorIdentityError(HASH_IDENTITY_FAILURE, stage)
    return digest


def _build_envelope(name: str, payload: object, stage: str) -> Dict[str, object]:
    try:
        return cjson.envelope(name, payload)
    except (ValueError, TypeError) as error:
        raise GeneratorSerializationError(SERIALIZATION_FAILURE, stage) from error


def _dependency_probe() -> Optional[str]:
    """Stdlib-only route: always available. Tests patch this to force the schema-compatible branch."""
    return None


# --------------------------------------------------------------------- 4. source-path ownership and hashing
def _repository_root() -> str:
    here = os.path.dirname(os.path.realpath(__file__))
    return os.path.dirname(os.path.dirname(here))


def default_generator_source_path() -> str:
    return os.path.join(_repository_root(), *_BRAINVISION_RELATIVE, _EXPECTED_GENERATOR_MODULE)


def default_serializer_source_path() -> str:
    return os.path.join(_repository_root(), *_BRAINVISION_RELATIVE, _EXPECTED_SERIALIZER_MODULE)


def _contained(child: str, parent: str) -> bool:
    try:
        return os.path.commonpath([parent, child]) == parent
    except ValueError:
        return False


def _validated_source(path: Optional[str], expected_module: str, stage: str) -> Tuple[str, str]:
    """Resolve and own-check a source path; return (repository_relative_path, sha256_of_raw_bytes)."""
    if path is None:
        path = os.path.join(_repository_root(), *_BRAINVISION_RELATIVE, expected_module)
    if not isinstance(path, str):
        raise GeneratorIdentityError(GENERATOR_CONFIGURATION_INVALID, stage)
    root = os.path.realpath(_repository_root())
    brainvision = os.path.realpath(os.path.join(root, *_BRAINVISION_RELATIVE))
    resolved = os.path.realpath(path)
    if not os.path.isfile(resolved):
        raise GeneratorIdentityError(GENERATOR_CONFIGURATION_INVALID, stage)
    if not _contained(resolved, root) or not _contained(resolved, brainvision):
        raise GeneratorIdentityError(GENERATOR_CONFIGURATION_INVALID, stage)
    if resolved != os.path.realpath(os.path.join(brainvision, expected_module)):
        raise GeneratorIdentityError(GENERATOR_CONFIGURATION_INVALID, stage)
    try:
        digest = cjson.source_file_sha256(resolved)
    except OSError as error:
        raise GeneratorIdentityError(HASH_IDENTITY_FAILURE, stage) from error
    if not cjson.is_lower_hex_64(digest):
        raise GeneratorIdentityError(HASH_IDENTITY_FAILURE, stage)
    return "/".join(("research", "brainvision", expected_module)), digest


# --------------------------------------------------------------------- 5. identity / configuration / budget
def generator_identity_payload(generator_source_path: Optional[str] = None,
                               serializer_source_path: Optional[str] = None) -> Dict[str, object]:
    """Validate both paths, compute both raw-source SHA-256 identities, return the exact identity payload.

    Raises GeneratorIdentityError carrying HASH_IDENTITY_FAILURE or GENERATOR_CONFIGURATION_INVALID on failure.
    The exception never escapes the public run/replay operations.
    """
    generator_relative, generator_digest = _validated_source(
        generator_source_path, _EXPECTED_GENERATOR_MODULE, "generator_identity")
    serializer_relative, serializer_digest = _validated_source(
        serializer_source_path, _EXPECTED_SERIALIZER_MODULE, "generator_identity")
    return {
        "schema_name": IDENTITY_SCHEMA_NAME, "schema_version": SCHEMA_VERSION,
        "generator_name": GENERATOR_NAME, "generator_version": GENERATOR_VERSION,
        "route_identity": ROUTE_IDENTITY,
        "generator_source_path": generator_relative, "generator_source_sha256": generator_digest,
        "serializer_source_path": serializer_relative, "serializer_source_sha256": serializer_digest,
    }


def source_identity_payload(generator_source_path: Optional[str] = None,
                            serializer_source_path: Optional[str] = None) -> Dict[str, object]:
    generator_relative, generator_digest = _validated_source(
        generator_source_path, _EXPECTED_GENERATOR_MODULE, "source_identity")
    serializer_relative, serializer_digest = _validated_source(
        serializer_source_path, _EXPECTED_SERIALIZER_MODULE, "source_identity")
    return {
        "schema_name": SOURCE_IDENTITY_SCHEMA_NAME, "schema_version": SCHEMA_VERSION,
        "generator_source_path": generator_relative, "generator_source_sha256": generator_digest,
        "serializer_source_path": serializer_relative, "serializer_source_sha256": serializer_digest,
    }


def generator_configuration_payload() -> Dict[str, object]:
    return {
        "schema_name": CONFIGURATION_SCHEMA_NAME, "schema_version": SCHEMA_VERSION,
        "N": N, "u_size": U_SIZE, "v_size": V_SIZE, "candidate_weight": CANDIDATE_WEIGHT,
        "verification_mode": VERIFICATION_MODE,
        "parameter_order_identity": PARAMETER_ORDER_IDENTITY,
        "translation_normalization": "TRANSLATION_NORMAL_FORM",
        "v_sign_normalization": "V_LEQ_LEX_TNF_NEG_V",
        "u_v_role_separation": True,
        "unit_affine_normalization": False,
        "generator_side_g_orbit_suppression": False,
        "complement_suppression": False,
        "deduplication_policy": "EXACT_ORIENTED_RAW_PAIR_ONLY",
        "orientation_rule": "LEXICOGRAPHICALLY_SMALLER_RAW_SUPPORT_IS_A",
        "diagnostics_policy": "HASHED_UNTRUSTED_PREDICATE_INERT",
        "worker_count": 1, "randomness_enabled": False, "random_seed": 0,
        "serializer_name": cjson.SERIALIZER_NAME, "serializer_version": cjson.SERIALIZER_VERSION,
    }


def structural_budget_payload(profile_name: str) -> Dict[str, object]:
    if profile_name == PRIMARY_PROFILE:
        max_tuples, max_records = NORMALIZED_PARAMETER_DOMAIN_SIZE, 20_000
    elif profile_name == TEST_PROFILE:
        max_tuples, max_records = 64, 4
    else:
        raise GeneratorConfigurationError(GENERATOR_CONFIGURATION_INVALID, "structural_budget")
    return {
        "schema_name": BUDGET_SCHEMA_NAME, "schema_version": SCHEMA_VERSION,
        "profile_name": profile_name,
        "normalized_parameter_domain_size": NORMALIZED_PARAMETER_DOMAIN_SIZE,
        "max_parameter_tuples_examined": max_tuples,
        "max_candidate_records_emitted": max_records,
        "termination_precedence": list(TERMINATION_PRECEDENCE),
    }


# --------------------------------------------------------------------- 6. translation / V-sign normalization
def translation_normal_form(support: Sequence[int]) -> Tuple[int, ...]:
    """Lexicographically smallest ascending translated tuple over translations anchored by members."""
    if not isinstance(support, (tuple, list)) or len(support) == 0:
        raise GeneratorInvariantError(GENERATOR_SUPPORT_NORMALIZATION_FAILURE, "translation_normal_form")
    seen = set()
    for value in support:
        if not is_strict_int(value) or value < 0 or value >= N or value in seen:
            raise GeneratorInvariantError(GENERATOR_SUPPORT_NORMALIZATION_FAILURE, "translation_normal_form")
        seen.add(value)
    best: Optional[Tuple[int, ...]] = None
    for anchor in support:
        candidate = tuple(sorted((value - anchor) % N for value in support))
        if best is None or candidate < best:
            best = candidate
    return best  # type: ignore[return-value]


def negated_normal_form(support: Sequence[int]) -> Tuple[int, ...]:
    return translation_normal_form(tuple((-value) % N for value in support))


# --------------------------------------------------------------------- 7. deterministic representative sets
def canonical_u_representatives() -> Tuple[Tuple[int, ...], ...]:
    """Ascending-lexicographic canonical |U|=3 translation representatives (every TNF contains 0)."""
    return tuple(candidate for candidate in ((0,) + rest for rest in combinations(range(1, N), U_SIZE - 1))
                 if translation_normal_form(candidate) == candidate)


def translation_normalized_v_representatives() -> Tuple[Tuple[int, ...], ...]:
    """Ascending-lexicographic canonical |V|=4 translation representatives, before sign reduction."""
    return tuple(candidate for candidate in ((0,) + rest for rest in combinations(range(1, N), V_SIZE - 1))
                 if translation_normal_form(candidate) == candidate)


def sign_reduced_v_representatives(
        translation_normalized: Optional[Sequence[Tuple[int, ...]]] = None) -> Tuple[Tuple[int, ...], ...]:
    """Retain V iff V <= translation_normal_form(-V), removing the U+V / U-V exchange duplicate."""
    source = translation_normalized if translation_normalized is not None \
        else translation_normalized_v_representatives()
    return tuple(candidate for candidate in source if candidate <= negated_normal_form(candidate))


def negation_fixed_v_count(translation_normalized: Optional[Sequence[Tuple[int, ...]]] = None) -> int:
    source = translation_normalized if translation_normalized is not None \
        else translation_normalized_v_representatives()
    return sum(1 for candidate in source if candidate == negated_normal_form(candidate))


def parameter_domain_counts() -> Dict[str, int]:
    """Recompute every normalized-domain cardinality from the enumerators (count-regression surface)."""
    u_reps = canonical_u_representatives()
    v_translation = translation_normalized_v_representatives()
    v_sign = sign_reduced_v_representatives(v_translation)
    return {
        "normalized_u_count": len(u_reps),
        "translation_normalized_v_count": len(v_translation),
        "negation_fixed_v_count": negation_fixed_v_count(v_translation),
        "sign_reduced_v_count": len(v_sign),
        "normalized_parameter_domain_size": len(u_reps) * len(v_sign),
    }


def _parameter_tuples(v_representatives: Sequence[Tuple[int, ...]],
                      u_representatives: Sequence[Tuple[int, ...]]
                      ) -> Iterator[Tuple[Tuple[int, ...], Tuple[int, ...]]]:
    """Lazy frozen traversal: V lexicographic outer, U lexicographic inner. Never materialized."""
    for v_tuple in v_representatives:
        for u_tuple in u_representatives:
            yield (v_tuple, u_tuple)


def _frozen_domain_iterator() -> Iterator[Tuple[Tuple[int, ...], Tuple[int, ...]]]:
    u_reps = canonical_u_representatives()
    v_reps = sign_reduced_v_representatives()
    if len(u_reps) != NORMALIZED_U_COUNT or len(v_reps) != SIGN_REDUCED_V_COUNT:
        raise GeneratorInvariantError(GENERATOR_COUNTER_INCONSISTENCY, "frozen_domain")
    return _parameter_tuples(v_reps, u_reps)


# --------------------------------------------------------------------- 8. directness and construction
def directness(u_tuple: Sequence[int], v_tuple: Sequence[int]) -> Tuple[bool, bool, int, int]:
    """Independently compute both directness forms. Returns (sum_direct, difference_direct, |sums|, |diffs|)."""
    sum_values = [(u + v) % N for u in u_tuple for v in v_tuple]
    difference_values = [(u - v) % N for u in u_tuple for v in v_tuple]
    sum_distinct = len(set(sum_values))
    difference_distinct = len(set(difference_values))
    return (sum_distinct == CANDIDATE_WEIGHT, difference_distinct == CANDIDATE_WEIGHT,
            sum_distinct, difference_distinct)


def _validate_constructed_support(support: List[int]) -> None:
    if len(support) != CANDIDATE_WEIGHT:
        raise GeneratorInvariantError(GENERATOR_SUPPORT_NORMALIZATION_FAILURE, "candidate_support")
    previous = -1
    for value in support:
        if not is_strict_int(value) or value < 0 or value >= N or value <= previous:
            raise GeneratorInvariantError(GENERATOR_SUPPORT_NORMALIZATION_FAILURE, "candidate_support")
        previous = value


def construct_oriented_pair(u_tuple: Sequence[int],
                            v_tuple: Sequence[int]) -> Tuple[List[int], List[int]]:
    """Build the weight-12 supports and orient them (lexicographically smaller raw support is A)."""
    sum_support = sorted({(u + v) % N for u in u_tuple for v in v_tuple})
    difference_support = sorted({(u - v) % N for u in u_tuple for v in v_tuple})
    _validate_constructed_support(sum_support)
    _validate_constructed_support(difference_support)
    if sum_support <= difference_support:
        return sum_support, difference_support
    return difference_support, sum_support


# --------------------------------------------------------------------- 9. candidate-stream generation core
def _generate_core(parameter_iterable: Iterable[Tuple[Tuple[int, ...], Tuple[int, ...]]],
                   max_parameter_tuples_examined: int,
                   max_candidate_records_emitted: int
                   ) -> Tuple[List[Dict[str, object]], Dict[str, int], str, str]:
    """Pure deterministic core. Returns (records, counters, terminal_status, termination_reason)."""
    iterator = iter(parameter_iterable)
    records: List[Dict[str, object]] = []
    counters = _zero_counters()
    emitted_pairs = set()
    terminal_status: Optional[str] = None
    termination_reason: Optional[str] = None

    pending = next(iterator, _SENTINEL)
    while pending is not _SENTINEL:
        v_tuple, u_tuple = pending  # type: ignore[misc]
        parameter_tuple_index = counters["parameter_tuples_examined"]
        sum_direct, difference_direct, sum_distinct, difference_distinct = directness(u_tuple, v_tuple)
        if sum_direct != difference_direct:
            raise GeneratorInvariantError(GENERATOR_DIRECTNESS_CONSISTENCY_DISAGREEMENT, "directness")
        if not sum_direct:
            counters["colliding_parameter_tuples_rejected"] += 1
        else:
            counters["direct_tuples_found"] += 1
            raw_a, raw_b = construct_oriented_pair(u_tuple, v_tuple)
            pair_key = (tuple(raw_a), tuple(raw_b))
            if pair_key in emitted_pairs:
                counters["exact_duplicate_candidates_skipped"] += 1
            else:
                emitted_pairs.add(pair_key)
                records.append({
                    "raw_support_A": raw_a,
                    "raw_support_B": raw_b,
                    "candidate_generation_index": counters["candidate_records_emitted"],
                    "generator_diagnostics": {
                        "parameter_tuple_index": parameter_tuple_index,
                        "U": list(u_tuple), "V": list(v_tuple),
                        "sum_directness_count": sum_distinct,
                        "difference_directness_count": difference_distinct,
                        "exact_duplicate_count_before_emission":
                            counters["exact_duplicate_candidates_skipped"],
                    },
                })
                counters["candidate_records_emitted"] += 1
        counters["parameter_tuples_examined"] += 1

        pending = next(iterator, _SENTINEL)
        if pending is _SENTINEL:
            terminal_status, termination_reason = STREAM_COMPLETED, "DOMAIN_EXHAUSTED"
            break
        if counters["candidate_records_emitted"] == max_candidate_records_emitted:
            terminal_status, termination_reason = BUDGET_EXHAUSTED, "MAX_CANDIDATE_RECORDS_EMITTED"
            break
        if counters["parameter_tuples_examined"] == max_parameter_tuples_examined:
            terminal_status, termination_reason = BUDGET_EXHAUSTED, "MAX_PARAMETER_TUPLES_EXAMINED"
            break

    if terminal_status is None:  # empty domain
        terminal_status, termination_reason = STREAM_COMPLETED, "DOMAIN_EXHAUSTED"
    _validate_records_and_counters(records, counters)
    return records, counters, terminal_status, termination_reason  # type: ignore[return-value]


def _validate_records_and_counters(records: Sequence[Dict[str, object]], counters: Dict[str, int]) -> None:
    for position, record in enumerate(records):
        index = record.get("candidate_generation_index")
        if not is_strict_int(index) or index != position:
            raise GeneratorInvariantError(GENERATOR_INDEX_ORDER_FAILURE, "records")
    if counters.get("candidate_records_emitted") != len(records):
        raise GeneratorInvariantError(GENERATOR_COUNTER_INCONSISTENCY, "counters")
    for key in _COUNTER_KEYS:
        if not is_strict_int(counters.get(key)) or counters[key] < 0:
            raise GeneratorInvariantError(GENERATOR_COUNTER_INCONSISTENCY, "counters")


def _candidate_stream_payload(records: Sequence[Dict[str, object]], identity_hash: str,
                              configuration_hash: str, budget_hash: str,
                              terminal_status: str) -> Dict[str, object]:
    return {
        "schema_name": STREAM_SCHEMA_NAME, "schema_version": STREAM_SCHEMA_VERSION,
        "verification_mode": VERIFICATION_MODE, "N": N,
        "generator_identity_hash": identity_hash,
        "generator_configuration_hash": configuration_hash,
        "budget_identity_hash": budget_hash,
        "records": list(records), "candidate_count": len(records),
        "terminal_status": terminal_status,
    }


def _run_result(candidate_stream_envelope: Optional[Dict[str, object]], terminal_status: str,
                termination_reason: str, counters: Dict[str, int],
                failure_record: Optional[Dict[str, object]]) -> Dict[str, object]:
    payload = {
        "schema_name": RUN_RESULT_SCHEMA_NAME, "schema_version": SCHEMA_VERSION,
        "provisional": True,
        "candidate_stream_envelope": candidate_stream_envelope,
        "terminal_status": terminal_status, "termination_reason": termination_reason,
        "structural_counters": dict(counters),
        "failure_record": failure_record,
    }
    return cjson.envelope("generator_run_result", payload)


# --------------------------------------------------------------------- 10. provisional public operation
def generate_candidate_stream(profile_name: str, generator_source_path: Optional[str] = None,
                              serializer_source_path: Optional[str] = None) -> Dict[str, object]:
    """PROVISIONAL ONLY; never authoritative. Emits a canonical result and leaks no internal error."""
    counters = _zero_counters()

    # --- pre-hash stages: a stream may not be emitted at all unless all three hashes exist honestly ---
    try:
        identity_hash = _payload_hash(
            generator_identity_payload(generator_source_path, serializer_source_path), "generator_identity")
        configuration_hash = _payload_hash(generator_configuration_payload(), "generator_configuration")
        budget = structural_budget_payload(profile_name)
        budget_hash = _payload_hash(budget, "structural_budget")
    except _GeneratorError as error:
        return _run_result(None, ROUTE_INCOMPLETE, error.failure_code, counters,
                           _failure_record(error.failure_code, error.stage))

    # --- all mandatory hashes exist: any further failure emits a valid zero-record stream ---
    failure_record: Optional[Dict[str, object]] = None
    terminal_status = ROUTE_INCOMPLETE
    termination_reason = ROUTE_INCOMPLETE
    records: List[Dict[str, object]] = []

    dependency_code = _dependency_probe()
    if dependency_code is not None:
        terminal_status = DEPENDENCY_UNAVAILABLE
        termination_reason = GENERATOR_UNEXPECTED_DEPENDENCY_UNAVAILABLE
        failure_record = _failure_record(GENERATOR_UNEXPECTED_DEPENDENCY_UNAVAILABLE, "dependency_probe")
    else:
        try:
            records, counters, terminal_status, termination_reason = _generate_core(
                _frozen_domain_iterator(),
                int(budget["max_parameter_tuples_examined"]),
                int(budget["max_candidate_records_emitted"]))
        except _GeneratorError as error:
            records, counters = [], _zero_counters()
            terminal_status, termination_reason = ROUTE_INCOMPLETE, error.failure_code
            failure_record = _failure_record(error.failure_code, error.stage)

    try:
        stream_payload = _candidate_stream_payload(
            records, identity_hash, configuration_hash, budget_hash, terminal_status)
        stream_envelope = _build_envelope("candidate_stream", stream_payload, "candidate_stream")
    except _GeneratorError as error:
        return _run_result(None, ROUTE_INCOMPLETE, error.failure_code, counters,
                           _failure_record(error.failure_code, error.stage))

    try:
        return _run_result(stream_envelope, terminal_status, termination_reason, counters, failure_record)
    except (ValueError, TypeError):
        return cjson.envelope("generator_run_result", {
            "schema_name": RUN_RESULT_SCHEMA_NAME, "schema_version": SCHEMA_VERSION, "provisional": True,
            "candidate_stream_envelope": None, "terminal_status": ROUTE_INCOMPLETE,
            "termination_reason": SERIALIZATION_FAILURE, "structural_counters": _zero_counters(),
            "failure_record": _failure_record(SERIALIZATION_FAILURE, "run_result")})


# --------------------------------------------------------------------- 11. replay public operation
def _replay_result(payload: Dict[str, object]) -> Dict[str, object]:
    return cjson.envelope("generator_replay_result", payload)


def generate_candidate_stream_with_replay(profile_name: str, generator_source_path: Optional[str] = None,
                                          serializer_source_path: Optional[str] = None) -> Dict[str, object]:
    """Authoritative two-pass operation. Never invokes the verifier, freezer, ΨTRS, or any descriptor."""
    identity_envelope: Optional[Dict[str, object]] = None
    configuration_envelope: Optional[Dict[str, object]] = None
    budget_envelope: Optional[Dict[str, object]] = None
    source_envelope: Optional[Dict[str, object]] = None
    pre_hash_failure: Optional[Dict[str, object]] = None

    for builder, name, stage in (
            (lambda: generator_identity_payload(generator_source_path, serializer_source_path),
             "generator_identity", "generator_identity"),
            (generator_configuration_payload, "generator_configuration", "generator_configuration"),
            (lambda: structural_budget_payload(profile_name), "structural_budget", "structural_budget"),
            (lambda: source_identity_payload(generator_source_path, serializer_source_path),
             "source_identity", "source_identity")):
        try:
            built = _build_envelope(name, builder(), stage)
        except _GeneratorError as error:
            if pre_hash_failure is None:
                pre_hash_failure = _failure_record(error.failure_code, error.stage)
            continue
        if name == "generator_identity":
            identity_envelope = built
        elif name == "generator_configuration":
            configuration_envelope = built
        elif name == "structural_budget":
            budget_envelope = built
        else:
            source_envelope = built

    run1 = generate_candidate_stream(profile_name, generator_source_path, serializer_source_path)
    run2 = generate_candidate_stream(profile_name, generator_source_path, serializer_source_path)
    result1 = run1["generator_run_result"]
    result2 = run2["generator_run_result"]
    stream1 = result1["candidate_stream_envelope"]
    stream2 = result2["candidate_stream_envelope"]

    def _stream_hash(stream: Optional[Dict[str, object]]) -> Optional[str]:
        if not isinstance(stream, dict):
            return None
        value = stream.get("candidate_stream_sha256")
        return value if isinstance(value, str) else None

    base: Dict[str, object] = {
        "schema_name": REPLAY_RESULT_SCHEMA_NAME, "schema_version": SCHEMA_VERSION,
        "authoritative_operation": False, "downstream_freeze_eligible": False, "byte_identical": False,
        "run1_candidate_stream_sha256": _stream_hash(stream1),
        "run2_candidate_stream_sha256": _stream_hash(stream2),
        "generator_identity_envelope": identity_envelope,
        "generator_configuration_envelope": configuration_envelope,
        "structural_budget_envelope": budget_envelope,
        "source_identity_envelope": source_envelope,
        "run1_structural_counters": result1["structural_counters"],
        "run2_structural_counters": result2["structural_counters"],
        "candidate_stream_envelope": None,
        "failure_record": None,
    }

    if pre_hash_failure is not None or stream1 is None or stream2 is None:
        base["failure_record"] = pre_hash_failure or result1["failure_record"] \
            or _failure_record(SERIALIZATION_FAILURE, "candidate_stream")
        return _replay_result(base)

    try:
        identical = (cjson.canonical_json_bytes(stream1) == cjson.canonical_json_bytes(stream2)
                     and result1["structural_counters"] == result2["structural_counters"]
                     and result1["terminal_status"] == result2["terminal_status"]
                     and result1["termination_reason"] == result2["termination_reason"])
    except (ValueError, TypeError):
        base["failure_record"] = _failure_record(SERIALIZATION_FAILURE, "replay_comparison")
        return _replay_result(base)

    base["byte_identical"] = identical
    if not identical:
        base["failure_record"] = _failure_record(REPLAY_MISMATCH, "replay")
        return _replay_result(base)

    terminal_status = result1["terminal_status"]
    base["authoritative_operation"] = True
    base["candidate_stream_envelope"] = stream1
    base["downstream_freeze_eligible"] = terminal_status in (STREAM_COMPLETED, BUDGET_EXHAUSTED)
    if not base["downstream_freeze_eligible"]:
        base["failure_record"] = result1["failure_record"]
    return _replay_result(base)


# --------------------------------------------------------------------- 12. independence / self-check helpers
def import_roots_from_source(path: str) -> frozenset:
    """AST-only import roots for a source file. Never imports or executes the inspected module."""
    with open(path, "r", encoding="utf-8") as handle:
        tree = ast.parse(handle.read())
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                roots.add("__relative__")
            elif node.module:
                roots.add(node.module.split(".")[0])
    return frozenset(roots)


def dynamic_import_calls_in_source(path: str) -> frozenset:
    """AST-only detection of dynamic import / subprocess-style call names in a source file."""
    watched = {"__import__", "import_module", "exec", "eval", "compile", "popen", "system", "run",
               "Popen", "check_output", "urlopen", "socket", "loads"}
    with open(path, "r", encoding="utf-8") as handle:
        tree = ast.parse(handle.read())
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            target = node.func
            name = target.id if isinstance(target, ast.Name) else (
                target.attr if isinstance(target, ast.Attribute) else None)
            if name in watched:
                found.add(name)
    return frozenset(found)


def independence_report(generator_source_path: Optional[str] = None,
                        serializer_source_path: Optional[str] = None) -> Dict[str, object]:
    """Structural independence surface used by the tests; AST-only, imports nothing it inspects."""
    generator_path = generator_source_path or default_generator_source_path()
    serializer_path = serializer_source_path or default_serializer_source_path()
    generator_roots = import_roots_from_source(generator_path)
    serializer_roots = import_roots_from_source(serializer_path)
    project_local = generator_roots - {"__future__", "ast", "os", "itertools", "typing"}
    violations: List[str] = []
    if not generator_roots.issubset(_ALLOWED_GENERATOR_IMPORT_ROOTS):
        violations.append("generator_import_ownership")
    if not serializer_roots.issubset(_ALLOWED_SERIALIZER_IMPORT_ROOTS):
        violations.append("serializer_import_ownership")
    if not project_local.issubset(_PROJECT_LOCAL_ALLOWED):
        violations.append("project_local_import")
    if dynamic_import_calls_in_source(generator_path):
        violations.append("dynamic_import_or_subprocess")
    return {
        "generator_import_roots": sorted(generator_roots),
        "serializer_import_roots": sorted(serializer_roots),
        "project_local_import_roots": sorted(project_local),
        "violations": sorted(violations),
        "failure_code": FORBIDDEN_IMPORT_DETECTED if violations else None,
    }

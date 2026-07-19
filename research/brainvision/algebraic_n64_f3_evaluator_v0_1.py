"""Frozen-family F3 evaluator for the algebraic N=64 PRIMARY_V0_1 witness family (offline; descriptor-gated).

This module applies the already-frozen F3 contract to the immutable K=3 family (candidates 478, 479, 480). It
re-expresses the exact frozen rotation and symmetric-response formulas LOCALLY (parity-proven against the old
N64 runner's pure functions in tests) and never imports the old runner as its production engine.

Descriptor contact is isolated to exactly one function: build_production_feature_cache(...). No response,
orbit, aggregation, gate, verdict, replay, or serialization function calls psi_trs. Importing this module runs
no descriptor call and builds no cache. evaluate_from_feature_cache(...) is pure over a supplied feature cache.

Governing specification:
  docs/TORMENT_BRAINVISION_ALGEBRAIC_N64_PRIMARY_V0_1_F3_EVALUATOR_IMPLEMENTATION_SPECIFICATION_v0.1.md

FORMAL_HOLD and Mode_0 remain active. Offline, quarantined, non-runtime, non-production, descriptive-only.
"""
from __future__ import annotations

import math
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np

import psi_trs
import witness_canonical_json_v0_1 as cjson
import witness_family_verifier_v0_1 as verifier
import algebraic_n64_f3_frozen_identity_v0_1 as frozen

# --------------------------------------------------------------------------- constants
N = 64
FEATURE_COUNT = 11
EPSILON = 1e-12
NEAR_EPSILON_THRESHOLD = 1e-9
COMPARISON_TOLERANCE = 0.0

VARIANTS: Tuple[str, str] = ("psi_trs", "psi_trs_k0")
KAPPA_BY_VARIANT: Dict[str, float] = {"psi_trs": 0.5, "psi_trs_k0": 0.0}
FULL_VARIANT = "psi_trs"
K0_VARIANT = "psi_trs_k0"

SCHEMA_NAME = "torment_brainvision_algebraic_n64_f3_family_evaluation"
SCHEMA_VERSION = "0.1"
FAILURE_NAMESPACE = "torment_brainvision_algebraic_n64_f3_evaluation_v0_1"
FAILURE_VERSION = "0.1"

# pair verdict labels
PAIR_STRONG_PASS = "PAIR_STRONG_PASS"
PAIR_FULL_NOT_DUAL_ORBIT_EXTREME = "PAIR_FULL_NOT_DUAL_ORBIT_EXTREME"
PAIR_K0_ALSO_DUAL_ORBIT_EXTREME = "PAIR_K0_ALSO_DUAL_ORBIT_EXTREME"
PAIR_RECURSIVE_SIGN_FAILURE = "PAIR_RECURSIVE_SIGN_FAILURE"
PAIR_INVALID = "PAIR_INVALID"

# family verdict labels
STRONG_FAMILY_FALSIFIER_SUCCESS = "STRONG_FAMILY_FALSIFIER_SUCCESS"
VALID_MIXED_FAMILY_RESULT = "VALID_MIXED_FAMILY_RESULT"
STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED = "STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY"
INVALID_FAMILY_EVALUATION = "INVALID_FAMILY_EVALUATION"

# failure codes
EVALUATION_NOT_AUTHORIZED = "EVALUATION_NOT_AUTHORIZED"
REPOSITORY_STATE_INVALID = "REPOSITORY_STATE_INVALID"
SOURCE_IDENTITY_FAILURE = "SOURCE_IDENTITY_FAILURE"
INPUT_FILE_MISSING = "INPUT_FILE_MISSING"
INPUT_WHOLE_FILE_HASH_MISMATCH = "INPUT_WHOLE_FILE_HASH_MISMATCH"
INPUT_JSON_INVALID = "INPUT_JSON_INVALID"
FREEZE_RESULT_PAYLOAD_HASH_MISMATCH = "FREEZE_RESULT_PAYLOAD_HASH_MISMATCH"
FAMILY_MANIFEST_HASH_MISMATCH = "FAMILY_MANIFEST_HASH_MISMATCH"
FAMILY_CERTIFICATE_HASH_MISMATCH = "FAMILY_CERTIFICATE_HASH_MISMATCH"
PAIR_CERTIFICATE_HASH_MISMATCH = "PAIR_CERTIFICATE_HASH_MISMATCH"
FROZEN_SUPPORT_MISMATCH = "FROZEN_SUPPORT_MISMATCH"
WITNESS_REVERIFICATION_FAILURE = "WITNESS_REVERIFICATION_FAILURE"
OUTPUT_PATH_EXISTS = "OUTPUT_PATH_EXISTS"
DESCRIPTOR_CALL_FAILED = "DESCRIPTOR_CALL_FAILED"
DESCRIPTOR_FEATURE_SCHEMA_INVALID = "DESCRIPTOR_FEATURE_SCHEMA_INVALID"
DESCRIPTOR_FEATURE_NONFINITE = "DESCRIPTOR_FEATURE_NONFINITE"
FEATURE_COVERAGE_INCOMPLETE = "FEATURE_COVERAGE_INCOMPLETE"
CROSS_COVERAGE_INCOMPLETE = "CROSS_COVERAGE_INCOMPLETE"
SELF_PAIR_CONTROL_FAILURE = "SELF_PAIR_CONTROL_FAILURE"
SELF_ORBIT_COVERAGE_INCOMPLETE = "SELF_ORBIT_COVERAGE_INCOMPLETE"
NORMALIZATION_FAILURE = "NORMALIZATION_FAILURE"
GATE_INPUT_INVALID = "GATE_INPUT_INVALID"
CANONICAL_SERIALIZATION_FAILURE = "CANONICAL_SERIALIZATION_FAILURE"
REPLAY_MISMATCH = "REPLAY_MISMATCH"
PUBLICATION_FAILURE = "PUBLICATION_FAILURE"
STDOUT_FAILURE = "STDOUT_FAILURE"

# expected coverage per pass
IDENTITY_CONTROLS_PER_PASS = 6 * 2 * 64          # 768
NONIDENTITY_RESPONSES_PER_PASS = 6 * 2 * 63 * 64  # 48,384
CROSS_RESPONSES_PER_PASS = 3 * 2 * 64            # 384
DESCRIPTOR_CALLS_PER_PASS = 6 * 2 * 64           # 768


# --------------------------------------------------------------------------- float canonicalization
def canonical_float(value: object) -> float:
    """Native float with negative zero normalized to +0.0. Raises on non-finite (never serialize NaN/Inf)."""
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("non-finite value cannot be canonicalized")
    return 0.0 if number == 0.0 else number


def _is_finite_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


# --------------------------------------------------------------------------- field construction
def build_field(support: Tuple[int, ...]) -> np.ndarray:
    """Direct scalar binary (64,1) float field. value[t] = 1.0 iff t in support, else 0.0. No mutation."""
    field = np.zeros((N, 1), dtype=float)
    for index in support:
        field[int(index), 0] = 1.0
    return field


def support_from_field(field: np.ndarray) -> Tuple[int, ...]:
    array = np.asarray(field, dtype=float)
    return tuple(int(t) for t in range(array.shape[0]) if array[t, 0] == 1.0)


def validate_field(field: np.ndarray, support: Tuple[int, ...]) -> Optional[str]:
    array = np.asarray(field, dtype=float)
    if array.shape != (N, 1):
        return "shape"
    if not np.all(np.isfinite(array)):
        return "nonfinite"
    if not np.all((array == 0.0) | (array == 1.0)):
        return "not_binary"
    if int(array.sum()) != frozen.MEMBER_WEIGHT:
        return "weight"
    if support_from_field(array) != tuple(support):
        return "support_mismatch"
    return None


# --------------------------------------------------------------------------- rotation and response (local)
def rotate(field: np.ndarray, s: int) -> np.ndarray:
    """rotate(x,s)[t] = x[(t+s) mod 64] == np.roll(x, -s, axis=0). Parity-proven against the old N64 runner."""
    return np.roll(field, -s % N, axis=0)


def _l2(vector: np.ndarray) -> float:
    return float(np.linalg.norm(np.asarray(vector, dtype=float).reshape(-1)))


def symmetric_response(f_a: np.ndarray, f_b: np.ndarray) -> Dict[str, object]:
    """Symmetric joint-mean-norm normalized L2 response. Bit-identical to the old N64 runner's function."""
    numerator = _l2(np.asarray(f_a, dtype=float) - np.asarray(f_b, dtype=float))
    joint_scale = (_l2(f_a) + _l2(f_b)) / 2.0
    effective = max(joint_scale, EPSILON)
    return {
        "numerator": numerator,
        "joint_scale": joint_scale,
        "effective_joint_scale": effective,
        "joint_epsilon_hit": bool(joint_scale <= EPSILON),
        "joint_near_epsilon_hit": bool(joint_scale <= NEAR_EPSILON_THRESHOLD),
        "finite": bool(math.isfinite(numerator) and math.isfinite(joint_scale)),
        "distance": numerator / effective,
    }


def _response_payload(response: Dict[str, object]) -> Dict[str, object]:
    return {
        "numerator": canonical_float(response["numerator"]),
        "joint_scale": canonical_float(response["joint_scale"]),
        "effective_joint_scale": canonical_float(response["effective_joint_scale"]),
        "joint_epsilon_hit": bool(response["joint_epsilon_hit"]),
        "joint_near_epsilon_hit": bool(response["joint_near_epsilon_hit"]),
        "finite": bool(response["finite"]),
        "distance": canonical_float(response["distance"]),
    }


# --------------------------------------------------------------------------- aggregation
def aggregate(values: List[float]) -> Dict[str, object]:
    array = np.asarray(values, dtype=float)
    minimum = float(array.min())
    maximum = float(array.max())
    return {
        "count": int(array.size),
        "minimum": canonical_float(minimum),
        "maximum": canonical_float(maximum),
        "median": canonical_float(float(np.median(array))),
        "mean": canonical_float(float(array.mean())),
        "population_standard_deviation": canonical_float(float(array.std(ddof=0))),
        "argmin_starts": sorted(int(i) for i in np.where(array == minimum)[0]),
        "argmax_starts": sorted(int(i) for i in np.where(array == maximum)[0]),
    }


# --------------------------------------------------------------------------- frozen-evidence validation
class EvidenceError(Exception):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(code)
        self.code = code
        self.detail = detail


def _mapping(value: object) -> Optional[Dict[str, object]]:
    return value if isinstance(value, dict) else None


def validate_frozen_evidence(freeze_result_envelope: object) -> Dict[str, object]:
    """Read-only structural + hash validation of the canonical freeze-result envelope. No descriptor contact.

    Returns a mapping of extracted, frozen-agreeing pieces. Raises EvidenceError(code) on any mismatch.
    """
    envelope = _mapping(freeze_result_envelope)
    if envelope is None or set(envelope) != {"freeze_result", "freeze_result_sha256"}:
        raise EvidenceError(INPUT_JSON_INVALID, "envelope shape")
    payload = _mapping(envelope["freeze_result"])
    if payload is None:
        raise EvidenceError(INPUT_JSON_INVALID, "payload not a mapping")
    if cjson.payload_sha256(payload) != envelope["freeze_result_sha256"]:
        raise EvidenceError(FREEZE_RESULT_PAYLOAD_HASH_MISMATCH, "envelope hash")
    if envelope["freeze_result_sha256"] != frozen.freeze_result_payload_sha256:
        raise EvidenceError(FREEZE_RESULT_PAYLOAD_HASH_MISMATCH, "frozen payload hash")

    if payload.get("family_frozen") is not True or payload.get("authoritative_operation") is not True:
        raise EvidenceError(REPOSITORY_STATE_INVALID, "not an authoritative frozen family")
    if payload.get("accepted_candidate_indices") != list(frozen.accepted_candidate_indices):
        raise EvidenceError(FROZEN_SUPPORT_MISMATCH, "accepted indices")
    if payload.get("candidate_count") != frozen.candidate_count:
        raise EvidenceError(REPOSITORY_STATE_INVALID, "candidate_count")
    if payload.get("terminal_stream_status") != frozen.terminal_stream_status:
        raise EvidenceError(REPOSITORY_STATE_INVALID, "terminal_stream_status")
    if payload.get("candidate_stream_sha256") != frozen.candidate_stream_payload_sha256:
        raise EvidenceError(REPOSITORY_STATE_INVALID, "candidate_stream_sha256")
    if payload.get("N") != N:
        raise EvidenceError(REPOSITORY_STATE_INVALID, "N")

    manifest_env = _mapping(payload.get("family_manifest"))
    if manifest_env is None or set(manifest_env) != {"family_manifest", "family_manifest_sha256"}:
        raise EvidenceError(FAMILY_MANIFEST_HASH_MISMATCH, "manifest envelope")
    manifest_payload = _mapping(manifest_env["family_manifest"])
    if manifest_payload is None or cjson.payload_sha256(manifest_payload) != manifest_env["family_manifest_sha256"]:
        raise EvidenceError(FAMILY_MANIFEST_HASH_MISMATCH, "manifest hash")
    if manifest_env["family_manifest_sha256"] != frozen.family_manifest_sha256:
        raise EvidenceError(FAMILY_MANIFEST_HASH_MISMATCH, "frozen manifest hash")
    if manifest_payload.get("repository_commit_identity") != frozen.execution_commit_identity:
        raise EvidenceError(REPOSITORY_STATE_INVALID, "execution commit binding")

    cert_env = _mapping(payload.get("family_certificate"))
    if cert_env is None or set(cert_env) != {"family_verifier_certificate", "family_verifier_certificate_sha256"}:
        raise EvidenceError(FAMILY_CERTIFICATE_HASH_MISMATCH, "certificate envelope")
    cert_payload = _mapping(cert_env["family_verifier_certificate"])
    if cert_payload is None or cjson.payload_sha256(cert_payload) != cert_env["family_verifier_certificate_sha256"]:
        raise EvidenceError(FAMILY_CERTIFICATE_HASH_MISMATCH, "certificate hash")
    if cert_env["family_verifier_certificate_sha256"] != frozen.family_verifier_certificate_sha256:
        raise EvidenceError(FAMILY_CERTIFICATE_HASH_MISMATCH, "frozen certificate hash")

    pair_envelopes = payload.get("accepted_pair_certificate_envelopes")
    if not isinstance(pair_envelopes, list) or len(pair_envelopes) != frozen.K:
        raise EvidenceError(PAIR_CERTIFICATE_HASH_MISMATCH, "pair envelope count")
    extracted_pairs: List[Dict[str, object]] = []
    for order_index, pair_env_obj in enumerate(pair_envelopes):
        pair_env = _mapping(pair_env_obj)
        if pair_env is None or "pair_verifier_certificate" not in pair_env \
                or "pair_verifier_certificate_sha256" not in pair_env:
            raise EvidenceError(PAIR_CERTIFICATE_HASH_MISMATCH, "pair envelope shape %d" % order_index)
        pair_cert = _mapping(pair_env["pair_verifier_certificate"])
        supplied_hash = pair_env["pair_verifier_certificate_sha256"]
        if pair_cert is None or cjson.payload_sha256(pair_cert) != supplied_hash:
            raise EvidenceError(PAIR_CERTIFICATE_HASH_MISMATCH, "pair hash %d" % order_index)
        if supplied_hash != frozen.pair_certificate_sha256[order_index]:
            raise EvidenceError(PAIR_CERTIFICATE_HASH_MISMATCH, "frozen pair hash %d" % order_index)
        candidate_index, _order, frozen_a, frozen_b, _h = frozen.frozen_pairs[order_index]
        support_a = _mapping(pair_cert.get("member_certificate_A"))
        support_b = _mapping(pair_cert.get("member_certificate_B"))
        if support_a is None or support_b is None \
                or tuple(support_a.get("raw_support") or ()) != frozen_a \
                or tuple(support_b.get("raw_support") or ()) != frozen_b:
            raise EvidenceError(FROZEN_SUPPORT_MISMATCH, "pair %d supports" % order_index)
        extracted_pairs.append({"candidate_generation_index": candidate_index, "pair_order_index": order_index,
                                "raw_support_A": frozen_a, "raw_support_B": frozen_b,
                                "pair_certificate": pair_cert, "pair_certificate_sha256": supplied_hash})
    return {"payload": payload, "family_certificate": cert_payload,
            "family_certificate_envelope": cert_env, "pairs": extracted_pairs}


def reverify_witnesses(extracted_pairs: List[Dict[str, object]],
                       family_certificate_envelope: object) -> Dict[str, object]:
    """Integer-exact independent reverification of pairs and family (§7). No descriptor contact.

    Enforces exact payload equality and canonical hash equality between the recomputed family certificate and
    the embedded frozen family certificate. Any mismatch is a pre-descriptor refusal
    (FAMILY_CERTIFICATE_HASH_MISMATCH / PAIR_CERTIFICATE_HASH_MISMATCH / WITNESS_REVERIFICATION_FAILURE),
    NOT a scientific PAIR_INVALID / INVALID_FAMILY_EVALUATION.
    """
    # --- embedded family-certificate envelope integrity (before recomputation) ---
    cert_env = _mapping(family_certificate_envelope)
    if cert_env is None or set(cert_env) != {"family_verifier_certificate", "family_verifier_certificate_sha256"}:
        raise EvidenceError(FAMILY_CERTIFICATE_HASH_MISMATCH, "embedded envelope shape")
    embedded_payload = _mapping(cert_env["family_verifier_certificate"])
    supplied_hash = cert_env["family_verifier_certificate_sha256"]
    if embedded_payload is None:
        raise EvidenceError(FAMILY_CERTIFICATE_HASH_MISMATCH, "embedded payload not a mapping")
    if cjson.payload_sha256(embedded_payload) != supplied_hash:
        raise EvidenceError(FAMILY_CERTIFICATE_HASH_MISMATCH, "embedded payload hash != supplied")
    if supplied_hash != frozen.family_verifier_certificate_sha256:
        raise EvidenceError(FAMILY_CERTIFICATE_HASH_MISMATCH, "supplied hash != frozen")

    # --- integer-exact pair reverification ---
    recomputed_certificates: List[Dict[str, object]] = []
    for pair in extracted_pairs:
        record = {"raw_support_A": list(pair["raw_support_A"]), "raw_support_B": list(pair["raw_support_B"]),
                  "candidate_generation_index": pair["candidate_generation_index"]}
        result = verifier.verify_candidate(record, N)
        if result.get("execution_invalid") is not False or result.get("pair_valid") is not True \
                or list(result.get("ordered_failure_codes") or []) != []:
            raise EvidenceError(WITNESS_REVERIFICATION_FAILURE,
                                "pair %d verify_candidate" % pair["pair_order_index"])
        recomputed = result.get("pair_certificate")
        if _mapping(recomputed) is None:
            raise EvidenceError(WITNESS_REVERIFICATION_FAILURE, "no recomputed certificate")
        if cjson.payload_sha256(recomputed) != pair["pair_certificate_sha256"]:
            raise EvidenceError(PAIR_CERTIFICATE_HASH_MISMATCH,
                                "recomputed pair %d" % pair["pair_order_index"])
        recomputed_certificates.append(recomputed)

    # --- integer-exact family reverification + exact certificate equality ---
    family = verifier.verify_family(recomputed_certificates, N)
    for field in ("family_valid", "members_non_reused", "mutual_G_inequivalent",
                  "distinct_autocorrelation_classes"):
        if family.get(field) is not True:
            raise EvidenceError(WITNESS_REVERIFICATION_FAILURE, "family %s" % field)
    if list(family.get("ordered_failure_codes") or []) != []:
        raise EvidenceError(WITNESS_REVERIFICATION_FAILURE, "family ordered_failure_codes")

    recomputed_family_certificate = {
        "pair_certificate_hashes": [cjson.payload_sha256(cert) for cert in recomputed_certificates],
        "mutual_G_inequivalent": family["mutual_G_inequivalent"],
        "members_non_reused": family["members_non_reused"],
        "distinct_autocorrelation_classes": family["distinct_autocorrelation_classes"],
        "family_valid": family["family_valid"], "ordered_failure_codes": family["ordered_failure_codes"]}
    if recomputed_family_certificate != embedded_payload:
        raise EvidenceError(FAMILY_CERTIFICATE_HASH_MISMATCH, "recomputed payload != embedded payload")
    if cjson.payload_sha256(recomputed_family_certificate) != frozen.family_verifier_certificate_sha256:
        raise EvidenceError(FAMILY_CERTIFICATE_HASH_MISMATCH, "recomputed hash != frozen")

    return {"recomputed_pair_certificates": recomputed_certificates, "family": family,
            "recomputed_family_certificate": recomputed_family_certificate}


# --------------------------------------------------------------------------- production feature cache (SOLE psi contact)
def default_feature_provider(field: np.ndarray, kappa: float) -> object:
    """The ONLY production descriptor call site. Returns the RAW descriptor output, unaltered in shape."""
    return psi_trs.psi_trs_features(field, kappa=kappa)


def build_production_feature_cache(feature_provider: Optional[Callable[[np.ndarray, float], object]] = None
                                   ) -> Dict[str, object]:
    """Build the complete 6*2*64 = 768 feature cache by contacting the production descriptor once per start.

    This is the ONLY evaluator function that invokes psi_trs. The raw descriptor return is inspected for exact
    dimensionality and finiteness BEFORE any shape-changing operation; no reshape/flatten/squeeze/ravel is
    performed. A schema or nonfinite failure stops the pass before any response mathematics.
    """
    provider = feature_provider if feature_provider is not None else default_feature_provider
    features: Dict[str, Dict[str, List[List[float]]]] = {}
    attempted = 0
    completed = 0
    for member_id, _candidate, _order, _role, support in frozen.frozen_members:
        field = build_field(support)
        problem = validate_field(field, support)
        if problem is not None:
            raise EvidenceError(FROZEN_SUPPORT_MISMATCH, "%s field %s" % (member_id, problem))
        features[member_id] = {}
        for variant in VARIANTS:
            kappa = KAPPA_BY_VARIANT[variant]
            rows: List[List[float]] = []
            for start in range(N):
                rotated = rotate(field, start)
                attempted += 1
                raw_features = provider(rotated, kappa)
                array = np.asarray(raw_features, dtype=float)
                if array.ndim != 1 or array.shape != (FEATURE_COUNT,):
                    raise EvidenceError(DESCRIPTOR_FEATURE_SCHEMA_INVALID,
                                        "%s/%s/%d shape %r" % (member_id, variant, start, tuple(array.shape)))
                if not bool(np.all(np.isfinite(array))):
                    raise EvidenceError(DESCRIPTOR_FEATURE_NONFINITE,
                                        "%s/%s/%d nonfinite" % (member_id, variant, start))
                rows.append([float(x) for x in array])       # 1-D float copy; shape and values unchanged
                completed += 1
            features[member_id][variant] = rows
    call_record = {"attempted_descriptor_calls": attempted, "completed_descriptor_calls": completed,
                   "expected_descriptor_calls": DESCRIPTOR_CALLS_PER_PASS,
                   "descriptor_variants": list(VARIANTS), "kappa_by_variant": dict(KAPPA_BY_VARIANT)}
    return {"features": features, "descriptor_call_record": call_record}


# --------------------------------------------------------------------------- pure cache evaluation
def _schema_failure(failure_code: str, value_status: str, member: Optional[str], variant: Optional[str],
                    start: Optional[int], detail: str) -> Dict[str, object]:
    """Structured feature-cache-validation failure record. Known member/variant/start are never discarded."""
    return {"failure_code": failure_code, "stage": "feature_cache_validation", "member": member,
            "variant": variant, "start": start, "value_status": value_status, "detail": detail}


def _validate_feature_schema(features: Dict[str, object]) -> Optional[Dict[str, object]]:
    for member_id, _c, _o, _r, _s in frozen.frozen_members:
        by_variant = _mapping(features.get(member_id))
        if by_variant is None:
            return _schema_failure(FEATURE_COVERAGE_INCOMPLETE, "coverage_incomplete", member_id, None, None,
                                   "member absent")
        for variant in VARIANTS:
            rows = by_variant.get(variant)
            if not isinstance(rows, list) or len(rows) != N:
                actual = len(rows) if isinstance(rows, list) else None
                return _schema_failure(FEATURE_COVERAGE_INCOMPLETE, "coverage_incomplete", member_id, variant,
                                       actual, "start row count %s != 64" % actual)
            for start, vector in enumerate(rows):
                if not isinstance(vector, list) or len(vector) != FEATURE_COUNT:
                    length = len(vector) if isinstance(vector, list) else None
                    return _schema_failure(DESCRIPTOR_FEATURE_SCHEMA_INVALID, "schema_invalid", member_id,
                                           variant, start, "feature length %s != 11" % length)
                for value in vector:
                    if not isinstance(value, (int, float)) or isinstance(value, bool):
                        return _schema_failure(DESCRIPTOR_FEATURE_SCHEMA_INVALID, "schema_invalid", member_id,
                                               variant, start, "non-numeric feature element")
                    if not math.isfinite(float(value)):
                        return _schema_failure(DESCRIPTOR_FEATURE_NONFINITE, "nonfinite", member_id, variant,
                                               start, "nonfinite feature value")
    return None


def _vector(features: Dict[str, object], member_id: str, variant: str, start: int) -> np.ndarray:
    return np.asarray(features[member_id][variant][start], dtype=float)


def _self_orbit(features: Dict[str, object], member_id: str, variant: str
                ) -> Tuple[Dict[str, object], List[str]]:
    failures: List[str] = []
    identity_nonzero: List[int] = []
    for start in range(N):
        control = symmetric_response(_vector(features, member_id, variant, start),
                                     _vector(features, member_id, variant, start))
        if not (control["numerator"] == 0.0 and control["distance"] == 0.0 and control["finite"]):
            identity_nonzero.append(start)
    if identity_nonzero:
        failures.append(SELF_PAIR_CONTROL_FAILURE)

    shift_objects: List[Dict[str, object]] = []
    max_mean = None
    argmax_shifts: List[int] = []
    for relative_shift in range(1, N):
        distances: List[float] = []
        per_start: List[Dict[str, object]] = []
        for start in range(N):
            response = symmetric_response(_vector(features, member_id, variant, start),
                                          _vector(features, member_id, variant, (start + relative_shift) % N))
            if not response["finite"]:
                failures.append(NORMALIZATION_FAILURE)
            per_start.append(_response_payload(response))
            distances.append(response["distance"])
        agg = aggregate(distances)
        shift_objects.append(dict({"relative_shift": relative_shift, "per_start": per_start}, **agg))
        mean_value = agg["mean"]
        if max_mean is None or mean_value > max_mean:
            max_mean = mean_value
            argmax_shifts = [relative_shift]
        elif mean_value == max_mean:
            argmax_shifts.append(relative_shift)

    orbit = {
        "identity_controls": {"count": N, "all_distance_zero": (identity_nonzero == []),
                              "nonzero_starts": identity_nonzero},
        "nonidentity_shifts": shift_objects,
        "maximum_nonidentity_mean": max_mean,
        "argmax_nonidentity_shifts": sorted(argmax_shifts),
        "coverage": {"shift_count": len(shift_objects), "responses": len(shift_objects) * N},
    }
    return orbit, failures


def _cross_by_variant(features: Dict[str, object], member_a: str, member_b: str, variant: str
                      ) -> Tuple[Dict[str, object], List[float], List[str]]:
    failures: List[str] = []
    distances: List[float] = []
    per_start: List[Dict[str, object]] = []
    for start in range(N):
        response = symmetric_response(_vector(features, member_a, variant, start),
                                      _vector(features, member_b, variant, start))
        if not response["finite"]:
            failures.append(NORMALIZATION_FAILURE)
        per_start.append(_response_payload(response))
        distances.append(response["distance"])
    agg = aggregate(distances)
    cross = dict({"per_start": per_start}, **agg)
    return cross, distances, failures


def evaluate_from_feature_cache(cache: Dict[str, object]) -> Dict[str, object]:
    """PURE evaluation over a supplied feature cache. Invokes NO descriptor. Returns the evaluation_pass payload
    plus valid_run / family_verdict / failure_record. Deterministic; no host state, timestamps, or paths."""
    features = _mapping(cache.get("features"))
    descriptor_call_record = _mapping(cache.get("descriptor_call_record")) or {}
    failures: List[Dict[str, object]] = []

    feature_schema_valid = True
    feature_coverage_valid = True
    schema_problem = _validate_feature_schema(features if features is not None else {})
    if schema_problem is not None:
        feature_coverage_valid = schema_problem["failure_code"] != FEATURE_COVERAGE_INCOMPLETE
        feature_schema_valid = schema_problem["failure_code"] == FEATURE_COVERAGE_INCOMPLETE
        return _invalid_pass(descriptor_call_record, schema_problem,
                             feature_schema_valid=feature_schema_valid,
                             feature_coverage_valid=feature_coverage_valid)

    # --- members and self orbits ---
    members: List[Dict[str, object]] = []
    self_max: Dict[Tuple[str, str], object] = {}
    identity_ok = True
    normalization_ok = True
    finite_ok = True
    self_orbit_responses = 0
    for member_id, candidate_index, pair_order_index, raw_role, support in frozen.frozen_members:
        orbits: Dict[str, object] = {}
        features_by_variant: Dict[str, object] = {}
        for variant in VARIANTS:
            orbit, orbit_failures = _self_orbit(features, member_id, variant)
            if SELF_PAIR_CONTROL_FAILURE in orbit_failures:
                identity_ok = False
                failures.append({"failure_code": SELF_PAIR_CONTROL_FAILURE, "stage": "identity_control",
                                 "member": member_id, "variant": variant})
            if NORMALIZATION_FAILURE in orbit_failures:
                normalization_ok = False
                failures.append({"failure_code": NORMALIZATION_FAILURE, "stage": "self_orbit",
                                 "member": member_id, "variant": variant})
            orbits[variant] = orbit
            self_max[(member_id, variant)] = orbit["maximum_nonidentity_mean"]
            self_orbit_responses += orbit["coverage"]["responses"]
            rows = [{"start": start, "feature_vector": [canonical_float(v) for v in
                                                        features[member_id][variant][start]],
                     "feature_vector_sha256": cjson.payload_sha256(
                         [canonical_float(v) for v in features[member_id][variant][start]]),
                     "finite": True, "feature_count": FEATURE_COUNT} for start in range(N)]
            features_by_variant[variant] = rows
        members.append({
            "member_id": member_id, "candidate_generation_index": candidate_index,
            "pair_order_index": pair_order_index, "raw_role": raw_role, "raw_support": list(support),
            "raw_support_sha256": cjson.payload_sha256(list(support)), "weight": frozen.MEMBER_WEIGHT,
            "pair_verifier_certificate_sha256": frozen.pair_certificate_sha256[pair_order_index],
            "features_by_variant": features_by_variant, "self_orbits_by_variant": orbits})

    # --- pairs, cross responses, recursive companion, gates ---
    pairs: List[Dict[str, object]] = []
    cross_responses = 0
    strong_pass_count = 0
    for candidate_index, pair_order_index, support_a, support_b, cert_hash in frozen.frozen_pairs:
        member_a = "candidate_%d_A" % candidate_index
        member_b = "candidate_%d_B" % candidate_index
        cross_by_variant: Dict[str, object] = {}
        distances_by_variant: Dict[str, List[float]] = {}
        for variant in VARIANTS:
            cross, distances, cross_failures = _cross_by_variant(features, member_a, member_b, variant)
            if NORMALIZATION_FAILURE in cross_failures:
                normalization_ok = False
                failures.append({"failure_code": NORMALIZATION_FAILURE, "stage": "cross",
                                 "member": "%s/%s" % (member_a, member_b), "variant": variant})
            cross_by_variant[variant] = cross
            distances_by_variant[variant] = distances
            cross_responses += N

        full_cross = distances_by_variant[FULL_VARIANT]
        k0_cross = distances_by_variant[K0_VARIANT]
        differences = [full_cross[s] - k0_cross[s] for s in range(N)]
        recursive = _recursive_companion(differences)

        full_cross_mean = cross_by_variant[FULL_VARIANT]["mean"]
        k0_cross_mean = cross_by_variant[K0_VARIANT]["mean"]
        full_self_A_max = self_max[(member_a, FULL_VARIANT)]
        full_self_B_max = self_max[(member_b, FULL_VARIANT)]
        k0_self_A_max = self_max[(member_a, K0_VARIANT)]
        k0_self_B_max = self_max[(member_b, K0_VARIANT)]

        full_dual_orbit_extreme = bool(full_cross_mean > full_self_A_max
                                       and full_cross_mean > full_self_B_max)
        k0_not_extreme = bool(k0_cross_mean <= k0_self_A_max and k0_cross_mean <= k0_self_B_max)
        recursive_positive_all_starts = bool(all(d > COMPARISON_TOLERANCE for d in differences))

        valid_pair = identity_ok and normalization_ok and finite_ok
        primary_pass = bool(valid_pair and full_dual_orbit_extreme and k0_not_extreme
                            and recursive_positive_all_starts)
        if primary_pass:
            strong_pass_count += 1

        flags: List[str] = []
        if primary_pass:
            flags.append(PAIR_STRONG_PASS)
        if not valid_pair:
            flags.append(PAIR_INVALID)
        if not full_dual_orbit_extreme:
            flags.append(PAIR_FULL_NOT_DUAL_ORBIT_EXTREME)
        if not k0_not_extreme:
            flags.append(PAIR_K0_ALSO_DUAL_ORBIT_EXTREME)
        if not recursive_positive_all_starts:
            flags.append(PAIR_RECURSIVE_SIGN_FAILURE)

        pairs.append({
            "candidate_generation_index": candidate_index, "pair_order_index": pair_order_index,
            "member_A_id": member_a, "member_B_id": member_b,
            "pair_verifier_certificate_sha256": cert_hash,
            "cross_by_variant": cross_by_variant, "recursive_companion": recursive,
            "gates": {
                "full_cross_mean": full_cross_mean, "k0_cross_mean": k0_cross_mean,
                "full_self_A_max": full_self_A_max, "full_self_B_max": full_self_B_max,
                "k0_self_A_max": k0_self_A_max, "k0_self_B_max": k0_self_B_max,
                "full_dual_orbit_extreme": full_dual_orbit_extreme,
                "k0_not_extreme_against_either_member": k0_not_extreme,
                "recursive_positive_all_starts": recursive_positive_all_starts},
            "margins": {
                "full_margin_vs_A": canonical_float(full_cross_mean - full_self_A_max),
                "full_margin_vs_B": canonical_float(full_cross_mean - full_self_B_max),
                "k0_margin_vs_A": canonical_float(k0_cross_mean - k0_self_A_max),
                "k0_margin_vs_B": canonical_float(k0_cross_mean - k0_self_B_max),
                "minimum_recursive_difference": canonical_float(min(differences))},
            "primary_pass": primary_pass, "pair_verdict_flags": flags})

    # --- coverage / validity ---
    identity_self_pair_valid = identity_ok
    self_orbit_coverage_valid = (self_orbit_responses == NONIDENTITY_RESPONSES_PER_PASS)
    cross_coverage_valid = (cross_responses == CROSS_RESPONSES_PER_PASS)
    if not self_orbit_coverage_valid:
        failures.append({"failure_code": SELF_ORBIT_COVERAGE_INCOMPLETE, "stage": "self_orbit_coverage"})
    if not cross_coverage_valid:
        failures.append({"failure_code": CROSS_COVERAGE_INCOMPLETE, "stage": "cross_coverage"})
    if not identity_self_pair_valid:
        pass  # already recorded

    validity = _validity_object(feature_schema_valid, feature_coverage_valid, cross_coverage_valid,
                                identity_self_pair_valid, self_orbit_coverage_valid, finite_ok,
                                normalization_ok)
    valid_run = all(validity.values())

    if valid_run:
        family_verdict = _family_verdict(strong_pass_count, all_valid=True)
    else:
        family_verdict = INVALID_FAMILY_EVALUATION

    family_summary = {
        "strong_pass_count": strong_pass_count,
        "pair_verdicts": [{"candidate_generation_index": p["candidate_generation_index"],
                           "pair_order_index": p["pair_order_index"], "primary_pass": p["primary_pass"],
                           "pair_verdict_flags": p["pair_verdict_flags"]} for p in pairs],
        "family_verdict": family_verdict}

    pass_payload = {
        "members": members, "pairs": pairs, "family_summary": family_summary,
        "descriptor_call_record": descriptor_call_record, "pass_validity": validity}
    failure_record = failures[0] if (failures and not valid_run) else None
    return {"evaluation_pass": pass_payload, "valid_run": valid_run, "family_verdict": family_verdict,
            "strong_pass_count": strong_pass_count, "failure_record": failure_record, "validity": validity}


def _recursive_companion(differences: List[float]) -> Dict[str, object]:
    array = np.asarray(differences, dtype=float)
    positive = int(sum(1 for d in differences if d > 0.0))
    zero = int(sum(1 for d in differences if d == 0.0))
    negative = int(sum(1 for d in differences if d < 0.0))
    return {
        "differences": [canonical_float(d) for d in differences],
        "minimum": canonical_float(float(array.min())), "maximum": canonical_float(float(array.max())),
        "median": canonical_float(float(np.median(array))), "mean": canonical_float(float(array.mean())),
        "population_standard_deviation": canonical_float(float(array.std(ddof=0))),
        "positive_count": positive, "zero_count": zero, "negative_count": negative,
        "all_positive": bool(positive == len(differences))}


def _validity_object(feature_schema_valid: bool, feature_coverage_valid: bool, cross_coverage_valid: bool,
                     identity_self_pair_valid: bool, self_orbit_coverage_valid: bool, finite_ok: bool,
                     normalization_ok: bool) -> Dict[str, bool]:
    return {
        "freeze_result_identity_valid": True, "family_manifest_identity_valid": True,
        "family_certificate_identity_valid": True, "pair_certificate_identities_valid": True,
        "frozen_support_identity_valid": True, "witness_reverification_valid": True,
        "source_identity_valid": True, "descriptor_identity_valid": True, "input_encoding_valid": True,
        "feature_schema_valid": bool(feature_schema_valid), "feature_coverage_valid": bool(feature_coverage_valid),
        "cross_coverage_valid": bool(cross_coverage_valid),
        "identity_self_pair_valid": bool(identity_self_pair_valid),
        "self_orbit_coverage_valid": bool(self_orbit_coverage_valid),
        "all_response_values_finite": bool(finite_ok), "normalization_valid": bool(normalization_ok),
        "gate_inputs_valid": True, "canonical_serialization_valid": True}


def _family_verdict(strong_pass_count: int, all_valid: bool) -> str:
    if not all_valid:
        return INVALID_FAMILY_EVALUATION
    if strong_pass_count == 3:
        return STRONG_FAMILY_FALSIFIER_SUCCESS
    if strong_pass_count in (1, 2):
        return VALID_MIXED_FAMILY_RESULT
    return STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED


def _invalid_pass(descriptor_call_record: Dict[str, object], failure_record: Optional[Dict[str, object]],
                  feature_schema_valid: bool, feature_coverage_valid: bool) -> Dict[str, object]:
    validity = _validity_object(feature_schema_valid, feature_coverage_valid, False, False, False, False, False)
    family_summary = {"strong_pass_count": 0, "pair_verdicts": [],
                      "family_verdict": INVALID_FAMILY_EVALUATION}
    # The structured failure record survives into the pass payload and thus into the final result payload.
    pass_payload = {"members": [], "pairs": [], "family_summary": family_summary,
                    "descriptor_call_record": descriptor_call_record, "pass_validity": validity,
                    "failure_record": failure_record}
    return {"evaluation_pass": pass_payload, "valid_run": False,
            "family_verdict": INVALID_FAMILY_EVALUATION, "strong_pass_count": 0,
            "failure_record": failure_record, "validity": validity}


# --------------------------------------------------------------------------- canonical serialization
def canonical_pass_bytes(evaluation_pass: Dict[str, object]) -> bytes:
    """Canonical bytes of one pass payload (excludes host state, timestamps, durations, and paths)."""
    return cjson.canonical_json_bytes(evaluation_pass)


def canonical_pass_sha256(evaluation_pass: Dict[str, object]) -> str:
    return cjson.payload_sha256(evaluation_pass)

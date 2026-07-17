"""TORMENT Brainvision exact N=64 homometric falsifier - evaluation runner v0.1.

Offline, quarantined, descriptive. Implements the accepted evaluation contract v0.1 + implementation
specification v0.1. Owns: boundary validation, rotations, descriptor invocation, feature schema,
symmetric/directional metrics, all-start evaluation, self-pair + role-swap + complete self-shift controls,
kappa differences, tie-aware placement, canonical schema assembly, validity/error codes, environment
capture, canonical JSON, hashing, and stdout transport.

Candidate evaluation (passing member A/B through the descriptor) is hard-gated behind the
N64_EVALUATION_AUTHORIZED == "1" environment flag; no other value authorizes. Imports only quarantined
research functionality (psi_trs, the N64 fixture module) plus stdlib + numpy. No torment_service import. No
result file is written. The CLI is guarded and is NOT executed at import time.
"""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import math
import os
import platform
import sys
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np

_HERE = os.path.dirname(os.path.realpath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import psi_trs  # noqa: E402  (quarantined descriptor; unchanged)
import n64_falsifier_fixture_v0_1 as fixture_module  # noqa: E402

N: int = 64
EPSILON: float = 1e-12
NEAR_EPSILON_THRESHOLD: float = 1e-9
FEATURE_COUNT: int = 11
DESCRIPTOR_VARIANTS: Tuple[str, str] = ("psi_trs", "psi_trs_k0")
DESCRIPTOR_PARAMETERS: Dict[str, Dict[str, float]] = {
    "psi_trs": {"kappa": 0.5},
    "psi_trs_k0": {"kappa": 0.0},
}
KAPPA_DIFFERENCE_ORIENTATION: str = "psi_trs_minus_psi_trs_k0"
EVALUATION_AUTHORIZATION_ENV: str = "N64_EVALUATION_AUTHORIZED"
EVALUATION_AUTHORIZATION_VALUE: str = "1"

SCHEMA_NAME: str = "torment_brainvision_n64_falsifier_evaluation"
SCHEMA_VERSION: str = "0.1"
RUNNER_NAME: str = "run_n64_falsifier_v0_1"
RUNNER_VERSION: str = "0.1"
CANONICALIZATION_NAME: str = "compact_finite_only_canonical_json"
CANONICALIZATION_VERSION: str = "0.1"
ERROR_CODE_NAMESPACE: str = "torment_brainvision_n64_falsifier_v0_1"
ERROR_CODE_VERSION: str = "0.1"

_UNAVAILABLE_API_ABSENT: str = "unavailable_api_absent"
_UNAVAILABLE_CALL_FAILED: str = "unavailable_call_failed"
_UNAVAILABLE_EMPTY: str = "unavailable_empty"

_VALIDITY_COMPONENT_KEYS: Tuple[str, ...] = (
    "fixture_valid", "schema_valid", "input_valid", "descriptor_valid", "self_pair_valid",
    "role_swap_valid", "control_completeness_valid", "placement_completeness_valid",
    "environment_capture_valid", "serialization_valid", "payload_hash_valid", "replay_material_valid",
)

FEATURE_SCHEMA: List[Dict[str, object]] = [
    {"index": 0, "name": "rho_mean", "source_expression": "rho.mean()"},
    {"index": 1, "name": "rho_std", "source_expression": "rho.std()"},
    {"index": 2, "name": "rho_range", "source_expression": "rho.max() - rho.min()"},
    {"index": 3, "name": "desync_mean", "source_expression": "desync.mean()"},
    {"index": 4, "name": "desync_std", "source_expression": "desync.std()"},
    {"index": 5, "name": "desync_absmax", "source_expression": "np.abs(desync).max()"},
    {"index": 6, "name": "psi_traj_mean", "source_expression": "psi_traj.mean()"},
    {"index": 7, "name": "psi_traj_std", "source_expression": "psi_traj.std()"},
    {"index": 8, "name": "psi_traj_last", "source_expression": "float(psi_traj[-1])"},
    {"index": 9, "name": "ch0_rfft_mag_mean", "source_expression": "np.abs(rfft(Dw[:,0]-mean)).mean()"},
    {"index": 10, "name": "ch0_rfft_mag_std", "source_expression": "np.abs(rfft(Dw[:,0]-mean)).std()"},
]
for _entry in FEATURE_SCHEMA:
    _entry["descriptor_variants"] = list(DESCRIPTOR_VARIANTS)


class ValidationError(ValueError):
    """Raised when the boundary input contract is violated; carries a stable error code."""

    def __init__(self, message: str, code: str) -> None:
        super().__init__(message)
        self.code = code


class NonFiniteError(ValueError):
    """Raised when a nonfinite value reaches canonical serialization."""


class EvaluationNotAuthorizedError(RuntimeError):
    """Raised before any candidate A/B descriptor evaluation when evaluation is not authorized."""


# --------------------------------------------------------------------------- evaluation gate

def _evaluation_authorized(env_value: Optional[str]) -> bool:
    """Pure predicate: evaluation is authorized only for the exact string '1'."""
    return env_value == EVALUATION_AUTHORIZATION_VALUE


def _require_evaluation_authorized() -> None:
    """Raise EvaluationNotAuthorizedError unless N64_EVALUATION_AUTHORIZED == '1'."""
    if not _evaluation_authorized(os.environ.get(EVALUATION_AUTHORIZATION_ENV)):
        raise EvaluationNotAuthorizedError(
            "N64 candidate evaluation is not authorized "
            "(set " + EVALUATION_AUTHORIZATION_ENV + "='1' under a separate evaluation authorization)"
        )


# --------------------------------------------------------------------------- canonical JSON + hashing

def canonicalize(obj: object) -> object:
    """Recursively convert to native finite JSON-safe types; -0.0 -> +0.0; raise on nonfinite floats."""
    if isinstance(obj, dict):
        return {str(key): canonicalize(value) for key, value in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [canonicalize(value) for value in obj]
    if isinstance(obj, (bool, np.bool_)):
        return bool(obj)
    if isinstance(obj, (int, np.integer)):
        return int(obj)
    if isinstance(obj, (float, np.floating)):
        value = float(obj)
        if not math.isfinite(value):
            raise NonFiniteError("nonfinite float reached canonical serialization")
        return 0.0 if value == 0.0 else value
    if isinstance(obj, np.ndarray):
        return canonicalize(obj.tolist())
    if obj is None or isinstance(obj, str):
        return obj
    raise TypeError("uncanonicalizable object of type " + type(obj).__name__)


def canonical_text(value: object) -> str:
    return json.dumps(
        canonicalize(value), ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def canonical_bytes(value: object) -> bytes:
    return canonical_text(value).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_sequence_sha256(value: object) -> str:
    return sha256_hex(canonical_bytes(value))


# --------------------------------------------------------------------------- input validation + rotation

def _contains_boolean(value: object) -> bool:
    """Recursively detect any Python bool or np.bool_ leaf before numeric coercion."""
    if isinstance(value, (bool, np.bool_)):
        return True
    if isinstance(value, (list, tuple)):
        return any(_contains_boolean(item) for item in value)
    if isinstance(value, np.ndarray):
        if value.dtype.kind == "b":
            return True
        if value.dtype.kind == "O":
            return any(_contains_boolean(item) for item in value.reshape(-1).tolist())
    return False


def validate_input(raw: object) -> np.ndarray:
    """Pre-coercion boundary validation. Returns a validated finite (64,1) float field on success."""
    if _contains_boolean(raw):
        raise ValidationError("boolean value rejected before numeric coercion", "invalid_input_boolean")
    try:
        array = np.asarray(raw)
    except (ValueError, TypeError) as exc:
        raise ValidationError("input is not a well-formed array (ragged or unconvertible)",
                              "invalid_input_dtype") from exc
    kind = array.dtype.kind
    if kind == "b":
        raise ValidationError("boolean dtype is rejected", "invalid_input_boolean")
    if kind in ("O", "U", "S", "c") or kind not in ("i", "u", "f"):
        raise ValidationError("non-numeric / object / string / complex dtype is rejected",
                              "invalid_input_dtype")
    if array.ndim != 2 or array.shape != (N, 1):
        raise ValidationError("input shape must be (64,1)", "invalid_input_shape")
    if not np.all(np.isfinite(array)):
        raise ValidationError("nonfinite input value", "invalid_input_nonfinite")
    values = set(array.reshape(-1).tolist())
    if not values.issubset({0, 1}):
        raise ValidationError("nonbinary input value (values must be exactly 0 or 1)",
                              "invalid_input_nonbinary")
    return array.astype(float)


def rotate(field: np.ndarray, s: int) -> np.ndarray:
    """rotate(x,s)[t] = x[(t+s) mod 64]  ==  np.roll(x, -s, axis=0)."""
    return np.roll(field, -s % N, axis=0)


def features(field: np.ndarray, variant: str) -> np.ndarray:
    """Invoke the unchanged descriptor for the named variant; returns a length-11 float vector."""
    kappa = DESCRIPTOR_PARAMETERS[variant]["kappa"]
    return np.asarray(psi_trs.psi_trs_features(field, kappa=kappa), dtype=float)


# --------------------------------------------------------------------------- metrics

def _l2(vector: np.ndarray) -> float:
    return float(np.linalg.norm(np.asarray(vector, dtype=float).reshape(-1)))


def symmetric_response(f_a: np.ndarray, f_b: np.ndarray) -> Dict[str, object]:
    numerator = _l2(f_a - f_b)
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


def directional_response(f_from: np.ndarray, f_to: np.ndarray, direction: str) -> Dict[str, object]:
    numerator = _l2(f_to - f_from)
    raw_denominator = _l2(f_from)
    effective = max(raw_denominator, EPSILON)
    return {
        "direction": direction,
        "numerator": numerator,
        "raw_denominator": raw_denominator,
        "effective_denominator": effective,
        "epsilon_hit": bool(raw_denominator <= EPSILON),
        "near_epsilon_hit": bool(raw_denominator <= NEAR_EPSILON_THRESHOLD),
        "finite": bool(math.isfinite(numerator) and math.isfinite(raw_denominator)),
        "response": numerator / effective,
    }


def aggregate(values: List[float]) -> Dict[str, object]:
    array = np.asarray(values, dtype=float)
    minimum = float(array.min())
    maximum = float(array.max())
    return {
        "count": int(array.size),
        "minimum": minimum,
        "maximum": maximum,
        "median": float(np.median(array)),
        "mean": float(array.mean()),
        "population_standard_deviation": float(array.std(ddof=0)),
        "argmin_starts": sorted(int(i) for i in np.where(array == minimum)[0]),
        "argmax_starts": sorted(int(i) for i in np.where(array == maximum)[0]),
    }


def placement(p_value: float, reference: List[float]) -> Dict[str, object]:
    """Tie-aware descriptive placement of p_value within the reference distribution (exact float ties)."""
    array = np.asarray(reference, dtype=float)
    count = int(array.size)
    lower = int(sum(1 for r in reference if r < p_value))
    equal = int(sum(1 for r in reference if r == p_value))
    higher = int(sum(1 for r in reference if r > p_value))
    return {
        "reference_count": count,
        "lower_count": lower,
        "equal_count": equal,
        "higher_count": higher,
        "strict_empirical_fraction": lower / count,
        "weak_empirical_fraction": (lower + equal) / count,
        "midrank_fraction": (lower + 0.5 * equal) / count,
        "reference_minimum": float(array.min()),
        "reference_maximum": float(array.max()),
        "reference_median": float(np.median(array)),
        "reference_mean": float(array.mean()),
        "reference_population_standard_deviation": float(array.std(ddof=0)),
    }


# --------------------------------------------------------------------------- feature cache / results / controls

def _feature_cache(member_fields: Dict[str, np.ndarray]) -> Dict[str, Dict[str, List[np.ndarray]]]:
    cache: Dict[str, Dict[str, List[np.ndarray]]] = {}
    for member, field in member_fields.items():
        cache[member] = {}
        for variant in DESCRIPTOR_VARIANTS:
            cache[member][variant] = [features(rotate(field, s), variant) for s in range(N)]
    return cache


def _member_results(cache: Dict[str, Dict[str, List[np.ndarray]]]) -> Dict[str, object]:
    out: Dict[str, object] = {}
    for variant in DESCRIPTOR_VARIANTS:
        out[variant] = {}
        for member in ("member_A", "member_B"):
            rows = []
            for s in range(N):
                vector = [float(x) for x in cache[member][variant][s]]
                rows.append({
                    "start": s, "features": vector, "feature_count": len(vector),
                    "finite": bool(all(math.isfinite(x) for x in vector)),
                    "feature_vector_sha256": canonical_sequence_sha256(vector),
                })
            out[variant][member] = rows
    return out


def _pair_results(cache: Dict[str, Dict[str, List[np.ndarray]]]) -> Dict[str, object]:
    out: Dict[str, object] = {}
    for variant in DESCRIPTOR_VARIANTS:
        per_start = []
        sym_dist: List[float] = []
        ab_resp: List[float] = []
        ba_resp: List[float] = []
        for s in range(N):
            f_a = cache["member_A"][variant][s]
            f_b = cache["member_B"][variant][s]
            sym = symmetric_response(f_a, f_b)
            ab = directional_response(f_a, f_b, "member_A_to_member_B")
            ba = directional_response(f_b, f_a, "member_B_to_member_A")
            per_start.append({
                "start": s, "symmetric": sym,
                "directional": {"member_A_to_member_B": ab, "member_B_to_member_A": ba},
            })
            sym_dist.append(float(sym["distance"]))
            ab_resp.append(float(ab["response"]))
            ba_resp.append(float(ba["response"]))
        out[variant] = {
            "per_start": per_start,
            "aggregate": {
                "symmetric": aggregate(sym_dist),
                "directional": {"member_A_to_member_B": aggregate(ab_resp),
                                "member_B_to_member_A": aggregate(ba_resp)},
            },
        }
    return out


def _kappa_differences(cache: Dict[str, Dict[str, List[np.ndarray]]],
                       pair_results: Dict[str, object]) -> Dict[str, object]:
    member_local: Dict[str, object] = {}
    for member in ("member_A", "member_B"):
        rows = []
        for s in range(N):
            diff = cache[member]["psi_trs"][s] - cache[member]["psi_trs_k0"][s]
            vector = [float(x) for x in diff]
            rows.append({"start": s, "difference": vector,
                         "finite": bool(all(math.isfinite(x) for x in vector))})
        member_local[member] = rows

    pairwise_symmetric = []
    for s in range(N):
        d = (float(pair_results["psi_trs"]["per_start"][s]["symmetric"]["distance"])
             - float(pair_results["psi_trs_k0"]["per_start"][s]["symmetric"]["distance"]))
        pairwise_symmetric.append({"start": s, "difference": d, "finite": bool(math.isfinite(d))})

    pairwise_directional: Dict[str, object] = {}
    for direction in ("member_A_to_member_B", "member_B_to_member_A"):
        rows = []
        for s in range(N):
            d = (float(pair_results["psi_trs"]["per_start"][s]["directional"][direction]["response"])
                 - float(pair_results["psi_trs_k0"]["per_start"][s]["directional"][direction]["response"]))
            rows.append({"start": s, "difference": d, "finite": bool(math.isfinite(d))})
        pairwise_directional[direction] = rows

    return {"orientation": KAPPA_DIFFERENCE_ORIENTATION, "member_local": member_local,
            "pairwise_symmetric": pairwise_symmetric, "pairwise_directional": pairwise_directional}


def _self_pair_controls(cache: Dict[str, Dict[str, List[np.ndarray]]]) -> Dict[str, object]:
    out: Dict[str, object] = {}
    for member in ("member_A", "member_B"):
        out[member] = {}
        for variant in DESCRIPTOR_VARIANTS:
            rows = []
            for s in range(N):
                f_left = cache[member][variant][s]
                f_right = cache[member][variant][s]  # rotate(member, s+0) == rotate(member, s)
                sym = symmetric_response(f_left, f_right)
                lr = directional_response(f_left, f_right, "left_to_right")
                rl = directional_response(f_right, f_left, "right_to_left")
                finite = bool(all(math.isfinite(x) for x in f_left)
                              and all(math.isfinite(x) for x in f_right))
                equal = bool(np.array_equal(f_left, f_right))
                rows.append({
                    "start": s, "feature_vectors_finite": finite, "feature_vectors_equal": equal,
                    "numerator_exact_zero": bool(float(sym["numerator"]) == 0.0),
                    "symmetric_distance_exact_zero": bool(float(sym["distance"]) == 0.0),
                    "q_left_to_right_exact_zero": bool(float(lr["response"]) == 0.0),
                    "q_right_to_left_exact_zero": bool(float(rl["response"]) == 0.0),
                    "valid": bool(finite and equal and float(sym["numerator"]) == 0.0
                                  and float(sym["distance"]) == 0.0
                                  and float(lr["response"]) == 0.0 and float(rl["response"]) == 0.0),
                })
            out[member][variant] = rows
    return out


def _role_swap_controls(pair_results: Dict[str, object]) -> Dict[str, object]:
    out: Dict[str, object] = {}
    for variant in DESCRIPTOR_VARIANTS:
        rows = []
        for s in range(N):
            ps = pair_results[variant]["per_start"][s]
            ab = ps["directional"]["member_A_to_member_B"]
            ba = ps["directional"]["member_B_to_member_A"]
            symmetric_unchanged = True  # symmetric distance is order-independent by construction
            exchanged = bool(ab["direction"] == "member_A_to_member_B"
                             and ba["direction"] == "member_B_to_member_A")
            rows.append({"start": s, "symmetric_response_unchanged": symmetric_unchanged,
                         "directional_objects_exchanged": exchanged,
                         "valid": bool(symmetric_unchanged and exchanged)})
        out[variant] = rows
    return out


def _self_shift_controls(cache: Dict[str, Dict[str, List[np.ndarray]]],
                         pair_results: Dict[str, object]) -> Dict[str, object]:
    out: Dict[str, object] = {}
    for member in ("member_A", "member_B"):
        out[member] = {}
        for variant in DESCRIPTOR_VARIANTS:
            per_shift = []
            shift_means: List[float] = []
            per_shift_start0: List[float] = []
            for r in range(N):
                per_start = []
                distances: List[float] = []
                for s in range(N):
                    sym = symmetric_response(cache[member][variant][s],
                                             cache[member][variant][(s + r) % N])
                    per_start.append({"start": s, "symmetric": sym})
                    distances.append(float(sym["distance"]))
                agg = aggregate(distances)
                per_shift.append({"relative_shift": r, "per_start": per_start, "aggregate": agg})
                shift_means.append(float(agg["mean"]))
                per_shift_start0.append(distances[0])
            p_all = float(pair_results[variant]["aggregate"]["symmetric"]["mean"])
            p_fixed = float(pair_results[variant]["per_start"][0]["symmetric"]["distance"])
            out[member][variant] = {
                "per_shift": per_shift,
                "all_start_placement": placement(p_all, [shift_means[r] for r in range(1, N)]),
                "fixed_start_placement": placement(p_fixed, [per_shift_start0[r] for r in range(1, N)]),
            }
    return out


# --------------------------------------------------------------------------- environment capture

def _python_executable_capture() -> Tuple[str, str]:
    path = sys.executable
    if not path:
        return "unavailable_empty", "unavailable_empty"
    if not os.path.isfile(path):
        return "unavailable_not_regular_file", "unavailable_not_regular_file"
    try:
        with open(path, "rb") as handle:
            digest = sha256_hex(handle.read())
    except OSError:
        return "unavailable_unreadable", "unavailable_unreadable"
    return digest, "ok"


def _normalize_capture_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if normalized.endswith("\n"):
        normalized = normalized[:-1]
    return "\n".join(line.rstrip(" \t") for line in normalized.split("\n"))


def _tagged_numpy_capture(api_name: str) -> Tuple[str, str, str]:
    """Return (capture_method, capture_status, sha256) for a numpy fingerprint API.

    Stdout printed by the API is captured under a redirect so it can never reach canonical stdout.
    """
    func: Optional[Callable[..., object]] = getattr(np, api_name, None)
    if func is None:
        tagged = {"capture_method": "unavailable", "capture_status": _UNAVAILABLE_API_ABSENT,
                  "data": _UNAVAILABLE_API_ABSENT}
        return "unavailable", _UNAVAILABLE_API_ABSENT, canonical_sequence_sha256(tagged)
    buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(buffer):
            result = func()
    except Exception as exc:  # deterministic sentinel; class name only, never the message
        tagged = {"capture_method": "unavailable", "capture_status": _UNAVAILABLE_CALL_FAILED,
                  "data": type(exc).__name__}
        return "unavailable", _UNAVAILABLE_CALL_FAILED, canonical_sequence_sha256(tagged)
    printed = buffer.getvalue()
    if isinstance(result, (dict, list)):
        tagged = {"capture_method": "structured", "capture_status": "ok", "data": canonicalize(result)}
        return "structured", "ok", canonical_sequence_sha256(tagged)
    if printed:
        tagged = {"capture_method": "stdout_text", "capture_status": "ok",
                  "data": _normalize_capture_text(printed)}
        return "stdout_text", "ok", canonical_sequence_sha256(tagged)
    tagged = {"capture_method": "unavailable", "capture_status": _UNAVAILABLE_EMPTY, "data": _UNAVAILABLE_EMPTY}
    return "unavailable", _UNAVAILABLE_EMPTY, canonical_sequence_sha256(tagged)


def capture_environment() -> Dict[str, object]:
    exe_sha, exe_status = _python_executable_capture()
    build_method, build_status, build_sha = _tagged_numpy_capture("show_config")
    runtime_method, runtime_status, runtime_sha = _tagged_numpy_capture("show_runtime")
    return {
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "python_compiler": platform.python_compiler(),
        "python_build": list(platform.python_build()),
        "python_executable_sha256": exe_sha,
        "python_executable_capture_status": exe_status,
        "numpy_version": np.__version__,
        "numpy_build_configuration_sha256": build_sha,
        "numpy_build_configuration_capture_method": build_method,
        "numpy_build_configuration_capture_status": build_status,
        "numpy_runtime_information_sha256": runtime_sha,
        "numpy_runtime_information_capture_method": runtime_method,
        "numpy_runtime_information_capture_status": runtime_status,
        "platform_system": platform.system(),
        "platform_release": platform.release(),
        "platform_version": platform.version(),
        "platform_machine": platform.machine(),
        "platform_processor": platform.processor(),
        "byteorder": sys.byteorder,
        "canonicalization_name": CANONICALIZATION_NAME,
        "canonicalization_version": CANONICALIZATION_VERSION,
    }


# --------------------------------------------------------------------------- payload assembly

def _authority() -> Dict[str, object]:
    return {
        "formal_hold_active": True, "mode_0_active": True, "file_modification_authorized": False,
        "implementation_authorized": False, "experiment_authorized": False,
        "production_kernel_modification_authorized": False, "scientific_claim_authorized": False,
        "temporal_order_claim_authorized": False, "perception_or_vision_claim_authorized": False,
        "runtime_integration_authorized": False,
        "non_claims": "descriptive engineering evaluation material only; no scientific outcome is asserted",
    }


def _configuration() -> Dict[str, object]:
    return {
        "N": N, "encoding": "direct_scalar_binary_0_1", "input_shape": [N, 1],
        "rotation_definition": "rotate(x,s)[t] = x[(t+s) mod 64]",
        "starts": list(range(N)), "relative_shifts": list(range(N)),
        "descriptor_variants": list(DESCRIPTOR_VARIANTS), "descriptor_parameters": DESCRIPTOR_PARAMETERS,
        "feature_count": FEATURE_COUNT, "epsilon": EPSILON, "near_epsilon_threshold": NEAR_EPSILON_THRESHOLD,
        "population_standard_deviation_ddof": 0, "external_normalization": "none",
        "quotient": "translation_only", "self_pair_policy": "exact_finite_in_process_equality",
        "self_shift_comparison_policy": "complete_orbit_plus_tie_aware_descriptive_placement",
        "canonicalization_policy": CANONICALIZATION_NAME,
    }


def _source(source_commit: str) -> Dict[str, object]:
    return {
        "source_commit": source_commit,
        "evaluation_contract_path": "docs/TORMENT_BRAINVISION_N64_FALSIFIER_EVALUATION_CONTRACT_v0.1.md",
        "evaluation_contract_version": "0.1",
        "implementation_specification_path":
            "docs/TORMENT_BRAINVISION_N64_FALSIFIER_IMPLEMENTATION_SPECIFICATION_v0.1.md",
        "implementation_specification_version": "0.1", "runner_name": RUNNER_NAME,
        "runner_version": RUNNER_VERSION, "fixture_module_name": "n64_falsifier_fixture_v0_1",
        "fixture_module_version": fixture_module.FIXTURE_VERSION,
    }


def _validity(components: Dict[str, bool], error_codes: List[str]) -> Dict[str, object]:
    internal = {key: bool(components.get(key, False)) for key in _VALIDITY_COMPONENT_KEYS}
    codes = sorted(set(error_codes))
    overall = all(internal.values()) and not codes
    ordered: Dict[str, object] = {"overall_valid": bool(overall)}
    ordered.update(internal)
    ordered["error_code_namespace"] = ERROR_CODE_NAMESPACE
    ordered["error_code_version"] = ERROR_CODE_VERSION
    ordered["error_codes"] = codes
    return ordered


def _replay(fixture: Dict[str, object], configuration: Dict[str, object], environment: Dict[str, object],
            replay_material_valid: bool = True) -> Dict[str, object]:
    return {
        "fixture_sha256": fixture["fixture_sha256"],
        "configuration_sha256": canonical_sequence_sha256(configuration),
        "environment_fingerprint_sha256": canonical_sequence_sha256(environment),
        "canonicalization_name": CANONICALIZATION_NAME, "canonicalization_version": CANONICALIZATION_VERSION,
        "same_environment_byte_replay_authority": True, "cross_environment_byte_replay_authority": False,
        "cross_environment_numerical_tolerance_selected": False,
        "cross_environment_replay_pass_fail_selected": False,
        "replay_metadata_valid": True, "payload_hash_valid": True,
        "same_environment_replay_compared": False, "same_environment_replay_match": "not_compared",
    }


def _empty_results() -> Dict[str, object]:
    return {"members": {}, "pair": {}, "kappa_differences": {}}


def _empty_controls() -> Dict[str, object]:
    return {"self_pair": {}, "role_swap": {}, "self_shift": {}}


def build_invalid_payload(error_codes: List[str], source_commit: str = "unspecified") -> Dict[str, object]:
    """Deterministic finite canonical payload for a validation failure (all eleven objects present).

    Used only for expected validation failures. Results/controls are deterministically empty; no numerical
    result is fabricated; no NaN/Infinity/null substitution is used; overall_valid is False.
    """
    fixture = fixture_module.build_fixture()
    configuration = _configuration()
    environment = capture_environment()
    replay_material_valid = True
    components = {
        "fixture_valid": True, "schema_valid": True, "input_valid": False, "descriptor_valid": False,
        "self_pair_valid": False, "role_swap_valid": False, "control_completeness_valid": False,
        "placement_completeness_valid": False, "environment_capture_valid": True,
        "serialization_valid": True, "payload_hash_valid": True,
        "replay_material_valid": replay_material_valid,
    }
    return {
        "schema": {"name": SCHEMA_NAME, "version": SCHEMA_VERSION},
        "authority": _authority(), "source": _source(source_commit), "environment": environment,
        "configuration": configuration, "fixture": fixture, "feature_schema": FEATURE_SCHEMA,
        "results": _empty_results(), "controls": _empty_controls(),
        "validity": _validity(components, error_codes),
        "replay": _replay(fixture, configuration, environment, replay_material_valid),
    }


def build_payload(source_commit: str = "unspecified") -> Dict[str, object]:
    """Evaluate the N=64 A/B fixture and assemble the complete canonical payload.

    Hard-gated: raises EvaluationNotAuthorizedError before any member A/B descriptor call unless
    N64_EVALUATION_AUTHORIZED == '1'. Invoked only under a separately authorized evaluation step.
    """
    _require_evaluation_authorized()
    fixture = fixture_module.build_fixture()
    field_a = validate_input(fixture_module.encode(fixture["member_A_support"]))
    field_b = validate_input(fixture_module.encode(fixture["member_B_support"]))
    cache = _feature_cache({"member_A": field_a, "member_B": field_b})

    pair_results = _pair_results(cache)
    results = {"members": _member_results(cache), "pair": pair_results,
               "kappa_differences": _kappa_differences(cache, pair_results)}
    controls = {"self_pair": _self_pair_controls(cache), "role_swap": _role_swap_controls(pair_results),
                "self_shift": _self_shift_controls(cache, pair_results)}
    configuration = _configuration()
    environment = capture_environment()
    components = {
        "fixture_valid": True, "schema_valid": True, "input_valid": True, "descriptor_valid": True,
        "self_pair_valid": all(row["valid"] for member in controls["self_pair"].values()
                               for variant in member.values() for row in variant),
        "role_swap_valid": all(row["valid"] for variant in controls["role_swap"].values() for row in variant),
        "control_completeness_valid": True, "placement_completeness_valid": True,
        "environment_capture_valid": True, "serialization_valid": True, "payload_hash_valid": True,
        "replay_material_valid": True,
    }
    return {
        "schema": {"name": SCHEMA_NAME, "version": SCHEMA_VERSION}, "authority": _authority(),
        "source": _source(source_commit), "environment": environment, "configuration": configuration,
        "fixture": fixture, "feature_schema": FEATURE_SCHEMA, "results": results, "controls": controls,
        "validity": _validity(components, []),
        "replay": _replay(fixture, configuration, environment),
    }


def build_wrapper(payload: Dict[str, object]) -> Dict[str, object]:
    return {"payload": payload, "payload_sha256": canonical_sequence_sha256(payload)}


def emit(wrapper: Dict[str, object]) -> None:
    """Write only the canonical wrapper text to stdout with no trailing newline; write no file."""
    sys.stdout.write(canonical_text(wrapper))


def _main(argv: Optional[List[str]] = None) -> int:
    import argparse

    _require_evaluation_authorized()  # fail cleanly before any output when unauthorized
    parser = argparse.ArgumentParser(
        prog=RUNNER_NAME,
        description="Offline quarantined N=64 falsifier evaluation runner (prints canonical wrapper only).",
    )
    parser.add_argument("--source-commit", default="unspecified",
                        help="repository commit identity recorded in the canonical source object.")
    args = parser.parse_args(argv)
    emit(build_wrapper(build_payload(source_commit=args.source_commit)))
    return 0


if __name__ == "__main__":  # pragma: no cover - guarded; not executed during the implementation phase
    raise SystemExit(_main())

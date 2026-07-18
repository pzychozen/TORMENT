"""Independent higher-order witness verifier (offline; integer-exact; descriptor-blind).

Recomputes every witness certificate from raw supports using integer arithmetic only. Imports no generator, no
psi_trs, no run_n64_falsifier_v0_1, no N64 mathematical helpers, and no shared witness-predicate helpers; the
only project-local import is the zero-mathematics canonical serializer. stdlib only otherwise. Offline,
quarantined, non-runtime, non-production, descriptive. No ΨTRS or descriptor evaluation exists anywhere here.

Governing specifications:
  docs/TORMENT_BRAINVISION_INDEPENDENT_DESCRIPTOR_BLIND_HIGHER_ORDER_WITNESS_FAMILY_IMPLEMENTATION_SPECIFICATION_v0.1.md
  docs/TORMENT_BRAINVISION_INDEPENDENT_HIGHER_ORDER_WITNESS_VERIFIER_AND_FREEZE_INFRASTRUCTURE_IMPLEMENTATION_SPECIFICATION_v0.1.md
"""
from __future__ import annotations

import ast
import os
from math import gcd
from typing import Dict, List, Optional, Tuple

import witness_canonical_json_v0_1 as cjson  # zero witness mathematics (serialization only)

VERIFIER_NAME = "witness_family_verifier_v0_1"
VERIFIER_VERSION = "0.1"
CONFIG_VERSION = "0.1"
FAILURE_PRECEDENCE_VERSION = "0.1"
TRIPLE_FORMULATION_IDENTITY = "production_single_action_relabel_TB_against_TX_uinv"
GROUP_ENUMERATION_ORDER = "complement_flag_then_ascending_unit_then_ascending_translation"

SUPPORTED_MODES = ("REFERENCE_REGRESSION_N12", "PRIMARY_CANDIDATE_N64")
MODE_N = {"REFERENCE_REGRESSION_N12": 12, "PRIMARY_CANDIDATE_N64": 64}
STREAM_SCHEMA_NAME = "brainvision_descriptor_blind_candidate_stream"
STREAM_SCHEMA_VERSION = "0.1"
VALID_TERMINAL_STATUS = ("stream_completed", "budget_exhausted", "route_incomplete", "dependency_unavailable")
K_FAMILY = 3

# ---- failure codes (candidate/family rejection = valid execution) --------------------------------------
CANDIDATE_SCHEMA_INVALID = "CANDIDATE_SCHEMA_INVALID"
CANDIDATE_N_MODE_INVALID = "CANDIDATE_N_MODE_INVALID"
CANDIDATE_SUPPORT_INVALID = "CANDIDATE_SUPPORT_INVALID"
CANDIDATE_NOT_HOMOMETRIC = "CANDIDATE_NOT_HOMOMETRIC"
CANDIDATE_MEMBER_NOT_PRIMITIVE = "CANDIDATE_MEMBER_NOT_PRIMITIVE"
CANDIDATE_AFFINE_EQUIVALENT = "CANDIDATE_AFFINE_EQUIVALENT"
CANDIDATE_COMPLEMENT_IMAGE = "CANDIDATE_COMPLEMENT_IMAGE"
CANDIDATE_AFFINE_PLUS_COMPLEMENT_EQUIVALENT = "CANDIDATE_AFFINE_PLUS_COMPLEMENT_EQUIVALENT"
CANDIDATE_TRIPLE_G_ALIGNABLE = "CANDIDATE_TRIPLE_G_ALIGNABLE"
CANDIDATE_CERTIFICATE_INVALID = "CANDIDATE_CERTIFICATE_INVALID"
FAMILY_MEMBER_REUSED = "FAMILY_MEMBER_REUSED"
FAMILY_MEMBER_G_EQUIVALENT = "FAMILY_MEMBER_G_EQUIVALENT"
FAMILY_AUTOCORRELATION_CLASS_REUSED = "FAMILY_AUTOCORRELATION_CLASS_REUSED"
FAMILY_PAIR_COUNT_INVALID = "FAMILY_PAIR_COUNT_INVALID"
FAMILY_NOT_FREEZABLE = "FAMILY_NOT_FREEZABLE"
# ---- failure codes (invalid execution) -----------------------------------------------------------------
CANDIDATE_STREAM_INVALID = "CANDIDATE_STREAM_INVALID"
CANDIDATE_STREAM_HASH_MISMATCH = "CANDIDATE_STREAM_HASH_MISMATCH"
VERIFIER_REGRESSION_FAILURE = "VERIFIER_REGRESSION_FAILURE"
VERIFIER_CONFIGURATION_INVALID = "VERIFIER_CONFIGURATION_INVALID"
VERIFIER_INTERNAL_DISAGREEMENT = "VERIFIER_INTERNAL_DISAGREEMENT"
SERIALIZATION_FAILURE = "SERIALIZATION_FAILURE"
HASH_IDENTITY_FAILURE = "HASH_IDENTITY_FAILURE"
REPLAY_MISMATCH = "REPLAY_MISMATCH"
FORBIDDEN_IMPORT_DETECTED = "FORBIDDEN_IMPORT_DETECTED"

_CANDIDATE_PRECEDENCE = (
    CANDIDATE_SCHEMA_INVALID, CANDIDATE_N_MODE_INVALID, CANDIDATE_SUPPORT_INVALID, CANDIDATE_NOT_HOMOMETRIC,
    CANDIDATE_MEMBER_NOT_PRIMITIVE, CANDIDATE_AFFINE_EQUIVALENT, CANDIDATE_COMPLEMENT_IMAGE,
    CANDIDATE_AFFINE_PLUS_COMPLEMENT_EQUIVALENT, CANDIDATE_TRIPLE_G_ALIGNABLE, CANDIDATE_CERTIFICATE_INVALID,
)
_ALL_CANDIDATE_CODES = frozenset(_CANDIDATE_PRECEDENCE)

_FORBIDDEN_IMPORT_ROOTS = frozenset({
    "psi_trs", "run_n64_falsifier_v0_1", "run_prerecorded_paired_analysis_v0_1",
    "run_prerecorded_operational_harness_v0_1", "descriptors", "symmetry_gain", "metrics", "baselines",
    "rpsr", "psi_mapping", "real_video",
})
_GENERATOR_HINTS = ("generator",)
_ALLOWED_VERIFIER_ROOTS = frozenset({"__future__", "ast", "os", "math", "typing", "witness_canonical_json_v0_1"})
_ALLOWED_FREEZER_ROOTS = frozenset({"__future__", "os", "typing", "witness_canonical_json_v0_1",
                                    "witness_family_verifier_v0_1"})
_ALLOWED_SERIALIZER_ROOTS = frozenset({"__future__", "hashlib", "json", "typing"})
_WITNESS_MATH_TOKENS = ("autocorrelation", "triple_array", "member_g_equivalence_key", "affine_apply",
                        "primitive_period")
_EXPECTED_MODULES = {"verifier": VERIFIER_NAME + ".py", "serializer": cjson.SERIALIZER_NAME + ".py",
                     "freeze": "witness_family_freeze_v0_1.py"}


def is_strict_int(value: object) -> bool:
    """True iff value is an int and NOT a bool (True/False are never accepted as integers)."""
    return isinstance(value, int) and not isinstance(value, bool)


# ------------------------------------------------------------------ core integer-exact primitives
def validate_support(support: object, n: int) -> bool:
    if not isinstance(support, list) or not support:
        return False
    previous = -1
    for value in support:
        if not is_strict_int(value) or value < 0 or value >= n or value <= previous:
            return False
        previous = value
    return True


def complement(support: List[int], n: int) -> List[int]:
    present = set(support)
    return [t for t in range(n) if t not in present]


def shift_support(support: List[int], r: int, n: int) -> List[int]:
    return sorted((s + r) % n for s in support)


def affine_apply(support: List[int], u: int, a: int, n: int) -> List[int]:
    return sorted((u * s + a) % n for s in support)


def weight(support: List[int]) -> int:
    return len(support)


def autocorrelation(support: List[int], n: int) -> List[int]:
    present = set(support)
    return [sum(1 for t in present if (t + k) % n in present) for k in range(n)]


def one_step_table(support: List[int], n: int) -> Dict[str, int]:
    present = set(support)
    counts = {"c00": 0, "c01": 0, "c10": 0, "c11": 0}
    for t in range(n):
        a = 1 if t in present else 0
        b = 1 if (t + 1) % n in present else 0
        counts["c" + str(a) + str(b)] += 1
    return counts


def transition_multiset(support: List[int], n: int) -> Dict[str, int]:
    present = set(support)
    counts = {"0": 0, "1": 0}
    for t in range(n):
        a = 1 if t in present else 0
        b = 1 if (t + 1) % n in present else 0
        counts[str(abs(b - a))] += 1
    return counts


def triple_array(support: List[int], n: int) -> List[List[int]]:
    present = set(support)
    array = [[0] * n for _ in range(n)]
    for k in range(n):
        for l in range(n):
            array[k][l] = sum(1 for t in present if (t + k) % n in present and (t + l) % n in present)
    return array


def triple_disagreement_count(array_a: List[List[int]], array_b: List[List[int]], n: int) -> int:
    return sum(1 for k in range(n) for l in range(n) if array_a[k][l] != array_b[k][l])


def primitive_period(support: List[int], n: int) -> int:
    present = sorted(support)
    for r in range(1, n):
        if shift_support(present, r, n) == present:
            return r
    return n


def units(n: int) -> List[int]:
    return [u for u in range(1, n) if gcd(u, n) == 1]


def member_g_equivalence_key(support: List[int], n: int) -> List[int]:
    best: Optional[Tuple[int, ...]] = None
    for base in (sorted(support), complement(support, n)):
        for u in units(n):
            for a in range(n):
                candidate = tuple(sorted((u * s + a) % n for s in base))
                if best is None or candidate < best:
                    best = candidate
    return list(best) if best is not None else []


def affine_equivalent(support_a: List[int], support_b: List[int], n: int) -> bool:
    target = tuple(sorted(support_b))
    for u in units(n):
        for a in range(n):
            if tuple(affine_apply(support_a, u, a, n)) == target:
                return True
    return False


def affine_to_complement_equivalent(support_a: List[int], support_b: List[int], n: int) -> bool:
    target = tuple(complement(support_b, n))
    for u in units(n):
        for a in range(n):
            if tuple(affine_apply(support_a, u, a, n)) == target:
                return True
    return False


def direct_complement_image(support_a: List[int], support_b: List[int], n: int) -> bool:
    return tuple(sorted(support_b)) == tuple(complement(support_a, n))


def triple_g_aligned(support_a: List[int], support_b: List[int], n: int) -> bool:
    triple_b = triple_array(support_b, n)
    inverse = {u: pow(u, -1, n) for u in units(n)}
    for base in (sorted(support_a), complement(support_a, n)):
        triple_x = triple_array(base, n)
        for u in units(n):
            u_inv = inverse[u]
            aligned = True
            for k in range(n):
                row = triple_b[k]
                relabel_k = triple_x[(u_inv * k) % n]
                for l in range(n):
                    if row[l] != relabel_k[(u_inv * l) % n]:
                        aligned = False
                        break
                if not aligned:
                    break
            if aligned:
                return True
    return False


def normalize_pair(support_a: object, support_b: object) -> Tuple[List[int], List[int], bool]:
    left, right = sorted(support_a), sorted(support_b)
    return (left, right, False) if left <= right else (right, left, True)


# ------------------------------------------------------------------ safe serialization wrappers
def safe_canonical_bytes(payload: object) -> Tuple[bool, Optional[bytes]]:
    try:
        return True, cjson.canonical_json_bytes(payload)
    except (ValueError, TypeError):
        return False, None


def safe_envelope(name: str, payload: object) -> Tuple[bool, Optional[dict]]:
    try:
        return True, cjson.envelope(name, payload)
    except (ValueError, TypeError):
        return False, None


def serialize_or_failure(payload: object) -> Tuple[Optional[bytes], Optional[str]]:
    ok, data = safe_canonical_bytes(payload)
    return (data, None) if ok else (None, SERIALIZATION_FAILURE)


def envelope_or_failure(name: str, payload: object) -> Tuple[Optional[dict], Optional[str]]:
    ok, env = safe_envelope(name, payload)
    return (env, None) if ok else (None, SERIALIZATION_FAILURE)


def safe_payload_sha256(payload: object) -> Tuple[Optional[str], Optional[str]]:
    data, code = serialize_or_failure(payload)
    if code is not None:
        return None, code
    return cjson.sha256_hex(data), None


# ------------------------------------------------------------------ member / pair certificates
def member_certificate(support: List[int], n: int) -> Dict[str, object]:
    support_sorted = sorted(support)
    return {
        "raw_support": support_sorted,
        "weight": weight(support_sorted),
        "autocorrelation": autocorrelation(support_sorted, n),
        "one_step_table": one_step_table(support_sorted, n),
        "transition_multiset": transition_multiset(support_sorted, n),
        "primitive_period": primitive_period(support_sorted, n),
        "member_G_equivalence_key": member_g_equivalence_key(support_sorted, n),
    }


def _canonical_pair_key(key_a: List[int], key_b: List[int]) -> List[List[int]]:
    first, second = (key_a, key_b) if list(key_a) <= list(key_b) else (key_b, key_a)
    return [list(first), list(second)]


def _reject(code: str) -> Dict[str, object]:
    return {"execution_invalid": False, "execution_code": None, "pair_certificate": None,
            "ordered_failure_codes": [code], "primary_failure_code": code, "pair_valid": False}


def verify_candidate(record: object, n: int) -> Dict[str, object]:
    if not is_strict_int(n):
        return {"execution_invalid": True, "execution_code": VERIFIER_CONFIGURATION_INVALID,
                "pair_certificate": None, "ordered_failure_codes": [], "primary_failure_code": None,
                "pair_valid": False}
    if not isinstance(record, dict) or "raw_support_A" not in record or "raw_support_B" not in record:
        return _reject(CANDIDATE_SCHEMA_INVALID)
    stream_a, stream_b = record["raw_support_A"], record["raw_support_B"]
    if not validate_support(stream_a, n) or not validate_support(stream_b, n):
        return _reject(CANDIDATE_SUPPORT_INVALID)
    if sorted(stream_a) == sorted(stream_b):
        return _reject(CANDIDATE_SUPPORT_INVALID)

    support_a, support_b, roles_swapped = normalize_pair(stream_a, stream_b)
    member_a, member_b = member_certificate(support_a, n), member_certificate(support_b, n)

    autocorrelation_equal = member_a["autocorrelation"] == member_b["autocorrelation"]
    one_step_table_equal = member_a["one_step_table"] == member_b["one_step_table"]
    transition_multiset_equal = member_a["transition_multiset"] == member_b["transition_multiset"]
    if autocorrelation_equal and not (one_step_table_equal and transition_multiset_equal):
        return {"execution_invalid": True, "execution_code": VERIFIER_INTERNAL_DISAGREEMENT,
                "pair_certificate": None, "ordered_failure_codes": [], "primary_failure_code": None,
                "pair_valid": False}

    both_primitive = (member_a["primitive_period"] == n) and (member_b["primitive_period"] == n)
    affine_eq = affine_equivalent(support_a, support_b, n)
    direct_complement = direct_complement_image(support_a, support_b, n)
    affine_plus_complement_eq = affine_to_complement_equivalent(support_a, support_b, n)
    triple_aligned = triple_g_aligned(support_a, support_b, n)
    disagreements = triple_disagreement_count(triple_array(support_a, n), triple_array(support_b, n), n)

    flags: List[str] = []
    if not autocorrelation_equal:
        flags.append(CANDIDATE_NOT_HOMOMETRIC)
    if not both_primitive:
        flags.append(CANDIDATE_MEMBER_NOT_PRIMITIVE)
    if affine_eq:
        flags.append(CANDIDATE_AFFINE_EQUIVALENT)
    if direct_complement:
        flags.append(CANDIDATE_COMPLEMENT_IMAGE)
    if affine_plus_complement_eq:
        flags.append(CANDIDATE_AFFINE_PLUS_COMPLEMENT_EQUIVALENT)
    if triple_aligned:
        flags.append(CANDIDATE_TRIPLE_G_ALIGNABLE)
    ordered = [code for code in _CANDIDATE_PRECEDENCE if code in flags]
    pair_valid = (len(ordered) == 0)

    index = record.get("candidate_generation_index")
    certificate = {
        "member_certificate_A": member_a, "member_certificate_B": member_b,
        "canonical_pair_key": _canonical_pair_key(
            member_a["member_G_equivalence_key"], member_b["member_G_equivalence_key"]),
        "autocorrelation_equal": autocorrelation_equal, "one_step_table_equal": one_step_table_equal,
        "transition_multiset_equal": transition_multiset_equal, "triple_disagreement_count": disagreements,
        "affine_inequivalent": not affine_eq,
        "affine_plus_complement_inequivalent": not affine_plus_complement_eq,
        "direct_complement_image": direct_complement, "triple_G_nonaligned": not triple_aligned,
        "pair_valid": pair_valid, "ordered_failure_codes": ordered,
        "provenance": {
            "stream_raw_support_A": sorted(stream_a), "stream_raw_support_B": sorted(stream_b),
            "normalized_raw_support_A": support_a, "normalized_raw_support_B": support_b,
            "raw_roles_swapped": roles_swapped,
            "candidate_generation_index": (index if is_strict_int(index) else None),
        },
    }
    # Build the actual certificate envelope and validate that exact envelope (same production path used for
    # internally assembled and supplied/replayed certificates).
    certificate_envelope, serialization_code = envelope_or_failure("pair_verifier_certificate", certificate)
    if serialization_code is not None:
        return _reject(CANDIDATE_CERTIFICATE_INVALID)
    valid_cert, cert_code = validate_pair_certificate_envelope(certificate_envelope, n)
    if not valid_cert:
        return {"execution_invalid": False, "execution_code": None, "pair_certificate": None,
                "ordered_failure_codes": [cert_code], "primary_failure_code": cert_code, "pair_valid": False}
    return {"execution_invalid": False, "execution_code": None, "pair_certificate": certificate,
            "ordered_failure_codes": ordered, "primary_failure_code": (ordered[0] if ordered else None),
            "pair_valid": pair_valid}


def certificate_core(certificate: dict) -> dict:
    return {key: value for key, value in certificate.items() if key != "provenance"}


# ------------------------------------------------------------------ complete certificate validation
_MEMBER_FIELDS = ("raw_support", "weight", "autocorrelation", "one_step_table", "transition_multiset",
                  "primitive_period", "member_G_equivalence_key")
_PAIR_FIELDS = ("member_certificate_A", "member_certificate_B", "canonical_pair_key", "autocorrelation_equal",
                "one_step_table_equal", "transition_multiset_equal", "triple_disagreement_count",
                "affine_inequivalent", "affine_plus_complement_inequivalent", "direct_complement_image",
                "triple_G_nonaligned", "pair_valid", "ordered_failure_codes", "provenance")
_PAIR_BOOL_FIELDS = ("autocorrelation_equal", "one_step_table_equal", "transition_multiset_equal",
                     "affine_inequivalent", "affine_plus_complement_inequivalent", "direct_complement_image",
                     "triple_G_nonaligned", "pair_valid")
# Exact allowed key sets (unknown/extra keys are rejected at every certificate level).
_MEMBER_KEYS = frozenset(_MEMBER_FIELDS)
_PAIR_REQUIRED_KEYS = frozenset(_PAIR_FIELDS)
# Exactly the fields emitted by the production pair-certificate builder. The builder emits no schema_name,
# schema_version, or N at pair-payload level, so those (and any other key) are rejected as unknown.
_PAIR_ALLOWED_KEYS = _PAIR_REQUIRED_KEYS
_PROVENANCE_KEYS = frozenset({"stream_raw_support_A", "stream_raw_support_B", "normalized_raw_support_A",
                              "normalized_raw_support_B", "raw_roles_swapped", "candidate_generation_index"})
_PAIR_ENVELOPE_KEYS = frozenset({"pair_verifier_certificate", "pair_verifier_certificate_sha256"})


def _validate_member(member: object, n: int) -> bool:
    if not isinstance(member, dict) or set(member.keys()) != _MEMBER_KEYS:  # exact keys; no extra/missing
        return False
    raw = member["raw_support"]
    if not validate_support(raw, n):
        return False
    if not is_strict_int(member["weight"]) or member["weight"] != len(raw):
        return False
    autocorr = member["autocorrelation"]
    if not isinstance(autocorr, list) or len(autocorr) != n or not all(is_strict_int(x) for x in autocorr):
        return False
    ost = member["one_step_table"]
    if not isinstance(ost, dict) or set(ost.keys()) != {"c00", "c01", "c10", "c11"} \
            or not all(is_strict_int(v) for v in ost.values()) or sum(ost.values()) != n:
        return False
    tm = member["transition_multiset"]
    if not isinstance(tm, dict) or set(tm.keys()) != {"0", "1"} \
            or not all(is_strict_int(v) for v in tm.values()) or sum(tm.values()) != n:
        return False
    if not is_strict_int(member["primitive_period"]) or not (1 <= member["primitive_period"] <= n):
        return False
    key = member["member_G_equivalence_key"]
    if not isinstance(key, list) or not all(is_strict_int(x) for x in key):
        return False
    return True


def _is_subsequence(ordered: List[str], precedence: Tuple[str, ...]) -> bool:
    iterator = iter(precedence)
    return all(code in iterator for code in ordered)


def _validate_provenance(provenance: object, certificate: dict, n: int) -> bool:
    if not isinstance(provenance, dict):
        return False
    required = {"stream_raw_support_A", "stream_raw_support_B", "normalized_raw_support_A",
                "normalized_raw_support_B", "raw_roles_swapped", "candidate_generation_index"}
    if set(provenance.keys()) != required:
        return False
    stream_a, stream_b = provenance["stream_raw_support_A"], provenance["stream_raw_support_B"]
    if not validate_support(stream_a, n) or not validate_support(stream_b, n):
        return False
    if not isinstance(provenance["raw_roles_swapped"], bool):
        return False
    normalized_a, normalized_b = provenance["normalized_raw_support_A"], provenance["normalized_raw_support_B"]
    if normalized_a != certificate["member_certificate_A"]["raw_support"] \
            or normalized_b != certificate["member_certificate_B"]["raw_support"]:
        return False
    if list(normalized_a) > list(normalized_b):
        return False
    expected_a, expected_b, expected_swapped = normalize_pair(stream_a, stream_b)
    if normalized_a != expected_a or normalized_b != expected_b \
            or provenance["raw_roles_swapped"] != expected_swapped:
        return False
    index = provenance["candidate_generation_index"]
    if index is not None and not is_strict_int(index):
        return False
    return True


def validate_pair_certificate(certificate: object, n: int) -> Tuple[bool, Optional[str]]:
    """Complete pair-certificate PAYLOAD schema + consistency + provenance validation (exact keys, no extras)."""
    if not isinstance(certificate, dict):
        return False, CANDIDATE_CERTIFICATE_INVALID
    if set(certificate.keys()) != _PAIR_ALLOWED_KEYS:  # exact production key set; reject unknown/missing
        return False, CANDIDATE_CERTIFICATE_INVALID
    if not _validate_member(certificate["member_certificate_A"], n) \
            or not _validate_member(certificate["member_certificate_B"], n):
        return False, CANDIDATE_CERTIFICATE_INVALID
    key = certificate["canonical_pair_key"]
    if not isinstance(key, list) or len(key) != 2 \
            or not all(isinstance(k, list) and all(is_strict_int(x) for x in k) for k in key):
        return False, CANDIDATE_CERTIFICATE_INVALID
    if list(key[0]) > list(key[1]):
        return False, CANDIDATE_CERTIFICATE_INVALID
    expected_keys = sorted([list(certificate["member_certificate_A"]["member_G_equivalence_key"]),
                            list(certificate["member_certificate_B"]["member_G_equivalence_key"])])
    if [list(key[0]), list(key[1])] != expected_keys:
        return False, CANDIDATE_CERTIFICATE_INVALID
    tdc = certificate["triple_disagreement_count"]
    if not is_strict_int(tdc) or not (0 <= tdc <= n * n):
        return False, CANDIDATE_CERTIFICATE_INVALID
    if any(not isinstance(certificate[field], bool) for field in _PAIR_BOOL_FIELDS):
        return False, CANDIDATE_CERTIFICATE_INVALID
    ordered = certificate["ordered_failure_codes"]
    if not isinstance(ordered, list) or not all(isinstance(c, str) and c in _ALL_CANDIDATE_CODES for c in ordered) \
            or not _is_subsequence(ordered, _CANDIDATE_PRECEDENCE):
        return False, CANDIDATE_CERTIFICATE_INVALID
    if not _validate_provenance(certificate["provenance"], certificate, n):
        return False, CANDIDATE_CERTIFICATE_INVALID
    expected_valid = (
        certificate["autocorrelation_equal"] and certificate["one_step_table_equal"]
        and certificate["transition_multiset_equal"] and certificate["affine_inequivalent"]
        and certificate["affine_plus_complement_inequivalent"] and not certificate["direct_complement_image"]
        and certificate["triple_G_nonaligned"]
        and certificate["member_certificate_A"]["primitive_period"] == n
        and certificate["member_certificate_B"]["primitive_period"] == n and len(ordered) == 0)
    if bool(certificate["pair_valid"]) != bool(expected_valid):
        return False, CANDIDATE_CERTIFICATE_INVALID
    _data, serialization_code = serialize_or_failure(certificate)   # payload must be canonically serializable
    if serialization_code is not None:
        return False, CANDIDATE_CERTIFICATE_INVALID
    return True, None


def validate_pair_certificate_envelope(envelope: object, n: int) -> Tuple[bool, Optional[str]]:
    """Validate the ACTUAL supplied pair-certificate envelope: exact envelope keys, payload schema, and that the
    supplied SHA-256 matches SHA256(canonical_json_bytes(supplied_payload)). The envelope is not mutated."""
    if not isinstance(envelope, dict) or set(envelope.keys()) != _PAIR_ENVELOPE_KEYS:
        return False, CANDIDATE_CERTIFICATE_INVALID
    payload = envelope["pair_verifier_certificate"]
    ok, code = validate_pair_certificate(payload, n)
    if not ok:
        return False, code
    supplied_hash = envelope["pair_verifier_certificate_sha256"]
    if not cjson.is_lower_hex_64(supplied_hash):
        return False, CANDIDATE_CERTIFICATE_INVALID
    recomputed, serialization_code = safe_payload_sha256(payload)
    if serialization_code is not None or recomputed != supplied_hash:
        return False, CANDIDATE_CERTIFICATE_INVALID
    return True, None


def verify_family(pair_certificates: List[dict], n: int) -> Dict[str, object]:
    ordered: List[str] = []
    if len(pair_certificates) != K_FAMILY:
        return {"family_valid": False, "ordered_failure_codes": [FAMILY_PAIR_COUNT_INVALID],
                "mutual_G_inequivalent": False, "members_non_reused": False,
                "distinct_autocorrelation_classes": False}
    members, keys, classes = [], [], []
    for certificate in pair_certificates:
        for side in ("member_certificate_A", "member_certificate_B"):
            members.append(tuple(certificate[side]["raw_support"]))
            keys.append(tuple(certificate[side]["member_G_equivalence_key"]))
        classes.append(tuple(certificate["member_certificate_A"]["autocorrelation"]))
    members_non_reused = len(set(members)) == len(members)
    mutual_g_inequivalent = len(set(keys)) == len(keys)
    distinct_classes = len(set(classes)) == len(classes)
    all_pairs_valid = all(certificate["pair_valid"] for certificate in pair_certificates)
    if not members_non_reused:
        ordered.append(FAMILY_MEMBER_REUSED)
    if not mutual_g_inequivalent:
        ordered.append(FAMILY_MEMBER_G_EQUIVALENT)
    if not distinct_classes:
        ordered.append(FAMILY_AUTOCORRELATION_CLASS_REUSED)
    family_valid = (members_non_reused and mutual_g_inequivalent and distinct_classes and all_pairs_valid)
    if not family_valid and not ordered:
        ordered.append(FAMILY_NOT_FREEZABLE)
    return {"family_valid": family_valid, "ordered_failure_codes": ordered,
            "mutual_G_inequivalent": mutual_g_inequivalent, "members_non_reused": members_non_reused,
            "distinct_autocorrelation_classes": distinct_classes}


# ------------------------------------------------------------------ candidate-stream validation (safe hashing)
def _stream_invalid(code: str) -> Dict[str, object]:
    return {"valid": False, "code": code, "payload": None, "mode": None, "n": None}


def validate_stream_envelope(envelope_obj: object) -> Dict[str, object]:
    """Validate the candidate_stream_envelope. All hashing goes through safe wrappers: unserializable content
    (e.g. nonfinite generator_diagnostics) yields SERIALIZATION_FAILURE and never raises to the caller."""
    if not isinstance(envelope_obj, dict) or "candidate_stream" not in envelope_obj \
            or "candidate_stream_sha256" not in envelope_obj:
        return _stream_invalid(CANDIDATE_STREAM_INVALID)
    payload = envelope_obj["candidate_stream"]
    if not isinstance(payload, dict):
        return _stream_invalid(CANDIDATE_STREAM_INVALID)
    digest, code = safe_payload_sha256(payload)             # untrusted content (incl. generator_diagnostics)
    if code is not None:
        return _stream_invalid(SERIALIZATION_FAILURE)
    if digest != envelope_obj["candidate_stream_sha256"]:
        return _stream_invalid(CANDIDATE_STREAM_HASH_MISMATCH)
    required = ("schema_name", "schema_version", "verification_mode", "N", "generator_identity_hash",
                "generator_configuration_hash", "budget_identity_hash", "records", "candidate_count",
                "terminal_status")
    for field in required:
        if field not in payload:
            return _stream_invalid(CANDIDATE_STREAM_INVALID)
    if payload["schema_name"] != STREAM_SCHEMA_NAME or payload["schema_version"] != STREAM_SCHEMA_VERSION:
        return _stream_invalid(CANDIDATE_STREAM_INVALID)
    for hash_field in ("generator_identity_hash", "generator_configuration_hash", "budget_identity_hash"):
        if not cjson.is_lower_hex_64(payload[hash_field]):
            return _stream_invalid(CANDIDATE_STREAM_INVALID)
    if payload["terminal_status"] not in VALID_TERMINAL_STATUS:
        return _stream_invalid(CANDIDATE_STREAM_INVALID)
    records = payload["records"]
    if not isinstance(records, list) or not is_strict_int(payload["candidate_count"]) \
            or payload["candidate_count"] != len(records):
        return _stream_invalid(CANDIDATE_STREAM_INVALID)
    for index, record in enumerate(records):
        if not isinstance(record, dict) or not is_strict_int(record.get("candidate_generation_index")) \
                or record.get("candidate_generation_index") != index:
            return _stream_invalid(CANDIDATE_STREAM_INVALID)
    mode, n = payload["verification_mode"], payload["N"]
    if not is_strict_int(n) or mode not in SUPPORTED_MODES or MODE_N.get(mode) != n:
        return {"valid": False, "code": CANDIDATE_N_MODE_INVALID, "payload": payload, "mode": mode, "n": n}
    return {"valid": True, "code": None, "payload": payload, "mode": mode, "n": n}


# ------------------------------------------------------------------ configuration / source-path ownership
def default_repository_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))


def default_source_paths(repository_root: Optional[str] = None) -> Dict[str, str]:
    root = repository_root or default_repository_root()
    return {role: os.path.join(root, "research", "brainvision", filename)
            for role, filename in _EXPECTED_MODULES.items()}


def _contained(child: str, parent: str) -> bool:
    try:
        return os.path.commonpath([parent, child]) == parent
    except ValueError:
        return False


def validate_source_ownership(repository_root: str, source_paths: Dict[str, str]) -> Dict[str, object]:
    """Enforce that every implementation source resolves to its exact expected repository module path."""
    resolved_root = os.path.realpath(repository_root)
    resolved_bv = os.path.realpath(os.path.join(resolved_root, "research", "brainvision"))
    if not os.path.isdir(resolved_bv) or not _contained(resolved_bv, resolved_root):
        return {"valid": False, "code": VERIFIER_CONFIGURATION_INVALID, "stage": "repository_root"}
    identities: Dict[str, object] = {}
    for role, filename in _EXPECTED_MODULES.items():
        candidate = source_paths.get(role)
        if not isinstance(candidate, str):
            return {"valid": False, "code": VERIFIER_CONFIGURATION_INVALID, "stage": "missing_path:" + role}
        resolved = os.path.realpath(candidate)
        if not os.path.isfile(resolved):
            return {"valid": False, "code": VERIFIER_CONFIGURATION_INVALID, "stage": "not_regular_file:" + role}
        if not _contained(resolved, resolved_root) or not _contained(resolved, resolved_bv):
            return {"valid": False, "code": VERIFIER_CONFIGURATION_INVALID, "stage": "outside_tree:" + role}
        if resolved != os.path.realpath(os.path.join(resolved_bv, filename)):
            return {"valid": False, "code": VERIFIER_CONFIGURATION_INVALID, "stage": "wrong_module_path:" + role}
        identities[role + "_source_path"] = "research/brainvision/" + filename
        identities[role + "_source_sha256"] = cjson.source_file_sha256(resolved)
        identities[role + "_resolved_path"] = resolved
    return {"valid": True, "code": None, "identities": identities}


def verifier_configuration() -> Dict[str, object]:
    return {
        "verifier_name": VERIFIER_NAME, "verifier_version": VERIFIER_VERSION, "config_version": CONFIG_VERSION,
        "stream_schema_name": STREAM_SCHEMA_NAME, "stream_schema_version": STREAM_SCHEMA_VERSION,
        "verification_modes": list(SUPPORTED_MODES), "mode_N": {m: MODE_N[m] for m in SUPPORTED_MODES},
        "K": K_FAMILY, "canonical_json_policy": "ensure_ascii_sort_keys_compact_no_nan_no_trailing_newline",
        "triple_formulation_identity": TRIPLE_FORMULATION_IDENTITY,
        "group_enumeration_order": GROUP_ENUMERATION_ORDER,
        "failure_code_precedence_version": FAILURE_PRECEDENCE_VERSION,
        "serializer_name": cjson.SERIALIZER_NAME, "serializer_version": cjson.SERIALIZER_VERSION,
    }


def verify_supplied_hash(payload: object, supplied_hash: object) -> Tuple[bool, Optional[str]]:
    if not cjson.is_lower_hex_64(supplied_hash):
        return False, HASH_IDENTITY_FAILURE
    digest, code = safe_payload_sha256(payload)
    if code is not None or digest != supplied_hash:
        return False, HASH_IDENTITY_FAILURE
    return True, None


def validate_local_configuration(repository_root: Optional[str] = None,
                                 source_paths: Optional[Dict[str, str]] = None,
                                 expected_source_hashes: Optional[Dict[str, str]] = None) -> Dict[str, object]:
    """Source-path ownership + configuration self-check. Ownership/config failures -> VERIFIER_CONFIGURATION_INVALID;
    validated-path-but-hash-mismatch -> HASH_IDENTITY_FAILURE."""
    root = repository_root or default_repository_root()
    paths = source_paths or default_source_paths(root)
    ownership = validate_source_ownership(root, paths)
    if not ownership["valid"]:
        return {"valid": False, "code": ownership["code"], "stage": "source_ownership:" + ownership["stage"]}
    identities = ownership["identities"]
    if expected_source_hashes:
        for role, expected in expected_source_hashes.items():
            if identities.get(role + "_source_sha256") != expected:
                return {"valid": False, "code": HASH_IDENTITY_FAILURE, "stage": "source_hash_mismatch:" + role}
    config = verifier_configuration()
    if config["verifier_name"] != VERIFIER_NAME or config["verifier_version"] != VERIFIER_VERSION:
        return {"valid": False, "code": VERIFIER_CONFIGURATION_INVALID, "stage": "identity_name_version"}
    config_hash, code = safe_payload_sha256(config)
    if code is not None:
        return {"valid": False, "code": HASH_IDENTITY_FAILURE, "stage": "config_hash"}
    consistent, hash_code = verify_supplied_hash(config, config_hash)
    if not consistent:
        return {"valid": False, "code": hash_code, "stage": "config_hash_consistency"}
    public_identities = {key: value for key, value in identities.items() if not key.endswith("_resolved_path")}
    return {"valid": True, "code": None, "identities": public_identities,
            "verifier_configuration_payload": config, "verifier_configuration_sha256": config_hash}


# ------------------------------------------------------------------ runtime independence self-check
def _import_roots_from_source(path: str) -> set:
    with open(path, "r", encoding="utf-8") as handle:
        tree = ast.parse(handle.read())
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            roots.add(node.module.split(".")[0])
    return roots


def _forbidden_root(root: str) -> bool:
    return (root in _FORBIDDEN_IMPORT_ROOTS or any(hint in root for hint in _GENERATOR_HINTS)
            or root.startswith("torment_service"))


def independence_self_check(source_paths: Optional[Dict[str, str]] = None) -> Dict[str, object]:
    """AST-only inspection (never imports generator code). Direct + transitive closure from BOTH verifier and
    freezer over the three implementation modules; serializer edges checked. Violation -> FORBIDDEN_IMPORT_DETECTED."""
    paths = source_paths or default_source_paths()
    role_by_module = {os.path.basename(paths[role])[:-3]: role for role in paths}
    project_local = set(role_by_module)
    seen: set = set()
    frontier = ["verifier", "freeze"]
    while frontier:
        role = frontier.pop()
        if role in seen:
            continue
        seen.add(role)
        if role not in paths or not os.path.isfile(paths[role]):
            return {"valid": False, "code": FORBIDDEN_IMPORT_DETECTED, "stage": "missing_source:" + role}
        for root in _import_roots_from_source(paths[role]):
            if _forbidden_root(root):
                return {"valid": False, "code": FORBIDDEN_IMPORT_DETECTED, "stage": "forbidden_import:" + root}
            if root in project_local and role_by_module[root] not in seen:
                frontier.append(role_by_module[root])
    if not _import_roots_from_source(paths["verifier"]).issubset(_ALLOWED_VERIFIER_ROOTS):
        return {"valid": False, "code": FORBIDDEN_IMPORT_DETECTED, "stage": "verifier_import_ownership"}
    if not _import_roots_from_source(paths["freeze"]).issubset(_ALLOWED_FREEZER_ROOTS):
        return {"valid": False, "code": FORBIDDEN_IMPORT_DETECTED, "stage": "freezer_import_ownership"}
    serializer_roots = _import_roots_from_source(paths["serializer"])
    if not serializer_roots.issubset(_ALLOWED_SERIALIZER_ROOTS) \
            or VERIFIER_NAME in serializer_roots or "witness_family_freeze_v0_1" in serializer_roots:
        return {"valid": False, "code": FORBIDDEN_IMPORT_DETECTED, "stage": "serializer_imports"}
    with open(paths["serializer"], "r", encoding="utf-8") as handle:
        serializer_tree = ast.parse(handle.read())
    for node in ast.walk(serializer_tree):
        if isinstance(node, ast.FunctionDef) and any(token in node.name for token in _WITNESS_MATH_TOKENS):
            return {"valid": False, "code": FORBIDDEN_IMPORT_DETECTED, "stage": "serializer_witness_math"}
    return {"valid": True, "code": None}


# ------------------------------------------------------------------ runtime regression self-check
_N12_A = [0, 1, 3, 5, 6]
_N12_B = [0, 1, 2, 4, 7]


def regression_self_check() -> Dict[str, object]:
    result = verify_candidate({"raw_support_A": _N12_A, "raw_support_B": _N12_B,
                               "candidate_generation_index": 0}, 12)
    cert = result["pair_certificate"]
    if result["pair_valid"] is not True or cert is None:
        return {"valid": False, "code": VERIFIER_REGRESSION_FAILURE, "stage": "n12_positive_valid"}
    checks = (
        cert["member_certificate_A"]["autocorrelation"] == [5, 2, 2, 2, 1, 2, 2, 2, 1, 2, 2, 2],
        cert["member_certificate_A"]["one_step_table"] == {"c00": 4, "c01": 3, "c10": 3, "c11": 2},
        cert["member_certificate_A"]["transition_multiset"] == {"0": 6, "1": 6},
        cert["triple_disagreement_count"] == 48,
        cert["member_certificate_A"]["primitive_period"] == 12,
        cert["member_certificate_B"]["primitive_period"] == 12,
        cert["affine_inequivalent"] is True, cert["affine_plus_complement_inequivalent"] is True,
        cert["triple_G_nonaligned"] is True,
    )
    if not all(checks):
        return {"valid": False, "code": VERIFIER_REGRESSION_FAILURE, "stage": "n12_certificates"}
    negatives = (
        verify_candidate({"raw_support_A": [0, 1, 2], "raw_support_B": [0, 3, 7, 9]}, 12)["primary_failure_code"]
        == CANDIDATE_NOT_HOMOMETRIC,
        verify_candidate({"raw_support_A": [0, 1, 2, 3, 4, 7], "raw_support_B": [5, 6, 8, 9, 10, 11]}, 12)
        ["primary_failure_code"] == CANDIDATE_COMPLEMENT_IMAGE,
    )
    if not all(negatives):
        return {"valid": False, "code": VERIFIER_REGRESSION_FAILURE, "stage": "negatives"}
    reflection = sorted((-x) % 12 for x in _N12_A)
    if not (triple_g_aligned(_N12_A, reflection, 12) is True and triple_g_aligned(_N12_A, _N12_B, 12) is False):
        return {"valid": False, "code": VERIFIER_REGRESSION_FAILURE, "stage": "triple_branches"}
    data, code = serialize_or_failure({"b": 2, "a": [3, 1, 2]})
    if code is not None or data != b'{"a":[3,1,2],"b":2}' \
            or cjson.sha256_hex(data) != cjson.payload_sha256({"b": 2, "a": [3, 1, 2]}):
        return {"valid": False, "code": VERIFIER_REGRESSION_FAILURE, "stage": "serialization_hash"}
    return {"valid": True, "code": None}

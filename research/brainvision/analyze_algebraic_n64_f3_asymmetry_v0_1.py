"""Standalone read-only F3 frozen-family asymmetry audit analyzer (v0.1).

This module performs a POST-RESULT, DESCRIPTIVE, READ-ONLY audit of the retained
canonical algebraic N=64 PRIMARY_V0_1 frozen-family F3 evaluation result. It does
not evaluate PsiTRS, does not recompute descriptors, does not rerun the F3
evaluator, and does not modify any retained evidence. It never amends, weakens, or
rescues the authoritative F3 verdict:

    STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY

Governing documents:
  docs/TORMENT_BRAINVISION_ALGEBRAIC_N64_PRIMARY_V0_1_F3_READ_ONLY_ASYMMETRY_AUDIT_SPECIFICATION_v0.1.md
  docs/TORMENT_BRAINVISION_ALGEBRAIC_N64_PRIMARY_V0_1_F3_READ_ONLY_ASYMMETRY_AUDIT_IMPLEMENTATION_AUTHORIZATION_v0.1.md

Standard-library only. Importing this module is inert: it performs no filesystem
read or write, no Git command, no calculation, no output, and no directory
creation. The real zero-argument audit is closed by default behind the gate
environment variable ALGEBRAIC_N64_F3_ASYMMETRY_AUDIT_AUTHORIZED=1 and a
repository-state / source-identity gate; all descriptor contact and F3 gates are
outside this module entirely.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import statistics
import stat as stat_module
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

# --------------------------------------------------------------------------- #
# Constants and embedded identities
# --------------------------------------------------------------------------- #

AUDIT_SCHEMA_NAME = "torment_brainvision_algebraic_n64_f3_asymmetry_audit"
AUDIT_SCHEMA_VERSION = "0.1"

FAILURE_NAMESPACE = "torment_brainvision_algebraic_n64_f3_asymmetry_audit_v0_1"
FAILURE_VERSION = "0.1"

GATE_ENV = "ALGEBRAIC_N64_F3_ASYMMETRY_AUDIT_AUTHORIZED"
GATE_VALUE_REQUIRED = "1"

# Bound source commit identities.
SOURCE_FINDINGS_COMMIT_IDENTITY = (
    "f0c5fdbc6f75e3749323de9e2b13c77b3710df82"
)
SOURCE_AUDIT_SPECIFICATION_COMMIT_IDENTITY = (
    "db82ec06faf398d52a002ba56f976e91045d12a4"
)
SOURCE_IMPLEMENTATION_AUTHORIZATION_COMMIT_IDENTITY = (
    "75ba05485ae3d1dafcbe64d8330920459d54fa7e"
)
INPUT_EXECUTION_COMMIT_IDENTITY = (
    "c4f489c439d4190611e8e0c5b3034ead3353c26d"
)

# Retained-input identity.
EXPECTED_INPUT_SIZE_BYTES = 10_784_993
EXPECTED_INPUT_WHOLE_FILE_SHA256 = (
    "51e7cd8087050428c2559262764044624fcb84e19576b5f682bae3ca5b59fd7b"
)

INPUT_RELATIVE_PATH = (
    "research/brainvision/results/algebraic_n64_primary_v0_1_f3_evaluation_v0_1/"
    "algebraic_n64_primary_v0_1_f3_evaluation_result.json"
)

ANALYZER_RELATIVE_PATH = (
    "research/brainvision/analyze_algebraic_n64_f3_asymmetry_v0_1.py"
)

FINAL_DIR_RELATIVE_PATH = (
    "research/brainvision/results/"
    "algebraic_n64_primary_v0_1_f3_asymmetry_audit_v0_1"
)
STAGING_DIR_RELATIVE_PATH = (
    "research/brainvision/results/"
    ".algebraic_n64_primary_v0_1_f3_asymmetry_audit_v0_1.staging"
)
RESULT_FILE_NAME = "algebraic_n64_primary_v0_1_f3_asymmetry_audit_result.json"
SUMMARY_FILE_NAME = "algebraic_n64_primary_v0_1_f3_asymmetry_audit_summary.txt"

# Required retained payload bindings.
REQUIRED_SCHEMA_NAME = "torment_brainvision_algebraic_n64_f3_family_evaluation"
REQUIRED_SCHEMA_VERSION = "0.1"
REQUIRED_FAMILY_VERDICT = "STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY"
REQUIRED_ACCEPTED_CANDIDATE_INDICES = [478, 479, 480]

# Exact expected validity key set (from the frozen F3 result payload). valid_run
# is derived strictly: this exact key set, every value strictly Boolean True,
# failure_record exactly None, and replay_record.byte_identical exactly True.
EXPECTED_VALIDITY_KEYS = frozenset({
    "all_response_values_finite",
    "canonical_serialization_valid",
    "cross_coverage_valid",
    "descriptor_identity_valid",
    "family_certificate_identity_valid",
    "family_manifest_identity_valid",
    "feature_coverage_valid",
    "feature_schema_valid",
    "freeze_result_identity_valid",
    "frozen_support_identity_valid",
    "gate_inputs_valid",
    "identity_self_pair_valid",
    "input_encoding_valid",
    "normalization_valid",
    "pair_certificate_identities_valid",
    "replay_byte_identical",
    "self_orbit_coverage_valid",
    "source_identity_valid",
    "witness_reverification_valid",
})

N = 64
VARIANTS = ("psi_trs", "psi_trs_k0")
FULL_VARIANT = "psi_trs"
K0_VARIANT = "psi_trs_k0"

WITHIN_FRACTION_LEVELS = (0.99, 0.95, 0.90)
TOP_K_CLASS_MEANS = (2, 5)
TOP_K_DISTANCE_CONTRIBUTION = (8, 16)
LARGEST_ALIGNED_START_LIMIT = 8

NARROW_MAX = 2
INTERMEDIATE_MIN = 3
INTERMEDIATE_MAX = 7
BROAD_MIN = 8

DISPOSITION_A = "A. BLOCKING SELF-ORBIT MAXIMUM IS NARROWLY CONCENTRATED"
DISPOSITION_B = "B. BLOCKING SELF-ORBIT ELEVATION IS BROAD"
DISPOSITION_C = "C. MIXED BLOCKING STRUCTURE ACROSS THE FROZEN FAMILY"
DISPOSITION_D = "D. RETAINED EVIDENCE IS INSUFFICIENT OR INTERNALLY INCONSISTENT"

# Exit codes.
EXIT_OK = 0
EXIT_PROCESS_FAILURE = 1
EXIT_REFUSAL = 2

# Failure codes.
AUDIT_NOT_AUTHORIZED = "AUDIT_NOT_AUTHORIZED"
UNEXPECTED_CLI_ARGUMENTS = "UNEXPECTED_CLI_ARGUMENTS"
REPOSITORY_STATE_INVALID = "REPOSITORY_STATE_INVALID"
SOURCE_IDENTITY_FAILURE = "SOURCE_IDENTITY_FAILURE"
INPUT_PATH_INVALID = "INPUT_PATH_INVALID"
INPUT_FILE_MISSING = "INPUT_FILE_MISSING"
INPUT_FILE_NOT_REGULAR = "INPUT_FILE_NOT_REGULAR"
INPUT_FILE_SYMLINK = "INPUT_FILE_SYMLINK"
INPUT_SIZE_MISMATCH = "INPUT_SIZE_MISMATCH"
INPUT_WHOLE_FILE_HASH_MISMATCH = "INPUT_WHOLE_FILE_HASH_MISMATCH"
INPUT_JSON_INVALID = "INPUT_JSON_INVALID"
INPUT_ENVELOPE_INVALID = "INPUT_ENVELOPE_INVALID"
INPUT_PAYLOAD_HASH_MISMATCH = "INPUT_PAYLOAD_HASH_MISMATCH"
INPUT_SCHEMA_MISMATCH = "INPUT_SCHEMA_MISMATCH"
INPUT_EXECUTION_IDENTITY_MISMATCH = "INPUT_EXECUTION_IDENTITY_MISMATCH"
INPUT_REPLAY_STATUS_INVALID = "INPUT_REPLAY_STATUS_INVALID"
INPUT_VALIDITY_INVALID = "INPUT_VALIDITY_INVALID"
INPUT_PAIR_ORDER_MISMATCH = "INPUT_PAIR_ORDER_MISMATCH"
INPUT_FAMILY_VERDICT_MISMATCH = "INPUT_FAMILY_VERDICT_MISMATCH"
INPUT_COVERAGE_INVALID = "INPUT_COVERAGE_INVALID"
INPUT_VALUE_NONFINITE = "INPUT_VALUE_NONFINITE"
INVERSE_SHIFT_VALIDATION_FAILURE = "INVERSE_SHIFT_VALIDATION_FAILURE"
RETAINED_AGGREGATE_INCONSISTENCY = "RETAINED_AGGREGATE_INCONSISTENCY"
AUDIT_CALCULATION_FAILURE = "AUDIT_CALCULATION_FAILURE"
CANONICAL_SERIALIZATION_FAILURE = "CANONICAL_SERIALIZATION_FAILURE"
OUTPUT_PATH_EXISTS = "OUTPUT_PATH_EXISTS"
PUBLICATION_FAILURE = "PUBLICATION_FAILURE"
STDOUT_FAILURE = "STDOUT_FAILURE"

NON_CLAIM_BOUNDARY = [
    "This audit is descriptive, read-only, non-gating, and non-rescue.",
    "It does not amend, weaken, or rescue the authoritative F3 verdict.",
    "It does not establish true vision, perception, temporal-order perception, "
    "recursive-time mechanism, higher-order consciousness, scientific "
    "significance, physics emergence, general PsiTRS failure, general "
    "impossibility of order sensitivity, or production readiness.",
    "Descriptive dispositions A/B/C/D are not F3 gates, scientific thresholds, "
    "or rescue criteria.",
]


# --------------------------------------------------------------------------- #
# Control-flow signalling
# --------------------------------------------------------------------------- #

class AuditRefusal(Exception):
    """Pre-audit refusal. Produces no derived output. Maps to exit 2."""

    def __init__(self, code: str, message: str = "") -> None:
        super().__init__("%s: %s" % (code, message) if message else code)
        self.code = code
        self.message = message


class AuditProcessFailure(Exception):
    """Post-preflight process failure. Maps to exit 1. Never disposition D."""

    def __init__(self, code: str, message: str = "") -> None:
        super().__init__("%s: %s" % (code, message) if message else code)
        self.code = code
        self.message = message


# --------------------------------------------------------------------------- #
# Pure numeric / serialization helpers
# --------------------------------------------------------------------------- #

def canonical_json_bytes(value: Any) -> bytes:
    """Deterministic canonical JSON bytes (no trailing newline)."""
    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def whole_file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _num(x: Any) -> float:
    """Coerce to a finite float, normalising negative zero to positive zero."""
    value = float(x)
    if not math.isfinite(value):
        raise AuditProcessFailure(INPUT_VALUE_NONFINITE, "nonfinite numeric value")
    if value == 0.0:
        return 0.0
    return value


def _is_finite_number(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _norm0(x: float) -> float:
    """Normalise negative zero to positive zero for an already-finite value."""
    value = float(x)
    return 0.0 if value == 0.0 else value


def _stats(values: Sequence[float]) -> Dict[str, Any]:
    vals = [float(v) for v in values]
    count = len(vals)
    result = {
        "count": count,
        "minimum": _num(min(vals)),
        "maximum": _num(max(vals)),
        "mean": _num(sum(vals) / count),
        "median": _num(statistics.median(vals)),
        "population_standard_deviation": _num(statistics.pstdev(vals)),
    }
    return result


def _is_sha40(text: str) -> bool:
    return len(text) == 40 and all(c in "0123456789abcdef" for c in text)


# --------------------------------------------------------------------------- #
# Read-only Git plumbing (injectable)
# --------------------------------------------------------------------------- #

def _real_git(root: str, args: Sequence[str], binary: bool = False) -> Tuple[bool, Any]:
    """Run read-only Git plumbing. Never used at import time."""
    proc = subprocess.run(
        ["git", "-C", str(root), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    ok = proc.returncode == 0
    out = proc.stdout if binary else proc.stdout.decode("utf-8", "replace")
    return ok, out


GitRunner = Callable[..., Tuple[bool, Any]]


def resolve_and_validate_repository_state(
    start_dir: str,
    git: GitRunner = _real_git,
) -> Dict[str, str]:
    """Resolve repo root and require branch=main, HEAD==origin/main, clean tree."""
    ok, top = git(start_dir, ["rev-parse", "--show-toplevel"])
    if not ok:
        raise AuditRefusal(REPOSITORY_STATE_INVALID, "not a Git repository")
    root = top.strip()
    ok, branch = git(root, ["symbolic-ref", "--short", "-q", "HEAD"])
    branch = branch.strip()
    if not ok or branch != "main":
        raise AuditRefusal(REPOSITORY_STATE_INVALID, "branch is not main")
    ok, head = git(root, ["rev-parse", "--verify", "HEAD^{commit}"])
    head = head.strip()
    if not ok or not _is_sha40(head):
        raise AuditRefusal(REPOSITORY_STATE_INVALID, "HEAD did not resolve")
    ok, origin = git(root, ["rev-parse", "--verify", "refs/remotes/origin/main^{commit}"])
    origin = origin.strip()
    if not ok or origin != head:
        raise AuditRefusal(REPOSITORY_STATE_INVALID, "HEAD != origin/main")
    ok, status = git(root, ["status", "--porcelain"])
    if not ok or status.strip() != "":
        raise AuditRefusal(REPOSITORY_STATE_INVALID, "working tree is not clean")
    return {
        "repository_root": root,
        "audit_execution_commit_identity": head,
        "branch": branch,
    }


def validate_analyzer_source_identity(
    root: str,
    local_path: Path,
    git: GitRunner = _real_git,
) -> Dict[str, str]:
    """Require the analyzer committed at HEAD with local bytes equal to the blob."""
    rel = ANALYZER_RELATIVE_PATH
    ok, blob = git(root, ["rev-parse", "--verify", "HEAD:" + rel])
    blob = blob.strip()
    if not ok or not _is_sha40(blob):
        raise AuditRefusal(SOURCE_IDENTITY_FAILURE, "analyzer not committed at HEAD")
    ok, committed = git(root, ["cat-file", "blob", "HEAD:" + rel], binary=True)
    if not ok:
        raise AuditRefusal(SOURCE_IDENTITY_FAILURE, "cannot read committed analyzer blob")
    if isinstance(committed, str):
        committed = committed.encode("utf-8")
    try:
        local_bytes = local_path.read_bytes()
    except OSError as exc:
        raise AuditRefusal(SOURCE_IDENTITY_FAILURE, "cannot read local analyzer: %s" % exc)
    if local_bytes != committed:
        raise AuditRefusal(SOURCE_IDENTITY_FAILURE, "local analyzer bytes != HEAD blob")
    return {
        "analyzer_git_blob_sha": blob,
        "analyzer_raw_file_sha256": sha256_bytes(local_bytes),
    }


# --------------------------------------------------------------------------- #
# Retained-input loading and identity/envelope/payload validation
# --------------------------------------------------------------------------- #

def load_and_validate_retained_input(
    input_path: Path,
    expected_size: int = EXPECTED_INPUT_SIZE_BYTES,
    expected_sha256: str = EXPECTED_INPUT_WHOLE_FILE_SHA256,
) -> Dict[str, Any]:
    """Read-only load + whole-file identity + envelope + payload validation."""
    if input_path is None or str(input_path) == "":
        raise AuditRefusal(INPUT_PATH_INVALID, "empty input path")
    try:
        lst = os.lstat(str(input_path))
    except FileNotFoundError:
        raise AuditRefusal(INPUT_FILE_MISSING, "retained input not found")
    except OSError as exc:
        raise AuditRefusal(INPUT_PATH_INVALID, "cannot stat input: %s" % exc)
    if stat_module.S_ISLNK(lst.st_mode):
        raise AuditRefusal(INPUT_FILE_SYMLINK, "retained input is a symlink")
    if not stat_module.S_ISREG(lst.st_mode):
        raise AuditRefusal(INPUT_FILE_NOT_REGULAR, "retained input is not a regular file")
    if lst.st_size != expected_size:
        raise AuditRefusal(INPUT_SIZE_MISMATCH, "size %d != %d" % (lst.st_size, expected_size))
    digest = whole_file_sha256(Path(input_path))
    if digest != expected_sha256:
        raise AuditRefusal(INPUT_WHOLE_FILE_HASH_MISMATCH, "whole-file hash mismatch")
    raw = Path(input_path).read_bytes()
    try:
        text = raw.decode("utf-8")
        envelope = json.loads(text)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AuditRefusal(INPUT_JSON_INVALID, "invalid JSON: %s" % exc)
    payload = validate_retained_envelope(envelope)
    validate_retained_payload(payload)
    return {
        "envelope": envelope,
        "payload": payload,
        "input_size_bytes": lst.st_size,
        "input_whole_file_sha256": digest,
        "input_payload_sha256": envelope["family_evaluation_result_sha256"],
    }


def validate_retained_envelope(envelope: Any) -> Dict[str, Any]:
    if not isinstance(envelope, dict):
        raise AuditRefusal(INPUT_ENVELOPE_INVALID, "envelope is not an object")
    if set(envelope.keys()) != {"family_evaluation_result", "family_evaluation_result_sha256"}:
        raise AuditRefusal(INPUT_ENVELOPE_INVALID, "unexpected top-level key set")
    payload = envelope["family_evaluation_result"]
    stored = envelope["family_evaluation_result_sha256"]
    if not isinstance(payload, dict):
        raise AuditRefusal(INPUT_ENVELOPE_INVALID, "payload is not an object")
    if not isinstance(stored, str):
        raise AuditRefusal(INPUT_ENVELOPE_INVALID, "payload hash is not a string")
    try:
        recomputed = sha256_bytes(canonical_json_bytes(payload))
    except (ValueError, TypeError) as exc:
        raise AuditRefusal(INPUT_ENVELOPE_INVALID, "payload not canonically serialisable: %s" % exc)
    if recomputed != stored:
        raise AuditRefusal(INPUT_PAYLOAD_HASH_MISMATCH, "payload hash mismatch")
    return payload


def _derive_valid_run(payload: Dict[str, Any]) -> bool:
    """valid_run is derived with strict, exact semantics (no generic truthiness):

    - failure_record is exactly None,
    - the validity object's key set exactly equals EXPECTED_VALIDITY_KEYS,
    - every validity value is strictly Boolean True,
    - replay_record.byte_identical is strictly Boolean True.
    """
    if payload.get("failure_record") is not None:
        return False
    validity = payload.get("validity")
    if not isinstance(validity, dict):
        return False
    if frozenset(validity.keys()) != EXPECTED_VALIDITY_KEYS:
        return False
    for value in validity.values():
        if value is not True:
            return False
    replay = payload.get("replay_record")
    if not isinstance(replay, dict) or replay.get("byte_identical") is not True:
        return False
    return True


def validate_retained_payload(payload: Dict[str, Any]) -> None:
    if payload.get("schema_name") != REQUIRED_SCHEMA_NAME or \
            payload.get("schema_version") != REQUIRED_SCHEMA_VERSION:
        raise AuditRefusal(INPUT_SCHEMA_MISMATCH, "schema name/version mismatch")
    if payload.get("execution_commit_identity") != INPUT_EXECUTION_COMMIT_IDENTITY:
        raise AuditRefusal(INPUT_EXECUTION_IDENTITY_MISMATCH, "execution commit mismatch")
    replay = payload.get("replay_record")
    if not isinstance(replay, dict) or replay.get("byte_identical") is not True:
        raise AuditRefusal(INPUT_REPLAY_STATUS_INVALID, "replay not byte-identical")
    if not _derive_valid_run(payload):
        raise AuditRefusal(INPUT_VALIDITY_INVALID, "run not valid")
    frozen = payload.get("frozen_evidence_identity")
    accepted = frozen.get("accepted_candidate_indices") if isinstance(frozen, dict) else None
    ep = payload.get("evaluation_pass")
    pairs = ep.get("pairs") if isinstance(ep, dict) else None
    if accepted != REQUIRED_ACCEPTED_CANDIDATE_INDICES:
        raise AuditRefusal(INPUT_PAIR_ORDER_MISMATCH, "accepted candidate indices mismatch")
    if not isinstance(pairs, list) or len(pairs) != 3:
        raise AuditRefusal(INPUT_PAIR_ORDER_MISMATCH, "pairs structure invalid")
    for idx, pair in enumerate(pairs):
        if pair.get("pair_order_index") != idx or \
                pair.get("candidate_generation_index") != REQUIRED_ACCEPTED_CANDIDATE_INDICES[idx]:
            raise AuditRefusal(INPUT_PAIR_ORDER_MISMATCH, "pair order mismatch at index %d" % idx)
    if payload.get("family_verdict") != REQUIRED_FAMILY_VERDICT:
        raise AuditRefusal(INPUT_FAMILY_VERDICT_MISMATCH, "family verdict mismatch")


# --------------------------------------------------------------------------- #
# Coverage and inverse-shift content validation (produces disposition D)
# --------------------------------------------------------------------------- #

def _per_start_distances(shift_obj: Any) -> Optional[List[float]]:
    if not isinstance(shift_obj, dict):
        return None
    per_start = shift_obj.get("per_start")
    if not isinstance(per_start, list) or len(per_start) != N:
        return None
    distances: List[float] = []
    for entry in per_start:
        if not isinstance(entry, dict):
            return None
        dist = entry.get("distance")
        if not _is_finite_number(dist):
            return None
        distances.append(float(dist))
    return distances


def _index_member_shifts(
    member: Any, variant: str,
) -> Tuple[bool, Dict[int, List[float]], Dict[int, float], str]:
    """Return (ok, per-start distances by r, retained aggregate mean by r, reason).

    Per-start distances are authoritative for multiset validation and per-start
    summaries. The retained aggregate ``mean`` field is authoritative for every
    class-level calculation; it is never recomputed from the per-start values.
    """
    if not isinstance(member, dict):
        return False, {}, {}, "member not an object"
    sob = member.get("self_orbits_by_variant")
    if not isinstance(sob, dict) or variant not in sob:
        return False, {}, {}, "missing self_orbits_by_variant[%s]" % variant
    shifts = sob[variant].get("nonidentity_shifts") if isinstance(sob[variant], dict) else None
    if not isinstance(shifts, list) or len(shifts) != 63:
        return False, {}, {}, "nonidentity_shifts not length 63"
    by_r_dist: Dict[int, List[float]] = {}
    by_r_mean: Dict[int, float] = {}
    for shift_obj in shifts:
        r = shift_obj.get("relative_shift") if isinstance(shift_obj, dict) else None
        if not isinstance(r, int) or isinstance(r, bool) or not (1 <= r <= 63):
            return False, {}, {}, "invalid relative_shift"
        dists = _per_start_distances(shift_obj)
        if dists is None:
            return False, {}, {}, "invalid per_start distances at shift %r" % r
        retained_mean = shift_obj.get("mean")
        if not _is_finite_number(retained_mean):
            return False, {}, {}, "invalid retained mean at shift %r" % r
        by_r_dist[r] = dists
        by_r_mean[r] = float(retained_mean)
    if set(by_r_dist.keys()) != set(range(1, 64)):
        return False, {}, {}, "relative shifts not exactly 1..63"
    return True, by_r_dist, by_r_mean, ""


def validate_member_and_pair_coverage(payload: Dict[str, Any]) -> Tuple[bool, List[str]]:
    failures: List[str] = []
    ep = payload.get("evaluation_pass")
    members = ep.get("members") if isinstance(ep, dict) else None
    pairs = ep.get("pairs") if isinstance(ep, dict) else None
    if not isinstance(members, list) or len(members) != 6:
        failures.append(INPUT_COVERAGE_INVALID + ":members")
    if not isinstance(pairs, list) or len(pairs) != 3:
        failures.append(INPUT_COVERAGE_INVALID + ":pairs")
    if failures:
        return False, failures
    member_ids = [m.get("member_id") for m in members]
    if len(set(member_ids)) != 6 or any(not isinstance(x, str) for x in member_ids):
        failures.append(INPUT_COVERAGE_INVALID + ":member_ids")
    for pair in pairs:
        for role_key in ("member_A_id", "member_B_id"):
            if pair.get(role_key) not in member_ids:
                failures.append(INPUT_COVERAGE_INVALID + ":" + role_key)
        cbv = pair.get("cross_by_variant")
        if not isinstance(cbv, dict):
            failures.append(INPUT_COVERAGE_INVALID + ":cross_by_variant")
            continue
        for variant in VARIANTS:
            if variant not in cbv or _cross_distances(cbv[variant]) is None:
                failures.append(INPUT_COVERAGE_INVALID + ":cross:" + variant)
    return (len(failures) == 0), failures


def _cross_distances(cross_variant_obj: Any) -> Optional[List[float]]:
    if not isinstance(cross_variant_obj, dict):
        return None
    per_start = cross_variant_obj.get("per_start")
    if not isinstance(per_start, list) or len(per_start) != N:
        return None
    out: List[float] = []
    for entry in per_start:
        if not isinstance(entry, dict):
            return None
        dist = entry.get("distance")
        if not _is_finite_number(dist):
            return None
        out.append(float(dist))
    return out


_INVERSE_AGGREGATE_FIELDS = (
    "mean", "median", "minimum", "maximum", "population_standard_deviation",
)


def validate_inverse_shift_classes(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Governing check: sorted per-start distance multisets of q and 64-q agree.

    Additionally emits deterministic inverse-shift aggregate diagnostics. A
    distance-multiset mismatch is governing (disposition D). An aggregate-field
    mismatch on a valid distance multiset is diagnostic only: it never triggers
    disposition D, never alters class means, and never averages inverse shifts.
    """
    ep = payload["evaluation_pass"]
    members = ep["members"]
    failures: List[str] = []
    checked = 0
    diagnostics: Dict[str, Any] = {}
    for member in members:
        member_id = member.get("member_id")
        member_diag: Dict[str, Any] = {}
        for variant in VARIANTS:
            ok, by_r, _by_r_mean, why = _index_member_shifts(member, variant)
            if not ok:
                failures.append("%s:%s:%s" % (member_id, variant, why))
                continue
            sob = member["self_orbits_by_variant"][variant]["nonidentity_shifts"]
            by_r_obj = {s["relative_shift"]: s for s in sob}
            variant_diag: Dict[str, Any] = {}
            for q in range(1, 32):
                a = sorted(by_r[q])
                b = sorted(by_r[64 - q])
                checked += 1
                multiset_equal = (a == b)
                if not multiset_equal:
                    failures.append("%s:%s:q=%d multiset mismatch" % (member_id, variant, q))
                comparisons: Dict[str, Any] = {}
                mismatch_fields: List[str] = []
                for field in _INVERSE_AGGREGATE_FIELDS:
                    qv = by_r_obj[q].get(field)
                    iv = by_r_obj[64 - q].get(field)
                    if _is_finite_number(qv) and _is_finite_number(iv):
                        exactly_equal = float(qv) == float(iv)
                        comparisons[field] = {
                            "raw_shift_q_value": _norm0(float(qv)),
                            "raw_shift_inverse_value": _norm0(float(iv)),
                            "exactly_equal": exactly_equal,
                            "difference": _norm0(float(qv) - float(iv)),
                        }
                    else:
                        exactly_equal = False
                        comparisons[field] = {
                            "raw_shift_q_value": None,
                            "raw_shift_inverse_value": None,
                            "exactly_equal": False,
                            "difference": None,
                        }
                    if not exactly_equal:
                        mismatch_fields.append(field)
                variant_diag[str(q)] = {
                    "raw_shift_q": q,
                    "raw_shift_inverse": 64 - q,
                    "self_inverse": False,
                    "distance_multiset_equal": multiset_equal,
                    "aggregate_comparisons": comparisons,
                    "aggregate_mismatch_fields": mismatch_fields,
                }
            # q == 32 is self-inverse.
            variant_diag["32"] = {
                "raw_shift_q": 32,
                "raw_shift_inverse": 32,
                "self_inverse": True,
                "distance_multiset_equal": True,
                "aggregate_comparisons": {},
                "aggregate_mismatch_fields": [],
            }
            member_diag[variant] = variant_diag
        if member_diag:
            diagnostics[member_id] = member_diag
    return {
        "valid": len(failures) == 0,
        "classes_compared": checked,
        "failures": failures,
        "inverse_shift_diagnostics": diagnostics,
    }


def _retained_self_max(member: Any, variant: str) -> Any:
    sob = member.get("self_orbits_by_variant") if isinstance(member, dict) else None
    node = sob.get(variant) if isinstance(sob, dict) else None
    return node.get("maximum_nonidentity_mean") if isinstance(node, dict) else None


def _retained_cross_mean(pair: Any, variant: str) -> Any:
    cbv = pair.get("cross_by_variant") if isinstance(pair, dict) else None
    node = cbv.get(variant) if isinstance(cbv, dict) else None
    return node.get("mean") if isinstance(node, dict) else None


def validate_retained_aggregates(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Validate retained aggregate means exist, are finite, and are internally
    consistent with the retained pair gate and margin objects (exact equality).

    This binds the audit to the authoritative retained aggregates rather than to
    any recomputation from per-start distances. Any inconsistency is an internal
    retained-evidence inconsistency and yields disposition D.
    """
    ep = payload["evaluation_pass"]
    members = {m["member_id"]: m for m in ep["members"]}
    failures: List[str] = []
    consistency: List[Dict[str, Any]] = []
    self_orbit_diag: List[Dict[str, Any]] = []

    # Blocker 1: the retained self-orbit maximum must equal the maximum over ALL
    # 63 retained raw-shift means (not the 32 canonical classes).
    for member in ep["members"]:
        member_id = member.get("member_id")
        for variant in VARIANTS:
            ok, _dist, by_r_mean, why = _index_member_shifts(member, variant)
            if not ok:
                failures.append("self_max_index:%s:%s:%s" % (member_id, variant, why))
                continue
            all_raw_shift_maximum = max(by_r_mean[r] for r in range(1, 64))
            retained_self_max = _retained_self_max(member, variant)
            class_means = {q: by_r_mean[q] for q in range(1, 33)}
            class_mean_maximum = max(class_means.values())
            raw_shifts_at_maximum = sorted(r for r in range(1, 64) if by_r_mean[r] == all_raw_shift_maximum)
            canonical_q_at_class_maximum = sorted(q for q in range(1, 33) if class_means[q] == class_mean_maximum)
            self_max_finite = _is_finite_number(retained_self_max)
            consistent = self_max_finite and float(retained_self_max) == all_raw_shift_maximum
            if not consistent:
                failures.append("self_max:%s:%s" % (member_id, variant))
            self_orbit_diag.append({
                "member_id": member_id,
                "variant": variant,
                "retained_self_orbit_maximum": (_norm0(float(retained_self_max)) if self_max_finite else None),
                "all_raw_shift_maximum": _norm0(all_raw_shift_maximum),
                "raw_shifts_at_maximum": raw_shifts_at_maximum,
                "class_mean_maximum": _norm0(class_mean_maximum),
                "canonical_q_at_class_maximum": canonical_q_at_class_maximum,
                "consistent": bool(consistent),
            })

    for pair in ep["pairs"]:
        for variant in VARIANTS:
            if not _is_finite_number(_retained_cross_mean(pair, variant)):
                failures.append("cross_mean:%s:%s" % (pair.get("candidate_generation_index"), variant))
        gates = pair.get("gates")
        margins = pair.get("margins")
        member_a = members.get(pair.get("member_A_id"))
        member_b = members.get(pair.get("member_B_id"))
        pair_ok = True
        if not isinstance(gates, dict) or not isinstance(margins, dict) \
                or member_a is None or member_b is None:
            pair_ok = False
        else:
            fields = {
                "full_cross_mean": _retained_cross_mean(pair, "psi_trs"),
                "k0_cross_mean": _retained_cross_mean(pair, "psi_trs_k0"),
                "full_self_A_max": _retained_self_max(member_a, "psi_trs"),
                "full_self_B_max": _retained_self_max(member_b, "psi_trs"),
                "k0_self_A_max": _retained_self_max(member_a, "psi_trs_k0"),
                "k0_self_B_max": _retained_self_max(member_b, "psi_trs_k0"),
            }
            if any(not _is_finite_number(v) for v in fields.values()):
                pair_ok = False
            elif any(fields[key] != gates.get(key) for key in fields):
                pair_ok = False
            else:
                expected_margins = {
                    "full_margin_vs_A": fields["full_cross_mean"] - fields["full_self_A_max"],
                    "full_margin_vs_B": fields["full_cross_mean"] - fields["full_self_B_max"],
                    "k0_margin_vs_A": fields["k0_cross_mean"] - fields["k0_self_A_max"],
                    "k0_margin_vs_B": fields["k0_cross_mean"] - fields["k0_self_B_max"],
                }
                if any(margins.get(key) != expected_margins[key] for key in expected_margins):
                    pair_ok = False
                elif not _validate_boolean_and_recursive_gates(pair, gates, margins, fields):
                    pair_ok = False
        consistency.append({
            "candidate_generation_index": pair.get("candidate_generation_index"),
            "pair_order_index": pair.get("pair_order_index"),
            "retained_gate_consistent": bool(pair_ok),
        })
        if not pair_ok:
            failures.append("gate_consistency:%s" % pair.get("candidate_generation_index"))

    return {
        "valid": len(failures) == 0,
        "failures": failures,
        "pair_gate_consistency": consistency,
        "self_orbit_maximum_diagnostics": self_orbit_diag,
    }


def _validate_boolean_and_recursive_gates(
    pair: Dict[str, Any],
    gates: Dict[str, Any],
    margins: Dict[str, Any],
    fields: Dict[str, Any],
) -> bool:
    """Blocker 2: derive and require exact retained Boolean gates and the
    recursive minimum from retained numeric gates and retained cross per-start
    distances. Retained Boolean gates must be strict ``bool``.
    """
    expected_full_dual = (fields["full_cross_mean"] > fields["full_self_A_max"]
                          and fields["full_cross_mean"] > fields["full_self_B_max"])
    expected_k0_not = (fields["k0_cross_mean"] <= fields["k0_self_A_max"]
                       and fields["k0_cross_mean"] <= fields["k0_self_B_max"])
    gate_dual = gates.get("full_dual_orbit_extreme")
    gate_k0 = gates.get("k0_not_extreme_against_either_member")
    if not (isinstance(gate_dual, bool) and gate_dual == expected_full_dual):
        return False
    if not (isinstance(gate_k0, bool) and gate_k0 == expected_k0_not):
        return False

    cbv = pair.get("cross_by_variant")
    full_d = _cross_distances(cbv.get(FULL_VARIANT)) if isinstance(cbv, dict) else None
    k0_d = _cross_distances(cbv.get(K0_VARIANT)) if isinstance(cbv, dict) else None
    if full_d is None or k0_d is None:
        return False
    diffs = [full_d[s] - k0_d[s] for s in range(N)]
    expected_recursive_positive = all(d > 0.0 for d in diffs)
    expected_min = min(diffs)
    gate_recursive = gates.get("recursive_positive_all_starts")
    margin_min = margins.get("minimum_recursive_difference")
    if not (isinstance(gate_recursive, bool) and gate_recursive == expected_recursive_positive):
        return False
    if not (_is_finite_number(margin_min) and float(margin_min) == expected_min):
        return False
    return True


# --------------------------------------------------------------------------- #
# Class-collapsed representations (validated inputs only)
# --------------------------------------------------------------------------- #

def collapse_validated_inverse_shift_classes(by_r_mean: Dict[int, float]) -> Dict[int, float]:
    """Canonical class means keyed by q=1..32.

    The class mean is the retained aggregate ``mean`` of the canonical raw shift q.
    Inverse shifts are never averaged, and per-start values are never substituted
    for the retained aggregate mean.
    """
    return {q: by_r_mean[q] for q in range(1, 33)}


def _member_class_means(member: Any, variant: str) -> Dict[int, float]:
    ok, _by_r_dist, by_r_mean, why = _index_member_shifts(member, variant)
    if not ok:
        raise AuditProcessFailure(AUDIT_CALCULATION_FAILURE, why)
    return collapse_validated_inverse_shift_classes(by_r_mean)


def _sorted_desc_by_mean(class_means: Dict[int, float]) -> List[Tuple[int, float]]:
    return sorted(class_means.items(), key=lambda kv: (-kv[1], kv[0]))


# --------------------------------------------------------------------------- #
# Audit Question 1 — shift-class distribution
# --------------------------------------------------------------------------- #

def summarize_shift_class_distribution(class_means: Dict[int, float]) -> Dict[str, Any]:
    means = [class_means[q] for q in range(1, 33)]
    maximum = max(means)
    minimum = min(means)
    ordered = _sorted_desc_by_mean(class_means)
    argmax_q = sorted(q for q in range(1, 33) if class_means[q] == maximum)
    second = ordered[1][1] if len(ordered) > 1 else maximum
    median = statistics.median(means)
    out: Dict[str, Any] = {
        "maximum": _num(maximum),
        "argmax_q": argmax_q,
        "minimum": _num(minimum),
        "median": _num(median),
        "mean": _num(sum(means) / len(means)),
        "population_standard_deviation": _num(statistics.pstdev(means)),
        "top_2": [{"q": q, "mean": _num(m)} for q, m in ordered[:2]],
        "top_5": [{"q": q, "mean": _num(m)} for q, m in ordered[:5]],
        "maximum_minus_second": _num(maximum - second),
        "maximum_minus_median": _num(maximum - median),
        "maximum_to_median_ratio": (_num(maximum / median) if median != 0.0 else None),
    }
    for frac in WITHIN_FRACTION_LEVELS:
        threshold = frac * maximum
        count = sum(1 for m in means if m >= threshold)
        key = "within_%d_percent" % int(round(frac * 100))
        out[key] = {"count": count, "fraction": _num(count / 32.0)}
    return out


# --------------------------------------------------------------------------- #
# Audit Question 2 — blocking classes
# --------------------------------------------------------------------------- #

def summarize_blocking_classes(
    class_means: Dict[int, float],
    cross_mean: float,
    self_orbit_maximum: Optional[float] = None,
) -> Dict[str, Any]:
    """Blocking-class summary.

    ``cross_mean`` and ``self_orbit_maximum`` are the retained aggregate cross
    mean and the retained ``maximum_nonidentity_mean``. Rank, argmax, and the
    above-cross set derive from the retained class means. When
    ``self_orbit_maximum`` is not supplied the class-mean maximum is used (only
    for isolated pure-function tests).
    """
    means = [class_means[q] for q in range(1, 33)]
    class_max = max(means)
    if self_orbit_maximum is None:
        self_orbit_maximum = class_max
    argmax_q = sorted(q for q in range(1, 33) if class_means[q] == class_max)
    above = sorted(q for q in range(1, 33) if class_means[q] > cross_mean)
    count_above = len(above)
    rank = 1 + count_above  # cross insertion rank; equality is not "greater"
    return {
        "cross_mean": _num(cross_mean),
        "self_orbit_maximum": _num(self_orbit_maximum),
        "class_mean_maximum": _num(class_max),
        "margin_cross_minus_self": _num(cross_mean - self_orbit_maximum),
        "argmax_q": argmax_q,
        "classes_above_cross_mean": above,
        "count_above_cross_mean": count_above,
        "fraction_above_cross_mean": _num(count_above / 32.0),
        "cross_insertion_rank": rank,
    }


# --------------------------------------------------------------------------- #
# Audit Question 3 — A/B shiftwise asymmetry
# --------------------------------------------------------------------------- #

def summarize_ab_shiftwise_asymmetry(
    class_means_a: Dict[int, float],
    class_means_b: Dict[int, float],
) -> Dict[str, Any]:
    diffs = {q: class_means_a[q] - class_means_b[q] for q in range(1, 33)}
    values = [diffs[q] for q in range(1, 33)]
    a_gt = sum(1 for v in values if v > 0.0)
    a_eq = sum(1 for v in values if v == 0.0)
    a_lt = sum(1 for v in values if v < 0.0)
    largest_a = sorted(diffs.items(), key=lambda kv: (-kv[1], kv[0]))[:5]
    largest_b = sorted(diffs.items(), key=lambda kv: (kv[1], kv[0]))[:5]
    a_max = max(class_means_a[q] for q in range(1, 33))
    b_max = max(class_means_b[q] for q in range(1, 33))
    return {
        "a_minus_b_by_q": [{"q": q, "difference": _num(diffs[q])} for q in range(1, 33)],
        "count_a_greater": a_gt,
        "count_a_equal": a_eq,
        "count_a_less": a_lt,
        "mean_difference": _num(sum(values) / len(values)),
        "median_difference": _num(statistics.median(values)),
        "minimum_difference": _num(min(values)),
        "maximum_difference": _num(max(values)),
        "five_largest_a_minus_b": [{"q": q, "difference": _num(d)} for q, d in largest_a],
        "five_largest_b_minus_a": [{"q": q, "difference": _num(-d)} for q, d in largest_b],
        "a_maximum_minus_b_maximum": _num(a_max - b_max),
    }


# --------------------------------------------------------------------------- #
# Audit Question 4 — per-start concentration at blocking shifts
# --------------------------------------------------------------------------- #

def _contribution_share(distances: Sequence[float], k: int) -> Optional[float]:
    total = sum(distances)
    if total == 0.0:
        return None
    ordered = sorted(distances, key=lambda d: -d)
    return _num(sum(ordered[:k]) / total)


def _summarize_start_distances(distances: List[float]) -> Dict[str, Any]:
    base = _stats(distances)
    total = sum(distances)
    mean = base["mean"]
    median = base["median"]
    indexed = list(enumerate(distances))
    maximum = base["maximum"]
    minimum = base["minimum"]
    argmax_starts = [s for s, d in indexed if d == maximum]
    argmin_starts = [s for s, d in indexed if d == minimum]
    out = dict(base)
    out["mean_minus_median"] = _num(mean - median)
    out["maximum_to_mean_ratio"] = (_num(maximum / mean) if mean != 0.0 else None)
    out["top_8_contribution_share"] = _contribution_share(distances, 8)
    out["top_16_contribution_share"] = _contribution_share(distances, 16)
    out["zero_total"] = (total == 0.0)
    out["argmax_starts"] = sorted(argmax_starts)
    out["argmin_starts"] = sorted(argmin_starts)
    return out


def summarize_blocking_per_start(
    member_a: Any,
    class_means_a_full: Dict[int, float],
    cross_full_distances: List[float],
) -> Dict[str, Any]:
    self_max = max(class_means_a_full[q] for q in range(1, 33))
    blocking_q = min(q for q in range(1, 33) if class_means_a_full[q] == self_max)
    raw_shifts = [blocking_q] if blocking_q == 32 else [blocking_q, 64 - blocking_q]
    ok, by_r, _by_r_mean, why = _index_member_shifts(member_a, FULL_VARIANT)
    if not ok:
        raise AuditProcessFailure(AUDIT_CALCULATION_FAILURE, why)
    per_raw_shift = []
    for r in raw_shifts:
        self_distances = by_r[r]
        aligned = [self_distances[s] - cross_full_distances[s] for s in range(N)]
        pos = [(s, aligned[s]) for s in range(N) if aligned[s] > 0.0]
        neg = [(s, aligned[s]) for s in range(N) if aligned[s] < 0.0]
        largest_pos = sorted(pos, key=lambda sd: (-sd[1], sd[0]))[:LARGEST_ALIGNED_START_LIMIT]
        largest_neg = sorted(neg, key=lambda sd: (sd[1], sd[0]))[:LARGEST_ALIGNED_START_LIMIT]
        per_raw_shift.append({
            "raw_shift": r,
            "self_distance_summary": _summarize_start_distances(self_distances),
            "aligned_self_minus_cross": {
                "positive_count": sum(1 for v in aligned if v > 0.0),
                "zero_count": sum(1 for v in aligned if v == 0.0),
                "negative_count": sum(1 for v in aligned if v < 0.0),
                "mean": _num(sum(aligned) / len(aligned)),
                "median": _num(statistics.median(aligned)),
                "minimum": _num(min(aligned)),
                "maximum": _num(max(aligned)),
                "population_standard_deviation": _num(statistics.pstdev(aligned)),
                "largest_positive_starts": [{"start": s, "difference": _num(v)} for s, v in largest_pos],
                "largest_negative_starts": [{"start": s, "difference": _num(v)} for s, v in largest_neg],
            },
        })
    return {
        "blocking_class_q": blocking_q,
        "raw_shifts": raw_shifts,
        "per_raw_shift": per_raw_shift,
    }


# --------------------------------------------------------------------------- #
# Audit Question 6 — recursive companion
# --------------------------------------------------------------------------- #

def summarize_recursive_companion(
    cross_full_distances: List[float],
    cross_k0_distances: List[float],
) -> Dict[str, Any]:
    diffs = [cross_full_distances[s] - cross_k0_distances[s] for s in range(N)]
    minimum = min(diffs)
    maximum = max(diffs)
    argmin_starts = sorted(s for s in range(N) if diffs[s] == minimum)
    argmax_starts = sorted(s for s in range(N) if diffs[s] == maximum)
    return {
        "minimum": _num(minimum),
        "maximum": _num(maximum),
        "mean": _num(sum(diffs) / len(diffs)),
        "median": _num(statistics.median(diffs)),
        "population_standard_deviation": _num(statistics.pstdev(diffs)),
        "argmin_starts": argmin_starts,
        "argmax_starts": argmax_starts,
        "positive_count": sum(1 for v in diffs if v > 0.0),
        "zero_count": sum(1 for v in diffs if v == 0.0),
        "negative_count": sum(1 for v in diffs if v < 0.0),
    }


# --------------------------------------------------------------------------- #
# Classification
# --------------------------------------------------------------------------- #

def select_pair_classification(blocking_class_count: int) -> str:
    if blocking_class_count <= NARROW_MAX:
        return "narrow"
    if INTERMEDIATE_MIN <= blocking_class_count <= INTERMEDIATE_MAX:
        return "intermediate"
    return "broad"


def select_family_disposition(classifications: Sequence[str]) -> str:
    if all(c == "narrow" for c in classifications):
        return DISPOSITION_A
    if all(c == "broad" for c in classifications):
        return DISPOSITION_B
    return DISPOSITION_C


# --------------------------------------------------------------------------- #
# Pure audit driver
# --------------------------------------------------------------------------- #

def _member_map(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {m["member_id"]: m for m in payload["evaluation_pass"]["members"]}


def _member_order(payload: Dict[str, Any]) -> List[str]:
    return [m["member_id"] for m in payload["evaluation_pass"]["members"]]


def run_pure_audit(payload: Dict[str, Any], identities: Dict[str, Any]) -> Dict[str, Any]:
    """Pure audit over an already-identity-validated payload.

    Content-validation failures yield a complete disposition-D result. This
    function never contacts the filesystem, Git, or PsiTRS.
    """
    input_validation = {
        "envelope_valid": True,
        "payload_identity_valid": True,
        "execution_identity_valid": True,
        "replay_valid": True,
        "validity_valid": True,
        "pair_order_valid": True,
        "family_verdict_valid": True,
    }
    coverage_ok, coverage_failures = validate_member_and_pair_coverage(payload)
    inverse = validate_inverse_shift_classes(payload) if coverage_ok else {
        "valid": False, "classes_compared": 0, "failures": ["coverage precondition failed"]}
    aggregates = validate_retained_aggregates(payload) if coverage_ok else {
        "valid": False, "failures": ["coverage precondition failed"], "pair_gate_consistency": []}

    base = _base_result(payload, identities, input_validation, inverse)
    base["retained_aggregate_validation"] = aggregates

    if not coverage_ok or not inverse["valid"] or not aggregates["valid"]:
        codes = []
        if not coverage_ok:
            codes.append(INPUT_COVERAGE_INVALID)
        if not inverse["valid"]:
            codes.append(INVERSE_SHIFT_VALIDATION_FAILURE)
        if not aggregates["valid"]:
            codes.append(RETAINED_AGGREGATE_INCONSISTENCY)
        base.update({
            "audit_valid": False,
            "ordered_failure_codes": codes,
            "coverage_failures": coverage_failures,
            "member_audit_tables": None,
            "pair_audit_tables": None,
            "recursive_companion_tables": None,
            "pair_classifications": None,
            "family_disposition": DISPOSITION_D,
        })
        return base

    members = _member_map(payload)
    pairs = payload["evaluation_pass"]["pairs"]

    member_tables = []
    for member in payload["evaluation_pass"]["members"]:
        variants_block = {}
        for variant in VARIANTS:
            cm = _member_class_means(member, variant)
            variants_block[variant] = summarize_shift_class_distribution(cm)
        member_tables.append({
            "member_id": member["member_id"],
            "pair_order_index": member.get("pair_order_index"),
            "raw_role": member.get("raw_role"),
            "shift_class_distribution": variants_block,
        })

    pair_tables = []
    recursive_tables = []
    classifications = []
    for pair in pairs:
        member_a = members[pair["member_A_id"]]
        member_b = members[pair["member_B_id"]]
        cbv = pair["cross_by_variant"]
        blocking = {}
        asymmetry = {}
        class_means_a = {}
        cross_mean_diagnostic = {}
        for variant in VARIANTS:
            cross_mean = float(_retained_cross_mean(pair, variant))  # retained authoritative
            cm_a = _member_class_means(member_a, variant)
            cm_b = _member_class_means(member_b, variant)
            class_means_a[variant] = cm_a
            self_max_a = float(_retained_self_max(member_a, variant))
            self_max_b = float(_retained_self_max(member_b, variant))
            blocking[variant] = {
                "member_A": summarize_blocking_classes(cm_a, cross_mean, self_max_a),
                "member_B": summarize_blocking_classes(cm_b, cross_mean, self_max_b),
            }
            asymmetry[variant] = summarize_ab_shiftwise_asymmetry(cm_a, cm_b)
            recomputed = sum(_cross_distances(cbv[variant])) / float(N)
            cross_mean_diagnostic[variant] = {
                "retained_cross_mean": _num(cross_mean),
                "recomputed_cross_mean_from_per_start": _num(recomputed),
                "equal": cross_mean == recomputed,
            }
        cross_full = _cross_distances(cbv[FULL_VARIANT])
        cross_k0 = _cross_distances(cbv[K0_VARIANT])
        per_start = summarize_blocking_per_start(member_a, class_means_a[FULL_VARIANT], cross_full)
        pair_tables.append({
            "candidate_generation_index": pair.get("candidate_generation_index"),
            "pair_order_index": pair.get("pair_order_index"),
            "member_A_id": pair["member_A_id"],
            "member_B_id": pair["member_B_id"],
            "blocking_classes": blocking,
            "ab_shiftwise_asymmetry": asymmetry,
            "blocking_per_start_full": per_start,
            "diagnostic_per_start_recomputation": cross_mean_diagnostic,
        })
        recursive_tables.append({
            "candidate_generation_index": pair.get("candidate_generation_index"),
            "pair_order_index": pair.get("pair_order_index"),
            "recursive_companion": summarize_recursive_companion(cross_full, cross_k0),
        })
        full_cross_mean = float(_retained_cross_mean(pair, FULL_VARIANT))  # retained authoritative
        blocking_class_count = sum(
            1 for q in range(1, 33) if class_means_a[FULL_VARIANT][q] > full_cross_mean
        )
        classification = select_pair_classification(blocking_class_count)
        classifications.append({
            "candidate_generation_index": pair.get("candidate_generation_index"),
            "pair_order_index": pair.get("pair_order_index"),
            "blocking_class_count": blocking_class_count,
            "classification": classification,
        })

    disposition = select_family_disposition([c["classification"] for c in classifications])
    base.update({
        "audit_valid": True,
        "ordered_failure_codes": [],
        "member_audit_tables": member_tables,
        "pair_audit_tables": pair_tables,
        "recursive_companion_tables": recursive_tables,
        "pair_classifications": classifications,
        "family_disposition": disposition,
    })
    return base


def _audit_configuration() -> Dict[str, Any]:
    return {
        "N": N,
        "K": 3,
        "class_convention": "inverse_shift_classes_q_1_to_32",
        "self_inverse_q": 32,
        "variant_order": list(VARIANTS),
        "full_variant": FULL_VARIANT,
        "k0_variant": K0_VARIANT,
        "comparison_tolerance": 0.0,
        "within_fraction_levels": list(WITHIN_FRACTION_LEVELS),
        "top_k_class_means": list(TOP_K_CLASS_MEANS),
        "top_k_distance_contribution": list(TOP_K_DISTANCE_CONTRIBUTION),
        "largest_aligned_start_limit": LARGEST_ALIGNED_START_LIMIT,
        "blocking_reference_member": "A",
        "blocking_reference_variant": FULL_VARIANT,
        "pair_classification": {
            "narrow_max": NARROW_MAX,
            "intermediate_min": INTERMEDIATE_MIN,
            "intermediate_max": INTERMEDIATE_MAX,
            "broad_min": BROAD_MIN,
        },
        "failure_namespace": FAILURE_NAMESPACE,
        "failure_version": FAILURE_VERSION,
    }


def _base_result(
    payload: Dict[str, Any],
    identities: Dict[str, Any],
    input_validation: Dict[str, Any],
    inverse: Dict[str, Any],
) -> Dict[str, Any]:
    config = _audit_configuration()
    return {
        "schema_name": AUDIT_SCHEMA_NAME,
        "schema_version": AUDIT_SCHEMA_VERSION,
        "input_relative_path": INPUT_RELATIVE_PATH,
        "input_size_bytes": identities.get("input_size_bytes"),
        "input_whole_file_sha256": identities.get("input_whole_file_sha256"),
        "input_payload_sha256": identities.get("input_payload_sha256"),
        "input_execution_commit_identity": INPUT_EXECUTION_COMMIT_IDENTITY,
        "audit_execution_commit_identity": identities.get("audit_execution_commit_identity"),
        "source_findings_commit_identity": SOURCE_FINDINGS_COMMIT_IDENTITY,
        "source_audit_specification_commit_identity": SOURCE_AUDIT_SPECIFICATION_COMMIT_IDENTITY,
        "source_implementation_authorization_commit_identity":
            SOURCE_IMPLEMENTATION_AUTHORIZATION_COMMIT_IDENTITY,
        "analyzer_git_blob_sha": identities.get("analyzer_git_blob_sha"),
        "analyzer_raw_file_sha256": identities.get("analyzer_raw_file_sha256"),
        "audit_configuration": config,
        "audit_configuration_sha256": sha256_bytes(canonical_json_bytes(config)),
        "pair_order": list(REQUIRED_ACCEPTED_CANDIDATE_INDICES),
        "member_order": _member_order(payload),
        "variant_order": list(VARIANTS),
        "input_validation": input_validation,
        "inverse_shift_validation": inverse,
        "authoritative_f3_verdict_preserved": REQUIRED_FAMILY_VERDICT,
        "non_claim_boundary": list(NON_CLAIM_BOUNDARY),
    }


def build_audit_payload(payload: Dict[str, Any], identities: Dict[str, Any]) -> Dict[str, Any]:
    return run_pure_audit(payload, identities)


def build_audit_envelope(audit_payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "asymmetry_audit_result": audit_payload,
        "asymmetry_audit_result_sha256": sha256_bytes(canonical_json_bytes(audit_payload)),
    }


# --------------------------------------------------------------------------- #
# Operator summary (convenience only)
# --------------------------------------------------------------------------- #

def render_operator_summary(audit_payload: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("TORMENT Brainvision algebraic N=64 PRIMARY_V0_1 frozen-family F3 asymmetry audit summary v0.1")
    lines.append("operator convenience only; not canonical audit evidence")
    lines.append("")
    lines.append("input_relative_path = %s" % audit_payload["input_relative_path"])
    lines.append("input_whole_file_sha256 = %s" % audit_payload["input_whole_file_sha256"])
    lines.append("input_payload_sha256 = %s" % audit_payload["input_payload_sha256"])
    lines.append("input_execution_commit_identity = %s" % audit_payload["input_execution_commit_identity"])
    lines.append("audit_execution_commit_identity = %s" % audit_payload["audit_execution_commit_identity"])
    lines.append("source_findings_commit_identity = %s" % audit_payload["source_findings_commit_identity"])
    lines.append("source_audit_specification_commit_identity = %s"
                 % audit_payload["source_audit_specification_commit_identity"])
    lines.append("source_implementation_authorization_commit_identity = %s"
                 % audit_payload["source_implementation_authorization_commit_identity"])
    lines.append("analyzer_git_blob_sha = %s" % audit_payload["analyzer_git_blob_sha"])
    lines.append("analyzer_raw_file_sha256 = %s" % audit_payload["analyzer_raw_file_sha256"])
    lines.append("")
    lines.append("pair_order = %s" % audit_payload["pair_order"])
    lines.append("audit_valid = %s" % audit_payload["audit_valid"])
    lines.append("ordered_failure_codes = %s" % audit_payload["ordered_failure_codes"])
    classifications = audit_payload.get("pair_classifications")
    if classifications:
        for c in classifications:
            lines.append("  candidate %s blocking_class_count = %s classification = %s"
                         % (c["candidate_generation_index"], c["blocking_class_count"], c["classification"]))
    lines.append("family_disposition = %s" % audit_payload["family_disposition"])
    lines.append("")
    lines.append("authoritative_f3_verdict_preserved = %s"
                 % audit_payload["authoritative_f3_verdict_preserved"])
    lines.append("descriptive audit only; A/B/C/D are not gates, thresholds, or rescue criteria")
    lines.append("the authoritative F3 verdict is unchanged by this audit")
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #
# Publication
# --------------------------------------------------------------------------- #

def _exclusive_write(path: Path, data: bytes) -> None:
    fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
    except BaseException:
        raise


def write_derived_artifacts_exclusively(
    final_dir: Path,
    staging_dir: Path,
    result_bytes: bytes,
    summary_bytes: bytes,
) -> None:
    """Exclusive staging + two-file set + single atomic rename. Retains evidence."""
    final_dir = Path(final_dir)
    staging_dir = Path(staging_dir)
    if final_dir.exists():
        raise AuditProcessFailure(OUTPUT_PATH_EXISTS, "final directory exists")
    if staging_dir.exists():
        raise AuditProcessFailure(OUTPUT_PATH_EXISTS, "staging directory exists")
    os.makedirs(str(final_dir.parent), exist_ok=True)
    try:
        os.mkdir(str(staging_dir))
    except OSError as exc:
        raise AuditProcessFailure(PUBLICATION_FAILURE, "cannot create staging: %s" % exc)
    artifact_written = False
    try:
        _exclusive_write(staging_dir / RESULT_FILE_NAME, result_bytes)
        artifact_written = True
        _exclusive_write(staging_dir / SUMMARY_FILE_NAME, summary_bytes)
        os.rename(str(staging_dir), str(final_dir))
    except BaseException as exc:
        if not artifact_written:
            # An empty staging directory created before any artifact byte was
            # written may be removed; a non-empty staging directory is retained.
            try:
                is_empty = next(iter(staging_dir.iterdir()), None) is None
                if is_empty:
                    os.rmdir(str(staging_dir))
            except OSError:
                pass
        raise AuditProcessFailure(PUBLICATION_FAILURE, "publication failed: %s" % exc)


# --------------------------------------------------------------------------- #
# Execution orchestration (injectable)
# --------------------------------------------------------------------------- #

def run_execution(
    *,
    gate_value: Optional[str],
    argv: Sequence[str] = (),
    repository_start_dir: Optional[str] = None,
    repo_state: Optional[Dict[str, str]] = None,
    source_identity: Optional[Dict[str, str]] = None,
    input_path: Optional[Path] = None,
    final_dir: Optional[Path] = None,
    staging_dir: Optional[Path] = None,
    stdout: Any = None,
    stderr: Any = None,
    git: GitRunner = _real_git,
    expected_input_size: int = EXPECTED_INPUT_SIZE_BYTES,
    expected_input_sha256: str = EXPECTED_INPUT_WHOLE_FILE_SHA256,
) -> int:
    """Internal execution function. Injectable for tests. Returns an exit code."""
    stdout = sys.stdout if stdout is None else stdout
    stderr = sys.stderr if stderr is None else stderr

    # ---- refusal phase (exit 2) ----
    try:
        if gate_value != GATE_VALUE_REQUIRED:
            raise AuditRefusal(AUDIT_NOT_AUTHORIZED, "gate absent or not '1'")
        if list(argv):
            raise AuditRefusal(UNEXPECTED_CLI_ARGUMENTS, "no command-line arguments accepted")

        if repo_state is None:
            if repository_start_dir is None:
                raise AuditRefusal(REPOSITORY_STATE_INVALID, "no repository start dir")
            repo_state = resolve_and_validate_repository_state(repository_start_dir, git=git)
        root = repo_state["repository_root"]

        if source_identity is None:
            analyzer_path = Path(root) / ANALYZER_RELATIVE_PATH
            source_identity = validate_analyzer_source_identity(root, analyzer_path, git=git)

        resolved_input = Path(input_path) if input_path is not None else Path(root) / INPUT_RELATIVE_PATH
        resolved_final = Path(final_dir) if final_dir is not None else Path(root) / FINAL_DIR_RELATIVE_PATH
        resolved_staging = Path(staging_dir) if staging_dir is not None else Path(root) / STAGING_DIR_RELATIVE_PATH

        if resolved_final.exists():
            raise AuditRefusal(OUTPUT_PATH_EXISTS, "final directory already exists")
        if resolved_staging.exists():
            raise AuditRefusal(OUTPUT_PATH_EXISTS, "staging directory already exists")

        loaded = load_and_validate_retained_input(
            resolved_input, expected_size=expected_input_size, expected_sha256=expected_input_sha256)
    except AuditRefusal as refusal:
        stderr.write("REFUSAL %s: %s\n" % (refusal.code, refusal.message))
        return EXIT_REFUSAL

    identities = {
        "input_size_bytes": loaded["input_size_bytes"],
        "input_whole_file_sha256": loaded["input_whole_file_sha256"],
        "input_payload_sha256": loaded["input_payload_sha256"],
        "audit_execution_commit_identity": repo_state.get("audit_execution_commit_identity"),
        "analyzer_git_blob_sha": source_identity.get("analyzer_git_blob_sha"),
        "analyzer_raw_file_sha256": source_identity.get("analyzer_raw_file_sha256"),
    }

    # ---- calculation + serialization (exit 1 on process failure) ----
    try:
        audit_payload = run_pure_audit(loaded["payload"], identities)
        envelope = build_audit_envelope(audit_payload)
        try:
            result_bytes = canonical_json_bytes(envelope)
        except (ValueError, TypeError) as exc:
            raise AuditProcessFailure(CANONICAL_SERIALIZATION_FAILURE, str(exc))
        summary_text = render_operator_summary(audit_payload)
        summary_bytes = summary_text.encode("utf-8")
    except AuditProcessFailure as exc:
        stderr.write("PROCESS_FAILURE %s: %s\n" % (exc.code, exc.message))
        return EXIT_PROCESS_FAILURE
    except Exception as exc:  # noqa: BLE001  (unexpected calculation exception)
        stderr.write("PROCESS_FAILURE %s: %s\n" % (AUDIT_CALCULATION_FAILURE, exc))
        return EXIT_PROCESS_FAILURE

    # ---- publication (exit 1 on failure; evidence-bearing staging retained) ----
    try:
        write_derived_artifacts_exclusively(resolved_final, resolved_staging, result_bytes, summary_bytes)
    except AuditProcessFailure as exc:
        stderr.write("PROCESS_FAILURE %s: %s\n" % (exc.code, exc.message))
        return EXIT_PROCESS_FAILURE
    except Exception as exc:  # noqa: BLE001
        stderr.write("PROCESS_FAILURE %s: %s\n" % (PUBLICATION_FAILURE, exc))
        return EXIT_PROCESS_FAILURE

    # ---- stdout mirror (exit 1 on failure; final directory preserved) ----
    try:
        stdout.write(summary_text)
        stdout.flush()
    except Exception as exc:  # noqa: BLE001
        stderr.write("PROCESS_FAILURE %s: %s\n" % (STDOUT_FAILURE, exc))
        return EXIT_PROCESS_FAILURE
    return EXIT_OK


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Real zero-argument CLI. Closed by default behind the audit gate."""
    args = list(sys.argv[1:] if argv is None else argv)
    here = Path(__file__).resolve().parent
    return run_execution(
        gate_value=os.environ.get(GATE_ENV),
        argv=args,
        repository_start_dir=str(here),
        stdout=sys.stdout,
        stderr=sys.stderr,
        git=_real_git,
    )


if __name__ == "__main__":
    sys.exit(main())

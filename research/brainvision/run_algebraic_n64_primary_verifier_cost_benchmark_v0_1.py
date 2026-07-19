"""TORMENT Brainvision algebraic N=64 PRIMARY_V0_1 verifier-cost benchmark v0.1 (offline; NON-AUTHORITATIVE).

Narrow, deterministic cost benchmark implementing docs/TORMENT_BRAINVISION_ALGEBRAIC_N64_PRIMARY_V0_1_
VERIFIER_COST_BENCHMARK_SPECIFICATION_v0.1.md. It times exactly one verifier call per sampled record over a
frozen 16-record two-pass profile and publishes a canonical cost report whose schema is DISTINCT from the
freezer's freeze_result. It performs NO family mathematics: it never selects a family, verifies a family,
freezes a family, or invokes the freezer. Its only witness-side call is verifier.verify_candidate, made once
per sampled record inside the timed region. It never calls verify_family, incremental_family_eligibility,
freeze, freeze_with_replay, or validate_local_configuration, and never imports the freezer, the freezer runner,
the generator, ΨTRS, descriptors, the N64 falsifier, or torment_service.

Operator interface (complete):

    python research\\brainvision\\run_algebraic_n64_primary_verifier_cost_benchmark_v0_1.py

No CLI argument, environment override, or configuration surface exists. The internal run_operation(...) accepts
test-only repository/result roots, a timer, an environment provider, and diagnostic streams, all unreachable
from the command line.

Exit contract (benchmark-level only; never a witness or freezer outcome):

    0  complete two-file publication with benchmark_status = BENCHMARK_COMPLETE
    1  verifier execution-invalid / exception / output mismatch / result-validation / serialization /
       I-O / publication / post-publication stdout failure
    2  pre-contact refusal

FORMAL HOLD and Mode 0 remain active. A complete benchmark establishes only per-call verifier cost under this
frozen non-random profile. It is a linear engineering measurement, not measured full-stream runtime, not total
freezer runtime, not a confidence interval, and not authorization or prediction of any freezer outcome.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import stat
import subprocess
import sys
import time
from typing import Callable, Dict, List, Optional, Tuple

# Committed verifier and serializer only. No freezer, generator, falsifier, or production import exists.
import witness_canonical_json_v0_1 as cjson
import witness_family_verifier_v0_1 as verifier

BENCHMARK_NAME = "run_algebraic_n64_primary_verifier_cost_benchmark_v0_1"
BENCHMARK_VERSION = "0.1"
GOVERNING_SPEC = ("docs/TORMENT_BRAINVISION_ALGEBRAIC_N64_PRIMARY_V0_1_"
                  "VERIFIER_COST_BENCHMARK_SPECIFICATION_v0.1.md")

BENCHMARK_PROFILE = "PRIMARY_V0_1_FIXED_16_TWO_PASS"
N = 64
PASSES = (1, 2)
PLANNED_CALL_COUNT = 32

# frozen sample order per pass; positions 0..7 = PREFIX_8, 8..15 = SPREAD_8
SAMPLE_INDICES = (0, 1, 2, 3, 4, 5, 6, 7,
                  2499, 4999, 7499, 9999, 12499, 14999, 17499, 19999)
PANEL_PREFIX = "PREFIX_8"
PANEL_SPREAD = "SPREAD_8"
PANEL_BY_POSITION = tuple(PANEL_PREFIX if position < 8 else PANEL_SPREAD for position in range(16))

RUNNER_RELATIVE_PATH = "research/brainvision/run_algebraic_n64_primary_verifier_cost_benchmark_v0_1.py"
EXPECTED_BRANCH = "main"

# direct source binding: runner blob resolved dynamically; verifier/serializer blobs frozen by the spec
SOURCE_RELATIVE_PATHS = {
    "runner": RUNNER_RELATIVE_PATH,
    "verifier": "research/brainvision/witness_family_verifier_v0_1.py",
    "serializer": "research/brainvision/witness_canonical_json_v0_1.py",
}
FROZEN_SOURCE_BLOB_IDS = {
    "verifier": "db1e1fa606bdbf17fda62cd998aeb2a29d47d59a",
    "serializer": "6eb382b314325033443fc7331cae5050ee6e6ed2",
}  # runner is intentionally absent: its committed HEAD blob is resolved dynamically

# frozen retained input identity
INPUT_RELATIVE_DIR = "research/brainvision/results/algebraic_n64_primary_v0_1"
INPUT_FILENAME = "algebraic_n64_primary_v0_1_candidate_stream.json"
INPUT_EXPECTED_SIZE = 6_421_010
INPUT_WHOLE_FILE_SHA256 = "00a816364ddcfc9d06dc8ce1225f58bca013e96a8914ff1eb665004b39ed949b"
INPUT_PAYLOAD_SHA256 = "70763a2ebbf7ea71267553debee2bf79c2ed3b7b0c016d9a903161074e7bf8c5"

STREAM_SCHEMA_NAME = "brainvision_descriptor_blind_candidate_stream"
STREAM_SCHEMA_VERSION = "0.1"
STREAM_VERIFICATION_MODE = "PRIMARY_CANDIDATE_N64"
STREAM_CANDIDATE_COUNT = 20000
STREAM_TERMINAL_STATUS = "budget_exhausted"

RESULT_SCHEMA_NAME = "brainvision_verifier_cost_benchmark_result"
RESULT_SCHEMA_VERSION = "0.1"
BENCHMARK_CLASS = "NON_AUTHORITATIVE_VERIFIER_COST_BENCHMARK"

RESULTS_RELATIVE_DIR = "research/brainvision/results"
FINAL_DIRECTORY_NAME = "algebraic_n64_primary_verifier_cost_benchmark_v0_1"
STAGING_DIRECTORY_NAME = ".algebraic_n64_primary_verifier_cost_benchmark_v0_1.staging"
RESULT_FILENAME = "algebraic_n64_primary_verifier_cost_benchmark_v0_1_result.json"
SUMMARY_FILENAME = "algebraic_n64_primary_verifier_cost_benchmark_v0_1_summary.txt"

# statuses
BENCHMARK_COMPLETE = "BENCHMARK_COMPLETE"
OUTPUT_REPLAY_MISMATCH = "OUTPUT_REPLAY_MISMATCH"
VERIFIER_EXECUTION_INVALID = "VERIFIER_EXECUTION_INVALID"
VERIFIER_CALL_EXCEPTION = "VERIFIER_CALL_EXCEPTION"
RESULT_SERIALIZATION_FAILURE = "RESULT_SERIALIZATION_FAILURE"
BENCHMARK_RESULT_INVALID = "BENCHMARK_RESULT_INVALID"
PUBLICATION_FAILURE = "PUBLICATION_FAILURE"

EXIT_PUBLISHED = 0
EXIT_FAILURE = 1
EXIT_REFUSED = 2

ABSENT = "absent"
LF = "\n"
_GIT_TIMEOUT_SECONDS = 30

_REQUIRED_VERIFIER_KEYS = ("execution_invalid", "execution_code", "pair_certificate",
                           "ordered_failure_codes", "primary_failure_code", "pair_valid")


class _Refusal(Exception):
    """Pre-contact refusal -> exit code 2. Raised only before any verify_candidate call."""

    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(code)
        self.code = code
        self.detail = detail


# --------------------------------------------------------------------------- path derivation
def _default_repository_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))


def _default_results_root(repository_root: str) -> str:
    return os.path.join(repository_root, "research", "brainvision", "results")


def _under_root(repository_root: str, relative_path: str) -> str:
    return os.path.join(repository_root, *relative_path.split("/"))


# --------------------------------------------------------------------------- small helpers
def _is_strict_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_strict_bool(value: object) -> bool:
    return isinstance(value, bool)


def _mapping(value: object) -> Optional[Dict[str, object]]:
    return value if isinstance(value, dict) else None


def file_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _gcd(a: int, b: int) -> int:
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a or 1


def _rational(numerator: int, denominator: int) -> Dict[str, object]:
    """Exact reduced rational nanoseconds; avoids all binary floating-point ambiguity in canonical evidence."""
    divisor = _gcd(int(numerator), int(denominator))
    reduced_num = int(numerator) // divisor
    reduced_den = int(denominator) // divisor
    if reduced_den < 0:
        reduced_num, reduced_den = -reduced_num, -reduced_den
    return {"numerator": reduced_num, "denominator": reduced_den}


def _is_regular_nonsymlink_file(path: str) -> bool:
    if os.path.islink(path):
        return False
    try:
        return stat.S_ISREG(os.lstat(path).st_mode)
    except OSError:
        return False


def _is_full_lower_hex_40(value: object) -> bool:
    return isinstance(value, str) and len(value) == 40 and all(c in "0123456789abcdef" for c in value)


# --------------------------------------------------------------------------- git (fixed-argument, non-shell)
def _git(repository_root: str, arguments: List[str]) -> Tuple[bool, str]:
    try:
        completed = subprocess.run(["git", "-C", repository_root] + arguments,
                                   capture_output=True, text=True, shell=False,
                                   timeout=_GIT_TIMEOUT_SECONDS)
    except (OSError, subprocess.SubprocessError):
        return False, ""
    if completed.returncode != 0:
        return False, ""
    return True, completed.stdout.strip()


def _git_blob_bytes(repository_root: str, blob_id: str) -> Optional[bytes]:
    try:
        completed = subprocess.run(["git", "-C", repository_root, "cat-file", "blob", blob_id],
                                   capture_output=True, shell=False, timeout=_GIT_TIMEOUT_SECONDS)
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout


# --------------------------------------------------------------------------- repository / source provenance
def _check_repository(repository_root: str, is_production: bool) -> str:
    resolved_root = os.path.realpath(repository_root)
    if not os.path.isdir(resolved_root):
        raise _Refusal("REPOSITORY_ROOT_INVALID", "root is not a directory")

    ok, toplevel = _git(resolved_root, ["rev-parse", "--show-toplevel"])
    if not ok or os.path.realpath(toplevel) != resolved_root:
        raise _Refusal("REPOSITORY_ROOT_MISMATCH", "git toplevel != derived root")

    expected_runner = _under_root(resolved_root, RUNNER_RELATIVE_PATH)
    if not _is_regular_nonsymlink_file(expected_runner):
        raise _Refusal("RUNNER_PATH_OWNERSHIP_INVALID", "runner not at expected path")
    if is_production and os.path.realpath(expected_runner) != os.path.realpath(__file__):
        raise _Refusal("RUNNER_PATH_OWNERSHIP_INVALID", "runner realpath mismatch")

    ok, branch = _git(resolved_root, ["symbolic-ref", "--short", "-q", "HEAD"])
    if not ok or branch != EXPECTED_BRANCH:
        raise _Refusal("BRANCH_NOT_MAIN", "branch != main")

    ok, head = _git(resolved_root, ["rev-parse", "--verify", "HEAD^{commit}"])
    if not ok or not _is_full_lower_hex_40(head):
        raise _Refusal("HEAD_UNRESOLVED", "HEAD did not resolve")

    ok, origin = _git(resolved_root, ["rev-parse", "--verify", "refs/remotes/origin/main^{commit}"])
    if not ok or origin != head:
        raise _Refusal("ORIGIN_MAIN_MISMATCH", "origin/main != HEAD")

    ok, porcelain = _git(resolved_root, ["status", "--porcelain=v1", "--untracked-files=all"])
    if not ok or porcelain != "":
        raise _Refusal("WORKING_TREE_NOT_CLEAN", "tracked/untracked entries present")

    return head


def _bind_sources(repository_root: str) -> Dict[str, Dict[str, str]]:
    """Direct source binding for runner/verifier/serializer. Returns per-role identity mapping."""
    identities: Dict[str, Dict[str, str]] = {}
    brainvision_dir = os.path.realpath(_under_root(repository_root, "research/brainvision"))

    for role, relative in SOURCE_RELATIVE_PATHS.items():
        absolute = _under_root(repository_root, relative)
        if not _is_regular_nonsymlink_file(absolute):
            raise _Refusal("SOURCE_PATH_INVALID", "not a regular file or is a symlink: " + role)
        resolved = os.path.realpath(absolute)
        if os.path.commonpath([brainvision_dir, resolved]) != brainvision_dir:
            raise _Refusal("SOURCE_PATH_INVALID", "escapes research/brainvision: " + role)

        ok, blob_id = _git(repository_root, ["rev-parse", "--verify", "HEAD:" + relative])
        if not ok or not _is_full_lower_hex_40(blob_id):
            raise _Refusal("SOURCE_NOT_COMMITTED", role)
        ok, object_type = _git(repository_root, ["cat-file", "-t", blob_id])
        if not ok or object_type != "blob":
            raise _Refusal("SOURCE_TREE_ENTRY_NOT_BLOB", role)
        if role in FROZEN_SOURCE_BLOB_IDS and blob_id != FROZEN_SOURCE_BLOB_IDS[role]:
            raise _Refusal("SOURCE_BLOB_IDENTITY_MISMATCH", role)

        committed_bytes = _git_blob_bytes(repository_root, blob_id)
        if committed_bytes is None:
            raise _Refusal("SOURCE_BLOB_UNREADABLE", role)
        with open(resolved, "rb") as handle:
            local_bytes = handle.read()
        if local_bytes != committed_bytes:
            raise _Refusal("SOURCE_BYTES_DIFFER_FROM_COMMIT", role)

        identities[role] = {"path": relative, "blob_id": blob_id, "sha256": file_sha256(committed_bytes)}
    return identities


# --------------------------------------------------------------------------- input loading
def _reject_duplicate_keys(pairs: List[Tuple[str, object]]) -> Dict[str, object]:
    keys = [key for key, _value in pairs]
    if len(set(keys)) != len(keys):
        raise ValueError("duplicate object keys")
    return dict(pairs)


def _reject_nonfinite(_token: str) -> object:
    raise ValueError("nonfinite JSON constant")


def _load_input(repository_root: str) -> Dict[str, object]:
    input_path = os.path.join(_under_root(repository_root, INPUT_RELATIVE_DIR), INPUT_FILENAME)
    if not _is_regular_nonsymlink_file(input_path):
        raise _Refusal("INPUT_PATH_INVALID", "input not a regular non-symlink file")

    with open(input_path, "rb") as handle:
        loaded_bytes = handle.read()
    if len(loaded_bytes) != INPUT_EXPECTED_SIZE:
        raise _Refusal("INPUT_SIZE_MISMATCH", "%d != %d" % (len(loaded_bytes), INPUT_EXPECTED_SIZE))
    if file_sha256(loaded_bytes) != INPUT_WHOLE_FILE_SHA256:
        raise _Refusal("INPUT_WHOLE_FILE_HASH_MISMATCH", "")

    try:
        text = loaded_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise _Refusal("INPUT_NOT_UTF8", "")
    try:
        parsed = json.loads(text, object_pairs_hook=_reject_duplicate_keys, parse_constant=_reject_nonfinite)
    except ValueError as error:
        raise _Refusal("INPUT_JSON_INVALID", str(error))
    if not isinstance(parsed, dict):
        raise _Refusal("INPUT_NOT_A_MAPPING", "")

    try:
        canonical = cjson.canonical_json_bytes(parsed)
    except (ValueError, TypeError):
        raise _Refusal("INPUT_NOT_CANONICAL", "not canonically serializable")
    if canonical != loaded_bytes:
        raise _Refusal("INPUT_NOT_CANONICAL", "canonical bytes differ from loaded bytes")

    if parsed.get("candidate_stream_sha256") != INPUT_PAYLOAD_SHA256:
        raise _Refusal("INPUT_PAYLOAD_HASH_FIELD_MISMATCH", "")
    stream = _mapping(parsed.get("candidate_stream"))
    if stream is None:
        raise _Refusal("INPUT_STRUCTURE_INVALID", "missing candidate_stream mapping")
    if cjson.payload_sha256(stream) != INPUT_PAYLOAD_SHA256:
        raise _Refusal("INPUT_PAYLOAD_HASH_RECOMPUTE_MISMATCH", "")

    validation = verifier.validate_stream_envelope(parsed)
    if not validation.get("valid"):
        raise _Refusal("INPUT_STREAM_ENVELOPE_INVALID", str(validation.get("code")))

    _require_frozen_structure(stream)
    _require_sampled_records(stream)
    return stream


def _require_frozen_structure(stream: Dict[str, object]) -> None:
    checks = (
        ("schema_name", STREAM_SCHEMA_NAME), ("schema_version", STREAM_SCHEMA_VERSION),
        ("verification_mode", STREAM_VERIFICATION_MODE), ("N", N),
        ("candidate_count", STREAM_CANDIDATE_COUNT), ("terminal_status", STREAM_TERMINAL_STATUS),
    )
    for field, expected in checks:
        if stream.get(field) != expected:
            raise _Refusal("INPUT_STRUCTURE_INVALID", "field %s" % field)
    records = stream.get("records")
    if not isinstance(records, list) or len(records) != STREAM_CANDIDATE_COUNT:
        raise _Refusal("INPUT_STRUCTURE_INVALID", "records length")
    for index, record in enumerate(records):
        if not isinstance(record, dict) or record.get("candidate_generation_index") != index:
            raise _Refusal("INPUT_STRUCTURE_INVALID", "non-contiguous index at %d" % index)


def _require_sampled_records(stream: Dict[str, object]) -> None:
    records = stream["records"]
    for index in SAMPLE_INDICES:
        if index >= len(records):
            raise _Refusal("SAMPLE_INDEX_OUT_OF_RANGE", str(index))
        record = records[index]
        if not isinstance(record, dict) or record.get("candidate_generation_index") != index:
            raise _Refusal("SAMPLE_INDEX_MISMATCH", str(index))


# --------------------------------------------------------------------------- environment
def _default_environment() -> Dict[str, object]:
    clock = time.get_clock_info("perf_counter")
    return {
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "os_name": platform.system(),
        "os_release": platform.release(),
        "machine_architecture": platform.machine(),
        "logical_cpu_count": (os.cpu_count() or 0),
        "process_bitness_bits": (64 if sys.maxsize > 2 ** 32 else 32),
        "perf_counter_resolution": repr(clock.resolution),
        "perf_counter_monotonic": bool(clock.monotonic),
        "perf_counter_adjustable": bool(clock.adjustable),
    }


# --------------------------------------------------------------------------- timed verifier call
def _timed_verify(record: Dict[str, object], timer_ns: Callable[[], int]
                  ) -> Tuple[int, object]:
    """The ONLY timed region and the ONLY verify_candidate call site. Nothing else runs between the clocks."""
    started_ns = timer_ns()
    result = verifier.verify_candidate(record, N)
    completed_ns = timer_ns()
    return completed_ns - started_ns, result


# --------------------------------------------------------------------------- statistics
def _aggregate(durations: List[int]) -> Dict[str, object]:
    count = len(durations)
    if count == 0:
        return {"count": 0, "total_ns": 0, "minimum_ns": None, "maximum_ns": None,
                "mean_ns": None, "median_ns": None, "p25_ns": None, "p75_ns": None}
    ordered = sorted(durations)
    total = sum(ordered)
    if count % 2 == 1:
        median = _rational(ordered[count // 2], 1)
    else:
        median = _rational(ordered[count // 2 - 1] + ordered[count // 2], 2)
    p25_rank = min(max((count + 3) // 4, 1), count)      # ceil(0.25*count), 1-based, clamped
    p75_rank = min(max((3 * count + 3) // 4, 1), count)  # ceil(0.75*count), 1-based, clamped
    return {"count": count, "total_ns": total, "minimum_ns": ordered[0], "maximum_ns": ordered[-1],
            "mean_ns": _rational(total, count), "median_ns": median,
            "p25_ns": ordered[p25_rank - 1], "p75_ns": ordered[p75_rank - 1]}


def _panel_durations(call_records: List[Dict[str, object]], pass_number: Optional[int],
                     panel: Optional[str]) -> List[int]:
    return [int(record["duration_ns"]) for record in call_records
            if (pass_number is None or record["pass_number"] == pass_number)
            and (panel is None or record["panel"] == panel)
            and _is_strict_int(record["duration_ns"])]


def _statistics(call_records: List[Dict[str, object]]) -> Dict[str, object]:
    def group(pass_number: Optional[int]) -> Dict[str, object]:
        return {
            PANEL_PREFIX: _aggregate(_panel_durations(call_records, pass_number, PANEL_PREFIX)),
            PANEL_SPREAD: _aggregate(_panel_durations(call_records, pass_number, PANEL_SPREAD)),
            "overall": _aggregate(_panel_durations(call_records, pass_number, None)),
        }
    return {"pass_1": group(1), "pass_2": group(2), "combined": group(None)}


def _linear_projections(call_records: List[Dict[str, object]]) -> Dict[str, object]:
    all_durations = _panel_durations(call_records, None, None)
    prefix_durations = _panel_durations(call_records, None, PANEL_PREFIX)
    spread_durations = _panel_durations(call_records, None, PANEL_SPREAD)
    overall_total, overall_count = sum(all_durations), len(all_durations)
    prefix_total, prefix_count = sum(prefix_durations), len(prefix_durations)
    spread_total, spread_count = sum(spread_durations), len(spread_durations)
    label = ["linear engineering projection", "not measured full-stream runtime",
             "not total freezer runtime", "not a confidence interval", "not a guarantee"]
    return {
        "labels": label,
        "overall_mean_times_16_ns": _rational(overall_total * 16, overall_count),
        "overall_mean_times_20000_ns": _rational(overall_total * 20000, overall_count),
        "overall_mean_times_40000_ns": _rational(overall_total * 40000, overall_count),
        "prefix_mean_times_40000_ns": _rational(prefix_total * 40000, prefix_count),
        "spread_mean_times_40000_ns": _rational(spread_total * 40000, spread_count),
    }


# --------------------------------------------------------------------------- verifier output handling
def _validate_verifier_output(result: object) -> Optional[str]:
    payload = _mapping(result)
    if payload is None:
        return "OUTPUT_NOT_A_MAPPING"
    for key in _REQUIRED_VERIFIER_KEYS:
        if key not in payload:
            return "OUTPUT_MISSING_" + key.upper()
    if not _is_strict_bool(payload.get("execution_invalid")):
        return "OUTPUT_EXECUTION_INVALID_NOT_BOOL"
    if not _is_strict_bool(payload.get("pair_valid")):
        return "OUTPUT_PAIR_VALID_NOT_BOOL"
    return None


def _call_record(pass_number: int, position: int, index: int, duration_ns: int,
                 result: Dict[str, object], canonical_sha256: str) -> Dict[str, object]:
    return {
        "pass_number": pass_number, "panel": PANEL_BY_POSITION[position],
        "sample_order_position": position, "candidate_generation_index": index,
        "duration_ns": duration_ns,
        "execution_invalid": bool(result["execution_invalid"]),
        "execution_code": result.get("execution_code"),
        "pair_valid": bool(result["pair_valid"]),
        "primary_failure_code": result.get("primary_failure_code"),
        "ordered_failure_codes": list(result.get("ordered_failure_codes") or []),
        "canonical_result_sha256": canonical_sha256,
    }


# --------------------------------------------------------------------------- result / summary
def _boundary_declarations() -> Dict[str, object]:
    return {
        "benchmark_is_non_authoritative": True,
        "freezer_invoked": False,
        "family_selection_performed": False,
        "family_verification_performed": False,
        "family_freeze_performed": False,
        "retained_stream_modified": False,
        "output_identity_is_not_authoritative_freezer_replay": True,
        "scientific_inference_authorized": False,
    }


def _build_result_payload(head: str, source_identities: Dict[str, Dict[str, str]],
                          environment: Dict[str, object], call_records: List[Dict[str, object]],
                          statistics: Dict[str, object], projections: Optional[Dict[str, object]],
                          pass_identity: Dict[str, object], status: str,
                          failure_record: Optional[Dict[str, object]],
                          verifier_config: Dict[str, object], verifier_config_sha256: str
                          ) -> Dict[str, object]:
    return {
        "schema_name": RESULT_SCHEMA_NAME, "schema_version": RESULT_SCHEMA_VERSION,
        "benchmark_class": BENCHMARK_CLASS, "benchmark_profile": BENCHMARK_PROFILE,
        "authoritative_operation": False, "family_selection_performed": False,
        "family_verification_performed": False, "family_freeze_performed": False,
        "repository_commit_identity": head,
        "source_identities": source_identities,
        "verifier_configuration_payload": verifier_config,
        "verifier_configuration_sha256": verifier_config_sha256,
        "input_identity": {
            "path": INPUT_RELATIVE_DIR + "/" + INPUT_FILENAME, "size_bytes": INPUT_EXPECTED_SIZE,
            "whole_file_sha256": INPUT_WHOLE_FILE_SHA256, "payload_sha256": INPUT_PAYLOAD_SHA256},
        "sample_definition": {
            "profile": BENCHMARK_PROFILE, "sample_indices": list(SAMPLE_INDICES),
            "panels": {PANEL_PREFIX: list(SAMPLE_INDICES[:8]), PANEL_SPREAD: list(SAMPLE_INDICES[8:])},
            "passes": list(PASSES)},
        "environment": environment,
        "planned_call_count": PLANNED_CALL_COUNT,
        "completed_call_count": len(call_records),
        "call_records": call_records,
        "statistics": statistics,
        "linear_projections": projections,
        "pass_to_pass_identity": pass_identity,
        "benchmark_status": status,
        "failure_record": failure_record,
        "boundary_declarations": _boundary_declarations(),
    }


def _summary_text(payload: Dict[str, object], status: str, result_file_sha256: str) -> str:
    """Construct the complete summary ONCE, before publication. It states benchmark computation facts and the
    intended artifact contents; it never claims that the later rename or stdout mirroring succeeded."""
    lines: List[str] = []
    lines.append("TORMENT Brainvision algebraic N=64 PRIMARY_V0_1 verifier-cost benchmark summary v%s"
                 % BENCHMARK_VERSION)
    lines.append("governing specification = %s" % GOVERNING_SPEC)
    lines.append("benchmark is non-authoritative")
    lines.append("")
    lines.append("benchmark_profile = %s" % BENCHMARK_PROFILE)
    lines.append("benchmark_status = %s" % status)
    lines.append("benchmark computation status = %s" % status)
    lines.append("repository_commit_identity = %s" % payload.get("repository_commit_identity"))
    lines.append("planned_call_count = %d" % PLANNED_CALL_COUNT)
    lines.append("completed_call_count = %d" % payload.get("completed_call_count"))
    lines.append("verify_candidate calls completed = %d" % payload.get("completed_call_count"))
    lines.append("")
    combined = _mapping(_mapping(payload.get("statistics")).get("combined")) if _mapping(
        payload.get("statistics")) else None
    overall = _mapping(combined.get("overall")) if combined else None
    if overall and overall.get("count"):
        mean = _mapping(overall.get("mean_ns"))
        lines.append("combined overall count = %s" % overall.get("count"))
        lines.append("combined overall minimum_ns = %s" % overall.get("minimum_ns"))
        lines.append("combined overall maximum_ns = %s" % overall.get("maximum_ns"))
        if mean:
            lines.append("combined overall mean_ns = %d/%d (~ %.1f ns)"
                         % (mean["numerator"], mean["denominator"],
                            mean["numerator"] / mean["denominator"]))
    projections = _mapping(payload.get("linear_projections"))
    if projections:
        proj = _mapping(projections.get("overall_mean_times_40000_ns"))
        if proj:
            seconds = proj["numerator"] / proj["denominator"] / 1e9
            lines.append("")
            lines.append("linear engineering projection (verifier component, two-pass 40000 calls):")
            lines.append("  overall_mean_ns * 40000 = %d/%d ns (~ %.3f s, ~ %.3f min, ~ %.4f h)"
                         % (proj["numerator"], proj["denominator"], seconds, seconds / 60.0,
                            seconds / 3600.0))
            lines.append("  not measured full-stream runtime; not total freezer runtime; not a guarantee")
    failure = _mapping(payload.get("failure_record"))
    lines.append("")
    if failure:
        lines.append("failure_code = %s" % failure.get("failure_code"))
        lines.append("failure_stage = %s" % failure.get("stage"))
    else:
        lines.append("failure_code = %s" % ABSENT)
    lines.append("result_whole_file_sha256 = %s" % result_file_sha256)
    lines.append("planned artifact set = result+summary")
    lines.append("publication protocol = staging-to-final atomic rename")
    lines.append("")
    lines.append("freezer calls = 0")
    lines.append("family-selection calls = 0")
    lines.append("family-verification calls = 0")
    lines.append("family frozen = not evaluated")
    lines.append("retained stream modified = False")
    lines.append("PsiTRS invoked = False")
    lines.append("scientific interpretation performed = False")
    return LF.join(lines) + LF


# --------------------------------------------------------------------------- staging / publication
def _write_exclusive(path: str, data: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(data)


def _remove_empty_staging(staging_path: str) -> None:
    try:
        if os.path.isdir(staging_path) and not os.listdir(staging_path):
            os.rmdir(staging_path)
    except OSError:
        pass


def _safe_write(stream, text: str) -> None:
    try:
        stream.write(text)
    except Exception:
        pass


# --------------------------------------------------------------------------- the operation
def run_operation(repository_root: Optional[str] = None, results_root: Optional[str] = None,
                  extra_arguments: Optional[List[str]] = None,
                  timer_ns: Optional[Callable[[], int]] = None,
                  environment: Optional[Dict[str, object]] = None, stdout=None, stderr=None) -> int:
    out = stdout if stdout is not None else sys.stdout
    err = stderr if stderr is not None else sys.stderr

    if extra_arguments:
        _safe_write(err, "%s: takes no arguments; pre-contact refusal\n" % BENCHMARK_NAME)
        return EXIT_REFUSED

    is_production = repository_root is None
    root = os.path.realpath(repository_root) if repository_root is not None else _default_repository_root()
    results = results_root if results_root is not None else _default_results_root(root)
    final_path = os.path.join(results, FINAL_DIRECTORY_NAME)
    staging_path = os.path.join(results, STAGING_DIRECTORY_NAME)
    clock = timer_ns if timer_ns is not None else time.perf_counter_ns

    # ---- pre-contact refusals (exit 2); verify_candidate is called zero times on any failure ----
    try:
        if os.path.exists(final_path):
            raise _Refusal("FINAL_DIRECTORY_EXISTS", final_path)
        if os.path.exists(staging_path):
            raise _Refusal("STAGING_DIRECTORY_EXISTS", staging_path)
        head = _check_repository(root, is_production)
        source_identities = _bind_sources(root)
        stream = _load_input(root)
    except _Refusal as refusal:
        _safe_write(err, "%s: pre-contact refusal %s %s\n" % (BENCHMARK_NAME, refusal.code, refusal.detail))
        return EXIT_REFUSED

    env = dict(environment) if environment is not None else _default_environment()
    verifier_config = verifier.verifier_configuration()
    verifier_config_sha256 = cjson.payload_sha256(verifier_config)
    records = stream["records"]

    # ---- staging reservation (only after every pre-contact check passed) ----
    try:
        os.makedirs(staging_path)
    except OSError:
        _safe_write(err, "%s: staging reservation failed (path appeared)\n" % BENCHMARK_NAME)
        return EXIT_REFUSED

    # ---- two measured passes; exactly one timed verify_candidate call per sampled record ----
    call_records: List[Dict[str, object]] = []
    hashes_by_pass: Dict[int, Dict[int, str]] = {1: {}, 2: {}}
    status = BENCHMARK_COMPLETE
    failure_record: Optional[Dict[str, object]] = None

    for pass_number in PASSES:
        if failure_record is not None:
            break
        for position, index in enumerate(SAMPLE_INDICES):
            record = records[index]
            try:
                duration_ns, result = _timed_verify(record, clock)
            except Exception as error:  # noqa: BLE001 - contain verifier exceptions
                status = VERIFIER_CALL_EXCEPTION
                failure_record = {"failure_code": VERIFIER_CALL_EXCEPTION, "stage": "verify_candidate",
                                  "pass_number": pass_number, "candidate_generation_index": index,
                                  "detail": repr(error)}
                break

            # a duration must be a strict nonnegative integer; an injected timer must never manufacture
            # a "successful" invalid measurement. The production perf_counter_ns path is naturally monotone.
            if not _is_strict_int(duration_ns) or duration_ns < 0:
                status = BENCHMARK_RESULT_INVALID
                failure_record = {"failure_code": BENCHMARK_RESULT_INVALID, "stage": "negative_duration",
                                  "pass_number": pass_number, "candidate_generation_index": index}
                break

            shape_error = _validate_verifier_output(result)
            if shape_error is not None:
                status = BENCHMARK_RESULT_INVALID
                failure_record = {"failure_code": BENCHMARK_RESULT_INVALID, "stage": shape_error,
                                  "pass_number": pass_number, "candidate_generation_index": index}
                break

            try:
                canonical_sha256 = cjson.payload_sha256(result)
            except (ValueError, TypeError) as error:
                status = RESULT_SERIALIZATION_FAILURE
                failure_record = {"failure_code": RESULT_SERIALIZATION_FAILURE, "stage": "result_hash",
                                  "pass_number": pass_number, "candidate_generation_index": index,
                                  "detail": repr(error)}
                break

            call_records.append(_call_record(pass_number, position, index, duration_ns, result,
                                             canonical_sha256))
            hashes_by_pass[pass_number][index] = canonical_sha256

            if result["execution_invalid"] is True:
                status = VERIFIER_EXECUTION_INVALID
                failure_record = {"failure_code": VERIFIER_EXECUTION_INVALID, "stage": "execution_invalid",
                                  "pass_number": pass_number, "candidate_generation_index": index,
                                  "execution_code": result.get("execution_code")}
                break

    # ---- pass-to-pass output identity (only meaningful if both passes completed) ----
    pass_identity: Dict[str, object] = {"checked": False, "all_match": False, "mismatched_indices": []}
    if failure_record is None:
        mismatched = [index for index in SAMPLE_INDICES
                      if hashes_by_pass[1].get(index) != hashes_by_pass[2].get(index)]
        pass_identity = {"checked": True, "all_match": (mismatched == []),
                         "mismatched_indices": mismatched}
        if mismatched:
            status = OUTPUT_REPLAY_MISMATCH
            failure_record = {"failure_code": OUTPUT_REPLAY_MISMATCH, "stage": "pass_to_pass_identity",
                              "mismatched_indices": mismatched}

    complete = (status == BENCHMARK_COMPLETE and len(call_records) == PLANNED_CALL_COUNT)
    statistics = _statistics(call_records)
    projections = _linear_projections(call_records) if complete else None

    payload = _build_result_payload(head, source_identities, env, call_records, statistics, projections,
                                    pass_identity, status, failure_record, verifier_config,
                                    verifier_config_sha256)

    # ---- serialize the result ONCE, outside any timed region ----
    try:
        result_bytes = cjson.canonical_json_bytes(cjson.envelope("verifier_cost_benchmark_result", payload))
    except (ValueError, TypeError) as error:
        _safe_write(err, "%s: %s %r; staging retained\n" % (BENCHMARK_NAME, RESULT_SERIALIZATION_FAILURE,
                                                            error))
        return EXIT_FAILURE  # staging holds no complete evidence set; retained, never auto-removed

    # ---- compute the whole-file result hash BEFORE constructing the summary; build the summary ONCE ----
    result_file_sha256 = hashlib.sha256(result_bytes).hexdigest()
    exit_code = EXIT_PUBLISHED if complete else EXIT_FAILURE
    summary_text = _summary_text(payload, status, result_file_sha256)
    summary_bytes = summary_text.encode("utf-8")

    # ---- write the exact two-file set entirely inside staging (exclusive; never overwrites) ----
    try:
        _write_exclusive(os.path.join(staging_path, RESULT_FILENAME), result_bytes)
        _write_exclusive(os.path.join(staging_path, SUMMARY_FILENAME), summary_bytes)
    except OSError as error:
        _safe_write(err, "%s: artifact write failed %r; staging retained\n" % (BENCHMARK_NAME, error))
        return EXIT_FAILURE  # any staged evidence bytes are retained; final is never created

    # ---- verify staging holds exactly the required two-file set before the single publication event ----
    if sorted(os.listdir(staging_path)) != sorted([RESULT_FILENAME, SUMMARY_FILENAME]):
        _safe_write(err, "%s: staged set mismatch; staging retained\n" % BENCHMARK_NAME)
        return EXIT_FAILURE

    # ---- single publication event: staging -> final. Nothing below reopens either final artifact. ----
    try:
        os.rename(staging_path, final_path)
    except OSError as error:
        _safe_write(err, "%s: publication rename failed %r; complete staging retained\n"
                    % (BENCHMARK_NAME, error))
        return EXIT_FAILURE  # complete two-file staging retained; no staged artifact is rewritten

    if failure_record is not None:
        _safe_write(err, "%s: benchmark_status %s\n" % (BENCHMARK_NAME, status))

    # ---- mirror the already-constructed in-memory summary; no final artifact is reopened for writing ----
    try:
        out.write(summary_text)
    except Exception as error:  # noqa: BLE001
        _safe_write(err, "%s: stdout mirroring failed after publication: %r\n" % (BENCHMARK_NAME, error))
        _safe_write(err, "%s: the published artifact set is intact and was not rolled back\n" % BENCHMARK_NAME)
        return EXIT_FAILURE

    return exit_code


# --------------------------------------------------------------------------- entry point
def main(argv: Optional[List[str]] = None) -> int:
    arguments = (argv if argv is not None else sys.argv)[1:]
    if arguments:
        sys.stderr.write("%s: takes no arguments; invoke exactly:\n" % BENCHMARK_NAME)
        sys.stderr.write("  python research\\brainvision\\%s.py\n" % BENCHMARK_NAME)
        return EXIT_REFUSED
    return run_operation()


if __name__ == "__main__":
    sys.exit(main())

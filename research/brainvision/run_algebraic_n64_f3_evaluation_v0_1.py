"""Frozen-family F3 evaluation runner for the algebraic N=64 PRIMARY_V0_1 witness family (offline; gated).

Zero-argument CLI. Closed by default: production descriptor contact requires the exact environment gate
ALGEBRAIC_N64_F3_EVALUATION_AUTHORIZED=1 and passes all pre-contact checks first. Descriptor contact is
delegated entirely to algebraic_n64_f3_evaluator_v0_1.build_production_feature_cache; this runner performs no
witness mathematics. Importing this module does nothing: no evaluation, no descriptor call, no file creation.

This runner must not become an engine for the old N64 runner and imports neither it, the freezer, the
generator, ΨTRS directly, any prerecorded harness, SAG, nor anything under torment_service.

Governing specification:
  docs/TORMENT_BRAINVISION_ALGEBRAIC_N64_PRIMARY_V0_1_F3_EVALUATOR_IMPLEMENTATION_SPECIFICATION_v0.1.md

FORMAL_HOLD and Mode_0 remain active. Offline, quarantined, non-runtime, non-production, descriptive-only.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import stat
import subprocess
import sys
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np

import witness_canonical_json_v0_1 as cjson
import algebraic_n64_f3_frozen_identity_v0_1 as frozen
import algebraic_n64_f3_evaluator_v0_1 as evaluator

RUNNER_NAME = "run_algebraic_n64_f3_evaluation_v0_1"
RUNNER_VERSION = "0.1"
GOVERNING_SPEC = ("docs/TORMENT_BRAINVISION_ALGEBRAIC_N64_PRIMARY_V0_1_"
                  "F3_EVALUATOR_IMPLEMENTATION_SPECIFICATION_v0.1.md")

EVALUATION_AUTHORIZATION_ENV = "ALGEBRAIC_N64_F3_EVALUATION_AUTHORIZED"
EVALUATION_AUTHORIZATION_VALUE = "1"
EXPECTED_BRANCH = "main"

RUNNER_RELATIVE_PATH = "research/brainvision/run_algebraic_n64_f3_evaluation_v0_1.py"
SOURCE_RELATIVE_PATHS = {
    "frozen_identity": "research/brainvision/algebraic_n64_f3_frozen_identity_v0_1.py",
    "evaluator": "research/brainvision/algebraic_n64_f3_evaluator_v0_1.py",
    "runner": RUNNER_RELATIVE_PATH,
    "psi_trs": "research/brainvision/psi_trs.py",
    "verifier": "research/brainvision/witness_family_verifier_v0_1.py",
    "serializer": "research/brainvision/witness_canonical_json_v0_1.py",
}

INPUT_RELATIVE_DIR = "research/brainvision/results/algebraic_n64_primary_v0_1_freeze_v0_1"
INPUT_FILENAME = "algebraic_n64_primary_v0_1_freeze_result.json"

RESULTS_RELATIVE_DIR = "research/brainvision/results"
FINAL_DIRECTORY_NAME = "algebraic_n64_primary_v0_1_f3_evaluation_v0_1"
STAGING_DIRECTORY_NAME = ".algebraic_n64_primary_v0_1_f3_evaluation_v0_1.staging"
RESULT_FILENAME = "algebraic_n64_primary_v0_1_f3_evaluation_result.json"
SUMMARY_FILENAME = "algebraic_n64_primary_v0_1_f3_evaluation_summary.txt"

SCHEMA_NAME = evaluator.SCHEMA_NAME
SCHEMA_VERSION = evaluator.SCHEMA_VERSION

EXIT_PUBLISHED = 0
EXIT_FAILURE = 1
EXIT_REFUSED = 2

ABSENT = "absent"
LF = "\n"
_GIT_TIMEOUT_SECONDS = 30


class _Refusal(Exception):
    """Pre-contact refusal -> exit 2. Raised only before the first production descriptor call."""

    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(code)
        self.code = code
        self.detail = detail


# --------------------------------------------------------------------------- paths / helpers
def _default_repository_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))


def _under_root(repository_root: str, relative_path: str) -> str:
    return os.path.join(repository_root, *relative_path.split("/"))


def file_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _is_regular_nonsymlink_file(path: str) -> bool:
    if os.path.islink(path):
        return False
    try:
        return stat.S_ISREG(os.lstat(path).st_mode)
    except OSError:
        return False


def _is_full_lower_hex_40(value: object) -> bool:
    return isinstance(value, str) and len(value) == 40 and all(c in "0123456789abcdef" for c in value)


def _safe_write(stream, text: str) -> None:
    try:
        stream.write(text)
    except Exception:
        pass


def _write_exclusive(path: str, data: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(data)


# --------------------------------------------------------------------------- git (fixed-argument, non-shell)
def _git(repository_root: str, arguments: List[str]) -> Tuple[bool, str]:
    try:
        completed = subprocess.run(["git", "-C", repository_root] + arguments, capture_output=True,
                                   text=True, shell=False, timeout=_GIT_TIMEOUT_SECONDS)
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


# --------------------------------------------------------------------------- repository / source preflight
def _check_repository(repository_root: str, is_production: bool) -> str:
    resolved_root = os.path.realpath(repository_root)
    if not os.path.isdir(resolved_root):
        raise _Refusal(evaluator.REPOSITORY_STATE_INVALID, "root is not a directory")
    ok, toplevel = _git(resolved_root, ["rev-parse", "--show-toplevel"])
    if not ok or os.path.realpath(toplevel) != resolved_root:
        raise _Refusal(evaluator.REPOSITORY_STATE_INVALID, "git toplevel != derived root")
    expected_runner = _under_root(resolved_root, RUNNER_RELATIVE_PATH)
    if not _is_regular_nonsymlink_file(expected_runner):
        raise _Refusal(evaluator.REPOSITORY_STATE_INVALID, "runner not at expected path")
    if is_production and os.path.realpath(expected_runner) != os.path.realpath(__file__):
        raise _Refusal(evaluator.REPOSITORY_STATE_INVALID, "runner realpath mismatch")
    ok, branch = _git(resolved_root, ["symbolic-ref", "--short", "-q", "HEAD"])
    if not ok or branch != EXPECTED_BRANCH:
        raise _Refusal(evaluator.REPOSITORY_STATE_INVALID, "branch != main")
    ok, head = _git(resolved_root, ["rev-parse", "--verify", "HEAD^{commit}"])
    if not ok or not _is_full_lower_hex_40(head):
        raise _Refusal(evaluator.REPOSITORY_STATE_INVALID, "HEAD did not resolve")
    ok, origin = _git(resolved_root, ["rev-parse", "--verify", "refs/remotes/origin/main^{commit}"])
    if not ok or origin != head:
        raise _Refusal(evaluator.REPOSITORY_STATE_INVALID, "origin/main != HEAD")
    ok, porcelain = _git(resolved_root, ["status", "--porcelain=v1", "--untracked-files=all"])
    if not ok or porcelain != "":
        raise _Refusal(evaluator.REPOSITORY_STATE_INVALID, "working tree not clean")
    return head


def _bind_sources(repository_root: str) -> Dict[str, Dict[str, str]]:
    identities: Dict[str, Dict[str, str]] = {}
    brainvision_dir = os.path.realpath(_under_root(repository_root, "research/brainvision"))
    for role, relative in SOURCE_RELATIVE_PATHS.items():
        absolute = _under_root(repository_root, relative)
        if not _is_regular_nonsymlink_file(absolute):
            raise _Refusal(evaluator.SOURCE_IDENTITY_FAILURE, "not a regular file: " + role)
        resolved = os.path.realpath(absolute)
        if os.path.commonpath([brainvision_dir, resolved]) != brainvision_dir:
            raise _Refusal(evaluator.SOURCE_IDENTITY_FAILURE, "escapes research/brainvision: " + role)
        ok, blob_id = _git(repository_root, ["rev-parse", "--verify", "HEAD:" + relative])
        if not ok or not _is_full_lower_hex_40(blob_id):
            raise _Refusal(evaluator.SOURCE_IDENTITY_FAILURE, "not committed: " + role)
        committed = _git_blob_bytes(repository_root, blob_id)
        if committed is None:
            raise _Refusal(evaluator.SOURCE_IDENTITY_FAILURE, "blob unreadable: " + role)
        with open(resolved, "rb") as handle:
            local_bytes = handle.read()
        if local_bytes != committed:
            raise _Refusal(evaluator.SOURCE_IDENTITY_FAILURE, "bytes differ from commit: " + role)
        identities[role] = {"path": relative, "blob_id": blob_id, "raw_byte_sha256": file_sha256(committed)}
    return identities


def _load_and_validate_input(repository_root: str) -> Tuple[Dict[str, object], str, List[Dict[str, object]]]:
    input_path = os.path.join(_under_root(repository_root, INPUT_RELATIVE_DIR), INPUT_FILENAME)
    if not _is_regular_nonsymlink_file(input_path):
        raise _Refusal(evaluator.INPUT_FILE_MISSING, "input not a regular non-symlink file")
    with open(input_path, "rb") as handle:
        loaded_bytes = handle.read()
    if file_sha256(loaded_bytes) != frozen.freeze_result_whole_file_sha256:
        raise _Refusal(evaluator.INPUT_WHOLE_FILE_HASH_MISMATCH, "")
    try:
        parsed = json.loads(loaded_bytes.decode("utf-8"))
    except ValueError as error:
        raise _Refusal(evaluator.INPUT_JSON_INVALID, str(error))
    try:
        extracted = evaluator.validate_frozen_evidence(parsed)
    except evaluator.EvidenceError as error:
        raise _Refusal(error.code, error.detail)
    try:
        evaluator.reverify_witnesses(extracted["pairs"], extracted["family_certificate_envelope"])
    except evaluator.EvidenceError as error:
        raise _Refusal(error.code, error.detail)
    return parsed, file_sha256(loaded_bytes), extracted["pairs"]


# --------------------------------------------------------------------------- environment fingerprint
def environment_fingerprint() -> Dict[str, object]:
    executable_sha = _stable_file_sha(sys.executable)
    return {
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "python_compiler": platform.python_compiler(),
        "numpy_version": str(np.__version__),
        "platform_system": platform.system(), "platform_release": platform.release(),
        "platform_machine": platform.machine(), "byte_order": sys.byteorder,
        "python_executable_sha256": executable_sha,
        "numpy_build_configuration_sha256": _stable_text_sha(_safe_numpy_build_info()),
        "numpy_runtime_information_sha256": _stable_text_sha(str(np.__version__))}


def _stable_file_sha(path: str) -> str:
    try:
        with open(path, "rb") as handle:
            return file_sha256(handle.read())
    except OSError:
        return "UNAVAILABLE"


def _stable_text_sha(text: str) -> str:
    return file_sha256(text.encode("utf-8"))


def _safe_numpy_build_info() -> str:
    try:
        return json.dumps(np.show_config(mode="dicts"), sort_keys=True)  # type: ignore[call-arg]
    except Exception:
        return "UNAVAILABLE"


# --------------------------------------------------------------------------- production pass provider
def _production_pass() -> Dict[str, object]:
    """Build the full production feature cache (sole descriptor contact) and evaluate it purely."""
    cache = evaluator.build_production_feature_cache()
    return evaluator.evaluate_from_feature_cache(cache)


# --------------------------------------------------------------------------- result / summary construction
def _evaluation_configuration() -> Dict[str, object]:
    return {
        "schema_name": SCHEMA_NAME, "schema_version": SCHEMA_VERSION,
        "runner_name": RUNNER_NAME, "runner_version": RUNNER_VERSION,
        "N": evaluator.N, "feature_count": evaluator.FEATURE_COUNT,
        "descriptor_variants": list(evaluator.VARIANTS), "kappa_by_variant": dict(evaluator.KAPPA_BY_VARIANT),
        "epsilon": evaluator.EPSILON, "near_epsilon_threshold": evaluator.NEAR_EPSILON_THRESHOLD,
        "comparison_tolerance": evaluator.COMPARISON_TOLERANCE,
        "identity_controls_per_pass": evaluator.IDENTITY_CONTROLS_PER_PASS,
        "nonidentity_responses_per_pass": evaluator.NONIDENTITY_RESPONSES_PER_PASS,
        "cross_responses_per_pass": evaluator.CROSS_RESPONSES_PER_PASS,
        "descriptor_calls_per_pass": evaluator.DESCRIPTOR_CALLS_PER_PASS,
        "failure_namespace": evaluator.FAILURE_NAMESPACE, "failure_version": evaluator.FAILURE_VERSION}


def _frozen_evidence_identity() -> Dict[str, object]:
    return {
        "accepted_candidate_indices": list(frozen.accepted_candidate_indices),
        "execution_commit_identity": frozen.execution_commit_identity,
        "freeze_result_payload_sha256": frozen.freeze_result_payload_sha256,
        "freeze_result_whole_file_sha256": frozen.freeze_result_whole_file_sha256,
        "family_manifest_sha256": frozen.family_manifest_sha256,
        "family_verifier_certificate_sha256": frozen.family_verifier_certificate_sha256,
        "candidate_stream_payload_sha256": frozen.candidate_stream_payload_sha256,
        "pair_certificate_sha256": list(frozen.pair_certificate_sha256)}


def _build_result_payload(head: str, source_identities: Dict[str, Dict[str, str]],
                          pass1: Dict[str, object], pass2: Dict[str, object]) -> Dict[str, object]:
    pass1_bytes = evaluator.canonical_pass_bytes(pass1["evaluation_pass"])
    pass2_bytes = evaluator.canonical_pass_bytes(pass2["evaluation_pass"])
    byte_identical = pass1_bytes == pass2_bytes
    replay_record = {"run1_sha256": file_sha256(pass1_bytes), "run2_sha256": file_sha256(pass2_bytes),
                     "byte_identical": bool(byte_identical)}

    validity = dict(pass1["validity"])
    validity["replay_byte_identical"] = bool(byte_identical)
    valid_run = bool(pass1["valid_run"] and byte_identical)

    if not byte_identical:
        family_verdict = evaluator.INVALID_FAMILY_EVALUATION
        failure_record = {"failure_code": evaluator.REPLAY_MISMATCH, "stage": "two_pass_replay"}
    else:
        family_verdict = pass1["family_verdict"] if valid_run else evaluator.INVALID_FAMILY_EVALUATION
        failure_record = pass1["failure_record"]

    configuration = _evaluation_configuration()
    payload = {
        "schema_name": SCHEMA_NAME, "schema_version": SCHEMA_VERSION,
        "authoritative_operation": bool(valid_run),
        "execution_commit_identity": head,
        "frozen_evidence_identity": _frozen_evidence_identity(),
        "source_identities": source_identities,
        "environment_fingerprint": environment_fingerprint(),
        "evaluation_configuration": configuration,
        "evaluation_configuration_sha256": cjson.payload_sha256(configuration),
        "evaluation_pass": pass1["evaluation_pass"],
        "evaluation_pass_sha256": file_sha256(pass1_bytes),
        "replay_record": replay_record,
        "validity": validity,
        "family_verdict": family_verdict,
        "failure_record": failure_record,
        "authority": {
            "authoritative_operation": bool(valid_run),
            "psitrs_frozen_family_contact": True,
            "scientific_inference_authorized": False,
            "production_integration_authorized": False}}
    return payload


def _summary_text(payload: Dict[str, object], result_file_sha256: str) -> str:
    replay = payload.get("replay_record", {})
    family = payload.get("evaluation_pass", {}).get("family_summary", {})
    lines: List[str] = []
    lines.append("TORMENT Brainvision algebraic N=64 PRIMARY_V0_1 frozen-family F3 evaluation summary v%s"
                 % RUNNER_VERSION)
    lines.append("governing specification = %s" % GOVERNING_SPEC)
    lines.append("operator convenience only; not canonical evaluation evidence")
    lines.append("")
    lines.append("execution_commit_identity = %s" % payload.get("execution_commit_identity"))
    lines.append("freeze_result_payload_sha256 = %s" % frozen.freeze_result_payload_sha256)
    lines.append("family_manifest_sha256 = %s" % frozen.family_manifest_sha256)
    lines.append("family_verifier_certificate_sha256 = %s" % frozen.family_verifier_certificate_sha256)
    lines.append("")
    call_record = payload.get("evaluation_pass", {}).get("descriptor_call_record", {})
    lines.append("descriptor_calls_completed_pass = %s" % call_record.get("completed_descriptor_calls"))
    lines.append("run1_sha256 = %s" % replay.get("run1_sha256"))
    lines.append("run2_sha256 = %s" % replay.get("run2_sha256"))
    lines.append("replay_byte_identical = %s" % replay.get("byte_identical"))
    lines.append("")
    lines.append("pair order = [478, 479, 480]")
    for verdict in family.get("pair_verdicts", []):
        lines.append("  candidate %s primary_pass = %s flags = %s"
                     % (verdict.get("candidate_generation_index"), verdict.get("primary_pass"),
                        ",".join(verdict.get("pair_verdict_flags", []))))
    for pair in payload.get("evaluation_pass", {}).get("pairs", []):
        gates = pair.get("gates", {})
        margins = pair.get("margins", {})
        lines.append("  candidate %s gates: full_dual_orbit_extreme=%s k0_not_extreme=%s recursive_positive=%s"
                     % (pair.get("candidate_generation_index"), gates.get("full_dual_orbit_extreme"),
                        gates.get("k0_not_extreme_against_either_member"),
                        gates.get("recursive_positive_all_starts")))
        lines.append("    margins: full_vs_A=%s full_vs_B=%s k0_vs_A=%s k0_vs_B=%s min_recursive=%s"
                     % (margins.get("full_margin_vs_A"), margins.get("full_margin_vs_B"),
                        margins.get("k0_margin_vs_A"), margins.get("k0_margin_vs_B"),
                        margins.get("minimum_recursive_difference")))
    lines.append("")
    lines.append("strong_pass_count = %s" % family.get("strong_pass_count"))
    lines.append("family_verdict = %s" % payload.get("family_verdict"))
    lines.append("valid_run = %s" % all(bool(v) for v in payload.get("validity", {}).values()))
    failure = payload.get("failure_record")
    if isinstance(failure, dict):
        lines.append("failure_code = %s" % failure.get("failure_code"))
        lines.append("failure_stage = %s" % failure.get("stage"))
    else:
        lines.append("failure_code = %s" % ABSENT)
    lines.append("result_whole_file_sha256 = %s" % result_file_sha256)
    lines.append("planned artifact set = result+summary")
    lines.append("publication protocol = staging-to-final atomic rename")
    lines.append("")
    lines.append("freezer invoked = False")
    lines.append("generator invoked = False")
    lines.append("old N64 evaluation invoked = False")
    lines.append("scientific interpretation performed = False")
    lines.append("production integration performed = False")
    return LF.join(lines) + LF


# --------------------------------------------------------------------------- the operation
def run_operation(repository_root: Optional[str] = None, results_root: Optional[str] = None,
                  extra_arguments: Optional[List[str]] = None, gate_value: object = "__ENV__",
                  pass_provider: Optional[Callable[[], Dict[str, object]]] = None,
                  stdout=None, stderr=None) -> int:
    out = stdout if stdout is not None else sys.stdout
    err = stderr if stderr is not None else sys.stderr

    if extra_arguments:
        _safe_write(err, "%s: takes no arguments; pre-contact refusal\n" % RUNNER_NAME)
        return EXIT_REFUSED

    is_production = repository_root is None
    root = os.path.realpath(repository_root) if repository_root is not None else _default_repository_root()
    results = results_root if results_root is not None else _under_root(root, RESULTS_RELATIVE_DIR)
    final_path = os.path.join(results, FINAL_DIRECTORY_NAME)
    staging_path = os.path.join(results, STAGING_DIRECTORY_NAME)
    gate = os.environ.get(EVALUATION_AUTHORIZATION_ENV) if gate_value == "__ENV__" else gate_value

    # ---- pre-contact refusals (exit 2); no descriptor contact, no staging, no output ----
    try:
        if gate != EVALUATION_AUTHORIZATION_VALUE:
            raise _Refusal(evaluator.EVALUATION_NOT_AUTHORIZED, "gate closed")
        if os.path.exists(final_path):
            raise _Refusal(evaluator.OUTPUT_PATH_EXISTS, "final directory exists")
        if os.path.exists(staging_path):
            raise _Refusal(evaluator.OUTPUT_PATH_EXISTS, "staging directory exists")
        head = _check_repository(root, is_production)
        source_identities = _bind_sources(root)
        _load_and_validate_input(root)
    except _Refusal as refusal:
        _safe_write(err, "%s: pre-contact refusal %s %s\n" % (RUNNER_NAME, refusal.code, refusal.detail))
        return EXIT_REFUSED

    # ---- staging reservation, then two fresh complete passes (descriptor contact happens here) ----
    try:
        os.makedirs(staging_path)
    except OSError:
        _safe_write(err, "%s: staging reservation failed (path appeared)\n" % RUNNER_NAME)
        return EXIT_REFUSED

    provider = pass_provider if pass_provider is not None else _production_pass
    try:
        pass1 = provider()
        pass2 = provider()
    except Exception as error:  # noqa: BLE001 - contain any evaluation exception (post-contact)
        _safe_write(err, "%s: %s %r; staging retained\n" % (RUNNER_NAME, evaluator.DESCRIPTOR_CALL_FAILED, error))
        return EXIT_FAILURE

    try:
        payload = _build_result_payload(head, source_identities, pass1, pass2)
        result_bytes = cjson.canonical_json_bytes(cjson.envelope("family_evaluation_result", payload))
    except (ValueError, TypeError) as error:
        _safe_write(err, "%s: %s %r; staging retained\n"
                    % (RUNNER_NAME, evaluator.CANONICAL_SERIALIZATION_FAILURE, error))
        return EXIT_FAILURE

    result_file_sha256 = file_sha256(result_bytes)
    summary_text = _summary_text(payload, result_file_sha256)

    try:
        _write_exclusive(os.path.join(staging_path, RESULT_FILENAME), result_bytes)
        _write_exclusive(os.path.join(staging_path, SUMMARY_FILENAME), summary_text.encode("utf-8"))
    except OSError as error:
        _safe_write(err, "%s: %s %r; staging retained\n" % (RUNNER_NAME, evaluator.PUBLICATION_FAILURE, error))
        return EXIT_FAILURE

    if sorted(os.listdir(staging_path)) != sorted([RESULT_FILENAME, SUMMARY_FILENAME]):
        _safe_write(err, "%s: %s staged set mismatch; staging retained\n"
                    % (RUNNER_NAME, evaluator.PUBLICATION_FAILURE))
        return EXIT_FAILURE

    try:
        os.rename(staging_path, final_path)
    except OSError as error:
        _safe_write(err, "%s: %s %r; complete staging retained\n"
                    % (RUNNER_NAME, evaluator.PUBLICATION_FAILURE, error))
        return EXIT_FAILURE

    try:
        out.write(summary_text)
    except Exception as error:  # noqa: BLE001
        _safe_write(err, "%s: %s %r; final evidence intact, not rolled back\n"
                    % (RUNNER_NAME, evaluator.STDOUT_FAILURE, error))
        return EXIT_FAILURE

    return EXIT_PUBLISHED


# --------------------------------------------------------------------------- entry point
def main(argv: Optional[List[str]] = None) -> int:
    arguments = (argv if argv is not None else sys.argv)[1:]
    if arguments:
        sys.stderr.write("%s: takes no arguments; invoke exactly:\n" % RUNNER_NAME)
        sys.stderr.write("  python research\\brainvision\\%s.py\n" % RUNNER_NAME)
        return EXIT_REFUSED
    return run_operation()


if __name__ == "__main__":
    sys.exit(main())

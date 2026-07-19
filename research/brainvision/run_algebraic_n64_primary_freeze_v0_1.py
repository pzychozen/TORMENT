"""TORMENT Brainvision algebraic N=64 PRIMARY_V0_1 freezer runner v0.1 (offline; quarantined; descriptive-only).

Narrow operator runner implementing docs/TORMENT_BRAINVISION_ALGEBRAIC_N64_PRIMARY_V0_1_FREEZER_RUNNER_
IMPLEMENTATION_SPECIFICATION_v0.1.md. It binds the exact repository / source / input state, then makes exactly
one call to freezer.freeze_with_replay(...), publishes the returned object safely, and distinguishes runner
success from mathematical success. It performs NO witness mathematics: it never calls verify_candidate,
verify_family, member_certificate, or triple_array, never calls freezer.freeze(...), and performs no outer
replay. Its only permitted verifier uses are validate_stream_envelope and validate_local_configuration, for
pre-contact refusal only.

Operator interface (complete):

    python research\\brainvision\\run_algebraic_n64_primary_freeze_v0_1.py

There is no CLI argument, environment override, path/commit/prefix/selector/budget/overwrite option of any kind.
The internal run_operation(...) accepts test-only repository/result roots and diagnostic streams that are
unreachable from the command line.

Exit contract (runner-level only; never inserted into any canonical freezer artifact):

    0  complete two-file publication with either family_frozen=True or a valid mathematical negative
    1  runner failure, malformed / execution-invalid / unserializable result, I/O or publication failure,
       or post-publication stdout failure
    2  pre-contact refusal (argument, path, repository, source identity, cleanliness, or input identity)

FORMAL HOLD and Mode 0 remain active. A successful publication establishes only that the committed freezer ran
deterministically over the exact retained stream and returned a canonical result. It establishes no witness
validity, family validity, perception, temporal order, production vision, or scientific meaning.
"""
from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
import sys
from typing import Dict, List, Optional, Tuple

# Committed serializer, verifier, and freezer. Nothing mathematical is reimplemented here.
import witness_canonical_json_v0_1 as cjson
import witness_family_verifier_v0_1 as verifier
import witness_family_freeze_v0_1 as freezer

RUNNER_NAME = "run_algebraic_n64_primary_freeze_v0_1"
RUNNER_VERSION = "0.1"
GOVERNING_SPEC = "docs/TORMENT_BRAINVISION_ALGEBRAIC_N64_PRIMARY_V0_1_FREEZER_RUNNER_IMPLEMENTATION_SPECIFICATION_v0.1.md"

RUNNER_RELATIVE_PATH = "research/brainvision/run_algebraic_n64_primary_freeze_v0_1.py"
EXPECTED_BRANCH = "main"

# --- frozen source paths (relative to the resolved repository root) and their frozen Git blob identities ---
SOURCE_RELATIVE_PATHS = {
    "verifier": "research/brainvision/witness_family_verifier_v0_1.py",
    "serializer": "research/brainvision/witness_canonical_json_v0_1.py",
    "freeze": "research/brainvision/witness_family_freeze_v0_1.py",
}
FROZEN_SOURCE_BLOB_IDS = {
    "verifier": "db1e1fa606bdbf17fda62cd998aeb2a29d47d59a",
    "serializer": "6eb382b314325033443fc7331cae5050ee6e6ed2",
    "freeze": "cf4ea57890fbbbdf9593879cf648b84c6c68d9b0",
}

# --- frozen input identity (candidate stream) ---
INPUT_RELATIVE_DIR = "research/brainvision/results/algebraic_n64_primary_v0_1"
INPUT_FILENAME = "algebraic_n64_primary_v0_1_candidate_stream.json"
INPUT_EXPECTED_SIZE = 6_421_010
INPUT_WHOLE_FILE_SHA256 = "00a816364ddcfc9d06dc8ce1225f58bca013e96a8914ff1eb665004b39ed949b"
INPUT_PAYLOAD_SHA256 = "70763a2ebbf7ea71267553debee2bf79c2ed3b7b0c016d9a903161074e7bf8c5"

# --- frozen structural identity of the candidate stream payload ---
STREAM_SCHEMA_NAME = "brainvision_descriptor_blind_candidate_stream"
STREAM_SCHEMA_VERSION = "0.1"
STREAM_VERIFICATION_MODE = "PRIMARY_CANDIDATE_N64"
STREAM_N = 64
STREAM_CANDIDATE_COUNT = 20000
STREAM_TERMINAL_STATUS = "budget_exhausted"

# --- frozen freeze-result identity ---
FREEZE_RESULT_SCHEMA_NAME = "brainvision_witness_freeze_result"
FREEZE_RESULT_SCHEMA_VERSION = "0.1"
RESOURCE_POLICY_STATUS = "UNBOUNDED_BY_V0_1_SPECIFICATION"
K_FAMILY = 3

# --- output layout ---
RESULTS_RELATIVE_DIR = "research/brainvision/results"
FINAL_DIRECTORY_NAME = "algebraic_n64_primary_v0_1_freeze_v0_1"
STAGING_DIRECTORY_NAME = ".algebraic_n64_primary_v0_1_freeze_v0_1.staging"
RESULT_FILENAME = "algebraic_n64_primary_v0_1_freeze_result.json"
SUMMARY_FILENAME = "algebraic_n64_primary_v0_1_freeze_summary.txt"

# --- execution-invalid freezer failure codes (exit 1); anything else non-frozen is a valid negative (exit 0) ---
EXECUTION_INVALID_CODES = frozenset({
    "CANDIDATE_STREAM_INVALID", "CANDIDATE_STREAM_HASH_MISMATCH", "CANDIDATE_N_MODE_INVALID",
    "SERIALIZATION_FAILURE", "VERIFIER_CONFIGURATION_INVALID", "FORBIDDEN_IMPORT_DETECTED",
    "HASH_IDENTITY_FAILURE", "VERIFIER_INTERNAL_DISAGREEMENT", "VERIFIER_REGRESSION_FAILURE",
    "REPLAY_MISMATCH",
})

# runner-level diagnostic codes (never inserted into any canonical freezer artifact)
FREEZER_CALL_EXCEPTION = "FREEZER_CALL_EXCEPTION"
RESULT_NOT_SERIALIZABLE = "RESULT_NOT_SERIALIZABLE"
RESULT_RUNNER_INVALID = "RESULT_RUNNER_INVALID"

EXIT_PUBLISHED = 0
EXIT_FAILURE = 1
EXIT_REFUSED = 2

ABSENT = "absent"
LF = "\n"

_GIT_TIMEOUT_SECONDS = 30


class _Refusal(Exception):
    """Pre-contact refusal -> exit code 2. Raised only before the freezer is contacted."""

    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(code)
        self.code = code
        self.detail = detail


# --------------------------------------------------------------------------- 1. path derivation
def _default_repository_root() -> str:
    """Repository root derived from this file's own real path: research/brainvision/<file> -> three up."""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))


def _default_results_root(repository_root: str) -> str:
    return os.path.join(repository_root, "research", "brainvision", "results")


def _under_root(repository_root: str, relative_path: str) -> str:
    return os.path.join(repository_root, *relative_path.split("/"))


# --------------------------------------------------------------------------- 2. small helpers
def _is_strict_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_strict_bool(value: object) -> bool:
    return isinstance(value, bool)


def _mapping(value: object) -> Optional[Dict[str, object]]:
    return value if isinstance(value, dict) else None


def file_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _is_regular_nonsymlink_file(path: str) -> bool:
    if os.path.islink(path):
        return False
    try:
        mode = os.lstat(path).st_mode
    except OSError:
        return False
    return stat.S_ISREG(mode)


# --------------------------------------------------------------------------- 3. git (fixed-argument, non-shell)
def _git(repository_root: str, arguments: List[str]) -> Tuple[bool, str]:
    """Run a fixed-argument, read-only Git command. Returns (ok, stripped_stdout). Never uses a shell."""
    try:
        completed = subprocess.run(
            ["git", "-C", repository_root] + arguments,
            capture_output=True, text=True, shell=False, timeout=_GIT_TIMEOUT_SECONDS)
    except (OSError, subprocess.SubprocessError):
        return False, ""
    if completed.returncode != 0:
        return False, ""
    return True, completed.stdout.strip()


def _git_blob_bytes(repository_root: str, blob_id: str) -> Optional[bytes]:
    """Raw committed bytes of a blob. Non-shell, read-only."""
    try:
        completed = subprocess.run(
            ["git", "-C", repository_root, "cat-file", "blob", blob_id],
            capture_output=True, shell=False, timeout=_GIT_TIMEOUT_SECONDS)
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout


# --------------------------------------------------------------------------- 4. repository pre-contact checks
def _check_repository(repository_root: str, is_production: bool) -> str:
    """Establish repository ownership, branch, HEAD, origin/main == HEAD, clean tree. Returns full HEAD commit."""
    resolved_root = os.path.realpath(repository_root)
    if not os.path.isdir(resolved_root):
        raise _Refusal("REPOSITORY_ROOT_INVALID", "root is not a directory")

    ok, toplevel = _git(resolved_root, ["rev-parse", "--show-toplevel"])
    if not ok or os.path.realpath(toplevel) != resolved_root:
        raise _Refusal("REPOSITORY_ROOT_MISMATCH", "git toplevel != derived root")

    # runner path ownership: the runner must live at its exact expected repository path
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


def _is_full_lower_hex_40(value: object) -> bool:
    return isinstance(value, str) and len(value) == 40 and all(c in "0123456789abcdef" for c in value)


# --------------------------------------------------------------------------- 5. source binding
def _bind_sources(repository_root: str) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Bind verifier/serializer/freezer to frozen blob ids and local bytes. Returns (source_paths, sha256s)."""
    source_paths: Dict[str, str] = {}
    expected_source_hashes: Dict[str, str] = {}
    brainvision_dir = os.path.realpath(_under_root(repository_root, "research/brainvision"))

    for role, relative in SOURCE_RELATIVE_PATHS.items():
        absolute = _under_root(repository_root, relative)
        if not _is_regular_nonsymlink_file(absolute):
            raise _Refusal("SOURCE_PATH_INVALID", "not a regular file: " + role)
        resolved = os.path.realpath(absolute)
        if os.path.commonpath([brainvision_dir, resolved]) != brainvision_dir:
            raise _Refusal("SOURCE_PATH_INVALID", "escapes research/brainvision: " + role)

        ok, blob_id = _git(repository_root, ["rev-parse", "--verify", "HEAD:" + relative])
        if not ok or blob_id != FROZEN_SOURCE_BLOB_IDS[role]:
            raise _Refusal("SOURCE_BLOB_IDENTITY_MISMATCH", role)

        ok, object_type = _git(repository_root, ["cat-file", "-t", blob_id])
        if not ok or object_type != "blob":
            raise _Refusal("SOURCE_BLOB_IDENTITY_MISMATCH", "not a blob: " + role)

        committed_bytes = _git_blob_bytes(repository_root, blob_id)
        if committed_bytes is None:
            raise _Refusal("SOURCE_BLOB_UNREADABLE", role)
        with open(resolved, "rb") as handle:
            local_bytes = handle.read()
        if local_bytes != committed_bytes:
            raise _Refusal("SOURCE_BYTES_DIFFER_FROM_COMMIT", role)

        source_paths[role] = resolved
        expected_source_hashes[role] = file_sha256(committed_bytes)

    return source_paths, expected_source_hashes


# --------------------------------------------------------------------------- 6. verifier configuration precheck
def _precheck_local_configuration(repository_root: str, source_paths: Dict[str, str],
                                  expected_source_hashes: Dict[str, str]) -> None:
    """Pre-contact configuration + source-ownership validation only. Evaluates no candidate."""
    config = verifier.validate_local_configuration(
        repository_root=repository_root, source_paths=source_paths,
        expected_source_hashes=expected_source_hashes)
    if not config.get("valid"):
        raise _Refusal("LOCAL_CONFIGURATION_INVALID", str(config.get("code")))


# --------------------------------------------------------------------------- 7. input loading
def _reject_duplicate_keys(pairs: List[Tuple[str, object]]) -> Dict[str, object]:
    keys = [key for key, _value in pairs]
    if len(set(keys)) != len(keys):
        raise ValueError("duplicate object keys")
    return dict(pairs)


def _reject_nonfinite(_token: str) -> object:
    raise ValueError("nonfinite JSON constant")


def _load_input(repository_root: str) -> Dict[str, object]:
    """Strict frozen-identity input loading. Any failure raises _Refusal (exit 2). Returns the stream envelope."""
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
    return parsed


def _require_frozen_structure(stream: Dict[str, object]) -> None:
    checks = (
        ("schema_name", STREAM_SCHEMA_NAME), ("schema_version", STREAM_SCHEMA_VERSION),
        ("verification_mode", STREAM_VERIFICATION_MODE), ("N", STREAM_N),
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


# --------------------------------------------------------------------------- 8. returned-result classification
def _local_hash_ok(payload: object, supplied_hash: object) -> bool:
    """Local canonical envelope-hash validation. The runner never calls verifier.verify_supplied_hash: its
    verifier surface is limited to validate_stream_envelope, validate_local_configuration, and constants."""
    if not cjson.is_lower_hex_64(supplied_hash):
        return False
    try:
        return cjson.payload_sha256(payload) == supplied_hash
    except (ValueError, TypeError):
        return False


def _classify_result(result_envelope: object, resolved_head_commit: str,
                     expected_source_hashes: Dict[str, str],
                     source_paths: Dict[str, str]) -> Tuple[str, List[str]]:
    """Classify a canonically serializable freeze-result envelope. Returns (classification, runner_failures).

    classification in {POSITIVE, VALID_NEGATIVE, EXECUTION_INVALID, RUNNER_INVALID}.
    POSITIVE / VALID_NEGATIVE -> exit 0; EXECUTION_INVALID / RUNNER_INVALID -> exit 1. All are published.
    """
    failures: List[str] = []

    def invalid(reason: str) -> Tuple[str, List[str]]:
        failures.append(reason)
        return "RUNNER_INVALID", failures

    envelope = _mapping(result_envelope)
    if envelope is None or "freeze_result" not in envelope or "freeze_result_sha256" not in envelope:
        return invalid("ENVELOPE_SHAPE_INVALID")
    payload = _mapping(envelope["freeze_result"])
    if payload is None:
        return invalid("PAYLOAD_NOT_A_MAPPING")
    if not _local_hash_ok(payload, envelope["freeze_result_sha256"]):
        return invalid("RESULT_PAYLOAD_HASH_MISMATCH")

    required_scalars = (
        ("schema_name", FREEZE_RESULT_SCHEMA_NAME), ("schema_version", FREEZE_RESULT_SCHEMA_VERSION),
        ("verification_mode", STREAM_VERIFICATION_MODE), ("N", STREAM_N),
        ("candidate_stream_sha256", INPUT_PAYLOAD_SHA256), ("candidate_count", STREAM_CANDIDATE_COUNT),
        ("terminal_stream_status", STREAM_TERMINAL_STATUS), ("authoritative_operation", True),
        ("resource_policy_status", RESOURCE_POLICY_STATUS),
    )
    for field, expected in required_scalars:
        if payload.get(field) != expected:
            failures.append("FIELD_MISMATCH:" + field)

    replay_record = _mapping(payload.get("replay_record"))
    if replay_record is None or not _is_strict_bool(replay_record.get("byte_identical")):
        failures.append("REPLAY_RECORD_INVALID")
    if not _is_strict_bool(payload.get("family_frozen")):
        failures.append("FAMILY_FROZEN_NOT_BOOL")

    # bind the same source paths and source SHA-256 identities established before contact
    identities = _mapping(payload.get("local_source_identities"))
    if identities is None:
        failures.append("SOURCE_IDENTITIES_ABSENT")
    else:
        for role, expected_hash in expected_source_hashes.items():
            if identities.get(role + "_source_sha256") != expected_hash:
                failures.append("SOURCE_SHA256_UNBOUND:" + role)
            if identities.get(role + "_source_path") != SOURCE_RELATIVE_PATHS[role]:
                failures.append("SOURCE_PATH_UNBOUND:" + role)

    if failures:
        return "RUNNER_INVALID", failures

    family_frozen = payload.get("family_frozen")
    failure_record = _mapping(payload.get("failure_record"))

    if family_frozen is True:
        if replay_record.get("byte_identical") is not True:
            failures.append("POSITIVE_REPLAY_NOT_IDENTICAL")
        if failure_record is not None:
            failures.append("POSITIVE_WITH_FAILURE_RECORD")
        # manifest envelope must be structurally exact and locally hash-consistent
        manifest = _mapping(payload.get("family_manifest"))
        if manifest is None or set(manifest.keys()) != {"family_manifest", "family_manifest_sha256"}:
            failures.append("POSITIVE_MANIFEST_SHAPE_INVALID")
        else:
            manifest_payload = _mapping(manifest["family_manifest"])
            manifest_hash = manifest["family_manifest_sha256"]
            if manifest_payload is None:
                failures.append("POSITIVE_MANIFEST_PAYLOAD_NOT_MAPPING")
                if not _local_hash_ok(manifest["family_manifest"], manifest_hash):
                    failures.append("POSITIVE_MANIFEST_HASH_INVALID")
            elif not _local_hash_ok(manifest_payload, manifest_hash):
                failures.append("POSITIVE_MANIFEST_HASH_INVALID")
            else:
                if manifest_payload.get("repository_commit_identity") != resolved_head_commit:
                    failures.append("POSITIVE_MANIFEST_COMMIT_MISMATCH")
                if manifest_payload.get("candidate_stream_sha256") != INPUT_PAYLOAD_SHA256:
                    failures.append("POSITIVE_MANIFEST_STREAM_MISMATCH")
        accepted = payload.get("accepted_candidate_indices")
        certificates = payload.get("accepted_pair_certificate_envelopes")
        if not isinstance(accepted, list) or len(accepted) != K_FAMILY:
            failures.append("POSITIVE_ACCEPTED_INDEX_COUNT")
        if not isinstance(certificates, list) or len(certificates) != K_FAMILY:
            failures.append("POSITIVE_ACCEPTED_CERTIFICATE_COUNT")
        if failures:
            return "RUNNER_INVALID", failures
        return "POSITIVE", failures

    # family_frozen is False: full structural validation before any negative classification.
    # A false result is NEVER a valid negative merely because failure_record is a mapping.
    if payload.get("family_manifest") is not None:
        failures.append("NEGATIVE_MANIFEST_NOT_NULL")
    if failure_record is None:
        failures.append("NEGATIVE_FAILURE_RECORD_NOT_MAPPING")
    else:
        failure_code = failure_record.get("failure_code")
        stage = failure_record.get("stage")
        ordered = failure_record.get("ordered_failure_codes")
        if not isinstance(failure_code, str) or not failure_code:
            failures.append("NEGATIVE_FAILURE_CODE_INVALID")
        if not isinstance(stage, str) or not stage:
            failures.append("NEGATIVE_STAGE_INVALID")
        if not isinstance(ordered, list) or not all(isinstance(code, str) for code in ordered):
            failures.append("NEGATIVE_ORDERED_CODES_INVALID")
        elif isinstance(failure_code, str) and failure_code not in ordered:
            failures.append("NEGATIVE_FAILURE_CODE_NOT_IN_ORDERED")
    if replay_record is not None and replay_record.get("byte_identical") is not True:
        failures.append("NEGATIVE_REPLAY_NOT_IDENTICAL")
    if failures:
        return "RUNNER_INVALID", failures

    failure_code = failure_record.get("failure_code")
    if failure_code in EXECUTION_INVALID_CODES:
        return "EXECUTION_INVALID", failures
    return "VALID_NEGATIVE", failures


# --------------------------------------------------------------------------- 9. summary
def _hex_or_absent(value: object) -> str:
    return value if isinstance(value, str) and cjson.is_lower_hex_64(value) else ABSENT


def _build_summary(payload: Optional[Dict[str, object]], result_envelope: object,
                   resolved_head_commit: str, source_paths: Dict[str, str],
                   expected_source_hashes: Dict[str, str], input_path: str,
                   classification: str, exit_code: int, runner_failures: List[str],
                   result_file_hash: Optional[str], published: bool) -> str:
    lines: List[str] = []
    lines.append("TORMENT Brainvision algebraic N=64 PRIMARY_V0_1 freezer runner summary v%s" % RUNNER_VERSION)
    lines.append("governing specification = %s" % GOVERNING_SPEC)
    lines.append("operator convenience only; not canonical freezer evidence")
    lines.append("")
    lines.append("resolved_head_commit = %s" % resolved_head_commit)
    lines.append("repository_agreement = branch main, origin/main == HEAD, clean tree")
    lines.append("")
    lines.append("input_path = %s" % INPUT_RELATIVE_DIR + "/" + INPUT_FILENAME)
    lines.append("input_size = %d" % INPUT_EXPECTED_SIZE)
    lines.append("input_whole_file_sha256 = %s" % INPUT_WHOLE_FILE_SHA256)
    lines.append("input_payload_sha256 = %s" % INPUT_PAYLOAD_SHA256)
    lines.append("")
    lines.append("source paths and committed-byte SHA-256:")
    for role in ("verifier", "serializer", "freeze"):
        lines.append("  %s_source_path = %s" % (role, SOURCE_RELATIVE_PATHS[role]))
        lines.append("  %s_source_sha256 = %s" % (role, expected_source_hashes.get(role, ABSENT)))
        lines.append("  %s_source_blob_id = %s" % (role, FROZEN_SOURCE_BLOB_IDS[role]))
    lines.append("")

    envelope = _mapping(result_envelope)
    payload_hash = envelope.get("freeze_result_sha256") if envelope is not None else None
    lines.append("freeze_result payload hash (over payload bytes only) = %s" % _hex_or_absent(payload_hash))
    lines.append("freeze_result whole-file SHA-256 (over file bytes) = %s"
                 % (result_file_hash if result_file_hash is not None else ABSENT))
    lines.append("")

    if payload is not None:
        manifest = _mapping(payload.get("family_manifest"))
        manifest_hash = manifest.get("family_manifest_sha256") if manifest is not None else None
        replay = _mapping(payload.get("replay_record")) or {}
        failure = _mapping(payload.get("failure_record"))
        lines.append("family_manifest_sha256 = %s" % _hex_or_absent(manifest_hash))
        lines.append("candidate_decision_ledger_sha256 = %s"
                     % _hex_or_absent(payload.get("candidate_decision_ledger_sha256")))
        lines.append("replay byte_identical = %s" % replay.get("byte_identical"))
        lines.append("family_frozen = %s" % payload.get("family_frozen"))
        accepted = payload.get("accepted_candidate_indices")
        lines.append("accepted_candidate_indices = %s"
                     % (accepted if isinstance(accepted, list) else ABSENT))
        if failure is not None:
            lines.append("failure_code = %s" % failure.get("failure_code"))
            lines.append("failure_stage = %s" % failure.get("stage"))
        else:
            lines.append("failure_code = %s" % ABSENT)
            lines.append("failure_stage = %s" % ABSENT)
    else:
        lines.append("freeze_result payload = %s" % ABSENT)
    lines.append("")

    lines.append("classification = %s" % classification)
    lines.append("exit_code = %d" % exit_code)
    if runner_failures:
        for entry in runner_failures:
            lines.append("runner_validation_failure = %s" % entry)
    else:
        lines.append("runner_validation_failure = none")
    if classification == "VALID_NEGATIVE":
        lines.append("negative_scope = greedy non-backtracking first-fit scan did not freeze a family under "
                     "its exact semantics; this does not establish that no valid triple exists elsewhere in "
                     "the 20000-record stream or in the complete generator domain")
    lines.append("published_artifact_set = %s" % ("result+summary" if published else "none"))
    lines.append("")
    lines.append("freezer invoked = True")
    lines.append("outer replay performed = False")
    lines.append("PsiTRS invoked = False")
    lines.append("descriptors invoked = False")
    lines.append("scientific interpretation performed = False")
    return LF.join(lines) + LF


# --------------------------------------------------------------------------- 10. staging / publication
def _write_exclusive(path: str, data: bytes) -> None:
    """Exclusive binary create: raises FileExistsError if the file exists. No overwrite is ever possible."""
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as handle:  # fdopen takes ownership; the with-block closes it
        handle.write(data)


def _remove_empty_staging(staging_path: str) -> None:
    """Remove staging only when it holds no evidence bytes. Retained staging blocks future runs by design."""
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


# --------------------------------------------------------------------------- 11. the operation
def run_operation(repository_root: Optional[str] = None, results_root: Optional[str] = None,
                  extra_arguments: Optional[List[str]] = None, stdout=None, stderr=None) -> int:
    out = stdout if stdout is not None else sys.stdout
    err = stderr if stderr is not None else sys.stderr

    if extra_arguments:
        _safe_write(err, "%s: takes no arguments; pre-contact refusal\n" % RUNNER_NAME)
        return EXIT_REFUSED

    is_production = repository_root is None
    root = os.path.realpath(repository_root) if repository_root is not None else _default_repository_root()
    results = results_root if results_root is not None else _default_results_root(root)
    final_path = os.path.join(results, FINAL_DIRECTORY_NAME)
    staging_path = os.path.join(results, STAGING_DIRECTORY_NAME)

    # ---- pre-contact refusals (exit 2) ----
    try:
        if os.path.exists(final_path):
            raise _Refusal("FINAL_DIRECTORY_EXISTS", final_path)
        if os.path.exists(staging_path):
            raise _Refusal("STAGING_DIRECTORY_EXISTS", staging_path)
        resolved_head_commit = _check_repository(root, is_production)
        source_paths, expected_source_hashes = _bind_sources(root)
        _precheck_local_configuration(root, source_paths, expected_source_hashes)
        candidate_stream_envelope = _load_input(root)
    except _Refusal as refusal:
        _safe_write(err, "%s: pre-contact refusal %s %s\n" % (RUNNER_NAME, refusal.code, refusal.detail))
        return EXIT_REFUSED

    # ---- staging reservation (only after every pre-contact check passed) ----
    try:
        os.makedirs(staging_path)  # no exist_ok: a concurrently created staging path is a refusal
    except OSError:
        _safe_write(err, "%s: staging reservation failed (path appeared)\n" % RUNNER_NAME)
        return EXIT_REFUSED

    # ---- the sole authoritative freezer call ----
    try:
        result_envelope = freezer.freeze_with_replay(
            candidate_stream_envelope,
            repository_commit_identity=resolved_head_commit,
            source_paths=source_paths)
    except Exception as error:  # noqa: BLE001 - contain any freezer exception
        _safe_write(err, "%s: %s %r\n" % (RUNNER_NAME, FREEZER_CALL_EXCEPTION, error))
        _remove_empty_staging(staging_path)
        return EXIT_FAILURE

    # ---- returned-result validation: serializability is the first gate ----
    try:
        result_bytes = cjson.canonical_json_bytes(result_envelope)
    except (ValueError, TypeError) as error:
        _safe_write(err, "%s: %s %r\n" % (RUNNER_NAME, RESULT_NOT_SERIALIZABLE, error))
        # cannot publish canonical evidence; retain staging (no evidence bytes were written) and fail
        _remove_empty_staging(staging_path)
        return EXIT_FAILURE

    payload = _mapping(_mapping(result_envelope).get("freeze_result")) if _mapping(result_envelope) else None
    classification, runner_failures = _classify_result(
        result_envelope, resolved_head_commit, expected_source_hashes, source_paths)
    exit_code = EXIT_PUBLISHED if classification in ("POSITIVE", "VALID_NEGATIVE") else EXIT_FAILURE
    result_file_hash = file_sha256(result_bytes)

    summary_text = _build_summary(
        payload, result_envelope, resolved_head_commit, source_paths, expected_source_hashes,
        os.path.join(INPUT_RELATIVE_DIR, INPUT_FILENAME), classification, exit_code, runner_failures,
        result_file_hash, published=True)

    # ---- publish: write the exact two-file set into staging, then one atomic rename ----
    try:
        _write_exclusive(os.path.join(staging_path, RESULT_FILENAME), result_bytes)
        _write_exclusive(os.path.join(staging_path, SUMMARY_FILENAME), summary_text.encode("utf-8"))
    except OSError as error:
        _safe_write(err, "%s: artifact write failed %r; staging retained\n" % (RUNNER_NAME, error))
        return EXIT_FAILURE  # staging now holds evidence bytes -> retained, never auto-removed

    try:
        os.rename(staging_path, final_path)
    except OSError as error:
        _safe_write(err, "%s: publication rename failed %r; staging retained\n" % (RUNNER_NAME, error))
        return EXIT_FAILURE

    # ---- published: nothing below may roll back the final directory ----
    if runner_failures:
        _safe_write(err, "%s: %s %s\n" % (RUNNER_NAME, RESULT_RUNNER_INVALID, ", ".join(runner_failures)))
    elif classification == "EXECUTION_INVALID":
        code = payload.get("failure_record", {}).get("failure_code") if payload else None
        _safe_write(err, "%s: execution-invalid freezer result %s\n" % (RUNNER_NAME, code))

    try:
        out.write(summary_text)
    except Exception as error:  # noqa: BLE001
        _safe_write(err, "%s: stdout mirroring failed after publication: %r\n" % (RUNNER_NAME, error))
        _safe_write(err, "%s: the published artifact set is intact and was not rolled back\n" % RUNNER_NAME)
        return EXIT_FAILURE

    return exit_code


# --------------------------------------------------------------------------- 12. entry point
def main(argv: Optional[List[str]] = None) -> int:
    arguments = (argv if argv is not None else sys.argv)[1:]
    if arguments:
        sys.stderr.write("%s: takes no arguments; invoke exactly:\n" % RUNNER_NAME)
        sys.stderr.write("  python research\\brainvision\\%s.py\n" % RUNNER_NAME)
        return EXIT_REFUSED
    return run_operation()


if __name__ == "__main__":
    sys.exit(main())

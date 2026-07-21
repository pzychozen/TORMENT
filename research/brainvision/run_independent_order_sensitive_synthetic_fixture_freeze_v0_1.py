"""Authoritative independent order-sensitive synthetic-fixture freeze runner (v0.1).

This module is the S1C execution boundary. It conforms directly to the accepted
governing document
``docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_FIXTURE_FREEZE_RUNNER_IMPLEMENTATION_AUTHORIZATION_v0.1.md``,
including the revised Section 8A seven-field execution-authorization binding.

Import-time discipline: only the Python standard library is imported at module
load. The three accepted S1B project modules are imported *locally*, and only
after every early identity and path pre-contact check succeeds. All verifier,
generator, reducer, manifest, comparison, and finalization mathematics are used
from those accepted modules; none is reimplemented here.

Execution is not authorized by this file. Its presence is the execution boundary,
not the execution authority. The entry point at the bottom is never invoked by
the bounded tests, which drive the internal functions directly with injected
read-only Git responses, injected module namespaces, and finite hand-authored
seed streams. The real complete canonical iterator is never driven here.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

# --------------------------------------------------------------------------- #
# Frozen constants (from the accepted governing document)
# --------------------------------------------------------------------------- #

PYTHON_VERSION = "3.11.15"

AUTHORIZATION_DOCUMENT_PATH = (
    "docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_FIXTURE_FREEZE_"
    "EXECUTION_AUTHORIZATION_v0.1.md"
)

RUNNER_SOURCE_PATH = "research/brainvision/run_independent_order_sensitive_synthetic_fixture_freeze_v0_1.py"
RUNNER_TEST_SOURCE_PATH = (
    "research/brainvision/test_brainvision_run_independent_order_sensitive_synthetic_fixture_freeze_v0_1.py"
)
RUNNER_ARTIFACT_ID = "independent-order-sensitive-synthetic-fixture-freeze-runner-v0.1"
RUNNER_TEST_ARTIFACT_ID = "independent-order-sensitive-synthetic-fixture-freeze-runner-test-v0.1"

# Section 8A.2 frozen execution-envelope constants.
ENVELOPE_SCHEMA = (
    "torment-brainvision-independent-order-sensitive-synthetic-fixture-freeze-execution-envelope-v0.1"
)
ENVELOPE_VERSION = "0.1"
OPERATION_IDENTITY = "independent-order-sensitive-synthetic-fixture-freeze-v0.1"
AUTHORITATIVE_OPERATION = True

# Section 8A.4/8A.5 authorization-binding contract.
AUTHORIZATION_SCHEMA = (
    "torment-brainvision-independent-order-sensitive-synthetic-fixture-freeze-authorization-binding-v0.1"
)
AUTHORIZATION_VERSION = "0.1"
BINDING_BEGIN_MARKER = "BEGIN-SYNTHETIC-FIXTURE-FREEZE-AUTHORIZATION-BINDING-v0.1"
BINDING_END_MARKER = "END-SYNTHETIC-FIXTURE-FREEZE-AUTHORIZATION-BINDING-v0.1"
BINDING_FIELD_ORDER: Tuple[str, ...] = (
    "authorization_schema",
    "authorization_version",
    "runner_git_blob",
    "runner_raw_sha256",
    "runner_test_git_blob",
    "runner_test_raw_sha256",
    "configuration_sha256",
)
_BLOB_FIELDS = frozenset({"runner_git_blob", "runner_test_git_blob"})
_SHA256_FIELDS = frozenset({"runner_raw_sha256", "runner_test_raw_sha256", "configuration_sha256"})

# Section 3 frozen accepted S1B source identities.
S1B_SOURCE_IDENTITIES: Tuple[Dict[str, str], ...] = (
    {
        "artifact_role": "verifier",
        "source_path": "research/brainvision/independent_order_sensitive_synthetic_fixture_verifier_v0_1.py",
        "git_blob": "74e25002db4e45870ee20397cbc9e5416f108cb0",
        "raw_sha256": "15e31e50319daaf8e45704c5e3b339e876a0e2949927365928b32f5c412ba95c",
    },
    {
        "artifact_role": "generator",
        "source_path": "research/brainvision/independent_order_sensitive_synthetic_fixture_generator_v0_1.py",
        "git_blob": "77bc2e319e1283ce5d00b283f99a1d1d56732d83",
        "raw_sha256": "001317367d5f8e3c06ae3da177901b88f94560ae555eeca54247464e2cb9ed78",
    },
    {
        "artifact_role": "freeze_library",
        "source_path": "research/brainvision/independent_order_sensitive_synthetic_fixture_freeze_v0_1.py",
        "git_blob": "a06a80ac1a253a6b85f2c3e6bf4bf712b0d78d8a",
        "raw_sha256": "ef78cc21a3a6e139a781ce4f8c356c88b9a132ab89771d8250dc57ea375b2fca",
    },
    {
        "artifact_role": "verifier_test",
        "source_path": "research/brainvision/test_brainvision_independent_order_sensitive_synthetic_fixture_verifier_v0_1.py",
        "git_blob": "97f2605284c53dedfec43d8e65112d30418877a8",
        "raw_sha256": "af0a798d5195e78ad2e051cc0ec2846ec82d20c8d796f448e355f77ec4d76032",
    },
    {
        "artifact_role": "generator_freeze_test",
        "source_path": "research/brainvision/test_brainvision_independent_order_sensitive_synthetic_fixture_freeze_v0_1.py",
        "git_blob": "a7774cfc49e05e75c1d49355a28166fd2375abae",
        "raw_sha256": "a02c613f2620755611c3e86914458c4f72bfa2a7d3cfce55f94748bafef0fa0c",
    },
)

# Section 8 configuration payload (exact 16 fields, in order).
CONFIGURATION_SCHEMA = (
    "torment-brainvision-independent-order-sensitive-synthetic-fixture-freeze-configuration-v0.1"
)
SEED_ENUMERATION_POLICY = "canonical-lexicographic-c1-lt-c2-d1-lt-d2-mod-64-v0.1"
CONSTRUCTION_POLICY = "c-plus-d-and-c-minus-d-mod-64-collision-collapsed-v0.1"
ELIGIBILITY_POLICY = "first-failure-eight-predicate-descriptor-blind-v0.1"
DUPLICATE_POLICY = "member-orbit-affine-plus-complement-slot-invariant-pair-key-v0.1"

# Section 11 output constants.
RESULTS_DIR = "research/brainvision/results"
FINAL_DIR_NAME = "independent_order_sensitive_synthetic_fixture_freeze_v0_1"
STAGING_DIR_NAME = ".independent_order_sensitive_synthetic_fixture_freeze_v0_1.staging"
MANIFEST_FILE_NAME = "independent_order_sensitive_synthetic_fixture_freeze_manifest_v0_1.json"
ENVELOPE_FILE_NAME = "independent_order_sensitive_synthetic_fixture_freeze_execution_envelope_v0_1.json"
SUMMARY_FILE_NAME = "independent_order_sensitive_synthetic_fixture_freeze_summary_v0_1.txt"

# Section 10 execution-envelope top-level field order (24).
ENVELOPE_KEY_ORDER: Tuple[str, ...] = (
    "envelope_schema",
    "envelope_version",
    "operation_identity",
    "authoritative_operation",
    "repository_execution_head",
    "authorization_document_path",
    "authorization_document_git_blob",
    "python_version",
    "runner_identity",
    "runner_test_identity",
    "source_identities",
    "configuration_identity",
    "pre_contact_status",
    "canonical_contact_status",
    "pass_1_identity_summary",
    "pass_2_identity_summary",
    "comparison_result",
    "finalization_status",
    "family_frozen",
    "manifest_payload_sha256",
    "external_manifest_sha256",
    "failure_code",
    "failure_stage",
    "publication_status",
)

# Section 10.8 pass-summary field order (9).
PASS_SUMMARY_KEY_ORDER: Tuple[str, ...] = (
    "pass_label",
    "pass_status",
    "canonical_result_kind",
    "manifest_payload_sha256",
    "external_manifest_sha256",
    "accepted_fixture_order",
    "search_diagnostics",
    "failure_code",
    "failure_stage",
)

# Section 10.5 identity object field order (5).
IDENTITY_KEY_ORDER: Tuple[str, ...] = (
    "artifact_role",
    "artifact_id",
    "source_path",
    "git_blob",
    "raw_sha256",
)

SUMMARY_SCHEMA = "torment-brainvision-independent-order-sensitive-synthetic-fixture-freeze-summary-v0.1"

# Section 11.6 summary TXT line order (17).
SUMMARY_LINE_ORDER: Tuple[str, ...] = (
    "summary_schema",
    "operation_identity",
    "authoritative_operation",
    "repository_execution_head",
    "pre_contact_status",
    "canonical_contact_status",
    "pass_1_status",
    "pass_2_status",
    "canonical_result_kind",
    "comparison_status",
    "finalization_status",
    "family_frozen",
    "manifest_payload_sha256",
    "external_manifest_sha256",
    "failure_code",
    "failure_stage",
    "publication_status",
)

# Publication-failure stderr lines (Section 11.5).
PUBLICATION_FAILURE_SERIALIZATION = (
    "SYNTHETIC_FIXTURE_FREEZE_PUBLICATION_FAILURE SERIALIZATION_FAILURE publication"
)
PUBLICATION_FAILURE_HASH_IDENTITY = (
    "SYNTHETIC_FIXTURE_FREEZE_PUBLICATION_FAILURE HASH_IDENTITY_FAILURE publication"
)

# Exit codes (Section 11.4).
EXIT_PROMOTED = 0
EXIT_POST_CONTACT_FAILURE = 1
EXIT_PRE_CONTACT_REFUSAL = 2
EXIT_PUBLICATION_FAILURE = 3


# --------------------------------------------------------------------------- #
# Deterministic runner-internal exceptions
# --------------------------------------------------------------------------- #

class PreContactRefusal(Exception):
    """A fail-closed pre-contact refusal; no evidence is created."""

    def __init__(self, failure_code: str, detail: str = "", failure_stage: str = "pre_contact") -> None:
        super().__init__("%s@%s" % (failure_code, failure_stage))
        self.failure_code = failure_code
        self.failure_stage = failure_stage
        self.detail = detail


class PostContactFailure(Exception):
    """A deterministic post-contact failure whose evidence must be promoted."""

    def __init__(self, failure_code: str, failure_stage: str, detail: str = "") -> None:
        super().__init__("%s@%s" % (failure_code, failure_stage))
        self.failure_code = failure_code
        self.failure_stage = failure_stage
        self.detail = detail


class PublicationFailure(Exception):
    """A staging/write/verify/rename failure; exit 3 with an exact stderr line."""

    def __init__(self, stderr_line: str) -> None:
        super().__init__(stderr_line)
        self.stderr_line = stderr_line


# --------------------------------------------------------------------------- #
# Read-only Git interface (frozen commands; injected in tests)
# --------------------------------------------------------------------------- #

class ReadOnlyGit:
    """The only Git surface the runner exposes: an exact set of read-only
    commands. No caller-supplied command is accepted; no mutating command
    exists. Bounded tests inject a fake with the same methods."""

    def __init__(self, repo_root: str) -> None:
        self._repo_root = repo_root

    def _run(self, args: Sequence[str]) -> Tuple[int, bytes]:
        completed = subprocess.run(  # noqa: S603 - frozen read-only argv, no shell
            ["git", *args],
            cwd=self._repo_root,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return completed.returncode, completed.stdout

    def resolve_head(self) -> str:
        code, out = self._run(["rev-parse", "HEAD"])
        return out.decode("ascii", "replace").strip() if code == 0 else ""

    def resolve_origin_main(self) -> str:
        code, out = self._run(["rev-parse", "origin/main"])
        return out.decode("ascii", "replace").strip() if code == 0 else ""

    def current_branch(self) -> str:
        code, out = self._run(["rev-parse", "--abbrev-ref", "HEAD"])
        return out.decode("ascii", "replace").strip() if code == 0 else ""

    def status_porcelain(self) -> str:
        code, out = self._run(["status", "--porcelain"])
        return out.decode("utf-8", "replace") if code == 0 else "\x00dirty"

    def path_exists_at_head(self, path: str) -> bool:
        code, _ = self._run(["cat-file", "-e", "HEAD:%s" % path])
        return code == 0

    def latest_commit_for_path(self, path: str) -> str:
        code, out = self._run(["log", "-1", "--format=%H", "--", path])
        return out.decode("ascii", "replace").strip() if code == 0 else ""

    def blob_id_at_head(self, path: str) -> str:
        code, out = self._run(["rev-parse", "HEAD:%s" % path])
        return out.decode("ascii", "replace").strip() if code == 0 else ""

    def committed_bytes(self, path: str) -> bytes:
        code, out = self._run(["show", "HEAD:%s" % path])
        if code != 0:
            raise PreContactRefusal("UNAUTHORIZED_EXECUTION", "committed bytes unavailable: %s" % path)
        return out

    def show_toplevel(self) -> str:
        code, out = self._run(["rev-parse", "--show-toplevel"])
        return out.decode("utf-8", "replace").strip() if code == 0 else ""


# --------------------------------------------------------------------------- #
# Pure helpers
# --------------------------------------------------------------------------- #

def _is_lower_hex(value: Any, length: int) -> bool:
    return isinstance(value, str) and len(value) == length and all(
        ch in "0123456789abcdef" for ch in value)


def collect_stdin(stdin: Any) -> bytes:
    """Deterministic stdin collection factored for testability.

    An interactive console (isatty) returns empty and never blocks. Redirected
    empty stdin remains empty. Redirected non-empty stdin returns its exact bytes,
    which ``validate_cli`` then refuses before any project-module import.
    """
    if stdin is None:
        return b""
    try:
        if stdin.isatty():
            return b""
    except (AttributeError, ValueError):
        pass
    buffer = getattr(stdin, "buffer", None)
    if buffer is not None:
        return buffer.read()
    data = stdin.read()
    return data.encode("utf-8") if isinstance(data, str) else data


def build_configuration_payload() -> Dict[str, Any]:
    """The exact ordered 16-field configuration object (Section 8)."""
    return {
        "configuration_schema": CONFIGURATION_SCHEMA,
        "configuration_version": "0.1",
        "N": 64,
        "K_synthetic": 8,
        "seed_enumeration_policy": SEED_ENUMERATION_POLICY,
        "construction_policy": CONSTRUCTION_POLICY,
        "eligibility_policy": ELIGIBILITY_POLICY,
        "duplicate_policy": DUPLICATE_POLICY,
        "fixed_fixture_duplicate_key_seeding": True,
        "selection_rule": "first-eight-unique-eligible-pairs",
        "descriptor_blind_selection": True,
        "pass_count": 2,
        "parallelism": 1,
        "backtracking": False,
        "challenger_contact": False,
        "frozen_F3_contact": False,
    }


_SEARCH_DIAGNOSTICS_KEY_ORDER: Tuple[str, ...] = (
    "total_seeds_visited",
    "eligibility_rejection_counts",
    "eligible_duplicate_count",
    "accepted_seed_order_positions",
    "terminal_seed_tuple",
    "terminal_status",
)
_REJECTION_REASON_ORDER: Tuple[str, ...] = (
    "A_CARDINALITY_NOT_9",
    "B_CARDINALITY_NOT_9",
    "IDENTICAL_SUPPORTS",
    "A2_MISMATCH",
    "TRANSITION_TABLE_MISMATCH",
    "AFFINE_EQUIVALENT",
    "AFFINE_COMPLEMENT_EQUIVALENT",
    "TRIPLE_ARRAY_EQUAL",
)


def _is_strict_nonneg_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


_ACCEPTED_RECORD_KEY_ORDER: Tuple[str, ...] = ("family_index", "seed_order_position", "fixture_record")


def _is_exact_pair_key(value: Any) -> bool:
    return (type(value) is tuple and len(value) == 2
            and all(isinstance(k, str) and len(k) == 64 and set(k) <= {"0", "1"} for k in value)
            and value[0] < value[1])


def validate_scan_result(scan: Any, pass_label: str, fixed_pair_key: Any) -> str:
    """Validate a scan result, its diagnostic structure, and its canonical
    cardinality / distinctness invariants.

    Returns the canonical result kind (ACCEPTED_EIGHT or SEED_SPACE_EXHAUSTED).
    Any malformed scan object, non-exact boolean, missing key, invalid diagnostic
    structure, cardinality contradiction, duplicated pair key, duplicated seed
    tuple, fixed-fixture pair key among the accepted records, or malformed wrapper
    raises a deterministic process failure for the given pass, never a manifest.
    """
    stage = pass_label_to_stage(pass_label)

    def bad(detail: str) -> "PostContactFailure":
        return PostContactFailure("GENERATOR_CONFIGURATION_INVALID", stage, detail)

    if not isinstance(scan, dict):
        raise bad("scan result not a mapping")
    if scan.get("valid") is not True:
        raise bad("scan result not exactly valid=True")
    accepted = scan.get("accepted_records")
    diagnostics = scan.get("search_diagnostics")
    if not isinstance(accepted, list):
        raise bad("accepted_records not a list")
    if not isinstance(diagnostics, dict) or tuple(diagnostics.keys()) != _SEARCH_DIAGNOSTICS_KEY_ORDER:
        raise bad("search_diagnostics key set/order invalid")
    counts = diagnostics["eligibility_rejection_counts"]
    if not isinstance(counts, dict) or tuple(counts.keys()) != _REJECTION_REASON_ORDER:
        raise bad("eligibility_rejection_counts key order invalid")
    if not all(_is_strict_nonneg_int(counts[reason]) for reason in _REJECTION_REASON_ORDER):
        raise bad("eligibility_rejection_counts not nonnegative integers")
    positions = diagnostics["accepted_seed_order_positions"]
    if not isinstance(positions, list):
        raise bad("accepted_seed_order_positions not a list")
    if not _is_strict_nonneg_int(diagnostics["total_seeds_visited"]):
        raise bad("total_seeds_visited invalid")
    if not _is_strict_nonneg_int(diagnostics["eligible_duplicate_count"]):
        raise bad("eligible_duplicate_count invalid")
    terminal_tuple = diagnostics["terminal_seed_tuple"]
    if terminal_tuple is not None and not (
            isinstance(terminal_tuple, list) and len(terminal_tuple) == 4
            and all(_is_strict_nonneg_int(v) for v in terminal_tuple)):
        raise bad("terminal_seed_tuple shape invalid")

    wrapper_positions: List[int] = []
    pair_keys: List[Any] = []
    seed_tuples: List[Any] = []
    for index, wrapper in enumerate(accepted):
        if not isinstance(wrapper, dict) or tuple(wrapper.keys()) != _ACCEPTED_RECORD_KEY_ORDER:
            raise bad("accepted wrapper key set/order invalid")
        if wrapper["family_index"] != index or not _is_strict_nonneg_int(wrapper["family_index"]):
            raise bad("accepted wrapper family_index not gap-free")
        seed_order_position = wrapper["seed_order_position"]
        if not _is_strict_nonneg_int(seed_order_position):
            raise bad("accepted wrapper seed_order_position invalid")
        fixture_record = wrapper["fixture_record"]
        if not isinstance(fixture_record, dict) or "pair_duplicate_key" not in fixture_record \
                or "seed_tuple" not in fixture_record:
            raise bad("accepted fixture_record missing")
        pair_key = fixture_record["pair_duplicate_key"]
        if not _is_exact_pair_key(pair_key):
            raise bad("accepted pair_duplicate_key representation invalid")
        if pair_key == fixed_pair_key:
            raise bad("accepted pair key equals the fixed-fixture pair key")
        wrapper_positions.append(seed_order_position)
        pair_keys.append(pair_key)
        seed_tuples.append(fixture_record["seed_tuple"])

    if positions != wrapper_positions:
        raise bad("accepted positions disagree with accepted wrappers")
    previous = -1
    for position in positions:
        if position <= previous:
            raise bad("accepted positions not strictly increasing")
        previous = position
    if len(set(pair_keys)) != len(pair_keys):
        raise bad("duplicated accepted pair key")
    if len(set(seed_tuples)) != len(seed_tuples):
        raise bad("duplicated accepted seed tuple")

    terminal_status = diagnostics["terminal_status"]
    if terminal_status == "ACCEPTED_EIGHT":
        if len(accepted) != 8 or len(positions) != 8 or len(set(pair_keys)) != 8:
            raise bad("ACCEPTED_EIGHT without exactly eight distinct accepted fixtures")
        return "ACCEPTED_EIGHT"
    if terminal_status == "SEED_SPACE_EXHAUSTED":
        if len(accepted) >= 8:
            raise bad("SEED_SPACE_EXHAUSTED with eight or more accepted fixtures")
        return "SEED_SPACE_EXHAUSTED"
    raise bad("unexpected terminal status")


def parse_authorization_binding(document_bytes: bytes) -> Dict[str, str]:
    """Parse and validate the seven-field binding from committed document bytes.

    Deterministic standard-library string parsing only; the document is never
    executed, imported, or evaluated. A grammar/marker/field/hex defect raises
    PreContactRefusal(UNAUTHORIZED_EXECUTION)."""
    if not isinstance(document_bytes, (bytes, bytearray)):
        raise PreContactRefusal("UNAUTHORIZED_EXECUTION", "authorization bytes not bytes")
    text = bytes(document_bytes).decode("utf-8", "replace")
    lines = text.split("\n")
    begins = [i for i, line in enumerate(lines) if line == BINDING_BEGIN_MARKER]
    ends = [i for i, line in enumerate(lines) if line == BINDING_END_MARKER]
    if len(begins) != 1 or len(ends) != 1 or ends[0] <= begins[0]:
        raise PreContactRefusal("UNAUTHORIZED_EXECUTION", "binding markers missing/duplicated/out-of-order")
    body = lines[begins[0] + 1:ends[0]]
    if len(body) != len(BINDING_FIELD_ORDER):
        raise PreContactRefusal("UNAUTHORIZED_EXECUTION", "binding does not have exactly seven field lines")
    fields: Dict[str, str] = {}
    for index, line in enumerate(body):
        if "=" not in line:
            raise PreContactRefusal("UNAUTHORIZED_EXECUTION", "binding line is not key=value")
        key, _, value = line.partition("=")
        if key != BINDING_FIELD_ORDER[index]:
            raise PreContactRefusal("UNAUTHORIZED_EXECUTION", "binding key order invalid")
        if key in fields:
            raise PreContactRefusal("UNAUTHORIZED_EXECUTION", "binding has a duplicated field")
        fields[key] = value
    if fields["authorization_schema"] != AUTHORIZATION_SCHEMA:
        raise PreContactRefusal("UNAUTHORIZED_EXECUTION", "authorization_schema literal invalid")
    if fields["authorization_version"] != AUTHORIZATION_VERSION:
        raise PreContactRefusal("UNAUTHORIZED_EXECUTION", "authorization_version literal invalid")
    for key in _BLOB_FIELDS:
        if not _is_lower_hex(fields[key], 40):
            raise PreContactRefusal("UNAUTHORIZED_EXECUTION", "%s not 40 lowercase hex" % key)
    for key in _SHA256_FIELDS:
        if not _is_lower_hex(fields[key], 64):
            raise PreContactRefusal("UNAUTHORIZED_EXECUTION", "%s not 64 lowercase hex" % key)
    return fields


def _reject_non_json_scalars(value: Any, path: str = "envelope") -> None:
    """Reject floats/NaN/Infinity and any non-JSON scalar before serialization.

    Lists and tuples are both permitted (each serializes to a JSON array; the
    accepted pair-duplicate keys are exact built-in tuples of two strings).
    """
    if isinstance(value, bool) or value is None or isinstance(value, (int, str)):
        return
    if isinstance(value, float):
        raise PostContactFailure("SERIALIZATION_FAILURE", "serialization", "float at %s" % path)
    if isinstance(value, dict):
        for key, sub in value.items():
            if not isinstance(key, str):
                raise PostContactFailure("SERIALIZATION_FAILURE", "serialization", "non-string key at %s" % path)
            _reject_non_json_scalars(sub, "%s.%s" % (path, key))
        return
    if isinstance(value, (list, tuple)):
        for index, sub in enumerate(value):
            _reject_non_json_scalars(sub, "%s[%d]" % (path, index))
        return
    raise PostContactFailure("SERIALIZATION_FAILURE", "serialization", "unsupported type at %s" % path)


_COMMITTED_FAILURE_CODES = frozenset({
    "FIXED_FIXTURE_RECONSTRUCTION_FAILURE",
    "FIXED_FIXTURE_LOWER_ORDER_CERTIFICATE_FAILURE",
    "FIXED_FIXTURE_AFFINE_CERTIFICATE_FAILURE",
    "FIXED_FIXTURE_AFFINE_COMPLEMENT_CERTIFICATE_FAILURE",
    "FIXED_FIXTURE_TRIPLE_CERTIFICATE_FAILURE",
    "GENERATOR_CONFIGURATION_INVALID",
    "SEED_ENUMERATION_FAILURE",
    "CONSTRUCTION_FAILURE",
    "ELIGIBILITY_CERTIFICATE_FAILURE",
    "DUPLICATE_KEY_FAILURE",
    "INSUFFICIENT_UNIQUE_FIXTURES",
    "MANIFEST_SCHEMA_FAILURE",
    "SERIALIZATION_FAILURE",
    "HASH_IDENTITY_FAILURE",
    "REPLAY_MISMATCH",
    "FORBIDDEN_IMPORT_DETECTED",
    "SOURCE_OWNERSHIP_FAILURE",
    "PROHIBITED_CHALLENGER_CONTACT",
    "PROHIBITED_FROZEN_FAMILY_CONTACT",
    "PRODUCTION_BOUNDARY_VIOLATION",
    "UNAUTHORIZED_EXECUTION",
})
_RUNNER_STAGES = frozenset({
    "pre_contact", "pass_1", "pass_2", "replay_comparison", "finalization", "publication",
})
# The exact failure codes a generator seed-stream scan can truthfully report on a
# valid=False result, per the accepted generator contract. Only these two are
# preserved; every other value (including unrelated runner / finalization /
# boundary codes) is a malformed generator result normalized at the pass boundary.
_GENERATOR_SCAN_FAILURE_CODES = frozenset({
    "SEED_ENUMERATION_FAILURE",
    "GENERATOR_CONFIGURATION_INVALID",
})


def _canonical_config_sha256() -> str:
    """The exact canonical SHA-256 of the 16-field configuration payload, using
    the same fixed serialization the freeze library uses (compact separators,
    ASCII, allow_nan=False, one terminal LF)."""
    payload = build_configuration_payload()
    data = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode("utf-8") + b"\n"
    return hashlib.sha256(data).hexdigest()


def _serialization_fault(detail: str) -> "PostContactFailure":
    return PostContactFailure("SERIALIZATION_FAILURE", "serialization", detail)


def _valid_repo_rel_path(path: Any) -> bool:
    if not isinstance(path, str) or path == "" or path.startswith("/") or "\\" in path:
        return False
    if len(path) >= 2 and path[1] == ":":
        return False
    segments = path.split("/")
    return all(seg not in ("", ".", "..") for seg in segments)


def _valid_binary_key(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(ch in "01" for ch in value)


def _validate_identity_object(obj: Any, role: str, artifact_id: str, source_path: str) -> None:
    if not isinstance(obj, dict) or tuple(obj.keys()) != IDENTITY_KEY_ORDER:
        raise _serialization_fault("identity key set/order invalid")
    if obj["artifact_role"] != role or obj["artifact_id"] != artifact_id:
        raise _serialization_fault("identity role/id invalid")
    if obj["source_path"] != source_path or not _valid_repo_rel_path(source_path):
        raise _serialization_fault("identity source_path invalid")
    if not _is_lower_hex(obj["git_blob"], 40):
        raise _serialization_fault("identity git_blob invalid")
    if not _is_lower_hex(obj["raw_sha256"], 64):
        raise _serialization_fault("identity raw_sha256 invalid")


def _validate_search_diagnostics(diagnostics: Any, expected_kind: str) -> List[int]:
    if not isinstance(diagnostics, dict) or tuple(diagnostics.keys()) != _SEARCH_DIAGNOSTICS_KEY_ORDER:
        raise _serialization_fault("search_diagnostics key order invalid")
    if not _is_strict_nonneg_int(diagnostics["total_seeds_visited"]):
        raise _serialization_fault("total_seeds_visited invalid")
    counts = diagnostics["eligibility_rejection_counts"]
    if not isinstance(counts, dict) or tuple(counts.keys()) != _REJECTION_REASON_ORDER:
        raise _serialization_fault("eligibility_rejection_counts order invalid")
    if not all(_is_strict_nonneg_int(counts[reason]) for reason in _REJECTION_REASON_ORDER):
        raise _serialization_fault("eligibility_rejection_counts not nonnegative integers")
    if not _is_strict_nonneg_int(diagnostics["eligible_duplicate_count"]):
        raise _serialization_fault("eligible_duplicate_count invalid")
    positions = diagnostics["accepted_seed_order_positions"]
    if not isinstance(positions, list) or not all(_is_strict_nonneg_int(p) for p in positions):
        raise _serialization_fault("accepted_seed_order_positions invalid")
    previous = -1
    for position in positions:
        if position <= previous:
            raise _serialization_fault("accepted_seed_order_positions not strictly increasing")
        previous = position
    terminal = diagnostics["terminal_seed_tuple"]
    if terminal is not None and not (isinstance(terminal, list) and len(terminal) == 4
                                     and all(_is_strict_nonneg_int(v) for v in terminal)):
        raise _serialization_fault("terminal_seed_tuple shape invalid")
    terminal_status = diagnostics["terminal_status"]
    if terminal_status not in ("ACCEPTED_EIGHT", "SEED_SPACE_EXHAUSTED", "FIXED_FIXTURE_FAILURE"):
        raise _serialization_fault("terminal_status invalid")
    if expected_kind == "ACCEPTED_EIGHT" and (terminal_status != "ACCEPTED_EIGHT" or len(positions) != 8):
        raise _serialization_fault("diagnostics inconsistent with ACCEPTED_EIGHT")
    if expected_kind == "SEED_SPACE_EXHAUSTED" and (terminal_status != "SEED_SPACE_EXHAUSTED" or len(positions) >= 8):
        raise _serialization_fault("diagnostics inconsistent with SEED_SPACE_EXHAUSTED")
    if expected_kind == "FIXED_FIXTURE_FAILURE" and terminal_status != "FIXED_FIXTURE_FAILURE":
        raise _serialization_fault("diagnostics inconsistent with FIXED_FIXTURE_FAILURE")
    return positions


def _validate_pass_summary(summary: Any, expected_label: str) -> None:
    if not isinstance(summary, dict) or tuple(summary.keys()) != PASS_SUMMARY_KEY_ORDER:
        raise _serialization_fault("pass-summary key order invalid")
    if summary["pass_label"] != expected_label:
        raise _serialization_fault("pass_label invalid")
    status = summary["pass_status"]
    optional_keys = ("canonical_result_kind", "manifest_payload_sha256", "external_manifest_sha256",
                     "accepted_fixture_order", "search_diagnostics", "failure_code", "failure_stage")
    if status == "NOT_STARTED":
        if any(summary[key] is not None for key in optional_keys):
            raise _serialization_fault("NOT_STARTED summary not fully null")
    elif status == "COMPLETE":
        kind = summary["canonical_result_kind"]
        if kind not in ("ACCEPTED_EIGHT", "FIXED_FIXTURE_FAILURE", "SEED_SPACE_EXHAUSTED"):
            raise _serialization_fault("COMPLETE canonical_result_kind invalid")
        if not _is_lower_hex(summary["manifest_payload_sha256"], 64) or \
                not _is_lower_hex(summary["external_manifest_sha256"], 64):
            raise _serialization_fault("COMPLETE hash invalid")
        order = summary["accepted_fixture_order"]
        if not isinstance(order, list):
            raise _serialization_fault("accepted_fixture_order not a list")
        if kind == "ACCEPTED_EIGHT" and len(order) != 8:
            raise _serialization_fault("ACCEPTED_EIGHT accepted_fixture_order not eight")
        for pair in order:
            if not isinstance(pair, (list, tuple)) or len(pair) != 2:
                raise _serialization_fault("accepted_fixture_order entry not a 2-array")
            if not _valid_binary_key(pair[0]) or not _valid_binary_key(pair[1]) or not pair[0] < pair[1]:
                raise _serialization_fault("accepted_fixture_order key format invalid")
        positions = _validate_search_diagnostics(summary["search_diagnostics"], kind)
        if len(positions) != len(order):
            raise _serialization_fault("accepted positions inconsistent with accepted_fixture_order")
        if summary["failure_code"] is not None or summary["failure_stage"] is not None:
            raise _serialization_fault("COMPLETE summary carries a failure")
    elif status == "FAILED":
        nulls = ("canonical_result_kind", "manifest_payload_sha256", "external_manifest_sha256",
                 "accepted_fixture_order", "search_diagnostics")
        if any(summary[key] is not None for key in nulls):
            raise _serialization_fault("FAILED summary not null in result fields")
        if summary["failure_code"] not in _COMMITTED_FAILURE_CODES:
            raise _serialization_fault("FAILED summary code not in the committed vocabulary")
        expected_stage = "pass_1" if expected_label == "PASS_1" else "pass_2"
        if summary["failure_stage"] != expected_stage:
            raise _serialization_fault("FAILED summary stage is not this pass's stage")
    else:
        raise _serialization_fault("pass_status invalid")


_SUCCESS_MISMATCH_ORDER = (
    "canonical_payload_bytes_mismatch",
    "manifest_payload_sha256_mismatch",
    "canonical_manifest_bytes_mismatch",
    "external_manifest_sha256_mismatch",
    "accepted_fixture_order_mismatch",
    "search_diagnostics_mismatch",
)
_FINALIZATION_STATUS_VOCAB = ("NOT_STARTED", "NOT_APPLICABLE", "COMPLETE", "FAILED")


def _validate_comparison_result(comparison: Any) -> None:
    if comparison is None:
        return
    if not isinstance(comparison, dict) or \
            tuple(comparison.keys()) != ("matches", "failure_code", "failure_stage", "mismatch_reasons"):
        raise _serialization_fault("comparison_result key order invalid")
    reasons = comparison["mismatch_reasons"]
    if comparison["matches"] is True:
        if comparison["failure_code"] is not None or comparison["failure_stage"] is not None or reasons != []:
            raise _serialization_fault("success comparison_result invalid")
    elif comparison["matches"] is False:
        if comparison["failure_code"] != "REPLAY_MISMATCH" or comparison["failure_stage"] != "replay_comparison":
            raise _serialization_fault("mismatch comparison_result code/stage invalid")
        if not isinstance(reasons, list) or len(reasons) == 0 or \
                any(reason not in _SUCCESS_MISMATCH_ORDER for reason in reasons):
            raise _serialization_fault("mismatch reasons invalid")
        if len(set(reasons)) != len(reasons):
            raise _serialization_fault("mismatch reasons not unique")
        indices = [_SUCCESS_MISMATCH_ORDER.index(reason) for reason in reasons]
        if indices != sorted(indices):
            raise _serialization_fault("mismatch reasons not in accepted order")
    else:
        raise _serialization_fault("comparison_result matches not a strict boolean")


def _validate_live_comparison_result(comparison: Any) -> None:
    """Strict validation of a freshly returned comparison object on the live path.

    Unlike :func:`_validate_comparison_result` (which permits an absent comparison
    during envelope validation), the trusted-library return here must be a concrete
    accepted comparison object; ``None`` or any non-mapping is a malformed return.
    """
    if not isinstance(comparison, dict):
        raise _serialization_fault("comparison result is not a mapping")
    _validate_comparison_result(comparison)


def _validate_finalized_transport(finalized: Any) -> None:
    """Validate only the transport structure and required identity fields of a
    finalized bundle (never the finalization mathematics). A missing key, wrong
    type, malformed hash, or a non-frozen final manifest is a malformed return.
    """
    if not isinstance(finalized, dict) or tuple(finalized.keys()) != (
            "final_manifest_object", "canonical_payload_bytes", "manifest_payload_sha256",
            "canonical_manifest_bytes", "external_manifest_sha256"):
        raise _serialization_fault("finalized bundle key order invalid")
    final_manifest = finalized["final_manifest_object"]
    if not isinstance(final_manifest, dict) or final_manifest.get("family_frozen") is not True:
        raise _serialization_fault("finalized manifest not family_frozen")
    if not isinstance(finalized["canonical_payload_bytes"], (bytes, bytearray)) or \
            not isinstance(finalized["canonical_manifest_bytes"], (bytes, bytearray)):
        raise _serialization_fault("finalized bundle bytes invalid")
    if not _is_lower_hex(finalized["manifest_payload_sha256"], 64) or \
            not _is_lower_hex(finalized["external_manifest_sha256"], 64):
        raise _serialization_fault("finalized bundle hash format invalid")


def _validate_execution_envelope(envelope: Dict[str, Any]) -> None:
    if not isinstance(envelope, dict) or tuple(envelope.keys()) != ENVELOPE_KEY_ORDER:
        raise _serialization_fault("envelope key order invalid")
    if envelope["envelope_schema"] != ENVELOPE_SCHEMA or envelope["envelope_version"] != ENVELOPE_VERSION:
        raise _serialization_fault("envelope schema/version invalid")
    if envelope["operation_identity"] != OPERATION_IDENTITY or envelope["authoritative_operation"] is not True:
        raise _serialization_fault("operation identity invalid")
    if not _is_lower_hex(envelope["repository_execution_head"], 40):
        raise _serialization_fault("repository_execution_head invalid")
    if envelope["authorization_document_path"] != AUTHORIZATION_DOCUMENT_PATH or \
            not _valid_repo_rel_path(envelope["authorization_document_path"]):
        raise _serialization_fault("authorization_document_path invalid")
    if not _is_lower_hex(envelope["authorization_document_git_blob"], 40):
        raise _serialization_fault("authorization_document_git_blob invalid")
    if not isinstance(envelope["python_version"], str) or envelope["python_version"] == "":
        raise _serialization_fault("python_version invalid")
    _validate_identity_object(envelope["runner_identity"], "runner", RUNNER_ARTIFACT_ID, RUNNER_SOURCE_PATH)
    _validate_identity_object(envelope["runner_test_identity"], "runner_test",
                              RUNNER_TEST_ARTIFACT_ID, RUNNER_TEST_SOURCE_PATH)
    sources = envelope["source_identities"]
    expected_roles = [s["artifact_role"] for s in S1B_SOURCE_IDENTITIES]
    if not isinstance(sources, list) or len(sources) != 5:
        raise _serialization_fault("source_identities not five objects")
    for obj, expected in zip(sources, S1B_SOURCE_IDENTITIES):
        if not isinstance(obj, dict) or tuple(obj.keys()) != ("artifact_role", "source_path", "git_blob", "raw_sha256"):
            raise _serialization_fault("source identity key order invalid")
        if not _valid_repo_rel_path(obj["source_path"]):
            raise _serialization_fault("source identity path invalid")
        # Every source identity must equal the exact frozen S1B identity.
        if obj["artifact_role"] != expected["artifact_role"] or obj["source_path"] != expected["source_path"] \
                or obj["git_blob"] != expected["git_blob"] or obj["raw_sha256"] != expected["raw_sha256"]:
            raise _serialization_fault("source identity does not equal frozen S1B identity")
    if [s["artifact_role"] for s in sources] != expected_roles:
        raise _serialization_fault("source_identities role order invalid")
    if envelope["python_version"] != PYTHON_VERSION:
        raise _serialization_fault("python_version not the exact frozen version")
    config_identity = envelope["configuration_identity"]
    if not isinstance(config_identity, dict) or \
            tuple(config_identity.keys()) != ("configuration_payload", "configuration_sha256"):
        raise _serialization_fault("configuration_identity key order invalid")
    if config_identity["configuration_payload"] != build_configuration_payload():
        raise _serialization_fault("configuration_payload not the exact 16-field object")
    if config_identity["configuration_sha256"] != _canonical_config_sha256():
        raise _serialization_fault("configuration_sha256 not the canonical SHA-256 of the payload")
    if envelope["pre_contact_status"] != "PASSED":
        raise _serialization_fault("pre_contact_status invalid")
    if envelope["canonical_contact_status"] not in (
            "NOT_CONTACTED", "PASS_1_STARTED", "PASS_1_COMPLETE", "PASS_2_STARTED", "PASS_2_COMPLETE"):
        raise _serialization_fault("canonical_contact_status invalid")
    pass_1 = envelope["pass_1_identity_summary"]
    pass_2 = envelope["pass_2_identity_summary"]
    _validate_pass_summary(pass_1, "PASS_1")
    _validate_pass_summary(pass_2, "PASS_2")
    comparison = envelope["comparison_result"]
    _validate_comparison_result(comparison)
    if envelope["finalization_status"] not in _FINALIZATION_STATUS_VOCAB:
        raise _serialization_fault("finalization_status invalid")
    if not isinstance(envelope["family_frozen"], bool):
        raise _serialization_fault("family_frozen not boolean")
    payload_hash = envelope["manifest_payload_sha256"]
    external_hash = envelope["external_manifest_sha256"]
    if payload_hash is None:
        if external_hash is not None or envelope["family_frozen"] is True:
            raise _serialization_fault("manifest hash presence inconsistent")
    else:
        if not _is_lower_hex(payload_hash, 64) or not _is_lower_hex(external_hash, 64):
            raise _serialization_fault("manifest hash format invalid")

    # canonical_contact_status must agree with the pass states.
    status_1 = pass_1["pass_status"]
    status_2 = pass_2["pass_status"]
    if status_1 == "FAILED":
        expected_contact = "PASS_1_STARTED"
    elif status_2 == "FAILED":
        expected_contact = "PASS_2_STARTED"
    elif status_1 == "COMPLETE" and status_2 == "COMPLETE":
        expected_contact = "PASS_2_COMPLETE"
    else:
        expected_contact = None
    if expected_contact is not None and envelope["canonical_contact_status"] != expected_contact:
        raise _serialization_fault("canonical_contact_status inconsistent with pass states")

    # finalization_status / family_frozen / comparison / manifest-hash cross-checks.
    matched = isinstance(comparison, dict) and comparison.get("matches") is True
    finalization_status = envelope["finalization_status"]
    if finalization_status == "COMPLETE":
        if not envelope["family_frozen"] or not matched:
            raise _serialization_fault("COMPLETE requires matched passes and family_frozen")
        if status_1 != "COMPLETE" or status_2 != "COMPLETE" \
                or pass_1["canonical_result_kind"] != "ACCEPTED_EIGHT" \
                or pass_2["canonical_result_kind"] != "ACCEPTED_EIGHT":
            raise _serialization_fault("COMPLETE requires two matched ACCEPTED_EIGHT passes")
        if payload_hash is None or external_hash is None:
            raise _serialization_fault("COMPLETE requires finalized manifest hashes")
    elif finalization_status == "NOT_APPLICABLE":
        if envelope["family_frozen"]:
            raise _serialization_fault("NOT_APPLICABLE cannot be family_frozen")
        if payload_hash is not None:   # replay-matched canonical failure
            if not matched or status_1 != "COMPLETE" or status_2 != "COMPLETE":
                raise _serialization_fault("canonical failure requires matched complete passes")
            kind_1 = pass_1["canonical_result_kind"]
            kind_2 = pass_2["canonical_result_kind"]
            if kind_1 != kind_2 or kind_1 not in ("FIXED_FIXTURE_FAILURE", "SEED_SPACE_EXHAUSTED"):
                raise _serialization_fault("canonical failure kind invalid")
            if payload_hash != pass_1["manifest_payload_sha256"] or payload_hash != pass_2["manifest_payload_sha256"] \
                    or external_hash != pass_1["external_manifest_sha256"] \
                    or external_hash != pass_2["external_manifest_sha256"]:
                raise _serialization_fault("canonical-failure manifest hashes disagree with pass bundles")
        else:   # ordinary replay mismatch — fully bound
            if status_1 != "COMPLETE" or status_2 != "COMPLETE":
                raise _serialization_fault("replay mismatch requires two complete passes")
            if comparison is None or matched or comparison.get("matches") is not False:
                raise _serialization_fault("replay mismatch requires a matches=false comparison")
            if external_hash is not None:
                raise _serialization_fault("replay mismatch carries no manifest hashes")
            if envelope["failure_code"] != "REPLAY_MISMATCH" \
                    or envelope["failure_stage"] != "replay_comparison":
                raise _serialization_fault(
                    "replay mismatch requires REPLAY_MISMATCH / replay_comparison")
    elif finalization_status == "NOT_STARTED":
        if envelope["family_frozen"] or payload_hash is not None or external_hash is not None:
            raise _serialization_fault("NOT_STARTED carries no frozen family and no manifest")
        if comparison is not None:
            raise _serialization_fault("NOT_STARTED requires a null comparison_result")
        not_started_code = envelope["failure_code"]
        not_started_stage = envelope["failure_stage"]
        if status_1 == "FAILED":
            # Pass 1 failed: pass 2 never started; the failure is exactly pass 1's.
            if status_2 != "NOT_STARTED":
                raise _serialization_fault("PASS_1 failure requires a NOT_STARTED PASS_2")
            if not_started_code != pass_1["failure_code"] or not_started_stage != "pass_1":
                raise _serialization_fault("PASS_1 failure not bound to the top-level failure")
        elif status_2 == "FAILED":
            # Pass 2 failed: pass 1 completed; the failure is exactly pass 2's.
            if status_1 != "COMPLETE":
                raise _serialization_fault("PASS_2 failure requires a COMPLETE PASS_1")
            if not_started_code != pass_2["failure_code"] or not_started_stage != "pass_2":
                raise _serialization_fault("PASS_2 failure not bound to the top-level failure")
        elif status_1 == "COMPLETE" and status_2 == "COMPLETE":
            # Comparison-process failure: two complete passes, no comparison produced.
            if not_started_stage != "replay_comparison" or not_started_code != "MANIFEST_SCHEMA_FAILURE":
                raise _serialization_fault("comparison-process failure code/stage invalid")
        else:
            raise _serialization_fault("NOT_STARTED pass-state combination invalid")
    else:   # FAILED — only a genuine attempted positive finalization may fail
        if status_1 != "COMPLETE" or status_2 != "COMPLETE":
            raise _serialization_fault("FAILED finalization requires two complete passes")
        if pass_1["canonical_result_kind"] != "ACCEPTED_EIGHT" \
                or pass_2["canonical_result_kind"] != "ACCEPTED_EIGHT":
            raise _serialization_fault("FAILED finalization requires two ACCEPTED_EIGHT passes")
        if not matched:
            raise _serialization_fault("FAILED finalization requires a successful replay comparison")
        if envelope["family_frozen"]:
            raise _serialization_fault("FAILED finalization cannot be family_frozen")
        if payload_hash is not None or external_hash is not None:
            raise _serialization_fault("FAILED finalization carries no manifest hashes")
        if envelope["failure_stage"] != "finalization":
            raise _serialization_fault("FAILED finalization stage must be finalization")
        if envelope["failure_code"] not in ("REPLAY_MISMATCH", "HASH_IDENTITY_FAILURE"):
            raise _serialization_fault("FAILED finalization code invalid")

    failure_code = envelope["failure_code"]
    failure_stage = envelope["failure_stage"]
    if (payload_hash is not None) != (failure_code is None):
        raise _serialization_fault("failure_code presence inconsistent with a published manifest")
    if failure_code is None:
        if failure_stage is not None:
            raise _serialization_fault("failure_stage set without failure_code")
    else:
        if failure_code not in _COMMITTED_FAILURE_CODES or failure_stage not in _RUNNER_STAGES:
            raise _serialization_fault("failure code/stage not in the committed vocabulary")
    if envelope["publication_status"] != "VERIFIED_FOR_PROMOTION":
        raise _serialization_fault("publication_status invalid")


def serialize_execution_envelope(envelope: Dict[str, Any]) -> bytes:
    """Validate the complete top-level and nested contract, then serialize
    canonically (Section 10.11)."""
    _validate_execution_envelope(envelope)
    _reject_non_json_scalars(envelope)
    try:
        text = json.dumps(envelope, ensure_ascii=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise PostContactFailure("SERIALIZATION_FAILURE", "serialization", str(exc))
    return text.encode("utf-8") + b"\n"


def _not_started_pass_summary(pass_label: str) -> Dict[str, Any]:
    return {
        "pass_label": pass_label,
        "pass_status": "NOT_STARTED",
        "canonical_result_kind": None,
        "manifest_payload_sha256": None,
        "external_manifest_sha256": None,
        "accepted_fixture_order": None,
        "search_diagnostics": None,
        "failure_code": None,
        "failure_stage": None,
    }


def build_summary_text(envelope: Dict[str, Any]) -> bytes:
    """Derive the exact summary TXT (Section 11.6) from an envelope."""
    def scalar(value: Any) -> str:
        if value is None:
            return "null"
        if value is True:
            return "true"
        if value is False:
            return "false"
        return str(value)

    pass_1 = envelope["pass_1_identity_summary"]
    pass_2 = envelope["pass_2_identity_summary"]
    comparison = envelope["comparison_result"]
    if comparison is None:
        comparison_status = "NOT_RUN"
    elif comparison.get("matches") is True:
        comparison_status = "MATCH"
    else:
        comparison_status = "MISMATCH"
    # A canonical result kind is used only when both passes completed, comparison
    # matched, and a publishable canonical manifest exists (its hash is present);
    # every other outcome is PROCESS_FAILURE.
    both_complete = pass_1["pass_status"] == "COMPLETE" and pass_2["pass_status"] == "COMPLETE"
    if (envelope["manifest_payload_sha256"] is not None and both_complete
            and comparison_status == "MATCH"
            and pass_1["canonical_result_kind"] == pass_2["canonical_result_kind"]):
        canonical_result_kind = pass_1["canonical_result_kind"]
    else:
        canonical_result_kind = "PROCESS_FAILURE"
    values = {
        "summary_schema": SUMMARY_SCHEMA,
        "operation_identity": envelope["operation_identity"],
        "authoritative_operation": scalar(envelope["authoritative_operation"]),
        "repository_execution_head": scalar(envelope["repository_execution_head"]),
        "pre_contact_status": envelope["pre_contact_status"],
        "canonical_contact_status": envelope["canonical_contact_status"],
        "pass_1_status": pass_1["pass_status"],
        "pass_2_status": pass_2["pass_status"],
        "canonical_result_kind": canonical_result_kind,
        "comparison_status": comparison_status,
        "finalization_status": envelope["finalization_status"],
        "family_frozen": scalar(envelope["family_frozen"]),
        "manifest_payload_sha256": scalar(envelope["manifest_payload_sha256"]),
        "external_manifest_sha256": scalar(envelope["external_manifest_sha256"]),
        "failure_code": scalar(envelope["failure_code"]),
        "failure_stage": scalar(envelope["failure_stage"]),
        "publication_status": "VERIFIED_FOR_PROMOTION",
    }
    lines = ["%s=%s" % (key, values[key]) for key in SUMMARY_LINE_ORDER]
    text = "\n".join(lines) + "\n"
    if not all(ord(ch) < 128 for ch in text):
        raise PostContactFailure("SERIALIZATION_FAILURE", "serialization", "non-ASCII summary")
    return text.encode("ascii")


# --------------------------------------------------------------------------- #
# The runner
# --------------------------------------------------------------------------- #

class Outcome:
    def __init__(self, exit_code: int, stdout: bytes, stderr: bytes) -> None:
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr


class PassResult:
    def __init__(self, pass_label: str, kind: Optional[str], manifest: Optional[Dict[str, Any]],
                 bundle: Optional[Dict[str, Any]], summary: Dict[str, Any]) -> None:
        self.pass_label = pass_label
        self.kind = kind
        self.manifest = manifest
        self.bundle = bundle
        self.summary = summary


class FreezeRunner:
    """Deterministic two-pass authoritative freeze runner with injected boundaries.

    Injected dependencies (all optional; defaults are the real read-only Git and
    the real local project-module import) let bounded tests exercise every
    boundary without real Git, without real repository discovery, and without
    driving the real canonical iterator."""

    def __init__(
        self,
        *,
        repo_root: str,
        argv: Optional[Sequence[str]] = None,
        stdin_bytes: bytes = b"",
        git: Optional[ReadOnlyGit] = None,
        importer: Optional[Callable[[], Any]] = None,
        file_reader: Optional[Callable[[str], bytes]] = None,
        seed_iterator_factory: Optional[Callable[[], Any]] = None,
        renamer: Optional[Callable[[str, str], None]] = None,
        runner_file: Optional[str] = None,
    ) -> None:
        self._repo_root = repo_root
        self._argv = list(argv) if argv is not None else [RUNNER_SOURCE_PATH]
        self._stdin_bytes = stdin_bytes
        self._runner_file = runner_file if runner_file is not None else os.path.abspath(__file__)
        self._git = git if git is not None else ReadOnlyGit(repo_root)
        self._importer = importer if importer is not None else _default_import_project_modules
        self._file_reader = file_reader if file_reader is not None else self._default_file_reader
        self._seed_iterator_factory = seed_iterator_factory
        self._renamer = renamer if renamer is not None else os.rename
        self._modules: Any = None  # populated only after early checks succeed
        self.project_modules_imported = False  # observable for tests

    def _default_file_reader(self, repo_relative_path: str) -> bytes:
        with open(os.path.join(self._repo_root, repo_relative_path), "rb") as handle:
            return handle.read()

    # ---- CLI validation --------------------------------------------------- #

    def validate_cli(self) -> None:
        argv = list(self._argv)
        if len(argv) == 0:
            raise PreContactRefusal("UNAUTHORIZED_EXECUTION", "empty argv")
        if len(argv) != 1:
            raise PreContactRefusal("UNAUTHORIZED_EXECUTION", "no arguments or options are accepted")
        invoked = argv[0]
        if not isinstance(invoked, str) or invoked == "":
            raise PreContactRefusal("UNAUTHORIZED_EXECUTION", "invalid runner invocation path")
        normalized = invoked.replace("\\", "/")
        # Exactly the repository-relative runner path: no absolute path, no drive
        # prefix, no suffix-only match.
        if normalized != RUNNER_SOURCE_PATH:
            raise PreContactRefusal("UNAUTHORIZED_EXECUTION", "argv[0] is not the exact runner path")
        if self._stdin_bytes:
            raise PreContactRefusal("UNAUTHORIZED_EXECUTION", "no stdin input is accepted")

    def verify_repository_root(self) -> None:
        """Authoritative repository-root ownership check (before project import)."""
        toplevel = self._git.show_toplevel()
        if not isinstance(toplevel, str) or toplevel == "":
            raise PreContactRefusal("UNAUTHORIZED_EXECUTION", "git top level unresolved")
        if os.path.realpath(toplevel) != os.path.realpath(self._repo_root):
            raise PreContactRefusal("UNAUTHORIZED_EXECUTION", "git top level != repository root")
        expected_runner = os.path.join(toplevel, *RUNNER_SOURCE_PATH.split("/"))
        if os.path.realpath(self._runner_file) != os.path.realpath(expected_runner):
            raise PreContactRefusal("UNAUTHORIZED_EXECUTION", "runner not at authoritative repository path")

    # ---- Read-only Git identity + non-circular HEAD rule ------------------ #

    def resolve_execution_head(self) -> Tuple[str, str]:
        head = self._git.resolve_head()
        origin_main = self._git.resolve_origin_main()
        if not _is_lower_hex(head, 40) or not _is_lower_hex(origin_main, 40):
            raise PreContactRefusal("UNAUTHORIZED_EXECUTION", "HEAD/origin not resolvable")
        if head != origin_main:
            raise PreContactRefusal("UNAUTHORIZED_EXECUTION", "HEAD != origin/main")
        if self._git.current_branch() != "main":
            raise PreContactRefusal("UNAUTHORIZED_EXECUTION", "branch is not main")
        if self._git.status_porcelain() != "":
            raise PreContactRefusal("UNAUTHORIZED_EXECUTION", "working tree is not clean")
        if not self._git.path_exists_at_head(AUTHORIZATION_DOCUMENT_PATH):
            raise PreContactRefusal("UNAUTHORIZED_EXECUTION", "authorization document absent at HEAD")
        path_commit = self._git.latest_commit_for_path(AUTHORIZATION_DOCUMENT_PATH)
        if not _is_lower_hex(path_commit, 40):
            raise PreContactRefusal("UNAUTHORIZED_EXECUTION", "authorization path commit not resolvable")
        if path_commit != head:
            raise PreContactRefusal("UNAUTHORIZED_EXECUTION", "authorization path commit != HEAD")
        document_blob = self._git.blob_id_at_head(AUTHORIZATION_DOCUMENT_PATH)
        if not _is_lower_hex(document_blob, 40):
            raise PreContactRefusal("HASH_IDENTITY_FAILURE", "authorization document blob malformed")
        return head, document_blob

    # ---- Identity checks (before project-module import) ------------------- #

    def _blob_and_raw(self, path: str) -> Tuple[str, str]:
        blob = self._git.blob_id_at_head(path)
        raw = hashlib.sha256(self._file_reader(path)).hexdigest()
        return blob, raw

    def verify_s1b_identities(self) -> None:
        for source in S1B_SOURCE_IDENTITIES:
            blob, raw = self._blob_and_raw(source["source_path"])
            if blob != source["git_blob"] or raw != source["raw_sha256"]:
                raise PreContactRefusal(
                    "HASH_IDENTITY_FAILURE", "S1B identity mismatch: %s" % source["source_path"])

    def verify_runner_identities(self, binding: Dict[str, str]) -> None:
        runner_blob, runner_raw = self._blob_and_raw(RUNNER_SOURCE_PATH)
        if runner_blob != binding["runner_git_blob"] or runner_raw != binding["runner_raw_sha256"]:
            raise PreContactRefusal("HASH_IDENTITY_FAILURE", "runner identity mismatch")
        test_blob, test_raw = self._blob_and_raw(RUNNER_TEST_SOURCE_PATH)
        if test_blob != binding["runner_test_git_blob"] or test_raw != binding["runner_test_raw_sha256"]:
            raise PreContactRefusal("HASH_IDENTITY_FAILURE", "runner-test identity mismatch")

    def verify_python_version(self) -> None:
        actual = "%d.%d.%d" % (sys.version_info[0], sys.version_info[1], sys.version_info[2])
        if actual != PYTHON_VERSION:
            raise PreContactRefusal("HASH_IDENTITY_FAILURE", "python version mismatch: %s" % actual)

    def _final_dir(self) -> str:
        return os.path.join(self._repo_root, RESULTS_DIR, FINAL_DIR_NAME)

    def _staging_dir(self) -> str:
        return os.path.join(self._repo_root, RESULTS_DIR, STAGING_DIR_NAME)

    def verify_output_paths_absent(self) -> None:
        if os.path.exists(self._final_dir()):
            raise PreContactRefusal("UNAUTHORIZED_EXECUTION", "final output directory already exists")
        if os.path.exists(self._staging_dir()):
            raise PreContactRefusal("UNAUTHORIZED_EXECUTION", "staging output directory already exists")

    # ---- Pre-contact orchestration --------------------------------------- #

    def pre_contact(self) -> Dict[str, Any]:
        """Run the full fail-closed pre-contact sequence and return the context.

        Any unexpected repository, Git, file-read, import, configuration,
        source-boundary, or fixed-fixture exception is normalized into an
        authorized pre-contact refusal; no ordinary exception escapes.
        """
        try:
            return self._pre_contact_impl()
        except PreContactRefusal:
            raise
        except Exception:
            raise PreContactRefusal("UNAUTHORIZED_EXECUTION", "unexpected pre-contact fault")

    def _pre_contact_impl(self) -> Dict[str, Any]:
        self.validate_cli()
        self.verify_repository_root()
        execution_head, document_blob = self.resolve_execution_head()
        document_bytes = self._git.committed_bytes(AUTHORIZATION_DOCUMENT_PATH)
        binding = parse_authorization_binding(document_bytes)
        self.verify_s1b_identities()
        self.verify_python_version()
        self.verify_runner_identities(binding)
        self.verify_output_paths_absent()

        # Local project-module import (only now).
        self._modules = self._importer()
        self.project_modules_imported = True
        freeze = self._modules.freeze

        # Library-backed checks.
        configuration_payload = build_configuration_payload()
        configuration_sha256 = freeze.canonical_configuration_sha256(configuration_payload)
        if configuration_sha256 != binding["configuration_sha256"]:
            raise PreContactRefusal("HASH_IDENTITY_FAILURE", "configuration identity mismatch")
        configuration_identity = freeze.build_configuration_identity(configuration_payload)

        for source in S1B_SOURCE_IDENTITIES:
            source_text = self._file_reader(source["source_path"]).decode("utf-8", "replace")
            try:
                freeze.validate_source_boundary(
                    source["source_path"], source_text, freeze.AUTHORIZED_ALLOWLIST)
            except freeze.SyntheticFixtureProcessFailure as exc:
                # Preserve the exact source-boundary code; stage becomes pre_contact.
                raise PreContactRefusal(exc.failure_code, "source-boundary rejection")

        fixed_fixture = self._modules.verifier.verify_fixed_fixture()
        if not fixed_fixture["validation"]["valid"]:
            raise PreContactRefusal(
                fixed_fixture["validation"]["failure_code"] or "FIXED_FIXTURE_RECONSTRUCTION_FAILURE",
                "pre-contact fixed-fixture verification failed")
        if fixed_fixture["triple_disagreement_count"] != 288:
            raise PreContactRefusal(
                "FIXED_FIXTURE_TRIPLE_CERTIFICATE_FAILURE", "pre-contact 288 certificate failed")

        return {
            "execution_head": execution_head,
            "authorization_document_git_blob": document_blob,
            "binding": binding,
            "configuration_identity": configuration_identity,
            "source_identity": self._build_manifest_source_identity(execution_head),
        }

    def _build_manifest_source_identity(self, execution_head: str) -> Dict[str, Any]:
        by_role = {source["artifact_role"]: source for source in S1B_SOURCE_IDENTITIES}
        return {
            "generator_source_path": by_role["generator"]["source_path"],
            "generator_git_blob": by_role["generator"]["git_blob"],
            "generator_raw_sha256": by_role["generator"]["raw_sha256"],
            "verifier_source_path": by_role["verifier"]["source_path"],
            "verifier_git_blob": by_role["verifier"]["git_blob"],
            "verifier_raw_sha256": by_role["verifier"]["raw_sha256"],
            "test_source_identities": [
                {"source_path": by_role["freeze_library"]["source_path"],
                 "git_blob": by_role["freeze_library"]["git_blob"],
                 "raw_sha256": by_role["freeze_library"]["raw_sha256"]},
                {"source_path": by_role["verifier_test"]["source_path"],
                 "git_blob": by_role["verifier_test"]["git_blob"],
                 "raw_sha256": by_role["verifier_test"]["raw_sha256"]},
                {"source_path": by_role["generator_freeze_test"]["source_path"],
                 "git_blob": by_role["generator_freeze_test"]["git_blob"],
                 "raw_sha256": by_role["generator_freeze_test"]["raw_sha256"]},
            ],
            "repository_commit": execution_head,
            "python_version": PYTHON_VERSION,
        }

    # ---- One complete pass ----------------------------------------------- #

    def run_one_pass(self, pass_label: str, source_identity: Dict[str, Any],
                     configuration_identity: Dict[str, Any]) -> PassResult:
        """One independent pass with its own fresh iterator and state objects.

        Every deterministic generator / manifest / serialization / hash failure is
        normalized at this boundary into a FAILED pass with the exact authorized
        failure code and stage ``pass_1``/``pass_2``; it never yields a candidate
        manifest for a malformed or contradictory scan.
        """
        stage = pass_label_to_stage(pass_label)
        verifier = self._modules.verifier
        generator = self._modules.generator
        freeze = self._modules.freeze
        try:
            fixed_fixture = verifier.verify_fixed_fixture()
            if not fixed_fixture["validation"]["valid"]:
                manifest = freeze.build_fixed_fixture_failure_manifest(
                    fixed_fixture, source_identity, configuration_identity)
                bundle = freeze.build_candidate_pass_bundle(manifest)
                return PassResult(pass_label, "FIXED_FIXTURE_FAILURE", manifest, bundle,
                                  self._complete_pass_summary(pass_label, "FIXED_FIXTURE_FAILURE", manifest, bundle))

            seed_iterator = self._make_seed_iterator()
            scan = generator.scan_seed_stream(seed_iterator)
            if isinstance(scan, dict) and scan.get("valid") is False:
                # Preserve a reported failure code only when it is one the generator
                # scan boundary can truthfully produce; any absent, malformed, or
                # inappropriate code (including unrelated runner / finalization /
                # boundary codes) is normalized here so it can never survive to
                # envelope serialization.
                reported = scan.get("failure_code")
                failure_code = reported if reported in _GENERATOR_SCAN_FAILURE_CODES \
                    else "GENERATOR_CONFIGURATION_INVALID"
                return PassResult(pass_label, None, None, None,
                                  self._failed_pass_summary(pass_label, failure_code, stage))
            fixed_pair_key = generator.fixed_fixture_pair_key()
            kind = validate_scan_result(scan, pass_label, fixed_pair_key)   # exact invariants
            accepted_records = scan["accepted_records"]
            diagnostics = scan["search_diagnostics"]
            if kind == "ACCEPTED_EIGHT":
                manifest = freeze.build_candidate_manifest(
                    fixed_fixture, accepted_records, diagnostics, source_identity, configuration_identity)
            else:
                manifest = freeze.build_seed_exhaustion_failure_manifest(
                    fixed_fixture, accepted_records, diagnostics, source_identity, configuration_identity)
            bundle = freeze.build_candidate_pass_bundle(manifest)
            return PassResult(pass_label, kind, manifest, bundle,
                              self._complete_pass_summary(pass_label, kind, manifest, bundle))
        except PostContactFailure as failure:
            return PassResult(pass_label, None, None, None,
                              self._failed_pass_summary(pass_label, failure.failure_code, stage))
        except freeze.SyntheticFixtureProcessFailure as failure:
            return PassResult(pass_label, None, None, None,
                              self._failed_pass_summary(pass_label, failure.failure_code, stage))
        except Exception:
            # Any unexpected verifier / iterator / generator / manifest / bundle /
            # serialization / hash exception is normalized to a deterministic pass
            # failure at this boundary; no traceback escapes.
            return PassResult(pass_label, None, None, None,
                              self._failed_pass_summary(pass_label, "GENERATOR_CONFIGURATION_INVALID", stage))

    def _make_seed_iterator(self) -> Any:
        if self._seed_iterator_factory is not None:
            return self._seed_iterator_factory()
        return self._modules.generator.iter_canonical_seed_tuples()

    def _complete_pass_summary(self, pass_label: str, kind: str, manifest: Dict[str, Any],
                               bundle: Dict[str, Any]) -> Dict[str, Any]:
        accepted_order = [af["pair_duplicate_key"] for af in manifest["accepted_fixtures"]]
        return {
            "pass_label": pass_label,
            "pass_status": "COMPLETE",
            "canonical_result_kind": kind,
            "manifest_payload_sha256": manifest["manifest_payload_sha256"],
            "external_manifest_sha256": bundle["external_manifest_sha256"],
            "accepted_fixture_order": accepted_order,
            "search_diagnostics": manifest["search_diagnostics"],
            "failure_code": None,
            "failure_stage": None,
        }

    def _failed_pass_summary(self, pass_label: str, failure_code: str, failure_stage: str) -> Dict[str, Any]:
        summary = _not_started_pass_summary(pass_label)
        summary["pass_status"] = "FAILED"
        summary["failure_code"] = failure_code
        summary["failure_stage"] = failure_stage
        return summary

    # ---- Two-pass orchestration ------------------------------------------ #

    def two_pass_operation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run two fully independent passes and the replay comparison.

        Pass 2 receives a fresh iterator and fresh state; nothing from pass 1 is
        reused. Only a replay-matched ACCEPTED_EIGHT calls positive finalization.
        """
        freeze = self._modules.freeze
        source_identity = context["source_identity"]
        configuration_identity = context["configuration_identity"]

        def result(outcome, pass_1=None, pass_2=None, comparison=None, finalized=None,
                   failure_code=None, failure_stage=None):
            return {"outcome": outcome, "pass_1": pass_1, "pass_2": pass_2,
                    "comparison": comparison, "finalized": finalized,
                    "failure_code": failure_code, "failure_stage": failure_stage}

        pass_1 = self.run_one_pass("PASS_1", source_identity, configuration_identity)
        if pass_1.kind is None:
            return result("PASS_FAILURE", pass_1=pass_1,
                          failure_code=pass_1.summary["failure_code"], failure_stage="pass_1")

        pass_2 = self.run_one_pass("PASS_2", source_identity, configuration_identity)
        if pass_2.kind is None:
            return result("PASS_FAILURE", pass_1=pass_1, pass_2=pass_2,
                          failure_code=pass_2.summary["failure_code"], failure_stage="pass_2")

        try:
            comparison = freeze.compare_candidate_passes(pass_1.bundle, pass_2.bundle)
            # The trusted-library return shape is validated before it is trusted:
            # any malformed comparison object is a process failure, never a match.
            _validate_live_comparison_result(comparison)
        except freeze.SyntheticFixtureProcessFailure:
            # A malformed candidate bundle. comparison stays null; finalization
            # never started (rendered NOT_STARTED in the envelope).
            return result("COMPARISON_PROCESS_FAILURE", pass_1=pass_1, pass_2=pass_2,
                          failure_code="MANIFEST_SCHEMA_FAILURE", failure_stage="replay_comparison")
        except Exception:
            return result("COMPARISON_PROCESS_FAILURE", pass_1=pass_1, pass_2=pass_2,
                          failure_code="MANIFEST_SCHEMA_FAILURE", failure_stage="replay_comparison")
        if not comparison["matches"]:
            return result("REPLAY_MISMATCH", pass_1=pass_1, pass_2=pass_2, comparison=comparison,
                          failure_code="REPLAY_MISMATCH", failure_stage="replay_comparison")

        if pass_1.kind == "ACCEPTED_EIGHT":
            try:
                finalized = freeze.finalize_authoritative_manifest(pass_1.manifest, comparison)
                # Validate only the returned transport structure and identity fields
                # (not the finalization mathematics) before the bundle is trusted.
                _validate_finalized_transport(finalized)
            except freeze.SyntheticFixtureProcessFailure as failure:
                return result("FINALIZATION_FAILURE", pass_1=pass_1, pass_2=pass_2, comparison=comparison,
                              failure_code=failure.failure_code, failure_stage="finalization")
            except Exception:
                return result("FINALIZATION_FAILURE", pass_1=pass_1, pass_2=pass_2, comparison=comparison,
                              failure_code="HASH_IDENTITY_FAILURE", failure_stage="finalization")
            return result("POSITIVE", pass_1=pass_1, pass_2=pass_2, comparison=comparison, finalized=finalized)
        return result("CANONICAL_FAILURE", pass_1=pass_1, pass_2=pass_2, comparison=comparison)

    # ---- Execution-envelope assembly ------------------------------------- #

    def _runner_identity_object(self, binding: Dict[str, str], role: str, artifact_id: str,
                                source_path: str, blob_key: str, raw_key: str) -> Dict[str, Any]:
        return {
            "artifact_role": role,
            "artifact_id": artifact_id,
            "source_path": source_path,
            "git_blob": binding[blob_key],
            "raw_sha256": binding[raw_key],
        }

    def _source_identities_array(self) -> List[Dict[str, Any]]:
        return [
            {"artifact_role": source["artifact_role"], "source_path": source["source_path"],
             "git_blob": source["git_blob"], "raw_sha256": source["raw_sha256"]}
            for source in S1B_SOURCE_IDENTITIES
        ]

    def build_execution_envelope(self, context: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        binding = context["binding"]
        outcome = result["outcome"]
        pass_1 = result["pass_1"]
        pass_2 = result["pass_2"]
        comparison = result["comparison"]
        finalized = result["finalized"]

        pass_1_summary = pass_1.summary if pass_1 is not None else _not_started_pass_summary("PASS_1")
        pass_2_summary = pass_2.summary if pass_2 is not None else _not_started_pass_summary("PASS_2")

        if pass_2 is not None and pass_2.kind is not None:
            canonical_contact_status = "PASS_2_COMPLETE"
        elif pass_2 is not None:
            canonical_contact_status = "PASS_2_STARTED"
        elif pass_1 is not None and pass_1.kind is not None:
            canonical_contact_status = "PASS_1_COMPLETE"
        else:
            canonical_contact_status = "PASS_1_STARTED"

        family_frozen = False
        manifest_payload_sha256: Optional[str] = None
        external_manifest_sha256: Optional[str] = None
        failure_code: Optional[str] = None
        failure_stage: Optional[str] = None

        if outcome == "POSITIVE":
            finalization_status = "COMPLETE"
            family_frozen = True
            manifest_payload_sha256 = finalized["manifest_payload_sha256"]
            external_manifest_sha256 = finalized["external_manifest_sha256"]
        elif outcome == "CANONICAL_FAILURE":
            finalization_status = "NOT_APPLICABLE"
            manifest_payload_sha256 = pass_1.bundle["manifest_payload_sha256"]
            external_manifest_sha256 = pass_1.bundle["external_manifest_sha256"]
        elif outcome == "REPLAY_MISMATCH":
            finalization_status = "NOT_APPLICABLE"
            failure_code = "REPLAY_MISMATCH"
            failure_stage = "replay_comparison"
        elif outcome == "COMPARISON_PROCESS_FAILURE":
            # A comparison-process failure is bound to an exact, non-arbitrary
            # replay-comparison schema failure (two complete passes, no comparison).
            finalization_status = "NOT_STARTED"
            failure_code = "MANIFEST_SCHEMA_FAILURE"
            failure_stage = "replay_comparison"
        elif outcome == "FINALIZATION_FAILURE":
            finalization_status = "FAILED"
            failure_code = result["failure_code"]
            failure_stage = "finalization"
        else:  # PASS_FAILURE
            finalization_status = "NOT_STARTED"
            failure_code = result["failure_code"]
            failure_stage = result["failure_stage"]

        envelope = {
            "envelope_schema": ENVELOPE_SCHEMA,
            "envelope_version": ENVELOPE_VERSION,
            "operation_identity": OPERATION_IDENTITY,
            "authoritative_operation": AUTHORITATIVE_OPERATION,
            "repository_execution_head": context["execution_head"],
            "authorization_document_path": AUTHORIZATION_DOCUMENT_PATH,
            "authorization_document_git_blob": context["authorization_document_git_blob"],
            "python_version": PYTHON_VERSION,
            "runner_identity": self._runner_identity_object(
                binding, "runner", RUNNER_ARTIFACT_ID, RUNNER_SOURCE_PATH,
                "runner_git_blob", "runner_raw_sha256"),
            "runner_test_identity": self._runner_identity_object(
                binding, "runner_test", RUNNER_TEST_ARTIFACT_ID, RUNNER_TEST_SOURCE_PATH,
                "runner_test_git_blob", "runner_test_raw_sha256"),
            "source_identities": self._source_identities_array(),
            "configuration_identity": context["configuration_identity"],
            "pre_contact_status": "PASSED",
            "canonical_contact_status": canonical_contact_status,
            "pass_1_identity_summary": pass_1_summary,
            "pass_2_identity_summary": pass_2_summary,
            "comparison_result": comparison,
            "finalization_status": finalization_status,
            "family_frozen": family_frozen,
            "manifest_payload_sha256": manifest_payload_sha256,
            "external_manifest_sha256": external_manifest_sha256,
            "failure_code": failure_code,
            "failure_stage": failure_stage,
            "publication_status": "VERIFIED_FOR_PROMOTION",
        }
        return envelope

    # ---- Publication ------------------------------------------------------ #

    def _canonical_manifest_bytes_for(self, result: Dict[str, Any]) -> Optional[bytes]:
        # The exact replay-matched pass bytes are reused; canonical_manifest_bytes
        # is never re-invoked for a canonical-failure publication.
        if result["outcome"] == "POSITIVE":
            return result["finalized"]["canonical_manifest_bytes"]
        if result["outcome"] == "CANONICAL_FAILURE":
            return result["pass_1"].bundle["canonical_manifest_bytes"]
        return None

    def publish(self, context: Dict[str, Any], result: Dict[str, Any]) -> int:
        """Publish evidence, normalizing any unexpected fault at this boundary.

        Delegates to the deterministic publication implementation. Every fault
        inside publication is surfaced as a PublicationFailure (exit 3) with an
        exact stderr line and the partial or complete staging is retained exactly
        as written; no ordinary exception escapes. A deterministic serialization
        fault while assembling the evidence bytes maps to SERIALIZATION_FAILURE;
        any other unexpected fault maps to HASH_IDENTITY_FAILURE.
        """
        try:
            return self._publish_impl(context, result)
        except PublicationFailure:
            raise
        except PostContactFailure:
            raise PublicationFailure(PUBLICATION_FAILURE_SERIALIZATION)
        except Exception:
            raise PublicationFailure(PUBLICATION_FAILURE_HASH_IDENTITY)

    def _publish_impl(self, context: Dict[str, Any], result: Dict[str, Any]) -> int:
        """Write staging evidence, re-read and verify, then atomically promote.

        Returns the process exit code (0 for a complete canonical result, 1 for a
        promoted post-contact failure). Raises PublicationFailure (exit 3) on any
        staging/write/verify/rename fault, leaving staging unchanged. Staging
        creation / encoding / write failures map to SERIALIZATION_FAILURE; close /
        re-read / verification / listing / rename failures map to
        HASH_IDENTITY_FAILURE.
        """
        outcome = result["outcome"]
        envelope = self.build_execution_envelope(context, result)
        try:
            envelope_bytes = serialize_execution_envelope(envelope)
            summary_bytes = build_summary_text(envelope)
            manifest_bytes = self._canonical_manifest_bytes_for(result)
        except PostContactFailure:
            raise PublicationFailure(PUBLICATION_FAILURE_SERIALIZATION)

        intended: List[Tuple[str, bytes]] = []
        if manifest_bytes is not None:
            intended.append((MANIFEST_FILE_NAME, manifest_bytes))
        intended.append((ENVELOPE_FILE_NAME, envelope_bytes))
        intended.append((SUMMARY_FILE_NAME, summary_bytes))

        staging = self._staging_dir()
        final = self._final_dir()
        # 1. exclusive staging creation (SERIALIZATION on failure)
        try:
            os.makedirs(os.path.dirname(staging), exist_ok=True)
            os.mkdir(staging)
        except OSError:
            raise PublicationFailure(PUBLICATION_FAILURE_SERIALIZATION)
        # 2-4. write (SERIALIZATION on open/encode/write); 5. close (HASH on close failure)
        for name, data in intended:
            try:
                handle = open(os.path.join(staging, name), "xb")
            except OSError:
                raise PublicationFailure(PUBLICATION_FAILURE_SERIALIZATION)
            try:
                handle.write(data)
                handle.flush()
            except OSError:
                try:
                    handle.close()
                except OSError:
                    pass
                raise PublicationFailure(PUBLICATION_FAILURE_SERIALIZATION)
            try:
                handle.close()
            except OSError:
                raise PublicationFailure(PUBLICATION_FAILURE_HASH_IDENTITY)
        # 6-7. re-read and verify bytes + SHA-256 identity (HASH on any failure)
        for name, data in intended:
            try:
                with open(os.path.join(staging, name), "rb") as handle:
                    on_disk = handle.read()
            except OSError:
                raise PublicationFailure(PUBLICATION_FAILURE_HASH_IDENTITY)
            if on_disk != data or hashlib.sha256(on_disk).hexdigest() != hashlib.sha256(data).hexdigest():
                raise PublicationFailure(PUBLICATION_FAILURE_HASH_IDENTITY)
        # 8. exact-set listing (HASH on listing failure or wrong set)
        expected_names = sorted(name for name, _ in intended)
        try:
            listing = sorted(os.listdir(staging))
        except OSError:
            raise PublicationFailure(PUBLICATION_FAILURE_HASH_IDENTITY)
        if listing != expected_names:
            raise PublicationFailure(PUBLICATION_FAILURE_HASH_IDENTITY)
        # 9. atomic rename. The rename is atomic: on failure the source staging
        # directory is untouched, so its bytes remain exactly as written.
        try:
            self._renamer(staging, final)
        except Exception:
            raise PublicationFailure(PUBLICATION_FAILURE_HASH_IDENTITY)
        return EXIT_PROMOTED if outcome in ("POSITIVE", "CANONICAL_FAILURE") else EXIT_POST_CONTACT_FAILURE

    # ---- Top-level orchestration ----------------------------------------- #

    def run(self) -> Outcome:
        # Each boundary normalizes its own faults; no path returns exit 1 merely
        # because an exception escaped. A pre-contact fault is an authorized
        # refusal (exit 2, no evidence). The two-pass operation converts any pass,
        # comparison, or finalization fault into a deterministic process-failure
        # result, which is published like any other outcome (exit 1 only after a
        # successful promotion). Publication normalizes any fault into a
        # PublicationFailure (exit 3, exact stderr, staging retained).
        try:
            context = self.pre_contact()
        except PreContactRefusal:
            return Outcome(EXIT_PRE_CONTACT_REFUSAL, b"", b"")
        result = self.two_pass_operation(context)
        try:
            exit_code = self.publish(context, result)
        except PublicationFailure as failure:
            return Outcome(EXIT_PUBLICATION_FAILURE, b"", (failure.stderr_line + "\n").encode("ascii"))
        return Outcome(exit_code, b"", b"")


def pass_label_to_stage(pass_label: str) -> str:
    return "pass_1" if pass_label == "PASS_1" else "pass_2"


# --------------------------------------------------------------------------- #
# Default local project-module import (only after early checks)
# --------------------------------------------------------------------------- #

def _default_import_project_modules() -> Any:
    import types

    import independent_order_sensitive_synthetic_fixture_verifier_v0_1 as verifier
    import independent_order_sensitive_synthetic_fixture_generator_v0_1 as generator
    import independent_order_sensitive_synthetic_fixture_freeze_v0_1 as freeze

    namespace = types.SimpleNamespace()
    namespace.verifier = verifier
    namespace.generator = generator
    namespace.freeze = freeze
    return namespace


# --------------------------------------------------------------------------- #
# Entry point (the execution boundary; never invoked by the bounded tests)
# --------------------------------------------------------------------------- #

def main() -> int:  # pragma: no cover - execution boundary, never invoked in tests
    # The operator's original working directory is preserved and is required to
    # equal the Git top level (verify_repository_root); it is never replaced with
    # the resolved top level.
    cwd = os.getcwd()
    runner = FreezeRunner(
        repo_root=cwd,
        argv=list(sys.argv),
        stdin_bytes=collect_stdin(sys.stdin),
    )
    outcome = runner.run()
    if outcome.stdout:
        sys.stdout.buffer.write(outcome.stdout)
    if outcome.stderr:
        sys.stderr.buffer.write(outcome.stderr)
    return outcome.exit_code


if __name__ == "__main__":  # pragma: no cover - never invoked in tests
    raise SystemExit(main())

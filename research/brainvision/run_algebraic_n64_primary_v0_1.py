"""TORMENT Brainvision algebraic N=64 PRIMARY_V0_1 runner v0.1 (offline; quarantined; descriptive-only).

Minimal dedicated runner implementing docs/TORMENT_BRAINVISION_ALGEBRAIC_N64_PRIMARY_V0_1_EXECUTION_
PROTOCOL_v0.1.md. Its sole generator call is ``generate_candidate_stream_with_replay("PRIMARY_V0_1")``. It
never calls the provisional ``generate_candidate_stream``, never makes a third generator call, and performs no
witness mathematics of any kind: no autocorrelation, difference multiset, triple array, primitive period,
affine image, or equivalence class is computed here. It never imports or contacts the witness verifier, the
family freezer, psi_trs, any descriptor, SAG, the paired prerecorded analyzer, the N64 falsifier, or
torment_service. stdlib only, plus the frozen generator and its canonical serializer.

Operator interface (complete):

    python research\\brainvision\\run_algebraic_n64_primary_v0_1.py

There is no CLI argument, environment override, profile selection, output-path selection, budget override,
source-path override, worker count, or overwrite flag. The ``results_root`` parameter on the internal
operation function exists solely so tests can publish into a temporary directory; it is unreachable from the
command line.

Exit contract (runner-level only; never inserted into any canonical generator artifact):

    0  a complete permitted two- or three-file artifact set was atomically published
    1  runner validation, serialization, generation-call, I/O, cleanup, or publication failure
    2  pre-execution refusal because the final or staging directory already exists

Exit 0 reports that the RUNNER did its job, not that a candidate stream exists. A canonical generator failure
(route_incomplete, dependency_unavailable, pre-hash null stream, replay mismatch) publishes the permitted
two-file set and exits 0; the summary line ``candidate-stream artifact written = False`` is the unambiguous
signal. Runner-level protocol-validation failures that still permit retention (§9.5 unresolved derived reason,
§12 run1/run2 counter mismatch) publish the permitted two-file set and exit 1.

FORMAL HOLD and Mode 0 remain active. Producing artifacts with this runner establishes deterministic generator
execution only. It establishes no witness validity, family validity, perception, temporal order, production
vision, or scientific meaning whatsoever.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import sys
from typing import Dict, List, Optional, Tuple

# Frozen generator (sole authoritative call) and its canonical serializer. Nothing else is imported.
import algebraic_direct_sum_n64_candidate_generator_v0_1 as generator
import witness_canonical_json_v0_1 as cjson

RUNNER_NAME = "run_algebraic_n64_primary_v0_1"
RUNNER_VERSION = "0.1"
PROFILE_NAME = "PRIMARY_V0_1"
PROTOCOL_DOCUMENT = "docs/TORMENT_BRAINVISION_ALGEBRAIC_N64_PRIMARY_V0_1_EXECUTION_PROTOCOL_v0.1.md"

RESULTS_DIRECTORY_NAME = "results"
FINAL_DIRECTORY_NAME = "algebraic_n64_primary_v0_1"
STAGING_DIRECTORY_NAME = ".algebraic_n64_primary_v0_1.staging"

REPLAY_RESULT_FILENAME = "algebraic_n64_primary_v0_1_replay_result.json"
CANDIDATE_STREAM_FILENAME = "algebraic_n64_primary_v0_1_candidate_stream.json"
SUMMARY_FILENAME = "algebraic_n64_primary_v0_1_summary.txt"

REPLAY_ENVELOPE_KEY = "generator_replay_result"
REPLAY_ENVELOPE_HASH_KEY = "generator_replay_result_sha256"
STREAM_ENVELOPE_KEY = "candidate_stream"
STREAM_ENVELOPE_HASH_KEY = "candidate_stream_sha256"

STREAM_COMPLETED = "stream_completed"
BUDGET_EXHAUSTED = "budget_exhausted"
ROUTE_INCOMPLETE = "route_incomplete"
DEPENDENCY_UNAVAILABLE = "dependency_unavailable"
EXTRACTABLE_TERMINAL_STATUSES = (STREAM_COMPLETED, BUDGET_EXHAUSTED)

LABEL_DERIVED = "derived_termination_reason"
LABEL_REPLAY_FAILURE = "replay_failure_reason"
LABEL_UNRESOLVED = "unresolved"
UNRESOLVED_REASON = "DERIVED_TERMINATION_REASON_UNRESOLVED"

COUNTER_FIELDS = ("parameter_tuples_examined", "colliding_parameter_tuples_rejected", "direct_tuples_found",
                  "exact_duplicate_candidates_skipped", "candidate_records_emitted")
COUNTER_SHAPE_INVALID = "STRUCTURAL_COUNTER_SHAPE_INVALID"
COUNTER_MISMATCH = "RUN1_RUN2_STRUCTURAL_COUNTER_MISMATCH"

EXIT_PUBLISHED = 0
EXIT_FAILURE = 1
EXIT_REFUSED = 2

ABSENT = "absent"
LF = "\n"


# --------------------------------------------------------------------------------- 1. path resolution
def default_results_root() -> str:
    """research/brainvision/results, resolved from this file only. No environment or argument input."""
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), RESULTS_DIRECTORY_NAME)


def final_directory(results_root: str) -> str:
    return os.path.join(results_root, FINAL_DIRECTORY_NAME)


def staging_directory(results_root: str) -> str:
    return os.path.join(results_root, STAGING_DIRECTORY_NAME)


# --------------------------------------------------------------------------------- 2. small helpers
def _is_strict_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _mapping(value: object) -> Optional[Dict[str, object]]:
    return value if isinstance(value, dict) else None


def _hex_or_absent(value: object) -> str:
    return value if isinstance(value, str) and cjson.is_lower_hex_64(value) else ABSENT


def _envelope_hash(payload: Dict[str, object], envelope_field: str, hash_field: str) -> str:
    """Read an envelope's own payload hash. A null envelope reports absent, never a zero or empty hash."""
    envelope = _mapping(payload.get(envelope_field))
    if envelope is None:
        return ABSENT
    return _hex_or_absent(envelope.get(hash_field))


def file_sha256(data: bytes) -> str:
    """SHA-256 over complete file bytes. Distinct byte domain from any envelope payload hash."""
    return hashlib.sha256(data).hexdigest()


# --------------------------------------------------------------------------------- 3. replay-payload reading
def replay_payload_of(replay_envelope: object) -> Optional[Dict[str, object]]:
    envelope = _mapping(replay_envelope)
    if envelope is None:
        return None
    return _mapping(envelope.get(REPLAY_ENVELOPE_KEY))


def candidate_stream_payload_of(payload: Dict[str, object]) -> Optional[Dict[str, object]]:
    stream_envelope = _mapping(payload.get("candidate_stream_envelope"))
    if stream_envelope is None:
        return None
    return _mapping(stream_envelope.get(STREAM_ENVELOPE_KEY))


def terminal_status_of(payload: Dict[str, object]) -> Optional[str]:
    """Terminal status is read from the embedded stream when present; otherwise it is null (protocol §9.2)."""
    stream = candidate_stream_payload_of(payload)
    if stream is None:
        return None
    status = stream.get("terminal_status")
    return status if isinstance(status, str) else None


def _failure_code_of(payload: Dict[str, object]) -> Optional[str]:
    record = _mapping(payload.get("failure_record"))
    if record is None:
        return None
    code = record.get("failure_code")
    return code if isinstance(code, str) and code else None


def _failure_stage_of(payload: Dict[str, object]) -> Optional[str]:
    record = _mapping(payload.get("failure_record"))
    if record is None:
        return None
    stage = record.get("stage")
    return stage if isinstance(stage, str) and stage else None


def _structural_budget_of(payload: Dict[str, object]) -> Optional[Dict[str, object]]:
    envelope = _mapping(payload.get("structural_budget_envelope"))
    if envelope is None:
        return None
    return _mapping(envelope.get("structural_budget"))


# --------------------------------------------------------------------------------- 4. termination derivation
def derive_termination_reason(payload: Dict[str, object]) -> Tuple[str, str]:
    """Return (label, value). Human-only; never written into a canonical generator artifact (protocol §9.3).

    Ceilings come from structural_budget_envelope; counters from run1_structural_counters. The record ceiling
    is tested before the tuple ceiling, encoding the frozen terminal precedence.
    """
    terminal_status = terminal_status_of(payload)
    failure_code = _failure_code_of(payload)

    if terminal_status is None:
        if failure_code is not None:
            return LABEL_REPLAY_FAILURE, failure_code
        return LABEL_UNRESOLVED, UNRESOLVED_REASON

    if terminal_status == STREAM_COMPLETED:
        return LABEL_DERIVED, "DOMAIN_EXHAUSTED"

    if terminal_status == BUDGET_EXHAUSTED:
        counters = _mapping(payload.get("run1_structural_counters"))
        budget = _structural_budget_of(payload)
        if counters is None or budget is None:
            return LABEL_UNRESOLVED, UNRESOLVED_REASON
        emitted = counters.get("candidate_records_emitted")
        examined = counters.get("parameter_tuples_examined")
        max_records = budget.get("max_candidate_records_emitted")
        max_tuples = budget.get("max_parameter_tuples_examined")
        if _is_strict_int(emitted) and _is_strict_int(max_records) and emitted == max_records:
            return LABEL_DERIVED, "MAX_CANDIDATE_RECORDS_EMITTED"
        if _is_strict_int(examined) and _is_strict_int(max_tuples) and examined == max_tuples:
            return LABEL_DERIVED, "MAX_PARAMETER_TUPLES_EXAMINED"
        return LABEL_UNRESOLVED, UNRESOLVED_REASON

    if terminal_status in (ROUTE_INCOMPLETE, DEPENDENCY_UNAVAILABLE):
        if failure_code is not None:
            return LABEL_DERIVED, failure_code
        return LABEL_UNRESOLVED, UNRESOLVED_REASON

    return LABEL_UNRESOLVED, UNRESOLVED_REASON


# --------------------------------------------------------------------------------- 5. extraction gate
def counter_mapping_conforms(counters: object) -> bool:
    """Exact five-key strict-integer nonnegative counter schema. Bools are rejected as counter values."""
    mapping = _mapping(counters)
    if mapping is None:
        return False
    if set(mapping) != set(COUNTER_FIELDS):
        return False                                 # missing or extra keys are both failures
    for field in COUNTER_FIELDS:
        value = mapping[field]
        if not _is_strict_int(value) or value < 0:
            return False
    return True


def counter_validation_failure(payload: Dict[str, object]) -> Optional[str]:
    """Return a runner-validation code when the returned counters are unusable, else None (protocol §12).

    Shape is checked before equality: two identically malformed mappings are a shape failure, not agreement.
    """
    run1 = payload.get("run1_structural_counters")
    run2 = payload.get("run2_structural_counters")
    if not counter_mapping_conforms(run1) or not counter_mapping_conforms(run2):
        return COUNTER_SHAPE_INVALID
    if _mapping(run1) != _mapping(run2):
        return COUNTER_MISMATCH
    return None


def counters_agree(payload: Dict[str, object]) -> bool:
    """Redundant cross-check of the generator's own comparison (protocol §12). No witness mathematics."""
    return counter_validation_failure(payload) is None


def extraction_permitted(payload: Dict[str, object]) -> bool:
    """All five protocol §8 conditions, each checked independently. No condition is inferred from another."""
    if payload.get("authoritative_operation") is not True:
        return False
    if payload.get("downstream_freeze_eligible") is not True:
        return False
    if payload.get("byte_identical") is not True:
        return False
    if _mapping(payload.get("candidate_stream_envelope")) is None:
        return False
    return terminal_status_of(payload) in EXTRACTABLE_TERMINAL_STATUSES


# --------------------------------------------------------------------------------- 6. summary construction
def _counter_lines(prefix: str, counters: Optional[Dict[str, object]]) -> List[str]:
    if counters is None:
        return ["%s_structural_counters = %s" % (prefix, ABSENT)]
    lines = []
    for field in COUNTER_FIELDS:
        value = counters.get(field)
        lines.append("%s_%s = %s" % (prefix, field, value if _is_strict_int(value) else ABSENT))
    return lines


def build_summary_text(payload: Dict[str, object], replay_payload_hash: object,
                       file_hashes: List[Tuple[str, str]],
                       stream_written: bool, validation_failures: List[str]) -> str:
    """Deterministic UTF-8 summary. Operator convenience only; carries no authority and is never parsed."""
    label, reason = derive_termination_reason(payload)
    terminal_status = terminal_status_of(payload)
    stream = candidate_stream_payload_of(payload)
    failure_code = _failure_code_of(payload)
    failure_stage = _failure_stage_of(payload)

    lines: List[str] = []
    lines.append("TORMENT Brainvision algebraic N=64 PRIMARY_V0_1 runner summary v%s" % RUNNER_VERSION)
    lines.append("governing protocol = %s" % PROTOCOL_DOCUMENT)
    lines.append("operator convenience only; not canonical generator evidence")
    lines.append("")
    lines.append("profile = %s" % PROFILE_NAME)
    lines.append("authoritative_operation = %s" % payload.get("authoritative_operation"))
    lines.append("downstream_freeze_eligible = %s" % payload.get("downstream_freeze_eligible"))
    lines.append("byte_identical = %s" % payload.get("byte_identical"))
    lines.append("")

    lines.append("envelope payload hashes (SHA-256 over payload bytes only):")
    lines.append("  generator_identity_sha256 = %s"
                 % _envelope_hash(payload, "generator_identity_envelope", "generator_identity_sha256"))
    lines.append("  generator_configuration_sha256 = %s"
                 % _envelope_hash(payload, "generator_configuration_envelope",
                                  "generator_configuration_sha256"))
    lines.append("  structural_budget_sha256 = %s"
                 % _envelope_hash(payload, "structural_budget_envelope", "structural_budget_sha256"))
    lines.append("  source_identity_sha256 = %s"
                 % _envelope_hash(payload, "source_identity_envelope", "source_identity_sha256"))
    lines.append("  run1_candidate_stream_sha256 = %s"
                 % _hex_or_absent(payload.get("run1_candidate_stream_sha256")))
    lines.append("  run2_candidate_stream_sha256 = %s"
                 % _hex_or_absent(payload.get("run2_candidate_stream_sha256")))
    stream_envelope = _mapping(payload.get("candidate_stream_envelope"))
    lines.append("  candidate_stream_sha256 = %s"
                 % (_hex_or_absent(stream_envelope.get(STREAM_ENVELOPE_HASH_KEY))
                    if stream_envelope is not None else ABSENT))
    lines.append("  generator_replay_result_sha256 = %s" % _hex_or_absent(replay_payload_hash))
    lines.append("")

    lines.append("artifact file hashes (SHA-256 over complete file bytes; a different byte domain):")
    if file_hashes:
        for filename, digest in file_hashes:
            lines.append("  %s = %s" % (filename, digest))
    else:
        lines.append("  %s" % ABSENT)
    lines.append("")

    lines.append("terminal_status = %s" % (terminal_status if terminal_status is not None else "null"))
    if label == LABEL_REPLAY_FAILURE:
        lines.append("replay_failure_reason = %s" % reason)
    elif label == LABEL_UNRESOLVED:
        lines.append("derived_termination_reason = %s" % UNRESOLVED_REASON)
    else:
        lines.append("derived_termination_reason = %s" % reason)
    lines.append("")

    lines.extend(_counter_lines("run1", _mapping(payload.get("run1_structural_counters"))))
    lines.append("")
    lines.extend(_counter_lines("run2", _mapping(payload.get("run2_structural_counters"))))
    lines.append("")

    if stream is not None:
        count = stream.get("candidate_count")
        lines.append("candidate_count = %s" % (count if _is_strict_int(count) else ABSENT))
    else:
        lines.append("candidate_count = %s" % ABSENT)
    lines.append("failure_code = %s" % (failure_code if failure_code is not None else ABSENT))
    lines.append("failure_stage = %s" % (failure_stage if failure_stage is not None else ABSENT))
    lines.append("")

    lines.append("candidate-stream artifact written = %s" % stream_written)
    if validation_failures:
        for entry in validation_failures:
            lines.append("runner_validation_failure = %s" % entry)
    else:
        lines.append("runner_validation_failure = none")
    lines.append("freezer invoked = False")
    lines.append("PsiTRS invoked = False")
    lines.append("scientific interpretation performed = False")

    return LF.join(lines) + LF


# --------------------------------------------------------------------------------- 7. staging / publication
def _write_bytes(path: str, data: bytes) -> None:
    """Binary write only: the exact serializer-produced bytes reach disk with no text-layer transformation."""
    with open(path, "wb") as handle:
        handle.write(data)


def _safe_write(stream, text: str) -> bool:
    """Best-effort diagnostic write. A failing diagnostic stream must never mask the exit contract."""
    try:
        stream.write(text)
        return True
    except Exception:
        return False


def _cleanup_staging(staging_path: str, stderr) -> bool:
    """Remove staging when safely possible. A retained staging directory blocks future execution by design."""
    if not os.path.exists(staging_path):
        return True
    try:
        shutil.rmtree(staging_path)
        return True
    except OSError as error:
        stderr.write("%s: staging cleanup failed: %s\n" % (RUNNER_NAME, error))
        stderr.write("%s: staging directory retained; it will block future execution until removed\n"
                     % RUNNER_NAME)
        return False


# --------------------------------------------------------------------------------- 8. the operation
def run_operation(results_root: Optional[str] = None, stdout=None, stderr=None) -> int:
    """Perform the complete protocol operation. results_root is test-only and unreachable from the CLI."""
    root = results_root if results_root is not None else default_results_root()
    out = stdout if stdout is not None else sys.stdout
    err = stderr if stderr is not None else sys.stderr
    final_path = final_directory(root)
    staging_path = staging_directory(root)

    # --- pre-execution refusal: checked BEFORE any generator call, so refusal costs nothing ---
    if os.path.exists(final_path):
        err.write("%s: refusing to run; final directory already exists: %s\n"
                  % (RUNNER_NAME, FINAL_DIRECTORY_NAME))
        return EXIT_REFUSED
    if os.path.exists(staging_path):
        err.write("%s: refusing to run; staging directory already exists: %s\n"
                  % (RUNNER_NAME, STAGING_DIRECTORY_NAME))
        return EXIT_REFUSED

    try:
        os.makedirs(staging_path)
    except OSError as error:
        err.write("%s: could not create staging directory: %s\n" % (RUNNER_NAME, error))
        return EXIT_FAILURE

    # --- the sole generator call; generate_candidate_stream is never called, here or anywhere ---
    try:
        replay_envelope = generator.generate_candidate_stream_with_replay(PROFILE_NAME)
    except Exception as error:  # defensive: the frozen generator is documented never to leak
        err.write("%s: generator replay call failed: %r\n" % (RUNNER_NAME, error))
        _cleanup_staging(staging_path, err)
        return EXIT_FAILURE

    # --- canonical serialization of the complete returned envelope ---
    try:
        replay_bytes = cjson.canonical_json_bytes(replay_envelope)
    except (ValueError, TypeError) as error:
        err.write("%s: replay result is not canonically serializable: %r\n" % (RUNNER_NAME, error))
        err.write("%s: no artifact fabricated\n" % RUNNER_NAME)
        _cleanup_staging(staging_path, err)
        return EXIT_FAILURE

    payload = replay_payload_of(replay_envelope)
    if payload is None:
        err.write("%s: replay envelope has no %s payload mapping; no artifact fabricated\n"
                  % (RUNNER_NAME, REPLAY_ENVELOPE_KEY))
        _cleanup_staging(staging_path, err)
        return EXIT_FAILURE

    # The replay envelope's own payload hash, read from the envelope. Passed separately for reporting; no
    # runner-local key is ever inserted into the payload, which is the canonical artifact's own content.
    replay_payload_hash = _mapping(replay_envelope).get(REPLAY_ENVELOPE_HASH_KEY)

    validation_failures: List[str] = []
    label, _reason = derive_termination_reason(payload)
    if label == LABEL_UNRESOLVED:
        validation_failures.append(UNRESOLVED_REASON)

    stream_envelope = payload.get("candidate_stream_envelope")
    permitted = extraction_permitted(payload)
    counter_failure = counter_validation_failure(payload)
    if counter_failure is not None:
        validation_failures.append(counter_failure)
    extract = permitted and counter_failure is None and label != LABEL_UNRESOLVED

    # --- build the complete permitted set inside staging; nothing outside staging is touched ---
    file_hashes: List[Tuple[str, str]] = []
    try:
        _write_bytes(os.path.join(staging_path, REPLAY_RESULT_FILENAME), replay_bytes)
        file_hashes.append((REPLAY_RESULT_FILENAME, file_sha256(replay_bytes)))

        if extract:
            stream_bytes = cjson.canonical_json_bytes(stream_envelope)
            _write_bytes(os.path.join(staging_path, CANDIDATE_STREAM_FILENAME), stream_bytes)
            file_hashes.append((CANDIDATE_STREAM_FILENAME, file_sha256(stream_bytes)))

        summary_text = build_summary_text(payload, replay_payload_hash, file_hashes, extract,
                                          validation_failures)
        _write_bytes(os.path.join(staging_path, SUMMARY_FILENAME), summary_text.encode("utf-8"))
    except (ValueError, TypeError) as error:
        err.write("%s: artifact serialization failed: %r\n" % (RUNNER_NAME, error))
        _cleanup_staging(staging_path, err)
        return EXIT_FAILURE
    except OSError as error:
        err.write("%s: artifact write failed: %r\n" % (RUNNER_NAME, error))
        _cleanup_staging(staging_path, err)
        return EXIT_FAILURE

    # --- single publication event ---
    try:
        os.rename(staging_path, final_path)
    except OSError as error:
        err.write("%s: atomic publication failed: %r\n" % (RUNNER_NAME, error))
        _cleanup_staging(staging_path, err)
        return EXIT_FAILURE

    # --- published. Nothing below may delete, roll back, or re-stage the final artifact set. ---
    try:
        out.write(summary_text)
    except Exception as error:
        _safe_write(err, "%s: stdout mirroring failed after publication: %r\n" % (RUNNER_NAME, error))
        _safe_write(err, "%s: the published artifact set is intact and was not rolled back\n" % RUNNER_NAME)
        return EXIT_FAILURE

    if validation_failures:
        _safe_write(err, "%s: runner protocol validation failed: %s\n"
                    % (RUNNER_NAME, ", ".join(validation_failures)))
        return EXIT_FAILURE
    return EXIT_PUBLISHED


# --------------------------------------------------------------------------------- 9. entry point
def main(argv: Optional[List[str]] = None) -> int:
    """No CLI surface. Any argument is a runner validation failure, not a refusal."""
    arguments = (argv if argv is not None else sys.argv)[1:]
    if arguments:
        sys.stderr.write("%s: takes no arguments; invoke exactly:\n" % RUNNER_NAME)
        sys.stderr.write("  python research\\brainvision\\%s.py\n" % RUNNER_NAME)
        return EXIT_FAILURE
    return run_operation()


if __name__ == "__main__":
    sys.exit(main())

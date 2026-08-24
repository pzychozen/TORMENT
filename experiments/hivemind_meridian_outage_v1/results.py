"""Append-only result writing and fail-closed Meridian evidence verification."""
from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .spec import (
    EXPERIMENT_VERSION,
    FROZEN_BASELINE_COMMIT,
    VALID_CONDITIONS,
    VALID_N,
    assignment_manifest,
    assignment_manifest_sha256,
    agent_view,
    corpus_sha256,
    ground_truth_sha256,
    payload_sha256,
)


RESULT_SCHEMA_VERSION = "meridian-result-v2"
SEAL_INDEX_FILENAME = "meridian-seal-index.jsonl"
RESULT_SCHEMA_PREREGISTRATION = {
    "B1_TORMENT_MECHANISMS_ONLY": (
        "Mechanism/state-formation measurement only; byte-identical provider input to A_PRIVATE "
        "except provider nondeterminism, and not evidence of collective cognition."
    ),
    "deterministic_union_score": [
        "ORACLE-LIKE POPULATION UPPER BOUND",
        "NOT AN AGENT ANSWER",
        "NOT COLLECTIVE COGNITION",
    ],
    "N5": (
        "Every agent receives one decisive card; mechanics characterization only, with no "
        "intelligence, efficacy, salience, scaling, or efficiency claim."
    ),
}
_B2_CONTEXT_TOP_LEVEL_KEYS = frozenset({"recent_events", "event_count"})
_B2_EVENT_KEYS = frozenset({
    "event_id", "workspace_id", "domain_id", "ts_start", "ts_end",
    "participating_agents", "source_packets", "source_eids", "confidence",
    "persistence", "semantic_overlap", "phase_alignment", "symbol_alignment",
    "dominant_motifs", "dominant_symbol", "dominant_cycle_stage",
    "dominant_identity_state", "summary", "policy_flags",
})
_SENSITIVE_EVIDENCE_KEYS = frozenset({
    "api_key", "apikey", "authorization", "credential", "credentials", "password", "secret", "token",
})
_SAMPLING_FIELDS = frozenset({"max_tokens", "temperature", "top_p", "top_k", "thinking", "timeout"})


class ResultVerificationError(ValueError):
    """Raised when an experiment artifact is missing, malformed, or rewritten."""


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ResultVerificationError(f"cannot read JSON evidence {path.name}: {exc}") from exc


def _write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_seal_index(index_path: Path) -> list[dict[str, Any]]:
    if not index_path.exists():
        return []
    try:
        rows = [json.loads(line) for line in index_path.read_text(encoding="utf-8").splitlines() if line]
    except (OSError, json.JSONDecodeError) as exc:
        raise ResultVerificationError(f"cannot read external seal index: {exc}") from exc
    if not all(isinstance(row, dict) for row in rows):
        raise ResultVerificationError("external seal index contains a malformed row")
    return rows


def _append_seal_index(index_path: Path, row: dict[str, Any]) -> None:
    existing = _read_seal_index(index_path)
    if any(existing_row.get("run_id") == row["run_id"] for existing_row in existing):
        raise FileExistsError(f"duplicate experiment run ID in external seal index: {row['run_id']}")
    with index_path.open("a", encoding="utf-8", newline="\n") as index_file:
        index_file.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _validate_run_identity(result: dict[str, Any]) -> None:
    required = {
        "schema_version",
        "run_status",
        "run_id",
        "experiment_version",
        "baseline",
        "condition",
        "n_agents",
        "seed",
        "corpus_sha256",
        "ground_truth_sha256",
        "assignment_manifest_sha256",
        "provider",
        "model_call_evidence",
        "environment",
        "timing",
        "task_metrics",
        "mechanism_metrics",
        "cost_metrics",
        "failure_ledger",
        "visibility_ledger",
        "artifact_hashes",
        "result_timestamp",
        "preregistration",
    }
    missing = sorted(required - set(result))
    if missing:
        raise ResultVerificationError(f"result missing required fields: {missing}")
    if result["schema_version"] != RESULT_SCHEMA_VERSION:
        raise ResultVerificationError("unexpected result schema version")
    if result["preregistration"] != RESULT_SCHEMA_PREREGISTRATION:
        raise ResultVerificationError("result preregistration language mismatch")
    if result["experiment_version"] != EXPERIMENT_VERSION:
        raise ResultVerificationError("unexpected experiment version")
    if result["condition"] not in VALID_CONDITIONS:
        raise ResultVerificationError("invalid condition")
    if result["n_agents"] not in VALID_N:
        raise ResultVerificationError("invalid N")
    if not isinstance(result["run_id"], str) or not result["run_id"]:
        raise ResultVerificationError("run_id must be a non-empty string")
    if not isinstance(result["result_timestamp"], str) or not result["result_timestamp"]:
        raise ResultVerificationError("result timestamp is missing")
    if result["corpus_sha256"] != corpus_sha256():
        raise ResultVerificationError("corpus hash mismatch")
    if result["ground_truth_sha256"] != ground_truth_sha256():
        raise ResultVerificationError("ground truth hash mismatch")
    if result["assignment_manifest_sha256"] != assignment_manifest_sha256(result["n_agents"]):
        raise ResultVerificationError("assignment manifest hash mismatch")

    provider = result["provider"]
    if not isinstance(provider, dict):
        raise ResultVerificationError("provider metadata must be a mapping")
    missing_provider = sorted({
        "provider", "model_id", "provider_mode", "session_isolation", "retry_policy", "sampling",
    } - set(provider))
    if missing_provider:
        raise ResultVerificationError(f"provider metadata missing required fields: {missing_provider}")
    if provider.get("provider_mode") not in {"dry", "live"}:
        raise ResultVerificationError("provider metadata has invalid provider mode")
    if provider.get("session_isolation") != "per_agent_per_round":
        raise ResultVerificationError("invalid shared provider session isolation")
    if provider.get("retry_policy") != "none":
        raise ResultVerificationError("Meridian retry policy must be none")
    sampling = provider.get("sampling")
    if not isinstance(sampling, dict) or set(sampling) != _SAMPLING_FIELDS | {"system_instruction"}:
        raise ResultVerificationError("provider sampling configuration is incomplete")
    for field in _SAMPLING_FIELDS:
        sampling_field = sampling[field]
        if not isinstance(sampling_field, dict) or set(sampling_field) != {"mode", "explicit_value"}:
            raise ResultVerificationError(f"provider sampling {field} is malformed")
        if sampling_field.get("mode") not in {"explicit", "provider_default"}:
            raise ResultVerificationError(f"provider sampling {field} has invalid mode")
        if sampling_field.get("mode") == "provider_default" and sampling_field.get("explicit_value") is not None:
            raise ResultVerificationError(f"provider-default sampling {field} invents a value")
        if sampling_field.get("mode") == "explicit" and sampling_field.get("explicit_value") is None:
            raise ResultVerificationError(f"explicit sampling {field} is missing a value")
    system_instruction = sampling["system_instruction"]
    if not isinstance(system_instruction, dict) or set(system_instruction) != {"mode", "sha256"}:
        raise ResultVerificationError("provider system instruction identity is malformed")
    if system_instruction.get("mode") != "harness_instruction" or not isinstance(system_instruction.get("sha256"), str):
        raise ResultVerificationError("provider system instruction identity is incomplete")

    run_status = result.get("run_status")
    if run_status not in {"COMPLETE", "FAILED"}:
        raise ResultVerificationError("run status must be COMPLETE or FAILED")
    call_evidence = result.get("model_call_evidence")
    required_call_evidence = {
        "live_model_calls_performed",
        "logical_model_call_count_planned",
        "characterization_logical_model_call_count_planned",
        "logical_model_call_count_attempted",
        "logical_model_call_count_succeeded",
        "logical_model_call_count_failed",
        "retry_count",
        "hidden_evaluator_model_calls",
        "maximum_attempts_per_logical_call",
    }
    if not isinstance(call_evidence, dict) or set(call_evidence) != required_call_evidence:
        raise ResultVerificationError("model call evidence is incomplete")
    if not isinstance(call_evidence["live_model_calls_performed"], bool):
        raise ResultVerificationError("live model call evidence must be boolean")
    for field in required_call_evidence - {"live_model_calls_performed"}:
        if not isinstance(call_evidence[field], int) or call_evidence[field] < 0:
            raise ResultVerificationError(f"model call evidence {field} is malformed")
    if call_evidence["logical_model_call_count_planned"] != 2 * result["n_agents"]:
        raise ResultVerificationError("run-level planned model call count is incorrect")
    if call_evidence["characterization_logical_model_call_count_planned"] != 8 * result["n_agents"]:
        raise ResultVerificationError("characterization planned model call count is incorrect")
    if call_evidence["logical_model_call_count_attempted"] != (
        call_evidence["logical_model_call_count_succeeded"] + call_evidence["logical_model_call_count_failed"]
    ):
        raise ResultVerificationError("model call evidence counts do not reconcile")
    if call_evidence["retry_count"] != 0 or call_evidence["maximum_attempts_per_logical_call"] != 1:
        raise ResultVerificationError("Meridian v1 evidence permits no retries")
    if call_evidence["hidden_evaluator_model_calls"] != 0:
        raise ResultVerificationError("Meridian v1 permits no hidden evaluator model calls")
    expected_live = provider["provider_mode"] == "live" and call_evidence["logical_model_call_count_attempted"] > 0
    if call_evidence["live_model_calls_performed"] is not expected_live:
        raise ResultVerificationError("live model call evidence does not match provider attempts")
    if not isinstance(result["failure_ledger"], list):
        raise ResultVerificationError("failure ledger must be a list")
    if run_status == "COMPLETE":
        if call_evidence["logical_model_call_count_attempted"] != call_evidence["logical_model_call_count_planned"]:
            raise ResultVerificationError("complete run has unexecuted provider calls")
        if call_evidence["logical_model_call_count_failed"] != 0:
            raise ResultVerificationError("complete run records failed provider calls")
        if result["failure_ledger"]:
            raise ResultVerificationError("complete run records failure evidence")
        if result["task_metrics"] is None or result["mechanism_metrics"] is None:
            raise ResultVerificationError("complete run is missing scored metrics")
    else:
        if not result["failure_ledger"]:
            raise ResultVerificationError("failed run is missing failure evidence")
        required_failure_fields = {
            "stage", "logical_call_id", "error_type", "message",
            "unexecuted_logical_call_count", "condition_partially_administered",
        }
        for failure in result["failure_ledger"]:
            if not isinstance(failure, dict) or set(failure) != required_failure_fields:
                raise ResultVerificationError("failed run failure evidence is malformed")
            if failure["stage"] not in {"provider_or_schema", "harness_or_evidence"}:
                raise ResultVerificationError("failed run has an invalid failure stage")
            if failure["logical_call_id"] is not None and not isinstance(failure["logical_call_id"], str):
                raise ResultVerificationError("failed run logical call ID is malformed")
            if not isinstance(failure["error_type"], str) or not isinstance(failure["message"], str):
                raise ResultVerificationError("failed run exception evidence is malformed")
            if failure["unexecuted_logical_call_count"] != (
                call_evidence["logical_model_call_count_planned"]
                - call_evidence["logical_model_call_count_attempted"]
            ):
                raise ResultVerificationError("failed run unexecuted-call count is inconsistent")
            if not isinstance(failure["condition_partially_administered"], bool):
                raise ResultVerificationError("failed run partial-condition flag is malformed")
        if result["task_metrics"] is not None or result["mechanism_metrics"] is not None:
            raise ResultVerificationError("failed run must not be classified with complete metrics")

    baseline = result["baseline"]
    if not isinstance(baseline, dict):
        raise ResultVerificationError("baseline must be a mapping")
    if baseline.get("frozen_implementation_commit") != FROZEN_BASELINE_COMMIT:
        raise ResultVerificationError("frozen implementation commit mismatch")
    execution_commit = baseline.get("execution_commit")
    if not isinstance(execution_commit, str) or not execution_commit:
        raise ResultVerificationError("execution commit missing")
    if execution_commit != FROZEN_BASELINE_COMMIT:
        successor_kind = baseline.get("successor_kind")
        if successor_kind != "instrumentation_only":
            raise ResultVerificationError("successor baseline lacks explicit allowed classification")


def _validate_condition_visibility(result: dict[str, Any]) -> None:
    manifest = assignment_manifest(result["n_agents"])
    assignments = manifest["assignments"]
    records = result["visibility_ledger"]
    if not isinstance(records, list):
        raise ResultVerificationError("visibility ledger must be a list")
    condition = result["condition"]
    expected_config = {
        "A_PRIVATE": (False, False, False, False),
        "B1_TORMENT_MECHANISMS_ONLY": (True, True, False, False),
        "B2_TORMENT_SALIENCE_SURFACED": (True, True, True, False),
        "C_NAIVE_SHARED_CONTENT": (False, False, False, True),
    }[condition]
    condition_config = result.get("condition_config")
    if not isinstance(condition_config, dict):
        raise ResultVerificationError("condition configuration missing")
    actual_config = (
        bool(condition_config.get("hivemind_enabled")),
        bool(condition_config.get("telemetry_enabled")),
        bool(condition_config.get("collective_context_surfaced")),
        bool(condition_config.get("naive_shared_content")),
    )
    if actual_config != expected_config:
        raise ResultVerificationError("condition configuration violates frozen condition isolation")

    observed_pairs: set[tuple[int, str]] = set()
    for record in records:
        if not isinstance(record, dict):
            raise ResultVerificationError("visibility record must be a mapping")
        agent_id = record.get("agent_id")
        if agent_id not in assignments:
            raise ResultVerificationError("visibility record has unknown agent")
        round_number = record.get("round")
        if round_number not in {1, 2}:
            raise ResultVerificationError("visibility record has invalid round")
        pair = (round_number, agent_id)
        if pair in observed_pairs:
            raise ResultVerificationError("visibility ledger has a duplicate provider call")
        observed_pairs.add(pair)
        assigned = set(assignments[agent_id])
        visible = set(record.get("assigned_card_ids", []))
        if visible != assigned:
            raise ResultVerificationError("agent assignment view was changed")
        shared_card_ids = set(record.get("naive_shared_card_ids", []))
        surfaced = bool(record.get("collective_context_surfaced"))
        if condition in {"A_PRIVATE", "B1_TORMENT_MECHANISMS_ONLY"}:
            if shared_card_ids or surfaced:
                raise ResultVerificationError("private/current condition received forbidden sharing")
        elif condition == "B2_TORMENT_SALIENCE_SURFACED":
            if shared_card_ids:
                raise ResultVerificationError("B2 received naive shared card content")
            if record.get("round") == 2 and not surfaced:
                raise ResultVerificationError("B2 round 2 did not surface collective context")
        elif condition == "C_NAIVE_SHARED_CONTENT":
            if surfaced:
                raise ResultVerificationError("C received Hivemind collective context")
            if record.get("round") == 2 and not shared_card_ids:
                raise ResultVerificationError("C round 2 did not receive declared naive sharing")
            if not shared_card_ids.issubset({
                card_id for card_ids in assignments.values() for card_id in card_ids
            }):
                raise ResultVerificationError("C declared an unknown shared card")
    if result["run_status"] == "COMPLETE":
        expected_pairs = {
            (round_number, agent_id)
            for round_number in (1, 2)
            for agent_id in assignments
        }
        if observed_pairs != expected_pairs:
            raise ResultVerificationError("complete run visibility ledger is incomplete")


def _output_card_ids(output: object) -> set[str]:
    if not isinstance(output, dict):
        raise ResultVerificationError("raw provider output must be a mapping")
    card_ids: set[str] = set()
    for key in ("findings", "claims"):
        rows = output.get(key, [])
        if not isinstance(rows, list):
            raise ResultVerificationError(f"raw provider {key} must be a list")
        for row in rows:
            if not isinstance(row, dict):
                raise ResultVerificationError(f"raw provider {key} row must be a mapping")
            values = row.get("card_ids", [])
            if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
                raise ResultVerificationError(f"raw provider {key} card IDs are malformed")
            card_ids.update(values)
            if key == "claims":
                if row.get("stance") not in {"asserts", "refutes", "mentions"}:
                    raise ResultVerificationError("raw provider claim stance is missing or invalid")
    final_answer = output.get("final_answer", {})
    if not isinstance(final_answer, dict):
        raise ResultVerificationError("raw provider final answer must be a mapping")
    values = final_answer.get("cited_card_ids", [])
    if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
        raise ResultVerificationError("raw provider final citations are malformed")
    card_ids.update(values)
    return card_ids


def _validate_b2_collective_context(context: object) -> None:
    if not isinstance(context, dict):
        raise ResultVerificationError("B2 collective context must be a mapping")
    unexpected = set(context) - _B2_CONTEXT_TOP_LEVEL_KEYS
    if unexpected:
        raise ResultVerificationError(f"B2 collective context has forbidden fields: {sorted(unexpected)}")
    events = context.get("recent_events", [])
    if not isinstance(events, list):
        raise ResultVerificationError("B2 recent_events must be a list")
    if "event_count" in context and not isinstance(context["event_count"], int):
        raise ResultVerificationError("B2 event_count must be an integer")
    for event in events:
        if not isinstance(event, dict):
            raise ResultVerificationError("B2 recent event must be a mapping")
        event_unexpected = set(event) - _B2_EVENT_KEYS
        if event_unexpected:
            raise ResultVerificationError(
                f"B2 recent event has forbidden fields: {sorted(event_unexpected)}"
            )
    serialized_context = json.dumps(context, ensure_ascii=False, sort_keys=True)
    for card in agent_view():
        if card["text"] in serialized_context:
            raise ResultVerificationError("B2 collective context exposes corpus card text")


def _expected_c_shared_pool(round_outputs: Mapping[str, Any]) -> list[dict[str, Any]]:
    pool: list[dict[str, Any]] = []
    for key, output in sorted(round_outputs.items()):
        if not key.startswith("round_1:"):
            continue
        agent_id = key.split(":", 1)[1]
        if not isinstance(output, dict) or not isinstance(output.get("findings", []), list):
            raise ResultVerificationError("C round-one findings are malformed")
        for finding in output["findings"]:
            if not isinstance(finding, dict):
                raise ResultVerificationError("C round-one finding is malformed")
            card_ids = finding.get("card_ids", [])
            if not isinstance(card_ids, list) or not all(isinstance(card_id, str) for card_id in card_ids):
                raise ResultVerificationError("C round-one finding citations are malformed")
            if card_ids:
                pool.append({
                    "agent_id": agent_id,
                    "text": str(finding.get("text", "")),
                    "card_ids": list(card_ids),
                })
    return sorted(pool, key=lambda item: (item["agent_id"], item["text"], item["card_ids"]))


def _has_sensitive_evidence_key(value: object) -> bool:
    if isinstance(value, dict):
        return any(
            str(key).lower() in _SENSITIVE_EVIDENCE_KEYS or _has_sensitive_evidence_key(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_has_sensitive_evidence_key(item) for item in value)
    return False


def _validate_provider_attempts(result: dict[str, Any], raw_outputs: dict[str, Any]) -> set[str]:
    attempts = raw_outputs.get("provider_attempts")
    if not isinstance(attempts, list):
        raise ResultVerificationError("raw provider attempt evidence is missing")
    if _has_sensitive_evidence_key(result["provider"]) or _has_sensitive_evidence_key(attempts):
        raise ResultVerificationError("provider evidence contains a credential-shaped field")
    expected_attempted = result["model_call_evidence"]["logical_model_call_count_attempted"]
    if len(attempts) != expected_attempted:
        raise ResultVerificationError("provider attempt evidence count does not match result")
    successful_keys: set[str] = set()
    expected_hash_keys = {
        "base_instruction_sha256",
        "assigned_cards_sha256",
        "round_number_sha256",
        "collective_context_sha256",
        "naive_shared_findings_sha256",
        "provider_visible_input_sha256",
    }
    assignments = assignment_manifest(result["n_agents"])["assignments"]
    logical_call_ids: set[str] = set()
    for sequence, attempt in enumerate(attempts, start=1):
        if not isinstance(attempt, dict):
            raise ResultVerificationError("provider attempt must be a mapping")
        required = {
            "run_id", "condition", "n_agents", "seed", "round_number", "agent_id",
            "logical_call_id", "attempt_number", "sequence", "timestamp", "provider",
            "request_metadata", "raw_response_text", "response_metadata", "usage",
            "parser_schema_outcome", "success", "failure_stage", "exception",
        }
        if set(attempt) != required:
            raise ResultVerificationError("provider attempt evidence has missing or unexpected fields")
        if (
            attempt["run_id"] != result["run_id"]
            or attempt["condition"] != result["condition"]
            or attempt["n_agents"] != result["n_agents"]
            or attempt["seed"] != result["seed"]
            or attempt["sequence"] != sequence
            or attempt["attempt_number"] != 1
        ):
            raise ResultVerificationError("provider attempt identity is inconsistent")
        if attempt["provider"] != result["provider"]:
            raise ResultVerificationError("provider attempt metadata differs from result metadata")
        if attempt["round_number"] not in {1, 2} or attempt["agent_id"] not in assignments:
            raise ResultVerificationError("provider attempt has invalid round or agent")
        if attempt["logical_call_id"] != f"round_{attempt['round_number']}:{attempt['agent_id']}":
            raise ResultVerificationError("provider attempt logical call ID is malformed")
        if attempt["logical_call_id"] in logical_call_ids:
            raise ResultVerificationError("Meridian retry policy permits only one attempt per logical call")
        logical_call_ids.add(attempt["logical_call_id"])
        request_metadata = attempt["request_metadata"]
        if not isinstance(request_metadata, dict) or set(request_metadata) != {
            "input_hashes", "assigned_card_ids", "provider_visible_prompt_sha256",
        }:
            raise ResultVerificationError("provider request metadata is malformed")
        prompt_hash = request_metadata["provider_visible_prompt_sha256"]
        if prompt_hash is not None and not isinstance(prompt_hash, str):
            raise ResultVerificationError("provider-visible prompt hash is malformed")
        input_hashes = request_metadata["input_hashes"]
        if not isinstance(input_hashes, dict) or set(input_hashes) != expected_hash_keys:
            raise ResultVerificationError("provider input hash evidence is incomplete")
        if not all(value is None or isinstance(value, str) for value in input_hashes.values()):
            raise ResultVerificationError("provider input hash evidence is malformed")
        usage = attempt["usage"]
        if not isinstance(usage, dict) or set(usage) != {
            "availability", "input_tokens", "output_tokens", "total_tokens",
        }:
            raise ResultVerificationError("provider usage evidence is malformed")
        if usage["availability"] not in {"unavailable", "provider_reported"}:
            raise ResultVerificationError("provider usage availability is malformed")
        if not all(value is None or (isinstance(value, int) and value >= 0) for key, value in usage.items() if key != "availability"):
            raise ResultVerificationError("provider usage values are malformed")
        if attempt["raw_response_text"] is not None and not isinstance(attempt["raw_response_text"], str):
            raise ResultVerificationError("provider raw response text is malformed")
        if not isinstance(attempt["response_metadata"], dict):
            raise ResultVerificationError("provider response metadata is malformed")
        if not isinstance(attempt["success"], bool):
            raise ResultVerificationError("provider attempt success is malformed")
        if attempt["success"]:
            if (
                attempt["parser_schema_outcome"] != "valid"
                or attempt["failure_stage"] is not None
                or attempt["exception"] is not None
            ):
                raise ResultVerificationError("successful provider attempt has failure evidence")
            successful_keys.add(f"round_{attempt['round_number']}:{attempt['agent_id']}")
        else:
            exception = attempt["exception"]
            if (
                attempt["parser_schema_outcome"] != "failed"
                or attempt["failure_stage"] not in {"provider_invocation", "parser_schema"}
                or not isinstance(exception, dict)
                or set(exception) != {"type", "message"}
                or not isinstance(exception["type"], str)
                or not isinstance(exception["message"], str)
            ):
                raise ResultVerificationError("failed provider attempt lacks parser or exception evidence")
    succeeded = result["model_call_evidence"]["logical_model_call_count_succeeded"]
    if len(successful_keys) != succeeded:
        raise ResultVerificationError("successful provider attempt evidence count does not match result")
    return successful_keys


def _validate_raw_output_visibility(result: dict[str, Any], raw_outputs: object) -> None:
    if not isinstance(raw_outputs, dict) or not isinstance(raw_outputs.get("round_outputs"), dict):
        raise ResultVerificationError("raw round outputs are missing")
    if not isinstance(raw_outputs.get("round_inputs"), dict):
        raise ResultVerificationError("raw provider inputs are missing")
    if raw_outputs.get("research_instruction") is None or "final_answer" not in raw_outputs:
        raise ResultVerificationError("raw provider evidence is incomplete")
    if _has_sensitive_evidence_key(raw_outputs):
        raise ResultVerificationError("raw provider evidence contains a credential-shaped field")
    round_outputs = raw_outputs["round_outputs"]
    round_inputs = raw_outputs["round_inputs"]
    if set(round_inputs) != set(round_outputs):
        raise ResultVerificationError("raw provider input/output keys do not match")
    successful_keys = _validate_provider_attempts(result, raw_outputs)
    if set(round_outputs) != successful_keys:
        raise ResultVerificationError("raw provider outputs do not match successful provider attempts")
    if result["run_status"] == "FAILED":
        if raw_outputs["final_answer"] is not None:
            raise ResultVerificationError("failed run must not fabricate a final answer")
        return
    assignments = assignment_manifest(result["n_agents"])["assignments"]
    visibility = {
        (record["round"], record["agent_id"]): record
        for record in result["visibility_ledger"]
    }
    condition = result["condition"]
    naive_shared_from_round_one: set[str] = set()
    if condition == "C_NAIVE_SHARED_CONTENT":
        for key, output in round_outputs.items():
            if not key.startswith("round_1:"):
                continue
            if not isinstance(output, dict) or not isinstance(output.get("findings", []), list):
                raise ResultVerificationError("C round-one findings are malformed")
            for finding in output["findings"]:
                if not isinstance(finding, dict):
                    raise ResultVerificationError("C round-one finding is malformed")
                card_ids = finding.get("card_ids", [])
                if not isinstance(card_ids, list) or not all(isinstance(card_id, str) for card_id in card_ids):
                    raise ResultVerificationError("C round-one finding citations are malformed")
                naive_shared_from_round_one.update(card_ids)
        expected_pool = _expected_c_shared_pool(round_outputs)
    else:
        expected_pool = []
    for key, output in round_outputs.items():
        try:
            round_label, agent_id = key.split(":", 1)
            round_number = int(round_label.removeprefix("round_"))
        except (AttributeError, ValueError) as exc:
            raise ResultVerificationError("malformed raw output key") from exc
        record = visibility.get((round_number, agent_id))
        if record is None:
            raise ResultVerificationError("raw output lacks visibility record")
        input_payload = round_inputs[key]
        if not isinstance(input_payload, dict):
            raise ResultVerificationError("raw provider input must be a mapping")
        if set(input_payload) != {
            "base_instruction", "assigned_cards", "round_number", "collective_context",
            "naive_shared_findings", "input_hashes",
        }:
            raise ResultVerificationError("raw provider input has forbidden fields")
        if input_payload["round_number"] != round_number:
            raise ResultVerificationError("raw provider input round differs from output key")
        if not isinstance(input_payload["assigned_cards"], list):
            raise ResultVerificationError("raw provider input cards are malformed")
        if [card.get("card_id") for card in input_payload["assigned_cards"] if isinstance(card, dict)] != list(assignments[agent_id]):
            raise ResultVerificationError("raw provider input cards differ from assignment")
        input_hashes = input_payload["input_hashes"]
        expected_hashes = {
            "base_instruction_sha256": payload_sha256(input_payload["base_instruction"]),
            "assigned_cards_sha256": payload_sha256(input_payload["assigned_cards"]),
            "round_number_sha256": payload_sha256(input_payload["round_number"]),
            "collective_context_sha256": (
                payload_sha256(input_payload["collective_context"])
                if input_payload["collective_context"] is not None else None
            ),
            "naive_shared_findings_sha256": (
                payload_sha256(input_payload["naive_shared_findings"])
                if input_payload["naive_shared_findings"] else None
            ),
        }
        expected_hashes["provider_visible_input_sha256"] = payload_sha256({
            key: value for key, value in input_payload.items() if key != "input_hashes"
        })
        if input_hashes != expected_hashes:
            raise ResultVerificationError("raw provider input hashes do not match input")
        attempt = next(
            item for item in raw_outputs["provider_attempts"]
            if item["logical_call_id"] == f"round_{round_number}:{agent_id}"
        )
        if attempt["request_metadata"]["input_hashes"] != input_hashes:
            raise ResultVerificationError("provider attempt input hashes do not match raw input")
        if condition == "B2_TORMENT_SALIENCE_SURFACED" and round_number == 2:
            _validate_b2_collective_context(input_payload.get("collective_context"))
        elif input_payload.get("collective_context") is not None:
            raise ResultVerificationError("non-B2 provider input received collective context")
        if condition == "C_NAIVE_SHARED_CONTENT" and round_number == 2:
            shared_pool = input_payload.get("naive_shared_findings")
            if shared_pool != expected_pool:
                raise ResultVerificationError("C shared pool is not exactly actual round-one findings")
            if not all(
                isinstance(finding, dict) and set(finding) == {"agent_id", "text", "card_ids"}
                for finding in shared_pool
            ):
                raise ResultVerificationError("C shared pool contains forbidden evaluator fields")
        elif input_payload.get("naive_shared_findings") not in ([], None):
            raise ResultVerificationError("non-C provider input received naive shared content")
        allowed = set(assignments[agent_id])
        if condition == "C_NAIVE_SHARED_CONTENT" and round_number == 2:
            declared_shared = set(record.get("naive_shared_card_ids", []))
            if declared_shared != naive_shared_from_round_one:
                raise ResultVerificationError("C shared content does not match cited round-one findings")
            allowed.update(declared_shared)
        cited = _output_card_ids(output)
        if not cited.issubset(allowed):
            raise ResultVerificationError("agent output cites a card outside its permitted view")


def validate_result_schema(result: dict[str, Any]) -> None:
    """Validate static identity and condition isolation without accepting partial evidence."""
    if not isinstance(result, dict):
        raise ResultVerificationError("result must be a mapping")
    _validate_run_identity(result)
    _validate_condition_visibility(result)


def write_sealed_run(
    output_root: Path,
    *,
    result: dict[str, Any],
    raw_outputs: dict[str, Any],
    telemetry_records: list[dict[str, Any]],
) -> Path:
    """Write one immutable result directory; existing run IDs are rejected."""
    result_payload = copy.deepcopy(result)
    run_id = result_payload.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        raise ResultVerificationError("run_id is required before writing evidence")
    result_payload.setdefault("result_timestamp", datetime.now(timezone.utc).isoformat())
    output_root.mkdir(parents=True, exist_ok=True)
    index_path = output_root / SEAL_INDEX_FILENAME
    if any(row.get("run_id") == run_id for row in _read_seal_index(index_path)):
        raise FileExistsError(f"duplicate experiment run ID in external seal index: {run_id}")
    run_dir = output_root / run_id
    if run_dir.exists():
        raise FileExistsError(f"duplicate experiment run ID: {run_id}")
    result_payload["artifact_hashes"] = {
        "raw_outputs.json": payload_sha256(raw_outputs),
        "telemetry.json": payload_sha256(telemetry_records),
    }
    validate_result_schema(result_payload)
    _validate_raw_output_visibility(result_payload, raw_outputs)
    run_dir.mkdir(parents=True, exist_ok=False)

    raw_path = run_dir / "raw_outputs.json"
    telemetry_path = run_dir / "telemetry.json"
    _write_json(raw_path, raw_outputs)
    _write_json(telemetry_path, telemetry_records)
    result_path = run_dir / "result.json"
    _write_json(result_path, result_payload)
    seal = {
        "schema_version": "meridian-seal-v2",
        "run_id": run_id,
        "artifact_hashes": {
            "raw_outputs.json": payload_sha256(_read_json(raw_path)),
            "telemetry.json": payload_sha256(_read_json(telemetry_path)),
            "result.json": payload_sha256(_read_json(result_path)),
        },
    }
    _write_json(run_dir / "SEALED.json", seal)
    _append_seal_index(index_path, {
        "run_id": run_id,
        "run_status": result_payload["run_status"],
        "condition": result_payload["condition"],
        "n_agents": result_payload["n_agents"],
        "seed": result_payload["seed"],
        "sealed_json_sha256": _file_sha256(run_dir / "SEALED.json"),
        "result_timestamp": result_payload["result_timestamp"],
    })
    return run_dir


def verify_sealed_run(run_dir: Path, *, require_complete: bool = False) -> dict[str, Any]:
    """Fail closed if required evidence is absent, mismatched, or rewritten."""
    required_paths = {
        name: run_dir / name
        for name in ("raw_outputs.json", "telemetry.json", "result.json", "SEALED.json")
    }
    missing = [name for name, path in required_paths.items() if not path.is_file()]
    if missing:
        raise ResultVerificationError(f"required evidence missing: {sorted(missing)}")
    raw_outputs = _read_json(required_paths["raw_outputs.json"])
    telemetry_records = _read_json(required_paths["telemetry.json"])
    result = _read_json(required_paths["result.json"])
    seal = _read_json(required_paths["SEALED.json"])
    if not isinstance(seal, dict) or seal.get("schema_version") != "meridian-seal-v2":
        raise ResultVerificationError("invalid evidence seal")
    if seal.get("run_id") != result.get("run_id"):
        raise ResultVerificationError("seal run ID mismatch")
    expected_hashes = {
        "raw_outputs.json": payload_sha256(raw_outputs),
        "telemetry.json": payload_sha256(telemetry_records),
        "result.json": payload_sha256(result),
    }
    if seal.get("artifact_hashes") != expected_hashes:
        raise ResultVerificationError("sealed artifact hash mismatch")
    if result.get("artifact_hashes") != {
        "raw_outputs.json": expected_hashes["raw_outputs.json"],
        "telemetry.json": expected_hashes["telemetry.json"],
    }:
        raise ResultVerificationError("result artifact hash mismatch")
    validate_result_schema(result)
    _validate_raw_output_visibility(result, raw_outputs)
    if require_complete and result["run_status"] != "COMPLETE":
        raise ResultVerificationError("failed evidence artifact is not a completed experiment")
    index_rows = _read_seal_index(run_dir.parent / SEAL_INDEX_FILENAME)
    matching_rows = [row for row in index_rows if row.get("run_id") == result["run_id"]]
    if len(matching_rows) != 1:
        raise ResultVerificationError("external seal index does not uniquely anchor this run")
    expected_index = {
        "run_id": result["run_id"],
        "run_status": result["run_status"],
        "condition": result["condition"],
        "n_agents": result["n_agents"],
        "seed": result["seed"],
        "sealed_json_sha256": _file_sha256(required_paths["SEALED.json"]),
        "result_timestamp": result["result_timestamp"],
    }
    if matching_rows[0] != expected_index:
        raise ResultVerificationError("external seal index entry mismatch")
    return result

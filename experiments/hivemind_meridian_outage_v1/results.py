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


RESULT_SCHEMA_VERSION = "meridian-result-v1"
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
    missing_provider = sorted({"model_id", "session_isolation", "retry_policy"} - set(provider))
    if missing_provider:
        raise ResultVerificationError(f"provider metadata missing required fields: {missing_provider}")
    if provider.get("session_isolation") not in {"per_agent_per_round", "per_agent"}:
        raise ResultVerificationError("invalid shared provider session isolation")
    retry_count = provider.get("retry_count")
    if retry_count is not None:
        if not isinstance(retry_count, int) or retry_count < 0:
            raise ResultVerificationError("provider retry_count is malformed")
    elif provider.get("retry_observability") != "unavailable":
        raise ResultVerificationError("provider retry observability is missing")

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

    for record in records:
        if not isinstance(record, dict):
            raise ResultVerificationError("visibility record must be a mapping")
        agent_id = record.get("agent_id")
        if agent_id not in assignments:
            raise ResultVerificationError("visibility record has unknown agent")
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


def _validate_raw_output_visibility(result: dict[str, Any], raw_outputs: object) -> None:
    if not isinstance(raw_outputs, dict) or not isinstance(raw_outputs.get("round_outputs"), dict):
        raise ResultVerificationError("raw round outputs are missing")
    if not isinstance(raw_outputs.get("round_inputs"), dict):
        raise ResultVerificationError("raw provider inputs are missing")
    round_outputs = raw_outputs["round_outputs"]
    round_inputs = raw_outputs["round_inputs"]
    if set(round_inputs) != set(round_outputs):
        raise ResultVerificationError("raw provider input/output keys do not match")
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
        if set(input_payload) != {"collective_context", "naive_shared_findings"}:
            raise ResultVerificationError("raw provider input has forbidden fields")
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
        "schema_version": "meridian-seal-v1",
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
        "condition": result_payload["condition"],
        "n_agents": result_payload["n_agents"],
        "seed": result_payload["seed"],
        "sealed_json_sha256": _file_sha256(run_dir / "SEALED.json"),
        "result_timestamp": result_payload["result_timestamp"],
    })
    return run_dir


def verify_sealed_run(run_dir: Path) -> dict[str, Any]:
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
    if not isinstance(seal, dict) or seal.get("schema_version") != "meridian-seal-v1":
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
    index_rows = _read_seal_index(run_dir.parent / SEAL_INDEX_FILENAME)
    matching_rows = [row for row in index_rows if row.get("run_id") == result["run_id"]]
    if len(matching_rows) != 1:
        raise ResultVerificationError("external seal index does not uniquely anchor this run")
    expected_index = {
        "run_id": result["run_id"],
        "condition": result["condition"],
        "n_agents": result["n_agents"],
        "seed": result["seed"],
        "sealed_json_sha256": _file_sha256(required_paths["SEALED.json"]),
        "result_timestamp": result["result_timestamp"],
    }
    if matching_rows[0] != expected_index:
        raise ResultVerificationError("external seal index entry mismatch")
    return result

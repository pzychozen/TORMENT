"""Test-only detached Phase-13 evidence with a strict raw-state boundary."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Final

from brainvision.projection import BrainvisionProjectionV1
from brainvision.sink import Phase12SinkMetrics

from brainvision_phase13.schemas import canonical_json_bytes, sha256_hex


_FORBIDDEN_FIELD_NAMES: Final[frozenset[str]] = frozenset(
    {
        "FastTrace",
        "VheState",
        "PersistentContext",
        "SemanticRegister",
        "amplitude_1_q",
        "amplitude_2_q",
        "remaining_ns",
        "write_gate_q",
        "clamped_orientation_q",
        "gain_1_q",
        "gain_2_q",
        "gain_3_q",
        "base_gain_q",
        "process_local_origin_ns",
        "vhe_state",
    }
)
_FORBIDDEN_TYPE_NAMES: Final[frozenset[str]] = frozenset(
    {"VheState", "FastTrace", "PersistentContext", "SemanticRegister"}
)


class RawStateEvidenceError(ValueError):
    """Raised when a proposed evidence value crosses the Phase-13 boundary."""


def assert_evidence_safe(value: object) -> None:
    """Reject evidence carrying raw recursive state or a raw-state container."""
    if type(value).__name__ in _FORBIDDEN_TYPE_NAMES:
        raise RawStateEvidenceError(f"prohibited raw-state type: {type(value).__name__}")
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if type(key) is str and key in _FORBIDDEN_FIELD_NAMES:
                raise RawStateEvidenceError(f"prohibited raw-state field: {key}")
            assert_evidence_safe(nested)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for nested in value:
            assert_evidence_safe(nested)


def canonical_projection_evidence(payload: Mapping[str, object]) -> dict[str, object]:
    """Canonicalize exactly the detached nine-field Phase-5 projection mapping."""
    projection = BrainvisionProjectionV1(
        current_activity_code=payload["current_activity_code"],
        retained_history_code=payload["retained_history_code"],
        present_history_relation_code=payload["present_history_relation_code"],
        trajectory_code=payload["trajectory_code"],
        open_event_class=payload["open_event_class"],
        recurrence_code=payload["recurrence_code"],
    )
    canonical_payload = projection.to_dict()
    if canonical_payload != dict(payload):
        raise ValueError("detached projection payload is not the frozen nine-field mapping")
    raw = projection.to_canonical_json_bytes()
    return {
        "canonical_bytes_ascii": raw.decode("ascii"),
        "payload": canonical_payload,
        "sha256": sha256_hex(raw),
    }


def _failure_record(failure: object | None) -> dict[str, object] | None:
    if failure is None:
        return None
    record: dict[str, object] = {
        "field": getattr(failure, "field", None),
        "reason": getattr(failure, "reason", None),
    }
    durable_committed = getattr(failure, "durable_committed", None)
    if durable_committed is not None:
        record["durable_committed"] = durable_committed
    return record


def _metrics_record(metrics: object | None) -> dict[str, int] | None:
    if metrics is None:
        return None
    return {
        "projection_construction_failures_total": metrics.projection_construction_failures_total,
        "sink_delivery_failures_total": metrics.sink_delivery_failures_total,
        "sink_invocations_total": metrics.sink_invocations_total,
    }


def detached_operation_record(operation: object) -> dict[str, object]:
    """Detach one complete post-operation observation without runtime objects.

    Each command produces a ledger record.  A command is not made evidentiary
    merely by being named as a checkpoint; checkpoints are a convenient index
    into this complete bounded ledger.
    """
    receipt = getattr(operation, "receipt", None)
    projection = getattr(operation, "projection_record", None)
    artifact_hashes = getattr(operation, "artifact_hashes", None)
    artifact_metadata = getattr(operation, "artifact_metadata", None)
    lineage_identity = getattr(operation, "lineage_identity", None)
    recovery = getattr(operation, "recovery", None)
    record: dict[str, object] = {
        "arm": getattr(operation, "arm", None),
        "artifact_hashes": dict(artifact_hashes) if isinstance(artifact_hashes, Mapping) else None,
        "artifact_metadata": (
            dict(artifact_metadata) if isinstance(artifact_metadata, Mapping) else None
        ),
        "failure": _failure_record(getattr(operation, "failure", None)),
        "failure_type": (
            None
            if getattr(operation, "failure", None) is None
            else getattr(operation, "failure").error_class
        ),
        "lineage_identity": (
            dict(lineage_identity) if isinstance(lineage_identity, Mapping) else None
        ),
        "metrics": _metrics_record(getattr(operation, "metrics", None)),
        "operation": getattr(operation, "operation", None),
        "projection": None if projection is None else dict(projection),
        "recovery": dict(recovery) if isinstance(recovery, Mapping) else None,
        "receipt": (
            None
            if receipt is None
            else {
                "committed_active_time_ns": receipt.committed_active_time_ns,
                "observation_id": receipt.observation_id,
                "source_sequence": receipt.source_sequence,
            }
        ),
    }
    if type(record["operation"]) is not str:
        raise TypeError("backend operation evidence must name an operation")
    if record["arm"] is not None and type(record["arm"]) is not str:
        raise TypeError("backend operation evidence arm must be str or None")
    assert_evidence_safe(record)
    return record


def checkpoint_record_from_operation(operation: object) -> tuple[str, dict[str, object]] | None:
    """Return a detached record for one explicitly checkpointed operation."""
    checkpoint = getattr(operation, "checkpoint", None)
    if checkpoint is None:
        return None
    if type(checkpoint) is not str:
        raise TypeError("checkpoint must be str or None")
    return checkpoint, detached_operation_record(operation)


def _comparison_record(record: Mapping[str, object]) -> dict[str, object]:
    """Remove arm-local naming while retaining every observable outcome."""
    return {
        key: value
        for key, value in record.items()
        if key not in {"arm", "lineage_identity"}
    }


def detached_block_evidence(
    operations: Sequence[object], *, complete: bool = True, defect: object | None = None
) -> dict[str, object]:
    """Freeze complete bounded block evidence for the later independent grader."""
    checkpoints: dict[str, dict[str, object]] = {}
    records: list[dict[str, object]] = []
    arm_records: dict[str, list[dict[str, object]]] = {}
    for operation in operations:
        record = detached_operation_record(operation)
        records.append(record)
        arm = record["arm"]
        if arm is not None:
            arm_records.setdefault(arm, []).append(record)
        checkpoint = getattr(operation, "checkpoint", None)
        if checkpoint is not None:
            if type(checkpoint) is not str or checkpoint in checkpoints:
                raise ValueError("checkpoint must be unique textual evidence index")
            checkpoints[checkpoint] = record
    arms: dict[str, object] = {}
    for arm, entries in arm_records.items():
        comparison_entries = [_comparison_record(entry) for entry in entries]
        arms[arm] = {
            "comparison_canonical_bytes_ascii": canonical_json_bytes(
                comparison_entries
            ).decode("ascii"),
            "records": entries,
        }
    result: dict[str, object] = {
        "arm_ledgers": arms,
        "checkpoints": checkpoints,
        "run_ledger": records,
        "run_ledger_canonical_bytes_ascii": canonical_json_bytes(records).decode("ascii"),
        "execution_state": "COMPLETE" if complete else "INCOMPLETE",
        "defect": (
            None
            if defect is None
            else {
                "arm": getattr(defect, "arm", None),
                "block_id": getattr(defect, "block_id", None),
                "durable_committed": getattr(defect, "durable_committed", None),
                "exception_class": getattr(defect, "exception_class", None),
                "field": getattr(defect, "field", None),
                "invalid_subcode": getattr(defect, "invalid_subcode", None),
                "operation": getattr(defect, "operation", None),
                "operation_index": getattr(defect, "operation_index", None),
                "reason": getattr(defect, "reason", None),
            }
        ),
    }
    assert_evidence_safe(result)
    return result


def detached_block_checkpoint_evidence(operations: Sequence[object]) -> dict[str, object]:
    """Compatibility alias returning the complete detached block evidence."""
    return detached_block_evidence(operations)


@dataclass
class EvidenceBuilder:
    """In-memory collector; construction does not write output files."""

    run_ledger: list[dict[str, object]] = field(default_factory=list)
    projection_records: list[dict[str, object]] = field(default_factory=list)
    artifact_hashes: list[dict[str, object]] = field(default_factory=list)
    metrics_records: list[dict[str, object]] = field(default_factory=list)
    recovery_records: list[dict[str, object]] = field(default_factory=list)
    operation_journal_writer: Callable[[str, Mapping[str, object]], None] | None = None

    def record(self, collection: str, entry: Mapping[str, object]) -> None:
        assert_evidence_safe(entry)
        target = getattr(self, collection)
        if type(target) is not list:
            raise ValueError("unknown evidence collection")
        target.append(dict(entry))

    def record_metrics(self, *, block: str, arm: str, metrics: Phase12SinkMetrics) -> None:
        self.record(
            "metrics_records",
            {
                "arm": arm,
                "block": block,
                "projection_construction_failures_total": (
                    metrics.projection_construction_failures_total
                ),
                "sink_delivery_failures_total": metrics.sink_delivery_failures_total,
                "sink_invocations_total": metrics.sink_invocations_total,
            },
        )

    def record_backend_operation(self, block_id: str, operation: object) -> None:
        """Detach and durably journal each post-start operation before continuing."""
        if type(block_id) is not str:
            raise TypeError("block ID must be textual")
        record = detached_operation_record(operation)
        entry = {"block_id": block_id, "record": record}
        assert_evidence_safe(entry)
        self.run_ledger.append(entry)
        if self.operation_journal_writer is not None:
            self.operation_journal_writer(block_id, entry)

    def to_canonical_bytes(self) -> bytes:
        payload = {
            "artifact_hashes": self.artifact_hashes,
            "metrics_records": self.metrics_records,
            "projection_records": self.projection_records,
            "recovery_records": self.recovery_records,
            "run_ledger": self.run_ledger,
        }
        assert_evidence_safe(payload)
        return canonical_json_bytes(payload)


__all__ = (
    "EvidenceBuilder",
    "RawStateEvidenceError",
    "assert_evidence_safe",
    "canonical_projection_evidence",
    "checkpoint_record_from_operation",
    "detached_block_checkpoint_evidence",
    "detached_block_evidence",
    "detached_operation_record",
)

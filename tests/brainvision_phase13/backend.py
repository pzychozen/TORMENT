"""Test-only live-operation backend for the Phase-13 external grader.

This module translates explicit schedule commands into the already-frozen
production entry points.  It contains no expected numerical result, predicate,
or PASS/FAIL decision.  Importing it creates neither lineage nor artifact.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Final
from unittest.mock import patch

import brainvision.lifecycle as lifecycle_module
from brainvision.configuration import (
    brainvision_configuration_path,
    configuration_from_json_bytes,
)
from brainvision.character_modulation import modulation_profile_id
from brainvision.fixtures import D0, DA, DB
from brainvision.ingress import FirsthandVisualAdmissionReceipt
from brainvision.lifecycle import BrainvisionLifecycleManager
from brainvision.observation import (
    FirsthandVisualObservationV1,
    ObservationProvenanceType,
    derive_observation_id,
)
from brainvision.sink import Phase12IngressHost, Phase12SinkMetrics
from brainvision.vhe_sidecar import vhe_sidecar_from_json_bytes, vhe_sidecar_path
from torment_service.agent_locks import AgentLockManager
from torment_service.identity import IdentityStore

from brainvision_phase13.clock import QualificationClock
from brainvision_phase13.evidence import canonical_projection_evidence
from brainvision_phase13.qualification import stimulate_runtime_snapshot
from brainvision_phase13.schemas import BlockExecutionEvidence, ExecutionDefect


SCHEDULE_OPERATION_NAMES: Final[tuple[str, ...]] = (
    "CREATE_LINEAGE",
    "CONFIGURE",
    "ENABLE",
    "CREATE_HOST",
    "SET_CLOCK",
    "ADVANCE_CLOCK",
    "ADMIT",
    "SUSPEND",
    "RESUME",
    "RESET",
    "DISABLE",
    "CLOSE_HOST",
    "DESTROY_MANAGER",
    "REBUILD_MANAGER",
    "RUNTIME_SNAPSHOT_STIMULUS",
    "CAPTURE_ARTIFACTS",
    "INJECT_FAULT",
    "CLEAR_FAULT",
    "TRIGGER_RECOVERY",
)
FAULT_IDS: Final[frozenset[str]] = frozenset(
    {
        "E7_SIDECAR_WRITE_FAIL",
        "E7_CONFIG_WRITE_PRE_DURABILITY_FAIL",
        "E7_CONFIG_WRITE_POST_DURABILITY_RAISE",
    }
)
FIXTURE_IDS: Final[Mapping[str, object]] = {"d0": D0, "dA": DA, "dB": DB}


class BackendOperationError(RuntimeError):
    """A test-only schedule/backend boundary error, never a graded outcome."""


class _ScheduleExecutionDefect(RuntimeError):
    """Internal bounded stop carrying operations already durably journaled."""

    def __init__(self, defect: ExecutionDefect, operations: tuple[object, ...]) -> None:
        super().__init__(defect.exception_class)
        self.defect = defect
        self.operations = operations


@dataclass(frozen=True, kw_only=True)
class QualificationLineageSpec:
    workspace_id: str
    agent_id: str
    stream_identity: str
    adapter_contract_id: str
    theta: int
    adapter_id: str


@dataclass(frozen=True, kw_only=True)
class ArtifactBytes:
    configuration_bytes: bytes | None
    sidecar_bytes: bytes | None

    def hashes(self) -> dict[str, str | None]:
        return {
            "configuration_sha256": (
                None if self.configuration_bytes is None else sha256(self.configuration_bytes).hexdigest()
            ),
            "sidecar_sha256": (
                None if self.sidecar_bytes is None else sha256(self.sidecar_bytes).hexdigest()
            ),
        }


@dataclass(frozen=True, kw_only=True)
class CapturedFailure:
    error_class: str
    field: str | None
    reason: str | None
    durable_committed: bool | None


@dataclass(frozen=True, kw_only=True)
class BackendOperationEvidence:
    operation: str
    checkpoint: str | None
    lineage_name: str
    arm: str | None
    receipt: FirsthandVisualAdmissionReceipt | None
    projection_record: Mapping[str, object] | None
    failure: CapturedFailure | None
    artifact_hashes: Mapping[str, str | None]
    artifact_metadata: Mapping[str, int | str | None]
    lineage_identity: Mapping[str, int | str]
    recovery: Mapping[str, int | str | None]
    metrics: Phase12SinkMetrics | None


@dataclass(frozen=True, kw_only=True)
class BackendFailureOperationEvidence:
    """Safe record when a command fails before a lineage can yield artifacts."""

    operation: str
    checkpoint: str | None
    lineage_name: str | None
    arm: str | None
    receipt: None = None
    projection_record: None = None
    failure: CapturedFailure | None = None
    artifact_hashes: None = None
    artifact_metadata: None = None
    lineage_identity: None = None
    recovery: None = None
    metrics: None = None


class RecordingSink:
    """Append-only test sink retaining only detached Phase-12 payloads."""

    def __init__(self) -> None:
        self.records: list[tuple[FirsthandVisualAdmissionReceipt, dict[str, object]]] = []

    def on_projection(
        self,
        receipt: FirsthandVisualAdmissionReceipt,
        projection_payload: dict[str, object],
    ) -> None:
        self.records.append((receipt, dict(projection_payload)))


class ThrowingSink:
    """Frozen E7.5-style post-commit callback interruption; never retries."""

    def __init__(self) -> None:
        self.attempts = 0

    def on_projection(
        self,
        receipt: FirsthandVisualAdmissionReceipt,
        projection_payload: dict[str, object],
    ) -> None:
        del receipt, projection_payload
        self.attempts += 1
        raise RuntimeError("phase13_test_only_throwing_sink")


@dataclass
class _Lineage:
    spec: QualificationLineageSpec
    root: Path
    clock: QualificationClock
    identities: IdentityStore
    locks: AgentLockManager
    manager: BrainvisionLifecycleManager | None
    host: Phase12IngressHost | None
    sink: object | None
    sidecar_ahead_configuration_repairs_total: int = 0
    last_recovery_event: str | None = None


class QualificationFaultController:
    """Scoped E7 persistence faults; all patches restore in ``clear``/finally."""

    def __init__(self) -> None:
        self._patches: list[object] = []

    def inject(self, fault_id: str) -> None:
        if self._patches:
            raise BackendOperationError("a fault is already active")
        if fault_id not in FAULT_IDS:
            raise BackendOperationError(f"unknown preregistered fault: {fault_id}")
        if fault_id == "E7_SIDECAR_WRITE_FAIL":
            def fail_sidecar(*_: object, **__: object) -> None:
                raise OSError("phase13_sidecar_write_failure")

            self._install(patch.object(lifecycle_module, "write_vhe_sidecar", fail_sidecar))
            return
        real_configuration_write = lifecycle_module.write_brainvision_configuration
        if fault_id == "E7_CONFIG_WRITE_PRE_DURABILITY_FAIL":
            def fail_configuration(*_: object, **__: object) -> None:
                raise OSError("phase13_config_write_pre_durability_failure")

            self._install(
                patch.object(lifecycle_module, "write_brainvision_configuration", fail_configuration)
            )
            return

        def write_then_raise(*args: object, **kwargs: object) -> None:
            real_configuration_write(*args, **kwargs)
            raise OSError("phase13_config_write_post_durability_raise")

        self._install(
            patch.object(lifecycle_module, "write_brainvision_configuration", write_then_raise)
        )

    def _install(self, replacement: object) -> None:
        replacement.start()
        self._patches.append(replacement)

    def clear(self) -> None:
        while self._patches:
            self._patches.pop().stop()

    def __enter__(self) -> "QualificationFaultController":
        return self

    def __exit__(self, *_: object) -> None:
        self.clear()


class QualificationExecutionBackend:
    """The sole Phase-13 test layer allowed to call live Brainvision surfaces."""

    def __init__(self, data_root: Path) -> None:
        self._data_root = data_root
        self._lineages: dict[str, _Lineage] = {}
        self._faults = QualificationFaultController()

    def close(self) -> None:
        self._faults.clear()
        for lineage in self._lineages.values():
            self.close_host(lineage)
            if lineage.manager is not None:
                lineage.manager.shutdown()
                lineage.manager = None

    def create_lineage(
        self,
        *,
        name: str,
        spec: QualificationLineageSpec,
        sink: object | None = None,
        clock: QualificationClock | None = None,
    ) -> _Lineage:
        if name in self._lineages:
            raise BackendOperationError(f"duplicate lineage: {name}")
        root = self._data_root / name
        selected_clock = QualificationClock() if clock is None else clock
        identities = IdentityStore(str(root))
        identities.create(spec.workspace_id, spec.agent_id)
        locks = AgentLockManager()
        manager = BrainvisionLifecycleManager(
            data_dir=root,
            identity_store=identities,
            lock_manager=locks,
            monotonic_ns_source=selected_clock,
        )
        lineage = _Lineage(
            spec=spec,
            root=root,
            clock=selected_clock,
            identities=identities,
            locks=locks,
            manager=manager,
            host=None,
            sink=sink,
        )
        self._lineages[name] = lineage
        return lineage

    def configure(self, lineage: _Lineage) -> None:
        manager = self._require_manager(lineage)
        manager.configure_brainvision(
            lineage.spec.workspace_id,
            lineage.spec.agent_id,
            lineage.spec.stream_identity,
            lineage.spec.adapter_contract_id,
            lineage.spec.theta,
        )

    def enable(self, lineage: _Lineage) -> None:
        self._require_manager(lineage).enable(lineage.spec.workspace_id, lineage.spec.agent_id)

    def create_host(self, lineage: _Lineage) -> None:
        if lineage.host is not None:
            raise BackendOperationError("lineage already has a Phase-12 host")
        lineage.host = Phase12IngressHost(
            lifecycle_manager=self._require_manager(lineage),
            workspace_id=lineage.spec.workspace_id,
            agent_id=lineage.spec.agent_id,
            sink=lineage.sink,
        )

    def close_host(self, lineage: _Lineage) -> None:
        if lineage.host is not None:
            lineage.host.close()
            lineage.host = None

    def set_clock(self, lineage: _Lineage, active_time_ns: int) -> None:
        lineage.clock.set_ns(active_time_ns)

    def advance_clock(self, lineage: _Lineage, delta_ns: int) -> None:
        lineage.clock.advance_ns(delta_ns)

    def build_observation(
        self,
        lineage: _Lineage,
        *,
        fixture_id: str,
        source_sequence: int,
        adapter_id: str,
        adapter_contract_id: str,
        source_capture_time_unix_ns: int | None = None,
        confidence_q: int | None = None,
        semantic_event_class: str | None = None,
        world_event_id: str | None = None,
    ) -> FirsthandVisualObservationV1:
        descriptor = FIXTURE_IDS.get(fixture_id)
        if descriptor is None:
            raise BackendOperationError(f"unknown frozen fixture: {fixture_id}")
        stream_identity = lineage.spec.stream_identity
        return FirsthandVisualObservationV1(
            provenance_type=ObservationProvenanceType.FIRSTHAND_VISUAL,
            stream_identity=stream_identity,
            source_sequence=source_sequence,
            observation_id=derive_observation_id(stream_identity, source_sequence),
            descriptor=descriptor,
            adapter_id=adapter_id,
            adapter_contract_id=adapter_contract_id,
            source_capture_time_unix_ns=source_capture_time_unix_ns,
            confidence_q=confidence_q,
            semantic_event_class=semantic_event_class,
            world_event_id=world_event_id,
        )

    @staticmethod
    def tamper_observation_id(
        observation: FirsthandVisualObservationV1,
    ) -> FirsthandVisualObservationV1:
        """Use Phase-11's lawful test-only frozen-dataclass tampering technique."""
        object.__setattr__(
            observation,
            "observation_id",
            derive_observation_id(observation.stream_identity, 2),
        )
        return observation

    def admit(
        self,
        lineage: _Lineage,
        observation: FirsthandVisualObservationV1,
        *,
        arm: str | None = None,
        checkpoint: str | None = None,
    ) -> BackendOperationEvidence:
        host = lineage.host
        if host is None:
            raise BackendOperationError("ADMIT requires a Phase-12 host")
        try:
            receipt = host.admit(observation)
        except Exception as error:
            return self._evidence(
                lineage,
                "ADMIT",
                failure=self._capture_failure(error),
                arm=arm,
                checkpoint=checkpoint,
            )
        projection_record: Mapping[str, object] | None = None
        if isinstance(lineage.sink, RecordingSink) and lineage.sink.records:
            delivered_receipt, payload = lineage.sink.records[-1]
            if delivered_receipt == receipt:
                projection_record = canonical_projection_evidence(payload)
        return self._evidence(
            lineage,
            "ADMIT",
            receipt=receipt,
            projection_record=projection_record,
            arm=arm,
            checkpoint=checkpoint,
        )

    def suspend(self, lineage: _Lineage) -> None:
        self._require_manager(lineage).suspend(lineage.spec.workspace_id, lineage.spec.agent_id)

    def resume(self, lineage: _Lineage) -> None:
        self._require_manager(lineage).resume(lineage.spec.workspace_id, lineage.spec.agent_id)

    def reset(self, lineage: _Lineage) -> None:
        self._require_manager(lineage).reset(lineage.spec.workspace_id, lineage.spec.agent_id)

    def disable(self, lineage: _Lineage) -> None:
        self._require_manager(lineage).disable(lineage.spec.workspace_id, lineage.spec.agent_id)

    def destroy_manager(self, lineage: _Lineage) -> None:
        if lineage.host is not None:
            raise BackendOperationError("DESTROY_MANAGER requires host closed first")
        if lineage.manager is not None:
            lineage.manager.shutdown()
            lineage.manager = None

    def rebuild_manager(self, lineage: _Lineage) -> None:
        if lineage.manager is not None:
            raise BackendOperationError("REBUILD_MANAGER requires destroyed manager")
        lineage.manager = BrainvisionLifecycleManager(
            data_dir=lineage.root,
            identity_store=lineage.identities,
            lock_manager=lineage.locks,
            monotonic_ns_source=lineage.clock,
        )

    def stimulate_snapshot(self, lineage: _Lineage) -> None:
        before = self.artifact_metadata(lineage)
        stimulate_runtime_snapshot(
            self._require_manager(lineage), lineage.spec.workspace_id, lineage.spec.agent_id
        )
        after = self.artifact_metadata(lineage)
        if (
            before["configuration_last_accepted_source_sequence"] is not None
            and before["sidecar_accepted_source_sequence"] is not None
            and before["configuration_last_accepted_source_sequence"]
            < before["sidecar_accepted_source_sequence"]
            and after["configuration_last_accepted_source_sequence"]
            == after["sidecar_accepted_source_sequence"]
        ):
            lineage.sidecar_ahead_configuration_repairs_total += 1
            lineage.last_recovery_event = "SIDECAR_AHEAD_CONFIGURATION_WATERMARK_REPAIRED"
        else:
            lineage.last_recovery_event = None
        return None

    def artifact_bytes(self, lineage: _Lineage) -> ArtifactBytes:
        configuration_path = Path(
            brainvision_configuration_path(
                lineage.root, lineage.spec.workspace_id, lineage.spec.agent_id
            )
        )
        sidecar_path = Path(vhe_sidecar_path(lineage.root, lineage.spec.workspace_id, lineage.spec.agent_id))
        return ArtifactBytes(
            configuration_bytes=(configuration_path.read_bytes() if configuration_path.exists() else None),
            sidecar_bytes=(sidecar_path.read_bytes() if sidecar_path.exists() else None),
        )

    def artifact_metadata(self, lineage: _Lineage) -> dict[str, int | str | None]:
        """Expose only configuration/sidecar continuation metadata, never VHE state."""
        artifacts = self.artifact_bytes(lineage)
        configuration = (
            None
            if artifacts.configuration_bytes is None
            else configuration_from_json_bytes(artifacts.configuration_bytes)
        )
        sidecar = (
            None
            if artifacts.sidecar_bytes is None
            else vhe_sidecar_from_json_bytes(artifacts.sidecar_bytes)
        )
        return {
            "configuration_last_accepted_source_sequence": (
                None if configuration is None else configuration.last_accepted_source_sequence
            ),
            "configuration_modulation_profile_id": (
                None if configuration is None else configuration.modulation_profile_id
            ),
            "configuration_theta": None if configuration is None else configuration.theta,
            "sidecar_accepted_source_sequence": (
                None if sidecar is None else sidecar.accepted_source_sequence
            ),
            "sidecar_committed_active_time_ns": (
                None if sidecar is None else sidecar.committed_active_time_ns
            ),
        }

    def metrics(self, lineage: _Lineage) -> Phase12SinkMetrics | None:
        return None if lineage.host is None else lineage.host.metrics_snapshot()

    def inject_fault(self, fault_id: str) -> None:
        self._faults.inject(fault_id)

    def clear_fault(self) -> None:
        self._faults.clear()

    def trigger_recovery(self, lineage: _Lineage) -> None:
        self.stimulate_snapshot(lineage)
        return None

    def execute_block(self, plan: object, evidence: object) -> BlockExecutionEvidence:
        """Execute only a future frozen structured command list for one block.

        The current command-line latch prevents this method from being reached
        in this workorder.  The method intentionally accepts no expected value
        and returns only ungraded operation evidence.
        """
        block_id = getattr(plan, "block_id", None)
        schedule = getattr(plan, "schedule", None)
        if type(block_id) is not str or not isinstance(schedule, Mapping):
            raise BackendOperationError("invalid qualification block plan")
        commands = flatten_block_commands(schedule)

        def journal(operation: object) -> None:
            recorder = getattr(evidence, "record_backend_operation", None)
            if callable(recorder):
                recorder(block_id, operation)

        try:
            operations = self.execute_schedule(commands, on_operation=journal, block_id=block_id)
        except _ScheduleExecutionDefect as defect:
            return BlockExecutionEvidence(
                block_id=block_id,
                operations=defect.operations,
                complete=False,
                defect=defect.defect,
            )
        return BlockExecutionEvidence(block_id=block_id, operations=operations)

    def execute_schedule(
        self,
        commands: Sequence[Mapping[str, object]],
        *,
        on_operation: object | None = None,
        block_id: str | None = None,
    ) -> tuple[BackendOperationEvidence, ...]:
        """Dispatch only explicit command dictionaries; no retry or implicit time."""
        evidence: list[object] = []

        def append(record: object) -> None:
            evidence.append(record)
            if callable(on_operation):
                on_operation(record)

        for operation_index, command in enumerate(commands):
            operation = command.get("operation")
            name = command.get("lineage")
            lineage = self._lineages.get(name) if type(name) is str else None
            checkpoint = command.get("checkpoint")
            arm = command.get("arm")
            try:
                if operation not in SCHEDULE_OPERATION_NAMES:
                    raise BackendOperationError(f"unsupported schedule operation: {operation!r}")
                if checkpoint is not None and type(checkpoint) is not str:
                    raise BackendOperationError("checkpoint must be str when supplied")
                if operation == "CREATE_LINEAGE":
                    spec = command.get("spec")
                    if isinstance(spec, Mapping):
                        spec = QualificationLineageSpec(**spec)
                    if type(spec) is not QualificationLineageSpec or type(name) is not str:
                        raise BackendOperationError("CREATE_LINEAGE requires a lineage name and exact spec")
                    sink = self._sink_for_mode(command.get("sink_mode", "recording"))
                    created = self.create_lineage(name=name, spec=spec, sink=sink)
                    append(self._evidence(created, operation, arm=arm, checkpoint=checkpoint))
                    continue
                if lineage is None:
                    raise BackendOperationError(f"{operation} requires an existing lineage")
                if arm is not None and type(arm) is not str:
                    raise BackendOperationError("arm must be str when supplied")
                if operation == "CONFIGURE": self.configure(lineage)
                elif operation == "ENABLE": self.enable(lineage)
                elif operation == "CREATE_HOST":
                    sink_mode = command.get("sink_mode")
                    if sink_mode is not None:
                        lineage.sink = self._sink_for_mode(sink_mode)
                    self.create_host(lineage)
                elif operation == "SET_CLOCK": self.set_clock(lineage, command["active_time_ns"])
                elif operation == "ADVANCE_CLOCK": self.advance_clock(lineage, command["delta_ns"])
                elif operation == "ADMIT":
                    observation_spec = command.get("observation")
                    if not isinstance(observation_spec, Mapping):
                        raise BackendOperationError("ADMIT requires an observation mapping")
                    observation = self.build_observation(lineage, **observation_spec)
                    if command.get("tamper_observation_id", False):
                        observation = self.tamper_observation_id(observation)
                    append(self.admit(lineage, observation, arm=arm, checkpoint=checkpoint))
                    continue
                elif operation == "SUSPEND": self.suspend(lineage)
                elif operation == "RESUME": self.resume(lineage)
                elif operation == "RESET": self.reset(lineage)
                elif operation == "DISABLE": self.disable(lineage)
                elif operation == "CLOSE_HOST": self.close_host(lineage)
                elif operation == "DESTROY_MANAGER": self.destroy_manager(lineage)
                elif operation == "REBUILD_MANAGER": self.rebuild_manager(lineage)
                elif operation == "RUNTIME_SNAPSHOT_STIMULUS": self.stimulate_snapshot(lineage)
                elif operation == "CAPTURE_ARTIFACTS": pass
                elif operation == "INJECT_FAULT": self.inject_fault(command["fault_id"])
                elif operation == "CLEAR_FAULT": self.clear_fault()
                elif operation == "TRIGGER_RECOVERY": self.trigger_recovery(lineage)
                append(self._evidence(lineage, operation, arm=arm, checkpoint=checkpoint))
            except Exception as error:
                failure = self._capture_failure(error)
                if lineage is not None:
                    append(self._evidence(lineage, str(operation), failure=failure, arm=arm, checkpoint=checkpoint))
                else:
                    append(
                        BackendFailureOperationEvidence(
                            operation=str(operation), checkpoint=checkpoint if isinstance(checkpoint, str) else None,
                            lineage_name=name if isinstance(name, str) else None,
                            arm=arm if isinstance(arm, str) else None,
                            failure=failure,
                        )
                    )
                defect = ExecutionDefect(
                    block_id=block_id or "E1",
                    operation_index=operation_index,
                    operation=str(operation),
                    arm=arm if isinstance(arm, str) else None,
                    exception_class=failure.error_class,
                    field=failure.field,
                    reason=failure.reason,
                    durable_committed=failure.durable_committed,
                )
                raise _ScheduleExecutionDefect(defect, tuple(evidence)) from None
        return tuple(evidence)  # type: ignore[return-value]

    def _require_manager(self, lineage: _Lineage) -> BrainvisionLifecycleManager:
        if lineage.manager is None:
            raise BackendOperationError("operation requires a live lifecycle manager")
        return lineage.manager

    def _evidence(
        self,
        lineage: _Lineage,
        operation: str,
        *,
        receipt: FirsthandVisualAdmissionReceipt | None = None,
        projection_record: Mapping[str, object] | None = None,
        failure: CapturedFailure | None = None,
        arm: str | None = None,
        checkpoint: str | None = None,
    ) -> BackendOperationEvidence:
        return BackendOperationEvidence(
            operation=operation,
            checkpoint=checkpoint,
            lineage_name=next(name for name, value in self._lineages.items() if value is lineage),
            arm=arm,
            receipt=receipt,
            projection_record=projection_record,
            failure=failure,
            artifact_hashes=self.artifact_bytes(lineage).hashes(),
            artifact_metadata=self.artifact_metadata(lineage),
            lineage_identity={
                "adapter_contract_id": lineage.spec.adapter_contract_id,
                "adapter_id": lineage.spec.adapter_id,
                "agent_id": lineage.spec.agent_id,
                "modulation_profile_id": modulation_profile_id(lineage.spec.theta),
                "stream_identity": lineage.spec.stream_identity,
                "theta": lineage.spec.theta,
                "workspace_id": lineage.spec.workspace_id,
            },
            recovery={
                "last_recovery_event": lineage.last_recovery_event,
                "sidecar_ahead_configuration_repairs_total": (
                    lineage.sidecar_ahead_configuration_repairs_total
                ),
            },
            metrics=self.metrics(lineage),
        )

    @staticmethod
    def _sink_for_mode(sink_mode: object) -> object | None:
        if sink_mode == "recording":
            return RecordingSink()
        if sink_mode == "throwing":
            return ThrowingSink()
        if sink_mode == "null":
            return None
        raise BackendOperationError("unknown sink mode")

    @staticmethod
    def _capture_failure(error: Exception) -> CapturedFailure:
        field = getattr(error, "field", None)
        reason = getattr(error, "reason", None)
        durable_committed = getattr(error, "durable_committed", None)
        return CapturedFailure(
            error_class=type(error).__name__,
            field=field if type(field) is str else None,
            reason=reason if type(reason) is str else None,
            durable_committed=durable_committed if type(durable_committed) is bool else None,
        )


def validate_schedule_handler_completeness(schedule: Mapping[str, object]) -> None:
    """Pure graph validation: each declared operation has one backend handler."""
    declared = schedule.get("operation_vocabulary")
    if tuple(declared) != SCHEDULE_OPERATION_NAMES:
        raise ValueError("schedule operation vocabulary differs from backend handlers")
    blocks = schedule.get("blocks")
    if not isinstance(blocks, Mapping) or tuple(blocks) != tuple(f"E{i}" for i in range(1, 13)):
        raise ValueError("schedule must include exactly E1 through E12")


def flatten_block_commands(schedule: Mapping[str, object]) -> tuple[Mapping[str, object], ...]:
    """Resolve explicit metadata defaults and return frozen commands in arm order."""
    from brainvision_phase13.manifests import resolve_effective_observation_spec

    arms = schedule.get("arms")
    observation_defaults = schedule.get("observation_defaults")
    if not isinstance(arms, Mapping) or not arms:
        raise BackendOperationError("block lacks frozen arms")
    flattened: list[Mapping[str, object]] = []
    if not isinstance(observation_defaults, Mapping):
        raise BackendOperationError("block lacks explicit observation-default binding")
    for arm_name, arm in arms.items():
        if type(arm_name) is not str:
            raise BackendOperationError("arm name must be textual")
        if not isinstance(arm, Mapping):
            raise BackendOperationError("arm must be a mapping")
        commands = arm.get("commands")
        if not isinstance(commands, Sequence) or isinstance(commands, (str, bytes)):
            raise BackendOperationError("arm lacks frozen structured commands")
        for command in commands:
            if not isinstance(command, Mapping):
                raise BackendOperationError("command must be a mapping")
            resolved = dict(command)
            resolved.setdefault("arm", arm_name)
            if resolved.get("operation") == "ADMIT":
                observation = resolved.get("observation")
                if not isinstance(observation, Mapping):
                    raise BackendOperationError("ADMIT requires an observation mapping")
                resolved["observation"] = resolve_effective_observation_spec(
                    observation_defaults, observation
                )
            flattened.append(resolved)
    return tuple(flattened)


def validate_backend_manifest_bindings(
    *,
    fixture_manifest: Mapping[str, object],
    expected_manifest: Mapping[str, object],
    schedule_manifest: Mapping[str, object],
    authority_manifest: Mapping[str, object],
) -> None:
    """Check test-only graph completeness without instantiating a lineage."""
    descriptors = fixture_manifest.get("descriptors")
    if not isinstance(descriptors, Mapping) or tuple(descriptors) != tuple(FIXTURE_IDS):
        raise ValueError("fixture manifest does not resolve exactly d0/dA/dB")
    for document, name in (
        (expected_manifest, "expected"),
        (schedule_manifest, "schedule"),
    ):
        blocks = document.get("blocks")
        if not isinstance(blocks, Mapping) or tuple(blocks) != tuple(f"E{i}" for i in range(1, 13)):
            raise ValueError(f"{name} manifest does not resolve every E1–E12 block")
    if tuple(schedule_manifest.get("fault_ids", ())) != tuple(sorted(FAULT_IDS)):
        raise ValueError("schedule manifest fault IDs do not resolve to backend faults")
    theta_lineages = expected_manifest["blocks"]["E5"].get("theta_lineages")
    if not isinstance(theta_lineages, Mapping) or tuple(theta_lineages) != ("-1", "0", "1"):
        raise ValueError("E5 theta lineages are incomplete")
    profiles = authority_manifest.get("theta_profile_ids")
    if not isinstance(profiles, Mapping):
        raise ValueError("authority manifest theta profile IDs are missing")
    for theta, lineage in theta_lineages.items():
        if not isinstance(lineage, Mapping) or lineage.get("modulation_profile_id") != profiles.get(theta):
            raise ValueError(f"E5 theta lineage does not bind authority profile: {theta}")


__all__ = (
    "ArtifactBytes",
    "BackendOperationError",
    "BackendOperationEvidence",
    "BackendFailureOperationEvidence",
    "BlockExecutionEvidence",
    "CapturedFailure",
    "FAULT_IDS",
    "FIXTURE_IDS",
    "QualificationExecutionBackend",
    "QualificationFaultController",
    "QualificationLineageSpec",
    "RecordingSink",
    "SCHEDULE_OPERATION_NAMES",
    "ThrowingSink",
    "flatten_block_commands",
    "validate_schedule_handler_completeness",
    "validate_backend_manifest_bindings",
)

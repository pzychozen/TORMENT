"""Production orchestration of the ratified post-P6 disposition owners.

This module does not own Character, trajectory, selector, or any receipt-only
state. It verifies the frozen plan entry then calls the designated owner and
returns a compact evidence token for the existing immutable root receipt.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Mapping, Sequence

from torment_service.character import CharacterStore

from .character_baseline_disposition import (
    CharacterBaselineDispositionOwner,
    CharacterBaselineReceipt,
    CharacterBaselineRequest,
    CharacterBaselineRefused,
)
from .deployment_types import RootDispositionExecutionReceipt, RootDispositionOwnerResult
from .errors import DeploymentAuthorityError
from .root_blocker5_binding import RootGeometryDispositionPlanEntry
from .trajectory_writer_handoff import (
    AggregateTrajectoryReceipt,
    TrajectoryHandoffBinding,
    TrajectoryHandoffPhase,
    TrajectoryHandoffRefused,
    TrajectoryScopeIdentity,
    TrajectoryWriterHandoffCoordinator,
)


_RECEIPT_ONLY = frozenset({
    "bridge_registry", "character_drift_history", "character_seed",
    "conflict_role_affect_identity", "deep_archive_vector_state",
    "hivemind_historical_geometry_scores", "proposal_registry",
})
_SYNTHETIC_ONLY = frozenset({"checkpoint_kernel_calibration", "srg_payload_markers"})
_CHARACTER = "character_active_baseline"
_TRAJECTORY = "world_trajectory"


class ProductionRootDispositionRefused(DeploymentAuthorityError):
    """The production adapter lacks one exact ratified owner proof."""


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _require_digest(value: object, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ProductionRootDispositionRefused(f"{label} must be a lowercase SHA-256 digest")
    return value


@dataclass(frozen=True)
class ReceiptOnlyDispositionEvidence:
    """A pre-existing owner receipt, bound to exactly one frozen plan entry."""

    owner_identity: str
    root_admission_envelope_digest: str
    plan_digest: str
    source_observation_digest: str
    evidence_digest: str

    def __post_init__(self) -> None:
        if self.owner_identity not in _RECEIPT_ONLY:
            raise ProductionRootDispositionRefused("receipt-only evidence names a non receipt-only owner")
        for name in (
            "root_admission_envelope_digest", "plan_digest", "source_observation_digest", "evidence_digest",
        ):
            _require_digest(getattr(self, name), name)


@dataclass(frozen=True)
class SyntheticOnlyDispositionEvidence:
    """Prior evidence used to classify an owner with no production operation."""

    owner_identity: str
    root_admission_envelope_digest: str
    plan_digest: str
    source_observation_digest: str
    classification_evidence_digest: str

    def __post_init__(self) -> None:
        if self.owner_identity not in _SYNTHETIC_ONLY:
            raise ProductionRootDispositionRefused("synthetic-only evidence names a production owner")
        for name in (
            "root_admission_envelope_digest", "plan_digest", "source_observation_digest", "classification_evidence_digest",
        ):
            _require_digest(getattr(self, name), name)


@dataclass(frozen=True)
class TrajectoryScopeHandoffInstruction:
    """The scoped P2/P6 evidence required to advance one real handoff."""

    scope: TrajectoryScopeIdentity
    legacy_writer_identity: str
    operation_key: str
    quiescing_evidence_digest: str
    quiescence_evidence_digest: str
    native_admission_evidence_digest: str
    native_writer_identity: str = "NATIVE_TRAJECTORY_EVIDENCE"

    def __post_init__(self) -> None:
        if not isinstance(self.scope, TrajectoryScopeIdentity):
            raise ProductionRootDispositionRefused("trajectory instruction scope must be typed")
        for name in (
            "legacy_writer_identity", "operation_key", "native_writer_identity",
        ):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                raise ProductionRootDispositionRefused(f"{name} must be non-empty")
        for name in (
            "quiescing_evidence_digest", "quiescence_evidence_digest", "native_admission_evidence_digest",
        ):
            _require_digest(getattr(self, name), name)


class ProductionRootDispositionAdapter:
    """Thin plan-entry router over existing Character and trajectory owners."""

    def __init__(
        self,
        *,
        data_root: str | Path,
        p6_receipt_id: str,
        plan_digest: str,
        character_requests: Sequence[CharacterBaselineRequest],
        trajectory_binding: TrajectoryHandoffBinding,
        trajectory_instructions: Sequence[TrajectoryScopeHandoffInstruction],
        receipt_only_evidence: Sequence[ReceiptOnlyDispositionEvidence],
        synthetic_only_evidence: Sequence[SyntheticOnlyDispositionEvidence],
    ) -> None:
        self._data_root = Path(data_root).expanduser().resolve()
        if not self._data_root.is_absolute():
            raise ProductionRootDispositionRefused("data_root must be absolute")
        if not isinstance(p6_receipt_id, str) or not p6_receipt_id:
            raise ProductionRootDispositionRefused("p6_receipt_id must be non-empty")
        _require_digest(plan_digest, "plan_digest")
        self._p6_receipt_id = p6_receipt_id
        self._plan_digest = plan_digest
        self._character_requests = tuple(character_requests)
        self._trajectory_binding = trajectory_binding
        self._trajectory_instructions = tuple(trajectory_instructions)
        if not self._character_requests or any(not isinstance(item, CharacterBaselineRequest) for item in self._character_requests):
            raise ProductionRootDispositionRefused("Character disposition requires typed baseline requests")
        if not isinstance(trajectory_binding, TrajectoryHandoffBinding):
            raise ProductionRootDispositionRefused("trajectory binding must be typed")
        if not self._trajectory_instructions or any(not isinstance(item, TrajectoryScopeHandoffInstruction) for item in self._trajectory_instructions):
            raise ProductionRootDispositionRefused("trajectory disposition requires typed scope instructions")
        if len({item.scope.exclusivity_key for item in self._trajectory_instructions}) != len(self._trajectory_instructions):
            raise ProductionRootDispositionRefused("trajectory instructions overlap a writer exclusivity key")
        supplied_receipt_only = tuple(receipt_only_evidence)
        supplied_synthetic_only = tuple(synthetic_only_evidence)
        if any(not isinstance(item, ReceiptOnlyDispositionEvidence) for item in supplied_receipt_only):
            raise ProductionRootDispositionRefused("receipt-only evidence must be typed")
        if any(not isinstance(item, SyntheticOnlyDispositionEvidence) for item in supplied_synthetic_only):
            raise ProductionRootDispositionRefused("synthetic-only evidence must be typed")
        self._receipt_only = {item.owner_identity: item for item in supplied_receipt_only}
        self._synthetic_only = {item.owner_identity: item for item in supplied_synthetic_only}
        if len(self._receipt_only) != len(supplied_receipt_only) or len(self._synthetic_only) != len(supplied_synthetic_only):
            raise ProductionRootDispositionRefused("production disposition evidence has duplicate owners")
        if set(self._receipt_only) != _RECEIPT_ONLY:
            raise ProductionRootDispositionRefused("receipt-only evidence census is incomplete")
        if set(self._synthetic_only) != _SYNTHETIC_ONLY:
            raise ProductionRootDispositionRefused("synthetic-only evidence census is incomplete")
        # Owner sidecars are created only when their corresponding plan entry
        # is actually executed. Constructing an adapter grants no mutation.
        self._character_owner: CharacterBaselineDispositionOwner | None = None
        self._trajectory: TrajectoryWriterHandoffCoordinator | None = None

    def execute(
        self,
        *, entry: RootGeometryDispositionPlanEntry,
        root_admission_envelope_digest: str,
        geometry_transition_identity: str,
    ) -> str:
        """Execute exactly the owner named by one frozen geometry-plan entry."""
        if not isinstance(entry, RootGeometryDispositionPlanEntry):
            raise ProductionRootDispositionRefused("production disposition entry must be typed")
        _require_digest(root_admission_envelope_digest, "root_admission_envelope_digest")
        if not isinstance(geometry_transition_identity, str) or not geometry_transition_identity:
            raise ProductionRootDispositionRefused("geometry_transition_identity must be non-empty")
        if entry.owner_identity == _CHARACTER:
            return self._character_outcome(entry, root_admission_envelope_digest)
        if entry.owner_identity == _TRAJECTORY:
            return self._trajectory_outcome(entry, root_admission_envelope_digest)
        if entry.owner_identity in _RECEIPT_ONLY:
            return self._receipt_only_outcome(entry, root_admission_envelope_digest)
        if entry.owner_identity in _SYNTHETIC_ONLY:
            return self._synthetic_only_outcome(entry, root_admission_envelope_digest)
        raise ProductionRootDispositionRefused("frozen plan names an unknown disposition owner")

    def _character_outcome(self, entry: RootGeometryDispositionPlanEntry, envelope: str) -> str:
        receipts: list[CharacterBaselineReceipt] = []
        for request in self._character_requests:
            binding = request.binding
            if (
                binding.p6_receipt_id != self._p6_receipt_id
                or binding.root_admission_envelope_digest != envelope
                or binding.plan_digest != self._plan_digest
            ):
                raise ProductionRootDispositionRefused("Character request P6/root/plan binding disagrees")
            receipts.append(self._character_owner_for_execution().execute(request))
        if entry.disposition != "RECOMPUTE_TARGET_GEOMETRY_BASELINE":
            raise ProductionRootDispositionRefused("Character plan disposition disagrees with owner law")
        return "PRODUCTION_CHARACTER_BASELINE:" + ";".join(sorted(item.digest for item in receipts))

    def _trajectory_outcome(self, entry: RootGeometryDispositionPlanEntry, envelope: str) -> str:
        binding = self._trajectory_binding
        if (
            binding.p6_receipt_id != self._p6_receipt_id
            or binding.root_admission_envelope_digest != envelope
            or binding.plan_digest != self._plan_digest
            or entry.disposition != "RETAIN"
        ):
            raise ProductionRootDispositionRefused("trajectory P6/root/plan binding disagrees")
        coordinator = self._trajectory_for_execution()
        for instruction in self._trajectory_instructions:
            phase = coordinator.initialize_legacy_scope(
                scope=instruction.scope, binding=binding,
                legacy_writer_identity=instruction.legacy_writer_identity,
                operation_key=instruction.operation_key,
            )
            if phase is TrajectoryHandoffPhase.LEGACY_AUTHORITATIVE:
                phase = coordinator.begin_quiescing(
                    scope=instruction.scope, operation_key=instruction.operation_key,
                    evidence_digest=instruction.quiescing_evidence_digest,
                )
            if phase is TrajectoryHandoffPhase.QUIESCING:
                phase = coordinator.fence_legacy_after_quiescence(
                    scope=instruction.scope, operation_key=instruction.operation_key,
                    quiescence_evidence_digest=instruction.quiescence_evidence_digest,
                )
            if phase is TrajectoryHandoffPhase.LEGACY_QUIESCED:
                phase = coordinator.begin_native_admission(
                    scope=instruction.scope, operation_key=instruction.operation_key,
                    evidence_digest=instruction.native_admission_evidence_digest,
                )
            if phase is TrajectoryHandoffPhase.NATIVE_ADMITTING:
                coordinator.admit_native_writer(
                    scope=instruction.scope, operation_key=instruction.operation_key,
                    native_writer_identity=instruction.native_writer_identity,
                    native_admission_evidence_digest=instruction.native_admission_evidence_digest,
                )
                phase = TrajectoryHandoffPhase.NATIVE_AUTHORITATIVE
            if phase is TrajectoryHandoffPhase.NATIVE_AUTHORITATIVE:
                coordinator.complete_handoff(scope=instruction.scope, operation_key=instruction.operation_key)
            elif phase is not TrajectoryHandoffPhase.HANDOFF_COMPLETE:
                raise ProductionRootDispositionRefused("trajectory handoff is in an illegal partial phase")
        aggregate = coordinator.aggregate_receipt(
            expected_scopes=tuple(item.scope for item in self._trajectory_instructions), binding=binding,
        )
        return "PRODUCTION_TRAJECTORY_HANDOFF:" + aggregate.digest

    def _receipt_only_outcome(self, entry: RootGeometryDispositionPlanEntry, envelope: str) -> str:
        evidence = self._receipt_only[entry.owner_identity]
        if (
            evidence.root_admission_envelope_digest != envelope
            or evidence.plan_digest != self._plan_digest
            or evidence.source_observation_digest != entry.source_observation_digest
        ):
            raise ProductionRootDispositionRefused("receipt-only evidence does not bind the frozen plan entry")
        return "PRODUCTION_RECEIPT_ONLY:" + evidence.evidence_digest

    def _synthetic_only_outcome(self, entry: RootGeometryDispositionPlanEntry, envelope: str) -> str:
        evidence = self._synthetic_only[entry.owner_identity]
        if (
            evidence.root_admission_envelope_digest != envelope
            or evidence.plan_digest != self._plan_digest
            or evidence.source_observation_digest != entry.source_observation_digest
        ):
            raise ProductionRootDispositionRefused("synthetic-only classification does not bind frozen evidence")
        return "PRODUCTION_SYNTHETIC_ONLY:" + evidence.classification_evidence_digest

    def _character_owner_for_execution(self) -> CharacterBaselineDispositionOwner:
        if self._character_owner is None:
            self._character_owner = CharacterBaselineDispositionOwner(
                data_root=self._data_root, store=CharacterStore(str(self._data_root)),
            )
        return self._character_owner

    def _trajectory_for_execution(self) -> TrajectoryWriterHandoffCoordinator:
        if self._trajectory is None:
            self._trajectory = TrajectoryWriterHandoffCoordinator.create(data_root=self._data_root)
        return self._trajectory


def verify_production_root_disposition_receipt(
    *, data_root: str | Path, receipt: RootDispositionExecutionReceipt,
) -> None:
    """P7-time read-only proof that the aggregate receipt is production law."""
    if not isinstance(receipt, RootDispositionExecutionReceipt):
        raise ProductionRootDispositionRefused("root disposition receipt must be typed")
    results = {item.owner_identity: item for item in receipt.owner_results}
    character = _parse_token(results[_CHARACTER], "PRODUCTION_CHARACTER_BASELINE:", allow_many=True)
    trajectory = _parse_token(results[_TRAJECTORY], "PRODUCTION_TRAJECTORY_HANDOFF:", allow_many=False)
    for owner in _RECEIPT_ONLY:
        _parse_token(results[owner], "PRODUCTION_RECEIPT_ONLY:", allow_many=False)
    for owner in _SYNTHETIC_ONLY:
        _parse_token(results[owner], "PRODUCTION_SYNTHETIC_ONLY:", allow_many=False)
    root = Path(data_root).expanduser().resolve()
    character_owner = CharacterBaselineDispositionOwner(data_root=root, store=CharacterStore(str(root)))
    try:
        for digest in character:
            proof = character_owner.verify_completed_receipt_digest(digest)
            binding = proof.request.binding
            if (
                binding.root_admission_envelope_digest != receipt.root_admission_envelope_digest
                or binding.plan_digest != receipt.geometry_disposition_table_digest
                or binding.corrected_core_id != receipt.native_staging_core_id
            ):
                raise ProductionRootDispositionRefused("Character baseline proof disagrees with root receipt")
        coordinator = TrajectoryWriterHandoffCoordinator.open_existing(data_root=root)
        aggregate = coordinator.verify_aggregate_receipt_digest(trajectory[0])
        if (
            aggregate.binding.root_admission_envelope_digest != receipt.root_admission_envelope_digest
            or aggregate.binding.plan_digest != receipt.geometry_disposition_table_digest
            or aggregate.binding.corrected_core_id != receipt.native_staging_core_id
        ):
            raise ProductionRootDispositionRefused("trajectory aggregate proof disagrees with root receipt")
    except ProductionRootDispositionRefused:
        raise
    except DeploymentAuthorityError as exc:
        raise ProductionRootDispositionRefused("production owner proof is absent or inconsistent") from exc


def _parse_token(result: RootDispositionOwnerResult, prefix: str, *, allow_many: bool) -> tuple[str, ...]:
    if not result.outcome.startswith(prefix):
        raise ProductionRootDispositionRefused("root disposition outcome does not prove its production owner")
    values = tuple(result.outcome[len(prefix):].split(";"))
    if not values or (not allow_many and len(values) != 1):
        raise ProductionRootDispositionRefused("root disposition outcome token has invalid cardinality")
    for value in values:
        _require_digest(value, "root disposition outcome digest")
    return values


__all__ = [
    "ProductionRootDispositionAdapter", "ProductionRootDispositionRefused",
    "ReceiptOnlyDispositionEvidence", "SyntheticOnlyDispositionEvidence",
    "TrajectoryScopeHandoffInstruction", "verify_production_root_disposition_receipt",
]

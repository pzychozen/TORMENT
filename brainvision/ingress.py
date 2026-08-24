"""Phase-11 direct typed FIRSTHAND_VISUAL admission.

This module owns only the narrow admission boundary between a validated
Phase-2 observation and the locked Phase-10 successor-commit transaction. It
does not parse observations, persist state directly, or contact ordinary
TORMENT ingestion, memory, cognition, kernel, or model paths.
"""

from __future__ import annotations

from dataclasses import dataclass

from brainvision.character_modulation import update_vhe_state_with_character_modulation
from brainvision.lifecycle import BrainvisionLifecycleManager
from brainvision.observation import (
    FirsthandVisualObservationV1,
    derive_observation_id,
)


class BrainvisionIngressError(ValueError):
    """One distinct Phase-11-owned admission failure."""

    def __init__(self, field: str, reason: str) -> None:
        self.field = field
        self.reason = reason
        super().__init__(f"{field}: {reason}")


@dataclass(frozen=True, kw_only=True)
class FirsthandVisualAdmissionReceipt:
    """Minimal immutable evidence of one durably accepted observation."""

    observation_id: str
    source_sequence: int
    committed_active_time_ns: int

    def __post_init__(self) -> None:
        if type(self.observation_id) is not str:
            raise TypeError("observation_id must be str")
        if type(self.source_sequence) is not int or self.source_sequence < 0:
            raise TypeError("source_sequence must be a nonnegative exact int")
        if (
            type(self.committed_active_time_ns) is not int
            or self.committed_active_time_ns < 0
        ):
            raise TypeError("committed_active_time_ns must be a nonnegative exact int")


def _admit_firsthand_visual_observation_with_committed_snapshot(
    *,
    lifecycle_manager: BrainvisionLifecycleManager,
    workspace_id: str,
    agent_id: str,
    observation: FirsthandVisualObservationV1,
    capture_committed_snapshot,
) -> tuple[FirsthandVisualAdmissionReceipt, object]:
    """Admit once and privately capture the committed snapshot under its lock."""

    if type(observation) is not FirsthandVisualObservationV1:
        raise BrainvisionIngressError("observation", "malformed_observation")

    with lifecycle_manager.active_transaction(workspace_id, agent_id) as transaction:
        configuration = transaction.configuration
        if observation.stream_identity != configuration.stream_identity:
            raise BrainvisionIngressError(
                "stream_identity", "stream_identity_mismatch"
            )
        if observation.adapter_contract_id != configuration.adapter_contract_id:
            raise BrainvisionIngressError(
                "adapter_contract_id", "adapter_contract_mismatch"
            )
        if observation.source_sequence <= transaction.current_replay_watermark:
            raise BrainvisionIngressError("source_sequence", "refused_replay")

        if observation.observation_id != derive_observation_id(
            observation.stream_identity,
            observation.source_sequence,
        ):
            raise BrainvisionIngressError("observation_id", "invalid_observation_id")

        try:
            update_result = update_vhe_state_with_character_modulation(
                state=transaction.base_vhe_state,
                descriptor=observation.descriptor,
                semantic_event_class=observation.semantic_event_class,
                prior_committed_active_time_ns=(
                    transaction.prior_committed_active_time_ns
                ),
                elapsed_active_time_ns=transaction.elapsed_active_time_ns,
                theta=configuration.theta,
            )
        except Exception as error:
            raise BrainvisionIngressError(
                "successor", "successor_derivation_failure"
            ) from error

        if update_result.event_active_time_ns != transaction.cutoff_active_time_ns:
            raise BrainvisionIngressError(
                "event_active_time_ns", "successor_derivation_failure"
            )

        committed = transaction.commit_successor(
            update_result.state,
            observation.source_sequence,
        )
        receipt = FirsthandVisualAdmissionReceipt(
            observation_id=observation.observation_id,
            source_sequence=observation.source_sequence,
            committed_active_time_ns=committed.active_time_ns,
        )
        return receipt, capture_committed_snapshot(receipt, committed)


def admit_firsthand_visual_observation(
    *,
    lifecycle_manager: BrainvisionLifecycleManager,
    workspace_id: str,
    agent_id: str,
    observation: FirsthandVisualObservationV1,
) -> FirsthandVisualAdmissionReceipt:
    """Admit one exact Phase-2 observation through the Phase-10 boundary."""

    receipt, _ = _admit_firsthand_visual_observation_with_committed_snapshot(
        lifecycle_manager=lifecycle_manager,
        workspace_id=workspace_id,
        agent_id=agent_id,
        observation=observation,
        capture_committed_snapshot=lambda _receipt, _snapshot: None,
    )
    return receipt


__all__ = (
    "BrainvisionIngressError",
    "FirsthandVisualAdmissionReceipt",
    "admit_firsthand_visual_observation",
)

"""Qualification-only storage adapter for already-authorized share proposals.

This module deliberately has no access to ``TormentFabric`` or to proposal,
bridge, conflict, or domain-suggestion registries.  Existing TORMENT authority
paths decide whether a quorum or operator approval exists; this adapter only
turns those durable facts into one explicitly-qualified native router request.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from torment_service.collective_models import MemoryGovernanceFlags
from torment_service.embeddings import embedding_checksum
from torment_service.proposals import ShareProposal
from torment_service.provenance_v1 import ProvenanceV1

from .fabric_native_routing import (
    NativeFabricMemoryRouter,
    NativeFabricRouteAttempt,
    NativeFabricRouteRequest,
    NativeFabricRoutingCapability,
)


_COLLECTIVE_AGENT_ID = "collective"
_SHARED_SCOPE = "shared"
_CANON_LIFECYCLE_STATE = "PROTECTED"
_CANON_GOVERNANCE_STATE = "EXPLICIT"


@dataclass(frozen=True)
class NativeSharedProposalStorageClock:
    """Caller-owned, retry-stable storage times for one materialization.

    The adapter intentionally never calls a clock.  In particular, production
    ownership of a retry-stable operator approval step remains outside this
    qualification-only boundary.
    """

    logical_step: int
    created_ts: int
    last_active_ts: int
    last_reinforced_ts: int

    def __post_init__(self) -> None:
        for field_name in (
            "logical_step",
            "created_ts",
            "last_active_ts",
            "last_reinforced_ts",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"{field_name} must be a non-negative integer")


@dataclass(frozen=True)
class AuthorizedSharedProposalQuorum:
    """Facts emitted after existing TORMENT quorum authority has succeeded.

    ``representative`` and ``support_agents`` are inputs from that authority
    decision.  This object validates only storage-input coherence; it does not
    count agents, regroup proposals, or select a representative.
    """

    workspace_id: str
    domain_id: str
    representative: ShareProposal
    participating_proposals: tuple[ShareProposal, ...] | list[ShareProposal]
    support_agents: tuple[str, ...] | list[str]
    embedding_provider: str
    embedding_model: str

    def __post_init__(self) -> None:
        _require_text("workspace_id", self.workspace_id)
        _require_text("domain_id", self.domain_id)
        _require_text("embedding_provider", self.embedding_provider)
        _require_text("embedding_model", self.embedding_model)
        _require_proposal(self.representative)
        proposals = tuple(self.participating_proposals)
        if not proposals:
            raise ValueError("participating_proposals must be non-empty")
        for proposal in proposals:
            _require_proposal(proposal)
            if proposal.workspace_id != self.workspace_id or proposal.domain_id != self.domain_id:
                raise ValueError("participating proposals must match the authorized target scope")
        proposal_ids = tuple(proposal.proposal_id for proposal in proposals)
        if len(set(proposal_ids)) != len(proposal_ids):
            raise ValueError("participating proposals must have distinct proposal IDs")
        if self.representative.proposal_id not in proposal_ids:
            raise ValueError("representative must be a participating proposal")
        if (
            self.representative.workspace_id != self.workspace_id
            or self.representative.domain_id != self.domain_id
        ):
            raise ValueError("representative must match the authorized target scope")
        support_agents = tuple(self.support_agents)
        if not support_agents:
            raise ValueError("support_agents must be non-empty already-authorized facts")
        if any(not isinstance(agent_id, str) or not agent_id for agent_id in support_agents):
            raise ValueError("support_agents must contain non-empty text")
        if support_agents != tuple(sorted(set(support_agents))):
            raise ValueError("support_agents must be distinct and sorted")
        object.__setattr__(self, "participating_proposals", proposals)
        object.__setattr__(self, "support_agents", support_agents)


@dataclass(frozen=True)
class AuthorizedSharedProposalOperator:
    """Facts emitted after an existing TORMENT operator approval succeeds."""

    workspace_id: str
    domain_id: str
    proposal: ShareProposal
    embedding_provider: str
    embedding_model: str

    def __post_init__(self) -> None:
        _require_text("workspace_id", self.workspace_id)
        _require_text("domain_id", self.domain_id)
        _require_text("embedding_provider", self.embedding_provider)
        _require_text("embedding_model", self.embedding_model)
        _require_proposal(self.proposal)
        if self.proposal.workspace_id != self.workspace_id or self.proposal.domain_id != self.domain_id:
            raise ValueError("proposal must match the authorized target scope")


class NativeAuthorizedSharedProposalMaterializer:
    """Build and route native storage requests for already-authorized facts.

    The prepared STAGING capability is required at construction.  The router
    remains the sole qualification and SQLite mutation boundary, including its
    explicit claimed-``SHARED_DOMAIN`` scope check and retry protocol.
    """

    def __init__(self, capability: NativeFabricRoutingCapability) -> None:
        if not isinstance(capability, NativeFabricRoutingCapability):
            raise ValueError("a prepared NativeFabricRoutingCapability is required")
        self._capability = capability
        self._router = NativeFabricMemoryRouter(capability)

    def build_quorum_request(
        self,
        *,
        authorization: AuthorizedSharedProposalQuorum,
        native_operation_key: str,
        clock: NativeSharedProposalStorageClock,
    ) -> NativeFabricRouteRequest:
        """Construct, but do not route, one authorized quorum storage request."""
        if not isinstance(authorization, AuthorizedSharedProposalQuorum):
            raise ValueError("authorized quorum facts are required")
        _require_operation_key(native_operation_key)
        _require_clock(clock)
        representative = authorization.representative
        return self._build_request(
            workspace_id=authorization.workspace_id,
            domain_id=authorization.domain_id,
            proposal=representative,
            embedding_provider=authorization.embedding_provider,
            embedding_model=authorization.embedding_model,
            source="proposal_group",
            support_agents=authorization.support_agents,
            source_proposal_ids=tuple(
                proposal.proposal_id for proposal in authorization.participating_proposals
            ),
            provenance=ProvenanceV1.for_share_proposal_quorum(
                contributing_created_ts=(
                    proposal.created_ts for proposal in authorization.participating_proposals
                )
            ),
            native_operation_key=native_operation_key,
            clock=clock,
        )

    def build_operator_request(
        self,
        *,
        authorization: AuthorizedSharedProposalOperator,
        native_operation_key: str,
        clock: NativeSharedProposalStorageClock,
    ) -> NativeFabricRouteRequest:
        """Construct, but do not route, one operator-authorized storage request."""
        if not isinstance(authorization, AuthorizedSharedProposalOperator):
            raise ValueError("authorized operator facts are required")
        _require_operation_key(native_operation_key)
        _require_clock(clock)
        proposal = authorization.proposal
        return self._build_request(
            workspace_id=authorization.workspace_id,
            domain_id=authorization.domain_id,
            proposal=proposal,
            embedding_provider=authorization.embedding_provider,
            embedding_model=authorization.embedding_model,
            source="proposal_manual",
            support_agents=(proposal.agent_id,),
            source_proposal_ids=None,
            provenance=ProvenanceV1.for_share_proposal_operator(
                proposal_created_ts=proposal.created_ts,
            ),
            native_operation_key=native_operation_key,
            clock=clock,
        )

    def materialize_quorum(
        self,
        *,
        authorization: AuthorizedSharedProposalQuorum,
        native_operation_key: str,
        clock: NativeSharedProposalStorageClock,
        _test_stop_after: str | None = None,
    ) -> NativeFabricRouteAttempt:
        """Route one already-authorized quorum fact set; never decide quorum."""
        return self._router.route(
            self.build_quorum_request(
                authorization=authorization,
                native_operation_key=native_operation_key,
                clock=clock,
            ),
            _test_stop_after=_test_stop_after,
        )

    def materialize_operator(
        self,
        *,
        authorization: AuthorizedSharedProposalOperator,
        native_operation_key: str,
        clock: NativeSharedProposalStorageClock,
        _test_stop_after: str | None = None,
    ) -> NativeFabricRouteAttempt:
        """Route one already-authorized operator fact set; never approve one."""
        return self._router.route(
            self.build_operator_request(
                authorization=authorization,
                native_operation_key=native_operation_key,
                clock=clock,
            ),
            _test_stop_after=_test_stop_after,
        )

    def _build_request(
        self,
        *,
        workspace_id: str,
        domain_id: str,
        proposal: ShareProposal,
        embedding_provider: str,
        embedding_model: str,
        source: str,
        support_agents: tuple[str, ...],
        source_proposal_ids: tuple[str, ...] | None,
        provenance: ProvenanceV1,
        native_operation_key: str,
        clock: NativeSharedProposalStorageClock,
    ) -> NativeFabricRouteRequest:
        embedding = np.asarray(proposal.embedding, dtype=np.float32)
        if embedding.ndim != 1:
            embedding = embedding.reshape(-1)
        payload: dict[str, Any] = {
            "workspace_id": workspace_id,
            "domain_id": domain_id,
            "agent_id": _COLLECTIVE_AGENT_ID,
            "source": source,
            "embedding_provider": embedding_provider,
            "embedding_model": embedding_model,
            "embedding_dim": int(embedding.shape[0]),
            "embedding_checksum": embedding_checksum(
                proposal.summary, embedding_provider, embedding_model,
            ),
            "support_agents": list(support_agents),
            # ``canon`` remains a legacy compatibility payload fact.  The
            # typed native lifecycle fields below are the structural mapping.
            "canon": True,
            "created_ts": clock.created_ts,
        }
        if source_proposal_ids is not None:
            payload["source_proposal_ids"] = list(source_proposal_ids)
        return NativeFabricRouteRequest(
            workspace_id=workspace_id,
            scope=_SHARED_SCOPE,
            agent_id=_COLLECTIVE_AGENT_ID,
            domain_id=domain_id,
            native_operation_key=native_operation_key,
            embedder_lane=self._capability.binding.representation_lane,
            summary=proposal.summary,
            memory_type=proposal.mtype,
            memory_class="core",
            strength=max(0.7, float(proposal.strength)),
            confidence=max(0.7, float(proposal.confidence)),
            half_life_days=30.0,
            logical_step=clock.logical_step,
            created_ts=clock.created_ts,
            last_active_ts=clock.last_active_ts,
            last_reinforced_ts=clock.last_reinforced_ts,
            incoming_embedding=embedding,
            provenance=provenance,
            # Canon implies lifecycle protection; it does not imply an
            # independent governance flag in the legacy proposal writer.
            governance=MemoryGovernanceFlags(),
            flexible_payload=payload,
            lifecycle_state=_CANON_LIFECYCLE_STATE,
            lifecycle_authoritative=True,
            governance_state=_CANON_GOVERNANCE_STATE,
            attach_threshold=0.62,
        )


def _require_text(field_name: str, value: object) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} must be non-empty text")


def _require_operation_key(value: object) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError("native_operation_key must be caller-supplied non-empty text")


def _require_clock(value: object) -> None:
    if not isinstance(value, NativeSharedProposalStorageClock):
        raise ValueError("a NativeSharedProposalStorageClock is required")


def _require_proposal(value: object) -> None:
    if not isinstance(value, ShareProposal):
        raise ValueError("ShareProposal facts are required")
    for field_name in ("proposal_id", "workspace_id", "domain_id", "agent_id", "summary", "mtype"):
        _require_text(field_name, getattr(value, field_name))
    if not isinstance(value.created_ts, int) or isinstance(value.created_ts, bool) or value.created_ts < 0:
        raise ValueError("proposal.created_ts must be a non-negative integer")


__all__ = [
    "AuthorizedSharedProposalOperator",
    "AuthorizedSharedProposalQuorum",
    "NativeAuthorizedSharedProposalMaterializer",
    "NativeSharedProposalStorageClock",
]

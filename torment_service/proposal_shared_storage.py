"""Backend-neutral storage seam for already-authorized shared proposals.

This module deliberately starts *after* TORMENT has selected a quorum
representative or accepted an operator decision.  Proposal authority,
conflicts, proposal events, bridges, and domain suggestions remain Fabric
workflows.  The native implementation composes the existing qualified writer
and readers; it neither selects storage for production nor owns any external
side-store.
"""
from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any, Protocol

import numpy as np

from .embeddings import embedding_checksum
from .motif_geometry_port import MotifGeometryPort
from .motif_maintenance import NativeMotifMaintenanceAdapter
from .proposals import ShareProposal
from .substrate.native_memory_vector_runtime import NativeMemoryVectorRuntime
from .substrate.authorized_proposal_receipts import (
    AuthorizedProposalReceipt,
    NativeAuthorizedProposalReceiptStore,
)
from .substrate.shared_proposal_materialization import (
    AuthorizedSharedProposalOperator,
    AuthorizedSharedProposalQuorum,
    NativeAuthorizedSharedProposalMaterializer,
    NativeSharedProposalStorageClock,
)


@dataclass(frozen=True)
class SharedProposalMaterialization:
    """One already-authorized shared-memory result exposed to Fabric."""

    eid: int
    created_new: bool


class AuthorizedSharedProposalStorage(Protocol):
    """The small storage dependency needed by proposal orchestration."""

    geometry: MotifGeometryPort

    def pre_conflict_read(self, embedding: Any) -> list[dict[str, Any]]: ...

    def materialize_quorum(
        self,
        *,
        workspace_id: str,
        domain_id: str,
        representative: ShareProposal,
        participating_proposals: tuple[ShareProposal, ...],
        support_agents: tuple[str, ...],
        embedding_provider: str,
        embedding_model: str,
        step: int | None,
        receipt: Any | None = None,
    ) -> SharedProposalMaterialization: ...

    def materialize_operator(
        self,
        *,
        workspace_id: str,
        domain_id: str,
        proposal: ShareProposal,
        embedding_provider: str,
        embedding_model: str,
        receipt: Any | None = None,
    ) -> SharedProposalMaterialization: ...

    def ensure_motif_current(
        self,
        *,
        embedding: np.ndarray,
        eid: int,
        summary: str,
    ) -> None: ...

    def update_motif_maintenance(self, policy: dict[str, Any]) -> dict[str, Any]: ...


class LegacyAuthorizedSharedProposalStorage:
    """Compatibility implementation retaining the existing JSON/graph writes."""

    def __init__(self, *, shared_graph: Any, motif_registry: Any, geometry: MotifGeometryPort) -> None:
        self._shared_graph = shared_graph
        self._motif_registry = motif_registry
        self.geometry = geometry

    def pre_conflict_read(self, embedding: Any) -> list[dict[str, Any]]:
        return self._shared_graph.search_by_embedding(
            embedding, top_k=6, user_id=None, canon_only=True,
        )

    def materialize_quorum(
        self,
        *,
        workspace_id: str,
        domain_id: str,
        representative: ShareProposal,
        participating_proposals: tuple[ShareProposal, ...],
        support_agents: tuple[str, ...],
        embedding_provider: str,
        embedding_model: str,
        step: int | None,
        receipt: Any | None = None,
    ) -> SharedProposalMaterialization:
        return self._materialize(
            workspace_id=workspace_id,
            domain_id=domain_id,
            proposal=representative,
            embedding_provider=embedding_provider,
            embedding_model=embedding_model,
            source="proposal_group",
            support_agents=support_agents,
            source_proposal_ids=tuple(item.proposal_id for item in participating_proposals),
            step=step,
        )

    def materialize_operator(
        self,
        *,
        workspace_id: str,
        domain_id: str,
        proposal: ShareProposal,
        embedding_provider: str,
        embedding_model: str,
        receipt: Any | None = None,
    ) -> SharedProposalMaterialization:
        return self._materialize(
            workspace_id=workspace_id,
            domain_id=domain_id,
            proposal=proposal,
            embedding_provider=embedding_provider,
            embedding_model=embedding_model,
            source="proposal_manual",
            support_agents=(proposal.agent_id,),
            source_proposal_ids=None,
            step=None,
        )

    def ensure_motif_current(
        self,
        *,
        embedding: np.ndarray,
        eid: int,
        summary: str,
    ) -> None:
        # This remains after conflict recording to preserve the legacy
        # process_proposals order.  Native publication has already performed
        # its structural motif attach/create/split and is a no-op here.
        self._motif_registry.attach_or_create(
            embedding,
            memory_eid=int(eid),
            agent_id="collective",
            summary=summary,
            attach_threshold=0.62,
        )

    def update_motif_maintenance(self, policy: dict[str, Any]) -> dict[str, Any]:
        return self._motif_registry.update_entropy_and_suggest(
            target_n=int(policy.get("motif_entropy_target_n", 24)),
            entropy_high=float(policy.get("motif_entropy_high", 0.72)),
            sim_threshold=float(policy.get("motif_merge_similarity", 0.93)),
            max_suggestions=int(policy.get("motif_merge_max_suggestions", 20)),
            auto_merge=bool(policy.get("auto_merge_motifs", False)),
            auto_merge_trigger=float(policy.get("auto_merge_entropy_trigger", 0.80)),
        )

    def _materialize(
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
        step: int | None,
    ) -> SharedProposalMaterialization:
        embedding = np.asarray(proposal.embedding, dtype=np.float32)
        payload: dict[str, Any] = {
            "workspace_id": workspace_id,
            "domain_id": domain_id,
            "scope": "shared",
            "agent_id": "collective",
            "source": source,
            "embedding_provider": embedding_provider,
            "embedding_model": embedding_model,
            "embedding_dim": int(np.asarray(embedding).reshape(-1).shape[0]),
            "embedding_checksum": embedding_checksum(
                proposal.summary, embedding_provider, embedding_model,
            ),
            "support_agents": list(support_agents),
        }
        if source_proposal_ids is not None:
            payload["source_proposal_ids"] = list(source_proposal_ids)
        eid = self._shared_graph.add_memory(
            summary=proposal.summary,
            embedding=embedding,
            mtype=proposal.mtype,
            strength=max(0.7, float(proposal.strength)),
            confidence=max(0.7, float(proposal.confidence)),
            half_life_days=30.0,
            links=[],
            canon=True,
            user_id="collective",
            step=step if step is not None else int(time.time()),
            extra_payload=payload,
        )
        return SharedProposalMaterialization(eid=int(eid), created_new=True)


class NativeAuthorizedSharedProposalStorage:
    """Explicit qualification-only native implementation of the storage port.

    All native dependencies are caller-supplied qualified instances.  This is
    intentionally not constructible from a ``TormentFabric`` workspace and
    therefore cannot become a production selector by accident.
    """

    def __init__(
        self,
        *,
        materializer: NativeAuthorizedSharedProposalMaterializer,
        vector_runtime: NativeMemoryVectorRuntime,
        geometry: MotifGeometryPort,
        motif_maintenance: NativeMotifMaintenanceAdapter,
        receipts: NativeAuthorizedProposalReceiptStore,
    ) -> None:
        if not isinstance(materializer, NativeAuthorizedSharedProposalMaterializer):
            raise ValueError("native proposal storage requires the qualified materializer")
        if not isinstance(vector_runtime, NativeMemoryVectorRuntime):
            raise ValueError("native proposal storage requires a qualified vector runtime")
        if not isinstance(geometry, MotifGeometryPort):
            raise ValueError("native proposal storage requires qualified native motif geometry")
        if not isinstance(motif_maintenance, NativeMotifMaintenanceAdapter):
            raise ValueError("native proposal storage requires qualified native motif maintenance")
        if not isinstance(receipts, NativeAuthorizedProposalReceiptStore):
            raise ValueError("native proposal storage requires qualified recovery receipts")
        self._materializer = materializer
        self._vector_runtime = vector_runtime
        self.geometry = geometry
        self._motif_maintenance = motif_maintenance
        self.receipts = receipts

    def pre_conflict_read(self, embedding: Any) -> list[dict[str, Any]]:
        # This is the established exact MemoryGraph-shaped native vector
        # runtime.  It is deliberately not an ad-hoc SQLite cosine query.
        return self._vector_runtime.search_by_embedding(
            embedding, top_k=6, user_id=None, canon_only=True,
        )

    def materialize_quorum(
        self,
        *,
        workspace_id: str,
        domain_id: str,
        representative: ShareProposal,
        participating_proposals: tuple[ShareProposal, ...],
        support_agents: tuple[str, ...],
        embedding_provider: str,
        embedding_model: str,
        step: int | None,
        receipt: AuthorizedProposalReceipt | None = None,
    ) -> SharedProposalMaterialization:
        if receipt is not None:
            self.receipts.require_current_core(receipt)
            if receipt.kind != "QUORUM":
                raise ValueError("quorum storage requires a quorum receipt")
            if receipt.native_storage_key != native_quorum_operation_key(
                workspace_id, domain_id, participating_proposals,
            ):
                raise ValueError("quorum receipt native storage key differs")
            clock = receipt.clock
            native_operation_key = receipt.native_storage_key
        else:
            now = int(time.time())
            clock = NativeSharedProposalStorageClock(
                logical_step=int(step) if step is not None else now,
                created_ts=now,
                last_active_ts=now,
                last_reinforced_ts=now,
            )
            native_operation_key = native_quorum_operation_key(
                workspace_id, domain_id, participating_proposals,
            )
        authorization = AuthorizedSharedProposalQuorum(
            workspace_id=workspace_id,
            domain_id=domain_id,
            representative=representative,
            participating_proposals=participating_proposals,
            support_agents=support_agents,
            embedding_provider=embedding_provider,
            embedding_model=embedding_model,
        )
        attempt = self._materializer.materialize_quorum(
            authorization=authorization,
            native_operation_key=native_operation_key,
            clock=clock,
        )
        return self._native_result(attempt)

    def materialize_operator(
        self,
        *,
        workspace_id: str,
        domain_id: str,
        proposal: ShareProposal,
        embedding_provider: str,
        embedding_model: str,
        receipt: AuthorizedProposalReceipt | None = None,
    ) -> SharedProposalMaterialization:
        if receipt is not None:
            self.receipts.require_current_core(receipt)
            if receipt.kind != "OPERATOR_APPROVE":
                raise ValueError("operator storage requires an operator receipt")
            if receipt.native_storage_key != native_operator_operation_key(
                workspace_id, domain_id, proposal,
            ):
                raise ValueError("operator receipt native storage key differs")
            clock = receipt.clock
            native_operation_key = receipt.native_storage_key
        else:
            now = int(time.time())
            clock = NativeSharedProposalStorageClock(now, now, now, now)
            native_operation_key = native_operator_operation_key(workspace_id, domain_id, proposal)
        authorization = AuthorizedSharedProposalOperator(
            workspace_id=workspace_id,
            domain_id=domain_id,
            proposal=proposal,
            embedding_provider=embedding_provider,
            embedding_model=embedding_model,
        )
        attempt = self._materializer.materialize_operator(
            authorization=authorization,
            native_operation_key=native_operation_key,
            clock=clock,
        )
        return self._native_result(attempt)

    def ensure_motif_current(
        self,
        *,
        embedding: np.ndarray,
        eid: int,
        summary: str,
    ) -> None:
        # NativeAuthorizedSharedProposalMaterializer owns motif attachment.
        # Calling an additional attach path would double-write membership truth.
        return None

    def update_motif_maintenance(self, policy: dict[str, Any]) -> dict[str, Any]:
        return self._motif_maintenance.update_entropy_and_suggest(
            target_n=int(policy.get("motif_entropy_target_n", 24)),
            entropy_high=float(policy.get("motif_entropy_high", 0.72)),
            sim_threshold=float(policy.get("motif_merge_similarity", 0.93)),
            max_suggestions=int(policy.get("motif_merge_max_suggestions", 20)),
            auto_merge=bool(policy.get("auto_merge_motifs", False)),
            auto_merge_trigger=float(policy.get("auto_merge_entropy_trigger", 0.80)),
        )

    def _native_result(self, attempt: Any) -> SharedProposalMaterialization:
        if not attempt.qualification.eligible or attempt.result is None:
            raise RuntimeError(
                "qualified native proposal storage refused: "
                f"{attempt.qualification.reason_code}"
            )
        # Shared proposal materialization has no private duplicate/reinforce
        # branch.  Treat a contrary result as an invariant breach.
        if attempt.result.reinforced:
            raise RuntimeError("native shared proposal materialization unexpectedly reinforced")
        self._vector_runtime.invalidate("native-shared-proposal-materialized")
        return SharedProposalMaterialization(eid=int(attempt.result.eid), created_new=True)


def native_quorum_operation_key(
    workspace_id: str,
    domain_id: str,
    proposals: tuple[ShareProposal, ...],
) -> str:
    return "|".join((
        "7G5E4D", "PROPOSAL_ORCHESTRATION", "QUORUM", workspace_id, domain_id,
        *(proposal.proposal_id for proposal in proposals),
    ))


def native_operator_operation_key(
    workspace_id: str,
    domain_id: str,
    proposal: ShareProposal,
) -> str:
    return "|".join((
        "7G5E4D", "PROPOSAL_ORCHESTRATION", "OPERATOR", workspace_id, domain_id,
        proposal.proposal_id,
    ))


__all__ = [
    "AuthorizedSharedProposalStorage",
    "LegacyAuthorizedSharedProposalStorage",
    "NativeAuthorizedSharedProposalStorage",
    "SharedProposalMaterialization",
    "native_operator_operation_key",
    "native_quorum_operation_key",
]

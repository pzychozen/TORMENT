"""7G5E4D qualification for authorized share-proposal native storage only."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from torment_service.bridges import BridgeRegistry
from torment_service.collective_models import MemoryGovernanceFlags
from torment_service.conflicts import ConflictRegistry
from torment_service.fabric import TormentFabric
from torment_service.proposals import ProposalRegistry, ShareProposal
from torment_service.provenance_v1 import ProvenanceV1
from torment_service.substrate.compat import NativeMemoryCompatibilityFacade
from torment_service.substrate.errors import SubstrateIdempotencyConflict
from torment_service.substrate.fabric_translation import translate_provenance_v1
from torment_service.substrate.ids import native_id_to_bytes
from torment_service.substrate.motif_runtime_reader import NativeMotifRuntimeReader
from torment_service.substrate.native_memory_runtime_access import NativePostWriteMemoryAccess
from torment_service.substrate.object_revision_governance import (
    NativeMemoryGovernanceFacts,
    NativeObjectRevisionGovernanceService,
)
from torment_service.substrate.shared_proposal_materialization import (
    AuthorizedSharedProposalOperator,
    AuthorizedSharedProposalQuorum,
    NativeAuthorizedSharedProposalMaterializer,
    NativeSharedProposalStorageClock,
)

# This is the established native router fixture.  It prepares a STAGING core
# with LEGACY_ACTIVE deployment metadata and a genuinely claimed shared scope.
from test_substrate_fabric_native_routing import _counts, _prepared


WORKSPACE = "qualified-workspace"
DOMAIN = "research"
PROVIDER = "hash"
MODEL = "hash:3:torment"


@pytest.fixture
def fabric(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("TORMENT_EMBED_PROVIDER", PROVIDER)
    monkeypatch.setenv("TORMENT_HASH_DIM", "3")
    monkeypatch.setenv("TORMENT_COMPRESS_ENABLE", "0")
    monkeypatch.setenv("TORMENT_SRG_ENABLE", "0")
    monkeypatch.setenv("TORMENT_SQLITE_INDEX_ENABLE", "0")
    with TormentFabric(data_dir=str(tmp_path / "legacy")) as instance:
        instance.get_workspace(WORKSPACE, domains=[DOMAIN])
        yield instance


def _embed(second: float = 0.0) -> list[float]:
    vector = np.asarray((1.0, second, 0.0), dtype=np.float32)
    return (vector / np.linalg.norm(vector)).tolist()


def _submit(
    fabric: TormentFabric,
    *,
    agent_id: str,
    summary: str,
    mtype: str = "fact",
    strength: float = 0.8,
    confidence: float = 0.9,
    embedding: list[float] | None = None,
) -> ShareProposal:
    response = fabric.propose_share(
        workspace_id=WORKSPACE,
        agent_id=agent_id,
        summary=summary,
        embedding=embedding or _embed(),
        domain_id=DOMAIN,
        mtype=mtype,
        strength=strength,
        confidence=confidence,
    )
    proposal_id = response["proposal"]["proposal_id"]
    return fabric.get_workspace(WORKSPACE).proposals[DOMAIN].apply_events()[proposal_id]


def _quorum_facts(
    first: ShareProposal,
    second: ShareProposal,
    echo: ShareProposal,
) -> AuthorizedSharedProposalQuorum:
    return AuthorizedSharedProposalQuorum(
        workspace_id=WORKSPACE,
        domain_id=DOMAIN,
        representative=first,
        participating_proposals=(first, second, echo),
        support_agents=("genuine_a", "genuine_b"),
        embedding_provider=PROVIDER,
        embedding_model=MODEL,
    )


def _operator_facts(proposal: ShareProposal) -> AuthorizedSharedProposalOperator:
    return AuthorizedSharedProposalOperator(
        workspace_id=WORKSPACE,
        domain_id=DOMAIN,
        proposal=proposal,
        embedding_provider=PROVIDER,
        embedding_model=MODEL,
    )


def _legacy_payload(fabric: TormentFabric, eid: int) -> dict:
    return fabric.get_workspace(WORKSPACE).shared_graphs[DOMAIN].entities[eid].payload


def _native_payload(connection, scope, eid: int):
    return NativeMemoryCompatibilityFacade(connection).get_memory_by_eid(
        legacy_source_namespace_id=scope.runtime_scope.legacy_source_namespace_id,
        eid=eid,
    )


def _assert_storage_parity(
    *,
    legacy: dict,
    native,
    connection,
    scope,
    expected_provenance: ProvenanceV1,
    expected_embedding: list[float],
) -> None:
    # Compatibility payload preserves the meaningful legacy storage facts.
    for field_name in (
        "summary", "type", "memory_class", "strength", "confidence", "half_life",
        "user_id", "workspace_id", "domain_id", "agent_id", "source", "canon",
        "embedding_provider", "embedding_model", "embedding_dim", "embedding_checksum",
        "support_agents",
    ):
        assert native.payload[field_name] == legacy[field_name]
    assert legacy["scope"] == "shared"
    # Native scope is structural (and therefore intentionally excluded from
    # flexible payload shadows); it resolves to this exact claimed shared lane.
    assert native.semantic_scope_id == scope.runtime_scope.semantic_scope_id
    assert "scope" not in native.payload
    assert native.payload.get("source_proposal_ids") == legacy.get("source_proposal_ids")
    assert native.payload["created_at"] == legacy["created_at"]
    assert native.payload["created_ts"] == legacy["created_ts"]
    assert native.payload["last_reinforced"] == legacy["last_reinforced"]

    # The legacy envelope maps to the existing normalized native structural
    # representation; authority remains non-authorizing for an ordinary memory.
    assert legacy["lifecycle_status"] == {
        "state": "protected",
        "is_authoritative_on_row": True,
        "requires_join": None,
        "set_by": {"actor": "system", "via": "canon_set", "at": legacy["created_ts"]},
        "history_ref": None,
    }
    assert (
        native.lifecycle_state,
        native.lifecycle_authoritative,
        native.governance_state,
        native.authority_category,
    ) == ("PROTECTED", True, "EXPLICIT", "NOT_APPLICABLE")
    governance = NativeObjectRevisionGovernanceService(connection).get_current_object_governance(
        object_id=native.object_id,
    )
    assert governance is not None and governance.facts == NativeMemoryGovernanceFacts()

    translated = translate_provenance_v1(expected_provenance)
    assert connection.execute(
        """SELECT origin_kind,source_channel,source_role,derivation_status,
                  uncertainty_state,source_time_ns,capture_time_ns,memory_role,
                  descriptive_notes
             FROM provenance_records WHERE provenance_id=?""",
        (native_id_to_bytes(native.provenance_id),),
    ).fetchone() == (
        translated.origin_kind,
        translated.source_channel,
        translated.source_role,
        translated.derivation_status,
        translated.uncertainty_state,
        translated.source_time_ns,
        translated.capture_time_ns,
        translated.memory_role,
        translated.descriptive_notes,
    )
    assert len(native.representation_references) == 1
    assert native.representation_references[0].readiness == "READY"
    embedding = NativePostWriteMemoryAccess(
        connection,
        legacy_source_namespace_id=scope.runtime_scope.legacy_source_namespace_id,
        expected_dimension=3,
    ).read_current_embedding(native.eid, expected_dimension=3)
    assert embedding is not None
    assert embedding.payload_bytes == np.asarray(expected_embedding, dtype=np.float32).tobytes()
    motif_reader = NativeMotifRuntimeReader(connection)
    motifs = motif_reader.list_runtime_motifs(
        motif_alias_namespace_id=scope.motif_alias_namespace_id,
        domain_id=DOMAIN,
        semantic_scope_id=scope.runtime_scope.semantic_scope_id,
    )
    assert any(
        native.object_id in {
            member.member_object_id
            for member in motif_reader.list_ordered_current_motif_members(item.motif_object_id)
        }
        for item in motifs
    )


def test_authorized_share_proposal_storage_parity_and_boundaries(
    fabric: TormentFabric,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Freeze every legacy writer clock so proposal provenance timestamps and
    # proposal-created memory timestamps are explicit qualification facts.
    import time

    clock_value = 1_000
    monkeypatch.setattr(time, "time", lambda: clock_value)

    first = _submit(
        fabric, agent_id="genuine_a", summary="Genuine representative fact.",
        strength=0.85, confidence=0.91, embedding=_embed(0.00),
    )
    second = _submit(
        fabric, agent_id="genuine_b", summary="Second genuine supporting fact.",
        strength=0.75, confidence=0.95, embedding=_embed(0.02),
    )
    echo = _submit(
        fabric, agent_id="collective_evidence", summary="Collective echo evidence.",
        mtype="collective_echo", strength=0.99, confidence=0.99, embedding=_embed(0.01),
    )
    legacy_quorum = fabric.process_proposals(
        workspace_id=WORKSPACE, domain_id=DOMAIN, sim_threshold=0.99,
        min_distinct_agents=2, step=41,
    )
    assert legacy_quorum["approved_groups"] == 1
    assert legacy_quorum["approved"] == 3
    legacy_quorum_payload = _legacy_payload(fabric, legacy_quorum["created_shared_eids"][0])
    assert legacy_quorum_payload["summary"] == first.summary
    assert legacy_quorum_payload["support_agents"] == ["genuine_a", "genuine_b"]
    assert legacy_quorum_payload["source_proposal_ids"] == [
        first.proposal_id, second.proposal_id, echo.proposal_id,
    ]

    qualified, connection, capability, _private, scope = _prepared(tmp_path, include_shared=True)
    assert scope is not None
    try:
        materializer = NativeAuthorizedSharedProposalMaterializer(capability)
        quorum_authorization = _quorum_facts(first, second, echo)
        quorum_clock = NativeSharedProposalStorageClock(41, 1_000, 1_000, 1_000)
        quorum_key = "7G5E4D:QUORUM:qualified-workspace:research:authority-group-1"
        quorum_attempt = materializer.materialize_quorum(
            authorization=quorum_authorization,
            native_operation_key=quorum_key,
            clock=quorum_clock,
        )
        assert quorum_attempt.qualification.eligible is True
        assert quorum_attempt.result is not None and quorum_attempt.result.reinforced is False
        native_quorum = _native_payload(connection, scope, quorum_attempt.result.eid)
        _assert_storage_parity(
            legacy=legacy_quorum_payload,
            native=native_quorum,
            connection=connection,
            scope=scope,
            expected_provenance=ProvenanceV1.for_share_proposal_quorum(
                contributing_created_ts=(first.created_ts, second.created_ts, echo.created_ts),
            ),
            expected_embedding=first.embedding,
        )

        # A shared repeat remains a fresh shared creation, never a private R2.
        second_shared = materializer.materialize_quorum(
            authorization=quorum_authorization,
            native_operation_key=quorum_key + ":second-shared-write",
            clock=quorum_clock,
        ).result
        assert second_shared is not None
        assert (second_shared.reinforced, second_shared.eid) == (False, native_quorum.eid + 1)

        clock_value = 2_000
        operator = _submit(
            fabric, agent_id="operator_agent", summary="Operator approved fact.",
            strength=0.84, confidence=0.93, embedding=_embed(0.50),
        )
        legacy_operator = fabric.decide_proposal(
            workspace_id=WORKSPACE, domain_id=DOMAIN, proposal_id=operator.proposal_id,
            decision="approve",
        )
        legacy_operator_payload = _legacy_payload(fabric, legacy_operator["created_shared_eid"])
        assert legacy_operator_payload["source"] == "proposal_manual"
        assert "source_proposal_ids" not in legacy_operator_payload
        operator_clock = NativeSharedProposalStorageClock(2_000, 2_000, 2_000, 2_000)
        operator_key = "7G5E4D:OPERATOR:qualified-workspace:research:operator-approve"
        operator_attempt = materializer.materialize_operator(
            authorization=_operator_facts(operator), native_operation_key=operator_key, clock=operator_clock,
        )
        assert operator_attempt.result is not None and operator_attempt.result.reinforced is False
        native_operator = _native_payload(connection, scope, operator_attempt.result.eid)
        _assert_storage_parity(
            legacy=legacy_operator_payload,
            native=native_operator,
            connection=connection,
            scope=scope,
            expected_provenance=ProvenanceV1.for_share_proposal_operator(
                proposal_created_ts=operator.created_ts,
            ),
            expected_embedding=operator.embedding,
        )

        # Existing authority refuses/rejects before the adapter is ever called.
        reject = _submit(fabric, agent_id="reject_agent", summary="Reject me.", embedding=_embed(.7))
        calls: list[str] = []
        monkeypatch.setattr(materializer, "materialize_operator", lambda **_kwargs: calls.append("called"))
        assert fabric.decide_proposal(
            workspace_id=WORKSPACE, domain_id=DOMAIN, proposal_id=reject.proposal_id, decision="reject",
        )["decision"] == "rejected"
        collective = _submit(
            fabric, agent_id="collective_evidence", summary="Refused collective approval.",
            mtype="collective_echo", embedding=_embed(.8),
        )
        with pytest.raises(ValueError, match="collective-derived proposals require"):
            fabric.decide_proposal(
                workspace_id=WORKSPACE, domain_id=DOMAIN, proposal_id=collective.proposal_id,
                decision="approve",
            )
        assert calls == []
    finally:
        qualified.close()


def test_native_materializer_retry_refusal_conflict_and_external_ownership(
    fabric: TormentFabric,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import time

    monkeypatch.setattr(time, "time", lambda: 3_000)
    first = _submit(fabric, agent_id="genuine_a", summary="Retry quorum representative.", embedding=_embed())
    second = _submit(fabric, agent_id="genuine_b", summary="Retry quorum support.", embedding=_embed(.01))
    echo = _submit(fabric, agent_id="collective_evidence", summary="Retry quorum echo.", mtype="collective_echo", embedding=_embed(.02))
    quorum = _quorum_facts(first, second, echo)
    quorum_clock = NativeSharedProposalStorageClock(73, 3_000, 3_000, 3_000)
    operator = _submit(fabric, agent_id="operator_agent", summary="Retry operator fact.", embedding=_embed(.4))
    operator_clock = NativeSharedProposalStorageClock(74, 3_000, 3_000, 3_000)

    qualified, connection, capability, _private, scope = _prepared(tmp_path, include_shared=True)
    assert scope is not None
    try:
        materializer = NativeAuthorizedSharedProposalMaterializer(capability)
        owners: list[str] = []
        monkeypatch.setattr(ProposalRegistry, "mark", lambda *_args, **_kwargs: owners.append("proposal"))
        monkeypatch.setattr(BridgeRegistry, "suggest", lambda *_args, **_kwargs: owners.append("bridge"))
        monkeypatch.setattr(ConflictRegistry, "add", lambda *_args, **_kwargs: owners.append("conflict"))
        monkeypatch.setattr(TormentFabric, "_maybe_suggest_domain", lambda *_args, **_kwargs: owners.append("domain"))

        quorum_key = "7G5E4D:QUORUM:qualified-workspace:research:retry"
        before = _counts(connection)
        with pytest.raises(RuntimeError, match="committed native new-memory source"):
            materializer.materialize_quorum(
                authorization=quorum, native_operation_key=quorum_key, clock=quorum_clock,
                _test_stop_after="source",
            )
        after_source = _counts(connection)
        quorum_retry = materializer.materialize_quorum(
            authorization=quorum, native_operation_key=quorum_key, clock=quorum_clock,
        ).result
        assert quorum_retry is not None and quorum_retry.reinforced is False
        assert _counts(connection)[0] == after_source[0] == before[0] + 2  # memory + created motif
        assert _counts(connection)[2] == after_source[2] == before[2] + 1  # one membership
        assert _counts(connection)[4] == after_source[4] + 1  # E1 only on retry

        operator_key = "7G5E4D:OPERATOR:qualified-workspace:research:retry"
        before_operator = _counts(connection)
        with pytest.raises(RuntimeError, match="committed native new-memory source"):
            materializer.materialize_operator(
                authorization=_operator_facts(operator), native_operation_key=operator_key,
                clock=operator_clock, _test_stop_after="source",
            )
        after_operator_source = _counts(connection)
        operator_retry = materializer.materialize_operator(
            authorization=_operator_facts(operator), native_operation_key=operator_key,
            clock=operator_clock,
        ).result
        assert operator_retry is not None and operator_retry.reinforced is False
        assert _counts(connection)[0] == after_operator_source[0] == before_operator[0] + 1
        assert _counts(connection)[2] == after_operator_source[2] == before_operator[2] + 1
        assert _counts(connection)[4] == after_operator_source[4] + 1
        assert owners == []

        # A changed source input under a completed key must fail closed.
        with pytest.raises(SubstrateIdempotencyConflict):
            materializer.materialize_quorum(
                authorization=replace(quorum, representative=replace(first, summary="changed summary")),
                native_operation_key=quorum_key, clock=quorum_clock,
            )
        with pytest.raises(SubstrateIdempotencyConflict):
            changed_member = replace(second, proposal_id="changed-member", created_ts=3_001)
            materializer.materialize_quorum(
                authorization=replace(quorum, participating_proposals=(first, changed_member, echo)),
                native_operation_key=quorum_key, clock=quorum_clock,
            )
        with pytest.raises(SubstrateIdempotencyConflict):
            changed_embedding = replace(first, embedding=_embed(.9))
            materializer.materialize_quorum(
                authorization=replace(quorum, representative=changed_embedding),
                native_operation_key=quorum_key, clock=quorum_clock,
            )
        assert _counts(connection)[0] == before_operator[0] + 1

        # An unclaimed shared domain is a router refusal before every native effect.
        wrong = replace(first, domain_id="creative")
        wrong_authorization = AuthorizedSharedProposalQuorum(
            workspace_id=WORKSPACE, domain_id="creative", representative=wrong,
            participating_proposals=(wrong, replace(second, domain_id="creative"), replace(echo, domain_id="creative")),
            support_agents=("genuine_a", "genuine_b"), embedding_provider=PROVIDER, embedding_model=MODEL,
        )
        wrong_before = _counts(connection)
        wrong_attempt = materializer.materialize_quorum(
            authorization=wrong_authorization,
            native_operation_key="7G5E4D:QUORUM:qualified-workspace:creative:wrong-domain",
            clock=quorum_clock,
        )
        assert (wrong_attempt.qualification.eligible, wrong_attempt.qualification.reason_code, wrong_attempt.result) == (
            False, "SCOPE_NOT_CLAIMED", None,
        )
        assert _counts(connection) == wrong_before
    finally:
        qualified.close()

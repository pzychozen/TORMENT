"""Synthetic Phase 9B qualification for metadata-less private per-EID sources."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

import numpy as np
import pytest

from torment_service.substrate.errors import SubstrateIdempotencyConflict
from torment_service.substrate.ids import generate_native_id
from torment_service.substrate.migration.existing_workspace_multi_scope_admission import (
    ExistingWorkspaceNativeMultiScopeAdmissionRequest,
)
from torment_service.substrate.migration.explicit_source_evidence import (
    EvidenceAbsenceReason,
    EvidenceOwnerBoundary,
    EvidenceOwnerBoundaryKind,
    EvidencePresenceExpectation,
    EvidenceSemanticRole,
    ExplicitSourceEvidence,
    ExplicitSourceEvidenceDrift,
    ExplicitSourceEvidenceError,
    SourceOwnerClass,
    capture_present_source_evidence,
)
from torment_service.substrate.migration.metadata_less_per_eid_legacy_source import (
    DIMENSION_DOES_NOT_ESTABLISH_REPRESENTATION_IDENTITY,
    MetadataLessPerEidLegacySourceRefused,
    MetadataLessPerEidQualificationIntent,
    MetadataLessRepresentationIdentity,
    UNKNOWN_LEGACY_VECTOR_CAN_BECOME_TARGET_BY_RELABEL,
    UNKNOWN_MODEL_REMAINS_UNKNOWN,
    UNKNOWN_PROVIDER_REMAINS_UNKNOWN,
    qualify_metadata_less_per_eid_legacy_source,
    require_metadata_less_qualification_retry_compatibility,
)
from torment_service.substrate.migration.root_scope import RootScopeKey, RootScopeKind
from torment_service.substrate.migration.runtime_reembedding_bootstrap import (
    NativeMigrationRuntimeReembeddingBootstrapService,
)
from torment_service.substrate.migration.runtime_readiness import LegacyVectorStrategy


def _write(root: Path, relative: str, payload: bytes) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return path


def _capture(
    root: Path,
    *,
    workspace_id: str,
    agent_id: str,
    eid: int,
    representation_locator: str | None = None,
) -> tuple[RootScopeKey, ExplicitSourceEvidence, ExplicitSourceEvidence, ExplicitSourceEvidence]:
    scope = RootScopeKey(workspace_id, RootScopeKind.PRIVATE, agent_id=agent_id)
    boundary = EvidenceOwnerBoundary(
        workspace_id, EvidenceOwnerBoundaryKind.PRIVATE_SCOPE, agent_id=agent_id
    )
    nodes = capture_present_source_evidence(
        data_root=root,
        owner_class=SourceOwnerClass.PRIVATE_GRAPH_SOURCE,
        owner_boundary=boundary,
        canonical_locator="nodes.jsonl",
        semantic_role=EvidenceSemanticRole.NODES,
        scope_key=scope,
    )
    edges = ExplicitSourceEvidence(
        owner_class=SourceOwnerClass.PRIVATE_GRAPH_SOURCE,
        owner_boundary=boundary,
        canonical_locator="edges.jsonl",
        semantic_role=EvidenceSemanticRole.EDGES,
        presence_expectation=EvidencePresenceExpectation.EXPECTED_ABSENT,
        scope_key=scope,
        absence_reason=EvidenceAbsenceReason.OPTIONAL_EDGE_SOURCE,
    )
    representation = capture_present_source_evidence(
        data_root=root,
        owner_class=SourceOwnerClass.METADATA_LESS_PER_EID_LEGACY_REPRESENTATION,
        owner_boundary=boundary,
        canonical_locator=representation_locator or f"emb_{eid}.npy",
        semantic_role=EvidenceSemanticRole.LEGACY_REPRESENTATION,
        scope_key=scope,
    )
    return scope, nodes, edges, representation


def _fixture(
    tmp_path: Path,
    *,
    workspace_id: str = "synthetic-alpha",
    agent_id: str = "aria",
    eid: int = 7,
    payload: dict[str, object] | None = None,
    dimension: int = 3,
) -> tuple[Path, RootScopeKey, ExplicitSourceEvidence, ExplicitSourceEvidence, ExplicitSourceEvidence]:
    root = tmp_path / "root"
    private = root / "workspaces" / workspace_id / "agents" / agent_id / "private"
    private.mkdir(parents=True)
    node = {"eid": eid, "payload": payload or {"summary": "canonical summary", "text": "other text"}}
    _write(root, f"workspaces/{workspace_id}/agents/{agent_id}/private/nodes.jsonl", json.dumps(node).encode("utf-8") + b"\n")
    np.save(private / f"emb_{eid}.npy", np.arange(dimension, dtype=np.float32))
    return (root, *_capture(root, workspace_id=workspace_id, agent_id=agent_id, eid=eid))


def _qualify(
    root: Path,
    scope: RootScopeKey,
    nodes: ExplicitSourceEvidence,
    edges: ExplicitSourceEvidence,
    representation: ExplicitSourceEvidence,
    *,
    eid: int = 7,
    legacy_source_namespace_id=None,
    target_identity_namespace_id=None,
):
    return qualify_metadata_less_per_eid_legacy_source(
        data_root=root,
        scope_key=scope,
        legacy_eid=eid,
        legacy_source_namespace_id=legacy_source_namespace_id or generate_native_id(),
        target_identity_namespace_id=target_identity_namespace_id or generate_native_id(),
        nodes_source=nodes,
        optional_edges_source=edges,
        legacy_representation_source=representation,
    )


def test_recognized_per_eid_source_retains_unknown_identity_and_canonical_text(tmp_path: Path) -> None:
    root, scope, nodes, edges, representation = _fixture(tmp_path)
    source = _qualify(root, scope, nodes, edges, representation)

    assert source.legacy_representation_source.canonical_locator == "emb_7.npy"
    assert source.canonical_graph_source_identity != source.legacy_representation_evidence_identity
    assert source.provider_identity is None
    assert source.model_identity is None
    assert source.representation_identity is MetadataLessRepresentationIdentity.UNKNOWN
    assert source.legacy_vector_strategy is LegacyVectorStrategy.REEMBED_REQUIRED
    assert source.canonical_embedding_input.field == "summary"
    assert source.canonical_embedding_input.text == "canonical summary"
    assert source.retained_legacy_vector.array_dtype == "float32"
    assert source.retained_legacy_vector.array_shape == (3,)
    assert source.retained_legacy_vector.dimension == 3
    assert UNKNOWN_PROVIDER_REMAINS_UNKNOWN is True
    assert UNKNOWN_MODEL_REMAINS_UNKNOWN is True
    assert DIMENSION_DOES_NOT_ESTABLISH_REPRESENTATION_IDENTITY is True
    assert UNKNOWN_LEGACY_VECTOR_CAN_BECOME_TARGET_BY_RELABEL is False


def test_per_eid_filename_and_owner_boundary_refuse_unqualified_forms(tmp_path: Path) -> None:
    root, scope, nodes, edges, _representation = _fixture(tmp_path)
    private = root / "workspaces/synthetic-alpha/agents/aria/private"
    for locator in ("emb_foo.npy", "emb_7.exe", "nested/emb_7.npy"):
        path = private / locator
        path.parent.mkdir(parents=True, exist_ok=True)
        np.save(path, np.arange(3, dtype=np.float32)) if path.suffix == ".npy" else path.write_bytes(b"not-npy")
        _scope, _nodes, _edges, representation = _capture(
            root, workspace_id="synthetic-alpha", agent_id="aria", eid=7, representation_locator=locator
        )
        with pytest.raises(MetadataLessPerEidLegacySourceRefused, match="qualified form"):
            _qualify(root, scope, nodes, edges, representation)

    with pytest.raises(ExplicitSourceEvidenceError, match="locator"):
        capture_present_source_evidence(
            data_root=root,
            owner_class=SourceOwnerClass.METADATA_LESS_PER_EID_LEGACY_REPRESENTATION,
            owner_boundary=EvidenceOwnerBoundary("synthetic-alpha", EvidenceOwnerBoundaryKind.PRIVATE_SCOPE, agent_id="aria"),
            canonical_locator="../emb_7.npy",
            semantic_role=EvidenceSemanticRole.LEGACY_REPRESENTATION,
            scope_key=scope,
        )
    with pytest.raises(ExplicitSourceEvidenceError, match="owner boundary"):
        ExplicitSourceEvidence(
            owner_class=SourceOwnerClass.METADATA_LESS_PER_EID_LEGACY_REPRESENTATION,
            owner_boundary=EvidenceOwnerBoundary("synthetic-alpha", EvidenceOwnerBoundaryKind.SHARED_SCOPE, domain_id="research"),
            canonical_locator="emb_7.npy",
            semantic_role=EvidenceSemanticRole.LEGACY_REPRESENTATION,
            presence_expectation=EvidencePresenceExpectation.EXPECTED_PRESENT,
            scope_key=RootScopeKey("synthetic-alpha", RootScopeKind.SHARED, domain_id="research"),
            byte_length=1,
            sha256_hex="0" * 64,
        )


def test_filename_eid_mismatch_and_generic_legacy_owner_are_refused(tmp_path: Path) -> None:
    root, scope, nodes, edges, representation = _fixture(tmp_path)
    with pytest.raises(MetadataLessPerEidLegacySourceRefused, match="qualified form"):
        _qualify(root, scope, nodes, edges, representation, eid=8)

    generic_owner = replace(
        representation, owner_class=SourceOwnerClass.LEGACY_REPRESENTATION_ARTIFACT
    )
    with pytest.raises(MetadataLessPerEidLegacySourceRefused, match="unqualified owner"):
        _qualify(root, scope, nodes, edges, generic_owner)


def test_same_dimension_does_not_promote_bytes_and_b3b_seam_has_only_canonical_text(tmp_path: Path) -> None:
    root, scope, nodes, edges, representation = _fixture(tmp_path, dimension=384)
    source = _qualify(root, scope, nodes, edges, representation)
    b3b_input = source.b3b_input

    assert source.retained_legacy_vector.dimension == 384
    assert b3b_input.legacy_vector_strategy is LegacyVectorStrategy.REEMBED_REQUIRED
    assert b3b_input.canonical_embedding_input.text == "canonical summary"
    assert not hasattr(b3b_input, "legacy_vector_bytes")
    assert callable(NativeMigrationRuntimeReembeddingBootstrapService.bootstrap_from_qualified_text)


def test_source_eid_requires_one_well_formed_canonical_node_mapping(tmp_path: Path) -> None:
    root, scope, nodes, edges, representation = _fixture(tmp_path)
    node_path = root / "workspaces/synthetic-alpha/agents/aria/private/nodes.jsonl"

    node_path.write_text(
        '{"eid":7,"payload":{"summary":"one"}}\n{"eid":7,"payload":{"summary":"two"}}\n',
        encoding="utf-8",
    )
    _scope, nodes, edges, representation = _capture(root, workspace_id="synthetic-alpha", agent_id="aria", eid=7)
    with pytest.raises(MetadataLessPerEidLegacySourceRefused, match="not unique"):
        _qualify(root, scope, nodes, edges, representation)

    node_path.write_text('{"eid":8,"payload":{"summary":"other"}}\n', encoding="utf-8")
    _scope, nodes, edges, representation = _capture(root, workspace_id="synthetic-alpha", agent_id="aria", eid=7)
    with pytest.raises(MetadataLessPerEidLegacySourceRefused, match="absent"):
        _qualify(root, scope, nodes, edges, representation)

    node_path.write_text('{"eid":7,"payload":{"other":"missing"}}\n', encoding="utf-8")
    _scope, nodes, edges, representation = _capture(root, workspace_id="synthetic-alpha", agent_id="aria", eid=7)
    with pytest.raises(MetadataLessPerEidLegacySourceRefused, match="canonical embedding input"):
        _qualify(root, scope, nodes, edges, representation)

    node_path.write_text('{"eid":7,"payload":\n', encoding="utf-8")
    _scope, nodes, edges, representation = _capture(root, workspace_id="synthetic-alpha", agent_id="aria", eid=7)
    with pytest.raises(MetadataLessPerEidLegacySourceRefused, match="malformed"):
        _qualify(root, scope, nodes, edges, representation)


def test_recheck_refuses_nodes_or_vector_drift_and_vector_deletion(tmp_path: Path) -> None:
    root, scope, nodes, edges, representation = _fixture(tmp_path)
    source = _qualify(root, scope, nodes, edges, representation)
    assert source.recheck(data_root=root) == source

    node_path = root / "workspaces/synthetic-alpha/agents/aria/private/nodes.jsonl"
    node_path.write_text('{"eid":7,"payload":{"summary":"changed"}}\n', encoding="utf-8")
    with pytest.raises(ExplicitSourceEvidenceDrift, match="declared evidence drifted"):
        source.recheck(data_root=root)

    root, scope, nodes, edges, representation = _fixture(tmp_path / "vector-drift")
    source = _qualify(root, scope, nodes, edges, representation)
    vector_path = root / "workspaces/synthetic-alpha/agents/aria/private/emb_7.npy"
    np.save(vector_path, np.array([9, 8, 7], dtype=np.float32))
    with pytest.raises(ExplicitSourceEvidenceDrift, match="declared evidence drifted"):
        source.recheck(data_root=root)
    vector_path.unlink()
    with pytest.raises(ExplicitSourceEvidenceDrift, match="required evidence is missing"):
        source.recheck(data_root=root)


def test_unexpected_different_per_eid_file_never_substitutes_for_declared_evidence(tmp_path: Path) -> None:
    root, scope, nodes, edges, representation = _fixture(tmp_path)
    source = _qualify(root, scope, nodes, edges, representation)
    np.save(root / "workspaces/synthetic-alpha/agents/aria/private/emb_8.npy", np.arange(3, dtype=np.float32))

    assert source.recheck(data_root=root) == source
    assert source.retained_legacy_vector.canonical_locator == "emb_7.npy"


def test_namespace_scope_and_retry_identity_remain_isolated_and_conflict_on_semantic_change(tmp_path: Path) -> None:
    left = _fixture(tmp_path / "left", workspace_id="workspace-a", agent_id="aria")
    right = _fixture(tmp_path / "right", workspace_id="workspace-b", agent_id="aria")
    left_source = _qualify(*left)
    right_source = _qualify(*right)

    assert left_source.legacy_eid == right_source.legacy_eid == 7
    assert left_source.scope_key != right_source.scope_key
    assert left_source.source_evidence_identity != right_source.source_evidence_identity

    retry = _qualify(
        *left,
        legacy_source_namespace_id=left_source.legacy_source_namespace_id,
        target_identity_namespace_id=left_source.target_identity_namespace_id,
    )
    assert retry.source_evidence_identity == left_source.source_evidence_identity
    namespace = generate_native_id()
    initial = MetadataLessPerEidQualificationIntent(namespace, "metadata-less-eid-7", left_source)
    same = MetadataLessPerEidQualificationIntent(namespace, "metadata-less-eid-7", retry)
    require_metadata_less_qualification_retry_compatibility(initial, same)

    node_path = left[0] / "workspaces/workspace-a/agents/aria/private/nodes.jsonl"
    node_path.write_text('{"eid":7,"payload":{"summary":"semantic change"}}\n', encoding="utf-8")
    root, scope, nodes, edges, representation = _fixture(tmp_path / "changed", workspace_id="workspace-a", agent_id="aria")
    changed_path = root / "workspaces/workspace-a/agents/aria/private/nodes.jsonl"
    changed_path.write_text(node_path.read_text(encoding="utf-8"), encoding="utf-8")
    _scope, nodes, edges, representation = _capture(root, workspace_id="workspace-a", agent_id="aria", eid=7)
    changed = _qualify(
        root,
        scope,
        nodes,
        edges,
        representation,
        legacy_source_namespace_id=left_source.legacy_source_namespace_id,
        target_identity_namespace_id=left_source.target_identity_namespace_id,
    )
    conflicting = MetadataLessPerEidQualificationIntent(namespace, "metadata-less-eid-7", changed)
    with pytest.raises(SubstrateIdempotencyConflict, match="intent differs"):
        require_metadata_less_qualification_retry_compatibility(initial, conflicting)


def test_first_profile_request_and_existing_b3b_strategy_semantics_remain_unchanged() -> None:
    assert "lane_plans" in ExistingWorkspaceNativeMultiScopeAdmissionRequest.__dataclass_fields__
    assert LegacyVectorStrategy.BYTE_DERIVATION_POSSIBLE.value == "BYTE_DERIVATION_POSSIBLE"
    assert LegacyVectorStrategy.REEMBED_REQUIRED.value == "REEMBED_REQUIRED"

"""Phase 9A synthetic qualification for root-wide admission evidence only."""

from __future__ import annotations

from dataclasses import replace
import hashlib
from pathlib import Path

import pytest

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
    RootEvidenceManifest,
    SourceOwnerClass,
    capture_present_source_evidence,
    load_explicit_source_manifest,
    write_explicit_source_manifest,
)
from torment_service.substrate.migration.root_admission_description import (
    CENSUS_AND_MANIFEST_REQUIRE_WRITER_FREEZE,
    DeclaredUnmaterializedDomain,
    ExpectedRootCensus,
    ExternalOwnerObservation,
    ExternalOwnerObservationKind,
    IdentityOnlyAgentObservation,
    MaterializedRootScopePlan,
    MaterializedScopePosture,
    RepresentationDispositionCount,
    RootAdmissionDescriptionError,
    RootFeaturePosture,
    RootNativeProductionAdmissionDescription,
    RootRepresentationDisposition,
    SEMANTIC_ADAPTER_OWNERSHIP_DOES_NOT_EQUAL_DURABLE_STORE_OWNERSHIP,
    WorkspaceRootAdmissionPlan,
    WorkspaceTopologyCounts,
    representation_identity_matches_target,
)
from torment_service.substrate.migration.root_scope import RootScopeKey, RootScopeKeyError, RootScopeKind
from torment_service.substrate.runtime_binding import NativeRepresentationLane


def _lane(*, provider: str = "st", model: str = "BAAI/bge-small-en-v1.5") -> NativeRepresentationLane:
    return NativeRepresentationLane(
        provider=provider,
        model=model,
        dimension=384,
        representation_class="COMPAT_EMBEDDING",
        generation=1,
        derivation_contract_version="compat-embedding-v1",
        encoding_id="RAW_VECTOR",
        dtype="float32",
    )


def _write(root: Path, relative: str, payload: bytes) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def _present(
    root: Path,
    owner_class: SourceOwnerClass,
    owner: EvidenceOwnerBoundary,
    locator: str,
    role: EvidenceSemanticRole,
    scope: RootScopeKey | None = None,
) -> ExplicitSourceEvidence:
    return capture_present_source_evidence(
        data_root=root,
        owner_class=owner_class,
        owner_boundary=owner,
        canonical_locator=locator,
        semantic_role=role,
        scope_key=scope,
    )


def _fixture_description(tmp_path: Path) -> tuple[RootNativeProductionAdmissionDescription, Path, RootEvidenceManifest]:
    root = tmp_path / "synthetic-root"
    root.mkdir(parents=True)
    for workspace in ("ws-empty", "ws-many", "ws-one"):
        _write(root, f"workspaces/{workspace}/workspace_meta.json", b"{}")
    _write(root, "workspaces/ws-one/domains.json", b"{}")
    _write(root, "workspaces/ws-one/domain_policies.json", b"{}")
    _write(root, "workspaces/ws-one/bridges.json", b"{}")
    _write(root, "workspaces/ws-one/agents/aria/private/nodes.jsonl", b"private-a")
    _write(root, "workspaces/ws-one/agents/aria/private/embeddings/manifest.json", b"manifest-a")
    _write(root, "workspaces/ws-one/agents/aria/private/emb_1.npy", b"legacy-a")
    _write(root, "workspaces/ws-one/agents/aria/character_state.json", b"character-a")
    (root / "workspaces/ws-one/domains/research/shared").mkdir(parents=True)
    _write(root, "workspaces/ws-one/domains/research/motifs.json", b"motif-research")
    _write(root, "workspaces/ws-many/agents/bert/private/nodes.jsonl", b"private-b")
    _write(root, "workspaces/ws-many/agents/charlie/private/nodes.jsonl", b"private-c")
    _write(root, "workspaces/ws-many/domains/creative/shared/nodes.jsonl", b"shared-creative")
    _write(root, "workspaces/ws-many/domains/engineering/shared/nodes.jsonl", b"shared-engineering")

    aria = RootScopeKey("ws-one", RootScopeKind.PRIVATE, agent_id="aria")
    research = RootScopeKey("ws-one", RootScopeKind.SHARED, domain_id="research")
    bert = RootScopeKey("ws-many", RootScopeKind.PRIVATE, agent_id="bert")
    charlie = RootScopeKey("ws-many", RootScopeKind.PRIVATE, agent_id="charlie")
    creative = RootScopeKey("ws-many", RootScopeKind.SHARED, domain_id="creative")
    engineering = RootScopeKey("ws-many", RootScopeKind.SHARED, domain_id="engineering")

    ws_one = EvidenceOwnerBoundary("ws-one", EvidenceOwnerBoundaryKind.WORKSPACE)
    aria_private = EvidenceOwnerBoundary("ws-one", EvidenceOwnerBoundaryKind.PRIVATE_SCOPE, agent_id="aria")
    aria_agent = EvidenceOwnerBoundary("ws-one", EvidenceOwnerBoundaryKind.AGENT, agent_id="aria")
    research_shared = EvidenceOwnerBoundary("ws-one", EvidenceOwnerBoundaryKind.SHARED_SCOPE, domain_id="research")
    research_domain = EvidenceOwnerBoundary("ws-one", EvidenceOwnerBoundaryKind.DOMAIN, domain_id="research")
    future_shared = EvidenceOwnerBoundary("ws-empty", EvidenceOwnerBoundaryKind.SHARED_SCOPE, domain_id="future")
    bert_private = EvidenceOwnerBoundary("ws-many", EvidenceOwnerBoundaryKind.PRIVATE_SCOPE, agent_id="bert")
    charlie_private = EvidenceOwnerBoundary("ws-many", EvidenceOwnerBoundaryKind.PRIVATE_SCOPE, agent_id="charlie")
    creative_shared = EvidenceOwnerBoundary("ws-many", EvidenceOwnerBoundaryKind.SHARED_SCOPE, domain_id="creative")
    engineering_shared = EvidenceOwnerBoundary("ws-many", EvidenceOwnerBoundaryKind.SHARED_SCOPE, domain_id="engineering")

    entries = [
        _present(root, SourceOwnerClass.WORKSPACE_IDENTITY_METADATA, EvidenceOwnerBoundary("ws-empty", EvidenceOwnerBoundaryKind.WORKSPACE), "workspace_meta.json", EvidenceSemanticRole.WORKSPACE_META),
        _present(root, SourceOwnerClass.WORKSPACE_IDENTITY_METADATA, EvidenceOwnerBoundary("ws-many", EvidenceOwnerBoundaryKind.WORKSPACE), "workspace_meta.json", EvidenceSemanticRole.WORKSPACE_META),
        _present(root, SourceOwnerClass.WORKSPACE_IDENTITY_METADATA, ws_one, "workspace_meta.json", EvidenceSemanticRole.WORKSPACE_META),
        _present(root, SourceOwnerClass.DOMAIN_DECLARATION, ws_one, "domains.json", EvidenceSemanticRole.DOMAINS),
        _present(root, SourceOwnerClass.DOMAIN_POLICY, ws_one, "domain_policies.json", EvidenceSemanticRole.DOMAIN_POLICY),
        _present(root, SourceOwnerClass.BRIDGE_OWNER_EVIDENCE, ws_one, "bridges.json", EvidenceSemanticRole.BRIDGES),
        _present(root, SourceOwnerClass.PRIVATE_GRAPH_SOURCE, aria_private, "nodes.jsonl", EvidenceSemanticRole.NODES, aria),
        _present(root, SourceOwnerClass.EMBEDDING_MANIFEST, aria_private, "embeddings/manifest.json", EvidenceSemanticRole.EMBEDDING_MANIFEST, aria),
        _present(root, SourceOwnerClass.LEGACY_REPRESENTATION_ARTIFACT, aria_private, "emb_1.npy", EvidenceSemanticRole.LEGACY_REPRESENTATION, aria),
        _present(root, SourceOwnerClass.EXTERNAL_OWNER_OBSERVATION, aria_agent, "character_state.json", EvidenceSemanticRole.EXTERNAL_OBSERVATION, aria),
        ExplicitSourceEvidence(
            SourceOwnerClass.PRIVATE_GRAPH_SOURCE, aria_private, "edges.jsonl", EvidenceSemanticRole.EDGES,
            EvidencePresenceExpectation.EXPECTED_ABSENT, aria, absence_reason=EvidenceAbsenceReason.OPTIONAL_EDGE_SOURCE,
        ),
        ExplicitSourceEvidence(
            SourceOwnerClass.SHARED_GRAPH_SOURCE, research_shared, "nodes.jsonl", EvidenceSemanticRole.NODES,
            EvidencePresenceExpectation.EXPECTED_ABSENT, research, absence_reason=EvidenceAbsenceReason.EMPTY_GRAPH,
        ),
        ExplicitSourceEvidence(
            SourceOwnerClass.SHARED_GRAPH_SOURCE, future_shared, "nodes.jsonl", EvidenceSemanticRole.NODES,
            EvidencePresenceExpectation.EXPECTED_ABSENT,
            RootScopeKey("ws-empty", RootScopeKind.SHARED, domain_id="future"),
            absence_reason=EvidenceAbsenceReason.UNMATERIALIZED_DECLARATION,
        ),
        _present(root, SourceOwnerClass.MOTIF_SOURCE, research_domain, "motifs.json", EvidenceSemanticRole.MOTIFS, research),
        _present(root, SourceOwnerClass.PRIVATE_GRAPH_SOURCE, bert_private, "nodes.jsonl", EvidenceSemanticRole.NODES, bert),
        _present(root, SourceOwnerClass.PRIVATE_GRAPH_SOURCE, charlie_private, "nodes.jsonl", EvidenceSemanticRole.NODES, charlie),
        _present(root, SourceOwnerClass.SHARED_GRAPH_SOURCE, creative_shared, "nodes.jsonl", EvidenceSemanticRole.NODES, creative),
        _present(root, SourceOwnerClass.SHARED_GRAPH_SOURCE, engineering_shared, "nodes.jsonl", EvidenceSemanticRole.NODES, engineering),
    ]
    manifest = RootEvidenceManifest(tuple(reversed(entries)))
    plans = (
        WorkspaceRootAdmissionPlan(
            workspace_id="ws-empty",
            identity_only_agents=(IdentityOnlyAgentObservation("ghost", "identity-only-ghost"),),
            declared_unmaterialized_domains=(DeclaredUnmaterializedDomain("future", "declared-domain-future"),),
            no_memory_scope=True,
        ),
        WorkspaceRootAdmissionPlan(
            workspace_id="ws-many",
            private_materialized_scopes=(
                MaterializedRootScopePlan(bert, RootRepresentationDisposition.REEMBED_REQUIRED),
                MaterializedRootScopePlan(charlie, RootRepresentationDisposition.UNKNOWN_IDENTITY),
            ),
            shared_materialized_scopes=(
                MaterializedRootScopePlan(creative, RootRepresentationDisposition.NO_VECTOR),
                MaterializedRootScopePlan(engineering, RootRepresentationDisposition.UNUSABLE_VECTOR),
            ),
        ),
        WorkspaceRootAdmissionPlan(
            workspace_id="ws-one",
            private_materialized_scopes=(MaterializedRootScopePlan(aria, RootRepresentationDisposition.TARGET_COMPATIBLE),),
            shared_materialized_scopes=(
                MaterializedRootScopePlan(
                    research,
                    RootRepresentationDisposition.TARGET_COMPATIBLE,
                    MaterializedScopePosture.EMPTY_SHARED_WITH_MOTIF,
                ),
            ),
        ),
    )
    census = ExpectedRootCensus(
        workspace_count=3,
        materialized_private_scope_count=3,
        materialized_shared_scope_count=3,
        total_materialized_scope_count=6,
        representation_disposition_counts=tuple(
            RepresentationDispositionCount(disposition, 2 if disposition is RootRepresentationDisposition.TARGET_COMPATIBLE else 1)
            for disposition in RootRepresentationDisposition
        ),
        workspace_topology_counts=WorkspaceTopologyCounts(1, 1, 1, 1, 1, 1),
    )
    description = RootNativeProductionAdmissionDescription(
        data_root_identity="pytest-synthetic-root",
        operator_identity="pytest-operator",
        workspace_plans=plans,
        target_representation_lane=_lane(),
        expected_census=census,
        explicit_source_manifest=manifest,
        external_owner_observations=(
            ExternalOwnerObservation(
                "ws-one", ExternalOwnerObservationKind.CHARACTER, "character-observation",
                hashlib.sha256(b"synthetic-character-observation").hexdigest(), aria,
            ),
        ),
        feature_posture=RootFeaturePosture("compression-deep-disabled", False, False),
    )
    return description, root, manifest


def test_root_description_represents_multi_workspace_and_all_frozen_scope_shapes(tmp_path: Path) -> None:
    description, _root, _manifest = _fixture_description(tmp_path)

    assert [plan.workspace_id for plan in description.workspace_plans] == ["ws-empty", "ws-many", "ws-one"]
    assert description.workspace_plans[0].no_memory_scope is True
    assert description.workspace_plans[0].identity_only_agents[0].agent_id == "ghost"
    assert description.workspace_plans[0].declared_unmaterialized_domains[0].domain_id == "future"
    assert len(description.workspace_plans[1].private_materialized_scopes) == 2
    assert len(description.workspace_plans[1].shared_materialized_scopes) == 2
    assert description.workspace_plans[2].shared_materialized_scopes[0].materialization_posture is MaterializedScopePosture.EMPTY_SHARED_WITH_MOTIF
    assert description.is_activation_evidence is False
    assert CENSUS_AND_MANIFEST_REQUIRE_WRITER_FREEZE is True
    assert SEMANTIC_ADAPTER_OWNERSHIP_DOES_NOT_EQUAL_DURABLE_STORE_OWNERSHIP is True


def test_empty_scope_postures_require_explicit_identity_and_domain_declaration() -> None:
    private = RootScopeKey("ws-empty", RootScopeKind.PRIVATE, agent_id="aria")
    shared = RootScopeKey("ws-empty", RootScopeKind.SHARED, domain_id="research")
    empty_private = MaterializedRootScopePlan(
        private, RootRepresentationDisposition.NO_VECTOR, MaterializedScopePosture.EMPTY_PRIVATE,
    )
    declared_shared = MaterializedRootScopePlan(
        shared, RootRepresentationDisposition.NO_VECTOR, MaterializedScopePosture.DECLARED_EMPTY_SHARED,
    )
    physical_no_motif_shared = MaterializedRootScopePlan(
        shared, RootRepresentationDisposition.NO_VECTOR, MaterializedScopePosture.EMPTY_SHARED_WITHOUT_MOTIF,
    )

    with pytest.raises(RootAdmissionDescriptionError, match="identity-only"):
        WorkspaceRootAdmissionPlan("ws-empty", private_materialized_scopes=(empty_private,))
    with pytest.raises(RootAdmissionDescriptionError, match="domain declaration"):
        WorkspaceRootAdmissionPlan("ws-empty", shared_materialized_scopes=(declared_shared,), no_memory_scope=True)
    with pytest.raises(RootAdmissionDescriptionError, match="NO_VECTOR"):
        MaterializedRootScopePlan(
            private, RootRepresentationDisposition.TARGET_COMPATIBLE, MaterializedScopePosture.EMPTY_PRIVATE,
        )
    with pytest.raises(RootAdmissionDescriptionError, match="SHARED"):
        MaterializedRootScopePlan(
            private, RootRepresentationDisposition.NO_VECTOR, MaterializedScopePosture.EMPTY_SHARED_WITHOUT_MOTIF,
        )
    with pytest.raises(RootAdmissionDescriptionError, match="NO_VECTOR"):
        MaterializedRootScopePlan(
            shared, RootRepresentationDisposition.TARGET_COMPATIBLE,
            MaterializedScopePosture.EMPTY_SHARED_WITHOUT_MOTIF,
        )
    with pytest.raises(RootAdmissionDescriptionError, match="NO_VECTOR"):
        MaterializedRootScopePlan(
            shared, RootRepresentationDisposition.REEMBED_REQUIRED,
            MaterializedScopePosture.EMPTY_SHARED_WITHOUT_MOTIF,
        )
    with pytest.raises(RootAdmissionDescriptionError, match="TARGET_COMPATIBLE"):
        MaterializedRootScopePlan(
            shared, RootRepresentationDisposition.NO_VECTOR, MaterializedScopePosture.EMPTY_SHARED_WITH_MOTIF,
        )

    plan = WorkspaceRootAdmissionPlan(
        "ws-empty",
        private_materialized_scopes=(empty_private,),
        shared_materialized_scopes=(declared_shared,),
        identity_only_agents=(IdentityOnlyAgentObservation("aria", "lawful-identity"),),
        declared_unmaterialized_domains=(DeclaredUnmaterializedDomain("research", "lawful-domain"),),
    )
    assert plan.materialized_scopes == (empty_private,)
    assert plan.runtime_scopes == (empty_private, declared_shared)

    physical_plan = WorkspaceRootAdmissionPlan(
        "ws-empty", shared_materialized_scopes=(physical_no_motif_shared,),
    )
    assert physical_plan.materialized_scopes == (physical_no_motif_shared,)
    assert physical_plan.runtime_scopes == (physical_no_motif_shared,)
    assert physical_plan.no_memory_scope is False


def test_empty_shared_postures_require_their_respective_motif_evidence(tmp_path: Path) -> None:
    description, _root, _manifest = _fixture_description(tmp_path)
    workspace = next(item for item in description.workspace_plans if item.workspace_id == "ws-one")
    original_scope = workspace.shared_materialized_scopes[0]
    no_motif_scope = MaterializedRootScopePlan(
        original_scope.scope_key, RootRepresentationDisposition.NO_VECTOR,
        MaterializedScopePosture.EMPTY_SHARED_WITHOUT_MOTIF,
    )
    revised_workspace = replace(workspace, shared_materialized_scopes=(no_motif_scope,))
    revised_counts = tuple(
        RepresentationDispositionCount(
            item.disposition,
            item.scope_count - 1 if item.disposition is RootRepresentationDisposition.TARGET_COMPATIBLE
            else item.scope_count + 1 if item.disposition is RootRepresentationDisposition.NO_VECTOR
            else item.scope_count,
        )
        for item in description.expected_census.representation_disposition_counts
    )
    with pytest.raises(RootAdmissionDescriptionError, match="cannot declare motif evidence"):
        replace(
            description,
            workspace_plans=tuple(
                revised_workspace if item.workspace_id == "ws-one" else item
                for item in description.workspace_plans
            ),
            expected_census=replace(
                description.expected_census, representation_disposition_counts=revised_counts,
            ),
        )

    without_motif = RootEvidenceManifest(tuple(
        item for item in description.explicit_source_manifest.entries
        if not (
            item.scope_key == original_scope.scope_key
            and item.semantic_role is EvidenceSemanticRole.MOTIFS
        )
    ))
    with pytest.raises(RootAdmissionDescriptionError, match="lacks absent motif evidence"):
        replace(
            description,
            workspace_plans=tuple(
                revised_workspace if item.workspace_id == "ws-one" else item
                for item in description.workspace_plans
            ),
            expected_census=replace(
                description.expected_census, representation_disposition_counts=revised_counts,
            ),
            explicit_source_manifest=without_motif,
        )
    with pytest.raises(RootAdmissionDescriptionError, match="lacks present motif evidence"):
        replace(description, explicit_source_manifest=without_motif)


def test_census_refuses_arithmetic_and_topology_contradictions() -> None:
    counts = tuple(RepresentationDispositionCount(disposition, 0) for disposition in RootRepresentationDisposition)
    with pytest.raises(RootAdmissionDescriptionError, match="private plus shared"):
        ExpectedRootCensus(1, 1, 0, 2, counts, WorkspaceTopologyCounts(0, 1, 0, 1, 0, 0))
    with pytest.raises(RootAdmissionDescriptionError, match="representation disposition"):
        ExpectedRootCensus(1, 0, 0, 0, counts[:-1], WorkspaceTopologyCounts(1, 0, 0, 1, 0, 0))
    with pytest.raises(RootAdmissionDescriptionError, match="private workspace topology"):
        ExpectedRootCensus(2, 0, 0, 0, counts, WorkspaceTopologyCounts(1, 0, 0, 2, 0, 0))


def test_root_scope_key_requires_complete_composite_identity_and_prevents_collisions() -> None:
    left = RootScopeKey("ws-a", RootScopeKind.PRIVATE, agent_id="aria")
    right = RootScopeKey("ws-b", RootScopeKind.PRIVATE, agent_id="aria")

    assert left != right
    assert left.canonical_key != right.canonical_key
    with pytest.raises(RootScopeKeyError, match="forbids domain_id"):
        RootScopeKey("ws-a", RootScopeKind.PRIVATE, agent_id="aria", domain_id="research")
    with pytest.raises(RootScopeKeyError, match="requires agent_id"):
        RootScopeKey("ws-a", RootScopeKind.PRIVATE)
    with pytest.raises(RootScopeKeyError, match="forbids agent_id"):
        RootScopeKey("ws-a", RootScopeKind.SHARED, agent_id="aria", domain_id="research")

    ordering = WorkspaceRootAdmissionPlan(
        workspace_id="ws-order",
        private_materialized_scopes=(
            MaterializedRootScopePlan(RootScopeKey("ws-order", RootScopeKind.PRIVATE, agent_id="zulu"), RootRepresentationDisposition.NO_VECTOR),
            MaterializedRootScopePlan(RootScopeKey("ws-order", RootScopeKind.PRIVATE, agent_id="alpha"), RootRepresentationDisposition.NO_VECTOR),
        ),
        shared_materialized_scopes=(
            MaterializedRootScopePlan(RootScopeKey("ws-order", RootScopeKind.SHARED, domain_id="zulu"), RootRepresentationDisposition.NO_VECTOR),
            MaterializedRootScopePlan(RootScopeKey("ws-order", RootScopeKind.SHARED, domain_id="alpha"), RootRepresentationDisposition.NO_VECTOR),
        ),
    )
    assert [scope.scope_key.qualifier for scope in ordering.private_materialized_scopes] == ["alpha", "zulu"]
    assert [scope.scope_key.qualifier for scope in ordering.shared_materialized_scopes] == ["alpha", "zulu"]


def test_manifest_is_deterministic_reopenable_and_owner_bounded(tmp_path: Path) -> None:
    description, root, manifest = _fixture_description(tmp_path)
    reverse = RootEvidenceManifest(tuple(reversed(manifest.entries)))
    manifest_path = tmp_path / "root-evidence-manifest.json"

    assert reverse.digest == manifest.digest
    write_explicit_source_manifest(manifest, manifest_path)
    reloaded = load_explicit_source_manifest(manifest_path)
    verification = reloaded.verify(data_root=root)
    assert reloaded.digest == manifest.digest
    assert len(verification.verified_present_entries) > 0
    assert len(verification.verified_absent_entries) == 3
    assert description.explicit_source_manifest.digest == manifest.digest


def test_manifest_recheck_refuses_declared_drift_required_deletion_and_absent_creation(tmp_path: Path) -> None:
    _description, root, manifest = _fixture_description(tmp_path)
    manifest.verify(data_root=root)

    declared = root / "workspaces/ws-one/agents/aria/private/nodes.jsonl"
    declared.write_bytes(b"changed")
    with pytest.raises(ExplicitSourceEvidenceDrift, match="declared evidence drifted"):
        manifest.verify(data_root=root)

    declared.unlink()
    with pytest.raises(ExplicitSourceEvidenceDrift, match="required evidence is missing"):
        manifest.verify(data_root=root)

    _description, root, manifest = _fixture_description(tmp_path / "fresh")
    unexpected = root / "workspaces/ws-one/domains/research/shared/nodes.jsonl"
    unexpected.write_bytes(b"unexpected")
    with pytest.raises(ExplicitSourceEvidenceDrift, match="expected-absent evidence was created"):
        manifest.verify(data_root=root)


def test_unrelated_non_owner_file_does_not_change_manifest_identity_or_recheck(tmp_path: Path) -> None:
    _description, root, manifest = _fixture_description(tmp_path)
    before = manifest.digest
    _write(root, "workspaces/ws-one/unrelated-non-owner.bin", b"unrelated")

    assert manifest.verify(data_root=root).manifest_digest == before
    assert manifest.digest == before


def test_manifest_rejects_escape_cross_workspace_and_owner_class_mismatch(tmp_path: Path) -> None:
    _description, root, _manifest = _fixture_description(tmp_path)
    private = EvidenceOwnerBoundary("ws-one", EvidenceOwnerBoundaryKind.PRIVATE_SCOPE, agent_id="aria")
    shared = EvidenceOwnerBoundary("ws-one", EvidenceOwnerBoundaryKind.SHARED_SCOPE, domain_id="research")
    aria = RootScopeKey("ws-one", RootScopeKind.PRIVATE, agent_id="aria")

    with pytest.raises(ExplicitSourceEvidenceError, match="escapes|locator"):
        capture_present_source_evidence(
            data_root=root,
            owner_class=SourceOwnerClass.PRIVATE_GRAPH_SOURCE,
            owner_boundary=private,
            canonical_locator="../nodes.jsonl",
            semantic_role=EvidenceSemanticRole.NODES,
            scope_key=aria,
        )
    with pytest.raises(ExplicitSourceEvidenceError, match="relative"):
        capture_present_source_evidence(
            data_root=root,
            owner_class=SourceOwnerClass.PRIVATE_GRAPH_SOURCE,
            owner_boundary=private,
            canonical_locator="/nodes.jsonl",
            semantic_role=EvidenceSemanticRole.NODES,
            scope_key=aria,
        )
    with pytest.raises(ExplicitSourceEvidenceError, match="crosses its owner workspace"):
        ExplicitSourceEvidence(
            SourceOwnerClass.PRIVATE_GRAPH_SOURCE, private, "nodes.jsonl", EvidenceSemanticRole.NODES,
            EvidencePresenceExpectation.EXPECTED_ABSENT,
            RootScopeKey("ws-other", RootScopeKind.PRIVATE, agent_id="aria"),
            absence_reason=EvidenceAbsenceReason.UNMATERIALIZED_DECLARATION,
        )
    with pytest.raises(ExplicitSourceEvidenceError, match="owner boundary"):
        ExplicitSourceEvidence(
            SourceOwnerClass.PRIVATE_GRAPH_SOURCE, shared, "nodes.jsonl", EvidenceSemanticRole.NODES,
            EvidencePresenceExpectation.EXPECTED_ABSENT,
            RootScopeKey("ws-one", RootScopeKind.SHARED, domain_id="research"),
            absence_reason=EvidenceAbsenceReason.EMPTY_GRAPH,
        )
    with pytest.raises(ExplicitSourceEvidenceError, match="owner boundary"):
        ExplicitSourceEvidence(
            SourceOwnerClass.PRIVATE_GRAPH_SOURCE,
            EvidenceOwnerBoundary("ws-one", EvidenceOwnerBoundaryKind.WORKSPACE),
            "nodes.jsonl",
            EvidenceSemanticRole.NODES,
            EvidencePresenceExpectation.EXPECTED_ABSENT,
            absence_reason=EvidenceAbsenceReason.UNMATERIALIZED_DECLARATION,
        )


def test_unknown_owner_is_refused_and_representation_identity_requires_provider_model_dimension(tmp_path: Path) -> None:
    _description, _root, _manifest = _fixture_description(tmp_path)
    with pytest.raises(ExplicitSourceEvidenceError, match="owner_class"):
        ExplicitSourceEvidence(
            "UNKNOWN",  # type: ignore[arg-type]
            EvidenceOwnerBoundary("ws-one", EvidenceOwnerBoundaryKind.WORKSPACE),
            "workspace_meta.json",
            EvidenceSemanticRole.WORKSPACE_META,
            EvidencePresenceExpectation.EXPECTED_ABSENT,
            absence_reason=EvidenceAbsenceReason.UNMATERIALIZED_DECLARATION,
        )
    assert representation_identity_matches_target(
        provider="st", model="BAAI/bge-small-en-v1.5", dimension=384, target_lane=_lane()
    ) is True
    assert representation_identity_matches_target(
        provider="hash", model="torment", dimension=384, target_lane=_lane()
    ) is False


def test_description_identity_changes_with_semantic_input_and_first_profile_is_not_replaced(tmp_path: Path) -> None:
    description, _root, _manifest = _fixture_description(tmp_path)
    changed = replace(description, operator_identity="different-operator")

    assert changed.identity_digest != description.identity_digest
    with pytest.raises(RootAdmissionDescriptionError, match="frozen st"):
        replace(description, target_representation_lane=_lane(provider="hash", model="torment"))
    assert ExistingWorkspaceNativeMultiScopeAdmissionRequest is not RootNativeProductionAdmissionDescription
    assert "lane_plans" in ExistingWorkspaceNativeMultiScopeAdmissionRequest.__dataclass_fields__

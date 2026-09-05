from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import shutil
from typing import Callable

import pytest

from torment_service.substrate.canonical_intent import canonical_intent_text
from torment_service.substrate.deployment_types import digest_mapping
from torment_service.substrate.corrective_freeze_packet import (
    CORRECTIVE_FREEZE_PACKET_VERSION,
    CorrectiveCaptureObservations,
    CorrectiveFreezePacketRefused,
    CorrectiveFreezeTypedEvidence,
    DeclaredEmptySharedSourceEvidence,
    EmptyPrivateSourceEvidence,
    ExcludedSourceArtifactExpectation,
    FrozenWorkspaceTreeTriple,
    MetadataLessPerEidEvidence,
    PredecessorFreezeLineage,
    RootSourceScopePlan,
    SourceArtifactKind,
    SourceArtifactObservation,
    SourceArtifactPresence,
    capture_corrective_freeze_packet,
    load_corrective_freeze_packet,
)
from torment_service.substrate.migration.explicit_source_evidence import (
    EvidenceAbsenceReason,
    EvidenceOwnerBoundary,
    EvidenceOwnerBoundaryKind,
    EvidencePresenceExpectation,
    EvidenceSemanticRole,
    ExplicitSourceEvidence,
    RootEvidenceManifest,
    SourceOwnerClass,
    capture_present_source_evidence,
)
from torment_service.substrate.migration.root_admission_description import (
    DeclaredUnmaterializedDomain,
    ExpectedRootCensus,
    ExternalOwnerObservation,
    ExternalOwnerObservationKind,
    IdentityOnlyAgentObservation,
    MaterializedRootScopePlan,
    MaterializedScopePosture,
    RepresentationDispositionCount,
    RootFeaturePosture,
    RootNativeProductionAdmissionDescription,
    RootRepresentationDisposition,
    WorkspaceRootAdmissionPlan,
    WorkspaceTopologyCounts,
)
from torment_service.substrate.migration.root_scope import RootScopeKey, RootScopeKind
from torment_service.substrate.root_blocker5_binding import (
    RootBlocker5BindingRefused,
    RootGeometryDispositionPlan,
    RootWriterFreezeWitness,
    build_real_root_v2_admission_envelope,
    discover_canonical_root_layout,
    frozen_root_geometry_disposition_plan,
)
from torment_service.substrate.runtime_binding import NativeRepresentationLane
from torment_service.substrate.writer_freeze_evidence import (
    ListenerObservation,
    ListenerObservationResult,
    RootJobObservation,
    RootWriterClass,
    WriterObservationResult,
    WriterProcessObservation,
    snapshot_root_workspaces,
)


def _digest(value: object) -> str:
    if isinstance(value, bytes):
        payload = value
    elif isinstance(value, str):
        payload = value.encode("utf-8")
    else:
        payload = canonical_intent_text(value).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _lane() -> NativeRepresentationLane:
    return NativeRepresentationLane(
        "st", "BAAI/bge-small-en-v1.5", 384,
        "COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR", "float32",
    )


def _write(path: Path, content: str | bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content if isinstance(content, bytes) else content.encode("utf-8"))


def _present(
    root: Path, *, owner_class: SourceOwnerClass, boundary: EvidenceOwnerBoundary,
    locator: str, role: EvidenceSemanticRole, scope: RootScopeKey | None = None,
) -> ExplicitSourceEvidence:
    return capture_present_source_evidence(
        data_root=root, owner_class=owner_class, owner_boundary=boundary,
        canonical_locator=locator, semantic_role=role, scope_key=scope,
    )


def _absent(
    *, owner_class: SourceOwnerClass, boundary: EvidenceOwnerBoundary, locator: str,
    role: EvidenceSemanticRole, scope: RootScopeKey, reason: EvidenceAbsenceReason,
) -> ExplicitSourceEvidence:
    return ExplicitSourceEvidence(
        owner_class=owner_class, owner_boundary=boundary, canonical_locator=locator,
        semantic_role=role, presence_expectation=EvidencePresenceExpectation.EXPECTED_ABSENT,
        scope_key=scope, absence_reason=reason,
    )


@dataclass
class _FixtureAdapter:
    root: Path
    description: RootNativeProductionAdmissionDescription
    source_scope_plans: tuple[RootSourceScopePlan, ...]
    unknown: tuple[MetadataLessPerEidEvidence, ...]
    empty_private: tuple[EmptyPrivateSourceEvidence, ...]
    declared_empty: tuple[DeclaredEmptySharedSourceEvidence, ...]
    geometry: RootGeometryDispositionPlan

    def capture_typed_evidence(self, *, data_root: Path, discovered_census):
        assert data_root == self.root
        return CorrectiveFreezeTypedEvidence(
            description=self.description,
            discovered_census=discovered_census,
            source_scope_plans=self.source_scope_plans,
            unknown_identity_evidence=self.unknown,
            empty_private_evidence=self.empty_private,
            declared_empty_shared_evidence=self.declared_empty,
            geometry_disposition_plan=self.geometry,
        )


@dataclass
class _Fixture:
    root: Path
    adapter: _FixtureAdapter
    lineage: PredecessorFreezeLineage
    observations: CorrectiveCaptureObservations
    excluded: tuple[ExcludedSourceArtifactExpectation, ...]


def _fixture(tmp_path: Path) -> _Fixture:
    root = tmp_path / "disposable-held-freeze-source"
    alpha = root / "workspaces" / "alpha"
    beta = root / "workspaces" / "beta"
    _write(alpha / "workspace_meta.json", "{}")
    _write(alpha / "domains.json", '{"domains":["team","ghost"]}')
    _write(beta / "workspace_meta.json", "{}")
    _write(beta / "domains.json", '{"domains":["project"]}')
    for workspace, agent in ((alpha, "alice"), (alpha, "bob"), (alpha, "cory"), (alpha, "aria"), (beta, "dana")):
        _write(workspace / "agents" / agent / "identity.json", '{"identity":true}')
        (workspace / "agents" / agent / "private").mkdir(parents=True, exist_ok=True)
    for workspace, agent in ((alpha, "alice"), (alpha, "bob"), (alpha, "cory"), (beta, "dana")):
        _write(workspace / "agents" / agent / "private" / "nodes.jsonl", '{"node":1}\n')
    _write(alpha / "agents" / "cory" / "private" / "legacy-vector.bin", b"vector-cory")
    _write(alpha / "agents" / "cory" / "private" / "canonical-text.json", '{"text":"opaque"}')
    _write(alpha / "agents" / "aria" / "private" / "embedding_manifest.json", '{"total_rows":0,"next_row":0}')
    for workspace, domain in ((alpha, "team"), (beta, "project")):
        _write(workspace / "domains" / domain / "shared" / "nodes.jsonl", '{"node":1}\n')
    _write(root / "unscoped_nodes.jsonl", "residual")
    _write(root / "unscoped_embeddings.bin", b"residual-vectors")

    alice = RootScopeKey("alpha", RootScopeKind.PRIVATE, agent_id="alice")
    bob = RootScopeKey("alpha", RootScopeKind.PRIVATE, agent_id="bob")
    cory = RootScopeKey("alpha", RootScopeKind.PRIVATE, agent_id="cory")
    aria = RootScopeKey("alpha", RootScopeKind.PRIVATE, agent_id="aria")
    dana = RootScopeKey("beta", RootScopeKind.PRIVATE, agent_id="dana")
    team = RootScopeKey("alpha", RootScopeKind.SHARED, domain_id="team")
    ghost = RootScopeKey("alpha", RootScopeKind.SHARED, domain_id="ghost")
    project = RootScopeKey("beta", RootScopeKind.SHARED, domain_id="project")
    alpha_workspace = EvidenceOwnerBoundary("alpha", EvidenceOwnerBoundaryKind.WORKSPACE)
    beta_workspace = EvidenceOwnerBoundary("beta", EvidenceOwnerBoundaryKind.WORKSPACE)
    alpha_aria_agent = EvidenceOwnerBoundary("alpha", EvidenceOwnerBoundaryKind.AGENT, agent_id="aria")

    entries: list[ExplicitSourceEvidence] = []
    alpha_domains = _present(root, owner_class=SourceOwnerClass.DOMAIN_DECLARATION, boundary=alpha_workspace,
        locator="domains.json", role=EvidenceSemanticRole.DOMAINS)
    entries.extend((
        _present(root, owner_class=SourceOwnerClass.WORKSPACE_IDENTITY_METADATA, boundary=alpha_workspace,
            locator="workspace_meta.json", role=EvidenceSemanticRole.WORKSPACE_META),
        alpha_domains,
        _present(root, owner_class=SourceOwnerClass.WORKSPACE_IDENTITY_METADATA, boundary=beta_workspace,
            locator="workspace_meta.json", role=EvidenceSemanticRole.WORKSPACE_META),
        _present(root, owner_class=SourceOwnerClass.DOMAIN_DECLARATION, boundary=beta_workspace,
            locator="domains.json", role=EvidenceSemanticRole.DOMAINS),
        _present(root, owner_class=SourceOwnerClass.EXTERNAL_OWNER_OBSERVATION, boundary=alpha_workspace,
            locator="workspace_meta.json", role=EvidenceSemanticRole.EXTERNAL_OBSERVATION),
    ))
    for scope in (alice, bob, cory, dana):
        boundary = EvidenceOwnerBoundary(scope.workspace_id, EvidenceOwnerBoundaryKind.PRIVATE_SCOPE, agent_id=scope.agent_id)
        entries.append(_present(root, owner_class=SourceOwnerClass.PRIVATE_GRAPH_SOURCE, boundary=boundary,
            locator="nodes.jsonl", role=EvidenceSemanticRole.NODES, scope=scope))
    for scope in (team, project):
        boundary = EvidenceOwnerBoundary(scope.workspace_id, EvidenceOwnerBoundaryKind.SHARED_SCOPE, domain_id=scope.domain_id)
        entries.append(_present(root, owner_class=SourceOwnerClass.SHARED_GRAPH_SOURCE, boundary=boundary,
            locator="nodes.jsonl", role=EvidenceSemanticRole.NODES, scope=scope))
    cory_boundary = EvidenceOwnerBoundary("alpha", EvidenceOwnerBoundaryKind.PRIVATE_SCOPE, agent_id="cory")
    cory_vector = _present(root, owner_class=SourceOwnerClass.METADATA_LESS_PER_EID_LEGACY_REPRESENTATION,
        boundary=cory_boundary, locator="legacy-vector.bin", role=EvidenceSemanticRole.LEGACY_REPRESENTATION, scope=cory)
    cory_text = _present(root, owner_class=SourceOwnerClass.PRIVATE_GRAPH_SOURCE,
        boundary=cory_boundary, locator="canonical-text.json", role=EvidenceSemanticRole.NODES, scope=cory)
    entries.extend((cory_vector, cory_text))
    aria_boundary = EvidenceOwnerBoundary("alpha", EvidenceOwnerBoundaryKind.PRIVATE_SCOPE, agent_id="aria")
    aria_nodes = _absent(owner_class=SourceOwnerClass.PRIVATE_GRAPH_SOURCE, boundary=aria_boundary,
        locator="nodes.jsonl", role=EvidenceSemanticRole.NODES, scope=aria, reason=EvidenceAbsenceReason.EMPTY_GRAPH)
    aria_embedding = _present(root, owner_class=SourceOwnerClass.EMBEDDING_MANIFEST, boundary=aria_boundary,
        locator="embedding_manifest.json", role=EvidenceSemanticRole.EMBEDDING_MANIFEST, scope=aria)
    ghost_boundary = EvidenceOwnerBoundary("alpha", EvidenceOwnerBoundaryKind.SHARED_SCOPE, domain_id="ghost")
    ghost_nodes = _absent(owner_class=SourceOwnerClass.SHARED_GRAPH_SOURCE, boundary=ghost_boundary,
        locator="nodes.jsonl", role=EvidenceSemanticRole.NODES, scope=ghost,
        reason=EvidenceAbsenceReason.UNMATERIALIZED_DECLARATION)
    aria_identity = _present(root, owner_class=SourceOwnerClass.EXTERNAL_OWNER_OBSERVATION,
        boundary=alpha_aria_agent, locator="identity.json", role=EvidenceSemanticRole.EXTERNAL_OBSERVATION)
    entries.extend((aria_nodes, aria_embedding, ghost_nodes, aria_identity))
    manifest = RootEvidenceManifest(tuple(entries))

    external = (ExternalOwnerObservation(
        workspace_id="alpha", owner_kind=ExternalOwnerObservationKind.IDENTITY,
        observation_key="synthetic:alpha:identity", observation_digest=_digest("alpha-owner"),
    ),)
    alpha_private = (
        MaterializedRootScopePlan(alice, RootRepresentationDisposition.TARGET_COMPATIBLE),
        MaterializedRootScopePlan(bob, RootRepresentationDisposition.REEMBED_REQUIRED),
        MaterializedRootScopePlan(cory, RootRepresentationDisposition.UNKNOWN_IDENTITY),
        MaterializedRootScopePlan(aria, RootRepresentationDisposition.NO_VECTOR, MaterializedScopePosture.EMPTY_PRIVATE),
    )
    alpha_shared = (
        MaterializedRootScopePlan(team, RootRepresentationDisposition.TARGET_COMPATIBLE),
        MaterializedRootScopePlan(ghost, RootRepresentationDisposition.NO_VECTOR, MaterializedScopePosture.DECLARED_EMPTY_SHARED),
    )
    beta_private = (MaterializedRootScopePlan(dana, RootRepresentationDisposition.TARGET_COMPATIBLE),)
    beta_shared = (MaterializedRootScopePlan(project, RootRepresentationDisposition.REEMBED_REQUIRED),)
    counts = {
        RootRepresentationDisposition.TARGET_COMPATIBLE: 3,
        RootRepresentationDisposition.REEMBED_REQUIRED: 2,
        RootRepresentationDisposition.UNKNOWN_IDENTITY: 1,
        RootRepresentationDisposition.NO_VECTOR: 2,
        RootRepresentationDisposition.UNUSABLE_VECTOR: 0,
    }
    description = RootNativeProductionAdmissionDescription(
        data_root_identity="synthetic-held-freeze-root", operator_identity="synthetic-corrective-operator",
        workspace_plans=(
            WorkspaceRootAdmissionPlan("alpha", alpha_private, alpha_shared,
                identity_only_agents=(IdentityOnlyAgentObservation("aria", "synthetic:aria:identity"),),
                declared_unmaterialized_domains=(DeclaredUnmaterializedDomain("ghost", "synthetic:ghost:domains"),)),
            WorkspaceRootAdmissionPlan("beta", beta_private, beta_shared),
        ),
        target_representation_lane=_lane(),
        expected_census=ExpectedRootCensus(
            workspace_count=2, materialized_private_scope_count=5, materialized_shared_scope_count=2,
            total_materialized_scope_count=7, declared_empty_shared_scope_count=1,
            empty_private_identity_scope_count=1,
            representation_disposition_counts=tuple(RepresentationDispositionCount(key, value) for key, value in counts.items()),
            workspace_topology_counts=WorkspaceTopologyCounts(0, 1, 1, 0, 1, 1),
        ),
        explicit_source_manifest=manifest, external_owner_observations=external,
        feature_posture=RootFeaturePosture("synthetic-held-freeze", False, False),
    )
    all_scopes = tuple(scope for workspace in description.workspace_plans for scope in workspace.runtime_scopes)
    source_plans = tuple(RootSourceScopePlan(
        scope_key=scope.scope_key, materialization_posture=scope.materialization_posture,
        representation_disposition=scope.representation_disposition,
        motif_domain_id=("team" if scope.scope_key.scope_kind is RootScopeKind.PRIVATE else scope.scope_key.domain_id),
        target_representation_lane=_lane(),
    ) for scope in all_scopes)
    unknown = (MetadataLessPerEidEvidence(
        scope_key=cory, eid=7, vector_evidence=cory_vector, canonical_text_evidence=cory_text,
        dtype="float32", shape=(384,), metadata_less_source_evidence_identity="synthetic:cory:eid:7",
    ),)
    directory = SourceArtifactObservation(
        "private", SourceArtifactPresence.PRESENT, "DIRECTORY_PRESENT",
        artifact_kind=SourceArtifactKind.DIRECTORY,
    )
    memory_events = SourceArtifactObservation("memory_events.jsonl", SourceArtifactPresence.ABSENT, "ABSENT")
    empty_unsigned = {
        "scope_key": aria.identity_payload(), "identity_declaration_evidence": aria_identity.identity_payload(),
        "private_directory_observation": directory.payload(), "nodes_absence_evidence": aria_nodes.identity_payload(),
        "memory_events_observation": memory_events.payload(), "embedding_manifest_evidence": aria_embedding.identity_payload(),
        "embedding_manifest_total_rows": 0, "embedding_manifest_next_row": 0,
    }
    empty = (EmptyPrivateSourceEvidence(
        scope_key=aria, identity_declaration_evidence=aria_identity, private_directory_observation=directory,
        nodes_absence_evidence=aria_nodes, memory_events_observation=memory_events,
        embedding_manifest_evidence=aria_embedding, embedding_manifest_total_rows=0,
        embedding_manifest_next_row=0, canonical_source_evidence_digest=_digest(empty_unsigned),
    ),)
    shared_absent = SourceArtifactObservation(
        "shared", SourceArtifactPresence.ABSENT, "ABSENT", artifact_kind=SourceArtifactKind.DIRECTORY,
    )
    motif_absent = SourceArtifactObservation("motifs.json", SourceArtifactPresence.ABSENT, "ABSENT")
    declared_unsigned = {
        "workspace_id": "alpha", "domain_id": "ghost", "domains_declaration_evidence": alpha_domains.identity_payload(),
        "shared_directory_observation": shared_absent.payload(), "nodes_absence_evidence": ghost_nodes.identity_payload(),
        "motif_observation": motif_absent.payload(), "observation_key": "synthetic:alpha:ghost",
    }
    declared = (DeclaredEmptySharedSourceEvidence(
        workspace_id="alpha", domain_id="ghost", domains_declaration_evidence=alpha_domains,
        shared_directory_observation=shared_absent, nodes_absence_evidence=ghost_nodes,
        motif_observation=motif_absent, observation_key="synthetic:alpha:ghost",
        observation_digest=_digest(declared_unsigned),
    ),)
    geometry = frozen_root_geometry_disposition_plan(
        external_owner_observation_digest=description.external_owner_observation_digest,
    )
    predecessor_snapshot = snapshot_root_workspaces(data_root=root)
    lineage = PredecessorFreezeLineage(
        predecessor_operation_identity="synthetic-predecessor", predecessor_payload_digest=_digest("previous-payload"),
        predecessor_witness_digest=_digest("previous-witness"),
        predecessor_tree=FrozenWorkspaceTreeTriple(
            predecessor_snapshot.tree_digest, predecessor_snapshot.file_count, predecessor_snapshot.maximum_mtime_ns,
        ),
        successor_operation_identity="synthetic-successor", operator_identity="synthetic-corrective-operator",
        capture_head="synthetic-head",
    )
    observations = CorrectiveCaptureObservations(
        covered_writer_classes=tuple(WriterProcessObservation(item, "SYNTHETIC", WriterObservationResult.ABSENT) for item in RootWriterClass),
        listener_observation=ListenerObservation("synthetic-listener", "SYNTHETIC", ListenerObservationResult.ABSENT),
        job_observer=lambda **_kwargs: RootJobObservation(0, "SYNTHETIC"),
        clock_ns=iter((2_000_000_000_000_000_000, 2_000_000_061_000_000_000, 2_000_000_062_000_000_000)).__next__,
        snapshotter=snapshot_root_workspaces,
    )
    excluded = tuple(ExcludedSourceArtifactExpectation(name, role, _digest((root / name).read_bytes())) for name, role in (
        ("unscoped_nodes.jsonl", "TOP_LEVEL_UNSCOPED_NODES"),
        ("unscoped_embeddings.bin", "TOP_LEVEL_UNSCOPED_EMBEDDINGS"),
    ))
    return _Fixture(
        root=root,
        adapter=_FixtureAdapter(root, description, source_plans, unknown, empty, declared, geometry),
        lineage=lineage, observations=observations, excluded=excluded,
    )


def _capture(fixture: _Fixture, packet: Path):
    return capture_corrective_freeze_packet(
        data_root=fixture.root, packet_directory=packet,
        data_root_identity="synthetic-held-freeze-root", lineage=fixture.lineage,
        observations=fixture.observations, source_adapter=fixture.adapter, excluded_artifacts=fixture.excluded,
        expected_root_admission_description_contract="ROOT_ADMISSION_DESCRIPTION_V1",
        invalidation_rule_version="ROOT_WRITER_FREEZE_INVALIDATION_V1",
    )


def test_complete_packet_reloads_after_disposable_source_is_absent(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    packet = _capture(fixture, tmp_path / "packet")

    assert packet.writer_freeze_witness.writer_evidence_digest == packet.writer_freeze_payload.digest
    assert packet.typed_evidence.discovered_census == discover_canonical_root_layout(data_root=fixture.root)
    assert len(packet.typed_evidence.source_scope_plans) == 8
    assert len(packet.typed_evidence.unknown_identity_evidence) == 1
    assert len(packet.typed_evidence.empty_private_evidence) == 1
    assert len(packet.typed_evidence.declared_empty_shared_evidence) == 1
    shutil.rmtree(fixture.root)

    reloaded = load_corrective_freeze_packet(packet.directory)
    assert reloaded.packet_digest == packet.packet_digest
    assert reloaded.typed_evidence.description.identity_digest == packet.typed_evidence.description.identity_digest
    assert not fixture.root.exists()


def test_predecessor_tree_mismatch_refuses_before_source_adapter(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    fixture.lineage = PredecessorFreezeLineage(
        predecessor_operation_identity=fixture.lineage.predecessor_operation_identity,
        predecessor_payload_digest=fixture.lineage.predecessor_payload_digest,
        predecessor_witness_digest=fixture.lineage.predecessor_witness_digest,
        predecessor_tree=FrozenWorkspaceTreeTriple(_digest("wrong"), 0, 0),
        successor_operation_identity=fixture.lineage.successor_operation_identity,
        operator_identity=fixture.lineage.operator_identity, capture_head=fixture.lineage.capture_head,
    )
    with pytest.raises(CorrectiveFreezePacketRefused, match="PREDECESSOR_MISMATCH"):
        _capture(fixture, tmp_path / "packet")


def test_post_capture_tree_drift_refuses(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    calls = 0

    def drifting_snapshotter(*, data_root: Path):
        nonlocal calls
        calls += 1
        if calls == 3:
            _write(data_root / "workspaces" / "alpha" / "workspace_meta.json", '{"changed":true}')
        snapshot = snapshot_root_workspaces(data_root=data_root)
        return snapshot

    fixture.observations = CorrectiveCaptureObservations(
        fixture.observations.covered_writer_classes, fixture.observations.listener_observation,
        fixture.observations.job_observer, fixture.observations.clock_ns, drifting_snapshotter,
    )
    with pytest.raises(CorrectiveFreezePacketRefused, match="T2_TREE_DRIFT"):
        _capture(fixture, tmp_path / "packet")


def test_predecessor_excluded_artifact_mismatch_refuses(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    fixture.excluded = (ExcludedSourceArtifactExpectation("unscoped_nodes.jsonl", "TOP_LEVEL", _digest("wrong")),)
    with pytest.raises(CorrectiveFreezePacketRefused, match="PREDECESSOR_EXCLUDED"):
        _capture(fixture, tmp_path / "packet")


def test_real_root_v2_entry_refuses_witness_only_before_any_root_read(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    with pytest.raises(RootBlocker5BindingRefused, match="ROOT_V2_WRITER_FREEZE_PAYLOAD_REQUIRED"):
        build_real_root_v2_admission_envelope(
            data_root=tmp_path / "not-read", description=fixture.adapter.description,
            writer_freeze=RootWriterFreezeWitness(
                data_root_identity=fixture.adapter.description.data_root_identity,
                writer_freeze_operation_identity="witness-only", writer_evidence_digest=_digest("witness-only"),
            ),
            geometry_disposition_plan=fixture.adapter.geometry, effective_profile=None,  # type: ignore[arg-type]
            native_staging_core_id=None, root_profile=None, runtime_scopes=(), runtime_scope_plans=(), connection=None,
            writer_freeze_evidence=None, writer_freeze_recheck=None,
        )


def _rewrite_manifest(packet: Path) -> None:
    files = []
    for path in sorted(packet.glob("*.json")):
        if path.name == "packet_manifest.json":
            continue
        raw = path.read_bytes()
        files.append({"filename": path.name, "byte_length": len(raw), "sha256": _digest(raw)})
    unsigned = {
        "contract": "TORMENT_HELD_FREEZE_CORRECTIVE_PACKET",
        "version": CORRECTIVE_FREEZE_PACKET_VERSION,
        "artifacts": files,
    }
    (packet / "packet_manifest.json").write_text(canonical_intent_text({**unsigned, "packet_digest": _digest(unsigned)}) + "\n", encoding="utf-8")


def _change_json(packet: Path, filename: str, change: Callable[[dict], None]) -> None:
    path = packet / filename
    payload = json.loads(path.read_text(encoding="utf-8"))
    change(payload)
    path.write_text(canonical_intent_text(payload) + "\n", encoding="utf-8")
    _rewrite_manifest(packet)


@pytest.mark.parametrize("filename", ("writer_freeze_payload.json", "source_manifest.json"))
def test_packet_file_changed_or_manifest_hash_mismatch_refuses(tmp_path: Path, filename: str) -> None:
    fixture = _fixture(tmp_path)
    packet = _capture(fixture, tmp_path / "packet").directory
    path = packet / filename
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(CorrectiveFreezePacketRefused, match="HASH_MISMATCH"):
        load_corrective_freeze_packet(packet)


@pytest.mark.parametrize("filename", ("unknown_identity_evidence.json", "excluded_alternate_roots.json"))
def test_packet_file_missing_refuses(tmp_path: Path, filename: str) -> None:
    fixture = _fixture(tmp_path)
    packet = _capture(fixture, tmp_path / "packet").directory
    (packet / filename).unlink()
    with pytest.raises(CorrectiveFreezePacketRefused):
        load_corrective_freeze_packet(packet)


def test_witness_payload_mismatch_refuses_after_the_witness_digest_is_recomputed(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    packet = _capture(fixture, tmp_path / "packet").directory

    def change(value: dict) -> None:
        value["witness"]["writer_evidence_digest"] = _digest("another-payload")
        value["witness_digest"] = digest_mapping(value["witness"])

    _change_json(packet, "writer_freeze_witness.json", change)
    with pytest.raises(CorrectiveFreezePacketRefused, match="SUCCESSOR_WITNESS_PAYLOAD_MISMATCH"):
        load_corrective_freeze_packet(packet)


def test_geometry_source_digest_mismatch_refuses_after_plan_digest_is_recomputed(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    packet = _capture(fixture, tmp_path / "packet").directory

    def change(value: dict) -> None:
        value["entries"][0]["source_observation_digest"] = _digest("other-owner-source")
        value["plan_digest"] = digest_mapping({"entries": value["entries"]})

    _change_json(packet, "geometry_disposition_plan.json", change)
    with pytest.raises(CorrectiveFreezePacketRefused, match="does not bind the external owner aggregate"):
        load_corrective_freeze_packet(packet)


@pytest.mark.parametrize(
    ("filename", "change", "message"),
    (
        ("writer_freeze_witness.json", lambda p: p["witness"].__setitem__("writer_evidence_digest", _digest("wrong")), "witness digest"),
        ("discovered_census.json", lambda p: p.__setitem__("census_digest", _digest("wrong")), "census digest"),
        ("unknown_identity_evidence.json", lambda p: p.__setitem__("entries", []), "metadata-less evidence"),
        ("declared_empty_shared_evidence.json", lambda p: p.__setitem__("entries", []), "declared-empty evidence"),
        ("external_owner_observations.json", lambda p: p["entries"][0].__setitem__("observation_digest", _digest("changed")), "aggregate digest"),
        ("geometry_disposition_plan.json", lambda p: p["entries"][0].__setitem__("source_observation_digest", _digest("changed")), "plan digest"),
        ("writer_freeze_payload.json", lambda p: p.__setitem__("version", 2), "contract or version"),
    ),
)
def test_typed_packet_tampering_refuses(tmp_path: Path, filename: str, change, message: str) -> None:
    fixture = _fixture(tmp_path)
    packet = _capture(fixture, tmp_path / "packet").directory
    _change_json(packet, filename, change)
    with pytest.raises(CorrectiveFreezePacketRefused, match=message):
        load_corrective_freeze_packet(packet)

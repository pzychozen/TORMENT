from __future__ import annotations

from collections.abc import Callable
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
from dataclasses import replace
from uuid import UUID, uuid4

import pytest

from torment_service.substrate.corrective_freeze_packet import (
    CorrectiveCaptureObservations,
    CorrectiveFreezePacketRefused,
    CorrectiveFreezeTypedEvidence,
    ExcludedAlternateRootRole,
    FrozenWorkspaceTreeTriple,
    PredecessorFreezeLineage,
    SourceArtifactPresence,
    capture_corrective_freeze_packet,
    load_corrective_freeze_packet,
)
from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.deployment_types import QualifiedDeploymentProfile
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.migration.explicit_source_evidence import (
    EvidenceAbsenceReason,
    EvidenceOwnerBoundary,
    EvidenceOwnerBoundaryKind,
    EvidencePresenceExpectation,
    EvidenceSemanticRole,
    ExplicitSourceEvidence,
    ExplicitSourceEvidenceDrift,
    SourceOwnerClass,
)
from torment_service.substrate.migration.metadata_less_per_eid_legacy_source import (
    MetadataLessRepresentationIdentity,
    qualify_metadata_less_per_eid_legacy_source,
)
from torment_service.substrate.migration.root_admission_description import (
    MaterializedScopePosture,
    RootRepresentationDisposition,
)
from torment_service.substrate.migration.root_scope import RootScopeKey, RootScopeKind
from torment_service.substrate.migration.runtime_readiness import LegacyVectorStrategy
from torment_service.substrate.objects import NativeObjectService, ObjectState
from torment_service.substrate.real_root_typed_evidence import (
    DirectPhase9BNamespaceBinding,
    DirectAdmissionSourcePreparation,
    ExcludedAlternateRootLocator,
    ExcludedSourceArtifactLocator,
    RealRootTypedEvidenceAdapter,
    _file_observation,
    _hash_file,
    _npy_header,
    _read_json,
    _regular_file,
    _validate_regular_file,
    build_real_direct_admission_source_adapter,
)
from torment_service.substrate.root_blocker5_binding import (
    RootBlocker5BindingRefused,
    build_real_root_v2_admission_envelope,
    discover_canonical_root_layout,
    root_runtime_scope_plan_digest,
)
from torment_service.substrate.root_profile import (
    ROOT_NATIVE_PROFILE_GENERATION_KIND,
    current_root_profile_generation,
    root_profile_generation_payload,
)
from torment_service.substrate.schema import create_schema
from torment_service.substrate.writer_freeze_evidence import (
    ListenerObservation,
    ListenerObservationResult,
    RootJobObservation,
    RootWriterClass,
    RootWriterFreezeRecheck,
    WriterObservationResult,
    WriterProcessObservation,
    capture_root_writer_freeze_evidence,
    snapshot_root_workspaces,
)


def _write(path: Path, value: str | bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value.encode("utf-8") if isinstance(value, str) else value)


def _json(path: Path, value: object) -> None:
    _write(path, json.dumps(value, sort_keys=True, separators=(",", ":")))


def _digest(value: object) -> str:
    if isinstance(value, bytes):
        payload = value
    else:
        payload = str(value).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _npy(path: Path, *, dimension: int = 384) -> None:
    header = "{'descr': '<f4', 'fortran_order': False, 'shape': (%d,), }" % dimension
    raw = header.encode("latin1")
    raw += b" " * ((16 - ((10 + len(raw) + 1) % 16)) % 16) + b"\n"
    _write(path, b"\x93NUMPY\x01\x00" + struct.pack("<H", len(raw)) + raw + (b"\x00" * (dimension * 4)))


def _assert_regular_file_refusal(
    operation: Callable[[], object], path: Path, shape: str,
) -> None:
    with pytest.raises(CorrectiveFreezePacketRefused) as refusal:
        operation()
    message = str(refusal.value)
    assert message.startswith("typed evidence source must be a non-symlink regular file") or (
        "typed evidence source must be a non-symlink regular file" in message
    )
    assert f"path={path}" in message
    assert f"shape={shape}" in message


def _storage(path: Path, *, dimension: int = 384, total_rows: int = 1, next_row: int = 1) -> None:
    _json(path / "embeddings" / "manifest.json", {
        "version": 1, "embedding_dim": dimension, "dtype": "float32", "rows_per_shard": 4096,
        "active_shard": 0, "next_row": next_row, "total_rows": total_rows,
    })


def _scope(root: Path, workspace: str, agent: str) -> None:
    private = root / "workspaces" / workspace / "agents" / agent / "private"
    _json(private.parent / "identity.json", {"agent": agent})
    _write(private / "nodes.jsonl", '{"node":1}\n')
    _storage(private)


def _shared(root: Path, workspace: str, domain: str) -> None:
    shared = root / "workspaces" / workspace / "domains" / domain / "shared"
    _write(shared / "nodes.jsonl", '{"node":1}\n')
    _storage(shared)


def _target_lock() -> dict[str, object]:
    return {"embed_provider": "st", "embed_model": "BAAI/bge-small-en-v1.5", "embed_dim": 384}


def _hash_lock() -> dict[str, object]:
    return {"embed_provider": "hash", "embed_model": "hash:384:torment", "embed_dim": 384}


def _direct_phase9b_bindings() -> tuple[DirectPhase9BNamespaceBinding, ...]:
    """Fixed test-only stand-ins for caller-supplied frozen P1 identities."""

    return tuple(
        DirectPhase9BNamespaceBinding(
            RootScopeKey(workspace_id, RootScopeKind.PRIVATE, agent_id="a1"),
            UUID(legacy_namespace_id),
            UUID(target_namespace_id),
        )
        for workspace_id, legacy_namespace_id, target_namespace_id in (
            ("ws3", "10000000-0000-0000-0000-000000000003", "20000000-0000-0000-0000-000000000003"),
            ("ws4", "10000000-0000-0000-0000-000000000004", "20000000-0000-0000-0000-000000000004"),
            ("ws5", "10000000-0000-0000-0000-000000000005", "20000000-0000-0000-0000-000000000005"),
        )
    )


def _fixture(tmp_path: Path) -> tuple[Path, RealRootTypedEvidenceAdapter]:
    root = tmp_path / "production-shaped-disposable-source"
    empty = root / "workspaces" / "empty"
    multi = root / "workspaces" / "multi"
    hashed = root / "workspaces" / "hash"
    _json(empty / "workspace_meta.json", {"workspace": "empty", **_target_lock()})
    _json(empty / "domains.json", {"domains": ["declared"]})
    _json(multi / "workspace_meta.json", {"workspace": "multi", **_target_lock()})
    _json(multi / "domains.json", {
        "domains": ["team", "motif", "missing"], "legacy_default_domain": "legacy",
    })
    _json(hashed / "workspace_meta.json", {"workspace": "hash", **_hash_lock()})
    _json(hashed / "domains.json", {"domains": []})
    _scope(root, "multi", "target")
    _scope(root, "hash", "rehash")
    _json(multi / "agents" / "target" / "roles.json", {"role": "synthetic"})
    _json(multi / "agents" / "target" / "character_state.json", {"state": "retained"})
    _json(multi / "seeds" / "seed-a" / "seed.json", {"seed": "retained"})
    _json(multi / "bridges.json", {"bridges": []})
    _write(multi / "bridge_events.jsonl", "")
    _json(multi / "agents" / "target" / "affect_state.json", {"affect": "retained"})
    _json(multi / "agents" / "target" / "anchors.json", {"anchors": []})
    _json(multi / "agents" / "target" / "symbol_state.json", {"symbol": "retained"})
    _write(multi / "agents" / "target" / "feedback_events.jsonl", "")
    _write(multi / "agents" / "target" / "index" / "memory_index.sqlite", b"derived-index")
    _write(multi / "agents" / "target" / "memory_archive" / "documents.jsonl", "retained")
    _write(multi / "agents" / "target" / "warmup" / "state.json", "retained")
    _write(multi / "agents" / "target" / "private" / "checkpoints" / "checkpoint.json", "retained")
    _write(multi / "agents" / "target" / "private" / "logs" / "trajectories" / "daily.jsonl", "retained")
    _shared(root, "multi", "team")
    _json(multi / "domains" / "team" / "proposals.jsonl", {"proposal": "retained"})
    _write(multi / "domains" / "team" / "proposal_events.jsonl", "")
    _json(multi / "domains" / "team" / "conflicts.jsonl", {"conflict": "retained"})
    _write(multi / "domains" / "team" / "conflict_events.jsonl", "")
    motif = multi / "domains" / "motif"
    (motif / "shared").mkdir(parents=True, exist_ok=True)
    _json(motif / "motifs.json", {"motif": "synthetic"})
    _write(motif / "motif_events.jsonl", "")
    _json(motif / "motif_merges.json", {"merges": []})
    for workspace in ("ws3", "ws4", "ws5"):
        path = root / "workspaces" / workspace
        _json(path / "workspace_meta.json", {"workspace": workspace})
        _json(path / "domains.json", {"domains": []})
        _scope(root, workspace, "a1")
        private = path / "agents" / "a1" / "private"
        _write(private / "nodes.jsonl", json.dumps({"metadata_less_source_evidence": [{
            "eid": 7,
            "vector_locator": "emb_7.npy",
            "canonical_text_locator": "canonical_text_7.json",
            "metadata_less_source_evidence_identity": f"{workspace}-eid-7",
        }]}) + "\n")
        _npy(private / "emb_7.npy")
        _json(private / "canonical_text_7.json", {"text": "qualified legacy source"})
    empty_private = root / "workspaces" / "multi" / "agents" / "empty-private" / "private"
    _json(empty_private.parent / "identity.json", {"agent": "empty-private"})
    _storage(empty_private, total_rows=0, next_row=0)
    _write(root / "unscoped_nodes.jsonl", "residual")
    _write(root / "unscoped_embeddings.bin", b"residual-vectors")
    _write(root / "lived_use" / "arbitrary_nested_basin" / "embedding_manifest.json", "not source JSON")
    _write(root / "lived_use" / "arbitrary_nested_basin" / "malformed.npy", b"not a NumPy file")
    return root, RealRootTypedEvidenceAdapter(
        data_root_identity="synthetic-real-root", operator_identity="synthetic-operator",
        excluded_source_artifacts=(
            ExcludedSourceArtifactLocator("unscoped_nodes.jsonl", "TOP_LEVEL_UNSCOPED_NODES"),
            ExcludedSourceArtifactLocator("unscoped_embeddings.bin", "TOP_LEVEL_UNSCOPED_EMBEDDINGS"),
        ),
        excluded_alternate_roots=(ExcludedAlternateRootLocator("lived_use"),),
    )


def _capture(root: Path, adapter: RealRootTypedEvidenceAdapter):
    discovered = discover_canonical_root_layout(data_root=root)
    return adapter.capture_typed_evidence(data_root=root, discovered_census=discovered)


def test_regular_file_refusals_preserve_the_exact_path_and_shape(tmp_path: Path) -> None:
    regular = tmp_path / "typed-source.json"
    _write(regular, "synthetic")
    missing = tmp_path / "missing-source.json"
    directory = tmp_path / "directory-at-file-path"
    directory.mkdir()

    assert _regular_file(regular) == regular
    _assert_regular_file_refusal(lambda: _regular_file(missing), missing, "ABSENT")
    _assert_regular_file_refusal(lambda: _regular_file(directory), directory, "NON_FILE")


def test_regular_file_symlink_refusal_preserves_the_exact_path_and_shape(tmp_path: Path) -> None:
    target = tmp_path / "typed-source-target.json"
    link = tmp_path / "typed-source-link.json"
    _write(target, "synthetic")
    try:
        os.symlink(target, link)
    except OSError:
        pytest.skip("symlink creation is not available on this Windows host")

    _assert_regular_file_refusal(lambda: _regular_file(link), link, "SYMLINK")


def test_regular_file_context_survives_direct_helper_wrappers(tmp_path: Path) -> None:
    root, adapter = _fixture(tmp_path)
    missing = root / "workspaces" / "empty" / "workspace_meta.json"
    missing.unlink()
    directory = tmp_path / "directory-at-file-path"
    directory.mkdir()

    prepared = adapter.prepare_direct_admission_source(data_root=root)
    workspace_meta = next(
        item
        for item in prepared.description.explicit_source_manifest.entries
        if item.owner_boundary.workspace_id == "empty"
        and item.semantic_role is EvidenceSemanticRole.WORKSPACE_META
    )
    assert workspace_meta.presence_expectation is EvidencePresenceExpectation.EXPECTED_ABSENT
    assert workspace_meta.absence_reason is EvidenceAbsenceReason.METADATA_LESS_SOURCE_SHAPE
    assert workspace_meta.scope_key is None
    _assert_regular_file_refusal(
        lambda: _capture(root, adapter), missing, "ABSENT",
    )
    _assert_regular_file_refusal(
        lambda: _validate_regular_file(missing, "private nodes"), missing, "ABSENT",
    )
    _assert_regular_file_refusal(lambda: _read_json(missing), missing, "ABSENT")
    _assert_regular_file_refusal(lambda: _hash_file(directory), directory, "NON_FILE")
    _assert_regular_file_refusal(
        lambda: _file_observation(directory, "directory-at-file-path"), directory, "NON_FILE",
    )
    _assert_regular_file_refusal(lambda: _npy_header(missing), missing, "ABSENT")


def _direct_metadata_less_six_workspace_fixture(
    tmp_path: Path,
) -> tuple[Path, RealRootTypedEvidenceAdapter]:
    """The frozen six-workspace family, built only below pytest's disposable root."""

    root = tmp_path / "direct-metadata-less-six-workspace-source"
    domains = ("research", "engineering", "operations", "creative", "meta")
    for workspace_id in ("sim-ws", "ws1", "ws2", "ws3", "ws4", "ws5"):
        workspace = root / "workspaces" / workspace_id
        _json(workspace / "domains.json", {"domains": list(domains)})
        (workspace / "agents").mkdir(parents=True, exist_ok=True)

    for workspace_id in ("ws3", "ws4", "ws5"):
        _scope(root, workspace_id, "a1")
        private = root / "workspaces" / workspace_id / "agents" / "a1" / "private"
        (private / "embeddings" / "manifest.json").unlink()
        _write(
            private / "nodes.jsonl",
            json.dumps({"eid": 1, "payload": {"summary": f"{workspace_id} canonical source"}}) + "\n",
        )
        _npy(private / "emb_1.npy")
        _json(
            root / "workspaces" / workspace_id / "domains" / "research" / "motifs.json",
            {"motif": "retained owner state"},
        )

    return root, RealRootTypedEvidenceAdapter(
        data_root_identity="synthetic-metadata-less-six-workspace-root",
        operator_identity="synthetic-metadata-less-six-workspace-operator",
        direct_phase9b_namespace_bindings=_direct_phase9b_bindings(),
    )


def test_direct_metadata_less_six_workspace_family_is_explicitly_bound_and_closed(
    tmp_path: Path,
) -> None:
    root, adapter = _direct_metadata_less_six_workspace_fixture(tmp_path)
    before = _source_snapshot(root)

    prepared = adapter.prepare_direct_admission_source(data_root=root)
    census = prepared.description.expected_census
    manifest = prepared.description.explicit_source_manifest

    assert census.workspace_count == 6
    assert census.materialized_private_scope_count == 3
    assert census.materialized_shared_scope_count == 0
    assert census.total_materialized_scope_count == 3
    assert census.declared_empty_shared_scope_count == 30
    assert census.total_runtime_scope_count == 33
    assert len(prepared.source_scope_plans) == 33
    assert {item.representation_disposition for item in prepared.source_scope_plans} == {
        RootRepresentationDisposition.UNKNOWN_IDENTITY,
        RootRepresentationDisposition.NO_VECTOR,
    }

    workspace_meta = [
        item for item in manifest.entries
        if item.owner_class is SourceOwnerClass.WORKSPACE_IDENTITY_METADATA
    ]
    assert {item.owner_boundary.workspace_id for item in workspace_meta} == {
        "sim-ws", "ws1", "ws2", "ws3", "ws4", "ws5",
    }
    assert all(item.owner_boundary.boundary_kind.value == "WORKSPACE" for item in workspace_meta)
    assert all(item.canonical_locator == "workspace_meta.json" for item in workspace_meta)
    assert all(item.semantic_role is EvidenceSemanticRole.WORKSPACE_META for item in workspace_meta)
    assert all(item.presence_expectation is EvidencePresenceExpectation.EXPECTED_ABSENT for item in workspace_meta)
    assert all(item.absence_reason is EvidenceAbsenceReason.METADATA_LESS_SOURCE_SHAPE for item in workspace_meta)
    assert all(item.scope_key is None for item in workspace_meta)

    plans = {item.scope_key.canonical_key: item for item in prepared.source_scope_plans}
    for workspace_id in ("ws3", "ws4", "ws5"):
        assert plans[(workspace_id, "PRIVATE", "a1")].representation_disposition is RootRepresentationDisposition.UNKNOWN_IDENTITY
        research = plans[(workspace_id, "SHARED", "research")]
        assert research.materialization_posture is MaterializedScopePosture.DECLARED_EMPTY_SHARED
        assert research.representation_disposition is RootRepresentationDisposition.NO_VECTOR
        assert research.motif_presence is SourceArtifactPresence.PRESENT
        for domain_id in ("engineering", "operations", "creative", "meta"):
            plan = plans[(workspace_id, "SHARED", domain_id)]
            assert plan.materialization_posture is MaterializedScopePosture.DECLARED_EMPTY_SHARED
            assert plan.representation_disposition is RootRepresentationDisposition.NO_VECTOR
            assert plan.motif_presence is SourceArtifactPresence.ABSENT

    declared = {item.scope_key.canonical_key: item for item in prepared.declared_empty_shared_evidence}
    assert len(declared) == 30
    assert all(item.shared_directory_observation.presence is SourceArtifactPresence.ABSENT for item in declared.values())
    assert declared[("ws3", "SHARED", "research")].motif_observation.presence is SourceArtifactPresence.PRESENT
    research_motif = next(
        item
        for item in manifest.entries
        if item.scope_key is not None
        and item.scope_key.canonical_key == ("ws3", "SHARED", "research")
        and item.semantic_role is EvidenceSemanticRole.MOTIFS
    )
    assert research_motif.owner_class is SourceOwnerClass.MOTIF_SOURCE
    assert research_motif.owner_boundary.boundary_kind.value == "DOMAIN"
    assert research_motif.canonical_locator == "motifs.json"
    assert research_motif.presence_expectation is EvidencePresenceExpectation.EXPECTED_PRESENT
    assert {item.scope_key.canonical_key for item in prepared.unknown_identity_evidence} == {
        ("ws3", "PRIVATE", "a1"),
        ("ws4", "PRIVATE", "a1"),
        ("ws5", "PRIVATE", "a1"),
    }
    assert {item.eid for item in prepared.unknown_identity_evidence} == {1}
    assert not list(root.rglob("canonical_text_*.json"))
    assert all(
        "metadata_less_source_evidence" not in json.loads(
            (root / "workspaces" / workspace_id / "agents" / "a1" / "private" / "nodes.jsonl").read_text(
                encoding="utf-8"
            )
        )
        for workspace_id in ("ws3", "ws4", "ws5")
    )
    assert manifest.verify(data_root=root).verified_absent_entries
    assert _source_snapshot(root) == before


def test_direct_unknown_identity_manifest_absence_is_explicit_and_drift_refuses(tmp_path: Path) -> None:
    root, adapter = _direct_metadata_less_six_workspace_fixture(tmp_path)
    prepared = adapter.prepare_direct_admission_source(data_root=root)
    manifest = prepared.description.explicit_source_manifest

    absent_manifest_entries = [
        item
        for item in manifest.entries
        if item.owner_class is SourceOwnerClass.EMBEDDING_MANIFEST
        and item.semantic_role is EvidenceSemanticRole.EMBEDDING_MANIFEST
    ]
    assert {
        item.scope_key.canonical_key for item in absent_manifest_entries if item.scope_key is not None
    } == {
        ("ws3", "PRIVATE", "a1"),
        ("ws4", "PRIVATE", "a1"),
        ("ws5", "PRIVATE", "a1"),
    }
    assert all(item.presence_expectation is EvidencePresenceExpectation.EXPECTED_ABSENT for item in absent_manifest_entries)
    assert all(item.absence_reason is EvidenceAbsenceReason.METADATA_LESS_SOURCE_SHAPE for item in absent_manifest_entries)
    verification = manifest.verify(data_root=root)
    assert set(absent_manifest_entries).issubset(verification.verified_absent_entries)

    created = root / "workspaces" / "ws3" / "agents" / "a1" / "private" / "embeddings" / "manifest.json"
    _write(created, "{malformed manifest remains an unexpected changed shape")
    with pytest.raises(ExplicitSourceEvidenceDrift, match="expected-absent evidence was created: embeddings/manifest.json"):
        manifest.verify(data_root=root)
    with pytest.raises(CorrectiveFreezePacketRefused, match="requires embeddings/manifest.json to remain expected absent"):
        adapter.prepare_direct_admission_source(data_root=root)


def test_direct_unknown_identity_manifest_alignment_keeps_ordinary_missing_manifest_strict(tmp_path: Path) -> None:
    root, adapter = _fixture(tmp_path)
    ordinary_manifest = root / "workspaces" / "multi" / "agents" / "target" / "private" / "embeddings" / "manifest.json"
    ordinary_manifest.unlink()

    _assert_regular_file_refusal(
        lambda: adapter.prepare_direct_admission_source(data_root=root), ordinary_manifest, "ABSENT",
    )


def test_direct_phase9b_production_shape_refuses_missing_matching_vector(tmp_path: Path) -> None:
    root, adapter = _direct_metadata_less_six_workspace_fixture(tmp_path)
    vector = root / "workspaces" / "ws4" / "agents" / "a1" / "private" / "emb_1.npy"
    vector.unlink()

    with pytest.raises(CorrectiveFreezePacketRefused, match="non-symlink regular file"):
        adapter.prepare_direct_admission_source(data_root=root)


def test_direct_phase9b_production_shape_projects_existing_qualified_source(tmp_path: Path) -> None:
    root, adapter = _direct_metadata_less_six_workspace_fixture(tmp_path)
    before = _source_snapshot(root)
    prepared = adapter.prepare_direct_admission_source(data_root=root)
    entries = prepared.description.explicit_source_manifest.entries
    bindings = {item.scope_key: item for item in adapter.direct_phase9b_namespace_bindings}

    assert not list(root.rglob("canonical_text_*.json"))
    assert len([
        item for item in entries
        if item.scope_key in bindings and item.semantic_role is EvidenceSemanticRole.NODES
    ]) == 3
    for direct in prepared.unknown_identity_evidence:
        nodes = next(
            item for item in entries
            if item.scope_key == direct.scope_key and item.semantic_role is EvidenceSemanticRole.NODES
        )
        representation = next(
            item for item in entries
            if item.scope_key == direct.scope_key
            and item.semantic_role is EvidenceSemanticRole.LEGACY_REPRESENTATION
        )
        optional_edges = next(
            item for item in entries
            if item.scope_key == direct.scope_key
            and item.semantic_role is EvidenceSemanticRole.EDGES
        )
        binding = bindings[direct.scope_key]
        qualified = qualify_metadata_less_per_eid_legacy_source(
            data_root=root,
            scope_key=direct.scope_key,
            legacy_eid=1,
            legacy_source_namespace_id=binding.legacy_source_namespace_id,
            target_identity_namespace_id=binding.target_identity_namespace_id,
            nodes_source=nodes,
            optional_edges_source=optional_edges,
            legacy_representation_source=representation,
        )

        assert qualified.provider_identity is None
        assert qualified.model_identity is None
        assert qualified.representation_identity is MetadataLessRepresentationIdentity.UNKNOWN
        assert qualified.legacy_vector_strategy is LegacyVectorStrategy.REEMBED_REQUIRED
        assert qualified.b3b_input.legacy_vector_strategy is LegacyVectorStrategy.REEMBED_REQUIRED
        assert qualified.canonical_embedding_input.field == "summary"
        assert direct.scope_key == qualified.scope_key
        assert direct.eid == qualified.legacy_eid
        assert direct.vector_evidence == qualified.legacy_representation_source
        assert direct.canonical_text_evidence == qualified.nodes_source
        assert direct.dtype == qualified.retained_legacy_vector.array_dtype
        assert direct.shape == qualified.retained_legacy_vector.array_shape
        assert direct.metadata_less_source_evidence_identity == qualified.source_evidence_identity
    assert _source_snapshot(root) == before


def test_direct_phase9b_production_shape_refuses_malformed_vector(tmp_path: Path) -> None:
    root, adapter = _direct_metadata_less_six_workspace_fixture(tmp_path)
    vector = root / "workspaces" / "ws3" / "agents" / "a1" / "private" / "emb_1.npy"
    _write(vector, b"not-a-valid-npy")

    with pytest.raises(CorrectiveFreezePacketRefused, match="structurally valid NPY array"):
        adapter.prepare_direct_admission_source(data_root=root)


def test_direct_phase9b_production_shape_refuses_eid_vector_mismatch(tmp_path: Path) -> None:
    root, adapter = _direct_metadata_less_six_workspace_fixture(tmp_path)
    private = root / "workspaces" / "ws3" / "agents" / "a1" / "private"
    (private / "emb_1.npy").replace(private / "emb_2.npy")

    with pytest.raises(CorrectiveFreezePacketRefused, match="non-symlink regular file"):
        adapter.prepare_direct_admission_source(data_root=root)


def test_direct_phase9b_production_shape_refuses_ambiguous_canonical_eid(tmp_path: Path) -> None:
    root, adapter = _direct_metadata_less_six_workspace_fixture(tmp_path)
    nodes = root / "workspaces" / "ws3" / "agents" / "a1" / "private" / "nodes.jsonl"
    _write(
        nodes,
        "\n".join((
            json.dumps({"eid": 1, "payload": {"summary": "first"}}),
            json.dumps({"eid": 1, "payload": {"summary": "second"}}),
        )) + "\n",
    )

    with pytest.raises(CorrectiveFreezePacketRefused, match="exactly one unique canonical EID"):
        adapter.prepare_direct_admission_source(data_root=root)


def test_direct_phase9b_production_shape_refuses_missing_canonical_input(tmp_path: Path) -> None:
    root, adapter = _direct_metadata_less_six_workspace_fixture(tmp_path)
    nodes = root / "workspaces" / "ws3" / "agents" / "a1" / "private" / "nodes.jsonl"
    _write(nodes, json.dumps({"eid": 1, "payload": {"opaque": "not canonical input"}}) + "\n")

    with pytest.raises(CorrectiveFreezePacketRefused, match="canonical embedding input is unavailable"):
        adapter.prepare_direct_admission_source(data_root=root)


def test_direct_metadata_less_workspace_manifest_refuses_created_metadata_drift(tmp_path: Path) -> None:
    root, adapter = _direct_metadata_less_six_workspace_fixture(tmp_path)
    manifest = adapter.prepare_direct_admission_source(data_root=root).description.explicit_source_manifest
    _json(root / "workspaces" / "sim-ws" / "workspace_meta.json", {"workspace": "sim-ws", **_target_lock()})

    with pytest.raises(ExplicitSourceEvidenceDrift, match="expected-absent evidence was created: workspace_meta.json"):
        manifest.verify(data_root=root)


def test_direct_metadata_less_workspace_keeps_unqualified_memory_graph_refused(tmp_path: Path) -> None:
    root, adapter = _direct_metadata_less_six_workspace_fixture(tmp_path)
    _scope(root, "sim-ws", "new-agent")

    with pytest.raises(CorrectiveFreezePacketRefused, match="lacks the frozen workspace representation lock"):
        adapter.prepare_direct_admission_source(data_root=root)


def test_direct_metadata_less_workspace_keeps_missing_metadata_strict_in_packet_capture(tmp_path: Path) -> None:
    root, adapter = _direct_metadata_less_six_workspace_fixture(tmp_path)
    missing = root / "workspaces" / "sim-ws" / "workspace_meta.json"

    _assert_regular_file_refusal(lambda: _capture(root, adapter), missing, "ABSENT")


def test_declared_empty_domain_owner_directory_still_refuses_unsafe_children(tmp_path: Path) -> None:
    root, adapter = _direct_metadata_less_six_workspace_fixture(tmp_path)
    research = root / "workspaces" / "ws3" / "domains" / "research"
    motif = research / "motifs.json"
    motif.unlink()
    motif.mkdir()

    _assert_regular_file_refusal(
        lambda: adapter.prepare_direct_admission_source(data_root=root), motif, "NON_FILE",
    )

    root, adapter = _direct_metadata_less_six_workspace_fixture(tmp_path / "shared-not-directory")
    shared = root / "workspaces" / "ws3" / "domains" / "research" / "shared"
    _write(shared, "not a directory")
    with pytest.raises(RootBlocker5BindingRefused, match="shared scope must be a non-symlink directory"):
        adapter.prepare_direct_admission_source(data_root=root)

    root, adapter = _direct_metadata_less_six_workspace_fixture(tmp_path / "undeclared-domain")
    _json(root / "workspaces" / "sim-ws" / "domains" / "not-declared" / "motifs.json", {"motif": "refuse"})
    with pytest.raises(CorrectiveFreezePacketRefused, match="materialized domain lacks a direct declaration"):
        adapter.prepare_direct_admission_source(data_root=root)


def _orchard_empty_shared_fixture(tmp_path: Path) -> tuple[Path, RealRootTypedEvidenceAdapter]:
    root, adapter = _fixture(tmp_path)
    orchard = root / "workspaces" / "orchard"
    domains = ("creative", "engineering", "personal", "research")
    _json(orchard / "workspace_meta.json", {"workspace": "orchard", **_target_lock()})
    _json(orchard / "domains.json", {"domains": list(domains)})
    empty_private = orchard / "agents" / "empty-private" / "private"
    _json(empty_private.parent / "identity.json", {"agent": "empty-private"})
    _storage(empty_private, total_rows=0, next_row=0)
    for domain_id in domains:
        (orchard / "domains" / domain_id / "shared").mkdir(parents=True, exist_ok=True)
    return root, adapter


def _real_named_root_fixture(tmp_path: Path) -> Path:
    """Return the smallest root using the qualified production child names."""

    root = tmp_path / "real-named-production-shaped-source"
    workspace = root / "workspaces" / "empty"
    _json(workspace / "workspace_meta.json", {"workspace": "empty", **_target_lock()})
    _json(workspace / "domains.json", {"domains": []})
    _write(root / "nodes.jsonl", "retained unscoped nodes")
    _write(root / "emb_1.npy", b"retained unscoped representation")
    _write(root / "lived_use" / "opaque-basin" / "must-not-be-read.bin", b"opaque alternate data")
    return root


def test_real_direct_admission_factory_binds_only_qualified_root_exclusions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _real_named_root_fixture(tmp_path)
    generic = RealRootTypedEvidenceAdapter(
        data_root_identity="generic-root",
        operator_identity="generic-operator",
    )
    assert generic.excluded_source_artifacts == ()
    assert generic.excluded_alternate_roots == ()

    adapter = build_real_direct_admission_source_adapter(
        data_root_identity="qualified-real-root",
        operator_identity="qualified-real-operator",
    )

    assert [(item.canonical_locator, item.source_role) for item in adapter.excluded_source_artifacts] == [
        ("nodes.jsonl", "TOP_LEVEL_UNSCOPED_NODES"),
        ("emb_1.npy", "TOP_LEVEL_UNSCOPED_EMBEDDINGS"),
    ]
    assert tuple(item.canonical_locator for item in adapter.excluded_alternate_roots) == ("lived_use",)

    lived_use = root / "lived_use"
    original_iterdir = Path.iterdir
    original_open = Path.open

    def _no_lived_use_descendant_iteration(path: Path):
        if path == lived_use:
            raise AssertionError("lived_use descendants must not be enumerated")
        return original_iterdir(path)

    def _no_lived_use_descendant_read(path: Path, *args: object, **kwargs: object):
        if lived_use in path.parents:
            raise AssertionError("lived_use descendants must not be read or hashed")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "iterdir", _no_lived_use_descendant_iteration)
    monkeypatch.setattr(Path, "open", _no_lived_use_descendant_read)
    prepared = adapter.prepare_direct_admission_source(data_root=root)
    assert prepared.description.expected_census.workspace_count == 1

    for omitted_locator in ("nodes.jsonl", "emb_1.npy"):
        omitted = replace(
            adapter,
            excluded_source_artifacts=tuple(
                item for item in adapter.excluded_source_artifacts
                if item.canonical_locator != omitted_locator
            ),
        )
        with pytest.raises(CorrectiveFreezePacketRefused, match="unclassified durable root artifact"):
            omitted.prepare_direct_admission_source(data_root=root)

    without_lived_use = replace(adapter, excluded_alternate_roots=())
    with pytest.raises(CorrectiveFreezePacketRefused, match="unclassified durable root artifact"):
        without_lived_use.prepare_direct_admission_source(data_root=root)

    _write(root / "unexpected_fourth_root_artifact", "must refuse")
    with pytest.raises(CorrectiveFreezePacketRefused, match="unclassified durable root artifact"):
        adapter.prepare_direct_admission_source(data_root=root)


def _source_snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): _digest(path.read_bytes())
        for path in sorted(root.rglob("*")) if path.is_file()
    }


def test_discovers_direct_declarations_and_builds_all_source_plans(tmp_path: Path) -> None:
    root, adapter = _fixture(tmp_path)
    typed = _capture(root, adapter)

    assert typed.discovered_census.workspace_ids == ("empty", "hash", "multi", "ws3", "ws4", "ws5")
    assert typed.description.expected_census.workspace_count == 6
    assert typed.description.expected_census.total_materialized_scope_count == 8
    assert typed.description.expected_census.declared_empty_shared_scope_count == 3
    assert typed.description.expected_census.empty_private_identity_scope_count == 1
    assert len(typed.source_scope_plans) == 11
    assert {plan.representation_disposition for plan in typed.source_scope_plans} == {
        RootRepresentationDisposition.TARGET_COMPATIBLE,
        RootRepresentationDisposition.REEMBED_REQUIRED,
        RootRepresentationDisposition.UNKNOWN_IDENTITY,
        RootRepresentationDisposition.NO_VECTOR,
    }


def test_empty_private_and_declared_empty_facts_are_explicit(tmp_path: Path) -> None:
    root, adapter = _fixture(tmp_path)
    typed = _capture(root, adapter)

    empty = typed.empty_private_evidence[0]
    assert empty.scope_key.agent_id == "empty-private"
    assert empty.embedding_manifest_total_rows == empty.embedding_manifest_next_row == 0
    assert empty.memory_events_observation.presence is SourceArtifactPresence.ABSENT
    assert {item.domain_id for item in typed.declared_empty_shared_evidence} == {"declared", "legacy", "missing"}


def test_unknown_metadata_less_reads_only_header_identity_and_hash(tmp_path: Path) -> None:
    root, adapter = _fixture(tmp_path)
    typed = _capture(root, adapter)

    unknown = typed.unknown_identity_evidence
    assert len(unknown) == 3
    assert {item.scope_key.workspace_id for item in unknown} == {"ws3", "ws4", "ws5"}
    assert {item.eid for item in unknown} == {7}
    assert {item.dtype for item in unknown} == {"float32"}
    assert {item.shape for item in unknown} == {(384,)}


def test_target_legacy_hash_and_unknown_classification_require_persisted_markers(tmp_path: Path) -> None:
    root, adapter = _fixture(tmp_path)
    typed = _capture(root, adapter)
    plans = {plan.scope_key.canonical_key: plan for plan in typed.source_scope_plans}

    assert plans[("multi", "PRIVATE", "target")].representation_disposition is RootRepresentationDisposition.TARGET_COMPATIBLE
    assert plans[("hash", "PRIVATE", "rehash")].representation_disposition is RootRepresentationDisposition.REEMBED_REQUIRED
    assert plans[("ws3", "PRIVATE", "a1")].representation_disposition is RootRepresentationDisposition.UNKNOWN_IDENTITY


def test_dimension_alone_never_infers_target_compatibility(tmp_path: Path) -> None:
    root, adapter = _fixture(tmp_path)
    _json(root / "workspaces" / "multi" / "workspace_meta.json", {"workspace": "multi"})

    with pytest.raises(CorrectiveFreezePacketRefused, match="lacks the frozen workspace representation lock"):
        _capture(root, adapter)


@pytest.mark.parametrize("lock", [
    {"embed_provider": "st", "embed_dim": 384},
    {"embed_provider": "", "embed_model": "BAAI/bge-small-en-v1.5", "embed_dim": 384},
    {"embed_provider": "st", "embed_model": "BAAI/bge-small-en-v1.5", "embed_dim": 0},
])
def test_partial_or_empty_workspace_representation_lock_refuses(tmp_path: Path, lock: dict[str, object]) -> None:
    root, adapter = _fixture(tmp_path)
    _json(root / "workspaces" / "multi" / "workspace_meta.json", {"workspace": "multi", **lock})

    with pytest.raises(CorrectiveFreezePacketRefused, match="workspace representation lock"):
        _capture(root, adapter)


def test_other_explicit_workspace_representation_lock_refuses(tmp_path: Path) -> None:
    root, adapter = _fixture(tmp_path)
    _json(root / "workspaces" / "multi" / "workspace_meta.json", {
        "workspace": "multi", "embed_provider": "other", "embed_model": "other:384", "embed_dim": 384,
    })

    with pytest.raises(CorrectiveFreezePacketRefused, match="frozen census"):
        _capture(root, adapter)


def test_storage_and_node_stamps_only_detect_lock_contradictions(tmp_path: Path) -> None:
    root, adapter = _fixture(tmp_path)
    private = root / "workspaces" / "multi" / "agents" / "target" / "private"
    _storage(private, dimension=768)
    with pytest.raises(CorrectiveFreezePacketRefused, match="storage manifest dimension"):
        _capture(root, adapter)

    root, adapter = _fixture(tmp_path)
    private = root / "workspaces" / "multi" / "agents" / "target" / "private"
    _write(private / "nodes.jsonl", json.dumps({
        "embedding_provider": "st", "embedding_model": "wrong", "embedding_dim": 384,
    }) + "\n")
    with pytest.raises(CorrectiveFreezePacketRefused, match="node embedding stamp"):
        _capture(root, adapter)


def test_empty_scope_with_target_lock_remains_no_vector(tmp_path: Path) -> None:
    root, adapter = _fixture(tmp_path)
    typed = _capture(root, adapter)
    empty = next(plan for plan in typed.source_scope_plans if plan.scope_key.agent_id == "empty-private")

    assert empty.representation_disposition is RootRepresentationDisposition.NO_VECTOR
    assert empty.materialization_posture is MaterializedScopePosture.EMPTY_PRIVATE


def test_production_owner_observations_and_geometry_are_bound_to_the_source(tmp_path: Path) -> None:
    root, adapter = _fixture(tmp_path)
    typed = _capture(root, adapter)

    assert typed.description.explicit_source_manifest.entries
    assert {item.owner_kind.value for item in typed.description.external_owner_observations} >= {
        "IDENTITY", "ROLE", "CHARACTER", "BRIDGE", "CONFLICT", "PROPOSAL_WORKFLOW",
    }
    assert typed.geometry_disposition_plan.entries
    assert all(
        entry.source_observation_digest
        for entry in typed.geometry_disposition_plan.entries
    )


def test_roles_character_seed_and_retained_side_stores_never_become_core_memory(tmp_path: Path) -> None:
    root, adapter = _fixture(tmp_path)
    typed = _capture(root, adapter)
    external = typed.description.external_owner_observations
    manifest = typed.description.explicit_source_manifest.entries

    assert {(item.owner_kind.value, item.observation_key) for item in external} >= {
        ("ROLE", "agent:target:roles.json"),
        ("CHARACTER", "agent:target:character_state.json"),
        ("CHARACTER", "seed:seed-a"),
    }
    assert all(item.scope_key is None for item in manifest if item.canonical_locator in {
        "roles.json", "character_state.json", "seeds/seed-a/seed.json",
    })
    retained_locators = {item.canonical_locator for item in manifest}
    assert "feedback_events.jsonl" not in retained_locators
    assert "memory_archive/documents.jsonl" not in retained_locators
    assert "index/memory_index.sqlite" not in retained_locators


def test_synthetic_owner_registry_and_unknown_durable_artifacts_refuse(tmp_path: Path) -> None:
    root, adapter = _fixture(tmp_path)
    _json(root / "workspaces" / "multi" / "external_owner_observations.json", {"observations": []})

    with pytest.raises(CorrectiveFreezePacketRefused, match="unclassified durable workspace owner"):
        _capture(root, adapter)


def test_unclassified_durable_workspace_owner_refuses(tmp_path: Path) -> None:
    root, adapter = _fixture(tmp_path)
    _json(root / "workspaces" / "multi" / "unclassified_owner.json", {"owner": "refuse"})

    with pytest.raises(CorrectiveFreezePacketRefused, match="unclassified durable workspace owner"):
        _capture(root, adapter)


def test_excluded_artifact_expectations_and_observations_are_typed(tmp_path: Path) -> None:
    root, adapter = _fixture(tmp_path)
    expectations = adapter.excluded_artifact_expectations(data_root=root)
    observed = adapter.capture_excluded_source_artifacts(data_root=root)

    assert [item.canonical_locator for item in expectations] == [item.canonical_locator for item in observed]
    assert all(item.sha256 == expected.predecessor_sha256 for item, expected in zip(observed, expectations))


def test_alternate_root_is_presence_only_and_never_enters_source_evidence(tmp_path: Path) -> None:
    root, adapter = _fixture(tmp_path)
    typed = _capture(root, adapter)
    alternate = adapter.capture_excluded_alternate_roots(data_root=root)

    assert alternate[0].canonical_locator == "lived_use"
    assert alternate[0].exclusion_role is ExcludedAlternateRootRole.ALTERNATE_SELECTED_ROOT
    assert all("lived_use" not in entry.canonical_locator for entry in typed.description.explicit_source_manifest.entries)
    assert all("lived_use" not in plan.scope_key.canonical_key for plan in typed.source_scope_plans)


def test_adapter_leaves_disposable_source_tree_exactly_unchanged(tmp_path: Path) -> None:
    root, adapter = _fixture(tmp_path)
    before = _source_snapshot(root)
    _capture(root, adapter)

    assert _source_snapshot(root) == before
    assert not list(root.rglob("*.sqlite-wal"))
    assert not list(root.rglob("*.db"))


def test_direct_preparation_reuses_source_grammar_and_allows_known_empty_shared_residue(
    tmp_path: Path,
) -> None:
    root, adapter = _fixture(tmp_path)
    shared = root / "workspaces" / "multi" / "domains" / "motif" / "shared"
    _storage(shared, total_rows=7, next_row=7)
    _write(shared / "memory_events.jsonl", "retained event")
    _write(shared / "logs" / "retained.jsonl", "retained log")
    _write(shared / "trajectories" / "retained.jsonl", "retained trajectory")
    before = _source_snapshot(root)

    prepared = adapter.prepare_direct_admission_source(data_root=root)

    assert isinstance(prepared, DirectAdmissionSourcePreparation)
    assert not isinstance(prepared, CorrectiveFreezeTypedEvidence)
    assert prepared.description.expected_census.workspace_count == 6
    assert {plan.representation_disposition for plan in prepared.source_scope_plans} == {
        RootRepresentationDisposition.TARGET_COMPATIBLE,
        RootRepresentationDisposition.REEMBED_REQUIRED,
        RootRepresentationDisposition.UNKNOWN_IDENTITY,
        RootRepresentationDisposition.NO_VECTOR,
    }
    motif = next(plan for plan in prepared.source_scope_plans if plan.scope_key.domain_id == "motif")
    assert motif.materialization_posture is MaterializedScopePosture.EMPTY_SHARED_WITH_MOTIF
    assert motif.representation_disposition is RootRepresentationDisposition.TARGET_COMPATIBLE
    motif_entries = [
        item for item in prepared.description.explicit_source_manifest.entries
        if item.scope_key == motif.scope_key
    ]
    assert {item.canonical_locator for item in motif_entries} == {"nodes.jsonl", "motifs.json"}
    assert all("lived_use" not in item.canonical_locator for item in motif_entries)
    assert _source_snapshot(root) == before

    with pytest.raises(CorrectiveFreezePacketRefused, match="unclassified durable artifact"):
        _capture(root, adapter)

    _write(shared / "unknown_canonical_source.json", "refuse")
    with pytest.raises(CorrectiveFreezePacketRefused, match="unclassified durable artifact"):
        adapter.prepare_direct_admission_source(data_root=root)


def test_direct_preparation_recognizes_only_top_level_native_control_plane_root(
    tmp_path: Path,
) -> None:
    without_parent = tmp_path / "without-substrate"
    with_parent = tmp_path / "with-substrate"
    without_parent.mkdir()
    with_parent.mkdir()
    without_substrate, without_adapter = _fixture(without_parent)
    with_substrate, with_adapter = _fixture(with_parent)
    _write(with_substrate / "substrate" / "cores" / "opaque-control-plane.db", b"not-source")
    _write(with_substrate / "substrate" / "cores" / "opaque-control-plane.db-wal", b"not-source")
    _write(with_substrate / "substrate" / "other" / "unrelated.json", "not source JSON")

    without = without_adapter.prepare_direct_admission_source(data_root=without_substrate)
    with_control_plane = with_adapter.prepare_direct_admission_source(data_root=with_substrate)

    # Direct admission recognizes the native control-plane directory but never
    # descends into it or lets its descendants enter source-derived facts.
    assert with_control_plane.discovered_census == without.discovered_census
    assert with_control_plane.source_scope_plans == without.source_scope_plans
    assert with_control_plane.description.explicit_source_manifest == without.description.explicit_source_manifest
    assert with_control_plane.description.external_owner_observations == without.description.external_owner_observations
    assert with_control_plane.description.external_owner_observation_digest == without.description.external_owner_observation_digest
    assert with_control_plane.geometry_disposition_plan == without.geometry_disposition_plan

    with pytest.raises(CorrectiveFreezePacketRefused, match="unclassified durable root artifact"):
        _capture(with_substrate, with_adapter)

    _json(with_substrate / "mystery-control-plane" / "state.json", {"must": "refuse"})
    with pytest.raises(CorrectiveFreezePacketRefused, match="unclassified durable root artifact"):
        with_adapter.prepare_direct_admission_source(data_root=with_substrate)


def test_direct_preparation_refuses_non_directory_native_control_plane_root(tmp_path: Path) -> None:
    root, adapter = _fixture(tmp_path)
    _write(root / "substrate", "not a directory")

    with pytest.raises(CorrectiveFreezePacketRefused, match="native control plane root must be a real top-level directory"):
        adapter.prepare_direct_admission_source(data_root=root)


def test_direct_preparation_refuses_linked_native_control_plane_root(tmp_path: Path) -> None:
    root, adapter = _fixture(tmp_path)
    target = tmp_path / "native-control-plane-target"
    target.mkdir()
    try:
        os.symlink(target, root / "substrate", target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation is not available on this Windows host")

    with pytest.raises(CorrectiveFreezePacketRefused, match="native control plane root must be a real top-level directory"):
        adapter.prepare_direct_admission_source(data_root=root)


def test_direct_preparation_admits_physical_empty_shared_scopes_without_motif_as_runtime_members(
    tmp_path: Path,
) -> None:
    root, adapter = _orchard_empty_shared_fixture(tmp_path / "unknown-child")
    before = _source_snapshot(root)

    prepared = adapter.prepare_direct_admission_source(data_root=root)

    expected = {
        ("orchard", "SHARED", domain_id)
        for domain_id in ("creative", "engineering", "personal", "research")
    }
    plans = {
        item.scope_key.canonical_key: item
        for item in prepared.source_scope_plans
        if item.scope_key.workspace_id == "orchard" and item.scope_key.scope_kind.value == "SHARED"
    }
    workspace = next(item for item in prepared.description.workspace_plans if item.workspace_id == "orchard")
    assert set(plans) == expected
    assert len(workspace.private_materialized_scopes) == 1
    assert len(workspace.shared_materialized_scopes) == 4
    assert len(workspace.materialized_scopes) == len(workspace.runtime_scopes) == 5
    assert all(item.materialization_posture is MaterializedScopePosture.EMPTY_SHARED_WITHOUT_MOTIF for item in plans.values())
    assert all(item.representation_disposition is RootRepresentationDisposition.NO_VECTOR for item in plans.values())
    assert all(item.motif_presence is SourceArtifactPresence.ABSENT for item in plans.values())
    assert {item.scope_key.canonical_key for item in workspace.materialized_scopes} >= expected
    assert {item.scope_key.canonical_key for item in workspace.runtime_scopes} >= expected
    assert workspace.no_memory_scope is False
    private = workspace.private_materialized_scopes[0]
    assert private.materialization_posture is MaterializedScopePosture.EMPTY_PRIVATE
    assert private.representation_disposition is RootRepresentationDisposition.NO_VECTOR
    with_motif = next(item for item in prepared.source_scope_plans if item.scope_key.canonical_key == ("multi", "SHARED", "motif"))
    declared_empty = next(item for item in prepared.source_scope_plans if item.scope_key.canonical_key == ("multi", "SHARED", "missing"))
    assert with_motif.materialization_posture is MaterializedScopePosture.EMPTY_SHARED_WITH_MOTIF
    assert with_motif.representation_disposition is RootRepresentationDisposition.TARGET_COMPATIBLE
    assert declared_empty.materialization_posture is MaterializedScopePosture.DECLARED_EMPTY_SHARED
    assert declared_empty.representation_disposition is RootRepresentationDisposition.NO_VECTOR
    for scope_key in (item.scope_key for item in plans.values()):
        entries = [
            item for item in prepared.description.explicit_source_manifest.entries
            if item.scope_key == scope_key
        ]
        assert {item.canonical_locator for item in entries} == {"nodes.jsonl", "motifs.json"}
        assert next(item for item in entries if item.canonical_locator == "motifs.json").presence_expectation.value == "EXPECTED_ABSENT"
    assert _source_snapshot(root) == before

    with pytest.raises(CorrectiveFreezePacketRefused, match="non-symlink regular file"):
        _capture(root, adapter)


def test_direct_empty_shared_without_motif_refuses_unknown_children_and_nonregular_motif_paths(
    tmp_path: Path,
) -> None:
    root, adapter = _orchard_empty_shared_fixture(tmp_path)
    shared = root / "workspaces" / "orchard" / "domains" / "creative" / "shared"
    unknown = shared / "unknown.json"
    _write(unknown, "refuse")
    with pytest.raises(CorrectiveFreezePacketRefused, match="unclassified durable artifact"):
        adapter.prepare_direct_admission_source(data_root=root)

    unknown.unlink()
    motifs = root / "workspaces" / "orchard" / "domains" / "creative" / "motifs.json"
    motifs.mkdir()
    with pytest.raises(CorrectiveFreezePacketRefused, match="non-symlink regular file"):
        adapter.prepare_direct_admission_source(data_root=root)

    motifs.rmdir()
    target = tmp_path / "motif-target.json"
    _write(target, "synthetic")
    motifs = root / "workspaces" / "orchard" / "domains" / "creative" / "motifs.json"
    try:
        os.symlink(target, motifs)
    except OSError:
        pytest.skip("symlink creation is not available on this Windows host")
    with pytest.raises(CorrectiveFreezePacketRefused, match="non-symlink regular file"):
        adapter.prepare_direct_admission_source(data_root=root)


@pytest.mark.parametrize(("total_rows", "next_row"), ((0, 0), (1, 1)))
def test_direct_empty_private_keeps_known_residue_outside_canonical_memory(
    tmp_path: Path,
    total_rows: int,
    next_row: int,
) -> None:
    root, adapter = _fixture(tmp_path)
    private = root / "workspaces" / "multi" / "agents" / "empty-private" / "private"
    _storage(private, total_rows=total_rows, next_row=next_row)
    if total_rows:
        _write(private / "embeddings" / "shard_0.npy", b"historical orphan vector")
    _write(private / "memory_events.jsonl", "historical retained audit event")
    _write(private / "edges.jsonl", "historical retained edge residue")
    _write(private / "logs" / "retained.jsonl", "retained log")
    _write(private / "trajectories" / "retained.jsonl", "retained trajectory")
    _write(private / "checkpoints" / "checkpoint.json", "retained checkpoint")
    _write(private / "trajectories.jsonl", "retained legacy trajectory")
    before = _source_snapshot(root)

    prepared = adapter.prepare_direct_admission_source(data_root=root)

    empty = next(item for item in prepared.empty_private_evidence if item.scope_key.agent_id == "empty-private")
    source_plan = next(item for item in prepared.source_scope_plans if item.scope_key.agent_id == "empty-private")
    workspace = next(item for item in prepared.description.workspace_plans if item.workspace_id == "multi")
    manifest_entries = [
        item for item in prepared.description.explicit_source_manifest.entries
        if item.scope_key == source_plan.scope_key
    ]
    assert empty.embedding_manifest_total_rows == total_rows
    assert empty.embedding_manifest_next_row == next_row
    assert empty.memory_events_observation.presence is SourceArtifactPresence.PRESENT
    assert empty.memory_events_observation.byte_length > 0
    assert source_plan.materialization_posture is MaterializedScopePosture.EMPTY_PRIVATE
    assert source_plan.representation_disposition is RootRepresentationDisposition.NO_VECTOR
    assert [item.agent_id for item in workspace.identity_only_agents] == ["empty-private"]
    assert [(item.canonical_locator, item.presence_expectation.value) for item in manifest_entries] == [
        ("embeddings/manifest.json", "EXPECTED_PRESENT"),
        ("nodes.jsonl", "EXPECTED_ABSENT"),
    ]
    assert _source_snapshot(root) == before

    _write(private / "unknown_private_artifact.json", "must refuse")
    with pytest.raises(CorrectiveFreezePacketRefused, match="unclassified durable artifact"):
        adapter.prepare_direct_admission_source(data_root=root)


def test_direct_empty_private_residue_does_not_relax_compatibility_capture(tmp_path: Path) -> None:
    root, adapter = _fixture(tmp_path)
    private = root / "workspaces" / "multi" / "agents" / "empty-private" / "private"
    _storage(private, total_rows=1, next_row=1)
    _write(private / "embeddings" / "shard_0.npy", b"historical orphan vector")

    prepared = adapter.prepare_direct_admission_source(data_root=root)

    assert next(
        item for item in prepared.source_scope_plans if item.scope_key.agent_id == "empty-private"
    ).materialization_posture is MaterializedScopePosture.EMPTY_PRIVATE
    with pytest.raises(CorrectiveFreezePacketRefused, match="must prove zero rows and next row"):
        _capture(root, adapter)


def test_direct_preparation_feeds_writer_callback_and_root_envelope_without_packet(
    tmp_path: Path,
) -> None:
    root = tmp_path / "direct-preparation-root"
    workspace = root / "workspaces" / "empty"
    _json(workspace / "workspace_meta.json", {"workspace": "empty", **_target_lock()})
    _json(workspace / "domains.json", {"domains": []})
    adapter = RealRootTypedEvidenceAdapter(
        data_root_identity="direct-preparation-synthetic-root",
        operator_identity="direct-preparation-synthetic-operator",
    )
    before = _source_snapshot(root)
    observations = tuple(
        WriterProcessObservation(item, "SYNTHETIC", WriterObservationResult.ABSENT)
        for item in RootWriterClass
    )
    listener = ListenerObservation(
        "synthetic-listener", "SYNTHETIC", ListenerObservationResult.ABSENT,
    )
    prepared_box: dict[str, DirectAdmissionSourcePreparation] = {}

    def _during_capture(_stability: object) -> None:
        prepared_box["value"] = adapter.prepare_direct_admission_source(data_root=root)

    captured = capture_root_writer_freeze_evidence(
        data_root=root,
        data_root_identity=adapter.data_root_identity,
        writer_freeze_operation_identity="direct-preparation-freeze",
        operator_identity=adapter.operator_identity,
        covered_writer_classes=observations,
        listener_observation=listener,
        external_owner_observation_digest=None,
        expected_root_admission_description_contract="ROOT_ADMISSION_DESCRIPTION_V1",
        invalidation_rule_version="ROOT_WRITER_FREEZE_INVALIDATION_V1",
        minimum_delta_seconds=60,
        clock_ns=iter((2_000_000_000_000_000_000, 2_000_000_061_000_000_000, 2_000_000_062_000_000_000)).__next__,
        external_owner_observation_digest_supplier=lambda: prepared_box[
            "value"
        ].description.external_owner_observation_digest,
        during_capture=_during_capture,
        job_observer=lambda **_kwargs: RootJobObservation(0, "SYNTHETIC"),
    )
    prepared = prepared_box["value"]

    assert _source_snapshot(root) == before
    assert not isinstance(prepared, CorrectiveFreezeTypedEvidence)
    assert captured.payload.external_owner_observation_digest == prepared.description.external_owner_observation_digest
    assert captured.witness.writer_evidence_digest == captured.payload.digest

    core_path = root / "substrate" / "cores" / "direct-preparation.db"
    core_path.parent.mkdir(parents=True)
    qualified = open_temporary_test_connection(core_path)
    try:
        connection = qualified.connection
        metadata = create_schema(connection)
        profile_identity = generate_native_id()
        profile_scope = generate_native_id()
        profile_idempotency = generate_native_id()
        connection.execute(
            "INSERT INTO identity_namespaces VALUES (?,?,0)",
            (native_id_to_bytes(profile_identity), "direct-preparation-profile"),
        )
        connection.execute(
            "INSERT INTO semantic_scopes VALUES (?,?,0)",
            (native_id_to_bytes(profile_scope), "direct-preparation-profile-scope"),
        )
        connection.execute(
            "INSERT INTO idempotency_namespaces VALUES (?,?)",
            (native_id_to_bytes(profile_idempotency), "direct-preparation-profile-operations"),
        )
        NativeObjectService(connection).create_object(
            idempotency_namespace_id=profile_idempotency,
            idempotency_key="direct-preparation-profile",
            state=ObjectState(
                profile_identity,
                profile_scope,
                ROOT_NATIVE_PROFILE_GENERATION_KIND,
                "EXISTS",
                "ACTIVE",
                True,
                "QUALIFIED",
                authority_category="EVIDENCE",
                payload=root_profile_generation_payload(1),
                payload_format="JSON",
            ),
        )
        root_profile = current_root_profile_generation(connection)
        profile = QualifiedDeploymentProfile(
            compression_enabled=False,
            deep_memory_enabled=False,
            representation_provider=prepared.description.target_representation_lane.provider,
            representation_model=prepared.description.target_representation_lane.model,
            representation_dimension=prepared.description.target_representation_lane.dimension,
            admitted_scope_plan_digest=root_runtime_scope_plan_digest(
                (), prepared.description.target_representation_lane,
            ),
            external_owner_digest=prepared.description.external_owner_observation_digest,
        )
        recheck = RootWriterFreezeRecheck(
            covered_writer_classes=observations,
            listener_observation=listener,
            job_observation=RootJobObservation(0, "SYNTHETIC"),
            external_owner_observation_digest=prepared.description.external_owner_observation_digest,
        )
        envelope = build_real_root_v2_admission_envelope(
            data_root=root,
            description=prepared.description,
            writer_freeze=captured.witness,
            geometry_disposition_plan=prepared.geometry_disposition_plan,
            effective_profile=profile,
            native_staging_core_id=UUID(bytes=metadata.core_id),
            root_profile=root_profile,
            runtime_scopes=(),
            runtime_scope_plans=(),
            connection=connection,
            writer_freeze_evidence=captured.payload,
            writer_freeze_recheck=recheck,
        )
    finally:
        qualified.close()

    assert envelope.description is prepared.description
    assert envelope.writer_freeze == captured.witness
    assert envelope.discovered_census == prepared.discovered_census
    assert not (root / "corrective-packet").exists()


def test_packet_round_trip_uses_actual_adapter_then_reloads_without_source(tmp_path: Path) -> None:
    root, adapter = _fixture(tmp_path)
    before = _source_snapshot(root)
    predecessor = snapshot_root_workspaces(data_root=root)
    lineage = PredecessorFreezeLineage(
        predecessor_operation_identity="synthetic-predecessor",
        predecessor_payload_digest=_digest("previous-payload"),
        predecessor_witness_digest=_digest("previous-witness"),
        predecessor_tree=FrozenWorkspaceTreeTriple(
            predecessor.tree_digest, predecessor.file_count, predecessor.maximum_mtime_ns,
        ),
        successor_operation_identity="synthetic-successor", operator_identity="synthetic-operator",
        capture_head="synthetic-head",
    )
    observations = CorrectiveCaptureObservations(
        covered_writer_classes=tuple(
            WriterProcessObservation(item, "SYNTHETIC", WriterObservationResult.ABSENT)
            for item in RootWriterClass
        ),
        listener_observation=ListenerObservation("synthetic-listener", "SYNTHETIC", ListenerObservationResult.ABSENT),
        job_observer=lambda **_kwargs: RootJobObservation(0, "SYNTHETIC"),
        clock_ns=iter((2_000_000_000_000_000_000, 2_000_000_061_000_000_000, 2_000_000_062_000_000_000)).__next__,
        snapshotter=snapshot_root_workspaces,
    )
    packet = capture_corrective_freeze_packet(
        data_root=root, packet_directory=tmp_path / "packet", data_root_identity="synthetic-real-root",
        lineage=lineage, observations=observations, source_adapter=adapter,
        excluded_artifacts=adapter.excluded_artifact_expectations(data_root=root),
        excluded_alternate_roots=adapter.excluded_alternate_root_expectations(data_root=root),
        expected_root_admission_description_contract="ROOT_ADMISSION_DESCRIPTION_V1",
        invalidation_rule_version="ROOT_WRITER_FREEZE_INVALIDATION_V1",
    )

    assert _source_snapshot(root) == before
    assert packet.typed_evidence.description.expected_census.total_runtime_scope_count == 11
    assert packet.excluded_alternate_roots == adapter.capture_excluded_alternate_roots(data_root=root)
    shutil.rmtree(root)
    reloaded = load_corrective_freeze_packet(packet.directory)
    assert reloaded.packet_digest == packet.packet_digest
    assert reloaded.typed_evidence.description.identity_digest == packet.typed_evidence.description.identity_digest
    assert reloaded.excluded_alternate_roots == packet.excluded_alternate_roots
    assert not root.exists()


def test_empty_shared_motif_is_captured_as_a_distinct_source_posture(tmp_path: Path) -> None:
    root, adapter = _fixture(tmp_path)
    typed = _capture(root, adapter)
    motif = next(plan for plan in typed.source_scope_plans if plan.scope_key.domain_id == "motif")

    assert motif.materialization_posture is MaterializedScopePosture.EMPTY_SHARED_WITH_MOTIF
    assert motif.motif_presence is SourceArtifactPresence.PRESENT


def test_undeclared_alternate_root_and_unexpected_fourth_root_refuse(tmp_path: Path) -> None:
    root, adapter = _fixture(tmp_path)
    no_alternate = RealRootTypedEvidenceAdapter(
        data_root_identity=adapter.data_root_identity, operator_identity=adapter.operator_identity,
        excluded_source_artifacts=adapter.excluded_source_artifacts,
    )
    with pytest.raises(CorrectiveFreezePacketRefused, match="unclassified durable root artifact"):
        _capture(root, no_alternate)

    _write(root / "fourth_top_level.txt", "unexpected")
    with pytest.raises(CorrectiveFreezePacketRefused, match="unclassified durable root artifact"):
        _capture(root, adapter)


def test_alternate_root_requires_a_real_top_level_directory(tmp_path: Path) -> None:
    root, adapter = _fixture(tmp_path)
    shutil.rmtree(root / "lived_use")
    _write(root / "lived_use", "not a directory")
    with pytest.raises(CorrectiveFreezePacketRefused, match="alternate root"):
        _capture(root, adapter)


def test_alternate_root_nested_and_duplicate_declarations_refuse(tmp_path: Path) -> None:
    root, adapter = _fixture(tmp_path)
    with pytest.raises(CorrectiveFreezePacketRefused, match="direct child"):
        ExcludedAlternateRootLocator("lived_use/nested")
    with pytest.raises(CorrectiveFreezePacketRefused, match="duplicate"):
        RealRootTypedEvidenceAdapter(
            data_root_identity=adapter.data_root_identity, operator_identity=adapter.operator_identity,
            excluded_source_artifacts=adapter.excluded_source_artifacts,
            excluded_alternate_roots=(ExcludedAlternateRootLocator("lived_use"), ExcludedAlternateRootLocator("lived_use")),
        )


def test_alternate_root_symlink_refuses_when_supported(tmp_path: Path) -> None:
    root, adapter = _fixture(tmp_path)
    target = tmp_path / "alternate-target"
    target.mkdir()
    shutil.rmtree(root / "lived_use")
    try:
        os.symlink(target, root / "lived_use", target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation is not available on this Windows host")
    with pytest.raises(CorrectiveFreezePacketRefused, match="alternate root"):
        _capture(root, adapter)

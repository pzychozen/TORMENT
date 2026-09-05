from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import struct

import pytest

from torment_service.substrate.corrective_freeze_packet import (
    CorrectiveCaptureObservations,
    CorrectiveFreezePacketRefused,
    ExcludedAlternateRootRole,
    FrozenWorkspaceTreeTriple,
    PredecessorFreezeLineage,
    SourceArtifactPresence,
    capture_corrective_freeze_packet,
    load_corrective_freeze_packet,
)
from torment_service.substrate.migration.root_admission_description import (
    MaterializedScopePosture,
    RootRepresentationDisposition,
)
from torment_service.substrate.real_root_typed_evidence import (
    ExcludedAlternateRootLocator,
    ExcludedSourceArtifactLocator,
    RealRootTypedEvidenceAdapter,
)
from torment_service.substrate.root_blocker5_binding import discover_canonical_root_layout
from torment_service.substrate.writer_freeze_evidence import (
    ListenerObservation,
    ListenerObservationResult,
    RootJobObservation,
    RootWriterClass,
    WriterObservationResult,
    WriterProcessObservation,
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

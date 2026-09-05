from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
from dataclasses import replace
from uuid import UUID

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
from torment_service.substrate.migration.root_admission_description import (
    MaterializedScopePosture,
    RootRepresentationDisposition,
)
from torment_service.substrate.objects import NativeObjectService, ObjectState
from torment_service.substrate.real_root_typed_evidence import (
    DirectAdmissionSourcePreparation,
    ExcludedAlternateRootLocator,
    ExcludedSourceArtifactLocator,
    RealRootTypedEvidenceAdapter,
    build_real_direct_admission_source_adapter,
)
from torment_service.substrate.root_blocker5_binding import (
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

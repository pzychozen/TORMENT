"""Focused Phase 7G4 inert STAGING runtime-binding tests."""
from __future__ import annotations

from dataclasses import replace
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

import numpy as np
import pytest

from torment_service import fabric as fabric_module
from torment_service.fabric import TormentFabric
from torment_service.memory_graph import MemoryGraph
from torment_service.substrate import compat_query
from torment_service.substrate.compat import NativeMemoryCompatibilityFacade
from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.errors import (
    SubstrateConfigurationError,
    SubstrateSchemaCompatibilityError,
)
from torment_service.substrate.ids import generate_native_id, native_id_from_bytes, native_id_to_bytes
from torment_service.substrate.objects import NativeObjectService
from torment_service.substrate.relationships import NativeRelationshipService
from torment_service.substrate.representations import NativeRepresentationService
from torment_service.substrate.runtime_binding import (
    NativeMemoryRuntimeScope,
    NativeRepresentationLane,
    prepare_native_memory_runtime_binding,
    validate_fabric_embedder,
)
from torment_service.substrate.schema import CORE_ROLE_STAGING, create_schema, open_schema


def _id(): return generate_native_id()


class FakeEmbedder:
    def __init__(self, *, provider="synthetic", model="synthetic-v1", dim=3):
        self.provider = provider
        self.model = model
        self.dim = dim
        self.calls: list[str] = []

    def embed(self, text: str) -> np.ndarray:
        self.calls.append(text)
        return np.array((1.0, 0.0, 0.0), dtype=np.float32)


def _lane(**overrides):
    values = {
        "provider": "synthetic", "model": "synthetic-v1", "dimension": 3,
        "representation_class": "COMPAT_EMBEDDING", "generation": 1,
        "derivation_contract_version": "compat-embedding-v1",
        "encoding_id": "RAW_VECTOR", "dtype": "float32",
    }
    values.update(overrides)
    return NativeRepresentationLane(**values)


def _core(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "staging-runtime-binding.db")
    metadata = create_schema(qualified.connection)
    connection = qualified.connection
    return qualified, connection, native_id_from_bytes(metadata.core_id)


def _scope(connection, *, workspace_id: str, scope_kind: str, qualifier: str):
    identity, semantic, source = _id(), _id(), _id()
    connection.execute(
        "INSERT INTO identity_namespaces VALUES (?,?,0)",
        (native_id_to_bytes(identity), f"identity:{workspace_id}:{scope_kind}:{qualifier}"),
    )
    connection.execute(
        "INSERT INTO semantic_scopes VALUES (?,?,0)",
        (native_id_to_bytes(semantic), f"semantic:{workspace_id}:{scope_kind}:{qualifier}"),
    )
    connection.execute(
        "INSERT INTO legacy_source_namespaces VALUES (?,?,0)",
        (native_id_to_bytes(source), f"source:{workspace_id}:{scope_kind}:{qualifier}"),
    )
    return NativeMemoryRuntimeScope(
        workspace_id=workspace_id,
        scope_kind=scope_kind,
        agent_id=qualifier if scope_kind == "PRIVATE_AGENT" else None,
        domain_id=qualifier if scope_kind == "SHARED_DOMAIN" else None,
        legacy_source_namespace_id=source,
        identity_namespace_id=identity,
        semantic_scope_id=semantic,
    )


def _semantic_counts(connection):
    tables = (
        "objects", "object_revisions", "relationships", "relationship_revisions",
        "representations", "operations", "semantic_transitions",
        "integrity_expectations", "integrity_measurements", "reconciliation_cases",
    )
    counts = tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in tables)
    active_authorizations = connection.execute(
        "SELECT count(*) FROM object_revisions WHERE authority_category='ACTIVE_AUTHORIZATION'"
    ).fetchone()[0]
    return counts, active_authorizations


def _prepare(connection, qualified, core_id, *scopes):
    return prepare_native_memory_runtime_binding(
        connection=connection,
        core_database_path=qualified.database_path,
        expected_core_id=core_id,
        scope_bindings=tuple(scopes),
        representation_lane=_lane(),
    )


def test_staging_binding_is_explicit_immutable_and_creates_no_semantic_state(tmp_path: Path):
    qualified, connection, core_id = _core(tmp_path)
    try:
        private = _scope(connection, workspace_id="workspace", scope_kind="PRIVATE_AGENT", qualifier="agent")
        shared = _scope(connection, workspace_id="workspace", scope_kind="SHARED_DOMAIN", qualifier="domain")
        before = _semantic_counts(connection)
        binding = _prepare(connection, qualified, core_id, private, shared)
        assert binding.core_id == core_id
        assert binding.core_role == CORE_ROLE_STAGING
        assert binding.core_database_path == qualified.database_path.resolve()
        assert binding.scope_bindings == (private, shared)
        assert _semantic_counts(connection) == before
        with pytest.raises(Exception):
            binding.core_role = "ACTIVE_CORE"  # type: ignore[misc]

        readiness = validate_fabric_embedder(binding, FakeEmbedder())
        assert readiness.core_qualified is True
        assert readiness.core_role == CORE_ROLE_STAGING
        assert readiness.scope_bindings_valid is True
        assert readiness.embedder_lane_compatible is True
        assert readiness.activation_allowed is False
        assert readiness.status == "INERT_STAGING_BOUND"
        assert _semantic_counts(connection) == before
    finally:
        qualified.close()


def test_scope_bindings_are_private_shared_distinct_and_fail_closed(tmp_path: Path):
    qualified, connection, core_id = _core(tmp_path)
    try:
        private_a = _scope(connection, workspace_id="workspace-a", scope_kind="PRIVATE_AGENT", qualifier="same-name")
        shared_a = _scope(connection, workspace_id="workspace-a", scope_kind="SHARED_DOMAIN", qualifier="same-name")
        private_b = _scope(connection, workspace_id="workspace-b", scope_kind="PRIVATE_AGENT", qualifier="same-name")
        binding = _prepare(connection, qualified, core_id, private_a, shared_a, private_b)
        assert [(item.workspace_id, item.scope_kind, item.qualifier) for item in binding.scope_bindings] == [
            ("workspace-a", "PRIVATE_AGENT", "same-name"),
            ("workspace-a", "SHARED_DOMAIN", "same-name"),
            ("workspace-b", "PRIVATE_AGENT", "same-name"),
        ]
        with pytest.raises(SubstrateConfigurationError, match="collision"):
            _prepare(connection, qualified, core_id, private_a, private_a)
        with pytest.raises(SubstrateConfigurationError, match="collision"):
            _prepare(connection, qualified, core_id, shared_a, shared_a)
        duplicate_source = replace(private_b, legacy_source_namespace_id=private_a.legacy_source_namespace_id)
        with pytest.raises(SubstrateConfigurationError, match="source namespace"):
            _prepare(connection, qualified, core_id, private_a, duplicate_source)
        missing_identity = replace(private_a, identity_namespace_id=_id())
        with pytest.raises(SubstrateConfigurationError, match="missing identity_namespace_id"):
            _prepare(connection, qualified, core_id, missing_identity)
        missing_scope = replace(private_a, semantic_scope_id=_id())
        with pytest.raises(SubstrateConfigurationError, match="missing semantic_scope_id"):
            _prepare(connection, qualified, core_id, missing_scope)
        missing_source = replace(private_a, legacy_source_namespace_id=_id())
        with pytest.raises(SubstrateConfigurationError, match="missing legacy_source_namespace_id"):
            _prepare(connection, qualified, core_id, missing_source)
        malformed_private = replace(private_a, agent_id=None)
        with pytest.raises(SubstrateConfigurationError, match="private runtime scope"):
            _prepare(connection, qualified, core_id, malformed_private)
    finally:
        qualified.close()


def test_binding_refuses_unknown_active_evidence_and_nonlegacy_deployment_cores(tmp_path: Path):
    qualified, connection, core_id = _core(tmp_path)
    try:
        scope = _scope(connection, workspace_id="workspace", scope_kind="PRIVATE_AGENT", qualifier="agent")
        with pytest.raises(SubstrateConfigurationError, match="identity"):
            _prepare(connection, qualified, _id(), scope)
        connection.execute("UPDATE core_metadata SET core_role='ACTIVE_CORE'")
        with pytest.raises(SubstrateConfigurationError, match="only STAGING"):
            _prepare(connection, qualified, core_id, scope)
        connection.execute("UPDATE core_metadata SET core_role='EVIDENCE_ONLY'")
        with pytest.raises(SubstrateConfigurationError, match="only STAGING"):
            _prepare(connection, qualified, core_id, scope)
        connection.execute("UPDATE core_metadata SET core_role='STAGING'")
        connection.execute(
            "UPDATE deployment_metadata SET deployment_state='NATIVE_ACTIVE',referenced_core_id=?",
            (native_id_to_bytes(core_id),),
        )
        with pytest.raises(SubstrateConfigurationError, match="non-legacy-active"):
            _prepare(connection, qualified, core_id, scope)
    finally:
        qualified.close()


def test_binding_refuses_unknown_schema_without_creating_one(tmp_path: Path):
    database_path = tmp_path / "unknown-schema.db"
    connection = sqlite3.connect(str(database_path), isolation_level=None)
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        scope = NativeMemoryRuntimeScope(
            workspace_id="workspace", scope_kind="PRIVATE_AGENT", agent_id="agent",
            legacy_source_namespace_id=_id(), identity_namespace_id=_id(), semantic_scope_id=_id(),
        )
        with pytest.raises(SubstrateSchemaCompatibilityError):
            prepare_native_memory_runtime_binding(
                connection=connection, core_database_path=database_path,
                expected_core_id=_id(), scope_bindings=(scope,), representation_lane=_lane(),
            )
        assert connection.execute(
            "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='core_metadata'"
        ).fetchone()[0] == 0
    finally:
        connection.close()


def test_fabric_embedder_lane_mismatch_refuses_same_dimension_wrong_model(tmp_path: Path):
    qualified, connection, core_id = _core(tmp_path)
    try:
        scope = _scope(connection, workspace_id="workspace", scope_kind="PRIVATE_AGENT", qualifier="agent")
        binding = _prepare(connection, qualified, core_id, scope)
        with pytest.raises(SubstrateConfigurationError, match="model"):
            validate_fabric_embedder(binding, FakeEmbedder(model="synthetic-v2"))
        with pytest.raises(SubstrateConfigurationError, match="provider"):
            validate_fabric_embedder(binding, FakeEmbedder(provider="other"))
        with pytest.raises(SubstrateConfigurationError, match="dimension"):
            validate_fabric_embedder(binding, FakeEmbedder(dim=4))
    finally:
        qualified.close()


def test_default_and_attached_fabric_remain_legacy_only_and_never_touch_native(tmp_path: Path, monkeypatch):
    qualified, connection, core_id = _core(tmp_path)
    try:
        scope = _scope(connection, workspace_id="workspace", scope_kind="PRIVATE_AGENT", qualifier="agent")
        shared = _scope(connection, workspace_id="workspace", scope_kind="SHARED_DOMAIN", qualifier="default")
        binding = _prepare(connection, qualified, core_id, scope, shared)
        factory_calls: list[FakeEmbedder] = []

        def build_fake_embedder():
            embedder = FakeEmbedder()
            factory_calls.append(embedder)
            return embedder

        monkeypatch.setattr(fabric_module, "build_embedder_from_env", build_fake_embedder)
        monkeypatch.setenv("TORMENT_SQLITE_INDEX_ENABLE", "0")
        monkeypatch.setenv("TORMENT_CHARACTER_ENABLE", "0")
        default_root = tmp_path / "default-fabric"
        default_fabric = TormentFabric(data_dir=str(default_root))
        try:
            assert default_fabric.native_memory_binding is None
            assert default_fabric.native_memory_binding_readiness is None
            assert not list(default_root.rglob("*.db"))
        finally:
            default_fabric.close()

        def fail_native(*_args, **_kwargs):
            raise AssertionError("ordinary Fabric runtime attempted a native substrate call")

        monkeypatch.setattr(NativeMemoryCompatibilityFacade, "__init__", fail_native)
        monkeypatch.setattr(NativeObjectService, "__init__", fail_native)
        monkeypatch.setattr(NativeRepresentationService, "__init__", fail_native)
        monkeypatch.setattr(NativeRelationshipService, "__init__", fail_native)
        monkeypatch.setattr(compat_query, "search_text", fail_native)
        before = _semantic_counts(connection)
        attached_root = tmp_path / "attached-fabric"
        attached = TormentFabric(data_dir=str(attached_root), native_memory_binding=binding)
        try:
            assert attached.native_memory_binding is binding
            assert attached.native_memory_binding_readiness is not None
            assert attached.native_memory_binding_readiness.activation_allowed is False
            result = attached.ingest("workspace", "agent", "legacy-only inert binding exercise", step=1)
            assert isinstance(result["eid"], int)
            assert isinstance(attached.private_graphs[attached._agent_key("workspace", "agent")], MemoryGraph)
            workspace = attached.get_workspace("workspace")
            assert all(isinstance(graph, MemoryGraph) for graph in workspace.shared_graphs.values())
            assert attached.private_graphs[attached._agent_key("workspace", "agent")].search("legacy-only")
            assert _semantic_counts(connection) == before
            assert not any(isinstance(value, sqlite3.Connection) for value in attached.__dict__.values())
            assert not list(attached_root.rglob("*.db"))
        finally:
            attached.close()
        assert len(factory_calls) == 2
    finally:
        qualified.close()


def test_app_startup_ignores_native_selector_names_and_creates_no_core(tmp_path: Path):
    data_dir = tmp_path / "app-data"
    environment = os.environ.copy()
    environment.update({
        "TORMENT_DATA_DIR": str(data_dir),
        "TORMENT_MEMORY_BACKEND": "native",
        "TORMENT_SUBSTRATE_ENABLE": "1",
        "TORMENT_NATIVE_MEMORY": "1",
        "TORMENT_SQLITE_INDEX_ENABLE": "0",
        "TORMENT_CHARACTER_ENABLE": "0",
    })
    code = """
import os
from pathlib import Path
from torment_service import app
root = Path(os.environ['TORMENT_DATA_DIR'])
assert app.fabric.native_memory_binding is None
assert not list(root.rglob('*.db'))
"""
    completed = subprocess.run(
        [sys.executable, "-c", code], cwd=str(Path(__file__).resolve().parents[1]),
        env=environment, capture_output=True, text=True, timeout=30,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr

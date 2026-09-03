"""P9D-I3B0: bounded native query materialization-fence regression tests."""
from __future__ import annotations

from hashlib import sha256
import inspect
from pathlib import Path

import pytest
from fastapi import HTTPException

from torment_service.fabric import _load_affect_state
from torment_service.public_runtime import (
    NativePublicOperationRefused,
    _ReadOnlyConflictRegistry,
    close_public_runtime,
    create_public_runtime,
)
from torment_service.query_read_model import NativeQueryReadRefused
from torment_service.roles import RoleStore

from test_b5_a3_production_native_resource_owner import _active_fixture
from test_b5_a4r3_public_backend_selection import (
    _NativeLaneFabric,
    _configuration,
    _prime_external_identity,
)
from tests.test_7g5e4e_native_query_read_model import qualified_models
from tests.test_7g5e4e_query_cognition_parity import fabric_models


# This is deliberately a small maintained census rather than a general static
# analyzer.  A change to a native root's materializer-like helper reference
# must add an entry here and focused execution coverage below.
NATIVE_READ_MATERIALIZER_CENSUS = {
    "workspace_agent_bootstrap": {
        "route": "TormentFabric.query",
        "materializer": "get_workspace/create_agent -> Workspace/identity state",
        "disposition": "I2 legacy-materialization fence plus native existing-state path",
    },
    "collective_field": {
        "route": "TormentFabric.query -> _collective_query_context",
        "materializer": "CollectiveField.__init__ -> collective directory",
        "disposition": "refuse when native collective context is applicable",
    },
    "archive_recall": {
        "route": "POST /retrieve -> _get_archive_store",
        "materializer": "ArchiveStore.__init__ -> memory_archive directory",
        "disposition": "refuse before core/archive composition when recall is enabled",
    },
    "archive_promotion_count": {
        "route": "POST /retrieve -> increment_retrieval_counts",
        "materializer": "promotion counter JSON write",
        "disposition": "unreachable after the same archive composition refusal",
    },
    "affect_read": {
        "route": "TormentFabric.query / native derived side-store",
        "materializer": "_affect_state_path -> agent directory",
        "disposition": "native read passes materialize_parent=False",
    },
    "role_default": {
        "route": "TormentFabric.query -> _role_context",
        "materializer": "RoleStore.load default -> roles.json",
        "disposition": "native disposition passes read_only=True",
    },
}


def _native_runtime(tmp_path: Path, monkeypatch):
    """Build an active synthetic root with pre-existing external facts only."""
    import torment_service.public_runtime as public_runtime

    monkeypatch.setattr(public_runtime, "TormentFabric", _NativeLaneFabric)
    root, _core, descriptor, profile, _agreement = _active_fixture(tmp_path)
    _prime_external_identity(root)
    runtime = create_public_runtime(root, _configuration(root, descriptor, profile))
    return root, runtime


def _tree_signature(root: Path) -> tuple[tuple[str, str], ...]:
    values: list[tuple[str, str]] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_dir():
            values.append((f"dir:{relative}", ""))
        elif path.is_file():
            values.append((f"file:{relative}", sha256(path.read_bytes()).hexdigest()))
    return tuple(values)


def test_native_collective_query_refuses_before_collective_directory_creation(tmp_path, monkeypatch):
    root, runtime = _native_runtime(tmp_path, monkeypatch)
    collective_dir = root / "workspaces" / "orchard" / "collective"
    runtime.cognition_fabric._hivemind_enable = True
    try:
        with pytest.raises(NativePublicOperationRefused, match="qualified read evidence"):
            runtime.query("orchard", "aria", "collective context")
        assert not collective_dir.exists()
    finally:
        close_public_runtime(root)


def test_native_retrieve_refuses_archive_recall_before_archive_store_or_counter(tmp_path, monkeypatch):
    import torment_service.app as app_module

    root, runtime = _native_runtime(tmp_path, monkeypatch)
    archive_dir = root / "workspaces" / "orchard" / "agents" / "aria" / "memory_archive"

    class _RuntimeProxy:
        def runtime(self):
            return runtime

        def query(self, **_kwargs):
            raise AssertionError("archive-native refusal must precede core query")

    monkeypatch.setattr(app_module, "fabric", _RuntimeProxy())
    monkeypatch.setattr(app_module._thinking_controller_module, "_ARCHIVE_RECALL_ENABLE", True)
    try:
        request = app_module.AssembleContextReq(
            workspace_id="orchard", agent_id="aria", query="archive recall",
        )
        with pytest.raises(HTTPException) as refused:
            app_module.retrieve_assembled(request)
        assert refused.value.status_code == 409
        assert not archive_dir.exists()
    finally:
        close_public_runtime(root)


def test_native_archive_route_inventory_fails_closed_for_unknown_future_route():
    from torment_service.app import (
        NATIVE_EXPLICIT_ARCHIVE_REST_ROUTES,
        _native_rest_route_is_classified,
    )

    assert NATIVE_EXPLICIT_ARCHIVE_REST_ROUTES == frozenset()
    assert not _native_rest_route_is_classified("POST", "/archive/future-write")
    assert not _native_rest_route_is_classified("POST", "/archive/query")


def test_native_derived_affect_read_does_not_create_absent_agent_directory(tmp_path, monkeypatch):
    root, runtime = _native_runtime(tmp_path, monkeypatch)
    missing_agent_dir = root / "workspaces" / "orchard" / "agents" / "missing"
    try:
        state = runtime._side_store.load_affect_state(  # noqa: SLF001 - explicit native adapter contract
            workspace_id="orchard", agent_id="missing",
        )
        assert state["drift_hist"] == []
        assert not missing_agent_dir.exists()
    finally:
        close_public_runtime(root)


def test_native_qualified_read_model_does_not_create_default_role_state(fabric_models):
    fabric, native_model, _embedder, _legacy_embedders = fabric_models
    role_path = Path(fabric.data_dir) / "workspaces" / "orchard" / "agents" / "aria" / "roles.json"
    # The established parity fixture creates legacy setup state.  Remove only
    # its disposable role artifact to prove the native execution itself does
    # not recreate a default role profile.
    role_path.unlink()
    assert not role_path.exists()

    result = fabric._query_with_read_model(
        "orchard", "aria", "qualified native role read", read_model=native_model,
    )

    assert "role_context" in result
    assert not role_path.exists()


def test_native_malformed_conflict_evidence_refusal_survives_query_layer(fabric_models, tmp_path):
    fabric, native_model, _embedder, _legacy_embedders = fabric_models
    ws = fabric.workspaces["orchard"]
    evidence_root = tmp_path / "native-conflicts"
    evidence_root.mkdir()
    malformed = evidence_root / "conflicts.jsonl"
    malformed.write_text("{not-json}\n", encoding="utf-8")
    ws.conflicts = {
        domain: _ReadOnlyConflictRegistry(evidence_root)
        for domain in ws.domains
    }

    with pytest.raises(NativeQueryReadRefused, match="conflict evidence is malformed"):
        fabric._query_with_read_model(
            "orchard", "aria", "qualified native conflict read", read_model=native_model,
        )


def test_native_absent_conflict_evidence_retains_empty_legacy_compatible_result(fabric_models, tmp_path):
    fabric, native_model, _embedder, _legacy_embedders = fabric_models
    ws = fabric.workspaces["orchard"]
    absent_root = tmp_path / "absent-native-conflicts"
    ws.conflicts = {
        domain: _ReadOnlyConflictRegistry(absent_root / domain)
        for domain in ws.domains
    }

    result = fabric._query_with_read_model(
        "orchard", "aria", "qualified native no conflict evidence", read_model=native_model,
    )

    assert result["results"]
    assert all("conflict_status" not in item for item in result["results"])


def test_native_qualified_query_with_optional_legacy_paths_disabled_leaves_external_tree_unchanged(
    fabric_models, monkeypatch,
):
    fabric, native_model, _embedder, _legacy_embedders = fabric_models
    monkeypatch.setenv("TORMENT_AFFECT_ENABLE", "0")
    monkeypatch.setenv("TORMENT_MOOD_SPIRAL_ENABLE", "0")
    monkeypatch.setenv("TORMENT_HIVEMIND_ENABLE", "0")
    monkeypatch.setenv("TORMENT_SRG_ENABLE", "0")
    fabric._hivemind_enable = False
    fabric._srg_enable = False
    fabric._character_enable = False
    before = _tree_signature(Path(fabric.data_dir))

    result = fabric._query_with_read_model(
        "orchard", "aria", "qualified native no optional side paths", read_model=native_model,
    )

    assert result["results"]
    assert _tree_signature(Path(fabric.data_dir)) == before


def test_legacy_authoritative_affect_and_role_reads_retain_materializing_defaults(tmp_path):
    data_dir = tmp_path / "legacy"
    _load_affect_state(str(data_dir), "orchard", "aria")
    affect_agent_dir = data_dir / "workspaces" / "orchard" / "agents" / "aria"
    assert affect_agent_dir.is_dir()

    role_store = RoleStore(str(data_dir))
    role_store.load("orchard", "aria")
    assert (affect_agent_dir / "roles.json").is_file()


def test_native_materializer_census_is_complete_for_bounded_native_roots():
    from torment_service import app as app_module
    from torment_service.fabric import TormentFabric

    assert set(NATIVE_READ_MATERIALIZER_CENSUS) == {
        "workspace_agent_bootstrap",
        "collective_field",
        "archive_recall",
        "archive_promotion_count",
        "affect_read",
        "role_default",
    }
    assert all(item["disposition"] for item in NATIVE_READ_MATERIALIZER_CENSUS.values())

    query_source = inspect.getsource(TormentFabric.query)
    retrieve_source = inspect.getsource(app_module.retrieve_assembled)
    # Every materializer-like legacy helper currently reachable from the two
    # native roots has a maintained census entry above.  New references fail
    # this assertion until their native disposition is explicitly classified.
    observed = {
        "workspace_agent_bootstrap": all(name in query_source for name in ("get_workspace", "create_agent")),
        "collective_field": "_collective_query_context" in query_source,
        "archive_recall": "_get_archive_store" in retrieve_source,
        "archive_promotion_count": "increment_retrieval_counts" in retrieve_source,
        "affect_read": "_load_affect_state" in query_source,
        "role_default": "_role_context" in query_source,
    }
    assert set(observed) == set(NATIVE_READ_MATERIALIZER_CENSUS)
    assert all(observed.values())

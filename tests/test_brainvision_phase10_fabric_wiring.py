"""Phase-10 Fabric hosting boundary and import-isolation coverage."""

import ast
from pathlib import Path

from brainvision.lifecycle import BrainvisionLifecycleManager
from torment_service.fabric import TormentFabric


def test_fabric_constructs_one_inert_manager_using_its_existing_infrastructure(
    tmp_path: Path,
) -> None:
    fabric = TormentFabric(str(tmp_path))
    try:
        manager = fabric.brainvision_lifecycle
        assert type(manager) is BrainvisionLifecycleManager
        assert manager._identity_store is fabric.ident_store
        assert manager._lock_manager is fabric.locks
        assert manager.runtime_count == 0
        assert not list(tmp_path.rglob("brainvision"))
    finally:
        fabric.close()


def test_fabric_close_invokes_brainvision_shutdown_first_and_is_defensive(tmp_path: Path) -> None:
    fabric = TormentFabric(str(tmp_path))
    events: list[str] = []

    class RecordingManager:
        def shutdown(self) -> None:
            events.append("brainvision")

    class RecordingIndex:
        def close(self) -> None:
            assert events == ["brainvision"]
            events.append("sqlite")

    fabric.brainvision_lifecycle = RecordingManager()
    fabric._sqlite_indexes["one"] = RecordingIndex()
    fabric.close()
    fabric.close()
    assert events == ["brainvision", "sqlite", "brainvision"]

    class RaisingManager:
        def shutdown(self) -> None:
            raise RuntimeError("deliberate shutdown failure")

    second = TormentFabric(str(tmp_path / "second"))
    second.brainvision_lifecycle = RaisingManager()
    second.close()


def test_lifecycle_imports_are_limited_to_the_frozen_hosting_boundary() -> None:
    import brainvision.lifecycle as lifecycle_module

    source = Path(lifecycle_module.__file__).read_text(encoding="utf-8")
    imports: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.add(node.module)

    assert {
        "brainvision.clock",
        "brainvision.configuration",
        "brainvision.vhe",
        "brainvision.vhe_sidecar",
        "torment_service.agent_locks",
        "torment_service.identity",
    } <= imports
    forbidden_prefixes = (
        "torment_service.fabric",
        "memory",
        "kernel",
        "character",
        "cognition",
        "srg",
        "hivermind",
        "model",
        "prompt",
    )
    assert not any(
        imported == prefix or imported.startswith(prefix + ".")
        for imported in imports
        for prefix in forbidden_prefixes
    )


def test_fabric_exposes_no_phase11_ingress_or_phase12_sink_api() -> None:
    # The module source is inspected through the import location so the test
    # remains independent of checkout-relative working-directory assumptions.
    source = Path(__import__(TormentFabric.__module__, fromlist=["__file__"]).__file__)
    text = source.read_text(encoding="utf-8")
    assert "brainvision_lifecycle" in text
    assert "brainvision_ingest" not in text
    assert "brainvision_snapshot" not in text
    assert "brainvision_projection" not in text

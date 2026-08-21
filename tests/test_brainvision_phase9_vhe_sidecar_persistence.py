"""Phase-9 VHE sidecar mechanical persistence and compatibility coverage."""

import ast
from dataclasses import replace
import json
from pathlib import Path

import pytest

import brainvision.vhe_sidecar as sidecar_module
from brainvision.configuration import (
    LIFECYCLE_ACTIVE,
    LIFECYCLE_SUSPENDED,
    fresh_disabled_brainvision_configuration,
)
from brainvision.vhe_sidecar import (
    CONFIG_AHEAD,
    EQUAL,
    SIDECAR_AHEAD,
    VHE_SIDECAR_FILENAME,
    VheSidecarValidationError,
    fresh_vhe_sidecar,
    load_vhe_sidecar,
    validate_configuration_sidecar_compatibility,
    vhe_sidecar_path,
    write_vhe_sidecar,
)


def _configuration(*, watermark: int = -1, status: str = "disabled", theta: int = 0):
    return replace(
        fresh_disabled_brainvision_configuration(
            stream_identity="camera-main",
            adapter_contract_id="descriptor-v1",
            theta=theta,
        ),
        lifecycle_status=status,
        last_accepted_source_sequence=watermark,
    )


def _sidecar(*, watermark: int = -1, theta: int = 0):
    return fresh_vhe_sidecar(_configuration(watermark=watermark, theta=theta))


def _path(root: Path) -> Path:
    return Path(vhe_sidecar_path(root, "workspace-a", "agent-a"))


def _prepare_brainvision_directory(root: Path) -> Path:
    directory = root / "workspaces" / "workspace-a" / "agents" / "agent-a" / "brainvision"
    directory.mkdir(parents=True)
    return directory


def _force_mutation(value: object, **changes: object):
    changed = replace(value)
    for field, replacement in changes.items():
        object.__setattr__(changed, field, replacement)
    return changed


def test_sidecar_path_is_exactly_contained_and_nonmutating(tmp_path: Path) -> None:
    root = tmp_path / "data"

    assert _path(root) == (
        root
        / "workspaces"
        / "workspace-a"
        / "agents"
        / "agent-a"
        / "brainvision"
        / VHE_SIDECAR_FILENAME
    )
    assert not root.exists()


@pytest.mark.parametrize(
    ("workspace_id", "agent_id"),
    (("../workspace", "agent-a"), ("workspace-a", "../agent"), ("workspace/a", "agent-a")),
)
def test_sidecar_path_rejects_traversal(tmp_path: Path, workspace_id: str, agent_id: str) -> None:
    with pytest.raises(ValueError):
        vhe_sidecar_path(tmp_path / "data", workspace_id, agent_id)


def test_absent_read_returns_none_without_creating_paths(tmp_path: Path) -> None:
    root = tmp_path / "data"

    assert load_vhe_sidecar(root, "workspace-a", "agent-a") is None
    assert not root.exists()


def test_write_refuses_missing_brainvision_directory_without_creating_agent_paths(
    tmp_path: Path,
) -> None:
    root = tmp_path / "data"
    root.mkdir()

    with pytest.raises(FileNotFoundError):
        write_vhe_sidecar(root, "workspace-a", "agent-a", _sidecar())

    assert root.exists()
    assert not (root / "workspaces").exists()
    assert not _path(root).parent.exists()
    assert not _path(root).exists()


def test_existing_brainvision_directory_permits_canonical_sidecar_write_only(
    tmp_path: Path,
) -> None:
    root = tmp_path / "data"
    directory = _prepare_brainvision_directory(root)
    sidecar = _sidecar()

    write_vhe_sidecar(root, "workspace-a", "agent-a", sidecar)

    target = _path(root)
    assert target.read_bytes() == sidecar.to_canonical_json_bytes()
    assert load_vhe_sidecar(root, "workspace-a", "agent-a") == sidecar
    assert {entry.name for entry in directory.iterdir()} == {VHE_SIDECAR_FILENAME}
    assert not (directory / "configuration.json").exists()


def test_malformed_existing_sidecar_raises(tmp_path: Path) -> None:
    root = tmp_path / "data"
    _prepare_brainvision_directory(root)
    _path(root).write_bytes(b"{")

    with pytest.raises(json.JSONDecodeError):
        load_vhe_sidecar(root, "workspace-a", "agent-a")


def test_atomic_replacement_replaces_entire_sidecar_and_leaves_no_temp(tmp_path: Path) -> None:
    root = tmp_path / "data"
    _prepare_brainvision_directory(root)
    prior = _sidecar(watermark=0)
    replacement = _sidecar(watermark=1)
    write_vhe_sidecar(root, "workspace-a", "agent-a", prior)
    prior_bytes = _path(root).read_bytes()

    write_vhe_sidecar(root, "workspace-a", "agent-a", replacement)

    assert _path(root).read_bytes() == replacement.to_canonical_json_bytes()
    assert _path(root).read_bytes() != prior_bytes
    assert not list(_path(root).parent.glob(".vhe-state-*.tmp"))


def test_temporary_write_failure_preserves_prior_sidecar(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "data"
    _prepare_brainvision_directory(root)
    prior = _sidecar(watermark=0)
    replacement = _sidecar(watermark=1)
    write_vhe_sidecar(root, "workspace-a", "agent-a", prior)
    target = _path(root)
    prior_bytes = target.read_bytes()
    failing_path = target.parent / ".vhe-state-write-failure.tmp"

    class FailingTemporaryFile:
        def __init__(self) -> None:
            self.name = str(failing_path)
            self._handle = None

        def __enter__(self) -> "FailingTemporaryFile":
            self._handle = open(self.name, "xb")
            return self

        def write(self, data: bytes) -> int:
            raise OSError("simulated temporary write failure")

        def flush(self) -> None:
            raise AssertionError("flush must not run after write failure")

        def fileno(self) -> int:
            raise AssertionError("fsync must not run after write failure")

        def __exit__(self, *_: object) -> None:
            assert self._handle is not None
            self._handle.close()

    def failing_named_temporary_file(**_: object) -> FailingTemporaryFile:
        return FailingTemporaryFile()

    monkeypatch.setattr(
        sidecar_module.tempfile,
        "NamedTemporaryFile",
        failing_named_temporary_file,
    )
    with pytest.raises(OSError, match="simulated temporary write failure"):
        write_vhe_sidecar(root, "workspace-a", "agent-a", replacement)

    assert target.read_bytes() == prior_bytes
    assert not failing_path.exists()


def test_compatibility_classifies_equal_sidecar_ahead_and_configuration_ahead() -> None:
    configuration = _configuration(watermark=5)

    assert validate_configuration_sidecar_compatibility(
        configuration,
        _sidecar(watermark=5),
    ) == EQUAL
    assert validate_configuration_sidecar_compatibility(
        configuration,
        _sidecar(watermark=6),
    ) == SIDECAR_AHEAD
    assert validate_configuration_sidecar_compatibility(
        configuration,
        _sidecar(watermark=4),
    ) == CONFIG_AHEAD


def test_compatibility_rejects_lineage_and_continuation_identity_mismatch() -> None:
    configuration = _configuration()
    candidates = (
        _force_mutation(_sidecar(), stream_identity="camera-other"),
        _force_mutation(_sidecar(), adapter_contract_id="descriptor-v2"),
        _force_mutation(_sidecar(), expected_operator_id="other"),
        _force_mutation(_sidecar(), expected_projection_id="other"),
        _sidecar(theta=1),
    )
    for sidecar in candidates:
        with pytest.raises(VheSidecarValidationError):
            validate_configuration_sidecar_compatibility(configuration, sidecar)


@pytest.mark.parametrize("status", (LIFECYCLE_ACTIVE, LIFECYCLE_SUSPENDED))
def test_compatibility_ignores_lifecycle_policy_and_does_not_mutate(status: str) -> None:
    configuration = _configuration(watermark=3, status=status)
    sidecar = _sidecar(watermark=3)
    before_configuration = configuration.to_dict()
    before_sidecar = sidecar.to_dict()

    assert validate_configuration_sidecar_compatibility(configuration, sidecar) == EQUAL
    assert configuration.to_dict() == before_configuration
    assert sidecar.to_dict() == before_sidecar


def test_static_import_isolation_and_no_recovery_or_deletion_api() -> None:
    source = Path(sidecar_module.__file__).read_text(encoding="utf-8")
    imports: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.add(node.module)

    assert {"brainvision.configuration", "brainvision.vhe", "torment_service.pathing"} <= imports
    forbidden_prefixes = (
        "torment_service.fabric",
        "torment_service.agent_locks",
        "memory",
        "kernel",
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
    assert not hasattr(sidecar_module, "delete_vhe_sidecar")
    assert not hasattr(sidecar_module, "repair_configuration_watermark")

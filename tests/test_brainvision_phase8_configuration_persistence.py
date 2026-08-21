"""Phase-8 Brainvision configuration replacement and persistence coverage."""

import ast
from dataclasses import replace
import json
from pathlib import Path

import pytest

import brainvision.configuration as configuration_module
from brainvision.configuration import (
    BrainvisionConfigurationV1,
    BrainvisionConfigurationValidationError,
    LIFECYCLE_ACTIVE,
    LIFECYCLE_DISABLED,
    LIFECYCLE_SUSPENDED,
    brainvision_configuration_path,
    fresh_disabled_brainvision_configuration,
    load_brainvision_configuration,
    validate_configuration_replacement,
    write_brainvision_configuration,
)


def _configuration(
    *,
    theta: int = 0,
    watermark: int = -1,
    lifecycle_status: str = LIFECYCLE_DISABLED,
) -> BrainvisionConfigurationV1:
    configuration = fresh_disabled_brainvision_configuration(
        stream_identity="camera-main",
        adapter_contract_id="descriptor-v1",
        theta=theta,
    )
    return replace(
        configuration,
        lifecycle_status=lifecycle_status,
        last_accepted_source_sequence=watermark,
    )


def _path(root: Path) -> Path:
    return Path(brainvision_configuration_path(root, "workspace-a", "agent-a"))


def _prepare_agent_root(root: Path) -> Path:
    agent_root = root / "workspaces" / "workspace-a" / "agents" / "agent-a"
    agent_root.mkdir(parents=True)
    return agent_root


def _force_mutation(
    configuration: BrainvisionConfigurationV1, **changes: object
) -> BrainvisionConfigurationV1:
    """Construct invalid frozen-object input to prove replacement revalidates it."""
    changed = replace(configuration)
    for field, value in changes.items():
        object.__setattr__(changed, field, value)
    return changed


def test_configuration_path_is_exactly_contained_and_nonmutating(tmp_path: Path) -> None:
    root = tmp_path / "data"

    assert _path(root) == (
        root
        / "workspaces"
        / "workspace-a"
        / "agents"
        / "agent-a"
        / "brainvision"
        / "configuration.json"
    )
    assert not root.exists()


@pytest.mark.parametrize(
    ("workspace_id", "agent_id"),
    (("../workspace", "agent-a"), ("workspace-a", "../agent"), ("workspace/a", "agent-a")),
)
def test_configuration_path_rejects_dynamic_component_traversal(
    tmp_path: Path, workspace_id: str, agent_id: str
) -> None:
    with pytest.raises(ValueError):
        brainvision_configuration_path(tmp_path / "data", workspace_id, agent_id)


def test_absent_read_returns_none_without_creating_any_path(tmp_path: Path) -> None:
    root = tmp_path / "data"

    assert load_brainvision_configuration(root, "workspace-a", "agent-a") is None
    assert not root.exists()


def test_write_is_canonical_and_read_is_a_strict_equal_round_trip(tmp_path: Path) -> None:
    root = tmp_path / "data"
    configuration = _configuration()
    _prepare_agent_root(root)

    write_brainvision_configuration(root, "workspace-a", "agent-a", configuration)

    target = _path(root)
    assert target.read_bytes() == configuration.to_canonical_json_bytes()
    assert load_brainvision_configuration(root, "workspace-a", "agent-a") == configuration
    assert {path.name for path in root.rglob("*") if path.is_file()} == {"configuration.json"}


def test_write_requires_a_preexisting_ordinary_agent_directory(tmp_path: Path) -> None:
    root = tmp_path / "data"
    root.mkdir()

    with pytest.raises(FileNotFoundError):
        write_brainvision_configuration(root, "workspace-a", "agent-a", _configuration())

    assert root.exists()
    assert not (root / "workspaces").exists()
    assert not (root / "workspaces" / "workspace-a" / "agents" / "agent-a").exists()
    assert not _path(root).parent.exists()
    assert not _path(root).exists()


def test_write_creates_only_the_brainvision_leaf_for_a_preexisting_agent(tmp_path: Path) -> None:
    root = tmp_path / "data"
    agent_root = _prepare_agent_root(root)

    write_brainvision_configuration(root, "workspace-a", "agent-a", _configuration())

    assert {entry.name for entry in agent_root.iterdir()} == {"brainvision"}
    assert {entry.name for entry in (agent_root / "brainvision").iterdir()} == {
        "configuration.json"
    }


def test_malformed_or_incompatible_existing_configuration_raises(tmp_path: Path) -> None:
    root = tmp_path / "data"
    target = _path(root)
    target.parent.mkdir(parents=True)
    target.write_bytes(b"{")

    with pytest.raises(json.JSONDecodeError):
        load_brainvision_configuration(root, "workspace-a", "agent-a")

    incompatible = _configuration().to_dict()
    incompatible["expected_operator_id"] = "not-the-frozen-operator"
    target.write_bytes(
        json.dumps(
            incompatible,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    )
    with pytest.raises(BrainvisionConfigurationValidationError) as error:
        load_brainvision_configuration(root, "workspace-a", "agent-a")
    assert (error.value.field, error.value.reason) == (
        "expected_operator_id",
        "operator_identity_mismatch",
    )


def test_atomic_replacement_replaces_the_complete_canonical_artifact(tmp_path: Path) -> None:
    root = tmp_path / "data"
    prior = _configuration()
    replacement = _configuration(watermark=0, lifecycle_status=LIFECYCLE_ACTIVE)
    _prepare_agent_root(root)
    write_brainvision_configuration(root, "workspace-a", "agent-a", prior)
    prior_bytes = _path(root).read_bytes()

    write_brainvision_configuration(root, "workspace-a", "agent-a", replacement)

    assert _path(root).read_bytes() == replacement.to_canonical_json_bytes()
    assert _path(root).read_bytes() != prior_bytes
    assert not list(_path(root).parent.glob(".configuration-*.tmp"))


def test_temporary_write_failure_preserves_the_prior_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "data"
    prior = _configuration()
    replacement = _configuration(watermark=1)
    _prepare_agent_root(root)
    write_brainvision_configuration(root, "workspace-a", "agent-a", prior)
    target = _path(root)
    prior_bytes = target.read_bytes()
    failing_temp_path = target.parent / ".configuration-write-failure.tmp"

    class FailingTemporaryFile:
        def __init__(self) -> None:
            self.name = str(failing_temp_path)
            self._handle = None

        def __enter__(self) -> "FailingTemporaryFile":
            self._handle = open(self.name, "xb")
            return self

        def write(self, data: bytes) -> int:
            raise OSError("simulated temporary write failure")

        def flush(self) -> None:
            raise AssertionError("flush must not run after the write failure")

        def fileno(self) -> int:
            raise AssertionError("fsync must not run after the write failure")

        def __exit__(self, *_: object) -> None:
            assert self._handle is not None
            self._handle.close()

    def failing_named_temporary_file(**_: object) -> FailingTemporaryFile:
        return FailingTemporaryFile()

    monkeypatch.setattr(
        configuration_module.tempfile, "NamedTemporaryFile", failing_named_temporary_file
    )
    with pytest.raises(OSError, match="simulated temporary write failure"):
        write_brainvision_configuration(root, "workspace-a", "agent-a", replacement)

    assert target.read_bytes() == prior_bytes
    assert not failing_temp_path.exists()


def test_replacement_allows_equal_or_increasing_watermark_and_rejects_decrease() -> None:
    prior = _configuration(watermark=5)
    validate_configuration_replacement(prior, _configuration(watermark=5))
    validate_configuration_replacement(prior, _configuration(watermark=6))

    with pytest.raises(BrainvisionConfigurationValidationError) as error:
        validate_configuration_replacement(prior, _configuration(watermark=4))
    assert (error.value.field, error.value.reason) == (
        "last_accepted_source_sequence",
        "watermark_decrease",
    )


def test_replacement_rejects_stream_adapter_and_base_identity_mutation() -> None:
    prior = _configuration()
    for candidate in (
        _force_mutation(prior, stream_identity="camera-other"),
        _force_mutation(prior, adapter_contract_id="descriptor-v2"),
        _force_mutation(prior, expected_operator_id="other-operator"),
        _force_mutation(prior, expected_projection_id="other-projection"),
    ):
        with pytest.raises(BrainvisionConfigurationValidationError):
            validate_configuration_replacement(prior, candidate)


def test_replacement_rejects_modulation_identity_mutation() -> None:
    prior = _configuration()
    for candidate in (
        _force_mutation(prior, modulation_schema_id="other-schema"),
        _force_mutation(prior, modulation_mapping_id="other-mapping"),
        _force_mutation(prior, modulation_profile_schema_id="other-profile-schema"),
    ):
        with pytest.raises(BrainvisionConfigurationValidationError):
            validate_configuration_replacement(prior, candidate)


@pytest.mark.parametrize("status", (LIFECYCLE_ACTIVE, LIFECYCLE_SUSPENDED))
def test_active_and_suspended_prior_configurations_reject_theta_changes(status: str) -> None:
    prior = _configuration(lifecycle_status=status)
    candidate = _configuration(theta=1)

    with pytest.raises(BrainvisionConfigurationValidationError) as error:
        validate_configuration_replacement(prior, candidate)
    assert (error.value.field, error.value.reason) == (
        "theta",
        "profile_change_requires_disabled",
    )


def test_disabled_configuration_permits_a_consistent_theta_profile_change() -> None:
    validate_configuration_replacement(_configuration(theta=-1), _configuration(theta=1))


def test_profile_identifier_must_move_atomically_with_theta() -> None:
    prior = _configuration()
    mismatched_candidate = _force_mutation(
        _configuration(theta=1), modulation_profile_id=prior.modulation_profile_id
    )

    with pytest.raises(BrainvisionConfigurationValidationError) as error:
        validate_configuration_replacement(prior, mismatched_candidate)
    assert (error.value.field, error.value.reason) == (
        "modulation_profile_id",
        "modulation_profile_mismatch",
    )


def test_lifecycle_status_change_is_not_itself_a_replacement_rejection() -> None:
    prior = _configuration(lifecycle_status=LIFECYCLE_DISABLED)
    candidate = _configuration(lifecycle_status=LIFECYCLE_ACTIVE)

    validate_configuration_replacement(prior, candidate)


def test_module_import_boundary_excludes_fabric_locks_and_runtime_systems() -> None:
    source = Path(configuration_module.__file__).read_text(encoding="utf-8")
    imports: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.add(node.module)

    allowed_nonstdlib = {
        "brainvision.character_modulation",
        "brainvision.observation",
        "brainvision.projection",
        "brainvision.vhe",
        "torment_service.pathing",
    }
    assert allowed_nonstdlib <= imports
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

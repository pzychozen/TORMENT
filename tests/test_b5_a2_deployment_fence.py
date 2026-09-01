"""B5-A2 durable deployment-selector and core-maintenance fence tests."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest

from torment_service.substrate.connection import (
    open_existing_native_core_connection,
    open_temporary_test_connection,
)
from torment_service.substrate.deployment_core_maintenance import (
    abort_cutover_pending,
    activate_core,
    enter_cutover_pending,
    inspect_contained_core_deployment,
    staging_legacy_witness,
)
from torment_service.substrate.deployment_selector import (
    abort_selector_pending,
    activate_selector_native,
    begin_cutover_pending,
    establish_selector_era,
    initialize_selector,
    read_selector_state,
    resolve_deployment_agreement,
    selector_paths,
)
from torment_service.substrate.deployment_types import (
    DeploymentResolutionMode,
    DeploymentState,
    QualifiedDeploymentProfile,
)
from torment_service.substrate.errors import (
    DeploymentAuthorityError,
    DeploymentIdempotencyConflict,
    SubstrateConfigurationError,
)
from torment_service.substrate.runtime_binding import prepare_native_memory_runtime_binding
from torment_service.substrate.schema import create_schema


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _profile(**overrides: object) -> QualifiedDeploymentProfile:
    values: dict[str, object] = {
        "compression_enabled": False,
        "deep_memory_enabled": False,
        "representation_provider": "test-provider",
        "representation_model": "test-model",
        "representation_dimension": 3,
        "admitted_scope_plan_digest": _digest("scope-plan"),
        "external_owner_digest": _digest("owner-facts"),
    }
    values.update(overrides)
    return QualifiedDeploymentProfile(**values)  # type: ignore[arg-type]


def _root_with_staging_core(tmp_path: Path, name: str = "alpha.db") -> tuple[Path, str]:
    root = tmp_path / "data-root"
    core_root = root / "substrate" / "cores"
    core_root.mkdir(parents=True)
    qualified = open_temporary_test_connection(core_root / name)
    try:
        create_schema(qualified.connection)
    finally:
        qualified.close()
    return root, name


def _pending(root: Path, name: str, *, operation: str = "selector-pending"):
    profile = _profile()
    establish_selector_era(data_root=root)
    initial = initialize_selector(data_root=root, operation_key="selector-init")
    selected = begin_cutover_pending(
        data_root=root,
        core_relative_path=name,
        descriptor_digest=_digest("descriptor"),
        profile=profile,
        expected_generation=initial.generation,
        operation_key=operation,
    )
    return profile, selected


def _core_pending(root: Path, name: str, selected):
    inspection = inspect_contained_core_deployment(data_root=root, core_relative_path=name)
    initial_witness = staging_legacy_witness(
        inspection,
        descriptor_digest=selected.descriptor_digest,
        profile_digest=selected.profile_digest,
    )
    return enter_cutover_pending(
        data_root=root,
        core_relative_path=name,
        expected_witness=initial_witness,
        selector_generation=selected.generation,
        selector_witness_digest=selected.core_witness_digest,
        operation_key="core-pending",
    )


def _activate(root: Path, name: str, selected):
    pending = _core_pending(root, name, selected)
    active = activate_core(
        data_root=root,
        core_relative_path=name,
        expected_witness=pending.witness,
        selector_generation=selected.generation,
        selector_witness_digest=selected.core_witness_digest,
        operation_key="core-active",
    )
    return pending, active


def test_preselector_and_marker_without_selector_dispositions(tmp_path: Path):
    root, name = _root_with_staging_core(tmp_path)
    profile = _profile()

    preselector = resolve_deployment_agreement(data_root=root, effective_profile=profile)
    assert preselector.mode is DeploymentResolutionMode.LEGACY_PUBLIC

    establish_selector_era(data_root=root)
    marker_without_db = resolve_deployment_agreement(data_root=root, effective_profile=profile)
    assert marker_without_db.mode is DeploymentResolutionMode.REFUSED

    initialized = initialize_selector(data_root=root, operation_key="init")
    assert initialized == read_selector_state(data_root=root)
    assert resolve_deployment_agreement(data_root=root, effective_profile=profile).mode is DeploymentResolutionMode.LEGACY_PUBLIC
    assert name == "alpha.db"


def test_era_marker_and_selector_initialization_are_write_once_recoverable(tmp_path: Path):
    root, _name = _root_with_staging_core(tmp_path)
    marker = establish_selector_era(data_root=root)
    marker_bytes = marker.read_bytes()
    assert establish_selector_era(data_root=root) == marker
    assert marker.read_bytes() == marker_bytes
    initial = initialize_selector(data_root=root, operation_key="init")
    assert initialize_selector(data_root=root, operation_key="init") == initial
    with pytest.raises(DeploymentAuthorityError, match="already initialized"):
        initialize_selector(data_root=root, operation_key="other-init")
    marker.write_text("{}", encoding="utf-8")
    with pytest.raises(DeploymentAuthorityError, match="marker"):
        establish_selector_era(data_root=root)


def test_cutover_order_never_routes_until_exact_native_agreement(tmp_path: Path):
    root, name = _root_with_staging_core(tmp_path)
    profile, selected = _pending(root, name)

    untouched = resolve_deployment_agreement(data_root=root, effective_profile=profile)
    assert untouched.mode is DeploymentResolutionMode.MAINTENANCE_ONLY

    pending, active = _activate(root, name, selected)
    assert pending.witness.deployment_state is DeploymentState.CUTOVER_PENDING
    assert active.witness.deployment_state is DeploymentState.NATIVE_ACTIVE
    still_pending = resolve_deployment_agreement(data_root=root, effective_profile=profile)
    assert still_pending.mode is DeploymentResolutionMode.MAINTENANCE_ONLY

    final = activate_selector_native(
        data_root=root,
        core_relative_path=name,
        core_result=active,
        expected_generation=selected.generation,
        operation_key="selector-active",
    )
    assert final.deployment_state is DeploymentState.NATIVE_ACTIVE
    agreement = resolve_deployment_agreement(data_root=root, effective_profile=profile)
    assert agreement.mode is DeploymentResolutionMode.NATIVE_AGREEMENT
    assert agreement.reason == "native-agreement-qualified-no-public-routing"


def test_lost_response_retries_are_exact_and_changed_intention_refuses(tmp_path: Path):
    root, name = _root_with_staging_core(tmp_path)
    profile, selected = _pending(root, name)
    assert begin_cutover_pending(
        data_root=root,
        core_relative_path=name,
        descriptor_digest=_digest("descriptor"),
        profile=profile,
        expected_generation=0,
        operation_key="selector-pending",
    ) == selected
    with pytest.raises(DeploymentIdempotencyConflict):
        begin_cutover_pending(
            data_root=root,
            core_relative_path=name,
            descriptor_digest=_digest("different-descriptor"),
            profile=profile,
            expected_generation=0,
            operation_key="selector-pending",
        )

    pending, active = _activate(root, name, selected)
    # The pending receipt remains recoverable even after a later core event.
    assert enter_cutover_pending(
        data_root=root,
        core_relative_path=name,
        expected_witness=replace(
            pending.witness,
            core_role="STAGING",
            deployment_state=DeploymentState.LEGACY_ACTIVE,
        ),
        selector_generation=selected.generation,
        selector_witness_digest=selected.core_witness_digest,
        operation_key="core-pending",
    ) == pending
    assert activate_core(
        data_root=root,
        core_relative_path=name,
        expected_witness=pending.witness,
        selector_generation=selected.generation,
        selector_witness_digest=selected.core_witness_digest,
        operation_key="core-active",
    ) == active
    final = activate_selector_native(
        data_root=root,
        core_relative_path=name,
        core_result=active,
        expected_generation=selected.generation,
        operation_key="selector-active",
    )
    assert activate_selector_native(
        data_root=root,
        core_relative_path=name,
        core_result=active,
        expected_generation=selected.generation,
        operation_key="selector-active",
    ) == final
    with pytest.raises(DeploymentIdempotencyConflict):
        activate_selector_native(
            data_root=root,
            core_relative_path="different.db",
            core_result=active,
            expected_generation=selected.generation,
            operation_key="selector-active",
        )


def test_safe_pending_abort_is_the_only_reversal(tmp_path: Path):
    root, name = _root_with_staging_core(tmp_path)
    profile, selected = _pending(root, name)
    pending = _core_pending(root, name, selected)
    aborted_core = abort_cutover_pending(
        data_root=root,
        core_relative_path=name,
        expected_witness=pending.witness,
        selector_generation=selected.generation,
        selector_witness_digest=selected.core_witness_digest,
        operation_key="core-abort",
    )
    assert abort_cutover_pending(
        data_root=root,
        core_relative_path=name,
        expected_witness=pending.witness,
        selector_generation=selected.generation,
        selector_witness_digest=selected.core_witness_digest,
        operation_key="core-abort",
    ) == aborted_core
    aborted_selector = abort_selector_pending(
        data_root=root,
        core_relative_path=name,
        core_result=aborted_core,
        expected_generation=selected.generation,
        operation_key="selector-abort",
    )
    assert aborted_selector.deployment_state is DeploymentState.LEGACY_ACTIVE
    assert resolve_deployment_agreement(data_root=root, effective_profile=profile).mode is DeploymentResolutionMode.LEGACY_PUBLIC
    assert abort_selector_pending(
        data_root=root,
        core_relative_path=name,
        core_result=aborted_core,
        expected_generation=selected.generation,
        operation_key="selector-abort",
    ) == aborted_selector


def test_native_agreement_refuses_profile_or_selected_core_mismatch(tmp_path: Path):
    root, name = _root_with_staging_core(tmp_path)
    profile, selected = _pending(root, name)
    _pending_receipt, active = _activate(root, name, selected)
    activate_selector_native(
        data_root=root,
        core_relative_path=name,
        core_result=active,
        expected_generation=selected.generation,
        operation_key="selector-active",
    )

    compressed = resolve_deployment_agreement(
        data_root=root,
        effective_profile=_profile(compression_enabled=True),
    )
    assert compressed.mode is DeploymentResolutionMode.REFUSED

    paths = selector_paths(root)
    (paths.core_root / name).rename(paths.core_root / "missing-selected-core.db")
    missing = resolve_deployment_agreement(data_root=root, effective_profile=profile)
    assert missing.mode is DeploymentResolutionMode.REFUSED


@pytest.mark.parametrize(
    "profile_overrides",
    ({"compression_enabled": True}, {"deep_memory_enabled": True}),
)
def test_native_agreement_requires_compression_and_deep_memory_disabled(
    tmp_path: Path, profile_overrides: dict[str, object]
):
    root, name = _root_with_staging_core(tmp_path)
    profile, selected = _pending(root, name)
    _pending_receipt, active = _activate(root, name, selected)
    activate_selector_native(
        data_root=root,
        core_relative_path=name,
        core_result=active,
        expected_generation=selected.generation,
        operation_key="selector-active",
    )
    assert resolve_deployment_agreement(
        data_root=root, effective_profile=_profile(**profile_overrides)
    ).mode is DeploymentResolutionMode.REFUSED


def test_active_core_rejects_the_existing_staging_runtime_binding(tmp_path: Path):
    root, name = _root_with_staging_core(tmp_path)
    _profile_value, selected = _pending(root, name)
    _pending_receipt, active = _activate(root, name, selected)
    with open_existing_native_core_connection(root / "substrate" / "cores" / name) as opened:
        with pytest.raises(SubstrateConfigurationError, match="only STAGING"):
            prepare_native_memory_runtime_binding(
                connection=opened.connection,
                core_database_path=opened.database_path,
                expected_core_id=active.witness.core_id,
                scope_bindings=(),
                representation_lane=None,  # type: ignore[arg-type]
            )


def test_native_agreement_refuses_a_nonexact_actual_sqlite_runtime(tmp_path: Path, monkeypatch):
    from torment_service.substrate import deployment_selector as selector_module

    root, name = _root_with_staging_core(tmp_path)
    profile, selected = _pending(root, name)
    _pending_receipt, active = _activate(root, name, selected)
    activate_selector_native(
        data_root=root,
        core_relative_path=name,
        core_result=active,
        expected_generation=selected.generation,
        operation_key="selector-active",
    )
    monkeypatch.setattr(
        selector_module,
        "qualify_runtime",
        lambda: type("Runtime", (), {"sqlite_runtime_version": "3.51.2"})(),
    )
    assert resolve_deployment_agreement(data_root=root, effective_profile=profile).mode is DeploymentResolutionMode.REFUSED


@pytest.mark.parametrize("corruption", ("wrong-schema", "generation-mismatch", "unknown-state"))
def test_corrupt_selector_refuses_without_legacy_fallback(tmp_path: Path, corruption: str):
    root, _name = _root_with_staging_core(tmp_path)
    establish_selector_era(data_root=root)
    paths = selector_paths(root)
    if corruption == "wrong-schema":
        connection = sqlite3.connect(paths.selector_path)
        try:
            connection.execute("CREATE TABLE unrelated (value TEXT)")
        finally:
            connection.close()
    else:
        initialize_selector(data_root=root, operation_key="init")
        connection = sqlite3.connect(paths.selector_path)
        try:
            if corruption == "generation-mismatch":
                connection.execute("UPDATE selector_state SET generation=99")
            else:
                connection.execute("UPDATE selector_state SET deployment_state='UNKNOWN'")
            connection.commit()
        finally:
            connection.close()
    result = resolve_deployment_agreement(data_root=root, effective_profile=_profile())
    assert result.mode is DeploymentResolutionMode.REFUSED


def test_contained_core_path_and_unselected_claims_fail_closed(tmp_path: Path):
    root, name = _root_with_staging_core(tmp_path)
    profile, selected = _pending(root, name)
    with pytest.raises(DeploymentAuthorityError):
        begin_cutover_pending(
            data_root=root,
            core_relative_path="..\\escape.db",
            descriptor_digest=_digest("descriptor"),
            profile=profile,
            expected_generation=selected.generation,
            operation_key="bad-path",
        )

    second = root / "substrate" / "cores" / "second.db"
    qualified = open_temporary_test_connection(second)
    try:
        create_schema(qualified.connection)
        qualified.connection.execute("UPDATE core_metadata SET core_role='ACTIVE_CORE'")
        core_id = qualified.connection.execute("SELECT core_id FROM core_metadata").fetchone()[0]
        qualified.connection.execute(
            "UPDATE deployment_metadata SET deployment_state='NATIVE_ACTIVE',referenced_core_id=?",
            (core_id,),
        )
    finally:
        qualified.close()
    assert resolve_deployment_agreement(data_root=root, effective_profile=profile).mode is DeploymentResolutionMode.REFUSED


def test_resolver_is_side_effect_free_and_public_entrypoints_remain_legacy(tmp_path: Path):
    root, name = _root_with_staging_core(tmp_path)
    profile, selected = _pending(root, name)
    _pending_receipt, active = _activate(root, name, selected)
    activate_selector_native(
        data_root=root,
        core_relative_path=name,
        core_result=active,
        expected_generation=selected.generation,
        operation_key="selector-active",
    )
    paths = selector_paths(root)
    core_path = paths.core_root / name
    tracked_paths = (paths.marker_path, paths.selector_path, core_path)
    before = {path: path.read_bytes() for path in tracked_paths}
    before_core_files = {
        path.name: path.read_bytes()
        for path in paths.core_root.iterdir()
        if path.is_file()
    }

    first = resolve_deployment_agreement(data_root=root, effective_profile=profile)
    second = resolve_deployment_agreement(data_root=root, effective_profile=profile)
    assert first.mode is second.mode is DeploymentResolutionMode.NATIVE_AGREEMENT
    assert {path: path.read_bytes() for path in tracked_paths} == before
    assert {
        path.name: path.read_bytes()
        for path in paths.core_root.iterdir()
        if path.is_file()
    } == before_core_files

    # Hide the selected active core.  The legacy public entrypoints must still
    # start, proving that B5-A2 has not wired selector resolution, native-core
    # opening, or a routing capability into either public surface.
    hidden = paths.core_root / "hidden-active-core.db"
    core_path.rename(hidden)
    try:
        environment = os.environ.copy()
        environment.update({"TORMENT_DATA_DIR": str(root), "TORMENT_MCP_DATA_DIR": str(root)})
        probe = "\n".join(
            (
                "import os",
                "from pathlib import Path",
                "root = Path(os.environ['TORMENT_DATA_DIR'])",
                "marker = (root / 'substrate' / 'deployment' / 'selector-era-v1.json').read_bytes()",
                "selector = (root / 'substrate' / 'deployment' / 'selector.sqlite').read_bytes()",
                "from torment_service import app",
                "assert app.fabric is not None",
                "assert (root / 'substrate' / 'deployment' / 'selector-era-v1.json').read_bytes() == marker",
                "assert (root / 'substrate' / 'deployment' / 'selector.sqlite').read_bytes() == selector",
                "from torment_service import mcp_server",
                "assert mcp_server._get_fabric() is not None",
                "assert (root / 'substrate' / 'deployment' / 'selector-era-v1.json').read_bytes() == marker",
                "assert (root / 'substrate' / 'deployment' / 'selector.sqlite').read_bytes() == selector",
            )
        )
        subprocess.run(
            [sys.executable, "-c", probe],
            cwd=Path(__file__).resolve().parents[1],
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        hidden.rename(core_path)
